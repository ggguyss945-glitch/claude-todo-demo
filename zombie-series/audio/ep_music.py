# Episode score as cues. Each cue runs from its start to the next cue, is rendered on its own synth
# (so instruments never fight over a channel) and fades out over a short tail.
import numpy as np
from music import Score, GM, m, ms, SR

GM.update(glock=9, brass=61, horn=60, celesta=8, harp=46, flute=73, oboe=68, clarinet=71, marimba=12)

def pad(sc, ch, t0, t1, keys, vel=60, fi=1.0, fo=1.2, top=100):
    sc.ramp(ch, max(0, t0 - 0.01), t0 + fi, 0, top); sc.ramp(ch, max(t0 + fi, t1 - fo), t1, top, 0)
    sc.chord(t0, t1 - t0 + 0.3, ch, keys, vel)

def ostinato(sc, ch, t0, t1, bpm, keys, vel=80, frac=0.45, accent=(0,)):
    q = 60 / bpm / 2; t = t0; i = 0
    while t < t1 - 0.02:
        sc.note(t, q * frac, ch, keys[i % len(keys)], vel + (12 if i % len(keys) in accent else 0)); t += q; i += 1

def chords_seq(sc, ch, t0, t1, seq, bar, vel=55, bass_ch=None, bass_vel=70, arp=False):
    t = t0; i = 0
    while t < t1 - 0.1:
        root, up = seq[i % len(seq)]; d = min(bar, t1 - t)
        if bass_ch is not None: sc.note(t, d * 0.98, bass_ch, m(root), bass_vel)
        if arp:
            for j, k in enumerate(up): sc.note(t + j * bar / (len(up) + 1), d - j * bar / (len(up) + 1), ch, k, vel - 6 + 4 * (j == len(up) - 1))
        else: sc.chord(t, d * 0.99, ch, up, vel)
        t += bar; i += 1

DM = [('D2', ms('D3', 'F3', 'A3')), ('Bb1', ms('D3', 'F3', 'Bb3')), ('G1', ms('D3', 'G3', 'Bb3')), ('A1', ms('C#3', 'E3', 'A3'))]
HOPE = [('Bb1', ms('F3', 'Bb3', 'D4')), ('F2', ms('F3', 'A3', 'C4')), ('C2', ms('E3', 'G3', 'C4')), ('D2', ms('F3', 'A3', 'D4'))]
WARM = [('F2', ms('A3', 'C4', 'F4')), ('C2', ms('G3', 'C4', 'E4')), ('D2', ms('A3', 'D4', 'F4')), ('Bb1', ms('F3', 'Bb3', 'D4'))]

# ---------- cue writers: (sc, D, p) with local time 0..D ----------
def dawn(sc, D, p):
    pn, pd, gl = sc.inst(0, 'piano'), sc.inst(1, 'warm_pad'), sc.inst(2, 'glass')
    sc.cc.append((0, pn, 64, 127)); bar = 60 / 64 * 4
    chords_seq(sc, pn, 0.2, D, [('D2', ms('A3', 'D4', 'F4')), ('Bb1', ms('F3', 'Bb3', 'D4')), ('F2', ms('A3', 'C4', 'F4')), ('C2', ms('G3', 'C4', 'E4'))], bar, 42, pn, 50, arp=True)
    pad(sc, pd, 0, D, ms('D3', 'A3', 'F4'), 40, 2.5, 2.0, 80); sc.note(1.0, D - 1, gl, m('A5'), 34)

def dread(sc, D, p):
    cb, ce, ha, tr = sc.inst(0, 'contrabass'), sc.inst(1, 'cello'), sc.inst(2, 'halo'), sc.inst(3, 'tremolo')
    pad(sc, cb, 0, D, ms('D1', 'D2'), 92, 2.0, 1.5, 105); pad(sc, ha, 0, D, ms('D3', 'A3', 'D4'), 48, 3.0, 2.0, 70)
    t = 1.5
    while t < D - 3:
        sc.note(t, 3.2, ce, [m('A2'), m('Bb2'), m('A2'), m('F2')][int(t) % 4], 62); t += 3.6
    sc.ramp(tr, 0, D * 0.6, 0, 40); sc.ramp(tr, D * 0.6, D, 40, 0); sc.chord(0.5, D, tr, ms('D4', 'Eb4'), 50)

