"""Bunnyman-film sets (and the dummy / delivery / police regressions): stills of every set / variant, a contact sheet,
the floor plan with every camera, the framing check at each view's widest camera move and the draw-time bench.

    python3 tools/sets_sheet.py                       # bunny-film stills (1280x720) + contact_sheet.jpg + index.json
                                                      #   (anchors with plan / screen data per variant) + floorplan.jpg -> W/sets/
    python3 tools/sets_sheet.py --dummy               # the dummy film's variants (regression)
    python3 tools/sets_sheet.py --stage               # staging test stills: cast figures placed only from the sets' Spots
                                                      #   (ST.stage_figure) -> W/sets/stage_*.jpg + stage_sheet.jpg
    python3 tools/sets_sheet.py --only hall,ins_      # variants whose name contains any of these
    python3 tools/sets_sheet.py --frame               # + framing check: every view at the corners of its info['cam_env'] (and
                                                      #   +-8 px handheld) over a magenta background -> frame_check.json / .jpg
    python3 tools/sets_sheet.py --bench               # + time every variant at 2560x1440 (one process, 1 OpenCV thread)
    python3 tools/sets_sheet.py --delivery            # the delivery film's variants (regression)
    python3 tools/sets_sheet.py --police              # police-set regression stills
W = film/_work. Stills are graded through the engine exactly like the film (lens, grade, set fx incl. the VHS tape look).
Sets that need people are shown empty (anchors in SETS.md / index.json); rule cards are drawn over a blurred living room.
"""
import argparse, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
sys.path.insert(0, FILM)
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.join(FILM, '_work', 'sets'))
ap.add_argument('--size', default='1280x720')
ap.add_argument('--only', default=None)
ap.add_argument('--bench', action='store_true')
ap.add_argument('--bench_frames', type=int, default=6)
ap.add_argument('--police', action='store_true')
ap.add_argument('--delivery', action='store_true')
ap.add_argument('--dummy', action='store_true')
ap.add_argument('--stage', action='store_true')
ap.add_argument('--frame', action='store_true')
ap.add_argument('--no_sheet', action='store_true')
a = ap.parse_args()
cv2.setNumThreads(1)

from engine import *                                                     # noqa: E402,F401,F403
from engine import hud as H                                              # noqa: E402
from engine.core import set_render_size                                  # noqa: E402

W0, H0 = (int(v) for v in a.size.split('x'))
set_render_size(W0, H0)
import sets as ST                                                        # noqa: E402
try:
    import characters as CH
    H._hand = CH.hud_phone_hand
except Exception:
    CH = None


def app(screen, t=1.2, bg='hall', **kw):
    def build():
        sp = ST.phone_bg(bg)
        return sp, dict(hud=lambda cv, tt: ST.app_phone(cv, screen, t, 960, 560, 1.25, skin='#c9aa98', **kw), post=dict(dim=0.25))
    return build


def S(fn, **opt):
    def build():
        return fn(), opt
    return build


