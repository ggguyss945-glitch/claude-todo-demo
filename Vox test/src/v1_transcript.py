"""V1 - edit built from the transcript alone (no reference frames viewed).

A Vox-style explainer: cream paper, ink line art, yellow highlighter, cut-out
illustrations with white borders, mono labels, a running HUD (win streak +
suspicion meter) and word-synced captions. Everything is procedural.
"""
import math
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mg  # noqa: E402
from mg import (W, H, clamp, lerp, prog, env, ease_out_cubic, ease_in_cubic, ease_in_out_cubic,
                ease_out_back, ease_out_expo, ease_in_out_quint, ease_out_quint, spring, hash01,
                noise1, hexc, paint, font, draw_text, text_width, rrect, rect, poly, trim)  # noqa: E402

WORDS = mg.load_words()
DURATION = 79.0

PAPER = "#F2ECE0"
INK = "#151515"
YEL = "#FFD21F"
RED = "#E0412E"
FELT = "#1F6A4A"
FELT_D = "#164E36"
TEAL = "#2C6E8F"
GRAY = "#8E877A"
WHITE = "#FFFFFF"
SKINS = ["#E9B996", "#C98D65", "#8E5B3C", "#F1C9A8", "#A8714C"]

HEAD = "LibreFranklin[wght].ttf"
MONO = "IBMPlexMono-Bold.ttf"
MONO_M = "IBMPlexMono-Medium.ttf"
COND = "BarlowCondensed-ExtraBold.ttf"

WHEEL_ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16,
               33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


def numcol(n):
    return "#2E9E5B" if n == 0 else (RED if n in REDS else "#1B1B1B")


def hf(size, w=800):
    return font(HEAD, size, wght=w)


# ------------------------------------------------------------ components ---
def shadowed(c, bounds, fn, dx=0, dy=10, blur=14, alpha=0.28):
    p = skia.Paint()
    p.setImageFilter(skia.ImageFilters.DropShadow(dx, dy, blur, blur, hexc("#2B1D0E", alpha)))
    c.saveLayer(bounds, p)
    fn()
    c.restore()


def cutout(c, shapes, outline=10, shadow=True, sdy=12, sblur=16, salpha=0.25):
    """Draw [(path, colour)] as a paper cut-out: white border + soft shadow."""
    def body():
        wp = paint(WHITE, stroke=outline * 2)
        wf = paint(WHITE)
        for path, _ in shapes:
            c.drawPath(path, wp)
            c.drawPath(path, wf)
        for path, col in shapes:
            if isinstance(col, skia.Paint):
                c.drawPath(path, col)
            else:
                c.drawPath(path, paint(col))
    if shadow:
        b = skia.Rect.MakeEmpty()
        for path, _ in shapes:
            b.join(path.computeTightBounds())
        b = b.makeOutset(outline + sblur * 3, outline + sblur * 3 + sdy)
        shadowed(c, b, body, dy=sdy, blur=sblur, alpha=salpha)
    else:
        body()


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def circ(cx, cy, r):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def rr(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(rect(x, y, w, h), r, r))
    return p


def shoulders(cx, top, w, h):
    p = skia.Path()
    p.moveTo(cx - w / 2, top + h)
    p.cubicTo(cx - w / 2, top + h * 0.25, cx - w * 0.33, top, cx - w * 0.12, top)
    p.lineTo(cx + w * 0.12, top)
    p.cubicTo(cx + w * 0.33, top, cx + w / 2, top + h * 0.25, cx + w / 2, top + h)
    p.close()
    return p


def person(c, cx, cy, s=1.0, kind="you", skin=0, look=0.0, blink=0.0, shirt=None, hair="#2A1D14",
           glow=0.0, shadow=True, outline=10):
    """Bust figure; (cx, cy) is the centre of the head."""
    sk = SKINS[skin % len(SKINS)]
    shapes = []
    body_top = cy + 78 * s
    shirt = shirt or {"you": "#2C6E8F", "dealer": "#FAFAF7", "pit": "#23262D", "crowd": "#7C5CA8",
                      "manager": "#2A2E37", "security": "#1E1E1E"}[kind]
    shapes.append((shoulders(cx, body_top, 300 * s, 210 * s), shirt))
    shapes.append((rr(cx - 26 * s, cy + 40 * s, 52 * s, 60 * s, 10 * s), sk))
    if kind == "dealer":
        vest = skia.Path()
        vest.moveTo(cx - 120 * s, body_top + 210 * s)
        vest.lineTo(cx - 105 * s, body_top + 40 * s)
        vest.lineTo(cx - 30 * s, body_top + 10 * s)
        vest.lineTo(cx, body_top + 120 * s)
        vest.lineTo(cx + 30 * s, body_top + 10 * s)
        vest.lineTo(cx + 105 * s, body_top + 40 * s)
        vest.lineTo(cx + 120 * s, body_top + 210 * s)
        vest.close()
        shapes.append((vest, "#1C1C1E"))
        bow = poly([(cx - 34 * s, body_top - 2 * s), (cx, body_top + 12 * s), (cx + 34 * s, body_top - 2 * s),
                    (cx + 34 * s, body_top + 30 * s), (cx, body_top + 16 * s), (cx - 34 * s, body_top + 30 * s)])
        shapes.append((bow, RED))
    elif kind in ("pit", "manager", "security"):
        lapel = poly([(cx - 40 * s, body_top + 2 * s), (cx, body_top + 150 * s), (cx + 40 * s, body_top + 2 * s)])
        shapes.append((lapel, "#F4F1EA"))
        tie_col = {"pit": "#7A1F2B", "manager": YEL, "security": "#111111"}[kind]
        tie = poly([(cx - 12 * s, body_top + 6 * s), (cx + 12 * s, body_top + 6 * s), (cx + 18 * s, body_top + 120 * s),
                    (cx, body_top + 145 * s), (cx - 18 * s, body_top + 120 * s)])
        shapes.append((tie, tie_col))
    elif kind == "you":
        hood = skia.Path()
        hood.addArc(skia.Rect.MakeXYWH(cx - 90 * s, body_top - 30 * s, 180 * s, 80 * s), 0, 180)
        shapes.append((hood, "#235A75"))
    shapes.append((oval(cx, cy, 62 * s, 72 * s), sk))
    # ears
    shapes.append((oval(cx - 62 * s, cy + 6 * s, 11 * s, 17 * s), sk))
    shapes.append((oval(cx + 62 * s, cy + 6 * s, 11 * s, 17 * s), sk))
    # hair
    hp = skia.Path()
    if kind in ("dealer", "pit", "manager", "security"):
        hp.moveTo(cx - 64 * s, cy - 6 * s)
        hp.cubicTo(cx - 70 * s, cy - 80 * s, cx + 70 * s, cy - 92 * s, cx + 64 * s, cy - 6 * s)
        hp.cubicTo(cx + 50 * s, cy - 40 * s, cx - 10 * s, cy - 60 * s, cx - 64 * s, cy - 6 * s)
    else:
        hp.moveTo(cx - 66 * s, cy + 4 * s)
        hp.cubicTo(cx - 80 * s, cy - 96 * s, cx + 80 * s, cy - 104 * s, cx + 66 * s, cy + 4 * s)
        hp.cubicTo(cx + 40 * s, cy - 30 * s, cx - 20 * s, cy - 40 * s, cx - 66 * s, cy + 4 * s)
    hp.close()
    shapes.append((hp, hair))
    cutout(c, shapes, outline=outline * s, shadow=shadow, sdy=14 * s, sblur=18 * s)
    # face details (no outline)
    ex = look * 9 * s
    eh = max(0.12, 1 - blink)
    for side in (-1, 1):
        c.drawOval(skia.Rect.MakeLTRB(cx + side * 22 * s - 6 * s + ex, cy - 4 * s - 7 * s * eh,
                                      cx + side * 22 * s + 6 * s + ex, cy - 4 * s + 7 * s * eh), paint(INK))
    c.drawArc(skia.Rect.MakeXYWH(cx - 16 * s + ex * 0.5, cy + 22 * s, 32 * s, 16 * s), 20, 140, False,
              paint(INK, stroke=4 * s))
    if kind == "you":
        magic_glasses(c, cx + ex * 0.4, cy - 4 * s, 0.62 * s, 1.0, glow)


def glasses_path(cx, cy, s):
    p = skia.Path()
    for side in (-1, 1):
        x0 = cx + side * 70 * s
        p.addRRect(skia.RRect.MakeRectXY(rect(x0 - 58 * s, cy - 38 * s, 116 * s, 80 * s), 26 * s, 26 * s))
    p.moveTo(cx - 12 * s, cy - 10 * s)
    p.quadTo(cx, cy - 22 * s, cx + 12 * s, cy - 10 * s)
    p.moveTo(cx - 128 * s, cy - 20 * s)
    p.lineTo(cx - 150 * s, cy - 26 * s)
    p.moveTo(cx + 128 * s, cy - 20 * s)
    p.lineTo(cx + 150 * s, cy - 26 * s)
    return p


