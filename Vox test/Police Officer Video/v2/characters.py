"""characters.py: the cast, their creepy faces and an acting timeline for "If A Police Officer Knocks..." v2.

Everything draws with skia in the engine's 1920x1080 design space, on any canvas the engine hands a Layer (camera zoom and
render size are already in the canvas matrix). Line weight follows the VISUAL_SPEC: about 8 design px on close-ups and
3 to 4 on wide shots, colour LINE (#1d1f26).

Cast (`CAST`): 'officer' (cap, badge 4471, shoulder radio with coiled cord, bodycam, duty belt), 'officer2' (female
officer, bun), 'double' (your face but wrong: grey coat, scar on his RIGHT, ring on his RIGHT hand, hair parted the other
way), 'you' (hoodie, scar on your LEFT, ring on your LEFT hand), 'mum' (elderly, curly grey hair, glasses, cardigan,
pearls). Left/right are the character's own sides (in a front view the character's left is screen right).

Drawing
    draw(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, aim=None)
        Full body. height = feet to crown in design px (hats and hair go above). pose: Pose, expression name, dict or
        None. detail: 0 wide, 1 medium, 2 close (None = automatic from the on-screen head size, camera zoom included).
        aim=(x, y): while pose.approach rises 0 -> 1 the figure slides so its head reaches that point (the lens axis
        for lean_in toward a doorbell or peephole; pair with Layer(acting.depth(base), ..., ref_depth=base)).
        Returns the Body rig (Body.p3 projects body-unit points if you need to pin a HUD tag to a hand or the head).
    draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None)
        Head-and-shoulders close-up. scale 1.0 = head (crown to chin) 600 design px, head centre at (cx, cy) (eyes sit
        about 0.04 head heights above it). The torso, arms and hands are the real rig, so gestures (radio, hand to
        glass, held props) work in close-ups too. pose.approach > 0 grows the face toward the lens (lean_in).
    draw_head(pen, who, cx, cy, size, pose=None, detail=2, light=None)   head only, size = head height in design px.
    draw_hand(pen, who, x, y, size, shape='open', angle=0, side=1, pose=None)   a single hand (shape: mitt, fist, point,
        open, flat (pressed on glass), grip). draw_prop(pen, name, x, y, size, angle=0): 'radio', 'card', 'notebook',
        'key' (orange key ring), 'phone', 'photo', 'badge'.
    hud_phone_hand(pen, w, h, skin, a, front): drop-in replacement for engine.hud._hand
        (`hud._hand = characters.hud_phone_hand`).
    light = dict(rim='#9fb6ff', rim_a=70, side=1, key=0.0): a cool rim on one side; key in -1..1 darkens (night) or
        warms (porch lamp) the skin. police_flash red/blue on faces: light=dict(rim='#ff3040', rim_a=120, side=-1).

Poses
    Pose(**params) holds every animatable number (see POSE_DEFAULTS) plus discrete fields (hand shapes, props).
    Pose.expr(name) / EXPR[name]: 'neutral', 'calm_smirk', 'polite', 'creep_smile', 'wide_grin', 'stare', 'dead_stare',
        'nervous', 'fear', 'angry', 'whisper', 'shout', 'scream', 'cry', 'grin_cry', 'shock', 'sad', 'suspicious',
        'sweaty', 'blank', 'talk_smile'.
    Pose.lerp(a, b, k) blends two poses continuously.
    View: pose.turn (body yaw) and pose.h_turn (head yaw) in quarter turns: 0 front, +-0.5 three-quarter (+ = facing
        screen right), +-1 profile, +-2 back. VIEWS = {'front':0, 'q_right':0.5, 'q_left':-0.5, 'profile_right':1,
        'profile_left':-1, 'back':2}.

Speed (2560x1440, one process, best of runs on a shared machine): full body 18-27 ms, bust filling the frame 36-51 ms.

Acting (timeline builder; every clip is eased, sub-frame continuous and layered over breathing, blinks and noise)
    a = Acting('officer', seed=1, height=700, expr='neutral', blink=None)   blink None = cast default (the officer and
        the double never blink; you and mum blink 1-2 frames).
    a.at(t) -> Pose          a.events -> SFX events [{t, name, gain_db, pan, params}]   a.depth(base, k) -> f(t)
    Non-sound clips return the Acting (chainable); clips that make a sound return their list of events.
    a.expr(name, t0, t1=None, fade=0.35)             blend to an expression (t1 None = hold)
    a.idle(t0, t1)                                   restore plain idle look-around
    a.stare(t0, t1=None)                             pupils shrink and lock on the lens, no blinks, everything stills
    a.creep_smile(t0, dur=4.0, t1=None, amount=1.0)  slow grin growth (teeth appear at ~40%), eyes do not smile
    a.wide_grin(t0, t1=None, fade=0.6)               too-wide toothy grin with gums, tiny pupils
    a.head_tilt(t0, angle=32, dur=1.6, t1=None, back='ease')  tilt beyond natural; back='snap' snaps upright at t1
    a.snap_turn(t, frm=1.0, to=0.0)                  head snaps to the lens (spring overshoot), eyes lead, body follows
    a.lean_in(t0, dur=2.5, t1=None, amount=1.0)      torso leans to the lens, face grows (pose.approach 0..1)
    a.knock(t0, n=3, spacing=0.32, side=0.0) -> [knock_door events]   side: -1/+1 door to screen left/right, 0 = lens
    a.talk(intervals, text=None, intensity=1.0)      visemes from text (vowels/consonants) or pseudo-syllables;
        intervals: [(t0, t1)] or [(t0, t1, text)]; a.talk_lines(timeline_lines, who='O') takes timeline.json lines
    a.radio_to_mouth(t0, t1) -> [radio_click x2, police_radio_squelch]   hand keys the shoulder mic, head dips to it
    a.press_bodycam(t, on=True) -> [bodycam_beep]    finger presses the chest camera; LED follows pose.cam_on
    a.hold_up(prop, t0, t1, side=-1) -> [paper|...]  raises a prop toward the lens (side -1 = right hand)
    a.hand_on_glass(t0, t1, side=1) -> [knock_door soft]   palm comes at the lens and flattens (pressure-pale fingertips)
    a.walk(t0, t1, x_from, x_to, facing=None, surface='porch') -> [footsteps]   real walk cycle; pose.dx in design px
    a.turn(t0, to, dur=0.6) / a.turn_back(t0, dur=0.45)   body+head yaw with overlapping action
    a.cry(t0, t1=None, smile=False) -> [breath sobs] tears stream, shoulders sob; smile=True = smiling while crying
    a.scream(t0, t1)                                 huge mouth, head shake, tiny pupils
    a.nervous_glance(t0, n=2, side=-1, dur=1.4)      eyes dart to the side and back with quick blinks
    a.twitch(times, amp=1.0)                         sudden jerks (head, eyes, shoulder) with spring settle
    a.freeze(t0, t1) / a.jerk(t, amp=1.0)            total stillness (even breathing), then a jerk back to life
    a.look(t0, x, y, dur=0.12) / a.head_down(t0, t1=None, amount=1.0) / a.sit(t0, t1=None) / a.point(t0, t1, side=-1)
    a.blink(t) forces a blink; hands: hr_* = character's right (screen left in a front view), hl_* = left
    a.set(t0, t1, fade, **params)                    any pose numbers over a window (escape hatch)
    Clips layer in the order they are added (later ones win where they overlap). Overlapping action is built in: eyes
    lead the head, the head leads the body, the shoulder-mic cord, drawstrings and skirts swing from lagged motion
    (pose.sec_x). Events are dicts {t, name, gain_db, pan, params, who} using the required SFX names (knock_door,
    radio_click, police_radio_squelch, bodycam_beep, paper, footsteps_porch / footsteps_wood_inside, breath).

v2.1 additions (character fixer; everything above still works unchanged)
    Acting / lip sync
    a.talk(intervals, text=None, intensity=1.0, env='auto', words='auto', lead=0.02)
        The mouth now follows the real voice: env='auto' samples the vo_en.wav RMS envelope (voice_envelope(), cached as
        $S/pov2/cache/vo_env_*.npy), shut below -40 dBFS and normalised per line; words='auto' places each word's visemes
        in its own ASR window (asr_cache en_words). Grins talk through the teeth (jaw drops on top of the grin), shout /
        scream modulate around their open base, so no line is mouthed with a frozen mouth. Film check (crit sync.py, 31
        visible lines): zero-lag r median 0.16 -> 0.71, p10 -0.19 -> 0.54, frozen-mouth lines 4 -> 0 (best lag now -1
        frame: the mouth leads the voice by ~1 frame). Pass env=None, words=None for the old behaviour.
        CAST[who]['talk'] scales the mouth per character (officer2 0.62: flat, polite).
        voice_envelope(path=None) -> 100 fps dBFS array; voice_words(path=None) -> [(word, t_start)].
    a.snap_turn(t, frm=1.0, to=0.0, hold=0.6, body=0.35, until=None, release=0.5)
        Now OVERRIDES the head yaw (it runs after every other clip, whatever the order they were added in) and holds `to`
        after the snap (until None = for good). A held look_side() underneath no longer wins: yaw at snap+0.5 s = 0.0.
        frm=None starts from the current yaw.
    a.knock(t0, n=3, spacing=0.32, side=0.0, hand=None, strength=1.0, reach=0.72)
        side +1/-1 (door slab to screen right/left of the doorbell): the near hand (hand=None picks it) reaches out at
        shoulder height (0.72 arm length) with a forearm snap per hit, a 2-4 deg body rock, head locked on the lens.
        side 0 = knock ON the lens (peephole / doorbell glass): fist at face height in front, growing ~1.3x per hit; the
        events carry params lens=True -> add a ~1.5 % cam.hit at each event t. Events pan 0.35*side for side knocks.
    a.radio_to_mouth(t0, t1, side=1, tilt=13.0)   the shoulder speaker-mic comes up beside the mouth in the hand (the coiled
        cord follows), the head tilts 13 deg into it with the eyes locked on the lens, the thumb squashes the PTT key on
        each click. Frame busts at cy ~ 470, scale <= 0.9 so the mic is in frame.
    a.phone_to_ear(t0, t1=None, side=1, fade=0.5, tilt=6.0)   phone pressed to the ear in busts and full body: wrist under
        the ear, elbow forward and down, the dark back of the phone on the cheek, the hand wrapped round it. The old
        film.phone_ear() pose (prop 'phone', hand raised near the shoulder) is detected and drawn the same way, so
        existing shots are fixed without changes (no more purple spike).
    a.blink(t, dur=0.067) / a.blink_burst(t0, n=4, dur=1.0)   blinks are 1-2 frames at 30 fps now (shut in 17 ms, open by
        67 ms); ~28 % of the scheduled blinks of you / mum are nervous doubles.
    a.life(t0, t1=None, amount=0.0)   scales the new always-on idle life. Acting(..., life=1.0) sets it per actor.
        Creepy cast (officer, officer2, double) and anyone staring: breathing never stops, slow +-3 deg head drift, a head
        re-settle (pose swap, 1.5-4.5 deg) every 2-3.6 s, slow weight shifts, and (creepy cast) a small involuntary twitch
        every 4.5-8.5 s; no blinks. Scared cast (you, mum): quick nervous head re-orients every 1.3-2.6 s scaled by the
        fear in the face, and a shiver with pose.tremble. freeze() still stops everything. Crit activity metric on the
        same film plan, old -> new characters.py: officer frozen 42 -> 36 %, you 67 -> 59 %, double 49 -> 41 %, mum 63 -> 53 %,
        officer2 56 -> 51 %; holds >= 2 s 9/8/7/5/1 -> 4/2/2/1/0 (critic's v2 baseline: officer 65 %, you 91 %).
        Use a.life(t0, t1, 0) for a deliberate dead-still beat (or freeze()).
    a.hand_to_mouth(t0, t1=None, side=-1, fade=0.45, shock=True)   hand over the mouth (stifled sob / shock), eyes wide.
    a.wipe_tears(t0, side=1, dur=1.3)   back of the fingers wipes under one eye and out across the cheek.
    a.glasses_off(t0, t1=None, side=1)  mum takes her glasses off at t0 + 0.55 and holds them at chest height (back on at t1).
    a.creep(t0, t1, tilt=8.0, jerk_at=None, side=None, sway=5.0)   one-call weird beat for a held creepy shot: slow
                                        over-long tilt across the shot, weight shift, a jerk at 55 % (critic's creep()).
    a.impatient(t0, dur=2.6, side=1)    weight shift, glance away to the street, sharp look back, twitch on arrival.
    a.flinch(t, amp=1.0)                startle on a knock / hit / countdown number: head jerks back, shoulders up, 2-frame
                                        squeeze, wide-eyed settle. Good on 'you' at every knock event time.
    Pose fields: life, hl_ear / hr_ear (phone at the ear), hl_scale / hr_scale (hand size, the lens knock uses it), specs
    (mum's glasses on the face).

    Faces
    Rounder egg / bean skulls with tapered jaws for the whole cast (officer jaw@82 88 -> 76, mum 92 -> 76; silhouette fill
    0.876 -> 0.82); grins push the cheeks out ~5 %. EXPR 'scream' = terror (O mouth with corners pulled DOWN, bottom teeth
    only, up-slanted pinched brows, tremble); 'fear' / 'shout' / 'shock' get downturned corners too. 'you' / double
    brows are drawn over the fringe (never hidden). Tears are thin pale-blue streaks with a white highlight that stop at
    the jaw outline and drip from it (below mum's glasses rims). Wrinkles are a few clean folds (forehead folds only
    when the brows lift); pore texture halved. officer2's lips are muted (#8f6466) and her talk is 0.62.

    Hands and inserts
    draw_hand(...) shapes now have real fingers (3 phalanges, nails, knuckle creases, one shade step): 'open' (back of the
        hand), 'flat' (palm, pressed pads), 'fist' (knuckles + wrapped thumb), 'point', 'grip' (4 finger rolls round a prop,
        thumb on the side), 'relaxed' (fingers together), 'palm4' (no thumb), 'mitt'. The ring is a gold band ON the
        ring finger with a glint. Angle convention unchanged: angle 0 = fingers DOWN, 180 = fingers up.
    draw_hands_lap(pen, who, cx, cy, size, rub_phase=0.0, ring_side=None, t=0.0, detail=2, light=None, cuffs=True,
                   thread=False, rub_amp=12.0, rub=True) -> dict(ring_xy=(x, y) design point of the ring, ...)
        Two hands folded in the lap, arms coming in from both top corners: the lower hand back up (it wears the ring when
        ring_side is +1 = character's left = screen right, -1 = screen left; None or 0 = no ring), the other cradling it
        with its thumb over the base of the ring finger, rocking +-12 deg with rub_phase (None = still). size = one hand
        length in design px (the group spans ~2.4x size). cuffs=False if the set already draws sleeves; thread=True hangs
        the lit loose thread from the lower cuff (pass p.get('thread')). Use ring_xy for the RING tag leader line.
    draw_palm_on_glass(pen, who, x, y, size, press=1.0, t=0.0, angle=0.0, side=1, alpha=1.0, halo=1.0, slide=0.0)
        Open hand pressed on glass, FINGERS UP at angle 0, 5 spread fingers, pale flattened pads, darker pressed rim,
        condensation halo. (x, y) = wrist; slide = extra y for the slow slide down the glass; alpha fades it. For the
        back-seat window put it beside the face (x ~ face x + 0.7 head width) and drop act=hand_on_glass so there is
        one hand only.
    hud_phone_hand (installed as engine.hud._hand) draws real fingertips curling round the phone edge and a thumb.
    Props: 'mic' (shoulder speaker-mic), 'phone_back' (dark back of a phone).
    Creepy cast (lock >= 0.5): a smile never squints their eyes (the eyes do not smile). 'flat' hands with press > 0 are
    drawn pale with a darker pressed rim (hand_on_glass).
    Self-test: python3 characters.py --selftest (snap override, blink length, phone at the ear, lip-sync correlation).

Typical use in a shot
    a = Acting('officer', seed=7, height=700); a.stare(0); a.creep_smile(1.0, 3.5); ev = a.knock(0.4)
    Layer(a.depth(1.0), lambda pen, t: draw(pen, 'officer', 960, 905, 700, a.at(t), aim=(960, 470)), 'officer', ref_depth=1.0)
    Close-up: Layer(1.0, lambda pen, t: draw_bust(pen, 'officer', 960, 560, 1.1, a.at(t), light=dict(rim='#9fb6ff')), 'face')
"""
import math, os, sys
from contextlib import contextmanager
import numpy as np
import skia

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
from engine.core import (CFG, LINE, col, mix, Pen, smooth, poly, rect, rrect, oval, inter, union, minus, clamp, lerp, prog,  # noqa: E402
                         ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, ease_out_quad, spring, noise1, hash01,
                         tex, text)
from engine.core import _ramp, _stops_key                                                   # noqa: E402

PI = math.pi
INF = float('inf')
VIEWS = {'front': 0.0, 'q_right': 0.5, 'q_left': -0.5, 'profile_right': 1.0, 'profile_left': -1.0, 'back': 2.0}

# ====================================================================================================== cast
_POLICE = dict(shirt='#1f2a44', shirt_sh='#121a2d', shirt_hi='#33446a', trousers='#161d30', trousers_sh='#0d1220',
               cap='#18213a', cap_sh='#0f1528', visor='#0a0c11', tie='#0e121c', gold='#c9a64a', gold_sh='#86682a',
               gold_hi='#f2dc94', silver='#a7aeb7', silver_sh='#5f666f', black='#15161a', black_hi='#3a3d45',
               patch='#24386e', patch_rim='#c9a64a', shoes='#0c0c0f', belt='#0f1013')

CAST = {
    'officer': dict(
        outfit='police', hat='cap', hair='short', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 56, 80, 95, 100, 99, 91, 76, 54, 29, 0],
        eye_dx=44, eye_y=-10, eye_r=20.5, pupil=0.78, brow_th=11, nose_len=26, mouth_y=60, mouth_w=24,
        skin='#c4ada2', skin_sh='#937b76', skin_dp='#5e4a50', blush='#d4979b', lip='#97706f', stubble='#4f5966', stub=0.6,
        hair_c='#41352f', brow_c='#221c1c', bags=1.0, age=0.8, blink_rate=0.0, lock=1.0, micro=0.5, breath=0.8,
        scar=0, ring=0, part=0, lashes=0.0,
        body=dict(sh=130, ch=124, wa=106, hip=110, arm=(52, 42), leg=(66, 52), neck=50, hand=1.0),
        cloth=dict(_POLICE)),
    'officer2': dict(
        outfit='police', hat='cap', hair='bun', sex='f', hh=176.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 72, 87, 92, 90, 81, 64, 43, 22, 0],
        eye_dx=41, eye_y=-8, eye_r=19.5, pupil=0.85, brow_th=8, nose_len=20, mouth_y=58, mouth_w=21,
        skin='#c5ae a0'.replace(' ', ''), skin_sh='#937a73', skin_dp='#6a5257', blush='#dc9a9e', lip='#8f6466', stubble=None, stub=0, lips=0.6, talk=0.62,
        hair_c='#2b1d19', brow_c='#2b1d19', bags=0.55, age=0.35, blink_rate=0.0, lock=1.0, micro=0.45, breath=0.7,
        scar=0, ring=0, part=0, lashes=1.4, earrings=True,
        body=dict(sh=114, ch=110, wa=90, hip=104, arm=(44, 36), leg=(58, 46), neck=41, hand=0.88),
        cloth=dict(_POLICE, shirt='#22304d', shirt_hi='#38496f')),
    'you': dict(
        outfit='hoodie', hat=None, hair='messy', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 74, 91, 97, 96, 86, 69, 47, 24, 0],
        eye_dx=43, eye_y=-8, eye_r=20, pupil=1.0, brow_th=9.5, nose_len=22, mouth_y=58, mouth_w=22,
        skin='#c9aa98', skin_sh='#97786c', skin_dp='#634c4b', blush='#dd9b97', lip='#a06f6a', stubble='#5a5550', stub=0.25,
        hair_c='#382821', brow_c='#2d211c', bags=0.6, age=0.3, blink_rate=0.35, lock=0.0, micro=1.0, breath=1.0,
        scar=1, ring=1, part=1, lashes=0.0,
        body=dict(sh=120, ch=118, wa=108, hip=106, arm=(54, 46), leg=(58, 48), neck=46, hand=1.0),
        cloth=dict(top='#34443f', top_sh='#212d2a', top_hi='#4b5f58', trousers='#2a3347', trousers_sh='#1a2030',
                   shoes='#b9b3a6', shoes_sh='#7c776d', string='#cfc9bb')),
    'double': dict(
        outfit='coat', hat=None, hair='messy', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 74, 91, 97, 96, 86, 69, 47, 24, 0],
        eye_dx=43, eye_y=-8, eye_r=20.5, pupil=0.62, brow_th=9.5, nose_len=22, mouth_y=58, mouth_w=22,
        skin='#bcaea8', skin_sh='#8a7c7a', skin_dp='#584a52', blush='#c99a9c', lip='#8f6f6e', stubble='#5a5a5c', stub=0.3,
        hair_c='#382821', brow_c='#2d211c', bags=0.95, age=0.35, blink_rate=0.0, lock=1.0, micro=0.3, breath=0.5,
        scar=-1, ring=-1, part=-1, lashes=0.0,
        body=dict(sh=122, ch=118, wa=108, hip=110, arm=(52, 44), leg=(56, 46), neck=46, hand=1.0),
        cloth=dict(coat='#6b6f74', coat_sh='#4c5056', coat_hi='#8a8f95', shirt='#26282e', trousers='#23252b',
                   trousers_sh='#16171b', shoes='#111113', button='#2c2d31')),
    'mum': dict(
        outfit='cardigan', hat=None, hair='curly', sex='f', hh=190.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 52, 77, 94, 100, 99, 91, 76, 54, 28, 0],
        eye_dx=42, eye_y=-6, eye_r=18.5, pupil=1.0, brow_th=7, nose_len=24, mouth_y=60, mouth_w=21,
        skin='#c8ab9f', skin_sh='#96786f', skin_dp='#6a5153', blush='#de9c9c', lip='#a5716f', stubble=None, stub=0, lips=0.45,
        hair_c='#c2beba', brow_c='#8d8580', bags=0.85, age=1.0, blink_rate=0.3, lock=0.0, micro=1.0, breath=1.0,
        scar=0, ring=1, part=0, lashes=0.6, glasses=True,
        body=dict(sh=100, ch=108, wa=104, hip=112, arm=(42, 34), leg=(38, 32), neck=34, hand=0.85),
        cloth=dict(top='#6c5270', top_sh='#4c3850', top_hi='#86688a', blouse='#ddd3c2', blouse_sh='#b3a893',
                   skirt='#3a3342', skirt_sh='#27222d', legs='#a58e86', shoes='#2a2220', pearl='#ece6dc')),
}
CAST['officer2']['skin'] = '#cdb3a6'

# ====================================================================================================== pose
POSE_DEFAULTS = dict(
    # placement / body (body units: 1000 = feet to crown)
    dx=0.0, dy=0.0, turn=0.0, lean=0.0, tilt=0.0, sway=0.0, bob=0.0, breath=0.5, approach=0.0, sit=0.0, crouch=0.0,
    shrug=0.0, hunch=0.0,
    # head
    h_turn=0.0, h_tilt=0.0, h_nod=0.0, h_dx=0.0, h_dy=0.0, h_scale=1.0,
    # eyes: look in -1..1 (relative to the face), lock 1 = pupils on the lens whatever the head does
    look_x=0.0, look_y=0.0, lock=0.0, pupil=1.0, eye_open=1.0, blink=0.0, wide=0.0, squint=0.0, bloodshot=0.0, wet=0.0,
    # brows
    brow_up=0.0, brow_angry=0.0, brow_sad=0.0, brow_asym=0.0,
    # mouth
    m_open=0.0, m_wide=0.0, m_round=0.0, smile=0.0, grin=0.0, teeth=0.0, gums=0.0, tremble=0.0, m_side=0.0, m_press=0.0,
    # skin extras
    tears=0.0, sweat=0.0, blush=0.0, pale=0.0, jitter=0.0, glint=0.0,
    # arms: hand target relative to its shoulder: out (away from body), down, fwd (toward the character's front)
    hl_out=10.0, hl_down=336.0, hl_fwd=6.0, hr_out=10.0, hr_down=336.0, hr_fwd=6.0,
    hl_up=0.0, hr_up=0.0, hl_press=0.0, hr_press=0.0, hl_rot=0.0, hr_rot=0.0, thumb=0.0,
    # legs
    walk_ph=0.0, walk_amt=0.0, stance=0.0,
    # secondary motion and gadgets
    sec_x=0.0, sec_y=0.0, cam_on=1.0, still=0.0, t=0.0,
    # v2.1: idle-life scale (creepy drift / re-settles / weight shifts / micro twitches), phone-to-ear arm weights,
    # per-hand size (fist punch toward the lens)
    life=1.0, hl_ear=0.0, hr_ear=0.0, hl_scale=1.0, hr_scale=1.0, specs=1.0,
)
POSE_DISCRETE = dict(hl_shape='mitt', hr_shape='mitt', hl_prop=None, hr_prop=None)


class Pose:
    """All animatable pose numbers (POSE_DEFAULTS) plus discrete hand shapes / props (POSE_DISCRETE)."""

    def __init__(self, expr=None, **kw):
        d = self.__dict__
        d.update(POSE_DEFAULTS); d.update(POSE_DISCRETE)
        if expr: self.mix(EXPR[expr], 1.0)
        d.update(kw)

    def copy(self):
        p = Pose.__new__(Pose); p.__dict__ = dict(self.__dict__); return p

    def mix(self, params, w=1.0):
        """Blend toward params (dict) by weight w (0..1). Discrete fields switch at w >= 0.5."""
        if w <= 0: return self
        d = self.__dict__
        for k, v in params.items():
            if k in POSE_DISCRETE or not isinstance(v, (int, float)):
                if w >= 0.5: d[k] = v
            else:
                c = d.get(k, 0.0); d[k] = c + (v - c) * min(1.0, w)
        return self

    def add(self, params, w=1.0):
        d = self.__dict__
        for k, v in params.items(): d[k] = d.get(k, 0.0) + v * w
        return self

    def expr(self, name, w=1.0):
        return self.mix(EXPR[name], w)

    @staticmethod
    def lerp(a, b, k):
        p = a.copy(); p.mix({k_: v for k_, v in b.__dict__.items()}, k); return p

    def __repr__(self):
        return 'Pose(%s)' % ', '.join('%s=%.2f' % (k, v) for k, v in self.__dict__.items()
                                      if isinstance(v, float) and abs(v - POSE_DEFAULTS.get(k, 0)) > 1e-3)


EXPR = {
    'neutral': {},
    'blank': dict(pupil=0.8, eye_open=0.92),
    'calm_smirk': dict(smile=0.38, m_side=0.6, brow_angry=0.2, squint=0.22, pupil=0.9, brow_asym=0.3),
    'polite': dict(smile=0.5, teeth=0.15, brow_up=0.15, squint=0.1),
    'talk_smile': dict(smile=0.55, teeth=0.4, brow_up=0.2, pupil=0.75),
    'creep_smile': dict(smile=0.9, grin=0.45, teeth=0.75, pupil=0.55, wide=0.3, brow_up=0.3, bloodshot=0.35, lock=1.0),
    'wide_grin': dict(smile=1.0, grin=1.0, teeth=1.0, gums=0.7, m_open=0.22, pupil=0.42, wide=0.55, brow_up=0.55,
                      bloodshot=0.6, lock=1.0),
    'stare': dict(pupil=0.5, wide=0.5, brow_up=0.3, bloodshot=0.45, lock=1.0, still=1.0),
    'dead_stare': dict(pupil=0.55, eye_open=0.82, wide=0.1, m_press=0.6, lock=1.0, still=1.0, bloodshot=0.3),
    'nervous': dict(brow_sad=0.75, brow_up=0.25, smile=-0.3, tremble=0.7, wide=0.25, pupil=0.85, sweat=0.5, m_press=0.3),
    'fear': dict(wide=0.75, pupil=0.4, brow_sad=0.85, brow_up=0.6, brow_angry=0.15, m_open=0.28, m_round=0.3, smile=-0.4,
                 tremble=0.6, sweat=0.7),
    'angry': dict(brow_angry=1.0, smile=-0.45, squint=0.35, m_open=0.16, teeth=0.8, m_wide=0.55, pupil=0.7),
    'whisper': dict(m_open=0.1, m_round=0.45, brow_up=0.2, squint=0.25, smile=0.18, pupil=0.62, h_nod=0.1, lock=1.0),
    'shout': dict(m_open=0.85, m_round=0.35, brow_angry=0.95, wide=0.35, pupil=0.55, teeth=0.4, smile=-0.35),
    'scream': dict(m_open=1.0, m_round=0.4, smile=-0.7, wide=0.85, pupil=0.3, brow_up=0.5, brow_sad=0.9, brow_angry=0.3,
                   teeth=0.35, gums=0.0, tremble=0.45),
    'cry': dict(tears=1.0, brow_sad=1.0, smile=-0.55, m_open=0.32, m_round=0.35, tremble=0.65, squint=0.3, blush=0.7, wet=1.0),
    'grin_cry': dict(tears=1.0, smile=1.0, grin=0.9, teeth=1.0, gums=0.3, brow_sad=0.95, wide=0.4, pupil=0.48, blush=0.6,
                     wet=1.0, lock=1.0),
    'shock': dict(m_open=0.62, m_round=0.85, wide=0.85, pupil=0.38, brow_up=0.85, smile=-0.25),
    'sad': dict(brow_sad=0.85, smile=-0.45, pupil=0.95, eye_open=0.8, h_nod=0.08, wet=0.5),
    'suspicious': dict(squint=0.5, brow_angry=0.45, brow_asym=0.7, smile=0.12, m_side=-0.7, pupil=0.8, look_x=-0.35),
    'sweaty': dict(sweat=1.0, brow_sad=0.55, wide=0.3, smile=-0.2, tremble=0.35, pupil=0.7, m_press=0.4),
}


