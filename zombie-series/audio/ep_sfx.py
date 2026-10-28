# Episode sound effects and ambience beds, built from the synthesized primitives in sfx.py.
# Every effect is fx(p, dur) -> float32 (N, 2); dur is set when the script gives the sound an end ('until').
import numpy as np
from pedalboard import Pedalboard, Reverb, LowpassFilter, HighpassFilter, Distortion, Compressor
import sfx as X
from sfx import SR, t_, lp, hp, bp, white, pink, brown, st, fade, norm

R = np.random.default_rng(11)
def fx(x, *plugins): return Pedalboard(list(plugins))(np.asarray(x, np.float32), SR)
def place(n, parts):
    out = np.zeros((n, 2), np.float32)
    for t, s in parts:
        i = int(t * SR); s = s if s.ndim == 2 else st(s); m = min(len(s), n - i)
        if m > 0 and i >= 0: out[i:i + m] += s[:m]
    return out
def tink(f, d=0.25, a=1.0):
    t = t_(d); return a * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t / (d * 0.25))

# ---------- one-shots ----------
def keys_jingle(p, dur=None):
    n = int(0.8 * SR); parts = []
    for i in range(12):
        parts.append((R.uniform(0, 0.45), st(tink(R.uniform(2800, 7200), 0.2, R.uniform(0.2, 0.6)), R.uniform(-0.4, 0.4))))
    return fx(place(n, parts), HighpassFilter(1500)) * 0.7
def door_close(p, dur=None):
    t = t_(0.5); x = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.08) + 0.5 * lp(white(len(t)), 900) * np.exp(-t / 0.05)
    return place(int(0.7 * SR), [(0, st(x)), (0.08, X.click(0.7, 2200))])
def pizz_sting(p, dur=None):
    from music import Score, m
    import os
    sc = Score(SF2, 1.4); pz, bs = sc.inst(0, 'pizz'), sc.inst(1, 'bassoon')
    sc.note(0.0, 0.25, pz, m('A4'), 96); sc.note(0.24, 0.4, pz, m('D3'), 100); sc.ramp(bs, 0.2, 0.25, 70, 70); sc.note(0.24, 0.42, bs, m('D2'), 62)
    return sc.render() * 0.9
def tap(p, dur=None): return X.click(0.5, 2600)
def heartbeat_run(p, dur):
    parts, t = [], 0.0
    while t < dur - 0.4:
        parts.append((t, X.heartbeat_at(1.0))); k = t / max(dur, 1)
        t += 60 / (p.get('bpm0', 72) + (p.get('bpm1', 110) - p.get('bpm0', 72)) * k)
    return place(int(dur * SR), parts)
def phone_ring(p, dur):
    # a marimba ringtone inside a steel box: muffled, metallic
    from music import Score, m
    sc = Score(SF2, dur + 0.5); mb = sc.inst(0, 'marimba'); t = 0.0
    while t < dur:
        for j, k in enumerate(['E5', 'B5', 'E6', 'B5', 'G#5', 'E5']): sc.note(t + j * 0.14, 0.2, mb, m(k), 100)
        t += 1.6
    y = sc.render()[:int(dur * SR)]
    return fx(y, HighpassFilter(300), LowpassFilter(2600), Reverb(room_size=0.25, damping=0.2, wet_level=0.4, dry_level=0.8)) * 0.9
def steps_close(p, dur):
    return X.crowd_steps(dur, 1.2, 2.4, walkers=p.get('n', 3), level=1.4, muffle=1500, seed=int(dur * 10))
def groan_close(p, dur=None):
    return fx(X.groan(1.4, R.uniform(70, 95), 1.0, int(R.integers(1, 99)), R.choice(['uh', 'oh', 'eh'])), Reverb(room_size=0.3, wet_level=0.2))
def thud_land(p, dur=None):
    t = t_(0.5); x = np.sin(2 * np.pi * 60 * t) * np.exp(-t / 0.07) + 0.6 * lp(white(len(t)), 700) * np.exp(-t / 0.04)
    return st(x) * 1.2
def freezer_slam(p, dur=None):
    return place(int(2.0 * SR), [(0, X.slam(1.3)), (0.0, X.metal_rattle(0.4, 1.6, 9)), (0.02, X.boom(0.6, 1.4)), (0.12, X.click(0.8, 1800))])
def stamp(p, dur=None):
    t = t_(0.3); return st(np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.05) + 0.6 * bp(white(len(t)), 400, 3000) * np.exp(-t / 0.02))
