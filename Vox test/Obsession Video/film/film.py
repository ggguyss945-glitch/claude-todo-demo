"""film.py: the shot list, editor and cue sheets for "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE
YOUR NAME" (Night Policy).

Built in the machinery of the Buttons film (film_buttons_ref.py: the Film class, plan(), the shot builders, BUILDERS,
captions, header, cue sheets) on this film's cast (characters.py + characters_evie.py + characters_obsession.py) and sets
(sets.py + sets_obsession.py: ONE plan of Adam's house, the front path from his window, the school, the playground with
the Keeping Square, Mom's camcorder tape, the inserts). EVERY time in the plan is keyed to timeline.json (line starts /
ends and per-line word times): there is no absolute time anywhere, so a re-edit of the narration moves the picture.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration, F.shots              # seconds (narration + TAIL); [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None)             # W/cues/sfx_cues.json + music_cues.json + shots.json + beats_cues.json + spans.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --contact | --frames PREFIX | --lipcheck | --still T,T

THE OWNER'S NOTES, MADE INTO CODE:
  * The cold open is a TRAILER (plan_trailer): three waves of the film's creepiest flash-forwards, every cut on a word or
    a hit (TRAILER_HITS), a hard stop, a beat of black and the one silence before "I know who it is."
  * Every figure in a set shot stands on an anchor or plan point of the set (height from the px-per-metre there, draw
    order from sp.order_at(), light from sp.light_kw()); tools/validate.py checks it at 8 fps.
  * Prefer cuts; show exactly what each line says. EVIE is active in every beat she is in (closing in, watching from
    the background with her phone glow, appearing on cuts, blocking, flattening, sliding, stretching, writing).
  * Her look follows EVIE_ARC on the film clock (CH.evie_arc_from_lines, called once from the timeline). Her four limits:
    she never touches anyone; a grown-up's look holds her back (grown-ups in her shots face away until the porch light,
    the floodlight, Mom's chair and Mom at the door); telling drains her.
  * The chalk tracker ONLY ME stands at OM_TRACK's place each night; every dawn the path is wet and clean, the bucket by
    the door. Red only on the square, her ribbons and the one sunset. Door shots look DOWN from an upstairs window.
  * The tape (om_tape + om_tape_stamp) plays full frame in the setup, returns warped in rule 4 and as a rewind in rule 7;
    the cue sheets mark every tape span and every Evie-near span (the sound team's tape song, sweet and rotted).
  * Lip sync on character lines only (VOICE); the grown narrator is never drawn, only adam_grown's hands in the coda.

Shot kinds (builders B_<kind>):
  set    a set view (om_* builders) with figures on the plan: room 'front' | 'room' | 'hall' | 'kitchen' | 'school' |
         'play'; view = the builder's view; set = builder kwargs; ppl = [P(who, at, ...)]; acts -> extra layers
  bust   a face close-up over the blurred set
  ins    an om_insert (phone, card, car_window, locker, shoebox, stub); kw = dict or f(time since the cut)
  tape   Mom's camcorder tape, full frame (warp, rewind, the stamp), little Adam and Danny on the swings
  rule   Danny's card: rule n written word by word in purple as it is read
  prompt the comment prompt ("Special, or Trapped?")
  list   the outro checklist, every item legible while it is read
  card   plain text cards (title, end card)
  black  black
"""
import bisect, hashlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *                                                    # noqa: F401,F403
from engine import hud as H
from engine import post as _epost
from engine.core import tex_ns  # noqa: E402
from engine.core import DW, DH, CFG, clamp, lerp, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, noise1, hash01, prog, image_from
import characters as CH
import sets as ST

