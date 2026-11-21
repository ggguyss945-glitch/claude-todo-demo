"""plan/shotlist.py: the director's shot list for "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN".

Read PLAN.md first: it defines the cast, the sets and their views (with the design-space layout each view must keep),
the lighting variants, the acting clips and the HUD devices that these entries name. make_plan.py resolves this table
into plan/shots.json and plan/sound_plan.json; validate.py checks them.

Conventions
- Every shot starts at a cut time built from the timeline (T, Wc, RULE) and ends where the next starts.
- cam() moves: push (2.8 %/s), creep (1 %/s, grief), fast (6 %/s), pull (-3 %/s), reveal (fast pull-out reveal),
  drift (push + 27 design px/s pan), track (60 px/s follow), hand (handheld 15 px/s + 1.5 %/s), crane, tilt (roll), orbit,
  move (explicit x1, y1, z1). x, y = design point at frame centre (depth-1 plane); z = zoom. snap=(t, k) optical punch-in,
  hit=[(t, amp_px)] camera jolt, shake= handheld amplitude override.
- chars: C(who, at, view, expr, acts, mode). at = anchor name of the view, or [x, y_feet, height(, depth)] for bodies,
  [cx, cy, scale] for busts, [x, y, size] for hands. mode body | bust | hands | silhouette | photo.
- STATE(t, ...) changes the running prop state; every shot gets the state at its t0 plus the changes inside it.
"""
from dsl import (S, cam, C, A, fx, M, tag, label, redx, R, t, e, w, T, Wc, LINES, DUR)

STATES = []


def STATE(at, **kw):
    STATES.append((at, kw))


RULE_TEXT = {
    1: "Count the steps with your *finger*.",
    2: "If you see her face, *keep your wishes to yourself*.",
    3: "*Leave somebody* on your side of the glass.",
    4: "Ask what he *wished for*.",
    5: "Ring the *real* bell.",
    6: "Let him go *first*.",
    7: "*Cover* anything else that can *reflect* the stairs.",
}
RULE_LINES = {1: (47, 48), 2: (78, 79), 3: (104, 105), 4: (138, 139), 5: (181, 182), 6: (225, 226), 7: (259, 260)}
RULE_BG = {1: ('cabin_now', 'mirror_ots', 'flash'), 2: ('mirror', 'mirror_cu', 'queen'), 3: ('cabin_now', 'doorway', 'doorway_glow'),
           4: ('cabin_dawn', 'wide', 'dawn'), 5: ('cabin_dawn', 'wide', 'dawn_queen'), 6: ('cabin_dawn', 'doorway_back', 'dawn_break'),
           7: ('cabin_now', 'doorway', 'red')}


def card_times(n):
    li, ti = RULE_LINES[n]
    t0 = round(w(li, 'Rule') - 0.45, 3)
    return t0, round(e(ti) + 0.15, 3)


def RULE(n):
    """Rule card shot: a lipstick-on-glass card (PLAN.md 'Rule cards'). Appears 0.45 s before 'Rule', title +1.0 s,
    statement written word by word in sync with the narration, finger-wipe exit, cut 0.15 s after the sentence."""
    li, ti = RULE_LINES[n]
    t0, t1 = card_times(n)
    words = [[wd, tt] for wd, tt in LINES[ti]['words'] if tt is not None]
    bg = RULE_BG[n]
    hud = [dict(t=t0, type='rule_card', n=n, text=RULE_TEXT[n], title='RULE ' + ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN'][n - 1],
                appear=t0, glitch=[t0, round(t0 + 2 / 60, 3)], title_at=round(t0 + 1.0, 3), words=words,
                wipe_out=round(e(ti) + 0.0, 3), end=t1, steps_progress=n, captions=False)]
    if n <= 2: hud.append(dict(t=round(t0 + 1.2, 3), type='like_sub', hold=round(t1 - t0 - 1.4, 2)))
    sfx = [fx(t0, 'glitch', -4, 'dry', 'card in: 2-frame static', dur=0.12, amount=0.8),
           fx(t0, 'glass_resonance', -2, 'close', 'card lands: the pane rings, the riser peaks here', hit=True),
           fx(round(t0 + 1.0, 3), 'lipstick_draw', -6, 'close', 'title RULE N written in lipstick (2 strokes)', strokes=2),
           fx(round(words[0][1], 3), 'glass_wipe', -14, 'close', 'statement written on (soft finger squeaks per word)', n=len(words), soft=True),
           fx(round(e(ti) - 0.05, 3), 'glass_wipe', -5, 'close', 'finger-wipe exit smear', strokes=1)]
    mus = [M(t0, 'riser', 0.9, 5.0, 'ends ON the card (+13 LU over 5 s, peak at voice level)'), M(t0, 'rule', 0.95, None, 'rule sting'),
           M(round(t0 + 0.6, 3), 'swell', 0.6, 4.5, 'decay under the card')]
    S(t0, 'rule_mirror', 'card', bg[2], 'card', 'CARD',
      'mirror pane card ~35 %% of frame, flashlight-lit silver, over the blurred live set %s/%s' % bg[:2],
      cam('push', x=960, y=540, z=1.0, rate=0.02),
      bg=dict(set=bg[0], view=bg[1], var=bg[2], post=dict(blur=6, dim=0.35)), hud=hud, sfx=sfx, mus=mus, tr='glitch', captions=False,
      energy='card slides up and settles (0.17 s), lipstick title pops, words write on, dust drifts in the flashlight across the pane, '
             'background figures keep moving under the blur, camera pushes 2 %/s')
    return t1


# ---------------------------------------------------------------- shared shorthand
P = lambda **k: cam('push', **k)
CR = lambda **k: cam('creep', **k)
FA = lambda **k: cam('fast', **k)                    # default 8 %/s
PU = lambda **k: cam('pull', **k)
RV = lambda **k: cam('reveal', **k)
DR = lambda **k: cam('drift', **k)
TR = lambda **k: cam('track', **k)
HH = lambda **k: cam('hand', **k)
FLASH = dict(rim='#9fb6ff', rim_a=70, side=1, key=-0.25, flash='tess')          # moon rim + Tess's beam
DAWN = dict(rim='#f3e2c0', rim_a=90, side=-1, key=0.35)                          # pale window key from screen left
RED = dict(rim='#ff4060', rim_a=150, side=-1, key=-0.2)                          # lipstick-red spill from the glass

# =================================================================================================================
# INITIAL PROP STATE (make_plan.py starts from this)
STATE(0.0, steps_drawn=7, steps_smeared=0, eighth='none', mirror='hook_glass', towel='wrapped', flashlight='off', candy='none',
      bell='crate', tape='on', shoe='one_on_lace_loose', phone='tess_pocket', doorway='none', jacket='you', sweatshirt='fits',
      clock='running', sprinkler='off', drop='none', lantern='on', queen='absent')

# ================================================================ HOOK 0 - 19.18 (lines 0-6)
S(0.0, 'mirror', 'mirror_cu', 'flash', 'mirror', 'ECU',
  'glass fills frame, staircase drawn lower-left to upper-right; a small hand with three blue-taped fingers (in shadow) '
  'finishes the top steps in lipstick', P(x=1060, y=420, z=1.05, rate=0.03),
  chars=[C('noah13', [1180, 330, 260], 'front', 'neutral', [A(0.56, 'draw_step', step=2), A(0.88, 'draw_step', step=1),
                                                         A(1.2, 'withdraw')], mode='hands', note='taped hand only, no face')],
  props=dict(steps_drawn='5 -> 7 (drawn on at 0.56 and 0.88)'),
  sfx=[fx(0.56, 'lipstick_draw', -4, 'close', 'stroke step 6'), fx(0.88, 'lipstick_draw', -4, 'close', 'stroke step 7 (top)'),
       fx(0.05, 'ambience_mirror', -6, 'close', 'glass room tone in')],
  mus=[M(0.0, 'drone', 0.55, None, 'D drone with Eb rub fades up from 0'), M(0.3, 'motif', 0.4, 4, 'music-box: the bell motif D-F-E-A, detuned')],
  energy='lipstick tip moving, crumbs falling, flashlight hot-spot sliding 40 px/s across the glass, push 3 %/s')
S(Wc(1, 'and'), 'mirror', 'mirror_cu', 'flash', 'mirror', 'CU', 'whole staircase; below the bottom step a clean thin line draws itself',
  PU(x=880, y=620, z=1.18, rate=-0.03),
  props=dict(eighth='drawing at %.2f (0.6 s, left to right, no hand)' % w(1, 'eighth')),
  hud=[label(w(1, 'eighth') + 0.2, '8TH STEP', [510, 860], dx=-40, dy=-150)],
  sfx=[fx(w(1, 'eighth'), 'lipstick_draw', -8, 'close', 'the 8th line draws itself: thinner, glassy, too clean', clean=True),
       fx(w(1, 'eighth'), 'sub_drop', -8, 'dry', 'soft sub under the line', hit=True)],
  energy='the line drawing itself, slow pull-out 3 %/s, dust in the beam')
STATE(w(1, 'eighth'), eighth='present')
S(Wc(1, 'wipe') - 0.07, 'mirror', 'mirror_cu', 'wipe', 'mirror', 'CU', 'a towel slams across the glass and wipes top-down: red streaks',
  FA(x=960, y=540, z=1.0, rate=0.07, hit=[(3.92, 14)]),
  chars=[C('you', [960, 300, 520], 'front', 'fear', [A(3.92, 'wipe_glass', strokes=2, dir='down')], mode='hands')],
  hud=[tag(3.85, 'WIPE THE GLASS', 960, 120, 'cmd', 1.25)],
  sfx=[fx(3.92, 'impact_hit', 0, 'dry', 'BIGGEST HIT OF THE OPENING (top-3 loudest bed moment)', hit=True, size=1.4),
       fx(3.92, 'braam', -3, 'dry', 'braam under the tag', hit=True, key='d'),
       fx(3.95, 'glass_wipe', -2, 'close', 'towel squeal down the glass', strokes=2),
       fx(3.85, 'whoosh', -6, 'dry', 'tag whoosh in', kind='hard')],
  mus=[M(3.92, 'hit', 1.0), M(3.4, 'silence', 0.0, 0.45, 'bed out 0.45 s before the hit')],
  energy='towel smearing the steps, red streaks running, camera jolt on the hit, fast push 7 %/s')
S(Wc(2, "don't"), 'mirror_world', 'stairs', 'void', 'mirror', 'WS', 'looking DOWN the staircase from the top step into black; '
  'a pale head is rising from far below', P(x=960, y=470, z=1.0, rate=0.05, dy=30),
  chars=[C('queen', [960, 640, 120, 6.0], 'front', 'queen_still', [A(R(0), 'climb', steps_per_s=0.8)], mode='silhouette', stage=0)],
  hud=[tag(5.55, "DON'T WAIT", 960, 120, 'cmd', 1.1), redx(6.05, 960, 600, 160, 0.9)],
  sfx=[fx(5.6, 'ui_pop', -6, 'dry', 'tag pop'), fx(6.05, 'stinger', -6, 'dry', 'red X strokes', hit=True),
       fx(5.9, 'bare_foot_step', -16, 'mirror', 'far below, a step')],
  energy='dolly down the stairs 5 %/s, the figure rising, red X drawing on')
S(Wc(2, 'coming', off=-0.0), 'mirror_world', 'feet', 'void', 'mirror', 'ECU', 'low on the treads: a pale bare foot comes up out of the dark '
  'onto a red-edged step (first tease of the queen)', cam('crane', x=960, y=760, z=1.15, dy=-40, rate=0.03),
  chars=[C('queen', [960, 900, 900], 'front', 'queen_still', [A(7.2, 'step_up', foot='right')], mode='feet', stage=0)],
  sfx=[fx(7.36, 'bare_foot_step', -4, 'mirror', 'wet slap on the tread', hit=True), fx(7.36, 'sub_drop', -10, 'dry', 'low thump under the step')],
  energy='the foot rising and landing, hem of the black dress swaying, crane up 40 px/s')
S(T(3), 'mirror_world', 'stairs', 'void_noah', 'mirror', 'WS', 'far down the staircase a small boy in a green sweatshirt stands '
  'in a patch of pale dawn light, looking up', CR(x=960, y=600, z=1.1, rate=0.02, dy=12),
  chars=[C('noah13', [960, 760, 150, 8.0], 'front', 'calm_kid', [A(9.68, 'look_up')], mode='body')],
  energy='slow creep down, dust motes drifting through the dawn patch, the light breathing')
S(T(4), 'mirror_world', 'stairs', 'void_noah', 'mirror', 'ECU', 'profile of Noah\'s lips in pale light, the gap in his front teeth; '
  'a breath fogs nothing', FA(x=1000, y=560, z=1.2, rate=0.07),
  chars=[C('noah13', [1000, 560, 1.6], 'profile_right', 'calm_kid', [A(10.72, 'talk_silent', dur=1.4)], mode='bust')],
  hud=[tag(10.67, 'LISTEN', 960, 120, 'cmd', 1.2)],
  sfx=[fx(10.67, 'ui_pop', -6, 'dry', 'tag pop', hit=True), fx(10.9, 'tinnitus', -22, 'dry', 'thin whistle tone (his gap-tooth whistle)', dur=1.6)],
  energy='push 4 %/s on the lips, light flickering on the cheek')
S(T(5), 'camp_gate', 'poster', 'moon_flash', 'ours', 'INSERT', 'MISSING poster on the notice board: Noah\'s school photo (gap-tooth grin, '
  'green sweatshirt); a flashlight beam slides across it', CR(x=960, y=470, z=1.05, rate=0.015),
  hud=[], sfx=[fx(T(5) + 0.1, 'ambience_camp_night', -8, 'outside', 'night bed in (crickets, frogs, pines)', dur=7)],
  mus=[M(T(5), 'dip', 0.3, 5.5, 'bed dips under the premise line'), M(T(5) + 0.3, 'motif', 0.45, 5, 'music-box bell motif, slow')],
  energy='the beam sweeping left to right 120 px/s and reaching the photo on "fourteen", paper edges fluttering, slow push 1.5 %/s')
S(Wc(6, 'when'), 'cabin_dawn', 'noah_ms', 'dawn', 'theirs', 'MS', 'Noah at 13 on the bottom bunk at dawn, three-quarter back, one shoe on, '
  'tying the same knot', CR(x=960, y=600, z=1.0, rate=0.012),
  chars=[C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4), A(w(6, 'breakfast'), 'head_lift', amount=0.3)])],
  sfx=[fx(R(0.1), 'ambience_dawn', -10, 'inside', 'dawn chorus loop (identical every 19.48 s)', dur=3.3),
       fx(R(0.3), 'lace_pull', -12, 'close', 'shoelace loop', n=2)],
  energy='hands tying in a loop, curtains perfectly still (wrong), lantern glow breathing, creep 1.2 %/s')

# ================================================================ ARRIVAL 19.18 - 54.34 (lines 7-18)
S(T(7, 0.03), 'camp_gate', 'wide', 'moon', 'ours', 'WS', 'the camp gate at night: arch sign CAMP CEDAR LAKE, chained gate, pines, moon, mist, fireflies; '
  'time card top-left', cam('crane', x=960, y=470, z=1.0, dy=18, rate=0.025),
  hud=[dict(t=w(7, "it's"), type='time_card', icon='clock', day='FRIDAY', time='11:57 PM', sub='CAMP CEDAR LAKE  ·  DEMOLITION TOMORROW',
            flip_at=w(7, '11:57'), hold=2.6, x=110, y=170)],
  sfx=[fx(w(7, "it's"), 'ui_pop', -5, 'dry', 'time card in'), fx(w(7, '11:57'), 'clock_tick', -10, 'dry', 'digits flip', dur=0.6),
       fx(R(0.2), 'owl', -18, 'outside', 'far owl', dist=2)],
  mus=[M(T(7), 'swell', 0.45, 6, 'low strings in under the card')],
  energy='crane down 18 px/s + push, mist bands drifting, fireflies blinking and crossing, pines swaying')
STATE(T(7), clock='running', eighth='none', mirror='not_found', steps_drawn=7, steps_smeared=0, towel='wrapped', queen='absent')   # the hook was a flash-forward: reset to the present
S(T(8), 'camp_path', 'aerial', 'moon', 'ours', 'EWS', 'high over the camp: three cabins, the mess hall, the lake with the moon in it, an excavator parked, '
  'your car\'s headlights at the gate; two tiny figures', RV(x=980, y=560, z=1.25, rate=-0.08),
  energy='pull-out reveal 8 %/s, headlights switching off at 22.6 s, lake shimmer, fireflies')
S(Wc(8, 'where'), 'camp_path', 'cabins_row', 'moon', 'ours', 'MS', 'CABIN 7: number plaque, door with a padlocked hasp, a faded strip of old search tape on the rail',
  P(x=1300, y=500, z=1.05, rate=0.035),
  hud=[label(w(8, 'brother') + 0.1, 'CABIN 7', [1300, 380], dx=150, dy=-80)],
  sfx=[fx(R(0.4), 'gate_chain', -18, 'outside', 'the old search tape flutters (cloth flap)', kind='tape_flutter')],
  energy='push 3.5 %/s, the tape strip fluttering, moths at the door lamp (dead bulb), mist')
S(T(9), 'camp_path', 'cabins_row', 'moon', 'ours', 'WS', 'the excavator bucket in foreground silhouette, the three cabins behind',
  DR(x=900, y=520, z=1.0, dx=30), sfx=[fx(R(0.3), 'excavator_creak', -16, 'outside', 'cooling metal tick of the parked machine')],
  energy='parallax drift: bucket (depth 0.6) slides past the cabins (depth 3), fireflies, mist')
S(Wc(9, 'demolition'), 'camp_gate', 'notice', 'moon_flash', 'ours', 'INSERT', 'NOTICE OF DEMOLITION zip-tied to the fence: CABINS 5 - 7 · SATURDAY 7:00 AM',
  P(x=960, y=520, z=1.02, rate=0.03),
  sfx=[fx(R(0.2), 'gate_chain', -14, 'outside', 'fence rattles in a gust', kind='fence'), fx(R(0.1), 'paper', -14, 'outside', 'sign flapping')],
  energy='flashlight beam crossing the sign, the zip-tied sheet flapping, push 3 %/s')
S(Wc(9, 'last'), 'camp_path', 'cabins_row', 'moon', 'ours', 'WS', 'low angle: three dark cabins in a row under the moon', DR(x=1000, y=560, z=1.02, dx=-30),
  energy='drift left, clouds sliding over the moon, fireflies, grass swaying')
S(T(10), 'camp_gate', 'wide', 'moon_flash', 'ours', 'MS', 'Tess steps into frame and clicks her flashlight on; the beam sweeps to the gate; she lifts the key ring',
  P(x=900, y=560, z=1.15, rate=0.025),
  chars=[C('tess', 'tess_gate', 'q_right', 'brave', [A(w(10, 'tess'), 'flashlight', on=True, aim='gate', sweep=0.6),
                                                     A(w(10, 'keys'), 'hold_up', prop='keys', side=-1), A(R(0.3), 'look', x=1100, y=480)])],
  props=dict(flashlight='tess_on at %.2f' % w(10, 'tess')),
  sfx=[fx(w(10, 'tess'), 'flashlight_click', -6, 'close', 'switch on'), fx(w(10, 'keys'), 'key_in_lock', -8, 'close', 'key ring jingle', jingle=True),
       fx(R(0.1), 'footsteps_gravel', -10, 'outside', 'Tess steps in', n=2)],
  energy='beam sweeping across the gate, keys swinging, Tess turning, push 2.5 %/s')
