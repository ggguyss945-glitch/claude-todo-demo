# Episode 2 · The Mall (Day 8-14). Same item grammar as ep1_script.py; there is no reused cold open, the
# episode starts at 0:00 with its own POV opening and title card.
#
# Items play in order. Voiced items: N (narrator), DALE (radio), HERO (you, hushed), NORA (hushed, or over the
# radio with radio=True), PA (a speaker). Positional args alternate phrase text and the pause after it.
# BEAT holds a silent stretch for `dur` seconds. Keyword args as in ep1: gap, rate, level, shot, shots, sfx,
# music, amb, caps.
SAY = {'aisle': 'ile', 'Aisle': 'Ile', 'S. O. S.': 'S, O, S.', 'Nora': 'Nora', 'Leo': 'Leo'}   # spellings the voice pronounces right

VOICE_MODE, VOICE_STEPS = 'item', 16   # whole-line takes, cleaner synthesis than ep1's 8 steps
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
BEAT('TITLE', 5.6, shot=('ep_title', dict(ep=2, title='THE MALL')), music=('stop', {'fade': 0.6}), amb='silence', sfx=[(0.1, 'low_sting', {})])

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
DALE('A8', "One gallon.", 0.35, "For twenty cans.", 0.3, "Every morning.", shot=('radio', dict(mode='doors')))
N('A8b', "Twenty cans for one gallon.", 0.35, "In a normal store, that's a terrible deal.", 0.4, "This is not a normal store anymore.",
  shot=('card2', dict(kind='trade')), music=('humor', {}))
DALE('A8c', "So how many cans you got left, anyway?", shot=('radio', dict(mode='talk', who='dale')), music=('radio', {}))
N('A9', "He wants to know how many cans you have.", shot=('hclose2', dict(expr='worried', bg='aisle_day', look=0.3)))
N('A10', "Rule four.", 0.35, "Never tell anyone what you have.", shot=('card', dict(kind='rule', n=4, lines=['NEVER TELL ANYONE', 'WHAT YOU HAVE.'], icon='note')),
  sfx=[(0, 'whoosh', {}), (0.15, 'stamp', dict(level=-14))])
HERO('A11', "Maybe a hundred.", gap=0.6, shot=('hclose2', dict(expr='neutral', bg='aisle_day', prop='radio_mouth')))
DALE('A11b', "Last week you said nine thousand.", gap=0.5, shot=('radio', dict(mode='doors')))
HERO('A11c', "It's been a long week.", gap=0.7, shot=('hclose2', dict(expr='neutral', bg='aisle_day', prop='radio_mouth', look=-0.2)))
N('A12', "You have eight thousand nine hundred.", gap=0.7, music=('humor', {}),
  shot=('card', dict(kind='supplies', day=8, rows=[['Food', '8,900 cans', ''], ['Water', '2 liters', 'THE REST IS DALE\'S'], ['Batteries', '2', '']])))
N('A12b', "At twenty cans a day, that's enough to buy water for over a year.", 0.35, "As long as Dale keeps his word.", music=('stop', {'fade': 1.0}))
N('A12c', "Day nine.", 0.35, "Seven in the morning.", 0.35, "The gallon doesn't come.", gap=0.6, music=('pulse_soft', {}),
  shot=('stockdoors', dict(mode='jammed', hud=H(9, '7:01 AM', 1, 'FRESHWAY · STOCKROOM DOORS'))))
