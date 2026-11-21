# The ice cream film's variants for tools/sets_sheet_ice.py (exec'd there: ST, G, II, math in scope).
# (name, builder, t, note). STAGE_ICE: (name, set builder, [(who, spot, stage_figure kwargs)], note).
_A = dict(truck='A')
ICE = [
    # ---- Birch Lane at night (truck at A)
    ('ext_house', G(lambda: ST.ic_street('house', win=dict(liv=0.9, kitchen=0.5))), 0.5, 'our house from across the lane, the truck at A (window lit before the power dies)'),
    ('ext_house_dark', G(lambda: ST.ic_street('house', blackout=True, our_smoke=0.0)), 0.5, 'after the power dies: our windows dark, no smoke from our chimney'),
    ('ext_kessler', G(lambda: ST.ic_street('kessler')), 0.5, "Kessler's house from our yard: his dark window, NO chimney smoke; the truck at A right"),
    ('ext_kessler_notruck', G(lambda: ST.ic_street('kessler', truck=None, win=dict(his=0.25))), 0.5, "before the truck: Lina waves at his window (faint light)"),
    ('ext_lane', G(lambda: ST.ic_street('lane', win=dict(liv=0.9))), 0.5, 'down Birch Lane from the west: the truck at A, no tracks behind it'),
    ('ext_lane_e', G(lambda: ST.ic_street('lane_e')), 0.5, 'up Birch Lane from the east'),
    ('ext_truck', G(lambda: ST.ic_street('truck')), 0.5, 'the truck at A from our walk at child height'),
    ('ext_curb', G(lambda: ST.ic_street('curb', truck_open=1.0)), 0.5, 'low at the kerb up at the serving window (open)'),
    ('ext_window_close', G(lambda: ST.ic_street('window_close', truck_open=1.0)), 0.5, 'the serving window close: frost, mitten bunting'),
    ('ext_window_lina', G(lambda: ST.ic_street('window_close', truck_open=0.0, lina_mitten=True)), 0.5, "Lina's mitten added at the right end"),
    ('ext_door', G(lambda: ST.ic_street('door', porch=0.0, tracks=[('child', [(-2.1, -0.6), (-2.1, -2.3), (-2.1, -6.4), (-0.6, -7.7)])],
                                         props=[('mitten', -2.05, -2.6), ('mitten', -1.9, -4.6)])), 0.5, 'our door from the walk: her footprints, her two mittens'),
    ('ext_door_boot', G(lambda: ST.ic_street('door', props=[('boot', -0.45, -7.55)], walk='trodden')), 0.5, 'our door, the boot frozen at the kerb behind'),
    ('ext_yard', G(lambda: ST.ic_street('yard', blackout=True, our_smoke=0.0)), 0.5, "the chase route: the fence, Dad's car, our roof"),
    ('ext_roof', G(lambda: ST.ic_street('roof', blackout=True, our_smoke=0.0)), 0.5, 'up at our roof and eave'),
    ('ext_gap', G(lambda: ST.ic_street('gap')), 0.5, 'POV through the curtain crack: the truck, Kessler\'s window'),
    ('ext_flicker', G(lambda: ST.ic_street('truck', street=0.05)), 0.5, 'the streetlight out (one flicker)'),
    ('ext_plow', G(lambda: ST.ic_street('plow', plow=dict(x=-2.0, y=-11.0, dir=1, beacon=1.0), truck=None)), 0.5, "Dad's plow passing, the beacon"),
    ('ext_plow_climax', G(lambda: ST.ic_street('lane', truck='B', plow=dict(x=-9.0, y=-11.4, dir=1, beacon=1.0), porches=[1.0, 1.0, 0.0, 1.0], kporch=0.0)), 0.5,
     'the plow roars onto Birch Lane; porch lights coming on'),
    # ---- Birch Lane, the truck at B
    ('ext_kwide', G(lambda: ST.ic_street('kwide', truck='B', kdoor_open=True, blackout=True)), 0.5, "Kessler's porch and the truck at B, his door open"),
    ('ext_kporch', G(lambda: ST.ic_street('kporch', truck='B', kdoor_open=True)), 0.5, "Kessler's porch and door from his walk"),
    ('ext_kdoor', G(lambda: ST.ic_street('kdoor', truck='B', kdoor_open=True)), 0.5, "close on his doorway (the huddle)"),
    ('ext_kout', G(lambda: ST.ic_street('kout', truck='B', kdoor_open=True, blackout=True, our_smoke=0.0)), 0.5, "from his doorway: the truck at B, our house across"),
    ('ext_bathout', G(lambda: ST.ic_street('bathout', truck='B', kdoor_open=True, blackout=True)), 0.5, 'POV through the bathroom window to Kessler\'s door'),
    ('ext_porches', G(lambda: ST.ic_street('house', truck='B', porches=1.0, porch=1.0, blackout=True)), 0.5, 'porch lights on all along the lane'),
    # ---- 1958, the morning, across town
    ('y58_curb', G(lambda: ST.ic_1958('kout')), 0.5, "1958: the pink window at the kerb, Benny's small footprints"),
    ('y58_lane', G(lambda: ST.ic_1958('lane')), 0.5, '1958: the lane, old cars'),
    ('y58_mitten', G(lambda: ST.ic_1958('mitten')), 0.5, '1958: one red mitten at the kerb'),
    ('morning_kessler', G(lambda: ST.ic_morning('kporch')), 0.5, "morning: his walk shoveled, his chimney smoking"),
    ('morning_lane', G(lambda: ST.ic_morning('house')), 0.5, 'morning: Birch Lane, sunrise'),
    ('town', G(lambda: ST.ic_town('town')), 0.5, 'across town: the house with no chimney smoke, the truck slowing'),
]
ICE += [
    ('liv_wide', G(lambda: ST.ic_living('wide', lamp=1.0, ceil=0.6, curtains=1.0, truck=None)), 0.5, 'the living room, warm, before the truck (curtains open)'),
    ('liv_wide_dark', G(lambda: ST.ic_living('wide', blackout=True, frost=0.8, blanket=True)), 0.5, 'after the power dies: frost inside, pink through the curtains, the nest'),
    ('liv_couch', G(lambda: ST.ic_living('couch', lamp=0.8)), 0.5, 'the couch face-on, the crack behind'),
    ('liv_couch3q', G(lambda: ST.ic_living('couch3q', lamp=0.8)), 0.5, 'the couch at 3/4'),
    ('liv_tv', G(lambda: ST.ic_living('tv', blackout=True, skull=1.0)), 0.5, 'the black TV: us, the crack, the skull'),
    ('liv_window', G(lambda: ST.ic_living('window', blackout=True)), 0.5, 'the curtains and the crack, pink behind'),
    ('liv_window_beacon', G(lambda: ST.ic_living('window', blackout=True, curtains=0.0, beacon=1.0, frost=1.0)), 0.5, 'curtains shut, the orange beacon sweeps, frost'),
    ('liv_radio', G(lambda: ST.ic_living('radio', lamp=0.8)), 0.5, "Dad's radio on the side table"),
    ('liv_opening', G(lambda: ST.ic_living('opening', lamp=0.8, hall=0.6)), 0.5, 'to the opening and the hall'),
    ('liv_shards', G(lambda: ST.ic_living('couch3q', blackout=True, cone='floor', phone=0.6, phone_at=(3.0, 1.0, 2.4))), 0.5, 'the shards on the floor, the power dead'),
    ('hall_door', G(lambda: ST.ic_hall('door', hall=1.0)), 0.5, 'down the hall to the front door'),
    ('hall_door_dark', G(lambda: ST.ic_hall('door', blackout=True)), 0.5, 'dark hall: the door glass lit pink by his window'),
    ('hall_doorclose', G(lambda: ST.ic_hall('doorclose', blackout=True, face=(lambda t: (1.0, 0.55)), knob_frost=1.0)), 0.5, 'the door: the face up the frost, the knob frosting'),
    ('hall_back', G(lambda: ST.ic_hall('back', hall=1.0)), 0.5, 'down the hall: the hatch'),
    ('hall_hatch', G(lambda: ST.ic_hall('hatch', blackout=True, hatch=1.0, phone=1.0, phone_at=(-2.1, 1.2, 4.6))), 0.5, 'the hatch dropped open'),
    ('hall_hatch_shut', G(lambda: ST.ic_hall('hatch', blackout=True, hatch=0.0, phone=1.0, phone_at=(-2.1, 1.2, 4.6))), 0.5, 'the hatch closed (the clicking above)'),
    ('hall_bathdoor', G(lambda: ST.ic_hall('bathdoor', blackout=True, phone=1.0, phone_at=(-2.3, 1.1, 2.4))), 0.5, 'the bathroom door from the hall'),
    ('kit_window', G(lambda: ST.ic_kitchen('window', kitchen_light=1.0, cone='sill')), 0.5, 'the kitchen window, the cone on the outside sill'),
    ('kit_window_open', G(lambda: ST.ic_kitchen('window', sash=0.12)), 0.5, 'the window open a crack, the stool under it'),
    ('kit_wide', G(lambda: ST.ic_kitchen('wide', kitchen_light=1.0)), 0.5, "the kitchen wide (Mom's photo on the fridge)"),
    ('bath_door', G(lambda: ST.ic_bath('door', phone=1.0, phone_at=(-0.3, 0.8, 1.6))), 0.5, 'the bathroom door, towels in the gap'),
    ('bath_gap', G(lambda: ST.ic_bath('gap', towels='jammed', phone=1.0, phone_at=(-0.6, 0.5, 1.4))), 0.5, 'low at the gap'),
    ('bath_window', G(lambda: ST.ic_bath('window', wipe=1.0, phone=0.6, phone_at=(-0.5, 1.2, 1.2))), 0.5, 'the small window wiped clear'),
    ('bath_wide', G(lambda: ST.ic_bath('wide', phone=1.0, phone_at=(-0.4, 0.9, 1.7))), 0.5, 'the bathroom wide'),
]
ICE += [('ins_' + _n, II(_n), 0.5, ST.IC_INSERTS[_n][2]) for _n in sorted(ST.IC_INSERTS) if _n not in ('rule', 'card', 'outro')]
ICE += [('ins_rule%d' % n, II('rule', prop_kw=dict(n=n)), 0.5, 'rule card %d (legible)' % n) for n in range(1, 9)]
ICE += [('ins_card_1102', II('card', prop_kw=dict(time_='Eleven-oh-two.', temp='Minus thirty-three.')), 0.5, 'card: Eleven-oh-two. Minus thirty-three.'),
        ('ins_card_open', II('card', prop_kw=dict(time_='Larkfield.', temp='Minus thirty-one.', sub='Sunrise: seven fifty-one.')), 0.5, 'card: Larkfield. Minus thirty-one. Sunrise 7:51'),
        ('ins_card_210', II('card', prop_kw=dict(time_='Two-ten.', temp='Minus thirty-eight.')), 0.5, 'card: Two-ten. Minus thirty-eight.'),
        ('ins_card_305', II('card', prop_kw=dict(time_='Three-oh-five.', temp=None)), 0.5, 'card: Three-oh-five.'),
        ('ins_rules_8', II('rules', prop_kw=dict(eighth=True)), 0.5, 'the rules with rule 8 added'),
        ('ins_rules_hl1', II('rules', prop_kw=dict(hl=1, door='kessler')), 0.5, "the rules on Kessler's door, rule 1 lit")]
