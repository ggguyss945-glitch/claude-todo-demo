"""ui_v2_diag: diagrams D1-D10, split overlays, sound rings, the montage, the phone UI and the evidence documents
(DIRECTION_V2 5.4, PLAN_V2 2.3). Drawn in the film's own materials: chalk-white lines, lipstick red, the chip style.

HUD side (design coords, after the grade; `cs` = the shot camera state for the pinned ones):
    diagram(cv, e, t, sh, cs)    dispatch on e['id']: D1 game (pinned to the glass), D3 side view, D4 floors (+ split),
                                 D5 eye line (+ eye_line), D6 time split (+ dials), D7 loop clock, D8 bell rings (+ rings),
                                 D9 7:00:00, loop_split, watch (ALM 6:45 -> 4:45)
    split_overlay(cv, sh, t)     divider, panel labels, world chips, red X / green tick marks (shots[].split)
    sound_rings(cv, e, t, sh)    clean (smooth rings) / rattle (ring + jagged red squiggle) / broken (jagged, burst)
    eye_line(cv, e, t)           D5: target rings on both eyes, a dashed red line from her eye to yours
    dials(cv, e, t)              D6: OUR SIDE dial crawling / THEIR SIDE dial looping :40 -> :59 with a return arrow
    map_inset(cv, e, t)          D10: CABIN 7 -> path -> MESS HALL crate, Tess's dot running
    level_guide(cv, e, t, cs)    the dashed level line against the -13 deg frame
    montage_overlay(cv, sh, t)   the face-up phone montage: a flash and a clock chip per tile
    phone_ui(cv, e, t, sh, film) the phone states (message, voicemail_list, voicemail, calling, connected) + text fit
Set side (draw into a Layer so the camera push, DOF and grade apply):
    doc_layer(sh) -> Layer       the DOC shot's paper object with its marks animated (poster, notice, stencil, card,
                                 polaroid, photo, menu, sign); draw_doc(pen, kind, t, sh) is the raw draw
    phone_screen(pen, x, y, w, h, t, state, ...)   the phone's black glass: 7 tiny steps, the 8th line ('steps'),
                                 dust, a reflection; 'face' leaves the face to characters (q_nface)
"""
import math
import numpy as np
import skia
from engine.core import (CFG, DW, DH, Pen, col, mix, text, text_width, rrect, rect, oval, poly, smooth, union, minus,
                         clamp, lerp, prog, ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, hash01, noise1,
                         wrap as wrap_text)
from ui_v2_letter import (LIP, LIP_DK, LIP_HI, LIP_GLOW, CHALK, GREASE, MARKER, INK_RED, CHIP, paint, blur_mf, sprite, blit,
                          Script, write, wax, chalk_line, marker_line, dotted, arrow_head, ring_pts, squiggle_ring, text_path,
                          soft_shadow, _star)

FPS = 60
STEP_XY = [(1280 - 110 * k, 300 + 80 * k) for k in range(7)]      # sets.py lipstick treads (mirror_cu coords)
EIGHTH = (510.0, 860.0, 130.0)


def _proj(x, y, cs, d=1.0):
    if cs is None: return x, y
    try:
        from engine.scene import project
        X, Y = project(x, y, d, cs)
        return float(X), float(Y)
    except Exception:
        return x, y


def _chalk_label(cv, s, x, y, size=34, a=255, align='center', c=CHALK):
    """Small chalk caps in the font (readable at 640x360) with a dark halo."""
    tw = text_width(s, 800, size, 0.08)
    x0 = x - tw / 2 if align == 'center' else (x - tw if align == 'right' else x)
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0 - 14, y - size * 0.95, x0 + tw + 14, y + size * 0.35), 10, 10, paint('#000000', 0.42 * a, None, blur=10))
    path, _ = text_path(s, x0, y, 800, size, 0.08)
    pp = paint(c, a); pp.setPathEffect(skia.DiscretePathEffect.Make(2.5, 0.6, 3))
    cv.drawPath(path, pp)


def _panel(cv, x0, y0, x1, y1, a, c='#0c1024', edge='#ffffff'):
    b = rrect(x0, y0, x1 - x0, y1 - y0, 18)
    soft_shadow(cv, b, 140 * a / 255, 18, 0, 8)
    cv.drawPath(b, paint(c, 0.82 * a))
    cv.drawPath(b, paint(edge, 0.22 * a, 2))
    return b


def _fade(u, hold, fin=0.12, fout=0.15):
    return clamp(u / fin) * (1.0 - clamp((u - hold) / fout))


# ================================================================================================ queen chalk figure
def _tiny_queen(cv, x, y, h, a=255, chalk=True, fill='#0c0a12'):
    """A tiny Queen of Spades silhouette (crown of spades, fan collar, bell gown) standing with her feet at (x, y)."""
    s = h
    head = oval(x, y - s * 0.86, s * 0.065, s * 0.08)
    crown = poly([(x - s * 0.07, y - s * 0.93), (x - s * 0.05, y - s * 1.0), (x - s * 0.025, y - s * 0.95), (x, y - s * 1.03),
                  (x + s * 0.025, y - s * 0.95), (x + s * 0.05, y - s * 1.0), (x + s * 0.07, y - s * 0.93)])
    collar = poly([(x - s * 0.16, y - s * 0.86), (x - s * 0.05, y - s * 0.76), (x + s * 0.05, y - s * 0.76), (x + s * 0.16, y - s * 0.86),
                   (x + s * 0.08, y - s * 0.70), (x - s * 0.08, y - s * 0.70)])
    gown = smooth([(x - s * 0.07, y - s * 0.74), (x + s * 0.07, y - s * 0.74), (x + s * 0.09, y - s * 0.5), (x + s * 0.24, y),
                   (x - s * 0.26, y), (x - s * 0.09, y - s * 0.5)], True, 0.4)
    hair = smooth([(x - s * 0.07, y - s * 0.9), (x + s * 0.07, y - s * 0.9), (x + s * 0.09, y - s * 0.55), (x - s * 0.09, y - s * 0.55)], True, 0.6)
    shape = union(union(union(head, crown), union(collar, gown)), hair)
    cv.drawPath(shape, paint(fill, a))
    if chalk:
        pp = paint(CHALK, 0.85 * a, max(1.5, s * 0.018)); pp.setPathEffect(skia.DiscretePathEffect.Make(3.0, 0.8, 9))
        cv.drawPath(shape, pp)
    cv.drawCircle(x, y - s * 0.86, s * 0.03, paint('#ece6e8', a))


# ================================================================================================ D1 the game
def d1_game(cv, e, t, cs=None):
    """D1, drawn on the glass in chalk: numerals 1 (top) .. 7 beside the lipstick treads, a tiny dark figure below step
    7, a dotted arrow climbing, WISH with a star at the top. Pinned to the glass plane (mirror_cu coordinates)."""
    u = t - e['t']
    hold = float(e.get('hold', 2.4))
    if u < 0 or u > hold + 0.25: return
    a = 255 * (1.0 - clamp((u - hold) / 0.2))
    pen = Pen(cv)
    P = lambda x, y: _proj(x, y, cs)                              # noqa: E731
    sc = 1.0
    if cs is not None:
        x0_, _ = P(0, 0); x1_, _ = P(100, 0); sc = (x1_ - x0_) / 100.0
    for k in range(7):                                             # chalk tread outlines over the lipstick and numerals
        kk = clamp((u - k * 0.07) / 0.1)
        if kk <= 0: continue
        x, y = STEP_XY[k]
        p0, p1 = P(x - 60, y - 14), P(x - 60 + 120 * kk, y - 14)
        chalk_line(pen, [p0, p1], 5 * sc, 0.75 * a / 255, k)
        nx, ny = P(x + 92, y + 6)
        ss = 1.0 + 0.5 * (1 - ease_out_back(kk, 2.0))
        cv.save(); cv.translate(nx, ny); cv.scale(ss * sc, ss * sc)
        write(pen, Script(str(k + 1), 0, 0, 46, seed=k + 3, align='center', slant=0.05), 'chalk', 1.0, a * kk, tip=False, w=6)
        cv.restore()
    kf = clamp((u - 0.5) / 0.15)                                   # the tiny figure below step 7
    if kf > 0:
        fx, fy = P(560, 880)
        _tiny_queen(cv, fx, fy, 120 * sc, a * kf)
        _chalk_label(cv, 'HER', fx - 110 * sc, fy - 40 * sc, 34 * sc, a * kf)
    ka = clamp((u - 0.7) / 0.7)                                    # the dotted arrow climbing
    if ka > 0:
        pts = [P(x - 80, y - 70) for (x, y) in [(640, 760), (690, 710)] + [(STEP_XY[k][0], STEP_XY[k][1]) for k in range(6, -1, -1)]]
        pts += [P(1390, 210)]
        dotted(pen, pts, 6 * sc, 22 * sc, CHALK, a, ka)
        if ka >= 1:
            arrow_head(pen, pts[-1][0], pts[-1][1], -38, 34 * sc, CHALK, a)
    kw = clamp((u - 1.35) / 0.35)                                   # WISH and the star
    if kw > 0:
        sx, sy = P(1440, 160)
        r = 52 * sc * (1 + 0.3 * (1 - ease_out_back(clamp(kw * 2), 2.0)))
        cv.drawCircle(sx, sy, r * 2.2, paint('#fff2c0', 70 * kw * a / 255, None, blur=r))
        star = poly(_star(0, 0, 1.0))
        m = skia.Matrix(); m.setScale(r, r); m.postTranslate(sx, sy); star.transform(m)
        cv.drawPath(star, paint('#fff6d8', a * kw))
        pp = paint(CHALK, a * kw, 3 * sc); pp.setPathEffect(skia.DiscretePathEffect.Make(3, 0.7, 2)); cv.drawPath(star, pp)
        wx, wy = P(1505, 190)
        cv.save(); cv.translate(wx, wy); cv.scale(sc, sc)
        write(pen, Script('WISH', 0, 0, 70, seed=21, slant=0.08, track=0.22), 'chalk', kw, a, tip=True, w=8)
        cv.restore()


