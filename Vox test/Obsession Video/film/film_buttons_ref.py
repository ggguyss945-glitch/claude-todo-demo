"""film.py: the shot list, editor and cue sheets for "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET"
(Night Policy).

Built in the machinery of the Walls film (film_walls_ref.py: the Film class, plan(), the shot builders, BUILDERS,
captions, header, cue sheets) on this film's cast (characters.py + characters_buttons.py) and sets (sets.py +
sets_buttons.py: our block, the apartment, the school lane and the narrator's home now, each on a plan in metres). EVERY
time in the plan is keyed to timeline.json (line starts / ends and per-line word times): there is no absolute time
anywhere, so a re-edit of the narration moves the picture with its lines.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + TAIL)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json + beats_cues.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --still T,T

THE OWNER'S NOTES, MADE INTO CODE:
  * Every figure in a set shot stands on a plan point of the set (an anchor or (x, y, Y)): height from the px-per-metre
    there, draw order from sp.order_at(), light from sp.light_kw(); seats / lying from the anchor's kind. tools/validate.py
    checks floors, ground lines, furniture, overlaps, reach, props, cut positions and the STATE table at 8 fps.
  * Prefer cuts; the camera only pushes a little while people act. Show exactly what each line says.
  * THE BLANK is active in every beat she is in: she waves (at the wrong window), presses her palms to the glass, tilts
    toward sounds, swaps Mom's package, drives Mom's car and stretches her arm out of the open window, types from Mom's
    account, appears in front of Mom's door, closes in inside the microwave door while Mom looks down, grows, sets the
    lamp swinging, sings at the window, unfolds beside the fridge, wraps the coat, lunges at the marker's squeak. She is
    blind; she moves only while nobody who loves him is looking. Kid-safe: her fingers always stop short of him.
  * Continuity (STATE, applied to every actor by escalate()): Owen fades (FADE: cool, a little translucent, always
    readable) as the secrets pile up and comes back "like a photo developing"; the headset lady goes pencil grey (PGREY)
    from rule five until he says "Mom"; the Brave List's ink (INK) goes pale rule by rule and comes back as he writes.
    Owen in pyjamas at night, the green coat outdoors; Mom's glare hides her green eyes until she takes the glasses off.
  * Lip sync on character lines only (VOICE: the timeline's `who`); the narrator (the grown-up Owen) is only drawn from
    behind and by his hands in the present day (narrator_b) and moves no mouth. Captions come out clean (no markup).

Shot kinds (builders B_<kind>):
  set    a set view (sets_buttons bt_* builders) with figures on the plan: room 'apt' | 'owen' | 'street' | 'lobby' |
         'school' | 'now'; view = the builder's view (or cam = a custom camera on the plan); set = builder kwargs;
         ppl = [P(who, at, ...)]; acts; mirror = figures reflected in the microwave door
  bust   a face close-up over the blurred set (bg=(room, view) + set=dict(..))
  ins    a prop insert: sets_buttons bt_insert(name, kw, motion); kw = dict or f(time since the cut); hands=[..]; layers
  chat   the tablet screen (sets_buttons bt_chat): msgs, show, head, typing, name, draft, account, banner, theme
  rule   the Brave List inside Owen's closet door: list=True the whole list (hl n), else rule n big, its words appearing
         as they are read; the ink of broken rules stays pale (INK)
  prompt the comment prompt ("Buttons, or Mom?": stage 'ask' L78-L80, 'return' L371-L377)
  list   the outro checklist (L350-L368), every item legible while it is read
  card   plain text cards (the outro)
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
TESTS = os.path.join(W, 'tests', 'film')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
BEATS = os.path.join(ALIGN, 'beats.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
TAIL = 4.0                       # the end card holds after the last line
TITLE = "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET"
BASE = 'If_Your_Moms_Eyes_Turn_Into_Buttons'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card
PART_B = 212                       # tools/validate.py --part: A = lines 0..211 (.. rule five), B = 212..
def set_retime(lines, duration): return None


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (the timeline's `who`). The narrator (the grown-up Owen) never moves a mouth on screen.
_VB = [('blank', None)]
VOICE = {'owen': [('owen', None)], 'owen_pj': [('owen', None)], 'owen_coat': [('owen', None)], 'mom': [('mom', None)],
         'blank1': _VB, 'blank1_shades': _VB, 'blank2': _VB, 'blank3': _VB, 'dunn': [('dunn', None)], 'mensah': [('mensah', None)],
         'son': [('son', None)], 'narrator_b': []}
KIDS = ('owen', 'owen_pj', 'owen_coat', 'son')
OWENS = ('owen', 'owen_pj', 'owen_coat')
BLANKS = ('blank1', 'blank1_shades', 'blank2', 'blank3')
# ---------------------------------------------------------------- the header corner (day / time), keyed to lines
CORNER = [(0, 'FRIDAY   12:00 AM'), (7, 'AGE 8'), (10, 'AGE 11'), (12, 'NOW'), (14, 'MY BIRTHDAY WEEK'), (25, 'MONDAY'),
          (31, 'YEARS AGO'), (33, 'MONDAY'), (34, 'MONDAY NIGHT'), (78, ''), (81, 'TUESDAY'), (93, 'TUESDAY NIGHT'),
          (96, 'WEDNESDAY   3:00 AM'), (108, 'WEDNESDAY'), (143, 'WEDNESDAY NIGHT'), (147, 'THURSDAY   2:00 AM'),
          (172, 'THURSDAY'), (185, 'THURSDAY DINNER'), (208, 'THURSDAY NIGHT'), (212, 'THURSDAY   11:58 PM'),
          (235, 'FRIDAY   12:00 AM'), (317, '25 YEARS LATER'), (340, '')]


def clock_str(t):
    F = _FILM[0]
    lab = ''
    for i, s in CORNER:
        if i < len(F.L) and t >= F.t(i) - LEAD: lab = s
    return lab


def header(cv, right, corner, alpha=255):
    """The header with this film's left label."""
    left = 'THE BRAVE LIST'
    w = text(cv, left, 44, 42, 600, 13, '#8c8c98', 120 * alpha / 255, 0.24, 'left')
    text(cv, '/   ' + right, 44 + w + 16, 42, 600, 13, '#c4c4ce', 150 * alpha / 255, 0.24, 'left')
    text(cv, corner, DW - 44, 42, 600, 13, '#8c8c98', 100 * alpha / 255, 0.24, 'right')


# ==================================================================================================== light on figures
NIGHT = dict(rim='#8fa6e8', rim_a=80, side=1, key=-0.22)                   # moonlight through the windows
NIGHT_L = dict(rim='#8fa6e8', rim_a=80, side=-1, key=-0.22)
NL = dict(rim='#ffc884', rim_a=90, side=-1, key=-0.3)                      # the hall / kitchen nightlight (warm, low)
NL_R = dict(rim='#ffc884', rim_a=90, side=1, key=-0.3)
DAY = dict(rim='#fff0c8', rim_a=60, side=1, key=0.12)                      # August day
DAY_L = dict(rim='#fff0c8', rim_a=60, side=-1, key=0.12)
LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.06)                    # a lamp on at night
LAMP_R = dict(rim='#ffcf8f', rim_a=60, side=1, key=0.06)
MORNING = dict(rim='#fff0c8', rim_a=60, side=1, key=0.16)
PHONE = dict(rim='#dfeaff', rim_a=90, side=1, key=-0.3)                    # a phone screen in the dark
ATTIC = dict(rim='#ffd870', rim_a=150, side=1, key=-0.35)                  # the thin yellow line from below
SLIT = dict(rim='#ffe2a8', rim_a=140, side=-1, key=-0.38)                  # light through a crack in the plaster
DARK = dict(rim='#8fa6e8', rim_a=45, side=1, key=-0.45)


def POLICE(t):
    """Red / blue bars through the window (the light pulses with the cruisers' sweep)."""
    u = 0.5 + 0.5 * math.sin(t * 5.2)
    return dict(rim='#5a8cff' if u > 0.5 else '#ff4a5a', rim_a=int(90 + 70 * abs(u - 0.5) * 2), side=1, key=-0.25)

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
        sh.sfx, sh.music, sh.actors = [], [], []
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
    if who == 'blank3' and abs(s0.Y - ST.BT_UP) < 0.05:     # review 1 B1: form 3 is floor to CEILING at her own plan point
        h0 = max(0.8 * h0, s0.y - v.p(s0.X, s0.Y + ST.BT_CEIL, s0.Yp)[1])
    a = CH.Acting(who, seed=q.get('seed', 0) + k * 11 + sh.idx * 3, height=h0, expr=q.get('expr', 'neutral'), blink=q.get('blink'))
    a.place(s0.x, s0.y + q.get('dy', 0.0))
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
        if torch or path:
            a.x0, a.y0, a.height = float(x), float(y), float(hh)
        P_ = m(t)
        if torch and torch.get('behind'):
            beam(pen, t, hh)
        if sil:
            CH.draw_silhouette(pen, who, x, y, hh, P_, t=t, colr=q.get('sil_c', '#04060c'), a=sil, rim=q.get('sil_rim', '#9fb6ff'),
                               rim_a=q.get('sil_rim_a', 0.5), rim_side=q.get('sil_side', 1), eyes=q.get('sil_eyes', 0.0))
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
    sp = ST.bt_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
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
ROOMS = {'apt': 'bt_apt', 'owen': 'bt_owen', 'street': 'bt_street', 'lobby': 'bt_lobby', 'school': 'bt_school', 'now': 'bt_now'}
_PRE = {'apt': 'bt_apt_', 'owen': 'bt_owen_', 'street': 'bt_ext_', 'lobby': 'bt_lobby_', 'school': 'bt_sch_', 'now': 'bt_now_'}
ROOM_RIM = {'apt': NIGHT, 'owen': NIGHT, 'street': NIGHT, 'lobby': NIGHT, 'school': DAY, 'now': NIGHT}
ALIAS = {'owen': OWENS, 'blank': BLANKS}
SPACE = {'apt': 'inside', 'owen': 'inside', 'street': 'outside', 'lobby': 'inside', 'school': 'outside', 'now': 'inside'}
DAYK = ('day', 'morning', 'evening')
SLEEVE.update({'owen': ('#5d7fb0', '#3f5c88'), 'owen_pj': ('#9ab4d8', '#7890b4'), 'owen_coat': ('#4f8a52', '#3a6a3c'),
               'mom': ('#d9caa9', '#ae9d7c'), 'narrator_b': ('#4a4e58', '#363a44'), 'son': ('#2f8a7a', '#226a5c'),
               'blank1': ('#d9caa9', '#ae9d7c'), 'blank2': ('#d9caa9', '#ae9d7c')})


def shot_space(s):
    if s.kind in ('rule', 'black', 'card', 'list', 'prompt'): return None
    if s.kind in ('ins', 'chat'): return 'close'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return {'street': 'outside', 'school': 'outside'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('memory', 'outro'): return s.p['era']
    if s.kind in ('rule', 'card', 'black', 'prompt', 'list', 'chat'): return s.kind
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    return {'street': 'outside', 'school': 'school', 'now': 'now', 'lobby': 'outside'}.get(room, 'home')


def _ramp(t, t0, t1):
    return ease_in_out(clamp((t - t0) / max(1e-3, t1 - t0)))


def FADE(t):
    """Owen rubbed out of his family's sight (pose.faded 0..1: cool, slightly translucent, always readable): one step per
    secret kept (the photo, the coat, half a secret, the nod, "Only you."), then back "like a photo developing" (L281-282)."""
    F = _FILM[0]
    v = 0.0
    for t0, lv in ((F.w(60, 'send'), 0.18), (F.t(89), 0.3), (F.t(144), 0.42), (F.t(170), 0.55), (F.t(203), 0.78)):
        v = lerp(v, lv, _ramp(t, t0, t0 + 1.2))
    return v * (1.0 - _ramp(t, F.t(281) - 0.2, F.e(282) + 0.3))


def PGREY(t):
    """The headset lady in Owen's sight: a little grey after rule two (L94), pencil grey from L205, colour back as he says
    "Mom" (L232)."""
    F = _FILM[0]
    v = 0.3 * _ramp(t, F.t(94), F.e(95)) + 0.7 * _ramp(t, F.t(205), F.e(205))
    return v * (1.0 - _ramp(t, F.w(232, 'mom'), F.w(232, 'mom') + 1.1))


def INK(t):
    """The Brave List's blue ink per rule (1 blue .. 0 pale): R1 after the photo (L61), R2 after the coat (L93), R4 after
    the nod (L171), every line but rule three after "Only you." (L204); in R7 it comes back line by line as he writes on
    the fridge board (L271: six; L280: seven, one, two, four, five)."""
    F = _FILM[0]
    ink = [1.0] * 7
    for n, i in ((1, 61), (2, 93), (4, 171), (5, 204), (6, 204), (7, 204)):
        ink[n - 1] = 1.0 - _ramp(t, F.t(i) + 0.3, F.e(i))
    back = {6: (WD(271, 'mom'), WD(271, 'here') + 0.4), 7: (WD(280, 'chat'), WD(280, 'chat') + 0.5),
            1: (WD(280, 'photo'), WD(280, 'photo') + 0.5), 2: (WD(280, 'coat'), WD(280, 'coat') + 0.5),
            4: (WD(280, 'two'), WD(280, 'two') + 0.5), 5: (WD(280, 'wished'), WD(280, 'mom') + 0.4)}
    for n, (a, b) in back.items():
        ink[n - 1] = max(ink[n - 1], _ramp(t, a, b))
    return ink


KID_ARC = [(0, 0.6), (5, 0.2), (14, 0.0), (34, 0.2), (45, 0.5), (49, 0.3), (62, 0.6), (70, 0.9), (75, 0.5), (96, 0.7), (103, 0.9),
           (108, 0.2), (117, 0.4), (125, 0.9), (131, 0.8), (137, 0.3), (150, 0.4), (157, 0.9), (163, 0.6), (172, 0.6), (182, 1.0),
           (185, 0.4), (189, 0.8), (205, 0.7), (212, 0.5), (222, 0.8), (231, 0.6), (237, 1.0), (256, 0.6), (284, 0.2), (297, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    pts = [(F.t(i), v) for i, v in arc if i < len(F.L)]
    return float(np.interp(t, [p_[0] for p_ in pts], [p_[1] for p_ in pts]))


def escalate(a, sh, who):
    """The STATE of every actor at every frame (keyed to lines): Owen's fade, the headset lady's grey, Mom's headset and
    glasses (off from L276 / L277), the Blank's never-blinking eyes, and the kids' tension (wider eyes, faster breath)."""
    if sh.kind in ('rule', 'card', 'black', 'prompt', 'list'): return
    p = sh.p
    F = _FILM[0]
    if who in OWENS:
        fd = p.get('fade')
        if fd is None and p.get('era') == 'memory': fd = 0.0
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, (lambda P_, t, fd=fd: P_.__dict__.__setitem__('faded', FADE(t) if fd is None else (fd(t) if callable(fd) else fd))),
               real=True, late=True)
    if who == 'mom':
        pg = p.get('pgrey')
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, (lambda P_, t, pg=pg: P_.__dict__.__setitem__('pgrey', PGREY(t) if pg is None else pg)), real=True, late=True)
        if (sh.t0 >= F.t(276) + 0.3 and not p.get('own_off')) or p.get('era') == 'memory' or p.get('hs_off'):
            a.set(-1e9, None, 0.0, hs_off=1.0)
        if sh.t0 >= F.t(277) + 0.3 and not p.get('own_off') and not p.get('specs_on'):
            a.set(-1e9, None, 0.0, specs=0.0)
    if who in KIDS and p.get('era') != 'memory':
        k = _arc(KID_ARC, sh.t0) if who != 'son' else 0.2
        if k > 0.02:
            def fn(P_, t, k=k):
                P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
                per = 3.9 - 1.5 * k
                P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
            a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)


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


def _header_text(self, t):
    cur = 'INTRODUCTION'
    for t0, n in self.rules:
        if t >= t0: cur = 'RULE %d OF 7' % n
    for i, s in ((78, 'ONE WORD'), (81, None), (297, 'AFTER'), (317, 'NOW'), (340, 'THE TRUTH'), (350, 'THE REAL LIST'), (371, 'YOUR WORD'), (378, CHANNEL)):
        if i < len(self.L) and t >= self.t(i) - LEAD:
            cur = s if s else 'RULE 2 OF 7'
    return cur


def _clean(s):
    """Caption text comes out clean: no markup characters ever reach the screen."""
    import re
    return re.sub(r'[\*_\[\]\{\}<>#`~|]', '', s).replace('  ', ' ').strip()


def _overlay(self, cv, t, sh):
    if sh.kind == 'black' and not sh.p.get('caption'): return
    if sh.kind != 'black': header(cv, self.header_text(t), clock_str(t))
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


# ==================================================================================================== B_set extras
def _mirror_setup(F, sh, sp, figs, holder):
    """Figures seen in the black microwave door: each at its plan point reflected across the door plane (ST.bt_mirror),
    facing the mirrored way, drawn with reflection=True (Owen's pose.refl_hide 1 = gone from the glass). q: who, at=(x, y),
    face=(dx, dy), kind 'stand' | 'seat' (seat_Y), tall, expr, act, alpha=f(t) (a figure that is there or gone), id."""
    v = sp.view
    acts = []
    for k, q in enumerate(figs):
        x, y = q['at']
        sx, sy, ppm, dep = ST.bt_mirror(v, x, ST.BT_UP, y)
        h = CH.height_px(q['who'], ppm, tall=q.get('tall', 0.0))
        a = CH.Acting(q['who'], seed=31 + k * 5 + sh.idx * 3, height=h, expr=q.get('expr', 'neutral'), blink=q.get('blink'))
        a.place(sx, sy)
        fd = q.get('face', (1.0, 0.0))
        a.face(v.turn_for(2 * ST.BT_MX - x, y, -fd[0], fd[1]))
        if q.get('kind') == 'seat':
            a.seated(ST.bt_mirror(v, x, ST.BT_UP + q.get('seat_Y', 0.46), y)[1], hands=q.get('hands', 'lap'))
        escalate(a, sh, q['who'])
        if q.get('act'): q['act'](a, sh)
        a._mirror = True
        sh.actors.append(a)
        if getattr(sh, 'A', None) is not None: sh.A['refl_' + q.get('id', q['who'])] = a
        acts.append((dep, a, q))
    acts.sort(key=lambda r: -r[0])
    lt = dict(rim='#bcd4ff', rim_a=60, side=1, key=-0.25)

    def draw(pen, t, clip):
        for dep, a, q in acts:
            al = q.get('alpha', 1.0)
            al = al(t) if callable(al) else al
            if al <= 0.01: continue
            if al < 0.99: pen.cv.saveLayer(None, skia.Paint(Alphaf=float(al)))
            CH.draw(pen, q['who'], a.x0, a.y0, a.height, a.at(t), t=t, light=lt, reflection=True)
            if al < 0.99: pen.cv.restore()
    holder['f'] = draw


_B_set0 = B_set


def B_set(F, sh):
    p = sh.p
    if p.get('room') == 'apt' and (p.get('view') == 'fridge' and not p.get('cam') or p.get('cam_cull')):
        p.setdefault('cull', FRIDGE_CULL)
    if p.get('room') == 'school' and p.get('view') in ('dunn', 'back'):
        p.setdefault('cull', ('snowfall',))
    if p.get('mirror'):
        holder = {}
        p['set'] = dict(p.get('set', {}), refl=lambda pen, t, clip, h=holder: h['f'](pen, t, clip) if 'f' in h else None)
        spec = _B_set0(F, sh)
        _mirror_setup(F, sh, sh.sp, p['mirror'], holder)
        return spec
    return _B_set0(F, sh)


def lay_at(sh, who, dorder, draw, name):
    """A layer drawn at actor `who`'s depth, just in front of (dorder < 0) or behind (> 0) that figure's own layer."""
    L = sh.I[who]['layer']
    o = L.order
    lay = Layer(L.depth, draw, name, ref_depth=L.ref_depth if hasattr(L, 'ref_depth') else L.depth)
    lay.order = (lambda t, o=o: _val(o, t) + dorder) if callable(o) else o + dorder
    return lay


def _val(o, t): return o(t) if callable(o) else o


def coat_acts(owen='owen', blank='blank', held=None, wrap=None, btn=None, full=None, opn=None, top=None, top_to=None, drop=None, ext=None,
              empty=None, top_t0=None):
    """The red coat in the climax (acts for a set shot): held(t) -> (cx, cy, h) where her hands hold it open; wrap = (t0, t1):
    from held to on his shoulders (CH.coat_on); btn(t) buttons closed 0..6 (the top one never); full(t) 0..1 (somebody in
    it); opn(t) how open; top(t) 0..1 the top button held out (top_to = his hand); drop = t: he dropped out (the coat stays
    in her hands, empty). Worn: back behind him, front over him. She holds it by its shoulders (b3_hold_coat)."""
    def acts(A, sh, sp):
        o = A[owen]
        def coat(t):
            h0 = held(t)
            if wrap is None: return h0
            on = CH.coat_on(o, min(t, drop if drop is not None else 1e9))
            k = ease_in_out(clamp((t - wrap[0]) / max(0.1, wrap[1] - wrap[0])))
            if drop is not None and t > drop:
                if empty is not None:                       # review 1 B2: she keeps the EMPTY coat (drawn back to her side)
                    h0 = empty(t); k = k * (1.0 - ease_in_out(clamp((t - drop - 0.35) / 1.3)))
                else:
                    k = k * (1.0 - ease_in_out(clamp((t - drop) / 0.9)) * 0.35)
            return lerp(h0[0], on[0], k), lerp(h0[1], on[1], k), lerp(h0[2], on[2], k)
        worn = (lambda t: wrap is not None and wrap[0] + 0.6 * (wrap[1] - wrap[0]) <= t < (drop if drop is not None else 1e9) + 0.3)
        tt = top_to or (lambda t: o.where(t, 'hand_r'))

        def args(t):
            cx, cy, h = coat(t)
            return dict(cx=cx, cy=cy, h=h, buttons=btn(t) if btn else 0.0, open_=opn(t) if opn else 1.0, full=full(t) if full else 0.0,
                        top_out=top(t) if top else 0.0, top_to=tt(t))
        def d_all(pen, t):
            if worn(t): return
            a_ = args(t); CH.draw_red_coat(pen, a_['cx'], a_['cy'], a_['h'], a_['buttons'], a_['open_'], a_['full'], top_out=a_['top_out'], top_to=a_['top_to'])
        def d_back(pen, t):
            if not worn(t): return
            a_ = args(t); CH.draw_red_coat(pen, a_['cx'], a_['cy'], a_['h'], a_['buttons'], a_['open_'], a_['full'], part='back')
        def d_front(pen, t):
            if not worn(t): return
            a_ = args(t); CH.draw_red_coat(pen, a_['cx'], a_['cy'], a_['h'], a_['buttons'], a_['open_'], a_['full'], part='front', top_out=a_['top_out'], top_to=a_['top_to'])
        def top_btn(t):                                     # where the top button is drawn (held out toward top_to)
            cx, cy, h = coat(t); bx, by = cx + 0.03 * h, cy + 0.16 * h
            k_ = ease_in_out(clamp(top(t) if top else 0.0)) * 0.85
            if k_ <= 0: return bx, by
            tx, ty = tt(t); return bx + (tx - bx) * k_, by + (ty - by) * k_
        if blank in A:
            def seam(sd):
                def g(t):
                    cx, cy, h = coat(t); q = CH.coat_pts(cx, cy, h)
                    l_, r_ = q['shoulder_l'], q['shoulder_r']
                    p_ = l_ if l_[0] < r_[0] else r_            # both hands LOW on HER side of the coat: never near his face or neck
                    pt = (p_[0] - 0.02 * h, p_[1] + 0.3 * h) if sd > 0 else (p_[0] + 0.01 * h, p_[1] + 0.62 * h)
                    if drop is not None and t > drop - 1.2:              # before he drops: up to the coat's outer shoulder (his head goes DOWN)
                        u0 = ease_in_out(clamp((t - drop + 1.2) / 0.9)); pt = (lerp(pt[0], p_[0] - 0.05 * h, u0), lerp(pt[1], p_[1] + 0.03 * h, u0))
                    if sd < 0 and drop is not None and t > drop:          # after the drop the far hand holds the empty coat's shoulder
                        u_ = ease_in_out(clamp((t - drop) / 0.8)); pt = (lerp(pt[0], p_[0], u_), lerp(pt[1], p_[1] + 0.02 * h, u_))
                    return pt
                return g
            near_t1 = (drop + 0.3) if drop is not None else None
            A[blank].b3_hand(-1e9, 1, seam(1), near_t1, 0.6)
            A[blank].b3_hand(-1e9, -1, seam(-1), None, 0.6)
            if top_t0 is not None:                          # "She held it out to me": her fingertips pinch the top corner, an inch off him
                A[blank].b3_hand(top_t0, 1, lambda t: (lambda b_: (b_[0] - 0.08 * coat(t)[2], b_[1] - 0.03 * coat(t)[2]))(top_btn(t)), (drop - 1.3) if drop else None, 1.2)
        sh._coat = coat
        sh._top_btn = top_btn
        return [lay_at(sh, blank if blank in sh.I else owen, -0.02, d_all, 'coat_held'), lay_at(sh, owen, 0.015, d_back, 'coat_back'),
                lay_at(sh, owen, -0.015, d_front, 'coat_front')]
    return acts


