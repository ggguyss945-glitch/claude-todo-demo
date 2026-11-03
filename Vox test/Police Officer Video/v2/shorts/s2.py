"""Short 2: YOUR VOICE ON THE RADIO (shorts_spec.json S2), built only from the owner's narration.

Voice changes from the plan (no new recordings):
  B10       line 76 is not in the recording -> the first take of "I live here." (line 64) plays again (it IS the recording)
  + 2.5     line 65 "It's the sentence you said when he first arrived."
  + 8.5     line 72 "The officer presses a button on his radio."
  B13 subscribe (on screen only) rides line 54 "...don't give him a second recording." (hand over your mouth, the live
            waveform flattens as the button is pressed)
  + 17.5    line 99 "Then she says it again."
  + 20.5    line 104 "Try calling her yourself."
  B22 end   line 106 "Try again, and it will still be busy." under the card WHERE IS YOUR MOTHER? / FULL VIDEO ON THE CHANNEL
  B23       tail: radio insert, comments panel, the radio click (frame 1's sound), REWIND
HUD: PLAYBACK #1 -> #5 with a live waveform strip, clock 12:38 AM.
"""
from film import P, DA, _A, ex, stare, smile, grin, tilt, lean, creep, hand_mouth, tremble, radio
import vfx
from vfx import RED, AMBER, BLUE, PINK, GREEN, WHITE, VH

OFF, DBL, YOU = 'officer', 'double', 'you'


def voice(E):
    E.voice(1, [dict(i=64)], kw=['LIVE'])
    E.insert(2, 2.5, [dict(i=65)], kw=['FIRST ARRIVED'])
    E.B(2)['kw'] = ['OWN VOICE']
    E.insert(8, 8.5, [dict(i=72)], kw=['RADIO'])
    E.voice(10, [dict(i=76, alias=64)])
    E.voice(13, [dict(i=54, match="don't give him a second recording.")], kw=['SECOND RECORDING'])
    E.insert(17, 17.5, [dict(i=99)], kw=['AGAIN'])
    E.insert(20, 20.5, [dict(i=104)], kw=['YOURSELF'])
    E.voice(22, [dict(i=106)], kw=['STILL BUSY'])
    if E.has_nl('S2-N1'): E.voice(13, [E.nl('S2-N1')], kw=['SUBSCRIBES', 'VOICE'])
    if E.has_nl('S2-N2'): E.voice(22, [E.nl('S2-N2')], kw=['MOTHER', 'FULL VIDEO'])
    E.B(19)['kw'] = ['CLICK']
    E.tail(23, 1.3)
    E.tension_after = 18
    E.tension = 1.2
    E.gap(1, 0.22); E.gap(9, 0.18); E.gap(10, 0.22); E.gap(20, 0.22)


