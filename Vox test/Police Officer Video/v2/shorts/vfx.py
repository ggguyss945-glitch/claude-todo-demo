"""shorts.vfx: vertical (9:16) overlays for the Shorts, drawn with skia in a 1080 x 1920 DESIGN space.

Every function takes `cv` (a skia canvas already scaled so 1 unit = 1 px of a 1080 x 1920 frame) and, where animated,
`u` = seconds since the element appeared. Colours follow shorts_spec.json format.captions.colours.

    caption(cv, words, key=None, colour=None, u=0, punch=0)   word-synced 1-2 word chunk at 64 % height (Montserrat 900,
                                                             white, black outline 12 % of cap height, soft shadow)
    hud_pill(cv, u, text, sub=None, accent=RED, y=VY_HUD, meter=None, extra=None)   top-centre HUD counter (9-15 % height)
    clock(cv, text, u, x, y)                                  small "12:36 AM" pill with a blinking red dot
    slam(cv, u, text, colour, y, size, dur)                   text slam: 170 % -> 100 % in 4 frames, shake, hard out
    stamp(cv, u, text, colour, x, y, size, rot)               rubber stamp (MATCH 100 %, IDENTICAL)
    tag(cv, u, text, x, y, style, pin=None)                   engine tag (+ leader line to a pinned point)
    subscribe(cv, u)                                          SUBSCRIBE button press (u = 0 at the press; -0.45 .. 1.75)
    endcard(cv, u, question, sub, beats)                      FULL VIDEO ON THE CHANNEL card with the open question
    comments(cv, u, prompt, word)                             fake comments panel (slides up, types the word)
    notebook(cv, u, rows, x, y, w)                            the officer's ANSWER KEY page, ticks writing in
    complaint(cv, u, rows, hl)                                complaint form lines with highlight bars
    bodycam(cv, u, rec=True)                                  bodycam REC overlay (top-left, inside the safe zone)
    doorbell(cv, t, clock)                                    vertical doorbell-app HUD (LIVE pill + timestamp)
    rule_card(cv, n, text, u)                                 the long video's rule card, re-laid for 9:16
    rewind_fx(img, k)                                         VHS REWIND glitch on an RGB frame (k = 0..1 strength)
Safe zones: nothing important above 8 % or below 80 % of the height or right of 88 % of the width.
"""
import math
import numpy as np
import cv2
import skia
from engine.core import Pen, col, text, text_width, rrect, rect, oval, poly, smooth, clamp, ease, ease_out_back, ease_out_cubic, \
    noise1, hash01, _font
from engine import hud as H

VW, VH = 1080, 1920
RED, AMBER, BLUE, PINK, GREEN, WHITE = '#FF2E2E', '#FFC23D', '#5AB0FF', '#FF8FC2', '#3DDC84', '#FFFFFF'
YT_RED = '#FF0033'
CAP_Y = 0.64 * VH            # caption chunk centre
CAP_H = 92.0                 # cap height in px
CAP_SIZE = CAP_H / 0.70      # Montserrat cap height = 0.70 em
VY_HUD = 0.115 * VH          # HUD centre (9-15 % band)
SAFE_R = 0.88 * VW
SAFE_CX = 0.46 * VW          # centre of the usable width (0 .. 88 %)


# ==================================================================================================== text helpers
def _blob(s, size, weight=900, spacing=0.0):
    f = _font(weight, size)
    glyphs = f.textToGlyphs(s); widths = f.getWidths(glyphs)
    pos, x = [], 0.0
    for w in widths: pos.append(skia.Point(x, 0)); x += w + spacing * size
    total = x - spacing * size if glyphs else 0.0
    return skia.TextBlob.MakeFromPosText(s, pos, f), total


def outlined(cv, s, x, y, size, fill=WHITE, outline=0.12, align='center', shadow=0.35, a=255, weight=900, spacing=0.0,
             oc='#000000', glow=None):
    """Heavy text with a thick black outline (outline = fraction of the cap height) and a soft drop shadow; baseline y.
    Returns the width."""
    if not s: return 0.0
    blob, w = _blob(s, size, weight, spacing)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    sw = 2 * outline * size * 0.70
    if shadow:
        cv.drawTextBlob(blob, x0, y + size * 0.07, skia.Paint(Color=col('#000000', 255 * shadow * a / 255), AntiAlias=True,
                                                               Style=skia.Paint.kStrokeAndFill_Style, StrokeWidth=sw,
                                                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.09)))
    if glow:
        gc, ga, gb = glow
        cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(gc, ga * a / 255), AntiAlias=True, Style=skia.Paint.kStrokeAndFill_Style,
                                                StrokeWidth=sw, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, gb)))
    if outline:
        cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(oc, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=sw,
                                                StrokeJoin=skia.Paint.kRound_Join))
    cv.drawTextBlob(blob, x0, y, skia.Paint(Color=col(fill, a), AntiAlias=True))
    return w


def twidth(s, size, weight=900, spacing=0.0):
    return _blob(s, size, weight, spacing)[1]


