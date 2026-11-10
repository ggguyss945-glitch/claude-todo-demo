"""ui_v2: on-screen text, type, diagrams and the rule cards of the v2 film (DIRECTION_V2 5.3-5.5, PLAN_V2 2.3).

One entry point draws everything a shot's HUD asks for (shots.json `hud[]`, `chip`, `teaser`, `glint`, `tr`, `fx_post`,
`split`, `montage`, the counter and the captions):

    import ui_v2
    UI = ui_v2.UI(plan)                          # plan = plan/shots.json dict (Film.P); one per Film
    UI.hud(cv, t, sh, cs=None, film=None)        # inside render_frame's hud callback (design coords, after the grade)
    img = UI.frame_fx(img, t, sh, frame_i)       # after render_frame: RGB split, rewind tear, pixel sort (numpy RGB)
    layer = ui_v2.doc_layer(sh)                  # DOC shots: the paper object as a set Layer (gets push, DOF, grade)

`cs` is the shot camera state (Cam.at(t)): labels, count numerals, D1 and the highlighter are pinned to the glass /
paper plane (depth 1.0) through engine.scene.project, so they ride the push.

The pieces are importable on their own (UI_V2.md documents each): caption, header, chip, ring_badge, giant_number,
cmd_tag, red_x, pin_label, teaser_border, glint, smear_carry, rewind_overlay, kinetic_title, typebeat, end_card,
stamp, highlight, count_pop, circle_mark, balloon, like_sub, time_card; the rule card (ui_v2_card.rule_card); the
diagrams, documents and phone states (ui_v2_diag).
"""
import bisect, math
import numpy as np
import cv2
import skia
from engine.core import (CFG, DW, DH, Pen, col, mix, text, text_width, rrect, rect, oval, poly, smooth, union, minus,
                         clamp, lerp, prog, ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, hash01, noise1)
from ui_v2_letter import (LIP, LIP_DK, LIP_HI, LIP_GLOW, LIP_CORE, RED, CHALK, GREASE, MARKER, INK_RED, GOLD, CHIP, paint, blur_mf,
                          sprite, blit, Script, write, wax, chalk_line, marker_line, dotted, arrow_head, ring_pts, text_path,
                          soft_shadow, fit_size, offset_pts)

FPS = 60
HEADER_Y, HEADER_SIZE = 61, 15.5
CHIP_X, CHIP_Y, CHIP_H = 44, 108, 46                  # chip slot: left edge, centre line, height (cap 1.75 % H)
BADGE_X, BADGE_Y, BADGE_R = 1792, 126, 50             # Tess's ring timer
CAP_Y, CAP_SIZE = 976, 33                             # caption baseline (centre at 0.893 H), size (cap 2.1 % H)
GIANT_HOLD, GIANT_FLY = 0.50, 0.22                    # giant number: hold, then the flight into the badge
CAP_FADE_IN, CAP_FADE_OUT = 0.12, 0.06


# ==================================================================================================== clocks (as sets.py)
def clock_ours(t):
    base = -180.0 + (t - 19.40)
    if t < 278.97: return base
    b0 = -180.0 + (278.97 - 19.40)
    if t < 281.81: return b0 - (t - 278.97)
    return b0 - (281.81 - 278.97) + (t - 281.81)


def clock_theirs(t):
    """Seconds after 06:00 on the other side: 06:59:40 + ((t - 297.59) mod 19.48); 07:00:00 from 538.70 (D9)."""
    if t >= 538.70: return 3600.0
    return 3580.0 + ((t - 297.59) % 19.48)


def _tc(sec, frac_fps=30):
    sec = sec % 86400.0
    hh, mm, ss = int(sec // 3600), int(sec // 60) % 60, int(sec) % 60
    ff = int((sec - math.floor(sec)) * frac_fps) % frac_fps
    return '%02d:%02d:%02d:%02d' % (hh, mm, ss, ff)


# ==================================================================================================== captions + header
def caption(cv, s, alpha=255):
    """REF: white bold caps, letter-spaced, one line centred on y 0.893 H, cap height 2.1 % H, soft dark halo."""
    if not s or alpha <= 0: return
    s = s.upper()
    size, sp = CAP_SIZE, 0.045
    w = text_width(s, 700, size, sp)
    if w > 1500:
        size = size * 1500 / w; w = 1500
    a = alpha / 255.0
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(DW / 2 - w / 2 - 30, CAP_Y - 36, w + 60, 50), 24, 24),
                 paint('#000000', 140 * a, None, blur=18.0))
    text(cv, s, DW / 2, CAP_Y, 700, size, '#ffffff', alpha, sp, 'center', 1.0)


def caption_alpha(c, t):
    """Soft fade: in over 0.12 s, out over the last 0.06 s (a following caption fades in over it)."""
    return 255.0 * ease(clamp((t - c['t0']) / CAP_FADE_IN)) * ease(clamp((c['t1'] - t) / CAP_FADE_OUT + 0.25))


def header(cv, sh, t):
    hd = sh.get('header') or {}
    left = hd.get('left') or ''
    op = float(hd.get('opacity', 0.2) or 0.2)
    size, y, sp = HEADER_SIZE, HEADER_Y, 0.22
    if '//' in left:
        a_, b_ = left.split('//', 1)
        w = text(cv, a_.rstrip() + '  //  ', 44, y, 600, size, '#ffffff', 255 * op, sp, 'left')
        text(cv, b_.strip(), 44 + w + sp * size, y, 700, size, '#ffffff', 255 * min(1.0, op * 1.8), sp, 'left')
    else:
        text(cv, left, 44, y, 600, size, '#ffffff', 255 * op, sp, 'left')
    mode = hd.get('clock_mode', 'hidden')
    if mode == 'hidden' or t < 19.1: return
    a, dx, c = op * 1.1, 0.0, '#ffffff'
    if mode == 'ours':
        s = _tc(clock_ours(t))
        if 278.97 <= t < 281.81:                       # the clock runs backward: flicker, jitter, a red cast
            a = op + 0.45 * (hash01(int(t * 30), 5) > 0.55); dx = 6.0 * (hash01(int(t * 30), 6) - 0.5); c = '#ff9aa4'
    elif mode == 'theirs':
        s = _tc(6 * 3600 + clock_theirs(t))
        ph = (t - 297.59) % 19.48
        if ph < 2.0 / FPS + 1e-4 and t > 297.6: a, dx = 0.6, 9.0
    elif mode == 'stuck':
        s = '07:00:00:00'; a = op + 0.06 * math.sin(t * 9.0)
    elif mode == 'memory':
        s = '14 YEARS AGO'
    else:
        return
    text(cv, s, DW - 44 + dx, y, 600, size, c, 255 * a, sp, 'right')


# ==================================================================================================== chips
def _loop_icon(cv, x, y, r, c, a, spin=0.0):
    p = skia.Path(); p.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), -60 + spin, 290)
    cv.drawPath(p, paint(c, a, r * 0.34))
    ang = math.radians(-60 + spin)
    hx, hy = x + r * math.cos(ang), y + r * math.sin(ang)
    d = math.radians(-60 + spin - 90)
    tip = (hx + math.cos(d + math.pi) * 0.0, hy)
    cv.drawPath(poly([(hx + r * 0.55 * math.cos(ang), hy + r * 0.55 * math.sin(ang)),
                      (hx - r * 0.55 * math.cos(ang), hy - r * 0.55 * math.sin(ang)),
                      (hx + r * 0.62 * math.cos(d + math.pi), hy + r * 0.62 * math.sin(d + math.pi))]), paint(c, a))


def chip(cv, s, style='ours', u=10.0, x=CHIP_X, y=CHIP_Y, alpha=255, out=None):
    """Place / time chip (top-left under the header). u = seconds since it appeared (0.4 s pop); out = seconds left
    (fades in the last 0.12 s). Styles: ours (navy, blue dot), theirs (gold, amber dot), loop (plum, loop arrow),
    teaser (red), stairs, climax, ending; memory = the red-brown rubber stamp rotated -4 deg. Returns its right edge."""
    if u < 0 or alpha <= 0: return x
    a = alpha * clamp(u / 0.08)
    if out is not None: a *= clamp(out / 0.12)
    if a <= 1: return x
    if style == 'memory':
        return _stamp_chip(cv, s, u, x, y, a)
    fill, edge, dot, tc = CHIP.get(style, CHIP['ours'])
    size, sp = 26.5, 0.13
    parts = [p.strip() for p in s.split('·')]
    tws = [text_width(p, 700 if i == 0 else 800, size, sp) for i, p in enumerate(parts)]
    sep = 34.0
    tw = sum(tws) + sep * (len(parts) - 1)
    lead = 48.0
    W = lead + tw + 20.0
    quick = style == 'teaser'                                # flash-forwards are 0.6 s: no delay
    k = ease_out_back(clamp(u / (0.08 if quick else 0.28)), 1.4)   # the chip opens from its dot
    w = 40.0 + (W - 40.0) * clamp(k)
    h = CHIP_H
    box = rrect(x, y - h / 2, w, h, h / 2)
    soft_shadow(cv, box, 120 * a / 255, 10, 0, 4)
    cv.drawPath(box, paint(fill, 0.88 * a))
    Pen(cv).linear(box, x, y - h / 2, x, y + h / 2, [(0, '#ffffff', 26), (0.5, '#ffffff', 0), (1, '#000000', 30)], a / 255)
    cv.drawPath(box, paint(edge, 0.95 * a, 1.6))
    cx_ = x + 23
    if style == 'loop':
        _loop_icon(cv, cx_, y, 10.5, dot, a, spin=-u * 260.0)
    else:
        pulse = 0.55 + 0.45 * math.sin(u * 5.0)
        cv.drawCircle(cx_, y, 13 + 3 * pulse, paint(dot, 70 * pulse * a / 255, None, blur=5))
        cv.drawCircle(cx_, y, 7.0, paint(dot, a))
    ta = a * (clamp((u - 0.02) / 0.05) if quick else clamp((u - 0.10) / 0.18))
    if ta > 0:
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(x, y - h, x + w - 6, y + h))
        xx = x + lead
        for i, p in enumerate(parts):
            c_ = tc if i == 0 else mix(tc, '#ffffff', 0.5)
            text(cv, p, xx, y + size * 0.36, 700 if i == 0 else 800, size, c_, ta * (0.86 if i == 0 else 1.0), sp, 'left')
            xx += tws[i]
            if i < len(parts) - 1:
                cv.drawCircle(xx + sep / 2, y, 3.2, paint(dot, ta)); xx += sep
        cv.restore()
    return x + w