def arm_acts(owen='owen', ext=None, at='car_window'):
    """The car arm (R3): out of the OPEN driver window toward Owen's hood, bending where arms don't bend, fingers tapping;
    it stops 3 cm short (CH.draw_long_arm); ext(t) 0..1 (back to 0 folds it in)."""
    def acts(A, sh, sp):
        s_ = spot_of(sp, at)
        o = A[owen]
        def draw(pen, t):
            e = ext(t)
            if e <= 0.005: return
            h_ = o.height                                   # review 1 M4: aim at his HOOD (the shoulder on the car side), never his neck
            sl, sr = o.where(t, 'shoulder_l'), o.where(t, 'shoulder_r')
            hx, hy = min((sl, sr), key=lambda q: abs(q[0] - s_.x))
            CH.draw_long_arm(pen, (s_.x, s_.y), (hx, hy - 0.05 * h_), e, t, s_.ppm / 100.0)
        lay = Layer(s_.depth, draw, 'long_arm', ref_depth=s_.depth)
        lay.order = ST.ORDER_OUT if False else sp.info.get('orders', {}).get('car_kerb_side', s_.depth) - 0.02
        return [lay]
    return acts


def rolling_buttons(sp, frm, to, t0, dur=2.2, stop=None):
    """Two black buttons rolling across the floor from plan point frm to plan point to (stopping at Mom's slippers)."""
    a, b = spot_of(sp, frm), spot_of(sp, to)
    def draw(pen, t):
        for j, (dx, lag) in enumerate(((-0.06, 0.0), (0.05, 0.25))):
            u = ease_out_cubic(clamp((t - t0 - lag) / dur))
            if t < t0: u = 0.0
            x = lerp(a.x, b.x + dx * b.ppm, u); y = lerp(a.y, b.y, u) - 0.012 * b.ppm
            r = 0.02 * lerp(a.ppm, b.ppm, u)                         # review 1 M5: big enough to read
            ST._bt_button(pen, x, y, r)
    lay = Layer(b.depth, draw, 'buttons_roll', ref_depth=b.depth)
    lay.order = sp.order_at(b.X, b.Yp) - 0.04
    return lay


def flat_cardigan(sp, at, w_m=0.9, t_on=-1e9, notes=None):
    s_ = spot_of(sp, at)
    def draw(pen, t):
        if t < t_on: return
        CH.draw_flat_cardigan(pen, s_.x, s_.y, w_m * s_.ppm, alpha=clamp((t - t_on) / 0.2), t=t)
    lay = Layer(s_.depth, draw, 'flat_cardigan', ref_depth=s_.depth)
    lay.order = sp.order_at(s_.X, s_.Yp) + 0.02
    return lay


def drop_button(x0, y0, x1, y1, t_hit, r=46.0, c='#c84a3a', fall=0.45, box=(684, 286, 1236, 930)):
    """An insert layer: one button falling into the jar (lands at t_hit: the 'tik')."""
    def draw(pen, t):
        u = (t - (t_hit - fall)) / fall
        if u < 0: return
        if u > 1.6: return
        uu = clamp(u)
        x = lerp(x0, x1, uu); y = y0 + (y1 - y0) * uu * uu
        if u > 1.0: y = y1 - 30 * math.sin(clamp((u - 1.0) / 0.3) * math.pi) * (1 - clamp((u - 1.0) / 0.6))
        ST._bt_button(pen, x, y, r, c)

    def mk(F_, sh):
        e = ('button', x1, y1, box)
        sh._lands = [x for x in (getattr(sh, '_lands', None) or []) if x != e] + [e]      # tools/validate.py: lands in the jar
        return Layer(0.95, draw, 'drop_button', blur=0)
    return mk


# ==================================================================================================== builders: the Brave List
RULE_LINES = {1: (53, 54), 2: (82, 82), 3: (109, 110), 4: (148, 149), 5: (184, 184), 6: (213, 215), 7: (244, 245)}


def rule_write(F, n, lead=0.25):
    """write(t) 0..1 for rule n: the share of its words already read (+ a lead). Word times from the lines' own words;
    a line whose word list misses words is spread evenly."""
    i0, i1 = RULE_LINES[n]
    total = len(ST.BT_RULES[n - 1][1].split())
    ts = []
    for i in range(i0, i1 + 1):
        l = F.L[i]; nw = len(l['en'].split()); ww = l.get('words') or []
        if len(ww) == nw: ts += [w_[1] for w_ in ww]
        else: ts += [l['t'] + (l['end'] - l['t']) * j / max(1, nw) for j in range(nw)]
    ts = ts[:total] + [ts[-1]] * max(0, total - len(ts))
    return lambda t: sum(1 for x in ts if x <= t + lead) / float(total)


def B_rule(F, sh):
    """The Brave List inside Owen's closet door. list=True: the whole list (hl = the rule being read, ink = INK(t): broken
    rules stay pale, only the crayon border stays bright); else rule n big, each word appearing as it is read, in the ink
    it has now (a pale rule stays legible: at least 0.45)."""
    p = sh.p
    n = p['n']
    t0 = sh.t0
    mo = lambda t: (5.0 * math.sin((t - t0) * 0.6), 3.0 * math.sin((t - t0) * 0.45), 0.01 * clamp((t - t0) / 6.0), 0.0)
    if p.get('list'):
        sp = ST.bt_insert('brave_list', lambda t: dict(ink=INK(t), hl=p.get('hl', n)), mo, t0=0.0)
    else:
        wf = p.get('write') or rule_write(F, n)
        sp = ST.bt_insert('brave_rule', lambda t: dict(n=n, write=wf(t), ink=max(0.45, INK(t)[n - 1])), mo, t0=0.0)
    cam = scam(sh, None, dict(mv='push', rate=p.get('rate', 0.008), free=True, f=p.get('f', 1.0), x=p.get('x', 960), y=p.get('y', 540)))
    return Spec(list(sp), cam, None, 'bt_ins', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def rule_cues(F, sh):
    if sh.p.get('list'):
        sh.sfx.append(_ev(sh.t0 + 0.02, 'closet_door_creak', -12, 0, 'close'))
        sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.7})
    else:
        n = sh.p['n']; i0, i1 = RULE_LINES[n]
        sh.sfx.append(_ev(F.t(i0), 'pen_scratch', -16, 0, 'close', dur=round(F.e(i1) - F.t(i0), 2)))


def B_blist(F, sh):
    """The list as an insert inside a scene (no header change): ink = INK(t); hl."""
    p = sh.p
    t0 = sh.t0
    mo = lambda t: (4.0 * math.sin((t - t0) * 0.5), 2.0 * math.sin((t - t0) * 0.4), 0.012 * clamp((t - t0) / 5.0), 0.0)
    sp = ST.bt_insert('brave_list', lambda t: dict(ink=INK(t), hl=p.get('hl')), mo, t0=0.0)
    cam = scam(sh, None, dict(mv='push', rate=p.get('rate', 0.01), free=True, f=p.get('f', 1.0), x=p.get('x', 960), y=p.get('y', 540)))
    return Spec(list(sp), cam, None, p.get('grade', 'bt_ins_night'), 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


# ==================================================================================================== builders: the chat
def B_chat(F, sh):
    """The tablet screen, full frame (ST.bt_chat): msgs (a list or a BT_CHAT key / keys), show, head, typing, name, draft,
    draft_k, account, banner, theme (values or f(t))."""
    p = sh.p
    msgs = p.get('msgs', [])
    if isinstance(msgs, str): msgs = list(ST.BT_CHAT[msgs])
    elif msgs and isinstance(msgs[0], str): msgs = [m for k_ in msgs for m in ST.BT_CHAT[k_]]
    sp = ST.bt_chat(msgs, p.get('show'), p.get('head', 0.0), p.get('typing', 0.0), p.get('name', ''), p.get('draft', ''), p.get('draft_k', 1.0),
                    p.get('account', 'game'), p.get('banner'), p.get('theme', 'old'))
    layers = list(sp)
    for lf in p.get('layers', []): layers.append(lf(F, sh))
    c = dict(p.get('c') or dict(mv='push', rate=0.012))
    c.setdefault('free', True)
    return Spec(layers, scam(sh, None, c), None, p.get('grade', 'bt_screen'), 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


# ==================================================================================================== builders: prompt, list, cards
def _words_in(F, i):
    l = F.L[i]; ws = l['en'].split(); ww = l.get('words') or []
    if len(ww) == len(ws): return [(w_, t_) for w_, (_, t_) in zip(ws, ww)]
    return [(w_, l['t'] + (l['end'] - l['t']) * j / max(1, len(ws))) for j, w_ in enumerate(ws)]


def _say_line(cv, F, i, t, x, y, size, c='#ffffff', w=1500, weight=700, lead=0.12, dim=None):
    """Line i's caption text written as it is read (each word appears on its word), wrapped at w, centred on x."""
    ws = _words_in(F, i)
    lines, cur, cw = [], [], 0.0
    for wd, tw in ws:
        ww_ = text_width(wd + ' ', weight, size, 0.02)
        if cur and cw + ww_ > w: lines.append(cur); cur, cw = [], 0.0
        cur.append((wd, tw)); cw += ww_
    if cur: lines.append(cur)
    for j, ln in enumerate(lines):
        tot = sum(text_width(wd + ' ', weight, size, 0.02) for wd, _ in ln)
        xx = x - tot / 2
        for wd, tw in ln:
            a = clamp((t - tw + lead) / 0.18) * 255
            if dim is not None and t > dim: a *= 0.55
            if a > 1: text(cv, _clean(wd), xx, y + j * size * 1.25, weight, size, c, a, 0.02, 'left', 0.8)
            xx += text_width(wd + ' ', weight, size, 0.02)
    return len(lines)


def _chip(pen, cv, x, y, s, label, kind, a=255):
    """A big answer chip: BUTTONS (black, two four-hole buttons) or MOM (warm, a little heart)."""
    if a <= 1 or s <= 0.01: return
    w, h = 470 * s, 150 * s
    pen.fill(rrect(x - w / 2, y - h / 2, w, h, 30 * s), '#000000', 0.5 * a, blur=16)
    if kind == 'buttons':
        pen.fill(rrect(x - w / 2, y - h / 2, w, h, 30 * s), '#16161c', a); pen.line(rrect(x - w / 2, y - h / 2, w, h, 30 * s), 4, '#5a5a66', a)
        for dx in (-150, -78): ST._bt_button(pen, x + dx * s, y, 26 * s, a=a)
        text(cv, label, x + 50 * s, y + 22 * s, 900, 62 * s, '#ffffff', a, 0.06, 'center', 0.4)
    else:
        pen.fill(rrect(x - w / 2, y - h / 2, w, h, 30 * s), '#f4e6c8', a); pen.line(rrect(x - w / 2, y - h / 2, w, h, 30 * s), 4, '#c8a878', a)
        text(cv, label, x + 30 * s, y + 22 * s, 900, 62 * s, '#5a3a24', a, 0.06, 'center', 0.0)
        hx, hy = x - 140 * s, y
        pen.fill(smooth([(hx, hy + 22 * s), (hx - 26 * s, hy - 2 * s), (hx - 16 * s, hy - 22 * s), (hx, hy - 12 * s), (hx + 16 * s, hy - 22 * s), (hx + 26 * s, hy - 2 * s)], True), '#e84a5a', a)


def B_prompt(F, sh):
    """The comment prompt over Owen's dark room. stage 'ask' (L78-L80): ONE WORD, IN THE COMMENTS / the question written
    as it is read / BUTTONS or MOM chips on their words. stage 'return' (L371-L377): BUTTONS or MOM again / "one word is
    harmless" / Owen's one-sentence message / the real answer to your mom's face / a comment reply "Told her."."""
    p = sh.p
    st_ = p.get('stage', 'ask')
    sp = ST.bt_owen('wide', tod='night', tablet=0.6, tablet_bed=True)
    layers = list(sp)

    def hud(cv, t):
        pen = Pen(cv)
        u = t - sh.t0
        pen.fill(rect(0, 0, DW, 1080), '#05060c', 175 * clamp(u / 0.3))
        if st_ == 'ask':
            if t >= F.t(78) - 0.1 and t < F.t(79) - 0.1:
                _say_line(cv, F, 78, t, 960, 470, 70, '#ffffff', 1500, 800)
            if t >= F.t(79) - 0.1:
                text(cv, 'ONE WORD, IN THE COMMENTS', 960, 200, 800, 34, '#ffd890', 230, 0.18, 'center', 0.5)
                _say_line(cv, F, 79, t, 960, 380, 64, '#ffffff', 1480, 700)
            if t >= F.t(80) - 0.15:
                for (wd, kind, x) in (('buttons', 'buttons', 640), ('mom', 'mom', 1280)):
                    ta = F.w(80, wd) - 0.08
                    k = ease_out_back(clamp((t - ta) / 0.3))
                    _chip(pen, cv, x, 760, k, 'BUTTONS' if kind == 'buttons' else 'MOM', kind, 255 * clamp((t - ta) / 0.15))
                if t >= F.w(80, 'or') - 0.05: text(cv, 'or', 960, 780, 700, 48, '#c8ccd8', 220, 0.0, 'center', 0.5)
        else:
            if t < F.t(373) - 0.1:
                text(cv, 'NOW.', 960, 330, 900, 80, '#ffffff', 255 * clamp((t - F.t(371) + 0.1) / 0.2), 0.12, 'center', 0.6)
                for (wd, kind, x) in (('buttons', 'buttons', 640), ('mom', 'mom', 1280)):
                    ta = F.w(372, wd) - 0.08
                    _chip(pen, cv, x, 600, ease_out_back(clamp((t - ta) / 0.3)), 'BUTTONS' if kind == 'buttons' else 'MOM', kind, 255 * clamp((t - ta) / 0.15))
            elif t < F.t(376) - 0.1:
                _say_line(cv, F, 373, t, 960, 250, 60, '#ffd890', 1500, 800)
                _say_line(cv, F, 374, t, 960, 360, 56, '#ffffff', 1500, 700)
                if t >= F.t(375) - 0.2:
                    _say_line(cv, F, 375, t, 960, 470, 52, '#c8ccd8', 1500, 600)
                    a = 255 * clamp((t - F.w(375, 'message') + 0.1) / 0.3)
                    bw = text_width('I wish I had a different mom.', 600, 46, 0.0) + 80
                    pen.fill(rrect(960 - bw / 2, 600, bw, 96, 40), '#2f6ad8', a); text(cv, 'I wish I had a different mom.', 960, 664, 600, 46, '#ffffff', a, 0.0, 'center', 0.0)
                    text(cv, 'Owen, Monday night', 960, 750, 600, 30, '#8a92b0', a * 0.9, 0.06, 'center', 0.0)
            else:
                _say_line(cv, F, 376, t, 960, 300, 62, '#ffffff', 1500, 800)
                if t >= F.t(377) - 0.15:
                    _say_line(cv, F, 377, t, 960, 450, 50, '#c8ccd8', 1500, 600)
                    ta = F.w(377, 'told') - 0.1
                    a = 255 * clamp((t - ta) / 0.25)
                    pen.fill(rrect(560, 560, 800, 230, 24), '#1c2030', a); pen.line(rrect(560, 560, 800, 230, 24), 3, '#3a4058', a)
                    pen.fill(oval(630, 625, 30), '#4a5068', a); text(cv, 'You', 680, 618, 700, 30, '#c8ccd8', a, 0.0, 'left', 0.0)
                    text(cv, 'Mom', 680, 662, 800, 40, '#ffffff', a, 0.0, 'left', 0.0)
                    pen.line(poly([(640, 690), (640, 735), (700, 735)], False), 4, '#8a92b0', a)
                    text(cv, 'Told her.', 720, 750, 800, 46, '#ffd890', a, 0.02, 'left', 0.0)
    cam = scam(sh, sp.info.get('cam_env'), dict(mv='push', rate=0.004, free=True))
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=lambda t: dict(blur=9), hud=hud)


LIST_ITEMS = [(350, 352), (353, 355), (356, 357), (358, 359), (360, 363), (364, 368)]


def B_list(F, sh):
    """The real list (the story bible's outro checklist), six items over the kitchen in the morning: each item appears as
    it is read, the one being read bright and highlighted (its words appear on their words), a tick when read; all of it
    stays legible."""
    sp = ST.bt_apt('wide', tod='day')
    layers = list(sp)

    def hud(cv, t):
        pen = Pen(cv)
        pen.fill(rect(0, 0, DW, 1080), '#0b0c12', 178)
        text(cv, 'THE REAL LIST', 960, 128, 900, 52, '#ffd890', 245 * clamp((t - sh.t0) / 0.3), 0.18, 'center', 0.5)
        y = 200
        for k, (i0, i1) in enumerate(LIST_ITEMS):
            ta, tb = F.t(i0) - 0.15, F.e(i1)
            s = ' '.join(F.L[i]['en'] for i in range(i0, i1 + 1))
            lines = _wrap_txt(_clean(s), 64)
            hh = 47 * len(lines) + 20
            if t >= ta:
                a = clamp((t - ta) / 0.25)
                cur = ta <= t < (F.t(LIST_ITEMS[k + 1][0]) - 0.15 if k + 1 < len(LIST_ITEMS) else 1e9)
                if cur: pen.fill(rrect(230, y - 38, 1460, hh, 14), '#ffffff', 26 * a)
                box = rrect(250, y - 26, 34, 34, 6)
                pen.line(box, 3, '#ffd890', 230 * a)
                if t >= tb: pen.line(poly([(257, y - 9), (267, y + 2), (281, y - 20)], False), 5, '#7ee08a', 255 * clamp((t - tb) / 0.2))
                for j, ln in enumerate(lines):
                    text(cv, ln, 310, y + j * 47, 700 if cur else 600, 40, '#ffffff' if cur else '#c8ccd8', (255 if cur else 190) * a, 0.0, 'left', 0.5)
            y += hh
    cam = scam(sh, sp.info.get('cam_env'), dict(mv='push', rate=0.004, free=True))
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=lambda t: dict(blur=9), hud=hud)


def _thumb(pen, x, y, s, a=255):
    pen.fill(rrect(x - 70 * s, y - 10 * s, 40 * s, 110 * s, 8 * s), '#ffffff', a)
    pen.fill(smooth([(x - 22 * s, y - 10 * s), (x + 6 * s, y - 90 * s), (x + 30 * s, y - 84 * s), (x + 24 * s, y - 20 * s), (x + 80 * s, y - 16 * s),
                     (x + 76 * s, y + 92 * s), (x - 22 * s, y + 100 * s)], True), '#ffffff', a)


def B_card(F, sh):
    """Plain cards: p text (lines split by \\n), line_t {k: t} (a line appears on its word), strikes=[(t, line index)],
    sub, icon 'thumb' | 'sub' (pops at icon_t), bg (c1, c2) or bgset=(room, view, kw) blurred."""
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
            w_ = text(cv, s, 960, y0 + k * 90, 900, p.get('size', 64), '#ffffff', 240 * ak, 0.12, 'center', 0.8)
            for (ts_, kk) in p.get('strikes', []):
                if kk == k and t >= ts_:
                    L_ = (w_ + 40) * ease_out_cubic(clamp((t - ts_) / 0.35))
                    pen.fill(rrect(960 - (w_ + 40) / 2, y0 + k * 90 - 26, L_, 12, 6), '#e03a3a', 240)
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
EXPO = {'ins': -0.02, 'chat': 0.0}
NIGHT_LIFT = 0.10                    # night interiors: dark, but the action must read (bus-film lesson)


def glob_fx(F, sh, t, fx):
    """Per-frame global effects keyed to lines: cut flashes; a night lift; grain that rises through the week; the memory
    (warm, desaturated); the midnight climax (L235 .. L297): a slow cold pulse at the frame edge; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'blink' and u < 0.12: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - u / 0.12)
    ek = EXPO.get(sh.kind, 0.0)
    st = sh.p.get('set') or {}
    room = sh.p.get('room') or (sh.p.get('bg') or ['x'])[0]
    if sh.kind in ('set', 'bust') and st.get('tod', 'night') not in DAYK and room not in ('street', 'school'):
        ek += NIGHT_LIFT
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('outro',) or sh.kind in ('rule', 'black', 'card', 'prompt', 'list', 'chat')
    if era == 'memory':
        fx['sat'] = fx.get('sat', 1.0) * 0.55; fx['grain'] = max(fx.get('grain', 0.0), 0.12)
    if not clean:
        n = len(F.L)
        g = 0.04 + 0.06 * clamp((t - F.t(34)) / max(1.0, F.t(235) - F.t(34)))
        if t >= F.t(297): g = 0.04
        fx['grain'] = max(fx.get('grain', 0.0), g)
        if F.t(235) - LEAD <= t < F.t(297):
            ramp = clamp((t - F.t(235)) / 4.0) * (1.0 - clamp((t - F.t(286)) / 2.0))
            ph = ((t - F.t(235)) * 0.8) % 1.0
            beat = math.exp(-ph * 6.0)
            if 'flash' not in fx:
                fx['flash'] = _epost.Spill(0.10 * ramp * beat, side=-1.0 if sh.idx % 2 else 1.0, color=(0.55, 0.65, 1.0), reach=0.7)
            fx['sat'] = fx.get('sat', 1.0) * (1.0 - 0.10 * ramp)
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names)."""
    D = F.duration
    n = len(F.L)
    t = lambda i: F.t(min(i, n - 1))
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(0.0, t(12) - 0.1, 'apartment_night', -18, 'inside', fridge_hum=True)
    bed(t(12) - 0.1, t(14) - 0.1, 'room_tone_house', -22, 'inside')
    bed(t(14) - 0.1, t(25) - 0.1, 'apartment_day', -20, 'inside', city=True)
    bed(t(25) - 0.1, t(31) - 0.1, 'ambience_street_day', -18, 'outside')
    bed(t(31) - 0.1, t(33) - 0.1, 'room_tone_house', -24, 'inside', memory=True)
    bed(t(33) - 0.1, t(34) - 0.1, 'apartment_day', -20, 'inside')
    bed(t(34) - 0.1, t(78) - 0.1, 'apartment_night', -19, 'inside', street=True)
    bed(t(81) - 0.1, t(96) - 0.1, 'apartment_day', -20, 'inside')
    bed(t(96) - 0.1, t(108) - 0.1, 'apartment_night', -19, 'inside')
    bed(t(111) - 0.1, t(137) - 0.1, 'ambience_snow_school', -16, 'outside', kids=True)
    bed(t(137) - 0.1, t(141) - 0.1, 'ambience_snow_school', -20, 'outside')
    bed(t(141) - 0.1, t(147) - 0.1, 'apartment_night', -19, 'inside')
    bed(t(150) - 0.1, t(172) - 0.1, 'apartment_night', -18, 'inside', fridge_hum=True)
    bed(t(172) - 0.1, t(185) - 0.1, 'apartment_day', -21, 'inside')
    bed(t(185) - 0.1, t(212) - 0.1, 'apartment_night', -19, 'inside')
    bed(t(216) - 0.1, t(297) - 0.1, 'apartment_night', -18, 'inside', fridge_hum=True)
    bed(t(297) - 0.1, t(317) - 0.1, 'room_tone_house', -22, 'inside')
    bed(t(317) - 0.1, t(340) - 0.1, 'apartment_night', -20, 'inside', modern=True)
    bed(t(340) - 0.1, D, 'room_tone_house', -24, 'inside')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.6), (2, 0.8), (3, 0.95), (4, 0.5), (7, 0.3), (11, 0.7), (12, 0.3), (14, 0.15), (25, 0.2), (31, 0.15), (34, 0.4), (35, 0.6),
    (38, 0.7), (45, 0.75), (47, 0.85), (49, 0.6), (52, 0.5), (55, 0.6), (62, 0.75), (67, 0.9), (68, 0.85), (70, 0.95), (72, 1.0),
    (74, 0.7), (77, 0.85), (78, 0.3), (81, 0.5), (88, 0.7), (93, 0.5), (96, 0.75), (103, 0.9), (106, 0.95), (108, 0.5), (111, 0.4),
    (117, 0.7), (125, 0.95), (127, 1.0), (131, 0.8), (135, 0.6), (137, 0.3), (143, 0.55), (146, 0.8), (147, 0.5), (150, 0.6),
    (157, 0.85), (158, 0.95), (161, 0.9), (167, 0.85), (171, 0.6), (173, 0.75), (179, 0.9), (182, 1.0), (183, 0.5), (189, 0.8),
    (196, 0.9), (201, 0.85), (203, 0.95), (206, 0.9), (208, 0.85), (212, 0.5), (216, 0.6), (222, 0.85), (230, 0.6), (232, 0.7),
    (237, 0.95), (240, 1.0), (242, 1.0), (243, 0.6), (246, 0.9), (251, 1.0), (256, 1.0), (259, 0.9), (263, 0.7), (270, 0.8),
    (273, 0.95), (276, 0.7), (281, 0.6), (283, 0.85), (284, 0.5), (286, 0.4), (297, 0.6), (299, 0.2), (304, 0.15), (316, 0.1),
    (317, 0.25), (322, 0.45), (327, 0.7), (330, 0.8), (333, 0.4), (337, 0.6), (340, 0.15), (384, 0.1)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY if i < len(F.L)]
    pts.append([round(F.duration, 2), 0.0])
    return pts


# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(3, -0.5, 0.5), (67, -0.4, 0.5), (107, -0.4, 0.5), (126, -0.4, 0.5), (158, -0.4, 0.5), (177, -0.3, 0.4),
             (196, -0.4, 0.5), (237, -0.5, 0.6), (256, -0.4, 0.4), (294, -0.5, 0.6), (330, -0.4, 0.5)]


# ==================================================================================================== Tik / Ping beats: their causes
# beats.json (the sound team places them): what the picture shows at each one (the cue sheet carries it: beats_cues.json)
BEAT_CAUSE = {
    'loose_buttons_went': 'a loose button drops into the jar on the windowsill (insert)',
    'owen_i_wish_i': 'his message sends; the grey default head pops up in the chat',
    'two_black_buttons': 'two black four-hole buttons click onto the avatar face',
    'she_was_waving': 'the chat message "I see you." arrives on his tablet',
    'i_ducked': 'the spot under the streetlight is empty: she has moved closer',
    'she_was_at': 'her fingertips tap the lobby glass, palms flat on it',
    'empty': 'a button drops into the jar on the dark kitchen windowsill: she is closer',
    'half_a_secret': 'the chat message "Tell her about me..." arrives',
    'blank_tell_her_about': 'a button drops into the jar on the windowsill',
    'two_in_the': 'a message from Mom\'s account lights his tablet on the bed',
    'i_glanced_at': 'cut: the Blank is suddenly standing in front of Mom\'s door',
    'closer': 'in the microwave door the Blank is closer behind him',
    'the_blanks_chin': 'in the microwave door her chin is almost on his shoulder',
    'my_fingers_rose': 'his fingers rise toward the top button and stop short',
    'she_dropped_them': 'Mom drops the two black buttons into her jar, one, two',
}


def load_beats():
    try: return json.load(open(BEATS)).get('beats', [])
    except Exception: return []


_cues0 = Film.cues


def _cues(self, out_dir=None, write=True):
    """The cue sheets (sfx, music, shots) + beats_cues.json: every Tik / Ping beat with the shot on screen and its cause.
    Acting 'tik' events that are not a beat become soft fingertip taps (the beats themselves are the sound team's)."""
    sfx, music = _cues0(self, out_dir, write=False)
    bts = load_beats()
    bt_ts = [b['t'] for b in bts]
    for e in sfx:
        if e['name'] == 'tik' and not any(abs(e['t'] - b) < 0.2 for b in bt_ts): e['name'] = 'fingertip_tap'
    sfx = [e for e in sfx if not (e['name'] == 'tik' and any(abs(e['t'] - b) < 0.2 for b in bt_ts))]
    rows = []
    for b in bts:
        sh = self.shot_at(b['t'])
        cause = BEAT_CAUSE.get(b.get('tag'), '')
        rows.append(dict(b, shot=sh.idx, shot_kind=sh.kind, room=sh.p.get('room') or sh.p.get('name') or sh.p.get('who'), cause=cause))
        sfx.append(_ev(b['t'], b['kind'], -6 if b['kind'] == 'tik' else -8, 0, 'close', beat=True, cause=cause))
    sfx.sort(key=lambda e: (e['t'], e['name']))
    if write:
        out_dir = out_dir or CUES_DIR
        os.makedirs(out_dir, exist_ok=True)
        json.dump(sfx, open(os.path.join(out_dir, 'sfx_cues.json'), 'w'), indent=0)
        json.dump(music, open(os.path.join(out_dir, 'music_cues.json'), 'w'), indent=0)
        json.dump(shot_table(self), open(os.path.join(out_dir, 'shots.json'), 'w'), indent=0)
        json.dump(rows, open(os.path.join(out_dir, 'beats_cues.json'), 'w'), indent=1)
    return sfx, music


Film.cues = _cues


# ==================================================================================================== plan helpers (this film)
def MC(at, ang, d=2.4, h=1.45, lh=1.0, S=1000.0, sy=560.0):
    """A camera d metres from plan point `at` (x, y, Y) in compass direction ang (deg: 0 = +y north, 90 = +x east), the
    eye h above the floor, looking at the point lh above it (which lands at screen (960, sy))."""
    X, Yp, Y = at
    a = math.radians(ang)
    return cm((X + d * math.sin(a), Yp + d * math.cos(a), Y + h), (X, Yp, Y + lh), S, sy=sy)


U = ST.BT_UP


def AP(x, y): return (x, y, U)


def ZO(f, on, rate=0.015, **k):
    """A push framed on an anchor / plan point / '@actor' (screen point at its depth)."""
    return dict(mv='push', f=f, rate=rate, on=on, **k)


def CHAT(t, **p): _FILM[0].cut(t, 'chat', **p)
def BLIST(t, hl=None, **p): _FILM[0].cut(t, 'blist', hl=hl, **p)
def RLIST(t, n, **p): _FILM[0].cut(t, 'rule', n=n, list=True, hl=n, **p)
def RBIG(t, n, **p): _FILM[0].cut(t, 'rule', n=n, **p)
def PROMPT(t, stage): _FILM[0].cut(t, 'prompt', stage=stage)
def CHECKLIST(t): _FILM[0].cut(t, 'list')
def CARD(t, text_, **p): _FILM[0].cut(t, 'card', text=text_, **p)
def BLACK(t, **p): _FILM[0].cut(t, 'black', **p)


def pdur(i, k=0.5):
    """A time k of the way through line i."""
    F = _FILM[0]
    return F.t(i) + k * (F.e(i) - F.t(i))


def typ(t0, t1, at='laptop', side=0, dy=0.0, dx=0.0):
    """type at the laptop / keyboard: the anchor's screen point (+ an offset)"""
    return lambda a, s: a.typing(max(t0, s.t0 - 0.5), t1 if t1 is not None else s.t1 + 1.0, scr(s.sp, at, dx, dy), side)


def fing(t0, t1, side=1, toward=None): return lambda a, s: a.one_finger(t0, t1, side, toward=toward)


def nodf(t0, n=1, amp=0.16, dur=0.7):
    def f(a, s):
        def fn(P_, t):
            u = (t - t0) / dur
            if 0 <= u <= 1: P_.h_nod += amp * math.sin(u * n * math.pi) ** 2
        a._add(t0 - 0.05, t0 + dur + 0.05, fn)
    return f


def tabf(t0=-1e9, t1=None, typing_=None, side=-1, up=0.0):
    """Owen / the son holding his tablet at his chest (screen to him), the other hand tapping it (typing_ = (t0, t1))."""
    def f(a, s):
        ts = max(t0, s.t0) + 0.05
        cx, cy = a.where(ts, 'chest'); tr = a.at(ts).turn
        sg = 1.0 if tr > 0 else -1.0
        tab = (cx + sg * 0.07 * a.height * min(1.0, abs(tr)), cy + (0.07 - up) * a.height)
        a.reach_to(t0, side, tab, t1=t1, dur=0.4, z=60.0, contact='palm', shape='grip', prop='tab_back')
        a.hold_prop('tab_back', side, t0, t1)
        if typing_: a.typing(typing_[0], typing_[1], tab, side=-side)
        a.look_at(t0, tab, t1=t1, dur=0.3)
    return f


def coat_held(dx=0.15, dy=0.10, hk=0.78):
    """act: a standing figure holds the red coat open in front of her (by its shoulders); a._coat = (cx, cy, h)."""
    def f(a, s):
        cx, cy = a.where(s.t0 + 0.05, 'chest')
        a._coat = (cx + dx * a.height, cy - dy * a.height, hk * a.height * 0.55)
        q = CH.coat_pts(*a._coat)
        l_, r_ = q['shoulder_l'], q['shoulder_r']
        lo, hi = (l_, r_) if l_[0] < r_[0] else (r_, l_)
        a.reach_to(-1e9, 1, hi, dur=0.3, z=70.0, contact='palm', shape='grip', fade=0.3)
        a.reach_to(-1e9, -1, lo, dur=0.3, z=70.0, contact='palm', shape='grip', fade=0.3)
    return f


def coat2_layer(who_id, dorder=-0.02):
    """acts: the red coat held open (drawn in front of the holder: A[who_id]._coat)."""
    def acts(A, sh, sp):
        a = A[who_id]
        def d(pen, t):
            cx, cy, h = a._coat
            CH.draw_red_coat(pen, cx, cy, h, 0.0, 1.0, 0.0)
        return [lay_at(sh, who_id, dorder, d, 'coat2')]
    return acts


# set states
K_DAY = dict(tod='day', laptop=1.0, carton=True)
K_EVE = dict(tod='evening', laptop=1.0, lamp=1.0, carton=True)
K_2AM = dict(tod='night', laptop=1.0)
K_DIN = dict(tod='evening', lamp=1.0, dinner=True, laptop=1.0)
K_MID = dict(tod='night', lamp=1.0, ceil=0.6, living=1.0, laptop=0.7)
O_NIGHT = dict(tod='night', tablet=0.7, tablet_bed=False)
O_DARK = dict(tod='night', tablet=0.0)
TWO_TABLE = MC(AP(4.6, 2.35), 0, 2.7, h=1.35, lh=0.85, S=1100, sy=600)                 # the table from the north: Mom left, Owen right
MOM_TABLE = MC(AP(3.66, 2.35), 55, 2.3, h=1.3, lh=1.0, S=1250, sy=600)                # Mom at her laptop, 3/4 front
OWEN_TABLE = MC(AP(5.54, 2.35), 300, 2.2, h=1.25, lh=0.9, S=1300, sy=600)             # Owen at his end, from behind Mom's shoulder side
FRONTDOOR = MC(AP(0.55, 4.6), 120, 2.4, h=1.4, lh=1.1, S=850)                # the front door from the living room
STOOL2 = MC(AP(5.3, 2.75), 180, 2.2, h=1.45, lh=0.9, S=720)                    # the stool and Mom behind him, from the north
WINDOW_K = MC(AP(5.4, 0.55), 35, 2.6, h=1.5, lh=1.2, S=1150)                  # Mom at the kitchen window (3/4 back)
DOOR_IN = MC(AP(1.6, 3.0), 110, 2.3, h=1.45, lh=1.0, S=1100)                  # Owen coming out of his door into the living room
KIT = MC(AP(5.5, 4.2), 240, 3.3, h=1.65, lh=1.15, S=900)
MICRO_CAM = cm((6.2, 3.16, U + 1.3), (7.1, 3.0, U + 1.4), 1150)                # seated eye height into the black microwave door
NOW_POV = cm((5.85, 0.3, U + 1.4), (6.25, -3.9, 1.2), 900)                     # out of his son's window, down to the streetlight
FRIDGE_CULL = ('table', 'chair_mom', 'chair_owen', 'on_table', 'chair_n', 'stool', 'side_table')                     # the kitchen master: the fridge, the gap, the counter
ROOM_BED = MC((-0.52, 1.6, U), 300, 2.0, h=1.3, lh=0.55, S=850)              # Owen's bed (him in it), medium


def BED(t, expr, act=None, f=1.3):
    """review 1 B4: Owen LYING in his bed under the covers (never a bust turned 90 degrees)."""
    S(t, 'owen', 'bed', st=O_DARK, cam=BED_FOOT, rim=NIGHT, ppl=[P('owen_pj', 'pillow', id='owen', kind='pillow', hem='bed_hem', expr=expr, act=act)],
      c=Z(f, 0.015, 960, 560))


BED_FOOT = MC((-0.52, 0.4, U), 0, 2.1, h=1.25, lh=0.6, S=1150)               # from the foot of his bed: his head on the pillow


def plan_open(F):
    # 0 If someone online says, "Your mom doesn't even see you"... don't answer.
    CHAT(T(0), msgs='answer', show=lambda t: 0.35 + 0.65 * clamp((t - WD(0, 'your') + 0.3) / 0.5), head=0.0, typing=0.0,
         c=dict(mv='push', rate=0.02, f=1.0, x=960, y=540))
    # 1 If a present says don't tell your mom, and at three a.m. it stands up in your closet... don't keep quiet.
    IN(T(1), 'card', c=dict(mv='push', rate=0.03))
    IN(W(1, 'three'), 'coat', lambda u: dict(full=0.6 + 0.4 * clamp(u / 1.5)), c=dict(mv='push', f=1.1, rate=0.04),
       sfx=[(WD(1, 'stands'), 'cloth_rustle', -10, 0, 'close')])
    # 2 And if your mom holds your coat open at midnight, with two shiny black buttons where her eyes should be...
    S(T(2), 'apt', 'fridge', st=K_MID, fade=0.75, pgrey=0.0,
      ppl=[P('blank2', AP(5.35, 4.35), face=(0.0, -1.0), id='blank', hk=1.10, expr='too_sweet', blink=False,
             act=_A(coat_held(), lk(T(2), (960, 900))))],
      acts=coat2_layer('blank'), c=Z(2.1, 0.02, 930, 760))
    BU(W(2, 'two'), 'blank2', 'apt', 'fridge', K_MID, cx=960, cy=560, scale=1.25, expr='too_sweet', blink=False, c=BZ(0.03), light=NIGHT_L)
    # 3 "Button up, sweetheart. We're going home."
    BU(T(3), 'blank2', 'apt', 'fridge', K_MID, cx=1040, cy=600, scale=0.95, turn=-0.3, expr='too_sweet', blink=False, light=NIGHT_L,
       act=_A(lambda a, s: a.head_tilt(T(3) + 0.4, 12.0, 2.0)), c=BZ(0.02))
    # 4 ...don't.
    BU(T(4), 'owen_pj', 'apt', 'fridge', K_MID, cx=900, cy=600, scale=1.0, turn=0.3, expr='determined', fade=0.75,
       act=_A(shake_head(T(4) + 0.05, 2, 8.0, 0.6)), c=BZ(0.02))
    # 5-6 Your real mom is in the kitchen. Talking to the police.
    S(T(5), 'apt', 'couch', st=K_MID, fade=0.75, pgrey=0.0,
      ppl=[P('mom', 'couch_s', id='mom', expr='terrified_call', act=_A(lambda a, s: a.cry(T(5), None))),
           P('mensah', AP(3.3, 3.75), face=(2.35, 3.5), id='mensah', expr='calm_firm', act=_A(lambda a, s: a.take_notes(T(5) + 0.2, E(6) + 1)))],
      c=Z(1.2, 0.015, 960, 600))
    BU(T(6), 'mom', 'apt', 'couch', K_MID, cx=880, cy=620, scale=0.95, turn=0.35, expr='grief_still', pgrey=0.0,
       act=_A(lookxy(1500, 420, T(6))), c=BZ(0.02))
    # 7-9 At eight, my mom and I wrote seven rules inside my closet door. Her words in blue pen, my crayon around them. The Brave List.
    S(T(7), 'owen', 'closet', st=dict(tod='day', closet=95.0, ink=[1.0] * 7), c=Z(1.0, 0.015, 960, 520), era='memory',     # review 1 M15: the two of them writing
      ppl=[P('mom', (-2.95, 1.22, U), id='mom', kind='kneel', face=(-3.6, 1.5), expr='tender', act=_A(pose(-9, None, 0.0, hs_off=1.0),
             lambda a, s: a.reach_to(T(7) + 0.3, 1, scr(s.sp, (-3.6, 1.45, U + 1.15)), t1=None, dur=0.6, z=10, contact='grip', shape='grip'))),
           P('owen_pj', (-2.9, 1.95, U), id='owen', hk=0.82, face=(-3.6, 1.75), expr='kid_grin',
             act=_A(lambda a, s: a.reach_to(T(7) + 0.6, -1, scr(s.sp, (-3.6, 1.8, U + 1.0)), t1=None, dur=0.6, z=10, contact='grip', shape='grip')))])
    BLIST(T(8), f=1.6, x=900, y=520, rate=0.02, grade='bt_ins')
    BLIST(T(9), f=1.0, rate=0.015, grade='bt_ins')
    # 10 At eleven, I broke four of them in one week.
    BLIST(T(10), f=1.05, rate=0.01, grade='bt_ins_night',
          post_fn=None)
    # 11 By midnight on my birthday, a police officer stood in our kitchen, my mom was crying my name... and I was standing right next to her.
    S(T(11), 'apt', 'couch', st=K_MID, fade=0.78, pgrey=0.0,
      ppl=[P('mom', 'couch_s', id='mom', expr='cry', act=_A(lambda a, s: a.cry(T(11), None), lookxy(700, 420, T(11)))),
           P('mensah', AP(3.3, 3.75), face=(2.35, 3.5), id='mensah', expr='calm_firm', act=_A(lambda a, s: a.take_notes(T(11), E(11) + 1))),
           P('owen_pj', AP(2.95, 2.75), face=(2.35, 3.5), id='owen', expr='sad', act=_A(lk(W(11, 'standing'), ('mom', 'head'))))],
      c=Z(1.15, 0.02, 1000, 600))
    # 12-13 I kept the buttons. In a jar by my headset.
    IN(T(12), 'jar', dict(state='black', bg='desk'), c=dict(mv='push', f=1.2, rate=0.03, x=760, y=640))
    S(T(13), 'now', 'desk', st=dict(headset='desk', jar='black', lamp=1.0), c=Z(1.2, 0.02, 1200, 760))


def plan_setup(F):
    # 14-16 Mom worked twelve-hour help-line shifts at our kitchen table. Every caller got the same words. "Thank you for calling. I'm listening."
    S(T(14), 'apt', 'wide', st=K_DAY, rim=DAY_L, ppl=[P('mom', 'table_mom', id='mom', expr='busy', act=_A(typ(T(14), E(15) + 1)))],
      c=Z(2.0, 0.02, 1010, 700))
    S(T(15), 'apt', 'wide', st=K_DAY, cam=MOM_TABLE, rim=DAY_L, ppl=[P('mom', 'table_mom', id='mom', expr='busy', act=_A(typ(T(15), E(15) + 1), lk(T(15), 'laptop')))],
      c=Z(1.0, 0.012))
    BU(T(16), 'mom', 'apt', 'wide', K_DAY, cx=1000, cy=600, scale=0.95, turn=0.35, h_turn=0.1, expr='listening_soft', light=DAY_L,
       act=_A(lambda a, s: a.typing(T(16), E(16), (1300, 1100), 0)), c=BZ(0.015))
    # 17-20 When I talked, up went one finger. "One minute." Strangers got "I'm listening." I got one finger.
    S(T(17), 'apt', 'wide', st=K_DAY, cam=TWO_TABLE, rim=DAY_L,
      ppl=[P('mom', 'table_mom', id='mom', expr='busy', act=_A(typ(T(17), E(18) + 2, side=1), fing(W(17, 'up') - 0.1, E(18) + 1.5, side=-1), lk(T(17), 'laptop'))),
           P('owen', 'table_owen', id='owen', expr='asking', act=_A(lk(T(17), ('mom', 'head')), lambda a, s: a.point_at(T(17) + 0.2, scr(s.sp, 'laptop'), t1=W(17, 'up'), side=1)))],
      c=Z(1.05, 0.012))
    BU(T(18), 'mom', 'apt', 'wide', K_DAY, cx=960, cy=600, scale=0.9, turn=0.3, expr='busy', light=DAY_L,
       act=_A(fing(T(18) - 0.2, E(18) + 0.5, side=-1, toward=-1.0), lookxy(1300, 1000, T(18))), c=BZ(0.015))
    BU(T(19), 'mom', 'apt', 'wide', K_DAY, cx=1040, cy=620, scale=0.95, turn=0.35, expr='listening_soft', light=DAY_L, c=BZ(0.015))
    BU(T(20), 'owen', 'apt', 'wide', K_DAY, cx=900, cy=620, scale=0.95, turn=-0.35, expr='sad', light=DAY,
       act=_A(lookxy(300, 500, T(20)), lambda a, s: a.head_down(E(20) - 0.4, None, 0.5)), c=BZ(0.015))
    # 21-23 I ate with my tablet propped on the milk carton. Her glasses always caught the laptop's glare. Loose buttons went in a jar on the windowsill.
    S(T(21), 'apt', 'wide', st=K_DAY, cam=OWEN_TABLE, rim=DAY_L,
      ppl=[P('owen', 'table_owen', id='owen', expr='neutral', act=_A(lk(T(21), 'tablet_carton')))], c=Z(1.0, 0.012))
    IN(T(22), 'glasses', dict(circles=0.0), c=dict(mv='push', rate=0.025))
    IN(T(23), 'jar', dict(state='open', bg='sill_day'), c=dict(mv='push', rate=0.02, f=1.05),
       layers=[drop_button(1030, -120, 975, 520, 67.93 if False else _beat_t('loose_buttons_went', 0), c='#4a8ad8')],
       hands=[dict(who='mom', fn=lambda t, t0=T(23): (1080, 60 - 80 * clamp((t - t0 - 1.6) / 0.6), 10.0, 1.0), size=420.0, shape='pinch', side=1, sleeve_from=(1500, -500))])
    # 24 On the fridge: FRI. O'S BIRTHDAY.
    IN(T(24), 'board', dict(state='birthday', k=1.0), c=dict(mv='push', rate=0.03, f=1.3, x=960, y=330))
    # 25-30 Monday, Barlow's window: a red coat with seven black buttons. Mine flapped open. Broken zip. I pointed. Mom, on a call, just lifted her phone. She didn't even look.
    S(T(25), 'street', 'barlow', st=dict(tod='day', snow=0.2), rim=DAY,
      ppl=[P('owen_coat', 'barlow_walk', id='owen', face=(-7.3, -16.45), expr='neutral', act=_A(lk(T(25), 'coat'))),
           P('mom', 'barlow_mom', id='mom', expr='busy', act=_A(lambda a, s: a.phone_to_ear(T(25), E(28)), lookxy(600, 700, T(25))))],
      c=Z(2.2, 0.015, 930, 600))                                                    # review 1 M9: faces read at 640
    S(W(25, 'red'), 'street', 'shopwin', st=dict(tod='day'), rim=DAY, c=Z(1.0, 0.03, 1034, 577))
    BU(T(26), 'owen_coat', 'street', 'barlow', dict(tod='day'), cx=960, cy=640, scale=0.95, turn=-0.3, expr='wistful', light=DAY,
       act=_A(lookxy(1500, 400, T(26))), c=BZ(0.02))
    BU(T(27), 'owen_coat', 'street', 'barlow', dict(tod='day'), cx=980, cy=-120, scale=1.4, turn=-0.25, expr='wistful', light=DAY, c=BZ(0.025))
    S(T(28), 'street', 'barlow', st=dict(tod='day'), rim=DAY,
      ppl=[P('owen_coat', 'barlow_walk', id='owen', face=(-7.3, -16.45), expr='kid_grin', act=_A(lambda a, s: a.point_at(T(28), scr(s.sp, 'coat'), t1=E(30) + 1, side=1), lk(T(28), ('mom', 'head'), dur=0.4))),
           P('mom', 'barlow_mom', id='mom', expr='busy', act=_A(lambda a, s: a.phone_to_ear(-9.0, T(29) + 0.2)))],
      c=Z(2.7, 0.02, 930, 610))
    ts29 = pdur(29, 0.55)
    S(T(29), 'street', 'barlow', st=dict(tod='day'), rim=DAY,
      ppl=[P('mom', 'barlow_mom', id='mom', expr='busy', act=_A(lambda a, s: a.snap_photo(T(29) + 0.15, (s.A['owen'], 'head'), side=1, dur=2.2))),
           P('owen_coat', 'barlow_walk', id='owen', face=(-7.3, -16.45), expr='kid_grin', act=_A(lambda a, s: a.point_at(-9, scr(s.sp, 'coat'), t1=E(30), side=1)))],
      c=Z(3.0, 0.02, 860, 600))
    BU(T(30), 'owen_coat', 'street', 'barlow', dict(tod='day'), cx=1000, cy=620, scale=0.95, turn=-0.3, expr='sad', light=DAY,
       act=_A(lookxy(400, 560, T(30)), lambda a, s: a.head_down(E(30) - 0.5, None, 0.4)), c=BZ(0.015))
    # 31-32 When I was little, she buttoned my coat to her own song. (Mom sings)
    S(T(31), 'apt', 'living', st=dict(tod='day', living=1.0), rim=LAMP, era='memory', cam=MC(AP(0.75, 4.3), 150, 2.0, h=1.05, lh=0.6, S=1000),
      ppl=[P('mom', 'frontdoor', id='mom', kind='kneel', face=(0.95, 4.0), expr='warm_smile',
             act=_A(lambda a, s: a.reach_to(T(31) + 0.3, 1, (s.A['owen'], 'chest'), t1=E(32), dur=0.6, z=40.0, contact='tips', shape='pinch'),
                    lambda a, s: a.reach_to(T(31) + 0.4, -1, (s.A['owen'], 'chest'), t1=E(32), dur=0.6, z=40.0, contact='tips', shape='pinch'),
                    lk(T(31), ('owen', 'head')))),
           P('owen_coat', AP(0.95, 4.05), id='owen', hk=0.72, face=(0.55, 4.6), expr='kid_grin', act=_A(lk(T(31), ('mom', 'head'))))],
      c=Z(1.0, 0.015))
    BU(T(32), 'mom', 'apt', 'living', dict(tod='day', living=1.0), cx=1000, cy=600, scale=0.95, turn=-0.3, expr='warm_smile', era='memory',
       light=LAMP, hs_off=True, specs_on=True, act=_A(lookxy(560, 840, T(32))), c=BZ(0.012))
    BU(W(32, 'top'), 'owen_coat', 'apt', 'living', dict(tod='day', living=1.0), cx=920, cy=620, scale=0.9, turn=0.3, expr='kid_grin', era='memory',
       light=LAMP, act=_A(lookxy(1500, 420, W(32, 'top'))), c=BZ(0.012))
    S(W(32, 'mama'), 'apt', 'living', st=dict(tod='day', living=1.0), rim=LAMP, era='memory', cam=MC(AP(0.75, 4.3), 150, 2.0, h=1.05, lh=0.6, S=1000),
      ppl=[P('mom', 'frontdoor', id='mom', kind='kneel', face=(0.95, 4.0), expr='warm_smile',
             act=_A(lambda a, s: a.reach_to(-9, 1, (s.A['owen'], 'neck'), t1=E(32) - 0.2, dur=0.6, z=40.0, contact='tips', shape='pinch'), lk(-9, ('owen', 'head')))),
           P('owen_coat', AP(0.95, 4.05), id='owen', hk=0.72, face=(0.55, 4.6), expr='kid_grin', act=_A(lk(-9, ('mom', 'head'))))],
      c=Z(1.3, 0.02, 960, 520))
    # 33 She hadn't sung it in years.
    S(T(33), 'apt', 'wide', st=K_EVE, cam=MOM_TABLE, rim=LAMP, ppl=[P('mom', 'table_mom', id='mom', expr='exhausted', act=_A(typ(T(33), E(33) + 1), lk(T(33), 'laptop')))],
      c=Z(1.05, 0.012))


