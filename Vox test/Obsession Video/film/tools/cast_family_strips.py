"""cast_family_strips.py: acting strips for the Obsession film's family (used by tools/cast_family.py strips).

Each action is staged on a flat stand-in set (the real sets are the sets team's) and rendered as 8 frames (320x180);
three actions per image -> _work/cast/family_strips_<group>.jpg, with a printed contact report.
"""
import os, math
import numpy as np
import cv2
import skia
from engine.core import Pen, CFG, rect, rrect, oval, poly, smooth, mix
import characters as CH
from cast_clips import room, door, window, table, stairs, actor, fig
from cast_family import _surface, _grab, OUT, FLOOR, NIGHT, WARM, PHONE

DAWN = dict(rim='#ffd9a8', rim_a=70, side=-1, key=-0.1)
STRIPS = {}
GROUPS = {'adam_a': ['adam_bed_type', 'adam_window', 'adam_locker'],
          'adam_b': ['adam_stairs', 'adam_step_over', 'adam_run'],
          'adam_c': ['adam_tell', 'adam_door_no', 'adam_shoebox'],
          'mom_a': ['mom_scrub', 'mom_phone', 'mom_hoodie'],
          'mom_b': ['mom_drive', 'mom_fork', 'mom_taps'],
          'lina': ['lina_knock', 'lina_point', 'lina_card'],
          'danny': ['danny_card', 'danny_lunch', 'danny_explain'],
          'help': ['rahman_door', 'rahman_chair', 'caretaker_roll'],
          'misc': ['tape_swings', 'lina_scrub_sing', 'caretaker_squint']}


def strip(name, dur):
    def deco(f):
        STRIPS[name] = (f, dur); return f
    return deco


def chair(pen, x, seat, w=150, back=1, c='#6a4a34'):
    pen.fill(rect(x - w / 2, seat, w, 18), c); pen.line(rect(x - w / 2, seat, w, 18), 2)
    bx = x - back * w / 2
    pen.fill(rect(bx - 10, seat - 230, 20, 230), c); pen.line(rect(bx - 10, seat - 230, 20, 230), 2)
    for lx in (x - w / 2 + 8, x + w / 2 - 20): pen.fill(rect(lx, seat + 18, 12, FLOOR - seat - 18), mix(c, '#000000', 0.3))


def kitchen_table(pen, x0, x1, top, c='#8a6a48'):
    pen.fill(rect(x0, top, x1 - x0, 20), c); pen.line(rect(x0, top, x1 - x0, 20), 2.5)
    for x in (x0 + 24, x1 - 44): pen.fill(rect(x, top + 20, 20, FLOOR - top - 20), mix(c, '#000000', 0.3))


def chalk_word(pen, x, y, w, word='ONLY ME', a=230):
    CH.chalk_word(pen, word, x, y, w) if hasattr(CH, 'chalk_word') else None


# ------------------------------------------------------------------------------------------------ Adam
@strip('adam_bed_type', 5.0)
def _s_bed():
    ppm = 400.0; seat = FLOOR - 0.5 * ppm
    a = actor('adam_night', 820, FLOOR, ppm, seed=3, expr='adam_lonely'); a.set(-1e9, None, 0.0, turn=0.45)
    a.seated(seat, hands='lap')
    a.phone_type(0.6, 4.6, side=-1)
    a.expr('adam_scared', 3.6, None)
    def draw(pen, t):
        room(pen, '#1e2436', '#262a36')
        pen.fill(rect(520, seat - 40, 900, 60), '#3a4660'); pen.fill(rect(520, seat + 20, 900, FLOOR - seat - 20), '#2a3044')
        pen.fill(rect(500, seat - 330, 40, 330 + FLOOR - seat), '#4a3a30')
        fig(pen, a, t, PHONE)
        duvet = smooth([(700, seat - 20), (1000, seat - 70), (1420, seat - 40), (1420, seat + 40), (700, seat + 30)], True, 0.5)
        pen.fill(duvet, '#5a6c8c'); pen.line(duvet, 3)
    return dict(draw=draw, actors=[a], grounded=[])


@strip('adam_window', 5.0)
def _s_window():
    ppm = 380.0
    a = actor('adam_night', 900, FLOOR, ppm, seed=4, expr='adam_guarded'); a.set(-1e9, None, 0.0, turn=0.6)
    a.look_down_at(0.4, (1320, 1300), t1=2.9, lean=0.8)
    a.expr('adam_scared', 1.6, None)
    a.duck(3.0, t1=None)
    def draw(pen, t):
        room(pen, '#1e2436', '#262a36')
        window(pen, 1320, 260, w=330, h=420, night=True)
        fig(pen, a, t, NIGHT)
    return dict(draw=draw, actors=[a], grounded=[a])


