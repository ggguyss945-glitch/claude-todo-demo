#!/usr/bin/env python3
"""Underscore for the police-officer "rules" video, rendered from a cue sheet.

    python3 score.py <cues.json> <out.wav>
    cues.json = {"duration": s, "cues": [{"t": s, "type": ..., "level": 0..1}, ...]}

Everything lives in D phrygian (D Eb F G A Bb C) with Ab, the tritone, as the wrong note; slow,
sparse and dark, normalised to about -26 LUFS integrated so it can sit ~15 LU under the narrator.
  drone    equal-power crossfade (4 s) to a dark evolving drone at this intensity. The voicing
           thickens with level: open D-A fifth (<0.4), + Eb or Ab (<0.7), D-Ab-A-Eb clusters with a
           resonant whistling air above them (>=0.7). Brightness and partials drift slowly. 0 fades out.
  pulse    slow lub-dub on D1 (50 bpm at low level up to 68 bpm at 1); level 0 stops it.
  piano    one or two sparse notes (FluidSynth grand), each doubled 16 cents sharp and 12 ms late
           like a neglected upright, in a long dark hall.
  strings  a dissonant cluster (FluidSynth slow strings: semitone pairs a tritone apart) swelling up
           and away over 6-10 s; above 0.6 a high tremolo rub joins in the middle.
  riser    5 s of rising cluster, tremolo and noise that stops dead at t.
  hit      low sub boom falling onto D1 at t.
  silence  everything ducks to -40 dB for 2 s from t: hits/piano come back instantly at t+2, the
           drone/pulse/strings fade back in over ~1.8 s.
  rule     rule-title-card motif: a lighter low hit, a soft high bell on D6, answered by Ab5.
"""
import json, os, subprocess, sys, tempfile
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
import soundfile as sf
from scipy import signal, ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_horror import SR, t_, noise, hz, lp, hp, norm, unit, wavetable, room_ir, riser as riser_fx, _boom

TARGET_LUFS, CEIL = -26.0, 10 ** (-2.0 / 20)        # sample-peak ceiling leaves room for inter-sample peaks
SOUNDFONT = next((p for p in ('/etc/alternatives/MuseScore_General.sf3', '/usr/share/sounds/sf3/MuseScore_General_Full.sf3',
                              '/usr/share/sounds/sf2/FluidR3_GM.sf2') if os.path.exists(p)), None)
XF, FLOOR, RISER_LEN = 4.0, 0.01, 5.0
GAIN = dict(drone=1.0, pulse=2.6, piano=10.0, strings=6.6, riser=3.7, hit=1.4, rule=1.2)   # layer balance, measured in K-weighted loudness

def lvl(c): return float(np.clip(c.get('level', 0.5), 0, 1))

def put(out, x, t, g=1.0):
    """add a mono or stereo sound into the stereo buffer at t seconds (clipped to the buffer)"""
    x = np.asarray(x, np.float32); x = x if x.ndim == 2 else np.stack([x, x], 1)
    i = int(round(t * SR))
    for a in range(max(0, i), min(len(out), i + len(x)), 1 << 20):       # in chunks: no full-length temporaries
        b = min(len(out), i + len(x), a + (1 << 20)); out[a:b] += g * x[a - i:b - i]

def verb(x, rt60, wet, seed, damp=3500.0, dry=1.0):
    """stereo hall from two decorrelated synthetic IRs: mono or stereo in, stereo out with its tail"""
    x = np.asarray(x, np.float32); x = x if x.ndim == 2 else np.stack([x, x], 1)
    y = np.zeros((len(x) + int(rt60 * 1.2 * SR), 2), np.float32); y[:len(x)] = dry * x
    for c in (0, 1):
        ir = room_ir(rt60, damp, seed + c, 4.0).astype(np.float32)
        for a in range(0, len(x), 30 * SR):                       # overlap-add in 30 s chunks, skipping silence
            if np.any(x[a:a + 30 * SR, c]): w = signal.fftconvolve(x[a:a + 30 * SR, c], ir); y[a:a + len(w), c] += wet * w
    return y

def wander(dur, rate, seed):
    """a smooth random 0..1 control (50 Hz), returned as a function of time so long holds stay cheap"""
    m = int(dur * 50) + 16
    v = signal.sosfiltfilt(signal.butter(2, rate, fs=50, output='sos'), np.random.default_rng(seed).standard_normal(m))
    v = (v - v.min()) / (np.ptp(v) + 1e-12); tc = np.arange(m) / 50
    return lambda tt: np.interp(tt, tc, v)

