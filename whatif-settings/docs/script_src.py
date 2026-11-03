# Master script for "What If Real Life Had a SETTINGS MENU?". One row per spoken line:
#   (scene, role, tag, text, picture)
# role: N narrator, SYS settings voice, SAM, LILY, MOM, DAD, PICKLES, BRIGGS, KEVIN
# tag : the delivery. For N it is HYPE or DEADPAN (the two narrator registers); for characters an emotion.
# Run: python3 -I docs/script_src.py  -> docs/script.tsv, docs/SCRIPT.md, docs/voices/*.md|txt, docs/stats.txt
import os, re, json

S = []
def L(scene, role, tag, text, pic=''):
    S.append(dict(scene=scene, role=role, tag=tag, text=text, pic=pic))

# ---------------------------------------------------------------- COLD OPEN
# Pictures marked [drop] stop the music dead on the punchline; it slams back on the next line.
c = 'S00 COLD OPEN'
L(c, 'N', 'HYPE', 'What if real life had a SETTINGS menu?', 'Sam\'s thumb drags a DOG SIZE slider: the neighbour\'s dog grows to the size of a house')
L(c, 'N', 'HYPE', 'One app.', 'The gear app icon zooms at the lens; a second slider flips a tree upside down')
L(c, 'N', 'HYPE', 'Total control.', 'Our DAY card flips 1 to 7; sliders and toggles fan across the screen')
L(c, 'N', 'DEADPAN', 'No undo.', 'An UNDO button cracks and falls off the screen')
L(c, 'SYS', 'calm', 'Factory reset in one minute.', 'Flash-forward, Day 7: the sky is a loading bar; Mom and Dad flicker into grey mannequins with DEFAULT tags; red countdown pill 1:00')
L(c, 'SAM', 'nervous', 'In my defense... I only changed ONE thing.', 'Sam to camera, sweat drop growing')
L(c, 'SYS', 'calm', 'Changes made by you: four hundred and twelve.', 'A counter rolls 1 to 412 beside his head')
L(c, 'SAM', 'guilty', '...Ish.', 'Tiny shrug, guilty half-lid eyes [drop]')
L(c, 'N', 'DEADPAN', "Let's scroll back... seven days.", 'Our UNDO HISTORY panel: 412 changes scroll back at speed, day icons blurring past')
L(c, 'N', 'DEADPAN', 'Bedtime. Supposedly.', "Sam under his blanket at 2:13 a.m., phone glow on his face, moonlight")
L(c, 'N', 'HYPE', 'An app you never downloaded.', 'The phone rattles; a gear icon: SETTINGS - for real life')
L(c, 'N', 'DEADPAN', 'First, the terms and conditions.', 'T&C card, page counter 1 / 4,812')
L(c, 'N', 'DEADPAN', 'Four thousand, eight hundred and twelve pages.', 'Pages stack up past the ceiling')
L(c, 'N', 'HYPE', 'So you read every word...', 'Sam squints seriously at page one')
L(c, 'N', 'HYPE', '...in half a second.', 'One flick, whoosh; for 3 frames the fine print of page 4,812 is readable (the rule that saves Day 7)')
L(c, 'N', 'HYPE', '...and press I AGREE.', 'Big green button; sub boom; a ripple spreads out: room, house, street')
L(c, 'SYS', 'cheerful', 'Welcome to Reality Settings!', 'Toast slides in, the gear glows')
L(c, 'SAM', 'yawning', 'Prove it.', 'Sam mid-yawn, unimpressed')
L(c, 'N', 'HYPE', 'You open Brightness.', 'Brightness slider fills the screen')
L(c, 'N', 'HYPE', 'Slide it up. Just a little.', 'The moon outside flares into a sun; the room blows out white; birds wake up and sing')
L(c, 'DAD', 'shouting', 'Who turned on the SUN?!', 'Down the hall, Dad in pyjamas, shielding his eyes')
L(c, 'N', 'HYPE', "That's not the PHONE's brightness.", 'Sam slowly lowers the phone, star eyes fading to fear')
L(c, 'N', 'DEADPAN', "That's the planet's.", 'Snap zoom out to space: one side of Earth glowing like a lamp [drop]')

