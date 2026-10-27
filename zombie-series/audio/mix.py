# Build the full soundtrack: voice + SFX + score, duck the score under the voice, master to -14 LUFS.
# usage: python3 -I mix.py <scratch_dir> <timeline.json> <voice_dir> <out_dir>
import sys, os, json, subprocess, re, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pedalboard import Pedalboard, Reverb, LowpassFilter, HighpassFilter, Compressor, Limiter, PeakFilter, Gain
import sfx as X
from music import build

S, TL, VD, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
SR = X.SR
T = json.load(open(TL)); E = T['events']; DUR = T['dur']; N = int(DUR * SR)
sh = {s['name']: s for s in T['shots']}
db = lambda d: 10 ** (d / 20)

class Track:
    def __init__(self): self.x = np.zeros((N, 2), np.float32)
    def add(self, sig, t, gain_db=0.0):
        i = int(round(t * SR)); sig = np.asarray(sig, np.float32)
        if sig.ndim == 1: sig = X.st(sig)
        if i < 0: sig = sig[-i:]; i = 0
        m = min(len(sig), N - i)
        if m > 0: self.x[i:i + m] += sig[:m] * db(gain_db)
    def span(self, sig, t0, t1, gain_db=0.0, fi=0.4, fo=0.6):
        n = int((t1 - t0) * SR); s = sig[:n]
        self.add(X.fade(s, fi, fo), t0, gain_db)

def fx(x, *plugins): return Pedalboard(list(plugins))(x.astype(np.float32), SR)

# ---------- voice ----------
voice = Track()
V = T['voice']
for L in V['lines']:
    a, _ = sf.read(f'{VD}/{L["id"]}.wav', dtype='float32'); voice.add(a, L['start'])
pa, _ = sf.read(f'{VD}/PA.wav', dtype='float32')
if pa.ndim == 1: pa = X.st(pa, 0, 0.4)
cut = int((E['pa_cut'] - E['pa_start']) * SR); pa = pa[:cut].copy(); pa[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))[:, None]

# ---------- SFX ----------
amb, sfxT, pov = Track(), Track(), Track()
pov_end = sh['pov_open']['end']
# POV stockroom: fridge hum, breath, PA, crowd steps behind the door, switch, silence
amb.span(X.fridge_hum(pov_end + 0.3), 0, pov_end + 0.05, -14, 0.8, 0.05)
t = 0.35; k = 0
while t < 9.4:
    if 5.95 < t < 9.0: t = 9.05; continue                  # breath held after the switch
    kind = 'in' if k % 2 == 0 else 'out'; d = 0.85 if kind == 'in' else 1.05
    if 3.6 < t < 5.9: d *= 0.7                               # faster when the steps start
    pov.add(X.breath(d, kind, 0.9 if kind == 'in' else 0.75), t, -16); t += d + (0.25 if kind == 'out' else 0.1); k += 1
pov.add(X.breath(1.1, 'shaky', 0.8), 9.0, -17)
pa_room = Pedalboard([Reverb(room_size=0.9, damping=0.5, wet_level=0.5, dry_level=0.6, width=1.0), LowpassFilter(3500)])
pov.add(fx(X.pa_pop(1.0), HighpassFilter(300), LowpassFilter(3500)), 1.55, -12)
pov.add(pa_room(X.chime(0.9), SR), 1.85, -11)
pov.add(pa, E['pa_start'], -6.5)
pov.add(fx(X.pa_pop(0.7), HighpassFilter(300), LowpassFilter(3500)), E['pa_cut'], -14)
steps = X.crowd_steps(E['steps_stop'] - E['steps_start'] + 0.6, 2, 26, level=1.0, muffle=850)
env = np.clip(np.linspace(0.15, 1.6, len(steps)), 0, 1.0)[:, None]
env[-int(0.9 * SR):] *= np.linspace(1, 0, int(0.9 * SR))[:, None]
pov.add(fx(steps * env, Reverb(room_size=0.6, wet_level=0.3, dry_level=0.8)), E['steps_start'], -9)
pov.add(X.st(X.lp(X.footstep(1.0, soft=True), 700), 0.15), E['last_step'], -6)
pov.add(X.toggle_switch(1.0), E['switch'] - 0.02, -6)
pov.add(fx(X.groan(1.6, 74, 1.0, 11), LowpassFilter(700), Reverb(room_size=0.5, wet_level=0.4)), 7.6, -20)

