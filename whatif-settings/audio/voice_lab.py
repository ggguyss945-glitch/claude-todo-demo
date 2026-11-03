#!/usr/bin/env python3
"""voice_lab.py - acted voice lines from stock Kokoro voices (Apache-2.0) with designed prosody.

    python3 -I audio/voice_lab.py --hook                       # S00 + S01-L001 with the chosen recipe per role (final takes)
    python3 -I audio/voice_lab.py --ids S00-L006,S00-L021       # regenerate some lines
    python3 -I audio/voice_lab.py --scene S01                   # every line of a scene whose role has a recipe
    python3 -I audio/voice_lab.py --lab --hook                  # build every candidate (approaches a, b, c, e), score, pick
    python3 -I audio/voice_lab.py --say "Total control." --role N --tag HYPE --out /tmp/x.wav   # ad-hoc line

How the acting is made ("approach e", the chosen recipe). Kokoro is a StyleTTS2-type model: a prosody predictor
outputs per-phoneme durations, an F0 curve (80 frames/s, Hz) and an energy curve, and an iSTFTNet decoder renders
audio from them. Plain Kokoro reads flat because those curves are average. We open the ONNX graph (in memory, the
model file is untouched) so that (1) a per-phoneme duration multiplier goes in before rounding and (2) the F0 and
energy curves can be replaced. A per-line "direction" (register, stressed words, beats, contour) is turned into new
durations and a new F0 curve, and Kokoro's own decoder renders them, so the voice keeps its natural harmonics
instead of being bent afterwards by PSOLA or a vocoder. Characters add a Praat formant shift (Sam) or strain EQ (Dad).
Every candidate is scored by voice_ingest.measure (ASR, pitch, rate, DNSMOS, HNR, jitter, clicks, speaker similarity).
"""
import argparse, json, os, re, sys, time, warnings
import numpy as np

warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voice_ingest as VI  # noqa: E402

PROJECT = VI.PROJECT
SCRIPT_JSON = os.path.join(PROJECT, 'docs', 'script.json')
TTS_DIR = os.environ.get('KOKORO_DIR', VI.SCRATCH + '/tts')
KOKORO_MODEL, KOKORO_VOICES = TTS_DIR + '/kokoro-v1.0.onnx', TTS_DIR + '/voices-v1.0.bin'
POCKET_DIR = VI.MODELS + '/sherpa-onnx-pocket-tts-2026-01-26'
LAB_DIR = os.path.join(VI.VOICE_DIR, 'lab')
QA_DIR = os.path.join(VI.VOICE_DIR, 'qa')
SR = 24000
DFPS, FFPS = 40, 80          # Kokoro duration frames / F0 frames per second
F0T, NT = '/encoder/Reshape_output_0', '/encoder/Reshape_1_output_0'
HOOK_IDS = [f'S00-L{i:03d}' for i in range(1, 24)] + ['S01-L001']
WPM_CAL = 1.09     # measured wpm_voiced / predicted word-token rate (calibrated in the lab: e takes ran 7-12 % fast at 1.0)
VOWELS = set('aeiouyæɑɐɒɔəɘɛɜɞɪʊʌʏɤɯɵøœᵻɚɝAIOWYQɨ')

# ================================================================================================ roles & registers
# Voices are stock Kokoro voice packs (Apache-2.0). A spec is a voice name, a {name: weight} blend, or
# {'dec': spec, 'pro': spec}: the decoder half of the style vector (timbre) and the predictor half (prosody) chosen apart.
# 'alt' = runner-up from the casting scan, rendered in the lab as e_alt (a voice check, not eligible for the final pick)
ROLES = {
    'N':   {'voice': {'am_michael': 0.5, 'am_puck': 0.5}, 'alt': {'am_echo': 0.5, 'am_michael': 0.5}, 'lang': 'en-us'},
    'SYS': {'voice': 'af_nova', 'alt': 'af_alloy', 'lang': 'en-us'},
    'SAM': {'voice': {'dec': {'af_sky': 0.7, 'am_puck': 0.3}, 'pro': 'af_sky'}, 'alt': 'af_sky', 'lang': 'en-us', 'formant': 1.0},
    'DAD': {'voice': 'am_eric', 'alt': 'am_onyx', 'lang': 'en-us'},
}
# register presets: hz = target median F0 of the intonation, k = contour exaggeration around the median,
# acc = default pitch accent (semitones) on stressed words, wpm = target words/min over voiced time,
# fall/rise = final contour (st), creak = lift creaky dips (0..1), micro = keep fine F0 detail (0..1),
# amp = loudness accent (dB) on stressed words, eq = finishing EQ name, pause = default beats (s) for ... / . / ,
REGS = {
    ('N', 'HYPE'):        dict(hz=205, k=1.45, acc=3.5, wpm=172, fall=3.0, rise=5.0, creak=0.8, micro=0.8, amp=2.0, eq='bright', pause=(0.42, 0.30, 0.16)),
    ('N', 'DEADPAN'):     dict(hz=112, k=0.55, acc=0.8, wpm=156, fall=2.0, rise=1.5, creak=0.3, micro=0.9, amp=0.5, eq='warm', pause=(0.48, 0.36, 0.20), decl=1.5),
    ('SYS', 'calm'):      dict(hz=200, k=0.60, acc=1.0, wpm=165, fall=2.0, rise=2.0, creak=0.5, micro=0.8, amp=0.8, eq='clean', pause=(0.40, 0.30, 0.22)),
    ('SYS', 'cheerful'):  dict(hz=238, k=1.25, acc=2.5, wpm=170, fall=3.0, rise=3.0, creak=0.6, micro=0.8, amp=1.5, eq='clean', pause=(0.40, 0.28, 0.18)),
    ('SAM', 'nervous'):   dict(hz=280, k=1.50, acc=4.0, wpm=182, fall=0.0, rise=2.0, creak=0.8, micro=0.8, amp=2.0, eq='kid', pause=(0.40, 0.25, 0.15), tremor=0.25),
    ('SAM', 'guilty'):    dict(hz=250, k=0.80, acc=1.0, wpm=120, fall=1.5, rise=1.0, creak=0.6, micro=0.8, amp=0.0, eq='kid', pause=(0.30, 0.25, 0.15)),
    ('SAM', 'yawning'):   dict(hz=245, k=0.70, acc=1.0, wpm=105, fall=4.0, rise=1.0, creak=0.6, micro=0.6, amp=0.0, eq='kid', pause=(0.30, 0.25, 0.15)),
    ('SAM', 'default'):   dict(hz=275, k=1.20, acc=3.0, wpm=175, fall=2.0, rise=3.0, creak=0.8, micro=0.8, amp=1.5, eq='kid', pause=(0.40, 0.28, 0.15)),
    ('DAD', 'shouting'):  dict(hz=265, k=1.30, acc=4.0, wpm=150, fall=4.0, rise=3.0, creak=1.0, micro=0.7, amp=3.0, eq='shout', pause=(0.40, 0.28, 0.15), effort=1.0),
    ('DAD', 'default'):   dict(hz=108, k=0.70, acc=1.5, wpm=160, fall=2.0, rise=2.0, creak=0.3, micro=0.9, amp=1.0, eq='warm', pause=(0.45, 0.32, 0.18)),
}

# Per-line direction for the hook. stress: {script word: accent st}; len: {word: duration factor};
# beat: {word: pause after it, s}; contour: q question rise, x exclaim (high then fall), f fall, s suspend, rf small rise-fall,
# yawn glide; soft: {word: dB} quieter words; say: text sent to the TTS (caps are lowered before phonemizing).
DIRECTION = {
    'S00-L001': dict(stress={'What': 1.5, 'real': 2.0, 'SETTINGS': 4.5}, len={'SETTINGS': 1.15}, contour='q', wpm=165),
    'S00-L002': dict(stress={'One': 4.0, 'app': 1.0}, len={'One': 1.15}, contour='x'),
    'S00-L003': dict(stress={'Total': 3.0, 'control': 3.5}, contour='x'),
    'S00-L004': dict(say='No un-do.', stress={'No': 1.2}, len={'undo': 1.1}, contour='f', wpm=140),
    'S00-L005': dict(stress={'reset': 0.8, 'one': 1.2}, contour='f'),
    'S00-L006': dict(stress={'defense': 2.0, 'ONE': 4.5, 'thing': 1.0}, len={'ONE': 1.3}, beat={'defense': 0.42}, contour='q', rise=2.0),
    'S00-L007': dict(stress={'you': 1.5, 'twelve': 1.0}, beat={'you': 0.28}, contour='f'),
    'S00-L008': dict(say='ish.', carrier='Well...', stress={}, len={'Ish': 1.3}, contour='rf'),
    'S00-L009': dict(stress={'scroll': 0.8, 'seven': 0.8}, beat={'back': 0.45}, contour='f'),
    'S00-L010': dict(stress={'Bedtime': 0.8, 'Supposedly': 1.0}, beat={'Bedtime': 0.36}, contour='f'),
    'S00-L011': dict(stress={'app': 1.5, 'never': 4.0}, len={'never': 1.15}, contour='x'),
    'S00-L012': dict(stress={'terms': 0.8}, beat={'First': 0.2}, contour='f'),
    'S00-L013': dict(stress={'pages': 1.0}, beat={'thousand': 0.18}, contour='f', wpm=150),
    'S00-L014': dict(say='So you read every word...', stress={'every': 3.5, 'word': 2.0}, len={'word': 1.2}, contour='s'),
    'S00-L015': dict(say='in half a second!', stress={'half': 4.0, 'second': 1.5}, contour='x', wpm=185),
    'S00-L016': dict(say='and press I agree!', stress={'press': 1.0, 'I': 2.5, 'AGREE': 4.5}, len={'AGREE': 1.2}, contour='x'),
    'S00-L017': dict(stress={'Welcome': 2.5, 'Reality': 2.0, 'Settings': 1.5}, contour='x'),
    'S00-L018': dict(carrier='Okay...', stress={'Prove': 1.0}, len={'Prove': 1.8}, contour='yawn'),
    'S00-L019': dict(stress={'open': 2.0, 'Brightness': 4.0}, contour='x'),
    'S00-L020': dict(stress={'Slide': 1.5, 'up': 4.0, 'little': 2.0}, beat={'up': 0.3}, soft={'Just': -3, 'a': -3, 'little': -2}, contour='f'),
    'S00-L021': dict(say='Who turned on the sun?!', stress={'Who': 2.5, 'SUN': 5.0}, len={'SUN': 1.7}, contour='x'),
    'S00-L022': dict(say="That's not the phone's brightness.", stress={'not': 2.0, "PHONE's": 5.0}, len={"PHONE's": 1.2}, contour='f'),
    'S00-L023': dict(stress={"planet's": 0.8}, len={"planet's": 1.1}, contour='f', wpm=140),
    'S01-L001': dict(stress={'Day': 3.0, 'one': 4.0}, len={'one': 1.25}, contour='x', wpm=140),
}
# Chosen recipe per role/register (and per-line exceptions) after the lab, see docs/VOICE_LAB.md.
RECIPE = {'default': dict(approach='e_mid')}

