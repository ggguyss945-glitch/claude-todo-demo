"""Before / after strips for the polish pass: the same film times rendered by two copies of the film code (BEFORE: a
directory holding the old film.py / sets_bunny.py / characters_bunny.py next to symlinks to the rest of the film folder;
AFTER: this folder), side by side, a title per problem.

    python3 tools/before_after.py --before /path/to/old/film --out _work/tests/polish/before_after [--size 640x360] [--only 1,4]

Each problem is a list of film times (the new cut list may differ from the old one, so a time is given per side when
the moment moved: (t_before, t_after)). One image per problem: BEFORE row over AFTER row, the line under the pictures.
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBLEMS = [
    ('01_night_windows', 'Night windows read as daytime (living room); now the dark yard / street at night',
     [206.0, 212.3, 213.2, 512.5]),
    ('02_lens_hand', 'The hand over the lens on "close your eyes and count to": a flat pink hand with red lines -> the cast\'s hand, '
     'soft and dark as it nears the glass', [14.2, 14.9, 15.3, 15.9]),
    ('03_porch_switch', 'Porch switch: a floating pointing finger -> Grandma\'s / Mom\'s fingertip lands on the lever and pushes it',
     [(146.0, 145.95), (146.2, 146.2), (150.7, 151.45), (151.0, 151.75)]),
    ('04_grandma_knock', 'Grandma\'s family knock: a bare sleeve and a fist in the air -> her fist (ring, cardigan cuff) on the checked cloth',
     [404.05, 404.25, 405.2, 405.45]),
    ('05_small_scared', '"Small, and scared." was a reaction close-up -> the source: the flap held open from outside, trembling',
     [433.5, 434.2]),
    ('06_attic_corner', '"And from the dark corner ... Back to bed, you two." Mom lit, standing in the open -> a silhouette in the dark '
     'corner, only her eyes in the bulb\'s edge', [581.5, 583.5, 585.0]),
    ('07_under_bridge', '"The real Laurie woke up under a railroad bridge": a flat starfish sprite -> curled on its side on the gravel, '
     'from under the trestle', [817.5, 819.0]),
    ('08_swap', 'The swap: Mom\'s smiling face on "It\'s the easiest thing in the world" and flat overlay hands -> the narrator\'s own '
     'face under Mom\'s scratched hand; June\'s mouth free to count', [786.0, 902.0, 909.0, 911.5]),
    ('09_dress_photo', '"Yellow. Exactly like the one in the photo.": the new dress was not on screen with the photo -> the dress and the '
     '1987 clipping on the same door', [181.5, 185.2, 187.3]),
    ('10_hatchets', 'The three hatchet lines were one composition -> the flight from the side, the blade biting a tread, the drag '
     'along the runner', [620.5, 624.3, 627.0]),
    ('11_sunrise_door', 'At sunrise Mom was never seen at the door -> the reverse from the corridor: her key in the keyhole, the door '
     'swings open', [(735.6, 735.6), (736.3, 736.3)]),
    ('12_parade_photo', 'The parade photo: Laurie and the mascot hidden behind the float -> in front of it, hand in paw, the flash',
     [88.6, 94.0]),
]

ap = argparse.ArgumentParser()
ap.add_argument('--before', required=True)
ap.add_argument('--out', default=os.path.join(HERE, '_work', 'tests', 'polish', 'before_after'))
ap.add_argument('--size', default='640x360')
ap.add_argument('--only', default=None)
ap.add_argument('--render-side', default=None, help=argparse.SUPPRESS)
ap.add_argument('--times', default=None, help=argparse.SUPPRESS)
ap.add_argument('--dst', default=None, help=argparse.SUPPRESS)
a = ap.parse_args()

if a.render_side:
    # child process: render the given times with the film code in cwd (BEFORE or AFTER) into .npy files
    sys.path.insert(0, os.getcwd())
    from engine.core import set_render_size
    W_, H_ = (int(v) for v in a.size.split('x'))
    set_render_size(W_, H_)
    import numpy as np
    import film as FM
    F = FM.Film(json.load(open(os.path.join(FM.ALIGN, 'timeline.json'))))
    os.makedirs(a.dst, exist_ok=True)
    for ts in a.times.split(','):
        t = float(ts)
        img = F.frame(t, int(round(t * FM.FPS)))
        np.save(os.path.join(a.dst, '%s_%08.3f.npy' % (a.render_side, t)), img)
    sys.exit(0)

import numpy as np
import cv2
sel = PROBLEMS if not a.only else [p for k, p in enumerate(PROBLEMS, 1) if str(k) in a.only.split(',')]
tb, ta = [], []
for (_, _, ts) in sel:
    for t in ts:
        b, f = (t if isinstance(t, tuple) else (t, t))
        tb.append(b); ta.append(f)
tmp = os.path.join(a.out, '_npy')
os.makedirs(tmp, exist_ok=True)
me = os.path.abspath(__file__)
procs = [subprocess.Popen([sys.executable, me, '--before', a.before, '--render-side', 'before', '--times', ','.join('%.3f' % x for x in tb),
                           '--dst', tmp, '--size', a.size], cwd=a.before),
         subprocess.Popen([sys.executable, me, '--before', a.before, '--render-side', 'after', '--times', ','.join('%.3f' % x for x in ta),
                           '--dst', tmp, '--size', a.size], cwd=HERE)]
for p in procs: p.wait()
W_, H_ = (int(v) for v in a.size.split('x'))
tl = json.load(open(os.path.join(HERE, '_work', 'align', 'timeline.json')))['lines']


def line_at(t):
    cur = None
    for l in tl:
        if l['t'] - 0.05 <= t: cur = l
    return cur['en'] if cur and t <= cur['end'] + 0.8 else ''


def lab(im, s, col=(255, 255, 255)):
    cv2.putText(im, s, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(im, s, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 1, cv2.LINE_AA)


paths = []
for (name, title, ts) in sel:
    rows = []
    for side, col in (('before', (90, 90, 255)), ('after', (90, 255, 120))):
        tiles = []
        for t in ts:
            b, f = (t if isinstance(t, tuple) else (t, t))
            tt = b if side == 'before' else f
            img = np.load(os.path.join(tmp, '%s_%08.3f.npy' % (side, tt)))
            im = cv2.cvtColor(img, cv2.COLOR_RGB2BGR).copy()
            lab(im, '%s  %.2f s' % (side.upper(), tt), col)
            tiles.append(im); tiles.append(np.full((H_, 6, 3), 255, np.uint8))
        rows.append(np.hstack(tiles[:-1]))
    wmax = max(r.shape[1] for r in rows)
    band_h = 58
    band = np.full((band_h, wmax, 3), 24, np.uint8)
    cv2.putText(band, title[:150], (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 230, 255), 1, cv2.LINE_AA)
    lines = ' / '.join(dict.fromkeys(line_at(t if not isinstance(t, tuple) else t[1]) for t in ts))
    cv2.putText(band, lines[:160], (8, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (235, 235, 235), 1, cv2.LINE_AA)
    sheet = np.vstack([band, rows[0], np.full((8, wmax, 3), 70, np.uint8), rows[1]])
    pth = os.path.join(a.out, name + '.jpg')
    cv2.imwrite(pth, sheet, [cv2.IMWRITE_JPEG_QUALITY, 86]); paths.append(pth)
for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
os.rmdir(tmp)
print('\n'.join(paths))
