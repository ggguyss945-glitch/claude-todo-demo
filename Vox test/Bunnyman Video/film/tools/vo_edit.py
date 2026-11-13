"""The voiceover edit: the owner's raw TTS take -> a clean, paced narration (English only).
    python3 vo_edit.py analyze        per-line source spans, what gets removed, internal pauses (prints; writes nothing)
    python3 vo_edit.py pacing [--force]   write W/narration/pacing_map.md from the rules + PACE below (keeps an existing
                                      map unless --force: the map is the source of truth, edit it by hand if you like)
    python3 vo_edit.py build          read pacing_map.md -> narration_clean.wav (edited, no character voices),
                                      narration_en.wav (+ character voices, tools/vo_voices.py), edit_list.json,
                                      W/narration/build_stats.json (numbers for voice_report.md)
    python3 vo_edit.py check          scan the edited files (residual breaths, clicks, gaps vs the map, peaks, loudness)
                                      and draw the before/after strips into W/narration/tests/
Source: W/narration/raw/narration_raw_24k.wav (24 kHz mono 16-bit, two uploaded parts joined at 454.0587 s inside
"...facing | the back door"); words: W/narration/asr_raw.json (tools/vo_asr.py: Parakeet TDT word start/end times,
80 ms resolution, used as anchors); script: script/lines.py.

How the edit works
  1. Repair: every clipped run (|x| >= 0.999: 149 runs of 1-2 samples) is redrawn with a cubic spline through the
     4 good samples on each side (peaks come back above full scale; the final gain makes room); then 24 -> 48 kHz with
     soxr VHQ (linear phase).
  2. Map: every line of lines.py is matched to the recogniser's words (difflib on normalised words, as align.py does).
     Sound "islands" = stretches above -60 dBFS (5 ms RMS, 1 ms hop) merged across gaps under 15 ms; the TTS leaves
     digital silence between most phrases, so islands are clean units. A word owns the island at its recognised start
     (word_island) and the clearly-speech islands right after it inside its span (a word cut by a closure: "emp-ty").
     A word-less island joins a line only when it is speech: pitched and touching a word, a nasal / l murmur against
     its word ("smile"), the release of a final stop or the s after a stop closure ("suit", "six"), a loud final s
     ("since", "sense"), an initial s before its closure; everything else (breaths, mouth clicks, low lip thumps, the
     TTS's "huh" / "yah" / "mm-hmm" noises) is dropped, between lines and inside them. Two lines in one island are split
     at the quietest point between their words. A loud pitched island that would be dropped stops the build.
  3. Fix the TTS slips (FIXES below; each one checked with two recognisers, see voice_report.md).
  4. Pace: every line boundary gets the gap of pacing_map.md (silence from the end of one line's decay to the next
     line's first sound); pauses inside a line keep the take's natural timing, clamped by their punctuation (comma
     0.12-0.30 s, colon 0.25-0.45 s, ellipsis 0.45-0.80 s, mid-line full stop 0.30-0.55 s, no punctuation <= 0.25 s)
     and by INTERNAL overrides; a pause inside a word (before its release or final s) is never touched.
  5. Level and clean: one gain per line (60 % of its distance from the narrator's median speech level, +-3 dB, nothing
     inside 1.5 dB) so no gain moves inside a phrase (no pumping); 70 Hz high-pass (4th order); a split-band de-esser
     (only where the 4.5 kHz+ band rises above the neighbouring vowel - 7 dB, at most 6 dB); the gaps gated to digital
     silence; one gain for both files puts the true peak at -1 dBTP (no limiter: the dynamics stay the take's; mix.py
     brings the voice to -14 LUFS itself). The narrator's pitch, formants and tone are not touched.
  6. Character voices (tools/vo_voices.py) on the quoted words only -> narration_en.wav. narration_clean.wav is the
     same edit without them (identical timing).
Cuts are made at low-energy points (island edges sit at <= -60 dBFS) with raised-cosine fades: 2 ms at island edges,
6-10 ms where a cut falls inside sound, 8-12 ms equal-power crossfades where two pieces join without a gap. Tails are
kept down to -60 dBFS (deeper than the -50 dB the brief asks for).
"""
import json, os, re, sys, difflib
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
W = os.path.join(FILM, '_work')
N = os.path.join(W, 'narration')
RAW = os.path.join(N, 'raw', 'narration_raw_24k.wav')
ASR = os.path.join(N, 'asr_raw.json')
PACING = os.path.join(N, 'pacing_map.md')
OUT_CLEAN = os.path.join(N, 'narration_clean.wav')
OUT = os.path.join(N, 'narration_en.wav')
EDL = os.path.join(N, 'edit_list.json')
STATS = os.path.join(N, 'build_stats.json')
TESTS = os.path.join(N, 'tests')
SCRIPT_TXT = os.path.join(ROOT, 'script', 'narration_en.txt')
sys.path.insert(0, os.path.join(ROOT, 'script'))
from lines import LINES                                           # noqa: E402

SR = 48000
PART_JOIN = 454.0587                                              # end of part1.wav inside the joined raw file
PEAK_CEIL = -1.0                                                  # dBTP: one gain for both files puts the true peak here
DEESS_THR_DB, DEESS_MAX_DB = -7.0, 6.0                            # sibilants above (vowel level - 7 dB) come down

# ============================================================================ the TTS slips (raw-file seconds)
# Each was found by comparing two recognisers (Parakeet, Whisper) with the script, then cut by eye on 2 ms
# spectrograms; every repaired phrase was re-recognised as the script by both (voice_report.md).
FIXES = {
    # "Rule number three. Ye knocks": the TTS dropped "If"; "If he" comes from rule four's "If he talks," (the same
    # rule-text reading, its "he" ends at 144-147 Hz where this "knocks" starts at 141-145 Hz), joined by a 10 ms
    # equal-power crossfade at the onset of the n of "knocks"
    'rule3_text': {'start': 326.700, 'prepend': [(376.165, 376.452)], 'join': 'xfade'},
    # "it's family. Yah. I I taught it": the line starts on the second "I" (the one said into "taught")
    'taught_mother': {'start': 356.266},
    # "the dark c- corner": the stutter goes; 75 ms of silence is the k closure of "dark corner"
    'corner': {'cuts': [(520.135, 520.392, 0.075)]},
    # "a very ordinary c- cup": the stutter goes; 60 ms k closure
    'coffee': {'cuts': [(901.962, 902.145, 0.060)]},
    # "See leave well" (an extra vowel after the S, and a v for the p): the S runs straight into "lee", and the v
    # becomes a 70 ms p closure. Both recognisers then hear "Sleep well."
    'sleep_well': {'cuts': [(964.952, 965.104, 0.0), (965.300, 965.425, 0.070)]},
    # "At eleven seven": the TTS read 11:07 without the "oh"; the "O" of the comment prompt's "Okay" (142-154 Hz, it
    # sits between "eleven" (ends ~176 Hz) and "seven" (starts ~156 Hz)) goes in. Both recognisers then hear 11:07.
    'song': {'inserts': [(186.476, (235.452, 235.535), 0.020, 0.050)]},
    # the two uploaded parts meet inside "facing | the back door" (a 0.011 step in the waveform): a 12 ms equal-power
    # crossfade across the seam (both recognisers hear "facing the back door"; a 40 ms gap made Whisper hear "facing in")
    'couch': {'cuts': [(PART_JOIN, PART_JOIN, 0.0, 0.012)]},
    # Mom's "And count to seven" and June's "One": the stray "opt" between them (a weak vowel and a click) is dropped
    # (the n of "seven" runs straight into a "pt"-like burst: it ends on an 80 ms fade at the end of its voicing; a
    # 25 ms fade read as "seven up")
    'count_to_seven': {'end': 694.950, 'end_fade': 0.080},
    'count': {'start': 695.086},
}
# pauses inside a line, by the word they follow (line tag -> {word index in the line: seconds})
INTERNAL = {
    'open_count': {'seven': 0.65},           # "count to seven... don't."  the hook's held breath
    'said_mom': {'mom': 0.50},               # "And if you said Mom... don't worry."
    'next': {'back': 0.50},                  # "...came back... don't ask what they found."
    'end': {'tonight': 0.50},                # "...a little song tonight... that's just the outro."
}
NOISE_WORDS = {'yes', 'huh', 'yeah', 'mmhmm', 'yah', 'opt', 'c', 'hmm', 'mm', 'uh', 'um', 'ah', 'oh'}


def log(*a):
    print('[vo]', *a, flush=True)


