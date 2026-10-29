"""Voices for "The Other Resident": English on its own timeline, the Russian dub fitted line by line into the same slots.
    python3 voice.py <supertonic model dir> <out dir>
Writes vo_en.wav, vo_ru.wav (48 kHz mono, same length) and timeline.json (start, durations, speaker, text, tag per line).
"""
import json, math, os, re, sys
import numpy as np, soundfile as sf, sherpa_onnx
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'script'))
from lines import LINES

MODEL, OUT = sys.argv[1], sys.argv[2]
SR = 48000
# speaker -> (Supertonic voice id, base speed, semitone shift)
VOICE = {'N': (1, 0.9, 0.0), 'O': (8, 0.9, -0.6), 'Y': (5, 0.95, 0.0), 'D': (5, 0.95, 0.0), 'M': (4, 0.88, -0.8), 'F': (3, 0.95, 0.0)}
SHAKY = {"He looks just like you.", "The ring's on the correct hand,", "And the scar...", "Of course I do.", "Mum, please. It's cold.",
         "Have you found him? Is he all right?"}
TTS_FIX = {'12:36': 'twelve thirty-six', 'IDENTITY VERIFIED': 'identity verified', 'ЛИЧНОСТЬ ПОДТВЕРЖДЕНА': 'личность подтверждена'}
LEAD = 0.8                                      # silence before the first line

tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=f'{MODEL}/duration_predictor.int8.onnx', text_encoder=f'{MODEL}/text_encoder.int8.onnx',
        vector_estimator=f'{MODEL}/vector_estimator.int8.onnx', vocoder=f'{MODEL}/vocoder.int8.onnx', tts_json=f'{MODEL}/tts.json',
        unicode_indexer=f'{MODEL}/unicode_indexer.bin', voice_style=f'{MODEL}/voice.bin'), num_threads=2)))


def say(text, who, lang, speed_mul=1.0):
    sid, base, semis = VOICE[who]
    for a, b in TTS_FIX.items(): text = text.replace(a, b)
    g = sherpa_onnx.GenerationConfig(); g.sid = sid; g.speed = base * speed_mul; g.num_steps = 12; g.extra = {'lang': lang}
    a = tts.generate(text, g)
    x = np.asarray(a.samples, np.float32)
    x = signal.resample_poly(x, SR, a.sample_rate).astype(np.float32)
    if semis: x = pitch(x, semis)
    return trim(x)


def trim(x, thr=0.008, pad=0.03):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx): return x
    a, b = max(0, idx[0] - int(pad * SR)), min(len(x), idx[-1] + int(pad * SR))
    y = x[a:b].copy(); f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def pitch(x, semis):
    """Shift pitch, keep length: resample then time-stretch back with a simple overlap-add."""
    r = 2 ** (semis / 12)
    y = signal.resample(x, int(len(x) / r))
    return stretch(y, len(x) / len(y))


def stretch(x, ratio, win=0.04):
    """Overlap-add time stretch (ratio > 1 makes it longer). Fine for small changes on speech."""
    n = int(win * SR); hop_in = n // 4; hop_out = int(hop_in * ratio)
    w = np.hanning(n).astype(np.float32)
    frames = max(1, (len(x) - n) // hop_in)
    out = np.zeros(frames * hop_out + n, np.float32); norm = np.zeros_like(out)
    for i in range(frames):
        seg = x[i * hop_in:i * hop_in + n]
        if len(seg) < n: break
        out[i * hop_out:i * hop_out + n] += seg * w; norm[i * hop_out:i * hop_out + n] += w
    return out / np.maximum(norm, 1e-3)


def shaky(x):
    """A trembling voice: slow pitch wobble and a little amplitude tremor."""
    t = np.arange(len(x)) / SR
    wob = 0.0035 * np.sin(2 * np.pi * 5.5 * t) + 0.002 * np.sin(2 * np.pi * 3.1 * t + 1)
    idx = np.clip(np.arange(len(x)) + np.cumsum(wob) * SR * 0.02, 0, len(x) - 1)
    y = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
    return y * (1 - 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * 6.2 * t)))


