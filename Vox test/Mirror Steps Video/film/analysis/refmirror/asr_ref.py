"""Timed transcript of a separated voice stem: silero VAD segments -> sherpa-onnx NeMo transducer, with token times.

Usage: python3 -I asr_ref.py <voice.wav> <vad.onnx> <transducer_model_dir> <out.json> [threads]
Output: [{"t0", "t1", "text", "words": [[t, word], ...]}] (absolute seconds).
"""
import json, sys
import numpy as np, librosa, sherpa_onnx

def main(wav, vadm, md, out, threads=2):
    y, _ = librosa.load(wav, sr=16000, mono=True); y = y.astype(np.float32)
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = vadm
    cfg.silero_vad.min_silence_duration = 0.3; cfg.silero_vad.min_speech_duration = 0.2; cfg.silero_vad.max_speech_duration = 15
    cfg.silero_vad.threshold = 0.45; cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{md}/encoder.int8.onnx", decoder=f"{md}/decoder.int8.onnx",
        joiner=f"{md}/joiner.int8.onnx", tokens=f"{md}/tokens.txt", model_type="nemo_transducer", num_threads=int(threads))
    segs = []
    for i in range(0, len(y), 512):
        vad.accept_waveform(y[i:i + 512])
        while not vad.empty():
            s = vad.front; segs.append((s.start, np.array(s.samples, dtype=np.float32))); vad.pop()
    vad.flush()
    while not vad.empty():
        s = vad.front; segs.append((s.start, np.array(s.samples, dtype=np.float32))); vad.pop()
    res = []
    for st0, smp in segs:
        st = rec.create_stream(); st.accept_waveform(16000, smp); rec.decode_stream(st)
        r = st.result; t0 = st0 / 16000
        words, cur, ct = [], "", None
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith(" ") or tok.startswith("▁") or cur == "":
                if cur: words.append([round(t0 + ct, 2), cur.strip()])
                cur, ct = tok.replace("▁", " "), ts
            else:
                cur += tok
        if cur: words.append([round(t0 + ct, 2), cur.strip()])
        res.append({"t0": round(t0, 2), "t1": round(t0 + len(smp) / 16000, 2), "text": r.text.strip(), "words": words})
    json.dump(res, open(out, "w"), indent=0)
    print(wav, len(res), "segments")

if __name__ == "__main__":
    main(*sys.argv[1:6])
