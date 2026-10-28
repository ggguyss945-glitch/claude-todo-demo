# Voice every line of an episode script: narrator, Dale over the radio, you (hushed), the store PA.
# Each phrase's chosen take is cached by its text and settings, so editing the script re-voices only what changed.
# A script with VOICE_MODE = 'item' voices each line in one pass (intonation carries across its sentences) and
# then fits the pauses between phrases; a line that will not read back falls back to phrase by phrase.
# usage: python3 -I ep_voice.py <scratch_dir> <out_dir> [script_module=ep1_script]
import sys, os, json, re, hashlib, importlib, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts
from tts import SR, best_take, script_words, process_narration, pa_chain, pipe_chain, trim, asr, radio, whisper

S, OUT = sys.argv[1], sys.argv[2]
SC = importlib.import_module(sys.argv[3] if len(sys.argv) > 3 else 'ep1_script')
os.makedirs(f'{OUT}/cache', exist_ok=True)
tts.init(S)

VOICES = {'N': dict(sid=5, takes=5), 'DALE': dict(sid=9, takes=4), 'HERO': dict(sid=8, takes=4), 'NORA': dict(sid=1, takes=5)}
MODE = getattr(SC, 'VOICE_MODE', 'phrase'); STEPS = getattr(SC, 'VOICE_STEPS', 8)

def spoken(text):
    for a, b in SC.SAY.items(): text = re.sub(rf'\b{a}\b', b, text)
    return text

def phrase(who, text, rate):
    v = VOICES[who]; say = spoken(text)
    key = hashlib.sha1(f'{who}|{v}|{text}|{say}|{rate}{"" if STEPS == 8 else f"|{STEPS}"}'.encode()).hexdigest()[:16]
    p = f'{OUT}/cache/{key}.npz'
    if os.path.exists(p):
        a = np.load(p, allow_pickle=True)['a']
    else:
        a, exp, heard, speed, score = best_take(text, rate, v['sid'], v['takes'], say if say != text else None, STEPS)
        np.savez(p, a=a)
        print(f'    {who:4s} "{text}" speed {speed:.2f} score {score:.2f} | {heard}', flush=True)
    exp, heard = asr(a)
    times = tts.align(asr.raw, text, len(a) / SR)
    return a, times, heard

def whole(who, phrases, rate):
    """One take for the whole line, cached; None if no take reads back (then the line goes phrase by phrase)."""
    v = VOICES[who]; text = ' '.join(t for t, _ in phrases); say = spoken(text)
    key = hashlib.sha1(f'item2|{who}|{v}|{json.dumps(phrases)}|{say}|{rate}|{STEPS}'.encode()).hexdigest()[:16]
    p = f'{OUT}/cache/{key}.npz'
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True)
        if z['a'].size == 0: return None
        return z['a'], list(z['st']), list(z['ends']), str(z['heard'])
    r = tts.item_take(phrases, rate, v['sid'], v['takes'], say if say != text else None, STEPS)
    if r is None:
        np.savez(p, a=np.zeros(0, np.float32)); return None
    a, st, ends, heard, speed, score = r
    np.savez(p, a=a, st=np.array(st), ends=np.array(ends), heard=heard)
    print(f'    {who:4s} speed {speed:.2f} score {score:.2f} | {heard}', flush=True)
    return a, st, ends, heard

items, bad = [], []
for k, it in enumerate(SC.ITEMS):
    if it['who'] == 'BEAT':
        items.append({x: y for x, y in it.items()}); continue
    parts, words, heard_all, pos = [], [], [], 0.0
    if it['who'] == 'PA':
        text = ' '.join(p for p, _ in it['phrases'])
        a, psr = tts.kok.create(spoken(text), voice='af_heart', speed=1.06, lang='en-us')
        a = trim(librosa.resample(a.astype(np.float32), orig_sr=psr, target_sr=SR))
        exp, heard = asr(a)
        sw = script_words(text)
        words = [{'w': w, 't': round(exp[j][1] if j < len(exp) else len(a) / SR * j / len(sw), 3)} for j, w in enumerate(sw)]
        y = pa_chain(a.astype(np.float32), SR)
        heard_all = [heard]
    else:
        w1 = whole(it['who'], it['phrases'], it['rate']) if MODE == 'item' else None
        if w1:
            raw, st, ends, heard = w1
            sw = script_words(' '.join(p for p, _ in it['phrases']))
            words = [{'w': w, 't': round(st[j], 3)} for j, w in enumerate(sw)]
            k0 = 0
            for (ptxt, _), e in zip(it['phrases'], ends):
                k0 += len(script_words(ptxt)); words[k0 - 1]['e'] = round(e, 3)
            heard_all = [heard]
        elif MODE == 'item': bad.append((it['id'], 'whole line did not read back', ''))
        for i, (ptxt, pause) in enumerate(it['phrases'] if not w1 else []):
            a, times, heard = phrase(it['who'], ptxt, it['rate'])
            sw = script_words(ptxt)
            if times is None:   # fall back to spreading the words over the phrase by length
                bad.append((it['id'], ptxt, heard))
                L = np.array([len(w) + 1 for w in sw], float); times = list(np.concatenate([[0], np.cumsum(L)[:-1]]) / L.sum() * len(a) / SR * 0.9 + 0.04)
            for j, w in enumerate(sw):
                words.append({'w': w, 't': round(pos + times[j], 3)})
            words[-1]['e'] = round(pos + len(a) / SR - 0.06, 3)
            parts.append(a); heard_all.append(heard); pos += len(a) / SR
            if i < len(it['phrases']) - 1:
                parts.append(np.zeros(int(pause * SR), np.float32)); pos += pause
        if not w1: raw = np.concatenate(parts)
        if it['who'] == 'N':
            y = process_narration(raw)
        elif it['who'] == 'HERO':
            y = whisper(process_narration(raw) * 0.8, seed=k)
        elif it['who'] == 'DALE' and it.get('pipe'):   # his own voice through the wall, not the radio
            y = pipe_chain(process_narration(raw).astype(np.float32), SR)
        elif it['who'] == 'NORA' and not it.get('radio'):   # hushed, but less breath than you: she's used to it
            y = whisper(process_narration(raw) * 0.85, seed=k, air_mix=0.28)
        else:   # DALE: keep the room-free voice for the echo, send the radio version to the speaker
            clean = process_narration(raw)
            sf.write(f'{OUT}/{it["id"]}_clean.wav', clean.astype(np.float32), SR)
            y, pre = radio(clean, seed=k)
            for w in words:
                w['t'] = round(w['t'] + pre, 3)
                if 'e' in w: w['e'] = round(w['e'] + pre, 3)
    y = y * 10 ** (it['level'] / 20)
    sf.write(f'{OUT}/{it["id"]}.wav', y.astype(np.float32), SR)
    items.append({x: v for x, v in it.items()} | {'dur': round(len(y) / SR, 3), 'words': words, 'asr': ' '.join(heard_all),
                                                'text': ' '.join(p for p, _ in it['phrases'])})
    print(f'{it["id"]:6s} {it["who"]:4s} {len(y) / SR:5.2f}s  {items[-1]["text"][:70]}', flush=True)

json.dump({'sr': SR, 'items': items, 'voices': VOICES}, open(f'{OUT}/voice.json', 'w'), indent=1)
print('items', len(items), '| phrases that never read back cleanly:', len(bad))
for b in bad: print('  ', b)