# ---------------------------------------------------------------- DAY 1
c = 'S01 DAY 1 - JUST TESTING'
L(c, 'N', 'HYPE', 'Day one.', 'DAY 1 card slams in')
L(c, 'MOM', 'yelling', 'SAM! UP! NOW!', 'Mom in the doorway, mid-yell, label maker in hand')
L(c, 'N', 'HYPE', 'You find Snooze...', 'SNOOZE (unlimited)')
L(c, 'N', 'DEADPAN', '...for Mom.', 'A target lock on Mom\'s head')
L(c, 'N', 'DEADPAN', 'And Mom... waits.', 'Tap: Mom freezes mid-yell; a fly freezes on her nose; Sam snuggles back into bed')
L(c, 'N', 'DEADPAN', 'Nine minutes. Then nine more.', 'Snooze pill: 9:00, 9:00, 9:00')
L(c, 'N', 'DEADPAN', 'Then ninety more.', 'Mom still frozen, dust specks hanging in a sunbeam [drop]')
L(c, 'N', 'HYPE', 'Breakfast.', 'Kitchen, morning light')
L(c, 'N', 'DEADPAN', 'Lily is awake.', 'Lily at the table, inhaling')
L(c, 'LILY', 'shouting', 'I WANT THE BLUE SPOON!', "Glasses rattle, Pickles flattens his ears, Dad's moustache blows back")
L(c, 'N', 'HYPE', 'You find Volume.', 'Volume list: Dad, Mom, Lily, Pickles, Kevin next door')
L(c, 'N', 'DEADPAN', 'And slide her... to zero.', 'A mute badge pops over Lily; she keeps screaming silently; the music mutes with her [drop]')
L(c, 'MOM', 'relieved', 'Why is it so... peaceful?', 'Mom sips tea, eyes closed, sparkles; Lily silently dancing on her chair')
L(c, 'N', 'DEADPAN', 'Best breakfast of your life.', 'Sam eats cereal in slow, happy bliss')
L(c, 'N', 'HYPE', 'Next: Subtitles.', 'Toggle: SUBTITLES: HONEST')
L(c, 'N', 'HYPE', 'Honest mode: on.', 'A boxed subtitle bar appears under every person (in-world style, not our captions)')
L(c, 'DAD', 'warm', 'Morning, champ!', "Dad's subtitle: [I forgot his name for a second]")
L(c, 'SAM', 'deadpan', '...You forgot my name.', 'Sam stares; Dad sweats')
L(c, 'DAD', 'nervous', 'Pfft. No. ...Steve!', 'Subtitle: [guessed] [drop]')
L(c, 'N', 'HYPE', 'Then Gravity.', 'A planet dial: EARTH')
L(c, 'N', 'HYPE', 'Earth... Moon.', "Click; Dad's coffee lifts out of his mug as a wobbling brown blob")
L(c, 'N', 'HYPE', 'You get to school in four steps.', 'Sam bounds over rooftops, one boing per step')
L(c, 'N', 'DEADPAN', 'Then Dad sneezes...', 'Dad, nose twitching, on the front lawn')
L(c, 'DAD', 'panic falsetto', 'BLESS MEEEEE!', 'Dad rockets up past the chimney (Doppler fade)')
L(c, 'N', 'HYPE', 'Day one. Changes made: five.', 'Counter toast: 5')
L(c, 'N', 'DEADPAN', 'Totally under control.', 'Dad drifts past the window beside the goldfish in its floating water ball [drop]')