# ==================================================================================================== captions
def caption(cv, words, key=None, colour=None, u=1.0, punch=0.0, quote=(False, False), y=CAP_Y, alpha=255):
    """words: the chunk's words (1-2); key: index of the coloured keyword in words (or None). u: seconds since the chunk
    appeared (pop 0.85 -> 1 in 3 frames). punch: seconds since the keyword landed (100 -> 118 -> 100 % over 4 frames)."""
    ws = list(words)
    if quote[0]: ws[0] = '“' + ws[0]
    if quote[1]: ws[-1] = ws[-1] + '”'
    size = CAP_SIZE
    sp = twidth(' ', size)
    widths = [twidth(w, size) for w in ws]
    total = sum(widths) + sp * (len(ws) - 1)
    maxw = 2 * (SAFE_R - VW / 2) - 30            # stay left of the right-side buttons
    k = min(1.0, maxw / max(1.0, total))
    sc = k * (0.86 + 0.14 * ease_out_back(clamp(u / 0.05), 2.0))
    if key is not None and 0 <= punch < 0.0667:
        sc *= 1.0 + 0.18 * math.sin(math.pi * punch / 0.0667)
    cv.save(); cv.translate(VW / 2, y + CAP_H / 2); cv.scale(sc, sc)
    x = -total / 2
    for j, w in enumerate(ws):
        c = (colour or AMBER) if (key is not None and j == key) else WHITE
        outlined(cv, w, x, 0, size, c, 0.12, 'left', 0.35, alpha)
        x += widths[j] + sp
    cv.restore()


# ==================================================================================================== HUD
def _pop(u, d=0.18, s=2.2):
    return 0.7 + 0.3 * ease_out_back(clamp(u / d), s) if u < d else 1.0


def hud_pill(cv, u, title, value, accent=RED, y=VY_HUD, meter=None, sub=None, w=520, flash=0.0):
    """Top-centre HUD: a dark pill with a small title and a big value, an optional meter bar (0..1) and a sub line.
    u: seconds since the value last changed (pops)."""
    pen = Pen(cv)
    sc = _pop(u)
    h = 118 if meter is None else 150
    cv.save(); cv.translate(VW / 2, y); cv.scale(sc, sc)
    box = rrect(-w / 2, -h / 2, w, h, 26)
    pen.shadow(box, 0, 8, 18, '#000000', 120)
    pen.fill(box, '#07090f', 205)
    pen.line(box, 4, accent, 230)
    if flash > 0: pen.fill(box, accent, 160 * flash)
    text(cv, title, -w / 2 + 34, -h / 2 + 44, 800, 26, '#aeb6c8', 255, 0.16, 'left')
    pen.fill(oval(w / 2 - 34, -h / 2 + 35, 9), accent, 255 * (0.5 + 0.5 * (math.sin(u * 7.0) > -0.3)))
    outlined(cv, value, 0, -h / 2 + 100, 64, WHITE, 0.08, 'center', 0.0, 255, 900)
    if meter is not None:
        bw, by = w - 70, h / 2 - 30
        pen.fill(rrect(-bw / 2, by, bw, 14, 7), '#262b38', 255)
        pen.fill(rrect(-bw / 2, by, max(14, bw * clamp(meter)), 14, 7), accent, 255)
    if sub:
        text(cv, sub, 0, h / 2 + 40, 800, 30, '#ffffff', 235, 0.08, 'center', 0.8)
    cv.restore()


def scoreboard(cv, u, him, you, y=VY_HUD + 112):
    """S3 scoreboard under the quiz HUD: HIM ✓✓✗ / YOU —."""
    pen = Pen(cv)
    sc = _pop(u)
    cv.save(); cv.translate(VW / 2, y); cv.scale(sc, sc)
    for side, (lab, marks, c) in enumerate((('HIM', him, '#ff6b6b'), ('YOU', you, AMBER))):
        x0 = -250 + side * 270
        box = rrect(x0, -34, 230, 68, 18)
        pen.fill(box, '#07090f', 200); pen.line(box, 3, c, 220)
        text(cv, lab, x0 + 18, 12, 900, 30, c, 255, 0.06, 'left')
        mx = x0 + 112
        for m in marks:
            _mark(pen, m, mx + 12, 0, 13)
            mx += 30
    cv.restore()


def _mark(pen, m, x, y, r, a=255):
    """Tick / cross / dash / tilde drawn as strokes (the font has no check-mark glyphs)."""
    if m == 'Y':
        p = skia.Path(); p.moveTo(x - r, y); p.lineTo(x - r * 0.3, y + r * 0.75); p.lineTo(x + r, y - r * 0.9)
        pen.line(p, r * 0.5, GREEN, a)
    elif m == 'N':
        pen.seg((x - r * 0.8, y - r * 0.8), (x + r * 0.8, y + r * 0.8), r * 0.5, RED, a)
        pen.seg((x + r * 0.8, y - r * 0.8), (x - r * 0.8, y + r * 0.8), r * 0.5, RED, a)
    elif m == '~':
        p = skia.Path(); p.moveTo(x - r, y + r * 0.2); p.cubicTo(x - r * 0.4, y - r * 0.7, x + r * 0.2, y + r * 0.9, x + r, y - r * 0.2)
        pen.line(p, r * 0.45, AMBER, a)
    else:
        pen.seg((x - r * 0.7, y), (x + r * 0.7, y), r * 0.35, '#9aa3b8', a)


def clock(cv, s, u, x=VW / 2, y=VY_HUD - 104, accent=RED):
    pen = Pen(cv)
    sc = _pop(u, 0.14)
    w = text_width(s, 800, 30, 0.08) + 70
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    box = rrect(-w / 2, -24, w, 48, 24)
    pen.fill(box, '#07090f', 190)
    pen.fill(oval(-w / 2 + 26, 0, 8), accent, 255 * (0.35 + 0.65 * ((u % 1.0) < 0.6)))
    text(cv, s, -w / 2 + 44, 11, 800, 30, '#ffffff', 245, 0.08, 'left')
    cv.restore()


