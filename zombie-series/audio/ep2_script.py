# Episode 2 · The Mall (Day 8-14). Same item grammar as ep1_script.py; there is no reused cold open, the
# episode starts at 0:00 with its own POV opening and title card.
#
# Items play in order. Voiced items: N (narrator), DALE (radio), HERO (you, hushed), NORA (hushed, or over the
# radio with radio=True), PA (a speaker). Positional args alternate phrase text and the pause after it.
# BEAT holds a silent stretch for `dur` seconds. Keyword args as in ep1: gap, rate, level, shot, shots, sfx,
# music, amb, caps.
SAY = {'aisle': 'ile', 'Aisle': 'Ile', 'S. O. S.': 'S, O, S.', 'Nora': 'Nora', 'Leo': 'Leo'}   # spellings the voice pronounces right

ITEMS = []
def _voiced(who, id_, args, kw):
    phrases, i = [], 0
    while i < len(args):
        txt = args[i]; pause = args[i + 1] if i + 1 < len(args) and isinstance(args[i + 1], (int, float)) else 0.32
        phrases.append([txt, pause]); i += 2 if i + 1 < len(args) and isinstance(args[i + 1], (int, float)) else 1
    d = dict(id=id_, who=who, phrases=phrases, rate=kw.pop('rate', dict(N=2.75, DALE=2.6, HERO=2.3, NORA=2.5, PA=3.0)[who]),
             level=kw.pop('level', 0), gap=kw.pop('gap', 0.45))
    d.update(kw); ITEMS.append(d)
def N(id_, *a, **kw): _voiced('N', id_, a, kw)
def DALE(id_, *a, **kw): _voiced('DALE', id_, a, kw)
def HERO(id_, *a, **kw): _voiced('HERO', id_, a, kw)
def NORA(id_, *a, **kw): _voiced('NORA', id_, a, kw)
def PA(id_, *a, **kw): _voiced('PA', id_, a, kw)
def BEAT(id_, dur, **kw): ITEMS.append(dict(id=id_, who='BEAT', dur=dur, gap=kw.pop('gap', 0.0), **kw))

H = lambda day, time, noise=1, place='FRESHWAY · AISLE 7': dict(day=day, time=time, noise=noise, place=place)
MALL = lambda day, time, noise=1, place='BROOKFIELD MALL · LEVEL 1': dict(day=day, time=time, noise=noise, place=place)

# ======================= COLD OPEN · 2:31 AM, DAY 8 =======================
BEAT('CO1', 5.0, shot=('povaisle', dict(phase='walk')), amb='store_dark', music=('dread', {}),
     caps=[(0.4, 2.6, 'an alarm clock'), (2.8, 4.8, 'aisle twelve')], sfx=[(0, 'alarm_far', dict(until='CO4', off=-1.2))])
N('C1', "Two thirty-one in the morning.", 0.3, "Day eight.", shot=('povaisle', dict(phase='near')))
N('C2', "The alarm in aisle twelve is ringing again.", shot=('prop2', dict(item='clock12', mode='ring')))
N('C3', "And every dead thing outside Freshway can hear it.", shot=('lot', dict(mode='turn', time='night', hud=H(8, '2:31 AM', 4, 'FRESHWAY · PARKING LOT'))),
  sfx=[(0.8, 'crowd_surge', dict(dur=3.2, level=-18))])
BEAT('CO4', 2.6, shot=('povaisle', dict(phase='reach')), caps=[(0.3, 1.2, 'click'), (1.4, 2.5, 'silence')], sfx=[(1.05, 'ring_cut', {}), (1.1, 'tok', {})])
N('C4', "You turn it off.", 0.4, "And under the clock, there's a candy wrapper.", shot=('prop2', dict(item='wrapper')), music=('sting_mystery', {}))
N('C5', "Sour worms.", 0.35, "Still sticky.", gap=0.6)
DALE('C6', "Kid.", 0.4, "That wasn't me.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('C7', "Two people are locked inside this store.", 0.35, "One of them is lying.", music=('pulse_soft', {}),
  shot=('map2', dict(mode='split', show='both')))
