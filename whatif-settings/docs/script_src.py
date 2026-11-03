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
c = 'S00 COLD OPEN'
L(c, 'N', 'HYPE', 'What if real life had a SETTINGS menu?', 'Title card: a glossy gear spins in over the street; the title stamps word by word')
L(c, 'N', 'HYPE', 'One app.', 'The gear app icon zooms at the lens')
L(c, 'N', 'HYPE', 'Seven days.', 'Our DAY card flips 1 to 7')
L(c, 'N', 'HYPE', 'Total control.', 'A fan of sliders and toggles sweeps across the screen')
L(c, 'SYS', 'calm', 'Factory reset in sixty seconds.', 'Flash-forward, Day 7: the sky is a loading bar, Dad floats past upside down, red countdown pill 1:00')
L(c, 'SAM', 'nervous', 'Okay. In my defense... I only changed one thing.', 'Sam to camera, sweat drop growing')
L(c, 'SYS', 'calm', 'Changes made: four hundred and twelve.', 'A counter rolls 1 to 412 beside his head')
L(c, 'SAM', 'guilty', '...Ish.', 'Tiny shrug, guilty half-lid eyes')
L(c, 'N', 'DEADPAN', "Let's scroll back.", 'Our UNDO HISTORY panel: a list of 412 changes scrolls back at speed, day icons blurring past')
L(c, 'N', 'DEADPAN', 'Seven days ago. 2:13 a.m.', "Sam's bedroom, moonlight, Sam asleep")
L(c, 'N', 'HYPE', 'Your phone buzzes.', 'Phone on the nightstand rattles, screen glow on his face')
L(c, 'N', 'HYPE', "An app you never downloaded.", "A gear icon: SETTINGS - for real life")
L(c, 'N', 'DEADPAN', 'First, the terms and conditions.', 'T&C card, page counter 1 / 4,812')
L(c, 'N', 'DEADPAN', 'Four thousand, eight hundred and twelve pages.', 'Pages stack up past the ceiling')
L(c, 'N', 'HYPE', 'So you do what everyone does.', 'Sam squints, thumb raised')
L(c, 'N', 'HYPE', 'Scroll to the bottom...', 'One flick: pages blur, whoosh')
L(c, 'N', 'HYPE', '...and press I AGREE.', 'Big green button, press, ding')
L(c, 'SYS', 'cheerful', 'Welcome to Reality Settings! All changes apply... for real.', 'Toast slides in, gear glows')
L(c, 'N', 'DEADPAN', 'Sure they do.', 'Sam rolls his eyes')
L(c, 'N', 'HYPE', 'You open Brightness.', 'Brightness slider fills the screen')
L(c, 'N', 'HYPE', 'Slide it up. Just a little.', 'The moon outside flares into a sun; the room blows out white; birds wake and sing')
L(c, 'DAD', 'shouting', 'Who turned on the SUN?!', 'Down the hall, Dad in pyjamas, shielding his eyes')
L(c, 'N', 'HYPE', "Okay. That's not your phone's brightness.", 'Sam slowly lowers the phone, star eyes fading to fear')
L(c, 'N', 'DEADPAN', "That's the planet's.", 'Snap zoom out to space: one side of Earth glowing like a lamp')

