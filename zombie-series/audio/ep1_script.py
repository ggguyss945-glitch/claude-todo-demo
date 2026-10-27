# Episode 1 · The Night Shift (Day 0-7). The cold open (0:00-1:07) is the approved 60 s test; this file
# holds everything after its title card.
#
# Items play in order. Voiced items: N (narrator), DALE (radio voice), HERO (you, whispering), PA (store
# speakers). Positional args alternate phrase text and the pause after it, e.g.
#   N('A10', "Here's what you know.", 0.3, "They follow sound.")
# BEAT holds a silent stretch (POV scenes, stingers) for `dur` seconds.
# Keyword args: gap (silence after the item), rate (words/s inside a phrase), level (dB),
#   shot=(template, params) cuts to a new shot at the item start; shots=[(offset, template, params), ...]
#   cuts inside the item (offset in seconds, or '@word' for that word's start);
#   sfx=[(offset, name, params)], music=(cue, params) starts a score cue, amb=bed name, caps=[(t0, t1, text)]
#   for sound captions inside BEATs.
SAY = {'aisle': 'ile', 'night shift': 'nightshift', 'Aisle': 'Ile', 'Two-oh-three': 'Two-o-three'}   # spellings the voice pronounces right

ITEMS = []
def _voiced(who, id_, args, kw):
    phrases, i = [], 0
    while i < len(args):
        txt = args[i]; pause = args[i + 1] if i + 1 < len(args) and isinstance(args[i + 1], (int, float)) else 0.32
        phrases.append([txt, pause]); i += 2 if i + 1 < len(args) and isinstance(args[i + 1], (int, float)) else 1
    d = dict(id=id_, who=who, phrases=phrases, rate=kw.pop('rate', dict(N=2.9, DALE=2.7, HERO=2.3, PA=3.0)[who]),
             level=kw.pop('level', 0), gap=kw.pop('gap', 0.45))
    d.update(kw); ITEMS.append(d)
def N(id_, *a, **kw): _voiced('N', id_, a, kw)
def DALE(id_, *a, **kw): _voiced('DALE', id_, a, kw)
def HERO(id_, *a, **kw): _voiced('HERO', id_, a, kw)
def PA(id_, *a, **kw): _voiced('PA', id_, a, kw)
def BEAT(id_, dur, **kw): ITEMS.append(dict(id=id_, who='BEAT', dur=dur, gap=kw.pop('gap', 0.0), **kw))

H = lambda day, time, noise=1, place='FRESHWAY · AISLE 7': dict(day=day, time=time, noise=noise, place=place)

# ======================= PROMISE (after the title) =======================
N('P1', "This is your first week inside Freshway.", gap=0.5, music=('dawn', {}), amb='lot_dawn',
  shot=('lot', dict(mode='dawn', push=[1.0, 1.05])))
N('P2', "You'll make four rules.", 0.35, "You'll learn how they hunt.", shot=('card', dict(kind='promise_rules')))
N('P3', "And you'll find out you're not alone in this store.", gap=0.6, amb='store_night',
  shot=('prop', dict(item='clock', mode='still')))
N('P4', "You'll survive it.", 0.3, "Not because you're lucky.", shot=('hclose', dict(expr='determined', bg='aisle_dark')))
N('P5', "Because of one decision you make on day six.", gap=0.9, shot=('prop', dict(item='keys', mode='mystery')),
  sfx=[('$', 'keys_jingle', {})])

# ======================= ACT 1 · NIGHT 0 =======================
N('A1', "Back to two thirty-one.", 0.3, "The ringing comes from aisle twelve.", music=('dread', {}), amb='store_night',
  shot=('aisle', dict(mode='night', clock12=True, zombies='four_turn', hero=None, hud=H(0, '2:31 AM', 4, 'FRESHWAY · AISLE 12'))),
  sfx=[(0, 'alarm_far', dict(until='A20', off=2.6))])
N('A2', "And every dead thing in this store turns toward it.", shot=('zclose', dict(who=['milk', 'darlene', 'mike'], look='turn')))
N('A3', "There are four of them in here with you.", shot=('aisle', dict(mode='night', zombies='four_line', hud=H(0, '2:31 AM', 4))))
N('A4', "Darlene from the register.", 0.3, "Mike, the night guard.", 0.3, "A lady who came in for milk at midnight.",
  shots=[(0, 'zname', dict(who='darlene', label='DARLENE · REGISTER 3')), ('@Mike', 'zname', dict(who='mike', label='MIKE · NIGHT SECURITY')),
         ('@lady', 'zname', dict(who='milk', label='CUSTOMER · 2% MILK'))])
N('A5', "And Gary.", gap=0.6, shot=('gary', dict(mode='stand', label=True)), sfx=[(0.1, 'pizz_sting', {})])
N('A6', "Three of them shuffle toward aisle twelve.", shot=('aisle', dict(mode='night', zombies='three_walk_away', hud=H(0, '2:32 AM', 4))))
N('A7', "Gary doesn't.", 0.35, "Gary walks to his office.", 0.25, "Like he does every night at two thirty.",
  shot=('gary', dict(mode='walk')))
N('A8', "He closes the door behind him.", 0.4, "Habit.", gap=0.7, shot=('office', dict(view='door_close')),
  sfx=[('@door', 'door_close', {})])
