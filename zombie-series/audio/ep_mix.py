# Episode soundtrack: the approved cold-open mix, then voice + score cues + ambience + SFX for the rest,
# ducked under the voice and mastered to the same loudness, joined into one file at -14 LUFS.
# usage: python3 -I ep_mix.py <scratch_dir> <timeline.json> <voice_dir> <cold_mix.wav|-> <out_dir>
#   '-' when the episode has no reused cold open: the whole timeline is mixed here
import sys, os, json, re, subprocess, numpy as np, soundfile as sf
from scipy.ndimage import minimum_filter1d, uniform_filter1d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pedalboard import Pedalboard, Reverb, LowpassFilter, HighpassFilter, Compressor, Gain, Distortion, PeakFilter
import sfx as X
import ep_sfx as FX
from ep_music import render_cue, GAIN

S, TL, VD, COLD, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)
SR = X.SR; FX.SF2 = f'{S}/sf/GeneralUser-GS.sf2'
T = json.load(open(TL)); E0 = T['ep_start']; DUR = T['dur']; N = int((DUR - E0) * SR) + SR
ITEMS = T['items']
db = lambda d: 10 ** (d / 20)
def fx(x, *pl): return Pedalboard(list(pl))(np.asarray(x, np.float32), SR)
class Track:
    def __init__(self): self.x = np.zeros((N, 2), np.float32)
    def add(self, sig, t, gain_db=0.0):
        i = int(round((t - E0) * SR)); sig = np.asarray(sig, np.float32)
        if sig.ndim == 1: sig = X.st(sig)
        if i < 0: sig = sig[-i:]; i = 0
        m = min(len(sig), N - i)
        if m > 0: self.x[i:i + m] += sig[:m] * db(gain_db)
voice, score, amb, sfxT, loopT = Track(), Track(), Track(), Track(), Track()
# sustained effects (alarms, breathing, the store jingle) duck under the voice like the beds; one-shot hits do not
CONT = {'alarm_far', 'alarm_near', 'decoy_alarm', 'heartbeat_run', 'breath_run', 'crowd_steps_far', 'phone_ring', 'crowd_surge', 'run_steps',
        'drone_buzz', 'drone_song', 'water_pour'}
# cues that are meant to hit; every other cue eases in so a change of music never jumps out
STINGS = {'rule', 'twist', 'sting_mystery', 'end', 'chaos', 'reveal'}

# ---------- voice ----------
store_room = Pedalboard([Reverb(room_size=0.9, damping=0.45, wet_level=0.45, dry_level=0.7, width=1.0)])
for L in T['voice']['lines']:
    if L['start'] < E0 - 0.01: continue
    a, _ = sf.read(f"{VD}/{L['id']}.wav", dtype='float32')
    if L['who'] == 'PA': voice.add(store_room(a, SR), L['start'], -2)
    else: voice.add(a, L['start'], {'N': 0, 'NORA': 1.5}.get(L['who'], -1))   # Nora is hushed, so she sits a little higher
    if L.get('echo'):   # the same voice, live, from the roof behind you: late, far, wide
        c, _ = sf.read(f"{VD}/{L['id']}_clean.wav", dtype='float32')
        far = fx(c, HighpassFilter(250), LowpassFilter(2200), Reverb(room_size=0.95, damping=0.6, wet_level=0.7, dry_level=0.35, width=1.0))
        voice.add(X.st(far.mean(1) if far.ndim == 2 else far, 0.55, 0.4), L['start'] + 0.12 + 0.3, -13)