# ================================================================================================ D3 the side view
def d3_side(cv, e, t):
    """D3: the glass plane edge-on, the seven drawn steps ON it, the eighth step BEHIND it, a dashed line between."""
    u = t - e['t']
    hold = float(e.get('hold', 1.5))
    if u < 0 or u > hold + 0.3: return
    a = 255 * (1.0 - clamp((u - hold) / 0.2)) * clamp(u / 0.1)
    pen = Pen(cv)
    gx, gy0, gy1 = 820.0, 190.0, 830.0
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#04050a', 110 * a / 255))
    _panel(cv, 300, 90, 1620, 920, a, '#0a0c16')
    _chalk_label(cv, 'SIDE VIEW', DW / 2, 150, 40, a)
    k0 = ease_out_cubic(clamp(u / 0.25))                           # the glass plane
    glass = rect(gx - 14, gy0, 28, (gy1 - gy0) * k0)
    pen.linear(glass, gx - 14, 0, gx + 14, 0, [(0, '#c9d6e8'), (0.4, '#f4f8ff'), (1, '#8c9ab0')], a / 255)
    cv.drawRect(skia.Rect.MakeLTRB(gx - 26, gy0 - 22, gx + 26, gy0), paint('#d8d4c8', a))
    if k0 >= 1: cv.drawRect(skia.Rect.MakeLTRB(gx - 26, gy1, gx + 26, gy1 + 22), paint('#d8d4c8', a))
    _chalk_label(cv, 'THE GLASS', gx, gy1 + 76, 38, a * k0)
    marks = [gy0 + 60 + j * 72 for j in range(7)]                    # steps 1-7 drawn ON the glass (our side face)
    for j, my in enumerate(marks):
        kk = clamp((u - 0.25 - j * 0.04) / 0.08)
        if kk <= 0: continue
        wax(pen, [(gx - 16, my), (gx - 16 - 46 * kk, my + 2)], 12, a / 255, 0.3, seed=j)
        text(cv, str(j + 1), gx - 96, my + 10, 900, 30, '#ffffff', a * kk, 0.0, 'center', 0.6)
    kl = clamp((u - 0.55) / 0.2)
    if kl > 0:
        _chalk_label(cv, 'DRAWN ON IT', gx - 270, gy0 + 120, 38, a * kl, 'center')
    ey = marks[-1] + 70                                              # the eighth: a real tread behind the glass
    kd = clamp((u - 0.6) / 0.25)
    if kd > 0:
        chalk_line(pen, [(gx + 16, ey), (gx + 16 + 150 * kd, ey)], 5, a / 255, 7, CHALK, dash=(14, 10))
    k8 = clamp((u - 0.8) / 0.2)
    if k8 > 0:
        tx0, tx1 = gx + 170, gx + 400
        tread = poly([(tx0, ey), (tx1, ey), (tx1, ey + 26), (tx0, ey + 26)])
        cv.drawPath(tread, paint('#2a1838', a * k8))
        cv.drawLine(tx0, ey, tx1, ey, paint(LIP_GLOW, 120 * k8 * a / 255, 16, blur=8))
        cv.drawLine(tx0, ey, tx1, ey, paint(LIP, a * k8, 6))
        for j in range(1, 4):                                        # more treads going down into the dark
            yy = ey + 26 + j * 46; xx = tx1 + j * 120
            cv.drawLine(tx1 + (j - 1) * 120, yy - 46 + 26, xx, yy - 20, paint('#6a4a7a', a * k8 * (0.7 - 0.15 * j), 4))
            cv.drawLine(xx - 120, yy - 20, xx, yy - 20, paint(LIP, a * k8 * (0.6 - 0.12 * j), 4))
        _tiny_queen(cv, (tx0 + tx1) / 2, ey, 190, a * k8)
        _chalk_label(cv, '8TH STEP: BEHIND IT', (tx0 + tx1) / 2 + 80, ey + 110, 40, a * k8, c='#ff8a98')
    kb = clamp((u - 0.4) / 0.2)
    if kb > 0:
        _chalk_label(cv, 'OUR SIDE', gx - 330, gy1 + 76, 38, a * kb)
        _chalk_label(cv, 'BEHIND THE GLASS', gx + 360, gy0 + 40, 38, a * kb)
        ex, ey_ = gx - 360, 470.0                                   # your eye looking at the glass
        cv.drawOval(skia.Rect.MakeLTRB(ex - 34, ey_ - 18, ex + 34, ey_ + 18), paint(CHALK, a * kb, 4))
        cv.drawCircle(ex + 8, ey_, 10, paint(CHALK, a * kb))
        dotted(pen, [(ex + 40, ey_), (gx - 70, ey_)], 4, 16, CHALK, a * kb * 0.7)


# ================================================================================================ D7 / D9 loop clock
def _dial(cv, cx, cy, r, sec, a, loop=True, hi=(40, 59), ring='#ffcf8a', broken=0.0, label=None, readout=None, flash=0.0):
    pen = Pen(cv)
    cv.drawCircle(cx, cy, r + 18, paint('#000000', 0.45 * a, None, blur=24))
    cv.drawCircle(cx, cy, r, paint('#0c0a14', 0.86 * a))
    cv.drawCircle(cx, cy, r, paint('#f4f1e8', 0.9 * a, 5))
    for k in range(60):
        an = math.radians(-90 + k * 6)
        r0 = r * (0.84 if k % 5 == 0 else 0.9)
        cv.drawLine(cx + math.cos(an) * r0, cy + math.sin(an) * r0, cx + math.cos(an) * r * 0.96, cy + math.sin(an) * r * 0.96,
                    paint('#f4f1e8', a * (0.9 if k % 5 == 0 else 0.45), 3.4 if k % 5 == 0 else 1.6))
    if hi is not None and loop:                                   # the looping band :40 -> :59
        a0, a1 = -90 + hi[0] * 6, -90 + hi[1] * 6 + 6
        arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72), a0, a1 - a0)
        cv.drawPath(arc, paint(ring, 0.30 * a, r * 0.16, cap='butt'))
        if broken < 1:                                             # the return arrow :59 -> :40 inside the dial
            ret = skia.Path(); ret.addArc(skia.Rect.MakeLTRB(cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5), a1, -(a1 - a0))
            if broken > 0:
                m = skia.Matrix(); m.setTranslate((hash01(3, 1) - 0.5) * 40 * broken, 30 * broken * broken); ret.transform(m)
            cv.drawPath(ret, paint(LIP_GLOW, a * (1 - broken), r * 0.05))
            ea = math.radians(a0)
            hx, hy = cx + r * 0.5 * math.cos(ea), cy + r * 0.5 * math.sin(ea)
            arrow_head(Pen(cv), hx, hy + 30 * broken * broken, math.degrees(ea) + 90 + 180, r * 0.13, LIP_GLOW, a * (1 - broken), 'solid', r * 0.05)
    an = math.radians(-90 + sec * 6)
    cv.drawLine(cx, cy, cx + math.cos(an) * r * 0.86, cy + math.sin(an) * r * 0.86, paint(LIP, a, 6))
    cv.drawLine(cx, cy, cx - math.cos(an) * r * 0.16, cy - math.sin(an) * r * 0.16, paint(LIP, a, 6))
    cv.drawCircle(cx, cy, 10, paint(LIP, a))
    if flash > 0:
        cv.drawCircle(cx, cy, r * 1.05, paint('#ffffff', 160 * flash * a / 255, 14, blur=6))
    if label: _chalk_label(cv, label, cx, cy - r - 30, 30, a)
    if readout:
        text(cv, readout, cx, cy + r + 66, 900, 50, '#fff6e2', a, 0.04, 'center', 0.8)


def d7_loop(cv, e, t, sh):
    """D7: the loop clock: the second hand climbs to :59 and snaps back to :40 (the snap = the shot's rewind time, or
    its end); the :40-:59 band and a lipstick return arrow; a 6:59:4x readout."""
    u = t - e['t']
    hold = float(e.get('hold', 1.6))
    if u < 0 or u > max(hold, sh['t1'] - e['t']) + 0.2: return
    snap = None
    for f in sh.get('fx_post') or []:
        if f.get('rewind'): snap = f['t']
    if snap is None: snap = sh['t1'] + 0.02
    a = 255 * clamp(u / 0.12)
    if t < snap: sec = 59.0 - min(19.0, (snap - t) * 1.6)
    else: sec = 40.0 + (t - snap) * 1.6
    flash = 1.0 - clamp((t - snap) / 0.15) if t >= snap else 0.0
    s_ = int(sec)
    _dial(cv, 1520, 440, 200, sec, a, True, label='THEIR CLOCK', readout='6:59:%02d' % s_, flash=flash)


def d9_seven(cv, e, t, sh):
    """D9: the clock passes 12 at 538.70 and keeps going: 7:00:00, the loop band fades and its return arrow breaks."""
    u = t - e['t']
    if u < 0: return
    brk = 538.70
    a = 255 * clamp(u / 0.12)
    sec = 59.0 - (brk - t) * 1.0 if t < brk else 60.0 + (t - brk) * 1.0
    broken = clamp((t - brk) / 0.4)
    ro = '6:59:%02d' % int(min(59, sec)) if t < brk else '7:00:%02d' % int(sec - 60)
    k = 1.0 - 0.45 * clamp((t - brk) / 0.25)                       # it shrinks as the 7:00 AM type slams in
    cv.save(); cv.translate(1520, 440); cv.scale(k, k); cv.translate(-1520, -440)
    _dial(cv, 1520, 440, 200, sec % 60, a * (1 - 0.4 * broken), True, ring=mix('#ffcf8a', '#ffffff', broken), broken=broken,
          label='THEIR CLOCK', readout=ro, flash=1.0 - clamp((t - brk) / 0.2) if t >= brk else 0.0)
    cv.restore()


