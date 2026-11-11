"""Cast design sheets for the Mirror Steps film: one PNG per character in _work/cast/.

    python3 tools/cast_sheets.py [names...]      names: you tess noah13 noah_grown queen queen_scary memory (default all)

Every cell is a miniature 1920x1080 design frame (so the plan's `at` values work as they are), drawn at 400x225 (or a
multiple for big cells), with a label. Actions are shown as frames sampled over time from real Acting clips.
"""
import os, sys, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
import skia                                                              # noqa: E402
import characters as C                                                   # noqa: E402
from engine.core import Pen, text                                        # noqa: E402

OUT = os.path.join(FILM, '_work', 'cast')
CW, CH = 400, 225
BG = {'ours': (22, 36, 50), 'theirs': (204, 204, 200), 'mirror': (10, 12, 20), 'memory': (150, 136, 116), 'red': (40, 14, 20),
      'grey': (58, 64, 72)}


class Sheet:
    def __init__(self, title, cols=4):
        self.title, self.cols, self.cells = title, cols, []

    def add(self, label, fn, bg='ours', span=(1, 1)):
        self.cells.append((label, fn, bg, span))

    def render(self, path):
        # simple flow layout: big cells take span[0] columns x span[1] rows
        grid = {}; place = []
        r = c = 0
        for label, fn, bg, (sw, sh) in self.cells:
            while True:
                if c + sw > self.cols: r += 1; c = 0; continue
                if all((r + i, c + j) not in grid for i in range(sh) for j in range(sw)): break
                c += 1
            for i in range(sh):
                for j in range(sw): grid[(r + i, c + j)] = 1
            place.append((r, c, label, fn, bg, sw, sh)); c += sw
        rows = max(k[0] for k in grid) + 1
        W, H = CW * self.cols, CH * rows + 50
        surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(skia.Color(12, 14, 18))
        text(cv, self.title, W / 2, 34, 800, 20, '#ffffff', 255)
        t_all = time.time()
        for r, c, label, fn, bg, sw, sh in place:
            x0, y0, w, h = c * CW, 50 + r * CH, CW * sw, CH * sh
            cv.save(); cv.translate(x0, y0); cv.clipRect(skia.Rect.MakeWH(w - 2, h - 2))
            col = BG.get(bg, BG['ours'])
            p = skia.Paint(Shader=skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, h)],
                                                                [skia.Color(*[min(255, v + 18) for v in col]), skia.Color(*col)]))
            cv.drawRect(skia.Rect.MakeWH(w, h), p)
            cv.save(); cv.scale(w / 1920.0, h / 1080.0)
            try:
                fn(Pen(cv))
            except Exception as e:                                       # keep the sheet going, show the error
                cv.restore(); cv.save()
                text(cv, 'ERR ' + repr(e)[:60], w / 2, h / 2, 700, 12, '#ff5050')
                print('ERR', label, repr(e))
            cv.restore()
            lc = '#101216' if bg in ('theirs', 'memory') else '#ffffff'
            text(cv, label, 8, h - 10, 700, 12, lc, 220, align='left')
            cv.restore()
        surf.makeImageSnapshot().save(path, skia.kPNG)
        print('%s  %dx%d  %.1fs' % (path, W, H, time.time() - t_all))


# ------------------------------------------------------------------ helpers
def bust(who, expr='neutral', t=1.0, scale=0.62, cy=600, cx=960, light='moon', **pose):
    def fn(pen):
        P = C.Pose(expr if expr in C.EXPR else 'neutral', **pose); P.t = t
        C.draw_bust(pen, who, cx, cy, scale, P, light=light, t=t)
    return fn


def body(who, expr='neutral', turn=0.0, light='moon', h=900, x=960, y=1040, t=1.0, **pose):
    def fn(pen):
        P = C.Pose(expr if expr in C.EXPR else 'neutral', turn=turn, **pose); P.t = t
        C.draw(pen, who, x, y, h, P, light=light, t=t)
    return fn