W = os.path.join(HERE, '_work')                                         # this film's work dir (film/_work)
ALIGN = os.path.join(W, 'align')
CUES_DIR = os.path.join(W, 'cues')
TESTS = os.path.join(W, 'shots')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
BEATS = os.path.join(ALIGN, 'beats.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
TAIL = 4.0                       # the end card holds after the last line
TITLE = "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME"
BASE = 'If_a_Girl_Is_Obsessed_With_Being_Your_Only_Friend'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card
PART_B = 213                       # tools/validate.py --part: A = lines 0..212 (.. rule six), B = 213..
def set_retime(lines, duration): return None


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (the timeline's `who`). The narrator (grown Adam) never moves a mouth on screen.
VOICE = {'adam': [('adam', None)], 'adam_night': [('adam', None)], 'adam7': [('adam7', None)], 'danny': [('danny', None)],
         'mom': [('mom', None)], 'lina': [('lina', None)], 'rahman': [('rahman', None)], 'evie': [('evie', None)]}
KIDS = ('adam', 'adam_night', 'danny', 'lina')
ADAMS = ('adam', 'adam_night')
# ---------------------------------------------------------------- the day label (small chalk font), keyed to lines
CORNER = [(0, ''), (7, ''), (13, 'MONDAY'), (17, 'AGE 7'), (21, 'MONDAY'), (39, 'MONDAY'), (44, 'TUESDAY'), (47, 'WEDNESDAY'),
          (56, 'WEDNESDAY NIGHT'), (74, 'THURSDAY'), (83, ''), (86, 'THURSDAY'), (104, 'THURSDAY NIGHT'), (108, 'THURSDAY'),
          (119, 'THURSDAY  2 A.M.'), (127, 'FRIDAY'), (168, 'LAST SUNDAY'), (171, 'FRIDAY  SUNSET'), (181, 'FRIDAY NIGHT'),
          (184, 'SATURDAY'), (213, 'SATURDAY  MIDNIGHT'), (281, 'LAST SUNDAY  MIDNIGHT'), (286, 'SATURDAY  MIDNIGHT'),
          (302, 'SUNDAY  DAWN'), (306, 'MONDAY'), (318, 'WEEKS LATER'), (331, 'NOW'), (341, '')]


def clock_str(t):
    F = _FILM[0]
    lab = ''
    for i, s in CORNER:
        if i < len(F.L) and t >= F.t(i) - LEAD: lab = s
    return lab


def header(cv, right, corner, alpha=255):
    """The header: the card's name, the rule, and the day in the small chalk font (top right)."""
    left = "DANNY'S CARD"
    w = text(cv, left, 44, 42, 600, 13, '#8c8c98', 120 * alpha / 255, 0.24, 'left')
    text(cv, '/   ' + right, 44 + w + 16, 42, 600, 13, '#c4c4ce', 150 * alpha / 255, 0.24, 'left')
    if corner:
        pen = Pen(cv)
        ST.btext(pen, corner, DW - 42, 58, 'kid', 34, '#000000', 90 * alpha / 255, 'right')
        ST.btext(pen, corner, DW - 44, 56, 'kid', 34, '#f1eee4', 215 * alpha / 255, 'right')


def puffs(**k):                    # (no cold breath in this film)
    return lambda pen, t, a: None


# ==================================================================================================== light on figures

def _ev(t, name, gain_db=0.0, pan=0.0, space=None, **params):
    e = {'t': round(float(t), 3), 'name': name, 'gain_db': round(float(gain_db), 1), 'pan': round(float(pan), 2)}
    if params: e['params'] = params
    if space: e['space'] = space
    return e


class Shot:
    def __init__(self, t0, kind, p, idx=0):
        self.t0, self.kind, self.p, self.idx = float(t0), kind, p, idx
        self.t1 = self.t0 + 3.0
        self.sfx, self.music = [], []
        self.actors = []

    @property
    def d(self): return self.t1 - self.t0

    def __repr__(self): return 'Shot(%d %.2f-%.2f %s)' % (self.idx, self.t0, self.t1, self.kind)


class Spec:
    def __init__(self, layers, cam, lens=None, grade=None, focus=1.0, dof=0.0, fx=None, hud=None):
        self.layers, self.cam, self.lens, self.grade, self.focus, self.dof = layers, cam, lens, grade, focus, dof
        self.fx, self.hud = fx, hud


class _Memo:
    """Acting.at memo (the depth function and the draw both ask for the same t)."""
    def __init__(self, a): self.a, self.t, self.p = a, None, None

    def __call__(self, t):
        if t != self.t: self.t, self.p = t, self.a.at(t)
        return self.p

def as_fn(v):
    return v if callable(v) else (lambda t, v=v: v)


def lvl(f, t):
    return float(f(t)) if callable(f) else float(f if f is not None else 1.0)


# ==================================================================================================== the film
class Film:
    def __init__(self, tl):
        self.tl = tl
        self.L = tl['lines']
        self.duration = float(tl.get('duration_en', 1079.16)) + TAIL
        set_retime(self.L, self.duration)        # the authored absolute-time tables follow their lines
        self.words = []
        if os.path.exists(WORDS):
            try:
                self.words = [(w.strip().lower().strip('.,?!;:"“”…'), float(t)) for w, t in json.load(open(WORDS))['en_words']]
            except Exception:
                self.words = []
        self._wt = [t for _, t in self.words]
        self.shots = []
        _FILM[0] = self
        self.globals = []                    # extra global cues (beds, music)
        self._freeze = {}
        plan(self)
        self.shots.sort(key=lambda s: s.t0)
        for k, s in enumerate(self.shots):
            s.idx = k
            s.t1 = self.shots[k + 1].t0 if k + 1 < len(self.shots) else self.duration
        self._starts = [s.t0 for s in self.shots]
        self.rules = [(s.t0, s.p['n']) for s in self.shots if s.kind == 'rule' and not s.p.get('recall')]
        self._built = {}
        for s in self.shots:                 # build every shot once: cues need the acting events (cheap: no drawing)
            self._build(s)
        self._built.clear()

    # ---------------------------------------------------------------- script timing
    def t(self, i, off=0.0): return self.L[i]['t'] + off

    def e(self, i, off=0.0): return self.L[i]['end'] + off

    def w(self, i, word, k=0, off=0.0):
        """Start time of the k-th occurrence of `word` inside line i (ASR word times; proportional fallback)."""
        l = self.L[i]; word = word.lower()
        a = bisect.bisect_left(self._wt, l['t'] - 0.25); n = 0
        for j in range(a, len(self.words)):
            ww, tt = self.words[j]
            if tt > l['end'] + 0.2: break
            if ww == word or ww.startswith(word):
                if n == k: return tt + off
                n += 1
        txt = l['en'].lower(); p = txt.find(word)
        return l['t'] + (l['end'] - l['t']) * (p / max(1, len(txt)) if p >= 0 else 0.5) + off

    def cut(self, t, kind, **p):
        self.shots.append(Shot(max(0.0, t), kind, p))

    def lines_in(self, t0, t1, codes=None):
        return [l for l in self.L if l.get('found_en', True) and (codes is None or l['who'] in codes) and l['end'] > t0 - 0.2 and l['t'] < t1 + 0.2]

    def voice_lines(self, t0, t1, voice):
        out = []
        for l in self.lines_in(t0, t1):
            for c, fx in voice:
                if c == 'NQ':
                    if l['who'] == 'narrator' and l['en'].lstrip().startswith(('"', '\u201c')): out.append(l); break
                    continue
                if l['who'] == c and (fx is None or l.get('fx') == fx):
                    out.append(l); break
        return out

    # ---------------------------------------------------------------- shot lookup / build
    def shot_at(self, t):
        k = max(0, bisect.bisect_right(self._starts, t) - 1)
        return self.shots[k]

    def _build(self, sh):
        if sh.idx in self._built: return self._built[sh.idx]
        sh.sfx, sh.music, sh.actors, sh.xev = [], [], [], []
        spec = BUILDERS[sh.kind](self, sh)
        shot_common(self, sh, spec)
        if len(self._built) > 4: self._built.clear()
        self._built[sh.idx] = spec
        return spec

    # ---------------------------------------------------------------- frame
    def frame(self, t, i, bg='#000000', overlay=True):
        sh = self.shot_at(t)
        # opt-in shot param tex_seed (popscan v2 chunk-join texture jumps): the shot's grain / stain / frost textures are
        # seeded from the shot (True: its kind and start; a string: that name) instead of the per-process hash
        ts_ = sh.p.get('tex_seed')
        prev_ns = tex_ns(None if not ts_ else (ts_ if isinstance(ts_, str) else '%s@%.2f' % (sh.kind, sh.t0)))
        try:
            return self._frame(sh, t, i, bg, overlay)
        finally:
            tex_ns(prev_ns)

    def _frame(self, sh, t, i, bg, overlay):
        spec = self._build(sh)
        for ts in (getattr(spec, 'pre', None) or []):          # the VHS pause's frozen frames are rendered first
            self.freeze(ts)
        fx = dict(spec.fx(t) if spec.fx else {})
        glob_fx(self, sh, t, fx)
        cs = spec.cam.at(t) if spec.cam is not None else None
        if cs is not None: cs = safe_post(cs)

        def hud_all(cv, tt):
            if spec.hud: spec.hud(cv, tt)
            if overlay: self.overlay(cv, tt, sh)
        focus = spec.focus(t) if callable(spec.focus) else spec.focus
        return render_frame(spec.layers, cs, t, i, focus=focus, dof=spec.dof, lens=spec.lens, grade=spec.grade, post=fx,
                            hud=hud_all, bg=bg)

    def freeze(self, t_src):
        """The picture (no captions / header) at film time t_src at the current render size: the VHS pause's frozen frame."""
        key = (round(t_src, 3), CFG.rw, CFG.rh)
        if key not in self._freeze:
            if len(self._freeze) > 6: self._freeze.clear()
            self._freeze[key] = self.frame(t_src, int(round(t_src * FPS)), overlay=False)
        return self._freeze[key]

    # ---------------------------------------------------------------- captions + header (police / v1 logic)
    def header_text(self, t):
        cur = 'INTRODUCTION'
        for t0, n in self.rules:
            if t >= t0: cur = ('RULE %d OF 7' % n) if n <= 7 else 'RULE 8'
        if len(self.L) > 407 and t >= self.t(407) - LEAD: cur = 'THE END'
        return cur

    def line_at(self, t):
        cur = None
        for l in self.L:
            if l['t'] - 0.05 <= t: cur = l
            else: break
        if cur is None: return None
        if t > cur['end'] + 0.6: return None
        return cur

    @staticmethod
    def chunks(l):
        words = l['en'].split(); out, cur = [], ''
        for w in words:
            if len(cur) + len(w) + 1 > 40 and cur: out.append(cur); cur = w
            else: cur = (cur + ' ' + w).strip()
            if cur.endswith((',', '.', '?', '!', ':')) and len(cur) > 22: out.append(cur); cur = ''
        if cur: out.append(cur)
        return out

    def chunk_at(self, l, t):
        ch = self.chunks(l)
        if len(ch) == 1: return 0, ch
        total = sum(len(c) for c in ch); acc = 0; span = max(0.3, l['end'] - l['t'])
        for k, c in enumerate(ch):
            if t < l['t'] + span * (acc + len(c)) / total or k == len(ch) - 1: return k, ch
            acc += len(c)

    def overlay(self, cv, t, sh):
        if sh.kind == 'black' and not sh.p.get('caption'): return
        if sh.kind not in ('black',):
            header(cv, self.header_text(t), clock_str(t))
        if sh.kind == 'rule': return
        l = self.line_at(t)
        if not l or not l.get('found_en', True): return
        k, ch = self.chunk_at(l, t)
        txt = ch[k]
        if l['who'] != 'N' or l['en'].lstrip().startswith(('"', '\u201c')):
            if k == 0: txt = txt.lstrip('"\u201c\u201d ')                     # the line's own quote marks: never doubled
            if k == len(ch) - 1: txt = txt.rstrip('"\u201c\u201d ')
            if k == 0: txt = '“' + txt
            if k == len(ch) - 1: txt = txt + '”'
        H.caption(cv, txt)

    # ---------------------------------------------------------------- cues
    def cues(self, out_dir=None, write=True):
        sfx, mus = [], []
        for sh in self.shots:
            self._build(sh)
            sfx.extend(sh.sfx); mus.extend(sh.music)
        self._built.clear()
        sfx.extend(beds(self))
        sfx.extend(e for e in self.globals if 'name' in e)
        mus.extend(e for e in self.globals if 'type' in e)
        sfx = [e for e in sfx if 0 <= e['t'] <= self.duration]
        sfx, mus = polish_cues(self, sfx, mus)
        sfx.sort(key=lambda e: (e['t'], e['name']))
        mus.sort(key=lambda e: e['t'])
        music = {'duration': round(self.duration, 2), 'intensity': intensity_curve(self), 'events': mus}
        if write:
            out_dir = out_dir or CUES_DIR
            os.makedirs(out_dir, exist_ok=True)
            json.dump(sfx, open(os.path.join(out_dir, 'sfx_cues.json'), 'w'), indent=0)
            json.dump(music, open(os.path.join(out_dir, 'music_cues.json'), 'w'), indent=0)
            json.dump(shot_table(self), open(os.path.join(out_dir, 'shots.json'), 'w'), indent=0)
        return sfx, music


def safe_post(cs):
    """Keep the post offset inside the post zoom's margin (|px| <= 960 (1 - 1/pz), |py| <= 540 (1 - 1/pz)): past it the post
    move would pad with a mirrored copy of the frame edge."""
    if not (cs.px or cs.py): return cs
    pz = max(1.0, cs.pz)
    mx, my = 960.0 * (1 - 1 / pz), 540.0 * (1 - 1 / pz)
    px, py = clamp(cs.px, -mx, mx), clamp(cs.py, -my, my)
    if px == cs.px and py == cs.py: return cs
    return CamState(cs.x, cs.y, cs.zoom, cs.roll, cs.fz, cs.pz, px, py, cs.vx, cs.vy)


def shot_table(F):
    """The cut list for the sound team: [{i, t0, t1, kind, space, loc, era, cut, room}]."""
    out = []
    for s in F.shots:
        out.append({'i': s.idx, 't0': round(s.t0, 3), 't1': round(s.t1, 3), 'kind': s.kind, 'space': shot_space(s), 'loc': shot_loc(s),
                    'era': s.p.get('era', 'now'), 'cut': s.p.get('cut'), 'room': s.p.get('room') or (s.p.get('bg') or [None])[0]})
    return out


class KeyCam(Cam):
    """Cam whose keys also carry an optical zoom f (no parallax). fkeys [(t, f, ease)] interpolate like the keys."""
    def __init__(self, keys, fkeys, **kw):
        super().__init__(keys, **kw)
        self.fkeys = sorted(fkeys, key=lambda k: k[0])

    def _fz(self, t):
        ks = self.fkeys; f = ks[0][1]
        if t >= ks[-1][0]: f = ks[-1][1]
        elif t > ks[0][0]:
            for a, b in zip(ks, ks[1:]):
                if a[0] <= t <= b[0]:
                    u = ease_fn(b[2] or self.ease)((t - a[0]) / max(1e-9, b[0] - a[0]))
                    f = math.exp(lerp(math.log(a[1]), math.log(b[1]), u)); break
        return super()._fz(t) * f


ENV0 = dict(x=(930, 990), y=(510, 570), zoom=(1.0, 1.06), f=(1.0, 1.4))


def _clampk(v, rng, free=False):
    if free or rng is None: return v
    return clamp(v, rng[0], rng[1])


def scam(sh, env=None, c=None, depth=None):
    """The camera of a shot: c = dict(mv='push' | 'keys' | 'hold', f (optical zoom at the cut), rate (push %/s as optical
    zoom), x, y, x1, y1 (design point on the depth-1 plane; with d=depth they are screen points of a layer at that depth),
    z (dolly), keys=[(t, x, y, z, ease, f)], shake, hit=[t] | [(t, amp)], snap=(t, k), free=True (no env clamp))."""
    c = dict(c or {})
    env = dict(env or ENV0)
    # a view's env must contain its home framing (960, 540); a few sets' envs do not (the porch-egg view): fall back to a box
    if env.get('x') and not (env['x'][0] <= 960 <= env['x'][1]): env['x'] = (900, 1020)
    if env.get('y') and not (env['y'][0] <= 540 <= env['y'][1]): env['y'] = (490, 590)
    free = c.get('free', False)
    t0, t1 = sh.t0, sh.t1
    d = c.get('d', depth)

    def P(x, y):
        if d is not None and c.get('screen'):
            return 960 + d * (x - 960), 540 + d * (y - 540)
        return x, y
    mv = c.get('mv', 'push')
    shake = c.get('shake', 1.1)
    if mv == 'keys':
        ks, fk = [], []
        for k in c['keys']:
            x, y = P(k[1], k[2])
            z = k[3] if len(k) > 3 else 1.0
            e = k[4] if len(k) > 4 else None
            f = k[5] if len(k) > 5 else 1.0
            ks.append((k[0], _clampk(x, env.get('x'), free), _clampk(y, env.get('y'), free), _clampk(z, env.get('zoom'), free), 0.0, e))
            fk.append((k[0], _clampk(f, env.get('f'), free), e))
        cam = KeyCam(ks, fk, shake=shake, seed=sh.idx)
    else:
        x, y = P(c.get('x', 960), c.get('y', 540))
        x1, y1 = P(c.get('x1', c.get('x', 960)), c.get('y1', c.get('y', 540)))
        f0 = c.get('f', 1.0)
        # review r3: a push the plan asks for (f 2-4: inserts, close-ups inside a wide set) was silently clamped to the
        # view's f range (1.8) and its centre range, leaving tiny wides. A zoom-in never shows past the set's edges, so the
        # f cap rises to the request (max 4) and the centre may move as far as the zoom keeps the frame inside the set.
        if not free and env.get('f') and f0 > env['f'][1]:
            fz_ = min(f0, 4.0)
            env['f'] = (env['f'][0], fz_)
            hx, hy = 960.0 * (1.0 - 1.0 / fz_), 540.0 * (1.0 - 1.0 / fz_)
            if env.get('x'): env['x'] = (min(env['x'][0], 960 - hx), max(env['x'][1], 960 + hx))
            if env.get('y'): env['y'] = (min(env['y'][0], 540 - hy), max(env['y'][1], 540 + hy))
        rate = c.get('rate', 0.02) if mv == 'push' else 0.0
        f1 = c.get('f1', f0 * (1.0 + rate) ** max(0.3, sh.d))
        z0 = c.get('z', 1.0); z1 = c.get('z1', z0)
        # polish pass (the owner: no long camera moves): a push that runs longer than 4 s creeps at most 8 % over the shot,
        # so a long shot reads as held while the people in it act (a keyed move is left as designed)
        if mv == 'push' and sh.d > 4.0 and not c.get('long_ok'):
            ratio = (f1 * z1) / max(1e-6, f0 * z0)
            if ratio > 1.08:
                kx = math.log(1.08) / math.log(ratio)
                f1 = f0 * (f1 / f0) ** kx; z1 = z0 * (z1 / z0) ** kx
        ks = [(t0, _clampk(x, env.get('x'), free), _clampk(y, env.get('y'), free), _clampk(z0, env.get('zoom'), free), 0.0, None),
              (t1, _clampk(x1, env.get('x'), free), _clampk(y1, env.get('y'), free), _clampk(z1, env.get('zoom'), free), 0.0, c.get('ease', 'push'))]
        fk = [(t0, _clampk(f0, env.get('f'), free), None), (t1, _clampk(f1, env.get('f'), free), c.get('ease', 'push'))]
        cam = KeyCam(ks, fk, shake=shake, seed=sh.idx)
    for h in c.get('hit', []) or []:
        if isinstance(h, (tuple, list)): cam.hit(h[0], h[1] if len(h) > 1 else 6.0)
        else: cam.hit(h, 6.0)
    if c.get('snap'):
        cam.snap_back = False; cam.snap(c['snap'][0], c['snap'][1] if len(c['snap']) > 1 else 1.2, 0.24)
    if c.get('post'):
        for q in c['post']: cam.post_push(*q)
    return cam


def cam_over(cam, base):
    """A camera dict -> BView overrides: eye=(x, y, Y) at the plan point, look=(x, y, Y) lands at screen (sx, sy) with focal
    length S (design px per metre at 1 m); yaw from the look direction; a shift lens (verticals stay vertical)."""
    c0 = ST.CAMS[base]
    ex, ey, eY = cam['eye']
    lx, ly, lY = cam['look']
    yaw = math.degrees(math.atan2(lx - ex, ly - ey)) + cam.get('yaw_off', 0.0)
    S = float(cam.get('S', c0['S']))
    D = max(0.2, math.hypot(lx - ex, ly - ey))
    sy = float(cam.get('sy', 540.0)); sx = float(cam.get('sx', 960.0))
    h = sy + (lY - eY) * S / D
    if cam.get('pitch'):                                   # a pitched (tilted) camera: its optical axis lands at sy
        h = sy
    ov = dict(S=S, h=h, eye=eY, x=ex, y=ey, yaw=yaw, cx=sx)
    ov['env'] = cam.get('env', dict(ENV0))
    if cam.get('pitch'): ov['pitch'] = cam['pitch']
    return ov

def base_cam(room, view, kw):
    """The CAMS name the builder uses for (room, view)."""
    return _PRE[room] + view


def make_set(room, view, cam=None, **kw):
    """The set `room` seen from `view` (the builder's own camera) or from a custom camera on the same plan (cam dict, see
    cam_over). Built through the sets' own builders, so the far rooms, the outside and the lights are the view's; a
    custom camera gets its own cache key."""
    builder = getattr(ST, ROOMS[room])
    if cam is None:
        return builder(view, **kw)
    base = base_cam(room, view, kw)
    ov = cam_over(cam, base)
    tag = hashlib.md5(json.dumps(ov, sort_keys=True).encode()).hexdigest()[:8]
    orig_cam, orig_bv = ST.cam, ST.build_view

    def cam2(name, **o):
        if name == base: return orig_cam(base, **dict(ov, **o))
        return orig_cam(name, **o)

    def bv2(vname, v_, *a, **k): return orig_bv(vname + '@' + tag, v_, *a, **k)
    ST.cam, ST.build_view = cam2, bv2
    try:
        sp = builder(view, **kw)
    finally:
        ST.cam, ST.build_view = orig_cam, orig_bv
    sp.info['cam_env'] = ov['env']
    return sp



def spot_of(sp, at, Y=None, kind=None):
    """A plan point -> Spot: an anchor name, a Spot, (x, y) or (x, y, Y)."""
    if isinstance(at, str):
        s = sp.anchors[at]
        return s
    if isinstance(at, ST.Spot): return at
    x, y = at[0], at[1]
    YY = at[2] if len(at) > 2 else (Y if Y is not None else 0.0)
    return sp.spot(x, y, YY, kind=kind or 'stand')


def plan_xy(sp, at):
    s = spot_of(sp, at)
    return (s.X, s.Yp, s.Y)


def P(who, at=None, **k):
    """A figure entry for set shots: who, at (anchor | (x, y[, Y])), face=(x, y) plan point to face (or turn=), kind
    ('stand' | 'seat' | 'kneel' | 'lie' | 'floor'), expr, act=f(a, shot), path=[(t, at), ...] (walks between plan points;
    run=True), seat=0.45 (seat height m for a seat at a plan tuple), knees, hands, light (rim dict), sil (silhouette 0..1),
    talk, voice, seed, name, dz (depth nudge), legs_hidden."""
    return dict(who=who, at=at, **k)


def _turn_for(sp, X, Y, face):
    if face is None: return None
    if isinstance(face, str): face = plan_xy(sp, face)[:2]
    return sp.view.turn_for(X, Y, face[0] - X, face[1] - Y)


def acting(F, sh, who, act=None, seed=0, height=700.0, expr=None, talk=True, voice=None, blink=None, intensity=None):
    a = CH.Acting(who, seed=seed + sh.idx * 3, height=height, expr=expr or 'neutral', blink=blink)
    if act: act(a, sh)
    escalate(a, sh, who)
    if talk:
        v = voice if voice is not None else VOICE.get(who, [])
        ls = F.voice_lines(sh.t0, sh.t1, v) if v else []
        if ls:
            for l in ls:
                k = intensity if intensity is not None else (0.55 if l.get('fx') == 'whisper' else (1.15 if l['en'].isupper() else 1.0))
                a.talk([(l['t'], l['end'], l['en'])], intensity=k)
    sh.actors.append(a)
    return a


def _walk_clip(a, legs, surface='inside', run=False, step_m=0.62, gain=-6.0):
    """Walk cycle for plan walks: legs [(t0, t1, dist_m, face_fn)]: walk_amt / walk_ph / turn (no dx: the layer moves);
    footsteps (surface 'inside' wood, 'porch', 'grass', 'stairs', 'heavy' for the Bunnyman, '_quiet' none)."""
    info = []
    quiet = surface.endswith('_quiet')
    name = {'inside': 'footsteps_wood_inside', 'porch': 'footsteps_porch', 'grass': 'footsteps_grass', 'stairs': 'footsteps_wood_inside',
            'heavy': 'footsteps_heavy', 'gravel': 'footsteps_gravel', 'snow': 'snow_walk'}.get(surface.replace('_quiet', ''), 'footsteps_wood_inside')
    if surface.startswith('snow') and run: name = 'snow_run'
    for (t0, t1, dist, face) in legs:
        n = max(2, int(round(dist / (step_m * (1.25 if run else 1.0)))))
        info.append((t0, t1, n / 2.0, face))
        if quiet: continue
        for k in range(1, n + 1):
            pr = dict(n=1, foot='L' if k % 2 else 'R')
            if run: pr['kind'] = 'run'
            if surface == 'stairs': pr['kind'] = 'stair'
            a._ev(t0 + (t1 - t0) * (k - 0.5) / n, name, gain + (2.0 if run else 0.0), pan=0.0, **pr)

    def fn(P_, t):
        for (t0, t1, cyc, face) in info:
            if t0 - 0.45 <= t <= t1 + 0.45:
                amt = ease_in_out(clamp((t - t0 + 0.15) / 0.3)) * ease_in_out(clamp((t1 + 0.15 - t) / 0.3))
                w_ = ease_in_out(clamp((t - t0 + 0.4) / 0.4)) * ease_in_out(clamp((t1 + 0.45 - t) / 0.45))
                P_.walk_amt = max(P_.walk_amt, amt)
                P_.walk_ph = cyc * clamp((t - t0) / max(1e-3, t1 - t0))
                tr = face(t)
                if tr is not None: P_.turn = lerp(P_.turn, tr, w_)
                if run:
                    P_.run = max(getattr(P_, 'run', 0.0), amt); P_.lean += 0.14 * amt
                else:
                    P_.lean += 0.04 * amt
    a._add(legs[0][0] - 0.5, legs[-1][1] + 0.6, fn)


def _ta(torch, t):
    v = torch.get('a', 0.9)
    return v(t) if callable(v) else v


def figure(F, sh, sp, q, k=0, rim=None):
    """One figure on a set (P entry q) -> (Layer, Acting, info). Static figures stand / sit / kneel / lie on their Spot;
    walkers follow plan keys (depth, scale and order follow the plan point)."""
    who = q['who']
    v = sp.view
    path = q.get('path')
    s0 = spot_of(sp, q['at'] if q.get('at') is not None else path[0][1], kind=q.get('kind'))
    kind = q.get('kind') or {'seat': 'seat', 'kneel': 'kneel', 'lie': 'lie', 'floor_sit': 'floor'}.get(s0.kind, 'stand')
    Yf = s0.Y if s0.kind != 'seat' else s0.Y
    h0 = CH.height_px(who, s0.ppm) * q.get('hk', 1.0)
    rot = 0.0
    fore = q.get('fore')
    if fore is None: fore = (kind in ('stand', 'kneel') and not path and getattr(v, 'pitch', 0.0) >= 25.0)
    if fore:
        # a camera looking steeply DOWN (from an upstairs window): a standing figure is drawn at its projected length
        # (feet to crown through the view), leaning along the projected vertical, so it is small and stands ON its spot
        Hm = CH.height_px(who, 100.0) / 100.0 * q.get('hk', 1.0)
        fx_, fy_ = v.p(s0.X, s0.Y, s0.Yp); hx_, hy_ = v.p(s0.X, s0.Y + Hm, s0.Yp)
        L_ = math.hypot(hx_ - fx_, hy_ - fy_)
        if L_ > 8.0:
            h0 = L_ * q.get('fore_k', 1.5)           # a touch over the true projection: small, but readable at 640 px
            rot = math.degrees(math.atan2(hx_ - fx_, -(hy_ - fy_)))
    a = CH.Acting(who, seed=q.get('seed', 0) + k * 11 + sh.idx * 3, height=h0, expr=q.get('expr', 'neutral'), blink=q.get('blink'))
    a.place(s0.x, s0.y + q.get('dy', 0.0))
    a._rot = rot
    tr = q.get('turn')
    if tr is None and q.get('face') is not None: tr = _turn_for(sp, s0.X, s0.Yp, q['face'])
    if tr is None: tr = s0.turn
    if tr is not None and kind == 'seat' and abs(tr) < 0.6 and not q.get('turn_free'):
        tr = math.copysign(0.6, tr)                        # a seat facing the lens reads as standing: turn it to >= 0.6
    if tr is not None: a.face(tr, q.get('h_turn', 0.0))
    if kind == 'seat':
        seat_y = s0.seat_y
        if seat_y is None:
            seat_y = v.p(s0.X, s0.Y + q.get('seat', 0.45), s0.Yp)[1]
        if who == 'later':                                  # Doctor Later folds onto a seat with his own rig
            nm = q['at'] if isinstance(q.get('at'), str) else ''
            a.perch(seat_y, q.get('perch') or ('armchair' if 'armchair' in nm else ('bench' if 'bus' in nm else ('car' if 'back_' in nm else 'plastic'))),
                    knee=q.get('knee'))
        elif q.get('sit_t') is not None:
            a.sit_on(q['sit_t'], seat_y, dur=q.get('sit_dur', 1.0), t1=q.get('stand_t'), hands=q.get('hands', 'lap'))
        else:
            a.seated(seat_y, hands=q.get('hands', 'lap'), t1=q.get('stand_t'))
            if q.get('stand_t') is not None: a.stand_up(q['stand_t'], seat_y=seat_y, hands=q.get('hands', 'lap'))
    elif kind == 'kneel':
        a.kneel_down(q.get('kneel_t', -2.0), q.get('kneel_dur', 0.01), knees=q.get('knees', 1), t1=q.get('rise_t'))
    elif kind == 'lie':
        a.lie(-1.0, q.get('lie_face', 'up'), arms=q.get('arms', 'side'))
        if q.get('cover', True) and 'bed' in str(q.get('at')):         # in bed: the duvet over him (review 1, blocker 1)
            q = dict(q, _extras=list(q.get('_extras', [])) + [_bed_cover(COVER_C.get(str(q.get('at')), '#6a4a5a'))])
    elif kind == 'pillow':
        # lying in bed seen from the bed's foot (review 1, blocker 1): the head rests on the pillow (the spot), the rest of
        # the body is under the quilt (the bed piece draws it): the figure is clipped at the quilt's hem (plan point `hem`)
        a.set(-9.0, None, 0.01, h_tilt=q.get('h_tilt', 12.0))
        hy_ = a.where(sh.t0 + 0.02, 'head')[1]
        q = dict(q, dy=q.get('dy', 0.0) + (s0.y - hy_) - 0.02 * h0)
        if q.get('hem') is not None: q['clip'] = float(spot_of(sp, q['hem']).y)
        bo_ = [ov for k_, ov in sp.info.get('orders', {}).items() if k_ == q.get('bed', 'bed') or k_.startswith(q.get('bed', 'bed') + '_')]
        if bo_ and 'order' not in q: q['order'] = min(bo_) - 0.03                      # in front of the pillow (the clip hides the rest)
        a.place(s0.x, s0.y + q['dy'])
    elif kind == 'floor':
        a.sit_floor(-1.0, None, 0.01)
    if q.get('act'):
        try: q['act'](a, sh)
        except KeyError:                                    # it reaches an actor not placed yet: run it after all are placed
            if getattr(sh, '_defer', None) is None: raise
            sh._defer.append((q['act'], a))
    if kind == 'kneel' or q.get('snap'):
        # ground snap (the owner's rule: nothing sinks into the floor): the rig's kneel can put a knee or a foot below the
        # feet line; the figure is lifted / lowered once so its lowest contact (soles, knee caps) sits ON the anchor's line
        try:
            tm_ = sh.t0 + 0.75 * (sh.t1 - sh.t0)
            hh_ = a.height
            cs_ = [a.where(tm_, 'foot_l')[1] + 0.038 * hh_, a.where(tm_, 'foot_r')[1] + 0.038 * hh_,
                   a.where(tm_, 'knee_l')[1] + 0.017 * hh_, a.where(tm_, 'knee_r')[1] + 0.017 * hh_]
            Pk_ = a.at(tm_)
            low_ = (sum(cs_) / 4.0) if getattr(Pk_, 'kneel', 0.0) > 0.5 else max(cs_)    # kneeling: the knees and the soles
            fix_ = (s0.y + q.get('dy', 0.0)) - low_                                         # straddle the line in depth
            if 1.0 < abs(fix_) < 0.15 * hh_:
                q = dict(q, dy=q.get('dy', 0.0) + fix_)
                a.place(s0.x, s0.y + q['dy'])
        except Exception:
            pass
    child = None
    if q.get('hush'):                                   # a child carried with a hand over the mouth (kept from the engine; unused here)
        hq = q['hush']
        child = CH.Acting(hq['who'], seed=k * 7 + sh.idx, height=CH.height_px(hq['who'], s0.ppm), expr=hq.get('expr', 'sleepy'))
        child.place(s0.x, s0.y)
        _cw0 = child.where
        def _hwhere(t, *args, _cw0=_cw0, _car=a, _ch=child, **kw):       # he is where Sam's arms hold him (as 'carry')
            try:
                x_, y_ = CH.carry_anchor(_car, t); _ch.place(x_, y_)
            except Exception: pass
            return _cw0(t, *args, **kw)
        child.where = _hwhere
        a.carry_hush(hq.get('t0', -9.0), child, hq.get('t1'))
        if hq.get('act'): hq['act'](child, sh)
        sh.actors.append(child)
        if getattr(sh, 'A', None) is not None: sh.A[hq.get('id', hq['who'])] = child
    if q.get('carry'):                                  # a child carried in the arms (draw_carry_child)
        cq = q['carry']
        child = CH.Acting(cq['who'], seed=k * 7 + sh.idx, height=CH.height_px(cq['who'], s0.ppm), expr=cq.get('expr', 'neutral'))
        child.place(s0.x, s0.y)                         # placed every frame at the carrier's arms (draw_carry_child)
        _cw, _car = child.where, a
        def _where(t, *args, _cw=_cw, _car=_car, _ch=child, **kw):
            try:
                x_, y_ = CH.carry_anchor(_car, t); _ch.place(x_, y_)
            except Exception: pass
            return _cw(t, *args, **kw)
        child.where = _where                            # acts that reach / look at her find her in the arms at that time
        a.carry(cq.get('t0', -9.0), child, cq.get('t1'))
        if getattr(sh, 'A', None) is not None: sh.A[cq.get('id', cq['who'])] = child
        if cq.get('act'): cq['act'](child, sh)
        escalate(child, sh, cq['who'])
        sh.actors.append(child)
    escalate(a, sh, who)
    if q.get('talk', True):
        vv = q.get('voice') if q.get('voice') is not None else VOICE.get(who, [])
        for l in (F.voice_lines(sh.t0, sh.t1, vv) if vv else []):
            kk = 0.55 if l.get('fx') == 'whisper' else (1.15 if l['en'].isupper() else 1.0)
            a.talk([(l['t'], l['end'], l['en'])], intensity=kk * q.get('talk_k', 1.0))
    sh.actors.append(a)
    m = _Memo(a)
    lt = q.get('light', rim)
    sil = q.get('sil', 0.0)

    torch = q.get('torch')

    def put(pen, t, x, y, hh):
        if q.get('until') is not None and t >= q['until']: return          # gone from here (e.g. now carried by another figure)
        if rot:
            pen.cv.save(); pen.cv.rotate(rot, x, y)
            try: return _put(pen, t, x, y, hh)
            finally: pen.cv.restore()
        return _put(pen, t, x, y, hh)

    def _put(pen, t, x, y, hh):
        if torch or path:
            a.x0, a.y0, a.height = float(x), float(y), float(hh)
        P_ = m(t)
        if torch and torch.get('behind'):
            beam(pen, t, hh)
        if sil >= 0.999:
            CH.draw_silhouette(pen, who, x, y, hh, P_, t=t, col=q.get('sil_c', '#04060c'), alpha=255, rim=q.get('sil_rim', '#9fb6ff'),
                               rim_side=q.get('sil_side', 1))
        else:
            lt_ = lt(t) if callable(lt) else lt
            clip_ = q.get('clip')
            if clip_:
                cy_ = (spot_of(sp, clip_).y if isinstance(clip_, str) else float(clip_)) + q.get('clip_dy', 4.0)
                pen.cv.save(); pen.cv.clipRect(skia.Rect.MakeLTRB(-6000, -6000, 8000, cy_), skia.ClipOp.kIntersect, True)
            cq_ = q.get('carry')
            if child is not None and q.get('hush'):
                a.x0, a.y0, a.height = float(x), float(y), float(hh)
                child.height = hh * CH.height_px(q['hush']['who'], 100.0) / CH.height_px(who, 100.0)
                CH.draw_carry_walls(pen, a, child, t, lt_, lt_, blanket=True)
            elif child is not None and t >= cq_.get('t0', -9.0) and (cq_.get('t1') is None or t < cq_['t1']):
                a.x0, a.y0, a.height = float(x), float(y), float(hh)
                child.height = hh * CH.height_px(cq_['who'], 100.0) / CH.height_px(who, 100.0)
                CH.draw_carry_child(pen, a, child, t, lt_, lt_)
                if q.get('_cold'): puffs()(pen, t, child)
            else:
                CH.draw(pen, who, x, y, hh, P_, light=lt_, t=t)
            if 0.001 < sil < 0.999:             # half in shadow: the figure, then its dark shape over it (a night stranger)
                CH.draw_silhouette(pen, who, x, y, hh, P_, t=t, col=q.get('sil_c', '#04060c'), alpha=int(255 * sil),
                                   rim=q.get('sil_rim', '#9fb6ff'), rim_side=q.get('sil_side', 1))
            if clip_: pen.cv.restore()
            for fx_ in q.get('_extras', []): fx_(pen, t, a)
        if torch and not torch.get('behind'):
            beam(pen, t, hh)

    def beam(pen, t, hh):
        if True:
            lx, ly, ang = CH.torch_pos3(a, t, torch.get('side', 1))
            tip = getattr(a, '_torch_tip', None) if torch.get('ground') else None
            if tip is not None:
                # fix round 1 (critic 2 M8): the beam lands on the grass ahead of him (a cone to a pool of light on the
                # ground `ground` metres along his walk), never up at the sky
                gx, gy = tip
                L_ = max(20.0, math.hypot(gx - lx, gy - ly))
                ang = math.degrees(math.atan2(gx - lx, -(gy - ly)))
                CH.draw_torch_beam(pen, lx, ly, ang, L_ * 1.05, torch.get('spread', 12.0), _ta(torch, t), t)
                pw = max(18.0, 0.55 * hh * torch.get('pool', 0.5))
                pen.glow(gx, gy, pw, '#fff1c8', 85 * _ta(torch, t))
                pen.fill(oval(gx, gy, pw * 0.95, pw * 0.16), '#fff4d8', 42 * _ta(torch, t), blur=6)
            else:
                CH.draw_torch_beam(pen, lx, ly, ang, torch.get('length', 4.0) * hh, torch.get('spread', 12.0), _ta(torch, t), t)
    name = q.get('name') or 'p%d_%s' % (k, who)
    if path:
        keys = []
        for (tk, at) in path:
            s_ = spot_of(sp, at)
            keys.append((float(tk), s_.X, s_.Yp, s_.Y))
        R = max(0.3, s0.depth)

        def pos(t):
            if t <= keys[0][0]: return keys[0][1:]
            if t >= keys[-1][0]: return keys[-1][1:]
            for ka, kb in zip(keys, keys[1:]):
                if ka[0] <= t <= kb[0]:
                    u = (t - ka[0]) / max(1e-6, kb[0] - ka[0])
                    u = u * u * (3 - 2 * u) * 0.25 + u * 0.75 if not q.get('linear') else u
                    return tuple(ka[j] + (kb[j] - ka[j]) * u for j in (1, 2, 3))
            return keys[-1][1:]
        legs = []
        for ka, kb in zip(keys, keys[1:]):
            dist = math.hypot(kb[1] - ka[1], kb[2] - ka[2])
            if dist < 0.05 or kb[0] - ka[0] < 0.1: continue
            dX, dY = kb[1] - ka[1], kb[2] - ka[2]
            legs.append((ka[0], kb[0], dist, (lambda t, dX=dX, dY=dY: v.turn_for(pos(t)[0], pos(t)[1], dX, dY))))
        if legs and not q.get('no_walk'):
            _walk_clip(a, legs, q.get('surface', 'inside'), q.get('run', False), gain=q.get('step_gain', -6.0))

        def sp_at(t):
            X, Y, YY = pos(t)
            return v.spot(X, Y, YY)

        def dfun(t): return max(0.25, sp_at(t).depth) + q.get('dz', 0.0)

        gd = (keys[-1][1] - keys[0][1], keys[-1][2] - keys[0][2])
        gn = math.hypot(*gd) or 1.0

        def draw(pen, t):
            s_ = sp_at(t)
            kk = max(0.25, s_.depth) / R
            hh = CH.height_px(who, s_.ppm) * q.get('hk', 1.0)
            if torch and torch.get('ground'):                   # where the beam meets the ground ahead of the walker
                X_, Yp_, YY_ = pos(t)
                gx_, gy_ = v.p(X_ + gd[0] / gn * torch['ground'], YY_, Yp_ + gd[1] / gn * torch['ground'])
                a._torch_tip = (960 + (gx_ - 960) * kk, 540 + (gy_ - 540) * kk)
            put(pen, t, 960 + (s_.x - 960) * kk, 540 + (s_.y + q.get('dy', 0.0) - 540) * kk, hh * kk)
        lkw = sp.light_kw(s0.X, s0.Yp, s0.Y + 1.2) if q.get('room_light', True) else ({'dim': q['dimk']} if q.get('dimk') else {})
        lay = Layer(dfun, draw, name, ref_depth=R, alpha=q.get('alpha', 1.0), **lkw)
        lay.order = q.get('order', lambda t: sp.order_at(*pos(t)[:2]))
        info = dict(depth=s0.depth, spot=s0, pos=pos)
        return lay, a, info

    def draw(pen, t):
        put(pen, t, s0.x, s0.y + q.get('dy', 0.0), h0)
    lkw = sp.light_kw(s0.X, s0.Yp, s0.Y + 1.2) if q.get('room_light', True) else ({'dim': q['dimk']} if q.get('dimk') else {})
    lay = Layer(s0.depth + q.get('dz', 0.0), draw, name, ref_depth=s0.depth + q.get('dz', 0.0), alpha=q.get('alpha', 1.0), **lkw)
    lay.order = q.get('order', sp.order_at(s0.X, s0.Yp) + q.get('dorder', 0.0))
    if q.get('order_at'):                                  # outside a doorway: drawn just behind the door frame
        lay.order = sp.order_at(*q['order_at'][:2]) + q['order_at'][2]
    return lay, a, dict(depth=s0.depth, spot=s0)


COVER_C = {'bed': '#3a5a9a'}


def _bed_cover(col, hem='#e6e0d2'):
    """A duvet drawn over a lying figure on a bed (side views; review 1, blocker 1): from under the arms to past the feet,
    as wide as his arms and hands (they lie under it), the sheet's hem folded back over the chest."""
    def fx(pen, t, a):
        try:
            Q = lambda n_: np.array(a.where(t, n_), float)
            nk, hp = Q('neck'), Q('hip')
            ft = (Q('foot_l') + Q('foot_r')) / 2.0
            ax = ft - nk
            L = float(np.hypot(ax[0], ax[1]))
            if L < 5.0: return
            u = ax / L
            n = np.array([-u[1], u[0]])
            if n[1] < 0: n = -n                                   # n: down the screen (the near side of the bed)
            ds = [float(np.dot(Q(k_) - nk, n)) for k_ in ('hand_l', 'hand_r', 'elbow_l', 'elbow_r', 'shoulder_l', 'shoulder_r',
                                                         'knee_l', 'knee_r', 'foot_l', 'foot_r')]
            wf, wn = -min(ds) + 0.05 * L, max(ds) + 0.09 * L
            A = nk + u * max(0.12 * L, 0.3 * float(np.dot(hp - nk, u)))
            B = ft + u * 0.07 * L
            M = (A + B) / 2.0
            pts = [A - n * wf, M - n * (wf + 0.02 * L), B - n * (wf * 0.8), B + u * 0.035 * L, B + n * (wn * 0.9),
                   M + n * (wn + 0.015 * L), A + n * wn]
            path = smooth([tuple(p_) for p_ in pts], True, 0.6)
            pen.fill(path, col)
            pen.line(path, None, '#1c1820', 200)
            for k_ in (0.42, 0.7):                                # two soft folds across the duvet
                c_ = A + (B - A) * k_
                pen.line(poly([tuple(c_ - n * wf * 0.7), tuple(c_ + u * 0.03 * L), tuple(c_ + n * wn * 0.7)], False), None, '#000000', 60)
            h0_, h1_ = A - n * (wf + 0.01 * L), A + n * (wn + 0.01 * L)
            band = poly([tuple(h0_), tuple(h1_), tuple(h1_ + u * 0.06 * L), tuple(h0_ + u * 0.06 * L)])
            pen.fill(band, hem)
            pen.line(band, None, '#1c1820', 160)
        except Exception:
            pass
    return fx


def prop_layer(sp, track, at, name='prop', order_dz=-0.05):
    """A resting PropTrack drawn at its plan point's depth (it disappears while a hand holds it)."""
    s = spot_of(sp, at)
    lay = Layer(s.depth, lambda pen, t: track.draw(pen, t), name, ref_depth=s.depth)
    lay.order = sp.order_at(s.X, s.Yp) + order_dz
    return lay


def ptrack(sp, name, at, dx=0.0, dy=0.0, angle=0.0):
    s = spot_of(sp, at)
    return ST and CH.PropTrack(name, s.x + dx, s.y + dy, s.ppm / 100.0, angle)

def _fx(sp, p):
    def fx(t):
        d = dict((sp.fx(t) if sp is not None and hasattr(sp, 'fx') else None) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return fx


def dimmed(sp, k, keep=()):
    for l in sp:
        if l.name not in keep and not callable(l.dim): l.dim = max(l.dim if isinstance(l.dim, (int, float)) else 0.0, k)
    return sp



class ADict(dict):
    """The shot's actors by id; 'sam' / 'mom' / 'dad' / 'pell' also find the costume variant placed in the shot (ALIAS)."""
    def _k(self, k):
        if dict.__contains__(self, k): return k
        for v in ALIAS.get(k, ()):
            if dict.__contains__(self, v): return v
        return None
    def __missing__(self, k):
        kk = self._k(k)
        if kk is None: raise KeyError(k)
        return dict.__getitem__(self, kk)
    def __contains__(self, k): return self._k(k) is not None


def B_set(F, sh):
    """A set view with figures on the plan (see the module docstring)."""
    p = sh.p
    sp = make_set(p['room'], p['view'], p.get('cam'), **p.get('set', {}))
    sh.sp = sp
    rim = p.get('rim', ROOM_RIM.get(p['room']))
    L, A, I = [], ADict(), {}
    sh.A = A                                  # acts can reach actors placed before them (s.A['mina']); later ones are deferred
    sh._defer = []
    ppl = list(p.get('ppl', []))
    for k, q in enumerate(ppl):
        q = dict(q)
        ex_ = list(q.get('extras', []))
        cold = bool(p.get('cold') or q.get('breath'))
        if cold and q.get('breath', True) is not False and not q['who'].startswith('shiver'): ex_.append(puffs(hide_back=bool(p.get('breath_back_off'))))
        q['_extras'] = ex_; q['_cold'] = cold and q.get('breath', True) is not False
        lay, a, info = figure(F, sh, sp, q, k, rim)
        L.append(lay); key = q.get('id', q['who']); A[key] = a; I[key] = info
        info['layer'] = lay
    for fn, a_ in sh._defer: fn(a_, sh)       # acts that reach an actor placed after them
    sh._defer = []
    sh.I = I                                  # acts can draw in a walker's own layer space (I[who]['layer'] depth / ref_depth)
    if p.get('acts'):
        L += [l for l in (p['acts'](A, sh, sp) or []) if l is not None]
    if p.get('bg_dim'): dimmed(sp, p['bg_dim'])
    if p.get('focus') is not None:
        focus = p['focus']
    elif I:
        first = p.get('focus_on') or list(I)[0]
        focus = I[first]['depth']
    else:
        focus = sp.focus
    cam = scam(sh, sp.info.get('cam_env'), _c_on(sh, sp, p.get('c'), A))
    grade = p.get('grade', sp.grade)
    sh.A = A
    if p.get('cull'): sp = sp.without(*p['cull'])          # set pieces this camera must not see (a prop at its near plane)
    return Spec(sp.add(*L), cam, p.get('lens', sp.lens), grade, focus, p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


# ==================================================================================================== builders: busts
# framing presets (cx, cy, scale, body turn, head turn): rotated so the same face never sits twice in a row in the same spot
BUST_FRAMES = {
    'default': [(960, 600, 0.82, 0.0, 0.0), (1120, 620, 0.78, -0.35, 0.05), (800, 620, 0.78, 0.35, -0.05), (960, 640, 0.95, 0.0, 0.0)],
}


def bust_eyes(who, cx, cy, scale):
    """Design point between the eyes of a bust drawn at (cx, cy, scale) facing front (for hands over the eyes)."""
    sp = CH.CAST[who]
    k = 600.0 * scale / sp['hh']
    return cx, cy + sp['eye_y'] * k


def bust_place(who, cx, cy, scale):
    """The full-figure placement (x, y_feet, height) that draws the head where draw_bust(cx, cy, scale) does, so look_at /
    reach_to / hand_over work in close-ups too."""
    hh = CH.CAST[who]['hh']
    s = 600.0 * scale / hh
    return cx, cy + (1000.0 - hh / 2.0) * s, 1000.0 * s


def bust_layer(F, sh, who, cx, cy, scale, act=None, expr=None, light=None, depth=1.0, voice=None, name=None, seed=0, talk=True, blink=None):
    """cx / cy may be functions of t (a bust pulled across the frame); the acting is placed at their start values."""
    cx0 = cx(sh.t0) if callable(cx) else cx
    cy0 = cy(sh.t0) if callable(cy) else cy
    bx, by, bh = bust_place(who, cx0, cy0, scale)
    pre = lambda a_, s_: a_.place(bx, by, bh)
    a = acting(F, sh, who, (lambda a_, s_: (pre(a_, s_), act and act(a_, s_))), seed=seed, expr=expr, voice=voice, talk=talk, blink=blink)
    m = _Memo(a)
    lt = light

    def draw(pen, t):
        CH.draw_bust(pen, who, cx(t) if callable(cx) else cx, cy(t) if callable(cy) else cy, scale, m(t), light=lt(t) if callable(lt) else lt, t=t)
    lay = Layer(depth, draw, name or 'bust_' + who, blur=0)
    lay._m = m
    return lay, a


def _sleeve_poly(x0, y0, x1, y1, w0, w1):
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n, dx / n
    return poly([(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1), (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)])


SLEEVE = {'mom': ('#d7a3a8', '#b07e86'), 'mom_scratched': ('#d7a3a8', '#b07e86'), 'narrator': ('#8fae8a', '#6c8a68'),
          'bunny87': ('#a7abb5', '#7a7f8b'), 'bunny': ('#5d5f66', '#3f4148'), 'grandma': ('#b9a6d6', '#8f7cb0'),
          'june': ('#a8e0c8', '#7cb8a0'), 'narrator_new': ('#8fae8a', '#6c8a68')}


# ==================================================================================================== hero hands
# Hands seen big (inserts, a hand over the eyes, a hand toward the lens) are drawn with the cast's own hand geometry
# (characters._hand_geom: the same fingers, nails and creases as the figures) but finished for their size: skin shaded
# across the hand toward the light, soft knuckle highlights, nails with a glint, thin creases in a skin tone (not red
# lines), a wrist, the character's own sleeve (the cast's colours) with its cuff (knit rib for the cardigans and the
# hoodie, a hem for the pyjamas), folds and the fabric's grain, and at dawn Mom's pushed-up sleeve over a scratched
# forearm. The Bunnyman's paws get fur: a shaded mitten, tufts along the edge, pads, mud on the filthy suit.
CUFF = {'cardigan3': 'rib', 'gran3': 'rib', 'hoodie3': 'rib', 'pj3': 'hem', 'dress3': 'puff', 'jacket3': 'hem', 'gown3': 'hem',
        'police': 'button', 'labcoat3': 'hem', 'neat3': 'hem'}


def _arm_dir(angle):
    a = math.radians(angle)
    return math.sin(a), -math.cos(a)                    # from the wrist toward the elbow (fingers point the other way)


def _tube_q(x0, y0, x1, y1, w0, w1):
    return _sleeve_poly(x0, y0, x1, y1, w0, w1)


def hero_sleeve(pen, who, wx, wy, ex, ey, k, bare=0.0, scratch=0.0, light=None, cuff=None, t=0.0):
    """The forearm from the wrist (wx, wy) toward the elbow end (ex, ey) (off frame), k = design px per hand unit:
    `bare` hand units of skin above the wrist (a pushed-up sleeve), then the sleeve with its cuff."""
    sp = CH.CAST[who]
    skin, skin_sh, skin_dp = CH._skin_cols(sp, CH.Pose(), light)
    try:
        sl, sl_sh = CH._limb_cols3(sp)[:2]
    except Exception:
        sl, sl_sh = SLEEVE.get(who, ('#8a8a8a', '#666666'))
    L = math.hypot(ex - wx, ey - wy) or 1.0
    ux, uy = (ex - wx) / L, (ey - wy) / L
    nx, ny = -uy, ux
    lw = max(1.6, 1.15 * k)
    side_lit = 1.0 if (light or {}).get('side', -1) > 0 else -1.0
    # bare forearm (skin): tapered from the wrist, shaded across, scratches when Mom has fought
    b = clamp(bare * k, 0.0, L * 0.85)
    if b > 2:
        cx, cy = wx + ux * b, wy + uy * b
        arm = _tube_q(wx, wy, cx + ux * 6 * k, cy + uy * 6 * k, 15.5 * k, 19.5 * k)
        pen.fill(arm, skin)
        pen.linear(arm, wx + nx * 18 * k * side_lit, wy + ny * 18 * k * side_lit, wx - nx * 18 * k * side_lit, wy - ny * 18 * k * side_lit,
                   [(0, '#ffffff', 46), (0.45, skin, 0), (1, skin_sh, 175)])
        if scratch > 0:
            rng = np.random.default_rng(7)
            for j in range(int(9 * scratch)):
                u0 = rng.uniform(0.08, 0.92); off = rng.uniform(-0.75, 0.75)
                ang = rng.uniform(-0.9, 0.9); ln = rng.uniform(5, 11) * k
                px, py = wx + ux * b * u0 + nx * off * 15 * k, wy + uy * b * u0 + ny * off * 15 * k
                dx_, dy_ = (ux * math.cos(ang) - nx * math.sin(ang)), (uy * math.cos(ang) - ny * math.sin(ang))
                q0, q1 = (px - dx_ * ln / 2, py - dy_ * ln / 2), (px + dx_ * ln / 2, py + dy_ * ln / 2)
                pen.seg(q0, q1, max(1.4, 1.5 * k), '#e9a39a', 150)              # the welt
                pen.seg(q0, q1, max(0.8, 0.55 * k), '#8a1f24', 225)             # the cut
        pen.line(arm, lw, CH.LINE, 230)
        wx, wy = cx, cy
    # the sleeve
    w0, w1 = 21.0 * k, 26.0 * k
    tube = _tube_q(wx, wy, ex, ey, w0, w1)
    pen.fill(tube, sl)
    pen.linear(tube, wx + nx * w0 * side_lit, wy + ny * w0 * side_lit, wx - nx * w0 * side_lit, wy - ny * w0 * side_lit,
               [(0, '#ffffff', 40), (0.35, sl, 0), (0.8, sl_sh, 150), (1, sl_sh, 220)])
    try:
        pen.texture(tube, 'fabric', 0.32, 'overlay', max(0.6, k * 0.35))
    except Exception:
        pass
    # folds where the sleeve bunches above the cuff
    for j, (u0, d0) in enumerate(((0.18, 0.55), (0.30, -0.35), (0.46, 0.2))):
        if u0 * L > L - 8 * k: break
        px, py = wx + ux * (u0 * min(L, 140 * k)), wy + uy * (u0 * min(L, 140 * k))
        a0 = (px + nx * w0 * 0.85, py + ny * w0 * 0.85); a1 = (px - nx * w0 * 0.85 + ux * 10 * k * d0, py - ny * w0 * 0.85 + uy * 10 * k * d0)
        mid = ((a0[0] + a1[0]) / 2 + ux * 7 * k, (a0[1] + a1[1]) / 2 + uy * 7 * k)
        pen.line(smooth([a0, mid, a1], False), max(1.0, 0.9 * k), sl_sh, 120)
    pen.line(tube, lw, CH.LINE, 235)
    # the cuff
    kind = cuff or CUFF.get(sp.get('outfit'), 'hem')
    cl = 15.0 * k if kind == 'rib' else 7.0 * k
    band = _tube_q(wx - ux * 2 * k, wy - uy * 2 * k, wx + ux * cl, wy + uy * cl, w0 * 0.98, w0 * 1.02)
    pen.fill(band, CH.mix(sl, sl_sh, 0.25))
    if kind == 'rib':
        for j in range(-6, 7):
            o_ = j / 6.5 * w0 * 0.95
            pen.seg((wx + nx * o_, wy + ny * o_), (wx + nx * o_ + ux * cl, wy + ny * o_ + uy * cl), max(0.8, 0.55 * k), sl_sh, 150)
    else:
        pen.line(_tube_q(wx + ux * cl * 0.55, wy + uy * cl * 0.55, wx + ux * cl * 0.56, wy + uy * cl * 0.56, w0 * 0.9, w0 * 0.9),
                 max(0.8, 0.45 * k), sl_sh, 170)
    pen.line(band, lw, CH.LINE, 235)


def hero_hand(pen, who, x, y, size, shape='open', angle=0.0, side=1, sleeve_to=None, light=None, press=0.0, t=0.0,
              bare=0.0, scratch=0.0, shadow=None, ring=None, cuff=None):
    """One big hand: wrist at (x, y), size = wrist-to-fingertip length (design px), angle 0 = fingers down; the arm runs
    to sleeve_to (off frame). shadow = (dx, dy, blur, alpha): the hand's soft shadow on what it lies on (a face)."""
    sp = CH.CAST[who]
    if sp.get('bunny'):
        return hero_paw(pen, who, x, y, size, shape, angle, side, sleeve_to, light, t, shadow)
    k = size / 66.0 * sp['body'].get('hand', 1.0)
    G = CH._hand_cached(shape, side, round(press, 1))
    u = G['union']
    skin, skin_sh, skin_dp = CH._skin_cols(sp, CH.Pose(), light)
    m = skia.Matrix(); m.setTranslate(x, y); m.preRotate(angle); m.preScale(k, k)
    hu = skia.Path(u); hu.transform(m)
    dxa, dya = _arm_dir(angle)
    ex, ey = sleeve_to if sleeve_to is not None else (x + dxa * size * 3.0, y + dya * size * 3.0)
    if shadow:
        sdx, sdy, sbl, sa = shadow
        pen.fill(moved(hu, sdx, sdy), '#120806', sa, blur=sbl)
        sh_arm = _tube_q(x, y, ex, ey, 22 * k, 27 * k)
        pen.fill(moved(sh_arm, sdx, sdy), '#120806', sa * 0.8, blur=sbl)
    hero_sleeve(pen, who, x + dxa * 2 * k, y + dya * 2 * k, ex, ey, k, bare, scratch, light, cuff, t)
    # the hand
    c = CH.Ctx(pen, m, 1.0)
    lit = 1.0 if (light or {}).get('side', -1) > 0 else -1.0
    c.fill(u, skin)
    c.grad(u, 22 * lit * side, 10, -22 * lit * side, 30, [(0, '#fff3ea', 70), (0.4, skin, 0), (0.85, skin_sh, 120), (1, skin_sh, 170)])
    c.fill(G['shade'], skin_sh, 110)
    # knuckles: soft highlights at the finger roots, a darker dimple between them
    if shape in ('open', 'flat', 'wave', 'relaxed', 'palm4', 'point', 'fist', 'grip', 'knock'):
        for j, off in enumerate((-1.45, -0.48, 0.48, 1.45)):
            bx = -side * off * 9.6
            by = 31.0 - abs(off) * 2.0 if shape not in ('fist', 'grip', 'knock') else 30.0
            c.glow(bx, by - 1.5, 5.2, 3.0, '#fff4ec', 70)
            c.fill(oval(bx + 4.6 * (1 if off < 1 else 0), by + 1.0, 1.0, 1.6), skin_sh, 70)
    if G['seps'] is not None and shape != 'mitt':
        c.line(G['seps'], 0.55, CH.mix(skin_dp, skin_sh, 0.5), 130)
    if G['creases_p'] is not None:
        c.line(G['creases_p'], 0.42, CH.mix(skin_sh, skin_dp, 0.35), 105)
    if G['lines_p'] is not None:
        c.line(G['lines_p'], 0.42, CH.mix(skin_sh, skin_dp, 0.35), 95)
    nailc = CH.mix(skin, '#ffffff', 0.42)
    for pth in G['nails']:
        c.fill(pth, nailc, 235)
        bb = pth.getBounds()
        c.fill(oval(bb.centerX() - bb.width() * 0.15, bb.centerY() - bb.height() * 0.1, bb.width() * 0.18, bb.height() * 0.22), '#ffffff', 120)
        c.line(pth, 0.35, CH.mix(skin_sh, skin_dp, 0.5), 170)
    c.line(u, max(0.75, 1.5 / max(0.4, k)), CH.LINE, 240)
    if ring and G['ring'] is not None:
        CH._ring_band(c, G['ring'], 2, t)


def pen_geom(x, y, ang, sz, tilt=-34.0):
    """A ballpoint held in a 'grip' hero hand (wrist (x, y), angle ang, size sz): (tip, back) design points; the pen runs
    through the fist, tilted `tilt` degrees off the fingers' direction, its tip just beyond the curled fingers."""
    a = math.radians(ang); dx, dy = -math.sin(a), math.cos(a)
    b = math.radians(ang + tilt); px, py = -math.sin(b), math.cos(b)
    cx, cy = x + dx * sz * 0.52, y + dy * sz * 0.52
    return (cx + px * sz * 0.42, cy + py * sz * 0.42), (cx - px * sz * 0.62, cy - py * sz * 0.62)


def draw_pen(pen, tip, back, sz, body='#1d3f8a'):
    """A plain blue ballpoint from its tip to its back end (design px)."""
    (x0, y0), (x1, y1) = tip, back
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    w = sz * 0.034
    cone = sz * 0.07
    bx, by = x0 + ux * cone, y0 + uy * cone
    pen.fill(_sleeve_poly(bx, by, x1, y1, w, w), body)
    pen.fill(_sleeve_poly(bx, by, x1, y1, w * 0.35, w * 0.35), '#5f86d8', 120)
    pen.fill(poly([(x0, y0), (bx - uy * w, by + ux * w), (bx + uy * w, by - ux * w)]), '#c9ccd2')
    pen.fill(_sleeve_poly(x1 - ux * sz * 0.05, y1 - uy * sz * 0.05, x1 + ux * sz * 0.03, y1 + uy * sz * 0.03, w * 0.6, w * 0.6), '#d8dbe2')
    pen.line(_sleeve_poly(bx, by, x1, y1, w, w), max(1.2, sz * 0.006), '#0d1530')


def hand_layer(who, fn, size, shape='open', side=1, depth=0.9, sleeve_from=None, scratch=False, name='hand', paw=False,
               light=None, shadow=True, bare=None, held_pen=False):
    """A hand in a close-up or an insert: fn(t) -> (x, y, angle, alpha[, size]) | None (design px, angle 0 = fingers
    down); the arm runs from the wrist to sleeve_from (x, y) (off frame). Drawn by hero_hand / hero_paw (the cast's hand
    geometry, shaded, with the character's own sleeve and cuff); scratch=True: Mom at dawn, her cardigan sleeve pushed
    up over a scratched forearm. shadow: its soft shadow on what it lies on."""
    who_ = who if who in CH.CAST else 'mom'

    def draw(pen, t):
        r = fn(t)
        if r is None: return
        x, y, ang, al = r[:4]
        sz = r[4] if len(r) > 4 else size
        if al <= 0.01: return
        cv = pen.cv
        if al < 0.999: cv.saveLayerAlpha(None, int(255 * al))
        sf = (sleeve_from(t) if callable(sleeve_from) else sleeve_from) if sleeve_from is not None else None
        shd = (sz * 0.025, sz * 0.045, sz * 0.05, 95) if shadow else None
        bl = r[5] if len(r) > 5 else 0.0                     # out of focus (a hand coming at the lens)
        dk = r[6] if len(r) > 6 else 0.0                     # in its own shadow (blocking the light)
        lt = dict(light or {}); lt['key'] = lt.get('key', 0.0) - 0.9 * dk
        if bl > 0.5:
            cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(bl * CFG.rw / 1920.0, bl * CFG.rw / 1920.0)))
        b = bare if bare is not None else (34.0 if scratch else 0.0)
        if held_pen:
            tip, back = pen_geom(x, y, ang, sz)
            draw_pen(pen, tip, back, sz)
        hero_hand(pen, who_, x, y, sz, shape, ang, side, sf, lt, 0.0, t, bare=b, scratch=1.0 if scratch else 0.0, shadow=shd,
                  ring=(CH.CAST[who_].get('ring') == side))
        if bl > 0.5: cv.restore()
        if al < 0.999: cv.restore()
    return Layer(depth, draw, name, blur=0)


def _draw_order(l):
    """The depth a layer is sorted by in the composite (its .order when it has one: room shells, the outside and the far
    rooms carry big orders and are drawn first whatever their projected depth)."""
    o = getattr(l, 'order', None)
    try:
        return float(o(0.0)) if callable(o) else (float(o) if o is not None else l.depth_at(0.0))
    except Exception:
        return l.depth_at(0.0)


def win_sill_layer(ys=940.0, jamb=True, name='win_sill'):
    """Review (he read as standing in the street in his window busts): the serving window's own frame IN FRONT of him:
    the counter ledge across the bottom (frosted, lit pink from inside, its shadow on his coat) over the striped truck
    wall, and the jambs at the frame edges. A flat foreground layer of the window busts."""
    def draw(pen, t):
        pen.linear(rect(-500, ys - 90, 2920, 92), 0, ys - 90, 0, ys, [(0, '#14060e', 0), (1, '#14060e', 150)])    # his coat in the ledge's shadow
        wall = rect(-500, ys + 12, 2920, 900)
        pen.fill(wall, '#f2e6ee')
        for k in range(-6, 26):
            pen.fill(rect(-500 + k * 120 + 40, ys + 12, 60, 900), '#e2709e', 235)
        pen.linear(wall, 0, ys, 0, ys + 260, [(0, '#2a0c1c', 60), (1, '#0c0610', 200)])
        pen.fill(rect(-500, ys - 30, 2920, 46), '#fbf4f8'); pen.fill(rect(-500, ys - 30, 2920, 9), '#ffd6ea', 230)
        pen.fill(rect(-500, ys + 10, 2920, 8), '#1a0c14', 160); pen.line(rect(-500, ys - 30, 2920, 46), 3.0, '#2a1420', 220)
        for k in range(26):                                    # frost along the ledge, short icicles under it
            x = -200 + k * 92 + 40 * hash01(k, 77)
            pen.fill(oval(x, ys - 30, 34 + 22 * hash01(k, 78), 7), '#ffffff', 220)
            ln = 18 + 34 * hash01(k, 79)
            pen.fill(poly([(x - 7, ys + 14), (x + 7, ys + 14), (x + 1, ys + 14 + ln)], True), '#eaf4ff', 210)
        if jamb:
            for x0, x1 in ((-500, 46), (1874, 2420)):
                jr = rect(x0, -500, x1 - x0, ys - 470)
                pen.fill(jr, '#f2e6ee'); pen.linear(jr, 0, -500, 0, ys, [(0, '#3a1428', 120), (1, '#1a0a14', 150)])
                pen.line(poly([(x1 if x0 < 0 else x0, -500), (x1 if x0 < 0 else x0, ys - 28)], False), 9.0, '#fbf4f8', 235)
    return Layer(0.8, draw, name, blur=0)


def B_bust(F, sh):
    """A face close-up over a blurred, darkened set: p who, bg=(room, view[, cam]) + set=dict(..), cx, cy, scale, turn,
    h_turn (or a framing preset), act, expr, light; busts=[dict(who, cx, cy, scale, act, expr, light, depth)] more faces;
    hands=[dict(who, fn, size, shape, side, sleeve_from, depth)]; plain=(c1, c2) a plain gradient background instead."""
    p = sh.p
    who = p['who']
    if p.get('bg'):
        bg = p['bg']
        st_ = dict(p.get('set', {}))
        if who == 'shiver' and bg[1] == 'window_close' and st_.get('truck') == 'B' and p.get('win_a', True):
            st_['truck'] = 'A'      # review M7: the window_close camera is built on the truck at A; at B it saw the street behind him
        sp = make_set(bg[0], bg[1], bg[2] if len(bg) > 2 else None, **st_)
        dimmed(sp, p.get('bg_dim', 0.28))
        # a close-up's background is behind the face: near set pieces (a crowd cut-out, a door frame at arm's length)
        # would be drawn over the face, so they are left out
        layers = [l for l in sp if _draw_order(l) >= p.get('bg_near', 1.3)]
        lens = None; grade = p.get('grade', sp.grade); sfx_fn = sp
    else:
        c1, c2 = p.get('plain', ('#1c2030', '#0c0e16'))
        layers = [Layer(4.0, lambda pen, t, c1=c1, c2=c2: pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, [c1, c2]), 'plain_bg',
                        cache='film:plain:%s:%s' % (c1, c2), bounds=(-1200, -900, 3120, 1980))]
        if p.get('bg_fn'):                                 # a drawn background instead (Dad's plow cab)
            layers = [Layer(4.0, p['bg_fn'], 'bg_fn', blur=p.get('bg_blur', 6.0), bounds=(-1200, -900, 3120, 1980))]
        sp = None; lens = None; grade = p.get('grade', 'face_close'); sfx_fn = None
    fr = BUST_FRAMES['default'][sh.idx % 4]
    cx, cy, sc = p.get('cx', fr[0]), p.get('cy', fr[1]), p.get('scale', fr[2])
    # review round 3: HIS close-ups frame the FACE (eyes about a third from the top; the tall hat leaves the frame).
    # His rest head centre sits on his eyes, so cy is lifted to eye_to; hands / acts / extra busts move with it.
    fdy = 0.0
    if who in ('shiver',) and not callable(cy) and p.get('face_fix', True):
        fdy = min(0.0, p.get('eye_to', 430.0) - cy); cy = cy + fdy
    tr, ht = p.get('turn', 0.0), p.get('h_turn', 0.0)
    base = lambda a, s: a.set(s.t0 - 3, None, 0.1, turn=tr, h_turn=ht)
    act = p.get('act')
    lay, a = bust_layer(F, sh, who, cx, cy, sc, lambda a_, s: (base(a_, s), act and act(a_, s)), expr=p.get('expr'),
                        light=p.get('light', ROOM_RIM.get((p.get('bg') or ['x'])[0], LAMP)), seed=p.get('seed', 0), blink=p.get('blink'),
                        depth=p.get('depth', 1.0))      # depth > a set piece's: the face is BEHIND it (Mom outside the door glass)
    if who == 'shiver' and p.get('mfit', True) and not callable(cy) and not p.get('rot'):
        # cast round 3: the MONSTER head grows x1.8 and thrusts at the lens, so a bust framed for the man showed only the
        # eyes (crown and jaw cut). Monster busts are re-framed on the whole mask: eyes ~36% down, the jaw in frame.
        mons = 0.0
        for u_ in (0.2, 0.5, 0.85):
            P_ = a.at(sh.t0 + u_ * (sh.t1 - sh.t0))
            mons = max(mons, float(getattr(P_, 'sh_m', 0.0)), clamp(float(getattr(P_, 'sh_legs', 0.0)) / 2.0))
        if mons > 0.48:
            sc2 = min(sc, p.get('mscale', 0.48)); cy2 = p.get('meye', 370.0) + 82.0 * sc2
            sh.actors.remove(a)
            fdy += cy2 - cy; cy, sc = cy2, sc2
            lay, a = bust_layer(F, sh, who, cx, cy, sc, lambda a_, s: (base(a_, s), act and act(a_, s)), expr=p.get('expr'),
                                light=p.get('light', ROOM_RIM.get((p.get('bg') or ['x'])[0], LAMP)), seed=p.get('seed', 0), blink=p.get('blink'))
    sh.A = ADict({who: a})
    sill_ = p.get('sill', who == 'shiver' and (p.get('bg') or ('', ''))[1] == 'window_close' and p.get('scale', fr[2]) <= 1.6 and not p.get('hands'))
    on_ = list(p.get('on', []))
    if p.get('cold') and not who.startswith('shiver'): on_.append(puffs())
    if on_:
        def odraw(pen, t, d0_=lay.draw, a=a, on_=on_):
            d0_(pen, t)
            for f_ in on_: f_(pen, t, a)
        lay.draw = odraw
    if p.get('rot'):                                       # the whole face turned in the frame (lying on the floor, from above)
        d0, r_ = lay.draw, float(p['rot'])

        def rdraw(pen, t, d0=d0, r_=r_):
            cv = pen.cv
            cv.save(); cv.translate(960, 540); cv.rotate(r_); cv.translate(-960, -540)
            d0(pen, t)
            cv.restore()
        lay.draw = rdraw
    extra = []
    for k, b in enumerate(p.get('busts', [])):
        tr2, ht2 = b.get('turn', 0.0), b.get('h_turn', 0.0)
        act2 = b.get('act')
        l2, a2 = bust_layer(F, sh, b['who'], b['cx'], b['cy'], b['scale'],
                            (lambda tr2, ht2, act2: lambda a_, s: (a_.set(s.t0 - 3, None, 0.1, turn=tr2, h_turn=ht2), act2 and act2(a_, s)))(tr2, ht2, act2),
                            expr=b.get('expr'), light=b.get('light', p.get('light', LAMP)), depth=b.get('depth', 1.02 + 0.02 * k),
                            name='bust%d_%s' % (k, b['who']), seed=k + 5)
        if p.get('cold') and not b['who'].startswith('shiver'):
            def odraw2(pen, t, d0_=l2.draw, a=a2):
                d0_(pen, t); puffs()(pen, t, a)
            l2.draw = odraw2
        extra.append(l2); sh.A[b.get('id', b['who'])] = a2
    for hd in p.get('hands', []):
        extra.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand'), held_pen=hd.get('pen', False)))
    if p.get('acts'):
        extra += [l for l in (p['acts'](sh.A, sh, None) or []) if l is not None]
    if fdy:
        for l_ in extra:
            if getattr(l_, 'name', '').startswith('bust'): continue
            def mdraw(pen, t, d0=l_.draw, dy=fdy):
                pen.cv.save(); pen.cv.translate(0.0, dy); d0(pen, t); pen.cv.restore()
            l_.draw = mdraw
    if sill_:                                            # (after the face-fix shift: the frame does not move with him)
        extra.append(win_sill_layer(p.get('sill_y', 940.0) if sill_ is True else float(sill_)))
    cxs, cys = (cx(sh.t0) if callable(cx) else cx), (cy(sh.t0) if callable(cy) else cy)
    c = dict(p.get('c') or dict(mv='push', x=960 + (cxs - 960) * 0.25, y=cys - 40, rate=0.0))
    c.setdefault('free', True)
    if c.get('mv', 'push') == 'push' and 'z1' not in c:
        c['z1'] = (1.0 + c.get('zrate', 0.022)) ** max(0.3, sh.d)
    cam = scam(sh, None, c)

    def fx(t):
        d = dict((sfx_fn.fx(t) if sfx_fn is not None else None) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(layers + [lay] + extra, cam, lens, grade, 1.0, p.get('dof', 6.75), fx=fx, hud=p.get('hud'))


def strike_layer(t0, x0, y0, x1, y1, w=26.0, dur=0.45, c='#d8262e'):
    """A red marker line struck through something (the outro: no Holloway, no Pemberton's)."""
    def draw(pen, t):
        u = ease_out_cubic(clamp((t - t0) / dur))
        if u <= 0: return
        pen.seg((x0, y0), (lerp(x0, x1, u), lerp(y0, y1, u)), w, c, 235)
    return Layer(0.99, draw, 'strike', blur=0)

SLEEVE.update({'mina': ('#8fa08a', '#6c7d68'), 'mina_bare': ('#8fa08a', '#6c7d68'), 'sami': ('#5f9a52', '#467a3c'),
               'sami_torn': ('#5f9a52', '#467a3c'), 'della': ('#2f3f62', '#22304c')})
CUFF.update({'hoodie_bus': 'rib'})

# ==================================================================================================== builders: inserts
def ring_fn(times, t0=0.0, dur=0.9):
    """A ring envelope f(time since the cut) -> 0..1 for a phone that rings at absolute times `times` (each ring a bell
    burst of `dur` s)."""
    ts = sorted(times)

    def f(u):
        t = u + t0
        for r in ts:
            if r - 0.05 <= t <= r + dur:
                x = (t - r) / dur
                return clamp(x / 0.08) * (1.0 - clamp((x - 0.7) / 0.3))
        return 0.0
    return f


def B_ins(F, sh):
    """A prop insert from sets_bus BU_INSERTS: name, kw = dict | f(time since the cut) -> dict, motion = f(time since
    the cut) -> (dx, dy, dscale, drot); hands=[dict(who, fn(t) -> (x, y, angle, alpha[, size]), size, shape, side,
    sleeve_from)]; layers=[f(F, sh) -> Layer]; c = camera (default a 3 %/s optical push)."""
    p = sh.p
    t0 = sh.t0
    kw = p.get('kw')
    if callable(kw):
        kwf = (lambda tt, f=kw: f(tt - t0))
    else:
        kwf = kw
    mo = p.get('motion')
    mof = (lambda tt, f=mo: f(tt - t0)) if mo else None
    sp = ST.om_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
    layers = list(sp)
    if p.get('strike'):
        layers.append(strike_layer(*p['strike']))
    for hd in p.get('hands', []):
        layers.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                 hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand'), held_pen=hd.get('pen', False)))
    for lf in p.get('layers', []):
        layers.append(lf(F, sh))
    c = dict(p.get('c') or dict(mv='push', rate=0.03))
    c.setdefault('free', True)
    cam = scam(sh, None, c)
    return Spec(layers, cam, sp.lens, p.get('grade', sp.grade), 1.0, 0.0, fx=_fx(sp, p), hud=p.get('hud'))


def notes_layer(src, t0, t1=None, rate=1.6, rise=-160.0, drift=90.0, size=34.0, depth=0.95, slow=1.0, c='#f4ead0', a=200, name='notes'):
    """Small music notes drifting out of a point (the hold music): src = (x, y) or f(t) -> (x, y). slow > 1 sinks them
    (the tune "falling asleep")."""
    def draw(pen, t):
        if t < t0 or (t1 is not None and t > t1 + 3.0): return
        x0, y0 = src(t) if callable(src) else src
        n = int((t - t0) * rate) + 1
        for k in range(max(0, n - 8), n):
            tb = t0 + k / rate
            u = (t - tb) / (3.2 * slow)
            if u < 0 or u > 1 or (t1 is not None and tb > t1): continue
            al = a * clamp(u / 0.15) * (1 - clamp((u - 0.6) / 0.4))
            x = x0 + drift * u * (1 if k % 2 else -0.6) + 18 * math.sin(u * 6 + k)
            y = y0 + rise * u * (1.0 / slow) + (40 * u * u * (slow - 1.0))
            s = size * (0.8 + 0.3 * hash01(k * 7))
            pen.fill(oval(x, y, s * 0.36, s * 0.27), c, al)
            pen.line(poly([(x + s * 0.32, y - s * 0.05), (x + s * 0.32, y - s * 1.15)], False), max(2.0, s * 0.08), c, al)
            if k % 3 == 0:
                pen.line(poly([(x + s * 0.32, y - s * 1.15), (x + s * 0.75, y - s * 0.9)], False), max(2.0, s * 0.08), c, al)
    return Layer(depth, draw, name, blur=0)


# ==================================================================================================== spaces + per-shot cues
SPACE = {'street': 'outside', 'living': 'inside', 'hall': 'inside', 'kitchen': 'inside', 'bath': 'inside', 'y58': 'memory', 'morning': 'outside',
         'town': 'outside'}


def shot_space(s):
    if s.kind in ('rule', 'black', 'card', 'outro', 'endB'): return None
    if s.kind == 'pause': return 'close'
    if s.kind == 'ins': return 'close'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return {'street': 'outside', 'morning': 'outside', 'y58': 'memory', 'town': 'outside'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('memory', 'outro', 'morning'): return s.p['era']
    if s.kind in ('rule', 'card', 'black', 'pause'): return s.kind
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if room in ('street', 'town'): return 'outside'
    if room == 'y58': return 'memory'
    if room == 'morning': return 'morning'
    return 'house'


def shot_common(F, sh, spec):
    """Collect the shot's SFX / music events from its acting, camera, tags, cut type and explicit cue lists."""
    p = sh.p
    space = shot_space(sh)
    for a in sh.actors:
        for e in a.events:
            if sh.t0 - 0.05 <= e['t'] <= sh.t1 + 0.4 and e['name']:
                pr = dict(e.get('params') or {})
                if e.get('who'): pr['who'] = e['who']
                if p.get('era') in ('memory', '1987'): pr['era'] = p['era']
                g = e.get('gain_db', 0.0)
                pass
                sh.sfx.append(_ev(e['t'], e['name'], g, e.get('pan', 0.0), space, **pr))
    for e in getattr(sh, 'xev', []):              # set-layer events (the letterbox fingers, the stub)
        if sh.t0 - 0.05 <= e['t'] <= sh.t1 + 0.4:
            pr = dict(e.get('params') or {}); pr['who'] = e.get('who', 'evie')
            sh.sfx.append(_ev(e['t'], e['name'], e.get('gain_db', 0.0), e.get('pan', 0.0), space, **pr))
    c = p.get('c') or {}
    if c.get('snap'):
        sh.sfx.append(_ev(c['snap'][0], 'whoosh', -4, 0, None, kind='hard'))
    for tg in p.get('tags', []):
        if p.get('tag_sound', True) and tg[4] != 'pill': sh.sfx.append(_ev(tg[0], 'ui_pop', -6, 0, 'close'))   # ring / call counters: the ring is the sound
    cut = p.get('cut')
    if cut in ('static', 'glitch'):
        sh.sfx.append(_ev(sh.t0, 'glitch', -4, 0, None, dur=0.25, amount=0.8))
    if cut == 'vhs':
        sh.sfx.append(_ev(sh.t0, 'vhs_glitch', -6, 0, 'vhs', dur=0.3))
    if cut == 'white' and not p.get('quiet_cut'):
        sh.sfx.append(_ev(sh.t0, 'impact_hit', -1, 0, None, size=1.1))
    for h in (p.get('hit') if isinstance(p.get('hit'), (list, tuple)) else ([p['hit']] if p.get('hit') else [])):
        sh.sfx.append(_ev(h, 'impact_hit', -2, 0, None, size=1.0))
        sh.music.append({'t': round(h, 3), 'type': 'hit', 'level': 0.75})
    for cc in p.get('sfx', []):                   # explicit (t, name, gain, pan, space, params)
        t, name = cc[0], cc[1]
        g = cc[2] if len(cc) > 2 else 0.0; pan = cc[3] if len(cc) > 3 else 0.0
        sp_ = cc[4] if len(cc) > 4 else space
        pr = cc[5] if len(cc) > 5 else {}
        sh.sfx.append(_ev(t, name, g, pan, sp_, **pr))
    for m in p.get('music', []):
        e = {'t': round(m[0], 3), 'type': m[1], 'level': m[2] if len(m) > 2 else 0.7}
        if len(m) > 3: e['len'] = m[3]
        if len(m) > 4: e.update(m[4])
        sh.music.append(e)
    if sh.kind == 'rule': rule_cues(F, sh)
    if sh.kind == 'card' and p.get('mode') == 'like':
        th_ = p.get('hit_t', sh.t0 + 0.4)
        for k_, tk_ in enumerate(p.get('knocks') or [th_ - 0.36, th_ - 0.18, th_]):     # knock-knock-KNOCK (fix round 1, fixer C)
            sh.sfx.append(_ev(tk_, 'knock_door', 2 if k_ == 2 else -2, 0, 'close', n=1, kind='like', index=k_))
    tags = p.get('tags')
    if tags:
        prev = spec.hud

        def hud(cv, t, prev=prev, tags=tags):
            if prev: prev(cv, t)
            for tg in tags:
                t0_, txt, x, y, style = tg[:5]
                hold_ = tg[5] if len(tg) > 5 else (1.2 if style == 'alert' else 2.6)
                if t0_ <= t <= t0_ + hold_: H.tag(cv, txt, x, y, style, t - t0_)
        spec.hud = hud

HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
WHOOSH_GAP = 40.0
def polish_cues(F, sfx, mus):
    """Cue-sheet pass after the shots (police / dummy film): hits land on the reveal cut, braams leave the reveal line
    clear, whooshes are rationed, silences sit before the big scares, swells breathe, duplicates are merged."""
    cuts = sorted(sh.t0 for sh in F.shots)
    lines = [(l['t'], l['end']) for l in F.L]

    def line_at(t):
        for a, b in lines:
            if a - 0.02 <= t <= b: return (a, b)
        return None

    def retime(t):
        prev = [c for c in cuts if 0.0 < t - c <= 0.25]
        if prev: return max(prev)
        ln = line_at(t); nxt = [c for c in cuts if 0.0 < c - t <= 0.35]
        if ln and nxt and ln[1] <= nxt[0] + 0.02: return min(nxt)
        return t

    for e in sfx:
        if e['name'] in HIT_SFX and not (e.get('params') or {}).get('fixed'): e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] in HIT_MUS and not e.get('fixed'): e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] != 'braam': continue
        ln = line_at(e['t'] + 0.02)
        if ln and ln[0] < e['t'] - 0.02:
            nxt = [c for c in cuts if ln[1] - 0.05 <= c <= ln[1] + 1.0]
            e['t'] = round(min(nxt) if nxt else ln[1] + 0.05, 3)
    wh = [e for e in sfx if e['name'] == 'whoosh' and (e.get('params') or {}).get('kind') != 'soft']
    keep = []
    for e in sorted(wh, key=lambda e: e['t']):
        if all(abs(e['t'] - k['t']) >= WHOOSH_GAP for k in keep): keep.append(e)
    kid = set(map(id, keep))
    sfx = [e for e in sfx if e['name'] != 'whoosh' or id(e) in kid or (e.get('params') or {}).get('kind') == 'soft']
    for i_, off_, ln in EXTRA_SIL:
        t = round(F.t(i_) + off_, 3)
        if not any(e['type'] == 'silence' and abs(e['t'] - t) < 2 for e in mus):
            mus.append({'t': t, 'type': 'silence', 'level': 0.0, 'len': ln})
    for e in mus:
        if e['type'] == 'swell' and float(e.get('len', 12)) < 12:
            pk = e['t'] + float(e.get('len', 6)); e['len'] = 12.0; e['t'] = round(max(0.5, pk - 12.0), 3)
    out = []
    kk = lambda e: (e['name'], str(e.get('space')), str((e.get('params') or {}).get('who')), str((e.get('params') or {}).get('index')))
    for e in sorted(sfx, key=lambda e: kk(e) + (e['t'],)):
        if out and kk(out[-1]) == kk(e) and e['t'] - out[-1]['t'] < 0.05:
            if e['gain_db'] > out[-1]['gain_db']: out[-1] = e
            continue
        out.append(e)
    mo = []
    for e in sorted(mus, key=lambda e: (e['type'], e['t'])):
        if mo and mo[-1]['type'] == e['type'] and e['type'] not in ('silence', 'jingle') and e['t'] - mo[-1]['t'] < 0.06:
            if e.get('level', 0) > mo[-1].get('level', 0): mo[-1] = e
            continue
        mo.append(e)
    return out, mo

def _wrap_txt(s, n):
    out, cur = [], ''
    for w_ in s.split():
        if len(cur) + len(w_) + 1 > n and cur: out.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    if cur: out.append(cur)
    return out


def shot_sheets(F, prefix, rng=None, per=8, tile=320):
    """The review sheet: one row per shot = first | middle | last frame (960x540 renders scaled to tile) and, under it,
    the shot's index / kind / times and the narration lines it covers (the words it must show)."""
    import cv2
    ks = list(range(len(F.shots))) if rng is None else list(range(rng[0], min(rng[1], len(F.shots))))
    th = tile * 9 // 16
    rows, mids = [], []
    for k in ks:
        sh = F.shots[k]
        ts = [sh.t0 + min(0.04, sh.d * 0.1), (sh.t0 + sh.t1) / 2, sh.t1 - min(0.05, sh.d * 0.1)]
        ims = []
        for tt in ts:
            try:
                img = F.frame(tt, int(round(tt * FPS)))
            except Exception as ex_:
                import traceback; print('FRAME ERROR t=%.2f shot %s: %r' % (tt, sh, ex_)); traceback.print_exc(limit=-4)
                img = np.zeros((CFG.rh, CFG.rw, 3), np.uint8); img[..., 0] = 140
            ims.append(cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (tile, th), interpolation=cv2.INTER_AREA))
        row = np.hstack(ims)
        ls = [l for l in F.L if l['end'] > sh.t0 + 0.05 and l['t'] < sh.t1 - 0.05]
        txt = ' / '.join('[%d%s] %s' % (l['i'], '' if l['who'] == 'narrator' else ' ' + l['who'], l['en']) for l in ls) or '(no line)'
        hdr = '#%d %s %s  %.2f-%.2f (%.2fs)' % (sh.idx, sh.kind, sh.p.get('room') or sh.p.get('name') or sh.p.get('who') or sh.p.get('mode') or '',
                                              sh.t0, sh.t1, sh.d)
        tl = [hdr] + _wrap_txt(txt, 118)[:3]
        band = np.full((16 * len(tl) + 6, row.shape[1], 3), 24, np.uint8)
        for j, s_ in enumerate(tl):
            cv2.putText(band, s_, (5, 14 + 16 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 230, 255) if j == 0 else (235, 235, 235), 1, cv2.LINE_AA)
        rows.append(np.vstack([row, band, np.full((4, row.shape[1], 3), 70, np.uint8)]))
        mid = ims[1].copy()
        cv2.putText(mid, '#%d L%s' % (sh.idx, ls[0]['i'] if ls else '-'), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1, cv2.LINE_AA)
        mids.append(mid)
        F._built.clear()
    paths = []
    for s0 in range(0, len(rows), per):
        p_ = '%s_%03d.jpg' % (prefix, ks[s0])
        cv2.imwrite(p_, np.vstack(rows[s0:s0 + per]), [cv2.IMWRITE_JPEG_QUALITY, 84]); paths.append(p_)
    for s0 in range(0, len(mids), 72):              # a compact review grid: the middle frame of every shot, 6 x 12
        tl_ = mids[s0:s0 + 72]
        while len(tl_) % 6: tl_.append(np.zeros_like(mids[0]))
        p_ = '%s_mid_%03d.jpg' % (prefix, ks[s0])
        cv2.imwrite(p_, np.vstack([np.hstack(tl_[i:i + 6]) for i in range(0, len(tl_), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 80]); paths.append(p_)
    return paths


def cut_frames(F, prefix, size=(480, 270), rng=None, cols=4):
    """Every cut as a pair: the last frame of shot k | the first frame of shot k+1, rendered over MAGENTA so a camera that
    sees past a set plate shows as magenta (holes are counted per frame -> prefix_holes.json)."""
    import cv2
    ks = range(len(F.shots) - 1) if rng is None else range(rng[0], min(rng[1], len(F.shots) - 1))
    pairs, holes = [], []
    for k in ks:
        a, b = F.shots[k], F.shots[k + 1]
        ims = []
        for tt, sh in ((b.t0 - 1.0 / FPS, a), (b.t0, b)):
            img = F.frame(tt, int(round(tt * FPS)), bg='#ff00ff')
            r_, g_, b_ = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
            mag = float(np.mean((r_ - g_ > 60) & (b_ - g_ > 60) & (np.abs(r_ - b_) < 70)))
            if mag > 0.0005 and sh.kind not in ('card',): holes.append(dict(shot=sh.idx, kind=sh.kind, t=round(tt, 3), hole=round(mag, 4)))
            im = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), size, interpolation=cv2.INTER_AREA)
            cv2.putText(im, '%d %s %.2f' % (sh.idx, sh.kind, tt), (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 255, 255), 1, cv2.LINE_AA)
            ims.append(im)
        pairs.append(np.hstack([ims[0], np.full((size[1], 4, 3), 255, np.uint8), ims[1]]))
        F._built.clear()
    paths = []
    per = cols * 6
    for s0 in range(0, len(pairs), per):
        tl = pairs[s0:s0 + per]
        while len(tl) % cols: tl.append(np.zeros_like(pairs[0]))
        rows = [np.hstack([np.pad(x, ((4, 4), (6, 6), (0, 0))) for x in tl[i:i + cols]]) for i in range(0, len(tl), cols)]
        p_ = '%s_%02d.jpg' % (prefix, s0 // per)
        cv2.imwrite(p_, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80]); paths.append(p_)
    json.dump(holes, open(prefix + '_holes.json', 'w'), indent=1)
    return paths, holes