hz_off = dict(t_off=0.6)
VARIANTS = [
    # name, builder, t, camera (None = home), note
    ('porch_doorbell_van', S(lambda: ST.delivery_porch()), 0.12, None, 'doorbell, 3:07: van at the curb, hazards on'),
    ('porch_doorbell_box_door', S(lambda: ST.delivery_porch(box='door')), 0.12, None, 'the box against the front door (left edge)'),
    ('porch_doorbell_box_boots', S(lambda: ST.delivery_porch(box='boots')), 0.7, None, 'the box next to his boots (hazards off phase)'),
    ('porch_doorbell_ir', S(lambda: ST.delivery_porch(box='door', ir=True)), 0.12, None, 'IR night mode (eyes flash white)'),
    ('porch_doorbell_seat_empty', S(lambda: ST.delivery_porch(box='door', van=dict(driver=False))), 0.12, None, '3:40: driver\'s seat empty'),
    ('porch_doorbell_van_door', S(lambda: ST.delivery_porch(box='door', van=dict(driver=False, door=1.0))), 0.12, None, 'sliding door open'),
    ('porch_doorbell_van_leaving', S(lambda: ST.delivery_porch(box='door', van=dict(drive=('out', 0.0, 4.0, 4.0, 24.0)), hazard=hz_off)), 2.2, None,
     'hazards off, pulling away, headlights off'),
    ('porch_peephole_van', S(lambda: ST.delivery_porch('peephole')), 0.12, None, 'peephole'),
    ('street_van', S(lambda: ST.delivery_street()), 0.12, None, 'house 144 across the street, van at the curb'),
    ('street_van_door_open', S(lambda: ST.delivery_street(van=dict(driver=False, door=1.0))), 0.12, None, 'van door open, seat empty'),
    ('street_memory', S(lambda: ST.memory_porch('street')), 0.12, None, '21 years ago: the wagon, the same van'),
    ('doorway_night', S(lambda: ST.porch_doorway(tod='night')), 0.12, None, 'front door open at 3 AM: the box backlit'),
    ('doorway_memory', S(lambda: ST.memory_porch('doorway')), 0.12, None, '21 years ago: the open door, box, van'),
    ('hall_door_open_far', S(lambda: ST.delivery_hall(door_open=0.85, outside=dict(tod='night', box='door'))), 0.12, 'doorway',
     'the hall view with the front door open'),
    ('sunrise_doorbell', S(lambda: ST.sunrise_porch()), 0.12, None, '6:12: tape cut, box open, no van'),
    ('sunrise_doorway', S(lambda: ST.sunrise_porch('doorway')), 0.12, None, '6:12: mum opens the door'),
    ('sunrise_door_opening', S(lambda: ST.porch_doorway(tod='dawn', door_open=lambda t: min(1.0, t / 2.0) * 0.92)), 0.8, None, 'door swinging in (animated)'),
    ('side_yard', S(lambda: ST.side_yard()), 0.12, None, 'under Lily\'s open window, van light from the street'),
    ('side_yard_closed', S(lambda: ST.side_yard(window_open=False, hazard=False)), 0.12, None, 'window closed, no van light'),
    ('hall_stairs', S(lambda: ST.delivery_hall()), 0.1, None, 'front hall to the door: stairs, side table, key bowl'),
    ('hall_stairs_lamp_dad', S(lambda: ST.delivery_hall(lamp=1.0, bowl='dad')), 0.1, None, 'lamp on, dad\'s keys in the bowl'),
    ('hall_back', S(lambda: ST.hall_back()), 0.1, None, 'from the door into the house (behind you)'),
    ('hall_back_dad_upstairs', S(lambda: ST.hall_back(bowl='dad', upstairs=0.8, hazard=True)), 0.1, None, 'dad\'s keys; mum\'s light upstairs'),
    ('upstairs_crack', S(lambda: ST.upstairs_hall()), 0.1, None, 'Lily\'s door open a crack'),
    ('upstairs_open', S(lambda: ST.upstairs_hall(lily_door=0.9, hazard=True)), 0.1, None, 'her door pushed open: the window'),
    ('lily_room_sleeping', S(lambda: ST.lily_room()), 0.1, None, 'Lily asleep, moon nightlight'),
    ('lily_room_empty', S(lambda: ST.lily_room(window_open=True, bed='empty', hazard=True)), 0.1, None, 'window wide open, bed empty'),
    ('lily_window', S(lambda: ST.lily_room(view='window', hazard=True)), 0.1, None, 'out of her window: side yard, van'),
    ('lily_window_leaving', S(lambda: ST.lily_room(view='window', hazard=dict(t_off=0.5), drive=('out', 0.5, 5.0, -9.0, -32.0))), 3.4, None,
     'hazards stop, the van pulls away'),
]
for n in ('label', 'label_to', 'label_lily', 'tablet_sign', 'tablet_lily', 'key_bowl', 'key_bowl_dad', 'box_keys', 'van_seat', 'hazard_switch'):
    VARIANTS.append(('ins_' + n, S((lambda n_: lambda: ST.insert(n_, police=False))(n)), 0.1, None, 'insert ' + n))
VARIANTS.append(('ins_key_bowl_drop', S(lambda: ST.insert('key_bowl_dad', police=False, prop_kw=dict(drop=0.55))), 0.1, None, 'keys dropping in'))
for scr in ST.APP_SCREENS:
    VARIANTS.append(('app_' + scr, app(scr), 1.2, None, 'app screen ' + scr))
DELIVERY = VARIANTS


def card(n, text_, reveal=None, mode='tear', tc=2.4):
    def build():
        sp = ST.gp_living('tv', tv=dict(on=-5.0), lamp=0.25)
        return sp, dict(hud=lambda cv, tt: ST.rule_card_lie(cv, n, text_, tc, reveal=reveal, mode=mode), post=dict(blur=6.0, dim=0.3))
    return build


def G(fn, grade=None, **opt):
    def build():
        sp = fn()
        if grade: sp.grade = grade
        return sp, opt
    return build


