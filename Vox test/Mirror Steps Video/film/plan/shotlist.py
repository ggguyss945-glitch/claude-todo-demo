"""plan/shotlist.py (v2): the director's shot list for "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH".

The contract is DIRECTION_V2.md; PLAN_V2.md documents every field this table produces (make_plan.py -> shots.json) and maps
the 33 v1 errors to the shots that fix them. v1's list is kept in plan/v1/shotlist_v1.py.

Conventions
- Every shot starts at a cut time built from the timeline (T, Wc, w) and ends where the next starts. The picture leads the
  voice by 0.17 s on clause starts; action cuts sit on the action (the hit, the snap, the drop).
- X(t0, typ, world, 'set/view', var, frame, cam, **kw). typ: EWS WS SEC (wides) | MS OTS 2S (mids) | MCU CU ECU (faces only)
  | INSERT DOC DIAGRAM SPLIT UI TYPE MONTAGE (inserts) | POV (your hands or feet in frame) | CARD BLACK.
- world: ours stairs theirs theirs_break memory climax ending ui card black (the look; side follows).
- cam: P(r) push r %/s, SIL() the 1.5 %/s silence push, FA(r) fast push, PU(r) pull, RV(r) reveal pull, DR drift, TR track,
  HH handheld, CRN crane, ORB orbit, WH whip, TL tilt. x, y = design point at frame centre; z = zoom; snap=(t, k) punch-in;
  hit=[(t, px)] camera jolt; roll = dutch degrees.
- chars: bust/body/hands/feet/Q helpers below (C() underneath). Q(stage, ...) is the Queen at a ladder stage.
- q=dict(stage, step, size, where, framing, wrong): the Queen's ladder entry for this appearance (DIRECTION_V2 2.4).
- hold='H1'..'H10' (the only shots over 2.5 s with the cards and the time card); reuse=<time of the earlier shot> (setup
  reuse, resolved to an id); errfix=[n] (section 6 numbers); device=dict(kind, id, what) (inserts / documents / diagrams that
  teach a noun or a mechanism, counted per minute); teaser='RULE 2' (flash-forwards); split / plate / montage (see PLAN_V2.md).
- STATE(t, ...) changes the running prop state; every shot gets the state at its t0 plus the changes inside it.
"""
from dsl import (S, X, SHOTS, cam, C, A, fx, M, tag, label, redx, R, t, e, w, w0, T, Wc, LINES, DUR, chip, teaser, kinetic, typebeat,
                 giant, diagram, doc, count_pop, stamp, highlight, mapins, level_guide, rings, eye_line, dials)

STATES = []
MERGES = []


def STATE(at, **kw):
    STATES.append((at, kw))


def MERGE(ta, tb, **kw):
    """Flow over cut count (owner's v2 verdict, critic round 1): the shots starting in [ta, tb) become ONE continuous shot
    whose camera passes through each old framing on one eased move (make_plan.apply_merges). Options: keep=[t0 of a
    cutaway kept as a cut, the move resumes after it], path=[(t, x, y, z[, roll]), ...] (an explicit 2D move),
    cam3=[[t, view | {view, pos, look, fov, dp, dl}], ...] (a travelling move through the 3D room), travel=True (views of a
    non-room set as 3D keys, e.g. the mirror), flat=True (never travel: keep the first view), glide=[v0, v1, ramp] (the
    speed at the ends), accel=[[t, factor, dur]] (an eased push acceleration on a beat), chars=[...] (the cast of the
    merged shot, when the old shots' cast cannot simply be joined), frame='...', set_={field: value} (any shot field), tr,
    join (how a place change inside the group joins: 'flow' travel dissolve by default), flow_at=[x, y] (where the
    camera goes through on a flow), resume_tr, cutaway_tr."""
    MERGES.append(dict(ta=float(ta), tb=float(tb), **kw))


def FLAG(t0, **kw):
    """Set fields on the shot that starts at t0 (e.g. match_action=True: the cut continues an action across the same set-up)."""
    MERGES.append(dict(flag_t=float(t0), fields=kw))


def DROP(t0):
    """A shot the continuous move no longer needs: the shot before it runs on over its time (its cues and HUD move there)."""
    MERGES.append(dict(drop_t=float(t0)))


# ================================================================================================= shorthand
def P(r=3.0, **k): return cam('push', rate=r / 100.0, **k)
def SIL(r=1.5, **k): return cam('push', rate=r / 100.0, silence=True, **k)
def FA(r=7.0, **k): return cam('fast', rate=r / 100.0, **k)
def PU(r=3.0, **k): return cam('pull', rate=-r / 100.0, **k)
def RV(r=8.0, **k): return cam('reveal', rate=-r / 100.0, **k)
def DR(r=2.0, dx=30, **k): return cam('drift', rate=r / 100.0, dx=dx, **k)
def TR(dx=70, r=1.0, **k): return cam('track', rate=r / 100.0, dx=dx, **k)
def HH(r=2.5, shake=18, **k): return cam('hand', rate=r / 100.0, shake=shake, **k)
def CRN(dy=-25, r=2.5, **k): return cam('crane', rate=r / 100.0, dy=dy, **k)
def ORB(dx=30, r=2.0, **k): return cam('orbit', rate=r / 100.0, dx=dx, **k)
def TL(dy=-90, r=2.0, **k): return cam('tilt', rate=r / 100.0, dy=dy, **k)
def WH(x1, y1, z1=1.1, **k): return cam('whip', x1=x1, y1=y1, z1=z1, **k)


# lights (the cast is lit by its world; DIRECTION_V2 1.2, 3.6)
L_OURS = dict(rim='#9fa8ff', rim_a=80, side=1, key=-0.15, flash='tess', world='ours')
L_BEAM = dict(rim='#ffd58a', rim_a=110, side=-1, key=0.1, flash='tess', world='ours')
L_GOLD = dict(rim='#ffe2a8', rim_a=100, side=-1, key=0.35, world='theirs')
L_STAIRS = dict(rim='#9fa8ff', rim_a=70, side=1, key=-0.05, under='#ffcf8a', world='stairs')
L_RED = dict(rim='#ff3b5c', rim_a=150, side=-1, key=-0.2, world='climax')
L_MEM = dict(rim='#f1e2c4', rim_a=60, side=1, key=0.2, world='memory')
L_PHONE = dict(rim='#9fa8ff', rim_a=60, side=1, key=-0.3, under='#bcd2ff', world='ours')
L_END = dict(rim='#9fa8ff', rim_a=80, side=1, key=-0.1, under='#f0a84e', world='ending')
L_QUEEN = dict(key_c='#e8ecff', key_from='below_front', rim='#ff3b5c', rim_a=140, bloom=1.5, drain_px=450)


def bust(who, x=960, y=560, s=1.0, view='q_left', expr='neutral', acts=(), light=None, **ex):
    return C(who, [x, y, s], view, expr, acts, mode='bust', light=light, **ex)


def body(who, x, yf, h, view='front', expr='neutral', acts=(), d=None, **ex):
    return C(who, [x, yf, h] + ([d] if d else []), view, expr, acts, mode='body', **ex)


def hands(who, x=960, y=560, size=460, acts=(), view='front', **ex):
    return C(who, [x, y, size], view, 'neutral', acts, mode='hands', **ex)


def feet(who, x=960, y=900, size=900, acts=(), view='front', **ex):
    return C(who, [x, y, size], view, 'neutral', acts, mode='feet', **ex)


def Q(stage, at, mode='bust', acts=(), view='front', expr=None, **ex):
    ex.setdefault('light', L_QUEEN)
    return C('queen', at, view, expr or {'S0': 'queen_still', 'S1': 'queen_soft', 'S2': 'queen_drawn', 'S3a': 'queen_grin',
                                         'S3b': 'queen_grin_red', 'S3c': 'queen_full', 'OFF': 'queen_off', 'S4': 'queen_void'}[stage],
             acts, mode=mode, stage=stage, **ex)


def POVH(acts, x=960, y=600, size=520, **ex):
    """Your POV hand: the consistent olive sleeve (#4a5038, stitched cuff #33382a), DIRECTION_V2 3.7."""
    return C('you', [x, y, size], 'front', 'neutral', acts, mode='hands', pov=True, sleeve='olive', **ex)


def Fist(x=960, y=620, size=460, acts=(), **ex):
    """Your LEFT candy fist (323.65-649 s): white knuckles, the red wrapper twist always visible between the fingers."""
    return C('you', [x, y, size], 'front', 'neutral', [A(R(0), 'fist', hand='left', candy=True)] + list(acts), mode='hands',
             hand='left', fist=True, **ex)


def DEV(kind, did, what): return dict(kind=kind, id=did, what=what)


# the rule cards (times unchanged: 0.45 s before "Rule", cut 0.15 s after the sentence; DIRECTION_V2 5.3)
RULE_TEXT = {
    1: "*Count the steps* with your finger.",
    2: "If you see her face, *keep your wishes to yourself*.",
    3: "*Leave somebody* on your side of the glass.",
    4: "Ask *what he wished for*.",
    5: "Ring the *real* bell.",
    6: "Let him go *first*.",
    7: "*Cover* anything else that can reflect the stairs.",
}
RULE_CMD = {1: 'COUNT THE STEPS', 2: 'KEEP YOUR WISHES TO YOURSELF', 3: 'LEAVE SOMEBODY', 4: 'WHAT HE WISHED FOR', 5: 'REAL',
            6: 'FIRST', 7: 'COVER'}
RULE_LINES = {1: (47, 48), 2: (78, 79), 3: (104, 105), 4: (138, 139), 5: (181, 182), 6: (225, 226), 7: (259, 260)}
RULE_BG = {1: ('cabin_now', 'ots_mirror', 'night', 'ours'), 2: ('mirror', 'glass_wide', 'night', 'ours'),
           3: ('cabin_now', 'master', 'doorway_glow', 'ours'), 4: ('cabin_dawn', 'master', 'dawn', 'theirs'),
           5: ('cabin_dawn', 'reverse', 'dawn_queen', 'theirs'), 6: ('cabin_dawn', 'master', 'dawn_break', 'theirs_break'),
           7: ('cabin_now', 'dutch_low', 'red', 'climax')}
CARD_QUEEN = {1: dict(size=0.09, pose='tiny figure on the bottom step', stage='S0'),
              2: dict(size=0.16, pose='head turned toward the lens', stage='S1'),
              3: dict(size=0.25, pose='standing in gold doorway light', stage='S1'),
              4: dict(size=0.30, pose='seated, hands in her lap', stage='S2'),
              5: dict(size=0.45, pose='the S2 drawn smile', stage='S2'),
              6: dict(size=0.65, pose='red eyes', stage='S3b'),
              7: dict(size=0.90, pose='the S3c face filling the glass', stage='S3c')}
CARD_GLASS = {1: 'clean silver', 2: 'clean silver', 3: 'gold reflection', 4: 'gold reflection', 5: 'a hairline crack',
              6: 'three cracks, 30 % red tint', 7: 'graded red, steps glowing'}


def card_times(n):
    li, ti = RULE_LINES[n]
    return round(w(li, 'Rule') - 0.45, 3), round(e(ti) + 0.15, 3)


def RULE(n):
    """The rule card is the mirror itself (DIRECTION_V2 5.3): static glitch (2 frames), the orange-striped towel whips up and
    out (0.30 s), the mirror card settles (62 % of W, -2 deg, 4 % overshoot in 0.13 s); RULE is written in lipstick by a
    visible bullet tip at t0 + 0.45 in 0.35 s, the numeral stamps in at 1.6x -> 1.0 in 0.13 s throwing crumbs; the statement
    writes word-synced in off-white grease pencil, the command in lipstick red with an underline swipe at the sentence end;
    a masking-tape label NOAH'S · CABIN 7 on the frame's top edge; the 7-step progress staircase bottom right with step n
    filled; her reflection behind the words, closer each card; the glass degrades; LIKE / SUBSCRIBE with a cursor on 1-2;
    finger-wipe exit at the sentence end, carried 0.2 s over the next shot."""
    li, ti = RULE_LINES[n]
    t0, t1 = card_times(n)
    words = [[wd, tt] for wd, tt in LINES[ti]['words'] if tt is not None]
    bg = RULE_BG[n]
    hud = [dict(t=t0, type='rule_card', n=n, text=RULE_TEXT[n], command=RULE_CMD[n],
                title='RULE ' + ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN'][n - 1],
                appear=t0, glitch=[t0, round(t0 + 2 / 60, 3)], towel_whip=[t0, round(t0 + 0.30, 3)],
                card=dict(width_w=0.62, rot=-2.0, overshoot=0.04, settle=0.13),
                rule_write=[round(t0 + 0.45, 3), round(t0 + 0.80, 3)], numeral_stamp=dict(t=round(t0 + 0.80, 3), scale0=1.6, settle=0.13, crumbs=True),
                title_at=round(t0 + 0.45, 3), words=words, underline_at=round(e(ti) - 0.12, 3),
                tape_label="NOAH'S · CABIN 7", steps_progress=n, reflection=CARD_QUEEN[n], glass=CARD_GLASS[n],
                wipe_out=round(e(ti), 3), wipe_carry=0.2, end=t1, captions=False)]
    if n <= 2:
        hud.append(dict(t=round(t0 + 1.2, 3), type='like_sub', hold=round(t1 - t0 - 1.4, 2), cursor=True,
                        clicks=['like', 'subscribe', 'bell']))
    # music events for the cards (riser, rule sting, swell) are carried over unchanged from the v1 sound plan (make_plan.py)
    X(t0, 'CARD', 'card', 'rule_mirror/card', bg[2],
      'the rule card is the mirror: towel whips off, RULE in lipstick, numeral %d stamps in; her reflection %d %% of the glass '
      '(%s); glass: %s; over the live plate %s/%s blurred 8, dimmed 30 %%' % (n, CARD_QUEEN[n]['size'] * 100, CARD_QUEEN[n]['pose'],
                                                                         CARD_GLASS[n], bg[0], bg[1]),
      P(2), bg=dict(set=bg[0], view=bg[1], var=bg[2], world=bg[3], post=dict(blur=8, dim=0.30)), hud=hud, tr='flow', flow=[960, 520],
      captions=False, card=n,
      q=dict(stage=CARD_QUEEN[n]['stage'], size=CARD_QUEEN[n]['size'], where='reflection behind the card words',
             framing='card %d' % n, wrong=CARD_QUEEN[n]['pose']),
      energy='towel whip off, lipstick bullet writing, numeral stamp with crumbs, words writing on, her reflection drifting '
             'closer 2 px/s behind the words, plate figures moving under the blur, camera push 2 %/s')
    return t1


# =================================================================================================================
# INITIAL PROP STATE (make_plan.py starts from this; PLAN_V2.md "Props")
STATE(0.0, steps_drawn=7, eighth='none', smeared=0, erased=0, mirror='hook_glass', doorway='none', towel='wrapped',
      flashlight='off', fist='none', candy='none', tape='on', shoe='left_on_lace_loose', jacket='you', padlock='hasp_locked',
      keys='tess_pocket', gate_padlock='locked', phone='tess_pocket', your_phone='pocket', bell='crate', drop='none',
      sprinkler='off', clock='running', queen='hook_flash', noah='theirs_bunk', tess='with_you', you='ours')

# ================================================================ HOOK 0 - 19.26 (lines 0-6): 20 shots, 24 cuts by 30 s
X(0.0, 'ECU', 'climax', 'stairs/queen_ecu', 'red',
  'FLASH-FORWARD (605 s): the Queen at S3c inside the glass, face 120 % of H, the chipped white frame edge on the left; red '
  'teaser border, chip RULE 6; she is looking into the lens', FA(9, x=960, y=500, z=1.15),
  chars=[Q('S3c', [980, 520, 1.25], acts=[A(R(0), 'grin_widen', amount=0.2), A(R(0.05), 'stare')])],
  hud=[teaser(0.0, 'RULE 6'), chip(0.0, 'RULE 6', 'teaser')], teaser='RULE 6', tr='cut',
  q=dict(stage='S3c', size=1.2, where='glass (flash-forward of 605 s)', framing='ECU', wrong='(teaser)'),
  fx_post=[dict(t=0.36, glitch=0.9, static=0.5, dur=0.06)],
  energy='grin widening 3 px/frame, red pulse, fast push 9 %/s, glitch out at 0.36')
STATE(0.42, queen='absent')
STATE(2.56, eighth='present')
X(0.42, 'INSERT', 'ours', 'mirror/glass_cu', 'night',
  'a taped kid hand (green CEDAR LAKE cuff, the one blue tape design: middle, ring and little fingers, two bands, lifting edge) '
  'draws steps 6 and 7 in lipstick on the glass; the flashlight hot spot blooms on the silvering; a faint reflection of the '
  'hand moves the opposite way (it is glass)', P(3.5, x=1060, y=420, z=1.05),
  chars=[hands('noah13', 1160, 360, 300, [A(0.56, 'draw_step', step=6), A(0.88, 'draw_step', step=7), A(1.5, 'withdraw')],
               tape=True, reflection=True, note='kid hand only, no face')],
  props=dict(steps_drawn='5 -> 7 (drawn at 0.56 and 0.88)'), tr='glitch', errfix=[14, 33],
  device=DEV('insert', 'lipstick', 'lipstick steps drawn on a mirror (it reflects: the hand, the hot spot)'),
  energy='lipstick tip moving, crumbs falling, hot spot sliding 40 px/s, the reflected hand mirroring, push 3.5 %/s')
X(1.90, 'WS', 'ours', 'mirror/glass_wide', 'night',
  'the whole mirror leaning on the back wall of Cabin 7, white chipped frame, the seven steps; numerals 1-7 pop beside the steps '
  '(0.08 s each); your reflection dim behind the drawing', P(3, x=960, y=540, z=1.0),
  hud=[count_pop(1.95 + 0.08 * k, k + 1, 1230 - 52 * k, 300 + 70 * k) for k in range(7)],
  device=DEV('diagram', 'D2', 'count the steps: 1-7 pop beside the drawn steps'), errfix=[33],
  energy='numerals popping, dust in the beam, push 3 %/s')
X(2.56, 'WS', 'ours', 'mirror/glass_wide', 'night',
  'the whole mirror: below the bottom step a thick glowing red line draws itself in 0.6 s, too clean; label 8TH STEP', P(4, x=880, y=640, z=1.15),
  hud=[label(2.95, '8TH STEP', [700, 760], dx=-60, dy=-150)], tr='white',
  props=dict(eighth='drawing 2.56-3.16 (no hand)'), device=DEV('insert', '8th', 'the eighth line appears by itself'),
  energy='the line drawing itself with a glow, push 4 %/s')
X(3.28, 'INSERT', 'stairs', 'stairs/treads', 'stairs',
  'inside the glass: a pale bare foot with black toenails sets down on the red line (anatomical: arch, tendon, long toes; the '
  'satin hem with spade pips brushes the ankle)', P(5, x=960, y=760, z=1.2),
  chars=[Q('S0', [960, 900, 900], mode='feet', acts=[A(3.4, 'step_up', foot='right')])],
  q=dict(stage='S0', size=0.15, where='glass, on the eighth line', framing='foot 15 %', wrong='somebody is there'),
  energy='the foot lowering and settling, hem swaying 3 px, red edge glow breathing, push 5 %/s')
X(Wc(1, 'wipe'), 'TYPE', 'ours', 'type/kinetic', 'night',
  'KINETIC TITLE over the darkened, blurred mirror: WIPE THE GLASS in white (Montserrat 900, cap 9 % H) with an elliptical ring '
  'flash at 3.92; CLEAN. in lipstick red at 4.80 with a 3-frame RGB split and a lipstick underline swipe; out with a towel-wipe smear',
  P(4), plate=dict(set='mirror', view='glass_cu', var='night', post=dict(blur=10, dim=0.55)),
  hud=[kinetic(3.75, [dict(t=3.92, text='WIPE THE GLASS', color='#ffffff', size_h=0.09, fx='ring_flash'),
                      dict(t=4.80, text='CLEAN.', color='#c63449', size_h=0.09, fx='rgb_split_3f', underline=True)],
               out=dict(t=5.30, fx='towel_smear')), typebeat(3.75, 1, 'WIPE THE GLASS CLEAN.')],
  hit=True, energy='ring flash expanding, letters slamming, RGB split, push 4 %/s, smear out')
X(Wc(2, "don't", off=-0.03), 'POV', 'ours', 'mirror/glass_cu', 'night',
  'POV: your olive sleeve wipes the towel across the glass, leaving red streaks', FA(6, x=960, y=540, z=1.05),
  chars=[POVH([A(5.45, 'wipe_glass', strokes=2, dir='down', towel=True)])],
  props=dict(smeared='streaked'), energy='towel dragging red streaks, fast push 6 %/s')
X(Wc(2, 'see', off=-0.1), 'WS', 'stairs', 'mirror/through', 'stairs',
  'through a gap in the smear: a tall figure three steps down the stairs inside the glass, climbing; RED X (1 of 4) over her',
  P(5, x=960, y=520, z=1.1),
  chars=[Q('S0', [960, 760, 300, 5.0], mode='body', view='q_left', acts=[A(R(0), 'climb', steps_per_s=0.8)])],
  hud=[redx(6.05, 1390, 330, 120, 0.55, n=1)],
  q=dict(stage='S0', size=0.18, where='glass, three steps down', framing='figure 18 %', wrong='she is coming'),
  energy='red streaks dripping across the lens, the figure rising one tread, push 5 %/s')
X(6.62, 'WS', 'stairs', 'stairs/low', 'stairs',
  'low angle up the plum stairs: her silhouette climbing, the spade crown glinting, the white mirror frame at the top',
  CRN(dy=-30, r=3, x=960, y=600, z=1.05),
  chars=[Q('S0', [960, 820, 520, 3.0], mode='body', view='back', acts=[A(R(0), 'climb', steps_per_s=0.8)])],
  q=dict(stage='S0', size=0.18, where='the stairs', framing='figure 18 % (low angle)', wrong=''),
  energy='fog bands drifting, red edge glow breathing (2.4 s), crown glint, crane up 30 px/s')
X(7.36, 'WS', 'stairs', 'stairs/railing', 'stairs',
  'the stairs from the side along the railing: she climbs, the crown glinting, her red-fingertip hand gliding up the rail (face hidden)',
  P(4, x=960, y=560, z=1.05),
  chars=[Q('S0', [960, 860, 420, 3.0], mode='body', view='q_left', acts=[A(R(0), 'climb', steps_per_s=0.8), A(R(0), 'slide_rail', dx=60)], face_hidden=True)],
  energy='the hand gliding up the rail 60 px/s, dust falling through the gold from below, push 5 %/s')
X(T(3), 'WS', 'stairs', 'stairs/down', 'stairs',
  'from the top of the stairs looking down: eight red-edged treads in one-point perspective; at the bottom a gold rectangle '
  'with small Noah13 sitting on his bunk, face up, lit', SIL(2, x=960, y=600, z=1.05),
  chars=[body('noah13', 960, 860, 140, 'front', 'calm_kid', [A(9.6, 'look_up')], d=8.0)],
  energy='fog sliding, gold light breathing at the bottom, dust falling, slow push 2 %/s')
X(Wc(3, 'there', off=-0.0), 'CU', 'ours', 'cabin_now/bokeh', 'night',
  'CU of you (olive jacket, stubble) leaning in, wet eyes, the beam on your cheek; blue-violet bokeh with warm beam discs',
  P(3, x=960, y=520, z=1.05), chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0.1), 'lean_in', amount=0.3)], light=L_BEAM)],
  dof=dict(focus=1.0, dof=6.75), energy='bokeh discs drifting 5 px/s, a tear forming, push 3 %/s')
X(Wc(4, 'listen'), 'INSERT', 'ours', 'cabin_now/towel_over', 'night',
  'FLASH-FORWARD (253 s): five long fingertips press through the towel toward the lens, lipstick red bleeding through the cloth',
  FA(8), chars=[Q('S1', [960, 520, 700], mode='hands', acts=[A(R(0), 'press_through_cloth', depth=1.0)])],
  hud=[teaser(Wc(4, 'listen'), 'RULE 2'), chip(Wc(4, 'listen'), 'RULE 2', 'teaser')], teaser='RULE 2', tr='glitch',
  energy='cloth stretching toward the lens, fast push 8 %/s')
X(11.20, 'WS', 'climax', 'mess_porch/porch_crate', 'bell_hit',
  'FLASH-FORWARD (535 s): on the dark porch Tess swings the padlock into the cracked bell: spark and white flash', FA(6, hit=[(11.45, 12)]),
  chars=[body('tess', 960, 900, 420, 'profile_left', 'angry', [A(11.42, 'strike', prop='padlock')])],
  hud=[teaser(11.20, 'RULE 5'), chip(11.20, 'RULE 5', 'teaser')], teaser='RULE 5', tr='glitch',
  fx_post=[dict(t=11.45, white=0.8, dur=0.05)], energy='swing, contact, spark, fast push 9 %/s')
X(11.88, 'WS', 'climax', 'mirror/through', 'red',
  'FLASH-FORWARD (625 s): through a red streak, her whole figure on the lower steps lifts a bare foot over a wiped-away step', P(5, x=960, y=600, z=1.05),
  chars=[Q('S3c', [960, 900, 380, 2.0], mode='body', acts=[A(R(0), 'lift_foot', hang=True)])],
  hud=[teaser(11.88, 'RULE 7'), chip(11.88, 'RULE 7', 'teaser')], teaser='RULE 7', tr='glitch',
  fx_post=[dict(t=12.70, glitch=0.9, static=0.5, dur=0.08)], energy='the foot trembling in the air, red pulse 1.2 s, push 5 %/s, glitch out')
X(T(5), 'DOC', 'ours', 'camp_gate/poster', 'night',
  'MISSING poster on the gate board: NOAH, 13, gap-tooth school photo, green sweatshirt, rain-stained; the beam slides across it',
  P(4, x=960, y=480, z=1.05), tr='cut',
  hud=[doc(T(5), 'poster', 'MISSING · NOAH BRENNAN, 13 · LAST SEEN JULY 18 · CAMP CEDAR LAKE')],
  device=DEV('doc', 'poster', 'the MISSING poster: Noah, 13'),
  energy='the beam sweeping 120 px/s, the torn corner fluttering, push 4 %/s')
X(Wc(5, 'fourteen'), 'DOC', 'ours', 'camp_gate/poster', 'night',
  'a red rubber stamp 14 YEARS slams onto the poster with a camera hit (type beat 2)', P(3, x=960, y=500, z=1.15, hit=[(14.78, 10)]),
  hud=[stamp(14.72, '14 YEARS', 960, 520, '#c0392b', -4, 0.18), typebeat(14.72, 2, '14 YEARS')],
  energy='stamp slam, paper shudder, ink spreading, push 3 %/s')
X(Wc(6, 'when'), 'WS', 'theirs', 'cabin_dawn/master', 'dawn',
  'THEIRS master wide: Cabin 7 flipped and golden, frozen; the stairs rise along the back wall to the raised doorway in the white '
  'frame; Noah13 on his bunk at the foot of the stairs, one white sneaker (left), right foot bare; curtains held at 12 deg',
  DR(2, dx=24, x=960, y=540, z=1.0), tr='glint',
  chars=[body('noah13', 560, 760, 300, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)],
  chip='THE OTHER SIDE · 6:59 AM', errfix=[31],
  energy='the knot loop, motes twinkling in place, the camera drifting 24 px/s; nothing else moves (wrong)')
X(Wc(6, 'still'), 'INSERT', 'theirs', 'cabin_dawn/clock', 'dawn',
  'D7 the loop clock: 6:59:59 snaps back to 6:59:40 with the rewind glitch; chip LOOP with a circular arrow',
  P(5, x=960, y=500, z=1.2), tr='cut',
  hud=[diagram(17.60, 'D7', 'loop clock: the second hand reaches :59 and snaps back to :40', hold=0.6), chip(17.62, 'LOOP', 'loop')],
  fx_post=[dict(t=17.95, glitch=0.8, dur=0.2, rewind=1.0)],
  device=DEV('diagram', 'D7', 'the loop clock 6:59:59 -> :40'), energy='second hand sweeping then scrubbing back, push 5 %/s')
X(Wc(6, 'for'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn',
  'CU of Noah13 looking up with the gap-tooth smile (almond eyes, two highlights); gold bokeh', P(4, x=960, y=520, z=1.05),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'grin_kid', [A(R(0.1), 'look_up'), A(R(0.4), 'smile')], light=L_GOLD)],
  dof=dict(focus=1.0, dof=6.75), energy='gold bokeh drifting, the smile, push 4 %/s; hard cut to the time card')

# ================================================================ ARRIVAL 19.26 - 54.46 (lines 7-18): 22 shots
STATE(19.26, queen='absent', mirror='wrapped', steps_drawn=7, eighth='none', smeared=0, noah='unseen')
X(T(7), 'EWS', 'ours', 'camp_gate/aerial', 'night',
  'the camp aerial relit blue-violet: the lake with the moon, Cabins 5-7 in a row with orange X marks (Cabin 7 nearest the path), '
  'the mess hall across the path with its porch, the gate, the caretaker\'s warm window, your car at the gate; TIME CARD',
  RV(5, x=980, y=560, z=1.2), tr='glint',
  hud=[dict(t=w(7, "it's"), type='time_card', icon='clock', day='FRIDAY', time='11:57 PM',
            sub='CAMP CEDAR LAKE  ·  DEMOLITION TOMORROW', flip_at=w(7, '11:57'), hold=2.8, x=110, y=170)],
  device=DEV('doc', 'time_card', 'FRIDAY 11:57 PM · CAMP CEDAR LAKE · DEMOLITION TOMORROW'), time_card=True,
  energy='reveal pull-out 5 %/s, lake shimmer, mist, fireflies, the car\'s headlights on')
