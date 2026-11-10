"""Cast v2 design sheets (DIRECTION_V2 §3): the Queen of Spades redesign and the people upgrades, in _work/cast_v2/.

    python3 tools/cast_v2_sheets.py [queen thumb compare you tess noah13 noah_grown hands ...]   (default: all)

Every cell is a miniature 1920x1080 design frame drawn on a world plate (OURS blue-violet night, THEIRS gold, STAIRS
plum, CLIMAX red, MEMORY sepia) with soft bokeh discs, so colours and contrast read as they will in the film. Actions
are frames sampled from real Acting clips at their film times. The queen sheet prints the checks of the brief:
face highlight luma on the OURS / THEIRS / CLIMAX plates and talk_line r on lines 97, 110 and 196.
"""
import os, sys, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
import numpy as np                                                       # noqa: E402
import skia                                                              # noqa: E402
import characters as C                                                   # noqa: E402
from engine.core import Pen, text, hash01                                # noqa: E402

OUT = os.path.join(FILM, '_work', 'cast_v2')
os.makedirs(OUT, exist_ok=True)
CW, CH = 480, 270
PLATES = {  # top, bottom, bokeh discs (DIRECTION_V2 1.2 / 4.7)
    'ours': ('#3a3d6e', '#2b2d57', ['#5a5fa8', '#7b80c8', '#ffd58a']),
    'theirs': ('#e8b97a', '#c48f55', ['#ffcf8a', '#f6b9a0', '#ffe2a8']),
    'stairs': ('#3a2450', '#1a0f26', ['#c63449', '#ffcf8a', '#9fa8ff']),
    'climax': ('#57183d', '#1a0610', ['#c2185b', '#ff2d55', '#ae3a6a']),
    'memory': ('#f1e2c4', '#c9a878', ['#fff3dc', '#f1e2c4', '#e8d2a8']),
    'grey': ('#5a6070', '#3a3f4a', ['#7a8090', '#8a90a0', '#6a7080']),
}
LIGHT = {'ours': 'moon', 'theirs': 'dawn', 'stairs': None, 'climax': 'red', 'memory': None, 'grey': None}


def plate(cv, w, h, key, seed=0):
    top, bot, disc = PLATES[key]
    p = skia.Paint(Shader=skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, h)], [skia.Color4f.FromColor(int(C.col(top))).toColor(),
                                                                                              int(C.col(bot))]))
    cv.drawRect(skia.Rect.MakeWH(w, h), p)
    for i in range(9):
        x = hash01(i, 31 + seed) * w; y = hash01(i, 37 + seed) * h * 0.85; r = (0.04 + 0.09 * hash01(i, 41 + seed)) * w
        c = disc[i % len(disc)]
        cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color=C.col(c, 40 + 30 * hash01(i, 43 + seed)),
                                          MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.08)))


class Sheet:
    def __init__(self, title, cols=4, cw=CW, ch=CH):
        self.title, self.cols, self.cw, self.ch, self.cells = title, cols, cw, ch, []
        self.notes = []

    def add(self, label, fn, bg='ours', span=(1, 1)):
        self.cells.append((label, fn, bg, span))

    def render(self, path):
        grid = {}; place = []; r = c = 0
        for label, fn, bg, (sw, sh) in self.cells:
            while True:
                if c + sw > self.cols: r += 1; c = 0; continue
                if all((r + i, c + j) not in grid for i in range(sh) for j in range(sw)): break
                c += 1
            for i in range(sh):
                for j in range(sw): grid[(r + i, c + j)] = 1
            place.append((r, c, label, fn, bg, sw, sh)); c += sw
        rows = max(k[0] for k in grid) + 1
        top = 56 + 20 * len(self.notes)
        W, H = self.cw * self.cols, self.ch * rows + top
        surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(skia.Color(12, 12, 18))
        text(cv, self.title, W / 2, 34, 800, 20, '#ffffff', 255)
        for i, n in enumerate(self.notes): text(cv, n, W / 2, 58 + 20 * i, 600, 13, '#c8c8d8', 255)
        t_all = time.time()
        for r, c, label, fn, bg, sw, sh in place:
            x0, y0, w, h = c * self.cw, top + r * self.ch, self.cw * sw, self.ch * sh
            cv.save(); cv.translate(x0, y0); cv.clipRect(skia.Rect.MakeWH(w - 2, h - 2))
            plate(cv, w, h, bg, seed=r * 7 + c)
            cv.save(); cv.scale(w / 1920.0, h / 1080.0)
            try:
                fn(Pen(cv), bg)
            except Exception as e:                                       # keep the sheet going, show the error
                import traceback; traceback.print_exc()
                cv.restore(); cv.save()
                text(cv, 'ERR ' + repr(e)[:60], w / 2, h / 2, 700, 12, '#ff5050')
            cv.restore()
            lc = '#101216' if bg in ('theirs', 'memory') else '#ffffff'
            text(cv, label, 8, h - 10, 700, 13, lc, 230, align='left')
            cv.restore()
        surf.makeImageSnapshot().save(path, skia.kPNG)
        print('%s  %dx%d  %.1fs' % (path, W, H, time.time() - t_all))