R6 = "If he's ever on someone's lap, *don't pull him off*."
_hd = dict(light=0.0, kitchen=0.0, living=0.0)
DUMMY = [
    ('hall_kitchen', G(lambda: ST.gp_hall()), 0.5, None, 'front hall, lights on: the case on the bench, the kitchen opening lit'),
    ('hall_kitchen_case_open', G(lambda: ST.gp_hall(case='open')), 0.5, None, 'the case open: red velvet, the hollow'),
    ('hall_kitchen_push', G(lambda: ST.gp_hall()), 0.5, 'kopen', 'pushed down the hall into the opening (chair, mug, window)'),
    ('hall_dark_kitchen_on', G(lambda: ST.gp_hall(light=0.0, living=0.0), 'gp_dark'), 0.5, None, 'hall dark, the kitchen light on'),
    ('hall_dark_beam', G(lambda: ST.gp_hall(case='open', beam=dict(keys=[(0, -0.4, 5.6), (6, -0.3, 2.5)], on=0.0), **_hd), 'gp_dark'), 3.0, None,
     'all dark: the knee-high flashlight coming down the hall'),
    ('hall_door', G(lambda: ST.gp_hall(view='door')), 0.5, None, 'toward the front door: stairs left, bench + case right'),
    ('hall_door_morning', G(lambda: ST.gp_hall(view='door', tod='morning', door=0.85, light=0.0)), 0.5, None, '8 AM: the door open'),
    ('stairs', G(lambda: ST.gp_hall(view='stairs')), 0.5, None, 'up the stairs to the moonlit landing (anchor step3)'),
    ('stairs_beam', G(lambda: ST.gp_hall(view='stairs', beam=dict(keys=[(0, 0.92, 1.55)], Y=0.82, aim=(0, 0.45, -1)))), 0.5, None,
     '3 AM: the flashlight on step 3 aimed at your face'),
    ('kitchen_table', G(lambda: ST.gp_kitchen()), 0.5, None, 'kitchen from the opening: chair, mug steaming, pendant'),
    ('kitchen_chair', G(lambda: ST.gp_kitchen('chair')), 0.5, None, 'seated, across the table: the chair, the mug'),
    ('kitchen_flicker', G(lambda: ST.gp_kitchen('chair', kitchen=dict(flick=[(0.0, 9.0)]), sway=0.04)), 0.47, None, 'the pendant flickering'),
    ('kitchen_morning', G(lambda: ST.gp_kitchen(tod='morning')), 0.5, None, 'the kitchen at morning'),
    ('living_tv', G(lambda: ST.gp_living('tv')), 0.5, None, 'from the couch: TV off, the kitchen doorway (his chair)'),
    ('living_tv_on', G(lambda: ST.gp_living('tv', tv=dict(on=0.0, snow=0.4), lamp=0.25), 'tv_glow'), 2.0, None, 'the TV on by itself: the 1974 tape'),
    ('living_tv_snow', G(lambda: ST.gp_living('tv', tv=dict(on=0.0, snow=0.6), lamp=0.25), 'tv_glow'), 0.3, None, 'static before the tape'),
    ('living_couch', G(lambda: ST.gp_living('couch')), 0.5, None, 'the couch under the lamp, the window, the bookcase (bookcase_top)'),
    ('living_couch_lamp_out', G(lambda: ST.gp_living('couch', lamp=0.0), 'gp_dark'), 0.5, None, 'the lamp out'),
    ('den', G(lambda: ST.gp_den()), 0.5, None, 'the den: armchair, lamp, posters, rug'),
    ('den_lamp_out', G(lambda: ST.gp_den(lamp=0.0), 'gp_dark'), 0.5, None, 'the den lamp out'),
    ('bedroom_doorway', G(lambda: ST.bedroom_doorway()), 0.5, None, 'your bedroom at home: the doorway backlit'),
    ('hospital', G(lambda: ST.hospital()), 1.3, None, 'hospital room at night: bed, chair, monitor'),
    ('hospital_close_flat', G(lambda: ST.hospital('close', flat=0.4)), 1.3, None, 'close: the monitor flatlines'),
    ('studio_full', G(lambda: ST.gp_studio(laugh=ST.laugh_waves([0.4]))), 1.0, None, '1974 tape full frame (VHS + CRT)'),
    ('studio_bezel', G(lambda: ST.gp_studio(laugh=ST.laugh_waves([0.4]), bezel=1.0, track=0.8)), 1.0, None, 'with the TV bezel, bad tracking'),
    ('studio_clean', G(lambda: ST.gp_studio(laugh=ST.laugh_waves([0.4]), vhs=False)), 1.0, None, 'the stage without the tape look'),
    ('stage_1962', G(lambda: ST.stage_1962()), 0.5, None, '1962: the first show (sepia)'),
    ('museum_case', G(lambda: ST.museum()), 0.5, None, 'the museum vitrine, the plaque'),
    ('museum_wide', G(lambda: ST.museum('wide')), 0.5, None, 'the gallery'),
    ('street_window', G(lambda: ST.street_morning(van=dict(drive=('out', 0.0, 5.0, -5.5, -14.0)))), 2.0, None, '8 AM: the van pulls away (Owen at the glass)'),
    ('street_outside', G(lambda: ST.street_morning('outside')), 0.5, None, 'the house from across the street, the van'),
]
for n in sorted(ST.GP_INSERTS):
    kw = {}
    if n == 'back_slot': kw = dict(prop_kw=dict(hand=0.6))
    if n == 'squeeze': kw = dict(prop_kw=dict(squeeze=0.85))
    if n == 'latches': kw = dict(prop_kw=dict(latch=(1.0, 0.25)))
    if n == 'mug': kw = dict(prop_kw=dict(stir=lambda t: t * 1.5))
    DUMMY.append(('ins_' + n, G((lambda n_, kw_: lambda: ST.insert(n_, **kw_))(n, kw)), 0.4, None, 'insert ' + n))
DUMMY += [('ins_letter_hl6', G(lambda: ST.insert('letter', prop_kw=dict(hl=6))), 0.4, None, 'the letter, rule six lit'),
          ('ins_letter_smear', G(lambda: ST.insert('letter', prop_kw=dict(smear=1.0))), 0.4, None, 'rule six running'),
          ('ins_slot_paper', G(lambda: ST.insert('back_slot', prop_kw=dict(paper=0.8))), 0.4, None, 'the P.S. sliding out of the slot'),
          ('card_rule6', card(6, R6), 0.0, None, 'rule card 6 intact'),
          ('card_rule6_tear', card(6, R6, 2.0, 'tear'), 0.0, None, 'rule card 6 tears (the lie)'),
          ('card_rule6_smear', card(6, R6, 1.9, 'smear', 2.8), 0.0, None, 'rule card 6 smears, LIE'),
          ('card_rule2_flicker', card(2, "He *does voices*.", 2.35, 'flicker'), 0.0, None, 'rule card 2 flickers LIE? (the false lead)')]
POLICE = [('police_porch_doorbell', S(lambda: ST.porch_doorbell()), 1.0, None, 'police regression'),
          ('police_street_wide', S(lambda: ST.street_wide()), 1.0, None, 'police regression'),
          ('police_hallway', S(lambda: ST.hallway()), 1.0, None, 'police regression'),
          ('police_peephole', S(lambda: ST.porch_peephole()), 1.0, None, 'police regression'),
          ('police_living_room', S(lambda: ST.living_room_window()), 1.0, None, 'police regression'),
          ('police_insert_licence', S(lambda: ST.insert('licence')), 1.0, None, 'police regression')]