def magic_glasses(c, cx, cy, s, draw=1.0, glow=0.0, lens_fn=None):
    if glow > 0:
        c.drawCircle(cx - 70 * s, cy, 90 * s, paint(YEL, a=0.45 * glow, blur=40 * s))
        c.drawCircle(cx + 70 * s, cy, 90 * s, paint(YEL, a=0.45 * glow, blur=40 * s))
    for side in (-1, 1):
        x0 = cx + side * 70 * s
        lens = skia.RRect.MakeRectXY(rect(x0 - 58 * s, cy - 38 * s, 116 * s, 80 * s), 26 * s, 26 * s)
        c.drawRRect(lens, paint(mg.mix("#DDE7EA", YEL, glow), a=0.85 * draw))
        if lens_fn:
            c.save()
            c.clipRRect(lens, True)
            lens_fn(x0, cy, s, side)
            c.restore()
        # glint
        c.drawLine(x0 - 30 * s, cy - 18 * s, x0 - 12 * s, cy - 28 * s, paint(WHITE, a=0.9 * draw, stroke=6 * s))
    c.drawPath(trim(glasses_path(cx, cy, s), 0, draw), paint(INK, stroke=13 * s))


def chip(c, x, y, r, col="#D23A2B", label=None, a=1.0):
    c.drawCircle(x, y + r * 0.12, r, paint("#000000", a=0.25 * a, blur=r * 0.15))
    c.drawCircle(x, y, r, paint(col, a=a))
    for i in range(8):
        ang = i * math.pi / 4
        c.save()
        c.translate(x, y)
        c.rotate(math.degrees(ang))
        c.drawRect(rect(-r * 0.13, -r, r * 0.26, r * 0.28), paint(WHITE, a=a))
        c.restore()
    c.drawCircle(x, y, r * 0.66, paint(WHITE, a=0.95 * a, stroke=r * 0.06))
    c.drawCircle(x, y, r * 0.6, paint(col, a=a))
    if label:
        draw_text(c, label, x, y + r * 0.2, font(COND, r * 0.62), paint(WHITE, a=a), "center")


def wheel(c, cx, cy, r, rot=0.0, ball=None, glow_pocket=None, glow=0.0):
    """Top-down European roulette wheel. rot in radians, ball=(angle, radius frac)."""
    c.drawCircle(cx, cy + r * 0.05, r * 1.02, paint("#000000", a=0.3, blur=r * 0.06))
    p = paint()
    p.setShader(mg.radial(cx, cy, r, ["#9A6237", "#6E4021", "#4A2914"], [0.7, 0.9, 1.0]))
    c.drawCircle(cx, cy, r, p)
    c.drawCircle(cx, cy, r * 0.93, paint("#D9CDB4"))
    c.drawCircle(cx, cy, r * 0.93, paint("#8C7B5E", stroke=r * 0.012))
    n = 37
    da = 2 * math.pi / n
    r_out, r_num, r_in = r * 0.84, r * 0.72, r * 0.58
    for i, num in enumerate(WHEEL_ORDER):
        a0 = rot + i * da - da / 2 - math.pi / 2
        path = skia.Path()
        path.arcTo(skia.Rect.MakeLTRB(cx - r_out, cy - r_out, cx + r_out, cy + r_out), math.degrees(a0),
                   math.degrees(da), True)
        path.arcTo(skia.Rect.MakeLTRB(cx - r_in, cy - r_in, cx + r_in, cy + r_in), math.degrees(a0 + da),
                   -math.degrees(da), False)
        path.close()
        col = numcol(num)
        c.drawPath(path, paint(col))
        if glow_pocket is not None and num == glow_pocket and glow > 0:
            c.drawPath(path, paint(YEL, a=glow))
    # pocket separators + inner pocket ring
    for i in range(n):
        a0 = rot + i * da - da / 2 - math.pi / 2
        c.drawLine(cx + r_in * math.cos(a0), cy + r_in * math.sin(a0), cx + r_out * math.cos(a0),
                   cy + r_out * math.sin(a0), paint("#E8D9A8", stroke=r * 0.008))
    c.drawCircle(cx, cy, r_num * 0.985, paint("#E8D9A8", stroke=r * 0.006))
    f = font(COND, r * 0.075)
    for i, num in enumerate(WHEEL_ORDER):
        a = rot + i * da
        c.save()
        c.translate(cx, cy)
        c.rotate(math.degrees(a))
        draw_text(c, str(num), 0, -r_num - r * 0.035, f, paint(WHITE), "center")
        c.restore()
    p = paint()
    p.setShader(mg.radial(cx - r * 0.1, cy - r * 0.1, r_in, ["#B57A45", "#7A4B26", "#4F2E15"], [0, 0.7, 1]))
    c.drawCircle(cx, cy, r_in, p)
    for k in range(4):
        a = rot + k * math.pi / 2 + math.pi / 4
        c.drawLine(cx + r * 0.12 * math.cos(a), cy + r * 0.12 * math.sin(a), cx + r * 0.45 * math.cos(a),
                   cy + r * 0.45 * math.sin(a), paint("#E3C27A", stroke=r * 0.025))
        c.drawCircle(cx + r * 0.45 * math.cos(a), cy + r * 0.45 * math.sin(a), r * 0.03, paint("#F0D898"))
    p = paint()
    p.setShader(mg.radial(cx - r * 0.04, cy - r * 0.04, r * 0.14, ["#FFF6D8", "#D4AE5A", "#8A6420"]))
    c.drawCircle(cx, cy, r * 0.12, p)
    if ball:
        ba, bf = ball
        bx, by = cx + r * bf * math.cos(ba - math.pi / 2), cy + r * bf * math.sin(ba - math.pi / 2)
        c.drawCircle(bx + r * 0.008, by + r * 0.012, r * 0.034, paint("#000000", a=0.35, blur=r * 0.01))
        p = paint()
        p.setShader(mg.radial(bx - r * 0.01, by - r * 0.012, r * 0.04, ["#FFFFFF", "#E9E6DF", "#A8A39A"]))
        c.drawCircle(bx, by, r * 0.032, p)


def table_layout(c, x, y, w, h, hl=None, hl_a=0.0, felt=FELT, cols=3):
    """Vertical roulette betting grid. Returns function cell_center(n)."""
    rrect(c, x - 18, y - 18, w + 36, h + 36, 34, paint("#5B3A1F"))
    rrect(c, x - 18, y - 18, w + 36, h + 36, 34, paint("#3E2614", stroke=4))
    rrect(c, x, y, w, h, 22, paint(felt))
    zero_h = h * 0.1
    cw, ch = w / cols, (h - zero_h) / 12
    line = paint("#EDE6D0", a=0.85, stroke=3)
    # zero
    zp = poly([(x + w * 0.5, y + 6), (x + w - 6, y + zero_h * 0.55), (x + w - 6, y + zero_h),
               (x + 6, y + zero_h), (x + 6, y + zero_h * 0.55)])
    c.drawPath(zp, line)
    fnum = font(COND, ch * 0.5)
    draw_text(c, "0", x + w / 2, y + zero_h * 0.78, fnum, paint("#9BE3B5"), "center")
    centers = {0: (x + w / 2, y + zero_h * 0.62)}
    for row in range(12):
        for col in range(3):
            n = row * 3 + col + 1
            cx0, cy0 = x + col * cw, y + zero_h + row * ch
            c.drawRect(rect(cx0, cy0, cw, ch), line)
            ccx, ccy = cx0 + cw / 2, cy0 + ch / 2
            centers[n] = (ccx, ccy)
            if hl is not None and n == hl and hl_a > 0:
                c.drawRect(rect(cx0 + 3, cy0 + 3, cw - 6, ch - 6), paint(YEL, a=hl_a))
            rrect(c, ccx - ch * 0.36, ccy - ch * 0.3, ch * 0.72, ch * 0.6, ch * 0.3, paint(numcol(n)))
            draw_text(c, str(n), ccx, ccy + ch * 0.18, fnum, paint(WHITE), "center")
    return centers


def stamp(c, text, cx, cy, size, t, color=RED, angle=-8):
    """Rubber stamp that slams in at local time t=0."""
    if t <= 0:
        return
    k = ease_out_cubic(prog(t, 0, 0.18))
    sc = lerp(2.2, 1.0, k)
    a = clamp(t / 0.08)
    f = font(COND, size)
    tw = text_width(text, f, size * 0.04)
    c.save()
    c.translate(cx, cy)
    c.rotate(angle)
    c.scale(sc, sc)
    pad = size * 0.28
    rrect(c, -tw / 2 - pad, -size * 0.62 - pad * 0.5, tw + pad * 2, size * 0.86 + pad, size * 0.12,
          paint(color, a=a, stroke=size * 0.08))
    draw_text(c, text, 0, size * 0.27, f, paint(color, a=a), "center", size * 0.04)
    # ink speckle knockouts
    for i in range(26):
        hx = (hash01(i, 3) - 0.5) * (tw + pad * 2)
        hy = (hash01(i, 5) - 0.5) * size
        c.drawCircle(hx, hy, size * 0.02 * (0.5 + hash01(i, 9)), paint(PAPER, a=0.7 * a))
    c.restore()


def label(c, text, x, y, size=26, col=INK, align="left", a=1.0, bg=None, track=2.0, f=None):
    f = f or font(MONO, size)
    w_ = text_width(text, f, track)
    if bg:
        bx = x - (w_ / 2 if align == "center" else w_ if align == "right" else 0)
        rrect(c, bx - 12, y - size * 0.95, w_ + 24, size * 1.35, 4, paint(bg, a=a))
    draw_text(c, text, x, y, f, paint(col, a=a), align, track)
    return w_