# 2D aisle at night (frozen): emergency hum, distant groans, low hit on the cut
a0, a1 = sh['aisle_frozen']['start'], sh['exterior']['start']
amb.span(X.fridge_hum(a1 - a0 + 1), a0, a1, -22, 0.3, 0.4)
sfxT.add(X.boom(0.6, 2.0), a0, -14)
for t, f0, s_ in [(10.4, 80, 3), (13.1, 70, 4), (14.2, 92, 5)]:
    sfxT.add(fx(X.groan(1.5, f0, 1.0, s_), Reverb(room_size=0.7, wet_level=0.45, dry_level=0.7)), t, -21)
sfxT.add(X.reverse_swell(1.7, 1.0), E['boom_where'] - 1.7, -15)
sfxT.add(X.boom(1.0, 3.0), E['boom_where'], -6)

# exterior + shutter: wind, crowd moans, metal rattles, scrapes
e0, e1 = sh['exterior']['start'], sh['gary']['start']
amb.span(X.wind(e1 - e0 + 1), e0, e1, -17, 0.25, 0.3)
for i, t in enumerate(np.arange(e0 + 0.3, e1 - 0.6, 0.75)):
    sfxT.add(fx(X.groan(1.4 + 0.5 * (i % 3), 70 + 9 * (i % 5), 1.0, 20 + i, ['uh', 'oh', 'eh'][i % 3]), Reverb(room_size=0.8, wet_level=0.5, dry_level=0.5)), t, -26 + (3 if i % 4 == 0 else 0))
for t in [e0 + 0.9, e0 + 2.6, e0 + 4.1, sh['shutter_hands']['start'] + 0.2, sh['shutter_hands']['start'] + 1.6, sh['shutter_hands']['start'] + 2.9]:
    sfxT.add(X.metal_rattle(0.8, 1.0, int(t * 10)), t, -15 if t > sh['shutter_hands']['start'] else -19)
for t in [sh['shutter_hands']['start'] + 0.5, sh['shutter_hands']['start'] + 2.2]:
    sfxT.add(X.scrape(1.1, 1.0, int(t)), t, -15)

# Gary: quiet aisle, one wet groan, then dead silence for the deadpan
g0, g1 = sh['gary']['start'], sh['counting']['start']
amb.span(X.room_tone(g1 - g0 + 1), g0, g1, -46, 0.2, 0.3)
sfxT.add(X.groan(1.3, 88, 1.0, 31, 'oh'), g0 + 1.2, -24)

# counting (calm): soft room, pencil tick on "count"
c0, c1 = sh['counting']['start'], sh['rule']['start']
amb.span(X.room_tone(c1 - c0 + 1), c0, c1, -42, 0.5, 0.3)
sfxT.add(X.pencil_tick(1.0), E['count_tick'] + 0.25, -14)
sfxT.add(X.pencil_tick(0.7), E['count_tick'] + 0.42, -16)
# inventory card: whoosh in, a "tok" for each item
sfxT.add(X.whoosh(0.45, 1.0), sh['inventory']['start'] - 0.2, -16)
for k_, f in [('item_cans', 980), ('item_water', 1100), ('item_batt', 1240)]:
    sfxT.add(X.tok(1.0, f), E[k_], -11)
sfxT.add(X.tok(0.8, 600), E['problem_hit'], -12)

# rule card: slam + heartbeat that speeds up toward the alarm
sfxT.add(X.whoosh(0.4, 1.0), sh['rule']['start'] - 0.18, -17)
sfxT.add(X.slam(1.0), E['rule_slam'], -8)
t = E['heart_start']
while t < E['title'] - 0.2:
    sfxT.add(X.heartbeat_at(1.0), t, -9 if t > E['ring'] else -12)
    bpm = 66 + 50 * max(0, (t - E['heart_start']) / (E['title'] - E['heart_start'])) ** 1.6
    t += 60 / bpm
ar0 = sh['aisle_alarm']['start']
amb.span(X.fridge_hum(E['title'] - ar0 + 1), ar0, E['title'], -24, 0.4, 0.05)
sfxT.add(X.groan(1.6, 76, 1.0, 41), ar0 + 1.0, -24)

