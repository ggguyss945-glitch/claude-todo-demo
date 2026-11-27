"""Short 3: NEVER CORRECT HIM (shorts_spec.json S3), built only from the owner's narration.

Voice changes from the plan (no new recordings):
  + 3.5     line 151 "You almost say it."
  (line 156 "The next question will be more personal." dropped: the subscribe press must land by 50 %)
  B14 (moved before B13) line 174 "After a few seconds, he turns off his camera.": his finger tap on the bodycam is the
            SUBSCRIBE press (on screen only, 49-50 %); then B13 line 163 over the split screen him / you
  B18       the whole line 229 "He asked a few questions to make sure he had the right family."
  B24 end   line 264 "You tell her to come away from the door." under DOES SHE OPEN THE DOOR? / FULL VIDEO ON THE CHANNEL
  B24-B25   the card from its first frame to the REWIND; tail 0.75 s: knocking at her door, the pen click (frame 1's
            sound), REWIND 10 frames. Tension gap: right before "She tells you he called earlier" (the twist).
Premise in the first 3 s: WHO REALLY LIVES HERE? over the quiz, the double labelled HIM (SAYS HE'S YOU) on "Green,".
HUD: QUESTION 1/5 -> 5/5 with the scoreboard HIM / YOU, clock 12:51 AM -> 1:14 AM -> 1:16 AM.
"""
from film import P, DA, _A, ex, stare, smile, grin, tilt, lean, creep, snap, look_side, tremble
import vfx
from vfx import RED, AMBER, BLUE, PINK, GREEN, WHITE, VH

OFF, DBL, YOU, MUM = 'officer', 'double', 'you', 'mum'
RW = 10 / 60.0                       # REWIND: 10 frames at 60 fps back to frame 1
SUB_XY = (497, 1415)                 # SUBSCRIBE button centre (under the caption)
CAM_XY = (600, 1600)                 # his bodycam (the button flies out of the camera his finger taps)


def voice(E):
    E.B(1)['kw'] = ['KITCHEN TILES']
    E.insert(3, 3.5, [dict(i=151)], kw=['ALMOST'])
    E.voice(13, [dict(i=163)], kw=['LESS CONVINCING'])
    E.voice(18, [dict(i=229)], kw=['RIGHT FAMILY'])
    E.voice(24, [dict(i=264)], kw=['DOOR'])
    if E.has_nl('S3-N1'): E.voice(13, [E.nl('S3-N1')], kw=['SUBSCRIBES', 'REAL'])
    if E.has_nl('S3-N2'): E.voice(24, [E.nl('S3-N2')], kw=['OPEN', 'FULL VIDEO'])
    E.move(14, 12)                         # "he turns off his camera" first: his finger tap on the bodycam is the SUBSCRIBE press
    E.tail(25, 0.75)
    E.tension_after = 16                   # the silence lands right before 'She tells you he called earlier' (the twist)
    E.tension = 1.0
    E.gap(1, 0.2); E.gap(2, 0.2); E.gap(10, 0.2); E.gap(11, 0.2); E.gap(19, 0.18); E.gap(20, 0.18)