def thump_metal(p, dur=None):
    return place(int(1.0 * SR), [(0, st(np.sin(2 * np.pi * 85 * t_(0.6)) * np.exp(-t_(0.6) / 0.09))), (0, X.metal_rattle(0.3, 0.8, 3))])
def sock_step(p, dur=None): return st(lp(X.footstep(0.5, soft=True), 600))
def creak(p, dur=None):
    d = 0.9; t = t_(d); rate = 35 + 25 * np.sin(np.pi * t / d); ph = np.cumsum(2 * np.pi * rate / SR)
    pulses = (np.sin(ph) > 0.97).astype(float)
    x = bp(lp(pulses, 4000) + 0.02 * white(len(t)), 400, 1800) * np.sin(np.pi * t / d)
    return st(norm(x, 0.6))
def big_switch(p, dur=None): return place(int(0.4 * SR), [(0, X.toggle_switch(1.4)), (0.03, X.click(0.9, 900))])
def pa_pop(p, dur=None): return fx(X.pa_pop(1.0), HighpassFilter(300), LowpassFilter(3500))
def crowd_surge(p, dur):
    parts = [(0, X.crowd_steps(dur, 6, 14, walkers=20, level=1.2, muffle=1200, seed=5))]
    for i in range(int(dur * 2)): parts.append((i * 0.5 + R.uniform(0, 0.3), X.metal_rattle(0.4, 0.7, i)))
    for i in range(int(dur)): parts.append((i + R.uniform(0, 0.5), X.groan(1.2, R.uniform(70, 110), 0.7, 60 + i)))
    return fx(place(int(dur * SR), parts), Reverb(room_size=0.6, wet_level=0.3))
def boom(p, dur=None): return X.boom(1.0, 2.5)
def cable_rip(p, dur=None):
    t = t_(0.25); x = bp(white(len(t)), 800, 6000) * np.exp(-t / 0.05) + 0.6 * np.sign(np.sin(2 * np.pi * 120 * t)) * np.exp(-t / 0.03)
    return st(x * 0.8)
def jingle_cut(p, dur=None): return X.flicker_buzz(0.12, 1.2)
def metal_rattle(p, dur=None): return X.metal_rattle(0.8, 1.0, 21)
def lock_click(p, dur=None): return place(int(0.3 * SR), [(0, X.click(0.9, 1700)), (0.06, X.click(0.6, 2600))])
def radio_click(p, dur=None):
    burst = st(bp(white(int(0.1 * SR)), 900, 4000) * np.exp(-t_(0.1) / 0.03) * 0.4)
    return place(int(0.2 * SR), [(0, X.click(0.7, 1500)), (0.01, burst)])
def low_sting(p, dur=None): return place(int(2.6 * SR), [(0, X.reverse_swell(0.8, 0.8)), (0.8, X.boom(0.8, 1.8))])
def hum_stop(p, dur=None):
    d = 1.4; t = t_(d); f = 59.7 * 2 * (1 - 0.55 * (t / d) ** 2); x = np.sin(np.cumsum(2 * np.pi * f / SR)) * (1 - t / d) ** 1.5
    return st(x * 0.4, 0, 0.5)
def power_down(p, dur=None):
    d = 1.6; t = t_(d); f = 220 * np.exp(-t / 0.4) + 30; x = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.6) * 0.5
    return place(int(d * SR), [(0, X.click(1.0, 700)), (0, st(x)), (0.02, X.boom(0.5, 1.2))])
def maglock_clunk(p, dur=None):
    t = t_(1.0); ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in [(180, 1, .25), (412, .5, .15), (780, .3, .08)])
    return place(int(1.2 * SR), [(0, st(ring * 0.6)), (0, X.slam(1.0)), (0.01, X.click(1.0, 600))])
def door_bang(p, dur=None): return place(int(1.4 * SR), [(0, X.slam(1.2)), (0.0, X.metal_rattle(0.5, 1.0, 13)), (0.01, X.boom(0.5, 1.0))])
def door_bang_soft(p, dur=None):
    t = t_(0.3); return place(int(0.9 * SR), [(k * 0.22, st(np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.04) + 0.3 * bp(white(len(t)), 800, 3000) * np.exp(-t / 0.01))) for k in range(3)])
