"""The shot list for "The Other Resident", anchored to the narrator's line starts (timeline.json).
Each shot names a scene and its parameters; a shot runs from its line until the next shot's line.
"""
import math
from look import *
import people as P
import places as PL
import ui as UI

LEAD = 0.12          # cut a moment before the word


# ------------------------------------------------------------------ scenes: each draws a full frame and returns the post look
def cam(cv, lt, d, kind='in', amt=0.05, fx=DW / 2, fy=DH / 2):
    k = ease(min(1.0, lt / max(d, 0.01)))
    if kind == 'in': z = 1.0 + amt * k
    elif kind == 'out': z = 1.0 + amt * (1 - k)
    else: z = 1.0
    cv.translate(fx, fy); cv.scale(z, z); cv.translate(-fx, -fy)
    if kind == 'pan': cv.translate(-amt * DW * (k - 0.5), 0)


def car_kw(F, gt, back=True, driver=True, lights=0.0, x=1180, y=None, s=1.0, door_open=False):
    def drv(cx, cy):
        P.draw(F.pen, P.COP2, cx, cy + 240 * s, 260 * s, P.pose(look=(0.6, 0), blink=P.blink_at(gt, 2)))
    def bk(cx, cy):
        P.draw(F.pen, P.DOUBLE, cx, cy + 250 * s, 260 * s, P.pose(head=(0, 0.15), look=(0, 0.8)))
    return dict(x=x, y=y, s=s, facing=1, lights=lights, t=gt, driver=drv if driver else None, backseat=bk if back else None)


class Film:
    def __init__(self, tl):
        self.tl = tl; self.L = tl['lines']; self.dur = tl['duration_en']
        self.pen = None
        self.shots = []
        self._cursor = 0
        build(self)
        self.shots.sort(key=lambda s: s['t'])
        for k, s in enumerate(self.shots):
            s['end'] = self.shots[k + 1]['t'] if k + 1 < len(self.shots) else self.dur + 2.0
        self.rules = [(s['t'], s['p']['n']) for s in self.shots if s['scene'] == 'rule']

    # line lookup by text prefix, moving forward through the script
    def at_line(self, prefix, after=None):
        start = self._cursor if after is None else after
        for i in range(start, len(self.L)):
            if self.L[i]['en'].startswith(prefix):
                self._cursor = i; return i
        for i in range(0, len(self.L)):
            if self.L[i]['en'].startswith(prefix): return i
        raise KeyError(prefix)

    def add(self, prefix, scene, **p):
        i = self.at_line(prefix)
        t = max(0.0, self.L[i]['t'] - LEAD) if self.shots else 0.0
        self.shots.append({'t': t, 'line': i, 'scene': scene, 'p': p})

    def speaking(self, who, gt):
        for l in self.L:
            if l['who'] == who and l['t'] - 0.05 <= gt <= l['end'] + 0.05: return P.talk_mouth(gt, 8.0, hash(who) % 7)
        return 0.0

    def at(self, t):
        lo, hi = 0, len(self.shots) - 1
        while lo < hi:
            m = (lo + hi + 1) // 2
            if self.shots[m]['t'] <= t: lo = m
            else: hi = m - 1
        s = self.shots[lo]
        return _Shot(self, s)

    # ---------------------------------------------------------------- captions and header (drawn after the look)
    def line_at(self, t):
        cur = None
        for l in self.L:
            if l['t'] - 0.05 <= t: cur = l
            else: break
        if cur is None: return None
        nxt = self.L[cur['i'] + 1]['t'] if cur['i'] + 1 < len(self.L) else cur['end'] + 1.0
        if t > max(cur['end'] + 0.6, min(nxt, cur['end'] + 0.6)) and t > cur['end'] + 0.6: return None
        return cur

    def header_text(self, t):
        cur = 'INTRODUCTION'
        for t0, n in self.rules:
            if t >= t0: cur = f'RULE {n} OF 7'
        return cur

    def chunks(self, l):
        """Split a long line into caption chunks of at most ~40 characters, breaking after punctuation where possible."""
        words = l['en'].split(); out, cur = [], ''
        for w in words:
            if len(cur) + len(w) + 1 > 40 and cur: out.append(cur); cur = w
            else: cur = (cur + ' ' + w).strip()
            if cur.endswith((',', '.', '?', '!')) and len(cur) > 22: out.append(cur); cur = ''
        if cur: out.append(cur)
        return out

    def chunk_at(self, l, t):
        ch = self.chunks(l)
        if len(ch) == 1: return 0, ch
        total = sum(len(c) for c in ch); acc = 0; span = max(0.3, l['end'] - l['t'])
        for k, c in enumerate(ch):
            if t < l['t'] + span * (acc + len(c)) / total or k == len(ch) - 1: return k, ch
            acc += len(c)

    def overlay_key(self, t):
        l = self.line_at(t); s = self.at(t).s
        k = self.chunk_at(l, t)[0] if l else -1
        return (l['i'] if l else -1, k, self.header_text(t), s['scene'] == 'rule')

    def overlay(self, cv, t):
        s = self.at(t).s
        header(cv, self.header_text(t), '12:36 AM')
        if s['scene'] == 'rule': return                # the rule card carries its own text
        l = self.line_at(t)
        if not l or not l.get('found_en', True): return
        k, ch = self.chunk_at(l, t)
        txt = ch[k]
        if l['who'] != 'N':
            if k == 0: txt = '“' + txt
            if k == len(ch) - 1: txt = txt + '”'
        caption(cv, txt)


class _Shot:
    def __init__(self, film, s): self.f, self.s = film, s

    def render(self, cv, gt):
        F = self.f; F.pen = Pen(cv)
        lt, d = gt - self.s['t'], self.s['end'] - self.s['t']
        fn = SCENES[self.s['scene']]
        cv.save()
        look_ = fn(F, F.pen, lt, d, gt, **self.s['p']) or {}
        cv.restore()
        return look_


