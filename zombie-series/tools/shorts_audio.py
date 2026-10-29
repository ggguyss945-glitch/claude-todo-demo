# Sound for the cut shorts: the episode's own voice and effects, cut on the same frames as the picture, and its
# score brought up front for a phone (louder, lighter ducking), crossfaded across the cuts so it never jumps; where
# the episode has no music, a cue in the same mood fills the gap. Then muxed with the rendered video.
# usage: python3 -I tools/shorts_audio.py <id> [work_dir]   (after tools/shorts.py render has made <work>/video.mp4)
import sys, os, json, re, subprocess
import numpy as np, soundfile as sf
from pedalboard import Pedalboard, Compressor
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, f'{ROOT}/audio')
from ep_music import render_cue, GAIN
SCR = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad'
SF2 = f'{SCR}/sf/GeneralUser-GS.sf2'
SR, FPS = 48000, 60
db = lambda d: 10 ** (d / 20)
MOOD = dict(ep2_s1_storm='storm', ep2_s2_dontmove='tender', ep2_s3_song='plan', ep1_s1_doors='tick', ep1_s2_radio='radio', ep1_s3_freezer='pulse_soft')
MUSIC_UP = 4.0      # dB over the episode's score bus
DUCK = -5.0         # under the voice (the episode used -11)
XF = 0.15           # score overlap on each side of a cut

def read(path, a, b):
    x, _ = sf.read(path, start=max(0, a), stop=max(0, b), dtype='float32', always_2d=True)
    if a < 0: x = np.concatenate([np.zeros((-a, 2), np.float32), x])
    if len(x) < b - a: x = np.concatenate([x, np.zeros((b - a - len(x), 2), np.float32)])
    return x

def lufs(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])

def limit(x, ceil=-1.0):
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    n = int(0.03 * SR) | 1
    g = np.minimum(1.0, db(ceil) / np.maximum(np.abs(x).max(1), 1e-9)).astype(np.float32)
    return (x * uniform_filter1d(minimum_filter1d(g, 2 * n + 1), n)[:, None]).astype(np.float32)

def build(sid, work):
    P = json.load(open(f'{ROOT}/shorts/{sid}.json')); T = json.load(open(f"{ROOT}/{P['timeline']}")); E0 = T['ep_start']
    st = f"{SCR}/shorts/stems/ep{P['ep']}"
    segs = P['segments']; dur = sum((s['f1'] - s['f0']) / FPS for s in segs); N = int(round(dur * SR))
    voice, fx, score = (np.zeros((N + SR, 2), np.float32) for _ in range(3))
    cues = sorted(T['music'], key=lambda c: c['t'])
    iv = [(c['t'], cues[i + 1]['t'] if i + 1 < len(cues) else T['dur']) for i, c in enumerate(cues) if c['cue'] != 'stop']
    # music playing inside the story (the store jingle out of the drone) counts as music: no filler over it
    for e in T['sfx']:
        if e['name'] in ('drone_song', 'jingle'):
            p = e.get('p') or {}
            end = T['items'][p['until']][0] + p.get('off', 0) if 'until' in p else e['t'] + p.get('dur', 10)
            iv.append((e['t'], end))
    has_score = np.zeros(N + SR, np.float32)
    o = 0
    for k, s in enumerate(segs):
        a = int(round((s['f0'] / FPS - E0) * SR)); n = int(round((s['f1'] - s['f0']) / FPS * SR)); i = int(round(o * SR))
        e = np.ones(n, np.float32); f = int(0.025 * SR); e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
        voice[i:i + n] += read(f'{st}/stemfull_voice.wav', a, a + n) * e[:, None]
        fx[i:i + n] += read(f'{st}/stemfull_fx.wav', a, a + n) * e[:, None]
        # the score overlaps its neighbours by XF on each side, so every cut is a short crossfade
        x = int(XF * SR) if k > 0 else 0; y = int(XF * SR) if k < len(segs) - 1 else 0
        m = read(f'{st}/stemfull_score.wav', a - x, a + n + y)
        em = np.ones(len(m), np.float32)
        if x: em[:2 * x] = np.linspace(0, 1, 2 * x)
        if y: em[-2 * y:] = np.linspace(1, 0, 2 * y)
        j = i - x; score[max(0, j):j + len(m)] += (m * em[:, None])[max(0, -j):]
        ts = s['f0'] / FPS + np.arange(0, n, SR // 100) / SR
        on = np.array([any(p <= t < q for p, q in iv) for t in ts], np.float32)
        has_score[i:i + n] = np.repeat(on, SR // 100)[:n]
        o += n / SR
    # fill the stretches without music with a cue in the short's mood, eased in and out over 0.8 s
    from scipy.ndimage import uniform_filter1d
    need = uniform_filter1d(1 - has_score, int(0.8 * SR))
    cue = MOOD[sid]; bed = render_cue(SF2, cue, dur + 1.0, {})[:N + SR]
    bed = np.concatenate([bed, np.zeros((N + SR - len(bed), 2), np.float32)]) if len(bed) < N + SR else bed
    music = score + bed * db(GAIN.get(cue, 0) - 6.5) * need[:, None]
    # duck lightly under the voice, a little ahead of each word
    hop = SR // 100; v = np.abs(voice).mean(1); nf = len(v) // hop
    fr = np.sqrt((v[:nf * hop].reshape(nf, hop) ** 2).mean(1)); on = (fr > 0.004).astype(np.float32)
    on = np.maximum(on, np.convolve(on, np.ones(12), 'same') > 0)
    sm = np.zeros(nf, np.float32); c = 0.0
    for q in range(nf): c += (on[q] - c) * ((1 - np.exp(-1 / 8)) if on[q] > c else (1 - np.exp(-1 / 35))); sm[q] = c
    act = np.interp(np.arange(len(v)), np.arange(nf) * hop + hop / 2, sm).astype(np.float32)
    act = np.concatenate([act[int(0.06 * SR):], np.full(int(0.06 * SR), act[-1], np.float32)])
    music *= (db(MUSIC_UP) * (1 - act * (1 - db(DUCK))))[:, None]
    sf.write(f'{work}/voice_only.wav', voice[:N], SR, subtype='PCM_16')
    mix = (voice + fx + music)[:N]
    mix = limit(Pedalboard([Compressor(threshold_db=-16, ratio=2.0, attack_ms=12, release_ms=150)])(mix, SR), -2.0)
    sf.write(f'{work}/pre_music.wav', mix, SR, subtype='PCM_24')
    g = -14.0 - lufs(f'{work}/pre_music.wav')
    for _ in range(4):
        fin = limit(mix * db(g)); sf.write(f'{work}/audio_music.wav', fin, SR, subtype='PCM_24')
        L = lufs(f'{work}/audio_music.wav')
        if abs(L + 14) < 0.1: break
        g += -14.0 - L
    out = f'{work}/{sid}_1440x2560_60fps.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{work}/video.mp4', '-i', f'{work}/audio_music.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True)
    print(sid, 'audio', round(L, 2), 'LUFS,', round(float((1 - has_score[:N]).mean()) * dur, 1), 's filled with', cue, '->', out)

if __name__ == '__main__':
    sid = sys.argv[1]; build(sid, sys.argv[2] if len(sys.argv) > 2 else f'{SCR}/shorts/{sid}')