# ------------------------------------------------------------------ drone ---
VOICINGS = [[[38, 45], [38, 50, 57]],                  # open D2-A2 fifth / D2 D3 A3
            [[38, 45, 51], [38, 44, 50]],              # + Eb3, the phrygian flat second / + Ab2, the tritone
            [[38, 44, 45, 51], [38, 45, 51, 56]]]      # clusters: D2 Ab2 A2 Eb3 / D2 A2 Eb3 Ab3

def drone_voice(n, level, notes, seed, blk=20 * SR):
    """n samples (stereo) of drone at one intensity: detuned saws through two lowpasses with a
    drifting balance, a D1 sub, and (level > 0.5) noise ringing three octaves above the chord.
    Rendered in 20 s blocks with filter state carried across."""
    dur = n / SR + 0.1; out = np.empty((n, 2), np.float32)
    for c in (0, 1):
        s = seed * 7 + c * 101; r = np.random.default_rng(s)
        osc = [(hz(m) * 2 ** ((cents + 1.5 * (2 * c - 1)) / 1200), r.random(), wander(dur, 0.03, s + 10 * j + k), 1.0 if j == 0 else 0.7,
                wavetable(int(np.clip(1500 / hz(m), 1, 256)))) for j, m in enumerate(notes) for k, cents in enumerate((-4 - j, 3 + j))]
        bright, sub, air = wander(dur, 0.02, s + 50), wander(dur, 0.05, s + 60), wander(dur, 0.06, s + 80)
        sd, sb = (signal.butter(2, f, fs=SR, output='sos') for f in (190 + 250 * level, 450 + 900 * level))
        zd, zb = np.zeros((1, 2)), np.zeros((1, 2))
        rings = [signal.iirpeak(hz(m + 36), 60, fs=SR) for m in notes]; zr = [np.zeros(2) for _ in notes]
        gen = np.random.default_rng(s + 70)
        for a in range(0, n, blk):
            tt = np.arange(a, min(n, a + blk)) / SR; x = np.zeros(len(tt))
            for f, ph, amp, w, tab in osc: x += w * (0.5 + 0.5 * amp(tt)) * tab[(((ph + f * tt) % 1.0) * 4096).astype(np.int64) & 4095]
            dark, zd = signal.sosfilt(sd, x, zi=zd); light, zb = signal.sosfilt(sb, x, zi=zb)
            k = bright(tt) * level
            y = dark * (1 - k) + 0.7 * light * k + 0.3 * np.sin(2 * np.pi * hz(26) * tt + c) * (0.6 + 0.4 * sub(tt))
            if level > 0.5:
                nz = gen.standard_normal(len(tt)); ring = np.zeros(len(tt))
                for i, (bb, aa) in enumerate(rings):
                    yy, zr[i] = signal.lfilter(bb, aa, nz, zi=zr[i]); ring += yy / np.sqrt(np.pi / 2 * hz(notes[i] + 36) / 60 / (SR / 2))
                y += 0.12 * (level - 0.5) * 2 * ring * air(tt)
            out[a:a + len(tt), c] = y
    return out

def render_drone(cues, out, g):
    n = len(out)
    for i, c in enumerate(cues):
        L, t0 = lvl(c), c['t']; t1 = cues[i + 1]['t'] if i + 1 < len(cues) else None
        a, b = int(round(t0 * SR)), n if t1 is None else min(n, int(round((t1 + XF) * SR)))
        if L <= 0 or b <= a: continue
        seg = drone_voice(b - a, L, VOICINGS[0 if L < 0.4 else 1 if L < 0.7 else 2][i % 2], i + 1)
        seg *= L / (np.std(seg) + 1e-9)
        tt = np.arange(a, b) / SR; e = np.sin(0.5 * np.pi * np.clip((tt - t0) / XF, 0, 1))
        if t1 is not None: e *= np.cos(0.5 * np.pi * np.clip((tt - t1) / XF, 0, 1))
        out[a:b] += g * seg * e[:, None].astype(np.float32)

