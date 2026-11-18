"""Every line of the edited narration (the Bus film) against what the recogniser hears in it.
    python3 tools/vo_asrcheck.py [--whole-file-only] [--every]   exit 1 on any mismatch that is not in ALLOW
    --every: also recognise EVERY line on its own (50 ms margins, 0.3 s of silence padding) and judge it the same way
Reads W/narration/edit_list.json (each line's output span) and W/align/asr_cache.json (Parakeet on narration_en.wav,
written by align.py: run align.py after every vo_edit.py build, then this). A recognised word belongs to the line whose
sound holds its start (out span - 40 ms .. + 20 ms); a word that starts in a gap goes to the next line when that line
starts within 0.35 s (Parakeet puts the first word after a silence up to ~0.3 s early), else to the
line before. A line fails when its first or last word is wrong, when it reads under 80 % of its script, when it is not
heard at all, or when a word is split across a line boundary ("wood" | "pile", "door at" | "At six"): exactly the
fragments a mis-placed cut leaves. A line flagged in the whole-file pass is then recognised again on its own (50 ms
margins, from narration_en.wav): the whole-file pass depends on where the VAD cut its chunks (a last word cut off at a
chunk edge, "weak T."), so a line that reads right on its own is reported as "chunking" and passes.
"""
import difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(os.path.dirname(HERE), '_work')
sys.path.insert(0, HERE)
from vo_edit import toks                                           # noqa: E402  (the edit's own word normaliser)

# what the recogniser cannot help hearing its own way (homophones and spellings: not edit faults)
SAME = {'gray': 'grey', 'mr': 'mister', 'dr': 'doctor', 'oh': '0', 'sh': 'shh', 'genes': 'jeans', 'colour': 'color',
        'twentytwo': '22', 'sammy': 'sami', 'breaks': 'brakes'}
JOIN2 = {('rear', 'view'): 'rearview', ('land', 'line'): 'landline', ('arm', 'chair'): 'armchair'}
# lines that may fail, by tag, with the reason (checked on the spectrogram and with a second recogniser, not an edit fault)
ALLOW_TAGS = {
    'hook_knows': 'the take reduces "And" to a nasal "\'nd": Parakeet writes "Then" for the line on its own, "And" with the line before (raw take too); Whisper also "Then"',   # L2 "And if he knows it... don't op"
    'tape_ride_right': '"Ride" is spliced from the title; Parakeet merges the d into the r of "right" on any "ride right" ("Right, right" on the raw title phrase in isolation too); Whisper: "Ride right kids"',   # L19 '"Ride right, kids!"'
    'mailbox_letters': 'Parakeet writes "mail box" as two words (raw take too); Whisper: "mailbox"',   # L63 'Grandma unscrews the letters o'
    'whistle1': '"Fweet-fweet." is an invented whistle word: Parakeet "Free t freed", Whisper "Tweet, tweet" (raw take too)',   # L78 'Fweet-fweet.'
    'never_walks': 'the take says "walks" with a weak s before the full stop: both recognisers "walked" on the raw take too',   # L98 'He never walks.'
    'peephole_white': 'Parakeet and Whisper both write "people" for this "peephole" (raw take too)',   # L144 'The peephole goes white.'
    'pads_upstairs': '"Rex" read as "wrecks" (a homophone; raw take too)',   # L157 'Sami pads upstairs for his din'
    'pressed_grin': '"Pressed" with its d fused into "to": both recognisers "Press to" (raw take too)',   # L178 'Pressed to the grin.'
    'practiced_all_week': '"Samis" for "Sami\'s" (the possessive written without an apostrophe; Whisper "Sami\'s")',   # L217 "Sami's practiced all week."
    'grab_other': 'the take says "grab" with a released b before "the": Parakeet "grabbed" (raw take too); Whisper "grabbed"',   # L222 'I grab the other.'
    'doors_slap': 'the take fuses "doors slap" ("door slapped", raw take too); Whisper: "The doors slap shut"',   # L231 'The doors slap shut an inch fr'
    'over_loudspeaker': 'the colon reading lifts "loudspeaker" (Parakeet "loudspeakers", raw take too; Whisper "loudspeaker")',   # L236 'Over the loudspeaker:'
    'della_mina': 'the TTS swallowed the "two" of "twenty-two" into this "Mina" (raw: "To Mina"); the line before now carries a spliced "Seat twenty-two."; re-record wanted',   # L255 '"Mina.'
    'whistle2': '"Fweet-fweet." (invented whistle word, see rule above)',   # L284 'Fweet-fweet.'
    'cobwebs': '"in the" read "and the" (raw take too); Whisper "Cobb Web\'s in the wipers"',   # L295 'Cobwebs in the wipers.'
    'whistle3': '"Fweet-fweet." (invented whistle word)',   # L343 'Fweet-fweet.'
    'theo_shout': 'the take\'s group shout "THEO!" is unreadable to both recognisers even on the raw take; re-record wanted (or layer with the mix)',   # L358 '"THEO!"'
}


def norm(s):
    out = []
    for t in toks(s):
        t = SAME.get(t, t)
        if t == '0': continue
        if out and re.fullmatch(r'[2-9]0', out[-1]) and re.fullmatch(r'[1-9]', t):    # "forty seven" = 47
            out[-1] = out[-1][0] + t; continue
        if out and (out[-1], t) in JOIN2:
            out[-1] = JOIN2[(out[-1], t)]; continue
        out.append(t)
    return out


