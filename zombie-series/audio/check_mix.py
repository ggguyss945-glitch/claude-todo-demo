# per-shot loudness of stems: is the score audible where it should be, is the voice on top
import sys, json, numpy as np, soundfile as sf
A, TL = sys.argv[1], sys.argv[2]
T = json.load(open(TL)); st = {n: sf.read(f'{A}/stem_{n}.wav')[0] for n in ('voice', 'score', 'sfx')}
mix = sf.read(f'{A}/mix.wav')[0]; SR = 48000
def rms(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
print(f"{'shot':15s} {'voice':>7s} {'score':>7s} {'sfx':>7s} {'mix':>7s}  (dB RMS, premaster stems)")
for s in T['shots']:
    a, b = int(s['start'] * SR), int(s['end'] * SR)
    print(f"{s['name']:15s} " + ' '.join(f"{rms(st[n][a:b]):7.1f}" for n in ('voice', 'score', 'sfx')) + f" {rms(mix[a:b]):7.1f}")