def acted(who, mode, at, build, t, light='moon', expr='neutral', main='r', seed=3):
    """A frame at time t of an Acting built by build(acting) (clips at absolute times), drawn in a plan mode."""
    def fn(pen):
        a = C.Acting(C.WHO_ALIAS.get(who, who), seed=seed, height=at[2] if mode in ('body', 'legs') else 700.0, expr=expr)
        a._at = tuple(at[:3])
        build(a)
        P = a.at(t); P.t = t
        C.draw_mode(pen, C.WHO_ALIAS.get(who, who), mode, at, P, light=light, main=main)
    return fn


def spec_frame(shot_id, t, ci=0, at=None, light='auto'):
    """A frame of a real plan shot (characters only) via CharRig."""
    sh = C.plan_shots()[shot_id]
    rig = C.CharRig(sh['chars'][ci], sh)
    def fn(pen):
        rig.draw(pen, t, at=at, light=light)
    return fn


def frames(sheet, label, mk, ts, bg='ours'):
    for k, t in enumerate(ts):
        sheet.add('%s  %d/%d  t=%.2f' % (label, k + 1, len(ts), t), mk(t), bg)


# ------------------------------------------------------------------ sheets
def sheet_you():
    S = Sheet('YOU  (you)  -  27, looks like Dad: olive work jacket, corduroy collar, stubble')
    S.add('bust front (moon)', bust('you', 'neutral', scale=0.95, cy=560), span=(2, 2))
    S.add('bust 3/4 (flashlight key)', bust('you', 'grief', scale=0.95, cy=560, light='flashlight', h_turn=0.45, turn=0.2), span=(2, 2))
    for k, (tv, lt, bg) in enumerate(((0.0, 'moon', 'ours'), (-0.5, 'flashlight', 'ours'), (1.0, 'dawn', 'theirs'), (2.0, 'red', 'red'))):
        S.add('turn %s  light %s' % (tv, lt), body('you', 'neutral', tv, lt), bg)
    for e in ('neutral', 'grief', 'fear', 'shock', 'dread', 'tense', 'tempted', 'resolve', 'shout', 'wonder', 'relief_cry', 'scream'):
        S.add('expr ' + e, bust('you', e, scale=0.8, cy=560, h_turn=0.15 if e in ('tempted', 'grief') else 0.0))
    frames(S, 'tears (grief)', lambda t: acted('you', 'bust', [960, 560, 0.8], lambda a: (a.expr('grief', 0.0), a.tears(0.3, 1.0)), t), [0.4, 1.4, 2.6])
    S.add('candy fist, left hand (bust)', acted('you', 'bust', [960, 520, 0.6], lambda a: (a.expr('grief', 0), a.set(0, None, 0.1, hl_shape='fist', hl_out=-60, hl_down=150, hl_fwd=240)), 1.0))
    frames(S, 'touch_glass + nail_tap', lambda t: acted('you', 'hands', [960, 560, 420], lambda a: (a.touch_glass(0.2), a.nail_tap(1.2)), t, expr='fear'), [0.25, 0.7, 1.16])
    frames(S, 'grip_frame (will not open)', lambda t: acted('you', 'hands', [960, 600, 380], lambda a: a.grip_frame(0.0, 1.0, True, t1=3.0), t, expr='fear'), [0.4, 0.85])
    frames(S, 'wipe_glass towel', lambda t: acted('you', 'hands', [960, 540, 420], lambda a: a.wipe_glass(0.2, 3, 'down', prop='towel'), t), [0.3, 0.55, 0.8])
    frames(S, 'take candy, fist, open_fist', lambda t: acted('you', 'hands', [960, 600, 440], lambda a: (a.take(0.0, 'candy_red'), a.fist(0.6, slow=True), a.open_fist(2.4, 1.4)), t, main='l'), [0.35, 1.2, 3.0, 3.9])
    frames(S, 'yanked_back (by the collar)', lambda t: acted('you', 'body', [900, 1040, 860], lambda a: (a.expr('fear', 0), a.yanked_back(0.3)), t), [0.3, 0.45, 0.8])
    frames(S, 'squeeze_through', lambda t: acted('you', 'body', [700, 1040, 860], lambda a: a.squeeze_through(0.0, 1.0, 1.2), t), [0.3, 0.7])
    S.add('feet on the step (S276)', spec_frame('S276', 605.0, 0), 'mirror')
    S.add('no jacket (from 635.06)', body('you', 'relief_cry', 0.0, 'red', jacket_off=1.0), 'red')
    return S


