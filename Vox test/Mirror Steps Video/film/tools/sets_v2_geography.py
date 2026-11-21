"""The geography sheet of the v2 sets (DIRECTION_V2 7, check 1): top-down plans of both cabins rendered from the one
room model (Cabin 7 OURS and the other side = the same model flipped), their master wides, the stairs from both ends and
the section through the crossing, labelled.  usage: python3 tools/sets_v2_geography.py [OUT.jpg]"""
import sys, os, json
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, F); os.chdir(F)
import numpy as np, cv2
from engine import set_render_size
set_render_size(960, 540)
import sets, sets_v2 as V
from engine.room3d import Cam3, Xf, v3, ID
from engine.scene import render_frame, Layer
from engine.camera import Cam
out = sys.argv[1] if len(sys.argv) > 1 else '_work/sets_v2/geography_v2.jpg'
D = json.load(open('plan/shots.json')); S = {s['id']: s for s in D['shots']}


def plan(side, var, t):
    st = sets.St({'t0': t, 't1': t + 1, 'props': dict(S['S177']['props'] if side == 'ours' else S['S196']['props'])})
    cx = V.CabinCtx(side, var, st, t)
    sc, info = V.cabin_scene(cx)
    cx.refl_scene = sc
    sc.items = [it for it in sc.items if not (it.name.startswith('roof') or it.tag == 'beams' or it.name in ('bulb', 'nest', 'outside_front',
                                                                                                         'ground_front', 'step'))]
    xf = ID if side == 'ours' else Xf.flip_x(V.W)
    cam = Cam3((V.W / 2, 40.0, V.D / 2), pitch=-89.95, yaw=0.0, fov=18.6)
    lay = Layer(1.0, lambda pen, t: sc.render(pen, cam, xf), 'plan')
    img = render_frame([lay], None, t, 0, grade='night_v2' if side == 'ours' else 'dawn_v2')
    bgr = np.ascontiguousarray(img[..., ::-1])
    labels = ([('left bunk', (0.5, 5.3)), ('clock', (1.15, 6.2)), ('window', (1.82, 6.15)), ('MIRROR = DOORWAY', (2.66, 5.95)),
               ("NOAH'S BUNK", (5.1, 5.3)), ('cubbies (NOAH)', (5.15, 4.5)), ('rules sign', (0.25, 0.9)), ('mattresses', (0.6, 1.3)),
               ('DOOR (padlock)', (4.0, 0.25)), ('moon patch', (2.4, 3.9))] if side == 'ours' else
              [("NOAH'S BUNK", (0.5, 5.3)), ('8 STEPS UP', (1.9, 5.95)), ('DOORWAY 1.8 m up', (2.93, 6.2)), ('window + lantern', (3.78, 6.15)),
               ('clock 6:59', (4.45, 6.2)), ('other bunk', (5.1, 5.3)), ('towel + drop', (3.78, 5.75)), ('shoe', (1.18, 4.6)),
               ('wash-house door', (1.6, 0.25)), ('duffel', (5.0, 3.4))])
    for (txt, (x, z)) in labels:
        px, py = cam.pt(v3(x, 0.0, z))
        px, py = int(px / 2), int(py / 2)
        cv2.putText(bgr, txt, (px - 4 * len(txt), py), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(bgr, txt, (px - 4 * len(txt), py), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    return bgr


def shot(sid, t=None):
    s = S[sid]; t = t or (s['t0'] + s['t1']) / 2
    sp = sets.build_shot(s)
    cam = Cam([tuple(k) for k in s['cam']['keys']])
    img = render_frame(list(sp), cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
    return np.ascontiguousarray(img[..., ::-1])


tiles = [('A. CABIN 7 (OURS) plan, back wall at top', plan('ours', 'night', 120.0)),
         ('B. THE OTHER SIDE (THEIRS) plan = Cabin 7 flipped', plan('theirs', 'dawn', 300.0)),
         ('C. SECTION through the crossing (stairs/section)', shot('S194', 290.3)),
         ('Cabin 7 master wide from the door (S055)', shot('S055')),
         ('THEIRS master from their door (S196)', shot('S196')),
         ('the doorway at the mirror spot (S177)', shot('S177')),
         ('stairs: down from our doorway (S124)', shot('S124')),
         ('stairs: up to the doorway, Tess in it (S381)', shot('S381')),
         ('THEIRS reverse: up the stairs (S226)', shot('S226'))]
H = []
for i in range(0, 9, 3):
    row = []
    for (title, im) in tiles[i:i + 3]:
        im = cv2.resize(im, (800, 450), interpolation=cv2.INTER_AREA)
        cv2.rectangle(im, (0, 0), (800, 30), (20, 18, 28), -1)
        cv2.putText(im, title, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 255), 1, cv2.LINE_AA)
        row.append(im)
    H.append(np.hstack(row))
sheet = np.vstack(H)
hdr = np.full((70, sheet.shape[1], 3), (28, 24, 22), np.uint8)
cv2.putText(hdr, 'GEOGRAPHY v2: one room model. The mirror is the doorway is the staircase; the other side is Cabin 7 flipped left-right, 6:59 AM',
            (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (200, 225, 255), 2, cv2.LINE_AA)
cv2.imwrite(out, np.vstack([hdr, sheet]), [cv2.IMWRITE_JPEG_QUALITY, 90])
print('wrote', out, sheet.shape)