def pulse_soft(sc, D, p):
    ce, st, cb = sc.inst(0, 'cello'), sc.inst(1, 'strings'), sc.inst(2, 'contrabass')
    sc.ramp(ce, 0, 1.5, 30, 75); sc.ramp(ce, D - 1.2, D, 75, 0)
    ostinato(sc, ce, 0, D, 96, ms('D3', 'A2', 'D3', 'F3', 'D3', 'A2', 'C3', 'D3'), 62, accent=(0, 4))
    bar = 60 / 96 * 4; chords_seq(sc, st, 0, D, DM, bar, 42, cb, 70); sc.ramp(st, 0, 3, 10, 55); sc.ramp(st, D - 1.2, D, 55, 0)

def tick(sc, D, p):
    pz, st, cb, tp = sc.inst(0, 'pizz'), sc.inst(1, 'tremolo'), sc.inst(2, 'contrabass'), sc.inst(3, 'timpani')
    ostinato(sc, pz, 0, D, 120, ms('A4', 'A4', 'D5', 'A4', 'Bb4', 'A4', 'D5', 'A4'), 70, 0.3, accent=(0,))
    pad(sc, st, 0, D, ms('D4', 'A4'), 45, 3, 1.5, 70); pad(sc, cb, 0, D, ms('D2'), 70, 2, 1.2, 90)
    t = 0
    while t < D - 0.5: sc.note(t, 0.3, tp, m('D2'), 50); t += 2.0

def stalk(sc, D, p):
    cb, ha, gl, pz = sc.inst(0, 'contrabass'), sc.inst(1, 'halo'), sc.inst(2, 'glass'), sc.inst(3, 'pizz')
    pad(sc, ha, 0, D, ms('D3', 'G#3'), 38, 3, 2, 65); pad(sc, cb, 0, D, ms('D1'), 70, 2, 2, 85)
    t = 0.8
    while t < D - 1: sc.note(t, 0.4, pz, [m('D2'), m('Eb2'), m('D2'), m('A1')][int(t / 1.7) % 4], 55); t += 1.7
    sc.note(2.0, D - 3, gl, m('Eb6'), 26)

def jingle(sc, D, p):
    gk, br, pn, bs = sc.inst(0, 'glock'), sc.inst(1, 'brass'), sc.inst(2, 'piano'), sc.inst(3, 'contrabass')
    q = 60 / 132
    mel = [('C5', 1), ('E5', 1), ('G5', 1), ('C6', 2), ('A5', 1), ('G5', 2), ('E5', 1), ('F5', 1), ('D5', 1), ('C5', 3)]
    t = 0.05
    for rep in range(3):
        for n, l in mel:
            if t > D: break
            sc.note(t, q * l * 0.9, gk, m(n), 100); sc.note(t, q * l * 0.9, br, m(n) - 12, 78); t += q * l
    for i in range(int(D / (q * 4)) + 1):
        sc.chord(i * q * 4, q * 3.8, pn, [ms('C3', 'E3', 'G3'), ms('F3', 'A3', 'C4'), ms('G3', 'B3', 'D4'), ms('C3', 'E3', 'G3')][i % 4], 70)
        sc.note(i * q * 4, q * 1.8, bs, [m('C2'), m('F2'), m('G2'), m('C2')][i % 4], 85)