# ------------------------------------------------------------------ helpers
def qpose(stage='S1', t=1.0, **kw):
    p = C.Pose(); p.mix(C.queen_stage(stage)); p.lock = 1.0; p.t = t
    for k, v in kw.items(): setattr(p, k, v)
    return p


def qbust(stage='S1', scale=0.62, cx=960, cy=560, **kw):
    def fn(pen, bg):
        C.draw_bust(pen, 'queen', cx, cy, scale, qpose(stage, **kw), light=LIGHT[bg], t=kw.get('t', 1.0))
    return fn


def qbody(stage='S1', h=980, x=960, y=1050, **kw):
    def fn(pen, bg):
        C.draw(pen, 'queen', x, y, h, qpose(stage, **kw), light=LIGHT[bg], t=kw.get('t', 1.0))
    return fn


def actor(who, setup, mode, at, t, light='auto', view=None, **pose):
    """A frame of an Acting clip: setup(a) adds the clips; mode body / bust / hands / feet."""
    def fn(pen, bg):
        a = C.Acting(who, seed=5, height=at[2] if mode == 'body' else 700.0)
        setup(a)
        P = a.at(t); P.t = t
        for k, v in pose.items(): setattr(P, k, v)
        L = LIGHT[bg] if light == 'auto' else light
        C.draw_mode(pen, who, mode, at, P, light=L, main=pose.get('_main', 'r') if '_main' in pose else 'r')
    return fn


def face_luma(stage, bg, scale=0.62):
    """99.5th percentile luma of the face region of a bust on a plate (DIRECTION_V2 check: >= 200)."""
    w, h = 640, 360
    surf = skia.Surface(w, h); cv = surf.getCanvas(); plate(cv, w, h, bg)
    cv.save(); cv.scale(w / 1920.0, h / 1080.0)
    C.draw_bust(Pen(cv), 'queen', 960, 560, scale, qpose(stage), light=LIGHT[bg], t=1.0)
    cv.restore()
    a = surf.makeImageSnapshot().toarray()[:, :, :3].astype(np.float32)
    lum = 0.299 * a[:, :, 2] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 0]
    # the face: centre box of the head (scale 0.62 -> head ~372 design px ~ 124 px at 640)
    cx, cy = w // 2, int(560 / 1080 * h)
    box = lum[cy - 45:cy + 40, cx - 35:cx + 35]
    return float(np.percentile(box, 99.5)), float(np.median(box))


def talk_r(line):
    env = C.voice_envelope(); L = C.timeline_line(line)
    if env is None or not L: return float('nan')
    a = C.Acting('queen', seed=1); a.talk_line(L['t'], line)
    ts = np.arange(L['t'] - 0.1, L['end'] + 0.1, 1 / 30.0)
    mo = np.array([a.at(t).m_open for t in ts]); ev = np.array([10 ** (C._env_db(env, t) / 20.0) for t in ts])
    return float(np.corrcoef(mo, ev)[0, 1])


