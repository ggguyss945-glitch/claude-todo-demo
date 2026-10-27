# 60-second test: narration lines with delivery notes.
# speed < 1 slows the read; gap = silence after the line (seconds); level = dB offset for intimacy.
PA_LINE = dict(id='PA', text='Attention, Freshway shoppers. Aisle seven is now open.', voice='af_heart', speed=1.0)

LINES = [
    dict(id='L1', text="They don't see you.", speed=0.86, gap=0.55, level=-2.5, mood='whisper-close'),
    dict(id='L2', text='They hear you.', speed=0.86, gap=0.45, level=-2.5, mood='whisper-close'),
    dict(id='L3', text='And the store radio just told every one of them... where you are.', speed=0.9, gap=1.15, level=-1.5, mood='tense'),
    dict(id='L4', text="It's two fourteen in the morning. You stack shelves on the night shift at Freshway.", speed=1.0, gap=0.35, level=0, mood='story'),
    dict(id='L5', text='An hour ago, the customers stopped being customers.', speed=0.95, gap=0.95, level=0, mood='dry'),
    dict(id='L6', text='Your manager promised the night shift would be quiet.', speed=1.0, gap=0.8, level=0, mood='wry'),
    dict(id='L7', text='Gary has never been more right.', speed=0.92, gap=1.05, level=0, mood='deadpan'),
    dict(id='L8', text='So you do what you always do at two in the morning. You count.', speed=0.97, gap=0.55, level=0, mood='warm'),
    dict(id='L9a', text='Nine thousand cans.', speed=0.95, gap=0.35, level=0, mood='warm'),
    dict(id='L9b', text='Thirty-eight gallons of water.', speed=0.95, gap=0.35, level=0, mood='warm'),
    dict(id='L9c', text='Two batteries.', speed=0.92, gap=0.75, level=0, mood='warm'),
    dict(id='L10', text='Food is not the problem.', speed=0.88, gap=0.9, level=-1, mood='realisation'),
    dict(id='L11', text="Rule one. They hear. They don't see.", speed=0.9, gap=0.85, level=0, mood='firm'),
    dict(id='L12', text='At two thirty-one, somewhere in aisle twelve, an alarm clock starts to ring.', speed=0.97, gap=0.75, level=0, mood='tense'),
    dict(id='L13', text='Nobody here set that alarm.', speed=0.84, gap=0.0, level=-2.5, mood='whisper-close'),
]
NARRATION_START = 9.8   # after the POV cold open
NARRATOR = {'am_puck': 0.5, 'am_michael': 0.5}