def chaos(sc, D, p):
    tr, tp, br, cb = sc.inst(0, 'tremolo'), sc.inst(1, 'timpani'), sc.inst(2, 'brass'), sc.inst(3, 'contrabass')
    pad(sc, tr, 0, D, ms('D4', 'Eb4', 'A4', 'Bb4', 'D5'), 85, 0.2, 1.0, 120); pad(sc, cb, 0, D, ms('D1', 'D2'), 100, 0.1, 1.0, 115)
    t = 0
    while t < D - 0.3: sc.note(t, 0.15, tp, m('D2'), 110 if int(t * 4) % 4 == 0 else 70); t += 0.25
    for t in np.arange(0, D - 0.5, 1.5): sc.chord(t, 0.35, br, ms('D3', 'Eb3', 'A3'), 105)

def rule(sc, D, p):
    cb, ch, tp = sc.inst(0, 'contrabass'), sc.inst(1, 'choir'), sc.inst(2, 'timpani')
    sc.note(0.1, 1.5, tp, m('D2'), 118); pad(sc, cb, 0.1, D, ms('D1', 'A1'), 95, 0.1, 1.2, 110); pad(sc, ch, 0.3, D, ms('D3', 'A3', 'D4'), 60, 0.8, 1.2, 85)

def humor(sc, D, p):
    pz, bs = sc.inst(0, 'pizz'), sc.inst(1, 'bassoon')
    seq = ms('D3', 'F3', 'A3', 'F3', 'D3', 'E3', 'F3', 'A3'); t = 0.2; i = 0
    while t < D - 0.6: sc.note(t, 0.3, pz, seq[i % 8], 60); t += 0.42; i += 1
    sc.note(D - 0.55, 0.25, pz, m('A4'), 92); sc.note(D - 0.3, 0.4, pz, m('D3'), 96); sc.ramp(bs, 0, 0.1, 75, 75); sc.note(D - 0.3, 0.42, bs, m('D2'), 64)

def day(sc, D, p):
    tp, gl, ha = sc.inst(0, 'timpani'), sc.inst(1, 'glass'), sc.inst(2, 'halo')
    e = min(D, 9.0)   # a stinger that settles into a short pad, never a long drone
    sc.note(0.05, 1.2, tp, m('D2'), 80); sc.note(0.1, e, gl, m('D6'), 50); pad(sc, ha, 0, e, ms('D3', 'A3'), 45, 0.3, 2.5, 75)

def think(sc, D, p):
    pn, pd = sc.inst(0, 'piano'), sc.inst(1, 'warm_pad')
    sc.cc.append((0, pn, 64, 127)); bar = 60 / 72 * 4
    chords_seq(sc, pn, 0.1, D, [('D2', ms('A3', 'D4', 'F4', 'A4')), ('C2', ms('G3', 'C4', 'E4', 'G4')), ('Bb1', ms('F3', 'Bb3', 'D4', 'F4')), ('A1', ms('E3', 'A3', 'C#4', 'E4'))], bar, 40, pn, 48, arp=True)
    pad(sc, pd, 0, D, ms('D3', 'A3'), 34, 2, 2, 70)

def build(sc, D, p):
    pz, st, cb, tp = sc.inst(0, 'pizz'), sc.inst(1, 'strings'), sc.inst(2, 'contrabass'), sc.inst(3, 'timpani')
    ostinato(sc, pz, 0, D, 104, ms('F3', 'C4', 'A3', 'C4', 'F3', 'C4', 'Bb3', 'C4'), 66, 0.35, accent=(0, 4))
    bar = 60 / 104 * 4; chords_seq(sc, st, 0, D, WARM, bar, 48, cb, 66); sc.ramp(st, 0, 2, 20, 70); sc.ramp(st, D - 1.5, D, 70, 0)
    t = 0
    while t < D - 0.5: sc.note(t, 0.3, tp, m('F2'), 55); t += bar / 2