# ====================================================================================================== drawing context
_TXI = {}


def _overlay_img(name, k=2.2):
    """Normal-blend version of a core texture: dark specks = black with alpha, light = white with alpha (fast src-over)."""
    key = (name, k)
    if key not in _TXI:
        g = tex(name)
        d = np.clip((0.5 - g) * k, 0, 1); l_ = np.clip((g - 0.5) * k, 0, 1)
        a = np.maximum(d, l_)
        v = np.where(l_ > d, l_, 0.0)
        arr = np.dstack([v * 255, v * 255, v * 255, a * 255]).astype(np.uint8)
        arr = np.ascontiguousarray(arr)
        _TXI[key] = (skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
    return _TXI[key][0]


_LINS = skia.SamplingOptions(skia.FilterMode.kNearest)
_GIMG = {}


def _gimg(kind, stops):
    """Cached gradient image (premultiplied BGRA): 'r' 512x512 radial, 'l' 1024x2 linear. Drawn as a nearest-sampled
    image shader on the path: ~10x faster than stretched image rects and correct under any rotation."""
    key = (kind, _stops_key(stops))
    im = _GIMG.get(key)
    if im is None:
        if kind == 'r':
            n = 512
            yy, xx = np.mgrid[0:n, 0:n]
            r = np.sqrt((xx + 0.5 - n / 2) ** 2 + (yy + 0.5 - n / 2) ** 2) / (n / 2)
            arr = _ramp(key[1], np.clip(r, 0, 1))
        elif kind == 'v':
            arr = np.repeat(_ramp(key[1], (np.arange(1024) + 0.5) / 1024)[:, None, :], 2, axis=1)
        else:
            arr = np.repeat(_ramp(key[1], (np.arange(1024) + 0.5) / 1024)[None, :, :], 2, axis=0)
        arr = np.ascontiguousarray(arr)
        im = (skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
        if len(_GIMG) > 400: _GIMG.clear()
        _GIMG[key] = im
    return im[0]


def _snap_axis(m, cx, cy, tol=0.105):
    """Drop a small rotation (< ~6 deg) from a shader matrix, keeping the image point (cx, cy) in place: rotated image
    sampling is skia's slow path, and idle head sway would otherwise put every face gradient on it."""
    a, b, c, d = m.getScaleX(), m.getSkewX(), m.getSkewY(), m.getScaleY()
    if (b == 0 and c == 0) or abs(b) > tol * abs(d) or abs(c) > tol * abs(a): return m
    px = a * cx + b * cy + m.getTranslateX(); py = c * cx + d * cy + m.getTranslateY()
    a2 = math.copysign(math.hypot(a, c), a); d2 = math.copysign(math.hypot(b, d), d)
    r = skia.Matrix(); r.setAll(a2, 0, px - a2 * cx, 0, d2, py - d2 * cy, 0, 0, 1)
    return r


class Ctx:
    """Local drawing frame: geometry in local units goes through matrix M onto the (axis-aligned) engine canvas, so the
    engine's fast gradient paths keep working even when a head is tilted. lw = outline width in local units."""
    __slots__ = ('pen', 'cv', 'M', 's', 'lw', 'm6', 'det')

    def __init__(self, pen, M, lw):
        self.pen, self.cv, self.M = pen, pen.cv, M
        a, b, c, d = M.getScaleX(), M.getSkewX(), M.getSkewY(), M.getScaleY()
        self.det = a * d - b * c
        self.s = math.sqrt(abs(self.det)) or 1e-6
        self.lw = lw
        self.m6 = (a, b, M.getTranslateX(), c, d, M.getTranslateY())

    def sub(self, tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=None):
        m = skia.Matrix(); m.preConcat(self.M); m.preTranslate(tx, ty)
        if rot: m.preRotate(rot)
        sy = sx if sy is None else sy
        if sx != 1.0 or sy != 1.0: m.preScale(sx, sy)
        k = math.sqrt(abs(sx * sy)) or 1e-6
        return Ctx(self.pen, m, self.lw / k)

    def P(self, path):
        q = skia.Path(path); q.transform(self.M); return q

    def pt(self, x, y):
        a, b, tx, c, d, ty = self.m6
        return a * x + b * y + tx, c * x + d * y + ty

    def fill(self, path, c, a=255):
        if a > 0.5: self.pen.fill(self.P(path), c, a)

    def line(self, path, w=None, c=LINE, a=255, cap='round'):
        if a > 0.5: self.pen.line(self.P(path), (self.lw if w is None else w) * self.s, c, a, cap)

    def shape(self, path, c, w=None, lc=LINE, a=255):
        q = self.P(path)
        self.pen.fill(q, c, a)
        self.pen.line(q, (self.lw if w is None else w) * self.s, lc, a)

    def _shade_path(self, path, img, m, a):
        sm = skia.Matrix(); sm.preConcat(self.M); sm.preConcat(m)
        sm = _snap_axis(sm, img.width() / 2.0, img.height() / 2.0)
        p = skia.Paint(AntiAlias=True, Shader=img.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, _LINS, sm), Alphaf=float(clamp(a)))
        self.cv.drawPath(self.P(path), p)

    def radial(self, path, cx, cy, r, stops, sy=1.0, a=1.0, clip=True):
        """Radial gradient (local coords, rotates with the frame). path None: just the gradient's ellipse (clip=False)
        or everything visible (clip=True, beyond r = last stop)."""
        m = skia.Matrix(); m.setScale(2 * r / 512.0, 2 * r * sy / 512.0); m.postTranslate(cx - r, cy - r * sy)
        if path is None:
            if clip: path = rect(cx - 4000, cy - 4000, 8000, 8000)
            else: path = oval(cx, cy, r, r * sy)
        self._shade_path(path, _gimg('r', stops), m, a)

    def glow(self, cx, cy, rx, ry, c, a):
        if a > 0.5: self.radial(None, cx, cy, rx, [(0, c, a), (0.5, c, a * 0.5), (1, c, 0)], sy=ry / rx, clip=False)

    def grad(self, path, x0, y0, x1, y1, stops, a=1.0):
        """Linear gradient between two local points (clamped beyond them)."""
        dx, dy = x1 - x0, y1 - y0
        m = skia.Matrix()
        if abs(dx) <= 0.02 * abs(dy):                      # vertical: axis-aligned matrix keeps skia on its fast path
            m.setScale(1.0, dy / 1024.0); m.postTranslate(x0, y0)
            self._shade_path(path, _gimg('v', stops), m, a); return
        if abs(dy) <= 0.02 * abs(dx):
            m.setScale(dx / 1024.0, 1.0); m.postTranslate(x0, y0)
            self._shade_path(path, _gimg('l', stops), m, a); return
        L = math.hypot(dx, dy)
        m.setScale(L / 1024.0, 1.0); m.postRotate(math.degrees(math.atan2(dy, dx))); m.postTranslate(x0, y0)
        self._shade_path(path, _gimg('l', stops), m, a)

    def texture(self, path, name, alpha=0.2, scale=1.0, dx=0.0, dy=0.0):
        if alpha <= 0.01: return
        img = _overlay_img(name)
        m = skia.Matrix(); m.preConcat(self.M); m.preTranslate(dx, dy); m.preScale(scale, scale)
        m = _snap_axis(m, 0.0, 0.0)
        p = skia.Paint(AntiAlias=True, Shader=img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, _LINS, m),
                       Alphaf=float(clamp(alpha)))
        self.cv.drawPath(self.P(path), p)

    @contextmanager
    def clip(self, path, diff=False):
        self.cv.save()
        self.cv.clipPath(self.P(path), skia.ClipOp.kDifference if diff else skia.ClipOp.kIntersect, True)
        try: yield
        finally: self.cv.restore()


@contextmanager
def _noop():
    yield


def _lw_for(head_px):
    """Outline width (design px) for a head of head_px design px: ~3.7 on wide shots, ~8.2 on close-ups (VISUAL_SPEC)."""
    return clamp(2.8 + 0.009 * head_px, 2.4, 9.5)


def _auto_detail(pen, head_design):
    m = pen.cv.getTotalMatrix()
    px = head_design * math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY()))
    return 0 if px < 70 else (1 if px < 260 else 2)


def _pts_path(xs, ys, closed=True, k=1.0):
    return smooth(list(zip(xs.tolist() if hasattr(xs, 'tolist') else xs, ys.tolist() if hasattr(ys, 'tolist') else ys)), closed, k)


def _multi(paths):
    """Several open/closed paths as one path (one draw call)."""
    p = skia.Path()
    for q in paths: p.addPath(q)
    return p


def _crescent(path, dx, dy):
    """The part of `path` not covered by itself moved by (dx, dy): a shade / rim band (path op, no clip mask)."""
    q = skia.Path(path); q.offset(dx, dy)
    r = skia.Op(path, q, skia.PathOp.kDifference_PathOp)
    return r if r is not None else skia.Path()


def _circle_pts(cx, cy, rx, ry=None, n=16, a0=0.0):
    ry = rx if ry is None else ry
    a = np.linspace(0, 2 * PI, n, endpoint=False) + a0
    return cx + rx * np.cos(a), cy + ry * np.sin(a)


# ====================================================================================================== head mapping
class HeadMap:
    """Maps front-view face coordinates (head units: crown -120, chin +120, half-width ~100) onto the turned head.
    The cross-section is an egg: a flat-ish face in front (depth DF * w) and a deep cranium behind (DB * w), so turned
    faces stay inside the silhouette and profiles put the nose on the edge. yaw (rad, + = facing screen right), pitch
    (rad, + = nod down), jaw (head units the chin drops by). Returns local 2D points (roll/scale/translate live in Ctx)."""
    DF, DB = 0.74, 1.2

    def __init__(self, sp, yaw, pitch, jaw=0.0, cheek=0.0):
        self.ys = np.asarray(sp['head_ys'], float); self.ws = np.asarray(sp['head_ws'], float)
        if cheek > 0.01:                                  # v2.1: a grin pushes the cheeks out (4-6 % at y ~ 40)
            self.ws = self.ws * (1.0 + 0.055 * cheek * np.exp(-((self.ys - 40.0) / 26.0) ** 2))
        self.yaw, self.pitch, self.jaw = yaw, pitch, jaw
        self.ct, self.st = math.cos(yaw), math.sin(yaw)
        self.cp, self.spi = math.cos(pitch), math.sin(pitch)
        self.dk = self.DF

    def W(self, y):
        return np.interp(y, self.ys, self.ws)

    def J(self, y):
        """Jaw drop: stretches everything below the mouth line."""
        y = np.asarray(y, float)
        return y + self.jaw * np.clip((y - 40.0) / 80.0, 0, None) if self.jaw else y

    def map(self, x0, y0, dz=0.0):
        x0 = np.asarray(x0, float); y0 = np.asarray(y0, float)
        w = np.maximum(self.W(y0), 1.0)
        s = np.clip(x0 / w, -1.0, 1.0)
        c = np.sqrt(1.0 - s * s)
        pz = self.DF * w * c + dz
        yj = self.J(y0)
        y1 = yj * self.cp + pz * self.spi
        z1 = pz * self.cp - yj * self.spi
        X = x0 * self.ct + z1 * self.st
        nx, nz = s * self.DF, c
        nn = np.sqrt(nx * nx + nz * nz) + 1e-9
        vis = (-nx * self.st + nz * self.cp * self.ct) / nn
        return X, y1, vis

    def map1(self, x0, y0, dz=0.0):
        X, Y, V = self.map(x0, y0, dz); return float(X), float(Y), float(V)

    def sx(self, x0, y0, dz=0.0):
        """Horizontal foreshortening at a face point."""
        a = self.map1(x0 - 1.0, y0, dz); b = self.map1(x0 + 1.0, y0, dz)
        return max(0.08, abs(b[0] - a[0]) / 2.0)

    def extent(self, w, df=None, db=None):
        """(left, right) screen x of a cross-section of half-width w."""
        df = self.DF if df is None else df; db = self.DB if db is None else db
        fr = np.sqrt((w * self.ct) ** 2 + (w * df * self.st) ** 2)
        bk = np.sqrt((w * self.ct) ** 2 + (w * db * self.st) ** 2)
        return (-bk, fr) if self.st >= 0 else (-fr, bk)

    def silhouette(self, grow=0.0, y_top=-120.0, y_bot=120.0, n=26):
        ys = np.linspace(y_top, y_bot, n)
        w = self.W(np.clip(ys, -120, 120)) + grow * (self.W(np.clip(ys, -120, 120)) > 0)
        xl, xr = self.extent(w)
        yy = self.J(ys) * self.cp + self.DF * w * self.spi * 0.25
        xs = np.concatenate([xr, xl[::-1]])
        yv = np.concatenate([yy, yy[::-1]])
        return _pts_path(xs, yv, True, 0.9)

    def arc(self, yfun, n=64):
        """Visible part of a curve running right round the head (phi in -pi..pi, 0 = front). yfun(phi) -> height.
        Returns 2D points sorted left to right."""
        phis = np.linspace(-PI, PI, n, endpoint=False)
        y0 = yfun(phis)
        w = np.maximum(self.W(y0), 1.0)
        c = np.cos(phis); s = np.sin(phis)
        d = np.where(c > 0, self.DF, self.DB)
        px = w * s; pz = d * w * c
        y1 = self.J(y0) * self.cp + pz * self.spi
        z1 = pz * self.cp - y0 * self.spi
        X = px * self.ct + z1 * self.st
        nx, nz = s * d, c
        vis = (-nx * self.st + nz * self.ct)
        k = vis > -0.02
        X, Y = X[k], y1[k]
        o = np.argsort(X)
        return X[o], Y[o]


# ====================================================================================================== head drawing
def _skin_cols(sp, P, light):
    skin, sh, dp = sp['skin'], sp['skin_sh'], sp['skin_dp']
    if P.pale > 0:
        skin = mix(skin, '#b9b4b4', 0.6 * P.pale); sh = mix(sh, '#7d7880', 0.6 * P.pale)
    k = (light or {}).get('key', 0.0)
    if k > 0: skin = mix(skin, '#e2b48a', 0.25 * k); sh = mix(sh, '#9a6a52', 0.25 * k)
    elif k < 0: skin = mix(skin, '#7d8496', -0.35 * k); sh = mix(sh, '#4a5064', -0.35 * k)
    return skin, sh, dp


def _ear(c, hm, sp, side, skin, sh, det):
    y = 4.0
    w = float(hm.W(y))
    ph = 0.2
    ax3, az3 = side * w * math.cos(ph) * 0.95, -hm.DB * w * math.sin(ph)
    AX = ax3 * hm.ct + az3 * hm.st
    AY = float(hm.J(y)) * hm.cp + az3 * hm.spi * 0.3
    du = side * 0.8 * hm.ct - 0.86 * hm.st          # ear plane direction (outward and back) on screen
    nz = -side * hm.st
    if nz < -0.5: return
    pts = [(0, -24), (9, -29), (19, -20), (21, -2), (15, 18), (5, 27), (-1, 17)]
    P_ = [(AX + u * du, AY + v) for u, v in pts]
    p = smooth(P_, True, 0.9)
    c.fill(p, skin); c.line(p, c.lw * 0.9)
    if sp.get('earrings'):
        ex_, ey_ = AX + 6 * du, AY + 24
        c.fill(oval(ex_, ey_, 4.5), '#d8b04c'); c.line(oval(ex_, ey_, 4.5), c.lw * 0.35)
        if det >= 1: c.fill(oval(ex_ - 1.3, ey_ - 1.3, 1.4), '#fff2c0')
    if det >= 1 and abs(du) > 0.3:
        inner = smooth([(AX + 13 * du, AY - 16), (AX + 6 * du, AY - 6), (AX + 10 * du, AY + 8), (AX + 4 * du, AY + 14)], False)
        c.line(inner, c.lw * 0.5, sp['skin_dp'], 190)
        c.glow(AX + 8 * du, AY, 9, 14, sh, 110)


def _eye(c, hm, sp, P, side, det, t, skin, sh):
    """One eye: big white, tiny pupil, lids, bags, veins, lashes. side -1 = screen-left eye (character's right)."""
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
    X, Y, V = hm.map1(ex0, ey0, 2.0)
    if V < 0.12: return None
    fs = hm.sx(ex0, ey0)
    r = sp['eye_r'] * (1.0 + 0.16 * P.wide) * (1.0 + 0.04 * P.brow_up)
    asym = P.brow_asym * 0.0
    op = clamp(P.eye_open * (1.0 - P.blink) * (1.0 - 0.45 * P.squint) + 0.18 * P.wide * (1 - P.blink), 0, 1.25)
    rx = r * fs
    # sockets and bags (under everything else of the eye)
    c.glow(X, Y + 2, rx * 1.9, r * 1.7, sp['skin_dp'], 46 + 34 * P.wide + 30 * sp['bags'])
    bags = sp['bags']
    if bags > 0:
        bag = smooth([(X - rx * 0.95, Y + r * 0.55), (X, Y + r * 1.42 + 3 * bags), (X + rx * 0.95, Y + r * 0.55), (X, Y + r * 1.05)], True, 0.9)
        c.fill(bag, mix(sh, sp['skin_dp'], 0.45), 80 * bags)
        if det >= 1:
            fold = smooth([(X - rx * 0.8, Y + r * 1.0), (X, Y + r * 1.48 + 3 * bags), (X + rx * 0.8, Y + r * 1.0)], False)
            c.line(fold, c.lw * 0.42, sp['skin_dp'], 150 * bags)
            if det >= 2 and bags > 0.7:
                f2 = smooth([(X - rx * 0.55, Y + r * 1.42), (X, Y + r * 1.78 + 2 * bags), (X + rx * 0.55, Y + r * 1.42)], False)
                c.line(f2, c.lw * 0.32, sp['skin_dp'], 90 * bags)
    if op < 0.07:                                                     # closed: lid curve + lashes
        lid = smooth([(X - rx * 1.02, Y + r * 0.05), (X, Y + r * 0.42), (X + rx * 1.02, Y + r * 0.05)], False)
        c.line(lid, c.lw * 1.05)
        if sp['lashes'] > 0:
            for k in (0.55, 0.85):
                x1 = X + side * rx * k; c.line(poly([(x1, Y + r * 0.25), (x1 + side * 6, Y + r * 0.55)], False), c.lw * 0.5)
        return (X, Y, r, fs)
    xs, ys = _circle_pts(X, Y, rx, r, 20)
    white = _pts_path(xs, ys)
    wc = '#ebe9e3' if P.pale < 0.5 else '#e3e3e1'
    c.fill(white, wc)
    if det >= 1:
        c.radial(white, X, Y + r * 0.15, r * 1.05, [(0, wc, 0), (0.62, wc, 0), (1, '#b9b0aa', 230)], sy=1.0)
    # pupils
    lock = clamp(P.lock)
    lx = lerp(P.look_x, -math.sin(hm.yaw) * 0.85, lock)
    ly = lerp(P.look_y, -math.sin(hm.pitch) * 1.1 - 0.05, lock)
    pr = r * 0.40 * sp['pupil'] * P.pupil
    pr = max(pr, 2.2)
    reach = r - pr - 1.5
    px = X + lx * reach * fs; py = Y + ly * reach
    with c.clip(white):
        if det >= 1 and P.bloodshot > 0.02:
            a_v = 150 * clamp(P.bloodshot)
            vs, vs2 = [], []
            for k in range(6 if det >= 2 else 3):
                ang = (hash01(k, 7 + side) * 2 - 1) * PI
                x1, y1 = X + math.cos(ang) * rx * 1.02, Y + math.sin(ang) * r * 1.02
                mx_, my_ = X + math.cos(ang + 0.3) * rx * 0.62, Y + math.sin(ang + 0.3) * r * 0.62
                x2, y2 = X + math.cos(ang - 0.15) * rx * 0.42, Y + math.sin(ang - 0.15) * r * 0.42
                vs.append(smooth([(x1, y1), (mx_, my_), (x2, y2)], False))
                if det >= 2:
                    vs2.append(smooth([(mx_, my_), (mx_ + math.cos(ang + 1.4) * r * 0.2, my_ + math.sin(ang + 1.4) * r * 0.2)], False))
            c.line(_multi(vs), c.lw * 0.22, '#b8424c', a_v)
            if vs2: c.line(_multi(vs2), c.lw * 0.15, '#c04a52', a_v * 0.8)
        if P.wet > 0 and det >= 1:
            c.fill(smooth([(X - rx, Y + r * 0.62), (X, Y + r * 0.85), (X + rx, Y + r * 0.62), (X, Y + r * 1.1)], True), '#a8c8f0', 120 * P.wet)
        c.fill(oval(px, py, pr * fs, pr), '#0b0b0e')
        cl = max(pr * 0.3, 1.6)
        c.fill(oval(px - pr * 0.38 * fs, py - pr * 0.38, cl * fs, cl), '#f4f4f2')
        if det >= 2: c.fill(oval(px + pr * 0.35 * fs, py + pr * 0.3, cl * 0.45 * fs, cl * 0.45), '#f4f4f2', 200)
        # upper lid
        lid_y = Y - r + (1.0 - min(op, 1.0)) * 2.0 * r
        if op < 0.99:
            lidp = smooth([(X - rx * 1.3, Y - r * 1.5), (X + rx * 1.3, Y - r * 1.5), (X + rx * 1.3, lid_y - r * 0.05),
                           (X, lid_y + r * 0.18 * (1 - op)), (X - rx * 1.3, lid_y - r * 0.05)], True, 0.6)
            c.fill(lidp, mix(skin, sh, 0.35))
            c.line(smooth([(X - rx * 1.1, lid_y - r * 0.05), (X, lid_y + r * 0.18 * (1 - op)), (X + rx * 1.1, lid_y - r * 0.05)], False), c.lw * 1.05)
        else:
            c.radial(None, X, Y - r * 1.05, rx * 1.1, [(0, '#5a4a4a', 70), (1, '#5a4a4a', 0)], sy=0.45, clip=False)
        # lower lid (squint / smile push)
        sq = P.squint * 0.75 + max(0.0, P.smile) * 0.12 * (1 - P.wide) * (0.0 if sp['lock'] >= 0.5 else 1.0)   # creepy: eyes never smile
        if sq > 0.03:
            ly2 = Y + r - sq * r * 1.1
            low = smooth([(X - rx * 1.3, Y + r * 1.5), (X - rx * 1.3, ly2 + r * 0.2), (X, ly2), (X + rx * 1.3, ly2 + r * 0.2), (X + rx * 1.3, Y + r * 1.5)], True, 0.6)
            c.fill(low, skin)
            c.line(smooth([(X - rx * 1.05, ly2 + r * 0.25), (X, ly2), (X + rx * 1.05, ly2 + r * 0.25)], False), c.lw * 0.6)
    c.line(white, c.lw * 0.85)
    if op < 0.99:
        c.line(smooth([(X - rx * 1.06, lid_y + r * 0.02), (X, lid_y + r * 0.18 * (1 - op) - 1), (X + rx * 1.06, lid_y + r * 0.02)], False), c.lw * 1.15)
    if sp['lashes'] > 0 and det >= 1:
        ly_ = max(Y - r, lid_y if op < 0.99 else Y - r)
        for k, ln in ((0.62, 7), (0.86, 9), (1.0, 8)):
            ang = -PI / 2 + side * k * 1.25
            x1, y1 = X + math.cos(ang) * rx, ly_ + (Y - r - ly_) * 0 + (math.sin(ang) + 1) * r * 0.5 * (1 if op >= 0.99 else 0.3)
            c.line(poly([(x1, y1), (x1 + side * ln * 0.75 * fs, y1 - ln * 0.6)], False), c.lw * 0.45 * sp['lashes'])
    # lower lash line
    if det >= 1:
        c.line(smooth([(X - rx * 0.7, Y + r * 0.86), (X, Y + r * 1.06), (X + rx * 0.7, Y + r * 0.86)], False), c.lw * 0.4, sp['skin_dp'], 120)
    return (X, Y, r, fs)


def _brow(c, hm, sp, P, side, eyeinfo):
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']; r = sp['eye_r'] * (1 + 0.16 * P.wide)
    up = P.brow_up + (P.brow_asym * 0.5 * side)
    if sp['hair'] == 'messy': up = min(up, 0.55)              # keep the brow tops clear of the fringe
    base = ey0 - r - 15 - 13 * up
    inner_dy = 13 * P.brow_angry - 14 * P.brow_sad
    outer_dy = -5 * P.brow_angry + 7 * P.brow_sad
    th = sp['brow_th']
    xi, xo = ex0 - side * 24, ex0 + side * 28
    pts_top = [(xi, base + inner_dy - th * 0.55), ((xi + xo) / 2, base - 6 - th * 0.5 + (inner_dy + outer_dy) * 0.3), (xo, base + outer_dy - th * 0.1)]
    pts_bot = [(xo, base + outer_dy + th * 0.25), ((xi + xo) / 2, base - 6 + th * 0.55 + (inner_dy + outer_dy) * 0.3), (xi, base + inner_dy + th * 0.55)]
    allp = pts_top + pts_bot
    X, Y, V = hm.map([p[0] for p in allp], [p[1] for p in allp], 3.0)
    if V.mean() < 0.1: return
    path = _pts_path(X, Y, True, 0.8)
    c.fill(path, sp['brow_c'])
    c.line(path, c.lw * 0.3, sp['brow_c'])


def _nose(c, hm, sp, P, det, skin, sh):
    L = sp['nose_len']; ey = sp['eye_y']
    root_y, tip_y = ey + 4, sp['mouth_y'] - 28
    side = 1.0 if hm.st >= -0.05 else -1.0
    turned = abs(hm.st) > 0.32
    # soft shade under the nose
    X, Y, V = hm.map1(0, tip_y + 6, L * 0.4)
    if V > -0.2 and not turned:
        c.glow(X + 6 * side, Y + 4, 20, 9, sh, 90)
    if not turned:
        pts = [(side * 5, root_y + 6), (side * 9, tip_y - 6), (side * 13, tip_y + 2), (side * 7, tip_y + 9), (-side * 4, tip_y + 8)]
        dz = [3, L * 0.7, L * 0.85, L * 0.55, L * 0.35]
        X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], np.array(dz))
        c.line(_pts_path(X, Y, False, 0.8), c.lw * 0.85)
        if det >= 1:
            for s2 in (-1, 1):
                nx, ny, nv = hm.map1(s2 * 9, tip_y + 6, L * 0.4)
                if nv > 0.1: c.fill(oval(nx, ny, 3.2 * hm.sx(s2 * 9, tip_y + 6), 2.2), sp['skin_dp'], 160)
        return
    pts = [(0, root_y), (0, tip_y), (0, tip_y + 8), (side * 0.0, tip_y + 12)]
    dz = np.array([4.0, L * 1.05, L * 0.7, 2.0])
    X, Y, V = hm.map([0, 0, 0, 0], [root_y, tip_y, tip_y + 9, tip_y + 13], dz)
    wedge = smooth([(X[0], Y[0]), (X[1], Y[1]), (X[2], Y[2]), (X[3] - side * 8, Y[3]), (X[0] - side * 10, Y[0] + 8)], True, 0.5)
    c.fill(wedge, skin)
    c.line(_pts_path(X[:3], Y[:3], False, 0.7), c.lw * 0.9)
    nx = X[2] - side * 9; ny = Y[2] - 1
    c.line(smooth([(nx + side * 5, ny - 6), (nx, ny), (nx + side * 4, ny + 3)], False), c.lw * 0.55)