N('C8', "And in three days, you run out of water.", gap=0.5, shot=('prop2', dict(item='bottle')))
N('C9', "This week, you'll cross to the mall.", 0.3, "You'll meet someone alive.", shot=('mall', dict(time='night')))
N('C10', "And you'll learn what Dale has been hiding.", gap=0.8, shot=('stockdoors', dict(mode='shadow')))
BEAT('TITLE', 4.6, shot=('ep_title', dict(ep=2, title='THE MALL')), music=('stop', {'fade': 0.6}), amb='silence', sfx=[(0.1, 'low_sting', {})])

# ======================= ACT 1 · DAY 8 · THE BORDER =======================
N('A1', "Day eight.", 0.35, "Here's the new map of Freshway.", music=('think', {}), amb='store_day',
  shot=('map2', dict(mode='split', show='none')))
N('A2', "The front is yours.", 0.3, "Fourteen aisles.", 0.25, "Eight thousand cans.", 0.25, "Gary's office.",
  shot=('map2', dict(mode='split', show='front')))
N('A3', "The back is Dale's.", 0.3, "The stockroom.", 0.25, "The freezer.", 0.3, "And the wall you built out of bottled water.",
  shot=('map2', dict(mode='split', show='back')))
N('A4', "Every gallon you have is in that wall.", 0.35, "And Dale is on the other side of it.",
  shot=('map2', dict(mode='split', show='wall')))
N('A5', "On day seven, he jammed the stockroom doors shut.", shot=('stockdoors', dict(mode='jammed', hud=H(8, '9:12 AM', 1, 'FRESHWAY · STOCKROOM DOORS'))),
  sfx=[('$-0.4', 'thump_metal', dict(level=-16))])
BEAT('A5b', 1.0, sfx=[(0.2, 'radio_click', {})])
DALE('A6', "Here's how this works, kid.", 0.35, "You stay up front.", 0.3, "I stay in back.", 0.35, "Nobody gets hurt.",
     shot=('radio', dict(mode='talk', who='dale')), music=('radio', {}))
HERO('A7', "And the water?", gap=0.5, shot=('hclose2', dict(expr='determined', bg='stockdoors', prop='radio_mouth')))
DALE('A8', "One gallon.", 0.35, "For twenty cans.", 0.3, "Every morning.", shot=('radio', dict(mode='talk', who='dale')))
N('A9', "He wants to know how many cans you have.", shot=('hclose2', dict(expr='worried', bg='aisle_day', look=0.3)))
N('A10', "Rule four.", 0.35, "Never tell anyone what you have.", shot=('card', dict(kind='rule', n=4, lines=['NEVER TELL ANYONE', 'WHAT YOU HAVE.'], icon='note')),
  sfx=[(0, 'whoosh', {}), (0.15, 'stamp', dict(level=-14))])
HERO('A11', "Maybe a hundred.", gap=0.6, shot=('hclose2', dict(expr='neutral', bg='aisle_day', prop='radio_mouth')))
N('A12', "You have eight thousand nine hundred.", gap=0.7, music=('humor', {}),
  shot=('card', dict(kind='supplies', day=8, rows=[['Food', '8,900 cans', ''], ['Water', '2 liters', 'THE REST IS DALE\'S'], ['Batteries', '2', '']])))