# ---------------------------------------------------------------- DAY 2
c = 'S02 DAY 2 - THE RULES'
L(c, 'N', 'HYPE', 'Day two.', 'DAY 2 card')
L(c, 'N', 'HYPE', 'You find Difficulty.', 'Difficulty selector: EASY / NORMAL / HARD')
L(c, 'N', 'HYPE', 'Easy, for homework.', 'The pencil writes by itself; A+ stamps rain down')
L(c, 'N', 'DEADPAN', 'But Lily finds your phone.', 'Lily, still muted (tiny grey subtitle: [i want the blue spoon]), grins with the phone')
L(c, 'N', 'DEADPAN', 'And sets the laundry to HARD.', 'The laundry pile turns into a boss: health bar LAUNDRY MOUNTAIN')
L(c, 'N', 'DEADPAN', 'Dad is still on sock three.', 'Dad wrestling one sock, his own health bar at 12%')
L(c, 'DAD', 'exhausted', 'Tell your mother... I loved her.', 'Dad faints dramatically into the laundry')
L(c, 'N', 'HYPE', 'That night, the app updates.', 'A PATCH NOTES card unrolls (counter toast 31, silent)')
L(c, 'SYS', 'cheerful', 'Patch notes. Version one point one.', 'Gear spins, confetti')
L(c, 'SYS', 'calm', 'Rule one. Your changes affect... everyone.', 'A ring expands from Sam over the whole town')
L(c, 'N', 'HYPE', 'So you pick: Snow Day.', 'Weather picker: SNOW DAY')
L(c, 'N', 'HYPE', 'Everyone gets one. In July.', 'Snow bursts over every house; kids cheer in shorts')
L(c, 'KEVIN', 'angry', 'MY LAWN!', 'Kevin on his knees in the snow, leaf blower in hand')
L(c, 'SYS', 'calm', 'Rule two. There is no undo.', 'An UNDO button greys out and crumbles')
L(c, 'N', 'DEADPAN', 'You press undo anyway.', 'Sam jabbing the empty spot')
L(c, 'SYS', 'cheerful', 'Did you mean: more snow?', "A second drift buries Kevin up to his sunglasses [drop]")
L(c, 'SYS', 'calm', 'Rule three. Everything resets at midnight.', 'A midnight clock icon')
L(c, 'N', 'HYPE', 'Perfect. A free trial!', 'Sam punches the air')
L(c, 'N', 'HYPE', 'Midnight comes.', 'The family in pyjamas staring at the kitchen clock: 11:59... 12:00')
L(c, 'N', 'DEADPAN', 'Nothing resets.', 'Lily still muted, snow still falling, homework still writing itself')
L(c, 'SYS', 'cheerful', 'Update one point two. Rule three has been removed.', 'A red REMOVED stamp slams on rule three')
L(c, 'SAM', 'outraged', "You can't just REMOVE a rule!", 'Sam shouting at the phone, lurching at the lens')
L(c, 'SYS', 'cheerful', 'Rule four. I can.', 'Rule four types itself, cursor blinking [drop]')

# ---------------------------------------------------------------- DAY 3
c = 'S03 DAY 3 - 2X SPEED'
L(c, 'N', 'HYPE', 'Day three.', 'DAY 3 card, then the classroom')
L(c, 'N', 'DEADPAN', 'Mr. Briggs starts the lesson.', 'Briggs at the board, chalk squeak')
L(c, 'BRIGGS', 'monotone', 'Today... we will discuss... the history of the paperclip.', "Every student falls asleep, Z's rise")
L(c, 'N', 'HYPE', 'So you find Playback Speed.', 'A speed control: 0.5x 1x 2x')
L(c, 'N', 'HYPE', 'Two times.', '2x: Briggs becomes a blur, chalk flying, the wall clock spinning; the music plays at 2x too')
L(c, 'BRIGGS', 'fast', 'And that is why the paperclip changed everything, any questions, no, good!', 'We speed this line up to chipmunk')
L(c, 'N', 'HYPE', 'Lunch?', 'Cafeteria')
L(c, 'N', 'DEADPAN', 'Nine fifteen.', 'Clock 9:15, kids eating at double speed')
L(c, 'N', 'HYPE', 'Recess?', 'Playground')
L(c, 'N', 'DEADPAN', 'Four seconds.', 'Kids blur across the playground and back')
L(c, 'N', 'HYPE', 'Then a pop quiz.', 'A quiz paper slaps onto the desk')
L(c, 'N', 'HYPE', 'You skip... to the end.', 'The paper fast-forwards to the last page')
L(c, 'N', 'DEADPAN', 'Score: skipped.', 'A red SKIPPED stamp')
L(c, 'BRIGGS', 'stern', 'Detention.', 'Normal speed again; record scratch; his glasses flash [drop]')
L(c, 'N', 'HYPE', 'You try to fast-forward detention...', 'Sam jabs the speed control')
L(c, 'N', 'DEADPAN', '...and press half speed.', '0.5x: the clock hands crawl; the music drags at half speed')
L(c, 'SAM', 'slow-motion despair', 'Noooooo...', 'We slow this line down; Sam melts onto the desk in slow motion')
L(c, 'N', 'DEADPAN', 'Detention ends. Eventually.', 'Sam walking home, aged, with a long beard of dust that falls off (counter toast 89, silent)')
L(c, 'N', 'HYPE', 'At home, you find the best button ever made.', 'A glowing button rises: SKIP INTRO')
L(c, 'DAD', 'storytelling', 'Did I ever tell you about the summer of nineteen ninety—', 'Dad on the couch, starting a story')
L(c, 'N', 'HYPE', 'Skip intro.', 'Tap, whoosh: Dad jumps forward')
L(c, 'DAD', 'storytelling', '—and that is why I can never go back to the water park.', 'Dad finishes, satisfied; Sam nods')
L(c, 'KEVIN', 'smug', 'So this is a premium fertilizer blend—', 'Kevin leaning on the fence, sunglasses glinting')
L(c, 'N', 'DEADPAN', 'Skip ad.', 'Tap: Kevin vanishes mid-sentence with a pop [drop]')