def _stamp_chip(cv, s, u, x, y, a):
    """MEMORY: the `14 YEARS AGO` rubber stamp, red-brown, rotated -4 deg, slammed in."""
    c = '#b8452a'
    k = clamp(u / 0.11)
    sc = 1.0 + 0.45 * (1 - ease_in_cubic(k)) if k < 1 else 1.0 + 0.03 * math.exp(-(u - 0.11) * 30) * math.sin((u - 0.11) * 60)
    size = 30.0
    tw = text_width(s, 900, size, 0.12)
    w, h = tw + 40, 54
    cx_, cy_ = x + w / 2, y + 2
    def draw(c_):
        b = rrect(-w / 2, -h / 2, w, h, 4)
        c_.drawPath(b, paint(c, 235, 3.4)); c_.drawPath(rrect(-w / 2 + 5, -h / 2 + 5, w - 10, h - 10, 2), paint(c, 200, 1.4))
        text(c_, s, 0, size * 0.36, 900, size, c, 240, 0.12, 'center')
        for i in range(40):                                  # worn ink
            px, py = (hash01(i, 71) - 0.5) * w, (hash01(i, 72) - 0.5) * h
            r = 0.8 + 2.4 * hash01(i, 73) ** 2
            c_.drawCircle(px, py, r, paint('#000000', 255, None, blend=skia.BlendMode.kDstOut))
    spr = sprite(('stampchip', s), (-w / 2 - 8, -h / 2 - 8, w / 2 + 8, h / 2 + 8), draw, 1.0)
    cv.save(); cv.translate(cx_, cy_); cv.rotate(-4.0); cv.scale(sc, sc)
    blit(cv, spr, min(255.0, a * 1.15) * (0.4 + 0.6 * k))
    cv.restore()
    return x + w


# ==================================================================================================== Tess's ring timer
def ring_badge(cv, value, t, u_step, kind='step', alpha=255, prev=None, leave=0.0):
    """Ring timer badge: a ring that depletes clockwise with the count (60 = full), the number inside, TESS above it.
    u_step = seconds since the value changed (0.12 s tick; calls pop 1.35x with a red flash; 0 flashes red).
    leave 0..1: the badge glitches away (card 7)."""
    a = alpha
    if a <= 1: return
    sc = 1.0; flash = 0.0
    if kind in ('call', 'zero'):
        sc = 1.0 + 0.35 * (1.0 - ease_out_cubic(clamp(u_step / 0.26)))
        flash = 1.0 - clamp(u_step / 0.45)
    else:
        sc = 1.0 + 0.07 * (1.0 - clamp(u_step / 0.12))
    if kind == 'zero': flash = max(flash, 0.55 + 0.45 * math.sin(u_step * 18.0))
    frac_new = clamp(value / 60.0)
    frac_old = clamp((prev if prev is not None else value) / 60.0)
    fr = lerp(frac_old, frac_new, ease_out_cubic(clamp(u_step / 0.12)))
    x, y, R = BADGE_X, BADGE_Y, BADGE_R
    if leave > 0:
        x += (hash01(int(leave * 40), 3) - 0.5) * 40 * leave; a *= 1.0 - leave
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    disc = oval(0, 0, R + 8)
    soft_shadow(cv, disc, 130 * a / 255, 12, 0, 5)
    cv.drawPath(disc, paint('#0b1024', 0.80 * a))
    low = value <= 5
    rc = mix('#ffffff', '#ff3048', clamp(flash + (0.85 if low else 0.0)))
    cv.drawCircle(0, 0, R - 4, paint('#ffffff', 0.16 * a, 7))
    if fr > 0.001:
        arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(-R + 4, -R + 4, R - 4, R - 4), -90, 360 * fr)
        if flash > 0: cv.drawPath(arc, paint('#ff3048', 160 * flash * a / 255, 16, blur=8))
        cv.drawPath(arc, paint(rc, a, 7))
        ea = math.radians(-90 + 360 * fr)                     # the bright moving end
        cv.drawCircle((R - 4) * math.cos(ea), (R - 4) * math.sin(ea), 5.0, paint('#ffffff', a))
    for k in range(12):                                       # 5-second ticks
        an = math.radians(-90 + k * 30)
        cv.drawLine((R + 2) * math.cos(an), (R + 2) * math.sin(an), (R + 6) * math.cos(an), (R + 6) * math.sin(an), paint('#ffffff', 0.35 * a, 1.6))
    text(cv, 'TESS', 0, -17, 700, 11.5, '#ffffff', 0.45 * a, 0.3, 'center')
    nc = mix('#ffffff', '#ff4b55', clamp(flash)) if kind != 'zero' else '#ff3b46'
    text(cv, '%d' % value, 0, 21, 800, 38, nc, a, 0.0, 'center', 0.0, glow=('#ff2030', 150 * flash, 10) if flash > 0.05 else None)
    cv.restore()


class Counter:
    """The plan counter (shots.json `counter`) resolved against the giant numbers: a call's new value shows when its
    giant number lands in the badge (t + 0.5 + 0.22); the badge itself first appears when 60 lands."""

    def __init__(self, C, giants):
        self.C = C
        self.steps = []
        gts = sorted(giants)
        for ts, v, kind in C['steps']:
            show = ts
            if kind == 'call':
                j = bisect.bisect_left(gts, ts - 0.06)
                if j < len(gts) and abs(gts[j] - ts) < 0.06: show = gts[j] + GIANT_HOLD + GIANT_FLY
            self.steps.append((show, v, kind))
        self.steps.sort()
        self.t_show = [s[0] for s in self.steps]
        self.v0, self.v1 = C['visible']

    def draw(self, cv, t, sh):
        if not self.steps or t < self.t_show[0] or t > self.v1 + 0.35: return
        if sh.get('side') in ('card', 'black') or sh.get('type') in ('CARD', 'BLACK'): return
        if sh.get('type') in ('TYPE',) or sh.get('world') == 'ui': return
        j = bisect.bisect_right(self.t_show, t) - 1
        if j < 0: return
        ts, v, kind = self.steps[j]
        prev = self.steps[j - 1][1] if j > 0 else None
        dim = 0.6 if sh.get('world') == 'memory' or sh.get('side') == 'memory' else 1.0
        a_in = ease_out_cubic(clamp((t - self.t_show[0]) / 0.2))
        leave = clamp((t - self.v1) / 0.3)
        ring_badge(cv, v, t, t - ts, kind, 255 * dim * a_in, prev, leave)


# ==================================================================================================== giant numbers (type beat 4)
def _giant_sprite(value):
    size = 585.0                                              # cap 0.38 H = 410 px
    s = '%d' % value
    tw = text_width(s, 900, size, -0.02)

    def draw(c):
        path, w = text_path(s, -tw / 2, size * 0.36, 900, size, -0.02)
        q = skia.Path(path); q.offset(0, 18)
        c.drawPath(q, paint('#000000', 170, None, blur=22))
        c.drawPath(path, paint('#ffffff', 255, 22))
        Pen(c).linear(path, 0, -size * 0.36, 0, size * 0.36, [(0, '#ff5468'), (0.55, '#e3233d'), (1, '#9c1024')])
        c.drawPath(path, paint('#5a0814', 200, 3))
        c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
        Pen(c).linear(rect(-tw, -size * 0.40, tw * 2, size * 0.18), 0, -size * 0.40, 0, -size * 0.22,
                      [(0, '#ffffff', 90), (1, '#ffffff', 0)])
        c.restore()
    return sprite(('giant', value), (-tw / 2 - 80, -size * 0.45, tw / 2 + 80, size * 0.55), draw, 1.0)


