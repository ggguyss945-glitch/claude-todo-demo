"""Characters in the reference look: a tall rounded-box head, small white eyes with dot pupils, thin brows, an L nose,
a small mouth, flat clothes with one shade tone and thin dark outlines. Front-facing, posed with a few parameters.
draw(pen, spec, x, y, h, pose): x = centre, y = feet (ground), h = full height in design px.
"""
import math
from look import *

SKIN = {'light': ('#d9ab8c', '#c29274'), 'mid': ('#c99a76', '#b0835f'), 'olive': ('#c4a07c', '#a98762'), 'old': ('#dcb399', '#c49b82')}

COP = dict(name='cop', skin='mid', hair=('short', '#2b2420'), outfit='police', moustache=None, brows='#2b2420', cap=True, bodycam=True, radio=True)
COP2 = dict(name='cop2', skin='light', hair=('bun', '#5a3a26'), outfit='police', moustache=None, brows='#3a2618', cap=True, female=True, bodycam=False, radio=True)
DOUBLE = dict(name='double', skin='light', hair=('short', '#3a2a20'), outfit='coat', brows='#2a1d16', scar='right', ring='right')
YOU = dict(name='you', skin='light', hair=('short', '#3a2a20'), outfit='hoodie', brows='#2a1d16', scar='left', ring='left')
MUM = dict(name='mum', skin='old', hair=('curly', '#b9b6b2'), outfit='cardigan', brows='#7a706a', glasses=True, female=True)

NEUTRAL = dict(look=(0, 0), blink=0.0, talk=0.0, expr='neutral', arms=('down', 'down'), head=(0, 0), hold=None, turn=0.0)


def pose(**kw):
    p = dict(NEUTRAL); p.update(kw); return p


def talk_mouth(t, rate=7.0, seed=0.0):
    """A talking mouth opening from time t: chunky, irregular, like hand-timed mouth flaps."""
    v = 0.5 + 0.5 * math.sin(t * rate + seed) * math.sin(t * rate * 0.37 + 1.3 + seed)
    return max(0.0, min(1.0, v * 1.4 - 0.15))


def blink_at(t, seed=0.0, every=3.7):
    """Blink for ~0.12 s every few seconds."""
    ph = (t + seed * 1.7) % every
    return 1.0 if ph < 0.12 else 0.0