# ---------------------------------------------------------------- DAY 4
c = 'S04 DAY 4 - LANGUAGE'
L(c, 'N', 'HYPE', 'Day four.', 'DAY 4 card')
L(c, 'N', 'HYPE', 'Somebody changes the language.', 'A town-wide toast: LANGUAGE changed by: unknown user')
L(c, 'N', 'DEADPAN', 'To emoji.', "Every speech bubble in town turns into our own emoji; Lily's bubble is twenty blue spoons")
L(c, 'N', 'HYPE', 'Mom is fluent in seconds.', 'Mom firing emoji bubbles at machine-gun speed, smug')
L(c, 'N', 'DEADPAN', 'Dad is not.', "Dad's bubble: duck, bread, question mark")
L(c, 'SAM', 'deadpan', 'Dad. You just said "duck bread."', 'Sam flat-eyed')
L(c, 'DAD', 'proud', 'And I stand by it.', 'Dad crosses his arms [drop]')
L(c, 'N', 'HYPE', 'So you try to fix it.', 'Sam scrolling a language list')
L(c, 'N', 'HYPE', 'Pirate?', 'Tap: PIRATE; Dad gets an eye patch')
L(c, 'DAD', 'pirate', 'Arr. Duck bread.', 'Dad with eye patch')
L(c, 'N', 'HYPE', 'Robot?', 'Tap: ROBOT; Dad goes stiff, eyes square')
L(c, 'DAD', 'robot', 'DUCK. BREAD.', 'We add a robot filter')
L(c, 'N', 'DEADPAN', '...and your thumb slips.', 'Slow motion: the thumb lands on CAT')
L(c, 'N', 'DEADPAN', 'Language: Cat.', 'The whole town meows; then Pickles turns to camera')
L(c, 'PICKLES', 'bored posh', 'Finally.', 'Pickles, half-lidded, on the counter')
L(c, 'PICKLES', 'bored posh', 'I have so many complaints.', 'A scroll of complaints unrolls to the floor')
L(c, 'PICKLES', 'bored posh', 'One. The food. Is beige.', 'He pushes his bowl off the counter')
L(c, 'PICKLES', 'bored posh', 'Two. I watch you sleep. Every night.', "Sam's face drains white")
L(c, 'SAM', 'scared', 'WHY?!', 'Sam lurches at the lens')
L(c, 'PICKLES', 'bored posh', 'Three. That is none of your business.', 'Pickles licks one paw [drop]')
L(c, 'N', 'DEADPAN', 'You fix the language. Mostly.', 'Everyone speaks normally again; Pickles slowly turns to camera (counter toast 130, silent)')