# ------------------------------------------------------------------ pulse ---
def beat():
    """one lub-dub tuned to D1; tanh adds harmonics so it still reads on small speakers"""
    tt = t_(1.0)
    def th(dec): f = hz(26) * (1 + 0.8 * np.exp(-tt * 30)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * dec) * (1 - np.exp(-tt * 300))
    x = th(9); d = int(0.3 * SR); x[d:] += 0.6 * th(12)[: len(x) - d]
    return verb(lp(np.tanh(1.6 * x), 220), 1.2, 0.25, 77)

def render_pulse(cues, out, g):
    b, dur, t = beat(), len(out) / SR, cues[0]['t']
    while t < dur:
        L = next((lvl(c) for c in reversed(cues) if c['t'] <= t + 1e-6), 0.0)
        if L <= 0:
            nxt = [c['t'] for c in cues if c['t'] > t + 1e-6 and lvl(c) > 0]
            if not nxt: break
            t = nxt[0]; continue
        put(out, b, t, g * L); t += 60 / (50 + 18 * L)

# -------------------------------------------------------- piano & strings ---
def vlq(v):
    b = [v & 0x7F]; v >>= 7
    while v: b.insert(0, (v & 0x7F) | 0x80); v >>= 7
    return bytes(b)

def write_midi(path, ev, end):
    """ev: (seconds, order, message bytes); a format-0 file at 120 bpm / 960 ppq = 1920 ticks per second"""
    trk, last = bytearray(b'\x00\xff\x51\x03\x07\xa1\x20'), 0
    for t, _, msg in sorted(ev, key=lambda e: (e[0], e[1])):
        k = int(round(t * 1920)); trk += vlq(max(0, k - last)) + bytes(msg); last = max(last, k)
    trk += vlq(max(0, int(end * 1920) - last)) + b'\xff\x2f\x00'
    with open(path, 'wb') as f: f.write(b'MThd' + (6).to_bytes(4, 'big') + b'\x00\x00\x00\x01\x03\xc0' + b'MTrk' + len(trk).to_bytes(4, 'big') + trk)

def setup(ch, prog, pan): return [(0, 0, [0xB0 | ch, 7, 100]), (0, 0, [0xB0 | ch, 10, pan]), (0, 0, [0xB0 | ch, 11, 127]), (0, 0, [0xC0 | ch, prog])]
def note(ev, ch, t, dur, m, vel): ev += [(t, 3, [0x90 | ch, m, int(np.clip(vel, 1, 127))]), (t + dur, 1, [0x80 | ch, m, 0])]

def fluid(ev, end, name, tmp):
    """render MIDI events with FluidSynth (its own reverb/chorus off) to a float stereo array"""
    if SOUNDFONT is None: raise RuntimeError('no General MIDI soundfont found for piano/strings cues')
    mid, wav = os.path.join(tmp, name + '.mid'), os.path.join(tmp, name + '.wav')
    write_midi(mid, ev, end)
    subprocess.run(['fluidsynth', '-ni', '-q', '-o', 'synth.dynamic-sample-loading=1', '-o', 'synth.cpu-cores=1', '-R', '0', '-C', '0',
                    '-g', '0.8', '-r', str(SR), '-O', 'float', '-T', 'wav', '-F', wav, SOUNDFONT, mid], check=True, stdout=subprocess.DEVNULL)
    x, sr = sf.read(wav, dtype='float32', always_2d=True)
    if sr != SR: raise RuntimeError(f'fluidsynth rendered at {sr} Hz')
    return x

PIANO = [[(0.0, 74)], [(0.0, 69), (1.2, 75)], [(0.0, 62), (1.6, 68)],      # D5 / A4 -> Eb5 / D4 -> Ab4 (tritones)
         [(0.0, 70), (0.9, 69)], [(0.0, 75), (1.4, 74)], [(0.0, 50), (0.06, 56)]]   # Bb4 -> A4 / Eb5 -> D5 / low D3 + Ab3

def render_piano(cues, out, g, tmp):
    t0 = max(0.0, cues[0]['t'] - 0.5); bend = 8192 + round(8192 * 16 / 200)       # +16 cents (bend range +-2 st)
    ev = setup(0, 0, 46) + setup(1, 0, 82) + [(0, 0, [0xE1, bend & 0x7F, bend >> 7])]
    for k, c in enumerate(cues):
        v = 30 + 50 * lvl(c)
        for dt, m in PIANO[[0, 1, 3, 2, 4, 5][k % 6]]:
            note(ev, 0, c['t'] - t0 + dt, 4.5, m, v); note(ev, 1, c['t'] - t0 + dt + 0.012, 4.5, m, v - 14)
    put(out, verb(fluid(ev, cues[-1]['t'] - t0 + 7, 'piano', tmp), 4.5, 0.9, 11, 3000, 0.7), t0, g)