# ---------------------------------------------------------------------------------------------- the Bunnyman film
def rcard(n, t=4.0):
    """Rule card n (engine.hud.rule_card in the police style + its icon) over the blurred living room."""
    def build():
        sp = ST.ob_living('wide', lamp=0.7)
        return sp, dict(hud=lambda cv, tt: ST.rule_card_bunny(cv, n, t), post=dict(blur=6.0, dim=0.3))
    return build


def I(name, grade=None, **kw):
    return G((lambda n_, kw_: lambda: ST.ob_insert(n_, **kw_))(name, kw), grade)


_feet = lambda t: [(0.28, 0.42), (0.55, 0.69)]
_rattle = lambda t: math.sin(t * 40.0) * (0.6 + 0.4 * math.sin(t * 3.0))
BUNNY = [
    # the living room
    ('liv_wide', G(lambda: ST.ob_living('wide')), 0.5, None, 'from the back-right corner: couch under the lamp, front window, Mom\'s wingback'),
    ('liv_wide2', G(lambda: ST.ob_living('wide2')), 0.5, None, 'from the hall opening: the couch at 3/4 (seat people on the couch here)'),
    ('liv_wide_dark', G(lambda: ST.ob_living('wide', lamp=0.0)), 0.5, None, 'lamp off: moonlight only (grade ob_dark)'),
    ('liv_wide_chairlamp', G(lambda: ST.ob_living('wide', lamp=0.0, chair_lamp=1.0)), 0.5, None, 'only the little lamp by the wingback'),
    ('liv_wide_curtains', G(lambda: ST.ob_living('wide', curtains=0.0)), 0.5, None, 'curtains closed (rule 1)'),
    ('liv_back', G(lambda: ST.ob_living('back')), 0.5, None, 'the back door\'s POV: through the opening, the wingback facing the lens'),
    ('liv_chair', G(lambda: ST.ob_living('chair')), 0.5, None, 'from the couch: the wingback\'s back, the dark kitchen, the back door'),
    ('liv_chair_kitchen', G(lambda: ST.ob_living('chair', kitchen=1.0)), 0.5, None, 'the kitchen light on through the opening'),
    ('liv_couch', G(lambda: ST.ob_living('couch')), 0.5, None, 'medium on the couch (anchors couch_left/mid/right, couch_lie)'),
    ('liv_couch_blanket', G(lambda: ST.ob_living('couch', blanket=True, lamp=0.4)), 0.5, None, '2:47: June\'s blanket left on the couch'),
    ('liv_window', G(lambda: ST.ob_living('window')), 0.5, None, 'the front window, curtains open'),
    ('liv_window_closed', G(lambda: ST.ob_living('window', curtains=0.0)), 0.5, None, 'curtains closed'),
    ('liv_hall', G(lambda: ST.ob_living('hall', hall=1.0)), 0.5, None, 'from the hall into the living room'),
    # hall + stairs + front door
    ('hall_door', G(lambda: ST.ob_hall('door')), 0.5, None, 'facing the front door: peephole, mail slot, deadbolt, chain; stairs left'),
    ('hall_door_dark', G(lambda: ST.ob_hall('door', hall=0.0, console=0.4)), 0.5, None, 'hall light off, console lamp low'),
    ('hall_door_crack', G(lambda: ST.ob_hall('door', door=14, porch=1.0)), 0.5, None, 'the door open a crack, porch light outside'),
    ('hall_door_open_dawn', G(lambda: ST.ob_hall('door', door=88, tod='dawn', hall=0.0)), 0.5, None, 'dawn: the door wide open'),
    ('hall_in', G(lambda: ST.ob_hall('in', living=1.0)), 0.5, None, 'from the door into the house'),
    ('hall_foot', G(lambda: ST.ob_hall('foot', upstairs=1.0)), 0.5, None, 'up the flight from the bottom: June\'s door at the top'),
    ('hall_top', G(lambda: ST.ob_hall('top')), 0.5, None, 'down the flight from the top: the front door at the bottom'),
    ('hall_slot', G(lambda: ST.ob_hall('slot')), 0.5, None, 'the mail slot close, flap shut'),
    ('hall_slot_open', G(lambda: ST.ob_hall('slot', flap=1.0)), 0.5, None, '1:40: the flap pushed open from outside'),
    ('hall_peep', G(lambda: ST.ob_hall('peep')), 0.5, None, 'the peephole + deadbolt close'),
    ('hall_bottom_dawn', G(lambda: ST.ob_hall('bottom', tod='dawn', hall=0.0)), 0.5, None, 'dawn: low at the foot of the stairs'),
    # upstairs
    ('up_hall', G(lambda: ST.ob_upstairs('hall', upstairs=1.0)), 0.5, None, 'the corridor looking west (attic door at the end)'),
    ('up_hall_dark', G(lambda: ST.ob_upstairs('hall', attic_gap=1.0)), 0.5, None, 'dark: only the line of light under the attic door'),
    ('up_west', G(lambda: ST.ob_upstairs('west', upstairs=1.0)), 0.5, None, 'looking east to the window'),
    ('up_bath', G(lambda: ST.ob_upstairs('bath', upstairs=1.0)), 0.5, None, 'from the stairhead: the bathroom door, June\'s door'),
    ('up_june', G(lambda: ST.ob_upstairs('june', june_gap=1.0)), 0.5, None, 'June\'s door, light under it'),
    ('up_from_bath', G(lambda: ST.ob_upstairs('from_bath', upstairs=1.0)), 0.5, None, 'from the bathroom door down the corridor'),
    ('up_hall_wrecked', G(lambda: ST.ob_upstairs('hall', wrecked=1.0, tod='dawn')), 0.5, None, 'dawn: the corridor wrecked'),
    ('up_bath_wrecked', G(lambda: ST.ob_upstairs('bath', wrecked=1.0, tod='dawn')), 0.5, None, 'dawn: the gouged bathroom door'),
    # June's room
    ('june_window', G(lambda: ST.ob_june('window')), 0.5, None, 'June\'s room: the window to the treeline, moon nightlight'),
    ('june_window_closed', G(lambda: ST.ob_june('window', curtains=0.0)), 0.5, None, 'curtains closed'),
    ('june_out', G(lambda: ST.ob_june('out')), 0.5, None, 'the treeline from June\'s window (anchors bunny_treeline / bunny_clearing)'),
    ('june_door', G(lambda: ST.ob_june('door', hall=1.0)), 0.5, None, 'toward the door, hall light'),
    ('june_bed', G(lambda: ST.ob_june('bed')), 0.5, None, 'the bed, made'),
    ('june_bed_empty', G(lambda: ST.ob_june('bed', bed='empty', dress=False)), 0.5, None, 'the bed empty, quilt thrown back'),
    # the bathroom
    ('bath_door', G(lambda: ST.ob_bath('door')), 0.5, None, 'from the tub: the door, the line of light under it'),
    ('bath_door_feet', G(lambda: ST.ob_bath('door', feet=_feet)), 0.5, None, 'two shadows in the gap (someone outside)'),
    ('bath_tub', G(lambda: ST.ob_bath('tub')), 0.5, None, 'the empty tub (anchors tub_left / tub_right)'),
    ('bath_gap', G(lambda: ST.ob_bath('gap')), 0.5, None, 'the gap under the door'),
    ('bath_gap_sunrise', G(lambda: ST.ob_bath('gap', tod='dawn', gap_col=ST.DAWN_C)), 0.5, None, '6:12: the gap turns gold'),
    ('bath_lock', G(lambda: ST.ob_bath('lock')), 0.5, None, 'the lock close: bolt across'),
    ('bath_lock_turning', G(lambda: ST.ob_bath('lock', lock=0.45, key=0.6, tod='dawn', gap_col=ST.DAWN_C)), 0.5, None, 'the bolt turning by itself, the key from outside'),
    # the attic
    ('attic_chest', G(lambda: ST.ob_attic('chest')), 0.5, None, 'Mom\'s old toy chest under the bare bulb'),
    ('attic_corner', G(lambda: ST.ob_attic('corner')), 0.5, None, 'the dark corner (the rocker)'),
    ('attic_mom', G(lambda: ST.ob_attic('mom')), 0.5, None, 'from the stairhead: Mom\'s POV on June at the chest'),
    ('attic_dark', G(lambda: ST.ob_attic('chest', bulb=0.0)), 0.5, None, 'the bulb off'),
    # the kitchen
    ('kit_back', G(lambda: ST.ob_kitchen('back', kitchen=1.0)), 0.5, None, 'the window over the sink, the back door, the fridge'),
    ('kit_back_dark', G(lambda: ST.ob_kitchen('back')), 0.5, None, 'dark kitchen'),
    ('kit_back_smash', G(lambda: ST.ob_kitchen('back', smash_t=0.3)), 0.42, None, 'the window exploding (smash_t)'),
    ('kit_back_smashed', G(lambda: ST.ob_kitchen('back', smash=1.0, mud=1.0)), 0.5, None, 'after: glass, mud drag marks'),
    ('kit_door', G(lambda: ST.ob_kitchen('door', porch=1.0)), 0.5, None, 'the back door, Grandma\'s porch light'),
    ('kit_door_crash', G(lambda: ST.ob_kitchen('door', crash_t=0.3)), 0.4, None, 'the back door crashing open (crash_t)'),
    ('kit_door_open', G(lambda: ST.ob_kitchen('door', back_door=82.0)), 0.5, None, 'the back door hanging open'),
    ('kit_fridge', G(lambda: ST.ob_kitchen('fridge', kitchen=1.0)), 0.5, None, 'the fridge: the rules under the bunny magnet'),
    ('kit_table', G(lambda: ST.ob_kitchen('table', kitchen=1.0)), 0.5, None, 'the table under the pendant'),
    ('kit_memory', G(lambda: ST.ob_kitchen('back', tod='memory')), 0.5, None, 'Grandma\'s daylight kitchen (memory)'),
    # outside
    ('yard_woods', G(lambda: ST.ob_yard('woods')), 0.5, None, 'from the back porch to the treeline'),
    ('yard_woods_light', G(lambda: ST.ob_yard('woods', back_light=1.0)), 0.5, None, 'Grandma\'s porch light on'),
    ('yard_house', G(lambda: ST.ob_yard('house', kitchen=1.0, june_light=1.0)), 0.5, None, 'from the treeline back at the house, windows lit'),
    ('yard_house_dark', G(lambda: ST.ob_yard('house')), 0.5, None, 'the house dark'),
    ('yard_wide', G(lambda: ST.ob_yard('wide', back_light=1.0)), 0.5, None, 'establishing from the east side'),
    ('yard_close', G(lambda: ST.ob_yard('close')), 0.5, None, 'telephoto on the treeline (anchor treeline)'),
    ('yard_dawn', G(lambda: ST.ob_yard('woods', tod='dawn')), 0.5, None, 'dawn'),
    ('woods_edge_sunrise87', G(lambda: ST.ob_yard('close', tod='sunrise87')), 0.5, None, '1987 sunrise: the woods\' edge (little Laurie walks out)'),
    ('yard_barrel', G(lambda: ST.ob_yard('barrel', fire=1.0, egg=0.4)), 1.2, None, 'the burn barrel: the egg melting in the fire'),
    ('front_house', G(lambda: ST.ob_front('house')), 0.5, None, 'the last house on Orchard Road, porch light on'),
    ('front_house_off', G(lambda: ST.ob_front('house', front_light=0.0)), 0.5, None, 'porch light off'),
    ('front_porch', G(lambda: ST.ob_front('porch', egg=True)), 0.5, None, 'on the porch: the egg on the doormat'),
    ('front_egg', G(lambda: ST.ob_front('egg', egg=True, egg_rattle=_rattle)), 0.5, None, 'low on the egg (rattling)'),
    ('front_peephole', G(lambda: ST.ob_front('peephole', egg=True)), 0.5, None, 'the fisheye peephole view: the empty porch, the egg'),
    ('front_police', G(lambda: ST.ob_front('house', tod='dawn', police=dict(mode='sweep'))), 0.5, None, 'dawn: police lights at the house'),
    ('woods_bridge', G(lambda: ST.ob_woods('bridge')), 0.5, None, 'the old railroad bridge'),
    ('woods_under', G(lambda: ST.ob_woods('under')), 0.5, None, 'Dad\'s flashlight on the gravel, still on'),
    ('woods_path', G(lambda: ST.ob_woods('path')), 0.5, None, 'deep in Holloway Woods'),
    ('woods_day87', G(lambda: ST.ob_woods('bridge', tod='day87')), 0.5, None, '1987: the search, overcast'),
    ('hosp_room', G(lambda: ST.ob_hospital('room')), 0.5, None, 'the narrator\'s room, the window, the calendar'),
    ('hosp_bed', G(lambda: ST.ob_hospital('bed')), 0.5, None, 'the bed, the calendar'),
    ('hosp_visit', G(lambda: ST.ob_hospital('visit')), 0.5, None, 'the visiting room'),
    ('hosp_table', G(lambda: ST.ob_hospital('table')), 0.5, None, 'a visiting table'),
    ('hosp_corridor', G(lambda: ST.ob_hospital('corridor')), 0.5, None, 'the corridor'),
    ('parade_street', G(lambda: ST.ob_parade('street')), 0.5, None, '1987 parade: Main Street, the float, the crowd (VHS)'),
    ('parade_store', G(lambda: ST.ob_parade('store')), 0.5, None, 'Pemberton\'s store front (VHS)'),
    ('parade_photo', G(lambda: ST.ob_parade('photo')), 0.5, None, 'the photo spot by the float (VHS)'),
    ('parade_clean', G(lambda: ST.ob_parade('street', vhs=False)), 0.5, None, 'the street without the tape look'),
]
for n in ST.INSERTS_B:
    BUNNY.append(('ins_' + n, I(n), 0.5, None, ST.INSERTS_B[n][2]))