# ============================================================================ source: repair + resample
def declip(x, thr=0.999, k=4):
    """Redraw clipped runs with a cubic spline through k good samples on each side (never lowering a sample)."""
    from scipy.interpolate import CubicSpline
    y = x.copy()
    c = np.abs(x) >= thr
    d = np.diff(np.concatenate([[0], c.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    peaks = []
    for a, b in zip(st, en):
        left = np.arange(max(0, a - k), a); right = np.arange(b, min(len(x), b + k))
        if len(left) < 2 or len(right) < 2:
            continue
        xs = np.concatenate([left, right]); cs = CubicSpline(xs, x[xs])
        est = cs(np.arange(a, b)); s = np.sign(x[a])
        y[a:b] = s * np.maximum(np.abs(est), np.abs(x[a:b]))
        peaks.append(float(np.abs(y[a:b]).max()))
    return y, {'runs': int(len(st)), 'samples': int(c.sum()), 'max_redrawn_peak': round(max(peaks), 3) if peaks else 0}


def load_source():
    import soxr
    x24, sr = sf.read(RAW, dtype='float64')
    assert sr == 24000, sr
    x24, clip = declip(x24)
    x = soxr.resample(x24, 24000, SR, quality='VHQ')
    return x24, x, clip


# ============================================================================ analysis
def envelope(x, sr=SR, win=0.005, hop=0.001):
    """dB RMS of [k*hop, k*hop+win) for every k."""
    w, h = int(win * sr), int(hop * sr)
    cs = np.concatenate([[0.0], np.cumsum(x * x)])
    idx = np.arange(0, len(x) - w, h)
    return 10 * np.log10((cs[idx + w] - cs[idx]) / w + 1e-20)


def voicing_1ms(x24, n_frames):
    import parselmouth
    p = parselmouth.Sound(x24, sampling_frequency=24000).to_pitch_ac(time_step=0.005, pitch_floor=70, pitch_ceiling=600,
                                                                    voicing_threshold=0.45)
    f0 = p.selected_array['frequency']; tp = p.xs()
    v = np.zeros(n_frames, bool)
    for t, f in zip(tp, f0):
        if f > 0:
            k = int(t * 1000); v[max(0, k - 3):k + 3] = True
    return v, (tp, f0)


def lowband_ratio(x, n_frames):
    """dB of the < 900 Hz band minus the full band (voiced energy shows even where the pitch tracker gives up)."""
    from scipy import signal
    lp = signal.sosfilt(signal.butter(4, 900, 'lowpass', fs=SR, output='sos'), x)
    e = envelope(lp)[:n_frames]
    return e


def islands(db, thr=-60.0, merge=15):
    act = db > thr
    d = np.diff(np.concatenate([[0], act.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    out = []
    for a, b in zip(st, en):
        if out and a - out[-1][1] < merge: out[-1][1] = b
        else: out.append([int(a), int(b)])
    return [(a / 1000.0, (b - 1) / 1000.0 + 0.005) for a, b in out]          # seconds: first sound .. last sound


NUM = {'zero': '0', 'oh': '0', 'one': '1', 'two': '2', 'to': '2', 'too': '2', 'three': '3', 'four': '4', 'five': '5',
       'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
       'thirty': '30', 'forty': '40', 'fifty': '50', 'eighty': '80', 'nineteen': '19', 'mr': 'mister', 'mamma': 'mama', 'lori': 'laurie',
       'gray': 'grey', 'aged': 'age', 'pembertons': 'pemberton'}
JOIN = {('tree', 'line'): 'treeline', ('bunny', 'man'): 'bunnyman', ('door', 'knob'): 'doorknob', ('any', 'more'): 'anymore',
        ('arm', 'chair'): 'armchair', ('grown', 'up'): 'grownup'}


def toks(s, keep_index=False):
    """Normalised word tokens (as align.py: lower case, clock times split, number words -> digits, possessives dropped)
    and, with keep_index, the index of the text word each token came from."""
    s = s.lower().replace('’', "'").replace('—', ' ')
    s = re.sub(r'\b1987\b', 'nineteen eighty-seven', s)                   # the year as it is read
    s = re.sub(r"(\w)'ve\b", r'\1 have', s)                               # would've = would have
    words = s.split()
    out, src = [], []
    for wi, w in enumerate(words):
        w = re.sub(r"(\w)'s\b", r'\1', w); w = re.sub(r"s'(?=\W|$)", 's', w)
        w = re.sub(r'(\d+)[:.](\d\d)', r'\1 \2', w)
        for part in re.split(r'[\s\-]+', w):
            n = re.sub(r'[^a-z0-9]', '', part)
            if not n: continue
            n = NUM.get(n, n)
            if re.fullmatch(r'0\d', n): n = n[1]
            if out and (out[-1], n) in JOIN: out[-1] = JOIN[(out[-1], n)]; continue
            out.append(n); src.append(wi)
    return (out, src) if keep_index else out


def map_lines(words):
    """Line -> list of ASR word indices it owns (difflib on the whole script), and per ASR word its (line, text-word)."""
    asr, aw, extra = [], [], {}                                     # extra: token -> further words it covers
    for k, w in enumerate(words):
        for n in toks(w[0]):
            if asr and (asr[-1], n) in JOIN:                          # 'tree' 'line' -> treeline: both words own it
                asr[-1] = JOIN[(asr[-1], n)]; extra.setdefault(len(asr) - 1, []).append(k); continue
            asr.append(n); aw.append(k)
    sc, own, tw = [], [], []
    for i, l in enumerate(LINES):
        t, src = toks(l['en'], keep_index=True)
        sc += t; own += [i] * len(t); tw += src
    sm = difflib.SequenceMatcher(None, sc, asr, autojunk=False)
    owned = {i: [] for i in range(len(LINES))}
    wline = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i = own[blk.a + k]
            for wk in [aw[blk.b + k]] + extra.get(blk.b + k, []):
                if wk not in owned[i]: owned[i].append(wk)
                wline[wk] = (i, tw[blk.a + k])
    # unmatched ASR words (a word heard its own way): between two words of the same line they belong to that line;
    # between two lines, to the line that has unmatched script words on that side (else to the nearer one in time)
    matched_tok = set(blk.a + k for blk in sm.get_matching_blocks() for k in range(blk.size))
    tail_open = {i: False for i in range(len(LINES))}; head_open = {i: False for i in range(len(LINES))}
    for i in range(len(LINES)):
        idx = [j for j, o in enumerate(own) if o == i]
        if idx: head_open[i] = idx[0] not in matched_tok; tail_open[i] = idx[-1] not in matched_tok
    unowned = []
    for k in range(len(words)):
        if k in wline: continue
        noise = re.sub(r'[^a-z]', '', words[k][0].lower()) in NOISE_WORDS
        pk = next((j for j in range(k - 1, -1, -1) if j in wline), None)
        nk = next((j for j in range(k + 1, len(words)) if j in wline), None)
        prev = wline[pk] if pk is not None else None
        nxt = wline[nk] if nk is not None else None
        if prev and nxt and prev[0] == nxt[0]:
            if noise: continue
            owned[prev[0]].append(k); wline[k] = (prev[0], prev[1]); continue
        if noise: continue
        if prev and tail_open[prev[0]] and not (nxt and head_open[nxt[0]]): i = prev[0]
        elif nxt and head_open[nxt[0]] and not (prev and tail_open[prev[0]]): i = nxt[0]
        elif prev and nxt:
            i = prev[0] if words[k][1] - words[pk][2] <= words[nk][1] - words[k][2] else nxt[0]
        else:
            unowned.append(k); continue
        owned[i].append(k); wline[k] = (i, prev[1] if i == (prev or (None,))[0] else nxt[1])
    for i in owned: owned[i].sort()
    return owned, wline, unowned


def text_words(i):
    return LINES[i]['en'].replace('—', ' ').split()


def punct_after(i, wi):
    """Punctuation after text word wi of line i: '...', ':', ',', ';', '.', or ''."""
    tw = text_words(i)
    if wi >= len(tw): return ''
    w = tw[wi]
    if w.endswith('...'): return '...'
    m = re.search(r'([,:;.?!])["\']?$', w)
    return m.group(1) if m else ''


class Take:
    """The raw take, repaired, at 48 kHz, with its islands and the line map."""

    def __init__(self):
        self.x24, self.x, self.clip = load_source()
        self.db = envelope(self.x)
        nf = len(self.db)
        self.voiced, self.f0 = voicing_1ms(self.x24, nf)
        lf = lowband_ratio(self.x, nf)
        self.lfdom = (lf > self.db - 6) & (self.db > -50)                  # low-band dominant frames: voiced-ish
        self.words = json.load(open(ASR))['words']
        self.isl = islands(self.db)
        self.owned, self.wline, self.unowned = map_lines(self.words)
        self.missing = [i for i in range(len(LINES)) if not self.owned[i]]

    def frames(self, a, b):
        return self.db[max(0, int(a * 1000)):max(0, int(b * 1000))]

    def vfrac(self, a, b):
        """Share of voiced 1 ms frames; low-band dominance counts too (nasals, voice bars) except in islands under
        80 ms, where only the pitch tracker counts (a low-frequency lip pop is not speech)."""
        sl = slice(int(a * 1000), int(b * 1000))
        v = self.voiced[sl] if b - a < 0.08 else (self.voiced[sl] | self.lfdom[sl])
        return float(v.mean()) if len(v) else 0.0

    def quietest(self, a, b, smooth=12):
        """Time of the lowest smoothed level in [a, b]."""
        seg = self.frames(a, b)
        if len(seg) < 3: return (a + b) / 2
        k = np.convolve(10 ** (seg / 10), np.ones(smooth) / smooth, 'same')
        return a + (int(np.argmin(k)) + 2.5) / 1000.0


# ============================================================================ line spans
# word-less voiced islands between lines that are known TTS noises (dropped on purpose: the "huh" after "hospital.",
# the "yah" after "it's family.", a voiced blip after "magic trick?", the "mm-hmm" after "cup of coffee.")
KNOWN_NOISE = [56.94, 355.42, 884.64, 903.30]


def coda_ok(word, gap, dur, peak=-99.0):
    """Can an unvoiced island 'gap' s after a word's last sound be that word's own ending? The TTS often leaves a short
    dip before a final consonant: a stop's release with its aspiration ("suit", "night", "it", "Lock", "Thunk") comes
    up to 0.10 s later and lasts up to 0.20 s; a final s ("since", "sense", "use", "Silence") up to 0.09 s later and
    louder than -32 dB; the s of a stop + s ending
    ("six", "knocks") comes after the closure, up to 0.17 s later. A breath comes later, lasts longer, or (after an
    s that is already there, "spotless", "eggs") is much quieter than an s (-35..-45 dB against -17..-27 dB)."""
    w = re.sub(r'[^a-z]', '', word.lower())
    if re.search(r'(x|ts|ks|ps|ds|cks|cts|pts|kes|tes|pes|des|xes)$', w): return gap <= 0.17 and dur <= 0.40
    if re.search(r'(t|k|p|ck|ct|pt|ed|d|de|te|ke|pe|g|b|ght)$', w): return gap <= 0.10 and dur <= 0.20
    if re.search(r'(s|ce|se|z|ze|sh|ch)$', w): return gap <= 0.09 and dur <= 0.40 and peak > -32
    if re.search(r'(f|ff|fe|th|gh)$', w): return gap <= 0.04 and dur <= 0.30 and peak > -40
    return False


def ends_in_noise(T, a, b):
    """Does the island [a, b] end in an unvoiced noise (a fricative already said)?"""
    seg = slice(max(int(a * 1000), int(b * 1000) - 60), int(b * 1000))
    loud = T.db[seg] > -50
    if loud.sum() < 10: return False
    unv = ~(T.voiced[seg] | T.lfdom[seg])
    return bool((unv & loud).sum() / loud.sum() > 0.6)


def onset_ok(word, gap, dur):
    """Can an unvoiced island 'gap' s before a word be its first sound (the s of st- / sk- before the closure, an
    initial s / sh / f / h / th, a stop's burst)?"""
    w = re.sub(r'[^a-z]', '', word.lower())
    if re.match(r'(st|sp|sk|sc|squ)', w): return gap <= 0.12 and dur <= 0.35
    if re.match(r'(s|sh|f|th|h|ch|c|k|p|t|x|wh|q)', w): return gap <= 0.05 and dur <= 0.30
    return False


def is_speechlike(T, a, b):
    """An island that is speech for sure: pitched (>= 20 % of frames), or louder than -30 dBFS without being a short
    low-frequency lip thump."""
    sl = slice(int(a * 1000), int(b * 1000))
    if b <= a: return False
    vp = float(T.voiced[sl].mean()); pk = float(T.db[sl].max()); vl = float(T.lfdom[sl].mean())
    return vp >= 0.2 or (pk > -30 and not (vl >= 0.5 and b - a < 0.08))


def word_island(T, k):
    """The island a word belongs to. The recogniser's start time (80 ms frames) is the anchor, its end time is not (it
    often runs on through the breath after the word): the island holding start + 30 ms when that island is speech
    (pitched); else the first pitched island that starts inside the word's span (the start fell in the silence before
    it: "The" after "once", "I'm" after a breath); else the island at the start; else the most-overlapped island; else
    the nearest within 0.15 s."""
    t0 = T.words[k][1]; t1 = max(T.words[k][2], t0 + 0.08)
    def pitched(j):                                                # speech-like: pitched, or loud and not a low thump
        a, b = T.isl[j]
        return is_speechlike(T, a, b)
    at, over, near, bd = None, [], None, 1e9
    for j, (a, b) in enumerate(T.isl):
        if b < t0 - 0.3: continue
        if a > t1 + 0.3: break
        if a <= t0 + 0.03 <= b: at = j
        o = min(b, t1) - max(a, t0)
        if o > 0: over.append((o, j))
        d = a - t0 if a > t0 else (t0 - b if t0 > b else 0.0)
        if d < bd: near, bd = j, d
    if at is not None and pitched(at): return at
    later = sorted(j for o, j in over if T.isl[j][0] >= t0 - 0.02 and pitched(j))
    if later: return later[0]
    if at is not None: return at
    if over: return max(over)[1]
    return near if bd <= 0.15 else None


def line_spans(T, verbose=False):
    """For every line: the source islands it is made of and what was removed inside it.
    Words own the island that holds their first token. A word-less island joins a line when it is speech: voiced and
    next to the line's sound (a word the recogniser timed late, a voiced tail), or an unvoiced sound one of the
    neighbouring words explains (coda_ok / onset_ok); otherwise it is a breath, a click or a TTS noise and is dropped,
    wherever it is. Two lines in one island are split at the quietest point between their words.
    Returns ({i: {'span', 'keep', 'removed', 'cut_in', 'cut_out'}}, dropped islands between lines, island owners)."""
    W_ = T.words
    isl = T.isl
    owner_of = [set() for _ in isl]
    words_of = [[] for _ in isl]                                   # the words whose island it is
    for i, ks in T.owned.items():
        for k in ks:
            j = word_island(T, k)
            if j is not None: owner_of[j].add(i); words_of[j].append(k)
    # a word cut by a closure ("emp-ty", "door-s") also owns the islands that follow inside its recognised span when
    # they are clearly speech (pitched and above -40 dBFS, or above -30 dBFS) and close (<= 0.12 s); a quiet unvoiced
    # island there is the breath after the word and stays free
    for i, ks in T.owned.items():
        for k in ks:
            j = word_island(T, k)
            if j is None: continue
            t1 = T.words[k][2]; prev_end = isl[j][1]
            for m in range(j + 1, len(isl)):
                a, b = isl[m]
                if a >= t1 or a - prev_end > 0.12: break
                pk = float(T.frames(a, b).max()); vp = float(T.voiced[int(a * 1000):int(b * 1000)].mean()) if b > a else 0.0
                if (vp >= 0.2 and pk > -40) or (pk > -30 and is_speechlike(T, a, b)):
                    owner_of[m].add(i); prev_end = b
                else:
                    break
    owned_isl = [j for j in range(len(isl)) if owner_of[j]]
    word_t0 = [(W_[k][1], k, i) for i, ks in T.owned.items() for k in ks]
    word_t0.sort()
    dropped = {}
    free = [j for j in range(len(isl)) if not owner_of[j]]
    for j in free:                                                 # the TTS's own noises go first
        p, q = isl[j]
        if any(p - 0.05 <= t <= q + 0.05 for t in KNOWN_NOISE):
            dropped[j] = ('TTS noise', float(T.frames(p, q).max()))

    def neighbours(j):
        own = [m for m in range(len(isl)) if owner_of[m]]
        pj = next((m for m in reversed(own) if m < j), None)
        nj = next((m for m in own if m > j), None)
        return pj, nj

    def feats(j):
        """duration, pitch-voiced share, low-band-dominant share, peak dB"""
        p, q = isl[j]; sl = slice(int(p * 1000), int(q * 1000))
        vp = float(T.voiced[sl].mean()) if q > p else 0.0
        vl = float(T.lfdom[sl].mean()) if q > p else 0.0
        return q - p, vp, vl, float(T.frames(p, q).max())

    # pass 1, forward: voiced sound next to a line, and codas (a release may follow another release: "snapped")
    for j in free:
        if j in dropped or owner_of[j]: continue
        p, q = isl[j]; dur, vp, vl, pk = feats(j)
        pj, nj = neighbours(j)
        gp = p - isl[pj][1] if pj is not None else 9.0
        gn = isl[nj][0] - q if nj is not None else 9.0
        li_prev = max(owner_of[pj]) if pj is not None else None
        li_next = min(owner_of[nj]) if nj is not None else None
        wprev = next((W_[k][0] for t, k, i in reversed(word_t0) if t < p), '')
        near = li_prev if gp <= gn else li_next
        if vp >= 0.2:                                              # pitched: speech (a word timed late, a voiced tail)
            if (min(gp, gn) <= 0.06 and pk > -55) or (pk > -40 and min(gp, gn) <= 0.35): owner_of[j].add(near)
        elif vl >= 0.5 and ((min(gp, gn) <= 0.03 and pk > -55) or (gp <= 0.07 and pk > -40)):
            owner_of[j].add(near if min(gp, gn) <= 0.03 else li_prev)  # a nasal / l murmur against its word ("smile")
        elif li_prev is not None and coda_ok(wprev, gp, dur, pk):
            owner_of[j].add(li_prev)
    # pass 2, backward: onsets (the s of "Stamped" before its closure, an initial s / f / h)
    for j in reversed(free):
        if j in dropped or owner_of[j]: continue
        p, q = isl[j]; dur, vp, vl, pk = feats(j)
        pj, nj = neighbours(j)
        gn = isl[nj][0] - q if nj is not None else 9.0
        li_next = min(owner_of[nj]) if nj is not None else None
        wnext = next((W_[k][0] for t, k, i in word_t0 if t >= q - 0.02), '')
        if vp < 0.2 and li_next is not None and onset_ok(wnext, gn, dur):
            owner_of[j].add(li_next)
    for j in free:
        if j in dropped or owner_of[j]: continue
        p, q = isl[j]; dur, vp, vl, pk = feats(j)
        why = 'voiced noise' if vp >= 0.2 else ('low thump' if vl >= 0.5 else ('breath' if dur >= 0.08 else 'click'))
        dropped[j] = (why, pk)
    tag2i = {l['tag']: i for i, l in enumerate(LINES) if l['tag']}
    fx = {tag2i[t]: v for t, v in FIXES.items()}
    first, last = {}, {}
    for j, s_ in enumerate(owner_of):
        for i in s_:
            first.setdefault(i, j); last[i] = j
    for i in range(len(LINES)):
        if i not in first: raise SystemExit(f'line {i} has no island: {LINES[i]["en"]}')
    for i in range(len(LINES) - 1):
        if first[i + 1] < last[i]:
            raise SystemExit(f'lines {i} and {i + 1} overlap: islands {first[i]}-{last[i]} / {first[i + 1]}-{last[i + 1]}')
    bounds = {}
    for i in range(len(LINES)):
        bounds[i] = [isl[first[i]][0], isl[last[i]][1], False, False]
    for i in range(len(LINES) - 1):                               # two lines in one island: split at the quietest point
        if last[i] == first[i + 1]:
            k_last = T.owned[i][-1]; k_next = T.owned[i + 1][0]
            a_isl, b_isl = isl[last[i]]
            lo = max(W_[k_last][1] + 0.05, a_isl + 0.03)
            hi = min(W_[k_next][1] + 0.06, b_isl - 0.03)
            if hi <= lo: lo, hi = W_[k_next][1] - 0.10, W_[k_next][1] + 0.06
            t = T.quietest(lo, hi)
            bounds[i][1] = t; bounds[i][3] = True
            bounds[i + 1][0] = t; bounds[i + 1][2] = True
    for i, f in fx.items():                                       # hand-set starts / ends (the slips)
        if 'start' in f: bounds[i][0] = f['start']; bounds[i][2] = True
        if 'end' in f: bounds[i][1] = f['end']; bounds[i][3] = True
    out = {}
    for i in range(len(LINES)):
        a, b, ci, co = bounds[i]
        keep, removed = [], []
        for j, (p, q) in enumerate(isl):
            if q <= a or p >= b: continue
            p2, q2 = max(p, a), min(q, b)
            if q2 - p2 <= 0.001: continue
            if j in dropped:
                removed.append({'src': [round(p2, 3), round(q2, 3)], 'why': dropped[j][0], 'peak_db': round(dropped[j][1], 1)})
            else:
                keep.append([p2, q2, [k for k in words_of[j] if k in T.owned[i]]])
        if keep:                                                   # the span is the sound: no leading / trailing silence
            a = max(a, keep[0][0]); b = min(b, keep[-1][1])
        out[i] = {'span': [a, b], 'keep': keep, 'removed': removed, 'cut_in': ci, 'cut_out': co}
    between = []
    for j, (why, pk) in dropped.items():
        p, q = isl[j]
        if any(out[i]['span'][0] <= (p + q) / 2 <= out[i]['span'][1] for i in out): continue
        between.append({'src': [round(p, 3), round(q, 3)], 'why': why, 'peak_db': round(pk, 1)})
    between.sort(key=lambda r: r['src'][0])
    loud = [r for r in between if r['why'] == 'voiced noise' and r['peak_db'] > -35]
    if loud:
        for r in loud: log('UNEXPLAINED voiced island between lines: %.3f-%.3f %.1f dB' % (r['src'][0], r['src'][1], r['peak_db']))
        if not verbose: raise SystemExit('voiced sound would be dropped between lines: check the line map')
    return out, between, owner_of


# ============================================================================ pieces (what the output is made of)
def line_pieces(T, i, sp):
    """A line as a list of pieces {'src': [a, b], 'fi', 'fo', 'gap_before' (s of silence before it inside the line),
    'xfade_before' (s: overlap with the previous piece), 'why'}. Internal pauses get their punctuation clamp here."""
    l = LINES[i]; tag = l['tag']
    f = FIXES.get(tag, {})
    a, b = sp['span']
    keep = [[k[0], k[1]] for k in sp['keep']]
    kw = [list(k[2]) if len(k) > 2 else [] for k in sp['keep']]
    if not keep: keep, kw = [[a, b]], [list(T.owned[i])]
    keep[0][0] = max(keep[0][0], a); keep[-1][1] = min(keep[-1][1], b)
    # merge kept islands separated by < 50 ms (closures inside words stay untouched)
    groups = [keep[0][:]]; gwords = [kw[0][:]]
    for (p, q), w_ in zip(keep[1:], kw[1:]):
        if p - groups[-1][1] < 0.05: groups[-1][1] = q; gwords[-1] += w_
        else: groups.append([p, q]); gwords.append(w_[:])
    word_at = {}                                                   # source time ranges that start a new word
    for (p, q), w_ in zip(groups, gwords):
        for k in w_: word_at[k] = (p, q)
    # cuts and inserts inside the line (the slips): split a group at the cut, drop [c0, c1), put 'sil' of silence
    cuts = list(f.get('cuts', []))
    for cut in cuts:
        c0, c1, sil = cut[:3]
        xf_len = cut[3] if len(cut) > 3 else 0.008
        ng = []
        for g in groups:
            p, q = g[0], g[1]
            if q <= c0 or p >= c1 or (c0 == c1 and not (p < c0 < q)):
                ng.append(g); continue
            if p < c0: ng.append([p, c0, 'cut_out'] if len(g) == 2 else [p, c0, 'cut_out'] + ([] if g[2] != 'cut_in' else []))
            if q > c1: ng.append([c1, q, 'cut_in', sil, xf_len])
            if p < c0 and len(g) > 2 and g[2] == 'cut_in':           # keep the earlier cut's silence on the left part
                ng[-2 if q > c1 else -1] = [p, c0, 'cut_in_out', g[3], g[4] if len(g) > 4 else 0.008]
        groups = ng
    pieces = []
    prev_end = None
    for g in groups:
        p, q = g[0], g[1]
        pc = {'src': [p, q], 'fi': 0.002, 'fo': 0.002, 'gap_before': 0.0, 'xfade_before': 0.0, 'why': ''}
        if len(g) > 2 and g[2] in ('cut_out', 'cut_in_out'): pc['fo'] = 0.010
        if len(g) > 2 and g[2] in ('cut_in', 'cut_in_out'):
            pc['fi'] = 0.006
            pc['forced_gap'] = g[3]; pc['xf_len'] = g[4] if len(g) > 4 else 0.008
            if pieces: pieces[-1]['fo'] = max(pieces[-1]['fo'], 0.010)
        if prev_end is not None:
            pc['orig_gap'] = p - prev_end
        pieces.append(pc); prev_end = q
    if sp['cut_in']: pieces[0]['fi'] = 0.008
    if sp['cut_out']: pieces[-1]['fo'] = 0.010
    if 'end_fade' in f: pieces[-1]['fo'] = f['end_fade']
    if 'start_fade' in f: pieces[0]['fi'] = f['start_fade']
    # internal pauses: the word before each pause and its punctuation
    W_ = T.words
    owned = T.owned[i]
    for k in range(1, len(pieces)):
        pc = pieces[k]
        if 'forced_gap' in pc:
            pc['gap_before'] = pc['forced_gap']; pc['why'] = 'slip repair'
            if pc['forced_gap'] == 0.0:
                n_ = pc.get('xf_len', 0.008)
                pc['xfade_before'] = n_; pc['fi'] = n_; pieces[k - 1]['fo'] = n_
                pc['xf_in'] = True; pieces[k - 1]['xf_out'] = True
            continue
        t_pause = pieces[k - 1]['src'][1]
        og = pc.get('orig_gap', 0.0)
        # does a new word start after this pause? (a pause before a word's own release or final s is inside the word)
        starts_word = any(p_ >= pc['src'][0] - 0.001 and p_ < pc['src'][1] for kk, (p_, q_) in word_at.items())
        if not starts_word:
            pc['gap_before'] = round(og, 3); pc['why'] = 'inside a word (closure before its release / final s): as read'
            continue
        prev_words = [kk for kk, (p_, q_) in word_at.items() if q_ <= t_pause + 0.001]
        prev_words.sort(key=lambda kk: W_[kk][1])
        wi = T.wline[prev_words[-1]][1] if prev_words else -1
        pu = punct_after(i, wi) if wi >= 0 else ''
        word = re.sub(r'[^a-z]', '', text_words(i)[wi].lower()) if wi >= 0 else ''
        ov = INTERNAL.get(tag, {}).get(word)
        if ov is not None: g, why = ov, f'held pause after "{word}" ({pu or "no mark"})'
        elif pu == '...': g, why = min(max(og, 0.45), 0.80), 'ellipsis 0.45-0.80'
        elif pu == ':': g, why = min(max(og, 0.25), 0.45), 'colon 0.25-0.45'
        elif pu in (',', ';'): g, why = min(max(og, 0.12), 0.30), 'comma 0.12-0.30'
        elif pu in ('.', '?', '!'): g, why = min(max(og, 0.30), 0.55), 'sentence inside a line 0.30-0.55'
        else: g, why = min(og, 0.25), 'between words: as read, <= 0.25'
        pc['gap_before'] = round(g, 3); pc['why'] = why; pc['after_word'] = word; pc['punct'] = pu
    # prepended material (the "If he" of rule three)
    for (p, q) in reversed(f.get('prepend', [])):
        first_pc = pieces[0]
        first_pc['xfade_before'] = 0.010 if f.get('join') == 'xfade' else 0.0
        first_pc['gap_before'] = 0.0
        first_pc['fi'] = 0.010 if f.get('join') == 'xfade' else first_pc['fi']
        first_pc['xf_in'] = f.get('join') == 'xfade'
        first_pc['why'] = 'slip repair: joined to the spliced words'
        pieces.insert(0, {'src': [p, q], 'fi': 0.004, 'fo': 0.010, 'gap_before': 0.0, 'xfade_before': 0.0,
                          'xf_out': f.get('join') == 'xfade', 'why': 'spliced in (slip repair)'})
    # inserted material (the "O" of 11:07): split the piece holding t_at
    for t_at, (p, q), g0, g1 in f.get('inserts', []):
        for k, pc in enumerate(pieces):
            if pc['src'][0] < t_at < pc['src'][1]:
                left = dict(pc); left['src'] = [pc['src'][0], t_at]; left['fo'] = 0.006
                ins = {'src': [p, q], 'fi': 0.004, 'fo': 0.008, 'gap_before': g0, 'xfade_before': 0.0,
                       'why': 'spliced in (slip repair)'}
                right = {'src': [t_at, pc['src'][1]], 'fi': 0.004, 'fo': pc['fo'], 'gap_before': g1, 'xfade_before': 0.0,
                         'why': 'slip repair'}
                pieces[k:k + 1] = [left, ins, right]
                break
    return pieces


# ============================================================================ pacing map
def paragraphs():
    """Paragraph index of every line: lines are found in order in script/narration_en.txt (one word may differ: the
    recording's "and a" for the script's "in a")."""
    paras = [p for p in open(SCRIPT_TXT).read().split('\n\n') if p.strip()]
    ptok = [toks(p) for p in paras]
    out, pi, pos = [], 0, 0
    for l in LINES:
        t = toks(l['en'])
        hit = None
        for pj in range(pi, min(pi + 3, len(paras))):
            seq = ptok[pj]
            for s0 in range(pos if pj == pi else 0, len(seq) - len(t) + 1):
                miss = sum(1 for a, b in zip(seq[s0:s0 + len(t)], t) if a != b)
                if miss == 0 or (miss == 1 and len(t) >= 4):
                    hit = (pj, s0); break
            if hit: break
        if hit is None:
            raise SystemExit(f'line not found in the script: {l["en"]}')
        pi, pos = hit[0], hit[1] + len(t)
        out.append(pi)
    return out


def rule_no(tag):
    m = re.fullmatch(r'rule(\d)', tag or ''); return int(m.group(1)) if m else None


# gap after the line with this tag: (seconds, kind, reason). Everything not listed here follows RULES in pacing_rows().
PACE = {
    # cold open
    'open': (0.50, 'sentence', 'first rule of the hook; let "don\'t wave at him" land'),
    'open_egg': (0.50, 'sentence', 'second rule of the hook'),
    'open_count': (1.00, 'paragraph', 'the hook\'s last "don\'t": hold before the jingle'),
    'jingle': (0.35, 'jingle', 'the jingle is chanted: even sing-song rhythm'),
    'jingle_song': (0.35, 'jingle', 'jingle rhythm'),
    'jingle_count': (0.35, 'jingle', 'jingle rhythm'),
    'jingle_egg': (0.90, 'paragraph', 'out of the jingle back to the story'),
    'disappeared': (0.50, 'beat', '"She was seven years old." lands on its own'),
    'seven_years': (0.50, 'beat', 'set-up for the return'),
    'walked_out_tease': (0.60, 'beat', 'hold before the hook line "And she has been humming it ever since."'),
    'rules_true': (0.60, 'beat', 'hold before the twist "not one of them was written to protect us"'),
    'not_protect': (1.00, 'paragraph', 'the cold open\'s sting; the hospital line starts fresh'),
    'dont_believe': (1.20, 'section', 'end of the cold open: room for the title sting before 1987'),
    # 1987
    'suit': (0.35, 'staccato', 'description fragments'),
    'glass_eyes': (0.35, 'staccato', 'description fragments'),
    'laurie': (0.55, 'beat', '"Laurie Price." ... "My mom." the first reveal'),
    'my_mom': (0.60, 'beat', 'after the reveal'),
    'woods': (0.50, 'beat', 'hold before "And she followed him."'),
    'golden_egg': (0.55, 'beat', 'hold before "And she was humming."'),
    'humming_1987': (0.90, 'paragraph', 'paragraph break after the eerie detail'),
    'never_found': (0.40, 'staccato', 'short follow-up'),
    'fur': (0.38, 'staccato', 'description fragments'),
    'ear': (0.38, 'staccato', 'description fragments'),
    'belly': (0.38, 'staccato', 'description fragments'),
    'standing': (0.45, 'staccato', 'last fragment gets a little more'),
    'watching': (1.00, 'section', 'from 1987 to now'),
    'talk_to_it': (0.55, 'beat', 'hold before "He never came back."'),
    'left_us': (0.55, 'beat', 'hold before "Mom told them a lot of things."'),
    'same_age': (0.40, 'sentence', 'short follow-up'),
    'yellow': (0.45, 'staccato', 'one-word sentence, then the detail'),
    'fridge': (1.40, 'before rule', 'the seven rules go up: first rule card'),
    # rule 1
    'tinny': (0.55, 'beat', 'a beat before the narrator sings the slow song'),
    'song_hop': (0.90, 'paragraph', 'after the dying-battery jingle'),
    'curtains': (0.60, 'paragraph', 'running up the stairs: the action goes on'),
    'june_window': (0.80, 'held', 'hold before the reveal "At the treeline ... there he is."'),
    'taller': (0.40, 'staccato', 'description'),
    'no_reflect': (0.50, 'beat', 'hold before "And he\'s waving back."'),
    'wave': (0.50, 'beat', 'hold before "Slowly."'),
    'slowly': (0.80, 'paragraph', 'into June\'s whisper'),
    'sad': (0.80, 'paragraph', 'out of June\'s whisper'),
    'stops_waving': (0.50, 'beat', 'the paw lifts'),
    'point': (0.45, 'staccato', 'the pointing builds'),
    'past_us': (0.90, 'paragraph', 'turn around'),
    'how_long': (0.60, 'beat', 'dread before "She\'s smiling."'),
    'smiling': (0.80, 'paragraph', 'Mom speaks'),
    'told_you': (1.00, 'before prompt', 'the comment prompt breaks the fourth wall (about 1 s)'),
    # the comment prompt
    'cta': (0.35, 'dialogue', '"Okay." runs into the ask'),
    'cta_now': (0.50, 'beat', 'the question comes'),
    'cta_question': (0.50, 'beat', 'let the choice sit'),
    'cta_let_in': (0.50, 'beat', 'let the choice sit'),
    'cta_one_word': (0.40, 'staccato', 'short instruction'),
    'cta_end': (1.40, 'before rule', 'back into the story: rule card'),
    # rule 2
    'peephole': (0.50, 'beat', 'hold before "Except for an egg on the doormat."'),
    'nine_years': (0.40, 'staccato', 'counting'),
    'nine_eggs': (0.50, 'beat', 'hold before "They smell sweet when they melt."'),
    'crack_open': (0.50, 'beat', 'hold before opening the egg'),
    'egg_open': (0.90, 'held', 'suspense before what is inside'),
    'ring': (0.80, 'paragraph', 'the reveal sinks in'),
    'not_once_ring': (0.85, 'paragraph', 'paragraph break'),
    'has_ring': (1.00, 'held', 'silence before Mom\'s sudden "You opened it."'),
    'you_opened': (0.70, 'paragraph', 'after the jump line'),
    'takes_ring': (0.55, 'beat', 'the long stare'),
    'no_fire': (1.30, 'held', 'held dread before "She puts it in her pocket."'),
    'pocket': (1.50, 'before rule', 'reveal lands, then rule card'),
    # rule 3
    'knock': (0.80, 'paragraph', 'the first knocks sound here'),
    'knock_two': (0.50, 'knocks', 'room for the two knocks'),
    'knock_pause1': (0.40, 'knocks', 'the pause itself'),
    'knock_three': (0.50, 'knocks', 'room for the three knocks'),
    'knock_pause2': (0.40, 'knocks', 'the pause itself'),
    'knock_two_end': (0.80, 'paragraph', 'room for the last two knocks, then the count'),
    'knock_seven': (0.85, 'paragraph', 'Mom nods'),
    'mom_nods': (0.35, 'dialogue', 'Mom answers'),
    'thats_him': (0.35, 'dialogue', 'Mom goes on'),
    'grandma': (0.45, 'dialogue', 'into the memory of Grandma'),
    'its_family': (0.40, 'dialogue', 'Grandma goes on'),
    'taught_mother': (0.50, 'beat', 'the memory slows'),
    'quiet': (0.60, 'beat', '"she got very quiet": a real quiet before her last words'),
    'never_used': (0.45, 'dialogue', 'Grandma'),
    'knock_recall': (0.45, 'knocks', 'the knock pattern again: 2-3-2'),
    'knock_recall_3': (0.45, 'knocks', 'the knock pattern again: 2-3-2'),
    'secret_knock': (0.50, 'beat', 'hold before "And my mother ... doesn\'t recognize it at all."'),
    'doesnt_recognize': (1.50, 'before rule', 'reveal lands, then rule card'),
    # rule 4
    'small_scared': (0.80, 'paragraph', 'the little voice comes through the slot'),
    'mama': (0.90, 'paragraph', 'the chill: Grandma has been dead for years'),
    'grandma_dead': (0.90, 'paragraph', 'the voice again'),
    'lost_egg': (0.40, 'dialogue', 'the girl goes on'),
    'come_home': (0.90, 'paragraph', 'Mom\'s reaction'),
    'mom_face': (0.40, 'dialogue', 'Mom speaks'),
    'when_seven': (0.35, 'dialogue', 'Mom goes on'),
    'perfect_sense': (0.50, 'beat', 'doubt creeps in'),
    'right_here': (0.90, 'paragraph', '"Silence." is a real silence'),
    'silence': (0.70, 'held', 'hold the silence'),
    'voice_whispers': (0.30, 'dialogue', 'the whisper follows its cue'),
    'june_looks': (0.50, 'dialogue', 'June turns to Mom'),
    'not_monster': (0.40, 'sentence', 'running'),
    'smooth_hair': (0.40, 'dialogue', 'Mom speaks'),
    'bedtime': (1.40, 'held', 'held dread before "She\'s humming."'),
    'humming': (1.50, 'before rule', 'reveal lands, then rule card'),
    # rule 5
    'june_gone': (0.45, 'sentence', 'the discoveries pile up'),
    'attic_light': (0.90, 'paragraph', 'going up to the attic'),
    'diary': (0.40, 'sentence', 'the name on the diary follows'),
    'crooked': (0.50, 'beat', 'then the diary is read'),
    'diary_mama': (0.40, 'diary', 'diary lines'),
    'diary_biscuit': (0.40, 'diary', 'diary lines'),
    'diary_1987': (0.50, 'beat', 'hold before "And the handwriting changes."'),
    'i_am_laurie': (0.35, 'repetition', 'the same sentence over and over: mechanical'),
    'i_am_laurie2': (0.32, 'repetition', 'mechanical'),
    'i_am_laurie3': (0.32, 'repetition', 'mechanical'),
    'last_page': (1.30, 'held', 'held dread before "It is so nice to be small again."'),
    'small_again': (1.00, 'paragraph', 'let the line sink before June speaks'),
    'june_smiles': (0.40, 'dialogue', 'June speaks'),
    'wear_dress': (0.35, 'dialogue', 'June goes on'),
    'corner': (0.30, 'dialogue', '"Mom says," into her line'),
    'back_to_bed': (1.30, 'held', 'held dread before "I never saw her sitting there."'),
    'never_saw': (1.50, 'before rule', 'reveal lands, then rule card'),
    # rule 6
    'rule6_anybody': (0.50, 'rule text', '"Not even me." gets its weight'),
    'window': (0.25, 'action', 'fast action: the house is broken into'),
    'back_door': (0.25, 'action', 'fast action'),
    'heavy': (0.30, 'action', 'fast action'),
    'wet': (0.30, 'action', 'fast action'),
    'dragging': (0.40, 'action', 'fast action (paragraph break kept short)'),
    'run': (0.25, 'action', 'fast action'),
    'bathroom': (0.25, 'action', 'fast action'),
    'lock': (0.45, 'action', 'the lock clicks; they settle in the tub'),
    'bathtub': (0.90, 'paragraph', 'quiet before the footsteps'),
    'slow_steps': (0.45, 'beat', 'slow'),
    'knocking_steps': (0.45, 'beat', 'the thunks come'),
    'thunk': (0.60, 'steps', 'spaced like steps on the stairs'),
    'thunk2': (0.55, 'steps', 'then the reveal of the hatchet'),
    'doorknob': (0.45, 'beat', 'the knob turns'),
    'gently': (0.50, 'beat', 'hold before the voice under the door'),
    'crack_voice': (0.70, 'paragraph', 'the girl speaks through the door'),
    'please': (0.40, 'dialogue', 'the girl goes on'),
    'dont_close': (0.90, 'paragraph', 'the drawing slides in'),
    'drawing': (0.50, 'beat', 'the drawing is described piece by piece'),
    'drawing_bridge': (0.45, 'beat', 'piece by piece'),
    'drawing_man': (0.45, 'beat', 'piece by piece'),
    'drawing_lady': (0.50, 'beat', 'piece by piece'),
    'shaky_letters': (0.40, 'beat', 'the written words follow the colon'),
    'never_heard': (0.60, 'beat', 'hold before Mom\'s shout'),
    'get_out': (0.35, 'action', 'the fight: shouts answer each other fast'),
    'screams_back': (0.20, 'action', 'the scream follows its cue at once'),
    'my_house': (0.40, 'action', 'the fight'),
    'shakes': (0.30, 'action', 'the fight'),
    'slam': (0.30, 'action', 'the fight'),
    'screaming': (0.35, 'action', 'the fight'),
    'heavy_crack': (1.20, 'held', 'the silence after the crack'),
    'nothing': (1.30, 'held', '"Then nothing." and the nothing itself'),
    'softly': (0.40, 'dialogue', 'Mom\'s soft voice'),
    'its_over': (0.40, 'dialogue', 'Mom goes on'),
    'its_gone': (0.40, 'dialogue', 'Mom goes on'),
    'rule6_recall': (0.50, 'beat', '"Rule six." ... "Not even me."'),
    'not_even_me': (1.20, 'held', 'held dread before "I don\'t open it."'),
    'dont_open_it': (1.50, 'before rule', 'the decision lands, then rule card'),
    # rule 7
    'gold': (0.55, 'beat', 'the gold light, then "Sunrise."'),
    'sunrise': (0.45, 'staccato', '"Sunrise." "Easter morning."'),
    'mom_knocks': (0.45, 'dialogue', 'Mom speaks through the door'),
    'sunrise_babies': (0.40, 'dialogue', 'Mom goes on'),
    'did_it': (0.40, 'dialogue', 'Mom goes on'),
    'followed_rules': (0.40, 'dialogue', 'Mom goes on'),
    'rule_said': (0.50, 'beat', 'the loophole dawns'),
    'outside': (0.55, 'beat', 'dread before "Mom has a key."'),
    'no_monster': (0.50, 'beat', 'the face inside'),
    'stubble': (0.40, 'staccato', 'description fragments'),
    'fifty_five': (0.40, 'staccato', 'description fragments'),
    'skin_bone': (0.50, 'beat', 'then the eyes'),
    'lips_move': (0.80, 'paragraph', 'his last word'),
    'dying_mama': (1.40, 'held', 'held dread before "Then he\'s still."'),
    'still': (1.00, 'paragraph', 'Mom turns to June'),
    'hand_over_eyes': (0.80, 'paragraph', 'Mom speaks'),
    'happy_easter': (0.45, 'dialogue', 'Mom goes on, slowly'),
    'trick': (0.45, 'dialogue', 'Mom goes on, slowly'),
    'close_eyes': (0.40, 'dialogue', 'Mom goes on'),
    'count_to_seven': (0.90, 'count', 'June starts counting'),
    'count': (0.15, 'split', '"One," June whispers.'),
    'count_whisper': (0.60, 'count', '"One," June whispers. ... "Two." spaced like counting'),
    'count_2': (0.95, 'count', 'spaced like counting'),
    'count_3': (1.00, 'paragraph', 'the realisation'),
    # the reveal
    'reveal': (0.50, 'beat', 'hold before "He traded with her."'),
    'traded': (0.50, 'beat', 'hold before "That\'s the trick."'),
    'someone_else': (0.50, 'beat', 'the swap explained'),
    'girl_body': (0.40, 'staccato', 'Clean. Calm. Humming.'),
    'clean': (0.38, 'staccato', 'Clean. Calm. Humming.'),
    'calm': (0.45, 'staccato', 'Clean. Calm. Humming.'),
    'came_home': (0.50, 'beat', 'hold before "Her daughter."'),
    'recap': (0.50, 'recap', 'each rule re-read with its true reason'),
    'recap1': (0.50, 'recap', 'each rule re-read with its true reason: an even, deliberate rhythm'),
    'recap2': (0.50, 'recap', 'even recap rhythm'),
    'recap3': (0.50, 'recap', 'even recap rhythm'),
    'recap4': (0.50, 'recap', 'even recap rhythm'),
    'recap5': (0.50, 'recap', 'even recap rhythm'),
    'recap6': (0.50, 'recap', 'the last rule of the recap'),
    'recap7': (0.60, 'recap', 'the trailing "..." of sunrise'),
    'count_4': (0.15, 'split', '"Four," June whispers.'),
    'count_whisper2': (0.60, 'count', '"Four," June whispers. ... "Five." spaced like counting'),
    'count_5': (0.90, 'paragraph', 'the decision'),
    'not_her': (0.80, 'paragraph', 'the act'),
    'easiest': (1.30, 'held', 'held dread before "Six. Seven."'),
    'six': (0.95, 'count', 'spaced like counting'),
    'seven': (1.30, 'section', 'eyes shut: blackout beat before the ending'),
    # the ending
    'holding_hand': (0.50, 'beat', 'hold before "Smiling."'),
    'own_face': (0.60, 'beat', 'hold before "And it hums."'),
    'it_hums': (1.00, 'paragraph', 'the aftermath'),
    'screamed': (0.35, 'staccato', 'the screams pile up'),
    'screamed_sixteen': (0.35, 'staccato', 'the screams pile up'),
    'screamed_name': (0.50, 'sentence', 'the police'),
    'police': (1.00, 'paragraph', 'the hospital now'),
    'where_now': (0.50, 'beat', 'the hospital'),
    'hospital': (0.50, 'beat', 'echo of the cold open'),
    'straight_as': (0.35, 'staccato', 'the report card'),
    'never_late': (0.40, 'staccato', 'the report card'),
    'hums_all': (0.90, 'paragraph', 'last Sunday'),
    'lap': (0.35, 'dialogue', 'June\'s whisper follows its cue'),
    'car': (0.90, 'held', 'dread before the old body\'s question'),
    'x_trick': (1.50, 'held', 'held dread before "Easter is in nine days."'),
    'nine_days': (2.80, 'before outro', 'the story ends: about 2.5-3 s of silence before "Okay. Breathe."'),
    # outro
    'outro': (0.45, 'beat', '"Okay." "Breathe."'),
    'breathe': (0.50, 'beat', 'calming'),
    'no_holloway': (0.30, 'list', 'the list of things that aren\'t real'),
    'no_pembertons': (0.30, 'list', 'the list'),
    'costume': (0.40, 'sentence', 'running'),
    'never_did': (0.90, 'paragraph', 'back to the comments'),
    'reply': (0.35, 'staccato', '"Gently."'),
    'gently_reply': (0.35, 'staccato', 'running'),
    'said_mom': (0.50, 'beat', 'the joke lands: "She liked you too."'),
    'liked_you': (0.85, 'paragraph', 'the like'),
    'like': (0.40, 'sentence', 'the subscribe'),
    'subscribe': (0.40, 'sentence', 'the reason'),
    'one_rule': (0.90, 'paragraph', 'next time'),
    'next': (1.10, 'paragraph', 'the goodbye'),
    'sleep_well': (0.55, 'beat', 'last line'),
}


def pacing_rows():
    """One row per line boundary: (i, gap, kind, reason)."""
    para = paragraphs()
    rows = []
    rule_text_open = None
    for i in range(len(LINES) - 1):
        A, B = LINES[i], LINES[i + 1]
        same_para = para[i] == para[i + 1]
        ra, rb = rule_no(A['tag']), rule_no(B['tag'])
        if A['tag'] and re.fullmatch(r'rule\d_text', A['tag']): rule_text_open = para[i]
        if A['tag'] in PACE:
            g, kind, why = PACE[A['tag']]
        elif rb:
            g, kind, why = 1.40, 'before rule', f'rule card {rb}'
        elif ra:
            g, kind, why = 0.55, 'rule title', '"Rule number %d." then the rule itself' % ra
        elif rule_text_open is not None and para[i] == rule_text_open and same_para:
            g, kind, why = 0.45, 'rule text', 'the rule card text'
        elif rule_text_open is not None and para[i] == rule_text_open:
            g, kind, why = 1.00, 'after rule', 'the rule card holds, then the scene'
        elif not re.search(r'[.?!]["\']?$|\.\.\.$', A['en'].strip()):
            g, kind, why = 0.18, 'split', 'one sentence split for the speaker (quote / "she says")'
        elif not same_para:
            g, kind, why = 0.85, 'paragraph', 'paragraph break'
        elif A['who'] != 'N' or B['who'] != 'N':
            g, kind, why = 0.35 if A['who'] == B['who'] else 0.40, 'dialogue', 'dialogue'
        elif len(A['en'].split()) <= 3 and len(B['en'].split()) <= 3:
            g, kind, why = 0.40, 'staccato', 'short fragments'
        else:
            g, kind, why = 0.45, 'sentence', 'running narration'
        if rule_text_open is not None and para[i + 1] != rule_text_open: rule_text_open = None
        rows.append((i, round(g, 3), kind, why))
    return rows


def write_pacing(force=False):
    if os.path.exists(PACING) and not force:
        log('pacing map exists (use --force to rewrite):', PACING); return
    rows = pacing_rows()
    L_ = LINES
    with open(PACING, 'w') as f:
        f.write('# Pacing map: every gap between two lines of the edited narration\n\n')
        f.write('Written by `film/tools/vo_edit.py pacing` from the rules in that file (PACE, pacing_rows) and read back by '
                '`vo_edit.py build`: **this table is the source of truth**; change a gap here and rebuild.\n\n')
        f.write('A gap is the silence from the end of one line\'s natural decay (-60 dBFS) to the first sound of the next. '
                'The guide (from the brief): commas and running phrases inside a line keep a natural 0.12-0.30 s; '
                'sentences in running narration 0.35-0.6 s; staccato fragments 0.3-0.5 s; dialogue 0.3-0.6 s; '
                'paragraph breaks 0.7-1.0 s; before each "Rule number" 1.2-1.6 s and after its rule text 0.8-1.2 s; '
                'held dread before the reveal lines 1.0-1.8 s; fast action (rule six, the window to the lock) '
                '0.2-0.35 s; counts spaced like counting (0.9-1.0 s); about 1 s before the comment prompt and '
                '2.5-3 s before the outro. Never under 0.15 s between sentences (a line split for its speaker, '
                '"One," / "June whispers.", may sit at 0.15-0.2 s), never over 2 s except the outro.\n\n')
        f.write('Pauses inside a line are not in this table: they keep the take\'s own timing, clamped by punctuation '
                '(comma 0.12-0.30 s, colon 0.25-0.45 s, ellipsis 0.45-0.80 s, a mid-line full stop 0.30-0.55 s, '
                'no mark <= 0.25 s), with these held exceptions (INTERNAL in vo_edit.py):\n\n')
        for tag, d in INTERNAL.items():
            i = next(k for k, l in enumerate(L_) if l['tag'] == tag)
            for w, g in d.items():
                f.write(f'- line {i} ({tag}): {g:.2f} s after "{w}" in "{L_[i]["en"]}"\n')
        f.write('\n| # | after (end of line) | before (start of next line) | kind | gap s | why |\n')
        f.write('|---:|---|---|---|---:|---|\n')
        for i, g, kind, why in rows:
            a = L_[i]['en']; b = L_[i + 1]['en']
            a = ('...' + a[-38:]) if len(a) > 41 else a
            b = (b[:38] + '...') if len(b) > 41 else b
            f.write(f'| {i} | {L_[i]["who"]}: {a} | {L_[i + 1]["who"]}: {b} | {kind} | {g:.2f} | {why} |\n')
    log(f'pacing map: {len(rows)} boundaries -> {PACING}')


def read_pacing():
    gaps = {}
    for row in open(PACING):
        m = re.match(r'\|\s*(\d+)\s*\|.*\|\s*([\w \-]+?)\s*\|\s*([\d.]+)\s*\|\s*(.*?)\s*\|\s*$', row)
        if m: gaps[int(m.group(1))] = (float(m.group(3)), m.group(2), m.group(4))
    missing = [i for i in range(len(LINES) - 1) if i not in gaps]
    assert not missing, f'pacing map lacks boundaries {missing[:10]}'
    return gaps


# ============================================================================ assembly
def fade(n, kind, equal_power=False):
    """Raised-cosine fade (to / from silence), or the sin / cos pair of an equal-power crossfade."""
    t = np.linspace(0, 1, n, endpoint=False) + 0.5 / n
    if equal_power:
        return np.sin(t * np.pi / 2) if kind == 'in' else np.cos(t * np.pi / 2)
    return np.sin(t * np.pi / 2) ** 2 if kind == 'in' else np.cos(t * np.pi / 2) ** 2


def render_piece(x, pc):
    a, b = int(round(pc['src'][0] * SR)), int(round(pc['src'][1] * SR))
    y = x[a:b].copy()
    fi, fo = int(pc['fi'] * SR), int(pc['fo'] * SR)
    if fi and len(y) > fi: y[:fi] *= fade(fi, 'in', pc.get('xf_in', False))
    if fo and len(y) > fo: y[-fo:] *= fade(fo, 'out', pc.get('xf_out', False))
    return y


def speech_level(y):
    """dB of the louder speech frames (the mean power of 10 ms frames within 20 dB of the line's loudest)."""
    w = int(0.01 * SR)
    n = len(y) // w
    if n < 3: return -99.0
    p = (y[:n * w].reshape(n, w) ** 2).mean(1)
    pdb = 10 * np.log10(p + 1e-20)
    sel = pdb > pdb.max() - 20
    return float(10 * np.log10(p[sel].mean() + 1e-20))


def assemble(T, spans, gaps, lead=0.30, tail=0.60):
    """Lay the lines end to end with the map's gaps. Returns the signal, the edit list and the line output times."""
    x = T.x
    lines_out = []
    # line signals first (pieces with their internal gaps / crossfades)
    sigs = []
    for i in range(len(LINES)):
        pcs = line_pieces(T, i, spans[i])
        parts, pos, placed = [], 0, []
        buf = np.zeros(0)
        for k, pc in enumerate(pcs):
            y = render_piece(x, pc)
            if k == 0:
                buf = y; placed.append((0, len(y))); continue
            if pc['xfade_before'] > 0:
                n = min(int(pc['xfade_before'] * SR), len(y), len(buf))
                start = len(buf) - n
                # equal-power: both sides already carry sin^2 / cos^2 ramps of the same length (fi / fo)
                nb = np.zeros(start + len(y)); nb[:len(buf)] = buf; nb[start:start + len(y)] += y
                buf = nb; placed.append((start, start + len(y)))
            else:
                g = int(round(pc['gap_before'] * SR))
                start = len(buf) + g
                nb = np.zeros(start + len(y)); nb[:len(buf)] = buf; nb[start:] = y
                buf = nb; placed.append((start, start + len(y)))
        sigs.append((buf, pcs, placed))
    # per-line gain (narrator lines; characters are levelled after their voice transform)
    lv = np.array([speech_level(s[0]) for s in sigs])
    nar = [k for k in range(len(LINES)) if LINES[k]['who'] == 'N' and len(LINES[k]['en']) >= 12]
    med = float(np.median(lv[nar]))
    gains = []
    for k in range(len(LINES)):
        d = med - lv[k]
        g = 0.0 if abs(d) < 1.5 else float(np.clip(0.6 * d, -3, 3))
        gains.append(round(g, 2))
    total = int((lead + sum(len(s[0]) / SR for s in sigs) + sum(gaps[i][0] for i in range(len(LINES) - 1)) + tail) * SR) + 10
    out = np.zeros(total)
    t = lead
    edl = []
    for i, (buf, pcs, placed) in enumerate(sigs):
        a = int(round(t * SR))
        out[a:a + len(buf)] += buf * 10 ** (gains[i] / 20)
        t0 = a / SR; t1 = (a + len(buf)) / SR
        items = []
        for pc, (p, q) in zip(pcs, placed):
            it = {'src': [round(pc['src'][0], 4), round(pc['src'][1], 4)], 'out': [round(t0 + p / SR, 4), round(t0 + q / SR, 4)],
                  'fade_in_ms': round(pc['fi'] * 1000, 1), 'fade_out_ms': round(pc['fo'] * 1000, 1)}
            if pc.get('gap_before'): it['pause_before'] = pc['gap_before']
            if pc.get('xfade_before'): it['crossfade_ms'] = round(pc['xfade_before'] * 1000, 1)
            if pc.get('why'): it['why'] = pc['why']
            if 'orig_gap' in pc: it['pause_in_take'] = round(pc['orig_gap'], 3)
            items.append(it)
        g = gaps.get(i, (tail, 'end', 'end of the narration'))
        edl.append({'i': i, 'who': LINES[i]['who'], 'tag': LINES[i]['tag'], 'fx': LINES[i]['fx'], 'en': LINES[i]['en'],
                    'out': [round(t0, 4), round(t1, 4)], 'src_span': [round(spans[i]['span'][0], 4), round(spans[i]['span'][1], 4)],
                    'gain_db': gains[i], 'level_db': round(float(lv[i]), 2), 'pieces': items,
                    'removed_inside': spans[i]['removed'], 'gap_after': g[0], 'gap_kind': g[1], 'gap_why': g[2]})
        lines_out.append((t0, t1))
        t = t1 + (gaps[i][0] if i in gaps else 0)
    end = int(round((lines_out[-1][1] + tail) * SR))
    return out[:end], edl, lines_out, med


# ============================================================================ cleanup chain (whole file)
def highpass(y, fc=70.0):
    from scipy import signal
    return signal.sosfilt(signal.butter(4, fc, 'highpass', fs=SR, output='sos'), y)


def deess(y, split=4500.0, max_cut_db=5.0, rel_thr_db=-4.0):
    """Split-band de-esser for hot sibilants only: the band above 4.5 kHz is turned down where its 5 ms level rises
    above (the loudest low-band level within +-150 ms, i.e. the neighbouring vowel) + rel_thr_db, by the excess, at
    most max_cut_db; instant attack (1 ms frames, 5 ms window), 40 ms release. Zero-phase complementary split
    (lo = filtfilt LP, hi = y - lo): where nothing is cut the signal is rebuilt exactly."""
    from scipy import signal
    from scipy.ndimage import maximum_filter1d
    sos = signal.butter(4, split, 'lowpass', fs=SR, output='sos')
    lo = signal.sosfiltfilt(sos, y); hi = y - lo
    eh = envelope(hi); el = envelope(lo)
    ref = maximum_filter1d(el, size=301, mode='nearest')
    over = np.clip(eh - (ref + rel_thr_db), 0, max_cut_db)
    over[ref < -45] = 0.0
    g = np.empty_like(over); s_ = 0.0; a = np.exp(-1 / 40.0)
    for k, v in enumerate(over):
        s_ = v if v > s_ else s_ * a + v * (1 - a)
        g[k] = s_
    tf = np.arange(len(g)) * (SR // 1000) + int(0.0025 * SR)
    gs = np.interp(np.arange(len(y)), tf, g)
    return lo + hi * 10 ** (-gs / 20), round(float((g > 0.5).mean()), 4), round(float(g.max()), 2)


def loudness(y):
    import pyloudnorm as pyln
    return float(pyln.Meter(SR).integrated_loudness(y))


def limiter(y, ceil_db=-1.0, att=0.003, rel=0.050):
    """Peak limiter for the rare overs: each group of samples above the ceiling gets one smooth gain dip (raised-cosine
    attack over the 3 ms before it, hold, 50 ms raised-cosine release) deep enough for its loudest sample."""
    ceil = 10 ** (ceil_db / 20)
    over = np.where(np.abs(y) > ceil)[0]
    if not len(over): return y, 0, 0.0
    A, R = int(att * SR), int(rel * SR)
    g = np.ones(len(y))
    cuts = np.where(np.diff(over) > R)[0]
    groups = np.split(over, cuts + 1)
    deepest = 1.0
    for grp in groups:
        a, b = int(grp[0]), int(grp[-1])
        need = float((ceil / np.abs(y[grp])).min()) * 0.999
        deepest = min(deepest, need)
        s0, e0 = max(0, a - A), min(len(y), b + R + 1)
        env = np.full(e0 - s0, need)
        na = a - s0
        if na > 0: env[:na] = 1 - (1 - need) * fade(na, 'in')
        nr = e0 - (b + 1)
        if nr > 0: env[-nr:] = need + (1 - need) * (1 - fade(nr, 'out'))
        g[s0:e0] = np.minimum(g[s0:e0], env)
    return y * g, int((g < 0.999).sum()), round(float(20 * np.log10(deepest)), 2)


def true_peak(y, n=400):
    """True peak (dBFS) estimated with 4x oversampling around the n largest samples."""
    from scipy.signal import resample_poly
    idx = np.argpartition(np.abs(y), -n)[-n:]
    best = float(np.abs(y).max())
    for k in idx:
        a, b = max(0, k - 64), min(len(y), k + 64)
        best = max(best, float(np.abs(resample_poly(y[a:b], 4, 1)).max()))
    return 20 * np.log10(best + 1e-12)


def silence_mask(edl, n, pre=0.015, post=0.030, ramp=0.005):
    """1 over every line (from 15 ms before its first sound to 30 ms after its last), 0 in the gaps, 5 ms ramps."""
    m = np.zeros(n)
    r = int(ramp * SR); up = fade(r, 'in')
    for e in edl:
        a = max(0, int((e['out'][0] - pre) * SR)); b = min(n, int((e['out'][1] + post) * SR))
        m[a:b] = 1.0
        if a - r >= 0: m[a - r:a] = np.maximum(m[a - r:a], up)
        if b + r <= n: m[b:b + r] = np.maximum(m[b:b + r], up[::-1])
    return m


def finish(y):
    """The narrator's gentle cleanup: 70 Hz high-pass and the de-esser. Level is set later from the peak."""
    st = {}
    y = highpass(y)
    y, st['deess_share'], st['deess_max_db'] = deess(y, rel_thr_db=DEESS_THR_DB, max_cut_db=DEESS_MAX_DB)
    return y, st


# ============================================================================ commands
def cmd_analyze():
    T = Take()
    log(f'clip repair: {T.clip}; {len(T.isl)} islands; {len(T.words)} ASR words; lines without words: {T.missing}')
    log('ASR words owned by no line:', [(T.words[k][0], T.words[k][1]) for k in T.unowned])
    spans, between, owner = line_spans(T, verbose=True)
    for i in range(len(LINES)):
        sp = spans[i]
        rm = ', '.join('%s %.2f-%.2f (%.0f dB)' % (r['why'], r['src'][0], r['src'][1], r['peak_db']) for r in sp['removed'])
        print('%3d %-2s %8.3f %8.3f %s%s %-44s %s' % (i, LINES[i]['who'], sp['span'][0], sp['span'][1],
              'C' if sp['cut_in'] else '.', 'C' if sp['cut_out'] else '.', LINES[i]['en'][:44], ('REMOVED: ' + rm) if rm else ''))
    print('between lines (dropped):')
    for r in between: print('   %-12s %8.3f %8.3f  %6.1f dB' % (r['why'], r['src'][0], r['src'][1], r['peak_db']))


def cmd_build():
    try:
        from vo_voices import apply_voices                             # noqa
    except ImportError:
        log('tools/vo_voices.py missing: narration_en.wav = narration_clean.wav')
        apply_voices = lambda y, edl, sr: (y.copy(), [])
    T = Take()
    log(f'clip repair: {T.clip}; {len(T.isl)} islands; lines without words: {T.missing}')
    spans, between, _ = line_spans(T)
    gaps = read_pacing()
    y, edl, lines_out, med = assemble(T, spans, gaps)
    log(f'assembled: {len(y) / SR:.2f} s, narrator median speech level {med:.1f} dB')
    clean, st = finish(y)
    voiced, vrep = apply_voices(clean, edl, SR)                     # character voices on the quoted words only
    gate = silence_mask(edl, len(clean))                            # the gaps are digital silence (no filter tails)
    clean = clean * gate; voiced = voiced * gate
    pk = max(true_peak(clean), true_peak(voiced))
    g = 10 ** ((PEAK_CEIL - pk) / 20)                               # one gain, no limiter: the dynamics stay the take's
    clean = clean * g; voiced = voiced * g
    st.update({'gain_db': round(20 * np.log10(g), 2), 'lufs': round(loudness(clean), 2), 'true_peak_dbtp': round(true_peak(clean), 2)})
    st_en = {'lufs': round(loudness(voiced), 2), 'true_peak_dbtp': round(true_peak(voiced), 2)}
    sf.write(OUT_CLEAN, clean.astype(np.float32), SR, subtype='PCM_24')
    sf.write(OUT, voiced.astype(np.float32), SR, subtype='PCM_24')
    log(f'narration_clean.wav: {len(clean) / SR:.2f} s {st}')
    log(f'narration_en.wav: {st_en}')
    json.dump({'source': os.path.relpath(RAW, FILM), 'asr': os.path.relpath(ASR, FILM), 'pacing_map': os.path.relpath(PACING, FILM),
               'sr': SR, 'duration': round(len(clean) / SR, 3), 'clip_repair': T.clip,
               'fixes': {k: str(v) for k, v in FIXES.items()}, 'internal_pauses': INTERNAL,
               'narrator_median_level_db': round(med, 2), 'chain_clean': st, 'chain_en': st_en, 'voices': vrep,
               'lines': edl, 'removed_between_lines': between}, open(EDL, 'w'), indent=1)
    json.dump({'clean': st, 'en': st_en, 'duration': round(len(clean) / SR, 3), 'clip': T.clip,
               'n_removed_between': len(between), 'n_removed_inside': sum(len(e['removed_inside']) for e in edl)},
              open(STATS, 'w'), indent=1)
    log('edit list ->', EDL)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'analyze'
    if cmd == 'analyze': cmd_analyze()
    elif cmd == 'pacing': write_pacing('--force' in sys.argv)
    elif cmd == 'build': cmd_build()
    elif cmd == 'check':
        from vo_check import main as check_main                       # noqa
        check_main()
    else: raise SystemExit(__doc__)