# ================================================================================================ D6 dials
def dials(cv, e, t):
    """D6 over the section: OUR SIDE (blue, upper left) crawling, THEIR SIDE (gold, lower right) looping :40 -> :59."""
    u = t - e['t']
    hold = float(e.get('hold', 2.0))
    if u < 0 or u > hold + 0.25: return
    a = 255 * _fade(u, hold)
    L, R = e.get('left', {}), e.get('right', {})
    sec_l = 12 + u * 0.5
    ph = (u % 1.1) / 1.1
    sec_r = 40 + 19.9 * ph
    for (cx, cy, d, sec, style, ring, loop) in ((470, 330, L, sec_l, 'ours', '#7f9dff', False), (1450, 700, R, sec_r, 'theirs', '#ffcf8a', True)):
        sc = ease_out_back(clamp(u / 0.18), 1.6)
        cv.save(); cv.translate(cx, cy); cv.scale(sc, sc); cv.translate(-cx, -cy)
        _dial(cv, cx, cy, 128, sec, a, loop, ring=ring, flash=(1.0 - clamp((ph * 1.1) / 0.12)) if loop and u > 1.1 else 0.0)
        cv.restore()
        _chalk_label(cv, d.get('label', ''), cx, cy - 166, 40, a)
        from ui_v2 import chip
        cw = text_width(d.get('chip', ''), 700, 26.5, 0.13) + 90
        chip(cv, d.get('chip', ''), 'loop' if loop else style, u - 0.1, cx - cw / 2, cy + 168, a)
        if not loop:
            for j in range(10):                                     # dust hanging in the beam (crawling)
                px = cx - 110 + 220 * hash01(j, 3); py = cy - 60 + 120 * hash01(j, 4) + u * 2
                cv.drawCircle(px, py, 2.4, paint('#ffffff', 0.6 * a))


# ================================================================================================ D5 eye line
def eye_line(cv, e, t):
    """D5: target rings on her eye (a) and yours (b), a dashed red line from hers to yours, a pulse travelling it."""
    u = t - e['t']
    hold = float(e.get('hold', 1.1))
    if u < 0 or u > hold + 0.2: return
    a = 255 * _fade(u, hold)
    (ax, ay), (bx, by) = e['a'], e['b']
    for j, (x, y) in enumerate(((ax, ay), (bx, by))):
        kk = ease_out_back(clamp((u - j * 0.12) / 0.16), 1.8)
        for r_, w_ in ((96, 6), (128, 3)):
            cv.drawCircle(x, y, r_ * kk, paint('#ff2a40', 0.5 * a, w_ * 3, blur=8))
            cv.drawCircle(x, y, r_ * kk, paint('#ff3048', a, w_))
    k = ease_out_cubic(clamp((u - 0.15) / 0.3))
    if k > 0:
        x0, x1 = ax + 130, bx - 130
        xe = lerp(x0, x1, k)
        dl = paint('#ff3048', a, 7); dl.setPathEffect(skia.DashPathEffect.Make([26, 16], -u * 120))
        cv.drawLine(x0, ay, xe, lerp(ay, by, k), paint('#ff2030', 0.45 * a, 20, blur=10))
        cv.drawLine(x0, ay, xe, lerp(ay, by, k), dl)
        if k >= 1:
            arrow_head(Pen(cv), x1, by, 0, 34, '#ff3048', a, 'solid', 7)
            px = lerp(x0, x1, (u * 1.6) % 1.0)
            cv.drawCircle(px, lerp(ay, by, (u * 1.6) % 1.0), 12, paint('#ffd0d6', a))
    _chalk_label(cv, 'HER EYES', ax, ay + 200, 40, a * clamp((u - 0.2) / 0.15))
    _chalk_label(cv, 'YOURS', bx, by + 200, 40, a * clamp((u - 0.3) / 0.15))


# ================================================================================================ D8 sound rings
def sound_rings(cv, e, t, sh=None):
    """Bell sound as rings from (x, y): clean = smooth white rings; rattle = a ring plus a jagged red squiggle trailing
    it; broken = jagged red-white rings with gaps, bursting (the real strike)."""
    u = t - e['t']
    hold = float(e.get('hold', 1.0))
    if u < 0 or u > hold + 0.5: return
    x, y = e['x'], e['y']; n = int(e.get('n', 3)); kind = e.get('kind', 'clean')
    pen = Pen(cv)
    life = 0.9
    for j in range(n):
        uj = u - j * 0.2
        if uj < 0 or uj > life: continue
        k = uj / life
        r = 70 + 380 * ease_out_cubic(k)
        a = 255 * (1 - k) ** 1.2
        if kind == 'clean':
            cv.drawCircle(x, y, r, paint('#ffffff', 0.12 * a, 20))
            cv.drawCircle(x, y, r, paint('#ffffff', 0.22 * a, 12))
            cv.drawCircle(x, y, r, paint('#ffffff', a, 6))
        elif kind == 'rattle':
            cv.drawCircle(x, y, r, paint('#ffffff', 0.8 * a, 5))
            if uj > 0.1:
                r2 = max(40, r - 50)
                pts = squiggle_ring(x, y, r2, 14, 30, uj * 3, seed=j)
                cv.drawPath(poly(pts), paint('#ff2a40', 0.25 * a, 14))
                cv.drawPath(poly(pts), paint('#ff3048', a, 5))
        else:
            pts = squiggle_ring(x, y, r, 22, 18, j * 0.7, seed=j + 5)
            pp = paint('#ffffff', a, 6); pp.setPathEffect(skia.DashPathEffect.Make([60, 26], j * 20))
            cv.drawPath(poly(pts), pp)
            pts2 = squiggle_ring(x, y, r * 0.86, 18, 22, j * 1.3, seed=j + 9)
            pr = paint('#ff3048', a, 5); pr.setPathEffect(skia.DashPathEffect.Make([40, 30], j * 13))
            cv.drawPath(poly(pts2), pr)
    if sh is not None and sh.get('type') in ('DIAGRAM', 'SPLIT') or e.get('label'):
        lab = e.get('label') or {'clean': 'CLEAN NOTE', 'rattle': '+ RATTLE', 'broken': ''}[kind]
        if lab:
            la = 255 * clamp(u / 0.12) * (1 - clamp((u - hold) / 0.2))
            yy = y + 230 if sh is None or sh.get('type') != 'SPLIT' else y + 300
            xx = x if sh is None or sh.get('type') != 'DIAGRAM' or kind != 'rattle' else x + 260
            _chalk_label(cv, lab, xx, yy, 36, la, c='#ffffff' if kind == 'clean' else '#ff8a98')


# ================================================================================================ D10 map
def map_inset(cv, e, t):
    """D10 (top left, 2 s): CABIN 7 -> the path -> MESS HALL · CRATE, with Tess's dot running the path and 40 M."""
    u = t - e['t']
    hold = float(e.get('hold', 2.0))
    if u < 0 or u > hold + 0.2: return
    a = 255 * _fade(u, hold, 0.15, 0.2)
    x0, y0, w, h = 44.0, 150.0, 420.0, 270.0
    k = ease_out_back(clamp(u / 0.2), 1.4) * 1.35
    cv.save(); cv.translate(x0, y0); cv.scale(k, k)
    _panel(cv, 0, 0, w, h, a, '#0c1430', '#9fb0ff')
    for gx in range(1, 8):
        cv.drawLine(gx * w / 8, 8, gx * w / 8, h - 8, paint('#9fb0ff', 0.08 * a, 1))
    for gy in range(1, 5):
        cv.drawLine(8, gy * h / 5, w - 8, gy * h / 5, paint('#9fb0ff', 0.08 * a, 1))
    items = {it[0]: (it[1], it[2]) for it in e.get('items', [])}
    c7 = items.get('CABIN 7', (60, 180)); ph = items.get('PATH', (180, 140)); mh = items.get('MESS HALL · CRATE', (300, 80))
    pen = Pen(cv)
    cv.drawRect(skia.Rect.MakeLTRB(c7[0] - 30, c7[1] - 26, c7[0] + 30, c7[1] + 26), paint('#7f9dff', 0.35 * a))
    cv.drawRect(skia.Rect.MakeLTRB(c7[0] - 30, c7[1] - 26, c7[0] + 30, c7[1] + 26), paint(CHALK, a, 3))
    text(cv, '7', c7[0], c7[1] + 12, 900, 34, '#ffffff', a, 0, 'center')
    cv.drawRect(skia.Rect.MakeLTRB(mh[0] - 60, mh[1] - 34, mh[0] + 60, mh[1] + 20), paint('#ffcf8a', 0.25 * a))
    cv.drawRect(skia.Rect.MakeLTRB(mh[0] - 60, mh[1] - 34, mh[0] + 60, mh[1] + 20), paint(CHALK, a, 3))
    cr = (mh[0] + 40, mh[1] + 34)                                   # the crate on the porch
    cv.drawRect(skia.Rect.MakeLTRB(cr[0] - 12, cr[1] - 10, cr[0] + 12, cr[1] + 10), paint('#ff3048', a))
    path = [(c7[0] + 30, c7[1] - 4), (ph[0], ph[1]), (cr[0] - 16, cr[1] + 6)]
    dotted(pen, path, 3.2, 12, CHALK, a * 0.85)
    _chalk_label(cv, 'CABIN 7', c7[0] + 6, c7[1] + 66, 26, a)
    _chalk_label(cv, 'MESS HALL', mh[0], mh[1] - 46, 26, a)
    _chalk_label(cv, 'CRATE', cr[0] + 4, cr[1] + 50, 26, a, c='#ff8a98')
    _chalk_label(cv, '40 M', ph[0] + 6, ph[1] + 44, 24, a * 0.9)
    q = clamp((u - 0.3) / max(0.3, hold - 0.5))                     # Tess's dot runs the path
    segs = [(path[i], path[i + 1]) for i in range(2)]
    L = [math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in segs]
    d = q * sum(L)
    px, py = path[0]
    for (a_, b), l in zip(segs, L):
        if d <= l: px, py = a_[0] + (b[0] - a_[0]) * d / l, a_[1] + (b[1] - a_[1]) * d / l; break
        d -= l; px, py = b
    pulse = 0.5 + 0.5 * math.sin(u * 12)
    cv.drawCircle(px, py, 14 + 6 * pulse, paint('#ffb84d', 0.5 * a, None, blur=6))
    cv.drawCircle(px, py, 8, paint('#ffb84d', a))
    cv.restore()