# ---------------------------------------------------------------- DAY 5
c = 'S05 DAY 5 - GRAPHICS LOW'
L(c, 'N', 'HYPE', 'Day five.', 'DAY 5 card')
L(c, 'N', 'HYPE', 'Your battery?', 'Phone in hand')
L(c, 'N', 'DEADPAN', 'One percent.', 'Battery icon blinking red')
L(c, 'SYS', 'calm', 'Battery saver on. Lowering reality graphics.', 'A slider crawls down: ULTRA, HIGH, LOW')
L(c, 'N', 'DEADPAN', 'And the world... gets cheap.', 'Everything pixelates; trees become flat cardboard cut-outs; the music turns 8-bit')
L(c, 'N', 'DEADPAN', 'The birds are just... the letter V.', 'Birds become little v shapes flapping')
L(c, 'N', 'HYPE', 'Mom?', 'Kitchen')
L(c, 'N', 'DEADPAN', 'Has corners.', "Mom's head is an octagon")
L(c, 'MOM', 'offended', 'Do NOT look at me.', 'Mom hiding her octagon face behind a pixel mug')
L(c, 'PICKLES', 'bored posh', 'I look magnificent in any resolution.', 'Pickles, perfectly smooth, reading the terms at page 2,113 of 4,812 [drop]')
L(c, 'N', 'HYPE', 'Render distance: one driveway.', 'A white wall of nothing past the end of the driveway')
L(c, 'N', 'HYPE', 'Dad walks to the mailbox...', 'Dad strolling into the white')
L(c, 'N', 'DEADPAN', '...and stops existing.', 'He fades into the white mid-step')
L(c, 'N', 'DEADPAN', 'He comes back... holding a duck.', 'Dad walks back out of the white with a duck and a loaf of bread')
L(c, 'DAD', 'deadpan', 'Duck. Bread. I stand by it.', 'The duck quacks [drop]')
L(c, 'N', 'HYPE', 'So you plug in your phone. Graphics: ULTRA.', 'Charging bolt, the slider slams to ULTRA')
L(c, 'N', 'DEADPAN', 'Now everything is too real.', "Ultra-detailed close-ups: Pickles' eye, Lily's gap tooth gleaming")
L(c, 'N', 'DEADPAN', "You can see every pore on Dad's nose.", "A slow, horrifying push into Dad's nose")
L(c, 'N', 'DEADPAN', 'Every. Single. One.', 'Three snap zooms, closer each time')
L(c, 'SAM', 'disgusted', 'Put it back. PUT IT BACK!', 'Sam gagging, slamming the slider back to normal (counter toast 206, silent)')

# ---------------------------------------------------------------- DAY 6
c = 'S06 DAY 6 - OTHER USERS'
L(c, 'N', 'HYPE', 'Day six.', 'DAY 6 card')
L(c, 'N', 'HYPE', 'You open the app...', 'Notifications start stacking')
L(c, 'SYS', 'cheerful', 'Kevin changed GRASS to: gold.', "Kevin's lawn turns to shining gold; the street squints")
L(c, 'N', 'HYPE', 'Kevin?', 'Kevin on his golden lawn')
L(c, 'N', 'DEADPAN', 'Has the app.', 'Kevin smug, phone in hand')
L(c, 'KEVIN', 'smug', 'Why do you think I wear sunglasses?', 'His sunglasses flare off the gold [drop]')
L(c, 'SYS', 'cheerful', 'LilyRoar changed GRAVITY to: bouncy.', 'The whole family bounces like rubber balls')
L(c, 'N', 'DEADPAN', 'Lily has the app.', 'Lily bouncing, still muted, delighted')
L(c, 'SYS', 'calm', 'Mom turned on Parental Controls.', "All of Sam's settings grey out with locks: ASK A PARENT")
L(c, 'N', 'DEADPAN', 'And Mom has had it... since one minute after you.', "Flashback tint: Mom in her robe at 2:14 a.m. pressing I AGREE; her change log: Lily volume LOCKED, Sam bedtime 8:00, Language: emoji")
L(c, 'MOM', 'sweet smug', 'Who do you think set your bedtime to eight?', 'Mom sips her tea')
L(c, 'SAM', 'outraged', 'I THOUGHT I WAS JUST TIRED!', 'Sam explodes, steam from his ears [drop]')
L(c, 'N', 'HYPE', 'Now everyone changes everything.', 'Split screens multiplying')
L(c, 'SYS', 'cheerful', 'Mr. Briggs set every channel to: paperclips.', 'Every TV in town shows a paperclip documentary')
L(c, 'N', 'HYPE', "The sun can't decide if it's day.", 'Day and night strobing over the street')
L(c, 'N', 'HYPE', 'Half the street is in winter.', 'A perfect line: snow on the left, summer on the right')
L(c, 'N', 'DEADPAN', "Dad's subtitles are in four languages.", 'Four stacked bars under Dad: [Steve] [Esteban] [Stefan] [Stefano]')
L(c, 'SYS', 'calm', 'Reality storage... almost full.', 'The counter flashes red at 400')
L(c, 'N', 'HYPE', 'Then Dad borrows your phone.', 'UPDATE AVAILABLE: Reality 2.0. [Later] [Install]')
L(c, 'DAD', 'casual', 'I always press later.', "Dad's thumb hovering")
L(c, 'N', 'DEADPAN', 'He presses install.', 'Tap. Freeze frame. Sub boom. [drop]')
L(c, 'SYS', 'calm', 'Installing Reality two point oh.', 'The sky becomes a giant progress bar at 1%')
L(c, 'N', 'DEADPAN', 'Day six. Your changes: four hundred and eleven.', 'Counter toast: 411, red, one slot left')

