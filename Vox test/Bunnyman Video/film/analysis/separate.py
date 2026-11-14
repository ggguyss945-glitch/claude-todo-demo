"""Separate reference narration from the music+SFX bed with sherpa-onnx.

Usage: python3 separate.py <in.wav> <out_dir> [spleeter|uvr] [--seconds N]
Writes <out_dir>/<stem>_voice.wav and <stem>_bed.wav (44.1 kHz stereo float).
UVR (MDX-NET Voc_FT) is the default: cleaner voice/bed split than spleeter.
The bed is computed as mix - voice so nothing is lost between stems.
"""
import os, sys, time
import numpy as np, soundfile as sf, sherpa_onnx

M = "/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work/pov2/models_sep"

def make(kind):
    if kind == "spleeter":
        mc = sherpa_onnx.OfflineSourceSeparationModelConfig(
            spleeter=sherpa_onnx.OfflineSourceSeparationSpleeterModelConfig(
                vocals=f"{M}/sherpa-onnx-spleeter-2stems-fp16/vocals.fp16.onnx",
                accompaniment=f"{M}/sherpa-onnx-spleeter-2stems-fp16/accompaniment.fp16.onnx"),
            num_threads=4)
    else:
        mc = sherpa_onnx.OfflineSourceSeparationModelConfig(
            uvr=sherpa_onnx.OfflineSourceSeparationUvrModelConfig(model=f"{M}/UVR-MDX-NET-Voc_FT.onnx"),
            num_threads=4)
    return sherpa_onnx.OfflineSourceSeparation(sherpa_onnx.OfflineSourceSeparationConfig(model=mc))

def main():
    a = sys.argv[1:]; secs = None
    if "--seconds" in a:
        i = a.index("--seconds"); secs = float(a[i + 1]); del a[i:i + 2]
    src, out = a[0], a[1]; kind = a[2] if len(a) > 2 else "uvr"
    x, sr = sf.read(src, dtype="float32", always_2d=True)
    if secs: x = x[: int(secs * sr)]
    sep = make(kind); t0 = time.time()
    # process in 60 s chunks with 2 s overlap crossfade to bound memory
    n = len(x); C = 60 * sr; O = 2 * sr
    voice = np.zeros_like(x); w = np.zeros(n, np.float32)
    s0 = 0
    while s0 < n:
        e = min(n, s0 + C + O)
        r = sep.process(sample_rate=sr, samples=np.ascontiguousarray(x[s0:e].T))
        v = np.stack([np.asarray(c.data) for c in r.stems[0].data]).T  # stem 0 = vocals
        v = v[: e - s0]
        if v.shape[1] == 1: v = np.repeat(v, 2, 1)
        L = e - s0; win = np.ones(L, np.float32)
        f = min(O, L)
        if s0 > 0: win[:f] = np.linspace(0, 1, f)
        if e < n: win[-f:] = np.minimum(win[-f:], np.linspace(1, 0, f))
        voice[s0:e] += v * win[:, None]; w[s0:e] += win
        if e >= n: break
        s0 = e - O
    voice /= np.maximum(w, 1e-6)[:, None]
    bed = x - voice
    stem = os.path.splitext(os.path.basename(src))[0]
    os.makedirs(out, exist_ok=True)
    sf.write(f"{out}/{stem}_voice.wav", voice, sr, subtype="FLOAT")
    sf.write(f"{out}/{stem}_bed.wav", bed, sr, subtype="FLOAT")
    print(f"{stem} {kind} {n/sr:.1f}s audio in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
