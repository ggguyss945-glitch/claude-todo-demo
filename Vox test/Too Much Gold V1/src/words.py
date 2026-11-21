"""Word timings for the one-word captions: Parakeet-TDT on the finished narration, aligned to the script text.

    words.py <vo_raw.wav> <vo_lines.json> <out words.json>
"""
import json, re, sys, numpy as np, soundfile as sf, librosa, sherpa_onnx, os
S = os.environ.get("ASR_DIR")
wav, lines_p, out = sys.argv[1:4]
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=S + "/encoder.int8.onnx", decoder=S + "/decoder.int8.onnx",
                                                    joiner=S + "/joiner.int8.onnx", tokens=S + "/tokens.txt", model_type="nemo_transducer", num_threads=4)
y, sr = sf.read(wav)
y16 = librosa.resample(y, orig_sr=sr, target_sr=16000).astype(np.float32)
lines = json.load(open(lines_p))
words = []
for ln in lines:
    # recognise each line on its own (with a little context padding) so timings never drift across lines
    a, b = int(max(0, ln["start"] - 0.05) * 16000), int((ln["end"] + 0.05) * 16000)
    seg = np.concatenate([np.zeros(3200, np.float32), y16[a:b], np.zeros(3200, np.float32)])
    st = rec.create_stream(); st.accept_waveform(16000, seg); rec.decode_stream(st)
    toks = [(t, ts - 0.2 + a / 16000) for t, ts in zip(st.result.tokens, st.result.timestamps)]
    asr = []
    for t, ts in toks:
        if t.startswith(" ") or not asr: asr.append([t.strip(), ts])
        else: asr[-1][0] += t
    script_words = ln["text"].split()
    # align by letters: each script word starts where its first letter falls in the recognised text,
    # so splits and merges ("twenty-four" / "twenty four", "Everyone's" / "Every one's") don't matter
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    pos, times = 0, []
    for w, ts in asr:
        times += [ts] * len(norm(w))
    starts, c = [], 0
    for w in script_words:
        starts.append(times[min(c, len(times) - 1)] if times else ln["start"])
        c += len(norm(w))
    if abs(c - len(times)) > 2:
        print("  letter count differs:", ln["text"], "|", " ".join(w[0] for w in asr))
    for w, t0 in zip(script_words, starts):
        words.append({"w": w, "s": round(max(ln["start"], float(t0)), 3), "line": ln["i"], "who": ln["who"]})
    words[-1]["end_line"] = ln["end"]
json.dump(words, open(out, "w"), indent=0)
print(len(words), "words; first", words[0], "last", words[-1])
