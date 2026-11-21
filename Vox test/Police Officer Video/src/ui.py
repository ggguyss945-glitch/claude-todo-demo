"""On-screen evidence in the reference style: rule cards, waveform panels, phone screens, the complaint sheet, countdown, body-cam HUD."""
import math, random
from look import *

RED = '#e3202a'


def rule_card(pen, n, words, t, total=7, icon=None):
    """'RULE' / big number / red rule / the rule typed in word by word / progress dashes. Draw over a dimmed background."""
    cv = pen.cv
    pen.fill(rect(0, 0, DW, DH), '#000000', 150)
    a = int(255 * ease(prog(t, 0.0, 0.35)))
    text(cv, 'R U L E', DW / 2, 330, 600, 24, '#d6d6de', a * 0.9, 0.3)
    s = 1.0 + 0.08 * (1 - ease(prog(t, 0, 0.5)))
    cv.save(); cv.translate(DW / 2, 500); cv.scale(s, s)
    text(cv, f'{n:02d}', 0, 0, 800, 200, '#ffffff', a, 0.0)
    cv.restore()
    w = 420 * ease(prog(t, 0.25, 0.75))
    pen.fill(rrect(DW / 2 - w / 2, 545, w, 5, 2), RED, a)
    # typed text: words appear one by one (0.13 s apart), wrapped to 2-3 lines
    shown = words.split()[:int(max(0, (t - 0.55) / 0.13))]
    lines = wrap(' '.join(shown).upper(), 700, 40, 1100, 0.05)
    for i, l in enumerate(lines): text(cv, l, DW / 2, 620 + i * 54, 700, 40, '#ffffff', 245, 0.05, 'center', 0.8)
    for i in range(total):
        pen.fill(rrect(DW / 2 - total * 30 + i * 60, 800, 46, 5, 2), RED if i == n - 1 else '#5a5a64', a if i == n - 1 else a * 0.6)
    if icon: icon(pen, a)


def panel(pen, x, y, w, h, title, sub=None, a=255):
    pen.fill(rrect(x, y, w, h, 14), '#0b111f', 225 * a / 255); pen.line(rrect(x, y, w, h, 14), 2, '#34446c', 200 * a / 255)
    text(pen.cv, title, x + 26, y + 40, 700, 19, '#8fa6d8', 230 * a / 255, 0.16, 'left')
    if sub: text(pen.cv, sub, x + w - 26, y + 40, 600, 17, '#6a7aa0', 200 * a / 255, 0.12, 'right')
    pen.fill(rect(x + 26, y + 56, w - 52, 1.5), '#34446c', a)


def wave(pen, x, y, w, h, seed, color, progress=1.0, gaps=(), a=255, dense=1.0):
    """A speech waveform: bursts for words, flat for gaps (list of (start, end) fractions)."""
    rnd = random.Random(seed); n = int(w / 5)
    for i in range(n):
        f = i / n
        if f > progress: break
        env = 0.25 + 0.75 * abs(math.sin(f * math.pi * 6 * dense + seed)) * (0.6 + 0.4 * rnd.random())
        if any(g0 <= f <= g1 for g0, g1 in gaps): env = 0.05
        hh = h * env
        pen.fill(rrect(x + i * 5, y - hh / 2, 3, hh, 1.5), color, a)


def radio_playback(pen, t, takes, focus=None):
    """SHOULDER RADIO panel: each take is (label, seed, color, gaps, start time, length)."""
    x, w = 300, 1320
    h = 140 + len(takes) * 150
    y = (DH - h) / 2 - 60
    panel(pen, x, y, w, h, 'SHOULDER RADIO  —  PLAYBACK', 'CH 4')
    for k, (label, seed, colr, gaps, t0, L) in enumerate(takes):
        yy = y + 140 + k * 150
        text(pen.cv, label, x + 26, yy - 46, 600, 16, '#7a88aa', 220, 0.14, 'left')
        p = prog(t, t0, t0 + L)
        wave(pen, x + 26, yy, w - 52, 90, seed, colr, p, gaps, 255 if p > 0 else 90)
        if 0 < p < 1: pen.fill(rect(x + 26 + (w - 52) * p, yy - 55, 3, 110), '#ffffff', 220)
        if focus == k:
            for g0, g1 in gaps:
                pen.line(rrect(x + 26 + (w - 52) * g0 - 8, yy - 60, (w - 52) * (g1 - g0) + 16, 120, 8), 4, RED, 230)
                text(pen.cv, 'PAUSE TOO LONG', x + 26 + (w - 52) * (g0 + g1) / 2, yy + 92, 700, 18, RED, 240, 0.12)