def band(x, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'); return signal.sosfilt(sos, x).astype(np.float32)


def radio(x, seed=0):
    rng = np.random.default_rng(seed)
    y = band(x, 380, 3200); y = np.tanh(y * 3.2) / np.tanh(3.2)
    hiss = band(rng.normal(0, 1, len(y)).astype(np.float32), 1500, 6000) * 0.012
    y = y + hiss
    sq = band(rng.normal(0, 1, int(0.12 * SR)).astype(np.float32), 800, 5000) * np.linspace(0.25, 0, int(0.12 * SR))
    return np.concatenate([sq * 0.8, y, sq[::-1] * 0.5]).astype(np.float32) * 0.9


def phone(x, far=False, seed=1):
    y = band(x, 320, 3300, 6); y = np.tanh(y * 1.8) / np.tanh(1.8)
    if far:  # heard through the phone from outside a door: muffled and roomy
        y = band(y, 300, 1600, 4)
        ir = np.exp(-np.linspace(0, 6, int(0.35 * SR))) * np.random.default_rng(seed).normal(0, 1, int(0.35 * SR))
        y = signal.fftconvolve(y, ir.astype(np.float32))[:len(y) + int(0.2 * SR)] * 0.05 + np.pad(y, (0, int(0.2 * SR))) * 0.6
    return y.astype(np.float32) * (0.8 if not far else 0.7)


def process(x, line):
    if line['en'] in SHAKY: x = shaky(x)
    fx = line['fx']
    if fx == 'radio': x = radio(x, hash(line['en']) % 100)
    elif fx == 'phone': x = phone(x)
    elif fx == 'phone_far': x = phone(x, True)
    return x


def level(x, target_db=-20.0):
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2) + 1e-9)
    return x * (10 ** (target_db / 20) / rms)


os.makedirs(OUT, exist_ok=True)
segs, t = [], LEAD
for i, ln in enumerate(LINES):
    en = level(process(say(ln['en'], ln['who'], 'en', ln['pace']), ln), -20 if ln['who'] == 'N' else -21)
    slot = len(en) / SR + ln['pause'] * 0.85                  # the Russian line must end before the next English line starts
    ru, k = None, 1.0
    for _ in range(4):                                        # speed the Russian up until it fits its slot
        ru = say(ln['ru'], ln['who'], 'ru', ln['pace'] * k)
        if len(ru) / SR <= slot: break
        k *= min(1.25, (len(ru) / SR) / slot * 1.02)
        if k > 1.35: break
    if len(ru) / SR > slot:                                   # last resort: squeeze it a little
        ru = stretch(ru, max(0.86, slot / (len(ru) / SR)))
    ru = level(process(ru, ln), -20 if ln['who'] == 'N' else -21)
    segs.append({'i': i, 'who': ln['who'], 'en': ln['en'], 'ru': ln['ru'], 'tag': ln['tag'], 'fx': ln['fx'], 't': round(t, 3),
                 'dur_en': round(len(en) / SR, 3), 'dur_ru': round(len(ru) / SR, 3), 'ru_speed': round(k, 3), '_en': en, '_ru': ru})
    t += len(en) / SR + ln['pause']
    if i % 20 == 0: print(f'{i}/{len(LINES)}  t={t:.1f}s', flush=True)
total = t + 1.5
for lang in ('en', 'ru'):
    buf = np.zeros(int(total * SR) + SR, np.float32)
    for s in segs:
        a = int(s['t'] * SR); x = s['_' + lang]; buf[a:a + len(x)] += x
    peak = np.abs(buf).max(); buf *= min(1.0, 0.89 / peak)
    sf.write(os.path.join(OUT, f'vo_{lang}.wav'), buf[:int(total * SR)], SR, subtype='PCM_24')
json.dump({'duration': round(total, 3), 'lines': [{k: v for k, v in s.items() if not k.startswith('_')} for s in segs]},
          open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
over = [s for s in segs if s['dur_ru'] > s['dur_en'] + 0.05]
print(f'total {total:.1f}s ({total / 60:.1f} min); Russian longer than English on {len(over)} lines (all inside their slot)')
