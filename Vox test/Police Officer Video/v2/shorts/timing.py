"""shorts.timing: cut the owner's narration (vo_en.wav) into a Short's voice track and re-time every beat around it.

    from shorts.timing import Voice, retime
    V = Voice()                                   # loads vo_en.wav (48 kHz mono), timeline.json, asr_cache.json en_words
    clip = V.clip(i)                              # whole line i (energy-trimmed: onset - 40 ms, last loud frame + 60 ms)
    clip = V.clip(i, words=(k0, k1))              # words k0..k1 (0-based, inclusive) of line i (ASR word starts)
    clip = V.clip(i, alias=64)                    # line i's text/speaker, audio taken from line 64 (a missing take)
    T = retime(V, beats, edit)                    # -> dict(duration, beats[...], clips[...], words[...], chunks[...])
    V.write(T, path)                              # 48 kHz 24-bit mono voice track (5 ms fades per clip)

Clip fields: i, who, fx, text, a, b (source cut, s), on, off (speech onset / end inside the cut), words [(word, src_t)].
Re-timing (shorts_spec.json assembly_rules): the first word lands at 0.25 s; clips follow with audible gaps (default 0.28 s,
0.18-0.22 s inside quick exchanges, one tension gap of ~1.1 s); a cut lands LEAD s before each beat's first word; beats
without voice keep a fixed length. If the total runs over 56 s the gaps tighten (>= 0.08 s, never the tension gap); if it
runs under 48 s the tension gap stretches to 1.6 s and the end beat to 2.5 s.
Word timing: script words are aligned to the ASR words (difflib on normalised tokens), so captions show the script text
at the recognised times (ASR duplicates are dropped, unrecognised words are interpolated).
"""
import bisect, difflib, json, os, re
import numpy as np
import soundfile as sf

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
ALIGN = os.path.join(S, 'pov2', 'align')
SR = 48000
HOP = 0.01
LEAD = 0.10
PRE, TAIL, FADE = 0.04, 0.06, 0.005

_norm = lambda s: re.sub(r"[^a-z0-9]", '', s.lower())


class Clip:
    def __init__(self, **k):
        self.__dict__.update(k)

    def to_json(self):
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in self.__dict__.items() if k not in ('words',)}