X(22.46, 'WS', 'ours', 'camp_gate/wide', 'night',
  'the gate wide (v1 set, relit): you and Tess small by the car, the MISSING poster on the board; the headlights go off at 22.6',
  CRN(dy=18, r=2.5, x=960, y=480, z=1.0),
  chars=[body('you', 760, 900, 300, 'q_right', 'grief', [A(R(0.3), 'walk', to=880, surface='gravel')]),
         body('tess', 600, 900, 290, 'q_right', 'brave', [A(R(0), 'walk', to=700, surface='gravel')])],
  props=dict(car='headlights off at 22.6'), energy='headlights switching off, mist bands, fireflies, pines swaying, crane down')
X(Wc(9, 'tomorrow'), 'DOC', 'ours', 'camp_gate/notice', 'night',
  'NOTICE OF DEMOLITION zip-tied to the fence: CABINS 5-7 · SAT 7:00 AM; the beam crosses it, SAT 7:00 AM underlined',
  P(3, x=960, y=520, z=1.02),
  hud=[doc(25.0, 'notice', 'NOTICE OF DEMOLITION · CABINS 5-7 · SAT 7:00 AM', marks=[dict(t=26.4, what='underline', text='SAT 7:00 AM')])],
  device=DEV('doc', 'notice', 'the demolition notice: Cabins 5-7, Saturday 7:00 AM'),
  energy='the sheet flapping, the beam crossing, push 3 %/s')
X(Wc(9, 'is'), 'WS', 'ours', 'camp_path/cabins_row', 'night',
  'low wide: three dark cabins in a row with orange spray-paint X marks, the excavator parked by the nearest',
  DR(2, dx=-30, x=1000, y=560, z=1.02), energy='parallax drift: the bucket slides past the cabins, clouds over the moon, fireflies')
X(Wc(9, 'cabins'), 'MS', 'ours', 'camp_path/cabin7_door', 'night',
  'Cabin 7 (nearest the path): the number plaque, the door with its padlock on the hasp, old search tape on the rail; label CABIN 7',
  P(4, x=1250, y=500, z=1.05), hud=[label(28.95, 'CABIN 7', [1250, 380], dx=150, dy=-80)],
  device=DEV('insert', 'cabin7', 'Cabin 7 is this one: plaque, padlock on the hasp'), errfix=[32],
  energy='search tape fluttering, moths at the dead lamp, push 4 %/s')
X(30.00, 'MS', 'ours', 'camp_gate/wide', 'night',
  'Tess at the gate lifts the carabiner of keys into the beam', P(3, x=900, y=560, z=1.15),
  chars=[body('tess', 900, 1000, 640, 'q_right', 'brave', [A(w(10, 'tess'), 'flashlight', on=True, aim='gate'),
                                                         A(w(10, 'keys') - 0.3, 'hold_up', prop='keys', side=-1)])],
  props=dict(flashlight='tess_on at 30.95', keys='lifted'), energy='beam sweeping, keys swinging, push 3 %/s')
STATE(30.95, flashlight='tess_on', keys='tess_hand')
X(31.75, 'INSERT', 'ours', 'camp_gate/keys_cu', 'night',
  'the key ring swings into CU: padlock keys, the carabiner and a CABIN 7 key tag', FA(7, x=960, y=540, z=1.2),
  chars=[hands('tess', 960, 520, 380, [A(R(0), 'jingle', prop='keys')], sleeve='orange')], errfix=[13],
  device=DEV('insert', 'keys', 'Tess has the keys: the CABIN 7 tag'), energy='keys swinging and glinting, fast push 7 %/s')
X(T(11), '2S', 'ours', 'camp_gate/wide', 'night',
  'you and Tess at the gate; she glances at you, half a smile', P(3, x=960, y=540, z=1.1),
  chars=[body('you', 1140, 1000, 640, 'q_left', 'grief', [A(R(0.4), 'look', x=800, y=420)]),
         body('tess', 780, 1000, 620, 'q_right', 'half_smile', [A(R(0.2), 'look', x=1140, y=420)])],
  energy='beam spill moving, fireflies behind, push 3 %/s')
X(T(12), 'CU', 'ours', 'camp_gate/bokeh', 'night',
  'CU of you looking at the poster photo of Noah in the green sweatshirt (it glows soft in the bokeh behind you)', P(3, x=960, y=520, z=1.05),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0.4), 'blink')], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='bokeh drift, a blink, push 3 %/s')
X(Wc(12, 'the', n=0), 'DOC', 'ours', 'camp_gate/poster_ecu', 'night',
  'ECU of the poster line LAST SEEN WEARING A GREEN SWEATSHIRT; a yellow highlighter swipes it (evidence device)',
  P(4, x=980, y=720, z=1.35), hud=[highlight(35.60, 'LAST SEEN WEARING A GREEN SWEATSHIRT', 560, 690, 1400, 760)],
  device=DEV('doc', 'poster_line', 'LAST SEEN WEARING A GREEN SWEATSHIRT (highlighted)'),
  energy='highlighter swipe, paper fluttering, push 4 %/s')
X(T(13), 'WS', 'memory', 'memory/dock', 'sepia_day',
  'memory: Noah13 on the lake dock in the green CEDAR LAKE sweatshirt, laughing; stamp 14 YEARS AGO', P(2.5, x=960, y=520, z=1.02),
  tr='sepia', chars=[body('noah13', 960, 960, 640, 'front', 'laugh', [A(R(0.2), 'laugh', dur=1.2)])],
  energy='water glitter, the hood strings swinging, gate weave, push 2.5 %/s')
X(Wc(13, 'he'), 'WS', 'memory', 'memory/night_window', 'sepia_night',
  'memory, the night he vanished: Cabin 7\'s window from outside at night, a boy\'s silhouette in the sweatshirt at the glass (no face)',
  P(2.5), energy='lantern flicker behind him, moths, push 2.5 %/s')
X(T(14), 'CU', 'ours', 'camp_gate/bokeh', 'night',
  'CU of you, resolved, jaw set', P(3, x=960, y=520, z=1.05), tr='sepia',
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'resolve', [A(R(0.5), 'blink')], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='bokeh drift, a breath, push 3 %/s')
X(Wc(14, 'bring', n=0), 'OTS', 'ours', 'camp_gate/fence_track', 'night',
  'OTS following Tess along the fence toward the gate, her beam bobbing ahead', TR(dx=60, r=1.5),
  chars=[body('tess', 1100, 980, 560, 'back', 'brave', [A(R(0), 'walk', to=1400, surface='gravel')]),
         body('you', 520, 1100, 820, 'back', 'neutral', [A(R(0), 'walk', to=700, surface='gravel')], ots=True)],
  energy='track 60 px/s, fence posts sliding past in the foreground, beam bobbing')
X(Wc(14, "you'd"), 'WS', 'ours', 'camp_gate/gate_reverse', 'night',
  'reverse wide from inside the gate: the two of you reach the chained bars; Tess hands the flashlight to you while she finds the key',
  P(2.5, x=960, y=520, z=1.0),
  chars=[body('tess', 900, 880, 330, 'q_right', 'brave', [A(R(0.3), 'pick_up', prop='keys')]),
         body('you', 1080, 880, 340, 'q_left', 'neutral', [])], energy='beam swinging over the chain, fireflies, push 2.5 %/s')
X(T(15), 'WS', 'ours', 'camp_gate/wide', 'night',
  'wide at the chained gate: Tess works the key into the gate padlock and pulls the chain through the bars; you hold the light',
  P(3, x=960, y=540, z=1.05),
  chars=[body('tess', 900, 900, 360, 'q_right', 'brave', [A(R(0.3), 'unlock', prop='gate_padlock'), A(R(-0.3), 'pull_chain')]),
         body('you', 1120, 900, 370, 'q_left', 'neutral', [A(R(0), 'flashlight', aim='gate')])],
  props=dict(gate_padlock='open at 45.75'), energy='hands working the key, chain sliding, beam wobble, push 4 %/s')
STATE(45.75, gate_padlock='open')
X(Wc(15, 'tess'), 'CU', 'ours', 'camp_gate/bokeh', 'night',
  'CU of you: your phone buzzed; you lift it, its glow under your chin', HH(2, shake=8, x=960, y=540, z=1.05),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'neutral', [A(R(0.2), 'look', x=960, y=760)], light=L_PHONE, phone_glow=True)],
  props=dict(your_phone='hand'), energy='phone glow flickering on, handheld')
STATE(44.4, your_phone='hand')
X(T(16), 'UI', 'ui', 'ui/text', 'phone',
  'your phone: MOM thread, bubble "Check the pocket." (text-fit checked)', HH(1.5, shake=6),
  hud=[dict(t=t(16), type='phone', state='message', name='MOM', bubbles=[dict(t=t(16), text='Check the pocket.')], x=960, y=560, scale=1.0,
            fit=True)], errfix=[23], device=DEV('ui', 'texts', "Mom's texts"),
  energy='bubble sliding up, the blurred gate behind with the beam moving, handheld')
X(T(17), 'UI', 'ui', 'ui/text', 'phone',
  'typing dots, then the second bubble "He always had one of those cinnamon candies in there."', HH(1.5, shake=6),
  hud=[dict(t=T(17), type='phone', state='message', name='MOM', bubbles=[dict(t=t(16), text='Check the pocket.'),
        dict(t=t(17), text='He always had one of those cinnamon candies in there.', typing_from=e(16) + 0.05)], x=960, y=560, scale=1.0, fit=True)],
  energy='typing dots pulsing, bubble sliding up')
X(Wc(17, 'cinnamon', off=-0.05), 'CU', 'ours', 'camp_gate/bokeh', 'night',
  'CU of you reading the second text in the phone glow; a small smile at "cinnamon candies"', P(3, x=960, y=520, z=1.05),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0.5), 'smile', amount=0.3)], light=L_PHONE)], dof=dict(focus=1.0, dof=6.75),
  energy='phone glow flicker, bokeh drift, push 3 %/s')
X(T(18), 'INSERT', 'memory', 'memory/pocket', 'sepia_day',
  'memory insert: the green sweatshirt\'s kangaroo pocket, a kid hand pulls out red cinnamon candies in red twist wrappers (plants the candy)',
  P(3, x=960, y=560, z=1.05), tr='sepia',
  chars=[hands('noah13', 960, 620, 360, [A(R(0.2), 'pull_from_pocket', prop='candy_red')])],
  device=DEV('insert', 'candy', 'red cinnamon candies in red twist wrappers'), energy='hand pulling the candy, cellophane glinting, push 3 %/s')
X(Wc(18, 'what'), 'CU', 'ours', 'camp_gate/bokeh', 'night',
  'CU of you reading the phone, eyes wet; blue-violet bokeh', P(2.5, x=960, y=520, z=1.0), tr='sepia',
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(w(18, 'pockets'), 'swallow')], light=L_PHONE)], dof=dict(focus=1.0, dof=6.75),
  energy='screen glow flicker, bokeh drift, a swallow, push 2.5 %/s')

# ================================================================ PORCH 54.46 - 67.59 (lines 19-23): 9 shots
X(T(19), 'WS', 'ours', 'mess_porch/high_wide', 'night',
  'HIGH WIDE from the mess-hall porch: the porch in the foreground, the SAVE FOR THE MUSEUM crate right of the screen door, '
  'Cabin 7\'s door across the path (40 m); you two climb the steps', CRN(dy=20, r=2, x=960, y=520, z=1.05),
  chars=[body('tess', 820, 900, 300, 'back', 'brave', [A(R(0), 'walk', to=900, surface='porch'), A(R(0), 'flashlight', aim='porch')]),
         body('you', 680, 920, 310, 'back', 'neutral', [A(R(0.3), 'walk', to=760, surface='porch')])],
  setup='PORCH_HIGH', energy='chimes swinging, the beam crawling over the screen door, walkers climbing, crane')
X(T(20), 'WS', 'ours', 'mess_porch/porch_low', 'night',
  'low angle on the boards: Tess\'s boot steps over the crate', P(3.5, x=960, y=640, z=1.1),
  chars=[C('tess', [900, 760, 700], 'profile_left', 'brave', [A(w(20, 'over'), 'step_over', prop='crate')], mode='legs')],
  energy='boot crossing the frame, beam spill, push 3.5 %/s')
X(Wc(20, 'crate'), 'DOC', 'ours', 'mess_porch/crate_cu', 'night',
  'insert: the stencil SAVE FOR THE MUSEUM on the slats and a paper museum tag on string', P(3, x=960, y=540, z=1.05),
  hud=[doc(57.3, 'stencil', 'SAVE FOR THE MUSEUM', marks=[dict(t=58.3, what='tag_flip', text='CEDAR LAKE HISTORICAL SOC.')])],
  device=DEV('doc', 'crate', 'the crate: SAVE FOR THE MUSEUM'), energy='tag flipping on its string, beam crossing, push 3 %/s')
X(T(21), 'WS', 'ours', 'mess_porch/porch_crate', 'night',
  'porch wide: you crouch at the crate; Tess shines the beam between the slats', P(3, x=960, y=560, z=1.05),
  chars=[body('you', 1000, 900, 300, 'q_left', 'neutral', [A(R(0.2), 'kneel')]), body('tess', 760, 900, 400, 'q_right', 'brave', [A(R(0), 'flashlight', aim='crate')])],
  energy='the beam probing between the slats, chimes, push 3 %/s')
X(Wc(21, 'you'), 'INSERT', 'ours', 'mess_porch/bell_ecu', 'night',
  'the old brass breakfast bell in the crate, lit by the beam', P(3, x=960, y=540, z=1.15),
  device=DEV('insert', 'bell', 'the old breakfast bell'), energy='dust in the beam, the brass glinting, push 3 %/s')
X(Wc(21, 'breakfast'), 'CU', 'ours', 'mess_porch/bokeh', 'night',
  'CU of you recognising the old breakfast bell, a brass glint on your face', P(3, x=960, y=520, z=1.05),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'wonder', [A(R(0.3), 'blink')], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='brass glint flickering on the cheek, bokeh drift')
X(T(22), 'INSERT', 'ours', 'mess_porch/bell_ecu', 'night',
  'ECU of the rim: the crack; label THE CRACK', P(4, x=1040, y=640, z=1.6), hud=[label(64.05, 'THE CRACK', [1040, 660], dx=180, dy=-110)],
  device=DEV('insert', 'crack', 'the crack in the rim'), energy='glint crawling along the crack, push 4 %/s')
X(T(23), 'WS', 'memory', 'memory/porch_drop', 'sepia_day',
  'memory: a counselor drops the bell on the porch steps; kid-you and Noah flinch at the sound', P(3, x=960, y=540, z=1.0), tr='sepia',
  chars=[body('counselor', 1000, 900, 420, 'front', 'shock', [A(w(23, 'dropped'), 'drop_prop', prop='bell')]),
         body('you_kid', 640, 940, 300, 'q_right', 'shock', [A(w(23, 'dropped') + 0.1, 'flinch')]),
         body('noah13', 760, 940, 330, 'q_right', 'shock', [A(w(23, 'dropped') + 0.1, 'flinch')])],
  energy='the bell falling and bouncing, kids flinching, gate weave')
X(Wc(23, 'it'), 'DIAGRAM', 'memory', 'memory/bell_ecu', 'sepia_day',
  'D8 planted: the bell rings on the boards; a clean white ring, then a jagged red rattle squiggle (the real bell has a rattle)',
  P(3, x=960, y=540, z=1.15),
  hud=[rings(66.20, 'clean', 960, 520, 3, 0.8), rings(66.80, 'rattle', 960, 520, 3, 0.8),
       diagram(66.15, 'D8', 'sound rings: a clean ring, then a ring plus a jagged rattle squiggle (the cracked bell)', hold=1.4)],
  device=DEV('diagram', 'D8', 'the cracked bell rings twice: clean, then a rattle'),
  energy='rings expanding, the bell rim vibrating, push 3 %/s')

# ================================================================ CARETAKER AND CABIN 7 67.59 - 88.70 (lines 24-30): 14 shots
X(T(24), 'CU', 'ours', 'camp_path/bokeh', 'night', 'CU of Tess, finger to her lips', P(3, x=960, y=520, z=1.05),
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'tense', [A(w(24, 'finger'), 'finger_to_lips')], light=L_BEAM)],
  dof=dict(focus=1.0, dof=6.75), energy='bokeh drift, the finger rising, push 3 %/s')
X(Wc(24, 'as'), 'WS', 'ours', 'caretaker/wide', 'night',
  'the caretaker\'s house: warm window #ffb84d with TV flicker, the curtain sways at 70.32; your two silhouettes cross in the foreground',
  TR(dx=40, r=1.0), chars=[body('tess', 700, 1060, 700, 'profile_right', 'tense', [A(R(0), 'walk', to=1300, surface='gravel', soft=True)]),
                          body('you', 520, 1080, 720, 'profile_right', 'tense', [A(R(0), 'walk', to=1100, surface='gravel', soft=True)])],
  energy='TV flicker, the curtain sway at 70.32, silhouettes crossing, track 40 px/s')
X(T(25), 'MS', 'ours', 'cabin_now/door', 'night',
  'Cabin 7\'s door: Tess unhooks the padlock and hangs it open on the hasp; the beam leads in', P(4, x=960, y=540, z=1.05),
  chars=[hands('tess', 960, 560, 420, [A(R(0.1), 'unlock', prop='padlock'), A(R(0.5), 'hang_open', prop='padlock')], sleeve='orange')],
  props=dict(padlock='hasp_open at 71.9'), errfix=[32], device=DEV('insert', 'padlock', 'the padlock on Cabin 7\'s hasp'),
  energy='padlock swinging on the hasp, the door creaking in, beam leading, push 4 %/s')
STATE(71.9, padlock='hasp_open')
X(Wc(25, 'you'), 'WS', 'ours', 'cabin_now/master', 'night',
  'CABIN 7 MASTER WIDE (high, from the door): left bunk, wall clock, window with torn screen and sill, the mirror spot (empty '
  'wall), Noah\'s bunk along the right wall with the NOAH cubby; moon shafts and the warm beam pool; you two enter',
  P(3, x=960, y=540, z=1.0), setup='C7_MASTER', chip='CABIN 7 · {ours}',
  chars=[body('tess', 760, 980, 380, 'back', 'tense', [A(R(0), 'walk', to=900, surface='wood'), A(R(0), 'flashlight', aim='room', sweep=0.6)]),
         body('you', 1080, 1000, 400, 'back', 'neutral', [A(R(0.2), 'walk', to=1180, surface='wood')])],
  energy='beam sweeping the room, dust in the shafts, moths, push 3 %/s')
X(Wc(25, 'wrapped'), 'INSERT', 'ours', 'cabin_now/cubby', 'night',
  'the NOAH cubby, empty: masking-tape label NOAH, a cobweb, no sweatshirt (you looked; it is not here)', P(4, x=960, y=520, z=1.1),
  errfix=[28], device=DEV('insert', 'cubby', 'the NOAH cubby is empty: no sweatshirt'), energy='the beam passing, cobweb stirring, push 4 %/s')
X(74.10, 'WS', 'ours', 'cabin_now/under_bunk', 'night',
  'floor-level under Noah\'s bunk, slats overhead: a towel-wrapped bundle in the beam; your hand pulls it out',
  P(3, x=960, y=600, z=1.05),
  chars=[hands('you', 1200, 640, 400, [A(w(25, 'bunk'), 'reach'), A(R(-0.4), 'pull_hand', prop='bundle')], sleeve='olive')],
  energy='dust drifting through slats, the bundle scraping out, push 3 %/s')
X(T(26), 'INSERT', 'ours', 'cabin_now/towel_label', 'night',
  'the striped towel\'s laundry label in marker: NOAH', P(4, x=960, y=540, z=1.15),
  device=DEV('insert', 'towel', 'Noah\'s towel (label NOAH)'), energy='thumb brushing the terry loops, push 4 %/s')
X(T(27), 'WS', 'memory', 'memory/sprinkler_lawn', 'sepia_day',
  'memory: the lawn sprinkler arcs; Noah runs through it holding the striped towel out', P(2.5), tr='sepia',
  chars=[body('noah13', 900, 900, 360, 'profile_right', 'laugh', [A(R(0), 'run', to=1200)])],
  energy='sprinkler arcs, Noah running, sun flare, gate weave')
X(Wc(27, 'sprinkler'), 'MS', 'memory', 'memory/sprinkler_lawn', 'sepia_day',
  'memory: the towel catches the water, soaking', P(3.5, x=960, y=520, z=1.1),
  chars=[body('noah13', 960, 1000, 640, 'front', 'grin_kid', [A(R(0), 'hold_up', prop='towel')])],
  energy='water pelting the towel, droplets flying, push 3.5 %/s')
X(T(28), 'WS', 'memory', 'memory/bunk_morning', 'sepia_morning',
  'memory: Noah wrings the towel over kid-you\'s pillow in the bottom bunk', P(2.5, x=960, y=560, z=1.0),
  chars=[body('noah13', 1080, 940, 420, 'q_left', 'grin_kid', [A(w(28, 'wring'), 'wring', prop='towel')]),
         C('you_kid', [760, 760, 0.8], 'front', 'sleep', [A(w(28, 'pillow'), 'wake_squint')], mode='lying')],
  energy='water pouring, kid stirring, gate weave, push')
X(Wc(28, 'when'), 'CU', 'memory', 'memory/bunk_morning', 'sepia_morning',
  'memory: kid-you squeals under the water, Noah laughing behind', FA(5, x=960, y=520, z=1.1),
  chars=[bust('you_kid', 960, 560, 1.0, 'front', 'laugh', [A(R(0.1), 'flinch')], light=L_MEM)],
  energy='water splashing, squeal, fast push 5 %/s')
X(T(29), 'WS', 'memory', 'memory/bunk_night', 'sepia_night',
  'memory, night: Noah asleep in the top bunk, his arm with the digital watch hanging over the edge', P(2.5),
  chars=[C('noah13', [960, 520, 1.0], 'front', 'sleep', [A(R(0), 'breathe_sleep')], mode='lying', watch=True)],
  energy='moonlight crawling, breathing, gate weave, push')
X(T(30), 'MS', 'memory', 'memory/bunk_night', 'sepia_night',
  'memory: kid-you on tiptoe reaching for the hanging watch arm, grinning', P(3.5, x=980, y=520, z=1.1),
  chars=[body('you_kid', 900, 1060, 720, 'q_right', 'sly', [A(R(0.2), 'reach')])], energy='tiptoe, the arm swaying, push 3.5 %/s')
X(Wc(30, 'changing'), 'INSERT', 'memory', 'memory/watch_cu', 'sepia_night',
  'the watch LCD fills 70 % of the frame; the finger presses the button BESIDE the digits (never over them); ALM 6:45 flips '
  'to 4:45 with a highlight', P(2.5, x=960, y=540, z=1.0), errfix=[24],
  chars=[hands('you_kid', 1380, 700, 360, [A(w(30, 'changing'), 'press_button'), A(w(30, 'alarm'), 'press_button')])],
  hud=[diagram(87.30, 'watch', 'ALM 6:45 -> 4:45 (the digits flip, highlighted)', hold=1.2)],
  device=DEV('insert', 'watch', 'the alarm changed: 6:45 -> 4:45'), energy='digits flipping, button chirps, push 2.5 %/s')

# ================================================================ THE STEPS AND THE GAME 88.70 - 121.06 (lines 31-42): 22 shots
STATE(88.9, mirror='glass', towel='floor_beside', eighth='none')
X(T(31), 'WS', 'ours', 'cabin_now/profile', 'night',
  'profile along the back wall: you pull the towel off; the mirror stands on the floor against the back wall at the mirror spot '
  '(between the window and Noah\'s bunk); in the glass: your and Tess\'s reflections and the beam hot spot',
  P(3, x=960, y=540, z=1.0), setup='C7_PROFILE',
  chars=[body('you', 760, 980, 430, 'profile_right', 'neutral', [A(R(0.1), 'unwrap', prop='towel')]),
         body('tess', 520, 980, 420, 'profile_right', 'tense', [A(R(0), 'flashlight', aim='mirror')])],
  props=dict(mirror='unwrapped at 89.0'), errfix=[33], energy='the towel sliding off, the hot spot blooming, dust, push 3 %/s')
X(Wc(31, 'drawn'), 'WS', 'ours', 'mirror/glass_wide', 'night',
  'the whole mirror (white chipped frame): seven waxy red steps; the frame edge on the left; your reflection behind them; the hot spot', P(3.5, x=980, y=520, z=1.1),
  errfix=[33], energy='hot spot sliding, crumbs glinting, push 3.5 %/s')
X(T(32), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of Tess: she recognises it', P(3, x=960, y=520, z=1.05),
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'recognise', [A(R(0.3), 'expr', name='recognise')], light=L_BEAM)],
  dof=dict(focus=1.0, dof=6.75), energy='eyes narrowing, bokeh drift, push 3 %/s')
X(T(33), 'WS', 'memory', 'memory/lantern_game', 'sepia_night',
  'memory, night by lantern in Cabin 7: kids in sleeping bags watch a kid draw steps on this mirror', P(2.5), tr='sepia',
  chars=[C('kids', [960, 900, 420], 'front', 'giggle', [A(R(0), 'dare')], mode='body'),
         hands('noah13', 1200, 420, 150, [A(R(0.2), 'draw_step', step=3)])],
  energy='lantern flicker, the lipstick moving, gate weave')
X(T(34), 'DOC', 'memory', 'memory/card_queen', 'sepia_night',
  'a vintage Queen of Spades playing card: the court-card queen wears her signature: spade crown, fan collar, spade beauty mark',
  P(4, x=960, y=500, z=1.1), hud=[doc(95.3, 'card', 'QUEEN OF SPADES (court card)')],
  device=DEV('doc', 'card', 'the Queen of Spades playing card (plants the crown, collar, beauty mark)'),
  energy='the card turning in the lantern light, push 4 %/s')
X(Wc(34, 'three'), 'CU', 'memory', 'memory/kids_mouths', 'sepia_night',
  'CU: three kids\' faces in a row by lantern whisper her name one after another; 1 · 2 · 3 pop', FA(5),
  chars=[C('kids', [960, 600, 1.0], 'front', 'giggle', [A(97.03, 'whisper'), A(97.31, 'whisper'), A(97.59, 'whisper')], mode='bust')],
  hud=[count_pop(97.03, 1, 600, 400), count_pop(97.31, 2, 960, 400), count_pop(97.59, 3, 1320, 400)],
  energy='mouths whispering one after another, numerals popping')
X(98.20, 'DIAGRAM', 'ours', 'mirror/glass_cu', 'night',
  'D1 the game, drawn on the glass in white chalk lines: steps numbered 1 (top) to 7, a tiny dark figure below step 7, a dotted '
  'arrow climbing; at 99.3 it reaches WISH with a star at the top', P(3, x=960, y=540, z=1.0),
  hud=[diagram(98.22, 'D1', 'steps numbered 1 (top) .. 7; a tiny figure below step 7; a dotted arrow climbs to WISH with a star', hold=2.4, build=True)],
  device=DEV('diagram', 'D1', 'the game: she climbs from the bottom to WISH at the top'), energy='chalk lines drawing on, the dotted arrow advancing')
X(100.70, 'WS', 'memory', 'memory/kids_game', 'sepia_night',
  'memory: kids in sleeping bags dare each other, flashlights under chins', P(2.5),
  chars=[C('kids', [960, 900, 460], 'front', 'giggle', [A(R(0), 'dare')], mode='body')], energy='flashlights wobbling, giggles')
X(Wc(36, 'dare'), 'WS', 'memory', 'memory/kids_game', 'sepia_night',
  'two speech balloons QUEEN OF SPADES... QUEEN OF SPADES...; a third balloon, empty', P(3, x=960, y=500, z=1.05),
  hud=[dict(t=102.6, type='balloon', text='QUEEN OF SPADES...', x=620, y=300), dict(t=103.3, type='balloon', text='QUEEN OF SPADES...', x=1000, y=260),
       dict(t=103.9, type='balloon', text='', x=1380, y=300, empty=True)],
  energy='balloons popping in, the third empty one wobbling')
X(T(37), 'CU', 'memory', 'memory/kids_game', 'sepia_night', 'CU: the kids laughing, flashlights under their chins', P(3.5),
  chars=[C('kids', [960, 600, 1.0], 'front', 'giggle', [A(R(0), 'laugh')], mode='bust')], energy='laughing, flashlights bobbing')
X(Wc(37, 'supposed'), 'CU', 'memory', 'memory/kids_game', 'sepia_night',
  'Noah13 not laughing: he looks at the glass', P(4, x=960, y=520, z=1.1),
  chars=[bust('noah13', 960, 560, 1.0, 'q_right', 'worried', [A(R(0.2), 'look', x=1400, y=480)], light=L_MEM)],
  energy='his eyes sliding to the mirror, push 4 %/s')