def highlight_text(c, text, x, y, size, k, align="center", hl=YEL, col=INK, w=850, skew=-1.5):
    """Headline with a marker highlight that wipes in with progress k."""
    f = hf(size, w)
    tw = text_width(text, f)
    x0 = x - tw / 2 if align == "center" else x
    if k > 0:
        c.save()
        c.skew(math.radians(skew) * 0, 0)
        rrect(c, x0 - size * 0.18, y - size * 0.8, (tw + size * 0.36) * ease_out_cubic(k), size * 1.0,
              size * 0.08, paint(hl))
        c.restore()
    draw_text(c, text, x0, y, f, paint(col), "left")


def pop(t, t0, dur=0.45):
    return ease_out_back(prog(t, t0, t0 + dur), 1.9)


def fade(t, t0, dur=0.25):
    return ease_out_cubic(prog(t, t0, t0 + dur))


def card(c, x, y, w, h, col="#FBF8F1", r=18, a=1.0):
    def body():
        rrect(c, x, y, w, h, r, paint(col, a=a))
    shadowed(c, rect(x - 60, y - 60, w + 120, h + 140), body, dy=14, blur=18, alpha=0.22 * a)


def dome_cam(c, cx, cy, r, look=(0.0, 0.0), rec=0.0, eye=0.0, t=0.0):
    """Ceiling dome camera seen from below/side. cy = ceiling line."""
    rrect(c, cx - r * 1.25, cy - r * 0.18, r * 2.5, r * 0.22, r * 0.06, paint("#C9C2B4"))
    p = paint()
    p.setShader(mg.linear(cx, cy, cx, cy + r, ["#3B3F47", "#0E1013"]))
    path = skia.Path()
    path.arcTo(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), 0, 180, True)
    path.close()
    c.drawPath(path, p)
    # inner eye
    lx, ly = look
    ex, ey = cx + lx * r * 0.35, cy + r * 0.45 + ly * r * 0.15
    if eye > 0:
        c.drawCircle(ex, ey, r * 0.3 * eye, paint("#F4F0E6", a=eye))
        c.drawCircle(ex + lx * r * 0.08, ey + ly * r * 0.05, r * 0.17 * eye, paint(TEAL, a=eye))
        c.drawCircle(ex + lx * r * 0.08, ey + ly * r * 0.05, r * 0.09 * eye, paint("#050505", a=eye))
        c.drawCircle(ex + lx * r * 0.08 - r * 0.05, ey - r * 0.06, r * 0.035 * eye, paint(WHITE, a=eye))
    else:
        c.drawCircle(ex, ey, r * 0.16, paint("#000000"))
        c.drawCircle(ex, ey, r * 0.1, paint("#1E3B52"))
    c.drawArc(skia.Rect.MakeLTRB(cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), 200 - 180, 50, False,
              paint(WHITE, a=0.35, stroke=r * 0.06))
    if rec > 0:
        on = (math.sin(t * 9) > -0.2)
        c.drawCircle(cx + r * 0.75, cy + r * 0.2, r * 0.06, paint(RED, a=rec * (1 if on else 0.25)))


def monitor(c, x, y, w, h, t, cam="CAM 07"):
    rrect(c, x - 16, y - 16, w + 32, h + 32, 22, paint("#2A2C30"))
    rrect(c, x, y, w, h, 8, paint("#0F1A17"))
    return rect(x, y, w, h)


