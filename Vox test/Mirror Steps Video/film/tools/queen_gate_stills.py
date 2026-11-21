"""Gate G1 stills of the Queen v2 in the real film pipeline (sets, camera, grade, HUD) at 284.5, 532.2 and 605.8 s.

    python3 tools/queen_gate_stills.py [--size 1280x720] [--extra]

The v2 shot list is being built in parallel, so this restages the v1 shots at those times (plan/v1/shots_v1.json) with the
v2 Queen as DIRECTION_V2 1.4 describes them, in a patched copy of the plan (_work/cast_v2/gate_plan.json):
  284.5  H1  S128 -> the cabin doorway set (v1 S127's view): she leans out of the gold doorway, S2 drawn smile, talking
             (line 110), her red-fingertip hand on the frame
  532.2  H4  S236 -> the full face S3c turned to the lens (531.9), the THEIRS dawn_queen plate
  605.8  H7  S276 -> your boots on the red-edged tread, her bare foot on the tread below (hit 605.21)
  606.4  H7  (--extra) the tilt up: her S3c face 30 cm away, a hand rising
Output: _work/cast_v2/gate_0284.5.jpg ... and a 2x2 contact sheet gate_stills.jpg.
"""
import argparse, copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
ap = argparse.ArgumentParser()
ap.add_argument('--size', default='1280x720')
ap.add_argument('--extra', action='store_true')
a = ap.parse_args()
W, H = (int(v) for v in a.size.lower().split('x'))
from engine.core import set_render_size                                  # noqa: E402
set_render_size(W, H)
import numpy as np                                                       # noqa: E402
import cv2                                                               # noqa: E402

OUT = os.path.join(FILM, '_work', 'cast_v2')
os.makedirs(OUT, exist_ok=True)
V1 = os.path.join(FILM, 'plan', 'v1', 'shots_v1.json')                   # the v1 shot list (plan/shots.json is now v2)
plan = json.load(open(V1 if os.path.exists(V1) else os.path.join(FILM, 'plan', 'shots.json')))
by = {s['id']: s for s in plan['shots']}


def patch(sid, **kw):
    s = by[sid]
    for k, v in kw.items(): s[k] = v
    return s


# H1 284.5: the doorway (S127's set), she leans out of the gold light; S2 smile drawn, lips speak line 110
s127 = by['S127']
patch('S128', set=s127['set'], view=s127['view'], var=s127['var'], side='ours', grade=s127['grade'], type='CU',
      chars=[dict(who='queen', mode='bust', at=[1010, 600, 0.92], view='front', expr='queen_still', queen=dict(stage='S2'),
                  light=dict(rim='#ffcf8a', side=1, qrim='#ffcf8a', qrim_a=200, qrim2='#7b80c8', qsplit=('#ffcf8a', '#7b80c8')),
                  acts=[[283.48, 'still', {}], [283.73, 'talk', {'line': 110}], [283.5, 'lean_in', {'dur': 2.4, 'amount': 0.25}],
                        [283.5, 'reach', {'side': 1}]])])
# H4 532.2: the full face turns to the lens
patch('S236', chars=[dict(who='queen', mode='bust', at=[960, 560, 1.05], view='front', expr='queen_still', queen=dict(stage='S3c'),
                          acts=[[531.47, 'still', {}], [531.9, 'head_to_lens', {'dur': 0.25}]])])
# H7 605.8: your boots, her foot on the tread below
patch('S276', chars=[dict(who='queen', mode='feet', at=[960, 560, 330], view='pov', expr='queen_still', queen=dict(stage='S3c'),
                          acts=[[605.21, 'toes_curl', {}]]),
                     dict(who='you', mode='feet', at=[960, 1010, 400], view='pov', expr='dread')])
# the tilt up (606.4): her S3c face on the stairs, 30 cm away
patch('S277', set='mirror_world', view=by['S276']['view'], var='red', side='mirror', grade='climax_red',
      chars=[dict(who='queen', mode='bust', at=[960, 600, 1.25], view='front', expr='queen_still', queen=dict(stage='S3c'),
                  acts=[[605.95, 'still', {}], [606.2, 'reach', {'side': -1}]])])
gp = os.path.join(OUT, 'gate_plan.json')
json.dump(plan, open(gp, 'w'))

from film import Film                                                    # noqa: E402
F = Film(plan_path=gp)
ts = [284.5, 532.2, 605.8] + ([606.4] if a.extra else [])
ims = []
for t in ts:
    img = F.frame(t)
    p = os.path.join(OUT, 'gate_%06.1f.jpg' % t)
    cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    ims.append(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(p)
while len(ims) % 2: ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + 2]) for i in range(0, len(ims), 2)]
sheet = np.vstack(rows)
sheet = cv2.resize(sheet, (sheet.shape[1] // 2 * 2 // 1, sheet.shape[0]))
cv2.imwrite(os.path.join(OUT, 'gate_stills.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(os.path.join(OUT, 'gate_stills.jpg'))