# the alarm clock: distant, right side, big room; muffled after the cut to the title card
ring = X.alarm_bell(E['silence'] - E['ring'] + 0.3, 1.0)
ring_far = fx(ring, LowpassFilter(5200), Reverb(room_size=0.85, damping=0.4, wet_level=0.55, dry_level=0.55, width=1.0))
ring_far[:, 0] *= 0.55
split = int((E['title'] - E['ring']) * SR)
ring_muf = fx(ring_far, LowpassFilter(1100))
ring_mix = np.concatenate([ring_far[:split], ring_muf[split:] * 0.7])
ring_mix[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))[:, None]
sfxT.add(ring_mix, E['ring'], -13)
sfxT.add(X.breath(0.45, 'in', 1.0), E['ring'] + 0.12, -12)                     # sharp gasp
sfxT.add(fx(X.crowd_steps(E['title'] - E['ring'], 4, 20, level=1.0, muffle=1400), Reverb(room_size=0.7, wet_level=0.35)), E['ring'] + 0.3, -17)
for t, f0, s_ in [(E['ring'] + 0.25, 84, 51), (E['ring'] + 0.6, 70, 52), (E['ring'] + 1.1, 95, 53)]:
    sfxT.add(fx(X.groan(1.3, f0, 1.0, s_), Reverb(room_size=0.6, wet_level=0.35)), t, -19)
for t in (E['flicker1'], E['flicker2']):
    sfxT.add(X.flicker_buzz(0.14, 1.0), t, -16); sfxT.add(X.click(0.6, 900), t, -20)
sfxT.add(X.riser(E['title'] - E['flicker1'] + 0.05, 1.0), E['flicker1'], -15)
sfxT.add(X.reverse_swell(1.2, 1.0), E['title'] - 1.2, -13)
sfxT.add(X.boom(1.0, 3.5), E['title'], -4)

# ---------- score ----------
stems = build(f'{S}/sf/GeneralUser-GS.sf2', T)
hall = Pedalboard([Reverb(room_size=0.78, damping=0.45, wet_level=0.28, dry_level=0.85, width=1.0)])
gains = dict(dread=1, pulse=-1, humor=0, calm=2, tension=4, title=1)
score = Track()
for name, x in stems.items():
    y = hall(x, SR)
    if name == 'calm': y = fx(y, PeakFilter(2500, -2, 1.0))
    score.add(y[:N], 0, gains[name])
# hard silence for the comic beat and the very end
def silence(tr, t0, t1, f=0.06):
    i0, i1, nf = int(t0 * SR), int(t1 * SR), int(f * SR)
    tr.x[i0:i0 + nf] *= np.linspace(1, 0, nf)[:, None]; tr.x[i0 + nf:i1] = 0
    if i1 + nf < N: tr.x[i1:i1 + nf] *= np.linspace(0, 1, nf)[:, None]
for tr in (score, amb, sfxT):
    silence(tr, E['silence'], DUR + 1, 0.03)
silence(score, E['gary_silence'] + 0.25, E['pizz_sting'] - 0.02, 0.35)

# ---------- ducking: score -6 dB and ambience -3 dB while the narrator talks ----------
v = np.abs(voice.x).mean(1); win = int(0.05 * SR)
envv = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, 'same'))
active = (envv > 0.004).astype(float)
k = int(0.25 * SR); active = np.convolve(active, np.ones(k) / k, 'same'); active = np.clip(active * 1.5, 0, 1)
score.x *= (1 - active * (1 - db(-6)))[:, None]; amb.x *= (1 - active * (1 - db(-3)))[:, None]

# ---------- master ----------
mix = voice.x * db(-1) + score.x * db(-4) + amb.x + sfxT.x + pov.x
# note: pedalboard's Limiter adds make-up gain equal to -threshold, so every Limiter is followed by Gain(threshold)
mix = Pedalboard([Compressor(threshold_db=-16, ratio=2.0, attack_ms=12, release_ms=150), Limiter(threshold_db=-2.0), Gain(-2.0)])(mix.astype(np.float32), SR)
for name, tr in [('voice', voice.x), ('score', score.x * db(-4)), ('sfx', amb.x + sfxT.x + pov.x)]:
    sf.write(f'{OUT}/stem_{name}.wav', tr, SR)
sf.write(f'{OUT}/premaster.wav', mix, SR)
# loudness to -14 LUFS (measure, gain, limit)
def lufs(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
g = -14.0 - lufs(f'{OUT}/premaster.wav')
for it in range(3):   # converge on -14 LUFS with peaks held under -1.5 dBFS
    final = Pedalboard([Gain(g), Limiter(threshold_db=-1.5, release_ms=80), Gain(-1.5)])(mix, SR)
    sf.write(f'{OUT}/mix.wav', final, SR, subtype='PCM_24')
    L = lufs(f'{OUT}/mix.wav'); print('pass %d: gain %.2f dB -> %.2f LUFS, peak %.2f dBFS' % (it, g, L, 20 * np.log10(np.abs(final).max())))
    if abs(L + 14) < 0.15: break
    g += -14.0 - L