def main(quiet_iso=False, every=False):
    el = json.load(open(os.path.join(W, 'narration', 'edit_list.json')))['lines']
    ALLOW = {e['i']: ALLOW_TAGS[e['tag']] for e in el if e['tag'] in ALLOW_TAGS}
    words = json.load(open(os.path.join(W, 'align', 'asr_cache.json')))['en_words']
    heard = {e['i']: [] for e in el}
    for w, t in words:
        k = next((k for k, e in enumerate(el) if e['out'][0] - 0.04 <= t <= e['out'][1] + 0.02), None)
        if k is None:
            nxt = next((k for k, e in enumerate(el) if e['out'][0] > t), None)
            if nxt is None: k = len(el) - 1
            elif nxt > 0 and el[nxt]['out'][0] - t > 0.35: k = nxt - 1
            else: k = nxt
        heard[el[k]['i']].append(w)
    sim = lambda x, y: x == y or difflib.SequenceMatcher(None, x, y).ratio() >= 0.67

    def judge(hs, sc):
        why = []
        if not hs: return ['nothing heard']
        if not sim(hs[0], sc[0]): why.append('first word')
        if not sim(hs[-1], sc[-1]): why.append('last word')
        r = difflib.SequenceMatcher(None, hs, sc).ratio()
        if r < 0.8 and len(sc) >= 3: why.append('reads %.2f' % r)
        return why

    bad = []
    H = {i: norm(' '.join(v)) for i, v in heard.items()}
    for n, e in enumerate(el):
        i = e['i']; hs = H[i]; sc = norm(e['en'])
        why = judge(hs, sc)
        if n + 1 < len(el) and hs and H[el[n + 1]['i']]:
            a, b = hs[-1], H[el[n + 1]['i']][0]
            nxt = norm(el[n + 1]['en'])
            if (a + b) in sc or (a + b) in nxt or (a == b and len(a) > 1 and nxt[:1] == [a] and sc[-1:] != [a]):
                why.append('word split across the boundary: "%s" | "%s"' % (a, b))
        if why:
            bad.append([i, ', '.join(why), e['en'], ' '.join(heard[i]), None])
    if bad and not quiet_iso:
        iso = isolated([b[0] for b in bad], el)
        for b in bad:
            txt = iso.get(b[0], '')
            if not judge(norm(txt), norm(el[b[0]]['en'])) and 'split' not in b[1]:
                b[4] = txt
    if every:                                                       # every line on its own as well, not only the flagged
        iso_all = isolated([e['i'] for e in el], el)
        flagged = {b[0] for b in bad}
        for e in el:
            i = e['i']
            txt = iso_all.get(i, '')
            why = judge(norm(txt), norm(e['en']))
            if why and i not in flagged:
                bad.append([i, 'on its own: ' + ', '.join(why), e['en'], txt, None])
        n_iso_ok = sum(1 for e in el if not judge(norm(iso_all.get(e['i'], '')), norm(e['en'])))
        print('every line on its own: %d/%d read as their script' % (n_iso_ok, len(el)))
    fails = [b for b in bad if b[0] not in ALLOW and b[4] is None]
    for i, why, s_, h, iso_txt in bad:
        tag = ('ALLOWED (%s)' % ALLOW[i]) if i in ALLOW else ('chunking: on its own it reads "%s"' % iso_txt if iso_txt is not None else 'FAIL')
        print('L%-3d %-28s script: %-46s | heard: %-40s %s' % (i, why, s_[:46], h[:40], tag))
    print('asrcheck: %d lines, %d flagged in the whole-file pass, %d read right on their own, %d allowed, %d failures'
          % (len(el), len(bad), sum(1 for b in bad if b[4] is not None), sum(1 for b in bad if b[0] in ALLOW), len(fails)))
    return 1 if fails else 0


def isolated(idx, el):
    """Parakeet on each listed line on its own (50 ms margins, 0.3 s of silence padding) -> {i: text}."""
    import numpy as np, soundfile as sf, soxr, sherpa_onnx
    pk = os.environ.get('PARAKEET_DIR', '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/'
                        'scratchpad/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
    if not os.path.exists(pk): return {}
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{pk}/encoder.int8.onnx', decoder=f'{pk}/decoder.int8.onnx',
                                                        joiner=f'{pk}/joiner.int8.onnx', tokens=f'{pk}/tokens.txt',
                                                        model_type='nemo_transducer', num_threads=2)
    y, sr = sf.read(os.path.join(W, 'narration', 'narration_en.wav'))
    by_i = {e['i']: e for e in el}; out = {}
    for i in idx:
        a, b = by_i[i]['out']
        z = y[max(0, int((a - 0.05) * sr)):int((b + 0.05) * sr)]
        z16 = np.concatenate([np.zeros(4800), soxr.resample(z, sr, 16000), np.zeros(4800)]).astype(np.float32)
        st = rec.create_stream(); st.accept_waveform(16000, z16); rec.decode_stream(st)
        out[i] = st.result.text.strip()
    return out


if __name__ == '__main__':
    sys.exit(main('--whole-file-only' in sys.argv, '--every' in sys.argv))