N('A13', "Problem one.", 0.35, "Water.", gap=0.5, music=('pulse_soft', {}),
  shot=('card', dict(kind='problem', n=1, title='WATER', sub='YOU HAVE TWO LITERS', icon='drop')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('A14', "A person needs about three liters a day.", 0.35, "With none, you get about three days.",
  shot=('card', dict(kind='fact', big='3', unit='DAYS', icon='drop', note='HOW LONG A PERSON LASTS WITHOUT WATER', src='RULE OF THREES · SURVIVAL MEDICINE')))

# ======================= ACT 1 · DAY 9 · THE PIPES =======================
N('B1', "Day nine.", 0.35, "You try the faucet in the staff restroom.", amb='restroom', music=('stop', {'fade': 1.0}),
  shot=('restroom', dict(view='sink', hud=H(9, '7:40 AM', 1, 'FRESHWAY · STAFF RESTROOM'))))
N('B2', "It coughs.", 0.3, "Spits.", 0.3, "And stops.", gap=0.6, shot=('restroom', dict(view='faucet')),
  sfx=[(0.0, 'pipe_cough', {}), ('@Spits', 'pipe_cough', dict(k=2)), ('$-0.2', 'tok', dict(level=-20))])
N('B3', "City water runs on pumps.", 0.3, "No power, no pumps.", 0.35, "The towers drain in a day or two.", music=('think', {}),
  shot=('card', dict(kind='fact', big='1-2', unit='DAYS', icon='drop', note='CITY WATER PRESSURE AFTER THE PUMPS STOP', src='MUNICIPAL WATER SYSTEMS · GRAVITY STORAGE')))
N('B4', "But every building with hot water keeps a tank of it.", shot=('restroom', dict(view='heater')))
N('B5', "This one holds twenty gallons.", 0.3, "Clean.", 0.3, "And it's on your side of the border.")
N('B6', "There's a drain valve at the bottom.", 0.35, "The first gallon comes out brown.", 0.35, "Then it runs clear.",
  shot=('restroom', dict(view='drain')), sfx=[('@drain', 'valve_squeak', {}), ('@first', 'water_pour', dict(dur=5.0))])
N('B7', "And the toilet tanks.", 0.3, "Not the bowls.", 0.3, "The tanks.", 0.3, "Same water as the tap.", music=('humor', {}),
  shot=('restroom', dict(view='tanks')), sfx=[('@tanks', 'lid_clunk', {})])
N('B8', "Problem one.", 0.3, "Solved.", gap=0.6,
  shot=('card', dict(kind='problem', n=1, title='WATER', sub='YOU HAVE TWO LITERS', icon='drop', stamp='SOLVED')), sfx=[(0.3, 'stamp', {})])
N('B9', "That night, the radio clicks.", amb='store_night', music=('radio', {}), shot=('radio', dict(mode='belt')), sfx=[('$-0.15', 'radio_click', {})])
DALE('B10', "Heard you found the water heater.", 0.4, "Smart.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('B11', "You never told him.", gap=0.7, shot=('hclose2', dict(expr='worried', bg='camp', prop='radio')), music=('stop', {'fade': 0.8}))
N('B12', "Then you hear it.", 0.35, "A tap.", 0.4, "In the pipes.", shot=('restroom', dict(view='pipes_dark')),
  sfx=[('@tap', 'pipe_knock', {}), ('$', 'pipe_knock', dict(k=2)), ('$+0.5', 'pipe_knock', dict(k=3))], gap=0.8)
N('B13', "The pipes run through the whole building.", 0.35, "Every sound in that restroom ends up in his ear.", music=('dread', {}),
  shot=('map2', dict(mode='pipes')))
N('B14', "Rule five.", 0.35, "The walls have ears.", gap=0.8, music=('rule', {}),
  shot=('card', dict(kind='rule', n=5, lines=['THE WALLS', 'HAVE EARS.'], icon='ear')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])

# ======================= ACT 2 · DAY 9 · THE LIGHT =======================
N('L1', "Eleven at night.", 0.3, "You climb to the roof.", music=('night_op', {}), amb='roof_night',
  shot=('roof', dict(time='night', hero='edge', hud=H(9, '11:02 PM', 1, 'FRESHWAY · ROOF'))))
N('L2', "The light in the mall is still on.", 0.3, "Top floor.", 0.3, "Same window.", shot=('mallwin', dict(mode='steady')))
N('L3', "Last week, you decided nobody was over there.", gap=0.6)
N('L4', "And then it blinks.", gap=0.2, shot=('mallwin', dict(mode='blink')), music=('stop', {'fade': 0.3}))
BEAT('L5', 3.4, caps=[(0.2, 3.2, 'a light, blinking')])
N('L6', "Three short.", 0.35, "Three long.", 0.35, "Three short.", shot=('card2', dict(kind='morse')))
N('L7', "S. O. S.", 0.45, "Somebody over there is alive.", 0.35, "And asking for help.", gap=0.6, music=('hope', {}))
N('L8', "Would you go?", 0.35, "Tell me in the comments.", gap=0.7, shot=('card', dict(kind='comment', text='Would you answer the SOS?')))

# ======================= ACT 2 · DAY 10 · THE STORM =======================
N('P1', "Day ten.", 0.35, "The decoy clocks are gone.", 0.3, "And Dale knows that trick anyway.", music=('plan', {}), amb='store_day',
  shot=('prop', dict(item='clocks6')))
N('P2', "You need a sound bigger than you.", 0.3, "Bigger than anything.", shot=('hclose2', dict(expr='determined', bg='aisle_day', look=0.2)))
N('P3', "Then, at two in the afternoon, the sky goes dark.", amb='roof', shot=('storm', dict(mode='clouds', hud=H(10, '2:04 PM', 1, 'FRESHWAY · ROOF'))),
  sfx=[('$', 'thunder', dict(far=True))])
N('P4', "A storm is coming.", gap=0.5)
N('P5', "Heavy rain is about fifty decibels.", 0.35, "Footsteps on wet asphalt, about thirty.",
  shot=('card', dict(kind='fact', big='50', unit='DECIBELS', icon='rain', note='HEAVY RAIN · FOOTSTEPS ARE ABOUT 30', src='TYPICAL SOUND LEVELS')))
N('P6', "In a storm, they can't pick you out.", 0.3, "They just stand there.", 0.3, "Listening to the sky.",
  shot=('storm', dict(mode='crowd')), amb='storm', sfx=[('$-0.5', 'thunder', {})])
N('P7', "Before you go, you chain the stockroom doors.", 0.3, "From your side.", amb='store_day',
  shot=('stockdoors', dict(mode='chain')), sfx=[('@chain', 'chain_rattle', {}), ('$', 'lock_click', {})])
BEAT('P7b', 0.9, sfx=[(0.3, 'radio_click', {})])
DALE('P8', "Going somewhere, kid?", gap=0.5, shot=('radio', dict(mode='talk', who='dale')))
N('P9', "Rule four.", 0.35, "You don't answer.", gap=0.8, shot=('hclose2', dict(expr='determined', bg='stockdoors', look=-0.3)))

# ======================= POV · ACROSS THE LOT IN THE RAIN =======================
BEAT('R0', 5.4, shot=('povstorm', dict(phase='walk')), amb='storm', music=('storm', {}),
     caps=[(0.3, 2.6, 'heavy rain'), (3.0, 5.2, 'thunder')], sfx=[(3.0, 'thunder', {})])
N('R1', "Two hundred of them.", 0.35, "Standing in the rain.", 0.35, "Faces up.", shot=('povstorm', dict(phase='crowd')))
BEAT('R1b', 4.2, shot=('povstorm', dict(phase='pass')), caps=[(0.3, 3.9, 'right next to you')], sfx=[(0.8, 'groan_close', dict(level=-24))])
N('R2', "Nobody turns.", gap=0.6)
N('R3', "The mall's side door is chained.", 0.35, "The glass next to it isn't.", shot=('malldoor', dict(mode='chained', hud=MALL(10, '2:31 PM', 2, 'BROOKFIELD MALL · SIDE DOOR'))))
N('R4', "You wait for the thunder.", 0.6, "And you break it.", gap=0.3, shot=('malldoor', dict(mode='break')),
  sfx=[('@break', 'thunder', dict(close=True)), ('@break', 'glass_break', {})])
BEAT('R4b', 1.2, shot=('black', {}), music=('stop', {'fade': 0.3}))

# ======================= ACT 2 · THE MALL =======================
N('M1', "Brookfield Mall.", 0.35, "Four floors.", 0.3, "Dark.", amb='mall_rain', music=('vast', {}),
  shot=('atrium', dict(mode='wide', hud=MALL(10, '2:33 PM', 2))))
N('M2', "Rain drums on the glass roof.", 0.3, "It's the loudest room you've ever stood in.", 0.4, "Good.", gap=0.6, shot=('atrium', dict(mode='skylight')))
N('M3', "Around the dry fountain, thirty of them.", shot=('atrium', dict(mode='fountain')))
N('M4', "Shoppers.", 0.3, "A security guard.", 0.3, "A kid from the pretzel stand, still in his paper hat.",
  shots=[(0, 'zname', dict(who='shopper', label='SHOPPER · LEVEL 1', bg='mall')), ('@security', 'zname', dict(who='mike', label='MALL SECURITY', bg='mall')),
         ('@kid', 'zname', dict(who='pretzel', label='PRETZEL PALACE · 16', bg='mall'))])
N('M5', "The window was on the top floor.", 0.35, "The escalators stopped on day four.", shot=('escalator', dict(mode='side')))
N('M6', "A stopped escalator is just stairs.", 0.3, "Loud stairs.", 0.3, "Metal.")
N('M7', "You walk on the edges.", 0.3, "Where the steps are bolted down.", shot=('escalator', dict(mode='feet')))
BEAT('M7b', 4.0, shot=('escalator', dict(mode='pov')), caps=[(0.3, 1.8, 'a clank'), (2.0, 3.8, 'thunder covers it')],
     sfx=[(0.5, 'escalator_clank', {}), (1.9, 'thunder', {})])
N('M8', "Top floor.", 0.3, "A store called Bright Tech.", 0.3, "The lantern is in the window.", music=('think', {}),
  shot=('brighttech', dict(mode='front', hud=MALL(10, '2:41 PM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('M9', "Nobody's there.", gap=0.5, shot=('brighttech', dict(mode='inside')))
N('M10', "A sleeping bag.", 0.3, "Two backpacks.", 0.3, "A solar panel taped to the glass.", shot=('brighttech', dict(mode='camp')))
N('M11', "Then something cold touches the back of your neck.", gap=0.3, music=('stop', {'fade': 0.15}),
  shot=('nora', dict(mode='behind')), sfx=[('$-0.3', 'tok', dict(level=-14))])
NORA('M12', "Don't.", 0.5, "Move.", gap=0.7)
N('M13', "It's a fire extinguisher.", 0.3, "Held by a girl.", 0.3, "Fifteen.", 0.3, "Maybe.", music=('tender', {}),
  shot=('nora', dict(mode='reveal')))
NORA('M14', "You're the Freshway guy.", gap=0.5, shot=('nora', dict(mode='close', expr='serious')))
N('M15', "She knows you.", gap=0.4, shot=('hclose2', dict(expr='surprised', bg='brighttech')))
NORA('M16', "I've been listening to you.", 0.35, "Every night.", 0.35, "Channel three.", shot=('nora', dict(mode='radio')))
N('M17', "Rule three.", 0.35, "Count the radios.", 0.4, "There are three.", gap=0.8,
  shot=('card2', dict(kind='radios3')), sfx=[(0, 'whoosh', {})])

# ======================= ACT 3 · DAY 11 · NORA =======================
N('N1', "The storm ends at six.", 0.35, "And the silence comes back.", amb='mall_quiet', music=('tender', {}),
  shot=('atrium', dict(mode='after', hud=MALL(10, '6:02 PM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('N2', "You're not crossing that lot tonight.", gap=0.6)
N('N3', "Her name is Nora.", 0.35, "She's been here since the first night.", shot=('brighttech', dict(mode='lantern')))
NORA('N4', "My mom worked nights here.", 0.35, "Inventory.", gap=0.6, shot=('nora', dict(mode='close', expr='sad')))
N('N5', "She doesn't say what happened to her mom.", 0.35, "You don't ask.", gap=0.7, shot=('brighttech', dict(mode='lantern', two=True)))
NORA('N6', "My little brother went across the street that night.", 0.35, "To Freshway.", 0.35, "For candy.",
     shot=('nora', dict(mode='close', expr='serious')))
N('N7', "He's nine.", 0.3, "His name is Leo.", shot=('prop2', dict(item='photo')))
N('N8', "You were in Freshway that night.", 0.35, "You never saw a kid.", shot=('hclose2', dict(expr='worried', bg='brighttech', look=-0.2)))
NORA('N9', "Every night, at two thirty-one, there's an alarm over there.", 0.35, "I can hear it from here.", shot=('nora', dict(mode='window')))
NORA('N10', "That's him.", 0.4, "That's how I know he's alive.", gap=0.7)
N('N11', "The candy wrapper.", 0.4, "Sour worms.", gap=0.6, shot=('prop2', dict(item='wrapper')), sfx=[(0.1, 'low_sting', {})])
N('N12', "Then Nora's radio clicks.", music=('stop', {'fade': 0.6}), shot=('nora', dict(mode='radio')), sfx=[('$-0.15', 'radio_click', {})])
DALE('N13', "Nora?", 0.5, "Honey?", 0.5, "Are you there?", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('N14', "Nora goes white.", gap=0.5, shot=('nora', dict(mode='close', expr='shock')))
NORA('N15', "That's my dad.", gap=0.9)
N('N16', "Dale is her father.", gap=0.8, music=('twist', {}), shot=('hclose2', dict(expr='surprised', bg='brighttech', look=0.1)), sfx=[(0, 'low_sting', {})])
N('N17', "He asked how many of you there were.", 0.35, "He asked about the freezer.", 0.35, "He asked about the alarm.",
  shot=('card2', dict(kind='clues')))
N('N18', "He wasn't counting your food.", 0.35, "He was looking for his son.", gap=0.7, shot=('stockdoors', dict(mode='shadow')))
N('N19', "Rule four works both ways.", 0.35, "Dale never told you what he has.", shot=('hclose2', dict(expr='determined', bg='brighttech')))
N('N20', "He has a son.", 0.4, "Somewhere inside Freshway.", gap=1.0, shot=('freshroof', dict(mode='figure')))

# ======================= ACT 3 · DAY 13 · THE SONG =======================
N('S1', "Day thirteen.", 0.35, "You need to get back.", 0.3, "Both of you.", music=('plan', {}), amb='mall_quiet',
  shot=('brighttech', dict(mode='lantern', two=True, day=True, hud=MALL(13, '1:15 AM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('S2', "No storm.", 0.3, "No clocks.", 0.3, "Just two hundred of them in the lot.", shot=('lot', dict(mode='count', time='night', hud=H(13, '1:20 AM', 1, 'FRESHWAY · PARKING LOT'))))
N('S3', "Nora has an idea.", 0.35, "Bright Tech sells drones.", shot=('drone', dict(mode='box')))
N('S4', "And a speaker that clips onto anything.", shot=('drone', dict(mode='clip')), sfx=[('$-0.3', 'tok', {})])
N('S5', "Rule two.", 0.3, "Music is a dinner bell.", 0.4, "This time, you ring it on purpose.", gap=0.6,
  shot=('card', dict(kind='rule', n=2, lines=['MUSIC IS A', 'DINNER BELL.'], icon='note')), sfx=[(0, 'whoosh', {})])
N('S6', "Nora has one song on her phone.", 0.35, "Guess which one.", gap=0.5, music=('stop', {'fade': 0.4}), shot=('nora', dict(mode='close', expr='smirk')))
BEAT('S7', 6.0, shot=('drone', dict(mode='fly')), music=('jingle', {}), amb='lot_night',
     caps=[(0.3, 2.8, 'the Freshway jingle'), (3.0, 5.8, 'two hundred of them, turning')], sfx=[(0, 'drone_buzz', dict(until='S9', off=0.0))])
N('S8', "Two hundred dead people follow a song about discount yogurt.", 0.35, "To the far end of the lot.", music=('humor', {}),
  shot=('drone', dict(mode='lot')))
N('S9', "You run for the staff door.", 0.3, "Gary's keys.", 0.3, "The fourth one.", 0.35, "You remember this time.",
  music=('chase', {}), shot=('staffdoor', dict(mode='arrive', hud=H(13, '1:42 AM', 3, 'FRESHWAY · STAFF DOOR'))), sfx=[(0, 'run_steps', dict(dur=3.0)), ('@fourth', 'lock_click', {})])
N('S10', "You're in.", 0.35, "Both of you.", gap=0.8, music=('stop', {'fade': 0.4}), amb='store_dark',
  shot=('staffdoor', dict(mode='inside')), sfx=[('@in', 'door_bang', {})])

# ======================= FINALE · DAY 14 =======================
N('F1', "Day fourteen.", 0.35, "Here's what you know.", music=('resolve', {}), shot=('card', dict(kind='rules', show=0, day=14, n=5)))
N('F2', "Rule one.", 0.3, "They hear.", 0.25, "They don't see.", shot=('card', dict(kind='rules', show=1, day=14, n=5)))
N('F3', "Rule two.", 0.3, "Music is a dinner bell.", shot=('card', dict(kind='rules', show=2, day=14, n=5)))
N('F4', "Rule three.", 0.3, "Count the radios.", shot=('card', dict(kind='rules', show=3, day=14, n=5)))
N('F5', "Rule four.", 0.3, "Never tell anyone what you have.", shot=('card', dict(kind='rules', show=4, day=14, n=5)))
N('F6', "Rule five.", 0.3, "The walls have ears.", gap=0.8, shot=('card', dict(kind='rules', show=5, day=14, n=5)))
N('F7', "The radio clicks.", music=('stop', {'fade': 0.8}), shot=('radio', dict(mode='belt')), sfx=[('$-0.1', 'radio_click', {})])
DALE('F8', "You brought her home.", 0.5, "Thank you.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
NORA('F9', "Where's Leo, Dad?", gap=1.2, shot=('nora', dict(mode='close', expr='serious', bg='store')))
N('F10', "Dale doesn't answer.", gap=0.8, shot=('radio', dict(mode='belt')))
N('F11', "Two thirty-one.", gap=0.3, shot=('prop2', dict(item='clock12', mode='still')))
N('F12', "The alarm in aisle twelve starts to ring.", shot=('prop2', dict(item='clock12', mode='ring')), sfx=[(0, 'alarm_near', dict(until='F13', off=1.4))])
N('F13', "Nora runs.", gap=0.6, shot=('aisle2', dict(mode='nora_run')), sfx=[(0, 'run_steps', dict(dur=2.2, level=-16))])
N('F14', "Next to the clock, there's a drawing.", 0.35, "In crayon.", shot=('prop2', dict(item='drawing', mode='reveal')), sfx=[(0.1, 'paper_rustle', {})], music=('sting_mystery', {}))
N('F15', "A girl.", 0.3, "A man in a cap.", 0.3, "And you.", 0.35, "Orange headphones and all.", shot=('prop2', dict(item='drawing', mode='close')))
N('F16', "Under it, three words.", 0.6, "Come find me.", gap=0.8, shot=('prop2', dict(item='drawing', mode='words')))
N('F17', "Leo is alive.", 0.35, "He's in this store.", 0.4, "And they don't see you.", 0.5, "But he does.", gap=1.4,
  shot=('povaisle', dict(phase='vent')), music=('end', {}))
BEAT('END', 8.0, shot=('card', dict(kind='end', day=15, ep=3, title='LIGHTS OUT', sub='WHERE IS LEO?')), amb='silence')
