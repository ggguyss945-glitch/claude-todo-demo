# Score for the 60 s test, played on GeneralUser GS through TinySoundFont.
# Each cue is a list of notes; expression ramps (CC11) shape swells.
import numpy as np, tinysoundfont

SR = 48000
GM = dict(piano=0, cello=42, contrabass=43, tremolo=44, pizz=45, timpani=47, strings=48, slow_strings=49,
          choir=52, bassoon=70, warm_pad=89, glass=92, halo=94)

class Score:
    def __init__(self, sf2, dur):
        self.sf2, self.dur = sf2, dur
        self.notes = []      # (t, dur, chan, key, vel)
        self.cc = []         # (t, chan, ctrl, val)
        self.prog = {}       # chan -> program
    def inst(self, chan, name): self.prog[chan] = GM[name]; return chan
    def note(self, t, d, chan, key, vel=80): self.notes.append((t, d, chan, key, vel))
    def chord(self, t, d, chan, keys, vel=70):
        for k in keys: self.note(t, d, chan, k, vel)
    def ramp(self, chan, t0, t1, v0, v1, ctrl=11, steps=None):
        steps = steps or max(2, int((t1 - t0) * 25))
        for i in range(steps + 1):
            self.cc.append((t0 + (t1 - t0) * i / steps, chan, ctrl, int(round(v0 + (v1 - v0) * i / steps))))
    def render(self):
        syn = tinysoundfont.Synth(samplerate=SR, gain=-6)
        sfid = syn.sfload(self.sf2)
        for ch, p in self.prog.items():
            syn.program_select(ch, sfid, 0, p)
            syn.control_change(ch, 91, 0); syn.control_change(ch, 93, 0)
        ev = [(t, 0, ch, k, v) for t, d, ch, k, v in self.notes] + [(t + d, 1, ch, k, 0) for t, d, ch, k, v in self.notes]
        ev += [(t, 2, ch, c, v) for t, ch, c, v in self.cc]
        ev.sort(key=lambda e: (e[0], e[1]))
        n = int(self.dur * SR); out = np.zeros((n, 2), np.float32); pos = 0; i = 0
        while pos < n:
            nxt = int(ev[i][0] * SR) if i < len(ev) else n
            nxt = min(max(nxt, pos), n)
            if nxt > pos:
                buf = np.frombuffer(syn.generate(nxt - pos), dtype=np.float32).reshape(-1, 2)
                out[pos:pos + len(buf)] = buf; pos = nxt
            while i < len(ev) and int(ev[i][0] * SR) <= pos:
                t, kind, ch, a, b = ev[i]
                if kind == 0: syn.noteon(ch, a, b)
                elif kind == 1: syn.noteoff(ch, a)
                else: syn.control_change(ch, a, b)
                i += 1
            if i >= len(ev) and pos < n:
                buf = np.frombuffer(syn.generate(n - pos), dtype=np.float32).reshape(-1, 2); out[pos:] = buf[:n - pos]; pos = n
        return out

# MIDI helpers
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}
NOTE.update({'Db': 1, 'D#': 3, 'Gb': 6, 'G#': 8, 'A#': 10})
def m(s):  # 'D2' -> 38
    name, octv = s[:-1], int(s[-1]); return 12 * (octv + 1) + NOTE[name]
def ms(*xs): return [m(x) for x in xs]