def sheet_tess():
    S = Sheet('TESS  (tess)  -  auburn low ponytail, freckles, burnt-orange rain shell, the flashlight')
    S.add('bust front', bust('tess', 'brave', scale=0.95, cy=560), span=(2, 2))
    S.add('bust 3/4 (flashlight)', bust('tess', 'tense', scale=0.95, cy=560, light='flashlight', h_turn=-0.45, turn=-0.2), span=(2, 2))
    for k, (tv, lt, bg) in enumerate(((0.0, 'moon', 'ours'), (0.5, 'flashlight', 'ours'), (-1.0, 'moon', 'ours'), (2.0, 'red', 'red'))):
        S.add('turn %s  light %s' % (tv, lt), body('tess', 'brave', tv, lt, hr_prop='flashlight', hr_shape='grip', hr_out=20.0, hr_down=150.0, hr_fwd=250.0, hr_rot=90.0), bg)
    for e in ('neutral', 'brave', 'tense', 'recognise', 'half_smile', 'fear', 'sad', 'shock', 'resolve', 'shout', 'angry', 'puzzled'):
        S.add('expr ' + e, bust('tess', e, scale=0.8, cy=560))
    frames(S, 'flashlight sweep', lambda t: acted('tess', 'body', [960, 1040, 880], lambda a: a.flashlight(0.0, 0.0, 0.9, True, True), t, expr='tense'), [0.2, 0.9, 1.6])
    frames(S, 'unlock + pull_chain', lambda t: acted('tess', 'hands', [960, 560, 300], lambda a: (a.unlock(0.0), a.pull_chain(1.4)), t), [0.3, 0.75, 1.8])
    frames(S, 'grab_collar + pull', lambda t: acted('tess', 'body', [900, 1040, 880], lambda a: (a.expr('shout', 0), a.grab_collar(0.2)), t), [0.2, 0.45, 0.9])
    frames(S, 'wind_up + strike the bell', lambda t: acted('tess', 'body', [960, 1040, 880], lambda a: (a.expr('angry', 0), a.wind_up(0.0), a.strike(0.6)), t), [0.4, 0.68, 0.9])
    frames(S, 'kick (legs, profile)', lambda t: acted('tess', 'legs', [960, 1040, 1300], lambda a: (a.set(-1e9, None, 0.01, turn=1.0), a.kick(0.5)), t), [0.35, 0.6])
    frames(S, 'set_down phone face up', lambda t: acted('tess', 'hands', [960, 560, 340], lambda a: a.set_down(0.0, 'phone'), t), [0.2, 0.5, 0.8])
    S.add('hand_to_mouth (shock)', acted('tess', 'bust', [960, 560, 0.75], lambda a: (a.expr('fear', 0), a.hand_to_mouth(0.0, 3.0)), 1.0))
    S.add('finger_to_lips', acted('tess', 'bust', [960, 560, 0.75], lambda a: (a.expr('tense', 0), a.finger_to_lips(0.0, 3.0)), 1.0))
    return S


