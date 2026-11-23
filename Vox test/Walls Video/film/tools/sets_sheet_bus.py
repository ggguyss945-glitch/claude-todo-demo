# The Bus film's set variants and staging tests for tools/sets_sheet.py (exec'd there: ST, G, math are in scope).
#   python3 tools/sets_sheet.py                 every set / view / state / insert (1280x720) -> W/sets/*.jpg, contact_sheet.jpg,
#                                               index.json (anchors with plan + screen data), floorplan.jpg
#   python3 tools/sets_sheet.py --stage         cast figures placed only from the sets' Spots -> stage_*.jpg + stage_sheet.jpg
#   python3 tools/sets_sheet.py --frame         the widest-framing edge check -> frame_check.json / .jpg
#   python3 tools/sets_sheet.py --bench         draw time at 2560x1440 -> bench_2560.json


def BI(name, grade=None, **kw):
    return G((lambda n_, kw_: lambda: ST.bu_insert(n_, **kw_))(name, kw), grade)


_lit = dict(liv=1.0, hall=0.6, gran=0.0, mina=0.8, den=0.0)
BUS = [
    # ---- Larch Street at night
    ('ext_house', G(lambda: ST.bu_front('house', his_heads=1.0)), 0.5, None, 'the house from across the street: bus 9 in the driveway, his bus at the kerb, headlights on'),
    ('ext_house_before', G(lambda: ST.bu_front('house', his=False, porch=1.0, win=_lit)), 0.5, None, 'before midnight: windows lit, porch light on, no bus at the kerb'),
    ('ext_street', G(lambda: ST.bu_front('street')), 0.5, None, 'from the porch: the walk, the lawn, the mailbox, his bus under the streetlight (tape-skip path)'),
    ('ext_street_flicker', G(lambda: ST.bu_front('street', street=0.08)), 0.5, None, 'the streetlight out (a flicker)'),
    ('ext_curb', G(lambda: ST.bu_front('curb', his_door=1.0)), 0.5, None, 'his bus door folded open (he unfolds out of it)'),
    ('ext_mailbox', G(lambda: ST.bu_front('mailbox')), 0.5, None, 'our mailbox: HAYES in stick-on letters'),
    ('ext_mailbox_off', G(lambda: ST.bu_front('mailbox', letters=0.0, his=False)), 0.5, None, 'the letters unscrewed (rule one)'),
    ('ext_porch', G(lambda: ST.bu_front('porch')), 0.5, None, 'the porch at 3/4 (the broom by the door)'),
    ('ext_door', G(lambda: ST.bu_front('door', frost_lit=0.6)), 0.5, None, 'up the steps to the front door'),
    ('ext_frame', G(lambda: ST.bu_front('frame')), 0.5, None, 'the doorframe close (the gloves curl round it)'),
    ('ext_driveway', G(lambda: ST.bu_front('driveway', broom='bus9', cab9=0.6)), 0.5, None, "bus 9 across the side yard, the broom through its doors, Grandma's cab lit"),
    ('ext_bus9door', G(lambda: ST.bu_front('bus9door', broom='bus9', cab9=0.6)), 0.5, None, "bus 9's doors close: the broom wedged through"),
    ('ext_sideyard', G(lambda: ST.bu_front('sideyard', flash=1.0, flash_at=(-6.1, -0.2, 5.0))), 0.5, None, 'the side yard: the flashlight crossing'),
    ('ext_peephole', G(lambda: ST.bu_front('peephole', porch=0.0)), 0.5, None, 'the fisheye through the peephole'),
    ('ext_gap', G(lambda: ST.bu_front('gap', his_door=0.0)), 0.5, None, 'POV through the curtain gap: his bus at the kerb'),
    ('ext_granout', G(lambda: ST.bu_front('granout', his=False, flash=1.0)), 0.5, None, "down from Grandma's window: bus 9, the flashlight in its cab"),
]