# ------------------------------------------------------------------ scene implementations
def s_black(F, pen, lt, d, gt): pen.fill(rect(0, 0, DW, DH), '#000000'); return {'vignette': 0.0, 'grain': 3}


def s_peep(F, pen, lt, d, gt, who=('cop',), expr='neutral', closer=0.0, turn=0.0, arms=None, car=True, lights=0.0, zoom=0.06, look=(0, 0.05),
           chips=(), walk=None, bag=False, cop_expr=None, dbl_expr=None, tint=None, carlook=False):
    cam(pen.cv, lt, d, 'in', zoom)
    PL.street(pen, 560, car=car_kw(F, gt, lights=lights, x=1250, y=870, s=0.75) if car else None)
    PL.porch_frame(pen)
    cast = {'cop': P.COP, 'double': P.DOUBLE, 'cop2': P.COP2}
    n = len(who)
    xs = {1: [960], 2: [820, 1110], 3: [700, 960, 1220]}[n]
    for k, w in enumerate(who):
        spec = cast[w]
        h = (1950 if n == 1 else 1650 if n == 2 else 1450) * (1 + 0.16 * closer)
        x = xs[k]
        ex = expr if n == 1 else ((cop_expr or 'neutral') if w == 'cop' else (dbl_expr or 'neutral') if w == 'double' else 'cold')
        lk = (turn * -1.0, 0.0) if (turn and w == 'cop') else look
        if walk and w == walk[0]:   # walking up the path toward the door
            k2 = ease(prog(lt, 0, walk[1]))
            h = lerp(520, 1900, k2); x = lerp(1260, 960, k2)
        a = arms or ('down', 'down')
        P.draw(pen, spec, x, 470 + h * (1 - 0.17 * 0.55), h, P.pose(expr=ex, look=lk, turn=-turn if w == 'cop' else 0.0, talk=F.speaking({'cop': 'O', 'double': 'D', 'cop2': 'F'}[w], gt),
                                                         blink=P.blink_at(gt, k + 1), arms=a if w == 'cop' else (('front', 'down') if (bag and w == 'cop2') else ('down', 'down'))))
        if bag and w == 'cop2':
            bx, by = x - h * 0.06, 470 + h * (1 - 0.0935) - h * 0.45
            pen.fill(rrect(bx - 70, by - 50, 140, 150, 12), '#dfe8f0', 90); pen.line(rrect(bx - 70, by - 50, 140, 150, 12), 3, '#ffffff', 160)
            pen.fill(oval(bx + 30, by + 60, 14), '#ff8a1e')
    for c_ in chips:
        UI.tag(pen, c_[0], c_[1], c_[2], c_[3] if len(c_) > 3 else '#ffffff')
    return {'lens': 'peephole', 'vignette': 0.35, 'tint': tint}


def s_house(F, pen, lt, d, gt, cop=True, lights=0.0, both=False, three=False, leaving=0.0, dbl_walk=None, cop2_out=False, upstairs=False, neighbour_dark=False):
    cam(pen.cv, lt, d, 'in', 0.05, 960, 520)
    PL.sky(pen, 640, seed=4)
    PL.bare_tree(pen, 160, 700, 600, 3); PL.bare_tree(pen, 1760, 700, 520, 8)
    pen.fill(rect(0, 640, DW, 440), '#141c26')
    if neighbour_dark: PL.house(pen, -260, 700, 420, 280, '#232a3e', '#141a28', '#3a2a20', (False, False, False), porch_lamp=False)
    d_ = PL.house(pen, 560, 760, 800, 360, '#2a3550', '#141a2a', '#5a3a28', (False, upstairs, True), porch_lamp=True, number='144')
    pen.fill(poly([(880, 1080), (930, 760), (990, 760), (1040, 1080)]), '#3a404c')
    pen.fill(rect(0, 950, DW, 130), '#1a202b')
    if cop: P.draw(pen, P.COP, d_[0] + d_[2] + 40, 772, 230, P.pose(arms=('down', 'down'), blink=P.blink_at(gt, 1)))
    if both: P.draw(pen, P.DOUBLE, d_[0] - 40, 772, 220, P.pose(blink=P.blink_at(gt, 2)))
    if three: P.draw(pen, P.COP2, d_[0] + d_[2] + 110, 772, 215, P.pose(arms=('front', 'down')))
    if dbl_walk is not None:
        k = ease(prog(lt, 0, dbl_walk)); P.draw(pen, P.DOUBLE, lerp(1400, d_[0] + d_[2] / 2, k), lerp(1000, 772, k), lerp(270, 220, k), P.pose())
    cx = lerp(1450, -500, ease(prog(lt, 0.2, 0.2 + max(1.0, d * 0.8)))) if leaving else 1450
    kw = car_kw(F, gt, lights=lights, x=cx, y=1060, s=0.9, driver=not cop2_out)
    PL.patrol_car(pen, **kw)
    if cop2_out: P.draw(pen, P.COP2, 1700, 1050, 300, P.pose(arms=('front', 'down')))
    return {'vignette': 0.7, 'grain': 6}