def giant_number(cv, e, t, x=960, y=520):
    """Tess's call as a giant red numeral in a ring at 38 % H: slams in, holds 0.5 s, flies into the badge."""
    u = t - e['t']
    v = int(e['value'])
    hold = float(e.get('hold', GIANT_HOLD)) if v != 0 else 9.0      # 0 holds until the card 7 glitch cuts it
    if u < 0 or u > hold + GIANT_FLY + 0.02: return
    R = 380.0
    fly = clamp((u - hold) / GIANT_FLY)
    kf = ease_in_cubic(fly)
    cx, cy = lerp(x, BADGE_X, kf), lerp(y, BADGE_Y, kf)
    sc = lerp(1.0, (BADGE_R * 0.9) / R, kf)
    slam = ease_out_back(clamp(u / 0.10), 2.0)
    sc *= lerp(1.55, 1.0, slam)
    a = 255 * clamp(u / 0.04)
    if u < 2.0 / FPS:                                         # the hit frame: a red-white flash on the whole frame
        cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#ff2a3a', 60))
    tr = (hash01(int(u * 60), 9) - 0.5) * 6 * (1 - fly) if 0.1 < u < hold else 0.0
    cv.save(); cv.translate(cx + tr, cy); cv.scale(sc, sc)
    if fly < 0.98:
        cv.drawCircle(0, 0, R + 40, paint('#000000', 0.32 * a * (1 - fly), None, blur=40))
    frac = clamp(v / 60.0)
    trk = skia.Path(); trk.addCircle(0, 0, R)
    dash = paint('#ffffff', 0.20 * a, 6); dash.setPathEffect(skia.DashPathEffect.Make([18, 14], u * 60))
    cv.drawPath(trk, dash)
    if frac > 0:
        arc = skia.Path(); arc.addArc(skia.Rect.MakeLTRB(-R, -R, R, R), -90, 360 * frac * ease_out_cubic(clamp(u / 0.2)))
        cv.drawPath(arc, paint('#ff2a40', 0.55 * a, 34, blur=18))
        cv.drawPath(arc, paint('#ff3048', a, 12))
        cv.drawPath(arc, paint('#ffd0d6', 0.7 * a, 3))
    ring_k = clamp(u / 0.22)
    if ring_k < 1:                                           # shock ring
        cv.drawCircle(0, 0, R * (1.0 + 0.5 * ease_out_cubic(ring_k)), paint('#ffffff', 200 * (1 - ring_k) * a / 255, 10 * (1 - ring_k) + 1))
    blit(cv, _giant_sprite(v), a)
    if v == 0:
        fl = 0.5 + 0.5 * math.sin(u * 30)
        cv.drawCircle(0, 0, R * 0.8, paint('#ff2030', 70 * fl * a / 255, None, blur=50))
    cv.restore()
    if fly > 0:                                              # trail
        for k in range(1, 4):
            kk = ease_in_cubic(clamp(fly - k * 0.12))
            if kk <= 0: continue
            tx, ty = lerp(x, BADGE_X, kk), lerp(y, BADGE_Y, kk)
            cv.drawCircle(tx, ty, R * lerp(1.0, 0.12, kk) * 0.5, paint('#ff3048', 40 / k, None, blur=20))


# ==================================================================================================== command tags, red X, labels
def _tag_sprite(s, size=64):
    tw = text_width(s, 900, size, 0.06)

    def draw(c):
        path, w = text_path(s, -tw / 2, size * 0.36, 900, size, 0.06)
        c.drawPath(path, paint('#000000', 190, None, blur=16))
        q = skia.Path(path); q.offset(0, 5); c.drawPath(q, paint('#1a0206', 230))
        c.drawPath(path, paint(LIP_DK, 255, 5))
        Pen(c).linear(path, 0, -size * 0.4, 0, size * 0.4, [(0, '#f04a62'), (0.5, '#d22e46'), (1, '#a01a30')])
        c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
        for j in range(9):                                    # wax drag streaks across the letters
            yy = -size * 0.36 + j * size * 0.09
            c.drawLine(-tw / 2, yy, tw / 2, yy + 3, paint(LIP_DK if j % 2 else '#ff8a98', 40, size * 0.02))
        Pen(c).linear(rect(-tw, -size * 0.40, tw * 2, size * 0.14), 0, -size * 0.40, 0, -size * 0.26, [(0, '#ffd0d6', 120), (1, '#ffd0d6', 0)])
        c.restore()
    return sprite(('tag', s, size), (-tw / 2 - 40, -size * 0.8, tw / 2 + 40, size * 0.75), draw, 1.0), tw


def cmd_tag(cv, s, x, y, u, hold, size=64):
    """Command tag: lipstick-red text with no box (6 in the film). Pops in 4 frames with an overshoot, a lipstick
    underline swipes under it, out in 3 frames."""
    if u < 0 or u > hold + 3.0 / FPS: return
    k_in = clamp(u / (4.0 / FPS))
    sc = 1.0 + 0.28 * (1.0 - ease_out_back(clamp(u / 0.12), 2.4)) if u < 0.12 else 1.0
    a = 255 * min(k_in, clamp((hold - u) / (3.0 / FPS) + 1.0) if u > hold else 1.0)
    if a <= 0: return
    spr, tw = _tag_sprite(s.upper(), size)
    cv.save(); cv.translate(x, y); cv.rotate(-1.5); cv.scale(sc, sc)
    blit(cv, spr, a)
    uk = ease_out_cubic(clamp((u - 0.07) / 0.16))
    if uk > 0:
        x0, x1 = -tw / 2 - 10, -tw / 2 - 10 + (tw + 30) * uk
        pts = [(lerp(x0, x1, i / 12), size * 0.62 + 4 * math.sin(i * 0.9) - i * 0.6) for i in range(13)]
        wax(Pen(cv), pts, size * 0.13, a / 255, 0.3, seed=len(s))
    cv.restore()


def red_x(cv, x, y, r, u, hold):
    """The red X (4 in the film): ring draws in 0.09 s, two strokes, a 1-frame red flash; out in 0.1 s."""
    pen = Pen(cv)
    if u < 0: return
    if u < 1.5 / FPS:
        cv.drawRect(skia.Rect.MakeLTRB(-50, -50, DW + 50, DH + 50), paint('#ff1020', 60))
    out = 1.0 - clamp((u - hold) / 0.1)
    a = 255 * out
    if a <= 0: return
    kr = ease_out_cubic(clamp(u / 0.09))
    ring = skia.Path(); ring.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), -90, 360 * kr)
    cv.drawPath(ring, paint('#000000', a * 0.35, 30, blur=12))
    cv.drawPath(ring, paint('#ff1a28', a * 0.3, 26, blur=14))
    cv.drawPath(ring, paint('#e3262e', a, 11))
    k1 = ease_out_cubic(clamp((u - 0.03) / 0.085)); k2 = ease_out_cubic(clamp((u - 0.1) / 0.085))
    d = r * 0.62
    for (k, (ax, ay, bx, by)) in ((k1, (x - d, y - d, x + d, y + d)), (k2, (x + d, y - d, x - d, y + d))):
        if k <= 0: continue
        ex, ey = lerp(ax, bx, k), lerp(ay, by, k)
        cv.drawLine(ax, ay, ex, ey, paint('#000000', a * 0.35, 34, blur=10))
        cv.drawLine(ax, ay, ex, ey, paint('#ff1a28', a * 0.3, 30))
        cv.drawLine(ax, ay, ex, ey, paint('#e3262e', a, 15))


def _proj(x, y, cs, d=1.0):
    if cs is None: return x, y
    try:
        from engine.scene import project
        X, Y = project(x, y, d, cs)
        return float(X), float(Y)
    except Exception:
        return x, y


def white_tag(cv, s, x, y, u=None, alpha=255, size=24):
    a = alpha; sc = 1.0
    if u is not None:
        if u < 0: return
        a *= clamp(u / 0.06); sc = 0.72 + 0.28 * ease_out_back(clamp(u / 0.2), 2.2)
    tw = text_width(s, 800, size, 0.1)
    bw, h = tw + size * 1.9, size * 1.75
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    box = rrect(-bw / 2, -h / 2, bw, h, 6)
    soft_shadow(cv, box, 130 * a / 255, 12, 0, 6)
    cv.drawPath(box, paint('#f4f2ec', a))
    text(cv, s, 0, size * 0.36, 800, size, '#16171c', a, 0.1, 'center')
    cv.restore()


def pin_label(cv, e, u, cs=None):
    """Label with a leader line, pinned to a point on the subject plane (projected through the camera)."""
    hold = e.get('hold', 1.0)
    if u < 0 or u > hold + 0.12: return
    px, py = e['pin']
    X, Y = _proj(px, py, cs, float(e.get('d', 1.0)))
    tx, ty = clamp(X + e.get('dx', 0), 170, DW - 170), clamp(Y + e.get('dy', 0), 130, 880)
    out = 1.0 - clamp((u - hold) / 0.12)
    k = ease_out_cubic(clamp(u / 0.15))
    a = 255 * out
    cv.drawLine(X, Y, X + (tx - X) * k, Y + (ty - Y) * k, paint('#000000', a * 0.4, 6, blur=3))
    cv.drawLine(X, Y, X + (tx - X) * k, Y + (ty - Y) * k, paint('#ffffff', a * 0.92, 3.0))
    cv.drawCircle(X, Y, 7, paint('#ffffff', a))
    cv.drawCircle(X, Y, 14 + 6 * math.sin(u * 8.0), paint('#ffffff', a * 0.55 * k, 2.5))
    if u > 0.08:
        white_tag(cv, e['text'], tx, ty, u - 0.08, a, 30)


