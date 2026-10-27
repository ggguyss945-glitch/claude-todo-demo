# 60-second test: narration lines with delivery notes.
# Each line is a list of phrases (text, pause after in seconds). Phrases are voiced separately so the
# pauses land where a narrator would breathe; the pause after the last phrase is the gap to the next line.
# rate = target words per second inside a phrase (pauses come on top); level = dB offset for intimacy.
# A phrase may carry a third item: the spelling the voice should read when the display spelling is
# mispronounced; the take must still read back as the display text.
PA_LINE = dict(id='PA', text='Attention, Freshway shoppers. Aisle seven is now open.', voice='af_heart', speed=1.0)

LINES = [
    dict(id='L1', phrases=[("They don't see you.", 0.75)], rate=2.5, level=-2.5, mood='whisper-close'),
    dict(id='L2', phrases=[('They hear you.', 0.65)], rate=2.4, level=-2.5, mood='whisper-close'),
    dict(id='L3', phrases=[('And the store radio just told every one of them...', 0.5), ('where you are.', 0.95)], rate=2.9, level=-1.5, mood='tense'),
    dict(id='L4', phrases=[("It's two fourteen in the morning.", 0.42), ('You stack shelves on the night shift at Freshway.', 0.45, 'You stack shelves on the nightshift at Freshway.')], rate=3.05, level=0, mood='story'),
    dict(id='L5', phrases=[('An hour ago,', 0.22), ('the customers stopped being customers.', 0.85)], rate=2.8, level=0, mood='dry'),
    dict(id='L6', phrases=[('Your manager promised the night shift would be quiet.', 0.7, 'Your manager promised the nightshift would be quiet.')], rate=3.0, level=0, mood='wry'),
    dict(id='L7', phrases=[('Gary has never been more right.', 0.9)], rate=2.6, level=0, mood='deadpan'),
    dict(id='L8', phrases=[('So you do what you always do at two in the morning.', 0.45), ('You count.', 0.6)], rate=3.0, level=0, mood='warm'),
    dict(id='L9a', phrases=[('Nine thousand cans.', 0.45)], rate=2.4, level=0, mood='warm'),
    dict(id='L9b', phrases=[('Thirty-eight gallons of water.', 0.45)], rate=2.6, level=0, mood='warm'),
    dict(id='L9c', phrases=[('Two batteries.', 0.8)], rate=2.2, level=0, mood='warm'),
    dict(id='L10', phrases=[('Food is not the problem.', 0.8)], rate=2.5, level=-1, mood='realisation'),
    dict(id='L11', phrases=[('Rule one.', 0.6), ('They hear.', 0.5), ("They don't see.", 0.85)], rate=2.4, level=0, mood='firm'),
    dict(id='L12', phrases=[('At two thirty-one,', 0.28), ('somewhere in aisle twelve,', 0.3, 'somewhere in ile twelve,'), ('an alarm clock starts to ring.', 0.75)], rate=2.9, level=0, mood='tense'),
    dict(id='L13', phrases=[('Nobody here set that alarm.', 0.0)], rate=2.4, level=-2.5, mood='whisper-close'),
]
for L in LINES:
    L['text'] = ' '.join(p[0] for p in L['phrases'])
    L['gap'] = L['phrases'][-1][1]

NARRATION_START = 9.8   # after the POV cold open
NARRATOR = dict(engine='supertonic-3', sid=5, takes=6)   # Supertonic M1: the most expressive male voice in tests