def doorbell(cv, t, clock_s='12:36:07 AM', name='FRONT DOOR', y=None):
    """Vertical doorbell-app HUD: camera name + LIVE pill (left) under the main HUD."""
    pen = Pen(cv)
    y = y if y is not None else 0.205 * VH
    text(cv, name, 60, y, 800, 26, '#e8ecf6', 230, 0.14, 'left', 0.6)
    lw = text_width(name, 800, 26, 0.14)
    bx = 60 + lw + 22
    pen.fill(rrect(bx, y - 26, 92, 34, 8), '#d4252c', 230)
    pen.fill(oval(bx + 18, y - 9, 6), '#ffffff', 255 * (0.4 + 0.6 * ((t % 1.0) < 0.55)))
    text(cv, 'LIVE', bx + 30, y + 1, 800, 22, '#ffffff', 255, 0.1, 'left')
    text(cv, clock_s, 60, y + 40, 600, 24, '#c8cfe0', 210, 0.06, 'left', 0.6)


def bodycam(cv, u, rec=True, label='AXON BODY 4  ·  UNIT 24-07'):
    pen = Pen(cv)
    y = 0.205 * VH
    if rec:
        pen.fill(oval(76, y - 10, 13), '#ff2a2a', 255 * (0.35 + 0.65 * ((u % 0.8) < 0.5)))
        text(cv, 'REC', 100, y + 2, 900, 36, '#ffffff', 245, 0.08, 'left', 0.7)
    else:
        text(cv, 'CAMERA OFF', 60, y + 2, 900, 36, '#ff5a5a', 245, 0.08, 'left', 0.7)
    text(cv, label, 60, y + 44, 700, 22, '#e8e8e8', 200, 0.1, 'left', 0.6)
    text(cv, '2026-10-14  00:36:%02d' % (7 + int(u) % 50), 60, y + 76, 600, 22, '#e8e8e8', 190, 0.08, 'left', 0.6)


# ==================================================================================================== slams, stamps, tags
def slam(cv, u, s, c=RED, y=0.40 * VH, size=150, dur=0.9, rot=-3.0, x=SAFE_CX, outline_c='#000000', sub=None):
    """Impact text: 170 % -> 100 % in 4 frames with a 2-frame white flash on the letters, jitter for 0.15 s, hold,
    hard exit (scale 106 % + fade over 3 frames). Lines split on '\\n'; each fits 86 % of the width."""
    if u < 0 or u > dur: return
    lines = s.split('\n')
    ws = [twidth(l, size) for l in lines]
    k = min(1.0, 0.84 * VW / max(ws))
    if u < 0.0667: sc = 1.7 - 0.7 * ease_out_cubic(u / 0.0667)
    elif u > dur - 0.05: sc = 1.0 + 0.06 * (u - (dur - 0.05)) / 0.05
    else: sc = 1.0
    a = 255 if u < dur - 0.05 else 255 * clamp((dur - u) / 0.05)
    jx = 9 * noise1(u * 40, 3) * clamp(1 - u / 0.18)
    jy = 7 * noise1(u * 40, 4) * clamp(1 - u / 0.18)
    half = min(x - 22, VW - 22 - x)                      # the overshoot frame never leaves the frame margins
    sc = min(sc, 2 * half / max(1.0, max(ws) * k * (1 + abs(math.sin(math.radians(rot))) * 0.3)))
    cv.save(); cv.translate(x + jx, y + jy); cv.rotate(rot); cv.scale(sc * k, sc * k)
    lh = size * 1.02
    y0 = -lh * (len(lines) - 1) / 2 + size * 0.36
    fl = u < 0.033
    for j, l in enumerate(lines):
        outlined(cv, l, 0, y0 + j * lh, size, '#ffffff' if fl else c, 0.14, 'center', 0.5, a, 900, 0.01, outline_c,
                 glow=(c, 110, 18) if c != WHITE else None)
    if sub:
        outlined(cv, sub, 0, y0 + len(lines) * lh - size * 0.25, size * 0.38, WHITE, 0.12, 'center', 0.4, a, 900, 0.06)
    cv.restore()


def stamp(cv, u, s, c=RED, x=SAFE_CX, y=0.33 * VH, size=96, rot=-9.0, dur=1.6):
    if u < 0 or u > dur: return
    pen = Pen(cv)
    sc = 1.45 - 0.45 * ease_out_cubic(clamp(u / 0.08))
    a = 255 * clamp((dur - u) / 0.12)
    w = twidth(s, size, 900, 0.06) + 70
    h = size * 1.35
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc, sc)
    box = rrect(-w / 2, -h / 2, w, h, 14)
    pen.fill(box, '#000000', a * 0.35)
    pen.line(box, 10, c, a)
    pen.line(rrect(-w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 8), 4, c, a * 0.8)
    text(cv, s, 0, size * 0.36, 900, size, c, a, 0.06, 'center', 0.0)
    cv.restore()


def tag(cv, u, s, x, y, style='red', pin=None, size=40, hold=None):
    """Engine tag at vertical coords; pin=(px, py) draws a leader line from the subject point to the tag."""
    if u < 0: return
    a = 255
    if hold is not None and u > hold: a = 255 * clamp(1 - (u - hold) / 0.12)
    if a <= 0: return
    if pin is not None:
        pen = Pen(cv)
        k = clamp(u / 0.15)
        px, py = pin
        pen.seg((px, py), (px + (x - px) * k, py + (y - py) * k), 4.0, '#ffffff', 0.9 * a)
        pen.fill(oval(px, py, 10), '#ffffff', 0.95 * a); pen.line(oval(px, py, 19), 3.5, '#ffffff', 0.65 * a * k)
    H.tag(cv, s, x, y, style, u, alpha=a, size=size)