# ---------------------------------------------------------------- DAY 7
c = 'S07 DAY 7 - FACTORY RESET'
L(c, 'N', 'HYPE', 'Day seven.', 'DAY 7 card, red; the sky bar at 99%')
L(c, 'MOM', 'yelling', 'SAM! UP! NOW!', 'The same shot and the same take as Day 1')
L(c, 'N', 'HYPE', 'You hit snooze...', 'Sam slaps the phone half asleep')
L(c, 'N', 'DEADPAN', '...but the update moved the buttons.', 'The button under his thumb says FACTORY RESET; the counter ticks 411 to 412')
L(c, 'SYS', 'calm', 'Factory reset in one minute.', 'Same shot as the cold open; countdown pill 1:00')
L(c, 'SYS', 'cheerful', 'Please do not turn off reality.', 'A spinning save icon in the corner of the sky')
L(c, 'SAM', 'defensive', 'See? ONE thing.', 'Sam to camera, framed exactly like the cold open')
L(c, 'N', 'HYPE', 'Everything goes back to default.', 'Settings fly back to their default positions')
L(c, 'N', 'DEADPAN', 'Including your family.', 'Dad turns grey and plastic, a DEFAULT tag on his shirt')
L(c, 'DAD', 'flat default', 'Hi. Do I... know you?', 'Default Dad, blank smile, no moustache [drop]')
L(c, 'SAM', 'determined', "Where's the CANCEL button?!", 'Sam tearing through the menu')
L(c, 'N', 'HYPE', 'Fifty seconds.', 'The dial pops: 50')
L(c, 'N', 'HYPE', 'You try half speed.', 'Speed control: 0.5x (callback)')
L(c, 'SYS', 'slowed', 'Fooorty... fiiive...', 'We slow this line down; the dial creeps')
L(c, 'SYS', 'cheerful', 'Nice try.', 'Back to full speed with a snap')
L(c, 'N', 'HYPE', 'You try undo.', 'Sam taps the empty corner again (callback)')
L(c, 'SYS', 'cheerful', 'Rule two.', 'Rule two card flashes')
L(c, 'N', 'HYPE', 'Forty seconds.', 'Dial: 40')
L(c, 'N', 'HYPE', 'Wait. The terms!', 'Sam freezes, star eyes')
L(c, 'PICKLES', 'bored posh', 'Page four thousand, eight hundred and twelve. Ahem.', 'Pickles closes the last page of the stack he has read all week')
L(c, 'SYS', 'calm', 'A reset can only be stopped by the loudest person in the house.', 'The fine print from the cold-open flash fills the screen')
L(c, 'N', 'HYPE', 'The loudest person in the house...', 'Every head slowly turns toward Lily')
L(c, 'N', 'DEADPAN', '...is muted.', 'Lily, mute badge, waving [drop]')
L(c, 'N', 'HYPE', 'Thirty seconds.', 'Dial: 30, music slams back in')
L(c, 'SAM', 'panic', 'Unmute! UNMUTE!', "Sam grabs Lily's volume slider: it is locked")
L(c, 'SYS', 'calm', 'Locked by Parental Controls.', 'Padlock clamps shut on the slider')
L(c, 'MOM', 'hurried', "The password is your father's worst joke!", "Mom slaps down a label: DAD'S WORST JOKE")
L(c, 'N', 'DEADPAN', 'Luckily, dad jokes come pre-installed.', 'Default Dad blinks; his moustache pops back')
L(c, 'DAD', 'delighted', 'Why did the bike fall over? Well. Summer of nineteen ninety—', 'Dad settling in for a long story')
L(c, 'SAM', 'shouting', 'SKIP INTRO!', 'Sam slams the SKIP INTRO button (callback)')
L(c, 'DAD', 'quick', '—because it was TWO TIRED!', 'Password field: a bike with two tyres, green check; Mom groans')
L(c, 'N', 'HYPE', 'Ten seconds.', 'The pill turns red: 0:10')
L(c, 'N', 'HYPE', "You slide Lily's volume...", 'The slider races past 100')
L(c, 'N', 'HYPE', '...all the way past the end.', 'It breaks through the frame of the slider: 200%')
L(c, 'SYS', 'calm', 'Five. Four. Three...', 'Dial pops 5, 4, 3')
L(c, 'LILY', 'epic scream', 'I WANT THE BLUE SPOOOOON!', 'Shockwave; the reset window shatters like glass (callback)')
L(c, 'SYS', 'calm', 'Reset... cancelled.', 'Shards drift down in silence; one tinkle [drop]')
L(c, 'SYS', 'cheerful', 'Undo... unlocked.', 'An UNDO button grows back where it broke off')
L(c, 'N', 'HYPE', 'So you undo... everything.', 'The UNDO HISTORY panel plays forward; the counter rolls 412 down to 0')
L(c, 'N', 'HYPE', 'Gravity: normal. Snow: gone. Dad: on the ground.', 'Dad lands softly; the goldfish plops back into its bowl; the duck waddles off')
L(c, 'PICKLES', 'sigh', 'Pity.', "Pickles' last word in English, then: meow")
L(c, 'N', 'HYPE', "Dad's subtitles show one last line.", 'Dad turns to Sam')
L(c, 'DAD', 'warm quiet', 'Good job, kiddo.', 'Subtitle: [so proud of you, Sam]')
L(c, 'SAM', 'soft smile', '...You remembered my name.', 'Sam smiles, blush')
L(c, 'N', 'HYPE', 'Lily gets the blue spoon.', 'Lily holds the blue spoon up like a trophy')
L(c, 'LILY', 'tiny whisper', '...thank you.', 'The loudest kid whispers; Sam blinks')
L(c, 'N', 'DEADPAN', "And Kevin's lawn stays gold.", 'Kevin hugging his golden lawn [drop]')
L(c, 'N', 'HYPE', "If you had this menu, what's the ONE setting you would change?", 'A settings list with an empty row: YOUR IDEA')
L(c, 'N', 'HYPE', 'Tell me in the comments.', 'Comment icon pops')
L(c, 'N', 'HYPE', 'And this button right here...', 'An in-world toggle: SUBSCRIBE: OFF')
L(c, 'N', 'DEADPAN', "...is the only setting that's actually real.", 'The toggle flips ON with sparkles')