# ================================================================================================ level guide
def level_guide(cv, e, t, cs=None):
    """The 8th step stays level: a dashed level line (LEVEL), the frame's -13 deg axis and the angle between them."""
    u = t - e['t']
    hold = float(e.get('hold', 1.6))
    if u < 0 or u > hold + 0.2: return
    a = 255 * _fade(u, hold)
    y = float(e.get('y', 680)); rot = float(e.get('frame_rot', -13.0))
    cx = 760.0
    X0, Y0 = _proj(300, y, cs); X1, Y1 = _proj(1620, y, cs); CX, CY = _proj(cx, y, cs)
    k = ease_out_cubic(clamp(u / 0.3))
    pen = Pen(cv)
    chalk_line(pen, [(CX - (CX - X0) * k, Y0), (CX + (X1 - CX) * k, Y1)], 6, a / 255, 3, '#ffffff', dash=(24, 14))
    if k >= 1:
        _chalk_label(cv, 'LEVEL', X1 - 40, Y1 - 24, 30, a)
    kr = clamp((u - 0.3) / 0.25)
    if kr > 0:
        r = math.radians(rot)
        L = 420 * kr
        chalk_line(pen, [(CX - L * math.cos(r), CY - L * math.sin(r)), (CX + L * math.cos(r), CY + L * math.sin(r))], 5, a / 255 * 0.8, 5, LIP_HI, dash=(18, 12))
        arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(CX + 160, CY - 160, CX + 480, CY + 160), rot, -rot)
        arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(CX - 300, CY - 300, CX + 300, CY + 300), rot, -rot)
        cv.drawPath(arc, paint('#ffffff', a * kr, 4))
        _chalk_label(cv, '%d°' % abs(int(round(rot))), CX + 340, CY - 30, 34, a * kr)
        _chalk_label(cv, 'THE FRAME', CX - 330, CY + 130, 26, a * kr * 0.9, c=LIP_HI)


# ================================================================================================ splits and montage
def split_overlay(cv, sh, t):
    """Two-panel split: the divider draws down, the panel labels pop, world chips under them, red X / green tick."""
    sp = sh.get('split') or {}
    panels = sp.get('panels') or []
    if len(panels) != 2: return
    u = t - sh['t0']
    k = ease_out_cubic(clamp(u / 0.14))
    x = DW / 2
    for (ya, yb) in ((0, 928), (1004, DH)):                  # a gap where the caption sits
        yb_ = min(yb, DH * k)
        if yb_ <= ya: continue
        cv.drawLine(x, ya, x, yb_, paint('#000000', 120, 22))
        cv.drawLine(x, ya, x, yb_, paint('#ffffff', 235, 7))
    from ui_v2 import chip
    for j, p in enumerate(panels):
        cx = DW / 4 + j * DW / 2
        la = clamp((u - 0.08 - j * 0.06) / 0.12)
        if p.get('label') and la > 0:
            s = 1.0 + 0.25 * (1 - ease_out_back(la, 2.0))
            cv.save(); cv.translate(cx, 190); cv.scale(s, s)
            path, tw = text_path(p['label'], 0, 0, 900, 62, 0.04, 'center')
            cv.drawPath(path, paint('#000000', 200 * la, None, blur=12))
            cv.drawPath(path, paint('#ffffff', 255 * la))
            ul = {'theirs': '#ffb43c', 'ours': '#7f9dff', 'memory': '#a8432c'}.get(p.get('world'), '#ffffff')
            cv.drawRoundRect(skia.Rect.MakeLTRB(-tw / 2, 18, -tw / 2 + tw * ease_out_cubic(la), 28), 5, 5, paint(ul, 255 * la))
            cv.restore()
        if p.get('chip'):
            w = text_width(p['chip'].replace('·', ' '), 700, 26.5, 0.13) + 100
            yy = 262 if p.get('label') else 130
            chip(cv, p['chip'], 'theirs' if p.get('world') == 'theirs' else 'ours', u - 0.2 - j * 0.06, cx - w / 2, yy)
        mk = p.get('mark')
        if mk:
            km = clamp((u - 0.45) / 0.12)
            if km > 0:
                lw_ = text_width(p.get('label', ''), 900, 62, 0.04)
                mx, my = cx + lw_ / 2 + 90, 172
                s = 0.8 * (1.0 + 0.4 * (1 - ease_out_back(km, 2.2)))
                cv.save(); cv.translate(mx, my); cv.scale(s, s)
                if mk == 'red_x':
                    cv.drawCircle(0, 0, 70, paint('#000000', 120 * km, None, blur=12))
                    for (ax, ay, bx, by) in ((-42, -42, 42, 42), (42, -42, -42, 42)):
                        cv.drawLine(ax, ay, bx, by, paint('#e3262e', 255 * km, 18))
                    _chalk_label(cv, 'FAKE', 0, 128, 44, 255 * km, c='#ff8a98')
                else:
                    cv.drawCircle(0, 0, 70, paint('#000000', 120 * km, None, blur=12))
                    cv.drawPath(poly([(-44, 2), (-12, 36), (48, -38)], False), paint('#3ad16a', 255 * km, 18))
                    _chalk_label(cv, 'REAL', 0, 128, 44, 255 * km, c='#8ff0a8')
                cv.restore()
    if sh.get('split') and any(p.get('src_t') for p in panels):        # the loop twins: SAME SECOND on the divider
        ks = ease_out_back(clamp((u - 0.3) / 0.15), 1.8)
        if ks > 0:
            cv.save(); cv.translate(x, DH / 2 + 220); cv.scale(ks, ks)
            b = rrect(-150, -34, 300, 68, 34)
            cv.drawPath(b, paint('#3a1830', 235)); cv.drawPath(b, paint('#ff6a8a', 255, 3))
            text(cv, '= SAME SECOND', 0, 11, 900, 28, '#ffffff', 255, 0.06, 'center')
            cv.restore()