VARIANTS = {'mild': dict(k=0.85, acc=0.75), 'mid': dict(k=1.0, acc=1.0), 'strong': dict(k=1.18, acc=1.3)}

# ================================================================================================ engine


class Engine:
    """Kokoro v1.0 ONNX with two edits made in memory: a per-token duration multiplier before rounding, and F0/energy
    curves that can be read (pred) or replaced (dec)."""

    def __init__(self, threads=int(os.environ.get('VOICE_THREADS', '4'))):
        import onnx, onnxruntime as ort
        from onnx import helper, TensorProto
        from kokoro_onnx.tokenizer import Tokenizer
        self.voices = np.load(KOKORO_VOICES)
        self.tok = Tokenizer()
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads

        def base():
            m = onnx.load(KOKORO_MODEL)
            g = m.graph
            idx = [i for i, n in enumerate(g.node) if n.name == '/encoder/Round'][0]
            g.node[idx].input[0] = 'dur_scaled'
            g.node.insert(idx, helper.make_node('Mul', ['/encoder/Div_output_0', 'dur_mul'], ['dur_scaled'], name='dur_mul_node'))
            g.input.append(helper.make_tensor_value_info('dur_mul', TensorProto.FLOAT, [1, 'n']))
            return m
        m = base()
        del m.graph.output[:]
        for t, ty in [('/encoder/Cast_output_0', TensorProto.INT64), (F0T, TensorProto.FLOAT), (NT, TensorProto.FLOAT)]:
            m.graph.output.append(helper.make_tensor_value_info(t, ty, None))
        self.pred = ort.InferenceSession(m.SerializeToString(), so, providers=['CPUExecutionProvider'])
        m = base()
        for n in m.graph.node:
            for i, x in enumerate(n.input):
                if x == F0T:
                    n.input[i] = 'F0_in'
                elif x == NT:
                    n.input[i] = 'N_in'
        m.graph.input.append(helper.make_tensor_value_info('F0_in', TensorProto.FLOAT, [1, 'f']))
        m.graph.input.append(helper.make_tensor_value_info('N_in', TensorProto.FLOAT, [1, 'f']))
        self.dec = ort.InferenceSession(m.SerializeToString(), so, providers=['CPUExecutionProvider'])
        del m

    def _vec(self, spec, n):
        if isinstance(spec, str):
            return self.voices[spec][n - 1, 0].astype(np.float32)
        if isinstance(spec, dict) and 'dec' in spec:
            a, b = self._vec(spec['dec'], n), self._vec(spec['pro'], n)
            return np.concatenate([a[:128], b[128:]]).astype(np.float32)
        tot = sum(spec.values())
        return (sum(w * self.voices[k][n - 1, 0] for k, w in spec.items()) / tot).astype(np.float32)

    def style(self, spec, n):
        return self._vec(spec, n)[None, :]

    def phonemize(self, text, lang='en-us'):
        return self.tok.phonemize(text, lang)

    def ids(self, ph):
        return [self.tok.vocab[c] for c in ph if c in self.tok.vocab]

    def predict(self, ph, voice, speed=1.0, dur_mul=None):
        key = (ph, json.dumps(voice, sort_keys=True), round(float(speed), 5), None if dur_mul is None else np.asarray(dur_mul, np.float32).tobytes())
        if not hasattr(self, '_memo'):
            self._memo = {}
        if key in self._memo:
            P = self._memo[key]
            return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in P.items()}
        P = self._predict(ph, voice, speed, dur_mul)
        if len(self._memo) > 256:
            self._memo.clear()
        self._memo[key] = P
        return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in P.items()}

    def _predict(self, ph, voice, speed=1.0, dur_mul=None):
        toks = self.ids(ph)
        tok = np.array([[0, *toks, 0]], np.int64)
        st = self.style(voice, len(toks))
        dm = np.ones((1, tok.shape[1]), np.float32) if dur_mul is None else np.asarray(dur_mul, np.float32).reshape(1, -1)
        d, f0, N = self.pred.run(None, {'tokens': tok, 'style': st, 'speed': np.array([speed], np.float32), 'dur_mul': dm})
        return dict(ph=ph, tok=tok, style=st, speed=float(speed), dur_mul=dm, dur=d.ravel().astype(int), f0=f0.ravel().copy(), N=N.ravel().copy())

    def render(self, P, f0=None, N=None):
        f0 = P['f0'] if f0 is None else f0
        N = P['N'] if N is None else N
        a = self.dec.run(None, {'tokens': P['tok'], 'style': P['style'], 'speed': np.array([P['speed']], np.float32), 'dur_mul': P['dur_mul'],
                                'F0_in': np.asarray(f0, np.float32).reshape(1, -1), 'N_in': np.asarray(N, np.float32).reshape(1, -1)})[0]
        return np.asarray(a, np.float32).ravel()

# ================================================================================================ text layout


def tts_text(text):
    """Script text -> TTS text: caps lowered (espeak spells capitals as letters: SUN -> S-U-N), leading '...' dropped."""
    t = text.strip()
    t = re.sub(r'^\.\.\.\s*', '', t)

    def low(m):
        w = m.group(0)
        return w if w == 'I' else w.lower()
    t = re.sub(r"[A-Za-z']+", low, t)
    return t[0].upper() + t[1:] if t else t


