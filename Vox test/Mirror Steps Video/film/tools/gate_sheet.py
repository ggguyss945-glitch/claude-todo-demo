"""Gates G1 + G2 for the owner (DIRECTION_V2 7): one combined sheet, _work/gate/gate_sheet.jpg.

    python3 tools/gate_sheet.py [--skip-sets] [--skip-ui]

Rows, all through the film's v2 grades (each cell graded with its world's preset, as in the film):
  A  THE QUEEN at every stage (S0 S1 S2 S3a S3b S3c OFF S4), the full figure front and 3/4, her foot from above (H7),
     her hand with the red fingertips
  B  THE PEOPLE: you, Tess, Noah13, grown Noah (busts and poses)
  C  12 SET STILLS with the cast at the G2 times (72.8 91.0 119.2 147.5 178.0 261.5 290.5 291.5 341.0 512.5 535.4 605.5)
     straight from the v2 plan shots (sets + cast + grade), plus the G1 Queen stills (284.5, 532.2, 605.8 / 606.3)
  D  6 UI DEVICES on the v2 sets: kinetic title, rule card 2, rule card 7, D1 game diagram, D4 floor split, giant number
Cells are 480x270 (the 1920 design frame at 1/4); the sheet is 6 cells wide (2880 px).
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM); sys.path.insert(0, HERE); os.chdir(FILM)
import numpy as np
import cv2
import skia

OUT = os.path.join(FILM, '_work', 'gate')
os.makedirs(OUT, exist_ok=True)
CW, CH, COLS = 480, 270, 6
SKIP_SETS = '--skip-sets' in sys.argv
SKIP_UI = '--skip-ui' in sys.argv


def label(img, text, sub=''):
    im = img.copy()
    cv2.rectangle(im, (0, im.shape[0] - (36 if sub else 20)), (im.shape[1], im.shape[0]), (14, 12, 18), -1)
    cv2.putText(im, text, (6, im.shape[0] - (22 if sub else 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    if sub: cv2.putText(im, sub[:70], (6, im.shape[0] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (170, 190, 255), 1, cv2.LINE_AA)
    return im


def section(title, cells, note=''):
    rows = []
    for i in range(0, len(cells), COLS):
        r = cells[i:i + COLS]
        r = r + [np.full((CH, CW, 3), 12, np.uint8)] * (COLS - len(r))
        rows.append(np.hstack(r))
    bar = np.full((44 if not note else 62, CW * COLS, 3), 10, np.uint8)
    cv2.putText(bar, title, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (120, 220, 255), 2, cv2.LINE_AA)
    if note: cv2.putText(bar, note, (12, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 215), 1, cv2.LINE_AA)
    return np.vstack([bar] + rows)


# ------------------------------------------------------------------ A + B: cast cells (graded, on world plates)
def cast_cells():
    import cast_v2_sheets as CS
    import characters as C
    from engine.core import Pen

    def cell(fn, bg, text):
        surf = skia.Surface(CW, CH); cv = surf.getCanvas()
        CS.plate(cv, CW, CH, bg, seed=hash(text) % 50)
        cv.save(); cv.scale(CW / 1920.0, CH / 1080.0)
        fn(Pen(cv), bg)
        cv.restore()
        a = np.ascontiguousarray(surf.makeImageSnapshot().toarray()[:, :, :3])
        return label(CS.grade_bgr(a, bg), text)

    A = [cell(CS.qbust(st, 0.92, cy=640, **kw), bg, '%s  %s' % (st, nm)) for st, bg, kw, nm in (
        ('S0', 'stairs', {}, 'hidden: crown, collar, hair'), ('S1', 'ours', {}, 'calm, regal, no blink'),
        ('S2', 'ours', {}, 'the drawn stair smile'), ('S3a', 'theirs_q', dict(m_open=0.2), 'it splits: flat teeth, gums'),
        ('S3b', 'theirs_q', dict(m_open=0.15), 'red irises, veined whites'), ('S3c', 'theirs_q', dict(m_open=0.15), 'folds, cracks, black tears'),
        ('OFF', 'theirs_q', {}, 'the smile goes off: scars'), ('S4', 'climax', dict(m_open=0.45), "the jaw void, Noah's face"))]
    A.append(cell(CS.qbody('S1', h=1000, y=1050), 'ours', 'full figure: girdle, pendant, pip hem'))
    A.append(cell(CS.qbody('S2', h=1000, y=1050, turn=0.45), 'theirs_q', '3/4: collar, sheen, train'))
    A.append(cell(CS.actor('queen', lambda a: a.toes_curl(605.21), 'feet', [960, 380, 640], 605.8, view='pov'), 'climax',
                  'H7 her foot from above'))
    A.append(cell(CS.actor('queen', lambda a: a.pat(476.0, 2, 0.32), 'hands', [960, 640, 440], 476.1), 'theirs_q',
                  'hand: black nails, red tips'))
    B = [cell(CS.pbust('you', 'dread', 0.95, cy=600), 'ours', 'you: fear CU'),
         cell(CS.pbust('you', 'neutral', 0.95, cy=600, turn=2.0), 'theirs', 'you: back of the head (OTS)'),
         cell(CS.actor('you', lambda a: (a.set(-1e9, None, 0.01, turn=0.5), a.kneel(1.0), a.grip_frame(1.4)), 'body', [960, 1050, 900], 2.2),
              'ours', 'you: kneel at the mirror'),
         cell(CS.pbust('tess', 'tense', 0.95, cy=600, turn=0.4), 'ours', 'Tess: tense 3/4'),
         cell(CS.actor('tess', lambda a: (a.set(-1e9, None, 0.01, hr_prop='flashlight', hr_shape='grip', beam=1.0), a.run(450.0, 900.0, 470.0)),
                       'body', [700, 1050, 860], 451.135), 'ours', 'Tess: run cycle'),
         cell(CS.pbust('noah13', 'neutral', 0.95, cy=600), 'theirs', 'Noah13: almond eyes, gap teeth'),
         cell(CS.actor('noah13', lambda a: (a.set(-1e9, None, 0.01, turn=0.5), a.sit(0.0), a.tie_loop(0.5)), 'body', [960, 1050, 640], 1.5,
                       under=CS.bunk(868)), 'theirs', 'Noah13: seated kid scale, the knot'),
         cell(CS.pbust('noah_grown', 'shaken', 0.95, cy=600), 'climax', 'grown Noah: brown human eyes'),
         cell(CS.actor('you', lambda a: a.fist(1.0, squeeze=0.8), 'hands', [960, 600, 520], 2.0), 'theirs', 'your candy fist (323.65-649 s)'),
         cell(CS.actor('noah13', lambda a: a.peel_tape(1.0), 'hands', [960, 600, 520], 1.6), 'theirs', 'the one tape design')]
    return A, B


# ------------------------------------------------------------------ C: set stills with the cast (v2 plan shots)
def set_cells():
    from engine import set_render_size
    set_render_size(960, 540)
    from engine.camera import Cam
    from engine.scene import render_frame
    import sets
    import characters as C
    D = json.load(open('plan/shots.json')); SH = D['shots']; S = {s['id']: s for s in SH}

    def at(t):
        b = SH[0]
        for s in SH:
            if s['t0'] <= t: b = s
        return b

    def render(t):
        s = at(t)
        sp = sets.build_shot(s); layers = list(sp)
        for spec in s.get('chars', []):
            spec = dict(spec); spec['at'] = sets.resolve_at(sp, spec)
            try: rig = C.CharRig(spec, s)
            except Exception as e: print('char fail', s['id'], e); continue
            a_ = spec['at']
            d = a_[3] if (isinstance(a_, list) and len(a_) > 3 and spec.get('mode') in ('body', 'legs', 'silhouette')) else 1.0
            layers.append(sets.Layer(d, (lambda r: (lambda pen, tt: r.draw(pen, tt)))(rig), 'char_' + spec['who']))
        cam = Cam([tuple(x) for x in s['cam']['keys']], ease=s['cam'].get('ease', 'lin'))
        img = render_frame(layers, cam.at(t), t, int(t * 60), **sp.render_kw(), post=sp.fx(t))
        bgr = np.ascontiguousarray(img[..., ::-1])
        cv2.imwrite(os.path.join(OUT, 'stills', '%s@%.1f.jpg' % (s['id'], t)), bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return label(cv2.resize(bgr, (CW, CH), interpolation=cv2.INTER_AREA), '%.1f s  %s  %s/%s' % (t, s['id'], s['set'], s['view']),
                     s.get('frame', '')[:70])
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    G2 = [72.8, 91.0, 119.2, 147.5, 178.0, 261.5, 290.5, 291.5, 341.0, 512.5, 535.4, 605.5]
    G1 = [148.9, 198.7, 284.5, 479.6, 532.2, 590.2, 605.8, 606.3]
    c2 = [render(t) for t in G2]
    c1 = [render(t) for t in G1]
    return c2, c1


# ------------------------------------------------------------------ D: UI devices on the v2 sets
def ui_cells():
    from engine.core import set_render_size
    set_render_size(1280, 720)
    import ui_v2_sheet as U

    class R2(U.Renderer):
        def frame(self, t, sid=None, hud=True, extra=None):        # the v2 set (no v1 fallback)
            F = self.F
            k = F.index[sid] if sid else F.idx_at(t)
            sh = F.shots[k]
            if self.cache_k != k:
                F._built.clear()
                B = F.build(k); B.sh = sh
                dl = self.U.doc_layer(sh)
                if dl is not None: B.layers = list(B.layers) + [dl]
                self.B, self.cache_k = B, k
            B = self.B
            from engine.scene import render_frame
            cs = B.cam.at(t)
            fx = F.fx_at(B, t, k)
            if sh['set'] == 'rule_mirror':
                fx = dict(fx); fx['blur'] = 8; fx['dim'] = 0.3
            i = int(round(t * 60))
            img = render_frame(B.layers, cs, t, i, focus=B.focus, dof=B.dof, lens=None, grade=B.grade, post=fx,
                               hud=lambda cv, tt: self.UI.hud(cv, tt, sh, cs, F))
            return self.UI.frame_fx(img, t, sh, i), sh
    R = R2()
    out = []
    for t, sid, nm in ((4.95, 'S006', 'kinetic title: WIPE THE GLASS CLEAN.'), (207.9, None, 'rule card 2 (the mirror)'),
                       (614.3, None, 'rule card 7: red glass, her S3c face'), (99.75, 'S072', 'D1 the game diagram'),
                       (177.2, 'S122', 'D4 THEIR FLOOR | OUR FLOOR'), (349.95, None, "giant 45 -> Tess's ring badge")):
        try:
            img, sh = R.frame(t, sid)
            bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception as e:
            import traceback; traceback.print_exc()
            bgr = np.zeros((720, 1280, 3), np.uint8); sh = {'id': 'ERR'}
        out.append(label(cv2.resize(bgr, (CW, CH), interpolation=cv2.INTER_AREA), '%.2f s  %s  %s' % (t, sh['id'], nm)))
    return out


if __name__ == '__main__':
    t0 = time.time()
    A, B = cast_cells()
    parts = [section('A  THE QUEEN OF SPADES v2: every stage (graded like the film)', A,
                     'S0 hidden > S1 calm and regal > S2 the drawn stair smile > S3a the drawing splits into teeth > S3b red eyes > '
                     'S3c the full face > OFF > S4 the void with Noah inside'),
             section('B  THE PEOPLE (graded like the film)', B)]
    if not SKIP_SETS:
        c2, c1 = set_cells()
        parts.append(section('C  G2: 12 SET STILLS with the cast (v2 plan shots, sets + cast + grade, no HUD)', c2))
        parts.append(section('C2 G1: THE QUEEN in the film (v2 plan shots at 148.9 198.7 284.5 479.6 532.2 590.2 605.8 606.3)', c1))
    if not SKIP_UI:
        parts.append(section('D  UI DEVICES on the v2 sets (HUD drawn by ui_v2 over the graded frame)', ui_cells()))
    sheet = np.vstack(parts)
    p = os.path.join(OUT, 'gate_sheet.jpg')
    cv2.imwrite(p, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(p, sheet.shape[1], 'x', sheet.shape[0], '%.0fs' % (time.time() - t0))