STATE(w(10, 'tess'), flashlight='tess_on')
S(T(11), 'camp_gate', 'wide', 'moon_flash', 'ours', 'MCU', 'You (first look): olive work jacket, stubble, your dad\'s face; you look past camera at the cabins',
  CR(x=960, y=520, z=1.0, rate=0.012),
  chars=[C('you', [960, 560, 0.9], 'q_left', 'grief', [A(R(0.4), 'look', x=600, y=500), A(R(-0.6), 'blink')], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), energy='fireflies drifting behind in the blur, beam spill moving on the cheek, a blink, creep 1.2 %/s')
S(Wc(12, 'mom'), 'memory', 'dock', 'memory_day', 'memory', 'MS', 'memory: Noah at 13 on the lake dock in the green sweatshirt, grinning (gap teeth), water glitter',
  P(x=960, y=520, z=1.02, rate=0.015), tr='dissolve',
  chars=[C('noah13', [960, 960, 640], 'front', 'calm_kid', [A(R(0.2), 'laugh', dur=1.2), A(R(1.2), 'wave')])],
  sfx=[fx(R(0.1), 'ambience_memory', -12, 'memory', 'summer morning, lake lapping, far kids', dur=2.6)],
  mus=[M(R(0), 'motif', 0.4, 3, 'music-box motif warm')],
  energy='water glitter crawling, sweatshirt drawstrings swinging, laugh, slow push')
S(T(13), 'camp_gate', 'poster', 'moon_flash', 'ours', 'INSERT', 'poster ECU: LAST SEEN WEARING A GREEN SWEATSHIRT', P(x=980, y=720, z=1.35, rate=0.03),
  energy='beam drifting down the text, torn corner flapping, push 3 %/s')
S(T(14), 'camp_path', 'path_track', 'moon_flash', 'ours', 'MS', 'you and Tess walk along the fence toward the gate; you look down at your hands',
  TR(x=960, y=540, z=1.05, dx=55),
  chars=[C('you', [1040, 960, 620], 'profile_right', 'grief', [A(R(0), 'walk', to=1400, surface='gravel'), A(w(14, 'one'), 'head_down', amount=0.5)]),
         C('tess', [780, 960, 590], 'profile_right', 'brave', [A(R(0), 'walk', to=1150, surface='gravel'), A(R(0), 'flashlight', aim='ahead')])],
  sfx=[fx(R(0.0), 'footsteps_gravel', -8, 'outside', 'two walkers on gravel', dur=3.5, n=2)],
  energy='side track 55 px/s, walk cycles, fence posts sliding past in the foreground (depth 0.6), beam bobbing')
S(T(15), 'camp_gate', 'lock_cu', 'moon_flash', 'ours', 'ECU', 'Tess\'s hands at the padlock and chain, flashlight tucked under her arm; your phone buzzes in your pocket',
  P(x=960, y=560, z=1.0, rate=0.035),
  chars=[C('tess', [960, 560, 300], 'front', 'brave', [A(w(15, 'unlocking'), 'unlock', prop='padlock'), A(w(15, 'gate'), 'pull_chain')], mode='hands')],
  sfx=[fx(w(15, 'texts'), 'phone_vibrate', -6, 'close', 'your pocket buzzes', n=2), fx(w(15, 'unlocking'), 'key_in_lock', -3, 'close', 'key in the padlock'),
       fx(w(15, 'gate'), 'padlock', -2, 'close', 'padlock pops open', hit=True), fx(w(15, 'gate') + 0.25, 'gate_chain', -3, 'close', 'chain slides through the bars')],
  energy='hands working the key, chain sliding out, beam wobbling, push 3.5 %/s')
STATE(w(15, 'gate'), phone='tess_pocket')
S(T(16), 'ui', 'text', 'phone', 'ui', 'UI', 'your phone in your hand: MOM thread; bubble "Check the pocket." then typing dots, then the second bubble',
  HH(x=960, y=560, z=1.0, rate=0.015),
  hud=[dict(t=t(16), type='phone', state='message', name='MOM', bubbles=[dict(t=t(16), text='Check the pocket.'),
        dict(t=t(17), text='He always had one of those cinnamon candies in there.', typing_from=e(16) + 0.05)], x=960, y=560, scale=1.0)],
  sfx=[fx(t(16), 'phone_message', -4, 'close', 'message tone'), fx(e(16) + 0.05, 'typing', -16, 'close', 'typing dots (soft)', dur=0.5, cps=6),
       fx(t(17), 'phone_message', -6, 'close', 'second message tone')],
  energy='phone held in hand with handheld drift, bubbles sliding up, typing dots pulsing, the blurred gate behind with the beam moving')
S(Wc(17, 'cinnamon'), 'memory', 'pocket', 'memory_day', 'memory', 'INSERT', 'memory: a kid\'s hand pulls a red cinnamon candy in a twist wrapper out of the green sweatshirt pocket',
  P(x=960, y=560, z=1.05, rate=0.03), tr='dissolve',
  chars=[C('noah13', [960, 620, 360], 'front', 'calm_kid', [A(R(0.2), 'pull_from_pocket', prop='candy_red')], mode='hands')],
  sfx=[fx(R(0.35), 'candy_wrapper', -4, 'memory', 'wrapper crinkle')],
  energy='hand pulling the candy out, cellophane catching light, push 3 %/s')
S(T(18), 'camp_gate', 'wide', 'moon_flash', 'ours', 'CU', 'you reading the phone, its glow under your chin, eyes wet', CR(x=960, y=520, z=1.0, rate=0.01),
  chars=[C('you', [960, 560, 1.0], 'q_left', 'grief', [A(w(18, 'pockets'), 'swallow'), A(R(1.0), 'blink')], mode='bust',
           light=dict(rim='#9fb6ff', rim_a=60, side=1, key=-0.3, under='#bcd2ff'))],
  dof=dict(focus=1.0, dof=6.75), energy='screen glow flickering as the text scrolls, fireflies in the blurred bg, gate swinging open behind, creep 1 %/s')

# ================================================================ PORCH AND BELL 54.34 - 67.49 (lines 19-23)
S(T(19), 'mess_porch', 'wide', 'moon_flash', 'ours', 'WS', 'the mess hall lodge and its porch: screen door, MESS HALL sign, wind chimes; you two come up the steps',
  PU(x=960, y=520, z=1.15, rate=-0.04, dx=-20),
  chars=[C('tess', 'tess_steps', 'back', 'brave', [A(R(0), 'walk', to='porch_mid', surface='porch'), A(R(0), 'flashlight', aim='porch')]),
         C('you', 'you_steps', 'back', 'neutral', [A(R(0.3), 'walk', to='porch_left', surface='porch')])],
  sfx=[fx(R(0.1), 'footsteps_porch', -8, 'outside', 'up the porch steps', n=3, creak=0.6), fx(R(0), 'wind_chimes', -14, 'outside', 'porch chimes', dur=1.6)],
  energy='chimes swinging, beam crawling over the screen door, walkers climbing, drift')
S(T(20), 'mess_porch', 'porch_low', 'moon_flash', 'ours', 'MS', 'low angle on the boards: Tess\'s boot steps over a slatted crate in the foreground',
  P(x=1100, y=700, z=1.1, rate=0.03),
  chars=[C('tess', [1150, 1000, 700], 'profile_left', 'brave', [A(w(20, 'over'), 'step_over', height=0.4)], mode='legs')],
  sfx=[fx(w(20, 'over'), 'footsteps_porch', -4, 'close', 'boot lands on boards', n=1), fx(w(20, 'over') - 0.15, 'crate_creak', -10, 'close', 'crate creaks as the boot clears it')],
  energy='boot passing over the crate close to lens, dust lifting from the slats')
S(Wc(20, 'marked'), 'mess_porch', 'crate_cu', 'moon_flash', 'ours', 'INSERT', 'stencil SAVE FOR THE MUSEUM on the crate; a museum tag on string',
  P(x=960, y=540, z=1.0, rate=0.03), sfx=[fx(R(0.2), 'paper', -16, 'close', 'tag on string flips', dur=0.4)],
  energy='beam sliding across the stencil, the tag swinging, push 3 %/s')
S(T(21), 'mess_porch', 'bell_slats', 'moon_flash', 'ours', 'CU', 'dolly along the slats: the beam finds the brass breakfast bell inside',
  TR(x=760, y=560, z=1.1, dx=70),
  sfx=[fx(w(21, 'breakfast'), 'bell_cracked', -24, 'close', 'the bell murmurs as the crate is nudged (sympathetic ring, no strike)', strike='touch')],
  energy='slats sliding past in the foreground (depth 0.7) with parallax, the bell revealed, brass glints')
STATE(w(21, 'bell'), bell='crate_seen')
S(T(22), 'mess_porch', 'bell_ecu', 'moon_flash', 'ours', 'ECU', 'the crack in the bell\'s rim, lit by the beam', P(x=980, y=600, z=1.2, rate=0.04),
  hud=[label(w(22, 'crack'), 'THE CRACK', [1020, 690], dx=170, dy=-110)],
  sfx=[fx(w(22, 'crack'), 'ui_pop', -9, 'dry', 'label pop')],
  energy='push 4 %/s along the rim, the hot-spot gliding over the brass')
S(Wc(23, 'counselor'), 'memory', 'porch_steps', 'memory_day', 'memory', 'MS', 'memory: a counselor\'s hands drop the bell on the porch boards; '
  'you (10) and Noah (13) watch from the steps', P(x=960, y=600, z=1.05, rate=0.025), tr='dissolve',
  chars=[C('counselor', [1150, 980, 700], 'front', 'shock', [A(w(23, 'dropped') - 0.2, 'drop_prop', prop='bell')], mode='legs'),
         C('you_kid', [640, 1010, 420], 'q_right', 'shock', [A(w(23, 'dropped'), 'flinch')]),
         C('noah13', [820, 1010, 500], 'q_right', 'calm_kid', [A(w(23, 'dropped') + 0.2, 'laugh', dur=0.8)])],
  sfx=[fx(w(23, 'dropped'), 'bell_cracked', -6, 'memory', 'THE REAL BELL SOUND PLANTED: clean note + thin rattle (memory-filtered)', strike='drop', hit=True)],
  energy='bell falling and bouncing, kids flinching and laughing, warm dust in sunlight')

# ================================================================ CARETAKER AND CABIN 67.49 - 88.66 (lines 24-30)
S(T(24), 'camp_path', 'path_track', 'moon_flash', 'ours', 'MCU', 'Tess turns back to you and holds a finger to her lips', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('tess', [960, 560, 0.95], 'q_right', 'tense', [A(w(24, 'finger') - 0.2, 'finger_to_lips', t1=w(24, 'as') + 0.6), A(R(0.1), 'nervous_glance', n=1)], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), sfx=[fx(w(24, 'lips'), 'breath', -12, 'close', 'a held "shh" breath', kind='held', dur=0.6)],
  energy='finger rising to lips, eyes darting to the house, beam swaying low')
S(Wc(24, 'as'), 'caretaker', 'wide', 'tv', 'ours', 'WS', 'the caretaker\'s house across the path, one window lit with TV flicker; '
  'you two pass in the foreground as silhouettes', TR(x=960, y=520, z=1.0, dx=45),
  chars=[C('tess', [700, 1060, 760, 0.6], 'profile_right', 'tense', [A(R(0), 'walk', to=1500, surface='gravel', sneak=True)], mode='silhouette'),
         C('you', [420, 1070, 790, 0.6], 'profile_right', 'tense', [A(R(0), 'walk', to=1250, surface='gravel', sneak=True)], mode='silhouette')],
  sfx=[fx(R(0), 'footsteps_gravel', -14, 'outside', 'sneaking steps', dur=2.0, n=2, soft=True), fx(R(0), 'tv_through_wall', -18, 'outside', 'TV murmur behind glass', dur=2.0)],
  energy='TV flicker blue on the window, curtain sways once at %.2f, silhouettes crossing, track 45 px/s' % w(24, "caretaker's"))
S(T(25), 'cabin_now', 'cabin_door', 'flash', 'ours', 'MS', 'inside Cabin 7: the door creaks open, Tess\'s beam leads in and sweeps the dusty bunks',
  P(x=960, y=520, z=1.0, rate=0.04),
  chars=[C('tess', [520, 1060, 720, 0.8], 'back', 'tense', [A(R(0.1), 'flashlight', aim='sweep', sweep=(300, 1600), dur=1.2)], mode='silhouette')],
  sfx=[fx(R(0.05), 'door_creak', -3, 'inside', 'cabin door', slow=1.2), fx(R(0.1), 'room_tone', -10, 'inside', 'dusty cabin tone in', dur=6)],
  energy='beam sweeping across bunks, dust exploding into the beam, door swinging')
STATE(T(25), mirror='wrapped_under_bunk')
S(Wc(25, 'mirror'), 'cabin_now', 'under_bunk', 'flash', 'ours', 'CU', 'low angle under Noah\'s bunk: a flat shape wrapped in a faded striped towel; your hand slides it out',
  P(x=980, y=740, z=1.05, rate=0.03, dx=-10),
  chars=[C('you', [700, 760, 300], 'front', 'neutral', [A(w(25, 'under'), 'reach', to=(980, 760)), A(w(25, 'bunk') + 0.1, 'slide_out')], mode='hands')],
  sfx=[fx(w(25, 'under') + 0.2, 'mirror_handle', -4, 'close', 'frame scrapes on floorboards', kind='scrape')],
  energy='the bundle sliding toward camera, dust rolling off it, the beam jittering')
S(T(26), 'cabin_now', 'towel_label', 'flash', 'ours', 'INSERT', 'the towel: faded orange-and-white stripes, a laundry tag with NOAH in marker; your thumb rubs it',
  CR(x=960, y=560, z=1.08, rate=0.012),
  chars=[C('you', [980, 640, 360], 'front', 'grief', [A(R(0.2), 'rub_thumb', n=2)], mode='hands')],
  sfx=[fx(R(0.2), 'towel_cloth', -14, 'close', 'thumb on terry cloth', kind='rub')],
  energy='thumb rubbing, cloth fibres catching the beam, creep')
S(T(27), 'memory', 'sprinkler_lawn', 'memory_day', 'memory', 'WS', 'memory: Noah runs through the sprinkler holding the towel out, catching the spray',
  TR(x=900, y=560, z=1.0, dx=70), tr='dissolve',
  chars=[C('noah13', [800, 960, 560], 'profile_right', 'laugh', [A(R(0), 'run', to=1300), A(R(0.4), 'laugh', dur=1.6)])],
  sfx=[fx(R(0.1), 'sprinkler_spit', -8, 'memory', 'sprinkler arcs (memory)', n=3, rhythm='tick'), fx(R(0.5), 'footsteps_gravel', -12, 'memory', 'bare feet on wet grass', dur=1.6, wet=True)],
  energy='spray arcs sweeping, the towel billowing, running, water glitter')
S(T(28), 'memory', 'cabin_morning', 'memory_day', 'memory', 'MS', 'memory: Noah wrings the towel over kid-you asleep on the pillow; you squint awake',
  P(x=960, y=600, z=1.05, rate=0.03),
  chars=[C('noah13', [1150, 980, 640], 'q_left', 'laugh', [A(w(28, 'wring'), 'wring', prop='towel')]),
         C('you_kid', [760, 820, 300], 'profile_right', 'sleep', [A(w(28, 'pillow') + 0.3, 'wake_squint')], mode='lying')],
  sfx=[fx(w(28, 'wring') + 0.1, 'water_drip', -6, 'memory', 'water pours from the twisted towel', kind='pour', dur=1.0), fx(w(28, 'when'), 'bed_creak', -12, 'memory', 'bunk creak as you squirm')],
  energy='water drops falling in sunbeams, the towel twisting, kid squirming')
S(T(29), 'memory', 'bunk_night', 'memory_night', 'memory', 'MS', 'memory, the night before: Noah asleep on his bunk, his wrist with a digital watch hanging off the edge',
  P(x=900, y=620, z=1.05, rate=0.03),
  chars=[C('noah13', 'bunk_sleep', 'front', 'sleep', [A(R(0), 'breathe_sleep')], mode='lying')],
  sfx=[fx(R(0.1), 'ambience_camp_night', -12, 'memory', 'crickets through the window (memory)', dur=2)],
  energy='moths around a lantern, sleeping breath, curtain moving in the night breeze')
S(T(30), 'memory', 'watch_cu', 'memory_night', 'memory', 'ECU', 'kid fingers press the buttons of Noah\'s watch: ALM 6:45 becomes ALM 4:45',
  P(x=960, y=560, z=1.1, rate=0.035),
  chars=[C('you_kid', [960, 640, 300], 'front', 'sly', [A(w(30, 'changing'), 'press_button', n=2), A(w(30, 'alarm'), 'press_button', n=2)], mode='hands')],
  props=dict(watch='ALM 6:45 -> 4:45 at %.2f' % w(30, 'alarm')),
  sfx=[fx(w(30, 'changing'), 'watch_beep', -8, 'memory', 'button chirps', n=2), fx(w(30, 'alarm'), 'watch_beep', -8, 'memory', 'button chirps', n=2)],
  energy='digits flipping, tiny fingers pressing, LCD backlight blinking green')

# ================================================================ STEPS AND THE GAME 88.66 - 120.98 (lines 31-42)
S(T(31), 'cabin_now', 'mirror_ots', 'flash', 'ours', 'OTS', 'present: you peel the towel back; the beam hits the glass: seven red steps',
  PU(x=960, y=520, z=1.2, rate=-0.03),
  chars=[C('you', 'you_mirror', 'back', 'neutral', [A(R(0.0), 'unwrap', prop='towel'), A(w(31, 'seven'), 'freeze', t1=R(-0.1))]),
         C('tess', 'tess_mirror', 'q_left', 'tense', [A(R(0), 'flashlight', aim='mirror')])],
  props=dict(mirror='unwrapped, upright against the back wall', towel='held in your left hand'),
  sfx=[fx(R(0.1), 'towel_cloth', -6, 'close', 'towel peeled off', kind='pull'), fx(w(31, 'seven'), 'glass_resonance', -10, 'close', 'glass hum as the light hits', hit=True)],
  mus=[M(w(31, 'seven'), 'braam', 0.45, None, 'soft low braam on the reveal')],
  energy='towel falling away, beam blooming on the glass, pull-out reveal 3 %/s')
STATE(T(31) + 0.4, mirror='held_upright', towel='held')
S(T(32), 'cabin_now', 'two_shot', 'flash', 'ours', 'MCU', 'Tess remembers: eyes widen, a nervous half-smile, beam under her face', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('tess', [960, 560, 0.95], 'q_left', 'recognise', [A(w(32, 'remembers'), 'expr', name='recognise'), A(w(32, 'game'), 'half_smile')], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), energy='beam flutter on her face, dust in front, push')
S(T(33), 'memory', 'lipstick_game', 'memory_night', 'memory', 'CU', 'memory: kid hands draw a staircase on a mirror with a cherry lipstick, flashlights under chins',
  PU(x=960, y=540, z=1.3, rate=-0.05), tr='dissolve',
  chars=[C('kids', [960, 600, 360], 'front', 'giggle', [A(w(33, 'staircase'), 'draw_step', step='zigzag')], mode='hands')],
  sfx=[fx(w(33, 'staircase'), 'lipstick_draw', -6, 'memory', 'lipstick zigzag', strokes=3), fx(R(0.2), 'kids_far', -14, 'memory', 'giggles under blankets')],
  energy='lipstick moving, flashlight beams wobbling, giggling heads bobbing')
S(T(34), 'memory', 'card_queen', 'memory_night', 'memory', 'INSERT', 'the Queen of Spades playing card propped against the mirror base',
  P(x=960, y=560, z=1.0, rate=0.03),
  sfx=[fx(w(34, 'three') + i * 0.28, 'crowd_whisper', -14, 'memory', 'whispered call %d of 3' % (i + 1), dur=0.3, density=2) for i in range(3)],
  energy='flashlight beam trembling on the card, the card\'s red lips catching light, push')
S(T(35), 'mirror', 'mirror_cu', 'flash', 'mirror', 'CU', 'tilt up the drawn staircase from the bottom step to the top; a faint red glow at the top',
  cam('crane', x=760, y=780, z=1.15, dx=55, dy=-60, rate=0.02),
  sfx=[fx(w(35, 'top'), 'whoosh', -12, 'dry', 'soft rising whoosh to the top step', kind='soft')],
  energy='camera climbing the steps diagonally, the glow pulsing at the top')
S(T(36), 'memory', 'kids_game', 'memory_night', 'memory', 'MS', 'memory: two kids in sleeping bags dare each other; one claps a hand over the other\'s mouth, laughing',
  PU(x=960, y=580, z=1.2, rate=-0.04),
  chars=[C('kids', [960, 900, 520], 'front', 'giggle', [A(w(36, 'dare'), 'dare'), A(w(36, 'twice'), 'hand_over_mouth')])],
  sfx=[fx(w(36, 'twice'), 'kids_far', -12, 'memory', 'muffled laugh', dur=1.0)],
  energy='kids wriggling, flashlight under the chin bobbing, shadows huge on the wall')
S(T(37), 'cabin_now', 'two_shot', 'flash', 'ours', '2S', 'present: you and Tess kneel at the mirror; her weak laugh dies, you do not smile',
  P(x=960, y=560, z=1.05, rate=0.025),
  chars=[C('tess', 'tess_mirror', 'q_left', 'half_smile', [A(w(37, 'joke'), 'laugh_dies')]), C('you', 'you_mirror', 'q_right', 'grief', [A(R(0.5), 'look', x=1200, y=500)])],
  energy='beam swaying, dust, the laugh fading into stillness, push')
S(T(38), 'cabin_now', 'two_shot', 'flash', 'ours', 'MS', 'profile: Tess raises the flashlight onto the glass; glare blooms toward the lens', P(x=1000, y=520, z=1.0, rate=0.03, dx=-15),
  chars=[C('tess', 'tess_mirror', 'profile_right', 'tense', [A(w(38, 'shines'), 'flashlight', aim='mirror', raise_=True)])],
  sfx=[fx(w(38, 'flashlight'), 'cloth_grab', -16, 'close', 'jacket rustle as she raises the light')],
  energy='beam swinging up, flare bloom crossing the lens on "flashlight", dust swirl')
S(T(39), 'cabin_now', 'sill', 'flash', 'ours', 'INSERT', 'Tess sets her phone face up on the dusty windowsill; its black glass catches a tiny red glint (plant)',
  P(x=960, y=600, z=1.05, rate=0.03),
  chars=[C('tess', [900, 560, 320], 'front', 'neutral', [A(w(39, 'phone'), 'set_down', prop='phone', face_up=True)], mode='hands')],
  props=dict(phone='sill_face_up at %.2f (stays there until 674.4)' % w(39, 'phone')),
  sfx=[fx(w(39, 'phone'), 'phone_handle', -6, 'close', 'phone set down on wood', kind='set_down')],
  energy='hand withdrawing, dust puffing off the sill, moonlight shafts, red glint sliding in the phone glass')
STATE(w(39, 'phone'), phone='sill_face_up')
S(T(40), 'mirror', 'mirror_cu', 'flash', 'mirror', 'CU', 'Tess\'s thumb brushes the bottom step', P(x=700, y=760, z=1.2, rate=0.03),
  chars=[C('tess', [760, 800, 340], 'front', 'tense', [A(w(40, 'brushes'), 'smear', step=7, length=0.6)], mode='hands')],
  sfx=[fx(w(40, 'thumb'), 'lipstick_smear', -4, 'close', 'waxy squeak under the thumb')],
  energy='thumb dragging, wax smearing, beam glare moving')
S(T(41), 'cabin_now', 'fingertip', 'flash', 'ours', 'ECU', 'red lipstick crumbs on Tess\'s thumb pad; she rubs them between finger and thumb and they fall glinting',
  CR(x=960, y=540, z=1.1, rate=0.012),
  chars=[C('tess', [960, 600, 420], 'front', 'neutral', [A(w(41, 'crumbs'), 'rub_fingers', n=3)], mode='hands')],
  sfx=[fx(w(41, 'crumbs'), 'lipstick_smear', -16, 'close', 'tiny crumbly rub', kind='crumb')],
  energy='crumbs falling through the beam, fingers rubbing, creep')
S(T(42), 'mirror', 'mirror_cu', 'flash', 'mirror', 'CU', 'a fresh red line draws itself beneath the bottom step: perfectly straight, too clean',
  P(x=620, y=820, z=1.15, rate=0.035),
  props=dict(eighth='redrawn fresh at %.2f (0.6 s, left to right)' % w(42, 'line')),
  hud=[label(w(42, 'appears'), '8TH STEP', [510, 860], dx=-60, dy=-140)],
  sfx=[fx(w(42, 'line'), 'lipstick_draw', -4, 'close', 'the line drawing itself (glassy, clean)', clean=True),
       fx(w(42, 'line'), 'impact_hit', -2, 'dry', 'HIT on the eighth step', hit=True, size=1.1), fx(w(42, 'line'), 'glass_resonance', -6, 'close', 'glass ring tail', hit=True)],
  mus=[M(w(42, 'line') - 1.25, 'silence', 0.0, 1.2, 'bed out under "Then a fresh red line", ends in the hit'), M(w(42, 'line'), 'hit', 0.9)],
  energy='the line drawing on, camera pushing 3.5 %/s and jolting on the hit, dust swirling in the beam')
STATE(w(42, 'line'), eighth='present')

# ================================================================ SEVEN RULES 120.98 - 129.80 (lines 43-46)
S(T(43), 'cabin_now', 'wide', 'flash', 'ours', 'WS', 'fast pull back from the glass to the whole cabin: you and Tess tiny at the mirror; punch-in on "seven"',
  RV(x=1150, y=620, z=1.6, rate=-0.12, snap=(w(43, 'seven'), 1.25)),
  hud=[tag(w(43, 'seven'), '7 RULES', 960, 120, 'white', 1.6)],
  sfx=[fx(w(43, 'seven'), 'impact_hit', -3, 'dry', 'punch-in hit', hit=True, size=1.0), fx(R(0.05), 'whoosh', -8, 'dry', 'pull-back whoosh', kind='soft')],
  mus=[M(w(43, 'seven'), 'hit', 0.8), M(w(43, 'seven') + 0.1, 'riser', 0.5, 7.0, 'long slow rise toward rule 1 begins (peaks on the card)')],
  energy='fast pull-out reveal, punch-in x1.25, the beam swinging as Tess looks round')
S(T(44), 'mirror', 'mirror_cu', 'flash', 'mirror', 'ECU', 'the fourth step from the top, glinting; punch-in on "fourth"', P(x=950, y=540, z=1.4, rate=0.03, snap=(w(44, 'fourth'), 1.25)),
  sfx=[fx(w(44, 'fourth'), 'stinger', -5, 'dry', 'stinger on the punch-in', hit=True)],
  energy='push, punch-in x1.25 on the stinger, wax glint sliding')
S(T(45), 'cabin_dawn', 'knot_cu', 'dawn', 'theirs', 'ECU', 'teaser: a taped hand ties a shoelace in pale dawn light, the knot half tied', P(x=960, y=600, z=1.1, rate=0.025),
  chars=[C('noah13', [960, 640, 400], 'front', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], mode='hands')],
  sfx=[fx(R(0.3), 'lace_pull', -10, 'close', 'lace pull', n=2)], energy='hands looping the lace, a drop falling past in the background')