X(T(38), 'WS', 'ours', 'cabin_now/three_q', 'night',
  'three-quarter from the left bunk: Tess raises the flashlight at the glass; you kneel at the mirror',
  P(3, x=960, y=540, z=1.0), tr='sepia',
  chars=[body('tess', 820, 980, 440, 'q_right', 'tense', [A(R(0.3), 'flashlight', aim='mirror')]),
         body('you', 1140, 980, 330, 'q_right', 'neutral', [], kneel=True)],
  energy='the beam swinging up onto the glass, dust, push 3 %/s')
X(Wc(38, 'on'), 'WS', 'ours', 'mirror/glass_wide', 'night',
  'the mirror in the beam: the hot spot blooms; your two reflections; the steps glow', P(3.5, x=960, y=540, z=1.05),
  energy='hot spot flaring, dust motes in the beam, push 3.5 %/s')
X(T(39), 'INSERT', 'ours', 'cabin_now/sill', 'night',
  'insert: Tess sets her phone FACE UP on the windowsill; its black glass reflects the moon and the window (it is a mirror too); hold',
  SIL(1.8, x=960, y=560, z=1.1),
  chars=[hands('tess', 960, 520, 340, [A(w(39, 'phone'), 'set_down', prop='phone')], sleeve='orange')],
  props=dict(phone='sill_face_up at 110.71'), device=DEV('insert', 'phone', 'the phone face up on the sill (a mirror too)'),
  energy='the phone laid down, the moon sliding across its glass, slow push 1.8 %/s')
STATE(110.71, phone='sill_face_up')
X(T(40), 'WS', 'ours', 'cabin_now/profile', 'night',
  'profile wide: Tess kneels at the mirror and brushes her thumb toward the lipstick; you watch', P(3, x=960, y=560, z=1.0),
  chars=[body('tess', 900, 980, 380, 'profile_right', 'tense', [A(w(40, 'brushes'), 'rub_thumb', at=(1200, 600))], kneel=True),
         body('you', 640, 980, 430, 'profile_right', 'neutral', [])], energy='kneeling, the thumb reaching, dust in the beam')
X(Wc(40, 'over'), 'OTS', 'ours', 'mirror/glass_cu', 'night',
  'over Tess\'s shoulder: her thumb smears the bottom step', P(4, x=960, y=560, z=1.2),
  chars=[bust('tess', 560, 700, 1.3, 'back', 'tense', [], light=L_BEAM, ots=True), hands('tess', 1060, 560, 440, [A(w(40, 'lipstick'), 'smear')], sleeve='orange')],
  energy='waxy smear, push 4 %/s')
X(T(41), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of Tess looking at the little red crumbs on her thumb, held up into the beam',
  P(3.5, x=960, y=540, z=1.05),
  chars=[bust('tess', 960, 580, 1.0, 'q_right', 'puzzled', [A(R(0.2), 'rub_fingers')], light=L_BEAM, hand_up=True)], dof=dict(focus=1.0, dof=6.75),
  energy='crumbs falling glinting, push 3.5 %/s')
X(Wc(41, 'come'), 'WS', 'ours', 'cabin_now/three_q', 'night',
  'three-quarter wide: Tess rubs the crumbs between her fingers and looks at you; the mirror and its steps between you', P(3, x=960, y=540, z=1.0),
  chars=[body('tess', 800, 980, 380, 'q_right', 'puzzled', [A(R(0.2), 'rub_fingers'), A(R(0.6), 'look', x=1200, y=500)], kneel=True),
         body('you', 1180, 980, 400, 'q_left', 'tense', [])],
  energy='fingers rubbing, dust in the beam, push 3 %/s')
X(T(42), 'INSERT', 'ours', 'mirror/glass_cu', 'night',
  'silence; slow push on the bottom step: clean glass below it', SIL(1.5, x=900, y=660, z=1.2),
  energy='the hot spot trembling, a crumb falling, slow push 1.5 %/s (silence)')
X(Wc(42, 'line'), 'INSERT', 'ours', 'mirror/glass_cu', 'night',
  'the eighth line draws itself below the bottom step; label 8TH STEP', P(3, x=900, y=660, z=1.3, accel=[(118.87, 1.06, 0.6)]), tr='white',
  hud=[label(119.2, '8TH STEP', [900, 700], dx=-60, dy=-150)], props=dict(eighth='drawing 118.87-119.47'),
  device=DEV('insert', '8th', 'a fresh red line appears beneath the bottom step'),
  energy='the line drawing itself, punch-in 1.08x on the hit')
STATE(118.87, eighth='present', phone='sill_face_up_red_glint')   # the phone's red glint from here (W10 plant)
X(119.90, '2S', 'ours', 'cabin_now/ots_mirror', 'night',
  'you and Tess react: you lean back, Tess\'s hand to her mouth; the line glowing in the glass between you',
  FA(5, x=960, y=540, z=1.05),
  chars=[body('you', 1180, 1060, 640, 'q_left', 'fear', [A(119.95, 'flinch')]), body('tess', 760, 1060, 620, 'q_right', 'fear', [A(119.95, 'hand_to_mouth')])],
  energy='both flinching, beam lurching, fast push 5 %/s')

# ================================================================ SEVEN RULES 121.06 - 129.80 (lines 43-46): 5 shots
X(T(43), 'WS', 'ours', 'mirror/glass_wide', 'night',
  'the whole mirror: the seven steps light up 1-7 like a progress bar (type beat 3 builds); you and Tess dim in the reflection', P(3, x=960, y=540, z=1.0),
  hud=[count_pop(121.15 + 0.12 * k, k + 1, 1230 - 52 * k, 300 + 70 * k, '#ff4060') for k in range(7)],
  energy='steps lighting one after another, push 3 %/s')
X(Wc(43, 'there'), 'TYPE', 'ours', 'type/beat', 'night', 'type beat 3: 7 RULES slams over the glowing steps', P(4),
  plate=dict(set='mirror', view='glass_cu', var='night', post=dict(blur=8, dim=0.45)),
  hud=[typebeat(122.87, 3, '7 RULES', size_h=0.2)], energy='slam on "seven" with overshoot, push 4 %/s')
X(T(44), 'INSERT', 'ours', 'mirror/glass_cu', 'night',
  'step 4 circles itself in lipstick: RULE 4', FA(6, x=1080, y=500, z=1.3), hud=[dict(t=124.97, type='circle', text='RULE 4', x=1080, y=500, color='#c63449', draw=0.35)],
  energy='lipstick circle drawing, fast push 6 %/s')
X(T(45), 'INSERT', 'ours', 'cabin_now/hands', 'night',
  'FLASH-FORWARD TONIGHT: big adult forearms in green CEDAR LAKE cuffs halfway up the arm, shaking', FA(7, x=960, y=540, z=1.1),
  chars=[hands('noah_grown', 960, 560, 560, [A(R(0), 'tremble', amount=0.5)], cuffs='halfway')],
  hud=[teaser(T(45), 'TONIGHT'), chip(T(45), 'TONIGHT', 'teaser')], teaser='TONIGHT', tr='glitch',
  energy='hands trembling, the cuffs straining, fast push 7 %/s')
X(T(46), 'DOC', 'ours', 'camp_gate/poster_ecu', 'night',
  'ECU of the poster line LAST SEEN WEARING A GREEN SWEATSHIRT, the highlight glowing [R 35.3] (critic M7: no cut back out to the '
  'night gate); the camera travels on into card 1',
  P(3, x=960, y=500, z=1.05), reuse=35.34, tr='glitch',
  energy='highlight glowing, push 4 %/s')

# ================================================================ RULE 1 (card 129.80-133.56)
RULE(1)
X(card_times(1)[1], 'WS', 'ours', 'cabin_now/profile', 'night',
  're-establishing wide: you kneel at the mirror, Tess beside you with the beam on the glass', P(3, x=960, y=540, z=1.0), reuse=88.7, tr='smear',
  chars=[body('you', 900, 980, 330, 'profile_right', 'tense', [A(R(0.2), 'reach')], kneel=True),
         body('tess', 600, 980, 430, 'profile_right', 'tense', [A(R(0), 'flashlight', aim='mirror')])],
  energy='your hand rising to the glass, dust in the beam, push 3 %/s')
X(Wc(49, 'top'), 'POV', 'ours', 'mirror/glass_cu', 'night',
  'POV olive sleeve: your fingertip touches the top step; the lipstick smears; numeral 1 pops beside it', P(3, x=1100, y=360, z=1.15),
  chars=[POVH([A(w(49, 'step'), 'touch_glass', at=(1230, 300))], 1300, 520)], hud=[count_pop(134.95, 1, 1300, 300)],
  props=dict(smeared='1 at 134.95'), device=DEV('diagram', 'D2', 'counting: a numeral pops beside each smeared step'),
  energy='finger smearing wax, push 3 %/s')
X(T(50), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you watching your fingertip smear the lipstick; red crumbs catch the beam in the foreground',
  P(3, x=960, y=520, z=1.05), chars=[bust('you', 960, 560, 1.0, 'q_right', 'tense', [A(R(0.3), 'look', x=1300, y=500)], light=L_BEAM)],
  dof=dict(focus=1.0, dof=6.75), energy='crumbs drifting in the foreground, push 3 %/s')
X(T(51), 'POV', 'ours', 'mirror/glass_cu', 'night', 'POV: the next step smears: 2, then 3, 4, 5 pop as the finger descends',
  P(3, x=1060, y=460, z=1.1), chars=[POVH([A(137.6, 'touch_glass', at=(1178, 370)), A(138.0, 'touch_glass', at=(1126, 440)),
                                        A(138.3, 'touch_glass', at=(1074, 510)), A(138.6, 'touch_glass', at=(1022, 580))], 1200, 640)],
  hud=[count_pop(137.55, 2, 1250, 370), count_pop(137.95, 3, 1198, 440), count_pop(138.30, 4, 1146, 510), count_pop(138.62, 5, 1094, 580)],
  props=dict(smeared='2-5 by 138.6'), energy='the finger descending step by step, numerals popping')
X(T(52), 'POV', 'ours', 'mirror/glass_cu', 'night', 'POV: steps 6 and 7 smear; the numerals 1-7 stand beside the smeared steps (D2)',
  P(3, x=1000, y=540, z=1.05), chars=[POVH([A(139.0, 'touch_glass', at=(970, 650)), A(139.5, 'touch_glass', at=(918, 720))], 1100, 800)],
  hud=[count_pop(139.05, 6, 1042, 650), count_pop(139.55, 7, 990, 720)], energy='the last smears, all seven numerals glowing')
STATE(139.6, smeared=7)
X(140.55, 'INSERT', 'ours', 'cabin_now/hands', 'night',
  'fingertip insert: seven red marks on your fingertip, counted', P(4, x=960, y=540, z=1.3),
  chars=[POVH([A(R(0.1), 'rub_thumb')], 960, 600, 560)], device=DEV('insert', 'fingertip', 'seven red marks on your finger'),
  energy='thumb rubbing the marks, push 4 %/s')
X(T(53), 'POV', 'ours', 'mirror/glass_cu', 'night', 'POV: the finger moves below step 7 and rests on the eighth line: no smear',
  P(3, x=900, y=720, z=1.2), chars=[POVH([A(w(53, 'eighth'), 'touch_glass', at=(860, 790))], 980, 900)],
  energy='the finger sliding down, the line glowing, push 3 %/s')
X(Wc(53, 'your'), 'INSERT', 'ours', 'mirror/glass_cu', 'night',
  'the nail on the eighth line: CLICK at 143.29 with a camera hit and a white flash; label CLEAN GLASS', SIL(1.5, x=860, y=790, z=1.45, hit=[(143.29, 10)], snap=(143.29, 1.08)),
  chars=[POVH([A(143.29, 'nail_tap')], 920, 860, 480)], hud=[label(143.40, 'CLEAN GLASS', [860, 790], dx=200, dy=-120)],
  fx_post=[dict(t=143.29, white=0.85, dur=0.05)], energy='silence push, then the click jolt')
X(Wc(53, 'against'), 'DIAGRAM', 'ours', 'diagram/side_view', 'night',
  'D3 side view: the glass plane edge-on, the seven drawn steps ON it, the eighth step BEHIND it, a dashed line between',
  P(2.5), plate=dict(set='mirror', view='glass_cu', var='night', post=dict(blur=10, dim=0.5)),
  hud=[diagram(143.65, 'D3', 'side view: glass plane; steps 1-7 drawn on the glass; step 8 behind the glass (dashed)', hold=1.5)],
  device=DEV('diagram', 'D3', 'the eighth step is behind the glass'), energy='lines drawing on, the 8th step sliding back behind the plane')
X(T(54), '2S', 'ours', 'cabin_now/ots_mirror', 'night', 'you tilt the mirror frame with both hands; Tess steadies the beam',
  P(3, x=960, y=540, z=1.05), chars=[body('you', 1100, 1040, 600, 'back', 'tense', [A(w(54, 'tilt'), 'tilt_frame', deg=-13)], kneel=True),
                                    body('tess', 700, 1040, 620, 'q_right', 'tense', [])],
  energy='frame tilting, the reflection swinging, push 3 %/s')
X(T(55), 'WS', 'ours', 'mirror/glass_tilt', 'night',
  'the whole mirror, frame and drawing tilted at -13 deg; the eighth line stays level, a dashed level guide across it', P(3, x=960, y=600, z=1.1),
  hud=[level_guide(146.6, 680, -13.0, 1.6)], props=dict(mirror='tilted -13'), energy='frame settling at -13, the line rock steady')
X(T(56), 'WS', 'stairs', 'mirror/queen_glass', 'stairs',
  'she stands on the eighth line inside the glass, back three-quarters, lit: 25 % of frame height; crown glint, fan collar, '
  'waist-length hair; perfectly level in a tilted frame', P(4, x=960, y=600, z=1.05),
  chars=[Q('S0', [980, 880, 270, 1.04], mode='body', view='back', acts=[A(R(0), 'drift')])],
  q=dict(stage='S0', step=8, size=0.25, where='glass, step 8', framing='WS 25 %', wrong='stands level in a tilted world'),
  energy='the hem swaying 3 px, crown glint, frame tilted around her, push 4 %/s')
STATE(148.23, queen='glass_step8')
X(T(57), 'MS', 'stairs', 'mirror/queen_glass', 'stairs',
  'MS of the dress: black satin sheen, the hem border of white spade pips between red lines', P(3.5, x=960, y=700, z=1.2),
  chars=[Q('S0', [960, 1100, 900], mode='body', view='back', acts=[A(R(0), 'hem_sway')])], energy='satin sheen sliding, hem swaying')
X(Wc(57, 'looking'), 'CU', 'stairs', 'mirror/queen_glass', 'stairs',
  'CU of her bowed head: the face hidden by straight black hair, the crown of spades', P(4, x=960, y=420, z=1.3),
  chars=[Q('S0', [960, 480, 1.1], view='back', acts=[A(R(0), 'still')])], setup='Q_BOWED',
  q=dict(stage='S0', step=8, size=0.45, where='glass, step 8', framing='CU of the bowed head', wrong=''),
  energy='hair sheen shifting, crown glint, push 4 %/s')
X(153.75, 'INSERT', 'stairs', 'mirror/queen_glass', 'stairs',
  'her hand at her side: porcelain, black almond nails, the index and middle fingertips smudged lipstick red', P(4, x=960, y=600, z=1.4),
  chars=[Q('S0', [960, 600, 560], mode='hands', acts=[A(R(0), 'fingers_curl', amount=0.2)])], energy='fingers curling slowly')
X(T(58), 'OTS', 'ours', 'mirror/through', 'stairs',
  'push past her shoulder into the glass: behind her the reflection opens up, gold', FA(6, x=1060, y=520, z=1.2),
  chars=[Q('S0', [700, 600, 1.4], view='back', acts=[A(R(0), 'still')])], energy='fast push past her into the gold')
X(Wc(58, 'cabin'), 'WS', 'theirs', 'cabin_dawn/top_stairs', 'dawn',
  'THEIRS from the top of the stairs: the gold, mirror-flipped Cabin 7 below, frozen; chip THE OTHER SIDE · 6:59 AM',
  P(2.5, x=960, y=600, z=1.0), tr='glint', chip='THE OTHER SIDE · 6:59 AM', errfix=[31],
  energy='motes twinkling in place, curtains frozen at 12 deg, push 2.5 %/s')
X(T(59), 'WS', 'theirs', 'cabin_dawn/swimsuits', 'dawn',
  'a row of damp swimsuits (teal, coral, violet, lemon) over the top rail', DR(2, dx=26),
  device=DEV('insert', 'swimsuits', 'damp swimsuits on the rail'), energy='one drip each, drifting camera')
X(Wc(59, 'hanging'), 'WS', 'theirs', 'cabin_dawn/top_stairs', 'dawn',
  'high wide from the top of the stairs: the swimsuits over the top-bunk rail, a drip falling to the boards (Noah\'s bunk hidden under the rail)',
  P(3, x=960, y=600, z=1.05), energy='the drip falling, motes twinkling in place, push 3 %/s')
X(T(60), 'WS', 'theirs', 'cabin_dawn/door_wash', 'dawn', 'the wash-house door swings in: wet morning light on the boards',
  P(3), device=DEV('insert', 'wash_door', 'someone came in from the wash house'), energy='the door swinging in, light sliding over the floor')
X(163.05, 'WS', 'theirs', 'cabin_dawn/floor_prints', 'dawn', 'low wide across the floor at the wash-house door: water spreading over the sill',
  P(3, x=960, y=600, z=1.0), energy='water creeping, push 3 %/s')
X(T(61), 'WS', 'theirs', 'cabin_dawn/overhead', 'dawn', 'high angle on the floor: two sets of wet footprints appear on the cues, one per 0.42 s',
  P(2.5), props=dict(prints='appearing 165.52-173.68'), energy='prints appearing one by one')
X(Wc(61, 'appear', off=-0.3), 'WS', 'theirs', 'cabin_dawn/floor_prints', 'dawn', 'closer: the prints lead toward Noah\'s bunk',
  P(3, x=1000, y=600, z=1.1), energy='prints appearing toward the bunk, push 3 %/s')
X(T(62), 'WS', 'theirs', 'cabin_dawn/overhead', 'dawn', 'high angle: the bare prints (long toes) walking beside the others toward the bunk',
  P(3, x=960, y=560, z=1.05),
  energy='a print forming, water sheen')
X(T(63), 'INSERT', 'theirs', 'cabin_dawn/floor_prints', 'dawn', 'ECU: a sneaker print', P(4, x=960, y=600, z=1.3), energy='a print forming')
X(Wc(63, 'then'), 'WS', 'theirs', 'cabin_dawn/overhead', 'dawn',
  'high wide: then a bare print after the sneaker print; the trail runs shoe, bare, shoe, bare toward the foot of Noah\'s bunk (bunk at the frame edge)',
  P(2.5, x=960, y=560, z=1.0), energy='prints appearing across the room, motes twinkling')
X(T(64), 'INSERT', 'theirs', 'cabin_dawn/floor_prints', 'dawn',
  'held insert: the shoe-then-bare trail to Noah\'s bunk; label ONE SHOE', P(3, x=980, y=560, z=1.1),
  hud=[label(172.8, 'ONE SHOE', [1100, 620], dx=170, dy=-110)], device=DEV('insert', 'one_shoe', 'one shoe, then a bare foot: ONE SHOE'),
  energy='the trail glinting, push 3 %/s')
X(T(65), 'MS', 'ours', 'cabin_now/ots_mirror', 'night', 'OURS: Tess angles the flashlight toward the floor', P(3), tr='glint',
  chars=[body('tess', 900, 1060, 640, 'q_right', 'tense', [A(w(65, 'angles'), 'flashlight', aim='floor')])], energy='the beam swinging down')
X(176.00, 'WS', 'ours', 'cabin_now/overhead', 'night', 'overhead wide of Cabin 7: the beam pool slides over our dusty floor from the mirror toward the door',
  P(3, x=960, y=560, z=1.0), energy='beam pool sliding, dust lifting')
X(T(66), 'SPLIT', 'ours', 'split/floors', 'night',
  'D4 split: THEIR FLOOR (wet prints, chip 6:59 AM · 14 YEARS AGO) | OUR FLOOR (smooth dust in the beam, chip 11:59 PM · TONIGHT)',
  P(2),
  split=dict(panels=[dict(set='cabin_dawn', view='floor_prints', var='dawn', world='theirs', label='THEIR FLOOR', chip='6:59 AM · 14 YEARS AGO'),
                     dict(set='cabin_now', view='floor_cu', var='night', world='ours', label='OUR FLOOR', chip='{ours} · TONIGHT')]),
  hud=[diagram(176.70, 'D4', 'split: THEIR FLOOR (wet prints) | OUR FLOOR (smooth dust)', hold=1.6)],
  device=DEV('diagram', 'D4', 'two times: their floor has prints, ours is untouched'), energy='prints glinting left, dust drifting right')
X(Wc(66, 'smooth'), 'WS', 'ours', 'cabin_now/reverse', 'night',
  'OUR FLOOR (reverse wide toward the door): the smooth dust film from the door to the bed, the beam sweeping along it', DR(1.5, dx=40, x=960, y=620, z=1.05),
  energy='the beam travelling along untouched dust')
X(T(67), 'WS', 'stairs', 'stairs/down', 'stairs',
  'the stairs from the top: at the bottom, Noah13 on his bunk by the railing, face up, a speech glow (silence)', SIL(1.5, x=960, y=600, z=1.1),
  chars=[body('noah13', 960, 860, 160, 'front', 'calm_kid', [A(R(0.5), 'look_up')], d=8.0, seated=True)], tr='glint',
  energy='fog sliding, the red edges breathing, slow push 1.5 %/s')
X(T(68), 'CU', 'theirs', 'mirror/through', 'dawn',
  'CU of Noah13 through the glass (glints on the glass), gap teeth, lip-sync: "Did they ring it yet?"', P(3, x=960, y=520, z=1.05),
  chars=[bust('noah13', 960, 560, 1.0, 'front', 'calm_kid', [A(t(68), 'talk', line=68)], light=L_GOLD, through_glass=True)],
  dof=dict(focus=1.0, dof=6.75), voice_fx='below', energy='lip-sync, glass glints sliding, push 3 %/s')
X(T(69), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you, eyes wet: you know the voice', P(3), tr='glint',
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'fear', [A(w(69, 'immediately'), 'expr', name='grief', fade=0.6)], light=L_BEAM)],
  dof=dict(focus=1.0, dof=6.75), energy='fear melting into grief, bokeh drift, push 3 %/s')
X(T(70), 'UI', 'ui', 'ui/voicemail', 'phone', 'your phone: VOICEMAIL list, NOAH · 0:09 · JUL 18', HH(1.5, shake=6),
  hud=[dict(t=T(70), type='phone', state='voicemail_list', name='NOAH', items=['NOAH  ·  0:09  ·  JUL 18', 'MOM  ·  0:31', 'MOM  ·  1:02'], x=960, y=560)],
  props=dict(your_phone='voicemail'), device=DEV('doc', 'voicemail', 'the 14-year-old voicemail from Noah'), energy='thumb scrolling, handheld')
X(T(71), 'CU', 'ours', 'cabin_now/bokeh', 'night',
  'CU of you, the phone at your ear playing the voicemail; its glow on your cheek; a small waveform inset lower right', P(2.5),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0), 'phone_to_ear', side=1)], light=L_PHONE)], dof=dict(focus=1.0, dof=6.75),
  hud=[dict(t=T(71), type='phone', state='voicemail', name='NOAH', timer='0:03', waveform=dict(seed=7, progress='live'), x=1600, y=860, scale=0.4, inset=True)],
  energy='listening, the waveform inset moving')
X(Wc(71, 'changing'), 'CU', 'memory', 'memory/office_phone', 'sepia_day',
  'memory CU: Noah at the camp office payphone, laughing into the receiver ("you brat"), the watch on his wrist', P(3), tr='sepia',
  chars=[bust('noah13', 960, 560, 1.0, 'q_right', 'laugh', [A(R(0), 'laugh')], light=L_MEM, receiver=True)],
  energy='laughing, the cord swinging')
X(T(72), 'CU', 'theirs', 'mirror/through', 'dawn', 'CU of Noah13 through the glass, talking to himself, the same boy',
  P(3, x=960, y=520, z=1.08), chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(R(0.2), 'talk_silent', dur=1.2)], light=L_GOLD, through_glass=True)],
  dof=dict(focus=1.0, dof=6.75), energy='lips moving, glass glints, push 3 %/s')
X(T(73), 'ECU', 'theirs', 'mirror/through', 'dawn', 'ECU of Noah13\'s gap teeth with a whistle curl', P(4, x=960, y=600, z=1.25),
  chars=[bust('noah13', 960, 520, 1.7, 'front', 'grin_kid', [A(R(0), 'whistle_s')], light=L_GOLD)], energy='whistle curl particles, push 4 %/s')
X(195.00, 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you smiling through tears', P(2.5), tr='glint',
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'relief_cry', [A(R(0.2), 'tears', amount=0.8)], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='a tear running, push 2.5 %/s')
X(T(74), 'CU', 'ours', 'mirror/glass_cu', 'night', 'CU of you leaning close to the glass; your breath fogs it', SIL(1.5, x=960, y=520, z=1.15),
  chars=[bust('you', 780, 600, 1.1, 'profile_right', 'grief', [A(R(0.1), 'lean_in', amount=0.4)], light=L_BEAM, reflection=True)],
  energy='fog blooming on the glass, slow push (silence)')
X(T(75), 'MS', 'stairs', 'mirror/queen_glass', 'stairs', 'MS of the back of her head in the glass (silence)', SIL(1.5, x=960, y=460, z=1.1),
  chars=[Q('S0', [960, 560, 1.0], view='back', acts=[A(R(0), 'still')])], energy='hair sheen, slow push (silence)')
X(198.15, 'MS', 'stairs', 'mirror/queen_glass', 'stairs',
  'the head snaps 130 deg in 0.18 s while the hair stays put (whip, white flash)', WH(1040, 460, 1.2), tr='white',
  chars=[Q('S1', [960, 560, 1.0], view='back', acts=[A(198.15, 'head_snap', deg=130, dur=0.18, hair_lag=0.4)])],
  q=dict(stage='S1', step=8, size=0.45, where='glass, step 8', framing='MS', wrong='head turns 130 deg, the hair does not follow'),
  energy='the snap, whip pan, hair hanging wrong')
X(198.55, 'CU', 'stairs', 'mirror/queen_glass', 'stairs',
  'CU: the calm, beautiful face, eyes into the lens; no blink; the spade beauty mark', P(3, x=960, y=500, z=1.1),
  chars=[Q('S1', [960, 540, 1.1], acts=[A(R(0), 'stare'), A(R(0.2), 'drift')])],
  q=dict(stage='S1', step=8, size=0.45, where='glass, step 8', framing='CU face 45 %', wrong='looks into the lens (1 of 3)'),
  energy='hair settling too fast, her stillness against the drifting dust, push 3 %/s')
STATE(198.15, queen='glass_step8_turned')
X(T(76), 'CU', 'stairs', 'mirror/queen_glass', 'stairs', '[R 152.3] her bowed head, a second ago, listening down the stairs', P(3, x=960, y=420, z=1.3),
  chars=[Q('S0', [960, 480, 1.1], view='back', acts=[A(R(0), 'still')])], reuse=152.4, past=True, energy='push 3 %/s, the crown glint')
X(Wc(76, 'she'), 'WS', 'stairs', 'stairs/down', 'stairs',
  'a second ago [R 180.2]: the stairs from above: her head bent toward Noah13 talking at the bottom (the listening line)', P(2.5, x=960, y=620, z=1.05), reuse=180.15, past=True,
  chars=[Q('S0', [960, 760, 360, 3.0], mode='body', view='back', acts=[A(R(0), 'head_tilt', deg=10)]),
         body('noah13', 960, 880, 140, 'front', 'calm_kid', [A(R(0), 'talk_silent', dur=1.5)], d=8.0, seated=True)],
  energy='fog drifting, Noah talking, push 2.5 %/s')
X(T(77), 'SPLIT', 'stairs', 'split/eyes', 'stairs',
  'D5 eye line: her unblinking eye (left) beside your eye (right), joined by a dashed red line; then the glitch into card 2',
  P(4), split=dict(panels=[dict(set='mirror', view='queen_glass', var='stairs', world='stairs', subject='queen eye ECU'),
                           dict(set='cabin_now', view='bokeh', var='night', world='ours', subject='your eye ECU')]),
  chars=[Q('S1', [480, 540, 2.6], acts=[A(R(0), 'stare')]), bust('you', 1440, 540, 2.6, 'front', 'fear', [A(R(0.4), 'blink')], light=L_BEAM)],
  hud=[eye_line(202.40, [560, 520], [1360, 520], 1.1), diagram(202.35, 'D5', 'her eye -> your eye (dashed red line)', hold=1.1)],
  q=dict(stage='S1', step=8, size=1.0, where='glass', framing='ECU of the eye', wrong='no blink'),
  device=DEV('diagram', 'D5', 'she is now listening to YOU: the eye line'), energy='the dashed line drawing, your blink, her none')

# ================================================================ RULE 2 (card 203.53-208.32)
RULE(2)
X(card_times(2)[1], 'WS', 'ours', 'cabin_now/master', 'night',
  're-establishing wide [R C7 master]: you kneel at the mirror; Tess behind you tells you to put it down', P(3), reuse=72.31, tr='smear',
  chars=[body('you', 1060, 760, 300, 'back', 'tense', [], kneel=True), body('tess', 820, 900, 380, 'q_right', 'tense', [A(w(80, 'tells'), 'talk_silent', dur=1.2)])],
  energy='beam wobble, dust, push 3 %/s')