DALE('A12d', "Tell me the real number, kid.", 0.4, "Then the water comes back.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
N('A13', "Problem one.", 0.35, "Water.", gap=0.5,
  shot=('card', dict(kind='problem', n=1, title='WATER', sub='YOU HAVE TWO LITERS', icon='drop')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('A14', "A person needs about three liters a day.", 0.35, "With none, you get about three days.",
  shot=('card', dict(kind='fact', big='3', unit='DAYS', icon='drop', note='HOW LONG A PERSON LASTS WITHOUT WATER', src='RULE OF THREES · SURVIVAL MEDICINE')))
N('A15', "So you need water Dale doesn't control.", 0.35, "Today.", gap=0.6, shot=('hclose2', dict(expr='determined', bg='aisle_day', look=0.2)))

# ======================= ACT 1 · DAY 9 · THE PIPES =======================
N('B1', "You try the faucet in the staff restroom.", amb='restroom', music=('stop', {'fade': 1.0}),
  shot=('restroom', dict(view='sink', hud=H(9, '7:40 AM', 1, 'FRESHWAY · STAFF RESTROOM'))))
N('B2', "It coughs.", 0.3, "Spits.", 0.3, "And stops.", gap=0.6, shot=('restroom', dict(view='faucet')),
  sfx=[(0.0, 'pipe_cough', {}), ('@Spits', 'pipe_cough', dict(k=2)), ('$-0.2', 'tok', dict(level=-20))])
N('B3', "City water runs on pumps.", 0.3, "No power, no pumps.", 0.35, "The towers drain in a day or two.", music=('think', {}),
  shot=('card', dict(kind='fact', big='1-2', unit='DAYS', icon='drop', note='CITY WATER PRESSURE AFTER THE PUMPS STOP', src='MUNICIPAL WATER SYSTEMS · GRAVITY STORAGE')))
N('B4', "But every building with hot water keeps a tank of it.", shot=('restroom', dict(view='heater')))
N('B5', "This one holds twenty gallons.", 0.3, "Clean.", 0.3, "And it's on your side of the border.")
N('B6', "There's a drain valve at the bottom.", 0.35, "The first gallon comes out brown.", 0.35, "Then it runs clear.",
  shot=('restroom', dict(view='drain')), sfx=[('@drain', 'valve_squeak', {}), ('@first', 'water_pour', dict(dur=5.0))])
N('B6b', "Water that sits in a tank can grow things.", 0.35, "So before you drink it, you clean it.")
N('B6c', "Eight drops of plain bleach per gallon.", 0.35, "Then wait thirty minutes.",
  shot=('card', dict(kind='fact', big='8', unit='DROPS', icon='drop', note='OF PLAIN, UNSCENTED BLEACH PER GALLON · WAIT 30 MINUTES', src='EPA · EMERGENCY DISINFECTION OF DRINKING WATER')))
N('B6d', "Aisle four has bleach.", 0.3, "Gary labeled the shelf, of course.", gap=0.6, music=('humor', {}))
N('B7', "And the toilet tanks.", 0.3, "Not the bowls.", 0.3, "The tanks.", 0.3, "Same water as the tap.",
  shot=('restroom', dict(view='tanks')), sfx=[('@tanks', 'lid_clunk', {})])
N('B7b', "Twenty gallons, plus four tanks.", 0.35, "If you're careful, that's about a month.")
N('B8', "Problem one.", 0.3, "Solved.", gap=0.6,
  shot=('card', dict(kind='problem', n=1, title='WATER', sub='ABOUT A MONTH, IF YOU\'RE CAREFUL', icon='drop', stamp='SOLVED')), sfx=[(0.3, 'stamp', {})])
N('B9', "That night, the radio clicks.", amb='store_night', music=('radio', {}), shot=('radio', dict(mode='belt')), sfx=[('$-0.15', 'radio_click', {})])
DALE('B10', "Heard you found the water heater.", 0.4, "Smart.", gap=0.6, shot=('radio', dict(mode='talk', who='dale')))
DALE('B10b', "Guess you don't need my water anymore.", gap=0.6)
N('B11', "You never told him.", gap=0.7, shot=('hclose2', dict(expr='worried', bg='camp', prop='radio')), music=('stop', {'fade': 0.8}))
N('B12', "Then you hear it.", 0.35, "A tap.", 0.4, "In the pipes.", shot=('restroom', dict(view='pipes_dark')),
  sfx=[('@tap', 'pipe_knock', {}), ('$', 'pipe_knock', dict(k=2)), ('$+0.5', 'pipe_knock', dict(k=3))], gap=0.8)
N('B13', "The pipes run through the whole building.", 0.35, "Every sound in that restroom ends up in his ear.", music=('dread', {}),
  shot=('map2', dict(mode='pipes')))
N('B14', "Rule five.", 0.35, "The walls have ears.", gap=0.8, music=('rule', {}),
  shot=('card', dict(kind='rule', n=5, lines=['THE WALLS', 'HAVE EARS.'], icon='ear')), sfx=[(0, 'whoosh', {}), (0.15, 'slam', {})])
N('B15', "Later that night, the pipes carry something else.", music=('stop', {'fade': 0.8}), amb='store_dark', shot=('restroom', dict(view='pipes_dark', voice=True)))
N('B16', "Dale's voice.", 0.35, "Not on the radio.", 0.3, "Through the wall.", gap=0.6)
DALE('B17', "Ninety-eight.", 0.6, "Ninety-nine.", 0.6, "A hundred.", 0.9, "Ready or not.", gap=0.9, pipe=True, rate=2.0, level=-2)
N('B18', "He's counting.", 0.35, "Like a kid playing hide-and-seek.", music=('sting_mystery', {}), shot=('hclose2', dict(expr='worried', bg='camp', look=-0.3)))
N('B19', "Who counts to a hundred in an empty store?", gap=1.0)
BEAT('B19x', 2.0, shot=('restroom', dict(view='pipes_dark')), caps=[(0.2, 1.8, 'the pipes go quiet')])

# ======================= ACT 2 · DAY 9 · THE LIGHT =======================
BEAT('L0', 2.5, music=('night_op', {}), amb='roof_night', shot=('roof', dict(time='night', hero='edge', hud=H(9, '11:02 PM', 1, 'FRESHWAY · ROOF'))),
     caps=[(0.3, 2.3, 'wind on the roof')])
N('L1', "Eleven at night.", 0.3, "You climb to the roof.")
N('L2', "The light in the mall is still on.", 0.3, "Top floor.", 0.3, "Same window.", shot=('mallwin', dict(mode='steady')))
N('L3', "Last week, you decided nobody was over there.", gap=0.6)
N('L4', "And then it blinks.", gap=0.2, shot=('mallwin', dict(mode='blink')), music=('stop', {'fade': 0.3}))
BEAT('L5', 3.4, caps=[(0.2, 3.2, 'a light, blinking')])
N('L6', "Three short.", 0.35, "Three long.", 0.35, "Three short.", shot=('card2', dict(kind='morse')))
N('L7', "S. O. S.", 0.45, "Somebody over there is alive.", 0.35, "And asking for help.", gap=0.6, music=('hope', {}))
N('L7b', "Not on the radio.", 0.3, "With a lamp.", 0.4, "Whoever it is, they don't want Dale to hear.", gap=0.6, shot=('mallwin', dict(mode='blink')))
N('L8', "Would you go?", 0.35, "Tell me in the comments.", gap=0.7, shot=('card', dict(kind='comment', text='Would you answer the SOS?')))

# ======================= ACT 2 · DAY 10 · THE STORM =======================
N('P1', "Day ten.", 0.35, "The decoy clocks are gone.", 0.3, "And Dale knows that trick anyway.", music=('plan', {}), amb='store_day',
  shot=('prop', dict(item='clocks6', hud=H(10, '9:20 AM', 0, 'FRESHWAY · AISLE 11'))))
N('P2', "You need a sound bigger than you.", 0.3, "Bigger than anything.", shot=('hclose2', dict(expr='determined', bg='aisle_day', look=0.2)))
N('P3', "Then, at two in the afternoon, the sky goes dark.", amb='roof', shot=('storm', dict(mode='clouds', hud=H(10, '2:04 PM', 1, 'FRESHWAY · ROOF'))),
  sfx=[('$', 'thunder', dict(far=True))])
N('P4', "A storm is coming.", gap=0.5)
BEAT('P4x', 2.5, caps=[(0.2, 2.3, 'thunder, far away')], sfx=[(0.6, 'thunder', dict(far=True))])
N('P5', "Heavy rain is about fifty decibels.", 0.35, "Footsteps on wet asphalt, about thirty.",
  shot=('card', dict(kind='fact', big='50', unit='DECIBELS', icon='rain', note='HEAVY RAIN · FOOTSTEPS ARE ABOUT 30', src='TYPICAL SOUND LEVELS')))
N('P6', "In a storm, they can't pick you out.", 0.3, "They just stand there.", 0.3, "Listening to the sky.",
  shot=('storm', dict(mode='crowd')), amb='storm', sfx=[('$-0.5', 'thunder', {})])
N('P6b', "And the thunder tells you where the storm is.", music=('think', {}))
N('P6c', "Count from the flash to the boom.", 0.35, "Every three seconds is about a kilometer.",
  shot=('card', dict(kind='fact', big='3', unit='SECONDS = 1 KM', icon='bolt', note='COUNT FROM THE FLASH TO THE THUNDER', src='SPEED OF SOUND · 343 METERS PER SECOND')))
N('P6d', "Flash.", 0.5, "One.", 0.5, "Two.", 0.5, "Boom.", 0.4, "Less than a kilometer.", rate=2.2,
  shot=('storm', dict(mode='clouds')), sfx=[('@Boom', 'thunder', {})])
N('P6e', "When the flash and the boom come together, it's right on top of you.", 0.35, "That's the loudest it gets.", gap=0.6)
N('P6f', "You pack light.", 0.3, "A flashlight.", 0.3, "A hammer from aisle three.", 0.3, "And the radio, turned all the way down.",
  shot=('card', dict(kind='backpack', day=10, items=['FLASHLIGHT', 'HAMMER', 'RADIO · VOLUME 0'])), music=('plan', {}))
N('P7', "Before you go, you chain the stockroom doors.", 0.3, "From your side.", amb='store_day',
  shot=('stockdoors', dict(mode='chain')), sfx=[('@chain', 'chain_rattle', {}), ('$', 'lock_click', {})])
BEAT('P7b', 0.9, sfx=[(0.3, 'radio_click', {})])
DALE('P8', "Going somewhere, kid?", gap=0.5, shot=('radio', dict(mode='doors')))
N('P9', "Rule four.", 0.35, "You don't answer.", gap=0.8, shot=('hclose2', dict(expr='determined', bg='stockdoors', look=-0.3)), music=('stop', {'fade': 0.6}))

# ======================= POV · ACROSS THE LOT IN THE RAIN =======================
BEAT('R0', 6.4, shot=('povstorm', dict(phase='walk')), amb='storm', music=('storm', {}),
     caps=[(0.3, 2.6, 'heavy rain'), (3.0, 5.2, 'thunder')], sfx=[(3.0, 'thunder', {})])
N('R1', "Two hundred of them.", 0.35, "Standing in the rain.", 0.35, "Faces up.", shot=('povstorm', dict(phase='crowd')))
BEAT('R1b', 4.2, shot=('povstorm', dict(phase='pass')), caps=[(0.3, 3.9, 'right next to you')], sfx=[(0.8, 'groan_close', dict(level=-24))])
N('R2', "Nobody turns.", gap=0.6)
N('R2b', "Halfway across, your shoe hits a bottle.", shot=('povstorm', dict(phase='bottle')), sfx=[('$-0.2', 'bottle_roll', {})])
BEAT('R2c', 2.4, caps=[(0.2, 2.2, 'a bottle, rolling')], sfx=[(1.5, 'clink', {})])
N('R2d', "It clinks against a car.", 0.4, "The closest one is two steps away.", gap=0.3, shot=('povstorm', dict(phase='freeze')))
BEAT('R2e', 2.2, caps=[(0.2, 2.0, 'rain')], sfx=[(1.2, 'thunder', {})])
N('R2f', "The rain eats the sound.", 0.35, "You keep walking.", gap=0.6, shot=('povstorm', dict(phase='walk')))
N('R3', "The mall's side door is chained.", 0.35, "The glass next to it isn't.", shot=('malldoor', dict(mode='chained', hud=MALL(10, '2:31 PM', 2, 'BROOKFIELD MALL · SIDE DOOR'))))
N('R3b', "Flash.", 0.5, "One.", 0.5, "Boom.", 0.4, "Close.", 0.3, "Not close enough.", rate=2.2, sfx=[('@Boom', 'thunder', {})])
N('R3c', "You wait.", 0.6, "Rain on your neck.", 0.4, "Hammer in your hand.", gap=0.5)
N('R4', "Flash and boom, together.", 0.35, "You swing.", gap=0.3, shot=('malldoor', dict(mode='break', at='@swing')),
  sfx=[('@swing', 'thunder', dict(close=True)), ('@swing', 'glass_break', {})])
BEAT('R4b', 1.2, shot=('black', {}), music=('stop', {'fade': 0.3}))

# ======================= ACT 2 · THE MALL =======================
N('M1', "Brookfield Mall.", 0.35, "Four floors.", 0.3, "Dark.", amb='mall_rain', music=('vast', {}),
  shot=('atrium', dict(mode='wide', hud=MALL(10, '2:33 PM', 2))))
BEAT('M1b', 3.4, caps=[(0.2, 2.2, 'rain on glass')])
N('M2', "Rain drums on the glass roof.", 0.3, "It's the loudest room you've ever stood in.", 0.4, "Good.", gap=0.6, shot=('atrium', dict(mode='skylight')))
N('M3', "Around the dry fountain, thirty of them.", shot=('atrium', dict(mode='fountain')))
N('M4', "Shoppers.", 0.3, "A security guard.", 0.3, "A kid from the pretzel stand, still in his paper hat.",
  shots=[(0, 'zname', dict(who='shopper', label='SHOPPER · LEVEL 1', bg='mall')), ('@security', 'zname', dict(who='mike', label='MALL SECURITY', bg='mall')),
         ('@kid', 'zname', dict(who='pretzel', label='PRETZEL PALACE · 16', bg='mall'))])
N('M4b', "They were shopping when it started.", 0.35, "Some of them are still holding the bags.", gap=0.6, shot=('atrium', dict(mode='fountain')))
N('M5', "The window was on the top floor.", 0.35, "The escalators stopped when the power did.", shot=('escalator', dict(mode='side')))
N('M6', "A stopped escalator is just stairs.", 0.3, "Loud stairs.", 0.3, "Metal.")
N('M7', "You walk on the edges.", 0.3, "Where the steps are bolted down.", shot=('escalator', dict(mode='feet')))
BEAT('M7b', 4.0, shot=('escalator', dict(mode='pov')), caps=[(0.3, 1.8, 'a clank'), (2.0, 3.8, 'thunder covers it')],
     sfx=[(0.5, 'escalator_clank', {}), (1.9, 'thunder', {})])
N('M7c', "Level two.", 0.3, "A toy store.", 0.3, "Every teddy bear still in the window.", shot=('atrium', dict(mode='climb', level=2)))
N('M7d', "Level three.", 0.3, "The cinema.", 0.3, "The poster still says coming soon.", gap=0.6, shot=('atrium', dict(mode='climb', level=3)), music=('humor', {}))
N('M8', "Top floor.", 0.3, "A store called Bright Tech.", 0.3, "The lantern is in the window.", music=('think', {}),
  shot=('brighttech', dict(mode='front', hud=MALL(10, '2:41 PM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('M9', "Nobody's there.", gap=0.5, shot=('brighttech', dict(mode='inside')))
N('M10', "A sleeping bag.", 0.3, "Two backpacks.", 0.3, "A solar panel taped to the glass.", shot=('brighttech', dict(mode='camp')))
N('M10b', "And a desk lamp, wired to the panel.", 0.35, "That's the light you've been watching all week.", gap=0.5)
BEAT('M10c', 2.0, caps=[(0.2, 1.8, 'rain on the glass')])
N('M11', "Then something cold touches the back of your neck.", gap=0.3, music=('stop', {'fade': 0.15}),
  shot=('nora', dict(mode='behind')), sfx=[('$-0.3', 'tok', dict(level=-14))])
NORA('M12', "Don't.", 0.5, "Move.", gap=0.7)
N('M13', "It's a fire extinguisher.", 0.3, "Held by a girl.", 0.3, "Fifteen.", 0.3, "Maybe.", music=('tender', {}),
  shot=('nora', dict(mode='reveal')))
NORA('M14', "You're the Freshway guy.", gap=0.5, shot=('nora', dict(mode='close', expr='serious')))
N('M15', "She knows you.", gap=0.4, shot=('hclose2', dict(expr='surprised', bg='brighttech')))
NORA('M16', "I've been listening to you.", 0.35, "Every night.", 0.35, "Channel three.", shot=('nora', dict(mode='radio')))
HERO('M16b', "Then why didn't you say something?", gap=0.5, shot=('hclose2', dict(expr='worried', bg='brighttech', look=0.2)))
NORA('M16c', "My button's broken.", 0.4, "I can hear.", 0.3, "I can't talk.", gap=0.6, shot=('nora', dict(mode='radio', broken=True)))
N('M16d', "So she used the light.", 0.35, "And a page of Morse code from the bookstore on level two.", gap=0.6)
N('M17', "Rule three.", 0.35, "Count the radios.", 0.4, "There are three.", gap=0.8,
  shot=('card2', dict(kind='radios3')), sfx=[(0, 'whoosh', {})])
NORA('M17b', "Rate your day, one to ten.", 0.4, "Every single night.", gap=0.5, shot=('nora', dict(mode='close', expr='smirk')), music=('humor', {}))
N('M17c', "She does a pretty good Dale.", gap=0.7, shot=('hclose2', dict(expr='smile', bg='brighttech')))

# ======================= ACT 3 · DAY 10 · NORA =======================
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
N('N10b', "You think about the batteries.", 0.35, "Somebody keeps putting new ones in that clock.", shot=('prop2', dict(item='clock12', mode='still')))
N('N11', "The candy wrapper.", 0.4, "Sour worms.", gap=0.6, shot=('prop2', dict(item='wrapper')), sfx=[(0.1, 'low_sting', {})])
N('N11b', "Somebody small.", 0.4, "Who likes sour worms.", gap=0.8)
N('N12', "Then Nora's radio clicks.", 0.35, "Not channel three.", 0.3, "Channel four.", music=('stop', {'fade': 0.6}), shot=('nora', dict(mode='radio')), sfx=[(0.0, 'radio_click', {})])
DALE('N13', "Nora?", 0.5, "Honey?", 0.5, "Are you there?", gap=0.6)
N('N14', "Nora goes white.", gap=0.5, shot=('nora', dict(mode='close', expr='shock')))
NORA('N15', "That's my dad.", gap=0.9)
N('N16', "Dale is her father.", gap=0.8, music=('twist', {}), shot=('hclose2', dict(expr='surprised', bg='brighttech', look=0.1)), sfx=[(0, 'low_sting', {})])
BEAT('N16x', 2.2, shot=('nora', dict(mode='close', expr='sad')))
NORA('N16b', "Channel four is ours.", 0.35, "He calls every night.", 0.4, "And I can't answer.", gap=0.7, shot=('nora', dict(mode='close', expr='sad')))
N('N16c', "Mall security.", 0.3, "That part was true.", 0.4, "He just wasn't at the mall.", gap=0.6)
N('N17', "He asked how many of you there were.", 0.35, "He asked about the freezer.", 0.35, "He asked about the alarm.",
  shot=('card2', dict(kind='clues')))
N('N18', "He wasn't counting your food.", 0.35, "He was looking for his son.", gap=0.7, shot=('stockdoors', dict(mode='shadow')))
N('N19', "Rule four works both ways.", 0.35, "Dale never told you what he has.", shot=('hclose2', dict(expr='determined', bg='brighttech')))
N('N20', "He has a son.", 0.4, "Somewhere inside Freshway.", gap=0.8, shot=('freshroof', dict(mode='figure')))
N('N20b', "And now you know where his daughter is.", gap=0.8)
NORA('N21', "Take me back with you.", 0.5, "Please.", gap=1.0, shot=('nora', dict(mode='close', expr='serious')))

# ======================= DAY 12 · THE RECEIPT =======================
N('D1', "Day twelve.", 0.35, "The lot fills up again.", 0.35, "You wait for a plan.", music=('tender', {}), amb='mall_quiet',
  shot=('nora', dict(mode='window', empty=True, crowd=True, hud=MALL(12, '6:40 PM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('D2', "Nora has rules too.", 0.35, "She wrote them on the back of a receipt.", shot=('card2', dict(kind='receipt')))
N('D3', "Never sleep on the ground floor.", 0.35, "Shoes off on the escalator.", 0.4, "And the sour worms are for Leo.", gap=0.7)
N('D4', "She's been saving one bag for twelve days.", gap=1.0, shot=('nora', dict(mode='window', bag=True)))
N('D5', "At two thirty-one, the alarm rings across the street.", music=('stop', {'fade': 1.0}), amb='mall_quiet',
  shot=('nora', dict(mode='window', bag=True, hud=MALL(12, '2:31 AM', 1, 'BROOKFIELD MALL · LEVEL 4'))), sfx=[(0.4, 'alarm_far', dict(until='D8', off=1.0, level=-24))])
N('D6', "Faint.", 0.4, "Like a phone ringing in another room.", gap=0.8)
NORA('D7', "Hi, Leo.", gap=1.4, shot=('nora', dict(mode='close', expr='sad')))
N('D8', "She says it every night.", gap=1.0)

# ======================= ACT 3 · DAY 13 · THE SONG =======================
N('S1', "Day thirteen.", 0.35, "One in the morning.", 0.35, "Time to go home.", 0.3, "Both of you.", music=('plan', {}), amb='mall_quiet',
  shot=('brighttech', dict(mode='lantern', two=True, day=True, hud=MALL(13, '1:05 AM', 1, 'BROOKFIELD MALL · LEVEL 4'))))
N('S2', "No storm.", 0.3, "No clocks.", 0.3, "Just two hundred of them in the lot.", shot=('lot', dict(mode='count', time='night', hud=H(13, '1:10 AM', 1, 'FRESHWAY · PARKING LOT'))))
N('S3', "Nora has an idea.", 0.35, "Bright Tech sells drones.", shot=('drone', dict(mode='box')))
N('S4', "And a speaker that clips onto anything.", shot=('drone', dict(mode='clip')), sfx=[('$-0.3', 'tok', {})])
N('S4b', "Every time you double the distance, a sound gets about six decibels quieter.",
  shot=('card', dict(kind='fact', big='-6', unit='DECIBELS', icon='speaker', note='EVERY TIME THE DISTANCE DOUBLES', src='INVERSE SQUARE LAW · SOUND IN OPEN AIR')), music=('think', {}))
N('S4c', "So the song has to go far.", 0.35, "And you have to stay very quiet.", gap=0.6)
N('S5', "Rule two.", 0.3, "Music is a dinner bell.", 0.4, "This time, you ring it on purpose.", gap=0.6,
  shot=('card', dict(kind='rule', n=2, lines=['MUSIC IS A', 'DINNER BELL.'], icon='note')), sfx=[(0, 'whoosh', {})])
N('S5b', "The box says thirty minutes of flight.", 0.35, "That's the plan's clock.", shot=('drone', dict(mode='box')))
N('S6', "Nora has one song on her phone.", 0.35, "Guess which one.", gap=0.5, music=('stop', {'fade': 0.4}), shot=('nora', dict(mode='close', expr='smirk')))
BEAT('S7', 9.0, shot=('drone', dict(mode='fly')), amb='lot_night',
     caps=[(0.3, 3.6, 'the Freshway jingle'), (4.0, 8.6, 'two hundred of them, turning')],
     sfx=[(0, 'drone_buzz', dict(until='S8g', off=0.3)), (0.6, 'drone_song', dict(until='S8g', off=0.0))])
N('S8', "Two hundred dead people follow a song about discount yogurt.", 0.35, "To the far end of the lot.",
  shot=('drone', dict(mode='lot', battery=[64, 40])))
N('S8b', "You go down the escalator.", 0.3, "Shoes in your hands.", shot=('escalator', dict(mode='side', two=True)))
N('S8c', "Out the side door.", 0.3, "Past the broken glass.", 0.3, "Into the lot.", shot=('malldoor', dict(mode='broken', hud=MALL(13, '1:31 AM', 2, 'BROOKFIELD MALL · SIDE DOOR'))))
BEAT('S8d', 3.0, shot=('drone', dict(mode='lot', battery=[22, 12], far=True)), caps=[(0.2, 2.8, 'the jingle, far away')])
N('S8e', "Then the drone beeps.", 0.4, "Low battery.", shot=('drone', dict(mode='lot', battery=[10, 4], far=True)), sfx=[('@beeps', 'drone_beep', {}), ('$', 'drone_beep', {})])
N('S8f', "Twelve minutes early.", 0.35, "Cheap drone.", gap=0.5)
N('S8g', "The song stops.", 0.4, "Two hundred heads turn back toward the store.", shot=('lot', dict(mode='turn', time='night')), sfx=[(0.6, 'crowd_surge', dict(dur=3.0, level=-18))])
N('S9', "You run for the staff door.", 0.3, "Gary's keys.", 0.3, "The fourth one.", 0.35, "You remember this time.",
  music=('chase', {}), shot=('staffdoor', dict(mode='arrive', nora=True, hud=H(13, '1:42 AM', 3, 'FRESHWAY · STAFF DOOR'))), sfx=[(0, 'run_steps', dict(dur=3.0)), ('@fourth', 'lock_click', {})])
N('S10', "You're in.", 0.35, "Both of you.", gap=0.8, music=('stop', {'fade': 0.4}), amb='store_dark',
  shot=('staffdoor', dict(mode='inside', nora=True)), sfx=[('@in', 'door_bang', {})])
BEAT('S10x', 2.5, caps=[(0.2, 2.3, 'two people, breathing')], sfx=[(0.1, 'breath_run', dict(dur=2.3, level=-22))])

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
N('F10', "Dale doesn't answer.", 0.4, "For a long time, the radio just hisses.", gap=0.8, shot=('radio', dict(mode='belt')))
DALE('F10b', "I've looked everywhere, honey.", 0.6, "Every night.", 0.6, "I count to a hundred.", 0.4, "And I look.", gap=0.9, rate=2.2, shot=('radio', dict(mode='doors', night=True)), music=('tender', {}))
NORA('F10c', "It's his favorite game.", 0.4, "He always hides.", 0.4, "You always find him.", gap=1.0, shot=('nora', dict(mode='close', expr='sad', bg='store')))
N('F11', "Two thirty-one.", gap=0.3, shot=('prop2', dict(item='clock12', mode='still')), music=('stop', {'fade': 0.5}))
N('F12', "The alarm in aisle twelve starts to ring.", shot=('prop2', dict(item='clock12', mode='ring')), sfx=[(0, 'alarm_near', dict(until='F13', off=1.4, level=-23))])
N('F13', "Nora runs.", gap=0.6, shot=('aisle2', dict(mode='nora_run')), sfx=[(0, 'run_steps', dict(dur=2.2, level=-16))])
N('F14', "Next to the clock, there's a drawing.", 0.35, "In crayon.", shot=('prop2', dict(item='drawing', mode='reveal')), sfx=[(0.1, 'paper_rustle', {})], music=('sting_mystery', {}))
N('F15', "A girl.", 0.3, "A man in a cap.", 0.3, "And you.", 0.35, "Orange headphones and all.", shot=('prop2', dict(item='drawing', mode='close')))
N('F16', "Under it, three words.", 0.6, "Come find me.", gap=0.8, shot=('prop2', dict(item='drawing', mode='words')))
BEAT('F16x', 2.0)
N('F17', "Leo is alive.", 0.35, "He's in this store.", 0.4, "And they don't see you.", 0.5, "But he does.", gap=1.4,
  shot=('povaisle', dict(phase='vent', eyes='@does')), music=('end', {}))
BEAT('END', 11.3, shot=('card', dict(kind='end', day=15, ep=3, title='LIGHTS OUT', sub='WHERE IS LEO?')), amb='silence')