# ------------------------------------------------------------------ the queen
def queen_sheet():
    S = Sheet('THE QUEEN OF SPADES v2 (queen): a playing-card queen in the cast language; one face, stages S0-S4 (DIRECTION_V2 §3)', cols=4)
    lum = {bg: face_luma('S1', bg) for bg in ('ours', 'theirs', 'climax')}
    rs = {li: talk_r(li) for li in (97, 110, 196)}
    S.notes.append('face highlight luma p99.5 (target >= 200): OURS %.0f | THEIRS %.0f | CLIMAX %.0f      talk_line r (target >= 0.8): '
                   'line 97 %.2f | line 110 %.2f | line 196 %.2f' % (lum['ours'][0], lum['theirs'][0], lum['climax'][0], rs[97], rs[110], rs[196]))
    S.notes.append('signature: crown of 5 spade points on a silver band, fan collar, spade beauty mark, lipstick-red right index and middle '
                   'fingertips, spade-pip hem; she never blinks or breathes; outline plum #2b1a2a at 0.75x')
    S.add('S1 the calm face (OURS, 197.7 s)', qbust('S1', 1.15, cy=600), 'ours', (2, 2))
    S.add('S3c the full face (THEIRS, 531.7 s)', qbust('S3c', 1.15, cy=600, m_open=0.15), 'theirs', (2, 2))
    labels = {'S0': 'S0 hidden (3.3 s, 148.4 s)', 'S1': 'S1 calm, no blink', 'S2': 'S2 the drawn stair smile (283.7)', 'S3a': 'S3a it splits: flat teeth (479.2)',
              'S3b': 'S3b red eyes (496.8)', 'S3c': 'S3c folds, cracks, tears (531.7)', 'OFF': 'OFF the smile goes off (533.68)', 'S4': 'S4 the jaw void (589.6)'}
    bgs = {'S0': 'stairs', 'S1': 'ours', 'S2': 'ours', 'S3a': 'theirs', 'S3b': 'theirs', 'S3c': 'theirs', 'OFF': 'theirs', 'S4': 'climax'}
    for st in ('S0', 'S1', 'S2', 'S3a', 'S3b', 'S3c', 'OFF', 'S4'):
        kw = dict(m_open=0.45) if st == 'S4' else {}
        S.add('front  ' + labels[st], qbust(st, 0.66, cy=560, **kw), bgs[st])
    for st in ('S0', 'S1', 'S2', 'S3a', 'S3b', 'S3c', 'OFF', 'S4'):
        kw = dict(m_open=0.45) if st == 'S4' else {}
        S.add('3/4  ' + st, qbust(st, 0.66, cy=560, turn=0.5 if st in ('S1', 'S3a', 'S3c', 'S4') else -0.5, **kw), bgs[st])
    # the head turn: MS of the back of her head, the 130 deg snap in 0.18 s, the hair stays put, the calm face
    def snap(a):
        a.set(-1e9, None, 0.01, turn=2.0, **C.queen_stage('S1')); a.still(190.0); a.head_snap(198.15, 130, 0.18)
    for t in (198.0, 198.21, 198.3, 198.42, 198.62):
        S.add('head turn 130 deg  t=%.2f%s' % (t, '  (hair still)' if 198.2 < t < 198.55 else ''), actor('queen', snap, 'bust', [960, 600, 0.55], t), 'stairs')
    def snap_cu(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('S1')); a.still(190.0)
    S.add('198.55 CU: eyes into the lens', actor('queen', snap_cu, 'bust', [960, 560, 1.05], 198.6), 'stairs')
    # the smile goes off in 2 frames (533.68), then S4
    def off(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('S3c')); a.still(530.0); a.smile_off(533.68, 0.033)
    for t in (533.60, 533.69, 533.72, 534.2):
        S.add('smile off  t=%.2f' % t, actor('queen', off, 'bust', [960, 560, 0.75], t), 'theirs')
    def jaw(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('OFF')); a.still(585.0); a.jaw_drop(589.6, 0.3); a.talk_line(589.6, 249)
    for t in (589.55, 589.75, 590.05, 590.9):
        S.add('S4 jaw drop + Noah13 (line 249)  t=%.2f' % t, actor('queen', jaw, 'bust', [960, 520, 0.8], t), 'climax')
    def s2talk(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('S2')); a.still(280.0); a.talk_line(283.73, 110)
    for t in (283.9, 284.5):
        S.add('S2 talking (line 110): lips move, the drawing does not  t=%.1f' % t, actor('queen', s2talk, 'bust', [960, 560, 0.9], t), 'ours')
    def s3talk(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('S2')); a.still(476.0); a.talk_line(478.2, 196); a.split_open(479.24, 0.12)
    for t in (479.1, 479.4):
        S.add('H3 on "back" the drawing splits  t=%.1f' % t, actor('queen', s3talk, 'bust', [960, 560, 0.9], t), 'theirs')
    # turnaround
    for turn, nm in ((0.0, 'front'), (0.5, '3/4 right'), (-0.5, '3/4 left'), (1.5, 'back 3/4'), (2.0, 'back (S0)')):
        S.add('turnaround %s  (1.12x adult, head 1/7.5)' % nm, qbody('S0' if turn == 2.0 else 'S1', h=1000, turn=turn), 'ours')
    # actions
    def sit(a):
        a.set(-1e9, None, 0.01, **C.queen_stage('S2')); a.still(460.0); a.sit_beside(465.4, 1.2)
    for t in (465.3, 466.0, 466.7):
        S.add('H2 the sit: 1.2 s glide, no bob  t=%.1f' % t, actor('queen', sit, 'body', [960, 1050, 900], t), 'theirs')
    S.add('seated 3/4, patting the dip (488 s)', actor('queen', lambda a: (a.set(-1e9, None, 0.01, sit=1.0, turn=-0.5, **C.queen_stage('S3a')),
                                                                         a.pat(488.0, 2, 0.32)), 'body', [960, 1050, 900], 488.1), 'theirs')
    S.add('calling (576.4 s, S3c)', actor('queen', lambda a: (a.set(-1e9, None, 0.01, **C.queen_stage('S3c')), a.call_silent(576.4, 1.4)),
                                        'bust', [960, 560, 0.7], 577.0), 'climax')
    S.add('climbing the stairs (S0, 6.1 s)', actor('queen', lambda a: (a.set(-1e9, None, 0.01, turn=-0.5, **C.queen_stage('S0')), a.climb(5.0, 0.8)),
                                                 'body', [700, 1050, 820], 6.1), 'stairs')
    S.add('H8 the foot lifts toward an erased step', actor('queen', lambda a: (a.set(-1e9, None, 0.01, turn=0.5, **C.queen_stage('S3c')),
                                                                          a.lift_foot(622.9, 0.3, 2.0)), 'body', [960, 1050, 900], 624.5), 'climax')
    # hands and feet
    S.add('hand through the towel (252.5 s): the press', actor('queen', lambda a: a.press_through_cloth(253.8, 0.8), 'hands', [960, 560, 380], 254.8), 'ours')
    S.add('the pat (475.8 s), red fingertips', actor('queen', lambda a: a.pat(476.0, 2, 0.32), 'hands', [960, 640, 440], 476.1), 'theirs')
    S.add('her hand on the doorway frame (H1)', actor('queen', lambda a: a.set(-1e9, None, 0.01, ir_shape='relaxed', ir_a=200.0),
                                                    'hands', [960, 600, 420], 1.0), 'ours')
    S.add('reaching for your shoulder (H7)', actor('queen', lambda a: a.set(-1e9, None, 0.01, ir_shape='claw', ir_a=160.0, ins_k=1.3),
                                                 'hands', [960, 560, 380], 1.0), 'climax')
    S.add('bare foot sets down on the 8th line (3.3 s)', actor('queen', lambda a: a.step_up(3.6, 'right'), 'feet', [1040, 900, 760], 3.6), 'stairs')
    S.add('H7 her foot on the step below yours (605.2)', actor('queen', lambda a: a.toes_curl(605.21), 'feet', [1040, 900, 760], 605.8), 'climax')
    S.add('H8 the foot hangs over nothing (625.6)', actor('queen', lambda a: a.lift_foot(623.0, 0.32, 2.0), 'feet', [1040, 960, 640], 626.0), 'climax')
    S.render(os.path.join(OUT, 'queen_sheet.png'))