ICE += [('ins_outro%d' % n, II('outro', prop_kw=dict(n=n)), 0.5, 'outro card %d' % n) for n in range(5)]
ICE += [('ins_mittens_lina', II('mittens', prop_kw=dict(lina=True)), 0.5, "the bunting with Lina's mitten"),
        ('ins_mittens_drop', II('mittens', prop_kw=dict(lina=True, drop=0.5)), 0.5, "hers drops; the red one stays"),
        ('ins_shatter0', II('shatter', prop_kw=dict(brk=0.0)), 0.5, 'the cone about to hit'),
        ('ins_radio_talk', II('radio', prop_kw=dict(talk=1.0, static=0.6)), 0.5, 'the radio: a voice (LED), static')]

STAGE_ICE = [
    ('liv_couch', lambda: ST.ic_living('couch3q', lamp=0.8), [('adam', 'couch_mid', {}), ('lina', 'couch_right', dict(seed=2))], 'Adam and Lina on the couch'),
    ('ext_truck', lambda: ST.ic_street('truck', truck_open=1.0), [('shiver', 'truck_vendor', {}), ('lina', 'truck_curb', dict(seed=2))], 'him at the window, Lina at the kerb'),
    ('ext_kout', lambda: ST.ic_street('kout', truck='B', kdoor_open=True), [('kessler', 'kwalk_mid', {}), ('shiver', 'truck_vendor', dict(seed=2))], 'Kessler halfway to the window (B)'),
    ('hall_door', lambda: ST.ic_hall('door', blackout=True), [('adam', 'door_in', {}), ('lina', 'hall_front', dict(seed=2))], 'at the door: the Mom beat'),
]