# ---------------------------------------------------------------- ENDING
c = 'S08 ENDING'
L(c, 'N', 'HYPE', 'That night, you delete the app.', 'UNINSTALL; ARE YOU SURE?')
L(c, 'SYS', 'cheerful', "You can't just delete me!", 'The gear shakes')
L(c, 'SAM', 'smug', 'Rule four. I can.', 'Tap YES; the gear dissolves into sparkles')
L(c, 'N', 'DEADPAN', 'Normal life. Finally.', 'Sam in bed, smiling; Pickles at the foot of the bed, eyes wide open')
L(c, 'N', 'DEADPAN', 'Bedtime. Supposedly.', 'The same 2:13 a.m. shot as the cold open; the phone buzzes')
L(c, 'SYS', 'cheerful', 'New app available. Reality Settings Two... now with TIME.', "A clock-gear icon; I AGREE glowing; Sam's thumb hovers")
L(c, 'SAM', 'sly', '...Just ONE thing.', 'Ding. Black.')

# ---------------------------------------------------------------- outputs
ROOT = os.path.dirname(os.path.abspath(__file__))
FISH = {'HYPE': 'excited', 'DEADPAN': 'calm', 'calm': 'calm', 'cheerful': 'happy', 'nervous': 'nervous', 'guilty': 'embarrassed', 'shouting': 'shouting',
        'relieved': 'relaxed', 'warm': 'happy', 'deadpan': 'indifferent', 'panic falsetto': 'panicked', 'angry': 'angry', 'outraged': 'angry', 'exhausted': 'sad',
        'monotone': 'indifferent', 'fast': 'hurried', 'storytelling': 'happy', 'smug': 'confident', 'stern': 'serious', 'slow-motion despair': 'sad',
        'proud': 'proud', 'bored posh': 'bored', 'yelling': 'shouting', 'yawning': 'tired', 'pirate': 'excited', 'robot': 'indifferent', 'defensive': 'embarrassed', 'flat default': 'indifferent', 'slowed': 'calm', 'tiny whisper': 'whispering', 'smug': 'confident', 'sly': 'sarcastic', 'scared': 'scared', 'offended': 'disdainful', 'disgusted': 'disgusted', 'sweet smug': 'sarcastic',
        'casual': 'relaxed', 'determined': 'determined', 'panic': 'panicked', 'hurried': 'hurried', 'delighted': 'delighted', 'quick': 'excited',
        'epic scream': 'shouting', 'sigh': 'sighing', 'warm quiet': 'soft tone', 'soft smile': 'soft tone'}