def layout(E, say, lang):
    """Phonemes of the whole line plus a word label per token (token 0 is the leading pad)."""
    import difflib
    ph = E.phonemize(say, lang)
    chars = [c for c in ph if c in E.tok.vocab]
    words = [w for w in re.findall(r"[A-Za-z0-9']+", say.replace('-', ' ')) if VI.norm_word(w)]
    # per-word phonemes to label the characters of the whole-line phonemes
    lab_seq, lab = [], []
    for wi, w in enumerate(words):
        pw = E.phonemize(w, lang)
        for c in pw:
            if c in E.tok.vocab and c not in ' ˈˌ.,!?;:…"' and c != 'ː':
                lab_seq.append(c)
                lab.append(wi)
    full_idx = [i for i, c in enumerate(chars) if c not in ' ˈˌ.,!?;:…"—' and c != 'ː']
    full_seq = [chars[i] for i in full_idx]
    tw = np.full(len(chars), -1, int)
    sm = difflib.SequenceMatcher(a=full_seq, b=lab_seq, autojunk=False)
    for a0, b0, n in sm.get_matching_blocks():
        for k in range(n):
            tw[full_idx[a0 + k]] = lab[b0 + k]
    # unlabeled letters inherit from their space-delimited group (nearest labeled char)
    groups, cur = [], []
    for i, c in enumerate(chars):
        if c == ' ':
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(i)
    if cur:
        groups.append(cur)
    for gidx in groups:
        for i in gidx:
            if tw[i] == -1 and chars[i] not in '.,!?;:…"—':
                labeled = [j for j in gidx if tw[j] >= 0]
                if labeled:
                    tw[i] = tw[min(labeled, key=lambda j: abs(j - i))]
    # a group with no label between words i and i+2 is word i+1 (espeak reads lone 'a' as a letter name, so it never matches)
    glab = [sorted(set(tw[i] for i in gi if tw[i] >= 0)) for gi in groups]
    for g_i, gi in enumerate(groups):
        if glab[g_i] or all(chars[i] in '.,!?;:…"—' for i in gi):
            continue
        prv = next((glab[k][-1] for k in range(g_i - 1, -1, -1) if glab[k]), -1)
        nxt = next((glab[k][0] for k in range(g_i + 1, len(groups)) if glab[k]), len(words))
        if nxt - prv == 2:
            for i in gi:
                if chars[i] not in '.,!?;:…"—':
                    tw[i] = prv + 1
            glab[g_i] = [prv + 1]
    # monotone fix: a label may not go backwards
    last = -1
    for i in range(len(tw)):
        if tw[i] >= 0:
            if tw[i] < last:
                tw[i] = last
            last = tw[i]
    tok_word = np.concatenate([[-1], tw, [-1]])
    tok_char = ['<s>'] + chars + ['</s>']
    # stressed vowel per word: first vowel after a primary stress mark, else the first vowel
    stress_tok = {}
    for wi in range(len(words)):
        ids_ = [i for i in range(len(tok_char)) if tok_word[i] == wi]
        if not ids_:
            continue
        pv = None
        for i in range(ids_[0] - 1, ids_[-1] + 1):
            if tok_char[i] == 'ˈ':
                for j in range(i + 1, ids_[-1] + 1):
                    if tok_char[j] in VOWELS:
                        pv = j
                        break
                if pv:
                    break
        if pv is None:
            vv = [i for i in ids_ if tok_char[i] in VOWELS]
            pv = vv[0] if vv else ids_[len(ids_) // 2]
        vend = pv
        while vend + 1 < len(tok_char) and (tok_char[vend + 1] in VOWELS or tok_char[vend + 1] == 'ː'):
            vend += 1
        stress_tok[wi] = (pv, vend)
    return dict(ph=ph, chars=tok_char, tok_word=tok_word, words=words, stress_tok=stress_tok)


def map_script_words(script_text, say_words):
    """Index in say_words for each script word (by normalised spelling; positional fallback)."""
    import difflib
    _, sn = VI.script_words(script_text)
    an = [VI.norm_word(w) for w in say_words]
    m = {}
    sm = difflib.SequenceMatcher(a=sn, b=an, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace'):
            for k in range(min(i2 - i1, j2 - j1)):
                m[i1 + k] = j1 + k
    return m, sn


def word_key(script_text, say_words, key):
    """Resolve a direction key (a script word, any case) to the say-word index."""
    m, sn = map_script_words(script_text, say_words)
    k = VI.norm_word(key)
    for i, w in enumerate(sn):
        if w == k and i in m:
            return m[i]
    for j, w in enumerate(say_words):
        if VI.norm_word(w) == k:
            return j
    return None

# ================================================================================================ prosody design


def frame_maps(dur):
    """Token frame spans (40 fps) -> F0 frame spans (80 fps)."""
    c = np.concatenate([[0], np.cumsum(dur)])
    return [(2 * c[i], 2 * c[i + 1]) for i in range(len(dur))]


def smooth_interp(lf, voiced, sigma):
    from scipy.ndimage import gaussian_filter1d
    x = np.arange(len(lf))
    if voiced.sum() < 2:
        return lf.copy()
    li = np.interp(x, x[voiced], lf[voiced])
    return gaussian_filter1d(li, sigma)


def raised_cos(n, c, half):
    x = np.arange(n)
    w = np.clip(1 - np.abs(x - c) / max(1.0, half), 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * w)


def design_f0(f0, fps, spans, stress_spans, R, D, last_word_span, rng_seed=0, active=None):
    """New F0 curve. f0: Hz per frame (0 or tiny = unvoiced); spans: {word: (f_start, f_end)}; stress_spans: {word: (fs, fe, st)}
    with the stressed vowel frames and the accent in semitones; R: register preset (scaled by variant); D: direction."""
    f0 = np.asarray(f0, np.float64)
    n = len(f0)
    v = f0 > 40
    out = f0.copy()
    if v.sum() < 3:
        return out.astype(np.float32)
    lf = np.where(v, np.log2(np.maximum(f0, 1.0)), 0.0)
    ls = smooth_interp(lf, v, sigma=0.03 * fps)
    li = np.interp(np.arange(n), np.where(v)[0], lf[v])
    micro = li - ls
    m = np.median(ls[v])
    tgt = np.log2(R['hz'])
    base = tgt + R['k'] * (ls - m)
    # creak / low-dip lift: compress what falls more than 5 st below the target
    low = tgt - 5 / 12
    dip = base < low
    base[dip] = low + (base[dip] - low) * (1 - R.get('creak', 0.5))
    st = np.zeros(n)
    # declination (deadpan)
    if R.get('decl'):
        vv = np.where(v)[0]
        st[vv[0]:vv[-1] + 1] += np.linspace(R['decl'] / 2, -R['decl'] / 2, vv[-1] - vv[0] + 1)
    # pitch accents: rise to a peak on the stressed vowel, small dip before (L+H*)
    for w, (fs, fe, a) in stress_spans.items():
        c = (fs + fe) / 2
        half = (fe - fs) / 2 + 0.07 * fps
        st += a * raised_cos(n, c, half)
        st -= 0.25 * a * raised_cos(n, c - half - 0.06 * fps, 0.08 * fps)
    # final contour on the last word
    ws, we = last_word_span
    vv = np.where(v[ws:we])[0]
    contour = D.get('contour', 'f')
    if len(vv) > 1:
        a0, a1 = ws + vv[0], ws + vv[-1] + 1
        L = a1 - a0
        ramp = np.linspace(0, 1, L)
        if contour == 'f':
            st[a0:a1] -= R['fall'] * ramp
        elif contour == 'x':
            st[a0:a1] -= 1.3 * R['fall'] * ramp ** 1.5
        elif contour == 'q':
            r = D.get('rise', R['rise'])
            k0 = int(L * 0.35)
            st[a0 + k0:a1] += r * np.linspace(0, 1, L - k0) ** 1.3
        elif contour == 's':
            st[a0:a1] += 1.0 * ramp
        elif contour == 'rf':
            st[a0:a1] += 2.0 * np.sin(np.pi * ramp) - 1.0 * ramp
        elif contour == 'yawn':
            # drawn-out glide: up 2 st then down through the stressed (lengthened) word, low flat tail
            st[a0:a1] -= R['fall'] * ramp
            fs, fe = spans.get(D.get('first_word', 0), (a0, a1))
            vf = np.where(v[fs:fe])[0]
            if len(vf) > 2:
                g0, g1 = fs + vf[0], fs + vf[-1] + 1
                gl = np.linspace(0, 1, g1 - g0)
                st[g0:g1] += 2.5 * np.sin(np.pi * np.minimum(1, gl * 1.6)) - 2.0 * gl
    # nervous tremor (deterministic): 6.5 Hz, slowly varying depth
    if R.get('tremor'):
        t = np.arange(n) / fps
        st += R['tremor'] * np.sin(2 * np.pi * 6.5 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t + 1.0))
    lf2 = base + st / 12 + R.get('micro', 0.8) * micro
    ratio = 2 ** (lf2 - li)
    from scipy.ndimage import gaussian_filter1d
    ratio = 2 ** gaussian_filter1d(np.log2(ratio), 1.0)
    # sub-pitch creak (a decay at 30-50 Hz into a fricative or a pause) is not modal voice: scaled by the register
    # ratio it became an audible extra vowel ("ish" -> "is it"). Frames under half the line median keep their pitch.
    fmed = float(np.median(f0[v]))
    wc = np.clip((f0 - 0.5 * fmed) / (0.25 * fmed), 0.0, 1.0)
    ratio = 2 ** (wc * np.log2(ratio))
    if active is not None:
        # only the words are re-pitched: outside them Kokoro's faint pre-voicing / end creak keeps its own pitch (raised,
        # it became an audible hum before the line and a 60 Hz creak after it); 50 ms ramps at the edges
        a_, b_ = int(active[0]), int(active[1])
        w = np.zeros(n)
        w[max(0, a_):min(n, b_)] = 1.0
        r = max(1, int(0.05 * fps))
        for k in range(1, r + 1):
            x = 0.5 - 0.5 * np.cos(np.pi * (r - k) / r)
            if 0 <= a_ - k < n:
                w[a_ - k] = max(w[a_ - k], x)
            if 0 <= b_ + k - 1 < n:
                w[b_ + k - 1] = max(w[b_ + k - 1], x)
        ratio = 2 ** (w * np.log2(ratio))
    # The decoder's source treats F0 > 10 Hz as voiced (sine excitation, little noise) and <= 10 Hz as unvoiced (noise).
    # Each frame keeps its voicing state: unvoiced frames are left exactly as predicted (else a 's' loses its noise),
    # voiced ones are scaled but never pushed under the threshold.
    out = np.where(f0 > 10, np.maximum(10.5, f0 * ratio), f0)
    out = np.where(v, np.clip(out, 55, 600), out)
    return out.astype(np.float32)


def reg_for(role, tag):
    t = tag if (role, tag) in REGS else 'default'
    if role == 'N':
        t = 'DEADPAN' if tag.upper().startswith('DEAD') else 'HYPE'
    return dict(REGS[(role, t)]), t


def merge_dir(lid, role, tag, text):
    D = dict(DIRECTION.get(lid, {}))
    D.setdefault('say', tts_text(text))
    D['say'] = tts_text(D['say'])
    if 'stress' not in D:              # default: capitalised words + the last content word
        D['stress'] = {w: 4.0 for w in re.findall(r"\b[A-Z][A-Z']+\b", text) if w != 'I'}
    D.setdefault('contour', 'q' if text.strip().endswith('?') else ('x' if '!' in text else 'f'))
    if 'beat' not in D:
        D['beat'] = {}
        for m in re.finditer(r"([A-Za-z']+)\s*\.\.\.\s*\S", text):
            D['beat'][m.group(1)] = None
    return D


class Take:
    pass


def plan(E, role, tag, text, lid=None, variant='mid', overrides=None, voice=None):
    """Durations, F0 and loudness plan for one line (approach e). Returns a Take with P (prediction), f0, amp envelope."""
    R, regname = reg_for(role, tag)
    for k_, v_ in VARIANTS[variant].items():
        R[k_] = R[k_] * v_
    if overrides:
        R.update(overrides)
    D = merge_dir(lid, role, tag, text)
    lang = ROLES[role]['lang']
    vspec = voice or ROLES[role]['voice']
    say = D['say']
    if D.get('carrier'):
        # very short lines ("Ish.", "Prove it.") read badly on their own (odd style row, stray onset vowel): render them
        # after a carrier phrase and a long beat, then cut the carrier off inside the beat
        say = D['carrier'] + ' ' + say[0].lower() + say[1:] if say[:1] != 'I' else D['carrier'] + ' ' + say
        D['beat'] = dict(D.get('beat', {}), **{re.findall(r"[A-Za-z']+", D['carrier'])[-1]: 0.6})
    lay = layout(E, say, lang)
    nt = len(lay['chars'])
    words = lay['words']
    n_carrier = len(re.findall(r"[A-Za-z0-9']+", D.get('carrier', '')))
    # 1) speed from the target rate, measured on the plain prediction (speech frames only)
    P0 = E.predict(lay['ph'], vspec, 1.0)
    sp_frames = sum(d for i, d in enumerate(P0['dur']) if lay['tok_word'][i] >= n_carrier)
    n_words = len(VI.script_words(text)[1])
    wpm1 = WPM_CAL * 60 * n_words / max(0.1, sp_frames / DFPS)     # ~ what voice_ingest measures as wpm_voiced
    wpm_t = D.get('wpm', R['wpm'])
    speed = float(np.clip(wpm_t / wpm1, 0.55, 1.25))
    P1 = E.predict(lay['ph'], vspec, speed)
    # 2) duration multipliers: lengthened words (stressed vowel x f, rest of word x sqrt f), beats after words
    dm = np.ones(nt, np.float32)
    for key, f in D.get('len', {}).items():
        wi = word_key(text, words, key)
        if wi is None:
            continue
        idx = [i for i in range(nt) if lay['tok_word'][i] == wi]
        vs, ve = lay['stress_tok'].get(wi, (None, None))
        for i in idx:
            dm[i] *= f if (vs is not None and vs <= i <= ve) else np.sqrt(f)
    beats = dict(D.get('beat', {}))
    pz = R['pause']
    # punctuation runs after a word: '...' -> pause[0], '.!?;:' -> pause[1], ',' -> pause[2] (unless given)
    beat_toks = []
    i = 1
    while i < nt - 1:
        c = lay['chars'][i]
        if c in '.,!?;:…—':
            j = i
            while j + 1 < nt - 1 and lay['chars'][j + 1] in '.,!?;:…— ':
                j += 1
            run = ''.join(lay['chars'][i:j + 1])
            prev_w = max([lay['tok_word'][k] for k in range(1, i)] + [-1])
            is_final = all(lay['tok_word'][k] < 0 for k in range(j + 1, nt))
            # Kokoro parks the pause inside the last phoneme before punctuation (a 0.6 s 's' or 'n'); clip it to a
            # normal length so the pause sits in the punctuation tokens, where we set it
            p_ = i - 1
            while p_ > 0 and lay['chars'][p_] in 'ˈˌː':
                p_ -= 1
            # (line-final obstruents keep their length: the model fades the ending inside it, and clipping it swallows
            #  the last 's'/'z'; a final nasal or vowel is clipped so a raised F0 cannot turn it into a long hum)
            if p_ > 0 and P1['dur'][p_] > 6 and not (is_final and lay['chars'][p_] not in VOWELS and lay['chars'][p_] not in 'mnŋlɹ'):
                dm[p_] *= (8.0 if is_final else 5.0) / P1['dur'][p_]
            # the line-final punctuation keeps its predicted length: the decoder renders the last consonant partly in
            # those frames (shortening them loses the final 's' of "planet's"); the silence is trimmed when conforming
            if not is_final:
                beat_toks.append((i, j))
                want = pz[0] if '...' in run or '…' in run else (pz[1] if re.search(r'[.!?;:]', run) else pz[2])
                for key, val in beats.items():
                    wi = word_key(text, words, key)
                    if wi == prev_w and val is not None:
                        want = val
                cur = sum(P1['dur'][i:j + 1]) / DFPS
                f = want / max(cur, 1.0 / DFPS)
                for k in range(i, j + 1):
                    dm[k] *= f
            i = j + 1
        else:
            i += 1
    # beats requested after a word with no punctuation: lengthen the following space
    for key, val in beats.items():
        if val is None:
            continue
        wi = word_key(text, words, key)
        if wi is None:
            continue
        last = max([k for k in range(nt) if lay['tok_word'][k] == wi], default=None)
        if last is not None and last + 1 < nt - 1 and lay['chars'][last + 1] == ' ':
            cur = P1['dur'][last + 1] / DFPS
            if cur < val * 0.7:
                dm[last + 1] *= val / max(cur, 1.0 / DFPS)
                beat_toks.append((last + 1, last + 1))
    P = E.predict(lay['ph'], vspec, speed, dm[None, :])
    # 3) F0 plan
    fsp = frame_maps(P['dur'])
    spans = {}
    for wi in range(len(words)):
        idx = [k for k in range(nt) if lay['tok_word'][k] == wi]
        if idx:
            spans[wi] = (fsp[idx[0]][0], fsp[idx[-1]][1])
    stress_spans = {}
    for key, a in D.get('stress', {}).items():
        wi = word_key(text, words, key)
        if wi is None or wi not in lay['stress_tok']:
            continue
        vs, ve = lay['stress_tok'][wi]
        stress_spans[wi] = (fsp[vs][0], fsp[ve][1], a * R['acc'] / max(1e-6, REGS[(role, regname)]['acc']) if R['acc'] else 0.0)
    last_w = max(spans) if spans else 0
    D['first_word'] = n_carrier
    line_words = [k for k in spans if k >= n_carrier]
    act = (spans[min(line_words)][0] - 2, spans[last_w][1] + 4) if line_words else None
    f0 = design_f0(P['f0'], FFPS, spans, stress_spans, R, D, spans.get(last_w, (0, len(P['f0']))), active=act)
    # energy: effort raises N a little on voiced frames (brighter, pressed). Crisp consonants: N (log energy) +0.3 on
    # sibilants and +1.0 on the line-final obstruent and the frames after it, where the decoder renders it (without
    # it ASR hears "planet" for "planet's")
    N = P['N'].copy()
    if R.get('effort'):
        N = N + 0.35 * R['effort'] * (P['f0'] > 40)
    # (only unvoiced frames: that is the fricative noise; boosting the voiced decay inside the token makes a buzz)
    uvm = (P['f0'] <= 10).astype(np.float32)
    for i in range(1, nt - 1):
        if lay['chars'][i] in 'szʃʒ':
            sl = slice(fsp[i][0], fsp[i][1])
            N[sl] += R.get('crisp', 0.3) * uvm[sl]
    # onset cleanup: Kokoro sometimes pre-voices the leading pad before an unvoiced onset ("Who" -> "Oh, who"); with a
    # raised F0 that pre-voicing becomes an audible extra syllable. Before an unvoiced first phoneme, the pad is unvoiced.
    first = next((i for i in range(1, nt) if lay['tok_word'][i] >= n_carrier and lay['chars'][i] not in 'ˈˌ'), None)
    if first is not None and lay['chars'][first] in 'hptkfsθʃʧ' and not n_carrier:
        e_ = max(0, fsp[first][0] - 2)
        f0[:e_] = np.where(f0[:e_] > 10, 0.0, f0[:e_])
        N[:e_] = np.minimum(N[:e_], -6.0)
    # lead/tail cleanup: voiced frames far before the first word (> 50 ms) or long after the last one (> 0.2 s) are a
    # faint hum or end creak, not speech; they are made silent (unvoiced frames, e.g. a final 's', are kept)
    if line_words:
        lead_end = spans[min(line_words)][0] - 4
        tail_start = spans[last_w][1] + int(0.2 * FFPS)
        for sl in (slice(0, max(0, lead_end)), slice(min(len(f0), tail_start), len(f0))):
            vz = f0[sl] > 10
            f0[sl] = np.where(vz, 0.0, f0[sl])
            N[sl] = np.where(vz, np.minimum(N[sl], -8.5), N[sl])
    # no re-voicing after the line's last fricative: once the F0 has gone unvoiced inside the final obstruent token,
    # a later voiced blip is spurious (it turned "ish" into "is it")
    fin_ = [i for i in range(1, nt - 1) if lay['tok_word'][i] >= 0]
    if fin_ and lay['chars'][fin_[-1]] in 'szʃʒfvθðtdkpbg':
        a0 = fsp[fin_[-1]][0]
        run = 0
        k0 = None
        for k_ in range(a0, len(f0)):
            run = run + 1 if f0[k_] <= 10 else 0
            if run >= 3:
                k0 = k_
                break
        if k0 is not None:
            vz = f0[k0:] > 10
            f0[k0:] = np.where(vz, 0.0, f0[k0:])
            N[k0:] = np.where(vz, np.minimum(N[k0:], -8.5), N[k0:])
    # beats are real silences: a stretched comma or space is not silent in Kokoro (the decoder fills it with a voiced
    # vowel: "First, the" -> "First are the"). Keep 3 frames for the release of the consonant before and 2 for the
    # onset after, silence the rest.
    for a_, b_ in beat_toks:
        s0, s1 = fsp[a_][0] + 3, fsp[b_][1] - 2
        if s1 > s0:
            f0[s0:s1] = np.where(f0[s0:s1] > 10, 0.0, f0[s0:s1])
            N[s0:s1] = np.minimum(N[s0:s1], -8.5)
    fin = [i for i in range(1, nt - 1) if lay['tok_word'][i] >= 0]
    if fin and lay['chars'][fin[-1]] in 'szʃʒfvθðtdkpbg':
        sl = slice(fsp[fin[-1]][0], fsp[min(nt - 1, fin[-1] + 1)][1])
        N[sl] += R.get('crisp_final', 1.0) * uvm[sl]
    T = Take()
    T.P, T.f0, T.N, T.lay, T.R, T.D, T.spans, T.stress_spans = P, f0, N, lay, R, D, spans, stress_spans
    T.role, T.tag, T.text, T.reg, T.speed, T.voice = role, tag, text, regname, speed, vspec
    # loudness plan (dB) per word, applied after rendering
    amp = []
    for wi, (fs, fe, a) in stress_spans.items():
        if a > 0:
            amp.append((spans[wi][0] / FFPS, spans[wi][1] / FFPS, R['amp'] * min(1.0, a / 4.0)))
    for key, db in D.get('soft', {}).items():
        wi = word_key(text, words, key)
        if wi is not None and wi in spans:
            amp.append((spans[wi][0] / FFPS, spans[wi][1] / FFPS, db))
    T.amp = amp
    T.cut = 0.0
    if n_carrier and n_carrier in spans:
        # cut 0.12 s before the first line word: inside the 0.6 s beat after the carrier
        T.cut = max(0.0, spans[n_carrier][0] / FFPS - 0.12)
    return T


def amp_env(n, sr, amp, ramp=0.04):
    g = np.zeros(n)
    t = np.arange(n) / sr
    for s, e, db in amp:
        w = np.clip(np.minimum((t - s + ramp) / ramp, (e + ramp - t) / ramp), 0, 1)
        g += db * (0.5 - 0.5 * np.cos(np.pi * w))
    return 10 ** (g / 20)

# ================================================================================================ finishing


def biquad(kind, f, sr, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f / sr
    cs, sn = np.cos(w), np.sin(w)
    al = sn / (2 * q)
    if kind == 'peak':
        b = [1 + al * A, -2 * cs, 1 - al * A]
        a = [1 + al / A, -2 * cs, 1 - al / A]
    elif kind == 'hs':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cs + sq), -2 * A * ((A - 1) + (A + 1) * cs), A * ((A + 1) + (A - 1) * cs - sq)]
        a = [(A + 1) - (A - 1) * cs + sq, 2 * ((A - 1) - (A + 1) * cs), (A + 1) - (A - 1) * cs - sq]
    elif kind == 'ls':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cs + sq), 2 * A * ((A - 1) - (A + 1) * cs), A * ((A + 1) - (A - 1) * cs - sq)]
        a = [(A + 1) + (A - 1) * cs + sq, -2 * ((A - 1) + (A + 1) * cs), (A + 1) + (A - 1) * cs - sq]
    elif kind == 'hp':
        b = [(1 + cs) / 2, -(1 + cs), (1 + cs) / 2]
        a = [1 + al, -2 * cs, 1 - al]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def eq(y, sr, name):
    from scipy.signal import lfilter
    chains = {
        'bright': [('hp', 70, 0, 0.7), ('ls', 180, 1.0, 0.7), ('peak', 3200, 2.5, 0.9), ('hs', 7000, 1.5, 0.7)],
        'warm':   [('hp', 60, 0, 0.7), ('ls', 160, 2.0, 0.7), ('peak', 3000, 0.5, 0.9), ('hs', 8000, -1.0, 0.7)],
        'clean':  [('hp', 90, 0, 0.7), ('peak', 250, -1.5, 1.0), ('peak', 3500, 1.5, 0.9)],
        'kid':    [('hp', 110, 0, 0.7), ('ls', 250, -2.0, 0.7), ('peak', 2800, 2.0, 0.9), ('hs', 7500, 1.0, 0.7)],
        'shout':  [('hp', 90, 0, 0.7), ('ls', 220, -2.5, 0.7), ('peak', 1800, 2.0, 0.8), ('peak', 3200, 4.0, 1.0)],
        'none':   [],
    }
    for kind, f, g, q in chains[name]:
        b, a = biquad(kind, f, sr, g, q)
        y = lfilter(b, a, y)
    return y.astype(np.float32)