_tv = lambda t: 0.7
BUS += [
    # ---- the living room
    ('liv_wide', G(lambda: ST.bu_living('wide', lamp=1.0)), 0.5, None, 'the living room, the floor lamp on (before midnight)'),
    ('liv_wide_dark', G(lambda: ST.bu_living('wide', heads=1.0)), 0.5, None, 'lights off; his headlights fill the curtains'),
    ('liv_reverse', G(lambda: ST.bu_living('reverse', lamp=1.0, tv=0.6)), 0.5, None, 'from the window: the couch face-on, the TV on'),
    ('liv_couch', G(lambda: ST.bu_living('couch')), 0.5, None, 'medium on the couch at night'),
    ('liv_couch3q', G(lambda: ST.bu_living('couch3q', lamp=0.6)), 0.5, None, 'the couch at 3/4 (seated figures)'),
    ('liv_window', G(lambda: ST.bu_living('window', heads=0.6)), 0.5, None, 'the curtains and the gap, headlights behind'),
    ('liv_door', G(lambda: ST.bu_living('door')), 0.5, None, 'from the couch to the front door through the opening'),
    ('liv_hand', G(lambda: ST.bu_living('hand', blackout=True, phone=1.0, phone_at=(-0.1, 0.9, 4.2))), 0.5, None, 'blackout: only the phone light on the cushion'),
    ('liv_wall_pack', G(lambda: ST.bu_living('reverse', lamp=1.0, backpack='wall')), 0.5, None, 'the backpack turned to the wall (rule one)'),
    # ---- the front hall
    ('hall_door', G(lambda: ST.bu_hall('door', hall=1.0)), 0.5, None, 'the front door: frosted panes, peephole, the rules taped inside'),
    ('hall_door_dark', G(lambda: ST.bu_hall('door', porch=1.0, frost=1.0)), 0.5, None, 'dark hall, his silhouette through the frosted panes'),
    ('hall_doorclose', G(lambda: ST.bu_hall('doorclose', hall=0.8, ticket=1.0)), 0.5, None, 'close on the door: the rules, the ticket under the door'),
    ('hall_side', G(lambda: ST.bu_hall('side', hall=0.6)), 0.5, None, '3/4 on the door from the opening'),
    ('hall_stairs', G(lambda: ST.bu_hall('stairs', hall=1.0, up=0.6)), 0.5, None, 'down the hall: the stairs, the back door'),
    ('hall_up', G(lambda: ST.bu_hall('up', hall=0.6, up=1.0)), 0.5, None, 'up the stairs'),
    ('hall_window', G(lambda: ST.bu_hall('window', broom='bus9', cab9=0.6)), 0.5, None, 'the side window: bus 9 across the yard'),
    # ---- upstairs
    ('up_hall', G(lambda: ST.bu_upstairs('hall', up=1.0, gran_door=95)), 0.5, None, "from Grandma's doorway down the hall"),
    ('up_back', G(lambda: ST.bu_upstairs('back', up=1.0)), 0.5, None, "from the landing to Grandma's door"),
    ('up_stairs', G(lambda: ST.bu_upstairs('stairs', up=1.0)), 0.5, None, 'down the stairs from the landing'),
    ('gran_door', G(lambda: ST.bu_gran('door', lamp=0.7)), 0.5, None, "Grandma's room: the deadbolted door"),
    ('gran_window', G(lambda: ST.bu_gran('window')), 0.5, None, "Grandma's window over the driveway"),
    ('gran_wide', G(lambda: ST.bu_gran('wide', lamp=1.0)), 0.5, None, "Grandma's room wide"),
    ('sami_room', G(lambda: ST.bu_sami('room')), 0.5, None, "Sami's room, the dino nightlight"),
    ('sami_bed', G(lambda: ST.bu_sami('bed', ceil=1.0)), 0.5, None, "Sami's bed and Rex, light on"),
]

STAGE_BUS = []