def hope(sc, D, p):
    pn, st, pd, gl = sc.inst(0, 'piano'), sc.inst(1, 'slow_strings'), sc.inst(2, 'warm_pad'), sc.inst(3, 'glass')
    sc.cc.append((0, pn, 64, 127)); bar = 60 / 66 * 4
    chords_seq(sc, pn, 0.1, D, HOPE, bar, 46, pn, 52, arp=True); chords_seq(sc, st, 0.1, D, HOPE, bar, 44)
    sc.ramp(st, 0, 3, 10, 80); sc.ramp(st, D - 1.5, D, 80, 0); pad(sc, pd, 0, D, ms('F3', 'C4'), 30, 2, 2, 65); sc.note(1, D - 1, gl, m('F6'), 28)

def radio(sc, D, p):
    ha, gl, pn = sc.inst(0, 'halo'), sc.inst(1, 'glass'), sc.inst(2, 'piano')
    pad(sc, ha, 0, D, ms('A2', 'E3', 'C4'), 42, 3, 2, 70); sc.cc.append((0, pn, 64, 127))
    t = 1.0; seq = ms('E5', 'C5', 'A4', 'B4', 'E5', 'G5', 'F5', 'E5')
    i = 0
    while t < D - 1.5: sc.note(t, 1.8, pn, seq[i % 8], 34); t += 2.2; i += 1
    sc.note(0.5, D - 0.5, gl, m('A5'), 24)

def warm(sc, D, p):
    pn, pd, cl = sc.inst(0, 'piano'), sc.inst(1, 'warm_pad'), sc.inst(2, 'clarinet')
    sc.cc.append((0, pn, 64, 127)); bar = 60 / 84 * 3
    chords_seq(sc, pn, 0.1, D, WARM, bar, 44, pn, 50, arp=True); pad(sc, pd, 0, D, ms('F3', 'A3', 'C4'), 30, 2, 2, 70)
    mel = ms('A4', 'C5', 'F5', 'E5', 'D5', 'C5', 'A4', 'G4'); t = bar * 2; i = 0
    while t < D - 2: sc.note(t, bar * 0.9, cl, mel[i % 8], 52); t += bar; i += 1

def action(sc, D, p):
    ce, cb, st, tp, br = sc.inst(0, 'cello'), sc.inst(1, 'contrabass'), sc.inst(2, 'strings'), sc.inst(3, 'timpani'), sc.inst(4, 'brass')
    ostinato(sc, ce, 0, D, 128, ms('D3', 'D3', 'F3', 'D3', 'G3', 'D3', 'F3', 'E3'), 84, 0.4, accent=(0, 4))
    ostinato(sc, cb, 0, D, 128, ms('D2', 'D2', 'D2', 'D2', 'Bb1', 'Bb1', 'C2', 'C2'), 80, 0.5)
    bar = 60 / 128 * 4; chords_seq(sc, st, 0, D, DM, bar, 62); sc.ramp(st, 0, 1, 50, 95); sc.ramp(st, D - 1, D, 95, 0)
    t = 0
    while t < D - 0.2: sc.note(t, 0.2, tp, m('D2'), 95); t += bar / 2
    for t in np.arange(bar * 2, D - 0.5, bar * 2): sc.chord(t, 0.4, br, ms('D3', 'A3', 'D4'), 96)

def sting_mystery(sc, D, p):
    tp, cb, ch, gl = sc.inst(0, 'timpani'), sc.inst(1, 'contrabass'), sc.inst(2, 'choir'), sc.inst(3, 'glass')
    sc.note(0.0, 2, tp, m('D2'), 112); pad(sc, cb, 0, D, ms('D1'), 100, 0.05, 1.5, 110)
    pad(sc, ch, 0.2, D, ms('A3', 'Bb3', 'D4'), 62, 1.0, 1.5, 90); sc.note(0.3, D, gl, m('Bb5'), 40); sc.note(0.3, D, gl, m('A5'), 40)