def loop_detect(pen, t, loops_at=(0.0, 2.2), click=True):
    """Mum's voice on the radio repeating: two identical waveforms, the cough marked in the same place, a click before the restart."""
    x, y, w = 300, 250, 1320
    panel(pen, x, y, w, 420, 'INCOMING  —  EMERGENCY CONTACT', 'SIGNAL ▮▮▮▯')
    for k, t0 in enumerate(loops_at):
        yy = y + 160 + k * 160
        p = prog(t, t0, t0 + 2.0)
        wave(pen, x + 26, yy, w - 52, 90, 77, '#7aa0ff', p, ((0.47, 0.52),), 255 if p > 0 else 70)
        cx = x + 26 + (w - 52) * 0.62
        if p > 0.62:
            pen.line(rrect(cx - 30, yy - 58, 60, 116, 8), 4, '#f2b84a', 230)
            text(pen.cv, 'COUGH', cx, yy - 70, 700, 16, '#f2b84a', 230, 0.14)
        if k == 1 and click and p > 0.0:
            pen.fill(rect(x + 26, yy - 70, 4, 140), RED, 230)
            text(pen.cv, 'CLICK', x + 26, yy + 92, 700, 16, RED, 230, 0.14, 'left')


def phone(pen, t, state='calling', name='MUM', timer=0.0, x=300, y=150, s=1.0):
    """A phone held up in a hand: calling / busy / connected / incoming."""
    cv = pen.cv; cv.save(); cv.translate(x, y); cv.scale(s, s)
    palm = smooth([(40, 920), (0, 640), (80, 560), (360, 560), (400, 700), (380, 920)], True, 0.6); pen.shape(palm, '#c9997a', 4)
    ph = rrect(90, 100, 300, 600, 40); pen.shape(ph, '#0e1220', 6); pen.fill(rrect(106, 116, 268, 568, 30), '#141c32')
    cx = 240
    text(cv, name, cx, 250, 700, 34, '#ffffff', 245, 0.04)
    label = {'calling': 'CALLING…', 'busy': 'LINE BUSY', 'connected': f'{int(timer // 60):02d}:{int(timer % 60):02d}', 'incoming': 'INCOMING CALL'}[state]
    text(cv, label, cx, 300, 600, 22, '#ff5a5a' if state == 'busy' else '#cdd6ee', 235, 0.1)
    if state in ('calling', 'connected'):
        for i in range(15):
            hh = 8 + abs(math.sin(i * 1.3 + t * (8 if state == 'connected' else 2))) * (34 if state == 'connected' else 10)
            pen.fill(rrect(150 + i * 12.5, 400 - hh / 2, 7, hh, 3), '#7aa0ff', 230)
    if state == 'busy':
        for i in range(3):
            on = int(t * 2) % 2 == 0
            pen.fill(rrect(160 + i * 60, 390, 40, 14, 6), '#ff5a5a' if on else '#3a2a34')
    pen.fill(oval(cx, 600, 36), RED); pen.line(smooth([(cx - 14, 608), (cx, 592), (cx + 15, 604)], False), 5, '#ffffff')
    pen.shape(smooth([(60, 640), (40, 520), (70, 460), (96, 510), (98, 640)], True, 0.6), '#c9997a', 4)
    for yy in (300, 380, 460, 540): pen.shape(rrect(370, yy, 48, 46, 20), '#c9997a', 4)
    cv.restore()