def draw(pen, spec, x, y, h, p=NEUTRAL, crop=None):
    """Full figure standing on y. Proportions: head = 0.17 h, shoulders at 0.24 h from the top."""
    lw = max(1.6, h * 0.0062)
    pen.lw = lw
    hh = h * 0.17; hw = hh * 0.78               # head height, width
    top = y - h
    hx, hy = x + p['head'][0] * hh, top + hh * 0.55 + p['head'][1] * hh   # head centre
    sk, sks = SKIN[spec['skin']]
    sh_y = top + hh * 1.12                      # shoulder line
    sw = hw * 1.12                              # half shoulder width
    hip = top + h * 0.56
    # ---------------------------------------------------------------- legs and shoes
    leg_c = {'police': '#1c2338', 'coat': '#2b2e36', 'hoodie': '#26282e', 'cardigan': '#4a3f44'}[spec['outfit']]
    for sx in (-1, 1):
        lx = x + sx * hw * 0.32
        leg = rrect(lx - hw * 0.2, hip - 4, hw * 0.4, y - hip - h * 0.02, hw * 0.08)
        pen.shape(leg, leg_c, lw)
        pen.shape(rrect(lx - hw * 0.26, y - h * 0.035, hw * 0.52, h * 0.035, h * 0.012), '#141414', lw)
    # ---------------------------------------------------------------- torso by outfit
    torso = smooth([(x - sw, sh_y + hh * 0.18), (x - sw * 0.85, sh_y), (x, sh_y - hh * 0.04), (x + sw * 0.85, sh_y), (x + sw, sh_y + hh * 0.18),
                    (x + sw * 0.78, hip + h * 0.02), (x - sw * 0.78, hip + h * 0.02)], True, 0.5)
    if spec['outfit'] == 'coat':  # a long coat that falls below the hips
        torso = smooth([(x - sw, sh_y + hh * 0.18), (x - sw * 0.85, sh_y), (x, sh_y - hh * 0.04), (x + sw * 0.85, sh_y), (x + sw, sh_y + hh * 0.18),
                        (x + sw * 0.9, top + h * 0.78), (x - sw * 0.9, top + h * 0.78)], True, 0.5)
    base = {'police': '#26365a', 'coat': '#8a8d93', 'hoodie': '#30333b', 'cardigan': '#8c6f7a'}[spec['outfit']]
    shade = mix(base, '#000000', 0.22)
    # arms behind the torso when hanging, in front when raised (drawn after)
    arm_c = base
    def arm(side, mode, front):
        sx = -1 if side == 0 else 1
        ax, ay = x + sx * sw * 0.9, sh_y + hh * 0.2
        L = h * 0.3
        if mode == 'down': ang = sx * 0.08
        elif mode == 'out': ang = sx * 0.55
        elif mode == 'up': ang = sx * 2.6
        elif mode == 'chest': ang = -sx * 0.9          # hand to the chest (body camera, radio)
        elif mode == 'front': ang = -sx * 0.45          # holding something in front
        elif mode == 'shoulder': ang = sx * 2.9         # hand on the shoulder radio
        elif mode == 'wave': ang = sx * 2.2
        else: ang = sx * 0.08
        if (mode in ('down', 'out')) == front: return None
        ex, ey = ax + math.sin(ang) * L, ay + math.cos(ang) * L
        if mode == 'shoulder': ex, ey = x + sx * sw * 0.55, sh_y + hh * 0.05
        if mode == 'chest': ex, ey = x + sx * hw * 0.25, sh_y + hh * 0.55
        if mode == 'front': ex, ey = x + sx * hw * 0.35, sh_y + hh * 1.35
        w = hw * 0.36
        dx, dy = ex - ax, ey - ay; d = math.hypot(dx, dy) or 1; nx, ny = -dy / d * w / 2, dx / d * w / 2
        sleeve = poly([(ax + nx, ay + ny), (ex + nx, ey + ny), (ex - nx, ey - ny), (ax - nx, ay - ny)])
        pen.shape(union(sleeve, oval(ax, ay, w / 2)), arm_c, lw)
        hand = oval(ex + dx / d * w * 0.3, ey + dy / d * w * 0.3, w * 0.42, w * 0.46)
        pen.shape(hand, sk, lw)
        if spec.get('ring') and ((side == 0 and spec['ring'] == 'left') or (side == 1 and spec['ring'] == 'right')):
            pen.fill(oval(ex + dx / d * w * 0.1, ey + dy / d * w * 0.1, w * 0.16, w * 0.07), '#d9b24a')
        return (ex + dx / d * w * 0.3, ey + dy / d * w * 0.3)
    hands = {}
    for s, m in enumerate(p['arms']):
        r = arm(s, m, False)
        if r: hands[s] = r
    pen.fill(torso, base)
    pen.shade(torso, poly([(x + sw * 0.35, sh_y - 20), (x + sw * 1.2, sh_y - 20), (x + sw * 1.2, y), (x + sw * 0.5, y)]), shade)
    if spec['outfit'] == 'police':
        pen.line(poly([(x, sh_y + hh * 0.05), (x, hip)], False), lw * 0.8, '#141b2c')
        for i in range(4): pen.fill(oval(x + lw * 1.8, sh_y + hh * (0.45 + i * 0.42), lw * 1.1), '#c9cbd4')
        for sx in (-1, 1):  # collar, pocket flaps, shoulder patches
            pen.shape(poly([(x, sh_y + hh * 0.12), (x + sx * hw * 0.42, sh_y - hh * 0.02), (x + sx * hw * 0.38, sh_y + hh * 0.32)]), '#2e4170', lw * 0.8)
            pen.shape(rrect(x + sx * hw * 0.62 - hw * 0.22, sh_y + hh * 0.78, hw * 0.44, hh * 0.18, 3), '#22304f', lw * 0.7)
            pen.shape(oval(x + sx * sw * 0.86, sh_y + hh * 0.42, hw * 0.13, hw * 0.18), '#b8963a', lw * 0.6)
        bx, by = x - hw * 0.62, sh_y + hh * 0.6                     # star badge
        star = [(bx + math.cos(-math.pi / 2 + i * math.pi / 5) * hw * (0.16 if i % 2 == 0 else 0.07),
                 by + math.sin(-math.pi / 2 + i * math.pi / 5) * hw * (0.16 if i % 2 == 0 else 0.07)) for i in range(10)]
        pen.shape(poly(star), '#d9ba55', lw * 0.6)
        pen.shape(rrect(x + hw * 0.38, sh_y + hh * 0.62, hw * 0.48, hh * 0.1, 2), '#cfd0d6', lw * 0.6)
        if spec.get('bodycam'):
            cx_, cy_ = x + hw * 0.08, sh_y + hh * 1.05
            pen.shape(rrect(cx_ - hw * 0.17, cy_ - hh * 0.16, hw * 0.34, hh * 0.32, 4), '#121316', lw * 0.7)
            pen.fill(oval(cx_, cy_ - hh * 0.02, hw * 0.07), '#2b3346')
            pen.fill(oval(cx_ + hw * 0.1, cy_ - hh * 0.1, hw * 0.03), p.get('rec', '#ff3030'))
        if spec.get('radio'):
            rx, ry = x + sw * 0.62, sh_y + hh * 0.1
            pen.shape(rrect(rx - hw * 0.1, ry, hw * 0.2, hh * 0.3, 3), '#151619', lw * 0.7)
            pen.line(smooth([(rx, ry + hh * 0.3), (rx - hw * 0.05, ry + hh * 0.5), (rx + hw * 0.05, ry + hh * 0.7), (rx - hw * 0.1, ry + hh * 0.85)], False), lw * 0.8, '#151619')
        pen.shape(rrect(x - sw * 0.86, hip - hh * 0.12, sw * 1.72, hh * 0.18, 3), '#121316', lw * 0.8)   # duty belt
        pen.shape(rrect(x + sw * 0.5, hip - hh * 0.1, hw * 0.3, hh * 0.42, 3), '#121316', lw * 0.7)
    elif spec['outfit'] == 'coat':
        for sx in (-1, 1):
            pen.shape(poly([(x, sh_y + hh * 0.05), (x + sx * hw * 0.5, sh_y - hh * 0.02), (x + sx * hw * 0.62, sh_y + hh * 0.55), (x + sx * hw * 0.12, sh_y + hh * 1.0)]),
                      mix(base, '#ffffff', 0.08), lw * 0.8)
        pen.fill(poly([(x - hw * 0.12, sh_y + hh * 0.06), (x + hw * 0.12, sh_y + hh * 0.06), (x, sh_y + hh * 0.9)]), '#e6e3dc')
        pen.line(poly([(x + hw * 0.12, sh_y + hh * 1.0), (x + hw * 0.12, top + h * 0.78)], False), lw * 0.8)
        for i in range(3): pen.fill(oval(x + hw * 0.24, sh_y + hh * (1.2 + i * 0.55), lw * 1.3), '#2b2b30')
    elif spec['outfit'] == 'hoodie' and not p.get('back'):
        pen.shape(smooth([(x - hw * 0.62, sh_y - hh * 0.06), (x, sh_y + hh * 0.3), (x + hw * 0.62, sh_y - hh * 0.06), (x, sh_y + hh * 0.12)]), mix(base, '#ffffff', 0.1), lw * 0.8)
        pen.shape(rrect(x - hw * 0.7, sh_y + hh * 1.5, hw * 1.4, hh * 0.6, hw * 0.1), mix(base, '#000000', 0.12), lw * 0.7)
    elif spec['outfit'] == 'cardigan':
        pen.fill(poly([(x - hw * 0.3, sh_y), (x + hw * 0.3, sh_y), (x + hw * 0.2, hip), (x - hw * 0.2, hip)]), '#e8e0d4')
        pen.line(poly([(x - hw * 0.3, sh_y), (x - hw * 0.2, hip)], False), lw * 0.8); pen.line(poly([(x + hw * 0.3, sh_y), (x + hw * 0.2, hip)], False), lw * 0.8)
        for i in range(4): pen.fill(oval(x + hw * 0.36, sh_y + hh * (0.4 + i * 0.4), lw * 1.2), '#d8cbb8')
    if spec['outfit'] == 'hoodie' and p.get('back'):   # the hood hanging down the back
        pen.shape(smooth([(x - hw * 0.55, sh_y - hh * 0.05), (x + hw * 0.55, sh_y - hh * 0.05), (x + hw * 0.4, sh_y + hh * 0.7), (x - hw * 0.4, sh_y + hh * 0.7)], True, 0.7), mix(base, '#000000', 0.15), lw * 0.8)
    pen.line(torso, lw)
    for s, m in enumerate(p['arms']):
        r = arm(s, m, True)
        if r: hands[s] = r
    # ---------------------------------------------------------------- neck and head
    pen.shape(rect(hx - hw * 0.2, hy + hh * 0.38, hw * 0.4, hh * 0.3), sks, lw)
    head(pen, spec, hx, hy, hh, hw, p, lw)
    return hands


