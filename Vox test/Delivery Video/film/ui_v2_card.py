"""ui_v2_card: the rule card is the mirror (DIRECTION_V2 5.3).

rule_card(cv, rc, e, t, film=None)
    rc = shots.json rule_cards[n-1] (appear, title_at, sentence_end, cut, text, command, reflection, glass)
    e  = the shot's `rule_card` HUD entry (towel_whip, card {width_w, rot, overshoot, settle}, rule_write,
         numeral_stamp {t, scale0, settle, crumbs}, words [[word, t]], underline_at, tape_label, steps_progress,
         reflection, glass, wipe_out, wipe_carry, end)

Choreography (t0 = appear):
    t0 .. t0+0.30   the orange-striped towel is whipped up and out of frame (cloth lag, motion streaks); under it the
                    mirror card (62 % W, -2 deg) settles with a 4 % overshoot in 0.13 s (the glass thud at t0+0.13)
    t0+0.45         "RULE" written in lipstick by the bullet in 0.35 s, then the numeral stamps in at 1.6x and settles
                    to 1.0 in 0.13 s, throwing crumbs
    words           the statement writes word-synced in off-white grease pencil; the command (the *red* words) in
                    lipstick; at underline_at a lipstick underline swipes under the command
    on the card     NOAH'S · CABIN 7 on masking tape on the frame's top edge (kid marker); the 7-step progress
                    staircase bottom right with step n filled; a flashlight hot spot and dust drifting over the glass
    in the glass    her reflection behind the words, closer each card (9 % tiny on the bottom step ... 90 % S3c face),
                    soft and dim: she is IN the glass, the words are ON it; the glass degrades: clean silver (1-2), gold
                    reflection (3-4), a hairline crack (5), three cracks + 30 % red (6), graded red with glowing steps (7)
    wipe_out .. end the finger-wipe smear erases the card left to right (the carry over the next shot is
                    ui_v2.smear_carry)
"""
import math
import numpy as np
import cv2
import skia
from engine.core import (CFG, DW, DH, Pen, col, mix, text, text_width, rrect, rect, oval, poly, smooth, union, minus,
                         clamp, lerp, prog, ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, hash01, noise1)
from ui_v2_letter import (LIP, LIP_DK, LIP_HI, LIP_GLOW, LIP_CORE, CHALK, GREASE, MARKER, paint, blur_mf, sprite, sprite_post,
                          blit, Script, write, wax, marker_line, text_path, soft_shadow, offset_pts, _lipstick_tool,
                          _pencil_tool)