def s_hall(F, pen, lt, d, gt, you=True, coat=True, red=0.0, blue=0.0, shake=0.0, phone=False, lean=0.0, dark=0.0, zoom=0.05, flash=False):
    sh = 0.0
    if shake:   # three knocks: the frame jolts
        for kt in (0.25, 0.65, 1.05):
            if 0 <= lt - kt < 0.12: sh = 6 * math.sin((lt - kt) * 90)
    pen.cv.translate(sh, 0)
    cam(pen.cv, lt, d, 'in', zoom, 960, 480)
    r = red * (0.5 + 0.5 * math.sin(gt * 6)) if flash else red
    b = blue * (0.5 - 0.5 * math.sin(gt * 6)) if flash else blue
    PL.hallway(pen, coat=coat, red=r, blue=b)
    if you:
        P.draw(pen, P.YOU, 520 + lean * 120, 1600, 1500, P.pose(back=True, arms=('down', 'chest' if phone else 'down')))
    if dark: pen.fill(rect(-200, -200, DW + 400, DH + 400), '#000000', 255 * dark)
    return {'vignette': 0.8, 'grain': 7}


def s_cop_cu(F, pen, lt, d, gt, expr='neutral', focus='face', look=(0, 0.05), rec=True, hand=None, pen_up=False):
    fx, fy = {'face': (960, 450), 'badge': (750, 960), 'cam': (985, 1110), 'radio': (1200, 790)}[focus]
    z = {'face': 0.06, 'badge': 0.08, 'cam': 0.08, 'radio': 0.08}[focus]
    if focus != 'face':
        pen.cv.translate(fx, fy); pen.cv.scale(1.9, 1.9); pen.cv.translate(-fx, -fy)
    cam(pen.cv, lt, d, 'in', z, fx, fy)
    PL.street(pen, 560, car=None, trees=False)
    pen.fill(rect(0, 0, DW, DH), '#05070c', 120)
    pen.glow(960, -100, 900, '#ffd38a', 120)
    arms = ('down', 'chest') if hand == 'cam' else (('down', 'shoulder') if hand == 'radio' else (('down', 'front') if pen_up else ('down', 'down')))
    P.draw(pen, P.COP, 960, 2807, 2600, P.pose(expr=expr, look=look, talk=F.speaking('O', gt), blink=P.blink_at(gt, 1), arms=arms, rec='#ff3030' if rec else '#3a3a3a'))
    return {'vignette': 0.8, 'grain': 6, 'lens': 'lens'}


def s_double_cu(F, pen, lt, d, gt, expr='impatient', circle=None, ring_hand=None, tears=0.0, scar=None, talk_who='D', creepy=False):
    cam(pen.cv, lt, d, 'in', 0.07, 960, 430)
    PL.street(pen, 560, car=None, trees=False)
    pen.fill(rect(0, 0, DW, DH), '#05070c', 130)
    pen.glow(960, -100, 900, '#ffd38a', 130)
    spec = dict(P.DOUBLE)
    if scar: spec['scar'] = scar
    arms = ('down', 'down')
    if ring_hand: arms = ('up', 'down') if ring_hand == 'left' else ('down', 'up')
    P.draw(pen, spec, 960, 2807, 2600, P.pose(expr='creepy' if creepy else expr, look=(0, 0.05), talk=F.speaking(talk_who, gt), tears=tears, blink=P.blink_at(gt, 3), arms=arms))
    a = ease(prog(lt, 0.3, 0.8))
    if circle == 'scar':
        sx = 1 if spec['scar'] == 'right' else -1
        pen.line(oval(960 + sx * 75, 590, 70, 55), 7, UI.RED, 230 * a)
    if circle == 'ring':
        hx = 1350 if ring_hand == 'right' else 570
        pen.line(oval(hx, 150, 110), 7, UI.RED, 230 * a)
    return {'vignette': 0.8, 'grain': 6, 'lens': 'lens'}


def s_car(F, pen, lt, d, gt, man='lowered', card=None, hand=None, look_up=0.0, lips=False, red=0.0, zoom=0.05, focus=(960, 480)):
    cam(pen.cv, lt, d, 'in', zoom, *focus)
    c = {'up': ease(prog(lt, 0.1, 1.2)), 'held': 1.0, 'down': 1 - ease(prog(lt, 0.1, 1.0))}.get(card, 0.0)
    h = {'up': ease(prog(lt, 0.1, 1.0)), 'held': 1.0}.get(hand, 0.0)
    lu = ease(prog(lt, 0.2, 1.5)) if look_up == 'anim' else look_up
    PL.car_window(pen, man, gt, card=c, hand=h, look_up=lu, lips=P.talk_mouth(gt, 9) if lips else 0.0)
    if red: pen.wash('#ff1e2a', 50 * red)
    return {'vignette': 0.8, 'grain': 7, 'lens': 'lens'}


def s_hands(F, pen, lt, d, gt, zoom=0.06): cam(pen.cv, lt, d, 'in', zoom, 1000, 650); PL.hands_lap(pen, gt); return {'vignette': 0.85, 'grain': 7}


def s_card(F, pen, lt, d, gt, zoom=0.05, focus=(1200, 340)):
    cam(pen.cv, lt, d, 'in', zoom, *focus); PL.holding_card(pen, gt); return {'vignette': 0.8, 'grain': 6}


def s_lock(F, pen, lt, d, gt, hand=None, key=None, red=0.0):
    cam(pen.cv, lt, d, 'in', 0.05)
    hv = {'reach': ease(prog(lt, 0.1, max(0.5, d * 0.8))) * 0.85, 'hold': 0.85, 'hover': 0.7}.get(hand, 0.0)
    kv = {'in': ease(prog(lt, 0.1, max(0.5, d * 0.7))) * 0.9, 'hold': 0.9, 'turn': 1.0}.get(key, 0.0)
    PL.lock_close(pen, hand=hv, key=kv)
    if key == 'turn':
        pen.cv.save(); pen.cv.translate(960, 450); pen.cv.rotate(-1.4 * ease(prog(lt, 0.4, 1.2))); pen.cv.translate(-960, -450)
        pen.shape(rrect(935, 410, 50, 140, 12), '#e0c060', 4); pen.cv.restore()
    if red: pen.wash('#ff1e2a', 60 * red)
    return {'vignette': 0.8, 'grain': 7}


