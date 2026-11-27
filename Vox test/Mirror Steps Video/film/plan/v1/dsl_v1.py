"""plan/dsl.py: the small language the shot list (plan/shotlist.py) is written in.

Times come from _work/align/timeline.json, never typed by hand:
    t(i) line start, e(i) line end, w(i, 'word', n=0) start of the n-th word in line i that starts with 'word'
    (case and punctuation ignored), T(i) = t(i) - LEAD and Wc(i, word) = w(i, word) - LEAD (cut points: the picture
    leads the voice by LEAD = 0.25 s, REF_MIRROR section 2), R(dt) a time relative to the shot (dt >= 0 from t0, < 0 from t1).

S(at, set, view, var, side, typ, frame, cam, **kw) appends one shot; it ends where the next one starts.
cam(mv, **p) describes the camera move; make_plan.py turns it into explicit keys [t, x, y, zoom, roll].
C(who, at, view, expr, acts, mode, **extra) is a character; A(t, clip, **p) one acting clip.
fx(t, name, gain_db, space, note, **params) one SFX cue; M(t, type, level, len, note) one music event.
hud events: tag(), redx(), label(), plus dicts for time_card / phone / rule_card / like_sub.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
TIMELINE = os.path.join(FILM, '_work', 'align', 'timeline.json')
TL = json.load(open(TIMELINE))
LINES = TL['lines']
DUR = float(TL['duration_en'])
LEAD = 0.25
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


def T(i, off=0.0): return round(t(i) - LEAD + off, 3)


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


def tag(at, text, x=960, y=110, style='cmd', hold=1.2, pin=None):
    """Command tag: red bold text in a near-black box with a red outline, pops in 3-4 frames with overshoot (REF 6)."""
    d = dict(t=at, type='tag', text=text, x=x, y=y, style=style, hold=hold)
    if pin: d['pin'] = pin
    return d


def label(at, text, pin, dx=160, dy=-120, hold=1.6):
    """Small white label pinned to a subject point with a leader line (police film's pinned tags)."""
    return dict(t=at, type='label', text=text, pin=pin, dx=dx, dy=dy, hold=hold, style='white')


def redx(at, x, y, r=170, hold=1.0):
    """Red X over the forbidden action: 1-frame red tint flash, ring, two strokes in 0.17 s (REF 6)."""
    return dict(t=at, type='red_x', x=x, y=y, r=r, hold=hold)


def S(at, set_, view, var, side, typ, frame, camera, **kw):
    d = dict(t0=at, set=set_, view=view, var=var, side=side, type=typ, frame=frame, cam=camera)
    d.update(kw)
    SHOTS.append(d)
    return d