def sheet_noah13():
    S = Sheet('NOAH AT 13  (noah13)  -  cowlick, freckles, gap teeth, CEDAR LAKE sweatshirt, one shoe, taped fingers')
    S.add('bust front (dawn)', bust('noah13', 'grin_kid', scale=0.95, cy=560, light='dawn'), 'theirs', span=(2, 2))
    S.add('bust 3/4 talking (dawn)', bust('noah13', 'grin_kid', scale=0.95, cy=560, light='dawn', h_turn=0.3, turn=0.15, m_open=0.3), 'theirs', span=(2, 2))
    for k, (tv, lt, bg) in enumerate(((0.0, 'dawn', 'theirs'), (0.5, 'dawn', 'theirs'), (-1.0, 'moon', 'mirror'), (2.0, 'red', 'red'))):
        S.add('turn %s  light %s' % (tv, lt), body('noah13', 'calm_kid', tv, lt, h=760), bg)
    for e in ('calm_kid', 'grin_kid', 'laugh', 'listening', 'neutral', 'puzzled', 'relief', 'shy', 'sleep', 'strain', 'worried', 'scream'):
        S.add('expr ' + e, bust('noah13', e, scale=0.8, cy=560, light='dawn'), 'theirs')
    frames(S, 'tie_loop (hands, 2.4 s cycle)', lambda t: acted('noah13', 'hands', [960, 560, 380], lambda a: a.tie_loop(0.0, 2.4, 0.0, 10.0), t, light='dawn'), [0.3, 1.2, 2.1], 'theirs')
    frames(S, 'tie_loop (body, sat on the bunk)', lambda t: acted('noah13', 'body', [960, 1000, 700], lambda a: a.tie_loop(0.0, 2.4, 0.0, 10.0), t, light='dawn', expr='calm_kid'), [0.5, 1.6], 'theirs')
    frames(S, 'look_up: the gap-tooth smile', lambda t: acted('noah13', 'bust', [960, 560, 0.8], lambda a: (a.expr('calm_kid', 0), a.set(0, None, 0.1, h_nod=0.25, look_y=0.5), a.look_up(0.4)), t, light='dawn'), [0.2, 1.4], 'theirs')
    frames(S, 'face_flash (grown face, 0.5 s)', lambda t: acted('noah13', 'bust', [960, 560, 0.8], lambda a: (a.expr('calm_kid', 0), a.face_flash(0.5, 0.5)), t, light='dawn'), [0.3, 0.7], 'theirs')
    frames(S, 'hold_out candy', lambda t: acted('noah13', 'hands', [900, 600, 420], lambda a: a.hold_out(0.0, 'candy_red'), t, light='dawn'), [0.2, 0.8], 'theirs')
    frames(S, 'peel_tape / slip_tape', lambda t: acted('noah13', 'hands', [960, 580, 460], lambda a: (a.peel_tape(0.0, 2), a.slip_tape(1.2)), t, light='dawn', expr='strain'), [0.25, 1.45, 1.9], 'theirs')
    frames(S, 'draw_step (lipstick)', lambda t: acted('noah13', 'hands', [1180, 330, 260], lambda a: a.draw_step(0.2, 1), t, light='flashlight'), [0.15, 0.5], 'mirror')
    S.add('step_through (feet)', acted('noah13', 'feet', [960, 900, 700], lambda a: a.step_through(0.0), 0.35, light='dawn'), 'theirs')
    S.add('lying asleep, watch wrist (S040)', acted('noah13', 'lying', [960, 560, 900], lambda a: (a.expr('sleep', 0), a.breathe_sleep(0)), 1.0, light=None), 'memory')
    S.add('hand_jerk (S159)', spec_frame('S159', 358.6, 0), 'theirs')
    return S