BUS += [
    # ---- inside his bus
    ('his_aisle', G(lambda: ST.bu_bus_in('aisle')), 0.5, None, 'his bus: the aisle, every seat dark but seat 4 and seat 22'),
    ('his_back', G(lambda: ST.bu_bus_in('back')), 0.5, None, 'his bus from the back forward'),
    ('his_seat4', G(lambda: ST.bu_bus_in('seat4')), 0.5, None, 'seat 4 and its window'),
    ('his_seat22', G(lambda: ST.bu_bus_in('seat22')), 0.5, None, 'seat 22 glowing'),
    ('his_steps', G(lambda: ST.bu_bus_in('steps', door=1.0)), 0.5, None, 'down the steps, the doors open'),
    ('his_doors', G(lambda: ST.bu_bus_in('doors', door=0.25, broom=1.0, bend=0.6)), 0.5, None, 'the doors closing on the broom (bending)'),
    ('his_doors_crack', G(lambda: ST.bu_bus_in('doors', door=0.15, broom=1.0, crack=1.0)), 0.5, None, 'the broom cracks'),
    ('his_driver', G(lambda: ST.bu_bus_in('driver', door=1.0)), 0.5, None, "his driver's seat and the steps"),
    # ---- bus 9 at night (the chase)
    ('b9_cab', G(lambda: ST.bu_bus_in('cab', kind='bus9', drive=14.0, his_ahead=(0.0, -26.0))), 0.5, None, 'bus 9 driving: Grandma at the wheel, his dark bus ahead'),
    ('b9_seat1', G(lambda: ST.bu_bus_in('seat1', kind='bus9', drive=14.0)), 0.5, None, 'Mina in seat 1'),
    ('b9_radio', G(lambda: ST.bu_bus_in('radio', kind='bus9', drive=14.0)), 0.5, None, 'the dash radio'),
    ('b9_windshield', G(lambda: ST.bu_bus_in('windshield', kind='bus9', drive=14.0, his_ahead=(0.0, -18.0), brake=1.0)), 0.5, None, 'POV: his brake lights flash ahead'),
    # ---- bus 9 in the morning
    ('b9m_aisle', G(lambda: ST.bu_bus_in('aisle', kind='bus9', tod='morning')), 0.5, None, 'bus 9 in the morning, sunlight'),
    ('b9m_seat21', G(lambda: ST.bu_bus_in('seat21', kind='bus9', tod='morning')), 0.5, None, 'seat 21 (the new girl)'),
    ('b9m_back_window', G(lambda: ST.bu_bus_in('back_window', kind='bus9', tod='morning')), 0.5, None, 'out of the rear window: the far tall figure'),
]

BUS += [
    ('his_step_out', G(lambda: ST.bu_bus_in('step_out', door=1.0)), 0.5, None, 'the bottom-step view up into his bus'),
    # ---- the chase
    ('road_side', G(lambda: ST.bu_road('side', his_pos=(-3.6, -4.0), his_win=0.0)), 0.5, None, 'beside the road: his bus swerving in front of bus 9'),
    ('road_ahead', G(lambda: ST.bu_road('ahead', his_pos=(0.0, -24.0), his_win=0.0, brake=1.0)), 0.5, None, 'his dark bus ahead, brake lights'),
    ('road_behind', G(lambda: ST.bu_road('behind', his_pos=(0.0, 22.0), his_win=1.0, mirror_r=False)), 0.5, None, 'his amber windows behind bus 9 (mirror gone)'),
    ('road_window', G(lambda: ST.bu_road('window', his_pos=(0.0, -24.0))), 0.5, None, "his driver's window close"),
    # ---- the school
    ('sch_wide', G(lambda: ST.bu_school('wide')), 0.5, None, 'Larkfield Elementary at 2:57 AM'),
    ('sch_doors', G(lambda: ST.bu_school('doors')), 0.5, None, 'his bus at the doors, open, amber, cobwebs in the wipers'),
    ('sch_doors_broom', G(lambda: ST.bu_school('doors', his_door=0.3, broom9=1.0, bend=0.7)), 0.5, None, 'the doors folding shut on the broom'),
    ('sch_clock', G(lambda: ST.bu_school('clock', clock=(2, 59))), 0.5, None, 'the clock: 2:59'),
    ('sch_flag', G(lambda: ST.bu_school('flag')), 0.5, None, 'the flagpole'),
    ('sch_reverse', G(lambda: ST.bu_school('reverse')), 0.5, None, "back to the lot: bus 9's headlights"),
    ('sch_lot', G(lambda: ST.bu_school('lot', his=False, clipboard=True, tail=True, police=True, clock=(3, 0))), 0.5, None, 'after: the empty lot, the clipboard, police lights'),
    ('theo_house', G(lambda: ST.bu_theo_stop('house', porch=0.0)), 0.5, None, "Theo's stop, dark"),
    ('theo_house_on', G(lambda: ST.bu_theo_stop('house', porch=1.0)), 0.5, None, "the porch light comes on"),
]