def _locker_ang(t):
    return 75.0 * CH.ease_in_out(CH.prog(t, 1.1, 1.8))


@strip('adam_locker', 5.5)
def _s_locker():
    ppm = 380.0; hx = 1420.0; lw = 230.0
    a = actor('adam', 1075, FLOOR, ppm, seed=5, expr='adam_guarded'); a.set(-1e9, None, 0.0, turn=0.55)
    handle = lambda t: (hx - (lw - 18) * math.cos(math.radians(_locker_ang(t))), 610.0)
    a.reach_to(0.5, 1, handle, t1=1.55, dur=0.5, z=40.0, contact='grip', shape='grip')
    br = CH.PropTrack('bracelet_real', 1212, 474, ppm / 100.0)
    a.pick_up(br, 2.7, side=-1, dur=1.2)
    a.look_at(0.0, handle, t1=2.6, dur=0.3)
    a.look_at(2.6, (1212, 474), t1=3.4, dur=0.3)
    a.look_at(3.4, lambda t: br.pos(t), dur=0.3)
    a.expr('adam_scared', 3.6, None)
    def draw(pen, t):
        room(pen, '#5a6270', '#4a4a50')
        pen.fill(rect(hx - lw, 220, lw, FLOOR - 220), '#3a3e46'); pen.fill(rect(hx - lw, 500, lw, 10), '#5a5e66')
        br.draw(pen, t)
        ang = math.radians(_locker_ang(t)); xe = hx - lw * math.cos(ang)
        d = poly([(hx, 220), (xe, 220 - 30 * math.sin(ang)), (xe, FLOOR + 30 * math.sin(ang)), (hx, FLOOR)], True)
        pen.fill(d, '#6f8fa8'); pen.line(d, 3)
        fig(pen, a, t, WARM)
    return dict(draw=draw, actors=[a], grounded=[a])


@strip('adam_stairs', 6.0)
def _s_stairs():
    ppm = 300.0; rise, run, n = 50.0, 80.0, 8
    top = FLOOR - n * rise
    a = actor('adam_night', 880, top, ppm, seed=6, expr='adam_scared'); a.set(-1e9, None, 0.0, turn=0.7)
    a.look_at(0.0, (1500, FLOOR - 60), dur=0.4)
    ev = a.climb(1.6, 5.0, 0, -rise, 4, run)
    a.expr('adam_lonely', 3.0, None)
    def draw(pen, t):
        room(pen, '#2a2a38', '#30303a')
        stairs(pen, 1500, n=n, rise=rise, run=run, w=520, dirn=-1)
        fig(pen, a, t, NIGHT)
    return dict(draw=draw, actors=[a], grounded=[])


@strip('adam_step_over', 4.5)
def _s_step_over():
    ppm = 360.0
    a = actor('adam_night', 520, FLOOR, ppm, seed=7, expr='adam_steady'); a.set(-1e9, None, 0.0, turn=0.9)
    a.walk(0.2, 3.8, 0, 900, facing=1, surface='inside')
    a.step_up(1.55, side=1, up=1.0, hold=0.3, back=0.5)
    a.look_at(0.9, (930, FLOOR), t1=2.0, dur=0.3)
    def draw(pen, t):
        room(pen, '#2a2a38', '#4a3a30')
        for k, ch in enumerate('ONLY'):
            pen.line(poly([(850 + k * 40, FLOOR - 4), (870 + k * 40, FLOOR - 14)], False), 6, '#f1efe8')
        fig(pen, a, t, NIGHT)
    return dict(draw=draw, actors=[a], grounded=[a])


@strip('adam_run', 3.0)
def _s_run():
    ppm = 340.0
    a = actor('adam', 300, FLOOR, ppm, seed=8, expr='adam_scared'); a.set(-1e9, None, 0.0, turn=0.9)
    a.run(0.2, 2.8, 0, 1300, surface='outside')
    def draw(pen, t):
        room(pen, '#a8b4c4', '#7a7a74')
        fig(pen, a, t, WARM)
    return dict(draw=draw, actors=[a], grounded=[a])