BUNNY += [
    ('ins_rules_hl3', I('rules', prop_kw=dict(hl=3)), 0.5, None, 'the rules, rule 3 highlighted'),
    ('ins_egg_rattle', I('egg', prop_kw=dict(rattle=_rattle)), 0.53, None, 'the egg rattling on the mat'),
    ('ins_slot_eyes', I('slot', prop_kw=dict(flap=0.9, eyes=1.0)), 0.5, None, 'the flap up, a glint in the dark'),
    ('ins_lock_key', I('lock', grade='ins_dawn', prop_kw=dict(lock=0.4, key=0.7, knob=12)), 0.5, None, 'the bolt turning, the key from outside'),
    ('ins_clock_113', I('clock', prop_kw=dict(time=(1, 13))), 0.5, None, '1:13'),
    ('ins_clock_612', I('clock', prop_kw=dict(time=(6, 12), kind='digital')), 0.5, None, '6:12 (June\'s clock)'),
    ('ins_switch_off', I('switch', prop_kw=dict(on=False)), 0.5, None, 'the porch switch off'),
    ('ins_drawing_slide', I('drawing', prop_kw=dict(slide=0.45)), 0.5, None, 'the drawing coming under the door'),
] + [('card_rule%d' % n, rcard(n), 0.0, None, 'rule card %d (typed on, key words in red)' % n) for n in range(1, 8)]