def plan(sc, D, p):
    pz, st, cb, tp = sc.inst(0, 'pizz'), sc.inst(1, 'strings'), sc.inst(2, 'contrabass'), sc.inst(3, 'timpani')
    ostinato(sc, pz, 0, D, 100, ms('D4', 'A3', 'F4', 'A3', 'D4', 'A3', 'E4', 'A3'), 62, 0.35, accent=(0,))
    bar = 60 / 100 * 4; chords_seq(sc, st, 0, D, [('D2', ms('D3', 'F3', 'A3')), ('Bb1', ms('D3', 'F3', 'Bb3')), ('F2', ms('C3', 'F3', 'A3')), ('C2', ms('C3', 'E3', 'G3'))], bar, 48, cb, 68)
    sc.ramp(st, 0, 3, 15, 70); sc.ramp(st, D - 1.5, D, 70, 0)
    t = 0
    while t < D - 0.5: sc.note(t, 0.3, tp, m('D2'), 48); t += bar

def night_op(sc, D, p):
    cb, tr, tp, ha = sc.inst(0, 'contrabass'), sc.inst(1, 'tremolo'), sc.inst(2, 'timpani'), sc.inst(3, 'halo')
    pad(sc, cb, 0, D, ms('D1', 'D2'), 88, 1.5, 1.0, 100); pad(sc, ha, 0, D, ms('D3', 'F3', 'A3'), 40, 2.5, 1.0, 70)
    sc.ramp(tr, 0, D, 10, 85); sc.chord(0, D, tr, ms('A3', 'D4', 'Eb4'), 60)
    t = 0.5
    while t < D - 0.4: sc.note(t, 0.25, tp, m('D2'), 62); sc.note(t + 0.28, 0.2, tp, m('D2'), 44); t += 60 / 70

def reveal(sc, D, p):
    tr, gl, cb, ch = sc.inst(0, 'tremolo'), sc.inst(1, 'glass'), sc.inst(2, 'contrabass'), sc.inst(3, 'choir')
    sc.ramp(tr, 0, D, 10, 120); sc.chord(0, D, tr, ms('D4', 'F4', 'Ab4', 'B4'), 72)
    sc.note(0, D, gl, m('B5'), 34); sc.note(D * 0.5, D * 0.5, gl, m('C6'), 34); pad(sc, cb, 0, D, ms('D1'), 80, 2, 0.4, 100); pad(sc, ch, D * 0.4, D, ms('D3', 'Ab3'), 50, 2, 0.4, 85)

def twist(sc, D, p):
    tp, cb, ch, br, tr = sc.inst(0, 'timpani'), sc.inst(1, 'contrabass'), sc.inst(2, 'choir'), sc.inst(3, 'brass'), sc.inst(4, 'tremolo')
    sc.note(0.0, 2.5, tp, m('D2'), 127); sc.note(0.0, 0.8, br, m('D2'), 110); sc.note(0.0, 0.8, br, m('Ab2'), 105)
    pad(sc, cb, 0, D, ms('D1', 'D2'), 110, 0.02, 2.0, 120); pad(sc, ch, 0.1, D, ms('D3', 'Ab3', 'D4'), 72, 0.4, 2.0, 100)
    sc.ramp(tr, 0, D, 60, 100); sc.chord(0.5, D, tr, ms('D5', 'Eb5'), 60)

def chase(sc, D, p):
    ce, cb, st, tp, br = sc.inst(0, 'cello'), sc.inst(1, 'contrabass'), sc.inst(2, 'tremolo'), sc.inst(3, 'timpani'), sc.inst(4, 'brass')
    ostinato(sc, ce, 0, D, 148, ms('D3', 'Eb3', 'D3', 'F3', 'D3', 'Eb3', 'D3', 'A2'), 92, 0.4, accent=(0, 4))
    ostinato(sc, cb, 0, D, 148, ms('D2', 'D2', 'D2', 'D2', 'Bb1', 'Bb1', 'A1', 'A1'), 86, 0.5)
    pad(sc, st, 0, D, ms('D4', 'Eb4', 'A4'), 80, 0.3, 0.8, 115)
    t = 0
    while t < D - 0.2: sc.note(t, 0.15, tp, m('D2'), 100 if int(t / (60 / 148)) % 2 == 0 else 72); t += 60 / 148
    for t in np.arange(0, D - 0.4, 60 / 148 * 4): sc.chord(t, 0.3, br, ms('D3', 'A3'), 100)