def monitor_overlay(c, x, y, w, h, t, cam="CAM 07"):
    for i in range(0, int(h), 6):
        c.drawRect(rect(x, y + i, w, 2), paint("#000000", a=0.18))
    f = font(MONO, 26)
    draw_text(c, cam, x + 24, y + 46, f, paint("#E9F5EE", a=0.9))
    on = math.sin(t * 7) > 0
    c.drawCircle(x + w - 120, y + 36, 9, paint(RED, a=1 if on else 0.3))
    draw_text(c, "REC", x + w - 100, y + 46, f, paint("#E9F5EE", a=0.9))
    secs = 22 * 3600 + 47 * 60 + 13 + t
    ts = "%02d:%02d:%02d" % ((secs // 3600) % 24, (secs // 60) % 60, secs % 60)
    draw_text(c, ts, x + w - 24, y + h - 24, f, paint("#E9F5EE", a=0.9), "right")
    p = paint()
    p.setShader(mg.radial(x + w / 2, y + h / 2, max(w, h) * 0.7, [hexc("#000000", 0), hexc("#000000", 0.55)],
                          [0.5, 1.0]))
    c.drawRect(rect(x, y, w, h), p)


def corners(c, x, y, w, h, L, col, sw=6, a=1.0):
    pp = paint(col, a=a, stroke=sw, cap="square")
    for (px, py, dx, dy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        c.drawLine(px, py, px + dx * L, py, pp)
        c.drawLine(px, py, px, py + dy * L, pp)


# ------------------------------------------------------------------ HUD ---
WINS = [7.76, 8.0, 8.4, 11.92, 12.2, 12.5, 13.2, 20.09, 20.73, 21.12, 33.92, 45.59, 48.08, 55.99, 64.34,
        64.91, 65.06]
LEVELS = [(13.2, "TABLE"), (22.57, "SURVEILLANCE"), (35.45, "SECURITY"), (57.06, "MANAGEMENT"),
          (69.39, "BANNED")]


def hud(c, t):
    a = fade(t, 4.7, 0.5)
    if a <= 0:
        return
    y = lerp(-80, 0, ease_out_cubic(prog(t, 4.7, 5.3)))
    c.save()
    c.translate(0, y)
    # streak counter
    n = sum(1 for w_ in WINS if t >= w_)
    last = max([w_ for w_ in WINS if t >= w_], default=-10)
    k = 1 - prog(t, last, last + 0.35)
    label(c, "WIN STREAK", 70, 118, 22, GRAY, a=a)
    sc = 1 + 0.25 * ease_in_cubic(k)
    c.save()
    c.translate(70, 205)
    c.scale(sc, sc)
    draw_text(c, "%02d" % n, 0, 0, font(COND, 104), paint(INK, a=a))
    c.restore()
    if k > 0 and n > 0:
        draw_text(c, "+35x", 200, 196 - 30 * (1 - k), font(COND, 44), paint(RED, a=a * k))
    # suspicion meter
    lvl = sum(1 for lt, _ in LEVELS if t >= lt)
    mx, my, mw, mh = 470, 140, 540, 34
    label(c, "SUSPICION", mx, 118, 22, GRAY, a=a)
    name = LEVELS[lvl - 1][1] if lvl else "NONE"
    lt_last = LEVELS[lvl - 1][0] if lvl else 0
    kk = prog(t, lt_last, lt_last + 0.4)
    label(c, name, mx + mw, 118, 22, RED if lvl >= 3 else INK, align="right", a=a)
    segw = (mw - 4 * 8) / 5
    for i in range(5):
        sx = mx + i * (segw + 8)
        rrect(c, sx, my, segw, mh, 6, paint("#D9D1C1", a=a))
        if i < lvl:
            fk = ease_out_cubic(kk) if i == lvl - 1 else 1.0
            col = mg.mix(YEL, RED, i / 4)
            rrect(c, sx, my, segw * fk, mh, 6, paint(col, a=a))
            if i == lvl - 1 and kk < 1:
                rrect(c, sx - 4, my - 4, segw + 8, mh + 8, 9, paint(col, a=a * (1 - kk), stroke=4))
    c.drawLine(70, 250, W - 70, 250, paint(INK, a=0.25 * a, stroke=2))
    c.restore()


# ------------------------------------------------------------- captions ---
def build_caption_groups():
    groups, cur = [], []
    for w_ in WORDS:
        cur.append(w_)
        txt = " ".join(x["w"] for x in cur)
        end_punct = w_["w"][-1] in ".,?!"
        if end_punct or len(txt) > 18 or len(cur) >= 4:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        s = g[0]["s"]
        e = groups[i + 1][0]["s"] if i + 1 < len(groups) else g[-1]["e"] + 0.6
        e = min(e, g[-1]["e"] + 0.7)
        out.append((s, e, g))
    return out


CAPS = build_caption_groups()


def captions(c, t):
    f = hf(64, 800)
    for s, e, g in CAPS:
        if not (s <= t < e):
            continue
        a = fade(t, s, 0.08) * (1 - prog(t, e - 0.06, e))
        words = [x["w"] for x in g]
        ws = [text_width(x, f) for x in words]
        space = 18
        total = sum(ws) + space * (len(ws) - 1)
        x = W / 2 - total / 2
        y = 1700 + 18 * (1 - ease_out_cubic(prog(t, s, s + 0.15)))
        for (wd, ww, wi) in zip(words, ws, g):
            active = wi["s"] <= t < max(wi["e"], wi["s"] + 0.12)
            if active:
                k = ease_out_cubic(prog(t, wi["s"], wi["s"] + 0.1))
                rrect(c, x - 10, y - 56, (ww + 20) * k, 74, 8, paint(YEL, a=a))
            draw_text(c, wd, x, y, f, paint(INK, a=a))
            x += ww + space


# --------------------------------------------------------------- scenes ---
def s_glasses(c, t, T):
    cx, cy = W / 2, 760
    draw = ease_in_out_cubic(prog(T, 0.15, 1.6))
    glow = ease_out_cubic(prog(T, 0.88, 1.5))
    s = 2.2 + 0.08 * prog(T, 0, 4.6)

    def lens(x0, y0, sc, side):
        k = prog(T, 3.1, 3.7)
        if k <= 0:
            return
        # spinning mini wheels inside each lens
        wheel(c, x0, y0, 70 * sc * ease_out_back(k), rot=T * (2.5 if side < 0 else -2.0))
    if glow > 0:
        for i in range(14):
            ang = i / 14 * 2 * math.pi + T * 0.4
            rr_ = lerp(260, 330, hash01(i, 2)) * ease_out_cubic(glow)
            sx, sy = cx + rr_ * math.cos(ang), cy + rr_ * math.sin(ang) * 0.7
            tw = 0.5 + 0.5 * math.sin(T * 6 + i)
            c.drawPath(mg.star(sx, sy, 16 * tw * glow, 5 * tw * glow, 4), paint(YEL, a=glow))
    c.save()
    c.translate(cx, cy)
    c.rotate(-4 + 4 * ease_out_cubic(prog(T, 0, 1.6)))
    c.translate(-cx, -cy)
    magic_glasses(c, cx, cy, s, draw, glow, lens)
    c.restore()
    # title
    k = fade(T, 0.0, 0.35)
    draw_text(c, "IMAGINE...", W / 2, 470, font(COND, 120), paint(INK, a=k), "center", 6)
    k2 = prog(T, 3.6, 4.0)
    if k2 > 0:
        label(c, "NEXT SPIN", W / 2, 1060, 30, GRAY, "center", a=k2)
        num = 17 if T > 3.9 else int(hash01(int(T * 30)) * 37)
        rrect(c, W / 2 - 130, 1095, 260, 140, 18, paint(numcol(num), a=k2))
        draw_text(c, str(num), W / 2, 1205, font(COND, 120), paint(WHITE, a=k2), "center")
    highlight_text(c, "magic glasses", W / 2, 1360, 72, prog(T, 0.88, 1.6))


def s_banned(c, t, T):
    # stopwatch
    cx, cy, r = W / 2, 760, 230
    k = pop(T, 4.6)
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    c.drawCircle(0, 12, r, paint("#000000", a=0.18, blur=20))
    c.drawCircle(0, 0, r, paint(WHITE))
    c.drawCircle(0, 0, r, paint(INK, stroke=16))
    rrect(c, -36, -r - 70, 72, 50, 8, paint(INK))
    rrect(c, -16, -r - 30, 32, 30, 4, paint(INK))
    for i in range(60):
        a = i / 60 * 2 * math.pi
        L = 30 if i % 5 == 0 else 14
        c.drawLine((r - 30) * math.sin(a), -(r - 30) * math.cos(a), (r - 30 - L) * math.sin(a),
                   -(r - 30 - L) * math.cos(a), paint(INK, stroke=6 if i % 5 == 0 else 3))
    sweep = ease_in_out_cubic(prog(T, 5.1, 6.7)) * 330
    path = skia.Path()
    path.moveTo(0, 0)
    path.arcTo(skia.Rect.MakeLTRB(-r + 40, -r + 40, r - 40, r - 40), -90, sweep, False)
    path.close()
    c.drawPath(path, paint(YEL, a=0.8))
    a = math.radians(sweep - 90)
    c.drawLine(0, 0, (r - 60) * math.cos(a), (r - 60) * math.sin(a), paint(RED, stroke=12))
    c.drawCircle(0, 0, 18, paint(INK))
    c.restore()
    draw_text(c, "HOW FAST", W / 2, 420, font(COND, 130), paint(INK, a=fade(T, 4.8)), "center", 6)
    label(c, "UNTIL YOU GET", W / 2, 1090, 34, GRAY, "center", a=fade(T, 6.3))
    stamp(c, "BANNED", W / 2, 1300, 170, T - 6.8)


def s_firstbets(c, t, T):
    x, y, w, h = 300, 330, 480, 1150
    k = ease_out_cubic(prog(T, 7.45, 7.9))
    c.save()
    c.translate(0, 120 * (1 - k))
    hlnum = None
    hits = [(7.76, 17), (8.0, 8), (8.4, 29)]
    for tt, n in hits:
        if T >= tt:
            hlnum = n
            hlt = tt
    hla = (1 - prog(T, hlt, hlt + 0.6)) if hlnum else 0
    cent = table_layout(c, x, y, w, h, hlnum, hla)
    for i, (tt, n) in enumerate(hits):
        if T >= tt - 0.25:
            dk = ease_out_back(prog(T, tt - 0.25, tt), 1.4)
            cx_, cy_ = cent[n]
            chip(c, cx_ + 900 * (1 - dk), cy_ - 300 * (1 - dk), 34, ["#D23A2B", "#2C6E8F", "#3C8D4F"][i])
            if T >= tt:
                wk = prog(T, tt, tt + 0.7)
                if wk < 1:
                    draw_text(c, "WIN", cx_ + 70, cy_ - 30 - 60 * wk, font(COND, 60), paint(RED, a=1 - wk))
    c.restore()
    # "nobody notices" side note
    nk = fade(T, 8.88, 0.3)
    if nk > 0:
        c.save()
        c.translate(150, 940)
        c.rotate(-6)
        card(c, -130, -110, 260, 220, a=nk)
        # closed eye
        c.drawArc(skia.Rect.MakeLTRB(-70, -50, 70, 30), 10, 160, False, paint(INK, a=nk, stroke=8))
        for i in range(5):
            a = math.radians(30 + i * 30)
            c.drawLine(70 * math.cos(a) * 0.95, -10 + 40 * math.sin(a), 90 * math.cos(a), -10 + 62 * math.sin(a),
                       paint(INK, a=nk, stroke=6))
        draw_text(c, "NOBODY", 0, 80, font(MONO, 26), paint(INK, a=nk), "center", 2)
        c.restore()


def s_odds(c, t, T):
    k = fade(T, 9.9, 0.3)
    label(c, "ODDS OF HITTING ONE NUMBER", W / 2, 470, 30, GRAY, "center", a=k)
    pk = pop(T, 10.0, 0.5)
    c.save()
    c.translate(W / 2, 800)
    c.scale(pk, pk)
    hk = prog(T, 10.4, 10.9)
    f = font(COND, 320)
    tw = text_width("1 in 37", f)
    rrect(c, -tw / 2 - 30, -250, (tw + 60) * ease_out_cubic(hk), 290, 16, paint(YEL))
    draw_text(c, "1 in 37", 0, 0, f, paint(INK), "center")
    c.restore()
    # 37 dots grid, one lit
    dk = prog(T, 10.2, 11.2)
    for i in range(37):
        gx, gy = 165 + (i % 10) * 83, 1010 + (i // 10) * 83
        ak = clamp(dk * 37 - i)
        if ak <= 0:
            continue
        col = YEL if i == 16 else "#CFC6B4"
        c.drawCircle(gx, gy, 28 * ease_out_back(ak), paint(col))
        if i == 16:
            c.drawCircle(gx, gy, 28 * ease_out_back(ak), paint(INK, stroke=5))
    label(c, "EVERYONE GETS LUCKY SOMETIMES", W / 2, 1440, 28, INK, "center", a=fade(T, 10.88))


def s_crushing(c, t, T):
    label(c, "YOUR LAST BETS", 120, 420, 30, GRAY, a=fade(T, 11.35))
    wins_here = [7.76, 8.0, 8.4, 11.92, 12.2, 12.5, 13.2]
    for i, wt in enumerate(wins_here):
        bx, by = 120 + (i % 4) * 215, 470 + (i // 4) * 230
        appear = wt if wt > 11 else 11.35 + i * 0.08
        k = pop(T, appear, 0.4)
        if k <= 0:
            continue
        c.save()
        c.translate(bx + 90, by + 90)
        c.scale(k, k)
        rrect(c, -90, -90, 180, 180, 22, paint(INK))
        draw_text(c, "W", 0, 42, font(COND, 130), paint(YEL), "center")
        c.restore()
    # suspicion rising at the table: table with question marks
    sk = fade(T, 12.72, 0.3)
    if sk > 0:
        c.save()
        c.translate(W / 2, 1210)
        c.drawOval(skia.Rect.MakeLTRB(-420, -120, 420, 140), paint(FELT_D, a=sk))
        c.drawOval(skia.Rect.MakeLTRB(-400, -110, 400, 120), paint(FELT, a=sk))
        for i in range(3):
            qk = pop(T, 13.0 + i * 0.25, 0.4)
            if qk > 0:
                qx = -260 + i * 260
                c.save()
                c.translate(qx, -40 - 20 * math.sin(T * 3 + i))
                c.scale(qk, qk)
                c.drawCircle(0, -30, 62, paint(YEL))
                draw_text(c, "?", 0, 10, font(COND, 110), paint(INK), "center")
                c.restore()
        c.restore()
    highlight_text(c, "suspicion starts", W / 2, 1470, 62, prog(T, 12.72, 13.4))


def s_staff(c, t, T):
    look = ease_in_out_cubic(prog(T, 15.9, 16.3))
    k1 = ease_out_back(prog(T, 14.3, 14.85), 1.3)
    k2 = ease_out_back(prog(T, 15.0, 15.55), 1.3)
    blink = 1.0 if (abs(T - 17.0) < 0.06 or abs(T - 18.3) < 0.06) else 0.0
    person(c, 270 - 500 * (1 - k1), 640, 1.15, "dealer", skin=1, look=look, blink=blink, hair="#1A120C")
    person(c, 810 + 500 * (1 - k2), 640, 1.15, "pit", skin=0, look=-look, blink=blink, hair="#8A8A86")
    label(c, "DEALER", 270, 1010, 30, INK, "center", a=k1 * 1.0, bg=YEL)
    label(c, "PIT MANAGER", 810, 1010, 30, INK, "center", a=clamp(k2), bg=YEL)
    # pattern chart
    pk = prog(T, 16.48, 17.6)
    if pk > 0:
        x0, y0, w, h = 140, 1110, 800, 320
        card(c, x0 - 30, y0 - 30, w + 60, h + 60, a=clamp(pk * 4))
        label(c, "WIN RATE  vs  EXPECTED", x0, y0 + 20, 22, GRAY, a=clamp(pk * 4))
        base = y0 + h - 30
        c.drawLine(x0, base, x0 + w, base, paint(INK, a=0.4, stroke=2))
        exp_y = base - 40
        c.drawLine(x0, exp_y, x0 + w, exp_y, paint(GRAY, stroke=3, effect=skia.DashPathEffect.Make([12, 10], 0)))
        path = skia.Path()
        path.moveTo(x0, exp_y)
        for i in range(1, 41):
            xx = x0 + w * i / 40
            yy = exp_y - (h - 110) * (i / 40) ** 1.3 + 8 * math.sin(i * 1.7)
            path.lineTo(xx, yy)
        c.drawPath(trim(path, 0, ease_in_out_cubic(pk)), paint(RED, stroke=8))
    # watching eyes
    ek = fade(T, 18.48, 0.3)
    if ek > 0:
        for ex in (270, 810):
            c.save()
            c.translate(ex, 400 - 10 * math.sin(T * 2.5))
            c.scale(ek, ek)
            eye_icon(c, 0, 0, 70, look=0.6 if ex == 270 else -0.6)
            c.restore()


def eye_icon(c, x, y, r, look=0.0, col=INK, a=1.0):
    p = skia.Path()
    p.moveTo(x - r, y)
    p.quadTo(x, y - r * 0.95, x + r, y)
    p.quadTo(x, y + r * 0.95, x - r, y)
    p.close()
    c.drawPath(p, paint(WHITE, a=a))
    c.drawPath(p, paint(col, a=a, stroke=r * 0.12))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    c.drawCircle(x + look * r * 0.3, y, r * 0.38, paint(col, a=a))
    c.drawCircle(x + look * r * 0.3 - r * 0.12, y - r * 0.12, r * 0.1, paint(WHITE, a=a))
    c.restore()


def s_surveillance(c, t, T):
    # ceiling strip
    ck = ease_out_cubic(prog(T, 19.45, 19.9))
    c.save()
    c.translate(0, -200 * (1 - ck))
    c.drawRect(rect(0, 270, W, 70), paint("#D8D0C0"))
    for i in range(7):
        c.drawLine(i * 180, 270, i * 180, 340, paint("#BDB4A2", stroke=3))
    c.restore()
    # streak continues: W tiles slide across
    for i, wt in enumerate([20.09, 20.73, 21.12]):
        k = pop(T, wt, 0.35)
        if k > 0 and T < 22.0:
            fa = 1 - prog(T, 21.6, 22.0)
            c.save()
            c.translate(250 + i * 290, 1150)
            c.scale(k, k)
            rrect(c, -90, -90, 180, 180, 22, paint(INK, a=fa))
            draw_text(c, "W", 0, 42, font(COND, 130), paint(YEL, a=fa), "center")
            c.restore()
    # ping notification
    pk = ease_out_back(prog(T, 21.77, 22.25), 1.2)
    if pk > 0 and T < 23.4:
        fa = 1 - prog(T, 23.0, 23.4)
        c.save()
        c.translate(W / 2, 900 - 60 * (1 - pk))
        card(c, -400, -90, 800, 180, a=fa)
        c.drawCircle(-310, 0, 46, paint(RED, a=fa))
        draw_text(c, "!", -310, 26, font(COND, 80), paint(WHITE, a=fa), "center")
        draw_text(c, "SURVEILLANCE ALERT", -240, -14, font(MONO, 32), paint(INK, a=fa), "left", 1)
        draw_text(c, "Table 7 · abnormal win rate", -240, 34, hf(32, 600), paint(GRAY, a=fa))
        c.restore()
        for i in range(3):
            rk = prog(T, 22.4 + i * 0.18, 23.2 + i * 0.18)
            if 0 < rk < 1:
                c.drawCircle(W / 2 - 310, 900, 46 + 220 * rk, paint(RED, a=(1 - rk) * 0.7 * fa, stroke=6))
    # the eye in the sky
    ek = lerp(0.62, 1.0, ease_out_back(prog(T, 23.1, 23.7), 1.3)) * ease_out_back(prog(T, 21.77, 22.2), 1.3)
    if ek > 0:
        look_x = math.sin(T * 1.7) * 0.8 * (1 - prog(T, 24.2, 24.5))
        look_y = 0.5 + 0.5 * ease_in_out_cubic(prog(T, 24.2, 24.5))
        c.save()
        c.translate(W / 2, 340)
        c.scale(ek, ek)
        dome_cam(c, 0, 0, 210, (look_x, look_y), rec=1, eye=ease_out_cubic(prog(T, 23.4, 23.9)), t=T)
        c.restore()
        label(c, "THE EYE IN THE SKY", W / 2, 680, 34, INK, "center", a=fade(T, 23.4), bg=YEL)
    # lock-on to "you"
    lk = prog(T, 24.32, 25.0)
    if T > 23.6:
        yk = ease_out_cubic(prog(T, 23.6, 24.1))
        person(c, W / 2, 1120 + 300 * (1 - yk), 1.2, "you", skin=3, glow=0.6)
        if lk > 0:
            e = ease_out_expo(lk)
            box = lerp(520, 330, e)
            col = RED
            # beam
            bp = poly([(W / 2 - 30, 440), (W / 2 + 30, 440), (W / 2 + box / 2, 1120 - box / 2 + 40),
                       (W / 2 - box / 2, 1120 - box / 2 + 40)])
            c.drawPath(bp, paint(RED, a=0.12 * e))
            corners(c, W / 2 - box / 2, 1120 - box / 2 + 40, box, box * 1.05, 60, col, 8)
            if lk > 0.6:
                label(c, "TARGET LOCKED", W / 2, 1560 - 120, 30, WHITE, "center", bg=RED,
                      a=fade(T, 24.73, 0.15))


def s_inspect(c, t, T):
    x, y, w, h = 90, 320, 900, 560
    k = ease_out_cubic(prog(T, 25.4, 25.8))
    c.save()
    c.translate(0, 80 * (1 - k))
    monitor(c, x, y, w, h, T)
    c.save()
    c.clipRect(rect(x, y, w, h))
    # top-down table inside monitor
    c.drawOval(skia.Rect.MakeXYWH(x + 120, y + 190, 660, 330), paint("#2B6A4E"))
    for i, (px, py) in enumerate([(x + 160, y + 160), (x + 450, y + 120), (x + 740, y + 170)]):
        c.drawCircle(px, py, 46, paint(["#5C4A8A", "#2C6E8F", "#7A5233"][i]))
        c.drawCircle(px, py, 26, paint("#2A1D14"))
    zoom = ease_in_out_cubic(prog(T, 26.0, 26.5))
    bx, by = x + 450, y + 120
    corners(c, bx - 90 - 20 * (1 - zoom), by - 90 - 20 * (1 - zoom), 180 + 40 * (1 - zoom), 180 + 40 * (1 - zoom),
            34, YEL, 6, a=zoom)
    c.restore()
    monitor_overlay(c, x, y, w, h, T)
    c.restore()
    # bet timing track
    tk = prog(T, 26.57, 27.4)
    if tk > 0:
        tx, ty, tw = 120, 990, 840
        label(c, "BET TIMING", tx, ty, 26, GRAY, a=clamp(tk * 4))
        c.drawLine(tx, ty + 60, tx + tw, ty + 60, paint(INK, stroke=3, a=clamp(tk * 4)))
        for i in range(6):
            mx = tx + 40 + i * 150
            mk = prog(T, 26.6 + i * 0.12, 26.9 + i * 0.12)
            if mk > 0:
                c.drawLine(mx, ty + 30, mx, ty + 90, paint(GRAY, stroke=4))
                draw_text(c, "spin", mx, ty + 120, font(MONO_M, 20), paint(GRAY), "center")
                bxk = mx + 52
                c.drawCircle(bxk, ty + 60, 14 * ease_out_back(mk), paint(RED))
        draw_text(c, "your bet", tx + 40 + 52, ty + 20, font(MONO_M, 20), paint(RED, a=clamp(tk * 3)), "center")
    # body language: pose skeleton
    bk = prog(T, 27.52, 28.2)
    if bk > 0:
        sx, sy = W / 2 - 120, 1340
        pts = {"h": (sx, sy - 120), "n": (sx, sy - 70), "ls": (sx - 70, sy - 60), "rs": (sx + 70, sy - 60),
               "le": (sx - 110, sy + 10), "re": (sx + 105, sy + 5 + 10 * math.sin(T * 5)),
               "lh": (sx - 70, sy + 60), "rh": (sx + 140, sy - 30 + 10 * math.sin(T * 5)), "p": (sx, sy + 60)}
        bones = [("n", "ls"), ("n", "rs"), ("ls", "le"), ("le", "lh"), ("rs", "re"), ("re", "rh"), ("n", "p")]
        bp = skia.Path()
        for a_, b_ in bones:
            bp.moveTo(*pts[a_])
            bp.lineTo(*pts[b_])
        c.drawPath(trim(bp, 0, ease_out_cubic(bk)), paint(TEAL, stroke=6))
        c.drawCircle(*pts["h"], 36 * ease_out_back(bk), paint(TEAL, stroke=6))
        for kname in ("n", "ls", "rs", "le", "re", "lh", "rh", "p"):
            c.drawCircle(*pts[kname], 10 * ease_out_back(bk), paint(YEL))
        label(c, "BODY LANGUAGE", sx + 190, sy - 40, 26, GRAY, a=bk)
        label(c, "NORMAL", sx + 190, sy + 4, 26, TEAL, a=fade(T, 28.0))


def s_methods(c, t, T):
    methods = ["Past posting", "Wheel bias", "Ball-tracking device", "Dealer signature", "Team collusion"]
    k = fade(T, 28.42, 0.3)
    label(c, "KNOWN CHEATING METHODS", 110, 420, 30, GRAY, a=k)
    for i, m in enumerate(methods):
        ti = 28.6 + i * 0.12
        mk = ease_out_cubic(prog(T, ti, ti + 0.35))
        y = 520 + i * 190
        if mk <= 0:
            continue
        c.save()
        c.translate(-200 * (1 - mk), 0)
        card(c, 100, y, 880, 150, a=mk)
        draw_text(c, m, 150, y + 92, hf(48, 700), paint(INK, a=mk))
        c.restore()
        xt = 30.3 + i * 0.22
        xk = prog(T, xt, xt + 0.25)
        if xk > 0:
            c.drawLine(140, y + 76, 140 + 560 * ease_out_cubic(xk), y + 76, paint(RED, stroke=7))
            stamp(c, "NO MATCH", 850, y + 78, 44, T - xt - 0.05, RED, angle=-4)


def s_draining(c, t, T):
    k = fade(T, 31.9, 0.3)
    label(c, "TABLE 7  ·  CASINO WIN / LOSS", 110, 420, 28, GRAY, a=k)
    x0, y0, w, h = 110, 480, 860, 700
    card(c, x0 - 30, y0 - 30, w + 60, h + 60, a=k)
    zero = y0 + 160
    c.drawLine(x0, zero, x0 + w, zero, paint(INK, a=0.5 * k, stroke=3))
    draw_text(c, "$0", x0 + 6, zero - 12, font(MONO_M, 22), paint(GRAY, a=k))
    pk = ease_in_out_cubic(prog(T, 32.3, 35.2))
    path = skia.Path()
    fill = skia.Path()
    path.moveTo(x0, zero - 30)
    fill.moveTo(x0, zero)
    fill.lineTo(x0, zero - 30)
    n = 60
    for i in range(1, n + 1):
        u = i / n
        xx = x0 + w * u
        yy = zero - 30 + (h - 220) * (u ** 1.6) + 14 * math.sin(i * 1.3) * u
        path.lineTo(xx, yy)
        fill.lineTo(xx, yy)
    fill.lineTo(x0 + w, zero)
    fill.close()
    c.save()
    c.clipRect(rect(x0, y0, w * pk + 2, h))
    c.drawPath(fill, paint(RED, a=0.15))
    c.drawPath(path, paint(RED, stroke=9))
    c.restore()
    loss = int(3500 * 11 * pk)
    f = font(COND, 150)
    draw_text(c, "-$%s" % format(loss, ","), x0 + w - 20, y0 + h - 40, f, paint(RED, a=k), "right")
    highlight_text(c, "cannot be ignored", W / 2, 1400, 66, prog(T, 35.45, 36.1), hl=YEL)


def s_identify(c, t, T):
    k = fade(T, 36.45, 0.3)
    # face scan
    cx, cy = W / 2, 640
    person(c, cx, cy - 40, 1.25, "you", skin=3, glow=0.4, shadow=True)
    scan = (T * 1.4) % 1.0
    sy = cy - 180 + 380 * scan
    if T < 40.3:
        c.drawLine(cx - 240, sy, cx + 240, sy, paint(TEAL, stroke=6))
        c.drawRect(rect(cx - 240, sy - 50, 480, 50), paint(TEAL, a=0.15))
        corners(c, cx - 250, cy - 200, 500, 420, 50, TEAL, 7)
        # face mesh points
        for i in range(18):
            px = cx + (hash01(i, 1) - 0.5) * 120
            py = cy - 40 + (hash01(i, 2) - 0.5) * 130
            if abs(py - sy) < 90:
                c.drawCircle(px, py, 5, paint(YEL))
    label(c, "IDENTIFYING..." if T < 40.3 else "NO PRIOR INCIDENTS", cx, 1030, 30, INK, "center", a=k, bg=YEL)
    # database rows
    rows = ["Banned player list", "Incident reports", "Shared casino network", "Known teams"]
    for i, r in enumerate(rows):
        ti = 38.3 + i * 0.25
        rk = ease_out_cubic(prog(T, ti, ti + 0.3))
        if rk <= 0:
            continue
        y = 1080 + i * 95
        c.save()
        c.translate(80 * (1 - rk), 0)
        rrect(c, 110, y, 860, 78, 10, paint("#FBF8F1", a=rk))
        draw_text(c, r, 140, y + 50, hf(34, 600), paint(INK, a=rk))
        done = T > ti + 0.9
        if done:
            draw_text(c, "0 results", 940, y + 50, font(MONO, 28), paint(TEAL, a=rk), "right")
        else:
            for d in range(3):
                c.drawCircle(860 + d * 26, y + 40, 7, paint(GRAY, a=0.3 + 0.7 * (int(T * 8 + d) % 3 == 0)))
        c.restore()
    stamp(c, "NO MATCH", W / 2, 1250, 120, T - 40.88, TEAL, angle=-6)


def crowd_positions(n):
    pts = []
    for i in range(n):
        ring = i // 12
        ang = (i % 12) / 12 * 2 * math.pi + ring * 0.26 + hash01(i, 8) * 0.2
        rx, ry = 395 + ring * 72, 290 + ring * 70
        pts.append((W / 2 + rx * math.cos(ang), 820 + ry * math.sin(ang), ang))
    return pts


def top_head(c, x, y, s, shirt, hair, a=1.0):
    c.drawOval(skia.Rect.MakeLTRB(x - 48 * s, y - 26 * s + 10, x + 48 * s, y + 26 * s + 10),
               paint("#000000", a=0.18 * a, blur=6))
    c.drawOval(skia.Rect.MakeLTRB(x - 48 * s, y - 26 * s, x + 48 * s, y + 26 * s), paint(shirt, a=a))
    c.drawCircle(x, y, 24 * s, paint(hair, a=a))


SHIRTS = ["#7C5CA8", "#D9822B", "#2C6E8F", "#C0392B", "#3C8D4F", "#E7C53C", "#5D6D7E", "#AF6E9D"]
HAIRS = ["#2A1D14", "#6B4226", "#C9A35B", "#111111", "#8A8A86"]


def top_table(c, cx, cy, hl=None, hl_a=0.0, a=1.0):
    c.drawRoundRect(skia.Rect.MakeLTRB(cx - 330, cy - 200, cx + 330, cy + 200), 200, 200, paint("#5B3A1F", a=a))
    c.drawRoundRect(skia.Rect.MakeLTRB(cx - 305, cy - 175, cx + 305, cy + 175), 180, 180, paint(FELT, a=a))
    wheel(c, cx - 170, cy, 120, rot=0.0)
    for i in range(12):
        for j in range(3):
            n = i * 3 + j + 1
            gx, gy = cx - 20 + i * 24, cy - 60 + j * 40
            col = numcol(n)
            c.drawRect(rect(gx, gy, 22, 38), paint(col, a=a))
            if hl == n and hl_a > 0:
                c.drawRect(rect(gx - 3, gy - 3, 28, 44), paint(YEL, a=hl_a, stroke=5))
    return {n: (cx - 20 + ((n - 1) // 3) * 24 + 11, cy - 60 + ((n - 1) % 3) * 40 + 19) for n in range(1, 37)}


def s_crowd(c, t, T):
    cx, cy = W / 2, 820
    k = ease_out_cubic(prog(T, 41.2, 41.7))
    c.save()
    c.translate(cx, cy)
    c.scale(lerp(0.85, 1.0, k), lerp(0.85, 1.0, k))
    c.translate(-cx, -cy)
    top_table(c, cx, cy)
    # you (yellow glow)
    top_head(c, cx + 60, cy + 250, 1.2, "#2C6E8F", "#2A1D14")
    c.drawCircle(cx + 60, cy + 250, 80 + 8 * math.sin(T * 4), paint(YEL, a=0.6, stroke=6))
    pts = crowd_positions(30)
    n_vis = 0
    for i, (px, py, ang) in enumerate(pts):
        if abs(px - (cx + 60)) < 110 and py > cy + 180:
            continue
        ti = 42.16 + i * 0.09
        pk = ease_out_back(prog(T, ti, ti + 0.35), 1.6)
        if pk <= 0:
            continue
        n_vis += 1
        sx = px + math.cos(ang) * 400 * (1 - pk)
        sy = py + math.sin(ang) * 400 * (1 - pk)
        top_head(c, sx, sy, 0.95, SHIRTS[i % 8], HAIRS[i % 5])
    c.restore()
    label(c, "SPECTATORS", 120, 1380, 28, GRAY, a=fade(T, 42.2))
    draw_text(c, str(n_vis), 120, 1510, font(COND, 130), paint(INK, a=fade(T, 42.2)))
    highlight_text(c, "incredible streak", 650, 1470, 50, prog(T, 45.03, 45.6))


def s_copy(c, t, T):
    cx, cy = W / 2, 820
    target = 17
    cent = top_table(c, cx, cy, target, 0.8 + 0.2 * math.sin(T * 6))
    tx, ty = cent[target]
    # your chip
    chip(c, tx, ty, 18, "#2C6E8F")
    pts = crowd_positions(30)
    copiers = [3, 7, 9, 14, 20, 26]
    for j, i in enumerate(pts):
        px, py, ang = i
        if abs(px - (cx + 60)) < 110 and py > cy + 180:
            continue
        top_head(c, px, py, 0.95, SHIRTS[j % 8], HAIRS[j % 5])
    top_head(c, cx + 60, cy + 250, 1.2, "#2C6E8F", "#2A1D14")
    for n_, j in enumerate(copiers):
        px, py, _ = pts[j]
        ti = 47.0 + n_ * 0.18
        ck = ease_in_out_cubic(prog(T, ti, ti + 0.45))
        if ck > 0:
            bx = lerp(px, tx + (n_ - 2.5) * 6, ck)
            by = lerp(py, ty - n_ * 5, ck) - 160 * math.sin(math.pi * ck)
            chip(c, bx, by, 18, SHIRTS[j % 8])
    label(c, "COPYING YOUR BETS", W / 2, 330, 30, INK, "center", bg=YEL, a=fade(T, 47.44))
    # payout multiplier
    mk = fade(T, 48.63, 0.3)
    if mk > 0:
        draw_text(c, "35x  ×  7 players", W / 2, 1330, font(COND, 100), paint(INK, a=mk), "center")
    # cash bleed: bills falling
    bk = prog(T, 49.67, 50.9)
    if bk > 0:
        for i in range(26):
            u = (T - 49.67) * 1.1 - hash01(i, 4) * 0.6
            if u < 0:
                continue
            bx = 120 + hash01(i, 1) * 840
            by = 1380 + u * 600
            if by > 1580:
                continue
            c.save()
            c.translate(bx, by)
            c.rotate((hash01(i, 6) - 0.5) * 80 + u * 120 * (hash01(i, 7) - 0.5))
            rrect(c, -50, -24, 100, 48, 4, paint("#6BA368"))
            c.drawCircle(0, 0, 14, paint("#4A7F48"))
            rrect(c, -44, -18, 88, 36, 3, paint("#E8F2E0", stroke=2))
            c.restore()
        draw_text(c, "BLEEDING CASH", W / 2, 1440, font(COND, 70), paint(RED, a=fade(T, 50.0)), "center", 4)


def s_insideman(c, t, T):
    dealer_out = ease_in_out_cubic(prog(T, 53.27, 53.9))
    dealer_in = ease_out_back(prog(T, 53.67, 54.3), 1.2)
    you_k = ease_out_cubic(prog(T, 50.85, 51.3))
    person(c, 300, 760 + 400 * (1 - you_k), 1.05, "you", skin=3, glow=0.5)
    # old dealer
    if dealer_out < 1:
        person(c, 790 + 600 * dealer_out, 760, 1.05, "dealer", skin=1, look=-0.5, hair="#1A120C")
    if dealer_in > 0:
        person(c, 790 - 600 * (1 - dealer_in), 760, 1.05, "dealer", skin=4, look=-0.5, hair="#C9A35B")
    # dotted connection + question mark
    qk = fade(T, 51.76, 0.3) * (1 - prog(T, 53.1, 53.4))
    if qk > 0:
        c.drawLine(390, 760, 700, 760, paint(RED, a=qk, stroke=8,
                                              effect=skia.DashPathEffect.Make([4, 22], -T * 60)))
        c.drawCircle(545, 640, 60 * ease_out_back(prog(T, 52.0, 52.4)), paint(RED, a=qk))
        draw_text(c, "?", 545, 676, font(COND, 100), paint(WHITE, a=qk), "center")
        label(c, "INSIDE MAN?", W / 2, 470, 40, WHITE, "center", bg=RED, a=fade(T, 52.23))
    sk = fade(T, 53.27, 0.2) * (1 - prog(T, 54.8, 55.1))
    if sk > 0:
        label(c, "NEW DEALER", 790, 470, 34, INK, "center", bg=YEL, a=sk)
    # still winning
    wk = pop(T, 55.99, 0.45)
    if wk > 0:
        c.save()
        c.translate(W / 2, 1300)
        c.scale(wk, wk)
        c.drawPath(mg.star(0, 0, 260, 170, 12, rot=T * 0.3), paint(YEL))
        draw_text(c, "WIN", 0, 50, font(COND, 160), paint(INK), "center", 4)
        c.restore()
    else:
        label(c, "STILL WINNING?", W / 2, 1300, 34, GRAY, "center", a=fade(T, 54.9))


def s_decision(c, t, T):
    k = fade(T, 56.6, 0.3)
    person(c, W / 2, 470 + 200 * (1 - ease_out_cubic(prog(T, 56.6, 57.2))), 0.9, "manager", skin=2,
           look=math.sin(T * 1.6) * 0.8, hair="#3A3A3A")
    label(c, "MANAGEMENT", W / 2, 760, 30, INK, "center", bg=YEL, a=fade(T, 57.06))
    # two options
    for side, (ti, title, sub) in enumerate([(59.3, "LET YOU CONTINUE", "keep losing money"),
                                             (60.27, "KICK YOU OUT", "in front of everyone")]):
        ok = ease_out_back(prog(T, ti, ti + 0.45), 1.2)
        if ok <= 0:
            continue
        x = 60 + side * 500
        c.save()
        c.translate(x + 230, 1150)
        c.scale(ok, ok)
        card(c, -230, -300, 460, 560, col=WHITE)
        draw_text(c, "A" if side == 0 else "B", 0, -190, font(COND, 110), paint(YEL if side == 0 else RED), "center")
        draw_text(c, title, 0, -100, font(COND, 52), paint(INK), "center", 1)
        draw_text(c, sub, 0, -50, hf(30, 500), paint(GRAY), "center")
        if side == 0:
            # draining bar
            dk = prog(T, 59.8, 61.5)
            rrect(c, -170, 20, 340, 60, 10, paint("#E7E0D2"))
            rrect(c, -170, 20, 340 * (1 - 0.7 * dk), 60, 10, paint(RED))
            draw_text(c, "CASINO $", 0, 140, font(MONO, 26), paint(GRAY), "center")
        else:
            # reputation bar cracks
            rk = prog(T, 62.83, 63.4)
            rrect(c, -170, 20, 340, 60, 10, paint("#E7E0D2"))
            rrect(c, -170, 20, 340 * (1 - 0.6 * rk), 60, 10, paint(TEAL))
            if rk > 0:
                cp = poly([(-20, 10), (5, 40), (-10, 55), (15, 92)], close=False)
                c.drawPath(trim(cp, 0, rk * 2), paint(INK, stroke=5))
            draw_text(c, "REPUTATION", 0, 140, font(MONO, 26), paint(GRAY), "center")
            # phones raised
            for i in range(3):
                pk_ = pop(T, 61.6 + i * 0.12, 0.3)
                if pk_ > 0:
                    px = -120 + i * 120
                    c.save()
                    c.translate(px, 205)
                    c.scale(pk_, pk_)
                    rrect(c, -22, -36, 44, 72, 8, paint(INK))
                    c.drawCircle(0, -18, 5, paint(RED if int(T * 3 + i) % 2 else WHITE))
                    c.restore()
        c.restore()
    if T > 60.27:
        c.drawCircle(W / 2, 1150, 46, paint(INK, a=fade(T, 60.27)))
        draw_text(c, "OR", W / 2, 1170, font(COND, 52), paint(YEL, a=fade(T, 60.27)), "center")


def s_advantage(c, t, T):
    k = fade(T, 63.95, 0.3)
    label(c, "ODDS OF THIS STREAK BY LUCK", W / 2, 420, 30, GRAY, "center", a=k)
    n = sum(1 for w_ in WINS if T >= w_)
    n_show = max(n, int(lerp(14, n, prog(T, 63.95, 64.4))))
    val = 37 ** n_show
    s = format(val, ",")
    f = font(COND, 64 if len(s) > 26 else 80)
    draw_text(c, "1 in", W / 2, 560, font(COND, 70), paint(INK, a=k), "center")
    # wrap the big number
    parts = [s[i:i + 20] for i in range(0, len(s), 20)]
    for i, p_ in enumerate(parts):
        draw_text(c, p_, W / 2, 680 + i * 86, f, paint(RED, a=k), "center", 2)
    label(c, "37^%d" % n_show, W / 2, 680 + len(parts) * 86 + 20, 30, GRAY, "center", a=k)
    hl = prog(T, 67.55, 68.5)
    highlight_text(c, "not just luck", W / 2, 1060, 74, hl)
    # dossier + stamp
    dk = ease_out_cubic(prog(T, 68.9, 69.4))
    if dk > 0:
        c.save()
        c.translate(W / 2, 1310 + 300 * (1 - dk))
        c.rotate(3)
        card(c, -330, -170, 660, 340, col="#E9D9B5")
        rrect(c, -330, -200, 220, 50, 10, paint("#E9D9B5"))
        label(c, "PLAYER FILE", -290, -110, 26, INK)
        c.drawLine(-290, -60, 280, -60, paint(INK, a=0.3, stroke=3))
        c.drawLine(-290, -10, 200, -10, paint(INK, a=0.3, stroke=3))
        c.restore()
        stamp(c, "ADVANTAGE PLAYER", W / 2, 1360, 70, T - 69.39, RED, angle=-7)


def s_finale(c, t, T):
    k = ease_out_cubic(prog(T, 71.2, 71.7))
    # polite letter
    lk = 1 - ease_in_cubic(prog(T, 75.4, 75.8))
    if lk > 0:
        c.save()
        c.translate(W / 2, 760 + 220 * (1 - k))
        c.rotate(-2)
        card(c, -390, -360, 780, 720, col="#FFFDF8", a=lk)
        draw_text(c, "Congratulations", 0, -230, font("PlayfairDisplay[wght].ttf", 76, wght=700),
                  paint(INK, a=lk), "center")
        draw_text(c, "on your wins!", 0, -150, font("PlayfairDisplay[wght].ttf", 56, wght=500),
                  paint(INK, a=lk), "center")
        c.drawLine(-300, -100, 300, -100, paint(INK, a=0.25 * lk, stroke=2))
        kk = prog(T, 73.2, 74.9)
        lines = ["We kindly ask that you", "stop playing roulette."]
        for i, ln in enumerate(lines):
            li = clamp(kk * 2 - i)
            n_ch = int(len(ln) * li)
            draw_text(c, ln[:n_ch], -300, -20 + i * 70, hf(44, 500), paint(INK, a=lk))
        draw_text(c, "— Casino Management", 300, 210, font("PlayfairDisplay[wght].ttf", 36, wght=400),
                  paint(GRAY, a=lk * fade(T, 74.5)), "right")
        c.restore()
        # roulette prohibited
        rk = pop(T, 74.75, 0.4)
        if rk > 0:
            c.save()
            c.translate(W / 2, 1340)
            c.scale(rk * lk, rk * lk)
            wheel(c, 0, 0, 130, rot=T)
            c.drawCircle(0, 0, 150, paint(RED, stroke=22))
            c.drawLine(-106, 106, 106, -106, paint(RED, stroke=22))
            c.restore()
    # other games
    if T > 75.6:
        label(c, "OTHER GAMES?", W / 2, 470, 34, INK, "center", bg=YEL, a=fade(T, 75.7))
        games = [(76.03, "BLACKJACK"), (76.42, "SLOTS"), (76.58, "CRAPS")]
        for i, (ti, name) in enumerate(games):
            gk = pop(T, ti, 0.45)
            if gk <= 0:
                continue
            gx, gy = 200 + i * 340, 860
            c.save()
            c.translate(gx, gy)
            c.scale(gk, gk)
            card(c, -150, -190, 300, 380, col=WHITE)
            game_icon(c, i, T)
            draw_text(c, name, 0, 150, font(COND, 44), paint(INK), "center", 2)
            ck = pop(T, ti + 0.3, 0.3)
            if ck > 0:
                c.drawCircle(110, -160, 44 * ck, paint("#2E9E5B"))
                c.drawPath(poly([(88, -160), (104, -142), (134, -178)], close=False), paint(WHITE, stroke=10))
            c.restore()
        draw_text(c, "...are still fine.", W / 2, 1230, hf(70, 800), paint(INK, a=fade(T, 76.91)), "center")
        stamp(c, "BANNED FROM ROULETTE", W / 2, 1400, 60, T - 77.3, RED, angle=-4)


def game_icon(c, i, T):
    if i == 0:
        for j, (rot, col) in enumerate([(-12, RED), (10, INK)]):
            c.save()
            c.rotate(rot)
            c.translate(-40 + j * 70, -20)
            rrect(c, -55, -80, 110, 160, 12, paint(WHITE))
            rrect(c, -55, -80, 110, 160, 12, paint(INK, stroke=4))
            draw_text(c, "A" if j == 0 else "K", -38, -40, font(COND, 44), paint(col))
            c.drawPath(mg.star(0, 10, 30, 14, 4), paint(col))
            c.restore()
    elif i == 1:
        rrect(c, -100, -110, 200, 200, 20, paint(RED))
        rrect(c, -80, -80, 160, 90, 10, paint(WHITE))
        for j in range(3):
            draw_text(c, "7", -52 + j * 52, -12, font(COND, 66), paint(RED), "center")
        c.drawLine(110, -60, 110, 20, paint(INK, stroke=8))
        c.drawCircle(110, -70, 16, paint(INK))
    else:
        for j in range(2):
            c.save()
            c.translate(-45 + j * 90, -20 + j * 20)
            c.rotate(-15 + j * 25)
            rrect(c, -50, -50, 100, 100, 16, paint(WHITE))
            rrect(c, -50, -50, 100, 100, 16, paint(INK, stroke=5))
            pips = [(0, 0)] if j == 0 else [(-22, -22), (22, 22), (-22, 22), (22, -22), (0, 0)]
            for (px, py) in pips:
                c.drawCircle(px, py, 10, paint(INK))
            c.restore()


SCENES = [
    (0.0, 4.6, s_glasses),
    (4.6, 7.45, s_banned),
    (7.45, 9.85, s_firstbets),
    (9.85, 11.3, s_odds),
    (11.3, 14.2, s_crushing),
    (14.2, 19.45, s_staff),
    (19.45, 25.4, s_surveillance),
    (25.4, 28.42, s_inspect),
    (28.42, 31.88, s_methods),
    (31.88, 36.43, s_draining),
    (36.43, 41.2, s_identify),
    (41.2, 46.18, s_crowd),
    (46.18, 50.83, s_copy),
    (50.83, 56.55, s_insideman),
    (56.55, 63.9, s_decision),
    (63.9, 71.17, s_advantage),
    (71.17, DURATION, s_finale),
]
TR = 0.22  # half-length of push transitions


def make(out_w, out_h):
    S = out_w / W
    paper = mg.paper_texture(out_w, out_h, seed=3, tint=(242, 236, 224))
    grains = mg.grain_frames(out_w, out_h, n=6, amount=9)
    grid = skia.Paint(AntiAlias=True)

    def draw(c, T):
        c.drawImage(paper, 0, 0)
        c.save()
        c.scale(S, S)
        # faint layout grid, like graph paper
        gp = paint(INK, a=0.035, stroke=1.5)
        for gx in range(0, W + 1, 90):
            c.drawLine(gx, 0, gx, H, gp)
        for gy in range(0, H + 1, 90):
            c.drawLine(0, gy, W, gy, gp)
        for i, (a, b, fn) in enumerate(SCENES):
            if not (a - TR <= T < b + TR):
                continue
            off = 0.0
            if i > 0 and T < a + TR:
                off = (1 - ease_in_out_quint(prog(T, a - TR, a + TR))) * W
            if i < len(SCENES) - 1 and T >= b - TR:
                off = -ease_in_out_quint(prog(T, b - TR, b + TR)) * W
            if abs(off) >= W:
                continue
            # slow camera push inside each scene
            z = 1.0 + 0.035 * prog(T, a, b)
            dx = noise1(T * 0.35, i) * 6
            dy = noise1(T * 0.3, i + 50) * 6
            c.save()
            c.translate(off + dx, dy)
            c.translate(W / 2, 900)
            c.scale(z, z)
            c.translate(-W / 2, -900)
            fn(c, T - a, T)
            c.restore()
        hud(c, T)
        captions(c, T)
        c.restore()
        g = grains[int(T * 24) % len(grains)]
        gpaint = skia.Paint()
        gpaint.setBlendMode(skia.BlendMode.kOverlay)
        gpaint.setAlphaf(0.55)
        c.drawImage(g, 0, 0, skia.SamplingOptions(), gpaint)
        mg.vignette(c, out_w, out_h, 0.22, "#3A2A12")

    return draw


if __name__ == "__main__":
    import render
    ROOT = mg.ROOT
    render.cli("v1_transcript", "make", DURATION, os.path.join(ROOT, "V1_transcript_edit.mp4"),
               audio=os.environ.get("VOX_AUDIO"))