def _beat_t(tag, k=0):
    bs = [b['t'] for b in load_beats() if b.get('tag') == tag]
    return bs[k] if k < len(bs) else 0.0


def plan_chat(F):
    # 34 That night, in a game chat, I typed the worst thing I've ever typed.
    S(T(34), 'owen', 'bed', st=O_NIGHT, rim=PHONE,
      ppl=[P('owen_pj', 'bed_edge', id='owen', expr='lonely', act=_A(tabf(-9, None, (T(34) + 0.6, E(34)))))], c=Z(1.9, 0.015, 1170, 800))
    # 35 "I wish I had a different mom."
    ws = [(w_, t_) for w_, t_ in F.L[35]['words']]
    draft_k = lambda t: clamp((t - F.t(35)) / max(0.3, F.e(35) - F.t(35)))
    BU(T(35), 'owen_pj', 'owen', 'bed', O_NIGHT, cx=960, cy=600, scale=1.0, turn=0.25, expr='lonely', light=PHONE,
       act=_A(lookxy(1100, 1200, T(35))), c=BZ(0.02))
    tping = _beat_t('owen_i_wish_i')
    CHAT(pdur(35, 0.45), msgs='wish', show=lambda t: 1.0 if t >= tping - 0.25 else 0.0, draft='I wish I had a different mom.', draft_k=lambda t: 0.0 if t >= tping - 0.25 else draft_k(t),
         head=0.0, c=dict(mv='push', rate=0.015))
    # 36-38 Ping. A grey default head. No name. "Your mom doesn't even see you. I can be her. Tell me about her."
    CHAT(tping - 0.05, msgs=['wish', 'answer'], show=lambda t: 1.0 + clamp((t - WD(38, 'your') + 0.6) / 0.4), head=0.0,
         typing=lambda t: 1.0 if F.t(37) < t < WD(38, 'your') - 0.6 else 0.0, c=dict(mv='push', rate=0.02, f=1.25, x=520, y=460))
    CHAT(T(37), msgs=['wish', 'answer'], show=lambda t: 1.0 + clamp((t - WD(38, 'your') + 0.6) / 0.4), head=0.0,
         typing=lambda t: 1.0 if t < WD(38, 'your') - 0.6 else 0.0, c=dict(mv='push', rate=0.03, f=1.6, x=420, y=700))
    CHAT(T(38) - 0.3, msgs=['wish', 'answer'], show=lambda t: 1.0 + clamp((t - F.t(38) + 0.3) / 0.4), head=0.0, c=dict(mv='push', rate=0.015, f=1.05, x=960, y=500))
    # 39-44 With every word, the grey head filled in. Her messy bun. Her cardigan. Our dented car. Saturday pancakes. Our song.
    S(T(39), 'owen', 'bed', st=O_NIGHT, rim=PHONE,
      ppl=[P('owen_pj', 'bed_edge', id='owen', expr='tempted', act=_A(tabf(-9, None, (T(39), E(39)))))], c=Z(2.1, 0.02, 1180, 800))
    tells = {40: 1, 41: 2, 42: 4, 43: 5, 44: 6}
    def head_f(t):
        h = 0.0
        for i, st_ in tells.items():
            h = max(h, (st_ - 1) + clamp((t - F.t(i) - 0.1) / 0.5)) if t >= F.t(i) else h
        if t >= F.t(41) + 0.8: h = max(h, 3.0 * clamp((t - F.t(41) - 0.8) / 0.5) + 2.0 * (1 - clamp((t - F.t(41) - 0.8) / 0.5)) if t < F.t(42) else h)
        return h
    show_f = lambda t: 2.0 + sum(clamp((t - F.t(i) + 0.2) / 0.3) for i in tells)
    CHAT(T(40), msgs=['wish', 'answer', 'tell'], show=show_f, head=head_f, c=dict(mv='push', rate=0.015, f=1.2, x=560, y=560))
    CHAT(T(42), msgs=['wish', 'answer', 'tell'], show=show_f, head=head_f, c=dict(mv='push', rate=0.015, f=1.05, x=900, y=560))
    # 45-48 "What color are her eyes?" "I don't know." Two black buttons clicked onto the face. Tik. "That's okay. I'll see you for both of us."
    CHAT(T(45), msgs=['tell', 'eyes'], show=lambda t: 5.0 + clamp((t - F.t(45) + 0.3) / 0.4), head=6.0, c=dict(mv='push', rate=0.02, f=1.05, x=960, y=640))
    BU(T(46), 'owen_pj', 'owen', 'bed', O_NIGHT, cx=940, cy=600, scale=1.0, turn=0.25, expr='lonely', light=PHONE,
       act=_A(lookxy(1100, 1200, T(46)), lambda a, s: a.head_down(T(46) + 0.2, None, 0.3)), c=BZ(0.02))
    tik47 = _beat_t('two_black_buttons')
    CHAT(T(47), msgs=['tell', 'eyes'], show=6.0, head=lambda t: 6.0 + clamp((t - (tik47 - 0.15)) / 0.15), c=dict(mv='push', rate=0.035, f=1.6, x=420, y=650))
    CHAT(T(48), msgs=['tell', 'eyes', 'ok'], show=lambda t: 6.0 + clamp((t - F.t(48) + 0.3) / 0.4), head=7.0, c=dict(mv='push', rate=0.015, f=1.05, x=960, y=640))
    # 49-50 So I named her. The Blank.
    CHAT(T(49), msgs=['eyes', 'ok'], show=3.0, head=7.0, name='', c=dict(mv='push', rate=0.03, f=1.5, x=420, y=620))
    CHAT(T(50), msgs=['eyes', 'ok'], show=3.0, head=7.0, name='The Blank', c=dict(mv='push', rate=0.03, f=1.75, x=420, y=640))
    # 51 Her kind hunt one thing: a kid who feels invisible... and tells strangers instead of home.
    S(T(51), 'owen', 'wide', st=O_NIGHT, rim=PHONE,
      ppl=[P('owen_pj', 'bed_edge', id='owen', expr='lonely', act=_A(tabf(-9, None, (T(51), E(51)))))], c=Z(2.0, 0.012, 860, 760))
    S(W(51, 'tells'), 'apt', 'wide', st=dict(tod='night', laptop=1.0), cam=MOM_TABLE,
      ppl=[P('mom', 'table_mom', id='mom', expr='exhausted', act=_A(typ(-9, None), lk(-9, 'laptop')))], c=Z(1.0, 0.01))


def plan_rule1(F):
    RLIST(T(52), 1)
    RBIG(T(53), 1)
    # 55 "You're so grown-up. Send me your view, so I can picture you."
    CHAT(T(55), msgs='view', show=lambda t: clamp((t - F.t(55) + 0.3) / 0.4), head=7.0, name='The Blank', c=dict(mv='push', rate=0.015, f=1.05, x=960, y=480))
    # 56-60 A photo out my window. Streetlight. Bus stop. Barlow's corner. Send.
    S(T(56), 'owen', 'window', st=dict(O_NIGHT, tablet_bed=False), rim=PHONE,
      ppl=[P('owen_pj', 'window', id='owen', expr='tempted', act=_A(lambda a, s: a.reach_to(T(56), 1, (lambda t: (a.where(T(56), 'head')[0], a.where(T(56), 'head')[1] + 0.02 * a.height)), t1=E(60) + 1, dur=0.5, z=-50.0, contact='palm', shape='grip', prop='tab'),
                                                       lambda a, s: a.hold_prop('tab', 1, T(56), E(60) + 1)))], c=Z(1.2, 0.015, 1080, 640))
    for i, at, f_ in ((57, 'under_lamp', 1.9), (58, 'bus_stop', 2.0), (59, 'coat', 2.6)):
        S(T(i), 'street', 'from_window', st=dict(tod='night'), c=ZO(f_, at, ody=-80 if at != 'coat' else 0, rate=0.02))
    IN(T(60), 'photo', lambda u: dict(send=clamp((u - 0.25) / 0.35)), c=dict(mv='push', rate=0.02), sfx=[(WD(60, 'send'), 'whoosh_send', -10, 0, 'close')])
    # 61 On my closet door, rule one went pale.
    BLIST(T(61), hl=1, f=1.5, x=900, y=330, rate=0.015)
    # 62-68 That night, a woman stood under that streetlight. Mom's bun. Mom's cardigan, buttoned to the throat. She looked up, and waved.
    #       Headlights swept her face. Two black buttons flashed. She was waving at the window next to mine.
    B1 = dict(hk=1.0 + CH.BLANK_TALL['r1'], expr='still_smile', blink=False)
    S(T(62), 'street', 'from_window', st=dict(tod='night'),
      ppl=[P('blank2', 'under_lamp', id='blank', face=(-1.05, 0.0), **dict(B1, act=_A(lambda a, s: a.head_down(-9, None, 0.6), pose(-9, None, 0.0, eye_shade=1.0))))], c=ZO(2.6, 'under_lamp', ody=-175, rate=0.0, free=True))
    BU(T(63), 'blank2', 'street', 'lamp_close', dict(tod='night'), cx=960, cy=640, scale=1.0, turn=2.6, h_turn=0.0, light=dict(rim='#ffb468', rim_a=140, side=-1, key=-0.3),
       blink=False, c=BZ(0.02))
    BU(T(64), 'blank2', 'street', 'lamp_close', dict(tod='night'), cx=960, cy=260, scale=1.2, turn=0.15, h_turn=0.0, expr='still_smile', blink=False,
       light=dict(rim='#ffb468', rim_a=140, side=-1, key=-0.45), act=_A(lambda a, s: a.head_down(-9, None, 1.0), pose(-9, None, 0.0, eye_shade=1.0)), c=BZ(0.02))
    S(T(65), 'street', 'lamp_close', st=dict(tod='night'),
      ppl=[P('blank2', 'under_lamp', id='blank', face=(-1.7, 0.0), **dict(B1, expr='too_sweet', act=_A(pose(-9, None, 0.0, eye_shade=1.0), lambda a, s: a.head_down(-9, T(65) + 0.2, 0.6), lambda a, s: a.look_at(T(65) + 0.3, scr(s.sp, 'next_window'), dur=0.6), wavef(W(65, 'waved'), E(68) + 2, side=1))))],
      c=Z(2.0, 0.015, 700, 620))
    tsw = T(66) + 0.2
    BU(T(66), 'blank2', 'street', 'lamp_close', dict(tod='night', sweep=ST.bt_sweep(tsw)), cx=960, cy=580, scale=1.05, turn=0.2, expr='too_sweet', blink=False,
       light=lambda t: dict(rim='#ffffff', rim_a=int(60 + 190 * math.exp(-((t - tsw - 1.0) / 0.5) ** 2)), side=1, key=-0.3 + 0.5 * math.exp(-((t - tsw - 1.0) / 0.5) ** 2)),
       act=_A(lookxy(960, 0, T(66)), pose(-9, tsw + 0.7, 0.25, eye_shade=1.0)), c=BZ(0.02), sfx=[(T(66), 'car_pass', -12, 0, 'outside')])
    BU(T(67), 'blank2', 'street', 'lamp_close', dict(tod='night'), cx=960, cy=520, scale=1.6, turn=0.1, expr='too_sweet', blink=False,
       light=dict(rim='#ffffff', rim_a=200, side=1, key=0.15), act=_A(lookxy(960, 0, T(67))), c=BZ(0.03), hit=WD(67, 'flashed'))
    S(T(68), 'street', 'lamp', st=dict(tod='night', win={'next': 0.0, 'owen': 0.4}),
      ppl=[P('blank2', 'under_lamp', id='blank', face=(-4.8, 0.0), **dict(B1, expr='too_sweet', act=_A(lambda a, s: a.look_at(-9, scr(s.sp, 'next_window'), dur=0.3), wavef(-9, None, side=1))))],
      c=Z(2.4, 0.02, 800, 820))
    # 69 "I see you."  (the ping before it: the chat message arrives)
    tp = _beat_t('she_was_waving')
    CHAT(tp - 0.05, msgs='see', show=lambda t: clamp((t - tp + 0.05) / 0.3), head=7.0, name='The Blank', c=dict(mv='push', rate=0.03, f=1.3, x=900, y=900))
    # 70-74 I ducked. Tik. I looked again. She was at our lobby door, palms on the glass, head tilting toward my window sliding shut. Tik. I looked again. Gone.
    S(T(70), 'owen', 'window', st=dict(O_NIGHT, tablet_bed=True, sash=lambda t: 0.5 * (1 - clamp((t - F.t(70)) / 0.4))),
      ppl=[P('owen_pj', 'window', id='owen', expr='fear', act=_A(lambda a, s: a.crouch(T(70) + 0.05, amount=1.6, t1=None, dur=0.25)))],
      c=Z(1.1, 0.01, 1080, 700), sfx=[(T(70) + 0.1, 'window_sash_shut', -8, 0, 'inside')])
    tk = _beat_t('i_ducked')
    S(tk - 0.04, 'street', 'from_window', st=dict(tod='night'), c=ZO(2.2, 'under_lamp', ody=-90, rate=0.0))
    S(T(72), 'street', 'lobby', st=dict(tod='night'),
      ppl=[P('blank2', 'glass_out', id='blank', face=(3.0, -1.5), **dict(B1, expr='too_sweet', act=_A(lambda a, s: a.hand_on_glass(T(72) + 0.1, E(72) + 3, side=1),
                                                                                                          lambda a, s: a.hand_on_glass(T(72) + 0.2, E(72) + 3, side=-1),
                                                                                                          lambda a, s: a.listen_tilt(W(72, 'tilting'), None, side=1, angle=24.0))))],
      c=Z(1.5, 0.02, 1225, 640))
    tk2 = _beat_t('she_was_at')
    S(tk2 - 0.35, 'lobby', 'close', tod='night',
      ppl=[P('blank2', 'glass_out', id='blank', face=(3.0, -1.5), **dict(B1, expr='too_sweet', act=_A(lambda a, s: a.hand_on_glass(-9, s.t1 + 1, side=1), lambda a, s: a.hand_on_glass(-9, s.t1 + 1, side=-1),
                                                                                                          lambda a, s: a.listen_tilt(-9, None, side=1, angle=24.0))))],
      c=Z(1.0, 0.02))
    S(T(73), 'street', 'lobby_pov', st=dict(tod='night'), c=ZO(1.5, 'glass_out', ody=-60, rate=0.01))
    S(T(74), 'street', 'lobby_pov', st=dict(tod='night'), c=ZO(1.7, 'glass_out', ody=-60, rate=0.02))
    # 75-77 She wasn't far away. She was made of everything I'd told her. And she was outside... wearing my mom.
    S(T(75), 'owen', 'window', st=dict(O_NIGHT, tablet_bed=False), rim=dict(rim='#ffb468', rim_a=120, side=1, key=-0.25),
      ppl=[P('owen_pj', 'window', id='owen', expr='fear', act=_A(lambda a, s: a.crouch(-9, amount=1.0, t1=T(75) + 0.6, dur=0.5)))], c=Z(1.3, 0.015, 1080, 640))
    CHAT(T(76), msgs=['tell'], show=5.0, head=7.0, name='The Blank', c=dict(mv='push', rate=0.03, f=1.7, x=420, y=560))
    BU(T(77), 'owen_pj', 'owen', 'window', O_DARK, cx=980, cy=600, scale=1.05, turn=-0.15, expr='fear', light=dict(rim='#ffb468', rim_a=150, side=1, key=-0.3),
       act=_A(lookxy(1300, 1100, T(77))), c=BZ(0.025))


def plan_prompt(F):
    PROMPT(T(78), 'ask')


def plan_rule2(F):
    RLIST(T(81), 2)
    RBIG(T(82), 2)
    # 83-88 Tuesday, a box on our doormat. Mom's name on the label. I opened it anyway. The red coat from Barlow's. And a card. "Because she never even looked. Don't tell her."
    IN(T(83), 'box', dict(state='closed'), c=dict(mv='push', rate=0.02))
    IN(T(84), 'box', dict(state='closed'), c=dict(mv='push', rate=0.03, f=1.9, x=780, y=380))
    IN(T(85), 'box', lambda u: dict(state='open' if u > (WD(85, 'opened') - T(85) + 0.2) else 'closed'), c=dict(mv='push', rate=0.02), sfx=[(WD(85, 'opened') + 0.2, 'cardboard_open', -8, 0, 'close')])
    IN(T(86), 'box', dict(state='open'), c=dict(mv='push', rate=0.03, f=1.3, x=960, y=600))
    IN(T(87), 'card', c=dict(mv='push', rate=0.02))
    IN(T(88), 'card', c=dict(mv='push', rate=0.03, f=1.15, x=880, y=560))
    # 89 I hid it in my closet.
    S(T(89), 'owen', 'closet', st=dict(tod='day', closet=95.0, ink=INK(T(89)), coat='sag'),
      ppl=[P('owen', 'closet', id='owen', expr='guilt', act=_A(lambda a, s: a.reach_to(T(89) + 0.2, 1, scr(s.sp, 'coat'), t1=E(89) + 0.6, dur=0.5, z=-20, contact='grip', shape='grip')))],
      c=Z(1.0, 0.015, 960, 600))
    # 90-92 Mom frowned at her laptop. "It says delivered. On the mat." I thought she was talking to a caller.
    S(T(90), 'apt', 'wide', st=K_EVE, cam=MOM_TABLE, rim=LAMP, ppl=[P('mom', 'table_mom', id='mom', expr='puzzled', act=_A(lk(T(90), 'laptop'), lambda a, s: a.lean_in(T(90) + 0.2, dur=1.2, amount=0.5)))],
      c=Z(1.05, 0.015))
    IN(W(90, 'laptop') - 0.2, 'laptop', dict(state='delivered'), c=dict(mv='push', rate=0.02))
    BU(T(91), 'mom', 'apt', 'wide', K_EVE, cx=1000, cy=600, scale=0.95, turn=0.35, expr='puzzled', light=LAMP, act=_A(lookxy(1400, 1000, T(91))), c=BZ(0.015))
    BU(T(92), 'owen', 'apt', 'living', dict(tod='evening', living=1.0), cx=900, cy=620, scale=0.95, turn=-0.3, expr='guilt', light=LAMP, act=_A(lookxy(1500, 600, T(92))), c=BZ(0.015))
    # 93-95 That night, rule two faded. And Mom looked a little grey. Like a photo left in the sun.
    BLIST(T(93), hl=2, f=1.5, x=900, y=400, rate=0.015)
    S(T(94), 'apt', 'wide', st=dict(K_2AM, lamp=0.6), cam=MOM_TABLE, rim=LAMP, ppl=[P('mom', 'table_mom', id='mom', expr='exhausted', act=_A(typ(T(94), E(95) + 1), lk(T(94), 'laptop')))],
      c=Z(1.05, 0.012))
    BU(T(95), 'mom', 'apt', 'wide', dict(K_2AM, lamp=0.6), cx=1000, cy=600, scale=1.0, turn=0.35, expr='exhausted', light=LAMP, c=BZ(0.015))
    # 96-101 Three a.m. Inside my closet... click. Click. Click. Like somebody counting. Then our song, slow, like a music box winding down.
    BED(T(96), 'sleepy', act=_A(lambda a, s: a.set(T(96) + 0.8, None, 0.4, lids=-0.4)))
    for i, f_ in ((97, 1.3), (98, 1.6), (99, 1.9)):
        S(T(i), 'owen', 'closet', st=dict(tod='night', closet=0.0), c=Z(f_, 0.02, 960, 560), sfx=[(WD(i, 'click'), 'button_click', -8, 0, 'inside')])
    BED(T(100), 'fear', act=_A(lookxy(1500, 700, T(100))), f=1.5)
    S(T(101), 'owen', 'closet', st=dict(tod='night', closet=0.0), c=Z(2.2, 0.02, 960, 600),
      acts=lambda A, sh, sp: [notes_layer((960, 600), T(101) + 0.3, rate=1.2, slow=1.8)])
    # 102-107 I opened the closet. The red coat hung there, buttoned to the top. Full. Like somebody was inside it. Then, slowly, it sagged. Empty.
    S(T(102), 'owen', 'wide', st=dict(O_DARK, closet=lambda t: 95.0 * ease_in_out(clamp((t - F.t(102) - 0.6) / 0.6)), coat='full', ink=INK(T(102))),
      ppl=[P('owen_pj', 'closet', id='owen', expr='fear', act=_A(lambda a, s: a.reach_to(T(102) + 0.1, 1, scr(s.sp, 'list', 0, 60), t1=T(102) + 0.9, dur=0.4, z=-20, contact='grip', shape='grip')))],
      c=Z(2.2, 0.015, 1300, 690), sfx=[(T(102) + 0.6, 'closet_door_creak', -8, 0, 'inside')])
    IN(T(103), 'coat', dict(full=1.0), c=dict(mv='push', rate=0.02))
    S(T(104), 'owen', 'closet', st=dict(tod='night', closet=95.0, coat='full', ink=INK(T(104))), c=Z(1.4, 0.03, 960, 520))
    IN(T(105), 'coat', dict(full=1.0), motion=lambda u: (0.0, 0.0, 0.006 * math.sin(u * 2.2), 0.0), c=dict(mv='push', rate=0.03, f=1.2))
    IN(T(106), 'coat', lambda u, t0=T(106): dict(full=1.0 - ease_in_out(clamp((t0 + u - F.t(106) - 0.4) / max(0.5, F.e(106) - F.t(106))))),
       c=dict(mv='push', rate=0.02), sfx=[(T(106) + 0.4, 'cloth_sag', -10, 0, 'close')])
    tk = _beat_t('empty')
    IN(tk - 0.4, 'jar', dict(state='full', bg='sill'), c=dict(mv='push', rate=0.02), layers=[drop_button(990, -120, 960, 500, tk, c='#7a7a86')])