def sheet_noah_grown():
    S = Sheet('NOAH GROWN  (noah_grown)  -  the same face at 27, gap teeth, sweatshirt two sizes too small, big shaking hands')
    S.add('bust front (red)', bust('noah_grown', 'shaken', scale=0.95, cy=560, light='red'), 'red', span=(2, 2))
    S.add('bust 3/4, your jacket on (red)', bust('noah_grown', 'relief_cry', scale=0.95, cy=560, light='red', h_turn=0.4, turn=0.2, jacket_on=1.0), 'red', span=(2, 2))
    for k, (tv, lt, bg) in enumerate(((0.0, 'red', 'red'), (0.5, 'moon', 'ours'), (1.0, 'red', 'red'), (2.0, 'moon', 'ours'))):
        S.add('turn %s  light %s' % (tv, lt), body('noah_grown', 'shaken', tv, lt, h=960), bg)
    for e in ('shaken', 'fear', 'hopeful', 'relief_cry'):
        S.add('expr ' + e, bust('noah_grown', e, scale=0.8, cy=560, light='red'), 'red')
    frames(S, 'age morph: face (S253)', lambda t: acted('noah_grown', 'bust', [960, 560, 0.85], lambda a: (a.expr('shaken', 0), a.age(0.0, 1.6, 'face', 0.0), a.age(0.0, 1.6, 'arms', 0.0)), t, light='red'), [0.0, 0.8, 1.6], 'red')
    frames(S, 'age morph: arms, cuffs ride up (S252)', lambda t: acted('noah_grown', 'hands', [960, 600, 460], lambda a: (a.age(0.0, 1.5, 'arms', 0.0), a.look_at_hands(0.0)), t, light='red'), [0.1, 0.8, 1.5], 'red')
    frames(S, 'cover_ears', lambda t: acted('noah_grown', 'bust', [960, 600, 0.7], lambda a: (a.expr('fear', 0), a.cover_ears(0.2, 2.0)), t, light='red'), [0.1, 0.6], 'red')
    S.add('shaking hands beside yours (S257)', lambda pen: (spec_frame('S257', 570.5, 0)(pen), spec_frame('S257', 570.5, 1)(pen)), 'red')
    S.add('jacket on the shoulders (body)', body('noah_grown', 'relief_cry', 0.0, 'moon', h=960, jacket_on=1.0, t=640.0))
    frames(S, 'stand_hit (the bunk)', lambda t: acted('noah_grown', 'body', [960, 1040, 900], lambda a: (a.expr('shaken', 0), a.set(-1e9, None, 0.01, sit=1.0), a.stand_hit(0.2)), t, light='red'), [0.2, 0.62], 'red')
    return S


def _queen_build(stage, face=None, crop=None):
    def b(a):
        spec = dict(who='queen', stage=stage, face=face, crop=crop, mode='bust')
        d = dict(hair_over=0.0, eye_gap=0.0, m_gap=0.0)
        if stage <= 2 or face in ('hidden', 'mouth_only'): d['hair_over'] = 1.0
        if stage == 1: d['eye_gap'] = 1.0
        if face == 'mouth_only': d['m_gap'] = 1.0
        a.set(-1e9, None, 0.01, **d); a.life(-1e9, None, 0.0)
    return b


QL = dict(rim='#ff4060', rim_a=110, side=-1, key=-0.25)