X(209.40, 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of Tess: "put it down"', P(3),
  chars=[bust('tess', 960, 560, 1.0, 'q_left', 'fear', [A(R(0), 'talk_silent', dur=0.6)], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='talking, bokeh drift')
X(T(81), 'POV', 'ours', 'mirror/glass_wide', 'night', 'POV: your hands on the frame; the fingers twitch open and clamp back',
  P(3.5, x=960, y=600, z=1.05), chars=[POVH([A(w(81, 'try'), 'grip_frame', fail=True)], 960, 760, 760, both=True)],
  energy='fingers twitching, the frame trembling, push 3.5 %/s')
X(T(82), 'WS', 'stairs', 'mirror/queen_glass', 'stairs',
  'mirror wide: she is on STEP 7 (1.25x her 148 s size), facing you', P(3, x=960, y=560, z=1.0),
  chars=[Q('S1', [960, 860, 340, 1.04], mode='body', acts=[A(R(0), 'drift')])],
  q=dict(stage='S1', step=7, size=0.32, where='glass, step 7', framing='WS 32 %', wrong='she climbs while nobody watches'),
  energy='her drift, the red edges breathing, push 3 %/s')
STATE(211.49, queen='glass_step7')
X(Wc(82, 'railing'), 'MS', 'stairs', 'stairs/railing', 'stairs',
  'behind her, at the foot of the stairs, a small hand pokes through the balusters of the stair railing (Noah\'s bunk is right there)',
  P(4, x=1100, y=600, z=1.15), chars=[Q('S1', [600, 900, 520, 1.04], mode='body', view='back', acts=[A(R(0), 'still')]),
                                      hands('noah13', 1180, 680, 190, [A(R(0.2), 'reach_through', through='railing')], tape=True)],
  errfix=[31], energy='the hand reaching through, push 4 %/s')
X(T(83), 'INSERT', 'stairs', 'stairs/railing', 'stairs',
  'ECU of the taped hand: middle, ring and little fingers wrapped together, two bands, a lifting edge; label BLUE MEDICAL TAPE',
  P(4, x=960, y=540, z=1.3), chars=[hands('noah13', 960, 560, 520, [A(R(0), 'fingers_flex')], tape=True)],
  hud=[label(216.9, 'BLUE MEDICAL TAPE', [960, 520], dx=180, dy=-140)], errfix=[14],
  device=DEV('insert', 'tape', 'three fingers taped with blue medical tape'), energy='fingers flexing, tape sheen, push 4 %/s')
X(Wc(83, 'blue'), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you: you know that tape; your eyes fill', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0.3), 'tears', amount=0.4)], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='eyes filling, bokeh drift, push 3 %/s')
X(T(84), 'WS', 'memory', 'memory/tape_wrap', 'sepia_day',
  'memory wide, the family kitchen: Mom (her face out of frame) wraps blue tape around three of kid Noah\'s fingers at the table', P(3), tr='sepia',
  chars=[body('noah13', 1040, 980, 460, 'q_left', 'sad', [A(R(0), 'flinch')], seated=True), hands('mom', 860, 560, 360, [A(R(0.1), 'wrap_tape')])],
  energy='tape wrapping, a sniffle')
X(Wc(84, 'after'), 'WS', 'memory', 'memory/car_door', 'sepia_day',
  'memory: the family car; the door slams on a small hand; kid Noah crying', P(3),
  chars=[body('noah13', 960, 960, 520, 'q_right', 'scream', [A(220.40, 'flinch')])], energy='the door swinging shut on "shut" (220.4), crying')
X(221.57, 'DOC', 'memory', 'memory/polaroid', 'sepia_day',
  'the polaroid: Noah by the family car holding up the taped fingers', P(3, x=960, y=540, z=1.05),
  hud=[doc(221.6, 'polaroid', 'NOAH · JUNE (taped fingers)')], device=DEV('doc', 'polaroid', 'the tape polaroid'),
  energy='polaroid edge curling, push 3 %/s')
X(T(85), 'INSERT', 'stairs', 'stairs/railing', 'stairs', 'ECU through the railing: his thumbnail picks at the tape edge', P(3.5, x=960, y=540, z=1.4), tr='sepia',
  chars=[hands('noah13', 960, 560, 600, [A(222.46, 'peel_tape'), A(222.76, 'peel_tape'), A(223.06, 'peel_tape')], tape=True)],
  energy='thumbnail picking, push 3.5 %/s')
X(224.60, 'MS', 'memory', 'memory/bench', 'sepia_day', 'memory: Noah on the bench by the lake picking at the tape, kid-you beside him waiting',
  P(3), tr='sepia', chars=[body('noah13', 860, 1040, 640, 'q_right', 'shy', [A(R(0), 'peel_tape')], seated=True),
                           body('you_kid', 1160, 1040, 560, 'q_left', 'sure', [], seated=True)],
  energy='lake glitter, picking')
X(Wc(86, 'had'), 'CU', 'memory', 'memory/bench', 'sepia_day', 'memory CU: Noah opens his mouth to say something; nothing comes',
  P(3.5), chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'shy', [A(R(0.3), 'mouth_open'), A(R(1.0), 'mouth_open_close')], light=L_MEM)],
  energy='lips parting and closing')
X(228.0, 'WS', 'stairs', 'mirror/queen_glass', 'stairs',
  'back to the glass, wide: she still stands on step 7; behind her at the foot of the stairs the small taped hand picks at the railing',
  P(3, x=960, y=560, z=1.0), tr='sepia',
  chars=[Q('S1', [900, 860, 340, 1.04], mode='body', acts=[A(R(0), 'drift')]), hands('noah13', 1260, 800, 90, [A(R(0), 'peel_tape')], tape=True)],
  q=dict(stage='S1', step=7, size=0.32, where='glass, step 7', framing='WS', wrong=''), energy='picking, fog, her drift')
X(T(88), 'MS', 'ours', 'cabin_now/ots_mirror', 'night',
  'Tess tugs your shoulder; in the glass behind you, she is on STEP 6', P(3),
  chars=[body('tess', 760, 1060, 640, 'q_right', 'fear', [A(w(88, 'tells'), 'grab_shoulder')]),
         body('you', 1100, 1060, 620, 'back', 'grief', [], kneel=True), Q('S1', [1500, 700, 220, 1.04], mode='body', acts=[A(R(0), 'drift')])],
  q=dict(stage='S1', step=6, size=0.40, where='glass, step 6', framing='background, 40 %', wrong='closer again'),
  energy='the tug, her drift in the glass, push 3 %/s')
STATE(230.0, queen='glass_step6')
X(T(89), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you: "the last thing you said to Noah..."', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0), 'talk_silent', dur=1.4)], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  energy='lips moving, push')
X(234.12, 'MS', 'stairs', 'mirror/queen_glass', 'stairs', 'the glass behind you: she is on STEP 5, nobody watching',
  P(3, x=960, y=520, z=1.1), chars=[Q('S1', [960, 820, 420, 1.04], mode='body', acts=[A(R(0), 'drift')])],
  q=dict(stage='S1', step=5, size=0.45, where='glass, step 5', framing='MS', wrong='she climbs while nobody watches'),
  energy='her drift, the hot spot sliding')
STATE(233.76, queen='glass_step5')
X(T(90), 'WS', 'memory', 'memory/night_window', 'sepia_night',
  'memory, night: kid-you grumbling at Noah by the open window: shut the window', P(2.5), tr='sepia',
  chars=[body('you_kid', 700, 940, 360, 'q_right', 'sad', [A(R(0), 'talk_silent', dur=1.0)]), body('noah13', 1200, 940, 380, 'q_left', 'shy', [])],
  energy='lantern flicker, moths')
X(T(91), 'WS', 'memory', 'memory/night_window', 'sepia_night', 'memory wide: the lantern on the sill swarmed by bugs and moths; Noah shrugs at the open window',
  P(3), chars=[body('noah13', 1200, 940, 380, 'q_left', 'shy', [A(R(0.3), 'shrug')])], energy='moths fluttering, lantern flicker')
X(T(92), 'CU', 'ours', 'cabin_now/bokeh', 'night',
  'CU of you speaking (lip-sync): "I wish I\'d had one more minute with him"; RED X (2 of 4) over your mouth on "wish"; tag KEEP IT TO YOURSELF',
  P(3), chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(t(92), 'talk', line=92)], light=L_BEAM)], dof=dict(focus=1.0, dof=6.75),
  hud=[redx(238.17, 960, 690, 150, 0.9, n=2), tag(238.25, 'KEEP IT TO YOURSELF', 960, 150, 'lipstick', 1.0)], tr='sepia',
  energy='talking, the X drawing on, push 3 %/s')
X(Wc(92, 'one'), 'ECU', 'stairs', 'mirror/queen_glass', 'stairs', 'ECU of her eyes in the glass, STEP 4, no blink',
  P(4, x=960, y=480, z=1.6), chars=[Q('S1', [960, 520, 2.0], acts=[A(R(0), 'stare')])],
  q=dict(stage='S1', step=4, size=1.0, where='glass, step 4', framing='ECU of the eyes', wrong='she heard it'),
  energy='eyes locked, the irises glinting, push 4 %/s')
STATE(239.2, queen='glass_step4')
X(T(93), 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of you finishing the wish', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0), 'swallow')], light=L_BEAM)], energy='a swallow')
X(T(94), '2S', 'ours', 'cabin_now/three_q', 'night', '2-shot: you facing Tess, the mirror behind you', P(3),
  chars=[body('you', 1060, 1040, 600, 'q_left', 'grief', [A(R(0), 'look', x=760, y=440)]), body('tess', 760, 1040, 590, 'q_right', 'sad', [])],
  energy='the beam between you, push 3 %/s')
X(T(95), 'CU', 'memory', 'memory/kitchen_15', 'sepia_day', 'memory flash: CU of you at 15 at the kitchen table saying it', FA(5), tr='sepia',
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0), 'talk_silent', dur=0.6)], light=L_MEM, age=15)], energy='flash, fast push')
X(243.30, 'CU', 'memory', 'memory/car_20', 'sepia_day', 'memory flash: CU of you at 20 in a car saying it', FA(5),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0), 'talk_silent', dur=0.6)], light=L_MEM, age=20)], energy='flash, fast push')
X(243.90, 'CU', 'ours', 'cabin_now/bokeh', 'night', 'CU of Tess: she has heard it a hundred times', P(3), tr='sepia',
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'sad', [A(R(0), 'nod')], light=L_BEAM)], energy='a small nod')
X(T(96), 'OTS', 'ours', 'mirror/reflection', 'night',
  'OTS on your reflection in the glass; behind its shoulder something pale rises (step 3)', SIL(1.5, x=1000, y=500, z=1.1),
  chars=[bust('you', 760, 640, 1.3, 'back', 'grief', [], light=L_BEAM), Q('S1', [1180, 480, 0.6], acts=[A(R(0), 'rise', dy=-30)], in_glass=True)],
  q=dict(stage='S1', step=3, size=0.25, where='glass, step 3', framing='behind your reflection', wrong='rising'),
  energy='slow push (silence), her face rising')
STATE(245.26, queen='glass_step3')
X(246.99, 'OTS', 'ours', 'mirror/reflection', 'night',
  'tighter: her face right behind your reflection\'s shoulder (STEP 2), pale, lit; push', SIL(2.0, x=1100, y=480, z=1.25),
  chars=[bust('you', 760, 640, 1.3, 'back', 'grief', [], light=L_BEAM), Q('S1', [1160, 460, 0.9], acts=[A(R(0), 'still')], in_glass=True)],
  q=dict(stage='S1', step=2, size=0.35, where='glass, step 2', framing='face behind your reflection 35 %', wrong='right behind you'),
  energy='slow push in the silence')
STATE(247.0, queen='glass_step2')
X(T(97), 'CU', 'stairs', 'mirror/queen_glass', 'stairs',
  'CU in the glass: "You have it." lip-sync, a thin red glow on the mouth while she speaks', P(3, x=960, y=520, z=1.15, accel=[(248.39, 1.06, 0.6)]),
  tr='white', chars=[Q('S1', [960, 560, 1.2], acts=[A(t(97), 'talk_line', line=97, glow=True)])],
  q=dict(stage='S1', step=1, size=0.70, where='glass, the top', framing='CU face 70 %', wrong='she speaks'),
  errfix=[20], energy='lips moving, red glow, punch-in')
STATE(248.3, queen='glass_top')
X(T(98), 'MS', 'ours', 'cabin_now/ots_mirror', 'night', 'Tess snatches the towel (motion blur)', HH(3, shake=20),
  chars=[body('tess', 900, 1060, 640, 'q_right', 'fear', [A(w(98, 'snatches'), 'snatch', prop='towel')])],
  props=dict(towel='tess_hands at 249.67'), energy='snatch blur, handheld')
STATE(249.67, towel='tess_hands')
X(Wc(98, 'throws'), 'MS', 'ours', 'cabin_now/ots_mirror', 'night', 'the towel flies at the lens (whip), then drapes over the mirror; the beam swings off it',
  WH(1240, 520, 1.15),
  chars=[body('tess', 760, 1060, 640, 'q_right', 'fear', [A(R(0), 'step_back')])], props=dict(towel='over_glass at 251.75'),
  energy='towel settling, beam swinging')
STATE(251.75, towel='over_glass', mirror='towel_over')
X(T(99), 'MS', 'ours', 'mirror/towel_over', 'night', 'the draped towel, still; Tess backing away', P(2.5),
  chars=[body('tess', 700, 1060, 600, 'q_right', 'fear', [A(R(0), 'step_back')])], energy='breathing, the towel still')
X(Wc(99, 'fingers'), 'INSERT', 'ours', 'mirror/towel_over', 'night',
  'five long fingertips push the cloth toward the lens, lipstick red bleeding through the terry at the tips (towel layer bounds checked)',
  FA(6, x=960, y=500, z=1.3), chars=[Q('S1', [960, 520, 700], mode='hands', acts=[A(R(0), 'press_through_cloth', depth=1.0, red_bleed=True)])],
  q=dict(stage='S1', where='through the towel', framing='fingers to the lens', wrong='red bleeds through the cloth'), errfix=[22],
  energy='cloth stretching toward camera, fast push 6 %/s')
X(T(100), 'MS', 'ours', 'mirror/towel_over', 'night', 'silence: the towel hanging on the frame', SIL(1.5),
  energy='slow push in the silence, a thread trembling')
X(256.87, 'WS', 'ours', 'cabin_now/profile', 'night',
  'the towel falls flat onto the floor: NO GLASS behind it; dust burst; camera hit; held wide', P(2, hit=[(256.87, 12)]), tr='white',
  props=dict(mirror='doorway at 256.87', towel='floor_flat'), reuse=88.7, errfix=[22],
  energy='towel dropping, dust bursting and settling, camera hit')
STATE(256.87, mirror='doorway', doorway='gold', towel='floor_flat', queen='absent')
X(Wc(100, 'mirror'), 'WS', 'ours', 'cabin_now/floor_cu', 'night',
  'low: the towel lying flat, dust settling, the empty frame above glowing faintly gold', P(2.5, x=960, y=600, z=1.05),
  energy='dust settling, gold haze creeping out')
X(T(101), 'WS', 'ours', 'cabin_now/master', 'doorway_glow',
  'master wide [R 72.3]: the doorway at the mirror spot, inside the same white chipped frame, gold haze', P(3), reuse=72.31,
  chars=[body('you', 1060, 760, 300, 'back', 'shock', [], kneel=True), body('tess', 800, 900, 380, 'q_right', 'fear', [])],
  energy='gold rays, dust, push 3 %/s')
X(Wc(101, 'reflection'), 'MS', 'ours', 'cabin_now/doorway', 'doorway_glow',
  'MS of the doorway: the white chipped frame around a raw splintered opening, gold haze and rays', P(3.5, x=960, y=520, z=1.05),
  energy='rays shimmering, haze curling, push 3.5 %/s')
STATE(260.4, towel='tess_hands')
X(T(102), 'POV', 'ours', 'cabin_now/doorway_down', 'doorway_glow',
  'POV down through the doorway: eight red-edged steps descending in one-point perspective to gold light; your hands on the frame',
  P(3, x=960, y=600, z=1.05), chars=[POVH([A(R(0), 'grip_frame')], 960, 900, 700, both=True)],
  device=DEV('insert', 'stairs', 'the doorway leads down a staircase'), energy='red edges breathing, gold light pulsing below')
X(Wc(102, 'smell'), 'MS', 'ours', 'cabin_now/doorway', 'doorway_glow', 'gold steam wisps curl out of the doorway (the smell, visible)',
  P(3), energy='steam wisps curling 20 px/s')
X(T(103), 'INSERT', 'memory', 'memory/percolator', 'sepia_morning', 'memory-morning insert: a percolator bubbling on the camp stove',
  P(3), tr='sepia', energy='coffee bubbling in the glass knob, steam')
X(268.58, 'CU', 'ours', 'cabin_now/bokeh', 'doorway_glow', 'CU of Tess sniffing, afraid; gold on her face', P(3), tr='sepia',
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'fear', [A(R(0.2), 'expr', name='fear')], light=L_GOLD)], dof=dict(focus=1.0, dof=6.75),
  energy='nostrils flaring, steam drifting past, push 3 %/s')

# ================================================================ RULE 3 (card 269.24-273.35)
RULE(3)
X(card_times(3)[1], 'WS', 'ours', 'cabin_now/master', 'doorway_glow',
  're-establishing wide: you go to the gold doorway; Tess behind you', P(3), reuse=72.31, tr='smear',
  chars=[body('you', 1060, 780, 320, 'back', 'resolve', [A(R(0), 'walk', to=1100, surface='wood')]), body('tess', 820, 900, 380, 'q_right', 'fear', [])],
  energy='rays, dust, walking, push 3 %/s')
X(Wc(106, 'wide'), 'MS', 'ours', 'cabin_now/doorway', 'doorway_glow',
  'you sideways in the doorway, your shoulders against the chipped frame', P(3, x=960, y=520, z=1.05),
  chars=[body('you', 960, 1060, 640, 'profile_right', 'tense', [A(R(0.3), 'squeeze_through')])], energy='jacket scraping the frame, gold rays')
X(T(107), 'MS', 'ours', 'cabin_now/doorway', 'doorway_glow', 'MS at the doorway: Tess catches your olive sleeve in her orange cuff', FA(5),
  chars=[body('tess', 760, 1060, 620, 'q_right', 'fear', [A(w(107, 'catches'), 'grab')]), body('you', 1140, 1060, 640, 'profile_right', 'tense', [])],
  energy='the grab, fast push')
X(T(108), 'WS', 'ours', 'cabin_now/reverse', 'doorway_glow',
  'wide: Tess in the foreground holding your sleeve, the back-wall clock behind her', P(3),
  chars=[body('tess', 760, 1040, 620, 'q_right', 'fear', [A(R(0), 'grab')]), body('you', 1180, 980, 520, 'profile_left', 'tense', [])],
  energy='gold spill on the wall, push 3 %/s')
X(Wc(108, 'cabin'), 'INSERT', 'ours', 'cabin_now/clock', 'doorway_glow',
  'clock insert: the second hand jerks back three ticks with the rewind glitch', FA(5, x=1000, y=440, z=1.6),
  fx_post=[dict(t=281.69, glitch=0.6, rewind=1.0, dur=0.2)], device=DEV('insert', 'clock_back', 'our clock jerks backward'),
  energy='second hand stepping back, fast push')
X(T(109), 'MS', 'ours', 'cabin_now/doorway', 'doorway_glow',
  'silence: the gold doorway; something rises at its lower edge', SIL(1.5, x=960, y=600, z=1.05),
  energy='slow push in the silence, a pale shape rising at the edge')
X(T(110), 'CU', 'ours', 'cabin_now/doorway', 'doorway_glow',
  'HOLD H1: she leans out of the doorway, half in blue, half in gold. The lipstick smile is drawn past her lips in 3 little steps '
  'up each cheek; her lips speak ("There\'s time for both of you") but the drawing does not move; pupils pinpoint; her red-fingertip '
  'hand on the white frame', P(4, x=960, y=520, z=1.05), hold='H1', tr='white',
  chars=[Q('S2', [960, 560, 1.15], acts=[A(283.62, 'lean_out', dur=0.6), A(t(110), 'talk_line', line=110, glow=True)])],
  q=dict(stage='S2', size=0.55, where='the doorway at the mirror spot', framing='CU face 55 %', wrong='the drawn stair-smile; pinpoint pupils'),
  errfix=[19, 20, 26], energy='she leans into the light, lips talking, the drawing still, push 4 %/s')
STATE(283.62, queen='doorway')
X(286.20, '2S', 'ours', 'cabin_now/doorway', 'doorway_glow', '2-shot: your hand on Tess\'s shoulder; she plants her feet at the threshold',
  P(3), chars=[body('you', 1100, 1060, 640, 'q_left', 'resolve', [A(R(0), 'grab_shoulder')]), body('tess', 780, 1060, 620, 'q_right', 'fear', [A(R(0.3), 'nod')])],
  energy='hand on shoulder, push 3 %/s')
STATE(286.2, queen='absent')
X(T(112), 'CU', 'ours', 'cabin_now/bokeh', 'doorway_glow',
  'CU of Tess nodding: she will count down from sixty; GIANT 60 slams over her (type beat 4) and flies into the ring badge TESS 60', P(3),
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'resolve', [A(R(0.3), 'nod')], light=L_GOLD)], dof=dict(focus=1.0, dof=6.75),
  hud=[giant(289.19, 60)], energy='a nod, numeral slam, fly to the badge')
X(T(113), 'POV', 'stairs', 'stairs/treads', 'stairs', 'POV: your boot on tread 1', P(5, x=960, y=700, z=1.1),
  chars=[C('you', [960, 900, 900], 'front', 'neutral', [A(290.1, 'step_down')], mode='feet', pov=True)], tr='glint',
  energy='boot lowering onto the red edge, fast')
STATE(290.0, you='stairs')
X(Wc(113, 'step'), 'SEC', 'stairs', 'stairs/section', 'stairs',
  'THE SECTION [setup]: Cabin 7 upper left in blue night, the white frame, 8 red treads stepping down to the right, the gold cabin '
  'lower right; your small figure going down', P(2), setup='SECTION',
  chars=[body('you', 760, 520, 90, 'profile_right', 'tense', [A(R(0), 'walk', to=840, stairs=True)])],
  device=DEV('diagram', 'section', 'the crossing is a place: blue cabin, stairs, gold cabin'), energy='your small figure stepping down')
X(T(114), 'OTS', 'stairs', 'stairs/ots_climb', 'stairs', 'OTS on the stairs: our blue cabin above, gold below; you go down',
  P(4, x=960, y=600, z=1.05), chars=[body('you', 760, 1200, 900, 'back', 'tense', [A(R(0), 'walk', stairs=True, dir='down')], ots=True)],
  energy='fog bands, the gold rising, push 4 %/s')
X(291.30, 'WS', 'theirs', 'cabin_dawn/master', 'dawn',
  'THEIRS MASTER WIDE from the cabin door: the stairs along the back wall up to the doorway (Tess small in it), Noah\'s bunk at their foot, '
  'the window, curtains frozen at 12 deg; everything mirror-flipped from 72.3 s', P(2.5), tr='glint', setup='THEIRS_MASTER',
  chip='THE OTHER SIDE · 6:59 AM', errfix=[31],
  chars=[body('you', 1500, 520, 230, 'front', 'tense', [A(R(0), 'walk', stairs=True, dir='down')], d=2.0),
         body('noah13', 560, 760, 300, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True),
         body('tess', 1640, 360, 120, 'front', 'fear', [A(R(0), 'flashlight', aim='stairs')], d=4.0)],
  energy='motes twinkling, the knot loop, you descending, push 2.5 %/s')
STATE(291.3, you='theirs')
X(T(115), 'WS', 'theirs', 'cabin_dawn/window', 'dawn', 'the window wall: the old battery lantern glowing on the sill, gingham curtains frozen mid-sway', P(3),
  device=DEV('insert', 'lantern', 'the battery lantern'), energy='lantern glow breathing, push 3.5 %/s')
X(Wc(115, 'glows'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you looking around the gold room in wonder; lantern bokeh', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'wonder', [A(R(0.4), 'look', x=1300, y=460)], light=L_GOLD)], dof=dict(focus=1.0, dof=6.75),
  energy='gold bokeh drifting, your eyes moving')
X(T(116), 'INSERT', 'theirs', 'cabin_dawn/lantern', 'dawn', 'the lantern glowing on the sill; through the glass a peach sky, almost light',
  P(3.5), device=DEV('insert', 'lantern', 'the battery lantern; almost light outside'), energy='glow breathing, sky gradient')
X(T(117), 'WS', 'theirs', 'cabin_dawn/window_out', 'dawn',
  'LOOP A: through the window: the sprinkler comes on, spits twice (298.87, 299.27) (this exact animation returns at 414.6)',
  P(2.5), setup='SPRINKLER', loop='A', energy='the sprinkler arcs (loop A, frame-identical)')
X(Wc(117, 'and'), 'WS', 'theirs', 'cabin_dawn/window', 'dawn', 'window wide from inside: the sprinkler dies outside; its last water beads hang frozen in the air',
  P(3, x=960, y=560, z=1.0), energy='beads hanging, motes twinkling')
X(T(118), 'WS', 'memory', 'memory/open_window', 'sepia_day',
  'memory: water through the open window onto the bottom bunk', P(3), tr='sepia', energy='water arcing in, gate weave')
X(T(119), 'CU', 'memory', 'memory/open_window', 'sepia_day', 'memory CU: kid-you yelps, soaked in the bottom bunk', P(4),
  chars=[bust('you_kid', 960, 560, 1.0, 'front', 'shock', [A(R(0.2), 'flinch')], light=L_MEM)], energy='splash, yelp')
X(Wc(119, 'if'), 'CU', 'memory', 'memory/open_window', 'sepia_day', 'memory CU: Noah, who left the window open, grinning', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'grin_kid', [A(R(0.2), 'smile')], light=L_MEM)], energy='grin, curtains flapping')
X(T(120), 'WS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn',
  'wide on the bunk: Noah at correct seated kid scale, feet on the floor, white sneaker on his left foot, right foot bare, the other shoe '
  'beside the bed', P(3), tr='sepia', setup='NOAH_BUNK', errfix=[21],
  chars=[body('noah13', 960, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)],
  energy='the knot loop, motes, push 3 %/s')
X(Wc(120, 'with'), 'INSERT', 'theirs', 'cabin_dawn/shoe', 'dawn', 'his feet: one white sneaker, one bare foot; label ONE SHOE', P(3.5),
  chars=[feet('noah13', 960, 800, 700, [A(R(0), 'still')], shoe='left')], hud=[label(307.9, 'ONE SHOE', [1100, 760], dx=160, dy=-120)],
  energy='push 3.5 %/s')
X(T(121), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn',
  'CU: Noah looks up and says your name (silently), gap-tooth smile, almond eyes', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'grin_kid', [A(w(121, 'looks'), 'look_up'), A(w(121, 'says'), 'talk_silent', dur=1.0)], light=L_GOLD)],
  dof=dict(focus=1.0, dof=6.75), energy='looking up, talking, push 3 %/s')
X(Wc(121, 'like'), 'OTS', 'theirs', 'cabin_dawn/ots_noah', 'dawn', 'reverse OTS past Noah to you: you stand in the gold room, unsure',
  P(3), chars=[body('noah13', 600, 1200, 760, 'back', 'calm_kid', [], seated=True, ots=True), body('you', 1180, 980, 560, 'q_left', 'wonder', [])],
  energy='gold light on you, push')
X(T(122), 'MCU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'MCU: his eyes travel over your face', P(3),
  chars=[bust('noah13', 960, 580, 0.9, 'q_left', 'puzzled', [A(R(0.3), 'look', x=1100, y=420), A(R(1.0), 'head_tilt')], light=L_GOLD)],
  energy='eyes moving, push 3 %/s')
X(T(123), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah: "Why do you look like Dad?" (gap teeth visible)', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'puzzled', [A(t(123), 'talk', line=123)], light=L_GOLD)], energy='lip-sync')
X(Wc(123, 'dad'), 'DOC', 'memory', 'memory/dad_photo', 'sepia_day', 'a sepia family photo: Dad with your square jaw and stubble',
  P(5), hud=[doc(315.95, 'photo', 'DAD (your jaw, your stubble)')], device=DEV('doc', 'dad_photo', 'you look like Dad'),
  energy='photo push 5 %/s')
X(T(124), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 looks down at his shoe; the half-tied knot in his hands below frame', P(3), tr='sepia',
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(w(124, 'looks'), 'look', x=960, y=900)], light=L_GOLD)], energy='eyes dropping to the shoe')
X(Wc(124, 'shoe'), 'INSERT', 'theirs', 'cabin_dawn/knot', 'dawn', 'knot insert: the lace half tied', P(3.5),
  chars=[hands('noah13', 960, 600, 480, [A(R(0), 'tie_loop', period=2.4)], tape=True)], setup='KNOT', energy='the knot loop')