ROLE_NAME = dict(N='Narrator', SYS='Settings (system voice)', SAM='Sam', LILY='Lily', MOM='Mom', DAD='Dad', PICKLES='Pickles the cat', BRIGGS='Mr. Briggs', KEVIN='Kevin')
scenes = []
for r in S:
    if not scenes or scenes[-1] != r['scene']: scenes.append(r['scene'])
counter = {}
for r in S:
    k = r['scene'][:3]; counter[k] = counter.get(k, 0) + 1
    r['id'] = f"{k}-L{counter[k]:03d}"
words = lambda t: len(re.findall(r"[A-Za-z0-9']+", t))
# time estimate: narrator about 150 wpm while voiced, characters about 140, plus about 0.45 s between lines
est = sum(words(r['text']) / (150 if r['role'] == 'N' else 140) * 60 + 0.45 for r in S)
os.makedirs(f'{ROOT}/voices', exist_ok=True)
with open(f'{ROOT}/script.tsv', 'w') as f:
    f.write('id\tscene\trole\ttag\ttext\tpicture\n')
    for r in S: f.write('\t'.join([r['id'], r['scene'], r['role'], r['tag'], r['text'], r['pic']]) + '\n')
json.dump(S, open(f'{ROOT}/script.json', 'w'), indent=1)
md = ['# What If Real Life Had a SETTINGS MENU? — script v2', '',
      f'{len(S)} lines · {sum(words(r["text"]) for r in S)} words · estimated {int(est // 60)}:{int(est % 60):02d} of voice (picture runs a little longer with the gags).', '',
      'Columns: line id · who · how · the line · what we see.', '']
for sc in scenes:
    md += [f'## {sc}', '', '| ID | Who | How | Line | Picture |', '|---|---|---|---|---|']
    for r in S:
        if r['scene'] == sc: md.append(f"| {r['id']} | {ROLE_NAME[r['role']]} | {r['tag']} | {r['text']} | {r['pic']} |")
    md.append('')
open(f'{ROOT}/SCRIPT.md', 'w').write('\n'.join(md))
# one sheet per voice: ids, delivery, a Fish-style emotion tag, and a paste-ready block per scene
stats = []
for role in ROLE_NAME:
    rows = [r for r in S if r['role'] == role]
    if not rows: continue
    w = sum(words(r['text']) for r in rows)
    stats.append(f"{role:8s} {len(rows):3d} lines {w:4d} words")
    out = [f'# {ROLE_NAME[role]} — every line ({len(rows)} lines, {w} words)', '',
           'Name each file `<ID>_' + role + '.wav` (for example `' + rows[0]['id'] + '_' + role + '.wav`). A retake gets `_t2`.',
           'Or export one file per scene with about 1 second of silence between lines, named `<scene>_' + role + '.wav` (for example `S01_' + role + '.wav`); we split it.', '',
           '| ID | Delivery | Line |', '|---|---|---|']
    for r in rows: out.append(f"| {r['id']} | {r['tag']} | {r['text']} |")
    out += ['', '## Paste-ready, one block per scene (emotion tag in brackets at the start)', '']
    for sc in scenes:
        rr = [r for r in rows if r['scene'] == sc]
        if not rr: continue
        out += [f'### {sc}', '```']
        out += [f"({FISH.get(r['tag'], 'calm')}) {r['text']}" for r in rr]
        out += ['```', '']
    open(f'{ROOT}/voices/{role}.md', 'w').write('\n'.join(out))
    open(f'{ROOT}/voices/{role}.txt', 'w').write('\n'.join(f"{r['id']}\t({FISH.get(r['tag'], 'calm')}) {r['text']}" for r in rows) + '\n')
stats.append(f"TOTAL    {len(S):3d} lines {sum(words(r['text']) for r in S):4d} words, est {est:.0f} s of voice")
open(f'{ROOT}/stats.txt', 'w').write('\n'.join(stats) + '\n')
print('\n'.join(stats))
