#!/usr/bin/env python3
"""Original score for "Perfect Score", written note by note against the narration
timeline and rendered with FluidSynth (MuseScore General soundfont).

Structure follows the retention curve: HOOK (sparse pulse + riser) -> RISING ACTION
(pizzicato ostinato, layers enter) -> CONFLICT (low staccato strings, timpani,
investigation pulse) -> DIP (solo piano) -> RISING ACTION (ostinato build, riser,
dead stop) -> PAYOFF (orchestral hit, silence, warm D major, playful button).

Each stem is a separate MIDI file so the mixer can balance and duck them.
    python3 music.py <outdir>
"""
import os, sys, subprocess
import mido

SF = '/usr/share/sounds/sf3/MuseScore_General_Full.sf3'
TPS = 1920  # ticks per second (120 BPM, 960 ppq)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'music_out'
os.makedirs(OUT, exist_ok=True)

N = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
def p(name):  # 'B3' -> midi
    nm, octv = (name[:-1], int(name[-1])) if name[-1].isdigit() else (name, 4)
    return 12 * (octv + 1) + N[nm]
CH = {  # chord tones (pitch classes as names) for the progressions
    'Bm': ['B', 'D', 'F#'], 'G': ['G', 'B', 'D'], 'D': ['D', 'F#', 'A'], 'A': ['A', 'C#', 'E'], 'Em': ['E', 'G', 'B'],
    'F#': ['F#', 'A#', 'C#'], 'C': ['C', 'E', 'G'], 'Bm/F#': ['F#', 'B', 'D'], 'Gmaj7': ['G', 'B', 'D', 'F#'], 'F#sus': ['F#', 'B', 'C#'],
}
def chord(name, octave=3, spread=True):
    tones = CH[name]
    out, base = [], p(tones[0] + str(octave))
    out.append(base)
    for t in tones[1:]:
        v = p(t + str(octave))
        while v <= out[-1]: v += 12
        out.append(v)
    return out

class Stem:
    def __init__(self, name):
        self.name, self.ev, self.progs = name, [], {}
    def prog(self, ch, program, vol=100, pan=64, bank=0):
        self.progs[ch] = (program, vol, pan, bank)
    def note(self, ch, t, dur, pitch, vel=80):
        if dur <= 0: return
        self.ev.append((t, 1, ch, pitch, max(1, min(127, int(vel)))))
        self.ev.append((t + dur, 0, ch, pitch, 0))
    def cc(self, ch, t, num, val):
        self.ev.append((t, 2, ch, num, int(max(0, min(127, val)))))
    def ramp(self, ch, t0, t1, num, v0, v1, steps=24):
        for i in range(steps + 1):
            k = i / steps
            self.cc(ch, t0 + (t1 - t0) * k, num, v0 + (v1 - v0) * k)
    def save(self):
        mid = mido.MidiFile(ticks_per_beat=960)
        tr = mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        for ch, (prg, vol, pan, bank) in self.progs.items():
            if ch != 9:
                tr.append(mido.Message('control_change', channel=ch, control=0, value=bank, time=0))
                tr.append(mido.Message('program_change', channel=ch, program=prg, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=7, value=vol, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=10, value=pan, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=11, value=127, time=0))
        evs = sorted(self.ev, key=lambda e: (e[0], e[1]))
        last = 0
        for t, kind, ch, a, b in evs:
            tick = int(round(t * TPS))
            dt = max(0, tick - last); last = max(last, tick)
            if kind == 1: tr.append(mido.Message('note_on', channel=ch, note=a, velocity=b, time=dt))
            elif kind == 0: tr.append(mido.Message('note_off', channel=ch, note=a, velocity=0, time=dt))
            else: tr.append(mido.Message('control_change', channel=ch, control=a, value=b, time=dt))
        tr.append(mido.MetaMessage('end_of_track', time=TPS * 2))
        path = os.path.join(OUT, self.name + '.mid')
        mid.save(path)
        return path

B = 0.5  # one beat at 120 BPM
def grid(t0, t1, step):
    t = t0
    while t < t1 - 1e-6:
        yield round(t, 4)
        t += step