# ==================================================================================================== teasers, glint, smear, rewind
def teaser_border(cv, u, px=6.0, alpha=255):
    """Flash-forward border: a red 6 px frame with an inner glow, flickering in its first 6 frames."""
    fl = 1.0 if u > 6.0 / FPS else (0.4 + 0.6 * (int(u * FPS) % 2))
    a = alpha * fl
    pen = Pen(cv)
    k = px * 1.333                                          # design px for 6 px at 1440
    cv.drawRect(skia.Rect.MakeLTRB(k / 2, k / 2, DW - k / 2, DH - k / 2), paint('#ff1a2c', 0.45 * a, k * 5, blur=k * 3))
    cv.drawRect(skia.Rect.MakeLTRB(k / 2, k / 2, DW - k / 2, DH - k / 2), paint('#e01020', a, k))
    if u < 0.5:                                              # REC-like blink dot by the chip
        pass


def glint(cv, u, alpha=1.0):
    """Side-switch cue: a diagonal white streak at 60 % alpha with a 6 px chromatic fringe, crossing in 3 frames."""
    k = u / (3.0 / FPS)
    if k < 0 or k >= 1: return
    xc = lerp(-150, DW + 150, (math.floor(k * 3) + 0.5) / 3.0)        # one position per frame: left, centre, right
    ang = -28.0
    fr = 6 * 1.333
    cv.save(); cv.translate(xc, DH / 2); cv.rotate(ang)
    W, L = 260.0, 2600.0
    for dx, c_, a_ in ((-fr, '#ff2a40', 0.28), (fr, '#2ad8ff', 0.28), (0, '#ffffff', 0.6)):
        Pen(cv).linear(rect(-W / 2 + dx, -L / 2, W, L), -W / 2 + dx, 0, W / 2 + dx, 0,
                       [(0, c_, 0), (0.42, c_, 255 * a_ * 0.55), (0.5, c_, 255 * a_), (0.58, c_, 255 * a_ * 0.55), (1, c_, 0)], alpha)
    cv.drawRect(skia.Rect.MakeLTRB(-6, -L / 2, 6, L / 2), paint('#ffffff', 150 * alpha))
    cv.restore()


def smear_carry(cv, u, dur=0.2):
    """The card's finger-wipe exit carried over the next shot: pink-white lipstick streaks sliding off right."""
    k = u / dur
    if k < 0 or k >= 1: return
    a = 1.0 - ease(k)
    xc = lerp(DW * 0.55, DW * 1.25, ease_out_cubic(k))
    cv.save(); cv.translate(xc, DH / 2); cv.rotate(-14)
    for j in range(7):
        o = -300 + j * 95 + 30 * math.sin(j * 1.7)
        w = 40 + 50 * hash01(j, 5)
        c_ = '#e8a0aa' if j % 2 else '#fff0f2'
        cv.drawRect(skia.Rect.MakeLTRB(o - w / 2, -900, o + w / 2, 900), paint(c_, 70 * a, None, blur=20))
    cv.restore()


def rewind_overlay(cv, u, dur=0.2):
    """Loop reset (the picture side is in frame_fx): a VHS rewind glyph and tracking lines for 0.2 s."""
    if u < 0 or u > dur: return
    k = u / dur
    a = 255 * (1.0 - k * 0.6)
    x, y = 60, 160
    for j in range(2):
        xx = x + j * 26
        cv.drawPath(poly([(xx + 26, y - 18), (xx + 26, y + 18), (xx, y)]), paint('#ffffff', a))
    text(cv, 'REWIND', x + 70, y + 8, 800, 20, '#ffffff', a, 0.16, 'left')
    for j in range(3):
        yy = (DH * (1 - ((k * 2.5 + j * 0.33) % 1.0)))
        cv.drawRect(skia.Rect.MakeLTRB(0, yy, DW, yy + 10 + 8 * j), paint('#ffffff', 40 + 30 * j))


# ==================================================================================================== type beats
_KT = {}


def _type_sprite(s, size, fill='#ffffff', weight=900, sp=0.02, red=False, key=None):
    tw = text_width(s, weight, size, sp)

    def draw(c):
        path, w = text_path(s, -tw / 2, size * 0.36, weight, size, sp)
        q = skia.Path(path); q.offset(0, size * 0.05)
        c.drawPath(q, paint('#000000', 200, None, blur=size * 0.09))
        if red:
            c.drawPath(path, paint(LIP_GLOW, 70, None, blur=size * 0.12))
            c.drawPath(path, paint(LIP_DK, 255, size * 0.05))
            Pen(c).linear(path, 0, -size * 0.38, 0, size * 0.38, [(0, '#ee4a62'), (0.55, LIP), (1, '#8e1a2c')])
            c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
            for j in range(12):
                yy = -size * 0.36 + j * size * 0.065
                c.drawLine(-tw / 2, yy, tw / 2, yy + size * 0.02, paint(LIP_DK if j % 2 else '#ff8a98', 45, size * 0.012))
            Pen(c).linear(rect(-tw, -size * 0.40, tw * 2, size * 0.16), 0, -size * 0.40, 0, -size * 0.24, [(0, '#ffd0d6', 130), (1, '#ffd0d6', 0)])
            c.restore()
        else:
            c.drawPath(path, paint(fill, 255))
            c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
            Pen(c).linear(rect(-tw, size * 0.0, tw * 2, size * 0.4), 0, 0, 0, size * 0.4, [(0, '#000000', 0), (1, '#000000', 40)])
            c.restore()
    return sprite(('type', s, round(size, 1), fill, weight, red, key), (-tw / 2 - size * 0.4, -size * 0.75, tw / 2 + size * 0.4, size * 0.7), draw, 1.0), tw


def _rgb_split(cv, spr, x, y, sc, a, off):
    """Draw a type sprite with red / cyan copies offset by `off` design px (additive), then the white on top."""
    for dx, filt in ((-off, (1, 0, 0)), (off, (0, 1, 1))):
        cv.save(); cv.translate(x + dx, y); cv.scale(sc, sc)
        p = skia.Paint(); p.setAlphaf(clamp(a / 255.0) * 0.85)
        p.setColorFilter(skia.ColorFilters.Matrix([filt[0], 0, 0, 0, 0, 0, filt[1], 0, 0, 0, 0, 0, filt[2], 0, 0, 0, 0, 0, 1, 0]))
        p.setBlendMode(skia.BlendMode.kPlus)
        img, (x0, y0, x1, y1), _, w, h = spr
        cv.drawImageRect(img, skia.Rect.MakeWH(w, h), skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.SamplingOptions(skia.FilterMode.kLinear), p, skia.Canvas.kFast_SrcRectConstraint)
        cv.restore()


def kinetic_title(cv, e, t):
    """WIPE THE GLASS (white, word-synced, elliptical ring flash at 3.92) / CLEAN. (lipstick red at 4.80, 3-frame RGB
    split, lipstick underline swipe); out with a towel-wipe smear at 5.30. Cap height 9 % H."""
    parts = e['parts']
    p1, p2 = parts[0], parts[1]
    size = 139.0
    out_t = e.get('out', {}).get('t', 99.0)
    words = p1['text'].split()
    wt = e.get('word_times') or [p1['t'], 4.24, 4.40][:len(words)]
    while len(wt) < len(words): wt.append(wt[-1] + 0.16)
    y1, y2 = 455.0, 655.0
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#05040a', 70 * clamp((t - e['t']) / 0.15)))
    # line 1, word by word
    sps = [(_type_sprite(w, size)) for w in words]
    gap = size * 0.30
    total = sum(s_[1] for s_ in sps) + gap * (len(sps) - 1)
    x = DW / 2 - total / 2
    smear_k = clamp((t - out_t) / 0.10)
    for (spr, tw), w_t in zip(sps, wt):
        u = t - w_t
        if u >= 0:
            sc = 1.0 + 0.32 * (1.0 - ease_out_back(clamp(u / 0.09), 2.0))
            cv.save(); cv.translate(x + tw / 2, y1); cv.scale(sc, sc); blit(cv, spr, 255 * clamp(u / 0.03)); cv.restore()
        x += tw + gap
    u = t - p1['t']
    if 0 <= u < 0.32:                                          # the elliptical ring flash
        k = u / 0.32
        rx, ry = (total / 2 + 120) * (0.75 + 0.45 * ease_out_cubic(k)), 150 * (0.75 + 0.45 * ease_out_cubic(k))
        r_ = skia.Rect.MakeLTRB(DW / 2 - rx, y1 - size * 0.36 - ry, DW / 2 + rx, y1 - size * 0.36 + ry)
        cv.drawOval(r_, paint('#ffffff', 170 * (1 - k), 22 * (1 - k) + 4, blur=10))
        cv.drawOval(r_, paint('#ffffff', 255 * (1 - k) ** 1.5, 5))
        if u < 2.0 / FPS: cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#ffffff', 70))
    # line 2: CLEAN. in lipstick red
    u2 = t - p2['t']
    if u2 >= 0:
        spr, tw = _type_sprite(p2['text'], size * 1.18, red=True)
        sc = 1.0 + 0.22 * (1.0 - ease_out_back(clamp(u2 / 0.08), 2.2))
        if u2 < 3.0 / FPS:
            _rgb_split(cv, spr, DW / 2, y2, sc, 255, 26 * (1 - u2 / (3.0 / FPS)) + 6)
        cv.save(); cv.translate(DW / 2, y2); cv.scale(sc, sc); blit(cv, spr, 255); cv.restore()
        if p2.get('underline'):
            uk = ease_out_cubic(clamp((u2 - 0.08) / 0.2))
            if uk > 0:
                x0 = DW / 2 - tw * 0.55; x1 = x0 + tw * 1.1 * uk
                pts = [(lerp(x0, x1, i / 16), y2 + 52 + 7 * math.sin(i * 0.7) - i * 1.2) for i in range(17)]
                wax(Pen(cv), pts, 22, 1.0, 0.4, seed=7)
    if smear_k > 0:                                            # the towel wipes across, right to left
        _towel_wipe(cv, smear_k)