def build(sf2, T):
    """T = timeline events + shot times. Returns dict of stems."""
    E = T['events']; sh = {s['name']: s for s in T['shots']}; dur = T['dur']
    stems = {}

    # ---- M1 dread: 9.55 -> 17.67 ----
    sc = Score(sf2, dur)
    cb, ce, tr, ha = sc.inst(0, 'contrabass'), sc.inst(1, 'cello'), sc.inst(2, 'tremolo'), sc.inst(3, 'halo')
    a, b = sh['aisle_frozen']['start'], sh['exterior']['start']
    sc.ramp(cb, a, a + 0.1, 0, 0); sc.ramp(cb, a, E['boom_where'], 50, 112); sc.ramp(cb, E['boom_where'], b + 0.6, 112, 70)
    sc.note(a, b - a + 0.8, cb, m('D1'), 95); sc.note(a, b - a + 0.8, cb, m('D2'), 80)
    sc.ramp(ce, a, a + 2.5, 30, 90); sc.note(a + 0.9, b - a, ce, m('A2'), 70); sc.note(a + 2.6, b - a - 1.7, ce, m('D3'), 60)
    t0 = sh['zombies_turn']['start']
    sc.ramp(tr, t0, E['boom_where'] - 0.05, 15, 118); sc.ramp(tr, E['boom_where'], E['boom_where'] + 0.05, 118, 0)
    sc.chord(t0, E['boom_where'] - t0, tr, ms('D4', 'Eb4', 'A4', 'Bb4'), 70)
    sc.ramp(ha, a, a + 3, 20, 70); sc.chord(a, b - a + 0.5, ha, ms('D3', 'A3', 'D4'), 50)
    stems['dread'] = sc.render()

    # ---- M2 pulse: exterior + shutter (96 bpm, 8ths) ----
    sc = Score(sf2, dur)
    ce, cb, st_, tp = sc.inst(0, 'cello'), sc.inst(1, 'contrabass'), sc.inst(2, 'strings'), sc.inst(3, 'timpani')
    start, end = sh['exterior']['start'], sh['gary']['start'] + 0.15
    q8 = 60 / 96 / 2; bar = q8 * 8
    prog = [('D2', ms('D3', 'A2', 'D3', 'F3', 'D3', 'A2', 'C3', 'D3'), ms('D4', 'F4', 'A4')),
            ('Bb1', ms('D3', 'Bb2', 'D3', 'F3', 'D3', 'Bb2', 'C3', 'D3'), ms('Bb3', 'D4', 'F4')),
            ('G1', ms('D3', 'G2', 'Bb2', 'D3', 'G3', 'D3', 'Bb2', 'D3'), ms('G3', 'Bb3', 'D4')),
            ('A1', ms('C#3', 'A2', 'C#3', 'E3', 'A3', 'E3', 'C#3', 'A2'), ms('A3', 'C#4', 'E4'))]
    sc.ramp(ce, start, start + bar, 55, 92); sc.ramp(st_, start, start + 2 * bar, 20, 62)
    sc.ramp(ce, end - 0.8, end + 0.3, 92, 0); sc.ramp(st_, end - 0.8, end + 0.3, 62, 0)
    t = start; bi = 0
    while t < end:
        root, eighths, chord = prog[bi % 4]
        sc.note(t, bar * 0.98, cb, m(root), 82)
        for j, k in enumerate(eighths):
            if t + j * q8 < end: sc.note(t + j * q8, q8 * 0.42, ce, k, 92 if j in (0, 4) else 70)
        sc.chord(t, bar * 0.99, st_, chord, 58)
        sc.note(t, 0.6, tp, m('D2') if bi % 2 == 0 else m('A1'), 70)
        t += bar; bi += 1
    stems['pulse'] = sc.render()

    # ---- M3 humor: Gary ----
    sc = Score(sf2, dur)
    pz, bs = sc.inst(0, 'pizz'), sc.inst(1, 'bassoon')
    g0 = sh['gary']['start'] + 0.25
    for j, k in enumerate(ms('D3', 'F3', 'A3', 'F3', 'D3', 'E3')):
        tt = g0 + j * 0.47
        if tt < E['gary_silence'] - 0.1: sc.note(tt, 0.3, pz, k, 58)
    sc.note(E['pizz_sting'], 0.25, pz, m('A4'), 96); sc.note(E['pizz_sting'] + 0.24, 0.4, pz, m('D3'), 100)
    sc.ramp(bs, E['pizz_sting'] + 0.2, E['pizz_sting'] + 0.25, 70, 70)
    sc.note(E['pizz_sting'] + 0.24, 0.42, bs, m('D2'), 62)
    stems['humor'] = sc.render()

    # ---- M4 calm: counting + inventory (70 bpm piano, warm pad) ----
    sc = Score(sf2, dur)
    pn, pd = sc.inst(0, 'piano'), sc.inst(1, 'warm_pad')
    c0 = sh['counting']['start'] + 0.15; beat = 60 / 70; seg = 2 * beat
    sc.cc.append((c0 - 0.05, pn, 64, 127))
    chords = [('F2', ms('C3', 'A3', 'F4', 'A4')), ('E2', ms('C3', 'G3', 'E4', 'G4')), ('D2', ms('A2', 'F3', 'D4', 'F4')),
              ('Bb1', ms('F2', 'D3', 'Bb3', 'D4')), ('F2', ms('C3', 'A3', 'F4', 'C5')), ('E2', ms('C3', 'G3', 'E4', 'G4'))]
    t = c0; ci = 0
    while t < E['problem_hit'] - 0.15 and ci < len(chords):
        bass, up = chords[ci]
        sc.note(t, seg * 1.6, pn, m(bass), 52)
        for j, k in enumerate(up): sc.note(t + (j + 1) * beat / 2, seg, pn, k, 40 + 6 * (j == len(up) - 1))
        sc.chord(t, seg * 1.05, pd, [m(bass) + 12] + up[:2], 36)
        t += seg; ci += 1
    # "Food is not the problem." -> borrowed minor iv, held
    pr = E['problem_hit']
    sc.cc.append((pr - 0.02, pn, 64, 0)); sc.cc.append((pr, pn, 64, 127))
    sc.note(pr, 2.6, pn, m('Bb1'), 60); sc.chord(pr + 0.02, 2.6, pn, ms('F2', 'Db3', 'Bb3', 'Db4'), 50)
    sc.ramp(pd, pr, pr + 0.4, 100, 100); sc.chord(pr, 2.3, pd, ms('Bb2', 'Db3', 'F3'), 40)
    sc.ramp(pd, sh['rule']['start'] - 0.4, sh['rule']['start'] + 0.2, 100, 0); sc.ramp(pn, sh['rule']['start'] - 0.3, sh['rule']['start'] + 0.3, 127, 0)
    stems['calm'] = sc.render()

    # ---- M5 tension: rule -> alarm -> title ----
    sc = Score(sf2, dur)
    cb, tr, sx, tp, gl = sc.inst(0, 'contrabass'), sc.inst(1, 'tremolo'), sc.inst(2, 'strings'), sc.inst(3, 'timpani'), sc.inst(4, 'glass')
    r0, title = sh['rule']['start'], E['title']
    sc.ramp(cb, r0, r0 + 2, 40, 95); sc.note(r0 + 0.05, title - r0, cb, m('D1'), 90); sc.note(r0 + 0.05, title - r0, cb, m('D2'), 70)
    a0 = sh['aisle_alarm']['start']
    sc.ramp(tr, a0, E['ring'], 10, 85); sc.chord(a0, E['ring'] - a0 + 0.1, tr, ms('D3', 'A3', 'Eb4'), 70)
    sc.ramp(tr, E['ring'], title - 0.05, 85, 127); sc.chord(E['ring'], title - E['ring'], tr, ms('D4', 'Eb4', 'A4', 'Bb4', 'D5'), 80)
    sc.chord(E['ring'], 0.7, sx, ms('C3', 'Db3', 'D3', 'G3', 'Ab3'), 122)
    t = E['ring'] + 0.6; k = 0
    while t < title - 0.05:  # timpani roll crescendo
        sc.note(t, 0.12, tp, m('D2'), int(40 + 80 * (t - E['ring']) / (title - E['ring']))); t += 0.11 - 0.04 * (t - E['ring']) / (title - E['ring']); k += 1
    sc.ramp(gl, a0, a0 + 2, 20, 70); sc.note(a0, title - a0, gl, m('D6'), 40)
    stems['tension'] = sc.render()

    # ---- M6 title hit ----
    sc = Score(sf2, dur)
    tp, cb, ch, gl = sc.inst(0, 'timpani'), sc.inst(1, 'contrabass'), sc.inst(2, 'choir'), sc.inst(3, 'glass')
    sc.note(title, 2.0, tp, m('D2'), 127); sc.note(title + 0.01, 3.4, cb, m('D1'), 110)
    sc.ramp(ch, title, title + 0.3, 90, 90); sc.ramp(ch, title + 1.0, E['silence'], 90, 25)
    sc.chord(title, E['silence'] - title, ch, ms('D3', 'A3', 'D4'), 70)
    sc.note(title + 0.3, E['silence'] - title, gl, m('A5'), 45)
    stems['title'] = sc.render()
    return stems