def strain(y, sr, drive=2.2, mix=0.35):
    """Shout strain: band-limited soft saturation blended in (adds the pressed, buzzy upper harmonics of a yell)."""
    from scipy.signal import lfilter
    b, a = biquad('hp', 700, sr, 0, 0.7)
    x = lfilter(b, a, y)
    pk = np.abs(x).max() + 1e-9
    s = np.tanh(drive * x / pk) * pk / np.tanh(drive)
    return (y + mix * (s - x)).astype(np.float32)


def formant_shift(y, sr, ratio):
    """Praat 'Change gender' with the pitch left alone: formants x ratio (shorter vocal tract)."""
    import parselmouth
    from parselmouth.praat import call
    if abs(ratio - 1) < 1e-3:
        return y
    snd = parselmouth.Sound(y.astype(np.float64), sampling_frequency=sr)
    out = call(snd, 'Change gender', 75, 600, float(ratio), 0.0, 1.0, 1.0)
    z = out.values[0].astype(np.float32)
    return z[:len(y)] if len(z) >= len(y) else np.pad(z, (0, len(y) - len(z)))


def finish(T, a):
    y = a * amp_env(len(a), SR, T.amp).astype(np.float32)
    fr = ROLES[T.role].get('formant', 1.0)
    if fr != 1.0:
        y = formant_shift(y, SR, fr)
    if T.R.get('effort'):
        y = strain(y, SR)
    y = eq(y, SR, T.R.get('eq', 'none'))
    return y