def resolve(sc, D, p):
    pn, st, pd = sc.inst(0, 'piano'), sc.inst(1, 'slow_strings'), sc.inst(2, 'warm_pad')
    sc.cc.append((0, pn, 64, 127)); bar = 60 / 60 * 4
    seq = [('D2', ms('A3', 'D4', 'F4')), ('Bb1', ms('F3', 'Bb3', 'D4')), ('F2', ms('A3', 'C4', 'F4')), ('A1', ms('E3', 'A3', 'C#4'))]
    chords_seq(sc, pn, 0.1, D, seq, bar, 44, pn, 50, arp=True); chords_seq(sc, st, 0.1, D, seq, bar, 40)
    sc.ramp(st, 0, 3, 10, 70); sc.ramp(st, D - 2, D, 70, 0); pad(sc, pd, 0, D, ms('D3', 'A3'), 30, 2, 2, 60)

def end(sc, D, p):
    tp, cb, ch, gl, pn = sc.inst(0, 'timpani'), sc.inst(1, 'contrabass'), sc.inst(2, 'choir'), sc.inst(3, 'glass'), sc.inst(4, 'piano')
    sc.note(0.1, 2.0, tp, m('D2'), 118); pad(sc, cb, 0.1, D, ms('D1'), 100, 0.05, 1.5, 110); pad(sc, ch, 0.1, D, ms('D3', 'A3', 'D4'), 66, 0.5, 1.5, 90)
    sc.cc.append((0, pn, 64, 127))
    for i, k in enumerate(ms('D4', 'F4', 'A4', 'G4', 'F4', 'E4', 'D4')): sc.note(1.2 + i * 0.55, 1.4, pn, k, 50)
    sc.note(0.4, D, gl, m('A5'), 40)

def relief(sc, D, p):
    st, pd, pn = sc.inst(0, 'slow_strings'), sc.inst(1, 'warm_pad'), sc.inst(2, 'piano')
    pad(sc, st, 0, min(D, 7), ms('F3', 'A3', 'C4', 'F4'), 50, 1.2, 2.5, 85); pad(sc, pd, 0, min(D, 7), ms('F2', 'C3'), 36, 1.0, 2.5, 70)
    sc.cc.append((0, pn, 64, 127)); sc.note(0.3, 3, pn, m('F2'), 46); sc.chord(0.35, 3, pn, ms('A3', 'C4', 'F4'), 40)

CUES = dict(dawn=dawn, dread=dread, pulse_soft=pulse_soft, tick=tick, stalk=stalk, jingle=jingle, chaos=chaos, rule=rule, humor=humor,
            day=day, think=think, build=build, hope=hope, radio=radio, warm=warm, action=action, sting_mystery=sting_mystery, plan=plan,
            night_op=night_op, reveal=reveal, twist=twist, chase=chase, resolve=resolve, end=end, relief=relief)
# cue loudness in the score bus (dB); diegetic jingle is handled by the mixer
GAIN = dict(dawn=0, dread=1, pulse_soft=-1, tick=0, stalk=1, jingle=0, chaos=2, rule=2, humor=0, day=-2, think=0, build=-1, hope=1,
            radio=0, warm=0, action=1, sting_mystery=2, plan=-1, night_op=1, reveal=2, twist=3, chase=1, resolve=1, end=2, relief=0)

def render_cue(sf2, cue, D, p, tail=2.5):
    sc = Score(sf2, D + tail)
    CUES[cue](sc, D, p)
    return sc.render()