# ---------- score ----------
hall = Pedalboard([Reverb(room_size=0.78, damping=0.45, wet_level=0.28, dry_level=0.85, width=1.0)])
pa_music = Pedalboard([HighpassFilter(350), LowpassFilter(4200), PeakFilter(1800, 4, 1.0), Distortion(drive_db=6), Reverb(room_size=0.92, damping=0.4, wet_level=0.5, dry_level=0.65, width=1.0)])
cues = sorted(T['music'], key=lambda c: c['t'])
for i, c in enumerate(cues):
    if c['cue'] == 'stop': continue
    t0 = c['t']; nxt = cues[i + 1] if i + 1 < len(cues) else None; t1 = nxt['t'] if nxt else DUR
    D = t1 - t0; fade = (nxt['p'].get('fade', 0.8) if nxt and nxt['cue'] == 'stop' else 2.0)
    y = render_cue(FX.SF2, c['cue'], D, c['p'])
    y = pa_music(y, SR) if c['cue'] == 'jingle' else hall(y, SR)
    n0, n1 = int((D - min(fade, D) * 0.3) * SR), int((D + fade * 0.7) * SR)
    env = np.ones(len(y), np.float32)
    if c['cue'] not in STINGS: k = int(0.45 * SR); env[:k] = np.linspace(0, 1, k) ** 1.5
    if n0 < len(env): env[n0:min(n1, len(env))] = np.linspace(1, 0, min(n1, len(env)) - n0); env[min(n1, len(env)):] = 0
    y = y * env[:, None]
    if c['cue'] == 'jingle': loopT.add(y, t0, -3)           # it plays from the store speakers, not the score
    else: score.add(y, t0, GAIN.get(c['cue'], 0))
    print(f"cue {c['cue']:14s} {t0:7.2f}-{t1:7.2f} ({D:5.1f}s)", flush=True)

# ---------- ambience beds ----------
beds = sorted(T['amb'], key=lambda b: b['t'])
rg = np.random.default_rng(3)
for i, b in enumerate(beds):
    t0 = b['t']; t1 = beds[i + 1]['t'] if i + 1 < len(beds) else DUR
    d = t1 - t0 + 0.8
    amb.add(X.fade(FX.bed(b['bed'], d), 0.6, 0.8), t0, FX.BED_LEVEL.get(b['bed'], -24))
    for k in range(int((t1 - t0) / 60 * FX.GROANS.get(b['bed'], 0))):
        g = fx(X.groan(1.6, rg.uniform(65, 100), 1.0, int(rg.integers(1, 999)), rg.choice(['uh', 'oh', 'eh'])), LowpassFilter(900), Reverb(room_size=0.85, wet_level=0.6, dry_level=0.4))
        amb.add(g, rg.uniform(t0 + 1, max(t0 + 1.5, t1 - 2)), -29)

# ---------- SFX ----------
m1, m2 = (ITEMS['M1'][0], ITEMS['M2'][1] - 0.3) if 'M2' in ITEMS else (0, 0)
for e in T['sfx']:
    name, p, t = e['name'], e['p'] or {}, e['t']
    f = FX.EFFECTS.get(name)
    if f is None: print('  WARNING: no effect', name); continue
    dur = None
    if 'until' in p: dur = ITEMS[p['until']][0] + p.get('off', 0) - t
    elif 'dur' in p: dur = p['dur']
    if name == 'decoy_alarm': dur = m1 + (p.get('k', 1) - 1) / 5 * (m2 - m1) - t
    if dur is not None and dur <= 0.05: print('  WARNING: no time for', name, e['item']); continue
    y = f(p, dur) if dur is not None else f(p)
    if name == 'drone_song':
        # the store jingle out of a tiny speaker under the drone: thin, a little crunchy, getting farther away
        j = render_cue(FX.SF2, 'jingle', dur, {})[:int(dur * SR)]
        j = fx(j, HighpassFilter(650), LowpassFilter(3800), PeakFilter(1500, 5, 1.0), Distortion(drive_db=5))
        tt = np.arange(len(j)) / SR; away = np.clip(tt / max(8.0, dur * 0.6), 0, 1)
        j = j * (1 - 0.75 * away)[:, None]
        y = fx(j, Reverb(room_size=0.95, damping=0.55, wet_level=0.5, dry_level=0.6, width=1.0))
    if dur is not None: y = X.fade(y[:int(dur * SR)], 0.01, 0.03 if name in ('phone_ring', 'alarm_far', 'alarm_near', 'decoy_alarm') else 0.3)
    (loopT if name in CONT else sfxT).add(y, t, p.get('level', FX.LEVEL.get(name, -12)))