def bags_slide(p, dur=None): return fx(X.scrape(1.0, 1.0, 4), LowpassFilter(1800)) + st(lp(pink(SR), 300)[:SR] * 1.5)
def crash(p, dur=None):
    parts = [(0, X.boom(1.2, 2.5)), (0, X.metal_rattle(1.2, 1.6, 31)), (0.0, X.slam(1.2))]
    for i in range(26): parts.append((R.uniform(0.02, 1.4), X.tok(R.uniform(0.3, 0.9), R.uniform(500, 1400))))
    return fx(place(int(2.8 * SR), parts), Reverb(room_size=0.7, wet_level=0.35, dry_level=0.9))
def throw_whoosh(p, dur=None): return X.whoosh(0.35, 0.8)
def alarm_far(p, dur): return fx(X.alarm_bell(dur, 1.0), LowpassFilter(5000), Reverb(room_size=0.85, damping=0.4, wet_level=0.55, dry_level=0.5, width=1.0)) * np.array([0.55, 1.0], np.float32)
def alarm_near(p, dur): return fx(X.alarm_bell(dur, 1.0), LowpassFilter(7000), Reverb(room_size=0.5, wet_level=0.25, dry_level=0.9))
def decoy_alarm(p, dur):
    k = p.get('k', 1); y = X.alarm_bell(dur, 1.0)
    y = fx(y, LowpassFilter(2600 - 120 * k), Reverb(room_size=0.95, damping=0.5, wet_level=0.7, dry_level=0.35, width=1.0))
    return y * np.array([0.6 + 0.06 * k, 1.0 - 0.05 * k], np.float32)
def ladder_steps(p, dur=None): return place(int(5.0 * SR), [(i * 0.6, X.tok(0.6, 420 + 30 * (i % 2))) for i in range(8)])
def breath_run(p, dur):
    parts, t, k = [], 0.0, 0
    while t < dur - 1:
        kind = 'in' if k % 2 == 0 else 'out'; d = 0.55 if kind == 'in' else 0.7
        parts.append((t, X.breath(d, kind, 0.8))); t += d + 0.12; k += 1
    return place(int(dur * SR), parts)
def glass_crunch(p, dur=None): t = t_(0.3); return st(hp(white(len(t)), 3000) * (np.abs(white(len(t))) > 2.2) * np.exp(-t / 0.08) * 1.5)
def decoy_stop(p, dur=None): return X.click(0.3, 1200)
def crowd_steps_far(p, dur): return X.crowd_steps(dur, 4, 18, walkers=30, level=1.0, muffle=700, seed=17)
def run_steps(p, dur):
    return place(int(dur * SR), [(i * 0.17, st(X.footstep(R.uniform(0.7, 1.0)), R.uniform(-0.2, 0.2))) for i in range(int(dur / 0.17))])
def key_try(p, dur=None):
    return place(int(1.3 * SR), [(0, keys_jingle({})), (0.25, X.scrape(0.5, 0.6, 3)), (0.8, X.click(0.5, 2400))])
def hatch_clang(p, dur=None):
    t = t_(2.0); ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in [(210, 1, .6), (455, .6, .4), (690, .4, .3), (1120, .25, .2)])
    return fx(place(int(2.2 * SR), [(0, st(ring * 0.5)), (0, X.slam(1.2))]), Reverb(room_size=0.8, wet_level=0.45, dry_level=0.8))
def ring_cut(p, dur=None): return X.click(0.4, 800)
def whoosh(p, dur=None): return X.whoosh(0.45, 1.0)
def slam(p, dur=None): return X.slam(1.0)
def tok(p, dur=None): return X.tok(1.0, 980)

# ---------- episode 2 ----------
def _glug(f0, d, a=1.0):
    t = t_(d); f = f0 * (1.6 - 0.6 * np.exp(-t / (d * 0.3)))
    return a * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d * 0.35)) * (1 - np.exp(-t / 0.004))
def pipe_cough(p, dur=None):
    # air in the line: a choke, a spit of water, a hollow glug down the pipe
    k = p.get('k', 1); n = 0.9 if k == 1 else 0.7
    air = fx(white(int(0.25 * SR)) * np.exp(-t_(0.25) / 0.06), HighpassFilter(900), LowpassFilter(6000)) * 0.6
    spit = fx(white(int(0.4 * SR)) * (np.abs(np.sin(2 * np.pi * 9 * t_(0.4))) ** 3) * np.exp(-t_(0.4) / 0.15), HighpassFilter(1500), LowpassFilter(8000)) * 0.5
    return norm(fx(place(int(n * SR), [(0, air), (0.05, spit), (0.02, _glug(140 + 30 * k, 0.5, 0.7)), (0.1, 0.5 * _glug(95, 0.6, 0.6))]), Reverb(room_size=0.35, damping=0.6, wet_level=0.22, dry_level=0.9)), 0.8)
