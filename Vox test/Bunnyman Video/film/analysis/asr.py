"""Transcribe a separated reference voice stem into timed segments (sherpa-onnx whisper base.en).

Usage: python3 asr.py <voice.wav> <out.json>
Output: [{"t": start_s, "end": end_s, "text": str}], segments cut at speech gaps, <= 25 s each.
Used only to locate rule announcements and scares for AUDIO_SPEC notes.
"""
import json, os, sys
import numpy as np, soundfile as sf, librosa, sherpa_onnx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import kweight, momentary, speech_mask, runs_of, HOP

M = "/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work/pov2/models_asr/sherpa-onnx-whisper-base.en"


def main(vp, out):
    x, sr = sf.read(vp, dtype="float32", always_2d=True)
    vm = momentary(kweight(x, sr), sr, win=0.1)
    sp, _ = speech_mask(vm)
    segs = [[a * HOP, b * HOP] for a, b in runs_of(sp)]
    chunks = []
    for a, b in segs:
        if chunks and b - chunks[-1][0] <= 25 and a - chunks[-1][1] < 1.2:
            chunks[-1][1] = b
        else:
            chunks.append([a, b])
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{M}/base.en-encoder.int8.onnx", decoder=f"{M}/base.en-decoder.int8.onnx",
        tokens=f"{M}/base.en-tokens.txt", num_threads=4)
    y = librosa.resample(x.mean(1), orig_sr=sr, target_sr=16000)
    res = []
    for a, b in chunks:
        s = rec.create_stream()
        s.accept_waveform(16000, y[int(max(0, a - 0.2) * 16000):int((b + 0.2) * 16000)])
        rec.decode_stream(s)
        res.append({"t": round(a, 2), "end": round(b, 2), "text": s.result.text.strip()})
    json.dump(res, open(out, "w"), indent=0)
    print(len(res), "segments")


if __name__ == "__main__":
    main(*sys.argv[1:3])