def lip_check(F, fps=30.0):
    """Mouths move only on their own lines: for every shot and actor, the mean |change| per second of m_open (people) inside
    and outside the actor's own lines (lines overlapping the shot by > 0.15 s). The Bunnyman's mask has no mouth; Dale's
    face (unmask) moves on D. Humming is a closed mouth (no motion)."""
    rows = []
    for sh in F.shots:
        F._build(sh)
        for a in sh.actors:
            who = a.who
            v = VOICE.get(who, [])
            lines = [(l['t'], l['end']) for l in F.voice_lines(sh.t0, sh.t1, v)] if v else []
            lines = [(l0, l1) for l0, l1 in lines if min(l1, sh.t1) - max(l0, sh.t0) > 0.15]
            ts = np.arange(sh.t0 + 0.02, sh.t1 - 0.02, 1.0 / fps)
            if len(ts) < 3: continue
            vals = np.array([a.at(float(tt)).m_open for tt in ts])
            d = np.abs(np.diff(vals)) * fps
            mid = ts[1:]
            ins = np.array([any(l0 - 0.1 <= tt <= l1 + 0.15 for l0, l1 in lines) for tt in mid])
            on = float(d[ins].mean()) if ins.any() else 0.0
            off = float(d[~ins].mean()) if (~ins).any() else 0.0
            rows.append(dict(shot=sh.idx, t0=round(sh.t0, 2), kind=sh.kind, who=who, lines=len(lines), move_on=round(on, 3), move_off=round(off, 3),
                             peak_off=round(float(d[~ins].max()) if (~ins).any() else 0.0, 2)))
        F._built.clear()
    return rows



