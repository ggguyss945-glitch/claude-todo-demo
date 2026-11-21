"""Delivery-film sets: stills of every set / variant, a contact sheet and the draw-time bench.

    python3 tools/sets_sheet.py                       # stills (1280x720) + contact sheet -> W/sets/
    python3 tools/sets_sheet.py --only door,lily      # variants whose name contains any of these
    python3 tools/sets_sheet.py --bench               # also time every variant at 2560x1440 (one process, 1 OpenCV thread)
    python3 tools/sets_sheet.py --police              # police-set regression stills (the police film's sets still build)
W = film/_work. Stills are graded through the engine exactly like the film (lens, grade, set fx). Variants that need
people show the set empty (anchors are listed in SETS.md); app screens are drawn over sets.phone_bg('hall').
"""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.join(FILM, '_work', 'sets'))
ap.add_argument('--size', default='1280x720')
ap.add_argument('--only', default=None)
ap.add_argument('--bench', action='store_true')
ap.add_argument('--bench_frames', type=int, default=6)
ap.add_argument('--police', action='store_true')
ap.add_argument('--no_sheet', action='store_true')
a = ap.parse_args()
cv2.setNumThreads(1)

from engine import *                                                     # noqa: E402,F401,F403
from engine import hud as H                                              # noqa: E402
from engine.core import set_render_size                                  # noqa: E402

W0, H0 = (int(v) for v in a.size.split('x'))
set_render_size(W0, H0)
import sets as ST                                                        # noqa: E402
try:
    import characters as CH
    H._hand = CH.hud_phone_hand
except Exception:
    CH = None


def app(screen, t=1.2, bg='hall', **kw):
    def build():
        sp = ST.phone_bg(bg)
        return sp, dict(hud=lambda cv, tt: ST.app_phone(cv, screen, t, 960, 560, 1.25, skin='#c9aa98', **kw), post=dict(dim=0.25))
    return build


def S(fn, **opt):
    def build():
        return fn(), opt
    return build


