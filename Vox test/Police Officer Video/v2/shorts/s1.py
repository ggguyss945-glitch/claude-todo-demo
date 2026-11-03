"""Short 1: THE OTHER GENTLEMAN (shorts_spec.json S1), built only from the owner's narration.

Voice changes from the plan (no new recordings):
  B1 hook   = line 0 words 0-10 ("If a police officer ever knocks on your door after midnight...") + line 1
  B9 subscribe (on screen only) rides line 52 "His fingers are spread exactly like yours." (palm hits the glass = press)
  B14       = line 126 "you finally see his face."
  B18.5     = line 25 (officer) "We just need to establish which one of you belongs here." -> the open question
  B19 end   = line 26 "If this happens, there are seven rules you need to follow." under the FULL VIDEO card
  B20       = tail: black, two knocks (frame 1's sound), comments panel, REWIND
HUD: 12:36 AM clock + ID MATCH meter 0 -> 20 -> 40 -> 50 -> 60 -> 80 -> 99 ERROR -> 100 %.
"""
from film import P, DA, _A, ex, stare, smile, grin, tilt, lean, knk_at, creep, look_side, snap, tremble
import vfx
from vfx import RED, AMBER, BLUE, WHITE, VH

OFF, DBL, YOU = 'officer', 'double', 'you'


def voice(E):
    E.voice(1, [dict(i=0, words=(0, 10)), dict(i=1)], inner=0.24, kw=['MIDNIGHT', 'YOU'])
    E.voice(9, [dict(i=52)], kw=['YOURS'])
    E.voice(14, [dict(i=126, match='you finally see his face.')], kw=['FACE'])
    E.B(12)['kw'] = ['NAME']
    E.B(13)['kw'] = ['YOURS']
    E.insert(18, 18.5, [dict(i=25)], kw=['WHICH ONE'])
    E.voice(19, [dict(i=26)], kw=['SEVEN RULES'])
    if E.has_nl('S1-N2'): E.voice(9, [E.nl('S1-N2')], kw=['SUBSCRIBES', 'FACE'])       # spoken subscribe (optional)
    if E.has_nl('S1-N3'): E.voice(19, [E.nl('S1-N3')], kw=['SEVEN RULES', 'FULL VIDEO'])
    E.B(10)['kw'] = ['CLEAR THINGS UP']
    E.tail(20, 1.3)
    E.tension_after = 12
    E.tension = 1.1
    E.gap(15, 0.2); E.gap(16, 0.18); E.gap(17, 0.2)


