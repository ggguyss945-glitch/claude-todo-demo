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
stems = {k: sf.read(f'{A}/stem_{k}.wav', dtype='float32')[0] for k in ('voice', 'score', 'sfx')}
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
bad, low = [], []
for L in T['voice']['lines']:
    if L['start'] < E0: continue
    a, b = L['start'] - 0.05, L['start'] + L['dur'] + 0.1
    seg = mono[int(a * sr):int(b * sr)]
    y = librosa.resample(seg, orig_sr=sr, target_sr=tts.SR)
    exp, heard = tts.asr(y)
    ok = tts.align(tts.asr.raw, L['text'], len(y) / tts.SR) is not None
    i0, i1 = int((L['start'] - E0) * 12000), int((L['start'] + L['dur'] - E0) * 12000)
    v, s, f = (rms(stems[k][i0:i1]) for k in ('voice', 'score', 'sfx'))
    if not ok: bad.append((L['id'], L['text'], heard))
    if v - max(s, f) < 8: low.append((L['id'], round(v - s, 1), round(v - f, 1), L['text'][:50]))
print('lines', sum(1 for L in T['voice']['lines'] if L['start'] >= E0), '| not understood:', len(bad), '| voice < 8 dB above music or sfx:', len(low))
for x in bad: print('  ASR', x)
for x in low: print('  LOW', x)
