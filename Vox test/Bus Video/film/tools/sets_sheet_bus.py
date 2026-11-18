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

STAGE_BUS = []
