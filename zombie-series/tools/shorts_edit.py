# Edited vertical shorts: word-level cuts with the pauses taken out, a little faster than the episode, punch-in
# zooms, shakes and flashes on the hits, word-group captions, a hook title, a new music bed that runs across the
# cuts, whooshes, risers and booms. The picture comes from clean 1440x2560 frames rendered through
# engine/short.html?clean=1 (named by episode frame, shared between shorts); everything else happens here.
#   python3 -I tools/shorts_edit.py plan   <edit.json>          -> clip list + the episode times still to render
#   python3 -I tools/shorts_edit.py render <edit.json>          -> renders the missing clean frames
#   python3 -I tools/shorts_edit.py make   <edit.json> <out_dir> -> audio + picture + final mp4
import sys, os, json, math, subprocess
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/shorts'
FPS, OW, OH = 60, 1440, 2560
TL = {1: f'{ROOT}/episodes/ep1/timeline.json', 2: f'{ROOT}/episodes/ep2/timeline.json'}
CACHE = lambda ep: f'{SCR}/clean_ep{ep}'
PAD0, PAD1 = 0.05, 0.08          # kept before a phrase's first word and after its last

def phrases(L, w=None, keep=False):
    """[(t0, t1, words)] in episode time; a phrase ends at a word that carries an end time"""
    ws = L['words']; i0, i1 = (w or [0, len(ws) - 1])
    end_of = lambda i: L['start'] + (ws[i]['e'] if 'e' in ws[i] else (ws[i + 1]['t'] - 0.03 if i + 1 < len(ws) else L['dur']))
    out, cur = [], []
    for i in range(i0, i1 + 1):
        cur.append(i)
        if 'e' in ws[i] or i == i1:
            out.append((L['start'] + ws[cur[0]]['t'] - PAD0, end_of(i) + PAD1, cur)); cur = []
    if keep: out = [(out[0][0], out[-1][1], [i for p in out for i in p[2]])]
    return [(a, b, [dict(w=ws[i]['w'], t=L['start'] + ws[i]['t']) for i in ix]) for a, b, ix in out]

def plan(E):
    T = json.load(open(TL[E['ep']])); L = {l['id']: l for l in T['voice']['lines']}
    shot_at = lambda t: next((i for i, s in enumerate(T['shots']) if s['start'] <= t < s['end']), len(T['shots']) - 1)
    FR = json.load(open(f'{ROOT}/shorts/framing_ep{E["ep"]}.json'))
    def is_fit(i):   # text cards are shown whole across the width; captions then sit below them
        sh = T['shots'][i]; d = FR.get(f"{sh['start']:.2f}")
        return (d or {}).get('mode') == 'fit' or (d is None and sh['name'] in ('card', 'card2', 'map', 'map2'))
    clips = []
    for bi, b in enumerate(E['beats']):
        sp = b.get('speed', E['speed'])
        if 'act' in b:
            ps = [(b['act'][0], b['act'][1], [])]; who = None
        else:
            ln = L[b['line']]; ps = phrases(ln, b.get('w'), b.get('keep')); who = ln.get('who', 'N')
            if b.get('post'): a, z, w = ps[-1]; ps[-1] = (a, z + b['post'], w)
        for k, (a, z, words) in enumerate(ps):
            f0 = round(a * FPS); n = max(1, round((z - a) / sp * FPS))
            src = [round((a + j * sp / FPS) * FPS) for j in range(n)]
            clips.append(dict(beat=bi, k=k, t0=a, t1=z, speed=sp, n=n, src=src, words=words, who=who, shot=shot_at((a + z) / 2), fit=is_fit(shot_at((a + z) / 2)),
                              fx=b.get('fx') if k == 0 else None, flash_word=b.get('flash_word'), act='act' in b))
    # no clip may start inside the previous one's source span when they are neighbours in the episode
    t = 0.0
    for c in clips: c['out0'] = t; t += c['n'] / FPS; c['out1'] = t
    return T, clips, t

def times_needed(E, clips):
    have = set(int(f[2:8]) for f in os.listdir(CACHE(E['ep'])) if f.startswith('f_')) if os.path.isdir(CACHE(E['ep'])) else set()
    need = sorted(set(f for c in clips for f in c['src']) - have)
    return [f / FPS for f in need], need

def clean_plan(ep):
    # every shot with its framing, so the clean page can place its 9:16 window at any episode time
    T = json.load(open(TL[ep])); FR = json.load(open(f'{ROOT}/shorts/framing_ep{ep}.json'))
    pcs = []
    for sh in T['shots']:
        key = f"{sh['start']:.2f}"
        d = FR.get(key) or ({'mode': 'fit'} if sh['name'] in ('card', 'card2', 'map', 'map2') else {'x': 960})
        pcs.append(dict(d, t0=sh['start'], t1=sh['end'], shot=key, name=sh['name']))
    P = dict(id=f'clean_ep{ep}', ep=ep, pieces=pcs, hook=dict(lines=[''], dur=0), tag='')
    json.dump(P, open(f'{ROOT}/shorts/clean_ep{ep}.json', 'w'))

def render(E):
    T, clips, dur = plan(E); times, need = times_needed(E, clips)
    print(E['id'], 'needs', len(need), 'new frames of', sum(c['n'] for c in clips), flush=True)
    if not need: return
    clean_plan(E['ep']); os.makedirs(CACHE(E['ep']), exist_ok=True)
    tf = f"{CACHE(E['ep'])}/times_{E['id']}.json"; json.dump(times, open(tf, 'w'))
    page = f"engine/short.html?ep={E['ep']}&clean=1&plan=/shorts/clean_ep{E['ep']}.json"
    r = subprocess.run(['node', f'{ROOT}/tools/render_anim.js', TL[E['ep']], CACHE(E['ep']), str(FPS), '4', '-', f'{2560 / 1080:.7f}', f'page={page}', f'times={tf}', 'warm=1', 'names=ep', 'quality=92'],
                       cwd=ROOT, stdout=open(f"{CACHE(E['ep'])}/render_{E['id']}.log", 'w'), stderr=subprocess.STDOUT)
    if r.returncode != 0: sys.exit('render failed')

if __name__ == '__main__':
    cmd, path = sys.argv[1], sys.argv[2]; E = json.load(open(path))
    if cmd == 'plan':
        T, clips, dur = plan(E); times, need = times_needed(E, clips)
        print(E['id'], f'{dur:.1f} s,', len(clips), 'clips,', len(need), 'frames to render')
    elif cmd == 'render': render(E)
    elif cmd == 'clean':   # free the disk once the short is made: its frames are not shared with the others
        T, clips, dur = plan(E)
        for f in set(f for c in clips for f in c['src']):
            try: os.remove(f"{CACHE(E['ep'])}/f_{f:06d}.jpg")
            except FileNotFoundError: pass
    elif cmd == 'make':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import shorts_make
        shorts_make.make(E, sys.argv[3])