def flash(img, c, k):
    """Full-frame colour flash (img uint8 RGB, k 0..1)."""
    if k <= 0: return img
    cc = np.array([int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)], np.float32)
    return cv2.addWeighted(img, 1 - k, np.full_like(img, 0) + cc.astype(np.uint8), k, 0)


# ==================================================================================================== subscribe
def _bell(pen, x, y, s, a, wig=0.0, c='#ffffff'):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(wig); cv.scale(s, s)
    body = smooth([(-20, 14), (-18, -6), (-12, -18), (0, -23), (12, -18), (18, -6), (20, 14)], False)
    p = skia.Path(body); p.lineTo(24, 18); p.lineTo(-24, 18); p.close()
    pen.fill(p, c, a)
    pen.fill(oval(0, 24, 6), c, a)
    pen.fill(oval(0, -26, 4), c, a)
    cv.restore()


def subscribe(cv, u, y=0.50 * VH, x=SAFE_CX, label='SUBSCRIBE', hand='cursor', from_=None, lead=0.5):
    """Big SUBSCRIBE button (720 x 184, 67 % of the width), u = seconds from the press (-0.5 pop-in .. 0 press .. 1.8 out):
    pops in with an overshoot (from_ = (x, y) it flies out of, e.g. the finger that will press it), breathes, gets squashed
    by the press (x 106 %, y 82 %) with a white impact ring and a rebound, flips to grey SUBSCRIBED + a check mark and a
    ringing bell, then pops out. hand: 'cursor' (a hand cursor taps it) or None (the story action is the press: a palm,
    a finger on a radio key or a bodycam)."""
    lead = max(0.12, min(0.5, lead))                   # pop-in lead before the press (starts at the cut into the action)
    if u < -lead or u > 1.8: return
    pen = Pen(cv)
    ui = u + lead
    s_in = ease_out_back(clamp(ui / min(0.24, lead)), 2.6)
    s_out = 1.0 - ease_out_cubic(clamp((u - 1.58) / 0.22))
    breathe = 1.0 + 0.025 * math.sin(ui * 14.0) if u < 0 else 1.0
    sx = sy = 1.0
    if 0 <= u < 0.08:
        q = math.sin(math.pi * u / 0.08); sx, sy = 1.0 + 0.06 * q, 1.0 - 0.18 * q
    elif 0.08 <= u < 0.26:
        q = math.sin(math.pi * (u - 0.08) / 0.18); sx, sy = 1.0 - 0.02 * q, 1.0 + 0.06 * q
    sc = s_in * s_out * breathe
    if sc <= 0.01: return
    done = u >= 0.06
    w, h = 720.0, 184.0
    cx, cy = x, y
    if from_ is not None and ui < min(0.24, lead):        # flies out of the pressing hand / object
        k = ease_out_cubic(clamp(ui / min(0.24, lead))); cx = from_[0] + (x - from_[0]) * k; cy = from_[1] + (y - from_[1]) * k
    cv.save(); cv.translate(cx, cy); cv.scale(sc * sx, sc * sy)
    box = rrect(-w / 2, -h / 2, w, h, h / 2)
    pen.shadow(box, 0, 16, 34, '#000000', 190)
    if not done:
        pen.line(box, 22, YT_RED, 90, blur=18)
    pen.fill(box, '#3a3a3a' if done else YT_RED, 255)
    pen.fill(rrect(-w / 2 + 10, -h / 2 + 8, w - 20, h * 0.40, h * 0.3), '#ffffff', 22 if done else 46)
    pen.line(box, 5, '#ffffff', 60 if done else 110)
    if done:
        wig = 20 * math.sin((u - 0.06) * 34) * clamp(1 - (u - 0.06) / 0.7)
        _bell(pen, -w / 2 + 92, -4, 1.9, 255, wig)
        outlined(cv, 'SUBSCRIBED', 38, 30, 80, '#eeeeee', 0.0, 'center', 0.0, 255, 900, 0.02)
        ck = clamp((u - 0.1) / 0.14)
        if ck > 0:
            pen.seg((w / 2 - 70, 2), (w / 2 - 70 + 16 * ck, 2 + 16 * ck), 9, GREEN, 255)
            if ck >= 1: pen.seg((w / 2 - 54, 18), (w / 2 - 22, -22), 9, GREEN, 255)
    else:
        pen.fill(oval(-w / 2 + 92, 0, 52), '#ffffff', 255)
        pen.fill(poly([(-w / 2 + 76, -26), (-w / 2 + 76, 26), (-w / 2 + 118, 0)]), YT_RED, 255)
        outlined(cv, label, 46, 32, 90, '#ffffff', 0.0, 'center', 0.0, 255, 900, 0.03)
    cv.restore()
    if 0 <= u <= 0.45:                                 # impact ring from the press
        r = 60 + 420 * ease_out_cubic(u / 0.45)
        pen.line(oval(x, y, r, r * 0.42), 10 * (1 - u / 0.45) + 2, '#ffffff', 230 * (1 - u / 0.45))
    if 0.08 <= u <= 1.3:                               # bell burst
        k = clamp((u - 0.08) / 0.25)
        bx, by = x - w / 2 * sc + 92, y - 6
        for j in range(7):
            ang = -math.pi / 2 + (j - 3) * 0.40
            r0, r1 = 70 + 26 * k, 96 + 70 * k
            pen.seg((bx + math.cos(ang) * r0, by + math.sin(ang) * r0), (bx + math.cos(ang) * r1, by + math.sin(ang) * r1),
                    7, AMBER, 255 * (1 - clamp((u - 0.55) / 0.5)))
    if hand == 'cursor' and -0.4 <= u <= 0.9:          # hand cursor: slides in from the lower right, taps at u = 0, leaves
        if u < 0: k = ease_out_cubic(clamp((u + 0.4) / 0.38)); hx, hy = x + 150 + 260 * (1 - k), y + 50 + 300 * (1 - k)
        else: k = ease_out_cubic(clamp((u - 0.35) / 0.5)); hx, hy = x + 150 + 300 * k, y + 50 + 340 * k
        press_k = 0.88 if 0 <= u < 0.1 else 1.0
        _hand_cursor(pen, hx, hy, 1.5 * press_k, 255 * (1 - clamp((u - 0.6) / 0.3)))