SNOW = dict(snow=1.0)
CURB_CAM = None


def plan_rule3(F):
    RLIST(T(108), 3)
    RBIG(T(109), 3)
    # 111-115 Wednesday pickup. Snow. Our car. Our dent. Mom at the wheel in sunglasses, humming our song.
    S(T(111), 'school', 'wide', st=SNOW, rim=DAY, c=Z(1.2, 0.015, 840, 600))
    S(W(111, 'pickup'), 'school', 'curb', st=SNOW, rim=DAY,
      ppl=[P('owen_coat', AP(0.3, 1.1)[:2] + (0.0,), id='owen', face=(0.6, -1.3), expr='neutral', act=_A(lk(-9, 'car_window')))], c=Z(1.0, 0.015, 840, 600))
    BU(T(112), 'owen_coat', 'school', 'wide', SNOW, cx=960, cy=620, scale=0.95, turn=-0.2, expr='neutral', light=DAY, act=_A(lookxy(960, 0, T(112))), c=BZ(0.015))
    S(T(113), 'school', 'curb', st=SNOW, rim=DAY, c=Z(1.0, 0.015, 840, 640))
    S(T(114), 'school', 'wide', st=SNOW, rim=DAY, c=ZO(3.2, (-1.55, -1.3, 0.45), rate=0.02))
    hum_ = lambda t0, t1: (lambda a, s: a.hum(t0, t1))
    DRV = dict(id='blank', expr='too_sweet', blink=False)
    S(T(115), 'school', 'window', st=SNOW, rim=DAY,
      ppl=[P('blank1_shades', 'driver', face=(1.0, -0.4), **dict(DRV, act=_A(hum_(T(115), E(115) + 1), lk(T(115), (1400, 520)))))],
      c=Z(1.35, 0.015, 1150, 560))
    # 116-117 The door swung open. "Get in, sweetheart. I got off early. Pancakes?"
    tdo = T(116) + 0.3
    S(T(116), 'school', 'curb', st=dict(SNOW, rear_door=lambda t: ease_out_cubic(clamp((t - tdo) / 0.7))), rim=DAY,
      ppl=[P('blank1_shades', 'driver', face=(1.0, 0.6), **dict(DRV, act=_A(lk(T(116), 'kerb_owen'))))],
      c=Z(1.1, 0.015, 900, 700), sfx=[(tdo, 'car_door_open', -6, 0, 'outside')])
    S(T(117), 'school', 'window', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('blank1_shades', 'driver', face=(0.2, 1.0), **dict(DRV, act=_A(lk(T(117), (600, 300)), tilt(T(117) + 0.8, 10.0, 1.8))))],
      c=Z(1.5, 0.02, 1150, 560))
    # 118-120 Mom never got off early. Pancakes were Saturdays. And I'd typed that.
    BU(T(118), 'owen_coat', 'school', 'curb', dict(SNOW, rear_door=1.0), cx=1000, cy=620, scale=0.95, turn=0.3, expr='suspicious', light=DAY, act=_A(lookxy(400, 600, T(118))), c=BZ(0.015))
    BU(T(119), 'owen_coat', 'school', 'curb', dict(SNOW, rear_door=1.0), cx=960, cy=600, scale=1.1, turn=0.25, expr='suspicious', light=DAY, act=_A(lookxy(400, 640, T(119))), c=BZ(0.02))
    CHAT(T(120), msgs=['tell'], show=5.0, head=7.0, name='The Blank', c=dict(mv='push', rate=0.04, f=1.6, x=1500, y=310))
    # 121-123 I stepped back. I called my mom. First ring.
    S(T(121), 'school', 'curb', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('owen_coat', 'step_back', id='owen', path=[(T(121), 'kerb_owen'), (E(121) + 0.3, 'step_back')], surface='snow', expr='fear', act=_A(lk(T(121), 'car_window'))),
           P('blank1_shades', 'driver', face=(0.2, 1.0), **dict(DRV, act=_A(lk(T(121), ('owen', 'head')))))],
      c=Z(1.0, 0.012))
    S(T(122), 'school', 'back', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('owen_coat', 'step_back', id='owen', expr='fear', face=(0.6, -1.3), act=_A(lambda a, s: a.phone_to_ear(T(122) + 0.1, E(140) + 9), lk(T(122), 'car_window')))],
      c=Z(2.2, 0.015, 1220, 640))
    BU(T(123), 'owen_coat', 'school', 'back', dict(SNOW, rear_door=1.0), cx=980, cy=600, scale=1.0, turn=-0.3, expr='fear', light=DAY,
       act=_A(lambda a, s: a.phone_to_ear(-9, None), lookxy(400, 620, T(123))), c=BZ(0.015), sfx=[(T(123) + 0.1, 'phone_ring_out', -12, 0, 'close')])
    # 124 "Baby? I'm at the table. Where are you?"
    S(T(124), 'apt', 'wide', st=K_DAY, cam=MOM_TABLE, rim=DAY_L,
      ppl=[P('mom', 'table_mom', id='mom', expr='terrified_call', act=_A(lambda a, s: a.press_headset(T(124), E(124) + 1, side=-1), lookxy(600, 400, T(124) + 0.3)))],
      c=Z(1.15, 0.02))
    # 125-126 She lowered the sunglasses. Buttons.
    S(T(125), 'school', 'window', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('blank1_shades', 'driver', face=(0.2, 1.0), **dict(DRV, act=_A(lk(-9, (600, 300)), pose(W(125, 'lowered'), None, 0.8, shades_dn=1.0))))],
      c=Z(1.6, 0.02, 1150, 540))
    BU(T(126), 'blank1_shades', 'school', 'window', dict(SNOW, rear_door=1.0), cx=960, cy=560, scale=1.35, turn=-0.15, expr='too_sweet', blink=False, light=DAY,
       act=_A(pose(-9, None, 0.0, shades_dn=1.0)), c=BZ(0.03), hit=WD(126, 'buttons'))
    # 127-130 Her arm slid out of the window. And kept coming. Bending where arms don't bend. Fingers tapping the air, reaching for my hood.
    ta = T(127) + 0.2
    arm = lambda t: 0.75 * ease_in_out(clamp((t - ta) / 3.2)) + 0.25 * ease_in_out(clamp((t - F.t(129)) / 3.5))
    for i, view, f_ in ((127, 'back', 1.0), (128, 'back', 1.12), (129, 'back', 1.25), (130, 'back', 1.4)):    # review 1 M4: one screen direction
        S(T(i), 'school', view, st=dict(SNOW, rear_door=1.0), rim=DAY,
          ppl=[P('owen_coat', 'step_back', id='owen', expr='terror', face=(0.6, -1.3),
                 act=_A(lambda a, s: a.phone_to_ear(-9, None), lk(-9, 'car_window'), lambda a, s: a.lean_in(T(130), dur=1.0, amount=-0.6) if s.t0 >= T(130) - 0.2 else None)),
               P('blank1_shades', 'driver', face=(0.2, 1.0), **dict(DRV, act=_A(pose(-9, None, 0.0, shades_dn=1.0), lk(-9, ('owen', 'head')))))],
          acts=arm_acts('owen', arm), c=Z(f_, 0.015, 960 if view == 'curb' else 1100, 640), sfx=[(T(130) + 0.2, 'fingertip_tap', -12, 0, 'outside')] if i == 130 else [])
    # 131-134 I ran to Mr. Dunn, the crossing guard. "You did right. You checked. Stand with me." His radio was already up. "Silver car. Dented bumper. Now."
    S(T(131), 'school', 'dunn', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('dunn', 'dunn', id='dunn', expr='calm_firm', act=_A(lambda a, s: a.hold_sign(-1e9, None, side=-1), lk(T(131), ('owen', 'head')))),
           P('owen_coat', 'dunn_owen', id='owen', path=[(T(131), 'step_back'), (E(131) + 0.2, 'dunn_owen')], run=True, surface='snow', expr='terror')],
      c=Z(3.0, 0.015, 1005, 560))
    S(T(132), 'school', 'dunn', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('dunn', 'dunn', id='dunn', expr='calm_firm', act=_A(lambda a, s: a.hold_sign(-1e9, None, side=-1), lk(T(132), ('owen', 'head')),
                                                               lambda a, s: a.shelter(T(132) + 0.4, s.A['owen'], None, side=1, toward=-1))),
           P('owen_coat', 'dunn_owen', id='owen', expr='fear', act=_A(lk(T(132), ('dunn', 'head'))))],
      c=Z(3.3, 0.015, 1012, 560))
    S(T(133), 'school', 'dunn', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('dunn', 'dunn', id='dunn', expr='calm_firm', act=_A(lambda a, s: a.hold_sign(-1e9, None, side=-1), lambda a, s: a.radio_up(T(133) - 0.3, E(134) + 1, side=1),
                                                               lk(T(133), (300, 600)))),
           P('owen_coat', 'dunn_owen', id='owen', expr='fear', act=_A(lk(T(133), ('dunn', 'head'))))],
      c=Z(3.4, 0.015, 1012, 560))
    BU(T(134), 'dunn', 'school', 'dunn', dict(SNOW, rear_door=1.0), cx=1000, cy=620, scale=0.95, turn=-0.35, expr='calm_firm', light=DAY,
       act=_A(lambda a, s: a.radio_up(-9, E(134) + 1, side=1), lookxy(300, 600, T(134))), c=BZ(0.015))
    # 135-136 The arm folded back in. Then, just tire tracks.
    tf = T(135) + 0.1
    S(T(135), 'school', 'back', st=dict(SNOW, rear_door=1.0), rim=DAY,
      ppl=[P('blank1_shades', 'driver', face=(1.0, 0.3), **dict(DRV, act=_A(pose(-9, None, 0.0, shades_dn=1.0))))],
      acts=lambda A, sh, sp: arm_acts('blank', lambda t: 1.0 - ease_in_out(clamp((t - tf) / 1.4)), 'car_window')(dict(A, blank=_Proxy(sp, 'hood_reach')), sh, sp),
      c=Z(1.2, 0.015, 900, 620), sfx=[(E(135) - 0.3, 'car_door_close', -6, 0, 'outside'), (E(135), 'car_drive_off', -8, 0, 'outside')])
    S(T(136), 'school', 'back', st=dict(SNOW, car=False), rim=DAY, c=ZO(1.6, 'lane', ody=-30, rate=0.02))
    # 137-141 Mom came running. I told her about the car. She called the police. Officer Mensah took notes. Mom checked every lock twice.
    S(T(137), 'school', 'back', st=dict(SNOW, car=False), rim=DAY,
      ppl=[P('mom', 'mom_run', id='mom', path=[(T(137), (1.8, 1.9, 0.0)), (T(138) - 0.05, (4.9, 1.6, 0.0))], run=True, surface='snow', expr='terrified_call',
             act=_A(pose(-9, None, 0.0, hs_off=1.0))),         # review 1 B5: no work headset outdoors (it drew as a mask on her face)
           P('owen_coat', (6.2, 1.2, 0.0), id='owen', face=(3.0, 1.6), expr='relief'),
           P('dunn', 'dunn', id='dunn', face=(3.0, 1.6), expr='calm_firm', act=_A(lambda a, s: a.hold_sign(-1e9, None, side=-1)))],
      c=Z(1.8, 0.015, 1150, 650))
    S(T(138), 'school', 'dunn', st=dict(SNOW, car=False), rim=DAY,
      ppl=[P('mom', (5.4, 1.15, 0.0), id='mom', kind='kneel', face=(6.2, 1.2), expr='terrified_call', act=_A(pose(-9, None, 0.0, hs_off=1.0), lk(T(138), ('owen', 'head')), lambda a, s: a.reach_to(T(138) + 0.3, 1, (s.A['owen'], 'shoulder_r'), t1=E(139), dur=0.5, z=-20, contact='palm', shape='open'))),
           P('owen_coat', (6.2, 1.2, 0.0), id='owen', face=(5.4, 1.15), expr='fear', act=_A(lk(T(138), ('mom', 'head')), lambda a, s: a.point_at(T(138) + 0.5, (300, 640), t1=E(138), side=-1)))],
      c=Z(2.3, 0.015, 960, 640))
    S(T(139), 'school', 'dunn', st=dict(SNOW, car=False), rim=DAY,
      ppl=[P('mom', (5.4, 1.15, 0.0), id='mom', face=(6.2, 1.2), expr='focused', act=_A(pose(-9, None, 0.0, hs_off=1.0), lambda a, s: a.phone_to_ear(T(139), None, side=1), lk(T(139), ('owen', 'head')))),
           P('owen_coat', (6.2, 1.2, 0.0), id='owen', face=(5.4, 1.15), expr='fear', act=_A(lk(T(139), ('mom', 'head'))))],
      c=Z(2.3, 0.015, 960, 640))
    S(T(140), 'school', 'dunn', st=dict(SNOW, car=False), rim=DAY,
      ppl=[P('mensah', 'mensah', id='mensah', face=(6.2, 1.2), expr='calm_firm', act=_A(lambda a, s: a.take_notes(T(140), None))),
           P('mom', (5.4, 1.15, 0.0), id='mom', face=(5.8, 1.6), expr='focused', act=_A(pose(-9, None, 0.0, hs_off=1.0), lk(T(140), ('mensah', 'head')))),
           P('owen_coat', (6.2, 1.2, 0.0), id='owen', face=(5.8, 1.6), expr='neutral', act=_A(lk(T(140), ('mensah', 'head'))))],
      c=Z(2.0, 0.015, 960, 640))
    S(T(141), 'apt', 'living', st=dict(tod='evening', living=1.0), cam=FRONTDOOR, rim=LAMP,
      ppl=[P('mom', AP(0.8, 4.45), id='mom', face=(0.0, 4.55), expr='focused',
             act=_A(lambda a, s: a.reach_to(T(141) + 0.2, 1, scr(s.sp, AP(0.02, 4.25), 0, -0.98 * s.I['mom']['spot'].ppm if False else 0), t1=pdur(141, 0.5), dur=0.4, z=-30, contact='grip', shape='grip'),
                    lambda a, s: a.reach_to(pdur(141, 0.55), 1, scr(s.sp, (0.02, 4.25, U + 1.0)), t1=E(141) + 0.4, dur=0.35, z=-30, contact='grip', shape='grip')))],
      c=Z(1.2, 0.015), sfx=[(pdur(141, 0.3), 'deadbolt', -10, 0, 'inside'), (pdur(141, 0.75), 'deadbolt', -10, 0, 'inside')])
    # 142 Rule three stayed blue.
    BLIST(T(142), hl=3, f=1.5, x=900, y=480, rate=0.015)
    # 143-146 But locks don't stop something in your pocket. I never told her about the chat. Half a secret is still a secret. Ping. "Tell her about me..."
    S(T(143), 'owen', 'bed', st=O_NIGHT, rim=PHONE, ppl=[P('owen_pj', 'bed_edge', id='owen', expr='guilt', act=_A(tabf(-9, None)))], c=Z(1.35, 0.015, 1180, 740))
    S(T(144), 'apt', 'wide', st=dict(K_EVE, lamp=0.8), cam=TWO_TABLE, rim=LAMP,
      ppl=[P('mom', 'table_mom', id='mom', expr='busy', act=_A(typ(T(144), None), lk(T(144), 'laptop'))),
           P('owen_pj', 'table_owen', id='owen', expr='guilt', act=_A(lk(T(144), ('mom', 'head')), lambda a, s: a.head_down(pdur(144, 0.6), None, 0.5)))],
      c=Z(1.1, 0.012))
    BU(T(145), 'owen_pj', 'owen', 'bed', O_NIGHT, cx=960, cy=600, scale=1.05, turn=0.25, expr='guilt', light=PHONE, act=_A(lookxy(1100, 1200, T(145))), c=BZ(0.02))
    tp = _beat_t('half_a_secret')
    CHAT(tp - 0.05, msgs=['tell', 'fault'], show=lambda t: 5.0 + clamp((t - tp + 0.05) / 0.35), head=7.0, name='The Blank', c=dict(mv='push', rate=0.015, f=1.1, x=1150, y=700))
    tk = _beat_t('blank_tell_her_about')
    IN(tk - 0.5, 'jar', dict(state='full', bg='sill'), c=dict(mv='push', rate=0.02), layers=[drop_button(930, -120, 960, 500, tk, c='#3a9a6a')])


class _Proxy:
    """A stand-in 'actor' at an anchor (the car arm's target when no Owen is in the shot)."""
    def __init__(self, sp, at):
        s_ = spot_of(sp, at); self.x, self.y, self.height = s_.x, s_.y, 1.45 * s_.ppm
    def where(self, t, part='neck'): return (self.x, self.y + 0.05 * self.height)


def plan_rule4(F):
    RLIST(T(147), 4)
    RBIG(T(148), 4)
    # 150-154 Two in the morning. Ping. Mom's name. "Come to the kitchen, baby." Mom, awake, wanting me? I went.
    tp = _beat_t('two_in_the')
    BED(T(150), 'sleepy', act=_A(lambda a, s: a.set(tp + 0.1, None, 0.25, lids=-0.3), lookxy(1500, 700, tp + 0.2)))
    CHAT(T(151), msgs='mom_2am', account='mom', show=0.0, banner=('Mom', 'Come to the kitchen, baby.', 1.0), c=dict(mv='push', rate=0.02))
    CHAT(T(152), msgs='mom_2am', account='mom', show=lambda t: clamp((t - F.t(152) + 0.3) / 0.4), c=dict(mv='push', rate=0.015, f=1.1, x=760, y=500))
    BU(T(153), 'owen_pj', 'owen', 'bed', O_NIGHT, cx=960, cy=600, scale=1.0, turn=0.2, expr='tempted', light=PHONE, act=_A(lookxy(1200, 1100, T(153))), c=BZ(0.02))
    S(T(154), 'apt', 'living', st=K_2AM, cam=DOOR_IN,
      ppl=[P('owen_pj', AP(2.4, 3.15), id='owen', path=[(T(154), 'owendoor'), (E(154) + 0.6, AP(2.4, 3.15))], surface='inside_quiet', expr='tempted')], c=Z(1.0, 0.012))
    # 155-158 She sat at her laptop, back to me, reading glasses on. Every key she pressed... my tablet pinged. She turned, and took the glasses off. Buttons.
    BACK = MC(AP(3.66, 2.35), 265, 2.0, h=1.45, lh=1.0, S=820)
    B1 = dict(id='blank', blink=False)
    S(T(155), 'apt', 'wide', st=K_2AM, cam=BACK, rim=dict(rim='#bcd4ff', rim_a=110, side=1, key=-0.3),
      ppl=[P('blank1', 'table_mom', **dict(B1, expr='polite', act=_A(lk(T(155), 'laptop'))))], c=Z(1.3, 0.012, 960, 600))
    IN(T(156), 'laptop', lambda u: dict(state='msg', typed=clamp(u / 1.6)), c=dict(mv='push', rate=0.02),
       sfx=[(T(156) + 0.25 + 0.35 * k, 'tablet_ping_soft', -18, 0, 'close') for k in range(4)])
    BU(W(156, 'tablet'), 'owen_pj', 'apt', 'wide', K_2AM, cx=980, cy=620, scale=1.0, turn=-0.3, expr='fear', light=PHONE, act=_A(lookxy(1100, 1150, W(156, 'tablet'))), c=BZ(0.02))
    tg = W(157, 'took')
    S(T(157), 'apt', 'wide', st=K_2AM, cam=MOM_TABLE, rim=dict(rim='#bcd4ff', rim_a=110, side=1, key=-0.3),
      ppl=[P('blank1', 'table_mom', **dict(B1, expr='polite', act=_A(lambda a, s: a.turn(T(157) + 0.1, 0.9, dur=0.6), lambda a, s: a.glasses_off(tg, None, side=1))))],
      c=Z(1.15, 0.02))
    BU(T(158), 'blank1', 'apt', 'table_back', K_2AM, cx=960, cy=560, scale=1.3, turn=0.15, expr='too_sweet', blink=False, light=dict(rim='#bcd4ff', rim_a=140, side=1, key=-0.1),
       act=_A(pose(-9, None, 0.0, specs=0.0)), c=BZ(0.03), hit=WD(158, 'buttons'))
    # 159 "Sit. Say something. I like to hear where you are."
    BU(T(159), 'blank1', 'apt', 'table_back', K_2AM, cx=1020, cy=600, scale=1.0, turn=0.3, expr='too_sweet', blink=False, light=dict(rim='#bcd4ff', rim_a=110, side=1, key=-0.2),
       act=_A(pose(-9, None, 0.0, specs=0.0), lambda a, s: a.listen_tilt(W(159, 'hear'), None, side=1, angle=22.0)), c=BZ(0.015))
    # 160-162 I glanced at Mom's door. Tik. The Blank was in front of it. "Or I tell her what you wished."
    tk = _beat_t('i_glanced_at')
    S(T(160), 'apt', 'momdoor', st=K_2AM, c=Z(1.2, 0.012, 917, 700))
    B2 = dict(id='blank', hk=1.0 + CH.BLANK_TALL['r4'], expr='too_sweet', blink=False)
    S(tk - 0.04, 'apt', 'momdoor', st=K_2AM, ppl=[P('blank2', 'momdoor', **dict(B2, act=_A(lambda a, s: a.listen_tilt(T(161), None, side=-1, angle=18.0))))], c=Z(1.25, 0.015, 917, 640))
    BU(T(162), 'blank2', 'apt', 'momdoor', K_2AM, cx=960, cy=580, scale=1.1, turn=-0.2, expr='wrong_smile', blink=False, light=NIGHT, c=BZ(0.02))
    # 163-166 So I answered. My school. What time it lets out. Which nights Mom works late.
    S(T(163), 'apt', 'wide', st=K_2AM, cam=OWEN_TABLE,
      ppl=[P('owen_pj', 'table_owen', id='owen', expr='guilt', act=_A(lambda a, s: a.head_down(T(163) + 0.2, None, 0.5)))], c=Z(1.05, 0.012))
    BU(T(164), 'blank2', 'apt', 'momdoor', K_2AM, cx=980, cy=600, scale=1.0, turn=-0.25, expr='too_sweet', blink=False, light=NIGHT,
       act=_A(lambda a, s: a.listen_tilt(T(164), None, side=1, angle=26.0)), c=BZ(0.02))
    BU(T(165), 'owen_pj', 'apt', 'wide', K_2AM, cx=940, cy=620, scale=0.95, turn=-0.3, expr='guilt', light=dict(rim='#bcd4ff', rim_a=100, side=1, key=-0.3), c=BZ(0.015))
    S(T(166), 'apt', 'wide', st=K_2AM, cam=TWO_TABLE,
      ppl=[P('blank2', AP(4.55, 3.36), face=(5.54, 2.35), **dict(B2, act=_A(lambda a, s: a.listen_tilt(T(166), None, side=1, angle=24.0)))),
           P('owen_pj', 'table_owen', id='owen', expr='guilt', act=_A(lambda a, s: a.head_down(-9, None, 0.4)))],
      c=Z(1.05, 0.015))
    # 167 "It's not a secret. It's a surprise. Your mom finds out when we're gone. On your birthday, you button up... and I take you home."
    S(T(167), 'apt', 'wide', st=K_2AM, cam=TWO_TABLE,
      ppl=[P('blank2', AP(4.95, 3.35), face=(5.54, 2.35), **dict(B2, act=_A(lambda a, s: a.lean_in(T(167) + 0.3, dur=2.0, amount=0.7)))),
           P('owen_pj', 'table_owen', id='owen', expr='fear', act=_A(lk(T(167), ('blank', 'head'))))],
      c=Z(1.2, 0.015, 1060, 560))
    BU(W(167, 'your'), 'blank2', 'apt', 'wide', K_2AM, cx=1000, cy=580, scale=1.15, turn=0.3, expr='too_sweet', blink=False, light=dict(rim='#bcd4ff', rim_a=120, side=-1, key=-0.25),
       act=_A(lambda a, s: a.head_tilt(W(167, 'birthday'), 14.0, 2.2)), c=BZ(0.025))
    # 168-171 With a surprise, everyone finds out soon, and smiles. "Your mom finds out when we're gone" is a secret wearing a bow. I nodded. Rule four faded.
    IN(T(168), 'board', dict(state='birthday', k=1.0), c=dict(mv='push', rate=0.02, f=1.15, x=960, y=330))
    BU(T(169), 'blank2', 'apt', 'wide', K_2AM, cx=960, cy=580, scale=1.2, turn=0.2, expr='wrong_smile', blink=False, light=dict(rim='#bcd4ff', rim_a=120, side=-1, key=-0.25), c=BZ(0.02))
    BU(T(170), 'owen_pj', 'apt', 'wide', K_2AM, cx=960, cy=620, scale=1.0, turn=-0.25, expr='guilt', light=dict(rim='#bcd4ff', rim_a=100, side=1, key=-0.3),
       act=_A(nodf(T(170) + 0.05, 1, 0.22, 0.7)), c=BZ(0.015))
    BLIST(T(171), hl=4, f=1.45, x=900, y=500, rate=0.015)
    # 172-182 the microwave door: Mom looks up, the Blank is gone; Mom looks down, she is closer
    S(T(172), 'apt', 'wide', st=K_EVE, cam=STOOL2, rim=LAMP,
      ppl=[P('mom', 'table_mom', id='mom', expr='busy', act=_A(typ(T(172), None), lk(T(172), 'laptop'))),
           P('owen', 'stool', id='owen', expr='lonely', act=_A(lk(T(172), 'micro')))],
      c=Z(1.05, 0.012))
    OW = dict(who='owen', at=(6.6, 2.9), face=(1.0, 0.0), kind='seat', seat_Y=0.66, expr='fear', id='owen')
    MO_UP = dict(who='mom', at=(3.9, 3.25), face=(1.0, 0.0), kind='seat', seat_Y=0.46, expr='busy', id='mom')     # review 1 B7: clear of his head in the door
    def bl(x, y=2.64, alpha=1.0, tall='r4_micro', lean=0.0):
        return dict(who='blank2', at=(x, y), face=(1.0, 0.0), tall=CH.BLANK_TALL[tall], expr='too_sweet', blink=False, alpha=alpha, id='blank',
                    act=(lambda a, s: a.lean_in(-9, dur=0.1, t1=None, amount=lean)) if lean else None)
    MIC = lambda i, figs, f_=1.0, **k: S(T(i), 'apt', 'micro', st=K_EVE, mirror=figs, cam=MICRO_CAM, c=Z(f_, 0.015, 990, 560), **k)
    MIC(173, [OW, MO_UP])
    MIC(174, [OW, MO_UP, bl(5.8, 2.38, alpha=lambda t: clamp((t - F.t(174) - 0.15) / 0.35))], 1.1)       # her face above his head, inside the door
    MIC(175, [OW, MO_UP, bl(5.8, 2.38)], 1.25)
    BU(T(176), 'mom', 'apt', 'wide', K_EVE, cx=1000, cy=620, scale=0.95, turn=0.35, expr='busy', light=LAMP,
       act=_A(lookxy(1300, 1100, -9), lambda a, s: a.look_at(T(176) + 0.15, (500, 520), None, 0.3), pose(T(176) + 0.1, None, 0.3, h_nod=-0.3)), c=BZ(0.015))
    MIC(177, [OW, dict(MO_UP, act=_A(lookxy(1300, 300, -9)))], 1.15)
    BU(T(178), 'mom', 'apt', 'wide', K_EVE, cx=1000, cy=620, scale=0.95, turn=0.35, expr='busy', light=LAMP,
       act=_A(lookxy(500, 520, -9), lambda a, s: a.look_at(T(178) + 0.1, (1300, 1100), None, 0.3), pose(-9, T(178) + 0.05, 0.0, h_nod=-0.3), pose(T(178) + 0.1, None, 0.3, h_nod=0.35)), c=BZ(0.015))
    tk = _beat_t('closer')
    MIC(179, [OW, MO_UP, bl(6.05, 2.5, alpha=lambda t: 1.0 if t >= tk - 0.02 else 0.0, lean=0.5)], 1.35)
    BU(T(180), 'mom', 'apt', 'wide', K_EVE, cx=1000, cy=620, scale=0.95, turn=0.35, expr='busy', light=LAMP, act=_A(lookxy(1300, 1100, -9), lambda a, s: a.look_at(T(180), (500, 520), None, 0.2), pose(T(180), None, 0.2, h_nod=-0.3)), c=BZ(0.0))
    BU(T(181), 'mom', 'apt', 'wide', K_EVE, cx=1000, cy=620, scale=0.95, turn=0.35, expr='busy', light=LAMP, act=_A(lookxy(500, 520, -9), lambda a, s: a.look_at(T(181), (1300, 1100), None, 0.2), pose(T(181), None, 0.2, h_nod=0.35)), c=BZ(0.0))
    tk2 = _beat_t('the_blanks_chin')
    MIC(182, [OW, MO_UP, bl(6.3, 2.7, lean=1.0)], 1.3, sfx=[])