stems = {k: Stem(k) for k in ['pads', 'strings', 'pizz', 'bass', 'drums', 'keys', 'brass', 'hits']}
S = stems
S['pads'].prog(0, 89, 100); S['pads'].prog(1, 91, 70)          # warm pad, choir pad
S['strings'].prog(0, 48, 110); S['strings'].prog(1, 49, 100, 40); S['strings'].prog(2, 44, 100, 90)  # ensemble, slow strings, tremolo
S['pizz'].prog(0, 45, 115, 50); S['pizz'].prog(1, 45, 100, 80)
S['bass'].prog(0, 32, 110); S['bass'].prog(1, 38, 90)          # acoustic bass, synth bass
S['drums'].prog(9, 0, 110)
S['keys'].prog(0, 0, 110); S['keys'].prog(1, 9, 90, 76); S['keys'].prog(2, 8, 90, 50); S['keys'].prog(3, 11, 80)  # piano, glock, celesta, vibes
S['brass'].prog(0, 60, 100); S['brass'].prog(1, 61, 90)        # horn, brass section
S['hits'].prog(0, 48, 127); S['hits'].prog(1, 61, 120); S['hits'].prog(2, 47, 127); S['hits'].prog(9, 0, 127)

# ------------------------------------------------------------------ HOOK ---
# 0.0-6.6  sparse: low pulse on B, warm pad, clock-like woodblock; tremolo riser into "cheating"
S['pads'].note(0, 0.0, 6.0, p('B2'), 70); [S['pads'].note(0, 0.0, 6.0, x, 52) for x in chord('Bm', 3)]
S['pads'].ramp(0, 0.0, 1.0, 11, 40, 110); S['pads'].ramp(0, 5.6, 6.25, 11, 110, 0)
for t in grid(0.0, 6.0, B / 2):
    S['bass'].note(1, t, B / 2 * 0.8, p('B1'), 62 + (14 if (t * 4) % 2 < 0.01 else 0))
for t in grid(0.0, 6.0, B):
    S['drums'].note(9, t, 0.1, 76 if (t * 2) % 2 < 0.01 else 77, 42)
for i, x in enumerate([p('F#4'), p('B4'), p('D5'), p('F#5')]):  # rising string tremolo
    S['strings'].note(2, 3.2 + i * 0.05, 3.0, x, 70)
S['strings'].ramp(2, 3.2, 5.9, 11, 10, 127); S['strings'].ramp(2, 5.95, 6.3, 11, 127, 0)

# --------------------------------------------------------- RISING ACTION ---
# 6.6-22.8 pizzicato ostinato, Bm G D A, two-second bars; layers enter and drop out with the story
prog1 = ['Bm', 'G', 'D', 'A']
t0 = 6.6
for bar in range(8):
    tb = t0 + bar * 2.0
    if tb >= 22.6: break
    c = prog1[bar % 4]
    tones = chord(c, 3)
    pat = [tones[0], tones[2], tones[0] + 12, tones[2], tones[1], tones[2], tones[0] + 12, tones[1] + 12]
    quiet = 13.8 <= tb + 0.01 < 15.1
    for i, t in enumerate(grid(tb, tb + 2.0, B / 2)):
        if t >= 22.75: break
        if 13.8 <= t < 15.1 and i % 2: continue  # "He doesn't say a word": half the notes drop out
        S['pizz'].note(0, t, 0.22, pat[i % 8], 78 + (10 if i % 4 == 0 else 0) - (14 if quiet else 0))
    if tb >= 8.5:  # bass from bar 2
        S['bass'].note(0, tb, 0.95, tones[0] - 12, 84); S['bass'].note(0, tb + 1.0, 0.95, tones[0] - 12 + (7 if bar % 2 else 0), 76)
    if tb >= 10.5:  # snaps/claps + soft kick
        for k, t in enumerate(grid(tb, tb + 2.0, B)):
            if 13.8 <= t < 15.1: continue
            if k % 2 == 1: S['drums'].note(9, t, 0.1, 39, 58)
            if k % 2 == 0: S['drums'].note(9, t, 0.1, 36, 74)
    if tb >= 15.1:  # hats + glock motif
        for t in grid(tb, tb + 2.0, B / 2):
            S['drums'].note(9, t + 0.25 * 0, 0.05, 42, 34 + (10 if int(t * 4) % 2 else 0))
    if tb >= 16.6:  # sustained strings and glockenspiel answer
        for x in chord(c, 4): S['strings'].note(0, tb, 2.0, x, 58)
        mel = {'Bm': ['F#5', 'D5'], 'G': ['G5', 'D5'], 'D': ['A5', 'F#5'], 'A': ['E5', 'C#5']}[c]
        S['keys'].note(1, tb + 1.0, 0.4, p(mel[0]), 70); S['keys'].note(1, tb + 1.5, 0.4, p(mel[1]), 62)
