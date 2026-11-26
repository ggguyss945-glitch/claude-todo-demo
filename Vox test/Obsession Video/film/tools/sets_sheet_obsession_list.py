# The Obsession film's variants for tools/sets_sheet_obsession.py (exec'd there: ST, G, II, math in scope).
# (name, builder, t, note): the best example of every set state and insert the script needs.
OBSESSION = [
    ('front_down_street', G(lambda: ST.om_front('street', track='street')), 0.5, 'Wed R1: ONLY ME under the streetlight, from his window'),
    ('front_down_half', G(lambda: ST.om_front('wide', track='half')), 0.5, 'Thu: halfway up the path'),
    ('front_down_foot', G(lambda: ST.om_front('down', track='foot', porch=0.0)), 0.5, 'Thu 2 a.m.: the foot of the step'),
    ('front_down_step', G(lambda: ST.om_front('down', track='step')), 0.5, 'Fri: on the step, an empty line under it'),
    ('front_down_door', G(lambda: ST.om_front('down', track='door', win={'adam': 1.0})), 0.5, 'Sat dinner: right against the green door'),
    ('front_down_mat', G(lambda: ST.om_front('down', track='mat', porch=1.0)), 0.5, 'Sat midnight: the doormat, the porch light on'),
    ('front_dawn', G(lambda: ST.om_front('step', tod='dawn', print=True, bucket=True)), 0.5, 'Thu dawn: wet clean path, bucket, the sneaker print pointing in'),
    ('front_dawn_wide', G(lambda: ST.om_front('wide', tod='dawn', track='half', track_wet=1.0, bucket=True)), 0.5, 'dawn: the washed ghost of ONLY ME'),
    ('danny_door', G(lambda: ST.om_front('down', house='danny', track='foot', win={'up': 1.0}, mom=True)), 0.5, "the cold open: Danny's BLUE door from his window"),
    ('danny_facade', G(lambda: ST.om_front('facade', house='danny', track='foot', win={'up': 1.0}, mom=True)), 0.5, "Danny's mom's silhouette at the next window"),
    ('room_wide', G(lambda: ST.om_room('wide', track='street')), 0.5, "Adam's room at night: the window, the desk, the door"),
    ('room_window', G(lambda: ST.om_room('window', track='street')), 0.5, 'at his window looking down'),
    ('room_door_strip', G(lambda: ST.om_room('door', strip=1.0, shadow=0.4)), 0.5, '2 a.m.: the light strip under the door, Mom\'s feet'),
    ('room_bed_phone', G(lambda: ST.om_room('bed', phone=1.0)), 0.5, 'his phone lighting the bed'),
    ('room_desk', G(lambda: ST.om_room('desk', lamp=1.0, drawer=1.0, tod='day')), 0.5, 'the desk drawer open (day)'),
    ('hall_landing', G(lambda: ST.om_hall('landing', landing=0.0, hall=0.0, chalk=[dict(text='ONLY', x=0.8, y=0.5, h=0.3)], stub=True)), 0.5, 'R6 midnight: from the landing, O-N-L-Y on the floor, the stub'),
    ('hall_halfway_lit', G(lambda: ST.om_hall('halfway', landing=1.0, chalk=[dict(text='ONLY', x=0.8, y=0.5, h=0.3)], stub=True)), 0.5, 'thumbnail angle: halfway down, the landing light on'),
    ('hall_up', G(lambda: ST.om_hall('up', landing=1.0)), 0.5, 'Lina under the bare bulb'),
    ('hall_door', G(lambda: ST.om_hall('door', fdoor=80.0, hall=1.0, kitchen=1.0, porch=1.0)), 0.5, 'R7: the door open onto the doormat'),
    ('hall_kitchen', G(lambda: ST.om_hall('kitchen', kitchen=1.0, chalk=[dict(text='M', x=0.5, y=2.5, h=0.3, reader=(0.5, 0.2)), dict(text='E', x=0.5, y=3.3, h=0.3, reader=(0.5, 0.2))])), 0.5, 'R7: M... E... toward the kitchen'),
    ('kit_dinner', G(lambda: ST.om_kitchen('dinner', kitchen=1.0, dinner=True)), 0.5, 'Saturday dinner: the dark window behind Mom'),
    ('kit_wide', G(lambda: ST.om_kitchen('wide', kitchen=1.0)), 0.5, 'R7: the kitchen light already on, the bucket by the door'),
    ('kit_tiles', G(lambda: ST.om_kitchen('tiles', kitchen=1.0, chalk=[dict(text='ME', x=1.4, y=6.2, h=0.3)])), 0.5, 'the letters stop at her chair'),
]
STAGE_OBS = []