def s_rule(F, pen, lt, d, gt, n=1, text_=''):
    PL.hallway(pen, coat=True)
    UI.rule_card(pen, n, text_, lt)
    return {'vignette': 0.85, 'grain': 6, 'soft': 1.6}


def s_radio(F, pen, lt, d, gt, takes=(), focus=None):
    PL.hallway(pen, coat=True); pen.fill(rect(0, 0, DW, DH), '#000000', 140)
    UI.radio_playback(pen, lt, takes, focus)
    return {'vignette': 0.75, 'grain': 6}


def s_loop(F, pen, lt, d, gt, loops=(0.2, 99.0), click=False):
    PL.hallway(pen, coat=True); pen.fill(rect(0, 0, DW, DH), '#000000', 140)
    UI.loop_detect(pen, lt, loops, click)
    return {'vignette': 0.75, 'grain': 6}


def s_phone(F, pen, lt, d, gt, state='calling', timer0=0.0, room='hall'):
    if room == 'hall': PL.hallway(pen, coat=True, red=0.0)
    else: PL.mother_room(pen, gt)
    pen.fill(rect(0, 0, DW, DH), '#000000', 110)
    UI.phone(pen, gt, state, 'MUM', timer0 + lt, x=700, y=140)
    return {'vignette': 0.8, 'grain': 6, 'soft': 0.9}


def s_mailslot(F, pen, lt, d, gt, paper=False):
    cam(pen.cv, lt, d, 'in', 0.06)
    pen.fill(rect(0, 0, DW, DH), '#5d3c28')
    for i in range(14): pen.seg((0, 30 + i * 80), (DW, 30 + i * 80 + 6), 2, '#4e3222', 120)
    flap = ease(prog(lt, 0.1, 0.5)) * (1 if paper else 0.4)
    pen.shape(rrect(560, 380, 800, 200, 16), '#b8933e', 6); pen.fill(rect(600, 450, 720, 60), '#120c06')
    pen.glow(960, 480, 500, '#ffd38a', 40)
    if paper:
        k = ease(prog(lt, 0.3, max(1.0, d * 0.7)))
        pen.shape(poly([(640, 470), (1280, 470), (1300, 470 + 520 * k), (620, 470 + 520 * k)]), '#f2eee4', 4)
        for i in range(int(6 * k)): pen.fill(rect(680, 520 + i * 70, 500 - i * 30, 12), '#a0a6b2')
    pen.shape(rrect(600, 440 - 60 * flap, 720, 40, 8), '#c9a24a', 4)
    return {'vignette': 0.8, 'grain': 7}


def s_complaint(F, pen, lt, d, gt, focus=None, name=0.0, zoom=0.04):
    cam(pen.cv, lt, d, 'in', zoom)
    nv = ease(prog(lt, 0.4, 1.0)) if name == 'anim' else name
    UI.complaint(pen, gt, focus, nv)
    return {'vignette': 0.75, 'grain': 6}


def s_cuff(F, pen, lt, d, gt):
    cam(pen.cv, lt, d, 'in', 0.08, 960, 600)
    pen.grad(0, 0, DW, DH, '#121826', '#0a0e16'); pen.glow(960, -200, 1000, '#ffd38a', 100)
    sl = poly([(300, 200), (1300, 380), (1260, 760), (260, 640)]); pen.shape(sl, '#8a8d93', 6); pen.shade(sl, rect(0, 560, DW, 400), '#74777e')
    pen.shape(poly([(1240, 360), (1330, 380), (1290, 780), (1200, 760)]), '#7a7d84', 6)
    sw = 30 * math.sin(gt * 1.3)
    pen.line(smooth([(1300, 620), (1360 + sw, 700), (1340 + sw, 820), (1380 + sw * 1.4, 900)], False), 4, '#5a5d63')
    pen.shape(oval(1450, 640, 120, 100), '#d9ab8c', 5)
    return {'vignette': 0.8, 'grain': 7, 'lens': 'lens'}


def s_bag(F, pen, lt, d, gt, zoom=0.06, focus=(960, 540)):
    cam(pen.cv, lt, d, 'in', zoom, *focus)
    pen.grad(0, 0, DW, DH, '#121826', '#0a0e16'); pen.glow(960, -200, 1000, '#ffd38a', 100)
    bag = rrect(520, 160, 880, 820, 40)
    pen.shape(rrect(620, 330, 360, 240, 20), '#5a3a26', 5); pen.line(rrect(640, 350, 320, 200, 14), 3, '#3a2418')
    pen.shape(rrect(1020, 300, 220, 400, 26), '#16181e', 5); pen.fill(rrect(1040, 330, 180, 330, 16), '#22283a')
    for k, x in enumerate((760, 820, 880)): pen.shape(rrect(x, 640, 40, 160, 12), '#b9bcc4', 4)
    pen.shape(oval(820, 640, 50), '#b9bcc4', 4)
    pen.shape(rrect(900, 720, 160, 80, 30), '#ff7a12', 5); pen.fill(oval(940, 760, 18), '#c85a00')
    pen.fill(bag, '#e8f2ff', 70); pen.line(bag, 5, '#ffffff', 180)
    pen.fill(rrect(560, 200, 120, 700, 30), '#ffffff', 40)
    return {'vignette': 0.8, 'grain': 6, 'lens': 'lens'}