S(T(46), 'cabin_now', 'floor_end', 'after', 'ours', 'MS', 'teaser: a shadowed man on the cabin floor in a too-small green sweatshirt, cuffs halfway up his arms, hands shaking',
  P(x=1060, y=760, z=1.1, rate=0.035),
  chars=[C('noah_grown', 'noah_floor', 'front', 'shaken', [A(R(0), 'tremble', amount=0.8), A(R(0.6), 'look_at_hands')], light=dict(rim='#9fb6ff', rim_a=90, side=1, key=-0.6), face='hidden')],
  sfx=[fx(R(0.4), 'breath', -12, 'close', 'shaky breathing', kind='nervous', dur=2)],
  energy='hands trembling, beam lying across the floor, dust, push 3.5 %/s')

# ================================================================ RULE 1 129.80 - 203.53 (lines 47-77)
c1 = RULE(1)
STATE(c1, flashlight='tess_on')
S(c1, 'mirror', 'mirror_cu', 'flash', 'mirror', 'ECU', 'your fingertip touches the top step', P(x=1280, y=320, z=1.3, rate=0.03),
  chars=[C('you', [1350, 360, 380], 'front', 'neutral', [A(w(49, 'top'), 'touch_glass', at=(1280, 300))], mode='hands')],
  sfx=[fx(w(49, 'top'), 'glass_tap', -10, 'close', 'fingertip on the wax (soft)')], energy='finger approaching, the beam glare on the glass, push')
S(T(50), 'mirror', 'mirror_cu', 'flash', 'mirror', 'ECU', 'the lipstick smears under your finger', FA(x=1240, y=330, z=1.45, rate=0.08),
  chars=[C('you', [1300, 380, 400], 'front', 'neutral', [A(w(50, 'smears') - 0.2, 'smear', step=1, length=0.5)], mode='hands')],
  props=dict(steps_smeared='0 -> 1'), sfx=[fx(w(50, 'smears') - 0.2, 'lipstick_smear', -2, 'close', 'smear 1')],
  energy='smear dragging, wax ridges, fast push')
STATE(w(50, 'smears'), steps_smeared=1)
S(T(51), 'mirror', 'mirror_cu', 'flash', 'mirror', 'CU', 'side angle: the finger moves down to the next step and the next, smearing', DR(x=1100, y=420, z=1.2, dx=-50, dy=40),
  chars=[C('you', [1200, 420, 360], 'front', 'neutral', [A(w(51, 'next') - 0.2, 'smear', step=2, length=0.35), A(R(-0.35), 'smear', step=3, length=0.3)], mode='hands')],
  props=dict(steps_smeared='1 -> 3'), sfx=[fx(w(51, 'next') - 0.2, 'lipstick_smear', -4, 'close', 'smear 2'), fx(R(-0.35), 'lipstick_smear', -5, 'close', 'smear 3')],
  energy='finger travelling down the staircase, camera following diagonally')
STATE(e(51), steps_smeared=7)
S(T(52), 'cabin_now', 'fingertip', 'flash', 'ours', 'ECU', 'seven little red marks stacked on your fingertip; it trembles; pull back to the hand and the smeared glass behind', PU(x=960, y=540, z=1.4, rate=-0.06),
  chars=[C('you', [960, 620, 440], 'front', 'fear', [A(R(0), 'tremble', amount=0.4)], mode='hands')],
  props=dict(steps_smeared=7, fingertip='seven red marks'), sfx=[fx(R(0.3), 'breath', -14, 'close', 'breath in', kind='held')],
  energy='fingertip trembling, wax glinting, push 3 %/s')
S(T(53), 'mirror', 'mirror_cu', 'flash', 'mirror', 'ECU', 'low on the glass: your finger reaches the eighth line; it does not smear; the nail clicks; punch-in',
  P(x=560, y=850, z=1.35, rate=0.03, snap=(w(53, 'clicks'), 1.3)),
  chars=[C('you', [640, 860, 400], 'front', 'fear', [A(w(53, 'eighth'), 'touch_glass', at=(560, 860)), A(w(53, 'clicks'), 'nail_tap')], mode='hands')],
  hud=[label(w(53, 'clicks') + 0.12, 'CLEAN GLASS', [560, 860], dx=160, dy=-130, hold=0.85)],
  sfx=[fx(w(53, 'clicks'), 'nail_click_glass', 0, 'close', 'THE CLICK: crisp nail on clean glass (reused identically at 690.2)', hit=True),
       fx(w(53, 'clicks'), 'glass_resonance', -8, 'close', 'thin glass ring', hit=True)],
  mus=[M(w(53, 'clicks') - 1.2, 'silence', 0.0, 1.15, 'bed out 1.2 s, ends in the click'), M(w(53, 'clicks'), 'stinger', 0.6)],
  energy='finger sliding down then stopping dead, punch-in x1.3 on the click, the line not smearing (parallax shows it is behind the glass)')
S(T(54), 'cabin_now', 'mirror_ots', 'flash', 'ours', 'OTS', 'you tilt the mirror frame', cam('tilt', x=960, y=520, z=1.1, rate=0.03, roll=-4),
  chars=[C('you', 'you_mirror', 'back', 'fear', [A(w(54, 'tilt'), 'tilt_frame', angle=-12, dur=0.8)])],
  props=dict(mirror='tilted -12 deg'), sfx=[fx(w(54, 'tilt'), 'mirror_handle', -6, 'close', 'wood frame creak as it tilts', kind='creak')],
  energy='mirror rotating, beam reflection swinging across the wall, camera roll -4')
STATE(w(54, 'tilt') + 0.8, mirror='tilted')
S(T(55), 'mirror', 'queen_step_tilt', 'flash', 'mirror', 'CU', 'in the glass the seven steps tilt with the frame, the eighth line stays LEVEL', cam('tilt', x=760, y=760, z=1.2, rate=0.03, roll0=-12, roll=-14),
  energy='the frame and the drawn steps rotated while the 8th line holds level: camera roll keeps going, beam glare sliding')
S(T(56), 'mirror', 'queen_step_tilt', 'queen', 'mirror', 'CU', 'closer: a small black figure stands on the eighth step, perfectly level while everything tilts around her (queen stage 0: back, hair, dress)',
  P(x=575, y=760, z=1.6, rate=0.04),
  chars=[C('queen', [575, 860, 230, 1.04], 'back', 'queen_still', [A(R(0), 'still')], mode='body', stage=0)],
  props=dict(queen='on the eighth step'),
  sfx=[fx(w(56, 'woman'), 'braam', -5, 'dry', 'low braam on the woman', hit=True, key='d'), fx(w(56, 'woman'), 'ambience_mirror', -8, 'mirror', 'glass world tone swells', dur=4)],
  mus=[M(w(56, 'woman'), 'braam', 0.7)],
  energy='push 4 %/s on her, her hair stirring with no wind, the rest of the image still tilted')
STATE(w(56, 'woman'), queen='eighth_step')
S(T(57), 'mirror_world', 'dress', 'void', 'mirror', 'ECU', 'her black satin dress: a lipstick-red glint crawling along the folds', DR(x=960, y=600, z=1.2, dx=-25, dy=20),
  chars=[C('queen', [960, 1500, 1800], 'back', 'queen_still', [A(R(0), 'hem_sway')], mode='body', stage=0)],
  sfx=[fx(R(0.1), 'cloth_press', -16, 'mirror', 'satin rustle (too close)', kind='satin')], energy='red glint crawling, hem swaying with no wind, drift')
S(Wc(57, 'looking'), 'mirror_world', 'stairs', 'void', 'mirror', 'OTS', 'over her shoulder (inside the glass world): she looks down a staircase into nothing',
  CR(x=980, y=560, z=1.05, rate=0.02),
  chars=[C('queen', [1260, 1150, 1100, 0.7], 'back', 'queen_still', [A(R(0), 'still')], mode='silhouette', stage=0)],
  energy='creep down the stairs 2 %/s, pale scratch-lines shimmering on the treads, dust falling into the dark')
S(T(58), 'mirror', 'old_cabin_refl', 'old_cabin', 'mirror', 'WS', 'pull out from her to the whole reflection: the cabin as it was (pale, clean, bunks made) framed by our dark glass',
  RV(x=760, y=760, z=1.9, rate=-0.10),
  sfx=[fx(w(58, 'cabin'), 'whoosh', -12, 'dry', 'reveal pull', kind='soft'), fx(w(58, 'glass'), 'ambience_dawn', -18, 'mirror', 'the old cabin heard through glass (muffled birds)', dur=3)],
  mus=[M(w(58, 'glass'), 'swell', 0.45, 6, 'warm detuned pad: the too-normal world')],
  energy='fast pull-out reveal, palette blooming from dark to pale inside the frame')
S(T(59), 'mirror', 'old_cabin_refl', 'old_cabin', 'mirror', 'CU', 'in the reflection: a row of damp swimsuits on the top-bunk rail, dripping', TR(x=800, y=420, z=1.4, dx=60),
  sfx=[fx(w(59, 'swimsuits') + 0.5, 'water_drip', -12, 'mirror', 'drip (through glass)', n=2), fx(w(59, 'rail'), 'water_drip', -12, 'mirror', 'drip', n=1)],
  energy='track along the rail, drops falling from the suits, suits swaying slightly')
S(T(60), 'mirror', 'old_cabin_refl', 'old_cabin', 'mirror', 'MS', 'in the reflection the cabin door swings in; daylight; no one there', P(x=960, y=480, z=1.3, rate=0.03),
  sfx=[fx(w(60, 'walked'), 'screen_door', -10, 'mirror', 'screen door spring and slap (muffled)')],
  energy='door swinging, light sweeping across the floor, push')
S(T(61), 'mirror', 'old_cabin_floor', 'old_cabin', 'mirror', 'CU', 'low on the reflected floorboards: two sets of wet footprints appear one by one toward the bunk', TR(x=760, y=700, z=1.2, dx=60),
  props=dict(footprints='appearing every 0.42 s from %.2f' % w(61, 'footprints')),
  sfx=[fx(round(w(61, 'footprints') + 0.42 * k, 3), 'wet_footstep', -9, 'mirror', 'print %d' % (k + 1), bare=(k % 2 == 0)) for k in range(4)],
  mus=[M(w(61, 'footprints') - 1.2, 'silence', 0.0, 1.2, 'silence; the first wet print ends it')],
  energy='prints appearing in rhythm with a wet sound each, track follows them')
S(T(62), 'mirror', 'old_cabin_floor', 'old_cabin', 'mirror', 'ECU', 'the bare prints: five toes, wet sheen', P(x=900, y=640, z=1.5, rate=0.03),
  sfx=[fx(w(62, 'bare'), 'wet_footstep', -7, 'mirror', 'bare print', bare=True), fx(w(62, 'feet') + 0.3, 'wet_footstep', -8, 'mirror', 'bare print', bare=True)],
  energy='new prints appearing, water glinting, push')
S(T(63), 'mirror', 'old_cabin_floor', 'old_cabin', 'mirror', 'CU', 'the other trail: a shoe print, then a bare foot, shoe, bare...', TR(x=700, y=680, z=1.3, dx=70),
  sfx=[fx(w(63, 'shoe'), 'wet_footstep', -7, 'mirror', 'shoe print', bare=False), fx(w(63, 'bare'), 'wet_footstep', -7, 'mirror', 'bare print', bare=True),
       fx(w(63, 'foot') + 0.4, 'wet_footstep', -9, 'mirror', 'shoe print', bare=False)],
  energy='alternating prints appearing, track')
S(T(64), 'mirror', 'old_cabin_refl', 'old_cabin', 'mirror', 'MS', 'the trail ends at Noah\'s bunk in the reflection: empty bunk, a dip in the mattress', P(x=1150, y=620, z=1.25, rate=0.03),
  sfx=[fx(w(64, 'bunk'), 'bed_creak', -16, 'mirror', 'the empty bunk creaks')], energy='the last print appearing at the bunk, mattress dipping by itself')
S(T(65), 'cabin_now', 'wide', 'flash_low', 'ours', 'WS', 'our side: Tess angles the flashlight toward the floor; the cone sweeps from the mirror down', PU(x=980, y=600, z=1.25, rate=-0.04, dx=-20),
  chars=[C('tess', 'tess_mirror', 'q_left', 'tense', [A(w(65, 'angles'), 'flashlight', aim='floor', sweep=0.8)]), C('you', 'you_mirror', 'q_right', 'fear', [A(R(0), 'grip_frame')])],
  sfx=[fx(w(65, 'angles'), 'cloth_grab', -16, 'close', 'sleeve rustle')], energy='beam sweeping down, dust, drift')
S(T(66), 'cabin_now', 'dust_floor', 'flash_low', 'ours', 'LOW', 'grazing angle over the floor: dust smooth and unbroken from the door to the bed', TR(x=760, y=640, z=1.15, dx=40),
  energy='beam raking the dust, motes lifting and settling, slow track along the floor (no prints)')
S(T(67), 'mirror_world', 'stairs', 'void', 'mirror', 'WS', 'past the woman down the dark stairs; something pale far below', CR(x=960, y=560, z=1.1, rate=0.02),
  chars=[C('queen', [1240, 1100, 1000, 0.72], 'back', 'queen_still', [A(R(0), 'still')], mode='silhouette', stage=0)],
  mus=[M(e(67) - 1.2, 'silence', 0.0, 1.2, 'bed out before the boy\'s voice')], energy='creep, faint glow breathing far below')
S(T(68), 'mirror_world', 'stairs', 'void_noah', 'mirror', 'CU', 'far below in the dark stairwell a small hand in a green cuff rests on the railing', P(x=900, y=760, z=1.4, rate=0.035),
  chars=[C('noah13', [900, 780, 160], 'front', 'calm_kid', [A(R(0.4), 'tap_rail', n=2)], mode='hands')],
  sfx=[fx(w(68, 'did'), 'sub_drop', -12, 'dry', 'low pressure under the voice', hit=True)], voice_fx='below',
  energy='the small hand tapping the rail, dust falling, push 3.5 %/s')
S(T(69), 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'you: fear eyes, then they soften with recognition', P(x=960, y=520, z=1.05, rate=0.03),
  chars=[C('you', [960, 560, 1.0], 'q_left', 'fear', [A(w(69, 'immediately'), 'expr', name='grief', fade=0.6)], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), energy='eyes swapping from fear discs to wet grief, beam flutter, push')
S(T(70), 'ui', 'voicemail', 'phone', 'ui', 'UI', 'your phone: VOICEMAIL list, entry NOAH · 0:09 · JUL 18 (14 years old)', HH(x=960, y=560, z=1.0, rate=0.015),
  hud=[dict(t=T(70), type='phone', state='voicemail_list', name='NOAH', items=['NOAH  ·  0:09  ·  JUL 18', 'MOM  ·  0:31', 'MOM  ·  1:02'], x=960, y=560)],
  sfx=[fx(w(70, 'voicemail'), 'ui_pop', -10, 'close', 'tap on the entry')], energy='thumb scrolling, list sliding, handheld')
S(Wc(71, 'noah'), 'ui', 'voicemail', 'phone', 'ui', 'UI', 'voicemail playing: waveform panel NOAH, the play head moving', P(x=960, y=540, z=1.0, rate=0.025),
  hud=[dict(t=Wc(71, 'noah'), type='phone', state='voicemail', name='NOAH', timer='0:0%d' % 3, waveform=dict(seed=7, progress='live'), x=960, y=560)],
  sfx=[fx(R(0.1), 'radio_static', -26, 'phone', 'faint phone-line hiss of the old message', dur=2.6, amount=0.2)],
  energy='waveform bars moving, play head sliding, push 2.5 %/s')
S(T(72), 'cabin_now', 'mirror_ots', 'flash', 'ours', 'MCU', 'you close to the glass; the old cabin glows in it', CR(x=980, y=520, z=1.15, rate=0.012),
  chars=[C('you', [800, 600, 0.9], 'q_right', 'grief', [A(R(0.4), 'lean_in', amount=0.3)], mode='bust', light=dict(rim='#e7e5e0', rim_a=80, side=1, key=-0.2))],
  dof=dict(focus=1.0, dof=6.75), energy='pale reflection light shifting on your face, creep')
S(T(73), 'memory', 'grin_ecu', 'memory_day', 'memory', 'ECU', 'memory: Noah\'s grin, the gap in his front teeth, a whistle on the "s"', P(x=960, y=600, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 520, 1.5], 'front', 'grin_kid', [A(w(73, 'whistle'), 'whistle_s')], mode='bust')],
  sfx=[fx(w(73, 'whistle'), 'tinnitus', -24, 'memory', 'tiny whistle tone through the gap', dur=0.5)], energy='grin widening, push 3 %/s, sunlight flicker')
S(T(74), 'cabin_now', 'mirror_ots', 'flash', 'ours', 'OTS', 'you lean toward the glass; your breath fogs a patch', FA(x=960, y=500, z=1.1, rate=0.10),
  chars=[C('you', 'you_mirror', 'back', 'grief', [A(w(74, 'lean'), 'lean_in', amount=0.8, dur=0.6)])],
  props=dict(mirror='fog patch blooms at %.2f' % (w(74, 'closer') + 0.2)), sfx=[fx(w(74, 'closer'), 'breath', -10, 'close', 'breath on glass', kind='held', dur=0.8)],
  energy='camera pushing with your lean 6 %/s, the fog bloom spreading on the glass')
S(T(75), 'mirror', 'queen_step_tilt', 'queen', 'mirror', 'CU', 'queen stage 1: in the glass her head turns too far (130 deg) toward you; one eye catches the beam: pinpoint pupil, red iris',
  FA(x=575, y=680, z=1.9, rate=0.08),
  chars=[C('queen', [575, 860, 230, 1.04], 'back', 'queen_still', [A(w(75, 'turns'), 'head_snap', deg=130, dur=0.18)], mode='body', stage=1)],
  props=dict(queen='head turned to you'),
  sfx=[fx(w(75, 'turns'), 'impact_hit', -1, 'dry', 'HIT on the head turn', hit=True, size=1.2), fx(w(75, 'turns'), 'cloth_press', -10, 'mirror', 'neck creak / satin', kind='creak')],
  mus=[M(w(75, 'turns') - 1.15, 'silence', 0.0, 1.15, 'silence before the turn (REF rule 11)'), M(w(75, 'turns'), 'hit', 1.0)],
  energy='head snapping round on the hit, push 5 %/s, the eye glint flaring')
STATE(w(75, 'turns'), queen='turned_to_you')
S(T(76), 'mirror_world', 'stairs', 'void', 'mirror', 'OTS', 'from behind her again: her face now turned away from the stairs, toward the glass (toward you)', DR(x=980, y=560, z=1.1, dx=-25),
  chars=[C('queen', [1240, 1100, 1000, 0.72], 'q_right', 'queen_still', [A(R(0), 'still')], mode='silhouette', stage=1)],
  sfx=[fx(199.40, 'glitch', -16, 'dry', 'header clock rolls over midnight (tiny glitch)', dur=0.1, amount=0.3)],
  energy='drift, her hair moving with no wind, header clock rolling over 00:00:00 at 199.40')
S(T(77), 'mirror', 'queen_face', 'queen', 'mirror', 'ECU', 'through strands of black hair: one eye locked on the lens (no blink), red lips just visible; punch-in on "listening"',
  P(x=960, y=500, z=1.2, rate=0.03, snap=(w(77, 'listening'), 1.25)),
  chars=[C('queen', [960, 560, 1.4], 'front', 'queen_stare', [A(R(0), 'stare')], mode='bust', stage=1)],
  sfx=[fx(w(77, 'listening'), 'braam', -4, 'dry', 'braam on the punch-in', hit=True, key='d')], mus=[M(w(77, 'listening'), 'braam', 0.8)],
  energy='punch-in x1.25, hair strands drifting over the eye, the eye never moving')

# ================================================================ RULE 2 203.53 - 269.24 (lines 78-103)
c2 = RULE(2)
S(c2, 'cabin_now', 'two_shot', 'flash', 'ours', '2S', 'Tess grabs your shoulder, urgent: put it down', HH(x=960, y=540, z=1.05, rate=0.02),
  chars=[C('tess', 'tess_mirror', 'q_right', 'fear', [A(w(80, 'tells'), 'grab_shoulder', side=-1), A(w(80, 'down'), 'point', side=-1)]),
         C('you', 'you_mirror', 'q_left', 'fear', [A(R(0), 'grip_frame', tremble=0.6)])],
  sfx=[fx(w(80, 'tells'), 'cloth_grab', -8, 'close', 'hand on your jacket')], energy='handheld, Tess shaking you, beam swinging wild')
S(T(81), 'cabin_now', 'hands', 'flash', 'ours', 'ECU', 'your hands on the mirror frame: the fingers will not open; knuckles white', FA(x=960, y=560, z=1.2, rate=0.10),
  chars=[C('you', [960, 600, 420], 'front', 'fear', [A(w(81, 'try'), 'grip_frame', tremble=1.0, fail_open=True)], mode='hands')],
  sfx=[fx(w(81, 'try'), 'mirror_handle', -10, 'close', 'frame creaks in your grip', kind='creak')], energy='fingers straining and trembling, fast push')
S(T(82), 'mirror_world', 'railing', 'void', 'mirror', 'WS', 'in the glass, behind the woman: balusters of a stair railing; a small hand slides through between two of them',
  PU(x=980, y=560, z=1.25, rate=-0.03),
  chars=[C('noah13', [980, 600, 260], 'front', 'calm_kid', [A(w(82, 'hand'), 'reach_through', dir='up')], mode='hands'),
         C('queen', [1500, 1000, 820, 0.8], 'back', 'queen_still', [A(R(0), 'still')], mode='silhouette', stage=1)],
  props=dict(queen='on the step, hand through the railing behind her'),
  sfx=[fx(w(82, 'hand'), 'stinger', -8, 'dry', 'soft stinger on the hand', hit=True)], energy='the hand emerging, pull-out 3 %/s, the queen\'s hem swaying')
S(T(83), 'mirror_world', 'railing', 'void', 'mirror', 'ECU', 'three fingers taped together with blue medical tape', P(x=980, y=580, z=1.6, rate=0.028),
  chars=[C('noah13', [980, 600, 520], 'front', 'calm_kid', [A(R(0.3), 'fingers_flex')], mode='hands')],
  hud=[label(w(83, 'blue'), 'BLUE MEDICAL TAPE', [990, 560], dx=180, dy=-140)], sfx=[fx(w(83, 'blue'), 'ui_pop', -10, 'dry', 'label pop')],
  energy='fingers flexing, tape sheen moving, push')
S(T(84), 'memory', 'polaroid', 'memory_day', 'memory', 'INSERT', 'a faded polaroid: Noah by the family car proudly holding up his taped fingers', P(x=960, y=540, z=1.0, rate=0.025),
  sfx=[fx(R(0.1), 'paper', -14, 'close', 'polaroid edge', dur=0.4)], energy='polaroid drifting and rotating 2 deg, flashlight sweep across its gloss')
S(Wc(84, 'shut'), 'memory', 'polaroid', 'memory_day', 'memory', 'ECU', 'inside the polaroid: the car door beside his hand', P(x=1080, y=520, z=1.6, rate=0.035),
  sfx=[fx(w(84, 'car'), 'car_door_close', -10, 'memory', 'a car door slams (memory, filtered)', hit=True)], energy='push into the photo, a flash of the door swinging closed')
S(T(85), 'mirror_world', 'railing', 'void', 'mirror', 'ECU', 'his thumbnail picks at the edge of the tape', P(x=990, y=580, z=1.8, rate=0.03),
  chars=[C('noah13', [990, 600, 560], 'front', 'calm_kid', [A(w(85, 'picks'), 'peel_tape', n=3)], mode='hands')],
  props=dict(tape='picking'), sfx=[fx(w(85, 'picks') + 0.3 * k, 'tape_peel', -9, 'mirror', 'tape edge pick %d' % (k + 1)) for k in range(3)],
  energy='thumbnail picking in a 0.3 s rhythm, tape edge lifting')