# ==================================================================================================== PLAN helpers

# ==================================================================================================== this film's rooms and light
NIGHT = dict(rim='#8fa6e8', rim_a=80, side=1, key=-0.22)                   # blue-black night, moon / streetlight rim
NIGHT_L = dict(rim='#8fa6e8', rim_a=80, side=-1, key=-0.22)
PORCH = dict(rim='#ffc884', rim_a=120, side=-1, key=-0.15)                 # our porch light
DAY = dict(rim='#fff0c8', rim_a=60, side=1, key=0.12)
DAY_L = dict(rim='#fff0c8', rim_a=60, side=-1, key=0.12)
WARM = dict(rim='#ffd89a', rim_a=90, side=1, key=0.15)                     # the tape's summer
SUNSET = dict(rim='#ff8a6a', rim_a=140, side=1, key=0.0)                   # the ONE red sunset
FLOOD = dict(rim='#f4f0d8', rim_a=150, side=1, key=0.05)                   # the caretaker's floodlight
BULB = dict(rim='#fff1c8', rim_a=120, side=1, key=-0.08)                   # the bare landing bulb
KITCH = dict(rim='#ffe2b0', rim_a=70, side=1, key=0.02)                    # the kitchen light
LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.06)
PHONE = dict(under='#cfe0ff', under_a=150, key=-0.3)                       # a phone screen in the dark, from below
DAWN = dict(rim='#ffd8b8', rim_a=70, side=1, key=0.02)

ROOMS = {'front': 'om_front', 'room': 'om_room', 'hall': 'om_hall', 'kitchen': 'om_kitchen', 'school': 'om_school', 'play': 'om_playground'}
_PRE = {'front': 'om_front_', 'room': 'om_room_', 'hall': 'om_hall_', 'kitchen': 'om_kit_', 'school': 'om_sc_', 'play': 'om_play_'}
ROOM_RIM = {'front': NIGHT, 'room': NIGHT, 'hall': NIGHT, 'kitchen': KITCH, 'school': DAY, 'play': DAY}
ALIAS = {'adam': ADAMS}
SPACE = {'front': 'outside', 'room': 'inside', 'hall': 'inside', 'kitchen': 'inside', 'school': 'inside', 'play': 'outside'}
DAYK = ('day', 'morning', 'evening', 'dawn', 'sunset', 'warm', 'summer')
NIGHT_ROOMS = ('front', 'room', 'hall')


def shot_space(s):
    if s.kind in ('rule', 'black', 'card', 'list', 'prompt'): return None
    if s.kind == 'tape': return 'tape'
    if s.kind == 'ins': return 'close'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return 'close'
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.kind == 'tape': return 'tape'
    if s.p.get('era') in ('memory', 'outro', 'trailer', 'coda'): return s.p['era']
    if s.kind in ('rule', 'card', 'black', 'prompt', 'list'): return s.kind
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    return {'front': 'outside', 'school': 'school', 'play': 'playground'}.get(room, 'home')


def is_night(sh):
    """Night shots: Evie goes chalk-flat (a.night()); dark interiors get the night lift."""
    p = sh.p
    if p.get('night') is not None: return p['night']
    st = p.get('set') or {}
    room = p.get('room') or (p.get('bg') or [None])[0]
    tod = st.get('tod')
    if tod is not None: return tod in ('night',)
    return room in NIGHT_ROOMS


def _ramp(t, t0, t1):
    return ease_in_out(clamp((t - t0) / max(1e-3, t1 - t0)))


def escalate(a, sh, who):
    """The STATE of every actor (keyed to lines; tools/validate.py STATE reads the same fields): Adam's hoodie sleeves
    (ob_chalk: chalk-white only on the Monday hoodie and at Danny's blue door), Mom's red knuckles (ob_knuck on the
    scrubbing mornings and at midnight), Evie's stage (EVIE_ARC, or the shot's stage=) and her night flatness, the kids'
    tension (wider eyes, quicker breath) as the week closes in."""
    if sh.kind in ('rule', 'card', 'black', 'prompt', 'list'): return
    p = sh.p
    if who in ADAMS or who == 'adam':
        a.set(-1e9, None, 0.0, ob_chalk=float(p.get('chalk', 0.0)))
    if who == 'mom' and p.get('knuck'):
        a.set(-1e9, None, 0.0, ob_knuck=1.0)
    if who == 'evie':
        if p.get('stage'): a.stage(-1e9, p['stage'])
        if is_night(sh): a.night(amount=p.get('night_k', 1.0))
    if who in ADAMS and p.get('era') not in ('memory', 'coda', 'tape'):
        k = _arc(KID_ARC, sh.t0)
        if k > 0.02:
            def fn(P_, t, k=k):
                P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
                per = 3.9 - 1.5 * k
                P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
            a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)


KID_ARC = [(0, 0.5), (13, 0.1), (47, 0.3), (56, 0.6), (74, 0.3), (89, 0.6), (104, 0.6), (119, 0.9), (127, 0.4), (154, 0.7),
           (171, 1.0), (181, 0.7), (187, 0.5), (201, 0.8), (213, 1.0), (245, 0.8), (251, 0.5), (285, 0.6), (290, 0.4), (302, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    pts = [(F.t(i), v) for i, v in arc if i < len(F.L)]
    return float(np.interp(t, [p_[0] for p_ in pts], [p_[1] for p_ in pts]))


def scr(sp, at, dx=0.0, dy=0.0):
    """Screen (design) point of a plan point / anchor in set sp (for look_at / reach_to targets)."""
    s = spot_of(sp, at)
    return (s.x + dx, s.y + dy)


def cm(eye, look, S=1000.0, sx=960.0, sy=540.0, env=None):
    """A custom camera on the house plan: eye (x, y, Y), look (x, y, Y) -> screen (sx, sy), focal S."""
    d = dict(eye=eye, look=look, S=S, sx=sx, sy=sy)
    if env: d['env'] = env
    return d


def _A(*fns):
    """Several acts on one actor; an act that reaches an actor placed later in the shot runs after all are placed."""
    def run(a, s):
        for f in fns:
            if not f: continue
            try: f(a, s)
            except KeyError:
                if getattr(s, '_defer', None) is None: raise
                s._defer.append((f, a))
    return run


def ex(name, t0, t1=None, fade=0.35): return lambda a, s: a.expr(name, t0, t1, fade)


def pose(t0, t1=None, fade=0.3, **kw): return lambda a, s: a.set(t0, t1, fade, **kw)


def hum(t0, t1=None, amount=1.0): return lambda a, s: a.hum(t0, t1, amount)


def lookp(at, t0, t1=None, dur=0.4, z=None, body=0.0):
    """look at a plan point / anchor of the shot's set"""
    return lambda a, s: a.look_at(t0, scr(s.sp, at), t1, dur, z=z, body=body)


def lookxy(x, y, t0, t1=None, dur=0.4, z=None):
    return lambda a, s: a.look_at(t0, (x, y), t1, dur, z=z)


def blinks(*ts): return lambda a, s: [a.blink(t) for t in ts]


def tilt(t0, ang=10.0, dur=1.6): return lambda a, s: a.head_tilt(t0, ang, dur)

# ==================================================================================================== PLAN helpers (this film)
def T(i, off=0.0):
    """Cut time for line i: a moment before its first word."""
    return _FILM[0].t(i) - LEAD + off


def W(i, word, k=0, off=0.0):
    """Cut time for the k-th `word` inside line i: a moment before it."""
    return _FILM[0].w(i, word, k) - LEAD + off


def WD(i, word, k=0, off=0.0):
    """The word's own start (for events that land ON the word)."""
    return _FILM[0].w(i, word, k) + off


def E(i, off=0.0): return _FILM[0].e(i) + off

def tagc(t, s, style='red', x=960, y=170, hold=2.2): return (t, s, x, y, style, hold)


def slide(t0, t1, p0, p1, ang0, ang1=None, a=1.0, ease=ease_out_cubic, extra=None):
    """A hand path for hand_layer: wrist from p0 to p1 between t0 and t1 (eased), angle ang0 -> ang1."""
    ang1 = ang0 if ang1 is None else ang1

    def fn(t):
        u = ease(clamp((t - t0) / max(1e-3, t1 - t0)))
        r = (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u), lerp(ang0, ang1, u), a)
        return extra(t, r) if extra else r
    return fn


def S(t, room, view, ppl=(), st=None, **p):
    """A set shot: room / view, figures ppl, set kwargs st."""
    _FILM[0].cut(t, 'set', room=room, view=view, set=dict(st or {}), ppl=list(ppl), **p)


def BU(t, who, room, view, st=None, **p):
    """A face close-up over the blurred set (room, view, st); room None = a plain gradient (p['plain'])."""
    if room is None: _FILM[0].cut(t, 'bust', who=who, **p)
    else: _FILM[0].cut(t, 'bust', who=who, bg=(room, view), set=dict(st or {}), **p)


def IN(t, name, kw=None, **p):
    _FILM[0].cut(t, 'ins', name=name, kw=kw, **p)


def RULE(t, n, **p): _FILM[0].cut(t, 'rule', n=n, **p)


def Z(f=1.0, rate=0.02, x=960, y=540, **k): return dict(mv='push', f=f, rate=rate, x=x, y=y, **k)


def BZ(z=0.02, **k): return dict(mv='push', rate=0.0, zrate=z, **k)


def lk(t0, target, t1=None, dur=0.35, body=0.0, snap=False):
    """look at: target = an anchor / plan point of the shot's set, (x, y) design point, or (actor_id, part)."""
    def f(a, s):
        tg = target
        if isinstance(tg, tuple) and len(tg) == 2 and isinstance(tg[0], str):
            tg = (s.A[tg[0]], tg[1])                   # KeyError -> deferred until that actor is placed
        elif isinstance(tg, str) or (isinstance(tg, tuple) and len(tg) == 3):
            tg = scr(s.sp, tg)
        a.look_at(t0, tg, t1, dur, body=body, snap=snap)
    return f


def reach(t0, side, target, t1=None, dur=0.5, shape='grip', contact='palm', z=30.0, prop=None):
    def f(a, s):
        tg = target
        if isinstance(tg, str) or (isinstance(tg, tuple) and len(tg) == 3 and not isinstance(tg[0], str)):
            tg = scr(s.sp, tg)
        elif isinstance(tg, tuple) and len(tg) == 2 and isinstance(tg[0], str):
            tg = (s.A[tg[0]], tg[1])
        a.reach_to(t0, side, tg, t1=t1, dur=dur, shape=shape, contact=contact, z=z, prop=prop)
    return f


def wavef(t0, t1, side=1, slow=True): return lambda a, s: a.wave(t0, t1 if t1 is not None else s.t1 + 1.0, side, slow=slow)


def radio(t0, t1, side=1, drop=0.0, rise=0.4): return lambda a, s: a.radio_to_mouth(t0, t1, side, drop=drop, rise=rise)


def quiet(f):
    """An act whose sound events are dropped (the same action continues into the next shot, which owns the sounds)."""
    def run(a, s):
        n = len(a.events); f(a, s); del a.events[n:]
    return run


def sleepyf(t0, t1=None): return lambda a, s: a.sleepy(t0, t1)


def tremblef(t0, t1=None, amp=1.0): return lambda a, s: a.tremble(t0, t1, amp)


def shake_head(t0, n=3, amp=9.0, dur=0.9):
    """A little 'no' (Lina and the mittens): the head swings side to side."""
    def f(a, s):
        def fn(P_, t):
            u = (t - t0) / dur
            if 0 <= u <= 1: P_.h_turn += 0.28 * math.sin(u * n * 2 * math.pi) * math.sin(u * math.pi)
        a._add(t0 - 0.1, t0 + dur + 0.1, fn)
    return f




# ==================================================================================================== this film: rooms, light, states
def _c_on(sh, sp, c, A):
    """A camera dict whose centre is an anchor / plan point (on='table_mom') or an actor (on='@owen', part='head') at the
    shot's start: the screen point of a layer at that depth (scam's screen / d)."""
    if not c or c.get('on') is None: return c
    c = dict(c); on = c.pop('on')
    if sp is None and not (isinstance(on, str) and on.startswith('@')): return c
    if isinstance(on, str) and on.startswith('@'):
        a_ = A[on[1:]]; x_, y_ = a_.where(sh.t0 + 0.05, c.pop('part', 'head'))
        d_ = c.pop('depth', None) or (getattr(sh, 'I', {}).get(on[1:], {}).get('depth') or 1.0)
    else:
        s_ = spot_of(sp, on)
        if c.get('h'): s_ = sp.spot(s_.X, s_.Yp, s_.Y + c.pop('h'))
        x_, y_, d_ = s_.x, s_.y, s_.depth
    c.setdefault('x', x_ + c.pop('odx', 0.0)); c.setdefault('y', y_ + c.pop('ody', 0.0))
    c['screen'] = True; c['d'] = max(0.3, d_)
    return c


def _w(self, i, word, k=0, off=0.0):
    """Start time of the k-th occurrence of `word` (as SPOKEN: the line's 'say' text) inside line i, from the line's own
    word times; proportional fallback."""
    l = self.L[i]; word = word.lower().strip('.,?!;:"')
    n = 0
    for ww, tt in (l.get('words') or []):
        w_ = ww.lower().strip('.,?!;:"“”…')
        if w_ == word or w_.startswith(word):
            if n == k: return tt + off
            n += 1
    txt = (l.get('say') or l['en']).lower(); p_ = txt.find(word)
    return l['t'] + (l['end'] - l['t']) * (p_ / max(1, len(txt)) if p_ >= 0 else 0.5) + off




HEADS = [(83, 'ONE WORD'), (86, None), (302, 'AFTER'), (331, 'NOW'), (341, 'THE TRUTH'), (348, 'THE WARNING SIGNS'), (369, 'YOUR WORD'),
         (376, CHANNEL)]


def _header_text(self, t):
    cur = 'INTRODUCTION'
    for t0, n in self.rules:
        if t >= t0: cur = 'RULE %d OF 7' % n
    for i, s in HEADS:
        if i < len(self.L) and t >= self.t(i) - LEAD:
            if s: cur = s
            else:
                cur = 'INTRODUCTION'
                for t0, n in self.rules:
                    if t >= t0: cur = 'RULE %d OF 7' % n
    return cur


def _clean(s):
    """Caption text comes out clean: no markup characters ever reach the screen."""
    import re
    return re.sub(r'[\*_\[\]\{\}<>#`~|]', '', s).replace('  ', ' ').strip()


def _overlay(self, cv, t, sh):
    if sh.kind == 'black' and not sh.p.get('caption'): return
    if sh.kind != 'black' and t >= self.t(7) - LEAD and sh.p.get('era') != 'trailer': header(cv, self.header_text(t), clock_str(t))
    if sh.kind in ('rule', 'list', 'prompt') or sh.p.get('no_caption'): return
    l = self.line_at(t)
    if not l or not l.get('found_en', True): return
    k, ch = self.chunk_at(l, t)
    txt = _clean(ch[k])
    if l['who'] != 'narrator':
        if k == 0: txt = txt.lstrip('"“” ')
        if k == len(ch) - 1: txt = txt.rstrip('"“” ')
        if k == 0: txt = '“' + txt
        if k == len(ch) - 1: txt = txt + '”'
    H.caption(cv, txt)


Film.w = _w
Film.header_text = _header_text
Film.overlay = _overlay



def lay_at(sh, who, dorder, draw, name):
    """A layer drawn at actor `who`'s depth, just in front of (dorder < 0) or behind (> 0) that figure's own layer."""
    L = sh.I[who]['layer']
    o = L.order
    lay = Layer(L.depth, draw, name, ref_depth=L.ref_depth if hasattr(L, 'ref_depth') else L.depth)
    lay.order = (lambda t, o=o: _val(o, t) + dorder) if callable(o) else o + dorder
    return lay


def _val(o, t): return o(t) if callable(o) else o


# ==================================================================================================== builders: the tape
def tape_kids(F, sh, kids=(('adam7', 'r'), ('danny7', 'l'))):
    """Little Adam and Danny on the swings in tape space (om_tape anchors): seated on the swing seats, riding them
    (swing_ride: the chains in their hands, a creak at each end), little Adam singing his song on his own sung line."""
    sp0 = ST.om_tape()
    rows = []
    for k, (who, side) in enumerate(kids):
        s = sp0.anchors['swing_' + side]; pv = sp0.anchors['swing_%s_pivot' % side]
        seat_y = s.seat_y if getattr(s, 'seat_y', None) is not None else s.y - 0.45 * s.ppm
        L = seat_y - pv.y
        h = CH.height_px(who, s.ppm)
        a = CH.Acting(who, seed=5 + k * 7, height=h, expr='kind_smile')
        a.place(pv.x, s.y)
        a.face(0.62)
        a.seated(seat_y, hands='lap')
        a.swing_ride(sh.t0 - 3.0 - 0.7 * k, sh.t1 + 2.0, (pv.x, pv.y), L, amp=15 + 3 * k, period=2.5 + 0.35 * k, ramp=0.01)
        if who == 'adam7':
            for l in F.voice_lines(sh.t0, sh.t1, VOICE['adam7']):
                a.talk([(l['t'], l['end'], l['en'])], intensity=1.0)
                a.sing_sway(l['t'], l['end'], amount=0.7)
        elif who == 'danny7':
            a.look_at(sh.t0, (pv.x + 900, pv.y + 380), None, 0.3)
        sh.actors.append(a)
        rows.append((a, who, (pv.x, pv.y), L, s.ppm / 100.0))

    def figures(pen, t):
        for a, who, pv, L, ppc in rows:
            ang, seat = a.swing_state(t)
            CH.draw_swing(pen, pv, L, ang, ppc, part='back')
            CH.draw(pen, who, a.x0, a.y0, a.height, a.at(t), light=WARM, t=t)
            CH.draw_swing(pen, pv, L, ang, ppc, part='front')
    return figures


def B_tape(F, sh):
    """Mom's camcorder tape, full frame: om_tape (warp 0..1 or f(t): the rule 4 return; rewind f(t): the rule 7 replay)
    with the stamp (PLAY / REW, the counter, the date) in the HUD; little Adam and Danny on the swings (kids=False: the
    empty swings); glitch=[t]: a tracking tear at those times."""
    p = sh.p
    t0 = sh.t0
    figs = tape_kids(F, sh) if p.get('kids', True) else None
    sp = ST.om_tape(figs, p.get('warp', 0.0), p.get('rewind'))
    sh.sp = sp
    mode = p.get('mode', 'play')
    off = p.get('off', 0.0)
    wp = p.get('warp', 0.0)

    def hud(cv, t):
        ST.om_tape_stamp(cv, t - t0 + off, mode=mode(t) if callable(mode) else mode, warp=lvl(wp, t))
    gl = list(p.get('glitch', []))

    def fx(t):
        d = dict(sp.fx(t) or {})
        for g in gl:
            if 0 <= t - g < 0.22: d['glitch'] = max(d.get('glitch', 0.0), 0.9 * (1 - (t - g) / 0.22))
        return d
    c = dict(p.get('c') or dict(mv='push', rate=0.012, f=1.04)); c.setdefault('free', True)
    cam = scam(sh, None, c)
    return Spec(list(sp), cam, None, sp.grade, 1.0, 0.0, fx=fx, hud=hud)


# ==================================================================================================== builders: Danny's card
RULE_LINES = {1: (53, 55), 2: (87, 88), 3: (109, 110), 4: (138, 139), 5: (185, 186), 6: (211, 212), 7: (240, 244)}


def rule_write(F, n, lead=0.2):
    """k(t) 0..1 for rule n: the share of its words already read (+ a lead), from the lines' own word times."""
    i0, i1 = RULE_LINES[n]
    total = len(ST.OM_RULES[n - 1][1].split())
    ts = []
    for i in range(i0, i1 + 1):
        l = F.L[i]; nw = len(l['en'].split()); ww = l.get('words') or []
        if len(ww) == nw: ts += [w_[1] for w_ in ww]
        else: ts += [l['t'] + (l['end'] - l['t']) * j / max(1, nw) for j in range(nw)]
    ts = ts[:total] + [ts[-1]] * max(0, total - len(ts))
    return lambda t: sum(1 for x in ts if x <= t + lead) / float(total)


def B_rule(F, sh):
    """Danny's card full screen (his mom's purple handwriting, ADAM scribbled out in blue pen at the top): rules 1..n-1
    already there, rule n written word by word as it is read, glowing while it is read."""
    p = sh.p
    n = p['n']
    t0 = sh.t0
    wf = rule_write(F, n)
    mo = lambda t: (5.0 * math.sin((t - t0) * 0.6), 3.0 * math.sin((t - t0) * 0.45), 0.012 * clamp((t - t0) / 6.0), 0.0)
    sp = ST.om_insert('card', lambda t: dict(show=n - 1, words=(n, wf(t)), hl=n, bg=p.get('bg', 'desk')), mo, t0=0.0)
    cam = scam(sh, None, dict(mv='push', rate=p.get('rate', 0.006), free=True, f=p.get('f', 1.0), x=p.get('x', 960), y=p.get('y', 540)))
    return Spec(list(sp), cam, None, sp.grade, 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def rule_cues(F, sh):
    n = sh.p['n']; i0, i1 = RULE_LINES[n]
    sh.sfx.append(_ev(sh.t0 + 0.02, 'card_slide', -16, 0, 'close'))
    sh.sfx.append(_ev(F.t(i0), 'pen_scratch', -20, 0, 'close', dur=round(F.e(i1) - F.t(i0), 2)))
    sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.6, 'n': n})


# ==================================================================================================== builders: prompt, list, cards
def _words_in(F, i):
    l = F.L[i]; ws = l['en'].split(); ww = l.get('words') or []
    if len(ww) == len(ws): return [(w_, t_) for w_, (_, t_) in zip(ws, ww)]
    return [(w_, l['t'] + (l['end'] - l['t']) * j / max(1, len(ws))) for j, w_ in enumerate(ws)]