def plan_rule5(F):
    RLIST(T(183), 5)
    RBIG(T(184), 5)
    # 185-188 Thursday dinner. Mom had made my favorite. She stood at the window in her headset, watching the front door. She didn't even sit down.
    S(T(185), 'apt', 'wide', st=K_DIN, rim=LAMP, ppl=[P('mom', 'window_k', id='mom', expr='terrified_call', act=_A(lambda a, s: a.press_headset(-9, None, side=-1)))], c=Z(2.6, 0.015, 1330, 600))
    S(T(186), 'apt', 'table', st=K_DIN, rim=LAMP, c=Z(1.3, 0.02, 1080, 820))
    S(T(187), 'apt', 'wide', st=K_DIN, cam=WINDOW_K, rim=LAMP,
      ppl=[P('mom', 'window_k', id='mom', expr='terrified_call', act=_A(lambda a, s: a.press_headset(T(187) + 0.2, None, side=-1), lookxy(900, 900, T(187))))], c=Z(1.0, 0.012))
    B5 = dict(id='blank', hk=1.0 + CH.BLANK_TALL['r5'], expr='too_sweet', blink=False)
    S(T(188), 'apt', 'wide', st=K_DIN, cam=OWEN_TABLE, rim=LAMP,
      ppl=[P('owen', 'table_owen', id='owen', expr='lonely', act=_A(lookxy(300, 500, T(188))))], c=Z(1.05, 0.012))
    # 189-192 In Mom's chair sat the Blank. Taller now. Her bun brushed the lamp. "Watch. She doesn't even see you."
    sw0 = W(191, 'brushed')
    swing1 = lambda t: 4.0 * math.sin((t - sw0) * 4.2) * math.exp(-(t - sw0) * 0.6) if t > sw0 else 0.0
    B5T = dict(B5, hk=1.0 + CH.BLANK_TALL['r5'] + 0.05)                                  # review 1 M2: taller at dinner, the shade beside her bun
    S(T(189), 'apt', 'wide', st=dict(K_DIN, swing=swing1), cam=TWO_TABLE, rim=LAMP, ppl=[P('blank2', 'table_mom', **dict(B5T, act=_A(lookxy(400, 600, -9))))], c=Z(1.7, 0.015, 1250, 440))
    S(T(190), 'apt', 'wide', st=dict(K_DIN, swing=swing1), cam=TWO_TABLE, rim=LAMP, ppl=[P('blank2', 'table_mom', **dict(B5T, act=_A(lookxy(400, 600, -9))))], c=Z(2.0, 0.02, 1250, 400))
    S(T(191), 'apt', 'wide', st=dict(K_DIN, swing=swing1), cam=TWO_TABLE, rim=LAMP, ppl=[P('blank2', 'table_mom', **dict(B5T, act=_A(lookxy(400, 600, -9), tilt(sw0 - 0.2, 8.0, 1.2),
                                                                                                                       lambda a, s: a.lean_in(sw0 - 0.5, dur=0.5, amount=0.3))))],
      c=Z(2.1, 0.02, 1240, 380))
    BU(T(192), 'blank2', 'apt', 'table', dict(K_DIN, swing=swing1), cx=960, cy=580, scale=1.1, turn=0.1, expr='too_sweet', blink=False, light=LAMP,
       act=_A(lookxy(1500, 500, T(192) + 0.2)), c=BZ(0.02))
    # 193-197 I waved at my mom. She turned, and looked straight through me. Her glasses caught the laptop. Two black, shiny circles. For one second, I couldn't tell my mothers apart.
    S(T(193), 'apt', 'wide', st=K_DIN, cam=MC(AP(5.45, 1.45), 25, 2.7, h=1.5, lh=1.0, S=900), rim=LAMP,     # review 1 M3: his wave and her turn both read
      ppl=[P('owen', 'table_owen', id='owen', expr='asking', act=_A(lk(T(193), ('mom', 'head')), wavef(T(193) + 0.1, E(194), side=1, slow=False))),
           P('mom', 'window_k', id='mom', expr='terrified_call', act=_A(lambda a, s: a.press_headset(-9, T(194), side=-1),
                                                                        lambda a, s: a.turn(T(194) + 0.1, 0.0, dur=0.6), lambda a, s: a.look_at(T(194) + 0.3, (s.A['owen'].where(T(194), 'head')[0], 200), None, 0.4)))],
      c=Z(1.05, 0.015))
    BU(T(195), 'mom', 'apt', 'wide', K_DIN, cx=960, cy=600, scale=1.0, turn=0.0, expr='terrified_call', light=LAMP, act=_A(lookxy(960, 300, -9)), c=BZ(0.02))
    IN(T(196), 'glasses', lambda u: dict(circles=clamp((u - 0.15) / 0.5)), c=dict(mv='push', rate=0.03), hit=WD(196, 'circles'))
    BU(T(197), 'mom', 'apt', 'wide', K_DIN, cx=960, cy=560, scale=1.25, turn=0.0, expr='blank', light=LAMP, act=_A(pose(-9, None, 0.0, circles=1.0)), c=BZ(0.02))
    BU(W(197, 'mothers') - 0.3, 'blank2', 'apt', 'table', K_DIN, cx=960, cy=560, scale=1.25, turn=0.0, expr='still_smile', blink=False, light=LAMP, c=BZ(0.02))
    # 198-199 Mom pressed the headset to her ear. "No... I can't see him anywhere."
    S(T(198), 'apt', 'wide', st=K_DIN, cam=WINDOW_K, rim=LAMP,
      ppl=[P('mom', 'window_k', id='mom', face=(5.4, 2.4), expr='terrified_call', act=_A(lambda a, s: a.press_headset(T(198) + 0.2, None, side=-1), lookxy(900, 700, T(198))))], c=Z(1.15, 0.015))
    BU(T(199), 'mom', 'apt', 'wide', K_DIN, cx=1000, cy=600, scale=1.0, turn=0.3, expr='terrified_call', light=LAMP,
       act=_A(lookxy(400, 500, T(199))), c=BZ(0.015))
    # 200-203 The Blank leaned in. "Only I see you." I heard myself. "Only you."
    S(T(200), 'apt', 'wide', st=K_DIN, cam=TWO_TABLE, rim=LAMP,
      ppl=[P('blank2', 'table_mom', **dict(B5, act=_A(lambda a, s: a.lean_in(T(200) + 0.1, dur=1.5, amount=0.4), lk(T(200), ('owen', 'head'))))),
           P('owen', 'table_owen', id='owen', expr='fear', act=_A(lk(T(200), ('blank', 'head'))))], c=Z(1.1, 0.015))
    BU(T(201), 'blank2', 'apt', 'table', K_DIN, cx=980, cy=600, scale=1.3, turn=0.15, expr='too_sweet', blink=False, light=LAMP, c=BZ(0.03))
    BU(T(202), 'owen', 'apt', 'wide', K_DIN, cx=940, cy=620, scale=1.0, turn=-0.3, expr='lonely', light=LAMP, c=BZ(0.015))
    BU(T(203), 'owen', 'apt', 'wide', K_DIN, cx=960, cy=600, scale=1.1, turn=-0.25, expr='tempted', light=LAMP, c=BZ(0.02))
    # 204-207 On my closet door, every line but rule three faded. And the headset lady went pencil grey. The Blank stood. Her head set the lamp swinging.
    BLIST(T(204), hl=3, f=1.0, rate=0.012)
    BU(T(205), 'mom', 'apt', 'wide', K_DIN, cx=1000, cy=600, scale=1.0, turn=-0.3, h_turn=-0.2, expr='terrified_call', light=LAMP,
       c=BZ(0.015))
    sw1 = W(207, 'head') + 0.1
    swing2 = lambda t: 22.0 * math.sin((t - sw1) * 3.4) * math.exp(-(t - sw1) * 0.18) if t > sw1 else 0.0
    S(T(206), 'apt', 'table', st=dict(K_DIN, swing=swing2), rim=LAMP,
      ppl=[P('blank2', 'table_mom', **dict(B5, act=_A(lambda a, s: a.stand_up(T(206) + 0.2, seat_y=s.sp.anchors['table_mom'].seat_y))))], c=Z(1.0, 0.015, 990, 560))
    S(T(207), 'apt', 'wide', st=dict(K_DIN, swing=swing2), cam=TWO_TABLE, rim=LAMP,
      ppl=[P('blank2', AP(3.82, 2.64), **dict(B5, hk=1.0 + CH.BLANK_TALL['r5'] + 0.05, face=(5.54, 2.35), act=_A(lk(-9, ('owen', 'head')), lambda a, s: a.lean_in(sw1 - 0.5, dur=0.5, amount=0.4)))),
           P('owen', 'table_owen', id='owen', expr='terror', act=_A(lk(-9, ('blank', 'head'))))],
      c=Z(1.1, 0.015, 900, 520), sfx=[(sw1, 'lamp_swing', -6, 0, 'inside')])
    # 208-211 That night, Mom sat on my windowsill, head tilted toward my breathing, singing our song. Again. And again. The headset lady was still on the phone.
    BS = dict(id='blank', hk=1.0 + CH.BLANK_TALL['sill'], expr='still_smile', blink=False)
    S(T(208), 'owen', 'sill_pov', st=O_DARK, ppl=[P('blank2', 'sill_seat', **dict(BS, act=_A(lambda a, s: a.listen_tilt(T(208) + 0.6, None, side=1, angle=26.0), hum(T(208), None)))),
                                                 P('owen_pj', 'pillow', id='owen', kind='pillow', hem='bed_hem', expr='fear')],     # review 1 M11: he is in the bed
      c=Z(1.15, 0.012, 1080, 700))
    BU(T(209), 'blank2', 'owen', 'window', O_DARK, cx=960, cy=600, scale=1.05, turn=0.1, expr='still_smile', blink=False, light=dict(rim='#ffb468', rim_a=150, side=-1, key=-0.3),
       act=_A(lambda a, s: a.listen_tilt(-9, None, side=1, angle=26.0), hum(-9, None)), c=BZ(0.015))
    BED(T(210), 'fear', act=_A(lookxy(1500, 700, -9), lambda a, s: a.set(-9, None, 0.0, lids=-0.2)), f=1.5)
    S(T(211), 'apt', 'living', st=dict(tod='night', living=1.0), rim=LAMP, cam=MC(AP(1.85, 0.9), 30, 2.4, h=1.5, lh=1.2, S=1000),
      ppl=[P('mom', AP(1.85, 0.9), id='mom', face=(1.85, 0.0), expr='terrified_call', act=_A(lambda a, s: a.press_headset(-9, None, side=-1)))], c=Z(1.0, 0.012))


def plan_rule6(F):
    RLIST(T(212), 6)
    RBIG(T(213), 6)
    # 216-219 Two minutes to midnight. Officer Mensah was back, notebook out. The headset lady sat facing the door, shoes on, crying. "He's eleven. Green coat. Broken zip. It's his birthday."
    IN(T(216), 'clock', dict(clock='11:58'), c=dict(mv='push', rate=0.03))
    MOMC = lambda expr='cry', **k: P('mom', 'couch_s', id='mom', expr=expr, **k)
    MEN = lambda **k: P('mensah', AP(3.3, 3.75), id='mensah', face=(2.35, 3.5), expr='calm_firm', **k)
    OWC = lambda **k: P('owen_pj', AP(2.95, 2.75), id='owen', face=(2.35, 3.5), expr=k.pop('expr', 'sad'), **k)
    S(T(217), 'apt', 'couch', st=K_MID, ppl=[MOMC(act=_A(lambda a, s: a.cry(-9, None))), MEN(act=_A(lambda a, s: a.take_notes(T(217) + 0.2, None)))], c=Z(1.15, 0.015, 960, 560))
    BU(T(218), 'mom', 'apt', 'couch', K_MID, cx=900, cy=620, scale=1.0, turn=0.3, expr='cry', act=_A(lambda a, s: a.cry(-9, None), lookxy(400, 520, -9)), c=BZ(0.015))
    BU(T(219), 'mom', 'apt', 'couch', K_MID, cx=1000, cy=620, scale=0.95, turn=0.35, expr='pleading', act=_A(lookxy(1500, 450, T(219))), c=BZ(0.012))
    S(W(219, 'broken'), 'apt', 'couch', st=K_MID, ppl=[MOMC('terrified_call', act=_A(lambda a, s: a.cry(-9, None), lk(-9, ('mensah', 'head')))),
                                                        MEN(act=_A(lambda a, s: a.take_notes(-9, None)))], c=Z(1.4, 0.015, 1000, 560))
    # 220-222 In the microwave door, I could see the headset lady. I could see the officer. I couldn't see me.
    MOM_R = dict(who='mom', at=(3.3, 3.05), face=(1.0, 0.3), kind='seat', seat_Y=0.46, expr='cry', id='mom')
    MEN_R = dict(who='mensah', at=(3.9, 2.62), face=(1.0, 0.0), expr='calm_firm', id='mensah', act=_A(lambda a, s: a.take_notes(-9, s.t1 + 1)))
    OW_R = dict(who='owen_pj', at=(6.62, 2.98), face=(1.0, 0.0), expr='fear', id='owen', act=_A(pose(-9, None, 0.0, refl_hide=1.0)))
    S(T(220), 'apt', 'micro', st=K_MID, cam=MICRO_CAM, mirror=[OW_R, MOM_R], c=Z(2.3, 0.012, 820, 650))          # review 1 M9: the faces in the door read
    S(T(221), 'apt', 'micro', st=K_MID, cam=MICRO_CAM, mirror=[OW_R, MOM_R, MEN_R], c=Z(2.1, 0.012, 850, 600))
    S(T(222), 'apt', 'micro', st=K_MID, cam=MICRO_CAM, mirror=[OW_R, MOM_R, MEN_R], c=Z(2.2, 0.02, 850, 610), hit=WD(222, 'see'))
    # 223-227 She wasn't ignoring me. She couldn't see me. Every secret had rubbed me out. Since dinner, the world thought I was missing. I was standing in my own kitchen.
    BU(T(223), 'mom', 'apt', 'couch', K_MID, cx=960, cy=620, scale=1.0, turn=0.2, expr='cry', act=_A(lambda a, s: a.cry(-9, None), lookxy(1300, 500, -9)), c=BZ(0.015))
    S(T(224), 'apt', 'couch', st=K_MID, ppl=[MOMC(act=_A(lambda a, s: a.cry(-9, None), lookxy(1500, 300, -9))), MEN(act=_A(lambda a, s: a.take_notes(-9, None))), OWC(expr='lonely', act=_A(lk(-9, ('mom', 'head'))))],
      c=Z(1.3, 0.015, 1000, 600))
    BU(T(225), 'owen_pj', 'apt', 'couch', K_MID, cx=960, cy=620, scale=1.0, turn=-0.2, expr='haunted', act=_A(lookxy(960, 1080, T(225) + 0.2)), c=BZ(0.015))
    S(T(226), 'apt', 'couch', st=K_MID, ppl=[MOMC(act=_A(lambda a, s: a.cry(-9, None))), MEN(act=_A(lambda a, s: a.take_notes(-9, None))), OWC(expr='lonely')], c=Z(1.05, 0.012))
    S(T(227), 'apt', 'wide', st=K_MID, cam=KIT, ppl=[P('owen_pj', 'kitchen_mid', id='owen', face=(5.3, 2.4), expr='haunted')], c=Z(1.0, 0.012))
    # 228-230 The headset lady. Listen to that. Three days, and I'd stopped calling my own mother Mom.
    BU(T(228), 'mom', 'apt', 'couch', K_MID, cx=1000, cy=620, scale=1.05, turn=0.3, expr='terrified_call', act=_A(lambda a, s: a.cry(-9, None)), c=BZ(0.015))
    BU(T(229), 'owen_pj', 'apt', 'wide', K_MID, cx=960, cy=620, scale=1.0, turn=-0.25, expr='shock', c=BZ(0.02))
    BU(T(230), 'owen_pj', 'apt', 'wide', K_MID, cx=960, cy=600, scale=1.1, turn=-0.2, expr='sad', c=BZ(0.02))
    # 231-234 So I kept rule six. "Mom. I'm here. I feel invisible." She turned her head. Like she'd heard a whisper.
    S(T(231), 'apt', 'couch', st=K_MID, ppl=[MOMC(act=_A(lambda a, s: a.cry(-9, None))), MEN(act=_A(lambda a, s: a.take_notes(-9, None))), OWC(expr='brave', path=[(T(231), AP(3.5, 2.95)), (E(231) + 0.2, AP(2.95, 2.75))])], c=Z(1.2, 0.015))
    BU(T(232), 'owen_pj', 'apt', 'couch', K_MID, cx=960, cy=600, scale=1.05, turn=-0.3, expr='brave', act=_A(lookxy(400, 560, -9)), c=BZ(0.015))
    S(W(232, 'invisible') - 0.3, 'apt', 'couch', st=K_MID, ppl=[MOMC('terrified_call', act=_A(lambda a, s: a.cry(-9, None))), MEN(act=_A(lambda a, s: a.take_notes(-9, None))), OWC(expr='brave', act=_A(lk(-9, ('mom', 'head'))))],
      c=Z(1.5, 0.015, 960, 560))
    BU(T(233), 'mom', 'apt', 'couch', K_MID, cx=960, cy=620, scale=1.05, turn=0.1, expr='terrified_call',
       act=_A(lookxy(300, 600, -9), lambda a, s: a.look_at(T(233) + 0.2, (1400, 560), None, 0.6)), c=BZ(0.015))
    BU(T(234), 'mom', 'apt', 'couch', K_MID, cx=980, cy=620, scale=1.15, turn=0.25, expr='listening_soft', act=_A(lookxy(1400, 560, -9), lambda a, s: a.listen_tilt(T(234), None, side=1, angle=14.0)), c=BZ(0.02))
    # 235-236 Midnight. My birthday.
    IN(T(235), 'clock', lambda u: dict(clock='11:59' if u < 0.3 else '12:00'), c=dict(mv='push', rate=0.03))
    IN(T(236), 'board', dict(state='birthday', k=1.0), c=dict(mv='push', rate=0.03, f=1.4, x=960, y=330))
    # 237-242 Behind the fridge, something unfolded. Up, and up, until her head bent along the ceiling. Long fingers, tapping like buttons on glass.
    #         A smile far too wide. Holding open... the red coat. "Happy birthday. She can't hear you. Only me. Button up. We're going home."
    tu = T(237) + 0.2
    B3 = lambda **k: P('blank3', 'fridge_gap', id='blank', expr='too_wide', blink=False, order=lambda t: 2.77, **k)   # in front of the fridge (2.79): she comes out of the gap BESIDE it
    unfold = lambda a, s: (a.set(-1e9, None, 0.0, b3_face=1.0), a.b3_unfold(tu, dur=max(3.0, F.e(238) - tu - 0.3)))
    S(T(237), 'apt', 'fridge', st=K_MID, ppl=[B3(act=_A(unfold))], c=Z(1.25, 0.012, 914, 640))
    S(T(238), 'apt', 'fridge', st=K_MID, ppl=[B3(act=_A(unfold))], c=Z(1.3, 0.012, 930, 600), sfx=[(E(238) - 0.5, 'ceiling_creak', -8, 0, 'inside')])
    tap = lambda t: (scr_cache['cnt'][0] - 40 * math.sin(t * 7.0), scr_cache['cnt'][1])
    BU(T(239), 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=520, scale=1.0, turn=0.0, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.02),
       sfx=[(T(239) + 0.3 + 0.28 * k, 'fingertip_tap', -12, 0, 'close') for k in range(8)])
    BU(T(240), 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=560, scale=1.35, turn=0.0, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.03), hit=WD(240, 'wide'))
    HOLD = lambda t: None
    S(T(241), 'apt', 'fridge', st=K_MID,
      ppl=[P('blank3', AP(5.32, 4.45), id='blank', expr='too_wide', blink=False, act=_A(lambda a, s: (a.set(-1e9, None, 0.0, b3_face=1.0, b3_unfold=1.0))))],
      acts=b3_coat_open('blank'), c=Z(1.0, 0.012, 920, 560))
    BU(T(242), 'blank3', 'apt', 'fridge', K_MID, cx=980, cy=560, scale=1.05, turn=0.0, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.02))
    S(W(242, 'button'), 'apt', 'fridge', st=K_MID,
      ppl=[P('blank3', AP(5.32, 4.45), id='blank', expr='too_wide', blink=False, act=_A(lambda a, s: a.set(-1e9, None, 0.0, b3_face=1.0, b3_unfold=1.0))),
           P('owen_pj', AP(5.95, 3.75), id='owen', face=(5.32, 4.45), expr='terror', act=_A(lk(-9, ('blank', 'head'))))],
      acts=b3_coat_open('blank'), c=Z(1.0, 0.012, 1000, 600))