def _mouth_geom(sp, P, t):
    """Mouth contour in front coords: returns (upper pts, lower pts, corner y, half width, open height)."""
    my = sp['mouth_y']
    o, wd, rd, sm, g = clamp(P.m_open), P.m_wide, clamp(P.m_round), clamp(P.smile, -1, 1), clamp(P.grin)
    hw = sp['mouth_w'] * (1.0 + 0.32 * wd - 0.48 * rd + 0.12 * o) + 10.0 * max(sm, 0) + 54.0 * g
    hw = max(hw, 8.0)
    cy = my - 12.0 * sm - 15.0 * g - 3 * o * (1 - rd)
    side_lift = 9.0 * P.m_side
    up_mid = my + 3.0 * g + 1.5 * max(sm, 0) - 5.0 * o * rd - 1.0 * o - 3.0 * min(sm, 0) * 0.3
    open_h = 42.0 * o * (1 + 0.2 * rd) + 31.0 * g + 4.0 * max(sm, 0) * clamp(P.teeth) * (1 - g)
    lo_mid = up_mid + open_h
    # roundness pulls corners toward mid height
    cyr = lerp(cy, (up_mid + lo_mid) * 0.5, rd * min(1.0, o * 3))
    dn = clamp(-sm) * clamp((o - 0.4) / 0.35)                         # v2.1: terror pulls the corners down (∩ upper lip)
    cyr += dn * 0.34 * (lo_mid - up_mid)
    cl_y, cr_y = cyr - side_lift, cyr + side_lift * 0.4
    q = 0.55 + 0.3 * rd
    qu = q + 0.08 * dn; ql = q + 0.2 * dn
    upper = [(-hw, cl_y), (-hw * qu, up_mid - 0.2 * (up_mid - cl_y) - 2 * rd * o + 2 * dn), (0, up_mid), (hw * qu, up_mid - 0.2 * (up_mid - cr_y) - 2 * rd * o + 2 * dn), (hw, cr_y)]
    lower = [(hw, cr_y), (hw * ql, lo_mid - 0.35 * (lo_mid - cr_y) * (1 - rd) * (1 - dn)), (0, lo_mid), (-hw * ql, lo_mid - 0.35 * (lo_mid - cl_y) * (1 - rd) * (1 - dn)), (-hw, cl_y)]
    if P.tremble > 0.01:
        f = 2.6 * P.tremble
        for arr in (upper, lower):
            for i in range(1, len(arr) - 1):
                x_, y_ = arr[i]
                arr[i] = (x_, y_ + f * math.sin(x_ * 0.28 + t * 31.0 + i) + f * 0.6 * noise1(t * 9 + i, 5))
    return upper, lower, (cl_y, cr_y), hw, lo_mid - up_mid


def _densify(pts, n=3):
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for k in range(n):
            u = k / n; out.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
    out.append(pts[-1]); return out


def _mouth(c, hm, sp, P, det, t, skin, sh):
    upper, lower, (cly, cry), hw, oh = _mouth_geom(sp, P, t)
    dzf = lambda xs: 10.0 - 0.0 * np.asarray(xs)   # noqa: E731
    up_d = _densify(upper, 3); lo_d = _densify(lower, 3)
    UX, UY, UV = hm.map([p[0] for p in up_d], [p[1] for p in up_d], 6.0)
    if UV.max() < 0.1: return
    LX, LY, _ = hm.map([p[0] for p in lo_d], [p[1] for p in lo_d], 6.0)
    sm, g, te = P.smile, P.grin, clamp(P.teeth)
    # folds that make smiles read: nasolabial lines, cheek bulges, dimples
    fold_a = clamp(0.28 * sp['age'] + 0.55 * max(sm, 0) + 0.5 * g + 0.25 * P.m_wide)
    if fold_a > 0.05:
        for s in (-1, 1):
            cx_ = s * (hw + 7)
            pts = [(s * 22, sp['mouth_y'] - 30), (s * (hw * 0.55 + 22), sp['mouth_y'] - 14 - 6 * g), (cx_, (cly if s < 0 else cry) + 6)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 5.0)
            if V.min() > 0.0: c.line(_pts_path(X, Y, False), c.lw * (0.5 + 0.2 * g), sp['skin_dp'], 200 * fold_a)
    if g > 0.25 and det >= 1:
        for s in (-1, 1):
            pts = [(s * 50, sp['eye_y'] + 34), (s * 64, sp['eye_y'] + 42), (s * 72, sp['eye_y'] + 34)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 3.0)
            if V.min() > 0.05: c.line(_pts_path(X, Y, False), c.lw * 0.45, sp['skin_dp'], 160 * (g - 0.25) / 0.75)
    lipk = sp.get('lips', 0.0)
    if lipk > 0 and det >= 1:                                         # coloured lips (officer2, mum)
        top_ = [(x, y - 5.5 * (1 - abs(x) / (hw + 1e-6)) ** 0.6 - 1.0) for x, y in up_d]
        bot_ = [(x, y + 8.5 * (1 - abs(x) / (hw + 1e-6)) ** 0.7 + 1.0) for x, y in lo_d]
        TX, TY, _ = hm.map([p[0] for p in top_], [p[1] for p in top_], 7.0)
        BX, BY, _ = hm.map([p[0] for p in bot_], [p[1] for p in bot_], 7.0)
        lips = _pts_path(np.concatenate([TX, BX[1:-1]]), np.concatenate([TY, BY[1:-1]]), True, 0.85)
        c.fill(lips, sp['lip'], 255 * lipk)
        c.line(lips, c.lw * 0.45, mix(sp['lip'], '#000000', 0.45), 200 * lipk)
        if det >= 2: c.glow(float(BX[len(BX) // 2]) - 4, float(BY[len(BY) // 2]) - 4, 9, 3, '#ffffff', 90 * lipk)
    if oh < 2.2:                                                      # closed mouth: one expressive line
        line = _pts_path(UX, UY, False, 0.9)
        c.line(line, c.lw * (0.95 + 0.25 * P.m_press))
        if det >= 1:
            lx_, ly_, lv = hm.map1(0, max(p[1] for p in upper) + 10 + 3 * P.m_press, 8.0)
            if lv > 0: c.line(smooth([(lx_ - 11, ly_), (lx_, ly_ + 2.5), (lx_ + 11, ly_)], False), c.lw * 0.45, sp['skin_dp'], 150)
            for s in (-1, 1):
                if sm > 0.2 or P.m_press > 0.2:
                    i = 0 if s < 0 else -1
                    x_, y_ = UX[i], UY[i]
                    c.line(smooth([(x_ - s * 2, y_ - 6), (x_ + s * 3, y_), (x_ - s * 1, y_ + 6)], False), c.lw * 0.45, LINE, 200)
        return
    ring_x = np.concatenate([UX, LX[1:-1]]); ring_y = np.concatenate([UY, LY[1:-1]])
    inner = _pts_path(ring_x, ring_y, True, 0.85)
    # lip volume below the mouth (close-ups)
    if det >= 1:
        lip = _pts_path(np.concatenate([LX, LX[::-1]]), np.concatenate([LY, (LY + 9 + 4 * P.m_open)[::-1]]), True, 0.8)
        c.fill(lip, mix(sp['lip'], skin, 0.4), 110)
    c.fill(inner, '#2a0e11')
    mid_x = float(np.mean(ring_x)); bot = float(LY[len(LY) // 2]); top = float(UY[len(UY) // 2])
    with c.clip(inner):
        if oh > 16 and g < 0.8:
            c.fill(oval(mid_x, bot - oh * 0.08, hw * 0.62 * hm.sx(0, sp['mouth_y']), oh * 0.32), '#93434d')
            if det >= 1: c.line(smooth([(mid_x, bot - oh * 0.3), (mid_x, bot - oh * 0.05)], False), c.lw * 0.35, '#5e2129', 150)
        c.glow(mid_x, top + oh * 0.55, hw * 0.9, oh * 0.6, '#000000', 140)
        tshow = max(te, 0.85 * clamp(g * 1.4))
        if tshow > 0.02:
            gum = 7.0 * clamp(P.gums) + 2.0 * g
            th_u = min(oh * (0.5 if g > 0.3 else 0.42), 13.0 + 6 * g) * clamp(tshow * 1.3)
            th_u *= 1.0 - clamp(-min(sm, 0.0) * 1.6) * clamp((P.m_open - 0.4) / 0.3)   # terror: bottom row only
            th_l = min(oh * (0.5 if g > 0.3 else 0.3), 11.0 + 6 * g) * clamp(tshow * 1.3) * (1.0 if g > 0.2 or P.m_wide > 0.3 else 0.6)
            if gum > 0.3:
                gp = _pts_path(np.concatenate([UX, UX[::-1]]), np.concatenate([UY - 2, (UY + gum)[::-1]]), True, 0.8)
                c.fill(gp, '#b9616d')
                if det >= 1: c.line(_pts_path(UX, UY + gum, False), c.lw * 0.3, '#7d3540', 160)
            _teeth_row(c, hm, sp, UX, UY + gum, th_u, +1, det, P, hw)
            if th_l > 1.0:
                _teeth_row(c, hm, sp, LX[::-1], LY[::-1], th_l, -1, det, P, hw)
    c.line(inner, c.lw)
    for s, i in ((-1, 0), (1, -1)):                                   # corner tucks
        x_, y_ = UX[i], UY[i]
        c.line(smooth([(x_ + s * 1, y_ - 7), (x_ + s * 4, y_), (x_ + s * 1, y_ + 7)], False), c.lw * 0.55)


def _teeth_row(c, hm, sp, X, Y, th, direction, det, P, hw):
    """A row of individual teeth hanging from (upper, direction +1) or standing on (lower, -1) the contour X, Y."""
    X = np.asarray(X); Y = np.asarray(Y)
    x0, x1 = float(X[0]), float(X[-1])
    span = x1 - x0
    if span < 4: return
    n = int(clamp(round(abs(span) / (13.0 if det >= 1 else 18.0)), 4, 16))
    if n % 2: n += 1
    edges = np.linspace(0, 1, n + 1)
    # front teeth wider: warp positions toward the centre
    edges = 0.5 + (edges - 0.5) * (0.82 + 0.18 * np.abs(edges - 0.5) * 2)
    ex = x0 + edges * span
    ey = np.interp(ex, X if x1 > x0 else X[::-1], Y if x1 > x0 else Y[::-1])
    # band polygon
    band_pts = []
    bot = []
    for i in range(n):
        xa, xb = ex[i], ex[i + 1]
        ya, yb = ey[i], ey[i + 1]
        centre = abs((i + 0.5) / n - 0.5) * 2
        h = th * (1.0 - 0.38 * centre ** 2) * (0.92 + 0.12 * hash01(i, 31))
        bot.append((xa, ya + direction * h * 0.92))
        bot.append(((xa + xb) / 2, (ya + yb) / 2 + direction * h))
    bot.append((ex[-1], ey[-1] + direction * th * 0.55))
    top = list(zip(ex.tolist(), (ey - direction * 3).tolist()))
    band = poly(top + bot[::-1], True)
    tooth = '#e8e2d2'
    c.fill(band, tooth)
    if det >= 1:
        cxm = (x0 + x1) / 2
        c.grad(band, x0, 0, x1, 0, [(0, '#8e8470', 255), (0.22, tooth, 0), (0.78, tooth, 0), (1, '#8e8470', 255)])
        if det >= 2:
            for i in range(n):                                        # grime on a couple of teeth
                hv = hash01(i, 77 + int(P.grin * 0))
                if hv > 0.8:
                    xa, xb = ex[i], ex[i + 1]
                    c.fill(rect(min(xa, xb) + 1, min(ey[i], ey[i] + direction * th) , abs(xb - xa) - 2, th), '#b4a27a', 70)
    c.line(_pts_path(np.array([p[0] for p in bot]), np.array([p[1] for p in bot]), False, 0.6), c.lw * 0.45)
    seps = []
    for i in range(1, n):
        ya = ey[i]
        h = th * (1.0 - 0.38 * (abs(i / n - 0.5) * 2) ** 2) * 0.95
        seps.append(poly([(ex[i], ya - direction * 2), (ex[i] + (0.6 if ex[i] < (x0 + x1) / 2 else -0.6), ya + direction * h)], False))
    c.line(_multi(seps), c.lw * (0.42 if det >= 1 else 0.5))


def _jaw_y(sp, x):
    """Front-view y of the face outline below the cheek at |x| (where a tear running down meets the jaw)."""
    ys = np.asarray(sp['head_ys'], float); ws = np.asarray(sp['head_ws'], float)
    k = ys >= 20.0
    yy, ww = ys[k][::-1], ws[k][::-1]                    # ascending width from the chin up
    return float(np.interp(abs(x), ww, yy))


def _tears(c, hm, sp, P, t, det, eyes):
    """v2.1 tears: 2 pale-blue (#a8c8f0) tapered wet streaks per eye with a thin white highlight, no dark outline. They
    run down the cheek and stop at the jaw outline, where a drop gathers and falls. Below the glasses rim on mum."""
    a = clamp(P.tears)
    if a <= 0.01: return
    glasses = sp.get('glasses')
    for side, info in eyes.items():
        if info is None: continue
        ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']; r = sp['eye_r']
        for k, off in enumerate((-0.42, 0.5)):
            x_start = ex0 + side * off * r
            y_start = ey0 + r * 0.92 + (31.0 - r * 0.92 if glasses else 0.0)
            drift = side * (5 + 4 * k)
            y_end = _jaw_y(sp, x_start + drift) - 3.0
            Lmax = max(4.0, y_end - y_start)
            L = Lmax * clamp(a * 1.25) * (0.88 + 0.12 * k)
            n = 9
            us = np.linspace(0, 1, n)
            xs = x_start + drift * us + 2.2 * np.sin(us * 5 + k * 2 + side) * us
            ys = y_start + L * us
            w = (2.3 - 0.9 * us) * (0.75 + 0.25 * a)
            X, Y, V = hm.map(xs, ys, 4.0)
            if V[0] < 0.1 or V[-1] < 0.0: continue
            dx = np.gradient(X); dy = np.gradient(Y); nn = np.hypot(dx, dy) + 1e-6
            nxs, nys = -dy / nn, dx / nn
            Lx = np.concatenate([X + nxs * w, (X - nxs * w)[::-1]]); Ly = np.concatenate([Y + nys * w, (Y - nys * w)[::-1]])
            rib = _pts_path(Lx, Ly, True, 0.7)
            c.fill(rib, '#a8c8f0', 200)
            if det >= 1: c.line(_pts_path(X - nxs * w * 0.35, Y - nys * w * 0.35, False), c.lw * 0.22, '#f4f9ff', 220)
            # one bead running down the streak
            u = ((t * (0.45 + 0.1 * k) + hash01(3 * k + side + 1, 11)) % 1.0)
            if det >= 1 and u * L > 6:
                i_f = u * (n - 1); i0 = int(i_f); fr = i_f - i0; i1 = min(i0 + 1, n - 1)
                bx = X[i0] + (X[i1] - X[i0]) * fr; by = Y[i0] + (Y[i1] - Y[i0]) * fr
                bw = w[i0] * 1.25
                c.fill(smooth([(bx, by - bw * 1.7), (bx + bw, by + bw * 0.2), (bx, by + bw * 1.15), (bx - bw, by + bw * 0.2)], True), '#bcd8f8', 220)
                c.fill(oval(bx - bw * 0.3, by - bw * 0.15, bw * 0.3), '#ffffff', 220)
            if a > 0.7 and L >= Lmax * 0.85:                     # a drop gathers on the jaw line and falls
                u2 = (t * 0.6 + 0.37 * k + 0.5 * side) % 1.0
                grow = clamp(u2 / 0.6); fall = clamp((u2 - 0.6) / 0.4)
                bx, by = X[-1], Y[-1] + 2 + 40.0 * ease_in_cubic(fall)
                rr = (1.6 + 2.2 * grow) * (0.8 + 0.2 * a)
                c.fill(smooth([(bx, by - rr * 1.5), (bx + rr, by + rr * 0.3), (bx, by + rr * 1.2), (bx - rr, by + rr * 0.3)], True), '#bcd8f8',
                       230 * (1 - 0.7 * fall))


def _sweat(c, hm, sp, P, t, det):
    a = clamp(P.sweat)
    if a <= 0.02: return
    spots = [(-58, -66, 0), (32, -72, 1), (70, -40, 2), (-74, -20, 3), (8, -60, 4), (52, 6, 5)]
    for (x0, y0, k) in spots[:int(2 + 4 * a)]:
        slide = ((t * 0.08 + hash01(k, 3)) % 1.0)
        yy = y0 + 22 * slide
        X, Y, V = hm.map1(x0, yy, 3.0)
        if V < 0.15: continue
        s_ = (5.5 + 2 * hash01(k, 9)) * (0.7 + 0.3 * a)
        d = smooth([(X, Y - s_ * 1.7), (X + s_, Y + s_ * 0.3), (X, Y + s_ * 1.1), (X - s_, Y + s_ * 0.3)], True)
        c.fill(d, '#dde8f2', 200 * (1 - 0.5 * slide))
        c.line(d, c.lw * 0.28, '#7d93ab', 200 * (1 - 0.5 * slide))
        c.fill(oval(X - s_ * 0.3, Y - s_ * 0.2, s_ * 0.3), '#ffffff', 220)


def _wrinkles(c, hm, sp, P, det, sh):
    """v2.1: a few clean fold lines (VISUAL_SPEC: flat fills, one shade step, no hatching). Forehead folds only when the
    brows lift (2, a third on big lifts), frown lines only on angry / pained brows, one chin crease, soft jowls on the
    old. Eye bags (drawn with the eyes) carry the age. Weight 0.35x the outline."""
    age = sp['age']
    dp = sp['skin_dp']
    ey = sp['eye_y']; r = sp['eye_r']
    lw = c.lw * 0.35
    lift = P.brow_up + 0.6 * P.brow_sad + 0.3 * P.wide
    a_f = clamp((lift - 0.3) / 0.5)
    if a_f > 0.03 and det >= 1:
        folds = []
        for k, yy in enumerate((-60, -49, -39)):
            if k == 2 and (det < 2 or a_f < 0.6): break
            w_ = 34 - k * 6
            mid = yy - 3 - 3 * P.brow_sad
            pts = [(-w_, yy + 2), (0, mid), (w_, yy + 2)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 2.0)
            if V.min() > 0.05: folds.append(_pts_path(X, Y, False))
        if folds: c.line(_multi(folds), lw, dp, 150 * a_f)
    a_v = clamp(1.1 * P.brow_angry + 0.6 * P.brow_sad - 0.25)
    if a_v > 0.05 and det >= 1:
        ls = []
        for s_ in (-1, 1):
            pts = [(s_ * 7, ey - r - 21), (s_ * 9, ey - r - 9)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 4.0)
            if V.min() > 0.1: ls.append(_pts_path(X, Y, False))
        if ls: c.line(_multi(ls), lw * 1.1, dp, 160 * a_v)
    if det >= 1:
        a_ch = clamp(0.2 * age + 0.5 * max(-P.smile, 0) + 0.4 * P.m_press)
        cy_ = min(100.0, _jaw_y(sp, 0.0) - 18)
        X, Y, V = hm.map([-11, 0, 11], [cy_, cy_ - 3 - 3 * P.m_press, cy_], 6.0)
        if V.min() > 0.1 and a_ch > 0.05: c.line(_pts_path(X, Y, False), lw, dp, 140 * a_ch)
        if age > 0.7:
            ls = []
            for s_ in (-1, 1):
                ys_ = [66.0, 80.0, 92.0]
                xs_ = [s_ * 0.66 * float(np.interp(y_, sp['head_ys'], sp['head_ws'])) for y_ in ys_]
                X, Y, V = hm.map(xs_, ys_, 3.0)
                if V.min() > 0.1: ls.append(_pts_path(X, Y, False))
            if ls: c.line(_multi(ls), lw, dp, 90 * age)


def _scar(c, hm, sp, side, det):
    x0, y0 = side * (sp['mouth_w'] + 9), sp['mouth_y'] + 2
    X, Y, V = hm.map([x0, x0 + side * 4, x0 + side * 6], [y0 - 9, y0 + 1, y0 + 11], 6.0)
    if V.min() < 0.12: return
    p = _pts_path(X, Y, False)
    c.line(p, c.lw * 0.75, '#d8a39d', 255)
    c.line(p, c.lw * 0.3, '#8d5552', 200)
    if det >= 1:
        for k in range(3):
            u = 0.2 + 0.3 * k
            x_ = X[0] + (X[-1] - X[0]) * u; y_ = Y[0] + (Y[-1] - Y[0]) * u
            c.line(poly([(x_ - 4, y_ + 1.5), (x_ + 4, y_ - 1.5)], False), c.lw * 0.22, '#8d5552', 180)


def _stubble(c, hm, sp, det, sil):
    a = sp['stub']
    if a <= 0 or not sp.get('stubble'): return
    my = sp['mouth_y']
    pts = [(-92, 34), (-84, 82), (-58, 108), (0, 122), (58, 108), (84, 82), (92, 34), (60, my - 6), (24, my - 16), (0, my - 14),
           (-24, my - 16), (-60, my - 6)]
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 1.0)
    reg = inter(_pts_path(X, Y, True, 0.8), sil)
    c.fill(reg, sp['stubble'], 26 * a)


def _hair_region(c, hm, sp, P, det, sil, t):
    style = sp['hair']; hc = sp['hair_c']
    hsh = mix(hc, '#000000', 0.35); hhi = mix(hc, '#ffffff', 0.25)
    part = sp['part']
    if style == 'short':
        def yf(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 1.05, 1.25, 1.62, 2.3, PI], [-74, -72, -30, -24, 12, 30])
        grow = 3.0
    elif style == 'bun':
        def yf(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.55, 0.95, 1.3, 1.7, 2.3, PI], [-74, -72, -50, -6, 4, 26, 36])
        grow = 6.0
    elif style == 'messy':
        def yf(ph):
            a = np.abs(ph)
            fr = -70.0 + 6.0 * np.sin(ph * 3.0 + part) + 7.0 * part * np.clip(ph * part, 0, 1)
            return np.interp(a, [0, 1.0, 1.3, 1.6, 2.0, PI], [0, 0, 1, 1, 1, 1]) * (np.interp(a, [1.0, 1.3, 1.6, 2.2, PI], [-60, -24, -14, 26, 46])) + \
                (1 - np.interp(a, [0, 1.0, 1.3], [0, 0, 1])) * fr
        grow = 9.0
    else:  # curly
        def yf(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.9, 1.25, 1.55, 2.0, PI], [-58, -54, -20, -6, 30, 44])
        grow = 22.0
    X, Y = hm.arc(yf, 44)
    if len(X) < 3: return
    order = np.argsort(X)
    X, Y = X[order], Y[order]
    top = -400.0
    region = poly([(float(X[0]) - 300, top)] + [(float(x), float(y)) for x, y in zip(X, Y)] + [(float(X[-1]) + 300, top)], True)
    vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.4, y_bot=70)
    if style == 'curly':
        vol = _cloud(hm, grow, 14, 11.0)
    elif style == 'messy':
        vol = _bumpy(hm, grow, 9, 9.0, -128.0, 40.0, spiky=True, seed=part)
    hair = inter(union(vol, sil), region)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -90, 175, [(0, hhi, 120), (0.5, hc, 0), (1, hsh, 200)], clip=False)
        if det >= 1 and style in ('messy', 'short', 'bun'):
            for k in range(7 if det >= 2 else 4):
                x_ = -70 + k * 22 + 6 * part
                c.line(smooth([(x_, -112), (x_ + 10 * part + 6, -92), (x_ + 4 + 8 * part, -70)], False), c.lw * 0.3, hsh, 150)
        if style == 'curly':
            _curls(c, hm, det, hc, hsh, hhi)
    c.line(hair, c.lw)
    if style == 'bun':
        pass


def _bumpy(hm, grow, n, amp, ytop, ybot, spiky=False, seed=0):
    ys = np.linspace(ytop, ybot, 30)
    ws = hm.W(np.clip(ys, -119.9, 119.9)) + grow
    ws = np.where(ys < -119, grow * 0.6 + 40, ws)
    xl, xr = hm.extent(ws)
    m = len(ys)
    ring = [(float(xr[i]), float(ys[i])) for i in range(m)] + [(float(xl[i]), float(ys[i])) for i in range(m - 1, -1, -1)]
    cx_ = float(np.mean([p[0] for p in ring])); cy_ = -20.0
    pts = []
    for i, (x, y) in enumerate(ring):
        ang = math.atan2(y - cy_, x - cx_)
        if spiky:
            bump = amp * (0.5 + 0.5 * math.sin(ang * n + seed * 1.7)) ** 3 * (1 if y < -30 else 0.3)
        else:
            bump = amp * abs(math.sin(ang * n)) ** 0.8
        d = math.hypot(x - cx_, y - cy_) + 1e-6
        pts.append((x + (x - cx_) / d * bump, y + (y - cy_) / d * bump))
    return smooth(pts, True, 0.9)


def _cloud(hm, grow, n, amp):
    """Curly hair cloud: an ellipse over the skull with round bumps, following the head's turn."""
    xl, xr = hm.extent(float(hm.W(-20.0)) + grow)
    cx, rx = (xl + xr) / 2, (xr - xl) / 2
    cy, ry = -22.0, 104.0 + grow * 0.75
    angs = np.linspace(math.radians(158), math.radians(382), 64)
    pts = []
    for a in angs:
        k = 1.0 + amp / rx * abs(math.sin(n * a)) ** 0.7
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    pts += [(cx + rx * 0.92, 70.0), (cx - rx * 0.92, 70.0)]
    return smooth(pts, True, 0.9)


def _curls(c, hm, det, hc, hsh, hhi):
    xl, xr = hm.extent(float(hm.W(-20.0)) + 18.0)
    cx, rx = (xl + xr) / 2, (xr - xl) / 2
    dark, light = skia.Path(), skia.Path()
    for k in range(34 if det >= 2 else 16):
        a = math.radians(165 + 210 * hash01(k, 41))
        rr = 0.35 + 0.62 * hash01(k, 43) ** 0.6
        x, y = cx + math.cos(a) * rx * rr, -22 + math.sin(a) * 118 * rr
        rad = 7 + 7 * hash01(k, 47)
        st = 360 * hash01(k, 49)
        dark.addArc(skia.Rect.MakeLTRB(x - rad, y - rad, x + rad, y + rad), st, 230)
        if det >= 2: light.addArc(skia.Rect.MakeLTRB(x - rad * 0.55 - 2, y - rad * 0.55 - 3, x + rad * 0.55 - 2, y + rad * 0.55 - 3), 200, 80)
    c.line(dark, c.lw * 0.42, hsh, 170)
    if det >= 2: c.line(light, c.lw * 0.32, hhi, 170)