GW, GH, FW = 1110.0, 610.0, 36.0               # glass size and frame width (outer 1182 = 61.6 % W)
CX, CY = 960.0, 528.0
TILT = -2.0
STATE = {1: 'silver', 2: 'silver', 3: 'gold', 4: 'gold', 5: 'crack1', 6: 'crack3', 7: 'red'}
NUMW = {1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR', 5: 'FIVE', 6: 'SIX', 7: 'SEVEN'}
VP = (250.0, -40.0)                            # the stairs' vanishing point inside the glass (glass coords)


def _state(n, e):
    g = (e or {}).get('glass', '')
    if 'red' in g and 'graded' in g: return 'red'
    if 'three' in g: return 'crack3'
    if 'hairline' in g: return 'crack1'
    if 'gold' in g: return 'gold'
    if 'silver' in g: return 'silver'
    return STATE.get(n, 'silver')


# ================================================================================================ the glass
def _glass_palette(st):
    return {'silver': ('#b8c4da', '#7884a0', '#3c445a', None),
            'gold': ('#c4b09a', '#7e6c74', '#3a2e3a', '#ffcf8a'),
            'crack1': ('#c0aa96', '#7a6670', '#382a36', '#ffcf8a'),
            'crack3': ('#ac7c84', '#683a46', '#2a1018', '#ff7a5a'),
            'red': ('#9a3446', '#56101e', '#1e0208', '#ff3b5c')}[st]


def _stairs_scene(c, n, st):
    """The stairs inside the glass: plum treads with glowing red nose strips stepping down to the far gold room,
    our moonlight from above, fog bands."""
    pen = Pen(c)
    x0, y0, x1, y1 = -GW / 2, -GH / 2, GW / 2, GH / 2
    vx, vy = VP
    gold = '#ffcf8a' if st not in ('red',) else '#ff6a50'
    pen.radial(None, vx, vy + 10, 300, [(0, gold, 150 if st != 'silver' else 90), (0.5, gold, 40), (1, gold, 0)], sy=0.7, clip=False)
    room = rect(vx - 70, vy - 52, 140, 104)
    pen.linear(room, vx, vy - 52, vx, vy + 52, [(0, '#ffe2a8'), (1, '#d9a96a')], 0.85 if st != 'silver' else 0.7)
    zs = [1.0 + k * 0.62 for k in range(9)]
    Yb = 360.0
    prev = None
    for k in range(8, -1, -1):
        z = zs[k]
        yk = vy + (Yb - vy) / z
        hw = 600.0 / z
        xl, xr = vx + (-560.0 - vx * 0.0) / z, vx + 560.0 / z
        xl, xr = vx - hw, vx + hw
        if prev is not None:
            py, pl, pr = prev
            tread = poly([(xl, yk), (xr, yk), (pr, py), (pl, py)])
            pen.linear(tread, 0, py, 0, yk, [(0, '#2a1838'), (1, '#3a2450')], 0.95)
        prev = (yk, xl, xr)
    for k in range(8, -1, -1):                       # nose strips last (they glow)
        z = zs[k]
        yk = vy + (Yb - vy) / z; hw = 600.0 / z
        w = 9.0 / z ** 0.7
        breath = 1.0
        c.drawLine(vx - hw, yk, vx + hw, yk, paint('#ff4060', 90, w * 5, blur=w * 2))
        c.drawLine(vx - hw, yk, vx + hw, yk, paint('#c63449', 240, w))
    for side in (-1, 1):                               # the side walls
        wall = poly([(vx + side * 600.0, Yb), (vx + side * 1000.0, Yb + 100), (vx + side * 90, vy - 70), (vx + side * 66, vy - 60)])
        pen.fill(wall, '#1a0f26', 150)
    pen.radial(None, vx - 300, y0 - 80, 520, [(0, '#9fa8ff', 70), (1, '#9fa8ff', 0)], sy=0.6, clip=False)
    for j in range(4):                                 # fog bands
        fy = vy + 40 + j * 60
        pen.radial(None, vx + (j - 1.5) * 120, fy, 380, [(0, '#3a2450', 90), (1, '#3a2450', 0)], sy=0.18, clip=False)


def _tread_y(k):
    vx, vy = VP
    z = 1.0 + k * 0.62
    return vy + (360.0 - vy) / z


def _queen_reflection(c, n, refl, st):
    """Her reflection for card n (glass coords). Full figure on a tread for cards 1-4, a bust for 5-7."""
    try:
        import characters as C
    except Exception:
        return
    stage = (refl or {}).get('stage') or {1: 'S0', 2: 'S1', 3: 'S1', 4: 'S2', 5: 'S2', 6: 'S3b', 7: 'S3c'}[n]
    size = float((refl or {}).get('size') or {1: 0.09, 2: 0.16, 3: 0.25, 4: 0.3, 5: 0.45, 6: 0.65, 7: 0.9}[n])
    P = C.Pose(); P.mix(C.queen_stage(stage)); P.lock = 1.0; P.t = 1.0
    light = {'silver': None, 'gold': 'dawn', 'crack1': 'dawn', 'crack3': 'red', 'red': 'red'}[st]
    pen = Pen(c)
    vx, vy = VP
    if n <= 4:
        h = size * GH
        k_tread = {1: 8, 2: 5, 3: 2.6, 4: 2.2}[n]
        yf = _tread_y(k_tread)
        x = vx + {1: 0, 2: -20, 3: 0, 4: -30}[n]
        if n == 3:                                     # standing in the gold doorway light
            pen.radial(None, x, yf - h * 0.5, h * 1.1, [(0, '#ffd590', 170), (0.5, '#ffb850', 70), (1, '#ffb850', 0)], sy=1.3, clip=False)
        if n == 2:
            P.turn = 0.5; P.h_turn = -0.5
        if n == 1:
            P.turn = 1.5
        if n == 4:
            P.sit = 1.0
            ys = yf - h * 0.27                               # she sits on a tread: its nose strip under her
            pen.linear(rect(x - h * 0.7, ys, h * 1.4, h * 0.27), 0, ys, 0, yf, ['#3a2450', '#22142e'], 0.9)
            c.drawLine(x - h * 0.7, ys, x + h * 0.7, ys, paint('#ff4060', 90, 10))
            c.drawLine(x - h * 0.7, ys, x + h * 0.7, ys, paint('#c63449', 240, 4))
            yf -= h * 0.02
        c.drawOval(skia.Rect.MakeLTRB(x - h * 0.22, yf - h * 0.03, x + h * 0.22, yf + h * 0.03), paint('#000000', 120, None, blur=h * 0.03))
        try:
            C.draw(pen, 'queen', x, yf, h, P, light=light, t=1.0)
        except Exception:
            pass
    else:
        sc = {5: 0.30, 6: 0.44, 7: 0.80}[n]
        cx_ = {5: 210.0, 6: 150.0, 7: 0.0}[n]
        cy_ = {5: 30.0, 6: 50.0, 7: 70.0}[n]
        try:
            C.draw_bust(pen, 'queen', cx_, cy_, sc, P, light=light, t=1.0)
        except Exception:
            pass


def _refl_post(dark):
    def post(arr, k):
        out = cv2.GaussianBlur(arr, (0, 0), 1.6 * k)
        return (out.astype(np.float32) * dark).astype(np.uint8)
    return post


def _glass_back(n, refl, st):
    """Glass base gradient + the stairs scene + her reflection, softened (blur) and dimmed: the IN-glass layer."""
    top, mid, bot, warm = _glass_palette(st)

    def draw(c):
        pen = Pen(c)
        g = rect(-GW / 2, -GH / 2, GW, GH)
        pen.linear(g, -GW / 2, -GH / 2, GW / 2, GH / 2, [(0, top), (0.45, mid), (1, bot)])
        c.save(); c.clipPath(g, skia.ClipOp.kIntersect, True)
        c.saveLayerAlpha(skia.Rect.MakeLTRB(-GW / 2, -GH / 2, GW / 2, GH / 2), int(255 * {'silver': 0.55, 'gold': 0.66, 'crack1': 0.7, 'crack3': 0.8, 'red': 0.84}[st]))
        _stairs_scene(c, n, st)
        c.restore()
        _queen_reflection(c, n, refl, st)
        pen.linear(g, 0, -GH / 2, 0, GH / 2, [(0, '#e8eef8', 46), (0.35, '#e8eef8', 0), (1, '#000000', 40)])
        # our room reflected: the window's moon shaft and a bunk rail, faint
        pen.fill(poly([(-GW / 2 + 60, -GH / 2), (-GW / 2 + 230, -GH / 2), (-GW / 2 + 120, GH / 2), (-GW / 2 - 60, GH / 2)]), '#9fb0ff', 16)
        c.restore()
    dark = {'silver': 0.93, 'gold': 0.94, 'crack1': 0.92, 'crack3': 0.88, 'red': 0.9}[st]
    return sprite_post(('cardback', n, st), (-GW / 2, -GH / 2, GW / 2, GH / 2), draw, 0.75, _refl_post(dark))


def _crack(c, pts, w, a=255):
    p = poly(pts, False)
    c.drawPath(p, paint('#ffffff', 0.25 * a, w * 5, blur=w * 2))
    c.drawPath(p, paint('#05070a', 0.8 * a, w * 2.4))
    q = poly([(x + 1.5, y - 1.2) for x, y in pts], False)
    c.drawPath(q, paint('#ffffff', 0.95 * a, w * 1.0))


def _crack_path(x, y, ang, L, seed, n=9):
    pts = [(x, y)]
    for i in range(n):
        ang += (hash01(i, seed) - 0.5) * 34
        d = L / n * (0.6 + 0.8 * hash01(i, seed + 1))
        x += d * math.cos(math.radians(ang)); y += d * math.sin(math.radians(ang))
        pts.append((x, y))
    return pts


def _glass_front(n, st, refl):
    """ON the glass: sheen bands, desilvering at the edges, dust, cracks, the red grade (7), the 7-step progress
    staircase, the frame and its tape label."""
    def draw(c):
        pen = Pen(c)
        x0, y0, x1, y1 = -GW / 2, -GH / 2, GW / 2, GH / 2
        g = rect(x0, y0, GW, GH)
        c.save(); c.clipPath(g, skia.ClipOp.kIntersect, True)
        for j, (sx_, w_, a_) in enumerate(((-380, 120, 40), (-240, 46, 30), (280, 80, 26))):
            band = poly([(sx_ + 160, y0 - 20), (sx_ + 160 + w_, y0 - 20), (sx_ - 240 + w_, y1 + 20), (sx_ - 240, y1 + 20)])
            pen.fill(band, '#ffffff', a_)
        pen.radial(g, 0, 0, 760, [(0, '#000000', 0), (0.6, '#000000', 0), (1, '#000000', 80)], sy=0.62)
        for j in range(60):                            # desilvering: the old mirror's edges
            e_ = j % 4; u = hash01(j, 11)
            if e_ < 2: px, py = (x0 + 70 * hash01(j, 12) ** 2 if e_ == 0 else x1 - 70 * hash01(j, 12) ** 2), y0 + u * GH
            else: px, py = x0 + u * GW, (y0 + 50 * hash01(j, 12) ** 2 if e_ == 2 else y1 - 50 * hash01(j, 12) ** 2)
            rr = 3 + 16 * hash01(j, 13) ** 2
            c.drawOval(skia.Rect.MakeLTRB(px - rr, py - rr * 0.8, px + rr, py + rr * 0.8), paint('#8a929c', 70 + 60 * hash01(j, 14)))
            c.drawCircle(px, py, rr * 0.4, paint('#1a1d22', 110))
        pen.texture(g, 'grunge', 0.10, 'screen', 1.2)
        for j in range(5):                             # finger smudges
            px, py = x0 + (0.15 + 0.7 * hash01(j, 40)) * GW, y0 + (0.2 + 0.6 * hash01(j, 41)) * GH
            pen.radial(None, px, py, 60, [(0, '#c8d2dc', 20), (1, '#c8d2dc', 0)], sy=0.7, clip=False)
        if st in ('crack1', 'crack3', 'red'):
            if st == 'crack1':
                _crack(c, _crack_path(x1 - 20, y0 + 30, 158, 640, 5, 12), 1.6)
                _crack(c, _crack_path(x1 - 220, y0 + 110, 120, 120, 9, 4), 1.1)
            else:
                ix, iy = 330.0, -170.0
                for j, (ang, L) in enumerate(((175, 700), (110, 420), (230, 380), (20, 260), (300, 200))):
                    if st == 'crack3' and j > 2: continue
                    _crack(c, _crack_path(ix, iy, ang, L, 20 + j, 10), 1.8)
                    bx, by = _crack_path(ix, iy, ang, L * 0.5, 20 + j, 5)[-1]
                    _crack(c, _crack_path(bx, by, ang + 40, L * 0.22, 40 + j, 4), 1.1)
                for r_ in (28, 56):
                    pts = [(ix + r_ * math.cos(math.radians(a)) * (1 + 0.15 * hash01(i, 7)), iy + r_ * math.sin(math.radians(a)) * (1 + 0.15 * hash01(i, 8)))
                           for i, a in enumerate(range(0, 361, 30))]
                    _crack(c, pts, 1.0, 200)
                c.drawCircle(ix, iy, 8, paint('#ffffff', 160))
        if st == 'crack3':
            pen.fill(g, '#c2185b', 60)
        if st == 'red':
            pen.radial(g, 0, 60, 820, [(0, '#ff2d55', 80), (0.7, '#ae3a6a', 50), (1, '#1a0610', 140)], sy=0.7)
        c.restore()
        # the 7-step progress staircase (on the glass, bottom right)
        bx, by = x1 - 238, y1 - 44
        for j in range(7):
            sx_, sy_ = bx + j * 28, by - j * 16
            if j + 1 < n:
                wax(pen, [(sx_, sy_), (sx_ + 22, sy_)], 6, 0.5, 0.0, j, crumbs=False)
                wax(pen, [(sx_ + 22, sy_), (sx_ + 22, sy_ - 16)], 4, 0.4, 0.0, j + 9, crumbs=False)
            elif j + 1 == n:
                c.drawOval(skia.Rect.MakeLTRB(sx_ - 6, sy_ - 12, sx_ + 30, sy_ + 10), paint(LIP_GLOW, 110, None, blur=8))
                wax(pen, [(sx_, sy_), (sx_ + 22, sy_)], 8, 1.0, 0.6, j)
                wax(pen, [(sx_ + 22, sy_), (sx_ + 22, sy_ - 16)], 5, 1.0, 0.6, j + 9)
            else:
                c.drawLine(sx_, sy_, sx_ + 22, sy_, paint('#aeb6c2', 110, 3))
                c.drawLine(sx_ + 22, sy_, sx_ + 22, sy_ - 16, paint('#aeb6c2', 90, 2))
        text(c, '%d / 7' % n, bx + 96, by + 30, 800, 15, '#d8dde6', 170, 0.2, 'center')
        # the frame
        _frame(c)
        # the tape label on the top edge
        _tape(c, -300.0, y0 - FW / 2, "NOAH'S · CABIN 7")
    return sprite(('cardfront', n, st), (-GW / 2 - FW - 60, -GH / 2 - FW - 70, GW / 2 + FW + 60, GH / 2 + FW + 60), draw, 1.0)


def _frame(c):
    try:
        import sets as ST
        ST.mirror_frame(Pen(c), -GW / 2, -GH / 2, GW / 2, GH / 2, FW, 1.0, 0.9, night=False)
        return
    except Exception:
        pass
    pen = Pen(c)
    outer = rect(-GW / 2 - FW, -GH / 2 - FW, GW + 2 * FW, GH + 2 * FW)
    pen.fill(minus(outer, rect(-GW / 2, -GH / 2, GW, GH)), '#d8d4c8')
    pen.line(outer, 4)


def _tape(c, x, y, label):
    pen = Pen(c)
    c.save(); c.translate(x, y); c.rotate(-3.0)
    w, h = 340.0, 58.0
    pts = [(-w / 2 + 6 * hash01(i, 3), -h / 2 + i * h / 6) for i in range(7)] + [(w / 2 - 6 * hash01(i, 4), h / 2 - i * h / 6) for i in range(7)]
    tape = poly(pts)
    soft_shadow(c, tape, 120, 6, 2, 4)
    pen.fill(tape, '#e6d6a8', 245)
    pen.texture(tape, 'paper', 0.35, 'multiply', 0.6)
    pen.linear(tape, 0, -h / 2, 0, h / 2, [(0, '#ffffff', 40), (1, '#000000', 30)])
    sc = Script(label, 0, 14, 27, seed=17, slant=0.06, track=0.2, align='center', wob=0.035)
    write(pen, sc, 'marker', 1.0, 255, tip=False)
    c.restore()


# ================================================================================================ the words
def _tokens(s):
    out, red = [], False
    for part in s.split('*'):
        for w in part.split():
            if out and all(ch in '.,!?;:' for ch in w): out[-1][0] += w
            else: out.append([w, red])
        red = not red
    return out


STMT_SIZE, STMT_W, STMT_LH = 58.0, 960.0, 78.0


def _layout(rc, e):
    toks = _tokens(rc['text'])
    wts = [w_[1] for w_ in (e.get('words') or [])]
    if len(wts) != len(toks):
        ws, we = rc['title_at'] + 0.9, rc['sentence_end']
        wts = [ws + (we - ws) * j / max(1, len(toks)) for j in range(len(toks))]
    size, sp = STMT_SIZE, 0.02
    space = text_width(' ', 800, size, sp) + 8
    lines, cur, curw = [], [], 0.0
    for j, (w_, red) in enumerate(toks):
        ww = text_width(w_.upper(), 900 if red else 800, size, sp)
        if cur and curw + space + ww > STMT_W:
            lines.append((cur, curw)); cur, curw = [], 0.0
        curw = curw + space + ww if cur else ww
        cur.append((j, w_.upper(), red, ww))
    if cur: lines.append((cur, curw))
    out = []
    n = len(lines)
    ly0 = {1: 40.0, 2: 6.0, 3: -30.0}.get(n, -30.0)
    for li, (ws_, lw) in enumerate(lines):
        xx = -lw / 2; yy = ly0 + li * STMT_LH
        for (j, w_, red, ww) in ws_:
            nxt = wts[j + 1] if j + 1 < len(wts) else rc['sentence_end']
            out.append(dict(j=j, w=w_, red=red, ww=ww, x=xx, y=yy, t=wts[j], dur=clamp(nxt - wts[j], 0.10, 0.26)))
            xx += ww + space
    return out, size, sp


def _word_sprite(n, j, w, red, size, sp, hot=False):
    ww = text_width(w, 900 if red else 800, size, sp)

    def draw(c):
        path, _ = text_path(w, 0, 0, 900 if red else 800, size, sp)
        c.drawPath(path, paint('#000000', 170, None, blur=9))
        if red:
            c.drawPath(path, paint(LIP_GLOW, 60, None, blur=10))
            c.drawPath(path, paint(LIP_DK, 255, 4))
            Pen(c).linear(path, 0, -size * 0.74, 0, 0, [(0, '#ffe2e8'), (0.5, '#ff7a90'), (1, '#e0304c')] if hot else [(0, '#f04a62'), (0.55, '#d22e46'), (1, '#9a1a2e')])
            c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
            for k in range(8):
                yy = -size * 0.72 + k * size * 0.1
                c.drawLine(0, yy, ww, yy + 3, paint(LIP_DK if k % 2 else '#ff8a98', 45, size * 0.025))
            Pen(c).linear(rect(-10, -size * 0.76, ww + 20, size * 0.14), 0, -size * 0.76, 0, -size * 0.62, [(0, '#ffd0d6', 120), (1, '#ffd0d6', 0)])
            c.restore()
        else:
            q = skia.Path(path); q.offset(0, 3)
            c.drawPath(q, paint('#141820', 200))
            pp = paint(GREASE, 250); pp.setPathEffect(skia.DiscretePathEffect.Make(3.0, 0.7, 5 + j))
            c.drawPath(path, pp)
            c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
            Pen(c).texture(rect(-10, -size, ww + 20, size * 1.3), 'grunge', 0.35, 'multiply', 0.9)
            c.restore()
    return sprite(('cw', n, j, w, red, hot), (-26, -size - 26, ww + 30, size * 0.4 + 26), draw, 1.0), ww


def _words(cv, rc, e, t, n, wipe_clip=None):
    lay, size, sp = _layout(rc, e)
    pen = Pen(cv)
    tool = None
    for d in lay:
        u = (t - d['t'] + 0.05) / d['dur']
        if u <= 0: continue
        spr, ww = _word_sprite(n, d['j'], d['w'], d['red'], size, sp, hot=(n == 7))
        k = clamp(u)
        cv.save(); cv.translate(d['x'], d['y'])
        if k < 1:
            cv.clipRect(skia.Rect.MakeLTRB(-30, -size - 30, ww * k + 4, size * 0.5 + 30))
        blit(cv, spr, 255)
        cv.restore()
        if k < 1: tool = (d['x'] + ww * k, d['y'] - size * 0.25, d['red'])
    # the command underline
    ua = e.get('underline_at')
    reds = [d for d in lay if d['red']]
    if ua is not None and reds and t >= ua:
        k = ease_out_cubic(clamp((t - ua) / 0.16))
        rows = {}
        for d in reds: rows.setdefault(d['y'], []).append(d)
        for yy, ds in rows.items():
            xa = min(d['x'] for d in ds) - 10; xb = max(d['x'] + d['ww'] for d in ds) + 18
            xe = lerp(xa, xb, k)
            pts = [(lerp(xa, xe, i / 18), yy + 20 + 5 * math.sin(i * 0.7) - i * 0.5) for i in range(19)]
            wax(pen, pts, 13, 1.0, 0.35, seed=int(yy))
            if k < 1: tool = (xe, yy + 20, True)
    if tool is not None:
        x, y, red = tool
        if red: _lipstick_tool(pen, x, y, 0, 70, 255)
        else: _pencil_tool(pen, x, y, 72, 255)


# ================================================================================================ title and numeral
TITLE_SIZE, NUM_SIZE = 112.0, 150.0


def _title_layout(n):
    sc = Script('RULE', 0, 0, TITLE_SIZE, seed=40 + n, slant=0.07, track=0.26, wob=0.018)
    tw = sc.width
    numw = 0.62 * NUM_SIZE
    total = tw + 80 + numw
    x0 = -total / 2
    yb = -150.0
    sc = Script('RULE', x0, yb, TITLE_SIZE, seed=40 + n, slant=0.07, track=0.26, wob=0.018)
    nx = x0 + tw + 80 + numw / 2
    return sc, (nx, yb + 8)


def _numeral(cv, n, u, nx, ny, glow):
    """The numeral stamped in lipstick: 1.6x -> 1.0 in 0.13 s, a print halo and crumbs flying."""
    if u < 0: return
    pen = Pen(cv)
    k = clamp(u / 0.13)
    sc = lerp(1.6, 1.0, ease_out_cubic(k)) if k < 1 else 1.0
    a = 255 * clamp(u / 0.03)
    if k >= 0.6:                                         # the smudged print round the numeral
        cv.drawOval(skia.Rect.MakeLTRB(nx - 95, ny - 170, nx + 95, ny + 20), paint('#c86070', 34 * clamp((u - 0.08) / 0.1), None, blur=18))
    cv.save(); cv.translate(nx, ny); cv.scale(sc, sc)
    s = Script(str(n), 0, 0, NUM_SIZE, seed=60 + n, slant=0.06, align='center', wob=0.016)
    write(pen, s, 'lipstick', 1.0, a, tip=False, glow=glow, w=NUM_SIZE * 0.2)
    cv.restore()
    if k >= 1 and u < 0.6:                               # crumbs thrown out on impact
        q = u - 0.13
        for i in range(16):
            ang = hash01(i, 77 + n) * 2 * math.pi
            v = 140 + 260 * hash01(i, 78 + n)
            px = nx + math.cos(ang) * v * q
            py = ny - 70 + math.sin(ang) * v * q + 900 * q * q
            r = 2.0 + 4.5 * hash01(i, 79 + n)
            cv.drawCircle(px, py, r, paint(LIP_DK if i % 3 else LIP, 230 * (1 - q / 0.47)))


# ================================================================================================ towel
def _towel(cv, k):
    """The orange-striped towel covering the card at t0, whipped up and out over 0.30 s (k 0..1)."""
    if k >= 1: return
    pen = Pen(cv)
    W, Hh = GW + 2 * FW + 160, GH + 2 * FW + 140
    lift = ease_in_cubic(k) * 1500.0
    lag = math.sin(min(1.0, k * 1.3) * math.pi) * 220 * (1 - k * 0.3)
    top = -Hh / 2 - lift
    bot = Hh / 2 - lift * 0.82 + lag * 0.3
    rot = 9.0 * ease_in_cubic(k)
    cv.save(); cv.rotate(rot)
    path = smooth([(-W / 2, top), (0, top - 30 * k), (W / 2, top), (W / 2 + 30 * k, (top + bot) / 2), (W / 2, bot),
                   (W / 4, bot + lag * 0.6), (0, bot + lag), (-W / 4, bot + lag * 0.7), (-W / 2, bot), (-W / 2 - 20 * k, (top + bot) / 2)], True, 0.5)
    if k > 0.05:
        for j in (1, 2):
            q = skia.Path(path); q.offset(0, 60 * j * k)
            cv.drawPath(q, paint('#d8945a', 50 / j))
    soft_shadow(cv, path, 170, 24, 0, 14)
    pen.fill(path, '#efe6d6')
    cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
    y = top - 40; i = 0
    while y < bot + lag + 60:
        sw = 52.0 * (0.55 if i % 4 == 0 else 1.0) * (1 + 0.25 * k)
        if i % 2 == 0: pen.fill(rect(-W, y, W * 2, sw), '#df9a58')
        y += sw; i += 1
    pen.texture(path, 'fabric', 0.55, 'overlay', 0.9)
    for j in range(6):
        fx = -W / 2 + (0.1 + 0.8 * hash01(j, 3)) * W
        pen.linear(rect(fx - 40, top, 80, bot - top + lag + 40), fx - 40, 0, fx + 40, 0, [(0, '#000000', 0), (0.5, '#000000', 70), (1, '#000000', 0)])
    pen.linear(rect(-W, bot - 60, W * 2, lag + 120), 0, bot - 60, 0, bot + lag, [(0, '#000000', 0), (1, '#000000', 80)])
    cv.restore()
    cv.drawPath(path, paint('#3a2414', 220, 4))
    cv.restore()


# ================================================================================================ the card
def _card_static(n, st, refl, tilt):
    back = _glass_back(n, refl, st)
    front = _glass_front(n, st, refl)
    M = GW / 2 + FW + 90

    def draw(c):
        c.rotate(tilt)
        soft_shadow(c, rect(-GW / 2 - FW, -GH / 2 - FW, GW + 2 * FW, GH + 2 * FW), 200, 40, 0, 26)
        c.save(); c.clipPath(rect(-GW / 2, -GH / 2, GW, GH), skia.ClipOp.kIntersect, True)
        blit(c, back, 255)
        c.restore()
        blit(c, front, 255)
    return sprite(('cardstatic', n, st, round(tilt, 2)), (-M, -GH / 2 - FW - 110, M, GH / 2 + FW + 110), draw, 1.0)


def _settle(u, dur=0.13, over=0.04):
    """Scale and y of the card settling after the towel's yank: 0.97 -> 1 + over (at 45 %) -> 1.0 in dur."""
    if u >= dur: return 1.0, 0.0
    k = u / dur
    if k < 0.45:
        q = ease_out_cubic(k / 0.45); return lerp(0.97, 1.0 + over, q), lerp(16.0, -6.0, q)
    q = ease_in_out((k - 0.45) / 0.55); return lerp(1.0 + over, 1.0, q), lerp(-6.0, 0.0, q)


def rule_card(cv, rc, e, t, film=None):
    t0 = float(e.get('appear', rc.get('appear', e['t'])))
    cut = float(e.get('end', rc.get('cut', t0 + 4)))
    u = t - t0
    if u < 0 or t >= cut + 0.02: return
    n = int(e.get('n', rc.get('n', 1)))
    st = _state(n, e if e.get('glass') else rc)
    refl = e.get('reflection') or rc.get('reflection')
    cd = e.get('card') or {}
    over = float(cd.get('overshoot', 0.04)); settle = float(cd.get('settle', 0.13))
    tilt = float(cd.get('rot', TILT))
    wscale = float(cd.get('width_w', 0.62)) * DW / (GW + 2 * FW)
    pen = Pen(cv)
    s_, dy = _settle(u, max(settle, 0.34), min(over, 0.015))      # a soft settle (the 0.13 s bounce read as a camera jerk)
    drift = 1.0 + 0.010 * u                                    # the card keeps moving
    glow = 0.65 if st == 'red' else 0.0
    # review round 2 (M12): the card enters with the flow (the dolly into the mirror): it fades up and grows out of the
    # depth over the flow's 0.28 s instead of appearing whole in one frame, and the towel is already flying when it shows
    ent = ease_out_cubic(clamp(u / 0.28))
    ent_layer = ent < 0.999
    if ent_layer: cv.saveLayer(None, skia.Paint(Alphaf=float(ent)))
    # dim vignette round the card (the plate is already blurred and dimmed by the shot's bg post)
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#000000', 40))
    S = s_ * drift * wscale * (0.82 + 0.18 * ent)
    cv.save(); cv.translate(CX, CY + dy); cv.scale(S, S)
    # the static card (shadow, IN-glass reflection, ON-glass sheen / cracks / staircase, frame, tape) as ONE sprite with the
    # tilt baked in, blitted axis-aligned: a rotated full-card blit costs ~0.1 s per frame at 2560
    blit(cv, _card_static(n, st, refl, tilt), 255)
    # the flashlight hot spot sliding over the silvering (rotation-free blob: placed by hand, clipped to the tilted glass)
    gl = rect(-GW / 2, -GH / 2, GW, GH)
    m = skia.Matrix(); m.setRotate(tilt); glr = skia.Path(gl); glr.transform(m)
    cv.save(); cv.clipPath(glr, skia.ClipOp.kIntersect, True)
    hx = -260 + 180 * math.sin(u * 0.55) + 60 * u; hy = -120 + 40 * math.sin(u * 0.8)
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    spot = sprite(('cardspot2',), (-560, -450, 560, 450),
                  lambda c: Pen(c).radial(None, 0, 0, 520, [(0, '#fff3d6', 70), (0.45, '#ffe6b8', 26), (1, '#ffffff', 0)], sy=0.8, clip=False), 0.25)
    cv.save(); cv.translate(hx * ca - hy * sa, hx * sa + hy * ca); blit(cv, spot, 230); cv.restore()
    if st == 'red':                                            # the climax pulse (1.2 s)
        pr = 0.5 + 0.5 * math.sin(2 * math.pi * u / 1.2)
        cv.drawPath(glr, paint('#ff2d55', 22 * pr))
    cv.restore()
    cv.rotate(tilt)
    p = skia.Path()                                            # dust drifting in the beam
    for j in range(30):
        dx_ = -GW / 2 + ((hash01(j, 21) * GW + u * (14 + 20 * hash01(j, 22))) % GW)
        dy_ = -GH / 2 + ((hash01(j, 23) * GH - u * (6 + 10 * hash01(j, 24))) % GH)
        r = 1.4 + 1.6 * hash01(j, 25)
        p.addOval(skia.Rect.MakeLTRB(dx_ - r, dy_ - r, dx_ + r, dy_ + r))
    cv.drawPath(p, paint('#ffffff', 120))
    # the writing (clipped by the exit wipe)
    wo = float(e.get('wipe_out', rc.get('sentence_end', cut - 0.2) + 0.15))
    wipe = clamp((t - wo) / max(0.05, cut - wo))
    if wipe > 0:
        wx = lerp(-GW / 2 - 260, GW / 2 + 260, ease_in_out(wipe))
        cv.save(); cv.clipPath(poly([(wx + 120, -GH), (GW, -GH), (GW, GH), (wx - 120, GH)]), skia.ClipOp.kIntersect, True)
    ta = float(e.get('title_at', rc.get('title_at', t0 + 0.45)))
    rw = e.get('rule_write') or [ta, ta + 0.35]
    sc, (nx, ny) = _title_layout(n)
    uw = (t - rw[0]) / max(0.05, rw[1] - rw[0])
    if uw > 0: write(pen, sc, 'lipstick', clamp(uw), 255, tip=uw < 1, glow=glow)
    ns = (e.get('numeral_stamp') or {}).get('t', rw[1])
    _numeral(cv, n, t - ns, nx, ny, glow)
    _words(cv, rc, e, t, n)
    if wipe > 0:
        cv.restore()
        cv.save(); cv.clipPath(gl, skia.ClipOp.kIntersect, True)
        band = poly([(wx + 120, -GH), (wx + 300, -GH), (wx + 60, GH), (wx - 120, GH)])
        pen.fill(band, '#e9ecef', 70)
        for j in range(9):                                     # the smeared residue behind the finger
            o = -40 - j * 42 - 30 * hash01(j, 4)
            c_ = '#e07a8c' if j % 3 else '#f6eef0'
            ww_ = 18 + 16 * hash01(j, 3)
            cv.drawLine(wx + 120 + o, -GH * 0.6, wx - 120 + o, GH * 0.6, paint(c_, 22 - 1.5 * j, ww_ * 1.8))
            cv.drawLine(wx + 120 + o, -GH * 0.6, wx - 120 + o, GH * 0.6, paint(c_, 30 - 2 * j, ww_))
        fx, fy = wx + 10, 40                                   # the fingertip
        cv.drawOval(skia.Rect.MakeLTRB(fx - 34, fy - 60, fx + 34, fy + 60), paint('#e8b8a0', 140, None, blur=8))
        cv.restore()
    # the towel on top, whipped away
    tw_ = e.get('towel_whip') or [t0, t0 + 0.30]
    kt = 0.42 + 0.58 * (t - tw_[0]) / max(0.05, tw_[1] - tw_[0])          # already moving at the first frame
    if kt < 1: _towel(cv, clamp(kt))
    cv.restore()
    if ent_layer: cv.restore()
    if False:                                                  # v2's 2-frame static band at t0 (the card now enters on a flow)
        for j in range(6):
            yy = hash01(j + int(u * 60) * 7, 5) * DH
            cv.drawRect(skia.Rect.MakeLTRB(0, yy, DW, yy + 18 + 30 * hash01(j, 6)), paint('#ffffff', 50))