def _chalk_word(cv, s, x, y, size, a=255, c='#f2efe6', font='kid'):
    pen = Pen(cv)
    ST.btext(pen, s, x + 3, y + 4, font, size, '#000000', 0.45 * a, 'center')
    ST.btext(pen, s, x, y, font, size, c, a, 'center')


PROMPT_ASK = (83, 85)        # Forty-seven messages... / Before rule two... / would you feel Special, or Trapped?
PROMPT_BACK = (369, 375)     # Now. Special, or Trapped? ... the word that fixes both: Space.


def B_prompt(F, sh):
    """The comment prompt over Adam's phone thread (blurred): 47 in big chalk, then SPECIAL and TRAPPED each on its word;
    stage 'return': the same two words, the truth under them, and SPACE written on its word. Every word legible."""
    p = sh.p
    st = p.get('stage', 'ask')
    sp = ST.om_insert('phone', dict(screen='thread', count=47, typing=0.0, bg='dark'))
    layers = list(sp)
    i0, i1 = PROMPT_ASK if st == 'ask' else PROMPT_BACK
    li = i1 if st == 'ask' else 370
    tS = F.w(li, 'special'); tT = F.w(li, 'trapped')
    tSp = F.w(375, 'space') if st != 'ask' else None

    def hud(cv, t):
        pen = Pen(cv)
        pen.fill(rect(0, 0, DW, 1080), '#07080d', 175)
        a0 = clamp((t - sh.t0) / 0.3)
        if st == 'ask':
            text(cv, 'ONE WORD IN THE COMMENTS', 960, 150, 800, 34, '#c8ccd8', 220 * a0, 0.3, 'center', 0.5)
            _chalk_word(cv, '47', 960, 380, 190, 255 * a0)
            text(cv, 'MESSAGES IN ONE NIGHT', 960, 470, 700, 30, '#f2efe6', 200 * a0, 0.25, 'center', 0.5)
        else:
            text(cv, 'YOUR WORD', 960, 150, 800, 34, '#c8ccd8', 220 * a0, 0.3, 'center', 0.5)
            if t >= F.t(371) - 0.1:
                text(cv, 'Those 47 messages were mine first. To Danny.', 960, 300, 700, 40, '#ffffff', 235 * clamp((t - F.t(371) + 0.1) / 0.3), 0.0, 'center', 0.6)
        for (w_, tw, x, sub, ts_) in (('SPECIAL', tS, 600, 'what I thought I gave him', F.t(373) if st != 'ask' else 1e9),
                                      ('TRAPPED', tT, 1320, 'what he felt', F.t(374) if st != 'ask' else 1e9)):
            if t < tw - 0.15: continue
            k = ease_out_back(clamp((t - tw + 0.15) / 0.35))
            box = rrect(x - 250 * k, 560, 500 * k, 150, 22)
            pen.fill(box, '#ffffff', 22 * clamp(k)); pen.line(box, 3, '#f2efe6', 150 * clamp(k))
            _chalk_word(cv, w_, x, 668, 96 * max(0.05, k), 255 * clamp(k))
            text(cv, 'or', 960, 668, 600, 40, '#c8ccd8', 200 * clamp((t - tT + 0.15) / 0.3) if w_ == 'TRAPPED' else 0, 0.1, 'center', 0.4)
            if t >= ts_ - 0.1:
                text(cv, sub, x, 770, 600, 32, '#f2efe6', 230 * clamp((t - ts_ + 0.1) / 0.3), 0.0, 'center', 0.5)
        if tSp is not None and t >= tSp - 0.15:
            k = ease_out_back(clamp((t - tSp + 0.15) / 0.4))
            _chalk_word(cv, 'SPACE', 960, 930, 120 * max(0.05, k), 255 * clamp(k), c='#bfe6ff')
            pen.line(poly([(780, 960), (1140, 960)], False), 6, '#bfe6ff', 200 * clamp((t - tSp) / 0.4))
    cam = scam(sh, None, dict(mv='push', rate=0.004, free=True))
    return Spec(layers, cam, None, sp.grade, 1.0, 0.0, fx=lambda t: dict(blur=10), hud=hud)


LIST_ITEMS = [(348, 350, 'Too much, too fast'), (351, 353, 'Wanting you all to themselves'), (354, 355, 'Your passwords are yours'),
              (356, 358, '"It\'s your fault" is never true'), (359, 362, "Don't keep it secret"), (363, 366, "Can't stop checking on someone?")]


def _wrap_txt(s, n):
    out, cur = [], ''
    for w_ in s.split():
        if len(cur) + len(w_) + 1 > n and cur: out.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    if cur: out.append(cur)
    return out


def B_list(F, sh):
    """The outro checklist (the story bible's six items) over the clean path at dawn: each item appears as it is read
    (bold head + its spoken words), the one being read bright, a chalk tick when read. All of it stays legible."""
    sp = ST.om_front('wide', tod='dawn', bucket=True)
    layers = list(sp)

    def hud(cv, t):
        pen = Pen(cv)
        pen.fill(rect(0, 0, DW, 1080), '#0b0c12', 190)
        text(cv, 'THE REAL WARNING SIGNS', 960, 118, 900, 46, '#ffd890', 245 * clamp((t - sh.t0) / 0.3), 0.18, 'center', 0.5)
        y = 196
        for k, (i0, i1, head) in enumerate(LIST_ITEMS):
            ta, tb = F.t(i0) - 0.15, F.e(i1)
            body = ' '.join(F.L[i]['en'] for i in range(i0, i1 + 1))
            if body.startswith(head): body = body[len(head):].lstrip(' .?')
            lines = _wrap_txt(_clean(body), 62)
            hh = 44 * (len(lines) + 1) + 16
            if t >= ta:
                a = clamp((t - ta) / 0.25)
                cur = ta <= t < (F.t(LIST_ITEMS[k + 1][0]) - 0.15 if k + 1 < len(LIST_ITEMS) else 1e9)
                if cur: pen.fill(rrect(230, y - 36, 1460, hh, 14), '#ffffff', 26 * a)
                box = rrect(250, y - 26, 34, 34, 6)
                pen.line(box, 3, '#ffd890', 230 * a)
                if t >= tb: pen.line(poly([(257, y - 9), (267, y + 2), (281, y - 20)], False), 5, '#f2efe6', 255 * clamp((t - tb) / 0.2))
                text(cv, _clean(head), 310, y, 800, 40, '#ffd890' if cur else '#e8dcc0', (255 if cur else 200) * a, 0.0, 'left', 0.5)
                for j, ln in enumerate(lines):
                    text(cv, ln, 310, y + (j + 1) * 44, 700 if cur else 600, 36, '#ffffff' if cur else '#c8ccd8', (255 if cur else 190) * a, 0.0, 'left', 0.5)
            y += hh
    cam = scam(sh, sp.info.get('cam_env'), dict(mv='push', rate=0.004, free=True))
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=lambda t: dict(blur=9), hud=hud)


def _thumb(pen, x, y, s, a=255):
    pen.fill(rrect(x - 70 * s, y - 10 * s, 40 * s, 110 * s, 8 * s), '#ffffff', a)
    pen.fill(rrect(x - 26 * s, y - 20 * s, 100 * s, 120 * s, 22 * s), '#ffffff', a)
    pen.fill(rrect(x - 10 * s, y - 80 * s, 44 * s, 80 * s, 20 * s), '#ffffff', a)


def B_card(F, sh):
    """Plain cards: p text (lines split by \\n), line_t {k: t} (a line appears on its word), sub, icon 'thumb' | 'sub'
    (pops at icon_t), chalk=True (the text in the chalk hand), bg (c1, c2) or bgset=(room, view, kw) blurred."""
    p = sh.p
    if p.get('bgset'):
        r_, v_, kw_ = p['bgset']
        sp = make_set(r_, v_, None, **kw_); layers = list(sp); grade = sp.grade
    else:
        c1, c2 = p.get('bg', ('#141824', '#07080c'))
        layers = [Layer(4.0, lambda pen, t: pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, [c1, c2]), 'card_bg', blur=0)]
        grade = 'neutral'

    def hud(cv, t):
        pen = Pen(cv)
        if p.get('bgset'): pen.fill(rect(0, 0, DW, 1080), '#06070c', 150)
        a = clamp((t - sh.t0) / 0.4)
        lines = (p.get('text') or '').split('\n')
        y0 = p.get('y', 500) - (len(lines) - 1) * 45
        for k, s in enumerate(lines):
            ta = (p.get('line_t') or {}).get(k, sh.t0)
            if t < ta: continue
            ak = clamp((t - ta) / 0.3) * a
            if p.get('chalk'): _chalk_word(cv, s, 960, y0 + k * 96, p.get('size', 72), 245 * ak)
            else: text(cv, s, 960, y0 + k * 90, 900, p.get('size', 64), '#ffffff', 240 * ak, 0.12, 'center', 0.8)
        if p.get('sub'): text(cv, p['sub'], 960, y0 + len(lines) * 90 + 10, 700, 36, '#c8ccd8', 210 * a, 0.2, 'center', 0.5)
        ic = p.get('icon')
        if ic and t >= p.get('icon_t', sh.t0):
            k_ = ease_out_back(clamp((t - p.get('icon_t', sh.t0)) / 0.35))
            if ic == 'thumb': _thumb(pen, 960, 300, 1.3 * max(0.01, k_), 255 * clamp(k_))
            if ic == 'sub':
                pen.fill(rrect(960 - 230 * k_, 250, 460 * k_, 110, 18), '#d8262e', 255 * clamp(k_))
                text(cv, 'SUBSCRIBE', 960, 322, 900, 50 * max(0.01, k_), '#ffffff', 255 * clamp(k_), 0.12, 'center', 0.0)
    cam = scam(sh, None, dict(mv='push', rate=0.008, free=True))
    return Spec(layers, cam, None, grade, 1.0, 0.0, fx=lambda t: dict(p.get('post', {}), **({'blur': 7} if p.get('bgset') else {})), hud=hud)


def B_black(F, sh):
    lay = Layer(4.0, lambda pen, t: pen.fill(rect(-1200, -900, 4320, 2880), '#000000'), 'black', blur=0)
    return Spec([lay], None, None, None, 1.0, 0.0)


# ==================================================================================================== the global look
EXPO = {'ins': -0.02}
NIGHT_LIFT = 0.10                    # night interiors: dark, but the action must read (bus-film lesson)


def glob_fx(F, sh, t, fx):
    """Per-frame global effects keyed to lines: cut flashes (white, blink, glitch, whip), the night lift, grain that
    rises through the week, the trailer's harder grade, fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'blink' and u < 0.12: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - u / 0.12)
    elif c == 'glitch' and u < 0.2: fx['glitch'] = max(fx.get('glitch', 0.0), 0.8 * (1 - u / 0.2))
    elif c == 'whip' and u < 0.24: fx['blur'] = max(fx.get('blur', 0.0), 22.0 * (1 - u / 0.24))
    ek = EXPO.get(sh.kind, 0.0)
    if sh.kind in ('set', 'bust') and is_night(sh): ek += NIGHT_LIFT
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('outro',) or sh.kind in ('rule', 'black', 'card', 'prompt', 'list', 'tape')
    if era == 'trailer' and sh.kind != 'tape':
        fx['sat'] = fx.get('sat', 1.0) * 0.85; fx['grain'] = max(fx.get('grain', 0.0), 0.09)
    if era == 'coda':
        fx['sat'] = fx.get('sat', 1.0) * 0.9
    if not clean:
        g = 0.035 + 0.05 * clamp((t - F.t(39)) / max(1.0, F.t(213) - F.t(39)))
        if t >= F.t(302): g = 0.035
        fx['grain'] = max(fx.get('grain', 0.0), g)
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.3: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.3)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names)."""
    D = F.duration
    n = len(F.L)
    t = lambda i: F.t(min(i, n - 1))
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(t(7) - 0.1, t(13) - 0.1, 'room_tone_house', -24, 'inside')
    bed(t(13) - 0.1, t(17) - 0.1, 'school_lunch_hall', -20, 'inside')
    bed(t(21) - 0.1, t(23) - 0.1, 'school_lunch_hall', -22, 'inside')
    bed(t(23) - 0.1, t(28) - 0.1, 'house_morning', -22, 'inside')
    bed(t(28) - 0.1, t(39) - 0.1, 'playground_day', -20, 'outside', kids=True)
    bed(t(39) - 0.1, t(52) - 0.1, 'school_corridor', -20, 'inside', kids=True)
    bed(t(56) - 0.1, t(74) - 0.1, 'suburb_night', -21, 'outside', indoor=True)
    bed(t(74) - 0.1, t(83) - 0.1, 'house_morning', -22, 'inside', birds=True)
    bed(t(89) - 0.1, t(104) - 0.1, 'school_corridor', -21, 'inside')
    bed(t(104) - 0.1, t(108) - 0.1, 'suburb_night', -21, 'outside')
    bed(t(111) - 0.1, t(119) - 0.1, 'school_lunch_hall', -21, 'inside')
    bed(t(119) - 0.1, t(127) - 0.1, 'house_night', -23, 'inside')
    bed(t(127) - 0.1, t(137) - 0.1, 'school_corridor', -21, 'inside')
    bed(t(140) - 0.1, t(148) - 0.1, 'car_interior_idle', -20, 'inside')
    bed(t(148) - 0.1, t(154) - 0.1, 'playground_day', -20, 'outside', kids=True)
    bed(t(154) - 0.1, t(181) - 0.1, 'playground_evening', -21, 'outside', wind=True)
    bed(t(181) - 0.1, t(184) - 0.1, 'suburb_night', -21, 'outside')
    bed(t(187) - 0.1, t(210) - 0.1, 'house_evening', -22, 'inside')
    bed(t(213) - 0.1, t(302) - 0.1, 'house_night', -21, 'inside', fridge_hum=True)
    bed(t(302) - 0.1, t(306) - 0.1, 'suburb_dawn', -20, 'outside', birds=True)
    bed(t(306) - 0.1, t(318) - 0.1, 'school_corridor', -23, 'inside')
    bed(t(318) - 0.1, t(331) - 0.1, 'school_lunch_hall', -21, 'inside', kids=True)
    bed(t(331) - 0.1, t(341) - 0.1, 'house_morning', -24, 'inside', modern=True)
    bed(t(341) - 0.1, D, 'room_tone_house', -26, 'inside')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.55), (1, 0.75), (2, 0.8), (3, 0.95), (5, 1.0), (6, 0.2), (7, 0.25), (13, 0.15), (17, 0.1), (21, 0.25), (28, 0.3),
    (33, 0.45), (36, 0.55), (39, 0.25), (43, 0.2), (47, 0.5), (49, 0.4), (52, 0.35), (56, 0.6), (60, 0.75), (65, 0.9), (69, 0.95),
    (72, 0.8), (73, 0.9), (74, 0.3), (81, 0.55), (83, 0.2), (86, 0.35), (89, 0.6), (92, 0.8), (96, 0.55), (101, 0.45), (104, 0.7),
    (106, 0.75), (108, 0.35), (111, 0.55), (119, 0.75), (122, 0.9), (125, 0.95), (127, 0.35), (131, 0.6), (136, 0.75), (137, 0.4),
    (140, 0.6), (147, 0.75), (148, 0.55), (151, 0.65), (154, 0.6), (157, 0.75), (160, 0.85), (164, 0.95), (167, 1.0), (168, 0.6),
    (171, 0.9), (176, 1.0), (177, 0.85), (180, 0.7), (181, 0.75), (184, 0.4), (188, 0.75), (192, 0.55), (196, 0.6), (199, 0.7),
    (201, 0.85), (207, 0.95), (209, 1.0), (210, 0.5), (213, 0.7), (215, 0.85), (218, 0.95), (223, 0.9), (225, 0.95), (227, 1.0),
    (231, 0.7), (235, 0.9), (238, 1.0), (239, 0.45), (245, 0.6), (251, 0.55), (256, 0.85), (258, 0.6), (262, 0.45), (267, 0.55),
    (272, 0.75), (275, 0.85), (279, 0.9), (285, 1.0), (286, 0.5), (288, 0.45), (291, 0.8), (294, 0.85), (296, 0.6), (300, 0.9),
    (301, 0.7), (302, 0.15), (306, 0.15), (316, 0.2), (318, 0.15), (331, 0.35), (335, 0.45), (336, 0.55), (337, 0.2), (341, 0.1),
    (348, 0.1), (369, 0.15), (376, 0.1), (381, 0.2)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY if i < len(F.L)]
    pts.append([round(F.duration, 2), 0.0])
    return pts


# drop-outs before the big scares (the music goes out, the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(66, -0.35, 0.4), (69, -0.3, 0.35), (125, -0.4, 0.45), (167, -0.3, 0.4), (171, -0.3, 0.4), (218, -0.3, 0.35),
             (235, -0.35, 0.4), (238, -0.3, 0.35), (285, -0.35, 0.45), (336, -0.3, 0.35)]


# ==================================================================================================== Ping / Clank beats: their causes
BEAT_CAUSE = {
    'wednesday_night': "Adam's phone on the bed: each ping lights the dark room, a message bubble from Evie per ping (one note of his song each)",
    'evie_you_asked_for': "Clank: the caretaker's floodlight switches on over the gate, white light floods Evie (she goes flat)",
    'mom_saved_every': "Mom's phone: each ping a new message from Evie arriving while she taps Save",
}


def load_beats():
    try: return json.load(open(BEATS)).get('beats', [])
    except Exception: return []


# ==================================================================================================== the trailer and the spans for the sound team
TRAILER = {'hits': [], 'silence': None, 'pulse': None}   # filled by plan_trailer (times from the timeline)


def _spans(F, pred, gap=0.6):
    out = []
    for sh in F.shots:
        v = pred(sh)
        if not v: continue
        a, b = sh.t0, sh.t1
        if out and a - out[-1]['t1'] <= gap and out[-1]['version'] == v:
            out[-1]['t1'] = round(b, 3)
        else:
            out.append({'t0': round(a, 3), 't1': round(b, 3), 'version': v})
    return out


def _evie_in(sh):
    p = sh.p
    if p.get('evie') is not None: return p['evie']
    if sh.kind == 'bust': return 'near' if p.get('who') == 'evie' or any(b.get('who') == 'evie' for b in p.get('busts', [])) else None
    if sh.kind == 'set': return 'near' if any(q.get('who') == 'evie' for q in p.get('ppl', [])) else None
    if sh.kind == 'ins' and p.get('name') == 'car_window': return 'near'
    return None


def tape_spans(F):
    """Every span with the camcorder tape on screen: 'sweet' (the tape plays: the tape song from the camcorder speaker
    with little Adam's chant), 'warped' (rule 4: slowed, chewed, while Evie stands up), 'rewind' (rule 7: the replay)."""
    return _spans(F, lambda sh: sh.p.get('tape_v') or ('sweet' if sh.kind == 'tape' else None))


def evie_spans(F):
    """Every span where Evie is near (on screen, or her fingers / smile at the letterbox): the tape song ROTTED. 'drag'
    spans are the key reveals where it drags to a halt."""
    return _spans(F, _evie_in, gap=1.2)


DRAG_STOPS = [(167, 'I was.'), (238, 'From me.'), (285, 'It was me.'), (300, "I'm he-")]


_cues0 = Film.cues


def _cues(self, out_dir=None, write=True):
    """The cue sheets (sfx, music, shots) + beats_cues.json (every Ping / Clank with the shot on screen and its cause) +
    spans.json (tape spans, Evie-near spans, the trailer's hits and silence). Music events carry the same spans:
    type 'tape_song' (version sweet | warped | rewind), 'evie_theme' (the tape song rotted), 'drag_stop', 'hit' (trailer,
    with level), 'silence', 'trailer_pulse'."""
    sfx, music = _cues0(self, out_dir, write=False)
    bts = load_beats()
    rows = []
    for b in bts:
        sh = self.shot_at(b['t'])
        cause = BEAT_CAUSE.get(b.get('tag'), '')
        rows.append(dict(b, shot=sh.idx, shot_kind=sh.kind, room=sh.p.get('room') or sh.p.get('name') or sh.p.get('who'), cause=cause))
    ev = music['events']
    tsp, esp = tape_spans(self), evie_spans(self)
    for s in tsp:
        ev.append({'t': s['t0'], 'type': 'tape_song', 'level': 0.55 if s['version'] == 'sweet' else 0.5, 'len': round(s['t1'] - s['t0'], 2),
                   'version': s['version'], 'space': 'tape', 'fixed': True})
    for s in esp:
        if any(a['t0'] - 0.05 <= s['t0'] and s['t1'] <= a['t1'] + 0.05 for a in tsp): continue
        ev.append({'t': s['t0'], 'type': 'evie_theme', 'level': 0.4, 'len': round(s['t1'] - s['t0'], 2), 'version': 'rotted', 'fixed': True})
    drags = []
    for i, w_ in DRAG_STOPS:
        if i < len(self.L):
            te = round(self.e(i), 3); drags.append({'t': te, 'line': i, 'text': w_})
            ev.append({'t': te, 'type': 'drag_stop', 'level': 0.6, 'line': i, 'fixed': True})
    for (th, lv, why) in TRAILER['hits']:
        ev.append({'t': round(th, 3), 'type': 'hit', 'level': round(lv, 2), 'trailer': True, 'why': why, 'fixed': True})
        sfx.append(_ev(th, 'impact_hit', -6 + 6 * lv, 0, None, size=round(0.7 + 0.5 * lv, 2), trailer=True, fixed=True))
    if TRAILER['silence']:
        a, b = TRAILER['silence']
        ev.append({'t': round(a, 3), 'type': 'silence', 'level': 0.0, 'len': round(b - a, 2), 'trailer': True, 'fixed': True})
    if TRAILER['pulse']:
        a, b, waves = TRAILER['pulse']
        ev.append({'t': round(a, 3), 'type': 'trailer_pulse', 'level': 0.7, 'len': round(b - a, 2), 'waves': [round(w_, 3) for w_ in waves],
                   'version': 'tape_song_slowed_detuned', 'fixed': True})
    ev.sort(key=lambda e: e['t'])
    sfx.sort(key=lambda e: (e['t'], e['name']))
    spans = {'note': 'picture spans for the sound team (film seconds on narration_en.wav): tape = Mom\'s camcorder tape on screen '
                     '(the tape song from the camcorder speaker, sweet; warped in rule 4; rewind in rule 7); evie_near = Evie on '
                     'screen or at the letterbox (the same tune rotted); drag_stops = the reveals where it drags to a halt; trailer '
                     '= the cold open\'s hits [t, level 0..1, why], its one silence and its rising pulse (three waves)',
             'tape': tsp, 'evie_near': esp, 'drag_stops': drags,
             'trailer': {'hits': [[round(a, 3), round(b, 2), c] for a, b, c in TRAILER['hits']], 'silence': TRAILER['silence'],
                         'pulse': TRAILER['pulse']}}
    if write:
        out_dir = out_dir or CUES_DIR
        os.makedirs(out_dir, exist_ok=True)
        json.dump(sfx, open(os.path.join(out_dir, 'sfx_cues.json'), 'w'), indent=0)
        json.dump(music, open(os.path.join(out_dir, 'music_cues.json'), 'w'), indent=0)
        json.dump(shot_table(self), open(os.path.join(out_dir, 'shots.json'), 'w'), indent=0)
        json.dump(rows, open(os.path.join(out_dir, 'beats_cues.json'), 'w'), indent=1)
        json.dump(spans, open(os.path.join(out_dir, 'spans.json'), 'w'), indent=1)
    return sfx, music


Film.cues = _cues


# ==================================================================================================== plan helpers (this film)
SLEEVE.update({'adam': ('#8d9098', '#6c6f78'), 'adam_night': ('#2f3f66', '#22304e'), 'adam_grown': ('#44474e', '#32353b'),
               'mom': ('#7e9cbc', '#5f7d9c'), 'lina': ('#c4b0dc', '#a08cbc'), 'danny': ('#d9a93a', '#b4862a')})


def TAPE(t, **p): _FILM[0].cut(t, 'tape', **p)
def PROMPT(t, stage): _FILM[0].cut(t, 'prompt', stage=stage)
def CHECKLIST(t): _FILM[0].cut(t, 'list')
def CARD(t, text_, **p): _FILM[0].cut(t, 'card', text=text_, **p)
def BLACK(t, **p): _FILM[0].cut(t, 'black', **p)
def PH(t, kw, **p): IN(t, 'phone', kw, **p)
def EV(at, *acts, act=None, **k): return P('evie', at, id='evie', act=_A(*acts, act), **k)
def AD(at, *acts, who='adam', act=None, **k): return P(who, at, id='adam', act=_A(*acts, act), **k)
def lock(t0, t1=None): return lambda a, s: (a.lens_lock(t0, t1), a.hold_smile(t0, t1))
def tiltf(t0, ang=14.0, dur=1.2): return lambda a, s: a.tilt_hold(t0, ang, dur)
def glowf(t0, t1=None): return lambda a, s: a.phone_glow(t0, t1)
def typef(t0, t1): return lambda a, s: a.type_phone(t0, t1)
def talkf(t0, t1, txt='mm'): return lambda a, s: a.talk([(t0, t1, txt)])
def K(*keys, **k): return dict(mv='keys', keys=list(keys), free=True, **k)     # keys (t, x, y, z, ease, f)
def step_fn(pairs, default):
    """f(t): the value of the last (t_k, v_k) passed (a screen state that changes on words)."""
    def f(t):
        v = default
        for tk, vk in pairs:
            if t >= tk: v = vk
        return v
    return f


def pulse_fn(times, base=0.15, peak=1.0, dec=0.5):
    return lambda t: max([base] + [peak * math.exp(-(t - x) / dec) for x in times if t >= x])


def _xev(sh, evs):
    for e in evs:
        sh.xev.append(e)


def fingers_acts(text_, letter_t, t_in, t_out=None, key='floor_only', box=(0.15, 0.22, 0.85, 0.78), axis='u', slot_w=0.3,
                 smile=None, stub=None, flap=True):
    """The chalk fingers through the letterbox writing text_ (letters on letter_t) on the floor rect sp.info[key];
    smile = (t0, t1, hum): her chalk smile in the slot; stub = t0: the stub drops and rolls to the bottom stair."""
    def acts(A, sh, sp):
        quad, size = ST.om_floor_quad(sp, *(sp.info[key] if isinstance(key, str) else key))
        lb, db = sp.anchors['letterbox'], sp.anchors['door_base']
        ppc = lb.ppm / 100.0
        f = CH.LetterboxFingers((lb.x, lb.y, slot_w * lb.ppm), (db.x, db.y), quad, text_, box=box, size_cm=size, px_per_cm=ppc,
                                t_in=t_in, letter_times=list(letter_t), t_out=t_out, axis=axis)
        _xev(sh, f.events)
        sd = None
        if stub is not None and 'bottom_stair' in sp.anchors:
            bs = sp.anchors['bottom_stair']
            sd = CH.StubDrop(stub, (lb.x, lb.y), db.y, (bs.x, bs.y), ppc)
            _xev(sh, sd.events)

        def draw(pen, t):
            f.draw_chalk(pen, t)
            if t >= t_in - 0.05: f.draw(pen, t)
            if sd is not None: sd.draw(pen, t)
            if smile and smile[0] <= t <= smile[1]:
                w_, h_ = slot_w * lb.ppm * 0.9, 0.06 * lb.ppm
                pen.fill(rrect(lb.x - w_ / 2, lb.y - h_ / 2, w_, h_, h_ * 0.3), '#020204', 235)
                CH.draw_slot_smile(pen, (lb.x - w_ / 2, lb.y - h_ / 2, w_, h_), t, clamp((t - smile[0]) / 0.4), smile[2])
        lay = Layer(db.depth, draw, 'fingers', ref_depth=db.depth)
        lay.order = sp.order_at(db.X, db.Yp) - 0.3
        return [lay]
    return acts


def chalk_layer(at, text_, h=0.12, dy=0.0, u=1.0, rub=0.0, line=False, reader=None):
    """Chalk in Adam's hand on the ground at an anchor (+ dy metres): the legend's ONLY ME, a name, the empty line."""
    def acts(A, sh, sp):
        s = spot_of(sp, at)
        def draw(pen, t):
            if line: ST.om_line_ground(pen, sp.view, s.X, s.Yp + dy, s.Y + 0.003, h * 3.0, reader=reader)
            else: ST.om_chalk_ground(pen, sp.view, text_, s.X, s.Yp + dy, s.Y + 0.003, h, lvl(u, t), lvl(rub, t), reader=reader)
        lay = Layer(s.depth, draw, 'chalk_' + text_[:4], ref_depth=s.depth)
        lay.order = sp.order_at(s.X, s.Yp) + 0.2
        return [lay]
    return acts


def paint_layer(at, t0, dur, half=0.62, c='#e9c74e'):
    """Fresh paint rolled over the Keeping Square (the caretaker's roller), from the near edge to the far one."""
    def acts(A, sh, sp):
        s = spot_of(sp, at); v = sp.view
        def draw(pen, t):
            u = clamp((t - t0) / dur)
            if u <= 0: return
            y0, y1 = s.Yp - half, s.Yp - half + 2 * half * u
            q = [v.p(s.X - half, s.Y + 0.004, y0), v.p(s.X + half, s.Y + 0.004, y0), v.p(s.X + half, s.Y + 0.004, y1), v.p(s.X - half, s.Y + 0.004, y1)]
            pen.fill(poly(q), c, 245)
        lay = Layer(s.depth, draw, 'paint', ref_depth=s.depth)
        lay.order = sp.order_at(s.X, s.Yp) + 0.05
        return [lay]
    return acts


def girl_layer(at, flat_k, h_m=1.0, alpha=1.0):
    """The setup's chalk girl drawn in the square (flat_k 1 = flat on the ground; < 1 peeling up: rule 4)."""
    def acts(A, sh, sp):
        s = spot_of(sp, at)
        def draw(pen, t):
            CH.draw_chalk_girl(pen, s.x, s.y + 0.18 * s.ppm, h_m * s.ppm, alpha=lvl(alpha, t), t=t, flat_k=lvl(flat_k, t))
        lay = Layer(s.depth, draw, 'chalk_girl', ref_depth=s.depth)
        lay.order = sp.order_at(s.X, s.Yp) + 0.1
        return [lay]
    return acts