def _cap(c, hm, sp, P, det, cl, t):
    """Police peaked cap: band, flared crown, badge, gold cord and a glossy black visor that shadows the eyes."""
    navy, navy_sh = cl['cap'], cl['cap_sh']
    grow = 7.0
    (l0, r0), (l1, r1) = [hm.extent(float(hm.W(y)) + grow, 0.95, 1.1) for y in (-100.0, -72.0)]
    band = smooth([(l0, -100), (r0, -100), (r1, -70), (l1, -70)], True, 0.25)
    wc = 120.0
    cl_, cr_ = hm.extent(wc, 1.0, 1.12)
    sh_c = (cl_ + cr_) / 2; half_c = (cr_ - cl_) / 2
    lift = 12.0 * hm.spi
    crown = smooth([(l0 + 2, -96), (cl_, -128 - lift * 0.3), (sh_c - half_c * 0.72, -141 - lift), (sh_c, -145 - lift),
                    (sh_c + half_c * 0.72, -141 - lift), (cr_, -128 - lift * 0.3), (r0 - 2, -96)], True, 0.7)
    # visor (behind band when facing away)
    phis = np.linspace(-1.15, 1.15, 13)
    vy0 = -72.0
    w = float(hm.W(vy0)) + grow
    vx_in = w * np.sin(phis)
    dz_out = 30.0 * np.cos(phis) ** 1.2 + 3
    X_in, Y_in, V_in = hm.map(vx_in, np.full_like(phis, vy0), grow * np.cos(phis))
    X_out, Y_out, _ = hm.map(vx_in * 1.03, np.full_like(phis, vy0 + 4) + 15 * np.cos(phis) ** 0.7, grow + dz_out)
    vis_v = float(V_in[len(V_in) // 2])
    visor = _pts_path(np.concatenate([X_in, X_out[::-1]]), np.concatenate([Y_in, Y_out[::-1]]), True, 0.7)
    # visor shadow over the face
    if vis_v > -0.2:
        sy_ = float(np.max(Y_out)) - 2
        c.grad(inter(hm.silhouette(), rect(-140, sy_ - 30, 280, 100)), 0, sy_ - 4, 0, sy_ + 34 + 30 * max(0.0, P.h_nod),
               [(0, '#0b0d14', 170), (1, '#0b0d14', 0)])
    if vis_v <= 0:
        c.shape(visor, cl['visor'])
    c.fill(crown, navy)
    with c.clip(crown):
        c.grad(crown, 0, -146, 0, -96, [(0, mix(navy, '#ffffff', 0.12), 255), (0.6, navy, 255), (1, navy_sh, 255)])
        c.fill(_crescent(crown, -30, 0), navy_sh, 150)
    c.line(crown, c.lw)
    c.fill(band, cl['visor'] if det < 1 else '#11141c')
    with c.clip(band):
        if det >= 1:
            c.line(_multi([poly([(k * 16, -100), (k * 16 + 6, -70)], False) for k in range(-8, 9)]), c.lw * 0.25, '#2a2f3d', 140)
    c.line(band, c.lw)
    # gold chin cord on the band front
    if vis_v > 0.0:
        Xc, Yc, Vc = hm.map(np.linspace(-0.85, 0.85, 9) * w * 0.9, np.full(9, -80.0), grow + 1)
        c.line(_pts_path(Xc, Yc, False), c.lw * 1.25, cl['gold_sh'])
        c.line(_pts_path(Xc, Yc - 1, False), c.lw * 0.6, cl['gold'])
        for s in (0, -1):
            c.fill(oval(Xc[s], Yc[s], 5.5), cl['gold']); c.line(oval(Xc[s], Yc[s], 5.5), c.lw * 0.5)
    # cap badge
    bx, by, bv = hm.map1(0, -114, 14)
    if bv > 0.1:
        fs = hm.sx(0, -114, 14)
        cb = c.sub(bx, by, 0, fs, 1.0)
        shield = smooth([(0, -20), (13, -14), (16, 2), (8, 15), (0, 21), (-8, 15), (-16, 2), (-13, -14)], True, 0.6)
        cb.fill(shield, cl['gold'])
        cb.radial(shield, -4, -6, 22, [(0, cl['gold_hi'], 255), (0.5, cl['gold'], 255), (1, cl['gold_sh'], 255)])
        cb.line(shield, c.lw * 0.7)
        if det >= 1:
            cb.fill(oval(0, 0, 6.5), '#26386e'); cb.line(oval(0, 0, 6.5), c.lw * 0.35)
            cb.fill(oval(-1.5, -1.5, 2), cl['gold_hi'])
    if vis_v > 0:
        c.fill(visor, cl['visor'])
        with c.clip(visor):
            hx = float(X_out[len(X_out) // 2])
            c.radial(None, hx - 30, float(Y_in.mean()) + 6, 70, [(0, '#5b6378', 200), (0.5, '#2a2f3d', 90), (1, '#0a0c11', 0)], sy=0.25, clip=False)
            if det >= 1:
                c.line(_pts_path(X_in * 0.98 + X_out * 0.02, Y_in + 3, False), c.lw * 0.5, '#4a5163', 200)
        c.line(visor, c.lw)


def _glasses(c, hm, sp, P, det, eyes, t):
    fr = '#3a2f2c'
    pts_c = []
    for side, info in eyes.items():
        ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
        X, Y, V = hm.map1(ex0, ey0 + 2, 18.0)
        if V < 0.05: continue
        fs = hm.sx(ex0, ey0, 18.0)
        rx, ry = 31 * fs, 25
        lens = rrect(X - rx, Y - ry, rx * 2, ry * 2, 14)
        c.fill(lens, '#d9e6f2', 38)
        g = 0.5 + 0.5 * math.sin(t * 0.7 + side) if P.glint <= 0 else P.glint
        with c.clip(lens):
            c.fill(poly([(X - rx * 0.6 + 40 * g - 20, Y - ry), (X - rx * 0.2 + 40 * g - 20, Y - ry), (X - rx * 0.9 + 40 * g - 20, Y + ry),
                         (X - rx * 1.3 + 40 * g - 20, Y + ry)]), '#ffffff', 70)
        c.line(lens, c.lw * 0.75, fr)
        pts_c.append((side, X, Y, rx))
    if len(pts_c) == 2:
        (s0, x0, y0, r0), (s1, x1, y1, r1) = sorted(pts_c, key=lambda p: p[1])
        c.line(smooth([(x0 + r0, y0 - 6), ((x0 + x1) / 2, y0 - 12), (x1 - r1, y1 - 6)], False), c.lw * 0.7, fr)
    for side, X, Y, rx in pts_c:
        ear_x, ear_y, ev = hm.map1(side * float(hm.W(0)), -2, -6)
        if ev > -0.6 and abs(ear_x - X) > rx:
            c.line(poly([(X + (rx if ear_x > X else -rx), Y - 8), (ear_x, ear_y - 4)], False), c.lw * 0.6, fr)


def _pearls(c, cx, cy, w, n, det, colr):
    for k in range(n):
        u = k / (n - 1) - 0.5
        x = cx + u * w; y = cy + 30 * (1 - (2 * u) ** 2) - 30
        c.fill(oval(x, y, 7), colr); c.line(oval(x, y, 7), c.lw * 0.35, '#8c8478')
        if det >= 1: c.fill(oval(x - 2, y - 2, 2.2), '#ffffff', 220)


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """Head in head units (crown -120 .. chin +120) on Ctx c (origin at the head centre). yaw/pitch in radians."""
    sp = sp or CAST[who]
    hm = HeadMap(sp, yaw, pitch, jaw=26.0 * clamp(P.m_open) + 5.0 * clamp(P.grin), cheek=clamp(P.grin + 0.4 * max(P.smile, 0.0)))
    skin, sh, dp = _skin_cols(sp, P, light)
    sil = hm.silhouette()
    face_v = hm.map1(0, 0)[2]
    cl = sp['cloth']
    # behind-head things
    if sp['hair'] == 'bun':
        bx, by, bv = hm.map1(0, -40, -150)
        if bv < 0.2 or abs(hm.st) > 0.2:
            bun = oval(bx, by - 18, 34, 30)
            c.shape(bun, sp['hair_c'])
            if det >= 1: c.line(smooth([(bx - 20, by - 26), (bx, by - 36), (bx + 22, by - 22)], False), c.lw * 0.4, mix(sp['hair_c'], '#000000', 0.4))
    for side in (-1, 1):
        if -side * hm.st < 0.25: _ear(c, hm, sp, side, skin, sh, det)
    # skull
    c.fill(sil, skin)
    # skin shading: every layer is drawn on a path inside the silhouette (no clip masks: they are slow at 2560)
    lx = -0.35 * 100 * ((light or {}).get('side', 1))
    c.radial(sil, lx * 0.5 + hm.st * 20, -30, 150, [(0, skin, 0), (0.62, skin, 0), (0.9, sh, 70), (1.0, sh, 135)], sy=1.15)
    ls = (light or {}).get('side', 1)
    c.fill(_crescent(sil, -ls * 30, 6), sh, 42)
    if det >= 2: c.texture(inter(sil, rect(-130, -78 if sp['hat'] else -125, 260, 260)), 'skin', 0.06, 0.32)
    if face_v > -0.3:
        for side in (-1, 1):
            bx_, by_, bv_ = hm.map1(side * 56, sp['eye_y'] + 36, 2)
            if bv_ > 0.1: c.glow(bx_, by_, 24 * hm.sx(side * 56, sp['eye_y'] + 36), 13, sp['blush'], 90 + 80 * P.blush)
    _stubble(c, hm, sp, det, sil)
    c.radial(inter(sil, rect(-150, 70, 300, 120)), hm.st * 30, 128, 90, [(0, dp, 90), (0.5, dp, 45), (1, dp, 0)], sy=22 / 90.0)
    if light and light.get('rim'):
        rs = light.get('side', 1)
        c.fill(_crescent(sil, -rs * 7, 3), light['rim'], light.get('rim_a', 70))
    eyes = {}
    if face_v > -0.35:
        with (c.clip(hm.silhouette(grow=1.5)) if abs(hm.st) > 0.22 or abs(P.h_nod) > 0.3 else _noop()):
            _wrinkles(c, hm, sp, P, det, sh)
            _mouth(c, hm, sp, P, det, t, skin, sh)
            if sp['scar']: _scar(c, hm, sp, sp['scar'], det)
            for side in (-1, 1):
                eyes[side] = _eye(c, hm, sp, P, side, det, t, skin, sh)
            if sp['hair'] != 'messy':
                for side in (-1, 1):
                    _brow(c, hm, sp, P, side, eyes.get(side))
            _tears(c, hm, sp, P, t, det, eyes)
            _sweat(c, hm, sp, P, t, det)
    c.line(sil, c.lw)
    if face_v > -0.35:
        _nose(c, hm, sp, P, det, skin, sh)
    if sp['hair']:
        if sp['hat'] != 'cap' or True:
            _hair_region(c, hm, sp, P, det, sil, t)
        if sp['hair'] == 'messy' and face_v > -0.35:          # v2.1: brows over the fringe so fear/scream angles read
            for side in (-1, 1):
                _brow(c, hm, sp, P, side, eyes.get(side))
    for side in (-1, 1):
        if -side * hm.st >= 0.25: _ear(c, hm, sp, side, skin, sh, det)
    if sp.get('glasses') and face_v > -0.2 and getattr(P, 'specs', 1.0) > 0.5:
        _glasses(c, hm, sp, P, det, eyes, t)
    if sp['hat'] == 'cap':
        _cap(c, hm, sp, P, det, cl, t)
    return hm



# ====================================================================================================== body rig
def _ik(S, H, L1, L2, pole):
    """Two-bone IK in 3D. S shoulder/hip, H target (np arrays). Returns elbow/knee and the reachable end point."""
    d = H - S; dist = float(np.linalg.norm(d)) + 1e-9
    u = d / dist
    reach = L1 + L2 - 0.5
    if dist > reach: dist = reach; H = S + u * dist
    dist = max(dist, abs(L1 - L2) + 1.0)
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pp = pole - u * float(np.dot(pole, u)); n = float(np.linalg.norm(pp))
    pp = pp / n if n > 1e-6 else np.array([1.0, 0.0, 0.0])
    return S + u * a + pp * h, H


def _tube(pts, widths, k=0.9):
    """Tapered limb outline through 2D points with per-point widths (full width)."""
    pts = np.asarray(pts, float); n = len(pts)
    left, right = [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        dx, dy = b - a; L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = widths[i] / 2
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w)); right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    # round caps
    def cap(p, q, w, sgn):
        dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy) or 1.0
        return (p[0] + dx / L * w * 0.42 * sgn, p[1] + dy / L * w * 0.42 * sgn)
    end = cap(pts[-1], pts[-2], widths[-1], 1); start = cap(pts[0], pts[1], widths[0], 1)
    return smooth(left + [end] + right[::-1] + [start], True, k)


class Body:
    """Projects body-frame points (x right, y down, feet y=0, crown y=-1000, z toward the camera) through lean (about the
    hips), yaw, a mild perspective and the 2D tilt/sway/bob of the upper body."""
    D = 1400.0

    def __init__(self, sp, P):
        self.sp, self.P = sp, P
        b = sp['body']; hh = sp['hh']
        self.b = b
        self.yc = -1000.0 + hh                         # chin
        self.y_sh = self.yc + 44 - 3.0 * (P.breath - 0.5) * sp['breath'] - 26 * P.shrug
        self.y_ch = self.y_sh + 78
        self.y_wa = -540.0; self.y_belt = -478.0; self.y_hip = -422.0; self.y_cr = -392.0
        self.th = P.turn * PI / 2; self.ct, self.st = math.cos(self.th), math.sin(self.th)
        self.L = P.lean * 0.62 + P.hunch * 0.22
        self.cL, self.sL = math.cos(self.L), math.sin(self.L)
        self.sit = clamp(P.sit)
        self.hip_drop = 170.0 * self.sit + P.crouch * 120
        self.y0c = -620.0
        self.tilt = math.radians(P.tilt)
        self.ctl, self.stl = math.cos(self.tilt), math.sin(self.tilt)
        bk = 1.0 + 0.014 * (P.breath - 0.5) * sp['breath']
        self.chest_k = bk
        # walk: phases and the hip drop that keeps the stance foot on the ground
        self.walk = clamp(P.walk_amt)
        self.ph = P.walk_ph * 2 * PI
        self.stride = 230.0 * self.walk
        drop = 0.0
        for sd in (-1, 1):
            f = self.foot_fwd(sd)
            if self.foot_lift(sd) < 1: drop = max(drop, math.sqrt(384.0 ** 2 + f * f) - 384.0)
        self.bob = P.bob + drop + 5.0 * self.walk * math.cos(2 * self.ph) + self.hip_drop

    # ---- walk helpers (side: -1 = character's right leg, +1 = left)
    def leg_phase(self, side):
        return self.ph + (0.0 if side > 0 else PI)

    def foot_fwd(self, side):
        return self.stride / 2 * math.cos(self.leg_phase(side))

    def foot_lift(self, side):
        return max(0.0, -math.sin(self.leg_phase(side))) * 62.0 * self.walk

    # ---- projection
    def p3(self, x, y, z=0.0, upper=True):
        y = y + self.bob
        if upper:
            yp = self.y_hip + self.bob
            dy = y - yp
            z1 = z * self.cL - dy * self.sL
            y1 = yp + dy * self.cL + z * self.sL
        else:
            z1, y1 = z, y
        X = x * self.ct + z1 * self.st
        Z = -x * self.st + z1 * self.ct
        s = self.D / (self.D - Z)
        Xs = X * s; Ys = self.y0c + (y1 - self.y0c) * s
        if upper and (self.tilt or self.P.sway):
            hx, hy = 0.0, self.y_hip + self.bob
            dx, dy = Xs - hx, Ys - hy
            Xs = hx + dx * self.ctl - dy * self.stl + self.P.sway
            Ys = hy + dx * self.stl + dy * self.ctl
        return Xs, Ys, s, Z

    def rows(self, ys, ws, ds):
        """Torso rows -> (left pts, right pts) projected."""
        L, R = [], []
        for y, w, d in zip(ys, ws, ds):
            hw = math.sqrt((w * self.ct) ** 2 + (d * self.st) ** 2)
            up = y <= self.y_hip + 1
            X, Y, s, _ = self.p3(0.0, y, 0.0, up)
            # lean pushes rows toward the camera: half width grows with perspective; tilt rotates the row
            dxr, dyr = hw * s * self.ctl, hw * s * self.stl if up else 0.0
            if not up: dxr = hw * s
            L.append((X - dxr, Y - dyr)); R.append((X + dxr, Y + dyr))
        return L, R

    def surf(self, x0, y0, dz=0.0, back=False, rows=None):
        """Point on the torso surface given front-view coords (x0, y0). Returns X, Y, vis, scale."""
        ys, ws, ds = rows
        w = max(float(np.interp(y0, ys, ws)), 1.0); d = float(np.interp(y0, ys, ds))
        s_ = clamp(x0 / w, -1, 1); c_ = math.sqrt(1 - s_ * s_)
        z = (d * c_ + dz) * (-1 if back else 1)
        X, Y, s, _ = self.p3(x0, y0, z, y0 <= self.y_hip + 1)
        nx, nz = s_ * d, c_ * w * (-1 if back else 1)
        nn = math.hypot(nx, nz) + 1e-9
        vis = (-nx * self.st + nz * self.cL * self.ct) / nn
        fs = max(0.06, abs(self.ct * c_ * w * 1.0 - (d * s_) * self.st * (-1 if back else 1)) / (w * c_ + 1e-6) * c_ if c_ > 0.05 else 0.06)
        return X, Y, vis, s * fs


def _hull(pts):
    import cv2
    a = np.asarray(pts, np.float32).reshape(-1, 1, 2)
    h = cv2.convexHull(a).reshape(-1, 2)
    return [(float(x), float(y)) for x, y in h]


# ---------------------------------------------------------------------------------------------- hands & props
# v2.1 hands: real fingers (3 phalanges, knuckle creases, nails, one shade step). Hand coords: wrist at (0, 0), fingers
# toward +y, thumb toward -side * x; about 66 units wrist to fingertip. The finger order runs from the thumb side:
# index, middle, ring, little.
_FING = (  # (base offset along the knuckle line from the thumb side, phalanx lengths, base width, splay rad)
    (1.5, (14.0, 9.5, 8.0), 9.6, 0.20), (0.5, (15.0, 10.5, 8.5), 10.0, 0.06),
    (-0.5, (14.0, 10.0, 8.0), 9.6, -0.08), (-1.5, (11.0, 7.5, 7.0), 8.4, -0.22))


def _finger_pts(bx, by, ang, lens, curl=0.0, side_bend=0.0):
    """Centre line of a finger: base (bx, by), direction ang (rad from +y toward +x), 3 phalanges bending by curl."""
    pts = [(bx, by)]
    a = ang
    x, y = bx, by
    for i, ln in enumerate(lens):
        x += math.sin(a) * ln; y += math.cos(a) * ln
        pts.append((x, y))
        a += side_bend
    if curl:
        # curl foreshortens the outer phalanges toward the palm (seen from the back)
        k = 1.0 - 0.55 * curl
        (x0, y0) = pts[1]
        pts = pts[:2] + [(x0 + (px - x0) * k, y0 + (py - y0) * k) for px, py in pts[2:]]
    return pts


def _fattube(pts, w0, w1):
    n = len(pts)
    ws = [w0 + (w1 - w0) * (i / (n - 1)) for i in range(n)]
    return _tube(pts, ws, 0.9)


def _hand_geom(shape, side, press=0.0):
    """dict(fills=[paths], nails=[paths], creases=[paths], press=[paths], lines=[paths], ring=(x, y, ang_deg, w))."""
    th = -side
    G = dict(fills=[], nails=[], creases=[], press=[], lines=[], ring=None)
    sq = 1.0 + 0.06 * press

    def nail(pts, w, back=True):
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ang = math.degrees(math.atan2(x2 - x1, y2 - y1))
        L_ = math.hypot(x2 - x1, y2 - y1)
        m = skia.Matrix(); m.setRotate(-ang); m.postTranslate(x2, y2)
        p = rrect(-w * 0.32, -L_ * 0.78, w * 0.64, L_ * 0.62, w * 0.3); p.transform(m)
        G['nails'].append(p)

    def crease(pts, i, w):
        (x1, y1) = pts[i]; (x0, y0) = pts[i - 1] if i > 0 else pts[i]; (x2, y2) = pts[i + 1]
        dx, dy = x2 - x0, y2 - y0; L_ = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L_, dx / L_; ux, uy = dx / L_, dy / L_
        h = w * 0.3
        G['creases'].append(smooth([(x1 + nx * h - ux * 1.2, y1 + ny * h - uy * 1.2), (x1 + ux * 1.0, y1 + uy * 1.0),
                                    (x1 - nx * h - ux * 1.2, y1 - ny * h - uy * 1.2)], False))

    if shape in ('open', 'flat', 'wave', 'relaxed', 'palm4'):
        flat = shape == 'flat'
        spread = (1.45 if flat else (0.4 if shape in ('relaxed', 'palm4') else 1.0)) * (1.0 + 0.1 * press)
        palm = smooth([(-15 * sq, 0), (15 * sq, 0), (19 * sq, 18), (19.5 * sq, 33), (12, 38), (-12, 38), (-19.5 * sq, 33), (-19 * sq, 18)], True, 0.75)
        G['fills'].append(palm)
        for k, (off, lens, w, spl) in enumerate(_FING):
            bx = th * off * 9.6 * sq
            pts = _finger_pts(bx, 31.0 - abs(off) * 2.0, th * spl * spread, lens, 0.0, -th * spl * 0.12)
            G['fills'].append(_fattube(pts, w * sq, w * 0.78 * sq))
            if flat:
                (x2, y2) = pts[-1]; (x1, y1) = pts[-2]
                G['press'].append(oval(x1 + (x2 - x1) * 0.55, y1 + (y2 - y1) * 0.55, w * 0.42 * sq, w * 0.62))
                crease(pts, 1, w); crease(pts, 2, w * 0.9)
            else:
                nail(pts, w * 0.8)
                crease(pts, 2, w * 0.85)
                if k < 4: G['creases'].append(smooth([(pts[0][0] - 3, pts[0][1] + 1), (pts[0][0], pts[0][1] - 1.5), (pts[0][0] + 3, pts[0][1] + 1)], False))
            if k == 2:
                (x0, y0), (x1, y1) = pts[0], pts[1]
                G['ring'] = (x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45, math.degrees(math.atan2(x1 - x0, y1 - y0)), w)
        ta = th * (0.78 if flat else 0.55)
        tb = _finger_pts(th * 15.0, 10.0, ta, (15.5, 12.5), 0.0, -th * 0.18)
        if shape == 'palm4': return G
        G['fills'].append(_fattube(tb, 12.0 * sq, 9.0 * sq))
        if flat:
            (x2, y2) = tb[-1]; G['press'].append(oval(x2 - th * 1.5, y2 - 2, 4.8, 5.6))
            G['press'].append(oval(0, 20, 12.5 * sq, 9.5))
            G['lines'].append(smooth([(th * 12, 13), (th * 4, 22), (th * 2, 34)], False))           # life line
            G['lines'].append(smooth([(-th * 17, 25), (-th * 4, 27), (th * 9, 24)], False))         # heart line
        else:
            nail(tb, 9.5)
            G['creases'].append(smooth([(-9, 8), (0, 6), (9, 8)], False))                           # wrist tendon hint
        return G
    if shape in ('fist', 'point'):
        # knuckles toward the viewer: a block with 4 curled finger rolls and the thumb wrapped across
        blk = rrect(-17, -2, 34, 30, 11)
        G['fills'].append(blk)
        for k, (off, lens, w, spl) in enumerate(_FING):
            if shape == 'point' and k == 0: continue
            x = th * off * 8.4
            roll = rrect(x - w * 0.5, 17, w, 18 - abs(off) * 1.6, w * 0.46)
            G['fills'].append(roll)
            G['creases'].append(smooth([(x - w * 0.36, 25), (x, 23.6), (x + w * 0.36, 25)], False))
            if k == 2: G['ring'] = (x, 22.0, 0.0, w)
        if shape == 'point':
            pts = _finger_pts(th * 12.6, 20.0, th * 0.05, (15.0, 11.0, 9.0))
            G['fills'].append(_fattube(pts, 9.8, 8.0)); nail(pts, 7.8); crease(pts, 1, 9.0); crease(pts, 2, 8.4)
        tb = [(th * 18.0, 4.0), (th * 13.0, 15.0), (th * 2.0, 21.0)]
        G['fills'].append(_fattube(tb, 12.0, 9.5))
        nail(tb, 8.5)
        return G
    if shape == 'grip':
        # wrapped round a handle / phone seen from the front: 4 stacked finger rolls across the prop, thumb along the side
        palm = rrect(-17, -2, 34, 16, 9)
        G['fills'].append(palm)
        for k in range(4):
            y = 9.0 + k * 8.6
            ln = (34.0, 35.0, 33.0, 28.0)[k]
            x0 = th * 15.0; x1 = x0 - th * ln
            roll = _fattube([(x0, y), ((x0 + x1) / 2, y + 0.8), (x1, y)], 9.4 - 0.6 * k, 8.4 - 0.5 * k)
            G['fills'].append(roll)
            G['creases'].append(smooth([(x0 - th * ln * 0.55, y - 3.2), (x0 - th * ln * 0.58, y), (x0 - th * ln * 0.55, y + 3.2)], False))
            tip = rrect(min(x1, x1 + th * 7) - 0.5, y - 3.0, 7.0, 6.0, 3.0)
            G['nails'].append(tip)
            if k == 2: G['ring'] = (x0 - th * ln * 0.22, y, 90.0, 9.0)
        tb = [(th * 16.0, 0.0), (th * 17.5 + th * 1.5 * press, 12.0), (th * 15.5 + th * 3.0 * press, 22.0)]
        G['fills'].append(_fattube(tb, 12.0, 10.0))
        nail([tb[1], tb[2]], 9.0)
        return G
    # mitt (reference style, wide shots)
    palm = smooth([(-16, 0), (16, 0), (18, 30), (12, 52), (-10, 54), (-18, 30)], True, 0.8)
    thumb = rrect(-4.5, -2, 9, 26, 4.5)
    m = skia.Matrix(); m.setRotate(-side * 30); m.postTranslate(th * 16, 8); thumb.transform(m)
    G['fills'].append(union(palm, thumb))
    G['creases'] = [poly([(-5 + k * 9, 40), (-5 + k * 9, 52)], False) for k in range(2)]
    G['ring'] = (side * 4.0, 40.0, 0.0, 9.0)
    return G


def _hand_path(shape, L, side, press=0.0, t=0.0):
    """Legacy view of _hand_geom: [(path, kind)] with kind fill / line / detail / press."""
    G = _hand_geom(shape, side, press)
    u = G['fills'][0]
    for p in G['fills'][1:]: u = union(u, p)
    out = [(u, 'fill')]
    out += [(p, 'detail') for p in G['creases']] + [(p, 'press') for p in G['press']] + [(p, 'line') for p in G['lines']]
    return out


_HANDC = {}


def _hand_cached(shape, side, press):
    key = (shape, side, press)
    if key not in _HANDC:
        G = _hand_geom(shape, side, press)
        u = G['fills'][0]
        for p in G['fills'][1:]: u = union(u, p)
        G['union'] = u
        G['shade'] = _crescent(u, -5, -2.5)
        G['creases_p'] = _multi(G['creases']) if G['creases'] else None
        G['lines_p'] = _multi(G['lines']) if G['lines'] else None
        # finger separation lines: outline of each finger inside the union, drawn thin
        G['seps'] = _multi(G['fills'][1:]) if len(G['fills']) > 1 else None
        if len(_HANDC) > 300: _HANDC.clear()
        _HANDC[key] = G
    return _HANDC[key]


def _ring_band(hc, ring, det, t=0.0, lw=None):
    """Gold band across a finger at (x, y, ang, w): the back half darker (occluded), the front half lit, a glint."""
    x, y, ang, w = ring
    rc = hc.sub(x, y, -ang)
    hw = w * 0.53
    band = smooth([(-hw, -1.5), (0, -0.7), (hw, -1.5), (hw, 1.6), (0, 2.4), (-hw, 1.6)], True, 0.5)
    rc.fill(band, '#d8b04c')
    rc.grad(band, -hw, 0, hw, 0, [(0, '#7a5a1c', 255), (0.3, '#f2d77e', 255), (0.62, '#d8b04c', 255), (1, '#6e5018', 255)])
    rc.line(band, hc.lw * 0.3)
    if det >= 1:
        g = 0.5 + 0.5 * math.sin(t * 2.3)
        rc.fill(oval(-hw * 0.38, 0.0, 1.0 + 0.5 * g, 0.55), '#fffbe8', 190 + 60 * g)


def _draw_hand(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring=False, press=0.0, t=0.0):
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
    G = _hand_cached(shape, side, round(press, 1))
    u = G['union']
    hc.fill(u, skin)
    hc.fill(G['shade'], sh, 150)
    if det >= 1 and G['seps'] is not None and shape != 'mitt':
        hc.line(G['seps'], hc.lw * 0.42, LINE, 150)
    hc.line(u, hc.lw * 0.9)
    if det >= 1:
        if G['creases_p'] is not None: hc.line(G['creases_p'], hc.lw * 0.32, sp['skin_dp'], 170)
        if G['lines_p'] is not None: hc.line(G['lines_p'], hc.lw * 0.35, sp['skin_dp'], 150)
        nailc = mix(skin, '#ffffff', 0.38)
        for p in G['nails']:
            hc.fill(p, nailc, 230); hc.line(p, hc.lw * 0.25, sp['skin_dp'], 200)
    if press > 0.05:
        if shape == 'flat':                                     # pressed on glass: paler skin, darker pressed rim
            hc.fill(u, '#f1e6e0', 70 * press)
            hc.line(u, hc.lw * 1.6, mix(skin, '#6b4c46', 0.55), 120 * press)
            hc.line(u, hc.lw * 0.9)
        for p in G['press']: hc.fill(p, '#f3e8e2', 200 * press)
    if ring and G['ring'] is not None:
        _ring_band(hc, G['ring'], det, t)


def moved_path(p, dx, dy):
    q = skia.Path(p); q.offset(dx, dy); return q


def _prop(c, name, det, t=0.0):
    """Props in prop coords (centred, about 60-90 units tall), facing the camera."""
    if name == 'card':
        r = rrect(-46, -30, 92, 60, 6)
        c.shape(r, '#e9e6dc'); c.fill(rrect(-46, -30, 92, 14, 6), '#3f5f9c'); c.fill(rect(-46, -22, 92, 6), '#3f5f9c')
        c.shape(rect(-38, -8, 22, 28), '#b9a99c', c.lw * 0.4)
        c.fill(oval(-27, 0, 6), '#7a6a60'); c.fill(rect(-36, 8, 18, 12), '#7a6a60')
        for k in range(4): c.fill(rect(-8, -6 + k * 7, 44 - k * 6, 3), '#7b7f88', 200)
        if det >= 2: text(c.cv, '', 0, 0)
    elif name == 'notebook':
        r = rrect(-34, -46, 68, 92, 5)
        c.shape(r, '#1a1b1f'); c.fill(rect(18, -46, 6, 92), '#33343a'); c.line(rect(18, -46, 6, 92), c.lw * 0.4)
        c.fill(rect(-34, -40, 4, 80), '#d8d2c2')
    elif name == 'key':
        c.line(oval(0, -18, 15), c.lw * 2.6, '#ff7a12')
        c.line(oval(0, -18, 15), c.lw * 0.5)
        c.line(oval(0, -18, 15 + c.lw * 1.3), c.lw * 0.5)
        c.line(oval(0, -18, 15 - c.lw * 1.3), c.lw * 0.5)
        blade = poly([(-4, -2), (4, -2), (4, 40), (0, 46), (-4, 40)])
        head = oval(0, 0, 10)
        k_ = union(blade, head)
        c.shape(k_, '#b9bec6', c.lw * 0.6)
        for k in range(3): c.fill(rect(4, 18 + k * 7, 5, 4), '#b9bec6'); c.line(rect(4, 18 + k * 7, 5, 4), c.lw * 0.35)
        c.fill(oval(0, 0, 3.5), '#2a2a2e')
        c.shape(rrect(14, -42, 22, 28, 5), '#ff7a12', c.lw * 0.5)
    elif name == 'phone':
        r = rrect(-22, -44, 44, 88, 8)
        c.shape(r, '#121317')
        c.fill(rrect(-18, -38, 36, 74, 4), '#9fc3e8')
        c.radial(rrect(-18, -38, 36, 74, 4), -4, -10, 50, [(0, '#e6eef6', 255), (1, '#6f8fb8', 255)])
    elif name == 'phone_back':
        r = rrect(-21, -46, 42, 92, 9)
        c.shape(r, '#17181d')
        c.grad(r, -21, 0, 21, 0, [(0, '#3a3d47', 255), (0.35, '#1c1d23', 255), (1, '#0b0b0e', 255)])
        c.line(r, c.lw * 0.9)
        cam_ = rrect(-15, -40, 15, 22, 5)
        c.fill(cam_, '#0d0d10'); c.line(cam_, c.lw * 0.4, '#3d404a')
        c.fill(oval(-7.5, -34, 4), '#23252c'); c.fill(oval(-7.5, -24, 4), '#23252c')
        if det >= 1: c.fill(oval(-8.5, -35, 1.4), '#9fb0d0', 200)
    elif name == 'glasses':
        fr = '#3a2f2c'
        for sx_ in (-1, 1):
            l_ = rrect(sx_ * 26 - 22, -16, 44, 32, 12)
            c.fill(l_, '#d9e6f2', 60); c.line(l_, c.lw * 0.75, fr)
            c.fill(poly([(sx_ * 26 - 12, -16), (sx_ * 26 - 4, -16), (sx_ * 26 - 14, 16), (sx_ * 26 - 22, 16)]), '#ffffff', 60)
        c.line(smooth([(-4, -6), (0, -10), (4, -6)], False), c.lw * 0.7, fr)
        c.line(poly([(-48, -8), (-56, 18)], False), c.lw * 0.6, fr); c.line(poly([(48, -8), (56, 18)], False), c.lw * 0.6, fr)
    elif name == 'mic':
        r = rrect(-16, -26, 32, 52, 8)
        c.fill(r, '#15161a')
        c.grad(r, -16, 0, 16, 0, [(0, '#3a3d45', 255), (0.5, '#15161a', 255), (1, '#08080a', 255)])
        c.line(r, c.lw * 0.8)
        for k in range(5): c.line(poly([(-10, -18 + k * 6), (10, -18 + k * 6)], False), c.lw * 0.35, '#050506')
        c.shape(rrect(-21, -4, 7, 18, 2), '#2a2c33', c.lw * 0.4)
        c.fill(oval(9, 17, 2.6), '#3bd157' if (t % 1.0) < 0.6 else '#145a22')
        if det >= 1: c.glow(9, 17, 7, 7, '#3bd157', 90)
    elif name == 'photo':
        r = rect(-40, -32, 80, 64)
        c.shape(r, '#e8e4da', c.lw * 0.6); c.fill(rect(-33, -25, 66, 46), '#4d4a52')
        c.fill(oval(-10, -6, 9), '#b6a092'); c.fill(oval(12, -4, 8), '#b6a092'); c.fill(rect(-22, 4, 46, 17), '#2f3340')
    elif name == 'badge':
        r = rrect(-30, -42, 60, 84, 6)
        c.shape(r, '#2a1d17')
        sh_ = smooth([(0, -26), (17, -18), (20, 2), (10, 20), (0, 27), (-10, 20), (-20, 2), (-17, -18)], True, 0.6)
        c.shape(sh_, '#c9a64a', c.lw * 0.6)
        c.radial(sh_, -5, -8, 26, [(0, '#f2dc94', 255), (1, '#86682a', 255)]); c.line(sh_, c.lw * 0.6)
    elif name == 'radio':
        r = rrect(-17, -40, 34, 80, 8)
        c.shape(r, '#17181c')
        c.fill(rrect(-11, -32, 22, 30, 4), '#2a2c32')
        for k in range(5): c.line(poly([(-8, -28 + k * 6), (8, -28 + k * 6)], False), c.lw * 0.35, '#0b0b0d')
        c.shape(rrect(-6, 6, 12, 10, 3), '#c23b3b', c.lw * 0.4)
        c.shape(rrect(-4, -54, 8, 16, 3), '#17181c', c.lw * 0.6)


def draw_prop(pen, name, x, y, size=80.0, angle=0.0, detail=2, t=0.0):
    """A prop facing the camera, centred at (x, y); size = its height in design px (default props are ~80 units)."""
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 2.2) * 0.8).sub(x, y, angle, size / 80.0)
    _prop(c, name, detail, t)