hz_off = dict(t_off=0.6)
VARIANTS = [
    # name, builder, t, camera (None = home), note
    ('porch_doorbell_van', S(lambda: ST.delivery_porch()), 0.12, None, 'doorbell, 3:07: van at the curb, hazards on'),
    ('porch_doorbell_box_door', S(lambda: ST.delivery_porch(box='door')), 0.12, None, 'the box against the front door (left edge)'),
    ('porch_doorbell_box_boots', S(lambda: ST.delivery_porch(box='boots')), 0.7, None, 'the box next to his boots (hazards off phase)'),
    ('porch_doorbell_ir', S(lambda: ST.delivery_porch(box='door', ir=True)), 0.12, None, 'IR night mode (eyes flash white)'),
    ('porch_doorbell_seat_empty', S(lambda: ST.delivery_porch(box='door', van=dict(driver=False))), 0.12, None, '3:40: driver\'s seat empty'),
    ('porch_doorbell_van_door', S(lambda: ST.delivery_porch(box='door', van=dict(driver=False, door=1.0))), 0.12, None, 'sliding door open'),
    ('porch_doorbell_van_leaving', S(lambda: ST.delivery_porch(box='door', van=dict(drive=('out', 0.0, 4.0, 4.0, 24.0)), hazard=hz_off)), 2.2, None,
     'hazards off, pulling away, headlights off'),
    ('porch_peephole_van', S(lambda: ST.delivery_porch('peephole')), 0.12, None, 'peephole'),
    ('street_van', S(lambda: ST.delivery_street()), 0.12, None, 'house 144 across the street, van at the curb'),
    ('street_van_door_open', S(lambda: ST.delivery_street(van=dict(driver=False, door=1.0))), 0.12, None, 'van door open, seat empty'),
    ('street_memory', S(lambda: ST.memory_porch('street')), 0.12, None, '21 years ago: the wagon, the same van'),
    ('doorway_night', S(lambda: ST.porch_doorway(tod='night')), 0.12, None, 'front door open at 3 AM: the box backlit'),
    ('doorway_memory', S(lambda: ST.memory_porch('doorway')), 0.12, None, '21 years ago: the open door, box, van'),
    ('hall_door_open_far', S(lambda: ST.delivery_hall(door_open=0.85, outside=dict(tod='night', box='door'))), 0.12, 'doorway',
     'the hall view with the front door open'),
    ('sunrise_doorbell', S(lambda: ST.sunrise_porch()), 0.12, None, '6:12: tape cut, box open, no van'),
    ('sunrise_doorway', S(lambda: ST.sunrise_porch('doorway')), 0.12, None, '6:12: mum opens the door'),
    ('sunrise_door_opening', S(lambda: ST.porch_doorway(tod='dawn', door_open=lambda t: min(1.0, t / 2.0) * 0.92)), 0.8, None, 'door swinging in (animated)'),
    ('side_yard', S(lambda: ST.side_yard()), 0.12, None, 'under Lily\'s open window, van light from the street'),
    ('side_yard_closed', S(lambda: ST.side_yard(window_open=False, hazard=False)), 0.12, None, 'window closed, no van light'),
    ('hall_stairs', S(lambda: ST.delivery_hall()), 0.1, None, 'front hall to the door: stairs, side table, key bowl'),
    ('hall_stairs_lamp_dad', S(lambda: ST.delivery_hall(lamp=1.0, bowl='dad')), 0.1, None, 'lamp on, dad\'s keys in the bowl'),
    ('hall_back', S(lambda: ST.hall_back()), 0.1, None, 'from the door into the house (behind you)'),
    ('hall_back_dad_upstairs', S(lambda: ST.hall_back(bowl='dad', upstairs=0.8, hazard=True)), 0.1, None, 'dad\'s keys; mum\'s light upstairs'),
    ('upstairs_crack', S(lambda: ST.upstairs_hall()), 0.1, None, 'Lily\'s door open a crack'),
    ('upstairs_open', S(lambda: ST.upstairs_hall(lily_door=0.9, hazard=True)), 0.1, None, 'her door pushed open: the window'),
    ('lily_room_sleeping', S(lambda: ST.lily_room()), 0.1, None, 'Lily asleep, moon nightlight'),
    ('lily_room_empty', S(lambda: ST.lily_room(window_open=True, bed='empty', hazard=True)), 0.1, None, 'window wide open, bed empty'),
    ('lily_window', S(lambda: ST.lily_room(view='window', hazard=True)), 0.1, None, 'out of her window: side yard, van'),
    ('lily_window_leaving', S(lambda: ST.lily_room(view='window', hazard=dict(t_off=0.5), drive=('out', 0.5, 5.0, -9.0, -32.0))), 3.4, None,
     'hazards stop, the van pulls away'),
]
for n in ('label', 'label_to', 'label_lily', 'tablet_sign', 'tablet_lily', 'key_bowl', 'key_bowl_dad', 'box_keys', 'van_seat', 'hazard_switch'):
    VARIANTS.append(('ins_' + n, S((lambda n_: lambda: ST.insert(n_, police=False))(n)), 0.1, None, 'insert ' + n))
VARIANTS.append(('ins_key_bowl_drop', S(lambda: ST.insert('key_bowl_dad', police=False, prop_kw=dict(drop=0.55))), 0.1, None, 'keys dropping in'))
for scr in ST.APP_SCREENS:
    VARIANTS.append(('app_' + scr, app(scr), 1.2, None, 'app screen ' + scr))
POLICE = [('police_porch_doorbell', S(lambda: ST.porch_doorbell()), 1.0, None, 'police regression'),
          ('police_street_wide', S(lambda: ST.street_wide()), 1.0, None, 'police regression'),
          ('police_hallway', S(lambda: ST.hallway()), 1.0, None, 'police regression'),
          ('police_peephole', S(lambda: ST.porch_peephole()), 1.0, None, 'police regression'),
          ('police_living_room', S(lambda: ST.living_room_window()), 1.0, None, 'police regression'),
          ('police_insert_licence', S(lambda: ST.insert('licence')), 1.0, None, 'police regression')]