def stage(E):
    hud0 = dict(title='PLAYBACK', accent=BLUE, wave=True, wave_c='#5AB0FF', clock='12:38 AM')
    # ------------------------------------------------------------------ B1 your voice on the shoulder radio
    E.shot(1, 0.0, E.film(176.0), z=1.25, push=0.05, name='radio ECU')
    E.hud(1, 0.0, value='#1', **hud0)
    E.sfx(1, 0.0, 'police_radio_squelch', -2, space='close', kind='hit', kind_='key')
    E.sfx(1, 0.02, 'radio_click', 0, space='close')
    E.mus(1, 0.0, 'sub_drop', 0.6)
    # ------------------------------------------------------------------ B2 your own voice
    E.shot(2, 0.0, E.sync(2), name='you snap')
    E.ev('slam', 2, ('w', 'voice'), text='YOUR VOICE', c=AMBER, y=0.34 * VH, size=170, dur=0.9, shake=True)
    E.shot(2.5, 0.0, E.film(47.0), z=1.1, name='first time (hall)')
    E.ev('bubble', 2.5, 0.15, lines=['I LIVE HERE.'], x=vfx.SAFE_CX + 60, y=0.29 * VH, dur=1.5, size=46)
    E.ev('label', 2.5, 0.05, text='12:36 AM', x=vfx.SAFE_CX, y=0.21 * VH, size=56, c=AMBER, dur=1.6)
    E.ev('glitch', 2.5, 0.0, dur=0.1, k=0.6)
    # ------------------------------------------------------------------ B3 it plays again (waveform)
    b3 = E.beat(3)
    E.shot(3, 0.0, E.film(185.0), name='officer + panel bg')
    E.hud(3, 0.0, value='#2')
    E.ev('wave', 3, 0.0, title='SHOULDER RADIO', rows=[dict(label='PLAY 1', color='blue', seed=7, live=False),
                                                       dict(label='PLAY 2', color='red', seed=7, p=(b3['t0'], b3['t1'] + 3.0))],
         dur=b3['t1'] - b3['t0'], y=0.22 * VH, h=380)
    E.sfx(3, 0.0, 'radio_click', -3, space='outside')
    # ------------------------------------------------------------------ B4 something is wrong
    E.shot(4, 0.0, E.sync(4), name='peep officer radio')
    E.sfx(4, 0.1, 'radio_static', -16, space='outside', dur=1.5, amount=0.4)
    # ------------------------------------------------------------------ B5 the pause is too long
    b5 = E.beat(5)
    E.shot(5, 0.0, E.film(188.5), name='radio insert bg')
    E.ev('wave', 5, 0.0, title='PLAY 2  —  ANALYSIS', rows=[dict(label='I ... LIVE HERE', color='red', seed=9, live=False,
                                                                     marker=(0.22, 0.52, 'PAUSE TOO LONG'))],
         play=(b5['t0'], b5['t1']), dur=b5['t1'] - b5['t0'], y=0.22 * VH, h=330)
    E.ev('glitch', 5, ('w', 'long'), dur=0.1, k=0.5)
    # ------------------------------------------------------------------ B6 I... live here
    E.shot(6, 0.0, E.film(176.6), z=1.35, push=0.06, name='radio LED stutter')
    E.shot(6, 'w:live', E.film(178.7), z=1.1, name='you eyes wide')
    E.sfx(6, 0.0, 'police_radio_squelch', -4, space='close', kind_='burst')
    # ------------------------------------------------------------------ B7 the man in the car leaning forward
    E.shot(7, 0.0, E.sync(7), name='peep -> car')
    E.ev('tag', 7, ('w', 'car'), text='BACK SEAT', x=vfx.SAFE_CX + 130, y=0.27 * VH, style='red', dur=1.4, size=44)
    E.sfx(7, 0.2, 'car_idle', -18, kind='bed', space='street', dur=round(E.beat(8)['t1'] - E.t(7, 0.2), 2))
    # ------------------------------------------------------------------ B8 his lips are moving (practising)
    b8 = E.beat(8)
    T8 = E.long(8, b8['t0'])
    E.shot(8, 0.0, E.custom('car', T=T8, talk=[dict(who='D', t=T8 + 0.1, end=T8 + 1.1, en='I live here.')],
                            p=dict(expr='dead_stare', scale=0.55, cy=470, cam=dict(mv='push', x=985, y=470, z=1.35, rate=0.05))),
           z=1.15, name='lips moving')
    E.ev('ghost', 8, 0.1, text='i live here', y=0.52 * VH, dur=b8['t1'] - b8['t0'] - 0.1)
    E.ev('tag', 8, 0.35, text='PRACTISING', x=vfx.SAFE_CX, y=0.215 * VH, style='red', dur=1.0, size=44)
    E.sfx(8, 0.1, 'crowd_whisper', -20, space='close', dur=1.0, density=2)
    # ------------------------------------------------------------------ B8.5-B9 the button, "Again"
    E.shot(8.5, 0.0, E.sync(8.5), name='officer radio button')
    E.sfx(8.5, ('w', 'button'), 'radio_click', -2, space='outside')
    E.shot(9, 0.0, E.sync(9), z=1.4, name='officer: again')
    E.hud(9, 0.0, value='#3')
    # ------------------------------------------------------------------ B10 "I live here." from the back seat, in sync
    b10 = E.beat(10); c10 = E.clip(10)
    T10 = E.long(10, b10['t0'])
    E.shot(10, 0.0, E.custom('car', T=T10, talk=[dict(who='D', t=E.long(10, c10['dst_on']), end=E.long(10, c10['dst_off']),
                                                      en='I live here.')],
                             p=dict(expr='dead_stare', scale=0.6, cy=470, cam=dict(mv='push', x=985, y=470, z=1.45, rate=0.06))),
           z=1.2, name='his mouth in sync')
    E.sfx(10, 0.0, 'police_radio_squelch', -4, space='outside', kind_='key')
    # ------------------------------------------------------------------ B11 it sounds right: waveforms align
    b11 = E.beat(11)
    E.shot(11, 0.0, E.film(203.4), name='car creep smile')
    E.ev('panel_dim', 11, 0.0, k=0.3, dur=b11['t1'] - b11['t0'])
    E.ev('wave', 11, 0.0, title='VOICE MATCH', rows=[dict(label='YOU', color=AMBER, seed=7, live=False),
                                                     dict(label='BACK SEAT', color='#ff5a5f', seed=7, live=False)],
         play=(b11['t0'], b11['t1']), dur=b11['t1'] - b11['t0'], y=0.22 * VH, h=400)
    E.ev('stamp', 11, ('w', 'right'), text='MATCH 100%', c=GREEN, y=0.50 * VH, size=92, dur=b11['t1'] - E.w(11, 'right'))
    # ------------------------------------------------------------------ B12 now your name
    E.shot(12, 0.0, E.sync(12), name='officer: now your name')
    E.ev('slam', 12, ('w', 'now'), text='NOW YOUR\nNAME.', c=RED, y=0.34 * VH, size=160, dur=1.0, big=True, shake=True)
    # ------------------------------------------------------------------ B13 hand over your mouth = SUBSCRIBE press
    b13 = E.beat(13)
    T13 = E.long(13, b13['t0'])
    E.shot(13, 0.0, E.custom('bust', T=T13, talk=False, p=dict(who=YOU, bg='hall', cx=960, cy=560, scale=1.05,
                                                               act=_A(ex('fear'), hand_mouth(0.15, 3.0), tremble(0.8)),
                                                               cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.04))),
           name='hand over mouth')
    press = E.t(13, 0.55)
    E.ev('subscribe', None, press)
    E.flags['subscribe_t'] = round(press, 3)
    E.hud(None, press - 0.3, wave_amp=0.4, pop=False)
    E.hud(None, press, wave_amp=0.0, pop=False)
    E.sfx(13, 0.15, 'breath', -6, space='close', kind_='held', dur=1.6)
    # ------------------------------------------------------------------ B14-B15 your mother on the radio
    E.shot(14, 0.0, E.film(222.6), z=1.2, name='radio: mum')
    E.hud(14, 0.0, value='#4', wave_amp=1.0, wave_c='#FF8FC2', accent=PINK)
    E.ev('tag', 14, ('w', 'mother'), text='MUM', x=vfx.SAFE_CX, y=0.27 * VH, style='white', dur=1.0, size=50)
    E.sfx(14, 0.0, 'radio_static', -12, space='outside', dur=0.8, amount=0.5)
    E.shot(15, 0.0, E.film(250.2), name='radio to the peephole')
    E.shot(15, ('w', 'is', 0, -0.05), E.film(229.2), name='flash: her empty room', fx=dict(no_fill=True))
    E.shot(15, ('w', 'is', 0, 0.38), E.film(250.9), name='radio to the peephole 2')
    # ------------------------------------------------------------------ B16 the cough she never clears
    b16 = E.beat(16)
    E.shot(16, 0.0, E.film(253.0), name='officer bg')
    E.ev('wave', 16, 0.0, title='SHOULDER RADIO  —  MUM', rows=[dict(label='MUM', color='#FF8FC2', seed=21, live=False,
                                                                          marker=(0.62, 0.7, 'COUGH'))],
         play=(b16['t0'], b16['t1']), dur=b16['t1'] - b16['t0'], y=0.22 * VH, h=330)
    # ------------------------------------------------------------------ B17 the nickname, then again
    E.shot(17, 0.0, E.film(225.0), name='you: eyes wet')
    E.hud(17, 0.0, value='#5')
    E.ev('label', 17, ('w', 'nickname'), text='██████', x=vfx.SAFE_CX, y=0.30 * VH, size=110, c='#000000',
         dur=0.9)
    E.sfx(17, ('w', 'nickname'), 'bodycam_beep', -10, space='close', n=1)
    E.shot(17.5, 0.0, E.film(223.4), z=1.3, name='radio again')
    # ------------------------------------------------------------------ B18 the cough in exactly the same place + gap
    b18 = E.beat(18)
    E.shot(18, 0.0, E.film(256.3), name='radio bg')
    E.ev('panel_dim', 18, 0.0, k=0.3, dur=b18['t1'] - b18['t0'])
    E.ev('wave', 18, 0.0, title='MUM  —  TAKE 1 / TAKE 2', rows=[dict(label='TAKE 1', color='#FF8FC2', seed=21, live=False,
                                                                           marker=(0.62, 0.7, 'COUGH')),
                                                                      dict(label='TAKE 2', color='#FF8FC2', seed=21, live=False,
                                                                           marker=(0.62, 0.7, 'COUGH'))],
         play=(b18['t0'], b18['off']), dur=b18['t1'] - b18['t0'], y=0.20 * VH, h=470, line=E.w(18, 'same'), line_x=0.66)
    E.ev('stamp', 18, ('w', 'same'), text='IDENTICAL', c=RED, y=0.50 * VH, size=100, dur=b18['t1'] - E.w(18, 'same'))
    E.ev('flash', 18, ('w', 'same'), c='#ff1010', k=0.4, dur=0.07)
    E.sfx(None, b18['off'] + 0.05, 'radio_static', -14, kind='bed', space='outside', dur=round(b18['t1'] - b18['off'], 2), amount=0.35)
    E.sfx(None, b18['off'] + 0.05, 'riser', -8, dur=round(b18['t1'] - b18['off'], 2))
    # ------------------------------------------------------------------ B19 the click: IT'S A RECORDING (twist)
    tc = E.w(19, 'click')
    E.shot(19, 0.0, E.film(223.0), z=1.3, push=0.05, name='radio: before the click')
    E.shot(19, ('w', 'click', 0, -0.03), E.film(263.15), z=1.4, push=0.06, name='officer: the click')
    E.sfx(None, tc, 'radio_click', 2, space='close', kind='hit')
    E.sfx(None, tc, 'braam', 0, kind='hit'); E.sfx(None, tc, 'sub_drop', -2, kind='hit')
    E.ev('glitch', None, tc, dur=0.12, k=0.9)
    E.ev('slam', 19, ('w', 'starts'), text="IT'S A\nRECORDING", c=RED, y=0.34 * VH, size=170, dur=E.beat(19)['t1'] - E.w(19, 'starts') - 0.02, big=True, shake=True, amp=20)
    E.ev('loop', 19, ('w', 'starts', 0, 0.45), y=0.53 * VH, dur=E.beat(19)['t1'] - E.w(19, 'starts') - 0.47)
    E.ev('flash', None, tc, c='#ffffff', k=0.5, dur=0.05)
    E.flags['twist_t'] = round(tc, 3)
    E.flags['music_align'] = (tc, 46.2)
    E.hud(19, ('w', 'starts'), value='LOOP', flash=True)
    # ------------------------------------------------------------------ B20-B21 poor reception, call her: busy
    E.shot(20, 0.0, E.sync(20), z=1.45, name='officer lowers radio')
    E.sfx(20, 0.05, 'radio_click', -3, space='outside')
    b205, b21 = E.beat(20.5), E.beat(21)
    E.shot(20.5, 0.0, E.film(266.8), name='phone bg')
    E.ev('phone', 20.5, 0.0, states=[(b205['t0'], 'calling'), (E.w(21, 'will'), 'busy')], name='MUM',
         dur=b21['t1'] - b205['t0'], y=0.40 * VH)
    E.hud(20.5, 0.0, hide=True, pop=False)
    # ------------------------------------------------------------------ B22 end card: WHERE IS YOUR MOTHER?
    b22 = E.beat(22)
    T22 = 576.0
    E.shot(22, 0.0, E.custom('mumext', T=T22, talk=False, p=dict(police=dict(mode='strobe'), window=1.0, ppl=None,
                                                               cam=dict(mv='push', x=1000, y=600, z=1.15, rate=0.04))),
           name="her house at night")
    E.ev('panel_dim', 22, 0.0, k=0.3, dur=b22['t1'] - b22['t0'] + 0.1)
    hits = [b22['t0'] + 0.02, E.wf(22, 'and', 'find', frac=0.35) + 0.05, E.wf(22, 'busy', 'full', frac=0.65)]
    E.ev('endcard', 22, 0.0, question='WHERE IS\nYOUR MOTHER?', hits=hits, dur=b22['t1'] - b22['t0'] + 0.02, y=0.39 * VH,
         title='IF A POLICE OFFICER KNOCKS AT MIDNIGHT...')
    E.flags['end_t'] = round(b22['t0'], 3)
    E.sfx(22, 0.0, 'phone_busy', -10, space='phone', dur=round(b22['t1'] - b22['t0'], 2))
    # ------------------------------------------------------------------ B23 tail: radio, comments, the click, REWIND
    b23 = E.beat(23)
    E.shot(23, 0.0, E.film(176.3), z=1.25, name='radio tail', fx=dict(no_fill=True, no_punch=True))
    E.ev('panel_dim', 23, 0.0, k=0.55, dur=b23['t1'] - b23['t0'])
    E.ev('comments', 23, 0.0, prompt='COMMENT "MUM"\nIF YOU\'D HANG UP', word='MUM', dur=b23['t1'] - b23['t0'] - 0.14, y=0.30 * VH)
    rw = E.dur - 8 / 60.0
    E.sfx(None, rw - 0.12, 'radio_click', 0, space='close', kind='hit')
    E.shot(None, rw, E.film(176.0 - 8 / 60.0), z=1.25, push=0.05, name='rewind -> frame 1',
           fx=dict(no_fill=True, no_punch=True, rewind=True))
    E.ev('rewind', None, rw, dur=8 / 60.0)