# ================================================================================================ approaches


def approach_e(E, role, tag, text, lid, variant='mid', **kw):
    T = plan(E, role, tag, text, lid, variant, **kw)
    a = E.render(T.P, T.f0, T.N)
    return cut_carrier(finish(T, a), T), T


def cut_carrier(y, T):
    if not getattr(T, 'cut', 0):
        return y
    i = int(T.cut * SR)
    z = y[i:].copy()
    f = int(0.01 * SR)
    z[:f] *= np.linspace(0, 1, f)
    return z


def approach_a(E, role, tag, text, lid, split=False, voice=None):
    """Plain Kokoro: role voice, rate-matched speed, text shaping (caps lowered, !/? kept, '...' beats). split=True renders
    phrases apart and joins them with designed pauses."""
    R, _ = reg_for(role, tag)
    D = merge_dir(lid, role, tag, text)
    lang = ROLES[role]['lang']
    vspec = voice or ROLES[role]['voice']
    say = D['say']
    if role == 'N' and not tag.upper().startswith('DEAD'):
        say = re.sub(r'\.$', '!', say)          # hype: end on '!' for more energy
    T = plan(E, role, tag, text, lid)
    speed = T.speed
    if not split:
        if T.cut:                              # carrier lines: same carrier, plain prosody
            P = E.predict(T.lay['ph'], vspec, speed)
            return cut_carrier(eq(E.render(P), SR, R.get('eq', 'none')), T), P
        P = E.predict(E.phonemize(say, lang), vspec, speed)
        return eq(E.render(P), SR, R.get('eq', 'none')), P
    parts = [p.strip() for p in re.split(r'(?<=\.\.\.)|(?<=[.!?])\s+', say) if p and p.strip()]
    out = []
    for i, p in enumerate(parts):
        P = E.predict(E.phonemize(p, lang), vspec, speed)
        z = VI.trim_handles(E.render(P), SR, 0.02)
        out.append(z)
        if i < len(parts) - 1:
            gap = R['pause'][0] if p.endswith('...') else R['pause'][1]
            out.append(np.zeros(int(gap * SR), np.float32))
    return eq(np.concatenate(out), SR, R.get('eq', 'none')), None


def warp_map(T_plain_dur, dm):
    """Source/target time anchors (s) for a per-token duration change, from the plain durations (40 fps)."""
    src = np.concatenate([[0], np.cumsum(T_plain_dur)]) / DFPS
    dst = np.concatenate([[0], np.cumsum(np.asarray(T_plain_dur) * np.asarray(dm))]) / DFPS
    return src, dst


def approach_b(E, role, tag, text, lid, method='psola', variant='mid'):
    """Post-processing: render the plain line (same speed/voice), then impose the same direction afterwards with
    Praat PSOLA (Manipulation: PitchTier + DurationTier) or WORLD (harvest/cheaptrick/d4c, frame warping)."""
    T = plan(E, role, tag, text, lid, variant)
    Pp = E.predict(T.lay['ph'], T.voice, T.speed)            # plain durations at the same speed
    a = E.render(Pp)
    dm = T.P['dur'] / np.maximum(1, Pp['dur'])               # realised duration factors
    src, dst = warp_map(Pp['dur'], dm)
    # target F0 on the plain time base: designed on the plain prediction with the plain spans
    fsp = frame_maps(Pp['dur'])
    nt = len(T.lay['chars'])
    spans = {}
    for wi in range(len(T.lay['words'])):
        idx = [k for k in range(nt) if T.lay['tok_word'][k] == wi]
        if idx:
            spans[wi] = (fsp[idx[0]][0], fsp[idx[-1]][1])
    ss = {wi: (fsp[T.lay['stress_tok'][wi][0]][0], fsp[T.lay['stress_tok'][wi][1]][1], a_) for wi, (_, _, a_) in T.stress_spans.items()}
    if method == 'psola':
        import parselmouth
        from parselmouth.praat import call
        snd = parselmouth.Sound(a.astype(np.float64), sampling_frequency=SR)
        pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=600)
        f0a = pitch.selected_array['frequency']
        ta = pitch.xs()
        fps = 100
        # analysis frames -> model frame spans (scale 80 fps spans to 100 fps, offset by first frame time)
        sc = fps / FFPS
        off = ta[0] * fps
        sp2 = {k: (int(s * sc - off), int(e * sc - off)) for k, (s, e) in spans.items()}
        ss2 = {k: (int(s * sc - off), int(e * sc - off), a_) for k, (s, e, a_) in ss.items()}
        last = max(sp2) if sp2 else 0
        f0n = design_f0(f0a, fps, sp2, ss2, T.R, T.D, sp2.get(last, (0, len(f0a))),
                        active=(sp2[min(sp2)][0] - 2, sp2[last][1] + 5) if sp2 else None)
        manip = call(snd, 'To Manipulation', 0.01, 60, 600)
        pt = call('Create PitchTier', 'pt', 0, snd.duration)
        for t_, f_ in zip(ta, f0n):
            if f_ > 40:
                call(pt, 'Add point', float(t_), float(f_))
        call([manip, pt], 'Replace pitch tier')
        dt = call('Create DurationTier', 'dt', 0, snd.duration)
        for k in range(len(dm)):
            s0, s1 = src[k], src[k + 1]
            if s1 - s0 <= 0:
                continue
            call(dt, 'Add point', float(s0 + 1e-4), float(dm[k]))
            call(dt, 'Add point', float(s1 - 1e-4), float(dm[k]))
        call([manip, dt], 'Replace duration tier')
        out = call(manip, 'Get resynthesis (overlap-add)')
        y = out.values[0].astype(np.float32)
    else:
        import pyworld as pw
        x = a.astype(np.float64)
        fp = 5.0
        f0w, tw = pw.harvest(x, SR, f0_floor=60, f0_ceil=600, frame_period=fp)
        spw = pw.cheaptrick(x, f0w, tw, SR)
        apw = pw.d4c(x, f0w, tw, SR)
        fps = 1000 / fp
        sc = fps / FFPS
        sp2 = {k: (int(s * sc), int(e * sc)) for k, (s, e) in spans.items()}
        ss2 = {k: (int(s * sc), int(e * sc), a_) for k, (s, e, a_) in ss.items()}
        last = max(sp2) if sp2 else 0
        f0n = design_f0(f0w, fps, sp2, ss2, T.R, T.D, sp2.get(last, (0, len(f0w))),
                        active=(sp2[min(sp2)][0] - 3, sp2[last][1] + 6) if sp2 else None).astype(np.float64)
        # time warp: output frame times -> source times
        tout = np.arange(0, dst[-1], fp / 1000)
        tsrc = np.interp(tout, dst, src)
        fi = np.clip(tsrc * fps, 0, len(f0w) - 1)
        i0 = np.floor(fi).astype(int)
        i1 = np.minimum(i0 + 1, len(f0w) - 1)
        fr = (fi - i0)[:, None]
        spn = np.exp((1 - fr) * np.log(spw[i0] + 1e-12) + fr * np.log(spw[i1] + 1e-12))
        apn = (1 - fr) * apw[i0] + fr * apw[i1]
        f0o = np.where((f0n[i0] > 0) & (f0n[i1] > 0), (1 - fr[:, 0]) * f0n[i0] + fr[:, 0] * f0n[i1], 0.0)
        y = pw.synthesize(np.ascontiguousarray(f0o), np.ascontiguousarray(spn), np.ascontiguousarray(apn), SR, fp).astype(np.float32)
    # the loudness plan (T.amp) is on the designed time base, which the warp reproduces (dst)
    return cut_carrier(finish(T, y), T), T


_POCKET = {}


def approach_c(prompt, prompt_sr, text, speed=1.0, temperature=0.7):
    """Pocket TTS (Kyutai, sherpa-onnx export) zero-shot, prompted with our own stock-derived expressive audio."""
    import sherpa_onnx
    if 'tts' not in _POCKET:
        d = POCKET_DIR + '/'
        _POCKET['tts'] = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            pocket=sherpa_onnx.OfflineTtsPocketModelConfig(lm_flow=d + 'lm_flow.onnx', lm_main=d + 'lm_main.onnx', encoder=d + 'encoder.onnx',
                                                          decoder=d + 'decoder.onnx', text_conditioner=d + 'text_conditioner.onnx',
                                                          vocab_json=d + 'vocab.json', token_scores_json=d + 'token_scores.json'), num_threads=4)))
    g = sherpa_onnx.GenerationConfig()
    g.speed = float(speed)
    g.reference_audio = prompt.astype(np.float32).tolist()
    g.reference_sample_rate = int(prompt_sr)
    g.extra = {'temperature': str(temperature), 'max_reference_audio_len': '12'}
    r = _POCKET['tts'].generate(text, g)
    return np.asarray(r.samples, np.float32), r.sample_rate