@strip('adam_tell', 6.0)
def _s_tell():
    ppm = 360.0; seat = FLOOR - 0.45 * ppm; top = FLOOR - 0.74 * ppm
    a = actor('adam_night', 690, FLOOR, ppm, seed=9, expr='adam_ashamed'); a.set(-1e9, None, 0.0, turn=0.55)
    m = actor('mom', 1250, FLOOR, ppm, seed=10, expr='listening_soft'); m.set(-1e9, None, 0.0, turn=-0.55)
    a.seated(seat); m.seated(seat)
    for s_, dx in ((1, 0), (-1, 40)):
        a.reach_to(0.0, s_, (830 + dx, top - 4), dur=0.4, z=60.0, contact='palm', shape='flat')
    m.reach_to(0.0, -1, (1110, top - 4), dur=0.4, z=60.0, contact='palm', shape='flat')
    a.talk([(0.4, 1.6), (2.0, 3.2)], intensity=0.7)
    a.look_at(0.0, (980, top), t1=2.0, dur=0.3)
    a.look_at(3.4, (m, 'eyes'), dur=0.4); a.expr('adam_steady', 3.5, None)
    m.look_at(0.0, (a, 'eyes'), dur=0.4); m.nod(2.2, n=1); m.expr('mom_warm', 4.2, None)
    m.talk([(4.4, 5.6)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#5a5048', '#4a4038')
        chair(pen, 630, seat, back=1); chair(pen, 1310, seat, back=-1)
        fig(pen, a, t, WARM); fig(pen, m, t, WARM)
        kitchen_table(pen, 780, 1160, top)
        CH.draw_prop3(pen, 'phone_mom', 1060, top - 3, ppm / 100.0, angle=90)
    return dict(draw=draw, actors=[a, m], grounded=[])


@strip('adam_door_no', 5.0)
def _s_door_no():
    ppm = 340.0
    m = actor('mom', 760, FLOOR, ppm, seed=11, expr='mom_firm'); m.set(-1e9, None, 0.0, turn=0.45)
    a = actor('adam_night', 980, FLOOR, ppm, seed=12, expr='adam_steady'); a.set(-1e9, None, 0.0, turn=0.45)
    tgt = (1650, FLOOR - 0.9 * ppm)
    m.look_at(0.0, tgt, dur=0.3); a.look_at(0.0, tgt, dur=0.3)
    a.talk([(0.8, 1.2), (1.6, 3.6)], intensity=0.9)
    a.expr('adam_lonely', 3.9, 4.6); a.look_at(3.9, (1650, FLOOR), t1=4.5, dur=0.3)
    def draw(pen, t):
        room(pen, '#4a4038', '#5a4636')
        door(pen, 1650, open_=0.85, slot=True, peep=False, c='#3f7a4c')
        fig(pen, m, t, WARM); fig(pen, a, t, WARM)
    return dict(draw=draw, actors=[m, a], grounded=[m, a])


def _box_x(t):
    return 1170.0 - 250.0 * CH.ease_in_out(CH.prog(t, 0.8, 2.4))


@strip('adam_shoebox', 5.0)
def _s_shoebox():
    ppm = 360.0; seat = FLOOR - 0.45 * ppm; top = FLOOR - 0.74 * ppm
    a = actor('adam', 700, FLOOR, ppm, seed=13, expr='adam_lonely'); a.set(-1e9, None, 0.0, turn=0.55)
    d = actor('danny', 1330, FLOOR, ppm, seed=14, expr='danny_shy'); d.set(-1e9, None, 0.0, turn=-0.55)
    a.seated(seat); d.seated(seat)
    bw = 15.0 * ppm / 100.0
    for s_, sx in ((1, -1), (-1, 1)):
        d.reach_to(0.5, s_, lambda t, sx=sx: (_box_x(min(t, 1.75)) + sx * bw * 0.9, top - 0.06 * ppm), t1=1.75, dur=0.4,
                   z=60.0, contact='palm', shape='flat')
    for s_, sx in ((1, 1), (-1, -1)):
        a.reach_to(2.8, s_, (_box_x(5.0) + sx * bw * 0.45, top - 0.11 * ppm - 6), dur=0.6, z=60.0, contact='palm', shape='flat')
    a.look_at(0.0, lambda t: (_box_x(t), top - 40), dur=0.3)
    d.look_at(0.0, lambda t: (_box_x(t), top - 40), t1=2.8, dur=0.3); d.look_at(2.8, (a, 'eyes'), dur=0.4)
    d.expr('danny_kind', 2.8, None)
    def draw(pen, t):
        room(pen, '#7a8090', '#6a6460')
        chair(pen, 640, seat, back=1); chair(pen, 1390, seat, back=-1)
        fig(pen, a, t, WARM); fig(pen, d, t, WARM)
        kitchen_table(pen, 790, 1240, top, c='#b89a70')
        CH.draw_shoebox(pen, _box_x(t), top, ppm / 100.0)
    return dict(draw=draw, actors=[a, d], grounded=[])


# ------------------------------------------------------------------------------------------------ Mom
@strip('mom_scrub', 6.0)
def _s_scrub():
    ppm = 360.0
    m = actor('mom', 760, FLOOR, ppm, seed=15, expr='mom_tired'); m.set(-1e9, None, 0.0, turn=0.6, ob_knuck=1.0, ob_tired=0.8)
    ev = m.scrub(1.0, 5.6, (1010, FLOOR - 4), side=1)
    def draw(pen, t):
        room(pen, '#8a96aa', '#6e6e70')
        k = CH.clamp((t - 1.0) / 4.0)
        for j, ch in enumerate('ONLY'):
            pen.line(poly([(950 + j * 40, FLOOR - 4), (970 + j * 40, FLOOR - 14)], False), 6, '#f1efe8', int(230 * (1 - 0.8 * k)))
        pen.fill(oval(1010, FLOOR - 2, 140, 10), '#4a5058', 120)
        CH.draw_bucket(pen, 560, FLOOR, ppm / 100.0, wet=0.6)
        fig(pen, m, t, DAWN)
    return dict(draw=draw, actors=[m], grounded=[])


@strip('mom_phone', 5.0)
def _s_mom_phone():
    ppm = 360.0
    m = actor('mom', 880, FLOOR, ppm, seed=16, expr='mom_tired'); m.set(-1e9, None, 0.0, turn=-0.4, ob_knuck=1.0)
    m.phone_to_ear(0.3, 4.6, side=1)
    m.talk([(0.9, 1.6), (2.0, 3.0), (3.3, 4.4)], intensity=0.8)
    m.look_at(0.0, (500, FLOOR - 200), dur=0.4)
    def draw(pen, t):
        room(pen, '#6a6050', '#5a4a3a')
        CH.draw_bucket(pen, 1320, FLOOR, ppm / 100.0)
        fig(pen, m, t, DAWN)
    return dict(draw=draw, actors=[m], grounded=[m])


@strip('mom_hoodie', 5.0)
def _s_hoodie():
    ppm = 340.0
    m = actor('mom', 1150, FLOOR, ppm, seed=17, expr='mom_warm'); m.set(-1e9, None, 0.0, turn=-0.5)
    a = actor('adam', 640, FLOOR, ppm, seed=18, expr='adam_guarded'); a.set(-1e9, None, 0.0, turn=0.5)
    m.hold_hoodie(0.4, None, side=1)
    m.look_at(0.0, (a, 'eyes'), dur=0.4); m.talk([(1.0, 2.1)], intensity=0.8)
    m.expr('mom_watchful', 2.9, None)
    a.look_at(0.0, (m, 'eyes'), t1=2.4, dur=0.3); a.talk([(2.5, 2.9)], intensity=0.6)
    a.look_at(2.9, (300, FLOOR - 150), dur=0.3)
    def draw(pen, t):
        room(pen, '#6a6a5a', '#5a4a3a')
        fig(pen, a, t, WARM); fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m, a], grounded=[m, a])


