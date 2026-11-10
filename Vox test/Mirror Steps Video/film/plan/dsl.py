"""plan/dsl.py: the small language the shot list (plan/shotlist.py) is written in (v2; PLAN_V2.md documents every field).

Times come from _work/align/timeline.json, never typed by hand:
    t(i) line start, e(i) line end, w(i, 'word', n=0) start of the n-th word in line i that starts with 'word'
    (case and punctuation ignored), T(i) = t(i) - LEAD and Wc(i, word) = w(i, word) - LEAD (cut points: the picture
    leads the voice by LEAD = 0.17 s, DIRECTION_V2 5.1), R(dt) a time relative to the shot (dt >= 0 from t0, < 0 from t1).

S(at, set, view, var, side, typ, frame, cam, **kw) appends one shot; it ends where the next one starts.
X(at, typ, world, 'set/view', var, frame, cam, **kw) is the v2 front end: side, look and class come from the world.
cam(mv, **p) describes the camera move; make_plan.py turns it into explicit keys [t, x, y, zoom, roll].
C(who, at, view, expr, acts, mode, **extra) is a character; A(t, clip, **p) one acting clip.
fx(t, name, gain_db, space, note, **params) one SFX cue; M(t, type, level, len, note) one music event.
HUD builders: tag(), redx(), label() (v1) and the v2 devices chip(), teaser(), kinetic(), typebeat(), giant(), diagram(),
doc(), count_pop(), stamp(), highlight(), mapins(), level_guide(), rings(), eye_line(), dials() (PLAN_V2.md, "HUD").
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
TIMELINE = os.path.join(FILM, '_work', 'align', 'timeline.json')
TL = json.load(open(TIMELINE))
LINES = TL['lines']
DUR = float(TL['duration_en'])
LEAD = 0.17
SHOTS = []


def _norm(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum() or ch in "'-:")


def t(i): return float(LINES[i]['t'])


def e(i): return float(LINES[i]['end'])


def w(i, word, n=0):
    """Start time of the n-th word of line i that starts with `word` (digits as written by the aligner: '11:57')."""
    target = _norm(word)
    k = 0
    for wd, tt in LINES[i]['words']:
        if tt is None: continue
        if _norm(wd).startswith(target):
            if k == n: return float(tt)
            k += 1
    raise KeyError('word %r (n=%d) not in line %d: %s' % (word, n, i, LINES[i]['en']))


def w0(i):
    """Time of the first timed word of line i (the clause start the validator measures against)."""
    return next(float(tt) for wd, tt in LINES[i]['words'] if tt is not None)


def T(i, off=0.0): return round(w0(i) - LEAD + off, 3)


def Wc(i, word, n=0, off=0.0): return round(w(i, word, n) - LEAD + off, 3)


class R:
    """Time relative to the shot: R(0.3) = t0 + 0.3, R(-0.4) = t1 - 0.4."""
    def __init__(self, dt): self.dt = float(dt)

    def __repr__(self): return 'R(%g)' % self.dt


def resolve(x, t0, t1):
    if isinstance(x, R): return round(t0 + x.dt if x.dt >= 0 else t1 + x.dt, 3)
    if isinstance(x, dict): return {k: resolve(v, t0, t1) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [resolve(v, t0, t1) for v in x]
    if isinstance(x, float): return round(x, 3)
    return x


# ------------------------------------------------------------------ builders
def cam(mv, **p):
    p['mv'] = mv
    return p


def A(t_, clip, /, **p):
    return [t_, clip, p]


def C(who, at, view='front', expr='neutral', acts=(), mode='body', **extra):
    d = dict(who=who, at=at, view=view, expr=expr, acts=list(acts), mode=mode)
    d.update(extra)
    return d


def fx(at, name, g=0.0, sp='close', note='', hit=False, **params):
    d = dict(t=at, name=name, gain_db=g, space=sp, note=note)
    if hit: d['hit'] = True
    if params: d['params'] = params
    return d


def M(at, typ, level=0.7, length=None, note=''):
    d = dict(t=at, type=typ, level=level)
    if length is not None: d['len'] = length
    if note: d['note'] = note
    return d


def tag(at, text, x=960, y=150, style='lipstick', hold=1.2, pin=None):
    """Command tag (v2): lipstick-red hand-lettered text with no pill box, pops in 3-4 frames with overshoot (5.5)."""
    d = dict(t=at, type='tag', text=text, x=x, y=y, style=style, hold=hold)
    if pin: d['pin'] = pin
    return d


def label(at, text, pin, dx=160, dy=-120, hold=1.6):
    """Small white label pinned to a subject point with a leader line (police film's pinned tags)."""
    return dict(t=at, type='label', text=text, pin=pin, dx=dx, dy=dy, hold=hold, style='white')


def redx(at, x, y, r=170, hold=1.0, n=None):
    """Red X over the forbidden action: 1-frame red tint flash, ring, two strokes in 0.17 s (REF 6). n = 1..4 of the film."""
    d = dict(t=at, type='red_x', x=x, y=y, r=r, hold=hold)
    if n: d['n'] = n
    return d


# ------------------------------------------------------------------ v2 HUD devices (PLAN_V2.md "HUD")
def chip(at, text, style='ours', hold=None, x=110, y=118):
    """Place/time chip, top-left under the header, cap height 1.4 % H, 0.4 s pop. style ours (navy, blue dot), theirs (gold,
    amber dot), memory (red-brown rubber stamp rotated -4 deg), teaser (red), loop (gold with a circular arrow), split."""
    d = dict(t=at, type='chip', text=text, style=style, x=x, y=y)
    if hold is not None: d['hold'] = hold
    return d


def teaser(at, chip_text, border=6):
    """Flash-forward frame: red 6 px border, red chip, RGB split in and a glitch out (5.5)."""
    return dict(t=at, type='teaser', chip=chip_text, border_px=border, rgb_split=True, glitch_out=True)


def kinetic(at, parts, out=None):
    """The one kinetic title: parts [{t, text, color, size_h, fx}] full screen over the darkened, blurred plate (5.5)."""
    d = dict(t=at, type='kinetic', parts=parts)
    if out: d['out'] = out
    return d


def typebeat(at, n, text, **kw):
    """Type beats 1-6 (5.5): 1 the title, 2 the 14 YEARS stamp, 3 7 RULES, 4 the giant numbers, 5 7:00 AM, 6 the end card."""
    d = dict(t=at, type='typebeat', n=n, text=text)
    d.update(kw)
    return d


def giant(at, value, hold=0.5, to_badge=True):
    """Tess's giant number: red numeral in a ring at 38 % of H for 0.5 s, then it flies into the ring badge (type beat 4)."""
    return dict(t=at, type='giant_number', value=value, size_h=0.38, hold=hold, to_badge=to_badge)


def diagram(at, did, content, hold=None, **kw):
    """A diagram D1-D10 (5.4) drawn in chalk-white lines, lipstick red and chip style. content: what it shows, literally."""
    d = dict(t=at, type='diagram', id=did, content=content)
    if hold is not None: d['hold'] = hold
    d.update(kw)
    return d


def doc(at, kind, text, marks=(), **kw):
    """Evidence document insert: kind poster | notice | voicemail | menu | photo | polaroid | card; marks highlight /
    stamp / underline / circle entries [{t, what, text?}]."""
    d = dict(t=at, type='doc', kind=kind, text=text, marks=list(marks))
    d.update(kw)
    return d


def count_pop(at, n, x, y, color='#ffffff', erase=False):
    """D2: a numeral popping beside a step in 0.08 s (erase=True: it ticks off as the step is wiped)."""
    return dict(t=at, type='count_pop', n=n, x=x, y=y, color=color, erase=erase)


def stamp(at, text, x=960, y=540, color='#b8342c', rot=-4, size_h=0.16, hit=True):
    """Rubber stamp slam with a camera hit (14 YEARS, CANCELED, 14 YEARS AGO)."""
    return dict(t=at, type='stamp', text=text, x=x, y=y, color=color, rot=rot, size_h=size_h, hit=hit)


def highlight(at, text, x0, y0, x1, y1, color='#f4e04d', dur=0.35):
    """Yellow highlighter swipe across a line of a document (evidence device)."""
    return dict(t=at, type='highlight', text=text, box=[x0, y0, x1, y1], color=color, dur=dur)


def mapins(at, hold, items, dot=None):
    """D10 map inset (top left, 2 s): items [label, x, y] in a 360x240 inset; dot = Tess's moving dot [[t, x, y]...]."""
    d = dict(t=at, type='map', hold=hold, items=items)
    if dot: d['dot'] = dot
    return d


def level_guide(at, y, rot_frame=-13.0, hold=1.6):
    """The dashed level guide across a tilted frame (146.5 s): the eighth step and the woman stay level."""
    return dict(t=at, type='level_guide', y=y, frame_rot=rot_frame, hold=hold)


def rings(at, kind, x, y, n=3, hold=1.4):
    """D8 sound rings: kind clean (smooth white concentric rings) | rattle (a ring plus a jagged red squiggle) |
    broken (jagged, broken rings: the real bell struck)."""
    return dict(t=at, type='sound_rings', kind=kind, x=x, y=y, n=n, hold=hold)


def eye_line(at, a, b, hold=1.2):
    """D5: a dashed red line joining her eye (a) and your eye (b) across a split."""
    return dict(t=at, type='eye_line', a=a, b=b, hold=hold)


def dials(at, left, right, hold=2.0):
    """D6: two clock dials over the section: left/right = {label, chip, rate} (OUR SIDE crawling, THEIR SIDE looping)."""
    return dict(t=at, type='dials', left=left, right=right, hold=hold)


def S(at, set_, view, var, side, typ, frame, camera, **kw):
    d = dict(t0=at, set=set_, view=view, var=var, side=side, type=typ, frame=frame, cam=camera)
    d.update(kw)
    SHOTS.append(d)
    return d


# world -> v1-compatible side (film.py / sets.py / the header clock read `side`)
WORLD_SIDE = {'ours': 'ours', 'stairs': 'stairs', 'theirs': 'theirs', 'theirs_break': 'theirs', 'memory': 'memory',
              'climax': 'ours', 'ending': 'ours', 'ui': 'ui', 'card': 'card', 'black': 'black'}


def X(at, typ, world, sv, var, frame, camera, **kw):
    """v2 shot: typ (EWS WS SEC | MS OTS 2S | MCU CU ECU | INSERT DOC DIAGRAM SPLIT UI TYPE MONTAGE | POV | CARD BLACK),
    world (ours stairs theirs theirs_break memory climax ending ui card black), 'set/view', var, frame, cam."""
    set_, view = sv.split('/')
    side = kw.pop('side', None)
    if side is None:
        side = WORLD_SIDE[world]
        if set_ == 'mirror' and world in ('ours', 'climax', 'ending'): side = 'mirror'
        if world == 'climax' and set_ in ('stairs',): side = 'stairs'
        if world == 'climax' and set_ in ('cabin_dawn',): side = 'theirs'
    return S(at, set_, view, var, side, typ, frame, camera, world=world, **kw)