# ---------------------------------------------------------------- DAY 1
c = 'S01 DAY 1 - JUST TESTING'
L(c, 'N', 'HYPE', 'Day one.', 'DAY 1 card slams in')
L(c, 'N', 'HYPE', 'Seven a.m. Your alarm goes off.', 'Alarm clock jumping on the nightstand')
L(c, 'N', 'HYPE', 'But now it has a new button.', 'Alarm UI: STOP / SNOOZE (unlimited)')
L(c, 'N', 'DEADPAN', 'Snooze. Unlimited.', 'Push in on the word unlimited')
L(c, 'N', 'DEADPAN', 'You press it.', 'Tap; the whole world freezes: a bird stuck mid-air, Mom frozen mid-yell in the doorway')
L(c, 'N', 'HYPE', 'And everything... waits.', 'Sam snuggles back into bed among frozen dust specks')
L(c, 'N', 'DEADPAN', 'Nine minutes. Then nine more.', 'Snooze pill: 9:00, 9:00, 9:00')
L(c, 'N', 'DEADPAN', 'Then ninety more.', "Mom's frozen face, a fly frozen on her nose")
L(c, 'N', 'HYPE', 'Breakfast.', 'Kitchen, morning light')
L(c, 'N', 'DEADPAN', 'Lily is awake.', 'Lily at the table, inhaling')
L(c, 'LILY', 'shouting', 'I WANT THE BLUE SPOON!', 'Glasses rattle, Pickles flattens his ears, Dad\'s moustache blows back')
L(c, 'N', 'HYPE', 'You find Volume.', 'Volume list: Dad, Mom, Lily, Pickles, Kevin next door')
L(c, 'N', 'DEADPAN', 'And slide her... to zero.', 'A mute badge pops over Lily; she keeps screaming in silence; subtitle [muted]')
L(c, 'MOM', 'relieved', 'Why is it so... peaceful?', 'Mom sips tea, eyes closed, sparkles')
L(c, 'N', 'DEADPAN', 'Best breakfast of your life.', 'Sam eats cereal in slow, happy bliss')
L(c, 'N', 'HYPE', 'Next: Subtitles.', 'Toggle flips ON with a click')
L(c, 'N', 'HYPE', 'On.', 'A subtitle bar appears under every person in the kitchen')
L(c, 'DAD', 'warm', 'Morning, champ!', "Dad's subtitle: [I forgot his name for a second]")
L(c, 'SAM', 'deadpan', '...You forgot my name.', 'Sam stares; Dad sweats')
L(c, 'DAD', 'nervous', 'Pfft. No. ...Steve!', 'Subtitle: [guessed]')
L(c, 'N', 'HYPE', 'Then Gravity.', 'A planet dial: EARTH')
L(c, 'N', 'HYPE', 'Earth... Moon.', "Click; Dad's coffee lifts out of his mug as a wobbling brown blob")
L(c, 'N', 'HYPE', 'You get to school in four steps.', 'Sam bounds over rooftops, one boing per step')
L(c, 'N', 'DEADPAN', 'Dad gets to his car in forty minutes.', 'Dad swimming through the air, mug in hand, car drifting away')
L(c, 'DAD', 'panic falsetto', 'WHY AM I SWIMMING?!', 'Close-up, Dad flailing')
L(c, 'N', 'HYPE', 'Day one. Changes made: five.', 'Counter toast: 5')
L(c, 'N', 'DEADPAN', 'Totally under control.', 'A goldfish floats past the window in its water ball')

# ---------------------------------------------------------------- DAY 2
c = 'S02 DAY 2 - THE RULES'
L(c, 'N', 'HYPE', 'Day two.', 'DAY 2 card')
L(c, 'N', 'HYPE', 'Overnight, the app updates.', 'A PATCH NOTES card unrolls')
L(c, 'SYS', 'cheerful', 'Patch notes. Version one point one.', 'Gear spins, confetti')
L(c, 'SYS', 'calm', 'Rule one. Changes affect everyone within fifty meters.', 'A ring expands from Sam over the whole street')
L(c, 'N', 'HYPE', 'So when you set the weather to "snow day"...', 'Weather picker: SNOW DAY')
L(c, 'N', 'HYPE', '...the whole street gets one.', 'Snow bursts over every house in July; kids cheer in shorts')
L(c, 'KEVIN', 'angry', 'MY LAWN!', "Kevin on his knees in the snow, leaf blower in hand")
L(c, 'SYS', 'calm', 'Rule two. There is no undo.', 'An UNDO button greys out and crumbles')
L(c, 'N', 'DEADPAN', 'You check. There is no undo.', 'Sam tapping an empty corner of the screen')
L(c, 'SYS', 'calm', 'Rule three. Everything resets at midnight.', 'A midnight clock icon')
L(c, 'N', 'HYPE', 'Perfect. A free trial!', 'Sam punches the air')
L(c, 'N', 'HYPE', 'Midnight comes.', 'The family in pyjamas staring at the kitchen clock: 11:59... 12:00')
L(c, 'N', 'DEADPAN', 'Nothing resets.', 'Lily still muted, Dad still floating, snow still falling')
L(c, 'SYS', 'cheerful', 'Update one point two. Rule three has been removed.', 'A red REMOVED stamp slams on rule three')
L(c, 'SAM', 'outraged', 'You can\'t just REMOVE a rule!', 'Sam shouting at the phone, lurching at the lens')
L(c, 'SYS', 'cheerful', 'Rule four. I can.', 'Rule four types itself, cursor blinking')
L(c, 'N', 'HYPE', 'Then you find Difficulty.', 'Difficulty selector: EASY / NORMAL / HARD')
L(c, 'N', 'HYPE', 'Easy, for homework.', 'The pencil writes by itself; A+ stamps rain down')
L(c, 'N', 'DEADPAN', 'But Lily finds your phone.', 'Lily, still muted, grins with the phone')
L(c, 'N', 'DEADPAN', 'And sets the stairs to HARD.', 'The stairs turn into a boss: health bar THE STAIRS')
L(c, 'N', 'DEADPAN', 'Dad is still on step three.', 'Dad gripping the banister, health bar 12%')
L(c, 'DAD', 'exhausted', 'Tell your mother... I loved her.', 'Dad faints dramatically onto step three')
L(c, 'N', 'HYPE', 'Day two. Changes made: thirty-one.', 'Counter toast: 31')