class Voice:
    def __init__(self, wav=None, timeline=None, asr=None):
        self.wav_path = wav or os.path.join(ALIGN, 'vo_en.wav')
        self.tl = json.load(open(timeline or os.path.join(ALIGN, 'timeline.json')))
        self.L = self.tl['lines']
        self.asr = [(w, float(t)) for w, t in json.load(open(asr or os.path.join(ALIGN, 'asr_cache.json')))['en_words']]
        self.asr_t = [t for _, t in self.asr]
        self.y = None
        self._env = None

    # ---------------------------------------------------------------- audio + envelope
    def audio(self):
        if self.y is None:
            y, sr = sf.read(self.wav_path, dtype='float32', always_2d=False)
            if y.ndim > 1: y = y.mean(axis=1)
            assert sr == SR, sr
            self.y = y
        return self.y

    def env(self):
        """10 ms RMS in dB and the speech threshold."""
        if self._env is None:
            y = self.audio(); n = int(HOP * SR); m = len(y) // n
            r = np.sqrt(np.mean(y[:m * n].reshape(m, n).astype(np.float64) ** 2, axis=1) + 1e-12)
            db = 20 * np.log10(r + 1e-9)
            floor = float(np.percentile(db, 15))
            self._env = (db, floor)
        return self._env

    def _loud(self, t, thr):
        db, _ = self.env(); f = int(t / HOP)
        return 0 <= f < len(db) and db[f] > thr

    # ---------------------------------------------------------------- word alignment
    def line_words(self, i):
        """Script words of line i with source times aligned to the ASR words."""
        l = self.L[i]
        script = l['en'].split()
        a = bisect.bisect_left(self.asr_t, l['t'] - 0.3)
        b = bisect.bisect_right(self.asr_t, l['end'] + 0.25)
        cand = self.asr[a:b]
        sm = difflib.SequenceMatcher(None, [_norm(w) for w in script], [_norm(w) for w, _ in cand], autojunk=False)
        times = [None] * len(script)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = cand[blk.b + k][1]
        # fuzzy pass: unmatched script word vs an unmatched ASR word in the gap ("alright" / "all right")
        known = [(k, t) for k, t in enumerate(times) if t is not None]
        if not known:
            span = max(0.3, l['end'] - l['t'])
            return [(w, l['t'] + 0.05 + span * k / len(script)) for k, w in enumerate(script)]
        # interpolate the rest by character position between known neighbours
        out = []
        for k, w in enumerate(script):
            if times[k] is not None: out.append((w, times[k])); continue
            prev = max([(kk, tt) for kk, tt in known if kk < k], default=None)
            nxt = min([(kk, tt) for kk, tt in known if kk > k], default=None)
            if prev and nxt:
                t = prev[1] + (nxt[1] - prev[1]) * (k - prev[0]) / (nxt[0] - prev[0])
            elif prev:
                t = min(l['end'] - 0.1, prev[1] + 0.28 * (k - prev[0]))
            else:
                t = max(l['t'], nxt[1] - 0.28 * (nxt[0] - k))
            out.append((w, t))
        for k in range(1, len(out)):                       # monotone
            if out[k][1] <= out[k - 1][1]: out[k] = (out[k][0], out[k - 1][1] + 0.08)
        return out

    # ---------------------------------------------------------------- clips
    def _onset(self, t_word, lo):
        """Speech onset at or before an ASR word start (ASR starts can be late): walk back over loud frames, <= 120 ms."""
        db, floor = self.env(); thr = floor + 14
        f = int(t_word / HOP); f0 = max(int(lo / HOP), f - 12)
        while f > f0 and db[f - 1] > thr: f -= 1
        # also skip forward over silence if the ASR start sits before the sound
        g = f
        while g < f + 15 and g < len(db) and db[g] <= thr: g += 1
        if g < f + 15: f = g
        return f * HOP

    def _offset(self, t_hi, lo):
        """Last loud frame before t_hi (end of speech), not before lo."""
        db, floor = self.env(); thr = floor + 12
        f = int(t_hi / HOP)
        while f > int(lo / HOP) + 3 and db[min(f, len(db) - 1)] <= thr: f -= 1
        return (f + 1) * HOP

    def clip(self, i, words=None, alias=None, text=None):
        l = self.L[i]
        src_i = alias if alias is not None else i
        ls = self.L[src_i]
        lw = self.line_words(src_i)
        if words is not None:
            k0, k1 = words
            sel = lw[k0:k1 + 1]
            nxt = lw[k1 + 1][1] if k1 + 1 < len(lw) else ls['end']
            on = self._onset(sel[0][1], (lw[k0 - 1][1] + 0.12) if k0 > 0 else ls['t'] - 0.15)
            off = self._offset(nxt - 0.02 if k1 + 1 < len(lw) else ls['end'] + 0.05, sel[-1][1] + 0.1)
            if k1 + 1 < len(lw): off = min(off, nxt - 0.03)
            txt = ' '.join(w for w, _ in sel)
        else:
            sel = lw
            on = self._onset(lw[0][1], ls['t'] - 0.15)
            off = self._offset(ls['end'] + 0.05, lw[-1][1] + 0.1)
            nxt_line = self.L[src_i + 1]['t'] if src_i + 1 < len(self.L) else off + 1
            off = min(off, nxt_line - 0.02)
            txt = l['en'] if alias is None else (text or l['en'])
        if alias is not None and words is None:
            sel = [(w, sel[min(k, len(sel) - 1)][1]) for k, w in enumerate((text or l['en']).split())]
        a = on - PRE; b = off + TAIL
        if words is not None and k1 + 1 < len(lw): b = min(b, lw[k1 + 1][1] - 0.01)
        return Clip(i=i, src=src_i, who=l['who'], fx=l.get('fx'), text=(text or txt), a=a, b=b, on=on, off=off,
                    words=[(w, t) for w, t in sel], line_text=l['en'], trim=list(words) if words else None)

    def new_clip(self, path, text, who='N', ident=None):
        """A newly recorded line (shorts_vo/<ID>.wav): energy-trimmed, words spread over the speech by character count."""
        z = self._load_new(path)
        n = int(HOP * SR); m = len(z) // n
        r = 20 * np.log10(np.sqrt(np.mean(z[:m * n].reshape(m, n).astype(np.float64) ** 2, axis=1) + 1e-12) + 1e-9)
        thr = max(float(np.percentile(r, 10)) + 14, float(r.max()) - 40)
        loud = np.nonzero(r > thr)[0]
        on = (loud[0] * HOP) if len(loud) else 0.0
        off = ((loud[-1] + 1) * HOP) if len(loud) else len(z) / SR
        ws = text.split()
        tot = sum(len(w) + 1 for w in ws); acc = 0; words = []
        for w in ws:
            words.append((w, on + (off - on) * acc / tot)); acc += len(w) + 1
        return Clip(i=-1, src=ident or os.path.basename(path), who=who, fx=None, text=text, a=max(0.0, on - PRE), b=min(len(z) / SR, off + TAIL),
                    on=on, off=off, words=words, line_text=text, trim=None, wav=path)

    def _load_new(self, path):
        if not hasattr(self, '_new'): self._new = {}
        if path not in self._new:
            z, sr = sf.read(path, dtype='float32', always_2d=False)
            if z.ndim > 1: z = z.mean(axis=1)
            if sr != SR:
                try:
                    import soxr
                    z = soxr.resample(z, sr, SR).astype(np.float32)
                except ImportError:
                    import librosa
                    z = librosa.resample(z, orig_sr=sr, target_sr=SR).astype(np.float32)
            self._new[path] = z
        return self._new[path]

    # ---------------------------------------------------------------- render the voice track
    def write(self, T, path, dur=None):
        y = self.audio()
        n = int(round((dur or T['duration']) * SR))
        out = np.zeros(n, np.float32)
        for c in T['clips']:
            a, b = int(round(c['a'] * SR)), int(round(c['b'] * SR))
            seg = (self._load_new(c['wav']) if c.get('wav') else y)[a:b].copy()
            if c.get('tempo', 1.0) != 1.0:
                seg = _tempo(seg, c['tempo'])
            nf = int(FADE * SR)
            if len(seg) > 2 * nf:
                seg[:nf] *= np.linspace(0, 1, nf, dtype=np.float32); seg[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)
            d = int(round(c['dst_a'] * SR))
            m = min(len(seg), n - d)
            if m > 0: out[d:d + m] += seg[:m]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sf.write(path, out, SR, subtype='PCM_24')
        return path