# ================================================================================================ scoring


def score(met, role, reg, n_words, base=None):
    """0..1 sub-scores and a total that rewards acting without artifacts. base = metrics of the plain take (a)."""
    s = {}
    acc = met.get('word_acc', 0)
    s['intel'] = 1.0 if acc >= 0.999 else max(0.0, acc - 0.3)
    f0 = met.get('f0_med') or 1.0
    R = REGS.get((role, reg)) or REGS.get((role, 'default'))
    tgt = R['hz']
    dist = abs(12 * np.log2(f0 / tgt))
    s['register'] = float(np.exp(-(dist / 3.0) ** 2))
    sd = met.get('std_st', 0)
    # targets = the reference measured with the same pitch function (docs/VOICE_LAB.md section 1):
    # narrator hype sd 3.54 st, deadpan 2.00 st; >6.5 st is over-acted / tracking trouble
    if role == 'N' and reg == 'DEADPAN':
        s['movement'] = float(np.exp(-((sd - 2.0) / 1.3) ** 2))
    elif role == 'SYS' and reg == 'calm':
        s['movement'] = float(np.exp(-((sd - 1.6) / 1.2) ** 2))
    else:
        s['movement'] = float(min(1.0, sd / 3.54)) if sd <= 6.5 else float(max(0.0, 1 - (sd - 6.5) / 4))
    w = met.get('wpm_voiced', 0)
    rt = R['wpm']
    s['rate'] = float(np.exp(-((w - rt) / (0.22 * rt)) ** 2)) if n_words >= 3 else 1.0
    q = met.get('dnsmos_ovrl') or 2.5
    s['quality'] = float(np.clip((q - 2.4) / 1.0, 0, 1))
    pen = 0.0
    pen += 0.04 * max(0, met.get('f0_jumps', 0) - (base or {}).get('f0_jumps', 0))
    pen += 0.03 * max(0, met.get('click_frames', 0) - (base or {}).get('click_frames', 0) - 2)
    if base and met.get('hnr_db') is not None and base.get('hnr_db') is not None:
        pen += 0.08 * max(0.0, (base['hnr_db'] - met['hnr_db']) - 1.5)
    if met.get('clipped', 0) > 0:
        pen += 0.5
    s['artifact_pen'] = round(pen, 3)
    expr = 0.55 * s['register'] + 0.45 * s['movement']
    total = 0.35 * expr + 0.30 * s['quality'] + 0.15 * s['rate'] + 0.20 * s['intel'] - pen
    hype_like = (role == 'N' and reg == 'HYPE') or reg in ('cheerful', 'nervous', 'shouting')
    s['gate'] = 'ok'
    if hype_like and n_words > 2 and sd < 2.0:
        s['gate'] = 'reject: hype pitch std < 2 st'
        total -= 1.0
    if acc < 0.75:
        s['gate'] = 'reject: ASR mismatch'
        total -= 1.0
    s['total'] = round(float(total), 4)
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}


# ================================================================================================ lab: all approaches, scored

APPROACHES = ['a1', 'a2', 'b_psola', 'b_world', 'c_pocket', 'e_mild', 'e_mid', 'e_strong', 'e_alt']
APPROACH_TXT = {
    'a1': 'a: plain Kokoro, role voice, rate-matched speed, text shaping (caps lowered, hype ends on "!")',
    'a2': 'a: plain Kokoro, phrases rendered apart and re-joined with designed pauses',
    'b_psola': 'b: plain Kokoro + Praat PSOLA (PitchTier from the direction, DurationTier for lengthening/beats)',
    'b_world': 'b: plain Kokoro + WORLD re-synthesis (designed F0, frame time-warp)',
    'c_pocket': 'c: Pocket TTS zero-shot, prompted with our own e_mid takes of the same role (experiment only, see licence note)',
    'e_mild': 'e: Kokoro native prosody, contour x0.85, accents x0.75',
    'e_mid': 'e: Kokoro native prosody, preset register',
    'e_strong': 'e: Kokoro native prosody, contour x1.18, accents x1.3',
    'e_alt': 'e: Kokoro native prosody with the runner-up voice of the casting scan (voice check)',
}
FINAL_OK = {'a1', 'a2', 'b_psola', 'b_world', 'e_mild', 'e_mid', 'e_strong'}   # licence-clean, role's cast voice
NATIVE_MARGIN = 0.05


def _measure_cand(y, sr, text):
    m, w, vis, emb = VI.measure(y, sr, text)
    return m, emb


def run_lab(ids, approaches=None, out_json=None):
    import soundfile as sf
    approaches = approaches or APPROACHES
    E = Engine()
    SL = script_lines()
    out_json = out_json or os.path.join(LAB_DIR, 'lab.json')
    lab = json.load(open(out_json)) if os.path.exists(out_json) else {}
    embs = {}
    t_all = time.time()
    for lid in ids:
        L = SL[lid]
        role, tag, text = L['role'], L['tag'], L['text']
        if role not in ROLES:
            continue
        reg = reg_for(role, tag)[1]
        n_words = len(VI.script_words(text)[1])
        rec = lab.get(lid, {'id': lid, 'role': role, 'tag': tag, 'reg': reg, 'text': text, 'cands': {}})
        for ap in approaches:
            if ap == 'c_pocket':
                continue
            t0 = time.time()
            try:
                if ap == 'a1':
                    y, _ = approach_a(E, role, tag, text, lid)
                elif ap == 'a2':
                    if not re.search(r'\.\.\.|[.!?]\s+\S', text.strip().lstrip('.')):
                        continue
                    y, _ = approach_a(E, role, tag, text, lid, split=True)
                elif ap.startswith('b_'):
                    y, _ = approach_b(E, role, tag, text, lid, method=ap[2:])
                elif ap == 'e_alt':
                    if not ROLES[role].get('alt'):
                        continue
                    y, _ = approach_e(E, role, tag, text, lid, 'mid', voice=ROLES[role]['alt'])
                else:
                    y, _ = approach_e(E, role, tag, text, lid, ap[2:])
            except Exception as ex:          # a failed candidate is recorded, never fatal
                rec['cands'][ap] = {'error': repr(ex)[:200]}
                continue
            path = os.path.join(LAB_DIR, lid, ap + '.wav')
            y = (y / max(1.0, np.abs(y).max() / 0.98)).astype(np.float32)   # measured as saved (float renders may exceed 1)
            save24(path, y)
            m, emb = _measure_cand(y, SR, text)
            embs[(lid, ap)] = emb
            rec['cands'][ap] = {'file': path, 'metrics': m, 'secs': round(time.time() - t0, 1)}
            print(f"{lid} {ap:9s} f0 {m.get('f0_med')} sd {m.get('std_st')} wpm {m.get('wpm_voiced')} acc {m.get('word_acc')} "
                  f"mos {m.get('dnsmos_ovrl')} hnr {m.get('hnr_db')} | {m.get('asr')}", flush=True)
        lab[lid] = rec
        os.makedirs(LAB_DIR, exist_ok=True)
        json.dump(lab, open(out_json, 'w'), indent=1, default=float)
    # c: Pocket TTS prompted with the role's e_mid takes of OTHER lines (style transfer from our own acted audio)
    if 'c_pocket' in approaches:
        for lid in ids:
            rec = lab.get(lid)
            if not rec:
                continue
            others = [k for k, r in lab.items() if r['role'] == rec['role'] and r.get('reg') == rec.get('reg') and k != lid
                      and 'e_mid' in r['cands'] and 'file' in r['cands']['e_mid']]
            if not others:
                others = [k for k, r in lab.items() if r['role'] == rec['role'] and k != lid and 'file' in r['cands'].get('e_mid', {})]
            if not others and 'file' in rec['cands'].get('e_mid', {}):
                others = [lid]                 # a role with one line (Dad in the hook): prompt with that line's own e_mid
            if not others:
                continue
            pr = []
            for k in others:
                z, _ = VI.load(lab[k]['cands']['e_mid']['file'])
                pr += [VI.trim_handles(z, SR, 0.05), np.zeros(int(0.25 * SR), np.float32)]
                if sum(len(x) for x in pr) > 9 * SR:
                    break
            prompt = np.concatenate(pr)
            t0 = time.time()
            try:
                y, sr = approach_c(prompt, SR, tts_text(rec['text']))
                y = resample_to(y, sr, SR)
            except Exception as ex:
                rec['cands']['c_pocket'] = {'error': repr(ex)[:200]}
                continue
            path = os.path.join(LAB_DIR, lid, 'c_pocket.wav')
            save24(path, y)
            m, emb = _measure_cand(y, SR, rec['text'])
            embs[(lid, 'c_pocket')] = emb
            rec['cands']['c_pocket'] = {'file': path, 'metrics': m, 'secs': round(time.time() - t0, 1)}
            print(f"{lid} c_pocket  f0 {m.get('f0_med')} sd {m.get('std_st')} wpm {m.get('wpm_voiced')} acc {m.get('word_acc')} mos {m.get('dnsmos_ovrl')} | {m.get('asr')}", flush=True)
            json.dump(lab, open(out_json, 'w'), indent=1, default=float)
    # embeddings of candidates measured in earlier runs
    for lid, rec in lab.items():
        for ap, c in rec['cands'].items():
            if 'file' in c and (lid, ap) not in embs and os.path.exists(c['file']):
                z, _ = VI.load(c['file'])
                embs[(lid, ap)] = VI.embed(VI.resample(z, SR, 16000))
    select(lab, embs)
    json.dump(lab, open(out_json, 'w'), indent=1, default=float)
    write_table(lab)
    summarize(lab)
    print('lab done in %.0f s' % (time.time() - t_all))
    return lab


def remeasure_pitch(lab_json, approaches=None):
    """Recompute only the pitch statistics of stored candidates (after a change of the pitch measure)."""
    lab = json.load(open(lab_json))
    for lid, rec in lab.items():
        for ap, c in rec['cands'].items():
            if 'file' not in c or (approaches and ap not in approaches):
                continue
            y, sr = VI.load(c['file'])
            f0, hop = VI.pitch(y, sr)
            c['metrics'].update(VI.pitch_stats(f0, hop))
    json.dump(lab, open(lab_json, 'w'), indent=1, default=float)


def resample_to(y, sr, to):
    return VI.resample(y, sr, to)


