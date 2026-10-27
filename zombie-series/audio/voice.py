# Synthesize narration + PA line for the 60 s test, process like a close, warm studio mic, and get word timings.
# Narration: Supertonic-3, voiced phrase by phrase; each phrase gets several takes and the best one is kept
# (it must read back correctly through ASR, sit near the target pace, and have the liveliest pitch).
# usage: python3 -I voice.py <scratch_dir> <out_dir>
import sys, os, json, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts
from tts import SR, best_take, script_words, process_narration, pa_chain, trim, asr
from script_test import LINES, PA_LINE, NARRATOR, NARRATION_START

S, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
tts.init(S)

out = {'sr': SR, 'lines': [], 'narrator': NARRATOR}
t = NARRATION_START
for L in LINES:
    parts, words, heard_all, pos = [], [], [], 0.0
    for i, (ptxt, pause, *say) in enumerate(L['phrases']):
        a, exp, heard, speed, score = best_take(ptxt, L['rate'], NARRATOR['sid'], NARRATOR['takes'], say[0] if say else None)
        sw = script_words(ptxt)
        for j, w in enumerate(sw):
            words.append({'w': w, 't': round(pos + (exp[j][1] if j < len(exp) else len(a) / SR * j / len(sw)), 3)})
        words[-1]['e'] = round(pos + len(a) / SR - 0.06, 3)       # phrase-final word: when the voice stops
        parts.append(a); heard_all.append(heard); pos += len(a) / SR
        print(f'  {L["id"]:4s} "{ptxt}" speed {speed:.2f} score {score:.2f} | {heard}')
        if i < len(L['phrases']) - 1:
            parts.append(np.zeros(int(pause * SR), np.float32)); pos += pause
    raw = np.concatenate(parts)
    a = process_narration(raw) * 10 ** (L['level'] / 20)
    sf.write(f'{OUT}/{L["id"]}.wav', a.astype(np.float32), SR)
    out['lines'].append({k: v for k, v in L.items() if k != 'phrases'} | {'phrases': [list(p) for p in L['phrases']],
                        'start': round(t, 3), 'dur': round(len(a) / SR, 3), 'words': words, 'asr': ' '.join(heard_all)})
    print(f'{L["id"]:4s} {t:6.2f}s +{len(a)/SR:4.2f}s  {len(words) / (len(a) / SR):.2f} w/s')
    t += len(a) / SR + L['gap']
out['narration_end'] = round(t, 3)

pa, psr = tts.kok.create(PA_LINE['text'], voice=PA_LINE['voice'], speed=PA_LINE['speed'], lang='en-us')
pa = trim(librosa.resample(pa.astype(np.float32), orig_sr=psr, target_sr=SR))
pa_exp, _ = asr(pa); pa_words = [{'w': w, 't': round(tt, 3)} for w, (_, tt) in zip(script_words(PA_LINE['text']), pa_exp)]
pa_p = pa_chain(pa.astype(np.float32), SR)
sf.write(f'{OUT}/PA.wav', pa_p, SR)
out['pa'] = {'dur': round(len(pa_p) / SR, 3), 'words': pa_words, 'text': PA_LINE['text']}
json.dump(out, open(f'{OUT}/voice.json', 'w'), indent=1)
print('narration ends at', round(t, 2), 's | PA dur', out['pa']['dur'])