def valve_squeak(p, dur=None):
    d = 0.7; t = t_(d); f = 1900 + 500 * np.sin(2 * np.pi * 1.6 * t) + 120 * np.sin(2 * np.pi * 37 * t)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 13 * t))) * np.sin(np.pi * t / d) ** 0.6
    return st(lp(y, 5000) * 0.35)
def water_pour(p, dur):
    # a stream into a plastic bucket: bright noise riding a slow wobble, little bubbles, the note rising as it fills
    dur = dur or 4.0; t = t_(dur); n = len(t)
    jet = bp(pink(n), 500, 5000) * (0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 0.7 * t))
    r = np.random.default_rng(4); bub = np.zeros(n, np.float32)
    for _ in range(int(dur * 14)):
        i = int(r.uniform(0, n - 0.08 * SR)); g = _glug(r.uniform(350, 900) * (1 + t[i] / dur * 0.6), 0.07, r.uniform(0.2, 0.5)); bub[i:i + len(g)] += g
    env = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.3)
    return fx(st((jet * 0.5 + bub * 0.5) * env, 0, 0.3), Reverb(room_size=0.3, damping=0.6, wet_level=0.18, dry_level=0.9))
def lid_clunk(p, dur=None):
    return place(int(0.8 * SR), [(0, X.tok(0.7, 620)), (0.0, fx(X.scrape(0.25, 0.5, 6), LowpassFilter(3000)) * 0.4), (0.03, X.tok(0.4, 1400))])
def pipe_knock(p, dur=None):
    # a knuckle on a pipe somewhere else in the building: dull hit, metallic ring, long hollow tail
    k = p.get('k', 1); t = t_(1.6)
    ring = (np.sin(2 * np.pi * 880 * t) + 0.6 * np.sin(2 * np.pi * 1427 * t) + 0.3 * np.sin(2 * np.pi * 2310 * t)) * np.exp(-t / 0.25) * 0.25
    hit = X.tok(0.9, 300 + 40 * k)
    y = place(int(1.6 * SR), [(0, hit), (0.0, st(ring))])
    return fx(y, LowpassFilter(3500), Reverb(room_size=0.7, damping=0.5, wet_level=0.45, dry_level=0.7, width=0.6))
def chain_rattle(p, dur=None):
    r = np.random.default_rng(12); parts = [(0, X.metal_rattle(0.9, 0.8, 7))]
    for i in range(9): parts.append((0.08 + i * 0.11 + r.uniform(-0.02, 0.02), st(tink(r.uniform(2200, 4200), 0.12, 0.25))))
    return place(int(1.4 * SR), parts)
def thunder(p, dur=None):
    # close: a crack, then the roll; far: only the low roll, longer and softer
    far, close = p.get('far', False), p.get('close', False)
    d = 5.5 if far else 4.5; t = t_(d); n = len(t)
    roll = lp(brown(n), 180 if far else 320) * (1 - np.exp(-t / (0.5 if far else 0.08))) * np.exp(-t / (2.2 if far else 1.6))
    roll *= 0.75 + 0.25 * np.abs(np.sin(2 * np.pi * 0.9 * t + 1.3 * np.sin(2 * np.pi * 0.37 * t)))
    y = st(roll * (0.7 if far else 1.0), 0, 0.8)
    if not far:
        crack = fx(white(int(0.5 * SR)) * np.exp(-t_(0.5) / (0.05 if close else 0.09)), HighpassFilter(300), LowpassFilter(7000)) * (0.9 if close else 0.45)
        y = place(n, [(0, y), (0, st(crack, 0, 0.6))])
    return fx(y, Reverb(room_size=0.95, damping=0.5, wet_level=0.35, dry_level=0.9, width=1.0))
def glass_break(p, dur=None):
    r = np.random.default_rng(31); parts = [(0, fx(white(int(0.35 * SR)) * np.exp(-t_(0.35) / 0.07), HighpassFilter(1800)) * 0.9)]
    for i in range(34): parts.append((r.uniform(0.02, 1.1) ** 1.6, st(tink(r.uniform(2500, 7500), r.uniform(0.05, 0.18), r.uniform(0.08, 0.3)), r.uniform(-0.7, 0.7))))
    return norm(fx(place(int(1.6 * SR), parts), Reverb(room_size=0.5, wet_level=0.2, dry_level=0.9)), 0.9)
