"""Final mix: narration (English or the Russian dub) + diegetic voice effects + sound effects + score, -14 LUFS.
    python3 mix.py <timeline.json> <vo_en.wav> <vo_ru_dub.wav> <sfx dir> <out dir>
Writes mix_en.wav, mix_ru.wav (48 kHz stereo) and cues.json (the score cue sheet).
Radio, phone and through-the-door lines get their effect on whichever voice track is playing, at that line's time
(the Russian dub's own times for its lines come from the dub log).
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx_horror as SX

TL, VO_EN, VO_RU, SFXD, OUT = sys.argv[1:6]
SR = 48000
tl = json.load(open(TL)); L = tl['lines']
DUR = tl['duration_en'] + 2.5
N = int(DUR * SR)
os.makedirs(OUT, exist_ok=True)


def find(prefix, after=0):
    for l in L[after:]:
        if l['en'].startswith(prefix): return l
    raise KeyError(prefix)


def band(x, lo, hi, order=4):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x).astype(np.float32)


def radio_fx(x):
    y = band(x, 380, 3200); y = np.tanh(y * 3.0) / np.tanh(3.0)
    return (y + band(np.random.default_rng(1).normal(0, 1, len(y)).astype(np.float32), 1500, 6000) * 0.006) * 1.1


def phone_fx(x, far=False):
    y = band(x, 320, 3300, 6); y = np.tanh(y * 1.6) / np.tanh(1.6)
    if far: y = band(y, 300, 1500, 4) * 0.8
    return y * 1.05


def apply_line_fx(vo, spans):
    """spans: list of (start s, end s, kind). Replace those stretches of the voice with the processed version."""
    out = vo.copy()
    for a, b, kind in spans:
        i0, i1 = max(0, int((a - 0.05) * SR)), min(len(vo), int((b + 0.15) * SR))
        seg = vo[i0:i1]
        if len(seg) < 100: continue
        y = radio_fx(seg) if kind == 'radio' else phone_fx(seg, kind == 'phone_far')
        f = int(0.01 * SR); w = np.ones(len(seg), np.float32); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        out[i0:i1] = seg * (1 - w) + y[:len(seg)] * w
    return out


def load_vo(path):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    if sr != SR: x = signal.resample_poly(x, SR, sr).astype(np.float32)
    y = np.zeros(N, np.float32); y[:min(N, len(x))] = x[:N]
    return y


# ------------------------------------------------------------------ voice tracks with diegetic effects
en_spans = [(l['t'], l['end'], l['fx']) for l in L if l['fx'] and l.get('found_en', True)]
ru_start = {}
for g in tl.get('dub', []):
    i, j = g['lines']; ru_start[i] = g['ru_start']
ru_spans = []
for l in L:
    if not l['fx']: continue
    a = ru_start.get(l['i'], l['t']); d = l['ru_src'][1] - l['ru_src'][0] if 'ru_src' in l else l['end'] - l['t']
    ru_spans.append((a, a + max(0.4, d), l['fx']))
vo = {'en': apply_line_fx(load_vo(VO_EN), en_spans), 'ru': apply_line_fx(load_vo(VO_RU), ru_spans)}

# ------------------------------------------------------------------ sound effects on story beats
fx = np.zeros((N, 2), np.float32)


def put(x, t, gain_db=0.0, pan=0.0):
    if x is None or t is None: return
    if x.ndim == 1: x = np.stack([x * (1 - max(0, pan)), x * (1 + min(0, pan))], 1)
    a = int(t * SR); b = min(N, a + len(x))
    if a >= N or b <= a: return
    fx[a:b] += x[:b - a] * (10 ** (gain_db / 20))


def at(prefix, off=0.0):
    try: return find(prefix)['t'] + off
    except KeyError: return None


def end(prefix, off=0.0):
    try: return find(prefix)['end'] + off
    except KeyError: return None


def S(name, *a, **k):
    f = getattr(SX, name, None)
    return f(*a, **k).astype(np.float32) if f else None


put(S('house_room_tone_bed', DUR), 0, -6)
put(S('night_ambience_bed', DUR), 0, -10)
put(S('knock_door', variant='heavy') if 'variant' in SX.knock_door.__code__.co_varnames else S('knock_door'), at("It's 12:36", 0.15), 0)
put(S('camera_beep'), at("He touches the camera", 0.9), -6)
put(S('radio_crackle'), at("Eventually, his radio will crackle.", 1.1), -4)
for p in ("I live here.", "I... live here."):
    put(S('radio_click'), at(p, -0.25), -8)
put(S('radio_beep'), at("The officer presses a button", 1.2), -6)
put(S('radio_crackle'), at("After a while, another voice", 1.5), -6)
put(S('radio_click'), at("You'll hear a quiet click", 1.4), -2)
put(S('phone_ring_out', 2.4), at("Try calling her yourself.", 0.9), -10)
put(S('phone_busy_tone', 3.0), at("Her line will be busy.", 0.4), -12)
put(S('mail_slot'), at("He'll suggest sliding it", 1.0), -6)
put(S('mail_slot'), at("Eventually, the officer will slide", 1.2), -4)
put(S('paper_rustle'), at("You read it twice."), -10)
put(S('stinger_dissonant'), at("It's yours."), -8)
put(S('car_door_open'), at("Outside, a car door opens.", 0.6), -6, -0.4)
put(S('footsteps_path'), at("The man from the back seat walks", 0.2), -10, -0.2)
put(S('low_boom'), at("It's almost yours."), -6)
put(S('pen_click'), at("The officer takes a pen", 1.2), -8)
put(S('camera_beep'), at("After a few seconds, he turns off", 1.6), -6)
put(S('keys_jingle'), at("The other man will take a key", 1.0), -8)
put(S('key_in_lock'), at("He'll hold it near the lock", 0.6), -6)
cd = find("Let him reach zero.")
for k in range(10): put(S('countdown_tick'), cd['t'] + k * 0.33, -6)
put(S('breath_close'), at("You'll hear him breathing", 0.8), -6)
put(S('car_door_open'), at("Then the second officer will get out", 0.8), -8, -0.4)
put(S('footsteps_path'), at("She'll walk up the path", 0.1), -10, -0.2)
put(S('keys_jingle'), at("Inside are a wallet", 1.2), -10)
put(S('camera_beep'), at("The officer switches his camera back on.", 1.0), -6)
put(S('car_door_close'), at("The man with your face gets into", 1.4), -8, -0.4)
put(S('car_drive_away'), at("You keep watching until the car", 0.3), -8, -0.3)
put(S('phone_ring_out', 1.6), at("Then you try your mother again.", 0.8), -10)
put(S('phone_pickup'), at("This time, she answers", 1.2), -8)
put(S('tv_off'), at("You hear her television go quiet.", 0.9), -8)
k2 = S('knock_door'); put(phone_fx(k2) if k2 is not None else None, at("There's knocking at her door.", 0.6), -4)
put(S('slippers_floor'), at("You hear her slippers", 0.4), -8)
put(S('curtain_rings'), at("The little scrape of the curtain", 0.3), -6)
put(S('reverse_swell'), at("His fingers are spread"), -8)
put(S('stinger_dissonant'), at("It's empty."), -8)
put(S('lock_turn'), at("Then you hear her key turning.", 1.1), -2)
put(S('low_boom'), end("Then you hear her key turning.", 0.2), -4)
put(S('tinnitus_ring'), end("Then you hear her key turning.", 0.4), -16)
for n in range(1, 8):
    names = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven'}
    put(S('whoosh_soft'), at(f"Rule number {names[n]}.", -0.25), -12)

# ------------------------------------------------------------------ score cues
C = []
def cue(t, typ, lvl=0.5):
    if t is not None: C.append({'t': round(max(0.0, t), 3), 'type': typ, 'level': lvl})
cue(0.0, 'drone', 0.35)
cue(at("It's 12:36"), 'drone', 0.45)
cue(at("Only then do you notice"), 'strings', 0.5)
cue(at("If this happens, there are seven rules"), 'riser')
for n, w in enumerate(('one', 'two', 'three', 'four', 'five', 'six', 'seven'), 1):
    cue(at(f"Rule number {w}."), 'rule', 0.7)
cue(at("The card outside has the same"), 'piano', 0.6)
cue(at("His fingers are spread"), 'strings', 0.6)
cue(at("Eventually, his radio will crackle."), 'pulse', 0.5)
cue(at("This time, it sounds right."), 'pulse', 0.0)
cue(at("It's your mother."), 'piano', 0.5)
cue(at("You'll hear a quiet click"), 'hit', 0.5)
cue(at("Then you look at the complainant's name."), 'silence')
cue(at("It's yours."), 'hit', 0.8)
cue(at("Outside, a car door opens."), 'pulse', 0.55)
cue(at("It's almost yours."), 'strings', 0.7)
cue(at("Rule number five."), 'pulse', 0.0)
cue(at("Waiting."), 'silence')
cue(at("It was your father."), 'piano', 0.6)
cue(at("He may count down from ten."), 'pulse', 0.7)
cue(at("There won't be a kick."), 'silence')
cue(at("There won't be a kick."), 'pulse', 0.0)
cue(at("You recognize the bright orange"), 'strings', 0.6)
cue(at("Rule number seven."), 'drone', 0.5)
cue(at("There's knocking at her door."), 'pulse', 0.6)
cue(at("He looks just like you."), 'strings', 0.7)
cue(at("You turn toward the hook"), 'riser')
cue(at("It's empty."), 'hit', 0.9)
cue(at("Outside her house, the other you"), 'strings', 0.8)
cue(at("Then you hear her key turning."), 'riser')
cue(end("Then you hear her key turning.", 0.2), 'hit', 1.0)
cue(end("Then you hear her key turning.", 0.3), 'pulse', 0.0)
cue(at("So, if a police officer ever knocks"), 'drone', 0.3)
cue(at("Because the person waiting"), 'piano', 0.6)
cue(DUR - 1.0, 'drone', 0.0)
json.dump({'duration': DUR, 'cues': sorted(C, key=lambda c: c['t'])}, open(os.path.join(OUT, 'cues.json'), 'w'), indent=1)
subprocess.run([sys.executable, os.path.join(HERE, 'score.py'), os.path.join(OUT, 'cues.json'), os.path.join(OUT, 'score.wav')], check=True)
score, sr = sf.read(os.path.join(OUT, 'score.wav'), dtype='float32')
if score.ndim == 1: score = np.stack([score, score], 1)
score = score[:N] if len(score) >= N else np.pad(score, ((0, N - len(score)), (0, 0)))


# ------------------------------------------------------------------ ducking and the final mixes
def env_follow(x, attack=0.01, release=0.35):
    e = np.abs(x); out = np.zeros_like(e); a = np.exp(-1 / (attack * SR)); r = np.exp(-1 / (release * SR)); v = 0.0
    step = 64
    for i in range(0, len(e), step):
        m = e[i:i + step].max(); v = a * v + (1 - a) * m if m > v else r * v + (1 - r) * m; out[i:i + step] = v
    return out


def loudness(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True)
    for l in r.stderr.splitlines()[::-1]:
        if l.strip().startswith('I:'): return float(l.split()[1])
    return None


for lang in ('en', 'ru'):
    v = vo[lang]
    duck = 1 - 0.5 * np.clip(env_follow(v) / 0.05, 0, 1)            # music and beds dip ~6 dB under the voice
    mixd = np.stack([v, v], 1) * 1.0 + score * duck[:, None] * 0.9 + fx * (0.6 + 0.4 * duck[:, None])
    tmp = os.path.join(OUT, f'_pre_{lang}.wav'); sf.write(tmp, mixd, SR, subtype='FLOAT')
    li = loudness(tmp); g = 10 ** ((-14.0 - li) / 20) if li else 1.0
    y = mixd * g
    lim = 10 ** (-1.2 / 20); knee = 0.6 * lim                          # soft ceiling for the rare peak: linear below the knee
    a_ = np.abs(y); over = a_ > knee
    y[over] = np.sign(y[over]) * (knee + (lim - knee) * np.tanh((a_[over] - knee) / (lim - knee)))
    out = os.path.join(OUT, f'mix_{lang}.wav'); sf.write(out, y, SR, subtype='PCM_24'); os.remove(tmp)
    print(lang, 'pre', li, 'LUFS -> final', loudness(out))