def sheet_queen():
    S = Sheet('THE QUEEN OF SPADES  (queen)  -  no outline: pale scratch edges, lipstick red with the widest glow, uncanny stillness')
    S.add('stage 3: the full face', acted('queen', 'bust', [960, 560, 0.95], lambda a: (_queen_build(3)(a), a.expr('queen_grin', 0), a.head_tilt(0, 24, 0.01)), 1.0, light=QL, expr='queen_grin'), 'mirror', span=(2, 2))
    S.add('stage 2: mouth only', acted('queen', 'bust', [960, 520, 0.95], lambda a: (_queen_build(2, 'mouth_only')(a), a.expr('queen_soft', 0)), 1.0, light=QL, expr='queen_soft'), 'mirror', span=(2, 2))
    S.add('stage 0: back, hair, dress, feet', acted('queen', 'body', [960, 1040, 980], lambda a: (_queen_build(0)(a), a.set(-1e9, None, 0.01, turn=2.0)), 1.0, light=QL, expr='queen_still'), 'mirror')
    S.add('stage 1: one eye through the hair', acted('queen', 'bust', [960, 560, 0.75], lambda a: _queen_build(1)(a), 1.0, light=QL, expr='queen_stare'), 'mirror')
    S.add('stage 2: hair over the face', acted('queen', 'body', [960, 1040, 980], lambda a: _queen_build(2, 'hidden')(a), 1.0, light=QL, expr='queen_still'), 'mirror')
    S.add('3/4 body, stage 3 (dawn)', acted('queen', 'body', [960, 1040, 980], lambda a: (_queen_build(3)(a), a.set(-1e9, None, 0.01, turn=0.4)), 1.0, light='dawn', expr='queen_soft'), 'theirs')
    for e in ('queen_still', 'queen_stare', 'queen_soft', 'queen_call', 'queen_grin', 'queen_blank'):
        S.add('expr ' + e, acted('queen', 'bust', [960, 560, 0.8], lambda a, e=e: (_queen_build(3)(a), a.expr(e, 0)), 1.0, light=QL, expr=e), 'mirror')
    frames(S, 'head_snap 130 deg (S089: back -> over the shoulder)', lambda t: acted('queen', 'body', [960, 1040, 980], lambda a: (_queen_build(0)(a), a.set(-1e9, None, 0.01, turn=2.0), a.head_snap(0.5, 130, 0.18)), t, light=QL, expr='queen_stare'), [0.45, 0.6, 0.8], 'mirror')
    frames(S, 'smile_off (2 frames)', lambda t: acted('queen', 'bust', [960, 560, 0.8], lambda a: (_queen_build(3)(a), a.expr('queen_grin', 0), a.smile_off(0.5)), t, light='dawn', expr='queen_grin'), [0.49, 0.52], 'theirs')
    frames(S, 'sit_beside (one smooth motion)', lambda t: acted('queen', 'body', [960, 1040, 980], lambda a: (_queen_build(2, 'hidden')(a), a.sit_beside(0.2, 0.5)), t, light='dawn', expr='queen_still'), [0.2, 0.45, 0.75], 'theirs')
    frames(S, 'press_through_cloth', lambda t: acted('queen', 'hands', [960, 520, 380], lambda a: a.press_through_cloth(0.0, 1.0), t, light=QL), [0.2, 1.2], 'mirror')
    frames(S, 'feet: step_up, toes_curl', lambda t: acted('queen', 'feet', [960, 900, 800], lambda a: (a.step_up(0.8), a.toes_curl(1.2)), t, light=QL), [0.3, 0.9, 2.2], 'mirror')
    S.add('S276: her foot below yours', lambda pen: (spec_frame('S276', 605.0, 0)(pen), spec_frame('S276', 605.0, 1)(pen)), 'mirror')
    S.add('call_silent', acted('queen', 'bust', [960, 560, 0.8], lambda a: (_queen_build(3)(a), a.call_silent(0.0, 1.2)), 0.8, light=QL, expr='queen_still'), 'mirror')
    S.add('climb (silhouette, S004)', spec_frame('S004', 5.9, 0), 'mirror')
    S.add('pat beside Noah (hands)', acted('queen', 'hands', [960, 640, 440], lambda a: a.pat(0.0, 2, 0.32), 0.15, light='dawn'), 'theirs')
    return S