X(T(125), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'LOOP B: "What are they making for breakfast?" (breakfast_A, replayed frame for frame at 419.7)',
  P(2.5), setup='BREAKFAST_A', loop='B',
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(t(125), 'talk', line=125, clip_id='breakfast_A')], light=L_GOLD)],
  energy='lip-sync (loop B)')
X(T(126), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 holds up a cinnamon candy in a red twist wrapper by his face, not looking up', P(3.5),
  chars=[bust('noah13', 960, 580, 1.0, 'q_left', 'calm_kid', [A(w(126, 'holds'), 'hold_out', prop='candy_red')], light=L_GOLD)], energy='the candy offered')
X(Wc(126, 'without'), 'MS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'MS: Noah holds it out without looking up, eyes on the knot', P(3),
  chars=[body('noah13', 960, 1000, 600, 'q_right', 'calm_kid', [A(R(0), 'hold_out', prop='candy_red')], seated=True)], energy='hand held out')
X(T(127), 'POV', 'theirs', 'cabin_dawn/hands', 'dawn', 'POV: your olive cuff takes the candy; your LEFT hand closes into a fist at 323.65',
  FA(5), chars=[POVH([A(323.5, 'take', prop='candy_red'), A(323.65, 'fist', hand='left', candy=True)], 1040, 620, 520, hand='left'),
               hands('noah13', 860, 560, 380, [], tape=True)],
  props=dict(fist='candy_fist from 323.65'), errfix=[3], energy='the take, the fist closing')
STATE(323.65, fist='candy_fist', candy='fist')
STATE(192.0, your_phone='pocket')
X(T(128), 'INSERT', 'theirs', 'cabin_dawn/hands', 'dawn', 'ECU of your left fist, the red wrapper twist poking out between the fingers',
  P(3), chars=[Fist(960, 620, 560)], device=DEV('insert', 'fist', 'the candy in your fist (it stays there to 649 s)'), errfix=[3],
  energy='knuckles tightening, push 3 %/s')
X(T(129), 'MS', 'memory', 'memory/red_candy', 'sepia_day', 'memory: Noah gives kid-you the red one', P(3), tr='sepia',
  chars=[body('noah13', 860, 1040, 600, 'q_right', 'grin_kid', [A(R(0.2), 'hold_out', prop='candy_red')]), body('you_kid', 1160, 1040, 520, 'q_left', 'happy', [A(R(0.6), 'take')])],
  energy='hand-off, gate weave')
X(Wc(129, 'red'), 'CU', 'memory', 'memory/red_candy', 'sepia_day', 'memory CU: Noah grins and keeps a yellow one', P(4),
  chars=[bust('noah13', 960, 560, 1.0, 'q_right', 'grin_kid', [A(R(0), 'hold_up', prop='candy_yellow')], light=L_MEM)], energy='yellow wrapper glinting')
X(T(130), 'CU', 'memory', 'memory/red_candy', 'sepia_day', 'memory CU: Noah unwraps the yellow one, eyes on your red one',
  P(3), chars=[bust('noah13', 960, 560, 1.0, 'q_right', 'shy', [A(R(0.2), 'look', x=1300, y=600)], light=L_MEM)], energy='unwrapping')
X(T(131), 'WS', 'theirs', 'cabin_dawn/towel_floor', 'dawn', 'floor-level across the towel under the window: drips tap onto it',
  P(2.5, x=960, y=620, z=1.0), tr='sepia', setup='TOWEL_FLOOR', energy='drips falling (332.37, 333.33)')
X(Wc(131, 'under'), 'WS', 'theirs', 'cabin_dawn/window', 'dawn', 'window wide: the wet towel and its little puddle on the floor under the window',
  P(3, x=960, y=600, z=1.0), energy='puddle trembling, motes')
X(T(132), 'INSERT', 'theirs', 'cabin_dawn/towel_floor', 'dawn', 'a drop comes UP off the towel', P(4, x=960, y=560, z=1.35),
  props=dict(drop='rising 335.25-337.09'), energy='a drop rising backward')
X(Wc(132, 'and', n=0), 'INSERT', 'theirs', 'cabin_dawn/towel_floor', 'dawn',
  'the drop hangs in mid-air with the room drawn upside down inside it; hold', ORB(dx=20, r=2, x=960, y=480, z=1.8),
  device=DEV('insert', 'drop', 'a drop hangs in the air (time is stuck)'), energy='slow orbit around the still drop, highlights crawling')
STATE(337.09, drop='hanging')
X(T(133), 'WS', 'theirs', 'cabin_dawn/reverse', 'dawn',
  'REVERSE [setup] from the bunk up the stairs: Tess in the doorway at the top, mid-gesture, her beam steady down the steps',
  P(2.5), setup='THEIRS_REVERSE', chars=[body('tess', 1500, 360, 160, 'front', 'fear', [A(R(0), 'freeze')], d=4.0)],
  energy='the beam perfectly still (wrong), motes twinkling, push')
X(Wc(133, "tess's"), 'MS', 'theirs', 'cabin_dawn/reverse', 'dawn', 'closer on Tess frozen mid-gesture in the doorway', P(3.5, x=1460, y=380, z=1.6),
  chars=[body('tess', 1500, 560, 380, 'front', 'fear', [A(R(0), 'freeze')], d=4.0)], energy='push, nothing moves up there')
X(Wc(133, 'steady'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you looking up the stairs at her: the beam steady, its dust barely moving in the bokeh',
  P(3), chars=[bust('you', 960, 560, 1.0, 'q_right', 'dread', [A(R(0.2), 'look', x=1300, y=300)], light=L_GOLD)], energy='dust crawling 1 px/s behind you')
X(T(134), 'SEC', 'stairs', 'stairs/section', 'stairs',
  'D6 [R section]: two clock dials: OUR SIDE, dust crawling at 1 px/s, chip {ours} | THEIR SIDE, the drop falling again, chip 6:59:4x · LOOP',
  P(1.5), reuse=290.2,
  hud=[dials(343.0, dict(label='OUR SIDE', chip='{ours}', rate='crawling'), dict(label='THEIR SIDE', chip='6:59:4x · LOOP', rate='looping')),
       diagram(342.95, 'D6', 'time split: our side crawls, their side loops', hold=2.1)],
  device=DEV('diagram', 'D6', 'our time crawls, their time loops'), energy='the dials: ours creeping, theirs spinning back')
X(T(135), 'WS', 'theirs', 'cabin_dawn/towel_floor', 'dawn', 'THEIRS, floor-level wide: the same drop falls again onto the towel under the window', P(3, x=960, y=560, z=1.0),
  energy='the drop falling (loop)')
X(347.00, 'INSERT', 'theirs', 'cabin_dawn/towel_floor', 'dawn', 'the splash on the towel (the same sample as 332.37); chip LOOP',
  FA(6, x=960, y=600, z=1.6), hud=[chip(347.02, 'LOOP', 'loop')], energy='splash crown')
X(T(136), 'WS', 'theirs', 'cabin_dawn/reverse', 'dawn', 'Tess small at the top of the stairs, calling down', P(3), reuse=338.76,
  chars=[body('tess', 1500, 360, 160, 'front', 'shout', [A(w(136, 'calls'), 'shout_silent')], d=4.0)], energy='her call, push')
X(T(137), 'CU', 'stairs', 'stairs/bokeh', 'stairs', 'CU of Tess in the doorway at the top, calling down "Forty-five"; GIANT 45 slams over her and flies into the badge',
  P(4), chars=[bust('tess', 960, 560, 1.0, 'front', 'shout', [A(t(137), 'talk', line=137)], light=L_STAIRS)], dof=dict(focus=1.0, dof=6.75),
  hud=[giant(349.79, 45)], voice_fx='far', energy='her call, numeral slam')

# ================================================================ RULE 4 (card 350.38-353.53)
RULE(4)
X(card_times(4)[1], 'WS', 'theirs', 'cabin_dawn/master', 'dawn',
  're-establishing side wide: you take Noah\'s hand and lead him to the foot of the stairs', TR(dx=40, r=1.5), reuse=291.3, tr='smear', setup='LEAD_STAIRS',
  chars=[body('you', 900, 860, 420, 'profile_right', 'resolve', [A(w(140, 'take'), 'take_hand'), A(w(140, 'pull'), 'walk', to=1200)]),
         body('noah13', 700, 860, 330, 'profile_right', 'calm_kid', [A(w(140, 'pull'), 'pulled_along')])],
  energy='walking, track 40 px/s')
X(355.85, 'INSERT', 'theirs', 'cabin_dawn/master', 'dawn', 'their feet at the bottom tread: one sneaker, one bare foot, your boots',
  P(4, x=1200, y=820, z=1.6), chars=[feet('noah13', 1100, 880, 600, [A(R(0), 'step_through')], shoe='left'), feet('you', 1300, 880, 640, [])],
  setup='TREAD_FEET', energy='feet reaching the step')
X(T(141), 'MS', 'theirs', 'cabin_dawn/master', 'dawn', 'MS at the stairs: his hand pulls in yours as he reaches the bottom tread', P(3),
  chars=[body('noah13', 860, 1060, 560, 'profile_right', 'strain', [A(R(0), 'pulled_along')]), body('you', 1160, 1060, 640, 'profile_right', 'resolve', [])],
  energy='strain, push')
X(Wc(141, 'jerks'), 'POV', 'theirs', 'cabin_dawn/hands_jerk', 'dawn', 'POV: his hand snaps out of yours in 2 frames; your empty hand hangs there', FA(8),
  chars=[hands('noah13', 880, 560, 420, [A(358.43, 'hand_jerk', dir='back')], tape=True), hands('you', 1080, 560, 440, [], sleeve='olive')],
  fx_post=[dict(t=358.43, glitch=0.5, dur=0.06)], energy='hands snapping apart; your empty hand closes on nothing')
X(T(142), 'WS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'rewind glitch; wide [R 305.9]: Noah back on the bunk in the identical pose (loop_reset)',
  P(2.5), reuse=305.94, tr='rewind', chars=[body('noah13', 960, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4, phase='loop_reset')], seated=True)],
  energy='rewind tear, the knot loop resumes')
X(Wc(142, 'one'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13: the same blank calm, as if nothing happened', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(R(0), 'tie_loop')], light=L_GOLD)], energy='stillness')
X(T(143), 'INSERT', 'theirs', 'cabin_dawn/knot', 'dawn', 'the knot, half tied; label SAME KNOT', P(3.5), reuse=316.58,
  chars=[hands('noah13', 960, 600, 480, [A(R(0), 'tie_loop', period=2.4)], tape=True)], hud=[label(362.8, 'SAME KNOT', [960, 600], dx=180, dy=-120)],
  device=DEV('insert', 'same_knot', 'the same knot, half tied: SAME KNOT'), energy='the knot loop')
X(T(144), 'WS', 'theirs', 'cabin_dawn/master', 'dawn', 'the same framing as 353.5, shorter: you pull again', TR(dx=40, r=1.5), reuse=353.53,
  chars=[body('you', 900, 860, 420, 'profile_right', 'resolve', [A(w(144, 'pull'), 'walk', to=1200)]),
         body('noah13', 700, 860, 330, 'profile_right', 'calm_kid', [A(w(144, 'pull'), 'pulled_along')])], energy='pulling')
X(T(145), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU at the stairs: you watch his face', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'tense', [A(R(0.4), 'stare')], light=L_GOLD)], energy='watching')
X(T(146), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 straining at the bottom tread', P(4),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'strain', [A(R(0), 'expr', name='strain')], light=L_GOLD)], energy='straining')
X(Wc(146, 'looks'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'the face flickers to grown Noah (0.5 s), brown eyes', FA(8), tr='white',
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'shaken', [A(R(0), 'face_flash')], light=L_GOLD)], energy='flicker, hit')
X(368.34, 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you: shock', P(4),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'shock', [], light=L_GOLD)], energy='shock')
X(T(147), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13: thirteen again, puzzled', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'puzzled', [A(R(0.3), 'blink')], light=L_GOLD)], energy='a blink')
X(T(148), 'WS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn',
  'wide 2-shot: you sit at the foot end of the bunk; THE DIP by Noah\'s left hip stays empty', P(2.5), reuse=305.94,
  chars=[body('you', 1260, 900, 440, 'q_left', 'grief', [A(w(148, 'sitting'), 'sit')], seated=True),
         body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)],
  energy='the bunk creaking, push')
X(Wc(148, 'you'), 'OTS', 'theirs', 'cabin_dawn/ots_noah', 'dawn', 'OTS over you on Noah: you ask what he said to the woman', P(3),
  chars=[body('you', 600, 1200, 760, 'back', 'grief', [], seated=True, ots=True), body('noah13', 1200, 1000, 560, 'q_left', 'calm_kid', [A(R(0.6), 'look_up')], seated=True)],
  energy='push')
X(T(149), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah: "That I wanted to stay until the breakfast bell" (lip-sync)', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(t(149), 'talk', line=149)], light=L_GOLD)], energy='lip-sync, push')
X(Wc(149, 'the', n=0), 'INSERT', 'memory', 'memory/watch_cu', 'sepia_night',
  'FLASHBACK chip 14 YEARS AGO · 4:45 AM: the watch alarm flashing 4:45 (your prank woke him)', FA(5), tr='sepia',
  chip='14 YEARS AGO · 4:45 AM',
  hud=[diagram(376.3, 'watch', 'ALM 4:45 flashing', hold=0.8)], energy='LCD flashing, beeping')
X(376.80, 'WS', 'memory', 'memory/flash_445', 'sepia_night',
  'THE KEY MEMORY: Noah13 alone at this mirror at 4:45 AM in pajamas, lipstick in hand, the steps drawn; a pale hand rests on the '
  'INSIDE of the glass', P(3), device=DEV('insert', 'wish', 'Noah made the wish at 4:45 AM (his alarm woke him)'),
  chars=[body('noah13', 860, 980, 560, 'q_right', 'calm_kid', [A(R(0.2), 'draw_step', step=7)], pajamas=True)],
  energy='lantern flicker, the pale hand pressing from inside')
X(Wc(151, 'run'), 'WS', 'memory', 'memory/bus_run', 'sepia_morning',
  'memory (his plan): Noah in pajamas sprinting toward a yellow bus, laughing', TR(dx=80, r=1.0),
  chars=[body('noah13', 900, 960, 420, 'profile_right', 'laugh', [A(R(0), 'run', to=1300)], pajamas=True)], energy='running, track 80 px/s')
X(T(152), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 grinning: "I thought it\'d be funny"', P(3), tr='sepia',
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'grin_kid', [A(t(152), 'talk', line=152)], light=L_GOLD)], energy='lip-sync, grin')
X(T(153), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'wide [R 305.9]: SHE IS SITTING ON THE BUNK BESIDE NOAH, S2, perfectly still, head tilted to him; the gold drains around her',
  P(2.5), reuse=305.94, setup='QUEEN_BUNK',
  chars=[Q('S2', [1160, 900, 520, 1.0], mode='body', acts=[A(R(0), 'head_tilt', deg=12), A(R(0), 'drift')], seated=True),
         body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)],
  q=dict(stage='S2', size=0.30, where='on the bunk beside Noah', framing='WS 30 %', wrong='she was here all along'),
  energy='the knot loop; her drift only; colour draining near her')
STATE(382.16, queen='bunk')
X(T(154), 'MS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'MS: Noah glances at the window (the bus); her red-fingertip hand rests near his', P(3),
  chars=[body('noah13', 860, 1060, 620, 'q_right', 'worried', [A(R(0.2), 'look', x=1600, y=380)], seated=True),
         Q('S2', [1240, 760, 420], mode='hands', acts=[A(R(0), 'still')])], energy='glance, push')
X(T(155), 'INSERT', 'theirs', 'cabin_dawn/clock', 'dawn', 'D7 the clock: 6:59:5x climbing to :59', P(4, x=960, y=500, z=1.2), reuse=17.58,
  hud=[diagram(386.7, 'D7', 'the clock climbs 6:59:5x -> :59', hold=1.6)], device=DEV('diagram', 'D7', 'the loop clock'),
  energy='second hand sweeping')
X(Wc(155, 'go'), 'WS', 'theirs', 'cabin_dawn/master', 'dawn', 'the room flickers with the rewind glitch: the wall clock snaps back to :40; chip LOOP with a circular arrow',
  P(3), tr='rewind', hud=[chip(388.6, 'LOOP', 'loop')], energy='rewind tear, the knot loop resumes')
X(Wc(156, 'still'), '2S', 'theirs', 'cabin_dawn/queen_3s', 'dawn_queen',
  '2-shot: Noah asks; across the room in the window corner she answers with soft lips (S2, soft focus): "there\'s still a little while"',
  P(3), setup='QUEEN_CORNER',
  chars=[body('noah13', 760, 1000, 560, 'q_right', 'worried', [A(R(0), 'talk_silent', dur=0.8)], seated=True),
         Q('S2', [1600, 760, 380, 3.0], mode='body', acts=[A(R(0.3), 'talk_silent', dur=1.0)], soft_focus=True)],
  q=dict(stage='S2', size=0.20, where='the window corner, background', framing='soft focus 20 %', wrong='she watches'),
  energy='her soft lips, Noah nodding')
STATE(389.84, queen='window_corner')
X(T(157), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you: how long has he known her?', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'tense', [A(R(0), 'talk_silent', dur=1.2)], light=L_GOLD)], energy='asking')
X(Wc(157, 'known'), 'MCU', 'theirs', 'cabin_dawn/ots_noah', 'dawn',
  'Noah thinking; behind him in the window corner the queen, soft, standing', P(2.5),
  chars=[bust('noah13', 900, 580, 0.9, 'q_left', 'puzzled', [A(R(0.4), 'head_tilt')], light=L_GOLD),
         Q('S2', [1560, 760, 320, 3.0], mode='body', acts=[A(R(0), 'drift')], soft_focus=True)],
  q=dict(stage='S2', size=0.18, where='the window corner, background', framing='soft focus', wrong=''), energy='thinking')
X(T(158), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah, innocent: "Since you went to get Mom"', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(t(158), 'talk', line=158)], light=L_GOLD)], energy='lip-sync')
X(T(159), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah tilts his head, waiting for you', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(R(0), 'head_tilt')], light=L_GOLD)], energy='waiting')
X(T(160), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you stunned; silence', SIL(1.5),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'shock', [A(R(0), 'freeze')], light=L_GOLD)], energy='slow push in the silence')
X(T(161), 'CU', 'memory', 'memory/wake', 'sepia_morning', 'memory-morning CU: kid-you wakes in the bottom bunk and squints', P(3), tr='sepia',
  chars=[bust('you_kid', 960, 600, 1.0, 'front', 'sleep', [A(R(0.2), 'wake_up')], light=L_MEM, lying=True)], energy='waking')
X(400.34, 'WS', 'memory', 'memory/wake', 'sepia_morning', 'the bunk above: empty, the blanket thrown back', P(3),
  energy='morning light, a curtain moving')
X(T(162), 'WS', 'memory', 'memory/towel_wet', 'sepia_morning', 'memory wide: the cabin floor between the bunks: the same striped towel lying wet', P(3),
  device=DEV('insert', 'towel_wet', 'the wet towel on the floor that morning'), energy='water sheen, push')
X(T(163), 'WS', 'memory', 'memory/search_window', 'sepia_morning',
  'through the window: counselors with flashlights in the mist; a balloon NOAH!', P(3),
  hud=[dict(t=404.0, type='balloon', text='NOAH!', x=1100, y=320)], energy='flashlights sweeping, mist')
X(Wc(163, 'yelling'), 'WS', 'memory', 'memory/search_pines', 'sepia_morning', 'flashlights in the pines, mist', DR(2, dx=30),
  energy='beams crossing, drift')
X(T(164), 'WS', 'memory', 'memory/legs', 'sepia_morning', 'kid-you among adult legs on the porch', P(2.5),
  chars=[body('you_kid', 960, 980, 420, 'front', 'sure', [A(R(0.4), 'talk_silent', dur=1.0)]), C('extras', [960, 1000, 900], 'front', 'neutral', [A(R(0), 'shift_weight')], mode='legs')],
  energy='legs shifting')
X(408.20, 'MS', 'memory', 'memory/officer', 'sepia_morning', 'an officer with a notebook bends to listen', P(3),
  chars=[body('extras', 960, 1060, 660, 'q_left', 'neutral', [A(R(0), 'write')], role='officer')], energy='writing')
X(T(165), 'WS', 'memory', 'memory/legs', 'sepia_morning', 'kid-you pointing at the mess hall: back for breakfast', P(2.5),
  chars=[body('you_kid', 900, 980, 440, 'profile_right', 'sure', [A(R(0.3), 'point', x=1600, y=500)])], energy='pointing')
X(T(166), 'CU', 'memory', 'memory/breakfast_table', 'sepia_day', 'memory CU: Noah at the breakfast table stuffing pancakes', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'front', 'grin_kid', [A(R(0), 'eat')], light=L_MEM)], energy='eating')
X(Wc(166, 'when'), 'WS', 'memory', 'memory/breakfast_table', 'sepia_day',
  'kid-you laughing across the table; the breakfast bell on its hook behind them', P(2.5),
  chars=[body('you_kid', 700, 1000, 460, 'q_right', 'laugh', [A(R(0), 'laugh')]), body('noah13', 1200, 1000, 500, 'q_left', 'grin_kid', [A(R(0), 'eat')])],
  energy='laughing, steam from the pancakes')
X(T(167), 'WS', 'theirs', 'cabin_dawn/window_out', 'dawn',
  'LOOP A again [R 297.4]: THEIRS window, the identical sprinkler animation; chip AGAIN with a circular arrow', P(2.5), reuse=297.42,
  tr='rewind', loop='A', hud=[chip(414.4, '↺ AGAIN', 'loop')], energy='sprinkler arcs, frame-identical')
X(T(168), 'MS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'MS: Noah reaches for his loose shoelace', P(3), reuse=305.94,
  chars=[body('noah13', 960, 1040, 600, 'q_right', 'calm_kid', [A(w(168, 'reaches'), 'reach', prop='lace')], seated=True)], energy='the reach')
X(418.88, 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 tying, blank, the same as before', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(R(0), 'tie_loop')], light=L_GOLD)], energy='the knot loop')
X(T(169), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'LOOP B [R 318.4]: breakfast_A, frame-identical', P(2.5), reuse=318.42, loop='B',
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(t(169), 'talk', line=169, clip_id='breakfast_A')], light=L_GOLD)],
  energy='lip-sync (loop B replay)')
X(T(170), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you hearing it again', P(4),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'dread', [], light=L_GOLD)], energy='dread')
X(Wc(171, 'asked'), 'SPLIT', 'theirs', 'split/twins', 'dawn',
  'split: the two identical CUs side by side, both chipped 6:59:45 AM', P(2),
  split=dict(panels=[dict(set='cabin_dawn', view='bokeh', var='dawn', world='theirs', chip='6:59:45 AM', src_t=318.42),
                     dict(set='cabin_dawn', view='bokeh', var='dawn', world='theirs', chip='6:59:45 AM', src_t=419.52)]),
  hud=[diagram(422.4, 'loop_split', 'the same question, frame for frame: 6:59:45 AM | 6:59:45 AM', hold=2.3)],
  device=DEV('diagram', 'loop_split', 'the same moment twice'), energy='both mouths moving in perfect sync')
X(T(172), 'INSERT', 'theirs', 'cabin_dawn/knot', 'dawn', 'ECU of the knot; type beat 14 YEARS echoes the hook stamp', P(2), reuse=316.58,
  hud=[stamp(426.1, '14 YEARS', 960, 520, '#c0392b', -4, 0.14), typebeat(426.1, 2, '14 YEARS', echo=True)], energy='slow pull begins')
X(T(173), 'MS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'pull-out: Noah tying the knot', PU(3),
  chars=[body('noah13', 960, 1000, 580, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)], energy='pull-out 3 %/s')
X(Wc(173, 'half'), 'WS', 'theirs', 'cabin_dawn/master', 'dawn',
  'pull-out to the wide: Noah small in the frozen gold; she stands in the far window corner, soft focus', PU(3), reuse=291.3,
  chars=[body('noah13', 560, 760, 300, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True),
         Q('S2', [1560, 700, 300, 3.0], mode='body', acts=[A(R(0), 'drift')], soft_focus=True)],
  q=dict(stage='S2', size=0.15, where='the window corner, background', framing='soft focus 15 %', wrong='threat in the background'),
  energy='pull-out, the knot loop')
X(T(174), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you: you know why he never heard it', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0.6), 'swallow')], light=L_GOLD)], energy='a swallow')
X(T(175), 'MS', 'memory', 'memory/director', 'sepia_morning', 'memory: the director with a clipboard on the mess-hall porch', P(3), tr='sepia',
  chars=[body('extras', 960, 1060, 640, 'q_left', 'shout', [A(R(0), 'call_out')], role='director')], energy='calling out')
X(T(176), 'WS', 'memory', 'memory/kitchen_staff', 'sepia_morning', 'the director waves cooks in white aprons out of the kitchen', P(2.5),
  chars=[C('extras', [960, 980, 520], 'front', 'neutral', [A(R(0), 'walk')], mode='body', role='cooks')], energy='cooks filing out')
X(Wc(176, 'out'), 'WS', 'memory', 'memory/search_pines', 'sepia_morning', 'the cooks with flashlights into the pines', DR(2, dx=30),
  chars=[C('extras', [960, 900, 360], 'back', 'neutral', [A(R(0), 'walk')], mode='body', role='cooks')], energy='walking off, mist')
X(T(177), 'DOC', 'memory', 'memory/menu_board', 'sepia_morning',
  'the menu chalkboard JULY 19 · BREAKFAST 7:00 · PANCAKES with CANCELED chalked across and a red stamp', P(3),
  hud=[doc(438.0, 'menu', 'JULY 19 · BREAKFAST 7:00 · PANCAKES', marks=[dict(t=438.7, what='chalk', text='CANCELED'), dict(t=438.95, what='stamp', text='CANCELED')]),
       stamp(438.95, 'CANCELED', 980, 560, '#b8342c', -6, 0.14)], errfix=[30],
  device=DEV('doc', 'menu', 'Breakfast was canceled'), energy='chalk scraping, the stamp slam')
X(T(178), 'WS', 'memory', 'memory/buses', 'sepia_day', 'yellow buses in a line; kids\' faces in the windows; chip 12:00 PM', P(2.5),
  hud=[chip(439.5, '12:00 PM', 'memory')], energy='buses idling, hands at windows')
X(Wc(178, 'everyone'), 'CU', 'memory', 'memory/bus_window', 'sepia_day', 'kid-you\'s face in a bus window looking back at the cabins', P(3),
  chars=[bust('you_kid', 960, 560, 1.0, 'q_right', 'sad', [], light=L_MEM)], energy='the bus pulling away, reflections sliding')
X(T(179), 'WS', 'memory', 'memory/gate_close', 'sepia_day', 'the gate chained [R the gate, sepia]', P(2.5), reuse=22.46,
  energy='the chain pulled through, the padlock snapping')
X(Wc(179, 'camp'), 'DOC', 'memory', 'memory/gate_close', 'sepia_day', 'a sign CAMP CLOSED hung on the gate', P(3),
  hud=[doc(443.6, 'sign', 'CAMP CLOSED')], energy='the sign swinging')
X(T(180), 'WS', 'memory', 'memory/crate_bell', 'sepia_day',
  'memory wide on the porch: the counselor lowers the bell into the SAVE FOR THE MUSEUM crate and shuts the lid (callback to 56.1)', P(3), reuse=57.18,
  chars=[body('counselor', 960, 960, 480, 'q_left', 'neutral', [A(R(0.2), 'set_down', prop='bell')])],
  device=DEV('insert', 'crate_bell', 'the bell went into the crate'), energy='lowering, lid thump')

# ================================================================ RULE 5 (card 446.33-449.74)
RULE(5)
X(card_times(5)[1], 'WS', 'theirs', 'cabin_dawn/reverse', 'dawn',
  're-establishing wide [R reverse], low angle up the stairs: you shout up to Tess in the doorway; D10 map inset top left',
  HH(2, shake=15), reuse=338.76, tr='smear',
  chars=[body('you', 760, 1060, 560, 'back', 'shout', [A(R(0), 'shout_silent')]), body('tess', 1500, 400, 170, 'front', 'fear', [], d=4.0)],
  hud=[mapins(449.80, 2.0, [['CABIN 7', 60, 180], ['PATH', 180, 140], ['MESS HALL · CRATE', 300, 80]], dot=[[449.8, 60, 180]])],
  device=DEV('diagram', 'D10', 'the map: Cabin 7 -> the path -> the mess hall crate'), energy='handheld, shouting')
X(T(184), 'MS', 'theirs', 'cabin_dawn/reverse', 'dawn', 'Tess in the doorway at the top, hearing you; the map inset finishes',
  HH(2.5, shake=15, x=1480, y=420, z=1.5),
  chars=[body('tess', 1500, 600, 420, 'front', 'fear', [A(R(0.3), 'nod')], d=4.0)], energy='handheld')
X(T(185), 'WS', 'ours', 'cabin_now/reverse', 'doorway_glow', 'OURS, reverse wide from the mirror spot: Tess at the gold doorway turns toward Cabin 7\'s open front door', HH(2, shake=15), tr='glint',
  chars=[body('tess', 760, 1000, 520, 'q_left', 'fear', [A(w(185, 'looks'), 'turn', to='door')])], energy='the turn, handheld')
X(Wc(185, 'open'), 'POV', 'ours', 'cabin_now/reverse', 'doorway_glow', 'POV Tess: the open cabin door; the path and the porch beyond',
  HH(2, shake=15), energy='handheld, the beam on the doorway')
X(T(186), 'WS', 'ours', 'mess_porch/high_wide', 'night', 'the HIGH WIDE [R 54.6]: the porch across the path from Cabin 7\'s door', P(2.5), reuse=54.46,
  energy='mist on the path, push')
X(T(187), 'WS', 'memory', 'memory/run_barefoot', 'sepia_day', 'memory: kid-you and kid-Tess running barefoot across the path', TR(dx=80, r=1.0), tr='sepia',
  chars=[body('you_kid', 900, 960, 420, 'profile_right', 'laugh', [A(R(0), 'run', to=1300)]), body('kids', 700, 960, 400, 'profile_right', 'laugh', [A(R(0), 'run', to=1100)], role='tess_kid')],
  energy='running, track 80 px/s')
X(T(188), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you shouting "Go!"', HH(3, shake=18), tr='sepia',
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'shout', [A(t(188), 'talk', line=188)], light=L_GOLD)], energy='the shout')
X(T(189), 'WS', 'ours', 'cabin_now/master', 'doorway_glow', 'OURS: Tess spins and runs for the cabin door, beam swinging', HH(3, shake=20), tr='glint',
  chars=[body('tess', 960, 900, 420, 'q_left', 'fear', [A(R(0), 'run', to=520)])], energy='run cycle, beam swinging')
X(462.59, 'INSERT', 'ours', 'cabin_now/door', 'night', 'insert: her hand yanks the padlock off the hasp', FA(8),
  chars=[hands('tess', 960, 560, 420, [A(462.9, 'yank', prop='padlock')], sleeve='orange')], errfix=[32], energy='the yank')
STATE(462.9, padlock='tess_hand', flashlight='tess_running', tess='porch', towel='tess_shoulder')
X(463.03, 'WS', 'ours', 'camp_path/path_run', 'night', 'Tess runs out the door with the beam into the night; Cabin 7 goes dark blue behind her',
  HH(2.5, shake=22), chars=[body('tess', 960, 900, 360, 'back', 'fear', [A(R(0), 'run', to=1300)])], energy='run cycle, beam receding')
X(463.89, 'WS', 'theirs', 'cabin_dawn/reverse', 'dawn',
  'THEIRS: the doorway at the top goes DARK NAVY, no beam; the empty corner by the window', SIL(1.5), reuse=338.76, tr='glint', errfix=[10],
  props=dict(doorway='navy_dark at 463.89'), energy='silence push, the empty window corner')
STATE(463.89, doorway='navy_dark')
X(T(191), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'HOLD H2: she rises from the window corner (where she has stood since 389 s) and in one smooth 1.2 s glide, with no bob, bends at '
  'the hip and sits beside Noah; the mattress dips; her hair stays put', P(3), hold='H2', reuse=382.16,
  chars=[Q('S2', [1600, 760, 380, 2.0], mode='body', acts=[A(465.0, 'rise'), A(466.10, 'sit_beside', dur=1.2, to=[1160, 900, 520], bob=0)]),
         body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True)],
  q=dict(stage='S2', size=0.35, where='rises from the corner, sits on the bunk', framing='WS 35 %', wrong='the inhuman sit'),
  errfix=[1], energy='the glide, the mattress dipping, the knot loop')
STATE(467.3, queen='bunk')
X(T(192), 'MS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'MS: Noah scoots 40 px over without his eyes leaving the knot', P(3),
  chars=[body('noah13', 860, 1060, 600, 'q_right', 'calm_kid', [A(w(192, 'scoots'), 'scoot', dx=-40)], seated=True),
         Q('S2', [1300, 1060, 640], mode='body', acts=[A(R(0), 'still')], seated=True)], errfix=[1], energy='the scoot')
X(Wc(192, 'without'), 'WS', 'theirs_break', 'cabin_dawn/dip_low', 'dawn_queen', 'low wide along the mattress: her black satin settles into the dip beside Noah\'s knees',
  P(3), energy='satin settling, the mattress sagging')
X(T(193), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah, blank, eyes on the knot: he\'s done it before', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'listening', [], light=L_GOLD)], energy='stillness, push')
X(T(194), 'CU', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen', 'CU of her, S2, the drawn smile; her lips move: another minute?', P(3.5),
  chars=[Q('S2', [960, 560, 1.1], acts=[A(R(0.1), 'talk_silent', dur=1.6, glow=True)])],
  q=dict(stage='S2', size=0.50, where='on the bunk', framing='CU 50 %', wrong=''), energy='lips moving, the drawing still')
