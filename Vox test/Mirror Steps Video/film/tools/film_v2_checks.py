"""Assembly checks for v2 (DIRECTION_V2 7, rank 5): one labelled 720p still per error number at its fix moment, plus a
contact sheet of all 33.

    python3 tools/film_v2_checks.py [--size 1280x720] [--only 1,5,12]    -> _work/film_v2/errors/errfix_NN.jpg + errors_sheet.jpg

Each still is rendered by film.Film (sets + cast + grade + HUD) at the time below (chosen inside the fixing shots that
plan/shots.json `errors` lists) and carries the error, the fix and the shot in a bar under the picture.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM); os.chdir(FILM)
import numpy as np
import cv2

# error number -> (time, what the still must show)
ERR_T = {
    1: (467.1, 'H2: she glides down onto the bunk, the mattress dips'),
    2: (488.9, 'the 488 wide: Noah knotting, her patting the dip, you half-turned'),
    3: (507.0, 'your candy fist with the wrapper twist'),
    4: (651.8, 'the candy in the palm, the mark beside it'),
    5: (556.5, 'the empty tape loop slides off the lengthened fingers'),
    6: (573.7, 'he rises, the rail slams his shoulder (hit 573.54)'),
    7: (609.1, "Tess's fist on your collar, whip pull, giant 0"),
    8: (513.9, 'the far porch bell swinging by itself, clean rings'),
    9: (535.42, 'the real bell: contact, spark, flash, wobble'),
    10: (464.2, 'the doorway at the top goes navy, no beam'),
    11: (545.8, 'the section: Noah shoved up the stairs to the doorway'),
    12: (590.6, "S4: the jaw void with Noah13's face inside"),
    13: (32.1, 'the key ring with the CABIN 7 tag'),
    14: (1.2, 'one tape design: three fingers, two bands, a lifting edge'),
    15: (690.6, 'the 8th line under the glass on the phone, the click'),
    16: (680.2, 'Tess holds the phone (after 674.4)'),
    17: (646.0, 'the fist trembles and will not open'),
    18: (564.2, 'H5: the face morph 13 -> 27'),
    19: (532.6, 'the face turns on a real three-quarter head (no paper card)'),
    20: (479.6, 'H3: the lips talk while the drawn smile stays'),
    21: (306.8, 'Noah at seated kid scale, feet on the floor'),
    22: (255.3, 'no white half-disc at the left edge'),
    23: (47.4, "phone bubbles fit their text ('check the pocket')"),
    24: (88.2, 'the watch LCD: 6:45 -> 4:45, the finger beside the digits'),
    25: (685.1, 'the 7 steps are on the screen before "count"'),
    26: (284.9, 'H1: she leans out of the doorway at the mirror spot'),
    27: (603.5, 'stairs background only on the stairs (600-606)'),
    28: (73.8, 'the NOAH cubby, empty'),
    29: (565.0, "grown Noah's brown, human eyes"),
    30: (439.1, 'the menu chalkboard, CANCELED'),
    31: (292.2, 'THEIRS: the stairs along the back wall to the raised doorway'),
    32: (72.0, 'the padlock hanging open on the hasp'),
    33: (91.2, 'the mirror reads as glass: reflection, hot spot, frame'),
}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--only', default=None)
    a = ap.parse_args()
    from engine.core import set_render_size
    W, H = (int(v) for v in a.size.split('x'))
    set_render_size(W, H)
    import film as FM
    F = FM.Film()
    out = os.path.join(FILM, '_work', 'film_v2', 'errors')
    os.makedirs(out, exist_ok=True)
    nums = sorted(ERR_T) if not a.only else [int(v) for v in a.only.split(',')]
    tiles = []
    for n in nums:
        t, what = ERR_T[n]
        sh = F.shot_at(t)
        e = F.P['errors'].get(str(n), {})
        ok = sh['id'] in e.get('shots', [])
        t0 = time.time()
        img = cv2.cvtColor(F.frame(t, int(round(t * 60))), cv2.COLOR_RGB2BGR)
        bar = np.full((64, W, 3), 14, np.uint8)
        cv2.putText(bar, 'ERROR %d  %.2f s  %s %s/%s/%s%s' % (n, t, sh['id'], sh['set'], sh['view'], sh['var'], '' if ok else '  (not a listed fix shot)'),
                    (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (120, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(bar, ('v1: %s  ->  v2: %s' % (e.get('error', ''), what))[:150], (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (235, 235, 235), 1, cv2.LINE_AA)
        im = np.vstack([img, bar])
        p = os.path.join(out, 'errfix_%02d.jpg' % n)
        cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(p, sh['id'], '%.1fs' % (time.time() - t0), flush=True)
        tiles.append(cv2.resize(im, (480, int(480 * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA))
        while len(F._built) > 2: F._built.popitem(last=False)
    if not a.only:
        cols = 4; h, w = tiles[0].shape[:2]
        rows = (len(tiles) + cols - 1) // cols
        sheet = np.full((rows * h, cols * w, 3), 10, np.uint8)
        for j, im in enumerate(tiles): sheet[(j // cols) * h:(j // cols + 1) * h, (j % cols) * w:(j % cols + 1) * w] = im
        cv2.imwrite(os.path.join(out, 'errors_sheet.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
        print(os.path.join(out, 'errors_sheet.jpg'))


if __name__ == '__main__':
    main()
