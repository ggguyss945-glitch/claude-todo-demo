# Synthesize narration + PA line, process like a close, warm studio mic, and get word timings.
# usage: python3 -I voice.py <scratch_dir> <out_dir>
import sys, os, json, re, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kokoro_onnx import Kokoro
import sherpa_onnx
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, LowShelfFilter, HighShelfFilter, PeakFilter,
                        Compressor, Limiter, Reverb, Gain, Distortion)
from script_test import LINES, PA_LINE, NARRATOR, NARRATION_START

S, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SR = 48000
k = Kokoro(f'{S}/tts/kokoro-v1.0.onnx', f'{S}/tts/voices-v1.0.bin')
narr_style = sum(w * k.get_voice_style(v) for v, w in NARRATOR.items())

def tts(text, style, speed):
    a, sr = k.create(text, voice=style, speed=speed, lang='en-us')
    a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
    # trim leading/trailing silence but keep 40 ms of breath room
    idx = np.where(np.abs(a) > 0.008)[0]
    a = a[max(0, idx[0] - int(0.04 * SR)): idx[-1] + int(0.12 * SR)]
    return a

def hp(x, f, order=4):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(order, f / (SR / 2), 'high', output='sos'), x)

# "studio mic" chain: proximity warmth, cut boxiness, presence, air, gentle compression
mic = Pedalboard([HighpassFilter(70), LowShelfFilter(cutoff_frequency_hz=160, gain_db=2.0), PeakFilter(330, -2.5, 1.0),
                  PeakFilter(3200, 2.5, 0.8), HighShelfFilter(cutoff_frequency_hz=9000, gain_db=2.0),
                  Compressor(threshold_db=-22, ratio=3.0, attack_ms=4, release_ms=90), Gain(3)])
def deess(x):
    # dynamic cut of 5.5-9 kHz when it dominates
    from scipy.signal import butter, sosfiltfilt
    band = sosfiltfilt(butter(2, [5500 / (SR / 2), 9000 / (SR / 2)], 'band', output='sos'), x)
    env = np.sqrt(np.convolve(band ** 2, np.ones(240) / 240, 'same')) + 1e-9
    full = np.sqrt(np.convolve(x ** 2, np.ones(240) / 240, 'same')) + 1e-9
    red = np.clip((env / full - 0.35) * 1.6, 0, 0.6)
    return x - band * red
def exciter(x):
    # add gentle air above the 12 kHz ceiling of the model
    h = hp(x, 3500); h = np.tanh(4 * h) / 4
    return x + 0.12 * hp(h, 11000)

def process_narration(a):
    a = mic(a.astype(np.float32), SR)
    a = deess(a); a = exciter(a)
    room = Pedalboard([Reverb(room_size=0.12, damping=0.7, wet_level=0.045, dry_level=1.0, width=0.2)])
    return room(a.astype(np.float32), SR)

pa_chain = Pedalboard([HighpassFilter(450), LowpassFilter(3600), PeakFilter(1800, 5, 1.2), Distortion(drive_db=9),
                       Compressor(threshold_db=-18, ratio=6), Reverb(room_size=0.85, damping=0.4, wet_level=0.35, dry_level=0.75, width=0.6), Gain(-4)])

M = S + '/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M + '/encoder.int8.onnx', decoder=M + '/decoder.int8.onnx',
        joiner=M + '/joiner.int8.onnx', tokens=M + '/tokens.txt', num_threads=4, model_type='nemo_transducer')

SMALL = {0: 1, 1: 1}
def num_words(w):
    """How many spoken script words an ASR token stands for (digits only)."""
    w = w.strip('.,!?')
    if not re.search(r'\d', w): return 1
    if re.fullmatch(r'\d{1,2}[.:]\d{2}', w):  # clock time 2.14 -> two fourteen; 2.31 -> two thirty-one (hyphenated = 1)
        return 2
    n = int(re.sub(r'\D', '', w))
    if n >= 1000 and n % 1000 == 0: return 2   # nine thousand
    return 1                                     # 12 -> twelve, 38 -> thirty-eight

def word_times(a, text):
    y = librosa.resample(a.astype(np.float32), orig_sr=SR, target_sr=16000)
    st = rec.create_stream(); st.accept_waveform(16000, y); rec.decode_stream(st)
    r = st.result; words = []; cur = None
    for tok, t in zip(r.tokens, r.timestamps):
        if tok.startswith(' ') or cur is None:
            if cur: words.append(cur)
            cur = [tok.strip(), t]
        else: cur[0] += tok
    if cur: words.append(cur)
    script_words = re.findall(r"[A-Za-z0-9'\-]+", text)
    asr = [w for w in words if re.search(r'[A-Za-z0-9]', w[0])]
    dur = len(a) / SR
    # expand ASR numbers ("2.14", "9,000", "12") into the number of script words they cover
    exp = []
    for i, (w, t0) in enumerate(asr):
        t1 = asr[i + 1][1] if i + 1 < len(asr) else dur - 0.1
        n = num_words(w)
        for j in range(n): exp.append(t0 + (t1 - t0) * j / n)
    if len(exp) == len(script_words):
        times = exp
    elif len(asr) == len(script_words):
        times = [w[1] for w in asr]
    else:  # fall back to character-proportional timing
        lens = np.array([len(w) + 1 for w in script_words], float); times = list(np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * dur * 0.92 + 0.05)
        print('  timing fallback for', text, '| asr:', ' '.join(w[0] for w in asr))
    return [{'w': w, 't': float(t)} for w, t in zip(script_words, times)], r.text

out = {'sr': SR, 'lines': []}
t = NARRATION_START
for L in LINES:
    raw = tts(L['text'], narr_style, L['speed'])
    a = process_narration(raw) * 10 ** (L['level'] / 20)
    words, heard = word_times(raw, L['text'])
    sf.write(f'{OUT}/{L["id"]}.wav', a.astype(np.float32), SR)
    out['lines'].append({**L, 'start': round(t, 3), 'dur': round(len(a) / SR, 3), 'words': words, 'asr': heard})
    print(f'{L["id"]:4s} {t:6.2f}s +{len(a)/SR:4.2f}s  {heard}')
    t += len(a) / SR + L['gap']
out['narration_end'] = round(t, 3)

pa = tts(PA_LINE['text'], k.get_voice_style(PA_LINE['voice']), PA_LINE['speed'])
pa_words, _ = word_times(pa, PA_LINE['text'])
pa_p = pa_chain(pa.astype(np.float32), SR)
sf.write(f'{OUT}/PA.wav', pa_p, SR)
out['pa'] = {'dur': round(len(pa_p) / SR, 3), 'words': pa_words, 'text': PA_LINE['text']}
json.dump(out, open(f'{OUT}/voice.json', 'w'), indent=1)
print('narration ends at', round(t, 2), 's | PA dur', out['pa']['dur'])
