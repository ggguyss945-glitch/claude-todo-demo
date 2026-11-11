"""characters.py: the cast, their creepy faces and an acting timeline. Shared by "If A Police Officer Knocks..." v2 and
the Mirror Steps film ("If An Eighth Step Appears On Your Mirror...").

MIRROR STEPS (read CAST.md): new cast 'you' (the lead; the police lead is now 'you_police'), 'tess', 'noah13',
'noah_grown' (age morph), 'queen' (v2, DIRECTION_V2 3: a playing-card queen in the cast language, stages S0-S4 as q_*
pose numbers, drawn by the queen_* functions), 'you_kid', 'tess_kid', 'counselor',
'kid_a/b/c', 'director', 'cook', 'searcher', 'adult'; modes draw_hands / draw_feet / draw_legs / draw_silhouette /
draw_lying; light presets LIGHTS (flashlight, moon, dawn, red); ~115 new Acting clips; CharRig(spec, shot) builds a
plan/shots.json character (acts, stage, props, clip_id replays) and draws it. Voice: _work/align/vo_en.wav.

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


def smoothstep(x):
    x = 0.0 if x <= 0 else (1.0 if x >= 1 else x)
    return x * x * (3.0 - 2.0 * x)

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
    'you_police': dict(                                 # the police film's 'you' (renamed: 'you' is the Mirror Steps lead)
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

# ------------------------------------------------------------------------------------------- Mirror Steps cast
_HYS = [-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120]
CAST.update({
    'you': dict(                                    # 27, looks like their dad: squarer jaw, stubble, receding temples
        outfit='jacket', hat=None, hair='short_r', sex='m', hh=176.0, new=True,
        head_ys=_HYS, head_ws=[0, 50, 73, 89, 94, 93, 89, 80, 63, 35, 0],
        eye_dx=42, eye_y=-10, eye_r=18.5, eye_h=0.74, pupil=1.0, iris_h='#5b3b28', fear_eyes=0.14, brow_th=10.5,
        nose_len=25, mouth_y=53, mouth_w=23,
        skin='#c9aa98', skin_sh='#97786c', skin_dp='#634c4b', blush='#d39488', lip='#a2706a', stubble='#4a3c33', stub=0.6,
        stub_dots=1.0, forehead=0.35, hair_c='#382821', brow_c='#2a1f1a', bags=0.6, age=0.45, blink_rate=0.33, lock=0.0,
        micro=1.0, breath=1.0, scar=0, ring=0, part=1, lashes=0.0, talk=0.95,
        body=dict(sh=122, ch=118, wa=108, hip=106, arm=(55, 46), leg=(60, 50), neck=47, hand=1.0),
        cloth=dict(top='#4a5038', top_sh='#33382a', top_hi='#626a4c', collar='#6b5a3e', collar_sh='#4d3f2a',
                   shirt='#7d8287', shirt_sh='#5d6166', trousers='#2a3347', trousers_sh='#1a2030', shoes='#4a3426',
                   shoes_sh='#2e2018', button='#2a2c22')),
    'tess': dict(                                   # practical and brave: auburn low ponytail, freckles, orange shell
        outfit='shell', hat=None, hair='pony', sex='f', hh=178.0, new=True,
        head_ys=_HYS, head_ws=[0, 48, 70, 85, 89, 87, 80, 65, 45, 23, 0],
        eye_dx=41, eye_y=-8, eye_r=18.5, eye_h=0.78, pupil=1.0, iris_h='#5d6b3c', fear_eyes=0.14, brow_th=9.5,
        brow_level=0.6, nose_len=21, mouth_y=52, mouth_w=19,
        skin='#d7b6a3', skin_sh='#a8836f', skin_dp='#6e4f4a', blush='#e09a8c', lip='#b4686a', stubble=None, stub=0, lips=0.6,
        freckles='#b9785c', hair_c='#7a4128', brow_c='#4a2617', bags=0.35, age=0.2, blink_rate=0.36, lock=0.0, micro=1.0,
        breath=1.0, scar=0, ring=0, part=0, lashes=1.3, talk=0.85,
        body=dict(sh=110, ch=106, wa=92, hip=104, arm=(47, 38), leg=(56, 46), neck=40, hand=0.9),
        cloth=dict(top='#9a4a2e', top_sh='#6e321e', top_hi='#b8603e', zip='#2a2422', trousers='#3b3f45',
                   trousers_sh='#282b30', shoes='#3a2c22', shoes_sh='#251c16', lace='#b8a88a')),
    'noah13': dict(                                 # 13 forever: cowlick, freckles, gap teeth, green sweatshirt, one shoe
        outfit='sweatshirt', hat=None, hair='mop', sex='m', hh=182.0, new=True, kid=True,
        head_ys=_HYS, head_ws=[0, 54, 79, 96, 101, 100, 92, 77, 55, 29, 0],
        eye_dx=42, eye_y=-4, eye_r=20.0, eye_h=0.74, pupil=1.0, iris_h='#6a4228', iris_k=0.7, fear_eyes=0.12, brow_th=8.0,
        nose_len=17, mouth_y=52, mouth_w=19, gap=6.0, tooth_w=12.0,
        skin='#d2b3a0', skin_sh='#a3826f', skin_dp='#6e5048', blush='#e39e8d', lip='#b97a72', stubble=None, stub=0,
        freckles='#b07a62', hair_c='#4a3226', brow_c='#3a271c', bags=0.2, age=0.0, blink_rate=0.3, lock=0.0, micro=0.8,
        breath=1.0, scar=0, ring=0, part=1, lashes=0.0, talk=0.9, tape=-1,
        body=dict(sh=102, ch=98, wa=92, hip=92, arm=(44, 36), leg=(50, 41), neck=35, hand=0.88),
        cloth=dict(top='#3f6b45', top_sh='#2b4c31', top_hi='#57875c', print='#dcd9cc', trousers='#4c5a72',
                   trousers_sh='#3a465c', plaid='#3a465c', plaid2='#66748c', shoes='#e3ded2', shoes_sh='#b0aa9c',
                   lace='#f2efe6', sole='#cfc8b8', fit=0.0, bare='R')),
    'noah_grown': dict(                             # the same face at 27: longer jaw, stubble, the gap stays; shirt too small
        outfit='sweatshirt', hat=None, hair='mop', sex='m', hh=172.0, new=True,
        head_ys=_HYS, head_ws=[0, 46, 67, 82, 85, 84, 82, 77, 64, 40, 0],
        eye_dx=42, eye_y=-13, eye_r=18.5, eye_h=0.74, pupil=1.0, iris_h='#5e3a22', iris_k=0.7, fear_eyes=0.0, fear_wide=0.35,
        brow_th=11.5, nose_len=26, mouth_y=57, mouth_w=23, gap=6.0, tooth_w=12.5,
        skin='#cdae9b', skin_sh='#9a7b6c', skin_dp='#644a47', blush='#d99586', lip='#ac746d', stubble='#3e3028', stub=0.85,
        stub_dots=1.0, freckles='#a87a64', freckle_k=0.3, hair_c='#45301f', brow_c='#2e1f15', bags=0.75, age=0.7, forehead=0.3,
        blink_rate=0.34, lock=0.0, micro=1.0, breath=1.0, scar=0, ring=0, part=1, lashes=0.0, talk=0.95, tape=0,
        body=dict(sh=132, ch=128, wa=114, hip=110, arm=(58, 49), leg=(62, 52), neck=51, hand=1.25),
        cloth=dict(top='#3f6b45', top_sh='#2b4c31', top_hi='#57875c', print='#dcd9cc', trousers='#4c5a72',
                   trousers_sh='#3a465c', plaid='#3a465c', plaid2='#66748c', shoes='#e3ded2', shoes_sh='#b0aa9c',
                   lace='#f2efe6', sole='#cfc8b8', fit=1.0, bare='LR', jacket='#4a5038', jacket_sh='#33382a',
                   collar='#6b5a3e')),
    'queen': dict(                                  # the Queen of Spades v2 (DIRECTION_V2 §3): drawn by queen_* (Queen v2 section)
        outfit='dress', hat=None, hair='long', sex='f', hh=133.0, new=True, entity=True, v2=True,
        head_ys=_HYS, head_ws=[0, 38, 58, 76, 84, 87, 77, 57, 35, 16, 0],
        eye_dx=34.8, eye_y=-10, eye_r=7.8, eye_h=0.53, pupil=0.46, iris_h='#3b3346', brow_th=3.2, nose_len=18, mouth_y=62,
        mouth_w=26, grin_w=34.0, tooth_w=7.0, teeth_max=14, lips=1.0, lip='#c63449', lip_glow='#ff4060',
        skin='#ece6e8', skin_sh='#c3b8c9', skin_dp='#9a8aa4', blush='#ece6e8', blush_k=0.0, stubble=None, stub=0,
        hair_c='#0d0b14', brow_c='#0b0910', bags=0.0, sockets=0.0, age=0.3, blink_rate=0.0, lock=1.0, micro=0.0,
        breath=0.0, scar=0, ring=0, part=0, lashes=1.0, talk=0.8,
        body=dict(sh=88, ch=72, wa=50, hip=66, arm=(34, 21), leg=(48, 38), neck=17.5, hand=1.0, fingers=1.35, neck_extra=11),
        cloth=dict(top='#0f0d16', top_sh='#07060b', top_hi='#2a2638', sheen='#2a2638', scratch='#d9dee6',
                   trousers='#0f0d16', trousers_sh='#07060b', shoes=None, toe='#121018')),
    'you_kid': dict(                                # you at 10-11: big eyes, striped tee, shorts, sneakers
        outfit='tee', hat=None, hair='mop', sex='m', hh=196.0, new=True, kid=True,
        head_ys=_HYS, head_ws=[0, 55, 80, 97, 102, 101, 92, 76, 53, 27, 0],
        eye_dx=42, eye_y=-2, eye_r=21.5, eye_h=0.9, pupil=1.0, iris_h='#5b3b28', fear_eyes=0.12, brow_th=8.0,
        nose_len=15, mouth_y=52, mouth_w=18,
        skin='#d6b7a4', skin_sh='#a88673', skin_dp='#6e5048', blush='#e8a294', lip='#bd7f76', stubble=None, stub=0,
        hair_c='#382821', brow_c='#2d211c', bags=0.0, age=0.0, blink_rate=0.35, lock=0.0, micro=1.0, breath=1.0,
        scar=0, ring=0, part=-1, lashes=0.0, talk=0.9,
        body=dict(sh=94, ch=90, wa=86, hip=86, arm=(40, 33), leg=(46, 38), neck=33, hand=0.86),
        cloth=dict(top='#5a7fa8', top_sh='#3f5e82', top_hi='#7698c0', stripe='#e8e4da', trousers='#5c5a4e',
                   trousers_sh='#43413a', shoes='#d9d4c8', shoes_sh='#a8a296', legs='#d6b7a4', shorts=True)),
    'counselor': dict(                              # memory extra: teen camp staff, teal tee, whistle lanyard
        outfit='tee', hat=None, hair='short', sex='m', hh=180.0, new=True,
        head_ys=_HYS, head_ws=[0, 51, 75, 92, 97, 96, 88, 72, 50, 26, 0],
        eye_dx=42, eye_y=-6, eye_r=19.0, eye_h=0.82, pupil=1.0, iris_h='#4a3424', fear_eyes=0.12, brow_th=8.5,
        nose_len=20, mouth_y=52, mouth_w=20,
        skin='#c7a28c', skin_sh='#977462', skin_dp='#5e4440', blush='#d8927f', lip='#a86d63', stubble=None, stub=0,
        hair_c='#2b2420', brow_c='#241c18', bags=0.2, age=0.1, blink_rate=0.33, lock=0.0, micro=1.0, breath=1.0,
        scar=0, ring=0, part=1, lashes=0.0, lanyard=True,
        body=dict(sh=112, ch=108, wa=98, hip=98, arm=(48, 40), leg=(54, 44), neck=42, hand=0.95),
        cloth=dict(top='#3f7f86', top_sh='#2c5c61', top_hi='#58a0a6', stripe=None, trousers='#6b6450',
                   trousers_sh='#4d4838', shoes='#2a2a2c', shoes_sh='#151516', legs='#c7a28c', shorts=True)),
})
for _k, _v in (('kid_a', ('#b04a3a', '#7a3024', '#c8644e', '#c49a7c', '#6a4a30')), ('kid_b', ('#e0b040', '#a88020', '#f0c860', '#a87e62', '#2a1e18')),
               ('kid_c', ('#4a7a5a', '#31573e', '#62967a', '#d8b8a2', '#8a6a3a'))):
    _d = dict(CAST['you_kid']); _d['cloth'] = dict(_d['cloth'], top=_v[0], top_sh=_v[1], top_hi=_v[2], stripe=None, legs=_v[3])
    _d['skin'] = _v[3]; _d['hair_c'] = _v[4]; _d['part'] = 1 if _k == 'kid_b' else -1
    CAST[_k] = _d
for _k, _top, _hat in (('director', '#5d6a50', 'camp'), ('cook', '#e9e6df', None), ('searcher', '#3b4048', None), ('adult', '#4b5563', None)):
    _d = dict(CAST['counselor']); _d['cloth'] = dict(_d['cloth'], top=_top, top_sh=mix(_top, '#000000', 0.28), top_hi=mix(_top, '#ffffff', 0.18),
                                                      shorts=False, trousers='#2f3440', trousers_sh='#1f232c')
    _d['lanyard'] = False; _d['apron'] = _k == 'cook'; _d['camp_cap'] = _hat == 'camp'; _d['kid'] = False
    CAST[_k] = _d
_d = dict(CAST['you_kid']); _d['cloth'] = dict(_d['cloth'], top='#c0662e', top_sh='#8a4520', top_hi='#d88050', stripe=None)
_d.update(hair='pony', sex='f', hair_c='#7a4128', brow_c='#4a2617', freckles='#b9785c', lashes=1.2, part=0, skin='#dcbca8')
CAST['tess_kid'] = _d                                  # memory: Tess at 10 (the barefoot run, 458.8 s)
NEW_CAST = ('you', 'tess', 'noah13', 'noah_grown', 'queen', 'you_kid', 'tess_kid', 'counselor', 'kid_a', 'kid_b', 'kid_c', 'director',
            'cook', 'searcher', 'adult')

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
    # Mirror Steps: queen lipstick smear, Noah's age morph (body / face 0..1) and grown-face flash, hand shake, tape
    # (1 on the fingers, slip 0..1 = the fingers slide out of the ring), hair over the queen's face, leg/foot offsets
    # (body units: lift, fwd, out; point = toe angle; toes = curl), lying, kneel, jacket on noah_grown, insert hands
    smear=0.0, age_body=1.0, age_face=1.0, face_flash=0.0, hshake=0.0, tape=1.0, tape_slip=0.0, tape_peel=0.0,
    hair_over=0.0, eye_gap=0.0, fl_up=0.0, fl_fwd=0.0, fl_out=0.0, fr_up=0.0, fr_fwd=0.0, fr_out=0.0, fl_point=0.0,
    fr_point=0.0, toes=0.0, kneel=0.0, jacket_on=0.0, collar_pull=0.0, cuff_up=0.0, sleep=0.0, candy=0.0, glow=1.0,
    # hands inserts (mode 'hands'): per hand offset (units of the insert size), angle (deg, 180 = fingers up),
    # visibility 0..1 (slides in along the arm), press on glass, finger curl
    ir_x=0.0, ir_y=0.0, ir_a=180.0, ir_v=1.0, ir_press=0.0, ir_curl=0.0, il_x=-0.55, il_y=0.1, il_a=180.0, il_v=0.0,
    il_press=0.0, il_curl=0.0, ins_k=1.0, lace=0.0, wipe=0.0, m_gap=0.0, hem=0.0, ft_l=1.0, ft_r=1.0, beam=0.0, beam_dx=0.0,
    frame_tilt=0.0, palm_open=0.0, jacket_off=0.0, ft_hem=1.0,
    # Queen v2 stages (QSTAGES): hide (S0 hair over the face), draw (the lipstick stair smile), split (S3a grin of
    # teeth), red (S3b eyes), full (S3c folds, cracks, tears), off (the smile goes off), void (S4 jaw void), pin
    # (pinpoint pupils), noah (his face in the void), glitch; q_hair = lagged hair yaw (turn units) when q_hair_set
    q_hide=0.0, q_draw=0.0, q_split=0.0, q_red=0.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=0.0, q_noah=1.0, q_glitch=0.0,
    q_hair=0.0, q_hair_set=0.0, wrapper=0.0, run=0.0, ir_fore=0.0, q_widen=0.0, q_nface=0.0, alpha=1.0,
)
POSE_DISCRETE = dict(hl_shape='mitt', hr_shape='mitt', hl_prop=None, hr_prop=None, ir_shape='relaxed', il_shape='relaxed',
                     ir_prop=None, il_prop=None, base_prop=None)


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
    # ---------------------------------------------------------------- Mirror Steps (people read as real and grieving)
    'grief': dict(brow_sad=0.95, brow_up=0.12, smile=-0.38, eye_open=0.74, wet=0.9, h_nod=0.1, m_press=0.25, tremble=0.18,
                  blush=0.35),
    'dread': dict(brow_sad=0.6, brow_up=0.4, wide=0.4, pupil=0.62, m_press=0.45, smile=-0.32, sweat=0.35, tremble=0.3),
    'tense': dict(brow_angry=0.35, brow_sad=0.3, squint=0.15, m_press=0.6, smile=-0.22, pupil=0.82),
    'tempted': dict(eye_open=0.6, look_y=0.38, brow_sad=0.5, smile=0.2, m_open=0.05, wet=0.65, h_nod=0.12, blush=0.3),
    'resolve': dict(brow_angry=0.6, brow_sad=0.12, squint=0.22, m_press=0.7, smile=-0.18, pupil=0.85, h_nod=0.05),
    'wonder': dict(brow_up=0.6, wide=0.18, m_open=0.15, m_round=0.45, pupil=1.1, wet=0.35),
    'relief_cry': dict(tears=0.9, smile=0.42, teeth=0.3, brow_sad=0.85, wet=1.0, squint=0.28, m_open=0.12, blush=0.6, tremble=0.3),
    'brave': dict(brow_angry=0.22, m_press=0.38, squint=0.1, smile=0.04, pupil=0.92),
    'recognise': dict(brow_up=0.45, wide=0.15, smile=0.22, m_open=0.08, pupil=1.0),
    'half_smile': dict(smile=0.42, m_side=0.55, brow_up=0.12, squint=0.12, brow_asym=0.25),
    'puzzled': dict(brow_asym=0.85, brow_angry=0.25, squint=0.2, m_side=-0.5, smile=-0.06, h_tilt=6.0),
    'calm_kid': dict(smile=0.1, eye_open=0.86, brow_up=0.04, pupil=1.0, m_press=0.1),
    'grin_kid': dict(smile=0.8, teeth=0.9, m_open=0.12, squint=0.28, brow_up=0.22, blush=0.5),
    'laugh': dict(smile=0.9, teeth=0.9, m_open=0.34, squint=0.55, brow_up=0.32, blush=0.7),
    'listening': dict(brow_up=0.28, look_y=-0.22, m_open=0.04, pupil=1.0, h_tilt=5.0),
    'relief': dict(smile=0.5, teeth=0.4, brow_sad=0.42, wet=0.7, eye_open=0.86, blush=0.4),
    'shy': dict(smile=0.32, look_y=0.42, look_x=-0.3, eye_open=0.78, blush=0.7, h_nod=0.1),
    'sleep': dict(eye_open=0.0, m_open=0.05, smile=0.0, h_nod=0.04, sleep=1.0),
    'strain': dict(brow_angry=0.6, brow_sad=0.5, squint=0.55, teeth=0.9, m_wide=0.6, m_open=0.12, smile=-0.3, tremble=0.55),
    'worried': dict(brow_sad=0.72, brow_up=0.22, smile=-0.26, m_press=0.3, pupil=0.95),
    'hopeful': dict(brow_up=0.32, brow_sad=0.45, smile=0.26, wet=0.75, eye_open=0.95, pupil=1.05),
    'shaken': dict(brow_sad=0.8, brow_up=0.2, wide=0.18, pupil=0.8, tremble=0.6, m_open=0.08, wet=0.8, pale=0.2, sweat=0.2, eye_open=0.92),
    'happy': dict(smile=0.7, teeth=0.6, squint=0.22, brow_up=0.15, blush=0.4),
    'sly': dict(smile=0.45, m_side=0.65, squint=0.35, brow_asym=0.55, look_x=0.3),
    'sure': dict(smile=0.25, brow_up=0.2, h_nod=-0.05, m_press=0.22),
    'giggle': dict(smile=0.82, teeth=0.7, squint=0.45, m_open=0.15, blush=0.6),
    # the queen: dead eyes, red mouth, no blinks; her people-expressions are not human
    'queen_still': dict(lock=1.0, still=1.0, eye_open=1.0),
    'queen_stare': dict(lock=1.0, still=1.0, eye_open=1.0),
    'queen_soft': dict(lock=1.0, still=1.0, eye_open=1.0),
    'queen_call': dict(m_open=1.0, m_round=0.4, lock=1.0, still=1.0),
    'queen_grin': dict(lock=1.0, still=1.0),
    'queen_blank': dict(lock=1.0, still=1.0),
    'queen_full': dict(lock=1.0, still=1.0), 'queen_drawn': dict(lock=1.0, still=1.0), 'queen_grin_red': dict(lock=1.0, still=1.0),
    'queen_off': dict(lock=1.0, still=1.0), 'queen_void': dict(lock=1.0, still=1.0),
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
    __slots__ = ('pen', 'cv', 'M', 's', 'lw', 'm6', 'det', 'sty')

    def __init__(self, pen, M, lw, sty=None):
        self.pen, self.cv, self.M = pen, pen.cv, M
        self.sty = sty                       # None, or the queen's scratch-line style (see _scratch_line)
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
        return Ctx(self.pen, m, self.lw / k, self.sty)

    def P(self, path):
        q = skia.Path(path); q.transform(self.M); return q

    def pt(self, x, y):
        a, b, tx, c, d, ty = self.m6
        return a * x + b * y + tx, c * x + d * y + ty

    def fill(self, path, c, a=255):
        if a > 0.5: self.pen.fill(self.P(path), c, a)

    def line(self, path, w=None, c=LINE, a=255, cap='round'):
        if a <= 0.5: return
        if self.sty is not None and c == LINE: _scratch_line(self, self.P(path), (self.lw if w is None else w) * self.s, a); return
        self.pen.line(self.P(path), (self.lw if w is None else w) * self.s, c, a, cap)

    def shape(self, path, c, w=None, lc=LINE, a=255):
        q = self.P(path)
        self.pen.fill(q, c, a)
        if self.sty is not None and lc == LINE: _scratch_line(self, q, (self.lw if w is None else w) * self.s, a); return
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
        # one cached full-alpha image per colour; the (animated) alpha goes on the paint: same pixels, no cache misses
        if a > 0.5: self.radial(None, cx, cy, rx, [(0, c, 255), (0.5, c, 127.5), (1, c, 0)], sy=ry / rx, a=min(1.0, a / 255.0), clip=False)

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
    fw = clamp(P.wide * 1.25) * sp.get('fear_wide', 1.0)
    r = sp['eye_r'] * (1.0 + (0.16 + sp.get('fear_eyes', 0.0)) * P.wide * sp.get('fear_wide', 1.0)) * (1.0 + 0.04 * P.brow_up)
    asym = P.brow_asym * 0.0
    op = clamp(P.eye_open * (1.0 - P.blink) * (1.0 - 0.45 * P.squint) + 0.18 * P.wide * (1 - P.blink), 0, 1.25)
    rx = r * fs * (1.0 + 0.1 * (1.0 - fw) * (1.0 - sp.get('eye_h', 1.0)) * 2.0)
    r = r * lerp(sp.get('eye_h', 1.0), 1.0, fw)          # new cast: almond at rest, white discs in fear (REF rule 9)
    # sockets and bags (under everything else of the eye)
    c.glow(X, Y + 2, rx * 1.9, r * 1.7, sp['skin_dp'], 46 + 34 * P.wide + 30 * sp['bags'])
    if sp.get('sockets'): c.glow(X, Y + r * 0.3, rx * 1.6, r * 1.55, '#2a2f3c', 120 * sp['sockets'])
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
    if sp.get('eye_glow'):                      # optional red glow on the skin around the eye (thumbnail use)
        c.glow(X, Y + 2, rx * 1.75, r * 1.6, sp['eye_glow'], sp.get('eye_glow_a', 120))
    c.fill(white, wc)
    if det >= 1:
        c.radial(white, X, Y + r * 0.15, r * 1.05, [(0, wc, 0), (0.62, wc, 0), (1, sp.get('eye_edge', '#b9b0aa'), 230)], sy=1.0)
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
            a_v = min(255.0, 150 * clamp(P.bloodshot) * sp.get('vein_a', 1.0))
            vs, vs2 = [], []
            nv_ = int((6 if det >= 2 else 3) * sp.get('veins', 1.0)); vin = sp.get('vein_in', 0.42)
            for k in range(nv_):
                if sp.get('vein_even'):                  # spread evenly round the eye (thumbnail use)
                    ang = (k + 0.35 * hash01(k, 7 + side)) * 2 * PI / nv_ + side * 0.4
                else:
                    ang = (hash01(k, 7 + side) * 2 - 1) * PI
                x1, y1 = X + math.cos(ang) * rx * 1.02, Y + math.sin(ang) * r * 1.02
                mx_, my_ = X + math.cos(ang + 0.3) * rx * (vin + 0.2), Y + math.sin(ang + 0.3) * r * (vin + 0.2)
                x2, y2 = X + math.cos(ang - 0.15) * rx * vin, Y + math.sin(ang - 0.15) * r * vin
                vs.append(smooth([(x1, y1), (mx_, my_), (x2, y2)], False))
                if det >= 2:
                    vs2.append(smooth([(mx_, my_), (mx_ + math.cos(ang + 1.4) * r * 0.2, my_ + math.sin(ang + 1.4) * r * 0.2)], False))
            c.line(_multi(vs), c.lw * 0.22 * sp.get('vein_w', 1.0), '#b8424c', a_v)
            if vs2: c.line(_multi(vs2), c.lw * 0.15 * sp.get('vein_w', 1.0), '#c04a52', a_v * 0.8)
        if P.wet > 0 and det >= 1:
            c.fill(smooth([(X - rx, Y + r * 0.62), (X, Y + r * 0.85), (X + rx, Y + r * 0.62), (X, Y + r * 1.1)], True), '#a8c8f0', 120 * P.wet)
        if sp.get('iris_h') and det >= 1 and not sp.get('iris'):   # human iris (new cast): shrinks toward a dot in fear
            ir = r * lerp(sp.get('iris_k', 0.66), 0.3, fw) * (0.8 + 0.2 * clamp(P.pupil * 1.4))
            ic = sp['iris_h']
            # v2: a real iris: dark limbal ring, a lighter ring round the pupil, radial fibres; pupil 0.42 of the iris
            c.radial(oval(px, py, ir * fs, ir), px, py + ir * 0.1, ir * 1.02,
                     [(0, mix(ic, '#000000', 0.3), 255), (0.38, mix(ic, '#e8c49a', 0.38), 255), (0.7, ic, 255), (0.9, mix(ic, '#000000', 0.35), 255),
                      (1, mix(ic, '#000000', 0.6), 255)], sy=1.0)
            if det >= 2:
                fib = [poly([(px + math.cos(a_) * ir * 0.45 * fs, py + math.sin(a_) * ir * 0.45), (px + math.cos(a_) * ir * 0.85 * fs, py + math.sin(a_) * ir * 0.85)], False)
                       for a_ in np.linspace(0, 2 * PI, 14, endpoint=False)]
                c.line(_multi(fib), c.lw * 0.12, mix(ic, '#000000', 0.45), 110)
            c.line(oval(px, py, ir * fs, ir), c.lw * 0.18, mix(ic, '#000000', 0.7), 210)
            pr = min(pr, ir * 0.42)
            sp_hl = True
        if sp.get('iris'):                           # optional glowing iris (thumbnail use; the film's eyes have none)
            ir = r * sp.get('iris_r', 0.5)
            c.glow(px, py, ir * 1.9, ir * 1.9, sp['iris'], sp.get('iris_glow', 120))
            c.radial(oval(px, py, ir * fs, ir), px - ir * 0.2, py - ir * 0.25, ir * 1.1,
                     [(0, '#ff6070', 255), (0.55, sp['iris'], 255), (1, '#7d0614', 255)], sy=1.0)
            c.line(oval(px, py, ir * fs, ir), c.lw * 0.32, '#4a0209', 255)
            pr = ir * sp.get('iris_pupil', 0.36)
        c.fill(oval(px, py, pr * fs, pr), '#0b0b0e')
        if sp.get('iris_h') and det >= 1 and not sp.get('iris'):   # two highlights on the iris (0.3 and 0.12 of it)
            irr = r * lerp(sp.get('iris_k', 0.66), 0.3, fw) * (0.8 + 0.2 * clamp(P.pupil * 1.4))
            c.fill(oval(px - irr * 0.36 * fs, py - irr * 0.38, irr * 0.3 * fs, irr * 0.3), '#fbfaf6')
            c.fill(oval(px + irr * 0.38 * fs, py + irr * 0.34, irr * 0.12 * fs, irr * 0.12), '#fbfaf6', 220)
        else:
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
    hw = sp['mouth_w'] * (1.0 + 0.32 * wd - 0.48 * rd + 0.12 * o) + 10.0 * max(sm, 0) + sp.get('grin_w', 54.0) * g
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
    if sp.get('lip_glow'):                                            # queen: the lipstick red carries the widest glow
        gx, gy, gv = hm.map1(0, (cly + cry) * 0.5 + oh * 0.4, 8.0)
        if gv > 0: c.glow(gx, gy, hw * 1.9 + 30, oh * 0.8 + 34, sp['lip_glow'], 70 + 40 * clamp(g))
        if g > 0.3 and det >= 1 and P.smear > 0.01: _lip_smear(c, hm, sp, P, hw, cly, cry, oh)
    if lipk > 0 and det >= 1:                                         # coloured lips (officer2, mum, queen)
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
    n = int(clamp(round(abs(span) / (sp.get('tooth_w', 13.0) if det >= 1 else 18.0)), 4, sp.get('teeth_max', 16)))
    if n % 2: n += 1
    if sp.get('teeth_sep') and det >= 1:
        return _teeth_sep(c, X, Y, th, direction, n, P, hw)
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
        if sp.get('gap'):          # critic M9: Noah's front teeth are flat incisors (the pointed, longer pair read as fangs)
            h = th * (1.0 - 0.22 * centre ** 2) * (0.96 + 0.06 * hash01(i, 31)) * (0.9 if centre < 0.3 else 1.0)
            bot.append((xa, ya + direction * h * 0.99))
            bot.append(((xa + xb) / 2, (ya + yb) / 2 + direction * h))
            continue
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
    if sp.get('gap') and direction > 0 and det >= 1:                 # Noah: a gap between the two front teeth
        xm = (x0 + x1) / 2; ym = float(np.interp(xm, X if x1 > x0 else X[::-1], Y if x1 > x0 else Y[::-1]))
        gw = sp['gap'] * 0.5
        c.fill(poly([(xm - gw, ym - 3), (xm + gw, ym - 3), (xm + gw * 0.8, ym + th * 0.98), (xm - gw * 0.8, ym + th * 0.98)]), '#2a0e11')
        c.line(_multi([poly([(xm - gw, ym - 2), (xm - gw * 0.8, ym + th * 0.95)], False),
                       poly([(xm + gw, ym - 2), (xm + gw * 0.8, ym + th * 0.95)], False)]), c.lw * 0.4)


def _teeth_sep(c, X, Y, th, direction, n, P, hw):
    """Queen: a row of small SEPARATE teeth (dark gaps between them, slightly uneven, long and narrow)."""
    X = np.asarray(X); Y = np.asarray(Y)
    x0, x1 = float(X[0]), float(X[-1]); span = x1 - x0
    edges = np.linspace(0, 1, n + 1)
    ex = x0 + edges * span
    ey = np.interp(ex, X if x1 > x0 else X[::-1], Y if x1 > x0 else Y[::-1])
    teeth = []
    for i in range(n):
        xa, xb = ex[i], ex[i + 1]
        ya, yb = ey[i], ey[i + 1]
        w = abs(xb - xa); g = w * 0.16
        cen = abs((i + 0.5) / n - 0.5) * 2
        h = th * (1.08 - 0.42 * cen ** 2) * (0.85 + 0.3 * hash01(i, 91 + direction))
        lo, hi = (min(xa, xb) + g, max(xa, xb) - g)
        yt = (ya + yb) / 2 - direction * 2.5
        tip = yt + direction * h
        tilt = (hash01(i, 97) - 0.5) * w * 0.35
        teeth.append(smooth([(lo, yt), (hi, yt), (hi + tilt * 0.3, yt + direction * h * 0.7), ((lo + hi) / 2 + tilt, tip),
                             (lo + tilt * 0.3, yt + direction * h * 0.7)], True, 0.55))
    allp = _multi(teeth)
    c.fill(allp, '#e9e5da')
    c.grad(allp, x0, 0, x1, 0, [(0, '#8a8676', 255), (0.25, '#e9e5da', 0), (0.75, '#e9e5da', 0), (1, '#8a8676', 255)])
    ym = float(np.mean(ey))
    c.grad(allp, 0, ym, 0, ym + direction * th, [(0, '#e9e5da', 0), (1, '#b8b2a0', 200)])
    c.line(allp, c.lw * 0.32)


def _lip_smear(c, hm, sp, P, hw, cly, cry, oh):
    """Lipstick smeared from the grin's corners up the cheeks (queen, stage 3): tapered red strokes with a glow."""
    k = clamp(P.smear)
    for s_, cy_ in ((-1, cly), (1, cry)):
        pts = [(s_ * (hw - 4), cy_ + 2), (s_ * (hw + 10), cy_ - 14 * k), (s_ * (hw + 16), cy_ - 30 * k), (s_ * (hw + 14), cy_ - 44 * k)]
        X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 6.0)
        if V.min() < 0.05: continue
        path = _tube(list(zip(X.tolist(), Y.tolist())), [15.0, 12.0, 8.0, 2.0], 0.9)
        c.glow(float(X[1]), float(Y[1]), 30, 30, sp.get('lip_glow', '#ff4060'), 60 * k)
        c.fill(path, sp['lip'], 175 * k)
        c.fill(_tube(list(zip((X + s_ * 3).tolist(), (Y + 2).tolist())), [7.0, 5.0, 3.0, 1.0], 0.9), mix(sp['lip'], '#000000', 0.35), 120 * k)


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
    a_f = clamp(max((lift - 0.3) / 0.5, sp.get('forehead', 0.0)))
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
    c.fill(reg, sp['stubble'], 26 * a * (1.9 if sp.get('stub_dots') else 1.0))
    if sp.get('stub_dots') and det >= 2:                       # short stubble: fine dots (one path, one draw call)
        key = ('stub', my, tuple(sp['head_ws']))
        D = _SPC.get(key)
        if D is None:
            xs_, ys_, rs_ = [], [], []
            for k in range(420):
                u, v = hash01(k, 301), hash01(k, 302)
                x0 = (u * 2 - 1) * 84; y0 = my - 6 + v * (118 - my + 6)
                if y0 < my + 4 and abs(x0) < 30: continue
                w = float(np.interp(y0, sp['head_ys'], sp['head_ws'])) * 0.96
                if abs(x0) > w or (y0 < 40 and abs(x0) < 0.62 * w): continue
                xs_.append(x0); ys_.append(y0); rs_.append(0.45 + 0.35 * hash01(k, 303))
            D = _SPC[key] = (np.array(xs_), np.array(ys_), rs_)
        X1, Y1, V1 = hm.map(D[0], D[1], 1.0)
        dots = skia.Path()
        for xx, yy, vv, rr in zip(X1.tolist(), Y1.tolist(), V1.tolist(), D[2]):
            if vv > 0.15: dots.addCircle(xx, yy, rr)
        c.fill(dots, sp['stubble'], 120 * a)


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
    elif style == 'short_r':                      # short, receding at the temples (you: looks like dad)
        def yf(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.12, 0.42, 0.74, 1.02, 1.25, 1.62, 2.3, 2.8, PI], [-80, -84, -86, -100, -74, -46, -30, 22, 60, 72]) + \
                2.5 * np.sin(ph * 7.0 + part)
        grow = 4.0
    elif style == 'pony':                         # pulled back to a low ponytail, side part, wisps at the temples
        def yf(ph):
            a = np.abs(ph)
            base = np.interp(a, [0, 0.5, 1.0, 1.25, 1.6, 2.2, PI], [-88, -84, -64, -20, -2, 34, 46])
            # side part at +0.35 rad: the fringe sweeps diagonally down across the brow to the far temple
            u = np.clip((0.35 - ph) / 1.35, 0, 1)
            swoop = 40.0 * u ** 0.75 * (1.0 - np.clip((-1.0 - ph) / 0.3, 0, 1))
            return base + swoop
        grow = 10.0
    elif style == 'long':                         # queen: centre parting, hair hangs past the cheeks (see _queen_*)
        def yf(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.35, 0.75, 1.0, 1.3, PI], [-92, -86, -40, 30, 130, 130])
        grow = 7.0
    elif style == 'mop':                          # kid mop (Noah, kid-you): full, fringe on the brow, crown cowlick
        def yf(ph):
            a = np.abs(ph)
            fr = -64.0 + 12.0 * np.abs(np.sin(ph * 4.6 + part * 0.7)) ** 0.6 + 6.0 * part * np.clip(ph * part, 0, 1)
            return np.interp(a, [0, 1.0, 1.3, 1.6, 2.0, PI], [0, 0, 1, 1, 1, 1]) * (np.interp(a, [1.0, 1.3, 1.6, 2.2, PI], [-56, -18, -8, 30, 50])) + \
                (1 - np.interp(a, [0, 1.0, 1.3], [0, 0, 1])) * fr
        grow = 13.0
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
    if style == 'long':
        _queen_cap(c, hm, sp, P, det, sil); return
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
    elif style == 'mop':
        vol = _bumpy(hm, grow, 11, 10.0, -132.0, 46.0, spiky=True, seed=part + 2)
    elif style == 'pony':
        vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.6, y_bot=60)
    elif style == 'short_r':
        vol = _bumpy(hm, grow, 13, 4.0, -126.0, 30.0 + 44.0 * clamp(-hm.ct * 1.4), spiky=True, seed=part + 5)
    elif style == 'long':
        vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.4, y_bot=120)
    hair = inter(union(vol, sil), region)
    if style == 'long':
        c.fill(hair, hc)
        with c.clip(hair):
            c.radial(None, -20, -110, 120, [(0, sp['cloth'].get('sheen', '#2a3144'), 150), (0.6, hc, 0), (1, hc, 0)], clip=False)
        c.line(hair, c.lw)
        if det >= 1:                                  # centre parting
            X0, Y0, V0 = hm.map1(0, -118, 2); X1, Y1, V1 = hm.map1(0, -88, 4)
            if V1 > 0: c.line(poly([(X0, Y0), (X1, Y1)], False), c.lw * 0.6)
        return
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -90, 175, [(0, hhi, 120), (0.5, hc, 0), (1, hsh, 200)], clip=False)
        if style == 'mop' and det >= 1:               # crown cowlick: a tuft that sticks up against the grain
            X0, Y0, V0 = hm.map1(18 * part, -116, -20)
            c.fill(smooth([(X0 - 14, Y0 + 8), (X0 - 4, Y0 - 26), (X0 + 10, Y0 - 34), (X0 + 4, Y0 - 12), (X0 + 16, Y0 + 6)], True, 0.7), hc)
        if det >= 1 and style in ('pony',):
            for k in range(6 if det >= 2 else 3):     # combed back toward the tie
                x_ = -60 + k * 24
                c.line(smooth([(x_, -84), (x_ * 0.8, -104), (x_ * 0.4, -118)], False), c.lw * 0.3, hsh, 150)
        if det >= 1 and style in ('messy', 'short', 'bun', 'mop', 'short_r'):
            for k in range(7 if det >= 2 else 4):
                x_ = -70 + k * 22 + 6 * part
                c.line(smooth([(x_, -112), (x_ + 10 * part + 6, -92), (x_ + 4 + 8 * part, -70)], False), c.lw * 0.3, hsh, 150)
        if style == 'curly':
            _curls(c, hm, det, hc, hsh, hhi)
    if style == 'mop' and det >= 1:
        X0, Y0, V0 = hm.map1(18 * part, -116, -20)
        cw = smooth([(X0 - 14, Y0 + 8), (X0 - 4, Y0 - 26), (X0 + 10, Y0 - 34), (X0 + 4, Y0 - 12), (X0 + 16, Y0 + 6)], True, 0.7)
        c.fill(cw, hc); c.line(minus(cw, hair), c.lw * 0.8)
    c.line(hair, c.lw)
    if style == 'pony' and det >= 1 and abs(hm.st) < 0.6:  # two loose wisps at the temples
        for s_ in (-1, 1):
            X, Y, V = hm.map([s_ * 70, s_ * 80, s_ * 78], [-40, -4, 30], 2.0)
            if V.min() > 0.05: c.line(_pts_path(X, Y, False), c.lw * 0.45, hc, 230)


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
    if sp['hair'] == 'pony' and (abs(hm.st) > 0.25 or hm.ct < 0): _ponytail(c, hm, sp, P, det, t)
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
            if bv_ > 0.1: c.glow(bx_, by_, 24 * hm.sx(side * 56, sp['eye_y'] + 36), 13, sp['blush'], (90 + 80 * P.blush) * sp.get('blush_k', 1.0))
    if sp.get('freckles') and det >= 1 and face_v > -0.2: _freckles(c, hm, sp)
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
            if sp['hair'] not in ('messy', 'mop', 'long'):
                for side in (-1, 1):
                    _brow(c, hm, sp, P, side, eyes.get(side))
            _tears(c, hm, sp, P, t, det, eyes)
            _sweat(c, hm, sp, P, t, det)
    with _ink(c, 'pale'):
        c.line(sil, c.lw)
    if face_v > -0.35:
        _nose(c, hm, sp, P, det, skin, sh)
    if sp['hair']:
        if sp['hat'] != 'cap' or True:
            _hair_region(c, hm, sp, P, det, sil, t)
        if sp['hair'] in ('messy', 'mop', 'long') and face_v > -0.35:   # v2.1: brows over the fringe so fear angles read
            for side in (-1, 1):
                _brow(c, hm, sp, P, side, eyes.get(side))
        if sp['hair'] == 'long': _queen_face_hair(c, hm, sp, P, det, t)
    for side in (-1, 1):
        if -side * hm.st >= 0.25: _ear(c, hm, sp, side, skin, sh, det)
    if sp.get('glasses') and face_v > -0.2 and getattr(P, 'specs', 1.0) > 0.5:
        _glasses(c, hm, sp, P, det, eyes, t)
    if sp['hat'] == 'cap':
        _cap(c, hm, sp, P, det, cl, t)
    if sp['hair'] == 'pony' and hm.ct > -0.2 and getattr(P, '_body', False): _ponytail_front(c, hm, sp, P, det, t)
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
        self.hands = {}; self.info = {}
        b = sp['body']; hh = sp['hh']
        self.b = b
        self.yc = -1000.0 + hh                         # chin
        self.y_sh = self.yc + 44 + b.get('neck_extra', 0.0) - 3.0 * (P.breath - 0.5) * sp['breath'] - 26 * P.shrug
        self.y_ch = self.y_sh + 78
        self.y_wa = -540.0; self.y_belt = -478.0; self.y_hip = -422.0; self.y_cr = -392.0
        self.th = P.turn * PI / 2; self.ct, self.st = math.cos(self.th), math.sin(self.th)
        self.L = P.lean * 0.62 + P.hunch * 0.22
        self.cL, self.sL = math.cos(self.L), math.sin(self.L)
        self.sit = clamp(P.sit)
        self.hip_drop = 170.0 * self.sit + P.crouch * 120 + 150.0 * clamp(getattr(P, 'kneel', 0.0))
        self.y0c = -620.0
        self.tilt = math.radians(P.tilt)
        self.ctl, self.stl = math.cos(self.tilt), math.sin(self.tilt)
        bk = 1.0 + 0.014 * (P.breath - 0.5) * sp['breath']
        self.chest_k = bk
        # walk: phases and the hip drop that keeps the stance foot on the ground
        self.walk = clamp(P.walk_amt)
        self.run = clamp(getattr(P, 'run', 0.0))
        self.ph = P.walk_ph * 2 * PI
        self.stride = 230.0 * self.walk * (1.0 + 0.75 * self.run)
        drop = 0.0
        for sd in (-1, 1):
            f = self.foot_fwd(sd)
            if self.foot_lift(sd) < 1: drop = max(drop, math.sqrt(384.0 ** 2 + f * f) - 384.0)
        self.bob = P.bob + drop + 5.0 * self.walk * math.cos(2 * self.ph) + self.hip_drop - 20.0 * self.run * max(0.0, math.cos(2 * self.ph))

    # ---- walk helpers (side: -1 = character's right leg, +1 = left)
    def leg_phase(self, side):
        return self.ph + (0.0 if side > 0 else PI)

    def foot_fwd(self, side):
        return self.stride / 2 * math.cos(self.leg_phase(side))

    def foot_lift(self, side):
        return max(0.0, -math.sin(self.leg_phase(side))) * 62.0 * self.walk * (1.0 + 2.2 * self.run)

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


def _hand_geom(shape, side, press=0.0, fk=1.0):
    """dict(fills=[paths], nails=[paths], creases=[paths], press=[paths], lines=[paths], ring=(x, y, ang_deg, w)).
    fk scales the finger length (the queen: 1.4)."""
    th = -side
    FING = _FING if fk == 1.0 else tuple((o_, tuple(l_ * fk for l_ in ln_), w_ * (1.0 - 0.12 * (fk - 1.0)), sp_) for o_, ln_, w_, sp_ in _FING)
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
        for k, (off, lens, w, spl) in enumerate(FING):
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
        for k, (off, lens, w, spl) in enumerate(FING):
            if shape == 'point' and k == 0: continue
            x = th * off * 8.4
            roll = rrect(x - w * 0.5, 17, w, 18 - abs(off) * 1.6, w * 0.46)
            G['fills'].append(roll)
            G['creases'].append(smooth([(x - w * 0.36, 25), (x, 23.6), (x + w * 0.36, 25)], False))
            if k == 2: G['ring'] = (x, 22.0, 0.0, w)
        if shape == 'point':
            pts = _finger_pts(th * 12.6, 20.0, th * 0.05, tuple(l_ * fk for l_ in (15.0, 11.0, 9.0)))
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


def _hand_cached(shape, side, press, fk=1.0):
    key = (shape, side, press, fk)
    if key not in _HANDC:
        G = _hand_geom(shape, side, press, fk)
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


def _draw_hand(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring=False, press=0.0, t=0.0, wrapper=False):
    if sp.get('new') and not sp.get('v2'):                     # DIRECTION_V2 3.7: the Mirror cast's hands are the v2 hand system
        look = _hand2_look(sp, skin, sh)
        if wrapper: look['wrapper'] = True
        _hand2(c, x, y, scale * sp['body'].get('hand', 1.0), angle, side, shape, det, look, press, t)
        return
    if shape == 'pinch': shape = 'point'
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
    G = _hand_cached(shape, side, round(press, 1), sp['body'].get('fingers', 1.0))
    u = G['union']
    hc.fill(u, skin)
    hc.fill(G['shade'], sh, 150)
    ent = sp.get('entity')
    if ent and hc.sty is not None: hc.sty['ink'] = 'dark'
    if det >= 1 and G['seps'] is not None and shape != 'mitt':
        hc.line(G['seps'], hc.lw * 0.42, LINE, 150)
    hc.line(u, hc.lw * 0.9)
    if ent and hc.sty is not None: hc.sty['ink'] = 'pale'
    if det >= 1:
        if G['creases_p'] is not None: hc.line(G['creases_p'], hc.lw * 0.32, sp['skin_dp'], 170)
        if G['lines_p'] is not None: hc.line(G['lines_p'], hc.lw * 0.35, sp['skin_dp'], 150)
        nailc = mix(skin, '#ffffff', 0.38) if not ent else '#3a3f4a'
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
    elif name == 'pen':                       # black ballpoint, held upright: barrel, silver clip and tip
        c.shape(rrect(-6, -44, 12, 80, 5), '#17181c')
        c.fill(rrect(-4, -40, 3, 70, 1.5), '#4a4d57', 160)
        c.shape(rrect(3, -42, 4, 30, 2), '#c9ccd3', c.lw * 0.5)
        c.shape(poly([(-6, 36), (6, 36), (1.2, 50), (-1.2, 50)]), '#c9ccd3', c.lw * 0.5)
        c.fill(rrect(-6, -46, 12, 6, 3), '#2b2d33')
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
    else:
        _prop2(c, name, det, t)


def _prop2(c, name, det, t=0.0):
    """Mirror Steps props (prop coords, ~60-90 units, centred)."""
    if name == 'lipstick':                    # cherry lipstick: gold case, red bullet worn to a slant
        c.shape(rrect(-9, -6, 18, 46, 3), '#b8913e'); c.grad(rrect(-9, -6, 18, 46, 3), -9, 0, 9, 0,
                                                          [(0, '#6e5418', 255), (0.35, '#f0d27e', 255), (1, '#7a5c1c', 255)])
        c.shape(rrect(-7, -16, 14, 12, 2), '#d8b860', c.lw * 0.5)
        bullet = poly([(-6, -16), (6, -16), (6, -34), (-6, -44)])
        c.fill(bullet, '#c63449'); c.glow(0, -30, 14, 16, '#ff4060', 90); c.line(bullet, c.lw * 0.6)
        c.fill(poly([(-3, -18), (-1, -18), (-1, -38), (-3, -40)]), '#ff8a98', 160)
    elif name in ('candy_red', 'candy'):      # a red cinnamon candy in a clear twist wrapper
        for s_ in (-1, 1):
            tw = poly([(s_ * 12, -5), (s_ * 26, -12), (s_ * 29, 0), (s_ * 26, 12), (s_ * 12, 5)])
            c.fill(tw, '#e8eef2', 120); c.line(tw, c.lw * 0.35, LINE, 180)
            c.line(_multi([poly([(s_ * 14, -3), (s_ * 26, -8)], False), poly([(s_ * 14, 3), (s_ * 26, 8)], False)]), c.lw * 0.2, '#ffffff', 200)
        body = oval(0, 0, 15, 11)
        c.fill(body, '#c22a2e'); c.radial(body, -4, -4, 16, [(0, '#ff6a5a', 255), (0.6, '#c22a2e', 255), (1, '#7a1218', 255)])
        c.fill(oval(0, 0, 16, 12), '#e8eef2', 50); c.line(oval(0, 0, 16, 12), c.lw * 0.45)
        c.fill(oval(-5, -5, 4, 2.4), '#ffffff', 220)
    elif name == 'wrapper':                   # the empty twist wrapper (open fist at the end)
        c.fill(oval(0, 0, 18, 12), '#e8eef2', 110); c.line(oval(0, 0, 18, 12), c.lw * 0.35, LINE, 160)
        c.fill(oval(-2, 2, 9, 6), '#c22a2e', 60)
    elif name == 'keys':                      # carabiner, padlock key, CABIN 7 tag
        car = smooth([(-10, -40), (10, -40), (14, -20), (8, -2), (-8, -2), (-14, -20)], True, 0.8)
        c.line(car, c.lw * 2.0, '#9aa0a8'); c.line(car, c.lw * 0.4)
        c.line(oval(0, 4, 9), c.lw * 1.4, '#b9bec6'); c.line(oval(0, 4, 9), c.lw * 0.35)
        k_ = union(poly([(-3, 10), (3, 10), (3, 44), (0, 48), (-3, 44)]), oval(0, 12, 7))
        c.shape(k_, '#c9a44a', c.lw * 0.5)
        for k in range(3): c.fill(rect(3, 28 + k * 5, 4, 3), '#c9a44a')
        tag = rrect(8, 6, 30, 18, 3)
        c.shape(tag, '#d8cfb4', c.lw * 0.45)
        if det >= 1: text(c.cv, '', 0, 0)
        c.line(_multi([poly([(12, 13), (34, 13)], False), poly([(12, 18), (28, 18)], False)]), c.lw * 0.3, '#5a4a30', 220)
    elif name == 'padlock':                   # brass padlock (also the striker on the bell)
        sh_ = smooth([(-12, -2), (-12, -26), (0, -36), (12, -26), (12, -2)], False, 0.8)
        c.line(sh_, c.lw * 2.2, '#a7aeb7'); c.line(sh_, c.lw * 0.4)
        body = rrect(-18, -4, 36, 36, 6)
        c.fill(body, '#b8913e'); c.grad(body, -18, 0, 18, 0, [(0, '#6e5418', 255), (0.3, '#f0d27e', 255), (1, '#6e5418', 255)])
        c.line(body, c.lw * 0.6)
        c.fill(oval(0, 12, 3.5), '#2a2018'); c.fill(rect(-1.2, 12, 2.4, 9), '#2a2018')
    elif name == 'flashlight':                # big black aluminium flashlight, lens toward -y
        body = rrect(-9, -10, 18, 62, 5)
        c.fill(body, '#1c1e22'); c.grad(body, -9, 0, 9, 0, [(0, '#0e0f12', 255), (0.35, '#3a3e46', 255), (1, '#0e0f12', 255)])
        c.line(body, c.lw * 0.6)
        head = poly([(-9, -10), (9, -10), (14, -30), (-14, -30)])
        c.shape(head, '#1c1e22', c.lw * 0.6)
        c.shape(rrect(-15, -36, 30, 7, 2), '#b9bec6', c.lw * 0.5)
        if det >= 1:
            c.line(_multi([poly([(-9, 6 + k * 6), (9, 6 + k * 6)], False) for k in range(5)]), c.lw * 0.25, '#4a4e56', 200)
            c.fill(rrect(-3, 16, 6, 8, 2), '#3a3e46')
    elif name == 'phone_dark':                # Tess's black phone, screen off (a red glint in the glass)
        r = rrect(-22, -44, 44, 88, 8)
        c.shape(r, '#0c0d10'); c.fill(rrect(-19, -40, 38, 80, 5), '#14161b')
        c.grad(rrect(-19, -40, 38, 80, 5), -19, -40, 19, 40, [(0, '#3a3f4a', 140), (0.4, '#14161b', 0), (1, '#14161b', 0)])
        c.fill(oval(10, 26, 3, 1.5), '#ff4060', 160)
    elif name == 'bell':                      # the old breakfast hand bell: brass, wooden handle, cracked rim
        hd = rrect(-6, -48, 12, 26, 5); c.shape(hd, '#6b4a2a', c.lw * 0.6)
        bell = smooth([(-8, -22), (8, -22), (16, 4), (26, 26), (-26, 26), (-16, 4)], True, 0.6)
        c.fill(bell, '#b8913e'); c.grad(bell, -26, 0, 26, 0, [(0, '#5e4614', 255), (0.35, '#f2d488', 255), (0.6, '#c89a44', 255), (1, '#5e4614', 255)])
        c.line(bell, c.lw * 0.7)
        c.line(poly([(10, 26), (12, 18), (9, 12)], False), c.lw * 0.45, '#3a2a10', 220)      # the crack
    elif name == 'clipboard':
        c.shape(rrect(-28, -38, 56, 76, 4), '#8a6a44'); c.shape(rect(-22, -30, 44, 64), '#ece8de', c.lw * 0.4)
        c.shape(rrect(-10, -42, 20, 9, 2), '#a7aeb7', c.lw * 0.4)
    elif name == 'shoe':                      # Noah's white canvas sneaker (side view)
        up = smooth([(-30, 6), (-30, -12), (-10, -20), (14, -14), (30, -2), (32, 8)], True, 0.6)
        c.fill(up, '#e3ded2'); c.fill(_crescent(up, 0, -8), '#b0aa9c', 150); c.line(up, c.lw * 0.7)
        c.shape(rrect(-32, 6, 66, 8, 3), '#cfc8b8', c.lw * 0.6)
        c.line(_multi([poly([(-8 + k * 7, -16 + k * 1.5), (-2 + k * 7, -10 + k * 1.5)], False) for k in range(4)]), c.lw * 0.4, '#8a8478')
    elif name == 'tape_ring':                 # the empty blue tape ring left in Tess's grip
        c.line(oval(0, 0, 16, 9), c.lw * 2.6, '#4d8fd6'); c.line(oval(0, -1, 16, 8), c.lw * 0.8, '#8fc0f0')
        c.line(oval(0, 0, 18.5, 11.5), c.lw * 0.4); c.line(oval(0, 0, 13.5, 6.5), c.lw * 0.4)
    elif name == 'towel':                     # bunched striped towel (faded orange and white) with a hanging flap
        flap = smooth([(-34, 4), (30, -2), (52, 50), (60, 104), (30, 96), (4, 112), (-26, 100), (-50, 108), (-46, 54)], True, 0.6)
        bun = smooth([(-62, -18), (-20, -34), (30, -30), (64, -10), (50, 14), (0, 22), (-54, 14)], True, 0.8)
        for pth, dk in ((flap, 0.12), (bun, 0.0)):
            c.fill(pth, mix('#ece1cf', '#000000', dk))
            with c.clip(pth):
                c.line(_multi([smooth([(-60, -30 + k * 22), (0, -24 + k * 22 + 6 * (k % 2)), (60, -32 + k * 22)], False) for k in range(8)]),
                       c.lw * 2.6, mix('#d98a4e', '#000000', dk), 200)
                c.fill(_crescent(pth, 8, -6), '#7a5a40', 70)
            c.line(pth, c.lw * 0.7)
        c.line(_multi([smooth([(-30, -10), (-6, -2), (20, -14)], False), smooth([(-4, 40), (6, 70), (2, 100)], False)]), c.lw * 0.4, LINE, 150)
    elif name == 'watch':                     # Noah's digital watch (face toward the camera)
        c.shape(rrect(-10, -40, 20, 80, 4), '#2a2c30', c.lw * 0.5)
        c.shape(rrect(-20, -18, 40, 36, 6), '#3a3d44', c.lw * 0.6)
        c.fill(rrect(-14, -11, 28, 20, 2), '#9fb08a'); c.line(rrect(-14, -11, 28, 20, 2), c.lw * 0.35)
        for s_ in (-1, 1): c.shape(rrect(s_ * 20 - 3, -8, 6, 6, 1.5), '#6a6d74', c.lw * 0.3)
    elif name == 'lace':
        c.line(smooth([(-30, 0), (-10, -6), (10, 4), (30, -2)], False), c.lw * 0.9, '#f2efe6')
    elif name == 'mirror_small':
        c.shape(rrect(-30, -40, 60, 80, 4), '#6b4a2a'); c.fill(rect(-24, -34, 48, 68), '#9fb0c0')


def draw_prop(pen, name, x, y, size=80.0, angle=0.0, detail=2, t=0.0):
    """A prop facing the camera, centred at (x, y); size = its height in design px (default props are ~80 units)."""
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 2.2) * 0.8).sub(x, y, angle, size / 80.0)
    _prop(c, name, detail, t)


# ---------------------------------------------------------------------------------------------- outfits
def _torso_rows(sp, B):
    b = sp['body']; o = sp['outfit']; k = B.chest_k
    ys = [B.y_sh - 30, B.y_sh - 10, B.y_sh + 16, B.y_ch, B.y_ch + 80, B.y_wa, B.y_belt, B.y_hip]
    ws = [b['neck'] + 16, b['sh'] * 0.84, b['sh'], b['ch'] * k, b['ch'] * 0.97 * k, b['wa'], b['hip'] * 0.98, b['hip']]
    if o in ('hoodie', 'jacket', 'shell'):
        ws = [b['neck'] + 22, b['sh'] * 0.86, b['sh'], b['ch'] * k, b['ch'] * k, b['wa'] + 6, b['hip'] + 6, b['hip'] + 4]
    elif o == 'dress':
        ws = [b['neck'] + 6, b['sh'] * 0.8, b['sh'], b['ch'] * k, b['ch'] * 0.9 * k, b['wa'], b['hip'] * 0.96, b['hip']]
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


def _jacket_front(c, sp, B, rows, P, det, t):
    """You: open olive canvas work jacket, brown corduroy collar (Tess grabs it), grey henley with a button placket."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    pull = clamp(getattr(P, 'collar_pull', 0.0))
    op, v = _surf_poly(B, rows, [(-30, yS - 26), (30, yS - 26), (40, yC + 60), (36, B.y_hip - 22), (-36, B.y_hip - 22), (-40, yC + 60)], dz=2)
    if v > 0.05:
        hen = smooth(op, True, 0.3); c.fill(hen, cl['shirt'])
        c.grad(hen, 0, yS, 0, B.y_hip, [(0, cl['shirt'], 0), (1, cl['shirt_sh'], 210)])
        c.line(hen, lw * 0.5)
        pl, _ = _surf_poly(B, rows, [(-7, yS - 18), (7, yS - 18), (7, yS + 70), (-7, yS + 70)], dz=3)
        c.line(poly(pl), lw * 0.4, LINE, 200)
        for k in range(3):
            X, Y, vv, s_ = B.surf(0, yS - 4 + k * 26, 4, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 3.4 * s_), '#c9ccd0', lw * 0.3)
        nk, _ = _surf_poly(B, rows, [(-28, yS - 24), (0, yS - 10), (28, yS - 24)], dz=3)
        c.line(smooth(nk, False), lw * 0.5)
    # jacket fronts (open) with chest pockets
    for side in (-1, 1):
        fr, vv = _surf_poly(B, rows, [(side * 30, yS - 26), (side * 44, yC + 60), (side * 40, B.y_hip - 20)], dz=5)
        if vv > -0.1:
            c.line(smooth(fr, False), lw * 0.9)
        pk, vv = _surf_poly(B, rows, [(side * 50, yC - 6), (side * 92, yC - 8), (side * 92, yC + 50), (side * 52, yC + 52)], dz=4)
        if vv > 0.05:
            c.fill(poly(pk), cl['top_sh'], 90); c.line(poly(pk), lw * 0.5)
            fl, _ = _surf_poly(B, rows, [(side * 48, yC - 10), (side * 94, yC - 12), (side * 94, yC + 8), (side * 48, yC + 10)], dz=5)
            c.shape(poly(fl), cl['top'], lw * 0.5)
            X, Y, vv2, s_ = B.surf(side * 71, yC + 2, 6, False, rows)
            if vv2 > 0.1: c.shape(oval(X, Y, 3.6 * s_), cl['button'], lw * 0.3)
        lp, vv = _surf_poly(B, rows, [(side * 54, B.y_wa + 10), (side * 98, B.y_wa + 8), (side * 98, B.y_wa + 74), (side * 56, B.y_wa + 76)], dz=3)
        if vv > 0.05 and det >= 1: c.line(poly(lp), lw * 0.45, LINE, 200)
    if det >= 1:                                        # canvas seams and stitching
        for side in (-1, 1):
            sm, vv = _surf_poly(B, rows, [(side * (b['neck'] + 14), yS - 20), (side * b['ch'] * 0.9, yC - 20)], dz=1)
            if vv > 0.0: c.line(smooth(sm, False), lw * 0.35, cl['top_sh'], 220)
    # corduroy collar: folded flaps round the neck (lifted toward the back of the neck when grabbed)
    for side in (-1, 1):
        cp, vv = _surf_poly(B, rows, [(side * 8, yS - 34 - 16 * pull), (side * (b['neck'] + 30), yS - 42 - 22 * pull), (side * (b['neck'] + 36), yS - 8),
                                      (side * 44, yS + 30 - 10 * pull), (side * 26, yS + 4)], dz=8)
        if vv > -0.3:
            cpp = smooth(cp, True, 0.35)
            c.fill(cpp, cl['collar']); c.fill(_crescent(cpp, -side * 5, 3), cl['collar_sh'], 160)
            if det >= 1:
                with c.clip(cpp):
                    c.line(_multi([poly([(cp[0][0] + k * 5 * side, cp[0][1] - 20), (cp[3][0] + k * 5 * side, cp[3][1] + 20)], False)
                                   for k in range(-6, 8)]), lw * 0.22, cl['collar_sh'], 200)
            c.line(cpp, lw * 0.7)


def _shell_front(c, sp, B, rows, P, det, t):
    """Tess: burnt-orange rain shell zipped to the chest, stand collar, chest zip pocket, nylon sheen."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    zp, v = _surf_poly(B, rows, [(0, yS - 30), (1, yC + 40), (0, B.y_hip - 18)], dz=4)
    if v > 0.0:
        c.line(smooth(zp, False), lw * 1.5, cl['zip']); c.line(smooth(zp, False), lw * 0.45, mix(cl['zip'], '#ffffff', 0.25))
        X, Y, vv, s_ = B.surf(0, yS + 34, 6, False, rows)
        c.shape(rrect(X - 4 * s_, Y, 8 * s_, 20 * s_, 3 * s_), '#2a2422', lw * 0.35)
    for side in (-1, 1):                                # stand collar
        cp, vv = _surf_poly(B, rows, [(side * 2, yS - 34), (side * (b['neck'] + 18), yS - 40), (side * (b['neck'] + 22), yS - 10), (side * 4, yS - 4)], dz=7)
        if vv > -0.3:
            cpp = smooth(cp, True, 0.3); c.fill(cpp, cl['top_hi']); c.fill(_crescent(cpp, -side * 4, 3), cl['top_sh'], 150); c.line(cpp, lw * 0.6)
    pk, vv = _surf_poly(B, rows, [(18, yC - 10), (74, yC - 26)], dz=5)
    if vv > 0.05:
        c.line(poly(pk, False), lw * 0.9, cl['zip'])
    if det >= 1:
        for side in (-1, 1):
            sm, vv = _surf_poly(B, rows, [(side * (b['neck'] + 12), yS - 20), (side * b['ch'] * 0.88, yC + 4)], dz=1)
            if vv > 0.0: c.line(smooth(sm, False), lw * 0.35, cl['top_sh'], 220)
            hm_, vv = _surf_poly(B, rows, [(side * 30, B.y_hip - 26), (side * 30, B.y_hip - 6)], dz=2)
            if vv > 0.1: c.line(poly(hm_, False), lw * 0.4, '#d9d2c4', 200)
        hem, vv = _surf_poly(B, rows, [(-b['hip'] - 4, B.y_hip - 30), (b['hip'] + 4, B.y_hip - 30)], dz=2)
        if vv > -0.2: c.line(poly(hem, False), lw * 0.45, LINE, 180)
        # nylon sheen: a soft diagonal highlight band
        X0, Y0, _, _ = B.surf(-40, yC - 20, 2, False, rows); X1, Y1, _, _ = B.surf(30, B.y_wa, 2, False, rows)
        c.glow((X0 + X1) / 2, (Y0 + Y1) / 2, 46, 120, mix(cl['top_hi'], '#ffffff', 0.3), 60)


def _sweatshirt_front(c, sp, B, rows, P, det, t):
    """Noah: green crew-neck sweatshirt, faded white CEDAR LAKE arc print, kangaroo pocket (the candies); on grown Noah
    (cloth fit -> 1) stretch lines at the shoulders and across the chest."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    fit = cl.get('fit', 0.0)
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 10, yS - 26), (0, yS - 6), (b['neck'] + 10, yS - 26)], dz=4)
    if v > -0.2:
        c.line(smooth(nk, False), lw * 2.4, cl['top_sh']); c.line(smooth(nk, False), lw * 0.6)
    # arc print
    if det >= 1:
        txt = 'CEDAR LAKE'
        X, Y, vv, s_ = B.surf(0, yC - 6, 3, False, rows)
        if vv > 0.25:
            sc = s_ * (1.0 - 0.18 * fit)
            for i, ch in enumerate(txt):
                u = (i - (len(txt) - 1) / 2) / (len(txt) - 1)
                ang = u * 0.9
                x0 = u * 118.0 * (1 + 0.12 * fit); y0 = yC - 8 - 24.0 * math.cos(ang) + 24.0
                Xc, Yc, vc, sc2 = B.surf(x0, y0, 3, False, rows)
                if vc < 0.2 or ch == ' ': continue
                c.cv.save(); c.cv.translate(*c.pt(Xc, Yc)); c.cv.rotate(math.degrees(ang * 0.8) + B.tilt * 57.3)
                text(c.cv, ch, 0, 0, 800, 20 * sc2 * c.s * (1 - 0.15 * fit), cl['print'], 150)
                c.cv.restore()
            for k in (-1, 1):
                X2, Y2, v2, s2 = B.surf(k * 44, yC + 24, 3, False, rows)
                if v2 > 0.2: c.fill(oval(X2, Y2, 3 * s2), cl['print'], 120)
    # kangaroo pocket
    pk, v = _surf_poly(B, rows, [(-58, B.y_wa - 4), (58, B.y_wa - 4), (76, B.y_hip - 30 - 50 * fit), (-76, B.y_hip - 30 - 50 * fit)], dz=3)
    if v > 0.05:
        pp = smooth(pk, True, 0.25); c.fill(pp, cl['top_sh'], 110); c.line(pp, lw * 0.6)
        for side in (-1, 1):
            sl, _ = _surf_poly(B, rows, [(side * 58, B.y_wa - 4), (side * 72, B.y_wa + 56 - 40 * fit)], dz=4)
            c.line(poly(sl, False), lw * 0.5)
        if getattr(P, 'candy', 0) > 0.5 and det >= 1:   # a red candy wrapper peeking from the pocket
            X, Y, vv, s_ = B.surf(30, B.y_wa + 4, 6, False, rows)
            c.shape(oval(X, Y, 7 * s_, 4.5 * s_), '#c22a2e', lw * 0.35)
    hem, v = _surf_poly(B, rows, [(-b['hip'], B.y_hip - 30 - 60 * fit), (b['hip'], B.y_hip - 30 - 60 * fit)], dz=2)
    if v > -0.2: c.line(poly(hem, False), lw * 0.45, LINE, 200)
    if det >= 1:
        for side in (-1, 1):
            sm, vv = _surf_poly(B, rows, [(side * (b['neck'] + 12), yS - 22), (side * b['ch'] * 0.88, yC + 8)], dz=1)
            if vv > 0.0: c.line(smooth(sm, False), lw * 0.38, cl['top_sh'], 220)
        if fit > 0.3:                                       # two sizes too small: stretch lines
            ls = []
            for side in (-1, 1):
                for k in range(3):
                    a_, _ = _surf_poly(B, rows, [(side * (b['ch'] * 0.78), yC - 30 + k * 26), (side * (b['ch'] * 0.4), yC - 14 + k * 30)], dz=1)
                    ls.append(smooth(a_, False))
                a_, _ = _surf_poly(B, rows, [(side * (b['sh'] - 8), yS - 2), (side * (b['sh'] - 30), yS + 20)], dz=1)
                ls.append(smooth(a_, False))
            c.line(_multi(ls), lw * 0.35, LINE, 150 * fit)


def _tight_hem(c, sp, B, rows, P, det, skin, skin_sh):
    """Grown Noah: the sweatshirt hem sits above the belt line: a band of pyjama waistband and skin below it."""
    cl = sp['cloth']; b = sp['body']; fit = cl.get('fit', 0.0)
    y_hem = B.y_hip - 30 - 60 * fit
    band, v = _surf_poly(B, rows, [(-b['hip'] - 1, y_hem - 4), (b['hip'] + 1, y_hem - 4), (b['hip'], B.y_hip + 2), (-b['hip'], B.y_hip + 2)], dz=1)
    if v > -0.3:
        bp = poly(band); c.fill(bp, skin); c.fill(_crescent(bp, 0, -10), skin_sh, 120)
        wb, _ = _surf_poly(B, rows, [(-b['hip'], B.y_hip - 18), (b['hip'], B.y_hip - 18), (b['hip'], B.y_hip + 4), (-b['hip'], B.y_hip + 4)], dz=2)
        c.fill(poly(wb), cl['trousers']); c.line(poly(wb), c.lw * 0.5)
        c.line(bp, c.lw * 0.6)


def _jacket_drape(c, sp, B, rows, P, det, t):
    """Your olive jacket hung over grown Noah's shoulders (from 635.06): open, sleeves empty, corduroy collar up."""
    cl = sp['cloth']; b = sp['body']
    jc, jsh = cl['jacket'], cl['jacket_sh']
    for side in (-1, 1):
        pts, vv = _surf_poly(B, rows, [(side * 26, B.y_sh - 30), (side * (b['sh'] + 18), B.y_sh - 4), (side * (b['sh'] + 28), B.y_ch + 60),
                                       (side * (b['ch'] + 20), B.y_wa + 20), (side * 52, B.y_wa + 30), (side * 40, B.y_ch)], dz=14)
        if vv < -0.4: continue
        pp = smooth(pts, True, 0.45)
        c.fill(pp, jc); c.fill(_crescent(pp, -side * 16, 4), jsh, 170)
        c.line(pp, c.lw)
        cp, _ = _surf_poly(B, rows, [(side * 20, B.y_sh - 44), (side * (b['neck'] + 34), B.y_sh - 52), (side * (b['neck'] + 40), B.y_sh - 10), (side * 34, B.y_sh + 14)], dz=18)
        cpp = smooth(cp, True, 0.35); c.shape(cpp, cl['collar'], c.lw * 0.7)


def _dress_front(c, sp, B, rows, P, det, t):
    """The queen's black satin dress: high collar, a column of tiny buttons, vertical satin sheen (pale scratches)."""
    cl = sp['cloth']; b = sp['body']
    yS, yC = B.y_sh, B.y_ch
    X0, Y0, _, s0 = B.surf(-b['ch'] * 0.35, yC, 2, False, rows); X1, Y1, _, s1 = B.surf(-b['ch'] * 0.3, B.y_wa, 2, False, rows)
    c.glow((X0 + X1) / 2, (Y0 + Y1) / 2, 22 * s0, abs(Y1 - Y0) * 0.7 + 30, cl['sheen'], 150)
    if det >= 1:
        for k in range(6):
            X, Y, vv, s_ = B.surf(0, yS - 6 + k * 34, 4, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.2 * s_), cl['sheen'], 220)
        st = []
        for k in (-0.55, 0.5):
            a_, vv = _surf_poly(B, rows, [(k * b['ch'], yC - 30), (k * b['wa'] * 0.9, B.y_wa), (k * b['hip'] * 0.9, B.y_hip)], dz=1)
            if vv > 0: st.append(smooth(a_, False))
        with _ink(c, 'pale'):
            if st: c.line(_multi(st), c.lw * 0.4, LINE, 90)


def _dress_skirt(c, sp, B, P, det, t):
    """Floor-length black satin skirt over the legs; only the bare feet show under the hem (hem_sway swings it)."""
    cl = sp['cloth']; b = sp['body']
    sw = 14.0 * P.sec_x + 18.0 * getattr(P, 'hem', 0.0)
    X0, Y0, s0, _ = B.p3(0, B.y_wa + 10, 0, upper=True)
    X1, Y1, s1, _ = B.p3(0, -26, 0, upper=False)
    sit = clamp(P.sit)
    ht = math.sqrt((b['wa'] * B.ct) ** 2 + (b['wa'] * 0.6 * B.st) ** 2) * s0
    hh_ = math.sqrt(((b['hip'] * 1.5) * B.ct) ** 2 + ((b['hip'] * 1.0) * B.st) ** 2) * s1
    yk = Y0 + (Y1 - Y0) * 0.38
    feet = [B.foot_lift(sd) for sd in (-1, 1)]
    lift = max(getattr(P, 'fl_up', 0.0), getattr(P, 'fr_up', 0.0)) * 0.5
    pts = [(X0 - ht, Y0), (X0 + ht, Y0), (X0 + ht * 1.35, yk), (X1 + hh_ + sw, Y1 - lift), (X1 + hh_ * 0.3 + sw, Y1 + 6 - lift),
           (X1 - hh_ * 0.3 + sw, Y1 + 8 - lift), (X1 - hh_ + sw, Y1 - lift), (X0 - ht * 1.35, yk)]
    if sit > 0.3 and abs(B.st) > 0.55:
        fy = Y0 + 160 * s0
        pts = [(X0 - ht, Y0), (X0 + ht, Y0), (X0 + ht * 1.3, fy), (X0 + 230 * s0 + sw, fy + 10), (X0 + 240 * s0 + sw, Y1 - lift),
               (X0 + 120 * s0, Y1 + 6), (X0 - ht * 1.2, Y1 - 20), (X0 - ht * 1.3, fy)]
    _draw_legs(c, sp, B, P, det, t, cl['trousers'], cl['trousers_sh'], None, feet_only=True)
    sk = smooth(pts, True, 0.4)
    c.fill(sk, cl['top'])
    c.grad(sk, X0 - hh_, 0, X0 + hh_, 0, [(0, cl['top_hi'], 140), (0.3, cl['top'], 0), (0.62, cl['sheen'], 90), (0.75, cl['top'], 0), (1, cl['top_sh'], 220)])
    if det >= 1:
        folds = []
        for k in (-0.7, -0.25, 0.2, 0.62):
            folds.append(smooth([(X0 + k * ht, Y0 + 40), (X0 + k * ht * 1.4 + sw * 0.3, yk + 40), (X1 + k * hh_ + sw, Y1 - 6)], False))
        with _ink(c, 'pale'):
            c.line(_multi(folds), c.lw * 0.45, LINE, 100)
    with _ink(c, 'pale'):
        c.line(sk, c.lw)


def _tee_front(c, sp, B, rows, P, det, t):
    """Memory cast: crew-neck tee (you_kid: blue/white stripes; counselor: teal with a whistle lanyard; cook: apron)."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    if cl.get('stripe') and det >= 1:
        ys_, ws_, ds_ = rows
        torso_, _l, _r = _torso_path(B, rows)
        st = []
        for k in range(9):
            y0 = yS + 4 + k * 34
            if y0 > B.y_hip - 20: break
            a_, vv = _surf_poly(B, rows, [(-b['ch'] * 1.2, y0), (0, y0 + 2), (b['ch'] * 1.2, y0)], dz=1)
            st.append(smooth(a_, False))
        with c.clip(torso_):
            c.line(_multi(st), lw * 2.6, cl['stripe'], 230)
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 8, yS - 26), (0, yS - 8), (b['neck'] + 8, yS - 26)], dz=4)
    if v > -0.2: c.line(smooth(nk, False), lw * 0.7)
    if sp.get('lanyard') and v > 0.0:
        ly, _ = _surf_poly(B, rows, [(-b['neck'] - 4, yS - 24), (-8, yC + 40), (8, yC + 40), (b['neck'] + 4, yS - 24)], dz=6)
        c.line(smooth(ly, False), lw * 0.8, '#d8c040')
        X, Y, vv, s_ = B.surf(0, yC + 54, 8, False, rows)
        c.shape(rrect(X - 9 * s_, Y - 6 * s_, 18 * s_, 12 * s_, 5 * s_), '#c9ccd3', lw * 0.4)
    if sp.get('apron'):
        ap, vv = _surf_poly(B, rows, [(-50, yC - 10), (50, yC - 10), (70, B.y_hip), (-70, B.y_hip)], dz=4)
        if vv > 0: c.shape(poly(ap), '#f3f1ec', lw * 0.6)


# ---------------------------------------------------------------------------------------------- figure
def _limb_cols(sp):
    cl = sp['cloth']; o = sp['outfit']
    if o == 'police': return cl['shirt'], cl['shirt_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'hoodie': return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'coat': return cl['coat'], cl['coat_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o in ('jacket', 'shell', 'sweatshirt', 'dress', 'tee'):
        return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl.get('shoes')
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
        cov = 0.0 if getattr(P, 'hl_prop' if side > 0 else 'hr_prop') else 1.0          # covering the ear: further out and up
        He = np.array([ex + side * (4.0 + 0.3 * hw * cov), ey + (0.47 - 0.1 * cov) * hh, 26.0 - side * hw * 0.9 * math.sin(hy) - 20.0 * cov])
        H = H + (He - H) * ear
        # v2 review (B8): on the way up the hand swings out round the jaw instead of crossing the face
        H = H + np.array([side * (hw * 0.9 + 30.0), 0.0, -30.0]) * math.sin(math.pi * clamp(ear))
        pole = pole + (np.array([side * 0.2, 1.0, 0.75]) - pole) * ear
    hk = getattr(P, 'hshake', 0.0)
    if hk > 0.01:                                         # shaking hands (fear, grown Noah): 7-11 Hz tremor
        sd = 17 + side * 5
        H = H + np.array([noise1(P.t * 9.0, sd), noise1(P.t * 11.0, sd + 1), noise1(P.t * 7.0, sd + 2)]) * 9.0 * hk
    E, Wp = _ik(S, H, 182.0, 166.0, pole)
    return S, E, Wp


def _ear_weight(P, side):
    """Phone-to-ear weight of one arm: pose.hl_ear/hr_ear, or 1 for the legacy film.phone_ear() pose (prop 'phone',
    hand raised close to the shoulder: up > 0.5, fwd < 120, down < 60)."""
    pre = 'hl_' if side > 0 else 'hr_'
    ear = getattr(P, pre + 'ear', 0.0)
    # review round 2 (B18): phone_to_ear drives the ear weight itself; the legacy rule jumped it to 1 half way up the raise
    # (the phone snapped from the chest to the ear in one frame at 188.95, 660.95, 667.43)
    if getattr(P, '_ear_drv_' + pre, False): return clamp(ear)
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
    cut = 1.0 - 0.3 * sp['cloth'].get('fit', 0.0) * (o == 'sweatshirt') - 0.3 * clamp(getattr(P, 'cuff_up', 0.0))
    cut_pt = None
    if cut < 0.995:                                      # the sleeve ends up the forearm: bare wrist below it
        c.fill(tp, skin); _cloth_shade(c, tp, sh, 120, 1.0, 8 * pts[0][2]); c.line(tp, c.lw)
        tp, cut_pt, cut_prev = _cut_tube([(P2[0][0] - side * 4, P2[0][1] - 14)] + P2, [widths[0] * 1.05] + widths, 0.04 + 0.96 * cut)
    c.fill(tp, sleeve)
    _cloth_shade(c, tp, sleeve_sh, 170, 1.0, 12 * pts[0][2])
    if o == 'dress': c.glow((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2, 14, 60, sp['cloth']['sheen'], 120)
    with _ink(c, 'pale'):
        c.line(tp, c.lw)
    # elbow crease + cuff + patch
    if det >= 1:
        ex, ey = P2[1]
        dx, dy = P2[2][0] - P2[0][0], P2[2][1] - P2[0][1]
        c.line(smooth([(ex - 10, ey - 6), (ex, ey + 2), (ex + 9, ey - 4)], False), c.lw * 0.4, LINE, 150)
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    cuffc = sleeve_sh if o not in ('hoodie', 'sweatshirt') else mix(sleeve, '#000000', 0.15)
    if cut_pt is not None:
        cang = math.degrees(math.atan2(cut_pt[1] - cut_prev[1], cut_pt[0] - cut_prev[0])) - 90
        cuff = c.sub(cut_pt[0], cut_pt[1], cang, hz)
    else:
        cuff = c.sub(wx, wy, ang, hz)
    cw = aw1 * (0.62 if cut_pt is not None else 0.55)
    cpath = rrect(-cw, -22, cw * 2, 22, 5)
    if o != 'dress':
        cuff.fill(cpath, cuffc); cuff.line(cpath, c.lw * 0.7 / hz)
    if o in ('hoodie', 'sweatshirt') and det >= 1:
        cuff.line(_multi([poly([(k * cw / 4, -20), (k * cw / 4, -3)], False) for k in range(-3, 4)]), c.lw * 0.3 / hz, LINE, 140)
    B.hands[side] = c.pt(wx, wy)
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
    if ear > 0.0:                                         # turned over the raise (it snapped at ear 0.5)
        ee = smoothstep(clamp(ear))
        up = up + (1.0 - up) * ee
        rot = rot + ((-side * 14.0 * B.ct if prop else side * 22.0 * B.ct) - rot) * ee
        if not prop and ear > 0.5: hand_shape = 'relaxed'
    hang = ang * (1 - up) + (180.0) * up + rot
    hs = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0) * getattr(P, 'hl_scale' if side > 0 else 'hr_scale', 1.0)
    ring = (sp['ring'] == side)
    if prop:
        if ear > 0.35 and prop == 'phone':
            # phone pressed to the ear: dark back of the phone along the cheek, the hand wrapped round it. Review round 2:
            # the phone's face turns into its back over ear 0.35-0.65 (a cross-fade, it swapped in one frame at 0.5)
            xk = smoothstep(clamp((ear - 0.35) / 0.3))
            if xk < 0.999:
                c.pen.cv.saveLayer(None, skia.Paint(Alphaf=float(1.0 - xk)))
                pc0 = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs, 0, hs * 1.15)
                _prop(pc0, prop, det, t)
                c.pen.cv.restore()
            if xk > 0.001:
                c.pen.cv.saveLayer(None, skia.Paint(Alphaf=float(xk)))
                pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs,
                           side * 17.0 * B.ct * xk, hs * (1.15 - 0.15 * xk))
                _prop(pc, 'phone_back', det, t)
                c.pen.cv.restore()
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
        else:
            pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs, 0, hs * 1.15)
            _prop(pc, prop, det, t)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
    else:
        _draw_hand(c, sp, hand_shape, wx, wy, hs, hang, side, det, skin, sh, ring, press, t,
                   wrapper=(side > 0 and hand_shape == 'fist' and getattr(P, 'candy', 0.0) > 0.5))
    if sp.get('tape') == side and getattr(P, 'tape', 1.0) > 0.02 and det >= 1:
        _tape_on(c, wx, wy, hs * sp['body'].get('hand', 1.0), hang, side, P, hand_shape if not prop else 'grip', sp)


def _tape_on(c, x, y, scale, angle, side, P, shape, sp=None):
    """THE tape design (DIRECTION_V2 1.3 / 3.7; draw_tape): blue medical tape (#4d8fd6, sheen #8fc0f0) wrapping Noah's
    middle, ring and little fingers together in two bands, the edge lifting on the little-finger side. One function for
    every mode (body arms, hands inserts, fists, grips). tape_slip slides the bands toward the fingertips and off (the
    fingers slip out), tape_peel lifts the flap."""
    sp = sp or CAST['noah13']
    hc = c.sub(x, y, angle, scale)
    th = -side
    slip = clamp(getattr(P, 'tape_slip', 0.0)); peel = clamp(getattr(P, 'tape_peel', 0.0))
    a = 255 * clamp(P.tape) * (1.0 - clamp((slip - 0.7) / 0.3))
    if a < 2: return
    lw = hc.lw
    bands = []                                         # each band: (outline pts, flap anchor, flap dir)
    if shape in ('fist', 'grip', 'point'):
        if shape == 'grip':
            for xx in (0.3, 0.58):
                x0 = th * 15.0 - th * 33.0 * xx
                bands.append(([(x0 - 2.8, 13.0), (x0 + 2.8, 13.0), (x0 + 2.8, 39.5 + 6 * slip), (x0 - 2.8, 39.5 + 6 * slip)], (x0, 39.5), (0.0, 1.0)))
        else:
            xa, xb = th * (3.4 + 4.7), th * (-11.8 - 4.0)
            for yy in (27.0 + 6 * slip, 34.5 + 6 * slip):
                lo, hi = min(xa, xb), max(xa, xb)
                bands.append(([(lo, yy - 2.6), (hi, yy - 2.6), (hi, yy + 2.6), (lo, yy + 2.6)], (xb, yy), (-th * 1.0, 0.0)))
    else:
        look = _hand2_look(sp, '#000000', '#000000')
        G = _hand2_geom(shape if shape not in ('mitt',) else 'relaxed', side, look['fk'], look['fw'], 'short', 0.0, look.get('bound', False))
        fs = G['fingers'][1:4]
        for j, f0 in ((1, 0.62), (2, 0.42)):
            pts = []
            for k, (fp_, ws, cu) in enumerate(fs):
                jj = min(j, len(fp_) - 1)
                p0, p1 = fp_[jj - 1], fp_[jj]
                L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0
                f = clamp(f0 + slip * 1.2)
                cx_, cy_ = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
                ux, uy = (p1[0] - p0[0]) / L_, (p1[1] - p0[1]) / L_
                pts.append((cx_, cy_, ux, uy, ws[jj] * 0.55))
            h = 2.7
            (mx, my, mux, muy, mw), (lx, ly, lux, luy, lw_) = pts[0], pts[2]
            nx, ny = -muy, mux                                   # across the fingers, from the middle toward the little finger
            if (lx - mx) * nx + (ly - my) * ny < 0: nx, ny = -nx, -ny
            ux, uy = (mux + lux) * 0.5, (muy + luy) * 0.5
            A = (mx - nx * mw, my - ny * mw); Bp = (lx + nx * lw_, ly + ny * lw_)
            Mid = pts[1]
            outline = [(A[0] - ux * h, A[1] - uy * h), (Mid[0] - ux * h, Mid[1] - uy * h + 0.4), (Bp[0] - ux * h, Bp[1] - uy * h),
                       (Bp[0] + ux * h, Bp[1] + uy * h), (Mid[0] + ux * h, Mid[1] + uy * h + 0.4), (A[0] + ux * h, A[1] + uy * h)]
            bands.append((outline, Bp, (nx, ny)))
    for i, (pts, anchor, (dx_, dy_)) in enumerate(bands):
        band = smooth(pts, True, 0.35)
        hc.fill(band, '#4d8fd6', a)
        bb = band.getBounds()
        hc.grad(band, 0, bb.top(), 0, bb.bottom(), [(0, '#8fc0f0', 0.8 * a / 255), (0.45, '#4d8fd6', 0), (1, '#2f6aaa', 0.75 * a / 255)])
        hc.line(band, lw * 0.4, LINE, a)
        if i == len(bands) - 1:                          # the lifting edge on the little-finger side
            ax_, ay_ = anchor
            fl = poly([(ax_, ay_ - 2.4), (ax_ + dx_ * (3.5 + 3.0 * peel) - dy_ * (2.5 + 5.0 * peel), ay_ + dy_ * (3.5 + 3.0 * peel) - 1.5 - 6.0 * peel),
                       (ax_ + dx_ * (5.0 + 2.0 * peel), ay_ + dy_ * (5.0 + 2.0 * peel) + 1.5), (ax_, ay_ + 2.4)])
            hc.fill(fl, '#8fc0f0', a); hc.line(fl, lw * 0.32, LINE, a)


draw_tape = _tape_on


def _bare_side(sp, side):
    """True when this foot (side +1 = character's left) is bare."""
    cl = sp['cloth']
    if cl.get('shoes', 'x') is None: return True
    bare = cl.get('bare') or ''
    return ('L' in bare and side > 0) or ('R' in bare and side < 0)


def _cut_tube(P2, widths, f):
    """Tube along the leg polyline from the hip to fraction f (by length): (path, end point)."""
    L = [math.hypot(P2[i + 1][0] - P2[i][0], P2[i + 1][1] - P2[i][1]) for i in range(len(P2) - 1)]
    tot = sum(L) or 1.0; d = f * tot
    pts, ws = [P2[0]], [widths[0]]
    for i, l_ in enumerate(L):
        if d <= l_:
            u = d / (l_ or 1.0)
            pts.append((P2[i][0] + (P2[i + 1][0] - P2[i][0]) * u, P2[i][1] + (P2[i + 1][1] - P2[i][1]) * u))
            ws.append(widths[i] + (widths[i + 1] - widths[i]) * u); break
        d -= l_; pts.append(P2[i + 1]); ws.append(widths[i + 1])
    if len(pts) < 2: pts.append(P2[1]); ws.append(widths[1])
    return _tube(pts, [w * 1.06 for w in ws]), pts[-1], pts[-2]


def _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec, feet_only=False):
    b = sp['body']; cl = sp['cloth']
    skin, skin_sh, _ = _skin_cols(sp, P, None)
    order = []
    for side in (-1, 1):
        pre = 'fl_' if side > 0 else 'fr_'
        up_, fwd_, out_ = getattr(P, pre + 'up', 0.0), getattr(P, pre + 'fwd', 0.0), getattr(P, pre + 'out', 0.0)
        kn = getattr(P, 'kneel', 0.0)
        hip = np.array([side * b['hip'] * 0.46, B.y_hip + 8, 0.0])
        fwd = B.foot_fwd(side) + B.sit * 210.0 + fwd_
        lift = B.foot_lift(side) + up_
        ank = np.array([side * (b['hip'] * 0.46 + 6 + 30 * P.stance) + side * out_, -38.0 - lift, fwd])
        if kn > 0 and side < 0: ank = ank + np.array([0.0, -10.0 * kn, -230.0 * kn])
        if kn > 0 and side > 0: ank = ank + np.array([0.0, 0.0, 150.0 * kn])
        hipw = hip.copy()
        K, A = _ik(hipw + np.array([0, B.bob, 0]), ank, 206.0, 180.0, np.array([0.08 * side, -0.15, 1.0]))
        order.append((B.p3(*(hipw + np.array([0, 0, 0])), upper=False), B.p3(K[0], K[1] - B.bob, K[2], upper=False),
                      B.p3(A[0], A[1] - B.bob, A[2], upper=False), side, A))
    order.sort(key=lambda o: (o[0][3] + o[2][3]))
    lw0, lw1 = b['leg']
    o_ = sp['outfit']
    pants_end = 0.42 if cl.get('shorts') else (1.0 - 0.24 * cl.get('fit', 0.0) if o_ == 'sweatshirt' else 1.0)
    boots = o_ in ('jacket', 'shell')
    for hp, kp, ap, side, A in order:
        P2 = [(hp[0], hp[1]), (kp[0], kp[1]), (ap[0], ap[1])]
        widths = [lw0 * hp[2], (lw0 + lw1) / 2 * kp[2], lw1 * ap[2]]
        tp = _tube(P2, widths)
        bare = _bare_side(sp, side)
        pre = 'fl_' if side > 0 else 'fr_'
        pt_ = getattr(P, pre + 'point', 0.0)
        ax, ay, az = A
        pts = []
        if bare:
            box = ((-15, -22, 0), (15, -22, 0), (-19, 52, 0), (19, 52, 0), (-15, 66, 0), (15, 66, 0))
            hys = (0.0, -26.0)
        else:
            box = ((-22, -24, 0), (22, -24, 0), (-24, 58, 0), (24, 58, 0), (-18, 72, 0), (18, 72, 0))
            hys = (0.0, -30.0)
        for (hx, hz, _) in box:
            for hy in hys:
                hy2 = hy if hz < 40 else hy * (0.55 if bare else 0.73)
                if boots and hz < 10 and hy < 0: hy2 = -64.0
                zz = hz * math.cos(pt_) ; yy = hy2 + hz * math.sin(pt_)
                X, Y, s, Z = B.p3(ax + hx, ay + 38 + yy - B.bob, az + zz, upper=False)
                pts.append((X, Y))
        shoe = smooth(_hull(pts), True, 0.6)
        if not feet_only:
            if pants_end < 0.999:
                c.fill(tp, skin); _cloth_shade(c, tp, skin_sh, 140, 1.0, 8); c.line(tp, c.lw)
                pt, end, prev = _cut_tube(P2, widths, pants_end)
                c.fill(pt, legc); _cloth_shade(c, pt, legsh, 160, 1.0, 10)
                if cl.get('plaid') and det >= 1: _plaid(c, pt, cl, B)
                c.line(pt, c.lw)
            else:
                c.fill(tp, legc)
                _cloth_shade(c, tp, legsh, 160, 1.0, 10)
                if cl.get('plaid') and det >= 1: _plaid(c, tp, cl, B)
                c.line(tp, c.lw)
            if det >= 1 and sp['outfit'] in ('police', 'coat', 'hoodie', 'jacket', 'shell'):
                c.line(smooth([((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2), P2[1], ((P2[1][0] + P2[2][0]) / 2, (P2[1][1] + P2[2][1]) / 2 + 10)], False),
                       c.lw * 0.35, LINE, 120)
        if bare:
            fsk = skin if not sp.get('entity') else mix(skin, '#9aa6b4', 0.25)
            c.fill(shoe, fsk)
            bb = shoe.getBounds()
            c.fill(_crescent(shoe, 0, -bb.height() * 0.25), mix(skin_sh, '#000000', 0.1), 120)
            if det >= 1:
                toes = skia.Path()
                for k in range(5):
                    hx = side * (-13 + k * 6.5); hz = 64 - abs(k - 1) * 3.5 - 4 * clamp(P.toes)
                    X, Y, s, Z = B.p3(ax + hx, ay + 38 - 4 + 6 * clamp(P.toes) - B.bob, az + hz, upper=False)
                    toes.addCircle(X, Y, (5.2 - 0.6 * abs(k - 1)) * s)
                c.fill(toes, fsk)
                if cl.get('toe'): c.fill(toes, cl['toe'], 120)
                c.line(toes, c.lw * 0.45)
            c.line(shoe, c.lw)
        else:
            c.fill(shoe, shoec)
            bb = shoe.getBounds()
            c.glow(bb.centerX() - bb.width() * 0.18, bb.top() + bb.height() * 0.32, bb.width() * 0.3, bb.height() * 0.13, '#ffffff',
                   70 if shoec in ('#0c0c0f', '#111113') else 40)
            if cl.get('shoes_sh'): c.fill(_crescent(shoe, 0, -bb.height() * 0.3), cl['shoes_sh'], 150)
            c.line(shoe, c.lw)
            if sp['outfit'] in ('hoodie', 'sweatshirt', 'tee') and det >= 1:
                c.line(poly([(bb.left() + 4, bb.bottom() - 7), (bb.right() - 4, bb.bottom() - 7)], False), c.lw * 0.5, '#8a8478')
            if sp['outfit'] == 'sweatshirt' and det >= 1:      # Noah's loose lace
                lx, ly = bb.centerX(), bb.top() + bb.height() * 0.35
                c.line(smooth([(lx - 6, ly), (lx + 10, ly + 18 + 4 * P.sec_x), (lx + 4, ly + 34 + 6 * P.sec_x)], False), c.lw * 0.5, cl.get('lace', '#ffffff'))
            if boots and det >= 1:
                c.line(poly([(bb.left() + 3, bb.bottom() - 8), (bb.right() - 3, bb.bottom() - 8)], False), c.lw * 0.55)


def _plaid(c, path, cl, B, step=22.0):
    with c.clip(path):
        bb = path.getBounds()
        ls, ls2 = [], []
        x = bb.left() - step * 0.45
        k = 0
        while x < bb.right() + 10:
            (ls if k % 2 == 0 else ls2).append(poly([(x, bb.top()), (x, bb.bottom())], False)); x += step; k += 1
        y = bb.top(); k = 0
        while y < bb.bottom():
            (ls if k % 2 == 0 else ls2).append(poly([(bb.left(), y), (bb.right(), y)], False)); y += step * 1.18; k += 1
        c.line(_multi(ls), c.lw * 0.9, cl["plaid"], 140)
        c.line(_multi(ls2), c.lw * 0.45, cl['plaid2'], 120)


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


def _figure(c, who, P, det, t, light=None, upper_only=False, sp=None):
    """Whole character in body units on Ctx c (feet at y=0, crown at y=-1000)."""
    sp = sp or _resolve_sp(who, P)
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
    # v2 review (critic B8): an arm crossing from behind the torso to in front of it no longer pops in one frame; over
    # 30 design units of hand depth it is drawn behind AND, fading in, in front (a short cross-fade of the draw order)
    fz = {s: (1.0 if arm_z[s][0] >= -20 else smoothstep(clamp((arm_z[s][1] - 25.0) / 30.0))) for s in (-1, 1)}
    behind = [s for s in (-1, 1) if fz[s] < 1.0]
    front = [s for s in (-1, 1) if fz[s] > 0.0]
    front.sort(key=lambda s: arm_z[s][1])
    back_view = B.ct < -0.15
    # hood behind the neck
    for side in behind: _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    if not upper_only:
        if o == 'dress':
            _dress_skirt(c, sp, B, P, det, t)
        elif o not in ('cardigan',):
            _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
            _pelvis(c, sp, B, rows, legc, legsh, det)
        else:
            _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
    elif o not in ('coat', 'dress'):
        _pelvis(c, sp, B, rows, legc, legsh, det)
    torso, L, R = _torso_path(B, rows)
    top = {'police': cl.get('shirt'), 'coat': cl.get('coat')}.get(o, cl.get('top'))
    topsh = {'police': cl.get('shirt_sh'), 'coat': cl.get('coat_sh')}.get(o, cl.get('top_sh'))
    tophi = {'police': cl.get('shirt_hi'), 'coat': cl.get('coat_hi')}.get(o, cl.get('top_hi'))
    if o == 'cardigan' and not upper_only:
        _skirt(c, sp, B, det, B.y_wa + 10, -175, sp['body']['hip'] * 0.98, sp['body']['hip'] * 1.12, cl['skirt'], cl['skirt_sh'], t=t, P=P)
    # neck (behind collar)
    nb = B.p3(0, B.y_sh - 34, 0); nt = B.p3(0, B.yc - 30, 0)
    nw = sp['body']['neck']
    neck = _tube([(nb[0], nb[1]), (nt[0], nt[1])], [nw * 2 * nb[2], nw * 1.9 * nt[2]])
    if o == 'dress':                                          # high collar: the neck is covered to the jaw
        neck = _tube([(nb[0], nb[1]), (nt[0], nt[1] + 18)], [nw * 2.2 * nb[2], nw * 2.0 * nt[2]])
    if o == 'hoodie':
        hood = smooth([(nb[0] - (nw + 46) * nb[2], nb[1] + 8), (nb[0] - (nw + 30) * nb[2], nb[1] - 42), (nb[0], nb[1] - 56 - 10 * (B.ct < 0)),
                       (nb[0] + (nw + 30) * nb[2], nb[1] - 42), (nb[0] + (nw + 46) * nb[2], nb[1] + 8)], True, 0.8)
        c.shape(hood, cl['top_sh'])
    if o == 'dress':
        c.fill(neck, top); c.grad(neck, nb[0] - nw, 0, nb[0] + nw, 0, [(0, tophi, 120), (0.4, top, 0), (1, topsh, 200)])
        with _ink(c, 'pale'): c.line(neck, c.lw)
        if det >= 1:
            with _ink(c, 'pale'):
                c.line(_multi([smooth([(nb[0] - nw * 0.9, nt[1] + 26 + k * 22), (nb[0], nt[1] + 30 + k * 22), (nb[0] + nw * 0.9, nt[1] + 26 + k * 22)], False)
                               for k in range(3)]), c.lw * 0.4, LINE, 110)
    else:
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
    if o == 'sweatshirt' and cl.get('fit', 0) > 0.05: _tight_hem(c, sp, B, rows, P, det, skin, skin_sh)
    if not back_view:
        if o == 'police': _police_front(c, sp, B, rows, P, det, t)
        elif o == 'hoodie': _hoodie_front(c, sp, B, rows, P, det, t)
        elif o == 'coat': _coat_front(c, sp, B, rows, P, det, t)
        elif o == 'cardigan': _cardigan_front(c, sp, B, rows, P, det, t)
        elif o == 'jacket': _jacket_front(c, sp, B, rows, P, det, t)
        elif o == 'shell': _shell_front(c, sp, B, rows, P, det, t)
        elif o == 'sweatshirt': _sweatshirt_front(c, sp, B, rows, P, det, t)
        elif o == 'dress': _dress_front(c, sp, B, rows, P, det, t)
        elif o == 'tee': _tee_front(c, sp, B, rows, P, det, t)
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
    if getattr(P, 'jacket_on', 0) > 0.5 and sp['cloth'].get('jacket'): _jacket_drape(c, sp, B, rows, P, det, t)
    P._body = True; P._roll = head_rot
    head_front = math.cos(yaw) > -0.3
    if sp['hair'] == 'long' and back_view and head_front: _queen_back_hair(c, sp, B, P, det, t)
    with _ink(c, 'dark'):
        draw_head_local(hc, who, P, yaw, P.h_nod * 0.6 + 0.0, det, t, light, _head_sp(who, sp, P))
    if sp['hair'] == 'long' and back_view and not head_front: _queen_back_hair(c, sp, B, P, det, t)
    for side in front:
        if fz[side] < 1.0:
            c.pen.cv.saveLayerAlpha(None, int(255 * fz[side]))
            _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
            c.pen.cv.restore()
        else:
            _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    B.info = dict(head=c.pt(hx, hy), head_px=hs * 240.0 * c.s, roll=head_rot, hands=B.hands)
    return B


# ====================================================================================================== public drawing
def _as_pose(pose):
    if pose is None: return Pose()
    if isinstance(pose, str): return Pose(pose)
    if isinstance(pose, dict): return Pose(**pose)
    return pose


# ---------------------------------------------------------------------------------------------- lighting (new cast)
LIGHTS = {
    # Tess's flashlight as the key (warm core, falloff), the camp at midnight around it
    'flashlight': dict(rim='#fff2d6', rim_a=110, side=-1, key=-0.15, flash='tess', flash_c='#ffe2b0', flash_a=0.2),
    # moon rim on our side at midnight
    'moon': dict(rim='#9fb6ff', rim_a=80, side=1, key=-0.35),
    # the pale "too normal" dawn on the other side: low saturation, flat, cool-white rim
    'dawn': dict(rim='#e7e5e0', rim_a=85, side=1, key=-0.05, sat=0.72, tint='#e7e5e0', tint_k=0.12),
    # the red climax: lipstick light from one side, desaturated shadows
    'red': dict(rim='#ff4060', rim_a=150, side=-1, key=-0.2, tint='#ff6a78', tint_k=0.14, under='#3a1018'),
}


def _light_dict(light):
    if isinstance(light, str): return dict(LIGHTS[light])
    return light


def _key_mult(k):
    return [lerp(1, 0.6, -k), lerp(1, 0.68, -k), lerp(1, 0.86, -k)] if k < 0 else [1 + 0.1 * k, 1 + 0.02 * k, 1 - 0.12 * k]


def _key_only(light):
    """Lights that are only key + rim (moon, the plan's warm / red rims) take the fast path: no layer, the palette is
    keyed instead (cloth, hair, brows; skin through _skin_cols) - same look, ~25 ms less on a full-frame bust."""
    return bool(light) and not any(light.get(k_) for k_ in ('flash', 'tint', 'under')) and float(light.get('sat', 1.0)) >= 0.999


def _mulhex(h, m):
    v = col(h)
    r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
    return '#%02x%02x%02x' % tuple(int(clamp(x * mm / 255.0) * 255) for x, mm in zip((r, g, b), m))


def _palette_lit(sp, light):
    k = float(light.get('key', 0.0))
    if abs(k) < 1e-3: return sp
    key = ('lit', id(sp), round(k, 3))
    d = _SPC.get(key)
    if d is None:
        m = _key_mult(k)
        d = dict(sp)
        d['cloth'] = {kk: (_mulhex(v, m) if isinstance(v, str) and v.startswith('#') else v) for kk, v in sp['cloth'].items()}
        for kk in ('hair_c', 'brow_c'):
            if sp.get(kk): d[kk] = _mulhex(sp[kk], m)
        _SPC[key] = d
    return d


@contextmanager
def _lit(pen, light, fx, fy, r, feet, bounds=None):
    """Whole-figure light for the new cast: key (-1 night .. +1 warm) and tint/sat as one colour matrix on a layer, the
    flashlight hot spot ('flash') and an under light ('under') painted src-atop (only on the figure). Yields the light
    dict to hand to the figure (key 0: the skin is not keyed twice; the rim crescents stay)."""
    if not light:
        yield light; return
    k = float(light.get('key', 0.0)); sat = float(light.get('sat', 1.0)); tint = light.get('tint'); tk = float(light.get('tint_k', 0.0))
    if abs(k) < 1e-3 and sat >= 0.999 and not tint and not light.get('flash') and not light.get('under'):
        yield light; return
    if k < 0: m = [lerp(1, 0.6, -k), lerp(1, 0.68, -k), lerp(1, 0.86, -k)]
    else: m = [1 + 0.1 * k, 1 + 0.02 * k, 1 - 0.12 * k]
    if tint:
        tr, tg, tb = [v / 255.0 for v in col(tint)[:3]] if not isinstance(col(tint), int) else [((col(tint) >> sh_) & 255) / 255.0 for sh_ in (16, 8, 0)]
        m = [mi * lerp(1.0, tv * 1.25, tk) for mi, tv in zip(m, (tr, tg, tb))]
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    S = [[lerp(lr, 1, sat) if i == j else lerp([lr, lg, lb][j], 0, sat) * 0 + (1 - sat) * [lr, lg, lb][j] for j in range(3)] for i in range(3)]
    for i in range(3): S[i][i] = sat + (1 - sat) * [lr, lg, lb][i]
    cm = []
    for i in range(3): cm += [m[i] * S[i][0], m[i] * S[i][1], m[i] * S[i][2], 0.0, 0.0]
    cm += [0.0, 0.0, 0.0, 1.0, 0.0]
    cv = pen.cv
    bb = skia.Rect.MakeLTRB(*bounds) if bounds is not None else None     # keep the layer small (speed at 2560)
    cv.saveLayer(bb, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(cm)))
    area = bb if bb is not None else skia.Rect.MakeXYWH(fx - 4 * r, fy - 4 * r, 8 * r, 8 * r)
    try:
        yield dict(light, key=0.0)
        if light.get('flash'):                           # warm hot spot: cached radial image, src-atop, an oval only
            fc = light.get('flash_c', '#ffe2b0'); fa = float(light.get('flash_a', 0.2))
            sx = -0.18 * r * light.get('side', 1)
            R = 1.25 * r; cx_, cy_ = fx + sx, fy - 0.1 * r
            img = _gimg('r', [(0, fc, 255 * fa), (0.4, fc, 255 * fa * 0.4), (1, fc, 0)])
            m = skia.Matrix(); m.setScale(2 * R / 512.0, 2 * R / 512.0); m.postTranslate(cx_ - R, cy_ - R)
            p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kSrcATop,
                           Shader=img.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, _LINS, m))
            cv.drawOval(skia.Rect.MakeLTRB(cx_ - R, cy_ - R, cx_ + R, cy_ + R), p)
        if light.get('under'):
            p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kSrcATop)
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(feet[0], feet[1]), skia.Point(feet[0], fy - 0.3 * r)],
                                                       [col(light['under'], 140), col(light['under'], 0)]))
            cv.drawRect(area, p)
    finally:
        cv.restore()


def draw(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, aim=None):
    """Full body. height = feet-to-crown in design px. pose.dx (design px) shifts the figure (walks).
    aim=(x, y): as pose.approach goes 0 -> 1 the figure slides so its head reaches that point (put the lens axis
    here for lean_in toward a doorbell / peephole; pair it with Layer depth=acting.depth(base))."""
    P = _as_pose(pose); t = P.t if t is None else t
    if who == 'queen': return queen_draw(pen, x, y_feet, height, P, detail, light, t)
    s = height / 1000.0
    sp = CAST[who]
    head_px = sp['hh'] * s
    det = _auto_detail(pen, head_px) if detail is None else detail
    ox = oy = 0.0
    if aim is not None and P.approach > 0:
        k = ease_in_out(clamp(P.approach))
        ox = (aim[0] - (x + P.dx)) * k
        oy = (aim[1] - (y_feet + P.dy - (1000.0 - sp['hh'] / 2) * s)) * k
    sp = _resolve_sp(who, P)
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px), _sty_for(sp, t)).sub(x + P.dx + ox, y_feet + P.dy + oy, 0.0, s)
    if not sp.get('new'): return _figure(c, who, P, det, t, light)
    light = _light_dict(light)
    hx, hy = x + P.dx + ox, y_feet + P.dy + oy - (1000.0 - sp['hh'] / 2) * s
    X0, Y0 = x + P.dx + ox, y_feet + P.dy + oy
    if _key_only(light): return _figure(c, who, P, det, t, light, sp=_palette_lit(sp, light))
    with _lit(pen, light, hx, hy, height * 0.55, (X0, Y0), (X0 - 0.62 * height, Y0 - 1.12 * height, X0 + 0.62 * height, Y0 + 0.04 * height)) as l2:
        return _figure(c, who, P, det, t, l2)


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    """Head-and-shoulders close-up. scale 1 = head 600 design px tall; (cx, cy) = rest head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    if who == 'queen': return queen_bust(pen, cx, cy, scale, P, detail, light, t)
    sp = CAST[who]
    k = 1.0 + 1.1 * clamp(P.approach)
    head_px = 600.0 * scale * k
    s = head_px / sp['hh']
    sp = _resolve_sp(who, P); s = head_px / sp['hh']
    c0 = Ctx(pen, skia.Matrix(), _lw_for(head_px), _sty_for(sp, t))
    yh = -1000 + sp['hh'] / 2
    ty = cy + 60.0 * scale * clamp(P.approach)
    c = c0.sub(cx - 0 * s, ty - yh * s, 0.0, s)
    det = _auto_detail(pen, head_px) if detail is None else detail
    if not sp.get('new'): return _figure(c, who, P, det, t, light, upper_only=True)
    light = _light_dict(light)
    if _key_only(light): return _figure(c, who, P, det, t, light, upper_only=True, sp=_palette_lit(sp, light))
    with _lit(pen, light, cx, ty, head_px * 0.95, (cx, ty + head_px * 1.6),
              (cx - head_px * 1.9, ty - head_px * 0.95, cx + head_px * 1.9, ty + head_px * 3.2)) as l2:
        return _figure(c, who, P, det, t, l2, upper_only=True)


def draw_head(pen, who, cx, cy, size, pose=None, detail=2, light=None, t=None):
    """Head only. size = crown-to-chin height in design px, (cx, cy) = head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    if who == 'queen': return queen_head(pen, cx, cy, size, P, detail, light, t)
    s = size / 240.0
    sp = _resolve_sp(who, P)
    c = Ctx(pen, skia.Matrix(), _lw_for(size), _sty_for(sp, t)).sub(cx, cy, P.h_tilt, s)
    yaw = (P.turn + P.h_turn) * PI / 2; pitch = P.h_nod * 0.6
    return draw_head_local(c, who, P, yaw, pitch, detail, t, light, _head_sp(who, sp, P))


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
_SCR = os.path.join(_HERE, '_work')                    # Mirror Steps film: work dir (align/, cache/)
VOICE_WAV = os.environ.get('MS_VOICE_WAV', os.path.join(_SCR, 'align', 'vo_en.wav'))
VOICE_WORDS = os.environ.get('MS_VOICE_WORDS', os.path.join(_SCR, 'align', 'asr_cache.json'))
TIMELINE = os.environ.get('MS_TIMELINE', os.path.join(_SCR, 'align', 'timeline.json'))
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
        cdir = os.path.join(_SCR, 'cache')
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
        if self.sp.get('breath', 1.0) == 0.0: P.breath = 0.5            # the queen does not breathe
        if self.who == 'queen':                                           # v2 slow drift: tilt ~0.5 deg/s, lean, hem sway
            P.h_tilt += 3.2 * noise1(t * 0.13, sd + 71)
            P.lean += 0.014 * noise1(t * 0.09, sd + 72)
            P.hem += 0.45 * math.sin(t * 0.9 + sd)
            P.blink = 0.0
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
        if self.who == 'queen':                                           # her hair lags 0.4 s behind any head move
            L_ = self._raw(t - 0.4)
            P.q_hair = L_.turn + L_.h_turn; P.q_hair_set = 1.0
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

    def phone_to_ear(self, t0, t1=None, side=1, fade=0.8, tilt=6.0):
        """Phone held to the ear (busts and full body): wrist just below the ear, elbow forward and down, the dark back of
        the phone along the cheek, the hand wrapped round it; the head leans into it. side +1 = character's left hand."""
        pre = 'hl_' if side > 0 else 'hr_'
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            self._arm(P, side, w, 0.0, -20.0, 40.0, 'grip', up=1.0, prop='phone')
            setattr(P, pre + 'ear', max(getattr(P, pre + 'ear'), w))
            setattr(P, '_ear_drv_' + pre, True)
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
        name = {'card': 'paper', 'notebook': 'paper', 'photo': 'paper', 'radio': 'radio_click', 'phone': 'ui_pop', 'pen': 'pen_click'}.get(prop)
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

    def stride(self, t0, t1=None, steps_per_s=1.8, facing=None, ramp=0.35, bob=0.0, surface='inside'):
        """A walk cycle in place: the legs, arms and bob of walking while the body is carried by the set (film.py moves
        it through a 3D room on world keys). facing: the turn (view) to walk in, kept from the spec when None.
        bob: extra vertical step (design units of the body height) per step, for treads. Heel strikes as events."""
        t1 = t0 + 2.0 if t1 is None else t1
        dur = max(0.2, t1 - t0)

        def fn(P, t):
            w = clamp(_env(t, t0, t1, ramp, ramp))
            if w <= 0: return
            P.walk_amt = max(P.walk_amt, w)
            P.walk_ph = steps_per_s * 0.5 * (t - t0)
            if facing is not None: P.turn = lerp(P.turn, float(facing), clamp(_env(t, t0 - 0.3, t1, 0.4, 0.4)))
            P.lean += 0.04 * w
            if bob: P.bob += bob * w * abs(math.sin(math.pi * steps_per_s * (t - t0)))
        self._add(t0 - ramp, t1 + ramp, fn)
        evs = []
        k = 1
        while t0 + k / steps_per_s < t1:
            evs.append(self._ev(t0 + k / steps_per_s, 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch', -4.0,
                                pan=0.0, n=1, foot='L' if k % 2 else 'R'))
            k += 1
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


# ====================================================================================================== Mirror Steps: faces
_KSTROKE = skia.Paint.kStroke_Style


def _scratch_line(c, q, w, a):
    """The queen's drawing language: no outline. Every LINE stroke becomes thin jittered scratch lines (2 passes),
    pale #d9dee6 on her dark shapes (ink 'pale') or a dark etched grey on her pale face (ink 'dark'). The jitter seed
    comes from the frame number // 3 (re-jittered every 3 frames)."""
    sty = c.sty
    pale = sty.get('ink', 'pale') == 'pale'
    colr = sty.get('pale', '#d9dee6') if pale else sty.get('dark', '#2b2f3a')
    wd = clamp(w * (0.3 if pale else 0.42), 1.0, 2.2 if pale else 3.4) * sty.get('wk', 1.0)
    seed = int(sty.get('seed', 0))
    b = q.getBounds()
    big = max(b.width(), b.height()) * c.cv.getTotalMatrix().getScaleX() > 60.0     # small strokes: one pass only
    for i, (ka, kw, dev, seg) in enumerate(((0.55 if pale else 0.85, 1.0, 1.3, 7.0), (0.32 if pale else 0.4, 0.55, 2.4, 11.0))[:2 if big else 1]):
        pe = skia.DiscretePathEffect.Make(seg, dev, seed * 7 + i * 3 + 1)
        p = skia.Paint(Color=col(colr, int(clamp(a * ka / 255.0) * 255)), AntiAlias=True, Style=_KSTROKE, StrokeWidth=wd * kw,
                       StrokeCap=skia.Paint.kRound_Cap, PathEffect=pe)
        c.cv.drawPath(q, p)


@contextmanager
def _ink(c, ink):
    """Switch the scratch ink (pale/dark) for a block (no-op for outlined characters)."""
    if c.sty is None:
        yield; return
    old = c.sty.get('ink'); c.sty['ink'] = ink
    try: yield
    finally: c.sty['ink'] = old


def _freckles(c, hm, sp):
    k = sp.get('freckle_k', 1.0)
    p = skia.Path()
    for i in range(30):
        u = hash01(i, 401); v = hash01(i, 402)
        side = -1 if i % 2 else 1
        x0 = side * (6 + u * 56); y0 = sp['eye_y'] + 24 + v * 22 - 0.12 * abs(x0)
        X, Y, V = hm.map1(x0, y0, 2.0)
        if V > 0.2: p.addCircle(X, Y, 1.3 + 1.4 * hash01(i, 403))
    c.fill(p, sp['freckles'], 140 * k)


def _ponytail(c, hm, sp, P, det, t):
    """Tess's low ponytail at the nape, swinging with lagged motion (drawn behind the skull)."""
    w = float(hm.W(70.0))
    X0, Y0, V0 = hm.map1(0, 72, -(hm.DF + hm.DB) * w * 0.92)
    side = 1.0 if hm.st < 0 else -1.0
    sw = 16.0 * P.sec_x
    X0 += side * 8
    pts = [(X0 - 13, Y0 - 6), (X0 + 13, Y0 - 6), (X0 + 19 + sw * 0.4, Y0 + 50), (X0 + 10 + sw, Y0 + 120), (X0 + 2 + sw * 1.3, Y0 + 168),
           (X0 - 8 + sw, Y0 + 116), (X0 - 17 + sw * 0.4, Y0 + 48)]
    tail = smooth(pts, True, 0.8)
    hc = sp['hair_c']
    c.fill(tail, hc)
    c.grad(tail, X0 - 18, 0, X0 + 18, 0, [(0, mix(hc, '#ffffff', 0.2), 120), (0.5, hc, 0), (1, mix(hc, '#000000', 0.4), 170)])
    if det >= 1:
        c.line(smooth([(X0 - 4, Y0 + 10), (X0 + sw * 0.5, Y0 + 80), (X0 + 2 + sw * 1.1, Y0 + 150)], False), c.lw * 0.3, mix(hc, '#000000', 0.4), 160)
    c.line(tail, c.lw)
    c.shape(rrect(X0 - 12, Y0 - 4, 24, 9, 4), '#1d1a1c', c.lw * 0.5)


def _ponytail_front(c, hm, sp, P, det, t):
    """Tess's low ponytail brought forward over her left shoulder: it emerges from behind the jaw on her left and falls
    in a soft S onto the chest, the tip splitting into locks (front and 3/4 views, full figure and busts)."""
    w = float(hm.W(80.0))
    xl, xr = hm.extent(w)
    X0 = xr - 6.0; Y0 = float(hm.J(84.0)) * hm.cp
    sw = 12.0 * P.sec_x
    L = [(X0 - 6, Y0 + 4), (X0 + 4 + sw * 0.2, Y0 + 70), (X0 - 4 + sw * 0.6, Y0 + 140), (X0 + 6 + sw, Y0 + 200)]
    R = [(X0 + 30, Y0 - 6), (X0 + 44 + sw * 0.2, Y0 + 66), (X0 + 34 + sw * 0.6, Y0 + 140), (X0 + 30 + sw, Y0 + 196)]
    tips = [(X0 + 10 + sw, Y0 + 236), (X0 + 18 + sw, Y0 + 214), (X0 + 26 + sw, Y0 + 240), (X0 + 30 + sw, Y0 + 212)]
    tail = smooth(R + [tips[3], tips[2], tips[1], tips[0]] + L[::-1], True, 0.7)
    hc = sp['hair_c']
    c.fill(tail, hc)
    c.grad(tail, X0 - 8, 0, X0 + 46, 0, [(0, mix(hc, '#000000', 0.3), 150), (0.35, hc, 0), (0.62, mix(hc, '#ffffff', 0.28), 130), (0.8, hc, 0),
                                         (1, mix(hc, '#000000', 0.25), 120)])
    if det >= 1:
        st = []
        for f in (0.25, 0.5, 0.75):
            st.append(smooth([(lerp(L[i][0], R[i][0], f), lerp(L[i][1], R[i][1], f)) for i in range(4)] + [tips[int(f * 3)]], False))
        c.line(_multi(st), c.lw * 0.32, mix(hc, '#000000', 0.4), 170)
    c.line(tail, c.lw)


def _queen_cap(c, hm, sp, P, det, sil):
    """The queen's hair over the skull: everything but a long narrow face window under a centre parting."""
    vol = hm.silhouette(grow=7.0, y_top=-124, y_bot=118)
    ys = np.linspace(-86, 118, 16)
    L, R = [], []
    for y in ys:
        w = float(hm.W(y)) * (0.74 + 0.12 * clamp((y + 86) / 100.0))
        XL, YL, _ = hm.map1(-w, y, 1.0); XR, YR, _ = hm.map1(w, y, 1.0)
        L.append((XL, YL)); R.append((XR, YR))
    top = hm.map1(0, -92, 2.0)
    win = smooth([(top[0], top[1])] + R + [hm.map1(0, 124, 2.0)[:2]] + L[::-1], True, 0.8)
    hair = minus(vol, win) if hm.ct > -0.3 else vol
    hc = sp['hair_c']
    c.fill(hair, hc)
    c.radial(hair, -20, -100, 150, [(0, sp['cloth'].get('sheen', '#2a3144'), 150), (0.6, hc, 0), (1, hc, 0)], sy=1.1)
    with _ink(c, 'pale'):
        c.line(hair, c.lw)
        if det >= 1 and hm.ct > -0.3:
            X0, Y0, _ = hm.map1(0, -122, 2); X1, Y1, _ = hm.map1(0, -90, 4)
            c.line(poly([(X0, Y0), (X1, Y1)], False), c.lw * 0.6)
            st = []                                          # strands combed from the parting
            for s_ in (-1, 1):
                for k in range(6):
                    f = (k + 1) / 7.0
                    pts = [hm.map1(s_ * (4 + 30 * f), -116 + 4 * f, 3)[:2], hm.map1(s_ * (30 + 52 * f), -96 + 30 * f, 3)[:2],
                           hm.map1(s_ * (60 + 36 * f), -50 + 50 * f, 3)[:2]]
                    st.append(smooth(pts, False))
            c.line(_multi(st), c.lw * 0.4, LINE, 70)


def _bump(y, y0, half):
    return float(np.exp(-((y - y0) / half) ** 2))


def _queen_face_hair(c, hm, sp, P, det, t):
    """The queen's long straight black hair (head-local coords, drawn after the face): two sheets from the centre
    parting that fall STRAIGHT down from the widest point of the skull past the cheeks, over the shoulders to the
    waist (they hang with gravity whatever the head tilt). hair_over 0..1 closes them over the face; eye_gap opens a
    slit for one eye (stage 1); m_gap parts them round the red mouth (stage 2 'mouth_only')."""
    if hm.ct < -0.3: return                                  # back view: _queen_back_hair covers it
    ho = clamp(P.hair_over); eg = clamp(P.eye_gap); mg = clamp(getattr(P, 'm_gap', 0.0))
    roll = math.radians(getattr(P, '_roll', P.h_tilt + P.tilt))
    sway = 10.0 * P.sec_x + 6.0 * getattr(P, 'hem', 0.0)
    wmax = float(hm.W(-30.0)) + 8.0
    XLm, XRm = hm.extent(wmax)
    ys = np.linspace(-100, 560, 44)

    def grav(x, y):                                          # un-tilt the hanging part about the crown
        k = clamp((y + 40.0) / 160.0)
        if abs(roll) < 1e-3 or k <= 0: return x, y
        a = -roll * k; px, py = 0.0, -100.0
        dx, dy = x - px, y - py
        return px + dx * math.cos(a) - dy * math.sin(a), py + dx * math.sin(a) + dy * math.cos(a)

    halves = []
    for side in (-1, 1):
        outer, inner = [], []
        for y in ys:
            if y < -30:
                w = float(hm.W(y)) + 8.0; xl, xr = hm.extent(w)
            else:
                xl, xr = XLm, XRm
            edge = xr if side > 0 else xl
            below = max(0.0, y - 60.0)
            xo = edge + side * (3.0 + 0.05 * below + 3.0 * math.sin(y * 0.05 + side)) + sway * below / 500.0
            if y < 116:                                    # inner edge follows the cheek, a little inside the face
                wf = float(hm.W(min(y, 112.0)))
                fx = hm.map1(side * wf * 0.86, min(y, 112.0), 2.0)[0]
                xi_rest = fx
            else:
                xi_rest = hm.map1(side * 30.0, 112.0, 2.0)[0] + side * 0.04 * (y - 116.0)
            cx = hm.map1(0, min(y, 112.0), 6.0)[0]
            close = ho if y < 140 else ho * clamp(1.0 - (y - 140) / 120.0) * 0.7
            xi = lerp(xi_rest, cx + side * 1.0, close)
            if side > 0: xi += eg * (sp['eye_dx'] + sp['eye_r'] * 1.4) * _bump(y, sp['eye_y'], 28.0)
            xi += side * mg * (sp['mouth_w'] + 16.0) * _bump(y, sp['mouth_y'] + 8, 24.0)
            xi = min(max(xi, cx + 1.0), xo - 4.0) if side > 0 else max(min(xi, cx - 1.0), xo + 4.0)
            outer.append(grav(xo, y)); inner.append(grav(xi, y))
        tip = grav(lerp(outer[-1][0], inner[-1][0], 0.4), ys[-1] + 18)
        pts = [hm.map1(0, -104, 4)[:2]] + outer + [tip] + inner[::-1]
        halves.append(smooth(pts, True, 0.6))
    hc = sp['hair_c']
    allh = _multi(halves)
    c.fill(allh, hc)
    c.radial(allh, -16, -80, 230, [(0, sp['cloth'].get('sheen', '#2a3144'), 130), (0.45, hc, 0), (1, hc, 0)], sy=1.8)
    if det >= 1:                                              # strands: long pale scratches
        strands = []
        for side in (-1, 1):
            for k in range(6 if det >= 2 else 3):
                f = (k + 0.5) / 6.0
                pts = []
                for y in np.linspace(-60 + 14 * k, 520 - 34 * k, 9):
                    xl, xr = (hm.extent(float(hm.W(y)) + 8.0) if y < -30 else (XLm, XRm))
                    edge = xr if side > 0 else xl
                    below = max(0.0, y - 60.0)
                    span = 26.0 + 0.04 * below + ho * 50.0
                    pts.append(grav(edge + side * 0.04 * below - side * f * span + sway * below / 500.0, y))
                strands.append(smooth(pts, False))
        with _ink(c, 'pale'):
            c.line(_multi(strands), c.lw * 0.5, LINE, 120)
    with _ink(c, 'pale'):
        for h in halves: c.line(h, c.lw)


def _queen_back_hair(c, sp, B, P, det, t):
    """Back view: one black sheet of hair from the crown to the waist, edges scratched pale."""
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2]
    hx, hy = pv[0] + P.h_dx, pv[1] - (sp['hh'] / 2 - 22) * pv[2]
    w0 = 92 * hs; sway = 8.0 * P.sec_x + 5.0 * getattr(P, 'hem', 0.0)
    yw = B.p3(0, B.y_wa + 40, 0)[1]
    pts = [(hx - w0, hy - 40 * hs), (hx, hy - 128 * hs), (hx + w0, hy - 40 * hs), (hx + w0 * 1.05, hy + 60 * hs),
           (hx + w0 * 1.12 + sway * 0.5, (hy + yw) / 2), (hx + w0 * 0.95 + sway, yw), (hx + sway, yw + 24), (hx - w0 * 0.95 + sway, yw),
           (hx - w0 * 1.12 + sway * 0.5, (hy + yw) / 2), (hx - w0 * 1.05, hy + 60 * hs)]
    sheet = smooth(pts, True, 0.8)
    hc = sp['hair_c']
    c.fill(sheet, hc)
    c.radial(sheet, hx - 20 * hs, hy - 80 * hs, 160 * hs, [(0, sp['cloth'].get('sheen', '#2a3144'), 140), (1, hc, 0)], sy=1.4)
    if det >= 1:
        st = []
        for k in range(-3, 4):
            x0 = hx + k * w0 * 0.28
            st.append(smooth([(x0, hy - 60 * hs), (x0 + k * 3 * hs + sway * 0.3, (hy + yw) / 2), (x0 + k * 6 * hs + sway, yw - 6)], False))
        with _ink(c, 'pale'):
            c.line(_multi(st), c.lw * 0.5, LINE, 130)
    with _ink(c, 'pale'):
        c.line(sheet, c.lw)


_SPC = {}


def _resolve_sp(who, P):
    """CAST entry for a character at this pose: noah_grown morphs from noah13 (pose.age_body / age_face 0..1) - head
    shape, jaw, eyes, stubble and body widths are interpolated (cached per 1/20 step)."""
    sp = CAST[who]
    if who == 'you' and getattr(P, 'jacket_off', 0.0) > 0.5:
        if 'you_nojacket' not in _SPC:
            d = dict(sp); d['outfit'] = 'tee'; cl = sp['cloth']
            d['cloth'] = dict(cl, top=cl['shirt'], top_sh=cl['shirt_sh'], top_hi=mix(cl['shirt'], '#ffffff', 0.15), stripe=None)
            _SPC['you_nojacket'] = d
        return _SPC['you_nojacket']
    if who != 'noah_grown': return sp
    ab = round(clamp(P.age_body) * 20) / 20.0; af = round(clamp(P.age_face) * 20) / 20.0
    if ab >= 1.0 and af >= 1.0: return sp
    key = (who, ab, af)
    if key in _SPC: return _SPC[key]
    a, b = CAST['noah13'], sp
    d = dict(b)
    for k in ('eye_dx', 'eye_y', 'eye_r', 'eye_h', 'brow_th', 'nose_len', 'mouth_y', 'mouth_w', 'stub', 'bags', 'age',
              'freckle_k', 'hh', 'fear_eyes', 'forehead'):
        va = a.get(k, 1.0 if k == 'freckle_k' else 0.0); vb = b.get(k, 1.0 if k == 'freckle_k' else 0.0)
        kk = ab if k == 'hh' else af
        d[k] = va + (vb - va) * kk
    d['head_ws'] = [x + (y - x) * af for x, y in zip(a['head_ws'], b['head_ws'])]
    for k in ('skin', 'skin_sh', 'skin_dp', 'lip', 'hair_c', 'brow_c'): d[k] = mix(a[k], b[k], af)
    if af < 0.35: d['stubble'] = None
    d['body'] = {k: (tuple(x + (y - x) * ab for x, y in zip(a['body'][k], b['body'][k])) if isinstance(b['body'][k], tuple)
                     else a['body'][k] + (b['body'][k] - a['body'][k]) * ab) for k in b['body']}
    d['cloth'] = dict(b['cloth'], fit=ab, bare='R' if ab < 0.5 else 'LR')
    d['tape'] = -1 if ab < 0.25 else 0
    if len(_SPC) > 200: _SPC.clear()
    _SPC[key] = d
    return d


def _head_sp(who, sp, P):
    """Head profile: noah13 flashes grown Noah's face while pose.face_flash > 0.5 (S165)."""
    if who == 'noah13' and P.face_flash > 0.5: return CAST['noah_grown']
    return sp


def _sty_for(sp, t):
    """Scratch style for the entity (queen), re-jittered every 3 frames at 60 fps; None for the people."""
    if not sp.get('entity') or sp.get('v2'): return None
    return dict(seed=int(math.floor((t or 0.0) * 60.0 + 1e-6)) // 3, ink='pale', pale=sp['cloth'].get('scratch', '#d9dee6'),
                dark='#262a35')


# ====================================================================================================== Mirror Steps: modes
def _sleeve_cols(sp):
    cl = sp['cloth']
    return cl.get('top', '#333333'), cl.get('top_sh', '#222222')


def _hand_tip(x, y, ang, k, shape, side, fk=1.0):
    """Design point of the fingertip (index tip for 'point', middle fingertip otherwise) of a hand at wrist (x, y)."""
    th = -side
    hx, hy = ((th * 12.6, 20.0 + 35.0 * fk) if shape == 'point' else (th * 4.8, 31.0 + 33.0 * fk))
    if shape in ('fist', 'grip', 'mitt'): hx, hy = 0.0, 36.0
    return _hpt(x, y, ang, k, hx, hy)


def draw_hands(pen, who, x, y, size, pose=None, detail=2, light=None, t=None, main='r'):
    """Hand-only insert (mode 'hands'). (x, y) = palm centre of the main hand, size = its wrist-to-fingertip length in
    design px. The main hand is the character's RIGHT (pose ir_*); the second hand (il_*) shows when il_v > 0.
    Pose fields per hand (r / l): i?_x, i?_y offsets in units of size, i?_a angle (180 = fingers up), i?_v 0..1 (slides
    in along the forearm), i?_shape, i?_prop, i?_press, plus tape / tape_slip / hshake / cuff_up. base_prop draws an
    object under the hands ('shoe' with the lace for tie_loop, 'watch', 'padlock'). Returns dict(tip={'r':(x,y), 'l':..},
    wrist=..., prop=...) for syncing lipstick lines, smears and taps."""
    P = _as_pose(pose); t = P.t if t is None else t
    if who == 'queen': return queen_hands(pen, x, y, size, P, detail, light, t, main)
    sp = _resolve_sp(who, P)
    det = detail
    k = size / 66.0
    hk = sp['body'].get('hand', 1.0)
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.2), _sty_for(sp, t))
    skin, sh, _ = _skin_cols(sp, P, None)
    slv, slv_sh = _sleeve_cols(sp)
    out = dict(tip={}, wrist={}, prop={})
    light = _light_dict(light)
    with _lit(pen, light, x, y, size * 1.2, (x, y + size)) as l2:
        bp = P.base_prop
        if bp == 'shoe':                                  # Noah's sneaker on the floor, the lace looping up to the hands
            sx, sy = x, y + size * 0.62
            sc = c.sub(sx, sy, 0, size / 40.0)
            _prop2(sc, 'shoe', det, t)
            lz = clamp(P.lace)
            for s_ in (-1, 1):
                hx_ = x + (P.ir_x if s_ < 0 else P.il_x) * size; hy_ = y + (P.ir_y if s_ < 0 else P.il_y) * size
                hx2, hy2 = hx_ - s_ * size * 0.08, hy_ + size * 0.06
                lace = smooth([(sx - 6 * s_, sy - size * 0.3), (lerp(sx, hx2, 0.5) - s_ * 6, lerp(sy - size * 0.3, hy2, 0.5) + 10), (hx2, hy2)], False)
                c.line(lace, c.lw * 2.6, LINE); c.line(lace, c.lw * 1.4, sp['cloth'].get('lace', '#f2efe6'))
            if lz > 0.2:                                  # the half-tied loop between the hands
                lp = oval(x + size * 0.02, y - size * 0.02 - size * 0.12 * lz, size * 0.13 * lz, size * 0.1 * lz)
                c.line(lp, c.lw * 2.6, LINE); c.line(lp, c.lw * 1.4, sp['cloth'].get('lace', '#f2efe6'))
        elif bp == 'watch':                               # Noah's watch under kid-you's pressing finger
            _prop2(c.sub(x - size * 0.12, y + size * 0.28, 90.0, size / 42.0), bp, det, t)
        elif bp in ('padlock', 'towel', 'tape_ring'):
            _prop2(c.sub(x - size * 0.2, y + size * 0.35, 0, size / 60.0), bp, det, t)
        elif bp == 'collar':                              # your corduroy collar under Tess's fist (608.97), the olive shoulder below
            cc = CAST['you']['cloth']
            sh_ = smooth([(x - size * 2.2, y + size * 2.0), (x - size * 1.6, y + size * 0.55), (x + size * 1.6, y + size * 0.35), (x + size * 2.4, y + size * 2.0)], True, 0.7)
            c.fill(sh_, cc['top']); _cloth_shade(c, sh_, cc['top_sh'], 170, 1.0, size * 0.15); c.line(sh_, c.lw)
            col_ = smooth([(x - size * 1.5, y + size * 0.62), (x - size * 0.2, y - size * 0.1), (x + size * 1.5, y + size * 0.42),
                           (x + size * 1.3, y + size * 0.85), (x - size * 0.1, y + size * 0.4), (x - size * 1.3, y + size * 1.0)], True, 0.7)
            c.fill(col_, cc['collar']); _cloth_shade(c, col_, cc['collar_sh'], 170, 1.0, size * 0.08)
            if det >= 1:                                   # corduroy wales
                wl = [smooth([(x - size * (1.35 - 0.12 * k), y + size * (0.66 + 0.3 * (k % 2 == 7))), (x - size * 0.15 + size * 0.08 * k, y + size * (0.02 + 0.045 * k)),
                              (x + size * (1.4 - 0.1 * k), y + size * (0.46 + 0.04 * k))], False) for k in range(0, 8)]
                c.line(_multi(wl), c.lw * 0.3, cc['collar_sh'], 200)
            c.line(col_, c.lw)
        order = [('l', 1), ('r', -1)] if main == 'r' else [('l', -1), ('r', 1)]
        for nm, side in order:
            pre = 'i' + nm + '_'
            v = clamp(getattr(P, pre + 'v'))
            if v <= 0.01: continue
            ang = getattr(P, pre + 'a')
            a = math.radians(ang)
            fx_, fy_ = -math.sin(a), math.cos(a)                 # finger direction
            px = x + getattr(P, pre + 'x') * size; py = y + getattr(P, pre + 'y') * size
            slide = (1.0 - ease_out_cubic(v)) * 2.6 * size
            wx = px - fx_ * 24 * k - fx_ * slide; wy = py - fy_ * 24 * k - fy_ * slide
            ax, ay = -fx_, -fy_
            aw = 0.4 * size / max(0.7, hk) * (1.12 if sp['body'].get('hand', 1.0) > 1.1 else 1.0)
            if sp.get('kid'): aw *= 0.86
            fore = clamp(getattr(P, 'ir_fore', 0.0)) if nm == 'r' else 0.0
            end = (wx + ax * size * lerp(3.4, 1.25, fore), wy + ay * size * lerp(3.4, 1.25, fore))
            if fore > 0.01:                       # foreshortened: the arm comes at the lens from far away (the doorway above)
                ea = math.atan2(ay, ax) + math.radians(28.0) * fore
                up_end = (end[0] + math.cos(ea) * size * 2.6, end[1] + math.sin(ea) * size * 2.6)
                ua = _tube([end, up_end], [aw * lerp(1.25, 0.78, fore) * 1.3, aw * lerp(1.25, 0.55, fore) * 1.3])
                c.fill(ua, slv); _cloth_shade(c, ua, slv_sh, 170, 1.0, aw * 0.15)
                c.line(ua, c.lw * 0.8)
            arm = _tube([(wx + ax * size * 0.1, wy + ay * size * 0.1), end], [aw, aw * lerp(1.25, 0.8, fore)])
            c.fill(arm, skin); _cloth_shade(c, arm, sh, 120, 1.0, aw * 0.12)
            with _ink(c, 'dark'): c.line(arm, c.lw)
            cut = 0.32 + 0.5 * clamp(getattr(P, 'cuff_up', 0.0)) + 0.45 * sp['cloth'].get('fit', 0.0) * (sp['outfit'] == 'sweatshirt')
            cx0, cy0 = wx + ax * size * cut, wy + ay * size * cut
            slv_p = _tube([(cx0, cy0), end], [aw * 1.32, aw * lerp(1.5, 1.02, fore)])
            c.fill(slv_p, slv); _cloth_shade(c, slv_p, slv_sh, 170, 1.0, aw * 0.2)
            if sp['outfit'] == 'dress': c.glow(cx0 + ax * size * 0.8, cy0 + ay * size * 0.8, aw * 0.3, size * 0.6, sp['cloth']['sheen'], 120)
            with _ink(c, 'pale'): c.line(slv_p, c.lw)
            if sp['outfit'] != 'dress':
                ex0, ey0 = cx0 + ax * size * 0.14, cy0 + ay * size * 0.14
                cuff = smooth([(cx0 - ay * aw * 0.68, cy0 + ax * aw * 0.68), (cx0 + ay * aw * 0.68, cy0 - ax * aw * 0.68),
                               (ex0 + ay * aw * 0.7, ey0 - ax * aw * 0.7), (ex0 - ay * aw * 0.7, ey0 + ax * aw * 0.7)], True, 0.25)
                c.fill(cuff, sp['cloth'].get('top_sh', '#33382a') if sp['outfit'] == 'jacket' else mix(slv, '#000000', 0.12)); c.line(cuff, c.lw * 0.8)
                if sp['outfit'] == 'jacket' and det >= 1:      # DIRECTION_V2 3.7: the stitched cuff band (olive #4a5038 / #33382a)
                    for q_ in (0.25, 0.85):
                        sx0, sy0 = cx0 + ax * size * 0.14 * q_, cy0 + ay * size * 0.14 * q_
                        c.pen.dashed(c.P(poly([(sx0 - ay * aw * 0.62, sy0 + ax * aw * 0.62), (sx0 + ay * aw * 0.62, sy0 - ax * aw * 0.62)], False)),
                                     max(1.0, c.lw * 0.3 * c.s), '#8a8f6a', 220, on=5.0 * c.s, off=4.0 * c.s)
                if sp['outfit'] == 'jacket' and det >= 1:
                    c.line(_multi([poly([(cx0 + ax * size * 0.07 - ay * aw * 0.5 * q, cy0 + ay * size * 0.07 + ax * aw * 0.5 * q),
                                         (cx0 + ax * size * 0.07 - ay * aw * 0.5 * q + ax * 4, cy0 + ay * size * 0.07 + ax * aw * 0.5 * q + ay * 4)], False)
                                   for q in (-0.6, 0.6)]), c.lw * 0.4)
            shape = getattr(P, pre + 'shape'); prop = getattr(P, pre + 'prop'); press = getattr(P, pre + 'press')
            if sp.get('tape') == side and getattr(P, 'tape', 1.0) > 0.5 and not prop and str(shape) in ('point', 'relaxed', 'reach', 'mitt'):
                shape = 'open'     # critic M8: the index alone beside the folded taped bundle read as a raised middle finger
            if getattr(P, 'hshake', 0.0) > 0.01:
                wx += 0.035 * size * P.hshake * noise1(t * 10.0, 51 + side); wy += 0.03 * size * P.hshake * noise1(t * 12.0, 53 + side)
            hs = k / hk
            if prop:
                pa = ang + (90.0 if prop in ('candy_red', 'candy', 'tape_ring', 'keys') else 0.0)
                ppx, ppy = wx + fx_ * 34 * k, wy + fy_ * 34 * k
                if prop == 'lipstick':
                    pa = ang - 225.0; shape = 'grip'
                    ppx, ppy = wx + fx_ * 26 * k - fy_ * 10 * k * side, wy + fy_ * 26 * k + fx_ * 10 * k * side
                elif shape in ('pinch', 'point'):
                    ppx, ppy = _hand_tip(wx, wy, ang, k, 'point', side, sp['body'].get('fingers', 1.0))
                if shape in ('flat', 'open', 'palm'):          # resting on the open palm
                    _draw_hand(c, sp, 'flat', wx, wy, hs, ang, side, det, skin, sh, False, 0.0, t)
                    ppx, ppy = wx + fx_ * 26 * k, wy + fy_ * 26 * k
                    _prop(c.sub(ppx, ppy, ang + 90.0, k * 0.8), prop, det, t)
                else:
                    _prop(c.sub(ppx, ppy, pa, k * 0.95), prop, det, t)
                    _draw_hand(c, sp, 'grip' if shape not in ('pinch', 'point') else 'point', wx, wy, hs, ang, side, det, skin, sh, False, press, t)
                out['prop'][nm] = (ppx, ppy)
            else:
                _draw_hand(c, sp, shape, wx, wy, hs, ang, side, det, skin, sh, False, press, t,
                           wrapper=((shape == 'fist' or str(shape).startswith('xf:')) and getattr(P, 'candy', 0.0) > 0.5 and (nm == main)))
            if sp.get('tape') == side and getattr(P, 'tape', 1.0) > 0.02:
                _tape_on(c, wx, wy, hs * hk, ang, side, P, ('flat' if shape in ('flat', 'open', 'palm') else shape) if not prop or shape in ('flat', 'open', 'palm')
                         else ('point' if shape in ('pinch', 'point') else 'grip'), sp)
            if nm == 'r' and P.base_prop == 'candy_palm':
                _prop2(c.sub(wx + fx_ * 26 * k, wy + fy_ * 26 * k, ang + 90.0, k * 0.85 * clamp(P.palm_open * 1.6)), 'candy_red', det, t)
            out['tip'][nm] = _hand_tip(wx, wy, ang, k, shape, side, sp['body'].get('fingers', 1.0))
            out['wrist'][nm] = (wx, wy)
    return out


def _foot_paths(kind, d, toes_k, long_toes=1.0):
    """3/4 side view of a foot in feet-insert units (sole y=0, ankle at (0, -0.36)); d = +1 toes to screen right.
    kind 'bare' | 'boot' | 'sneaker'. Returns dict(outline, toes=[(cx, cy, rx, ry, ang)], extra=[paths])."""
    if kind == 'bare':
        tx = 0.44 * (1.0 + 0.12 * (long_toes - 1.0)) - 0.03 * toes_k
        pts = [(0.055, -0.44), (0.065, -0.32), (0.15, -0.2), (0.25, -0.12), (0.33, -0.08), (tx - 0.04, -0.055 + 0.01 * toes_k),
               (tx, -0.026 + 0.022 * toes_k), (tx - 0.005, 0.0 + 0.02 * toes_k), (0.36, 0.012), (0.22, 0.004), (0.12, -0.006),
               (0.0, 0.006), (-0.075, 0.01), (-0.11, -0.012), (-0.12, -0.055), (-0.1, -0.15), (-0.07, -0.3), (-0.062, -0.44)]
        toes = []
        for i, (u, r) in enumerate(((0.0, 1.0), (0.24, 0.78), (0.45, 0.7), (0.65, 0.62), (0.82, 0.55))[::-1]):
            cx = tx - 0.025 - u * 0.13 * long_toes; cy = -0.022 - u * 0.05 + 0.02 * toes_k * (1 - u)
            toes.append((cx, cy, 0.038 * r * long_toes ** 0.5, 0.026 * r, -0.35 - 0.6 * toes_k))
    elif kind == 'boot':
        pts = [(0.09, -0.56), (0.095, -0.34), (0.2, -0.22), (0.33, -0.16), (0.43, -0.12), (0.48, -0.06), (0.49, 0.0), (0.46, 0.04),
               (-0.13, 0.04), (-0.15, -0.02), (-0.14, -0.2), (-0.11, -0.56)]
        toes = []
    else:  # sneaker
        pts = [(0.075, -0.4), (0.085, -0.3), (0.2, -0.2), (0.34, -0.14), (0.44, -0.09), (0.48, -0.04), (0.48, 0.0), (0.45, 0.035),
               (-0.12, 0.035), (-0.14, -0.02), (-0.13, -0.16), (-0.1, -0.4)]
        toes = []
    pts = [(px * d, py) for px, py in pts]
    toes = [(cx * d, cy, rx, ry, ang * d) for cx, cy, rx, ry, ang in toes]
    return dict(outline=smooth(pts, True, 0.55), toes=toes)


def draw_feet(pen, who, x, y, size, pose=None, detail=2, light=None, t=None):
    """Feet insert (mode 'feet'): a low 3/4 view of the feet on a step edge at y. (x, y) = sole of the RIGHT foot (toes to
    screen right), size = shin-and-foot height in design px; the left foot stands 0.36 size to screen left (toes left).
    Pose: ft_l / ft_r 0..1 show them, fr_up / fl_up lift (units of size), fr_fwd / fl_fwd, fr_point / fl_point (toe down,
    rad), toes 0..1 curl the toes over the edge, ft_hem 0 hides the dress hem (seen from above, S276).
    The queen: pale blue-grey bare feet, too-long toes, tendons, cold dark toe tips, under the black satin hem;
    you: brown boots and jeans; Noah: one bare foot, one white sneaker, plaid pyjamas. Returns {'r': (x, y), 'l': ...}."""
    P = _as_pose(pose); t = P.t if t is None else t
    if who == 'queen': return queen_feet(pen, x, y, size, P, detail, light, t)
    sp = _resolve_sp(who, P); cl = sp['cloth']
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 1.6), _sty_for(sp, t))
    skin, sh, dp = _skin_cols(sp, P, None)
    ent = bool(sp.get('entity'))
    if ent: skin, sh = mix(skin, '#a9b4c2', 0.2), mix(sh, '#5d6676', 0.2)
    light = _light_dict(light)
    out = {}
    hem_on = sp['outfit'] == 'dress' and getattr(P, 'ft_hem', 1.0) >= 0.5
    with _lit(pen, light, x, y - size * 0.5, size * 0.9, (x, y), (x - 1.4 * size, y - 2.3 * size, x + 1.0 * size, y + 0.12 * size)) as l2:
        for side, vis, xo, d in ((1, getattr(P, 'ft_l', 1.0), -0.36, -1), (-1, getattr(P, 'ft_r', 1.0), 0.0, 1)):
            if vis <= 0.01: continue
            pre = 'fl_' if side > 0 else 'fr_'
            lift = getattr(P, pre + 'up') * size; fwd = getattr(P, pre + 'fwd') * size
            fx = x + xo * size + getattr(P, pre + 'out') * size + d * fwd * 0.4
            fy = y - lift + fwd * 0.15
            fc = c.sub(fx, fy, math.degrees(getattr(P, pre + 'point')) * d, size)
            bare = _bare_side(sp, side) or sp['outfit'] == 'dress'
            kind = 'bare' if bare else ('boot' if sp['outfit'] in ('jacket', 'shell') else 'sneaker')
            hem_y = -0.8 if sp['outfit'] == 'dress' else (-0.62 if (sp['outfit'] == 'sweatshirt' and cl.get('fit', 0) > 0.5) else -0.48)
            if kind == 'boot': hem_y = -0.5
            if bare and not (sp['outfit'] == 'dress' and not hem_on and ent):
                shin = _tube([(0.0, -1.3), (0.0, -0.36)], [0.13 if ent else 0.16, 0.105 if ent else 0.13])
                fc.fill(shin, skin); fc.fill(_crescent(shin, 0.025 * d, 0), sh, 140)
                with _ink(fc, 'dark'): fc.line(shin, fc.lw * 0.9)
            elif ent:                                        # from above: just the ankle under the dark
                shin = _tube([(0.0, -0.7), (0.0, -0.36)], [0.12, 0.105])
                fc.fill(shin, skin); fc.grad(shin, 0, -0.7, 0, -0.4, [(0, '#05070b', 255), (1, skin, 0)])
            F = _foot_paths(kind, d, clamp(P.toes), 1.35 if ent else 1.0)
            fo = F['outline']
            if kind == 'bare':
                fc.fill(fo, skin)
                fc.grad(fo, 0, -0.4, 0, 0.02, [(0, skin, 0), (0.6, skin, 0), (1, sh, 200)])
                fc.fill(_crescent(fo, -0.03 * d, -0.02), sh, 110)
                if ent:                                      # tendons and veins, cold toes
                    fc.line(_multi([smooth([(0.04 * d, -0.3), (0.16 * d, -0.17), (0.3 * d, -0.085)], False),
                                    smooth([(0.02 * d, -0.26), (0.12 * d, -0.13), (0.24 * d, -0.06)], False)]), fc.lw * 0.35, mix(sh, '#000000', 0.15), 170)
                    fc.line(smooth([(0.0, -0.22), (0.07 * d, -0.15), (0.06 * d, -0.08), (0.14 * d, -0.04)], False), fc.lw * 0.3, '#6d7d96', 160)
                fc.line(smooth([(-0.025, -0.33), (0.0, -0.355), (0.028, -0.33)], False), fc.lw * 0.35, dp, 150)     # ankle bone
                tps = []
                for cx, cy, rx, ry, ang in F['toes']:
                    q = oval(0, 0, rx, ry); m = skia.Matrix(); m.setRotate(math.degrees(ang)); m.postTranslate(cx, cy); q.transform(m)
                    tps.append((q, cx, cy, rx, ry, ang))
                for q, cx, cy, rx, ry, ang in tps:
                    fc.fill(q, skin)
                    if ent: fc.radial(q, cx + d * rx * 0.6, cy + ry * 0.2, rx * 1.6, [(0, '#3a404c', 220), (1, '#3a404c', 0)])
                    nl = oval(0, 0, rx * 0.55, ry * 0.45); m = skia.Matrix(); m.setRotate(math.degrees(ang)); m.postTranslate(cx + d * rx * 0.35, cy - ry * 0.35); nl.transform(m)
                    fc.fill(nl, '#9aa3b0' if ent else mix(skin, '#ffffff', 0.45), 220)
                    with _ink(fc, 'dark'): fc.line(q, fc.lw * 0.4)
                with _ink(fc, 'dark'): fc.line(fo, fc.lw * 0.9)
            else:
                shoe_c = cl.get('shoes') or '#4a3426'
                fc.fill(fo, shoe_c); fc.fill(_crescent(fo, -0.04 * d, -0.04), cl.get('shoes_sh', mix(shoe_c, '#000000', 0.3)), 170)
                fc.glow(0.22 * d, -0.13, 0.08, 0.03, '#ffffff', 55)
                fc.fill(rrect(-0.15, 0.005, 0.64, 0.04, 0.015) if d > 0 else rrect(-0.49, 0.005, 0.64, 0.04, 0.015), mix(shoe_c, '#000000', 0.5) if kind == 'boot' else cl.get('sole', '#cfc8b8'))
                fc.line(fo, fc.lw)
                lc = cl.get('lace', '#d8cfb8') if kind == 'sneaker' else '#2a2018'
                fc.line(_multi([poly([((0.12 + q_ * 0.06) * d, -0.24 + q_ * 0.035), ((0.17 + q_ * 0.06) * d, -0.2 + q_ * 0.035)], False) for q_ in range(4)]), fc.lw * 0.5, lc)
                if kind == 'sneaker':
                    fc.line(smooth([(0.2 * d, -0.18), (0.27 * d, -0.06 + 0.02 * P.sec_x), (0.24 * d, 0.03)], False), fc.lw * 0.5, lc)
            # hem / trouser cuff over the shin
            if hem_on:
                sw = 0.04 * getattr(P, 'hem', 0.0) + 0.02 * P.sec_x
                xs = np.linspace(-0.9, 0.9, 19)
                hem_pts = [(float(xx) + sw, hem_y + 0.025 * math.sin(xx * 9.0 + 1.3) + 0.04 * (abs(xx) > 0.5)) for xx in xs]
                hem = smooth([(-0.9, -2.2), (0.9, -2.2)] + hem_pts[::-1], True, 0.5)
                fc.fill(hem, cl['top']); fc.grad(hem, -0.6, 0, 0.6, 0, [(0, cl['top_hi'], 140), (0.35, cl['top'], 0), (0.62, cl['sheen'], 120), (1, cl['top_sh'], 220)])
                with _ink(fc, 'pale'):
                    fc.line(smooth(hem_pts, False), fc.lw)
                    fc.line(_multi([smooth([(q_ * 0.16, -1.6), (q_ * 0.17 + sw, hem_y + 0.01)], False) for q_ in (-4, -2, -1, 1, 3)]), fc.lw * 0.4, LINE, 110)
            elif sp['outfit'] != 'dress':
                pc = cl.get('trousers', '#2a3347')
                leg = smooth([(-0.15, -1.4), (0.15, -1.4), (0.15, hem_y), (0.0, hem_y + 0.02), (-0.15, hem_y)], True, 0.5)
                fc.fill(leg, pc); fc.fill(_crescent(leg, -0.05, 0), cl.get('trousers_sh', mix(pc, '#000000', 0.3)), 160)
                if cl.get('plaid'): _plaid(fc, leg, cl, None, 0.07)
                fc.line(leg, fc.lw)
            out['r' if side < 0 else 'l'] = (fx, fy)
    return out


def draw_feet_pov(pen, who, x, y, size, pose=None, detail=2, light=None, t=None):
    """Feet seen from above (mode 'feet', view 'pov'; DIRECTION_V2 H7): (x, y) = the centre between the feet, size = foot
    length in design px. People: boots / sneakers / bare feet with the trouser hems at the near (bottom) edge, toes
    pointing up the frame (away). The queen: her bare feet on the tread below, toes pointing DOWN the frame (at you),
    black nails, the satin hem with the spade-pip border round the ankles; toes curl over the tread edge (pose.toes)."""
    P = _as_pose(pose); t = P.t if t is None else t
    sp = _resolve_sp(who, P); cl = sp['cloth']
    q = who == 'queen'
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 1.4) * (0.75 if q else 1.0), None)
    ln = QV['line'] if q else LINE
    out = {}
    curl = clamp(P.toes)
    for side, vis in ((-1, getattr(P, 'ft_r', 1.0)), (1, getattr(P, 'ft_l', 1.0))):
        if vis <= 0.01: continue
        # the character's right foot is on screen left when they face you (queen), screen left from behind (you)
        sx = side * (0.21 if q else -0.21)
        lift = getattr(P, 'fr_up' if side < 0 else 'fl_up', 0.0)
        fc = c.sub(x + sx * size, y - lift * size * 0.5, 0.0, size * (1.0 + 0.25 * lift))
        lw = fc.lw
        d = 1.0 if q else -1.0                               # toes toward +y (queen, at you) or -y (yours, away)
        med = -side * (1.0 if q else -1.0)                   # the big toe on the inner side
        if q:                                                # her foot from above: a scalloped toe line, pale nails
            _q_foot_top(fc, med, curl, lw, detail, light)
        elif _bare_side(sp, side) or sp['outfit'] == 'dress':
            sk = QV['foot'] if q else sp['skin']; sh = QV['foot_sh'] if q else sp['skin_sh']
            tl = 0.5 - 0.04 * curl
            pts = [(-0.085, -0.5), (0.085, -0.5), (0.11, -0.3), (0.12 + 0.03 * med, -0.05), (0.17 + 0.02 * med, 0.2), (0.17, tl - 0.12),
                   (0.0, tl), (-0.17, tl - 0.12), (-0.17 + 0.02 * med, 0.2), (-0.12 + 0.03 * med, -0.05), (-0.11, -0.3)]
            ft = smooth([(px_, py_ * d) for px_, py_ in pts], True, 0.75)
            fc.fill(ft, sk)
            fc.grad(ft, 0, -0.5 * d, 0, 0.5 * d, [(0, sh, 180), (0.35, sk, 0), (0.85, sk, 0), (1, sh, 160)])
            fc.fill(_crescent(ft, 0.03 * med, 0), sh, 120)
            if q: fc.fill(_crescent(ft, -0.02 * med, 0), _ql(light)['rim'], 110)
            if detail >= 1:
                tnd = [smooth([(med * 0.02 * k, -0.2 * d), (med * (0.03 + 0.045 * k), 0.06 * d), (med * (0.04 + 0.06 * k), 0.24 * d)], False)
                       for k in (0.0, 1.5)]
                fc.line(_multi(tnd), lw * 0.28, QV['skin_dp'] if q else sp['skin_dp'], 90)
            # toes at the front: the big toe on the inner side, longer (1.2x) for her
            tk = 1.2 if q else 1.0
            for i in range(4, -1, -1):                       # little toe first, the big toe on top
                f = i / 4.0
                tx = med * lerp(0.105, -0.125, f); r_ = lerp(0.05, 0.027, f) * (0.86 if q else 1.0)
                L_ = r_ * ((3.0 if i == 0 else 2.7) if q else (2.3 if i == 0 else 2.0)) * tk * (1.0 - 0.22 * curl)
                ty = (tl - 0.06 - 0.05 * f ** 1.4) * d
                if q:                                        # long slim toes, splayed a little, a pale nail plate near the tip
                    spl = math.radians(-med * (4.0 + 7.0 * f))
                    toe = rrect(-r_, -L_ * 0.5, 2 * r_, L_, r_)
                    nh = L_ * 0.4
                    nl = rrect(-r_ * 0.66, L_ * 0.5 * d - (nh + r_ * 0.3 if d > 0 else -r_ * 0.3), r_ * 1.32, nh, r_ * 0.55)
                    m = skia.Matrix(); m.setRotate(math.degrees(spl)); m.postTranslate(tx, ty)
                    toe.transform(m); nl.transform(m)
                    fc.fill(toe, sk); fc.fill(_crescent(toe, 0.012 * med, 0), sh, 150); fc.line(toe, lw * 0.36, ln)
                    fc.fill(nl, QV['toenail'], 250); fc.line(nl, lw * 0.16, QV['toenail_edge'], 200)
                    b = nl.getBounds(); fc.fill(oval(b.centerX() - b.width() * 0.12, b.centerY(), b.width() * 0.12, b.height() * 0.22), QV['toenail_hi'], 190)
                    continue
                toe = rrect(tx - r_, ty - L_ * 0.5, 2 * r_, L_, r_)
                fc.fill(toe, sk); fc.fill(_crescent(toe, 0.01 * med, 0), sh, 120); fc.line(toe, lw * 0.38, ln)
                nh = L_ * 0.48
                nl = rrect(tx - r_ * 0.62, ty + d * L_ * 0.5 - (nh + r_ * 0.25 if d > 0 else -r_ * 0.25), r_ * 1.24, nh, r_ * 0.6)
                fc.fill(nl, mix(sk, '#ffffff', 0.45), 245)
            fc.line(ft, lw * 0.9, ln)
            if q and curl > 0.05:                            # the tread edge the toes curl over
                fc.line(poly([(-0.3, (tl - 0.06) * d), (0.3, (tl - 0.06) * d)], False), lw * 0.3, '#ff4060', 160 * curl)
        else:
            kind = 'boot' if sp['outfit'] in ('jacket', 'shell') else 'sneaker'
            shc = cl.get('shoes') or '#4a3426'; shs = cl.get('shoes_sh', mix(shc, '#000000', 0.3))
            pts = [(-0.15, 0.42), (0.15, 0.42), (0.16 + 0.02 * med, 0.0), (0.18 + 0.02 * med, -0.25), (0.13, -0.47), (0.0, -0.53),
                   (-0.13, -0.47), (-0.18 + 0.02 * med, -0.25), (-0.16 + 0.02 * med, 0.0)]
            sole = smooth([(px_ * 1.08, py_ * 1.03) for px_, py_ in pts], True, 0.75)
            fc.fill(sole, '#1f1712' if kind == 'boot' else cl.get('sole', '#cfc8b8')); fc.line(sole, lw * 0.8, ln)
            bt = smooth(pts, True, 0.75)
            fc.fill(bt, shc)
            fc.grad(bt, 0, -0.5, 0, 0.4, [(0, mix(shc, '#ffffff', 0.18), 200), (0.3, shc, 0), (1, shs, 200)])
            fc.fill(_crescent(bt, -0.03 * med, 0), shs, 150)
            fc.glow(0.02, -0.36, 0.07, 0.05, '#ffffff', 60)
            if detail >= 1:
                lc = '#2a2018' if kind == 'boot' else cl.get('lace', '#d8cfb8')
                lz = [poly([(-0.07, 0.05 - k * 0.08), (0.07, 0.01 - k * 0.08)], False) for k in range(4)] + \
                     [poly([(0.07, 0.05 - k * 0.08), (-0.07, 0.01 - k * 0.08)], False) for k in range(4)]
                fc.line(_multi(lz), lw * 0.45, lc)
                fc.line(smooth([(-0.15, -0.3), (0.0, -0.36), (0.15, -0.3)], False), lw * 0.35, shs, 200)       # toe-cap seam
            fc.line(bt, lw, ln)
            pc = cl.get('trousers', '#2a3347')                  # the trouser hem at the near edge
            leg = smooth([(-0.2, 0.9), (0.2, 0.9), (0.2, 0.3), (0.0, 0.32), (-0.2, 0.3)], True, 0.5)
            fc.fill(leg, pc); fc.fill(_crescent(leg, -0.04, 0), cl.get('trousers_sh', mix(pc, '#000000', 0.3)), 160)
            fc.line(leg, lw, ln)
        out['r' if side < 0 else 'l'] = c.pt(x + sx * size, y)
    if q and getattr(P, 'ft_hem', 1.0) >= 0.5:               # her hem round the ankles, rising out of frame toward you
        fc = c.sub(x, y, 0.0, size)
        lw = fc.lw
        sw = 0.02 * getattr(P, 'hem', 0.0)
        xs = np.linspace(-0.62, 0.62, 21)
        hp = [(float(xx) + sw, -0.3 + 0.03 * math.sin(xx * 10.0 + 0.7) - 0.05 * (1.0 - (xx / 0.62) ** 2)) for xx in xs]
        hem = smooth([(-0.62, -2.0), (0.62, -2.0)] + hp[::-1], True, 0.5)
        fc.fill(hem, QV['satin'])
        fc.grad(hem, -0.6, 0, 0.6, 0, [(0, QV['satin_sh'], 220), (0.35, QV['satin_sheen'], 220), (0.45, QV['satin_hi'], 140), (0.6, QV['satin'], 0),
                                      (1, QV['satin_sh'], 220)])
        b0 = [(px_, py_ - 0.03) for px_, py_ in hp]; b1 = [(px_, py_ - 0.14) for px_, py_ in hp]
        fc.line(smooth(b0, False), lw * 0.5, QV['hem_red']); fc.line(smooth(b1, False), lw * 0.5, QV['hem_red'])
        pp = skia.Path()
        for k in range(1, len(hp) - 1, 2): pp.addPath(_q_spade(hp[k][0], hp[k][1] - 0.085, 0.065, 0.056))
        fc.fill(pp, QV['pip'])
        fc.line(smooth(hp, False), lw, ln)
    return out


def _q_foot_top(fc, med, curl, lw, det, light):
    """The queen's bare foot seen from above, toes toward the viewer (+y), foot length 1: a narrow foot widening to the
    ball, five toes as one scalloped front edge (the big toe on the inner side `med`, longest; the second toe nearly as
    long), short creases between the toes, tendons, and small pale cold nails. Ash-white with lavender shade."""
    sk, sh = QV['foot'], QV['foot_sh']
    tl = 0.5 - 0.05 * curl
    spec = ((0.104, 0.047, tl + 0.02), (0.044, 0.034, tl + 0.012), (-0.012, 0.031, tl - 0.018), (-0.064, 0.028, tl - 0.052),
            (-0.11, 0.025, tl - 0.09))
    M = lambda x, y: (x * med, y)                                  # noqa: E731  canonical: the big toe at +x
    pts = [M(-0.085, -0.5), M(-0.108, -0.3), M(-0.128, -0.05), M(-0.142, 0.18), M(-0.138, spec[4][2] - 0.07)]
    notches = []
    for i in range(4, -1, -1):
        xc, r, yt = spec[i]
        for a in np.linspace(PI * 0.98, PI * 0.02, 7):
            pts.append(M(xc + math.cos(a) * r, yt - r * 1.25 + math.sin(a) * r * 1.25))
        if i > 0:
            xn = (xc + r + spec[i - 1][0] - spec[i - 1][1]) / 2.0
            yn = min(yt, spec[i - 1][2]) - r * 1.45
            pts.append(M(xn, yn)); notches.append((xn, yn, r))
    pts += [M(0.156, spec[0][2] - 0.08), M(0.166, 0.18), M(0.122, -0.05), M(0.108, -0.3), M(0.085, -0.5)]
    ft = smooth(pts, True, 0.55)
    fc.fill(ft, sk)
    fc.grad(ft, 0, -0.5, 0, 0.55, [(0, sh, 190), (0.35, sk, 0), (0.82, sk, 0), (1, sh, 120)])
    fc.fill(_crescent(ft, 0.03 * med, 0), sh, 130)
    fc.fill(_crescent(ft, -0.02 * med, 0), _ql(light)['rim'], 110)
    if det >= 1:
        tnd = [smooth([M(0.03 + 0.02 * k, -0.22), M(0.035 + 0.035 * k, 0.04), M(0.04 + 0.05 * k, 0.24)], False) for k in (0.0, 1.4, 2.6)]
        fc.line(_multi(tnd), lw * 0.26, QV['skin_dp'], 95)
        cr = [poly([M(xn, yn), M(xn + 0.004, yn - r * 1.6)], False) for xn, yn, r in notches]
        fc.line(_multi(cr), lw * 0.3, QV['inner'], 170)
        kn = [smooth([M(xc - r * 0.7, yt - r * 2.5), M(xc, yt - r * 2.75), M(xc + r * 0.7, yt - r * 2.5)], False) for xc, r, yt in spec[:3]]
        fc.line(_multi(kn), lw * 0.2, QV['skin_dp'], 110)
    fc.line(ft, lw * 0.9, QV['line'])
    nl = skia.Path()
    for xc, r, yt in spec:
        w_, h_ = r * 0.62, r * 0.82
        cx_, cy_ = M(xc, yt - r * 0.62)
        nl.addPath(rrect(cx_ - w_, cy_ - h_, 2 * w_, 2 * h_, w_ * 0.8))
    fc.fill(nl, QV['toenail'], 250)
    if det >= 1:
        fc.line(nl, lw * 0.16, QV['toenail_edge'], 210)
        hl = skia.Path()
        for xc, r, yt in spec[:3]:
            cx_, cy_ = M(xc - r * 0.18, yt - r * 0.85)
            hl.addOval(skia.Rect.MakeLTRB(cx_ - r * 0.1, cy_ - r * 0.22, cx_ + r * 0.1, cy_ + r * 0.22))
        fc.fill(hl, QV['toenail_hi'], 200)
    if curl > 0.05:                                                # the tread edge the toes curl over
        fc.line(poly([(-0.3, tl - 0.06), (0.3, tl - 0.06)], False), lw * 0.3, '#ff4060', 160 * curl)


def _mirror_x(path):
    q = skia.Path(path); m = skia.Matrix(); m.setScale(-1, 1); q.transform(m); return q


def draw_legs(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, cut=0.5):
    """Lower-body crop (mode 'legs'): the full figure clipped below `cut` of its height (0.5 = the waist; hands that
    come down to the hips, e.g. dropping the bell, still show)."""
    cv = pen.cv; cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(-1e5, y_feet - cut * height, 1e5, 1e5))
    try: return draw(pen, who, x, y_feet, height, pose, detail, light, t)
    finally: cv.restore()


def draw_silhouette(pen, who, x, y_feet, height, pose=None, light=None, t=None, fill='#05070b', rim=None, rim_a=170, side=1, detail=0):
    """Dark shape with a rim light only (mode 'silhouette'): the figure drawn twice through a colour filter (rim colour
    shifted toward the light, then the fill on top)."""
    if who == 'queen':                                  # v2: she is always lit; far shots darken the dress, never the face
        return draw(pen, who, x, y_feet, height, pose, detail, light, t)
    light = _light_dict(light) or {}
    rim = rim or light.get('rim', '#9fb6ff'); side = light.get('side', side)
    cv = pen.cv
    off = max(1.2, height * 0.006)
    for colr, a, dx in ((rim, rim_a, side * off), (fill, 255, 0.0)):
        cv.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(col(colr, a), skia.BlendMode.kSrcIn)))
        try: draw(pen, who, x + dx, y_feet, height, pose, detail, None, t)
        finally: cv.restore()


def draw_lying(pen, who, x, y, size, pose=None, detail=None, light=None, t=None, facing=1, blanket=None, hang_arm=False):
    """In a bunk (mode 'lying'): the figure on its back, head to screen left (facing=1) or right, head on a pillow, a
    sleeping bag / blanket over the body; (x, y) = body centre, size = body length (crown to feet) in design px.
    hang_arm: the right arm hangs off the bunk edge (Noah's watch wrist, S040)."""
    P = _as_pose(pose); t = P.t if t is None else t
    sp = _resolve_sp(who, P)
    s_ = size / 1000.0
    det = _auto_detail(pen, sp['hh'] * s_) if detail is None else detail
    rot = -90.0 if facing > 0 else 90.0
    cv = pen.cv
    light = _light_dict(light)
    bl = blanket or {'noah13': ('#3e5a7a', '#2c425c'), 'you_kid': ('#7a3a34', '#572822')}.get(who, ('#5a6a4a', '#3e4a32'))
    with _lit(pen, light, x - facing * size * 0.4, y, size * 0.5, (x, y + size * 0.2)) as l2:
        c0 = Ctx(pen, skia.Matrix(), _lw_for(sp['hh'] * s_), _sty_for(sp, t))
        pill = smooth([(x - facing * size * 0.58, y - size * 0.1), (x - facing * size * 0.28, y - size * 0.12), (x - facing * size * 0.26, y + size * 0.1),
                       (x - facing * size * 0.6, y + size * 0.1)], True, 0.8)
        c0.fill(pill, '#e9e4da'); c0.fill(_crescent(pill, 0, -size * 0.03), '#b8b2a6', 160); c0.line(pill, c0.lw)
        c = c0.sub(x + facing * 500.0 * s_, y, rot, s_)
        P2 = P.copy(); P2.h_turn += 0.0
        B = _figure(c, who, P2, det, t, l2)
        # blanket from the chest to past the feet
        b = sp['body']
        br = (P.breath - 0.5) * 6.0
        pts = []
        for yb, wb in ((B.y_ch - 30, b['ch'] * 1.35 + br), (B.y_wa, b['wa'] * 1.45 + br), (-300.0, b['hip'] * 1.3), (-20.0, b['hip'] * 1.15)):
            pts.append((wb, yb))
        poly_ = [(-p[0], p[1]) for p in pts] + [(p[0], p[1]) for p in pts[::-1]]
        bk = smooth(poly_, True, 0.6)
        c.fill(bk, bl[0]); _cloth_shade(c, bk, bl[1], 170, 1.0, 40)
        if det >= 1:
            c.line(_multi([smooth([(-b['ch'] * 1.1, B.y_wa + 60 * q), (0, B.y_wa + 60 * q + 18), (b['ch'] * 1.1, B.y_wa + 60 * q)], False) for q in range(4)]),
                   c.lw * 0.4, bl[1], 200)
        top = smooth([(-b['ch'] * 1.38 - br, B.y_ch - 30), (b['ch'] * 1.38 + br, B.y_ch - 30), (b['ch'] * 1.38 + br, B.y_ch + 20), (-b['ch'] * 1.38 - br, B.y_ch + 20)], True, 0.4)
        c.fill(top, mix(bl[0], '#ffffff', 0.25)); c.line(top, c.lw * 0.8)
        c.line(bk, c.lw)
        if hang_arm:
            sx, sy = c.pt(-b['sh'] + 10, B.y_sh + 30)
            wy = sy + size * 0.2 + 2 * math.sin(t * 1.6)
            arm = _tube([(sx, sy), (sx + 4, wy)], [b['arm'][0] * s_, b['arm'][1] * s_])
            skin, sh, _ = _skin_cols(sp, P, None)
            c0.fill(arm, sp['cloth']['top']); c0.line(arm, c0.lw)
            _prop2(c0.sub(sx + 4, wy - size * 0.03, 0, size / 900.0), 'watch', det, t)
            _draw_hand(c0, sp, 'relaxed', sx + 4, wy, s_ * 1.6, 0.0, -1, det, skin, sh, False, 0.0, t)
    return B


# ====================================================================================================== Mirror Steps: acting clips
def _wnd(t, t0, t1, fin=0.25, fout=0.3, e=ease):
    return _env(t, t0, t1, fin, fout, e, e)


class _MirrorClips:
    """Acting clips for the Mirror Steps cast (mixed into Acting). Every clip works in full body, bust and the hands /
    feet inserts: it drives the rig's arm targets (hl_* / hr_*: character's left / right) AND the insert fields
    (ir_* main hand, il_* second hand, base_prop, fl_* / fr_* feet). Clips that make a sound return their events
    (names from plan/sound_plan.json); the others return the Acting (chainable)."""

    # -------------------------------------------------------------- helpers
    def _ins(self, P, nm, w, **kv):
        P.mix({'i%s_%s' % (nm, k): v for k, v in kv.items()}, w)

    def _sh(self):
        return self.sp['body']['sh'] - 17

    def _ev2(self, t, name, gain_db=-6.0, pan=0.0, **params):
        return self._ev(t, name, gain_db, pan, **params)

    # -------------------------------------------------------------- speech and faces
    def talk_line(self, t0, line=None, intensity=1.0):
        """Lip-sync one timeline.json line (talk(line=i) in the plan) on the real voice envelope. Noah (13 and grown)
        shows his gap teeth on every spoken line (DIRECTION_V2 3.7)."""
        L = timeline_line(line)
        if self.who in ('noah13', 'noah_grown') and L and L.get('end'):
            t_a, t_b = L['t'], L['end']
            self._add(t_a - 0.1, t_b + 0.3, lambda P, t: setattr(P, 'teeth', max(P.teeth, 0.75 * _env(t, t_a - 0.08, t_b + 0.05, 0.08, 0.2))))
        if L and L.get('end'):
            return self.talk([(L['t'], L['end'], L.get('en'))], intensity=intensity)
        return self.talk([(t0, t0 + 1.2, None)], intensity=intensity, env=None, words=None)

    def talk_silent(self, t0, dur=1.2, intensity=0.6):
        """Soft mouth motion with no audio (speech the narrator only describes)."""
        return self.talk([(t0, t0 + dur, None)], intensity=intensity, env=None, words=None)

    def shout_silent(self, t0, dur=0.8):
        self.expr('shout', t0, t0 + dur, 0.08)
        return self.talk([(t0, t0 + dur, None)], intensity=1.2, env=None, words=None)

    def mouth_open(self, t0, dur=0.7, amount=0.5):
        return self.set(t0, t0 + dur, 0.12, m_open=amount, m_round=0.4)

    def mouth_open_close(self, t0, dur=0.8):
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.m_open = max(P.m_open, 0.5 * math.sin(PI * u) ** 0.7); P.m_round = max(P.m_round, 0.4 * math.sin(PI * u))
        return self._add(t0, t0 + dur, fn)

    def whistle_s(self, t0, dur=0.35):
        """Noah's gap-tooth whistle on an 's': teeth together (the gap shows), lips slightly rounded."""
        return self.set(t0, t0 + dur, 0.06, teeth=1.0, m_open=0.08, m_round=0.3, m_wide=0.3)

    def smile(self, t0, amount=0.6, dur=0.5, t1=None):
        return self.set(t0, t1, dur, smile=amount, teeth=0.4 * amount)

    def half_smile(self, t0, dur=1.2):
        return self.expr('half_smile', t0, t0 + dur, 0.3)

    def laugh(self, t0, dur=1.5):
        self.expr('laugh', t0, t0 + dur, 0.2)
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.15, 0.35)
            P.shrug += 0.18 * w * abs(math.sin((t - t0) * 9.0)); P.h_nod += 0.05 * w * math.sin((t - t0) * 9.0)
            P.m_open += 0.15 * w * abs(math.sin((t - t0) * 9.0))
        self._add(t0, t0 + dur + 0.4, fn)
        return [self._ev2(t0 + 0.05, 'breath', -12.0, kind='laugh', dur=dur)]

    def laugh_dies(self, t0, dur=1.4):
        """A laugh that dies in the throat: grin and shoulder bobs fade into a tense, closed face."""
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            w = _wnd(t, t0, t0 + dur, 0.1, 0.6)
            k = (1.0 - ease_in_out(u))
            P.mix(dict(smile=0.7 * k, teeth=0.6 * k, squint=0.35 * k, m_open=0.18 * k * abs(math.sin((t - t0) * 8.0))), w)
            P.mix(dict(brow_sad=0.5, m_press=0.5), w * ease_in_out(u))
            P.shrug += 0.12 * w * k * abs(math.sin((t - t0) * 8.0))
        self._add(t0, t0 + dur + 0.6, fn)
        return [self._ev2(t0, 'breath', -14.0, kind='laugh_short')]

    def tears(self, t0, amount=1.0, dur=2.0, t1=None):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur)) * amount
            w = 1.0 if t1 is None else 1.0 - prog(t, t1, t1 + 0.8)
            P.tears = max(P.tears, u * w); P.wet = max(P.wet, min(1.0, 0.5 + u) * w * (1.0 if t >= t0 else 0.0))
            P.brow_sad = max(P.brow_sad, 0.6 * u * w)
        return self._add(t0, None if t1 is None else t1 + 0.8, fn)

    def swallow(self, t0):
        def fn(P, t):
            k = math.sin(PI * prog(t, t0, t0 + 0.45))
            P.h_nod += 0.05 * k; P.shrug += 0.08 * k; P.m_press = max(P.m_press, 0.6 * k)
        self._add(t0, t0 + 0.5, fn)
        return [self._ev2(t0 + 0.12, 'breath', -20.0, kind='swallow')]

    def tremble(self, t0, amount=0.6, t1=None, fade=0.4):
        """Shaking: lips, head shiver and hands (pose.hshake) - grown Noah, you at the glass."""
        return self.set(t0, t1, fade, tremble=amount, hshake=amount)

    def face_flash(self, t0, dur=0.5, flicker=True, to='noah_grown'):
        """S165: for half a second Noah's face is grown Noah's, entered and left with 2-frame flickers."""
        fl = [t0 - 0.1, t0 - 0.067, t0 + dur + 0.05, t0 + dur + 0.083] if flicker else []
        def fn(P, t):
            on = t0 <= t < t0 + dur
            for a in fl[::2]:
                if a <= t < a + 0.034: on = True
            P.face_flash = 1.0 if on else 0.0
        return self._add(t0 - 0.2, t0 + dur + 0.2, fn, real=True)

    def look_at(self, t0, x, y, head_xy=(960.0, 400.0), dur=0.15, lost=False, t1=None):
        """Look at a design-space point (the plan's look {x, y}); head follows a quarter of the way. lost=True: the
        eyes drift unfocused instead."""
        hx, hy = head_xy
        lx = clamp((x - hx) / 520.0, -1, 1); ly = clamp((y - hy) / 420.0, -1, 1)
        def fn(P, t):
            w = _wnd(t, t0, t1, dur, 0.3)
            if w <= 0: return
            dx = 0.08 * noise1(t * 0.3, self.seed + 61) if lost else 0.0
            P.look_x = lerp(P.look_x, lx * 0.85 + dx, w); P.look_y = lerp(P.look_y, ly * 0.7, w)
            P.lock = lerp(P.lock, 0.0, w); P.h_turn += 0.22 * lx * w; P.h_nod += 0.1 * ly * w
            if lost: P.eye_open = min(P.eye_open, 0.85)
        return self._add(t0, None if t1 is None else t1 + 0.3, fn)

    def nod(self, t0, n=2, period=0.45):
        def fn(P, t):
            u = (t - t0) / period
            if 0 <= u <= n: P.h_nod += 0.09 * math.sin(PI * (u % 1.0)) * (1 if u < n else 0)
        return self._add(t0, t0 + n * period + 0.1, fn)

    def head_lift(self, t0, amount=1.0, dur=0.6):
        return self.set(t0, None, dur, h_nod=-0.12 * amount, look_y=-0.25 * amount)

    def look_up(self, t0, dur=0.5, t1=None):
        """He rarely looks up; when he does: head lifts, eyes up, a warm gap-tooth smile grows."""
        def fn(P, t):
            w = _wnd(t, t0, t1, dur, 0.5, ease_in_out)
            P.h_nod -= 0.14 * w; P.look_y = lerp(P.look_y, -0.3, w); P.lock = lerp(P.lock, 0.6, w)
            sk = ease_in_out(prog(t, t0 + 0.2, t0 + 0.9))
            P.smile = max(P.smile, 0.6 * w * sk); P.teeth = max(P.teeth, 0.9 * w * sk); P.m_open = max(P.m_open, 0.1 * w * sk)
        return self._add(t0, None if t1 is None else t1 + 0.5, fn)

    # -------------------------------------------------------------- body moves
    def stand_up(self, t0, dur=0.9, frm='sit'):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if frm == 'sit': P.sit = lerp(P.sit, 1.0, 1.0 - u)
            else: P.crouch = lerp(P.crouch, 1.0, 1.0 - u)
            P.lean += 0.25 * math.sin(PI * u)
        self._add(-INF, t0 + dur, fn)
        return [self._ev2(t0 + 0.1, 'bed_creak', -12.0)] if frm == 'sit' else self

    def kneel(self, t0, dur=0.6, t1=None):
        self.set(t0, t1, dur, crouch=0.75, kneel=1.0, lean=0.15)
        return [self._ev2(t0 + dur * 0.8, 'wood_thud', -12.0, kind='knee')]

    def step_back(self, t0, dur=0.45, dist=0.12):
        d = dist * self.height
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.dx -= d * u; P.lean -= 0.08 * math.sin(PI * u); P.fr_up += 40.0 * math.sin(PI * u)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.8, 'footsteps_wood_inside', -6.0, n=1)]

    def fall_back(self, t0, dur=0.6):
        d = 0.22 * self.height
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.dx -= d * u; P.lean -= 0.3 * u; P.sit = max(P.sit, 0.8 * ease_in_cubic(prog(t, t0 + 0.15, t0 + dur)))
            for side in (-1, 1): self._arm(P, side, math.sin(PI * min(1.0, u * 1.3)), 160.0, 120.0, 60.0, 'open', up=0.0)
            P.wide = max(P.wide, 0.8 * u); P.m_open = max(P.m_open, 0.3 * math.sin(PI * u))
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.85, 'body_fall', -3.0)]

    def stumble(self, t0, to=None, dur=0.7):
        d = 0.15 * self.height
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.dx += d * ease_out_cubic(u); P.lean += 0.3 * math.sin(PI * u); P.fr_up += 90.0 * math.sin(PI * min(1.0, u * 2))
            for side in (-1, 1): self._arm(P, side, math.sin(PI * u), 120.0, 160.0, 140.0, 'open', up=0.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.5, 'bare_foot_step', -4.0), self._ev2(t0 + dur * 0.9, 'footsteps_wood_inside', -6.0, n=1)]

    def run(self, t0, to=None, t1=None, x_from=None, surface='porch', step=0.27):
        """A run cycle (DIRECTION_V2 3.7): 0.27 s per step, a flight phase, knees high, the body leaning in, the arms
        pumping at 90 deg elbows opposite the legs (the flashlight beam swings with the right hand), the ponytail lagging."""
        x_from = 0.0 if x_from is None else x_from
        t1 = t0 + 1.2 if t1 is None else t1
        to = x_from + 0.8 * self.height if to is None else to
        ev = self.walk(t0, t1, x_from, to, surface=surface, ramp=0.15)
        def fn(P, t):
            w = _wnd(t, t0, t1, 0.2, 0.3)
            ph = (t - t0) / (2.0 * step)
            P.walk_ph = lerp(P.walk_ph, ph, w); P.run = max(P.run, w); P.walk_amt = max(P.walk_amt, w)
            P.lean += 0.3 * w
            for side in (-1, 1):
                sw = math.cos(2 * PI * ph + (0.0 if side > 0 else PI))
                self._arm(P, side, w * 0.9, 34.0, 150.0 - 30.0 * sw, 150.0 * sw, 'fist' if not getattr(P, 'hr_prop' if side < 0 else 'hl_prop') else None, up=0.0)
            P.h_nod += 0.04 * w * math.sin(4 * PI * ph)
        self._add(t0, t1 + 0.3, fn, real=True)
        n = int((t1 - t0) / step)
        return [self._ev(t0 + step * (k + 0.5), 'footsteps_run', -2.0, foot='L' if k % 2 else 'R') for k in range(n)]

    def sneak(self, t0, t1):
        return self.set(t0, t1, 0.4, crouch=0.25, lean=0.18, hunch=0.4)

    def scoot(self, t0, dx=40.0, dur=0.5):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.dx += dx * u; P.bob -= 6.0 * math.sin(PI * u)
            for side in (-1, 1): self._arm(P, side, math.sin(PI * u), -20.0, 300.0, 60.0, 'flat', up=0.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.1, 'bed_creak', -8.0)]

    def rock(self, t0, period=1.6, t1=None, amount=1.0):
        def fn(P, t):
            w = _wnd(t, t0, t1, 0.6, 0.6)
            P.lean += 0.12 * amount * w * math.sin(2 * PI * (t - t0) / period); P.h_nod += 0.05 * w * math.sin(2 * PI * (t - t0) / period + 0.6)
        return self._add(t0, None if t1 is None else t1 + 0.6, fn)

    def shift_weight(self, t0, dur=1.2):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur)); P.sway += 10.0 * math.sin(PI * u); P.tilt += 2.5 * math.sin(PI * u)
        return self._add(t0, t0 + dur, fn)

    def squeeze_through(self, t0, amount=1.0, dur=1.0):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.turn += 0.6 * amount * math.sin(PI * min(1.0, u * 1.2)); P.crouch += 0.3 * amount * math.sin(PI * u)
            P.lean += 0.25 * amount * math.sin(PI * u); P.dx += 0.25 * self.height * u * amount
            self._arm(P, 1, math.sin(PI * u), 100.0, -60.0, 300.0, 'flat', up=1.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.2, 'jacket_cloth', -8.0), self._ev2(t0 + dur * 0.7, 'whoosh', -14.0, kind='soft')]

    def step_over(self, t0, height=0.4, dur=0.7):
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.fr_up += 400.0 * height * math.sin(PI * u); P.fr_fwd += 260.0 * ease_in_out(u) - 260.0 * ease_in_out(prog(t, t0 + dur, t0 + dur + 0.5))
            P.dx += 0.12 * self.height * ease_in_out(u); P.lean += 0.08 * math.sin(PI * u)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.95, 'footsteps_porch', -4.0, n=1)]

    def step_through(self, t0, foot='bare', dur=0.7):
        """Noah's bare foot crosses the threshold: in the feet insert the foot lifts, moves forward and plants;
        in full body a big step forward."""
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.fr_up += 0.18 * math.sin(PI * u); P.fr_fwd += 0.5 * ease_in_out(u) - 0.5
            P.dx += 0.15 * self.height * ease_in_out(u)
        self._add(t0 - 0.3, None, fn)
        return [self._ev2(t0 + dur * 0.92, 'bare_foot_step', -4.0)]

    def fall_through(self, t0, dur=0.6):
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.lean += 0.45 * ease_in_cubic(u); P.dx += 0.3 * self.height * ease_in_cubic(u); P.dy += 0.08 * self.height * ease_in_cubic(u)
            for side in (-1, 1): self._arm(P, side, min(1.0, u * 2), 140.0, -40.0, 260.0, 'open', up=0.5)
            P.wide = max(P.wide, 0.8); P.m_open = max(P.m_open, 0.5 * u)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur, 'body_fall', -2.0)]

    def climb(self, t0, steps_per_s=0.8, t1=None, rise=0.17, run=0.22, dirx=1.0):
        """The queen climbs the stairs: one tread per 1/steps_per_s s, dx/dy move by run/rise x height per step,
        a slow walk cycle in place, the hem swaying. Events: bare_foot_step per tread."""
        t1 = t0 + 4.0 if t1 is None else t1
        per = 1.0 / max(0.05, steps_per_s)
        def fn(P, t):
            n = (t - t0) / per
            k = math.floor(n); f = ease_in_out(n - k)
            pos = k + f
            P.dx += dirx * run * self.height * pos; P.dy -= rise * self.height * pos
            P.walk_amt = max(P.walk_amt, 0.55); P.walk_ph = 0.5 * pos
            P.hem = math.sin(pos * PI)
        self._add(t0, t1, fn, real=True)
        return [self._ev2(t0 + per * (i + 0.6), 'bare_foot_step', -10.0) for i in range(int((t1 - t0) / per) + 1)]

    def step_up(self, t0, foot='right', dur=1.1):
        """Feet insert: a pale bare foot comes up out of the dark onto the step (the other foot not shown)."""
        nm = 'fr_' if foot != 'left' else 'fl_'
        ts = t0 - dur * 0.8                                   # the plan time is the landing
        def fn(P, t):
            u = ease_out_cubic(prog(t, ts, ts + dur))
            setattr(P, nm + 'up', getattr(P, nm + 'up') - 0.55 * (1.0 - u))
            setattr(P, nm + 'fwd', getattr(P, nm + 'fwd') + 0.3 * (1.0 - u))
            P.toes = max(P.toes, 0.3 * math.sin(PI * u))
            if foot != 'left': P.ft_l = 0.0
            else: P.ft_r = 0.0
        self._add(-INF, None, fn)
        return [self._ev2(ts + dur * 0.85, 'bare_foot_step', -8.0)]

    def lift_foot(self, t0, to=0.3, dur=1.4):
        """The queen lifts her foot, slowly, toward a step (to = lift in units of the feet insert size)."""
        to = to if isinstance(to, (int, float)) else 0.3
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.fr_up += to * u; P.fr_point += 0.3 * u; P.toes = max(P.toes, 0.2 * u)
            P.fl_up += 0.03 * self.height / 1000.0 * u
        return self._add(t0, None, fn)

    def toes_curl(self, t0, dur=0.9, t1=None):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.toes = max(P.toes, u * (0.9 + 0.1 * math.sin((t - t0) * 3.0)))
        return self._add(t0, None if t1 is None else t1, fn, real=True)

    def hem_sway(self, t0, t1=None, amount=1.0):
        """The dress hem moves though she does not (wrong)."""
        return self._add(t0, None if t1 is None else t1, lambda P, t: setattr(P, 'hem', amount * math.sin((t - t0) * 1.3)), real=True)

    # -------------------------------------------------------------- the queen
    def still(self, t0, t1=None):
        """Uncanny stillness: no breathing, no blinks, no drift (only snaps move her)."""
        def fn(P, t):
            P.still = 1.0; P.life = 0.0; P.breath = 0.5
        return self._add(t0, None if t1 is None else t1, fn, real=True)

    def head_snap(self, t0, deg=130.0, dur=0.18, hold=None):
        """Head snaps by deg (yaw) in dur (3-4 frames at 60 fps) with a 2-frame overshoot, then holds."""
        q = deg / 90.0
        def fn(P, t):
            if t < t0: return
            u = ease_in_cubic(prog(t, t0, t0 + dur * 0.7))
            ov = 0.08 * q * math.exp(-max(0.0, t - t0 - dur * 0.7) * 22.0) * (1.0 if t > t0 + dur * 0.7 else 0.0)
            P.h_turn += q * u + ov
            P.h_tilt += 6.0 * math.sin(PI * prog(t, t0, t0 + dur))
        self._add(t0 - 0.1, None if hold is None else hold, fn, late=True, real=True)
        return [self._ev2(t0, 'whoosh', -16.0, kind='snap')]

    def smile_off(self, t0, dur=0.033):
        """Her smile goes off her face in 2 frames: grin, teeth and smear drop to a blank stare."""
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            if u <= 0: return
            for k_ in ('smile', 'grin', 'teeth', 'gums', 'smear', 'm_open'):
                setattr(P, k_, getattr(P, k_) * (1.0 - u))
            P.mix(EXPR['queen_blank'], u)
            P.q_off = max(P.q_off, u)
        return self._add(t0 - 0.01, None, fn, late=True, real=True)

    def call_silent(self, t0, dur=1.2):
        """Mouth wide open, calling without sound: the jaw drops past natural, the head tips back."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur * 0.5))
            w = _wnd(t, t0, t0 + dur, 0.01, 0.4)
            P.mix(EXPR['queen_call'], w * u); P.h_nod -= 0.12 * u * w; P.m_open = max(P.m_open, 1.0 * u * w)
        return self._add(t0, t0 + dur + 0.4, fn)

    def stage(self, t0, to='S3a', dur=0.08, draw_on=False):
        """Queen v2: change stage at t0 (DIRECTION_V2 3.3). Every q_* parameter moves to the target stage over dur
        (0.033 = a 2-frame snap); draw_on=True draws the lipstick steps on instead (q_draw 0 -> 1 over dur)."""
        tgt = queen_stage(to)
        def fn(P, t):
            u = prog(t, t0, t0 + max(dur, 1e-3))
            if u <= 0: return
            for k_, v in tgt.items():
                if draw_on and k_ == 'q_draw': v = v * u
                setattr(P, k_, lerp(getattr(P, k_), v, 1.0 if (draw_on and k_ == 'q_draw') else u))
        return self._add(t0 - 0.01, None, fn, late=True, real=True)

    def split_open(self, t0, dur=0.12):
        """S3a: the drawn smile splits open into the grin of teeth (on "back", 479.24)."""
        return self.stage(t0, 'S3a', dur)

    def eyes_red(self, t0, dur=0.2):
        """S3b: the irises turn red (on "better", 496.8)."""
        return self.stage(t0, 'S3b', dur)

    def full_face(self, t0, dur=0.25):
        """S3c: folds, cracks and black tears join the grin and the red eyes (531.7)."""
        return self.stage(t0, 'S3c', dur)

    def jaw_drop(self, t0, dur=0.3, glitch=1.0):
        """S4: the jaw drops into a void, the face below the eyes stretches 1.35x, Noah13's face glitches inside it."""
        self.stage(t0, 'S4', dur)
        def fn(P, t):
            if t >= t0: P.q_glitch = max(P.q_glitch, glitch * (0.6 + 0.4 * (hash01(int(t * 20), 919) > 0.5)))
        self._add(t0, None, fn, late=True, real=True)
        return [self._ev2(t0, 'glitch', -10.0, kind='pixel')]

    def draw_smile(self, t0, dur=0.9):
        """S2 drawn on camera: the lipstick steps draw themselves up her cheeks."""
        return self.stage(t0, 'S2', dur, draw_on=True)

    def head_to_lens(self, t0, deg=None, dur=0.25):
        """Her head tilts / turns to the lens in 0.25 s (snap mode), then holds; eyes locked."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.h_turn *= 1.0 - u; P.turn *= 1.0 - u * 0.6; P.h_tilt *= 1.0 - 0.7 * u; P.lock = max(P.lock, u)
        return self._add(t0 - 0.01, None, fn, late=True, real=True)

    # -------------------------------------------------------------- v2 plan vocabulary (plan/shotlist.py act names)
    def grin_widen(self, t0, amount=0.2, dur=0.6):
        """S3c: the grin widens a little more (H7, 606.2; the flash-forward at 0.0)."""
        return self._add(t0, None, lambda P, t: setattr(P, 'q_widen', max(P.q_widen, amount * ease_in_out(prog(t, t0, t0 + dur)) * 2.5)), real=True)

    def drift(self, t0, t1=None, amount=1.0):
        """Her slow drift made explicit (it is always on): a slightly larger tilt and lean wander, never pixel-identical."""
        sd = self.seed * 7 + 91
        def fn(P, t):
            P.h_tilt += 1.6 * amount * noise1(t * 0.18, sd); P.lean += 0.01 * amount * noise1(t * 0.11, sd + 1)
            P.hem += 0.3 * amount * math.sin(t * 1.1)
        return self._add(t0, t1, fn, real=True)

    def slide_rail(self, t0, dx=60.0, dur=0.8):
        """She glides along the stair railing, her red-fingertip hand on the rail (dx in design px)."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.dx += dx * u
            self._arm(P, 1, 1.0, 70.0, 240.0, 60.0, 'relaxed', up=0.0)
        return self._add(t0, None, fn)

    def fingers_curl(self, t0, amount=0.3, dur=0.8):
        """Hands insert: her long fingers curl slowly (no other motion)."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur)) * amount
            self._ins(P, 'r', 1.0, shape=shape_mix('relaxed', 'claw', u / 0.36), a=lerp(P.ir_a, 175.0, 0.3))
        return self._add(t0, None, fn)

    def rise(self, t0, dy=None, dur=0.9):
        """Something pale rises into the frame (bust: dy design px, default -40) / she straightens up out of the
        window corner (body: from a slight stoop, default 6 % of her height)."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            d = dy if dy is not None else -0.06 * self.height
            P.dy += d * u - d; P.hunch += 0.3 * (1.0 - u)
        return self._add(t0 - 0.01, None, fn)

    def lean_out(self, t0, dur=0.6, dist=160.0):
        """H1: she leans out of the doorway into the light (bust): in from the frame side, the face growing a little."""
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.dx += dist * (1.0 - u); P.approach = max(P.approach, 0.18 * u); P.h_tilt -= 7.0 * (1.0 - u)
        return self._add(t0 - 0.01, None, fn)

    def glide_sit(self, t0, to=None, dur=1.2, bob=0.0):
        """H2: one smooth eased 1.2 s glide from where she stands to the bunk (`to` = [x, y_feet, h] design px), the
        bend at the hip and the sit at the end; no bob, the hair stays put."""
        to = to if isinstance(to, (list, tuple)) and len(to) >= 2 else None
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if to is not None and getattr(self, '_at', None):
                ax, ay, ah = self._at
                P.dx += (to[0] - ax) * u; P.dy += (to[1] - ay) * u
            P.sit = max(P.sit, ease_in_out(prog(t, t0 + dur * 0.35, t0 + dur)))
            for side in (-1, 1): self._arm(P, side, ease_in_out(prog(t, t0 + dur * 0.5, t0 + dur)), -40.0, 290.0, 150.0, 'relaxed', up=0.0)
        self._add(t0, None, fn, real=True)
        return [self._ev2(t0 + dur, 'bed_creak', -10.0, kind='slow')]

    def smile_split(self, t0, dur=0.25):
        """S3a on "back" (479.24): the drawn stair smile splits open into the grin of teeth."""
        return self.stage(t0, 'S3a', dur)

    def turn_to_lens(self, t0, dur=0.25):
        """She turns her face to the lens (531.9; snap mode, 0.25 s), the eyes locked."""
        return self.head_to_lens(t0, dur=dur)

    def climb_step(self, t0, to=None, dur=0.9, rise=0.1, run=0.13, dirx=1.0):
        """One tread up the stairs (body): the hem lifts, a bare foot steps, she rises by one tread."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.dx += dirx * run * self.height * u; P.dy -= rise * self.height * u
            P.fr_up += 0.25 * math.sin(PI * u); P.hem += 0.6 * math.sin(PI * u)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.7, 'bare_foot_step', -8.0)]

    def void_talk(self, t0, line=None, inner='noah13', pixel_sort=True, dur=0.3):
        """S4: the jaw drops into the void and Noah13's face inside speaks the line (his voice: line 249), glitching."""
        ev = self.jaw_drop(t0, dur, 1.0 if pixel_sort else 0.0)
        if line is not None: self.talk_line(t0, line)
        else: self.talk_silent(t0, 1.0, 0.35)
        return ev

    def reach_shoulder(self, t0, dur=0.7, side=1):
        """H7: her long hand rises toward your shoulder (at the lens), fingers curling."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            self._arm(P, side, u, 40.0, 60.0, 380.0, 'claw' if u > 0.5 else 'reach', up=0.7)
            self._ins(P, 'r', u, shape='claw', a=160.0, y=-0.3 * (1 - u))
            P.ins_k = max(P.ins_k, 1.0 + 0.3 * u)
        return self._add(t0, None, fn)

    def pixel_sort_in(self, t0, dur=0.3):
        """The phone (697.95): Noah13's face (speaking line 299) pixel-sorts into her S3c face looking into the lens."""
        def fn(P, t):
            P.q_nface = 1.0 - prog(t, t0, t0 + dur); P.q_glitch = max(P.q_glitch, math.sin(PI * prog(t, t0 - 0.05, t0 + dur + 0.05)))
            P.lock = 1.0
        self._add(-INF, None, fn, real=True)
        return [self._ev2(t0, 'glitch', -8.0, kind='pixel')]

    def hang_open(self, t0, prop='padlock', dur=1.0):
        """Tess unhooks the padlock and hangs it open on the hasp (71.6 s)."""
        return self.unlock(t0, prop, dur)

    def whisper(self, t0, dur=0.7):
        """A whispered name (the kids' dare): the whisper face and soft mouth motion."""
        self.expr('whisper', t0, t0 + dur, 0.15)
        return self.talk_silent(t0, dur, 0.35)

    def shrug(self, t0, dur=0.7):
        def fn(P, t):
            w = math.sin(PI * prog(t, t0, t0 + dur))
            P.shrug += 0.9 * w; P.brow_up += 0.3 * w
            for side in (-1, 1): self._arm(P, side, w, 70.0, 230.0, 90.0, 'open', up=0.0)
        return self._add(t0, t0 + dur + 0.2, fn)

    def wrap_tape(self, t0, dur=1.6):
        """Mom's hands wind the blue tape round three small fingers (memory insert, 218.2 s)."""
        def fn(P, t):
            ph = (t - t0) * 2.6
            self._ins(P, 'r', 1.0, shape='pinch', a=200.0, x=0.12 * math.cos(ph * 2 * PI), y=0.08 * math.sin(ph * 2 * PI))
            P.base_prop = 'tape_ring'
        return self._add(t0, t0 + dur, fn)

    def step_down(self, t0, dur=0.5):
        """Your boot comes down on tread 1 (feet insert; in the POV view it lowers into place)."""
        def fn(P, t):
            u = ease_out_cubic(prog(t - 0.0, t0 - 0.2, t0 + dur - 0.2))
            P.fr_up += 0.3 * (1.0 - u); P.fr_fwd += 0.1 * (1.0 - u)
        self._add(t0 - 0.5, None, fn)
        return [self._ev2(t0 + dur * 0.6, 'footsteps_wood_inside', -6.0, n=1)]

    def write(self, t0, dur=1.2):
        """An officer writes in his notebook (memory)."""
        return self.hold_up('notebook', t0, t0 + dur, -1)

    def reach_grab(self, t0, foreshortened=True, dur=0.25):
        """Tess's orange arm comes at the lens out of the doorway (foreshortened) and the hand closes (551.9, 608.3)."""
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            if foreshortened: P.ir_fore = max(P.ir_fore, u)
            self._ins(P, 'r', 1.0, shape='fist' if u > 0.75 else 'claw', a=lerp(-25.0, 6.0, u), y=lerp(-1.3, 0.0, u))
            self._arm(P, -1, u, -40.0, 60.0, 380.0, 'grip', up=0.3)
        self._add(t0 - 0.05, None, fn)
        return [self._ev2(t0 + dur, 'cloth_grab', -4.0)]

    def open_hand(self, t0, dur=0.01):
        """The palm already open: the red candy on it and the wrapper's mark beside it (651.1)."""
        def fn(P, t):
            self._ins(P, 'r', 1.0, shape='flat', a=180.0); P.palm_open = 1.0; P.base_prop = 'candy_palm'; P.candy = 1.0
        return self._add(t0 - 0.01, None, fn)

    def give(self, t0, prop='phone', dur=0.8):
        """Your hand passes the phone across to his (659.7): held out, then released and drawn back."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur * 0.6)); r = ease_in_out(prog(t, t0 + dur * 0.6, t0 + dur))
            self._ins(P, 'r', 1.0, shape='grip' if r < 0.3 else 'relaxed', prop=prop if r < 0.3 else None, x=0.4 * u - 0.6 * r, a=150.0)
        return self._add(t0, None, fn)

    def fade_in(self, t0, dur=0.12):
        """The character is not drawn before t0, then fades in over dur (H7: her face arrives as the camera tilts up)."""
        return self._add(-1e9, None, lambda P, t: setattr(P, 'alpha', min(getattr(P, 'alpha', 1.0), ease_in_out(prog(t, t0, t0 + dur)))), real=True)

    def fade_out(self, t0, dur=0.5):
        """The character fades away (Tess's reflection in the phone glass, 696.1)."""
        return self._add(t0, None, lambda P, t: setattr(P, 'alpha', min(getattr(P, 'alpha', 1.0), 1.0 - ease_in_out(prog(t, t0, t0 + dur)))), real=True)

    def sit_beside(self, t0, dur=1.2):
        """One smooth inhuman motion from standing to sitting (1.2 s eased glide): no weight, no bob, the head
        travels on a straight line, the hair stays put."""
        if self.who == 'queen': dur = max(dur, 1.2)
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.sit = max(P.sit, u); P.h_dy -= 0.0
            for side in (-1, 1): self._arm(P, side, u, -40.0, 290.0, 150.0, 'relaxed', up=0.0)
            P.ir_y += -0.25 * (1.0 - u)
        self._add(t0, None, fn, real=True)
        return [self._ev2(t0 + dur, 'bed_creak', -10.0, kind='slow')]

    def pat(self, t0, n=2, spacing=0.32):
        """Her long pale hand pats the empty place beside Noah (n pats)."""
        def fn(P, t):
            w = _wnd(t, t0, t0 + n * spacing + 0.3, 0.25, 0.4)
            ph = (t - t0) / spacing
            lift = 0.0 if ph < 0 or ph > n else math.sin(PI * (ph % 1.0)) ** 2
            self._arm(P, 1, w, 60.0, 300.0 - 50.0 * lift, 160.0, 'relaxed', up=0.0)
            self._ins(P, 'r', w, y=-0.18 * lift, a=180.0 + 70.0, shape='relaxed')
        self._add(t0, t0 + n * spacing + 0.8, fn)
        return [self._ev2(t0 + (i + 0.95) * spacing, 'cloth_press', -10.0) for i in range(n)]

    def press_through_cloth(self, t0, depth=0.7, dur=1.2):
        """Five long fingertips press out through the towel toward the lens (hands insert: the open hand grows toward
        the camera with pose.ins_k; the sets drape the cloth over info['tips'])."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.ins_k = lerp(1.0, 1.0 + 0.6 * depth, u); P.ir_press = max(P.ir_press, u)
            self._ins(P, 'r', 1.0, shape='flat', a=180.0)
            self._arm(P, 1, u, -40.0, -110.0, 420.0, 'flat', up=1.0, press=u)
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.1, 'cloth_press', -6.0)]

    # -------------------------------------------------------------- Tess and the flashlight
    def flashlight(self, t0, aim=None, sweep=0.0, on=True, raise_=False, dur=1.6, side=-1):
        """Flashlight in the right hand: raised to aim (design x of the target relative to the body: -1..1 or a
        point), sweeping +-sweep. pose.beam 0..1 and pose.beam_dx (-1..1 aim) tell the sets where the beam goes; the lens
        point is info['hands'][side] (+ the prop length)."""
        ax = 0.0 if not isinstance(aim, (int, float)) else float(aim)
        if isinstance(sweep, (list, tuple)): sweep = 0.8            # a design-x range: a wide sweep
        sweep = float(sweep or 0.0)
        def fn(P, t):
            w = _env(t, t0 - (0.0 if raise_ else 1.0), None, 0.4 if raise_ else 0.01, 0.4)
            sw = sweep * math.sin((t - t0) * 2.2)
            self._arm(P, side, w, 30.0 + 120.0 * (ax + sw) * -side, 40.0 - 30.0 * (1 if raise_ else 0), 300.0, 'grip', up=0.0,
                      prop='flashlight', rot=-90.0 * side)
            P.beam = (1.0 if on else 0.0) if t >= t0 + 0.05 else getattr(P, 'beam', 0.0)
            P.beam_dx = ax + sw
            self._ins(P, 'r', w, prop='flashlight', shape='grip', a=110.0)
        self._add(t0 - 1.0, None, fn)
        return [self._ev2(t0 + 0.05, 'flashlight_click', -6.0)] if on else self

    def jingle(self, t0, prop='keys', dur=0.9):
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.2, 0.3)
            P.ir_a = lerp(P.ir_a, 180.0 + 14.0 * math.sin((t - t0) * 21.0), w)
            P.ir_y += 0.03 * w * math.sin((t - t0) * 17.0)
            self._ins(P, 'r', w, prop=prop, shape='grip')
            self._arm(P, -1, w, -40.0, 60.0, 240.0, 'grip', up=1.0, prop=prop)
        self._add(t0, t0 + dur + 0.4, fn)
        return [self._ev2(t0 + 0.1, 'key_in_lock', -8.0, kind='jingle', dur=dur)]

    def unlock(self, t0, prop='padlock', dur=1.0):
        """Hands at the padlock: the left holds the lock, the right turns the key (click at 60 %)."""
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur + 0.6, 0.25, 0.3)
            turn = ease_out_back(prog(t, t0 + 0.4, t0 + 0.6))
            P.base_prop = prop if w > 0.3 else P.base_prop
            self._ins(P, 'l', w, v=1.0, x=-0.25, y=0.32, a=200.0, shape='grip')
            self._ins(P, 'r', w, x=0.12, y=0.05, a=150.0 + 55.0 * turn, shape='pinch', prop='keys')
            for side in (-1, 1): self._arm(P, side, w, -70.0, 200.0, 200.0, 'grip', up=0.5)
            P.h_nod += 0.15 * w
        self._add(t0, t0 + dur + 1.0, fn)
        return [self._ev2(t0 + 0.2, 'key_in_lock', -6.0), self._ev2(t0 + 0.6, 'padlock', -4.0)]

    def pull_chain(self, t0, dur=0.8):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            w = _wnd(t, t0, t0 + dur, 0.15, 0.4)
            self._ins(P, 'l', w, v=1.0, x=-0.35 - 0.3 * u, y=0.1, a=230.0, shape='fist')
            self._ins(P, 'r', w, x=0.2 + 0.35 * u, y=0.05, a=140.0, shape='fist')
            for side in (-1, 1): self._arm(P, side, w, 40.0 + 60.0 * u, 200.0, 220.0 - 80.0 * u, 'fist', up=0.0)
        self._add(t0, t0 + dur + 0.4, fn)
        return [self._ev2(t0 + 0.1, 'gate_chain', -3.0)]

    def finger_to_lips(self, t0, t1=None, side=-1):
        def fn(P, t):
            w = _wnd(t, t0, t1, 0.3, 0.35)
            out, down = self._mouth_target(0.0, side=side)
            # review round 2 (M4): the index finger crosses the lips (it stopped at the chin and read as pointing sideways)
            self._arm(P, side, w, out, down + 6.0, 80.0, 'point', up=1.0)
            P.m_press = max(P.m_press, 0.6 * w); P.brow_up += 0.2 * w
        return self._add(t0, None if t1 is None else t1 + 0.4, fn)

    def set_down(self, t0, prop='phone', face_up=True, dur=0.9):
        """Sets a prop down (the phone face up on the sill): the prop leaves the hand at t0 + 0.55."""
        rel = t0 + 0.55
        def fn(P, t):
            u = ease_in_out(prog(t, t0, rel)); r = ease_in_out(prog(t, rel + 0.05, t0 + dur))
            hold = t < rel
            self._ins(P, 'r', 1.0, y=-0.25 + 0.3 * u + 0.35 * r, a=200.0, shape='grip' if hold else 'relaxed', prop=prop + ('_dark' if prop == 'phone' else '') if hold else None)
            P.ir_v = min(P.ir_v, 1.0 - r)
            self._arm(P, -1, 1.0 - r, -30.0, 120.0 + 60.0 * u, 300.0, 'grip', up=0.0, prop=('phone_dark' if prop == 'phone' else prop) if hold else None)
        self._add(t0, t0 + dur + 0.2, fn)
        return [self._ev2(rel, 'phone_handle', -6.0, kind='set_down')]

    def pick_up(self, t0, prop='phone', dur=0.8):
        grab = t0 + 0.4
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, grab)); r = ease_in_out(prog(t, grab + 0.05, t0 + dur))
            has = t >= grab
            P.ir_v = min(P.ir_v, u if t < grab else 1.0)
            self._ins(P, 'r', 1.0, y=0.1 - 0.35 * r, a=200.0, shape='grip' if has else 'open', prop=('phone_dark' if prop == 'phone' else prop) if has else None)
            self._arm(P, -1, u, -30.0, 180.0 - 80.0 * r, 300.0, 'grip', up=0.0, prop=('phone_dark' if prop == 'phone' else prop) if has else None)
        self._add(t0, None, fn)
        return [self._ev2(grab, 'phone_handle', -6.0, kind='pick_up')]

    def rub_fingers(self, t0, n=3, period=0.35):
        def fn(P, t):
            w = _wnd(t, t0, t0 + n * period, 0.15, 0.3)
            self._ins(P, 'r', w, shape='pinch', a=190.0 + 8.0 * math.sin((t - t0) * 2 * PI / period))
            P.ir_x += 0.02 * w * math.sin((t - t0) * 2 * PI / period)
        return self._add(t0, t0 + n * period + 0.4, fn)

    def grab_shoulder(self, t0, side=1, dur=0.35, t1=None):
        def fn(P, t):
            w = _wnd(t, t0, t1, dur, 0.4, ease_out_cubic)
            self._arm(P, side, w, -10.0, -10.0, 330.0, 'grip', up=0.2)
            P.lean += 0.1 * w
        self._add(t0, None if t1 is None else t1 + 0.4, fn)
        return [self._ev2(t0 + dur, 'cloth_grab', -6.0)]

    def grab(self, t0, what='sleeve', dur=0.18, t1=None):
        """Hand shoots in and grips (insert: from off frame; body: arm forward)."""
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            self._ins(P, 'r', 1.0, shape='open' if u < 0.85 else 'grip', a=160.0)
            P.ir_v = min(P.ir_v, u) if t1 is None or t < t1 else P.ir_v
            self._arm(P, -1, u, -30.0, 100.0, 330.0, 'grip', up=0.0)
        self._add(-INF, None if t1 is None else t1 + 0.4, fn)
        return [self._ev2(t0 + dur, 'cloth_grab', -3.0)]

    def grab_collar(self, t0, dur=0.25, pull=0.6):
        """Tess grabs your collar (608.97) and pulls you through."""
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur)); p = ease_in_out(prog(t, t0 + dur, t0 + dur + pull))
            self._arm(P, -1, u, -60.0, -60.0 + 40.0 * p, 360.0 - 220.0 * p, 'grip', up=0.4)
            P.lean += 0.15 * u - 0.3 * p; P.brow_angry = max(P.brow_angry, 0.6 * u)
            # hands insert: the orange arm shoots down out of the doorway (foreshortened), the fist closes on the collar
            P.ir_fore = max(P.ir_fore, u); P.base_prop = 'collar'
            self._ins(P, 'r', 1.0, shape='fist' if u > 0.7 else 'claw', a=lerp(-30.0, 8.0, u), x=0.1 - 0.15 * p, y=lerp(-1.4, 0.05, u) - 1.1 * p)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur, 'jacket_cloth', -2.0), self._ev2(t0 + dur + 0.05, 'cloth_grab', -4.0)]

    def yank(self, t0, dur=0.35):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            for side in (-1, 1): self._arm(P, side, 1.0, -40.0, 160.0, 320.0 - 240.0 * u, 'fist', up=0.0)
            P.lean -= 0.28 * u; P.dx -= 0.06 * self.height * u
            self._ins(P, 'r', 1.0, x=0.0 - 0.4 * u, y=0.1 * u, shape='fist')
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.05, 'cloth_grab', -3.0)]

    def shove(self, t0, prop=None, dur=0.3):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur)); r = ease_in_out(prog(t, t0 + dur + 0.2, t0 + dur + 0.7))
            hold = t < t0 + dur + 0.05
            for side in (-1, 1): self._arm(P, side, 1.0 - r, -50.0, 150.0, 120.0 + 260.0 * u, 'flat' if not prop else 'grip', up=0.0,
                                           prop=prop if (prop and hold and side < 0) else None)
            P.lean += 0.15 * u
            self._ins(P, 'r', 1.0, x=0.45 * u, y=-0.05 * u, shape='grip' if prop else 'flat', prop=prop if hold else None)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur, 'towel_cloth' if prop == 'towel' else 'whoosh', -6.0)]

    def snatch(self, t0, prop='towel', dur=0.3):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur)); b = ease_in_out(prog(t, t0 + dur, t0 + dur + 0.3))
            self._arm(P, -1, 1.0, -40.0, 120.0, 340.0 * u - 160.0 * b, 'grip', up=0.0, prop=prop if t > t0 + dur else None)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur, 'towel_cloth', -4.0)]

    def throw(self, t0, prop='towel', at=None, dur=0.45):
        rel = t0 + dur * 0.62
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            back = math.sin(PI * min(1.0, u * 2.0)) if u < 0.5 else 0.0
            fwd = ease_out_cubic(prog(t, t0 + dur * 0.4, t0 + dur))
            self._arm(P, -1, _wnd(t, t0, t0 + dur + 0.3, 0.1, 0.5), 60.0, -160.0 * back + 120.0 * fwd, -100.0 * back + 380.0 * fwd, 'open' if t > rel else 'grip',
                      up=1.0 - fwd, prop=prop if t < rel else None)
            P.turn += 0.2 * back - 0.15 * fwd; P.lean += 0.15 * fwd
        self._add(t0, t0 + dur + 0.8, fn)
        return [self._ev2(rel, 'whoosh', -8.0), self._ev2(rel + 0.18, 'towel_cloth', -2.0)]

    def wind_up(self, t0, dur=0.4):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            self._arm(P, -1, u, 90.0, -220.0, -60.0, 'grip', up=1.0, prop='padlock')
            P.turn += 0.25 * u; P.tilt -= 4.0 * u
        return self._add(t0, None, fn)

    def strike(self, t0, prop='padlock', target='bell', dur=0.14):
        """Hits the real bell with the padlock: the arm comes down fast, contact at t0 + dur (the cracked rattle)."""
        def fn(P, t):
            u = ease_in_cubic(prog(t, t0 - 0.02, t0 + dur)); r = spring(max(0.0, t - t0 - dur), 4.0, 0.4) if t > t0 + dur else 0.0
            self._arm(P, -1, 1.0, 90.0 - 150.0 * u, -220.0 + 380.0 * u - 30.0 * r, -60.0 + 380.0 * u, 'grip', up=1.0 - u, prop=prop)
            P.turn += 0.25 * (1.0 - u); P.lean += 0.12 * u
        self._add(t0 - 0.1, None, fn)
        return [self._ev2(t0 + dur, 'bell_cracked', 0.0, kind='strike'), self._ev2(t0 + dur, 'impact_hit', -10.0)]

    def kick(self, t0, dur=0.22):
        def fn(P, t):
            u = prog(t, t0 - 0.15, t0 + dur)
            k = math.sin(PI * u)
            P.fr_up += 160.0 * k; P.fr_fwd += 320.0 * ease_out_cubic(min(1.0, u * 1.4)) * (1.0 - ease_in_out(prog(t, t0 + dur, t0 + dur + 0.3)))
            P.lean -= 0.12 * k
            for side in (-1, 1): self._arm(P, side, k, 110.0, 230.0, 40.0, 'fist', up=0.0)
        self._add(t0 - 0.2, t0 + dur + 0.4, fn)
        return [self._ev2(t0 + dur * 0.7, 'crate_break', 0.0), self._ev2(t0 + dur * 0.7, 'wood_thud', -6.0)]

    def wipe_glass(self, t0, strokes=2, dir='down', sleeve=False, stroke=0.45, prop=None):
        """Wipes the glass top-down (dir 'down') or across, stroke by stroke. Insert: the hand (flat, or a fist in the
        sleeve) travels -0.6 -> +0.6 size per stroke; body: arm forward at the glass. glass_wipe per stroke."""
        n = int(strokes)
        def fn(P, t):
            if t < t0 - 0.2 or t > t0 + n * stroke + 0.4: return
            w = _wnd(t, t0 - 0.2, t0 + n * stroke, 0.2, 0.3)
            ph = clamp((t - t0) / stroke, 0, n)
            k = min(int(ph), n - 1); u = ease_in_out(ph - k) if ph < n else 1.0
            off = (k - (n - 1) / 2.0) * 0.32
            if dir == 'down': x_, y_ = off, -0.6 + 1.2 * u
            else: x_, y_ = -0.6 + 1.2 * u, off
            self._ins(P, 'r', w, x=x_, y=y_, a=160.0 if dir == 'down' else 110.0, shape='grip' if prop else ('fist' if sleeve else 'flat'), press=0.6, prop=prop)
            if sleeve: P.cuff_up = 0.0
            P.wipe = u
            self._arm(P, -1, w, -60.0 + 120.0 * x_, -120.0 + 150.0 * y_, 400.0, 'flat' if not sleeve else 'fist', up=1.0, press=0.6)
        self._add(t0 - 0.2, t0 + n * stroke + 0.5, fn)
        return [self._ev2(t0 + i * stroke + 0.05, 'glass_wipe', -6.0, dur=stroke) for i in range(n)]

    # -------------------------------------------------------------- you at the mirror
    def unwrap(self, t0, prop='towel', dur=1.2):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur)); w = _wnd(t, t0, t0 + dur, 0.2, 0.4)
            self._ins(P, 'r', w, x=0.1 + 0.4 * u, y=0.0, a=120.0, shape='grip')
            self._ins(P, 'l', w, v=1.0, x=-0.2 - 0.3 * u, y=0.05, a=230.0, shape='grip')
            for side in (-1, 1): self._arm(P, side, w, -60.0 + 100.0 * u, 200.0, 240.0, 'grip', up=0.0)
            P.h_nod += 0.12 * w
        self._add(t0, t0 + dur + 0.5, fn)
        return [self._ev2(t0 + 0.1, 'towel_cloth', -4.0, dur=dur)]

    def grip_frame(self, t0, tremble=1.0, fail_open=True, dur=1.6, t1=None):
        """Both hands on the mirror frame; the fingers will not open (they twitch open and clamp back), knuckles
        white, the hands shaking."""
        def fn(P, t):
            w = _wnd(t, t0, t1, 0.15, 0.3)
            P.hshake = max(P.hshake, tremble * w)
            tw = 0.0
            if fail_open:
                ph = ((t - t0) % 0.9) / 0.9
                tw = math.sin(PI * clamp(ph / 0.35)) if ph < 0.35 else 0.0
            sh_ = 'grip' if tw < 0.5 else 'relaxed'
            self._ins(P, 'r', w, x=0.42, y=0.0, a=135.0, shape=sh_, press=1.0)
            self._ins(P, 'l', w, v=1.0, x=-0.42, y=0.04, a=225.0, shape=sh_, press=1.0)
            for side in (-1, 1): self._arm(P, side, w, -20.0, 140.0, 260.0, 'grip', up=0.0, press=1.0)
            P.brow_sad = max(P.brow_sad, 0.6 * w); P.m_press = max(P.m_press, 0.5 * w)
        return self._add(t0, None if t1 is None else t1 + 0.3, fn)

    def tilt_frame(self, t0, angle=12.0, dur=1.0):
        """Tilts the mirror (pose.frame_tilt deg for the sets); the hands rotate with the frame."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur)); a = math.radians(angle * u)
            P.frame_tilt = angle * u
            for nm, x0 in (('r', 0.42), ('l', -0.42)):
                setattr(P, 'i%s_x' % nm, x0 * math.cos(a)); setattr(P, 'i%s_y' % nm, x0 * math.sin(a))
                setattr(P, 'i%s_a' % nm, (135.0 if nm == 'r' else 225.0) + angle * u)
            P.il_v = 1.0; P.ir_shape = P.il_shape = 'grip'
            for side in (-1, 1): self._arm(P, side, 1.0, -20.0, 140.0 + side * 40.0 * math.sin(a), 260.0, 'grip', up=0.0)
        self._add(t0 - 0.3, None, fn)
        return [self._ev2(t0 + 0.05, 'mirror_handle', -6.0)]

    def touch_glass(self, t0, at=None, dur=0.4, t1=None):
        """Index finger to the glass: insert - the pointing hand comes in from below to the touch point; body - arm
        forward at face height. glass_tap (soft) at contact."""
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            self._ins(P, 'r', 1.0, shape='point', a=180.0 + 12.0, press=0.3 * u)
            if t1 is None or t < t1: P.ir_v = min(P.ir_v, max(u, 0.0))
            self._arm(P, -1, u, -50.0, -90.0, 420.0, 'point', up=1.0, press=u)
            P.lean += 0.08 * u
        self._add(-INF, None if t1 is None else t1 + 0.4, fn)
        return [self._ev2(t0 + dur, 'glass_tap', -12.0, soft=True)]

    def nail_tap(self, t0, n=1, spacing=0.22):
        def fn(P, t):
            for i in range(n):
                tt = t - (t0 + i * spacing)
                if -0.12 <= tt <= 0.08:
                    k = math.sin(PI * clamp((tt + 0.12) / 0.12)) if tt < 0 else 0.0
                    P.ir_y += 0.05 * k; P.ir_a += 6.0 * k; P.hr_fwd -= 20.0 * k
        self._add(t0 - 0.2, t0 + n * spacing + 0.1, fn)
        return [self._ev2(t0 + i * spacing, 'nail_click_glass', -2.0) for i in range(n)]

    def smear(self, t0, step=1, length=0.5, dur=0.35):
        """The fingertip drags down through a lipstick step (it smears): insert offset moves by length x size."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.ir_x += 0.25 * length * u; P.ir_y += 0.6 * length * u
            P.ir_shape = 'point'; P.ir_press = max(P.ir_press, 0.6)
            self._arm(P, -1, 1.0, -50.0 + 40.0 * u, -90.0 + 60.0 * u, 420.0, 'point', up=1.0, press=0.6)
        self._add(t0 - 0.3, None, fn)
        return [self._ev2(t0, 'lipstick_smear', -6.0, dur=dur, step=step)]

    def take_hand(self, t0, dur=0.4):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            self._arm(P, -1, u, -40.0, 230.0, 330.0, 'grip', up=0.0)
            self._ins(P, 'r', 1.0, shape='open' if u < 0.9 else 'grip', a=200.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur, 'cloth_grab', -14.0, kind='skin')]

    def pull_hand(self, t0, force=1.0, to=None, dur=0.6):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            self._arm(P, -1, 1.0, -20.0, 230.0, 330.0 - 260.0 * u * force, 'grip', up=0.0)
            P.lean -= 0.18 * force * math.sin(PI * min(1.0, u * 1.5)); P.turn += 0.25 * u
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.05, 'footsteps_wood_inside', -8.0, n=1)]

    def pulled_along(self, t0, to=None, dur=0.8):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            self._arm(P, -1, 1.0, -10.0, 150.0, 340.0, 'grip', up=0.0)
            P.lean += 0.22 * math.sin(PI * u); P.dx += 0.14 * self.height * u; P.fr_up += 60.0 * math.sin(PI * min(1, 2 * u))
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.5, 'bare_foot_step', -8.0)]

    def hand_jerk(self, t0, dir='back'):
        """His hand jerks out of yours: in 2 frames, with a spring settle (the loop resets him)."""
        sgn = -1.0 if dir == 'back' else 1.0
        def fn(P, t):
            if t < t0: return
            u = ease_out_cubic(prog(t, t0, t0 + 0.035)); r = 1.0 - spring(t - t0, 3.0, 0.45) * 0.0
            P.ir_x += sgn * 0.6 * u; P.ir_y -= 0.15 * u; P.ir_a += 25.0 * u * sgn
            P.hr_fwd -= 220.0 * u
        self._add(t0 - 0.05, None, fn, real=True)
        return [self._ev2(t0, 'whoosh', -12.0, kind='jerk')]

    def take(self, t0, prop='candy_red', dur=0.5):
        grab = t0 + dur * 0.7
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, grab))
            has = t >= grab
            P.ir_v = min(P.ir_v, u)
            self._ins(P, 'r', 1.0, shape='grip' if has else 'open', prop=prop if has else None, a=170.0)
            self._arm(P, -1, u, -40.0, 120.0, 300.0, 'grip', up=0.0, prop=prop if has else None)
        self._add(-INF, None, fn)
        return [self._ev2(grab, 'candy_wrapper' if 'candy' in str(prop) else 'towel_cloth', -8.0)]

    def fist(self, t0, slow=False, squeeze=0.0, fail_open=False, tremble=0.0, t1=None):
        """Closes the hand into a fist round the candy (slow: 1 s); squeeze: knuckles press, a tremor; fail_open: the
        fingers twitch open and clamp shut again (they will not open)."""
        dur = 1.0 if slow else 0.25
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            tw = 0.0
            if fail_open:
                ph = ((t - t0) % 1.1) / 1.1
                tw = math.sin(PI * clamp(ph / 0.3)) * 0.6 if ph < 0.3 else 0.0
            closed = u > 0.55 and tw < 0.4
            self._ins(P, 'r', 1.0, shape='fist' if closed else 'relaxed', press=squeeze, prop=None if closed else P.ir_prop)
            P.hshake = max(P.hshake, tremble + 0.6 * squeeze)
            self._arm(P, -1, 1.0, -40.0, 200.0, 200.0, 'fist' if closed else 'relaxed', up=0.0)
            P.candy = 1.0
        self._add(t0, None if t1 is None else t1, fn)
        return [self._ev2(t0 + dur * 0.6, 'candy_wrapper', -14.0, kind='crush')]

    def open_fist(self, t0, dur=1.4):
        """The fist opens slowly, palm up: the red candy (its wrapper printed a mark in the palm). Review round 2 (B18): no
        swap: the fingers strain first (the first 30 %: a tremor, the fist loosens a little), the fist cross-fades into a
        loose curl (30-42 %), then the fingers uncurl continuously to the flat palm (shape_mix curl -> flat)."""
        def fn(P, t):
            r = prog(t, t0, t0 + dur)
            if r < 0.30:
                shp = 'fist'
                P.hshake = max(P.hshake, 0.6 * (1.0 - r / 0.3) + 0.25)
            elif r < 0.42:
                shp = 'xf:%.3f:curl' % ease_in_out((r - 0.30) / 0.12)
            else:
                shp = shape_mix('curl', 'flat', ease_in_out((r - 0.42) / 0.58))
            u = ease_in_out(clamp((r - 0.30) / 0.70))
            self._ins(P, 'r', 1.0, shape=shp, a=180.0 - 10.0 * u, prop=None)
            if r >= 0.42: P.base_prop = 'candy_palm'
            P.palm_open = u
            self._arm(P, -1, 1.0, -40.0, 200.0, 220.0, 'fist' if r < 0.42 else 'flat', up=0.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + dur * 0.5, 'candy_wrapper', -10.0, kind='open')]

    def rub_thumb(self, t0, n=2, period=0.6):
        def fn(P, t):
            w = _wnd(t, t0, t0 + n * period, 0.2, 0.3)
            P.ir_x += 0.06 * w * math.sin((t - t0) * 2 * PI / period); P.ir_a += 5.0 * w * math.sin((t - t0) * 2 * PI / period)
            P.ir_shape = 'relaxed'
        self._add(t0, t0 + n * period + 0.4, fn)
        return [self._ev2(t0 + i * period, 'towel_cloth', -16.0, kind='rub') for i in range(n)]

    def reach(self, t0, to=None, dur=0.6, side=-1, t1=None):
        """Reaches toward `to` (a design point relative to the insert / figure, or a name): insert - the open hand slides
        in toward it; body - the arm extends forward-down."""
        tx, ty = (to if isinstance(to, (list, tuple)) else (None, None))
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.ir_v = min(P.ir_v, max(u, 0.0)) if t1 is None or t < t1 else P.ir_v
            if tx is not None and getattr(self, '_at', None):
                ax, ay, sz = self._at
                P.ir_x += (tx - ax) / sz * u; P.ir_y += (ty - ay) / sz * u
            self._ins(P, 'r', 1.0, shape='open', a=150.0)
            self._arm(P, side, u, -20.0, 160.0, 380.0, 'open', up=0.0)
            P.lean += 0.12 * u
        return self._add(-INF, None if t1 is None else t1 + 0.4, fn)

    def slide_out(self, t0, dur=0.9):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.ir_shape = 'grip'; P.ir_x -= 0.55 * u; P.ir_y += 0.08 * u
            self._arm(P, -1, 1.0, -20.0, 200.0, 380.0 - 220.0 * u, 'grip', up=0.0)
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.05, 'towel_cloth', -6.0, dur=dur), self._ev2(t0 + 0.1, 'wood_thud', -18.0, kind='scrape')]

    def give_jacket(self, t0, dur=1.4):
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            k = math.sin(PI * u)
            for side in (-1, 1): self._arm(P, side, k, -20.0, -40.0 + 120.0 * u, 260.0, 'grip', up=0.6)
            P.jacket_off = 1.0 if u > 0.3 else 0.0
            P.lean += 0.1 * k
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.2, 'jacket_cloth', -4.0, dur=dur)]

    def yanked_back(self, t0, dur=0.4):
        def fn(P, t):
            if t < t0: return
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.lean -= 0.35 * u; P.dx -= 0.2 * self.height * u; P.h_nod += 0.15 * math.exp(-(t - t0) * 8) * math.sin((t - t0) * 30)
            P.collar_pull = max(P.collar_pull, 1.0 - prog(t, t0 + 0.6, t0 + 1.0))
            for side in (-1, 1): self._arm(P, side, math.sin(PI * min(1, u)), 140.0, 80.0, 160.0, 'open', up=0.3)
            P.wide = max(P.wide, 0.8 * math.exp(-(t - t0) * 2))
        self._add(t0, None, fn, real=True)
        return [self._ev2(t0, 'jacket_cloth', -2.0), self._ev2(t0 + 0.02, 'whoosh', -8.0)]

    # -------------------------------------------------------------- Noah
    def tie_loop(self, t0, period=2.4, phase=0.0, t1=None):
        """Noah ties the same knot over and over: a fixed 2.4 s cycle that always starts from the same phase (same t0 +
        phase -> frame-identical replay). The loop forms (lace 0 -> 1) and slips undone at the end of each cycle.
        Insert: both hands over the sneaker with the lace (base_prop 'shoe'); body: leaning over his foot. A named phase
        (the plan's 'loop_reset') is the start of the cycle."""
        if not isinstance(phase, (int, float)): phase = 0.0
        if not isinstance(period, (int, float)): period = 2.4
        def fn(P, t):
            w = _wnd(t, t0 - 0.3, t1, 0.3, 0.4)
            if w <= 0: return
            ph = (((t - t0) / period) + phase) % 1.0
            loop = ease_in_out(clamp(ph / 0.6)) * (1.0 - ease_in_cubic(clamp((ph - 0.85) / 0.15)))
            pull = math.sin(PI * clamp((ph - 0.55) / 0.3)) if 0.55 <= ph <= 0.85 else 0.0
            P.base_prop = 'shoe'; P.lace = loop
            self._ins(P, 'r', w, x=0.34 + 0.14 * pull + 0.03 * math.sin(ph * 2 * PI * 2), y=0.02 - 0.12 * loop, a=112.0 - 12.0 * loop, shape='grip')
            self._ins(P, 'l', w, v=1.0, x=-0.34 - 0.14 * pull, y=0.06 - 0.06 * loop, a=248.0 + 12.0 * loop, shape='grip')
            P.sit = lerp(P.sit, 1.0, w); P.fl_up += 150.0 * w; P.fl_fwd += 60.0 * w      # sat on the bunk, left foot up
            for side in (-1, 1): self._arm(P, side, w, -60.0 + side * 30.0 * pull + (40.0 if side > 0 else 0.0), 420.0 - 60.0 * loop, 300.0, 'grip', up=0.0)
            P.h_nod = lerp(P.h_nod, 0.4, w); P.look_y = lerp(P.look_y, 0.6, w); P.lean += 0.42 * w
        self._add(t0 - 0.3, None if t1 is None else t1 + 0.4, fn, real=True)
        n = int(((t1 if t1 is not None else t0 + 6.0) - t0) / period) + 1
        return [self._ev2(t0 + ((k + 0.7 - phase) % 1e9) * period, 'lace_pull', -12.0, loop=True) for k in range(n)]

    def draw_step(self, t0, step=1, dur=0.3):
        """The taped hand finishes a lipstick step: a stroke right then up (insert; info tip = the lipstick tip)."""
        zig = step == 'zigzag'
        def fn(P, t):
            u = prog(t, t0, t0 + (1.0 if zig else dur))
            if zig:
                P.ir_x += 0.5 * u; P.ir_y += -0.35 * u + 0.06 * math.sin(u * 8 * PI)
            else:
                a = ease_in_out(clamp(u / 0.6)); b = ease_in_out(clamp((u - 0.6) / 0.4))
                P.ir_x += 0.22 * a; P.ir_y -= 0.14 * b
            P.ir_prop = 'lipstick'; P.ir_shape = 'pinch'
        self._add(t0 - 0.4, None, fn)
        return [self._ev2(t0, 'lipstick_draw', -6.0, dur=dur)]

    def withdraw(self, t0, dur=0.45):
        def fn(P, t):
            u = ease_in_cubic(prog(t, t0, t0 + dur))
            P.ir_v = min(P.ir_v, 1.0 - u)
            self._arm(P, -1, 1.0 - u, -30.0, 200.0, 200.0, 'relaxed', up=0.0)
        return self._add(t0, None, fn)

    def wave(self, t0, n=2, period=0.4, side=1):
        def fn(P, t):
            w = _wnd(t, t0, t0 + n * period, 0.25, 0.4)
            self._arm(P, side, w, 120.0, -220.0, 60.0, 'open', up=1.0, rot=side * 22.0 * math.sin((t - t0) * 2 * PI / period))
        return self._add(t0, t0 + n * period + 0.5, fn)

    def pull_from_pocket(self, t0, prop='candy_red', dur=0.8):
        out_ = t0 + dur * 0.5
        def fn(P, t):
            u = ease_in_out(prog(t, t0, out_)); r = ease_out_cubic(prog(t, out_, t0 + dur))
            has = t >= out_
            P.ir_y += 0.35 * (1.0 - r) if has else 0.35
            self._ins(P, 'r', 1.0, shape='pinch' if has else 'relaxed', prop=prop if has else None, a=180.0)
            self._arm(P, -1, 1.0, -70.0, 300.0 - 140.0 * r, 140.0 + 120.0 * r, 'grip' if has else 'relaxed', up=0.0, prop=prop if has else None)
            P.candy = 1.0 if not has else 0.0
        self._add(-INF, None, fn)
        return [self._ev2(out_, 'candy_wrapper', -8.0)]

    def hold_out(self, t0, prop='candy_red', dur=0.6, t1=None):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            if t1 is None or t < t1: P.ir_v = min(P.ir_v, u)
            self._ins(P, 'r', 1.0, shape='flat', prop=prop, a=170.0)
            self._arm(P, -1, u, -60.0, 160.0, 320.0, 'grip', up=0.0, prop=prop)
            P.smile = max(P.smile, 0.35 * u)
        self._add(-INF, None if t1 is None else t1 + 0.4, fn)
        return [self._ev2(t0 + 0.1, 'candy_wrapper', -14.0)]

    def wring(self, t0, prop='towel', dur=1.4):
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.2, 0.3)
            tw = math.sin((t - t0) * 7.0)
            for side in (-1, 1): self._arm(P, side, w, -60.0, 140.0, 220.0, 'grip', up=0.0, rot=side * 30.0 * tw, prop='towel' if side < 0 else None)
        self._add(t0, t0 + dur + 0.4, fn)
        return [self._ev2(t0 + 0.1, 'towel_cloth', -6.0, dur=dur), self._ev2(t0 + 0.4, 'water_drip', -10.0)]

    def breathe_sleep(self, t0, t1=None):
        def fn(P, t):
            P.breath = 0.5 + 0.5 * math.sin(2 * PI * (t - t0) / 4.6); P.eye_open = 0.0; P.m_open = max(P.m_open, 0.05 + 0.03 * P.breath)
        return self._add(t0, None if t1 is None else t1, fn)

    def tap_rail(self, t0, n=2, spacing=0.35):
        def fn(P, t):
            for i in range(n):
                tt = t - (t0 + i * spacing)
                if -0.15 <= tt <= 0.05: P.ir_y -= 0.06 * math.sin(PI * clamp((tt + 0.15) / 0.15))
        self._add(t0 - 0.2, t0 + n * spacing, fn)
        return [self._ev2(t0 + i * spacing, 'wood_thud', -18.0, kind='tap') for i in range(n)]

    def reach_through(self, t0, dir='up', dur=1.0):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            P.ir_v = min(P.ir_v, u); P.ir_a = 180.0 if dir == 'up' else 150.0; P.ir_shape = 'relaxed'
        return self._add(-INF, None, fn)

    def fingers_flex(self, t0, dur=1.2):
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            P.ir_shape = 'open' if 0.25 < u < 0.7 else 'relaxed'; P.ir_a += 6.0 * math.sin(u * PI)
        return self._add(t0, t0 + dur, fn)

    def peel_tape(self, t0, n=3, period=0.45):
        def fn(P, t):
            ph = (t - t0) / period
            if 0 <= ph <= n: P.tape_peel = max(P.tape_peel, math.sin(PI * (ph % 1.0)))
            P.ir_shape = 'relaxed'
        self._add(t0, t0 + n * period + 0.2, fn)
        return [self._ev2(t0 + (i + 0.5) * period, 'tape_peel', -12.0) for i in range(n)]

    def slip_tape(self, t0, dur=0.5):
        """The taped fingers slip out of the blue tape: the ring slides off and stays (base_prop 'tape_ring')."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.tape_slip = u; P.ir_x -= 0.3 * u; P.ir_y += 0.25 * u; P.ir_shape = 'relaxed'
            if u > 0.85: P.base_prop = 'tape_ring'; P.tape = 0.0
        self._add(t0, None, fn)
        return [self._ev2(t0 + 0.1, 'tape_peel', -6.0, kind='slip')]

    def drop_lace(self, t0, dur=0.4):
        def fn(P, t):
            u = ease_in_cubic(prog(t, t0, t0 + dur))
            P.lace *= (1.0 - u); P.ir_shape = 'relaxed'; P.il_shape = 'relaxed'; P.ir_y += 0.1 * u; P.il_y += 0.1 * u
        self._add(t0, None, fn, late=True)
        return [self._ev2(t0, 'lace_pull', -18.0, kind='drop')]

    def swat(self, t0, side=-1):
        def fn(P, t):
            k = math.sin(PI * prog(t, t0, t0 + 0.25))
            self._arm(P, side, k, 160.0, -20.0, 180.0, 'open', up=0.6)
        self._add(t0, t0 + 0.3, fn)
        return [self._ev2(t0 + 0.12, 'whoosh', -16.0, kind='soft')]

    def pat_knees(self, t0, n=2, spacing=0.3):
        def fn(P, t):
            ph = (t - t0) / spacing
            lift = math.sin(PI * (ph % 1.0)) if 0 <= ph <= n else 0.0
            w = _wnd(t, t0, t0 + n * spacing, 0.2, 0.3)
            for side in (-1, 1): self._arm(P, side, w, -30.0, 300.0 - 60.0 * lift, 200.0, 'flat', up=0.0)
        self._add(t0, t0 + n * spacing + 0.4, fn)
        return [self._ev2(t0 + (i + 0.9) * spacing, 'cloth_press', -12.0) for i in range(n)]

    def eat(self, t0, dur=1.6):
        def fn(P, t):
            w = _wnd(t, t0, t0 + 0.6, 0.25, 0.3)
            out, down = self._mouth_target(0.0)
            self._arm(P, -1, w, out, down + 30.0, 70.0, 'pinch', up=1.0, prop='candy_red' if t < t0 + 0.45 else None)
            if t > t0 + 0.5: P.m_open = max(P.m_open, 0.12 * abs(math.sin((t - t0) * 9.0)) * (1.0 - prog(t, t0 + dur - 0.3, t0 + dur)))
        self._add(t0, t0 + dur, fn)
        return [self._ev2(t0 + 0.1, 'candy_wrapper', -10.0)]

    # -------------------------------------------------------------- grown Noah
    def age(self, t0, t1=None, part='arms', start=0.0):
        """Age morph 0 -> 1 (S252-S255): part 'arms' drives the body (limb widths, hand size, the sweatshirt fit, the
        cuffs riding up), 'face' the head (jaw, eyes, stubble). Holds `start` before t0 and 1 after t1."""
        t1 = t0 + 1.5 if t1 is None else t1
        key = 'age_body' if part in ('arms', 'body') else 'age_face'
        def fn(P, t):
            u = start + (1.0 - start) * ease_in_out(prog(t, t0, t1))
            setattr(P, key, u)
            if part in ('arms', 'body'): P.hshake = max(P.hshake, 0.3)
        self._add(-INF, None, fn, real=True)
        return [self._ev2(t0, 'jacket_cloth', -12.0, kind='stretch', dur=t1 - t0)]

    def look_at_hands(self, t0, dur=0.6, t1=None):
        def fn(P, t):
            w = _wnd(t, t0, t1, dur, 0.5)
            for side in (-1, 1): self._arm(P, side, w, -70.0, 110.0, 260.0, 'open', up=0.8, rot=side * 15.0)
            P.h_nod += 0.3 * w; P.look_y = lerp(P.look_y, 0.6, w); P.wide = max(P.wide, 0.4 * w)
            self._ins(P, 'r', w, x=0.3, a=190.0, shape='open'); self._ins(P, 'l', w, v=1.0, x=-0.3, a=170.0, shape='open')
        return self._add(t0, None if t1 is None else t1 + 0.5, fn)

    def stand_hit(self, t0, what='bunk', dur=0.5):
        hit = t0 + dur * 0.7
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, hit))
            P.sit = lerp(P.sit, 1.0, 1.0 - u)
            if t >= hit:
                k = math.exp(-(t - hit) * 7.0) * math.sin((t - hit) * 30.0)
                P.tilt += 6.0 * k; P.h_tilt += 8.0 * k; P.shrug += 0.3 * abs(k); P.squint = max(P.squint, 0.6 * math.exp(-(t - hit) * 3))
        self._add(-INF, None, fn)
        return [self._ev2(hit, 'wood_thud', 0.0), self._ev2(hit, 'body_fall', -12.0, kind='shoulder')]

    def cover_ears(self, t0, dur=1.6, t1=None):
        """Both hands clamp over his ears, head down, eyes squeezed shut (the queen calls his name)."""
        t1 = t0 + dur if t1 is None else t1
        def fn(P, t):
            w = _wnd(t, t0, t1, 0.18, 0.4, ease_out_cubic)
            P.hl_ear = max(P.hl_ear, w); P.hr_ear = max(P.hr_ear, w)
            P.hl_shape = P.hr_shape = 'flat'
            P.h_nod += 0.25 * w; P.squint = max(P.squint, 0.9 * w); P.eye_open = min(P.eye_open, 1.0 - 0.8 * w)
            P.shrug += 0.3 * w; P.brow_sad = max(P.brow_sad, 0.8 * w); P.m_press = max(P.m_press, 0.6 * w)
        return self._add(t0, t1 + 0.4, fn)

    def hold_collar(self, t0, dur=0.5, t1=None):
        def fn(P, t):
            w = _wnd(t, t0, t1, dur, 0.4)
            self._arm(P, -1, w, -90.0, 10.0, 70.0, 'fist', up=0.8)
        return self._add(t0, None if t1 is None else t1 + 0.4, fn)

    def hand_out(self, t0, dur=0.6, t1=None):
        def fn(P, t):
            u = ease_out_cubic(prog(t, t0, t0 + dur))
            if t1 is None or t < t1: P.ir_v = min(P.ir_v, u)
            self._ins(P, 'r', 1.0, shape='flat', a=165.0)
            self._arm(P, -1, u, -40.0, 170.0, 330.0, 'flat', up=0.0)
        return self._add(-INF, None if t1 is None else t1 + 0.4, fn)

    # -------------------------------------------------------------- memory cast
    def wake_up(self, t0, dur=1.0):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.eye_open = min(P.eye_open, u) if t < t0 + dur else P.eye_open; P.sleep = 1.0 - u
            if 0.3 < u < 0.45 or 0.7 < u < 0.78: P.blink = 1.0
            P.h_nod -= 0.1 * u
        return self._add(-INF, None, fn)

    def wake_squint(self, t0, dur=0.8):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            P.eye_open = min(P.eye_open, 0.35 * u); P.squint = max(P.squint, 0.7 * u); P.brow_angry = max(P.brow_angry, 0.3 * u)
        return self._add(-INF, None, fn)

    def press_button(self, t0, n=2, spacing=0.25):
        def fn(P, t):
            P.base_prop = 'watch'; P.ir_shape = 'point'; P.ir_a = 205.0
            for i in range(n):
                tt = t - (t0 + i * spacing)
                if -0.1 <= tt <= 0.1: P.ir_x -= 0.06 * math.sin(PI * clamp((tt + 0.1) / 0.2)); P.ir_y += 0.04 * math.sin(PI * clamp((tt + 0.1) / 0.2))
        self._add(-INF, None, fn)
        return [self._ev2(t0 + i * spacing, 'watch_beep', -10.0) for i in range(n)]

    def pull_socks(self, t0, dur=1.2):
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.3, 0.4)
            P.crouch += 0.5 * w; P.lean += 0.4 * w; P.h_nod += 0.2 * w
            for side in (-1, 1): self._arm(P, side, w, -30.0, 560.0 - 60.0 * math.sin((t - t0) * 6), 200.0, 'grip', up=0.0)
        return self._add(t0, t0 + dur + 0.4, fn)

    def drop_prop(self, t0, prop='bell', dur=0.15):
        def fn(P, t):
            has = t < t0
            for side in (-1, 1): self._arm(P, side, 1.0, -50.0, 220.0 + (40.0 if not has else 0.0), 200.0, 'grip' if has else 'open', up=0.0,
                                           prop=prop if (has and side < 0) else None)
            if not has: P.wide = max(P.wide, 0.6 * math.exp(-(t - t0) * 2))
        self._add(-INF, None, fn)
        return [self._ev2(t0 + 0.28, 'bell_cracked', -2.0, kind='drop')]

    def ring_bell(self, t0, n=2, period=0.5):
        def fn(P, t):
            w = _wnd(t, t0, t0 + n * period, 0.3, 0.4)
            sw = math.sin((t - t0) * 2 * PI / period)
            self._arm(P, -1, w, 60.0, -180.0 + 40.0 * sw, 160.0, 'grip', up=1.0, prop='bell', rot=25.0 * sw)
        self._add(t0, t0 + n * period + 0.5, fn)
        return [self._ev2(t0 + (i + 0.25) * period, 'bell_cracked', -2.0, kind='ring', note=i) for i in range(n)]

    def dare(self, t0, dur=1.2):
        self.expr('sly', t0, t0 + dur, 0.2)
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.25, 0.4)
            P.lean += 0.15 * w
            self._arm(P, -1, w, 40.0, -20.0, 240.0, 'point', up=0.0, rot=-90.0)
        return self._add(t0, t0 + dur + 0.4, fn)

    def hand_over_mouth(self, t0, dur=1.0):
        return self.hand_to_mouth(t0, t0 + dur, shock=False)

    def call_out(self, t0, dur=1.0):
        def fn(P, t):
            w = _wnd(t, t0, t0 + dur, 0.2, 0.4)
            for side in (-1, 1):
                out, down = self._mouth_target(side * 20.0, side=side)
                self._arm(P, side, w, out, down + 20.0, 80.0, 'relaxed', up=1.0, rot=side * 30.0)
            P.m_open = max(P.m_open, 0.7 * w); P.m_round = max(P.m_round, 0.5 * w); P.h_nod -= 0.08 * w
        self._add(t0, t0 + dur + 0.4, fn)
        return [self._ev2(t0, 'voices_calling_far', -6.0, dur=dur)]


for _n, _f in list(_MirrorClips.__dict__.items()):
    if callable(_f) and not _n.startswith('__'): setattr(Acting, _n, _f)


def timeline_line(i):
    """timeline.json line i ({i, who, en, t, end, words}) of this film, or None."""
    global _TL
    if i is None: return None
    try:
        _TL
    except NameError:
        _TL = None
    if _TL is None:
        try:
            import json as _json
            _TL = {int(L['i']): L for L in _json.load(open(TIMELINE))['lines']}
        except Exception:
            _TL = {}
    return _TL.get(int(i))


# ====================================================================================================== hands v2 (everyone)
# DIRECTION_V2 §3.7: one hand system for the whole cast (no mittens): back / palm views, open, relaxed, flat, palm,
# claw, point, pinch, fist, grip; knuckle creases, nails, thumb, tendons, foreshortened curled fingers, outlines; skin
# per character. Hand coords as before: wrist at (0, 0), fingers toward +y, ~66 units wrist to the middle fingertip
# (fk scales the finger length), thumb toward th = -side (back of the hand toward the viewer).
_H2_FING = (  # knuckle (x along th, y), phalanx lengths, base width, splay (rad, + = toward the thumb)
    ((11.6, 28.0), (13.6, 9.2, 7.6), 8.9, 0.11), ((3.9, 30.4), (14.6, 10.2, 8.1), 9.3, 0.025),
    ((-4.1, 29.4), (13.6, 9.6, 7.7), 8.7, -0.07), ((-11.6, 26.2), (10.6, 7.6, 6.6), 7.5, -0.17))
_H2_SHAPES = {  # spread, curl per finger (index..little), thumb mode
    'open': (1.0, (0.06, 0.04, 0.05, 0.08), 'out'), 'wave': (1.15, (0.0, 0.0, 0.0, 0.04), 'out'),
    'relaxed': (0.32, (0.26, 0.3, 0.34, 0.4), 'along'), 'pat': (0.3, (0.12, 0.14, 0.16, 0.2), 'along'),
    'palm4': (0.32, (0.26, 0.3, 0.34, 0.4), 'none'), 'mitt': (0.32, (0.26, 0.3, 0.34, 0.4), 'along'),
    'claw': (1.05, (0.62, 0.58, 0.6, 0.66), 'out'), 'reach': (0.85, (0.32, 0.3, 0.34, 0.4), 'out'),
    'point': (0.4, (0.02, 1.0, 1.0, 1.0), 'across'), 'pinch': (0.45, (0.55, 0.62, 0.7, 0.78), 'pinch'),
    'flat': (1.35, (0.0, 0.0, 0.0, 0.0), 'flat'), 'palm': (0.9, (0.06, 0.06, 0.08, 0.1), 'flat'),
    'curl': (0.3, (0.9, 0.92, 0.94, 0.96), 'along'),        # review round 2: a loose fist, the bridge from 'fist' to an open hand
}
_H2C = {}


def _h2_params(shape):
    """(spread, curls, thumb) of a hand shape; 'mix:a:b:u' blends two shapes (u quantised to 1/16 by shape_mix): a pose
    can now move between shapes over several frames instead of swapping in one (critic B8: the Queen's hand snapped)."""
    if isinstance(shape, str) and shape.startswith('mix:'):
        _, a, b, u = shape.split(':'); u = float(u)
        sa, ca, ta = _H2_SHAPES.get(a, _H2_SHAPES['relaxed']); sb, cb, tb = _H2_SHAPES.get(b, _H2_SHAPES['relaxed'])
        return (sa + (sb - sa) * u, tuple(x + (y - x) * u for x, y in zip(ca, cb)), ta if u < 0.5 else tb)
    return _H2_SHAPES.get(shape, _H2_SHAPES['relaxed'])


def shape_mix(a, b, u):
    """A hand shape between a and b (u 0..1, quantised to 1/16 so the geometry caches stay small)."""
    u = round(max(0.0, min(1.0, u)) * 16) / 16.0
    if u <= 0: return a
    if u >= 1: return b
    return 'mix:%s:%s:%.4f' % (a, b, u)


def _h2_chain(bx, by, ang, lens, curl, bend=0.0):
    """Finger centre line from the knuckle: each joint bends by curl (toward the palm, away from the viewer in the
    back view) so the phalanges foreshorten: projected length = L cos(cumulative bend)."""
    pts = [(bx, by)]; x, y = bx, by; a = ang; cum = 0.0
    for i, ln in enumerate(lens):
        cum += curl * (0.95, 1.25, 0.9)[i]
        pl = ln * max(0.08, math.cos(min(cum, 1.52)))
        x += math.sin(a) * pl; y += math.cos(a) * pl
        pts.append((x, y)); a += bend
    return pts


def _hand2_geom(shape, side, fk=1.0, fw=1.0, nail='short', press=0.0, bound=False, view='back'):
    """Geometry of one hand (cached): dict(union, parts, fingers=[(pts, widths)], nails, creases, tendons, palm_lines,
    pads, tip_pts, thumb). Palm view shapes ('flat', 'palm') mirror the thumb side."""
    key = (shape, side, round(fk, 2), round(fw, 2), nail, round(press, 1), bound, view)
    G = _H2C.get(key)
    if G is not None: return G
    th = -side
    palm_view = shape in ('flat', 'palm') or view == 'palm'
    if palm_view: th = -th
    spread, curls, tmode = _h2_params(shape)
    sq = 1.0 + 0.05 * press
    parts, fingers, nails, creases, tendons, pads, tips = [], [], [], [], [], [], []
    palm_pts = [(th * 12.6, -2.0), (th * 16.4, 9.0), (th * 17.6, 20.0), (th * 15.6, 28.6), (th * 8.0, 32.2), (-th * 0.5, 33.0),
                (-th * 8.5, 31.6), (-th * 15.4, 27.4), (-th * 16.6, 15.0), (-th * 13.6, -2.0)]
    palm = smooth([(x * sq, y) for x, y in palm_pts], True, 0.8)
    parts.append(palm)
    for k, ((kx, ky), lens, w, spl) in enumerate(_H2_FING):
        cu = curls[k]
        L_ = tuple(l_ * fk for l_ in lens)
        w = w * fw * sq
        spr = min(spread, 0.3) if (bound and k >= 1) else spread
        kx_ = kx * (0.93 if (bound and k >= 2) else 1.0)
        pts = _h2_chain(th * kx_ * sq, ky, th * (spl - (0.04 if (bound and k == 1) else 0.0)) * spr, L_, cu, -th * spl * 0.1)
        ws = [w, w * 0.93, w * 0.85, w * 0.74]
        if cu > 0.8:                                   # folded into the palm: the knuckle and the proximal phalanx only
            pts = pts[:2]; ws = [w * 1.02, w * 0.98]
        tube = _tube(pts, ws, 0.9)
        parts.append(tube); fingers.append((pts, ws, cu))
        tips.append(pts[-1])
        if cu > 0.8:
            creases.append(smooth([(pts[1][0] - w * 0.36, pts[1][1] - 1.5), (pts[1][0], pts[1][1] + 0.6), (pts[1][0] + w * 0.36, pts[1][1] - 1.5)], False))
            continue
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        dl = math.hypot(x2 - x1, y2 - y1) or 1.0; ux, uy = (x2 - x1) / dl, (y2 - y1) / dl
        ang = math.degrees(math.atan2(ux, uy))
        if not palm_view:                              # nail on the distal phalanx (it foreshortens with the curl)
            nw = ws[-1] * 0.66; nl = max(2.0, dl * 0.7)
            if nail == 'almond':
                ext = 5.5 * fk
                pth = smooth([(-nw * 0.5, -nl * 0.75), (nw * 0.5, -nl * 0.75), (nw * 0.48, 0.0), (nw * 0.2, ext * 0.8), (0.0, ext),
                              (-nw * 0.2, ext * 0.8), (-nw * 0.48, 0.0)], True, 0.7)
            else:
                pth = rrect(-nw * 0.5, -nl * 0.82, nw, nl * 0.86, nw * 0.42)
            m = skia.Matrix(); m.setRotate(-ang); m.postTranslate(x2 - ux * 1.2, y2 - uy * 1.2); pth.transform(m)
            nails.append(pth)
            if nail == 'almond': tips[-1] = (x2 + ux * 5.5 * fk, y2 + uy * 5.5 * fk)
        for j, kk in ((1, 0.9), (2, 0.8)):             # joint creases: two tiny wrinkles at the middle joint, one at the end joint
            (xa, ya), (xb, yb) = pts[j - 1], pts[j + 1]
            dx_, dy_ = xb - xa, yb - ya; L2 = math.hypot(dx_, dy_) or 1.0
            nx, ny = -dy_ / L2, dx_ / L2; ux2, uy2 = dx_ / L2, dy_ / L2
            cx_, cy_ = pts[j]; h = ws[j] * 0.3 * kk
            for q in ((0.0,) if j == 2 else (-1.1, 1.1)):
                ox, oy = cx_ + ux2 * q, cy_ + uy2 * q
                creases.append(smooth([(ox + nx * h, oy + ny * h), (ox + ux2 * 0.9 * (1 if not palm_view else -1), oy + uy2 * 0.9 * (1 if not palm_view else -1)),
                                       (ox - nx * h, oy - ny * h)], False))
        if palm_view:
            pads.append(oval(x1 + (x2 - x1) * 0.62, y1 + (y2 - y1) * 0.62, ws[-1] * 0.36, max(2.0, dl * 0.42)))
        if not palm_view and k < 4:
            tendons.append(smooth([(th * (kx * 0.38), 5.0), (th * kx * 0.75, 17.0), (th * kx * 0.95 * sq, ky - 2.5)], False))
    # thumb
    if tmode != 'none':
        if tmode == 'flat':
            tb = _h2_chain(th * 15.0, 10.0, th * 0.82, (15.0 * fk ** 0.5, 12.0 * fk ** 0.5), 0.0, -th * 0.12)
        elif tmode == 'along':
            tb = _h2_chain(th * 14.0, 7.0, th * 0.24, (14.0 * fk ** 0.5, 11.0 * fk ** 0.5), 0.12, -th * 0.08)
        elif tmode == 'across':                       # pointing hand: thumb folded over the curled fingers
            tb = [(th * 15.0, 8.0), (th * 12.0, 22.0), (th * 3.0, 31.0), (-th * 4.0, 34.0)]
        elif tmode == 'pinch':                        # thumb tip meets the index tip
            ix, iy = tips[0]
            tb = [(th * 15.0, 8.0), (th * 19.0, 21.0), (lerp(th * 19.0, ix, 0.55), lerp(21.0, iy, 0.6)), (ix + th * 2.5, iy + 1.0)]
        else:
            tb = _h2_chain(th * 14.5, 8.0, th * 0.58, (14.5 * fk ** 0.5, 12.0 * fk ** 0.5), 0.0, -th * 0.16)
        tws = [12.2 * fw, 10.4 * fw, 8.8 * fw] + [8.2 * fw] * max(0, len(tb) - 3)
        ttube = _tube(tb, tws[:len(tb)], 0.9)
        parts.append(ttube)
        (x1, y1), (x2, y2) = tb[-2], tb[-1]
        dl = math.hypot(x2 - x1, y2 - y1) or 1.0; ux, uy = (x2 - x1) / dl, (y2 - y1) / dl
        if not palm_view and tmode not in ('across',):
            nw = tws[min(len(tws), len(tb)) - 1] * 0.62; nl = max(2.5, dl * 0.5)
            if nail == 'almond':
                pth = smooth([(-nw * 0.5, -nl * 0.7), (nw * 0.5, -nl * 0.7), (nw * 0.46, 0.0), (0.0, 4.5 * fk), (-nw * 0.46, 0.0)], True, 0.7)
            else:
                pth = rrect(-nw * 0.5, -nl * 0.8, nw, nl * 0.85, nw * 0.42)
            m = skia.Matrix(); m.setRotate(-math.degrees(math.atan2(ux, uy))); m.postTranslate(x2 - ux * 1.5, y2 - uy * 1.5); pth.transform(m)
            nails.append(pth)
        G_thumb = (tb, tws)
    else:
        G_thumb = None
    U = parts[0]
    for p in parts[1:]:
        U = union(U, p) or U
    palm_lines = []
    if palm_view:
        palm_lines = [smooth([(th * 13.5, 12.0), (th * 6.0, 19.0), (th * 3.5, 30.0)], False),          # life line
                      smooth([(-th * 16.0, 22.0), (-th * 4.0, 24.5), (th * 9.0, 22.0)], False),         # heart line
                      smooth([(-th * 15.0, 15.0), (-th * 2.0, 17.5), (th * 8.0, 13.5)], False)]          # head line
        pads.append(oval(th * 9.0, 12.0, 7.5, 9.0))                                                    # thenar
    G = dict(union=U, parts=parts, fingers=fingers, nails=nails, creases=_multi(creases) if creases else None,
             tendons=_multi(tendons) if tendons else None, palm_lines=_multi(palm_lines) if palm_lines else None, pads=pads,
             tips=tips, thumb=G_thumb, shade=_crescent(U, -th * 4.0, -2.0), palm_view=palm_view, th=th,
             seps=_multi([_tube(f[0], f[1], 0.9) for f in fingers if f[2] > 0.15 or shape in ('relaxed', 'pat', 'palm4', 'mitt')]))
    if len(_H2C) > 400: _H2C.clear()
    _H2C[key] = G
    return G


def _hand2(c, x, y, scale, angle, side, shape, det, look, press=0.0, t=0.0, view=None):
    """Draw one v2 hand on Ctx c at wrist (x, y), rotated angle deg (0 = fingers down), scale ~ size / 66.
    look: skin, sh (shade), dp (creases), line (outline colour), lw_k, fk / fw (finger length / width), nail
    ('short' | 'almond'), nail_c, nail_hi, red_tips (finger indices smudged with lipstick: 0 index .. 3 little),
    knuckles (bool). Returns the Ctx of the hand (hand coords)."""
    if shape == 'mitt': shape = 'relaxed'
    if isinstance(shape, str) and shape.startswith('xf:'):
        # review round 2 (B18): 'xf:<w>:<shape>' cross-fades the closed fist into another shape (the fist is its own
        # drawing, so a fist could only swap to an open hand in one frame)
        _, w_, sb = shape.split(':', 2); w_ = clamp(float(w_))
        cv = c.pen.cv
        if w_ < 0.999:
            cv.saveLayer(None, skia.Paint(Alphaf=float(1.0 - w_)))
            _hand2(c, x, y, scale, angle, side, 'fist', det, look, press, t, view); cv.restore()
        if w_ > 0.001:
            cv.saveLayer(None, skia.Paint(Alphaf=float(w_)))
            hc_ = _hand2(c, x, y, scale, angle, side, sb, det, look, press, t, view); cv.restore()
            return hc_
        return c.sub(x, y, angle, scale)
    view = view or look.get('view', 'back')
    if shape == 'grip' or shape == 'fist':
        return _hand2_fist(c, x, y, scale * (0.8 if view == '3q' else 1.0), angle, side, shape, det, look, press, t)
    # views: 'back' (the back of the hand), 'palm', '3q' (three-quarter: the hand turned on its side, narrower)
    hc = c.sub(x, y, angle, scale * (0.66 if view == '3q' else 1.0), scale) if view == '3q' else c.sub(x, y, angle, scale)
    G = _hand2_geom(shape, side, look.get('fk', 1.0), look.get('fw', 1.0), look.get('nail', 'short'), press, look.get('bound', False),
                    'palm' if view == 'palm' else 'back')
    skin, sh, dp = look['skin'], look['sh'], look['dp']
    ln = look.get('line', LINE); lw = hc.lw * look.get('lw_k', 1.0)
    U = G['union']
    hc.fill(U, skin)
    hc.fill(G['shade'], sh, 140)
    if view == '3q':                                   # the turned hand: the near edge (thumb side) in light, the far side shaded
        hc.fill(_crescent(U, G['th'] * 7.0, 0.0), sh, 170)
    if det >= 1:                                       # soft shade where the fingers meet the hand, a lit knuckle line
        hc.radial(U, -G['th'] * 6.0, 30.0, 26.0, [(0, sh, 0), (0.55, sh, 0), (1, sh, 70)], sy=0.7)
        if G['seps'] is not None: hc.line(G['seps'], lw * 0.42, ln, 150)
    if press > 0.05 and G['palm_view']:
        hc.fill(U, '#f6eee9', 70 * press)
    hc.line(U, lw * 0.9, ln)
    if det >= 1:
        if G['creases'] is not None: hc.line(G['creases'], lw * 0.3, dp, 175)
        if det >= 2 and G['tendons'] is not None: hc.line(G['tendons'], lw * 0.26, dp, 70)
        if G['palm_lines'] is not None: hc.line(G['palm_lines'], lw * 0.32, dp, 160)
        for p in G['pads']: hc.fill(p, '#ffffff', (120 if press > 0.05 else 40) * (0.4 + 0.6 * press))
        nc = look.get('nail_c') or mix(skin, '#ffffff', 0.42)
        for i, p in enumerate(G['nails']):
            hc.fill(p, nc, 245)
            if look.get('nail_hi'):
                b = p.getBounds(); hc.fill(oval(b.centerX() - b.width() * 0.12, b.centerY() - b.height() * 0.1, b.width() * 0.16, b.height() * 0.3),
                                         look['nail_hi'], 170)
            hc.line(p, lw * 0.28, ln if look.get('nail') == 'almond' else dp, 220)
    rt = look.get('red_tips') or ()
    if rt and det >= 0:                                # lipstick smudged on the fingertips (the queen drew the eighth step)
        for i in rt:
            if i >= len(G['fingers']): continue
            pts, ws, cu = G['fingers'][i]
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            sm = smooth([(lerp(x1, x2, 0.35) - ws[-1] * 0.5, lerp(y1, y2, 0.35)), (lerp(x1, x2, 0.6), lerp(y1, y2, 0.5) - 1.0),
                         (lerp(x1, x2, 0.35) + ws[-1] * 0.52, lerp(y1, y2, 0.4)), (x2 + ws[-1] * 0.45, y2 + 1.5), (x2, y2 + ws[-1] * 0.5),
                         (x2 - ws[-1] * 0.5, y2 + 1.0)], True, 0.8)
            with hc.clip(G['parts'][1 + i]):
                hc.fill(sm, '#c63449', 235)
                hc.fill(oval(x2 - ws[-1] * 0.1, y2 - 1.0, ws[-1] * 0.18, ws[-1] * 0.12), '#ff8a9a', 160)
            for q in range(3):                           # crumbs
                hc.fill(oval(x2 + (hash01(q, 61 + i) - 0.5) * ws[-1] * 1.3, y2 + 2.5 + hash01(q, 63 + i) * 3.0, 0.7, 0.6), '#a82638', 220)
    return hc


def _hand2_fist(c, x, y, scale, angle, side, shape, det, look, press=0.0, t=0.0):
    """Fist / grip seen from the front-thumb side: four stacked finger rolls with knuckles and nails, the thumb wrapped
    across the index and middle fingers. look['wrapper'] pokes a red candy-wrapper twist out between the ring and
    little fingers (your candy fist, 323.65-649 s)."""
    hc = c.sub(x, y, angle, scale)
    th = -side
    skin, sh, dp = look['skin'], look['sh'], look['dp']
    ln = look.get('line', LINE); lw = hc.lw * look.get('lw_k', 1.0)
    sqz = clamp(press)
    if shape == 'fist':
        back = smooth([(th * 12.5, -2.0), (th * 16.5, 9.0), (th * 17.5, 21.0), (th * 13.0, 30.0), (-th * 14.0, 30.0), (-th * 17.0, 18.0),
                       (-th * 14.0, -2.0)], True, 0.8)
        rolls = []
        for k in range(4):                              # proximal phalanges seen end-on: knuckle row
            xk = th * (11.0 - k * 7.6)
            w = (9.4, 9.8, 9.2, 8.0)[k] * look.get('fw', 1.0)
            r = rrect(xk - w * 0.5, 24.0 - abs(k - 1.5) * 0.8, w, 15.0 - k * 0.6, w * 0.45)
            rolls.append((r, xk, w, k))
        mids = []
        for k in range(4):                              # middle phalanges folded back under (their backs face the viewer)
            xk = th * (11.0 - k * 7.6); w = (9.0, 9.4, 8.8, 7.6)[k] * look.get('fw', 1.0)
            r = rrect(xk - w * 0.5, 34.0 - abs(k - 1.5) * 0.6 - 3 * sqz, w, 11.0, w * 0.45)
            mids.append((r, xk, w, k))
        tb = [(th * 16.0, 6.0), (th * 15.0, 22.0), (th * 6.0, 36.5), (-th * 3.0, 38.5)]
        thumb = _tube(tb, [12.0, 10.6, 9.4, 8.6], 0.9)
        U = back
        for r, *_ in rolls + mids: U = union(U, r) or U
        U = union(U, thumb) or U
        hc.fill(U, skin)
        hc.fill(_crescent(U, -th * 4.0, -2.0), sh, 140)
        if det >= 1:
            for r, xk, w, k in mids: hc.line(r, lw * 0.4, ln, 160)
            for r, xk, w, k in rolls:
                hc.line(r, lw * 0.42, ln, 170)
                hc.line(smooth([(xk - w * 0.34, 27.5), (xk, 25.5), (xk + w * 0.34, 27.5)], False), lw * 0.28, dp, 170)     # knuckle
            for r, xk, w, k in mids:                     # nails peeking under the folded fingers
                hc.fill(rrect(xk - w * 0.3, 41.0 - 3 * sqz - abs(k - 1.5) * 0.6, w * 0.6, 3.6, 1.6), look.get('nail_c') or mix(skin, '#ffffff', 0.4), 230)
        if look.get('wrapper'):                          # the red cinnamon-candy wrapper: twists out of both ends of the fist
            for (wx_, wy_, dx_, dy_) in ((-th * 13.0, 41.0, -th * 1.0, 0.75), (th * 14.0, 4.0, th * 1.0, -0.55)):
                ex_, ey_ = wx_ + dx_ * 9.0, wy_ + dy_ * 9.0
                nx_, ny_ = -dy_, dx_
                tw = poly([(wx_ - nx_ * 2.0, wy_ - ny_ * 2.0), (ex_ - nx_ * 6.5, ey_ - ny_ * 6.5), (ex_ + dx_ * 2.0, ey_ + dy_ * 2.0),
                           (ex_ + nx_ * 6.5, ey_ + ny_ * 6.5), (wx_ + nx_ * 2.0, wy_ + ny_ * 2.0)])
                hc.fill(tw, '#d42a3c'); hc.fill(_crescent(tw, th * 1.0, 0.8), '#8a1222', 170)
                hc.line(tw, lw * 0.45, ln)
                hc.line(poly([(lerp(wx_, ex_, 0.4) - nx_ * 1.5, lerp(wy_, ey_, 0.4) - ny_ * 1.5), (ex_ - nx_ * 4.0, ey_ - ny_ * 4.0)], False), lw * 0.25, '#ffb0b8', 210)
        hc.fill(thumb, skin); hc.fill(_crescent(thumb, 0, -2.5), sh, 120)
        hc.line(thumb, lw * 0.6, ln, 230)
        if det >= 1:
            tn = rrect(-th * 3.0 - 2.6, 35.8, 5.6, 4.8, 2.0)
            hc.fill(tn, look.get('nail_c') or mix(skin, '#ffffff', 0.4), 230); hc.line(tn, lw * 0.25, dp, 200)
            hc.line(smooth([(th * 13.5, 20.0), (th * 11.0, 24.5), (th * 9.0, 27.0)], False), lw * 0.28, dp, 160)
        hc.line(U, lw * 0.9, ln)
        return hc
    # grip: wrapped round a handle / phone seen from the front: 4 stacked finger rolls across the prop, thumb along it
    palm = rrect(-17.0, -2.0, 34.0, 16.0, 9.0)
    parts = [palm]; nails_ = []; cr = []
    for k in range(4):
        yk = 9.0 + k * 8.6
        lnn = (33.0, 34.5, 32.5, 27.5)[k]
        x0 = th * 15.0; x1 = x0 - th * lnn
        roll = _fattube([(x0, yk), ((x0 + x1) / 2, yk + 0.8), (x1, yk)], (9.6 - 0.6 * k) * look.get('fw', 1.0), (8.6 - 0.5 * k) * look.get('fw', 1.0))
        parts.append(roll)
        cr.append(smooth([(x0 - th * lnn * 0.55, yk - 3.0), (x0 - th * lnn * 0.58, yk), (x0 - th * lnn * 0.55, yk + 3.0)], False))
        cr.append(smooth([(x0 - th * lnn * 0.18, yk - 3.2), (x0 - th * lnn * 0.21, yk), (x0 - th * lnn * 0.18, yk + 3.2)], False))
        nails_.append(rrect(min(x1, x1 + th * 7) - 0.5, yk - 3.0, 7.0, 6.0, 3.0))
    tb = [(th * 16.0, 0.0), (th * 17.5 + th * 1.5 * press, 12.0), (th * 15.5 + th * 3.0 * press, 22.0)]
    parts.append(_fattube(tb, 12.0, 10.0))
    U = parts[0]
    for p in parts[1:]: U = union(U, p) or U
    hc.fill(U, skin); hc.fill(_crescent(U, -th * 4.0, -2.0), sh, 140)
    if det >= 1:
        hc.line(_multi(parts[1:5]), lw * 0.4, ln, 160)
        hc.line(_multi(cr), lw * 0.28, dp, 170)
        for p in nails_: hc.fill(p, look.get('nail_c') or mix(skin, '#ffffff', 0.4), 230); hc.line(p, lw * 0.25, dp, 200)
    hc.line(U, lw * 0.9, ln)
    return hc


def _hand2_look(sp, skin, sh):
    """Hand look for a cast entry (people): finger proportions by age, natural nails."""
    kid = sp.get('kid')
    return dict(skin=skin, sh=sh, dp=sp.get('skin_dp', '#6b4c46'), line=LINE, lw_k=1.0, fk=sp['body'].get('fingers', 1.0) * (0.94 if kid else 1.0),
                fw=0.94 if kid else (1.08 if sp['body'].get('hand', 1.0) > 1.1 else 1.0), nail='short', nail_c=mix(skin, '#ffffff', 0.45),
                bound=bool(sp.get('tape')))


# ====================================================================================================== Queen of Spades v2
# DIRECTION_V2 §3: a playing-card queen drawn as a real, regal woman in the cast's language (outlined, plum line at 0.75x),
# her own head (long oval, almond eyes, full red lips, a spade beauty mark), a crown of spades, a fan collar, waist-length
# hair with strands, a black satin gown with a spade-pip hem, porcelain hands with black almond nails and two lipstick-red
# fingertips, bare ash-white feet. One face, one set of stage parameters on the Pose (q_*), stages S0..S4 (QSTAGES).
# Her values are PRE-GRADE: the v2 grades (contrast ~1.3, bloom over ~225) lift skin #d0c9d3 to the brief's porcelain
# (~#ece6e8, luma ~220 after night_v2 / dawn_v2) and keep the modelling; the brief's #ece6e8 drawn raw blooms to white.
QV = dict(line='#2b1a2a', inner='#4a2c3a', skin='#d0c9d3', skin_sh='#a89bb2', skin_dp='#8a7c97', skin_hi='#e9e5ee',
          lip='#c63449', lip_line='#7a1428', lip_gloss='#ff8a9a', lip_glow='#ff4060', scar='#8e1f30',
          iris='#3b3346', iris_red='#e0213f', white='#e6e1e8', white_pink='#f2d4d8', vein='#c8263a', lid='#0b0910',
          hair='#0d0b14', hair_sheen='#2c2a4a', hair_dark='#050409', hair_hi='#4a4870', parting='#7c7898',
          silver='#c9ccd6', silver_dk='#6f7284', silver_hi='#f4f6ff', black='#0a0910',
          satin='#0f0d16', satin_sh='#07060b', satin_sheen='#2a2638', satin_hi='#4a4462', lace='#0b0910', lace_rib='#3b3550',
          lace_edge='#ebe7f2', teeth='#e8e4da', teeth_line='#9c9288', gum='#d8707e', mouth='#3a0d18', void0='#160308',
          void1='#4a0a18', foot='#d2ccd6', foot_sh='#a69db3', nail='#121018', nail_hi='#7a7690', key='#e8ecff', rim='#ff3b5c',
          tear='#09070d', tear_hi='#8a86a8', toenail='#c6bccd', toenail_edge='#9a8ca8', toenail_hi='#ffffff', crack='#5a4a62', pip='#f4f1f6', hem_red='#c63449', stone='#c63449')
# the stage ladder: every stage is a set of continuous parameters, so a stage change can be a 2-frame snap or a draw-on
QSTAGES = {
    'S0': dict(q_hide=1.0, q_draw=0.0, q_split=0.0, q_red=0.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=0.0),
    'S1': dict(q_hide=0.0, q_draw=0.0, q_split=0.0, q_red=0.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=0.0),
    'S2': dict(q_hide=0.0, q_draw=1.0, q_split=0.0, q_red=0.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=1.0),
    'S3a': dict(q_hide=0.0, q_draw=1.0, q_split=1.0, q_red=0.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=1.0),
    'S3b': dict(q_hide=0.0, q_draw=1.0, q_split=1.0, q_red=1.0, q_full=0.0, q_off=0.0, q_void=0.0, q_pin=1.0),
    'S3c': dict(q_hide=0.0, q_draw=1.0, q_split=1.0, q_red=1.0, q_full=1.0, q_off=0.0, q_void=0.0, q_pin=1.0),
    'OFF': dict(q_hide=0.0, q_draw=1.0, q_split=1.0, q_red=1.0, q_full=1.0, q_off=1.0, q_void=0.0, q_pin=1.0),
    'S4': dict(q_hide=0.0, q_draw=1.0, q_split=1.0, q_red=1.0, q_full=1.0, q_off=1.0, q_void=1.0, q_pin=1.0),
}
QSTAGE_V1 = {0: 'S0', 1: 'S1', 2: 'S2', 3: 'S3c'}       # v1 plans: stage 0..3


def queen_stage(stage):
    """Stage name (S0 S1 S2 S3a S3b S3c OFF S4) or a v1 int (0..3) -> the q_* parameter dict."""
    if isinstance(stage, (int, float)): stage = QSTAGE_V1.get(int(stage), 'S1')
    return dict(QSTAGES.get(str(stage), QSTAGES['S1']))


_QSP = dict(head_ys=[-120, -114, -100, -70, -40, -10, 15, 42, 68, 88, 104, 114, 119, 120],
            head_ws=[0, 38, 58, 75, 80, 84, 87, 80, 64, 46, 29, 16, 7, 0])    # high cheekbones, a jaw angle, a pointed chin
_Q_EYE = dict(dx=35.0, y=-7.0, hw=17.2, hh=9.4)       # 0.40 W apart, ~0.19 W wide, the eye line at 0.47 H
_Q_MOUTH_Y = 55.0                                         # the lip seam, close under the nose (base ~38)
_Q_LIP_HW = 26.0                                          # 0.30 W
_Q_NARROW = 0.88                                          # the head's width factor (a long elegant face)
_Q_GRIN = [None]                                          # the open grin's outline this frame (tears go behind it)
_Q_STEPS = [(26.0, 55.0), (37.3, 55.0), (37.3, 45.4), (48.6, 45.4), (48.6, 35.8), (60.0, 35.8), (60.0, 26.2)]   # tread 0.065 W, rise 0.04 H


class _QHM(HeadMap):
    """The queen's head map: her long oval (1.38 : 1), and S4's stretch (everything below the eyes x1.35) plus a small
    talking jaw."""

    def __init__(self, yaw, pitch, stretch=0.0, jaw=0.0):
        HeadMap.__init__(self, _QSP, yaw, pitch, 0.0)
        self.stretch = float(stretch); self.qjaw = float(jaw)

    def J(self, y):
        y = np.asarray(y, float)
        if self.stretch > 1e-4: y = y + 0.35 * self.stretch * np.clip(y + 10.0, 0, None)
        if self.qjaw > 1e-4: y = y + self.qjaw * np.clip((y - _Q_MOUTH_Y) / 46.0, 0, 1.0)
        return y


def _qm(hm, pts, dz=2.0):
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], dz)
    return list(zip(X.tolist(), Y.tolist())), float(np.min(V))


def _qst(P):
    """Effective stage values of a pose (the grin is open while split and not off; the void replaces the mouth)."""
    g = lambda k, d=0.0: float(getattr(P, k, d))        # noqa: E731
    s = dict(hide=clamp(g('q_hide')), draw=clamp(g('q_draw')), split=clamp(g('q_split')), red=clamp(g('q_red')),
             full=clamp(g('q_full')), off=clamp(g('q_off')), void=clamp(g('q_void')), pin=clamp(g('q_pin')),
             noah=clamp(g('q_noah', 1.0)), glitch=clamp(g('q_glitch')))
    s['open'] = s['split'] * (1.0 - s['off']) * (1.0 - s['void'])
    return s


def _ql(light):
    """The queen's own light from the scene light: rim colour/side/alpha, a red climax flag, a warm flashlight spot."""
    L = _light_dict(light) or {}
    red = bool(L.get('tint') == '#ff6a78' or L.get('under') == '#3a1018')
    side = float(L.get('side', -1.0)) or -1.0
    own = bool(L.get('key_from'))                       # the plan's queen light: its rim is hers
    return dict(rim=L.get('qrim') or (L.get('rim') if own else None) or ('#ff2d55' if red else QV['rim']),
                rim_a=220.0 if red else float(L.get('qrim_a', L.get('rim_a', 150.0) if own else 150.0)), side=side,
                red=red, flash=L.get('flash'), dawn=float(L.get('sat', 1.0)) < 0.99, glow=1.0, rim2=L.get('qrim2'),
                split=L.get('qsplit'))


# ---------------------------------------------------------------------------------------------- the head
def _q_brush(c, pts, w, colr, a=255, crumbs=0, seed=0, dark=None):
    """Waxy lipstick stroke (the mirror steps' brush): a flat stroke, a darker under-edge, crumbs along the edges."""
    p = poly(pts, False)
    if dark: c.pen.line(c.P(p), (w * 1.18) * c.s, dark, a * 0.85, 'square')
    c.pen.line(c.P(p), w * c.s, colr, a, 'square')
    if crumbs:
        acc = skia.Path()
        L = 0.0; segs = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            segs.append((x0, y0, x1, y1, math.hypot(x1 - x0, y1 - y0))); L += segs[-1][4]
        for i in range(crumbs):
            d = hash01(i, 700 + seed) * L
            for x0, y0, x1, y1, l_ in segs:
                if d <= l_:
                    u = d / (l_ or 1); px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                    nx, ny = -(y1 - y0) / (l_ or 1), (x1 - x0) / (l_ or 1)
                    o = (0.55 + 0.25 * hash01(i, 701 + seed)) * w * (1 if hash01(i, 702 + seed) > 0.5 else -1)
                    acc.addCircle(px + nx * o, py + ny * o, w * (0.08 + 0.1 * hash01(i, 703 + seed)))
                    break
                d -= l_
        c.fill(acc, colr, a * 0.9)


def _q_partial(pts, f):
    """The first fraction f (by length) of a polyline."""
    if f >= 0.999: return list(pts)
    L = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    d = f * sum(L); out = [pts[0]]
    for (a, b), l_ in zip(zip(pts[:-1], pts[1:]), L):
        if d >= l_: out.append(b); d -= l_; continue
        u = d / (l_ or 1); out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)); break
    return out


def _q_soft(c, hm, pts, colr, a, blur, dz=1.5, k=0.85):
    """A soft (blurred) shading shape in face coordinates (porcelain modelling, makeup, smudges)."""
    if a < 1.0: return
    Q_, v = _qm(hm, pts, dz)
    if v < -0.25: return
    c.pen.fill(c.P(smooth(Q_, True, k)), colr, min(255.0, a), max(0.5, blur * c.s))


def _q_face_model(c, hm, st, QL, det):
    """Porcelain modelling with a cool contour (DIRECTION_V2 3.2, no blush): temples, sockets, cheek hollows under high
    cheekbones, the jaw and chin, the side of the nose; highlights on the cheekbones, the bridge, the brow and the chin.
    The grin bunches the cheeks up (the hollows fill, the cheeks catch light); the full face sinks the sockets."""
    sh = QV['skin_sh']; dp = QV['skin_dp']; hi = QV['skin_hi']
    g = 1.0 + 0.4 * st['full']
    op = st['open']
    for s_ in (-1, 1):
        _q_soft(c, hm, [(s_ * 92, -68), (s_ * 66, -60), (s_ * 58, -30), (s_ * 66, -4), (s_ * 94, -2)], sh, 150, 8)            # temple
        _q_soft(c, hm, [(s_ * 11, -30), (s_ * 22, -31), (s_ * 22, -14), (s_ * 16, -1), (s_ * 9, -8)], sh, 135 * g, 4)        # socket by the bridge
        _q_soft(c, hm, [(s_ * 46, -37), (s_ * 64, -33), (s_ * 64, -15), (s_ * 52, -20)], sh, 95 * g, 4)                      # under the brow end
        _q_soft(c, hm, [(s_ * 94, 14), (s_ * 76, 24), (s_ * 58, 38), (s_ * 50, 46), (s_ * 58, 50), (s_ * 78, 40), (s_ * 96, 32)],
                sh, 150 * (1.0 - 0.55 * op) * g, 5)                                                                           # cheek hollow
        _q_soft(c, hm, [(s_ * 96, 56), (s_ * 80, 74), (s_ * 58, 97), (s_ * 34, 115), (s_ * 14, 123), (s_ * 40, 128), (s_ * 82, 104),
                        (s_ * 100, 70)], dp, 140, 5)                                                                          # the jaw, under it
        _q_soft(c, hm, [(s_ * 32, 7), (s_ * 54, -1), (s_ * 76, 5), (s_ * 68, 17), (s_ * 44, 19)], hi, 200, 5, 4.0)            # cheekbone light
        if op > 0.02:                                                                                                         # bunched cheeks
            _q_soft(c, hm, [(s_ * 52, 6), (s_ * 72, 4), (s_ * 84, 16), (s_ * 76, 28), (s_ * 60, 24)], hi, 150 * op, 5, 4.0)
    _q_soft(c, hm, [(-10, -60), (10, -60), (14, -45), (0, -41), (-14, -45)], hi, 120, 7, 4.0)                                  # brow
    _q_soft(c, hm, [(-12, 66), (12, 66), (14, 80), (0, 86), (-14, 80)], sh, 100 * (1.0 - op), 4)                               # under the lip
    _q_soft(c, hm, [(-12, 96), (12, 96), (10, 108), (0, 112), (-10, 108)], hi, 170, 5, 3.0)                                    # chin light
    _q_soft(c, hm, [(-7, 39), (7, 39), (8, 45), (0, 47), (-8, 45)], sh, 120, 2.5)                                              # under the nose
    sd = 1.0 if hm.st >= 0.0 else -1.0
    _q_soft(c, hm, [(sd * 6, -22), (sd * 12, -20), (sd * 14, 20), (sd * 15, 31), (sd * 8, 29), (sd * 6, 0)], sh, 125, 3, 8.0)   # nose side


def _q_grin_shape(sp_open, mo, widen):
    """The open grin in face coords: the top edge is the drawn stair smile (3 treads each side) plus the upper lip line,
    the bottom a deep U down toward the chin. Returns (top, bot, ytop)."""
    my = _Q_MOUTH_Y
    stp = _Q_STEPS
    top = [(-x, y) for x, y in stp[::-1]] + [(-13.0, my - 0.8), (0.0, my - 1.4), (13.0, my - 0.8)] + list(stp)
    treads = [(stp[0][0], stp[1][0], stp[0][1]), (stp[2][0], stp[3][0], stp[2][1]), (stp[4][0], stp[5][0], stp[4][1])]
    yc = stp[-1][1]

    def ytop(x):
        ax = abs(x)
        if ax <= treads[0][0]: return my - 1.4 * (1.0 - (ax / treads[0][0]) ** 2)
        for a_, b_, y_ in treads:
            if ax <= b_: return y_
        return yc
    depth = 37.0 + 10.0 * clamp(mo) + 8.0 * clamp(widen)
    xs = np.linspace(60.0, -60.0, 33)
    bot = []
    for x in xs:
        u = abs(x) / 60.0
        yb_full = yc + (my + depth - yc) * max(0.0, 1.0 - u ** 2.2) ** 0.55
        yt = ytop(x) if abs(x) < 59.9 else yc
        bot.append((float(x), yt + max(0.0, yb_full - yt) * sp_open))
    return top, bot, ytop


def _q_brush_steps(c, hm, pts, w, colr, a, det, seed, drawk=1.0, scar=0.0):
    """The drawn stair smile as hand-drawn lipstick: each tread and riser its own waxy stroke, overshooting the corner a
    little, a darker under-edge, a wax sheen, crumbs (the same brush as the mirror steps)."""
    L = [math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts[:-1], pts[1:])]
    tot = sum(L) * clamp(drawk)
    if tot < 0.5: return
    segs, glo = [], []
    for k, ((x0, y0), (x1, y1), l_) in enumerate(zip(pts[:-1], pts[1:], L)):
        if tot <= 0: break
        f = min(1.0, tot / (l_ or 1.0)); tot -= l_
        dx, dy = (x1 - x0) / (l_ or 1.0), (y1 - y0) / (l_ or 1.0)
        o0 = 1.0 + 0.8 * hash01(k, 731 + seed); o1 = 1.4 * hash01(k, 733 + seed) if f >= 0.999 else 0.0
        wob = (hash01(k, 737 + seed) - 0.5) * 1.1
        a0 = (x0 - dx * o0, y0 - dy * o0); a1 = (x0 + (x1 - x0) * f + dx * o1, y0 + (y1 - y0) * f + dy * o1)
        m = ((a0[0] + a1[0]) / 2 - dy * wob, (a0[1] + a1[1]) / 2 + dx * wob)
        Q_, v = _qm(hm, [a0, m, a1], 2.5)
        if v < -0.15: continue
        segs.append(smooth(Q_, False))
        Q2, _ = _qm(hm, [(p[0], p[1] - w * 0.2) for p in (a0, m, a1)], 2.6)
        glo.append(smooth(Q2, False))
    if not segs: return
    path = _multi(segs)
    c.line(path, w * 1.22, mix(colr, '#000000', 0.45), a * 0.8, 'round')
    c.line(path, w, colr, a, 'round')
    if det >= 1:
        if scar < 0.5: c.line(_multi(glo), w * 0.22, QV['lip_gloss'], 125 * (1 - scar), 'round')
        crumbs = skia.Path()
        for i in range(14):
            k = int(hash01(i, 741 + seed) * len(pts[:-1])) % max(1, len(pts) - 1)
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            u = hash01(i, 743 + seed)
            nx, ny = -(y1 - y0), (x1 - x0); nl = math.hypot(nx, ny) or 1.0
            o = (0.55 + 0.35 * hash01(i, 747 + seed)) * w * (1 if hash01(i, 749 + seed) > 0.5 else -1)
            X, Y, v = hm.map1(x0 + (x1 - x0) * u + nx / nl * o, y0 + (y1 - y0) * u + ny / nl * o, 2.6)
            if v > 0: crumbs.addCircle(X, Y, w * (0.07 + 0.09 * hash01(i, 751 + seed)) * hm.sx(x0, y0))
        c.fill(crumbs, colr, a * 0.9)


def _q_tear(c, hm, pts, full, seed):
    """A black mascara tear: a glossy tapered tube with drips, a bulb at the end, a smudge where it left the lashes."""
    Q_, v = _qm(hm, pts, 2.6)
    if v < 0.05 or len(Q_) < 2: return
    n = max(2, int(len(Q_) * clamp(full * 1.15)))
    N0 = len(Q_); Q_ = Q_[:n]
    k = hm.sx(pts[0][0], pts[0][1])
    L, R = [], []
    for i, (x, y) in enumerate(Q_):
        u = i / max(1, len(Q_) - 1)
        bulge = 0.9 if hash01(i, 761 + seed) > 0.78 else 0.0
        w = (0.55 + 0.85 * u + 0.75 * bulge) * 0.5
        a, b = Q_[max(0, i - 1)], Q_[min(len(Q_) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; ll = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ll, dx / ll
        L.append((x + nx * w * 2 * k, y + ny * w * 2)); R.append((x - nx * w * 2 * k, y - ny * w * 2))
    tube = smooth(L + R[::-1], True, 0.6)
    c.fill(tube, QV['tear'], 255 * full)
    hl = [(x - 0.9, y) for x, y in Q_[1:-1]]
    if len(hl) > 1: c.line(smooth(hl, False), 0.9, QV['tear_hi'], 200 * full, 'round')
    ex, ey = Q_[-1]
    if n == N0:
        c.fill(smooth([(ex - 3.2 * k, ey + 1.5), (ex, ey - 2.0), (ex + 3.2 * k, ey + 1.5), (ex + 2.2 * k, ey + 5.6), (ex, ey + 6.6),
                       (ex - 2.2 * k, ey + 5.6)], True, 0.8), QV['tear'], 255 * full)
        c.fill(oval(ex - 1.0 * k, ey + 2.4, 0.9 * k, 1.3), '#c8c4dc', 210 * full)


def _q_eye(c, hm, P, side, st, det, lw):
    """Almond eye (~0.19 W): grey-violet iris with fibres and two highlights, a smoky plum lid, a heavy tapered black liner
    with a wing, 5 curled lashes at the outer corner, a crease. S2 pins the pupil; S3b reddens the iris (bloom), pinks the
    whites with branching veins and inflames the lower rim; S3c opens the lids wide (white all round) and sinks the eye."""
    E = _Q_EYE
    ex0, ey0 = side * E['dx'], E['y']
    X, Y, V = hm.map1(ex0, ey0, 2.0)
    if V < 0.12: return None
    red = st['red']; full = st['full']
    hw = E['hw']; hh = E['hh'] * (1.0 + 0.3 * full)
    hu = hh * (0.8 + 0.2 * max(st['split'], red))            # calm (S1, S2): the upper lid rests on the iris, a hooded regal look
    fs = hm.sx(ex0, ey0)
    up = [(ex0 - side * hw, ey0 + 1.4), (ex0 - side * hw * 0.55, ey0 - hu * 0.84), (ex0 + side * hw * 0.12, ey0 - hu * 1.08),
          (ex0 + side * hw * 0.64, ey0 - hu * 0.76), (ex0 + side * hw * 1.02, ey0 - 2.4)]
    lo = [(ex0 + side * hw * 1.02, ey0 - 2.4), (ex0 + side * hw * 0.55, ey0 + hh * 0.64), (ex0 - side * hw * 0.05, ey0 + hh * 0.88),
          (ex0 - side * hw * 0.6, ey0 + hh * 0.58), (ex0 - side * hw, ey0 + 1.4)]
    U_, _ = _qm(hm, up, 2.0); L_, _ = _qm(hm, lo, 2.0)
    eye = smooth(U_ + L_[1:-1], True, 0.75)
    # makeup: a smoky plum lid (regal), bruised once she goes wrong; S3b+ the sockets sink plum-grey under the eye
    _q_soft(c, hm, [(ex0 - side * hw * 1.05, ey0 - 1.0), (ex0 - side * hw * 0.6, ey0 - E['hh'] * 1.9), (ex0 + side * hw * 0.2, ey0 - E['hh'] * 2.3),
                    (ex0 + side * hw * 1.25, ey0 - E['hh'] * 1.35), (ex0 + side * hw * 1.5, ey0 - 4.5), (ex0 + side * hw, ey0 - 1.0)],
            mix('#6a4a7a', '#4a1a30', red), 125 + 70 * full, 3.0, 2.0)
    if full > 0.02 or red > 0.02:
        _q_soft(c, hm, [(ex0 - side * hw * 0.9, ey0 + hh * 0.55), (ex0 + side * hw * 0.1, ey0 + hh * 0.95), (ex0 + side * hw * 1.05, ey0 + hh * 0.25),
                        (ex0 + side * hw * 0.95, ey0 + hh * 1.7), (ex0 - side * hw * 0.1, ey0 + hh * 2.2), (ex0 - side * hw * 0.85, ey0 + hh * 1.45)],
                '#5a3450', 150 * max(full, 0.55 * red), 3.0, 2.0)
    wc = mix(QV['white'], QV['white_pink'], red)
    if red > 0.02:
        c.glow(X, Y, hw * 3.2 * fs, hw * 2.6, QV['iris_red'], 70 * red)          # bloom halo, 1.6 eye widths
    c.fill(eye, wc)
    lock = clamp(P.lock)
    lx = lerp(P.look_x, -math.sin(hm.yaw) * 0.9, lock); ly = lerp(P.look_y, -math.sin(hm.pitch) * 0.9 - 0.04, lock)
    ir = E['hh'] * 0.78
    ix0 = ex0 + clamp(lx, -1, 1) * hw * 0.42; iy0 = ey0 - 0.4 + clamp(ly, -1, 1) * hh * 0.22
    IX, IY, _ = hm.map1(ix0, iy0, 3.0)
    ifs = hm.sx(ix0, iy0)
    with c.clip(eye):
        c.radial(eye, X, Y + hh * 0.2, hw * 1.05 * fs, [(0, wc, 0), (0.6, wc, 0), (1, mix(wc, '#9c8ea6' if red < 0.5 else '#c0506a', 0.55), 235)],
                 sy=hh / hw / max(fs, 0.2) * 1.4)
        if red > 0.02 and det >= 1:                                         # branching veins from both corners
            vs, vs2 = [], []
            for k in range(8):
                s0 = -1 if k % 2 else 1
                a0 = (hash01(k, 811 + side) - 0.5) * 1.4
                bx, by = ex0 + s0 * side * hw * 1.02, ey0 - 0.5 + a0 * hh * 0.6
                L0 = hw * (0.36 + 0.24 * hash01(k, 812 + side))
                mid = (bx - s0 * side * L0 * 0.5, by + a0 * 2.6 + (hash01(k, 813) - 0.5) * 2.0)
                end = (bx - s0 * side * L0, by + a0 * 4.6 + (hash01(k, 814) - 0.5) * 3.0)
                Q_, _ = _qm(hm, [(bx, by), mid, end], 2.2); vs.append(smooth(Q_, False))
                br = (mid[0] - s0 * side * L0 * 0.32, mid[1] + (1 if hash01(k, 815) > 0.5 else -1) * 3.4)
                Q_, _ = _qm(hm, [mid, br], 2.2); vs2.append(poly(Q_, False))
            c.line(_multi(vs), lw * 0.34, QV['vein'], 235 * red)
            c.line(_multi(vs2), lw * 0.2, QV['vein'], 210 * red)
        ic = mix(QV['iris'], QV['iris_red'], red)
        if red > 0.02: c.glow(IX, IY, ir * 2.2 * ifs, ir * 2.2, QV['iris_red'], 150 * red)
        c.radial(oval(IX, IY, ir * ifs, ir), IX, IY + ir * 0.15, ir * 1.05,
                 [(0, mix(ic, '#000000', 0.2), 255), (0.3, ic, 255), (0.62, mix(ic, '#a49ac0', 0.45 * (1 - red)) if red < 0.5 else mix(ic, '#ff8090', 0.3), 255),
                  (0.88, ic, 255), (1, mix(ic, '#000000', 0.6), 255)])
        if det >= 1:                                                       # iris fibres
            fb = []
            for k in range(12):
                a = 2 * PI * k / 12 + 0.3
                fb.append(poly([(IX + math.cos(a) * ir * 0.4 * ifs, IY + math.sin(a) * ir * 0.4),
                                (IX + math.cos(a) * ir * 0.84 * ifs, IY + math.sin(a) * ir * 0.84)], False))
            c.line(_multi(fb), lw * 0.09, mix(ic, '#ffffff', 0.35), 110)
        c.line(oval(IX, IY, ir * ifs, ir), lw * 0.22, mix(ic, '#000000', 0.7), 235)
        pr = ir * lerp(0.46, 0.15, st['pin'])
        c.fill(oval(IX, IY, pr * ifs, pr), '#050407')
        c.fill(oval(IX - ir * 0.34 * ifs, IY - ir * 0.36, ir * 0.26 * ifs, ir * 0.26), '#ffffff', 245)       # two highlights
        c.fill(oval(IX + ir * 0.36 * ifs, IY + ir * 0.3, ir * 0.11 * ifs, ir * 0.11), '#ffffff', 220)
        c.fill(_crescent(eye, 0, 3.2 * (1.0 - 0.6 * full)), '#5a4a66', 75)                  # the lid's shadow on the eye
    if red > 0.02 and det >= 1:                                             # an inflamed lower rim
        Q_, _ = _qm(hm, lo[1:-1], 2.0)
        c.line(smooth(Q_, False), lw * 0.34, '#c8263a', 210 * red)
    # heavy black upper liner, tapered, a wing past the outer corner
    wing = (ex0 + side * (hw * 1.02 + 6.5), ey0 - 6.6)
    thick = [0.4, 1.6, 2.9, 3.5, 1.9]
    top_ = [(x_, y_ - th_) for (x_, y_), th_ in zip(up, thick)]
    LT, _ = _qm(hm, top_ + [wing], 2.4)
    lid = smooth(U_ + [LT[-1]] + LT[:-1][::-1], True, 0.6)
    c.fill(lid, QV['lid'])
    if det >= 1:                                                            # 5 curled lashes at the outer corner, a crease
        lsh = []
        for k in range(5):
            f = 0.48 + k * 0.12
            bx, by = lerp(up[2][0], wing[0], f), lerp(up[2][1] - 2.6, wing[1] + 1.2, f)
            L0 = 5.4 + k * 0.7
            tx, ty = bx + side * (1.8 + k * 1.4), by - (L0 - k * 0.8)
            Q_, _ = _qm(hm, [(bx, by), (lerp(bx, tx, 0.42) - side * 0.7, lerp(by, ty, 0.72)), (tx, ty)], 2.6)
            lsh.append(smooth(Q_, False))
        c.line(_multi(lsh), lw * 0.32, QV['lid'], 255)
        crease = [(ex0 - side * hw * 0.7, ey0 - E['hh'] * 1.3), (ex0 + side * hw * 0.1, ey0 - E['hh'] * 1.75), (ex0 + side * hw * 0.92, ey0 - E['hh'] * 1.25)]
        Q_, _ = _qm(hm, crease, 2.0); c.line(smooth(Q_, False), lw * 0.26, QV['inner'], 175)
        Q_, _ = _qm(hm, [(ex0 + side * hw * 0.1, ey0 + hh * 0.97), (ex0 + side * hw * 0.62, ey0 + hh * 0.68), (ex0 + side * hw * 1.0, ey0 - 1.0)], 2.0)
        c.line(smooth(Q_, False), lw * 0.2, QV['inner'], 85)                 # a faint lower lash shade on the outer half
    return (X, Y, hw * fs, hh)


def _q_brow(c, hm, side, lw):
    E = _Q_EYE
    ex0 = side * E['dx']; by = E['y'] - 28.8
    top = [(ex0 - side * 14.0, by + 3.0), (ex0 + side * 2.0, by - 4.6), (ex0 + side * 21.0, by + 1.4)]
    bot = [(ex0 + side * 21.0, by + 2.4), (ex0 + side * 2.5, by - 2.0), (ex0 - side * 14.0, by + 5.6)]
    Q_, v = _qm(hm, top + bot, 3.0)
    if v < 0.05: return
    c.fill(smooth(Q_, True, 0.7), QV['lid'])


def _q_nose(c, hm, lw):
    """A long fine nose in the cast's line: one bridge line on the shadow side, the alar wings, the tip, two nostrils and
    a bridge highlight; turned, a profile wedge."""
    side = 1.0 if hm.st >= -0.02 else -1.0
    turned = abs(hm.st) > 0.34
    if not turned:
        sd = side if abs(hm.st) > 0.05 else 1.0
        Q_, v = _qm(hm, [(sd * 9.5, -27.0), (sd * 7.0, -6.0), (sd * 7.5, 14.0), (sd * 10.0, 25.0)], 10.0)
        if v > 0.0: c.line(smooth(Q_, False), lw * 0.24, QV['inner'], 125)
        wings = []
        for s2 in (-1, 1):
            Q_, v = _qm(hm, [(s2 * 8.0, 25.0), (s2 * 11.8, 30.5), (s2 * 10.8, 35.5), (s2 * 6.4, 37.2)], 12.0)
            if v > 0.0: wings.append(smooth(Q_, False))
        if wings: c.line(_multi(wings), lw * 0.3, QV['inner'], 205)
        Q_, v = _qm(hm, [(-3.6, 38.0), (0.0, 38.9), (3.6, 38.0)], 14.0)
        if v > 0.0: c.line(smooth(Q_, False), lw * 0.28, QV['inner'], 170)
        for s2 in (-1, 1):
            nx, ny, nv = hm.map1(s2 * 5.0, 36.0, 12.0)
            if nv > 0.1: c.fill(oval(nx, ny, 2.3 * hm.sx(s2 * 5.0, 36.0), 1.25), QV['inner'], 160)
        hx, hy, hv = hm.map1(-sd * 1.2, 10.0, 16.0)
        if hv > 0: c.glow(hx, hy, 2.6, 15.0, QV['skin_hi'], 175)
        hx, hy, hv = hm.map1(0.0, 31.0, 16.0)
        if hv > 0: c.glow(hx, hy, 4.6, 3.4, QV['skin_hi'], 205)
        return
    X, Y, V = hm.map([0, 0, 0, 0], [-8.0, 26.0, 34.5, 39.0], np.array([4.0, 17.0, 15.0, 6.0]))
    wedge = smooth([(X[0], Y[0]), (X[1], Y[1]), (X[2], Y[2]), (X[3] - side * 6, Y[3]), (X[0] - side * 8, Y[0] + 8)], True, 0.5)
    c.fill(wedge, QV['skin'])
    c.line(smooth([(X[0], Y[0]), (X[1], Y[1]), (X[2], Y[2]), (X[3] - side * 3, Y[3])], False), lw * 0.32, QV['inner'], 230)
    wx, wy, wv = hm.map1(side * 9.0, 32.0, 10.0)
    if wv > -0.4:
        c.line(smooth([(wx - side * 2.0, wy - 5.0), (wx + side * 1.6, wy - 1.0), (wx - side * 0.4, wy + 3.6)], False), lw * 0.28, QV['inner'], 200)


def _q_spade(cx, cy, h, w=None, up=True):
    """A spade pip of height h centred on (cx, cy) (tip up)."""
    w = w if w is not None else h * 0.86
    s = -1.0 if up else 1.0
    pts = [(0.0, -0.5), (0.1, -0.38), (0.26, -0.21), (0.42, -0.05), (0.5, 0.1), (0.45, 0.22), (0.32, 0.27), (0.18, 0.24), (0.07, 0.16),
           (0.1, 0.38), (0.2, 0.5), (-0.2, 0.5), (-0.1, 0.38), (-0.07, 0.16), (-0.18, 0.24), (-0.32, 0.27), (-0.45, 0.22), (-0.5, 0.1),
           (-0.42, -0.05), (-0.26, -0.21), (-0.1, -0.38)]
    return smooth([(cx + x * w, cy + (y if up else -y) * h) for x, y in pts], True, 0.55)


def _q_mouth(c, hm, P, st, det, t, lw, L):
    """Lips (S1), the drawn stair smile (S2), the split grin with flat human teeth and exposed gums (S3a), the flat line
    (OFF) and the jaw void with Noah13 inside (S4). The real lips talk on P.m_open; the drawing never moves."""
    o = clamp(P.m_open) * (1.0 - st['void'])
    my = _Q_MOUTH_Y
    _Q_GRIN[0] = None
    sp_open = st['open']
    voidk = st['void']
    flat = st['off'] * (1.0 - voidk)
    th_u = lerp(6.6, 2.2, flat); th_l = lerp(9.0, 2.6, flat)
    gap = 14.0 * o
    seam_u = [(-26.0, my), (-14.0, my - 0.4), (0.0, my + 0.3), (14.0, my - 0.4), (26.0, my)]
    upper = [(-26.0, my), (-16.0, my - th_u * 0.85), (-5.5, my - th_u * 1.1), (0.0, my - th_u * 0.7), (5.5, my - th_u * 1.1),
             (16.0, my - th_u * 0.85), (26.0, my)]
    seam_l = [(26.0, my), (14.0, my + gap * 0.8), (0.0, my + gap), (-14.0, my + gap * 0.8), (-26.0, my)]
    lower = [(26.0, my), (16.0, my + gap * 0.8 + th_l * 0.78), (0.0, my + gap + th_l), (-16.0, my + gap * 0.8 + th_l * 0.78), (-26.0, my)]
    drawk = st['draw']
    # ---- S3a: the mouth splits open along the drawing (a deep grin of flat human teeth, the gums exposed)
    if sp_open > 0.01 and voidk < 0.99:
        top, bot, ytop = _q_grin_shape(sp_open, P.m_open, getattr(P, 'q_widen', 0.0))
        TQ, _ = _qm(hm, top, 3.0); BQ, _ = _qm(hm, bot, 3.0)
        inner = poly(TQ + BQ[1:-1], True)
        _Q_GRIN[0] = inner
        g_ = clamp(sp_open * 1.5)
        cx0, cy0, _ = hm.map1(0.0, my + 20.0, 2.0)
        c.fill(inner, QV['mouth'])
        c.glow(cx0, cy0 + 4, 50.0 * hm.sx(0, my), 24.0, '#0a0206', 210 * sp_open)
        with c.clip(inner):
            # the upper gum: a pink band along the stepped top edge (the lip pulled up off it)
            gum_h = 3.6
            gq, _ = _qm(hm, [(x, y + gum_h * 0.5) for x, y in top], 3.0)
            c.line(poly(gq, False), gum_h * 2.4, QV['gum'], 245, 'butt')
            c.line(poly([(x, y) for x, y in _qm(hm, [(x, y + gum_h * 1.15) for x, y in top], 3.0)[0]], False), lw * 0.18, '#a84858', 200)
            # 14 upper teeth hanging from the gum: 8 across the lips, one on every tread (a staircase of teeth)
            tw = [5.2, 6.0, 6.6, 7.6, 7.6, 6.6, 6.0, 5.2]; sc = 52.0 / sum(tw)
            xcur = -26.0; teeth = []
            for w_ in tw:
                w_ *= sc; teeth.append((xcur + 0.25, xcur + w_ - 0.25, 14.5)); xcur += w_
            for s_ in (-1, 1):
                for (a_, b_), ln_ in zip(((26.5, 37.0), (37.8, 48.3), (49.1, 59.4)), (12.0, 10.5, 9.0)):
                    teeth.append(((a_, b_) if s_ > 0 else (-b_, -a_)) + (ln_,))
            tp = skia.Path(); lows = {}
            for xa, xb, ln_ in teeth:
                xm = (xa + xb) / 2.0
                y0 = ytop(xm) + gum_h * 0.9
                hgt = ln_ * g_
                lows[round(xm, 2)] = y0 + hgt
                q, _v = _qm(hm, [(xa, y0 - 1.0), (xb, y0 - 1.0), (xb - 0.2, y0 + hgt - 1.8), (xb - 1.2, y0 + hgt), (xa + 1.2, y0 + hgt),
                                 (xa + 0.2, y0 + hgt - 1.8)], 3.2)
                tp.addPath(smooth(q, True, 0.3))
            # 14 lower teeth standing on the bottom curve, their tops a dark gap below the upper row
            arc = bot[3:-3]
            Ls = [0.0]
            for a_, b_ in zip(arc[:-1], arc[1:]): Ls.append(Ls[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
            tot = Ls[-1] or 1.0
            lp = skia.Path()
            gap_t = 2.4 + 9.0 * clamp(P.m_open)
            for k in range(14):
                d0, d1 = tot * (0.02 + 0.96 * k / 14.0), tot * (0.02 + 0.96 * (k + 0.9) / 14.0)
                p0 = float(np.interp(d0, Ls, [p[0] for p in arc])), float(np.interp(d0, Ls, [p[1] for p in arc]))
                p1 = float(np.interp(d1, Ls, [p[0] for p in arc])), float(np.interp(d1, Ls, [p[1] for p in arc]))
                xm = (p0[0] + p1[0]) / 2.0; yb = (p0[1] + p1[1]) / 2.0 - 2.6
                yt_up = ytop(xm) + gum_h * 0.9 + 12.0 * g_ * (1.0 - 0.25 * min(1.0, abs(xm) / 45.0))
                hgt = min(11.0 * g_, max(0.0, yb - yt_up - gap_t))
                if hgt < 1.0: continue
                q, _v = _qm(hm, [(p0[0], p0[1] - 2.6), (p1[0], p1[1] - 2.6), (p1[0] + 0.1, yb - hgt + 1.6), (p1[0] - 1.0, yb - hgt),
                                 (p0[0] + 1.0, yb - hgt), (p0[0] - 0.1, yb - hgt + 1.6)], 3.2)
                lp.addPath(smooth(q, True, 0.3))
            gq2, _ = _qm(hm, [(x, y - 1.6) for x, y in arc], 3.0)
            c.line(poly(gq2, False), 5.5, QV['gum'], 235, 'butt')
            allt = skia.Path(tp); allt.addPath(lp)
            c.fill(allt, QV['teeth'])
            Lx, Ly, _ = hm.map1(-60.0, my, 3.0); Rx, Ry, _ = hm.map1(60.0, my, 3.0)
            c.grad(allt, Lx, Ly, Rx, Ry, [(0, '#8a7c72', 190), (0.2, '#d8d0c6', 90), (0.34, '#ffffff', 0), (0.66, '#ffffff', 0),
                                          (0.8, '#d8d0c6', 90), (1, '#8a7c72', 190)])
            c.fill(_crescent(tp, 0, 2.2), '#c8bcae', 120)              # the shade under the gum on each upper tooth
            c.fill(_crescent(lp, 0, -1.8), '#c8bcae', 100)
            c.line(allt, lw * 0.22, QV['teeth_line'], 235)
            if det >= 1:                                                # a glint on the front teeth
                gl = skia.Path()
                for xa, xb, ln_ in teeth[2:6]:
                    xm = (xa + xb) / 2.0; X, Y, v = hm.map1(xm - 1.2, ytop(xm) + gum_h + 3.0, 3.4)
                    if v > 0: gl.addOval(skia.Rect.MakeLTRB(X - 0.9, Y - 2.4, X + 0.9, Y + 2.4))
                c.fill(gl, '#ffffff', 200 * g_)
        # the lips stretched round the split: a thin upper lip over the middle, the lower lip along the bottom edge
        mid = [(x, y) for x, y in top if abs(x) <= 26.0]
        UQ, _ = _qm(hm, mid + [(x, y - 3.4 * (1.0 - (abs(x) / 26.0) ** 2) - 0.6) for x, y in mid[::-1]], 3.0)
        c.fill(smooth(UQ, True, 0.6), QV['lip'], 255)
        lowlip = [(x, y + 0.8 + 2.6 * (1.0 - (abs(x) / 60.0) ** 2)) for x, y in bot[2:-2]]
        LQ, _ = _qm(hm, bot[2:-2] + lowlip[::-1], 3.0)
        lpth = smooth(LQ, True, 0.6)
        c.fill(lpth, QV['lip'], 255)
        BQ2, _ = _qm(hm, [(x, y + 0.5) for x, y in bot[3:-3]], 3.0)
        c.line(smooth(BQ2, False), lw * 0.5, mix(QV['lip'], '#000000', 0.3), 150)
        c.line(inner, lw * 0.34, QV['lip_line'], 235)
    # ---- S4: the jaw drops into a tall glossy void with Noah13's face in it
    if voidk > 0.01:
        vw = lerp(26.0, 44.0, voidk); vt = lerp(my, my - 10.0, voidk); vb = lerp(my + 4.0, my + 56.0, voidk)
        vp = [(0.0, vt - 1.0), (vw * 0.62, vt + 0.5), (vw * 0.98, vt + (vb - vt) * 0.32), (vw * 0.92, vt + (vb - vt) * 0.7), (vw * 0.5, vb - 2.0),
              (0.0, vb), (-vw * 0.5, vb - 2.0), (-vw * 0.92, vt + (vb - vt) * 0.7), (-vw * 0.98, vt + (vb - vt) * 0.32), (-vw * 0.62, vt + 0.5)]
        VQ, _ = _qm(hm, vp, 3.0)
        vpath = smooth(VQ, True, 0.85)
        _Q_GRIN[0] = vpath
        lipr = [(x * 1.12 + (0.0 if x == 0 else 1.5 * (1 if x > 0 else -1)), vt + (y - vt) * 1.04 + (y > (vt + vb) / 2) * 2.5) for x, y in vp]
        RQ, _ = _qm(hm, lipr, 3.0)
        c.fill(smooth(RQ, True, 0.85), QV['lip'])
        cx_, cy_, _ = hm.map1(0.0, (vt + vb) * 0.5, 3.0)
        c.fill(vpath, QV['void1'])
        bb = vpath.getBounds()
        c.radial(vpath, cx_, cy_ - bb.height() * 0.08, max(bb.width(), bb.height()) * 0.55, [(0, QV['void0'], 255), (0.65, QV['void0'], 240), (1, QV['void1'], 0)], sy=1.25)
        with c.clip(vpath):
            if st['noah'] > 0.02 and voidk > 0.4: _q_noah_in_void(c, hm, P, st, cx_, cy_ + bb.height() * 0.08, bb.width() * 0.4, t, det)
            tp = skia.Path()                               # one short row of 6 upper teeth
            for k in range(6):
                xa = -15.0 + k * 5.0
                q, _v = _qm(hm, [(xa + 0.3, vt - 1.0), (xa + 4.7, vt - 1.0), (xa + 4.5, vt + 6.5), (xa + 2.5, vt + 7.4), (xa + 0.5, vt + 6.5)], 3.2)
                tp.addPath(smooth(q, True, 0.35))
            c.fill(tp, QV['teeth'], 255 * voidk); c.line(tp, lw * 0.2, QV['teeth_line'], 220 * voidk)
            hl = [(-vw * 0.7, vt + (vb - vt) * 0.25), (-vw * 0.82, vt + (vb - vt) * 0.55), (-vw * 0.6, vt + (vb - vt) * 0.82)]
            HQ, _ = _qm(hm, hl, 3.0); c.line(smooth(HQ, False), lw * 0.5, '#ffffff', 95 * voidk)
        c.line(vpath, lw * 0.4, QV['lip_line'], 255)
    # ---- closed / talking lips (S1, S2, OFF): the real lips (thin in OFF: the grin dropped to a flat line)
    if sp_open < 0.5 and voidk < 0.5:
        a_l = 255 * (1.0 - clamp(sp_open * 2.0)) * (1.0 - clamp(voidk * 2.0))
        UQ, uv = _qm(hm, upper + seam_u[::-1][1:-1], 6.0)
        LQ, _ = _qm(hm, seam_l + lower[::-1][1:-1], 6.0)
        if uv > -0.2:
            if o > 0.02:                                    # parted lips: the dark inside, a glint of top teeth
                IQ, _ = _qm(hm, seam_u + seam_l[1:-1], 5.0)
                ip = smooth(IQ, True, 0.8)
                c.fill(ip, QV['mouth'], a_l)
                with c.clip(ip):
                    TQ, _ = _qm(hm, [(-12.0, my - 1.0), (12.0, my - 1.0), (11.0, my + 3.4), (-11.0, my + 3.4)], 5.0)
                    c.fill(smooth(TQ, True, 0.5), QV['teeth'], a_l * clamp(o * 3.0))
            up_p = smooth(UQ, True, 0.75); lo_p = smooth(LQ, True, 0.75)
            lc = mix(QV['lip'], QV['scar'], 0.5 * flat)
            c.fill(up_p, lc, a_l); c.fill(lo_p, lc, a_l)
            c.fill(_crescent(up_p, 0, 2.2), mix(lc, '#000000', 0.32), a_l * 0.6)
            c.fill(_crescent(lo_p, 0, -2.6), mix(lc, '#000000', 0.25), a_l * 0.45)
            if det >= 1 and flat < 0.5:                     # gloss on the lower lip, a light on the cupid's bow
                GQ, _ = _qm(hm, [(-9.0, my + gap + th_l * 0.42), (-2.0, my + gap + th_l * 0.6), (6.0, my + gap + th_l * 0.48)], 7.0)
                c.line(smooth(GQ, False), lw * 0.4, QV['lip_gloss'], a_l * 0.9)
                BQ, _ = _qm(hm, [(-6.5, my - th_u * 1.25), (0.0, my - th_u * 0.95), (6.5, my - th_u * 1.25)], 7.0)
                c.line(smooth(BQ, False), lw * 0.22, QV['skin_hi'], a_l * 0.8)
            c.line(up_p, lw * 0.3, QV['lip_line'], a_l); c.line(lo_p, lw * 0.3, QV['lip_line'], a_l)
            SQ, _ = _qm(hm, seam_u, 6.0); c.line(smooth(SQ, False), lw * 0.34, QV['lip_line'], a_l)
    # ---- the drawing itself (S2: drawn past the lips; S3a: the edge of the grin; OFF/S4: scars)
    if drawk > 0.01:
        scar = max(st['off'], voidk)
        colr = mix(QV['lip'], QV['scar'], 0.55 * scar)
        for s_ in (-1, 1):
            pts = [(s_ * x, y) for x, y in _Q_STEPS]
            _q_brush_steps(c, hm, pts, 4.6 * (1.0 - 0.25 * scar), colr, 255, det, 7 + s_, drawk, scar)
    # her voice: a thin red glow on the mouth while she speaks
    if o > 0.03 or (sp_open > 0.3 and P.m_open > 0.03):
        gx, gy, gv = hm.map1(0.0, my + 6, 8.0)
        if gv > 0: c.glow(gx, gy, 48.0 * hm.sx(0, my), 20.0, QV['lip_glow'], (90 - 40 * sp_open) * clamp(max(o, P.m_open) * 2.5))


def _q_noah_in_void(c, hm, P, st, cx, cy, w, t, det):
    """Noah13's face floating in the void (40 % of its width), pixel-sort glitched, mouthing his voice (line 249)."""
    sp = CAST['noah13']
    P2 = Pose('calm_kid'); P2.t = t
    P2.m_open = clamp(P.m_open * 1.15); P2.m_round = P.m_round; P2.teeth = max(0.4, P.teeth); P2.m_wide = P.m_wide
    P2.look_y = -0.35; P2.lock = 1.0; P2.brow_up = 0.35; P2.wide = 0.15; P2.wet = 0.5
    s = w / (2.0 * max(sp['head_ws']))
    fr = int(math.floor(t * 60.0 + 1e-6))
    g = 0.35 + 0.65 * st['glitch']
    flick = hash01(fr // 3, 911)
    alpha = 1.0 if flick > 0.12 else 0.45
    nb = 7
    h = 240.0 * s
    top = cy - h * 0.55
    light = dict(rim='#ff4060', rim_a=120, side=1, key=-0.2)
    c.cv.saveLayer(None, skia.Paint(Alphaf=float(alpha)))
    try:
        for b in range(nb):
            y0 = top + b * h * 1.1 / nb; y1 = y0 + h * 1.1 / nb + 0.6
            r = hash01(b * 31 + fr // 3, 913)
            off = (r - 0.5) * w * 0.18 * g if r > 0.45 else 0.0
            with c.clip(rect(cx - w * 2, y0, w * 4, y1 - y0)):
                hc = c.sub(cx + off, cy, 0.0, s)
                draw_head_local(hc, 'noah13', P2, 0.0, -0.08, det, t, light, sp)
        # pixel-sort smear: two bands dragged sideways in the red
        for b in range(2):
            r = hash01(b + fr // 4, 917)
            yy = top + h * (0.2 + 0.6 * r)
            c.fill(rect(cx - w * 0.6 + (r - 0.5) * w * 0.4, yy, w * (0.6 + 0.6 * r), h * 0.03), '#ff4060', 90 * g)
    finally:
        c.cv.restore()
    c.glow(cx, cy, w * 0.9, h * 0.6, '#ff2040', 45)


def _q_face_extras(c, hm, P, st, det, lw):
    """Beauty mark (always); the grin's cheek folds (S3a+, 4 a side in S3c) and the bunched skin under the eyes; S3c's
    porcelain cracks and black mascara tears (2 an eye: one drips into the grin, one runs to the jaw)."""
    bx, by, bv = hm.map1(44.0, 17.0, 2.0)
    if bv > 0.1:
        fsx = hm.sx(44.0, 17.0)
        sp_ = _q_spade(0.0, 0.0, 8.4, 7.2)
        m = skia.Matrix(); m.setScale(fsx, 1.0); m.postTranslate(bx, by); sp_.transform(m)
        c.fill(sp_, QV['lid'])
    op = st['open']; full = st['full']
    E = _Q_EYE
    if op > 0.02 and det >= 1:                              # cheek folds round the grin corners
        fl, fl2 = [], []
        nf = 2 + int(round(2 * full))
        for s_ in (-1, 1):
            for k in range(nf):
                pts = [(s_ * (56.0 + 2.0 * k), 14.0 - 4.0 * k), (s_ * (66.0 + 3.8 * k), 22.0 - 1.0 * k), (s_ * (70.0 + 4.0 * k), 38.0 + 3.0 * k),
                       (s_ * (64.0 + 3.0 * k), 54.0 + 6.0 * k)]
                Q_, v = _qm(hm, pts, 2.0)
                if v > 0.05: (fl if k < 2 else fl2).append(smooth(Q_, False))
            if full > 0.05:                                 # the cheeks push the lower lids up: two arcs under each eye
                for k in range(2):
                    yy = E['y'] + E['hh'] * 1.9 + 4.5 * k
                    pts = [(s_ * (E['dx'] - 12.0), yy - 1.0), (s_ * (E['dx'] + 2.0), yy + 2.4), (s_ * (E['dx'] + 15.0), yy - 0.5)]
                    Q_, v = _qm(hm, pts, 2.0)
                    if v > 0.05: fl2.append(smooth(Q_, False))
        if fl: c.line(_multi(fl), lw * 0.3, QV['inner'], 205 * op)
        if fl2: c.line(_multi(fl2), lw * 0.24, QV['inner'], 175 * full)
    if full < 0.02: return
    a = 255 * full
    if det >= 1:                                            # 3 short porcelain cracks: temples and jaw
        cr = []
        for pts in ([(-70.0, -52.0), (-63.0, -46.0), (-65.5, -40.0), (-56.0, -33.0)], [(-63.0, -46.0), (-58.0, -50.5)],
                    [(68.0, -58.0), (61.0, -51.0), (63.0, -45.5), (54.5, -40.0)],
                    [(40.0, 100.0), (34.0, 94.0), (37.0, 88.0), (29.0, 82.0)]):
            Q_, v = _qm(hm, pts, 2.0)
            if v > 0.05: cr.append(poly(Q_, False))
        if cr:
            m_ = _multi(cr)
            c.line(m_, lw * 0.26, QV['crack'], a)
            q = skia.Path(m_); q.offset(0.9, 0.9); c.line(q, lw * 0.16, '#ffffff', a * 0.55)
    _, _, ytop = _q_grin_shape(1.0, 0.0, 0.0)
    with (c.clip(_Q_GRIN[0], diff=True) if _Q_GRIN[0] is not None else _noop()):     # the tears run behind the grin / void
        _q_tears(c, hm, st, op, full, ytop)


def _q_tears(c, hm, st, op, full, ytop):
    E = _Q_EYE
    for s_ in (-1, 1):
        x0 = s_ * (E['dx'] - 5.0); y0 = E['y'] + E['hh'] * 0.9
        _q_soft(c, hm, [(x0 - 6, y0 - 1), (x0 + 6, y0 - 1), (x0 + 5, y0 + 9), (x0 - 4, y0 + 8)], '#2a2030', 120 * full, 2.5, 2.0)   # the smudge
        y1 = (ytop(x0) - 1.0) if op > 0.3 else 98.0
        ys = np.linspace(y0, y1, 12)
        _q_tear(c, hm, [(x0 + s_ * (1.3 * math.sin(yy * 0.11) + 0.03 * (yy - y0)), float(yy)) for yy in ys], full, 3 + s_)
        xo = s_ * (E['dx'] + 11.0)
        path = [(xo, y0 - 1.0), (s_ * 56.0, 14.0), (s_ * 63.0, 26.0), (s_ * 64.0, 42.0), (s_ * 58.0, 62.0), (s_ * 45.0, 84.0)]
        dense = []
        for (xa, ya), (xb, yb) in zip(path[:-1], path[1:]):
            for u in np.linspace(0, 1, 4, endpoint=False): dense.append((xa + (xb - xa) * u, ya + (yb - ya) * u))
        dense.append(path[-1])
        _q_tear(c, hm, dense, full, 9 + s_)


def _q_ring_pt(hm, phi, y0, grow):
    """A point on a ring round the head (phi 0 = front) at height y0, grow units outside the skull: X, Y, vis."""
    w = max(float(hm.W(y0)), 1.0) + grow
    d = hm.DF if math.cos(phi) > 0 else hm.DB
    px, pz = w * math.sin(phi), d * w * math.cos(phi)
    yj = float(hm.J(y0))
    y1 = yj * hm.cp + pz * hm.spi
    z1 = pz * hm.cp - yj * hm.spi
    X = px * hm.ct + z1 * hm.st
    vis = math.cos(phi) * hm.ct - math.sin(phi) * hm.st
    return X, y1, vis


def _q_crown(c, hm, det, t, lw, which):
    """Crown of spades: a thin silver band with 5 black spade points (centre 0.22 H, then 0.16, outer 0.12). which:
    'back' draws the points behind the head (before it), 'front' the band and the front points."""
    H = 240.0
    phis = (-0.98, -0.5, 0.0, 0.5, 0.98)
    hs = (0.12, 0.16, 0.22, 0.16, 0.12)
    y0 = -93.0
    items = []
    for phi, hk in zip(phis, hs):
        X, Y, v = _q_ring_pt(hm, phi, y0, 9.0)
        items.append((v, X, Y, phi, hk * H))
    if which == 'front':                                    # the band (visible half), behind the front points
        ph = np.linspace(-PI, PI, 64)
        P_ = [_q_ring_pt(hm, float(p), y0, 9.0) for p in ph]
        vis = [p for p in P_ if p[2] > -0.05]
        if len(vis) > 2:
            vis.sort(key=lambda p: p[0])
            top = [(p[0], p[1] - 3.6) for p in vis]; bot = [(p[0], p[1] + 3.6) for p in vis[::-1]]
            band = smooth(top + bot, True, 0.5)
            c.fill(band, QV['silver'])
            bb = band.getBounds()
            c.grad(band, 0, bb.top(), 0, bb.bottom(), [(0, QV['silver_hi'], 255), (0.45, QV['silver'], 0), (1, QV['silver_dk'], 255)])
            c.line(band, lw * 0.32, QV['line'])
    for v, X, Y, phi, h in items:
        if (which == 'front') != (v > -0.05): continue
        fsx = max(0.28, abs(math.cos(phi) * hm.ct - math.sin(phi) * hm.st))
        pip_h = h * 0.74
        pw = pip_h * 0.9
        pip = _q_spade(0.0, -h + pip_h * 0.5, pip_h, pw)
        stem = poly([(-pw * 0.09, -h + pip_h * 0.85), (pw * 0.09, -h + pip_h * 0.85), (pw * 0.18, 0.0), (-pw * 0.18, 0.0)])
        sp_ = union(pip, stem) or pip
        m = skia.Matrix(); m.setScale(fsx, 1.0); m.postTranslate(X, Y - 1.5); sp_.transform(m)
        w = pw * 0.5 * fsx
        c.fill(sp_, QV['black'] if v > -0.05 else '#06050a')
        if v > -0.05:
            c.line(smooth([(X + 0.1 * w, Y - h * 0.95), (X + 0.62 * w, Y - h * 0.82), (X + 0.92 * w, Y - h * 0.64)], False), lw * 0.26, QV['silver_hi'], 230)
            c.line(poly([(X + 0.12 * w, Y - h * 0.45), (X + 0.18 * w, Y - h * 0.06)], False), lw * 0.2, QV['silver'], 200)
        c.line(sp_, lw * 0.36, QV['line'])
        if v > -0.05 and det >= 1:                           # a small silver bead where the point meets the band
            c.fill(oval(X, Y - 1.5, 2.6 * fsx, 2.6), QV['silver']); c.fill(oval(X - 0.7, Y - 2.3, 0.9, 0.9), '#ffffff', 220)
    if which == 'front' and det >= 1:                       # a glint that travels along the band
        g = (t * 0.35) % 1.0
        X, Y, v = _q_ring_pt(hm, -1.2 + 2.4 * g, y0, 9.0)
        if v > 0.1:
            a = 255 * math.sin(PI * g) ** 2
            c.fill(_multi([poly([(X - 9, Y), (X + 9, Y)], False), poly([(X, Y - 9), (X, Y + 9)], False)]), '#ffffff', 0)
            c.line(_multi([poly([(X - 8, Y), (X + 8, Y)], False), poly([(X, Y - 8), (X, Y + 8)], False)]), lw * 0.18, '#ffffff', a)
            c.glow(X, Y, 7.0, 7.0, '#ffffff', a * 0.7)


def _q_hair_region(hm, hide, grow=10.0, y_bot=150.0):
    """Front hair over the skull (head coords): a volume (skull grown, hanging straight from the widest point) minus the
    face window under the centre parting; hide 0..1 closes the curtains over the face (S0)."""
    ys = np.linspace(-132.0, y_bot, 30)
    wmax = float(hm.W(0.0)) + grow
    L, R = [], []
    for y in ys:
        if y < 0.0:
            w = float(hm.W(max(y, -120.0))) + grow * (0.8 + 0.2 * clamp((y + 120) / 120.0)) if y > -120 else 18.0
            w = max(w, 12.0)
        else:
            w = wmax + 0.04 * y
        xl, xr = hm.extent(w)
        yy = float(hm.J(min(y, 120.0))) * hm.cp + (y - min(y, 120.0))
        L.append((xl, yy)); R.append((xr, yy))
    vol = smooth(R + L[::-1], True, 0.8)
    face_v = hm.map1(0, 0)[2]
    if face_v < -0.05 or hide > 0.97: return vol, None
    # the face window (front surface coords): parting, hairline, along the cheeks inside the curtains, round the jaw
    hk = clamp(hide)
    win = [(0.0, -77.0), (14.0, -74.0), (30.0, -66.0), (44.0, -53.0), (55.0, -36.0), (63.0, -16.0), (69.0, 8.0), (71.0, 28.0),
           (68.0, 50.0), (61.0, 70.0), (53.0, 90.0), (48.0, 106.0), (47.0, 130.0), (48.0, 160.0), (50.0, 260.0)]
    # the curtains sweep over the temples and close in along the jaw: the face shows as a long oval, widest at the cheekbones
    pts = []
    for s_ in (1, -1):
        seq = win if s_ > 0 else win[::-1]
        for x, y in seq:
            xx = s_ * x * (1.0 - hk * (1.0 if y > -70 else 0.5))
            pts.append((xx, y))
    # drop the duplicated parting point
    pts = pts[:len(win)] + pts[len(win) + 1:]
    W_, _ = _qm(hm, [(x, min(y, 118.0)) for x, y in pts], 4.0)
    W_ = [(x, y + (max(0.0, py - 118.0))) for (x, y), (px, py) in zip(W_, pts)]
    kf = clamp((abs(hm.st) - 0.6) / 0.3)                     # turned: the far curtain goes behind the face profile
    if kf > 0:
        out = []
        for (x, y), (px, py) in zip(W_, pts):
            if px * hm.st > 0:
                xl_, xr_ = hm.extent(float(hm.W(min(max(py, -120.0), 120.0))) + 24.0)
                lim = xr_ if hm.st > 0 else xl_
                x = lerp(x, max(x, lim) if hm.st > 0 else min(x, lim), kf)
            out.append((x, y))
        W_ = out
    window = smooth(W_, True, 0.75)
    return vol, window


def _q_hair_front(c, hm, P, st, det, t, lw):
    """Cap and curtains to below the jaw: base #0d0b14, a blue-violet sheen band at 30 % of its length, dark strand
    lines, light highlights, a pale parting line."""
    vol, window = _q_hair_region(hm, st['hide'])
    hair = minus(vol, window) if window is not None else vol
    if hair is None: return
    c.fill(hair, QV['hair'])
    bb = hair.getBounds()
    with c.clip(hair):
        # sheen band at 30 % of the length: a ring of blue-violet light round the crown
        ph = np.linspace(-PI * 0.95, PI * 0.95, 40)
        band = [(p[0], p[1] + 14.0 * (1.0 - math.cos(q)), p[2]) for q, p in ((q, _q_ring_pt(hm, float(q), -70.0, 9.0)) for q in ph) if p[2] > -0.1]
        if len(band) > 2:
            band.sort(key=lambda p: p[0])
            bp = poly([(p[0], p[1]) for p in band], False)
            c.line(bp, 14.0, QV['hair_sheen'], 200); c.line(bp, 6.0, mix(QV['hair_sheen'], QV['hair_hi'], 0.6), 160)
        c.radial(None, -20.0, -110.0, 120.0, [(0, QV['hair_sheen'], 120), (1, QV['hair_sheen'], 0)], sy=0.7, clip=False)
        if det >= 1:                                        # strand lines from the parting, falling straight below the jaw
            dk, hi = [], []
            face_v = hm.map1(0, 0)[2]
            for s_ in (-1, 1):
                for k in range(5 if det >= 2 else 3):
                    f = (k + 0.6) / 5.0
                    path = []
                    for y in np.linspace(-118.0, 148.0, 12):
                        if y < 0:
                            w = float(hm.W(max(y, -119.0))) + 8.0
                            x0 = s_ * w * (0.25 + 0.75 * f) * clamp((y + 124.0) / 70.0) ** 0.6
                            X, Y, v = hm.map1(x0, y, 10.0 * f)
                        else:
                            wm = float(hm.W(0.0)) + 8.0
                            xl, xr = hm.extent(wm - 18.0 * (1.0 - f))
                            X = (xr if s_ > 0 else xl); Y = float(hm.J(min(y, 120.0))) * hm.cp + max(0.0, y - 120.0)
                        path.append((X, Y))
                    (dk if k % 2 == 0 else hi).append(smooth(path, False))
            c.line(_multi(dk), lw * 0.3, QV['hair_dark'], 220)
            c.line(_multi(hi[:4]), lw * 0.22, QV['hair_hi'], 150)
            if face_v > 0.0:
                X0, Y0, _ = hm.map1(0, -124.0, 10.0); X1, Y1, _ = hm.map1(0, -86.0, 6.0)
                c.line(poly([(X0, Y0), (X1, Y1)], False), lw * 0.28, QV['parting'], 210)
    yb_ = float(hm.J(120.0)) * hm.cp + 22.0
    with c.clip(rect(-600.0, -600.0, 1200.0, 600.0 + yb_)):
        c.line(hair, lw * 0.75, QV['line'])
    # two loose strands across her left cheek (they never move)
    face_v = hm.map1(0, 0)[2]
    if face_v > 0.05 and st['hide'] < 0.5 and det >= 1:
        ls = []
        for k, (x0, x1, x2) in enumerate(((52.0, 44.0, 50.0), (60.0, 51.0, 58.0))):
            Q_, v = _qm(hm, [(x0, -70.0), (x1 + 4.0, -30.0), (x1, 10.0), (x2, 52.0), (x2 + 6.0, 92.0)], 6.0)
            if v > 0: ls.append(smooth(Q_, False))
        if ls:
            c.line(_multi(ls), lw * 0.36, QV['hair'], 255)
            c.line(_multi(ls), lw * 0.12, QV['hair_hi'], 120)


def _q_head(c, P, yaw, pitch, det, t, light=None, crown=True):
    """The queen's head on Ctx c (head coords, crown -120 .. chin +120), all stages. Returns the head map. The head is
    drawn 0.88x narrow, so the face that shows between the curtains reads as a long oval (1.35 : 1)."""
    c = c.sub(0.0, 0.0, 0.0, _Q_NARROW, 1.0)
    st = _qst(P)
    QL = _ql(light)
    hm = _QHM(yaw, pitch, stretch=st['void'], jaw=5.0 * clamp(P.m_open) * (1.0 - st['open']))
    lw = c.lw * 0.75
    face_v = hm.map1(0, 0)[2]
    # back hair volume behind the skull
    vol, _w = _q_hair_region(hm, 1.0, grow=12.0, y_bot=112.0)
    c.fill(vol, QV['hair'])
    c.line(vol, lw * 0.7, QV['line'])
    if crown: _q_crown(c, hm, det, t, lw, 'back')
    sil = hm.silhouette(y_top=-120, y_bot=120, n=40)
    bb = sil.getBounds()
    # porcelain lit from below the front by a cool white key, then modelled with a cool contour (no blush)
    c.grad(sil, 0, bb.top(), 0, bb.bottom(), [(0, mix(QV['skin'], QV['skin_sh'], 0.35), 255), (0.36, QV['skin'], 255),
                                              (0.78, mix(QV['skin'], QV['skin_hi'], 0.45), 255), (1, mix(QV['skin'], QV['skin_sh'], 0.2), 255)])
    if face_v > -0.3:
        with c.clip(sil):
            _q_face_model(c, hm, st, QL, det)
    c.fill(_crescent(sil, -QL['side'] * 6.0, 2.0), QV['skin_sh'], 130)
    if QL.get('split'):                                     # half in one world's light, half in the other's (H1, the doorway)
        g0, g1 = QL['split']
        c.grad(sil, -100.0 * QL['side'], 0, 100.0 * QL['side'], 0, [(0, g1, 70), (0.42, g1, 0), (0.58, g0, 0), (1, g0, 80)])
    c.fill(_crescent(sil, QL['side'] * 4.5, 1.0), QL['rim'], QL['rim_a'] * 0.85)
    if QL.get('rim2'): c.fill(_crescent(sil, -QL['side'] * 4.0, 1.0), QL['rim2'], QL['rim_a'] * 0.6)
    if face_v > -0.35:
        with (c.clip(hm.silhouette(grow=1.5)) if abs(hm.st) > 0.2 else _noop()):
            for s_ in (-1, 1): _q_eye(c, hm, P, s_, st, det, lw)
            for s_ in (-1, 1): _q_brow(c, hm, s_, lw)
            _q_mouth(c, hm, P, st, det, t, lw, QL)
            _q_face_extras(c, hm, P, st, det, lw)
    c.line(sil, lw, QV['line'])
    if face_v > -0.35: _q_nose(c, hm, lw)
    _q_hair_front(c, hm, P, st, det, t, lw)
    if crown: _q_crown(c, hm, det, t, lw, 'front')
    return hm


# ---------------------------------------------------------------------------------------------- the figure
def _q_proj_floor(B, x, y, z):
    """Floor-anchored point (skirt, train, feet): yaw only, depth lowers it a little (the camera looks slightly down)."""
    X = x * B.ct + z * B.st
    Z = -x * B.st + z * B.ct
    return X, y + 0.12 * Z, Z


def _q_ell(B, cx, cy, cz, w, d, floor=False, dback=None, n=28):
    """Projected cross-section ellipse (half width w, half depth d; dback for the back half: the train)."""
    out = []
    for k in range(n):
        a = 2 * PI * k / n
        dd = d if math.sin(a) >= 0 or dback is None else dback
        x, z = cx + w * math.cos(a), cz + dd * math.sin(a)
        if floor:
            X, Y, Z = _q_proj_floor(B, x, cy, z)
        else:
            X, Y, s_, Z = B.p3(x, cy, z)
        out.append((X, Y, Z))
    return out


def _q_hull_path(pts, k=0.85):
    h = _hull([(p[0], p[1]) for p in pts])
    return smooth(h, True, k) if len(h) > 2 else skia.Path()


def _q_skirt(c, B, P, det, t, lw, QL):
    """The bell gown to the floor (hem 1.6x the shoulders) with a train trailing 15 % behind; seated it drapes over
    the lap from the knees. The hem border is a playing-card border: white spade pips between two thin red lines."""
    u = clamp(P.sit)
    sway = 3.0 * getattr(P, 'hem', 0.0) + 2.0 * P.sec_x
    lv = []                                                  # (cx, cy, cz, w, d, floor, dback)
    lv.append((0.0, -598.0, 0.0, 50.0, 34.0, False, None))
    lv.append((0.0, -540.0, 0.0, 70.0, 48.0, False, None))
    yk = lerp(-300.0, -268.0 + B.bob * 0.0, u)
    knee_y = -520.0 + B.bob + lerp(220.0, 6.0, u) - B.bob * (1.0 - u) * 0.0
    knee_y = lerp(-300.0, -520.0 + B.bob + 10.0, u)
    knee_z = 245.0 * u
    lv.append((0.0, knee_y, knee_z * 0.98, lerp(118.0, 98.0, u), lerp(108.0, 66.0, u), True, None))
    hem_z = lerp(0.0, 300.0, u)
    hw = lerp(146.0, 104.0, u)
    lv.append((sway, -2.0, hem_z, hw, hw * 0.92, True, hw * 0.92 * (1.0 + 0.45 * (1.0 - u))))
    E = []
    for cx, cy, cz, w, d, fl, db in lv:
        if fl and cy < -100:
            E.append([(X, Y + 0.0, Z) for X, Y, Z in _q_ell(B, cx, cy + B.bob * 0.0, cz, w, d, True, db)])
        else:
            E.append(_q_ell(B, cx, cy, cz, w, d, fl, db))
    # upper body ellipses carry the sit drop through B.p3; the knee level is placed directly at seat height
    parts = [_q_hull_path(E[i] + E[i + 1]) for i in range(len(E) - 1)]
    sk = parts[0]
    for p in parts[1:]: sk = union(sk, p) or sk
    c.fill(sk, QV['satin'])
    bb = sk.getBounds()
    # satin: soft diagonal sheen, a darker fall into the folds, the rim of her red light on the far side
    c.grad(sk, bb.left(), bb.top(), bb.right(), bb.bottom(), [(0, QV['satin'], 0), (0.28, QV['satin_sheen'], 230), (0.36, QV['satin_hi'], 150),
                                                             (0.45, QV['satin_sheen'], 120), (0.62, QV['satin'], 0), (1, QV['satin_sh'], 200)])
    c.grad(sk, bb.left(), 0, bb.right(), 0, [(0, QV['satin_hi'], 0), (0.2, QV['satin_hi'], 0), (0.29, '#5a547e', 150), (0.37, QV['satin_hi'], 0),
                                             (0.66, QV['satin_hi'], 0), (0.74, '#4a4468', 90), (0.8, QV['satin_hi'], 0), (1, QV['satin_hi'], 0)])
    c.fill(_crescent(sk, QL['side'] * 5.0, 0.0), QL['rim'], QL['rim_a'] * 0.55)
    c.fill(_crescent(sk, -QL['side'] * 4.0, 0.0), '#9aa4e8', 80)          # the cool moon rim on the other side
    with c.clip(sk):                                         # folds: from the waist to the hem, swaying with the hem
        if det >= 1:
            fl = []
            for k in range(9):
                a = -PI * 0.1 + PI * 1.2 * k / 8.0
                top = E[1][int((a % (2 * PI)) / (2 * PI) * len(E[1])) % len(E[1])]
                bot = E[-1][int((a % (2 * PI)) / (2 * PI) * len(E[-1])) % len(E[-1])]
                if bot[2] < -20: continue
                mx_ = lerp(top[0], bot[0], 0.55) + 4.0 * math.sin(k * 1.7 + t * 0.6)
                fl.append(smooth([(top[0], top[1]), (mx_, lerp(top[1], bot[1], 0.55)), (bot[0], bot[1] - 6.0)], False))
            c.line(_multi(fl), lw * 0.45, QV['satin_sh'], 200)
            c.line(_multi([moved_path(f_, 4.0, 0) for f_ in fl[::2]]), lw * 0.6, '#6a6490', 120)
    if u > 0.25 and det >= 1:                                # seated: two knees under the satin, a crease across the lap
        ka = clamp((u - 0.25) / 0.5)
        for s_ in (-1, 1):
            X, Y, Z = _q_proj_floor(B, s_ * 34.0, knee_y - 6.0, knee_z + 40.0)
            c.glow(X, Y, 30.0, 16.0, QV['satin_hi'], 150 * ka)
        X0, Y0, s0, _z = B.p3(-58.0, -548.0, 30.0); X1, Y1, s1, _z = B.p3(58.0, -548.0, 30.0)
        Xm, Ym, Zm = _q_proj_floor(B, 0.0, knee_y - 4.0, knee_z * 0.55)
        c.line(smooth([(X0, Y0 + 8), (Xm, Ym + 12.0 * ka), (X1, Y1 + 8)], False), lw * 0.55, QV['satin_sh'], 230 * ka)
        Xk, Yk, Zk = _q_proj_floor(B, 0.0, knee_y + 18.0, knee_z + 60.0)
        c.line(smooth([(Xk - 70, Yk - 4), (Xk, Yk + 6), (Xk + 70, Yk - 4)], False), lw * 0.5, QV['satin_sh'], 200 * ka)
    c.line(sk, lw, QV['line'])
    # the hem border along the visible front of the hem
    hem = E[-1]
    front = [p for p in hem if p[2] > -4.0]
    if len(front) > 3:
        front.sort(key=lambda p: p[0])
        line0 = [(p[0], p[1] - 5.0) for p in front]
        line1 = [(p[0], p[1] - 36.0) for p in front]
        band = smooth(line0 + line1[::-1], True, 0.5)
        c.fill(band, '#05040a', 200)
        c.line(smooth(line0, False), lw * 0.75, QV['hem_red'], 255)
        c.line(smooth(line1, False), lw * 0.75, QV['hem_red'], 255)
        xs = [p[0] for p in front]; ys = [p[1] for p in front]
        arc = 0.0; acc = [0.0]
        for i in range(1, len(front)): arc += math.hypot(xs[i] - xs[i - 1], ys[i] - ys[i - 1]); acc.append(arc)
        n = int(clamp(arc / 27.0, 5, 40))                    # pips every ~27 body units: a white dotted band even in wides
        pp = skia.Path()
        for k in range(n):
            d = arc * (k + 0.5) / n
            X = float(np.interp(d, acc, xs)); Y = float(np.interp(d, acc, ys)) - 20.5
            pp.addPath(_q_spade(X, Y, 18.0, 15.0))
        c.fill(pp, QV['pip'], 250)
    return E


def _q_foot_lifted(c, B, P, det, lw, QL):
    """Body mode: her right foot lifted out of the hem (lift_foot, step_up), the hem raised over the ankle."""
    up = max(0.0, P.fr_up)
    if up < 0.02: return
    L = up * 430.0
    d = 1.0 if B.st >= -0.05 else -1.0
    X, Y, Z = _q_proj_floor(B, -26.0, -L, 150.0 + 60.0 * up)
    fk = max(0.45, abs(B.st) * 1.2 + 0.25)
    fc = c.sub(X, Y, math.degrees(P.fr_point) * d * 0.6, 220.0)
    fc.M.preScale(fk, 1.0); fc = Ctx(c.pen, fc.M, fc.lw, None)
    shin = _tube([(0.0, -0.9), (0.0, -0.36)], [0.11, 0.1])
    fc.fill(shin, QV['foot']); fc.fill(_crescent(shin, 0.02 * d, 0), QV['foot_sh'], 150); fc.line(shin, fc.lw * 0.9, QV['line'])
    outline, toes, lines = _q_foot_paths(d, clamp(P.toes))
    fc.fill(outline, QV['foot']); fc.fill(_crescent(outline, -0.025 * d, -0.02), QV['foot_sh'], 130)
    fc.fill(_crescent(outline, 0.02 * d, 0.0), QL['rim'], QL['rim_a'] * 0.5)
    fc.line(outline, fc.lw * 0.9, QV['line'])
    _q_toe_draw(fc, toes, fc.lw, det)
    # the hem lifted over the shin: a satin drape with the red border
    kx, ky = X, Y - 0.74 * 220.0
    hx0, hy0 = kx - 86.0, ky + 46.0; hx1, hy1 = kx + 48.0 * d, ky + 14.0
    if d < 0: hx0, hx1 = kx + 86.0, kx - 48.0
    flap = smooth([(hx0, hy0 - 190.0), (kx, ky - 120.0), (hx1, hy1 - 40.0), (hx1, hy1), (kx, ky + 26.0), (hx0, hy0)], True, 0.7)
    c.fill(flap, QV['satin']); c.grad(flap, hx0, 0, hx1, 0, [(0, QV['satin_sh'], 220), (0.45, QV['satin_sheen'], 200), (1, QV['satin'], 0)])
    hem = smooth([(hx0 - 4.0, hy0), (kx + 10.0, ky + 42.0), (hx1 + 6.0, hy1)], False)
    c.line(hem, lw * 0.5, QV['hem_red'])
    c.line(flap, lw, QV['line'])


def _q_feet_peek(c, B, P, det, lw, E):
    """Bare ash-white toes under the front of the hem (standing or seated), long, with black nails."""
    if B.ct < -0.3: return
    u = clamp(P.sit)
    hw = lerp(146.0, 104.0, u); hz = lerp(0.0, 300.0, u)
    for s_ in (-1, 1):
        if s_ < 0 and P.fr_up > 0.02: continue
        x0 = s_ * 26.0
        zf = hz + math.sqrt(max(0.0, 1.0 - (x0 / hw) ** 2)) * hw * 0.92
        X, Y, Z = _q_proj_floor(B, x0, -2.0, zf)
        if Z < 0: continue
        Y += 7.0
        d = 1.0 if B.st >= 0 else -1.0
        fw = 15.0 * max(0.45, abs(B.ct)); fx = X + d * 6.0 * abs(B.st)
        f = smooth([(fx - fw, Y - 6.0), (fx - fw * 0.6, Y - 9.5), (fx + fw * 0.6, Y - 9.5), (fx + fw, Y - 5.0), (fx + fw * 0.9, Y + 3.5),
                    (fx, Y + 6.5), (fx - fw * 0.9, Y + 3.5)], True, 0.75)
        c.fill(f, QV['foot']); c.fill(_crescent(f, 0, -2.5), QV['foot_sh'], 170)
        c.line(f, lw * 0.6, QV['line'])
        if det >= 1:
            nl = skia.Path()
            for k in range(5):
                xx = fx + (k - 2) * fw * 0.36 * (1 if s_ > 0 else -1); yy = Y + 2.6 - abs(k - 2) * 0.9 + (0.0 if k != (0 if s_ < 0 else 4) else -0.4)
                r_ = 2.1 if k == (0 if s_ < 0 else 4) else 1.5
                nl.addOval(skia.Rect.MakeLTRB(xx - r_, yy - r_ * 0.75, xx + r_, yy + r_ * 0.75))
            c.fill(nl, QV['toenail_edge'], 230)


_LACE = []


def _lace_tile():
    """A 12 px lace-net tile (diagonal mesh with a dot at each crossing), drawn as a repeating shader in design px."""
    if not _LACE:
        n = 12
        arr = np.zeros((n, n, 4), np.uint8)
        sf = surface_for_tile = skia.Surface.MakeRasterDirect(skia.ImageInfo.Make(n, n, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
        cv = sf.getCanvas()
        p = skia.Paint(AntiAlias=True, Color=col('#4e4866', 255), Style=skia.Paint.kStroke_Style, StrokeWidth=0.9)
        for o in (-n, 0, n):
            cv.drawLine(o, 0, o + n, n, p); cv.drawLine(o + n, 0, o, n, p)
        cv.drawCircle(n / 2, n / 2, 1.1, skia.Paint(AntiAlias=True, Color=col('#5e5878', 255)))
        del cv, sf
        _LACE.append((skia.Image.fromarray(np.ascontiguousarray(arr), skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr))
    return _LACE[0][0]


def _q_collar(c, B, P, det, lw, which='all'):
    """Fan collar (Medici): a plane of black lace standing behind the neck, tilted back, 9 ribs radiating from the
    nape to a scalloped edge at ear height (2.1 head widths across), a fine white lace edge. Front views: a fan behind
    the head; back views: its back over the nape; turned: foreshortened."""
    sp = CAST['queen']
    yc = B.y_sh - 4.0
    r0 = 26.0
    r1 = (yc - (B.yc - sp['hh'] * 0.5)) * 1.22
    tilt = math.radians(18.0)
    zc = -16.0

    def fp(r, a):                                          # point on the fan plane: angle a from vertical, radius r
        x = r * math.sin(a); up = r * math.cos(a)
        return B.p3(x, yc - up * math.cos(tilt), zc - up * math.sin(tilt))
    angs = [(k - 4) / 4.0 * math.radians(56.0) for k in range(9)]
    ribs = [(fp(r0, a), fp(r1, a)) for a in angs]
    top = []
    for k in range(9):
        top.append((ribs[k][1][0], ribs[k][1][1]))
        if k < 8:                                          # a scallop between rib tips, bulging out along the radius
            am = (angs[k] + angs[k + 1]) / 2
            q = fp(r1 * 1.07, am); top.append((q[0], q[1]))
    bot = [(fp(r0, a)[0], fp(r0, a)[1]) for a in np.linspace(angs[-1], angs[0], 9)]
    fan = smooth(top + bot, True, 0.55)
    c.fill(fan, QV['lace'], 238)
    with c.clip(fan):
        bb = fan.getBounds()
        cx0, cy0 = ribs[4][0][0], ribs[4][0][1]
        c.radial(fan, cx0, cy0, r1 * 1.1, [(0, QV['lace'], 0), (0.7, '#1d1a2a', 120), (0.95, '#2a2640', 200), (1, '#2a2640', 200)])
        if det >= 1:                                       # the lace: concentric scallop rows and a fine net (cached tile)
            rows = []
            for rr in (0.55, 0.72, 0.87):
                q_ = [fp(r1 * rr, a) for a in np.linspace(angs[0], angs[-1], 33)]
                rows.append(smooth([(x, y) for x, y, *_ in q_], False))
            c.line(_multi(rows), max(0.7, lw * 0.22), '#4a4562', 150)
            c.cv.drawPath(c.P(fan), skia.Paint(AntiAlias=True, Shader=_lace_tile().makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, _LINS),
                                                Alphaf=0.55))
        c.line(_multi([poly([(b_[0], b_[1]), (t_[0], t_[1])], False) for b_, t_ in ribs]), lw * 0.5, QV['lace_rib'], 240)
    edge = smooth(top, False, 0.55)
    c.line(edge, lw * 1.2, QV['line'])
    c.line(edge, max(lw * 0.34, 1.5 / max(c.s, 0.05)), QV['lace_edge'], 250)
    if det >= 1:
        dots = skia.Path()
        for (x_, y_) in top[1::2]: dots.addCircle(x_, y_, max(lw * 0.3, 1.2 / max(c.s, 0.05)))
        c.fill(dots, QV['lace_edge'], 240)


def _q_arm_data(B, P, side):
    S = np.array([side * 70.0, B.y_sh + 14.0, 0.0])
    pre = 'hl_' if side > 0 else 'hr_'
    g = lambda k: getattr(P, pre + k)        # noqa: E731
    H = S + np.array([side * (g('out') - 18.0), g('down') * 1.02, g('fwd') + 14.0])
    pole = np.array([side * 0.75, 0.25, -0.65])
    kup = clamp((S[1] - H[1] - 10.0) / 60.0)
    if kup > 0: pole = pole + (np.array([side * 0.7, 1.0, 0.25]) - pole) * kup
    E, Wp = _ik(S, H, 182.0, 170.0, pole)
    return S, E, Wp


def _q_arm(c, B, P, side, det, t, lw, QL):
    S, E, Wr = _q_arm_data(B, P, side)
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    widths = [34.0 * pts[0][2], 27.0 * max(pts[1][2], hz ** 0.5), 21.0 * hz]
    tp = _tube([(P2[0][0] - side * 4, P2[0][1] - 12)] + P2, [widths[0] * 1.08] + widths)
    c.fill(tp, QV['satin'])
    c.grad(tp, P2[0][0] - 20, 0, P2[0][0] + 20, 0, [(0, QV['satin_sheen'], 150), (0.5, QV['satin'], 0), (1, QV['satin_sh'], 150)])
    c.glow((P2[1][0] + P2[2][0]) / 2, (P2[1][1] + P2[2][1]) / 2, 7.0, 46.0, '#5a547e', 150)
    c.glow((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2, 7.0, 40.0, '#5a547e', 120)
    c.fill(_crescent(tp, QL['side'] * 4.0, 0), QL['rim'], QL['rim_a'] * 0.5)
    c.fill(_crescent(tp, -QL['side'] * 3.5, 0), '#9aa4e8', 85)
    c.line(tp, lw, QV['line'])
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    pre = 'hl_' if side > 0 else 'hr_'
    shape = getattr(P, pre + 'shape'); up = getattr(P, pre + 'up'); rot = getattr(P, pre + 'rot'); press = getattr(P, pre + 'press')
    if shape in ('mitt', None): shape = 'relaxed'
    hang = ang * (1 - up) + 180.0 * up + rot
    hs = hz * 1.06
    look = _q_hand_look()
    _hand2(c, wx, wy, hs, hang, side, shape, det, look, press, t)
    # the sleeve ends in a point over the back of the hand
    a = math.radians(hang)
    fx_, fy_ = -math.sin(a), math.cos(a)
    nx, ny = fy_, -fx_
    w_ = widths[2] * 0.55
    pt = poly([(wx + nx * w_ - fx_ * 3, wy + ny * w_ - fy_ * 3), (wx + fx_ * 26 * hs, wy + fy_ * 26 * hs), (wx - nx * w_ - fx_ * 3, wy - ny * w_ - fy_ * 3)])
    c.fill(pt, QV['satin']); c.line(pt, lw * 0.8, QV['line'])
    B.hands[side] = c.pt(wx, wy)


def _q_hand_look():
    return dict(skin=QV['skin'], sh=QV['skin_sh'], dp=QV['inner'], line=QV['line'], lw_k=0.75, fk=1.35, fw=0.86, nail='almond',
                nail_c=QV['nail'], nail_hi=QV['nail_hi'], red_tips=(0, 1))


def _q_bodice(c, B, P, det, t, lw, QL, back):
    """Fitted black satin bodice: shoulders, bust, cinched waist; a high band at the neck with the spade brooch, a
    column of 9 tiny silver buttons."""
    lv = [(B.y_sh + 2.0, 82.0, 40.0), (B.y_sh + 40.0, 80.0, 44.0), (-724.0, 70.0, 46.0), (-660.0, 58.0, 40.0), (-600.0, 49.0, 34.0),
          (-560.0, 60.0, 42.0)]
    E = [_q_ell(B, 0.0, y, 0.0, w, d) for y, w, d in lv]
    parts = [_q_hull_path(E[i] + E[i + 1]) for i in range(len(E) - 1)]
    tor = parts[0]
    for p in parts[1:]: tor = union(tor, p) or tor
    c.fill(tor, QV['satin'])
    bb = tor.getBounds()
    c.grad(tor, bb.left(), bb.top(), bb.right(), bb.bottom(), [(0, QV['satin'], 0), (0.3, QV['satin_sheen'], 220), (0.38, QV['satin_hi'], 120),
                                                               (0.5, QV['satin'], 0), (1, QV['satin_sh'], 220)])
    c.fill(_crescent(tor, QL['side'] * 5.0, 0.0), QL['rim'], QL['rim_a'] * 0.55)
    c.fill(_crescent(tor, -QL['side'] * 4.0, 0.0), '#9aa4e8', 80)
    c.line(tor, lw, QV['line'])
    if not back:
        _q_girdle(c, B, P, det, lw, lv)
    if not back and det >= 1:
        # bodice seams (princess lines) and the buttons
        sm = []
        for s_ in (-1, 1):
            q = []
            for y in (B.y_sh + 50.0, -700.0, -640.0, -598.0):
                w = float(np.interp(y, [l_[0] for l_ in lv[::-1]], [l_[1] for l_ in lv[::-1]]))
                X, Y, s2, Z = B.p3(s_ * w * 0.48, y, 40.0 * math.sqrt(max(0.0, 1 - 0.23)))
                q.append((X, Y))
            sm.append(smooth(q, False))
        c.line(_multi(sm), lw * 0.35, QV['satin_sh'], 220)
        bt = skia.Path(); hi = skia.Path()
        for k in range(9):
            y = lerp(B.y_sh + 22.0, -604.0, k / 8.0)
            d = float(np.interp(y, [l_[0] for l_ in lv[::-1]], [l_[2] for l_ in lv[::-1]]))
            X, Y, s2, Z = B.p3(0.0, y, d + 1.0)
            if Z > -5:
                bt.addCircle(X, Y, 3.0); hi.addCircle(X - 0.9, Y - 0.9, 1.0)
        c.fill(bt, QV['silver']); c.line(bt, lw * 0.22, QV['line']); c.fill(hi, '#ffffff', 220)


def _q_front(B, x, y, lv, extra=0.0):
    """A point on the front surface of her bodice/skirt at body (x, y): projected (X, Y, Z)."""
    ys_ = [l_[0] for l_ in lv]; o = np.argsort(ys_)
    w = float(np.interp(y, [ys_[i] for i in o], [lv[i][1] for i in o])); d = float(np.interp(y, [ys_[i] for i in o], [lv[i][2] for i in o]))
    z = d * math.sqrt(max(0.0, 1.0 - min(1.0, (x / max(w, 1.0)) ** 2))) + extra
    X, Y, s_, Z = B.p3(x, y, z)
    return X, Y, Z


def _q_girdle(c, B, P, det, lw, lv):
    """The gown's shape in one silver line (it reads in wides): a pointed stomacher edged in silver from the bust to
    below the waist, a silver chain girdle round the waist with a spade clasp (red stone), and a pendant chain down the
    front of the skirt to a spade at the knee (standing)."""
    if B.ct < -0.1: return
    sil, hi = QV['silver'], QV['silver_hi']
    ys = np.linspace(B.y_sh + 46.0, -566.0, 9)
    edge = []
    for s_ in (-1, 1):
        q = []
        for y in ys:
            u = (y - ys[0]) / (ys[-1] - ys[0])
            x = s_ * 46.0 * (1.0 - u) ** 0.85
            X, Y, Z = _q_front(B, x, y, lv, 1.0)
            q.append((X, Y))
        edge.append(q)
    st_ = smooth(edge[0] + edge[1][::-1][1:], True, 0.6)
    c.grad(st_, edge[0][0][0], 0, edge[1][0][0], 0, [(0, QV['satin_sheen'], 0), (0.35, '#3a3552', 160), (0.5, QV['satin_sheen'], 60), (1, QV['satin'], 0)])
    c.line(smooth(edge[0], False), lw * 0.42, sil, 235); c.line(smooth(edge[1], False), lw * 0.42, sil, 235)
    # the chain girdle (front half of the waist) and the clasp
    wl = [lv_ for lv_ in lv if abs(lv_[0] + 600.0) < 1.0]
    w0, d0 = (wl[0][1], wl[0][2]) if wl else (49.0, 34.0)
    ring = []
    for a in np.linspace(0.08, PI - 0.08, 17):
        x = -math.cos(a) * w0 * 1.03; z = math.sin(a) * d0 * 1.03 + 1.0
        X, Y, s_, Z = B.p3(x, -598.0 + 5.0 * math.sin(a), z)
        if Z > -6: ring.append((X, Y))
    if len(ring) > 2:
        rp = smooth(ring, False)
        c.line(rp, lw * 0.95, QV['line'], 255); c.line(rp, lw * 0.6, sil, 255)
        if det >= 1:
            dots = skia.Path()
            for X, Y in ring[1:-1:2]: dots.addCircle(X, Y, lw * 0.22)
            c.fill(dots, hi, 230)
    X, Y, Z = _q_front(B, 0.0, -594.0, lv, 3.0)
    if Z > -4:
        br = _q_spade(X, Y + 2.0, 26.0, 22.0)
        c.fill(br, sil); c.line(br, lw * 0.35, QV['line'])
        c.fill(_q_spade(X, Y + 2.6, 15.0, 12.6), QV['stone']); c.fill(oval(X - 2.6, Y - 2.4, 1.6, 1.6), '#ffffff', 230)
        c.glow(X, Y, 12.0, 12.0, QV['lip_glow'], 70)
    if clamp(P.sit) < 0.3:                                   # the pendant chain down the front of the skirt
        skv = [(-598.0, 49.0, 34.0), (-540.0, 70.0, 48.0), (-300.0, 118.0, 108.0), (-2.0, 146.0, 134.0)]
        sway = 4.0 * P.sec_x + 3.0 * getattr(P, 'hem', 0.0)
        ch = []
        for y in np.linspace(-580.0, -350.0, 12):
            u = (y + 580.0) / 230.0
            X, Y, Z = _q_front(B, sway * u, y, skv, 2.0)
            ch.append((X, Y))
        cp = smooth(ch, False)
        c.line(cp, lw * 0.75, QV['line'], 230); c.line(cp, lw * 0.42, sil, 240)
        X, Y = ch[-1]
        pd = _q_spade(X, Y + 14.0, 30.0, 25.0)
        c.fill(pd, sil); c.line(pd, lw * 0.35, QV['line'])
        c.fill(_q_spade(X - 1.5, Y + 11.0, 9.0, 7.0), hi, 220)


def _q_neck(c, B, P, det, lw, QL, back):
    sp = CAST['queen']
    nb = B.p3(0, B.y_sh - 4.0, 0); nt = B.p3(0, B.yc - 16.0 + P.h_dy, 0)
    nw = 14.5
    neck = _tube([(nb[0], nb[1]), (nt[0] + P.h_dx * 0.5, nt[1])], [nw * 2 * nb[2], nw * 1.9 * nt[2]])
    c.fill(neck, QV['skin'])
    c.grad(neck, nb[0] - nw, 0, nb[0] + nw, 0, [(0, QV['skin_sh'], 230), (0.3, QV['skin'], 0), (0.7, QV['skin'], 0), (1, QV['skin_sh'], 230)])
    c.grad(neck, 0, nt[1], 0, nb[1], [(0, '#a89cb4', 255), (0.35, QV['skin_sh'], 150), (0.7, QV['skin'], 0)])
    c.fill(_crescent(neck, QL['side'] * 2.5, 0), QL['rim'], QL['rim_a'] * 0.6)
    c.line(neck, lw * 0.9, QV['line'])
    # the high band and the spade brooch at the throat
    band = _q_hull_path(_q_ell(B, 0.0, B.y_sh - 8.0, 0.0, 21.0, 18.0) + _q_ell(B, 0.0, B.y_sh + 8.0, 0.0, 25.0, 21.0))
    c.fill(band, QV['satin']); c.grad(band, nb[0] - 25, 0, nb[0] + 25, 0, [(0, QV['satin_sheen'], 180), (0.5, QV['satin'], 0), (1, QV['satin_sh'], 160)])
    c.line(band, lw * 0.8, QV['line'])
    if not back:
        X, Y, s2, Z = B.p3(0.0, B.y_sh + 1.0, 22.0)
        if Z > -4:
            br = _q_spade(X, Y, 15.0, 12.0)
            c.fill(br, QV['silver']); c.line(br, lw * 0.3, QV['line'])
            c.fill(_q_spade(X, Y + 0.6, 9.0, 7.2), QV['stone'])
            c.glow(X, Y, 9.0, 9.0, QV['lip_glow'], 120)
            c.fill(oval(X - 1.6, Y - 2.0, 1.2, 1.2), '#ffffff', 230)


def _q_fall(c, B, P, det, t, lw, part, hair_yaw):
    """The waist-length fall below the jaw in body coords. part 'back' = the sheet behind the shoulders (front views)
    or down the back (back views); part 'front' = the two curtains that continue the face-framing hair straight down
    in front of the shoulders. hair_yaw lags the head by 0.4 s: the head can snap round while the hair stays put."""
    sp = CAST['queen']
    cy = math.cos(hair_yaw); sy = math.sin(hair_yaw)
    pv = B.p3(0, B.yc - 22.0 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2]
    hx = pv[0] + P.h_dx; hy = pv[1] - (sp['hh'] / 2 - 22.0) * pv[2]
    yb = B.p3(0, -606.0, 0)[1]
    sway = 3.0 * P.sec_x + 1.5 * getattr(P, 'hem', 0.0)
    hc = QV['hair']
    if part == 'back':
        acy = abs(cy)
        w0 = (96.0 * acy + 70.0 * abs(sy)) * hs; w1 = (112.0 * acy + 80.0 * abs(sy)) * hs
        ox = -sy * 30.0 * hs * (1 if cy >= 0 else -1)
        top = hy - (60.0 if cy < 0 else 20.0) * hs
        tip = [(hx + ox + w1 * f + sway, yb + 10.0 * (1.0 - abs(f)) + 14.0 * math.sin(f * 7.0) ** 2) for f in np.linspace(0.95, -0.95, 9)]
        pts = [(hx + ox - w0 * 0.75, top - 30.0 * hs), (hx + ox, top - 52.0 * hs), (hx + ox + w0 * 0.75, top - 30.0 * hs), (hx + ox + w0, top + 60.0 * hs),
               (hx + ox + w1 + sway * 0.5, (top + yb) / 2)] + tip + [(hx + ox - w1 + sway * 0.5, (top + yb) / 2), (hx + ox - w0, top + 60.0 * hs)]
        sheet = smooth(pts, True, 0.7)
        c.fill(sheet, hc)
        with c.clip(sheet):
            c.grad(sheet, hx + ox - w1, 0, hx + ox + w1, 0, [(0, QV['hair_dark'], 220), (0.28, QV['hair_sheen'], 150), (0.42, hc, 0), (0.8, hc, 0),
                                                             (1, QV['hair_dark'], 220)])
            c.grad(sheet, 0, top, 0, yb, [(0, QV['hair_sheen'], 0), (0.28, QV['hair_sheen'], 130), (0.36, QV['hair_hi'], 70), (0.44, QV['hair_sheen'], 0)])
            if det >= 1:
                dk, hi = [], []
                for k in range(-5, 6):
                    f = k / 5.5
                    x0 = hx + ox + f * w0 * 0.9
                    q = smooth([(x0, top - 20.0 * hs), (x0 + f * (w1 - w0) * 0.5 + sway * 0.3, (top + yb) / 2), (hx + ox + f * w1 * 0.95 + sway, yb + 4.0)], False)
                    (dk if k % 2 else hi).append(q)
                c.line(_multi(dk), lw * 0.3, QV['hair_dark'], 230)
                c.line(_multi(hi[::2]), lw * 0.2, QV['hair_hi'], 130)
        c.line(sheet, lw * 0.8, QV['line'])
        return
    if cy < 0.05: return
    top_y = hy + 118.0 * hs
    for s_ in (-1, 1):
        far = s_ * sy
        if far > 0.45: continue
        k_ = clamp(1.0 - max(0.0, far) * 1.6)
        xi = hx + (s_ * 60.0 * cy + 24.0 * sy) * hs
        xo = hx + (s_ * 104.0 * cy + 24.0 * sy) * hs
        wid = abs(xo - xi)
        sh_y = B.p3(0, B.y_sh, 0)[1]
        mid = (sh_y + yb) * 0.5
        tipx = lerp(xi, xo, 0.45)
        pts = [(xi, top_y - 26.0 * hs), (xo, top_y - 26.0 * hs), (xo + s_ * wid * 0.08, sh_y - 4.0), (xo + s_ * wid * 0.02 + sway * 0.5, mid),
               (xo - s_ * wid * 0.1 + sway, yb - 26.0), (tipx + s_ * wid * 0.22 + sway, yb + 4.0), (tipx + sway, yb + 16.0),
               (tipx - s_ * wid * 0.2 + sway, yb + 2.0), (xi + s_ * wid * 0.1 + sway, yb - 30.0), (xi + s_ * wid * 0.04 + sway * 0.5, mid),
               (xi + s_ * wid * 0.02, sh_y - 8.0)]
        cur = smooth(pts, True, 0.7)
        c.fill(cur, hc, 255 * k_ + 0.0)
        with c.clip(cur):
            c.grad(cur, xi, 0, xo, 0, [(0, QV['hair_dark'], 190), (0.4, QV['hair_sheen'], 120), (0.55, hc, 0), (1, QV['hair_dark'], 210)])
            c.grad(cur, 0, top_y, 0, yb, [(0, QV['hair_sheen'], 0), (0.25, QV['hair_sheen'], 120), (0.33, QV['hair_hi'], 70), (0.42, QV['hair_sheen'], 0)])
            if det >= 1:
                st_ = [smooth([(lerp(xi, xo, f), top_y - 20.0 * hs), (lerp(xi, xo, f) + s_ * wid * 0.05 + sway * 0.5, mid),
                               (lerp(xi, xo, lerp(f, 0.45, 0.6)) + sway, yb + 6.0)], False) for f in (0.15, 0.35, 0.55, 0.75, 0.9)]
                c.line(_multi(st_[::2]), lw * 0.3, QV['hair_dark'], 230)
                c.line(_multi(st_[1::2]), lw * 0.2, QV['hair_hi'], 140)
        c.line(cur, lw * 0.8, QV['line'])


def _q_figure(c, P, det, t, light=None, upper_only=False):
    """The whole queen in body units on Ctx c (feet y=0, crown y=-1000)."""
    sp = CAST['queen']
    B = Body(sp, P)
    u = clamp(P.sit)
    if u > 0: B.bob += 100.0 * u                             # her hips drop 270 to the seat (Body gives 170)
    QL = _ql(light)
    lw = c.lw * 0.75
    back_view = B.ct < -0.15
    head_yaw = (P.turn + P.h_turn) * PI / 2
    hy_ = getattr(P, 'q_hair', None)
    hair_yaw = (hy_ * PI / 2) if (hy_ is not None and getattr(P, 'q_hair_set', 0.0) > 0.5) else head_yaw
    body_yaw = P.turn * PI / 2                              # the fall hangs from the shoulders: within 60 deg of the body
    dyaw = (hair_yaw - body_yaw + PI) % (2 * PI) - PI
    hair_yaw = body_yaw + clamp(dyaw, -PI / 3, PI / 3)
    hair_back = math.cos(hair_yaw) < 0.0
    # arms behind the body
    arm_z = {}
    for s_ in (-1, 1):
        S, E, Wr = _q_arm_data(B, P, s_)
        arm_z[s_] = (B.p3(*S)[3], B.p3(*Wr)[3])
    behind = [s_ for s_ in (-1, 1) if arm_z[s_][0] < -20 and arm_z[s_][1] < 40]
    front = sorted([s_ for s_ in (-1, 1) if s_ not in behind], key=lambda s_: arm_z[s_][1])
    if not hair_back: _q_fall(c, B, P, det, t, lw, 'back', hair_yaw)
    if not back_view: _q_collar(c, B, P, det, lw)
    for s_ in behind: _q_arm(c, B, P, s_, det, t, lw, QL)
    E = None
    if not upper_only:
        E = _q_skirt(c, B, P, det, t, lw, QL)
        _q_feet_peek(c, B, P, det, lw, E)
        _q_foot_lifted(c, B, P, det, lw, QL)
    _q_bodice(c, B, P, det, t, lw, QL, back_view)
    _q_neck(c, B, P, det, lw, QL, back_view)
    if back_view: _q_collar(c, B, P, det, lw)
    if hair_back: _q_fall(c, B, P, det, t, lw, 'back', hair_yaw)
    # head
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2] * P.h_scale
    head_rot = P.tilt + P.h_tilt
    arm_ = (sp['hh'] / 2 - 22) * pv[2] * P.h_scale
    ra = math.radians(head_rot)
    hx = pv[0] + P.h_dx + math.sin(ra) * arm_
    hy = pv[1] - math.cos(ra) * arm_
    hc = c.sub(hx, hy, head_rot, hs)
    hc.lw = c.lw / hs
    P._body = True; P._roll = head_rot
    if not hair_back: _q_fall(c, B, P, det, t, lw, 'front', hair_yaw)
    _q_head(hc, P, head_yaw, P.h_nod * 0.6, det, t, light)
    for s_ in front: _q_arm(c, B, P, s_, det, t, lw, QL)
    B.info = dict(head=c.pt(hx, hy), head_px=hs * 240.0 * c.s, roll=head_rot, hands=B.hands)
    return B


def _q_glow_layer(pen, cx, cy, r, a=60):
    """Her bloom: a soft cool halo behind the face (1.5x anyone else's)."""
    pen.ellipse_glow(cx, cy, r, r * 1.15, QV['key'], a)


def queen_draw(pen, x, y_feet, height, P, detail=None, light=None, t=None):
    t = P.t if t is None else t
    s = height / 1000.0
    sp = CAST['queen']
    head_px = sp['hh'] * s
    det = _auto_detail(pen, head_px) if detail is None else detail
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px * 1.25), None).sub(x + P.dx, y_feet + P.dy, 0.0, s)
    with _q_tint(pen, light, (x + P.dx - 0.6 * height, y_feet + P.dy - 1.1 * height, x + P.dx + 0.6 * height, y_feet + P.dy + 0.06 * height)):
        return _q_figure(c, P, det, t, light)


def queen_bust(pen, cx, cy, scale, P, detail=None, light=None, t=None):
    t = P.t if t is None else t
    sp = CAST['queen']
    k = 1.0 + 1.1 * clamp(P.approach)
    head_px = 600.0 * scale * k
    s = head_px / sp['hh']
    yh = -1000 + sp['hh'] / 2
    ty = cy + 60.0 * scale * clamp(P.approach)
    det = _auto_detail(pen, head_px) if detail is None else detail
    cx = cx + P.dx; ty = ty + P.dy
    nf = clamp(getattr(P, 'q_nface', 0.0))
    if nf > 0.001:                                         # the phone: Noah13's face, pixel-sorting into hers
        return _q_nface_bust(pen, cx, ty, scale, P, det, light, t, nf)
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px), None).sub(cx, ty - yh * s, 0.0, s)
    with _q_tint(pen, light, (cx - head_px * 2.2, ty - head_px * 1.0, cx + head_px * 2.2, ty + head_px * 3.4)):
        return _q_figure(c, P, det, t, light, upper_only=True)


def _q_nface_bust(pen, cx, ty, scale, P, det, light, t, nf):
    """Noah13's face (talking, his voice) occupying her bust; while nf falls 1 -> 0 horizontal bands switch to her S3c
    face, the switching bands smeared sideways (pixel sort)."""
    sp = CAST['queen']; s = 600.0 * scale / sp['hh']; yh = -1000 + sp['hh'] / 2
    fr = int(math.floor(t * 60.0 + 1e-6))
    nb = 18; H_ = 600.0 * scale * 2.6; top = ty - 600.0 * scale * 1.1
    P2 = Pose('calm_kid'); P2.t = t
    for k in ('m_open', 'm_round', 'm_wide', 'teeth'): setattr(P2, k, getattr(P, k))
    P2.teeth = max(P2.teeth, 0.6); P2.lock = 1.0; P2.wide = 0.15
    cv = pen.cv
    info = None
    for b in range(nb):
        y0 = top + H_ * b / nb; y1 = y0 + H_ / nb + 0.5
        her = hash01(b * 13 + 7, 921) > nf
        off = (hash01(b + fr // 2, 923) - 0.5) * 120.0 * scale * math.sin(PI * nf) if abs(nf - 0.5) < 0.49 else 0.0
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(-1e5, y0, 1e5, y1)); cv.translate(off, 0)
        try:
            if her:
                c = Ctx(pen, skia.Matrix(), _lw_for(600.0 * scale), None).sub(cx, ty - yh * s, 0.0, s)
                B = _q_figure(c, P, det, t, light, upper_only=True); info = info or B
            else:
                draw_bust(pen, 'noah13', cx, ty + 30.0 * scale, scale * 1.15, P2, detail=det, light=dict(rim='#ff4060', rim_a=90, side=1, key=-0.1), t=t)
        finally:
            cv.restore()
    if info is None:
        info = Body(sp, P); info.info = dict(head=(cx, ty), head_px=600.0 * scale, roll=0.0, hands={})
    return info


@contextmanager
def _q_tint(pen, light, bounds):
    """The climax red reaches her dress and hair, never her face's whites: a light red multiply on a layer."""
    L = _light_dict(light) or {}
    if L.get('under') == '#3a1018' or L.get('tint') == '#ff6a78':
        cv = pen.cv
        cv.saveLayer(skia.Rect.MakeLTRB(*bounds), skia.Paint(ColorFilter=skia.ColorFilters.Matrix(
            [1.0, 0, 0, 0, 0.0, 0, 0.97, 0, 0, 0, 0, 0, 0.975, 0, 0, 0, 0, 0, 1, 0])))
        try: yield
        finally: cv.restore()
    else:
        yield


def queen_head(pen, cx, cy, size, P, detail=2, light=None, t=None):
    s = size / 240.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size), None).sub(cx, cy, P.h_tilt, s)
    yaw = (P.turn + P.h_turn) * PI / 2
    return _q_head(c, P, yaw, P.h_nod * 0.6, detail, P.t if t is None else t, light)


def queen_hands(pen, x, y, size, P, detail=2, light=None, t=None, main='r'):
    """Hands insert for the queen: long porcelain hands (fingers 1.35x), black almond nails, the right index and middle
    fingertips smudged lipstick red, the black satin sleeve ending in a point over the back of the hand."""
    t = P.t if t is None else t
    k = size / 66.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.2) * 0.75, None)
    look = _q_hand_look()
    out = dict(tip={}, wrist={}, prop={})
    QL = _ql(light)
    order = [('l', 1), ('r', -1)] if main == 'r' else [('l', -1), ('r', 1)]
    for nm, side in order:
        pre = 'i' + nm + '_'
        v = clamp(getattr(P, pre + 'v'))
        if v <= 0.01: continue
        ang = getattr(P, pre + 'a'); a = math.radians(ang)
        fx_, fy_ = -math.sin(a), math.cos(a)
        px = x + getattr(P, pre + 'x') * size; py = y + getattr(P, pre + 'y') * size
        slide = (1.0 - ease_out_cubic(v)) * 2.6 * size
        wx = px - fx_ * 26 * k - fx_ * slide; wy = py - fy_ * 26 * k - fy_ * slide
        ax, ay = -fx_, -fy_
        aw = 0.34 * size
        end = (wx + ax * size * 3.6, wy + ay * size * 3.6)
        cx0, cy0 = wx + ax * size * 0.1, wy + ay * size * 0.1
        slv = _tube([(cx0, cy0), end], [aw * 1.18, aw * 1.45])
        c.fill(slv, QV['satin'])
        c.grad(slv, cx0 - ay * aw, cy0 + ax * aw, cx0 + ay * aw, cy0 - ax * aw, [(0, QV['satin_sh'], 200), (0.35, QV['satin_sheen'], 200), (0.5, QV['satin_hi'], 120),
                                                                               (0.7, QV['satin'], 0)])
        c.fill(_crescent(slv, QL['side'] * aw * 0.08, 0), QL['rim'], QL['rim_a'] * 0.5)
        c.line(slv, c.lw, QV['line'])
        shape = getattr(P, pre + 'shape'); press = getattr(P, pre + 'press')
        if shape in ('mitt', None): shape = 'relaxed'
        nx, ny = fy_, -fx_
        w_ = aw * 0.62
        pt = poly([(wx + nx * w_ + ax * size * 0.12, wy + ny * w_ + ay * size * 0.12), (wx + fx_ * 24 * k, wy + fy_ * 24 * k),
                   (wx - nx * w_ + ax * size * 0.12, wy - ny * w_ + ay * size * 0.12)])
        palm = shape in ('flat', 'palm')
        if palm: c.fill(pt, QV['satin']); c.line(pt, c.lw * 0.8, QV['line'])
        _hand2(c, wx, wy, k, ang, side, shape, detail, look, press, t)
        if not palm: c.fill(pt, QV['satin']); c.line(pt, c.lw * 0.8, QV['line'])
        tip = _hpt(wx, wy, ang, k, (-side) * 3.9 * 0.0 - side * 0.0, 30.4 + 32.9 * 1.35 + 5.0)
        out['tip'][nm] = tip; out['wrist'][nm] = (wx, wy)
    return out


def _q_foot_paths(d, toes_k):
    """Her bare foot, low 3/4 view on a step, sole y=0, ankle at (0, -0.36), toes to +x*d: narrow, a high arch, long toes
    (1.2x). Returns (outline, toes=[(toe path, nail path)] little toe first, lines). The toes are separate elongated
    digits aligned with the foot (a slight downward curl with toes_k), each with a small pale nail plate on top."""
    pts = [(0.05, -0.46), (0.06, -0.34), (0.13, -0.24), (0.22, -0.16), (0.3, -0.115), (0.36, -0.092), (0.405, -0.072), (0.425, -0.045),
           (0.42, -0.012), (0.36, 0.004), (0.28, 0.003), (0.21, -0.016), (0.12, -0.03), (0.02, -0.01), (-0.07, 0.008), (-0.11, -0.016),
           (-0.12, -0.07), (-0.095, -0.18), (-0.065, -0.32), (-0.06, -0.46)]
    outline = smooth([(px * d, py) for px, py in pts], True, 0.55)
    toes = []
    spec = ((0.0, 0.084, 0.03), (1.0, 0.07, 0.023), (2.0, 0.062, 0.021), (3.0, 0.054, 0.019), (4.0, 0.045, 0.017))
    for i, L, r in spec[::-1]:
        bx = 0.405 - 0.03 * i; by = -0.03 - 0.013 * i
        a = 0.12 + 0.55 * toes_k + 0.04 * i
        L *= 1.2 * (1.0 - 0.18 * toes_k)
        ca, sa = math.cos(a), math.sin(a)
        tx_, ty_ = bx + L * ca, by + L * sa
        nx, ny = -sa, ca                                     # toward the sole
        q = smooth([(bx - nx * r, by - ny * r), (tx_ - nx * r * 0.9 - ca * r * 0.1, ty_ - ny * r * 0.9 - sa * r * 0.1),
                    (tx_ + ca * r * 0.55, ty_ + sa * r * 0.55), (tx_ + nx * r * 0.85, ty_ + ny * r * 0.85), (bx + nx * r, by + ny * r)], True, 0.7)
        u0, u1 = 0.5, 0.97
        nl = smooth([(bx + ca * L * u0 - nx * r * 0.85, by + sa * L * u0 - ny * r * 0.85),
                     (bx + ca * L * u1 - nx * r * 0.7, by + sa * L * u1 - ny * r * 0.7),
                     (bx + ca * L * u1 - nx * r * 0.05, by + sa * L * u1 - ny * r * 0.05),
                     (bx + ca * L * u0 - nx * r * 0.25, by + sa * L * u0 - ny * r * 0.25)], True, 0.6)
        m = skia.Matrix(); m.setScale(d, 1.0); q.transform(m); nl.transform(m)
        toes.append((q, nl))
    lines = [smooth([(0.04 * d, -0.3), (0.16 * d, -0.19), (0.3 * d, -0.1)], False),          # tendons on the top of the foot
             smooth([(0.02 * d, -0.26), (0.13 * d, -0.15), (0.25 * d, -0.075)], False),
             smooth([(-0.05 * d, -0.42), (-0.075 * d, -0.26), (-0.1 * d, -0.13)], False),    # Achilles
             smooth([(0.03 * d, -0.016), (0.12 * d, -0.045), (0.21 * d, -0.03)], False)]      # the arch, off the step
    return outline, toes, lines


def _q_toe_draw(fc, toes, lw, det=2):
    """Toes (little toe first, the big toe on top), each outlined thin, a shade under it, a pale cold nail with an edge."""
    for q, nl in toes:
        fc.fill(q, QV['foot']); fc.fill(_crescent(q, 0, -0.01), QV['foot_sh'], 170)
        fc.line(q, lw * 0.42, QV['line'])
        fc.fill(nl, QV['toenail'], 250)
        if det >= 1:
            fc.line(nl, lw * 0.18, QV['toenail_edge'], 200)
            b = nl.getBounds(); fc.fill(oval(b.centerX(), b.top() + b.height() * 0.32, b.width() * 0.16, b.height() * 0.12), QV['toenail_hi'], 200)


def queen_feet(pen, x, y, size, P, detail=2, light=None, t=None):
    """Feet insert for the queen: bare, narrow, anatomical (arch, tendons, long toes, black toenails), ash-white with
    lavender shade at the toes and heel; the satin hem with the spade-pip border brushes the ankles."""
    t = P.t if t is None else t
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 1.6) * 0.75, None)
    QL = _ql(light)
    out = {}
    hem_on = getattr(P, 'ft_hem', 1.0) >= 0.5
    for side, vis, xo, d in ((1, getattr(P, 'ft_l', 1.0), -0.36, -1), (-1, getattr(P, 'ft_r', 1.0), 0.0, 1)):
        if vis <= 0.01: continue
        pre = 'fl_' if side > 0 else 'fr_'
        lift = getattr(P, pre + 'up') * size; fwd = getattr(P, pre + 'fwd') * size
        fx = x + xo * size + getattr(P, pre + 'out') * size + d * fwd * 0.4
        fy = y - lift + fwd * 0.15
        fc = c.sub(fx, fy, math.degrees(getattr(P, pre + 'point')) * d, size)
        lw = fc.lw
        shin = _tube([(0.0, -1.3), (0.0, -0.36)], [0.12, 0.1])
        if not hem_on: shin = _tube([(0.0, -0.75), (0.0, -0.36)], [0.115, 0.1])
        fc.fill(shin, QV['foot']); fc.fill(_crescent(shin, 0.025 * d, 0), QV['foot_sh'], 150)
        fc.fill(_crescent(shin, -0.02 * d, 0), QL['rim'], QL['rim_a'] * 0.5)
        if not hem_on: fc.grad(shin, 0, -0.75, 0, -0.45, [(0, '#05040a', 255), (1, QV['foot'], 0)])
        fc.line(shin, lw * 0.9, QV['line'])
        outline, toes, lines = _q_foot_paths(d, clamp(P.toes))
        fc.fill(outline, QV['foot'])
        fc.grad(outline, 0.45 * d, 0, -0.1 * d, 0, [(0, QV['foot_sh'], 200), (0.35, QV['foot'], 0), (0.8, QV['foot'], 0), (1, QV['foot_sh'], 170)])
        fc.fill(_crescent(outline, -0.025 * d, -0.02), QV['foot_sh'], 120)
        fc.fill(_crescent(outline, 0.02 * d, 0.0), QL['rim'], QL['rim_a'] * 0.45)
        if detail >= 1:
            fc.line(_multi(lines[:2]), lw * 0.3, QV['skin_dp'], 150)
            fc.line(lines[2], lw * 0.3, QV['skin_dp'], 130)
            fc.line(lines[3], lw * 0.3, QV['skin_dp'], 110)
            fc.line(smooth([(-0.022, -0.33), (0.0, -0.356), (0.026, -0.33)], False), lw * 0.3, QV['skin_dp'], 150)
        fc.line(outline, lw * 0.9, QV['line'])
        _q_toe_draw(fc, toes, lw, detail)
        out['r' if side < 0 else 'l'] = (fx, fy)
    if hem_on and out:                                     # one satin hem over both ankles, the playing-card border
        xs_ = [v[0] for v in out.values()]
        hx0 = (min(xs_) + max(xs_)) / 2.0 - 0.06 * size; hy0 = y
        fc = c.sub(hx0, hy0, 0.0, size)
        lw = fc.lw
        sw = 0.04 * getattr(P, 'hem', 0.0) + 0.02 * P.sec_x
        xs = np.linspace(-0.82, 0.82, 23)
        hem_y = -0.5
        hp = [(float(xx) + sw, hem_y + 0.022 * math.sin(xx * 9.0 + 1.3) + 0.035 * (abs(xx) > 0.55)) for xx in xs]
        hem = smooth([(-0.82, -2.4), (0.82, -2.4)] + hp[::-1], True, 0.5)
        fc.fill(hem, QV['satin'])
        fc.grad(hem, -0.8, 0, 0.8, 0, [(0, QV['satin_sh'], 220), (0.32, QV['satin_sheen'], 220), (0.42, QV['satin_hi'], 140), (0.58, QV['satin'], 0),
                                      (1, QV['satin_sh'], 220)])
        fc.fill(_crescent(hem, -0.02, 0), QL['rim'], QL['rim_a'] * 0.5)
        fc.line(_multi([smooth([(q_ * 0.14, -2.0), (q_ * 0.15 + sw, hem_y + 0.01)], False) for q_ in (-5, -3, -2, 1, 3, 5)]), lw * 0.4, QV['satin_sh'], 200)
        b0 = [(px_, py_ - 0.025) for px_, py_ in hp]; b1 = [(px_, py_ - 0.13) for px_, py_ in hp]
        fc.line(smooth(b0, False), lw * 0.5, QV['hem_red']); fc.line(smooth(b1, False), lw * 0.5, QV['hem_red'])
        pp = skia.Path()
        for k in range(1, len(hp) - 1, 2):
            pp.addPath(_q_spade(hp[k][0], hp[k][1] - 0.078, 0.06, 0.052))
        fc.fill(pp, QV['pip'])
        fc.line(smooth(hp, False), lw, QV['line'])
    return out


# ====================================================================================================== Mirror Steps: shot specs -> rigs
PLAN_SHOTS = os.environ.get('MS_SHOTS', os.path.join(_HERE, 'plan', 'shots.json'))
_PLAN = {}
WHO_ALIAS = {'kids': 'kid_a', 'extras': 'searcher', 'mom': 'mum'}
CLIP_ORIGIN = {'loop_reset': 199.3}           # clip_id -> origin shot (by a film time inside it; ids change when shots merge)
_SIG = {                                       # how each plan act maps onto a clip: (method, positional arg names)
    'expr': ('expr', ('name',)), 'hold_up': ('hold_up', ('prop',)), 'talk': ('talk_line', ()), 'look': ('look_at', ()),
    'walk': ('walk', ()), 'run': ('run', ()), 'tremble': ('tremble', ()), 'freeze': ('freeze', ()), 'sit': ('sit', ()),
    'point': ('point', ()), 'turn': ('turn', ()), 'snap_turn': ('snap_turn', ()), 'blink': ('blink', ()), 'flinch': ('flinch', ()),
    'hand_to_mouth': ('hand_to_mouth', ()), 'nervous_glance': ('nervous_glance', ()), 'phone_to_ear': ('phone_to_ear', ()),
}


def plan_shots():
    """plan/shots.json shots by id (cached)."""
    if 'by_id' not in _PLAN:
        try:
            import json as _json
            sh = _json.load(open(PLAN_SHOTS))['shots']
        except Exception:
            sh = []
        _PLAN['by_id'] = {s['id']: s for s in sh}; _PLAN['list'] = sh
    return _PLAN['by_id']


def _spec_clip_id(c):
    """A char spec's clip_id: the spec field, or (v2 plans) the clip_id argument of one of its acts."""
    if c.get('clip_id'): return c['clip_id']
    for a in c.get('acts') or []:
        if len(a) > 2 and isinstance(a[2], dict) and a[2].get('clip_id'): return a[2]['clip_id']
    return None


def _clip_origin(clip_id, who):
    """(shot, spec) whose acting a clip_id replays: CLIP_ORIGIN[clip_id] (when that shot has the character) or the
    first shot carrying the id."""
    by = plan_shots()
    sid = CLIP_ORIGIN.get(clip_id)
    if isinstance(sid, (int, float)):
        sid = next((s['id'] for s in _PLAN.get('list', []) if s['t0'] <= sid < s['t1']), None)
    cands = []
    if sid in by and any(c.get('who') == who for c in by[sid].get('chars') or []): cands = [by[sid]]
    if not cands: cands = [s for s in _PLAN.get('list', []) if any(_spec_clip_id(c) == clip_id for c in s.get('chars') or [])]
    for s in cands:
        for c in s.get('chars') or []:
            if c.get('who') == who and (s is not cands[0] or _spec_clip_id(c) in (None, clip_id)): return s, c
    return None, None


def default_light(shot, who=None, t=None):
    """Light preset for a character in a shot when the plan gives none: by the shot's side and the red climax."""
    if not shot: return 'moon'
    side = shot.get('side', 'ours'); t0 = shot.get('t0', 0.0)
    if who == 'queen' and side in ('mirror', 'ours'): return dict(rim='#ff4060', rim_a=110, side=-1, key=-0.25)
    if t0 >= 534.4 and side in ('ours', 'mirror'): return 'red'
    if side == 'theirs': return 'dawn'
    if side == 'memory': return None
    props = shot.get('props') or {}
    if str(props.get('flashlight', '')).startswith('tess_on') and who != 'tess': return 'flashlight'
    return 'moon'


class CharRig:
    """One character in one plan shot: builds the Acting from the shot spec (chars[i] of plan/shots.json) and draws it
    in its mode. rig = CharRig(spec, shot); rig.draw(pen, t, at=None, light=None) -> info dict; rig.events -> SFX
    events; rig.pose(t) -> Pose. `at` overrides spec['at'] (resolve anchor names in sets.py first). Times are film
    seconds. clip_id specs replay the origin shot's acting frame for frame (t - t0 + t0_origin)."""

    def __init__(self, spec, shot=None, seed=None):
        self.spec = spec; self.shot = shot or {}
        self.who_plan = spec['who']
        self.who = WHO_ALIAS.get(spec['who'], spec['who'])
        self.mode = spec.get('mode', 'body')
        self.t_shift = 0.0
        src_shot, src_spec = self.shot, spec
        cid = _spec_clip_id(spec)
        if cid:
            o_shot, o_spec = _clip_origin(cid, spec['who'])
            if o_shot is not None and o_shot.get('id') != self.shot.get('id'):
                self.t_shift = o_shot['t0'] - self.shot.get('t0', 0.0)
                src_shot, src_spec = o_shot, o_spec
        sid = src_shot.get('id', 'S000')
        self.seed = int(seed) if seed is not None else (sum(ord(ch) for ch in sid + self.who) * 7) % 997
        self.acting, self.events = build_acting(src_spec, src_shot, self.seed, who=self.who)
        if self.t_shift:
            for e in self.events: e['t'] = round(e['t'] - self.t_shift, 4)

    def pose(self, t):
        P = self.acting.at(t + self.t_shift)
        P.t = t + self.t_shift
        return P

    def draw(self, pen, t, at=None, light='auto', detail=None, main=None):
        at = at if at is not None else self.spec.get('at')
        if isinstance(at, str): raise ValueError('resolve anchor %r first (sets.py anchors)' % at)
        if light == 'auto': light = self.spec.get('light') or default_light(self.shot, self.who, t)
        P = self.pose(t)
        if self.mode == 'lying':
            P._facing = int(self.spec.get('_facing', 1)); P._hang = bool(self.spec.get('hang_arm', self.spec.get('watch', True)))
        view = 'pov' if (self.mode == 'feet' and (self.spec.get('pov') or self.spec.get('view') == 'pov')) else self.spec.get('view')
        if self.mode in ('body', 'legs', 'silhouette') and len(at) > 2 and float(at[2]) < 10.0:
            k_ = (self.shot.get('id'), self.who, 'at')
            if k_ not in _ACT_WARN:
                _ACT_WARN.add(k_); sys.stderr.write('characters: %s %s mode %s has at[2]=%s (a height in design px is expected)\n'
                                                   % (k_[0], self.who, self.mode, at[2]))
        return draw_mode(pen, self.who, self.mode, at, P, light=light, detail=detail, view=view, main=main or self._main(t))

    def _main(self, t):
        if self.who == 'you' and self.mode == 'hands' and 323.6 <= t <= 651.0:
            names = [a[1] for a in self.spec.get('acts') or []]
            if any(n in ('fist', 'open_fist') for n in names) or ('take' in names and 'candy' in json_dumps(self.spec)): return 'l'
        return 'r'


def json_dumps(x):
    import json as _json
    return _json.dumps(x)


def draw_mode(pen, who, mode, at, P, light=None, detail=None, view=None, main='r'):
    """Draw a character in a plan mode (body | bust | hands | feet | legs | silhouette | lying) at the plan's `at`.
    pose.alpha < 1 fades the whole character (fade_out)."""
    a_ = clamp(getattr(P, 'alpha', 1.0))
    if a_ < 0.999:
        if a_ <= 0.004: return {}
        pen.cv.saveLayer(None, skia.Paint(Alphaf=float(a_)))
        P.alpha = 1.0
        try: return draw_mode(pen, who, mode, at, P, light, detail, view, main)
        finally: P.alpha = a_; pen.cv.restore()
    at = list(at)
    if mode == 'body':
        B = draw(pen, who, at[0], at[1], at[2], P, detail, light, P.t)
        return dict(B.info, B=B)
    if mode == 'bust':
        B = draw_bust(pen, who, at[0], at[1], at[2], P, detail, light, P.t)
        return dict(B.info, B=B)
    if mode == 'hands':
        return draw_hands(pen, who, at[0], at[1], at[2] * P.ins_k, P, 2 if detail is None else detail, light, P.t, main=main)
    if mode == 'feet':
        if view == 'pov': return draw_feet_pov(pen, who, at[0], at[1], at[2], P, 2 if detail is None else detail, light, P.t)
        return draw_feet(pen, who, at[0], at[1], at[2], P, 2 if detail is None else detail, light, P.t)
    if mode == 'legs':
        B = draw_legs(pen, who, at[0], at[1], at[2], P, detail, light, P.t)
        return dict(B.info, B=B)
    if mode == 'silhouette':
        draw_silhouette(pen, who, at[0], at[1], at[2], P, light, P.t)
        return {}
    if mode == 'lying':
        B = draw_lying(pen, who, at[0], at[1], at[2], P, detail, light, P.t, facing=int(getattr(P, '_facing', 1) or 1),
                       hang_arm=(who == 'noah13' and getattr(P, '_hang', True)))
        return dict(B.info, B=B)
    raise ValueError(mode)


_ACT_WARN = set()


def build_acting(spec, shot=None, seed=0, who=None):
    """Acting for a plan char spec: base expression, view, stage / face (queen), prop-state defaults (flashlight,
    tape, jacket, candy fist) and every act in spec['acts'] ([t, name, args]). Returns (acting, events)."""
    shot = shot or {}
    who = who or WHO_ALIAS.get(spec['who'], spec['who'])
    t0s, t1s = shot.get('t0', 0.0), shot.get('t1', shot.get('t0', 0.0) + 3.0)
    sp = CAST[who]
    h = 700.0
    at = spec.get('at')
    if isinstance(at, (list, tuple)) and len(at) >= 3: h = float(at[2]) if spec.get('mode') in ('body', 'legs', 'silhouette') else 700.0
    ex = spec.get('expr') or 'neutral'
    if ex not in EXPR: ex = 'neutral'
    a = Acting(who, seed=seed, height=h, expr=ex)
    if isinstance(at, (list, tuple)) and len(at) >= 3: a._at = (float(at[0]), float(at[1]), float(at[2]))
    view = spec.get('view') or 'front'
    vt = VIEWS.get(view, 0.0)
    if vt: a.set(-INF, None, 0.01, turn=vt)
    props = shot.get('props') or {}
    evs = []
    # ---- defaults from the cast and the prop states
    if who == 'queen':
        q = spec.get('queen') if isinstance(spec.get('queen'), dict) else {}
        st = q.get('stage', spec.get('stage', 'S1')); face = spec.get('face')
        d = queen_stage(st)
        if face in ('hidden',) or spec.get('face_hidden'): d['q_hide'] = 1.0
        if spec.get('seated'): d['sit'] = 1.0
        if spec.get('mode') == 'feet' and any(x_[1] == 'toes_curl' for x_ in spec.get('acts') or []) and str(st) not in ('S3c', 'S4', '3'):
            d['ft_hem'] = 0.0; d['ft_l'] = 0.0
        a.set(-INF, None, 0.01, **d)
        a.life(-INF, None, 0.0)
    if who == 'tess':
        fl = str(props.get('flashlight', 'tess_on'))
        if fl.startswith('tess_on') or fl.startswith('tess_running') or fl == 'off':
            on = 0.0 if fl == 'off' else 1.0
            a.set(-INF, None, 0.01, hr_prop='flashlight', hr_shape='grip', hr_out=20.0, hr_down=150.0, hr_fwd=250.0, hr_rot=90.0, beam=on)
    if who in ('noah13',):
        tape = str(props.get('tape', 'on'))
        a.set(-INF, None, 0.01, tape=0.0 if tape.startswith('slipped') else 1.0, tape_peel=0.4 if tape == 'picking' else 0.0)
    if who == 'noah_grown':
        a.set(635.06, None, 0.05, jacket_on=1.0)
    if who == 'you':
        if 323.65 <= t1s and t0s <= 651.0:
            a.set(323.65, 651.0, 0.2, hl_shape='fist', candy=1.0)
        if str(props.get('jacket', 'you')).startswith('noah') or t0s >= 635.06: a.set(-INF, None, 0.01, jacket_off=1.0)
    # ---- the acts
    for act in spec.get('acts') or []:
        t = float(act[0]); name = act[1]; args = dict(act[2]) if len(act) > 2 and act[2] else {}
        try:
            r = _apply_act(a, who, spec, shot, t, name, args, t1s)
        except Exception as e:                                # a bad act never kills the rig (the plan is edited in parallel)
            r = None
            k_ = (shot.get('id'), who, name)
            if k_ not in _ACT_WARN:
                _ACT_WARN.add(k_); sys.stderr.write('characters: act %s %s %s skipped: %r\n' % (k_ + (e,)))
        if isinstance(r, list): evs.extend(r)
    return a, evs


def _apply_act(a, who, spec, shot, t, name, args, t_end):
    at = spec.get('at') if isinstance(spec.get('at'), (list, tuple)) else None
    if name == 'expr':
        nm = args.get('name', 'neutral'); return a.expr(nm if nm in EXPR else 'neutral', t, None, args.get('fade', 0.35))
    if name == 'talk':
        return a.talk_line(t, args.get('line'))
    if name == 'look':
        hx, hy = (at[0], at[1] - (at[2] * 0.85 if spec.get('mode') == 'body' else 0)) if at else (960.0, 400.0)
        return a.look_at(t, args.get('x', 960), args.get('y', 400), (hx, hy), lost=args.get('lost', False))
    if name == 'walk' or name == 'run':
        x0 = 0.0
        to = args.get('to')
        dx = (float(to) - at[0]) if (isinstance(to, (int, float)) and at) else 0.6 * a.height
        t1 = min(t_end, t + max(0.6, abs(dx) / (a.height * (1.1 if name == 'run' else 0.45))))
        surf = {'gravel': 'footsteps_gravel', 'wood': 'footsteps_wood_inside', 'inside': 'footsteps_wood_inside'}.get(args.get('surface'), 'footsteps_porch')
        if name == 'run':
            return a.run(t, x0 + dx, t1, x0)
        if args.get('sneak'): a.sneak(t, t1)
        ev = a.walk(t, t1, x0, x0 + dx, surface='inside' if surf == 'footsteps_wood_inside' else 'porch')
        for e in ev: e['name'] = surf; e['gain_db'] = -8.0 if args.get('sneak') else e['gain_db']
        return ev
    if name == 'hold_up':
        return a.hold_up(args.get('prop', 'phone'), t, t + args.get('dur', 1.2), args.get('side', -1))
    if name == 'freeze':
        return a.freeze(t, args.get('t1', t + 1.0))
    if name == 'sit':
        return a.sit(t, None, args.get('dur', 0.6))
    if name == 'point':
        return a.point(t, t + args.get('dur', 1.2), args.get('side', -1))
    if name == 'turn':
        to = args.get('to', 0.0)
        if isinstance(to, str):                                 # a view name, or a named target (the door is behind her)
            to = VIEWS.get(to, {'door': 2.0, 'away': 2.0, 'lens': 0.0, 'camera': 0.0, 'you': 0.0, 'left': -1.0, 'right': 1.0}.get(to, 0.5))
        return a.turn(t, float(to), args.get('dur', 0.6))
    if name == 'snap_turn':
        frm = args.get('frm', 1.0); to = args.get('to', 0.0)
        frm = VIEWS.get(frm, frm) if isinstance(frm, str) else frm; to = VIEWS.get(to, to) if isinstance(to, str) else to
        return a.snap_turn(t, frm, to)
    if name == 'tremble':
        return a.tremble(t, args.get('amount', 0.6), args.get('t1'))
    if name == 'head_down':
        return a.head_down(t, None, args.get('amount', 1.0))
    if name == 'head_tilt':
        return a.head_tilt(t, args.get('angle', 24.0), args.get('dur', 1.2))
    if name == 'lean_in':
        return a.lean_in(t, args.get('dur', 2.0), None, args.get('amount', 1.0))
    if name == 'stare':
        return a.stare(t)
    if name in ('hand_on_glass',):
        return a.hand_on_glass(t, t + args.get('dur', 1.5), args.get('side', 1))
    if name in ('nervous_glance',):
        return a.nervous_glance(t, args.get('n', 2))
    if name in ('phone_to_ear',):
        return a.phone_to_ear(t, None, args.get('side', 1))
    if name in ('blink', 'flinch'):
        return getattr(a, name)(t)
    if name == 'hide':                    # merged shots: a hand / foot entry that is not in this part of the move fades out
        return a.set(t, args.get('t1'), args.get('fade', 0.15), alpha=0.0)
    if name == 'hand_to_mouth':
        return a.hand_to_mouth(t, t + args.get('dur', 1.2))
    if name == 'wipe_glass' and who == 'you' and ('towel' in str(shot.get('frame', '')) or str((shot.get('props') or {}).get('towel')) in ('held', 'in_hands')):
        args = dict(args, prop='towel')
    fn = getattr(a, name, None)
    if fn is None or not callable(fn):
        return None
    import inspect
    try:
        prm = inspect.signature(fn).parameters
        kw = {k: v for k, v in args.items() if k in prm}
        if 't1' in prm and 't1' not in kw and name in ('tie_loop', 'climb', 'grip_frame', 'hem_sway', 'toes_curl', 'still', 'rock', 'breathe_sleep'):
            kw['t1'] = t_end + 0.5
        if name == 'raise': kw = {}
        if 'raise_' in args and 'raise_' in prm: kw['raise_'] = args['raise_']
        return fn(t, **kw)
    except TypeError:
        return fn(t)


# ====================================================================================================== HUD phone hand
POV_SLEEVE = ('#4a5038', '#33382a')              # your olive canvas sleeve and its stitched cuff band (every POV hand)


def hud_phone_hand(pen, w, h, skin='#c9aa98', a=255, front=False, sleeve=None):
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
        sleeve = sleeve or POV_SLEEVE[0]
        cuff = rrect(-w * 0.5, h * 0.92, w * 1.02, h * 0.5, 36)
        c.fill(cuff, sleeve, a); c.fill(_crescent(cuff, -w * 0.08, 0), mix(sleeve, '#000000', 0.35), 160 * k)
        if sleeve == POV_SLEEVE[0]: c.fill(rrect(-w * 0.5, h * 0.92, w * 1.02, h * 0.12, 18), POV_SLEEVE[1], a)
        c.line(cuff, lw, LINE, a)
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
    a = Acting('you_police', seed=1)
    ts = np.arange(0, 40, 1 / 240.0); b = np.array([a._blink_amt(t) for t in ts]) > 0.5
    runs, r = [], 0
    for v in b:
        if v: r += 1
        elif r: runs.append(r); r = 0
    assert runs and max(runs) / 240.0 <= 0.067, ('blink', max(runs) / 240.0)
    out.append('blinks: %d, longest shut %.0f ms' % (len(runs), 1000 * max(runs) / 240.0))
    # phone at the ear: wrist ends up near the ear, not past the shoulder (no spike)
    for who in ('mum', 'you_police', 'officer', 'you', 'tess'):
        a = Acting(who, seed=2); a.phone_to_ear(0.0, None, side=1)
        P = a.at(1.0); B = Body(CAST[who], P)
        S, E, W = _arm_data(CAST[who], B, P, 1)
        ear_y = B.yc - CAST[who]['hh'] / 2
        assert W[1] < B.y_sh and abs(W[1] - ear_y) < 0.6 * CAST[who]['hh'], ('phone_to_ear', who, W, ear_y)
        out.append('phone_to_ear %s: wrist %.0f above the shoulder, %.0f below the ear' % (who, B.y_sh - W[1], W[1] - ear_y))
    # lip sync follows the voice envelope (when the narration is available)
    env = voice_envelope()
    rs = []
    for li, who in ((125, 'noah13'), (97, 'queen'), (196, 'queen'), (110, 'queen')):   # this film's narration (timeline.json)
        L = timeline_line(li)
        if env is None or not L: continue
        a = Acting(who, seed=1); a.talk_line(L['t'], li)
        ts = np.arange(L['t'] - 0.1, L['end'] + 0.1, 1 / 30.0)
        mo = np.array([a.at(t).m_open for t in ts]); ev = np.array([10 ** (_env_db(env, t) / 20.0) for t in ts])
        rs.append(float(np.corrcoef(mo, ev)[0, 1]))
    if rs:
        assert min(rs) > 0.45, ('lip sync', rs)
        out.append('lip sync r = %s (lines 125, 97, 196, 110)' % ', '.join('%.2f' % r for r in rs))
    # Mirror Steps cast
    a = Acting('queen', seed=2); a.still(0.0)
    br = [a.at(t).breath for t in np.arange(0.0, 6.0, 0.05)]; bl = [a.at(t).blink for t in np.arange(0.0, 6.0, 0.05)]
    assert max(br) - min(br) < 1e-6 and max(bl) == 0.0, ('queen still', max(br) - min(br), max(bl))
    out.append('queen: no breathing, no blinks over 6 s')
    # Queen v2: the stage ladder is cumulative; the head snap is done in 0.18 s while the hair lags 0.4 s
    order = ['S1', 'S2', 'S3a', 'S3b', 'S3c']
    for a_, b_ in zip(order[:-1], order[1:]):
        A, B_ = queen_stage(a_), queen_stage(b_)
        assert all(B_[k] >= A[k] for k in A if k != 'q_hide'), ('stage ladder', a_, b_)
    assert queen_stage(3) == queen_stage('S3c') and queen_stage('S4')['q_void'] == 1.0
    a = Acting('queen', seed=2); a.head_snap(10.0, 130, 0.18)
    P1 = a.at(10.2); P2 = a.at(10.3)
    assert abs(P1.h_turn - 130 / 90.0) < 0.15 and abs(P1.q_hair) < 0.05 and abs(P2.q_hair) < 0.05, ('head snap', P1.h_turn, P1.q_hair)
    assert abs(a.at(10.75).q_hair - 130 / 90.0) < 0.15, ('hair settles', a.at(10.75).q_hair)
    out.append('queen v2: stage ladder S1 < S2 < S3a < S3b < S3c, head snap 130 deg in 0.18 s, the hair 0.4 s behind')
    sp0 = _resolve_sp('noah_grown', Pose(age_body=0.0, age_face=0.0))
    assert max(abs(x - y) for x, y in zip(sp0['head_ws'], CAST['noah13']['head_ws'])) < 1e-6 and sp0['cloth']['fit'] == 0.0
    out.append('age morph: age 0 = noah13 head and fit')
    by = plan_shots()
    if by:
        n = 0; nev = 0
        for sh in _PLAN['list']:
            for cs in sh.get('chars') or []:
                r_ = CharRig(cs, sh); r_.pose(sh['t0'] + 0.05); n += 1; nev += len(r_.events)
        out.append('plan: %d character rigs built, %d acting SFX events' % (n, nev))
        pairs = {}
        for sh in _PLAN['list']:
            for cs in sh.get('chars') or []:
                if _spec_clip_id(cs) and cs['who'] == 'noah13': pairs.setdefault(_spec_clip_id(cs), []).append((sh, cs))
        for cid, lst in pairs.items():
            if len(lst) < 2 or cid in CLIP_ORIGIN: continue
            (sa, ca), (sb, cb) = lst[0], lst[1]
            ra, rb = CharRig(ca, sa), CharRig(cb, sb)
            dmax = max(abs(getattr(ra.pose(sa['t0'] + k * 0.13), f) - getattr(rb.pose(sb['t0'] + k * 0.13), f))
                       for k in range(18) for f in ('m_open', 'h_tilt', 'lace', 'ir_x', 'breath', 'blink', 'h_turn', 'look_x'))
            assert dmax < 1e-9, ('clip_id replay', cid, dmax)
            out.append('clip_id %s: %s replays %s frame for frame (max diff %.1e)' % (cid, sb['id'], sa['id'], dmax))
    for o in out: print(o)
    print('characters self-test ok')


if __name__ == '__main__' and '--selftest' in sys.argv:
    _selftest()