# staging test stills: (name, set builder, [(who, spot, stage_figure kwargs)], note)
STAGE = [
    ('liv_wide', lambda: ST.ob_living('wide'), [('mom', 'armchair', dict(expr='too_still'))], 'Mom in the wingback (the couch is front-on here)'),
    ('liv_wide2', lambda: ST.ob_living('wide2'), [('narrator', 'couch_mid', dict(seed=3)), ('june', 'couch_right', dict(seed=4))],
     'the kids on the couch at 3/4'),
    ('liv_couch', lambda: ST.ob_living('couch'), [('narrator', 'couch_mid', dict(seed=3)), ('june', 'couch_right', dict(seed=4)),
                                                  ('mom', 'window_front', dict(turn=2.0))], 'on the couch; Mom at the front window'),
    ('liv_back', lambda: ST.ob_living('back', chair_lamp=1.0), [('mom', 'armchair', dict(expr='too_still'))], 'Mom facing the back door'),
    ('kit_fridge', lambda: ST.ob_kitchen('fridge', kitchen=1.0), [('mom', 'fridge', {})], 'Mom at the fridge (the rules)'),
    ('hall_door', lambda: ST.ob_hall('door'), [('mom', 'peephole_eye', {}), ('narrator', 'stairs_foot', dict(seed=3))],
     'Mom at the peephole (back to camera), the narrator at the foot of the stairs'),
    ('up_hall', lambda: ST.ob_upstairs('hall', upstairs=1.0), [('mom', 'hall_mid', dict(turn=0.0, expr='too_still'))], 'Mom in the corridor'),
    ('bath_tub', lambda: ST.ob_bath('tub'), [('narrator', 'tub_left', dict(seed=3)), ('june', 'tub_right', dict(seed=4))],
     'the kids in the empty tub (the near wall in front of them)'),
    ('june_window', lambda: ST.ob_june('window'), [('june', 'window', {})], 'June at her window'),
    ('june_out', lambda: ST.ob_june('out'), [('bunny', 'bunny_treeline', {})], 'the Bunnyman at the treeline from June\'s window'),
    ('attic_mom', lambda: ST.ob_attic('mom'), [('june', 'chest_floor', {})], 'June kneeling at the toy chest'),
    ('yard_woods', lambda: ST.ob_yard('woods', back_light=1.0), [('bunny', 'treeline', {}), ('dad', 'yard_mid', {})],
     'Dad walking to the treeline, the Bunnyman waiting'),
    ('hosp_table', lambda: ST.ob_hospital('table'), [('mom_hosp', 'seat1', {}), ('narrator_neat', 'seat0', dict(expr='wrong_smile'))],
     'the visit: the narrator in Mom\'s body, the thing in the narrator\'s'),
]