@strip('mom_drive', 5.0)
def _s_drive():
    ppm = 420.0; seat = FLOOR - 0.15 * ppm
    m = actor('mom', 700, FLOOR, ppm, seed=19, expr='mom_tired'); m.set(-1e9, None, 0.0, turn=0.0)
    a = actor('adam', 1220, FLOOR, ppm, seed=20, expr='adam_guarded'); a.set(-1e9, None, 0.0, turn=0.0)
    m.seated(seat, floor_y=FLOOR + 0.3 * ppm); a.seated(seat, floor_y=FLOOR + 0.3 * ppm)
    wc = (700, seat - 0.42 * ppm); wr = 0.17 * ppm
    g10 = (wc[0] + math.cos(math.pi * 1.17) * wr, wc[1] + math.sin(math.pi * 1.17) * wr * 0.86)
    g2 = (wc[0] + math.cos(math.pi * 1.83) * wr, wc[1] + math.sin(math.pi * 1.83) * wr * 0.86)
    m.drive(0.0, None, g10, g2)
    m.look_at(0.0, (720, 240), dur=0.3)
    a.look_at(0.0, (1900, 420), dur=0.3, body=0.1); a.look_at(2.6, (1900, 420), dur=0.15)
    a.expr('adam_scared', 2.5, None)
    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#2a2e38')
        pen.fill(rect(60, 60, 1800, 420), '#8ea4b8')
        fig(pen, m, t, WARM); fig(pen, a, t, WARM)
        pen.fill(rect(0, seat - 0.2 * ppm, 1920, 600), '#3a3e48'); pen.line(rect(0, seat - 0.2 * ppm, 1920, 600), 3)
        CH.draw_steering_wheel(pen, wc[0], wc[1], wr)
    return dict(draw=draw, actors=[m, a], grounded=[])