def _towel_wipe(cv, k):
    xe = lerp(DW + 200, -400, ease_in_out(k))
    cv.save()
    band = poly([(xe, -50), (DW + 400, -50), (DW + 400, DH + 50), (xe - 160, DH + 50)])
    cv.drawPath(band, paint('#120d10', 200 * clamp(k * 3)))
    for j in range(9):
        yy = j * 130 + 20
        cv.drawRect(skia.Rect.MakeLTRB(xe + 60, yy, DW + 400, yy + 26), paint('#e8a0aa', 55, None, blur=8))
    towel = poly([(xe - 40, -60), (xe + 260, -60), (xe + 100, DH + 60), (xe - 200, DH + 60)])
    Pen(cv).linear(towel, xe - 200, 0, xe + 260, 0, [(0, '#c98a4e'), (0.5, '#e8b070'), (1, '#b07040')])
    cv.save(); cv.clipPath(towel, skia.ClipOp.kIntersect, True)
    for j in range(0, 14):
        yy = j * 90 - 30
        cv.drawRect(skia.Rect.MakeLTRB(xe - 260, yy, xe + 300, yy + 40), paint('#f0e6d4', 220))
    cv.restore()
    cv.drawPath(towel, paint('#2a1a10', 200, 4))
    cv.restore()


def stamp(cv, e, t, x=None, y=None):
    """Rubber stamp slam (14 YEARS, CANCELED): a double-bordered ink stamp at rot deg, size_h = box height / H;
    slams from 1.7x in 0.09 s, a squash, ink spatter; distressed ink."""
    u = t - e['t']
    if u < 0: return
    x = e.get('x', 960) if x is None else x; y = e.get('y', 540) if y is None else y
    s = e['text'].upper()
    c = e.get('color', INK_RED)
    bh = float(e.get('size_h', 0.16)) * DH
    size = bh * 0.56
    tw = text_width(s, 900, size, 0.06)
    bw = tw + bh * 0.62

    def draw(c_):
        b = rrect(-bw / 2, -bh / 2, bw, bh, bh * 0.06)
        c_.drawPath(b, paint(c, 240, bh * 0.07))
        c_.drawPath(rrect(-bw / 2 + bh * 0.12, -bh / 2 + bh * 0.12, bw - bh * 0.24, bh - bh * 0.24, bh * 0.03), paint(c, 220, bh * 0.025))
        text(c_, s, 0, size * 0.36, 900, size, c, 245, 0.06, 'center')
        for i in range(int(90 + bw * 0.12)):                    # worn ink: the paper shows through
            px, py = (hash01(i, 81) - 0.5) * bw * 1.05, (hash01(i, 82) - 0.5) * bh * 1.05
            r = (0.6 + 3.4 * hash01(i, 83) ** 3) * bh / 180
            c_.drawCircle(px, py, r, paint('#000000', 255, None, blend=skia.BlendMode.kDstOut))
        for i in range(10):
            px, py = (hash01(i, 84) - 0.5) * bw, (hash01(i, 85) - 0.5) * bh
            c_.drawLine(px, py, px + bw * 0.08 * hash01(i, 86), py + 2, paint('#000000', 255, 1.6, blend=skia.BlendMode.kDstOut))
    spr = sprite(('stamp', s, round(bh), c), (-bw / 2 - 20, -bh / 2 - 20, bw / 2 + 20, bh / 2 + 20), draw, 1.0)
    k = clamp(u / 0.09)
    sc = lerp(1.7, 1.0, ease_in_cubic(k)) if k < 1 else 1.0 - 0.035 * math.exp(-(u - 0.09) * 25) * math.cos((u - 0.09) * 50)
    a = 255 * (0.3 + 0.7 * k)
    if 0.09 <= u < 0.09 + 2.0 / FPS and e.get('hit'):
        cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#000000', 40))
    cv.save(); cv.translate(x, y); cv.rotate(float(e.get('rot', -4))); cv.scale(sc, sc)
    if k >= 1:
        for i in range(14):                                     # spatter thrown at the hit
            ang = hash01(i, 91) * 2 * math.pi; dist = bw * (0.52 + 0.25 * hash01(i, 92))
            px, py = math.cos(ang) * dist, math.sin(ang) * dist * bh / bw * 1.4
            cv.drawCircle(px, py, 2 + 6 * hash01(i, 93) ** 2, paint(c, 200 * clamp((u - 0.09) / 0.05)))
    blit(cv, spr, a)
    cv.restore()


def typebeat_rules(cv, e, t):
    """Type beat 3: `7 RULES` slams on "seven": a lipstick 7 stamped (crumbs), RULES in white, a 7-step bar lighting."""
    u = t - e['t']
    if u < 0: return
    H = float(e.get('size_h', 0.2)) * DH
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, DW, DH), paint('#06040a', 90 * clamp(u / 0.1)))
    k = clamp(u / 0.09)
    sc = lerp(1.6, 1.0, ease_in_cubic(k)) if k < 1 else 1.0
    pen = Pen(cv)
    sc7 = Script('7', 0, 0, H * 1.05, seed=7, slant=0.1, align='center', wob=0.02)
    spr_r, tw = _type_sprite('RULES', H * 0.92)
    gx = DW / 2 - (H * 0.62 + tw) / 2
    cv.save(); cv.translate(gx + H * 0.25, 560 + H * 0.5); cv.scale(sc, sc)
    write(pen, sc7, 'lipstick', 1.0, 255, tip=False, glow=0.5, w=H * 0.2)
    cv.restore()
    ur = u - 0.06
    if ur > 0:
        dx = 80 * (1 - ease_out_cubic(clamp(ur / 0.12)))
        cv.save(); cv.translate(gx + H * 0.62 + tw / 2 + dx, 560 + H * 0.36 - H * 0.05); blit(cv, spr_r, 255 * clamp(ur / 0.08)); cv.restore()
    for j in range(7):                                         # the progress bar of seven treads
        kk = clamp((u - 0.18 - j * 0.05) / 0.06)
        if kk <= 0: continue
        bx = DW / 2 - 7 * 56 / 2 + j * 56
        by = 560 + H * 0.78 - j * 8
        wax(pen, [(bx, by), (bx + 42, by - 1)], 13, kk, 0.5 * kk, seed=j)


def typebeat_seven_am(cv, e, t):
    """Type beat 5: `7:00 AM` when the loop breaks (538.7): slams with a gold-white ring burst."""
    u = t - e['t']
    if u < 0: return
    size = float(e.get('size_h', 0.22)) * DH / 0.7
    spr, tw = _type_sprite('7:00', size, '#fff6e2')
    spr2, tw2 = _type_sprite('AM', size * 0.42, '#ffd88a')
    k = ease_out_back(clamp(u / 0.10), 1.8)
    sc = lerp(1.5, 1.0, k)
    x = DW / 2 - (tw + tw2 + 30) / 2
    cv.drawCircle(DW / 2, 520, 420, paint('#ffb84a', 90 * clamp(1 - u / 0.6), None, blur=90))
    if u < 0.3:
        kk = u / 0.3
        cv.drawCircle(DW / 2, 500, 300 + 500 * ease_out_cubic(kk), paint('#fff2d0', 220 * (1 - kk), 14 * (1 - kk) + 2))
    cv.save(); cv.translate(x + tw / 2, 560); cv.scale(sc, sc); blit(cv, spr, 255 * clamp(u / 0.03)); cv.restore()
    cv.save(); cv.translate(x + tw + 30 + tw2 / 2, 560); cv.scale(sc, sc); blit(cv, spr2, 255 * clamp((u - 0.05) / 0.05)); cv.restore()