scr_cache = {'cnt': (960, 700)}


def b3_coat_open(bid):
    """acts: form 3 holds the red coat open in front of her (toward the room), hands at its shoulders."""
    def acts(A, sh, sp):
        b = A[bid]
        x0, y0 = b.x0, b.y0
        k = b.height / 2.45
        held = (x0 + 0.42 * k, y0 - 1.05 * k, 0.62 * k)
        b.b3_hold_coat(-1e9, lambda t: held, dur=0.6, face=1)
        def d(pen, t):
            CH.draw_red_coat(pen, held[0], held[1], held[2], 0.0, 1.0, 0.0)
        return [lay_at(sh, bid, -0.02, d, 'coat_open')]
    return acts


FR = dict(st=K_MID)
CLIMAX = MC((5.62, 4.3, U), 185, 2.7, h=1.35, lh=1.2, S=850, sy=520)   # review 1 B6: the climax from the south, nothing between us and them
OW_F = AP(5.92, 4.12)          # Owen in front of the fridge when she wraps the coat round him
OW_B = AP(6.04, 4.16)          # Owen at the board (writing)
BL_F = AP(5.3, 4.47)           # form 3 just out of the gap beside the fridge
MOM_B = AP(5.62, 4.24)         # Mom between them at the end


def song_btn(t):
    """Buttons closed (0..6) in time with her song (L248: one / warm / two / snug / three / hug)."""
    F = _FILM[0]
    ws = [WD(248, w_, k) for (w_, k) in (('one', 0), ('warm', 0), ('two', 0), ('snug', 0), ('three', 0), ('hug', 0))]
    return sum(clamp((t - w_) / 0.18) for w_ in ws)


def r7_coat(drop_at=None, top_at=None):
    F = _FILM[0]
    wrap = (W(246, 'wrapped'), E(246) + 0.2)
    def held(t): return _R7['held']
    btn = lambda t: song_btn(t)
    full = lambda t: clamp((t - wrap[1] + 0.4) / 0.4) * (1.0 - clamp((t - WD(259, 'dropped') - 0.1) / 0.3))
    opn = lambda t: 1.0 - 0.6 * clamp((t - wrap[0]) / (wrap[1] - wrap[0]))
    top = lambda t: ease_in_out(clamp((t - F.t(252) - 0.2) / 1.0)) * (1.0 - clamp((t - WD(259, 'dropped')) / 0.3))
    return dict(held=held, wrap=wrap, btn=btn, full=full, opn=opn, top=top, drop=WD(259, 'dropped'))


_R7 = {}


def r7_empty(b):
    """(t) -> (cx, cy, h): the EMPTY red coat hanging from her far hand at her side (in front of her, never over him)."""
    k = b.height / 2.45
    q = (b.x0 + 0.16 * k, b.y0 - 1.08 * k, 0.8 * k)
    return lambda t: q


def r7_acts(extra=None):
    """acts for the climax shots: the coat (held open -> wrapped round him -> held out empty), plus extras."""
    def acts(A, sh, sp):
        b = A['blank']
        k = b.height / 2.45
        _R7['held'] = (b.x0 + 0.15 * k, b.y0 - 1.05 * k, 0.75 * k)
        if 'owen' not in A or sh.t0 >= WD(259, 'dropped') - 0.01:
            emp = r7_empty(b)
            b.b3_hand(-1e9, -1, lambda t: CH.coat_pts(*emp(t))['shoulder_l'], None, 0.6)     # one hand: the near one stays free
            def d(pen, t):
                cl = getattr(b.at(t), 'b3_collapse', 0.0)
                if cl > 0.02:                               # she folds: the empty coat drops with her and lies in a heap
                    cx, cy, h = emp_at[0] if emp_at else emp(t)
                    draw_fallen_coat(pen, cx, b.y0, h, ease_in_cubic(clamp(cl * 2.2)), cy)
                    return
                emp_at[:] = [emp(t)]
                cx, cy, h = emp(t); CH.draw_red_coat(pen, cx, cy, h, 0.0, 0.5, 0.0)
            emp_at = []
            L = [lay_at(sh, 'blank', -0.02, d, 'coat_empty')]
            if extra: L += [l for l in (extra(A, sh, sp) or []) if l is not None]
            return L
        o = A['owen']
        def top_to(t):                                      # held out in front of his chest, toward her (his fingers rise to it)
            cx_, cy_ = o.where(t, 'chest')
            return cx_ + 0.02 * o.height, cy_ + 0.12 * o.height      # mid-chest, in front of him: well below his chin
        cfg = r7_coat()
        L = coat_acts('owen', 'blank', top_to=top_to, empty=r7_empty(b), top_t0=_FILM[0].t(252) + 0.2, **cfg)(A, sh, sp)
        if extra: L += [l for l in (extra(A, sh, sp) or []) if l is not None]
        return L
    return acts


def draw_fallen_coat(pen, cx, y_floor, h, u=1.0, cy0=None):
    """The empty red coat falling (u 0..1) from its collar height cy0 to a flat heap on the floor line y_floor."""
    cy0 = y_floor - 1.1 * h if cy0 is None else cy0
    if u <= 0.0: CH.draw_red_coat(pen, cx, cy0, h, 0.0, 0.5, 0.0); return
    sy = 1.0 - 0.78 * u                                     # it settles: the hem on the floor, squashed flat
    pen.cv.save()
    m = skia.Matrix(); m.setScale(1.0 + 0.25 * u, sy, cx, y_floor); pen.cv.concat(m)
    CH.draw_red_coat(pen, cx, lerp(cy0, y_floor - h, u), h, 0.0, 0.8, 0.0)
    pen.cv.restore()


def fallen_coat(sp, at, h_m=0.8):
    s_ = spot_of(sp, at)
    def draw(pen, t): draw_fallen_coat(pen, s_.x, s_.y, h_m * s_.ppm, 1.0)
    lay = Layer(s_.depth, draw, 'fallen_coat', ref_depth=s_.depth)
    lay.order = sp.order_at(s_.X, s_.Yp) + 0.015
    return lay


def B3P(at=BL_F, act=None, **k):
    return P('blank3', at, id='blank', expr=k.pop('expr', 'too_wide'), blink=False,
             act=_A(lambda a, s: a.set(-1e9, None, 0.0, b3_face=1.0, b3_unfold=1.0, b3_elbow_out=1.0), act), **k)