def stage_run():
    set_render_size(W0, H0)
    tiles = []
    for name, build, figs, note in STAGE:
        t0 = time.time()
        sp = build()
        lays = [ST.stage_figure(sp, who, spot, **kw)[0] for who, spot, kw in figs]
        sp2 = sp.add(*lays)
        img = render_frame(list(sp2), None, 0.5, 0, **sp2.render_kw(), post=sp2.fx(0.5))
        cv2.imwrite(os.path.join(a.out, 'stage_' + name + '.jpg'), img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        tiles.append(label(cv2.resize(img[:, :, ::-1], (640, 360), interpolation=cv2.INTER_AREA).copy(), 'stage_' + name))
        print('%-24s %5.2fs  %s' % ('stage_' + name, time.time() - t0, note), flush=True)
    cols = 3
    rows = [np.hstack(tiles[i:i + cols] + [np.zeros_like(tiles[0])] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    cv2.imwrite(os.path.join(a.out, 'stage_sheet.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 86])


def cam_for(sp, mode):
    if mode == 'doorway' and 'doorway_cam' in sp.info:
        return ST.doorway_camera(sp, 0.0, 6.0)
    if mode == 'kopen':                                                       # optical push down the hall to the opening
        x0, y0, x1, y1 = sp.info['kopen']
        return Cam([(0.0, (x0 + x1) / 2, (y0 + y1) / 2 - 10, 1.15)]).snap(-1.0, 3.2, 0.001)
    return hold()


def render(sp, opt, t, cam, i=0):
    kw = sp.render_kw()
    post = dict(sp.fx(t)); post.update(opt.get('post', {}))
    return render_frame(list(sp), cam.at(t), t, i, **kw, post=post, hud=opt.get('hud'))


def label(img, s):
    cv2.rectangle(img, (0, img.shape[0] - 26), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
    cv2.putText(img, s, (8, img.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def main():
    os.makedirs(a.out, exist_ok=True)
    if a.stage:
        stage_run(); return
    vs = POLICE if a.police else (DELIVERY if a.delivery else (DUMMY if a.dummy else BUNNY))
    if a.only: vs = [v for v in vs if any(k in v[0] for k in a.only.split(','))]
    thumbs, index = [], []
    for name, build, t, cm, note in vs:
        t0 = time.time()
        sp, opt = build()
        img = render(sp, opt, t, cam_for(sp, cm))
        cv2.imwrite(os.path.join(a.out, name + '.jpg'), img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        th = cv2.resize(img[:, :, ::-1], (480, 270), interpolation=cv2.INTER_AREA)
        anchors = sorted(sp.anchors)
        if hasattr(ST, 'Spot') and any(isinstance(v_, ST.Spot) for v_ in sp.anchors.values()):
            anchors = {k_: dict(kind=v_.kind, x=round(v_.x, 1), y=round(v_.y, 1), depth=round(v_.depth, 3), ppm=round(v_.ppm, 1),
                                plan=(round(v_.X, 2), round(v_.Yp, 2), round(v_.Y, 2)), turn=None if v_.turn is None else round(v_.turn, 2),
                                seat_y=None if v_.seat_y is None else round(v_.seat_y, 1), note=v_.note)
                       for k_, v_ in sorted(sp.anchors.items()) if isinstance(v_, ST.Spot)}
        thumbs.append(label(th.copy(), name)); index.append(dict(name=name, set=sp.name, t=t, note=note, lens=str(sp.lens),
                                                                   grade=str(sp.grade), anchors=anchors))
        print('%-32s %5.2fs  %s' % (name, time.time() - t0, note), flush=True)
    if not a.no_sheet and thumbs:
        cols = 5
        rows = [np.hstack(thumbs[i:i + cols] + [np.zeros_like(thumbs[0])] * (cols - len(thumbs[i:i + cols]))) for i in range(0, len(thumbs), cols)]
        sheet = np.vstack(rows)
        pre = 'police_' if a.police else ('delivery_' if a.delivery else ('dummy_' if a.dummy else ''))
        cv2.imwrite(os.path.join(a.out, pre + 'contact_sheet.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
        if not (a.police or a.delivery or a.dummy): ST.plan_map(os.path.join(a.out, 'floorplan.jpg'))
        if not a.only: json.dump(index, open(os.path.join(a.out, pre + 'index.json'), 'w'), indent=1)
    if a.frame:
        frame_check(vs)
    if a.bench:
        bench(vs)


def frame_check(vs):
    """Render every view at the corners of its widest camera move (sp.info['cam_env']: x, y ranges of the frame centre on the
    depth-1 plane at zoom 1, f = 1, plus +-8 px of handheld) over a MAGENTA background at 480x270: any magenta pixel is a
    hole past a set plate's edge (the post move uses reflect padding, so a hole there would show a mirrored copy instead:
    film.py must keep post offsets inside the post zoom's margin). Also renders the deepest push (max zoom and optical f
    at the envelope centre). Writes frame_check.json and frame_check.jpg (the worst corner of each view)."""
    set_render_size(480, 270)
    res, tiles = [], []
    seen = set()
    for name, build, t, cm, note in vs:
        sp, opt = build()
        key = (sp.name, cm)
        if key in seen: continue
        seen.add(key)
        env = sp.info.get('cam_env') or dict(x=(920, 1000), y=(500, 580), zoom=(1.0, 1.1), f=(1.0, 1.0))
        x0, x1 = env['x']; y0, y1 = env['y']; z1 = env.get('zoom', (1.0, 1.0))[1]; f1 = env.get('f', (1.0, 1.0))[1]
        cams = [('%s_%s' % (cx_n, cy_n), Cam([(0.0, cx + dx, cy + dy, 1.0)]))
                for (cx_n, cx, dx) in (('L', x0, -8), ('R', x1, 8)) for (cy_n, cy, dy) in (('T', y0, -8), ('B', y1, 8))]
        cams.append(('deep', Cam([(0.0, (x0 + x1) / 2, (y0 + y1) / 2, z1)]).snap(-1.0, f1, 0.001)))
        worst, wimg, wname = -1.0, None, ''
        for cn, cam in cams:
            kw = sp.render_kw()
            post = dict(sp.fx(t)); post.update(opt.get('post', {}))
            post.pop('vhs', None)                                             # the tube mask is black by design: test the plates
            img = render_frame(list(sp), cam.at(t), t, 0, **kw, post=post, bg='#ff00ff')
            r_, g_, b_ = (img[..., k].astype(np.int16) for k in range(3))            # magenta, also where it is blended
            mag = float(np.mean((r_ > 150) & (b_ > 150) & (g_ * 20 < np.minimum(r_, b_) * 9)))
            if mag > worst: worst, wimg, wname = mag, img, cn
        res.append(dict(name=name, worst_hole=round(worst, 5), at=wname, env=env))
        th = wimg[:, :, ::-1].copy()
        tiles.append(label(th, '%s %s %.3f%%' % (name, wname, worst * 100)))
        print('frame %-28s worst %.4f%% (%s)' % (name, worst * 100, wname), flush=True)
    cols = 6
    rows = [np.hstack(tiles[i:i + cols] + [np.zeros_like(tiles[0])] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    cv2.imwrite(os.path.join(a.out, 'frame_check.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump(res, open(os.path.join(a.out, 'frame_check.json'), 'w'), indent=1)
    bad = [r for r in res if r['worst_hole'] > 0.0002]
    print('frame check: %d views, %d with holes > 0.02 %%: %s' % (len(res), len(bad), ', '.join(r['name'] for r in bad)))
    set_render_size(W0, H0)


def bench(vs):
    """Steady-state seconds per frame at 2560x1440 (caches warm, 1 OpenCV thread), camera pushing in 2.5 %/s."""
    set_render_size(2560, 1440)
    res = []
    for name, build, t, cm, note in vs:
        sp, opt = build()
        base = cam_for(sp, cm).at(t)
        cam = push_in(t, t + 10, base.x, base.y, base.zoom, rate=0.025)
        if cm == 'doorway': cam = cam.snap(t - 1.0, base.fz, 0.001)
        render(sp, opt, t, cam)                                                # warm caches
        ts = []
        for k in range(a.bench_frames):
            tt = t + (k + 1) / 60.0
            t0 = time.perf_counter(); render(sp, opt, tt, cam, k + 1); ts.append(time.perf_counter() - t0)
        res.append(dict(name=name, mean_s=round(float(np.mean(ts)), 3), max_s=round(float(np.max(ts)), 3)))
        print('bench %-32s mean %.3f s  max %.3f s' % (name, res[-1]['mean_s'], res[-1]['max_s']), flush=True)
    json.dump(res, open(os.path.join(a.out, ('police_' if a.police else ('delivery_' if a.delivery else ('dummy_' if a.dummy else ''))) + 'bench_2560.json'), 'w'), indent=1)
    ms = [r['mean_s'] for r in res]
    print('bench: %d variants, mean %.3f s/frame, worst %.3f s (%s); police budget 0.6 s/frame' %
          (len(ms), float(np.mean(ms)), max(ms), res[int(np.argmax(ms))]['name']))


if __name__ == '__main__':
    main()