def end_card(cv, e, t):
    """Type beat 6: `DON'T MAKE A WISH.` on black, fading in over 0.4 s at 698.75; WISH in lipstick red, a slow push."""
    u = t - e['t']
    if u < 0: return
    a = 255 * ease(clamp(u / float(e.get('fade', 0.4))))
    push = 1.0 + 0.022 * u
    spr1, tw1 = _type_sprite("DON'T MAKE A", 118)
    spr2, tw2 = _type_sprite('WISH.', 236, red=True)
    cv.save(); cv.translate(DW / 2, 540); cv.scale(push, push); cv.translate(-DW / 2, -540)
    cv.save(); cv.translate(DW / 2, 430); blit(cv, spr1, a); cv.restore()
    cv.save(); cv.translate(DW / 2, 680); blit(cv, spr2, a); cv.restore()
    uk = ease_out_cubic(clamp((u - 0.55) / 0.3))
    if uk > 0:
        x0 = DW / 2 - tw2 * 0.5; x1 = x0 + tw2 * uk
        pts = [(lerp(x0, x1, i / 16), 760 + 6 * math.sin(i * 0.8) - i * 0.8) for i in range(17)]
        wax(Pen(cv), pts, 16, a / 255, 0.4, seed=3)
    cv.restore()


def typebeat(cv, e, t, sh=None):
    n = int(e.get('n', 0))
    if n == 3: typebeat_rules(cv, e, t)
    elif n == 5: typebeat_seven_am(cv, e, t)
    elif n == 6: end_card(cv, e, t)
    # n == 1 is the kinetic title, n == 2 the 14 YEARS stamp: drawn by their own entries


# ==================================================================================================== evidence marks, pops, balloons
def highlight(cv, e, t, cs=None):
    """Yellow highlighter swiped across a line of the document (box in design px on the paper plane)."""
    u = t - e['t']
    if u < 0: return
    x0, y0, x1, y1 = e['box']
    k = ease_in_out(clamp(u / float(e.get('dur', 0.35))))
    X0, Y0 = _proj(x0, y0, cs); X1, Y1 = _proj(x1, y1, cs)
    xe = lerp(X0, X1, k)
    h = Y1 - Y0
    path = smooth([(X0 - 6, Y0 + h * 0.08), (xe, Y0 - h * 0.02), (xe + 6, Y1 - h * 0.05), (X0 - 2, Y1 + h * 0.06)], True, 0.3)
    c = e.get('color', '#f4e04d')
    cv.drawPath(path, paint(c, 120, None, blend=skia.BlendMode.kMultiply))
    cv.drawPath(path, paint(c, 92))
    cv.drawPath(path, paint('#fff6a0', 60, None, blur=6))
    if 0 < k < 1:                                              # the chisel tip
        cv.save(); cv.translate(xe, Y0 + h / 2); cv.rotate(-30)
        tip = rrect(-10, -h * 0.65, 20, h * 1.3, 4)
        cv.drawPath(tip, paint('#f6e64a', 255)); cv.drawPath(rrect(-13, -h * 2.4, 26, h * 1.8, 6), paint('#3a3a40', 255))
        cv.restore()


def count_pop(cv, e, t, cs=None):
    """D2: a numeral pops beside a step (0.08 s, overshoot); red = the 7 RULES bar; erase = ticked off by the wipe."""
    u = t - e['t']
    if u < 0: return
    X, Y = _proj(e['x'], e['y'], cs)
    n = int(e['n'])
    red = e.get('color', '#ffffff').lower() not in ('#ffffff', '#fff', 'white')
    k = clamp(u / 0.08)
    sc = 1.0 + 0.5 * (1.0 - ease_out_back(k, 2.0))
    size = 64.0
    a = 255 * clamp(u / 0.03)
    if e.get('erase'):
        a *= 1.0 - clamp((u - 0.35) / 0.25)
    if a <= 0: return
    cv.save(); cv.translate(X, Y); cv.scale(sc, sc)
    if u < 0.2:
        cv.drawCircle(0, -size * 0.36, size * (0.6 + 0.9 * u / 0.2), paint('#ffffff' if not red else LIP_GLOW, 180 * (1 - u / 0.2), 3))
    if red:
        cv.drawCircle(0, -size * 0.36, size * 0.7, paint(LIP_GLOW, 90 * a / 255, None, blur=18))
        text(cv, '%d' % n, 0, 0, 900, size, '#ffe0e6', a, 0.0, 'center', 0.0, glow=(LIP_GLOW, 200, 10))
    else:
        cv.drawCircle(0, -size * 0.36, size * 0.62, paint('#000000', 100 * a / 255, None, blur=14))
        text(cv, '%d' % n, 0, 0, 900, size, '#ffffff', a, 0.0, 'center', 0.0, glow=('#000000', 160, 6))
    if e.get('erase'):
        kk = ease_out_cubic(clamp((u - 0.12) / 0.12))
        if kk > 0:
            wax(Pen(cv), [(-size * 0.5, -size * 0.2), (-size * 0.5 + size * 1.0 * kk, -size * 0.5)], 9, a / 255, 0.3, seed=n)
    cv.restore()


def circle_mark(cv, e, t, cs=None):
    """RULE 4 circled in lipstick: a hand-drawn loop around (x, y) drawn in `draw` s, then RULE 4 written beside it."""
    u = t - e['t']
    if u < 0: return
    X, Y = _proj(e['x'], e['y'], cs)
    pen = Pen(cv)
    k = clamp(u / float(e.get('draw', 0.35)))
    pts = []
    n = 40
    for i in range(int(n * 1.12 * k) + 1):
        a_ = -200 + i * 360.0 * 1.12 / n
        r = 1.0 + 0.04 * math.sin(i * 0.5)
        pts.append((X + 150 * r * math.cos(math.radians(a_)), Y + 82 * r * math.sin(math.radians(a_)) - i * 0.4))
    wax(pen, pts, 15, 1.0, 0.5, seed=4)
    uw = clamp((u - 0.06) / 0.26)                              # written while the loop closes (the shot is 0.39 s)
    if uw > 0:
        sc = Script(e.get('text', 'RULE 4'), X + 190, Y - 70, 62, seed=11, track=0.26, wob=0.02)
        write(pen, sc, 'lipstick', uw, 255, tip=True, glow=0.4)


def balloon(cv, e, t):
    """Memory speech balloon: cream paper, brown outline, a tail; pops in; `empty` = the third call nobody says; a
    shout (text ending in !) gets a jagged edge."""
    u = t - e['t']
    if u < 0: return
    x, y = e['x'], e['y']
    s = e.get('text', '').upper()
    k = ease_out_back(clamp(u / 0.16), 2.0)
    a = 255 * clamp(u / 0.06)
    size = 40.0
    tw = max(160.0, text_width(s, 800, size, 0.04)) if s else 220.0
    w, h = tw + 90, 120
    shout = s.endswith('!')
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    if shout:
        pts = []
        for i in range(28):
            an = 2 * math.pi * i / 28
            r = 1.0 + (0.22 if i % 2 else 0.0)
            pts.append((w * 0.5 * r * math.cos(an), h * 0.5 * r * math.sin(an)))
        body = poly(pts)
    else:
        body = union(oval(0, 0, w / 2, h / 2), poly([(-w * 0.18, h * 0.3), (-w * 0.02, h * 0.38), (-w * 0.3, h * 0.78)]))
    soft_shadow(cv, body, 110 * a / 255, 10, 0, 6)
    cv.drawPath(body, paint('#f4ead6', a))
    cv.drawPath(body, paint('#4a3a2c', a, 4.5))
    if s:
        text(cv, s, 0, size * 0.36, 800, size, '#3a2a1e', a, 0.04, 'center')
    else:
        for j in range(3):
            ph = 0.5 + 0.5 * math.sin(u * 8 - j * 0.9)
            cv.drawCircle(-34 + j * 34, 0, 8 + 2 * ph, paint('#6a5440', a * (0.4 + 0.6 * ph)))
    cv.restore()


# ==================================================================================================== like / subscribe, time card
def _thumb(cx, cy, s):
    return smooth([(cx - 0.42 * s, cy + 0.42 * s), (cx - 0.42 * s, cy - 0.05 * s), (cx - 0.18 * s, cy - 0.1 * s), (cx - 0.02 * s, cy - 0.5 * s),
                   (cx + 0.14 * s, cy - 0.46 * s), (cx + 0.08 * s, cy - 0.12 * s), (cx + 0.42 * s, cy - 0.12 * s), (cx + 0.44 * s, cy + 0.42 * s)], True, 0.5)


def _bell(cx, cy, s):
    body = smooth([(cx - 0.36 * s, cy + 0.3 * s), (cx - 0.28 * s, cy - 0.1 * s), (cx - 0.12 * s, cy - 0.38 * s), (cx + 0.12 * s, cy - 0.38 * s),
                   (cx + 0.28 * s, cy - 0.1 * s), (cx + 0.36 * s, cy + 0.3 * s)], True, 0.6)
    return union(body, oval(cx, cy + 0.42 * s, 0.1 * s))