S(T(86), 'memory', 'bench', 'memory_day', 'memory', 'MS', 'memory: Noah on a mess hall bench picking at his tape, looking down, trying to start a sentence', P(x=960, y=560, z=1.05, rate=0.02),
  chars=[C('noah13', [960, 980, 640], 'front', 'shy', [A(R(0), 'peel_tape', n=4), A(R(1.0), 'mouth_open_close')])],
  sfx=[fx(R(0.2), 'kids_far', -18, 'memory', 'mess hall chatter far')], energy='picking, a fly crossing, sun dust, slow push')
S(Wc(87, 'and'), 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'you, tears welling', CR(x=960, y=520, z=1.1, rate=0.01),
  chars=[C('you', [960, 560, 1.05], 'q_left', 'grief', [A(R(0.5), 'tears', amount=0.6)], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  energy='a tear forming and running, beam flicker, creep 1 %/s')
S(T(88), 'cabin_now', 'two_shot', 'flash', 'ours', 'MCU', 'Tess, scared, glancing at the door; the flashlight beam trembles', HH(x=960, y=520, z=1.05, rate=0.02),
  chars=[C('tess', [960, 560, 0.95], 'q_right', 'fear', [A(R(0), 'nervous_glance', n=2), A(R(0), 'tremble', amount=0.5)], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), energy='handheld, beam jitter, eyes darting')
S(T(89), 'cabin_now', 'two_shot', 'flash', 'ours', 'MCU', 'you turn to tell her; your mouth works but nothing comes', P(x=940, y=520, z=1.05, rate=0.025),
  chars=[C('you', [940, 560, 0.95], 'q_right', 'grief', [A(R(0.2), 'talk_silent', dur=1.6)], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  energy='mouth trembling, beam swaying, push')
S(Wc(90, 'was'), 'memory', 'night_window', 'memory_night', 'memory', 'MS', 'memory: Noah at the cabin window at night, moths swarming the lantern; he starts to shut it',
  P(x=960, y=520, z=1.05, rate=0.03), tr='dissolve',
  chars=[C('noah13', [960, 1000, 640], 'back', 'neutral', [A(w(90, 'shut'), 'reach', to=(960, 380)), A(w(91, 'bugs'), 'swat')])],
  sfx=[fx(w(91, 'bugs'), 'moth_flutter', -12, 'memory', 'moths at the lantern', dur=1.2), fx(w(90, 'window'), 'window_slide', -10, 'memory', 'window sash slides down')],
  energy='moths swirling the lantern, window sliding, curtain lifting')
S(T(92), 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'you say it (lip-sync): "I wish I\'d had one more minute with him"; red X over your mouth', P(x=960, y=540, z=1.1, rate=0.025),
  chars=[C('you', [960, 560, 1.05], 'q_right', 'grief', [A(t(92), 'talk', line=92), A(R(-0.5), 'tears', amount=0.8)], mode='bust', light=FLASH)],
  dof=dict(focus=1.0, dof=6.75), hud=[redx(w(92, 'wish'), 960, 760, 130, 1.0), tag(w(92, 'wish') + 0.05, 'KEEP IT TO YOURSELF', 960, 120, 'cmd', 1.2)],
  sfx=[fx(w(92, 'wish'), 'stinger', -6, 'dry', 'red X stroke', hit=True)], energy='mouth talking, tears, red X drawing on, push')
S(T(94), 'cabin_now', 'two_shot', 'flash', 'ours', '2S', 'you looking at Tess; her face falls', P(x=960, y=540, z=1.05, rate=0.02),
  chars=[C('you', 'you_mirror', 'q_right', 'grief', [A(R(0), 'look', x=600, y=500)]), C('tess', 'tess_mirror', 'q_left', 'sad', [A(w(94, 'tess'), 'expr', name='sad')])],
  energy='Tess\'s face falling, beam lowering, push')
S(T(95), 'cabin_now', 'mirror_ots', 'flash', 'ours', 'CU', 'three-quarter profile, the old cabin\'s pale glow behind you in the glass', CR(x=920, y=520, z=1.1, rate=0.012),
  chars=[C('you', [900, 580, 1.0], 'profile_left', 'grief', [A(R(0.4), 'head_down', amount=0.3)], mode='bust', light=dict(rim='#e7e5e0', rim_a=90, side=1, key=-0.3))],
  dof=dict(focus=1.0, dof=6.75), energy='creep, the glass glow shifting behind')
S(T(96), 'mirror', 'mirror_cu', 'queen', 'mirror', 'CU', 'the glass: the small woman on the eighth step, now facing out; pull back until she is tiny in the frame', PU(x=575, y=720, z=1.9, rate=-0.06),
  chars=[C('queen', [575, 860, 230, 1.04], 'front', 'queen_still', [A(R(0), 'still')], mode='body', stage=1)],
  mus=[M(w(97, 'you') - 1.4, 'silence', 0.0, 1.4, 'silence into "You have it"')], energy='push, her hair lifting slowly, glass dust drifting')
S(T(97), 'mirror', 'queen_mouth', 'queen', 'mirror', 'ECU', 'her red lips in the dark glass say "You have it" (first time she speaks): too many small teeth', P(x=960, y=560, z=1.3, rate=0.04),
  chars=[C('queen', [960, 470, 1.8], 'front', 'queen_soft', [A(t(97), 'talk', line=97)], mode='bust', stage=2, crop='mouth')],
  sfx=[fx(w(97, 'you'), 'sub_drop', -2, 'dry', 'HIT: sub boom + glass resonance on her first word', hit=True), fx(w(97, 'you'), 'glass_resonance', -6, 'mirror', 'glass ring', hit=True)],
  voice_fx='queen', mus=[M(w(97, 'you'), 'hit', 0.9)], energy='lips moving, lipstick sheen sliding, push 4 %/s')
S(T(98), 'cabin_now', 'wide', 'flash', 'ours', 'MS', 'handheld: Tess snatches the towel from your hand and throws it over the glass', HH(x=1000, y=560, z=1.15, rate=0.03, shake=22),
  chars=[C('tess', 'tess_mirror', 'q_right', 'fear', [A(w(98, 'snatches'), 'snatch', prop='towel'), A(w(98, 'throws'), 'throw', prop='towel', at='mirror')]),
         C('you', 'you_mirror', 'q_left', 'fear', [A(w(98, 'snatches'), 'flinch')])],
  props=dict(towel='snatched at %.2f, thrown over the mirror at %.2f' % (w(98, 'snatches'), w(98, 'throws'))),
  sfx=[fx(w(98, 'snatches'), 'towel_cloth', -3, 'close', 'snatch', kind='snatch'), fx(w(98, 'throws'), 'towel_cloth', -2, 'close', 'throw / flap', kind='flap'),
       fx(w(98, 'throws'), 'whoosh', -6, 'dry', 'hard whoosh with the throw', kind='hard'), fx(w(98, 'glass'), 'mirror_handle', -8, 'close', 'towel slaps the frame', kind='bump')],
  energy='handheld 22 px/s, towel flying across frame, beam whipping around')
STATE(w(98, 'throws'), towel='over_mirror', mirror='towel_over')
S(T(99), 'cabin_now', 'towel_over', 'flash', 'ours', 'CU', 'the towel draped over the mirror; five long fingertips press out through the cloth', P(x=960, y=520, z=1.1, rate=0.05),
  chars=[C('queen', [960, 520, 380], 'front', 'queen_still', [A(w(99, 'fingers'), 'press_through_cloth', depth=0.7)], mode='hands', stage=2)],
  sfx=[fx(w(99, 'fingers'), 'cloth_press', -2, 'close', 'cloth stretching over fingertips', kind='stretch', hit=True), fx(w(99, 'fingers'), 'stinger', -4, 'dry', 'stinger', hit=True)],
  mus=[M(w(99, 'fingers'), 'stinger', 0.85)], energy='fingertips pushing the terry cloth out toward the lens, push 5 %/s')
S(T(100), 'cabin_now', 'towel_over', 'flash', 'ours', 'MS', 'the towel drops straight down as if the mirror has fallen away', P(x=960, y=560, z=1.0, rate=0.03),
  props=dict(towel='drops at %.2f to the floor' % w(100, 'drops')), mus=[M(w(100, 'drops') - 1.15, 'silence', 0.0, 1.15, 'silence; ends in the drop')],
  sfx=[fx(w(100, 'drops'), 'towel_drop', -3, 'close', 'towel falls straight down, soft thump'), fx(w(100, 'drops'), 'sub_drop', -6, 'dry', 'drop', hit=True)],
  energy='the towel falling in one piece, dust blown up from the floor')
STATE(w(100, 'drops'), towel='floor', mirror='gone', doorway='open')
S(Wc(100, 'as'), 'cabin_now', 'wide', 'doorway_glow', 'ours', 'WS', 'pull back: the towel on the floor, no mirror, warm pale light growing on the wall', RV(x=1180, y=650, z=1.5, rate=-0.08),
  chars=[C('tess', 'tess_mirror', 'q_right', 'shock', [A(R(0), 'step_back')]), C('you', 'you_mirror', 'q_left', 'shock', [A(R(0), 'stand_up')])],
  energy='reveal pull-out, the glow blooming, dust swirling into the new light')
S(T(101), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'MS', 'a narrow doorway in the wall exactly where the mirror stood: pale dawn light pours out onto the dusty floor', RV(x=960, y=520, z=1.4, rate=-0.06),
  sfx=[fx(w(101, 'doorway'), 'braam', -4, 'dry', 'warm dissonant braam on the doorway', hit=True, key='d'), fx(w(101, 'doorway'), 'ambience_dawn', -16, 'outside', 'birds heard through the doorway', dur=8)],
  mus=[M(w(101, 'doorway'), 'braam', 0.8)], energy='pull-out reveal, light rays with dust pouring through the doorway')
S(T(102), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'CU', 'pale haze drifting through the doorway into the dark cabin', P(x=960, y=480, z=1.25, rate=0.025),
  sfx=[fx(w(102, 'kitchen'), 'kitchen_far', -16, 'far', 'distant camp kitchen: clinks, a griddle', dur=3)],
  energy='haze curling through the gap, particles drifting, push')
S(T(103), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'MS', 'through the doorway: a glimpse of the other cabin, pale and clean', P(x=960, y=500, z=1.35, rate=0.015),
  sfx=[fx(w(103, 'coffee'), 'coffee_percolator', -14, 'far', 'percolator bubbling far away', dur=2)], energy='slow push toward the doorway, haze drifting')

# ================================================================ RULE 3 269.24 - 350.38 (lines 104-137)
c3 = RULE(3)
S(c3, 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'MS', 'you squeeze one shoulder into the narrow doorway; the jacket scrapes the frame', TR(x=960, y=520, z=1.2, dx=-40),
  chars=[C('you', 'you_doorway', 'profile_right', 'fear', [A(R(0.3), 'squeeze_through', amount=0.4)])],
  sfx=[fx(w(106, 'shoulders'), 'jacket_cloth', -6, 'close', 'canvas jacket scraping the frame', kind='scrape')], energy='you edging in, light spilling over your shoulder, track')
S(T(107), 'cabin_now', 'sleeve', 'doorway_glow', 'ours', 'ECU', 'Tess\'s hand grabs your jacket sleeve', FA(x=960, y=560, z=1.2, rate=0.10, snap=(w(107, 'catches'), 1.15)),
  chars=[C('tess', [900, 560, 420], 'front', 'fear', [A(w(107, 'catches'), 'grab', what='sleeve')], mode='hands')],
  sfx=[fx(w(107, 'catches'), 'cloth_grab', -2, 'close', 'sleeve grab', hit=True)], energy='hand snapping shut on the canvas, punch-in')
S(T(108), 'cabin_now', 'clock', 'flash', 'ours', 'INSERT', 'the cabin wall clock; the second hand jerks BACKWARD and keeps stepping back', P(x=960, y=540, z=1.0, rate=0.03),
  props=dict(clock='second hand ticks forward, then jerks backward at %.2f' % w(108, 'jerks')),
  sfx=[fx(R(0.1), 'clock_tick', -6, 'inside', 'ticking forward', dur=w(108, 'jerks') - T(108) - 0.1),
       fx(w(108, 'jerks'), 'clock_tick_backward', -2, 'inside', 'TOCK reversed, then reverse ticks', hit=True, n=4)],
  mus=[M(w(108, 'jerks'), 'stinger', 0.6)], energy='second hand moving, then jerking back; header clock runs backward 279.06-281.90')
STATE(w(108, 'jerks'), clock='backward')
S(T(109), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'MS', 'at the edge of the pale doorway a black-dressed figure stands just inside the other cabin, half hidden', CR(x=980, y=500, z=1.25, rate=0.015),
  chars=[C('queen', [1080, 900, 600, 1.6], 'front', 'queen_still', [A(R(0), 'still')], mode='body', stage=2)],
  props=dict(queen='in the doorway (other side)'), mus=[M(T(109) + 0.1, 'silence', 0.0, 1.2, 'silence before the face')],
  energy='haze drifting across her, creep')
STATE(T(109), clock='running', queen='doorway')
S(T(110), 'cabin_dawn', 'queen_face', 'dawn_queen', 'theirs', 'CU', 'FULL CREEPY FACE 1: huge whites, pinpoint pupils, red irises, too-wide toothy grin, lipstick smeared up the cheeks; '
  'head tilts beyond natural', P(x=960, y=500, z=1.0, rate=0.03, shake=4),
  chars=[C('queen', [960, 520, 1.15], 'front', 'queen_grin', [A(t(110), 'talk', line=110), A(w(110, 'both'), 'head_tilt', angle=28, dur=1.2)], mode='bust', stage=3)],
  sfx=[fx(w(110, "there's"), 'stinger', 0, 'dry', 'BIG STINGER: the first full face', hit=True), fx(w(110, "there's"), 'braam', -3, 'dry', 'braam layer', hit=True, key='d')],
  voice_fx='queen', mus=[M(w(110, "there's"), 'stinger', 1.0), M(w(110, "there's") + 0.1, 'pulse_on', 0.4, None, 'slow heartbeat pulse starts')],
  energy='grin talking through teeth, head tilting past natural, eyes locked, slow push with micro handheld')
S(T(111), 'cabin_now', 'doorway', 'doorway_glow', 'ours', '2S', 'over the doorway: you turn back to Tess', P(x=900, y=520, z=1.1, rate=0.025),
  chars=[C('you', 'you_doorway', 'q_left', 'resolve', [A(w(111, 'tess'), 'turn', to=-0.5)]), C('tess', 'tess_doorway', 'q_right', 'fear', [])],
  hud=[tag(w(111, 'stay'), 'STAY', 760, 140, 'cmd', 1.0)], sfx=[fx(w(111, 'stay'), 'ui_pop', -6, 'dry', 'tag pop', hit=True)],
  energy='you turning, Tess clutching the flashlight, haze, push')
S(T(112), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'MCU', 'Tess nods, flashlight steadying; her lips start the count; the counter pill appears: 60', P(x=960, y=520, z=1.1, rate=0.025),
  chars=[C('tess', [960, 560, 0.95], 'q_right', 'resolve', [A(w(112, 'count'), 'nod'), A(w(112, 'sixty'), 'talk_silent', dur=1.0)], mode='bust', light=dict(rim='#e7d9b8', rim_a=110, side=-1, key=-0.1))],
  dof=dict(focus=1.0, dof=6.75), hud=[dict(t=w(112, 'sixty'), type='counter_in', value=60)],
  sfx=[fx(w(112, 'sixty'), 'countdown_tick', -4, 'dry', 'counter appears: 60', hit=True)], energy='nod, flashlight beam settling still, push')
S(T(113), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'POV', 'you step through: the camera passes through the doorway into the light (white flash 3 frames into the next shot)',
  FA(x=960, y=520, z=1.2, rate=0.15),
  sfx=[fx(w(113, 'step'), 'whoosh', -3, 'dry', 'pressure whoosh through the doorway', kind='hard'), fx(w(113, 'through'), 'sub_drop', -6, 'dry', 'ear-pressure drop', hit=True)],
  energy='fast dolly through the doorway 15 %/s, light blooming to white')
STATE(w(113, 'through'), side='theirs')
S(T(114), 'cabin_dawn', 'window', 'dawn', 'theirs', 'MS', 'the other cabin: yellow gingham curtains, perfectly still', DR(x=700, y=420, z=1.05, dx=27), tr='white',
  sfx=[fx(R(0.05), 'ambience_dawn', -8, 'inside', 'dawn bed: birds loop, lantern hum, stillness', dur=4)],
  mus=[M(R(0), 'swell', 0.35, 8, 'too-normal pad: warm, detuned, unpulsed'), M(R(0), 'pulse_off', 0.0)], energy='drift, curtains utterly still, sunlight dust (very slow) only in the window shaft')
S(T(115), 'cabin_dawn', 'window', 'dawn', 'theirs', 'CU', 'an old battery lantern glowing on the windowsill; the camera pushes past it to the window: almost light outside, pale blue going peach behind the pines',
  cam('move', x=700, y=560, z=1.3, x1=820, y1=420, z1=1.5),
  sfx=[fx(w(115, 'lantern'), 'lantern_hum', -14, 'close', 'battery lantern hum', dur=2)], energy='lantern glow pulsing faintly, push past it to the window where the sky brightens and lawn mist drifts')
S(T(117), 'cabin_dawn', 'window_out', 'dawn', 'theirs', 'MS', 'the sprinkler on the lawn comes on, spits twice, dies', P(x=900, y=700, z=1.25, rate=0.03),
  props=dict(sprinkler='on %.2f, spits %.2f / %.2f, dies %.2f' % (w(117, 'on'), w(117, 'spits'), w(117, 'twice'), w(117, 'dies'))),
  sfx=[fx(w(117, 'on'), 'sprinkler_spit', -8, 'outside', 'valve hiss on'), fx(w(117, 'spits'), 'sprinkler_spit', -4, 'outside', 'spit 1 (reused identically at 415.75)', loop_id='A'),
       fx(w(117, 'twice'), 'sprinkler_spit', -4, 'outside', 'spit 2 (reused at 416.23)', loop_id='B'), fx(w(117, 'dies'), 'sprinkler_spit', -12, 'outside', 'gurgle and die', kind='die')],
  energy='two spray arcs sweeping and falling, droplets glittering, then stillness')
S(T(118), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you in the pale light, wonder and grief', CR(x=960, y=520, z=1.05, rate=0.012),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'wonder', [A(R(0.5), 'look', x=600, y=420)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  energy='dawn light warming across your face, creep')
S(T(119), 'cabin_dawn', 'window', 'dawn', 'theirs', 'MS', 'the bottom bunk under the window: a damp patch on the mattress, the window open a crack', P(x=760, y=640, z=1.1, rate=0.028),
  energy='curtain hem lifting once in a draught, push, drip from the frame')
S(T(120), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'MS', 'pull out from one sneaker to Noah sitting on the bunk with one shoe on (13, green sweatshirt, pajama pants)', RV(x=1060, y=880, z=1.9, rate=-0.08),
  chars=[C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  hud=[label(w(120, 'shoe'), 'ONE SHOE', [1080, 920], dx=170, dy=-120)], sfx=[fx(w(120, 'shoe'), 'ui_pop', -10, 'dry', 'label pop'), fx(R(0.3), 'lace_pull', -12, 'close', 'lace', n=2)],
  mus=[M(w(120, 'noah'), 'motif', 0.5, 5, 'music-box motif: Noah')], energy='reveal pull-out, hands tying the loop')
S(T(121), 'cabin_dawn', 'noah_ms', 'dawn', 'theirs', 'MS', 'Noah looks up and says your name (no sound: narrated), like he expected you an hour ago', P(x=960, y=560, z=1.05, rate=0.025),
  chars=[C('noah13', 'noah_bunk', 'front', 'calm_kid', [A(w(121, 'looks'), 'look_up'), A(w(121, 'name') - 0.15, 'talk_silent', dur=0.5), A(w(121, 'expected'), 'smile', amount=0.7)])],
  energy='head lifting, gap-tooth smile, lantern glow on him, push')
S(T(122), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'his smile fades as he gets a good look at you; head tilts', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('noah13', [960, 540, 1.0], 'front', 'puzzled', [A(w(122, 'good'), 'expr', name='puzzled'), A(w(122, 'look'), 'head_tilt', angle=10, dur=0.8)], mode='bust', light=DAWN)],
  dof=dict(focus=1.0, dof=6.75), energy='smile fading, tilt, push')
S(T(123), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'Noah: "Why do you look like Dad?" (lip-sync)', P(x=960, y=520, z=1.15, rate=0.025),
  chars=[C('noah13', [960, 540, 1.05], 'front', 'puzzled', [A(t(123), 'talk', line=123)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  energy='talking, brows working, push')
S(T(124), 'cabin_dawn', 'knot_cu', 'dawn', 'theirs', 'CU', 'he looks down at his shoe; his hands go back to the lace', P(x=960, y=600, z=1.1, rate=0.03),
  chars=[C('noah13', [960, 640, 400], 'front', 'calm_kid', [A(w(124, 'down'), 'tie_loop', period=2.4)], mode='hands')], sfx=[fx(w(124, 'shoe'), 'lace_pull', -10, 'close', 'lace', n=2)],
  energy='the loop starts (exact same cycle every time it is seen)')
S(T(125), 'cabin_dawn', 'noah_ms', 'dawn', 'theirs', 'MS', 'Noah, not looking up: "What are they making for breakfast?" (this exact acting clip is replayed at 419.46)', P(x=960, y=600, z=1.05, rate=0.025),
  chars=[C('noah13', 'noah_bunk', 'front', 'calm_kid', [A(t(125), 'talk', line=125), A(R(0), 'tie_loop', period=2.4)], clip_id='breakfast_A')],
  energy='tying while talking, push')
S(T(126), 'cabin_dawn', 'candy', 'dawn', 'theirs', 'INSERT', 'his taped hand holds out a red cinnamon candy in a clear twist wrapper', P(x=960, y=580, z=1.1, rate=0.03),
  chars=[C('noah13', [900, 600, 420], 'front', 'calm_kid', [A(w(126, 'holds'), 'hold_out', prop='candy_red')], mode='hands')],
  props=dict(candy='held out by Noah'), sfx=[fx(w(126, 'cinnamon'), 'candy_wrapper', -6, 'close', 'wrapper crinkle')], energy='hand extending into frame, wrapper glinting')
STATE(w(126, 'holds'), candy='held_out')
S(T(127), 'cabin_dawn', 'candy', 'dawn', 'theirs', 'ECU', 'your adult hand takes it from his small taped one and closes into a fist around it (the wrapper is warm)', cam('move', x=960, y=560, z=1.3, x1=1060, y1=580, z1=1.4),
  chars=[C('you', [1100, 520, 440], 'front', 'grief', [A(w(127, 'take'), 'take', prop='candy_red'), A(w(128, 'wrapper'), 'fist', slow=True)], mode='hands'),
         C('noah13', [880, 620, 420], 'front', 'calm_kid', [A(w(128, 'the'), 'withdraw')], mode='hands')],
  sfx=[fx(w(127, 'take'), 'candy_wrapper', -6, 'close', 'crinkle as it changes hands'), fx(w(128, 'warm'), 'candy_wrapper', -12, 'close', 'crinkle in the fist')],
  energy='hands meeting, candy passing, his hand withdrawing, your fingers curling slowly; drift-push')
STATE(w(127, 'take'), candy='your_fist')
S(T(129), 'memory', 'dock', 'memory_day', 'memory', 'MS', 'memory: on the dock Noah picks the red ones out of a bag of mixed candies and drops them in kid-you\'s palm', P(x=960, y=560, z=1.05, rate=0.02), tr='dissolve',
  chars=[C('noah13', [1100, 980, 600], 'q_left', 'calm_kid', [A(w(129, 'gave'), 'hold_out', prop='candy_red')]), C('you_kid', [760, 1000, 440], 'q_right', 'happy', [A(w(129, 'red'), 'take', prop='candy_red')])],
  sfx=[fx(w(129, 'gave'), 'candy_wrapper', -10, 'memory', 'bag rustle'), fx(R(0.1), 'ambience_memory', -14, 'memory', 'lake lapping, gulls', dur=3)],
  mus=[M(R(0), 'motif', 0.45, 4, 'music-box motif, tender')], energy='water glitter, hands passing candy, gentle push')
S(T(130), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'present: Noah, a faint smile, looking down at the lace', CR(x=960, y=540, z=1.1, rate=0.01),
  chars=[C('noah13', [960, 560, 1.0], 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  energy='creep, his shoulders moving with the knot')
S(T(131), 'cabin_dawn', 'towel', 'dawn', 'theirs', 'CU', 'a wet towel on the floor under the window; drips tap onto it from the frame', P(x=960, y=620, z=1.05, rate=0.03),
  props=dict(drop='falling drips'), sfx=[fx(w(131, 'taps'), 'water_drip', -6, 'close', 'drip 1'), fx(w(131, 'towel'), 'water_drip', -7, 'close', 'drip 2')],
  energy='drops falling into frame and soaking in, push')
S(T(132), 'cabin_dawn', 'towel', 'dawn', 'theirs', 'ECU', 'a drop comes UP off the towel and hangs in midair, glinting and turning slowly', cam('orbit', x=960, y=520, z=1.3, dx=30, rate=0.02, roll=2),
  props=dict(drop='rises %.2f, hangs from %.2f' % (w(132, 'up'), w(132, 'hangs'))),
  sfx=[fx(w(132, 'up'), 'drop_reverse', -4, 'close', 'reversed drip as it rises', hit=True), fx(w(132, 'hangs'), 'tinnitus', -18, 'dry', 'thin stopped-time tone', dur=3)],
  mus=[M(w(132, 'up'), 'stinger', 0.45)], energy='the drop rising and hanging, slow orbit around it, light refracting through it')
STATE(w(132, 'hangs'), drop='hanging')
S(T(133), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'MS', 'looking back at the doorway: Tess in the dark cabin, frozen, flashlight beam perfectly steady', CR(x=960, y=540, z=1.05, rate=0.01, dx=8),
  chars=[C('tess', 'tess_in_doorway', 'front', 'resolve', [A(R(0), 'freeze', t1=R(-0.01))], light=FLASH)],
  mus=[M(w(133, 'perfectly') - 0.2, 'silence', 0.0, 1.2, 'time stopped: music out, only the thin tone')],
  energy='Tess dead still (subject frozen), camera drifting 1 %/s, dust in the beam is the only motion')
S(T(134), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'ECU', 'the beam crossing the doorway, dust drifting through it', P(x=960, y=470, z=1.6, rate=0.02),
  energy='dust motes drifting through the beam, slow push')
S(T(135), 'cabin_dawn', 'towel', 'dawn', 'theirs', 'ECU', 'over here, the same drop falls again onto the towel (identical sound: the loop)', P(x=960, y=560, z=1.3, rate=0.03),
  props=dict(drop='falls again at %.2f' % w(135, 'falls')),
  sfx=[fx(w(135, 'falls'), 'water_drip', -3, 'close', 'THE SAME drip sample as 332.37 (loop)', hit=True, loop_id='drip')],
  energy='the drop falling and splashing, push')
STATE(w(135, 'falls'), drop='falling')
S(T(136), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'MS', 'in the doorway Tess\'s lips move; the beam stays steady', P(x=960, y=520, z=1.15, rate=0.025),
  chars=[C('tess', 'tess_in_doorway', 'front', 'resolve', [A(w(136, 'calls'), 'talk_silent', dur=0.6)], light=FLASH)], energy='push, dust in the beam')
S(T(137), 'cabin_now', 'doorway', 'doorway_glow', 'ours', 'CU', 'Tess shouts through the doorway: "Forty-five." The counter pulses to 45', P(x=960, y=520, z=1.15, rate=0.04, hit=[(t(137), 8)]),
  chars=[C('tess', [960, 560, 1.0], 'q_right', 'shout', [A(t(137), 'talk', line=137)], mode='bust', light=dict(rim='#e7d9b8', rim_a=110, side=-1, key=-0.1))],
  dof=dict(focus=1.0, dof=6.75), hud=[dict(t=t(137), type='counter_call', value=45)],
  sfx=[fx(t(137), 'countdown_tick', 0, 'dry', 'counter 45 (big tick)', hit=True)], voice_fx='far', energy='shout, counter pulse, camera jolt')

# ================================================================ RULE 4 350.38 - 446.33 (lines 138-180)
c4 = RULE(4)
S(c4, 'cabin_dawn', 'wide', 'dawn', 'theirs', 'MS', 'you take Noah\'s hand and pull him toward the doorway', TR(x=1060, y=600, z=1.1, dx=-60),
  chars=[C('you', [1300, 1000, 680], 'profile_left', 'resolve', [A(w(140, 'take'), 'take_hand'), A(w(140, 'pull'), 'pull_hand', to='doorway')]),
         C('noah13', 'noah_bunk', 'q_right', 'calm_kid', [A(w(140, 'pull'), 'pulled_along', to=820)])],
  sfx=[fx(w(140, 'pull'), 'footsteps_wood_inside', -8, 'inside', 'two pairs of steps (one shoe, one bare)', n=3), fx(w(140, 'take'), 'cloth_grab', -12, 'close', 'hand grab')],
  energy='walking toward the doorway, track left, light swinging')
S(T(141), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'MS', 'at the threshold his hand jerks out of yours', HH(x=960, y=560, z=1.1, rate=0.03),
  chars=[C('noah13', [900, 980, 600], 'profile_right', 'calm_kid', [A(w(141, 'jerks'), 'hand_jerk', dir='back')]), C('you', [1150, 1000, 700], 'profile_left', 'shock', [A(w(141, 'jerks'), 'flinch')])],
  sfx=[fx(w(141, 'jerks'), 'whoosh', -4, 'dry', 'reverse whoosh: the snap back', kind='hard'), fx(w(141, 'jerks'), 'impact_hit', -4, 'dry', 'hit', hit=True)],
  mus=[M(w(141, 'jerks') - 1.2, 'silence', 0.0, 1.2, 'silence into the jerk')],
  energy='hand snapping away, handheld jolt')
S(T(142), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'MS', 'hard jump: Noah is back on the bunk in exactly the same pose and framing as at 305.72', P(x=1060, y=760, z=1.2, rate=0.028),
  chars=[C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4, phase=0)], clip_id='loop_reset')],
  sfx=[fx(R(0.0), 'drop_reverse', -10, 'dry', 'suck-back', hit=True)], energy='the loop pose, hands tying, push')
S(T(143), 'cabin_dawn', 'knot_cu', 'dawn', 'theirs', 'ECU', 'the same knot, half tied', P(x=960, y=620, z=1.2, rate=0.03),
  chars=[C('noah13', [960, 640, 420], 'front', 'calm_kid', [A(R(0), 'tie_loop', period=2.4, phase=0)], mode='hands')],
  hud=[label(w(143, 'knot'), 'SAME KNOT', [960, 660], dx=170, dy=-120)], sfx=[fx(w(143, 'knot'), 'ui_pop', -10, 'dry', 'label'), fx(R(0.2), 'lace_pull', -10, 'close', 'lace', n=2)],
  energy='hands looping, push')
S(T(144), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'MS', 'handheld: you pull again, harder', HH(x=1000, y=600, z=1.15, rate=0.03, shake=20),
  chars=[C('you', [1250, 1000, 700], 'profile_left', 'resolve', [A(w(144, 'pull'), 'pull_hand', force=1.4)]), C('noah13', 'noah_bunk', 'q_right', 'calm_kid', [A(w(144, 'pull'), 'pulled_along')])],
  sfx=[fx(w(144, 'pull'), 'bed_creak', -6, 'close', 'bunk creaks as he is dragged up')], energy='handheld 20 px/s, bodies straining')
S(T(145), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'his face as you pull: strained', HH(x=960, y=540, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 560, 1.0], 'q_right', 'strain', [A(R(0), 'pulled_along')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='handheld, head jerking with the pull')
S(T(146), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'for half a second his face is the grown man\'s (two 2-frame flickers, then held 0.5 s) and back', FA(x=960, y=520, z=1.2, rate=0.08, snap=(w(146, 'looks'), 1.2)),
  chars=[C('noah13', [960, 560, 1.0], 'q_right', 'strain', [A(w(146, 'looks'), 'face_flash', to='noah_grown', dur=0.5, flicker=2)], mode='bust', light=DAWN)],
  dof=dict(focus=1.0, dof=6.75), fx_post=[dict(t=w(146, 'looks'), static=0.6, dur=0.07), dict(t=w(146, 'looks') + 0.5, static=0.4, dur=0.05)],
  sfx=[fx(w(146, 'looks'), 'glitch', -4, 'dry', 'static on the face swap', dur=0.15, amount=0.8), fx(w(146, 'looks'), 'impact_hit', -2, 'dry', 'hit', hit=True)],
  mus=[M(w(146, 'looks'), 'hit', 0.85)], energy='face swap flicker, punch-in, static flash')
S(T(147), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'thirteen again, calm, as if nothing happened', CR(x=960, y=540, z=1.1, rate=0.01),
  chars=[C('noah13', [960, 560, 1.0], 'front', 'calm_kid', [A(R(0.2), 'blink')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='creep, blink')
S(T(148), 'cabin_dawn', 'wide', 'dawn', 'theirs', '2S', 'you sit on the bunk across from him', PU(x=1060, y=640, z=1.25, rate=-0.04),
  chars=[C('you', 'you_bunk', 'q_right', 'grief', [A(w(148, 'sitting'), 'sit', dur=0.6)]), C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  sfx=[fx(w(148, 'sitting'), 'bed_creak', -5, 'close', 'mattress creak as you sit')], energy='sitting down, the mattress dipping, push')
S(T(149), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'Noah: "That I wanted to stay until the breakfast bell," (lip-sync)', P(x=960, y=540, z=1.05, rate=0.025),
  chars=[C('noah13', [960, 560, 1.0], 'q_left', 'calm_kid', [A(t(149), 'talk', line=149)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='talking, push')
S(T(151), 'cabin_dawn', 'noah_ms', 'dawn', 'theirs', 'MS', 'Noah, grinning: "I was gonna run to the bus in my pajamas." Pajama pants visible', P(x=960, y=620, z=1.0, rate=0.025),
  chars=[C('noah13', 'noah_bunk', 'front', 'grin_kid', [A(t(151), 'talk', line=151), A(w(151, 'pajamas'), 'pat_knees')])], energy='talking, patting his pajama knees, push')
S(Wc(152, 'thought'), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', '"I thought it\'d be funny." Gap-tooth grin', P(x=960, y=540, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 560, 1.05], 'front', 'grin_kid', [A(t(152), 'talk', line=152)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='grin, push')
S(T(153), 'cabin_dawn', 'queen_bunk', 'dawn', 'theirs', 'MS', 'the empty space beside Noah on the mattress: it dips by itself, as if someone is sitting there', P(x=1300, y=700, z=1.15, rate=0.03),
  chars=[C('noah13', 'noah_bunk', 'q_right', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  props=dict(mattress='dip pressing down by itself'), sfx=[fx(w(153, 'sitting'), 'bed_creak', -10, 'close', 'creak with no one there')],
  energy='the dip pressing in, push, curtains still')
S(Wc(154, 'because'), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'Noah, worried: he is scared he will miss the bus', CR(x=960, y=540, z=1.1, rate=0.012),
  chars=[C('noah13', [960, 560, 1.0], 'q_left', 'worried', [A(w(154, 'scared'), 'look', x=500, y=380)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  energy='eyes going to the window, creep')
S(T(155), 'cabin_dawn', 'clock', 'dawn', 'theirs', 'INSERT', 'the dawn cabin\'s wall clock at 6:59: the second hand approaches 12 and snaps back to 40', P(x=960, y=540, z=1.0, rate=0.03),
  props=dict(clock_dawn='6:59:50 -> snaps back to 6:59:40 at %.2f' % w(155, 'go')),
  sfx=[fx(R(0.05), 'clock_tick', -8, 'inside', 'ticks', dur=w(155, 'go') - T(155) - 0.1), fx(w(155, 'go'), 'clock_tick_backward', -4, 'inside', 'snap back', hit=True, n=1)],
  energy='second hand ticking then snapping back')
S(T(156), 'cabin_dawn', 'queen_bunk', 'dawn_queen', 'theirs', 'MS', 'at the frame edge, in shadow, a black dress seated beside Noah; a long pale hand rests on the blanket', P(x=1180, y=660, z=1.1, rate=0.025),
  chars=[C('queen', 'queen_bunk', 'q_left', 'queen_soft', [A(R(0), 'still')], mode='body', stage=2, face='hidden'), C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  props=dict(queen='beside Noah (glimpse)'), sfx=[fx(w(156, 'while'), 'crowd_whisper', -18, 'close', 'a whisper under "a little while"', dur=1.0, density=1)],
  mus=[M(w(156, "there's"), 'silence', 0.0, 1.2, 'silence under her promise; only the whisper')],
  energy='the pale light cooling around her, push, Noah tying')
S(T(157), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you watching Noah, asking', CR(x=960, y=520, z=1.05, rate=0.012),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'grief', [A(w(157, 'ask'), 'talk_silent', dur=1.2)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='creep, a slow blink')
S(T(158), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'Noah, plainly: "Since you went to get Mom,"', P(x=960, y=540, z=1.1, rate=0.03),
  chars=[C('noah13', [960, 560, 1.0], 'front', 'calm_kid', [A(t(158), 'talk', line=158)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(w(158, 'mom'), 'sub_drop', -10, 'dry', 'soft low hit on "Mom"', hit=True)], energy='talking, push')
S(T(160), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you: shock (fear eyes)', FA(x=960, y=520, z=1.1, rate=0.08),
  chars=[C('you', [960, 560, 1.0], 'front', 'shock', [A(w(160, 'never'), 'expr', name='shock')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  mus=[M(w(160, 'never') - 0.1, 'silence', 0.0, 1.2, 'silence, ends on the cut into the memory')], energy='eyes snapping wide, fast push')
S(T(161), 'memory', 'cabin_morning', 'memory_morning', 'memory', 'MS', 'memory, the morning he vanished: kid-you wakes in the bottom bunk, light overexposed', P(x=900, y=620, z=1.05, rate=0.025), tr='white',
  chars=[C('you_kid', 'kid_bunk', 'front', 'sleep', [A(w(161, 'woke'), 'wake_up')], mode='lying')],
  sfx=[fx(R(0.05), 'ambience_memory', -10, 'memory', 'morning: birds, far voices', dur=4.5)], mus=[M(R(0), 'swell', 0.4, 8, 'memory pad, bleached')],
  energy='bleached light blooming, kid sitting up, curtains blowing in')
S(T(162), 'memory', 'cabin_morning', 'memory_morning', 'memory', 'INSERT', 'the wet towel on the floor, a puddle around it', P(x=960, y=700, z=1.1, rate=0.03),
  sfx=[fx(R(0.3), 'water_drip', -10, 'memory', 'drip into the puddle')], energy='puddle ripples, push')
S(T(163), 'memory', 'search_pines', 'memory_morning', 'memory', 'WS', 'through the window: counselors in the morning mist calling his name, flashlights in daylight', DR(x=960, y=520, z=1.0, dx=30),
  chars=[C('extras', 'search_line', 'front', 'shout', [A(w(163, 'yelling'), 'call_out')], mode='silhouette')],
  sfx=[fx(w(163, 'yelling'), 'voices_calling_far', -10, 'memory', 'distant voices calling a name (no words intelligible)', dur=2.5)],
  energy='figures moving through mist, flashlight beams waving, drift')
S(T(164), 'memory', 'porch_steps', 'memory_morning', 'memory', 'MS', 'kid-you on the mess hall steps among adult legs; he keeps nodding', P(x=960, y=620, z=1.05, rate=0.025),
  chars=[C('you_kid', [960, 1000, 420], 'front', 'sure', [A(R(0.2), 'nod', n=3)]), C('extras', 'adult_legs', 'front', 'neutral', [A(R(0), 'shift_weight')], mode='legs')],
  sfx=[fx(R(0.2), 'footsteps_porch', -14, 'memory', 'adults shuffling', dur=2.5, n=4)], energy='legs shifting around him, nodding, push')
S(T(165), 'memory', 'porch_steps', 'memory_morning', 'memory', 'CU', 'kid-you, certain: he\'ll be back for breakfast', CR(x=960, y=540, z=1.1, rate=0.012),
  chars=[C('you_kid', [960, 560, 1.0], 'front', 'sure', [A(w(165, 'breakfast'), 'smile', amount=0.4)], mode='bust')], energy='creep, morning light flicker')
S(T(166), 'memory', 'breakfast_table', 'memory_day', 'memory', 'MS', 'memory: Noah grinning over a plate of pancakes in the mess hall', CR(x=960, y=560, z=1.05, rate=0.012),
  chars=[C('noah13', [960, 980, 620], 'front', 'grin_kid', [A(R(0.3), 'eat'), A(R(1.4), 'laugh', dur=0.8)])],
  sfx=[fx(R(0.3), 'kids_far', -16, 'memory', 'mess hall clatter'), fx(R(0.6), 'spoon_drop', -20, 'memory', 'cutlery clink', kind='clink')],
  mus=[M(R(0), 'motif', 0.4, 3, 'music-box motif, warm')], energy='steam rising, fork moving, laugh, creep')
S(T(167), 'cabin_dawn', 'window_out', 'dawn', 'theirs', 'MS', 'present, through the window: the sprinkler spits twice (the same two spits)', P(x=900, y=700, z=1.25, rate=0.03), tr='white',
  sfx=[fx(w(167, 'spits'), 'sprinkler_spit', -4, 'outside', 'SAME spit 1 as 298.87', loop_id='A'), fx(w(167, 'twice'), 'sprinkler_spit', -4, 'outside', 'SAME spit 2 as 299.27', loop_id='B')],
  energy='identical spray arcs (same animation as 297.43)')
S(T(168), 'cabin_dawn', 'knot_cu', 'dawn', 'theirs', 'ECU', 'Noah reaches for his loose shoelace (same motion as 316.52)', P(x=960, y=620, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 640, 420], 'front', 'calm_kid', [A(w(168, 'reaches'), 'tie_loop', period=2.4, phase=0)], mode='hands')], sfx=[fx(w(168, 'shoelace'), 'lace_pull', -10, 'close', 'lace', n=2)],
  energy='hands reaching and looping')
S(T(169), 'cabin_dawn', 'noah_ms', 'dawn', 'theirs', 'MS', 'Noah asks again: "What are they making for breakfast?" (EXACT replay of clip breakfast_A, same framing)', P(x=960, y=600, z=1.05, rate=0.025),
  chars=[C('noah13', 'noah_bunk', 'front', 'calm_kid', [A(t(169), 'talk', line=169), A(R(0), 'tie_loop', period=2.4)], clip_id='breakfast_A')],
  energy='the same animation as 318.36, push')
S(T(171), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you realise; the header clock snaps back to 06:59:40', P(x=960, y=520, z=1.05, rate=0.03),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'dread', [A(w(171, 'asked'), 'expr', name='dread')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  mus=[M(w(171, 'you'), 'silence', 0.0, 1.2, 'silence: the loop sinks in')], energy='face falling, push')
S(T(172), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'WS', 'slow pull out: Noah tiny on the bunk in the pale, still cabin', PU(x=1060, y=700, z=1.35, rate=-0.025),
  chars=[C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])], energy='pull-out, hands tying, dust in the window shaft')
S(T(173), 'cabin_dawn', 'knot_cu', 'dawn', 'theirs', 'ECU', 'the shoe half tied, the loop again', P(x=960, y=620, z=1.15, rate=0.028),
  chars=[C('noah13', [960, 640, 420], 'front', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], mode='hands')], sfx=[fx(R(0.3), 'lace_pull', -12, 'close', 'lace', n=2)],
  energy='looping hands')
S(Wc(173, 'waiting'), 'cabin_dawn', 'noah_cu', 'dawn', 'theirs', 'CU', 'Noah\'s head lifts toward the window: listening for a bell', CR(x=960, y=540, z=1.1, rate=0.012),
  chars=[C('noah13', [960, 560, 1.0], 'q_left', 'listening', [A(w(173, 'hear'), 'look', x=420, y=380)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  energy='head turning slowly, creep')
S(T(174), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you, knowing why', CR(x=960, y=520, z=1.05, rate=0.012),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'grief', [A(R(0.4), 'head_down', amount=0.3)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='creep')
S(T(175), 'memory', 'search_pines', 'memory_morning', 'memory', 'WS', 'memory: the camp director with a clipboard waving people toward the pines', PU(x=960, y=560, z=1.2, rate=-0.05), tr='white',
  chars=[C('extras', 'director', 'front', 'shout', [A(R(0.2), 'wave', n=2)], mode='silhouette')],
  sfx=[fx(R(0.2), 'voices_calling_far', -14, 'memory', 'far calling', dur=1.5)], energy='waving arm, mist, push')
S(T(176), 'memory', 'kitchen_staff', 'memory_morning', 'memory', 'WS', 'kitchen staff in white aprons hurry out of the mess hall into the misty pines', TR(x=900, y=540, z=1.0, dx=60),
  chars=[C('extras', 'kitchen_line', 'profile_right', 'neutral', [A(R(0), 'walk', to=1600, surface='gravel')], mode='silhouette')],
  sfx=[fx(R(0.2), 'screen_door', -12, 'memory', 'screen door slap'), fx(R(0.5), 'footsteps_gravel', -14, 'memory', 'hurrying steps', dur=2.5, n=4)],
  energy='figures crossing frame, aprons flapping, track')
S(T(177), 'memory', 'kitchen', 'memory_morning', 'memory', 'MS', 'the empty kitchen: griddle switched off, batter bowl, the percolator; the bell on its hook, unrung', P(x=960, y=540, z=1.05, rate=0.03),
  sfx=[fx(R(0.2), 'coffee_percolator', -12, 'memory', 'percolator gurgling to a stop', dur=1.2)], energy='steam fading, push')
S(T(178), 'memory', 'buses', 'memory_day', 'memory', 'WS', 'noon: yellow buses at the gate, kids boarding with duffels; kid-you at a window looking back', PU(x=960, y=540, z=1.2, rate=-0.04, dx=-30),
  chars=[C('you_kid', 'bus_window', 'q_right', 'sad', [A(R(0.4), 'hand_on_glass')], mode='bust')],
  sfx=[fx(R(0.1), 'bus_door', -10, 'memory', 'bus door hiss and engine idle', dur=2.5)], energy='kids filing on, bus idling and shaking, drift')
S(T(179), 'memory', 'gate_close', 'memory_day', 'memory', 'MS', 'the gate swings shut, the chain is pulled through, the padlock snaps (dissolve back toward present)', P(x=960, y=600, z=1.05, rate=0.03), tr='dissolve',
  sfx=[fx(w(179, 'last'), 'gate_creak', -6, 'memory', 'gate swings shut'), fx(w(179, 'camp'), 'gate_chain', -6, 'memory', 'chain pulled through'), fx(w(179, 'opened'), 'padlock', -4, 'memory', 'padlock snaps', hit=True)],
  energy='gate swinging, chain rattling, push')
S(T(180), 'memory', 'storage_shed', 'memory_day', 'memory', 'MS', 'the bell lowered into the crate in a storage shed; the lid comes down', P(x=960, y=600, z=1.05, rate=0.03),
  sfx=[fx(w(180, 'bell'), 'bell_cracked', -14, 'memory', 'bell knocks the crate side: faint note + rattle', strike='touch'), fx(w(180, 'storage'), 'crate_creak', -6, 'memory', 'lid thumps down', hit=True)],
  energy='hands lowering the bell, lid closing, dust in the shed light')

# ================================================================ RULE 5 446.33 - 542.03 (lines 181-224)
c5 = RULE(5)
S(c5, 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you shout toward the doorway (mouth only, narrated)', HH(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('you', [960, 560, 1.0], 'profile_left', 'shout', [A(w(183, 'shout'), 'shout_silent', dur=1.2)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  mus=[M(c5, 'pulse_on', 0.5, None, 'urgency pulse in (slow, low)')], energy='handheld, shouting')
S(T(184), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'MS', 'Tess in the doorway hears you; her beam wavers for the first time', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('tess', 'tess_in_doorway', 'front', 'tense', [A(w(184, 'crate'), 'flinch')], light=FLASH)], energy='beam wavering, push')
S(T(185), 'cabin_now', 'cabin_door', 'flash', 'ours', 'MS', 'our side: Tess looks over her shoulder at the open cabin door; moonlit path beyond', PU(x=960, y=520, z=1.2, rate=-0.04),
  chars=[C('tess', [760, 1000, 680], 'back', 'tense', [A(w(185, 'looks'), 'turn', to=1.5, dur=0.5)])], energy='turning, the beam swinging toward the door')
S(T(186), 'camp_path', 'path', 'moon', 'ours', 'WS', 'from the cabin door: the mess hall porch just across the path', P(x=1200, y=520, z=1.0, rate=0.04),
  sfx=[fx(R(0.1), 'ambience_camp_night', -6, 'outside', 'night bed', dur=2)], energy='push 4 %/s, fireflies, mist')
S(T(187), 'memory', 'path_run', 'memory_day', 'memory', 'WS', 'memory: two barefoot kids racing across the path to the porch, splashing a puddle', TR(x=900, y=600, z=1.0, dx=90),
  chars=[C('noah13', [800, 980, 560], 'profile_right', 'laugh', [A(R(0), 'run', to=1500)]), C('you_kid', [600, 990, 420], 'profile_right', 'laugh', [A(R(0), 'run', to=1300)])],
  sfx=[fx(R(0.1), 'footsteps_gravel', -10, 'memory', 'bare feet running', dur=2, n=8, wet=True), fx(R(0.5), 'kids_far', -14, 'memory', 'laugh')],
  energy='running, splashes, fast track 90 px/s')
S(T(188), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you shout "Go," (lip-sync)', FA(x=960, y=520, z=1.15, rate=0.08),
  chars=[C('you', [960, 560, 1.0], 'profile_left', 'shout', [A(t(188), 'talk', line=188)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  hud=[tag(t(188) - 0.02, 'GO', 960, 120, 'cmd', 1.0)], sfx=[fx(t(188), 'ui_pop', -5, 'dry', 'tag', hit=True)], energy='shout, fast push')
S(T(190), 'cabin_dawn', 'doorway_back', 'dawn', 'theirs', 'MS', 'the doorway empty now: no Tess, no beam; her footsteps run away', P(x=960, y=500, z=1.15, rate=0.03),
  props=dict(flashlight='with Tess on the porch'), sfx=[fx(w(190, 'footsteps'), 'footsteps_run', -6, 'far', 'Tess running, receding', dur=1.8, approach=-1)],
  energy='the dark rectangle, dust settling in the space where the beam was')
STATE(w(190, 'footsteps'), flashlight='tess_running')
S(T(191), 'cabin_dawn', 'queen_bunk', 'dawn_queen', 'theirs', 'MS', 'the woman in the black dress sits down on the bunk beside Noah (full figure, human size, hair over her face); the pale light cools around her', RV(x=1300, y=600, z=1.5, rate=-0.08),
  chars=[C('queen', [1420, 960, 760], 'front', 'queen_still', [A(w(191, 'sits'), 'sit_beside', dur=0.5)], mode='body', stage=2, face='hidden'),
         C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  props=dict(queen='sitting beside Noah'), sfx=[fx(w(191, 'sits'), 'bed_creak', -3, 'close', 'mattress takes her weight', hit=True), fx(w(191, 'dress'), 'cloth_press', -10, 'close', 'satin settling', kind='satin')],
  mus=[M(w(191, 'sits') - 1.2, 'silence', 0.0, 1.2, 'silence; ends on her weight in the mattress'), M(w(191, 'sits'), 'braam', 0.6)], energy='her sitting in one smooth inhuman motion, colour draining near her, push')
STATE(w(191, 'sits'), queen='bunk')
S(T(192), 'cabin_dawn', 'queen_bunk', 'dawn_queen', 'theirs', '2S', 'Noah scoots over to make room without looking up', P(x=1250, y=640, z=1.15, rate=0.03),
  chars=[C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(w(192, 'scoots'), 'scoot', dx=-60), A(R(0), 'tie_loop', period=2.4)]), C('queen', 'queen_bunk', 'front', 'queen_still', [A(R(0), 'still')], mode='body', stage=2, face='hidden')],
  sfx=[fx(w(192, 'scoots'), 'bed_creak', -5, 'close', 'scoot creak')], energy='scoot, the queen motionless, push')
S(T(193), 'cabin_dawn', 'knot_cu', 'dawn_queen', 'theirs', 'ECU', 'his hands keep tying (habit)', P(x=960, y=620, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 640, 420], 'front', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)], mode='hands')], energy='hands looping')
S(T(194), 'cabin_dawn', 'queen_bust', 'dawn_queen', 'theirs', 'CU', 'the queen: hair over her face, only the red mouth smiling softly, motherly', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('queen', [960, 540, 1.0], 'front', 'queen_soft', [A(R(0), 'still')], mode='bust', stage=2, face='mouth_only')],
  sfx=[fx(R(0.3), 'crowd_whisper', -20, 'close', 'breathy presence', dur=1.2, density=1)], energy='hair strands lifting, the smile not moving, creep')
S(T(195), 'cabin_dawn', 'mattress_dip', 'dawn_queen', 'theirs', 'INSERT', 'her long pale hand pats the empty space beside Noah (the dip where you used to sit)', P(x=960, y=600, z=1.1, rate=0.03),
  chars=[C('queen', [960, 620, 440], 'front', 'queen_soft', [A(w(195, 'pats'), 'pat', n=2, spacing=0.32)], mode='hands', stage=2)],
  sfx=[fx(w(195, 'pats'), 'bed_creak', -10, 'close', 'pat 1', kind='pat'), fx(w(195, 'pats') + 0.32, 'bed_creak', -10, 'close', 'pat 2', kind='pat')], energy='hand patting, the mattress dipping')
S(T(196), 'cabin_dawn', 'queen_face', 'dawn_queen', 'theirs', 'CU', 'FULL CREEPY FACE 2: "I can put you back the way he remembers you," (lip-sync, Noah blurred beside her)', P(x=960, y=500, z=1.0, rate=0.03, roll=3),
  chars=[C('queen', [960, 520, 1.15], 'front', 'queen_grin', [A(t(196), 'talk', line=196), A(w(196, 'remembers'), 'head_tilt', angle=22, dur=1.0)], mode='bust', stage=3)],
  dof=dict(focus=1.0, dof=6.75), sfx=[fx(w(196, 'i'), 'stinger', -1, 'dry', 'STINGER: full face 2', hit=True)], voice_fx='queen',
  mus=[M(w(196, 'i'), 'stinger', 0.95), M(w(196, 'i'), 'pulse_off', 0.0)], energy='grin talking, slow roll 3 deg, push')
S(T(198), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you catch yourself looking down at the mattress', CR(x=960, y=520, z=1.05, rate=0.01),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'tempted', [A(w(198, 'looking'), 'look', x=900, y=800)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75),
  mus=[M(T(198), 'dip', 0.2, 18, 'temptation: bed drops to about -18 LU, no pulse, music-box only')], energy='eyes drifting down, creep')
S(T(199), 'cabin_dawn', 'mattress_dip', 'dawn', 'theirs', 'INSERT', 'the little dip in the mattress, warm light on it', CR(x=960, y=600, z=1.1, rate=0.01), energy='creep, dust in the warm shaft')
S(T(200), 'memory', 'cabin_morning', 'memory_day', 'memory', 'MS', 'memory: kid-you sitting in that dip pulling on socks; Noah tying his shoes beside you', P(x=960, y=600, z=1.05, rate=0.02), tr='dissolve',
  chars=[C('you_kid', 'kid_sit_dip', 'front', 'happy', [A(R(0.2), 'pull_socks')]), C('noah13', 'noah_bunk', 'q_left', 'calm_kid', [A(R(0), 'tie_loop', period=2.4)])],
  sfx=[fx(R(0.3), 'cloth_grab', -16, 'memory', 'sock pulled on', kind='sock')], mus=[M(R(0), 'motif', 0.4, 3)], energy='socks, laces, warm push')
S(T(201), 'cabin_dawn', 'wide', 'dawn', 'theirs', 'WS', 'the warm quiet cabin: lantern, curtains, the sprinkler idle outside; you small on the bunk edge', PU(x=980, y=560, z=1.2, rate=-0.025, dx=10),
  chars=[C('you', 'you_bunk', 'q_right', 'tempted', [A(w(202, 'understand'), 'head_down', amount=0.2)])], energy='slow pull-out (loneliness), lantern breathing, dust in the window shaft')
S(T(203), 'cabin_dawn', 'mattress_dip', 'dawn', 'theirs', 'INSERT', 'the dip again: red X over the empty space', P(x=960, y=600, z=1.15, rate=0.03),
  hud=[redx(w(203, 'sit'), 960, 600, 180, 1.2), tag(w(203, 'sit') + 0.05, "DON'T SIT DOWN", 960, 120, 'cmd', 1.3)], sfx=[fx(w(203, 'sit'), 'stinger', -6, 'dry', 'red X', hit=True)],
  energy='red X strokes, push')
S(T(204), 'cabin_dawn', 'queen_bunk', 'dawn_queen', 'theirs', 'CU', 'you in tears; the queen soft-focused behind, smiling', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('you', [880, 560, 1.0], 'q_right', 'grief', [A(R(0.3), 'tears', amount=1.0)], mode='bust', light=DAWN), C('queen', [1450, 500, 0.8], 'front', 'queen_soft', [A(R(0), 'still')], mode='bust', stage=2, depth=2.2)],
  dof=dict(focus=1.0, dof=6.75), energy='tears running, her blurred shape not moving, creep')
S(T(205), 'mess_porch', 'porch_run', 'run', 'ours', 'MS', 'our side, the porch at night: Tess at the crate, flashlight swinging, yelling back toward the cabin', HH(x=960, y=560, z=1.05, rate=0.03, shake=20),
  chars=[C('tess', 'tess_crate', 'q_right', 'shout', [A(w(205, 'yells'), 'shout_silent', dur=0.6), A(R(0), 'flashlight', aim='wild')])],
  sfx=[fx(R(0.05), 'ambience_camp_night', -6, 'outside', 'night bed', dur=2), fx(R(0.2), 'breath', -8, 'close', 'Tess panting', kind='panting', dur=1.8)], energy='handheld 20 px/s, beam swinging wildly')
S(T(206), 'mess_porch', 'porch_run', 'run', 'ours', 'CU', 'Tess: "Twenty!" The counter pops to 20', FA(x=960, y=520, z=1.15, rate=0.08, hit=[(t(206), 10)]),
  chars=[C('tess', [960, 560, 1.0], 'front', 'shout', [A(t(206), 'talk', line=206)], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  hud=[dict(t=t(206), type='counter_call', value=20)], sfx=[fx(t(206), 'countdown_tick', 0, 'dry', 'counter 20 (big tick)', hit=True)], voice_fx='far_outside',
  energy='shout, counter pop, camera jolt')
S(T(207), 'cabin_dawn', 'candy', 'dawn_queen', 'theirs', 'INSERT', 'Noah holds out another cinnamon candy', P(x=960, y=580, z=1.1, rate=0.03),
  chars=[C('noah13', [900, 600, 420], 'front', 'calm_kid', [A(w(207, 'holds'), 'hold_out', prop='candy_red')], mode='hands')],
  props=dict(candy='second one offered; first still in your fist'), sfx=[fx(w(207, 'cinnamon'), 'candy_wrapper', -6, 'close', 'crinkle')], energy='hand extending')
S(T(208), 'cabin_dawn', 'candy', 'dawn_queen', 'theirs', 'ECU', 'your fist tightening around the first one', P(x=960, y=560, z=1.2, rate=0.03),
  chars=[C('you', [960, 600, 440], 'front', 'resolve', [A(w(208, 'feel'), 'fist', squeeze=1.0)], mode='hands')], sfx=[fx(w(208, 'fist'), 'candy_wrapper', -8, 'close', 'crushed crinkle')], energy='knuckles whitening')
S(T(209), 'mess_porch', 'porch_run', 'run', 'ours', 'MS', 'Tess winds up and kicks the crate: the first slat cracks', HH(x=1080, y=700, z=1.1, rate=0.03, shake=24),
  chars=[C('tess', 'tess_crate', 'profile_left', 'angry', [A(R(0.1), 'wind_up'), A(w(209, 'kicking'), 'kick')])],
  props=dict(bell='crate broken open at %.2f' % w(209, 'apart')),
  sfx=[fx(w(209, 'kicking'), 'crate_break', -2, 'close', 'kick 1', hit=True), fx(w(209, 'box'), 'crate_break', -2, 'close', 'kick 2'), fx(w(209, 'apart'), 'crate_break', 0, 'close', 'kick 3: slats split', hit=True),
       fx(w(209, 'apart') + 0.3, 'bell_cracked', -14, 'close', 'bell rolls on the boards', strike='roll')],
  energy='kicks, splinters flying across frame, beam strobing, handheld 24 px/s')
STATE(w(209, 'apart'), bell='crate_broken')
S(T(210), 'cabin_dawn', 'window_out', 'dawn', 'theirs', 'WS', 'through the dawn window, far across the old camp: the mess hall bell swings by itself and rings PERFECTLY; pull back from the bell to the window frame', RV(x=1420, y=600, z=2.2, rate=-0.10),
  props=dict(fake_bell='swings at %.2f, no ringer' % w(210, 'bell')),
  sfx=[fx(w(210, 'bell'), 'bell_clean', -2, 'far', 'THE FAKE: one perfect clean note, long beautiful reverb, NO rattle', hit=True)],
  mus=[M(w(210, 'bell') - 0.6, 'silence', 0.0, 0.6, 'clear space for the bell'), M(w(210, 'bell'), 'swell', 0.5, 4)], energy='bell swinging far away, mist, push 3.5 %/s')
STATE(w(210, 'bell'), bell='fake_ringing')
S(T(211), 'cabin_dawn', 'shoe', 'dawn_queen', 'theirs', 'INSERT', 'Noah\'s hand reaches for his other shoe beside the bed', P(x=960, y=640, z=1.1, rate=0.03),
  chars=[C('noah13', [860, 560, 420], 'front', 'calm_kid', [A(w(211, 'reaches'), 'reach', to='shoe')], mode='hands')], props=dict(shoe='reaching_other'),
  sfx=[fx(w(211, 'shoe'), 'cloth_grab', -14, 'close', 'lace touched', kind='lace')], energy='hand reaching down')
S(T(212), 'cabin_dawn', 'wide', 'dawn_queen', 'theirs', 'CU', 'you nearly tell him to hurry: mouth opens', P(x=960, y=520, z=1.05, rate=0.03),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'tempted', [A(w(212, 'tell'), 'mouth_open_close')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='push')
S(T(213), 'memory', 'bell_ecu', 'memory_day', 'memory', 'ECU', 'memory: the crack in the old breakfast bell (callback to 62.76)', P(x=980, y=600, z=1.25, rate=0.04), tr='dissolve',
  energy='sunlight gliding over the brass, push 4 %/s')
S(T(214), 'memory', 'bell_ring_porch', 'memory_day', 'memory', 'MS', 'memory: a counselor rings the bell on the porch in the morning, rope swinging', P(x=960, y=540, z=1.05, rate=0.03),
  chars=[C('counselor', [1100, 980, 680], 'front', 'neutral', [A(w(214, 'rang'), 'ring_bell')])], energy='rope swinging, bell swinging, push')
S(T(215), 'memory', 'bell_ecu', 'memory_day', 'memory', 'ECU', 'the bell vibrating on a clean note', P(x=960, y=560, z=1.3, rate=0.03),
  sfx=[fx(w(215, 'clean'), 'bell_cracked', -8, 'memory', 'the clean note only (first half of the real bell)', part='note')], energy='rim vibrating, push')
S(Wc(216, 'then'), 'memory', 'bell_ecu', 'memory_day', 'memory', 'ECU', 'slow-motion: the crack rattling', P(x=1020, y=640, z=1.6, rate=0.03),
  sfx=[fx(w(216, 'rattle'), 'bell_cracked', -6, 'memory', 'the thin rattle (second half)', part='rattle')], energy='the crack edges buzzing, push')
S(Wc(216, 'somebody'), 'memory', 'breakfast_table', 'memory_day', 'memory', 'INSERT', 'a spoon dropped on a mess hall table, bouncing', P(x=960, y=600, z=1.2, rate=0.03),
  sfx=[fx(w(216, 'dropped') + 0.15, 'spoon_drop', -4, 'memory', 'spoon clatter')], energy='spoon falling and bouncing')
S(T(217), 'cabin_dawn', 'window_out', 'dawn', 'theirs', 'MS', 'the fake bell still swinging, ringing perfectly; red X over it', P(x=1420, y=600, z=1.6, rate=0.03),
  hud=[redx(w(217, 'perfect'), 960, 520, 200, 1.1), tag(w(217, 'perfect') + 0.05, 'NO RATTLE', 960, 120, 'cmd', 1.3)],
  sfx=[fx(R(0.2), 'bell_clean', -10, 'far', 'perfect bell tail'), fx(w(217, 'perfect'), 'stinger', -5, 'dry', 'red X', hit=True)], energy='swinging bell, red X')
S(T(218), 'cabin_dawn', 'queen_bunk', 'dawn_queen', 'theirs', 'CU', 'the queen\'s head snaps toward you, the grin still on', P(x=1300, y=520, z=1.2, rate=0.03),
  chars=[C('queen', [1300, 560, 0.95], 'front', 'queen_grin', [A(w(218, 'looks'), 'head_snap', deg=45, dur=0.12)], mode='bust', stage=3)],
  sfx=[fx(w(218, 'looks'), 'whoosh', -10, 'dry', 'snap', kind='hard')], energy='head snap, push')
S(T(219), 'cabin_dawn', 'queen_face', 'dawn_queen', 'theirs', 'ECU', 'the smile goes off her face in 2 frames: dead blank', P(x=960, y=520, z=1.25, rate=0.02),
  chars=[C('queen', [960, 540, 1.3], 'front', 'queen_grin', [A(w(219, 'goes'), 'smile_off', dur=2 / 60)], mode='bust', stage=3)],
  mus=[M(w(219, 'smile') - 0.1, 'silence', 0.0, 1.75, 'the deepest silence so far; ends on the real bell hit')],
  energy='the smile snapping off, then her face perfectly still, slow push (red share starts rising here)')
S(T(220), 'mess_porch', 'porch_run', 'bell_hit', 'ours', 'MS', 'Tess swings the padlock and hits the REAL bell', HH(x=1000, y=600, z=1.1, rate=0.04, shake=18, hit=[(w(220, 'hits'), 16)]),
  chars=[C('tess', 'tess_crate', 'profile_left', 'angry', [A(w(220, 'hits') - 0.25, 'strike', prop='padlock', target='bell')])],
  props=dict(bell='struck at %.2f' % w(220, 'hits')),
  sfx=[fx(w(220, 'hits'), 'bell_cracked', 2, 'close', 'THE REAL BELL: clean note + thin rattle, loudest hit of the section', strike='padlock', hit=True),
       fx(w(220, 'hits'), 'impact_hit', -4, 'dry', 'impact layer', hit=True)],
  mus=[M(w(220, 'hits'), 'hit', 1.0)], energy='padlock swing, bell jolting, beam flare, camera jolt 16 px')
STATE(w(220, 'hits'), bell='rattle', clock_theirs='07:00:00')
S(T(221), 'mess_porch', 'bell_ecu', 'bell_hit', 'ours', 'ECU', 'the crack rattling', P(x=1020, y=640, z=1.5, rate=0.04),
  sfx=[fx(w(221, 'rattle'), 'bell_cracked', -6, 'close', 'rattle tail continues', part='rattle')], energy='rim buzzing, push')
S(T(222), 'cabin_dawn', 'knot_cu', 'dawn_break', 'theirs', 'ECU', 'the lace drops from his fingers (the loop breaks); the dawn light flickers', P(x=960, y=620, z=1.15, rate=0.03),
  chars=[C('noah13', [960, 640, 420], 'front', 'calm_kid', [A(w(222, 'drops'), 'drop_lace')], mode='hands')], props=dict(shoe='lace dropped'),
  fx_post=[dict(t=w(222, 'drops'), exposure=-0.4, dur=0.12)], sfx=[fx(w(222, 'drops'), 'lace_pull', -10, 'close', 'lace falls'), fx(w(222, 'shoelace'), 'glitch', -12, 'dry', 'header clock 07:00:00', dur=0.1)],
  energy='lace falling, light flicker')
S(T(223), 'cabin_dawn', 'noah_cu', 'dawn_break', 'theirs', 'CU', 'Noah, relieved: "Finally," (lip-sync)', P(x=960, y=540, z=1.1, rate=0.03),
  chars=[C('noah13', [960, 560, 1.0], 'front', 'relief', [A(t(223), 'talk', line=223)], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='smile, push')

# ================================================================ RULE 6 542.03 - 609.48 (lines 225-258)
c6 = RULE(6)
S(c6, 'cabin_dawn', 'wide', 'dawn_break', 'theirs', 'MS', 'handheld: you shove Noah toward the opening', HH(x=1000, y=600, z=1.1, rate=0.04, shake=24),
  chars=[C('you', [1200, 1000, 700], 'profile_left', 'resolve', [A(w(227, 'shove'), 'shove')]), C('noah13', [960, 990, 600], 'profile_left', 'calm_kid', [A(w(227, 'shove'), 'stumble', to='doorway')])],
  hud=[tag(w(227, 'shove'), 'HIM FIRST', 960, 120, 'cmd', 1.1)], sfx=[fx(w(227, 'shove'), 'whoosh', -4, 'dry', 'shove', kind='hard'), fx(w(227, 'shove'), 'footsteps_wood_inside', -6, 'inside', 'stumbling steps', n=3)],
  mus=[M(c6 + 0.2, 'pulse_on', 0.7, None, 'climax pulse')], energy='shove, stumble, handheld 24 px/s')
S(T(228), 'cabin_dawn', 'doorway_back', 'dawn_break', 'theirs', 'ECU', 'low: his bare foot crosses the threshold into the dark side', P(x=960, y=860, z=1.4, rate=0.04),
  chars=[C('noah13', [960, 900, 700], 'profile_right', 'calm_kid', [A(w(228, 'foot'), 'step_through', foot='bare')], mode='feet')],
  sfx=[fx(w(228, 'foot'), 'bare_foot_step', -6, 'close', 'bare foot on dusty boards'), fx(w(228, 'through'), 'sub_drop', -8, 'dry', 'pressure', hit=True)], energy='foot crossing the light boundary')
S(T(229), 'cabin_dawn', 'doorway_back', 'dawn_break', 'theirs', 'MS', 'the foot stays; the doorway frame shudders', HH(x=960, y=560, z=1.15, rate=0.03, shake=14),
  sfx=[fx(w(229, 'stays'), 'wood_thud', -6, 'close', 'the wall creaks and shudders')], energy='frame shuddering, dust shaking loose')
S(T(230), 'cabin_now', 'doorway', 'red', 'ours', 'MS', 'our side: Tess, back and out of breath, grabs Noah\'s arm through the doorway', HH(x=960, y=540, z=1.1, rate=0.03, shake=18),
  chars=[C('tess', 'tess_doorway', 'q_right', 'fear', [A(w(230, 'grabs'), 'grab', what='arm')], light=RED), C('noah13', [1000, 980, 560], 'profile_left', 'strain', [], mode='body', note='half through the doorway')],
  sfx=[fx(w(230, 'grabs'), 'cloth_grab', -2, 'close', 'grab', hit=True), fx(R(0), 'breath', -8, 'close', 'Tess panting', kind='panting', dur=1.8)], energy='grab, handheld, red spill from the doorway')
STATE(w(230, 'grabs'), flashlight='tess_on')
S(T(231), 'cabin_now', 'doorway', 'red', 'ours', 'CU', 'Noah yelps: half in pale light, half in red', FA(x=960, y=520, z=1.15, rate=0.08),
  chars=[C('noah13', [960, 560, 1.0], 'profile_left', 'scream', [A(w(231, 'yelps'), 'flinch')], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(w(231, 'yelps'), 'impact_hit', -6, 'dry', 'hit', hit=True)], energy='flinch, fast push')
S(T(232), 'cabin_now', 'doorway', 'red', 'ours', 'ECU', 'his taped fingers slip out of the blue tape; the empty tape ring stays in Tess\'s grip', P(x=960, y=560, z=1.4, rate=0.04),
  chars=[C('noah13', [960, 580, 460], 'front', 'strain', [A(w(232, 'slipped'), 'slip_tape')], mode='hands')], props=dict(tape='slipped off at %.2f' % w(232, 'slipped')),
  sfx=[fx(w(232, 'slipped'), 'tape_peel', -4, 'close', 'tape slipping off in one go')], energy='fingers sliding out, the tape ring left behind')
STATE(w(232, 'slipped'), tape='slipped')
S(T(233), 'cabin_now', 'wide', 'red', 'ours', 'MS', 'Tess pulls him into the room; they fall back onto the boards', cam('reveal', x=1060, y=640, z=1.45, rate=-0.12, shake=22),
  chars=[C('tess', 'tess_mirror', 'q_right', 'fear', [A(w(233, 'pulls'), 'yank'), A(w(233, 'room'), 'fall_back')], light=RED), C('noah13', 'doorway_mid', 'profile_left', 'scream', [A(w(233, 'into'), 'fall_through')], light=RED)],
  sfx=[fx(w(233, 'room') + 0.1, 'body_fall', -2, 'close', 'two bodies hit the floor', hit=True)], energy='falling bodies, dust burst, handheld')
STATE(w(233, 'room'), sweatshirt='too_small')
S(T(234), 'cabin_now', 'cuffs', 'red', 'ours', 'ECU', 'the sweatshirt cuffs ride up his forearms as the arms lengthen (aging over 1.5 s)', P(x=960, y=560, z=1.2, rate=0.035),
  chars=[C('noah_grown', [960, 600, 460], 'front', 'shaken', [A(R(0), 'age', t1=R(1.5), part='arms')], mode='hands')],
  sfx=[fx(R(0.1), 'cloth_press', -6, 'close', 'cotton stretching, seams creaking', kind='stretch', dur=1.5)], energy='arms growing, cuffs sliding up, push')
S(T(235), 'cabin_now', 'wide', 'red', 'ours', 'CU', 'his face mid-change: jaw lengthening, stubble coming in; his voice cracks on your name (mouth only)', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('noah_grown', [960, 560, 1.0], 'front', 'shaken', [A(R(0), 'age', t1=R(-0.2), part='face', start=0.4), A(w(235, 'name'), 'talk_silent', dur=0.5)], mode='bust', light=RED)],
  dof=dict(focus=1.0, dof=6.75), sfx=[fx(w(235, 'cracks'), 'glitch', -16, 'dry', 'tiny crack in the room tone', dur=0.1, amount=0.3)], energy='face morphing, push')
S(T(236), 'cabin_now', 'wide', 'red', 'ours', 'CU', 'grown Noah, complete: about 27, gap teeth still there', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('noah_grown', [960, 560, 1.0], 'front', 'shaken', [A(w(236, 'drops'), 'talk_silent', dur=0.8)], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75),
  mus=[M(w(236, 'drops'), 'sub_drop', 0.6, None, 'the drone drops an octave with his voice')], energy='breathing hard, creep')
S(T(237), 'cabin_now', 'hands', 'red', 'ours', 'OTS', 'over his shoulder: he stares at his hands', P(x=960, y=620, z=1.1, rate=0.03),
  chars=[C('noah_grown', 'noah_floor', 'back', 'shaken', [A(R(0), 'look_at_hands')])], energy='hands turning over, push')
S(T(238), 'cabin_now', 'hands', 'red', 'ours', 'ECU', 'his big shaking hands beside yours: bigger', P(x=960, y=560, z=1.2, rate=0.03),
  chars=[C('noah_grown', [880, 600, 520], 'front', 'shaken', [A(R(0), 'tremble', amount=1.0)], mode='hands'), C('you', [1120, 620, 440], 'front', 'neutral', [], mode='hands')],
  sfx=[fx(R(0.2), 'breath', -10, 'close', 'his shaky breath', kind='nervous', dur=2)], energy='tremble, push')
S(T(239), 'cabin_now', 'wide', 'red', 'ours', 'MS', 'he stands and hits his shoulder on the top bunk', HH(x=1100, y=520, z=1.05, rate=0.03, hit=[(w(239, 'shoulder'), 12)]),
  chars=[C('noah_grown', 'noah_stand', 'q_left', 'shaken', [A(w(239, 'stands'), 'stand_up'), A(w(239, 'shoulder'), 'stand_hit', what='bunk')])],
  sfx=[fx(w(239, 'shoulder'), 'wood_thud', 0, 'close', 'shoulder into the bunk + bunk rattle', hit=True)], energy='standing, impact, bunk rattling, dust falling')
S(T(240), 'cabin_now', 'bunk_low', 'red', 'ours', 'LOW', 'low angle: the top bunk at his shoulder height; dust drifting down from the hit', CR(x=960, y=480, z=1.1, rate=0.015),
  energy='dust falling through the red light, the bunk still swaying')
S(T(241), 'cabin_now', 'doorway', 'red', 'ours', 'MS', 'from our side through the doorway: you in the pale light, and behind you the queen standing, mouth open, calling his name (no voice)', P(x=960, y=500, z=1.2, rate=0.03),
  chars=[C('you', [960, 960, 560, 1.4], 'back', 'fear', [A(R(0), 'grip_frame')]), C('queen', [1100, 900, 660, 2.2], 'front', 'queen_call', [A(w(241, 'calls'), 'call_silent', dur=1.4)], mode='body', stage=3)],
  sfx=[fx(w(241, 'calls'), 'crowd_whisper', -10, 'mirror', 'a reverberant breath shaped like a name (no words)', dur=1.4, density=1)], energy='her mouth opening wide, push')
S(T(242), 'cabin_now', 'wide', 'red', 'ours', 'CU', 'grown Noah covers his ears fast', FA(x=960, y=520, z=1.15, rate=0.08),
  chars=[C('noah_grown', [960, 560, 1.0], 'front', 'fear', [A(w(242, 'covers'), 'cover_ears', dur=0.15)], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(w(242, 'covers'), 'cloth_grab', -6, 'close', 'hands slap over ears')], energy='hands snapping to ears')
S(T(243), 'cabin_now', 'wide', 'red', 'ours', 'ECU', 'grown Noah rocking, eyes shut tight', HH(x=960, y=540, z=1.2, rate=0.02),
  chars=[C('noah_grown', [960, 560, 1.15], 'front', 'fear', [A(R(0), 'rock', period=0.9)], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75), energy='rocking, handheld')
S(T(244), 'cabin_dawn', 'queen_face', 'dawn_break', 'theirs', 'CU', 'the queen in the doorway light, head tilted, calling silently (entity language)', P(x=960, y=500, z=1.1, rate=0.03),
  chars=[C('queen', [960, 520, 1.0], 'front', 'queen_call', [A(R(0), 'head_tilt', angle=24, dur=1.5)], mode='bust', stage=3)], energy='tilt, hair floating, push')
S(T(245), 'cabin_now', 'doorway', 'red', 'ours', 'CU', 'Tess shouts: "Five!" The counter pops to 5', FA(x=960, y=520, z=1.15, rate=0.10, hit=[(t(246), 10)]),
  chars=[C('tess', [960, 560, 1.0], 'q_right', 'shout', [A(t(246), 'talk', line=246)], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75),
  hud=[dict(t=t(246), type='counter_call', value=5)], sfx=[fx(t(246), 'countdown_tick', 0, 'dry', 'counter 5 (big tick)', hit=True)], energy='shout, counter pop')
S(T(247), 'cabin_dawn', 'doorway_back', 'dawn_break', 'theirs', 'POV', 'your hand reaches for the doorway frame', HH(x=960, y=560, z=1.1, rate=0.04),
  chars=[C('you', [1000, 640, 440], 'front', 'fear', [A(w(247, 'reach'), 'reach', to='doorway')], mode='hands')], sfx=[fx(w(247, 'doorway'), 'mirror_handle', -10, 'close', 'hand on the frame', kind='bump')],
  mus=[M(e(248) - 1.0, 'silence', 0.0, 1.0, 'silence before "Wait"')], energy='hand stretching, handheld')
S(T(248), 'cabin_dawn', 'doorway_back', 'dawn_break', 'theirs', 'OTS', 'over your shoulder toward the doorway: Tess and grown Noah in the dark beyond', P(x=960, y=520, z=1.15, rate=0.03),
  chars=[C('you', [700, 1100, 900, 0.7], 'back', 'fear', [A(R(0), 'freeze')], mode='silhouette')], energy='push, red flicker beyond')
S(T(249), 'cabin_dawn', 'queen_mouth', 'dawn_break', 'theirs', 'ECU', 'her mouth speaking in Noah\'s 13-year-old voice: "Wait, he forgot his shoe."', P(x=960, y=560, z=1.3, rate=0.03),
  chars=[C('queen', [960, 470, 1.8], 'front', 'queen_soft', [A(t(249), 'talk', line=249)], mode='bust', stage=3, crop='mouth')],
  sfx=[fx(w(249, 'wait'), 'impact_hit', -2, 'dry', 'hit on "Wait" after the silence', hit=True)], voice_fx='queen_child', mus=[M(w(249, 'wait'), 'hit', 0.9)],
  energy='lips moving, push')
S(T(250), 'cabin_dawn', 'wide', 'dawn_break', 'theirs', 'CU', 'you, frozen', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('you', [960, 560, 1.0], 'front', 'fear', [A(R(0), 'freeze', t1=R(-0.1))], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='creep, the light flickering')
S(T(251), 'cabin_now', 'wide', 'red', 'ours', 'CU', 'grown Noah looks up with dread', P(x=960, y=520, z=1.1, rate=0.03),
  chars=[C('noah_grown', [960, 560, 1.0], 'front', 'fear', [A(R(0.2), 'look_up')], mode='bust', light=RED)], dof=dict(focus=1.0, dof=6.75), energy='look up, push')
S(T(252), 'cabin_dawn', 'wide', 'dawn_break', 'theirs', 'MS', 'you turn back toward the dawn cabin', HH(x=960, y=560, z=1.1, rate=0.03),
  chars=[C('you', [960, 1000, 680], 'back', 'fear', [A(w(252, 'turn'), 'snap_turn', frm=2, to=0)])],
  hud=[tag(w(252, 'you') - 0.05, "DON'T TURN AROUND", 960, 120, 'cmd', 1.3)], sfx=[fx(w(252, 'turn'), 'whoosh', -6, 'dry', 'turn', kind='soft'), fx(w(252, 'you'), 'ui_pop', -6, 'dry', 'tag', hit=True)],
  energy='the turn, handheld')
S(T(253), 'cabin_dawn', 'wide', 'dawn_break', 'theirs', 'WS', 'your POV: the empty bunk, the dip', PU(x=1100, y=640, z=1.25, rate=-0.03),
  mus=[M(T(253), 'dip', 0.25, 4, 'time stretches: the bed thins')], energy='creep, light flickering')
S(T(254), 'memory', 'night_window', 'memory_night', 'memory', 'MS', 'memory flash: Noah at 13 at the night window turns to say something; his mouth opens; cut before a word', P(x=960, y=520, z=1.1, rate=0.03), tr='white',
  chars=[C('noah13', [960, 1000, 640], 'q_right', 'neutral', [A(w(254, 'said'), 'turn', to=0.5), A(w(254, 'you') - 0.1, 'mouth_open')])], energy='turn, moths, push')
S(T(255), 'cabin_dawn', 'wide', 'dawn_break', 'theirs', 'MS', 'your body turns fully, before you can think', HH(x=960, y=560, z=1.1, rate=0.03),
  chars=[C('you', [960, 1000, 680], 'front', 'fear', [A(w(255, 'turns'), 'turn', to=0)])], sfx=[fx(w(255, 'turns'), 'jacket_cloth', -10, 'close', 'jacket swish')], energy='turning, handheld')
S(T(256), 'cabin_dawn', 'shoe', 'dawn_break', 'theirs', 'INSERT', 'the other shoe beside the bed, lace loose; red X over it', P(x=960, y=640, z=1.15, rate=0.03),
  hud=[redx(w(256, 'shoe'), 960, 640, 170, 1.0)], sfx=[fx(w(256, 'shoe'), 'stinger', -6, 'dry', 'red X', hit=True)], props=dict(shoe='left behind'), energy='push, red X')
S(T(257), 'mirror_world', 'feet', 'red', 'mirror', 'ECU', 'BIGGEST SCARE: you look down: you stand on a red-edged step, and her pale bare foot is on the step just below yours', P(x=960, y=700, z=1.15, rate=0.03, snap=(w(257, 'bare'), 1.4)),
  chars=[C('you', [880, 560, 600], 'front', 'fear', [], mode='feet'), C('queen', [1040, 900, 700], 'front', 'queen_still', [A(w(257, 'bare'), 'toes_curl')], mode='feet', stage=3)],
  props=dict(queen='on the step below yours'),
  sfx=[fx(w(257, 'bare'), 'impact_hit', 2, 'dry', 'THE BIGGEST HIT OF THE FILM (mix momentary max +10 LU)', hit=True, size=1.5), fx(w(257, 'bare'), 'braam', 0, 'dry', 'braam', hit=True, key='d'),
       fx(w(257, 'bare') + 0.1, 'bare_foot_step', -8, 'mirror', 'wet foot settling on the step')],
  mus=[M(w(257, 'bare') - 1.3, 'silence', 0.0, 1.3, 'silence into the biggest hit'), M(w(257, 'bare'), 'hit', 1.0)], energy='punch-in x1.4, toes curling, step edges glowing red')
STATE(w(257, 'bare'), queen='step_below')
S(T(258), 'cabin_now', 'doorway', 'red', 'ours', 'MS', 'Tess\'s arm reaches through the doorway, grabs your collar and yanks; whip pull back', cam('whip', x=960, y=520, z=1.2, x1=760, y1=560, z1=0.95),
  chars=[C('tess', 'tess_doorway', 'profile_right', 'angry', [A(w(258, 'collar'), 'grab_collar'), A(w(258, 'pulls'), 'yank')], light=RED), C('you', 'you_doorway', 'back', 'fear', [A(w(258, 'pulls'), 'yanked_back')])],
  sfx=[fx(w(258, 'collar'), 'cloth_grab', 0, 'close', 'collar grabbed', hit=True), fx(w(258, 'pulls'), 'whoosh', -2, 'dry', 'yank', kind='hard')],
  fx_post=[dict(t=w(258, 'pulls'), white=0.5, dur=0.08)], energy='grab, yank, whip pan, white flash')
STATE(w(258, 'pulls'), side='ours', doorway='closing')

# ================================================================ RULE 7 609.48 - 628.94 (lines 259-267)
c7 = RULE(7)
S(c7, 'cabin_now', 'floor_low', 'red', 'ours', 'LOW', 'you hit the floor; dust bursts', HH(x=960, y=640, z=1.1, rate=0.04, hit=[(w(261, 'hit'), 16)]),
  chars=[C('you', [960, 1000, 640], 'profile_right', 'fear', [A(w(261, 'hit'), 'fall_back')])], sfx=[fx(w(261, 'hit'), 'body_fall', 0, 'close', 'you land on the boards', hit=True)],
  energy='impact, dust burst, camera jolt')
STATE(w(261, 'hit'), mirror='mirror_again', doorway='glass')
S(T(262), 'cabin_now', 'hands', 'red', 'ours', 'CU', 'Tess shoves the towel into your hands', FA(x=960, y=560, z=1.1, rate=0.08),
  chars=[C('tess', [800, 520, 440], 'front', 'angry', [A(w(262, 'shoves'), 'shove', prop='towel')], mode='hands'), C('you', [1100, 620, 440], 'front', 'fear', [A(w(262, 'hands'), 'take', prop='towel')], mode='hands')],
  props=dict(towel='in your hands'), sfx=[fx(w(262, 'shoves'), 'towel_cloth', -3, 'close', 'towel shoved', kind='snatch')], energy='towel thrust in, fast push')
STATE(w(262, 'shoves'), towel='in_hands')
S(T(263), 'mirror', 'mirror_cu', 'red', 'mirror', 'CU', 'the doorway is a mirror again, the steps glowing red on it; you wipe from the top down', P(x=960, y=480, z=1.05, rate=0.04),
  chars=[C('you', [1200, 300, 460], 'front', 'fear', [A(w(263, 'wipe'), 'wipe_glass', strokes=3, dir='down')], mode='hands')],
  props=dict(steps_drawn='7 glowing, erased top-down 618.73-620.0'),
  hud=[tag(w(263, 'top'), 'TOP DOWN', 960, 120, 'cmd', 1.1)],
  sfx=[fx(w(263, 'wipe'), 'glass_wipe', 0, 'close', 'wipe 1'), fx(w(263, 'top'), 'glass_wipe', 0, 'close', 'wipe 2'), fx(w(263, 'down'), 'glass_wipe', -1, 'close', 'wipe 3'), fx(w(263, 'top'), 'ui_pop', -8, 'dry', 'tag')],
  energy='towel strokes wiping red streaks downward, push')
S(T(264), 'mirror', 'mirror_cu', 'red', 'mirror', 'ECU', 'the last streak of red on the glass, the towel moving across it', TR(x=760, y=760, z=1.4, dx=-50),
  sfx=[fx(w(264, 'streak'), 'glass_wipe', -3, 'close', 'slow squeak')], energy='streak thinning under the towel, track')
S(T(265), 'mirror', 'queen_step_tilt', 'red', 'mirror', 'CU', 'through the streak: the small woman lifts her bare foot toward a step you already erased (only a faint smudge)', P(x=760, y=700, z=1.5, rate=0.04),
  chars=[C('queen', [700, 900, 300, 1.04], 'q_right', 'queen_grin', [A(w(265, 'lift'), 'lift_foot', to='erased_step', dur=2.0)], mode='body', stage=3)],
  props=dict(queen='lifting her foot toward an erased step'), sfx=[fx(w(265, 'lift'), 'cloth_press', -10, 'mirror', 'satin', kind='satin')], energy='foot rising in slow motion, push')
S(T(266), 'mirror', 'queen_step_tilt', 'red', 'mirror', 'ECU', 'her foot hangs over clean glass, toes curling, no step to land on', CR(x=720, y=760, z=1.9, rate=0.015),
  chars=[C('queen', [700, 900, 300, 1.04], 'q_right', 'queen_grin', [A(R(0), 'toes_curl')], mode='feet', stage=3)],
  sfx=[fx(R(0.2), 'tinnitus', -16, 'dry', 'held tone', dur=1.3)], mus=[M(w(266, 'hangs'), 'silence', 0.0, 1.3, 'silence while the foot hangs')], energy='toes curling, creep')
S(T(267), 'mirror', 'mirror_cu', 'dark', 'mirror', 'CU', 'the glass goes dark: the red and the reflection are sucked out to black', P(x=960, y=540, z=1.1, rate=0.03),
  props=dict(mirror='dark at %.2f' % w(267, 'goes')),
  sfx=[fx(w(267, 'goes'), 'sub_drop', 0, 'dry', 'the glass goes dark', hit=True), fx(w(267, 'goes'), 'glass_resonance', -4, 'close', 'glass thump and cut-off', hit=True)],
  mus=[M(w(267, 'goes'), 'hit', 0.9), M(w(267, 'dark') + 0.2, 'silence', 0.0, 0.6, 'out to near silence; room tone only')], energy='light draining out of the glass in 0.3 s, push')
STATE(w(267, 'goes'), mirror='dark', queen='absent')

# ================================================================ ENDING 628.94 - 698.62, tail to the end (lines 268-299)
S(T(268), 'cabin_now', 'floor_end', 'after', 'ours', 'WS', 'moonlight back; Tess\'s flashlight on the floor throwing a beam across the dust; grown Noah sits on the floor in the too-small sweatshirt', PU(x=1000, y=700, z=1.2, rate=-0.012),
  chars=[C('noah_grown', 'noah_floor', 'front', 'shaken', [A(R(0), 'tremble', amount=0.4)]), C('tess', 'tess_floor_end', 'q_left', 'sad', [A(R(0.5), 'kneel')])],
  sfx=[fx(R(0.05), 'room_tone', -8, 'inside', 'cabin tone, crickets outside again', dur=4), fx(R(0.05), 'ambience_camp_night', -14, 'outside', 'crickets through the walls', dur=4)],
  mus=[M(T(268), 'swell', 0.3, 10, 'ending theme: low strings and piano, unpulsed, D')], energy='slow pull-out, dust settling in the floor beam, his breathing')
STATE(T(268), flashlight='tess_floor')
S(T(269), 'cabin_now', 'floor_end', 'after', 'ours', '2S', 'you beside him (he is bigger, older); you take off your jacket and put it around his shoulders', P(x=980, y=620, z=1.1, rate=0.02),
  chars=[C('you', 'you_floor', 'q_right', 'grief', [A(w(270, 'give'), 'give_jacket')]), C('noah_grown', 'noah_floor', 'q_left', 'shaken', [])],
  props=dict(jacket='you -> Noah at %.2f' % w(270, 'jacket')), sfx=[fx(w(270, 'give'), 'jacket_cloth', -5, 'close', 'jacket off and around')], energy='jacket swinging round')
STATE(w(270, 'jacket'), jacket='noah')
S(T(271), 'cabin_now', 'floor_end', 'after', 'ours', 'CU', 'grown Noah holds the jacket by the collar and asks about Mom (mouth only)', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('noah_grown', [960, 560, 1.0], 'front', 'hopeful', [A(w(271, 'holds'), 'hold_collar'), A(w(271, 'asks'), 'talk_silent', dur=1.2)], mode='bust', light=dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.3))],
  dof=dict(focus=1.0, dof=6.75), energy='hands on collar, creep')
S(T(272), 'cabin_now', 'clock', 'after', 'ours', 'INSERT', 'the cabin clock running forward again: just after midnight', P(x=960, y=540, z=1.0, rate=0.025),
  sfx=[fx(R(0.05), 'clock_tick', -10, 'inside', 'ticking forward', dur=1.4)], energy='second hand moving forward')
S(T(274), 'cabin_now', 'floor_end', 'after', 'ours', 'CU', 'you, crying and smiling', CR(x=960, y=520, z=1.05, rate=0.01),
  chars=[C('you', [960, 560, 1.0], 'q_left', 'relief_cry', [A(R(0.3), 'tears', amount=0.8)], mode='bust', light=dict(rim='#9fb6ff', rim_a=70, side=1, key=-0.3))], dof=dict(focus=1.0, dof=6.75),
  energy='tears, creep')
S(T(275), 'cabin_now', 'hands', 'after', 'ours', 'ECU', 'your left fist will not open; fingers trembling', P(x=960, y=560, z=1.15, rate=0.025),
  chars=[C('you', [960, 600, 460], 'front', 'neutral', [A(w(275, 'fingers'), 'fist', fail_open=True, tremble=0.8)], mode='hands')], energy='fingers straining, push')
S(T(276), 'cabin_now', 'hands', 'after', 'ours', 'ECU', 'the fist opens slowly: the red candy', CR(x=960, y=560, z=1.2, rate=0.012),
  chars=[C('you', [960, 600, 460], 'front', 'neutral', [A(R(0.4), 'open_fist', dur=1.4)], mode='hands')], sfx=[fx(R(0.6), 'candy_wrapper', -8, 'close', 'crinkle as the hand opens')],
  props=dict(candy='palm'), energy='fingers uncurling, creep')
STATE(T(276), candy='palm')
S(T(277), 'cabin_now', 'palm', 'after', 'ours', 'INSERT', 'the twist wrapper\'s imprint pressed red into your palm', P(x=960, y=560, z=1.2, rate=0.025),
  sfx=[fx(w(277, 'palm'), 'candy_wrapper', -14, 'close', 'candy rolls in the palm')], energy='candy rolling, push')
S(T(278), 'ui', 'call', 'phone', 'ui', 'UI', 'calling MOM: one ring, then connected', HH(x=960, y=560, z=1.0, rate=0.015),
  hud=[dict(t=T(278), type='phone', state='calling', name='MOM', x=960, y=560), dict(t=w(278, 'up'), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), x=960, y=560)],
  sfx=[fx(T(278) + 0.1, 'phone_ring', -8, 'phone', 'one ring-back', kind='ringback', n=1), fx(w(278, 'up'), 'phone_pickup', -6, 'phone', 'pickup click')], energy='call UI animating, handheld')
S(T(279), 'ui', 'call', 'phone', 'ui', 'UI', 'connected, Mom\'s live waveform: "Did you find the sweatshirt?"', P(x=960, y=560, z=1.02, rate=0.02),
  hud=[dict(t=T(279), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=True, follow_line=279), x=960, y=560)], energy='waveform bars moving with her voice')
S(T(280), 'cabin_now', 'floor_end', 'after', 'ours', 'INSERT', 'grown Noah\'s big hand held out for the phone, still shaking', P(x=960, y=560, z=1.1, rate=0.025),
  chars=[C('noah_grown', [960, 600, 460], 'front', 'hopeful', [A(w(280, 'holds'), 'hand_out'), A(R(0), 'tremble', amount=0.4)], mode='hands')], energy='hand reaching, tremble')
S(T(281), 'cabin_now', 'floor_end', 'after', 'ours', 'CU', 'grown Noah, phone at his ear: "Hi, Mom." (lip-sync; the emotional peak)', CR(x=960, y=520, z=1.1, rate=0.012),
  chars=[C('noah_grown', [960, 560, 1.0], 'q_left', 'relief_cry', [A(R(0), 'phone_to_ear', side=1), A(t(282), 'talk', line=282)], mode='bust', light=dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.3))],
  dof=dict(focus=1.0, dof=6.75), mus=[M(t(282), 'swell', 0.55, 3, 'the one warm swell')], energy='tears, creep')
S(round(e(282) + 0.02, 3), 'ui', 'call', 'phone', 'ui', 'UI', 'the waveform flat: silence on the line', CR(x=960, y=560, z=1.04, rate=0.01),
  hud=[dict(t=R(0), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=False, flat=True), x=960, y=560)],
  mus=[M(t(283), 'silence', 0.0, 1.3, 'a true pause: music out, room tone only')], energy='timer counting, flat line breathing slightly')
S(T(284), 'cabin_now', 'floor_end', 'after', 'ours', 'ECU', 'grown Noah says it again, softer (mouth only)', CR(x=960, y=540, z=1.2, rate=0.01),
  chars=[C('noah_grown', [960, 560, 1.15], 'q_left', 'relief_cry', [A(w(284, 'says'), 'talk_silent', dur=0.8)], mode='bust', light=dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.3))], energy='creep, tear running')
S(T(285), 'ui', 'call', 'phone', 'ui', 'UI', 'the waveform spikes with the chair scrape', P(x=960, y=560, z=1.04, rate=0.02),
  hud=[dict(t=T(285), type='phone', state='connected', name='MOM', timer_from=w(278, 'up'), waveform=dict(live=True, spike_at=w(285, 'chair')), x=960, y=560)],
  sfx=[fx(w(285, 'chair'), 'chair_scrape', -4, 'phone', 'her chair scrapes back (through the phone)', hit=True)], energy='spike, push')
S(T(286), 'cabin_now', 'floor_end', 'after', 'ours', '2S', 'you and grown Noah share the phone', CR(x=960, y=600, z=1.1, rate=0.012),
  chars=[C('you', 'you_floor', 'q_right', 'relief_cry', []), C('noah_grown', 'noah_floor', 'q_left', 'hopeful', [A(R(0), 'phone_to_ear', side=1), A(w(287, 'looks'), 'look', x=1300, y=520, lost=True)])],
  energy='creep; he turns to you for help on "He looks at you", beam on the floor')
S(T(288), 'cabin_now', 'floor_end', 'after', 'ours', 'CU', 'you: what do you tell him', PU(x=960, y=520, z=1.2, rate=-0.03),
  chars=[C('you', [960, 560, 1.0], 'q_left', 'grief', [A(R(1.0), 'swallow')], mode='bust', light=dict(rim='#9fb6ff', rim_a=70, side=1, key=-0.3))], dof=dict(focus=1.0, dof=6.75), energy='creep')
S(T(289), 'cabin_now', 'sill', 'after', 'ours', 'MS', 'behind you, Tess picks up her phone from the windowsill', P(x=960, y=580, z=1.05, rate=0.03),
  chars=[C('tess', [960, 560, 340], 'front', 'neutral', [A(w(289, 'picks'), 'pick_up', prop='phone')], mode='hands')],
  sfx=[fx(w(289, 'picks'), 'phone_handle', -6, 'close', 'phone lifted off the wood', kind='pick_up')], energy='hand lifting the phone, dust trail')
STATE(w(289, 'picks'), phone='tess_hand')
S(T(290), 'cabin_now', 'phone_screen', 'after', 'ours', 'INSERT', 'the phone in her hand, face up: red X', P(x=960, y=560, z=1.1, rate=0.03),
  hud=[redx(w(290, 'face'), 960, 560, 180, 1.1), tag(w(290, 'face') + 0.05, 'FACE UP', 960, 120, 'cmd', 1.2)], sfx=[fx(w(290, 'face'), 'stinger', -5, 'dry', 'red X', hit=True)],
  mus=[M(w(290, 'face'), 'riser', 0.6, 8, 'the last rise begins (peaks at 697)')], energy='push, red X')
S(T(291), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'her sleeve wipes dust off the dark screen', P(x=960, y=560, z=1.2, rate=0.03),
  chars=[C('tess', [960, 560, 520], 'front', 'neutral', [A(w(291, 'wipes'), 'wipe_glass', strokes=2, sleeve=True)], mode='hands')],
  sfx=[fx(w(291, 'wipes'), 'glass_wipe', -6, 'close', 'sleeve on glass', sleeve=True)], energy='sleeve swiping, dust lifting')
S(T(292), 'cabin_now', 'floor_end', 'after', 'ours', 'CU', 'Tess, puzzled, holding out the phone: "Did you get lipstick on this?" (lip-sync)', P(x=960, y=520, z=1.1, rate=0.025),
  chars=[C('tess', [960, 560, 1.0], 'q_right', 'puzzled', [A(t(292), 'talk', line=292), A(R(0), 'hold_up', prop='phone', side=-1)], mode='bust', light=dict(rim='#9fb6ff', rim_a=70, side=1, key=-0.3))],
  dof=dict(focus=1.0, dof=6.75), energy='talking, push')
S(T(294), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'seven tiny red lipstick steps on the dark screen', P(x=960, y=560, z=1.2, rate=0.04),
  props=dict(phone='screen_steps: 7 tiny steps'), sfx=[fx(w(294, 'seven'), 'glass_resonance', -12, 'close', 'faint glass hum', hit=True)], energy='push 4 %/s, the steps catching the floor beam')
STATE(w(294, 'seven'), phone='screen_steps')
S(T(295), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'your finger approaches the bottom step', P(x=900, y=640, z=1.35, rate=0.03),
  chars=[C('you', [1000, 720, 420], 'front', 'fear', [A(w(295, 'touch'), 'touch_glass', at=(900, 660))], mode='hands')],
  mus=[M(w(295, 'touch') + 0.1, 'silence', 0.0, 1.8, 'silence into the click')], energy='finger closing in, push')
S(T(296), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'the nail clicks on clean glass (the bottom step is on the other side); punch-in', P(x=900, y=660, z=1.5, rate=0.03, snap=(w(296, 'clicks'), 1.3)),
  chars=[C('you', [980, 720, 460], 'front', 'fear', [A(w(296, 'clicks'), 'nail_tap')], mode='hands')],
  sfx=[fx(w(296, 'clicks'), 'nail_click_glass', 0, 'close', 'THE SAME click sample as 143.29', hit=True), fx(w(296, 'clicks'), 'glass_resonance', -6, 'close', 'ring', hit=True)],
  mus=[M(w(296, 'clicks'), 'stinger', 0.8)], energy='punch-in x1.3 on the click')
S(T(297), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'CU', 'the phone in Tess\'s hand from above; deep in the dark glass, faint, a tiny black figure on the bottom step', P(x=960, y=560, z=1.1, rate=0.04),
  chars=[C('queen', [900, 660, 60, 1.04], 'front', 'queen_still', [A(R(0), 'still')], mode='body', stage=3, note='tiny, inside the phone glass')],
  props=dict(queen='phone'), energy='push 4 %/s, the figure barely there, the beam glinting')
STATE(T(297), queen='phone')
S(T(298), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'closer on the screen: the figure is there', FA(x=900, y=640, z=1.6, rate=0.08), energy='fast push')
S(T(299), 'cabin_now', 'phone_screen', 'phone_glow', 'ours', 'ECU', 'FULL CREEPY FACE 3 fills the phone screen: "Can I have one more minute?" in Noah\'s voice; hard cut to black on the last word', P(x=960, y=520, z=1.0, rate=0.04),
  chars=[C('queen', [960, 520, 1.1], 'front', 'queen_grin', [A(t(299), 'talk', line=299)], mode='bust', stage=3, inside='phone_screen')],
  sfx=[fx(w(299, 'can'), 'stinger', 0, 'dry', 'final stinger', hit=True), fx(w(299, 'can'), 'braam', -2, 'dry', 'final braam', hit=True, key='d')], voice_fx='phone_child',
  mus=[M(w(299, 'can'), 'stinger', 1.0)], energy='grin talking, push')
S(round(e(299) + 0.04, 3), 'black', 'black', 'black', 'black', 'BLACK', 'black', cam('push', x=960, y=540, z=1.0, rate=0.0), tr='black', captions=False,
  sfx=[fx(round(e(299) + 0.3, 3), 'bell_clean', -14, 'far', 'in the black: one faint, perfect, wrong bell note (the queen\'s bell); decays to nothing')],
  mus=[M(round(e(299) + 0.04, 3), 'end', 0.0, None, 'everything out except the hit tails and the faint bell')], energy='black (tail)')

# ================================================================ SHORT CUTS: impact and reaction inserts under 1 s (REF: 11-14 % of shots < 1 s)
# Each one splits a longer shot on an action word; SFX authored on the longer shot are re-homed to whichever shot contains them.
S(7.50, 'mirror_world', 'eye', 'void', 'mirror', 'ECU', 'a flash of a red iris with a pinpoint pupil in the dark (queen tease, stage 0)', FA(x=960, y=520, z=1.3, rate=0.12),
  sfx=[fx(7.52, 'stinger', -6, 'dry', 'eye flash', hit=True)], energy='the eye glint flaring and shrinking, fast push 12 %/s')
S(Wc(10, 'keys', off=-0.1), 'camp_gate', 'keys_cu', 'moon_flash', 'ours', 'ECU', 'the key ring swinging in Tess\'s hand: padlock key, carabiner, a CABIN 7 tag',
  FA(x=960, y=540, z=1.2, rate=0.10), chars=[C('tess', [960, 520, 380], 'front', 'brave', [A(w(10, 'keys'), 'jingle', prop='keys')], mode='hands')],
  energy='keys swinging and glinting in the beam, fast push')
S(119.90, 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'Tess: fear eyes (white discs, pinpoint pupils), a hand rising to her mouth', FA(x=960, y=520, z=1.1, rate=0.10),
  chars=[C('tess', [960, 560, 1.0], 'q_left', 'fear', [A(119.95, 'hand_to_mouth')], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(119.95, 'breath', -8, 'close', 'sharp gasp', kind='gasp')], energy='hand to mouth, beam shaking, fast push')
S(144.25, 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'you: fear eyes, the fingertip still raised', FA(x=960, y=520, z=1.1, rate=0.10),
  chars=[C('you', [960, 560, 1.0], 'q_right', 'fear', [A(144.3, 'flinch')], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(144.3, 'breath', -10, 'close', 'held breath', kind='held', dur=0.6)], energy='flinch, fast push')
S(Wc(56, 'on', off=0.0), 'mirror_world', 'feet', 'void', 'mirror', 'ECU', 'her bare heel and black hem standing on the clean red line (the eighth step)', P(x=960, y=760, z=1.3, rate=0.05),
  chars=[C('queen', [960, 900, 900], 'back', 'queen_still', [A(R(0), 'still')], mode='feet', stage=0)], energy='hem stirring, red line glinting, push 5 %/s')
S(198.55, 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'Tess flinches back from the glass, hand over her mouth', FA(x=960, y=520, z=1.1, rate=0.10),
  chars=[C('tess', [960, 560, 1.0], 'q_left', 'fear', [A(198.6, 'flinch'), A(198.7, 'hand_to_mouth')], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75),
  sfx=[fx(198.62, 'breath', -8, 'close', 'gasp', kind='gasp')], energy='flinch, beam lurching')
S(round(e(92) - 0.05, 3), 'cabin_now', 'two_shot', 'flash', 'ours', 'CU', 'Tess hears the wish; her eyes go to the glass', FA(x=960, y=520, z=1.1, rate=0.08),
  chars=[C('tess', [960, 560, 1.0], 'q_left', 'fear', [A(R(0.1), 'look', x=1300, y=500)], mode='bust', light=FLASH)], dof=dict(focus=1.0, dof=6.75), energy='eyes snapping to the mirror')
S(250.80, 'cabin_now', 'towel_fly', 'flash', 'ours', 'ECU', 'the towel flies at the lens (whip)', cam('whip', x=960, y=540, z=1.1, x1=1240, y1=520, z1=1.25),
  energy='terry cloth filling the frame, whip pan with motion blur')
S(251.60, 'cabin_now', 'mirror_ots', 'flash', 'ours', 'MS', 'the towel lands over the mirror; the beam swings off it', HH(x=960, y=520, z=1.1, rate=0.03, shake=20),
  chars=[C('tess', 'tess_mirror', 'q_right', 'fear', [A(R(0), 'step_back')])], energy='towel settling, beam swinging, handheld')
S(Wc(99, 'through', off=-0.05), 'cabin_now', 'towel_over', 'flash', 'ours', 'ECU', 'the fingertips straining the terry loops toward the lens', FA(x=960, y=500, z=1.5, rate=0.10),
  chars=[C('queen', [960, 520, 700], 'front', 'queen_still', [A(R(0), 'press_through_cloth', depth=1.0)], mode='hands', stage=2)],
  sfx=[fx(R(0.1), 'cloth_press', -6, 'close', 'loops stretching', kind='stretch')], energy='cloth stretching toward camera, fast push')
S(281.55, 'cabin_now', 'clock', 'flash', 'ours', 'ECU', 'ECU: the second hand stepping backward, tick by tick', FA(x=1000, y=420, z=1.8, rate=0.10),
  energy='second hand stepping back, fast push')
S(337.0, 'cabin_dawn', 'towel', 'dawn', 'theirs', 'ECU', 'the hanging drop: the room reflected upside-down inside it', cam('orbit', x=960, y=480, z=2.0, dx=25, rate=0.02, roll=3),
  energy='slow orbit around the still drop, highlights crawling')
S(346.70, 'cabin_dawn', 'towel', 'dawn', 'theirs', 'ECU', 'the splash on the towel', FA(x=960, y=600, z=1.6, rate=0.08), energy='splash crown, fast push')
S(358.30, 'cabin_dawn', 'hands_jerk', 'dawn', 'theirs', 'ECU', 'your hand and his small taped hand tear apart', FA(x=960, y=540, z=1.3, rate=0.12),
  chars=[C('noah13', [880, 560, 420], 'front', 'calm_kid', [A(w(141, 'jerks'), 'hand_jerk', dir='back')], mode='hands'), C('you', [1080, 560, 440], 'front', 'shock', [], mode='hands')],
  energy='hands snapping apart, fast push')
S(358.95, 'cabin_dawn', 'wide', 'dawn', 'theirs', 'CU', 'you: shock, your empty hand still out', P(x=960, y=520, z=1.1, rate=0.05),
  chars=[C('you', [960, 560, 1.0], 'q_left', 'shock', [A(R(0), 'stare')], mode='bust', light=DAWN)], dof=dict(focus=1.0, dof=6.75), energy='push 5 %/s')
S(466.40, 'cabin_dawn', 'mattress_dip', 'dawn_queen', 'theirs', 'ECU', 'the mattress sinks under her; black satin spreads over the blanket beside Noah\'s shoe', FA(x=960, y=600, z=1.2, rate=0.10),
  chars=[C('queen', [960, 640, 520], 'front', 'queen_still', [A(w(191, 'sits'), 'sit_beside', dur=0.5)], mode='hands', stage=2, note='skirt and hand only')],
  energy='fabric spreading, mattress sinking, fast push')
S(480.55, 'cabin_dawn', 'queen_face', 'dawn_queen', 'theirs', 'ECU', 'ECU of her red irises and pinpoint pupils, unblinking', FA(x=960, y=470, z=1.6, rate=0.10),
  chars=[C('queen', [960, 520, 1.15], 'front', 'queen_grin', [A(R(0), 'stare')], mode='bust', stage=3)], energy='eyes locked, red glow pulsing, fast push')
S(509.10, 'mess_porch', 'boot_ecu', 'run', 'ours', 'ECU', 'Tess\'s boot smashes a slat', HH(x=960, y=600, z=1.2, rate=0.10, shake=26),
  chars=[C('tess', [960, 640, 600], 'profile_left', 'angry', [A(w(209, 'box'), 'kick')], mode='legs')], energy='boot impact, splinters at the lens')
S(509.95, 'mess_porch', 'porch_run', 'run', 'ours', 'MS', 'the crate splits apart; the bell rolls out onto the boards', HH(x=1080, y=700, z=1.1, rate=0.03, shake=24),
  chars=[C('tess', 'tess_crate', 'profile_left', 'angry', [A(w(209, 'apart'), 'kick')])], energy='slats flying, bell rolling, beam strobing')
S(535.30, 'mess_porch', 'bell_ecu', 'bell_hit', 'ours', 'ECU', 'the padlock strikes the bell rim: a spark of flashlight glare', FA(x=1000, y=600, z=1.4, rate=0.12, hit=[(w(220, 'hits'), 18)]),
  energy='impact, the rim jumping, glare flare')
S(535.95, 'mess_porch', 'porch_run', 'bell_hit', 'ours', 'WS', 'Tess with the ringing bell, its rim still shaking; the dark camp behind', PU(x=1000, y=600, z=1.3, rate=-0.05),
  chars=[C('tess', 'tess_crate', 'profile_left', 'angry', [A(R(0), 'hold_up', prop='padlock', side=-1)])], energy='bell vibrating, pull-out, beam on the bell')
S(Wc(235, 'name', off=-0.1), 'cabin_now', 'wide', 'red', 'ours', 'ECU', 'his mouth on your name: the gap teeth, a stubble shadow spreading', FA(x=960, y=600, z=1.5, rate=0.10),
  chars=[C('noah_grown', [960, 480, 1.6], 'front', 'shaken', [A(R(0), 'age', t1=R(-0.05), part='stubble', start=0.6)], mode='bust', light=RED)], energy='stubble spreading, fast push')
S(573.40, 'cabin_now', 'bunk_hit', 'red', 'ours', 'ECU', 'his shoulder slams into the top bunk; the frame jumps, dust bursts', HH(x=960, y=480, z=1.3, rate=0.10, hit=[(w(239, 'shoulder'), 14)]),
  energy='impact, the bunk jumping, dust burst')
S(605.95, 'cabin_dawn', 'you_face', 'dawn_break', 'theirs', 'ECU', 'your face: terror, mouth open, no sound', FA(x=960, y=520, z=1.3, rate=0.12),
  chars=[C('you', [960, 560, 1.3], 'front', 'scream', [A(R(0), 'freeze')], mode='bust', light=RED)], energy='fast push 12 %/s, red light flickering on the face')
S(606.75, 'mirror_world', 'feet', 'red', 'mirror', 'ECU', 'her toes curl over the edge of the step below yours', P(x=1040, y=860, z=1.5, rate=0.05),
  chars=[C('queen', [1040, 900, 900], 'front', 'queen_still', [A(R(0), 'toes_curl')], mode='feet', stage=3)], energy='toes curling, step edge glowing')
S(628.55, 'black', 'black', 'black', 'black', 'BLACK', 'pure black for 0.4 s after the glass goes dark', cam('push', x=960, y=540, z=1.0, rate=0.0), tr='black', captions=False,
  energy='black (the sub-drop tail)')
S(690.95, 'cabin_now', 'floor_end', 'phone_glow', 'ours', 'ECU', 'your face over the phone: the click sinks in', FA(x=960, y=520, z=1.2, rate=0.08),
  chars=[C('you', [960, 560, 1.1], 'front', 'fear', [A(R(0), 'stare')], mode='bust', light=dict(rim='#ff4060', rim_a=60, side=-1, key=-0.4, under='#3a1018'))], energy='fast push, the phone\'s faint red under your chin')