def stage(E):
    t = E.t
    # ------------------------------------------------------------------ B1 hook: knocks on the lens, the grin, the house
    T0 = 1.55
    door_hook = dict(ppl=[P(OFF, at=DA(0.0, 0.75), act=_A(ex('calm_smirk'), stare(-1), grin(-0.6), lean(-1.4, 3.2, 1.35),
                                                          knk_at(T0 + 0.05, 2, 0.28, 0, 1.3), creep(4, 4, None)), lean=True)],
                     py=-70, hit=[T0 + 0.05, T0 + 0.33], z1=1.12)
    E.shot(1, 0.0, E.custom('door', p=door_hook, T=T0, talk=False), z=1.5, push=0.05, name='hook door')
    E.sfx(1, 0.05, 'knock_door', 0, space='doorbell_mic', kind='hit', n=2, spacing=0.28, force=1.0, material='glass')
    E.sfx(1, 0.05, 'impact_hit', -3, kind='hit', size=1.0)
    E.ev('slam', 1, 0.05, text='KNOCK', c=WHITE, y=0.30 * VH, size=140, dur=0.24, rot=-6, shake=True)
    E.ev('slam', 1, 0.33, text='KNOCK', c=WHITE, y=0.36 * VH, size=150, dur=0.26, rot=5, shake=True, gain=-2)
    E.shot(1, 'w:ever', E.film(28.95), push=0.06, name='peep officer')
    E.shot(1, 'w:after', E.custom('bust', T=44.0, talk=False, p=dict(who=OFF, bg='porch', cx=960, cy=560, scale=1.2, ecu=True,
                                                                    act=_A(stare(-1), smile(-0.2, 1.4, 1.0), tilt(0.4, 16, 1.2)),
                                                                    cam=dict(mv='push', x=960, y=600, z=1.0, rate=0.05))),
           cy=560, push=0.04, name='officer ECU low')
    E.hud(1, 0.0, clock='12:36 AM', title='ID MATCH', value='0%', meter=0.0, accent=RED, pop=False)
    E.hud(1, ('w', 'midnight'), clock='12:36 AM', clock_pop=True)
    c1 = E.clip(1, 1)
    E.shot(1, c1['dst_on'] - 0.1, E.film(9.35), push=0.05, name='your house')
    E.shot(1, ('w', 'belongs', 0, -0.1), E.custom('door', T=16.0, talk=False, p=dict(
        ppl=[P(OFF, at=DA(0.0, 0.8), act=_A(stare(-1), grin(-0.5), lean(-0.2, 1.6, 1.25), tilt(0.4, 14, 1.0), creep(4, 3, None)),
               lean=True)], py=-100, z1=1.15)), z=1.35, push=0.06, name='door grin')
    E.ev('slam', 1, ('w', 'belongs'), text="DON'T PROVE\nYOU LIVE THERE", c=RED, y=0.36 * VH, size=150, dur=1.45, big=True, shake=True)
    E.ev('flash', 1, ('w', 'belongs'), c='#ff2020', k=0.35, dur=0.08)
    E.mus(1, 0.0, 'braam', 0.8); E.mus(1, ('w', 'belongs'), 'hit', 0.85)

    # ------------------------------------------------------------------ B2 the report + bodycam
    E.shot(2, 0.0, E.sync(2), name='officer report')
    E.ev('tag', 2, ('w', 'unauthorized'), text='UNAUTHORIZED PERSON', x=vfx.SAFE_CX, y=0.30 * VH, style='red', dur=1.4, size=44)
    E.shot(2, ('f', 0.7), E.film(48.65), cy=760, z=1.05, push=0.05, name='bodycam chest')
    E.ev('bodycam', 2, ('f', 0.7), dur=E.beat(2)['t1'] - E.t(2, ('f', 0.7)))
    E.sfx(2, ('f', 0.7), 'bodycam_beep', -4, space='outside', n=2)

    # ------------------------------------------------------------------ B3 you live here
    E.shot(3, 0.0, E.sync(3), name='you behind door')
    E.ev('bubble', 3, ('w', 'live'), lines=['I LIVE HERE.'], x=vfx.SAFE_CX + 60, y=0.30 * VH, dur=1.2, size=46)
    E.sfx(3, 0.05, 'breath', -8, space='close', kind_='nervous', dur=1.2)

    # ------------------------------------------------------------------ B4 the other gentleman
    E.shot(4, 0.0, E.sync(4), name='officer snap')
    E.sfx(4, ('w', 'other'), 'stinger', -8, kind='hit')

    # ------------------------------------------------------------------ B5 the back seat
    E.shot(5, 0.0, E.sync(5), name='peep -> car')
    E.ev('tag', 5, ('w', 'back'), text='UNKNOWN', x=vfx.SAFE_CX + 120, y=0.28 * VH, style='red', dur=1.3, size=44)
    E.sfx(5, 0.3, 'car_idle', -18, kind='bed', space='street', dur=round(E.beat(6)['t1'] - E.t(5, 0.3), 2))

    # ------------------------------------------------------------------ B6 the habit
    E.shot(6, 0.0, E.sync(6), name='his hands')
    E.ev('tag', 6, ('w', 'rubbing'), text='HABIT', x=vfx.SAFE_CX - 160, y=0.30 * VH, style='white', dur=1.6, size=46)
    E.hud(6, ('w', 'ring'), value='20%', meter=0.2)

    # ------------------------------------------------------------------ B7 split: his hands / your hands
    E.shot(7, 0.0, _split(E, E.film(67.2), E.sync(7)), push=0.02, name='split hands')
    E.ev('split_labels', 7, 0.0, top='HIM', bot='YOU', dur=E.beat(7)['t1'] - E.beat(7)['t0'])
    E.ev('glitch', 7, 0.0, dur=0.12, k=0.7)

    # ------------------------------------------------------------------ B8 the chipped licence
    E.shot(8, 0.0, E.film(116.3), name='licence on glass')
    E.shot(8, 'w:same', E.film(124.5), name='your licence')
    E.ev('slam', 8, ('w', 'same'), text='SAME', c=RED, y=0.34 * VH, size=200, dur=0.8, shake=True)
    E.hud(8, ('w', 'same'), value='40%', meter=0.4)

    # ------------------------------------------------------------------ B9 the palm on the glass = SUBSCRIBE press
    E.shot(9, 0.0, E.film(148.62), name='palm on glass', fx=dict(no_punch=False))
    press = E.t(9, 0.2)
    E.ev('subscribe', None, press)
    E.flags['subscribe_t'] = round(press, 3)
    E.sfx(None, press - 0.02, 'knock_door', -6, space='street', kind='hit', n=1, material='glass', force=0.8)
    E.hud(None, E.wf(9, 'yours', 'face', frac=0.8), value='50%', meter=0.5)

    # ------------------------------------------------------------------ B10 the complaint through the slot
    E.shot(10, 0.0, E.sync(10), name='officer at doorbell')
    E.shot(10, ('f', 0.6), E.film(287.2), name='mail slot')
    E.sfx(10, ('f', 0.6), 'mail_slot', -2, space='inside', paper=True)

    # ------------------------------------------------------------------ B11 the clothes you're wearing
    E.shot(11, 0.0, E.sync(11), name='you reading')
    b11 = E.beat(11)
    E.ev('complaint', 11, 0.05, rows=[('HEIGHT:', "5'11\""), ('HAIR:', 'BROWN'), ('WEARING:', 'GREY HOODIE')],
         hl={0: E.t(11, 0.25), 1: E.t(11, 0.6), 2: E.w(11, 'wearing')}, dur=b11['t1'] - b11['t0'] - 0.05, y=0.33 * VH)
    E.hud(11, ('w', 'right'), value='60%', meter=0.6)

    # ------------------------------------------------------------------ B12 the complainant's name + tension gap
    b12 = E.beat(12)
    T12 = E.long(12, b12['t0'])
    E.shot(12, 0.0, E.custom('bust', T=T12, talk=False, p=dict(who=YOU, bg='hall', cx=960, cy=600, scale=1.0,
                                                               act=_A(ex('nervous'), tremble(0.6)),
                                                               cam=dict(mv='push', x=960, y=600, z=1.0, rate=0.05))),
           push=0.05, name='you read the name')
    E.ev('complaint', 12, 0.05, rows=[('ADDRESS:', '144 ELM STREET'), ('COMPLAINANT:', 'DANIEL J. REED')], blur_row=1,
         reveal=(b12['off'] + 0.1, b12['t1'] + 0.35), hl={1: E.w(12, 'name')}, dur=b12['t1'] - b12['t0'] + 0.9, y=0.33 * VH)
    E.sfx(None, b12['off'] + 0.1, 'riser', -6, kind='transient', dur=round(b12['t1'] - b12['off'] + 0.1, 2))

    # ------------------------------------------------------------------ B13 IT'S YOURS (twist A)
    ty = E.w(13, 'yours')
    E.shot(13, 0.0, E.sync(13), z=1.15, push=0.08, name='name ECU')
    E.ev('slam', 13, ('w', 'yours'), text="IT'S YOURS.", c=RED, y=0.47 * VH, size=190, dur=0.95, big=True, shake=True, amp=22)
    E.ev('flash', 13, ('w', 'yours'), c='#ff1010', k=0.6, dur=0.07)
    E.hud(13, ('w', 'yours'), value='80%', meter=0.8, flash=True)
    E.sfx(None, ty, 'braam', 0, kind='hit'); E.sfx(None, ty, 'sub_drop', -2, kind='hit')
    E.flags['twist_t'] = round(ty, 3)
    E.flags['music_align'] = (ty, 53.2)               # From Hell's loud section lands on "It's yours."

    # ------------------------------------------------------------------ B14-B15 his face, almost yours
    E.shot(14, 0.0, E.sync(14), name='man under porch light')
    E.ev('tag', 14, ('f', 0.25), text='GREY COAT', x=vfx.SAFE_CX + 150, y=0.27 * VH, style='white', dur=1.2, size=44)
    E.shot(15, 0.0, E.sync(15), name='double ECU')
    E.ev('tag', 15, 0.2, text='SCAR: WRONG SIDE', x=vfx.SAFE_CX, y=0.25 * VH, style='red', dur=1.3, size=42)
    E.ev('tag', 15, 0.7, text='RING: WRONG HAND', x=vfx.SAFE_CX, y=0.31 * VH, style='red', dur=0.9, size=42)
    E.hud(15, ('w', 'almost'), value='99% ERROR', meter=0.99)
    E.ev('glitch', 15, ('w', 'almost'), dur=0.12, k=0.8)

    # ------------------------------------------------------------------ B16-B18 "That's him" in your voice
    E.shot(16, 0.0, E.sync(16), name='double talks')
    b17 = E.beat(17)
    E.shot(17, 0.0, E.sync(17), name='double behind waveform')
    E.ev('panel_dim', 17, 0.0, k=0.35, dur=b17['t1'] - b17['t0'])
    E.ev('wave', 17, 0.0, title='VOICE MATCH', rows=[dict(label='YOU  (12:36 AM)', color=AMBER, seed=3, live=False),
                                                       dict(label='HIM  (BACK SEAT)', color='#ff5a5f', seed=3, live=False)],
         play=(b17['t0'], b17['t1']), dur=b17['t1'] - b17['t0'], y=0.24 * VH, h=420)
    E.ev('stamp', 17, ('w', 'voice'), text='MATCH 100%', c=RED, y=0.47 * VH, size=92, dur=1.0)
    E.hud(17, ('w', 'voice'), value='100%', meter=1.0, flash=True)
    E.sfx(17, 0.0, 'radio_static', -14, space='close', dur=0.4, amount=0.4)
    E.shot(18, 0.0, E.sync(18), z=1.3, name='double at doorbell')
    E.ev('slam', 18, ('w', 'man'), text='THE MAN\nIN MY HOUSE', c=RED, y=0.36 * VH, size=160, dur=1.25, big=True, shake=True)
    E.ev('flash', 18, ('w', 'man'), c='#ff1010', k=0.45, dur=0.07)

    # ------------------------------------------------------------------ B18.5 which one of you belongs here
    E.shot(18.5, 0.0, E.sync(18.5), name='officer: which one')
    E.ev('slam', 18.5, ('w', 'which'), text='WHICH ONE\nOF YOU?', c=WHITE, y=0.34 * VH, size=150, dur=1.5)
    E.hud(18.5, 0.0, clock='12:41 AM', clock_pop=True)

    # ------------------------------------------------------------------ B19 end card (line 26 carries it)
    b19 = E.beat(19)
    E.shot(19, 0.0, E.film(78.05), push=0.03, name='street pull 7 rules')
    E.ev('panel_dim', 19, 0.0, k=0.3, dur=b19['t1'] - b19['t0'] + 0.1)
    hits = [b19['t0'] + 0.02, E.wf(19, 'happens', 'keep', frac=0.3) + 0.1, E.wf(19, 'seven', 'full', frac=0.6)]
    E.ev('endcard', 19, 0.0, question='WHICH ONE OF YOU\nBELONGS HERE?', sub='FULL VIDEO ON THE CHANNEL', hits=hits,
         dur=b19['t1'] - b19['t0'] + 0.02, y=0.39 * VH, title='IF A POLICE OFFICER KNOCKS AT MIDNIGHT...')
    E.flags['end_t'] = round(b19['t0'], 3)
    E.hud(19, 0.0, hide=True, pop=False)

    # ------------------------------------------------------------------ B20 tail: knocks over black, comments, REWIND
    b20 = E.beat(20)
    E.shot(20, 0.0, _black(), name='black', fx=dict(no_fill=True, no_punch=True))
    E.ev('comments', 20, 0.0, prompt='COMMENT "BACK SEAT"\nIF YOU\'D KEEP THE DOOR SHUT', word='BACK SEAT', dur=b20['t1'] - b20['t0'] - 0.14,
         y=0.30 * VH)
    E.sfx(20, 0.55, 'knock_door', -1, space='doorbell_mic', kind='hit', n=2, spacing=0.28, force=1.0, material='glass')
    rw = E.dur - 8 / 60.0
    E.shot(None, rw, E.custom('door', p=dict(door_hook), T=T0 - 8 / 60.0, talk=False), z=1.5, push=0.05, name='rewind -> frame 1',
           fx=dict(no_fill=True, no_punch=True, rewind=True))
    E.ev('rewind', None, rw, dur=8 / 60.0)


def _split(E, top, bot):
    from stage import SplitSrc
    return SplitSrc(top, bot, z=(0.62, 0.62), cy=(560, 600))


def _black():
    from stage import BlackSrc
    return BlackSrc()