def montage_overlay(cv, sh, t):
    """The face-up phone montage: a 1-frame white flash on each tile and a chip with that moment's clock."""
    tiles = sh.get('montage') or []
    from ui_v2 import chip, clock_ours
    for j, tl in enumerate(tiles):
        t1 = tiles[j + 1]['t'] if j + 1 < len(tiles) else sh['t1']
        if tl['t'] <= t < t1:
            u = t - tl['t']
            if u < 1.0 / FPS + 1e-4: cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#ffffff', 150))
            sec = clock_ours(tl['src_t']) % 86400.0
            hh, mm = int(sec // 3600), int(sec // 60) % 60
            s = 'CABIN 7 · %d:%02d %s' % ((hh % 12) or 12, mm, 'AM' if hh < 12 else 'PM')
            chip(cv, s, 'ours', 1.0, 44, DH - 190)
            for k in range(len(tiles)):                           # 4 tile ticks
                cv.drawRoundRect(skia.Rect.MakeLTRB(44 + k * 34, DH - 152, 44 + k * 34 + 26, DH - 144), 3, 3,
                                 paint('#ffffff', 230 if k <= j else 70))


# ================================================================================================ the watch
def watch_overlay(cv, e, t):
    """ALM readout callout beside the watch: ALM 6:45 flips to 4:45 (highlighted), or ALM 4:45 flashing."""
    u = t - e['t']
    hold = float(e.get('hold', 1.2))
    if u < 0 or u > hold + 0.2: return
    a = 255 * _fade(u, hold)
    flip = '6:45' in e.get('content', '') and '4:45' in e.get('content', '')
    x, y = 1500.0, 300.0
    _panel(cv, x - 200, y - 90, x + 200, y + 90, a, '#0e1a12', '#9fe8b0')
    text(cv, 'ALM', x - 150, y + 14, 800, 30, '#9fe8b0', a, 0.1, 'left')
    if flip:
        fk = clamp((u - 0.35) / 0.12)
        s = '6:45' if fk < 0.5 else '4:45'
        cv.save(); cv.translate(x + 60, y); cv.scale(1, max(0.05, abs(math.cos(fk * math.pi)))); cv.translate(-(x + 60), -y)
        text(cv, s, x + 60, y + 28, 900, 82, '#d8ffe0', a, 0.02, 'center')
        cv.restore()
        if fk >= 1:
            cv.drawRoundRect(skia.Rect.MakeLTRB(x - 30, y - 50, x + 160, y + 46), 10, 10, paint('#f4e04d', 0.32 * a))
            _chalk_label(cv, '2 HOURS EARLY', x, y + 150, 30, a * clamp((u - 0.55) / 0.15))
    else:
        on = (u % 0.5) < 0.3
        text(cv, '4:45', x + 60, y + 28, 900, 82, '#d8ffe0', a * (1.0 if on else 0.25), 0.02, 'center')


# ================================================================================================ dispatch
def diagram(cv, e, t, sh, cs=None):
    i = e.get('id', '')
    if i == 'D1': d1_game(cv, e, t, cs)
    elif i == 'D3': d3_side(cv, e, t)
    elif i == 'D7': d7_loop(cv, e, t, sh)
    elif i == 'D9': d9_seven(cv, e, t, sh)
    elif i == 'watch': watch_overlay(cv, e, t)
    elif i == 'D4':
        u = t - e['t']; hold = float(e.get('hold', 1.6))
        if 0 <= u <= hold + 0.2:
            a = 255 * _fade(u, hold)
            ks = ease_out_back(clamp((u - 0.35) / 0.15), 1.8)
            cv.save(); cv.translate(DW / 2, DH / 2 + 60); cv.scale(ks, ks)
            cv.drawCircle(0, 0, 56, paint('#0c0a14', 0.9 * a)); cv.drawCircle(0, 0, 56, paint('#ffffff', a, 4))
            for yy in (-12, 12): cv.drawLine(-24, yy, 24, yy, paint('#ffffff', a, 8, cap='butt'))
            cv.drawLine(-16, 28, 16, -28, paint('#ffffff', a, 8))
            cv.restore()
            _chalk_label(cv, 'WET PRINTS', DW / 4, DH - 190, 34, a * clamp((u - 0.5) / 0.15))
            _chalk_label(cv, 'NO PRINTS', DW * 3 / 4, DH - 190, 34, a * clamp((u - 0.6) / 0.15))
    # D5 (eye_line), D6 (dials), D8 (sound_rings + split marks), loop_split (split_overlay) draw from their own entries


# ================================================================================================ phone UI (kept states)
def _phone_body(pen, W_, Hh, a):
    body = rrect(-W_ / 2, -Hh / 2, W_, Hh, 46)
    pen.radial(None, 0, 24, W_ * 0.95, [(0, '#000000', 170 * a / 255), (0.6, '#000000', 90 * a / 255), (1, '#000000', 0)],
               sy=Hh * 0.62 / (W_ * 0.95), clip=False)
    pen.fill(body, '#15161b', a); pen.line(body, 6, '#1d1f26', a)
    return rrect(-W_ / 2 + 12, -Hh / 2 + 12, W_ - 24, Hh - 24, 36)


def _status(cv, pen, W_, Hh, a, t):
    from ui_v2 import clock_ours
    sec = clock_ours(t) % 86400.0
    hh, mm = int(sec // 3600), int(sec // 60) % 60
    text(cv, '%d:%02d' % ((hh % 12) or 12, mm), -W_ / 2 + 44, -Hh / 2 + 44, 700, 13, '#e9edf7', a, 0.02, 'left')
    for k in range(4):
        hh_ = 4 + k * 2.6
        pen.fill(rrect(W_ / 2 - 84 + k * 6, -Hh / 2 + 44 - hh_, 4, hh_, 1.2), '#e9edf7', a * (0.95 if k < 2 else 0.35))
    pen.line(rrect(W_ / 2 - 52, -Hh / 2 + 34, 22, 11, 3), 1.5, '#e9edf7', a)
    pen.fill(rrect(W_ / 2 - 50, -Hh / 2 + 36, 6, 7, 1.5), '#e3262e', a)


BUBBLE_W, BUBBLE_SIZE, BUBBLE_LH = 240.0, 20.0, 26.0


def fit_bubble(txt, maxw=BUBBLE_W, size=BUBBLE_SIZE):
    """Wrap a bubble's text so that every line fits the bubble (error 23): words longer than a line are split."""
    lines = wrap_text(txt, 600, size, maxw - 28, 0.0)
    out = []
    for l in lines:
        while text_width(l, 600, size, 0.0) > maxw - 28 and len(l) > 1:
            k = len(l)
            while k > 1 and text_width(l[:k], 600, size, 0.0) > maxw - 28: k -= 1
            out.append(l[:k]); l = l[k:]
        out.append(l)
    return out


def _bubble(cv, pen, txt, x, y, maxw, a, sc=1.0, incoming=True):
    lines = fit_bubble(txt, maxw)
    bw = max(text_width(l, 600, BUBBLE_SIZE, 0.0) for l in lines) + 28
    bh = BUBBLE_LH * len(lines) + 20
    cv.save(); cv.translate(x, y + bh); cv.scale(sc, sc); cv.translate(-x, -(y + bh))
    pen.fill(rrect(x, y, bw, bh, 16), '#2b3245' if incoming else '#2f6fe0', a)
    for i, l in enumerate(lines):
        text(cv, l, x + 14, y + 28 + i * BUBBLE_LH, 600, BUBBLE_SIZE, '#eef2fb', a, 0.0, 'left')
    cv.restore()
    return bh


def _hand(pen, W_, Hh, skin, a, front):
    try:
        import characters as C
        C.hud_phone_hand(pen, W_, Hh, skin, a, front)
    except Exception:
        pass


def _button(pen, cx, cy, r, c, a, icon='end'):
    from engine import hud as H
    H._button(pen, cx, cy, r, c, a, icon)


def phone_ui(cv, ev, t, sh, film=None):
    """The phone held to the camera (v1 states kept): message (Mom's thread, bubbles text-fitted), voicemail_list,
    voicemail, calling, connected (waveform following Mom's line, flat in the pause, spiking on the chair scrape).
    `inset` entries are the small phone in the corner (x, y, scale)."""
    from engine import hud as H
    st = ev['state']; u = t - ev['t']
    pen = Pen(cv); a = 255
    W_, Hh = 300.0, 600.0
    x, y, sc = ev.get('x', 960), ev.get('y', 560), ev.get('scale', 1.0) * 1.22 * (1.1 if ev.get('fit') else 1.0)
    k = 1.015 ** max(0.0, t - sh['t0'])
    seed = int(''.join(ch for ch in sh['id'] if ch.isdigit()) or 1)
    ox = 7.0 * noise1(t * 0.9, seed * 5 + 1) + 2.0 * noise1(t * 3.3, seed * 5 + 2)
    oy = 6.0 * noise1(t * 0.8, seed * 5 + 3) + 2.0 * noise1(t * 2.9, seed * 5 + 4)
    rot = 1.1 * noise1(t * 0.6, seed * 5 + 5)
    if ev.get('inset'):
        ain = ease_out_cubic(clamp(u / 0.2))
        cv.save(); cv.translate(x, y); cv.scale(sc * ain, sc * ain)
        b = rrect(-W_ / 2 - 30, -Hh / 2 - 30, W_ + 60, Hh + 60, 60)
        soft_shadow(cv, b, 160, 30, 0, 14)
        cv.restore()
    cv.save(); cv.translate(x + ox, y + oy); cv.rotate(rot); cv.scale(sc * k, sc * k)
    _hand(pen, W_, Hh, '#c9aa98', a, False)
    scr = _phone_body(pen, W_, Hh, a)
    top, bot = {'voicemail': ('#14161f', '#0b0c12'), 'voicemail_list': ('#14161f', '#0b0c12'),
                'message': ('#10141f', '#0a0c12')}.get(st, ('#121a2e', '#0a0d16'))
    pen.linear(scr, 0, -Hh / 2, 0, Hh / 2, [top, bot], a / 255)
    pen.fill(rrect(-38, -Hh / 2 + 24, 76, 20, 10), '#050506', a)
    cv.save(); cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    _status(cv, pen, W_, Hh, a, t)

    def T(s, yy, size, c='#ffffff', w=800, sp=0.02, aa=1.0, al='center', xx=0.0):
        text(cv, s, xx, yy, w, size, c, a * aa, sp, al, 0.0)

    if st == 'message':
        pen.fill(rect(-W_ / 2, -Hh / 2 + 56, W_, 70), '#161b29', a)
        pen.seg((-W_ / 2, -Hh / 2 + 126), (W_ / 2, -Hh / 2 + 126), 1.2, '#2a3248', a)
        T('<', -Hh / 2 + 100, 26, '#6f95ff', 600, 0.0, 1.0, 'left', -W_ / 2 + 22)
        pen.fill(oval(-38, -Hh / 2 + 92, 19), '#3a4466', a)
        T('M', -Hh / 2 + 99, 18, '#d6dcf0', 800, 0.0, 1.0, 'center', -38)
        T(ev.get('name', 'MOM'), -Hh / 2 + 99, 20, '#ffffff', 800, 0.06, 1.0, 'left', -8)
        T('TODAY 11:57 PM', -Hh / 2 + 152, 10.5, '#7f8aa6', 700, 0.2)
        items = []
        for b in ev.get('bubbles', []):
            if b.get('typing_from') is not None and b['typing_from'] <= t < b['t']: items.append(('typing', None, b['typing_from']))
            if t >= b['t']: items.append(('msg', b['text'], b['t']))
        yy = Hh / 2 - 74
        for kind, txt, tb in reversed(items):
            hb = 40 if kind == 'typing' else BUBBLE_LH * len(fit_bubble(txt)) + 20
            ua = t - tb
            slide = 1.0 - ease_out_cubic(clamp(ua / 0.2))
            yy -= hb + 10
            sc_b = 0.85 + 0.15 * ease_out_back(clamp(ua / 0.18), 2.0)
            if kind == 'typing':
                pen.fill(rrect(-W_ / 2 + 22, yy + slide * 30, 70, 40, 18), '#2b3245', a)
                for j in range(3):
                    ph = 0.5 + 0.5 * math.sin(t * 9.0 - j * 0.9)
                    pen.fill(oval(-W_ / 2 + 41 + j * 16, yy + slide * 30 + 20 - 3 * ph, 4.5), '#c9d0e4', a * (0.45 + 0.55 * ph))
            else:
                _bubble(cv, pen, txt, -W_ / 2 + 22, yy + slide * 30, BUBBLE_W, a * clamp(ua / 0.08), sc_b)
        pen.fill(rrect(-W_ / 2 + 18, Hh / 2 - 60, W_ - 36, 34, 17), '#1b2131', a)
        T('Message', Hh / 2 - 37, 13, '#5d6782', 600, 0.02, 1.0, 'left', -W_ / 2 + 36)
    elif st == 'voicemail_list':
        T('VOICEMAIL', -Hh / 2 + 96, 13, '#9aa3b8', 700, 0.24)
        slide = 30 * (1.0 - ease_out_cubic(clamp(u / 0.5))) - 8.0 * clamp(u / 2.0)
        for j, it in enumerate(ev.get('items', [])):
            ry = -Hh / 2 + 130 + j * 64 + slide
            hl = j == 0
            if hl:
                pulse = 0.5 + 0.5 * math.sin(u * 5.0)
                pen.fill(rrect(-W_ / 2 + 16, ry, W_ - 32, 56, 10), '#232a3d', a * (0.7 + 0.3 * pulse))
                pen.fill(oval(-W_ / 2 + 30, ry + 28, 5), '#3d7bff', a)
            parts = [p.strip() for p in it.split('·')]
            T(parts[0], ry + 26, 17, '#ffffff' if hl else '#c5cbe0', 800, 0.04, 1.0, 'left', -W_ / 2 + 44)
            T('  '.join(parts[1:]), ry + 46, 11.5, '#8f9ab5', 600, 0.08, 1.0, 'left', -W_ / 2 + 44)
            pen.seg((-W_ / 2 + 44, ry + 60), (W_ / 2 - 16, ry + 60), 1.0, '#2a3248', a)
        tap = sh['t1'] - 0.45
        if 0 <= t - tap < 0.35:
            q = (t - tap) / 0.35
            pen.fill(oval(0, -Hh / 2 + 158 + slide, 16 + 50 * q), '#ffffff', a * 0.3 * (1 - q))
    elif st == 'voicemail':
        T('VOICEMAIL', -Hh / 2 + 96, 13, '#9aa3b8', 700, 0.24)
        T(ev.get('name', 'NOAH'), -Hh / 2 + 146, 34)
        T('JUL 18  ·  14 YEARS AGO', -Hh / 2 + 172, 11.5, '#8f9ab5', 700, 0.16)
        dur, t0s = 9.0, 3.0
        tm = ev.get('timer')
        if tm and ':' in tm: t0s = int(tm.split(':')[0]) * 60 + int(tm.split(':')[1])
        pos = clamp((t0s + u) / dur)
        T('0:%02d' % int(pos * dur), -Hh / 2 + 212, 20, '#e3262e', 800, 0.04)
        H.waveform(cv, -112, 10, 224, 104, 0.0, '#e0444c', (ev.get('waveform') or {}).get('seed', 13), pos, False, a, 3.0, 2.2, dim='#5a5e6e')
        pen.seg((-112, 104), (112, 104), 4, '#3a3e4c', a)
        pen.seg((-112, 104), (-112 + 224 * pos, 104), 4, '#f2f2f2', a)
        pen.fill(oval(-112 + 224 * pos, 104, 8), '#ffffff', a)
        _button(pen, 0, Hh / 2 - 100, 36, '#f2f2f2', a, 'pause')
    else:
        T('CALLING' if st == 'calling' else 'CONNECTED', -Hh / 2 + 92, 13, '#9aa3b8', 700, 0.22)
        T(ev.get('name', 'MOM'), -Hh / 2 + 146, 40)
        av = (0, -40)
        if st == 'calling':
            for j in range(3):
                ph = (u * 0.8 + j / 3.0) % 1.0
                pen.line(oval(av[0], av[1], 62 + ph * 70), 2.2, '#8fb0ff', a * (1 - ph) * 0.6)
        pen.fill(oval(av[0], av[1], 62), '#2a3350', a)
        T('M', av[1] + 18, 52, '#d6dcf0', 800)
        if st == 'calling':
            T('calling' + '.' * (1 + int(u * 2.5) % 3), 92, 19, '#c5cbe0', 600, 0.02)
        else:
            clk = max(0.0, t - ev.get('timer_from', ev['t']))
            T('%02d:%02d' % (int(clk) // 60, int(clk) % 60), 92, 22, '#c5cbe0', 600, 0.06)
            _call_wave(cv, pen, ev.get('waveform') or {}, t, a)
        _button(pen, 0, Hh / 2 - 92, 36, '#e0343b', a, 'end')
    cv.restore()
    pen.radial(scr, -W_ * 0.3, -Hh * 0.45, Hh * 0.9, [(0, '#ffffff', 16), (1, '#ffffff', 0)], a / 255)
    _hand(pen, W_, Hh, '#c9aa98', a, True)
    cv.restore()


def _call_wave(cv, pen, wv, t, a):
    x0, y0, w, h = -100.0, 140.0, 200.0, 46.0
    n = 36; bar = w / n * 0.6
    if wv.get('flat'):
        pen.seg((x0, y0), (x0 + w, y0), 2.5, '#6f95ff', a * 0.8); return
    env = None
    try:
        import characters as C
        env = C.voice_envelope() if wv.get('follow_line') is not None else None
    except Exception:
        env = None
    p = skia.Path()
    for j in range(n):
        tj = t - (n - 1 - j) * 0.035
        if env is not None:
            v = float(env[min(len(env) - 1, max(0, int(tj * 100)))]); amp = clamp((v + 52.0) / 34.0)
        else:
            amp = 0.15 + 0.5 * abs(noise1(tj * 6.0, 3)) * (0.6 + 0.4 * noise1(tj * 1.3, 4))
        sa = wv.get('spike_at')
        if sa is not None:
            amp = 0.08 + 0.06 * abs(noise1(tj * 9.0, 5))
            if 0 <= tj - sa < 0.35: amp = 1.0 - (tj - sa) / 0.35 * 0.6
        hh = max(2.0, amp * h / 2)
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + j * w / n, y0 - hh, bar, hh * 2), bar / 2, bar / 2))
    pen.fill(p, '#6f95ff', a)


# ================================================================================================ phone screen (set side)
def phone_screen(pen, x, y, w, h, t, state='steps', steps=1.0, eighth=0.0, dust=0.5, refl=0.25, red=0.0, seed=2):
    """The face-up phone's black glass at (x, y) centre, w x h: dust, a cool reflection band, 7 tiny lipstick steps
    (0..1 drawn, already there from 684.98) and the 8th line (0..1, a clean glowing line under step 7)."""
    cv = pen.cv
    scr = rrect(x - w / 2, y - h / 2, w, h, w * 0.08)
    pen.linear(scr, x - w / 2, y - h / 2, x + w / 2, y + h / 2, ['#10141a', '#05070a', '#0b0f14'])
    cv.save(); cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    pen.linear(poly([(x - w, y - h * 0.2), (x + w, y - h * 0.55), (x + w, y - h * 0.45), (x - w, y - h * 0.08)]), 0, y - h * 0.5, 0, y,
               [(0, '#ffffff', 0), (0.5, '#c8d6e6', 60 * refl * 4), (1, '#ffffff', 0)])
    if red > 0: pen.radial(None, x + w * 0.15, y + h * 0.1, w * 0.9, [(0, LIP_GLOW, 90 * red), (1, LIP_GLOW, 0)], clip=False)
    sc = w / 900.0
    for k in range(7):
        u = clamp(steps * 7 - (6 - k))
        if u <= 0: continue
        sx, sy = STEP_XY[k]
        px, py = x + (sx - 950) * sc, y + (sy - 560) * sc
        pts = [(px + 60 * sc, py), (px - 60 * sc, py - 1 * sc)]
        if k < 6: pts += [(px - 60 * sc, py), (px - 52 * sc, py + 80 * sc)]
        n = max(2, int(len(pts) * u))
        wax(pen, pts[:n], 19 * sc, 1.0, 0.4, seed=k, crumbs=False)
    if eighth > 0:
        ex, ey, L = EIGHTH
        x0_, y0_ = x + (ex - 950) * sc, y + (ey - 560) * sc
        x1_ = x0_ + L * sc * clamp(eighth)
        cv.drawLine(x0_, y0_, x1_, y0_, paint(LIP_GLOW, 120, 16 * sc, blur=8 * sc))
        cv.drawLine(x0_, y0_, x1_, y0_, paint(LIP, 255, 6 * sc))
    for i in range(int(90 * dust)):
        px, py = x + (-0.5 + hash01(i, seed)) * w, y + (-0.5 + hash01(i, seed + 1)) * h
        cv.drawCircle(px, py, w * 0.0035 * (1 + 2 * hash01(i, seed + 2)), paint('#aab4be', 60 + 80 * hash01(i, seed + 3)))
    cv.restore()
    return scr


# ================================================================================================ documents (set side)
SEPIA = dict(paper='#efe0bf', ink='#4a3a2c', red='#a8432c', shade='#c9a878')
NIGHT = dict(paper='#e9e4d6', ink='#1c1c24', red='#c0392b', shade='#9a9488')


def _paper(pen, path, box, pal, seed=0, rain=0.0, lit=None):
    x0, y0, x1, y1 = box
    soft_shadow(pen.cv, path, 170, 26, 8, 14)
    pen.fill(path, pal['paper'])
    pen.texture(path, 'paper', 0.45, 'multiply', 0.8)
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    pen.linear(path, x0, y0, x1, y1, [(0, '#ffffff', 30), (0.6, '#000000', 0), (1, '#000000', 50)])
    for i in range(int(rain * 14)):                         # rain stains: pale runs with darker edges
        rx = x0 + (x1 - x0) * hash01(i, seed + 1); ry = y0 + (y1 - y0) * 0.5 * hash01(i, seed + 2)
        L = (y1 - y0) * (0.2 + 0.5 * hash01(i, seed + 3))
        pen.cv.drawLine(rx, ry, rx + 6, ry + L, paint(pal['shade'], 50, 10 + 14 * hash01(i, seed + 4), blur=5))
        pen.cv.drawCircle(rx + 6, ry + L, 9, paint(pal['shade'], 70, 2))
    if lit is not None:
        lx, ly, lr = lit
        pen.radial(None, lx, ly, lr, [(0, '#fff3d6', 90), (1, '#fff3d6', 0)], sy=0.8, clip=False)
    pen.cv.restore()


def _portrait(pen, who, cx, cy, scale, expr='grin_kid', light=None, t=1.0):
    try:
        import characters as C
        P = C.Pose(expr if expr in C.EXPR else 'neutral'); P.t = t
        C.draw_bust(pen, who, cx, cy, scale, P, light=light, t=t)
        return True
    except Exception:
        return False


def _photo_box(pen, x0, y0, w, h, who, pal, expr='grin_kid', scale=0.42, sepia=False, seed=3):
    cv = pen.cv
    box = rect(x0, y0, w, h)
    pen.fill(box, '#8ab0c8' if not sepia else '#d8c09a')
    cv.save(); cv.clipPath(box, skia.ClipOp.kIntersect, True)
    pen.linear(box, x0, y0, x0, y0 + h, [(0, '#b8d4e6' if not sepia else '#e6d2ae'), (1, '#6a8aa0' if not sepia else '#b89870')])
    if not _portrait(pen, who, x0 + w / 2, y0 + h * 0.62, scale, expr):
        pen.fill(oval(x0 + w / 2, y0 + h * 0.45, w * 0.22, h * 0.26), '#c9a080')
    if sepia:
        cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, y0 + h), paint('#c09060', 70, None, blend=skia.BlendMode.kMultiply))
        cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, y0 + h), paint('#f0d8a8', 40, None, blend=skia.BlendMode.kScreen))
    cv.restore()
    pen.line(box, 3, pal['ink'], 200)