def fprint_layer(at, t0, dx=0.0, dy=-60.0):
    """One white chalk fingerprint on the inside of his window (whorls), fading in at t0."""
    def acts(A, sh, sp):
        s = spot_of(sp, at)
        def draw(pen, t):
            a = clamp((t - t0) / 0.5)
            if a <= 0: return
            x, y, r = s.x + dx, s.y + dy, 0.012 * s.ppm + 9
            pen.fill(oval(x, y, r, r * 1.35), '#f4f2ea', 120 * a, blur=2)
            for k in range(1, 6):
                pen.line(oval(x, y + 1.5 * k, r * k / 6.0, r * 1.35 * k / 6.0), 1.6, '#ffffff', 170 * a)
        return [Layer(max(0.3, s.depth - 0.05), draw, 'fingerprint', blur=0)]
    return acts


def car_evie(t_on, t_off=None, scale=1.0):
    """Evie on the pavement right by his car window (between the street and the door frame), lens-locked, never running:
    she is simply there on the cut."""
    def lf(F, sh):
        a = CH.Acting('evie', seed=3 + sh.idx, height=1500.0 * scale)
        a.place(1000, 1850 + 1300 * (scale - 1.0))
        escalate(a, sh, 'evie')
        a.lens_lock(sh.t0); a.hold_smile(sh.t0); a.tilt_hold(sh.t0 + 0.6, 8.0, 1.5)
        sh.actors.append(a)
        m = _Memo(a)

        def draw(pen, t):
            if t < t_on or (t_off is not None and t >= t_off): return
            CH.draw(pen, 'evie', a.x0, a.y0, a.height, m(t), light=DAY, t=t)
        lay = Layer(1.0, draw, 'evie_car', blur=0); lay.order = 1.0
        return lay
    return lf


def rewind_fx(t0, dur=1.4):
    """The cold open's blue door replayed as tape being rewound (rule 7): torn backward bands that settle."""
    def f(t):
        u = clamp((t - t0) / dur)
        return ST.om_tape_fx(warp=0.25, rewind=lambda tt, u=u: max(0.0, 1.0 - u) * 0.9 + 0.1)(t)
    return f


def rew_stamp(t0):
    return lambda cv, t: ST.om_tape_stamp(cv, 9.0 + (t - t0), mode='rew' if t - t0 < 1.6 else 'play')


def lit_win(t0):
    return {'up': (lambda t: clamp((t - t0) / 0.25))}


def swing_rider(t0, t1, anchor='swing_l', taps=True, amp=16.0):
    """Evie on a swing: seated on the seat, riding it (swing_ride keeps her hands on the chains), the swing drawn at the
    same angle (back chain + seat behind her, front chain over her); the other swing hangs still."""
    def act(a, s):
        sp = s.sp; st = sp.anchors[anchor]; pv = sp.anchors[anchor + '_pivot']
        seat_y = st.seat_y if getattr(st, 'seat_y', None) is not None else st.y - 0.45 * st.ppm
        a._swg = ((pv.x, pv.y), seat_y - pv.y, st.ppm / 100.0)
        a.swing_ride(t0, t1, (pv.x, pv.y), seat_y - pv.y, amp=amp)
    def front(pen, t, a):
        if getattr(a, '_swg', None):
            ang, _ = a.swing_state(t); CH.draw_swing(pen, a._swg[0], a._swg[1], ang, a._swg[2], part='front')
    def acts(A, sh, sp):
        a = A['evie']
        other = 'swing_r' if anchor == 'swing_l' else 'swing_l'
        def back(pen, t):
            ang, _ = a.swing_state(t); CH.draw_swing(pen, a._swg[0], a._swg[1], ang, a._swg[2], part='back')
            o, op = sp.anchors[other], sp.anchors[other + '_pivot']
            oy = o.seat_y if getattr(o, 'seat_y', None) is not None else o.y - 0.45 * o.ppm
            CH.draw_swing(pen, (op.x, op.y), oy - op.y, 0.0, o.ppm / 100.0, part='all')
        return [lay_at(sh, 'evie', 0.02, back, 'swing_back')]
    return act, front, acts


# ---------------------------------------------------------------- the trailer (the cold open, lines 0..6)
def plan_trailer(F):
    TR = dict(era='trailer')
    h1, h2, h3 = E(1) + 0.08, E(2) + 0.08, E(3) + 0.06
    h4 = T(4)
    hs = E(5) + 0.03
    hits = TRAILER['hits']; del hits[:]
    # WAVE 1: the tape, sweet, then wrong; her favourite-person stare; the smile that never blinks
    TAPE(0.0, glitch=[WD(0, 'met'), WD(0, 'says')], c=K((0.0, 960, 540, 1, None, 1.02), (W(0, 'favo'), 860, 600, 1, 'in', 1.45)), **TR)
    hits += [(WD(0, 'met'), 0.25, 'tape tracking tear'), (WD(0, 'says'), 0.3, 'tape tear')]
    BU(W(0, 'favo'), 'evie', 'school', 'corridor', stage='wed', cx=960, cy=600, scale=1.15, expr='evie_hold',
       act=_A(tiltf(WD(0, 'person'), 14, 1.0), lock(WD(0, 'whole'))), c=BZ(0.05), **TR)
    hits.append((W(0, 'favo'), 0.45, 'cut: Evie at his shoulder, "favourite person"'))
    TAPE(W(0, "don't"), warp=lambda t, t0=WD(0, "don't"): clamp((t - t0) / 0.7), glitch=[WD(0, "don't"), WD(0, 'back')], off=4.6,
         tape_v='warped', c=K((W(0, "don't"), 820, 600, 1, None, 1.5), (T(1), 800, 610, 1, 'in', 1.9)), **TR)
    hits.append((W(0, "don't"), 0.5, 'the tape chews: "don\'t say it back"'))
    BU(T(1), 'evie', 'front', 'down', st=dict(track='mat', porch=0.6), stage='r6', cx=960, cy=560, scale=1.0, expr='evie_flat',
       act=_A(lock(T(1))), light=PORCH, c=K((T(1), 960, 560, 1, None, 1.0), (h1, 960, 500, 1, 'in', 1.75)), **TR)
    # WAVE 2: the dark phone lights up; ONLY ME creeps up the path (from above); the neck stretches up to the window
    hits.append((h1, 0.7, 'HIT 1: the dark phone'))
    PH(h1, lambda u, t0=h1: dict(screen='dark', lit=clamp((u + t0 - WD(2, 'lights')) / 0.2), bg='bed'),
       c=K((h1, 960, 540, 1, None, 1.0), (W(2, "don't"), 960, 470, 1, 'in', 1.35)),
       sfx=[(WD(2, 'lights'), 'phone_buzz', -10, 0, 'close')], **TR)
    hits.append((WD(2, 'lights'), 0.5, 'the switched-off screen lights up'))
    for w_, tr, at in (("don't", 'street', 'on_street'), ('look', 'half', 'on_half'), ('out', 'foot', 'on_foot'), ('window', 'step', 'on_step')):
        S(W(2, w_), 'front', 'wide', st=dict(track=tr), stage='r5', c=Z(1.18, 0.03, 1150, 760),
          ppl=[EV(at, lock(W(2, w_)), fore_k=2.4)], cut='glitch', **TR)
        hits.append((W(2, w_), 0.35, 'ONLY ME one stretch nearer (%s)' % tr))
    hits.append((h2, 0.8, 'HIT 2: the neck'))
    S(h2, 'front', 'down', st=dict(track='door', porch=0.0, win={'adam': 1.0}), stage='r5',
      ppl=[EV('on_door', lock(h2), lambda a, s: a.neck_up(h2 + 0.15, 2.2, 2.4 * a.height, dx=-0.1 * a.height, grow=0.2))],
      c=K((h2, 830, 640, 1, None, 1.25), (W(3, 'and'), 820, 470, 1, 'in', 1.7)), **TR)
    # WAVE 3: the fingers write ONLY; the whip to the blue door; she stands up out of the red square; the counter races
    hits.append((W(3, 'and'), 0.6, 'the letterbox fingers'))
    S(W(3, 'and'), 'hall', 'floor', st=dict(flap=1.0), night=True, evie='near',
      acts=fingers_acts('ONLY', [WD(3, 'someone') - 0.15, WD(3, 'at'), WD(3, 'your'), WD(3, 'blue') - 0.05], W(3, 'and') - 0.9),
      c=Z(1.0, 0.04), **TR)
    hits.append((W(3, 'blue'), 0.65, 'whip: the blue door from above'))
    S(W(3, 'blue'), 'front', 'down', st=dict(house='danny', track='foot', win={'up': 0.0}), chalk=1.0,
      ppl=[AD('on_foot', lk(W(3, 'blue'), (960, -400)), expr='kind_smile', sil=0.45, sil_rim='#c8d4ff', fore_k=2.2)],
      c=K((W(3, 'blue'), 1300, 600, 1, 'out', 1.15), (W(3, 'blue') + 0.25, 960, 620, 1, 'out', 1.2), (W(3, 'two'), 960, 640, 1, None, 1.3)),
      cut='whip', sfx=[(W(3, 'blue'), 'whoosh', -6, 0, None, {'kind': 'hard'})], **TR)
    hits.append((W(3, 'two'), 0.75, 'Evie stands up out of the red Keeping Square'))
    S(W(3, 'two'), 'play', 'square', st=dict(tod='sunset', square='plain'), stage='r4', rim=SUNSET,
      ppl=[EV('square_stand', lambda a, s: a.flat_drawing(-1e9, WD(3, 'two') + 0.1), lambda a, s: a.stand_from_ground(WD(3, 'two') + 0.1, 1.1),
              lock(WD(3, 'chalked')))], c=K((W(3, 'two'), 960, 600, 1, None, 1.0), (h3, 960, 470, 1, 'in', 1.4)), **TR)
    hits.append((h3, 0.9, 'HIT 3: the counter races'))
    PH(h3, lambda u, t0=h3: dict(screen='thread', count=int(12 + 35 * clamp(u / max(0.2, h4 - t0 - 0.12))), typing=1.0, bg='dark'),
       c=K((h3, 960, 540, 1, None, 1.0), (h4, 960, 600, 1, 'in', 1.5)), cut='glitch', **TR)
    hits.append((h4, 1.0, '47: the blue door from above, slow tilt'))
    S(h4, 'front', 'down', st=dict(house='danny', track='foot', win={'up': 0.0}), chalk=1.0,
      ppl=[AD('on_foot', lk(h4, (960, -400)), expr='kind_smile', sil=0.45, sil_rim='#c8d4ff', fore_k=2.2)],
      c=K((h4, 900, 380, 1, None, 1.15), (T(5), 960, 600, 1, 'in_out', 1.3)), **TR)
    S(T(5), 'front', 'facade', st=dict(house='danny', track='foot', win=lit_win(WD(5, 'grown')), mom=True),
      c=K((T(5), 1000, 520, 1, None, 1.2), (hs, 1040, 380, 1, 'in', 1.5)), **TR)
    hits.append((hs, 1.0, 'HARD STOP: black'))
    BLACK(hs, **TR)
    TRAILER['silence'] = [round(hs, 3), round(T(6) + LEAD + 0.05, 3)]
    TRAILER['pulse'] = [0.0, round(hs, 3), [0.0, round(h1, 3), round(h2, 3)]]
    # 6 I know who it is. -> the scribbled name at the top of the card
    IN(W(6, 'who'), 'card', dict(show=7, bg='desk'), c=K((W(6, 'who'), 420, 220, 1, None, 2.6), (E(6) + 0.8, 430, 225, 1, 'out', 2.3)))


# ---------------------------------------------------------------- the hook (7..12)
def danny_gives(t0, t1, give_t, era=None, talk=False):
    """Danny crosses the corridor with the card and holds it out without meeting Adam's eyes; Mrs. Rahman nods from her
    open door behind him."""
    S(t0, 'school', 'corridor', st=dict(rdoor=80.0), era=era,
      ppl=[P('rahman', 'door_in', id='rahman', face='crossing', expr='rahman_kind',
             act=_A(lk(t0, ('danny', 'head')), nodf(give_t - 0.3))),
           AD('locker', lk(t0 + 0.2, ('danny', 'head')), expr='adam_guarded', face='crossing'),
           P('danny', path=[(t0, 'corr_far'), (give_t - 0.2, 'crossing')], id='danny', surface='inside', expr='danny_shy',
             act=_A(lambda a, s: a.hold_prop('rule_card', 1, t0), lk(give_t - 0.1, ('adam', 'chest'))), talk=talk)],
      c=Z(1.9, 0.03, 930, 720))


def nodf(t0, n=1):
    return lambda a, s: a.nod(t0, n)


def plan_hook(F):
    IN(T(7), 'card', dict(show=7, bg='desk'), c=K((T(7), 430, 225, 1, None, 2.3), (W(7, 'rules'), 960, 540, 1, 'in_out', 1.0)))
    IN(T(8), 'card', dict(show=7, bg='desk'), c=dict(mv='push', f=1.6, x=1000, y=600, rate=0.03, free=True))
    IN(T(9), 'card', dict(show=7, bg='desk'), c=K((T(9), 700, 400, 1, None, 1.5), (W(9, 'scribbled'), 420, 220, 1, 'in_out', 2.6)))
    BU(T(10), 'evie', 'school', 'lunch', stage='mon', cx=980, cy=600, scale=0.95, turn=-0.3, expr='evie_grin',
       act=_A(lambda a, s: a.bounce(T(10) + 0.2, E(10)), lambda a, s: a.laugh_away(W(10, 'best'), 1.2, 1)), c=BZ(0.02))
    BU(T(11), 'evie', 'school', 'lunch', stage='wed', cx=960, cy=580, scale=1.25, expr='evie_hold', act=_A(lock(T(11)), tiltf(T(11) + 0.2, 12)),
       c=BZ(0.05))
    S(T(12), 'front', 'down', st=dict(track='mat', porch=1.0), stage='r7', ppl=[EV('on_mat', lock(T(12)))], c=Z(1.2, 0.03, 800, 640), era='trailer')
    S(W(12, 'my'), 'hall', 'up', st=dict(landing=1.0), rim=BULB,
      ppl=[P('lina', 'lina_landing', id='lina', expr='lina_earnest', face=(0.0, -3.0),
             act=_A(lambda a, s: a.hold_prop('rule_card', 1), lambda a, s: a.reach_to(W(12, 'my') + 0.2, 1, (a.x0 + 40, a.y0 - 1.05 * a.height), dur=0.5, prop='rule_card')))],
      c=Z(1.4, 0.03, 760, 600))
    S(W(12, 'halfway', off=-0.5), 'hall', 'halfway', st=dict(landing=1.0, chalk=[dict(text='ONLY', x=0.8, y=0.5, h=0.3)], stub=True),
      c=Z(1.1, 0.03, 880, 760))


# ---------------------------------------------------------------- the setup (13..51)
def plan_setup(F):
    S(T(13), 'school', 'lunch',
      ppl=[P('kofi', 'opp_l', id='kofi', act=_A(lk(T(13), ('danny', 'head'))), talk=False), P('danny', 'opp_seat', id='danny', expr='kind_smile',
           act=_A(lk(T(13) + 0.3, ('kofi', 'head')))), P('sam', 'opp_r', id='sam', expr='kind_smile', act=_A(lk(T(13), ('danny', 'head'))))],
      c=Z(1.5, 0.02, 960, 700))
    BU(T(15), 'danny', 'school', 'lunch', cx=900, cy=600, scale=1.1, turn=-0.55, expr='kind_smile', c=BZ(0.03))
    S(T(16), 'school', 'lunch', ppl=[AD('adam_seat', lk(T(16), 'table_top'), expr='adam_lonely')], c=Z(1.6, 0.03, 1040, 700))
    # the tape: little Adam and Danny at seven on the swings, the song
    TAPE(T(17), c=K((T(17), 960, 540, 1, None, 1.0), (T(18), 900, 560, 1, 'in_out', 1.12)))
    TAPE(T(18), off=3.0, c=K((T(18), 800, 520, 1, None, 1.55), (W(18, 'everywhere'), 800, 540, 1, 'in_out', 1.7)))
    TAPE(W(18, 'everywhere'), off=8.0, c=K((W(18, 'everywhere'), 900, 560, 1, None, 1.2), (E(20), 900, 560, 1, 'in_out', 1.3)))
    S(T(21), 'school', 'lunch_table', ppl=[P('danny', 'opp_seat', id='danny', expr='kind_smile', hands='lap',
                                              act=_A(lk(T(21), (400, 560))))], c=Z(1.4, 0.02, 925, 760))
    TAPE(T(22), off=14.0, c=K((T(22), 1000, 560, 1, None, 1.6), (W(22, 'gone'), 1000, 580, 1, 'in', 2.0)))
    BU(W(22, 'gone'), 'danny', 'school', 'lunch', cx=980, cy=640, scale=0.9, turn=0.4, expr='danny_shy', c=BZ(0.02))
    # Monday: the hoodie
    S(T(23), 'kitchen', 'dinner', st=dict(kitchen=1.0), rim=KITCH, night=False,
      ppl=[P('mom', 'stand_mom', id='mom', expr='mom_watchful', turn=0.12, act=_A(lambda a, s: a.hold_hoodie(T(23) + 0.2), lk(T(23) + 0.4, (960, 300))))],
      c=Z(1.35, 0.02, 850, 700))
    S(T(24), 'kitchen', 'dinner', st=dict(kitchen=1.0), rim=KITCH, night=False,
      ppl=[P('mom', 'stand_mom', id='mom', expr='mom_watchful', turn=0.12, act=_A(lambda a, s: a.hold_hoodie(T(23) - 1.0), lk(T(24), (960, 300))))],
      c=Z(2.3, 0.02, 830, 640))
    BU(T(25), 'mom', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, cx=900, cy=600, scale=0.95, turn=0.35, expr='mom_watchful', light=KITCH, c=BZ(0.02))
    BU(T(26), 'adam', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, cx=1020, cy=600, scale=0.95, turn=-0.35, expr='adam_guarded', light=KITCH,
       act=_A(lk(E(26) + 0.1, (1600, 700))), c=BZ(0.02))
    BU(T(27), 'mom', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, cx=900, cy=590, scale=1.1, turn=0.3, expr='mom_watchful', light=KITCH,
       act=_A(lk(T(27), (1300, 560))), c=BZ(0.03))
    # the legend
    S(T(28), 'play', 'wide', st=dict(tod='day', square='plain'), c=Z(1.0, 0.015))
    S(T(29), 'play', 'hop', st=dict(tod='day', square='plain'), c=K((T(29), 1000, 700, 1, None, 1.0), (E(29), 965, 520, 1, 'in_out', 1.6)))
    S(T(30), 'play', 'square', st=dict(tod='day', square='plain'), c=Z(1.0, 0.04, 960, 520))
    S(T(32), 'play', 'hop', st=dict(tod='sunset', square='plain'), rim=SUNSET, c=Z(1.2, 0.02, 970, 560))
    S(T(33), 'play', 'square', st=dict(tod='sunset', square='plain'), rim=SUNSET,
      acts=lambda A, s, sp: (chalk_layer('square_stand', '', h=0.09, dy=0.1, line=True)(A, s, sp) +
                             chalk_layer('square_stand', 'ONLY ME', h=0.09, dy=-0.06, u=lambda t: clamp((t - WD(33, 'only')) / 0.8))(A, s, sp)),
      c=Z(1.4, 0.03, 960, 520))
    S(T(35), 'play', 'wide', st=dict(tod='day', square='plain'), c=Z(1.1, 0.01))
    S(T(36), 'play', 'square', st=dict(tod='day', square='girl'), c=Z(1.0, 0.02, 960, 520))
    S(T(37), 'play', 'square', st=dict(tod='day', square='girl'), c=K((T(37), 960, 480, 1, None, 1.8), (E(38), 960, 470, 1, 'in_out', 2.6)))
    # Monday: Evie
    BU(T(39), 'adam', 'school', 'lunch', cx=760, cy=640, scale=0.9, turn=0.25, expr='adam_lonely',
       busts=[dict(who='evie', cx=1260, cy=560, scale=0.75, depth=1.3, act=lambda a, s: a.bounce(T(39) + 0.4, E(39) + 1), expr='evie_grin')],
       c=BZ(0.02))
    BU(T(40), 'evie', 'school', 'lunch', stage='mon', cx=960, cy=640, scale=1.45, expr='evie_grin', act=_A(lambda a, s: a.bounce(T(40), E(41))), c=BZ(0.02))
    BU(T(42), 'evie', 'school', 'lunch', stage='mon', cx=1080, cy=560, scale=0.85, turn=-0.5, expr='evie_grin', act=_A(lambda a, s: a.laugh_away(T(42) + 0.3, 1.4, -1)),
       c=BZ(0.02))
    BU(T(43), 'evie', 'school', 'lunch', stage='mon', cx=960, cy=600, scale=1.0, expr='evie_grin',
       act=_A(lambda a, s: a.wave_hi(T(43), E(43)), lambda a, s: a.bounce(T(43), E(43))), c=BZ(0.02))
    S(T(44), 'school', 'corridor', ppl=[EV('locker', lambda a, s: a.bounce(T(44), E(45)), lk(T(44), (300, 600))),
                                        AD('corr_mid', expr='kind_smile', face='locker')], c=Z(2.4, 0.02, 980, 740))
    BU(T(45), 'evie', 'school', 'corridor', stage='mon', cx=960, cy=600, scale=1.0, expr='evie_laugh', act=_A(lambda a, s: a.laugh_away(T(45) + 0.2, 1.2, 1)),
       c=BZ(0.02))
    BU(T(46), 'adam', 'school', 'corridor', cx=960, cy=610, scale=1.0, turn=-0.2, expr='kind_smile', c=BZ(0.02))
    # Wednesday: at my shoulder
    BU(T(47), 'adam', 'school', 'corridor', cx=720, cy=640, scale=0.95, turn=0.3, expr='adam_guarded',
       busts=[dict(who='evie', cx=1180, cy=600, scale=0.95, depth=1.1, expr='evie_hold',
                   act=lambda a, s: (a.tilt_hold(T(47) + 0.3, 10, 1.4), a.lens_lock(WD(47, 'blink'))))],
       c=K((T(47), 960, 560, 1, None, 1.0), (E(47), 1120, 540, 1, 'in', 1.45)))
    BU(T(48), 'evie', 'school', 'corridor', cx=960, cy=600, scale=1.15, turn=-0.25, expr='evie_hold',
       act=_A(lk(T(48), (500, 560)), lock(WD(48, 'whole'))), c=BZ(0.04))
    BU(T(49), 'adam', 'school', 'corridor', cx=960, cy=610, scale=1.0, turn=0.25, expr='adam_guarded', act=_A(lk(T(49) + 0.3, (1500, 560))), c=BZ(0.02))
    danny_gives(T(50), E(51), W(51, 'they'))
    BU(T(51), 'danny', 'school', 'corridor', cx=980, cy=610, scale=1.0, turn=-0.35, expr='danny_shy',
       act=_A(lk(T(51), (1300, 900))), c=BZ(0.02))
    IN(W(51, 'they'), 'card', dict(show=7, bg='school'), c=Z(1.05, 0.02))


# ---------------------------------------------------------------- rule 1 (52..85)
def plan_rule1(F):
    bts = [b['t'] for b in load_beats() if b.get('line') == 56]
    RULE(T(52), 1)
    S(T(56), 'room', 'bed', st=dict(phone=pulse_fn(bts, 0.1, 1.0, 0.6)), night=True,
      ppl=[AD('bed_edge', lk(T(56), 'phone_bed'), who='adam_night', expr='adam_guarded')], c=Z(1.3, 0.02, 1000, 560))
    PH(T(57), dict(screen='thread', count=12, typing=1.0, bg='bed'), c=Z(1.0, 0.03))
    PH(T(58), lambda u, t0=T(58): dict(screen='thread', count=step_fn([(WD(59, 'thirty'), 30), (WD(60, 'forty'), 47)], 12)(u + t0), typing=1.0, bg='bed'),
       c=Z(1.1, 0.04))
    BU(W(60, 'forty'), 'evie', 'front', 'street', st=dict(track='street'), cx=960, cy=640, scale=1.1, expr='evie_hold', light=PHONE,
       act=_A(glowf(W(60, 'forty')), typef(W(60, 'forty'), E(62) + 1), lock(W(60, 'forty') + 0.4)), c=BZ(0.03), talk=False)
    PH(T(61), dict(screen='thread', count=47, typing=1.0, bg='bed'), c=Z(1.3, 0.03, 960, 700))
    BU(T(62), 'evie', 'front', 'street', st=dict(track='street'), cx=960, cy=620, scale=1.25, expr='evie_hurt', light=PHONE,
       act=_A(glowf(T(62)), typef(T(62), E(62) + 1)), c=BZ(0.04))
    S(T(63), 'room', 'bed', st=dict(phone=lambda t: 1.0 - clamp((t - WD(64, 'off')) / 0.2)), night=True,
      ppl=[AD('bed_edge', lambda a, s: a.phone_type(T(63), WD(64, 'off')), who='adam_night', expr='adam_steady')], c=Z(1.4, 0.02, 1000, 580))
    PH(T(65), lambda u, t0=T(65): dict(screen='dark', lit=clamp((u + t0 - WD(65, 'lit')) / 0.2), bg='bed'), c=Z(1.0, 0.03),
       sfx=[(WD(65, 'lit'), 'phone_buzz', -12, 0, 'close')])
    PH(T(66), dict(screen='dark', lit=1.0, bg='bed'), c=Z(1.3, 0.05, 960, 520))
    S(T(67), 'front', 'street', st=dict(track='street'), ppl=[EV('on_street', lock(T(67)), tiltf(T(67) + 0.5, 10))], c=Z(1.6, 0.02, 1110, 640))
    S(T(68), 'front', 'street', st=dict(track='street'), ppl=[EV('on_street', lock(T(67)))],
      c=K((T(68), 1110, 640, 1, None, 1.6), (E(69), 1120, 680, 1, 'in_out', 2.6)), hit=[WD(69, 'only')])
    BU(T(70), 'evie', 'front', 'street', st=dict(track='street'), cx=960, cy=600, scale=1.2, expr='evie_hold', act=_A(lock(T(70))), c=BZ(0.05))
    S(T(71), 'room', 'wide', st=dict(lamp=lambda t: 1.0 - clamp((t - WD(71, 'off')) / 0.12), track='street'), night=True,
      ppl=[AD('window', who='adam_night', face=(-1.4, -3.0))], c=Z(1.2, 0.02, 960, 700), sfx=[(WD(71, 'off'), 'light_switch', -14, 0, 'inside')])
    S(T(72), 'front', 'street', st=dict(track='street', porch=dict(on=WD(72, 'clicked'))),
      ppl=[EV('on_street', lock(T(72), WD(72, 'clicked')), lambda a, s: a.flinch(WD(72, 'clicked') + 0.1))], c=Z(1.45, 0.02, 1100, 680),
      sfx=[(WD(72, 'clicked'), 'porch_light_click', -10, 0, 'outside')])
    S(T(73), 'front', 'street', st=dict(track='street', porch=1.0),
      ppl=[EV('on_street', lambda a, s: a.lie_flat(WD(73, 'lay'), 0.8), lambda a, s: a.slide_flat(WD(73, 'slid'), 1.6, (a.x0 + 420, a.y0 - 70), scale_to=0.8))],
      c=Z(1.45, 0.02, 1150, 650))
    # Thursday morning
    S(T(74), 'front', 'wide', st=dict(tod='dawn', track='street', track_wet=1.0, bucket=True), rim=DAWN, c=Z(1.05, 0.01))
    S(T(76), 'front', 'step', st=dict(tod='dawn', bucket=True), rim=DAWN, c=Z(1.2, 0.03, 1100, 420))
    S(T(77), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1,
      ppl=[P('mom', 'stand_mom', id='mom', expr='mom_tired', face='bucket', act=_A(lambda a, s: a.phone_to_ear(T(77) - 0.5)))], c=Z(1.5, 0.02, 760, 700))
    BU(T(78), 'mom', 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1, cx=920, cy=600, scale=1.0, turn=0.45, expr='mom_tired', light=KITCH,
       act=_A(lambda a, s: a.phone_to_ear(T(78) - 1.0)), c=BZ(0.02))
    BU(T(79), 'adam', 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, cx=1000, cy=610, scale=0.95, turn=-0.3, expr='kind_smile', c=BZ(0.02))
    S(T(81), 'front', 'step', st=dict(tod='dawn', bucket=True, print=True), rim=DAWN, c=Z(1.3, 0.02, 960, 500))
    S(T(82), 'front', 'step', st=dict(tod='dawn', bucket=True, print=True), rim=DAWN, c=Z(2.6, 0.03, 960, 534), hit=[WD(82, 'pointing') + 0.2])
    PROMPT(T(83), 'ask')


# ---------------------------------------------------------------- rule 2 (86..107)
def plan_rule2(F):
    RULE(T(86), 2)
    IN(T(89), 'locker', dict(dust=0.0), c=Z(1.0, 0.02), sfx=[(T(89) + 0.15, 'locker_open', -12, 0, 'inside')])
    IN(T(90), 'locker', dict(dust=0.0), c=Z(1.6, 0.03, 960, 640))
    IN(T(91), 'locker', dict(dust=1.0), c=Z(2.3, 0.03, 960, 650))
    BU(W(92, 'evie'), 'adam', 'school', 'locker', cx=700, cy=640, scale=0.95, turn=0.35, expr='adam_scared',
       busts=[dict(who='evie', cx=1120, cy=610, scale=0.95, depth=1.1, expr='evie_hold',
                   act=lambda a, s: (a.one_inch(W(92, 'evie'), None, -1), a.lens_lock(T(93))))],
       c=K((W(92, 'evie'), 960, 560, 1, None, 1.0), (E(94), 930, 600, 1, 'in', 1.4)))
    BU(T(95), 'evie', 'school', 'locker', cx=960, cy=610, scale=1.1, turn=-0.2, expr='evie_hold', act=_A(lk(T(95), (420, 650)), lock(W(95, 'only'))),
       c=BZ(0.03))
    BU(T(96), 'adam', 'school', 'locker', cx=960, cy=610, scale=1.0, turn=0.25, expr='adam_scared', c=BZ(0.03))
    TAPE(T(98), off=16.0, c=K((T(98), 1000, 560, 1, None, 1.8), (E(98), 1000, 580, 1, 'in', 2.2)))
    S(T(99), 'school', 'lunch', ppl=[P('kofi', 'opp_l', id='kofi'), P('danny', 'opp_seat', id='danny', expr='kind_smile', act=_A(lk(T(99), ('kofi', 'head')))),
                                     P('sam', 'opp_r', id='sam', expr='kind_smile')], c=Z(1.6, 0.02, 950, 700))
    BU(T(100), 'adam', 'school', 'lunch', cx=980, cy=620, scale=1.0, turn=0.3, expr='adam_lonely', light=PHONE,
       act=_A(lk(T(100), (1200, 1100))), c=BZ(0.02))
    IN(T(101), 'locker', dict(dust=1.0), c=K((T(101), 960, 640, 1, None, 2.0), (E(102), 960, 660, 1, 'in', 2.7)))
    S(T(103), 'school', 'corridor', ppl=[AD('locker', expr='adam_lonely', face='crossing'),
                                         EV('corr_far', glowf(T(103)), lock(T(103) + 0.3))], c=Z(2.0, 0.03, 960, 690))
    S(T(104), 'front', 'wide', st=dict(track='half'), ppl=[EV('on_half', lock(T(104)))], c=Z(1.2, 0.02, 1100, 760))
    S(T(105), 'front', 'wide', st=dict(track='half'), ppl=[EV('on_half', lock(T(104)), tiltf(T(105) + 0.3, 12))], c=Z(2.2, 0.03, 1150, 700))
    BU(T(106), 'evie', 'front', 'wide', st=dict(track='half'), cx=960, cy=600, scale=1.15, expr='evie_hold', act=_A(lock(T(106))), c=BZ(0.03))
    BU(T(107), 'evie', 'front', 'wide', st=dict(track='half'), cx=960, cy=520, scale=1.7, expr='evie_hold', act=_A(lock(T(107))), c=BZ(0.04))