def like_sub(cv, e, t):
    """LIKE / SUBSCRIBE / bell bar (cards 1-2) with an animated cursor: clicks LIKE (it turns blue), SUBSCRIBE (grey,
    SUBSCRIBED) and the bell (it rings)."""
    u = t - e['t']; hold = float(e.get('hold', 2.0))
    if u < 0 or u > hold + 0.2: return
    a = 255 * ease_out_cubic(clamp(u / 0.2)) * (1.0 - clamp((u - hold) / 0.2))
    x0, y0 = 70 - 40 * (1 - ease_out_cubic(clamp(u / 0.25))), 948
    clk = (0.35, 0.85, 1.35)
    bar = rrect(x0, y0, 560, 68, 34)
    soft_shadow(cv, bar, 150 * a / 255, 14, 0, 6)
    cv.drawPath(bar, paint('#0e0f14', 0.88 * a)); cv.drawPath(bar, paint('#ffffff', 0.18 * a, 1.5))
    liked = u > clk[0]
    lb = rrect(x0 + 10, y0 + 9, 150, 50, 25)
    cv.drawPath(lb, paint('#1f6fe0' if liked else '#2a2c34', a))
    cv.drawPath(_thumb(x0 + 46, y0 + 34, 30), paint('#ffffff', a))
    text(cv, 'LIKE', x0 + 70, y0 + 42, 800, 21, '#ffffff', a, 0.08, 'left')
    subd = u > clk[1]
    sb = rrect(x0 + 172, y0 + 9, 270, 50, 25)
    cv.drawPath(sb, paint('#3a3c44' if subd else '#d3222a', a))
    text(cv, 'SUBSCRIBED' if subd else 'SUBSCRIBE', x0 + 307, y0 + 42, 800, 21, '#ffffff', a, 0.08, 'center')
    rung = u > clk[2]
    bx, by = x0 + 500, y0 + 34
    wig = math.sin((u - clk[2]) * 40) * 14 * math.exp(-(u - clk[2]) * 5) if rung else 0.0
    cv.save(); cv.translate(bx, by - 12); cv.rotate(wig); cv.translate(-bx, -(by - 12))
    cv.drawPath(_bell(bx, by, 34), paint('#ffffff' if rung else '#a9acb8', a))
    cv.restore()
    if rung:
        for j in (-1, 1):
            cv.drawLine(bx + j * 24, by - 20, bx + j * 32, by - 26, paint('#ffffff', a * clamp(1 - (u - clk[2]) / 0.6), 3))
    pts = [(0.0, x0 + 700, y0 + 160), (clk[0] - 0.08, x0 + 90, y0 + 38), (clk[0] + 0.12, x0 + 90, y0 + 38),
           (clk[1] - 0.08, x0 + 300, y0 + 38), (clk[1] + 0.12, x0 + 300, y0 + 38), (clk[2] - 0.08, x0 + 502, y0 + 36), (99, x0 + 502, y0 + 36)]
    px, py = pts[-1][1], pts[-1][2]
    for i in range(len(pts) - 1):
        if pts[i][0] <= u < pts[i + 1][0]:
            k = ease_in_out((u - pts[i][0]) / (pts[i + 1][0] - pts[i][0]))
            px, py = lerp(pts[i][1], pts[i + 1][1], k), lerp(pts[i][2], pts[i + 1][2], k); break
    press = any(0 <= u - c_ < 0.09 for c_ in clk)
    for c_ in clk:
        if 0 <= u - c_ < 0.28:
            q = (u - c_) / 0.28
            cv.drawCircle(px, py, 12 + 46 * q, paint('#ffffff', a * (1 - q), 3))
    sc = 0.86 if press else 1.0
    cv.save(); cv.translate(px, py); cv.scale(sc, sc)
    arrow = poly([(0, 0), (0, 40), (10, 31), (18, 47), (25, 44), (17, 28), (30, 28)])
    soft_shadow(cv, arrow, 120 * a / 255, 5, 2, 3)
    cv.drawPath(arrow, paint('#ffffff', a)); cv.drawPath(arrow, paint('#16171c', a, 2.5))
    cv.restore()