# ---------------------------------------------------------------- DAY 3
c = 'S03 DAY 3 - 2X SPEED'
L(c, 'N', 'HYPE', 'Day three. School.', 'DAY 3 card, then the classroom')
L(c, 'N', 'DEADPAN', 'Mr. Briggs starts the lesson.', 'Briggs at the board, chalk squeak')
L(c, 'BRIGGS', 'monotone', 'Today... we will discuss... the history of the paperclip.', 'Every student falls asleep, Z\'s rise')
L(c, 'N', 'HYPE', 'So you find Playback Speed.', 'A speed control: 0.5x 1x 2x')
L(c, 'N', 'HYPE', 'Two times.', '2x: Briggs becomes a blur, chalk flying, the wall clock spinning')
L(c, 'BRIGGS', 'fast', 'And that is why the paperclip changed everything, any questions, no, good!', 'We speed this line up to chipmunk')
L(c, 'N', 'HYPE', 'Lunch is at nine fifteen.', 'Cafeteria clock 9:15, kids eating at double speed')
L(c, 'N', 'HYPE', "School's out by ten.", 'Kids blast out of the doors like a time-lapse')
L(c, 'N', 'HYPE', 'Then you find the best button ever made.', 'A glowing button rises: SKIP INTRO')
L(c, 'DAD', 'storytelling', 'Did I ever tell you about the summer of nineteen ninety—', 'Dad on the couch, starting a story')
L(c, 'N', 'HYPE', 'Skip intro.', 'Tap, whoosh: Dad jumps forward')
L(c, 'DAD', 'storytelling', '—and that is why I can never go back to the water park.', 'Dad finishes, satisfied; Sam nods')
L(c, 'KEVIN', 'smug', 'So this is a premium fertilizer blend—', 'Kevin leaning on the fence, sunglasses glinting')
L(c, 'N', 'DEADPAN', 'Skip ad.', 'Tap: Kevin vanishes mid-sentence with a pop')
L(c, 'N', 'HYPE', 'Then the math test.', 'A test paper slaps onto the desk')
L(c, 'N', 'HYPE', 'You skip the whole thing.', 'The paper fast-forwards to the last page')
L(c, 'N', 'DEADPAN', 'Score: skipped.', 'A red SKIPPED stamp')
L(c, 'BRIGGS', 'stern', 'Detention.', 'Normal speed again; record scratch; his glasses flash')
L(c, 'N', 'HYPE', 'You try to fast-forward detention...', 'Sam jabs the speed control')
L(c, 'N', 'DEADPAN', '...and press half speed.', '0.5x: the clock hands crawl')
L(c, 'SAM', 'slow-motion despair', 'Noooooo...', 'We slow this line down; Sam melts onto the desk in slow motion')
L(c, 'N', 'HYPE', 'Day three. Changes made: eighty-nine.', 'Counter toast: 89')