# ---------------------------------------------------------------------------------------------- outfits
def _torso_rows(sp, B):
    b = sp['body']; o = sp['outfit']; k = B.chest_k
    ys = [B.y_sh - 30, B.y_sh - 10, B.y_sh + 16, B.y_ch, B.y_ch + 80, B.y_wa, B.y_belt, B.y_hip]
    ws = [b['neck'] + 16, b['sh'] * 0.84, b['sh'], b['ch'] * k, b['ch'] * 0.97 * k, b['wa'], b['hip'] * 0.98, b['hip']]
    if o == 'hoodie':
        ws = [b['neck'] + 22, b['sh'] * 0.86, b['sh'], b['ch'] * k, b['ch'] * k, b['wa'] + 6, b['hip'] + 6, b['hip'] + 4]
    ds = [w * f for w, f in zip(ws, [0.55, 0.52, 0.5, 0.56, 0.6, 0.6, 0.62, 0.64])]
    return ys, ws, ds


def _cloth_shade(c, path, sh, a, lside=1.0, dx=30.0, hi=None, hi_a=0):
    c.fill(_crescent(path, -lside * dx, 0), sh, a)
    if hi: c.fill(_crescent(path, lside * dx * 0.5, 0), hi, hi_a)


def _surf_poly(B, rows, pts, back=False, dz=0.0):
    out = []; vis = []
    for x0, y0 in pts:
        X, Y, v, _ = B.surf(x0, y0, dz, back, rows)
        out.append((X, Y)); vis.append(v)
    return out, min(vis)


def _police_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    sh = b['sh']; ch = b['ch']
    ys, ws, ds = rows
    yS, yC, yB = B.y_sh, B.y_ch, B.y_belt
    male = sp['sex'] == 'm'
    # placket + buttons
    pts, v = _surf_poly(B, rows, [(0, yS + 10), (0, yB - 16)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 0.5, '#0c1120', 220)
        c.line(poly([(pts[0][0] + 5, pts[0][1]), (pts[1][0] + 5, pts[1][1])], False), lw * 0.35, cl['shirt_hi'], 120)
        for k in range(4):
            X, Y, vv, s = B.surf(4, yC + 40 + k * 62, 2, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.6 * s, 3.6 * s), '#0b0f1a'); c.fill(oval(X - 1, Y - 1, 1.3 * s), '#4a5677')
    # pockets with flaps (both chests)
    for side in (-1, 1):
        x0, x1 = side * 26, side * (ch * 0.72)
        y0, y1 = yC - 44, yC + 34
        pk, v = _surf_poly(B, rows, [(x0, y0 + 14), (x1, y0 + 14), (x1, y1), ((x0 + x1) / 2, y1 + 6), (x0, y1)])
        if v > 0.05:
            pp = poly(pk)
            c.fill(pp, cl['shirt_sh'], 90); c.line(pp, lw * 0.5, '#0b101d')
            fl, _ = _surf_poly(B, rows, [(x0 - side * 2, y0), (x1 + side * 2, y0), (x1 + side * 2, y0 + 16), ((x0 + x1) / 2, y0 + 26), (x0 - side * 2, y0 + 16)])
            fp = poly(fl)
            c.fill(fp, cl['shirt']); c.line(fp, lw * 0.55, '#0b101d')
            if det >= 1:
                ctr, _ = _surf_poly(B, rows, [((x0 + x1) / 2, y0 + 26), ((x0 + x1) / 2, y1 + 2)])
                c.line(poly(ctr, False), lw * 0.35, '#0b101d', 160)
                X, Y, vv, s = B.surf((x0 + x1) / 2, y0 + 19, 2, False, rows)
                c.fill(oval(X, Y, 3.2 * s), '#0b0f1a')
                if det >= 2:
                    st_, _ = _surf_poly(B, rows, [(x0 + side * 4, y0 + 20), (x1 - side * 4, y0 + 20)])
    # epaulettes
    for side in (-1, 1):
        ep, v = _surf_poly(B, rows, [(side * (b['neck'] + 12), yS - 24), (side * sh * 0.92, yS + 2), (side * sh * 0.9, yS + 18), (side * (b['neck'] + 10), yS - 8)], dz=3)
        if v > -0.1:
            epp = poly(ep); c.fill(epp, cl['shirt_sh']); c.line(epp, lw * 0.5, '#0b101d')
            X, Y, vv, s = B.surf(side * (b['neck'] + 22), yS - 12, 5, False, rows)
            c.fill(oval(X, Y, 4.2 * s), cl['silver']); c.line(oval(X, Y, 4.2 * s), lw * 0.3)
    # tie
    if male:
        tie, v = _surf_poly(B, rows, [(-8, yS - 16), (8, yS - 16), (13, yC + 120), (0, yC + 140), (-13, yC + 120)], dz=4)
        if v > 0.05:
            tp = smooth(tie, True, 0.3); c.fill(tp, cl['tie']); c.line(tp, lw * 0.5)
            knot, _ = _surf_poly(B, rows, [(-10, yS - 30), (10, yS - 30), (7, yS - 12), (-7, yS - 12)], dz=5)
            c.shape(poly(knot), cl['tie'], lw * 0.5)
            X, Y, vv, s = B.surf(0, yC + 30, 6, False, rows)
            c.fill(rrect(X - 16 * s, Y - 2.5 * s, 32 * s, 5 * s, 2 * s), cl['gold']); c.line(rrect(X - 16 * s, Y - 2.5 * s, 32 * s, 5 * s, 2 * s), lw * 0.3)
    # collar
    for side in (-1, 1):
        col_, v = _surf_poly(B, rows, [(side * 4, yS - 22), (side * (b['neck'] + 16), yS - 34), (side * (b['neck'] + 8), yS - 14), (side * 34, yS + 22)], dz=6)
        if v > -0.2:
            cp = poly(col_); c.fill(cp, cl['shirt']); c.line(cp, lw * 0.6)
    # badge (character's left = +x), name plate (right)
    X, Y, v, s = B.surf(ch * 0.47, yC - 64, 8, False, rows)
    if v > 0.1:
        bc = c.sub(X, Y, 0, s * (B.surf(ch * 0.47 + 1, yC - 64, 8, False, rows)[0] - X) / max(s, 1e-3) if False else s, s)
        star = []
        for k in range(16):
            a_ = -PI / 2 + k * PI / 8; rr = 22 if k % 2 == 0 else 15
            star.append((math.cos(a_) * rr, math.sin(a_) * rr * 1.05))
        sp_ = smooth(star, True, 0.25)
        bc.fill(sp_, cl['gold']); bc.radial(sp_, -6, -8, 26, [(0, cl['gold_hi'], 255), (0.55, cl['gold'], 255), (1, cl['gold_sh'], 255)])
        bc.line(sp_, lw * 0.6)
        if det >= 1:
            bc.fill(oval(0, 1, 9), cl['gold_sh']); bc.line(oval(0, 1, 9), lw * 0.3)
            if det >= 2:
                c.cv.save(); m = skia.Matrix(); m.preConcat(bc.M); c.cv.concat(m)
                text(c.cv, '4471', 0, 4, 900, 8, '#2a1f08', 255, 0.5, 'center'); c.cv.restore()
    X, Y, v, s = B.surf(-ch * 0.47, yC - 60, 6, False, rows)
    if v > 0.1:
        npl = rrect(X - 24 * s, Y - 6 * s, 48 * s, 12 * s, 2 * s)
        c.fill(npl, cl['silver']); c.line(npl, lw * 0.4)
        if det >= 2:
            text(c.cv, 'M. DALE' if male else 'K. VOSS', X, Y + 3.5 * s, 800, 8.5 * s, '#1b1e26', 255, 0.5, 'center')
        elif det >= 1:
            c.fill(rect(X - 16 * s, Y - 1.5 * s, 32 * s, 3 * s), '#4b5160')
    # bodycam (centre chest)
    X, Y, v, s = B.surf(0, yC + 8, 10, False, rows)
    if v > 0.1:
        bc = c.sub(X, Y, 0, s)
        bc.fill(rrect(-21, -26, 42, 56, 7), '#000000', 90)
        bx = rrect(-20, -28, 40, 54, 7)
        bc.fill(bx, cl['black']); bc.grad(bx, 0, -28, 0, 26, [(0, cl['black_hi'], 255), (0.4, cl['black'], 255), (1, '#0a0a0c', 255)])
        bc.line(bx, lw * 0.7)
        bc.fill(oval(0, -6, 11), '#0a0b10'); bc.line(oval(0, -6, 11), lw * 0.45)
        bc.radial(oval(0, -6, 9), -3, -9, 12, [(0, '#5a6a8a', 255), (0.5, '#1a2030', 255), (1, '#05060a', 255)])
        bc.fill(oval(-3, -9, 2.5), '#c8d4f0', 220)
        on = clamp(P.cam_on)
        blink = 1.0 if (t * 1.2) % 1.0 < 0.55 else 0.35
        bc.fill(oval(12, 16, 3.6), mix('#3a1010', '#ff2a2a', on * blink)); bc.line(oval(12, 16, 3.6), lw * 0.3)
        if on * blink > 0.5: bc.glow(12, 16, 12, 12, '#ff3030', 120 * on)
        bc.fill(rrect(-12, 13, 14, 7, 2), '#2c2e35')
        if det >= 2:
            for k in range(3): bc.line(poly([(-13 + k * 5, 24), (-11 + k * 5, 24)], False), lw * 0.3, '#5a5e68')
    # shoulder mic (character's left shoulder) + coiled cord to belt radio
    mx, my, mv, ms = B.surf(sh * 0.66, yS + 14, 12, False, rows)
    rx_, ry_, rv_, rs_ = B.surf(b['hip'] * 0.82, yB - 2, 14, False, rows)
    held = (P.hl_prop in ('radio', 'mic'))
    if held:                                          # v2.1: the cord runs from the held mic (the hand) to the belt
        _S, _E, _W = _arm_data(sp, B, P, 1)
        hp_ = B.p3(*_W)
        mx, my, ms = hp_[0], hp_[1] - 22 * hp_[2], hp_[2]
        mv = 1.0
    if mv > -0.3:
        sway = 8 * P.sec_x
        cord = [(mx, my + 22 * ms)]
        for k in range(1, 9):
            u = k / 8
            cx_ = mx + (rx_ - mx) * u + math.sin(u * PI) * (30 + sway) * ms
            cy_ = my + 22 * ms + (ry_ - my - 22 * ms) * u + math.sin(u * PI) * 20 * ms
            cord.append((cx_, cy_))
        cp_ = smooth(cord, False)
        c.line(cp_, lw * 1.5, LINE); c.line(cp_, lw * 0.75, '#2b2d33')
        if det >= 1:
            coils = []
            for k in range(1, 18):
                u = k / 18
                i_f = u * 8; i0 = int(i_f); fr = i_f - i0
                x_ = cord[i0][0] + (cord[min(i0 + 1, 8)][0] - cord[i0][0]) * fr; y_ = cord[i0][1] + (cord[min(i0 + 1, 8)][1] - cord[i0][1]) * fr
                coils.append(oval(x_, y_, 4.2 * ms, 2.2 * ms))
            c.line(_multi(coils), lw * 0.3, '#4a4d55', 200)
        if not held:
            mc = c.sub(mx, my, -8 + 6 * P.sec_x, ms)
            body_ = rrect(-15, -24, 30, 48, 7)
            mc.fill(body_, cl['black']); mc.grad(body_, -15, 0, 15, 0, [(0, cl['black_hi'], 255), (0.5, cl['black'], 255), (1, '#08080a', 255)])
            mc.line(body_, lw * 0.7)
            for k in range(5): mc.line(poly([(-9, -16 + k * 6), (9, -16 + k * 6)], False), lw * 0.35, '#050506')
            mc.shape(rrect(-17, 6, 6, 14, 2), '#2a2c33', lw * 0.35)
            mc.fill(oval(9, 15, 2.5), '#2f8a3a' if (t % 2.0) < 1.6 else '#123516')


def _police_belt(c, sp, B, rows, P, det, back=False):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yB = B.y_belt
    w = b['hip'] * 0.98
    top, bot = [], []
    for k in range(13):
        x0 = -w + 2 * w * k / 12
        X, Y, v, s = B.surf(x0, yB - 17, 3, back, rows); top.append((X, Y))
        X, Y, v, s = B.surf(x0, yB + 17, 3, back, rows); bot.append((X, Y))
    band = smooth(top + bot[::-1], True, 0.4)
    c.fill(band, cl['belt'])
    if det >= 1:
        c.line(smooth(top, False, 0.4), lw * 0.3, '#3a3d45', 200)
        for k in range(-3, 4):
            X, Y, v, s = B.surf(k * w * 0.27, yB, 4, back, rows)
            if v > 0.1: c.fill(rrect(X - 4 * s, Y - 18 * s, 8 * s, 36 * s, 2 * s), '#1c1d22'); c.line(rrect(X - 4 * s, Y - 18 * s, 8 * s, 36 * s, 2 * s), lw * 0.3)
    c.line(band, lw * 0.7)
    if not back:
        X, Y, v, s = B.surf(0, yB, 5, False, rows)
        if v > 0.1:
            bk = rrect(X - 15 * s, Y - 13 * s, 30 * s, 26 * s, 3 * s)
            c.fill(bk, cl['silver']); c.radial(bk, X - 5 * s, Y - 5 * s, 22 * s, [(0, '#e6eaef', 255), (1, cl['silver_sh'], 255)]); c.line(bk, lw * 0.5)
            c.fill(rrect(X - 8 * s, Y - 6 * s, 16 * s, 12 * s, 2 * s), cl['belt'])
    # gear: holster (char right = -x), mag pouch, cuffs, radio (char left = +x), flashlight
    gear = [(-w * 0.86, 'holster'), (-w * 0.42, 'cuffs'), (w * 0.4, 'mags'), (w * 0.84, 'radio'), (-w * 0.98, 'light')]
    for x0, kind in gear:
        X, Y, v, s = B.surf(x0, yB, 12 if kind != 'holster' else 16, back, rows)
        if v < -0.15: continue
        gc = c.sub(X, Y, 0, s)
        if kind == 'holster':
            g = smooth([(-14, -14), (14, -14), (16, 70), (6, 112), (-12, 112), (-16, 70)], True, 0.5)
            gc.fill(g, '#121317'); gc.grad(g, -16, 0, 16, 0, [(0, '#2b2d34', 255), (0.6, '#121317', 255), (1, '#060607', 255)]); gc.line(g, lw * 0.7)
            grip = smooth([(-8, -14), (8, -14), (18, -44), (6, -50), (-6, -26)], True, 0.5)
            gc.shape(grip, '#1e1f24', lw * 0.6)
            if det >= 1:
                for k in range(3): gc.line(poly([(-2 + k * 4, -24 - k * 6), (8 + k * 3, -30 - k * 6)], False), lw * 0.25, '#3a3c44')
                gc.fill(rrect(-10, 10, 20, 26, 4), '#1b1c21'); gc.line(rrect(-10, 10, 20, 26, 4), lw * 0.35)
                gc.fill(oval(0, 23, 2.5), cl['silver'])
        elif kind == 'radio':
            g = rrect(-15, -6, 30, 58, 5)
            gc.fill(g, '#16171b'); gc.grad(g, -15, 0, 15, 0, [(0, '#33363e', 255), (1, '#0a0a0c', 255)]); gc.line(g, lw * 0.6)
            gc.shape(rrect(-10, -38, 7, 34, 3), '#111114', lw * 0.5)
            gc.shape(oval(6, -12, 5), '#24262c', lw * 0.4)
            if det >= 1:
                gc.fill(rect(-9, 8, 18, 10), '#4f7a5a'); gc.line(rect(-9, 8, 18, 10), lw * 0.3)
        elif kind == 'mags':
            for k in (-1, 1):
                gc.shape(rrect(k * 9 - 8, -10, 16, 40, 4), '#141519', lw * 0.5)
                gc.fill(oval(k * 9, -2, 2.4), cl['silver'])
        elif kind == 'cuffs':
            gc.shape(rrect(-14, -10, 28, 30, 5), '#141519', lw * 0.5)
            gc.fill(oval(0, -2, 2.4), cl['silver'])
        elif kind == 'light':
            gc.shape(rrect(-6, -16, 12, 70, 4), '#1a1b20', lw * 0.5)


def _hoodie_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    # kangaroo pocket
    pk, v = _surf_poly(B, rows, [(-62, B.y_wa - 10), (62, B.y_wa - 10), (80, B.y_hip - 18), (-80, B.y_hip - 18)], dz=3)
    if v > 0.05:
        pp = smooth(pk, True, 0.25); c.fill(pp, cl['top_sh'], 120); c.line(pp, lw * 0.6)
        for side in (-1, 1):
            sl, _ = _surf_poly(B, rows, [(side * 62, B.y_wa - 10), (side * 76, B.y_wa + 60)], dz=4)
            c.line(poly(sl, False), lw * 0.5)
    # hem rib
    hem, v = _surf_poly(B, rows, [(-b['hip'] - 4, B.y_hip - 26), (b['hip'] + 4, B.y_hip - 26)], dz=2)
    if v > -0.2: c.line(poly(hem, False), lw * 0.45, LINE, 200)
    # neckline + drawstrings
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 14, yS - 28), (0, yS - 2), (b['neck'] + 14, yS - 28)], dz=4)
    if v > -0.2: c.line(smooth(nk, False), lw * 0.7)
    for side in (-1, 1):
        sw = 4 * P.sec_x
        st, v = _surf_poly(B, rows, [(side * 16, yS - 6), (side * 18 + sw, yC + 10), (side * 15 + sw * 1.5, yC + 60)], dz=7)
        if v > 0.0:
            sp_ = smooth(st, False); c.line(sp_, lw * 2.2, LINE); c.line(sp_, lw * 1.0, cl['string'])
            x_, y_ = st[-1]
            c.fill(rrect(x_ - 3.5, y_, 7, 14, 2), '#8c8a84'); c.line(rrect(x_ - 3.5, y_, 7, 14, 2), lw * 0.35)
    # raglan seams
    if det >= 1:
        for side in (-1, 1):
            sm, v = _surf_poly(B, rows, [(side * (b['neck'] + 10), yS - 24), (side * b['ch'] * 0.86, yC + 10)], dz=1)
            if v > 0.0: c.line(smooth(sm, False), lw * 0.4, cl['top_sh'], 220)


def _coat_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    # shirt opening and lapels
    op, v = _surf_poly(B, rows, [(-14, yS - 24), (14, yS - 24), (10, yC + 70), (0, yC + 92), (-10, yC + 70)], dz=3)
    if v > 0.05:
        c.fill(smooth(op, True, 0.2), cl['shirt']); c.line(smooth(op, True, 0.2), lw * 0.5)
        for side in (-1, 1):
            lp, _ = _surf_poly(B, rows, [(side * 12, yS - 30), (side * (b['neck'] + 26), yS - 36), (side * (b['neck'] + 30), yS - 4),
                                         (side * 56, yC - 10), (side * 40, yC + 6), (side * 10, yC + 86)], dz=6)
            lpp = poly(lp)
            c.fill(lpp, cl['coat_hi'] if side < 0 else cl['coat']); c.line(lpp, lw * 0.7)
        for k in range(3):
            X, Y, vv, s = B.surf(8, yC + 110 + k * 80, 4, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 6.5 * s), cl['button'], lw * 0.4)
        cl_, _ = _surf_poly(B, rows, [(2, yC + 92), (2, -232)], dz=2)
        c.line(poly(cl_, False), lw * 0.55)
        for side in (-1, 1):
            fl, _ = _surf_poly(B, rows, [(side * 30, B.y_wa + 70), (side * 92, B.y_wa + 66), (side * 94, B.y_wa + 88), (side * 30, B.y_wa + 92)], dz=4)
            c.shape(poly(fl), cl['coat'], lw * 0.5)


def _cardigan_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-30, yS - 26), (30, yS - 26), (24, B.y_hip - 20), (-18, B.y_hip - 20)], dz=2)
    if v > 0.05:
        bl = smooth(op, True, 0.2); c.fill(bl, cl['blouse']); c.line(bl, lw * 0.5)
        with c.clip(bl):
            c.grad(bl, 0, yS, 0, B.y_hip, [(0, cl['blouse'], 0), (1, cl['blouse_sh'], 200)])
        for side in (-1, 1):
            cc, _ = _surf_poly(B, rows, [(0, yS - 20), (side * 30, yS - 26), (side * 36, yS + 4), (side * 6, yS + 6)], dz=5)
            c.shape(smooth(cc, True, 0.6), cl['blouse'], lw * 0.55)
        X, Y, vv, s = B.surf(0, yS + 34, 6, False, rows)
        _pearls(c.sub(X, Y - 14 * s, 0, s), 0, 0, 64, 9, det, cl['pearl'])
        for side in (-1, 1):
            ed, _ = _surf_poly(B, rows, [(side * 30, yS - 26), (side * 26, B.y_hip - 20)], dz=3)
            c.line(poly(ed, False), lw * 2.4, LINE); c.line(poly(ed, False), lw * 1.3, cl['top_hi'])
        for k in range(4):
            X, Y, vv, s = B.surf(-33, yC + k * 60, 5, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 5 * s), '#d8cfc0', lw * 0.35)
    if det >= 1:
        for k in range(-5, 6):
            if abs(k) < 2: continue
            rb, v = _surf_poly(B, rows, [(k * 18, yS + 8), (k * 19, B.y_hip - 26)], dz=1)
            if v > 0.1: c.line(poly(rb, False), lw * 0.25, cl['top_sh'], 150)
        hem, v = _surf_poly(B, rows, [(-b['hip'], B.y_hip - 24), (b['hip'], B.y_hip - 24)], dz=1)
        if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 200)


