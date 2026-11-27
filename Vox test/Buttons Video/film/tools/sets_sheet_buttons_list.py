# The Buttons film's variants for tools/sets_sheet_buttons.py (exec'd there: ST, G, II, math in scope).
# (name, builder, t, note): the best example of every set state and insert the script needs.
BUTTONS = [
    ('apt_wide_night', G(lambda: ST.bt_apt('wide', laptop=1.0, lamp=0.0, board='birthday')), 0.5, '2 a.m.: the kitchen dark, the laptop glow, the streetlight through the windows'),
    ('apt_wide_eve', G(lambda: ST.bt_apt('wide', tod='evening', lamp=1.0, ceil=1.0, dinner=True, laptop_on='closed')), 0.5, 'Thursday dinner: the lamp, Owen\'s favourite on the table'),
    ('apt_wide_day', G(lambda: ST.bt_apt('wide', tod='day', laptop=1.0, headset_table=False, carton=True, tablet=1.0)), 0.5, 'a day shift: the laptop, the tablet on the milk carton'),
    ('apt_living', G(lambda: ST.bt_apt('living', lamp=1.0, ceil=1.0, living=1.0, board='here', board_k=1.0)), 0.5, '11:58: the couch facing the front door, the lights on'),
    ('apt_table', G(lambda: ST.bt_apt('table', tod='evening', lamp=1.0, dinner=True, laptop_on='closed')), 0.5, "dinner: Mom's chair at the far end (the Blank sits there)"),
    ('apt_table_back', G(lambda: ST.bt_apt('table_back', laptop=1.0)), 0.5, "2 a.m. from behind Mom's chair: the laptop glow"),
    ('apt_fridge', G(lambda: ST.bt_apt('fridge', lamp=1.0, ceil=1.0, board='here', board_k=1.0, clock='12:00')), 0.5, 'midnight: the fridge, its board, the GAP beside it to the ceiling'),
    ('apt_board_all', G(lambda: ST.bt_apt('board', lamp=1.0, ceil=1.0, board='all', board_k=6.0)), 0.5, 'the board: everything written'),
    ('apt_micro', G(lambda: ST.bt_apt('micro', tod='evening', laptop=1.0, lamp=1.0)), 0.5, 'the black microwave door over his shoulder (reflection plate)'),
    ('apt_window', G(lambda: ST.bt_apt('window', jar='full')), 0.5, 'the kitchen window at night, the button jar on the sill'),
    ('apt_momdoor', G(lambda: ST.bt_apt('momdoor', laptop=1.0)), 0.5, "2 a.m.: Mom's bedroom door from Owen's seat"),
    ('apt_clock', G(lambda: ST.bt_apt('clock', clock='11:58')), 0.5, 'the oven clock: 11:58'),
    ('apt_door_day', G(lambda: ST.bt_apt('door', tod='day')), 0.5, 'the front door (Tuesday: the box outside it)'),
    ('apt_couch', G(lambda: ST.bt_apt('couch', lamp=1.0, ceil=1.0, living=1.0, board='here', board_k=1.0)), 0.5, '11:58: the couch from the front door, the kitchen behind'),
    ('owen_wide', G(lambda: ST.bt_owen('wide', tablet_bed=True, tablet=1.0)), 0.5, "Owen's room at night: the streetlight through the window, the tablet on the bed"),
    ('owen_wide_open', G(lambda: ST.bt_owen('wide', closet=100.0, coat='full', tablet=0.6, tablet_bed=True, ink=[0.1, 0.1, 1, 1, 1, 1, 1])), 0.5, '3 a.m.: the closet open, the coat full, the list (rules 1-2 pale)'),
    ('owen_window', G(lambda: ST.bt_owen('window', sash=0.4)), 0.5, 'the window seat, the streetlight right outside (sash up)'),
    ('owen_closet', G(lambda: ST.bt_owen('closet', closet=95.0, coat='sag', tablet=0.8)), 0.5, 'the closet open: the coat sagged empty'),
    ('owen_bed', G(lambda: ST.bt_owen('bed', tablet_bed=True, tablet=1.0)), 0.5, 'from the window corner to the bed and the door'),
    ('owen_sill_pov', G(lambda: ST.bt_owen('sill_pov')), 0.5, 'from his pillow to the window seat (the Blank sings there)'),
    ('owen_day', G(lambda: ST.bt_owen('wide', tod='day')), 0.5, "Owen's room by day"),
    ('ext_from_window', G(lambda: ST.bt_street('from_window')), 0.5, "POV out of Owen's window: streetlight, bus stop, Barlow's corner"),
    ('ext_lobby_pov', G(lambda: ST.bt_street('lobby_pov')), 0.5, 'POV down to the lobby door'),
    ('ext_lamp', G(lambda: ST.bt_street('lamp', win=dict(owen=0.6, living=0.5))), 0.5, 'across the street: the building, the streetlight, the window next to his'),
    ('ext_lamp_close', G(lambda: ST.bt_street('lamp_close', sweep=ST.bt_sweep(0.0))), 1.4, 'under the streetlight: headlights sweep'),
    ('ext_lobby', G(lambda: ST.bt_street('lobby')), 0.5, 'the lobby bay and its glass door at night'),
    ('ext_barlow', G(lambda: ST.bt_street('barlow', tod='day')), 0.5, "Monday: Barlow's window across the street"),
    ('ext_shopwin', G(lambda: ST.bt_street('shopwin', tod='day')), 0.5, 'the red coat with seven black buttons in the window'),
    ('lobby_door', G(lambda: ST.bt_lobby('door')), 0.5, 'inside the lobby: the glass door, the street beyond'),
    ('lobby_close', G(lambda: ST.bt_lobby('close')), 0.5, 'the glass door close from inside'),
    ('sch_wide', G(lambda: ST.bt_school('wide')), 0.5, 'the snowy pickup lane, the school, the silver car'),
    ('sch_curb', G(lambda: ST.bt_school('curb', rear_door=1.0)), 0.5, "the car's driver side: the OPEN window, the rear door swung open, the dent"),
    ('sch_window', G(lambda: ST.bt_school('window')), 0.5, 'close on the open driver window'),
    ('sch_dunn', G(lambda: ST.bt_school('dunn')), 0.5, "Mr. Dunn's crossing post"),
    ('sch_tracks', G(lambda: ST.bt_school('back', car=False)), 0.5, 'then, just tire tracks'),
    ('chat_fill', G(lambda: ST.bt_chat(ST.BT_CHAT['wish'] + ST.BT_CHAT['answer'] + ST.BT_CHAT['tell'], head=4.5, typing=1.0)), 0.5, 'the chat: the grey head filling in'),
    ('chat_buttons', G(lambda: ST.bt_chat(ST.BT_CHAT['tell'][2:] + ST.BT_CHAT['eyes'] + ST.BT_CHAT['ok'], head=7.0)), 0.5, 'the buttons clicked on'),
    ('chat_photo', G(lambda: ST.bt_chat(ST.BT_CHAT['view'] + ST.BT_CHAT['see'], head=7.0, name='The Blank')), 0.5, 'the photo sent; "I see you."'),
    ('chat_mom', G(lambda: ST.bt_chat(ST.BT_CHAT['mom_2am'], account='mom', typing=0.0, banner=('Mom', 'Come to the kitchen, baby.', 1.0))), 0.5, "2 a.m.: a message from Mom's account"),
    ('chat_dad', G(lambda: ST.bt_chat(ST.BT_CHAT['dad'], head=0.0, theme='now')), 0.5, "the son's tablet: the grey head, \"I don't know.\""),
    ('now_desk', G(lambda: ST.bt_now('desk', headset='desk', jar='empty')), 0.5, "now: the narrator's desk, the empty jar, the headset set down"),
    ('now_hall', G(lambda: ST.bt_now('hall')), 0.5, "now: down the hall to his son's door"),
    ('now_son', G(lambda: ST.bt_now('son', door=80.0, hall=0.8)), 0.5, "now: his son's room, the tablet, the window onto a streetlight"),
    ('now_window', G(lambda: ST.bt_now('window', tablet_bed='down', tablet=0.5)), 0.5, 'now: the window, the streetlight (someone waves under it)'),
    ('ins_list', II('brave_list', prop_kw=dict(ink=[0.12, 0.12, 1, 0.12, 0.12, 1, 1], hl=3)), 0.5, 'the Brave List after R5 (only rule three blue; 6-7 not yet)'),
    ('ins_list_words', II('brave_list', prop_kw=dict(words=(1, 6.5))), 0.5, 'rule one, word by word'),
    ('ins_rule3', II('brave_rule', prop_kw=dict(n=3, write=1.0)), 0.5, 'rule three big'),
    ('ins_board_bday', II('board', prop_kw=dict(state='birthday')), 0.5, 'FRI. O\'S BIRTHDAY'),
    ('ins_board_here', II('board', prop_kw=dict(state='here', k=1.0)), 0.5, "MOM IT'S OWEN I'M HERE"),
    ('ins_board_all', II('board', prop_kw=dict(state='all', k=6.0)), 0.5, 'the list of everything'),
    ('ins_box', II('box', prop_kw=dict(state='closed')), 0.5, 'the box on the doormat'),
    ('ins_box_open', II('box', prop_kw=dict(state='open')), 0.5, 'the box open: the coat, the card'),
    ('ins_card', II('card'), 0.5, 'the card'),
    ('ins_coat_full', II('coat', prop_kw=dict(full=1.0)), 0.5, 'the coat full (3 a.m.)'),
    ('ins_coat_sag', II('coat', prop_kw=dict(full=0.0)), 0.5, 'the coat sagged empty'),
    ('ins_jar', II('jar', prop_kw=dict(state='full', bg='sill')), 0.5, 'the jar on the sill'),
    ('ins_jar_black', II('jar', prop_kw=dict(state='black', bg='sill')), 0.5, 'two black buttons in, lid on'),
    ('ins_jar_desk', II('jar', prop_kw=dict(state='empty', bg='desk')), 0.5, 'now: the jar on his desk, lid off, empty'),
    ('ins_music_box', II('music_box', prop_kw=dict(crank=0.8)), 0.5, 'the music box in the empty cardigan'),
    ('ins_lock', II('lock_screen'), 0.5, "Mom's lock screen"),
    ('ins_glasses', II('glasses'), 0.5, 'glasses with the laptop glare'),
    ('ins_glasses_circles', II('glasses', prop_kw=dict(circles=1.0)), 0.5, 'two black, shiny circles'),
    ('ins_clock', II('clock', prop_kw=dict(clock='11:58', blink=False)), 0.5, 'the oven clock'),
    ('ins_laptop_deliv', II('laptop', prop_kw=dict(state='delivered')), 0.5, 'It says delivered. On the mat.'),
    ('ins_laptop_msg', II('laptop', prop_kw=dict(state='msg', typed=0.7)), 0.5, "2 a.m.: Mom's account typing"),
    ('ins_photo', II('photo', prop_kw=dict(send=1.0)), 0.5, 'the photo out of his window: Send'),
]


def _refl_test():
    """A geometry check for the microwave mirror: dots where Owen's head (stool), Mom's head (her chair) and the Blank's
    head (behind the stool) reflect."""
    def refl(pen, t, clip):
        v = ST.cam('bt_apt_micro')
        for (x, Y, y, c) in ((6.6, ST.BT_UP + 1.32, 2.9, '#5d7fb0'), (3.66, ST.BT_UP + 1.22, 2.35, '#d9caa9'), (5.95, ST.BT_UP + 1.72, 2.78, '#9ca2aa')):
            sx, sy, s, d = ST.bt_mirror(v, x, Y, y)
            pen.fill(ST.oval(sx, sy, 0.1 * s, 0.12 * s), c, 230)
    return refl


BUTTONS += [('apt_micro_refl', G(lambda: ST.bt_apt('micro', tod='evening', laptop=1.0, lamp=1.0, refl=_refl_test())), 0.5, 'mirror check: Owen (blue), the Blank (grey), Mom (oatmeal) in the glass')]
