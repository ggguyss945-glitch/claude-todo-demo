#!/usr/bin/env python3
"""Original score for "Too Much Gold", written note by note against the narration
timeline (script/vo_lines.json) and rendered with FluidSynth (MuseScore General).

Comedy-history bed in the style of the reference shorts: an orchestral hit on the first
word, a bouncy pizzicato ostinato in D "hijaz" (D Eb F# G A Bb C) with kalimba, frame drum
and an oboe answer for Cairo and the caravan, a dead stop on "Except,", a tiptoe bassoon
groove for the prices, a drone on the question, a shimmer for rarity, a sad oboe for
"twelve years later", a riser into "the best part", an overconfident fanfare for "the
richest king on Earth", silence for "runs out of money", a sheepish pluck for "Remember
me?", and the hook theme again at the end so the short loops.
    python3 music.py <outdir>
"""
import os, sys, subprocess
import mido

SF = '/usr/share/sounds/sf3/MuseScore_General_Full.sf3'
TPS = 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else 'music_out'
os.makedirs(OUT, exist_ok=True)
N = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
N.update({'Eb': 3, 'Bb': 10, 'Ab': 8, 'Db': 1, 'Gb': 6})
def p(name):
    nm, octv = name[:-1], int(name[-1])
    return 12 * (octv + 1) + N[nm]

class Stem:
    def __init__(self, name): self.name, self.ev, self.progs = name, [], {}
    def prog(self, ch, program, vol=100, pan=64, bank=0): self.progs[ch] = (program, vol, pan, bank)
    def note(self, ch, t, dur, pitch, vel=80):
        if dur <= 0: return
        self.ev.append((t, 1, ch, pitch, max(1, min(127, int(vel))))); self.ev.append((t + dur, 0, ch, pitch, 0))
    def cc(self, ch, t, num, val): self.ev.append((t, 2, ch, num, int(max(0, min(127, val)))))
    def ramp(self, ch, t0, t1, num, v0, v1, steps=24):
        for i in range(steps + 1): k = i / steps; self.cc(ch, t0 + (t1 - t0) * k, num, v0 + (v1 - v0) * k)
    def bend(self, ch, t, v): self.ev.append((t, 3, ch, int(v), 0))
    def save(self):
        mid = mido.MidiFile(ticks_per_beat=960); tr = mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        for ch, (prg, vol, pan, bank) in self.progs.items():
            if ch != 9:
                tr.append(mido.Message('control_change', channel=ch, control=0, value=bank, time=0))
                tr.append(mido.Message('program_change', channel=ch, program=prg, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=7, value=vol, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=10, value=pan, time=0))
            tr.append(mido.Message('control_change', channel=ch, control=11, value=127, time=0))
        last = 0
        for t, kind, ch, a, b in sorted(self.ev, key=lambda e: (e[0], e[1])):
            tick = int(round(t * TPS)); dt = max(0, tick - last); last = max(last, tick)
            if kind == 1: tr.append(mido.Message('note_on', channel=ch, note=a, velocity=b, time=dt))
            elif kind == 0: tr.append(mido.Message('note_off', channel=ch, note=a, velocity=0, time=dt))
            elif kind == 2: tr.append(mido.Message('control_change', channel=ch, control=a, value=b, time=dt))
            else: tr.append(mido.Message('pitchwheel', channel=ch, pitch=a, time=dt))
        tr.append(mido.MetaMessage('end_of_track', time=TPS * 2))
        path = os.path.join(OUT, self.name + '.mid'); mid.save(path); return path

def grid(t0, t1, step):
    t = t0
    while t < t1 - 1e-6:
        yield round(t, 4); t += step