# ---------------------------------------------------------------------------------------------- figure
def _limb_cols(sp):
    cl = sp['cloth']; o = sp['outfit']
    if o == 'police': return cl['shirt'], cl['shirt_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'hoodie': return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'coat': return cl['coat'], cl['coat_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    return cl['top'], cl['top_sh'], cl['legs'], mix(cl['legs'], '#000000', 0.25), cl['shoes']


def _arm_data(sp, B, P, side):
    """side +1 = character's left (screen right in front view). Returns 3D points S, E, W and hand info."""
    b = sp['body']
    pre = 'hl_' if side > 0 else 'hr_'
    g = lambda k: getattr(P, pre + k)   # noqa: E731
    sx = side * (b['sh'] - 17)
    S = np.array([sx, B.y_sh + 20, 0.0])
    swing = 0.0
    if B.walk > 0:
        swing = -60.0 * B.walk * math.cos(B.leg_phase(-side))
    H = S + np.array([side * g('out'), g('down'), g('fwd') + swing])
    pole = np.array([side * 0.75, 0.25, -0.65])
    kup = clamp((S[1] - H[1] - 10.0) / 60.0)            # v2.1: hand raised above the shoulder -> elbow down and out
    if kup > 0: pole = pole + (np.array([side * 0.7, 1.0, 0.25]) - pole) * kup
    ear = _ear_weight(P, side)
    if ear > 0:
        # v2.1 phone at the ear: wrist just below the ear so the phone covers ear and cheek; elbow forward and down
        hh = sp['hh']
        hw = float(np.interp(4.0, sp['head_ys'], sp['head_ws'])) * hh / 240.0
        hy = P.h_turn * PI / 2
        ex = side * (hw * 1.0 + 9.0) * math.cos(hy) + P.h_dx
        ey = B.yc - hh / 2 + 3.0 * hh / 240.0 + P.h_dy
        He = np.array([ex + side * 4.0, ey + 0.31 * hh, 26.0 - side * hw * 0.9 * math.sin(hy)])
        H = H + (He - H) * ear
        pole = pole + (np.array([side * 0.2, 1.0, 0.75]) - pole) * ear
    E, Wp = _ik(S, H, 182.0, 166.0, pole)
    return S, E, Wp


def _ear_weight(P, side):
    """Phone-to-ear weight of one arm: pose.hl_ear/hr_ear, or 1 for the legacy film.phone_ear() pose (prop 'phone',
    hand raised close to the shoulder: up > 0.5, fwd < 120, down < 60)."""
    pre = 'hl_' if side > 0 else 'hr_'
    ear = getattr(P, pre + 'ear', 0.0)
    if getattr(P, pre + 'prop') == 'phone' and getattr(P, pre + 'up') > 0.5 and getattr(P, pre + 'fwd') < 120 \
            and getattr(P, pre + 'down') < 60:
        ear = max(ear, 1.0)
    return clamp(ear)


def _draw_arm(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    S, E, Wr = _arm_data(sp, B, P, side)
    b = sp['body']
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    aw0, aw1 = b['arm']
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    widths = [aw0 * pts[0][2], (aw0 + aw1) / 2 * max(pts[1][2], hz ** 0.5), aw1 * hz]
    # extend the sleeve top into the shoulder
    tp = _tube([(P2[0][0] - side * 4, P2[0][1] - 14)] + P2, [widths[0] * 1.05] + widths)
    o = sp['outfit']
    c.fill(tp, sleeve)
    _cloth_shade(c, tp, sleeve_sh, 170, 1.0, 12 * pts[0][2])
    c.line(tp, c.lw)
    # elbow crease + cuff + patch
    if det >= 1:
        ex, ey = P2[1]
        dx, dy = P2[2][0] - P2[0][0], P2[2][1] - P2[0][1]
        c.line(smooth([(ex - 10, ey - 6), (ex, ey + 2), (ex + 9, ey - 4)], False), c.lw * 0.4, LINE, 150)
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    cuffc = sleeve_sh if o != 'hoodie' else mix(sleeve, '#000000', 0.15)
    cuff = c.sub(wx, wy, ang, hz)
    cw = aw1 * 0.55
    cpath = rrect(-cw, -22, cw * 2, 22, 5)
    cuff.fill(cpath, cuffc); cuff.line(cpath, c.lw * 0.7 / hz)
    if o == 'hoodie' and det >= 1:
        cuff.line(_multi([poly([(k * cw / 4, -20), (k * cw / 4, -3)], False) for k in range(-3, 4)]), c.lw * 0.3 / hz, LINE, 140)
    if o == 'police':
        # shoulder patch on the upper arm, outer side
        ux, uy = P2[0][0] + (P2[1][0] - P2[0][0]) * 0.28, P2[0][1] + (P2[1][1] - P2[0][1]) * 0.28
        vis = side * B.ct + 0.2 > 0 or abs(B.st) < 0.5
        if vis:
            pc = c.sub(ux + side * 6 * pts[0][2] * abs(B.ct), uy, 0, pts[0][2] * (0.45 + 0.55 * abs(B.ct)), pts[0][2])
            pat = smooth([(-15, -16), (15, -16), (17, 6), (0, 22), (-17, 6)], True, 0.5)
            cl = sp['cloth']
            pc.fill(pat, cl['patch']); pc.line(pat, c.lw * 0.9 / pts[0][2], cl['patch_rim'])
            pc.line(pat, c.lw * 0.35 / pts[0][2])
            if det >= 1:
                pc.fill(oval(0, -1, 6), cl['gold']); pc.fill(rect(-11, -13, 22, 4), '#e8e2d0', 220)
    # hand
    hand_shape = getattr(P, 'hl_shape' if side > 0 else 'hr_shape')
    prop = getattr(P, 'hl_prop' if side > 0 else 'hr_prop')
    up = getattr(P, 'hl_up' if side > 0 else 'hr_up')
    rot = getattr(P, 'hl_rot' if side > 0 else 'hr_rot')
    press = getattr(P, 'hl_press' if side > 0 else 'hr_press')
    ear = _ear_weight(P, side)
    if ear > 0.5:
        up, rot = 1.0, -side * 14.0 * B.ct
    hang = ang * (1 - up) + (180.0) * up + rot
    hs = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0) * getattr(P, 'hl_scale' if side > 0 else 'hr_scale', 1.0)
    ring = (sp['ring'] == side)
    if prop:
        if ear > 0.5 and prop == 'phone':
            # phone pressed to the ear: dark back of the phone along the cheek, the hand wrapped round it
            pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs,
                       side * 17.0 * B.ct, hs * 1.0)
            _prop(pc, 'phone_back', det, t)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
        else:
            pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs, 0, hs * 1.15)
            _prop(pc, prop, det, t)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
    else:
        _draw_hand(c, sp, hand_shape, wx, wy, hs, hang, side, det, skin, sh, ring, press, t)


def _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec):
    b = sp['body']
    order = []
    for side in (-1, 1):
        hip = np.array([side * b['hip'] * 0.46, B.y_hip + 8, 0.0])
        fwd = B.foot_fwd(side) + B.sit * 210.0
        lift = B.foot_lift(side)
        ank = np.array([side * (b['hip'] * 0.46 + 6 + 30 * P.stance), -38.0 - lift, fwd])
        hipw = hip.copy(); hipw[1] -= 0  # legs do not lean
        K, A = _ik(hipw + np.array([0, B.bob, 0]), ank, 206.0, 180.0, np.array([0.08 * side, -0.15, 1.0]))
        order.append((B.p3(*(hipw + np.array([0, 0, 0])), upper=False), B.p3(K[0], K[1] - B.bob, K[2], upper=False),
                      B.p3(A[0], A[1] - B.bob, A[2], upper=False), side, A))
    order.sort(key=lambda o: (o[0][3] + o[2][3]))
    lw0, lw1 = b['leg']
    for hp, kp, ap, side, A in order:
        P2 = [(hp[0], hp[1]), (kp[0], kp[1]), (ap[0], ap[1])]
        widths = [lw0 * hp[2], (lw0 + lw1) / 2 * kp[2], lw1 * ap[2]]
        tp = _tube(P2, widths)
        # shoe (convex hull of a box)
        ax, ay, az = A
        pts = []
        for (hx, hz) in ((-22, -24), (22, -24), (-24, 58), (24, 58), (-18, 72), (18, 72)):
            for hy in (0.0, -30.0 if hz < 40 else -22.0):
                X, Y, s, Z = B.p3(ax + hx * B.ct + 0, -B.bob + ay + 38 + hy + (0 if True else 0), az + hz, upper=False) if False else \
                    B.p3(ax + hx, ay + 38 + hy - B.bob, az + hz, upper=False)
                pts.append((X, Y))
        shoe = smooth(_hull(pts), True, 0.6)
        c.fill(tp, legc)
        _cloth_shade(c, tp, legsh, 160, 1.0, 10)
        c.line(tp, c.lw)
        if det >= 1 and sp['outfit'] in ('police', 'coat', 'hoodie'):
            c.line(smooth([((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2), P2[1], ((P2[1][0] + P2[2][0]) / 2, (P2[1][1] + P2[2][1]) / 2 + 10)], False),
                   c.lw * 0.35, LINE, 120)
        c.fill(shoe, shoec)
        bb = shoe.getBounds()
        c.glow(bb.centerX() - bb.width() * 0.18, bb.top() + bb.height() * 0.32, bb.width() * 0.3, bb.height() * 0.13, '#ffffff',
               70 if shoec in ('#0c0c0f', '#111113') else 40)
        c.line(shoe, c.lw)
        if sp['outfit'] == 'hoodie' and det >= 1:
            c.line(poly([(bb.left() + 4, bb.bottom() - 7), (bb.right() - 4, bb.bottom() - 7)], False), c.lw * 0.5, '#8a8478')


def _pelvis(c, sp, B, rows, legc, legsh, det):
    b = sp['body']
    ys, ws, ds = rows
    yh = B.y_hip
    Lp = []
    for x0, y0 in ((-b['hip'], yh - 30), (b['hip'], yh - 30)):
        X, Y, v, s = B.surf(x0 * 0.999, y0, 0, False, rows); Lp.append((X, Y))
    X0, Y0, _, s0 = B.p3(0, B.y_cr + 12, 0, upper=False)
    hw = math.sqrt((b['hip'] * B.ct) ** 2 + (b['hip'] * 0.62 * B.st) ** 2)
    pel = smooth([(X0 - hw * s0, yh - 30 + B.bob), (X0 + hw * s0, yh - 30 + B.bob), (X0 + hw * 0.98 * s0, yh + 14 + B.bob),
                  (X0 + 10, B.y_cr + 26 + B.bob), (X0 - 10, B.y_cr + 26 + B.bob), (X0 - hw * 0.98 * s0, yh + 14 + B.bob)], True, 0.4)
    c.fill(pel, legc)
    _cloth_shade(c, pel, legsh, 140, 1.0, 18)
    if det >= 1 and abs(B.st) < 0.7:
        c.line(smooth([(X0 + 4, yh - 20 + B.bob), (X0 + 6, B.y_cr + 6 + B.bob), (X0 - 2, B.y_cr + 20 + B.bob)], False), c.lw * 0.4, LINE, 170)


def _skirt(c, sp, B, det, y_top, y_hem, w_top, w_hem, colr, colsh, slit=False, t=0.0, P=None):
    X0, Y0, s0, _ = B.p3(0, y_top, 0, upper=True)
    X1, Y1, s1, _ = B.p3(0, y_hem, 0, upper=False)
    ht = math.sqrt((w_top * B.ct) ** 2 + (w_top * 0.62 * B.st) ** 2) * s0
    hh_ = math.sqrt((w_hem * B.ct) ** 2 + (w_hem * 0.66 * B.st) ** 2) * s1
    sw = (P.sec_x * 10 if P else 0) - B.st * 8 * B.walk
    pts = [(X0 - ht, Y0), (X0 + ht, Y0), (X1 + hh_ + sw, Y1), (X1 + hh_ * 0.5 + sw, Y1 + 6), (X1 - hh_ * 0.5 + sw, Y1 + 6), (X1 - hh_ + sw, Y1)]
    p = smooth(pts, True, 0.35)
    c.fill(p, colr)
    _cloth_shade(c, p, colsh, 150, 1.0, 24)
    if det >= 1:
        c.texture(p, 'fabric', 0.12, 0.6)
        for k in (-0.5, 0.0, 0.5):
            c.line(poly([(X0 + k * ht * 0.6, Y0 + 40), (X1 + k * hh_ * 0.8 + sw, Y1 + 2)], False), c.lw * 0.35, LINE, 110)
    c.line(p, c.lw)
    return p


def _torso_path(B, rows):
    ys, ws, ds = rows
    L, R = B.rows(ys, ws, ds)
    neck_l, neck_r = L[0], R[0]
    pts = R + L[::-1]
    return smooth(pts, True, 0.85), L, R


def _figure(c, who, P, det, t, light=None, upper_only=False):
    """Whole character in body units on Ctx c (feet at y=0, crown at y=-1000)."""
    sp = CAST[who]
    B = Body(sp, P)
    skin, skin_sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh, legc, legsh, shoec = _limb_cols(sp)
    rows = _torso_rows(sp, B)
    cl = sp['cloth']; o = sp['outfit']
    # arms: which are behind the torso
    arm_z = {}
    for side in (-1, 1):
        S, E, Wr = _arm_data(sp, B, P, side)
        zs = B.p3(*S)[3]; zh = B.p3(*Wr)[3]
        arm_z[side] = (zs, zh)
    behind = [s for s in (-1, 1) if arm_z[s][0] < -20 and arm_z[s][1] < 40]
    front = [s for s in (-1, 1) if s not in behind]
    front.sort(key=lambda s: arm_z[s][1])
    back_view = B.ct < -0.15
    # hood behind the neck
    for side in behind: _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    if not upper_only:
        if o not in ('cardigan',):
            _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
            _pelvis(c, sp, B, rows, legc, legsh, det)
        else:
            _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
    elif o not in ('coat',):
        _pelvis(c, sp, B, rows, legc, legsh, det)
    torso, L, R = _torso_path(B, rows)
    top = {'police': cl.get('shirt'), 'hoodie': cl.get('top'), 'coat': cl.get('coat'), 'cardigan': cl.get('top')}[o]
    topsh = {'police': cl.get('shirt_sh'), 'hoodie': cl.get('top_sh'), 'coat': cl.get('coat_sh'), 'cardigan': cl.get('top_sh')}[o]
    tophi = {'police': cl.get('shirt_hi'), 'hoodie': cl.get('top_hi'), 'coat': cl.get('coat_hi'), 'cardigan': cl.get('top_hi')}[o]
    if o == 'cardigan' and not upper_only:
        _skirt(c, sp, B, det, B.y_wa + 10, -175, sp['body']['hip'] * 0.98, sp['body']['hip'] * 1.12, cl['skirt'], cl['skirt_sh'], t=t, P=P)
    # neck (behind collar)
    nb = B.p3(0, B.y_sh - 34, 0); nt = B.p3(0, B.yc - 30, 0)
    nw = sp['body']['neck']
    neck = _tube([(nb[0], nb[1]), (nt[0], nt[1])], [nw * 2 * nb[2], nw * 1.9 * nt[2]])
    if o == 'hoodie':
        hood = smooth([(nb[0] - (nw + 46) * nb[2], nb[1] + 8), (nb[0] - (nw + 30) * nb[2], nb[1] - 42), (nb[0], nb[1] - 56 - 10 * (B.ct < 0)),
                       (nb[0] + (nw + 30) * nb[2], nb[1] - 42), (nb[0] + (nw + 46) * nb[2], nb[1] + 8)], True, 0.8)
        c.shape(hood, cl['top_sh'])
    c.fill(neck, skin)
    with c.clip(neck):
        c.fill(moved_path(neck, 0, -30), skin_sh, 0)
        c.grad(neck, 0, nt[1] - 10, 0, nb[1], [(0, mix(skin_sh, '#000000', 0.2), 255), (0.6, skin_sh, 160), (1, skin, 0)])
    c.line(neck, c.lw)
    # torso
    if o == 'coat':
        if not upper_only:
            _skirt(c, sp, B, det, B.y_wa, -236, sp['body']['wa'] + 8, sp['body']['hip'] * 1.22, cl['coat'], cl['coat_sh'], t=t, P=P)
    c.fill(torso, top)
    c.grad(torso, L[3][0] - 10, 0, R[3][0] + 10, 0, [(0, tophi, 90), (0.35, top, 0), (0.7, topsh, 60), (1, topsh, 200)])
    with c.clip(torso):
        c.grad(rect(-400, B.y_wa - 10, 800, 300), 0, B.y_wa - 60, 0, B.y_hip, [(0, topsh, 0), (1, topsh, 140)])
        if det >= 1: c.texture(torso, 'grunge', 0.07, 0.7)
        # armpit creases + blousing
        if det >= 1:
            for side in (-1, 1):
                for k in range(2):
                    p0 = B.surf(side * (sp['body']['ch'] * (0.78 - k * 0.1)), B.y_ch - 10 + k * 24, 1, back_view, rows)
                    p1 = B.surf(side * (sp['body']['ch'] * (0.5 - k * 0.08)), B.y_ch + 34 + k * 30, 1, back_view, rows)
                    c.line(smooth([(p0[0], p0[1]), ((p0[0] + p1[0]) / 2 + side * 4, (p0[1] + p1[1]) / 2), (p1[0], p1[1])], False), c.lw * 0.42, LINE, 130)
            if o == 'police':
                for k in range(-4, 5):
                    p0 = B.surf(k * 22, B.y_belt - 50, 1, back_view, rows); p1 = B.surf(k * 23 + 3, B.y_belt - 18, 1, back_view, rows)
                    if p0[2] > 0.1: c.line(smooth([(p0[0], p0[1]), (p1[0] + 2, (p0[1] + p1[1]) / 2), (p1[0], p1[1])], False), c.lw * 0.35, LINE, 110)
        if light and light.get('rim'):
            rs = light.get('side', 1)
            c.fill(_crescent(torso, -rs * 9, 0), light['rim'], light.get('rim_a', 70) * 0.8)
    c.line(torso, c.lw)
    if not back_view:
        if o == 'police': _police_front(c, sp, B, rows, P, det, t)
        elif o == 'hoodie': _hoodie_front(c, sp, B, rows, P, det, t)
        elif o == 'coat': _coat_front(c, sp, B, rows, P, det, t)
        elif o == 'cardigan': _cardigan_front(c, sp, B, rows, P, det, t)
    else:
        yy = B.y_sh + 30
        sm, v = _surf_poly(B, rows, [(-sp['body']['sh'] * 0.8, yy), (0, yy + 12), (sp['body']['sh'] * 0.8, yy)], back=True, dz=1)
        c.line(smooth(sm, False), c.lw * 0.4, LINE, 140)
    if o == 'police': _police_belt(c, sp, B, rows, P, det, back_view)
    # head
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2] * P.h_scale
    head_rot = P.tilt + P.h_tilt
    arm_ = (sp['hh'] / 2 - 22) * pv[2] * P.h_scale
    ra = math.radians(head_rot)
    hx = pv[0] + P.h_dx + math.sin(ra) * arm_
    hy = pv[1] - math.cos(ra) * arm_
    hc = c.sub(hx, hy, head_rot, hs)
    yaw = (P.turn + P.h_turn) * PI / 2
    draw_head_local(hc, who, P, yaw, P.h_nod * 0.6 + 0.0, det, t, light, sp)
    for side in front: _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    return B


# ====================================================================================================== public drawing
def _as_pose(pose):
    if pose is None: return Pose()
    if isinstance(pose, str): return Pose(pose)
    if isinstance(pose, dict): return Pose(**pose)
    return pose


def draw(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, aim=None):
    """Full body. height = feet-to-crown in design px. pose.dx (design px) shifts the figure (walks).
    aim=(x, y): as pose.approach goes 0 -> 1 the figure slides so its head reaches that point (put the lens axis
    here for lean_in toward a doorbell / peephole; pair it with Layer depth=acting.depth(base))."""
    P = _as_pose(pose); t = P.t if t is None else t
    s = height / 1000.0
    sp = CAST[who]
    head_px = sp['hh'] * s
    det = _auto_detail(pen, head_px) if detail is None else detail
    ox = oy = 0.0
    if aim is not None and P.approach > 0:
        k = ease_in_out(clamp(P.approach))
        ox = (aim[0] - (x + P.dx)) * k
        oy = (aim[1] - (y_feet + P.dy - (1000.0 - sp['hh'] / 2) * s)) * k
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(x + P.dx + ox, y_feet + P.dy + oy, 0.0, s)
    return _figure(c, who, P, det, t, light)


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    """Head-and-shoulders close-up. scale 1 = head 600 design px tall; (cx, cy) = rest head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    sp = CAST[who]
    k = 1.0 + 1.1 * clamp(P.approach)
    head_px = 600.0 * scale * k
    s = head_px / sp['hh']
    c0 = Ctx(pen, skia.Matrix(), _lw_for(head_px))
    yh = -1000 + sp['hh'] / 2
    ty = cy + 60.0 * scale * clamp(P.approach)
    c = c0.sub(cx - 0 * s, ty - yh * s, 0.0, s)
    det = _auto_detail(pen, head_px) if detail is None else detail
    return _figure(c, who, P, det, t, light, upper_only=True)


def draw_head(pen, who, cx, cy, size, pose=None, detail=2, light=None, t=None):
    """Head only. size = crown-to-chin height in design px, (cx, cy) = head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    s = size / 240.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size)).sub(cx, cy, P.h_tilt, s)
    yaw = (P.turn + P.h_turn) * PI / 2; pitch = P.h_nod * 0.6
    return draw_head_local(c, who, P, yaw, pitch, detail, t, light)


def draw_hand(pen, who, x, y, size, shape='open', angle=0.0, side=1, pose=None, detail=2):
    """One hand. size = wrist-to-fingertip length in design px; angle 0 = fingers down, 180 = fingers up."""
    sp = CAST[who]; P = _as_pose(pose)
    skin, sh, _ = _skin_cols(sp, P, None)
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5))
    _draw_hand(c, sp, shape, x, y, size / 66.0, angle, side, detail, skin, sh, sp['ring'] == side, 0.0, P.t)


def _hpt(x, y, ang, k, hx, hy):
    """Hand-coords point (hx, hy) of a hand drawn at (x, y), rotated ang deg, scaled k -> parent coords."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    return x + (hx * ca - hy * sa) * k, y + (hx * sa + hy * ca) * k


def draw_hands_lap(pen, who, cx, cy, size, rub_phase=0.0, ring_side=None, t=0.0, detail=2, light=None, cuffs=True,
                   thread=False, rub_amp=12.0, rub=True, _lay=None):
    """v2.1 insert: two hands folded in the lap, seen from the front and above. size = one hand's wrist-to-fingertip
    length in design px (the group is about 2.4 x size wide), centred at (cx, cy).
    The lower hand lies across the lap, back up, fingers relaxed (it wears the ring when ring_side is +1/-1, the band on
    its ring finger with a glint); the other hand cradles it from below (its fingertips show under the knuckles) and its
    thumb lies over the base of the ring finger, rocking +-rub_amp deg about the base knuckle with rub_phase (radians:
    pass e.g. (t - t0) * 4.6). ring_side None = no ring (the lower hand is the character's left). Sleeve cuffs come in
    from the frame edges (coat / hoodie / uniform / cardigan colours). thread=True hangs a lit loose thread from the
    lower hand's cuff."""
    sp = CAST[who]
    P = Pose(t=t)
    skin, sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh = _limb_cols(sp)[:2]
    k = size / 66.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5)).sub(cx, cy, 0.0, k)
    sB = int(ring_side) if ring_side in (-1, 1) else 1
    sA = -sB
    hb = sp['body'].get('hand', 1.0)
    # placements (lap units, hand length 66)
    L_ = dict(bx=46.0, by=-30.0, bang=50.0, wa=(30.0, 4.0), da=-88.0, tl=27.0)
    if _lay: L_.update(_lay)
    bx, by, bang = sB * L_['bx'], L_['by'], L_['bang'] * sB
    kx, ky = _hpt(bx, by, bang, hb, 0.0, 30.0)                 # centre the clasp (the lower hand's knuckles)
    bx -= kx; by -= ky - 4.0
    thB = -sB
    # the cradling hand, palm up under the lower hand (drawn mirrored, so its thumb lies on top): wrist on the lower
    # hand's thumb side, forearm toward the other side of the frame, fingertips peeking past the little finger
    wa_b = (thB * L_['wa'][0], L_['wa'][1])
    ax, ay = _hpt(bx, by, bang, hb, *wa_b)
    aang = bang + L_['da'] * sB
    sAd = sB
    # sleeves + cuffs (behind the hands)
    if cuffs:
        for s_, (wx, wy, wa) in ((sB, (bx, by, bang)), (sA, (ax, ay, aang))):
            ex_, ey_ = _hpt(wx, wy, wa, hb, 0.0, -4.0)
            fx_, fy_ = _hpt(wx, wy, wa, hb, 0.0, -130.0)
            tube = _tube([(fx_, fy_), (ex_, ey_)], [50.0, 42.0])
            c.fill(tube, sleeve); c.fill(_crescent(tube, 0, 8), sleeve_sh, 170); c.line(tube, c.lw)
            cuff = c.sub(ex_, ey_, wa, 1.0)
            cp = rrect(-22.5, -14, 45, 14, 4)
            cuff.fill(cp, mix(sleeve, '#000000', 0.18)); cuff.line(cp, c.lw * 0.8)
            if sp['outfit'] == 'hoodie' and detail >= 1:
                cuff.line(_multi([poly([(q * 5.0, -12), (q * 5.0, -2)], False) for q in range(-4, 5)]), c.lw * 0.3, LINE, 140)
            if s_ == sB and thread:
                corners = [_hpt(wx, wy, wa, hb, q * 22.0, -14.0) for q in (-1, 1)]
                thread_p0 = max(corners, key=lambda q: q[1])
    # the cradling hand (under), without its thumb
    _draw_hand(c, sp, 'palm4', ax, ay, 1.0, aang, sAd, detail, skin, sh, False, 0.0, t)
    # the lower hand, relaxed, ring on its ring finger
    _draw_hand(c, sp, 'relaxed', bx, by, 1.0, bang, sB, detail, skin, sh, ring_side in (-1, 1), 0.0, t)
    # the rubbing thumb of the cradling hand: from beside the little finger to the base of the ring finger
    G = _hand_cached('relaxed', sB, 0.0)
    rx, ry, rang, rw = G['ring']
    tgt_b = (-thB * 4.8, 31.5)
    tb0 = _hpt(ax, ay, aang, hb, -sAd * 15.0, 10.0)
    tgt = _hpt(bx, by, bang, hb, *tgt_b)
    ang0 = math.atan2(tgt[0] - tb0[0], tgt[1] - tb0[1])
    da = math.radians(rub_amp * math.sin(rub_phase)) if (rub and rub_phase is not None) else 0.0
    L1 = L_['tl'] * 0.54 * hb; L2 = L_['tl'] * 0.46 * hb
    a1 = ang0 + da
    j = (tb0[0] + math.sin(a1) * L1, tb0[1] + math.cos(a1) * L1)
    a2 = a1 + math.radians(6.0 * sB) + da * 0.5
    tip = (j[0] + math.sin(a2) * L2, j[1] + math.cos(a2) * L2)
    if cuffs and thread:                                       # the loose thread hangs free from the lower cuff, lit
        p0 = thread_p0
        sw = 4.0 * math.sin(t * 2.3) + 2.0 * math.sin(t * 3.7 + 1)
        th_ = smooth([p0, (p0[0] + sw * 0.3 + 1, p0[1] + 12), (p0[0] + sw * 0.7 - 2, p0[1] + 26), (p0[0] + sw, p0[1] + 40)], False)
        c.line(th_, c.lw * 0.7, LINE, 210); c.line(th_, c.lw * 0.38, '#d6d9de', 255)
    pts = [tb0, j, tip]
    thumb = _tube(pts, [12.0 * hb, 10.6 * hb, 9.0 * hb], 0.9)
    c.fill(thumb, skin); c.fill(_crescent(thumb, -2.5, -2.5), sh, 150); c.line(thumb, c.lw * 0.9)
    if detail >= 1:
        dx, dy = tip[0] - j[0], tip[1] - j[1]; Ld = math.hypot(dx, dy) or 1.0
        nc = c.sub(tip[0], tip[1], -math.degrees(math.atan2(dx, dy)))
        nl = rrect(-3.0 * hb, -Ld * 0.66, 6.0 * hb, Ld * 0.52, 2.8 * hb)
        nc.fill(nl, mix(skin, '#ffffff', 0.38), 230); nc.line(nl, c.lw * 0.25, sp['skin_dp'], 200)
        jc = c.sub(j[0], j[1], -math.degrees(a1))
        jc.line(smooth([(-3.5, -1.0), (0, 1.2), (3.5, -1.0)], False), c.lw * 0.32, sp['skin_dp'], 170)
    if light and light.get('rim'):
        c.fill(_crescent(thumb, -light.get('side', 1) * 2.5, 0), light['rim'], light.get('rim_a', 70))
    return dict(ring=_hpt(bx, by, bang, hb, rx, ry) if ring_side in (-1, 1) else None, thumb_tip=tip, scale=k,
                ring_xy=(cx + _hpt(bx, by, bang, hb, rx, ry)[0] * k, cy + _hpt(bx, by, bang, hb, rx, ry)[1] * k))


def draw_palm_on_glass(pen, who, x, y, size, press=1.0, t=0.0, angle=0.0, side=1, alpha=1.0, halo=1.0, slide=0.0,
                       light=None, detail=2):
    """v2.1: an open hand pressed flat on glass, palm toward the viewer, FINGERS UP at angle 0 (unlike draw_hand, where
    angle 0 = fingers down), 5 spread fingers with flattened pale pads, a darker pressed rim and a soft condensation
    halo. size = wrist-to-fingertip in design px; (x, y) = the wrist; slide = extra y (design px) for a slow slide down
    the glass; alpha 0..1 fades the whole hand. Place it beside the face, not over it."""
    sp = CAST[who]
    P = Pose(t=t)
    skin, sh, _ = _skin_cols(sp, P, light)
    k = size / 66.0
    cv = pen.cv
    lay = alpha < 0.999
    if lay: cv.saveLayerAlpha(None, int(255 * clamp(alpha)))
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5)).sub(x, y + slide, 180.0 + angle, k * sp['body'].get('hand', 1.0))
    G = _hand_cached('flat', side, round(clamp(press), 1))
    u = G['union']
    if halo > 0:
        c.glow(0, 30, 62, 58, '#dce8f4', 70 * halo)
        c.line(u, 9.0, '#e6eff8', 60 * halo)
        c.line(u, 4.5, '#eef4fb', 90 * halo)
    pskin = mix(skin, '#e8d6cf', 0.25 * press)
    c.fill(u, pskin)
    c.fill(G['shade'], sh, 110)
    c.line(u, c.lw * 1.7, mix(skin, '#7b5a52', 0.55), 130 * press)          # pressed rim
    if detail >= 1:
        if G['creases_p'] is not None: c.line(G['creases_p'], c.lw * 0.32, sp['skin_dp'], 160)
        if G['lines_p'] is not None: c.line(G['lines_p'], c.lw * 0.38, sp['skin_dp'], 160)
        if G['seps'] is not None: c.line(G['seps'], c.lw * 0.4, LINE, 140)
    for p in G['press']: c.fill(p, '#f3e8e2', 200 * press)
    c.line(u, c.lw * 0.9)
    if lay: cv.restore()


# ====================================================================================================== acting
import bisect as _bisect
import re as _re

VISEMES = {  # open, wide, round, teeth, press
    'A': (0.60, 0.15, 0.0, 0.45, 0.0), 'E': (0.34, 0.55, 0.0, 0.7, 0.0), 'I': (0.24, 0.75, 0.0, 0.8, 0.0),
    'O': (0.50, -0.2, 0.8, 0.15, 0.0), 'U': (0.20, -0.3, 1.0, 0.0, 0.0), 'M': (0.0, 0.0, 0.0, 0.0, 0.7),
    'F': (0.10, 0.25, 0.0, 0.9, 0.0), 'L': (0.30, 0.2, 0.0, 0.6, 0.0), 'rest': (0.04, 0.0, 0.0, 0.1, 0.1),
}