CLUSTERS = [[50, 51, 56, 57], [45, 46, 51, 62], [50, 56, 63, 69], [46, 57, 62, 63]]   # D Eb Ab A / A Bb Eb D / D Ab Eb A / Bb A D Eb

def render_strings(cues, out, g, tmp):
    t0 = max(0.0, cues[0]['t'] - 0.5); swell = lambda u: np.sin(np.pi * u ** 0.85) ** 1.5
    ev = sum((setup(ch, 49, pan) for ch, pan in zip((2, 3, 4, 5), (40, 88, 56, 72))), []) + setup(6, 44, 52) + setup(7, 44, 76)
    end = 0
    for k, c in enumerate(cues):
        L, T, ch, t = lvl(c), 6 + 4 * ((k * 0.618034) % 1), 2 + k % 4, c['t'] - t0
        for m in CLUSTERS[k % 4]: note(ev, ch, t, T + 0.3, m, 80)
        ev += [(t + i / 40 * T, 2, [0xB0 | ch, 11, int(round((40 + 87 * L) * swell(i / 40)))]) for i in range(41)]
        if L > 0.6:                                     # a high tremolo semitone rub through the middle of the swell
            tc, top = 6 + k % 2, CLUSTERS[k % 4][-1] + 12
            for m in (top, top - 1): note(ev, tc, t + 0.3 * T, 0.6 * T, m, 50)
            ev += [(t + 0.3 * T + i / 20 * 0.6 * T, 2, [0xB0 | tc, 11, int(round(70 * (L - 0.6) / 0.4 * np.sin(np.pi * i / 20) ** 2))]) for i in range(21)]
        end = max(end, t + T + 3)
    put(out, verb(fluid(ev, end, 'strings', tmp), 3.5, 0.6, 21, 3500, 0.8), t0, g)

# --------------------------------------------------------- risers, hits, rule ---
def render_risers(cues, out, g):
    for k, c in enumerate(cues): put(out, verb(riser_fx(RISER_LEN, 40 + k), 1.5, 0.3, 40 + k), c['t'] - RISER_LEN, g * lvl(c))

def render_hits(cues, out, g):
    for k, c in enumerate(cues): put(out, verb(norm(_boom(5.0, hz(26), 50 + k), 1.0), 3.5, 0.45, 50 + k, 1500), c['t'], g * lvl(c))

def bell(f, dur=6.0, seed=0):
    """a soft high bell: inharmonic partials in slowly beating pairs, the upper ones dying first"""
    tt = t_(dur); x = 0.03 * unit(hp(noise(dur, seed), 3000)) * np.exp(-tt * 300)
    for r, a, d in [(1.0, 1.0, 0.9), (2.0, 0.3, 1.6), (2.76, 0.35, 2.2), (4.07, 0.12, 3.5), (5.43, 0.07, 5.0)]:
        for det in (-0.35, 0.35): x = x + a * np.sin(2 * np.pi * (f * r + det) * tt) * np.exp(-tt * d)
    return x * (1 - np.exp(-tt * 400))

def render_rules(cues, out, g):
    for k, c in enumerate(cues):
        x = np.zeros(int(7 * SR)); b = norm(_boom(4.0, hz(26), 60 + k), 0.8); x[:len(b)] += b
        hi, lo = norm(bell(hz(86), 6.0, 61 + k), 0.35), norm(bell(hz(80), 6.0, 62 + k), 0.22)      # D6, then Ab5
        x[int(0.04 * SR):][:len(hi)] += hi[: len(x) - int(0.04 * SR)]; x[int(0.7 * SR):][:len(lo)] += lo[: len(x) - int(0.7 * SR)]
        put(out, verb(x, 4.5, 0.8, 60 + k, 4000), c['t'], g * lvl(c))

def duck(cues, n, rec):
    """gain curve for 'silence': -40 dB from t to t+2 s, recovering over `rec` seconds"""
    g = np.ones(n, np.float32)
    for c in cues:
        t = c['t']; up = t + 2.0 - min(rec, 0.12); a, b = max(0, int(t * SR)), min(n, int((up + rec) * SR) + 1)
        if b > a: g[a:b] = np.minimum(g[a:b], np.interp(np.arange(a, b) / SR, [t, t + 0.06, up, up + rec], [1, FLOOR, FLOOR, 1]))
    return g