S = {k: Stem(k) for k in ['pizz', 'world', 'bass', 'drums', 'keys', 'winds', 'strings', 'brass', 'pads', 'hits']}
S['pizz'].prog(0, 45, 115, 52); S['pizz'].prog(1, 45, 100, 76)
S['world'].prog(0, 108, 110, 70); S['world'].prog(1, 104, 90, 44); S['world'].prog(2, 46, 100, 64)   # kalimba, sitar (oud colour), harp
S['bass'].prog(0, 32, 112); S['bass'].prog(1, 58, 96)                                               # acoustic bass, tuba
S['drums'].prog(9, 0, 110)
S['keys'].prog(0, 9, 100, 80); S['keys'].prog(1, 8, 92, 48); S['keys'].prog(2, 13, 90, 64)          # glock, celesta, xylophone
S['winds'].prog(0, 68, 104, 60); S['winds'].prog(1, 70, 104, 70); S['winds'].prog(2, 71, 92, 54)    # oboe, bassoon, clarinet
S['strings'].prog(0, 48, 110); S['strings'].prog(1, 44, 100, 64); S['strings'].prog(2, 49, 96)      # ensemble, tremolo, slow
S['brass'].prog(0, 61, 104); S['brass'].prog(1, 56, 96, 70); S['brass'].prog(2, 57, 92)             # brass section, trumpet, trombone
S['pads'].prog(0, 89, 92); S['pads'].prog(1, 91, 76)
S['hits'].prog(0, 48, 127); S['hits'].prog(1, 61, 122); S['hits'].prog(2, 47, 127); S['hits'].prog(9, 0, 127)

B = 0.5        # one beat at 120 BPM; the cut points in the script are on (or nudged to) this grid
HIJAZ = {'Dm': ['D', 'A', 'F'], 'D': ['D', 'A', 'F#'], 'Eb': ['Eb', 'Bb', 'G'], 'Gm': ['G', 'D', 'Bb'], 'Cm': ['C', 'G', 'Eb'], 'A7': ['A', 'E', 'C#'], 'Bb': ['Bb', 'F', 'D']}
def tones(c, o=3): return [p(x + str(o)) for x in HIJAZ[c]]

def ostinato(t0, t1, prog, vel=80, ch=0, stem='pizz', skip=None, accent=True):
    """the hook figure: root-fifth-octave bounce with a hijaz turn on beat 4"""
    for bar, tb in enumerate(grid(t0, t1, 2.0)):
        c = prog[bar % len(prog)]; r, f, th = tones(c, 3)
        pat = [r, f, r + 12, f, th, f, r + 12, (r + 13 if c in ('D', 'Dm') else th + 12)]
        for i, t in enumerate(grid(tb, min(tb + 2.0, t1), B / 2)):
            if skip and skip(t): continue
            S[stem].note(ch, t, 0.2, pat[i % 8], vel + (12 if accent and i % 4 == 0 else 0))
def frame_drum(t0, t1, vel=70, busy=1):
    for i, t in enumerate(grid(t0, t1, B / 2)):
        k = i % 8
        if k in (0, 3, 6): S['drums'].note(9, t, 0.08, 64 if k == 0 else 63, vel + (10 if k == 0 else 0))   # low/open conga (doum)
        if busy and k in (2, 5, 7): S['drums'].note(9, t, 0.05, 62, vel - 18)                              # muted conga (tek)
        if busy > 1: S['drums'].note(9, t, 0.04, 54, vel - 34)                                             # tambourine shimmer

# --------------------------------------------------------------------- HOOK 0.0 - 3.3
# the first word lands on an orchestral hit (hits stem); the ostinato kicks in straight away
ostinato(0.05, 3.3, ['Dm', 'Eb'], 84)
frame_drum(0.05, 3.3, 72, 2)
for t, x in [(0.55, 'A5'), (0.8, 'D6'), (1.05, 'F#6'), (1.3, 'A6')]: S['keys'].note(0, t, 0.3, p(x), 72)   # coin sparkles
S['bass'].note(0, 0.05, 0.9, p('D2'), 96); S['bass'].note(0, 1.05, 0.45, p('A1'), 88)
# "that gold became worthless": a deflating tuba slide (1.6 - 3.2)
for t, x in [(1.62, 'A2'), (2.0, 'G2'), (2.38, 'F#2'), (2.76, 'Eb2')]: S['bass'].note(1, t, 0.34, p(x), 92)
S['bass'].note(1, 3.0, 0.3, p('D2'), 96)