# ---------------------------------------------------------------- DAY 4
c = 'S04 DAY 4 - LANGUAGE'
L(c, 'N', 'HYPE', 'Day four.', 'DAY 4 card')
L(c, 'N', 'HYPE', 'Somebody changes the language.', 'A town-wide toast: LANGUAGE changed by: unknown user')
L(c, 'N', 'DEADPAN', 'To emoji.', 'Every speech bubble in town turns into emoji')
L(c, 'N', 'HYPE', 'Mom is fluent in seconds.', 'Mom firing emoji bubbles at machine-gun speed, smug')
L(c, 'N', 'DEADPAN', 'Dad is not.', 'Dad\'s bubble: duck, bread, question mark')
L(c, 'SAM', 'deadpan', 'Dad. You just said "duck bread."', 'Sam flat-eyed')
L(c, 'DAD', 'proud', 'And I stand by it.', 'Dad crosses his arms')
L(c, 'N', 'HYPE', 'So you try to fix it.', 'Sam scrolling a language list')
L(c, 'N', 'HYPE', 'You scroll... and scroll...', 'Pirate, Dolphin, Robot, Medieval...')
L(c, 'N', 'DEADPAN', '...and your thumb slips.', 'Slow motion: the thumb lands on CAT')
L(c, 'N', 'DEADPAN', 'Language: Cat.', 'The whole town meows; then Pickles turns to camera')
L(c, 'PICKLES', 'bored posh', 'Finally.', 'Pickles, half-lidded, on the counter')
L(c, 'PICKLES', 'bored posh', 'I have so many complaints.', 'A scroll of complaints unrolls to the floor')
L(c, 'PICKLES', 'bored posh', 'One. The food. Is beige.', 'He pushes his bowl off the counter')
L(c, 'PICKLES', 'bored posh', 'Two. I watch you sleep. Every night.', 'Sam\'s face drains white')
L(c, 'SAM', 'scared', 'WHY?!', 'Sam lurches at the lens')
L(c, 'PICKLES', 'bored posh', 'Three. That is none of your business.', 'Pickles licks one paw')
L(c, 'N', 'HYPE', 'Day four. Changes made: one hundred and thirty.', 'Counter toast: 130')

# ---------------------------------------------------------------- DAY 5
c = 'S05 DAY 5 - GRAPHICS LOW'
L(c, 'N', 'HYPE', 'Day five.', 'DAY 5 card')
L(c, 'N', 'DEADPAN', 'Your phone hits one percent.', 'Battery icon blinking red')
L(c, 'SYS', 'calm', 'Battery saver on. Lowering reality graphics.', 'A progress bar crawls down: ULTRA, HIGH, LOW')
L(c, 'N', 'DEADPAN', 'And the world... gets cheap.', 'Everything pixelates; trees become flat cardboard cut-outs')
L(c, 'N', 'DEADPAN', 'The sun has eight pixels.', 'A blocky sun')
L(c, 'N', 'DEADPAN', 'Mom has corners.', 'Mom\'s head is an octagon')
L(c, 'MOM', 'offended', 'Do NOT look at me.', 'Mom hiding her octagon face behind a pixel mug')
L(c, 'N', 'HYPE', 'Then the lag starts.', 'The picture stutters')
L(c, 'N', 'HYPE', 'Dad walks to the fridge...', 'Dad mid-step')
L(c, 'N', 'HYPE', '...teleports onto the roof...', 'Dad on the roof, confused')
L(c, 'N', 'DEADPAN', '...and comes back holding a duck.', 'Dad back in the kitchen holding a duck (callback: duck bread)')
L(c, 'DAD', 'deadpan', "I don't want to talk about it.", 'The duck quacks')
L(c, 'N', 'HYPE', 'So you plug in your phone. Graphics: ULTRA.', 'Charging bolt, the slider slams to ULTRA')
L(c, 'N', 'DEADPAN', 'Now everything is too real.', 'Ultra-detailed close-ups: Pickles\' eye, Lily\'s gap tooth gleaming')
L(c, 'N', 'DEADPAN', "You can see every pore on Dad's nose.", 'A slow, horrifying push into Dad\'s nose')
L(c, 'N', 'DEADPAN', 'Every. Single. One.', 'Three snap zooms, closer each time')
L(c, 'SAM', 'disgusted', 'Put it back. PUT IT BACK!', 'Sam gagging, slamming the slider back to normal')
L(c, 'N', 'HYPE', 'Day five. Changes made: two hundred and six.', 'Counter toast: 206')