# -------------------------------------------------------------- loudness ---
KW = np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
               [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]])          # BS.1770 K-weighting at 48 kHz

def filter_inplace(sos, x, chunk=10 * SR):
    """run a filter over a long float32 (n, channels) array in place, 10 s at a time (memory stays flat)"""
    for c in range(x.shape[1]):
        zi = np.zeros((len(sos), 2))
        for a in range(0, len(x), chunk): x[a:a + chunk, c], zi = signal.sosfilt(sos, x[a:a + chunk, c], zi=zi)
    return x

def lufs(x):
    """integrated loudness, ITU-R BS.1770-4: K-weighting, 400 ms blocks every 100 ms, -70 LUFS and -10 LU gates"""
    hop = int(0.1 * SR); seg = np.zeros(len(x) // hop)            # K-weighted energy per 100 ms
    for c in range(x.shape[1]):
        zi = np.zeros((2, 2))
        for a in range(0, len(seg) * hop, 100 * hop):
            y, zi = signal.sosfilt(KW, x[a:min(a + 100 * hop, len(seg) * hop), c], zi=zi)
            seg[a // hop:a // hop + len(y) // hop] += (y ** 2).reshape(-1, hop).sum(1)
    z = np.convolve(seg, np.ones(4), 'valid') / (4 * hop); z = z[z > 10 ** ((-70 + 0.691) / 10)]
    if not len(z): return -np.inf
    z = z[z > z.mean() * 0.1]
    return -0.691 + 10 * np.log10(z.mean())

def limit(x, ceil=CEIL, hold=0.02):
    """peak limiter: the gain dips just before any peak over the ceiling (20 ms look-ahead) and eases back"""
    need = np.minimum(1.0, ceil / np.maximum(np.abs(x).max(1), 1e-9))
    if need.min() >= 1: return x
    w = int(hold * SR); g = ndimage.uniform_filter1d(ndimage.minimum_filter1d(need, 2 * w + 1), w)
    return (x * np.minimum(g, need)[:, None]).astype(np.float32)

# ------------------------------------------------------------------ render ---
def render(doc):
    n = int(round(float(doc['duration']) * SR)); cues = sorted(doc['cues'], key=lambda c: c['t'])
    by = lambda kind: [c for c in cues if c['type'] == kind]
    for c in cues:
        if c['type'] not in GAIN and c['type'] != 'silence': print('ignoring unknown cue type', c['type'], file=sys.stderr)
    beds, events = np.zeros((n, 2), np.float32), np.zeros((n, 2), np.float32)
    if by('drone'): render_drone(by('drone'), beds, GAIN['drone'])
    if by('pulse'): render_pulse(by('pulse'), beds, GAIN['pulse'])
    with tempfile.TemporaryDirectory() as tmp:
        if by('strings'): render_strings(by('strings'), beds, GAIN['strings'], tmp)
        if by('piano'): render_piano(by('piano'), events, GAIN['piano'], tmp)
    for kind, fn in (('riser', render_risers), ('hit', render_hits), ('rule', render_rules)):
        if by(kind): fn(by(kind), events, GAIN[kind])
    beds *= duck(by('silence'), n, 1.8)[:, None]; events *= duck(by('silence'), n, 0.12)[:, None]
    beds += events; del events
    mix = filter_inplace(signal.butter(2, 20, 'high', fs=SR, output='sos'), beds); del beds
    a, b = min(n, int(0.01 * SR)), min(n, int(0.5 * SR))
    mix[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None]; mix[n - b:] *= np.linspace(1, 0, b, dtype=np.float32)[:, None]
    for _ in range(4):
        L = lufs(mix)
        if not np.isfinite(L) or abs(L - TARGET_LUFS) < 0.1: break
        mix = limit(mix * np.float32(10 ** ((TARGET_LUFS - L) / 20)))
    mix = limit(mix); return mix, lufs(mix)

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    with open(sys.argv[1]) as f: mix, L = render(json.load(f))
    if not np.all(np.isfinite(mix)): sys.exit('non-finite samples in the mix')
    sf.write(sys.argv[2], mix, SR, subtype='PCM_24')
    print(f'{sys.argv[2]}: {len(mix) / SR:.3f} s, {L:.1f} LUFS integrated, peak {20 * np.log10(np.abs(mix).max() + 1e-12):.1f} dBFS')