def escalator_clank(p, dur=None):
    t = t_(1.4); ring = (np.sin(2 * np.pi * 310 * t) + 0.5 * np.sin(2 * np.pi * 777 * t)) * np.exp(-t / 0.35) * 0.3
    return norm(fx(place(int(1.4 * SR), [(0, X.tok(1.0, 240)), (0.01, X.metal_rattle(0.4, 0.6, 3)), (0, st(ring))]), Reverb(room_size=0.95, damping=0.4, wet_level=0.5, dry_level=0.8, width=1.0)), 0.9)
def drone_buzz(p, dur):
    # four props: a buzzing tone with beats, flying away over the shot (quieter and duller with distance)
    dur = dur or 6.0; t = t_(dur); n = len(t)
    f = 205 + 8 * np.sin(2 * np.pi * 0.4 * t)
    y = sum(np.sign(np.sin(2 * np.pi * np.cumsum(f * r) / SR)) * a for r, a in ((1.0, 0.5), (1.013, 0.4), (0.987, 0.35), (2.02, 0.15)))
    y = y + 0.3 * bp(white(n), 800, 4000)
    away = np.clip(t / max(6.0, dur * 0.5), 0, 1)
    y = lp(y, 3000) * (1 - 0.8 * away) * np.minimum(1, t / 0.8)
    return st(y * 0.12, 0.2, 0.4)
def drone_beep(p, dur=None):
    t = t_(0.5); b = np.sin(2 * np.pi * 2300 * t) * ((t < 0.12) | ((t > 0.2) & (t < 0.32)))
    return fx(st(b * 0.25), LowpassFilter(5000), Reverb(room_size=0.9, wet_level=0.45, dry_level=0.6))
def bottle_roll(p, dur=None):
    d = 1.6; t = t_(d); n = len(t)
    y = bp(white(n), 300, 2500) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 5.5 * t))) * np.exp(-t / 0.9) * np.minimum(1, t / 0.05)
    return fx(st(y * 0.5, 0.15, 0.2), Reverb(room_size=0.6, wet_level=0.3, dry_level=0.8))
def clink(p, dur=None): return place(int(0.6 * SR), [(0, X.tok(0.5, 1600)), (0.01, st(tink(2900, 0.2, 0.5)))])
def paper_rustle(p, dur=None):
    d = 0.9; t = t_(d); y = bp(white(len(t)), 1500, 7000) * (np.abs(np.sin(2 * np.pi * 7 * t)) ** 2) * np.sin(np.pi * t / d)
    return st(y * 0.35)
def drone_song(p, dur):
    return np.zeros((int((dur or 1) * SR), 2), np.float32)   # rendered by the mixer from the jingle cue

EFFECTS = {k: v for k, v in globals().items() if callable(v) and not k.startswith('_') and k not in ('fx', 'place', 'tink', 'st', 'fade', 'norm', 't_', 'lp', 'hp', 'bp', 'white', 'pink', 'brown', 'bed')}
# default gain (dB) of each effect in the SFX bus
LEVEL = dict(alarm_far=-15, alarm_near=-14, decoy_alarm=-21, phone_ring=-14, heartbeat_run=-12, steps_close=-10, groan_close=-20, keys_jingle=-18,
             crowd_surge=-11, crash=-6, freezer_slam=-6, hatch_clang=-8, maglock_clunk=-6, door_bang=-11, boom=-8, breath_run=-18, crowd_steps_far=-16,
             run_steps=-14, pizz_sting=-8, whoosh=-17, slam=-12, tok=-12, stamp=-9, thud_land=-8, low_sting=-14, sock_step=-14, creak=-12, cable_rip=-10,
             power_down=-8, hum_stop=-14, radio_click=-12, lock_click=-12, door_bang_soft=-12, bags_slide=-12, throw_whoosh=-16, glass_crunch=-14,
             ladder_steps=-16, key_try=-12, big_switch=-9, pa_pop=-12, door_close=-12, thump_metal=-10, tap=-16, jingle_cut=-14, metal_rattle=-14, decoy_stop=-30, ring_cut=-30,
             pipe_cough=-10, valve_squeak=-16, water_pour=-15, lid_clunk=-12, pipe_knock=-9, chain_rattle=-12, thunder=-11, glass_break=-9, escalator_clank=-10,
             drone_buzz=-14, drone_beep=-13, bottle_roll=-13, clink=-11, paper_rustle=-16, drone_song=-12)