def sheet_queen_scary():
    S = Sheet('THE QUEEN - SCARIEST FRAMES (S128 / S212 / S316, S089, S237, S278)', cols=4)
    S.add('S128 283.9  "There\'s time for both of you"', spec_frame('S128', 284.9, 0, light=QL), 'mirror', span=(2, 2))
    S.add('S212 480.6  "I can put you back..." head tilt', spec_frame('S212', 480.9, 0, light='dawn'), 'theirs', span=(2, 2))
    S.add('S089 198.3  head snap: now she is listening to you', acted('queen', 'bust', [960, 560, 0.75], lambda a: (_queen_build(1)(a), a.set(-1e9, None, 0.01, turn=2.0), a.head_snap(0.5, 160, 0.18)), 0.9, light=QL, expr='queen_stare'), 'mirror', span=(2, 2))
    S.add('S237 532.95  the smile goes off her face', acted('queen', 'bust', [960, 560, 0.8], lambda a: (_queen_build(3)(a), a.expr('queen_grin', 0), a.smile_off(0.5), a.head_tilt(0, 26, 0.01)), 0.6, light='dawn', expr='queen_grin'), 'theirs', span=(2, 2))
    S.add('S316 697.2  in the phone', spec_frame('S316', 697.3, 0, light=dict(rim='#ff4060', rim_a=140, side=-1, key=-0.45)), 'mirror', span=(2, 2))
    S.add('S278  toes curl over the step below yours', spec_frame('S278', 607.3, 0, light=QL), 'mirror', span=(2, 2))
    return S


def sheet_memory():
    S = Sheet('MEMORY CAST  (you_kid, counselor, kid_a/b/c, director, cook, searcher, adult)  -  memory grade off')
    S.add('you_kid bust', bust('you_kid', 'happy', scale=0.95, cy=560, light=None), 'memory', span=(2, 2))
    S.add('you_kid body turns', lambda pen: [C.draw(pen, 'you_kid', 400 + k * 380, 1040, 760, C.Pose('neutral', turn=tv), light=None, t=1.0)
                                             for k, tv in enumerate((0.0, 0.5, 1.0, 2.0))], 'memory', span=(2, 2))
    for e in ('happy', 'laugh', 'sad', 'shock', 'sleep', 'sly', 'sure'):
        S.add('you_kid ' + e, bust('you_kid', e, scale=0.8, cy=560, light=None), 'memory')
    S.add('you_kid lying, wake_squint', acted('you_kid', 'lying', [960, 560, 900], lambda a: (a.expr('sleep', 0), a.wake_squint(0.2)), 1.2, light=None), 'memory')
    S.add('press_button on the watch', acted('you_kid', 'hands', [960, 640, 300], lambda a: a.press_button(0.3, 2), 0.32, light=None, expr='sly'), 'memory')
    frames(S, 'counselor ring_bell', lambda t: acted('counselor', 'body', [960, 1040, 900], lambda a: a.ring_bell(0.0), t, light=None), [0.1, 0.35], 'memory')
    S.add('counselor drop_prop (legs)', acted('counselor', 'legs', [960, 1040, 1300], lambda a: (a.expr('shock', 0), a.drop_prop(0.5)), 0.4, light=None), 'memory')
    S.add('kids: a/b/c', lambda pen: [C.draw(pen, w, 500 + k * 460, 1040, 720, C.Pose('giggle'), light=None, t=1.0) for k, w in enumerate(('kid_a', 'kid_b', 'kid_c'))], 'memory')
    S.add('extras: director, cook, adult', lambda pen: [C.draw(pen, w, 500 + k * 460, 1040, 860, C.Pose('neutral'), light=None, t=1.0) for k, w in enumerate(('director', 'cook', 'adult'))], 'memory')
    S.add('search line (silhouettes)', lambda pen: [C.draw_silhouette(pen, 'searcher', 300 + k * 330, 900, 420, C.Pose('shout', turn=0.3 * (k % 2)), light='moon', t=1.0)
                                                    for k in range(5)], 'ours')
    return S


SHEETS = dict(you=sheet_you, tess=sheet_tess, noah13=sheet_noah13, noah_grown=sheet_noah_grown, queen=sheet_queen,
              queen_scary=sheet_queen_scary, memory=sheet_memory)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(SHEETS)
    for n in names:
        SHEETS[n]().render(os.path.join(OUT, 'cast_%s.png' % n))
