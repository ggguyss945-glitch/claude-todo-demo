"""The voiceover edit: the owner's raw TTS take -> a clean, paced narration (English only).
    python3 vo_edit.py analyze        per-line source spans, what gets removed, internal pauses (prints; writes nothing)
    python3 vo_edit.py pacing [--force]   write W/narration/pacing_map.md from the rules + PACE below (keeps an existing
                                      map unless --force: the map is the source of truth, edit it by hand if you like)
    python3 vo_edit.py build          read pacing_map.md -> narration_clean.wav (edited, no character voices),
                                      narration_en.wav (+ character voices, tools/vo_voices.py), edit_list.json,
                                      W/narration/build_stats.json (numbers for voice_report.md)
    python3 vo_edit.py check          scan the edited files (residual breaths, clicks, gaps vs the map, peaks, loudness)
                                      and draw the before/after strips into W/narration/tests/; after align.py, also
                                      every line against the recogniser (tools/vo_asrcheck.py; fails the check)
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
     in the last real dip before the next line's first word (split_point; SPLITS hand-sets the four the TTS ran together
     with no dip). An island where the next line's first word starts is never claimed by the line before, and a
     line-final piece under 60 ms is dropped unless the line ends in a stop (fix round 1: the "In-" / "A-" / "O-" ticks
     and the words cut in half, "wood | pile", "Se | ven"). A loud pitched island that would be dropped stops the build.
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
RAW = os.path.join(N, 'raw', 'narration_raw_44k.wav')     # tools/vo_join.py: the seven parts as one take
SRC_SR = 44100                                                    # the take's rate
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
PEAK_CEIL = -1.0                                                  # dBTP: one gain for both files puts the true peak here
CLIP_THR = 0.700                                                  # the take is hard-limited at 0.705: flat 1-2 sample tops at >= 0.700 are redrawn
DEESS_THR_DB, DEESS_MAX_DB = -7.0, 6.0                            # sibilants above (vowel level - 7 dB) come down

# ============================================================================ the TTS slips (raw-file seconds)
# Each was found by comparing two recognisers (Parakeet TDT, Whisper base.en) with the script, then cut by eye on 2 ms
# spectrograms with the pitch track; every repaired phrase is re-recognised by both (voice_report.md).
FIXES = {
    # cold open: "his head wrapped round and round in old yellow tape... he looks up at you" (the take has no "and"):
    # the "and" of "...all the way across the room, and tore a ticket" (621.785-621.945: said after a comma pause, as
    # here after the ellipsis; 131 -> 113 Hz, into this "he" at 107 Hz; it ends where the voicing stops before the t
    # closure of "tore") goes in front of "he", no gap (the d is unreleased into the h). Both recognisers: "tape and he
    # looks up at you and says very".
    'open_kindly': {'prepend': [(621.785, 621.945)]},
    # "Nurse. Always notice." (script "Nurses always notice."): the s of "Nurse" is trimmed to 0.10 s (151.72), the "is"
    # of "Let me take his pulse" (774.800-774.930: the vowel after the h, 208 -> 172 Hz, between this "Nurse" (ends
    # rising to 241 Hz) and "always" (158-172 Hz); its z ends at the p closure of "pulse") joins it with a 6 ms
    # equal-power crossfade, and "always notice." follows after 30 ms. Parakeet: "Nurses always notice."; Whisper:
    # "nurse is always notice" (the same sounds: "nur-siz").
    'nurses_notice': {'pieces': [(None, 151.72, 0.0, 0.003, 0.0), (774.800, 774.930, 0.0, 0.0, 0.008, 0.006),
                                 (152.035, None, 0.030, 0.003, 0.010)]},
    # "That's what the voice told you in 1979 in 1979.": the first "in 1979" already falls to a full stop (f0 -> 100 Hz
    # on "nine"); the line ends there (501.335, in the dip before the second "in") on a 25 ms fade. Both recognisers:
    # "That's what the voice told you in 1979."
    'voice_told': {'end': 501.335, 'end_fade': 0.025},
    # "rah-rahs of plastic chairs": the take has no usable "Rows" (its second syllable reads "ras"/"ross"). Built from
    # the clean word-initial r of the first "rah" (528.675-528.745), the "ow" of "in the last row," (571.935-572.200,
    # 165 -> 115 Hz) and the take's own "-z of plastic chairs" from 529.640, joined by 10 ms equal-power crossfades.
    # Both recognisers: "rows of plastic chairs" (a grid of 9 joins tried: row end 572.18-572.24 and z start 529.62-529.66
    # read right; later z starts read "row of", earlier row ends "ruff").
    'chairs': {'start': 529.640, 'prepend': [(528.675, 528.745), (571.935, 572.200)], 'join': 'xfade'},
    # "and I'm, s-, I'm sitting": the first "I'm" (945.71-946.08) and the stray "s" (946.13-946.27) go; "and" then the
    # second "I'm", the one said into "sitting", 0.12 s later (as the take's own pause after "and"). Both: "...in the
    # morning, I'm sitting in a little office".
    'office': {'cuts': [(945.650, 946.330, 0.12)]},
    # "Rule number four." and its text share one island only through a 10 ms blip in the silence (370.16): the line
    # ends where "four" decays into digital silence and the rule text starts on the "I" of "If"
    'rule4': {'end': 370.066},
    'rule4_text': {'start': 370.385},
    # "don't get on. the Sleemith well." (script "Sleep well."): the weak schwa before the S (1157.92-1158.01) goes;
    # "slee" ends where its clean "ee" ends (1158.370, before the "m"-like glide), a 65 ms closure stands for the p, and
    # the take's aspiration (1158.52-1158.61) is its release into "well". Both recognisers: "Don't get on. Sleep well."
    # "Take a seat." (cold open): the k of "Take" releases into 50 ms of hissy aspiration that both recognisers hear as
    # "Takes a seat"; 40 ms of it (29.565-29.605) go, joined by a 10 ms equal-power crossfade (the burst and 10 ms of
    # aspiration stay). Both: "Take a seat."
    'open_seat': {'cuts': [(29.565, 29.605, 0.0, 0.010)]},
    # "From Grandpa's chair. Rule number three." ran together through one r ("chai-r-ule"): the split sits at the r's F3
    # minimum (SPLITS) and "Rule" gets a clean word-initial r from "Rule number six." (515.225-515.285, 125-135 Hz)
    # crossfaded (10 ms) into the take's "-ule number three." from 322.130. Both: "Rule number three."
    'rule3': {'start': 322.130, 'prepend': [(515.225, 515.285)], 'join': 'xfade'},
    # "said Doctor Halverson.": the d of "said" came out as a hissy z (Parakeet: "says"); the hiss (413.045-413.130) goes
    # and 30 ms of silence join the d closure of "Doctor". Both: "said Doctor Halverson."
    'said_halverson': {'cuts': [(413.045, 413.130, 0.03)]},
    'sleep_well': {'pieces': [(1158.012, 1158.370, 0.0, 0.004, 0.010), (1158.520, None, 0.065, 0.002, 0.020)]},
}
# two lines the TTS ran together in one sound island: the split time (raw seconds), set by eye where split_point's dip
# search would land inside a word
SPLITS = {
    'grandpa_chair': 322.120,  # "chair | Rule": one shared r; the cut sits at its F3 minimum (1250-1390 Hz) (was 321.862: "ch | air")
    'call_you': 174.295,       # "...come in, | she said": the n murmur of "in" ends where the sh starts (was 174.432: inside "she")
    'rule2_ever': 280.600,     # "Ever. | The phone cord": the dip where the voiced th of "The" starts (was 280.752: "The | phone")
    'knees': 469.700,          # "head, | Waiting.": the middle of the dip before the w (was 469.721: on the w onset)
    'waiting_bench': 470.005,  # "Waiting. | Rule": the "-ing" vowel ends (F2 2490 Hz) where F2 falls into the r (was 469.928: inside "-ing")
}
# a hand-set split sits in voiced sound, so the line before it fades out over SPLIT_FO and the line after fades in over
# SPLIT_FI
SPLIT_FO, SPLIT_FI = 0.030, 0.010
# pauses inside a line, by the word they follow (line tag -> {word: seconds})
INTERNAL = {
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
    x24, sr = sf.read(RAW, dtype='float64')                      # (x24: the take at its own rate, 44.1 kHz here)
    assert sr == SRC_SR, sr
    x24, clip = declip(x24, thr=CLIP_THR)
    x = soxr.resample(x24, SRC_SR, SR, quality='VHQ')
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
    p = parselmouth.Sound(x24, sampling_frequency=SRC_SR).to_pitch_ac(time_step=0.005, pitch_floor=70, pitch_ceiling=600,
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
       'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50', 'seventy': '70', 'eighty': '80', 'nineteen': '19',
       'hundred': '100', 'mr': 'mister', 'dr': 'doctor', 'gray': 'grey', 'shh': 'sh', 'shhh': 'sh', 'genes': 'jeans'}
JOIN = {('any', 'more'): 'anymore', ('arm', 'chair'): 'armchair', ('grown', 'up'): 'grownup', ('2', 'night'): 'tonight',
        ('rear', 'view'): 'rearview', ('land', 'line'): 'landline', ('type', 'writer'): 'typewriter',
        ('cardi', 'gan'): 'cardigan', ('peep', 'hole'): 'peephole', ('street', 'light'): 'streetlight',
        ('wheel', 'chair'): 'wheelchair', ('clip', 'board'): 'clipboard', ('drive', 'way'): 'driveway',
        ('head', 'lights'): 'headlights', ('grass', 'hopper'): 'grasshopper', ('over', 'night'): 'overnight'}


def toks(s, keep_index=False):
    """Normalised word tokens (as align.py: lower case, clock times split, number words -> digits, possessives dropped)
    and, with keep_index, the index of the text word each token came from."""
    s = s.lower().replace('’', "'").replace('—', ' ')
    s = re.sub(r'\b1979\b', 'nineteen seventy-nine', s)                   # the year as it is read
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
            m = re.fullmatch(r'([1-9])(\d\d)', n)                         # '301' (the recogniser's three-oh-one) -> 3 0 1
            if m:
                for d in (m.group(1), '0', str(int(m.group(2)))) if m.group(2)[0] == '0' else (m.group(1), m.group(2)):
                    out.append(d); src.append(wi)
                continue
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
# word-less islands between lines that are known TTS noises (dropped on purpose; the recognisers read them as words):
# the "Mm." after "Halfway to the hospital," (a long inhale), the "Uh" after "picked up the phone and dialed." and the
# voiced "Mm-hmm." after "I'm a pediatrician now."
KNOWN_NOISE = [825.85, 920.35, 942.55]


def coda_ok(word, gap, dur, peak=-99.0):
    """Can an unvoiced island 'gap' s after a word's last sound be that word's own ending? The TTS often leaves a short
    dip before a final consonant: a stop's release with its aspiration ("suit", "night", "it", "Lock", "Thunk") comes
    up to 0.10 s later and lasts up to 0.20 s; a final s ("since", "sense", "use", "Silence") up to 0.09 s later and
    louder than -32 dB; the s of a stop + s ending
    ("six", "knocks") comes after the closure, up to 0.17 s later. A breath comes later, lasts longer, or (after an
    s that is already there, "spotless", "eggs") is much quieter than an s (-35..-45 dB against -17..-27 dB)."""
    w = re.sub(r'[^a-z]', '', word.lower())
    if re.search(r'(x|ts|ks|ps|ds|cks|cts|pts|kes|tes|pes|des|xes)$', w): return gap <= 0.17 and dur <= 0.40
    if re.search(r'(t|k|p|c|ck|ct|pt|ed|d|de|te|ke|pe|g|b|ght)$', w): return gap <= 0.10 and dur <= 0.20
    if re.search(r've$', w): return gap <= 0.04 and dur <= 0.30 and peak > -52       # a devoiced final v ("twelve")
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
    if re.match(r'(d|b|g)', w): return gap <= 0.03 and dur <= 0.04                     # a voiced stop's prevoicing
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


def split_point(T, i, isl_ab):
    """Where to split line i from line i + 1 when the TTS ran them together in one sound island. A hand-set SPLITS time
    wins. Else the window is anchored on the NEXT line's first word (its recognised start is the reliable anchor; the
    end of line i's last word is not): [start - 0.30, start + 0.08], never closer than 0.10 s to the start of line i's
    last word. In it, on a 10 ms envelope, the LAST real dip (the lowest point within +-25 ms, >= 20 dB under the
    island's p90; never the window's edge) is the
    boundary: a line's last word can hold its own dips (the closure before the z of "babie-s", the creak after
    "mother,") while nothing but the next word follows the last one. No real dip: the quietest point, logged as a cut
    inside running speech."""
    tag = LINES[i]['tag']
    if tag in SPLITS: return SPLITS[tag], 'hand-set (SPLITS)'
    W_ = T.words
    k_last = T.owned[i][-1]; k_next = T.owned[i + 1][0]
    a_isl, b_isl = isl_ab
    tn = W_[k_next][1]
    lo = max(W_[k_last][1] + 0.10, a_isl + 0.03, tn - 0.30)
    hi = min(tn + 0.08, b_isl - 0.03)
    if hi <= lo: lo, hi = max(a_isl + 0.03, tn - 0.10), min(b_isl - 0.03, tn + 0.06)
    seg = T.frames(a_isl, b_isl)
    p90 = float(np.percentile(seg, 90)) if len(seg) else 0.0
    win = T.frames(lo, hi)
    if len(win) >= 25:
        e = 10 * np.log10(np.convolve(10 ** (win / 10), np.ones(10) / 10, 'same') + 1e-20)
        r = 25                                                     # a dip is the lowest point within +-25 ms
        mins = [k for k in range(len(e)) if e[k] <= e[max(0, k - r):k + r + 1].min() + 1e-9 and e[k] <= p90 - 20
                and 0 < k < len(e) - 1]
        if mins:
            k = mins[-1]
            return lo + (k + 2.5) / 1000.0, 'last real dip, %.1f dB under the island p90' % (p90 - e[k])
    t = T.quietest(lo, hi, smooth=10)
    k = int(t * 1000); depth = p90 - float(T.db[max(0, k - 5):k + 5].mean())
    return t, 'quietest point, %.1f dB under the island p90 (SHALLOW: inside running speech)' % depth


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
    # island there is the breath after the word and stays free. Never an island where the next line's first word
    # starts (its recognised start within 0.15 s of the island's): the recogniser's end time of a line's last word
    # often runs into the next line's first word ("egg | In-side", "off | In-side", "door | At", "days | Okay", "woods |
    # Two"), and claiming it glued that word's first 30-150 ms to the end of the line before (fix round 1: 11 such
    # boundaries, the "In-" / "A-" / "O-" ticks). An island that starts well before the next word (a stop's release
    # merged with the next line's first fricative: "knoc-k she said") is still claimed and split in its dip.
    word_lines = [set(s_) for s_ in owner_of]                      # the lines whose words start in each island
    for i, ks in T.owned.items():
        for k in ks:
            j = word_island(T, k)
            if j is None: continue
            t1 = T.words[k][2]; prev_end = isl[j][1]
            for m in range(j + 1, len(isl)):
                a, b = isl[m]
                if a >= t1 or a - prev_end > 0.12: break
                if any(T.words[T.owned[o][0]][1] - a < 0.15 for o in word_lines[m] - {i} if T.owned.get(o)):
                    break                                           # the next line's first word starts right here

                pk = float(T.frames(a, b).max()); vp = float(T.voiced[int(a * 1000):int(b * 1000)].mean()) if b > a else 0.0
                if (vp >= 0.2 and pk > -40) or (pk > -30 and is_speechlike(T, a, b)):
                    owner_of[m].add(i); prev_end = b
                else:
                    break
    owned_isl = [j for j in range(len(isl)) if owner_of[j]]
    word_t0 = [(W_[k][1], k, i) for i, ks in T.owned.items() for k in ks]
    tail_guard = []                                                # islands kept from the line before (logged)
    in_word_bursts, decay_tails = [], []                           # islands kept by the stop-release / decay rules (logged)
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

    def next_line_t0(li):
        """Recognised start of the first word of the line after li (None at the end)."""
        if li is None or li + 1 >= len(LINES) or not T.owned.get(li + 1): return None
        return W_[T.owned[li + 1][0]][1]

    # pass 1, forward: voiced sound next to a line, and codas (a release may follow another release: "snapped").
    # An island that starts within 0.15 s of the next line's first word and sits nearer to that line's sound than to
    # the line before is never the previous line's coda or tail: it is the next word's onset (the breath onset of "A"
    # after "Two knocks."); a release that sits nearer its own word stays ("Whitloc-k" | "There's")
    for j in free:
        if j in dropped or owner_of[j]: continue
        p, q = isl[j]; dur, vp, vl, pk = feats(j)
        pj, nj = neighbours(j)
        gp = p - isl[pj][1] if pj is not None else 9.0
        gn = isl[nj][0] - q if nj is not None else 9.0
        li_prev = max(owner_of[pj]) if pj is not None else None
        li_next = min(owner_of[nj]) if nj is not None else None
        nt0 = next_line_t0(li_prev)
        if nt0 is not None and li_next is not None and li_next != li_prev and nt0 - p < 0.15 and gn < gp:
            li_prev_ok = False
        else:
            li_prev_ok = True
        wprev = next((W_[k][0] for t, k, i in reversed(word_t0) if t < p), '')
        near = li_prev if gp <= gn else li_next
        if near == li_prev and not li_prev_ok: near = li_next
        if not li_prev_ok and li_prev is not None:
            tail_guard.append(round(p, 3))
        if vp >= 0.2:                                              # pitched: speech (a word timed late, a voiced tail)
            if near is not None and ((min(gp, gn) <= 0.06 and pk > -55) or (pk > -40 and min(gp, gn) <= 0.35)):
                owner_of[j].add(near)
        elif vl >= 0.5 and ((min(gp, gn) <= 0.03 and pk > -55) or (gp <= 0.07 and pk > -40 and li_prev_ok)):
            tgt = near if min(gp, gn) <= 0.03 else li_prev        # a nasal / l murmur against its word ("smile")
            if tgt is not None: owner_of[j].add(tgt)
        elif li_prev is not None and li_prev_ok and coda_ok(wprev, gp, dur, pk):
            owner_of[j].add(li_prev)
        elif li_prev is not None and li_prev_ok and gp <= 0.025 and pk <= -38 and dur <= 0.08 and gn > 0.06:
            owner_of[j].add(li_prev)                               # the creaky end of a decaying word ("anyway", "her")
            decay_tails.append(round(p, 3))
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
    # pass 3: a short burst between two pieces of the same line, inside a recognised word: a stop's release between its
    # closure and the rest of the word ("doc-k-tors"); run last, once the islands on both sides are claimed
    for j in free:
        if j in dropped or owner_of[j]: continue
        p, q = isl[j]; dur, vp, vl, pk = feats(j)
        pj, nj = neighbours(j)
        if pj is None or nj is None: continue
        li_p, li_n = max(owner_of[pj]), min(owner_of[nj])
        if li_p == li_n and p - isl[pj][1] <= 0.04 and isl[nj][0] - q <= 0.04 and dur <= 0.06 \
                and any(W_[k][1] + 0.04 < p and q < W_[k][2] for k in T.owned[li_p]):
            owner_of[j].add(li_p); in_word_bursts.append(round(p, 3))
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
    split_log = []
    for i in range(len(LINES)):
        bounds[i] = [isl[first[i]][0], isl[last[i]][1], False, False]
    for i in range(len(LINES) - 1):                               # two lines in one island: split in its real dip
        if last[i] == first[i + 1]:
            t, how = split_point(T, i, isl[last[i]])
            split_log.append({'line': i, 'tag': LINES[i]['tag'], 'at': round(t, 4), 'how': how})
            bounds[i][1] = t; bounds[i][3] = True
            bounds[i + 1][0] = t; bounds[i + 1][2] = True
    for i, f in fx.items():                                       # hand-set starts / ends (the slips)
        if 'start' in f: bounds[i][0] = f['start']; bounds[i][2] = True
        if 'end' in f: bounds[i][1] = f['end']; bounds[i][3] = True
    out = {}
    short_tails = []
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
        # a line-final piece under 60 ms after a pause is a breath onset or the next line's first sound, unless the
        # line's last word ends in a stop (its release: "trick", "knocks")
        last_w = re.sub(r'[^a-z]', '', text_words(i)[-1].lower()) if text_words(i) else ''
        stop_end = bool(re.search(r'(t|k|p|c|d|b|ck|ct|pt|ght|ed|te|ke|pe|de|x|ts|ks|ps|ds|cks|cts|pts|kes|tes)$', last_w)) \
            or (last_w.endswith('g') and not last_w.endswith('ng'))
        while len(keep) > 1 and keep[-1][1] - keep[-1][0] < 0.06 and keep[-1][0] - keep[-2][1] > 0.015 and not stop_end \
                and not FIXES.get(LINES[i]['tag'], {}).get('end') and round(keep[-1][0], 3) not in decay_tails:
            short_tails.append({'line': i, 'src': [round(keep[-1][0], 3), round(keep[-1][1], 3)]})
            removed.append({'src': [round(keep[-1][0], 3), round(keep[-1][1], 3)], 'why': 'line-final tick (< 60 ms)', 'peak_db': 0.0})
            keep.pop()
        if keep:                                                   # the span is the sound: no leading / trailing silence
            a = max(a, keep[0][0]); b = min(b, keep[-1][1])
        out[i] = {'span': [a, b], 'keep': keep, 'removed': removed, 'cut_in': ci, 'cut_out': co}
    for i, f in fx.items():                                       # a line that reuses another line's take
        if 'reuse' in f:
            src_i = tag2i[f['reuse']]
            out[i] = dict(out[src_i]); out[i]['reused_from'] = src_i; out[i]['removed'] = []
    if verbose or split_log or short_tails or tail_guard or in_word_bursts or decay_tails:
        for r in split_log: log('split L%d/%d at %.4f: %s' % (r['line'], r['line'] + 1, r['at'], r['how']))
        for r in short_tails: log('dropped line-final tick L%d %.3f-%.3f' % (r['line'], r['src'][0], r['src'][1]))
        for t in tail_guard: log('island at %.3f kept off the line before (the next line\'s onset)' % t)
        for t in in_word_bursts: log('island at %.3f kept: a stop release inside a word' % t)
        for t in decay_tails: log('island at %.3f kept: the decaying end of a word' % t)
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
    if 'pieces' in f:                                              # a hand-built line (a slip repaired by splicing):
        pcs = []                                                   # (a, b, gap before, fade in, fade out[, crossfade]) in
        for spec in f['pieces']:                                   # seconds; None = the line's own first / last sound
            a_, b_, g, fi, fo = spec[:5]; xf = spec[5] if len(spec) > 5 else 0.0
            a_ = sp['span'][0] if a_ is None else a_
            b_ = sp['span'][1] if b_ is None else b_
            pc = {'src': [a_, b_], 'fi': fi, 'fo': fo, 'gap_before': 0.0 if xf else g, 'xfade_before': xf,
                  'why': 'slip repair: hand-set piece'}
            if xf and pcs:
                pc['fi'] = xf; pc['xf_in'] = True; pcs[-1]['fo'] = xf; pcs[-1]['xf_out'] = True
            pcs.append(pc)
        return pcs
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
        if len(g) > 2 and g[2] in ('cut_out', 'cut_in_out'): pc['fo'] = f.get('cut_fo', 0.010)
        if len(g) > 2 and g[2] in ('cut_in', 'cut_in_out'):
            pc['fi'] = 0.006
            pc['forced_gap'] = g[3]; pc['xf_len'] = g[4] if len(g) > 4 else 0.008
            if pieces: pieces[-1]['fo'] = max(pieces[-1]['fo'], 0.010)
        if prev_end is not None:
            pc['orig_gap'] = p - prev_end
        pieces.append(pc); prev_end = q
    if sp['cut_in']: pieces[0]['fi'] = 0.008
    if sp['cut_out']: pieces[-1]['fo'] = 0.010
    if sp['cut_out'] and tag in SPLITS: pieces[-1]['fo'] = SPLIT_FO
    if sp['cut_in'] and i > 0 and LINES[i - 1]['tag'] in SPLITS: pieces[0]['fi'] = SPLIT_FI
    if 'lead' in f and f['lead'] < pieces[0]['src'][0]:
        pieces[0]['src'] = [f['lead'], pieces[0]['src'][1]]; pieces[0]['why'] = (pieces[0]['why'] + ' lead-in on silence').strip()
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


# gap after the line with this tag: (seconds, kind, reason). Everything not listed here follows the rules in
# pacing_rows(): "Rule number N." 0.55 s then its text; 1.40 s before each "Rule number"; 1.00 s after the rule text;
# 0.18 s where one sentence is split for its speaker (quote / "she said."); 0.85 s at a paragraph break; 0.40 s
# between short fragments; dialogue 0.35-0.40 s; 0.45 s in running narration.
PACE = {
    # cold open
    'open': (0.60, 'beat', 'first rule of the hook: let "don\'t ask what they found" land'),
    'open_hold': (0.60, 'beat', 'second rule of the hook'),
    'open_room': (0.50, 'ellipsis', 'the sentence\'s own "..." before "and he looks up at you"'),
    'open_kindly': (0.35, 'dialogue', 'into his line, as said'),
    'open_seat': (0.45, 'dialogue', '"Take a seat." ... "It can wait.": slow, even, too calm'),
    'open_wait': (1.20, 'held', 'held dread after his line before "Don\'t sit down."'),
    'open_dont_sit': (1.00, 'paragraph', 'the hook ends; the phone-system recording comes in'),
    'hold_open': (0.35, 'dialogue', 'the automated recording\'s own rhythm'),
    'hold_open_please': (1.00, 'paragraph', 'out of the recording into the story (room for the hold-music sting)'),
    'about_waiting': (0.85, 'paragraph', 'beat before "And on the night my little brother almost died"'),
    'all_wrong': (0.85, 'paragraph', 'the tease'),
    'tease': (0.85, 'paragraph', 'the thesis line'),
    'difference': (1.30, 'section', 'end of the cold open: room for the title sting before Ruth'),
    # 1979
    'that_place': (0.85, 'paragraph', '1979'),
    'tinny_music': (0.45, 'sentence', 'running'),
    'voice_line': (0.45, 'beat', 'into "Calm. Patient. Kind."'),
    'calm': (0.40, 'staccato', 'Calm. Patient. Kind.: rhythmic'),
    'patient': (0.40, 'staccato', 'Calm. Patient. Kind.: rhythmic'),
    'kind': (0.90, 'held', 'hold before the 1979 voice ("It can wait until morning.")'),
    'it_can_wait_1979': (1.00, 'held', 'his line hangs before "So they waited."'),
    'waited': (0.45, 'sentence', 'running'),
    'armchair': (0.85, 'paragraph', 'paragraph break: sunrise'),
    'coffee': (0.85, 'held', 'the coffee: the gentle reveal starts'),
    'still_sitting': (1.00, 'held', 'held dread before "Still waiting."'),
    'still_waiting': (1.20, 'held', 'Grandpa died: a long, quiet beat'),
    'proved_it': (0.40, 'staccato', '"They were hiding something." follows'),
    'hiding': (0.85, 'paragraph', 'paragraph break'),
    'never_forgave': (0.90, 'section', 'out of 1979 into now'),
    # now: Mom, Milo, Halverson
    'didnt_speak': (0.85, 'paragraph', 'paragraph break: Milo'),
    'thirsty': (0.40, 'staccato', '"All the time."'),
    'all_the_time': (0.45, 'sentence', 'the symptoms list'),
    'mom_noticed': (0.40, 'staccato', '"Nurses always notice."'),
    'nurses_notice': (0.45, 'sentence', 'running'),
    'careful': (0.45, 'sentence', 'running'),
    'blood': (0.85, 'paragraph', 'into her promise'),
    'call_you': (0.18, 'split', '"...come in," / "she said."'),
    'day_or_night': (0.35, 'dialogue', '"Day or night. I mean it."'),
    'mean_it': (0.90, 'paragraph', 'paragraph break: that night'),
    'watching_us': (0.85, 'paragraph', 'sundown'),
    'card': (0.85, 'held', 'the card is shown'),
    'seven': (0.40, 'staccato', 'Seven rules. Typed on a typewriter.'),
    'typed': (0.40, 'staccato', 'fragments'),
    'weak_tea': (0.85, 'paragraph', 'Grandma speaks'),
    'same_as_always': (0.18, 'split', '"Same as always," / "Grandma said."'),
    'nobody_sick': (1.40, 'before rule', 'rule card 1'),
    # rule 1
    'rule1_text': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'call': (1.00, 'ring', 'room for the phone ring'),
    'landline': (0.40, 'staccato', '"Nobody calls the landline."'),
    'nobody_calls': (0.85, 'paragraph', 'paragraph break'),
    'whole_life': (0.85, 'paragraph', 'the rings'),
    'ring_seven': (0.60, 'ring', 'a ring sits here'),
    'tilted': (0.85, 'paragraph', 'the voice on the line'),
    'womans_voice': (0.40, 'staccato', 'A woman\'s voice. Rough. Out of breath.'),
    'rough': (0.40, 'staccato', 'fragments'),
    'out_of_breath': (0.40, 'staccato', 'fragments'),
    'running_crying': (0.85, 'paragraph', 'Doctor Halverson on the phone'),
    'this_is_halverson': (0.35, 'dialogue', 'her rushed call'),
    'sorry_hour': (0.35, 'dialogue', 'her rushed call'),
    'results_back': (0.25, 'cut off', 'Grandma cuts her off (still >= 0.15 s)'),
    'dont_tell': (0.18, 'split', '"Don\'t tell me," / "Grandma said."'),
    'dont_dare': (0.85, 'paragraph', 'the hang-up'),
    'hung_up': (0.85, 'ring', 'room for the click and the ring'),
    'rang_again': (0.55, 'ring', 'a ring between'),
    'and_again': (0.55, 'ring', 'a ring between'),
    'nine_times': (0.55, 'beat', 'the cord'),
    'cord': (1.00, 'held', 'the house goes quiet'),
    'scariest': (0.60, 'beat', '"I was wrong."'),
    'was_wrong': (0.50, 'beat', 'the tease'),
    'other_one': (1.00, 'before prompt', 'about 1 s before the comment prompt'),
    # the comment prompt
    'cta': (0.40, 'staccato', '"Okay. Hold on."'),
    'cta_hold': (0.40, 'staccato', 'the hold joke'),
    'cta_important': (0.85, 'paragraph', 'the ask'),
    'cta_word': (0.40, 'staccato', 'In the comments. Right now.'),
    'cta_comments': (0.40, 'staccato', 'fragments'),
    'cta_now': (0.85, 'paragraph', 'the question'),
    'cta_question': (0.60, 'beat', 'the two choices'),
    'cta_choice': (0.85, 'paragraph', 'let the choice sit'),
    'cta_one_word': (0.40, 'staccato', 'One word. Choose carefully.'),
    'cta_carefully': (0.45, 'beat', 'the sting: forty years'),
    'cta_forty': (1.40, 'before rule', 'rule card 2'),
    # rule 2
    'rule2_text': (0.45, 'rule text', '"Ever." completes the rule'),
    'rule2_ever': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'cord_floor': (0.85, 'held', 'the cord on the floor'),
    'rang_anyway': (1.00, 'ring', 'room for the impossible ring'),
    'picked_up': (0.45, 'sentence', 'running'),
    'no_voice': (0.45, 'beat', 'Just music. Hold music.'),
    'just_music': (0.40, 'staccato', 'fragments'),
    'hold_music': (0.60, 'beat', 'the hold music enters'),
    'tune': (0.85, 'paragraph', 'the recording'),
    'under_it': (0.45, 'beat', 'into the recording'),
    'recording_important': (0.40, 'dialogue', 'the recording\'s rhythm'),
    'recording_hold': (0.90, 'paragraph', 'out of the recording'),
    'receiver': (0.45, 'sentence', 'running'),
    'kept_playing': (0.40, 'staccato', '"All night."'),
    'all_night': (0.85, 'paragraph', 'time passes'),
    'not_only_phone': (0.60, 'beat', 'the rooms'),
    'rooms': (0.45, 'beat', 'From the hallway. From the living room.'),
    'rooms_living': (0.90, 'held', 'held dread before "From Grandpa\'s chair."'),
    'grandpa_chair': (1.40, 'before rule', 'rule card 3'),
    # rule 3
    'rule3_text': (0.45, 'rule text', '"He\'s listening." completes the rule'),
    'rule3_listening': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'cracked': (0.40, 'staccato', 'description'),
    'eyes_big': (0.85, 'paragraph', 'Milo speaks'),
    'so_thirsty': (0.18, 'split', '"I\'m so thirsty," / "he whispered."'),
    'tummy': (0.35, 'dialogue', 'his whisper runs on'),
    'tummy_really': (0.30, 'cut off', 'Grandma\'s hand cuts him off'),
    'clapped': (0.35, 'dialogue', 'into "Shh."'),
    'shh': (0.35, 'dialogue', 'her hushed lines'),
    'not_after_dark': (0.35, 'dialogue', 'her hushed lines'),
    'not_out_loud': (1.00, 'held', 'silence before the pen click'),
    'pen_click': (0.90, 'sfx', 'room for the pen click'),
    'scratch': (0.45, 'sfx', 'the scratching'),
    'writing_down': (0.90, 'paragraph', 'the sweet breath'),
    'sweet_breath': (0.40, 'staccato', 'Like fruit. Like nail-polish remover.'),
    'fruit': (0.40, 'staccato', 'fragments'),
    'nail_polish': (0.60, 'beat', 'hold'),
    'didnt_know': (0.85, 'held', 'held before "Doctor Halverson did."'),
    'halverson_did': (1.40, 'before rule', 'rule card 4'),
    # rule 4
    'rule4_text': (0.45, 'rule text', 'second sentence of the rule'),
    'rule4_house_calls': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'knock': (1.00, 'knock', 'room for the knock'),
    'raincoat': (0.40, 'staccato', 'description'),
    'soaked': (0.40, 'staccato', 'description'),
    'car_driveway': (0.85, 'paragraph', 'her voice through the door'),
    'ruth_door': (0.35, 'dialogue', 'her urgent, tired lines'),
    'anna': (0.35, 'dialogue', 'her lines'),
    'tried_to_call': (0.40, 'dialogue', 'the number'),
    'glucose': (0.40, 'dialogue', 'her lines'),
    'very_high': (0.40, 'dialogue', 'her lines'),
    'needs_insulin': (0.40, 'dialogue', '"This can\'t wait."'),
    'cant_wait': (0.85, 'dialogue', 'Grandma answers through the door'),
    'house_call': (0.18, 'split', '"...house calls," / "Grandma said through the door."'),
    'i_know': (0.18, 'split', '"I know," / "said Doctor Halverson."'),
    'making_one': (0.90, 'held', 'the door stays shut'),
    'didnt_open': (0.90, 'paragraph', 'the paper'),
    'lab_results': (0.45, 'sentence', 'running'),
    'marker': (0.60, 'beat', 'the note is read'),
    'note_thirsty': (0.40, 'list', 'the warning signs, one by one'),
    'note_peeing': (0.40, 'list', 'the warning signs'),
    'note_tired': (0.40, 'list', 'the warning signs'),
    'note_weight': (0.40, 'list', 'the warning signs'),
    'note_breath': (0.40, 'list', 'the warning signs'),
    'note_fast_deep': (0.50, 'list', 'the instruction'),
    'note_dont_wait': (0.45, 'list', 'her last line'),
    'note_car': (0.90, 'held', 'the match'),
    'burn': (0.90, 'paragraph', 'the window'),
    'calling_again': (0.85, 'paragraph', 'she isn\'t leaving'),
    'not_leaving': (0.45, 'beat', '"She was never going to leave."'),
    'never_leave': (0.90, 'paragraph', 'the bus stop'),
    'bus_stop': (0.60, 'beat', 'Very tall. Folded up. Knees above his head.'),
    'very_tall': (0.40, 'staccato', 'fragments'),
    'folded': (0.40, 'staccato', 'fragments'),
    'knees': (1.30, 'held', 'held dread before "Waiting."'),
    'waiting_bench': (1.40, 'before rule', 'rule card 5'),
    # rule 5
    'rule5_text': (0.45, 'rule text', '"It can wait." completes the rule'),
    'rule5_wait': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'breathing': (0.45, 'beat', 'Deep. Fast.'),
    'deep': (0.35, 'staccato', 'Deep. Fast.: like breaths'),
    'fast': (0.40, 'staccato', 'fragments'),
    'running_sleep': (0.40, 'staccato', 'the two "Like" lines'),
    'not_enough_air': (0.85, 'paragraph', 'he doesn\'t know me'),
    'who_i_was': (0.90, 'held', 'held: he doesn\'t know who I am'),
    'rocking': (0.45, 'dialogue', 'Grandma speaks'),
    'until_morning': (0.40, 'dialogue', '"It can wait. It can wait."'),
    'g_wait1': (0.45, 'dialogue', 'repeated, rocking'),
    'g_wait2': (0.85, 'dialogue', 'I answer'),
    'grandma_said': (0.40, 'dialogue', 'my answer runs on'),
    'voice_told': (0.90, 'held', '"She stopped rocking."'),
    'stopped_rocking': (0.90, 'held', 'her question'),
    'how_do_you_know': (0.85, 'dialogue', 'I answer'),
    'hear_it': (0.40, 'dialogue', 'my answer runs on'),
    'right_now': (0.90, 'held', 'the rooms'),
    'every_room': (1.00, 'held', 'held dread before "It can wait." from every room'),
    'rooms_wait': (1.40, 'before rule', 'rule card 6'),
    # rule 6
    'rule6_text': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'opened_door': (0.90, 'held', 'held before "It was a waiting room."'),
    'waiting_room': (0.90, 'held', 'the room is revealed'),
    'chairs': (0.40, 'list', 'the room\'s inventory'),
    'lights': (0.40, 'list', 'the room\'s inventory'),
    'tv': (0.40, 'list', 'the room\'s inventory'),
    'ticket_machine': (0.45, 'list', 'the sign'),
    'sign': (0.60, 'beat', 'the sign\'s numbers'),
    'now_serving': (1.00, 'held', 'NOW SERVING: 1979 sits'),
    'every_chair': (0.60, 'beat', 'the ghosts'),
    'ghosts': (0.40, 'list', 'the ghosts, one by one'),
    'ghost_woman': (0.40, 'list', 'the ghosts'),
    'ghost_teen': (0.40, 'list', 'the ghosts'),
    'ghost_girl': (0.45, 'list', 'All of them gray. All of them still.'),
    'all_gray': (0.35, 'staccato', 'fragments'),
    'all_still': (0.35, 'staccato', 'fragments'),
    'tickets': (0.60, 'beat', 'who they are'),
    'decided': (1.00, 'paragraph', 'the last row'),
    'last_row': (1.50, 'held', 'held dread before "Grandpa."'),
    'grandpa': (1.30, 'held', 'Grandpa: a long beat'),
    'him': (1.00, 'held', 'HIM'),
    'white_coat': (0.60, 'beat', 'his head'),
    'tape_head': (0.60, 'beat', 'the gap'),
    'eyes': (0.85, 'paragraph', 'the clipboard'),
    'clipboard': (0.40, 'staccato', 'clicking'),
    'clicking': (0.85, 'paragraph', 'the reach'),
    'held_out': (1.20, 'held', 'held dread before "My ticket said: Milo."'),
    'ticket_milo': (1.00, 'held', 'the name sinks in'),
    'kindest': (0.85, 'held', 'his line'),
    'take_a_seat': (0.60, 'dialogue', '"Take a seat." ... "It can wait.": slow, too calm'),
    'take_a_seat_wait': (1.40, 'before rule', 'rule card 7'),
    # rule 7
    'rule7_text': (1.00, 'after rule', 'the rule card holds, then the scene'),
    'pulse': (0.85, 'held', 'his fingers'),
    'began_count': (1.00, 'count', 'spaced like slow counting'),
    'count1': (1.00, 'count', '"One..." then the music slows'),
    'music_slowed': (1.10, 'count', 'slowing'),
    'count2': (1.20, 'count', '"Two..." then the clock slows'),
    'clock_slowed': (0.90, 'paragraph', 'what he does'),
    'what_he_does': (0.40, 'staccato', 'He doesn\'t hurt you. He just counts.'),
    'doesnt_hurt': (0.40, 'staccato', 'fragments'),
    'just_counts': (0.45, 'sentence', 'running'),
    'every_number': (0.45, 'sentence', 'running'),
    'longer_chair': (1.20, 'count', 'slowing before "Three..."'),
    'count3': (1.30, 'count', 'the slowest count, then the turn'),
    'one_thing': (0.90, 'held', 'held before "I asked."'),
    'ask': (0.90, 'held', 'held before the question'),
    'what_did_you_find': (1.00, 'held', 'he stops counting'),
    'stopped_counting': (0.85, 'paragraph', 'the questions tumble out'),
    'questions': (0.35, 'questions', 'the questions come fast'),
    'q_do': (0.35, 'questions', 'fast'),
    'q_long': (0.40, 'questions', 'fast'),
    'q_who': (0.90, 'paragraph', 'the tape loosens'),
    'strip1': (0.40, 'staccato', 'One strip. Then another.'),
    'strip2': (0.45, 'sentence', 'running'),
    'flinched': (0.90, 'paragraph', 'under the tape'),
    'no_doctor': (1.00, 'held', 'the faces'),
    'faces': (0.50, 'list', 'the faces, one after another'),
    'face_man': (0.45, 'list', 'the faces'),
    'face_girl': (0.45, 'list', 'the faces'),
    'face_grandma': (0.60, 'list', 'held before "Then... me."'),
    'face_me': (0.90, 'held', 'my own face'),
    'every_face': (0.25, 'split', 'the quote follows its "who ever said,"'),
    'probably_nothing': (0.45, 'sentence', 'running'),
    'made_of_them': (0.90, 'paragraph', 'what he is'),
    'not_a_doctor': (0.40, 'staccato', '"He had never been one."'),
    'never_been': (0.60, 'beat', 'what he is'),
    'no_real_doctor': (1.20, 'held', 'held dread before his "It can wait."'),
    'later_wait': (1.20, 'held', 'his line hangs'),
    'pulled_free': (0.85, 'paragraph', 'the card'),
    'signature': (1.30, 'held', 'held dread before "Doctor Later."'),
    'doctor_later': (1.20, 'held', 'the name sinks in'),
    'never_wrote': (0.45, 'beat', 'She wrote them down. Over the phone. While she was on hold.'),
    'wrote_down': (0.40, 'staccato', 'fragments'),
    'over_phone': (0.40, 'staccato', 'fragments'),
    'on_hold': (1.00, 'section', 'the rescue'),
    # the rescue
    'burned_paper': (0.85, 'paragraph', 'the front door'),
    'front_door': (0.60, 'beat', 'she is already running'),
    'running_up': (0.90, 'paragraph', 'the car'),
    'reached_wrist': (0.40, 'dialogue', 'her line'),
    'pulse_real': (0.85, 'held', 'rule seven recalled'),
    'rule_seven_recall': (0.40, 'staccato', '"I almost pulled him away."'),
    'almost': (0.60, 'beat', 'the choice'),
    'gave_wrist': (0.90, 'held', 'she counts for real'),
    'one_forty': (0.18, 'split', '"One-forty," / "she said."'),
    'fast_h': (0.35, 'dialogue', 'her calm, quick verdict'),
    'thats_okay': (0.35, 'dialogue', 'her verdict'),
    'fighting': (0.35, 'dialogue', 'her verdict'),
    'going': (0.90, 'paragraph', 'the drive'),
    'treatable': (0.85, 'paragraph', 'her line'),
    'ask_me': (0.18, 'split', '"Ask me anything," / "she said."'),
    'questions_good': (0.35, 'dialogue', 'her lines'),
    'questions_win': (0.85, 'paragraph', 'I ask'),
    'so_i_asked': (0.40, 'staccato', 'fragments'),
    'every_question': (0.40, 'staccato', 'fragments'),
    'answered': (0.90, 'paragraph', 'the mirror'),
    'mirror': (1.00, 'held', 'held before "He was in the back seat."'),
    'back_seat': (0.45, 'sentence', 'running'),
    'folded_beside': (0.45, 'sentence', 'running'),
    'clicking_car': (0.90, 'held', 'his line'),
    'car_wait': (0.18, 'split', '"It can wait," / "he said."'),
    'h_mirror': (0.45, 'beat', '"She saw him."'),
    'saw_him': (0.45, 'beat', 'not surprised'),
    'not_surprised': (0.85, 'paragraph', 'every doctor has seen him'),
    'every_waiting_room': (0.40, 'staccato', 'In every waiting room. In every chair.'),
    'every_chair_doc': (0.45, 'sentence', 'running'),
    'out_of_chairs': (0.90, 'paragraph', 'her line'),
    'not_tonight': (0.18, 'split', '"Not tonight," / "she said."'),
    'not_my_shift': (0.60, 'beat', 'she drives faster'),
    'faster': (1.00, 'section', 'the ER'),
    'people_everywhere': (0.40, 'staccato', 'Bright lights. Fluids. Insulin.'),
    'bright_lights': (0.35, 'staccato', 'the ER montage'),
    'fluids': (0.35, 'staccato', 'the ER montage'),
    'insulin': (0.40, 'staccato', 'the ER montage'),
    'cheering': (0.90, 'held', 'held before "Nobody told us to wait."'),
    'nobody_wait': (1.00, 'paragraph', 'the waiting room'),
    'nurse': (0.25, 'split', 'the nurse\'s line follows her "and said,"'),
    'sir': (0.35, 'dialogue', 'her lines'),
    'come_with_me': (0.90, 'paragraph', 'the empty chair'),
    'empty_chair': (0.50, 'beat', 'still rocking'),
    'still_rocking': (0.45, 'beat', 'gotten up and left'),
    'gotten_up': (1.30, 'section', 'the story turns: Milo lived'),
    # after
    'milo_lived': (0.90, 'held', 'let it land'),
    'marathons': (0.90, 'paragraph', 'sunrise, Grandma'),
    'ticket_hand': (0.60, 'held', 'held before "It said: Ruth."'),
    'ticket_ruth': (1.00, 'held', 'the name sinks in'),
    'not_a_word': (0.45, 'beat', '"Rule three."'),
    'rule_three_recall': (0.85, 'paragraph', 'Mom dials'),
    'dialed': (0.45, 'dialogue', 'Mom\'s line'),
    'mom_dont_wait': (0.18, 'split', '"You don\'t wait," / "she said."'),
    'you_call': (0.90, 'paragraph', 'Grandma\'s fine'),
    'cardiologist': (0.60, 'beat', 'the card'),
    'burned': (1.40, 'section', 'the twist'),
    # the twist
    'twist': (1.00, 'held', 'held before "Not as a patient."'),
    'not_patient': (1.00, 'held', 'the twist lands'),
    'terrible': (0.40, 'staccato', 'Rough. Out of breath. Probably a little scary.'),
    'rough_me': (0.35, 'staccato', 'fragments (an echo of the 3 AM call)'),
    'breath_me': (0.40, 'staccato', 'fragments'),
    'scary_me': (0.85, 'paragraph', 'calling you'),
    'calling_you': (0.90, 'paragraph', 'the hook line, flipped'),
    'if_your_doctor': (0.70, 'ellipsis', 'its own "..." before "Ask what we found."'),
    'ask_what_we_found': (0.60, 'beat', '"Please."'),
    'please': (0.60, 'beat', 'why'),
    'cant_wait_we': (0.90, 'paragraph', 'the hold-music warning'),
    'call_back': (0.40, 'staccato', '"We\'ll pick up."'),
    'pick_up': (0.90, 'paragraph', 'the last chair'),
    'pen_click_now': (0.60, 'beat', 'the hall'),
    'last_chair': (1.20, 'held', 'he\'s waiting'),
    'very_patient': (1.30, 'held', 'held dread before "So are we."'),
    'so_are_we': (2.80, 'before outro', 'the story ends: about 2.5-3 s of silence before "Okay. Breathe."'),
    # outro
    'outro': (0.45, 'beat', '"Okay." "Breathe."'),
    'breathe': (0.50, 'beat', 'calming'),
    'light_on': (0.85, 'paragraph', 'none of this happened'),
    'none_happened': (0.45, 'list', 'the list of things that aren\'t real'),
    'no_later': (0.35, 'list', 'the list'),
    'no_room': (0.45, 'sentence', 'who made it up'),
    'made_up': (0.90, 'paragraph', 'but he is a little bit real'),
    'voice_in_head': (0.25, 'split', 'the voice in your head follows its "that says,"'),
    'w_nothing': (0.35, 'list', 'his three phrases'),
    'w_bother': (0.35, 'list', 'his three phrases'),
    'w_wait': (0.60, 'beat', 'back to the narrator'),
    'sounds_kind': (0.35, 'staccato', 'He sounds kind. He sounds sensible.'),
    'sensible': (0.40, 'staccato', 'fragments'),
    'very_very_patient': (0.85, 'paragraph', 'how to beat him'),
    'beat_him': (0.40, 'staccato', '"For real."'),
    'for_real': (0.85, 'paragraph', 'the advice'),
    'kids': (0.40, 'staccato', 'Kids... Grown-ups...'),
    'grownups': (0.85, 'paragraph', 'the warning signs'),
    'signs': (0.40, 'list', '"Tell a doctor."'),
    'signs_doctor': (0.60, 'beat', 'the emergency signs'),
    'emergency': (0.40, 'list', '"Don\'t wait."'),
    'emergency_dont_wait': (0.40, 'staccato', '"Call your emergency number."'),
    'emergency_call': (0.85, 'paragraph', 'ask questions'),
    'ask_questions': (0.40, 'staccato', '"All of them."'),
    'all_of_them': (0.45, 'sentence', 'running'),
    'hundred': (0.85, 'paragraph', 'the strange call'),
    'real_number': (0.85, 'paragraph', 'the night shift'),
    'not_monster': (0.40, 'staccato', 'the two "They\'re" lines'),
    'out_of_his_chair': (0.90, 'paragraph', 'back to the comments'),
    'comment_back': (0.40, 'staccato', '"Now." "Go back..."'),
    'go_back': (0.60, 'beat', 'the two answers'),
    'said_ask': (0.45, 'beat', '"Thank you."'),
    'thank_you': (0.85, 'paragraph', 'the other answer'),
    'waiting_talking': (0.40, 'sentence', 'running'),
    'convincing': (0.60, 'beat', 'the edit'),
    'edit_ask': (0.40, 'staccato', '"Change it to \'ask.\'"'),
    'only_time': (0.85, 'paragraph', 'the names'),
    'first_name': (0.45, 'sentence', 'running'),
    'waiting_list': (0.90, 'paragraph', 'call someone'),
    'like': (0.85, 'paragraph', 'subscribe'),
    'subscribe': (0.40, 'sentence', 'the reason'),
    'never_hold': (0.40, 'sentence', 'running'),
    'next_story': (0.90, 'paragraph', 'next time'),
    'next': (1.00, 'paragraph', 'the goodbye (the take ran it into "Sleep well." with 0.15 s)'),
    'sleep_well': (0.55, 'beat', 'the last line'),
    'pick_up_end': (0.50, 'beat', 'the last sentence'),
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
                'held dread before the reveal lines ("Still waiting.", "Waiting.", "Grandpa.", "My ticket said: Milo.", '
                '"It can wait.", "Doctor Later.", "Not as a patient.", "So are we.") 1.0-1.8 s; the counts "One... '
                'Two... Three..." spaced like slow counting (1.0-1.3 s, slowing); the phone rings and the knock get '
                'about 1 s where they sit; about 1 s before the comment prompt and 2.5-3 s before the outro ("Okay. '
                'Breathe."). Never under 0.15 s between sentences (a line split for its speaker, "I\'ll call you the '
                'second the results come in," / "she said.", sits at 0.18 s; a speaker cut off mid-line at 0.25-0.30 s), '
                'never over 2 s except before the outro.\n\n')
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


def assemble(T, spans, gaps, lead=0.30, tail=0.60, voice=None):
    """Lay the lines end to end with the map's gaps. voice(y, line) -> (y', stats or None) gives a character line its
    voice (tools/vo_voices.py); a voice may lengthen its line (the Waiting Man speaks slower), and the layout makes room:
    the line slot is the voiced line's length in both files, so narration_clean.wav (the edit without voices) and
    narration_en.wav keep identical line starts (the clean file holds the dry line and silence to the slot's end).
    Returns (clean signal, voiced signal, edit list, line output times, narrator median level, voice report rows)."""
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
    dry, wet, vrep = [], [], []
    for i, (buf, pcs, placed) in enumerate(sigs):
        y = buf * 10 ** (gains[i] / 20)
        yv, st = voice(y, LINES[i]) if voice else (y, None)
        dry.append(y); wet.append(yv)
        if st: vrep.append(dict(st, i=i))
    total = int((lead + sum(max(len(a_), len(b_)) / SR for a_, b_ in zip(dry, wet))
                 + sum(gaps[i][0] for i in range(len(LINES) - 1)) + tail) * SR) + 10
    out = np.zeros(total); out_v = np.zeros(total)
    t = lead
    edl = []
    for i, (buf, pcs, placed) in enumerate(sigs):
        a = int(round(t * SR))
        n_slot = max(len(dry[i]), len(wet[i]))
        out[a:a + len(dry[i])] += dry[i]
        out_v[a:a + len(wet[i])] += wet[i]
        t0 = a / SR; t1 = (a + n_slot) / SR
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
        e = {'i': i, 'who': LINES[i]['who'], 'tag': LINES[i]['tag'], 'fx': LINES[i]['fx'], 'en': LINES[i]['en'],
             'out': [round(t0, 4), round(t1, 4)], 'src_span': [round(spans[i]['span'][0], 4), round(spans[i]['span'][1], 4)],
             'gain_db': gains[i], 'level_db': round(float(lv[i]), 2), 'pieces': items,
             'removed_inside': spans[i]['removed'], 'gap_after': g[0], 'gap_kind': g[1], 'gap_why': g[2]}
        if len(wet[i]) != len(dry[i]):                             # a voice that changed the line's length
            e['out_clean'] = [round(t0, 4), round(t0 + len(dry[i]) / SR, 4)]
            e['stretch'] = round(len(wet[i]) / max(1, len(dry[i])), 3)
        edl.append(e)
        lines_out.append((t0, t1))
        t = t1 + (gaps[i][0] if i in gaps else 0)
    end = int(round((lines_out[-1][1] + tail) * SR))
    return out[:end], out_v[:end], edl, lines_out, med, vrep


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
        if os.environ.get('VO_NO_VOICES'): raise ImportError        # a quick clean-only build (narration_en = clean)
        from vo_voices import voice_line                               # noqa
    except ImportError:
        log('character voices off: narration_en.wav = narration_clean.wav')
        voice_line = None
    T = Take()
    log(f'clip repair: {T.clip}; {len(T.isl)} islands; lines without words: {T.missing}')
    spans, between, _ = line_spans(T)
    gaps = read_pacing()
    y, yv, edl, lines_out, med, vrep = assemble(T, spans, gaps, voice=voice_line)
    log(f'assembled: {len(y) / SR:.2f} s, narrator median speech level {med:.1f} dB, {len(vrep)} character lines voiced')
    clean, st = finish(y)                                           # the narrator's cleanup runs on both files: the
    voiced, _ = finish(yv)                                          # character lines are the narrator's own take too
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
               'fixes': {k: str(v) for k, v in FIXES.items()}, 'splits': SPLITS, 'internal_pauses': INTERNAL,
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
        # every line against the recogniser (tools/vo_asrcheck.py): needs align.py's ASR of THIS narration_en.wav
        cache = os.path.join(W, 'align', 'asr_cache.json')
        if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(OUT):
            from vo_asrcheck import main as asr_main                  # noqa
            if asr_main(): raise SystemExit('vo_asrcheck: a line does not read as its script (see above)')
        else:
            log('asrcheck skipped: run tools/align.py --write-pauses on this build, then vo_edit.py check again')
    else: raise SystemExit(__doc__)