def thumb_sheet():
    """The thumbnail test (DIRECTION_V2 3.1): at 160 px wide a stranger must read crown, collar, red lips, pale face."""
    big = os.path.join(OUT, '_thumb_big.png')
    S = Sheet('thumbnail test: each cell is rendered at 1920x1080 and shown at 160 px wide (crown, collar, red lips, pale face)', cols=4, cw=480, ch=270)
    S.add('S3c bust', qbust('S3c', 0.62, cy=560, m_open=0.1), 'theirs')
    S.add('S1 bust', qbust('S1', 0.62, cy=560), 'ours')
    S.add('full figure S1', qbody('S1', h=1000), 'ours')
    S.add('S4', qbust('S4', 0.62, cy=540, m_open=0.45), 'climax')
    S.render(big)
    import cv2
    im = cv2.imread(big)
    top = 56 + 20 * len(S.notes)
    cells = [im[top + 2:top + 268, i * 480 + 2:(i + 1) * 480 - 2] for i in range(4)]
    smalls = [cv2.resize(cv2.resize(c, (160, 90), interpolation=cv2.INTER_AREA), (480, 270), interpolation=cv2.INTER_NEAREST) for c in cells]
    tiny = [cv2.resize(c, (160, 90), interpolation=cv2.INTER_AREA) for c in cells]
    row_t = np.zeros((90 + 20, 480 * 4, 3), np.uint8)
    for i, t_ in enumerate(tiny): row_t[10:100, i * 480 + 160:i * 480 + 320] = t_
    out = np.vstack([im[:top + 270], row_t, np.hstack(smalls)])
    cv2.putText(out, 'actual 160 px', (8, top + 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(out, '160 px blown up 3x', (8, top + 395), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, 'queen_thumbnail_test.png'), out)
    os.remove(big)
    print(os.path.join(OUT, 'queen_thumbnail_test.png'))


def compare_sheet():
    """Side by side with the references at the same face scale (DIRECTION_V2 7 rank 2 check 4)."""
    import cv2
    K = os.path.join(FILM, '_work', 'ref2', 'sheets')
    refs = [('sib_faces_a.jpg', None), ('keys/st_faces_build.jpg', None), ('vet_faces.jpg', None)]
    rows = []
    for name, _ in refs:
        p = os.path.join(K, name)
        if not os.path.exists(p): continue
        im = cv2.imread(p)
        h = 540; im = cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h))
        rows.append(im[:, :min(im.shape[1], 1920)])
    surf = skia.Surface(1920, 540); cv = surf.getCanvas()
    for i, (st, bg, kw) in enumerate((('S1', 'ours', {}), ('S2', 'ours', {}), ('S3c', 'theirs', dict(m_open=0.15)), ('S4', 'climax', dict(m_open=0.45)))):
        cv.save(); cv.translate(i * 480, 0); cv.clipRect(skia.Rect.MakeWH(478, 540)); plate(cv, 480, 540, bg, i)
        cv.scale(480 / 1920.0, 540 / 1080.0)
        C.draw_bust(Pen(cv), 'queen', 960, 600, 1.0, qpose(st, **kw), light=LIGHT[bg], t=1.0)
        cv.restore()
    ours = cv2.cvtColor(surf.makeImageSnapshot().toarray(), cv2.COLOR_BGRA2BGR)
    W = max([r.shape[1] for r in rows] + [1920])
    pad = lambda im: np.hstack([im, np.full((im.shape[0], W - im.shape[1], 3), 12, np.uint8)]) if im.shape[1] < W else im   # noqa: E731
    out = np.vstack([pad(ours)] + [pad(r) for r in rows])
    cv2.imwrite(os.path.join(OUT, 'queen_vs_references.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(os.path.join(OUT, 'queen_vs_references.jpg'))


SHEETS = {'queen': queen_sheet, 'thumb': thumb_sheet, 'compare': compare_sheet}

if __name__ == '__main__':
    names = sys.argv[1:] or list(SHEETS)
    for n in names:
        SHEETS[n]()