# ------------------------------------------------------- CARAVAN 3.3 - 10.1 (desert, hijaz)
ostinato(3.3, 10.1, ['Dm', 'Eb', 'Dm', 'Cm'], 72, stem='world', ch=0)          # kalimba carries the figure
frame_drum(3.3, 10.1, 70, 1)
for bar, tb in enumerate(grid(3.3, 10.1, 2.0)):
    c = ['Dm', 'Eb', 'Dm', 'Cm'][bar % 4]
    S['bass'].note(0, tb, 0.9, tones(c, 2)[0], 88); S['bass'].note(0, tb + 1.0, 0.9, tones(c, 2)[1] - 12, 80)
    for x in tones(c, 3): S['pads'].note(0, tb, 2.0, x, 46)
# the oboe sings a hijaz phrase over the caravan (sixty thousand people...)
mel = [(4.3, 'D5', 0.5), (4.8, 'Eb5', 0.25), (5.05, 'F#5', 0.25), (5.3, 'G5', 0.75), (6.05, 'F#5', 0.25), (6.3, 'Eb5', 0.25), (6.55, 'D5', 0.75),
       (7.3, 'A5', 0.5), (7.8, 'Bb5', 0.25), (8.05, 'A5', 0.25), (8.3, 'G5', 0.5), (8.8, 'F#5', 0.5), (9.3, 'Eb5', 0.3), (9.6, 'D5', 0.5)]
for t, x, d in mel: S['winds'].note(0, t, d, p(x), 80)
S['world'].note(1, 3.3, 0.6, p('D3'), 70); S['world'].note(1, 7.3, 0.6, p('A3'), 66)   # sitar drones on the downbeats
for i, x in enumerate(['D5', 'F#5', 'A5', 'D6', 'F#6', 'A6']): S['world'].note(2, 3.3 + i * 0.05, 1.2, p(x), 60)  # harp gliss on the dissolve

# ---------------------------------------------- GIVING 10.1 - 17.6 (build: everyone gets gold)
ostinato(10.1, 17.6, ['Dm', 'Eb', 'Gm', 'A7'], 80)
frame_drum(10.1, 17.6, 74, 2)
for bar, tb in enumerate(grid(10.1, 17.6, 2.0)):
    c = ['Dm', 'Eb', 'Gm', 'A7'][bar % 4]
    S['bass'].note(0, tb, 0.9, tones(c, 2)[0], 92); S['bass'].note(0, tb + 1.0, 0.9, tones(c, 2)[0] + 7, 84)
    if tb >= 12.1:
        for x in tones(c, 4): S['strings'].note(0, tb, 2.0, x, 54 + bar * 4)
S['strings'].ramp(0, 12.1, 17.5, 11, 70, 120)
# the list: a glock "ding" and pizz stab on each word
for t, x in [(13.86, 'D6'), (14.63, 'F#6'), (15.32, 'A6'), (16.01, 'D7')]:
    S['keys'].note(0, t, 0.35, p(x), 92); S['pizz'].note(1, t, 0.25, p(x) - 24, 100)
# camel guy: a dopey tuba blat
S['bass'].note(1, 16.95, 0.25, p('D2'), 100); S['bass'].note(1, 17.2, 0.3, p('A1'), 96)

# ---------------------------------------- DROWNING IN GOLD 17.6 - 19.66 (peak, then dead stop)
for t in grid(17.58, 19.62, B / 2):
    c = 'D' if t < 18.6 else 'Bb'
    for x in tones(c, 3): S['strings'].note(0, t, 0.22, x, 92)
    S['drums'].note(9, t, 0.05, 54, 70)