# ---------- ambience beds ----------
BED_RMS = 0.02
def _rms_to(x, r=BED_RMS): return (x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * r).astype(np.float32)
def bed(name, dur):
    n = int(dur * SR)
    if name in ('restroom', 'storm', 'mall_rain', 'mall_quiet'): return _rms_to(_bed2(name, dur, n))
    if name in ('silence',): return X.room_tone(dur, 0.02)
    if name in ('store_night', 'store_dawn'):
        return X.fridge_hum(dur, 0.18) + X.room_tone(dur, 0.06)
    if name == 'store_day': return X.fridge_hum(dur, 0.22) + X.room_tone(dur, 0.06) + st(0.004 * np.sign(np.sin(2 * np.pi * 120 * t_(dur))), 0, 0.5)
    if name == 'store_dark': return X.room_tone(dur, 0.05) + X.wind(dur, 0.05)
    if name == 'office':
        x = X.room_tone(dur, 0.06) + st(0.01 * np.sin(2 * np.pi * 60 * t_(dur)), 0, 0.3)
        parts = [(i * 1.0, X.tok(0.25, 2400)) for i in range(int(dur))]   # the wall clock
        return x + place(n, parts)
    if name == 'freezer_hum': return X.fridge_hum(dur, 0.35) + X.room_tone(dur, 0.04)
    if name in ('roof', 'roof_night', 'lot_dawn', 'lot_night'):
        x = X.wind(dur, 0.35 if name != 'lot_dawn' else 0.2)
        if name == 'roof_night' or name == 'lot_night':
            t = t_(dur); chirp = (np.sin(2 * np.pi * 4.3 * t) > 0.6) * np.sin(2 * np.pi * 4600 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t))
            x += st(chirp * 0.01, 0.4, 0.6)
        return x
    return X.room_tone(dur, 0.05)
def _bed2(name, dur, n):
    if name == 'restroom':   # fluorescent buzz, a slow drip into the sink
        t = t_(dur); x = X.room_tone(dur, 0.05) + st(0.006 * np.sin(2 * np.pi * 120 * t) + 0.003 * np.sin(2 * np.pi * 240 * t), 0, 0.2)
        return x + place(n, [(i * 2.3 + 0.7, st(0.5 * _glug(1200, 0.06, 0.4), 0.3, 0)) for i in range(int(dur / 2.3))])
    if name in ('storm', 'mall_rain'):
        t = t_(dur); nn = len(t)
        sheet = bp(pink(nn), 400, 9000) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t))
        r = np.random.default_rng(6); drops = np.zeros(nn, np.float32)
        for i in r.integers(0, nn - 400, int(dur * 120)): drops[i:i + 300] += r.uniform(0.05, 0.25) * np.exp(-np.arange(300) / 40) * np.sin(np.arange(300) * r.uniform(0.3, 0.9))
        if name == 'storm': return st(sheet * 0.5, 0, 0.9) + st(hp(drops, 1500) * 0.6, 0, 0.9) + X.wind(dur, 0.25)
        # indoors under a glass roof: duller sheet, drumming on the panes, a big hall around it
        return fx(st(lp(sheet, 3500) * 0.45 + hp(drops, 800) * 0.8, 0, 0.9), Reverb(room_size=0.96, damping=0.5, wet_level=0.45, dry_level=0.7, width=1.0))
    if name == 'mall_quiet':   # a huge empty hall: low air, far creaks
        return fx(X.room_tone(dur, 0.06) + st(lp(brown(n), 90) * 0.1, 0, 0.9), Reverb(room_size=0.97, damping=0.5, wet_level=0.5, dry_level=0.6, width=1.0))
# beds also carry distant groans of the dead outside, a few per minute
GROANS = dict(store_night=7, store_dawn=4, store_dark=6, roof=5, roof_night=6, lot_dawn=5, lot_night=7, office=2, store_day=3, mall_quiet=6, mall_rain=2, restroom=1)
BED_LEVEL = dict(silence=-40, store_night=-22, store_dawn=-22, store_day=-21, store_dark=-24, office=-22, freezer_hum=-18, roof=-17, roof_night=-18, lot_dawn=-19, lot_night=-17,
                 restroom=-23, storm=-27, mall_rain=-28, mall_quiet=-23)
SF2 = None