def select(lab, embs):
    """Score all candidates; consistency = cosine to the role/register centroid of the e_mid takes; pick the best
    licence-clean candidate per line."""
    cent = {}
    for lid, rec in lab.items():
        e = embs.get((lid, 'e_mid'))
        if e is not None:
            cent.setdefault((rec['role'], rec['reg']), []).append(e)
            cent.setdefault((rec['role'], '*'), []).append(e)
    cent = {k: (np.mean(v, 0) / (np.linalg.norm(np.mean(v, 0)) + 1e-9)) for k, v in cent.items()}
    for lid, rec in lab.items():
        role, reg = rec['role'], rec['reg']
        n_words = len(VI.script_words(rec['text'])[1])
        base = rec['cands'].get('a1', {}).get('metrics')
        best, best_s = None, -9
        for ap, c in rec['cands'].items():
            if 'metrics' not in c:
                continue
            sc = score(c['metrics'], role, reg, n_words, base)
            e = embs.get((lid, ap))
            cr = cent.get((role, reg))
            ca = cent.get((role, '*'))
            if e is not None and cr is not None:
                sim_r, sim_a = float(np.dot(e, cr)), float(np.dot(e, ca))
                sc['spk_sim_reg'], sc['spk_sim_role'] = round(sim_r, 3), round(sim_a, 3)
                sc['consistency'] = round(float(np.clip((sim_r - 0.55) / 0.35, 0, 1)), 3)
                sc['total'] = round(sc['total'] + 0.10 * sc['consistency'], 4)
            c['score'] = sc
            if ap in FINAL_OK and sc['total'] > best_s:
                best, best_s = ap, sc['total']
        # native preference: our measures are noisy at the 0.05 level (DNSMOS, pYIN), and the native render is the
        # role's regenerable recipe, so a post-processed or plain take must beat the best e take by more than that
        nat = [(c['score']['total'], ap) for ap, c in rec['cands'].items() if ap in ('e_mild', 'e_mid', 'e_strong') and 'score' in c]
        if best and not best.startswith('e_') and nat:
            ns, na = max(nat)
            if ns >= best_s - NATIVE_MARGIN and rec['cands'][na]['score'].get('gate', 'ok') == 'ok':
                rec['cands'][best]['score']['note'] = f'beaten by native preference ({na} within {NATIVE_MARGIN})'
                best = na
        rec['chosen'] = best