@strip('mom_fork', 5.0)
def _s_fork():
    ppm = 380.0; seat = FLOOR - 0.45 * ppm; top = FLOOR - 0.74 * ppm
    m = actor('mom', 760, FLOOR, ppm, seed=21, expr='mom_tired'); m.set(-1e9, None, 0.0, turn=0.5)
    m.seated(seat)
    fork_rest = (1000, top - 3)
    m.reach_to(-1e9, 1, (960, top - 60), t1=0.9, dur=0.3, z=60.0, contact='grip', shape='grip', prop='fork')
    m.hold_prop('fork', 1, -1e9, 1.4)
    tr = m.set_down(0.8, 'fork', 1, fork_rest, dur=1.0)
    m.look_at(0.0, (1000, top), t1=1.6, dur=0.3)
    m.look_at(1.7, (1700, FLOOR - 0.55 * ppm), dur=0.4); m.expr('mom_watchful', 1.8, None)
    m.talk([(2.4, 3.9)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#2e3040', '#4a4038')
        chair(pen, 700, seat, back=1)
        fig(pen, m, t, WARM)
        kitchen_table(pen, 880, 1500, top)
        pen.fill(oval(1150, top - 4, 70, 10), '#ecebe6'); pen.line(oval(1150, top - 4, 70, 10), 2)
        if t >= tr: CH.draw_prop3(pen, 'fork', fork_rest[0], fork_rest[1], ppm / 100.0, angle=90)
    return dict(draw=draw, actors=[m], grounded=[])


@strip('mom_taps', 5.0)
def _s_taps():
    ppm = 420.0
    m = actor('mom', 900, FLOOR, ppm, seed=22, expr='mom_firm'); m.set(-1e9, None, 0.0, turn=0.3)
    ev = m.phone_taps([1.4, 2.5, 3.6], side=1)
    def draw(pen, t):
        room(pen, '#5a5048', '#4a4038')
        fig(pen, m, t, WARM)
    return dict(draw=draw, actors=[m], grounded=[m])


# ------------------------------------------------------------------------------------------------ Lina
@strip('lina_knock', 4.0)
def _s_knock():
    ppm = 400.0
    l = actor('lina', 1040, FLOOR, ppm, seed=23, expr='lina_earnest'); l.set(-1e9, None, 0.0, turn=0.5)
    ev = l.knock(0.4, n=2, spacing=0.4, side=1)
    l.talk([(1.8, 3.6)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#3a3a4a', '#4a3a30')
        door(pen, 1340, open_=0.0, slot=False, peep=False, c='#e8e2d6')
        fig(pen, l, t, WARM)
    return dict(draw=draw, actors=[l], grounded=[l])


@strip('lina_point', 4.0)
def _s_point():
    ppm = 400.0
    l = actor('lina', 760, FLOOR, ppm, seed=24, expr='lina_earnest'); l.set(-1e9, None, 0.0, turn=0.3)
    up = (1500, 120)
    l.point_at(0.4, up, t1=3.6, side=1)
    l.look_at(0.2, up, t1=1.8, dur=0.4); l.look_at(1.8, (300, 300), dur=0.4)
    l.talk([(2.0, 3.6)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#3a3a4a', '#4a3a30')
        fig(pen, l, t, WARM)
    return dict(draw=draw, actors=[l], grounded=[l])


@strip('lina_card', 5.0)
def _s_card():
    ppm = 420.0
    l = actor('lina', 900, FLOOR, ppm, seed=25, expr='lina_earnest'); l.set(-1e9, None, 0.0, turn=-0.3)
    def held(t):
        x, y = l.where(t, 'eyes'); return x - 0.24 * ppm, y - 0.06 * ppm
    l.reach_to(0.4, 1, held, t1=None, dur=0.7, z=80.0, contact='grip', shape='grip', prop='rule_card')
    l.hold_prop('rule_card', 1, 0.4, None)
    l.look_at(0.0, (300, 380), dur=0.4)
    l.talk([(2.2, 3.4)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#2a2a34', '#3a3230')
        pen.line(poly([(1000, 0), (1000, 120)], False), 3, '#222222')
        pen.fill(oval(1000, 135, 22, 22), '#fff4d0')
        fig(pen, l, t, dict(rim='#fff1c8', rim_a=110, side=1, key=0.0))
    return dict(draw=draw, actors=[l], grounded=[l])


@strip('lina_scrub_sing', 5.0)
def _s_lina_scrub():
    ppm = 420.0
    l = actor('lina', 800, FLOOR, ppm, seed=26, expr='lina_sing'); l.set(-1e9, None, 0.0, turn=0.6)
    l.scrub(0.9, 4.8, (1000, FLOOR - 4), side=1, amp=10.0)
    l.sing_sway(1.0, 4.8)
    l.talk([(1.2, 2.4), (2.6, 3.8)], intensity=0.7)
    def draw(pen, t):
        room(pen, '#9aa6b8', '#5a4a3a')
        fig(pen, l, t, DAWN)
    return dict(draw=draw, actors=[l], grounded=[])


# ------------------------------------------------------------------------------------------------ Danny
@strip('danny_card', 6.0)
def _s_danny_card():
    ppm = 360.0
    d = actor('danny', 300, FLOOR, ppm, seed=27, expr='danny_shy'); d.set(-1e9, None, 0.0, turn=0.9)
    a = actor('adam', 1320, FLOOR, ppm, seed=28, expr='adam_lonely'); a.set(-1e9, None, 0.0, turn=-0.5)
    card = CH.PropTrack('rule_card', 0, 0, ppm / 100.0); card.held(-1e9, d, 1)
    CH._set_prop(d, 1, -1e9, None, 'rule_card')
    d.reach(-1e9, None, 1, out=-20.0, down=110.0, fwd=150.0, shape='grip', up=0.0, fade=0.1)
    d.walk(0.2, 2.6, 0, 700, facing=1, surface='inside')
    d.turn(2.6, 0.5, dur=0.5)
    tc = d.give(card, 3.2, 1, a, -1, dur=1.4)
    d.not_meeting(2.8, a, side=-1)
    d.talk([(3.4, 5.2)], intensity=0.7)
    a.look_at(0.0, (d, 'eyes'), dur=0.4)
    def draw(pen, t):
        room(pen, '#8a8e7e', '#6a6460')
        fig(pen, d, t, WARM); fig(pen, a, t, WARM)
    return dict(draw=draw, actors=[d, a], grounded=[d, a])


@strip('danny_lunch', 5.0)
def _s_lunch():
    ppm = 340.0; seat = FLOOR - 0.45 * ppm; top = FLOOR - 0.74 * ppm
    ks = [('kofi', 560, 0.5), ('danny', 960, 0.0), ('sam', 1360, -0.5)]
    acts = []
    for k, (who, x, tn) in enumerate(ks):
        b = actor(who, x, FLOOR, ppm, seed=30 + k, expr='kind_smile' if who != 'danny' else 'danny_kind'); b.set(-1e9, None, 0.0, turn=tn)
        b.seated(seat)
        for s_ in (1, -1): b.reach_to(0.0, s_, (x + s_ * -60, top - 4), dur=0.3, z=80.0, contact='palm', shape='flat')
        acts.append(b)
    acts[0].talk([(0.4, 1.8)], intensity=0.8); acts[0].look_at(0.0, (acts[1], 'eyes'), dur=0.3)
    acts[2].look_at(0.0, (acts[1], 'eyes'), dur=0.3); acts[1].look_at(0.0, (acts[0], 'eyes'), t1=2.4, dur=0.3)
    acts[1].expr('kind_smile', 1.9, None); acts[1].talk([(2.6, 3.8)], intensity=0.6); acts[1].look_at(2.4, (acts[2], 'eyes'), dur=0.3)
    def draw(pen, t):
        room(pen, '#a8a890', '#7a7460')
        for b in acts: fig(pen, b, t, WARM)
        kitchen_table(pen, 360, 1560, top, c='#c8c2b0')
    return dict(draw=draw, actors=acts, grounded=[])


@strip('danny_explain', 5.0)
def _s_explain():
    ppm = 420.0; seat = FLOOR - 0.45 * ppm; top = FLOOR - 0.74 * ppm
    d = actor('danny', 1100, FLOOR, ppm, seed=33, expr='danny_shy'); d.set(-1e9, None, 0.0, turn=-0.4)
    d.seated(seat)
    for s_ in (1, -1): d.reach_to(0.0, s_, (900 + s_ * 40, top - 4), dur=0.3, z=80.0, contact='palm', shape='flat')
    d.look_at(0.0, (800, top), t1=1.4, dur=0.3); d.look_at(1.4, (300, FLOOR - 0.6 * ppm), dur=0.4)
    d.talk([(0.4, 1.3), (1.6, 3.4)], intensity=0.7); d.expr('danny_kind', 1.5, None)
    def draw(pen, t):
        room(pen, '#a8a890', '#7a7460')
        chair(pen, 1180, seat, back=-1)
        fig(pen, d, t, WARM)
        kitchen_table(pen, 500, 1000, top, c='#c8c2b0')
    return dict(draw=draw, actors=[d], grounded=[])


# ------------------------------------------------------------------------------------------------ helpers
@strip('rahman_door', 4.0)
def _s_rahman_door():
    ppm = 360.0
    r = actor('rahman', 960, FLOOR, ppm, seed=34, expr='rahman_calm'); r.set(-1e9, None, 0.0, turn=0.35)
    r.look_at(0.0, lambda t: (300 + 300 * t, FLOOR - 0.5 * ppm), dur=0.4)
    r.nod(1.6, n=1); r.expr('rahman_kind', 1.4, None)
    def draw(pen, t):
        room(pen, '#8a8e7e', '#6a6460')
        pen.fill(rect(780, 260, 360, FLOOR - 260), '#d8d0bc'); pen.line(rect(780, 260, 360, FLOOR - 260), 6, '#5a4a3a')
        fig(pen, r, t, WARM)
    return dict(draw=draw, actors=[r], grounded=[r])


@strip('rahman_chair', 5.0)
def _s_rahman_chair():
    ppm = 400.0; seat = FLOOR - 0.47 * ppm
    r = actor('rahman', 900, FLOOR, ppm, seed=35, expr='rahman_calm'); r.set(-1e9, None, 0.0, turn=0.5)
    r.seated(seat)
    r.listen_tilt(0.5, 3.2, side=1)
    r.nod(3.4, n=2, amount=0.8); r.expr('rahman_kind', 3.0, None)
    r.talk([(3.9, 4.8)], intensity=0.7)
    def draw(pen, t):
        room(pen, '#b8b4a2', '#6a7064')
        chair(pen, 860, seat, back=1, c='#4a5a6a')
        pen.fill(rect(1500, FLOOR - 160, 90, 160), '#a0603a'); pen.fill(oval(1545, FLOOR - 220, 90, 80), '#4f8a4a')
        fig(pen, r, t, WARM)
    return dict(draw=draw, actors=[r], grounded=[])


@strip('caretaker_roll', 6.0)
def _s_roll():
    ppm = 340.0
    c = actor('caretaker', 700, FLOOR, ppm, seed=36, expr='neutral'); c.set(-1e9, None, 0.0, turn=0.7)
    ev = c.roller(0.6, 5.6, (1060, FLOOR - 4))
    c.look_at(0.0, (1060, FLOOR), dur=0.4)
    def draw(pen, t):
        room(pen, '#c89a78', '#7a7468')
        pen.fill(rect(900, FLOOR - 10, 400, 20), CH.KEEPING_RED); pen.fill(rect(900, FLOOR - 10, 320, 20), '#d9d4c6', 220)
        fig(pen, c, t, DAWN)
        CH.draw_roller(pen, c, t, ppm / 100.0)
    return dict(draw=draw, actors=[c], grounded=[c])


@strip('caretaker_squint', 3.0)
def _s_squint():
    ppm = 400.0
    c = actor('caretaker', 900, FLOOR, ppm, seed=37, expr='neutral'); c.set(-1e9, None, 0.0, turn=-0.3)
    c.expr('squint_up', 0.4, None)
    c.reach_to(0.5, 1, lambda t: (c.where(t, 'eyes')[0] + 0.02 * ppm, c.where(t, 'eyes')[1] - 0.06 * ppm), dur=0.4,
               z=60.0, contact='palm', shape='flat')
    c.look_at(0.0, (300, FLOOR - 0.3 * ppm), dur=0.3)
    def draw(pen, t):
        room(pen, '#2a2a34', '#3a3a3a')
        fig(pen, c, t, dict(rim='#f4f0d8', rim_a=130, side=1, key=0.1))
    return dict(draw=draw, actors=[c], grounded=[c])


@strip('tape_swings', 6.0)
def _s_swings():
    ppm = 330.0; L = 1.6 * ppm; seat_y = FLOOR - 0.45 * ppm
    kids = []
    for k, (who, px) in enumerate((('adam7', 700), ('danny7', 1250))):
        pv = (px, seat_y - L)
        b = actor(who, px, FLOOR, ppm, seed=38 + k, expr='kid_grin'); b.set(-1e9, None, 0.0, turn=0.85 - 1.7 * k)
        b.seated(seat_y)
        b.swing_ride(0.2, 5.8, pv, L, amp=16.0 + 4 * k, period=2.3 + 0.2 * k, sep=0.3)
        b.sing_sway(0.6, 5.6, smile=0.8)
        kids.append((b, pv))
    kids[0][0].talk([(0.8, 2.6), (3.0, 4.8)], intensity=0.8)
    def draw(pen, t):
        room(pen, '#a8c8e0', '#8aa86a')
        pen.fill(rect(300, seat_y - L - 20, 1320, 22), '#6a5a4a')
        for b, pv in kids:
            ang, _ = b.swing_state(t)
            CH.draw_swing(pen, pv, L, ang, ppm / 100.0, sep=0.3, part='back')
            fig(pen, b, t, WARM)
            CH.draw_swing(pen, pv, L, ang, ppm / 100.0, sep=0.3, part='front')
    return dict(draw=draw, actors=[b for b, _ in kids], grounded=[])


# ------------------------------------------------------------------------------------------------ render
def render_group(g):
    rows = []
    for name in GROUPS[g]:
        f, dur = STRIPS[name]
        S = f()
        ts = list(np.linspace(0.0, dur - 1.0 / 60, 8))
        tiles = []
        for t in ts:
            surf, cv = _surface(640, 360)
            cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
            S['draw'](Pen(cv), t); cv.restore()
            tl = cv2.resize(_grab(surf), (320, 180), interpolation=cv2.INTER_AREA)
            cv2.putText(tl, '%s %.1f' % (name if t == 0 else '', t), (5, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tl)
        rows.append(np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]))
        miss = max([m[-1] for a in S.get('actors', []) for m in getattr(a, 'misses', [])], default=0.0)
        feet = [round(max(a.foot_gap(t) for t in ts), 1) for a in S.get('grounded', [])]
        print('%-18s reach miss max %.1f px, foot gaps %s' % (name, miss, feet))
    cv2.imwrite(os.path.join(OUT, 'family_strips_%s.jpg' % g), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])


CHECK = ['adam_window', 'adam_locker', 'adam_step_over', 'adam_tell', 'adam_shoebox', 'mom_hoodie', 'lina_card', 'caretaker_roll']


def render_check(names=None, path=None):
    """4 frames per action, one row each: a quick re-check image after fixes."""
    rows = []
    for name in names or CHECK:
        f, dur = STRIPS[name]
        S = f(); ts = list(np.linspace(0.3, dur - 1.0 / 60, 4)); tiles = []
        for t in ts:
            surf, cv = _surface(640, 360)
            cv.save(); cv.clear(skia.Color(20, 22, 30)); cv.scale(CFG.k, CFG.k)
            S['draw'](Pen(cv), t); cv.restore()
            tl = cv2.resize(_grab(surf), (320, 180), interpolation=cv2.INTER_AREA)
            cv2.putText(tl, '%s %.1f' % (name, t), (5, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tl)
        rows.append(np.hstack(tiles))
        miss = max([m[-1] for a in S.get('actors', []) for m in getattr(a, 'misses', [])], default=0.0)
        feet = [round(max(a.foot_gap(t) for t in ts), 1) for a in S.get('grounded', [])]
        print('%-18s reach miss max %.1f px, foot gaps %s' % (name, miss, feet))
    cv2.imwrite(path or os.path.join(OUT, 'family_check.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