def _hand_cursor(pen, x, y, s, a):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s); cv.rotate(-18)
    fing = rrect(-13, -8, 26, 74, 13)
    palm = rrect(-30, 50, 76, 86, 26)
    shape = skia.Op(fing, palm, skia.PathOp.kUnion_PathOp)
    for dx in (24, 44):
        shape = skia.Op(shape, rrect(dx - 12, 38, 22, 46, 11), skia.PathOp.kUnion_PathOp)
    pen.shadow(shape, 3, 6, 10, '#000000', a * 0.5)
    pen.fill(shape, '#ffffff', a)
    pen.line(shape, 5, '#111111', a)
    cv.restore()


# ==================================================================================================== end card + comments
def _yt_logo(pen, x, y, hgt, a=255):
    w = hgt * 1.42
    pen.fill(rrect(x - w / 2, y - hgt / 2, w, hgt, hgt * 0.26), YT_RED, a)
    pen.fill(poly([(x - hgt * 0.17, y - hgt * 0.24), (x - hgt * 0.17, y + hgt * 0.24), (x + hgt * 0.25, y)]), '#ffffff', a)


def endcard(cv, u, question, sub='FULL VIDEO ON THE CHANNEL', hits=(), y=0.44 * VH, dur=4.0, title=None, x=SAFE_CX):
    """The long-video pointer over the moving story image. u = seconds since the card started.
    From the first frame (0.14 s overshoot pop): the YouTube play logo + FULL VIDEO / ON THE CHANNEL (held to the end).
    hits (relative seconds): the card punches (+7 %) on every hit; the question lines (split on '\n') slam in one per hit
    from the second hit on (or all on the first if there is only one), at caption size or larger. A slow push-in (+5 %
    over the card), a pulsing play logo and a bouncing arrow toward the related-video link under the Short."""
    if u < 0: return
    pen = Pen(cv)
    qs = question.split('\n')
    hits = sorted(hits) or [0.0, 0.4]
    qh = hits[1:] if len(hits) > 1 else hits
    w = 900.0
    qsize = []
    for q in qs:
        sz = 138.0
        sz = min(sz, (w - 90) / max(1.0, twidth(q, 1.0)))
        qsize.append(sz)
    qh_total = sum(sz * 1.04 for sz in qsize)
    h = 300 + qh_total + (70 if title else 20)
    k_in = ease_out_back(clamp(u / 0.14), 2.2)
    punch = 1.0
    for ht in hits:
        d = u - ht
        if 0 <= d < 0.2: punch = max(punch, 1.0 + 0.07 * math.sin(math.pi * min(1.0, d / 0.2)) * (1 - d / 0.2) * 2)
    push = 1.0 + 0.05 * clamp(u / max(1.0, dur))
    sc = k_in * punch * push
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    box = rrect(-w / 2, -h / 2, w, h, 44)
    pen.shadow(box, 0, 18, 44, '#000000', 170)
    pen.fill(box, '#05070c', 150)
    pen.line(box, 26, RED, 70 + 60 * max(0.0, punch - 1.0) / 0.07, blur=22)
    pen.line(box, 8, RED, 255)
    pen.line(rrect(-w / 2 + 18, -h / 2 + 18, w - 36, h - 36, 32), 2.5, '#ff8080', 110)
    y0 = -h / 2
    # FULL VIDEO line: there from the first frame
    pul = 1.0 + 0.05 * math.sin(u * 7.5)
    fw = twidth('FULL VIDEO', 104)
    gx = -(fw + 170) / 2
    cv.save(); cv.translate(gx + 66, y0 + 108); cv.scale(pul, pul)
    _yt_logo(pen, 0, 0, 104)
    cv.restore()
    outlined(cv, 'FULL VIDEO', gx + 150, y0 + 108 + 37, 104, AMBER, 0.12, 'left', 0.45, 255, 900, 0.01)
    outlined(cv, 'ON THE CHANNEL', 0, y0 + 230, 70, WHITE, 0.12, 'center', 0.45, 255, 900, 0.03)
    dv = ease_out_cubic(clamp(u / 0.25))
    pen.fill(rrect(-300 * dv, y0 + 268, 600 * dv, 6, 3), RED, 255)
    # the open question, one line per hit
    yy = y0 + 290
    for j, q in enumerate(qs):
        sz = qsize[j]; yy += sz * 1.04
        ht = qh[min(j, len(qh) - 1)]
        uu = u - ht
        if uu < 0: continue
        s2 = 1.65 - 0.65 * ease_out_cubic(clamp(uu / 0.0667))
        lim = (w - 40) / max(1.0, twidth(q, sz))
        s2 = min(s2, max(1.0, lim))
        cv.save(); cv.translate(0, yy - sz * 0.36); cv.scale(s2, s2)
        outlined(cv, q, 0, sz * 0.36, sz, '#ffffff' if uu < 0.034 else (WHITE if j < len(qs) - 1 else RED), 0.13, 'center', 0.5,
                 255, 900, 0.01, glow=(RED, 90, 16) if j == len(qs) - 1 else None)
        cv.restore()
    if title:
        text(cv, title, 0, h / 2 - 34, 800, 34, '#c9cfdc', 230 * clamp(u / 0.3), 0.04, 'center')
    cv.restore()
    # arrow toward the related-video link under the Short
    if u >= 0.15:
        bob = 22 * math.sin((u - 0.15) * 8.0)
        ay = y + h / 2 * sc + 60 + bob
        a_ = 255 * clamp((u - 0.15) / 0.1)
        pen.fill(rrect(x - 22, ay - 10, 44, 64, 8), AMBER, a_)
        pen.fill(poly([(x - 62, ay + 50), (x + 62, ay + 50), (x, ay + 120)]), AMBER, a_)