X(T(195), 'INSERT', 'theirs_break', 'cabin_dawn/dip_low', 'dawn_queen', 'insert: the red-fingertip hand pats the dip twice', P(3.5),
  chars=[Q('S2', [960, 640, 520], mode='hands', acts=[A(476.04, 'pat'), A(476.36, 'pat')])], energy='two pats')
X(478.03, 'CU', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'HOLD H3: CU push 5 %/s; on "back" (479.24) the drawn stair-smile SPLITS OPEN along the drawing into a grin of flat human teeth '
  'climbing her cheeks; the lips keep talking ("I can put you back the way he remembers you")', P(5), hold='H3',
  chars=[Q('S3a', [960, 560, 1.15], acts=[A(t(196), 'talk_line', line=196, glow=True), A(479.24, 'split_open', dur=0.25)])],
  q=dict(stage='S3a', size=0.70, where='on the bunk', framing='CU 70 %', wrong='the drawing opens into teeth'),
  errfix=[20], energy='the split on the word, lips talking, push 5 %/s')
X(481.13, 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you, tempted, eyes lowered; colour drains', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'tempted', [A(R(0.5), 'look', x=900, y=760)], light=L_GOLD)], energy='eyes lowering')
X(T(199), 'WS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'wide from the bunk end: the little dip in the mattress between you and Noah; she sits on his other side',
  P(3), chars=[body('noah13', 860, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop')], seated=True),
               Q('S3a', [600, 900, 500, 1.0], mode='body', acts=[A(R(0), 'still')], seated=True), body('you', 1460, 920, 470, 'q_left', 'tempted', [])],
  q=dict(stage='S3a', size=0.30, where='on the bunk', framing='WS', wrong=''), energy='the knot loop, push')
X(Wc(200, 'where', off=-0.06), 'MS', 'memory', 'memory/socks', 'sepia_morning', 'memory: kid-you on that spot pulling socks on', P(3), tr='sepia',
  chars=[body('you_kid', 960, 1040, 560, 'front', 'happy', [A(R(0), 'pull_socks')], seated=True)], energy='pulling socks')
X(T(201), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'WIDE: Noah tying the knot, the Queen beside him patting the dip, the beautiful gold room; you at the bunk\'s end, half-turned to the dip; slow push',
  P(2), reuse=382.16, tr='sepia', errfix=[2],
  chars=[body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], seated=True),
         Q('S3a', [1080, 900, 500, 1.0], mode='body', acts=[A(R(0.3), 'pat')], seated=True),
         body('you', 1500, 920, 480, 'q_left', 'tempted', [A(R(0), 'look', x=1000, y=760)])],
  q=dict(stage='S3a', size=0.30, where='on the bunk', framing='WS', wrong='the grin of teeth, patting the dip'), energy='the knot loop, the pat, slow push')
X(T(202), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you half-turned toward the dip, gold on your face; you understand', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'tempted', [A(R(0.4), 'lean_in', amount=0.2)], light=L_GOLD)], energy='leaning')
X(Wc(202, 'ask'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 tying, content', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'calm_kid', [A(R(0), 'tie_loop')], light=L_GOLD)], energy='content')
X(T(203), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'you begin to lower toward the dip; RED X (3 of 4) over the dip at 493.56; tag DON\'T SIT DOWN', P(3), reuse=382.16,
  chars=[body('you', 1300, 940, 520, 'q_left', 'tempted', [A(R(0), 'sit', partial=0.4)]),
         body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(R(0), 'tie_loop')], seated=True),
         Q('S3a', [1040, 900, 500, 1.0], mode='body', acts=[A(R(0), 'still')], seated=True)],
  hud=[redx(493.56, 1180, 840, 140, 0.8, n=3), tag(493.62, "DON'T SIT DOWN", 960, 150, 'lipstick', 1.0)], energy='lowering, the X')
X(Wc(203, 'and'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU you: your lips forming "leave it open"', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [A(R(0), 'talk_silent', dur=0.8)], light=L_GOLD)], energy='lips moving')
X(Wc(203, 'window'), 'MS', 'memory', 'memory/night_window', 'sepia_night', 'memory flash: Noah at the open window smiling back', FA(5), tr='sepia',
  chars=[body('noah13', 960, 1040, 620, 'q_left', 'grin_kid', [A(R(0), 'smile')])], energy='flash')
X(T(204), 'OTS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen', 'OTS over your shoulder: her face behind you', P(3), tr='sepia',
  chars=[bust('you', 640, 640, 1.3, 'back', 'tempted', [], light=L_GOLD), Q('S3a', [1220, 480, 0.8], acts=[A(R(0), 'drift')])],
  q=dict(stage='S3a', size=0.40, where='over your shoulder', framing='OTS 40 %', wrong=''), energy='her drift closer 2 px/s')
X(Wc(204, 'said'), 'OTS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen', 'closer: her irises turn RED on "better" (S3b)',
  P(4, x=1220, y=480, z=1.25), chars=[bust('you', 640, 640, 1.3, 'back', 'tempted', [], light=L_GOLD),
                                      Q('S3b', [1220, 480, 0.9], acts=[A(499.56, 'eyes_red', dur=0.3)])],
  q=dict(stage='S3b', size=0.40, where='over your shoulder', framing='OTS 40 %', wrong='red irises'), energy='the eyes turning')
X(T(205), 'WS', 'ours', 'mess_porch/porch_crate', 'night', 'OURS porch: Tess at the crate, beam swinging, the padlock in her hand', HH(2.5, shake=20), tr='glint',
  chars=[body('tess', 960, 900, 420, 'profile_left', 'angry', [A(R(0), 'shout_silent')])], energy='handheld, beam swinging')
STATE(500.03, tess='porch', flashlight='tess_porch')
X(Wc(205, 'yells'), 'CU', 'ours', 'mess_porch/bokeh', 'night', 'CU Tess yelling "Twenty!" across the camp; GIANT 20 slams over her and flies into the badge',
  HH(3, shake=18), chars=[bust('tess', 960, 560, 1.0, 'q_left', 'shout', [A(t(206), 'talk', line=206)], light=L_BEAM)],
  hud=[giant(502.36, 20)], energy='the yell, numeral slam')
X(T(207), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen', 'wide on the bunk: Noah holds out another cinnamon candy; the Queen beside him, red eyes on you; you at the bunk end', P(3), tr='glint',
  chars=[body('noah13', 860, 900, 420, 'q_right', 'calm_kid', [A(w(207, 'holds'), 'hold_out', prop='candy_red')], seated=True),
         Q('S3b', [1120, 900, 500, 1.0], mode='body', acts=[A(R(0), 'still')], seated=True), body('you', 1500, 920, 470, 'q_left', 'tempted', [], fist='left')],
  q=dict(stage='S3b', size=0.30, where='on the bunk', framing='WS', wrong=''), energy='offering, her stillness')
X(Wc(207, 'another'), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU Noah13 holding up the second candy by his face, eyes on the knot', P(3.5),
  chars=[bust('noah13', 960, 580, 1.0, 'q_left', 'calm_kid', [A(R(0), 'hold_out', prop='candy_red')], light=L_GOLD)], energy='push')
X(T(208), 'POV', 'theirs', 'cabin_dawn/hands', 'dawn', 'POV: your left fist, white knuckles, the wrapper twist between the fingers', P(3.5),
  chars=[Fist(960, 640, 580, [A(R(0.3), 'tremble', amount=0.3)])], errfix=[3], energy='knuckles whitening')
X(T(209), 'WS', 'ours', 'mess_porch/porch_crate', 'night', 'porch: Tess kicks the crate', HH(3, shake=24), tr='glint',
  chars=[body('tess', 960, 900, 420, 'profile_left', 'angry', [A(509.24, 'kick')])], energy='the kick')
X(Wc(209, 'kicking'), 'WS', 'ours', 'mess_porch/boot', 'night',
  'low wide on the porch boards: her boot smashes the slats (509.72, 510.12), splinters at the lens; the crate splits and the bell rolls out; the padlock in her other hand',
  HH(4, shake=26), chars=[body('tess', 960, 980, 520, 'profile_left', 'angry', [A(509.72, 'kick'), A(510.12, 'kick')])], props=dict(bell='on_boards at 510.4'),
  energy='slats flying, the bell rolling')
STATE(510.4, bell='porch_boards')
X(T(210), 'WS', 'theirs', 'cabin_dawn/window_out', 'dawn', 'THEIRS through the window: across the frozen lawn, the far mess-hall porch', P(3), tr='glint',
  energy='the frozen lawn, push')
X(Wc(210, 'bell'), 'INSERT', 'theirs', 'cabin_dawn/far_porch', 'dawn',
  'telephoto: a GLEAMING bell swinging by itself on the far porch, clean white rings', P(4), tr='white', errfix=[8],
  hud=[rings(513.6, 'clean', 960, 480, 4, 1.0)], device=DEV('insert', 'fake_bell', 'a perfect bell rings by itself (the fake)'),
  energy='the bell swinging, perfect rings')
X(T(211), 'MS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', 'MS: Noah leans down and reaches for his other shoe beside the bed', P(3),
  chars=[body('noah13', 960, 1040, 600, 'q_right', 'calm_kid', [A(w(211, 'reaches'), 'reach', prop='shoe')], seated=True)], energy='reaching')
X(T(212), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you, mouth opening to say hurry', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'tense', [A(R(0.3), 'mouth_open_close')], light=L_GOLD)], energy='mouth opening')
X(T(213), 'CU', 'theirs', 'cabin_dawn/bokeh', 'dawn', 'CU of you: you remember the crack; the sepia cracked rim [R 62.9] ghosts over your face', P(3), reuse=62.87,
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'tense', [A(R(0.3), 'expr', name='resolve')], light=L_GOLD)], energy='a realisation, push')
X(519.90, 'WS', 'memory', 'memory/bell_ring_porch', 'sepia_day', 'memory: the counselor rings it on the porch', P(3),
  chars=[body('counselor', 960, 960, 520, 'front', 'neutral', [A(R(0.3), 'ring_bell')])], energy='ringing')
X(T(214), 'MS', 'memory', 'memory/bell_ring_porch', 'sepia_day', 'it always rang twice: kids at the table flinch at the rattle', P(3),
  chars=[C('kids', [960, 1000, 520], 'front', 'giggle', [A(522.6, 'flinch')], mode='body')], energy='flinch')
X(T(215), 'DIAGRAM', 'memory', 'memory/bell_ecu', 'sepia_day', 'D8: a clean ring', P(3), reuse=66.15,
  hud=[rings(523.75, 'clean', 960, 520, 3, 1.0), diagram(523.6, 'D8', 'a clean note first', hold=1.2)],
  device=DEV('diagram', 'D8', 'the real bell: a clean note, then a rattle'), energy='a ring expanding')
X(T(216), 'CU', 'memory', 'memory/bell_ring_porch', 'sepia_day', 'memory CU: kid-you wincing at the thin rattle; D8 the jagged rattle squiggle drawn beside your ear',
  P(3), chars=[bust('you_kid', 960, 560, 1.0, 'q_right', 'shock', [A(R(0.2), 'flinch')], light=L_MEM)],
  hud=[rings(525.0, 'rattle', 1300, 480, 3, 1.4)], energy='the squiggle shaking, a wince')
X(Wc(216, 'that'), 'CU', 'memory', 'memory/breakfast_table', 'sepia_day', 'memory CU: Noah at the breakfast table dangles a spoon over his plate, grinning', P(3.5),
  chars=[bust('noah13', 960, 560, 1.0, 'front', 'grin_kid', [A(R(0.1), 'hold_up', prop='spoon')], light=L_MEM)], energy='the spoon swinging')
X(Wc(216, 'dropped'), 'INSERT', 'memory', 'memory/spoon', 'sepia_day', 'insert: the spoon drops on the table and bounces (the simile gets a shot)', P(3.5),
  device=DEV('insert', 'spoon', 'like somebody dropped a spoon'), energy='the spoon falling and bouncing at 527.9')
X(T(217), 'INSERT', 'theirs', 'cabin_dawn/clock', 'dawn', 'the THEIRS clock at :59 snaps back to :40 at 529.5: the fake bell did not count',
  P(4), reuse=17.58, tr='sepia', fx_post=[dict(t=529.5, glitch=0.8, rewind=1.0, dur=0.2)], hud=[chip(529.5, 'LOOP', 'loop')],
  energy='second hand, rewind')
X(Wc(217, 'was'), 'SPLIT', 'theirs', 'split/bells', 'dawn',
  'split: THEIR BELL (smooth rings, red X mark) | OUR BELL (rings plus rattle, green tick)', P(2),
  split=dict(panels=[dict(set='cabin_dawn', view='far_porch', var='dawn', world='theirs', label='THEIR BELL', mark='red_x'),
                     dict(set='mess_porch', view='bell_ecu', var='night', world='ours', label='OUR BELL', mark='green_tick')]),
  hud=[rings(530.6, 'clean', 480, 520, 3, 1.0), rings(530.6, 'rattle', 1440, 520, 3, 1.0),
       diagram(530.5, 'D8', 'THEIR BELL: perfect (X) | OUR BELL: rattle (tick)', hold=1.1)], errfix=[8],
  device=DEV('diagram', 'D8_split', 'the fake bell vs the real bell'), energy='rings pulsing on both sides')
X(T(218), 'CU', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_queen',
  'HOLD H4: her face turns to the lens (531.9): red glowing irises, veined whites, the full grin, cheek folds, porcelain cracks, black '
  'tears; deepest silence at 533.2; at 533.68 the grin drops to a flat line in 2 frames; the lipstick steps stay on her cheeks like scars',
  P(4), hold='H4',
  chars=[Q('S3c', [960, 560, 1.2], acts=[A(531.9, 'head_to_lens', dur=0.25), A(533.68, 'smile_off', frames=2)])],
  q=dict(stage='S3c', size=0.80, where='on the bunk', framing='CU to ECU 80 %', wrong='the full face; then the smile goes off'),
  errfix=[19], energy='the turn, the stare in the silence, the snap off')
X(534.68, 'WS', 'ours', 'mess_porch/porch_crate', 'night', 'OURS porch: Tess winds up with the padlock (534.96)', HH(3, shake=22), tr='glint',
  chars=[body('tess', 960, 900, 420, 'profile_left', 'angry', [A(534.96, 'wind_up', prop='padlock')])], errfix=[9], energy='the wind-up')
X(535.36, 'INSERT', 'ours', 'mess_porch/bell_hit', 'bell_hit',
  'CONTACT at 535.36: padlock on the rim, spark, 2-frame white flash, the rim vibrating (wobble lines), the crack rattling', FA(6, hit=[(535.36, 18)]),
  tr='white', hud=[rings(535.40, 'broken', 960, 540, 4, 1.2)], errfix=[9], energy='impact, vibrating rim, jagged rings')
STATE(535.36, bell='struck', padlock='struck')
STATE(534.70, doorway='red')                     # the spill through the doorway turns red (climax)
X(536.00, 'WS', 'climax', 'mess_porch/porch_crate', 'bell_hit',
  'Tess with the ringing bell, jagged broken rings; red rim light begins: the climax red starts', PU(3),
  chars=[body('tess', 960, 900, 420, 'profile_left', 'angry', [A(R(0), 'hold_up', prop='padlock', side=-1)])], energy='bell vibrating, pull-out')
STATE(536.4, padlock='tess_hand')
X(T(221), 'INSERT', 'theirs_break', 'cabin_dawn/clock', 'dawn_break',
  'D9: THEIRS clock 6:59:59 -> 7:00:00 at 538.7; the second hand passes 12 and stops looping; big chip 7:00 AM (type beat 5)',
  P(4), tr='glint', hud=[diagram(538.2, 'D9', 'the clock reaches 7:00:00 and stops looping', hold=1.0), typebeat(538.7, 5, '7:00 AM'),
                         chip(538.7, '7:00 AM', 'theirs')], fx_post=[dict(t=538.7, white=0.6, dur=0.05)],
  device=DEV('diagram', 'D9', 'the loop breaks: 7:00 AM'), energy='the hand passing 12, the gold flickering')
STATE(538.7, clock='7:00')
X(T(222), 'WS', 'theirs_break', 'cabin_dawn/queen_3s', 'dawn_break', 'wide (dawn_break): the gold stutters, red leaks in at the edges; Noah drops his shoelace and sits up; the Queen frozen beside him, her flat line of a mouth',
  P(3), chars=[body('noah13', 860, 900, 420, 'q_right', 'relief', [A(w(222, 'drops'), 'drop_lace')], seated=True),
               Q('OFF', [1120, 900, 500, 1.0], mode='body', acts=[A(R(0), 'still')], seated=True)],
  q=dict(stage='OFF', size=0.30, where='on the bunk', framing='WS', wrong='the smile is gone; the loop is broken'), energy='the lace falling, gold stuttering')
X(T(223), 'CU', 'theirs_break', 'cabin_dawn/bokeh', 'dawn_break', 'CU of Noah: "Finally"', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'relief', [A(t(223), 'talk', line=223)], light=L_GOLD)], energy='relief')

# ================================================================ RULE 6 (card 542.03-545.22)
RULE(6)
X(card_times(6)[1], 'SEC', 'climax', 'stairs/section', 'red',
  'THE SECTION [R]: you push Noah up the red steps toward the doorway; tag HIM FIRST', HH(2, shake=15), reuse=290.2, tr='smear',
  chars=[body('you', 1100, 640, 90, 'profile_left', 'resolve', [A(R(0), 'shove')]), body('noah13', 980, 600, 80, 'profile_left', 'strain', [A(R(0), 'climb')])],
  hud=[tag(545.40, 'HIM FIRST', 960, 150, 'lipstick', 1.0)], errfix=[11], energy='the shove, small figures climbing')
STATE(545.3, noah='stairs', you='stairs')
X(Wc(227, 'toward'), 'WS', 'ours', 'camp_path/path_run', 'night', 'cut-in: Tess sprinting back across the path to Cabin 7, beam swinging', HH(3, shake=22), tr='glint',
  chars=[body('tess', 960, 900, 400, 'front', 'fear', [A(R(0), 'run', to=960)])], energy='run cycle, beam swinging')
STATE(546.4, tess='cabin7_doorway', flashlight='tess_doorway')
X(546.73, 'OTS', 'climax', 'stairs/ots_climb', 'red', 'Noah climbing the top treads toward the doorway, you behind him', HH(3, shake=20), tr='glint',
  chars=[body('noah13', 960, 900, 600, 'back', 'strain', [A(R(0), 'climb')]), body('you', 760, 1200, 900, 'back', 'resolve', [], ots=True)],
  energy='climbing, red edges')
X(T(228), 'WS', 'climax', 'cabin_now/master', 'red',
  'OURS, from Cabin 7: his bare foot comes out of the dark stairs through the doorway onto our floorboards', P(3), tr='glint', errfix=[11],
  setup='C7_RED', energy='the foot stepping out, red spill')
X(T(229), 'INSERT', 'climax', 'cabin_now/floor_cu', 'red',
  'the same framing as 355.3 (feet at the step), the opposite outcome: the bare foot planted on our floorboard; it stays', P(3), reuse=355.3,
  chars=[feet('noah13', 960, 860, 720, [A(R(0), 'still')])], energy='the foot holding')
X(T(230), 'MS', 'climax', 'cabin_now/doorway', 'red',
  'MS at the doorway from our side: Tess\'s orange arm, foreshortened toward the lens, grabs his taped wrist and pulls', HH(3, shake=18),
  chars=[hands('tess', 900, 520, 620, [A(551.86, 'reach_grab', foreshortened=True)], sleeve='orange'), hands('noah13', 1100, 560, 480, [], tape=True)],
  errfix=[7], energy='the grab, the pull')
X(Wc(230, 'from'), 'CU', 'climax', 'cabin_now/bokeh', 'red', 'CU of Tess hauling with both hands, teeth gritted, the doorway red behind her', HH(3, shake=16),
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'angry', [A(R(0), 'yank')], light=L_RED)], energy='straining, handheld')
X(T(231), 'CU', 'climax', 'cabin_now/doorway', 'red', 'CU Noah13 yelps, half through the doorway', P(4),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'scream', [A(553.62, 'flinch')], light=L_RED)], energy='yelp')
X(T(232), 'INSERT', 'climax', 'cabin_now/hands', 'red', 'ECU: the fingers lengthen inside the blue tape', P(3),
  chars=[hands('noah13', 960, 560, 560, [A(R(0), 'age', part='hand', dur=1.6)], tape=True)], errfix=[5, 14], energy='fingers growing')
X(555.93, 'INSERT', 'climax', 'cabin_now/floor_cu', 'red', 'the empty tape loop slips off and drops onto the floorboards', P(3.5),
  props=dict(tape='off_loop at 556.3'), errfix=[5], energy='the loop falling')
STATE(556.3, tape='off_loop_floor')
X(T(233), 'MS', 'climax', 'cabin_now/doorway', 'red', 'MS: Tess leans back and pulls; his shoulders come through the white frame, already broader', HH(3, shake=18),
  chars=[body('tess', 820, 1060, 620, 'q_right', 'angry', [A(R(0), 'yank')]), body('noah_grown', 1160, 1060, 600, 'q_left', 'shaken', [A(R(0), 'pulled_along')])],
  energy='the pull')
X(Wc(233, 'pulls'), 'WS', 'climax', 'cabin_now/master', 'red', 'wide: they fall back onto the floorboards together (559.24); dust bursts in the red light', HH(3, shake=18), reuse=547.43,
  chars=[body('tess', 900, 980, 460, 'q_right', 'fear', [A(559.24, 'fall_back')]), body('noah_grown', 1100, 980, 500, 'q_left', 'shaken', [A(559.24, 'stumble')])],
  energy='the fall, dust')
STATE(559.0, noah='ours')
X(T(234), 'INSERT', 'climax', 'cabin_now/hands', 'red', 'insert: the cuffs ride up adult forearms', P(3),
  chars=[hands('noah_grown', 960, 560, 560, [A(R(0), 'age', part='forearm')], cuffs='riding_up')], errfix=[5], energy='cuffs sliding')
X(Wc(234, 'halfway'), 'MS', 'climax', 'cabin_now/master', 'red', 'MS: a grown body in a kid\'s sweatshirt, cuffs halfway up', P(3, roll=6),
  chars=[body('noah_grown', 960, 1060, 640, 'front', 'shaken', [A(R(0), 'tremble')], cuffs='halfway')], energy='trembling, dutch 6 deg')
X(T(235), 'CU', 'climax', 'cabin_now/bokeh', 'red',
  'HOLD H5: the face morphs from 13 to 27 on camera: the jaw lengthens, stubble fades in, brown eyes (never yellow)', P(4), hold='H5',
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'shaken', [A(562.45, 'age', t1=565.05, from_age=13, to_age=27), A(t(235), 'talk_silent', dur=1.2)], light=L_RED,
              eyes='brown')], errfix=[18, 29], energy='the morph, push 4 %/s')
X(T(236), 'CU', 'climax', 'stairs/bokeh', 'red', 'CU of you on the stairs below the doorway, staring up', P(3, roll=-6),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'shock', [A(R(0), 'stare')], light=L_RED)], energy='staring, dutch')
X(Wc(236, 'barely'), 'ECU', 'climax', 'cabin_now/bokeh', 'red', 'ECU his mouth: the low voice; stubble', P(4),
  chars=[bust('noah_grown', 960, 480, 1.6, 'front', 'shaken', [A(R(0), 'talk_silent', dur=1.0)], light=L_RED, eyes='brown')], energy='talking')
X(T(237), 'MS', 'climax', 'cabin_now/master', 'red', 'MS: he stares at his raised hands', P(3, roll=6),
  chars=[body('noah_grown', 960, 1060, 640, 'front', 'shaken', [A(R(0), 'look_at_hands')])], energy='staring at the hands')
X(T(238), 'CU', 'climax', 'cabin_now/bokeh', 'red', 'CU grown Noah staring at his shaking hands raised before his face (brown eyes)', P(4),
  chars=[bust('noah_grown', 960, 580, 1.0, 'front', 'shaken', [A(R(0), 'look_at_hands'), A(R(0), 'tremble', amount=0.6)], light=L_RED, eyes='brown')],
  energy='hands trembling in the foreground')
X(Wc(238, "they're", n=1), 'INSERT', 'climax', 'cabin_now/hands', 'red', 'insert: his big shaking hands beside your candy fist for scale', P(3),
  chars=[hands('noah_grown', 860, 560, 620, [A(R(0), 'tremble', amount=0.6)]), Fist(1220, 640, 440)], energy='shaking')
X(T(239), 'MS', 'climax', 'cabin_now/bunk_rail', 'red', 'MS: he rises', P(3),
  chars=[body('noah_grown', 960, 1060, 600, 'q_left', 'shaken', [A(R(0), 'stand_up')])], energy='rising')