# ---------------------------------------------------------------- rule 3 (108..136)
MAP_T = None


def plan_rule3(F):
    RULE(T(108), 3)
    S(T(111), 'school', 'lunch', ppl=[AD('adam_seat', lk(T(111), ('evie', 'head')), expr='adam_guarded'),
                                      EV('opp_seat', lambda a, s: a.reach_to(W(111, 'slid'), 1, scr(s.sp, 'table_top'), dur=0.7, prop='evie_phone'),
                                         lk(T(111), ('adam', 'head')))], c=Z(1.7, 0.02, 1000, 720))
    BU(T(112), 'evie', 'school', 'lunch', cx=960, cy=610, scale=1.05, turn=-0.25, expr='evie_hurt', act=_A(lk(T(112), (500, 640)), tiltf(W(112, 'trust'), 12)),
       c=BZ(0.03))
    PH(T(113), lambda u, t0=T(113): dict(screen='type', draft='•' * 8, draft_k=clamp((u) / 1.0), bg='table'), c=Z(1.2, 0.03),
       sfx=[(T(113) + 0.1, 'phone_tap', -20, 0, 'close', {'n': 8})])
    PH(T(114), lambda u, t0=T(114): dict(screen='map', blue='school', white=('school' if u + t0 >= WD(114, 'white') else 'shop'), bg='table'), c=Z(1.1, 0.02))
    PH(T(115), lambda u, t0=T(115): dict(screen='map', blue=step_fn([(WD(117, 'shop'), 'shop'), (WD(118, 'danny'), 'street')], 'bus_stop')(u + t0),
                                          white=step_fn([(WD(116, 'bus') - 0.6, 'bus_stop'), (WD(117, 'shop') - 0.6, 'shop'), (WD(118, 'danny') - 0.6, 'danny')], 'school')(u + t0),
                                          bg='table'), c=Z(1.15, 0.02))
    S(T(119), 'room', 'door', st=dict(strip=1.0, shadow=lambda t: clamp((t - T(119) - 0.4) / 0.6)), night=True, c=Z(1.3, 0.02, 850, 700))
    PH(T(120), lambda u, t0=T(120): dict(screen='map', zoom='house', blue='room',
                                          white=step_fn([(WD(121, 'inside'), 'inside'), (WD(122, 'room'), 'room')], 'house')(u + t0), bg='bed'), c=Z(1.2, 0.03))
    S(T(123), 'room', 'wide', st=dict(torch=lambda t: clamp((t - WD(123, 'swung')) / 0.15)), night=True,
      ppl=[AD('room_mid', who='adam_night', expr='adam_scared', face=(-1.0, -1.5), act=_A(lambda a, s: a.reach_to(WD(123, 'swung') - 0.2, 1, (a.x0 - 200, a.y0 - 0.7 * a.height), dur=0.4)))],
      c=Z(1.1, 0.02, 1000, 760), sfx=[(WD(123, 'swung'), 'torch_click', -14, 0, 'inside')])
    S(T(124), 'room', 'window', st=dict(torch=1.0, track='foot'), night=True, c=Z(1.0, 0.02))
    S(T(125), 'room', 'window', st=dict(torch=1.0, track='foot'), night=True, acts=fprint_layer('window_glass', W(125, 'fingerprint')),
      c=K((T(125), 960, 420, 1, None, 1.2), (E(125), 960, 320, 1, 'in', 2.2)), hit=[WD(125, 'inside')])
    S(T(126), 'front', 'down', st=dict(track='foot'), ppl=[EV('on_foot', lock(T(126)))], c=Z(1.15, 0.02, 1000, 720))
    # Friday
    S(T(127), 'school', 'rahman', st=dict(rdoor=80.0), ppl=[P('rahman', 'rahman_door', id='rahman', expr='rahman_kind', face=(0.0, -3.0))], c=Z(1.3, 0.02, 1050, 760))
    BU(T(129), 'rahman', 'school', 'rahman', st=dict(rdoor=80.0), cx=940, cy=600, scale=0.95, turn=0.3, expr='rahman_kind',
       act=_A(nodf(W(129, 'open'))), c=BZ(0.02))
    S(T(130), 'school', 'corridor', st=dict(rdoor=80.0),
      ppl=[P('rahman', 'door_in', id='rahman', expr='rahman_calm', act=_A(lk(T(130), ('adam', 'head')))),
           AD(None, path=[(T(130), 'corr_far'), (E(130) + 0.9, 'corr_mid')], surface='inside', expr='adam_guarded')], c=Z(1.9, 0.02, 880, 720))
    PH(T(131), lambda u, t0=T(131): dict(screen='mute', mute=step_fn([(WD(132, 'mom'), 1), (WD(133, 'sister'), 2), (WD(134, 'danny'), 3)], 0)(u + t0), bg='table'),
       c=Z(1.15, 0.02))
    BU(T(135), 'adam', 'school', 'corridor', cx=960, cy=620, scale=1.05, expr='adam_scared', light=PHONE, act=_A(lk(T(135), (960, 1200))), c=BZ(0.03))
    S(T(136), 'school', 'corridor', ppl=[AD('locker', expr='adam_scared', face='crossing', act=_A(lk(T(136), (960, 1000)))),
                                         EV('corr_far', glowf(T(136)), typef(T(136), E(136)), lock(W(136, 'me')))], c=Z(2.2, 0.03, 940, 690))


# ---------------------------------------------------------------- rule 4 (137..183)
def plan_rule4(F):
    RULE(T(137), 4)
    IN(T(140), 'car_window', dict(light='red'), c=Z(1.0, 0.02), sfx=[(T(140) + 0.3, 'car_indicator', -18, 0, 'inside', {'dur': 2.0})])
    IN(T(142), 'car_window', dict(light='red'), layers=[car_evie(T(142))], c=Z(1.0, 0.03), evie='near')
    IN(T(143), 'car_window', dict(light='green'), layers=[car_evie(T(143), WD(144, 'gone') - 0.05)], c=Z(1.0, 0.01), evie='near')
    IN(T(145), 'car_window', dict(light='red'), c=Z(1.0, 0.01), sfx=[(T(145) + 0.2, 'car_indicator', -18, 0, 'inside', {'dur': 1.2})])
    IN(W(146, 'there'), 'car_window', dict(light='red'), layers=[car_evie(W(146, 'there'))], c=Z(1.05, 0.05), evie='near',
       hit=[W(146, 'there') + 0.05])
    sw_act, sw_front, sw_acts = swing_rider(T(148) - 2.0, E(149) + 2.0)
    for i0, c_, tp in ((148, Z(1.15, 0.02, 1000, 560), True), (149, Z(1.9, 0.02, 1010, 520), False)):
        S(T(i0), 'play', 'swings', st=dict(tod='day', swings=False), stage='r4', acts=sw_acts,
          ppl=[EV('swing_l', sw_act, lambda a, s, tp=tp: a.sing_song(T(148) + 0.3, 0.42, 14, taps=tp), lock(W(148, 'sang')),
                  kind='seat', turn=0.65, extras=[sw_front])], c=c_)
    S(T(150), 'school', 'corridor', ppl=[P('danny', 'locker', id='danny', expr='kind_smile', face='crossing'),
                                         AD(None, path=[(T(150), 'corr_mid'), (E(150) + 0.4, 'crossing')], surface='inside', expr='adam_scared')],
      c=Z(2.2, 0.02, 960, 740))
    BU(T(151), 'adam', 'school', 'corridor', cx=960, cy=610, scale=1.0, turn=0.35, expr='adam_scared', act=_A(lk(T(151), (1500, 600))), c=BZ(0.03))
    BU(T(152), 'danny', 'school', 'corridor', cx=960, cy=610, scale=1.0, turn=-0.35, expr='puzzled', act=_A(blinks(WD(152, 'blinked'), WD(152, 'blinked') + 0.5)), c=BZ(0.02))
    # sunset: alone to the square
    S(T(154), 'play', 'wide', st=dict(tod='sunset', square='adam', prints=1.0), rim=SUNSET,
      ppl=[AD(None, path=[(T(154), 'gate_adam'), (E(155) + 0.5, 'hop_start')], surface='gravel', expr='adam_guarded')], c=Z(1.2, 0.02, 800, 650))
    S(T(156), 'play', 'hop', st=dict(tod='sunset', square='adam', prints=1.0), rim=SUNSET,
      ppl=[AD(None, path=[(T(156), 'hop_start'), (E(156) + 1.0, 'square_front')], surface='gravel', expr='adam_scared')], c=Z(1.1, 0.02, 1000, 650))
    S(T(157), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, c=Z(1.0, 0.02, 960, 500))
    S(T(158), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, c=K((T(158), 960, 520, 1, None, 1.6), (E(159), 1000, 560, 1, 'in_out', 2.2)))
    S(T(160), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, c=K((T(160), 960, 440, 1, None, 2.0), (E(161), 960, 450, 1, 'in_out', 2.3)))
    S(T(162), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, c=K((T(162), 960, 470, 1, None, 1.8), (E(163), 960, 560, 1, 'in', 2.4)),
      hit=[WD(163, 'only')])
    TAPE(T(164), off=10.0, warp=lambda t, t0=T(164): 0.4 + 0.6 * clamp((t - t0) / 1.5), tape_v='warped', evie='near',
         c=K((T(164), 800, 540, 1, None, 1.4), (E(164), 820, 560, 1, 'in', 1.6)))
    S(T(165), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, tape_v='warped', evie='near',
      acts=girl_layer('square_stand', lambda t, t0=T(165): 1.0 - 0.35 * clamp((t - t0) / 1.6), h_m=0.6), c=Z(1.4, 0.04, 960, 520))
    BU(T(166), 'adam', 'play', 'square', st=dict(tod='sunset', square='adam'), cx=960, cy=610, scale=1.0, turn=0.2, expr='adam_ashamed', light=SUNSET, c=BZ(0.02))
    BU(T(167), 'adam', 'play', 'square', st=dict(tod='sunset', square='adam'), cx=960, cy=560, scale=1.5, expr='adam_ashamed', light=SUNSET, c=BZ(0.05))
    S(T(168), 'play', 'hop', st=dict(tod='sunset', square='danny', chalk_u=lambda t: clamp((t - WD(169, 'chalked')) / 1.6)), rim=SUNSET, era='memory',
      ppl=[AD('square_front', expr='kind_smile', kind='kneel', face='square_stand',
              act=_A(lambda a, s: a.reach_to(WD(169, 'chalked') - 0.3, 1, scr(s.sp, 'square_stand'), dur=0.5, contact='grip')))],
      c=Z(1.9, 0.02, 965, 520))
    S(T(171), 'play', 'gate', st=dict(tod='sunset', square='adam'), rim=SUNSET, stage='r4',
      ppl=[AD('gate_adam', expr='adam_scared', face='gate'),
           EV('square_stand', lambda a, s: a.flat_drawing(-1e9, WD(171, 'stood')), lambda a, s: a.slide_flat(WD(171, 'slid') - 0.2, 1.9, scr(s.sp, 'gate'), scale_to=0.62),
              lambda a, s: a.stand_from_ground(WD(171, 'stood'), 1.2), lock(WD(171, 'stood') + 0.4))],
      c=Z(1.0, 0.02, 1150, 760))
    BU(T(172), 'evie', 'play', 'gate', st=dict(tod='sunset', square='adam'), cx=960, cy=600, scale=1.15, expr='evie_flat', light=SUNSET,
       act=_A(lock(T(172))), c=BZ(0.04))
    S(T(174), 'play', 'gate', st=dict(tod='sunset', square='adam'), rim=SUNSET,
      ppl=[AD('gate_adam', expr='adam_scared', face='gate'), EV('gate', lambda a, s: a.block_wide(T(174) + 0.1), lock(T(174)))], c=Z(1.35, 0.02, 950, 760))
    BU(T(176), 'evie', 'play', 'gate', st=dict(tod='sunset', square='adam'), cx=960, cy=600, scale=1.05, expr='evie_flat', light=SUNSET,
       act=_A(lk(T(176), (700, 900)), lambda a, s: a.block_wide(T(176) - 1.0)), c=BZ(0.03))
    clank = ([b['t'] for b in load_beats() if b['kind'] == 'clank'] or [E(176) + 0.3])[0]
    S(clank - 0.02, 'play', 'gate', st=dict(tod='sunset', square='adam', flood=dict(on=clank)), rim=FLOOD,
      ppl=[AD('gate_adam', expr='adam_scared', face='gate'),
           EV('gate', lambda a, s: a.block_wide(T(176) - 1.0, clank + 0.2), lambda a, s: a.flinch(clank + 0.05), lk(clank + 0.1, (300, 200)))],
      c=Z(1.35, 0.02, 950, 760), hit=[clank])
    BU(T(178), 'caretaker', 'play', 'flood', st=dict(tod='sunset', square='adam', flood=1.0), cx=960, cy=620, scale=1.0, turn=0.3, expr='squint_up', light=FLOOD,
       act=_A(lambda a, s: a.reach_to(T(178), 1, (a.x0 - 60, a.y0 - 0.93 * a.height), dur=0.45, shape='flat')), c=BZ(0.02))
    S(T(179), 'play', 'gate', st=dict(tod='sunset', square='adam', flood=1.0), rim=FLOOD,
      ppl=[AD('gate_adam', expr='adam_scared', face='gate'), EV('gate', lambda a, s: a.lie_flat(WD(179, 'flat') - 0.1, 0.35))], c=Z(1.35, 0.02, 950, 760))
    S(T(180), 'play', 'wide', st=dict(tod='sunset', square='adam', flood=1.0), rim=SUNSET,
      ppl=[AD(None, path=[(T(180), 'gate_adam'), (E(180) + 1.2, 'hop_start')], surface='gravel', run=True, expr='adam_scared')], c=Z(1.15, 0.02, 760, 680))
    S(T(181), 'front', 'down', st=dict(track='step'), ppl=[EV('on_step', lock(T(181)))], c=Z(1.2, 0.02, 950, 700))
    S(T(182), 'front', 'down', st=dict(track='step'), ppl=[EV('on_step', lock(T(181)), tiltf(T(182) + 0.4, 14, 1.6), lambda a, s: a.chalk_tap(W(183, 'waiting')))], c=K((T(182), 930, 700, 1, None, 1.6), (E(183), 930, 730, 1, 'in', 1.95)))


# ---------------------------------------------------------------- rule 5 (184..209)
def plan_rule5(F):
    RULE(T(184), 5)
    DIN = dict(kitchen=1.0, dinner=True)
    S(T(187), 'kitchen', 'dinner', st=DIN, night=False,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_warm', turn_free=True, act=_A(lambda a, s: a.hold_prop('fork', 1)))], c=Z(1.0, 0.015))
    S(T(188), 'kitchen', 'dinner', st=DIN, night=True,
      ppl=[EV('window_out', lock(W(188, 'lips')), talkf(W(188, 'lips'), E(188) + 0.3), check=False),
           P('mom', 'mom_chair', id='mom', expr='mom_tired', act=_A(lambda a, s: a.hold_prop('fork', 1), lk(T(188), 'table_top')))],
      c=K((T(188), 960, 700, 1, None, 1.2), (E(188), 960, 640, 1, 'in', 1.7)))
    PH(T(189), dict(screen='thread', count=3, typing=1.0, bg='table'), c=Z(1.1, 0.03), sfx=[(T(189) + 0.2, 'phone_buzz', -16, 0, 'close')])
    S(T(190), 'kitchen', 'dinner', st=DIN, night=True,
      ppl=[EV('window_out', lock(T(190)), check=False), P('mom', 'mom_chair', id='mom', expr='mom_tired', act=_A(lambda a, s: a.hold_prop('fork', 1), lk(T(190), 'table_top')))],
      c=Z(1.9, 0.02, 960, 650))
    BU(T(191), 'evie', 'kitchen', 'dinner', st=DIN, night=True, cx=960, cy=580, scale=1.0, expr='evie_flat', act=_A(lock(T(191))), c=BZ(0.04))
    S(T(192), 'kitchen', 'dinner', st=DIN, night=False,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_watchful',
             act=_A(lambda a, s: a.hold_prop('fork', 1, -1e9, WD(192, 'fork') + 0.6), lambda a, s: a.set_down(WD(192, 'fork') - 0.2, 'fork', 1, scr(s.sp, 'table_top', 80, 30))))],
      c=Z(1.5, 0.02, 960, 760), sfx=[(WD(192, 'fork') + 0.35, 'fork_down', -14, 0, 'inside')])
    BU(T(193), 'mom', 'kitchen', 'dinner', st=DIN, night=False, cx=940, cy=600, scale=1.0, expr='mom_watchful', light=KITCH, c=BZ(0.02))
    BU(T(194), 'adam', 'kitchen', 'tiles', st=DIN, night=False, cx=1000, cy=600, scale=1.0, turn=-0.3, expr='adam_guarded', light=PHONE,
       act=_A(lk(T(194), (1000, 1300))), c=BZ(0.02))
    S(T(195), 'kitchen', 'wide', st=DIN, night=False,
      ppl=[P('lina', 'lina_chair', id='lina', expr='lina_grin', act=_A(lambda a, s: a.hold_prop('lina_drawing', 1),
                                                                         lambda a, s: a.reach_to(T(195) + 0.3, 1, (a.x0 + 0.42 * a.height, a.y0 - 0.6 * a.height), dur=0.7, prop='lina_drawing'))),
           AD('adam_chair', lk(T(195), ('lina', 'head')), expr='adam_guarded')], c=Z(1.25, 0.02, 1040, 800))
    BU(W(196, 'went'), 'lina', 'kitchen', 'tiles', st=DIN, night=False, cx=960, cy=640, scale=1.1, expr='lina_earnest', light=KITCH,
       act=_A(lk(W(196, 'went'), (1500, 500))), c=BZ(0.02))
    PH(T(197), lambda u: dict(screen='type', draft="You're my only friend.", draft_k=clamp(u / 1.6), bg='bed'), c=Z(1.2, 0.02),
       sfx=[(T(197) + 0.1, 'phone_tap', -22, 0, 'close', {'n': 14})])
    BU(T(198), 'adam_night', 'room', 'bed', night=True, cx=960, cy=610, scale=1.05, expr='adam_ashamed', light=PHONE, c=BZ(0.03))
    BU(T(199), 'adam_night', 'room', 'bed', night=True, cx=960, cy=580, scale=1.3, expr='adam_ashamed', light=PHONE, c=BZ(0.03))
    IN(T(200), 'card', dict(show=7, bg='landing'), motion=lambda u: (0.0, -900 * (1 - ease_out_cubic(clamp(u / 0.5))), 0.0, 6 * (1 - clamp(u / 0.5))),
       c=Z(1.0, 0.01), sfx=[(T(200) + 0.45, 'card_drop', -14, 0, 'inside')])
    S(T(201), 'front', 'down', st=dict(track='door', win={'adam': 1.0}), ppl=[EV('on_door', lock(T(201)))], c=Z(1.15, 0.02, 880, 640))
    S(T(202), 'front', 'down', st=dict(track='door', win={'adam': 1.0}), ppl=[EV('on_door', lock(T(201)))], c=Z(1.9, 0.02, 770, 600))
    S(T(203), 'room', 'door', night=True, c=Z(1.1, 0.02, 850, 640), sfx=[(T(203) + 0.25, 'knock_door', -12, 0, 'inside', {'n': 3})])
    BU(T(204), 'adam_night', 'room', 'door', night=True, cx=980, cy=620, scale=1.0, turn=-0.3, expr='adam_guarded', act=_A(lk(T(204), (300, 640))), c=BZ(0.02))
    BU(T(205), 'lina', 'hall', 'landing', st=dict(landing=0.5), night=True, cx=960, cy=620, scale=1.05, turn=0.2, expr='lina_earnest', light=BULB, c=BZ(0.02))
    S(T(206), 'room', 'window', st=dict(track='door'), night=True, c=Z(1.0, 0.02))
    S(T(207), 'front', 'down', st=dict(track='door', win={'adam': 1.0}), stage='r5',
      ppl=[EV('on_door', lock(T(207)), lambda a, s: a.neck_up(WD(207, 'bending'), 3.2, 2.8 * a.height, dx=-0.15 * a.height, grow=0.2))],
      c=K((T(207), 850, 650, 1, None, 1.2), (E(208), 830, 470, 1, 'in_out', 1.7)), cut=None)
    BU(T(209), 'evie', 'front', 'down', st=dict(track='door'), stage='r5', cx=960, cy=600, scale=1.2, expr='evie_flat', act=_A(lock(T(209))),
       c=BZ(0.05), hit=[WD(209, 'ears')])


# ---------------------------------------------------------------- rule 6 (210..238)
def plan_rule6(F):
    RULE(T(210), 6)
    L18 = [WD(218, w_) for w_ in ('o', 'n', 'l', 'y')]
    flap = lambda t: clamp((t - WD(214, 'lift') + 0.1) / 0.3)
    S(T(213), 'hall', 'landing', st=dict(landing=0.0, hall=0.0), night=True, c=Z(1.0, 0.015))
    S(T(214), 'hall', 'landing', st=dict(landing=0.0, hall=0.0, flap=flap), night=True, c=K((T(214), 960, 560, 1, None, 1.3), (E(214), 975, 560, 1, 'in', 2.6)),
      sfx=[(WD(214, 'lift'), 'letterbox_flap', -12, 0, 'inside')], evie='near')
    FG = dict(t_in=WD(215, 'fingers') - 0.2)
    for i0, view, c in ((215, 'floor', Z(1.0, 0.03)), (217, 'halfway', Z(1.15, 0.02, 880, 780)), (218, 'floor', Z(1.1, 0.03, 960, 600))):
        S(T(i0), 'hall', view, st=dict(landing=0.0, flap=1.0), night=True, evie='near',
          acts=fingers_acts('ONLY', L18, FG['t_in'], t_out=T(219) - 0.5, smile=(T(219), E(226) + 1, 1.0), stub=WD(225, 'dropped')), c=c)
    S(T(219), 'hall', 'floor', st=dict(landing=0.0, flap=1.0), night=True, evie='near',
      acts=fingers_acts('ONLY', L18, FG['t_in'], t_out=T(219) - 0.5, smile=(T(219) - 0.2, E(226) + 1, 1.0), stub=WD(225, 'dropped')),
      c=dict(mv='push', on='letterbox', f=2.6, rate=0.02, free=True))
    BU(T(223), 'adam_night', 'hall', 'landing', st=dict(landing=0.0), night=True, cx=960, cy=620, scale=1.05, expr='adam_scared', light=NIGHT_L, c=BZ(0.03))
    S(T(224), 'hall', 'floor', st=dict(landing=0.0, flap=1.0), night=True, evie='near',
      acts=fingers_acts('ONLY', L18, FG['t_in'], t_out=T(219) - 0.5, smile=(T(219) - 0.2, E(226) + 1, 0.6), stub=WD(225, 'dropped')),
      c=dict(mv='push', on='letterbox', f=3.0, rate=0.02, free=True))
    S(T(225), 'hall', 'halfway', st=dict(landing=0.0, flap=1.0), night=True, evie='near',
      acts=fingers_acts('ONLY', L18, FG['t_in'], t_out=T(219) - 0.5, stub=WD(225, 'dropped')), c=Z(1.2, 0.02, 820, 800))
    S(T(226), 'hall', 'floor', st=dict(landing=0.0, flap=1.0), night=True, evie='near',
      acts=fingers_acts('ONLY', L18, FG['t_in'], t_out=T(219) - 0.5, smile=(T(219) - 0.2, E(226) + 1, 0.3), stub=WD(225, 'dropped')),
      c=dict(mv='push', on='letterbox', f=3.4, rate=0.03, free=True))
    S(T(227), 'hall', 'up', st=dict(landing=0.0), night=True,
      ppl=[AD(None, who='adam_night', path=[(T(227), 'landing'), (WD(228, 'step'), 'step12'), (WD(230, 'halfway') + 0.3, 'step9')], surface='stairs',
              expr='adam_scared', face=(0.0, -3.0))], c=Z(1.1, 0.02, 960, 820))
    S(T(231), 'hall', 'up', st=dict(landing=dict(on=WD(231, 'clicked'))), rim=BULB, night=True,
      ppl=[AD('step9', lk(WD(231, 'clicked') + 0.2, (945, 400)), who='adam_night', expr='adam_scared', face=(0.0, 3.0))],
      c=Z(1.1, 0.02, 960, 760), sfx=[(WD(231, 'clicked'), 'light_switch', -12, 0, 'inside')])
    S(T(232), 'hall', 'up', st=dict(landing=1.0), rim=BULB, night=False,
      ppl=[P('lina', 'lina_landing', id='lina', expr='lina_earnest', face=(0.0, -3.0),
             act=_A(lambda a, s: a.hold_prop('rule_card', 1), lambda a, s: a.reach_to(W(232, 'held'), 1, (a.x0 + 0.12 * a.height, a.y0 - 0.95 * a.height), dur=0.6, prop='rule_card')))],
      c=Z(1.6, 0.02, 780, 620))
    IN(T(233), 'card', lambda u, t0=T(233): dict(show=7, bg='landing', backlit=clamp((u + t0 - WD(233, 'light')) / 1.2)), c=Z(1.0, 0.02))
    BU(T(234), 'lina', 'hall', 'up', st=dict(landing=1.0), night=False, cx=960, cy=620, scale=1.1, expr='lina_earnest', light=BULB, c=BZ(0.02))
    IN(T(235), 'card', dict(show=7, bg='landing', backlit=1.0), c=K((T(235), 700, 400, 1, None, 1.4), (WD(235, 'adam') + 0.6, 420, 220, 1, 'in', 2.7)),
       hit=[WD(235, 'adam')])
    IN(T(236), 'card', dict(show=7, bg='landing', backlit=1.0), c=Z(1.0, 0.02))
    IN(T(237), 'card', dict(show=7, bg='landing', backlit=1.0), c=Z(1.5, 0.03, 1000, 620))
    BU(T(238), 'adam_night', 'hall', 'halfway', st=dict(landing=1.0), night=False, cx=960, cy=600, scale=1.3, expr='adam_ashamed', light=BULB, c=BZ(0.04))