def _split2(s):
    ws = s.split()
    if len(ws) <= 2: return [s]
    m = len(ws) // 2
    return [' '.join(ws[:m]), ' '.join(ws[m:])]


def comments(cv, u, prompt, word, y=0.53 * VH, dur=1.4, handles=('@nightshift_92', '@porchlight_k', '@dont.open.it')):
    """Fake comments panel: slides up, 2 comments already there, the viewer's comment field types `word`."""
    if u < 0 or u > dur: return
    pen = Pen(cv)
    k = ease_out_cubic(clamp(u / 0.18)) * (1 - ease_out_cubic(clamp((u - dur + 0.15) / 0.15)))
    w, h = 880.0, 470.0
    x0 = SAFE_CX - w / 2
    yy = y + (1 - k) * 260
    box = rrect(x0, yy, w, h, 34)
    pen.shadow(box, 0, 10, 30, '#000000', 180 * k)
    pen.fill(box, '#0f0f10', 245 * k)
    text(cv, 'Comments', x0 + 40, yy + 62, 900, 38, '#ffffff', 255 * k, 0.0, 'left')
    text(cv, '2.4K', x0 + 250, yy + 62, 700, 32, '#aaaaaa', 255 * k, 0.0, 'left')
    for j, (hd, msg, col_) in enumerate(((handles[0], word, '#6a8cff'), (handles[1], word + ' \U0001F6AA' if False else word + '!!', '#e86a8a'))):
        cy = yy + 130 + j * 92
        pen.fill(oval(x0 + 70, cy, 30), col_, 255 * k)
        text(cv, hd, x0 + 120, cy - 8, 700, 24, '#aaaaaa', 255 * k, 0.0, 'left')
        text(cv, msg, x0 + 120, cy + 28, 800, 32, '#ffffff', 255 * k, 0.0, 'left')
    fy = yy + h - 120
    pen.fill(rrect(x0 + 30, fy, w - 60, 84, 42), '#272727', 255 * k)
    typed = word[:int(len(word) * clamp((u - 0.3) / 0.5))]
    caret = '|' if (u * 3) % 1 < 0.6 else ''
    text(cv, typed + caret if typed else 'Add a comment...' + caret, x0 + 70, fy + 54, 800 if typed else 600, 34,
         '#ffffff' if typed else '#9a9a9a', 255 * k, 0.0, 'left')
    pl = prompt.split('\n')
    for j, l in enumerate(pl):
        outlined(cv, l, SAFE_CX, yy - 40 - (len(pl) - 1 - j) * 58, 48, AMBER if j == 0 else WHITE, 0.12, 'center', 0.4, 255 * k)


# ==================================================================================================== inserts
def notebook(cv, u, rows, x=SAFE_CX, y=0.40 * VH, w=780, title='ANSWER KEY', ticks=None):
    """The officer's notebook page, rows typed in a hand-written style; ticks[j] = seconds when row j's tick is drawn."""
    pen = Pen(cv)
    k = ease_out_back(clamp(u / 0.2), 1.6)
    h = 190 + 118 * len(rows)
    cv.save(); cv.translate(x, y); cv.rotate(-3.0); cv.scale(k, k)
    page = rrect(-w / 2, -h / 2, w, h, 16)
    pen.shadow(page, 0, 14, 30, '#000000', 190)
    pen.fill(page, '#efe8d4', 255)
    pen.texture(page, 'paper', 0.25, 'multiply', 1.0)
    for j in range(len(rows) + 2):
        yy = -h / 2 + 150 + j * 118 - 60
        pen.seg((-w / 2 + 30, yy + 64), (w / 2 - 30, yy + 64), 2.5, '#8fa9c9', 200)
    pen.seg((-w / 2 + 110, -h / 2 + 10), (-w / 2 + 110, h / 2 - 10), 3, '#d98080', 200)
    for r_ in range(6): pen.fill(oval(-w / 2 + 50, -h / 2 + 80 + r_ * (h - 160) / 5, 13), '#1b1b1f', 220)
    text(cv, title, -w / 2 + 140, -h / 2 + 88, 900, 54, '#1a2a6a', 255, 0.04, 'left')
    for j, r in enumerate(rows):
        t0 = (ticks[j] if ticks else 0.25 + j * 0.4) - 0.35
        uu = u - t0
        if uu < 0: continue
        yy = -h / 2 + 200 + j * 118
        s_ = r
        n = int(len(s_) * clamp(uu / 0.3))
        cv.save(); cv.skew(-0.18, 0)
        text(cv, s_[:n], -w / 2 + 160 + yy * 0.18, yy, 800, 56, '#1f2a5c', 255, 0.01, 'left')
        cv.restore()
        tu = uu - 0.35
        if tu > 0:
            tx = w / 2 - 110
            p = skia.Path(); p.moveTo(tx - 34, yy - 22)
            q = clamp(tu / 0.12)
            p.lineTo(tx - 34 + 22 * min(1, q * 2), yy - 22 + 26 * min(1, q * 2))
            if q > 0.5: p.lineTo(tx - 12 + 50 * (q - 0.5) * 2, yy + 4 - 60 * (q - 0.5) * 2)
            pen.line(p, 12, '#c0161c', 255)
    cv.restore()