BUS += [
    ('tape_full', G(lambda: ST.bu_tape94('full')), 0.5, None, "1994: Ride Right with Mister Whistlestop!, Channel 6 (full frame, VHS)"),
    ('tape_kids', G(lambda: ST.bu_tape94('kids')), 0.5, None, 'the kids hold up their cards'),
    ('tape_title', G(lambda: ST.bu_tape94('title')), 0.5, None, 'the title card'),
    ('class_cart', G(lambda: ST.bu_class94('cart')), 0.5, None, '1994: the classroom TV cart playing the tape'),
    ('class_tv', G(lambda: ST.bu_class94('tv', 'kids')), 0.5, None, 'closer on the CRT'),
]
for _n in ST.BU_INSERTS:
    BUS.append(('ins_' + _n, BI(_n), 0.5, None, ST.BU_INSERTS[_n][2]))
BUS += [
    ('ins_post_hl', BI('post', prop_kw=dict(show=2, hl='comment')), 0.5, None, 'the post, the comment highlighted'),
    ('ins_rules_8', BI('rules', prop_kw=dict(eighth=True)), 0.5, None, 'the rules with rule 8 added'),
    ('ins_rules_hl4', BI('rules', prop_kw=dict(hl=4)), 0.5, None, 'the rules, rule 4 lit'),
    ('ins_clipboard_last', BI('clipboard', prop_kw=dict(page='last')), 0.5, None, "the last page: today's date, one name"),
    ('ins_backpack_back', BI('backpack', prop_kw=dict(side='back')), 0.5, None, 'the backpack turned to the wall'),
    ('ins_mailbox_half', BI('mailbox', prop_kw=dict(letters=0.4)), 0.5, None, 'the letters half unscrewed'),
    ('ins_clock_300', BI('clock', prop_kw=dict(time=(3, 0, 0))), 0.5, None, '3:00'),
    ('ins_walkie_talk', BI('walkie', prop_kw=dict(talk=1.0)), 0.5, None, 'the walkie talking (LED on)'),
]

# staging test stills: cast placed ONLY from the sets' Spots (ST.stage_figure)
STAGE_BUS = [
    ('liv_couch', lambda: ST.bu_living('couch3q', lamp=1.0), [('mina', 'couch_right', {}), ('sami', 'couch_mid', dict(seed=2)), ('della', 'armchair', dict(seed=3))],
     'Mina and Sami on the couch, Grandma in her armchair'),
    ('hall_door', lambda: ST.bu_hall('door', hall=0.6), [('mina', 'peephole_eye', {}), ('della', 'hall_mid', dict(seed=2))], 'Mina at the peephole, Grandma behind'),
    ('ext_street', lambda: ST.bu_front('street'), [('whistle', 'mailbox', {}), ('whistle', 'lawn_mid', dict(seed=2, name='w2')), ('whistle', 'porch_step', dict(seed=3, name='w3'))],
     'the three tape-skips: mailbox, lawn, porch steps'),
    ('up_hall', lambda: ST.bu_upstairs('hall', up=0.6, gran_door=95), [('whistle', 'hall_mid', {})], 'him in the upstairs hall (he must bend double: ceiling 2.4 m)'),
    ('gran_door', lambda: ST.bu_gran('door', lamp=0.6), [('mina', 'door_sit', {}), ('sami', 'bed_edge', dict(seed=2))], "Mina's back against the deadbolted door"),
    ('his_aisle', lambda: ST.bu_bus_in('aisle'), [('sami', 'seat4', {}), ('theo', 'seat22', dict(seed=2)), ('whistle', 'aisle5', dict(seed=3))], 'his bus: Sami in seat 4, Theo in 22'),
    ('b9_seat1', lambda: ST.bu_bus_in('seat1', kind='bus9', drive=14.0), [('mina', 'seat1', {}), ('della', 'driver', dict(seed=2))], 'Mina in seat 1, Grandma driving'),
    ('sch_doors', lambda: ST.bu_school('doors'), [('mina_bare', 'bottom_step', {}), ('della', 'behind_mina', dict(seed=2)), ('whistle', 'his_top', dict(seed=3))],
     'the last stop: Mina at the bottom step, Grandma behind, him at the top of his steps'),
    ('b9m_seat21', lambda: ST.bu_bus_in('seat21', kind='bus9', tod='morning'), [('new_girl', 'seat21_win', {}), ('mina', 'seat21_aisle', dict(seed=2))], 'morning: Mina sits next to the new girl'),
]