# ---------------------------------------------------------------- DAY 6
c = 'S06 DAY 6 - OTHER USERS'
L(c, 'N', 'HYPE', 'Day six.', 'DAY 6 card')
L(c, 'N', 'HYPE', 'You open the app...', 'Notifications start stacking')
L(c, 'SYS', 'cheerful', 'Kevin changed GRASS to: gold.', 'Kevin\'s lawn turns to shining gold; the street squints')
L(c, 'N', 'DEADPAN', 'Kevin has the app.', 'Kevin smug, phone in hand, sunglasses glint')
L(c, 'SYS', 'cheerful', 'LilyRoar changed GRAVITY to: bouncy.', 'The whole family bounces like rubber balls')
L(c, 'N', 'DEADPAN', 'Lily has the app.', 'Lily bouncing, still muted, delighted')
L(c, 'SYS', 'calm', 'Mom turned on Parental Controls.', 'All of Sam\'s settings grey out with locks: ASK A PARENT')
L(c, 'N', 'DEADPAN', 'And Mom has had it... since day one.', 'Flashback tint: Mom in her robe at 2:14 a.m., pressing I AGREE')
L(c, 'MOM', 'sweet smug', 'Who do you think set your bedtime to eight?', 'Mom sips her tea')
L(c, 'SAM', 'outraged', 'I THOUGHT I WAS JUST TIRED!', 'Sam explodes, steam from his ears')
L(c, 'N', 'HYPE', 'Now everyone changes everything.', 'Split screens multiplying')
L(c, 'N', 'HYPE', "The sun can't decide if it's day.", 'Day and night strobing over the street')
L(c, 'N', 'HYPE', 'Half the street is in winter.', 'A perfect line: snow on the left, summer on the right')
L(c, 'N', 'DEADPAN', "Dad's subtitles are in four languages.", 'Four stacked subtitle bars under Dad')
L(c, 'N', 'HYPE', 'And then Dad sees a pop-up.', 'UPDATE AVAILABLE: Reality 2.0. [Later] [Install]')
L(c, 'DAD', 'casual', 'I always press later.', 'Dad\'s thumb hovering')
L(c, 'N', 'DEADPAN', 'He presses install.', 'Tap. Freeze frame. Sub boom.')
L(c, 'SYS', 'calm', 'Installing Reality two point oh.', 'The sky becomes a giant progress bar at 1%')
L(c, 'N', 'DEADPAN', 'Day six. Changes made: four hundred and eleven.', 'Counter toast: 411')

# ---------------------------------------------------------------- DAY 7
c = 'S07 DAY 7 - FACTORY RESET'
L(c, 'N', 'HYPE', 'Day seven.', 'DAY 7 card, red')
L(c, 'N', 'HYPE', 'The update runs all night.', 'The sky bar fills to 99%')
L(c, 'N', 'HYPE', 'And at sunrise...', 'The counter ticks 411 to 412')
L(c, 'SYS', 'calm', 'Factory reset in sixty seconds.', 'Same shot as the cold open; countdown pill 1:00')
L(c, 'N', 'HYPE', 'Factory reset means everything goes back to default.', 'Settings fly back to their default positions')
L(c, 'N', 'DEADPAN', 'No settings. No changes.', 'Icons wink out one by one')
L(c, 'N', 'DEADPAN', 'No memories.', 'The family photo on the wall fades to grey silhouettes')
L(c, 'SAM', 'determined', 'Okay. Cancel button. Where is the cancel button?!', 'Sam tearing through the menu')
L(c, 'N', 'HYPE', 'Fifty seconds.', 'The dial pops: 50')
L(c, 'N', 'HYPE', 'You try Snooze.', 'Snooze button tap (callback)')
L(c, 'SYS', 'cheerful', 'Snooze is not available during a factory reset.', 'Error buzz')
L(c, 'N', 'HYPE', 'You try Undo.', 'Sam taps the empty corner again (callback)')
L(c, 'SYS', 'cheerful', 'Rule two.', 'Rule two card flashes')
L(c, 'N', 'HYPE', 'Forty seconds.', 'Dial: 40')
L(c, 'N', 'HYPE', 'Wait. The terms and conditions!', 'Sam freezes, star eyes')
L(c, 'N', 'HYPE', 'Page four thousand, eight hundred and twelve.', 'Super-fast scroll, then a zoom into the tiniest print')
L(c, 'SYS', 'calm', 'A reset can only be stopped by the loudest person in the house.', 'The fine print enlarges to fill the screen')
L(c, 'N', 'HYPE', 'The loudest person in the house...', 'Every head slowly turns toward Lily')
L(c, 'N', 'DEADPAN', '...is muted.', 'Lily, mute badge, waving. Music drops out.')
L(c, 'N', 'HYPE', 'Thirty seconds.', 'Dial: 30, music slams back in')
L(c, 'SAM', 'panic', 'Unmute! UNMUTE!', "Sam grabs Lily's volume slider: it is locked")
L(c, 'SYS', 'calm', 'Locked by Parental Controls.', 'Padlock clamps shut on the slider')
L(c, 'MOM', 'hurried', "The password is your father's worst joke!", 'Mom pointing at Dad')
L(c, 'DAD', 'delighted', 'Oh! So a bicycle walks into a—', 'Dad settling in for a long story')
L(c, 'SAM', 'shouting', 'SKIP INTRO!', 'Sam slams the SKIP INTRO button (callback)')
L(c, 'DAD', 'quick', '—it was two tired!', 'The password field fills: TWO-TIRED, green check; Mom groans')
L(c, 'N', 'HYPE', 'Ten seconds.', 'The pill turns red: 0:10')
L(c, 'N', 'HYPE', "You slide Lily's volume...", 'The slider races past 100')
L(c, 'N', 'HYPE', '...all the way past the end.', 'It breaks through the frame of the slider: 200%')
L(c, 'SYS', 'calm', 'Five. Four. Three...', 'Dial pops 5, 4, 3')
L(c, 'LILY', 'epic scream', 'I WANT THE BLUE SPOOOOON!', 'Shockwave; the reset window shatters like glass (callback)')
L(c, 'SYS', 'calm', 'Reset... cancelled.', 'Shards drift down in silence; one tinkle')
L(c, 'N', 'HYPE', 'In one second, everything snaps back.', 'The sky, gravity and colours snap back to normal; Dad lands on his feet')
L(c, 'N', 'HYPE', 'Gravity, normal. Language, normal.', 'The duck waddles out of frame')
L(c, 'PICKLES', 'sigh', 'Pity.', 'Pickles\' last word in English, then: meow')
L(c, 'N', 'HYPE', "Dad's subtitles show one last line.", 'Dad turns to Sam')
L(c, 'DAD', 'warm quiet', 'Good job, kiddo.', 'Subtitle: [so proud of you, Sam]')
L(c, 'SAM', 'soft smile', '...You remembered my name.', 'Sam smiles, blush')
L(c, 'N', 'HYPE', 'Lily gets the blue spoon.', 'Lily holds the blue spoon up like a trophy')
L(c, 'N', 'DEADPAN', "And Kevin's lawn stays gold.", 'Kevin hugging his golden lawn')