S['strings'].ramp(0, 16.6, 22.7, 11, 70, 120)
# cymbal swell into the slam
S['drums'].note(9, 21.6, 1.6, 49, 30); S['drums'].ramp if False else None

# --------------------------------------------------------------- CONFLICT ---
# 22.8-27.15 staccato low strings in B minor (8ths), timpani on the slam
for i, t in enumerate(grid(22.8, 27.1, B / 2)):
    if 23.35 <= t < 23.7: continue
    c = ['Bm', 'Bm', 'G', 'F#'][int((t - 22.8) // 1.0) % 4]
    S['strings'].note(1, t, 0.18, chord(c, 2)[0], 82 + (16 if i % 4 == 0 else 0))
    S['strings'].note(1, t, 0.18, chord(c, 3)[0], 70)
for t in grid(23.75, 27.0, B):
    S['drums'].note(9, t, 0.1, 45 if int(t * 2) % 2 else 41, 70)
# "You solve it." 27.15: everything stops; a celesta flourish rising
for i, x in enumerate(['B4', 'D5', 'F#5', 'B5', 'D6', 'F#6']):
    S['keys'].note(2, 27.2 + i * 0.09, 0.6, p(x), 74)
S['strings'].note(0, 27.15, 1.2, p('F#6'), 60)
# 28.35-30.25 tension rises again: tremolo cluster + pulse, hit at the stand-up (hits layer)
for x in ['B3', 'C4', 'F#4']: S['strings'].note(2, 28.35, 0.85, p(x), 80)
S['strings'].ramp(2, 28.35, 29.1, 11, 50, 127)
# 30.25-32.05 corridor: low drone, heartbeat pulse (in the SFX), a slow horn
S['pads'].note(1, 30.25, 1.9, p('B2'), 60); S['pads'].note(1, 30.25, 1.9, p('F#3'), 50)
S['brass'].note(0, 30.6, 1.4, p('D4'), 54); S['brass'].note(0, 30.6, 1.4, p('B3'), 50)
# 32.05-42.7 investigation groove: muted pizz on B with a flat-2 (C) colour, synth bass, ticking hats
inv = ['B2', 'B2', 'C3', 'B2', 'F#2', 'B2', 'D3', 'C3']
for i, t in enumerate(grid(32.05, 42.6, B / 2)):
    if 39.6 <= t < 40.45: continue  # "Nothing." - full stop
    S['pizz'].note(1, t, 0.15, p(inv[i % 8]) + 12, 66 + (12 if i % 4 == 0 else 0))
    if i % 2 == 0: S['bass'].note(1, t, 0.4, p(inv[i % 8]) - 12, 70)
    S['drums'].note(9, t, 0.04, 42, 30 + (12 if i % 2 else 0))
    if i % 8 == 4 and t > 35.5: S['drums'].note(9, t, 0.1, 37, 50)
for t, x in [(32.05, 'Bm'), (36.05, 'G'), (40.45, 'Em'), ]:
    for y in chord(x, 3): S['pads'].note(0, t, 3.9 if t < 40 else 2.2, y, 46)
# checklist arpeggio (computer-ish) 40.45-42.7
for i, t in enumerate(grid(40.45, 42.6, B / 4)):
    S['keys'].note(3, t, 0.1, p(['B4', 'D5', 'F#5', 'A5'][i % 4]), 52)

# ------------------------------------------------------------------- DIP ---
# 42.7-51.3 solo piano, B minor, slow and exposed
pn = S['keys']
dip = [(42.75, ['B2', 'F#3'], ['D4', 'F#4'], 'B4'), (44.45, ['G2', 'D3'], ['B3', 'D4'], 'A4'),
       (46.1, ['E2', 'B2'], ['G3', 'B3'], 'G4'), (47.65, ['F#2', 'C#3'], ['A#3', 'C#4'], 'F#4'), (49.2, ['B1', 'F#2'], ['B3', 'D4'], 'F#4')]
for t, lh, rh, mel in dip:
    for x in lh: pn.note(0, t, 1.9, p(x), 58)
    for k, x in enumerate(rh): pn.note(0, t + 0.5 + k * 0.25, 1.3, p(x), 46)
    pn.note(0, t + 1.0, 0.8, p(mel), 60)
S['pads'].note(1, 47.6, 3.0, p('B3'), 40); S['pads'].note(1, 47.6, 3.0, p('C4'), 34)  # whispers: dissonant choir
S['pads'].ramp(1, 47.6, 50.3, 11, 30, 120); S['pads'].ramp(1, 50.3, 50.6, 11, 120, 0)

# --------------------------------------------------------- RISING ACTION ---
# 51.3-64.2 the comeback: horn motif, ostinato builds, clock ticking, riser, dead stop at 64.2
S['brass'].note(0, 51.4, 0.9, p('F#3'), 70); S['brass'].note(0, 52.3, 0.5, p('B3'), 76); S['brass'].note(0, 52.8, 1.4, p('D4'), 82)
for y in chord('Bm', 2): S['strings'].note(1, 51.3, 1.85, y, 70)
prog2 = ['Bm', 'G', 'D', 'A', 'Bm', 'G', 'Em', 'F#']
for bar in range(6):
    tb = 53.15 + bar * 2.0
    if tb >= 64.1: break
    c = prog2[bar % len(prog2)]
    tones = chord(c, 3)
    for i, t in enumerate(grid(tb, min(tb + 2.0, 64.15), B / 2)):
        if 58.85 <= t < 60.0: continue  # clock time-lapse: only the ticks
        S['strings'].note(1, t, 0.2, tones[i % 3] + (12 if i % 4 == 3 else 0), 64 + bar * 5 + (12 if i % 4 == 0 else 0))
    if not (58.85 <= tb < 60.0):
        S['bass'].note(0, tb, 1.9, tones[0] - 12, 80)
    if tb >= 57.5:
        for k, t in enumerate(grid(tb, min(tb + 2.0, 64.15), B)):
            if 58.85 <= t < 60.0: continue
            S['drums'].note(9, t, 0.1, 41 if k % 2 else 43, 66 + bar * 4)
for t in grid(58.85, 60.0, 0.125):  # time-lapse: fast clock ticks in the score too
    S['drums'].note(9, t, 0.05, 76, 48)
# 61.0-64.2: snare roll + tremolo riser, cut dead at 64.2
for t in grid(61.0, 64.2, 0.0625):
    v = 30 + 70 * ((t - 61.0) / 3.2) ** 1.6
    S['drums'].note(9, t, 0.05, 38, v)
for x in ['F#3', 'B3', 'D4', 'F#4', 'A4']: S['strings'].note(2, 61.0, 3.2, p(x), 80)
S['strings'].ramp(2, 61.0, 64.15, 11, 20, 127)

# ----------------------------------------------------------------- PAYOFF ---
# 64.36 the hit (hits stem) sustains as a D major chord until "The room goes silent"
for y in [p('D3'), p('A3'), p('D4'), p('F#4'), p('A4'), p('D5')]:
    S['strings'].note(0, 64.36, 1.45, y, 100)
S['strings'].ramp(0, 64.36, 65.8, 11, 127, 0)
S['brass'].note(1, 64.36, 1.2, p('D3'), 100); S['brass'].note(1, 64.36, 1.2, p('A3'), 96); S['brass'].note(1, 64.36, 1.2, p('F#4'), 96)
S['brass'].ramp(1, 64.4, 65.7, 11, 127, 0)
# 65.8-67.3 silence; a single high harmonic
S['strings'].note(0, 66.3, 1.0, p('A6'), 30)
# 67.3-72.65 warm, emotional: piano + strings, D major I-V-vi-IV
prog3 = [('D', 67.3), ('A', 68.85), ('Bm', 70.6), ('G', 71.65)]
for c, t in prog3:
    dur = {67.3: 1.55, 68.85: 1.75, 70.6: 1.05, 71.65: 1.0}[t]
    for x in chord(c, 3): S['strings'].note(1, t, dur + 0.15, x, 66)
    pn.note(0, t, dur, chord(c, 2)[0], 64)
    for k, x in enumerate(chord(c, 4)): pn.note(0, t + 0.25 + k * 0.18, dur - 0.3, x, 50)
mel3 = [(67.4, 'F#5', 0.7), (68.1, 'E5', 0.6), (68.9, 'E5', 0.5), (69.4, 'C#5', 0.9), (70.6, 'D5', 0.5), (71.1, 'F#5', 0.5), (71.7, 'G5', 0.9)]
for t, x, d in mel3: S['brass'].note(0, t, d, p(x) - 12, 62)
# 72.65-75.85 uplifting: full strings, light percussion, glock
for bar, (c, t) in enumerate([('D', 72.65), ('A', 73.45), ('Bm', 74.25), ('G', 75.05)]):
    for x in chord(c, 3) + [chord(c, 4)[0]]: S['strings'].note(0, t, 0.85, x, 74 + bar * 3)
    S['bass'].note(0, t, 0.8, chord(c, 2)[0] - 12, 84)
    for k, tt in enumerate(grid(t, t + 0.8, B / 2)):
        S['drums'].note(9, tt, 0.05, 42, 40);
        if k == 0: S['drums'].note(9, tt, 0.1, 36, 70)
    S['keys'].note(1, t + 0.4, 0.3, chord(c, 5)[2], 60)
# 75.85-80.4 playful pizzicato button
play = ['D', 'A', 'Bm', 'G', 'D', 'A']
for bar in range(6):
    tb = 75.85 + bar * 0.8
    if tb >= 79.9: break
    c = play[bar]
    tones = chord(c, 3)
    for i, t in enumerate(grid(tb, tb + 0.8, B / 2)):
        S['pizz'].note(0, t, 0.18, [tones[0], tones[2], tones[1] + 12, tones[2]][i % 4], 84)
    S['bass'].note(0, tb, 0.4, tones[0] - 12, 82)
    S['keys'].note(1, tb + 0.25, 0.25, chord(c, 5)[1], 52)
# "...can copy you." button: pizz + glock "ta-da" landing on D
for x in ['D3', 'A3', 'D4', 'F#4']: S['pizz'].note(0, 80.0, 0.6, p(x), 100)
S['keys'].note(1, 80.0, 0.9, p('D6'), 84); S['keys'].note(1, 79.85, 0.15, p('A5'), 70)
S['drums'].note(9, 80.0, 0.3, 49, 50)

# ------------------------------------------------------------------- HITS ---
def hit(t, ch_name='Bm', big=1.0, timp=True):
    for x in chord(ch_name, 2) + chord(ch_name, 3) + [chord(ch_name, 4)[0]]:
        S['hits'].note(0, t, 0.35 * big + 0.2, x, 110 * big)
        S['hits'].note(1, t, 0.3 * big + 0.15, x + 12, 100 * big)
    if timp:
        S['hits'].note(2, t, 0.6, chord(ch_name, 2)[0], 120 * big); S['hits'].note(2, t + 0.0, 0.6, chord(ch_name, 2)[0] - 12, 110 * big)
    S['hits'].note(9, t, 0.5, 49, 90 * big); S['hits'].note(9, t, 0.2, 36, 120 * big)
hit(6.25, 'Bm', 0.55)        # "...of cheating."
hit(23.42, 'Bm', 0.85)       # exam stack slam
hit(29.15, 'F#', 0.75)       # the teacher shoots up
hit(46.94, 'Em', 0.6, False) # CANCELLED
hit(50.32, 'Bm', 0.8)        # "Cheater."
hit(64.36, 'D', 1.0)         # "One hundred."

paths = {k: v.save() for k, v in S.items()}
for k, mp in paths.items():
    wav = os.path.join(OUT, k + '.wav')
    subprocess.run(['fluidsynth', '-ni', '-q', '-F', wav, '-r', '48000', '-g', '0.5', '-R', '1', '-C', '0', SF, mp], check=True)
    print('rendered', wav)