def time_card(cv, e, t):
    """FRIDAY 11:57 PM · CAMP CEDAR LAKE · DEMOLITION TOMORROW (kept from v1, chip palette)."""
    u = t - e['t']; hold = e.get('hold', 2.6)
    a = 255 * ease_out_cubic(clamp(u / 0.2)) * (1.0 - clamp((u - hold) / 0.25))
    if a <= 0 or u < 0: return
    pen = Pen(cv)
    x0, y0 = e.get('x', 110) - 60 * (1 - ease_out_cubic(clamp(u / 0.25))), e.get('y', 170)
    w, h = 600, 176
    box = rrect(x0, y0, w, h, 16)
    soft_shadow(cv, box, 150 * a / 255, 24, 0, 10)
    cv.drawPath(box, paint('#121a40', 0.86 * a))
    Pen(cv).linear(box, x0, y0, x0, y0 + h, [(0, '#ffffff', 22), (1, '#000000', 30)], a / 255)
    cv.drawPath(box, paint('#4b5aa8', a, 2))
    cx, cy, r = x0 + 76, y0 + 88, 44
    cv.drawCircle(cx, cy, r, paint('#e9eef5', a, 4))
    for k in range(12):
        an = k * math.pi / 6
        cv.drawLine(cx + math.cos(an) * r * 0.8, cy + math.sin(an) * r * 0.8, cx + math.cos(an) * r * 0.92, cy + math.sin(an) * r * 0.92, paint('#e9eef5', a * 0.8, 2.5))
    fa = e.get('flip_at', e['t'] + 0.24)
    mm = 57 if t >= fa else 56
    ah = math.radians(-90 + (11 + mm / 60.0) * 30); am = math.radians(-90 + (mm + clamp((t - fa) * 3) * 0) * 6)
    asec = math.radians(-90 + (t * 6.0 % 60) * 6)
    cv.drawLine(cx, cy, cx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5, paint('#e9eef5', a, 5))
    cv.drawLine(cx, cy, cx + math.cos(am) * r * 0.74, cy + math.sin(am) * r * 0.74, paint('#e9eef5', a, 3.5))
    cv.drawLine(cx, cy, cx + math.cos(asec) * r * 0.8, cy + math.sin(asec) * r * 0.8, paint(RED, a, 2))
    text(cv, e.get('day', 'FRIDAY'), x0 + 148, y0 + 48, 700, 17, '#9fb0e6', a, 0.3, 'left')
    base = e.get('time', '11:57 PM')
    hhmm, ampm = base.split(' ') if ' ' in base else (base, '')
    pre, last = hhmm[:-1], hhmm[-1]
    prev_last = str((int(last) - 1) % 10) if last.isdigit() else last
    wx = text(cv, pre, x0 + 148, y0 + 120, 800, 66, '#ffffff', a, 0.02, 'left')
    fx_ = x0 + 148 + wx + 66 * 0.02
    fl = clamp((t - fa) / 0.14)
    if fl <= 0: text(cv, prev_last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
    elif fl < 1:
        cv.save(); cv.translate(0, y0 + 98); cv.scale(1, max(0.02, abs(math.cos(fl * math.pi)))); cv.translate(0, -(y0 + 98))
        text(cv, prev_last if fl < 0.5 else last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
        cv.restore()
    else: text(cv, last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
    lw = text_width(last, 800, 66, 0.0)
    text(cv, ampm, fx_ + lw + 14, y0 + 120, 700, 30, '#c9d6f6', a, 0.06, 'left')
    text(cv, e.get('sub', ''), x0 + 148, y0 + 152, 600, 14.5, '#9fb0e6', a * 0.9, 0.2, 'left')


# ==================================================================================================== frame-level effects (numpy)
def rgb_split_img(img, amount_px):
    """Shift red left and blue right by amount_px output pixels."""
    sh = int(round(amount_px))
    if sh == 0: return img
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], -sh, axis=1)
    out[..., 2] = np.roll(img[..., 2], sh, axis=1)
    return out


def rewind_img(img, k, frame_i):
    """Loop reset: a horizontal tear (4 frames, bands thrown sideways) then a back-scrub: tracking noise rolling up,
    a vertical squash jitter and a chroma shift (0.2 s). k = 0..1 over the effect."""
    h, w = img.shape[:2]
    rng = np.random.default_rng(frame_i * 13 + 5)
    out = img.copy()
    if k < 0.34:                                         # the tear
        for _ in range(7):
            y0 = int(rng.integers(0, h - 10)); hh = int(rng.integers(h // 40, h // 9))
            out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-w // 5, w // 5)), axis=1)
    sq = 1.0 - 0.04 * math.sin(k * math.pi)
    if sq < 0.999:
        sm = cv2.resize(out, (w, max(2, int(h * sq))), interpolation=cv2.INTER_LINEAR)
        oy = int((h - sm.shape[0]) * (0.5 + 0.5 * math.sin(k * 20)))
        out = np.roll(np.pad(sm, ((oy, h - sm.shape[0] - oy), (0, 0), (0, 0)), mode='edge'), 0, axis=0)
    out = rgb_split_img(out, w * 0.004 * (1 - k) + 2)
    band_y = int(h * (1.0 - (k * 1.6) % 1.0))
    bh = max(6, h // 18)
    y0, y1 = max(0, band_y - bh), min(h, band_y)
    if y1 > y0:
        noise = rng.integers(0, 255, (y1 - y0, w, 1), dtype=np.uint8)
        out[y0:y1] = cv2.addWeighted(out[y0:y1], 0.45, np.repeat(noise, 3, axis=2), 0.55, 0)
    return out


def pixel_sort_img(img, k, frame_i, box=None):
    """Pixel-sort glitch: in random horizontal bands, everything right of a threshold column is smeared from that
    column's colours (a sort-like stretch). k = strength 0..1; box = (x0, y0, x1, y1) in 0..1 frame fractions."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box or (0, 0, 1, 1)
    X0, Y0, X1, Y1 = int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)
    rng = np.random.default_rng(frame_i * 7 + 1)
    out = img.copy()
    nb = int(10 + 26 * k)
    for _ in range(nb):
        yy = int(rng.integers(Y0, max(Y0 + 1, Y1 - 4))); hh = int(rng.integers(3, max(4, (Y1 - Y0) // 14)))
        xs = int(rng.integers(X0, max(X0 + 1, X1 - 8)))
        ln = int((X1 - xs) * (0.3 + 0.7 * rng.random()) * k)
        if ln < 4: continue
        band = out[yy:yy + hh, xs:xs + max(2, ln // 6)]
        if band.size == 0: continue
        srt = np.sort(band.reshape(-1, 3).sum(axis=1))
        stretched = cv2.resize(band, (ln, band.shape[0]), interpolation=cv2.INTER_LINEAR)
        out[yy:yy + hh, xs:xs + ln] = stretched[:, :min(ln, w - xs)][:, :out[yy:yy + hh, xs:xs + ln].shape[1]]
    return out


# ==================================================================================================== the dispatcher
class UI:
    """Per-film HUD state: captions, the counter, the cross-cut overlays (giant numbers fly over the next cut)."""

    def __init__(self, plan, tl=None):
        self.P = plan
        self.caps = sorted(plan.get('captions', []), key=lambda c: c['t0'])
        self._cap0 = [c['t0'] for c in self.caps]
        self.cards = {rc['n']: rc for rc in plan.get('rule_cards', [])}
        giants = []
        self.overlays = []                                    # entries that outlive their shot: (t0, t1, entry)
        for s in plan.get('shots', []):
            for e in s.get('hud', []):
                if e['type'] == 'giant_number':
                    giants.append(e['t'])
                    end = e['t'] + float(e.get('hold', GIANT_HOLD)) + GIANT_FLY + 0.02 if int(e['value']) != 0 else s['t1']
                    self.overlays.append((e['t'], end, e))
        self.overlays.sort(key=lambda o: o[0])
        self.counter = Counter(plan['counter'], giants) if plan.get('counter') else None
        self.shots = plan.get('shots', [])
        self._starts = [s['t0'] for s in self.shots]
        self.tl = tl

    # ------------------------------------------------------------ captions
    def caption_at(self, t):
        j = bisect.bisect_right(self._cap0, t) - 1
        if j < 0: return None
        c = self.caps[j]
        return c if t < c['t1'] else None

    def prev_shot(self, sh):
        j = bisect.bisect_left(self._starts, sh['t0']) - 1
        return self.shots[j] if j >= 0 else None

    # ------------------------------------------------------------ main HUD
    def hud(self, cv, t, sh, cs=None, film=None):
        """Everything the shot's HUD asks for, in draw order: transition overlays, diagrams and marks, type, tags and
        X, chips, the badge, the header, the captions; the rule card and the kinetic title own the frame."""
        from ui_v2_card import rule_card
        import ui_v2_diag as D
        if sh.get('side') == 'black' and not any(e['type'] == 'typebeat' for e in sh['hud']): return
        u0 = t - sh['t0']
        card = next((e for e in sh['hud'] if e['type'] == 'rule_card'), None)
        kinetic = next((e for e in sh['hud'] if e['type'] == 'kinetic'), None)
        types = {e['type'] for e in sh['hud']}
        # --- diagrams, split overlays and the montage under the type
        if sh.get('split'): D.split_overlay(cv, sh, t)
        if sh.get('montage'): D.montage_overlay(cv, sh, t)
        for e in sh['hud']:
            ty = e['type']; u = t - e['t']
            if ty == 'diagram': D.diagram(cv, e, t, sh, cs)
            elif ty == 'sound_rings': D.sound_rings(cv, e, t, sh)
            elif ty == 'eye_line': D.eye_line(cv, e, t)
            elif ty == 'dials': D.dials(cv, e, t)
            elif ty == 'map': D.map_inset(cv, e, t)
            elif ty == 'level_guide': D.level_guide(cv, e, t, cs)
            elif ty == 'count_pop': count_pop(cv, e, t, cs)
            elif ty == 'highlight': highlight(cv, e, t, cs)
            elif ty == 'circle': circle_mark(cv, e, t, cs)
            elif ty == 'balloon': balloon(cv, e, t)
            elif ty == 'label': pin_label(cv, e, u, cs)
        for e in sh['hud']:
            ty = e['type']; u = t - e['t']
            if ty == 'stamp': stamp(cv, e, t)
            elif ty == 'typebeat' and int(e.get('n', 0)) in (3, 5, 6): typebeat(cv, e, t, sh)
            elif ty == 'red_x': red_x(cv, e.get('x', 960), e.get('y', 600), e.get('r', 160), u, e.get('hold', 0.8))
            elif ty == 'tag': cmd_tag(cv, e['text'], e.get('x', 960), e.get('y', 150), u, e.get('hold', 1.0))
            elif ty == 'time_card': time_card(cv, e, t)
            elif ty == 'phone': pass
        ph = [e for e in sh['hud'] if e['type'] == 'phone']
        if ph:
            cur = None
            for e in ph:
                if e['t'] <= t + 1e-6 or (cur is None and e['t'] - sh['t0'] < 0.35): cur = e
            if cur is not None: D.phone_ui(cv, cur, t, sh, film)
        if kinetic is not None: kinetic_title(cv, kinetic, t)
        if card is not None:
            rule_card(cv, self.cards.get(card['n'], card), card, t, film=film)
            for e in sh['hud']:
                if e['type'] == 'like_sub': like_sub(cv, e, t)
        # --- teaser border and chips
        if sh.get('teaser') or 'teaser' in types:
            teaser_border(cv, u0)
        y = CHIP_Y
        ch = sh.get('chip')
        if ch and ch.get('pop') and card is None and kinetic is None:
            chip(cv, ch['text'], ch.get('style', 'ours'), u0 - 0.05, CHIP_X, y, out=sh['t1'] - t)
            y += CHIP_H + 12 if ch.get('style') != 'memory' else CHIP_H + 18
        for e in sh['hud']:
            if e['type'] == 'chip':
                chip(cv, e['text'], e.get('style', 'ours'), t - e['t'], CHIP_X, y, out=sh['t1'] - t)
                y += CHIP_H + 12
        # --- cross-cut overlays (giant numbers) and the badge
        if self.counter is not None and card is None: self.counter.draw(cv, t, sh)
        for (a_, b_, e) in self.overlays:
            if a_ <= t < b_ and card is None and sh.get('side') != 'black': giant_number(cv, e, t)
        # --- transitions drawn on the HUD side
        if sh.get('glint') or sh.get('tr') == 'glint': glint(cv, u0)
        if sh.get('tr') == 'smear':
            ps = self.prev_shot(sh)
            carry = 0.2
            if ps is not None:
                ce = next((e for e in ps['hud'] if e['type'] == 'rule_card'), None)
                if ce: carry = float(ce.get('wipe_carry', 0.2))
            smear_carry(cv, u0, carry)
        for e in sh.get('fx_post') or []:
            if e.get('rewind'): rewind_overlay(cv, t - e['t'], e.get('dur', 0.2))
        if sh.get('tr') == 'rewind': rewind_overlay(cv, u0, 0.2)
        # --- header + captions last
        if card is None and kinetic is None and sh.get('side') != 'black': header(cv, sh, t)
        if sh.get('captions', True) and card is None:
            c = self.caption_at(t)
            if c: caption(cv, c['text'], caption_alpha(c, t))

    # ------------------------------------------------------------ picture effects after the render
    def frame_fx(self, img, t, sh, frame_i):
        u0 = t - sh['t0']
        if (sh.get('teaser') or any(e['type'] == 'teaser' for e in sh['hud'])) and u0 < 3.0 / FPS:
            img = rgb_split_img(img, img.shape[1] * 0.006 * (1 - u0 / (3.0 / FPS)) + 3)
        if sh.get('tr') == 'rewind' and u0 < 0.2:
            img = rewind_img(img, u0 / 0.2, frame_i)
        for e in sh.get('fx_post') or []:
            uu = t - e['t']; d = float(e.get('dur', 0.2))
            if 0 <= uu < d:
                if e.get('rewind'): img = rewind_img(img, uu / d, frame_i)
                if e.get('pixel_sort'): img = pixel_sort_img(img, float(e['pixel_sort']) * math.sin(math.pi * uu / d) ** 0.5, frame_i)
        for e in sh['hud']:
            if e['type'] == 'kinetic':
                for p in e['parts']:
                    if p.get('fx') == 'rgb_split_3f' and 0 <= t - p['t'] < 3.0 / FPS:
                        img = rgb_split_img(img, img.shape[1] * 0.004)
        return img


def doc_layer(sh):
    """The document of a DOC shot as a set Layer (see ui_v2_diag.doc_layer)."""
    import ui_v2_diag as D
    return D.doc_layer(sh)