def plan_rule7(F):
    RLIST(T(243), 7)
    RBIG(T(244), 7)
    # 246-255 She wrapped the coat around me. The buttons closed themselves, in time with her song. "One for warm..." Six closed. The song stopped.
    #         The top one waited. She held it out to me. Not touching. "Top one's yours, sweetheart. Mama keeps you. Say goodbye." My fingers rose. Tik.
    OWP = lambda expr='terror', act=None, at=OW_F, **k: P('owen_pj', at, id='owen', face=(5.0, 3.3), expr=expr, act=act, dorder=-0.7, **k)
    # review 1 B6: close on Owen and the coat; her hands stay low on HER side of it; inserts of the buttons closing one by one in time
    # with her song, the top one held out in front of his chest, his fingers rising and stopping short
    TWO = lambda: [B3P(order=1.8), OWP()]                                               # her hands on the coat IN FRONT of him (her body is beside him)
    BTN = lambda f=3.0: Z(f, 0.01, 1080, 800)                                         # the coat front: the button column
    S(T(246), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=Z(1.2, 0.012, 960, 600))
    S(T(247), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=Z(1.9, 0.015, 1040, 720))
    BU(E(247) - 0.5, 'blank3', 'apt', 'fridge', K_MID, cx=980, cy=560, scale=1.1, expr='too_wide', blink=False, light=NIGHT, act=_A(tilt(E(247) - 0.2, 10.0, 2.5)), c=BZ(0.02))
    S(W(248, 'one') - 0.15, 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=BTN(3.0))
    BU(W(248, 'three') - 0.2, 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=560, scale=1.25, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.02))
    S(W(248, 'hug') - 0.3, 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=BTN(2.8))
    BU(T(250), 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=560, scale=1.2, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.0))
    S(T(251), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=Z(3.3, 0.01, 1080, 700))
    S(T(252), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=Z(2.2, 0.015, 1020, 690))
    S(T(253), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=TWO(), acts=r7_acts(), c=Z(2.9, 0.01, 1025, 700))
    BU(T(254), 'blank3', 'apt', 'fridge', K_MID, cx=980, cy=580, scale=1.15, expr='too_wide', blink=False, light=NIGHT, act=_A(tilt(T(254) + 0.4, 14.0, 2.5)), c=BZ(0.02))
    tk = _beat_t('my_fingers_rose')
    rise = lambda a, s: a.rise_to(tk - 1.4, lambda t: s._top_btn(t) if hasattr(s, '_top_btn') else (960, 600), side=-1, dur=1.4, short_cm=8.0)
    def fingers(A, sh, sp):                                 # his fingers come out between the coat fronts and rise; they stop short
        o = A['owen']; ppc = o.height / 145.0
        def d(pen, t):
            if not hasattr(sh, '_top_btn'): return
            bx, by = sh._top_btn(t); hx, hy = o.where(t, 'hip')
            k = ease_in_out(clamp((t - (tk - 1.4)) / 1.4))
            wx, wy = lerp(hx + 0.02 * o.height, bx + 0.3 * ppc, k), lerp(hy, by + 0.105 * o.height + 2.5 * ppc, k)   # tips stop 2.5 cm short
            hero_hand(pen, 'owen_pj', wx, wy, 0.105 * o.height, 'point', 180.0 - 8.0 * k, -1, (hx - 0.01 * o.height, hy + 0.06 * o.height), None, 0.0, t)
        return [lay_at(sh, 'owen', -0.03, d, 'owen_fingers')]
    S(T(255), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=[B3P(order=1.8), OWP(expr='tempted', act=_A(lk(-9, ('owen', 'chest'))))], acts=r7_acts(extra=fingers), c=Z(2.0, 0.015, 1050, 800))
    # 256-260 "NO!" As loud as I could. Then not one more word to her. I dropped down out of the coat and ran. She was left holding a red coat with nobody in it.
    BU(T(256), 'owen_pj', 'apt', 'fridge', K_MID, cx=960, cy=600, scale=1.15, turn=-0.15, expr='shout', light=NIGHT_L, c=dict(mv='push', rate=0.0, zrate=0.03, hit=[(WD(256, 'no'), 9.0)]), hit=WD(256, 'no'))
    S(T(257), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=[B3P(order=1.8, act=lambda a, s: a.set(T(257), T(257) + 1.0, 0.3, b3_lean=-0.6)), OWP(expr='brave')], acts=r7_acts(), c=Z(1.2, 0.012, 960, 600))
    BU(T(258), 'owen_pj', 'apt', 'fridge', K_MID, cx=960, cy=600, scale=1.05, turn=-0.2, expr='set_jaw', light=NIGHT_L, c=BZ(0.015))
    S(T(259), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=[B3P(), OWP(expr='brave', act=_A(lambda a, s: a.drop_out(WD(259, 'dropped'), 2300.0, run_dur=1.2)))], acts=r7_acts(), c=Z(1.05, 0.01, 960, 545))
    S(T(260), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=[B3P(), OWP(at=AP(3.3, 3.4), expr='fear')], acts=r7_acts(), c=Z(1.35, 0.012, 940, 600))
    # 261-266 Her head turned toward where my voice had been. "Tell me where you are." Those buttons were blind. She'd never seen me. She only knew what I told her. So I stopped telling her...
    BU(T(261), 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=560, scale=1.15, expr='too_wide', blink=False, light=NIGHT,
       act=_A(lambda a, s: a.set(T(261) + 0.2, None, 0.8, h_turn=-0.45), lambda a, s: a.listen_tilt(T(261) + 0.8, None, side=-1, angle=20.0)), c=BZ(0.015))
    BU(T(262), 'blank3', 'apt', 'fridge', K_MID, cx=980, cy=560, scale=1.2, expr='too_wide', blink=False, light=NIGHT,
       act=_A(pose(-9, None, 0.0, h_turn=-0.45), lambda a, s: a.listen_tilt(-9, None, side=-1, angle=20.0)), c=BZ(0.02))
    BU(T(263), 'blank3', 'apt', 'fridge', K_MID, cx=960, cy=520, scale=1.7, expr='too_wide', blink=False, light=NIGHT, c=BZ(0.03))
    OWC2 = lambda **k: P('owen_pj', AP(2.95, 2.75), id='owen', face=(2.35, 3.5), expr=k.pop('expr', 'fear'), **k)
    S(T(264), 'apt', 'couch', st=K_MID, ppl=[P('mom', 'couch_s', id='mom', expr='cry', act=_A(lambda a, s: a.cry(-9, None))),
                                              OWC2(act=_A(lambda a, s: a.hand_to_mouth(T(264), None, side=-1, shock=False), lookxy(1300, 500, -9)))], c=Z(1.25, 0.015))
    S(T(265), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=K_MID, ppl=[B3P(act=lambda a, s: a.listen_tilt(T(265), None, side=-1, angle=24.0))], acts=r7_acts(), c=Z(1.3, 0.012, 900, 600))
    BU(T(266), 'owen_pj', 'apt', 'couch', K_MID, cx=960, cy=600, scale=1.05, turn=0.25, expr='set_jaw', light=LAMP, c=BZ(0.015))
    # 267-269 And I told my mom. She couldn't hear me. So I told again, another way.
    S(T(267), 'apt', 'couch', st=K_MID, ppl=[P('mom', 'couch_s', id='mom', expr='cry', act=_A(lambda a, s: a.cry(-9, None))),
                                              OWC2(expr='brave', act=_A(lk(T(267), ('mom', 'head')), lambda a, s: a.lean_in(T(267) + 0.3, dur=1.4, amount=0.6)))],
      c=Z(1.35, 0.015))
    BU(T(268), 'mom', 'apt', 'couch', K_MID, cx=960, cy=620, scale=1.0, turn=0.25, expr='cry', act=_A(lambda a, s: a.cry(-9, None), lookxy(1300, 520, -9)), c=BZ(0.015))
    BU(T(269), 'owen_pj', 'apt', 'couch', K_MID, cx=940, cy=600, scale=1.0, turn=0.35, expr='determined', light=LAMP, act=_A(lookxy(1600, 450, T(269) + 0.3)), c=BZ(0.015))
    # 270-273 I grabbed the fridge marker. Under FRI, I wrote: MOM IT'S OWEN I'M HERE. The marker squeaked. The Blank lunged at the sound, fingers sweeping the counter.
    OWB = lambda expr='determined', act=None: P('owen_pj', OW_B, id='owen', face=(5.95, 4.6), expr=expr, act=act, dorder=-0.7)
    S(T(270), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='birthday'), ppl=[B3P(act=lambda a, s: a.set(-9, None, 0.0, h_turn=-0.45)), OWB(act=_A(lambda a, s: a.reach_to(T(270) + 0.3, 1, scr(s.sp, 'marker'), t1=E(270) + 0.5, dur=0.5, z=-10, contact='grip', shape='grip')))],
      acts=r7_acts(), c=Z(1.6, 0.015, 1020, 700))
    hk = lambda t: clamp((t - WD(271, 'mom')) / max(0.5, WD(271, 'here') + 0.4 - WD(271, 'mom')))
    IN(T(271), 'board', lambda u, t0=T(271): dict(state='here', k=hk(t0 + u)), c=dict(mv='push', rate=0.02),
       hands=[dict(who='owen_pj', fn=lambda t: _wrist_for_tip(*_board_pen(hk(t))) + (1.0 if t > WD(271, 'mom') - 0.3 else 0.0,), size=240.0, shape='grip', side=1, sleeve_from=(2300, 1300), pen=True)],
       sfx=[(WD(271, 'mom'), 'marker_squeak', -8, 0, 'close', dict(dur=round(WD(271, 'here') + 0.4 - WD(271, 'mom'), 2)))])
    S(T(272), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='here'), ppl=[B3P(act=lambda a, s: a.set(T(272) + 0.1, None, 0.25, h_turn=0.5)), OWB(act=_A(typ(T(272), E(272), 'board', side=1)))],
      acts=r7_acts(), c=Z(1.5, 0.015, 1000, 680), sfx=[(T(272) + 0.05, 'marker_squeak', -4, 0, 'inside')])
    def lunge(a, s):
        a.set(-9, None, 0.0, b3_elbow_out=0.0)
        a.b3_lunge(T(273) + 0.1, scr(s.sp, (7.2, 4.92, U + 0.93)), scr(s.sp, (6.75, 4.92, U + 0.93)), dur=1.5, t1=E(273) + 0.5, side=1)   # the back of the counter, clear of him
    S(T(273), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='here'), ppl=[B3P(act=lunge), OWB(expr='terror', act=_A(lambda a, s: a.crouch(T(273) - 0.05, amount=1.6, t1=None, dur=0.3)))],
      acts=r7_acts(), c=Z(1.3, 0.012, 1000, 650), sfx=[(T(273) + 0.2 + 0.2 * k, 'fingertip_tap', -10, 0, 'inside') for k in range(6)])
    # 274-278 Officer Mensah read it first. "Ma'am. The board." My mom pulled off her headset. And her glasses. "Tell me. I'm listening."
    S(T(274), 'apt', 'couch', st=dict(K_MID, board='here'), ppl=[P('mom', 'couch_s', id='mom', expr='cry', act=_A(lambda a, s: a.cry(-9, None))),
                                                                  P('mensah', AP(3.3, 3.75), id='mensah', face=(5.95, 4.43), expr='focused', act=_A(lambda a, s: a.read_board(T(274), scr(s.sp, 'board'))))],
      c=Z(1.2, 0.015, 980, 560))
    BU(T(275), 'mensah', 'apt', 'couch', dict(K_MID, board='here'), cx=1000, cy=600, scale=0.95, turn=-0.3, expr='calm_firm', light=LAMP,
       act=_A(lookxy(400, 600, T(275)), lambda a, s: a.point_at(T(275) + 0.4, (1700, 300), None, side=1)), c=BZ(0.015))
    BU(T(276), 'mom', 'apt', 'couch', dict(K_MID, board='here'), cx=960, cy=620, scale=1.0, turn=0.2, expr='shock', light=LAMP, own_off=True,
       act=_A(lambda a, s: a.headset_off(T(276) + 0.15, side=1), lookxy(1400, 420, T(276))), c=BZ(0.015))
    BU(T(277), 'mom', 'apt', 'couch', dict(K_MID, board='here'), cx=960, cy=600, scale=1.1, turn=0.2, expr='shock', light=LAMP, own_off=True,
       act=_A(pose(-9, None, 0.0, hs_off=1.0), lambda a, s: a.glasses_off(T(277) + 0.1, None, side=-1), lookxy(1400, 420, T(277))), c=BZ(0.02))
    BU(T(278), 'mom', 'apt', 'couch', dict(K_MID, board='here'), cx=1000, cy=600, scale=1.05, turn=0.3, expr='listening_soft', light=LAMP, act=_A(lookxy(1500, 420, T(278))), c=BZ(0.015))
    # 279-282 So I wrote everything. THE CHAT. THE PHOTO. THE COAT. THE CAR. 2 A.M. I WISHED FOR A DIFFERENT MOM. With every word, I came back. Like a photo developing.
    items = [WD(280, w_) for w_ in ('chat', 'photo', 'coat', 'car', 'two', 'wished')]
    allk = lambda t: sum(clamp((t - x + 0.1) / (0.5 if j < 5 else 1.2)) for j, x in enumerate(items))
    S(T(279), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='here'), ppl=[B3P(act=lambda a, s: a.set(-9, None, 0.0, h_turn=0.5)), OWB(act=_A(typ(T(279), None, 'board', side=1)))],
      acts=r7_acts(), c=Z(1.6, 0.015, 1030, 700))
    IN(T(280), 'board', lambda u, t0=T(280): dict(state='all', k=allk(t0 + u)), c=dict(mv='push', rate=0.015),
       hands=[dict(who='owen_pj', fn=lambda t: _wrist_for_tip(*_board_pen_all(allk(t))) + (1.0,), size=240.0, shape='grip', side=1, sleeve_from=(2300, 1300), pen=True)],
       sfx=[(x, 'marker_squeak', -10, 0, 'close', dict(dur=0.5)) for x in items])
    BLIST(W(280, 'car'), hl=None, f=1.0, rate=0.01)
    S(T(281), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'), ppl=[B3P(act=lambda a, s: a.set(-9, None, 0.0, h_turn=0.3)), OWB(act=_A(typ(T(281), E(281), 'board', side=1)))],
      acts=r7_acts(), c=Z(1.9, 0.015, 1060, 720))
    BU(T(282), 'owen_pj', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=600, scale=1.05, turn=-0.25, expr='brave', light=LAMP, c=BZ(0.015),
       post_fn=lambda t: dict(sat=0.6 + 0.4 * clamp((t - F.t(282)) / 1.2)))
    # 283-289 The long fingers were an inch from my hood. And my mom's eyes found me. "There you are." The Blank froze. Mid-reach. Mom stepped between us, her back to that thing. She only looked at me.
    hood = lambda s: (lambda t: (s.A['owen'].where(t, 'head')[0] - 0.14 * s.A['owen'].height, s.A['owen'].where(t, 'head')[1] + 0.03 * s.A['owen'].height))
    reachh = lambda a, s: a.b3_hand(T(283), 1, hood(s), dur=1.8)
    frz = lambda a, s: (a.b3_hand(-9, 1, hood(s), dur=0.1), a.freeze(T(286), 1e6))
    S(T(283), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'), ppl=[B3P(act=reachh), OWB(expr='fear')], acts=r7_acts(), c=Z(1.7, 0.015, 980, 640))
    BU(T(284), 'mom', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=600, scale=1.1, turn=0.2, expr='relief', light=LAMP, act=_A(lookxy(1500, 600, -9), lambda a, s: a.look_at(T(284) + 0.6, (900, 560), None, 0.5)), c=BZ(0.02))
    BU(T(285), 'mom', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=600, scale=1.15, turn=0.1, expr='tender', light=LAMP, act=_A(lookxy(900, 560, -9)), c=BZ(0.02))
    S(T(286), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'), ppl=[B3P(act=frz), OWB(expr='fear')], acts=r7_acts(), c=Z(1.6, 0.0, 980, 620))
    S(T(288), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'),
      ppl=[B3P(act=frz), OWB(expr='relief', act=_A(lk(-9, ('mom', 'head')))),
           P('mom', MOM_B, id='mom', path=[(T(288) - 0.2, AP(4.7, 3.7)), (E(288) - 0.4, MOM_B)], expr='cry', act=_A(lk(-9, ('owen', 'head'))))],
      acts=r7_acts(), c=Z(1.35, 0.012, 980, 680))
    S(T(289), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'),
      ppl=[B3P(act=frz), OWB(expr='relief', act=_A(lk(-9, ('mom', 'head')))), P('mom', MOM_B, id='mom', face=OW_B[:2], expr='tender', act=_A(lk(-9, ('owen', 'head'))))],
      acts=r7_acts(), c=Z(1.9, 0.015, 1000, 640))
    # 290-296 And I looked into my mother's eyes. Real. Tired. Wet. "Green." She'd put buttons where I'd never looked. Now I was looking.
    BU(T(290), 'owen_pj', 'apt', 'fridge', dict(K_MID, board='all'), cx=980, cy=620, scale=1.05, turn=-0.3, expr='relief', light=LAMP, act=_A(lookxy(400, 420, -9)), c=BZ(0.015))
    for i, sc in ((291, 1.7), (292, 2.0), (293, 2.3)):
        BU(T(i), 'mom', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=640 + 170 * (sc - 1.7), scale=sc, turn=0.05, expr='tired_kind' if i < 293 else 'tender', light=LAMP,
           act=_A(lookxy(900, 640, -9)), c=BZ(0.02))
    BU(T(294), 'owen_pj', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=600, scale=1.15, turn=-0.25, expr='quiet_sure', light=LAMP, act=_A(lookxy(400, 420, -9)), c=BZ(0.015))
    BU(T(295), 'blank3', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=560, scale=1.3, expr='too_wide', blink=False, light=NIGHT, act=_A(lambda a, s: a.freeze(-9, 1e6)), c=BZ(0.02))
    BU(T(296), 'owen_pj', 'apt', 'fridge', dict(K_MID, board='all'), cx=960, cy=600, scale=1.2, turn=-0.25, expr='warm_smile', light=LAMP, act=_A(lookxy(400, 420, -9)), c=BZ(0.015))


def _wrist_for_tip(tx, ty, ang=140.0, sz=240.0):
    """(wrist x, wrist y, angle) of a grip hand whose marker tip writes at (tx, ty): the hand trails BELOW and RIGHT of the
    words (review 1 M7: the sleeve never covers what is being read)."""
    tip, _ = pen_geom(0.0, 0.0, ang, sz)
    return (tx - tip[0], ty - tip[1], ang)


def _board_pen(k):
    """The marker tip on the board insert while 'MOM IT'S OWEN I'M HERE' is written (k 0..1: two lines)."""
    if k < 0.55: u = k / 0.55; return (580 + 40 + 560 * u, 45 + 220)
    u = (k - 0.55) / 0.45; return (580 + 40 + 300 * u, 45 + 290)


def _board_pen_all(k):
    j = min(5, int(k)); u = k - j
    rows = [(0, 0.45), (1, 0.45), (2, 0.45), (3, 0.45), (4, 0.3), (5, 1.0)]
    y = 45 + 400 + 62 * [0, 0, 1, 1, 2, 3][j] + (62 if j == 5 and u > 0.5 else 0)
    x = 580 + 40 + (0 if j % 2 == 0 or j >= 4 else 380) + 340 * u
    return (x, y)


def plan_after(F):
    OWB = lambda expr='determined', act=None: P('owen_pj', OW_B, id='owen', face=(5.95, 4.6), expr=expr, act=act)
    # 297-302 The Blank folded in on herself, down to a flat, empty cardigan. Two black buttons rolled... and stopped at Mom's slippers.
    #         She dropped them in her jar. Tik. Tik. Lid on tight. From the empty cardigan, four little notes. Our song.
    tc = T(297) + 0.3
    S(T(297), 'apt', 'fridge', cam=CLIMAX, cam_cull=True, st=dict(K_MID, board='all'), acts=r7_acts(),
      ppl=[B3P(act=lambda a, s: a.b3_collapse(tc, dur=max(2.0, F.e(297) - tc - 0.6))), P('mom', MOM_B, id='mom', face=OW_B[:2], expr='cry', act=_A(lk(-9, ('owen', 'head')))),
           OWB(expr='relief', act=_A(lk(-9, ('mom', 'head'))))],
      c=Z(1.3, 0.012, 960, 700), sfx=[(tc, 'cardigan_collapse', -4, 0, 'inside')])
    FLOOR = MC(AP(5.4, 4.2), 200, 1.5, h=0.45, lh=0.12, S=900, sy=720)
    S(T(298), 'apt', 'wide', st=dict(K_MID, board='all'), cam=FLOOR,
      ppl=[P('mom', MOM_B, id='mom', face=OW_B[:2], expr='cry')],
      acts=lambda A, sh, sp: [flat_cardigan(sp, (5.3, 4.47, U)), fallen_coat(sp, (5.48, 4.5, U)), rolling_buttons(sp, (5.3, 4.47, U), (5.55, 4.05, U), T(298) + 0.2, dur=2.4)],
      c=Z(1.0, 0.01), sfx=[(T(298) + 0.2, 'buttons_rolling', -8, 0, 'inside', dict(dur=2.6))])
    t1, t2 = _beat_t('she_dropped_them', 0), _beat_t('she_dropped_them', 1)
    IN(T(299), 'jar', lambda u, t0=T(299): dict(state='open' if t0 + u < t2 + 0.6 else 'black', bg='sill'), c=dict(mv='push', rate=0.02),
       layers=[drop_button(930, -100, 930, 500, t1, c='#121216'), drop_button(1000, -100, 1000, 500, t2, c='#121216')],
       hands=[dict(who='mom', fn=lambda t: (1000, 80 - 140 * clamp((t - t2 - 0.1) / 0.6), 5.0, 1.0), size=420.0, shape='pinch', side=1, sleeve_from=(1500, -500))])
    IN(T(300), 'jar', dict(state='black', bg='sill'), c=dict(mv='push', rate=0.03, f=1.1), sfx=[(T(300) + 0.2, 'jar_lid', -6, 0, 'close')],
       hands=[dict(who='mom', fn=lambda t, t0=T(300): (960 + 60 * math.sin((t - t0) * 6) * (1 - clamp((t - t0) / 1.0)), 240, 0.0, 1.0 - clamp((t - t0 - 1.0) / 0.3)), size=480.0, shape='grip', side=1, sleeve_from=(1400, -600))])
    S(T(301), 'apt', 'wide', st=dict(K_MID, board='all'), cam=FLOOR,
      acts=lambda A, sh, sp: [flat_cardigan(sp, (5.3, 4.47, U)), fallen_coat(sp, (5.48, 4.5, U)), notes_layer(scr(sp, (5.3, 4.47, U + 0.05)), T(301) + 0.3, rate=1.4, slow=1.0)],
      c=Z(1.2, 0.015), sfx=[(T(301) + 0.3, 'music_box_four_notes', -8, 0, 'close')])
    # 303-308 Mom pulled out a tiny music box. "My package. That was a surprise. You'd have had it Friday." Her lock screen was me. Monday. Pointing at Barlow's window. She did look.
    IN(T(303), 'music_box', dict(bg='cardigan'), c=dict(mv='push', rate=0.02),
       hands=[dict(who='mom', fn=lambda t, t0=T(303): (960, 760 - 220 * ease_out_cubic(clamp((t - t0 - 0.2) / 0.8)), 0.0, 1.0), size=520.0, shape='grip', side=1, sleeve_from=(1300, 1500))])
    KNEEL = MC(AP(5.75, 4.1), 200, 1.8, h=1.0, lh=0.75, S=950)
    S(T(304), 'apt', 'wide', st=dict(K_MID, board='all'), cam=KNEEL, cam_cull=True,
      ppl=[P('mom', MOM_B, id='mom', kind='kneel', face=OW_B[:2], expr='tender', act=_A(lambda a, s: (a.reach_to(T(304), -1, (a.where(s.t0 + 0.05, 'chest')[0], a.where(s.t0 + 0.05, 'chest')[1] + 0.12 * a.height), t1=None, dur=0.5, z=60.0, contact='palm', shape='grip', prop='music_box'), a.hold_prop('music_box', -1, T(304), None)), lk(-9, ('owen', 'head')))),
           OWB(expr='relief', act=_A(lk(-9, ('mom', 'head'))))],
      c=Z(1.1, 0.012))
    IN(T(305), 'lock_screen', c=dict(mv='push', rate=0.02))
    IN(T(306), 'lock_screen', c=dict(mv='push', rate=0.03, f=1.4, x=1150, y=650))
    BU(T(308), 'mom', 'apt', 'fridge', dict(K_MID, board='all'), cx=980, cy=620, scale=1.0, turn=0.25, expr='tender', light=LAMP, act=_A(lookxy(1500, 560, -9)), c=BZ(0.015))
    # 309-316 Mom laid her phone face down. "No more one finger..." I didn't know her eyes... "None of this is your fault. You can always come home." She wound the music box and sang along. The real words. Her voice cracked. "Mama sees you. Say goodnight."
    AFT = dict(K_MID, board='all', laptop=0.0)
    S(T(309), 'apt', 'wide', st=AFT, cam=TWO_TABLE, rim=LAMP,
      ppl=[P('mom', 'table_mom', id='mom', expr='tender', act=_A(lambda a, s: a.set_down(T(309) + 0.2, 'cell', 1, scr(s.sp, (4.2, 2.6, U + 0.76)), dur=1.2), lk(-9, ('owen', 'head')))),
           P('owen_pj', 'table_owen', id='owen', expr='relief', act=_A(lk(-9, ('mom', 'head'))))], c=Z(1.15, 0.012))
    BU(T(310), 'mom', 'apt', 'wide', AFT, cx=1000, cy=600, scale=1.0, turn=0.35, expr='tender', light=LAMP, act=_A(lookxy(1500, 560, -9)), c=BZ(0.012))
    BU(T(311), 'owen_pj', 'apt', 'wide', AFT, cx=940, cy=620, scale=1.0, turn=-0.3, expr='sad', light=LAMP, act=_A(lookxy(400, 560, -9)), c=BZ(0.012))
    BU(T(312), 'mom', 'apt', 'wide', AFT, cx=980, cy=600, scale=1.05, turn=0.3, expr='tender', light=LAMP, act=_A(lookxy(1500, 600, -9)), c=BZ(0.015))
    S(W(312, 'always'), 'apt', 'wide', st=AFT, cam=MC(AP(5.0, 3.5), 200, 2.4, h=1.2, lh=0.8, S=850), rim=LAMP,
      ppl=[P('mom', AP(4.75, 3.45), id='mom', face=(5.3, 3.6), expr='cry', snap=True, act=_A(lambda a, s: a.hug(W(312, 'always') + 0.1, s.A['owen'], None, kneel=False))),
           P('owen_pj', AP(5.3, 3.6), id='owen', face=(4.75, 3.45), expr='relief')], c=Z(1.1, 0.012))
    S(T(313), 'apt', 'wide', st=AFT, cam=MOM_TABLE, rim=LAMP,
      ppl=[P('mom', 'table_mom', id='mom', expr='tender', act=_A(lambda a, s: a.wind_box(T(313) + 0.2, E(316) + 2)))], c=Z(1.1, 0.012))
    BU(T(314), 'mom', 'apt', 'wide', AFT, cx=980, cy=600, scale=1.0, turn=0.3, expr='tender', light=LAMP, act=_A(lambda a, s: a.wind_box(-9, None)), c=BZ(0.012))
    BU(T(316), 'mom', 'apt', 'wide', AFT, cx=1000, cy=600, scale=1.05, turn=0.3, expr='tender', light=LAMP, act=_A(lambda a, s: a.wind_box(-9, None)), c=BZ(0.012))


def narr_hands(set_down=None, typing=None, kb=(960, 760), down_xy=(1180, 820)):
    """acts for the narrator's desk now: his arms come in from below the frame (narrator_b: hands and sleeves only);
    set_down = t: the headset carried down to the desk; typing = (t0, t1)."""
    def acts(A, sh, sp):
        n = CH.Acting('narrator_b', seed=24 + sh.idx, height=1500.0).place(960, 2050)
        if typing: n.typing(typing[0], typing[1], kb)
        if set_down is not None:
            n.reach_to(set_down - 0.6, 1, (1040, 300), t1=set_down, dur=0.5, z=40.0, contact='grip', shape='grip', prop='headset')
            n.hold_prop('headset', 1, set_down - 0.6, set_down + 0.2)
            n.set_down(set_down, 'headset', 1, down_xy, dur=1.4)
        sh.actors.append(n)
        def d(pen, t):
            for sd in (-1, 1): CH.draw_arm(pen, 'narrator_b', sd, n.at(t), x=n.x0, y_feet=n.y0, height=n.height, t=t)
        return [Layer(0.9, d, 'narrator_hands', blur=0)]
    return acts


def plan_sting(F):
    # 317-321 My son is ten now. I work from home, headset on all day. Just like her. Tonight, the lid was off the jar on my desk. The jar was empty.
    NOWS = dict(lamp=0.4, tablet=0.8, street=1.0, tablet_bed=None)
    NOWD = dict(NOWS, tablet_bed='down')
    S(T(317), 'now', 'son', st=NOWS, rim=PHONE, ppl=[P('son', 'bed_sit', id='son', expr='neutral', act=_A(tabf(-9, None, (T(317), E(317)))))], c=Z(1.9, 0.012, 830, 700))
    S(T(318), 'now', 'desk', st=dict(headset='desk', jar='empty', lamp=1.0), acts=narr_hands(typing=(T(318) + 0.2, E(319))), c=Z(1.0, 0.012))
    S(T(319), 'now', 'hall', st=dict(headset='desk', jar='empty', lamp=1.0), c=Z(1.3, 0.012, 400, 760))
    IN(T(320), 'jar', dict(state='empty', bg='desk'), c=dict(mv='push', rate=0.02, f=1.05))
    IN(T(321), 'jar', dict(state='empty', bg='desk'), c=dict(mv='push', rate=0.03, f=1.35, x=760, y=640))
    # 322-326 Down the hall, my son's tablet chimed. Four little notes. Our song. I set my headset down. I opened his door.
    S(T(322), 'now', 'hall', st=dict(lamp=0.6), c=Z(1.4, 0.015, 1050, 820), sfx=[(T(322) + 0.1, 'tablet_chime', -8, 0, 'inside')])
    S(T(323), 'now', 'hall', st=dict(lamp=0.6), c=Z(1.8, 0.02, 1050, 780), acts=lambda A, sh, sp: [notes_layer((1050, 760), T(323), rate=1.6)])
    S(T(325), 'now', 'desk', st=dict(headset=None, jar='empty', lamp=1.0), acts=narr_hands(set_down=T(325) + 0.4), c=Z(1.0, 0.01))
    S(T(326), 'now', 'hall', st=dict(lamp=0.6, door=lambda t: 18.0 + 70.0 * ease_in_out(clamp((t - F.t(326) - 0.6) / 0.8))),
      cam=MC((4.15, 2.6, U), 197, 1.7, h=1.55, lh=1.1, S=900),                    # review 1 M8: from behind him (his back, his hand on the door)
      ppl=[P('narrator_b', 'son_door', id='narr', path=[(T(326) - 0.2, 'hall_mid'), (T(326) + 0.7, 'son_door')], surface='inside_quiet', expr='neutral', talk=False,
             act=_A(lambda a, s: a.reach_to(T(326) + 0.5, 1, (a.x0 + 0.25 * a.height, a.y0 - 0.55 * a.height), t1=E(326) + 0.5, dur=0.4, z=10, contact='grip', shape='grip')))],
      c=Z(1.1, 0.012), sfx=[(T(326) + 0.6, 'door_open_soft', -10, 0, 'inside')])
    # 327-328 Under the streetlight, someone waved. At the window next to his.
    S(T(327), 'now', 'window', st=NOWS, cam=NOW_POV, ppl=[P('blank2', 'lamp_spot', id='blank', hk=1.0 + CH.BLANK_TALL['sill'], expr='too_sweet', blink=False,
                                                act=_A(wavef(T(327) + 0.3, E(328) + 1, side=1), lookxy(1500, 300, -9)), order=sp_out())], c=ZO(1.6, 'lamp_spot', ody=-60, rate=0.02))
    S(T(328), 'now', 'window', st=NOWS, cam=NOW_POV, ppl=[P('blank2', 'lamp_spot', id='blank', hk=1.0 + CH.BLANK_TALL['sill'], expr='too_sweet', blink=False,
                                                act=_A(wavef(-9, None, side=1), lookxy(1500, 300, -9)), order=sp_out())], c=ZO(2.2, 'lamp_spot', ody=-80, rate=0.02))
    # 329-332 On his screen, a grey default head. "I could be your dad. What color are his eyes?" Under it, my son's answer. "I don't know."
    CHAT(T(329), msgs='dad', theme='now', show=0.0, head=0.0, c=dict(mv='push', rate=0.02, f=1.2, x=500, y=520))
    CHAT(T(330) - 0.2, msgs='dad', theme='now', show=lambda t: clamp((t - F.t(330) + 0.2) / 0.4), head=0.0, c=dict(mv='push', rate=0.015))
    CHAT(T(331), msgs='dad', theme='now', show=lambda t: 1.0 + clamp((t - F.t(331) - 0.3) / 0.4), head=0.0, c=dict(mv='push', rate=0.02, f=1.15, x=1300, y=560))
    BU(T(332), 'son', 'now', 'son', NOWS, cx=960, cy=600, scale=1.0, turn=0.25, expr='lonely', light=PHONE, act=_A(lookxy(1100, 1150, -9)), c=BZ(0.015))
    # 333-336 "Look at me. How are you, really?" He turned the tablet face down, and told me everything. Then he looked right at me. "Brown. Your eyes are brown."
    NK = lambda act=None: P('narrator_b', 'kneel', id='narr', kind='kneel', face=(6.98, 1.4), expr='neutral', talk=False, act=act)
    SON = lambda expr='neutral', act=None, **k: P('son', 'bed_sit', id='son', expr=expr, act=act, **k)
    SONCAM = MC(AP(6.72, 1.4), 320, 1.3, h=1.25, lh=0.75, S=850)          # review 1 M8: over his shoulder (his back), never a full front view
    S(T(333), 'now', 'son', st=NOWS, cam=SONCAM, ppl=[SON('lonely', act=_A(tabf(-9, None), lambda a, s: a.look_at(pdur(333, 0.6), (s.A['narr'], 'head'), None, 0.5))), NK()], c=Z(1.05, 0.012))
    tdn = T(334) + 0.4
    S(T(334), 'now', 'son', st=NOWS, cam=SONCAM,
      ppl=[SON('sad', act=_A(lambda a, s: a.tablet_down(tdn, scr(s.sp, (6.98, 1.6, U + 0.56)), side=1), lk(-9, ('narr', 'head')))), NK()], c=Z(1.1, 0.012))
    BU(T(335), 'son', 'now', 'son', NOWD, cx=960, cy=600, scale=1.0, turn=-0.2, expr='kind_smile', light=LAMP, act=_A(lookxy(700, 380, -9)), c=BZ(0.015))
    BU(T(336), 'son', 'now', 'son', NOWD, cx=980, cy=600, scale=1.1, turn=-0.25, expr='kind_smile', light=LAMP, act=_A(lookxy(700, 380, -9)), c=BZ(0.015))
    # 337-339 Face down on the bed, the tablet pinged. Once. Still waiting.
    S(T(337), 'now', 'son', st=dict(NOWD, tablet=lambda t: 0.15 + 0.7 * math.exp(-((t - WD(337, 'pinged')) / 0.4) ** 2)), c=ZO(2.6, 'tablet_bed', rate=0.02),
      sfx=[(WD(337, 'pinged'), 'tablet_ping_soft', -12, 0, 'inside')])
    S(T(339), 'now', 'window', st=NOWD, cam=NOW_POV, ppl=[P('blank2', 'lamp_spot', id='blank', hk=1.0 + CH.BLANK_TALL['sill'], expr='still_smile', blink=False, order=sp_out(),
                                                act=_A(lambda a, s: a.listen_tilt(T(339), None, side=1, angle=18.0)))], c=ZO(1.9, 'lamp_spot', ody=-60, rate=0.015))


def sp_out():
    return ST.ORDER_OUT - 1


def plan_outro(F):
    CARD(T(340), 'OKAY.\nBREATHE.', line_t={1: T(341)}, sub=None, bg=('#1c2030', '#0a0b10'))
    CARD(T(342), 'YOU CAN TURN A LIGHT ON NOW.', size=56, bg=('#2a2a30', '#121216'))
    CARD(T(343), "NONE OF THIS HAPPENED.\nNO BLANK.\nNO BARLOW'S.\nNO RED COAT.", line_t={1: WD(344, 'no'), 2: WD(344, 'no', 1), 3: WD(344, 'no', 2)},
         strikes=[(WD(344, 'no') + 0.4, 1), (WD(344, 'no', 1) + 0.4, 2), (WD(344, 'no', 2) + 0.5, 3)], size=58)
    CARD(T(345), 'THE MONSTER IS MADE UP.\nTHE TRICKS ARE REAL.', line_t={1: T(346)}, size=62)
    CARD(T(347), "NO BUTTON EYES.\nNICE PROFILE PICTURES.\nA FRIENDLY FACE.\nA CAR THAT LOOKS RIGHT.", line_t={1: T(348), 2: T(349), 3: W(349, 'car')}, size=56)
    CHECKLIST(T(350))
    CARD(T(369), "REAL LOVE NEVER ASKS FOR SECRETS.\nAND IT NEVER SAYS YOU CAN'T COME HOME.", line_t={1: T(370)}, size=52)
    PROMPT(T(371), 'return')
    CARD(T(378), 'LOOKED UP FROM YOUR SCREEN?', sub='Leave a like, so I know.', icon='thumb', icon_t=W(379, 'like'), y=600, size=56)
    CARD(T(380), CHANNEL, sub='Stories come to you... and never ask you to keep a secret.', icon='sub', icon_t=T(380), y=620, size=72)
    BU(T(382), 'mom', 'apt', 'wide', dict(tod='day', laptop=0.0), cx=960, cy=600, scale=1.0, turn=0.15, expr='warm_smile', light=DAY_L, era='outro', act=_A(lookxy(960, 420, -9)), c=BZ(0.012))
    BU(T(384), 'mom', 'apt', 'wide', dict(tod='day', laptop=0.0), cx=960, cy=760, scale=2.0, turn=0.05, expr='warm_smile', light=DAY_L, era='outro', act=_A(lookxy(960, 600, -9)), c=BZ(0.015))
    CARD(E(384) + 0.4, CHANNEL, size=72, y=540)


def plan(F):
    plan_open(F); plan_setup(F); plan_chat(F); plan_rule1(F); plan_prompt(F); plan_rule2(F); plan_rule3(F); plan_rule4(F)
    plan_rule5(F); plan_rule6(F); plan_rule7(F); plan_after(F); plan_sting(F); plan_outro(F)
    plan_globals(F)


def plan_globals(F):
    """The Button Song (our motif) by version, keyed to lines: 'box_clean' (the chat), 'box_slow' (the closet at 3 a.m.,
    winding down), 'hum_slow' (through the car window), 'sung_loop' (the windowsill, again and again), 'detuned' (under
    the climax song, stopping with one button left), 'four_notes' (the empty cardigan), 'box_real' (Mom winds it and sings
    along), 'tablet_chime' (the son's tablet, the first four notes)."""
    g = F.globals
    n = len(F.L)

    def J(i0, i1, version, level, off0=0.0, **k):
        if i1 >= n: return
        g.append(dict({'t': round(T(i0) + off0, 3), 'type': 'jingle', 'level': level, 'len': round(F.e(i1) - T(i0) - off0, 2), 'version': version}, **k))
    g.append({'t': round(T(0) + 0.2, 3), 'type': 'drone', 'level': 0.35, 'len': round(F.t(4) - T(0), 2), 'version': 'cold_open'})
    J(44, 44, 'box_clean', 0.2)
    J(101, 101, 'box_slow', 0.3)
    J(115, 115, 'hum_slow', 0.25)
    J(208, 210, 'sung_loop', 0.28, loop=True)
    J(248, 248, 'detuned', 0.18, stop_at=round(F.t(249), 3))
    J(301, 302, 'four_notes', 0.4)
    J(313, 316, 'box_real', 0.22)
    J(322, 324, 'tablet_chime', 0.35)
    # on-screen sound events the shots do not carry themselves (the mix reads them with the shots' own)
    for k, (w_, j) in enumerate((('one', 0), ('warm', 0), ('two', 0), ('snug', 0), ('three', 0), ('hug', 0))):
        g.append(_ev(WD(248, w_, j) + 0.05, 'coat_button_close', -10, 0, 'inside', index=k, of=6))
    for i0, i1 in ((172, 182), (220, 222)):
        g.append(_ev(T(i0), 'microwave_hum', -24, 0, 'inside', dur=round(F.e(i1) - T(i0) + 0.5, 2)))
    g.append(_ev(T(313) + 0.2, 'music_box_wind', -12, 0, 'close', dur=round(F.e(316) - T(313), 2)))
    g.append(_ev(T(334) + 1.0, 'tablet_face_down', -12, 0, 'inside'))



BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}


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
    ap.add_argument('--still', default=None, help='comma-separated times -> W/tests/film/still_T.jpg')
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
    if a.sheet:
        print(shot_sheets(F, a.sheet, rng=a.range, per=a.per, tile=a.tile))