def draw_doc(pen, kind, t, sh=None, e=None):
    """The paper object of a DOC shot, centred on the frame, with its marks animated at film time t."""
    cv = pen.cv
    e = e or {}
    marks = e.get('marks') or []
    view = (sh or {}).get('view', '')
    if kind == 'poster':
        pal = NIGHT
        ecu = view == 'poster_ecu'
        cv.save()
        if ecu:                                              # ECU: the LAST SEEN line fills the box 560..1400 x 690..760
            ks = 840.0 / text_width('LAST SEEN WEARING A GREEN SWEATSHIRT', 800, 28, 0.04)   # the line spans the plan's box
            cv.translate(960, 748); cv.scale(ks, ks); cv.translate(-960, -(90 + 800))
        else:                                                # the whole poster above the caption band
            cv.translate(960, 66); cv.scale(0.82, 0.82); cv.translate(-960, -70)
        x0, y0, w, h = 560.0, 90.0, 800.0, 980.0
        path = rect(x0, y0, w, h)
        _paper(pen, path, (x0, y0, x0 + w, y0 + h), pal, 4, rain=1.0)
        text(cv, 'MISSING', 960, y0 + 150, 900, 132, '#b0141c', 255, 0.04, 'center')
        _photo_box(pen, x0 + 190, y0 + 200, 420, 420, 'noah13', pal, 'grin_kid', 0.36)
        text(cv, 'NOAH BRENNAN, 13', 960, y0 + 700, 900, 52, pal['ink'], 255, 0.03, 'center')
        text(cv, 'LAST SEEN JULY 18 · CAMP CEDAR LAKE', 960, y0 + 752, 700, 26, pal['ink'], 235, 0.06, 'center')
        text(cv, 'LAST SEEN WEARING A GREEN SWEATSHIRT', 960, y0 + 800, 800, 28, pal['ink'], 245, 0.04, 'center')
        text(cv, 'CEDAR LAKE PRINTED ON THE FRONT', 960, y0 + 838, 600, 22, pal['ink'], 200, 0.08, 'center')
        if not ecu:
            text(cv, 'IF YOU HAVE ANY INFORMATION CALL', 960, y0 + 900, 700, 20, pal['ink'], 190, 0.1, 'center')
            text(cv, '(555) 014-2288', 960, y0 + 936, 900, 30, pal['ink'], 220, 0.06, 'center')
        for (sx, sy) in ((x0 + 20, y0 + 20), (x0 + w - 20, y0 + 20)):
            pen.fill(oval(sx, sy, 10), '#c0c4cc'); pen.line(oval(sx, sy, 10), 2, '#4a4a50')
        cv.restore()
    elif kind == 'notice':
        pal = NIGHT
        x0, y0, w, h = 420.0, 160.0, 1080.0, 760.0
        path = rect(x0, y0, w, h)
        _paper(pen, path, (x0, y0, x0 + w, y0 + h), pal, 7, rain=0.4)
        pen.fill(rect(x0, y0, w, 120), '#d8a020')
        text(cv, 'NOTICE OF DEMOLITION', 960, y0 + 84, 900, 64, '#16171c', 255, 0.04, 'center')
        text(cv, 'CABINS 5-7', 960, y0 + 300, 900, 120, pal['ink'], 255, 0.02, 'center')
        text(cv, 'SAT 7:00 AM', 960, y0 + 470, 900, 110, '#b0141c', 255, 0.02, 'center')
        text(cv, 'BY ORDER OF THE COUNTY · KEEP OUT', 960, y0 + 600, 700, 30, pal['ink'], 220, 0.1, 'center')
        for (sx, sy) in ((x0 + 30, y0 + 30), (x0 + w - 30, y0 + 30), (x0 + 30, y0 + h - 30), (x0 + w - 30, y0 + h - 30)):
            pen.fill(rect(sx - 4, sy - 24, 8, 48), '#20232a')
        for m in marks:
            if m.get('what') == 'underline':
                k = ease_out_cubic(clamp((t - m['t']) / 0.25))
                if k > 0:
                    xa, xb = 960 - 330, 960 - 330 + 660 * k
                    wax(pen, [(lerp(xa, xb, i / 14), y0 + 500 + 6 * math.sin(i * 0.8)) for i in range(15)], 14, 1.0, 0.0, 5)
    elif kind == 'stencil':
        pal = NIGHT
        x0, y0, w, h = 240.0, 180.0, 1440.0, 720.0
        for j in range(5):                                   # slats
            sl = rect(x0, y0 + j * h / 5 + 6, w, h / 5 - 12)
            pen.linear(sl, x0, 0, x0 + w, 0, ['#8a6a48', '#a88560', '#7a5a3c'])
            pen.texture(sl, 'wood', 0.5, 'overlay', 1.0)
            pen.line(sl, 3, '#2a1e14')
        text(cv, 'SAVE FOR THE', 960, y0 + 300, 900, 96, '#1c1a1e', 230, 0.12, 'center')
        text(cv, 'MUSEUM', 960, y0 + 480, 900, 150, '#1c1a1e', 230, 0.16, 'center')
        fl = 0.0
        for m in marks:
            if m.get('what') == 'tag_flip': fl = clamp((t - m['t']) / 0.3)
        tx, ty = 1480.0, 690.0
        cv.drawLine(tx - 120, ty - 160, tx, ty - 40, paint('#d8d0c0', 255, 3))
        cv.save(); cv.translate(tx, ty); cv.rotate(-12 + 20 * math.sin(t * 2.2) * (1 - fl * 0.5))
        cv.scale(max(0.05, abs(math.cos(fl * math.pi))), 1)
        tag = rrect(-120, -60, 240, 150, 10)
        _paper(pen, tag, (-120, -60, 120, 90), dict(NIGHT, paper='#e6dcc0'), 3)
        pen.fill(oval(-90, -30, 10), '#5a5048')
        if fl < 0.5:
            text(cv, 'MUSEUM', 10, 0, 900, 30, '#1c1c24', 255, 0.06, 'center')
            text(cv, 'ITEM 0417', 10, 40, 700, 20, '#1c1c24', 220, 0.1, 'center')
        else:
            text(cv, 'CEDAR LAKE', 10, -4, 900, 22, '#1c1c24', 255, 0.04, 'center')
            text(cv, 'HISTORICAL SOC.', 10, 28, 700, 18, '#1c1c24', 230, 0.04, 'center')
        cv.restore()
    elif kind == 'card':
        pal = SEPIA
        x0, y0, w, h = 650.0, 70.0, 620.0, 940.0
        path = rrect(x0, y0, w, h, 34)
        _paper(pen, path, (x0, y0, x0 + w, y0 + h), dict(pal, paper='#f4ead4'), 5)
        cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
        inner = rect(x0 + 70, y0 + 90, w - 140, h - 180)
        pen.fill(inner, '#efe2c4')
        cv.save(); cv.clipPath(inner, skia.ClipOp.kIntersect, True)
        try:
            import characters as C
            P = C.Pose(); P.mix(C.queen_stage('S1')); P.lock = 1.0; P.t = 1.0
            mid = y0 + h / 2
            for rot in (0, 180):                               # the court card: the queen and her mirror image
                cv.save()
                if rot: cv.translate(960, mid); cv.rotate(180); cv.translate(-960, -mid)
                cv.clipRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, mid))
                pen.linear(rect(x0, y0, w, h / 2), 0, y0, 0, mid, ['#f2e6c8', '#e2cfa6'])
                C.draw_bust(pen, 'queen', 960, y0 + h * 0.30, 0.27, P, light=None, t=1.0)
                cv.restore()
        except Exception:
            pass
        cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, y0 + h), paint('#c09060', 70, None, blend=skia.BlendMode.kMultiply))
        cv.restore()
        pen.line(inner, 4, pal['ink'], 220)
        cv.drawLine(x0 + 70, y0 + h / 2, x0 + w - 70, y0 + h / 2, paint(pal['ink'], 160, 3))
        cv.restore()
        for (cx, cy, r) in ((x0 + 48, y0 + 70, 0), (x0 + w - 48, y0 + h - 70, 180)):
            cv.save(); cv.translate(cx, cy); cv.rotate(r)
            text(cv, 'Q', 0, 6, 900, 54, '#1c1414', 255, 0, 'center')
            sp = poly(_star(0, 0, 1.0, 0.42))
            cv.drawPath(_spade(0, 44, 18), paint('#1c1414', 255))
            cv.restore()
        pen.line(path, 4, '#5a4a3a', 230)
    elif kind == 'polaroid':
        pal = SEPIA
        x0, y0, w, h = 640.0, 130.0, 640.0, 760.0
        path = rect(x0, y0, w, h)
        cv.save(); cv.translate(960, 510); cv.rotate(-4); cv.translate(-960, -510)
        _paper(pen, path, (x0, y0, x0 + w, y0 + h), dict(pal, paper='#f2ead8'), 8)
        _photo_box(pen, x0 + 40, y0 + 40, w - 80, w - 80, 'noah13', pal, 'grin_kid', 0.5, sepia=True)
        try:
            import characters as C
            P = C.Pose('grin_kid'); P.t = 1.0
            C.draw_hands(pen, 'noah13', x0 + w * 0.68, y0 + w * 0.62, 190, P, light=None, t=1.0)
        except Exception:
            pass
        sc = Script(e.get('text', 'NOAH · JUNE').split('(')[0].strip(), 960, y0 + h - 60, 40, seed=31, align='center')
        write(pen, sc, 'marker', 1.0, 230, tip=False, c='#2a2a6a')
        cv.restore()
    elif kind == 'photo':
        pal = SEPIA
        x0, y0, w, h = 470.0, 90.0, 980.0, 760.0
        path = rect(x0, y0, w, h)
        cv.save(); cv.translate(960, 470); cv.rotate(2.5); cv.translate(-960, -470)
        _paper(pen, path, (x0, y0, x0 + w, y0 + h), dict(pal, paper='#f0e4c8'), 9)
        inner = rect(x0 + 36, y0 + 36, w - 72, h - 130)
        pen.fill(inner, '#d8c09a')
        cv.save(); cv.clipPath(inner, skia.ClipOp.kIntersect, True)
        pen.linear(inner, 0, y0, 0, y0 + h, ['#e8d4ae', '#a88a62'])
        _portrait(pen, 'you', 960, y0 + 470, 0.58, 'half_smile')
        _portrait(pen, 'noah13', 700, y0 + 560, 0.3, 'grin_kid')
        _portrait(pen, 'you_kid', 1220, y0 + 580, 0.28, 'happy')
        cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, y0 + h), paint('#b08050', 90, None, blend=skia.BlendMode.kMultiply))
        cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + w, y0 + h), paint('#f4dca8', 50, None, blend=skia.BlendMode.kScreen))
        cv.restore()
        pen.line(inner, 3, pal['ink'], 180)
        sc = Script('DAD · CEDAR LAKE', 960, y0 + h - 36, 34, seed=33, align='center')
        write(pen, sc, 'pencil', 1.0, 200, tip=False, c='#5a4a3a', w=3.5)
        cv.restore()
    elif kind == 'menu':
        pal = SEPIA
        x0, y0, w, h = 380.0, 120.0, 1160.0, 840.0
        frame = rect(x0 - 40, y0 - 40, w + 80, h + 80)
        pen.linear(frame, x0, 0, x0 + w, 0, ['#7a5434', '#a07850', '#6a4428'])
        pen.texture(frame, 'wood', 0.5, 'overlay', 1.0)
        board = rect(x0, y0, w, h)
        pen.fill(board, '#2e3a32')
        pen.texture(board, 'grunge', 0.35, 'screen', 1.4)
        for j in range(12):                                  # old erased chalk haze
            pen.radial(None, x0 + w * hash01(j, 5), y0 + h * hash01(j, 6), 160, [(0, '#ffffff', 18), (1, '#ffffff', 0)], sy=0.4, clip=False)
        kc = 0.0
        for m in marks:
            if m.get('what') == 'chalk': kc = clamp((t - m['t']) / 0.3)
        def cl(s, y, size, seed, a=1.0):
            sc = Script(s, 960, y, size, seed=seed, align='center', slant=0.05, track=0.2)
            write(pen, sc, 'chalk', 1.0, 255 * a * (1 - 0.45 * kc), tip=False, w=size * 0.11)
        cl('JULY 19', y0 + 150, 70, 3)
        cl('BREAKFAST 7:00', y0 + 330, 92, 5)
        cl('PANCAKES', y0 + 520, 108, 7)
        cl('OJ · MILK · FRUIT', y0 + 680, 52, 9, 0.8)
        if kc > 0:                                               # struck through, then CANCELED chalked across in pink
            for j, (yy, w_) in enumerate(((y0 + 300, 600), (y0 + 488, 560))):
                kk = clamp(kc * 2 - j * 0.3)
                chalk_line(pen, [(960 - w_ / 2, yy + 14), (960 - w_ / 2 + w_ * kk, yy - 6)], 12, 1.0, 40 + j, '#ffffff')
            cv.save(); cv.translate(960, y0 + 430); cv.rotate(-12)
            sc = Script('CANCELED', 0, 70, 160, seed=13, align='center', slant=0.1, track=0.2)
            write(pen, sc, 'chalk', kc, 255, tip=True, w=22, c='#ffb0bc')
            cv.restore()
    elif kind == 'sign':
        pal = SEPIA
        x0, y0, w, h = 520.0, 300.0, 880.0, 420.0
        cv.drawLine(x0 + 60, 0, x0 + 120, y0, paint('#5a5a60', 255, 8)); cv.drawLine(x0 + w - 60, 0, x0 + w - 120, y0, paint('#5a5a60', 255, 8))
        cv.save(); cv.translate(960, y0); cv.rotate(2.5 * math.sin(t * 1.8)); cv.translate(-960, -y0)
        sg = rrect(x0, y0, w, h, 14)
        soft_shadow(cv, sg, 170, 26, 8, 14)
        pen.linear(sg, x0, y0, x0, y0 + h, ['#e8dcc0', '#c8b48e'])
        pen.texture(sg, 'wood', 0.35, 'multiply', 1.0)
        pen.line(sg, 6, pal['ink'])
        text(cv, 'CAMP', 960, y0 + 170, 900, 130, pal['red'], 255, 0.06, 'center')
        text(cv, 'CLOSED', 960, y0 + 330, 900, 150, pal['red'], 255, 0.06, 'center')
        cv.restore()
        for j in range(9):                                     # the chain across the gate below
            cx_ = 300 + j * 150
            cv.drawOval(skia.Rect.MakeLTRB(cx_ - 50, 880 - 22, cx_ + 50, 880 + 22), paint('#8a8a90', 255, 10))
    return