def write_table(lab, path=None):
    path = path or os.path.join(QA_DIR, 'lab_table.md')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = ['| line | role/reg | approach | F0 med Hz | pitch sd st | range st | wpm voiced | ASR acc | DNSMOS | HNR dB | jitter % | clicks | spk sim | score |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for lid in sorted(lab):
        rec = lab[lid]
        for ap in APPROACHES:
            c = rec['cands'].get(ap)
            if not c or 'metrics' not in c:
                continue
            m, sc = c['metrics'], c.get('score', {})
            star = ' **chosen**' if rec.get('chosen') == ap else ''
            rows.append(f"| {lid} | {rec['role']}/{rec['reg']} | {ap}{star} | {m.get('f0_med')} | {m.get('std_st')} | {m.get('range_st')} | {m.get('wpm_voiced')} | "
                        f"{m.get('word_acc')} | {m.get('dnsmos_ovrl')} | {m.get('hnr_db')} | {m.get('jitter_pct')} | {m.get('click_frames')} | "
                        f"{sc.get('spk_sim_reg', '')} | {sc.get('total', '')}{(' (' + sc['gate'] + ')') if sc.get('gate', 'ok') != 'ok' else ''} |")
    open(path, 'w').write('\n'.join(rows) + '\n')
    return path


def refresh_similarity(json_path=VI.LINES_JSON):
    """Speaker consistency per role: mean cosine of each line's embedding to the role's other lines (and, for N, to the
    other lines of the same register)."""
    lines = json.load(open(json_path))
    E_ = {}
    for L in lines:
        y, sr = VI.load(L['file'])
        E_[L['id']] = VI.embed(VI.resample(y, sr, 16000))
    for L in lines:
        same = [o for o in lines if o['role'] == L['role'] and o['id'] != L['id']]
        if same:
            L['metrics']['spk_sim_role'] = round(float(np.mean([np.dot(E_[L['id']], E_[o['id']]) for o in same])), 3)
        reg = [o for o in same if reg_for(o['role'], o['tag'])[1] == reg_for(L['role'], L['tag'])[1]]
        if reg:
            L['metrics']['spk_sim_reg'] = round(float(np.mean([np.dot(E_[L['id']], E_[o['id']]) for o in reg])), 3)
    with open(json_path, 'w') as f:
        f.write(VI.dumps_lines(lines))


def finalize_from_lab(lab_json=None, ids=None):
    """Write the chosen candidate of each line as the final take (48 kHz, handles, loudness) and voice_lines.json."""
    lab = json.load(open(lab_json or os.path.join(LAB_DIR, 'lab.json')))
    for lid in sorted(lab):
        if ids and lid not in ids:
            continue
        rec = lab[lid]
        ap = rec.get('chosen')
        if not ap:
            print('no candidate for', lid)
            continue
        c = rec['cands'][ap]
        y, sr = VI.load(c['file'])
        alts = {k: v['score']['total'] for k, v in rec['cands'].items() if 'score' in v}
        extra = {'lab_score': c['score'], 'lab_alternatives': alts}
        e = final_write(lid, rec['role'], rec['tag'], rec['text'], y, sr, APPROACH_TXT[ap] + f' [{ap}]', extra)
        m = e['metrics']
        print(f"{lid} -> {ap}: f0 {m.get('f0_med')} sd {m.get('std_st')} wpm {m.get('wpm_voiced')} acc {m.get('word_acc')} mos {m.get('dnsmos_ovrl')} sim {m.get('spk_sim_role')}")
    refresh_similarity()


# ================================================================================================ QA plots

REF_UNITS = VI.SCRATCH + '/study/audio/voice_units.json'
INK, INK2, GRID, SURF = '#1f1f1e', '#5f5e5a', '#e4e3df', '#fcfcfb'
C_CHOSEN, C_PLAIN = '#2a78d6', '#eb6834'       # categorical slots 1 and 2 (dataviz reference palette)


def _f0_track(path):
    y, sr = VI.load(path)
    f0, hop = VI.pitch(y, sr)
    t = np.arange(len(f0)) * hop
    v = ~np.isnan(f0)
    t0 = t[v][0] if v.any() else 0.0
    return t - t0, f0, t0


def plot_contours(ids, lab_json=None, lines_json=VI.LINES_JSON):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    lab = json.load(open(lab_json or os.path.join(LAB_DIR, 'lab.json')))
    lines = {L['id']: L for L in json.load(open(lines_json))}
    os.makedirs(QA_DIR, exist_ok=True)
    outs = []
    for lid in ids:
        rec, L = lab.get(lid), lines.get(lid)
        if not rec or not L or 'file' not in rec['cands'].get('a1', {}):
            continue
        fig, ax = plt.subplots(figsize=(10, 3.8), dpi=150)
        fig.patch.set_facecolor(SURF)
        ax.set_facecolor(SURF)
        ax.axhspan(180, 330, color='#d9d8d3', alpha=0.55, lw=0)
        ax.axhspan(100, 140, color='#ecebe7', alpha=0.9, lw=0)
        ax.text(0.005, 330, ' reference narrator, hype register 180-330 Hz', va='top', fontsize=8, color=INK2, transform=ax.get_yaxis_transform())
        ax.text(0.005, 140, ' deadpan register 100-140 Hz', va='top', fontsize=8, color=INK2, transform=ax.get_yaxis_transform())
        tp, fp, _ = _f0_track(rec['cands']['a1']['file'])
        tc, fc, t0c = _f0_track(L['file'])
        mp, mc = rec['cands']['a1']['metrics'], L['metrics']
        ax.plot(tp, fp, color=C_PLAIN, lw=2, label=f"plain Kokoro (a1): median {mp.get('f0_med')} Hz, sd {mp.get('std_st')} st")
        ax.plot(tc, fc, color=C_CHOSEN, lw=2, label=f"chosen take ({rec.get('chosen')}): median {mc.get('f0_med')} Hz, sd {mc.get('std_st')} st")
        ax.set_yscale('log')
        ax.set_ylim(60, 480)
        ax.set_yticks([70, 100, 140, 200, 280, 400])
        ax.set_yticklabels(['70', '100', '140', '200', '280', '400'])
        ax.minorticks_off()
        xmax = max(np.nanmax(tp[~np.isnan(fp)]) if np.any(~np.isnan(fp)) else 1, np.nanmax(tc[~np.isnan(fc)]) if np.any(~np.isnan(fc)) else 1) + 0.15
        ax.set_xlim(-0.1, xmax)
        for w in L['words']:
            x = w['t'] - t0c
            ax.axvline(x, color=GRID, lw=1, zorder=0)
            ax.text(x + 0.01, 445, w['w'], fontsize=8.5, color=INK, va='top')
        ax.set_xlabel('time from first voiced frame (s); word starts from ASR on the chosen take', fontsize=8.5, color=INK2)
        ax.set_ylabel('F0 (Hz, log)', fontsize=9, color=INK2)
        ax.set_title(f"{lid}  “{L['text']}”  ({L['role']} {L['tag']})", fontsize=10.5, color=INK, loc='left')
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        for sp in ('left', 'bottom'):
            ax.spines[sp].set_color('#bdbcb6')
        ax.tick_params(colors=INK2, labelsize=8)
        ax.legend(loc='lower right', fontsize=8, frameon=False)
        fig.tight_layout()
        out = os.path.join(QA_DIR, f'pitch_{lid}.png')
        fig.savefig(out, facecolor=SURF)
        plt.close(fig)
        outs.append(out)
    # overview: narrator lines vs reference narrator units (register x pitch movement)
    if os.path.exists(REF_UNITS):
        R = [r for r in json.load(open(REF_UNITS)) if r.get('who') == 'NAR' and r.get('f0b')]
        fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
        fig.patch.set_facecolor(SURF)
        ax.set_facecolor(SURF)
        ax.scatter([r['f0b'] for r in R], [r['f0_sd_st'] for r in R], s=18, color='#b9b8b2', label='reference narrator sentence units (n=%d)' % len(R), zorder=1)
        for key, col, lab_ in (('plain', C_PLAIN, 'our narrator lines, plain Kokoro (a1)'), ('chosen', C_CHOSEN, 'our narrator lines, chosen takes')):
            for reg, mk in (('HYPE', 'o'), ('DEADPAN', 's')):
                xs, ys = [], []
                for lid, rec in lab.items():
                    if rec['role'] != 'N' or rec['reg'] != reg:
                        continue
                    m = rec['cands'].get('a1', {}).get('metrics') if key == 'plain' else lines.get(lid, {}).get('metrics')
                    if m and m.get('f0_med'):
                        xs.append(m['f0_med'])
                        ys.append(m['std_st'])
                ax.scatter(xs, ys, s=60, marker=mk, color=col, edgecolor=SURF, linewidth=2, zorder=3,
                           label=f'{lab_}, {reg.lower()} ({"circles" if mk == "o" else "squares"})')
        ax.axhline(2.0, color='#8e8d88', lw=1, ls='--', zorder=0)
        ax.text(62, 2.05, 'hype gate: 2 st', fontsize=8, color=INK2, va='bottom')
        ax.set_xscale('log')
        ax.set_xlim(60, 450)
        ax.set_xticks([70, 100, 140, 200, 280, 400])
        ax.set_xticklabels(['70', '100', '140', '200', '280', '400'])
        ax.minorticks_off()
        ax.set_xlabel('line median F0 (Hz, log)', fontsize=9, color=INK2)
        ax.set_ylabel('within-line pitch sd (semitones)', fontsize=9, color=INK2)
        ax.set_title('Narrator: register and pitch movement, ours vs the reference', fontsize=10.5, color=INK, loc='left')
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.tick_params(colors=INK2, labelsize=8)
        ax.legend(fontsize=7.5, frameon=False, loc='upper right')
        fig.tight_layout()
        out = os.path.join(QA_DIR, 'narrator_register_vs_reference.png')
        fig.savefig(out, facecolor=SURF)
        plt.close(fig)
        outs.append(out)
    return outs



def build_reel(ids, gap=0.35, out=None, lines_json=VI.LINES_JSON):
    """All final takes in script order with short gaps: one file to audition the cast (48 kHz, 24-bit)."""
    import soundfile as sf
    lines = {L['id']: L for L in json.load(open(lines_json))}
    parts, cues, t = [], [], 0.0
    for lid in ids:
        L = lines.get(lid)
        if not L or not os.path.exists(L['file']):
            continue
        y, sr = VI.load(L['file'])
        parts += [y, np.zeros(int(gap * sr), np.float32)]
        cues.append(f"{t:7.2f}  {lid}  {L['role']:4s} {L['tag']:9s} {L['text']}")
        t += len(y) / sr + gap
    out = out or os.path.join(QA_DIR, 'hook_voice_reel.wav')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sf.write(out, np.concatenate(parts), VI.SR_OUT, subtype='PCM_24')
    open(out[:-4] + '_cues.txt', 'w').write('\n'.join(cues) + '\n')
    return out



def summarize(lab, path=None):
    """Per approach x role/register: medians of pitch and rate, means of quality, gate passes, score."""
    path = path or os.path.join(QA_DIR, 'lab_summary.md')
    groups = [('N', 'HYPE'), ('N', 'DEADPAN'), ('SYS', '*'), ('SAM', '*'), ('DAD', '*')]
    out = ['| group | approach | lines | F0 median Hz | pitch sd st (median) | range st | wpm voiced | ASR acc | DNSMOS ovrl | HNR dB | jitter % | spk sim (reg) | hype gate pass | mean score | chosen |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for role, reg in groups:
        recs = [r for r in lab.values() if r['role'] == role and (reg == '*' or r['reg'] == reg)]
        if not recs:
            continue
        for ap in APPROACHES:
            ms = [(r, r['cands'][ap]) for r in recs if 'metrics' in r['cands'].get(ap, {})]
            if not ms:
                continue
            M = [c['metrics'] for _, c in ms]
            S = [c.get('score', {}) for _, c in ms]

            def med(k):
                v = [m.get(k) for m in M if m.get(k) is not None]
                return round(float(np.median(v)), 2) if v else ''

            def mean(k, src=M):
                v = [max(0.0, m.get(k)) if k == 'word_acc' else m.get(k) for m in src if isinstance(m.get(k), (int, float))]
                return round(float(np.mean(v)), 3) if v else ''
            gate = [s_.get('gate', 'ok') == 'ok' for s_ in S]
            ch = sum(1 for r, _ in ms if r.get('chosen') == ap)
            out.append(f"| {role}/{reg} | {ap} | {len(ms)} | {med('f0_med')} | {med('std_st')} | {med('range_st')} | {med('wpm_voiced')} | {mean('word_acc')} | "
                       f"{mean('dnsmos_ovrl')} | {mean('hnr_db')} | {mean('jitter_pct')} | {mean('spk_sim_reg', S)} | {sum(gate)}/{len(gate)} | {mean('total', S)} | {ch} |")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write('\n'.join(out) + '\n')
    return path

# ================================================================================================ io / runs


def script_lines():
    return {L['id']: L for L in json.load(open(SCRIPT_JSON))}


def save24(path, y, sr=SR):
    import soundfile as sf
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sf.write(path, (y / max(1.0, np.abs(y).max() / 0.98)).astype(np.float32), sr, subtype='PCM_16')


def final_write(lid, role, tag, text, y, sr, approach, extra=None, json_path=VI.LINES_JSON):
    import soundfile as sf
    yc, src = VI.conform(y, sr, role)
    out = os.path.join(VI.VOICE_DIR, f'{lid}_{role}.wav')
    os.makedirs(VI.VOICE_DIR, exist_ok=True)
    sf.write(out, yc, src, subtype='PCM_24')
    e, emb = VI.entry(lid, role, tag, text, out, yc, src, approach, extra)
    VI.update_json(e, json_path, emb)
    return e


def describe(T, variant):
    v = T.voice if isinstance(T.voice, str) else json.dumps(T.voice)
    return (f"e: Kokoro native prosody ({v}), register {T.role}/{T.reg} hz={T.R['hz']:.0f} k={T.R['k']:.2f} "
            f"acc={T.R['acc']:.1f}st speed={T.speed:.2f} variant={variant}" + (f", formant x{ROLES[T.role]['formant']}" if ROLES[T.role].get('formant') else ''))


def run_final(ids, E=None):
    E = E or Engine()
    SL = script_lines()
    for lid in ids:
        L = SL[lid]
        role, tag, text = L['role'], L['tag'], L['text']
        if role not in ROLES:
            print('skip (no recipe for role)', lid, role)
            continue
        reg = reg_for(role, tag)[1]
        rc = RECIPE.get(lid, RECIPE.get((role, reg), RECIPE['default']))
        ap = rc.get('approach', 'e_mid')
        if ap.startswith('e_'):
            y, T = approach_e(E, role, tag, text, lid, ap[2:])
            desc = describe(T, ap[2:]) + f' [{ap}]'
        elif ap.startswith('b_'):
            y, T = approach_b(E, role, tag, text, lid, method=ap[2:])
            desc = APPROACH_TXT[ap] + f' [{ap}]'
        else:
            y, _ = approach_a(E, role, tag, text, lid, split=(ap == 'a2'))
            desc = APPROACH_TXT[ap] + f' [{ap}]'
        e = final_write(lid, role, tag, text, y, SR, desc, {'recipe': rc})
        m = e['metrics']
        print(f"{lid} {role:3s} {tag:9s} f0 {m.get('f0_med')} sd {m.get('std_st')} wpm {m.get('wpm_voiced')} acc {m.get('word_acc')} mos {m.get('dnsmos_ovrl')} | {m.get('asr')}", flush=True)
    refresh_similarity()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ids', default='')
    ap.add_argument('--hook', action='store_true')
    ap.add_argument('--scene', default='')
    ap.add_argument('--lab', action='store_true', help='build and score every candidate approach (voice/lab/, voice/qa/lab_table.md)')
    ap.add_argument('--lab-json', default='', help='lab results file (default voice/lab/lab.json); lets lab runs go in parallel')
    ap.add_argument('--merge', default='', help='comma list of lab json files to merge into voice/lab/lab.json before --lab/--finalize')
    ap.add_argument('--approaches', default='', help='comma list for --lab (default: ' + ','.join(APPROACHES) + ')')
    ap.add_argument('--reel', action='store_true', help='concatenate the final takes (ids or the hook) into voice/qa/hook_voice_reel.wav')
    ap.add_argument('--remeasure-pitch', default='', help='lab json: recompute pitch stats of the stored candidates')
    ap.add_argument('--plots', default='', help='comma list of ids: pitch-contour PNGs (plain vs chosen) in voice/qa/')
    ap.add_argument('--finalize', action='store_true', help='write the lab-chosen take of each line as the final file + json')
    ap.add_argument('--say', default='')
    ap.add_argument('--role', default='N')
    ap.add_argument('--tag', default='HYPE')
    ap.add_argument('--variant', default='mid')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    ids = [x for x in a.ids.split(',') if x]
    if a.hook:
        ids += HOOK_IDS
    if a.scene:
        ids += [k for k, L in script_lines().items() if k.startswith(a.scene + '-') and L['role'] in ROLES]
    if a.say:
        E = Engine()
        y, T = approach_e(E, a.role, a.tag, a.say, None, a.variant)
        yc, sr = VI.conform(y, SR, a.role)
        import soundfile as sf
        sf.write(a.out or 'say.wav', yc, sr, subtype='PCM_24')
        print(describe(T, a.variant), '->', a.out or 'say.wav')
        return
    if a.remeasure_pitch:
        remeasure_pitch(a.remeasure_pitch, [x for x in a.approaches.split(',') if x] or None)
        return
    if a.plots:
        for o in plot_contours([x for x in a.plots.split(',') if x]):
            print(o)
        return
    if a.reel:
        print(build_reel(ids or HOOK_IDS))
        return
    if a.merge:
        merged = {}
        for f in a.merge.split(','):
            for k, r in json.load(open(f)).items():
                if k in merged:
                    merged[k]['cands'].update(r['cands'])
                else:
                    merged[k] = r
        os.makedirs(LAB_DIR, exist_ok=True)
        json.dump(merged, open(os.path.join(LAB_DIR, 'lab.json'), 'w'), indent=1, default=float)
        ids = ids or sorted(merged)
    if a.lab:
        run_lab(ids, [x for x in a.approaches.split(',') if x] or None, a.lab_json or None)
        if a.finalize:
            finalize_from_lab(ids=ids)
        return
    if a.finalize:
        finalize_from_lab(ids=ids or None)
        return
    if not ids:
        ap.print_help()
        return
    run_final(ids)


if __name__ == '__main__':
    main()