def _tempo(seg, k):
    """Pitch-preserving speed-up (WSOLA via ffmpeg atempo)."""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, 'i.wav'), os.path.join(d, 'o.wav')
        sf.write(i, seg, SR, subtype='FLOAT')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', i, '-filter:a', 'atempo=%.4f' % k, o], check=True)
        z, _ = sf.read(o, dtype='float32')
    return z


# ==================================================================================================== re-timing
def retime(V, beats, first_word=0.25, tension_after=None, tension=1.1, default_gap=0.28, min_total=48.0, max_total=56.0,
           end_beat=None, loop_dur=0.5):
    """beats: [dict(n, clips=[Clip], gap=after (s) | None, dur=for no-voice beats, inner=gap between clips)] in order.
    Returns the timing dict. Two passes: lay out, then stretch / tighten to 48-56 s."""
    def layout(gscale=1.0, tgap=tension, end_min=None, tempo=1.0):
        cur = first_word
        out = []
        clips = []
        for k, bt in enumerate(beats):
            e = dict(n=bt['n'], clips=[])
            if bt.get('clips'):
                for j, c in enumerate(bt['clips']):
                    tk = tempo if (c.who == 'N' and tempo != 1.0) else 1.0
                    span = (c.off - c.on) / tk
                    dst_on = cur
                    dst_a = dst_on - (c.on - c.a) / tk
                    cj = c.to_json(); cj.update(dst_a=dst_a, dst_b=dst_a + (c.b - c.a) / tk, dst_on=dst_on, dst_off=dst_on + span,
                                                tempo=tk, beat=bt['n'])
                    cj['words'] = [(w, dst_a + (t - c.a) / tk) for w, t in c.words]
                    e['clips'].append(cj); clips.append(cj)
                    cur = dst_on + span
                    if j + 1 < len(bt['clips']): cur += bt.get('inner', 0.3) * (gscale if gscale < 1 else 1)
                e['voice_on'] = e['clips'][0]['dst_on']
                e['voice_off'] = e['clips'][-1]['dst_off']
                g = bt.get('gap')
                if g is None: g = default_gap
                if tension_after is not None and bt['n'] == tension_after:
                    g = tgap; e['tension'] = True
                elif gscale != 1.0:
                    g = max(0.08, g * gscale)
                if end_min and end_beat is not None and bt['n'] == end_beat:
                    g = max(g, end_min - (e['voice_off'] - e['voice_on']))
                cur += g
            else:
                e['voice_on'] = e['voice_off'] = None
                cur += bt.get('dur', loop_dur)
                e['nodur'] = bt.get('dur', loop_dur)
            out.append(e)
        # beat boundaries: cut LEAD before the first word; voiceless beats start where the previous voice + gap ended
        for k, e in enumerate(out):
            if k == 0: e['t0'] = 0.0
            elif e['voice_on'] is not None: e['t0'] = max(out[k - 1]['t0'] + 0.2, e['voice_on'] - LEAD)
            else:
                p = out[k - 1]
                e['t0'] = (p['voice_off'] + 0.12) if p['voice_off'] is not None else p['t0'] + p.get('nodur', loop_dur)
        total = cur
        for k, e in enumerate(out):
            e['t1'] = out[k + 1]['t0'] if k + 1 < len(out) else total
        return out, clips, total

    out, clips, total = layout()
    tempo = 1.0
    if total > max_total:
        for gs in (0.8, 0.6, 0.45, 0.3):
            out, clips, total = layout(gscale=gs)
            if total <= max_total: break
        if total > max_total:
            for tempo in (1.02, 1.04, 1.06):
                out, clips, total = layout(gscale=0.3, tempo=tempo)
                if total <= max_total: break
    elif total < min_total:
        out, clips, total = layout(tgap=max(tension, 1.6), end_min=2.5)
    words = [dict(w=w, t=t, beat=c['beat'], who=c['who'], clip=k) for k, c in enumerate(clips) for (w, t) in c['words']]
    for k, w in enumerate(words):                 # word end: next word start inside the clip, else the clip's speech end
        c = clips[w['clip']]
        nxt = words[k + 1] if k + 1 < len(words) and words[k + 1]['clip'] == w['clip'] else None
        w['end'] = min(nxt['t'], w['t'] + 0.9) if nxt else c['dst_off']
    return dict(duration=total, beats=out, clips=clips, words=words, tempo=tempo)