def complaint(cv, u, rows, hl=(), x=SAFE_CX, y=0.36 * VH, w=900, title='COMPLAINT  —  UNAUTHORIZED PERSON', blur_row=None,
              reveal=None):
    """Complaint form: rows [(label, value)] (label 44 px over value 68 px, readable on a phone), hl = {row: seconds since
    its highlight}; blur_row = row index whose value is blurred until `reveal` (0..1 letters shown)."""
    pen = Pen(cv)
    k = ease_out_back(clamp(u / 0.18), 1.6)
    RH = 150
    h = 120 + RH * len(rows)
    cv.save(); cv.translate(x, y); cv.rotate(1.5); cv.scale(k, k)
    page = rrect(-w / 2, -h / 2, w, h, 12)
    pen.shadow(page, 0, 14, 30, '#000000', 190)
    pen.fill(page, '#f1efe9', 255)
    pen.texture(page, 'paper', 0.2, 'multiply', 1.0)
    pen.fill(rrect(-w / 2, -h / 2, w, 92, 12), '#1c2a4a', 255)
    text(cv, title.split('  ')[0], -w / 2 + 36, -h / 2 + 64, 900, 46, '#ffffff', 255, 0.08, 'left')
    for j, (lab, val) in enumerate(rows):
        yy = -h / 2 + 120 + j * RH
        hu = dict(hl).get(j)
        if hu is not None and hu >= 0:
            kk = ease_out_cubic(clamp(hu / 0.15))
            pen.fill(rect(-w / 2 + 20, yy + 6, (w - 40) * kk, RH - 12), '#ffd23d', 160)
        text(cv, lab.rstrip(':'), -w / 2 + 40, yy + 50, 800, 44, '#5a5f6e', 255, 0.06, 'left')
        vs = min(68.0, 68.0 * (w - 80) / max(1.0, text_width(val, 900, 68, 0.02)))
        if blur_row == j and reveal is not None and reveal < 1.0:
            n = int(len(val) * clamp(reveal))
            shown, hidden = val[:n], val[n:]
            wsh = text(cv, shown, -w / 2 + 40, yy + 126, 900, vs, '#c0161c', 255, 0.02, 'left') if shown else 0.0
            if hidden:
                xx = -w / 2 + 40 + wsh
                hw = text_width(hidden, 900, vs, 0.02)
                pen.fill(rrect(xx, yy + 126 - vs * 0.8, hw + 8, vs * 0.98, 8), '#1a1a1a', 235)
        else:
            text(cv, val, -w / 2 + 40, yy + 126, 900, vs, '#c0161c' if blur_row == j else '#16171c', 255, 0.02, 'left')
    cv.restore()


def callout(cv, u, x, y, r=90, label=None, c=RED, dur=1.2, lx=None, ly=None, size=64, to=None):
    """Hand-drawn style ring around a detail (draws on over 0.18 s, overshooting its start like a marker stroke) + an
    optional label with a leader line. to = (x1, y1): the ring follows the detail there over dur (camera push)."""
    if u < 0 or u > dur: return
    if to is not None:
        q = clamp(u / max(1e-3, dur)); dx, dy = (to[0] - x) * q, (to[1] - y) * q
        x, y = x + dx, y + dy
        if lx is not None: lx += dx
        if ly is not None: ly += dy
    pen = Pen(cv)
    a = 255 * clamp((dur - u) / 0.12)
    k = ease_out_cubic(clamp(u / 0.18))
    sw = 375.0 * k
    p = skia.Path(); p.addArc(skia.Rect.MakeLTRB(x - r, y - r * 0.86, x + r, y + r * 0.86), -100, min(sw, 359.0))
    if sw > 359.0:
        p.addArc(skia.Rect.MakeLTRB(x - r * 1.06, y - r * 0.92, x + r * 1.06, y + r * 0.92), -100, sw - 359.0)
    pen.line(p, 18, '#000000', a * 0.55)
    pen.line(p, 11, c, a)
    if label and u > 0.12:
        lx = x if lx is None else lx; ly = (y - r - 90) if ly is None else ly
        kk = ease_out_cubic(clamp((u - 0.12) / 0.12))
        y0 = y - r * 0.86 if ly < y else y + r * 0.86
        y1 = ly + 20 if ly < y else ly - size * 0.85
        pen.seg((x, y0), (x + (lx - x) * kk, y0 + (y1 - y0) * kk), 6, c, a)
        outlined(cv, label, lx, ly, size, WHITE, 0.14, 'center', 0.5, a * kk)