# ---------------------------------------------------------------- ENDING
c = 'S08 ENDING'
L(c, 'N', 'HYPE', 'That night, you delete the app.', 'UNINSTALL; are you sure; yes; the gear dissolves into sparkles')
L(c, 'N', 'DEADPAN', 'Normal life. Finally.', 'Sam in bed, smiling, eyes closing')
L(c, 'N', 'DEADPAN', '2:13 a.m.', 'The same bedroom shot as the cold open; the phone buzzes')
L(c, 'SYS', 'cheerful', 'New app available. Reality Settings Two... now with TIME.', 'A clock-gear icon; I AGREE glowing; Sam\'s thumb hovers')
L(c, 'N', 'HYPE', "If you had this menu, what's the ONE setting you would change?", 'A settings list with an empty row: YOUR IDEA')
L(c, 'N', 'HYPE', 'Tell me in the comments.', 'Comment icon pops')
L(c, 'N', 'HYPE', 'And this button right here...', 'An in-world toggle: SUBSCRIBE: OFF')
L(c, 'N', 'DEADPAN', "...is the only setting that's actually real.", 'The toggle flips ON with sparkles')

# ---------------------------------------------------------------- outputs
ROOT = os.path.dirname(os.path.abspath(__file__))
FISH = {'HYPE': 'excited', 'DEADPAN': 'calm', 'calm': 'calm', 'cheerful': 'happy', 'nervous': 'nervous', 'guilty': 'embarrassed', 'shouting': 'shouting',
        'relieved': 'relaxed', 'warm': 'happy', 'deadpan': 'indifferent', 'panic falsetto': 'panicked', 'angry': 'angry', 'outraged': 'angry', 'exhausted': 'sad',
        'monotone': 'indifferent', 'fast': 'hurried', 'storytelling': 'happy', 'smug': 'confident', 'stern': 'serious', 'slow-motion despair': 'sad',
        'proud': 'proud', 'bored posh': 'bored', 'scared': 'scared', 'offended': 'disdainful', 'disgusted': 'disgusted', 'sweet smug': 'sarcastic',
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
md = ['# What If Real Life Had a SETTINGS MENU? — script v1', '',
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