def complaint(pen, t, focus=None, name_reveal=0.0, verify=0.0):
    """The complaint sheet. focus: 'address' | 'desc' | 'name' | 'sign' | 'verify' highlights a field."""
    cv = pen.cv
    pen.grad(0, 0, DW, DH, '#1c1916', '#100e0c')
    cv.save(); cv.translate(960, 470); cv.rotate(-0.02); cv.scale(0.8, 0.8)
    pg = rect(-430, -520, 860, 1100); pen.shape(pg, '#f2eee4', 4)
    text(cv, 'COMPLAINT — UNAUTHORIZED OCCUPANT', 0, -440, 800, 30, '#1f2a44', 255, 0.04)
    pen.fill(rect(-380, -415, 760, 3), '#1f2a44')
    rows = [('ADDRESS', '144 ELM STREET', 'address'), ('DESCRIPTION', 'MALE, 5\'11", DARK BROWN HAIR', 'desc'), ('', 'GREY HOODIE, DARK TROUSERS', 'desc'),
            ('', 'REFUSES TO LEAVE THE PROPERTY', 'desc'), ('COMPLAINANT', '', 'name')]
    for k, (lab, val, key) in enumerate(rows):
        y = -340 + k * 92
        if lab: text(cv, lab, -380, y, 700, 22, '#5a6278', 255, 0.12, 'left')
        text(cv, val, -380, y + 40, 600, 28, '#20263a', 255, 0.02, 'left')
        if focus == key: pen.line(rrect(-396, y - 30, 792, 84 if lab else 60, 8), 5, RED, 230)
    if name_reveal:
        a = int(255 * ease(name_reveal))
        text(cv, 'THE HOMEOWNER  (YOU)', -380, 70, 800, 30, RED if focus == 'name' else '#20263a', a, 0.02, 'left')
    y = 220
    text(cv, 'SIGNATURE', -380, y, 700, 22, '#5a6278', 255, 0.12, 'left')
    pen.line(smooth([(-380, y + 70), (-320, y + 30), (-270, y + 80), (-200, y + 40), (-150, y + 75), (-90, y + 45), (-40, y + 82)], False), 4, '#1f3a8a')
    if focus == 'sign': pen.line(oval(-70, y + 64, 50, 36), 5, RED, 230)
    pen.line(rect(-380, y + 140, 50, 50), 4, '#20263a')
    text(cv, 'IDENTITY VERIFIED', -310, y + 178, 700, 26, '#20263a', 255, 0.06, 'left')
    if focus == 'verify': pen.line(rrect(-396, y + 124, 520, 82, 8), 5, RED, 230 * (0.6 + 0.4 * abs(math.sin(t * 3))))
    cv.restore()
    pen.glow(960, 300, 900, '#ffd8a0', 40); pen.wash('#0a1430', 35)


def countdown(pen, n, t):
    pen.fill(rect(0, 0, DW, DH), '#000000', 120)
    s = 1.15 - 0.15 * ease(prog(t, 0, 0.25))
    a = 255 * (1 - prog(t, 0.6, 0.95))
    pen.cv.save(); pen.cv.translate(DW / 2, 600); pen.cv.scale(s, s)
    text(pen.cv, str(n), 0, 0, 800, 300, '#ffffff', a, 0.0, 'center', 0.8)
    pen.cv.restore()


def bodycam_hud(pen, t, on=True):
    if not on:
        text(pen.cv, '● CAMERA OFF', 60, 1000, 700, 22, '#8a8a92', 230, 0.12, 'left'); return
    if int(t * 2) % 2 == 0: pen.fill(oval(70, 70, 10), RED)
    text(pen.cv, 'REC', 90, 79, 700, 22, '#ffffff', 230, 0.12, 'left')
    text(pen.cv, 'BODY CAM 0412', DW - 60, 79, 700, 22, '#ffffff', 220, 0.12, 'right')
    text(pen.cv, f'2024-11-03  00:{36 + int(t // 60):02d}:{int(t % 60):02d}', 60, 1020, 600, 22, '#ffffff', 220, 0.08, 'left')


def tag(pen, s, x, y, c='#ffffff', bg='#0b111f', a=255):
    """A small label chip, e.g. GREEN ✕ / BLUE."""
    f = 30
    w = 40 + len(s) * f * 0.72
    pen.fill(rrect(x - w / 2, y - 40, w, 60, 10), bg, 220 * a / 255); pen.line(rrect(x - w / 2, y - 40, w, 60, 10), 2, '#34446c', 200 * a / 255)
    text(pen.cv, s, x, y, 700, f, c, a, 0.06)