# ---------------------------------------------------------------- rule 7 and the climax (239..301)
def plan_rule7(F):
    RULE(T(239), 7)
    KM = [WD(257, 'm'), WD(257, 'e')]
    S(T(245), 'hall', 'kitchen', st=dict(kitchen=1.0, chalk=[dict(text='ONLY', x=0.8, y=0.6, h=0.3, reader=(0.5, 0.2))]), night=False,
      ppl=[AD(None, who='adam_night', path=[(T(245), 'door_in'), (E(246) + 0.5, 'kitchen_door')], surface='inside', expr='adam_steady')],
      c=Z(1.1, 0.02, 940, 640))
    S(T(247), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_tired', act=_A(lk(T(247) + 0.5, (1500, 700))))], c=Z(1.2, 0.02, 860, 760))
    S(T(249), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, c=Z(2.2, 0.03, 1290, 820))
    BU(T(250), 'mom', 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1, cx=960, cy=600, scale=1.0, turn=0.3, expr='mom_tired', light=KITCH, c=BZ(0.02))
    S(T(251), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_warm', act=_A(lk(T(251), ('adam', 'head')), lambda a, s: a.listen_tilt(T(251) + 0.4, None, 1, 14.0))),
           AD('adam_chair', lk(T(251), ('mom', 'head')), who='adam_night', expr='adam_ashamed')], c=Z(1.2, 0.02, 1060, 780))
    S(T(252), 'play', 'square', st=dict(tod='sunset', square='adam'), rim=SUNSET, era='memory', c=Z(1.3, 0.04, 960, 520))
    IN(T(253), 'locker', dict(dust=1.0), c=Z(1.6, 0.04, 960, 640), era='memory')
    PH(T(254), dict(screen='type', draft='•' * 8, draft_k=1.0, bg='table'), c=Z(1.2, 0.04), era='memory')
    BU(T(255), 'evie', 'school', 'corridor', stage='r3', cx=960, cy=600, scale=1.15, expr='evie_hold', act=_A(lock(T(255))), c=BZ(0.05), era='memory')
    S(T(256), 'hall', 'door', st=dict(kitchen=1.0, flap=lambda t: 0.5 + 0.5 * math.sin(max(0.0, t - WD(256, 'rattled')) * 40) * math.exp(-max(0.0, t - WD(256, 'rattled')) * 3)),
      night=True, evie='near', c=Z(1.4, 0.03, 900, 660), sfx=[(WD(256, 'rattled'), 'letterbox_rattle', -10, 0, 'inside')])
    S(T(257), 'hall', 'door', st=dict(kitchen=1.0, flap=1.0), night=True, evie='near',
      acts=fingers_acts('ME', KM, T(257) - 0.6, key=(0.3, 1.3, 0.25, 1.9, 0.0), axis='v', box=(0.2, 0.08, 0.8, 0.92)), c=Z(1.15, 0.02, 900, 760))
    BU(T(258), 'mom', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, knuck=1, cx=940, cy=600, scale=1.0, turn=0.3, expr='mom_warm', light=KITCH, c=BZ(0.02))
    S(T(259), 'kitchen', 'tiles', st=dict(kitchen=1.0, chalk=[dict(text='ME', x=1.4, y=6.2, h=0.3, u=lambda t: clamp((t - T(259)) / 2.4))]), night=False, knuck=1,
      evie='near', ppl=[P('mom', 'mom_chair', id='mom', expr='mom_firm', act=_A(lk(T(259) + 0.5, (900, 560))))], c=Z(1.2, 0.03, 960, 500))
    S(T(260), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1, era='memory',
      ppl=[P('mom', 'stand_mom', id='mom', expr='mom_tired', act=_A(lambda a, s: a.phone_to_ear(T(260) - 0.5)))], c=Z(1.5, 0.02, 760, 700))
    S(T(262), 'front', 'wide', st=dict(tod='dawn', track='half', track_rub=lambda t: clamp((t - T(262)) / 3.0), bucket=True), rim=DAWN, era='memory', knuck=1,
      ppl=[P('mom', 'on_half', id='mom', kind='kneel', expr='mom_tired', act=_A(lambda a, s: a.scrub(T(262), E(263) + 1, scr(s.sp, 'on_half', 0, 6))))],
      c=Z(1.6, 0.02, 1100, 760))
    S(T(264), 'school', 'office', era='memory', ppl=[P('rahman', 'her_chair', id='rahman', expr='rahman_calm', act=_A(lambda a, s: a.phone_to_ear(T(264) - 0.5)))],
      c=Z(1.4, 0.02, 1150, 820))
    S(T(265), 'room', 'door', st=dict(strip=1.0, shadow=1.0), night=True, era='memory', c=Z(1.3, 0.02, 850, 720))
    S(T(266), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_warm', act=_A(lk(T(266), ('adam', 'head')), nodf(W(266, 'let')))),
           AD('adam_chair', lk(T(266), ('mom', 'head')), who='adam_night', expr='adam_steady')], c=Z(1.2, 0.02, 1060, 780))
    pings = [b['t'] for b in load_beats() if b.get('line') == 267]
    PH(T(267), lambda u, t0=T(267): dict(screen='actions', tap=step_fn([(W(267, 'saved'), 'save'), (W(268, 'one') + 0.6, 'block'), (E(268) - 0.4, 'report')], None)(u + t0),
                                          done=('save',) if u + t0 > W(267, 'saved') + 0.4 else (), bg='kitchen'), c=Z(1.1, 0.02),
       sfx=[(W(267, 'saved') + 0.1, 'phone_tap', -16, 0, 'close'), (W(268, 'one') + 0.7, 'phone_tap', -16, 0, 'close'), (E(268) - 0.3, 'phone_tap', -16, 0, 'close')])
    DM = [(True, m_) for m_ in ST.OM_EVIE_MSGS] + [(False, "Please stop. You're scaring me.")]
    PH(T(269), dict(screen='thread', who='danny', mine=True, msgs=DM, bg='kitchen'), motion=lambda u: (0.0, -260 * ease_in_out(clamp(u / 2.0)), 0.0, 0.0), c=Z(1.0, 0.02))
    PH(T(272), dict(screen='thread', who='danny', mine=True, msgs=DM, bg='kitchen'), c=Z(1.4, 0.03, 960, 520))
    PH(T(275), dict(screen='thread', who='danny', mine=True, msgs=DM, count=47, bg='kitchen'), c=Z(1.2, 0.03, 960, 420))
    PH(T(278), dict(screen='thread', who='danny', mine=True, msgs=DM, bg='kitchen'), c=K((T(278), 960, 600, 1, None, 1.2), (E(279), 960, 760, 1, 'in', 1.8)))
    # the truth: the cold open's blue door replayed, rewinding
    RW = dict(post_fn=rewind_fx(T(280)), hud=rew_stamp(T(280)), tape_v='rewind')
    S(T(280), 'front', 'down', st=dict(house='danny', track='foot', win={'up': 0.0}), chalk=1.0,
      ppl=[AD('on_foot', lk(T(280), (960, -400)), expr='kind_smile', sil=0.55, sil_rim='#c8d4ff')], c=Z(1.15, 0.02, 950, 660), **RW)
    S(T(281), 'front', 'down', st=dict(house='danny', track='foot', win={'up': 0.0}), chalk=1.0, post_fn=rewind_fx(T(281) - 1.4), tape_v='rewind',
      ppl=[AD('on_foot', lk(T(281), (960, -400)), expr='kind_smile', sil=0.2)], c=Z(1.5, 0.02, 1050, 700))
    BU(T(283), 'adam', 'front', 'down', st=dict(house='danny', track='foot'), chalk=1.0, night=True, cx=960, cy=520, scale=0.8, expr='kind_smile', light=NIGHT,
       act=_A(lk(T(283), (960, -300))), c=K((T(283), 960, 760, 1, None, 1.3), (W(284, 'smiling'), 960, 560, 1, 'in_out', 1.15)), tape_v='rewind')
    BU(T(285), 'adam', 'front', 'down', st=dict(house='danny', track='foot'), chalk=1.0, night=True, cx=960, cy=600, scale=1.35, expr='kind_smile', light=NIGHT,
       act=_A(lk(T(285), (960, -300))), c=BZ(0.04), hit=[WD(285, 'me')])
    S(T(286), 'front', 'facade', st=dict(house='danny', track='foot', win=lit_win(WD(287, 'woke')), mom=True), c=Z(1.4, 0.02, 1040, 380))
    S(T(288), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False, knuck=1,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_firm', act=_A(lk(T(288), ('adam', 'head')))),
           AD('adam_chair', lk(T(288), 'table_top'), who='adam_night', expr='adam_ashamed')], c=Z(1.2, 0.02, 1060, 780))
    BU(T(289), 'mom', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, knuck=1, cx=940, cy=600, scale=1.0, turn=0.3, expr='mom_warm', light=KITCH, c=BZ(0.02))
    # the door: from inside the hall past Mom's and Adam's backs, the frame cropping her
    DOOR = lambda t0: dict(fdoor=80.0 if t0 < 0 else 0.0, kitchen=1.0, porch=1.0, hall=1.0)     # (a live fdoor f(t) leaves the shut door drawn)
    MAT = (0.8, -0.25, 0.02)
    MO = dict(order_at=(0.8, 0.06, 0.25))
    S(T(290), 'hall', 'door', st=DOOR(1), night=True, night_k=0.4,
      ppl=[P('mom', 'mom_door', id='mom', expr='mom_firm', face=(0.8, -1.0), act=_A(lambda a, s: a.reach_to(W(290, 'opened') - 0.4, -1, scr(s.sp, 'letterbox', -60, 120), dur=0.5))),
           AD('adam_door', who='adam_night', expr='adam_steady', face=(0.8, -1.0))],
      c=Z(1.05, 0.015, 900, 640))
    S(W(290, 'stood'), 'hall', 'door', st=DOOR(-9), night=True, night_k=0.4,
      ppl=[P('mom', 'mom_door', id='mom', expr='mom_firm', face=(0.8, -1.0)), AD('adam_door', who='adam_night', expr='adam_steady', face=(0.8, -1.0)),
           EV(MAT, lock(W(290, 'stood')), face=(0.8, 1.0), **MO)],
      c=Z(1.1, 0.015, 900, 640), sfx=[(W(290, 'stood') - 0.3, 'door_open', -12, 0, 'inside')])
    S(T(291), 'hall', 'door', st=DOOR(-9), night=True, night_k=0.4,
      ppl=[P('mom', 'mom_door', id='mom', expr='mom_firm', face=(0.8, -1.0)), AD('adam_door', who='adam_night', expr='adam_steady', face=(0.8, -1.0)),
           EV(MAT, lock(T(291)), face=(0.8, 1.0), **MO)], c=Z(1.5, 0.02, 900, 620))
    BU(T(292), 'mom', 'hall', 'door', st=DOOR(-9), night=False, cx=900, cy=600, scale=1.0, turn=-0.35, expr='mom_firm', light=PORCH, act=_A(lk(T(292), (1600, 560))), c=BZ(0.02))
    BU(T(293), 'evie', 'front', 'down', st=dict(track='mat', porch=1.0), stage='r7', night_k=0.4, cx=960, cy=600, scale=1.1, expr='evie_hold', light=PORCH,
       act=_A(lk(T(293), (500, 600))), c=BZ(0.02))
    BU(T(294), 'evie', 'front', 'down', st=dict(track='mat', porch=1.0), stage='r7', night_k=0.4, cx=960, cy=600, scale=1.2, expr='evie_hope', light=PORCH,
       act=_A(lk(T(294), (600, 640)), tiltf(T(294), 10)), c=BZ(0.03))
    BU(T(295), 'adam_night', 'hall', 'door', st=DOOR(-9), night=False, cx=980, cy=610, scale=1.0, turn=0.35, expr='adam_steady', light=PORCH, c=BZ(0.02))
    BU(T(297), 'adam_night', 'hall', 'door', st=DOOR(-9), night=False, cx=980, cy=600, scale=1.1, turn=0.3, expr='kind_smile', light=PORCH, c=BZ(0.02))
    BU(T(298), 'mom', 'hall', 'door', st=DOOR(-9), night=False, cx=900, cy=600, scale=1.0, turn=-0.35, expr='mom_firm', light=PORCH, c=BZ(0.02))
    S(T(299), 'hall', 'door', st=DOOR(-9), night=True, night_k=0.4,
      ppl=[P('mom', 'mom_door', id='mom', expr='mom_firm', face=(0.8, -1.0)), AD('adam_door', who='adam_night', expr='adam_steady', face=(0.8, -1.0)),
           EV(MAT, lock(T(299)), face=(0.8, 1.0), **MO)], c=Z(1.6, 0.02, 900, 620))
    BU(T(300), 'evie', 'front', 'down', st=dict(track='mat', porch=1.0), stage='drain', night_k=0.4, cx=960, cy=600, scale=1.2, expr='evie_hope', light=PORCH,
       act=_A(lock(T(300))), c=BZ(0.03))
    S(T(301), 'hall', 'door', st=DOOR(-9), night=True, night_k=0.4,
      ppl=[P('mom', 'mom_door', id='mom', expr='mom_firm', face=(0.8, -1.0)), AD('adam_door', who='adam_night', expr='adam_steady', face=(0.8, -1.0)),
           EV(MAT, lock(T(301)), lambda a, s: a.drain_away(T(301) + 0.2, 1.6, 2.8, wind=1.0), face=(0.8, 1.0), **MO)], c=Z(1.7, 0.02, 900, 620))


# ---------------------------------------------------------------- after (302..340)
def plan_after(F):
    S(T(302), 'front', 'wide', st=dict(tod='dawn', track='half', track_rub=lambda t: clamp((t - T(302)) / 4.0), bucket=True), rim=DAWN, knuck=1,
      ppl=[P('mom', 'on_half', id='mom', kind='kneel', expr='mom_warm', act=_A(lambda a, s: a.scrub(T(302), E(305) + 1, scr(s.sp, 'on_half', 0, 6)))),
           AD('on_foot', lambda a, s: a.scrub(T(302) + 0.4, E(305) + 1, scr(s.sp, 'on_foot', 0, 6)), kind='kneel', expr='adam_steady')],
      c=Z(1.3, 0.02, 1050, 790))
    S(T(303), 'hall', 'floor', st=dict(hall=1.0, chalk=[dict(text='ONLY', x=0.5, y=0.45, h=0.3, rub=lambda t: clamp((t - T(303)) / 2.0))]), night=False, c=Z(1.0, 0.02))
    S(T(304), 'front', 'step', st=dict(tod='dawn', bucket=True), rim=DAWN,
      ppl=[P('lina', 'on_step', id='lina', kind='kneel', expr='lina_sing', act=_A(lambda a, s: a.scrub(T(304), E(305) + 1, scr(s.sp, 'step', 0, 6), amp=10),
                                                                                  lambda a, s: a.sing_sway(T(305), E(305))))], c=Z(1.3, 0.02, 960, 560))
    BU(W(305, 'go'), 'lina', 'front', 'step', st=dict(tod='dawn'), night=False, cx=960, cy=620, scale=1.1, expr='lina_sing', light=DAWN,
       act=_A(lambda a, s: a.sing_sway(W(305, 'go'), E(305))), c=BZ(0.02))
    S(T(306), 'school', 'office', ppl=[P('rahman', 'her_chair', id='rahman', expr='rahman_kind', act=_A(lk(T(306), ('adam', 'head')))),
                                       AD('visitor', lk(T(306), ('rahman', 'head')), expr='adam_ashamed')], c=Z(1.2, 0.02, 1050, 820))
    BU(T(307), 'adam', 'school', 'office', cx=980, cy=610, scale=1.0, turn=0.35, expr='adam_ashamed', c=BZ(0.02))
    BU(T(308), 'rahman', 'school', 'office', cx=940, cy=600, scale=1.0, turn=-0.3, expr='rahman_kind', act=_A(nodf(W(308, 'caring'))), c=BZ(0.02))
    S(T(309), 'kitchen', 'wide', st=dict(kitchen=1.0), night=False,
      ppl=[P('mom', 'mom_chair', id='mom', expr='mom_warm', act=_A(lk(T(309), ('adam', 'hand_r')))),
           AD('adam_chair', lambda a, s: a.phone_type(T(309) + 0.3, E(310)), expr='adam_steady', talk=False)], c=Z(1.2, 0.02, 1060, 780))
    PH(T(310), lambda u: dict(screen='type', draft="Sorry. I'll give you space. You don't have to answer.", draft_k=clamp(u / 2.6), bg='table'), c=Z(1.2, 0.02))
    PH(T(311), dict(screen='thread', who='danny', mine=True, msgs=[(True, "Sorry. I'll give you space. You don't have to answer.")], bg='table'), c=Z(1.0, 0.01))
    BU(T(313), 'adam', 'kitchen', 'tiles', st=dict(kitchen=1.0), night=False, cx=760, cy=620, scale=0.95, turn=0.3, expr='adam_steady',
       busts=[dict(who='mom', cx=1250, cy=600, scale=0.9, depth=1.2, expr='mom_warm', act=lambda a, s: a.set(-9, None, 0.1, turn=-0.4))], c=BZ(0.02))
    IN(T(315), 'card', dict(show=7, bg='desk'), c=Z(1.0, 0.02))
    IN(T(316), 'shoebox', dict(dust=1.0), c=Z(1.2, 0.03))
    S(T(317), 'play', 'hop', st=dict(tod='day', square='adam'), acts=paint_layer('square_stand', T(317) + 0.3, 2.6),
      ppl=[P('caretaker', 'roller', id='caretaker', face='square_stand', act=_A(lambda a, s: a.roller(T(317), E(317) + 1, scr(s.sp, 'square_stand'))),
             extras=[lambda pen, t, a: CH.draw_roller(pen, a, t, a.height / 176.0)])], c=Z(1.8, 0.02, 965, 520))
    S(T(318), 'school', 'lunch', ppl=[AD('adam_seat', lk(T(318), ('danny', 'head')), expr='kind_smile'),
                                      P('danny', 'stand_by', id='danny', expr='danny_shy', face='adam_seat'),
                                      P('kofi', 'opp_l', id='kofi', act=_A(lk(T(318), ('danny', 'head')))), P('sam', 'opp_r', id='sam', expr='kind_smile')],
      c=Z(1.6, 0.02, 1040, 720))
    BU(T(320), 'danny', 'school', 'lunch', cx=960, cy=610, scale=1.0, turn=-0.35, expr='danny_shy', c=BZ(0.02))
    BU(T(321), 'adam', 'school', 'lunch', cx=980, cy=610, scale=1.0, turn=0.35, expr='kind_smile', c=BZ(0.02))
    IN(T(322), 'shoebox', dict(dust=0.0), motion=lambda u: (-500 * (1 - ease_out_cubic(clamp(u / 0.9))), 0.0, 0.0, 0.0), c=Z(1.0, 0.02),
       sfx=[(T(322) + 0.1, 'box_slide', -16, 0, 'inside')])
    IN(T(324), 'shoebox', dict(dust=0.0), c=Z(1.8, 0.03, 960, 520))
    S(T(325), 'school', 'lunch_table', ppl=[P('danny', 'opp_seat', id='danny', expr='danny_kind'), P('kofi', 'opp_l', id='kofi', expr='kind_smile'),
                                            P('sam', 'opp_r', id='sam', expr='kind_smile')], c=Z(1.1, 0.02, 925, 760))
    IN(T(326), 'card', dict(show=7, bg='school'), c=K((T(326), 960, 540, 1, None, 1.0), (E(327), 420, 220, 1, 'in_out', 2.5)))
    BU(W(327, 'chewed'), 'danny', 'school', 'lunch', cx=900, cy=600, scale=1.15, turn=-0.55, expr='danny_kind', c=BZ(0.02))
    BU(T(328), 'danny', 'school', 'lunch', cx=960, cy=610, scale=1.0, turn=-0.3, expr='danny_kind', c=BZ(0.02))
    S(T(329), 'school', 'lunch', ppl=[AD('adam_seat', lk(T(329), ('danny', 'head')), expr='kind_smile'),
                                      P('danny', 'beside_l', id='danny', expr='kind_smile', act=_A(lk(T(329), ('adam', 'head')))),
                                      P('kofi', 'opp_l', id='kofi', expr='kind_smile'), P('sam', 'opp_r', id='sam', expr='kind_smile')],
      c=Z(1.4, 0.015, 1000, 720))
    # the coda: grown Adam's hands only
    GH = lambda fn: [dict(who='adam_grown', fn=fn, size=330, shape='grip', side=1, sleeve_from=(1500, 1400))]
    PH(T(331), dict(screen='thread', who='danny', mine=True, msgs=[(True, 'Lunch Saturday?')], bg='table'), era='coda',
       hands=GH(lambda t: (1240, 820, -40, 1.0)), c=Z(1.0, 0.02))
    PH(T(332), dict(screen='thread', who='danny', mine=True, msgs=[(True, 'Lunch Saturday?')], bg='table'), era='coda',
       hands=GH(lambda t: (1220, 800, -40, 1.0)), c=Z(1.7, 0.03, 1150, 760))
    PH(T(334), dict(screen='dark', lit=0.0, bg='table'), era='coda', motion=lambda u: (0.0, 0.0, -0.03 * clamp(u / 0.6), 0.0),
       hands=GH(lambda t, t0=T(334): (1240, 820 + 300 * clamp((t - t0 - 0.5) / 0.6), -40, 1.0 - clamp((t - t0 - 0.5) / 0.6))), c=Z(1.0, 0.01),
       sfx=[(T(334) + 0.3, 'phone_face_down', -14, 0, 'close')])
    S(T(335), 'front', 'step', st=dict(tod='day', track='step', text='ONLY'), era='coda', c=Z(1.2, 0.02, 960, 540))
    S(T(336), 'front', 'step', st=dict(tod='day', track='step', text='ONLY'), era='coda', c=Z(2.0, 0.02, 960, 540), hit=[WD(336, 'only')])
    S(T(337), 'front', 'step', st=dict(tod='day', track='step', text='ONLY', track_rub=lambda t: clamp((t - T(337)) / 2.0), bucket=True), era='coda',
      c=Z(1.5, 0.02, 960, 560), sfx=[(T(337) + 0.2, 'brush_scrub', -16, 0, 'outside', {'dur': 2.0})])
    PH(T(338), dict(screen='thread', who='danny', mine=True, msgs=[(True, 'Calling Danny...'), (False, 'Hey! Good to hear you.')], bg='table'), era='coda',
       hands=GH(lambda t: (1240, 820, -40, 1.0)), c=Z(1.05, 0.02))


# ---------------------------------------------------------------- the outro (341..382)
def plan_outro(F):
    S(T(341), 'room', 'wide', st=dict(lamp=lambda t: clamp((t - WD(343, 'light')) / 0.15)), night=True, c=Z(1.0, 0.01),
      sfx=[(WD(343, 'light'), 'light_switch', -14, 0, 'inside')], era='outro')
    S(T(344), 'play', 'square', st=dict(tod='day', square='painted', paint=1.0), c=Z(1.0, 0.02), era='outro')
    S(T(345), 'play', 'wide', st=dict(tod='day', square='painted', paint=1.0), c=Z(1.0, 0.01), era='outro')
    CARD(T(346), 'The monster is made up.\nThe warning signs are real.', line_t={1: T(347) - 0.1}, chalk=True, era='outro')
    CHECKLIST(T(348))
    CARD(T(367), "You can't make anyone like you.\nAnd nobody can make you owe them.", line_t={1: T(368) - 0.1}, chalk=True, size=64, era='outro')
    PROMPT(T(369), 'return')
    CARD(T(376), 'Leave a like for Danny.', icon='thumb', icon_t=T(376) + 0.4, y=620, era='outro',
         sfx=[(T(376) + 0.45, 'ui_pop', -12, 0, 'close')])
    CARD(T(377), 'On Night Policy, you can leave whenever you want.\nThat\'s how you know we\'re real friends.', icon='sub', icon_t=T(377) + 0.2,
         line_t={0: T(378) - 0.1, 1: T(379) - 0.1}, y=640, size=48, era='outro', sfx=[(T(377) + 0.25, 'ui_pop', -12, 0, 'close')])
    S(T(380), 'front', 'wide', st=dict(porch=1.0), c=Z(1.0, 0.012), era='outro')


def plan(F):
    CH.evie_arc_from_lines([dict(text=l['en'], t=l['t']) for l in F.L])     # EVIE_ARC from the timeline, once
    plan_trailer(F); plan_hook(F); plan_setup(F); plan_rule1(F); plan_rule2(F); plan_rule3(F); plan_rule4(F)
    plan_rule5(F); plan_rule6(F); plan_rule7(F); plan_after(F); plan_outro(F)
    plan_globals(F)


def plan_globals(F):
    """On-screen sounds the shots do not carry themselves (the mix reads them with the shots' own)."""
    g = F.globals
    for b in load_beats():
        if b['kind'] == 'ping':
            g.append(_ev(b['t'] + 0.02, 'phone_screen_light', -26, 0, 'close', beat=True))
    g.append(_ev(T(17) + 0.2, 'swing_creak', -24, 0, 'tape', dur=round(E(20) - T(17), 2)))
    g.append(_ev(WD(225, 'dropped'), 'letterbox_flap', -16, 0, 'inside'))
    clank = ([b['t'] for b in load_beats() if b['kind'] == 'clank'] or [E(176) + 0.3])[0]
    g.append(_ev(clank + 0.05, 'floodlight_on', -14, 0, 'outside', dur=round(E(179) - clank, 2)))     # the hum under the white light
    g.append(_ev(T(316) + 0.1, 'drawer_open', -16, 0, 'inside'))
    g.append(_ev(W(323, 'every') + 0.05, 'shoebox_lid', -16, 0, 'inside'))
    for t_ in (T(76) + 0.2, T(262) + 0.4, T(302) + 0.6):
        g.append(_ev(t_, 'bucket_slosh', -20, 0, 'outside'))


BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}


def contact(F, out_dir=None, per=48, cols=8, tw=320, th=180, rng=None):
    """Contact sheets of every shot: the mid frame, the shot index / time / kind and the line being read under each
    (pages of `per` shots -> W/shots/contact_NN.jpg, and all pages stacked -> W/shots/contact_all.jpg)."""
    import cv2
    out_dir = out_dir or TESTS
    os.makedirs(out_dir, exist_ok=True)
    shots = F.shots[rng[0]:rng[1]] if rng else F.shots
    tiles = []
    for s in shots:
        tm = s.t0 + 0.5 * s.d
        img = cv2.resize(F.frame(tm, int(round(tm * FPS))), (tw, th), interpolation=cv2.INTER_AREA)
        lab = np.zeros((44, tw, 3), np.uint8)
        l = F.line_at(tm)
        txt = _clean(l['en']) if l else ''
        cv2.putText(lab, '%d  %.1fs  %s %s' % (s.idx, s.t0, s.kind, s.p.get('view') or s.p.get('name') or s.p.get('who') or ''), (4, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 220, 120), 1, cv2.LINE_AA)
        for j, ln in enumerate(_wrap_txt(txt, 52)[:2]):
            cv2.putText(lab, ln, (4, 28 + 13 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (235, 235, 235), 1, cv2.LINE_AA)
        tiles.append(np.vstack([img, lab]))
    pages, paths = [], []
    for k in range(0, len(tiles), per):
        rows = []
        chunk = tiles[k:k + per]
        for r in range(0, len(chunk), cols):
            row = chunk[r:r + cols]
            while len(row) < cols: row.append(np.zeros_like(tiles[0]))
            rows.append(np.hstack(row))
        page = np.vstack(rows); pages.append(page)
        pth = os.path.join(out_dir, 'contact_%02d.jpg' % (k // per))
        cv2.imwrite(pth, cv2.cvtColor(page, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 82]); paths.append(pth)
    if pages:
        allp = os.path.join(out_dir, 'contact_all.jpg')
        w_ = max(p_.shape[1] for p_ in pages)
        cv2.imwrite(allp, cv2.cvtColor(np.vstack([np.pad(p_, ((0, 0), (0, w_ - p_.shape[1]), (0, 0))) for p_ in pages]), cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 80]); paths.append(allp)
    return paths


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--timeline', default=os.path.join(ALIGN, 'timeline.json'))
    ap.add_argument('--cues', action='store_true')
    ap.add_argument('--out', default=None, help='cue sheet dir (default W/cues)')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--sheet', default=None, help='review sheets (first | mid | last frame + the lines) -> PREFIX_NNN.jpg')
    ap.add_argument('--per', type=int, default=8)
    ap.add_argument('--tile', type=int, default=320)
    ap.add_argument('--range', nargs=2, type=int, default=None)
    ap.add_argument('--size', default='960x540')
    ap.add_argument('--bench', type=int, default=0, help='N shots x 4 frames at --size (use 2560x1440), one process')
    ap.add_argument('--shots', default=None, help='comma-separated shot indices for --bench')
    ap.add_argument('--consec', type=int, default=0, help='--bench: N consecutive samples (every 3rd frame) per shot')
    ap.add_argument('--threads', type=int, default=None)
    ap.add_argument('--frames', default=None, help='cut pairs (last | first frame) over magenta -> PREFIX_NN.jpg + PREFIX_holes.json')
    ap.add_argument('--lipcheck', action='store_true')
    ap.add_argument('--still', default=None, help='comma-separated times -> W/shots/still_T.jpg')
    ap.add_argument('--contact', action='store_true', help='contact sheets of every shot -> W/shots/contact_*.jpg')
    a = ap.parse_args()
    if a.threads is not None:
        import cv2; cv2.setNumThreads(a.threads)
    W_, H_ = (int(v) for v in a.size.split('x'))
    set_render_size(W_, H_)
    t_ = time.time()
    F = Film(json.load(open(a.timeline)))
    print('%d shots built in %.1fs' % (len(F.shots), time.time() - t_))
    if a.list:
        for s in F.shots: print('%3d %7.2f %5.2f %-6s %s' % (s.idx, s.t0, s.d, s.kind, s.p.get('room') or s.p.get('name') or s.p.get('who') or s.p.get('mode') or ''))
        ds = np.array([s.d for s in F.shots])
        print('shots %d  median %.2f  p10 %.2f  p90 %.2f  min %.2f  max %.2f  cuts/min %.1f' % (len(ds), np.median(ds), np.percentile(ds, 10),
                                                                                            np.percentile(ds, 90), ds.min(), ds.max(), len(ds) / F.duration * 60))
    if a.cues:
        sfx, mus = F.cues(a.out)
        print('sfx %d, music events %d -> %s' % (len(sfx), len(mus['events']), a.out or CUES_DIR))
    if a.still:
        import cv2
        os.makedirs(TESTS, exist_ok=True)
        for s_ in a.still.split(','):
            tt = float(s_)
            img = F.frame(tt, int(round(tt * FPS)))
            pth = os.path.join(TESTS, 'still_%07.2f.jpg' % tt)
            cv2.imwrite(pth, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(pth)
    if a.bench:
        idx = [int(v) for v in a.shots.split(',')] if a.shots else np.linspace(0, len(F.shots) - 1, a.bench).round().astype(int)
        rows = []
        for k in idx:
            s_ = F.shots[k]
            for j in range(a.consec or 4):
                tt = (s_.t0 + min(s_.d - 0.02, 0.4 + j * 3.0 / FPS)) if a.consec else (s_.t0 + min(s_.d - 0.02, 0.1 + j * max(0.05, (s_.d - 0.2) / 3)))
                t1_ = time.perf_counter(); F.frame(tt, int(tt * FPS)); rows.append((s_.kind, j, time.perf_counter() - t1_, k))
        tot = np.mean([r[2] for r in rows]); steady = np.mean([r[2] for r in rows if r[1] > 0])
        kinds = sorted(set(r[0] for r in rows))
        res = {'size': a.size, 'frames': len(rows), 'mean_s': round(float(tot), 3), 'steady_mean_s': round(float(steady), 3),
               'max_s': round(float(max(r[2] for r in rows)), 3),
               'by_kind': {k_: round(float(np.mean([r[2] for r in rows if r[0] == k_])), 3) for k_ in kinds},
               'by_shot': {str(k_): round(float(np.mean([r[2] for r in rows if r[3] == k_ and r[1] > 0])), 3) for k_ in sorted(set(r[3] for r in rows))}}
        print(json.dumps(res))
        os.makedirs(TESTS, exist_ok=True)
        out = os.path.join(TESTS, ('speed_shots_%s.json' if a.shots else 'speed_%s.json') % a.size)
        json.dump(res, open(out, 'w'), indent=1); print(out)
    if a.frames:
        paths, holes = cut_frames(F, a.frames, rng=a.range)
        print(paths); print('holes:', len(holes), holes[:30])
    if a.lipcheck:
        rows = lip_check(F)
        os.makedirs(TESTS, exist_ok=True)
        json.dump(rows, open(os.path.join(TESTS, 'lipcheck.json'), 'w'), indent=0)
        bad = [r for r in rows if r['move_off'] > 0.35 or (r['lines'] and r['move_on'] < 0.4)]
        for r in bad: print('CHECK', r)
        print('lipcheck: %d actor-shots, %d flagged -> %s' % (len(rows), len(bad), os.path.join(TESTS, 'lipcheck.json')))
    if a.contact:
        print(contact(F, rng=a.range))
    if a.sheet:
        print(shot_sheets(F, a.sheet, rng=a.range, per=a.per, tile=a.tile))