for x in ['D3', 'A3', 'D4', 'F#4', 'A4']: S['brass'].note(0, 17.58, 1.0, p(x), 100)
for x in ['Bb2', 'F3', 'Bb3', 'D4', 'F4']: S['brass'].note(0, 18.6, 1.0, p(x), 104)
S['brass'].note(1, 18.6, 0.9, p('A5'), 96)
for k, t in enumerate(grid(17.58, 19.6, B)): S['drums'].note(9, t, 0.1, 36, 100); S['drums'].note(9, t + B / 2, 0.1, 38, 80 + k * 3)
S['drums'].note(9, 17.58, 1.5, 49, 90)
for i, x in enumerate(['D5', 'F#5', 'A5', 'D6', 'F#6', 'A6', 'D7']): S['keys'].note(1, 18.9 + i * 0.07, 0.4, p(x), 80)

# ------------------------------------------- EXCEPT 19.7 - 28.98 (tiptoe: prices go up)
# "Except," (record scratch in the SFX) -> 0.35 s of nothing -> sneaky bassoon + pizz
tip = ['D3', 'F3', 'A3', 'F3', 'Eb3', 'F#3', 'A3', 'F#3']
for i, t in enumerate(grid(20.05, 28.9, B / 2)):
    if 23.45 <= t < 23.95: continue                     # the shrug gets its own two notes
    if 24.1 <= t < 25.95 and i % 2: continue            # thin out under the baker's line
    S['pizz'].note(1, t, 0.14, p(tip[i % 8]), 66 + (12 if i % 4 == 0 else 0))
    if i % 2 == 0: S['bass'].note(0, t, 0.35, p(tip[i % 8]) - 12, 72)
    S['drums'].note(9, t, 0.03, 42, 26 + (10 if i % 2 else 0))
bsn = [(20.1, 'D3', 0.25), (20.6, 'F3', 0.25), (21.1, 'A3', 0.25), (21.35, 'Bb3', 0.6),          # "...asking for more gold,"
       (22.1, 'A3', 0.25), (22.35, 'F#3', 0.25), (22.6, 'Eb3', 0.4)]                               # "for the same bread"
for t, x, d in bsn: S['winds'].note(1, t, d, p(x), 84)
S['keys'].note(2, 21.4, 0.2, p('A5'), 80); S['keys'].note(2, 21.6, 0.2, p('D6'), 84)               # the price jumps 1 -> 3
S['winds'].note(1, 23.5, 0.18, p('A3'), 86); S['winds'].note(1, 23.72, 0.3, p('D3'), 82)           # the shrug: "hm-hm"
S['keys'].note(2, 24.15, 0.15, p('D6'), 70)
for k, (t, x) in enumerate([(27.15, 'A3'), (27.45, 'Ab3'), (27.75, 'G3'), (28.05, 'F#3')]):         # less and less silver
    S['winds'].note(1, t, 0.26, p(x), 86 - k * 4)
S['bass'].note(1, 28.4, 0.5, p('D2'), 90)

# ---------------------------------------------- THE QUESTION 28.98 - 31.6 (drone, suspense)
for x in ['D2', 'A2']: S['pads'].note(1, 29.0, 2.6, p(x), 62)
for x in ['D4', 'Eb4']: S['strings'].note(1, 29.0, 2.5, p(x), 70)
S['strings'].ramp(1, 29.0, 31.4, 11, 40, 110); S['strings'].ramp(1, 31.42, 31.58, 11, 110, 0)
S['pizz'].note(0, 31.32, 0.3, p('A4'), 96); S['pizz'].note(0, 31.32, 0.3, p('Eb5'), 90)             # "...money?" question pluck