N('A9', "Problem one.", 0.3, "Three dead people.", 0.25, "One store.", 0.25, "And you.", gap=0.6, music=('pulse_soft', {}),
  shot=('card', dict(kind='problem', n=1, title='THREE OF THEM', sub='ARE INSIDE WITH YOU', icon='zombie')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('A10', "Here's what you know.", 0.3, "They follow sound.", 0.25, "They don't see.",
  shot=('hclose', dict(expr='worried', bg='stock_dark', look=0.2)))
N('A11', "And the stockroom has a walk-in freezer.", shot=('stock', dict(view='wide', freezer='closed', hud=H(0, '2:36 AM', 1, 'FRESHWAY · STOCKROOM'))))
N('A12', "Steel door.", 0.25, "Four inches of foam in the walls.", shot=('freezer', dict(view='diagram')))
N('A13', "Sound goes in.", 0.3, "Nothing comes out.", gap=0.6)
N('A14', "You don't have a weapon.", 0.3, "You have a phone.", shot=('hclose', dict(expr='neutral', bg='stock_dark', prop='phone')))
N('A15', "Thirty-one percent battery.", 0.25, "No signal.", 0.3, "But it still has an alarm.", shot=('phone', dict(ui='home')))
N('A16', "You set it for two fifty.", shot=('phone', dict(ui='alarm')), sfx=[('$-0.4', 'tap', {})])
N('A17', "You put it on the freezer floor and prop the door open with a box of frozen peas.",
  shot=('stock', dict(view='freezer_open', freezer='open', phone=True, peas=True, hero='place', hud=H(0, '2:41 AM', 1, 'FRESHWAY · STOCKROOM'))))
N('A18', "Then you climb.", shot=('stock', dict(view='wide', freezer='open', phone=True, peas=True, hero='climb', hud=H(0, '2:43 AM', 1, 'FRESHWAY · STOCKROOM'))))
N('A19', "These shelves are eight feet tall and rated for a thousand pounds.", 0.35, "You're fine.", gap=0.6,
  shot=('stock', dict(view='wide', freezer='open', phone=True, peas=True, hero='top', label='RATED 1,000 LB', hud=H(0, '2:44 AM', 1, 'FRESHWAY · STOCKROOM'))))
N('A20', "At two forty-eight, the clock in aisle twelve gives up.", shot=('prop', dict(item='clock', mode='ring_stop')))
N('A21', "And the store goes very quiet.", gap=0.4, music=('stop', {'fade': 1.5}), amb='silence',
  shot=('stock', dict(view='top_dark', freezer='open', hud=H(0, '2:48 AM', 0, 'FRESHWAY · STOCKROOM'))))

# POV 2: on top of the shelving, no narrator
BEAT('POV2a', 6.0, shot=('povshelf', dict(phase='wait')), amb='freezer_hum', caps=[(0.3, 2.6, 'silence'), (2.8, 5.8, 'your heartbeat')],
     sfx=[(2.8, 'heartbeat_run', dict(until='POV2g', off=0.6, bpm0=72, bpm1=112))])
BEAT('POV2b', 5.0, shot=('povshelf', dict(phase='ring')), caps=[(0.2, 4.8, 'your phone. inside the freezer.')],
     sfx=[(0.0, 'phone_ring', dict(until='POV2g', off=0.38))])
BEAT('POV2c', 7.0, shot=('povshelf', dict(phase='enter')), caps=[(0.4, 3.2, 'footsteps'), (3.4, 6.8, 'three sets of them')],
     sfx=[(0.3, 'steps_close', dict(dur=13.0, n=3))])
BEAT('POV2d', 6.0, shot=('povshelf', dict(phase='stop')), caps=[(0.2, 2.8, 'one of them stops'), (3.0, 5.8, 'right under you')],
     sfx=[(1.0, 'groan_close', {})])
BEAT('POV2e', 4.0, shot=('povshelf', dict(phase='pass')), caps=[(0.3, 3.8, 'it moves on')])
BEAT('POV2f', 4.5, shot=('povshelf', dict(phase='drop')), caps=[(1.0, 2.6, 'too loud'), (2.7, 4.4, 'the last one turns')],
     sfx=[(0.9, 'thud_land', {}), (2.6, 'groan_close', {})])
BEAT('POV2g', 2.6, gap=0.5, shot=('povshelf', dict(phase='slam')), caps=[(0.6, 2.5, 'the door')], sfx=[(0.35, 'freezer_slam', {})])

N('A22', "Three of them.", 0.3, "One freezer.", 0.3, "Minus eighteen degrees.", music=('relief', {}), amb='store_night',
  shot=('freezer', dict(view='window', temp='-18°C')))
N('A23', "Problem one, solved.", gap=0.5, shot=('card', dict(kind='problem', n=1, title='THREE OF THEM', sub='ARE INSIDE WITH YOU', icon='zombie', stamp='SOLVED')),
  sfx=[(0.2, 'stamp', {})])
N('A24', "You also just locked your only phone in a freezer with three dead people.", gap=0.5,
  shot=('hclose', dict(expr='neutral', bg='stock_dark', look=-0.4)))
N('A25', "So.", 0.4, "Mostly solved.", gap=0.6, sfx=[('$', 'pizz_sting', {})])
N('A26', "One more thing.", 0.3, "Every walk-in freezer has a safety release on the inside.", 0.3, "So nobody gets trapped.",
  shot=('card', dict(kind='fact', big='INSIDE', unit='RELEASE', note='WALK-IN FREEZERS OPEN FROM INSIDE', src='SAFETY CODE · ANTI-ENTRAPMENT', icon='release')))
N('A27', "You really hope they never figure out how it works.", gap=0.9, shot=('freezer', dict(view='window_face')),
  sfx=[(1.2, 'thump_metal', {})])

# Problem 2: the store opens itself at 7:00
N('F1', "Six forty-one in the morning.", 0.3, "You haven't slept.", music=('tick', {}), amb='store_dawn',
  shot=('hclose', dict(expr='worried', bg='aisle_dawn', mode='sit', hud=H(0, '6:41 AM', 0))))
N('F2', "And then you remember what happens at seven.", gap=0.5, shot=('prop', dict(item='wallclock', time='6:41')))
N('F3', "Freshway opens at seven.", 0.3, "Every day.", 0.2, "Automatically.", shot=('doors', dict(mode='calm', locked=True, hud=H(0, '6:42 AM', 1, 'FRESHWAY · FRONT'))))
N('F4', "The lights come on.", 0.25, "The music starts.", 0.25, "And the front doors unlock.",
  shot=('card', dict(kind='schedule')))
N('F5', "There are two hundred of them outside those doors.", shot=('doors', dict(mode='crowd', locked=True, hud=H(0, '6:42 AM', 1, 'FRESHWAY · FRONT'))))
N('F6', "Most of them are regulars.", gap=0.6, sfx=[('$', 'pizz_sting', {})])
N('F7', "Problem two.", 0.3, "The store opens in nineteen minutes.", gap=0.5,
  shot=('card', dict(kind='problem', n=2, title='THE STORE OPENS', sub='IN 19 MINUTES', icon='clock', countdown=True)), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('F8', "The schedule runs from one room.", 0.3, "The manager's office.", 0.4, "Gary's office.", gap=0.6,
  shot=('office', dict(view='door_out', time='6:44 AM')))
N('G1', "Gary is standing at his desk.", 0.3, "Facing the clock.", 0.3, "Waiting for his shift to end.", music=('stalk', {}), amb='office',
  shot=('office', dict(view='wide', gary='desk', hero='door', time='6:52 AM')))
N('G2', "The control panel is on the wall behind him.", shot=('office', dict(view='panel', state='OPEN', time='6:53 AM')))
N('G3', "To reach it, you have to pass within arm's reach of a dead man who can hear a sneeze through a wall.",
  shot=('office', dict(view='wide', gary='desk', hero='door', path=True, time='6:54 AM')))
N('G4', "Shoes off.", 0.3, "Socks only.", 0.3, "Heel, then toe.", shot=('office', dict(view='socks', time='6:56 AM')),
  sfx=[('@Heel', 'sock_step', {}), ('@toe', 'sock_step', {})])
BEAT('G5', 4.2, shot=('office', dict(view='wide', gary='desk', hero='sneak1', time='6:57 AM', noise=2)), caps=[(1.0, 3.8, 'the floor creaks')],
     sfx=[(1.0, 'creak', {}), (2.2, 'groan_close', dict(level=-28))])
N('G6', "Six fifty-eight.", gap=0.5, shot=('office', dict(view='wide', gary='desk', hero='sneak2', time='6:58 AM', noise=1)))
N('G7', "His keys hang from his belt.", 0.3, "Fourteen of them.", 0.35, "If they jingle, you're done.",
  shot=('office', dict(view='keys_belt', time='6:58 AM')))
BEAT('G8', 3.0, shot=('office', dict(view='wide', gary='desk', hero='panel', time='6:59 AM', noise=1)), caps=[(0.5, 2.8, 'six fifty-nine')])
N('G9', "The switch says open.", 0.3, "You push it to closed.", gap=0.4, shot=('office', dict(view='switch', state='flip', time='6:59 AM')),
  sfx=[('$-0.2', 'big_switch', {})])
N('G10', "The doors stay locked.", 0.3, "You did it.", gap=0.6, music=('relief', {}), shot=('doors', dict(mode='crowd', locked=True, hud=H(0, '6:59 AM', 0, 'FRESHWAY · FRONT'))))
N('G11', "What you don't know is that the music runs on its own timer.", gap=0.5, music=('stop', {'fade': 0.6}),
  shot=('office', dict(view='speaker', time='6:59 AM')))
PA('G12', "Good morning, Freshway shoppers!", 0.25, "We're open!", gap=0.4, rate=3.2, music=('jingle', {}),
   shot=('office', dict(view='blast', time='7:00 AM', noise=5)), sfx=[(0, 'pa_pop', {})])
N('G13', "Two hundred dead people hear the Freshway jingle.", 0.3, "At the same time.", music=('chaos', {}),
  shot=('doors', dict(mode='surge', locked=True, hud=H(0, '7:00 AM', 5, 'FRESHWAY · FRONT'))), sfx=[(0.2, 'crowd_surge', dict(dur=7.0)), ('$', 'boom', {})])
N('G14', "You find the speaker cable in four seconds.", 0.25, "It feels like forty.", shot=('office', dict(view='cable', time='7:00 AM', noise=5)))
BEAT('G15', 2.2, music=('stop', {'fade': 0.02}), shot=('office', dict(view='cable_pulled', time='7:00 AM', noise=2)), caps=[(0.3, 2.1, 'silence')],
     sfx=[(0.0, 'cable_rip', {}), (0.05, 'jingle_cut', {})])
N('G16', "The doors hold.", gap=0.6, amb='store_day', shot=('doors', dict(mode='crowd', locked=True, hud=H(0, '7:01 AM', 1, 'FRESHWAY · FRONT'))),
  sfx=[(0.5, 'metal_rattle', {})])
N('G17', "Rule two.", 0.3, "Music is a dinner bell.", gap=0.7, music=('rule', {}),
  shot=('card', dict(kind='rule', n=2, lines=['MUSIC IS A', 'DINNER BELL.'], icon='note')), sfx=[(0, 'whoosh', {}), (0.12, 'slam', {})])
N('G18', "On your way out, you take Gary's keys off his belt.", 0.3, "Very slowly.", music=('humor', {}),
  shot=('office', dict(view='keys_take', time='7:03 AM')), sfx=[('$', 'keys_jingle', dict(level=-30))])
N('G19', "And you lock him in his own office.", shot=('office', dict(view='lockout', time='7:04 AM')), sfx=[('$-0.5', 'lock_click', {})])
N('G20', "In three years, it's the first time you've seen him stay past noon.", gap=1.0,
  shot=('gary', dict(mode='window')), sfx=[('$', 'pizz_sting', {})])

# ======================= ACT 2 · DAYS 1-5 =======================
BEAT('D1card', 2.4, shot=('card', dict(kind='day', n=1, title='THE BLUEPRINT')), music=('day', {}), amb='store_day', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('B1', "Day one.", 0.3, "You do something Gary never did.", 0.3, "You read the building manual.", music=('think', {}),
  shot=('hclose', dict(expr='neutral', bg='aisle_day', prop='binder', hud=H(1, '9:10 AM', 0))))
N('B2', "Freshway is thirty thousand square feet.", 0.25, "Fourteen rows of shelves.", shot=('map', dict(mode='blueprint', reveal='aisles')))
N('B3', "One front entrance.", 0.2, "One loading dock.", 0.2, "One fire exit.", 0.3, "And a ladder to the roof.",
  shot=('map', dict(mode='blueprint', reveal='exits')))
N('B4', "The front has steel shutters.", 0.25, "The dock has a roll-up door.", 0.25, "The fire exit has a magnetic lock.",
  shot=('map', dict(mode='blueprint', reveal='doors')))
N('B5', "That's the one that worries you.", gap=0.5, shot=('map', dict(mode='blueprint', reveal='firezoom')))
N('B6', "Magnetic locks are fail-safe.", 0.3, "If the power goes out, they open.", 0.3, "So nobody gets trapped in a fire.",
  shot=('card', dict(kind='fact', big='OFF', unit='= UNLOCKED', note='MAGNETIC LOCKS RELEASE WHEN POWER IS CUT', src='FIRE CODE · FAIL-SAFE HARDWARE', icon='magnet')))
N('B7', "Great for fires.", 0.35, "Terrible for this.", gap=0.6, shot=('exitdoor', dict(stage='bare', outside=True)))
N('B8', "At the security desk, you find a charging dock for the store radios.", shot=('dock', dict(mode='wide', hud=H(1, '11:20 AM', 0, 'FRESHWAY · SECURITY'))))
N('B9', "Two slots.", 0.4, "One radio.", gap=0.5, shot=('dock', dict(mode='close')))
N('B10', "You figure the night guard took the other one home.", gap=0.8, shot=('dock', dict(mode='take')))
N('B11', "Here's the thing about the power.", 0.3, "It's still on.",
  shot=('aisle', dict(mode='day', hero=dict(x=760, pose='stand', expr='neutral', look=-0.2), lights=True, hud=H(1, '11:40 AM', 0))))
N('B12', "Somewhere, a power plant is running with nobody in it.", shot=('skyline', dict(mode='day')))
N('B13', "Without people to balance it, a power grid doesn't last long.", 0.35, "Days, maybe.",
  shot=('card', dict(kind='fact', big='DAYS', unit='NOT WEEKS', note='AN UNTENDED POWER GRID FAILS FAST', src='GRID OPERATORS BALANCE LOAD 24/7', icon='bolt')))
N('B14', "When it goes, three things happen.")
N('B15', "The exit signs switch to batteries.", 0.25, "Ninety minutes of light.", 0.25, "That's the building code.",
  shot=('card', dict(kind='fact', big='90', unit='MIN', note='EMERGENCY LIGHTS ON BATTERY', src='LIFE SAFETY CODE · NFPA 101', icon='exit')))
N('B16', "The freezer starts warming.", 0.25, "A closed freezer stays frozen for about two days.",
  shot=('card', dict(kind='fact', big='48', unit='HRS', note='A FULL, CLOSED FREEZER STAYS FROZEN', src='USDA FOOD SAFETY', icon='snow')))
N('B17', "And the fire exit unlocks.", gap=0.5, shot=('exitdoor', dict(stage='bare', unlockfx=True)))
N('B18', "Problem three.", 0.3, "The back door.", gap=0.6,
  shot=('card', dict(kind='problem', n=3, title='THE BACK DOOR', sub='UNLOCKS WHEN THE POWER DIES', icon='door')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('B19', "So you build a wall.", music=('build', {}), shot=('exitdoor', dict(stage='bare', hero='carry')))
N('B20', "Forty bags of dog food.", 0.3, "Six pallets of bottled water.", 0.3, "A display of discounted patio chairs.",
  shots=[(0, 'montage', dict(what='dogfood')), ('@Six', 'montage', dict(what='water')), ('@display', 'montage', dict(what='chairs'))])
N('B21', "It takes eleven hours.", 0.35, "It's the best thing you've ever built.", gap=0.5,
  shot=('exitdoor', dict(stage='done', hero='proud', hud=H(1, '10:52 PM', 0, 'FRESHWAY · FIRE EXIT'))))
N('B22', "Water is no longer the problem.", 0.35, "Most of it is holding a door shut.", gap=0.9,
  shot=('card', dict(kind='supplies', day=1, rows=[('Food', '9,000 cans', ''), ('Water', '1,238 gal', '1,200 IN THE WALL'), ('Batteries', '2', '')])))

BEAT('D2card', 2.4, shot=('card', dict(kind='day', n=2, title='THE ROOF')), music=('day', {}), amb='roof', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('C1', "Day two.", 0.3, "Sunset.", 0.25, "You climb to the roof for the first time.",
  shot=('roof', dict(time='sunset', hero='hatch', hud=H(2, '7:48 PM', 1, 'FRESHWAY · ROOF'))))
N('C2', "And you count them.", music=('dread', {}), shot=('roof', dict(time='sunset', hero='edge', hud=H(2, '7:49 PM', 1, 'FRESHWAY · ROOF'))))
N('C3', "Two hundred and twelve.", 0.35, "Standing in the parking lot.", 0.25, "Facing the front doors.",
  shot=('lot', dict(mode='count', time='sunset', count=212)))
N('C4', "They don't sit.", 0.25, "They don't sleep.", 0.3, "They wait for the store to open.",
  shot=('zclose', dict(who=['jogger', 'park', 'nurse'], bg='lot_sunset', look='still')))
N('C5', "Across the street is Brookfield Mall.", 0.25, "Four floors.", 0.25, "Every window dark.", shot=('mall', dict(time='sunset', light='on', zoom=0)))
N('C6', "Except one.", 0.3, "Top floor.", 0.3, "A light.", gap=0.5, shot=('mall', dict(time='sunset', light='on', zoom=1)))
N('C7', "Someone over there is alive.", gap=0.9, music=('hope', {}), shot=('hclose', dict(expr='smile', bg='roof_sunset', warm=True)))

BEAT('D3card', 2.4, shot=('card', dict(kind='day', n=3, title='THE RADIO')), music=('stop', {'fade': 0.8}), amb='store_night', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('D1', "Day three.", 0.3, "Eleven forty at night.", shot=('camp', dict(time='night', hero='sit', hud=H(3, '11:40 PM', 0, 'FRESHWAY · AISLE 9'))))
N('D2', "The radio on your belt clicks.", gap=0.4, shot=('radio', dict(mode='belt')), sfx=[('$-0.2', 'radio_click', {})])
DALE('D3', "Freshway.", 0.4, "Anyone in Freshway.", 0.35, "Come back.", gap=0.5, music=('radio', {}), shot=('radio', dict(mode='talk')))
N('D4', "A man's voice.", 0.25, "Calm.", 0.25, "Tired.", shot=('hclose', dict(expr='surprised', bg='camp', prop='radio')))
DALE('D5', "This is Dale.", 0.3, "Mall security, across the street.", 0.3, "I saw your flashlight on the roof.", shot=('radio', dict(mode='talk', who='dale')))
N('D6', "You haven't heard a living voice in three days.", gap=0.6, shot=('hclose', dict(expr='worried', bg='camp', prop='radio', look=-0.2)))
HERO('D7', "I'm here.", gap=0.5, shot=('hclose', dict(expr='whisper', bg='camp', prop='radio_mouth')))
DALE('D8', "Good.", 0.35, "Keep it quiet.", 0.3, "They come to voices.", shot=('radio', dict(mode='talk', who='dale')))
DALE('D9', "How many of you are there?", gap=0.6)
HERO('D10', "Just me.", gap=0.8, shot=('hclose', dict(expr='whisper', bg='camp', prop='radio_mouth')))
DALE('D11', "Just you.", 0.7, "Okay.", gap=0.8, shot=('radio', dict(mode='talk', who='dale')), sfx=[('$', 'low_sting', {})])
N('D12', "Dale talks for an hour.", 0.3, "He knows things.", shot=('camp', dict(time='night', hero='radio', hud=H(3, '12:31 AM', 0, 'FRESHWAY · AISLE 9'))))
N('D13', "He knows they don't see.", 0.25, "He knows the front lot is full.")
DALE('D14', "And that alarm at two thirty-one.", 0.35, "You heard that too, right?", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('D15', "You never mentioned the alarm.", gap=0.6, shot=('hclose', dict(expr='worried', bg='camp', prop='radio', look=0.3)), sfx=[(0.1, 'low_sting', {})])
N('D16', "You figure the sound carries across the street.", gap=0.9, shot=('roof', dict(time='night', hero=None, mall=True, hud=None)))

BEAT('D4card', 2.4, shot=('card', dict(kind='day', n=4, title='LIGHTS OUT')), music=('day', {}), amb='store_day', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('E1', "Day four.", 0.3, "Three fifteen in the afternoon.", shot=('aisle', dict(mode='day', lights=True, hero=dict(x=980, pose='stand', expr='neutral', look=0.3), hud=H(4, '3:15 PM', 0))))
N('E2', "The fridges stop humming.", gap=0.6, music=('stop', {'fade': 0.4}), shot=('prop', dict(item='fridge')), sfx=[('$-0.4', 'hum_stop', {})])
N('E3', "The lights go out.", 0.25, "All of them.", 0.25, "At once.", gap=0.4, amb='silence',
  shots=[(0, 'aisle', dict(mode='day', lights=True, blackout='@out', hero=dict(x=980, pose='scared', expr='scared'), hud=H(4, '3:16 PM', 0)))],
  sfx=[('@out', 'power_down', {})])
N('E4', "The exit signs blink to battery.", 0.3, "Ninety minutes.", music=('dread', {}), amb='store_dark',
  shot=('prop', dict(item='exit_sign', timer=True)))
N('E5', "And at the back of the store...", gap=0.2, shot=('exitdoor', dict(stage='done', dark=True)))
BEAT('E6', 1.4, shot=('exitdoor', dict(stage='done', dark=True, clunk=True)), sfx=[(0.1, 'maglock_clunk', {})])
N('E7', "...the fire exit unlocks.", gap=0.5)
N('E8', "Fourteen of them are on the loading dock.", 0.3, "They heard it.", music=('chaos', {}),
  shot=('dockout', dict(mode='turn')))
BEAT('E9', 3.0, shot=('exitdoor', dict(stage='done', dark=True, push=True)), caps=[], sfx=[(0.3, 'door_bang', {}), (1.3, 'door_bang', {}), (2.2, 'bags_slide', {})])
N('E10', "Your wall moves an inch.", 0.35, "Then another.", shot=('exitdoor', dict(stage='done', dark=True, push=True, slide=True)), sfx=[('@another', 'bags_slide', {})])
N('E11', "Dog food was a mistake.", gap=0.5, sfx=[('$', 'pizz_sting', {})])
N('E12', "You need them away from that door.", 0.3, "And you need something louder than a door.",
  shot=('hclose', dict(expr='determined', bg='dark', flashlight=True)))
N('E13', "One shopping cart.", 0.25, "Forty cans of soup.", 0.25, "A twenty-foot drop.", music=('action', {}), amb='roof',
  shots=[(0, 'montage', dict(what='cart')), ('@twenty-foot', 'roof', dict(time='day', hero='cart', hud=H(4, '3:31 PM', 2, 'FRESHWAY · ROOF')))])
N('E14', "You push it off the far side of the roof.", gap=0.1, shot=('cart', dict(phase='push')))
BEAT('E15', 2.4, shot=('cart', dict(phase='crash')), sfx=[(0.55, 'crash', {})])
N('E16', "Every dead thing in the lot turns toward the noise.", 0.3, "Even the ones at your door.", music=('relief', {}),
  shot=('dockout', dict(mode='leave')))
N('E17', "It's the most fun you've had all week.", gap=0.5, shot=('hclose', dict(expr='smile', bg='roof_day')), sfx=[('$', 'pizz_sting', {})])
N('E18', "What would you have thrown?", 0.3, "Tell me in the comments.", gap=0.9, shot=('card', dict(kind='comment')))

BEAT('D5card', 2.4, shot=('card', dict(kind='day', n=5, title='ROUTINE')), music=('warm', {}), amb='store_dark', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('H1', "Day five.", 0.3, "You have a routine now.", shot=('camp', dict(time='morning', hero='wake', hud=H(5, '6:55 AM', 0, 'FRESHWAY · AISLE 9'))))
N('H2', "You sleep in a two-person tent in aisle nine.", 0.3, "Camping and outdoors.", shot=('camp', dict(time='morning', hero='tent', sign=True)))
N('H3', "Cold peaches for breakfast.", 0.3, "Every day.", shot=('hclose', dict(expr='neutral', bg='camp', prop='peaches', warm=True)))
N('H4', "At seven sharp, Gary bangs on his office door.", shot=('gary', dict(mode='bang')), sfx=[('@bangs', 'door_bang_soft', {}), ('$', 'door_bang_soft', {})])
N('H5', "Gary has never been late a day in his life.", 0.4, "Or after it.", gap=0.8, sfx=[('$', 'pizz_sting', {})])
N('H6', "And at night, you talk to Dale.", shot=('camp', dict(time='night', hero='radio', hud=H(5, '10:20 PM', 0, 'FRESHWAY · AISLE 9'))))
DALE('H7', "Rate your day, Freshway.", 0.3, "One to ten.", gap=0.5, shot=('radio', dict(mode='talk', who='dale')))
HERO('H8', "Four.", gap=0.5, shot=('hclose', dict(expr='smile', bg='camp', prop='radio_mouth')))
DALE('H9', "Four's good.", 0.35, "Four's alive.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('H10', "He tells bad jokes.", 0.25, "He asks about you.", 0.3, "He asks what you've got.", shot=('camp', dict(time='night', hero='laugh')))
DALE('H11', "How much water?", 0.3, "How much food?", gap=0.5, shot=('radio', dict(mode='talk', who='dale')))
N('H12', "You tell him.", gap=0.4, shot=('card', dict(kind='supplies', day=5, rows=[('Food', '8,960 cans', ''), ('Water', '1,224 gal', ''), ('Batteries', '2', '')], told=True)))
DALE('H13', "And the freezer?", 0.35, "Still holding?", gap=0.7, music=('stop', {'fade': 0.15}), shot=('radio', dict(mode='talk', who='dale')))
N('H14', "You stop.", gap=0.6, shot=('hclose', dict(expr='worried', bg='camp', prop='radio')), sfx=[(0, 'low_sting', {})])
N('H15', "You never told Dale about the freezer.", gap=0.5, music=('dread', {}))
N('H16', "Maybe you did.", 0.3, "It's been a long week.", gap=0.8, shot=('camp', dict(time='night', hero='lie')))

N('I1', "That night, at two thirty-one...", gap=0.2, shot=('aisle', dict(mode='dark', clock12=True, hud=H(5, '2:31 AM', 0, 'FRESHWAY · AISLE 12'))))
BEAT('I2', 2.2, shot=('prop', dict(item='clock', mode='ring')), sfx=[(0.1, 'alarm_near', dict(until='D6card', off=0.0))])
N('I3', "...the alarm in aisle twelve starts to ring.", gap=0.5)
N('I4', "You took the batteries out of that clock on the first night.", shot=('prop', dict(item='batteries')))
N('I5', "They're still in your pocket.", gap=0.5)
N('I6', "Someone put new ones in.", gap=1.4, music=('sting_mystery', {}), shot=('prop', dict(item='clock', mode='ring_close')))

# ======================= ACT 3 · DAYS 6-7 =======================
BEAT('D6card', 2.4, shot=('card', dict(kind='day', n=6, title='THE PLAN')), music=('stop', {'fade': 1.0}), amb='store_dark', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('J1', "Day six.", 0.3, "Dale has an idea.", shot=('camp', dict(time='day', hero='radio', hud=H(6, '1:30 PM', 0, 'FRESHWAY · AISLE 9'))))
DALE('J2', "Come over to the mall.", 0.3, "We've got a generator.", 0.25, "Hot food.", 0.25, "Twelve people.", gap=0.5, music=('hope', {}), shot=('radio', dict(mode='talk', who='dale')))
N('J3', "Twelve people.", 0.25, "Hot food.", 0.25, "A door that locks.", gap=0.5, shot=('mall', dict(time='day', light='on', zoom=0.5, dream=True)))
DALE('J4', "But you can't cross that lot with two hundred of them in it.", gap=0.5, shot=('radio', dict(mode='talk', who='dale')))
N('J5', "So you make a plan.", 0.3, "Rule one is still the rule.", 0.25, "They follow sound.", music=('plan', {}),
  shot=('map', dict(mode='plan', reveal='lot')))
N('J6', "Aisle eleven has alarm clocks.", 0.25, "Six of them.", 0.25, "Four ninety-nine each.", shot=('prop', dict(item='clocks6')))
N('J7', "You set them one minute apart.", 0.25, "Two-oh-one to two-oh-six.", shot=('prop', dict(item='clocks6', set=True)))
N('J8', "You'll throw them from the roof to the far end of the lot.", 0.3, "One by one, they'll pull the crowd away.",
  shot=('map', dict(mode='plan', reveal='decoys')))
N('J9', "Eighty meters to the mall's side door.", 0.25, "Ninety seconds if you walk.", shot=('map', dict(mode='plan', reveal='route')))
N('J10', "You won't run.", 0.3, "Running is loud.", gap=0.5)
DALE('J11', "And don't bring anything.", 0.3, "We've got plenty.", 0.35, "Just come.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('J12', "So you pack light.", 0.3, "Water.", 0.2, "A flashlight.", 0.35, "And Gary's keys.",
  shot=('card', dict(kind='backpack', items=['WATER · 2 L', 'FLASHLIGHT · 2 AA', "GARY'S KEYS · 14"])))
N('J13', "You don't know why.", 0.3, "You just never told Dale about the keys.", gap=1.0, shot=('prop', dict(item='keys', mode='pocket')),
  sfx=[('$', 'keys_jingle', {})])

BEAT('D7card', 2.6, shot=('card', dict(kind='day', n=7, title='2:00 AM')), music=('night_op', {}), amb='roof_night', sfx=[(0, 'whoosh', {}), (0.2, 'tok', {})])
N('K1', "Day seven.", 0.3, "Two in the morning.", 0.3, "You're on the roof.", shot=('roof', dict(time='night', hero='backpack', hud=H(7, '1:58 AM', 0, 'FRESHWAY · ROOF'))))
N('K2', "You throw the clocks.", 0.3, "Six of them.", 0.3, "Into the dark.", gap=0.4, shot=('roof', dict(time='night', hero='throw', hud=H(7, '1:59 AM', 0, 'FRESHWAY · ROOF'))),
  sfx=[('@clocks', 'throw_whoosh', {}), ('@Six', 'throw_whoosh', {}), ('@dark', 'throw_whoosh', {})])
BEAT('K3', 2.4, shot=('lot', dict(mode='turn', time='night', decoys=1, hud=H(7, '2:01 AM', 0, 'FRESHWAY · ROOF'))), sfx=[(0.2, 'decoy_alarm', dict(k=1))])
N('K4', "Two-oh-one.", 0.45, "The crowd turns.", 0.3, "Slowly.", 0.3, "Like grass in the wind.")
BEAT('K5', 1.6, sfx=[(0.1, 'decoy_alarm', dict(k=2))])
N('K6', "Two-oh-two.", 0.35, "Two-oh-three.", 0.45, "The front lot empties toward the far corner.",
  shot=('lot', dict(mode='empty', time='night', decoys=3, hud=H(7, '2:03 AM', 0, 'FRESHWAY · ROOF'))), sfx=[('@Two-oh-three', 'decoy_alarm', dict(k=3))])
N('K7', "You climb down the back ladder.", gap=0.3, music=('stop', {'fade': 0.5}), shot=('roof', dict(time='night', hero='ladder', hud=None)),
  sfx=[('$', 'decoy_alarm', dict(k=4))])

# POV 3: across the lot
BEAT('POV3a', 5.5, shot=('povlot', dict(phase='ladder')), amb='lot_night', caps=[(0.3, 5.2, 'alarms in the distance')], sfx=[(0.5, 'ladder_steps', {})])
BEAT('POV3b', 6.0, shot=('povlot', dict(phase='walk')), caps=[(0.3, 2.8, 'your breathing'), (3.2, 5.8, 'glass under your shoe')],
     sfx=[(0.2, 'breath_run', dict(until='K8', off=0.0)), (3.2, 'glass_crunch', {}), (3.6, 'decoy_alarm', dict(k=5))])
DALE('POV3c', "Stop.", 0.4, "Don't move.", gap=0.3, level=-2, shot=('povlot', dict(phase='freeze')))
BEAT('POV3d', 7.0, shot=('povlot', dict(phase='pass')), caps=[(0.4, 3.0, 'footsteps'), (3.2, 6.8, 'right next to you')],
     sfx=[(0.4, 'steps_close', dict(dur=6.0, n=1)), (3.0, 'groan_close', {})])
BEAT('POV3e', 3.0, shot=('povlot', dict(phase='gone')), caps=[(0.3, 2.8, 'it moves on')], sfx=[(0.5, 'decoy_alarm', dict(k=6))])
DALE('POV3f', "Okay.", 0.4, "Keep coming.", gap=0.3, level=-2)
BEAT('POV3g', 3.2, shot=('povlot', dict(phase='mall')), caps=[(0.3, 3.0, 'eighty meters')])
N('K8', "Halfway across, Dale talks again.", music=('reveal', {}), shot=('hclose', dict(expr='worried', bg='lot_night', prop='radio')))
DALE('K9', "Don't stop now, kid.", gap=0.4, echo=True, shot=('radio', dict(mode='talk', who='dale', echo=True)))
N('K10', "And you hear it twice.", gap=0.5, shot=('hclose', dict(expr='surprised', bg='lot_night', prop='radio')))
N('K11', "Once in your radio.", 0.45, "And once, faint, from behind you.", shot=('card', dict(kind='twowaves')))
N('K12', "From the roof of Freshway.", gap=0.6, shot=('freshroof', dict(mode='figure')))
N('K13', "Dale was never at the mall.", gap=0.6, music=('twist', {}), shot=('hclose', dict(expr='scared', bg='lot_night', look=-0.6)))
N('K14', "That light in the window?", 0.35, "Nobody's turned it off in six days.", 0.35, "Because nobody's there.",
  shot=('mall', dict(time='night', light='on', zoom=1, empty=True)))
N('K15', "He's been in your store the whole week.", shot=('freshroof', dict(mode='figure_close')))
N('K16', "He knew about the alarm.", 0.3, "He knew about the freezer.", shots=[(0, 'prop', dict(item='clock', mode='still')), ('@freezer', 'freezer', dict(view='window'))])
N('K17', "He never wanted you at the mall.", 0.35, "He wanted you out of Freshway.", shot=('freshroof', dict(mode='figure')))
N('K18', "With nothing.", gap=0.3)
BEAT('K19', 1.6, shot=('freshroof', dict(mode='hatch')), caps=[(0.2, 1.5, 'the roof hatch')], sfx=[(0.25, 'hatch_clang', {})])
N('K20', "Every can.", 0.25, "Every gallon.", 0.35, "His now.", gap=0.8, shot=('hclose', dict(expr='determined', bg='lot_night')))

N('M1', "And the alarms are dying.", 0.3, "One by one.", music=('chase', {}), shot=('lot', dict(mode='dying', time='night', decoys=6, hud=H(7, '2:05 AM', 2, 'FRESHWAY · PARKING LOT'))))
N('M2', "Two-oh-six.", 0.35, "The last clock stops.", gap=0.4, sfx=[('$-0.3', 'decoy_stop', {})])
N('M3', "Two hundred of them start walking back.", shot=('lot', dict(mode='return', time='night', hud=H(7, '2:06 AM', 3, 'FRESHWAY · PARKING LOT'))),
  sfx=[(0, 'crowd_steps_far', dict(until='M11', off=0.0))])
N('M4', "Now you run.", gap=0.3, shot=('run', dict()), sfx=[(0, 'run_steps', dict(dur=6.0))])
N('M5', "Not to the roof.", 0.25, "Not to the dock.", 0.3, "To the staff door on the side of the building.", shot=('map', dict(mode='plan', reveal='staffdoor')))
N('M6', "Steel door.", 0.25, "Key lock.", 0.3, "And you have Gary's keys.", shot=('staffdoor', dict(mode='arrive', hud=H(7, '2:07 AM', 3, 'FRESHWAY · STAFF DOOR'))))
N('M7', "Fourteen keys.", 0.3, "No labels.", shot=('prop', dict(item='keys', mode='shake')), sfx=[(0, 'keys_jingle', {})])
N('M8', "Gary labeled every shelf in that store.", 0.3, "Not one key.", gap=0.4)
BEAT('M9', 6.0, shot=('staffdoor', dict(mode='keys', hud=H(7, '2:07 AM', 4, 'FRESHWAY · STAFF DOOR'))),
     caps=[(0.2, 1.8, 'first key'), (1.9, 3.5, 'second'), (3.6, 5.8, 'third')],
     sfx=[(0.3, 'key_try', {}), (2.0, 'key_try', {}), (3.7, 'key_try', {}), (1.0, 'groan_close', dict(level=-24)), (4.0, 'groan_close', dict(level=-20))])
N('M10', "The fourth one turns.", gap=0.3, shot=('staffdoor', dict(mode='turn')), sfx=[('$-0.3', 'lock_click', {})])
N('M11', "You're inside.", 0.3, "You lock it behind you.", gap=0.3, music=('stop', {'fade': 0.1}), amb='store_dark',
  shot=('staffdoor', dict(mode='inside')), sfx=[('@lock', 'lock_click', {}), ('$', 'door_bang', {})])
BEAT('M11b', 1.6, sfx=[(0.3, 'door_bang', {}), (1.0, 'door_bang', {})])
N('M12', "You survive this week.", 0.35, "Not because you were lucky.", 0.35, "Because you kept one thing to yourself.", gap=1.0,
  music=('resolve', {}), shot=('hclose', dict(expr='determined', bg='dark', look=0.1)))

N('N1', "Day seven.", 0.3, "Here's what you know.", shot=('card', dict(kind='rules', show=0)))
N('N2', "Rule one.", 0.3, "They hear.", 0.25, "They don't see.", shot=('card', dict(kind='rules', show=1)))
N('N3', "Rule two.", 0.3, "Music is a dinner bell.", shot=('card', dict(kind='rules', show=2)))
N('N4', "Rule three.", 0.3, "Count the radios.", shot=('card', dict(kind='rules', show=3)))
N('N5', "Rule four.", 0.3, "Never tell anyone what you have.", gap=1.0, shot=('card', dict(kind='rules', show=4)))

N('O1', "Two thirty-one.", gap=0.4, music=('stop', {'fade': 1.0}), amb='store_dark', shot=('aisle', dict(mode='dark', hero=dict(x=760, pose='stand', expr='worried', look=0.4), hud=H(7, '2:31 AM', 0))))
N('O2', "The radio clicks.", gap=0.4, shot=('radio', dict(mode='belt')), sfx=[('$-0.1', 'radio_click', {})])
DALE('O3', "You came back.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
HERO('O4', "This is my store.", gap=0.8, shot=('hclose', dict(expr='determined', bg='dark', prop='radio_mouth')))
BEAT('O5', 1.8, shot=('aisle', dict(mode='dark', clock12=True, hud=None)), sfx=[(0.6, 'alarm_far', dict(until='O9', off=0.0))])
N('O6', "In aisle twelve, the alarm starts to ring.", gap=0.6, shot=('prop', dict(item='clock', mode='ring')))
BEAT('O7', 1.2)
DALE('O8', "That...", 0.6, "That's not me.", gap=0.6, rate=2.2, level=-3, shot=('radio', dict(mode='talk', who='dale', scared=True)))
BEAT('O9', 2.6, shot=('black', dict()), sfx=[(0.0, 'ring_cut', {})])
BEAT('END', 6.5, shot=('card', dict(kind='end')), music=('end', {}), amb='silence')