X(Wc(239, 'shoulder'), 'MS', 'climax', 'cabin_now/bunk_rail', 'red',
  'the top rail slams his shoulder (573.5): dust burst, the frame jumps, camera hit', HH(3, shake=20, hit=[(573.54, 16)]),
  chars=[body('noah_grown', 960, 1060, 640, 'q_left', 'shaken', [A(573.54, 'stand_hit')])], errfix=[6], energy='impact, dust burst')
X(T(240), 'WS', 'climax', 'cabin_now/dutch_low', 'red', 'wide: grown Noah hunched under the bunk he could walk under', P(3, roll=8),
  chars=[body('noah_grown', 960, 960, 560, 'q_left', 'shaken', [A(R(0), 'rock')])], energy='hunched, red pulse, dutch 8 deg')
X(T(241), 'WS', 'theirs_break', 'cabin_dawn/master', 'dawn_break',
  'THEIRS (dawn_break) behind you (OTS): she stands by the bunk calling his name, S3c face, mouth open', HH(2, shake=15), tr='glint',
  chars=[bust('you', 600, 640, 1.3, 'back', 'fear', [], light=L_RED), Q('S3c', [1300, 900, 480, 2.0], mode='body', acts=[A(R(0), 'call_silent')])],
  q=dict(stage='S3c', size=0.30, where='by the bunk, behind you', framing='WS 30 %', wrong='calling'), errfix=[27],
  energy='gold stuttering, red leaking from the edges')
X(Wc(241, 'name'), 'CU', 'theirs_break', 'cabin_dawn/bokeh', 'dawn_break', 'CU: she calls his name, the full grin stretched wide, red eyes, black tears', P(5),
  chars=[Q('S3c', [960, 560, 1.1], acts=[A(R(0), 'call_silent')])],
  q=dict(stage='S3c', size=0.65, where='by the bunk', framing='CU 65 %', wrong='calling'), energy='mouth working, gold stuttering')
STATE(576.25, queen='theirs_bunk_standing')
X(T(242), 'WS', 'climax', 'cabin_now/dutch_low', 'red', 'OURS, red wide: grown Noah on the floor slaps his hands over his ears; Tess beside him; the red doorway behind', HH(2.5, shake=16, roll=6), tr='glint',
  chars=[body('noah_grown', 900, 960, 540, 'front', 'fear', [A(w(242, 'covers'), 'cover_ears')], eyes='brown', seated=True),
         body('tess', 1300, 960, 480, 'q_left', 'fear', [A(R(0.3), 'look', x=900, y=600)], kneel=True)], errfix=[29], energy='hands over ears, red pulse')
X(T(243), 'ECU', 'climax', 'cabin_now/bokeh', 'red', 'ECU his eyes squeezed shut', P(4),
  chars=[bust('noah_grown', 960, 520, 1.6, 'front', 'fear', [A(R(0), 'cover_ears')], light=L_RED)], energy='squeezing')
X(T(244), 'MS', 'theirs', 'cabin_dawn/bunk_2s', 'dawn', '0.6 s flash in the THEIRS look (frozen gold): Noah13 covering his ears on the bunk, an earlier loop',
  FA(5), tr='glint', chars=[body('noah13', 960, 1000, 600, 'front', 'scream', [A(R(0), 'cover_ears')], seated=True)], energy='flash')
X(582.53, 'MS', 'climax', 'cabin_now/master', 'red', 'back: grown Noah rocking, hands on his ears', HH(2.5, shake=16), tr='glint',
  chars=[body('noah_grown', 960, 1060, 640, 'front', 'fear', [A(R(0), 'rock')])], energy='rocking')
X(T(245), 'WS', 'climax', 'stairs/up', 'red', 'Tess at the top of the stairs in the doorway (from the stairs), red light, shouting', HH(3, shake=20),
  chars=[body('tess', 960, 560, 360, 'front', 'shout', [A(R(0), 'shout_silent')], d=3.0)], energy='handheld, shouting')
X(T(246), 'CU', 'climax', 'stairs/bokeh', 'red', 'CU of Tess in the red doorway: "Five!"; GIANT 5 slams over her', HH(2, shake=12),
  chars=[bust('tess', 960, 560, 1.0, 'front', 'shout', [A(t(246), 'talk', line=246)], light=L_RED)], hud=[giant(585.62, 5)], voice_fx='far',
  energy='the shout, numeral slam')
X(T(247), 'SEC', 'climax', 'stairs/section', 'red', 'the section [R]: you climbing, three steps from the top', HH(2, shake=12), reuse=290.2,
  chars=[body('you', 900, 560, 90, 'profile_left', 'fear', [A(R(0), 'climb')])], energy='climbing')
STATE(586.28, you='stairs_top3')
X(587.20, 'POV', 'climax', 'stairs/up', 'red', 'POV from below: your hand reaching up toward Tess\'s light', HH(3, shake=18),
  chars=[POVH([A(R(0), 'reach', up=True)], 960, 700, 620)], energy='reaching')
X(T(248), 'WS', 'climax', 'stairs/low', 'red', 'low angle at the foot of the stairs: she steps onto tread 8 (silence)', SIL(1.5, roll=-8),
  chars=[Q('S3c', [960, 900, 520, 2.0], mode='body', view='q_left', acts=[A(588.4, 'climb_step', to=8)])],
  q=dict(stage='S3c', step=8, size=0.30, where='the foot of the stairs', framing='low WS', wrong='she follows'), errfix=[27],
  energy='silence push, her foot on the tread')
STATE(588.4, queen='stairs_tread8')
X(Wc(249, 'wait'), 'CU', 'climax', 'stairs/low', 'red',
  'HOLD H6: her jaw drops; the face below the eyes stretches 1.35x into a tall glossy void; Noah13\'s face glitches inside it, '
  'lip-synced to his voice ("Wait, he forgot his shoe.")', P(4), hold='H6', tr='white',
  chars=[Q('S4', [960, 520, 1.2], acts=[A(589.60, 'jaw_drop', stretch=1.35, dur=0.3), A(t(249), 'talk', line=249, inner='noah13', pixel_sort=True)])],
  q=dict(stage='S4', size=0.75, where='the foot of the stairs', framing='low CU 75 %', wrong='the jaw void with Noah\'s voice'),
  errfix=[12], energy='the jaw dropping, Noah\'s face glitching inside, push 4 %/s')
X(591.58, 'ECU', 'climax', 'stairs/low', 'red', 'ECU of the void with Noah13\'s face and gap teeth inside', P(5),
  chars=[Q('S4', [960, 560, 1.8], acts=[A(R(0), 'still', inner='noah13', pixel_sort=True)])], errfix=[12], energy='pixel-sort crawling')
X(T(251), 'ECU', 'climax', 'stairs/bokeh', 'red', 'your eyes widening', FA(6),
  chars=[bust('you', 960, 520, 1.6, 'front', 'fear', [A(R(0.1), 'expr', name='fear')], light=L_RED)], energy='eyes widening')
X(T(252), 'MS', 'climax', 'stairs/ots_climb', 'red', 'on the stairs, you turn with a 0.15 s whip; tag DON\'T TURN AROUND', WH(1300, 520, 1.15), tr='glitch',
  chars=[body('you', 960, 1060, 640, 'q_left', 'fear', [A(594.93, 'snap_turn', dur=0.15)])], hud=[tag(594.95, "DON'T TURN AROUND", 960, 150, 'lipstick', 1.0)],
  energy='whip pan on the turn')
X(T(253), 'MS', 'memory', 'memory/night_window', 'sepia_night', 'memory: Noah13 at the night window mouthing words you never heard', P(3), tr='sepia',
  chars=[body('noah13', 960, 1040, 620, 'q_left', 'shy', [A(R(0), 'talk_silent', dur=1.6)])], energy='lips moving, no sound')
X(T(254), 'CU', 'memory', 'memory/night_window', 'sepia_night', 'memory CU: his mouth moving, no sound', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'q_left', 'shy', [A(R(0), 'talk_silent', dur=2.0)], light=L_MEM)], energy='mouthing')
X(T(255), 'MS', 'climax', 'stairs/ots_climb', 'red', 'your turn in slow motion on the stairs', P(2, roll=-8), tr='sepia',
  chars=[body('you', 960, 1060, 640, 'q_left', 'fear', [A(R(0), 'turn', slow=0.3)])], energy='slow motion, red pulse')
X(Wc(255, 'before'), 'SEC', 'climax', 'stairs/section', 'red', 'the section [R]: she is climbing behind you, two steps down', P(2), reuse=290.2,
  chars=[body('you', 900, 540, 90, 'q_left', 'fear', []), Q('S3c', [840, 600, 100], mode='body', acts=[A(R(0), 'climb_step')])],
  q=dict(stage='S3c', step=3, size=0.10, where='two steps below you (section)', framing='section', wrong='she follows'), energy='her small figure climbing')
X(T(256), 'POV', 'climax', 'stairs/pov_down', 'red',
  'POV from the stairs down into the red-lit gold cabin: the shoe beside the bed; label ONE SHOE echo (stairs background only)', SIL(1.5),
  hud=[label(603.3, 'ONE SHOE', [1100, 900], dx=160, dy=-120)], errfix=[27], energy='silence push, red light flickering below')
X(T(257), 'POV', 'climax', 'stairs/pov_down', 'red',
  'HOLD H7: POV of your boots on a red-edged tread -> the next tread down holds HER FOOT (anatomical, ash-white, black nails, the satin '
  'hem with spade pips), hit at 605.21 -> tilt up the dress to her S3c face 30 cm away, grin widening, a hand rising toward your shoulder',
  TL(dy=-420, r=3, x=960, y=760, z=1.1, hit=[(605.21, 14)]), hold='H7', tr='cut',
  chars=[C('you', [960, 980, 900], 'front', 'neutral', [], mode='feet', pov=True),
         Q('S3c', [960, 300, 400], mode='feet', pov=True, acts=[A(605.17, 'fade_in', dur=0.05), A(605.21, 'toes_curl'), A(606.0, 'fade_out', dur=0.14)]),
         Q('S3c', [960, 330, 1.35], mode='bust', acts=[A(605.96, 'fade_in', dur=0.14), A(606.2, 'grin_widen'), A(606.6, 'reach_shoulder')])],
  q=dict(stage='S3c', step='below yours', size=1.0, where='the step below yours', framing='POV, 100 %', wrong='30 cm away'),
  errfix=[27], energy='the tilt up from her foot to her face, the hit')
STATE(604.48, queen='step_below_yours')
X(T(258), 'WS', 'climax', 'stairs/up', 'red', 'from the stairs side: Tess\'s orange arm shoots out of the doorway above', HH(3, shake=24),
  chars=[hands('tess', 960, 380, 620, [A(608.3, 'reach_grab', foreshortened=True)], sleeve='orange')], errfix=[7], energy='the arm shooting down')
X(608.97, 'INSERT', 'climax', 'stairs/up', 'red', 'her fist closes on your corduroy collar (608.97); whip pull; white flash; giant 0', WH(960, 200, 1.2, hit=[(608.97, 18)]),
  tr='white', chars=[hands('tess', 960, 520, 620, [A(608.97, 'grab_collar'), A(609.1, 'yank')], sleeve='orange')], hud=[giant(608.97, 0, hold=0.4)],
  errfix=[7], energy='the yank')
STATE(609.3, you='ours_floor', queen='glass')

# ================================================================ RULE 7 (card 609.48-614.71)
RULE(7)
X(card_times(7)[1], 'WS', 'climax', 'cabin_now/dutch_low', 'red',
  'OURS, red: you slam onto the floorboards (dust, camera hit at 614.9); behind you the white frame holds glass again: silvering crawls in '
  'from the edges in 0.3 s; the steps glow; her figure climbs', HH(2.5, shake=18, hit=[(614.9, 16)], roll=8), tr='white',
  chars=[C('you', [960, 900, 820], 'q_left', 'fear', [A(614.9, 'fall_back')], mode='lying')], props=dict(mirror='glass returning 614.9-615.2'),
  energy='the fall, dust, silvering crawling in, red pulse')
STATE(614.9, mirror='glass', doorway='none', flashlight='floor')
X(T(262), 'MS', 'climax', 'cabin_now/master', 'red', 'Tess shoves the towel into your hands; you clutch it', HH(3, shake=18, roll=6),
  chars=[body('tess', 900, 1060, 640, 'q_left', 'fear', [A(w(262, 'shoves'), 'shove', prop='towel')]),
         body('you', 1200, 1060, 600, 'q_left', 'fear', [A(w(262, 'towel') + 0.3, 'take', prop='towel')], kneel=True)], energy='the thrust')
STATE(617.8, towel='your_hands')
X(T(263), 'POV', 'climax', 'mirror/glass_cu', 'red', 'POV olive sleeve: steps 1, 2, 3 erased top-down, each numeral ticking off; tag TOP DOWN',
  HH(3, shake=14), chars=[POVH([A(618.73, 'wipe_glass', strokes=3, dir='down', towel=True)], 1000, 500)],
  hud=[count_pop(618.75, 1, 1230, 300, erase=True), count_pop(619.37, 2, 1178, 370, erase=True), count_pop(619.69, 3, 1126, 440, erase=True),
       tag(619.40, 'TOP DOWN', 960, 150, 'lipstick', 0.6)], props=dict(erased='1-3 by 619.7'), energy='wipe strokes')
STATE(619.7, erased=3)
X(620.00, 'POV', 'climax', 'mirror/glass_cu', 'red', 'POV: steps 4-7 wiped away, numerals ticking off', HH(3, shake=12),
  chars=[POVH([A(620.1, 'wipe_glass', strokes=2, dir='down', towel=True)], 960, 640)],
  hud=[count_pop(620.15 + 0.15 * k, 4 + k, 1074 - 52 * k, 510 + 70 * k, erase=True) for k in range(4)], energy='wipe strokes')
STATE(620.8, erased=7)
X(621.25, 'WS', 'climax', 'mirror/glass_wide', 'red', 'the whole mirror nearly clean: one streak of red left across the glass', P(3, roll=-6), energy='the last streak, red pulse')
X(T(265), 'WS', 'climax', 'mirror/through', 'red',
  'HOLD H8: through the last streak, her full figure lit red on the lower steps, lifting her foot toward a step that is no longer there',
  P(3), hold='H8', chars=[Q('S3c', [960, 900, 380, 2.0], mode='body', acts=[A(w(265, 'lift'), 'lift_foot', hang=True)])],
  q=dict(stage='S3c', size=0.35, where='through the streak, the lower steps', framing='WS 35 %', wrong='the foot finds no step'),
  energy='the foot rising, red pulse 1.2 s')
X(T(266), 'INSERT', 'climax', 'mirror/through', 'red', 'ECU: the foot hanging over nothing, red pulsing', P(3),
  chars=[Q('S3c', [960, 880, 820], mode='feet', acts=[A(R(0), 'lift_foot', hang=True)])], energy='the foot trembling')
X(T(267), 'WS', 'climax', 'mirror/glass_wide', 'red', 'the whole mirror: the glass goes black from the edges in at 628.18', P(2),
  fx_post=[dict(t=628.18, glitch=0.6, dur=0.08)], props=dict(mirror='dark at 628.18'), energy='black closing in')
STATE(628.18, mirror='dark', queen='absent')
X(628.55, 'BLACK', 'black', 'black/black', 'black', 'pure black for 0.5 s', P(0), tr='black', captions=False, energy='black (the sub-drop tail)')

# ================================================================ ENDING 629.05 - 700 (lines 268-299)
STATE(629.0, towel='draped_over_mirror', mirror='covered')
X(T(268), 'WS', 'ending', 'cabin_now/floor_wide', 'after',
  'ENDING wide: grown Noah sitting on the floor at adult scale (1.08x your height); the flashlight on the floor rakes a warm pool; the towel '
  'draped over the dark mirror; the phone on the sill with its red glint', P(2.5), setup='END_WIDE', tr='cut', chip='CABIN 7 · {ours}',
  chars=[body('noah_grown', 900, 900, 480, 'q_right', 'shaken', [A(R(0), 'rock')], seated=True), body('you', 1300, 900, 440, 'q_left', 'grief', [], seated=True)],
  energy='dust in the floor beam, breath, push')
X(Wc(268, 'sweatshirt'), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU grown Noah: the green CEDAR LAKE collar two sizes too small, cutting at his neck', P(3),
  chars=[bust('noah_grown', 960, 580, 1.0, 'front', 'shaken', [A(R(0), 'tremble')], light=L_END, eyes='brown', cuffs='halfway')], energy='trembling')
X(T(269), '2S', 'ending', 'cabin_now/floor_wide', 'after', '2-shot side by side: he is bigger than you', P(3),
  chars=[body('noah_grown', 760, 1060, 640, 'q_right', 'shaken', [], seated=True), body('you', 1180, 1060, 590, 'q_left', 'grief', [], seated=True)],
  energy='breathing')
X(T(270), 'MS', 'ending', 'cabin_now/floor_wide', 'after', 'you drape your olive jacket on him', P(3),
  chars=[body('you', 1100, 1060, 600, 'q_left', 'grief', [A(w(270, 'jacket'), 'give_jacket')]), body('noah_grown', 820, 1060, 640, 'q_right', 'shaken', [])],
  props=dict(jacket='noah at 635.06'), energy='the jacket swinging around')
STATE(635.06, jacket='noah')
X(T(271), 'WS', 'ending', 'cabin_now/floor_wide', 'after', 'wide on the floor: he pulls your olive jacket around himself by the corduroy collar', P(3),
  chars=[body('noah_grown', 860, 900, 480, 'q_right', 'hopeful', [A(R(0), 'hold_collar')], seated=True), body('you', 1260, 900, 440, 'q_left', 'grief', [], seated=True)],
  energy='the jacket settling, dust in the floor beam')
X(Wc(271, 'and'), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU grown Noah: is Mom still up?', P(3),
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'hopeful', [A(R(0), 'talk_silent', dur=1.2)], light=L_END, eyes='brown')], energy='asking')
X(T(272), 'INSERT', 'ending', 'cabin_now/clock', 'after', 'the Cabin 7 clock: 12:07', P(3), chip='CABIN 7 · {ours}',
  device=DEV('insert', 'clock_1207', 'just after midnight: 12:07'), energy='second hand ticking forward')
X(T(273), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of you: of course she is', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0.4), 'swallow')], light=L_END)], energy='a sad smile')
X(T(274), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of you: you haven\'t called her', P(3),
  chars=[bust('you', 960, 560, 1.0, 'q_right', 'grief', [], light=L_END)], energy='breath')
X(Wc(274, "you're"), 'MS', 'ending', 'cabin_now/floor_wide', 'after', 'you reach for your phone with your right hand; the left still a fist', P(3),
  chars=[body('you', 960, 1060, 640, 'q_left', 'grief', [A(R(0.2), 'reach', side=1)], fist='left')], energy='reaching')
X(T(275), 'POV', 'ending', 'cabin_now/hands', 'after', 'POV: your left fist trembles and will not open', P(3),
  chars=[Fist(960, 620, 560, [A(R(0), 'tremble', amount=0.8), A(646.9, 'fist', fail_open=True)])], errfix=[17], energy='straining')
STATE(645.0, fist='trembling')
X(Wc(275, 'your', n=1), 'POV', 'ending', 'cabin_now/hands', 'after', 'ECU: the fingers straining, still closed', P(3.5),
  chars=[Fist(960, 620, 700, [A(R(0), 'tremble', amount=0.9)])], errfix=[17], energy='fingers fighting')
X(T(276), 'POV', 'ending', 'cabin_now/hands', 'after', 'the palm opens slowly', P(2.5),
  chars=[POVH([A(649.2, 'open_fist', dur=1.8)], 960, 620, 600, hand='left')], errfix=[17], energy='fingers uncurling')
STATE(649.12, fist='opening')
X(T(277), 'POV', 'ending', 'cabin_now/hands', 'after', 'the red candy lies in the open palm', P(3),
  chars=[POVH([A(R(0), 'open_hand')], 960, 620, 640, hand='left', candy='palm')], errfix=[4], device=DEV('insert', 'candy_palm', 'the candy, kept'),
  energy='the candy rolling slightly')
STATE(651.11, fist='palm_candy', candy='palm')
STATE(653.91, your_phone='call_mom')
STATE(659.90, your_phone='noah_hand')
X(Wc(277, 'mark'), 'INSERT', 'ending', 'cabin_now/hands', 'after', 'the red wrapper mark pressed in the palm BESIDE the candy', P(3.5),
  chars=[POVH([A(R(0), 'open_hand')], 960, 620, 720, hand='left', candy='palm', mark=True)], errfix=[4], energy='push')
X(T(278), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of you, the phone at your ear; one ring, and she picks up', HH(1.5, shake=6),
  chars=[bust('you', 960, 560, 1.0, 'q_left', 'grief', [A(R(0), 'phone_to_ear', side=1)], light=L_END)], props=dict(your_phone='call_mom'),
  hud=[dict(t=T(278), type='phone', state='calling', name='MOM', x=1600, y=860, scale=0.4, inset=True)], energy='breath, the ring')
X(Wc(278, 'on'), 'WS', 'ending', 'cabin_now/floor_wide', 'after', 'wide: you on the floor with the phone at your ear, Noah beside you; the call connects (inset lower right)', P(2.5),
  chars=[body('you', 1240, 900, 440, 'q_left', 'grief', [A(R(0), 'phone_to_ear', side=1)], seated=True), body('noah_grown', 860, 900, 480, 'q_right', 'hopeful', [], seated=True)],
  hud=[dict(t=Wc(278, 'on'), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), x=1600, y=860, scale=0.4, inset=True)],
  device=DEV('ui', 'call', 'the call to Mom'), energy='timer running')
X(T(279), 'UI', 'ui', 'ui/call', 'phone', 'Mom\'s live waveform: "Did you find the sweatshirt?"', P(2),
  hud=[dict(t=T(279), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=True, follow_line=279), x=960, y=560)],
  energy='waveform moving with her voice')
X(T(280), 'INSERT', 'ending', 'cabin_now/hands', 'after', 'insert: his big shaking hand held out; the phone passes from your hand to his', P(3),
  chars=[hands('noah_grown', 860, 600, 480, [A(w(280, 'holds'), 'hand_out'), A(R(0), 'tremble', amount=0.4), A(659.9, 'take', prop='phone')]),
         hands('you', 1060, 560, 420, [A(659.7, 'give', prop='phone')], sleeve='olive')],
  props=dict(your_phone='noah_hand'), energy='hand-off')
X(T(281), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of grown Noah, phone at his ear: "Hi, Mom." (lip-sync)', P(2.5),
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'relief_cry', [A(R(0), 'phone_to_ear', side=1), A(t(282), 'talk', line=282)], light=L_END, eyes='brown')],
  energy='tears, push')
X(e(282) + 0.02, 'CU', 'ending', 'cabin_now/bokeh', 'after',
  'HOLD H9: the long pause: Noah\'s CU with tears running; the call waveform (small, lower right) goes flat; he says it again, softer', SIL(1.5), hold='H9',
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'relief_cry', [A(R(0.3), 'tears', amount=1.0), A(w(284, 'says'), 'talk_silent', dur=0.8)], light=L_END, eyes='brown')],
  hud=[dict(t=e(282) + 0.05, type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=False, flat=True), x=1600, y=860, scale=0.4, inset=True)],
  energy='tears running, slow push in the pause')
X(T(285), 'WS', 'ending', 'cabin_now/floor_wide', 'after', 'wide on the floor: you and Noah huddled over the phone; the call inset (lower right) spikes with her chair scrape',
  P(2.5), chars=[body('noah_grown', 860, 900, 480, 'q_right', 'relief_cry', [A(R(0), 'phone_to_ear', side=1)], seated=True),
                 body('you', 1240, 900, 440, 'q_left', 'grief', [A(R(0.3), 'lean_in', amount=0.2)], seated=True)],
  hud=[dict(t=T(285), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=True, spike_at=w(285, 'chair')), x=1600, y=860, scale=0.4, inset=True)],
  energy='the spike, both leaning in')
