"""Scare check on the final mix: momentary (400 ms) max over the integrated level after each boosted hit, and the
recogniser on each scare line cut from the mix (50 ms margins)."""
import json, os, sys
import numpy as np, soundfile as sf, soxr, pyloudnorm as pyln, sherpa_onnx
F = '/home/user/claude-todo-demo/Vox test/Bus Video/film'
sys.path.insert(0, F + '/audio')
import music_plan as M
L = json.load(open(F + '/_work/align/timeline.json'))['lines']
y, sr = sf.read(F + '/_work/mix/final/mix.wav')
mono = y.mean(1) if y.ndim > 1 else y
meter = pyln.Meter(sr)
I = meter.integrated_loudness(y)
print('integrated %.2f LUFS' % I)
for nm in ('show', 'music'):
    fp = F + '/_work/mix/final/stems/%s_en.wav' % nm
    if not os.path.exists(fp): fp = F + '/_work/mix/final/stems/%s.wav' % nm
    if not os.path.exists(fp): continue
    z, _ = sf.read(fp)
    for lab, t in (('PA L70', L[70]['t'] + 0.7), ('PA L238', L[238]['t'])):
        m = pyln.Meter(sr, block_size=0.4)
        print('%s %s: %.1f LU rel the mix' % (nm, lab, m.integrated_loudness(z[int(t * sr):int((t + 1.5) * sr)]) - I))
t = L[364]['t'] - 0.4
print('bell drop-out: min 50 ms RMS %.1f dBFS' % min(20 * np.log10(np.sqrt(np.mean(mono[int((t + k * 0.05) * sr):int((t + k * 0.05 + 0.05) * sr)] ** 2)) + 1e-12) for k in range(40)))
pk = os.environ.get("PARAKEET_DIR", "/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{pk}/encoder.int8.onnx', decoder=f'{pk}/decoder.int8.onnx',
                                                    joiner=f'{pk}/joiner.int8.onnx', tokens=f'{pk}/tokens.txt',
                                                    model_type='nemo_transducer', num_threads=2)
for i in (76, 106, 116, 143, 171, 187, 212, 213, 231, 232, 256, 275, 276, 305, 306, 342, 365, 366, 369, 370):
    a, b = L[i]['t'], L[i]['end']
    z = mono[int((a - 0.05) * sr):int((b + 0.05) * sr)]
    z16 = np.concatenate([np.zeros(4800), soxr.resample(z, sr, 16000), np.zeros(4800)]).astype(np.float32)
    st = rec.create_stream(); st.accept_waveform(16000, z16); rec.decode_stream(st)
    print('L%d %-40s | %s' % (i, L[i]['en'][:40], st.result.text.strip()))