def rule_card(cv, n, text_, u, y=0.40 * VH, type_dur=1.3):
    """The long video's rule card re-laid for 9:16: RULE label, a big numeral popping in, red line, the rule typed on
    in heavy text with *red* keywords, 7 progress dashes."""
    if u < 0: return
    pen = Pen(cv)
    x = SAFE_CX
    pen.radial(None, x, y, 760, [(0, '#000000', 150), (1, '#000000', 40)], sy=1.2)
    text(cv, 'RULE', x, y - 300, 800, 40, '#c8c8d2', 255 * clamp(u / 0.05), 0.5, 'center', 0.5)
    sc = 1.25 - 0.25 * ease_out_cubic(clamp(u / 0.08))
    cv.save(); cv.translate(x, y - 140); cv.scale(sc, sc)
    outlined(cv, '%d' % n, 0, 80, 250, WHITE, 0.06, 'center', 0.5, 255 * clamp(u / 0.04))
    cv.restore()
    lw = 220 * ease_out_cubic(clamp((u - 0.12) / 0.25))
    if lw > 0: pen.fill(rrect(x - lw, y - 20, lw * 2, 8, 4), RED, 255)
    lines = H.wrap_rich(text_.upper(), 900, 62, 860, 0.02)
    total = sum(len(l.replace('*', '')) for l in lines)
    shown = total * clamp((u - 0.25) / type_dur)
    used = 0
    for i, l in enumerate(lines):
        nl = len(l.replace('*', ''))
        rv = clamp(shown - used, 0, nl)
        if rv > 0: H.rich_text(cv, l, x, y + 80 + i * 78, 900, 62, '#ffffff', RED, 255, 0.02, 'center', 0.8, reveal=rv)
        used += nl
    yd = y + 80 + len(lines) * 78 + 30
    for k in range(7):
        c, a = ('#ffffff', 90) if k + 1 > n else (('#ffffff', 210) if k + 1 < n else (RED, 255))
        pen.fill(rrect(x - 7 * 34 + k * 68, yd, 52, 8, 4), c, a * clamp((u - 0.1) / 0.15))


def wave_panel(cv, u, rows, title='SHOULDER RADIO', y=0.30 * VH, h=None, playhead=None, x=50, w=900):
    """Waveform panel at full vertical width (engine.hud.waveform_panel)."""
    h = h or 150 + 150 * len(rows)
    H.waveform_panel(cv, x, y, w, h, title, rows, u, playhead=playhead, appear=u)


def loop_icon(cv, u, x=SAFE_CX, y=0.30 * VH, r=90):
    pen = Pen(cv)
    k = ease_out_back(clamp(u / 0.2), 2.0)
    cv.save(); cv.translate(x, y); cv.rotate(u * 220); cv.scale(k, k)
    p = skia.Path(); p.addArc(skia.Rect.MakeLTRB(-r, -r, r, r), 20, 300)
    pen.line(p, 16, '#ffffff', 255)
    ang = math.radians(20)
    hx, hy = math.cos(ang) * r, math.sin(ang) * r
    pen.fill(poly([(hx - 30, hy - 6), (hx + 30, hy - 6), (hx, hy + 34)]), '#ffffff', 255)
    cv.restore()


# ==================================================================================================== frame fx
def rewind_fx(img, k, seed=0, label=True):
    """VHS rewind glitch on an RGB uint8 frame: horizontal band displacement, chroma split, tracking lines, noise and a
    'REWIND' label (drawn by the caller on the overlay pass if label)."""
    if k <= 0: return img
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)
    out = img.copy()
    nb = int(10 + 30 * k)
    for _ in range(nb):
        y0 = int(rng.integers(0, h)); bh = int(rng.integers(4, max(6, int(h * 0.04))))
        dx = int(rng.normal(0, w * 0.08 * k))
        out[y0:y0 + bh] = np.roll(out[y0:y0 + bh], dx, axis=1)
    sh = max(1, int(w * 0.012 * k))
    out[..., 0] = np.roll(out[..., 0], sh, axis=1); out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    noise = rng.integers(0, 255, (h // 4, w // 4), dtype=np.uint8)
    noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_NEAREST)
    out = cv2.addWeighted(out, 1 - 0.12 * k, cv2.merge([noise, noise, noise]), 0.12 * k, 0)
    ty = int((seed * 0.37 % 1.0) * h)
    out[max(0, ty - int(h * 0.02)):ty + int(h * 0.02)] = (out[max(0, ty - int(h * 0.02)):ty + int(h * 0.02)] * 0.4 + 140).astype(np.uint8)
    return out


def rewind_label(cv, u):
    pen = Pen(cv)
    a = 255 if (u * 14) % 1 < 0.7 else 170
    x0, y0 = VW / 2 - 300, 0.22 * VH
    pen.fill(poly([(x0 + 70, y0 - 50), (x0 + 70, y0 + 50), (x0, y0)]), '#ffffff', a)
    pen.fill(poly([(x0 + 140, y0 - 50), (x0 + 140, y0 + 50), (x0 + 70, y0)]), '#ffffff', a)
    outlined(cv, 'REWIND', x0 + 170, y0 + 38, 108, '#ffffff', 0.10, 'left', 0.6, a, 900, 0.06)