def _spade(x, y, r):
    p = smooth([(x, y - r), (x + r * 0.9, y + r * 0.1), (x + r * 0.5, y + r * 0.7), (x, y + r * 0.35), (x - r * 0.5, y + r * 0.7),
                (x - r * 0.9, y + r * 0.1)], True, 0.7)
    return union(p, poly([(x, y + r * 0.2), (x + r * 0.35, y + r * 1.1), (x - r * 0.35, y + r * 1.1)]))


DOC_VIEWS = {('camp_gate', 'poster'): 'poster', ('camp_gate', 'poster_ecu'): 'poster', ('camp_gate', 'notice'): 'notice',
             ('mess_porch', 'crate_cu'): 'stencil', ('memory', 'card_queen'): 'card', ('memory', 'polaroid'): 'polaroid',
             ('memory', 'dad_photo'): 'photo', ('memory', 'menu_board'): 'menu', ('memory', 'gate_close'): 'sign'}


def doc_kind(sh):
    for e in sh.get('hud', []):
        if e['type'] == 'doc': return e['kind'], e
    k = DOC_VIEWS.get((sh.get('set'), sh.get('view')))
    return (k, {}) if k else (None, None)


def doc_layer(sh, depth=1.0):
    """A set Layer that draws the shot's document (with its marks) at the subject plane; None if the shot has none.
    Static parts are cached by the layer only when the doc has no marks."""
    if sh.get('type') != 'DOC' and not any(e['type'] == 'doc' for e in sh.get('hud', [])): return None
    kind, e = doc_kind(sh)
    if kind is None: return None
    from engine.scene import Layer
    if kind == 'sign' and sh.get('type') != 'DOC': return None
    animated = bool((e or {}).get('marks')) or kind in ('stencil', 'sign')

    def draw(pen, t):
        draw_doc(pen, kind, t, sh, e)
    return Layer(depth, draw, 'doc_' + kind, blur=0, cache=(False if animated else 'doc_%s_%s' % (kind, sh.get('view'))))