# ---------------------------------------- RARITY 31.6 - 33.84 (shimmer: one coin on a pedestal)
for x in ['D4', 'A4', 'D5', 'F#5']: S['pads'].note(0, 31.6, 2.3, p(x), 50)
for k, (t, x) in enumerate([(31.75, 'A6'), (32.25, 'F#6'), (32.75, 'D6'), (33.25, 'A5')]): S['keys'].note(1, t, 0.6, p(x), 70 - k * 4)
for t in grid(31.6, 33.8, B): S['world'].note(0, t, 0.3, p('D5'), 46)

# ------------------------------------------- FLOOD 33.84 - 35.86 (swell, coins pour in)
for i, t in enumerate(grid(33.84, 35.8, B / 4)):
    S['world'].note(2, t, 0.3, p(['D4', 'F#4', 'A4', 'D5', 'F#5', 'A5', 'D6', 'Eb6'][i % 8]) + (12 if i > 16 else 0), 60 + i)
for x in ['D3', 'A3', 'D4', 'F#4', 'A4']: S['strings'].note(1, 33.84, 1.95, p(x), 84)
S['strings'].ramp(1, 33.84, 35.6, 11, 30, 127); S['strings'].ramp(1, 35.62, 35.85, 11, 127, 0)
S['drums'].note(9, 34.6, 1.2, 49, 40)

# --------------------------------------- TWELVE YEARS LATER 35.86 - 38.6 (sad, a bit comic)
for t, c in [(35.9, 'Dm'), (37.3, 'Gm')]:
    for x in tones(c, 3): S['strings'].note(2, t, 1.4, x, 60)
sad = [(36.0, 'A4', 0.6), (36.6, 'G4', 0.3), (36.9, 'F4', 0.6), (37.5, 'Eb4', 0.4), (37.9, 'D4', 0.65)]
for t, x, d in sad: S['winds'].note(0, t, d, p(x), 74)
S['bass'].note(1, 38.25, 0.3, p('D2'), 70)

# -------------------------------------- THE BEST PART 38.62 - 39.94 (riser into the reveal)
for t in grid(38.62, 39.9, 0.0625): S['drums'].note(9, t, 0.05, 38, 30 + 80 * ((t - 38.62) / 1.28) ** 1.5)
for x in ['A3', 'D4', 'F#4', 'A4']: S['strings'].note(1, 38.62, 1.3, p(x), 84)
S['strings'].ramp(1, 38.62, 39.9, 11, 20, 127)
for i, t in enumerate(grid(38.62, 39.9, B / 2)): S['pizz'].note(0, t, 0.15, p('A3') + i, 76 + i * 3)

# -------------------------- THE RICHEST KING ON EARTH 39.94 - 41.9 (overconfident fanfare)
fan = [(39.95, ['D4', 'F#4', 'A4'], 0.35), (40.35, ['D4', 'F#4', 'A4'], 0.15), (40.55, ['D4', 'F#4', 'A4'], 0.15),
       (40.75, ['G4', 'B4', 'D5'], 0.45), (41.25, ['A4', 'C#5', 'E5'], 0.6)]
for t, xs, d in fan:
    for x in xs: S['brass'].note(0, t, d, p(x), 104)
    S['brass'].note(1, t, d, p(xs[-1]) + 12, 96)
for t in grid(39.95, 41.85, B): S['drums'].note(9, t, 0.1, 47, 80)
S['bass'].note(0, 39.95, 0.8, p('D2'), 100); S['bass'].note(0, 40.75, 0.4, p('G1'), 96); S['bass'].note(0, 41.25, 0.6, p('A1'), 100)
S['drums'].note(9, 39.95, 1.2, 49, 70)
# ... "runs out of money." (41.89): everything stops dead at 41.9; only the moth (SFX) and one sad low note
S['bass'].note(1, 42.55, 0.9, p('D1') + 12, 80)