# ==================================================================================================== captions
SMALL = {'a', 'an', 'the', 'of', 'to', 'in', 'on', 'at', 'is', 'if', 'and', 'or', 'i', 'he', 'his', 'her', 'it', 'you', 'your',
         'my', 'its', "it's", 'be', 'by', 'for', 'as', 'was', 'do', 'so', 'but', 'from', 'with', 'this', 'that', 'we',
         "we've", "you'll", "he'll", "you're", "that's", 'are', 'will', 'has', 'had', 'what', 'who', 'one', 'off', 'up', 'now'}


def chunk_words(words, max_chars=13):
    """1-2 words per chunk: short function words pair with the next word, a chunk ends at punctuation or after 2 words.
    words: [dict(w, t, end, ...)] in order (one clip at a time). Returns [dict(text, i0, i1, t, end)]."""
    out = []
    k = 0
    while k < len(words):
        w0 = words[k]
        txt = w0['w']; j = k
        ends = txt.endswith((',', '.', '?', '!', '...', ';', ':'))
        if not ends and k + 1 < len(words) and words[k + 1]['clip'] == w0['clip']:
            w1 = words[k + 1]
            pair = txt + ' ' + w1['w']
            if (_norm(txt) in SMALL or _norm(w1['w']) in SMALL or len(_norm(txt)) <= 3) and len(pair) <= max_chars:
                txt = pair; j = k + 1
        out.append(dict(text=txt, i0=k, i1=j, t=words[k]['t'], end=words[j]['end'], clip=w0['clip']))
        k = j + 1
    # chunk timing: show until the next chunk of the same clip starts; hold the last one up to 0.5 s after speech
    for k, c in enumerate(out):
        nxt = out[k + 1] if k + 1 < len(out) else None
        if nxt and nxt['clip'] == c['clip']:
            c['t1'] = nxt['t']
        else:
            c['t1'] = min(c['end'] + 0.35, (nxt['t'] - 0.02) if nxt else c['end'] + 0.35)
        c['t1'] = max(c['t1'], c['t'] + 0.18)
    return out