def cam_for(sp, mode):
    if mode == 'doorway' and 'doorway_cam' in sp.info:
        return ST.doorway_camera(sp, 0.0, 6.0)
    return hold()


def render(sp, opt, t, cam, i=0):
    kw = sp.render_kw()
    post = dict(sp.fx(t)); post.update(opt.get('post', {}))
    return render_frame(list(sp), cam.at(t), t, i, **kw, post=post, hud=opt.get('hud'))


def label(img, s):
    cv2.rectangle(img, (0, img.shape[0] - 26), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
    cv2.putText(img, s, (8, img.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def main():
    os.makedirs(a.out, exist_ok=True)
    vs = POLICE if a.police else VARIANTS
    if a.only: vs = [v for v in vs if any(k in v[0] for k in a.only.split(','))]
    thumbs, index = [], []
    for name, build, t, cm, note in vs:
        t0 = time.time()
        sp, opt = build()
        img = render(sp, opt, t, cam_for(sp, cm))
        cv2.imwrite(os.path.join(a.out, name + '.jpg'), img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        th = cv2.resize(img[:, :, ::-1], (480, 270), interpolation=cv2.INTER_AREA)
        thumbs.append(label(th.copy(), name)); index.append(dict(name=name, set=sp.name, t=t, note=note, lens=sp.lens,
                                                                   grade=str(sp.grade), anchors=sorted(sp.anchors)))
        print('%-32s %5.2fs  %s' % (name, time.time() - t0, note), flush=True)
    if not a.no_sheet and thumbs:
        cols = 5
        rows = [np.hstack(thumbs[i:i + cols] + [np.zeros_like(thumbs[0])] * (cols - len(thumbs[i:i + cols]))) for i in range(0, len(thumbs), cols)]
        sheet = np.vstack(rows)
        cv2.imwrite(os.path.join(a.out, ('police_' if a.police else '') + 'contact_sheet.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
        json.dump(index, open(os.path.join(a.out, ('police_' if a.police else '') + 'index.json'), 'w'), indent=1)
    if a.bench:
        bench(vs)


def bench(vs):
    """Steady-state seconds per frame at 2560x1440 (caches warm, 1 OpenCV thread), camera pushing in 2.5 %/s."""
    set_render_size(2560, 1440)
    res = []
    for name, build, t, cm, note in vs:
        sp, opt = build()
        base = cam_for(sp, cm).at(t)
        cam = push_in(t, t + 10, base.x, base.y, base.zoom, rate=0.025)
        if cm == 'doorway': cam = cam.snap(t - 1.0, base.fz, 0.001)
        render(sp, opt, t, cam)                                                # warm caches
        ts = []
        for k in range(a.bench_frames):
            tt = t + (k + 1) / 60.0
            t0 = time.perf_counter(); render(sp, opt, tt, cam, k + 1); ts.append(time.perf_counter() - t0)
        res.append(dict(name=name, mean_s=round(float(np.mean(ts)), 3), max_s=round(float(np.max(ts)), 3)))
        print('bench %-32s mean %.3f s  max %.3f s' % (name, res[-1]['mean_s'], res[-1]['max_s']), flush=True)
    json.dump(res, open(os.path.join(a.out, ('police_' if a.police else '') + 'bench_2560.json'), 'w'), indent=1)
    ms = [r['mean_s'] for r in res]
    print('bench: %d variants, mean %.3f s/frame, worst %.3f s (%s); police budget 0.6 s/frame' %
          (len(ms), float(np.mean(ms)), max(ms), res[int(np.argmax(ms))]['name']))


if __name__ == '__main__':
    main()
