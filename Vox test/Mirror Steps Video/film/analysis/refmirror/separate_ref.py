"""Split a reference mix into voice and bed (bed = mix - voice) with sherpa-onnx UVR MDX-NET Voc_FT.

Usage: python3 -I separate_ref.py <model.onnx> <in.wav> <out_dir> [threads]
Writes <out_dir>/voice.wav and <out_dir>/bed.wav (float, input rate). 60 s chunks, 2 s crossfades.
Same method as ../separate.py (police references), with the model path and thread count as arguments.
"""
import os, sys, time
import numpy as np, soundfile as sf, sherpa_onnx


def main(model, src, out, threads=2):
    mc = sherpa_onnx.OfflineSourceSeparationModelConfig(
        uvr=sherpa_onnx.OfflineSourceSeparationUvrModelConfig(model=model), num_threads=int(threads))
    sep = sherpa_onnx.OfflineSourceSeparation(sherpa_onnx.OfflineSourceSeparationConfig(model=mc))
    x, sr = sf.read(src, dtype="float32", always_2d=True)
    n = len(x); C = 60 * sr; O = 2 * sr; t0 = time.time()
    voice = np.zeros_like(x); w = np.zeros(n, np.float32); s0 = 0
    while s0 < n:
        e = min(n, s0 + C + O)
        r = sep.process(sample_rate=sr, samples=np.ascontiguousarray(x[s0:e].T))
        v = np.stack([np.asarray(c.data) for c in r.stems[0].data]).T[: e - s0]
        if v.shape[1] == 1: v = np.repeat(v, 2, 1)
        L = e - s0; win = np.ones(L, np.float32); f = min(O, L)
        if s0 > 0: win[:f] = np.linspace(0, 1, f)
        if e < n: win[-f:] = np.minimum(win[-f:], np.linspace(1, 0, f))
        voice[s0:e] += v * win[:, None]; w[s0:e] += win
        print(f"{s0/sr:.0f}s done ({time.time()-t0:.0f}s)", flush=True)
        if e >= n: break
        s0 = e - O
    voice /= np.maximum(w, 1e-6)[:, None]
    os.makedirs(out, exist_ok=True)
    sf.write(f"{out}/voice.wav", voice, sr, subtype="FLOAT")
    sf.write(f"{out}/bed.wav", x - voice, sr, subtype="FLOAT")
    print(f"{src}: {n/sr:.1f}s audio in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main(*sys.argv[1:5])