def s_badge(F, pen, lt, d, gt):
    cam(pen.cv, lt, d, 'in', 0.07)
    pen.fill(rect(0, 0, DW, DH), '#26365a'); pen.shade(rect(0, 0, DW, DH), rect(1200, 0, 800, DH), '#1d2a46')
    star = [(960 + math.cos(-math.pi / 2 + i * math.pi / 5) * (360 if i % 2 == 0 else 160), 520 + math.sin(-math.pi / 2 + i * math.pi / 5) * (360 if i % 2 == 0 else 160)) for i in range(10)]
    pen.shape(poly(star), '#d9ba55', 8); pen.fill(oval(960, 520, 120), '#b8963a'); text(pen.cv, '0412', 960, 545, 800, 70, '#6a4f12', 255, 0.06)
    pen.glow(800, 200, 900, '#ffd38a', 70)
    return {'vignette': 0.8, 'grain': 6}


def s_simple(F, pen, lt, d, gt, kind='kitchen', zoom=0.05, chip=None):
    cam(pen.cv, lt, d, 'in', zoom)
    {'kitchen': PL.kitchen, 'photo': lambda p: PL.photograph(p, gt), 'grip': lambda p: PL.table_grip(p, gt),
     'hook': lambda p: PL.coat_hook(p, True), 'hookfull': lambda p: PL.coat_hook(p, False)}[kind](pen)
    if chip: UI.tag(pen, chip[0], chip[1], chip[2], chip[3] if len(chip) > 3 else '#ffffff')
    return {'vignette': 0.8, 'grain': 6}


def s_chips(F, pen, lt, d, gt, items=()):
    PL.hallway(pen); pen.fill(rect(0, 0, DW, DH), '#000000', 170)
    for k, s in enumerate(items):
        a = ease(prog(lt, k * 0.7, k * 0.7 + 0.3))
        if a > 0: UI.tag(pen, s, 960, 380 + k * 120, '#ffffff', '#0b111f', 255 * a)
    return {'vignette': 0.8, 'grain': 6}


def s_countdown(F, pen, lt, d, gt, start=10, step=0.42):
    PL.hallway(pen, coat=True, red=0.2)
    n = max(0, start - int(lt / step))
    UI.countdown(pen, n, (lt % step) / step * 1.0)
    return {'vignette': 0.85, 'grain': 7}


def s_mum_room(F, pen, lt, d, gt, tv=True, curtain=0.0, expr='worried', tears=0.0, anim_curtain=False, look=(0.6, 0)):
    cam(pen.cv, lt, d, 'in', 0.05, 960, 420)
    c = ease(prog(lt, 0.2, 1.4)) if anim_curtain else curtain
    PL.mother_room(pen, gt, tv=tv, curtain=c, expr=expr, tears=tears, look=look)
    return {'vignette': 0.8, 'grain': 6}


def s_mum_cu(F, pen, lt, d, gt, expr='sad', tears=1.0):
    cam(pen.cv, lt, d, 'in', 0.07, 960, 420)
    pen.grad(0, 0, DW, DH, '#2e2630', '#1c171d'); pen.glow(1300, 200, 900, '#ffcb7a', 60)
    P.draw(pen, P.MUM, 960, 2807, 2600, P.pose(expr=expr, tears=tears, talk=F.speaking('M', gt), blink=P.blink_at(gt, 4), arms=('down', 'chest')))
    pen.shape(rrect(1180, 600, 110, 230, 18), '#16181e', 5)
    return {'vignette': 0.8, 'grain': 6, 'lens': 'lens'}


def s_mum_ext(F, pen, lt, d, gt, knock=False, curtain=0.0, people=True):
    cam(pen.cv, lt, d, 'in', 0.05, 960, 600)
    PL.mother_exterior(pen, gt, knock=knock, people=people, curtain=curtain)
    return {'vignette': 0.8, 'grain': 6}


SCENES = {k[2:]: v for k, v in globals().items() if k.startswith('s_')}
SCENES['house'] = s_house


