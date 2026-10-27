# Can every line be understood in the final mix, and does the voice sit above the score?
# usage: python3 -I ep_check.py <scratch_dir> <timeline.json> <mix_dir>
import sys, os, json, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts
S, TL, A = sys.argv[1:4]
tts.init(S)
T = json.load(open(TL)); E0 = T['ep_start']
mix, sr = sf.read(f'{A}/mix.wav', dtype='float32'); mono = mix.mean(1)
# balance is judged in the speech band, where masking happens; rumble under a line does not hide it
from scipy.signal import butter, sosfilt
band = butter(4, [300, 4000], 'bandpass', fs=12000, output='sos')
stems = {k: sosfilt(band, sf.read(f'{A}/stem_{k}.wav', dtype='float32')[0]) for k in ('voice', 'score', 'sfx')}
bad, low = [], []
for L in T['voice']['lines']:
    if L['start'] < E0: continue
    a, b = L['start'] - 0.05, L['start'] + L['dur'] + 0.1
    seg = mono[int(a * sr):int(b * sr)]
    y = librosa.resample(seg, orig_sr=sr, target_sr=tts.SR)
    exp, heard = tts.asr(y)
    ok = tts.align(tts.asr.raw, L['text'], len(y) / tts.SR) is not None
    i0, i1 = int((L['start'] - E0) * 12000), int((L['start'] + L['dur'] - E0) * 12000)
    # compare only where the voice is actually speaking (50 ms frames within 20 dB of the line's loudest)
    fr = lambda x: np.sqrt(np.mean(x[:len(x) // 600 * 600].reshape(-1, 600) ** 2, 1)) + 1e-9
    ev = fr(stems['voice'][i0:i1]); on = ev > ev.max() * 0.1
    v, s, f = (20 * np.log10(np.sqrt(np.mean(fr(stems[k][i0:i1])[on] ** 2))) for k in ('voice', 'score', 'sfx'))
    if not ok: bad.append((L['id'], L['text'], heard))
    if v - max(s, f) < 8: low.append((L['id'], round(v - s, 1), round(v - f, 1), L['text'][:50]))
print('lines', sum(1 for L in T['voice']['lines'] if L['start'] >= E0), '| not understood:', len(bad), '| voice < 8 dB above music or sfx:', len(low))
for x in bad: print('  ASR', x)
for x in low: print('  LOW', x)