def stage(E):
    sc = dict(him='', you='')

    def score(bn, at, him=None, you=None):
        if him is not None: sc['him'] = him
        if you is not None: sc['you'] = you
        E.hud(bn, at, score=(sc['him'] or '-', sc['you'] or '-'))

    # ------------------------------------------------------------------ B1 the quiz starts at your peephole
    E.shot(1, 0.0, E.sync(1), z=1.75, push=0.03, name='peep officer + notebook')
    E.hud(1, 0.0, title='QUESTION', value='1/5', accent=BLUE, clock='12:51 AM', pop=False)
    score(1, 0.0, '-', '-')
    E.sfx(1, 0.0, 'pen_click', 0, space='close', kind='hit', n=1)
    E.sfx(1, 0.02, 'impact_hit', -6, kind='hit', size=0.7)
    E.mus(1, 0.0, 'braam', 0.6)
    E.ev('label', 1, 0.15, text='WHO REALLY', x=vfx.SAFE_CX, y=0.245 * VH, size=84, c=WHITE, dur=1.85)
    E.ev('label', 1, 0.15, text='LIVES HERE?', x=vfx.SAFE_CX, y=0.245 * VH + 92, size=84, c=RED, dur=1.85)
    # ------------------------------------------------------------------ B2 "Green."
    E.shot(2, 0.0, E.sync(2), name='double: green')
    E.ev('label', 2, 0.02, text='HIM', x=vfx.SAFE_CX, y=0.25 * VH, size=130, c=RED, dur=E.beat(2)['t1'] - E.beat(2)['t0'] + 0.05)
    E.ev('label', 2, 0.1, text="(SAYS HE'S YOU)", x=vfx.SAFE_CX, y=0.25 * VH + 86, size=62, c=WHITE, dur=E.beat(2)['t1'] - E.beat(2)['t0'] - 0.03)
    score(2, ('w', 'green'), him='Y')
    # ------------------------------------------------------------------ B3 your tiles are blue; you almost say it
    E.shot(3, 0.0, E.film(370.7), name='your kitchen')
    E.shot(3, ('f', 0.45), E.sync(3, dt=0.0), z=1.1, name='tiles ECU')
    E.shot(3.5, 0.0, E.sync(3.5), name='you: lips pressed')
    E.sfx(3.5, 0.1, 'breath', -6, space='close', kind_='held', dur=1.4)
    # ------------------------------------------------------------------ B4 RULE 5 over the officer and HIM at your door (no static card)
    b4 = E.beat(4)
    T4 = E.long(4, b4['t0'])
    E.shot(4, 0.0, E.custom('door', T=T4, talk=False, p=dict(
        ppl=[P(OFF, at=DA(-0.3, 1.15), act=_A(stare(-1), smile(0.2, 2.0, 0.6), creep(5, 3, None))),
             P(DBL, at=DA(0.3, 1.2), act=_A(stare(-1), grin(0.4), creep(-4, 3, None)), detail=None)], py=-80, z1=1.15)),
           z=1.0, cx=960, cy=470, push=0.07, name='officer + HIM at the door: rule 5')
    E.ev('tag', 4, 0.05, text='RULE #5', x=vfx.SAFE_CX, y=0.215 * VH, style='red', dur=b4['t1'] - b4['t0'] - 0.1, size=84)
    E.ev('tag', 4, 0.35, text='HIM', x=vfx.SAFE_CX + 200, y=0.30 * VH, style='white', dur=b4['off'] - b4['t0'] - 0.4, size=66)
    E.ev('slam', 4, ('off', -0.05), text="DON'T CORRECT\nHIM.", c=RED, y=0.40 * VH, size=150, dur=b4['t1'] - b4['off'] + 0.05,
         big=True, shake=True)
    E.ev('flash', 4, 0.0, c='#ff1010', k=0.35, dur=0.07)
    E.hud(4, 0.0, hide=True, pop=False)
    # ------------------------------------------------------------------ B5 asking you both (both heads snap to the lens)
    b5 = E.beat(5)
    T5 = E.long(5, b5['t0']); tb = E.long(5, E.w(5, 'both'))
    E.shot(5, 0.0, E.custom('door', T=T5, talk=False, p=dict(
        ppl=[P(OFF, at=DA(-0.3, 1.15), act=_A(stare(-1), look_side(T5 - 1.0, 0.8, 0.1), snap(tb, 0.8, 0.0), smile(0.5, 2.0, 0.7))),
             P(DBL, at=DA(0.3, 1.2), act=_A(stare(-1), look_side(T5 - 1.0, -0.8, 0.1), snap(tb + 0.04, -0.8, 0.0), grin(1.2)),
               detail=None)], py=-80, z1=1.1)), z=1.0, cx=960, cy=470, name='officer + double: both snap')
    E.hud(5, 0.0, hide=False, pop=False)
    E.ev('tag', 5, ('w', 'both', 0, 0.12), text='HIM', x=vfx.SAFE_CX + 170, y=0.27 * VH, style='red', dur=1.1, size=46)
    E.sfx(5, ('w', 'both'), 'stinger', -8, kind='hit')
    # ------------------------------------------------------------------ B6-B8 the questions
    b6 = E.beat(6)
    E.shot(6, 0.0, E.sync(6), z=1.1, name='notebook')
    E.hud(6, 0.0, value='2/5')
    T6 = E.long(6, E.t(6, ('f', 0.55)))
    E.shot(6, ('f', 0.55), E.custom('bust', T=T6, talk=[dict(who='D', t=T6 + 0.05, end=T6 + 0.6, en='Biscuit.')],
                                    p=dict(who=DBL, bg='porch', cx=960, cy=570, scale=1.0, act=_A(stare(-1), smile(0.0, 1.5, 0.6)),
                                           cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.05))), name='double answers')
    score(6, ('off', 0.1), him='YY')
    E.shot(7, 0.0, E.film(393.0), name='double glances')
    E.hud(7, 0.0, value='3/5')
    E.ev('tag', 7, ('f', 0.05), text='HE CHECKS THE OFFICER', x=vfx.SAFE_CX, y=0.29 * VH, style='red',
         dur=E.beat(7)['t1'] - E.t(7, ('f', 0.05)) - 0.02, size=62)
    score(7, ('off', 0.05), him='YYY')
    b8 = E.beat(8)
    E.shot(8, 0.0, E.film(395.7), name='you sweating')
    E.hud(8, 0.0, value='4/5')
    E.shot(8, ('w', 'mother', 0, -0.05), E.film(390.3), name='flash: mum by her phone', fx=dict(no_fill=True))
    E.shot(8, ('w', 'mother', 0, 0.38), E.film(396.6), name='you again')
    E.sfx(8, ('w', 'mother'), 'phone_vibrate', -12, space='phone', n=1)
    score(8, ('w', 'worried'), him='YYY~')
    # ------------------------------------------------------------------ B9 Don't.
    E.shot(9, 0.0, E.film(423.2), z=1.3, name='hand grips the table')
    E.ev('slam', 9, ('w', 'don'), text="DON'T.", c=RED, y=0.36 * VH, size=230, dur=0.6, big=True, shake=True, amp=20)
    # ------------------------------------------------------------------ B10 the photograph
    E.shot(10, 0.0, E.film(410.6), name='hallway photo')
    E.hud(10, 0.0, value='5/5')
    E.shot(10, ('f', 0.42), E.sync(10), z=1.4, name='officer asks')
    E.ev('tag', 10, ('w', 'picture'), text='YOU NEVER MENTIONED IT', x=vfx.SAFE_CX, y=0.29 * VH, style='red', dur=1.0, size=40)
    # ------------------------------------------------------------------ B11-B12 "My mother." It was your father.
    E.shot(11, 0.0, E.sync(11), name='double: my mother')
    score(11, ('w', 'mother'), him='YYY~N')
    E.ev('stamp', 11, ('w', 'mother', 0, 0.15), text='WRONG', c=RED, y=0.36 * VH, size=110, dur=0.9)
    E.shot(12, 0.0, E.sync(12), name='photo insert')
    E.ev('tag', 12, ('w', 'father'), text='TAKEN BY: DAD', x=vfx.SAFE_CX, y=0.30 * VH, style='white', dur=1.0, size=46)
    # ------------------------------------------------------------------ B14 the camera goes off: his finger tap = SUBSCRIBE press
    b14 = E.beat(14)
    press = E.w(14, 'turns') + 0.12                    # his index finger pokes the bodycam (press_bodycam: poke = start + 0.42)
    T14 = E.long(14, b14['t0']); Tp = E.long(14, press)
    E.shot(14, 0.0, E.custom('bust', T=T14, talk=False, p=dict(
        who=OFF, bg='porch', cx=960, cy=330, scale=0.62,
        act=_A(stare(-1), smile(0.3, 2.5, 0.5), lambda a, s_: a.press_bodycam(Tp - 0.42, on=False)),
        cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.03))), cx=960, cy=560, z=1.0, push=0.03,
           name='officer: finger to the bodycam', fx=dict(no_cuts=True))
    E.ev('bodycam', 14, 0.0, off=press, dur=b14['t1'] - b14['t0'])
    E.ev('subscribe', None, press, y=SUB_XY[1], x=SUB_XY[0], hand=None, from_=CAM_XY, lead=0.4)
    E.flags['subscribe_t'] = round(press, 3)
    E.ev('tag', None, press + 0.1, text='CAMERA OFF', x=vfx.SAFE_CX, y=0.29 * VH, style='red', dur=1.2, size=66)
    # ------------------------------------------------------------------ B13 split screen: him / you (you stay quiet)
    b13 = E.beat(13)
    from stage import SplitSrc
    E.shot(13, 0.0, SplitSrc(E.film(432.6, speed=0.85), E.film(395.6), z=(0.62, 0.62), cy=(760, 640),
                             glitch=(E.wf(13, 'less', 'real', frac=0.6) - 0.02, E.wf(13, 'less', 'real', frac=0.6) + 0.16)), push=0.015, name='split him / you')
    E.ev('split_labels', 13, 0.0, top='HIM', bot='YOU', dur=b13['t1'] - b13['t0'])
    score(13, ('w', 'quiet') if not E.has_nl('S3-N1') else ('f', 0.3), you='Y')
    # ------------------------------------------------------------------ B15-B16 you call your mother
    b15, b16 = E.beat(15), E.beat(16)
    E.shot(15, 0.0, E.film(540.0), name='phone bg')
    E.ev('phone', 15, 0.0, states=[(b15['t0'], 'calling'), (b15['t1'] - 0.15, 'connected')], name='MUM', dur=b15['t1'] - b15['t0'],
         y=0.40 * VH, scale=1.4)
    E.hud(15, 0.0, clock='1:14 AM', hide=False)
    E.shot(16, 0.0, E.sync(16), name='mum answers')
    # ------------------------------------------------------------------ B17 he called her (twist starts)
    tcall = E.w(17, 'called')
    E.shot(17, 0.0, E.sync(17), name='mum standing')
    E.ev('slam', 17, ('w', 'called'), text='HE CALLED\nHER', c=RED, y=0.34 * VH, size=170, dur=1.1, big=True, shake=True)
    E.ev('flash', None, tcall, c='#ff1010', k=0.45, dur=0.07)
    E.sfx(None, tcall, 'braam', 0, kind='hit'); E.sfx(None, tcall, 'sub_drop', -2, kind='hit')
    E.flags['twist_t'] = round(tcall, 3)
    E.flags['music_align'] = (tcall, 50.4)
    # ------------------------------------------------------------------ B18-B21 the answer key
    b18, b21 = E.beat(18), E.beat(21)
    E.shot(18, 0.0, E.sync(18), name='officer bg for notebook')
    t_nb = E.w(18, 'questions')
    E.ev('panel_dim', None, t_nb, k=0.3, dur=E.w(21, 'took') - 0.05 - t_nb)
    E.ev('notebook', None, t_nb, rows=['FIRST PET', 'SCHOOL', 'PHOTO: FATHER'],
         ticks=[E.w(19, 'pet'), E.w(20, 'school'), E.w(21, 'photograph')], dur=E.w(21, 'took') - 0.05 - t_nb, y=0.36 * VH)
    E.shot(19, 0.0, E.film(565.2), name='notebook insert')
    E.shot(20, 0.0, E.film(562.6), z=1.15, name='officer writes')
    E.shot(21, 0.0, E.film(565.7), z=1.2, name='notebook insert 2')
    E.shot(21, ('w', 'took', 0, -0.05), E.film(608.0), z=1.15, name='flash: double smiling')
    E.ev('slam', 21, ('w', 'took'), text='NOW HE\nKNOWS', c=RED, y=0.30 * VH, size=170, dur=b21['t1'] - E.w(21, 'took') + 0.1, big=True,
         shake=True)
    E.ev('flash', 21, ('w', 'took'), c='#ff1010', k=0.5, dur=0.07)
    # ------------------------------------------------------------------ B22-B23 knocking at her door; he looks just like you
    E.shot(22, 0.0, E.sync(22), name='her porch: knock')
    E.hud(22, 0.0, clock='1:16 AM')
    E.sfx(22, ('w', 'knocking'), 'knock_door', -3, space='phone', kind='hit', n=3, spacing=0.3, force=0.9)
    E.shot(23, 0.0, E.film(599.55), name='curtain')
    E.sfx(23, 0.05, 'door_creak', -12, space='phone', dur=0.6)
    # ------------------------------------------------------------------ B24-B25 end card: DOES SHE OPEN THE DOOR? (to the REWIND)
    b24, b25 = E.beat(24), E.beat(25)
    rw = E.dur - RW
    E.shot(24, 0.0, E.film(601.6), name='her door from the street', fx=dict(no_cuts=True))
    E.ev('panel_dim', 24, 0.0, k=0.3, dur=rw - b24['t0'])
    tk = b25['t0'] + 0.1
    hits = [b24['t0'] + 0.02, b24['t0'] + 0.5, b24['t0'] + 0.95, tk]
    E.ev('endcard', 24, 0.0, question='DOES SHE\nOPEN THE DOOR?', hits=hits, dur=rw - b24['t0'], y=0.47 * VH,
         title='IF A POLICE OFFICER KNOCKS AT MIDNIGHT...')
    E.flags['end_t'] = round(b24['t0'], 3)
    E.hud(24, 0.0, hide=True, pop=False)
    E.sfx(None, tk - 0.2, 'knock_door', -6, space='phone', kind='hit', n=3, spacing=0.24, force=0.9)
    E.sfx(None, tk, 'pen_click', 0, space='close', kind='hit', n=1)
    E.sfx(None, tk, 'impact_hit', -3, kind='hit', size=1.0)
    c1 = E.clip(1)
    E.shot(None, rw, E.film(c1['a'] + (0.0 - c1['dst_a']) - RW), z=1.75, push=0.03, name='rewind -> frame 1',
           fx=dict(no_fill=True, no_punch=True, rewind=True))
    E.ev('rewind', None, rw, dur=RW)