X(T(286), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of Noah: she asks where he is', P(3),
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_left', 'hopeful', [A(R(0), 'phone_to_ear', side=1)], light=L_END, eyes='brown')], energy='listening')
X(T(287), 'CU', 'ending', 'cabin_now/bokeh', 'after', 'CU of Noah looking at you for help', P(3),
  chars=[bust('noah_grown', 960, 560, 1.0, 'q_right', 'fear', [A(R(0.2), 'look', x=1400, y=520, lost=True)], light=L_END, eyes='brown')], energy='the look')
X(T(288), 'WS', 'memory', 'memory/moms_car', 'sepia_day', 'memory: Mom\'s car at the gate, a waving arm from the window (no face)', P(3), tr='sepia',
  energy='the arm waving, dust from the tyres')
X(Wc(288, 'she'), 'CU', 'memory', 'memory/moms_car', 'sepia_day', 'memory CU: kid Noah waving back at the car, grinning, a week ago for him', P(3),
  chars=[bust('noah13', 960, 560, 1.0, 'front', 'grin_kid', [A(R(0), 'wave')], light=L_MEM)], energy='waving')
X(T(289), 'WS', 'ending', 'cabin_now/master', 'phone_glow', 'wide [R 109.8]: behind you, Tess at the sill', P(2.5), reuse=109.82, tr='sepia',
  chars=[body('tess', 1120, 820, 380, 'back', 'neutral', [A(R(0.3), 'walk', to=1180)]), body('you', 760, 960, 300, 'q_right', 'grief', [], seated=True),
         body('noah_grown', 600, 960, 320, 'q_right', 'hopeful', [], seated=True)], energy='Tess crossing, push')
X(Wc(289, 'picks'), 'MS', 'ending', 'cabin_now/sill', 'phone_glow', 'Tess picks up her phone from the windowsill', P(3),
  chars=[hands('tess', 960, 560, 420, [A(674.43, 'pick_up', prop='phone')], sleeve='orange')], props=dict(phone='tess_hand at 674.43'),
  errfix=[16], energy='lifting the phone, dust trail')
STATE(674.43, phone='tess_hand')
X(T(290), 'MS', 'ending', 'cabin_now/sill', 'phone_glow', 'MS: Tess turns from the sill holding the phone face up in her palm, the red glint in its glass', P(3), errfix=[16],
  chars=[body('tess', 960, 1060, 640, 'q_left', 'neutral', [A(R(0), 'hold_up', prop='phone', face_up=True)])],
  energy='the glint pulsing')
X(677.34, 'MONTAGE', 'ending', 'cabin_now/sill', 'night',
  'RED X (4 of 4) + tag FACE UP over a 1.4 s montage of the phone face up on the sill at 112, 150, 284 and 546 s (0.35 s each), each with the red glint',
  P(4), montage=[dict(t=677.34, src_t=112.0), dict(t=677.69, src_t=150.0), dict(t=678.04, src_t=284.0), dict(t=678.39, src_t=546.0)],
  hud=[redx(677.39, 960, 560, 170, 1.2, n=4), tag(677.45, 'FACE UP', 960, 150, 'lipstick', 1.2)], errfix=[16],
  device=DEV('doc', 'face_up', 'the phone lay face up the whole time (a mirror nobody covered)'), energy='tiles cutting, the X')
X(T(291), 'INSERT', 'ending', 'cabin_now/phone_screen', 'phone_glow', 'insert: the orange sleeve wipes the dust off the black glass',
  P(3), chars=[hands('tess', 960, 560, 520, [A(679.15, 'wipe_glass', strokes=2, sleeve=True)], sleeve='orange')], energy='sleeve swiping')
X(680.50, 'CU', 'ending', 'cabin_now/phone_screen', 'phone_glow', 'CU: Tess\'s face reflected in the wiped black glass (it is a mirror)', P(3),
  chars=[bust('tess', 960, 560, 0.9, 'front', 'puzzled', [], light=L_PHONE, reflection=True)], energy='reflection sliding')
X(T(292), 'CU', 'ending', 'cabin_now/bokeh', 'phone_glow', 'CU of Tess, puzzled: "Did you get lipstick on this?" (lip-sync), holding it out', P(3),
  chars=[bust('tess', 960, 560, 1.0, 'q_right', 'puzzled', [A(t(292), 'talk', line=292), A(R(0), 'hold_up', prop='phone', side=-1)], light=L_PHONE)],
  energy='talking')
X(T(293), 'MS', 'ending', 'cabin_now/floor_wide', 'phone_glow', 'she holds the phone toward you', P(3),
  chars=[body('tess', 960, 1060, 640, 'q_left', 'puzzled', [A(R(0), 'hold_up', prop='phone')])], errfix=[16], energy='holding it out')
X(T(294), 'INSERT', 'ending', 'cabin_now/phone_screen', 'phone_glow',
  'the phone (in Tess\'s hand) fills the frame: 7 tiny lipstick steps, already there; numerals 1-4 pop on "count"', P(3.5),
  hud=[count_pop(685.31 + 0.12 * k, k + 1, 1100 - 40 * k, 360 + 60 * k, '#ffffff') for k in range(4)], props=dict(phone='screen_steps'),
  errfix=[25], device=DEV('diagram', 'D2_phone', 'seven tiny steps on the phone screen'), energy='numerals popping')
STATE(684.98, phone='screen_steps')
X(Wc(294, 'steps'), 'POV', 'ending', 'cabin_now/phone_screen', 'phone_glow', 'POV: the phone in Tess\'s hand held out to you; numerals 5-7 pop beside the tiny steps', P(3.5),
  chars=[hands('tess', 960, 640, 520, [A(R(0), 'hold_up', prop='phone')], sleeve='orange')],
  hud=[count_pop(686.45 + 0.12 * k, k + 5, 940 - 40 * k, 600 + 60 * k, '#ffffff') for k in range(3)], energy='numerals popping')
X(T(295), 'POV', 'ending', 'cabin_now/phone_screen', 'phone_glow', 'your fingertip slides below step 7', P(3),
  chars=[POVH([A(w(295, 'touch'), 'touch_glass', at=(860, 800))], 980, 900, 480)], energy='the finger descending')
X(T(296), 'POV', 'ending', 'cabin_now/phone_screen', 'phone_glow',
  'silence: your fingertip finds a clean red line under the glass (the eighth); CLICK at 690.19 (the same sample as 143.29) with a camera hit, '
  'a white flash and a 1.25x punch-in; CLEAN GLASS echo', SIL(1.5, hit=[(690.19, 10)], snap=(690.19, 1.25)),
  chars=[POVH([A(R(0), 'touch_glass', at=(860, 860)), A(690.19, 'nail_tap')], 980, 940, 480)], fx_post=[dict(t=690.19, white=0.85, dur=0.05)],
  hud=[label(690.3, 'CLEAN GLASS', [860, 860], dx=200, dy=-120)], props=dict(phone='screen_eighth'), errfix=[15],
  device=DEV('insert', 'eighth_phone', 'the eighth line on the phone'), energy='the click, punch-in 1.25x')
STATE(690.19, phone='screen_eighth')
X(T(297), 'INSERT', 'ending', 'cabin_now/phone_screen', 'phone_glow',
  'HOLD H10: push into the screen: on the 8th line the Queen\'s tiny figure (3 % of the frame), looking up, then one step higher', P(4), hold='H10',
  chars=[Q('S3c', [900, 860, 32, 1.04], mode='body', acts=[A(R(0), 'look_up'), A(694.3, 'climb_step', to=7)], tiny=True)],
  q=dict(stage='S3c', step=8, size=0.03, where='in the phone', framing='3 %', wrong='starting again'), energy='push 4 %/s into the screen')
STATE(691.86, phone='screen_queen', queen='phone')
X(T(298), 'CU', 'ending', 'cabin_now/phone_screen', 'phone_glow', 'CU: Tess\'s face reflected in the phone glass, then gone', P(4),
  chars=[bust('tess', 960, 560, 0.9, 'front', 'neutral', [A(R(0.5), 'fade_out')], light=L_PHONE, reflection=True)], energy='the reflection fading')
X(T(299), 'INSERT', 'ending', 'cabin_now/phone_screen', 'phone_glow',
  'the screen: Noah13\'s face speaks "Can I have one more minute?" (lip-sync); on "minute?" (697.95) it pixel-sorts into her S3c face looking '
  'into the lens; hard cut at 698.62', P(4),
  chars=[bust('noah13', 960, 540, 1.0, 'front', 'calm_kid', [A(t(299), 'talk', line=299)], inside='phone_screen'),
         Q('S3c', [960, 540, 1.0], acts=[A(697.95, 'pixel_sort_in', dur=0.3), A(698.1, 'stare')], inside='phone_screen')],
  fx_post=[dict(t=697.95, glitch=0.9, pixel_sort=1.0, dur=0.3)], voice_fx='phone_child',
  q=dict(stage='S3c', size=0.60, where='the phone', framing='60 %', wrong='looks into the lens (3 of 3)'), energy='lip-sync, pixel-sort')
STATE(697.95, phone='screen_face')
X(round(e(299) + 0.04, 3), 'BLACK', 'black', 'black/black', 'black',
  'black: a faint perfect bell; type beat 6: DON\'T MAKE A WISH. fades in at 698.75, WISH in lipstick red', P(0), tr='black', captions=False,
  hud=[typebeat(698.75, 6, "DON'T MAKE A WISH.", red_word='WISH', fade=0.4)], energy='the end card fading in')

# ================================================================ PUNCH-INS (1.08x on emphasis words, 1.25x on hits; DIRECTION_V2 5.1)
# (time, factor, word): make_plan.py adds an optical snap to the shot that contains the time.
PUNCHES = [(18.55, 1.08, 'breakfast'), (36.07, 1.08, 'sweatshirt'), (64.00, 1.08, 'crack'), (100.15, 1.08, 'wish'),
           (124.97, 1.25, 'fourth'), (147.44, 1.08, 'stays'), (165.52, 1.08, 'footprints'), (183.20, 1.08, 'ring'),
           (239.69, 1.08, 'minute'), (316.11, 1.25, 'Dad'), (375.79, 1.08, 'stay'), (395.69, 1.08, 'Mom'),
           (438.94, 1.25, 'canceled'), (507.88, 1.08, 'fist'), (530.87, 1.08, 'perfect'), (538.72, 1.25, 'rattle'),
           (571.46, 1.08, 'bigger'), (593.09, 1.08, 'thirteen'), (603.25, 1.08, 'shoe'), (652.56, 1.08, 'mark')]

# ================================================================ CAMERA GRAMMAR (DIRECTION_V2 5.1: push median ~3 %/s, p75 ~5.5 %/s, pull-outs ~10 %)
# 1. PULL_OUTS: these shots open tight on a detail and pull back to show the place (reveals); first sights of a room, the
#    re-establishing wides after the cards, memory reveals and the scale reveals (he is bigger).
# 2. The fast quartile: inserts, documents, diagrams, UI, type and POV push at least 5.5 %/s (6.5 %/s under 1 s); ECUs at
#    least 5 %/s. Faces, mids and wides keep the rates written above (2-4 %/s). Holds, silences, handheld, whips, tilts and
#    tracks are never touched.
PULL_OUTS = {1.90: 'pull', 41.66: 'pull', 59.50: 'pull', 72.31: 'reveal', 77.51: 'pull', 80.07: 'pull', 88.70: 'pull', 93.50: 'pull',
             102.22: 'pull', 115.82: 'pull', 121.06: 'pull', 133.56: 'reveal', 155.99: 'reveal', 163.67: 'pull', 171.19: 'pull',
             175.59: 'pull', 208.32: 'reveal', 218.13: 'pull', 234.80: 'pull', 260.38: 'pull', 273.35: 'reveal', 290.23: 'pull',
             291.30: 'reveal', 299.58: 'pull', 305.94: 'pull', 338.76: 'reveal', 376.80: 'pull', 382.16: 'reveal', 400.24: 'pull',
             412.54: 'pull', 439.41: 'pull', 483.31: 'pull', 519.90: 'pull', 621.25: 'pull', 629.05: 'reveal', 664.87: 'pull',
             32.38: 'pull', 241.12: 'pull', 632.97: 'pull'}
FAST = ('INSERT', 'DOC', 'DIAGRAM', 'UI', 'TYPE', 'POV', 'SPLIT', 'MONTAGE')


def camera_grammar():
    shots = sorted(SHOTS, key=lambda s: s['t0'])
    for s, nxt in zip(shots, shots[1:] + [None]):
        d = (nxt['t0'] if nxt else 700.0) - s['t0']
        c = s['cam']
        key = next((k for k in PULL_OUTS if abs(k - s['t0']) < 0.03), None)
        if key is not None:
            mv = PULL_OUTS[key]
            s['cam'] = cam(mv, rate=-0.035 if mv == 'pull' else -0.07, x=c.get('x', 960), y=c.get('y', 540), z=max(c.get('z', 1.0), 1.12),
                           **{k: v for k, v in c.items() if k in ('hit', 'snap', 'roll', 'dx', 'dy')})
            continue
        if s.get('hold') or c.get('silence') or c['mv'] != 'push': continue
        r = c.get('rate', 0.03)
        if s['type'] in FAST:
            c['rate'] = max(r, 0.065 if d < 1.0 else 0.055)
        elif s['type'] == 'ECU':
            c['rate'] = max(r, 0.05)


camera_grammar()

# ================================================================ NEW SOUND FOR NEW PICTURE (merged into sound_plan.json as origin v2)
# The v1 cues carry over unchanged (make_plan.py re-homes them); the device cues (cards, numbers, stamps, chalk, glints,
# flashes, rewinds, ring ticks) are generated from the HUD and the transitions. These are the remaining v2 picture beats.
V2_SFX = [
    fx(3.40, 'bare_foot_step', -8, 'mirror', 'hook: her bare foot sets down on the eighth line (inside the glass)'),
    fx(10.60, 'cloth_press', -12, 'close', 'flash-forward RULE 2: fingertips press through the towel', kind='stretch'),
    fx(11.45, 'bell_cracked', -12, 'close', 'flash-forward RULE 5: the real bell struck (cut short by the glitch)', strike='padlock', part='note'),
    fx(11.95, 'tinnitus', -20, 'dry', 'flash-forward RULE 7: the foot hangs over nothing', dur=0.8),
    fx(71.90, 'padlock', -8, 'close', 'Tess hangs the open padlock on Cabin 7\'s hasp'),
    fx(97.60, 'glass_resonance', -16, 'mirror', 'the third call: the glass hums faintly'),
    fx(376.30, 'watch_beep', -10, 'memory', '4:45 AM: the watch alarm beeping (your prank woke him)', n=3),
    fx(377.60, 'glass_tap', -14, 'memory', 'a pale palm settles on the inside of the glass'),
    fx(462.90, 'padlock', -4, 'close', 'Tess yanks the padlock off the hasp', hit=True),
    fx(479.24, 'lipstick_smear', -6, 'close', 'the drawn smile tears open along the drawing (S3a)'),
    fx(479.24, 'sub_drop', -10, 'dry', 'under the split', hit=True),
    fx(499.56, 'sub_drop', -12, 'dry', 'her irises turn red (S3b)', hit=True),
    fx(546.25, 'footsteps_run', -8, 'outside', 'Tess sprinting back across the path', dur=0.5),
    fx(588.45, 'bare_foot_step', -6, 'mirror', 'her bare foot on tread 8 (just before the silence)'),
    fx(677.69, 'glitch', -14, 'dry', 'montage tile cut', dur=0.04, amount=0.4), fx(678.04, 'glitch', -14, 'dry', 'montage tile cut', dur=0.04, amount=0.4),
    fx(678.39, 'glitch', -14, 'dry', 'montage tile cut', dur=0.04, amount=0.4),
    fx(694.30, 'bare_foot_step', -16, 'phone', 'the tiny figure in the phone climbs one step'),
]

# ================================================================ FLOW (owner's v2 verdict + critic round 1, B1-B9)
# The references cut about as often as v2 did; their smoothness comes from staying in one place, a few set-ups on one axis,
# action that continues across cuts and transformations that happen inside the shot. v2 jumped between worlds every 3 s,
# started every shot from rest and never travelled. These groups become ONE continuous move each (make_plan.apply_merges);
# the cuts that stay are motivated (new information, a reaction, a reveal, a deliberate shock). Times are the old shots' t0.
# --- HOOK
MERGE(0.42, 3.28, cam3=[[0.42, 'glass_cu'], [2.1, 'glass_wide'], [3.28, {'view': 'glass_wide', 'dp': [-0.05, -0.12, 0.45]}]],
      glide=[0.5, 0.7, 0.6], frame='the taped kid hand draws steps 6 and 7 on the glass; the camera pulls back to the whole mirror '
      'as the numerals 1-7 pop; below the bottom step the eighth line draws itself (one move)')
MERGE(5.40, 6.62, flat=True, set_=dict(view='through', var='stairs', world='stairs', side='mirror'),
      path=[(5.40, 960, 560, 1.32), (6.05, 960, 545, 1.16), (6.62, 960, 530, 1.07)], glide=[0.7, 0.9, 0.3])
MERGE(6.62, 9.99, frame='inside the glass: the camera cranes down the plum stairs past her climbing silhouette (crown glint, '
      'her hand on the rail) to small Noah13 on his bunk at the bottom, face up, lit (one move)',
      cam3=[[6.62, {'pos': (0.0, 1.75, -0.55), 'look': (0.0, -1.45, 2.1), 'fov': 72}],
            [8.3, {'pos': (0.0, 1.5, -0.15), 'look': (0.0, -1.6, 2.3), 'fov': 70}],
            [9.99, {'pos': (0.0, 1.32, 0.12), 'look': (0.0, -1.75, 2.45), 'fov': 66}]], glide=[0.8, 0.5, 0.6],
      chars=[Q('S0', [960, 820, 520], mode='body', view='front', acts=[A(6.62, 'climb', steps_per_s=0.8), A(7.4, 'slide_rail', dx=60),
],
               w=[[6.62, 0.0, -1.2, 1.4], [9.99, 0.0, -1.0, 1.15]]),
             body('noah13', 960, 860, 140, 'front', 'calm_kid', [A(9.6, 'look_up')], seated=True, w=[0.0, -1.8, 2.6])],
      flow_at=[960, 540])
MERGE(12.79, 16.06)
MERGE(16.06, 19.26, cam3=[[16.06, 'master'], [17.75, {'pos': (2.55, 1.65, 2.9), 'look': (4.45, 1.95, 6.38), 'fov': 56}],
                          [19.26, {'pos': (1.85, 1.05, 4.05), 'look': (1.15, 0.95, 5.35), 'fov': 46}]], glide=[0.45, 0.4, 0.7],
      chars=[body('noah13', 560, 760, 300, 'q_right', 'calm_kid', [A(16.06, 'tie_loop', period=2.4), A(18.32, 'look_up'), A(18.62, 'smile'),
                                                                  A(18.5, 'expr', name='grin_kid')], seated=True)],
      frame='THEIRS master: the camera glides in past the loop clock (6:59:59 snaps back to :40) to Noah13 on his bunk, who looks '
            'up with the gap-tooth smile (one move)')
# --- ARRIVAL
MERGE(19.26, 24.94, flow_at=[960, 620])
MERGE(27.10, 30.0, flow_at=[1250, 500])
MERGE(30.0, 33.74, flat=True, drop=[('tess', 'hands')],
      path=[(30.0, 900, 560, 1.15), (31.55, 920, 600, 1.55), (32.4, 930, 590, 1.5), (33.74, 900, 560, 1.12)], glide=[0.5, 0.5, 0.6])
DROP(39.26)                                  # the same CU of you five times: two stay (33.74, 48.89)
DROP(41.66)                                  # the reverse broke the axis; the follow runs on to the gate
MERGE(40.38, 46.14, flow_at=[960, 560])
DROP(44.22)
MERGE(46.14, 48.89)
DROP(52.94)
# --- PORCH
MERGE(54.46, 57.18, flow_at=[1180, 760])
DROP(59.50)
MERGE(57.18, 64.79, keep=[61.58], flow_at=[1100, 640])
# --- CABIN
MERGE(69.43, 72.31, flow_at=[1400, 600])
MERGE(73.43, 75.91, cam3=[[73.43, {'pos': (4.35, 2.05, 4.95), 'look': (5.4, 2.1, 6.0), 'fov': 52}],
                          [74.6, {'pos': (4.75, 0.8, 4.2), 'look': (5.2, 0.35, 6.0), 'fov': 62}],
                          [75.91, 'under_bunk']], set_=dict(view='under_bunk'), glide=[0.5, 0.5, 0.6],
      frame='the empty NOAH cubby (no sweatshirt); the camera cranes down the bunk to the floor: under it, a towel-wrapped bundle '
            'in the beam; your hand pulls it out (one move)')
MERGE(77.51, 80.07)
MERGE(80.07, 83.58)
MERGE(83.58, 86.46)
# --- STEPS
MERGE(88.70, 91.98, cam3=[[88.70, 'profile'], [91.98, {'view': 'ots_mirror', 'dp': [-0.15, 0.25, -0.35]}]], glide=[0.5, 0.5, 0.7],
      w={'you': [3.25, 0.0, 5.35], 'tess': [1.95, 0.0, 5.05]},
      frame='profile along the back wall: you pull the towel off and the camera dollies round to the whole mirror: seven waxy '
            'red steps, your reflections behind them (one move)')
MERGE(100.70, 105.58)
MERGE(106.86, 109.82, cam3=[[106.86, 'three_q'], [109.82, {'view': 'ots_mirror', 'dp': [0.1, 0.3, -0.45]}]], glide=[0.5, 0.5, 0.7],
      w={'you': [3.15, 0.0, 5.55], 'tess': [1.9, 0.0, 5.0]})
MERGE(112.30, 117.50, cam3=[[112.30, 'profile'], [114.2, {'mview': 'glass_cu', 'dp': [0.35, 0.3, -0.55]}], [117.50, 'three_q']],
      drop=[('tess', 'hands'), ('tess', 'bust')], glide=[0.5, 0.5, 0.7])
MERGE(117.50, 119.90)
# --- RULE 1
DROP(140.55)
MERGE(134.32, 142.56, keep=[135.36], flat=True)
MERGE(148.23, 153.75)
FLAG(155.99, tr='flow', flow=[960, 560])     # through her shoulder and the glass into THEIRS (the glint rides the flow)
MERGE(155.99, 163.05, cam3=[[155.99, 'top_stairs'], [158.9, 'swimsuits'], [163.05, 'door_wash']], glide=[0.5, 0.5, 0.7])
MERGE(163.05, 174.07, cam3=[[163.05, 'floor_prints'], [168.6, {'pos': (2.3, 0.85, 1.95), 'look': (1.1, 0.0, 3.95), 'fov': 66}],
                            [174.07, {'pos': (1.85, 0.6, 3.35), 'look': (0.95, 0.15, 4.95), 'fov': 60}]], glide=[0.45, 0.5, 0.8],
      frame='THEIRS, low at the wash-house door: one track along the wet footprints (bare, sneaker, bare) across the golden '
            'floor to Noah\'s bunk (one move)')
MERGE(174.07, 176.63, cam3=[[174.07, 'ots_mirror'], [176.63, {'view': 'ots_mirror', 'dp': [0.0, 0.35, -0.2], 'dl': [0.1, -0.85, -1.2]}]],
      glide=[0.5, 0.5, 0.6])
MERGE(186.30, 190.06)
DROP(190.06)                                 # memory micro-flips (critic M14): the voicemail carries it
MERGE(191.42, 195.00)
MERGE(197.50, 200.46, accel=[[198.15, 1.12, 0.5]])
# --- RULE 2
MERGE(211.49, 216.77, flow_at=[960, 600])
MERGE(234.80, 237.84)
DROP(242.70)
DROP(243.30)                                 # the 15 / 20 flashes (micro-flips)
MERGE(245.26, 248.22)
MERGE(249.10, 252.30)
MERGE(252.30, 256.87)
DROP(267.36)
DROP(268.58)                                 # the steam wisps carry the smell to the card
MERGE(258.46, 265.52, keep=[263.92], cam3=[[258.46, 'floor_cu'], [262.0, 'doorway'], [265.52, {'view': 'doorway', 'dp': [0.0, 0.0, 0.35]}]],
      set_=dict(view='doorway'), glide=[0.5, 0.5, 0.7])
# --- RULE 3
MERGE(274.32, 278.80)
MERGE(282.56, 286.20, set_=dict(hold='H1'))
MERGE(289.74, 293.10, cam3=[[289.74, {'pos': (3.4, 3.05, 6.32), 'look': (2.0, 1.25, 5.75), 'fov': 70}],
                            [290.9, {'pos': (2.6, 2.45, 6.2), 'look': (1.1, 0.55, 5.35), 'fov': 70}],
                            [291.9, {'pos': (2.15, 1.9, 4.5), 'look': (1.15, 0.45, 5.6), 'fov': 72}],
                            [293.10, {'view': 'master', 'dp': [0.1, -0.1, 1.4]}]], glide=[0.7, 0.4, 0.6],
      set_=dict(set='cabin_dawn', view='master', var='dawn', world='theirs', side='theirs', type='WS'),
      chars=[body('you', 960, 900, 300, 'back', 'tense', [A(289.85, 'stride', t1=292.6, steps_per_s=2.2), A(291.7, 'turn', to=0.5, dur=0.8)],
                  w=[[289.74, 3.0, 1.8, 6.2], [290.05, 2.93, 1.6, 6.0], [291.6, 1.06, 0.2, 5.95], [292.2, 1.05, 0.0, 5.5],
                     [293.10, 1.5, 0.0, 4.95]]),
             body('noah13', 560, 760, 300, 'q_right', 'calm_kid', [A(289.74, 'tie_loop', period=2.4)], seated=True),
             body('tess', 1640, 360, 120, 'front', 'fear', [A(289.74, 'flashlight', aim='stairs')], w=[2.95, 1.8, 6.5])],
      frame='THE CROSSING (one move): behind you from the doorway down the eight treads, the gold room opening below, the camera '
            'swinging out into the THEIRS master as you reach the floor; Tess small in the doorway above; a glint at the threshold')
MERGE(293.10, 300.78, keep=[294.30])
MERGE(308.98, 321.94, keep=[310.50, 317.70])
DROP(315.94)
MERGE(323.24, 326.68)
MERGE(331.80, 338.76, flat=True)
MERGE(338.76, 342.12)
MERGE(345.06, 347.62)
# --- RULE 4
MERGE(353.53, 358.26, cam3=[[353.53, 'master'], [358.26, {'pos': (2.05, 1.45, 2.55), 'look': (1.55, 0.85, 5.6), 'fov': 66}]],
      glide=[0.45, 0.5, 0.8])
DROP(365.14)
MERGE(366.66, 371.14, keep=[368.34])
DROP(391.20)
MERGE(394.48, 397.20)
MERGE(405.98, 411.34, keep=[408.20])
MERGE(418.88, 421.52)
MERGE(424.80, 431.36, glide=[0.4, 0.5, 0.9])
# --- RULE 5
MERGE(449.74, 453.41)
MERGE(453.41, 456.37)
DROP(462.59)
DROP(460.93)                                 # the memory run (458.6) holds to Tess's run
MERGE(461.71, 463.89, flow_at=[1000, 520])
DROP(491.55)
DROP(495.47)
MERGE(487.87, 494.51, keep=[489.87])
MERGE(496.67, 500.03)
MERGE(508.19, 511.47, flow_at=[960, 700])
MERGE(516.62, 519.90)
# --- RULE 6
DROP(549.43)
DROP(552.25)
DROP(553.29)
DROP(555.93)
MERGE(547.43, 562.41, keep=[551.29, 554.33, 559.53], flat=True, set_=dict(view='doorway'), chars_from=557.37,
      drop=[('tess', 'hands'), ('noah13', 'hands'), ('noah_grown', 'hands')], glide=[0.5, 0.5, 0.8],
      path=[(547.43, 960, 560, 1.0), (552.0, 960, 540, 1.06), (557.0, 960, 560, 1.03), (562.41, 960, 540, 1.1)])
MERGE(572.09, 574.49)
DROP(581.93)
MERGE(578.73, 584.41, keep=[580.57])
MERGE(586.28, 587.88, flow_at=[960, 540])
MERGE(602.52, 607.36, cam3=[[602.52, 'pov_down'], [605.21, 'pov_down'],
                            [606.3, {'view': 'pov_down', 'dl': [0.0, 1.35, -0.25], 'fov': 64}],
                            [607.36, {'pos': (0.0, 0.2, 0.82), 'look': (0.0, 0.66, 1.42), 'fov': 54}]], glide=[0.4, 0.6, 0.5],
      set_=dict(hold='H7'), snap=[605.21, 1.08, 0.1], drop_hud=['label'],
      chars=[C('you', [960, 980, 900], 'front', 'neutral', [], mode='feet', pov=True, pin=True),
             Q('S3c', [960, 900, 600], mode='body', view='front', acts=[A(605.17, 'fade_in', dur=0.05), A(606.2, 'grin_widen'),
                                                                       A(606.6, 'reach_shoulder')], w=[0.0, -1.2, 1.4])],
      frame='HOLD H7 (one shot): POV of your boots on a red-edged tread; the next tread down holds HER FOOT (605.21 hit); the '
            'camera tilts up her dress to the S3c face looming over you')
MERGE(607.36, 609.48, cam3=[[607.36, {'pos': (0.12, -1.0, 3.05), 'look': (0.0, 0.45, 0.1), 'fov': 64}],
                            [608.9, {'pos': (0.1, -0.9, 2.85), 'look': (0.0, 0.6, 0.05), 'fov': 62}],
                            [609.48, {'pos': (0.08, -0.75, 2.7), 'look': (0.0, 1.5, 0.1), 'fov': 60}]], glide=[0.5, 1.0, 0.5],
      chars=[body('you', 960, 900, 600, 'back', 'fear', [A(607.4, 'stride', t1=608.95, steps_per_s=1.6)],
                  w=[[607.36, 0.0, -0.4, 0.37], [608.97, 0.0, -0.22, 0.17], [609.48, 0.0, 0.1, 0.0]]),
             C('tess', [960, 380, 170], 'front', 'neutral', [A(608.3, 'reach_grab', foreshortened=True), A(608.97, 'grab_collar'),
                                                           A(609.1, 'yank')], mode='hands', sleeve='orange', w=[0.04, 1.32, 0.12])],
      frame='one low shot from below you on the stairs: the doorway above, Tess\'s orange arm shoots out, grabs your collar and '
            'whips you up; white flash')
MERGE(618.40, 621.25)
MERGE(621.25, 625.53, flat=True, set_=dict(view='through'), path=[(621.25, 960, 560, 1.0), (623.4, 960, 600, 1.08), (625.53, 960, 640, 1.16)])
# --- ENDING
MERGE(629.05, 638.89, flat=True, cam3=[[629.05, 'floor_wide'], [634.0, {'pos': (1.35, 0.72, 1.8), 'look': (2.9, 0.45, 4.3), 'fov': 72}],
                                       [638.89, {'pos': (1.75, 0.86, 1.66), 'look': (2.95, 0.45, 4.3), 'fov': 70}]],
      glide=[0.4, 0.5, 1.0])
MERGE(640.57, 643.37)
MERGE(644.81, 652.39)
MERGE(684.98, 695.62)
# --- continuity pass 2 (validate.py): same-subject cuts on one set-up become one move; the rest are flagged
FLAG(142.56, match_action=True)               # the finger runs on into the click
FLAG(153.75, match_action=True)               # her hand opens on the glass (the same set-up, closer)
FLAG(625.53, match_action=True)               # her foot lifts over the wiped step
MERGE(224.60, 228.00)
MERGE(300.78, 304.66)
MERGE(326.68, 331.80)
MERGE(382.16, 386.64)
MERGE(398.96, 401.02)
MERGE(411.34, 414.30)
MERGE(442.29, 445.17)
MERGE(464.59, 470.51, set_=dict(hold='H2'))
MERGE(519.90, 523.42)
MERGE(587.88, 592.92, set_=dict(hold='H6'))
DROP(566.57)
MERGE(595.56, 599.72)
MERGE(660.39, 664.87, set_=dict(hold='H9'))
MERGE(666.87, 669.75)
MERGE(669.75, 673.06)
MERGE(674.26, 677.34)
MERGE(678.74, 682.18)
# B4: the OTS at 372.5 is over YOUR shoulder (olive, standing) at Noah sitting on his bunk, the stairs behind him (the
# ots_noah view put Noah's back in the foreground while Noah was also the subject)
MERGE(372.50, 374.66, cam3=[[372.50, {'pos': (2.9, 1.5, 2.6), 'look': (1.6, 0.9, 5.4), 'fov': 52}],
                            [374.66, {'pos': (2.82, 1.48, 2.75), 'look': (1.6, 0.9, 5.4), 'fov': 50}]], glide=[1.0, 1.0, 0.3],
      set_=dict(view='bunk_2s', type='OTS'),
      chars=[body('you', 960, 1200, 760, 'back', 'tense', [], w=[2.6, 0.0, 4.0]),
             body('noah13', 1200, 1000, 560, 'q_left', 'calm_kid', [A(373.1, 'look_up')], seated=True)],
      frame='OTS over your shoulder (olive jacket, standing): Noah13 on his bunk looks up at you, the stairs rising behind him')
# B6 / H2: one set-up that sees both the window corner and the bunk: she rises in the corner and glides 1.2 s to Noah's
# side, sits, the mattress dips; the two never overlap (film.py bunk_chart)
MERGE(464.59, 470.51, set_=dict(hold='H2'), glide=[1.0, 1.0, 0.5],
      cam3=[[464.59, {'pos': (3.05, 1.42, 2.0), 'look': (2.3, 0.85, 5.5), 'fov': 74}],
            [470.51, {'pos': (2.8, 1.35, 2.35), 'look': (1.9, 0.8, 5.4), 'fov': 70}]],
      chars=[Q('S2', [1600, 760, 380], mode='body', view='q_left', acts=[A(465.0, 'rise'), A(466.1, 'glide_sit', dur=1.2), A(468.35, 'still')],
               w=[[464.59, 3.95, 0.0, 5.6], [466.1, 3.95, 0.0, 5.6], [467.3, 1.24, 0.0, 4.45], [470.51, 1.24, 0.0, 4.45]]),
             body('noah13', 760, 900, 420, 'q_right', 'calm_kid', [A(464.59, 'tie_loop', period=2.4), A(468.68, 'scoot')], seated=True)],
      frame='HOLD H2 (one set-up): she rises from the window corner and in one smooth 1.2 s glide, with no bob, comes to Noah\'s '
            'side and sits; the mattress dips; he scoots over without looking up')
MERGE(696.74, 698.62, path=[(696.74, 960, 520, 1.5), (698.62, 960, 520, 1.72)], glide=[0.8, 1.0, 0.4])