def _env(t, t0, t1=None, fin=0.3, fout=0.3, ein=ease_in_out, eout=ease_in_out):
    """Envelope: eases in over fin from t0, holds, eases out over fout from t1 (t1 None = hold forever)."""
    if t < t0: return 0.0
    a = ein(prog(t, t0, t0 + fin)) if fin > 0 else 1.0
    if t1 is None: return a
    if t >= t1 + fout: return 0.0
    b = 1.0 - eout(prog(t, t1, t1 + fout)) if fout > 0 else float(t < t1)
    return min(a, b)


def _syllables(word):
    w = word.lower().replace("'", '')
    groups = _re.findall(r'[^aeiouy]*[aeiouy]+', w)
    if not groups: return [(w, '')]
    out = []
    for g in groups:
        m = _re.match(r'([^aeiouy]*)([aeiouy]+)', g)
        out.append((m.group(1), m.group(2)))
    if len(out) > 1 and out[-1][1] == 'e' and not out[-1][0].endswith('l'): out = out[:-1]   # silent e
    return out


def _vowel_vis(v):
    if v.startswith(('ee', 'ea', 'ie', 'y', 'i')): return 'I'
    if v.startswith(('oo', 'u', 'ew')): return 'U'
    if v.startswith(('ou', 'ow', 'o', 'au', 'aw')): return 'O'
    if v.startswith(('ai', 'ay', 'e', 'ei')): return 'E'
    return 'A'


def _onset_vis(c):
    if not c: return None
    ch = c[-1]
    if ch in 'mbp': return 'M'
    if ch in 'fv': return 'F'
    if ch in 'w': return 'U'
    if ch in 'ltdn': return 'L'
    return None


# ------------------------------------------------------------------ voice envelope + word timing (lip sync, v2.1)
_SCR = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
VOICE_WAV = os.environ.get('POV2_VOICE_WAV', os.path.join(_SCR, 'pov2', 'align', 'vo_en.wav'))
VOICE_WORDS = os.environ.get('POV2_VOICE_WORDS', os.path.join(_SCR, 'pov2', 'align', 'asr_cache.json'))
ENV_FPS = 100.0
_VENV, _VWORDS = {}, {}


def voice_envelope(path=None):
    """RMS envelope of the voice track in dBFS at 100 fps (30 ms window), as float32 np array, or None if the file is
    missing. Cached in memory and as .npy in $S/pov2/cache (keyed by size and mtime), so render workers load it in ms."""
    path = path or VOICE_WAV
    if path in _VENV: return _VENV[path]
    env = None
    try:
        st = os.stat(path)
        cdir = os.path.join(_SCR, 'pov2', 'cache')
        cache = os.path.join(cdir, 'vo_env_%d_%d.npy' % (st.st_size, int(st.st_mtime)))
        if os.path.exists(cache):
            env = np.load(cache)
        else:
            import soundfile as sf
            y, sr = sf.read(path, dtype='float32', always_2d=True)
            y = y.mean(1)
            hop = int(round(sr / ENV_FPS)); n = len(y) // hop
            p = (y[:n * hop] ** 2).reshape(n, hop).mean(1)
            p = np.convolve(p, np.ones(3) / 3.0, 'same')
            env = (10.0 * np.log10(np.maximum(p, 1e-10))).astype(np.float32)
            try:
                os.makedirs(cdir, exist_ok=True); np.save(cache, env)
            except OSError:
                pass
    except Exception:
        env = None
    _VENV[path] = env
    return env


def voice_words(path=None):
    """[(word, t_start)] from the ASR cache (en_words), or [] when it is missing."""
    path = path or VOICE_WORDS
    if path in _VWORDS: return _VWORDS[path]
    out = []
    try:
        import json as _json
        out = [(str(w), float(t)) for w, t in _json.load(open(path))['en_words']]
    except Exception:
        out = []
    _VWORDS[path] = out
    return out


def _env_db(env, t):
    """Envelope value (dBFS) at time t, linearly interpolated (env: 100 fps array, or a callable t -> dBFS)."""
    if callable(env): return float(env(t))
    x = t * ENV_FPS
    i = int(math.floor(x))
    if i < 0 or i >= len(env) - 1: return -100.0
    u = x - i
    return float(env[i] * (1 - u) + env[i + 1] * u)