def head(pen, spec, hx, hy, hh, hw, p, lw):
    sk, sks = SKIN[spec['skin']]
    turn = p.get('turn', 0.0)                       # -1..1: features slide toward where he looks
    style, hc = spec['hair']
    if style == 'curly' or style == 'bun':          # hair behind the head
        back = oval(hx, hy - hh * 0.08, hw * 0.62, hh * 0.56) if style == 'curly' else oval(hx, hy - hh * 0.12, hw * 0.56, hh * 0.52)
        pen.shape(back, hc, lw)
        if style == 'bun': pen.shape(oval(hx, hy - hh * 0.62, hw * 0.22, hh * 0.14), hc, lw)
    for sx in (-1, 1):
        pen.shape(oval(hx + sx * hw * 0.5, hy + hh * 0.02, hw * 0.12, hh * 0.15), sks, lw)
    face = rrect(hx - hw / 2, hy - hh / 2, hw, hh, hw * 0.42)
    pen.fill(face, sk)
    pen.shade(face, rect(hx + hw * (0.22 - turn * 0.1), hy - hh, hw, hh * 2), sks)
    pen.line(face, lw)
    if p.get('back'):                               # seen from behind: hair covers the head
        pen.shape(inter(face, rect(hx - hw, hy - hh, hw * 2, hh * 1.25)), hc, lw)
        return
    fx = hx + turn * hw * 0.16
    # hair on top
    if style == 'short':
        top = smooth([(hx - hw * 0.52, hy - hh * 0.1), (hx - hw * 0.5, hy - hh * 0.42), (hx - hw * 0.2, hy - hh * 0.58), (hx + hw * 0.25, hy - hh * 0.58),
                      (hx + hw * 0.52, hy - hh * 0.4), (hx + hw * 0.52, hy - hh * 0.12), (hx + hw * 0.4, hy - hh * 0.3), (hx - hw * 0.1, hy - hh * 0.33),
                      (hx - hw * 0.42, hy - hh * 0.26)], True, 0.7)
        pen.shape(top, hc, lw)
    elif style == 'curly':
        for i in range(9):
            a = math.pi * (1.05 + i * 0.11)
            pen.shape(oval(hx + math.cos(a) * hw * 0.45, hy - hh * 0.22 + math.sin(a) * hh * 0.36, hw * 0.16), hc, lw * 0.8)
    elif style == 'bun':
        pen.shape(smooth([(hx - hw * 0.52, hy - hh * 0.05), (hx - hw * 0.45, hy - hh * 0.45), (hx, hy - hh * 0.58), (hx + hw * 0.45, hy - hh * 0.45),
                          (hx + hw * 0.52, hy - hh * 0.05), (hx + hw * 0.3, hy - hh * 0.32), (hx - hw * 0.3, hy - hh * 0.32)], True, 0.7), hc, lw)
    if spec.get('cap'):
        crown = smooth([(hx - hw * 0.62, hy - hh * 0.34), (hx - hw * 0.4, hy - hh * 0.66), (hx + hw * 0.4, hy - hh * 0.66), (hx + hw * 0.62, hy - hh * 0.34),
                        (hx + hw * 0.48, hy - hh * 0.24), (hx - hw * 0.48, hy - hh * 0.24)], True, 0.7)
        pen.shape(crown, '#1c2640', lw)
        pen.shape(rect(hx - hw * 0.5, hy - hh * 0.32, hw, hh * 0.08), '#0f1424', lw * 0.8)
        pen.shape(smooth([(hx - hw * 0.5, hy - hh * 0.24), (hx + hw * 0.5, hy - hh * 0.24), (hx + hw * 0.42, hy - hh * 0.15), (hx - hw * 0.42, hy - hh * 0.15)], True, 0.6), '#0b0c10', lw)
        pen.shape(oval(hx, hy - hh * 0.46, hw * 0.08, hh * 0.07), '#d9ba55', lw * 0.6)
    # eyes
    er = hw * 0.13
    ey = hy - hh * 0.04
    expr = p.get('expr', 'neutral')
    for sx in (-1, 1):
        ex = fx + sx * hw * 0.2
        if p.get('blink', 0) > 0.5 or expr == 'closed':
            pen.line(smooth([(ex - er, ey), (ex, ey + er * 0.25), (ex + er, ey)], False), lw * 1.1)
            continue
        r = er * (1.18 if expr in ('scared', 'shock') else 1.0)
        pen.shape(oval(ex, ey, r), '#f4f1ea', lw)
        lx, ly = p['look']
        px, py = ex + lx * r * 0.45 + turn * r * 0.3, ey + ly * r * 0.45
        pr = r * (0.3 if expr in ('scared', 'shock') else 0.42)
        pen.fill(oval(px, py, pr), '#16110f')
        pen.fill(oval(px - pr * 0.35, py - pr * 0.35, pr * 0.3), '#ffffff', 200)
        if expr == 'tired':
            pen.fill(inter(oval(ex, ey, r), rect(ex - r, ey - r, r * 2, r * 0.8)), sk)
            pen.line(poly([(ex - r, ey - r * 0.2), (ex + r, ey - r * 0.2)], False), lw)
        if spec.get('glasses'):
            pen.line(oval(ex, ey, r * 1.35), lw * 0.9, '#4a3a30')
    if spec.get('glasses'): pen.line(poly([(fx - hw * 0.2 + er * 1.35, ey), (fx + hw * 0.2 - er * 1.35, ey)], False), lw * 0.9, '#4a3a30')
    # brows
    B = {'neutral': (0.0, 0.0), 'worried': (0.12, -0.12), 'scared': (0.18, -0.15), 'shock': (0.2, -0.2), 'angry': (-0.15, 0.12), 'impatient': (-0.1, 0.05),
         'sad': (0.15, -0.1), 'tired': (0.0, 0.0), 'cold': (-0.05, 0.0), 'creepy': (0.06, 0.06), 'closed': (0.0, 0.0)}.get(expr, (0, 0))
    for sx in (-1, 1):
        ex = fx + sx * hw * 0.2
        inner_dy, outer_dy = B
        a = (ex - sx * er * 0.9, ey - er * 1.7 - inner_dy * hh * 0.5)
        b = (ex + sx * er * 1.0, ey - er * 1.75 - outer_dy * hh * 0.5)
        pen.line(poly([a, b], False), lw * 1.3, spec.get('brows', '#2a1d16'))
    # nose: an L
    pen.line(poly([(fx + hw * 0.02, hy + hh * 0.02), (fx + hw * 0.06, hy + hh * 0.14), (fx - hw * 0.04, hy + hh * 0.15)], False), lw * 1.0, mix(sks, '#000000', 0.35))
    # moustache
    if spec.get('moustache'):
        pen.shape(smooth([(fx - hw * 0.2, hy + hh * 0.24), (fx, hy + hh * 0.19), (fx + hw * 0.2, hy + hh * 0.24), (fx + hw * 0.1, hy + hh * 0.26), (fx - hw * 0.1, hy + hh * 0.26)]), spec['moustache'], lw * 0.7)
    # scar beside the mouth
    if spec.get('scar'):
        sxs = -1 if spec['scar'] == 'left' else 1
        pen.line(poly([(fx + sxs * hw * 0.2, hy + hh * 0.24), (fx + sxs * hw * 0.25, hy + hh * 0.31)], False), lw * 0.8, '#9a5a4a')
    # mouth
    my = hy + hh * 0.3
    t_ = p.get('talk', 0.0)
    if expr == 'creepy':
        m = smooth([(fx - hw * 0.3, my - hh * 0.06), (fx, my - hh * 0.02), (fx + hw * 0.3, my - hh * 0.06), (fx + hw * 0.2, my + hh * 0.08), (fx, my + hh * 0.11), (fx - hw * 0.2, my + hh * 0.08)], True, 0.8)
        pen.fill(m, '#1a0c0c'); pen.cv.save(); pen.cv.clipPath(m, doAntiAlias=True)
        pen.fill(rect(fx - hw * 0.4, my - hh * 0.1, hw * 0.8, hh * 0.1), '#f2efe6'); pen.fill(rect(fx - hw * 0.4, my + hh * 0.01, hw * 0.8, hh * 0.1), '#e2ddd0')
        for i in range(-5, 6): pen.line(poly([(fx + i * hw * 0.055, my - hh * 0.1), (fx + i * hw * 0.055, my + hh * 0.12)], False), lw * 0.5, '#8c8478')
        pen.cv.restore(); pen.line(m, lw)
    elif t_ > 0.08:
        pen.shape(oval(fx, my + hh * 0.01, hw * (0.08 + 0.04 * t_), hh * (0.015 + 0.055 * t_)), '#3a1612', lw * 0.8)
    else:
        curve = {'neutral': 0.0, 'worried': -0.02, 'sad': -0.035, 'scared': -0.03, 'shock': 0.0, 'angry': -0.02, 'impatient': -0.012,
                 'tired': -0.01, 'cold': 0.0, 'closed': 0.0}.get(expr, 0.0)
        if expr == 'shock':
            pen.shape(oval(fx, my + hh * 0.01, hw * 0.07, hh * 0.06), '#3a1612', lw * 0.8)
        else:
            pen.line(smooth([(fx - hw * 0.12, my - curve * hh * 0.5), (fx, my + curve * hh), (fx + hw * 0.12, my - curve * hh * 0.5)], False), lw * 1.1, '#3a2418')
    if p.get('tears'):
        for sx in (-1, 1):
            ex = fx + sx * hw * 0.2
            pen.line(poly([(ex + sx * er * 0.3, ey + er), (ex + sx * er * 0.35, ey + er + hh * 0.3 * p['tears'])], False), lw * 2.2, '#9cc8ff', 200)