# ------------------------------------------------------------------ the film, line by line
def build(F):
    A = F.add
    I_LIVE = ('TAKE 1  —  12:36:51', 11, '#7aa0ff', (), 0.2, 1.4)
    # cold open
    A("If a police officer ever knocks", 'peep', zoom=0.08)
    A("Especially if the house", 'house', cop=True)
    A("Keep your identification inside.", 'card')
    A("Be careful what you say.", 'cop_cu', expr='neutral', look=(0, 0.1))
    A("And if the officer asks you to prove", 'car', man='lowered', zoom=0.08)
    A("It's 12:36 in the morning", 'hall', shake=1.0, zoom=0.04)
    A("Through the peephole, you see", 'peep', zoom=0.08)
    A("His uniform looks ordinary.", 'cop_cu', expr='neutral')
    A("His badge has a number.", 'badge')
    A("There's a patrol car at the curb", 'house', cop=False)
    A("Sorry to disturb you,", 'peep', closer=0.1)
    A("You tell him you live here.", 'hall', lean=0.3)
    A("He touches the camera on his chest.", 'cop_cu', focus='cam', hand='cam')
    A("Could you say that again?", 'peep', closer=0.15)
    A("You repeat yourself, a little louder.", 'hall', lean=0.5)
    A("He nods, then looks toward the car.", 'peep', turn=0.8, closer=0.15)
    A("That's what the other gentleman said.", 'peep', closer=0.2)
    A("Only then do you notice someone", 'house', cop=True, upstairs=False)
    A("His head is lowered.", 'car', man='lowered')
    A("His hands are folded in his lap.", 'hands')
    A("It's something you do when you're nervous.", 'hands', zoom=0.12)
    A("The officer moves closer to your door.", 'peep', closer=0.35)
    A("We just need to establish", 'peep', closer=0.45, expr='cold')
    A("If this happens, there are seven rules", 'hall', zoom=0.08)
    A("And the fourth one explains", 'house', cop=True)
    # rule 1
    A("Rule number one.", 'rule', n=1, text_="Keep your identification on your side of the door.")
    A("The officer will ask for your driver's license.", 'peep', closer=0.3)
    A("He'll suggest sliding it through the mail slot.", 'mailslot')
    A("It will sound reasonable.", 'hall')
    A("Keep the card in your hand.", 'card', zoom=0.1, focus=(980, 470))
    A("When you refuse, he won't become angry.", 'peep', closer=0.3)
    A("He'll simply turn toward the patrol car", 'peep', turn=0.8, arms=('down', 'out'), closer=0.3)
    A("The man in the back seat will raise something", 'car', man='raised', card='up')
    A("It's another driver's license.", 'car', man='raised', card='held', zoom=0.08, focus=(1180, 470))
    A("You can't see the photograph, but you recognize", 'car', man='raised', card='held', zoom=0.25, focus=(1340, 380))
    A("Years ago, you accidentally caught yours", 'card', zoom=0.12, focus=(1240, 300))
    A("The card outside has the same missing piece.", 'car', man='raised', card='held', zoom=0.3, focus=(1340, 380), red=0.4)
    A("You look down at the one you're holding.", 'card', zoom=0.2, focus=(1240, 300))
    A("For a moment, you'll feel an overwhelming need", 'lock', hand='reach')
    A("The officer seems to know.", 'peep', closer=0.5, look=(0, 0.0))
    A("Bring yours out,", 'peep', closer=0.5)
    A("Then the man in the car lowers his card.", 'car', man='raised', card='down')
    A("He keeps his hand raised against the glass.", 'car', man='raised', hand='up')
    A("His fingers are spread exactly like yours.", 'car', man='raised', hand='held', zoom=0.15, focus=(1250, 420), red=0.5)
    # rule 2
    A("Rule number two.", 'rule', n=2, text_="If the officer asks you to repeat something, don't give him a second recording.")
    A("He'll explain that his camera isn't picking up", 'cop_cu', focus='cam')
    A("Just tell me your full name", 'peep', closer=0.4)
    A("Stay quiet.", 'hall', zoom=0.1)
    A("He'll try an easier question.", 'peep', closer=0.4)
    A("Are you here alone?", 'peep', closer=0.45)
    A("Then another.", 'hall')
    A("Do you understand why we're here?", 'peep', closer=0.5, expr='cold')
    A("Eventually, his radio will crackle.", 'cop_cu', focus='radio')
    A("You'll hear your own voice coming through it.", 'radio', takes=(I_LIVE,))
    A("It's the sentence you said", 'radio', takes=((I_LIVE[0], 11, '#7aa0ff', (), -5, 1.4),))
    A("Then it plays again.", 'radio', takes=((I_LIVE[0], 11, '#7aa0ff', (), -5, 1.4), ('TAKE 2', 11, '#ff6a6a', ((0.18, 0.42),), 0.3, 2.0)))
    A("This time, something is wrong.", 'radio', takes=((I_LIVE[0], 11, '#7aa0ff', (), -5, 1.4), ('TAKE 2', 11, '#ff6a6a', ((0.18, 0.42),), -5, 2.0)), focus=1)
    A("Through the peephole, you'll see the man in the car", 'car', man='raised', lips=True, zoom=0.1)
    A("The officer presses a button on his radio.", 'cop_cu', focus='radio', hand='radio')
    A("Again,", 'peep', closer=0.5)
    A("Your voice repeats the sentence.", 'radio', takes=((I_LIVE[0], 11, '#7aa0ff', (), -5, 1.4), ('TAKE 2', 11, '#ff6a6a', ((0.18, 0.42),), -5, 2.0), ('TAKE 3', 11, '#7aa0ff', (), 0.3, 1.4)))
    A("This time, it sounds right.", 'radio', takes=((I_LIVE[0], 11, '#7aa0ff', (), -5, 1.4), ('TAKE 3  —  MATCH', 11, '#5ad08a', (), -5, 1.4)))
    A("The officer looks back at your door.", 'peep', closer=0.55, look=(0, 0.0))
    A("Good. Now your name.", 'cop_cu', expr='cold')
    # rule 3
    A("Rule number three.", 'rule', n=3, text_="If you hear someone you love on the police radio, don't speak to them through it.")
    A("After a while, another voice will come through", 'cop_cu', focus='radio')
    A("It's your mother.", 'simple', kind='photo')
    A("She sounds upset.", 'loop', loops=(0.2, 99.0))
    A("You'll recognize everything.", 'hall', lean=0.4)
    A("The small cough she never quite", 'loop', loops=(-5, 99.0))
    A("Your hand will move toward the lock.", 'lock', hand='reach')
    A("Keep it there without turning it.", 'lock', hand='hold')
    A("The officer will say he's been speaking", 'peep', closer=0.5)
    A("She can explain,", 'peep', closer=0.5, arms=('down', 'shoulder'))
    A("He lifts the radio toward the door.", 'peep', closer=0.6, arms=('down', 'front'))
    A("Your mother says your childhood nickname.", 'loop', loops=(0.2, 99.0))
    A("Then she says it again.", 'loop', loops=(-5, 0.2))
    A("The second time, the cough comes", 'loop', loops=(-5, -5))
    A("You'll hear a quiet click", 'loop', loops=(-5, -5), click=True)
    A("The officer lowers the radio quickly.", 'peep', closer=0.5, arms=('down', 'down'))
    A("Poor reception.", 'cop_cu', expr='cold')
    A("Try calling her yourself.", 'phone', state='calling')
    A("Her line will be busy.", 'phone', state='busy')
    A("Keep trying when you can.", 'phone', state='busy')
    A("Don't use the radio, even if", 'peep', closer=0.55, arms=('down', 'front'))
    # rule 4
    A("Rule number four.", 'rule', n=4, text_="If he shows you a complaint, read the name of the person who made it.")
    A("Eventually, the officer will slide a sheet", 'mailslot', paper=True)
    A("Perhaps this will clear things up.", 'peep', closer=0.5)
    A("At the top is your address.", 'complaint', focus='address')
    A("Underneath is a description", 'complaint', focus='desc')
    A("You read it twice.", 'complaint', zoom=0.02)
    A("Then you look at the complainant's name.", 'complaint', focus='name')
    A("It's yours.", 'complaint', focus='name', name='anim', zoom=0.1)
    A("So is the signature at the bottom", 'complaint', focus='sign', name=1.0)
    A("Outside, a car door opens.", 'house', cop=True, dbl_walk=6.0)
    A("The man from the back seat walks up your path.", 'peep', who=('double',), walk=('double', 3.5), car=True)
    A("He's wearing your gray coat.", 'peep', who=('double',), closer=0.1)
    A("You can see the loose thread", 'cuff')
    A("When he steps under the porch light", 'peep', who=('double',), closer=0.4, expr='impatient')
    A("It's almost yours.", 'double_cu', expr='neutral')
    A("The small scar beside his mouth", 'double_cu', expr='neutral', circle='scar')
    A("His wedding ring sits on the wrong hand.", 'double_cu', expr='neutral', ring_hand='right', circle='ring')
    A("And he's watching the door", 'double_cu', expr='impatient')
    A("That's him,", 'peep', who=('cop', 'double'), dbl_expr='impatient')
    A("You look down at the complaint again.", 'complaint', name=1.0)
    A("The space marked IDENTITY VERIFIED", 'complaint', focus='verify', name=1.0, zoom=0.08)
    A("The officer takes a pen from his pocket.", 'cop_cu', pen_up=True)
    A("This would be much easier,", 'peep', closer=0.55, arms=('down', 'front'))
    # rule 5
    A("Rule number five.", 'rule', n=5, text_="Don't correct anything the other man gets wrong.")
    A("The officer will suggest asking you both", 'peep', who=('cop', 'double'))
    A("The man outside agrees immediately.", 'peep', who=('cop', 'double'), dbl_expr='neutral')
    A("What color are the kitchen tiles?", 'peep', who=('cop', 'double'), chips=(('KITCHEN TILES?', 960, 160),))
    A("Green,", 'peep', who=('cop', 'double'), chips=(('KITCHEN TILES?', 960, 160), ('GREEN', 1110, 300, '#7ad07a')))
    A("Your kitchen tiles are blue.", 'simple', kind='kitchen', chip=('BLUE', 960, 140, '#8ab4ff'))
    A("You almost say it.", 'hall', lean=0.4, zoom=0.08)
    A("The man outside stops watching the officer.", 'peep', who=('cop', 'double'), dbl_expr='cold')
    A("Now he's watching the door.", 'double_cu', expr='cold')
    A("Waiting.", 'double_cu', expr='cold')
    A("The next question will be more personal.", 'peep', who=('cop', 'double'))
    A("The name of your first pet.", 'chips', items=('FIRST PET?', 'SCHOOL?', 'WHAT DOES MUM CALL YOU?'))
    A("Sometimes the man will answer correctly.", 'peep', who=('cop', 'double'), dbl_expr='neutral')
    A("Don't.", 'hall', zoom=0.1)
    A("When you remain quiet, he'll become less convincing.", 'peep', who=('cop', 'double'), dbl_expr='worried')
    A("He'll forget which hand", 'double_cu', expr='worried', ring_hand='right', circle='ring')
    A("He'll glance at the officer", 'peep', who=('cop', 'double'), dbl_expr='worried')
    A("Then the officer will ask about a photograph", 'simple', kind='photo')
    A("You haven't told him there's a photograph", 'simple', kind='photo', zoom=0.12)
    A("Who took that picture?", 'peep', who=('cop', 'double'), cop_expr='cold')
    A("The man outside says,", 'peep', who=('cop', 'double'), dbl_expr='neutral')
    A("It was your father.", 'simple', kind='photo', zoom=0.15)
    A("You grip the edge of the table", 'simple', kind='grip')
    A("The officer waits.", 'peep', who=('cop', 'double'), cop_expr='cold')
    A("After a few seconds, he turns off his camera.", 'cop_cu', focus='cam', hand='cam', rec=False)
    A("We're getting nowhere,", 'cop_cu', expr='impatient', rec=False)
    A("For the first time all night", 'double_cu', expr='worried')
    # rule 6
    A("Rule number six.", 'rule', n=6, text_="Whatever they promise, don't step outside voluntarily.")
    A("By now, the officer's patience", 'peep', closer=0.5, expr='impatient')
    A("He'll tell you there's an easy way", 'peep', closer=0.5, expr='impatient')
    A("Come onto the porch.", 'house', cop=True, both=True)
    A("Nobody's being arrested.", 'peep', closer=0.5)
    A("Then he'll say something you need to listen to", 'hall', zoom=0.08)
    A("Once you've left the property", 'cop_cu', expr='cold')
    A("The other man will take a key from his coat.", 'peep', who=('double',), closer=0.4, expr='cold')
    A("Your key.", 'lock', key='in')
    A("He'll hold it near the lock", 'lock', key='hold')
    A("Don't touch it.", 'lock', key='hold', hand='hover')
    A("The officer may threaten to force the door.", 'peep', closer=0.6, expr='angry')
    A("He may count down from ten.", 'countdown', start=10, step=10.0)
    A("Let him reach zero.", 'countdown', start=9, step=0.33)
    A("There won't be a kick.", 'hall', zoom=0.06)
    A("You'll hear him breathing on the other side.", 'lock')
    A("Then the second officer will get out of the car.", 'house', cop=True, both=True, cop2_out=True)
    A("She'll walk up the path carrying", 'peep', who=('cop2',), walk=('cop2', 3.0), bag=True)
    A("Inside are a wallet, a phone", 'bag')
    A("You recognize the bright orange key ring.", 'bag', zoom=0.4, focus=(980, 760))
    A("It belongs to the man who lives two houses down.", 'house', cop=False, neighbour_dark=True)
    A("That one came outside,", 'peep', who=('cop2',), closer=0.3, bag=True)
    A("The first officer motions for her to be quiet.", 'peep', who=('cop', 'cop2'), arms=('down', 'out'))
    A("She looks at your door.", 'peep', who=('cop2',), closer=0.5, expr='cold')
    A("This one heard you, didn't he?", 'peep', who=('cop2',), closer=0.5, expr='cold')
    A("Neither of them says anything else.", 'peep', who=('cop', 'double', 'cop2'))
    A("For a long time, all three stand", 'peep', who=('cop', 'double', 'cop2'), zoom=0.1)
    A("Then the man wearing your coat puts his key away.", 'peep', who=('cop', 'double', 'cop2'))
    A("We should try her,", 'double_cu', expr='cold')
    A("The officer switches his camera back on.", 'cop_cu', focus='cam', hand='cam', rec=True)
    # rule 7
    A("Rule number seven.", 'rule', n=7, text_="When they leave, keep your door locked and call your family again.")
    A("You'll watch them return to the car.", 'house', cop=False)
    A("The man with your face gets into the back seat.", 'car', man='lowered')
    A("Before he lowers his head", 'car', man='raised', look_up='anim', zoom=0.12)
    A("You keep watching until the car turns", 'house', cop=False, leaving=1.0)
    A("Then you try your mother again.", 'phone', state='calling')
    A("This time, she answers almost immediately.", 'phone', state='connected')
    A("Thank goodness.", 'mum_room', expr='worried')
    A("You tell her to lock her doors.", 'hall', phone=True)
    A("There's a pause.", 'mum_room', expr='worried')
    A("What did that officer say to you?", 'mum_cu', expr='worried', tears=0.0)
    A("Your hand tightens around the phone.", 'phone', state='connected', timer0=20)
    A("She tells you he called earlier.", 'mum_room', expr='worried')
    A("He asked a few questions", 'chips', items=('FIRST PET', 'SCHOOL', 'THE PHOTOGRAPH'))
    A("You close your eyes.", 'black')
    A("Then you ask whether she told him", 'hall', phone=True)
    A("Just the address,", 'mum_cu', expr='worried', tears=0.0)
    A("You tell her nobody is bringing you anywhere.", 'hall', phone=True, lean=0.3)
    A("You hear her television go quiet.", 'mum_room', tv=False, expr='scared')
    A("Then, very softly, she says your name.", 'mum_cu', expr='scared', tears=0.0)
    A("There's knocking at her door.", 'mum_ext', knock=True)
    A("You shout for her to leave it closed.", 'hall', phone=True, red=0.3)
    A("She says she's only going to look", 'mum_room', tv=False, expr='scared', look=(1.0, 0))
    A("The little scrape of the curtain rings.", 'mum_room', tv=False, anim_curtain=True, expr='scared', look=(1.0, 0))
    A("For several seconds, she doesn't speak.", 'mum_ext', curtain=1.0)
    A("Then you hear her start to cry.", 'mum_cu', expr='sad', tears=1.0)
    A("You tell her about the scar.", 'double_cu', expr='sad', circle='scar')
    A("She takes a shaky breath.", 'mum_cu', expr='sad', tears=1.0)
    A("The ring's on the correct hand,", 'double_cu', expr='sad', ring_hand='left', circle='ring')
    A("And the scar...", 'double_cu', expr='sad', scar='left', circle='scar')
    A("She stops.", 'mum_cu', expr='scared', tears=1.0)
    A("Through her phone, you hear a familiar voice", 'mum_ext')
    A("Mum, please. It's cold.", 'double_cu', expr='sad', tears=1.0)
    A("It sounds tired.", 'double_cu', expr='sad', tears=1.0)
    A("You tell her to come away from the door.", 'hall', phone=True, red=0.4, flash=True)
    A("The officer says something you can't quite hear.", 'mum_ext')
    A("Why does he have your coat?", 'mum_cu', expr='scared', tears=0.5)
    A("You turn toward the hook beside your front door.", 'hall', coat=False, zoom=0.1)
    A("It's empty.", 'simple', kind='hook', zoom=0.1)
    A("You remember hanging the coat there", 'simple', kind='hook')
    A("For the first time, you wonder how long", 'house', cop=False)
    A("At the other end of the call", 'mum_cu', expr='sad', tears=0.5)
    A("You're speaking to me now.", 'hall', phone=True, red=0.5, flash=True)
    A("But she's already moving the phone away", 'mum_room', tv=False, curtain=1.0, expr='sad', tears=0.5)
    A("You hear the officer clearly this time.", 'mum_ext')
    A("You keep saying her name.", 'hall', phone=True, red=0.6, flash=True)
    A("Outside her house, the other you begins to cry.", 'double_cu', expr='sad', tears=1.0)
    A("Your mother whispers,", 'mum_cu', expr='sad', tears=1.0)
    A("Then you hear her key turning.", 'lock', key='turn', red=0.6)
    # outro
    A("So, if a police officer ever knocks", 'peep', zoom=0.06)
    A("And warn your family while you still can.", 'phone', state='calling')
    A("Because the person waiting in that patrol car", 'car', man='raised', look_up='anim', zoom=0.2, focus=(960, 380))