# ------------------------------------------ BACK TO THE MERCHANTS 43.2 - 45.75 (sheepish walk)
walkb = ['D3', 'A2', 'Bb2', 'A2']
for i, t in enumerate(grid(43.25, 45.7, B)):
    S['bass'].note(0, t, 0.4, p(walkb[i % 4]), 82)
    S['pizz'].note(1, t + B / 2, 0.12, p(['F4', 'Eb4', 'D4', 'Eb4'][i % 4]), 66)
    S['drums'].note(9, t, 0.03, 42, 30)
for t, x in [(43.6, 'D4'), (44.1, 'F4'), (44.6, 'A4'), (45.1, 'G4'), (45.35, 'F#4')]: S['winds'].note(2, t, 0.3, p(x), 70)
# "Hey. Remember me?" — a single sheepish pluck figure, then a hopeful glock
S['pizz'].note(0, 45.78, 0.2, p('A3'), 84); S['pizz'].note(0, 46.25, 0.2, p('Bb3'), 80); S['pizz'].note(0, 46.55, 0.3, p('A3'), 76)
S['keys'].note(0, 46.85, 0.4, p('A5'), 64)

# ------------------------------------------------ THEY LEND IT 47.08 - 48.3 (light, cheeky)
for i, t in enumerate(grid(47.1, 48.28, B / 2)): S['pizz'].note(0, t, 0.18, p(['D4', 'F#4', 'A4', 'F#4'][i % 4]), 76)
S['keys'].note(2, 47.72, 0.2, p('D6'), 84); S['keys'].note(2, 47.85, 0.3, p('A6'), 80)              # pouch changes hands

# ------------------------------ THEY'RE THE ONES WITH ALL THE GOLD 48.3 - 51.0 (hook theme: loop)
ostinato(48.3, 51.0, ['Dm', 'Eb'], 86)
frame_drum(48.3, 51.0, 76, 2)
for tb, c in [(48.3, 'Dm'), (50.3, 'Eb')]:
    S['bass'].note(0, tb, 0.9, tones(c, 2)[0], 96)
    for x in tones(c, 4): S['strings'].note(0, tb, 2.0, x, 70)
S['strings'].ramp(0, 48.3, 50.9, 11, 80, 120)
for i, t in enumerate(grid(49.3, 50.3, B / 2)): S['keys'].note(0, t, 0.25, p(['D6', 'F#6', 'A6', 'D7'][i % 4]), 70 + i * 3)
# pickup into the loop: the last beat leads back into the opening hit
S['drums'].note(9, 50.55, 0.05, 38, 70); S['drums'].note(9, 50.8, 0.05, 38, 90)

# ------------------------------------------------------------------------- HITS
def hit(t, chord, big=1.0, timp=True, cym=True):
    xs = [p(x) for x in chord]
    for x in xs:
        S['hits'].note(0, t, 0.35 * big + 0.2, x, 110 * big); S['hits'].note(1, t, 0.3 * big + 0.15, x + 12, 100 * big)
    if timp: S['hits'].note(2, t, 0.6, xs[0], 120 * big); S['hits'].note(2, t, 0.6, xs[0] - 12, 110 * big)
    if cym: S['hits'].note(9, t, 0.5, 49, 90 * big)
    S['hits'].note(9, t, 0.2, 36, 120 * big)
hit(0.0, ['D2', 'A2', 'D3', 'F3', 'A3', 'D4'], 1.0)          # "He gave away..."
hit(17.58, ['D2', 'A2', 'D3', 'F#3', 'A3'], 0.8)             # "Suddenly, Cairo..."
hit(33.84, ['D2', 'A2', 'D3', 'F#3'], 0.5, True, False)      # the flood begins
hit(39.94, ['D2', 'A2', 'D3', 'F#3', 'A3'], 0.85)            # the camp reveal

paths = {k: v.save() for k, v in S.items()}
for k, mp in paths.items():
    wav = os.path.join(OUT, k + '.wav')
    subprocess.run(['fluidsynth', '-ni', '-q', '-F', wav, '-r', '48000', '-g', '0.5', '-R', '1', '-C', '0', SF, mp], check=True)
    print('rendered', wav)