class Acting:
    """Timeline of acting clips for one character. See the module docstring for the clip vocabulary."""

    def __init__(self, who='officer', seed=0, height=700.0, expr='neutral', blink=None, life=1.0):
        self.who, self.seed, self.height = who, int(seed), float(height)
        self.life_k = float(life)
        sp = CAST[who]
        self.sp = sp
        self.expr0 = expr
        self.blink_rate = sp['blink_rate'] if blink is None else (0.33 if blink is True else (0.0 if blink is False else float(blink)))
        self.micro = sp['micro']
        self.clips = []              # (t0, t1, fn, realtime)
        self.late = []               # clips that override everything else (snap_turn)
        self.freezes = []            # (t0, t1)
        self.events = []
        self.base = dict(lock=sp['lock'], pupil=1.0)
        rng = np.random.default_rng(900 + self.seed * 31 + len(who))
        # blink schedule
        self._blinks = []
        if self.blink_rate > 0:
            tt = rng.uniform(0.3, 2.0)
            while tt < 1500:
                self._blinks.append(tt)
                if rng.uniform() < 0.28:                           # nervous double blink
                    self._blinks.append(tt + rng.uniform(0.13, 0.2)); tt = self._blinks[-1]
                tt += max(0.6, rng.exponential(1.0 / self.blink_rate)) + 0.4
        # v2.1 idle life schedules: head re-settles (pose swaps), weight shifts, micro twitches (creepy cast)
        self.creepy = sp['lock'] >= 0.5
        def sched(lo, hi, n_t, f):
            ts, vs = [-1e9], [tuple(0.0 for _ in range(n_t))]
            tt = rng.uniform(0.2, hi)
            while tt < 1500:
                ts.append(tt); vs.append(f()); tt += rng.uniform(lo, hi)
            return ts, vs
        sgn = [1.0]
        def settle():
            sgn[0] = -sgn[0] if rng.uniform() < 0.7 else sgn[0]
            return (sgn[0] * rng.uniform(1.5, 4.5), rng.uniform(-0.035, 0.035), rng.uniform(-2.5, 2.5))
        self._set_t, self._set_v = sched(2.0, 3.6, 3, settle)
        self._nv_t, self._nv_v = sched(1.3, 2.6, 3, lambda: (rng.uniform(-4.0, 4.0), rng.uniform(-0.07, 0.07), rng.uniform(-0.045, 0.045)))
        self._ws_t, self._ws_v = sched(3.5, 6.5, 1, lambda: (rng.uniform(-6.0, 6.0),))
        self._tw_t, self._tw_v = sched(4.5, 8.5, 3, lambda: (rng.uniform(0.3, 0.55), 1.0 if rng.uniform() < 0.5 else -1.0, rng.uniform(-1, 1)))
        # saccade schedule for unlocked eyes
        self._sacc_t, self._sacc_xy = [-1e9], [(0.0, 0.0)]
        tt = 0.0
        while tt < 1500:
            tt += rng.uniform(0.7, 2.6)
            self._sacc_t.append(tt); self._sacc_xy.append((rng.uniform(-0.45, 0.45), rng.uniform(-0.25, 0.18)))

    # ------------------------------------------------------------------ core
    def _add(self, t0, t1, fn, real=False, late=False):
        (self.late if late else self.clips).append((t0, INF if t1 is None else t1, fn, real))
        return self

    def _ev(self, t, name, gain_db=0.0, pan=0.0, **params):
        e = dict(t=round(float(t), 4), name=name, gain_db=gain_db, pan=pan, params=params, who=self.who)
        self.events.append(e); return e

    def _tmap(self, t):
        for a, b in self.freezes:
            if a <= t <= b: return a
        return t

    def _blink_amt(self, t):
        if not self._blinks: return 0.0
        i = _bisect.bisect_right(self._blinks, t) - 1
        if i < 0: return 0.0
        dt = t - self._blinks[i]
        if dt < 0.017: return dt / 0.017
        if dt < 0.05: return 1.0
        if dt < 0.067: return 1.0 - (dt - 0.05) / 0.017
        return 0.0

    def _saccade(self, t):
        i = _bisect.bisect_right(self._sacc_t, t) - 1
        x1, y1 = self._sacc_xy[i]
        x0, y0 = self._sacc_xy[max(i - 1, 0)]
        u = ease_out_cubic(prog(t, self._sacc_t[i], self._sacc_t[i] + 0.06))
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u

    def _raw(self, t):
        tf = self._tmap(t)
        P = Pose()
        P.t = t
        P.mix(self.base); P.mix(EXPR[self.expr0])
        sd = self.seed * 7 + 3
        # idle: breathing, micro head motion, sway, wandering eyes
        P.breath = 0.5 + 0.45 * math.sin(2 * PI * tf / 3.9 + sd) + 0.08 * noise1(tf * 0.4, sd)
        for (t0, t1, fn, real) in (self.clips + self.late if self.late else self.clips):
            tt = t if real else tf
            if (t0 == -INF or t0 - 1.5 <= tt) and tt <= t1 + 1.5: fn(P, tt)
        m = self.micro * (1.0 - clamp(P.still))
        P.h_tilt += 1.7 * m * noise1(tf * 0.21, sd + 1)
        P.h_turn += 0.035 * m * noise1(tf * 0.16, sd + 2)
        P.h_nod += 0.03 * m * noise1(tf * 0.19, sd + 3)
        P.sway += 3.0 * m * noise1(tf * 0.3, sd + 4)
        P.tilt += 0.5 * m * noise1(tf * 0.13, sd + 5)
        lf = self.life_k * clamp(P.life)
        if P.still > 0: P.breath = lerp(P.breath, 0.5 + (0.15 + 0.17 * lf) * math.sin(2 * PI * tf / 4.6 + sd), clamp(P.still))
        if lf > 0.01: self._life(P, tf, lf, sd)
        sx, sy = self._saccade(tf)
        un = (1.0 - clamp(P.lock)) * (1.0 - clamp(P.still))
        P.look_x += sx * un; P.look_y += sy * un
        b = self._blink_amt(tf) * (1.0 - clamp(P.still)) * (1.0 - clamp(getattr(P, '_noblink', 0.0)))
        P.blink = max(P.blink, b)
        return P

    @staticmethod
    def _step(ts, vs, t, dur, fn=ease_out_cubic):
        """Value of a step schedule at t: eased move from the previous target to the current one over dur."""
        i = _bisect.bisect_right(ts, t) - 1
        if i <= 0: return vs[0]
        u = fn(prog(t, ts[i], ts[i] + dur))
        a, b = vs[i - 1], vs[i]
        return tuple(x + (y - x) * u for x, y in zip(a, b))

    def _life(self, P, tf, lf, sd):
        """v2.1 idle life, layered after the clips. Creepy cast (and anyone staring): very slow head drift, a head
        re-settle (pose swap) every 2-3.6 s, slow weight shifts, and (creepy cast) a small involuntary twitch every
        4.5-8.5 s. Scared cast (you, mum): quick nervous head re-orients every 1.3-2.6 s scaled by the fear in the face,
        and a shiver (8-12 Hz) with pose.tremble. Breathing never stops (only freeze() stops everything). No blinks."""
        st = clamp(P.still)
        k = lf * (1.0 if self.creepy else st)
        if k > 0.01:
            P.h_tilt += 3.2 * k * noise1(tf * 0.06, sd + 21)
            P.h_turn += 0.02 * k * noise1(tf * 0.05, sd + 22)
            a_, n_, x_ = self._step(self._set_t, self._set_v, tf, 0.32)
            P.h_tilt += a_ * k; P.h_nod += n_ * k; P.h_dx += x_ * k
            (w_,) = self._step(self._ws_t, self._ws_v, tf, 0.9, ease_in_out)
            P.sway += w_ * k; P.tilt += 0.22 * w_ * k
        if self.creepy and lf > 0.01:
            i = _bisect.bisect_right(self._tw_t, tf) - 1
            if i > 0:
                tau = tf - self._tw_t[i]
                if 0 <= tau < 0.6:
                    amp, d1, d2 = self._tw_v[i]
                    f = math.exp(-tau * 9.0) * math.sin(tau * 46.0) * amp * lf
                    P.h_tilt += 9.0 * f * d1; P.h_dx += 5.0 * f * d2; P.shrug += 0.2 * abs(f)
                    P.brow_asym += 0.5 * f * d1; P.m_side += 0.4 * f * d1
        if not self.creepy and lf > 0.01:
            # scared cast: quick nervous head re-orients (small glances, swallow dips) scaled by how afraid the face is
            fk = clamp(max(1.3 * P.tremble, 0.9 * P.brow_sad, P.sweat, 0.8 * P.wide)) * lf * (1.0 - 0.6 * clamp(P.lock))
            if fk > 0.05:
                a_, h_, n_ = self._step(self._nv_t, self._nv_v, tf, 0.18)
                P.h_tilt += a_ * fk; P.h_turn += h_ * fk; P.h_nod += n_ * fk
        tr = clamp(P.tremble) * (0.0 if self.creepy else 1.0) * lf
        if tr > 0.12:
            P.h_dx += 0.5 * tr * noise1(tf * 10.0, sd + 31)
            P.h_tilt += 0.8 * tr * noise1(tf * 9.0, sd + 32)
            P.shrug += 0.03 * tr * noise1(tf * 11.0, sd + 33)

    def at(self, t):
        """Pose at time t (seconds), with secondary motion (cord / hair / drawstring swing) from lagged motion."""
        P = self._raw(t)
        a = self._raw(t - 0.09); b = self._raw(t - 0.2)
        v = (a.h_tilt - P.h_tilt) * 0.05 + (b.h_tilt - a.h_tilt) * 0.03 + (a.turn + a.h_turn - P.turn - P.h_turn) * 1.2 + \
            (a.dx - P.dx) * 0.012 + (a.sway - P.sway) * 0.05 + (a.tilt - P.tilt) * 0.05
        P.sec_x = clamp(v, -1.5, 1.5)
        P.sec_y = clamp((a.lean - P.lean) * 2.0 + (a.bob - P.bob) * 0.02, -1, 1)
        return P

    __call__ = at

    def depth(self, base, k=0.55):
        """Layer depth function for lean_in: base * (1 - k * approach(t))."""
        return lambda t: base * (1.0 - k * clamp(self.at(t).approach))

    def cues(self):
        return sorted(self.events, key=lambda e: e['t'])

    # ------------------------------------------------------------------ expressions and looks
    def expr(self, name, t0, t1=None, fade=0.35):
        d = EXPR[name]
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def set(self, t0, t1=None, fade=0.3, **params):
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(params, _env(t, t0, t1, fade, fade)))

    def idle(self, t0=0.0, t1=None):
        return self.set(t0, t1, 0.4, lock=0.0, still=0.0)

    def look(self, t0, x, y, dur=0.12, t1=None):
        return self.set(t0, t1, dur, look_x=x, look_y=y, lock=0.0)

    def stare(self, t0, t1=None, fade=0.4):
        d = dict(pupil=0.5, wide=0.5, brow_up=0.3, lock=1.0, still=1.0, bloodshot=0.45)
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def creep_smile(self, t0, dur=4.0, t1=None, amount=1.0, fade=0.6):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            w = _env(t, t0, t1, 0.05, fade)
            if w <= 0: return
            P.mix(dict(smile=0.95 * amount * u, grin=0.5 * amount * ease_in_cubic(u), teeth=clamp((u - 0.35) / 0.4) * amount,
                       pupil=lerp(P.pupil, 0.55, u), wide=lerp(P.wide, 0.32, u), brow_up=lerp(P.brow_up, 0.3, u), lock=1.0,
                       still=u, bloodshot=0.35 * u), w)
            P.h_tilt += 5.0 * u * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def wide_grin(self, t0, t1=None, fade=0.6):
        d = EXPR['wide_grin']
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            P.mix(d, w)
            P.m_side += 0.12 * w * noise1(t * 3.0, self.seed + 40)
            P.still = max(P.still, w)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    # ------------------------------------------------------------------ head
    def head_tilt(self, t0, angle=32.0, dur=1.6, t1=None, back='ease', back_dur=None):
        bd = back_dur or (0.3 if back == 'snap' else dur)
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if t1 is not None and t >= t1:
                if back == 'snap': u = u * (1.0 - spring(t - t1, 3.2, 0.42))
                else: u = u * (1.0 - ease_in_out(prog(t, t1, t1 + bd)))
            a = angle * u
            P.h_tilt += a
            extra = max(0.0, abs(a) - 20.0) * (1 if a > 0 else -1)
            P.h_dx += -extra * 0.9
            P.h_dy += abs(extra) * 0.25
            P.tilt += a * 0.06
        return self._add(t0, None if t1 is None else t1 + bd + 1.0, fn)

    def snap_turn(self, t, frm=1.0, to=0.0, hold=0.6, body=0.35, until=None, release=0.5):
        """Head held at `frm` (from t-hold), snaps to `to` at t with a spring overshoot. Eyes lead by 50 ms, body follows.
        v2.1: the snap TAKES CONTROL of the yaw (it overrides earlier clips such as a held look-aside instead of adding to
        them) and holds `to` after the snap until `until` (None = for good), then releases over `release` s. It runs after
        the ordinary clips whatever the order they were added in. frm=None starts from the current head yaw."""
        def fn(P, tt):
            w_in = ease_in_out(prog(tt, t - hold, t - hold + 0.25))
            if until is not None and tt > until: w_in *= 1.0 - ease_in_out(prog(tt, until, until + release))
            if w_in <= 0: return
            body0 = 0.0
            f = (P.turn + P.h_turn) if frm is None else frm
            if tt < t:
                h = f
            else:
                h = to + (f - to) * (1.0 - spring(tt - t, 3.6, 0.5))
            bodyk = (1.0 - ease_out_cubic(prog(tt, t + 0.06, t + 0.5))) if tt >= t else 1.0
            b_des = body0 + (f - body0) * body * bodyk
            P.turn = lerp(P.turn, b_des, w_in)
            P.h_turn = lerp(P.h_turn, h - b_des, w_in)
            P.lock = lerp(P.lock, 1.0, prog(tt, t - 0.06, t - 0.01) * w_in)
            if tt >= t:
                P.look_x = lerp(P.look_x, 0.0, w_in); P.look_y = lerp(P.look_y, 0.0, w_in)
                k = math.exp(-(tt - t) * 6.0)
                P.h_tilt += 7.0 * math.sin((tt - t) * 26.0) * k
                P.wide += 0.35 * k; P.pupil *= 1.0 - 0.3 * k
        return self._add(t - hold - 0.3, (until + release) if until is not None else None, fn, late=True)

    def lean_in(self, t0, dur=2.5, t1=None, amount=1.0, back_dur=0.9):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if t1 is not None and t >= t1: u *= 1.0 - ease_in_out(prog(t, t1, t1 + back_dur))
            P.lean += 0.7 * amount * u
            P.approach += amount * u
            P.h_nod -= 0.1 * u
            P.lock = lerp(P.lock, 1.0, u)
        return self._add(t0, None if t1 is None else t1 + back_dur, fn)

    def head_down(self, t0, t1=None, amount=1.0, fade=0.8):
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            P.h_nod += 0.55 * amount * w
            P.h_dy += 8 * amount * w
            if P.lock < 0.5: P.look_y += 0.5 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def turn(self, t0, to, dur=0.6):
        """Body + head yaw to `to` (quarter turns). The head leads, the body follows (overlapping action)."""
        def fn(P, t):
            base = P.turn
            wh = ease_in_out(prog(t, t0, t0 + dur * 0.6))
            wb = ease_in_out(prog(t, t0 + dur * 0.15, t0 + dur))
            P.turn = base + (to - base) * wb
            P.h_turn += (to - base) * (wh - wb)
        return self._add(t0, None, fn)

    def turn_back(self, t0, dur=0.45, side=1):
        return self.turn(t0, 2.0 * side, dur)

    # ------------------------------------------------------------------ body and hands
    def _arm(self, P, side, w, out, down, fwd, shape=None, up=None, prop=None, press=None, rot=None):
        pre = 'hl_' if side > 0 else 'hr_'
        d = {pre + 'out': out, pre + 'down': down, pre + 'fwd': fwd}
        if up is not None: d[pre + 'up'] = up
        if press is not None: d[pre + 'press'] = press
        if rot is not None: d[pre + 'rot'] = rot
        if shape is not None: d[pre + 'shape'] = shape
        if prop is not None or w >= 0.5: d[pre + 'prop'] = prop
        P.mix(d, w)

    def knock(self, t0, n=3, spacing=0.32, side=0.0, hand=None, strength=1.0, reach=0.72):
        """Fist knocks. Returns the knock_door events (one per hit).
        side +1/-1: the door slab is to screen right/left of the lens (a doorbell sits beside the door): the near arm
            (hand=None picks it) reaches out at shoulder height (`reach` x arm length, >= 0.6) with a forearm snap on every
            hit, the body rocks 2-4 deg into the knock and the head stays locked on the lens.
        side 0: knock on the lens itself (peephole / doorbell glass): the fist comes up to face height in front of the
            body and grows ~1.3x toward the lens on each hit (events carry params lens=True: pair them with a ~1.5% camera
            punch)."""
        first = t0 + 0.34
        hits = [first + i * spacing for i in range(n)]
        end = hits[-1] + 0.45
        hs = hand if hand is not None else (int(math.copysign(1, side)) if side else -1)
        b_ = self.sp['body']
        L = 348.0 * reach

        def pulse_at(t):
            pulse = 0.0
            for h in hits:
                d = t - h
                if -0.11 <= d < 0: pulse = max(pulse, ease_in_cubic(prog(d, -0.11, 0)))
                elif 0 <= d < 0.17: pulse = max(pulse, 1.0 - ease_out_cubic(d / 0.17))
            return pulse

        def fn(P, t):
            w = _env(t, t0, end - 0.3, 0.32, 0.42, ease)
            if w <= 0: return
            pulse = pulse_at(t) * w
            if side:
                out = L * 0.82 + 38.0 * pulse
                self._arm(P, hs, w, out, -14.0 + 8.0 * pulse, 70.0 + 20.0 * pulse, 'fist', up=0.08)
                P.tilt += (2.0 + 1.6 * strength) * pulse * (1 if hs > 0 else -1)
                P.lean += 0.02 * pulse * strength
                P.turn += 0.1 * side * w; P.h_turn -= 0.1 * side * w
            else:
                self._arm(P, hs, w, 55.0 - (b_['sh'] - 17), -46.0 + 12.0 * pulse, 290.0 + 160.0 * pulse * strength, 'fist', up=0.95)
                setattr(P, ('hl_' if hs > 0 else 'hr_') + 'scale', 1.0 + 0.16 * pulse * strength)
                P.lean += 0.045 * pulse * strength
                P.h_nod += 0.02 * pulse
            P.lock = lerp(P.lock, 1.0, w)
        self._add(t0, end + 0.5, fn)
        evp = dict(lens=True) if not side else {}
        return [self._ev(h, 'knock_door', 0.0 if i == 0 else -1.0, pan=0.0 if not side else 0.35 * side, n=1, strength=strength, **evp)
                for i, h in enumerate(hits)]

    def radio_to_mouth(self, t0, t1, side=1, tilt=13.0):
        """The hand brings the shoulder speaker-mic up beside the mouth (the coiled cord follows), the head tilts 12-15 deg
        into it with the eyes locked on the lens, and the thumb squashes the push-to-talk key on each click."""
        sp = self.sp; b = sp['body']; hh = sp['hh']
        clicks = [t0 + 0.38, t1 - 0.02]
        mouth = -hh / 2 + sp['mouth_y'] * hh / 240.0          # mouth relative to the chin line
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4, ease)
            if w <= 0: return
            down = mouth + 46.0 - 64.0 + 26.0 * P.shrug
            out = (hh * 100.0 / 240.0) * 0.62 - (b['sh'] - 17)
            pr = 0.0
            for c_ in clicks:
                pr = max(pr, math.exp(-((t - c_) / 0.07) ** 2))
            self._arm(P, side, w, out, down, 78.0, 'grip', up=1.0, prop='mic', press=pr, rot=-side * 8.0)
            P.h_tilt += tilt * side * w; P.h_turn += 0.1 * side * w; P.h_nod += 0.08 * w
            P.lock = lerp(P.lock, 1.0, w)
            P.shrug += 0.1 * w
        self._add(t0, t1 + 0.4, fn)
        return [self._ev(clicks[0], 'radio_click', -3.0), self._ev(clicks[1], 'radio_click', -3.0),
                self._ev(t1 + 0.02, 'police_radio_squelch', -9.0)]

    def phone_to_ear(self, t0, t1=None, side=1, fade=0.5, tilt=6.0):
        """Phone held to the ear (busts and full body): wrist just below the ear, elbow forward and down, the dark back of
        the phone along the cheek, the hand wrapped round it; the head leans into it. side +1 = character's left hand."""
        pre = 'hl_' if side > 0 else 'hr_'
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            self._arm(P, side, w, 0.0, -20.0, 40.0, 'grip', up=1.0, prop='phone')
            setattr(P, pre + 'ear', max(getattr(P, pre + 'ear'), w))
            P.h_tilt += tilt * side * w
            P.shrug += 0.08 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def press_bodycam(self, t, on=True, side=-1):
        b = self.sp['body']; press = t + 0.42
        def fn(P, tt):
            w = _env(tt, t, t + 0.6, 0.4, 0.42, ease)
            if w > 0:
                poke = 6.0 * math.exp(-((tt - press) / 0.06) ** 2)
                self._arm(P, side, w, -(b['sh'] - 17) + 12, 70.0, 92.0 - poke, 'point', up=0.92, rot=-12 * side)
                P.h_nod += 0.08 * w
            P.cam_on = (1.0 if on else 0.0) if tt >= press else (0.0 if on else 1.0)
        self._add(t - 1.0, None, fn)
        return [self._ev(press, 'bodycam_beep', -2.0)]

    def hold_up(self, prop, t0, t1, side=-1):
        def fn(P, t):
            w = _env(t, t0, t1, 0.5, 0.45, ease)
            if w <= 0: return
            bob = 3.0 * noise1(t * 1.3, self.seed + 9)
            self._arm(P, side, w, -(self.sp['body']['sh'] - 17) * 0.45, -105.0 + bob, 240.0, 'grip', up=1.0, prop=prop)
            P.h_nod += 0.04 * w
        self._add(t0, t1 + 0.5, fn)
        name = {'card': 'paper', 'notebook': 'paper', 'photo': 'paper', 'radio': 'radio_click', 'phone': 'ui_pop'}.get(prop)
        return [self._ev(t0 + 0.1, name, -6.0)] if name else []

    def hand_on_glass(self, t0, t1, side=1, reach=470.0):
        contact = t0 + 0.55
        def fn(P, t):
            w = _env(t, t0, t1, 0.55, 0.45, ease)
            if w <= 0: return
            pr = clamp((t - contact) / 0.12) * (1.0 - prog(t, t1, t1 + 0.15))
            slide = 4.0 * noise1(t * 0.8, self.seed + 21) * pr
            self._arm(P, side, w, -(self.sp['body']['sh'] - 17) * 0.6, -125.0 + slide, reach, 'flat', up=1.0, press=pr)
            P.lean += 0.12 * w; P.h_nod -= 0.04 * w
        self._add(t0, t1 + 0.5, fn)
        return [self._ev(contact, 'knock_door', -12.0, n=1, soft=True)]

    def point(self, t0, t1, side=-1, dx=1.0, dy=0.0):
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4, ease)
            self._arm(P, side, w, 160.0 * dx * side if dx else 20.0, -40.0 + 200.0 * dy, 220.0, 'point', up=0.0,
                      rot=-90.0 * side)
        return self._add(t0, t1 + 0.4, fn)

    def sit(self, t0, t1=None, fade=0.6):
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            P.sit = lerp(P.sit, 1.0, w)
            for side in (-1, 1):
                self._arm(P, side, w, -48.0, 292.0, 150.0, 'mitt', up=0.0)
            P.thumb = math.sin(t * 5.5) * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def walk(self, t0, t1, x_from, x_to, facing=None, surface='porch', ramp=0.35):
        d = x_to - x_from
        units = abs(d) / (self.height / 1000.0)
        cycles = units / 440.0
        face = facing if facing is not None else (1.0 if d >= 0 else -1.0)
        dur = t1 - t0
        def u_of(t):
            # constant speed with short accelerations: integral of a trapezoid speed profile
            r = min(ramp, dur / 2)
            vmax = 1.0 / (dur - r)
            if t <= t0: return 0.0
            if t >= t1: return 1.0
            x = t - t0
            if x < r: return vmax * x * x / (2 * r)
            if x > dur - r: y = dur - x; return 1.0 - vmax * y * y / (2 * r)
            return vmax * (r / 2 + (x - r))
        def fn(P, t):
            u = u_of(t)
            w = _env(t, t0 - 0.35, t1, 0.45, 0.45, ease)
            P.dx = x_from + d * u
            P.walk_amt = max(P.walk_amt, clamp(_env(t, t0, t1, ramp, ramp)) * (1.0 if dur > 0 else 0))
            P.walk_ph = cycles * u
            P.turn = lerp(P.turn, face, w)
            P.lean += 0.05 * P.walk_amt
        if not getattr(self, '_walked', False):          # stand at the start point before the first walk
            self._walked = True
            self.clips.append((-INF, t0 - 0.5, lambda P, t: setattr(P, 'dx', x_from), False))
        self._add(t0 - 0.5, None, fn)
        # heel strikes at every half cycle
        evs = []
        ts = np.linspace(t0, t1, 600)
        us = np.array([u_of(x) for x in ts]) * cycles * 2.0
        for k in range(1, int(math.floor(cycles * 2.0)) + 1):
            i = int(np.searchsorted(us, k))
            if 0 < i < len(ts):
                evs.append(self._ev(float(ts[i]), 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch', -2.0,
                                    pan=0.0, n=1, foot='L' if k % 2 else 'R'))
        return evs

    # ------------------------------------------------------------------ emotional beats
    def cry(self, t0, t1=None, smile=False, fade=1.2):
        d = EXPR['grin_cry' if smile else 'cry']
        rng = np.random.default_rng(self.seed + 555)
        sobs = []
        tt = t0 + 0.8
        end = (t1 if t1 is not None else t0 + 60.0)
        while tt < end:
            sobs.append(tt); tt += rng.uniform(1.1, 1.9)
        def fn(P, t):
            w = _env(t, t0, t1, fade, 0.8)
            if w <= 0: return
            tears = ease_in_out(prog(t, t0, t0 + 2.2))
            P.mix(d, w); P.tears = max(P.tears, tears * w)
            pulse = 0.0
            for s in sobs:
                if s - 0.1 <= t <= s + 0.6:
                    pulse = max(pulse, ease_out_cubic(prog(t, s - 0.1, s)) * (1 - ease_in_out(prog(t, s, s + 0.6))))
            P.shrug += 0.35 * pulse * w; P.h_nod += 0.07 * pulse * w; P.m_open += (0.0 if smile else 0.15) * pulse * w
            P.blink = max(P.blink, 0.4 * pulse * (0 if smile else 1))
        self._add(t0, None if t1 is None else t1 + 0.8, fn)
        return [self._ev(s, 'breath', -8.0, kind='sob') for s in sobs if t1 is None or s < t1]

    def scream(self, t0, t1, fade=0.12):
        d = EXPR['scream']
        def fn(P, t):
            w = _env(t, t0, t1, fade, 0.35, ease_out_cubic)
            if w <= 0: return
            P.mix(d, w)
            P.h_tilt += (3.5 * math.sin(t * 37.0) + 2.0 * noise1(t * 11, self.seed + 31)) * w
            P.h_dx += 2.5 * noise1(t * 19, self.seed + 32) * w
            P.shrug += 0.3 * w; P.lean -= 0.06 * w; P.jitter = w
        return self._add(t0, t1 + 0.4, fn)

    def _mouth_target(self, dx=0.0, dz=60.0, side=1):
        """(out, down) arm targets that put the hand at the mouth (+dx toward the hand side, body units)."""
        sp = self.sp; hh = sp['hh']; b = sp['body']
        mouth = -hh / 2 + sp['mouth_y'] * hh / 240.0
        return dx - (b['sh'] - 17), mouth + 30.0 - 64.0

    def hand_to_mouth(self, t0, t1=None, side=-1, fade=0.45, shock=True):
        """A hand comes up over the mouth (fingers up, back of the hand to the lens): shock, a stifled sob. The head
        dips into it, the eyes go wide. Works in busts and full body."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            out, down = self._mouth_target(6.0, side=side)
            self._arm(P, side, w, out, down + 30.0, 70.0, 'relaxed', up=1.0, rot=side * 6.0)
            P.h_nod += 0.06 * w; P.shrug += 0.12 * w
            if shock: P.wide = max(P.wide, 0.6 * w); P.brow_up = max(P.brow_up, 0.5 * w); P.pupil = min(P.pupil, 1.0 - 0.4 * w)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def wipe_tears(self, t0, side=1, dur=1.3):
        """The back of the fingers wipes under one eye and out across the cheek, the head tilting into the hand."""
        def fn(P, t):
            w = _env(t, t0, t0 + dur - 0.4, 0.35, 0.4, ease)
            if w <= 0: return
            u = ease_in_out(prog(t, t0 + 0.35, t0 + dur - 0.4))
            out, down = self._mouth_target(0.0, side=side)
            hw = self.sp['hh'] * 100.0 / 240.0
            self._arm(P, side, w, out + hw * (0.15 + 0.55 * u), down - 34.0, 70.0, 'relaxed', up=1.0, rot=-side * (20.0 + 35.0 * u))
            P.h_tilt += 7.0 * side * w; P.h_nod += 0.05 * w
            P.blink = max(P.blink, 0.6 * w * (1 - u))
        return self._add(t0, t0 + dur + 0.2, fn)

    def glasses_off(self, t0, t1=None, side=1):
        """Takes the glasses off (mum): the hand goes to the temple, the glasses come away at t0 + 0.55 and stay held at
        chest height (t1 None = for good; at t1 they go back on). Pose.specs flags them on the face."""
        off = t0 + 0.55
        back = None if t1 is None else t1
        def fn(P, t):
            w_up = _env(t, t0, off, 0.4, 0.35, ease)
            on_face = t < off or (back is not None and t >= back + 0.45)
            P.specs = 1.0 if on_face else 0.0
            out, down = self._mouth_target(0.0, side=side)
            hw = self.sp['hh'] * 100.0 / 240.0
            if w_up > 0 and t < off + 0.35:
                self._arm(P, side, w_up, out + hw * 0.75, down - 52.0, 60.0, 'grip', up=1.0)
            if not on_face:
                w = _env(t, off, back, 0.45, 0.45, ease)
                self._arm(P, side, w, out + hw * 0.2, down + 120.0, 130.0, 'grip', up=0.9, prop='glasses' if w > 0.3 else None)
            if back is not None and back - 0.1 <= t < back + 0.6:
                w2 = _env(t, back, back + 0.2, 0.3, 0.3, ease)
                self._arm(P, side, w2, out + hw * 0.75, down - 52.0, 60.0, 'grip', up=1.0)
        return self._add(t0, None if t1 is None else t1 + 1.0, fn)

    def flinch(self, t, amp=1.0):
        """Startle on a hit / knock: the head jerks back and down, shoulders up, eyes squeeze shut for 2 frames, then a
        wide-eyed settle."""
        def fn(P, tt):
            tau = tt - t
            if tau < 0 or tau > 0.9: return
            k = math.exp(-tau * 6.5) * (1 - math.exp(-tau * 40.0))
            P.h_nod -= 0.12 * amp * k; P.h_dy += 6.0 * amp * k; P.shrug += 0.45 * amp * k; P.lean -= 0.05 * amp * k
            P.h_tilt += 4.0 * amp * k * (1 if hash01(int(t * 10), self.seed) > 0.5 else -1)
            if tau < 0.07: P.blink = max(P.blink, 1.0)
            P.wide = max(P.wide, 0.7 * amp * math.exp(-tau * 3.0)); P.pupil = min(P.pupil, 1.0 - 0.4 * amp * k)
        return self._add(t - 0.05, t + 1.0, fn, real=True)

    def creep(self, t0, t1, tilt=8.0, jerk_at=None, side=None, sway=5.0):
        """One-call weird beat for a held creepy shot: a slow over-long head tilt drifting over the whole shot (to `tilt`
        deg), a weight shift with sway, and a jerk at jerk_at (default 55 % through; None-able via jerk_at=False).
        Breathing continues. Typical: a.creep(s.t0, s.t1) on every officer door / peep shot."""
        sd = side if side is not None else (1.0 if hash01(int(t0 * 10), self.seed + 77) > 0.5 else -1.0)
        dur = max(0.5, t1 - t0)
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t1))
            w = _env(t, t0 - 0.2, t1, 0.3, 0.4)
            P.h_tilt += tilt * sd * u * w
            P.h_dx -= 0.25 * tilt * sd * u * w
            v = ease_in_out(prog(t, t0 + dur * 0.15, t0 + dur * 0.45))
            P.sway += sway * sd * v * w; P.tilt += 0.6 * sd * v * w
        self._add(t0 - 0.3, t1 + 0.5, fn)
        if jerk_at is not False:
            self.jerk(t0 + dur * 0.55 if jerk_at is None else jerk_at, 0.7)
        return self

    def impatient(self, t0, dur=2.6, side=1):
        """'He looks impatient': weight shift, a glance away toward the street (side), a sharp look back at the lens and a
        twitch on arrival."""
        g0, g1 = t0 + 0.5, t0 + dur * 0.62
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.4, 0.4)
            if w <= 0: return
            P.sway += 6.0 * side * ease_in_out(prog(t, t0, t0 + 0.6)) * w
            gl = ease_out_cubic(prog(t, g0, g0 + 0.3)) * (1.0 - spring(t - g1, 3.4, 0.5) if t >= g1 else 1.0)
            P.h_turn += 0.55 * side * gl
            P.lock = lerp(P.lock, 0.0, gl); P.look_x += 0.7 * side * gl
            P.brow_angry += 0.3 * w; P.m_press += 0.4 * w
        self._add(t0 - 0.2, t0 + dur + 0.5, fn)
        self.twitch([g1 + 0.12], 0.8)
        return self

    def nervous_glance(self, t0, n=2, side=-1, dur=1.4):
        starts = [t0 + i * dur / n for i in range(n)]
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.2, 0.3)
            if w <= 0: return
            g = 0.0
            for s in starts:
                g = max(g, ease_out_cubic(prog(t, s, s + 0.06)) * (1 - ease_in_out(prog(t, s + 0.42, s + 0.5))))
                b = t - (s + 0.5)
                if 0 <= b < 0.067: P.blink = max(P.blink, clamp(min(1.0, b / 0.017, (0.067 - b) / 0.017)))
            head = 0.0
            for s in starts:
                head = max(head, ease_in_out(prog(t, s + 0.08, s + 0.3)) * (1 - ease_in_out(prog(t, s + 0.45, s + 0.7))))
            P.lock = lerp(P.lock, 0.0, w)
            P.look_x = lerp(P.look_x, 0.85 * side, g); P.look_y = lerp(P.look_y, 0.05, g)
            P.h_turn += 0.16 * side * head
            P.mix(dict(brow_sad=0.6, m_press=0.5, pupil=0.85), w * 0.8)
        return self._add(t0 - 0.2, t0 + dur + 0.5, fn)

    def twitch(self, times, amp=1.0):
        times = [times] if isinstance(times, (int, float)) else list(times)
        dirs = [(1 if hash01(i, self.seed + 61) > 0.5 else -1, hash01(i, self.seed + 62) * 2 - 1) for i in range(len(times))]
        def fn(P, t):
            for (ti, (d1, d2)) in zip(times, dirs):
                tau = t - ti
                if 0 <= tau < 0.6:
                    f = math.exp(-tau * 9.0) * math.sin(tau * 46.0)
                    P.h_tilt += 11.0 * amp * f * d1
                    P.h_dx += 7.0 * amp * f * d2
                    P.shrug += 0.3 * amp * abs(f)
                    P.look_x += 0.25 * f * d2
                    P.brow_asym += 0.7 * f * d1
                    P.m_side += 0.7 * f * d1
                    P.blink = max(P.blink, clamp(1.0 - tau / 0.07) if tau < 0.07 else 0.0)
        return self._add(min(times) - 0.1, max(times) + 0.7, fn, real=True)

    def freeze(self, t0, t1):
        """Total stillness: every non-realtime clip, breathing and noise hold their t0 values until t1."""
        self.freezes.append((t0, t1))
        return self._add(t0, t1, lambda P, t: setattr(P, 'still', 1.0) if t0 <= P.t <= t1 else None, real=True)

    def jerk(self, t, amp=1.0):
        self.twitch([t], 1.8 * amp)
        def fn(P, tt):
            tau = tt - t
            if 0 <= tau < 0.8:
                k = math.exp(-tau * 7.0)
                P.h_nod += -0.12 * k * amp; P.wide += 0.5 * k; P.pupil *= 1 - 0.35 * k
        return self._add(t - 0.1, t + 0.9, fn, real=True)

    def blink(self, t, dur=0.067):
        """Forced blink: shut in 17 ms, held, open by t + dur (1-2 frames at 30 fps)."""
        def fn(P, tt):
            d = tt - t
            if 0 <= d <= dur:
                e = min(1.0, d / 0.017, (dur - d) / 0.017)
                P.blink = max(P.blink, clamp(e))
        return self._add(t - 0.05, t + dur + 0.05, fn, real=True)

    def blink_burst(self, t0, n=4, dur=1.0):
        """Nervous burst: n quick blinks inside dur seconds (hotel reference: 4 blinks in 1 s)."""
        for i in range(n): self.blink(t0 + i * dur / max(1, n))
        return self

    def life(self, t0, t1=None, amount=0.0, fade=0.3):
        """Scale the v2.1 idle life (drift, re-settles, weight shifts, micro twitches, shiver) over a window."""
        return self.set(t0, t1, fade, life=amount)

    # ------------------------------------------------------------------ speech
    def talk(self, intervals, text=None, intensity=1.0, env='auto', words='auto', lead=0.02):
        """Mouth shapes for speech. intervals: [(t0, t1)] or [(t0, t1, text)]; text applies to a single interval.
        v2.1: the mouth opening follows the real voice: env='auto' samples the vo_en.wav RMS envelope (shut below
        -40 dBFS, opening rising with the level, normalised per line); words='auto' places each word's visemes inside its
        own ASR window (asr_cache en_words), so shapes land on the right syllables. env=None / words=None fall back to
        evenly spread syllables. During a grin the jaw drops on top of the grin (talks through the teeth); during
        shout/scream (m_open >= 0.5) the opening modulates around the base."""
        intensity = intensity * self.sp.get('talk', 1.0)
        E = voice_envelope() if (isinstance(env, str) and env == 'auto') else env
        W = voice_words() if (isinstance(words, str) and words == 'auto') else (words or [])
        wt = [w_[1] for w_ in W]
        keys, ivs = [], []
        for k, iv in enumerate(intervals):
            t0, t1 = float(iv[0]), float(iv[1])
            txt = iv[2] if len(iv) > 2 else (text if len(intervals) == 1 else None)
            segs = []
            if W:
                j0 = _bisect.bisect_left(wt, t0 - 0.08); j1 = _bisect.bisect_left(wt, t1 - 0.03)
                for j in range(j0, j1):
                    ws = W[j][1]; we = min(W[j + 1][1] if j + 1 < len(W) else t1, t1, ws + 0.85)
                    if we - ws > 0.04: segs.append((W[j][0], ws, we))
            keys.extend(self._visemes_timed(segs, k) if segs else self._visemes(t0, t1, txt, k))
            ref = None
            if E is not None and not callable(E):
                seg = E[max(0, int(t0 * ENV_FPS)):max(0, int(t1 * ENV_FPS))]
                if len(seg) > 3: ref = max(float(np.percentile(seg, 95)), -30.0)
            elif E is not None:
                ref = max(max(_env_db(E, t0 + (t1 - t0) * q / 12.0) for q in range(13)), -30.0)
            ivs.append((t0, t1, ref))
        keys.sort(key=lambda k_: k_[0])
        kt = [k_[0] for k_ in keys]
        ivs.sort(key=lambda v: v[0])
        it0 = [v[0] for v in ivs]
        lo = min((float(iv[0]) for iv in intervals), default=0.0); hi = max((float(iv[1]) for iv in intervals), default=0.0)
        FLOOR = -40.0

        def fn(P, t):
            if not keys or t < kt[0] - 0.1 or t > kt[-1] + 0.2: return
            i = _bisect.bisect_right(kt, t) - 1
            if i < 0: a = b = keys[0]; u = 0.0
            elif i >= len(keys) - 1: a = b = keys[-1]; u = 0.0
            else:
                a, b = keys[i], keys[i + 1]
                u = ease((t - a[0]) / max(1e-3, b[0] - a[0]))
            ov = lerp(a[1], b[1], u); wd = lerp(a[2], b[2], u); rd = lerp(a[3], b[3], u)
            te = lerp(a[4], b[4], u); pr = lerp(a[5], b[5], u); acc = lerp(a[6], b[6], u)
            j = max(0, _bisect.bisect_right(it0, t + 0.06) - 1)
            t0_, t1_, ref = ivs[j]
            if ref is not None:
                gate = _env(t, t0_ - 0.06, t1_ + 0.02, 0.05, 0.12)
                if gate <= 0: on = 0.0
                else:
                    db = _env_db(E, t + lead)
                    on = clamp((db - FLOOR) / max(6.0, ref - FLOOR)) ** 1.35 * gate
                vf = clamp(ov / 0.6)
                o = on * (0.55 + 0.45 * vf) * 0.68 * intensity
                acc = max(acc * 0.5, clamp((on - 0.78) * 4.0))
                pr *= 1.0 - clamp(on * 3.0)
            else:
                o = ov * intensity; on = clamp(ov / 0.6)
            base = P.m_open; g = clamp(P.grin)
            if base >= 0.5:                                           # shout / scream: modulate around the base
                P.m_open = clamp(base - 0.27 * intensity * (1.0 - on) * (1.0 if ref is not None else 0.6), 0.0, 1.0)
            else:
                P.m_open = base + 0.34 * on * intensity * g + max(0.0, o - base) * (1.0 - g)
            kk = 1.0 - 0.6 * g
            P.m_round = lerp(P.m_round, rd, 0.85 * (1.0 - 0.7 * g))
            P.m_wide += wd * 0.6 * kk
            P.teeth = max(P.teeth, te * 0.8)
            P.m_press = max(P.m_press, pr)
            P.h_nod += 0.035 * acc; P.brow_up += 0.12 * acc
        return self._add(lo - 0.2, hi + 0.3, fn)

    def talk_lines(self, lines, who='O', intensity=1.0):
        """Talk on every timeline.json line spoken by `who` (uses each line's t, end and en text)."""
        iv = [(l['t'], l['end'], l.get('en')) for l in lines if l.get('who') == who and l.get('end')]
        return self.talk(iv, intensity=intensity) if iv else self

    def _visemes_timed(self, segs, k):
        """Viseme keys from [(word, t_start, t_end)]: each word's syllables share its own window."""
        R = VISEMES['rest']
        keys = [(segs[0][1] - 0.06,) + R + (0.0,)]
        for wi, (wd, ws, we) in enumerate(segs):
            syl = _syllables(_re.sub(r"[^A-Za-z']", '', wd) or 'a')
            sl = []
            for si, (on, vo) in enumerate(syl):
                sl.append([1.0 + (0.35 if len(vo) > 1 else 0.0), _onset_vis(on), _vowel_vis(vo), 1.0 if (si == 0 and len(syl) > 1) else 0.0])
            tot = sum(x[0] for x in sl) or 1.0
            dur = max(0.05, we - ws - 0.02)
            tt = ws
            for i, (wgt, on, vo, st) in enumerate(sl):
                d = wgt * dur / tot
                amp = (0.8 + 0.3 * hash01(i + 7 * wi + 31 * k, self.seed + 3)) * (1.1 if st else 1.0)
                if on:
                    v = VISEMES[on]; keys.append((tt + 0.1 * d, v[0], v[1], v[2], v[3], v[4], st))
                v = VISEMES[vo]
                keys.append((tt + (0.45 if on else 0.3) * d, v[0] * amp, v[1], v[2], v[3], v[4], st))
                tt += d
            nxt = segs[wi + 1][1] if wi + 1 < len(segs) else None
            if nxt is None or nxt - we > 0.12:
                keys.append((min(we, ws + dur) + 0.02, R[0] + 0.05, R[1], R[2], R[3], 0.2, 0.0))
        keys.append((segs[-1][2] + 0.06,) + R + (0.0,))
        return keys

    def _visemes(self, t0, t1, txt, k):
        dur = max(0.05, t1 - t0)
        sl = []        # (weight, onset vis, vowel vis, stress, word_end)
        if txt:
            words = _re.findall(r"[A-Za-z']+", txt)
            for wi, wd in enumerate(words):
                syl = _syllables(wd)
                for si, (on, vo) in enumerate(syl):
                    wgt = 1.0 + (0.35 if len(vo) > 1 else 0.0)
                    sl.append([wgt, _onset_vis(on), _vowel_vis(vo), 1.0 if (si == 0 and len(syl) > 1) else 0.0, si == len(syl) - 1])
                if sl: sl[-1][0] += 0.3
        else:
            n = max(1, int(dur * 5.2))
            vs = ['A', 'E', 'O', 'I', 'U', 'A', 'E']
            for i in range(n):
                h = hash01(i + 97 * k, self.seed + 13)
                on = 'M' if hash01(i, self.seed + 14) < 0.18 else ('F' if hash01(i, self.seed + 15) < 0.1 else None)
                sl.append([1.0 + 0.4 * hash01(i, 5), on, vs[int(h * len(vs)) % len(vs)], 1.0 if hash01(i, 6) > 0.8 else 0.0,
                           hash01(i, 7) > 0.65])
        if not sl: return []
        tot = sum(s[0] for s in sl)
        a0 = t0 + 0.03; scale = (dur - 0.08) / tot
        keys = [(t0 - 0.06,) + VISEMES['rest'] + (0.0,)]
        tt = a0
        for i, (wgt, on, vo, st, wend) in enumerate(sl):
            d = wgt * scale
            amp = (0.78 + 0.32 * hash01(i + 11 * k, self.seed + 3)) * (1.12 if st else 1.0)
            if on:
                v = VISEMES[on]; keys.append((tt + 0.08 * d, v[0], v[1], v[2], v[3], v[4], st))
            v = VISEMES[vo]
            keys.append((tt + (0.42 if on else 0.3) * d, v[0] * amp, v[1], v[2], v[3], v[4], st))
            if wend:
                r = VISEMES['rest']; keys.append((tt + 0.92 * d, r[0] + 0.05, r[1], r[2], r[3], 0.2, 0.0))
            tt += d
        keys.append((t1 + 0.05,) + VISEMES['rest'] + (0.0,))
        return keys


# ====================================================================================================== HUD phone hand
def hud_phone_hand(pen, w, h, skin='#c9aa98', a=255, front=False, sleeve='#34443f'):
    """Drop-in for engine.hud._hand(pen, w, h, skin, a, front): a hand holding the phone in phone coords (the phone spans
    -w/2..w/2, -h/2..h/2). front=False draws the palm, wrist and hoodie cuff behind the phone; front=True the four
    fingertips wrapping the right edge and the thumb over the left edge. Install: hud._hand = characters.hud_phone_hand."""
    sh = mix(skin, '#6b5148', 0.42); dp = mix(skin, '#3a2a2a', 0.55); nail = mix(skin, '#ffffff', 0.35)
    lw = 7.0; k = a / 255.0
    c = Ctx(pen, skia.Matrix(), lw)
    if not front:
        palm = smooth([(-w * 0.64, h * 0.06), (-w * 0.6, h * 0.5), (-w * 0.24, h * 0.8), (w * 0.34, h * 0.78), (w * 0.62, h * 0.44),
                       (w * 0.66, h * 0.06), (w * 0.36, -h * 0.04), (-w * 0.36, -h * 0.03)], True, 0.8)
        wrist = poly([(-w * 0.31, h * 0.6), (w * 0.33, h * 0.6), (w * 0.42, h * 1.3), (-w * 0.38, h * 1.3)])
        body = union(palm, wrist)
        c.fill(body, skin, a); c.fill(_crescent(body, -w * 0.07, -h * 0.02), sh, 150 * k); c.line(body, lw, LINE, a)
        c.line(smooth([(-w * 0.42, h * 0.46), (-w * 0.2, h * 0.6), (w * 0.05, h * 0.62)], False), lw * 0.45, dp, 160 * k)
        cuff = rrect(-w * 0.5, h * 0.92, w * 1.02, h * 0.5, 36)
        c.fill(cuff, sleeve, a); c.fill(_crescent(cuff, -w * 0.08, 0), mix(sleeve, '#000000', 0.35), 160 * k); c.line(cuff, lw, LINE, a)
        c.line(_multi([poly([(-w * 0.4 + i * w * 0.1, h * 0.95), (-w * 0.4 + i * w * 0.1, h * 1.05)], False) for i in range(9)]),
               lw * 0.4, LINE, 150 * k)
        return
    # v2.1: four real fingertips curl round the right edge (staggered, tapering, nails out, a crease where they bend
    # over the edge); the thumb comes round the left edge with its nail showing
    for i in (3, 2, 1, 0):
        fy = -h * 0.07 + i * h * 0.112
        fw = h * (0.084 - 0.007 * i)
        tipx = w * (0.355 + 0.02 * i + (0.025 if i == 0 else 0.0))
        pts = [(w * 0.565, fy + h * 0.03), (w * 0.505, fy + h * 0.01), (tipx, fy)]
        f = _tube(pts, [fw * 0.98, fw * 0.95, fw * 0.82], 0.9)
        c.fill(f, skin, a); c.fill(_crescent(f, 0, -h * 0.02), sh, 140 * k); c.line(f, lw * 0.85, LINE, a)
        c.line(smooth([(w * 0.5, fy - fw * 0.36), (w * 0.485, fy), (w * 0.5, fy + fw * 0.36)], False), lw * 0.35, dp, 170 * k)
        nl = rrect(tipx - fw * 0.02, fy - fw * 0.3, fw * 0.62, fw * 0.6, fw * 0.28)
        c.fill(nl, nail, 230 * k); c.line(nl, lw * 0.3, dp, 190 * k)
    tp = [(-w * 0.7, h * 0.46), (-w * 0.56, h * 0.27), (-w * 0.4, h * 0.15)]
    th = _tube(tp, [w * 0.2, w * 0.165, w * 0.13], 0.9)
    c.fill(th, skin, a); c.fill(_crescent(th, w * 0.03, -h * 0.02), sh, 140 * k); c.line(th, lw * 0.85, LINE, a)
    c.line(smooth([(-w * 0.62, h * 0.24), (-w * 0.56, h * 0.29), (-w * 0.5, h * 0.27)], False), lw * 0.35, dp, 170 * k)
    nl = rrect(-w * 0.44, h * 0.13, w * 0.07, h * 0.045, w * 0.03)
    c.fill(nl, nail, 230 * k); c.line(nl, lw * 0.3, dp, 190 * k)


# ====================================================================================================== self-test
def _selftest():
    """python3 characters.py --selftest : acting regressions for the v2.1 fixes (prints and asserts)."""
    out = []
    # snap_turn overrides a held look-aside (critic: yaw must be < 0.05 at snap + 0.5 s), in either clip order
    for order in (0, 1):
        a = Acting('officer', seed=3); a.stare(-3)
        look = lambda: a.set(-2.0, None, 0.45, h_turn=0.9, lock=0.0, look_x=0.6)
        if order == 0: look(); a.snap_turn(0.15, 0.9, 0.0)
        else: a.snap_turn(0.15, 0.9, 0.0); look()
        P = a.at(0.65); yaw = P.turn + P.h_turn
        assert abs(yaw) < 0.05, ('snap_turn', order, yaw)
        P0 = a.at(-0.3); assert abs(P0.turn + P0.h_turn - 0.9) < 0.12, ('pre-snap yaw', P0.turn + P0.h_turn)
        out.append('snap order %d: yaw %.3f at snap+0.5 s, %.2f before' % (order, yaw, P0.turn + P0.h_turn))
    # blinks: shut (>0.5) for at most 2 frames at 30 fps
    a = Acting('you', seed=1)
    ts = np.arange(0, 40, 1 / 240.0); b = np.array([a._blink_amt(t) for t in ts]) > 0.5
    runs, r = [], 0
    for v in b:
        if v: r += 1
        elif r: runs.append(r); r = 0
    assert runs and max(runs) / 240.0 <= 0.067, ('blink', max(runs) / 240.0)
    out.append('blinks: %d, longest shut %.0f ms' % (len(runs), 1000 * max(runs) / 240.0))
    # phone at the ear: wrist ends up near the ear, not past the shoulder (no spike)
    for who in ('mum', 'you', 'officer'):
        a = Acting(who, seed=2); a.phone_to_ear(0.0, None, side=1)
        P = a.at(1.0); B = Body(CAST[who], P)
        S, E, W = _arm_data(CAST[who], B, P, 1)
        ear_y = B.yc - CAST[who]['hh'] / 2
        assert W[1] < B.y_sh and abs(W[1] - ear_y) < 0.6 * CAST[who]['hh'], ('phone_to_ear', who, W, ear_y)
        out.append('phone_to_ear %s: wrist %.0f above the shoulder, %.0f below the ear' % (who, B.y_sh - W[1], W[1] - ear_y))
    # lip sync follows the voice envelope (when the narration is available)
    env = voice_envelope()
    if env is not None:
        a = Acting('officer', seed=1); a.talk([(42.42, 46.5, None)])
        ts = np.arange(42.3, 46.6, 1 / 30.0)
        mo = np.array([a.at(t).m_open for t in ts]); ev = np.array([10 ** (_env_db(env, t) / 20.0) for t in ts])
        r = float(np.corrcoef(mo, ev)[0, 1])
        assert r > 0.5, ('lip sync', r)
        out.append('lip sync r = %.2f (line 12)' % r)
    for o in out: print(o)
    print('characters self-test ok')


if __name__ == '__main__' and '--selftest' in sys.argv:
    _selftest()