# ---------- ducking under any voice: score -9 dB, sustained effects -12 dB, beds -6 dB ----------
# voice activity per 10 ms frame, then a smooth gain: duck in over ~0.15 s, recover over ~0.8 s, so the
# music swells back gently between lines instead of pumping
hop = SR // 100; v = np.abs(voice.x).mean(1); nf = len(v) // hop
fr = np.sqrt((v[:nf * hop].reshape(nf, hop) ** 2).mean(1))
on = (fr > 0.004).astype(np.float32)
on = np.maximum(on, np.convolve(on, np.ones(12), 'same') > 0)   # bridge the small gaps between words
a_up, a_dn = 1 - np.exp(-1 / 15), 1 - np.exp(-1 / 80)
sm = np.zeros(nf, np.float32); cur = 0.0
for i in range(nf):
    cur += (on[i] - cur) * (a_up if on[i] > cur else a_dn); sm[i] = cur
act = np.interp(np.arange(N), np.arange(nf) * hop + hop / 2, sm).astype(np.float32)
for tr, d in ((score, -11), (loopT, -13), (amb, -9)): tr.x *= (1 - act * (1 - db(d)))[:, None]

def limit(x, ceil_db=-1.0, ms=30):
    # lookahead peak limiter with no makeup gain: the gain curve is the minimum over +-ms/2, then a moving
    # average of the same span, so it is never above what each peak needs and moves smoothly into and out of it
    n = max(3, int(ms / 1000 * SR)) | 1
    g = np.minimum(1.0, db(ceil_db) / np.maximum(np.abs(x).max(1), 1e-9)).astype(np.float32)
    g = uniform_filter1d(minimum_filter1d(g, 2 * n + 1), n)
    return (x * g[:, None]).astype(np.float32)

# ---------- master the episode part, then join it to the cold open ----------
mix = voice.x * db(-1) + score.x * db(-6.5) + amb.x + sfxT.x + loopT.x
mix = limit(Pedalboard([Compressor(threshold_db=-16, ratio=2.0, attack_ms=12, release_ms=150)])(mix.astype(np.float32), SR), -2.0)
def lufs(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
sf.write(f'{OUT}/ep_part.wav', mix, SR, subtype='PCM_24')
if COLD == '-':
    full = mix[:int(DUR * SR)]; Lc = float('nan')
else:
    cold, _ = sf.read(COLD, dtype='float32'); Lc = lufs(COLD)
    g = Lc - lufs(f'{OUT}/ep_part.wav')
    part = limit(mix * db(g))
    gap = np.zeros((int(round(E0 * SR)) - len(cold), 2), np.float32) if E0 * SR > len(cold) else np.zeros((0, 2), np.float32)
    full = np.concatenate([cold, gap, part])[:int(DUR * SR)]
sf.write(f'{OUT}/premaster.wav', full, SR, subtype='PCM_24')
g = -14.0 - lufs(f'{OUT}/premaster.wav')
for it in range(5):
    final = limit(full * db(g))
    sf.write(f'{OUT}/mix.wav', final, SR, subtype='PCM_24')
    L = lufs(f'{OUT}/mix.wav'); print('pass %d: gain %.2f dB -> %.2f LUFS, peak %.2f dBFS' % (it, g, L, 20 * np.log10(np.abs(final).max())))
    if abs(L + 14) < 0.1: break
    g += -14.0 - L
# per-shot balance for a quick look
for nm, tr in (('voice', voice.x), ('score', score.x * db(-6.5)), ('sfx', sfxT.x + loopT.x + amb.x)):
    sf.write(f'{OUT}/stem_{nm}.wav', tr[::4].astype(np.float32), SR // 4, subtype='PCM_16')
print('cold open', round(Lc, 2), 'LUFS | episode', round(DUR, 1), 's')
