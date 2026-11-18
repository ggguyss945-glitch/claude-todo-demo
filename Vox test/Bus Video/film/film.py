"""film.py: the shot list, editor and cue sheets for "If The School Bus Stops At Midnight... DON'T GET ON" (Night Policy).

Built in the machinery of the Doctor film (now _work/film_doctor_old.py), film_bunny_ref.py, film_police_ref.py and
film_dummy_ref.py: the same engine, cast system (characters.py + characters_bus.py) and set system (sets.py +
sets_bus.py), the police header / rule cards / captions / tags, a global look with a climax ramp, and cue sheets
derived from the picture. The shot map this list follows line by line is W/shotmap.md (every timeline line -> the
picture that shows it). EVERY time in the plan is keyed to timeline.json (line starts / ends and word times): there is
no absolute time anywhere, so a re-edit of the narration moves the picture with its lines.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + TAIL)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --bench N [--shots ..]

THE OWNER'S NOTES, MADE INTO CODE:
  * Staging lives on the sets' plans (sets_bus: Grandma Della's house + yard + Larch Street on one plan in metres, the
    bus plan, the road, the school). Every figure in a set shot stands on a plan point (an anchor or (x, y[, Y])): its
    height from the px-per-metre there, feet on the floor point, draw order from sp.order_at(), light from sp.light_kw().
    Seats / kneels / floor sits come from the spot's kind (nobody stands on furniture, nothing floats).
  * Mediums are real cameras on the same plan (cam=cm(eye, look, S, sx, sy)): a cut keeps every wall, door and bus
    where it was. Prefer cuts; camera moves are short pushes while people act.
  * MISTER WHISTLESTOP is ACTIVE in every beat: tape_skip (hard cut of position + stutter frame + tracking tear),
    unfold, curl_door, grip_small, walkie_to_grin, blow_whistle, lean, look snaps. He never lip-syncs (VOICE 'W' gives
    a head bob only); the grin never moves.
  * Lip sync on character lines only (VOICE: D Della, S Sami, T Theo, X dispatcher; Mina's own quoted lines inside the
    narration are 'NQ'); narrator lines move no mouths.
  * escalate(): no "scared jiggle"; tension shows as wider eyes, raised brows, faster breath for the kids; Della grows
    stiller (a locked jaw) as the night goes on.

Shot kinds (builders B_<kind>):
  set      a set view (sets_bus bu_* builders) with figures on the plan: room 'living' | 'hall' | 'upstairs' | 'gran' |
           'sami' | 'front' | 'bus' | 'road' | 'school' | 'theo' | 'class'; view = the builder's view; cam = None (the
           view's own camera) or cm(...); set = builder kwargs; ppl = [P(who, at, ...)]; acts = f(A, shot, sp) -> [layers]
  flat     a flat set (the 1994 tape: ST.bu_tape94 / bu_class94 SetPieces with design-px anchors): set = f() -> SetPiece,
           ppl = [dict(who, x, y, h, turn, act, expr, light)]
  bust     a face close-up over a blurred set (bg=(room, view[, cam]) + set=dict(..)); busts=[..]; hands=[..]; plain=(c1, c2)
  ins      a prop insert: sets_bus bu_insert(name, kw, motion); kw = dict or f(time since the cut) -> dict; hands=[..]
  rule     the police rule card over the rules paper taped inside the front door (rule n lit)
  pause    the comment prompt: his 1994 broadcast takes over the screen (stage 'word' | 'ask')
  card     plain graphic cards (part B: the outro)
  black    black (with an optional line of text)
Plan conventions: F.cut(t, kind, **p) starts a shot that ends at the next cut. F.t(i) / F.e(i) line start / end,
F.w(i, 'word') the ASR start of a word inside line i; T(i) = F.t(i) - LEAD, W(i, 'word') = F.w(i, 'word') - LEAD,
WD(i, 'word') = the word itself. Common p keys: c=dict(mv='push'|'keys'|'hold', f, rate, x, y, keys=[(t, x, y, z, ease,
f)], hit=[t]), tags=[(t, text, x, y, style, hold)], sfx=[(t, name, gain_db, pan, space, params)], music=[(t, type,
level, len, extra)], cut='white'|'static'|'vhs'|'blink', era='now'|'1994'|'morning'|'outro', grade, post, post_fn,
focus (or focus_on=who), dof. See W/handoff/film_a.md for the helpers.
"""
import bisect, hashlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *                                                    # noqa: F401,F403
from engine import hud as H
from engine import post as _epost
from engine.core import DW, DH, CFG, clamp, lerp, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, noise1, hash01, prog, image_from
import characters as CH
import sets as ST

W = os.path.join(HERE, '_work')                                         # this film's work dir (film/_work)
ALIGN = os.path.join(W, 'align')
CUES_DIR = os.path.join(W, 'cues')
TESTS = os.path.join(W, 'tests', 'film')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
TAIL = 6.0                       # the end card holds after the last line
TITLE = "If The School Bus Stops At Midnight... DON'T GET ON"
BASE = 'If_The_School_Bus_Stops_At_Midnight'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card

PART_B = 190                       # part A = lines 0..189 (cold open .. rule 4), part B = lines 190..418
def set_retime(lines, duration): return None


def at(t): return t


def authored(t): return t


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (code, fx or None): narrator lines (N) move no mouths; Whistlestop (W) only bobs his
# head. 'NQ' = Mina's own quoted lines inside the narration ("What's the word?").
VOICE = {'della': [('D', None)], 'sami': [('S', None)], 'sami_torn': [('S', None)], 'theo': [('T', None)], 'theo_color': [('T', None)],
         'mina': [('NQ', None)], 'mina_bare': [('NQ', None)], 'whistle': [('W', None)], 'whistle94': [('W', None)], 'new_girl': []}
WHISPER = ('whisper',)


# ---------------------------------------------------------------- the story clock (header corner), keyed to lines
def _hm(h, m): return h * 60 + m


CLOCK_KEYS = [(66, _hm(0, 0)), (161, _hm(2, 10)), (196, _hm(2, 31)), (285, _hm(2, 41)), (290, _hm(2, 57)), (317, _hm(2, 58)),
              (336, _hm(2, 59)), (364, _hm(3, 0)), (386, _hm(3, 1))]
CORNER = [(0, 'LARCH STREET'), (5, '1994'), (9, 'LARKFIELD, 1994'), (22, 'NOW'), (27, 'MORNINGS'), (36, 'THE NIGHT BEFORE'), (66, None),
          (370, 'LARKFIELD ELEMENTARY'), (375, 'SEAT 22'), (386, 'MORNING'), (397, 'THAT NIGHT'), (401, CHANNEL)]


def clock_str(t):
    F = _FILM[0]
    lab = None
    for i, s in CORNER:
        if i < len(F.L) and t >= F.t(i) - LEAD: lab = (s,)
    if lab and lab[0] is not None: return lab[0]
    if F.t(79) - LEAD <= t < F.t(83) - LEAD: t = F.t(79) - LEAD          # the comment prompt: the clock stops
    ts = [F.t(i) for i, _ in CLOCK_KEYS]; ms = [m for _, m in CLOCK_KEYS]
    m = float(np.interp(t, ts, ms))
    h, mm = int(m // 60) % 24, int(m % 60)
    return '%d:%02d %s' % ((h % 12) or 12, mm, 'AM' if h < 12 else 'PM')


def header(cv, right, corner, alpha=255):
    """The police header with this film's left label."""
    left = "GRANDMA'S RULES"
    w = text(cv, left, 44, 42, 600, 13, '#8c8c98', 120 * alpha / 255, 0.24, 'left')
    text(cv, '/   ' + right, 44 + w + 16, 42, 600, 13, '#c4c4ce', 150 * alpha / 255, 0.24, 'left')
    text(cv, corner, DW - 44, 42, 600, 13, '#8c8c98', 100 * alpha / 255, 0.24, 'right')

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

# ==================================================================================================== light on figures
LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.1)                    # the house, lamps on: warm
LAMP_R = dict(rim='#ffcf8f', rim_a=60, side=1, key=0.1)
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.25)
NIGHT_L = dict(rim='#8fa6e8', rim_a=70, side=-1, key=-0.25)
DARK = dict(rim='#8fa6e8', rim_a=40, side=1, key=-0.45)                   # the 2:10 blackout
AMBER = dict(rim='#ffb040', rim_a=120, side=-1, key=-0.12)                # HIS light: headlights, sodium, the bus interior
AMBER_R = dict(rim='#ffb040', rim_a=120, side=1, key=-0.12)
HEADS = dict(rim='#ffc860', rim_a=130, side=-1, key=-0.2)                 # his headlights through the curtains
PORCH = dict(rim='#ffc888', rim_a=80, side=-1, key=-0.15)
PHONE = dict(rim='#dfeaff', rim_a=80, side=1, key=-0.35)                  # a phone screen / phone torch in the dark
MORNING = dict(rim='#fff0c8', rim_a=60, side=1, key=0.16)                 # bus 9 in the morning: warm and safe
TAPE = dict(rim='#ffffff', rim_a=40, side=-1, key=0.2)                    # the 1994 studio
WS_DARK = dict(AMBER, dark=0.55)                                          # him half sunk into the dark
WS_NIGHT = dict(rim='#ffb040', rim_a=110, side=1, key=-0.3, under='#ffb040', under_a=60)
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
                    if l['who'] == 'N' and l['en'].lstrip().startswith(('"', '\u201c')): out.append(l); break
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
        if len(self.L) > 401 and t >= self.t(401) - LEAD: cur = 'THE END'
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


# ==================================================================================================== camera
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

# ==================================================================================================== sets on the plan
ROOMS = {'living': 'bu_living', 'hall': 'bu_hall', 'upstairs': 'bu_upstairs', 'gran': 'bu_gran', 'sami': 'bu_sami', 'front': 'bu_front',
         'bus': 'bu_bus_in', 'road': 'bu_road', 'school': 'bu_school', 'theo': 'bu_theo_stop', 'class': 'bu_class94'}
_PRE = {'living': 'bu_liv_', 'hall': 'bu_hall_', 'upstairs': 'bu_up_', 'gran': 'bu_gran_', 'sami': 'bu_sami_', 'front': 'bu_ext_',
        'bus': 'bu_bus_', 'road': 'bu_road_', 'school': 'bu_sch_', 'theo': 'bu_theo_', 'class': 'bu_class_'}


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
            'heavy': 'footsteps_heavy', 'gravel': 'footsteps_gravel'}.get(surface.replace('_quiet', ''), 'footsteps_wood_inside')
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
    elif kind == 'floor':
        a.sit_floor(-1.0, None, 0.01)
    if q.get('act'): q['act'](a, sh)
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
        if torch or path:
            a.x0, a.y0, a.height = float(x), float(y), float(hh)
        P_ = m(t)
        if torch and torch.get('behind'):
            beam(pen, t, hh)
        if sil:
            CH.draw_silhouette(pen, who, x, y, hh, P_, t=t, colr=q.get('sil_c', '#04060c'), a=sil, rim=q.get('sil_rim', '#9fb6ff'),
                               rim_a=q.get('sil_rim_a', 0.5), rim_side=q.get('sil_side', 1), eyes=q.get('sil_eyes', 0.0))
        else:
            CH.draw(pen, who, x, y, hh, P_, light=lt(t) if callable(lt) else lt, t=t)
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


def prop_layer(sp, track, at, name='prop', order_dz=-0.05):
    """A resting PropTrack drawn at its plan point's depth (it disappears while a hand holds it)."""
    s = spot_of(sp, at)
    lay = Layer(s.depth, lambda pen, t: track.draw(pen, t), name, ref_depth=s.depth)
    lay.order = sp.order_at(s.X, s.Yp) + order_dz
    return lay


def ptrack(sp, name, at, dx=0.0, dy=0.0, angle=0.0):
    s = spot_of(sp, at)
    return ST and CH.PropTrack(name, s.x + dx, s.y + dy, s.ppm / 100.0, angle)

# ==================================================================================================== escalate
# The film-wide acting arc, keyed to timeline lines. NO tremble ("scared jiggle") as filler: tension shows in the eyes,
# brows and breath of the kids (Mina, Sami awake); Della grows stiller (a locked jaw) as the night goes on.
KID_ARC = [(0, 0.4), (5, 0.0), (66, 0.2), (72, 0.45), (88, 0.55), (100, 0.65), (134, 0.7), (162, 0.85), (180, 0.6), (187, 0.75),
           (212, 0.9), (243, 0.7), (272, 0.85), (297, 0.95), (364, 0.3), (386, 0.0)]
DELLA_ARC = [(0, 0.2), (22, 0.0), (53, 0.35), (66, 0.5), (130, 0.65), (246, 0.75), (370, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    return float(np.interp(t, [F.t(i) for i, _ in arc], [b for _, b in arc]))


def escalate(a, sh, who):
    if sh.kind in ('rule', 'card', 'black', 'pause', 'flat') or sh.p.get('era') in ('1994', 'outro', 'morning'): return
    if who in ('mina', 'mina_bare', 'sami', 'sami_torn'):
        k = _arc(KID_ARC, sh.t0)
        if who.startswith('sami'): k *= 0.7
        if k <= 0.02: return

        def fn(P_, t, k=k):
            P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
            per = 3.9 - 1.5 * k
            P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)
    elif who == 'della':
        k = _arc(DELLA_ARC, sh.t0)

        def fn(P_, t, k=k):
            P_.lock = max(P_.lock, 0.5 * k)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)

# ==================================================================================================== builders: sets
ROOM_RIM = {'living': NIGHT, 'hall': NIGHT, 'upstairs': NIGHT, 'gran': NIGHT, 'sami': NIGHT, 'front': NIGHT, 'bus': AMBER, 'road': NIGHT,
            'school': AMBER, 'theo': NIGHT, 'class': TAPE}
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



def B_set(F, sh):
    """A set view with figures on the plan (see the module docstring)."""
    p = sh.p
    sp = make_set(p['room'], p['view'], p.get('cam'), **p.get('set', {}))
    sh.sp = sp
    rim = p.get('rim', ROOM_RIM.get(p['room']))
    L, A, I = [], {}, {}
    sh.A = A                                  # acts can reach actors placed before them (s.A['mina'])
    ppl = list(p.get('ppl', []))
    for k, q in enumerate(ppl):
        lay, a, info = figure(F, sh, sp, q, k, rim)
        L.append(lay); key = q.get('id', q['who']); A[key] = a; I[key] = info
        info['layer'] = lay
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
    cam = scam(sh, sp.info.get('cam_env'), p.get('c'))
    grade = p.get('grade', sp.grade)
    sh.A = A
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


def B_bust(F, sh):
    """A face close-up over a blurred, darkened set: p who, bg=(room, view[, cam]) + set=dict(..), cx, cy, scale, turn,
    h_turn (or a framing preset), act, expr, light; busts=[dict(who, cx, cy, scale, act, expr, light, depth)] more faces;
    hands=[dict(who, fn, size, shape, side, sleeve_from, depth)]; plain=(c1, c2) a plain gradient background instead."""
    p = sh.p
    who = p['who']
    if p.get('bg'):
        bg = p['bg']
        sp = make_set(bg[0], bg[1], bg[2] if len(bg) > 2 else None, **p.get('set', {}))
        dimmed(sp, p.get('bg_dim', 0.28))
        # a close-up's background is behind the face: near set pieces (a crowd cut-out, a door frame at arm's length)
        # would be drawn over the face, so they are left out
        layers = [l for l in sp if _draw_order(l) >= p.get('bg_near', 1.3)]
        lens = None; grade = p.get('grade', sp.grade); sfx_fn = sp
    else:
        c1, c2 = p.get('plain', ('#1c2030', '#0c0e16'))
        layers = [Layer(4.0, lambda pen, t, c1=c1, c2=c2: pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, [c1, c2]), 'plain_bg',
                        cache='film:plain:%s:%s' % (c1, c2), bounds=(-1200, -900, 3120, 1980))]
        sp = None; lens = None; grade = p.get('grade', 'face_close'); sfx_fn = None
    fr = BUST_FRAMES['default'][sh.idx % 4]
    cx, cy, sc = p.get('cx', fr[0]), p.get('cy', fr[1]), p.get('scale', fr[2])
    tr, ht = p.get('turn', 0.0), p.get('h_turn', 0.0)
    base = lambda a, s: a.set(s.t0 - 3, None, 0.1, turn=tr, h_turn=ht)
    act = p.get('act')
    lay, a = bust_layer(F, sh, who, cx, cy, sc, lambda a_, s: (base(a_, s), act and act(a_, s)), expr=p.get('expr'),
                        light=p.get('light', ROOM_RIM.get((p.get('bg') or ['x'])[0], LAMP)), seed=p.get('seed', 0), blink=p.get('blink'))
    sh.A = {who: a}
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
        extra.append(l2); sh.A[b.get('id', b['who'])] = a2
    for hd in p.get('hands', []):
        extra.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand'), held_pen=hd.get('pen', False)))
    if p.get('acts'):
        extra += [l for l in (p['acts'](sh.A, sh, None) or []) if l is not None]
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
    sp = ST.bu_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
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


# ==================================================================================================== builders: flat sets (the 1994 tape)
def B_flat(F, sh):
    """A flat SetPiece (the 1994 tape / classroom: design-px anchors, no plan) with figures placed in design px."""
    p = sh.p
    sp = p['set']()
    L = []
    sh.A = {}
    for k, q in enumerate(p.get('ppl', [])):
        who = q['who']
        a = CH.Acting(who, seed=q.get('seed', 0) + 7 * k + sh.idx * 3, height=q['h'], expr=q.get('expr', 'neutral'))
        a.place(q['x'], q['y'])
        if q.get('turn') is not None: a.face(q['turn'])
        if q.get('act'): q['act'](a, sh)
        if q.get('talk', True):
            for l in F.voice_lines(sh.t0, sh.t1, VOICE.get(who, [])):
                a.talk([(l['t'], l['end'], l['en'])], intensity=1.0)
        sh.actors.append(a)
        m = _Memo(a)
        lt = q.get('light', TAPE)

        def draw(pen, t, m=m, who=who, q=q, lt=lt):
            CH.draw(pen, who, q['x'], q['y'], q['h'], m(t), light=lt, t=t)
        L.append(Layer(q.get('depth', 0.99), draw, 'f%d_%s' % (k, who), blur=0))
        sh.A[q.get('id', who)] = a
    if p.get('acts'):
        L += [l for l in (p['acts'](sh.A, sh, sp) or []) if l is not None]
    c = dict(p.get('c') or dict(mv='push', rate=0.015))
    c.setdefault('free', True)
    cam = scam(sh, None, c)
    return Spec(list(sp) + L, cam, getattr(sp, 'lens', None), p.get('grade', getattr(sp, 'grade', None)), 1.0, 0.0, fx=_fx(sp, p), hud=p.get('hud'))


# ==================================================================================================== rule cards
# The paper Grandma tapes inside the front door: the card text is the narration's words; the key clause is starred.
RULE_TEXT = {1: "At midnight, turn off every light that faces the street. *Take our name off anything he can see from the road.* He can only call the names he can read.",
             2: "If he calls your name, *never answer.* Never say \"here\" to him. If one of us calls you, look first. Only answer a face you know.",
             3: "If anyone says I sent them, *they have to say our word.* You never say it first. Never say it where anyone else can hear.",
             4: "If the lights go out, find Sami and *hold his hand.* Don't let go until the lights come back.",
             5: "If he gets inside, lock yourselves in my room. *Open the door only for the word.*",
             6: "If he takes one of you, *don't chase him on foot.* Come get me. We meet him at his last stop.",
             7: "*Never get on his bus.* Not for anybody. Not even for Sami.",
             8: "*Sit with the one who sits alone.* Ask their name."}

def _rule_marks(F, sh, n):
    """[(t0, t1, [(x0, x1, baseline_y), ...])]: for each narration line read over rule card n, where its words sit on
    the card (the card's own wrap: engine.hud.rule_card), so the hud can mark the sentence being read."""
    import re
    lines = H.wrap_rich(RULE_TEXT[n].upper(), 800, 31, 760, 0.045)
    plain = [l.replace('*', '') for l in lines]
    full = ' '.join(plain)
    norm, idx = [], []
    for j, ch in enumerate(full):
        if ch.isalnum() or ch == ' ':
            norm.append(ch.lower()); idx.append(j)
    norm = ''.join(norm)
    starts = []; acc = 0
    for pl in plain:
        starts.append(acc); acc += len(pl) + 1
    out = []
    for l in F.lines_in(sh.t0, sh.t1):
        q = re.sub(r'[^a-z0-9 ]', '', l['en'].lower()).strip()
        q = re.sub(r' +', ' ', q)
        if len(q) < 4 or l['t'] < sh.t0 or l['end'] > sh.t1 + 0.3: continue
        k = norm.find(q)
        if k < 0: continue
        a, b = idx[k], idx[k + len(q) - 1] + 1
        segs = []
        for i, pl in enumerate(plain):
            ls, le = starts[i], starts[i] + len(pl)
            if b <= ls or a >= le: continue
            wl = H.text_width(pl, 800, 31, 0.045)
            x_ = DW / 2 - wl / 2
            x0 = x_ + H.text_width(pl[:max(a, ls) - ls], 800, 31, 0.045)
            x1 = x_ + H.text_width(pl[:min(b, le) - ls], 800, 31, 0.045)
            segs.append((x0, x1, 648 + i * 44))
        if segs: out.append((l['t'], l['end'], segs))
    return out



def B_rule(F, sh):
    """The police rule card over the rules paper taped inside the front door (blurred, dimmed; rule n lit; rule 8 in
    Mina's hand); the sentence being read is underlined as it is read."""
    p = sh.p
    n = p['n']
    sp = ST.bu_insert('rules', dict(show=7, hl=n, eighth=(n == 8)) if n == 8 else dict(show=7, hl=n))
    t0 = sh.t0
    marks = _rule_marks(F, sh, n)

    def hud(cv, t):
        tt_ = t - t0
        if tt_ > 0.35:
            pen = Pen(cv)
            for (ta, tb, segs) in marks:
                if not (ta - 0.1 <= t <= tb + 0.45): continue
                k_ = clamp((t - ta + 0.1) / 0.3) * (1.0 - clamp((t - tb - 0.1) / 0.35))
                sw = ease_in_out(clamp((t - ta + 0.05) / max(0.4, tb - ta)))
                tot = sum(x1 - x0 for (x0, x1, y_) in segs) or 1.0
                run = sw * tot
                for (x0, x1, y_) in segs:
                    pen.fill(rrect(x0 - 10, y_ - 30, (x1 - x0) + 20, 40, 8), '#ffffff', 26 * k_)
                    L_ = clamp(run, 0.0, x1 - x0); run -= (x1 - x0)
                    if L_ > 0: pen.fill(rrect(x0, y_ + 9, L_, 4, 2), H.RED, 230 * k_)
        H.rule_card(cv, n, RULE_TEXT[n], tt_, total=8 if n == 8 else 7, icon=None, scrim=0.35)
    cam = scam(sh, None, dict(mv='push', rate=0.012, free=True))

    def fx(t):
        d = dict(blur=6, dim=0.45)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(list(sp), cam, None, 'bu_ins', 1.0, 0.0, fx=fx, hud=hud)


# ==================================================================================================== the comment prompt
def _glove_cursor(pen, x, y, s, a=255, press=0.0, curl=0.0):
    """A white glove, open palm (four segments per finger: one knuckle too many), tilted up-left: the prompt's cursor;
    curl 0..1 folds ALL four fingers evenly (a grip), press squeezes a little more. Never one finger alone."""
    cv = pen.cv
    k = clamp(curl + 0.25 * press)
    cv.save(); cv.translate(x, y); cv.rotate(-28); cv.scale(s, s)
    pen.fill(oval(6, 46, 30, 12), '#000000', 70 * a / 255, blur=5)
    for fx_, ln in ((-13, 50), (-4, 60), (5, 57), (14, 46)):
        L_ = ln * (1.0 - 0.55 * k)
        pen.fill(rrect(fx_ - 4.2, -L_ + 18, 8.4, L_, 4.2), '#e2ded2', a)
        for j in range(1, 4):
            yy = 18 - L_ * j / 4.0
            pen.seg((fx_ - 3.2, yy), (fx_ + 3.2, yy), 1.2, '#a9a495', a)
    pen.fill(rrect(-19, 10, 40, 34, 13), '#e2ded2', a)
    cv.save(); cv.translate(-18, 22); cv.rotate(-35 + 30 * k)
    pen.fill(rrect(-5, -26, 10, 30, 5), '#e2ded2', a)                     # the thumb
    cv.restore()
    pen.fill(rrect(-17, 40, 34, 12, 4), '#d6d0c0', a)
    cv.restore()


def B_pause(F, sh):
    """The comment prompt as HIS broadcast taking over the screen: the 1994 title card (tracking, VHS) and his questions
    on it, one beat per line: stage 'word' ONE WORD / IN THE COMMENTS (a comment box types '...'); stage 'ask' HE KNOWS
    YOUR NAME. -> DOES THAT MAKE HIM YOUR FRIEND? -> two buttons YES / NO, a white glove cursor drifting onto YES while NO
    pulses. p: stage, t_q (the question), t_yn (the buttons)."""
    p = sh.p
    sp = ST.bu_tape94('title', track=0.45)
    t0 = sh.t0
    st_ = p.get('stage', 'word')

    def hud(cv, t):
        pen = Pen(cv)
        u = t - t0
        a0 = clamp(u / 0.25)
        pen.fill(rect(0, 0, DW, 1080), '#06070c', 205 * a0)
        if st_ == 'word':
            text(cv, 'ONE WORD', 960, 470, 900, 112, '#ffd23a', 255 * clamp(u / 0.2), 0.06, 'center', 0.6)
            k2 = clamp((u - 0.45) / 0.3)
            text(cv, 'IN THE COMMENTS', 960, 560, 800, 46, '#ffffff', 240 * k2, 0.22, 'center', 0.5)
            kb = clamp((u - 0.8) / 0.3)
            if kb > 0:
                pen.fill(rrect(660, 640, 600, 84, 18), '#ffffff', 230 * kb)
                dots = '.' * (1 + int(u * 3) % 3)
                text(cv, 'Add a comment' + dots, 700, 694, 500, 30, '#7a7f8c', 255 * kb, 0.02, 'left')
        else:
            tq, tyn = p.get('t_q', t0 + 1.4), p.get('t_yn', t0 + 2.8)
            if t < tq + 0.2:
                text(cv, 'HE KNOWS YOUR NAME.', 960, 500, 800, 78, '#ffffff', 255 * clamp(u / 0.2) * (1 - clamp((t - tq) / 0.2)), 0.1, 'center', 0.6)
            if t >= tq:
                kq = clamp((t - tq) / 0.25)
                text(cv, 'DOES THAT MAKE HIM', 960, 380, 800, 54, '#ffffff', 245 * kq, 0.14, 'center', 0.5)
                text(cv, 'YOUR FRIEND?', 960, 470, 900, 96, '#ffd23a', 255 * kq, 0.06, 'center', 0.6)
            if t >= tyn:
                kb = ease_out_back(clamp((t - tyn) / 0.35))
                pulse = 0.5 + 0.5 * math.sin((t - tyn) * 7.0)
                for x_, lab, c_ in ((700, 'YES', '#2a2a30'), (1220, 'NO', '#c8202a')):
                    w_, h_ = 300 * kb, 120 * kb
                    pen.fill(rrect(x_ - w_ / 2, 640 - h_ / 2 + 60, w_, h_, 22 * kb), '#ffffff' if lab == 'YES' else c_, 235 * clamp(kb))
                    if lab == 'NO': pen.glow(x_, 700, 220, '#ff3030', 50 * pulse)
                    text(cv, lab, x_, 718, 900, 64 * max(0.01, kb), c_ if lab == 'YES' else '#ffffff', 255 * clamp(kb), 0.08, 'center', 0.6)
                g = ease_in_out(clamp((t - tyn - 0.3) / 1.2))
                _glove_cursor(pen, lerp(1500, 760, g), lerp(980, 742, g), 1.5, 255 * clamp((t - tyn - 0.2) / 0.3),
                              press=clamp((t - tyn - 1.6) / 0.15) * (1 - clamp((t - tyn - 1.9) / 0.2)))
    cam = scam(sh, None, dict(mv='push', rate=0.01, free=True))

    def fx(t):
        d = dict((sp.fx(t) if hasattr(sp, 'fx') else None) or {})
        if t - t0 < 0.12: d['glitch'] = 0.9; d['static'] = 0.4
        return d
    return Spec(list(sp), cam, None, getattr(sp, 'grade', None), 1.0, 0.0, fx=fx, hud=hud)


def B_card(F, sh):
    """A plain graphic card: p text (lines split by \\n), sub, bg (c1, c2). Part B replaces the outro's cards with the
    real ones (the lamp, the advice list, the comment, the like, the subscribe call, the next-episode bus, the end)."""
    p = sh.p
    c1, c2 = p.get('bg', ('#141824', '#07080c'))
    layers = [Layer(4.0, lambda pen, t: pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, [c1, c2]), 'card_bg', blur=0)]

    def hud(cv, t):
        a = clamp((t - sh.t0) / 0.4)
        lines = (p.get('text') or '').split('\n')
        for k, s in enumerate(lines):
            text(cv, s, 960, 500 + k * 80 - (len(lines) - 1) * 40, 1600, p.get('size', 64), '#ffffff', 240 * a, 0.12, 'center', 0.8)
        if p.get('sub'): text(cv, p['sub'], 960, 640 + (len(lines) - 1) * 40, 1600, 30, '#c8ccd8', 200 * a, 0.25, 'center', 0.5)
    return Spec(layers, scam(sh, None, dict(mv='push', rate=0.01, free=True)), None, 'neutral', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=hud)

def B_black(F, sh):
    p = sh.p

    def hud(cv, t):
        if p.get('text'):
            u = t - sh.t0
            a = clamp(u / 0.5) * (1 - clamp((u - (sh.d - 0.6)) / 0.5))
            text(cv, p['text'], 960, 560, 900, p.get('size', 64), '#ffffff', 255 * a, 0.12, 'center', 0.6)
    return Spec([], None, None, 'neutral', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=hud)



# ==================================================================================================== the outro (part B)
OUTRO_STOPS = [("KNOWING YOUR NAME", "DOESN'T MAKE SOMEONE SAFE"), ("PICK A FAMILY", "CODE WORD TONIGHT"), ("THE GROWN-UP", "SAYS IT FIRST"),
               ("IT SLIPS OUT?", "CHANGE IT"), ("NO RIDE, FROM ANYONE,", "WITHOUT A YES FROM HOME"), ('"HURRY. JUST YOU. OUR SECRET."', "THAT'S WHEN YOU TELL"),
               ("POST THE SMILE", "NOT THE SCHOOL, THE BUS, OR THE STREET"), ("TOMORROW, THANK YOUR DRIVER", "BY NAME")]


def _octagon(cx, cy, r):
    return poly([(cx + r * math.cos(math.radians(22.5 + 45 * k)), cy + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)])


def _bus9_icon(pen, x, y, s, a=255, door=0.0, arm=0.0, flash=0.0, t=0.0):
    """Bus 9 side-on (facing right), flat and warm: body, windows, the DELLA driver at the wheel, folding door at the front,
    the stop arm behind the driver (arm 0 folded flat .. 1 swung out at the lens), the red lights (flash 0..1)."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    pen.fill(oval(0, 8, 300, 14), '#000000', 60 * a / 255, blur=6)
    pen.fill(rrect(-300, -170, 600, 160, 26), '#e8b21e', a)                      # body
    pen.fill(rrect(-300, -170, 600, 24, 12), '#f2c84a', a)
    pen.fill(rect(-300, -62, 600, 10), '#1d1a16', a)                              # the black rub rails
    pen.fill(rect(-300, -40, 600, 6), '#1d1a16', a)
    for k in range(6):                                                            # side windows
        pen.fill(rrect(-270 + k * 70, -140, 56, 56, 8), '#2c3a52', a)
        pen.fill(rrect(-266 + k * 70, -136, 22, 48, 6), '#ffffff', 26 * a / 255)
    dw = 54 * (1.0 - 0.75 * clamp(door))                                          # the folding door (front, right)
    pen.fill(rrect(170, -150, 60, 140, 6), '#f7e0a0' if door > 0.05 else '#2c3a52', a)
    pen.fill(rect(172, -148, dw / 2, 136), '#3a4a62', a); pen.fill(rect(228 - dw / 2, -148, dw / 2, 136), '#3a4a62', a)
    pen.fill(rrect(236, -150, 56, 70, 10), '#2c3a52', a)                           # windshield
    pen.fill(rrect(292, -120, 20, 100, 6), '#d8a018', a)                           # the nose
    for wx in (-190, 180):                                                        # wheels
        pen.fill(oval(wx, -6, 42, 42), '#1a1816', a); pen.fill(oval(wx, -6, 18, 18), '#8a8a90', a)
    for lx in (-292, 284):                                                        # the red flashers
        on = flash * (0.5 + 0.5 * math.sin(t * 12.0 + (0 if lx < 0 else math.pi)))
        pen.fill(oval(lx, -158, 9, 9), '#ff2a2a' if on > 0.5 else '#7a1e1e', a)
        if on > 0.5: pen.glow(lx, -158, 60, '#ff3030', 90 * on * a / 255)
    if arm > 0.01:                                                                # the stop arm, swung out toward us
        k = ease_out_back(clamp(arm))
        cv.save(); cv.translate(150, -95); cv.scale(max(0.05, k), 1.0)
        pen.fill(_octagon(0, 0, 62), '#ffffff', a); pen.fill(_octagon(0, 0, 56), '#c8202a', a)
        cv.restore()
    text(cv, 'BUS 9', -40, -76, 900, 22, '#1d1a16', a, 0.2, 'center', 0.0)
    cv.restore()


def _house_door(pen, x, y, s, a=255, light=1.0):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    pen.fill(rect(-200, -420, 400, 420), '#c9b28c', a)                            # the wall
    pen.fill(poly([(-230, -420), (0, -560), (230, -420)]), '#6a3a2a', a)          # the roof
    pen.fill(rrect(-70, -300, 140, 300, 10), '#5a3a5a', a)                         # the door
    pen.fill(oval(45, -150, 8, 8), '#e8c060', a)
    pen.glow(-120, -330, 140, '#ffd890', 120 * light * a / 255)                     # the porch light: on
    pen.fill(oval(-120, -330, 12, 16), '#fff2c0', a * light)
    cv.restore()


def _ice_truck(pen, x, y, s, a=255, t=0.0):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    pen.fill(rrect(-260, -230, 380, 220, 18), '#e8ecf2', a)                       # the box
    pen.fill(rrect(120, -170, 130, 160, 18), '#d8dde6', a)                        # the cab
    pen.fill(rrect(150, -160, 80, 60, 8), '#1c2436', a)
    pen.fill(rrect(-230, -200, 200, 90, 8), '#1c2436', a)                         # the serving window, dark
    for k in range(9):                                                            # bulbs round the window: some dead
        on = 0.0 if k in (2, 6) else 0.55 + 0.45 * math.sin(t * 5.0 + k)
        c_ = ('#ff6a8a', '#ffd23a', '#7ad8ff')[k % 3]
        pen.fill(oval(-226 + k * 25, -214, 6, 6), c_, a * (0.3 + 0.7 * on))
        if on > 0.6: pen.glow(-226 + k * 25, -214, 30, c_, 60 * on * a / 255)
    pen.fill(poly([(-80, -230), (-50, -330), (-20, -230)]), '#e8c890', a)        # the cone on the roof
    pen.fill(oval(-50, -335, 34, 30), '#f2b8c8', a)
    for wx in (-170, 170):
        pen.fill(oval(wx, -6, 38, 38), '#1a1816', a)
    pen.fill(rrect(-262, -12, 516, 10, 4), '#ffffff', 160 * a / 255)               # snow on the bumper
    cv.restore()


def B_outro(F, sh):
    """The outro, brief and warm (p mode, keys = word times): 'nohim' (the 1994 tape, crossed out), 'tricks' (every trick is
    real: three cards), 'route' (bus 9's morning route; each stop is one piece of advice, big and legible as it is said),
    'yes' (the comment prompt returns: YES... exactly what he wanted), 'like' (bus 9 stops at your door), 'subscribe' (its
    stop arm swings out: SUBSCRIBE), 'next' (an ice cream truck in the snow), 'end' (NIGHT POLICY)."""
    p = sh.p
    mode = p['mode']
    t0 = sh.t0
    K = p.get('keys', {})
    bgc = {'nohim': ('#14121a', '#060508'), 'tricks': ('#1a1420', '#08060a'), 'route': ('#ffe6b8', '#f2b878'), 'yes': ('#0a0b10', '#020203'),
           'like': ('#ffe2b0', '#f0a868'), 'subscribe': ('#ffe2b0', '#f0a868'), 'next': ('#0c1426', '#03050c'), 'end': ('#07080c', '#000000')}[mode]
    L = [Layer(3.0, lambda pen, t: pen.linear(rect(-600, -400, 3120, 1880), 0, -400, 0, 1480, list(bgc)), 'card_bg',
               cache='film:obg:%s' % (bgc,), bounds=(-600, -400, 2520, 1480))]

    def hud(cv, t):
        u = t - t0
        pen = Pen(cv)
        fin = clamp(u / 0.3)
        if mode == 'nohim':
            tx = K.get('x', t0 + 1.0)
            pen.fill(rrect(560, 330, 800, 380, 26), '#151515', 255 * fin)          # the VHS cassette
            for cx_ in (760, 1160):
                pen.fill(oval(cx_, 470, 70, 70), '#2a2a2a', 255 * fin); pen.fill(oval(cx_, 470, 26, 26), '#e8e8e8', 255 * fin)
            pen.fill(rrect(620, 560, 680, 120, 10), '#f4ecd6', 255 * fin)          # the label
            text(cv, 'RIDE RIGHT WITH', 960, 600, 800, 26, '#c8202a', 255 * fin, 0.2, 'center', 0.0)
            text(cv, 'MISTER WHISTLESTOP!  1994', 960, 650, 900, 36, '#1d1a16', 255 * fin, 0.08, 'center', 0.0)
            k = clamp((t - tx) / 0.35)
            if k > 0:                                                             # the red marker X, two strokes
                for (x0, y0, x1, y1, d0) in ((600, 330, 1320, 710, 0.0), (1320, 330, 600, 710, 0.45)):
                    kk = clamp((k * 0.9 - d0 * 0.5) / 0.5)
                    if kk > 0: pen.seg((x0, y0), (lerp(x0, x1, kk), lerp(y0, y1, kk)), 26, '#d8262e', 235)
        elif mode == 'tricks':
            text(cv, 'EVERY TRICK HE USED IS REAL', 960, 250, 900, 52, '#ffd23a', 255 * fin, 0.08, 'center', 0.6)
            cards = ['HE KNEW MY NAME', 'HE SOUNDED LIKE GRANDMA', 'HURRY. JUST YOU. OUR SECRET.']
            for k_, s_ in enumerate(cards):
                tk = K.get('k%d' % k_, t0 + 0.4 * (k_ + 1))
                kk = ease_out_back(clamp((t - tk) / 0.35))
                if kk <= 0: continue
                y_ = 420 + k_ * 150
                pen.fill(rrect(960 - 520 * kk, y_ - 52, 1040 * kk, 104, 18), '#f4ecd6', 245 * clamp(kk))
                text(cv, s_, 960, y_ + 16, 900, 46, '#1d1a16', 255 * clamp(kk), 0.06, 'center', 0.0)
        elif mode == 'route':
            ks = K['stops']; n = len(ks)
            cur = max([i for i in range(n) if t >= ks[i]] or [0])
            pen.fill(rect(0, 820, 1920, 260), '#7a8a5a', 255)                      # the verge
            pen.fill(rect(0, 840, 1920, 90), '#4a4a50', 255)                       # the road
            for k_ in range(24): pen.fill(rect(k_ * 90 - (u * 40) % 90, 882, 46, 6), '#f2e2a0', 200)
            xs = [160 + i * (1600 / (n - 1)) for i in range(n)]
            for i, x_ in enumerate(xs):                                           # the stops: a little sign each; a check once passed
                pen.fill(rect(x_ - 3, 760, 6, 80), '#5a5a60', 255)
                pen.fill(_octagon(x_, 744, 22), '#c8202a' if i == cur else ('#2a7a3a' if i < cur else '#8a8a90'), 255)
                text(cv, '%d' % (i + 1) if i >= cur else 'OK', x_, 752, 900, 18, '#ffffff', 255, 0.0, 'center', 0.0)
            tprev = ks[cur]
            xb = lerp(xs[max(0, cur - 1)], xs[cur], ease_in_out(clamp((t - tprev + 0.05) / 0.6))) if cur > 0 else lerp(-300, xs[0], ease_out_cubic(clamp(u / 0.8)))
            _bus9_icon(pen, xb - 120, 880, 0.42, 255, door=clamp((t - tprev - 0.5) / 0.3) * (1.0 - clamp((t - tprev - 1.6) / 0.3)), t=t)
            a1, a2 = OUTRO_STOPS[cur]
            ka = clamp((t - tprev) / 0.25)
            pen.fill(rrect(160, 170, 1600, 430, 36), '#fffaf0', 235 * ka)          # the advice card: big, legible as it is said
            pen.line(rrect(160, 170, 1600, 430, 36), 6, '#e8b21e', 255 * ka)
            text(cv, 'STOP %d' % (cur + 1), 960, 250, 900, 34, '#c8202a', 255 * ka, 0.3, 'center', 0.0)
            text(cv, a1, 960, 380, 900, 76 if len(a1) < 24 else 58, '#1d1a16', 255 * ka, 0.04, 'center', 0.0)
            show2 = True if cur != 5 else t >= K.get('tell', tprev + 1.5)
            if show2:
                k2 = clamp((t - (tprev if cur != 5 else K.get('tell', tprev)) - 0.2) / 0.25)
                text(cv, a2, 960, 500, 900, 60 if len(a2) < 30 else 46, '#c8202a' if cur == 5 else '#3a5a8a', 255 * ka * k2, 0.06, 'center', 0.0)
        elif mode == 'yes':
            tp, tw = K.get('press', t0 + 0.6), K.get('wanted', t0 + 2.0)
            text(cv, 'YOU SAID:', 960, 360, 900, 44, '#ffffff', 230 * fin, 0.22, 'center', 0.5)
            g = clamp((t - tw) / 0.2)
            for x_, lab in ((700, 'YES'), (1220, 'NO')):
                lit = lab == 'YES'
                c_ = '#ffb040' if (lit and g > 0) else ('#ffffff' if lit else '#3a3a44')
                pen.fill(rrect(x_ - 150, 520, 300, 120, 22), c_, 235 * fin)
                text(cv, lab, x_, 604, 900, 64, '#1d1a16' if lit else '#8a8a90', 255 * fin, 0.08, 'center', 0.0)
            gx = lerp(1500, 760, ease_in_out(clamp((t - t0) / 0.6)))
            _glove_cursor(pen, gx, 642, 1.5, 255 * fin, press=clamp((t - tp) / 0.12) * (1 - clamp((t - tp - 0.3) / 0.2)))
            if g > 0:
                text(cv, "THAT'S EXACTLY WHAT HE WANTED.", 960, 800, 900, 58, '#ffb040', 255 * g, 0.06, 'center', 0.6)
                if (u * 8.0) % 1.0 < 0.3: CH.ws_tracking(pen, 0, 480 + 200 * math.sin(u * 3.0), 1920, 90, 0.7, t)
        elif mode in ('like', 'subscribe'):
            pen.fill(rect(0, 860, 1920, 220), '#5a5a62', 255)                     # the street
            pen.fill(rect(0, 840, 1920, 24), '#c8c0b0', 255)                       # the kerb
            _house_door(pen, 1500, 842, 1.15, 255)
            ts = K.get('stop', t0 + 0.4)
            if mode == 'like':
                xb = lerp(-500, 1060, ease_out_cubic(clamp((t - t0) / 1.0)))
                _bus9_icon(pen, xb, 920, 1.0, 255, door=clamp((t - t0 - 1.0) / 0.4), t=t)
                k = ease_out_back(clamp((t - ts) / 0.35))
                if k > 0:
                    pen.fill(rrect(560 - 230 * k, 200, 460 * k, 150, 30), '#ffffff', 240 * clamp(k))
                    text(cv, 'LIKE', 560, 300, 900, 90 * max(0.05, k), '#c8202a', 255 * clamp(k), 0.08, 'center', 0.0)
                    th = K.get('theo', ts + 0.6)
                    k2 = clamp((t - th) / 0.3)
                    text(cv, "IF YOU'D HAVE SAT WITH THEO", 560, 410, 900, 36, '#1d1a16', 255 * k2, 0.1, 'center', 0.0)
            else:
                ta = K.get('arm', t0 + 0.3)
                ka = clamp((t - ta) / 0.45)
                _bus9_icon(pen, 1060, 920, 1.0, 255, door=1.0, arm=ka, flash=clamp((t - ta) / 0.2), t=t)
                if ka > 0.6:
                    text(cv, 'SUB', 1210, 805, 900, 30, '#ffffff', 255 * clamp((ka - 0.6) / 0.3), 0.05, 'center', 0.0)
                    text(cv, 'SCRIBE', 1210, 838, 900, 24, '#ffffff', 255 * clamp((ka - 0.6) / 0.3), 0.05, 'center', 0.0)
                td = K.get('door', ta + 1.5)
                kd = clamp((t - td) / 0.3)
                pen.fill(rrect(330, 200, 860, 150, 30), '#ffffff', 240 * fin)
                text(cv, 'SUBSCRIBE', 760, 300, 900, 90, '#c8202a', 255 * fin, 0.08, 'center', 0.0)
                text(cv, 'SO THE NEXT ONE STOPS AT YOUR DOOR', 760, 420, 900, 36, '#1d1a16', 255 * kd, 0.1, 'center', 0.0)
        elif mode == 'next':
            pen.fill(rect(0, 820, 1920, 260), '#dfe6f0', 255)                     # snow on the street
            for k_ in range(70):                                                   # falling snow
                sx = (hash01(k_, 3) * 1920 + 30 * math.sin(u * 0.8 + k_)) % 1920
                sy = (hash01(k_, 7) * 1080 + u * (60 + 50 * hash01(k_, 9))) % 1080
                pen.fill(oval(sx, sy, 3 + 3 * hash01(k_, 5), 3 + 3 * hash01(k_, 5)), '#ffffff', 200)
            tk = K.get('truck', t0 + 0.5)
            xt = lerp(2300, 1200, ease_out_cubic(clamp((t - tk) / 1.6)))
            _ice_truck(pen, xt, 900, 1.0, 255, t)
            for k_ in range(4):                                                    # its song: notes drifting off the speaker
                ph = (u * 0.6 + k_ * 0.25) % 1.0
                text(cv, '♪', xt - 60 - 220 * ph, 640 - 160 * ph, 900, 54, '#f2b8c8', 220 * (1 - ph) * clamp((t - tk) / 0.5), 0.0, 'center', 0.0)
            text(cv, 'NEXT TIME', 960, 200, 900, 46, '#ffffff', 230 * fin, 0.4, 'center', 0.6)
            kw_ = clamp((t - K.get('winter', t0 + 3.0)) / 0.3)
            text(cv, 'THE ICE CREAM TRUCK IN WINTER', 960, 280, 900, 40, '#a8c8ff', 230 * kw_, 0.12, 'center', 0.5)
            kd = clamp((t - K.get('dont', t0 + 4.0)) / 0.2)
            if kd > 0: text(cv, "DON'T GO OUTSIDE.", 960, 440, 900, 96, '#d8262e', 255 * kd, 0.06, 'center', 0.8)
        elif mode == 'end':
            text(cv, CHANNEL, 960, 520, 900, 120, '#ffffff', 255 * fin, 0.14, 'center', 0.6)
            text(cv, TITLE.upper(), 960, 620, 900, 30, '#c8ccd8', 200 * clamp((u - 0.4) / 0.4), 0.12, 'center', 0.4)
    return Spec(L, scam(sh, None, dict(mv='push', rate=0.008, free=True)), None, 'neutral', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=hud)


BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}

# ==================================================================================================== spaces + per-shot cues
SPACE = {'living': 'inside', 'hall': 'inside', 'upstairs': 'inside', 'gran': 'inside', 'sami': 'inside', 'front': 'outside', 'bus': 'bus',
         'road': 'car', 'school': 'outside', 'theo': 'outside', 'class': 'classroom'}


def shot_space(s):
    if s.kind in ('rule', 'black', 'card', 'outro'): return None
    if s.kind == 'pause': return 'tv'
    if s.kind == 'flat': return 'vhs'
    if s.kind == 'ins': return 'close'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return {'front': 'outside', 'bus': 'bus', 'road': 'car', 'school': 'outside'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('1994', 'outro', 'morning'): return s.p['era']
    if s.kind in ('rule', 'card', 'black', 'pause'): return s.kind
    if s.kind == 'flat': return '1994'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if room in ('front', 'theo'): return 'outside'
    if room in ('bus', 'road'): return 'bus'
    if room == 'school': return 'school'
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
    if sh.kind == 'rule':
        n = sh.p['n']
        tm = H.rule_times(RULE_TEXT[n])
        sh.sfx.append(_ev(sh.t0 + tm['pop'], 'ui_pop', 0, 0, 'close'))
        if not p.get('recall'):
            sh.sfx.append(_ev(sh.t0 + tm['type0'], 'typing', -6, 0, 'close', dur=round(tm['type1'] - tm['type0'], 2), cps=14))
            sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.75})
            sh.music.append({'t': round(sh.t0, 3), 'type': 'riser', 'level': 0.5, 'len': 3.5})
            sh.sfx.append(_ev(sh.t0 + 0.02, 'paper_flutter', -10, 0, 'close'))
        else:
            sh.sfx.append(_ev(sh.t0 + 0.05, 'stinger', -6, 0, None, kind='recall'))
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

# ==================================================================================================== the global look
EXPO = {'ins': -0.03}


def glob_fx(F, sh, t, fx):
    """Per-frame global effects (keyed to lines): cut flashes ('white', 'static', 'vhs' = a tracking tear, 'blink' = the
    lights blinking); the house slowly going HIS amber as the night goes on (his headlights at L67 -> rule 5); grain that
    rises with the night; the climax ramp (rule 7, L286 .. the defeat, L369): amber edge pulses on the whistle's tempo,
    less colour, more grain; the 1994 tape, the mornings and the outro clean and warm; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'vhs' and u < 0.16: fx['glitch'] = max(fx.get('glitch', 0.0), 0.95 * (1 - u / 0.16)); fx['static'] = 0.2 * (1 - u / 0.16)
    elif c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'blink' and u < 0.12: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - u / 0.12)
    ek = EXPO.get(sh.kind, 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('1994', 'outro', 'morning') or sh.kind in ('rule', 'black', 'card', 'pause', 'flat')
    if not clean:
        ui = 0.5 if sh.kind == 'ins' else 1.0
        room = sh.p.get('room') or (sh.p.get('bg') or [''])[0]
        if room in ('living', 'hall', 'upstairs', 'gran', 'sami'):
            k = 0.22 * clamp((t - F.t(67)) / max(1.0, F.t(193) - F.t(67)))
            if t > F.t(370): k *= 1.0 - clamp((t - F.t(370)) / 3.0)
            if k > 0.004: fx['mix'] = ('bu_amber', k * ui)
        g = 0.05 + 0.1 * clamp((t - F.t(66)) / max(1.0, F.t(286) - F.t(66)))
        fx['grain'] = max(fx.get('grain', 0.0), g)
        if len(F.L) > 369 and F.t(286) - LEAD <= t < F.t(369) + 1.5:
            ramp = clamp((t - F.t(286)) / 3.0) * (1.0 - clamp((t - F.t(369) - 0.5) / 1.0))
            bpm = lerp(70, 132, clamp((t - F.t(286)) / max(1.0, F.t(360) - F.t(286))))
            ph = ((t - F.t(286)) * bpm / 60.0) % 1.0
            beat = math.exp(-ph * 9.0)
            if 'flash' not in fx:
                fx['flash'] = _epost.Spill(0.3 * ramp * clamp(beat) * ui, side=-1.0 if sh.idx % 2 else 1.0, color=(1.0, 0.72, 0.25), reach=0.8)
            fx['sat'] = fx.get('sat', 1.0) * (1.0 - 0.22 * ramp)
            fx['grain'] = fx.get('grain', 0.0) + 0.08 * ramp
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)

# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names): the house at night (warm early,
    then dead quiet), the street at night (crickets, the streetlight's buzz), HIS bus idling at the kerb from L67 until it
    pulls away (L238), the 1994 tape hiss, bus 9 driving (L246-L289), the school lot (wind, the flag rope), the morning."""
    D = F.duration
    n = len(F.L)
    t = lambda i: F.t(min(i, n - 1))
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(0.0, t(5) - 0.2, 'ambience_night', -16, 'outside', crickets=0.3, wind=0.4)
    bed(t(5) - 0.1, t(22) - 0.1, 'tape_hiss', -18, 'vhs')
    bed(t(22) - 0.1, t(66) - 0.1, 'room_tone', -14, 'inside', kind='house_evening')
    bed(t(66) - 0.1, t(190) - 0.1, 'room_tone', -10, 'inside', kind='house_night')
    bed(t(66) - 0.1, t(243), 'ambience_night', -20, 'outside', crickets=0.25, wind=0.5, through_walls=True)
    bed(t(67), t(238) + 3.0, 'bus_idle', -22, 'outside', far=True, kind='his', through_walls=True)
    bed(t(190) - 0.1, t(243) - 0.1, 'room_tone', -8, 'inside', kind='house_dead')
    bed(t(246) - 0.1, t(290) - 0.1, 'bus_drive', -14, 'bus', kind='bus9')
    bed(t(290) - 0.1, t(386) - 0.1, 'ambience_night', -16, 'outside', wind=0.7, flag_rope=True)
    bed(t(386) - 0.1, D, 'room_tone', -14, 'inside', kind='morning')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.6), (2, 0.75), (3, 0.9), (4, 0.7), (5, 0.35), (12, 0.45), (15, 0.6), (17, 0.5), (20, 0.55), (22, 0.15), (29, 0.3), (36, 0.15),
    (48, 0.35), (52, 0.6), (56, 0.35), (59, 0.45), (66, 0.55), (67, 0.7), (72, 0.8), (74, 0.9), (76, 0.85), (78, 0.95), (79, 0.3),
    (83, 0.6), (88, 0.75), (92, 0.85), (100, 0.9), (103, 0.95), (105, 0.8), (111, 0.9), (114, 1.0), (117, 0.85), (122, 0.6),
    (126, 0.7), (134, 0.8), (143, 0.9), (146, 1.0), (147, 0.8), (153, 0.9), (154, 0.6), (157, 0.5), (162, 0.85), (173, 1.0),
    (180, 0.7), (187, 0.95), (190, 0.6), (202, 0.75), (207, 0.9), (212, 1.0), (223, 0.9), (231, 1.0), (239, 0.7), (246, 0.75),
    (257, 0.6), (265, 0.85), (274, 0.95), (279, 1.0), (284, 0.95), (286, 0.75), (297, 0.85), (305, 0.9), (312, 1.0), (318, 0.8),
    (327, 0.9), (333, 0.7), (342, 0.8), (353, 0.95), (358, 1.0), (364, 0.9), (369, 0.6), (371, 0.3), (377, 0.2), (386, 0.1),
    (394, 0.35), (395, 0.5), (398, 0.2), (401, 0.1)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY if i < len(F.L)]
    pts.append([round(F.duration, 2), 0.0])
    return pts


HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(3, -0.6, 0.5), (73, -0.2, 0.9), (112, -0.2, 0.8), (141, -0.2, 0.7), (163, -0.3, 0.9), (212, -0.6, 0.6), (231, -0.5, 0.5),
             (279, -0.5, 0.5), (312, -0.5, 0.5), (358, -0.6, 0.6)]
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

# ==================================================================================================== the shot plan
def plan(F):
    plan_film(F)


def plan_film(F):
    plan_open(F)
    plan_tape(F)
    plan_family(F)
    plan_rule1(F)
    plan_pause(F)
    plan_rule2(F)
    plan_rule3(F)
    plan_rule4(F)
    if 'plan_partb' in globals():
        globals()['plan_partb'](F)
    else:
        F.cut(T(PART_B), 'black', text='PART B: lines %d..%d (see W/shotmap.md)' % (PART_B, len(F.L) - 1), size=40)
    plan_globals(F)


# ==================================================================================================== tools
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
    rows = []
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
        txt = ' / '.join('[%d%s] %s' % (l['i'], '' if l['who'] == 'N' else ' ' + l['who'], l['en']) for l in ls) or '(no line)'
        hdr = '#%d %s %s  %.2f-%.2f (%.2fs)' % (sh.idx, sh.kind, sh.p.get('room') or sh.p.get('name') or sh.p.get('who') or sh.p.get('mode') or '',
                                              sh.t0, sh.t1, sh.d)
        tl = [hdr] + _wrap_txt(txt, 118)[:3]
        band = np.full((16 * len(tl) + 6, row.shape[1], 3), 24, np.uint8)
        for j, s_ in enumerate(tl):
            cv2.putText(band, s_, (5, 14 + 16 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 230, 255) if j == 0 else (235, 235, 235), 1, cv2.LINE_AA)
        rows.append(np.vstack([row, band, np.full((4, row.shape[1], 3), 70, np.uint8)]))
        F._built.clear()
    paths = []
    for s0 in range(0, len(rows), per):
        p_ = '%s_%03d.jpg' % (prefix, ks[s0])
        cv2.imwrite(p_, np.vstack(rows[s0:s0 + per]), [cv2.IMWRITE_JPEG_QUALITY, 84]); paths.append(p_)
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
    return lambda a, s: [f(a, s) for f in fns if f]


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


# set states (the prop / light continuity of the shot map)
LIV_EVE = dict(lamp=1.0, ceil=1.0, backpack='window')                      # the evening before: lamps on, SAMI on the backpack
LIV_NIGHT = dict(lamp=0.0, ceil=0.0, hall=0.5, backpack='wall', walkie=True)  # after "Lights off" (the street side dark)
LIV_HEADS = dict(LIV_NIGHT, heads=1.0)                                     # his headlights through the curtains
LIV_BLACK = dict(lamp=0.0, ceil=0.0, hall=0.0, backpack='wall', blackout=True, walkie=True)
HALL_NIGHT = dict(hall=0.35, porch=0.0)
FRONT_HIS = dict(his=True, his_heads=1.0, his_win=1.0, letters=0.0, porch=0.0)   # after he arrives (letters already off)


def ws(at, act=None, light=AMBER, **k):
    """Mister Whistlestop on a set (full figure)."""
    return P('whistle', at, light=light, act=act, **k)


def skip_to(*keys):
    """Tape-skip keys [(t, at[, pose])] on the shot's set plan: at = anchor / plan point (his drawn height follows the
    px-per-metre there). A first key off frame: at = ('off', x, y)."""
    def f(a, s):
        ks = []
        for k in keys:
            tk, at = k[0], k[1]
            if isinstance(at, tuple) and at and at[0] == 'off':
                d = dict(x=at[1], y=at[2], h=a.height)
            else:
                sp_ = spot_of(s.sp, at)
                d = dict(x=sp_.x, y=sp_.y, h=CH.height_px('whistle', sp_.ppm))
            if len(k) > 2: d.update(k[2])
            ks.append((tk, d))
        a.tape_skip(ks)
    return f


def wlook(t0, target, snap=True, dur=0.08):
    return lambda a, s: a.look_at(t0, target, dur=dur, snap=snap)


def wsay(*ivs): return lambda a, s: a.say(list(ivs))


def hands_over(who, fn, size, shape='open', side=1, sleeve_from=None, depth=0.9, light=None):
    return dict(who=who, fn=fn, size=size, shape=shape, side=side, sleeve_from=sleeve_from, depth=depth)


def slide(t0, t1, p0, p1, ang0, ang1=None, a=1.0, ease=ease_out_cubic, extra=None):
    """A hand path for hand_layer: wrist from p0 to p1 between t0 and t1 (eased), angle ang0 -> ang1."""
    ang1 = ang0 if ang1 is None else ang1

    def fn(t):
        u = ease(clamp((t - t0) / max(1e-3, t1 - t0)))
        r = (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u), lerp(ang0, ang1, u), a)
        return extra(t, r) if extra else r
    return fn


def ws_hands(sides=(1, -1), light=AMBER, depth=None):
    """A layer drawing his gloves over everything nearer than him (the gloves round a doorframe)."""
    def acts(A, sh, sp):
        a = A['whistle']
        lay = Layer(depth if depth is not None else 0.3, lambda pen, t: CH.draw_whistle_hands(pen, a, t, sides, light), 'ws_hands', blur=0)
        lay.order = -10.0
        return [lay]
    return acts


def tagc(t, s, style='red', x=960, y=170, hold=2.2): return (t, s, x, y, style, hold)


def toward(a, side, pt, t0, reach=0.38):
    """A hand target on the way to pt that the arm can actually reach (handing something across a gap: the arm stops at
    full stretch instead of the hand floating off the wrist)."""
    sx, sy = a.where(t0, 'shoulder_l' if side > 0 else 'shoulder_r')
    d = math.hypot(pt[0] - sx, pt[1] - sy); m = reach * a.height
    if d <= m: return pt
    return (sx + (pt[0] - sx) * m / d, sy + (pt[1] - sy) * m / d)


# ==================================================================================================== COLD OPEN (0-8)
def plan_open(F):
    t, e, C = F.t, F.e, F.cut
    # 0 "If the school bus stops outside your house at midnight, and the driver knows your name... don't get on."
    C(T(0), 'set', room='front', view='house', set=dict(his=True, his_heads=1.0, his_win=1.0, porch=0.0, letters=1.0), rim=AMBER,
      c=dict(mv='push', f=1.0, rate=0.03), sfx=[(T(0) + 0.35, 'air_brakes', -2, -0.2, 'outside'), (T(0), 'bus_idle', -10, 0, 'outside', dict(dur=6.0, kind='his'))])
    C(W(0, 'driver'), 'bust', who='whistle', bg=('front', 'curb'), set=dict(his=True, his_heads=1.0, his_win=1.0), cx=900, cy=760, scale=0.85,
      turn=0.6, light=WS_DARK, act=_A(pose(-9, None, 0.1, h_turn=0.5), wlook(WD(0, 'knows') - 0.05, (1500, 420)), wlook(WD(0, 'name') + 0.1, (960, 520))),
      sfx=[(WD(0, 'knows') - 0.05, 'neck_tick', -4, 0, 'outside'), (WD(0, 'name') + 0.1, 'neck_tick', -2, 0, 'outside')], c=dict(mv='push', rate=0.0, zrate=0.03))
    C(W(0, "don't"), 'set', room='front', view='curb', set=dict(his=True, his_heads=1.0, his_door=lambda tt: ease_in_out(clamp((tt - WD(0, "don't")) / 0.6))),
      rim=AMBER, ppl=[ws('his_step', act=_A(pose(-9, None, 0.1, ws_bend=0.25), lambda a, s: a.reach_far(WD(0, 'get') - 0.1, -1, (980, 640), dur=0.5)))],
      sfx=[(WD(0, "don't"), 'bus_door_fold', -2, 0, 'outside')], c=dict(mv='push', f=1.05, rate=0.05))
    # 1 "If it sounds like your grandma at the door... ask for the family word."
    C(T(1), 'set', room='hall', view='door', set=dict(HALL_NIGHT, frost=1.0, porch=1.0),
      ppl=[P('mina', 'peephole_eye', expr='hush_fear', act=_A(lambda a, s: a.reach_to(s.t0 + 0.2, 1, scr(s.sp, 'knob'), dur=0.6, contact='grip', shape='grip', z=30.0)))],
      sfx=[(T(1) + 0.15 + k * 0.32, 'knock_door', -2 + 2 * (k == 2), 0, 'inside', dict(kind='glass', n=1, index=k)) for k in range(3)],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(W(1, 'ask'), 'bust', who='mina', bg=('hall', 'door'), set=dict(HALL_NIGHT, frost=1.0, porch=1.0), expr='hush_fear', cx=1050, cy=640, scale=0.82,
      turn=-0.45, light=PORCH, act=_A(lambda a, s: a.look_at(s.t0, (300, 420), dur=0.3), blinks(W(1, 'word') + 0.2)))
    # 2 "And if he knows it... don't open the door."
    C(T(2), 'set', room='front', view='frame', set=dict(FRONT_HIS, letters=1.0, porch=1.0), rim=AMBER,
      ppl=[ws((-4.74, -0.25), face=(-4.48, -0.03), act=_A(pose(-9, None, 0.1, ws_hands_front=3, ws_bend=0.12),
                                                       lambda a, s: a.curl_door(s.t0 + 0.15, 1, scr(s.sp, (-4.5, -0.03, 1.75)), dur=0.8),
                                                       lambda a, s: a.curl_door(s.t0 + 0.55, -1, scr(s.sp, (-4.5, -0.03, 1.3)), dur=0.8)))],
      sfx=[(T(2) + 0.4, 'glove_creak', -6, -0.3, 'outside')], c=dict(mv='push', f=1.0, rate=0.03))
    C(W(2, "don't"), 'set', room='hall', view='doorclose', set=dict(HALL_NIGHT, frost=1.0, porch=1.0), rim=PORCH,
      acts=lambda A, sh, sp: [hand_layer('mina', slide(WD(2, "don't") - 0.05, WD(2, "don't") + 0.25, (430, 1250), (600, 830), -150, -160), 330, 'grip', 1,
                                         sleeve_from=(250, 1500))],
      sfx=[(WD(2, "don't") + 0.25, 'deadbolt', 0, -0.3, 'inside', dict(kind='throw'))], c=dict(mv='push', f=1.0, rate=0.02, hit=[WD(2, "don't") + 0.25]))
    # 3 W "I know your name! That makes us friends!"  (the TV voice) - a tape-skip closer on "that"
    C(T(3), 'bust', who='whistle', bg=('front', 'porch'), set=dict(FRONT_HIS, porch=1.0), cx=960, cy=820, scale=0.8, light=AMBER, cut='vhs',
      act=_A(pose(-9, None, 0.1, h_tilt=8.0)), c=dict(mv='push', rate=0.0, zrate=0.02))
    C(W(3, 'that'), 'bust', who='whistle', bg=('front', 'porch'), set=dict(FRONT_HIS, porch=1.0), cx=1000, cy=900, scale=1.15, light=AMBER, cut='vhs',
      act=_A(pose(-9, None, 0.1, h_tilt=-10.0)), sfx=[(W(3, 'that'), 'tape_skip', -2, 0, None)], c=dict(mv='push', rate=0.0, zrate=0.03))
    # 4 "That's Mister Whistlestop."  by his bus under the streetlight; a flicker and he is at the mailbox
    C(T(4), 'set', room='front', view='street', set=dict(FRONT_HIS, letters=1.0, street=ST.bu_flicker(WD(4, 'whistlestop'))), rim=AMBER,
      ppl=[ws('his_step', act=skip_to((-9, 'his_step'), (WD(4, 'whistlestop') + 0.1, 'mailbox', dict(h_tilt=10.0))))],
      tags=[tagc(WD(4, 'mister'), 'MISTER WHISTLESTOP', 'red', 960, 170, 2.0)], c=dict(mv='push', f=1.0, rate=0.02))
    # 5 "A bus-safety cat from a 1994 kids' show."
    C(T(5), 'flat', set=lambda: ST.bu_tape94('full'), cut='vhs', era='1994',
      ppl=[dict(who='whistle94', x=860, y=860, h=CH.height_px('whistle94', 290.0), turn=-0.15, act=lambda a, s: a.host(s.t0 + 0.1, s.t1 + 0.5))],
      tags=[tagc(WD(5, '1994'), 'CHANNEL 6  /  1994', 'pill', 960, 170, 2.0)], music=[(T(5), 'jingle', 0.6, 3.0, dict(version='bright_tv'))])
    # 6 "Tonight, he took my little brother."
    C(T(6), 'set', room='bus', view='seat4', set=dict(kind='his', seat_lit={4: 1.0, 22: 1.0}, drive=6.0), rim=AMBER,
      ppl=[P('sami', 'seat4_win', kind='seat', expr='dazed', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'window4', dy=-40), dur=0.5),
                                                               lambda a, s: a.reach_to(s.t0 + 0.3, -1, scr(s.sp, 'window4'), dur=0.6, contact='palm', shape='flat', z=20.0)))],
      sfx=[(T(6), 'bus_rumble', -10, 0, 'bus', dict(dur=2.0))], c=dict(mv='push', f=1.0, rate=0.02))
    # 7 "All he needed was his name."
    C(T(7), 'ins', name='chalkboard', c=dict(mv='push', rate=0.05))
    # 8 "And I gave it to him."
    C(T(8), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_NIGHT, expr='guilt', cx=960, cy=640, scale=0.85, light=PHONE,
      act=_A(lambda a, s: a.look_at(s.t0, (960, 1000), dur=0.3), blinks(E(8) - 0.2)), c=dict(mv='push', rate=0.0, zrate=0.02))


# ==================================================================================================== THE 1994 TAPE (9-21)
def plan_tape(F):
    t, e, C = F.t, F.e, F.cut
    H94 = CH.height_px('whistle94', 290.0)

    def host(act=None, x=860, turn=-0.15):
        return dict(who='whistle94', x=x, y=860, h=H94, turn=turn, act=act or (lambda a, s: a.host(s.t0 + 0.05, s.t1 + 0.5)))
    # 9 "In 1994, every school in Larkfield rolled out the TV cart for one tape."
    C(T(9), 'set', room='class', view='cart', set=dict(content='title', tv=0.0), era='1994', rim=TAPE, c=dict(mv='push', f=1.0, rate=0.02),
      tags=[tagc(WD(9, 'larkfield'), 'LARKFIELD, 1994', 'pill', 960, 170, 2.4)], sfx=[(T(9) + 0.3, 'cart_squeak', -8, 0.2, 'classroom', dict(dur=1.8))])
    C(W(9, 'for'), 'set', room='class', view='tv', set=dict(content='title'), era='1994', rim=TAPE, c=dict(mv='push', f=1.0, rate=0.06),
      sfx=[(W(9, 'for') + 0.2, 'vcr_insert', -4, 0, 'classroom')])
    # 10-11 "Ride Right with Mister Whistlestop." "Channel 6."
    C(T(10), 'flat', set=lambda: ST.bu_tape94('title'), era='1994', music=[(T(10), 'jingle', 0.8, 4.0, dict(version='title'))],
      tags=[tagc(WD(11, 'channel'), 'CHANNEL 6', 'pill', 960, 170, 1.6)], c=dict(mv='push', rate=0.012))
    # 12 "A cat, taller than the cardboard bus behind him."
    C(T(12), 'flat', set=lambda: ST.bu_tape94('full'), era='1994', ppl=[host()], c=dict(mv='push', rate=0.01))
    # 13 "Crooked yellow top hat."  14 "Silver whistle."  15 "And a grin too wide for his face... that never moves."
    C(T(13), 'bust', who='whistle94', plain=('#5ab0e0', '#2a78b8'), era='1994', cx=960, cy=1010, scale=0.7, light=TAPE, grade='bu_vhs94',
      act=_A(pose(-9, None, 0.1, h_tilt=-8.0)), c=dict(mv='push', rate=0.0, zrate=0.02, y=420))
    C(T(14), 'bust', who='whistle94', plain=('#5ab0e0', '#2a78b8'), era='1994', cx=960, cy=300, scale=0.75, light=TAPE, grade='bu_vhs94',
      act=_A(lambda a, s: a.set(s.t0 - 1, None, 0.1, ws_whistle=0.0), lambda a, s: a.set(s.t0 + 0.15, None, 0.45, ws_whistle=1.0)),
      c=dict(mv='push', rate=0.0, zrate=0.02, y=640))
    C(T(15), 'bust', who='whistle94', plain=('#5ab0e0', '#2a78b8'), era='1994', cx=960, cy=560, scale=1.1, light=TAPE, grade='bu_vhs94',
      c=dict(mv='push', rate=0.0, zrate=0.025))
    C(W(15, 'never'), 'bust', who='whistle', bg=('front', 'porch'), set=dict(FRONT_HIS, porch=1.0), cx=960, cy=560, scale=1.1, light=AMBER, cut='vhs',
      sfx=[(W(15, 'never'), 'tape_warble', -6, 0, None)], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 16 "Not even when he talks."
    C(T(16), 'flat', set=lambda: ST.bu_tape94('full'), era='1994', cut='vhs',
      ppl=[host(lambda a, s: (a.host(s.t0, s.t1 + 0.5), a.say([(s.t0 + 0.25, s.t1 - 0.1, 'ride right ride right')])))],
      c=dict(mv='push', rate=0.0, f=1.35, x=880, y=470))
    # 17 W "Write your name, your school and your bus on your card! Hold it up to the camera!"
    C(T(17), 'flat', set=lambda: ST.bu_tape94('full'), era='1994', ppl=[host(lambda a, s: (a.host(s.t0, s.t1 + 0.5),
                                                                                          a.reach_far(WD(17, 'card') - 0.3, -1, (1200, 380), dur=0.45, z=260.0, shape='point')))],
      c=dict(mv='push', rate=0.012))
    C(W(17, 'hold'), 'bust', who='whistle94', plain=('#5ab0e0', '#2a78b8'), era='1994', cx=960, cy=640, scale=0.9, light=TAPE, grade='bu_vhs94',
      act=_A(pose(-9, None, 0.1, ws_bend=0.0), lambda a, s: a.set(s.t0 + 0.1, None, 0.9, ws_bend=0.25, h_tilt=10.0)),
      c=dict(mv='push', rate=0.0, zrate=0.05))
    # 18 "The kids hold up their cards."
    C(T(18), 'flat', set=lambda: ST.bu_tape94('kids'), era='1994', c=dict(mv='push', rate=0.015))
    # 19 W "Ride right, kids!"
    C(T(19), 'flat', set=lambda: ST.bu_tape94('full'), era='1994',
      ppl=[host(lambda a, s: (a.host(s.t0, s.t1 + 0.4), a.blow_whistle(E(19) - 0.05, 'two', -1)))],
      sfx=[], c=dict(mv='push', rate=0.012))
    # 20 "The tape was pulled that fall."  the CRT clicks off
    C(T(20), 'set', room='class', view='tv', set=dict(content='full'), era='1994', rim=TAPE, c=dict(mv='push', f=1.0, rate=0.02))
    C(W(20, 'pulled', off=0.1), 'set', room='class', view='tv', set=dict(content='full', tv=0.0), era='1994', rim=TAPE, cut='blink',
      sfx=[(W(20, 'pulled', off=0.1), 'tv_off', -2, 0, 'classroom')], c=dict(mv='push', f=1.0, rate=0.02))
    # 21 "Nobody at Channel 6 remembers why."  the tape eaten by tracking noise
    C(T(21), 'flat', set=lambda: ST.bu_tape94('title', track=0.9), era='1994', sfx=[(T(21), 'vhs_noise', -10, 0, 'vhs', dict(dur=2.6))],
      post_fn=lambda tt: dict(dim=0.4 * clamp((tt - T(21)) / 2.4)), c=dict(mv='push', rate=0.01))

# ==================================================================================================== GRANDMA DELLA, SEAT 22, SAMI, THE POST, THE RULES (22-58)
def plan_family(F):
    t, e, C = F.t, F.e, F.cut
    # 22 "My brother and I live with Grandma Della."
    C(T(22), 'set', room='living', view='couch3q', set=LIV_EVE, rim=LAMP,
      ppl=[P('della', 'couch_left', expr='warm', act=_A(lambda a, s: a.look_at(s.t0, (s.A_sami if False else scr(s.sp, 'couch_mid', dy=-260)), dur=0.4),
                                                         blinks(T(22) + 1.1))),
           P('sami', 'couch_mid', expr='proud_grin', act=_A(lambda a, s: a.look_at(s.t0 + 0.2, scr(s.sp, 'couch_left', dy=-330), dur=0.3),
                                                            pose(T(22) + 0.4, T(22) + 0.9, 0.25, bounce=0.6))),
           P('mina', 'couch_right', expr='neutral', act=_A(lambda a, s: a.look_at(s.t0 + 0.5, scr(s.sp, 'couch_mid', dy=-200), dur=0.4), blinks(E(22) - 0.3)))],
      tags=[tagc(WD(22, 'della'), 'GRANDMA DELLA', 'pill', 960, 170, 1.8)], c=dict(mv='push', f=1.0, rate=0.012))
    # 23 "She's driven bus 9 for thirty-two years, and parks it in our driveway."
    C(T(23), 'set', room='front', view='sideyard', set=dict(his=False, porch=1.0, letters=1.0, cab9=0.0), rim=PORCH,
      ppl=[P('della', 'b9_door', expr='warm', act=_A(lambda a, s: a.reach_to(s.t0 + 0.3, 1, scr(s.sp, 'b9_door', dx=60, dy=-330), dur=0.6, contact='palm', shape='flat', z=20.0),
                                                      lambda a, s: a.look_at(s.t0, scr(s.sp, 'b9_door', dx=80, dy=-380), dur=0.4)))],
      tags=[tagc(WD(23, 'thirty'), 'BUS 9  /  32 YEARS', 'pill', 960, 170, 2.2)], c=dict(mv='push', f=1.0, rate=0.015))
    # 24-26 D "Brakes, mirrors, names," she says. "That's the job."
    C(T(24), 'bust', who='della', bg=('front', 'driveway'), set=dict(his=False, porch=1.0, letters=1.0), expr='warm', cx=820, cy=640, scale=0.82, turn=0.35,
      light=PORCH, act=_A(lambda a, s: a.look_at(s.t0, (1500, 520), dur=0.3), lambda a, s: a.head_tilt(t(26), 8.0, 0.8)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 27 "Every kid gets a good morning, by name."
    C(T(27), 'set', room='bus', view='driver', set=dict(kind='bus9', tod='morning', door=1.0), era='morning', rim=MORNING,
      ppl=[P('della', 'driver', kind='seat', expr='warm', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'top_step', dy=-250), dur=0.4),
                                                                 lambda a, s: a.wave(s.t0 + 0.4, s.t0 + 1.6, 1))),
           P('mina', 'top_step', expr='neutral', face='driver', act=_A(lambda a, s: a.look_at(s.t0 + 0.3, scr(s.sp, 'driver', dy=-200), dur=0.4)))],
      sfx=[(T(27) + 0.1, 'bus_ambience', -12, 0, 'bus', dict(dur=2.4, kind='bus9_morning'))], c=dict(mv='push', f=1.0, rate=0.012))
    # 28 "She won't pull away until a porch light blinks back."
    blink = lambda tt: 1.0 if (WD(28, 'blinks') <= tt < WD(28, 'blinks') + 0.25 or WD(28, 'blinks') + 0.45 <= tt < WD(28, 'blinks') + 0.7) else 0.0
    C(T(28), 'set', room='front', view='house', set=dict(his=False, porch=blink, letters=1.0, street=1.0), rim=PORCH,
      sfx=[(WD(28, 'blinks'), 'porch_light', -6, 0, 'outside', dict(kind='click')), (WD(28, 'blinks') + 0.45, 'porch_light', -6, 0, 'outside', dict(kind='click'))],
      c=dict(mv='push', f=1.8, rate=0.02, x=870, y=500, free=True))
    # 29 "But one kid never gets a good morning."
    C(T(29), 'set', room='bus', view='seat22', set=dict(kind='bus9', tod='morning'), era='morning', rim=MORNING,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', act=blinks(T(29) + 0.8))], c=dict(mv='push', f=0.85, rate=0.02, free=True))
    # 30 "Seat twenty-two."
    C(T(30), 'set', room='bus', view='seat22', set=dict(kind='bus9', tod='morning'), era='morning', rim=MORNING,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'window22'), dur=0.5)))],
      tags=[tagc(WD(30, 'seat'), 'SEAT 22', 'red', 960, 170, 1.6)], c=dict(mv='push', f=1.0, rate=0.015))
    # 31 "A boy in a yellow raincoat, even in June."
    C(T(31), 'bust', who='theo', bg=('bus', 'seat22'), set=dict(kind='bus9', tod='morning'), era='morning', expr='lonely', cx=960, cy=640, scale=0.8, turn=0.4,
      light=MORNING, act=_A(lambda a, s: a.look_at(s.t0, (300, 500), dur=0.4), blinks(E(31) - 0.6)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 32 "Every day he says,"  33 T "Hi, Mina."
    pass_x = lambda tt: lerp(2350.0, -450.0, ease_in_out(clamp((tt - T(32)) / max(0.6, E(32) + 0.5 - T(32)))))
    C(T(32), 'bust', who='theo', bg=('bus', 'seat22'), set=dict(kind='bus9', tod='morning'), era='morning', expr='kind_smile', cx=700, cy=640, scale=0.72, turn=0.45,
      light=MORNING, act=_A(lambda a, s: a.look_at(s.t0, (1500, 480), dur=0.3), lambda a, s: a.look_at(E(32) - 0.3, (500, 480), dur=0.5)),
      busts=[dict(who='mina', cx=pass_x, cy=760, scale=1.0, turn=-0.7, expr='neutral', depth=0.9)],
      sfx=[(T(32) + 0.1 + 0.3 * k, 'footsteps_bus', -12, 0, 'bus', dict(n=1, index=k)) for k in range(3)], c=dict(mv='push', rate=0.0, zrate=0.01))
    C(T(33), 'bust', who='theo', bg=('bus', 'seat22'), set=dict(kind='bus9', tod='morning'), era='morning', expr='kind_smile', cx=900, cy=640, scale=0.8, turn=0.25,
      light=MORNING, act=_A(lambda a, s: a.look_at(s.t0, (1500, 480), dur=0.3), lambda a, s: a.wave(s.t0 + 0.05, E(33) + 0.3, 1)), c=dict(mv='push', rate=0.0, zrate=0.01))
    # 34 "I never asked his name."
    C(T(34), 'bust', who='mina', bg=('bus', 'seat21'), set=dict(kind='bus9', tod='morning'), era='morning', expr='guilt', cx=1000, cy=640, scale=0.8, turn=-0.35,
      light=MORNING, act=_A(lambda a, s: a.look_at(s.t0, (200, 420), dur=0.4), blinks(T(34) + 0.6)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 35 "Nobody sits with him."
    C(T(35), 'set', room='bus', view='seat22', set=dict(kind='bus9', tod='morning'), era='morning', rim=MORNING,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'aisle8', dy=-260), dur=0.6))],
      c=dict(mv='push', f=1.3, rate=0.03))
    # 36-37 "Tomorrow, my brother Sami starts first grade." "He's six."
    C(T(36), 'set', room='living', view='couch3q', set=LIV_EVE, rim=LAMP,
      ppl=[P('sami', 'couch_front', expr='proud_grin', face=(0.5, 2.0), act=_A(lambda a, s: a.hug_prop(s.t0 + 0.2, 'dino_pack'), blinks(T(37) + 0.2))),
           P('mina', 'couch_right', expr='kind_ask', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dy=-230), dur=0.4))],
      tags=[tagc(WD(36, 'sami'), 'SAMI', 'pill', 960, 170, 1.6), tagc(WD(37, 'six'), 'AGE 6', 'pill', 960, 170, 1.2)], c=dict(mv='push', f=1.0, rate=0.015))
    # 38-39 "All week, he's practiced roll call." "Say his name, and he shouts,"
    C(T(38), 'set', room='living', view='couch3q', set=LIV_EVE, rim=LAMP,
      ppl=[P('sami', 'couch_front', expr='proud_grin', face=(-0.05, 4.75), act=_A(pose(T(39) + 0.3, None, 0.4, chest_up=0.6), lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_right', dy=-300), dur=0.3))),
           P('mina', 'couch_right', expr='kind_ask', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dy=-230), dur=0.4),
                                                            lambda a, s: a.point_at(T(39), scr(s.sp, 'couch_front', dy=-260), t1=E(39) + 0.4, side=1)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    # 40 S "HERE!"
    C(T(40), 'bust', who='sami', bg=('living', 'couch3q'), set=LIV_EVE, expr='shout_here', cx=960, cy=660, scale=0.85, light=LAMP,
      act=_A(lambda a, s: a.reach_to(s.t0 + 0.02, 1, (1180, 300), dur=0.2, contact='palm', shape='open', z=80.0)), c=dict(mv='push', rate=0.0, zrate=0.03, hit=[WD(40, 'here')]))
    # 41 "I gave him walkie-talkies, so he can always reach me."
    C(T(41), 'set', room='living', view='couch3q', set=LIV_EVE, rim=LAMP,
      ppl=[P('mina', 'couch_right', expr='kind_ask', act=_A(lambda a, s: a.hold_prop('walkie', 1, -9, T(41) + 1.0),
                                                            lambda a, s: a.reach_to(T(41) + 0.2, 1, toward(a, 1, scr(s.sp, 'couch_front', dx=-40, dy=-200), T(41) + 0.2), t1=T(41) + 1.1, dur=0.5, contact='grip', shape='grip', z=60.0),
                                                            lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dy=-230), dur=0.4))),
           P('sami', 'couch_front', expr='proud_grin', face=(-0.05, 4.75), act=_A(lambda a, s: a.hold_prop('walkie', -1, T(41) + 1.0, None),
                                                                                  lambda a, s: a.reach_to(T(41) + 0.6, -1, scr(s.sp, 'couch_front', dx=-40, dy=-200), t1=T(41) + 1.2, dur=0.4)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    C(W(41, 'always'), 'ins', name='walkie', kw=lambda u: dict(talk=1.0 if (u % 0.6) < 0.3 else 0.0), sfx=[(W(41, 'always') + 0.1, 'walkie_squelch', -6, 0, 'close')],
      c=dict(mv='push', rate=0.03))
    # 42 "Today, I posted his first-day chalkboard."
    C(T(42), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_EVE, expr='neutral', cx=960, cy=640, scale=0.82, turn=0.2, light=PHONE,
      act=_A(lambda a, s: a.look_at(s.t0, (900, 1000), dur=0.3), lambda a, s: a.hold_prop('cell', 1, -9, None)),
      sfx=[(WD(42, 'posted'), 'phone_tap', -8, 0, 'close')], c=dict(mv='push', rate=0.0, zrate=0.012))
    # 43-47 Sami. First grade. Larkfield Elementary. Bus 9. Larch Street.  (the chalkboard, each word lit as it is read)
    words = [(43, 'SAMI', 330), (44, 'FIRST GRADE', 420), (45, 'LARKFIELD ELEMENTARY', 500), (46, 'BUS 9', 560), (47, 'LARCH STREET', 620)]
    C(T(43), 'ins', name='chalkboard', motion=lambda u: (0.0, -40.0 * ease_in_out(clamp(u / 4.0)), 0.06 * ease_in_out(clamp(u / 4.0)), 0.0),
      tags=[(t(i), s_, 1500, y_ + 120, 'red', e(i) - t(i) + 0.2) for i, s_, y_ in words], tag_sound=False,
      sfx=[(t(i), 'ui_tick', -10, 0, 'close') for i, _, _ in words], c=dict(mv='push', rate=0.0))
    # 48 "Forty-one likes."  49 "And one comment."
    C(T(48), 'ins', name='post', kw=dict(show=1), sfx=[(T(48) + 0.2 + 0.08 * k, 'like_pop', -12, 0, 'close') for k in range(5)], c=dict(mv='push', rate=0.03))
    C(T(49), 'ins', name='post', kw=dict(show=2, hl='comment'), sfx=[(WD(49, 'comment'), 'notification', -6, 0, 'close')], c=dict(mv='push', rate=0.04))
    # 50-51 "No face on the account." "Just a crooked yellow hat."
    C(T(50), 'ins', name='comment', c=dict(mv='push', rate=0.03))
    C(T(51), 'ins', name='comment', motion=lambda u: (360.0 * ease_in_out(clamp(u / 1.2)), 40.0 * ease_in_out(clamp(u / 1.2)), 0.5 * ease_in_out(clamp(u / 1.2)), 0.0),
      c=dict(mv='push', rate=0.0))
    # 52 "Great smile!"
    C(T(52), 'ins', name='comment', motion=lambda u: (0.0, 0.0, 0.2 + 0.1 * ease_out_cubic(clamp(u / 0.4)), 0.0), cut='vhs', hit=[WD(52, 'great')],
      c=dict(mv='push', rate=0.0))
    # 53-54 "Grandma's face went grey." D "Take it down."
    C(T(53), 'bust', who='della', bg=('living', 'reverse'), set=LIV_EVE, expr='set_jaw', cx=900, cy=640, scale=0.82, turn=0.3,
      light=dict(LAMP, key=-0.15), act=_A(lambda a, s: a.look_at(s.t0, (900, 1000), dur=0.3), lambda a, s: a.look_at(T(54), (1600, 500), dur=0.35)),
      c=dict(mv='push', rate=0.0, zrate=0.015))
    # 55 "I didn't."
    C(T(55), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_EVE, expr='resolve', cx=1020, cy=640, scale=0.82, turn=-0.3, light=LAMP,
      act=_A(lambda a, s: a.look_at(s.t0, (300, 500), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.01))
    # 56 "Every year, the night before the first day, Grandma tapes seven rules inside the front door."
    C(T(56), 'set', room='hall', view='door', set=dict(hall=1.0, porch=0.0, rules=1.0), rim=LAMP,
      ppl=[P('della', 'door_inside', face=(-3.95, 0.0), expr='calm_firm', act=_A(lambda a, s: a.reach_to(s.t0 + 0.3, 1, scr(s.sp, 'rules', dx=-60), dur=0.6, contact='palm', shape='flat', z=10.0),
                                                               lambda a, s: a.reach_to(s.t0 + 0.6, -1, scr(s.sp, 'rules', dx=60), dur=0.6, contact='palm', shape='flat', z=10.0)))],
      sfx=[(T(56) + 0.9, 'tape_rip', -8, 0, 'inside')], c=dict(mv='push', f=1.0, rate=0.015))
    C(W(56, 'seven'), 'set', room='hall', view='doorclose', set=dict(hall=1.0, rules=1.0), rim=LAMP,
      acts=lambda A, sh, sp: [hand_layer('della', slide(sh.t0, sh.t0 + 0.6, (760, 1180), (800, 980), -170, -175), 300, 'flat', 1, sleeve_from=(640, 1500)),
                              hand_layer('della', slide(sh.t0 + 0.2, sh.t0 + 0.8, (1160, 1180), (1120, 990), 170, 175), 300, 'flat', -1, sleeve_from=(1280, 1500))],
      sfx=[(W(56, 'seven') + 0.6, 'tape_press', -8, 0, 'close')], c=dict(mv='push', f=1.0, rate=0.02))
    # 57 "Every year, nothing comes."
    C(T(57), 'ins', name='rules', kw=dict(show=7), c=dict(mv='push', rate=0.025))
    # 58 "This year, she also whispers our family word."  (no lip sync: the narration names it, she whispers behind her hand)
    C(T(58), 'bust', who='della', bg=('hall', 'door'), set=dict(hall=1.0, rules=1.0), expr='whisper', cx=700, cy=660, scale=0.8, turn=0.55, light=LAMP, talk=False,
      act=_A(lambda a, s: a.set(s.t0 + 0.1, None, 0.6, lean=0.25, h_tilt=-6.0)),
      busts=[dict(who='mina', cx=1180, cy=690, scale=0.78, turn=-0.4, expr='hush_fear',
                  act=_A(lambda a, s: a.look_at(WD(58, 'family'), (1400, 600), dur=0.3), lambda a, s: a.expr('shock', WD(58, 'word'), None, 0.2)))],
      sfx=[(WD(58, 'whispers'), 'whisper_breath', -14, -0.2, 'close')], c=dict(mv='push', rate=0.0, zrate=0.02))


# ==================================================================================================== RULE 1, MIDNIGHT, THE LOUDSPEAKER (59-78)
def plan_rule1(F):
    t, e, C = F.t, F.e, F.cut
    # 59-61 RULE 1 card
    C(T(59), 'rule', n=1)
    # 62 "He can only call the names he can read."  HAYES on our mailbox, his headlights sweeping across it
    C(T(62), 'set', room='front', view='mailbox', set=dict(his=False, letters=1.0, porch=1.0), rim=PORCH,
      post_fn=lambda tt: dict(flash=_epost.Spill(0.25 * math.sin(math.pi * clamp((tt - T(62)) / 2.0)), side=1.0, color=(1.0, 0.85, 0.45), reach=0.9)),
      c=dict(mv='push', f=1.0, rate=0.03))
    # 63 "Grandma unscrews the letters off our mailbox."
    C(T(63), 'set', room='front', view='curb', set=dict(his=False, letters=1.0, porch=1.0), rim=PORCH,
      ppl=[P('della', 'mailbox_front', expr='set_jaw', face='mailbox_box',
             act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'mailbox_box'), dur=0.3),
                    *[(lambda k: lambda a, s: a.reach_to(s.t0 + 0.2 + k * 0.7, 1, scr(s.sp, 'mailbox_box', dx=-40 + 40 * k), t1=s.t0 + 0.75 + k * 0.7, dur=0.3, contact='grip', shape='grip', z=30.0))(k)
                      for k in range(2)]))],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(W(63, 'letters'), 'ins', name='mailbox', kw=lambda u: dict(letters=1.0 - clamp(u / 1.8)),
      sfx=[(W(63, 'letters') + 0.3 + 0.45 * k, 'letter_clink', -8, 0, 'close', dict(index=k)) for k in range(4)], c=dict(mv='push', rate=0.02))
    # 64 "She turns Sami's dinosaur backpack to face the wall."
    C(T(64), 'set', room='living', view='window', set=dict(lamp=1.0, ceil=0.0, backpack='window'), rim=LAMP,
      ppl=[P('della', 'backpack_reach', expr='set_jaw', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'backpack'), dur=0.3),
                                                              lambda a, s: a.reach_to(s.t0 + 0.25, 1, scr(s.sp, 'backpack', dy=-60), dur=0.5, contact='grip', shape='grip', z=30.0)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    flip = W(64, 'face')
    C(flip, 'ins', name='backpack', kw=lambda u: dict(side='front' if u < 0.35 else 'back'),
      motion=lambda u: ((-1600.0 * ease_in_cubic(clamp(u / 0.35)) if u < 0.35 else 1600.0 * (1 - ease_out_cubic(clamp((u - 0.35) / 0.3)))), 0.0, 0.0, 0.0),
      sfx=[(flip + 0.3, 'fabric_turn', -8, 0, 'close')], c=dict(mv='push', rate=0.02))
    # 65 "Lights off."  the street-facing windows go dark one by one
    off = lambda k: (lambda tt: 1.0 - clamp((tt - (WD(65, 'lights') + 0.2 * k)) / 0.06))
    C(T(65), 'set', room='front', view='house', set=dict(his=False, letters=0.0, porch=off(0), win=dict(liv=off(1), gran=off(2), mina=off(3), hall=0.0)), rim=NIGHT,
      sfx=[(WD(65, 'lights') + 0.2 * k, 'light_switch', -8, 0, 'inside', dict(index=k)) for k in range(4)], c=dict(mv='push', f=1.2, rate=0.01, y=520))
    # 66 "Midnight."
    C(T(66), 'set', room='living', view='couch3q', set=LIV_NIGHT, rim=NIGHT,
      ppl=[P('della', 'couch_left', expr='set_jaw'), P('sami', 'couch_mid', expr='sleepy', act=pose(-9, None, 0.1, h_tilt=-18.0, lean=0.15)),
           P('mina', 'couch_right', expr='fear', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-400, dy=-420), dur=0.3), blinks(T(66) + 0.5)))],
      tags=[tagc(WD(66, 'midnight'), '12:00 AM', 'alert', 960, 170, 1.2)], sfx=[(WD(66, 'midnight'), 'clock_tick', -10, 0, 'inside', dict(dur=0.8))],
      c=dict(mv='push', f=1.0, rate=0.01))
    # 67 "Air brakes hiss outside."  his bus pulls in to the kerb
    C(T(67), 'set', room='front', view='house', set=dict(his=True, his_heads=1.0, his_win=1.0, letters=0.0, porch=0.0),
      rim=AMBER, sfx=[(WD(67, 'air'), 'air_brakes', 2, 0.1, 'outside', dict(kind='hiss_long'))], c=dict(mv='push', f=1.1, rate=0.015))
    # 68 "Yellow headlights fill the curtains."
    C(T(68), 'set', room='living', view='window', set=dict(LIV_NIGHT, heads=lambda tt: ease_in_out(clamp((tt - T(68)) / 0.8))), rim=HEADS,
      sfx=[(T(68), 'engine_idle_swell', -8, 0, 'outside')], c=dict(mv='push', f=1.0, rate=0.02))
    # 69 "Nobody opens the curtains."
    C(T(69), 'set', room='living', view='couch3q', set=LIV_HEADS, rim=HEADS,
      ppl=[P('della', 'couch_left', expr='set_jaw', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-500, dy=-380), dur=0.2)),
           P('sami', 'couch_mid', expr='sleepy', act=pose(-9, None, 0.1, h_tilt=-18.0, lean=0.15)),
           P('mina', 'couch_right', expr='hush_fear', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-450, dy=-400), dur=0.2),
                                                             lambda a, s: a.reach_to(s.t0 + 0.2, -1, scr(s.sp, 'couch_mid', dx=60, dy=-170), dur=0.4, contact='palm', shape='flat', z=10.0)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 70 "A loudspeaker crackles."
    C(T(70), 'set', room='front', view='curb', set=FRONT_HIS, rim=AMBER, sfx=[(WD(70, 'loudspeaker'), 'loudspeaker_crackle', -2, 0, 'outside')],
      c=dict(mv='push', f=1.0, rate=0.02, hit=[(WD(70, 'crackles'), 2.0)]))
    # 71 "A bright TV voice starts to read."
    C(T(71), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_HEADS, expr='hush_fear', cx=1000, cy=640, scale=0.82, turn=-0.35, light=HEADS,
      act=_A(lambda a, s: a.look_at(s.t0, (240, 380), dur=0.3), blinks(T(71) + 0.9)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 72 W "Sami. First grade. Larkfield Elementary. Bus 9. Larch Street."  (HIM reading off a phone; Sami stirs; Grandma)
    C(T(72), 'bust', who='whistle', bg=('front', 'gap'), set=FRONT_HIS, cx=1000, cy=780, scale=0.75, turn=-0.3, light=dict(WS_NIGHT, under='#dfeaff', under_a=90),
      act=_A(lambda a, s: a.look_at(s.t0, (960, 1000), dur=0.2), lambda a, s: a.ws_hold(-9, -1, 'cell')), c=dict(mv='push', rate=0.0, zrate=0.012))
    C(W(72, 'larkfield'), 'bust', who='sami', bg=('living', 'couch3q'), set=LIV_HEADS, expr='sleepy', cx=960, cy=660, scale=0.85, turn=0.2, light=HEADS,
      act=_A(pose(-9, None, 0.1, h_tilt=-14.0), pose(WD(72, 'bus') - 0.3, None, 0.5, h_tilt=-4.0)), c=dict(mv='push', rate=0.0, zrate=0.01))
    C(W(72, 'bus'), 'bust', who='della', bg=('living', 'couch3q'), set=LIV_HEADS, expr='set_jaw', cx=880, cy=640, scale=0.82, turn=0.4, light=HEADS,
      act=_A(lambda a, s: a.look_at(s.t0, (1700, 420), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 73 "A pause."
    C(T(73), 'set', room='living', view='couch3q', set=LIV_HEADS, rim=HEADS,
      ppl=[P('della', 'couch_left', expr='set_jaw', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-500, dy=-380), dur=0.2)),
           P('sami', 'couch_mid', expr='sleepy', act=pose(-9, None, 0.1, h_tilt=-12.0, lean=0.1)),
           P('mina', 'couch_right', expr='hush_fear', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-450, dy=-400), dur=0.2))],
      c=dict(mv='push', f=1.08, rate=0.03))
    # 74 W "Great smile, Mina!"  his head snaps to the house
    C(T(74), 'bust', who='whistle', bg=('front', 'curb'), set=FRONT_HIS, cx=980, cy=800, scale=0.95, turn=-0.5, light=WS_NIGHT, cut='vhs',
      act=_A(wlook(T(74) - 0.5, (1700, 500)), wlook(WD(74, 'mina') - 0.05, (960, 520))), hit=[WD(74, 'mina')], c=dict(mv='push', rate=0.0, zrate=0.03))
    # 75 "He didn't read it off our house."  the blank mailbox
    C(T(75), 'set', room='front', view='mailbox', set=dict(FRONT_HIS), rim=AMBER, c=dict(mv='push', f=1.0, rate=0.02))
    # 76 "He read it off my phone."
    C(T(76), 'ins', name='post', kw=dict(show=2, hl='comment'), motion=lambda u: (0.0, 0.0, 0.25 * ease_out_cubic(clamp(u / 1.0)), 0.0),
      hands=[dict(who='mina', fn=lambda tt: (960, 1180, 180.0, 1.0), size=520, shape='grip', side=1, sleeve_from=(1000, 1500))],
      sfx=[(T(76), 'stinger', -4, 0, None, dict(kind='reveal'))], c=dict(mv='push', rate=0.0))
    # 77 W "I know your name! That makes us friends!"  (tape-skip closer)
    C(T(77), 'bust', who='whistle', bg=('front', 'curb'), set=FRONT_HIS, cx=960, cy=820, scale=0.85, light=WS_NIGHT, act=pose(-9, None, 0.1, h_tilt=6.0),
      c=dict(mv='push', rate=0.0, zrate=0.02))
    C(W(77, 'that'), 'bust', who='whistle', bg=('front', 'curb'), set=FRONT_HIS, cx=980, cy=900, scale=1.2, light=WS_NIGHT, cut='vhs', act=pose(-9, None, 0.1, h_tilt=-8.0),
      sfx=[(W(77, 'that'), 'tape_skip', -2, 0, None)], c=dict(mv='push', rate=0.0, zrate=0.03))
    # 78 "Fweet-fweet."
    C(T(78), 'bust', who='whistle', bg=('front', 'curb'), set=FRONT_HIS, cx=960, cy=700, scale=0.75, light=WS_NIGHT,
      act=lambda a, s: a.blow_whistle(WD(78, 'fweet') - 0.15, 'two', -1), c=dict(mv='push', rate=0.0, zrate=0.02))


# ==================================================================================================== THE COMMENT PROMPT (79-82)
def plan_pause(F):
    t, e, C = F.t, F.e, F.cut
    C(T(79), 'pause', stage='word', sfx=[(T(79), 'tv_on', -2, 0, 'tv'), (T(79) + 0.8, 'ui_pop', -6, 0, 'close')],
      music=[(T(79), 'jingle', 0.5, 2.0, dict(version='warped_sting'))])
    C(T(80), 'pause', stage='ask', t_q=T(81), t_yn=WD(82, 'yes') - 0.1,
      sfx=[(WD(82, 'yes') - 0.1, 'ui_pop', -4, 0, 'close'), (WD(82, 'yes') + 1.5, 'ui_click', -6, 0, 'close')])


# ==================================================================================================== RULE 2: HE UNFOLDS, THE SKIPS, THE DOOR, ROLL CALL, THE TICKET (83-121)
def plan_rule2(F):
    t, e, C = F.t, F.e, F.cut
    C(T(83), 'rule', n=2)
    # 88 "Through a gap in the curtains, his bus door folds open."
    C(T(88), 'bust', who='mina', bg=('living', 'window'), set=LIV_HEADS, expr='hush_fear', cx=980, cy=640, scale=0.85, turn=0.1, light=HEADS,
      act=_A(lambda a, s: a.look_at(s.t0, (900, 520), dur=0.3), blinks(T(88) + 0.6)), c=dict(mv='push', rate=0.0, zrate=0.015))
    door = lambda tt: ease_in_out(clamp((tt - WD(88, 'folds')) / 0.9))
    C(W(88, 'door'), 'set', room='front', view='gap', set=dict(FRONT_HIS, his_door=door), rim=AMBER, sfx=[(WD(88, 'folds'), 'bus_door_fold', -2, 0, 'outside')],
      c=dict(mv='push', f=1.0, rate=0.03))
    # 89-90 "Something unfolds out of it." "Like a ladder."  91 "Up, and up, and up."
    t_un = T(89) + 0.15
    un = lambda a, s: a.unfold(t_un, max(2.0, T(91) + 1.2 - t_un))
    C(T(89), 'set', room='front', view='curb', set=dict(FRONT_HIS, his_door=1.0), rim=AMBER, ppl=[ws('his_step', act=un)], c=dict(mv='push', f=1.0, rate=0.015))
    C(T(91), 'set', room='front', view='curb', set=dict(FRONT_HIS, his_door=1.0), rim=AMBER, ppl=[ws('his_step', act=un)],
      c=dict(mv='keys', free=True, keys=[(T(91), 960, 640, 1.0, None, 1.25), (E(91) + 0.3, 960, 380, 1.0, 'push', 1.35)]))
    # 92-95 the streetlight flickers: his bus step -> the mailbox -> the middle of the lawn
    C(T(92), 'set', room='front', view='street', set=dict(FRONT_HIS, his_door=1.0, street=ST.bu_flicker(WD(93, 'mailbox') - 0.4)), rim=AMBER,
      ppl=[ws('his_step', act=_A(skip_to((-9, 'his_step'), (WD(93, 'mailbox') - 0.25, 'mailbox', dict(h_tilt=8.0)), (WD(94, 'flicker'), 'lawn_mid', dict(h_tilt=14.0))),
                                 wlook(WD(95, 'lawn'), (960, 360))))],
      sfx=[(WD(92, 'flickers'), 'streetlight_flicker', -4, 0, 'outside')], c=dict(mv='push', f=1.0, rate=0.012))
    # 96-97 "Flicker. The porch steps."
    C(T(96), 'set', room='front', view='porch', set=dict(FRONT_HIS, porch=0.0), rim=AMBER,
      ppl=[ws('porch_step', face='porch_door', act=skip_to((-9, ('off', -900, 900)), (WD(96, 'flicker') + 0.05, 'porch_step', dict(h_tilt=10.0))))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 98-99 "He never walks. He skips, like a tape."
    C(T(98), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=960, cy=820, scale=0.8, light=AMBER, act=pose(-9, None, 0.1, h_tilt=12.0),
      c=dict(mv='push', rate=0.0, zrate=0.015))
    C(W(99, 'skips'), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=900, cy=900, scale=1.15, light=AMBER, cut='vhs', act=pose(-9, None, 0.1, h_tilt=-6.0),
      sfx=[(W(99, 'skips'), 'tape_skip', 0, 0, None)], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 100-101 "White gloves curl around our doorframe." "Too many knuckles."
    curl = _A(pose(-9, None, 0.1, ws_hands_front=3, ws_bend=0.12),
              lambda a, s: a.curl_door(T(100) + 0.2, 1, scr(s.sp, (-4.5, -0.03, 1.75)), dur=0.8),
              lambda a, s: a.curl_door(T(100) + 0.7, -1, scr(s.sp, (-4.5, -0.03, 1.3)), dur=0.8))
    C(T(100), 'set', room='front', view='frame', set=dict(FRONT_HIS, porch=0.0), rim=AMBER, ppl=[ws((-4.74, -0.25), face=(-4.48, -0.03), act=curl)],
      sfx=[(T(100) + 0.4, 'glove_creak', -6, -0.3, 'outside'), (T(100) + 0.9, 'glove_creak', -6, -0.3, 'outside')], c=dict(mv='push', f=1.0, rate=0.02))
    C(T(101), 'set', room='front', view='frame', set=dict(FRONT_HIS, porch=0.0), rim=AMBER, ppl=[ws((-4.74, -0.25), face=(-4.48, -0.03), act=curl)],
      c=dict(mv='push', f=1.7, rate=0.03, x=860, y=500))
    # 102 "Through the frosted glass: a crooked hat."
    C(T(102), 'set', room='hall', view='door', set=dict(HALL_NIGHT, frost=1.0, porch=0.0), rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.03))
    # 103 "And that grin."
    C(T(103), 'bust', who='whistle', bg=('hall', 'doorclose'), set=dict(HALL_NIGHT, frost=1.0), cx=960, cy=820, scale=1.0, light=AMBER,
      post=dict(blur=5), hit=[T(103) + 0.1], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 104 "He calls roll."
    C(T(104), 'set', room='front', view='porch', set=dict(FRONT_HIS, porch=0.0), rim=AMBER,
      ppl=[ws('porch_door', face=(-3.95, 0.0), act=lambda a, s: a.clipboard(s.t0 + 0.1, 1))], sfx=[(T(104) + 0.2, 'clipboard_lift', -8, 0, 'outside')],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 105 W "Della? Long time!"
    C(T(105), 'set', room='living', view='couch3q', set=LIV_HEADS, rim=HEADS,
      ppl=[P('della', 'couch_left', expr='set_jaw', act=_A(lambda a, s: a.look_at(s.t0 + 0.3, scr(s.sp, 'stairs_foot', dy=-300), dur=0.25))),
           P('sami', 'couch_mid', expr='sleepy', act=pose(-9, None, 0.1, h_tilt=-14.0, lean=0.12)),
           P('mina', 'couch_right', expr='hush_fear', act=lambda a, s: a.look_at(s.t0 + 0.5, scr(s.sp, 'couch_left', dy=-330), dur=0.3))],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 106 W "Mina?"  107 W "Sami?"
    C(T(106), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_HEADS, expr='hush_fear', cx=1000, cy=640, scale=0.85, turn=-0.3, light=HEADS,
      act=_A(lambda a, s: a.look_at(s.t0, (200, 460), dur=0.15)), c=dict(mv='push', rate=0.0, zrate=0.02))
    # 107-110 "Sami?" "Sami jolts awake." "Takes a breath." S "He..."
    C(T(107), 'bust', who='sami', bg=('living', 'couch3q'), set=LIV_HEADS, expr='sleepy', cx=960, cy=660, scale=0.9, turn=0.2, light=HEADS,
      act=_A(pose(-9, None, 0.1, h_tilt=-14.0), pose(WD(108, 'jolts') - 0.05, None, 0.12, h_tilt=0.0, wide=0.6),
             pose(T(109) + 0.1, None, 0.5, chest_up=0.6), lambda a, s: a.talk([(t(110), e(110), 'He')], env=None, words=None)),
      c=dict(mv='push', rate=0.0, zrate=0.02, hit=[(WD(108, 'jolts'), 3.0)]))
    # 111 "My hand slaps over his mouth."
    def _mouth(): return bust_eyes('sami', 960, 660, 0.9)
    t_s = WD(111, 'slaps') - 0.12
    C(T(111), 'bust', who='sami', bg=('living', 'couch3q'), set=LIV_HEADS, expr='shout_here', cx=960, cy=660, scale=0.9, turn=0.2, light=HEADS,
      act=_A(ex('fear', t_s + 0.15, None, 0.15)),
      hands=[dict(who='mina', fn=slide(t_s, t_s + 0.16, (300, 1100), (_mouth()[0] - 120, _mouth()[1] + 210), -60, -100), size=330, shape='flat', side=1, sleeve_from=(-100, 1400))],
      sfx=[(t_s + 0.16, 'hand_slap', 0, 0, 'close')], c=dict(mv='push', rate=0.0, zrate=0.0, hit=[(t_s + 0.16, 4.0)]))
    # 112 "Silence."
    C(T(112), 'set', room='living', view='couch3q', set=LIV_HEADS, rim=HEADS,
      ppl=[P('della', 'couch_left', expr='set_jaw', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'stairs_foot', dy=-300), dur=0.2)),
           P('sami', 'couch_mid', expr='fear'),
           P('mina', 'couch_right', expr='hush_fear', act=_A(lambda a, s: a.reach_to(-9, -1, scr(s.sp, 'couch_mid', dx=40, dy=-330), dur=0.01, contact='palm', shape='flat', z=40.0),
                                                             lambda a, s: a.look_at(s.t0, scr(s.sp, 'stairs_foot', dy=-300), dur=0.2)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    # 113 "From the porch, in Sami's own little voice:"  114 W "Here!"
    C(T(113), 'set', room='hall', view='door', set=dict(HALL_NIGHT, frost=1.0), rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.03))
    C(T(114), 'bust', who='whistle', bg=('hall', 'doorclose'), set=dict(HALL_NIGHT, frost=1.0), cx=960, cy=860, scale=1.0, light=AMBER, post=dict(blur=4),
      act=lambda a, s: a.head_tilt(s.t0, 22.0, 0.3), hit=[WD(114, 'here')], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 115 "And then, in his own:"  116 W "Almost."
    C(T(115), 'set', room='front', view='porch', set=dict(FRONT_HIS), rim=AMBER,
      ppl=[ws('porch_door', face=(-3.95, 0.0), act=lambda a, s: a.set(s.t0, None, 0.8, ws_bend=0.45, h_tilt=-10.0))], c=dict(mv='push', f=1.0, rate=0.02))
    C(T(116), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=960, cy=760, scale=1.05, light=AMBER, act=pose(-9, None, 0.1, h_tilt=-14.0),
      c=dict(mv='push', rate=0.0, zrate=0.02))
    # 117 "Click-clack."
    C(T(117), 'ins', name='punch', kw=lambda u: dict(click=1.0 if 0.15 < u < 0.3 or 0.42 < u < 0.55 else 0.0),
      sfx=[(T(117) + 0.15, 'punch_clack', 0, 0, 'close')], c=dict(mv='push', rate=0.03))
    # 118 "A yellow ticket slides under the door, punched through the middle."
    C(T(118), 'set', room='hall', view='doorclose', set=dict(HALL_NIGHT, ticket=lambda tt: clamp((tt - T(118) - 0.3) / 1.4)), rim=NIGHT,
      sfx=[(T(118) + 0.3, 'paper_slide', -6, 0, 'inside', dict(dur=1.4))], c=dict(mv='push', f=1.0, rate=0.02, y=600))
    C(W(118, 'punched'), 'ins', name='ticket', kw=dict(slide=1.0), c=dict(mv='push', rate=0.025))
    # 119-121 "Sami." "Seat four." "Last stop, three a.m."
    C(T(119), 'ins', name='ticket', kw=dict(slide=1.0), motion=lambda u: (0.0, -30.0 * ease_in_out(clamp(u / 3.0)), 0.25, 0.0),
      tags=[(t(119), 'SAMI', 1500, 330, 'red', 0.8), (t(120), 'SEAT 4', 1500, 330, 'red', 0.9), (t(121), 'LAST STOP 3 A.M.', 1500, 330, 'red', 1.6)], tag_sound=False,
      c=dict(mv='push', rate=0.0))


# ==================================================================================================== RULE 3: 911, GRANDMA GOES, THE FAKE GRANDMA, THE PEEPHOLE (122-153)
def plan_rule3(F):
    t, e, C = F.t, F.e, F.cut
    C(T(122), 'rule', n=3)
    # 126 "I dial 911."
    C(T(126), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_HEADS, expr='fear', cx=960, cy=640, scale=0.85, light=PHONE,
      act=_A(lambda a, s: a.look_at(s.t0, (900, 1000), dur=0.2)), sfx=[(t(126) + 0.2 + 0.18 * k, 'dial_beep', -10, 0, 'close', dict(index=k)) for k in range(3)],
      c=dict(mv='push', rate=0.0, zrate=0.015))
    # 127 "No bars."
    C(T(127), 'ins', name='nobars', sfx=[(T(127) + 0.2, 'call_fail', -6, 0, 'close')], c=dict(mv='push', rate=0.03))
    # 128 "Not since his headlights came."
    C(T(128), 'set', room='living', view='window', set=LIV_HEADS, rim=HEADS, c=dict(mv='push', f=1.0, rate=0.02))
    # 129 "Grandma grabs her keys."
    C(T(129), 'set', room='hall', view='stairs', set=HALL_NIGHT, rim=NIGHT,
      ppl=[P('della', 'stairs_foot', expr='set_jaw', face='back_door', act=_A(lambda a, s: a.hold_prop('keys', 1, WD(129, 'keys'), None),
                                                                             lambda a, s: a.reach_to(s.t0 + 0.1, 1, scr(s.sp, 'stairs_foot', dx=120, dy=-280), t1=WD(129, 'keys'), dur=0.35)))],
      sfx=[(WD(129, 'keys'), 'keys_jingle', -4, 0, 'inside')], c=dict(mv='push', f=1.0, rate=0.015))
    # 130 D "Bus 9 has a radio to the depot. Lock this behind me."
    C(T(130), 'bust', who='della', bg=('hall', 'stairs'), set=HALL_NIGHT, expr='calm_firm', cx=900, cy=640, scale=0.82, turn=0.35, light=NIGHT,
      act=_A(lambda a, s: a.look_at(s.t0, (1600, 520), dur=0.3), lambda a, s: a.hold_prop('keys', 1, -9, None)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 131 "She slips out the back."
    bd = lambda tt: 80.0 * ease_in_out(clamp((tt - (E(131) - 0.6)) / 0.5))
    C(T(131), 'set', room='hall', view='stairs', set=dict(HALL_NIGHT, back_door=bd), rim=NIGHT,
      ppl=[P('della', 'stairs_foot', path=[(T(131), 'stairs_foot'), (E(131) + 0.3, 'back_door')], expr='set_jaw',
             act=lambda a, s: a.hold_prop('keys', 1, -9, None))],
      sfx=[(E(131) - 0.6, 'door_open', -6, 0, 'inside', dict(kind='back'))], c=dict(mv='push', f=1.0, rate=0.01))
    # 132-133 "Her flashlight crosses the yard." "Halfway there, it goes out."
    beam = lambda tt: 0.9 if tt < WD(133, 'out') else 0.0
    C(T(132), 'set', room='front', view='sideyard', set=dict(his=True, his_heads=1.0, porch=0.0, letters=0.0, broom='porch'), rim=NIGHT,
      ppl=[P('della', 'yard_west', path=[(T(132), 'yard_west'), (E(133) + 0.6, 'b9_door')], expr='set_jaw', surface='grass',
             torch=dict(side=1, a=beam, ground=2.0, spread=12.0), act=lambda a, s: a.hold_prop('maglite', 1, -9, None))],
      sfx=[(WD(133, 'out'), 'flashlight_off', -4, 0, 'outside')], c=dict(mv='push', f=1.0, rate=0.012))
    # 134 "Three knocks on the front door."
    C(T(134), 'set', room='hall', view='door', set=dict(HALL_NIGHT, porch=0.0), rim=NIGHT,
      ppl=[P('mina', (-4.0, 2.7), face='door_inside', expr='fear', act=lambda a, s: a.look_at(s.t0 + 0.4, scr(s.sp, 'peephole'), dur=0.25))],
      sfx=[(WD(134, 'knocks') + 0.1 + 0.34 * k, 'knock_door', 0, 0, 'inside', dict(kind='wood', n=1, index=k)) for k in range(3)], c=dict(mv='push', f=1.0, rate=0.015))
    # 135 W "Mina, open up! It's Grandma! He's right behind me!"
    C(T(135), 'set', room='hall', view='door', set=dict(HALL_NIGHT, porch=0.0), rim=NIGHT,
      ppl=[P('mina', (-4.0, 2.7), path=[(T(135) + 0.4, (-4.0, 2.7)), (W(135, "he's"), 'peephole_eye')], expr='hush_fear')], c=dict(mv='push', f=1.0, rate=0.015))
    C(W(135, "he's"), 'bust', who='mina', bg=('hall', 'doorclose'), set=HALL_NIGHT, expr='hush_fear', cx=960, cy=660, scale=0.85, turn=-0.2, light=NIGHT,
      act=_A(lambda a, s: a.look_at(s.t0, (700, 420), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 136-137 "Her voice." "Exactly her voice."
    C(T(136), 'set', room='hall', view='doorclose', set=HALL_NIGHT, rim=NIGHT,
      acts=lambda A, sh, sp: [hand_layer('mina', lambda tt: (585, 900, -160.0, 1.0), 330, 'grip', 1, sleeve_from=(300, 1500))], c=dict(mv='push', f=1.0, rate=0.02))
    # 138 "What's the word?"  (Mina, lip sync)
    C(T(138), 'bust', who='mina', bg=('hall', 'doorclose'), set=HALL_NIGHT, expr='resolve', cx=960, cy=660, scale=0.85, turn=-0.15, light=NIGHT,
      act=_A(lambda a, s: a.look_at(s.t0, (650, 400), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.01))
    # 139 W "Baby, there's no time!"  the knob rattling
    C(T(139), 'set', room='hall', view='doorclose', set=HALL_NIGHT, rim=NIGHT,
      sfx=[(T(139) + 0.15, 'knob_rattle', -2, 0, 'inside', dict(dur=1.0)), (T(139) + 0.1, 'knock_door', -2, 0, 'inside', dict(kind='fist', n=2))],
      c=dict(mv='push', f=1.0, rate=0.02, hit=[(T(139) + 0.15, 3.0), (T(139) + 0.6, 2.0)]))
    # 140 "What's the word, Grandma?"
    C(T(140), 'bust', who='mina', bg=('hall', 'doorclose'), set=HALL_NIGHT, expr='resolve', cx=930, cy=660, scale=0.9, turn=-0.15, light=NIGHT,
      act=_A(lambda a, s: a.look_at(s.t0, (650, 400), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 141 "Nothing."
    C(T(141), 'set', room='hall', view='door', set=HALL_NIGHT, rim=NIGHT, ppl=[P('mina', 'peephole_eye', expr='hush_fear')], c=dict(mv='push', f=1.0, rate=0.01))
    # 142 "Then the voice slides down, like a slowing tape."
    C(T(142), 'set', room='hall', view='doorclose', set=dict(HALL_NIGHT, frost=lambda tt: ease_in_out(clamp((tt - T(142)) / 2.2))), rim=NIGHT,
      sfx=[(T(142), 'tape_slowdown', -6, 0, None, dict(dur=2.6))], c=dict(mv='push', f=1.0, rate=0.03))
    # 143 W "...Clever."
    C(T(143), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=960, cy=760, scale=1.0, light=AMBER, act=lambda a, s: a.head_tilt(s.t0, 18.0, 0.5),
      c=dict(mv='push', rate=0.0, zrate=0.02))
    # 144 "The peephole goes white."  145 "Fur."  146 "Grin."
    C(T(144), 'set', room='front', view='peephole', set=FRONT_HIS, rim=AMBER,
      post_fn=lambda tt: dict(white=0.95 * clamp((tt - WD(144, 'white')) / 0.25)), c=dict(mv='push', f=1.0, rate=0.02))
    C(T(145), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=1240, cy=900, scale=2.6, light=AMBER, post=dict(vignette=0.9),
      c=dict(mv='push', rate=0.0, zrate=0.03))
    C(T(146), 'bust', who='whistle', bg=('front', 'porch'), set=FRONT_HIS, cx=960, cy=380, scale=2.6, light=AMBER, post=dict(vignette=0.9), hit=[WD(146, 'grin')],
      c=dict(mv='push', rate=0.0, zrate=0.03))
    # 147 "Across the yard, the real Grandma is pounding on the glass of bus 9."
    B9 = dict(his=True, his_heads=1.0, porch=0.0, letters=0.0, broom='bus9', cab9=0.6)

    def pound_fn(t0, x, ph):
        def fn(tt):
            u = ((tt - t0 + ph) % 0.45) / 0.45
            z = math.exp(-u * 6.0)                       # the fist hits the glass (toward the lens) and pulls back
            return (x + 20 * z, 760 - 30 * z, 180.0, 1.0, 250 * (1.0 + 0.25 * z))
        return fn
    pound = lambda a, s: a.knock_pattern(s.t0 + 0.1, (3, 3, 3), 1, beat=0.22, gap=0.3, target=scr(s.sp, 'b9_door', dx=40, dy=-330), kind='glass')
    C(T(147), 'set', room='front', view='driveway', set=B9, rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.015))
    C(W(147, 'pounding'), 'bust', who='della', bg=('front', 'bus9door'), set=B9, expr='shout', cx=960, cy=700, scale=0.8, light=NIGHT, talk=False,
      hands=[dict(who='della', fn=pound_fn(W(147, 'pounding'), x, ph), size=300, shape='grip', side=sd, sleeve_from=(x, 1500), depth=0.8)
             for x, ph, sd in ((560, 0.0, 1), (1360, 0.22, -1))],
      post=dict(dim=0.1), sfx=[(W(147, 'pounding') + 0.12 + 0.45 * k, 'glass_pound', -2, 0, 'outside', dict(index=k)) for k in range(6)],
      c=dict(mv='push', rate=0.0, zrate=0.01))
    # 148 "Trapped in her own cab, our porch broom wedged through her folding doors."
    C(T(148), 'set', room='front', view='bus9door', set=B9, rim=NIGHT, sfx=[(T(148) + 0.3 + 0.45 * k, 'glass_pound', -8, 0, 'outside', dict(index=k)) for k in range(5)],
      c=dict(mv='push', f=1.0, rate=0.03, y=600))
    # 149 D "DON'T OPEN THE DOOR!"
    C(T(149), 'bust', who='della', bg=('front', 'bus9door'), set=B9, expr='shout', cx=960, cy=640, scale=0.85, light=NIGHT, post=dict(blur=1),
      c=dict(mv='push', rate=0.0, zrate=0.02, hit=[(WD(149, "don't"), 3.0)]))
    # 150 "So I don't."  151 "Not even to run to her."
    C(T(150), 'set', room='hall', view='door', set=HALL_NIGHT, rim=NIGHT,
      ppl=[P('mina', 'peephole_eye', path=[(T(150) + 0.1, 'peephole_eye'), (E(150) + 0.3, (-3.95, 1.3))], expr='resolve', linear=True)], c=dict(mv='push', f=1.0, rate=0.01))
    C(T(151), 'set', room='hall', view='window', set=dict(HALL_NIGHT, broom='bus9', cab9=0.6), rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.02))
    # 152 "At the peephole, the grin whispers,"  153 W "Smart one. I'll ask Sami."  (his head tips up to the upstairs window)
    C(T(152), 'set', room='front', view='porch', set=dict(FRONT_HIS, broom='bus9', cab9=0.6), rim=AMBER,
      ppl=[ws('porch_door', face=(-3.95, 0.0), act=lambda a, s: a.set(s.t0, None, 0.9, ws_bend=0.55, h_tilt=-12.0))], c=dict(mv='push', f=1.0, rate=0.02))
    C(T(153), 'bust', who='whistle', bg=('front', 'porch'), set=dict(FRONT_HIS, broom='bus9', cab9=0.6), cx=960, cy=780, scale=1.0, light=AMBER,
      act=_A(pose(-9, None, 0.1, h_tilt=-12.0), wlook(WD(153, 'sami') - 0.1, (1300, 0), snap=False, dur=0.5)), c=dict(mv='push', rate=0.0, zrate=0.015))


# ==================================================================================================== RULE 4: REX, THE DARK, THE GLOVE, LIGHTHOUSE (154-189)
def plan_rule4(F):
    t, e, C = F.t, F.e, F.cut
    C(T(154), 'rule', n=4)
    # 157 "Sami pads upstairs for his dinosaur, Rex."
    C(T(157), 'set', room='hall', view='stairs', set=HALL_NIGHT, rim=NIGHT,
      ppl=[P('sami', 'stairs_foot', path=[(T(157), 'stairs_foot'), (T(157) + 1.2, 'stair2'), (E(158) + 0.5, 'stair6')], surface='stairs', expr='proud_grin')],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 158 S "Be right back!"
    C(T(158), 'bust', who='sami', bg=('hall', 'stairs'), set=HALL_NIGHT, expr='proud_grin', cx=960, cy=620, scale=0.85, turn=-0.4, light=NIGHT,
      act=_A(lambda a, s: a.look_at(s.t0, (1500, 800), dur=0.3), lambda a, s: a.wave(s.t0 + 0.1, E(158) + 0.2, 1)), c=dict(mv='push', rate=0.0, zrate=0.01))
    # 159 "I let him go."
    LIV_210 = dict(LIV_NIGHT, hall=0.6)
    C(T(159), 'set', room='living', view='couch3q', set=LIV_210, rim=NIGHT,
      ppl=[P('mina', 'couch_right', expr='neutral', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'stair6', dy=-200), dur=0.4), blinks(T(159) + 0.5)))],
      c=dict(mv='push', f=1.0, rate=0.01))
    # 160 "My walkie's on the cushion beside me."
    C(T(160), 'ins', name='walkie', kw=dict(talk=0.0), c=dict(mv='push', rate=0.025))
    # 161 "Two ten."  162 "Every light dies."
    C(T(161), 'set', room='living', view='couch3q', set=LIV_210, rim=NIGHT,
      ppl=[P('mina', 'couch_right', expr='fear', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'stair6', dy=-200), dur=0.4))],
      tags=[tagc(WD(161, 'two'), '2:10 AM', 'alert', 960, 170, 1.2)], c=dict(mv='push', f=1.0, rate=0.01))
    C(T(162), 'set', room='living', view='couch3q', set=LIV_BLACK, rim=DARK, cut='blink',
      ppl=[P('mina', 'couch_right', expr='fear', light=DARK, act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'couch_front', dx=-300, dy=-300), dur=0.2))],
      sfx=[(T(162), 'power_down', 0, 0, 'inside')], c=dict(mv='push', f=1.0, rate=0.0))
    # 163 "Total black."
    C(T(163), 'black', sfx=[(T(163), 'room_tone_drop', -12, 0, 'inside')])
    # 164-165 "A small hand slides into mine." "Cold."  (it is his glove, folded small: in the dark it reads as a child's hand)
    t_in = T(164) + 0.3
    C(T(164), 'set', room='living', view='hand', set=LIV_BLACK, rim=DARK,
      acts=lambda A, sh, sp: [hand_layer('mina', lambda tt: (1180, 800, -100.0, 1.0, 340, 0.0, 0.6), 340, 'open', 1, sleeve_from=(1750, 1100)),
                              hand_layer('sami', slide(t_in, t_in + 1.4, (700, 1250), (1030, 850), -60, -80, extra=lambda tt, r: r + (300, 0.0, 0.7)), 300, 'open', -1,
                                         sleeve_from=(500, 1500))],
      sfx=[(t_in, 'skin_slide', -10, 0, 'close', dict(dur=1.4))], c=dict(mv='push', f=1.0, rate=0.015))
    # 166 "Sami? That was fast."  (Mina whispers, eyes front in the dark)
    C(T(166), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_BLACK, expr='hush_fear', cx=960, cy=640, scale=0.85, turn=-0.2, light=DARK, post=dict(dim=0.15),
      act=_A(lambda a, s: a.look_at(s.t0, (400, 500), dur=0.2)), c=dict(mv='push', rate=0.0, zrate=0.01))
    # 167 "No answer."
    hold2 = lambda A, sh, sp: [hand_layer('mina', lambda tt: (1180, 800, -100.0, 1.0, 340, 0.0, 0.6), 340, 'grip', 1, sleeve_from=(1750, 1100)),
                               hand_layer('sami', lambda tt: (1030, 850, -80.0, 1.0, 300, 0.0, 0.7), 300, 'grip', -1, sleeve_from=(450, 1300))]
    C(T(167), 'set', room='living', view='hand', set=LIV_BLACK, rim=DARK, acts=hold2, c=dict(mv='push', f=1.0, rate=0.02))
    # 168 "From upstairs... Sami."  169-170 "Laughing." "Talking to someone on his walkie."
    C(T(168), 'set', room='hall', view='up', set=dict(hall=0.0, up=0.0), rim=DARK, sfx=[(WD(168, 'sami'), 'kid_laugh_far', -10, 0, 'inside')],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(T(169), 'set', room='sami', view='room', set=dict(ceil=0.0, hall=0.0, nightlight=0.0, bed='turned', rex='bed'), rim=NIGHT,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='proud_grin', act=_A(lambda a, s: a.radio_to_mouth(s.t0 + 0.1, s.t1 + 0.5, 1),
                                                                        lambda a, s: a.hold_prop('walkie', 1, -9, None), lambda a, s: a.head_tilt(s.t0 + 0.4, -12.0, 0.6)))],
      sfx=[(T(170) + 0.1, 'walkie_squelch', -6, 0, 'inside')], c=dict(mv='push', f=1.0, rate=0.015))
    # 171 "I'm still holding a hand."
    C(T(171), 'set', room='living', view='hand', set=LIV_BLACK, rim=DARK, acts=hold2, c=dict(mv='push', f=1.25, rate=0.03))
    # 172 "I turn on my phone light."
    C(T(172), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_BLACK, expr='fear', cx=960, cy=640, scale=0.85, turn=0.2,
      light=lambda tt: PHONE if tt >= WD(172, 'phone') else DARK, act=_A(lambda a, s: a.look_at(WD(172, 'phone'), (900, 1000), dur=0.2)),
      sfx=[(WD(172, 'phone'), 'phone_light_click', -6, 0, 'close')], c=dict(mv='push', rate=0.0, zrate=0.01))
    # 173-177 the glove in the phone light, folded small round her fingers (one knuckle too many); then HIM lifting her walkie
    def glove_acts(press0, push=0.0):
        def acts(A, sh, sp):
            def pool(pen, t):
                pen.glow(1120, 760, 520, '#dfeaff', 70)
            def glove(pen, t):
                pr = clamp(press0 + (t - sh.t0) * push)
                _glove_cursor(pen, 1150, 790, 5.2, 255, press=pr, curl=0.55)
            L_ = [Layer(0.95, pool, 'phone_pool', blur=0),
                  hand_layer('mina', lambda tt: (1180, 800, -100.0, 1.0, 340), 340, 'grip', 1, sleeve_from=(1750, 1100), light=PHONE),
                  Layer(0.85, glove, 'glove', blur=0)]
            return L_
        return acts
    C(T(173), 'set', room='living', view='hand', set=LIV_BLACK, rim=PHONE, acts=glove_acts(0.0), sfx=[(T(173) + 0.1, 'glove_creak', -6, 0.2, 'close')],
      c=dict(mv='push', f=1.0, rate=0.03))
    C(T(174), 'set', room='living', view='hand', set=LIV_BLACK, rim=PHONE, acts=glove_acts(0.0), c=dict(mv='push', f=1.45, rate=0.03, x=1120, y=600))
    C(T(175), 'set', room='living', view='hand', set=LIV_BLACK, rim=PHONE, acts=glove_acts(0.2, 0.6), sfx=[(T(175) + 0.3, 'glove_squeeze', -4, 0, 'close')],
      c=dict(mv='push', f=1.2, rate=0.04, x=1100, y=620))
    C(T(176), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_BLACK, expr='terrified_call', cx=900, cy=640, scale=0.9, turn=0.35, light=PHONE,
      act=_A(lambda a, s: a.look_at(s.t0, (1400, 900), dur=0.1)), c=dict(mv='push', rate=0.0, zrate=0.03))
    C(T(177), 'bust', who='whistle', bg=('living', 'couch3q'), set=LIV_BLACK, cx=1000, cy=900, scale=0.85, turn=-0.3, light=dict(PHONE, dark=0.35),
      act=lambda a, s: a.walkie_to_grin(WD(177, 'walkie') - 0.3, -1, None, 0.6), sfx=[(WD(177, 'walkie'), 'walkie_squelch', -6, 0.2, 'inside')],
      c=dict(mv='push', rate=0.0, zrate=0.015))
    C(T(178), 'bust', who='whistle', bg=('living', 'couch3q'), set=LIV_BLACK, cx=960, cy=820, scale=1.0, light=dict(PHONE, dark=0.3),
      act=lambda a, s: a.walkie_to_grin(-9, -1, None, 0.01), hit=[T(178) + 0.05], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 179 "I rip free."
    C(T(179), 'bust', who='mina', bg=('living', 'couch3q'), set=LIV_BLACK, expr='terrified_call', cx=960, cy=640, scale=0.9, light=PHONE,
      act=_A(lambda a, s: a.set(WD(179, 'rip') - 0.1, None, 0.2, lean=-0.3, h_tilt=-8.0)), sfx=[(WD(179, 'rip'), 'rip_free', -2, 0, 'close')],
      c=dict(mv='push', rate=0.0, zrate=0.0, hit=[(WD(179, 'rip'), 4.0)]))
    # 180-181 "The lights snap back on." "Nobody's there."
    LIV_BACK = dict(LIV_NIGHT, hall=0.8, walkie=False)
    C(T(180), 'set', room='living', view='couch3q', set=LIV_BACK, rim=NIGHT, cut='white', quiet_cut=True,
      ppl=[P('mina', 'couch_right', expr='terrified_call', act=_A(lambda a, s: a.look_at(s.t0 + 0.2, scr(s.sp, 'couch_front', dx=200, dy=-300), dur=0.25),
                                                                  lambda a, s: a.look_at(T(181), scr(s.sp, 'couch_front', dx=-300, dy=-350), dur=0.35)))],
      sfx=[(T(180), 'power_up', 0, 0, 'inside')], c=dict(mv='push', f=1.0, rate=0.01))
    # 182 "Neither is my walkie."
    C(T(182), 'set', room='living', view='hand', set=LIV_BACK, rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.03))
    # 183-184 "Upstairs, Sami's hugging Rex." "Proud of himself."
    SAMI_LIT = dict(ceil=1.0, hall=1.0, bed='turned')
    C(T(183), 'set', room='sami', view='room', set=SAMI_LIT, rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='proud_grin', act=_A(lambda a, s: a.hug_prop(s.t0 + 0.1, 'rex'), lambda a, s: a.hold_prop('walkie', -1, -9, None)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 185 S "You told me on the walkie to say our word, so you'd know it was really me! So I did!"
    C(T(185), 'bust', who='sami', bg=('sami', 'room'), set=SAMI_LIT, expr='proud_grin', cx=960, cy=660, scale=0.85, turn=0.25, light=LAMP,
      act=_A(lambda a, s: a.look_at(s.t0, (1500, 450), dur=0.3), lambda a, s: a.hug_prop(-9, 'rex')), c=dict(mv='push', rate=0.0, zrate=0.01))
    C(W(185, 'so', 1), 'bust', who='sami', bg=('sami', 'room'), set=SAMI_LIT, expr='proud_grin', cx=700, cy=700, scale=0.72, turn=0.45, light=LAMP,
      act=_A(lambda a, s: a.look_at(s.t0, (1450, 420), dur=0.3), lambda a, s: a.hug_prop(-9, 'rex')),
      busts=[dict(who='mina', cx=1350, cy=640, scale=0.8, turn=-0.5, expr='terrified_call', light=LAMP, act=lambda a, s: a.look_at(s.t0, (700, 640), dur=0.2))],
      c=dict(mv='push', rate=0.0, zrate=0.01))
    # 186 "Sami... what did you say?"
    C(T(186), 'bust', who='mina', bg=('sami', 'room'), set=SAMI_LIT, expr='fear', cx=960, cy=640, scale=0.85, turn=-0.3, light=LAMP,
      act=_A(lambda a, s: a.look_at(s.t0, (300, 800), dur=0.3)), c=dict(mv='push', rate=0.0, zrate=0.012))
    # 187 S "LIGHTHOUSE!"
    C(T(187), 'bust', who='sami', bg=('sami', 'room'), set=SAMI_LIT, expr='shout_here', cx=960, cy=660, scale=0.92, light=LAMP,
      act=lambda a, s: a.hug_prop(-9, 'rex'), hit=[WD(187, 'lighthouse')], c=dict(mv='push', rate=0.0, zrate=0.02))
    # 188 "Then it's not our word anymore."  HIM on the porch with her walkie at the grin, head tilting up
    C(T(188), 'set', room='front', view='porch', set=dict(FRONT_HIS, broom='bus9', cab9=0.5), rim=AMBER,
      ppl=[ws('porch_step', face=(-3.95, 0.0), act=_A(lambda a, s: a.walkie_to_grin(-9, -1, None, 0.01), lambda a, s: a.head_tilt(s.t0 + 0.3, 16.0, 0.8)))],
      sfx=[(T(188) + 0.2, 'walkie_squelch', -4, 0, 'outside')], c=dict(mv='push', f=1.0, rate=0.02))
    # 189 "A word only works while it's secret."
    C(T(189), 'ins', name='rules', kw=dict(show=7, hl=3), c=dict(mv='push', rate=0.02))


# ==================================================================================================== PART B helpers
HEADS9 = dict(rim='#fff2d6', rim_a=110, side=1, key=-0.15)                # bus 9's headlights on us at the school
HEADS9_L = dict(HEADS9, side=-1)
FAKE = dict(rim='#ffb040', rim_a=150, side=-1, key=-0.4, dark=0.25)        # the fake Mina: amber, wrong
DASH9 = dict(rim='#9fc0ff', rim_a=70, side=1, key=-0.3)                   # bus 9's cab at night (dash light)
GR = dict(lamp=1.0, ceil=0.7, hall=0.0)                                   # Grandma's room after the lights came back (L180)
UPF, BU_GF = 2.95, -0.5                                                   # upstairs floor / the yard (plan tuples carry their floor)
FRONT_B9 = dict(FRONT_HIS, broom='bus9', cab9=0.5)                        # his bus at the kerb; the broom through bus 9's doors
HIS = dict(kind='his')
HIS_D = dict(kind='his', door=1.0)
B9N = dict(kind='bus9', tod='night')
B9M = dict(kind='bus9', tod='morning')
SCH0 = dict(clock=(2, 57), his_door=0.0)


def PU(r=0.015, f=1.0, **k): return dict(mv='push', f=f, rate=r, **k)


def BZ(z=0.012, **k): return dict(mv='push', rate=0.0, zrate=z, **k)


def bust(t0, who, bg, st, expr=None, light=NIGHT, cx=960, cy=640, scale=0.85, turn=0.0, act=None, z=0.012, **k):
    _FILM[0].cut(t0, 'bust', who=who, bg=bg, set=st, expr=expr, cx=cx, cy=cy, scale=scale, turn=turn, light=light, act=act,
                 c=k.pop('c', BZ(z)), **k)


def wbust(t0, bg, st, act=None, cx=960, cy=820, scale=0.9, light=AMBER, z=0.02, **k):
    """A Whistlestop close-up: never still (the act keeps him tilting, leaning, closing)."""
    _FILM[0].cut(t0, 'bust', who='whistle', bg=bg, set=st, cx=cx, cy=cy - 230, scale=scale, light=light, act=act, c=k.pop('c', BZ(z)), **k)


def blinkf(*wins):
    """A level that is 1 inside any (t0, t1) window."""
    return lambda tt: 1.0 if any(a <= tt < b for (a, b) in wins) else 0.0


def glove_on(x, y, s=4.2, press0=0.0, press1=0.0, t0=0.0, t1=1.0, a=255, curl=0.35, drift=None, name='glove', down=True):
    """HIS glove as a flat graphic settled on something (a shoulder) in a close-up; press ramps press0 -> press1."""
    def draw(pen, t):
        u = ease_in_out(clamp((t - t0) / max(1e-3, t1 - t0)))
        dx, dy = drift(t) if drift else (0.0, 0.0)
        gx, gy = x + dx, y + dy
        if down:
            pen.seg((gx - 40 * s, gy - 60 * s), (gx - 900, gy - 900), 22 * s, '#a88a3a', a)          # the mustard sleeve, off frame
            pen.seg((gx - 12 * s, gy - 22 * s), (gx - 40 * s, gy - 60 * s), 15 * s, '#7a6a55', a)   # tabby wrist
            cv = pen.cv; cv.save(); cv.translate(gx, gy); cv.rotate(150); cv.translate(-gx, -gy)
            _glove_cursor(pen, gx, gy, s, a, press=lerp(press0, press1, u), curl=curl)
            cv.restore()
        else:
            _glove_cursor(pen, gx, gy, s, a, press=lerp(press0, press1, u), curl=curl)
    lay = Layer(0.85, draw, name, blur=0)
    lay.order = -9.0
    return lay


def palm_glass(x, y, size, t_on, who='sami'):
    def draw(pen, t):
        CH.draw_palm_on_glass(pen, who, x, y, size, press=clamp((t - t_on) / 0.3), t=t)
    lay = Layer(0.8, draw, 'palm', blur=0)
    lay.order = -9.0
    return lay


# ==================================================================================================== RULE 5: THE DEADBOLT, THE HALLWAY, THE CAPTURE (190-238)
def plan_rule5(F):
    t, e, C = F.t, F.e, F.cut
    C(T(190), 'rule', n=5)
    # 193 "Grandma's room has the only deadbolt."  Mina throws it: reach (bolt open) | on the word: thrown, tight on the door
    C(T(193), 'set', room='gran', view='wide', set=dict(GR, bolt=0.0), rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='fear', act=_A(lambda a, s: a.hug_prop(-9, 'rex'), lambda a, s: a.look_at(T(193) + 0.2, scr(s.sp, 'door_in', dy=-150), dur=0.4))),
           P('mina', 'door_in', face=(-4.0, 3.3), expr='resolve',
             act=_A(lambda a, s: a.reach_to(T(193) + 0.25, 1, scr(s.sp, 'deadbolt'), dur=0.5, contact='grip', shape='grip', z=10.0),
                    lambda a, s: a.look_at(T(193), scr(s.sp, 'deadbolt'), dur=0.3)))],
      c=PU(0.015, 1.5, x=1040, y=800))
    C(W(193, 'deadbolt'), 'set', room='gran', view='door', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('mina', 'door_in', face=(-4.0, 3.3), expr='resolve',
             act=_A(lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'deadbolt'), dur=0.01, contact='grip', shape='grip', z=10.0),
                    lambda a, s: a.set(WD(193, 'deadbolt'), None, 0.12, lean=0.06)))],
      sfx=[(WD(193, 'deadbolt') + 0.05, 'deadbolt', 0, 0, 'inside')], c=PU(0.02, 1.3, x=900, y=620, hit=[(WD(193, 'deadbolt') + 0.05, 3.0)]))
    # 194 "I sit with my back against it."  she slides down the door to the floor; Sami on the bed edge with Rex
    C(T(194), 'set', room='gran', view='wide', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='fear', act=_A(lambda a, s: a.hug_prop(-9, 'rex'), lambda a, s: a.look_at(T(194), scr(s.sp, 'door_sit', dy=-120), dur=0.4))),
           P('mina', 'door_sit', kind='stand', face='room_mid', expr='resolve',
             act=_A(lambda a, s: a.sit_floor(T(194) + 0.15, None, 0.9), lambda a, s: a.look_at(T(194) + 0.6, scr(s.sp, 'bed_edge', dy=-200), dur=0.4)))],
      sfx=[(T(194) + 0.2, 'cloth_slide_door', -8, 0, 'inside', dict(dur=0.9))], c=PU(0.015, 1.5, x=1040, y=800))
    # 195 "The word's dead, Sami. Nobody opens."  (Mina, lip sync)
    bust(T(195), 'mina', ('gran', 'door'), dict(GR, bolt=1.0), 'resolve', LAMP, cx=760, cy=680, scale=0.8, turn=0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (1450, 640), dur=0.3), blinks(E(195) - 0.2)),
         busts=[dict(who='sami', cx=1460, cy=720, scale=0.6, turn=-0.5, expr='fear', light=LAMP, act=lambda a, s: a.look_at(s.t0, (760, 620), dur=0.3))])
    # 196 "Two thirty-one."
    C(T(196), 'set', room='gran', view='wide', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='sleepy', act=_A(lambda a, s: a.hug_prop(-9, 'rex'), blinks(T(196) + 0.4))),
           P('mina', 'door_sit', face='room_mid', expr='hush_fear', act=_A(lambda a, s: a.look_at(T(196) + 0.1, scr(s.sp, 'window', dy=-150), dur=0.5)))],
      tags=[tagc(WD(196, 'two'), '2:31 AM', 'alert', 960, 170, 1.2)], c=PU(0.012, 1.5, x=1040, y=800))
    # 197 "Down in the driveway, a flashlight blinks inside bus 9."  198 "Three times."
    b0 = WD(197, 'blinks')
    fl = blinkf((b0, b0 + 0.18))
    C(T(197), 'set', room='front', view='granout', set=dict(FRONT_B9, flash=fl), rim=AMBER,
      sfx=[(b0, 'flashlight_click', -8, 0, 'outside')], c=PU(0.02))
    C(T(198), 'ins', name='flashlight', kw=lambda u: dict(on=1.0 if (u < 0.12 or 0.24 <= u < 0.36 or 0.48 <= u < 0.6) else 0.0),
      sfx=[(T(198) + 0.24 * k, 'flashlight_click', -6, 0, 'close') for k in range(3)], c=dict(mv='push', rate=0.04))
    # 199 "Is she free?"
    bust(T(199), 'mina', ('gran', 'window'), dict(GR, bolt=1.0), 'relief', LAMP, cx=1000, cy=640, scale=0.85, turn=-0.25,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 560), dur=0.3), pose(T(199) + 0.2, None, 0.4, breath=1.0)))
    # 200-201 "I go to the window." "Just for a second."  (her back to the door)
    C(T(200), 'set', room='gran', view='wide', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='fear', act=_A(lambda a, s: a.hug_prop(-9, 'rex'), lambda a, s: a.look_at(T(200) + 0.3, scr(s.sp, 'window', dy=-150), dur=0.5))),
           P('mina', 'door_in', path=[(T(200), 'door_in'), (T(200) + 1.6, (-4.85, 1.75, UPF))], surface='inside', expr='hush_fear',
             act=_A(lambda a, s: a.look_at(T(200), scr(s.sp, 'window', dy=-200), dur=0.4),
                    lambda a, s: a.look_at(T(200) + 1.75, scr(s.sp, 'window', dy=-260), dur=0.5)))],
      c=PU(0.012, 1.45, x=880, y=780))
    # 202 "Knock, knock."  (the bolted door, nobody at it)
    kk = [WD(202, 'knock', 0), WD(202, 'knock', 1)]
    C(T(202), 'set', room='gran', view='door', set=dict(GR, bolt=1.0), rim=LAMP,
      sfx=[(k_, 'knock_door', -2, 0, 'inside', dict(kind='wood')) for k_ in kk], c=PU(0.02, 1.15, hit=[(k_, 3.0) for k_ in kk]))
    # 203 W "It's me, sweetheart."  Mina turns from the window; Sami sits up
    C(T(203), 'set', room='gran', view='wide', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', 'bed_edge', kind='seat', expr='dazed', act=_A(lambda a, s: a.hug_prop(-9, 'rex'), lambda a, s: a.look_at(T(203) + 0.1, scr(s.sp, 'door_in', dy=-160), dur=0.2),
                                                                  pose(T(203) + 0.1, None, 0.25, lean=-0.1))),
           P('mina', (-4.85, 1.75, UPF), face='door_in', expr='fear', act=lambda a, s: a.look_at(T(203) + 0.05, scr(s.sp, 'door_in', dy=-200), dur=0.25, body=0.4))],
      c=PU(0.015, 1.4, x=900, y=800))
    # 204-206 "Grandma's voice." "Calm." "Warm."
    bust(T(204), 'mina', ('gran', 'window'), dict(GR, bolt=1.0), 'tempted', LAMP, cx=960, cy=640, scale=0.9, turn=0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 620), dur=0.3), blinks(T(206) + 0.1)), z=0.02)
    # 207 W "Lighthouse."
    C(T(207), 'set', room='gran', view='door', set=dict(GR, bolt=1.0), rim=LAMP, hit=[WD(207, 'lighthouse')], c=PU(0.04, 1.2))
    # 208 "Sami's already up."  he runs for the door
    C(T(208), 'set', room='gran', view='wide', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', (-3.7, 2.25, UPF), path=[(T(208), (-3.7, 2.25, UPF)), (T(208) + 0.9, (-3.95, 2.55, UPF))], run=True, surface='inside', expr='proud_grin',
             act=lambda a, s: a.hug_prop(-9, 'rex')),
           P('mina', (-4.85, 1.75, UPF), face='door_in', expr='terrified_call',
             act=_A(lambda a, s: a.look_at(T(208), scr(s.sp, 'door_in', dy=-120), dur=0.15),
                    lambda a, s: a.reach_to(T(208) + 0.4, 1, scr(s.sp, 'door_in', dx=-80, dy=-200), dur=0.4, contact='palm', shape='open', z=60.0)))],
      c=PU(0.012, 1.4, x=900, y=800))
    # 209 S "That's the word! That's the RULE!"
    bust(T(209), 'sami', ('gran', 'door'), dict(GR, bolt=1.0), 'shout_here', LAMP, cx=960, cy=680, scale=0.85, turn=-0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 600), dur=0.2), lambda a, s: a.hug_prop(-9, 'rex')))
    # 210 "Sami, NO..."  (Mina, lip sync) her hand flies out
    bust(T(210), 'mina', ('gran', 'wide'), dict(GR, bolt=1.0), 'terrified_call', LAMP, cx=900, cy=640, scale=0.85, turn=0.3,
         act=lambda a, s: a.look_at(s.t0, (1500, 700), dur=0.15),
         hands=[dict(who='mina', fn=slide(T(210) + 0.05, T(210) + 0.35, (1700, 1250), (1420, 820), -40, -70), size=330, shape='open', side=1, sleeve_from=(1900, 1400))])
    # 211 "The deadbolt slides."  Sami's hand on it | on the word: slid back
    sami_bolt = lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'deadbolt'), dur=0.01, contact='grip', shape='grip', z=10.0)
    C(T(211), 'set', room='gran', view='door', set=dict(GR, bolt=1.0), rim=LAMP,
      ppl=[P('sami', 'door_in', face=(-4.0, 3.3), expr='proud_grin', act=sami_bolt)], c=PU(0.02, 1.3, x=900, y=600))
    C(W(211, 'slides'), 'set', room='gran', view='door', set=dict(GR, bolt=0.0), rim=LAMP,
      ppl=[P('sami', 'door_in', face=(-4.0, 3.3), expr='proud_grin', act=_A(sami_bolt, pose(WD(211, 'slides'), None, 0.15, lean=-0.06)))],
      sfx=[(WD(211, 'slides'), 'deadbolt_slide', 0, 0, 'inside')], c=PU(0.03, 2.2, x=901, y=560))
    # 212-215 the hallway is full of him: bent double, the hat crushed against the ceiling, gloves flat on both walls
    UPH = dict(up=0.0, gran=0.6, gran_door=95)

    def bent(t_walls=None, skip=None, look=None):
        def f(a, s):
            a.bend_double(-1.0, scr(s.sp, 'ceiling')[1], None, 0.01, crouch=0.4, bend=1.0)
            if t_walls is not None:
                a.walls_flat(t_walls, scr(s.sp, 'wall_l', dy=270), scr(s.sp, 'wall_r', dy=270), dur=0.35)
            if skip: skip(a, s)
            if look: look(a, s)
        return f
    C(T(212), 'set', room='upstairs', view='hall', set=UPH, rim=AMBER, hit=[T(212) + 0.05],
      ppl=[ws((-4.0, 6.0, UPF), face=(-4.0, 2.0), act=bent(-9, skip_to((-9, (-4.0, 6.4, UPF)), (T(212) + 0.55, (-4.0, 5.6, UPF))), lambda a, s: a.head_tilt(T(212) + 0.7, 12.0, 0.6)))],
      sfx=[(T(212), 'door_creak_open', -6, 0, 'inside')], c=PU(0.02))
    C(T(213), 'set', room='upstairs', view='hall', set=UPH, rim=AMBER, cut='vhs',
      ppl=[ws((-4.0, 5.2, UPF), face=(-4.0, 2.0), act=bent(-9, None, pose(T(213) + 0.1, None, 0.5, ws_bend=1.15)))],
      sfx=[(T(213), 'tape_skip', 0, 0, None)], c=PU(0.03, 1.15))
    C(T(214), 'set', room='upstairs', view='hall', set=UPH, rim=AMBER,
      ppl=[ws((-4.0, 5.2, UPF), face=(-4.0, 2.0), act=bent(-9, None, lambda a, s: a.head_tilt(T(214) + 0.2, -10.0, 0.9)))],
      sfx=[(T(214) + 0.2, 'hat_crumple', -6, 0, 'inside')], c=PU(0.03, 1.9, x=960, y=330))
    C(T(215), 'set', room='upstairs', view='hall', set=UPH, rim=AMBER,
      ppl=[ws((-4.0, 5.2, UPF), face=(-4.0, 2.0), act=bent(WD(215, 'gloves') - 0.1))],
      sfx=[(WD(215, 'gloves') + 0.25, 'glove_slap_wall', -2, -0.4, 'inside'), (WD(215, 'gloves') + 0.3, 'glove_slap_wall', -2, 0.4, 'inside')],
      c=PU(0.02, 1.0, hit=[(WD(215, 'gloves') + 0.25, 3.0)]))
    # 216 W "Sami?"
    wbust(T(216), ('upstairs', 'hall'), UPH, cx=960, cy=900, scale=1.0, act=_A(pose(-9, None, 0.1, h_tilt=-8.0), lambda a, s: a.head_tilt(T(216), 24.0, 0.5)))
    # 217-218 "Sami's practiced all week." "His mouth answers before his head does."
    bust(T(217), 'sami', ('upstairs', 'back'), dict(up=0.0, gran=0.6, gran_door=95), 'dazed', AMBER, cx=960, cy=660, scale=0.9, turn=0.15,
         act=_A(lambda a, s: a.look_at(s.t0, (1300, 430), dur=0.3), lambda a, s: a.hug_prop(-9, 'rex'), pose(T(218) + 0.3, None, 0.5, h_tilt=-6.0),
                ex('proud_grin', W(218, 'answers'), None, 0.3)))
    # 219 S "HERE!"
    bust(T(219), 'sami', ('upstairs', 'back'), dict(up=0.0, gran=0.6, gran_door=95), 'shout_here', AMBER, cx=960, cy=660, scale=1.0, turn=0.1,
         act=_A(lambda a, s: a.look_at(s.t0, (1300, 430), dur=0.1), lambda a, s: a.hug_prop(-9, 'rex')), hit=[WD(219, 'here')], c=BZ(0.03, hit=[(WD(219, 'here'), 4.0)]))
    # 220 "Click-clack."
    C(T(220), 'ins', name='punch', kw=lambda u: dict(click=1.0 if 0.12 < u < 0.26 or 0.38 < u < 0.52 else 0.0),
      sfx=[(T(220) + 0.12, 'punch_clack', 0, 0, 'close')], c=dict(mv='push', rate=0.03))
    # 221 "He takes Sami's hand, like a crossing guard."  222 "I grab the other."  (from inside Grandma's room, through the door)
    HCAM = cm((-4.0, 1.75, 4.15), (-4.0, 5.0, 3.95), 1000.0)

    def capture(t_hold, t_grab, hk=1.0, f=1.0, x=960, y=540):
        return dict(room='upstairs', view='hall', cam=HCAM, set=UPH, rim=AMBER,
                    ppl=[P('sami', (-4.05, 4.35, UPF), face=(-4.0, 6.0), expr='proud_grin'),
                         ws((-4.0, 5.35, UPF), face=(-4.0, 2.0), act=bent(-9, None, lambda a, s: a.hold_child(t_hold, 1, s.A['sami'], -1, dur=0.8))),
                         P('mina', (-4.38, 3.95, UPF), face=(-4.0, 6.0), expr='terrified_call',
                           act=_A(lambda a, s: a.look_at(-9, (s.A['sami'], 'eyes'), dur=0.3),
                                  lambda a, s: a.hold_hand(t_grab, -1, s.A['sami'], 1, dur=0.4)))],
                    c=PU(0.02, f, x=x, y=y))
    C(T(221), 'set', **capture(T(221) + 0.4, T(222) + 0.05))
    C(T(222), 'set', **capture(-9, T(222) + 0.05, f=1.6, x=900, y=640))
    # 223 "The lights blink, and we're on the stairs."  blink: the stairs | 224-225 front hall | 226-227 the lawn | 228-229 his bus steps
    C(W(223, 'stairs'), 'set', room='hall', view='stairs', set=dict(HALL_NIGHT, hall=0.0), rim=AMBER, cut='blink',
      ppl=[P('sami', 'stair10', face='stair2', expr='dazed', act=lambda a, s: a.look_at(-9, scr(s.sp, 'stair2', dy=-300), dur=0.3)),
           P('mina', 'stair13', face='stair2', expr='terrified_call', act=lambda a, s: a.hold_hand(-9, -1, s.A['sami'], 1, dur=0.01)),
           ws('stair6', face='stairs_foot', act=lambda a, s: a.hold_child(-9, 1, s.A['sami'], -1, dur=0.01))],
      sfx=[(T(223) + 0.1, 'lights_blink', -4, 0, 'inside'), (W(223, 'stairs'), 'tape_skip', -2, 0, None)], c=PU(0.02))
    C(T(224), 'set', room='hall', view='stairs', set=dict(HALL_NIGHT, hall=0.0), rim=AMBER, cut='blink',
      ppl=[ws('hall_mid', face='opening', act=lambda a, s: a.head_tilt(T(225), 10.0, 0.4)),
           P('sami', 'stairs_foot', face='hall_mid', expr='dazed'),
           P('mina', 'stair2', face='hall_mid', expr='terrified_call', act=lambda a, s: a.hold_hand(-9, -1, s.A['sami'], 1, dur=0.01))],
      sfx=[(T(224), 'lights_blink', -4, 0, 'inside')], c=PU(0.02))
    C(T(226), 'set', room='front', view='street', set=dict(FRONT_B9, his_door=1.0), rim=AMBER, cut='blink',
      ppl=[ws((-3.2, -8.0, BU_GF), face='his_step'), P('sami', (-3.6, -7.4, BU_GF), face='his_step', expr='dazed'),
           P('mina', (-4.0, -6.8, BU_GF), face='his_step', expr='terrified_call', act=lambda a, s: a.hold_hand(-9, -1, s.A['sami'], 1, dur=0.01))],
      sfx=[(T(226), 'lights_blink', -4, 0, 'outside')], c=PU(0.02))
    # 228-231 his bus steps; Sami's hand slips out of mine; the doors slap shut an inch from my fingers
    CURB = dict(FRONT_B9, his_door=1.0)
    C(T(228), 'set', room='front', view='curb', set=CURB, rim=AMBER, cut='blink',
      ppl=[P('sami', 'his_step', face='his_top', expr='dazed'),
           ws('his_top', face='his_door', act=lambda a, s: a.hold_child(-9, 1, s.A['sami'], -1, dur=0.01)),
           P('mina', 'his_door', face='his_step', expr='terrified_call', act=lambda a, s: a.hold_hand(-9, -1, s.A['sami'], 1, t1=W(230, 'slips') + 0.3, dur=0.01))],
      sfx=[(T(228), 'lights_blink', -4, 0, 'outside')], c=PU(0.025, 1.2, x=940, y=700))
    C(T(230), 'set', room='front', view='curb', set=CURB, rim=AMBER,
      ppl=[P('sami', 'his_step', path=[(T(230), 'his_step'), (T(230) + 0.9, (-3.19, -12.9, 0.1))], face='his_top', expr='cry', no_walk=False),
           ws('his_top', face='his_door', act=lambda a, s: a.hold_child(-9, 1, s.A['sami'], -1, dur=0.01)),
           P('mina', 'his_door', face='his_step', expr='terrified_call',
             act=_A(lambda a, s: a.hold_hand(-9, -1, s.A['sami'], 1, t1=WD(230, 'slips') + 0.1, dur=0.01),
                    lambda a, s: a.reach_to(WD(230, 'slips') + 0.2, -1, scr(s.sp, 'his_step', dy=-140), dur=0.5, contact='palm', shape='open', z=40.0)))],
      sfx=[(WD(230, 'slips'), 'hand_slip', -6, 0, 'close')], c=PU(0.03, 1.9, x=960, y=650))
    shut = lambda tt: 1.0 - ease_in_cubic(clamp((tt - (WD(231, 'slap') - 0.12)) / 0.12))
    C(T(231), 'set', room='front', view='curb', set=dict(FRONT_B9, his_door=shut), rim=AMBER,
      ppl=[P('mina', 'his_door', face='his_step', expr='terrified_call',
             act=lambda a, s: a.reach_to(T(231) + 0.1, -1, scr(s.sp, 'his_door', dy=-170), dur=0.5, contact='palm', shape='open', z=30.0))],
      sfx=[(WD(231, 'slap'), 'door_slap', 2, 0, 'outside')], c=PU(0.02, 1.6, x=980, y=700, hit=[(WD(231, 'slap'), 6.0)]))
    # 232 "Sami's palm presses against the window of seat four."  (inside his bus, the glass between us)
    bust(T(232), 'sami', ('bus', 'seat4'), HIS, 'cry', AMBER, cx=900, cy=640, scale=0.85, turn=0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 600), dur=0.3), blinks(T(232) + 1.6)),
         acts=lambda A, sh, sp: [palm_glass(1320, 620, 320, T(232) + 0.5)], post=dict(dim=0.05))
    # 233-235 "Every other seat is dark." "Except one." "Way in the back."
    C(T(233), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={4: 1.0, 22: 0.9}), rim=AMBER,
      ppl=[P('sami', 'seat4', kind='seat', expr='cry', act=lambda a, s: a.look_at(-9, scr(s.sp, 'window4'), dur=0.01)),
           P('theo', 'seat22', kind='seat', expr='lonely', alpha=0.6)], c=PU(0.012))
    C(T(234), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={4: 1.0, 22: 0.9}), rim=AMBER,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', alpha=0.6, act=_A(lambda a, s: a.look_at(T(235), (960, 520), dur=0.6), blinks(T(235) + 0.4)))],
      c=PU(0.04, 2.6, x=1000, y=560))
    # 236 "Over the loudspeaker:"  237 W "Seat's saved, Mina. Right next to him."
    C(T(236), 'set', room='front', view='curb', set=dict(FRONT_B9, his_door=0.0), rim=AMBER,
      ppl=[ws('his_driver', kind='seat', face='his_door', act=_A(lambda a, s: a.look_at(T(236) + 0.2, scr(s.sp, 'his_door', dx=60, dy=-150), dur=0.08, snap=True))),
           P('mina', 'his_door', face='his_driver', expr='terrified_call', act=lambda a, s: a.look_at(T(236), scr(s.sp, 'his_driver', dy=-120), dur=0.3))],
      sfx=[(T(236) + 0.6, 'loudspeaker_click', -4, 0, 'outside')], c=PU(0.02, 1.4, x=900, y=650))
    wbust(T(237), ('front', 'curb'), dict(FRONT_B9, his_door=0.0), cx=1000, cy=860, scale=0.95,
          act=_A(pose(-9, None, 0.1, h_tilt=-10.0), lambda a, s: a.head_tilt(W(237, 'right'), 18.0, 0.5)), post=dict(glitch=0.05))
    # 238 "The bus pulls away with no lights on."  it skips away down the street, dark
    for k, (tk, hx) in enumerate([(T(238), -0.2), (T(238) + 0.75, -9.0), (T(238) + 1.45, -18.0)]):
        C(tk, 'set', room='front', view='street', set=dict(FRONT_B9, his_x=hx, his_win=0.0, his_heads=0.0, his_door=0.0), rim=NIGHT, cut='vhs' if k else None,
          ppl=[P('mina', 'walk', face='street_mid', expr='terrified_call', act=lambda a, s: a.look_at(-9, scr(s.sp, 'street_mid', dx=-300, dy=-100), dur=0.3))],
          sfx=[(tk, 'bus_pull_away', -2, 0, 'outside')] if k == 0 else [(tk, 'tape_skip', -4, 0, None)], c=PU(0.015))


# ==================================================================================================== RULE 6: BUS 9, THE CALL, 1994, THE CHASE (239-285)
def plan_rule6(F):
    t, e, C = F.t, F.e, F.cut
    C(T(239), 'rule', n=6)
    AFTER = dict(FRONT_B9, his=False)
    # 243 "I don't chase him."
    bust(T(243), 'mina_bare', ('front', 'street'), dict(AFTER), 'resolve', NIGHT, cx=900, cy=640, scale=0.85, turn=-0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 560), dur=0.3), lambda a, s: a.look_at(T(243) + 0.8, (1600, 620), dur=0.25, body=0.5), pose(T(243), None, 0.4, breath=1.0)))
    # 244 "I run to bus 9."
    C(T(244), 'set', room='front', view='sideyard', set=dict(AFTER), rim=PORCH,
      ppl=[P('mina_bare', (-5.9, -0.5, BU_GF), path=[(T(244), (-5.9, -0.5, BU_GF)), (E(244) + 0.25, 'b9_door')], run=True, surface='grass', expr='resolve')],
      c=PU(0.015))
    # 245 "I rip the porch broom out of its doors and toss it in."
    C(T(245) - 0.35, 'set', room='front', view='bus9door', set=dict(AFTER), rim=PORCH,
      ppl=[P('mina_bare', 'b9_door', face=(-8.3, -1.0), expr='resolve',
             act=_A(lambda a, s: a.reach_to(T(245) - 0.25, 1, scr(s.sp, 'b9_step', dx=-60, dy=-260), dur=0.35, contact='grip', shape='grip', z=30.0),
                    lambda a, s: a.reach_to(T(245) - 0.2, -1, scr(s.sp, 'b9_step', dx=40, dy=-300), dur=0.35, contact='grip', shape='grip', z=30.0),
                    pose(WD(245, 'rip'), None, 0.15, lean=-0.18)))],
      sfx=[(WD(245, 'rip'), 'broom_rip', 0, 0, 'outside')], c=PU(0.02, hit=[(WD(245, 'rip'), 3.0)]))
    C(WD(245, 'rip') + 0.08, 'set', room='front', view='bus9door', set=dict(AFTER, broom=None, cab9=0.8), rim=PORCH,
      ppl=[P('mina_bare', 'b9_door', face=(-8.3, -1.0), expr='resolve',
             act=_A(lambda a, s: a.hold_prop('broom', 1, -9, None), pose(-9, None, 0.1, lean=-0.18), pose(WD(245, 'rip') + 0.3, None, 0.4, lean=0.0)))],
      c=PU(0.02, hit=[(WD(245, 'rip') + 0.08, 3.0)]))
    C(W(245, 'toss'), 'set', room='front', view='bus9door', set=dict(AFTER, broom=None, door9=1.0, cab9=0.8), rim=PORCH,
      ppl=[P('mina_bare', 'b9_door', face=(-8.3, -1.0), expr='resolve',
             act=_A(lambda a, s: a.hold_prop('broom', 1, -9, W(245, 'toss') + 0.3),
                    lambda a, s: a.reach_to(W(245, 'toss') + 0.05, 1, scr(s.sp, 'b9_top'), dur=0.3, contact='palm', shape='open', z=40.0)))],
      sfx=[(W(245, 'toss') + 0.05, 'bus_door_spring', -2, 0, 'outside'), (W(245, 'toss') + 0.35, 'broom_clatter_in', -6, 0, 'outside')], c=PU(0.02))
    # 246 "Grandma's at the wheel."
    wheel = lambda s: scr(s.sp, 'wheel')
    drive = lambda a, s: a.drive(-9, None, (wheel(s)[0] - 70, wheel(s)[1] - 10), (wheel(s)[0] + 70, wheel(s)[1] - 10), 0.01)
    C(T(246), 'set', room='bus', view='cab', set=dict(B9N, drive=0.0), rim=DASH9,
      ppl=[P('della', 'driver', kind='seat', expr='set_jaw', act=_A(drive, lambda a, s: a.look_at(T(246) + 0.6, (300, 700), dur=0.3)))],
      sfx=[(T(246) + 0.3, 'engine_start_bus', -2, 0, 'bus')], c=PU(0.015))
    # 247 "She shoves her phone at me."
    C(T(247), 'set', room='bus', view='seat1', set=dict(B9N, drive=0.0), rim=DASH9,
      ppl=[P('mina_bare', 'seat1', kind='seat', expr='fear', act=_A(lambda a, s: a.look_at(-9, scr(s.sp, 'driver', dy=-180), dur=0.3),
                                                                   lambda a, s: a.reach_to(T(247) + 0.6, 1, scr(s.sp, 'driver', dx=220, dy=-190), dur=0.35, contact='grip', shape='grip', z=60.0))),
           P('della', 'driver', kind='seat', expr='set_jaw',
             act=_A(lambda a, s: a.hold_prop('cell', -1, T(247), T(247) + 0.9),
                    lambda a, s: a.reach_to(T(247) + 0.15, -1, toward(a, -1, scr(s.sp, 'seat1', dy=-300), T(247)), t1=T(247) + 0.9, dur=0.3, contact='grip', shape='grip', z=60.0),
                    lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'wheel', dx=60), dur=0.01, contact='grip', shape='grip', z=120.0)))],
      c=PU(0.015))
    # 248 "The bars are back."  249 D "Call 911. Then belt on. Seat one."
    C(T(248), 'ins', name='call911', kw=dict(), c=dict(mv='push', rate=0.025))
    bust(T(249), 'della', ('bus', 'cab'), dict(B9N, drive=6.0), 'grim_drive', DASH9, cx=960, cy=640, scale=0.85, turn=0.5,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 600), dur=0.2), lambda a, s: a.look_at(W(249, 'seat'), (1500, 700), dur=0.3)))
    # 250 "I tell them everything."  251 X "Officers are on the way."
    bust(T(250), 'mina_bare', ('bus', 'seat1'), dict(B9N, drive=10.0), 'resolve', DASH9, cx=960, cy=640, scale=0.85, turn=-0.2,
         act=_A(lambda a, s: a.phone_to_ear(-9, None, 1), lambda a, s: a.hold_prop('cell', 1, -9, None), lambda a, s: a.look_at(s.t0, (300, 500), dur=0.3),
                pose(T(250) + 0.3, None, 0.3, h_nod=0.08), pose(T(250) + 0.9, None, 0.3, h_nod=0.0)))
    C(T(251), 'ins', name='call911', kw=dict(talk=1.0), c=dict(mv='push', rate=0.02))
    # 252 "Grandma hits the gas."  253 D "So are we."
    C(T(252), 'set', room='bus', view='cab', set=dict(B9N, drive=16.0), rim=DASH9,
      ppl=[P('della', 'driver', kind='seat', expr='set_jaw', act=_A(drive, pose(T(252) + 0.2, None, 0.3, lean=0.12)))],
      sfx=[(T(252) + 0.2, 'engine_rev_bus', 0, 0, 'bus')], c=PU(0.02, hit=[(T(252) + 0.25, 4.0)]))
    bust(T(253), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'set_jaw', DASH9, cx=960, cy=640, scale=0.88, turn=0.45,
         act=lambda a, s: a.look_at(s.t0, (250, 620), dur=0.2))
    # 254 "Grandma, the kid in his back seat. Yellow raincoat. He rides OUR bus. Seat twenty-two."
    bust(T(254), 'mina_bare', ('bus', 'seat1'), dict(B9N, drive=16.0), 'terrified_call', DASH9, cx=980, cy=640, scale=0.85, turn=-0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (260, 560), dur=0.3), lambda a, s: a.hold_prop('cell', 1, -9, None)))
    C(W(254, 'he'), 'set', room='bus', view='seat1', set=dict(B9N, drive=16.0), rim=DASH9,
      ppl=[P('mina_bare', 'seat1', kind='seat', expr='terrified_call', act=_A(lambda a, s: a.look_at(-9, scr(s.sp, 'driver', dy=-200), dur=0.3), lambda a, s: a.hold_prop('cell', 1, -9, None))),
           P('della', 'driver', kind='seat', expr='grim_drive', act=_A(lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'wheel', dx=60), dur=0.01, contact='grip', shape='grip', z=120.0),
                                                                    lambda a, s: a.reach_to(-9, -1, scr(s.sp, 'wheel', dx=-60), dur=0.01, contact='grip', shape='grip', z=120.0)))],
      c=PU(0.012))
    # 255-256 D "Mina. Seat twenty-two has been empty for thirty-two years."  (the empty seat in her own bus)
    bust(T(255), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'calm_firm', DASH9, cx=960, cy=640, scale=0.88, turn=0.45,
         act=_A(lambda a, s: a.look_at(s.t0, (250, 620), dur=0.2), blinks(T(256) + 0.3)))
    C(W(256, 'empty'), 'set', room='bus', view='seat22', set=dict(B9N, drive=16.0), rim=DASH9, tags=[tagc(WD(256, 'thirty'), 'EMPTY: 32 YEARS', 'pill', 960, 170, 1.6)],
      c=PU(0.03))
    # 257 "Nineteen ninety-four."  (the tape)  258 "My sixth day."  259 "He took three kids off my route."
    C(T(257), 'flat', set=lambda: ST.bu_tape94('title', track=0.6), era='1994', cut='vhs', sfx=[(T(257), 'vhs_noise', -10, 0, 'vhs', dict(dur=1.4))], c=dict(mv='push', rate=0.02))
    bust(T(258), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'grim_drive', DASH9, cx=900, cy=640, scale=0.9, turn=0.5,
         act=_A(lambda a, s: a.look_at(s.t0, (250, 640), dur=0.2), pose(T(258) + 0.1, None, 0.4, h_tilt=-5.0)))
    C(W(259, 'three'), 'flat', set=lambda: ST.bu_tape94('kids', track=0.5), era='1994', cut='vhs', sfx=[(W(259, 'three'), 'tape_skip', -6, 0, None)], c=dict(mv='push', rate=0.03))
    # 260 "At his last stop, if you call a child's name before the three o'clock bell, and they answer you, he has to let them go."
    bust(T(260), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'calm_firm', DASH9, cx=960, cy=640, scale=0.88, turn=0.45,
         act=_A(lambda a, s: a.look_at(s.t0, (250, 640), dur=0.2), lambda a, s: a.look_at(W(260, 'name'), (1500, 680), dur=0.35)),
         tags=[tagc(WD(260, 'call'), "CALL THEIR NAME BEFORE THE BELL", 'pill', 960, 170, 2.6)])
    C(W(260, 'three'), 'ins', name='clock', kw=dict(time=(2, 59, 50)), c=dict(mv='push', rate=0.04), sfx=[(W(260, 'three') + 0.1, 'clock_tick', -8, 0, 'close')])
    bust(W(260, 'answer'), 'mina_bare', ('bus', 'seat1'), dict(B9N, drive=16.0), 'fear', DASH9, cx=980, cy=640, scale=0.85, turn=-0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (260, 580), dur=0.3), lambda a, s: a.hold_prop('cell', 1, -9, None), blinks(W(260, 'let'))))
    # 261 "If they answer him... they stay."  262 "I got two back."
    bust(T(261), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'set_jaw', DASH9, cx=960, cy=640, scale=0.95, turn=0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (250, 640), dur=0.2)), z=0.02)
    bust(T(262), 'della', ('bus', 'cab'), dict(B9N, drive=16.0), 'tender', DASH9, cx=960, cy=640, scale=0.9, turn=0.45,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 700), dur=0.4), blinks(T(262) + 0.4)))
    # 263 "The dash radio crackles."  264 "Then, in Grandma's own voice:"  265 W "The third was a boy in the back."
    RAD = dict(B9N, drive=16.0)
    C(T(263), 'set', room='bus', view='cab', set=RAD, rim=DASH9, ppl=[P('della', 'driver', kind='seat', expr='grim_drive', act=drive)], sfx=[(T(263) + 0.15, 'radio_crackle', -2, 0, 'bus', dict(dur=1.4))],
      post_fn=lambda tt: dict(glitch=0.12 if (tt * 9.0) % 1.0 < 0.25 else 0.0), c=PU(0.03))
    bust(T(264), 'mina_bare', ('bus', 'seat1'), RAD, 'fear', DASH9, cx=980, cy=640, scale=0.85, turn=-0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 800), dur=0.25), lambda a, s: a.hold_prop('cell', 1, -9, None)))
    bust(T(265), 'mina_bare', ('bus', 'seat1'), RAD, 'terrified_call', dict(AMBER, rim_a=90), cx=960, cy=640, scale=0.92, turn=-0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 820), dur=0.2), lambda a, s: a.hold_prop('cell', 1, -9, None)), sfx=[(T(265), 'radio_crackle', -6, 0, 'bus', dict(dur=2.0))],
         post_fn=lambda tt: dict(glitch=0.2 if (tt * 7.0) % 1.0 < 0.18 else 0.03), z=0.02)
    # 266 "She doesn't look at it."  267-271 D "I didn't know his name yet... You thought that was manners?"
    bust(T(266), 'della', ('bus', 'cab'), RAD, 'grim_drive', DASH9, cx=960, cy=640, scale=0.9, turn=0.5, act=lambda a, s: a.look_at(s.t0, (250, 600), dur=0.2))
    C(T(268), 'set', room='bus', view='seat1', set=RAD, rim=DASH9,
      ppl=[P('mina_bare', 'seat1', kind='seat', expr='guilt', act=_A(lambda a, s: a.look_at(-9, scr(s.sp, 'driver', dy=-200), dur=0.3), lambda a, s: a.hold_prop('cell', 1, -9, None))),
           P('della', 'driver', kind='seat', expr='grim_drive', act=_A(lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'wheel', dx=60), dur=0.01, contact='grip', shape='grip', z=120.0),
                                                                    lambda a, s: a.reach_to(-9, -1, scr(s.sp, 'wheel', dx=-60), dur=0.01, contact='grip', shape='grip', z=120.0)))],
      c=PU(0.012))
    bust(T(270), 'della', ('bus', 'cab'), RAD, 'tender', DASH9, cx=960, cy=640, scale=0.9, turn=0.45, act=_A(lambda a, s: a.look_at(s.t0, (300, 620), dur=0.3)))
    bust(T(271), 'della', ('bus', 'cab'), RAD, 'calm_firm', DASH9, cx=960, cy=640, scale=0.95, turn=0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 680), dur=0.3), lambda a, s: a.head_tilt(T(271) + 0.4, 8.0, 0.8)))
    # 272-273 "Up ahead: his bus." "Dark."
    C(T(272), 'set', room='bus', view='windshield', set=dict(B9N, drive=16.0, his_ahead=(0.0, -26.0)), rim=DASH9, c=PU(0.03))
    C(T(273), 'set', room='road', view='ahead', set=dict(his_win=0.0, speed=16.0), rim=NIGHT, c=PU(0.02))
    # 274-276 "His head comes out of the driver's window, and turns." "Backwards." "Grinning at us."  (the head ratchets round
    # in three ticks to face us while the body drives on; each tick a tape-skip closer)
    RW = dict(his_win=0.0, speed=16.0)
    ticks = [WD(274, 'turns') + 0.12 * k for k in range(3)]
    wbust(T(274), ('road', 'window'), RW, cx=1150, cy=860, scale=0.7, light=dict(NIGHT, dark=0.3),
          act=_A(pose(-9, None, 0.1, h_turn=-0.9, h_tilt=-6.0), pose(ticks[0], None, 0.05, h_turn=-0.55), pose(ticks[1], None, 0.05, h_turn=-0.25),
                 pose(ticks[2], None, 0.05, h_turn=0.0, h_tilt=14.0)),
          sfx=[(tk, 'neck_ratchet', -2, 0, 'car') for tk in ticks], z=0.015)
    wbust(T(275), ('road', 'window'), RW, cx=980, cy=880, scale=1.0, light=dict(NIGHT, dark=0.25), cut='vhs',
          act=_A(pose(-9, None, 0.1, h_tilt=18.0), lambda a, s: a.head_tilt(T(275) + 0.1, 10.0, 0.4)), sfx=[(T(275), 'tape_skip', -2, 0, None)], z=0.02)
    wbust(T(276), ('road', 'window'), RW, cx=960, cy=900, scale=1.35, light=dict(NIGHT, dark=0.2), cut='vhs',
          act=_A(pose(-9, None, 0.1, h_tilt=-8.0), lambda a, s: a.head_tilt(T(276) + 0.1, 14.0, 0.4)),
          hit=[T(276) + 0.05], sfx=[(T(276), 'tape_skip', 0, 0, None)], z=0.03)
    # 277 "His brake lights flash."  278 "Grandma swerves."
    br = lambda tt: 1.0 if tt >= WD(277, 'brake') else 0.0
    C(T(277), 'set', room='road', view='ahead', set=dict(his_win=0.0, speed=16.0, brake=br), rim=NIGHT, hit=[WD(277, 'brake')],
      sfx=[(WD(277, 'brake'), 'brake_hiss', -2, 0, 'outside')], c=PU(0.04, 1.2))
    C(T(278), 'set', room='bus', view='cab', set=dict(B9N, drive=16.0), rim=DASH9,
      ppl=[P('della', 'driver', kind='seat', expr='shout',
             act=_A(lambda a, s: a.reach_to(-9, 1, scr(s.sp, 'wheel', dx=70, dy=-10), dur=0.01, contact='grip', shape='grip', z=120.0),
                    lambda a, s: a.reach_to(-9, -1, scr(s.sp, 'wheel', dx=-70, dy=-10), dur=0.01, contact='grip', shape='grip', z=120.0),
                    pose(WD(278, 'swerves'), None, 0.15, lean=-0.2, h_tilt=-12.0)))],
      sfx=[(WD(278, 'swerves'), 'tyre_screech', 0, 0, 'outside')],
      c=dict(mv='keys', free=True, keys=[(T(278), 960, 540, 1.0, None, 1.0), (WD(278, 'swerves') + 0.3, 900, 560, 1.0, 'push', 1.08)], hit=[(WD(278, 'swerves'), 7.0)]))
    # 279 "His bumper rips our side mirror off."  he drops back alongside (brake lights), the bumper swings in | the hit in the cab
    hp = lambda tt: (lerp(0.0, -2.6, ease_in_out(clamp((tt - T(279)) / 1.1))), lerp(-14.0, -4.5, ease_in_out(clamp((tt - T(279)) / 1.1))))
    C(T(279), 'set', room='road', view='ahead', set=dict(his_pos=hp, his_win=0.0, speed=16.0, brake=1.0), rim=NIGHT, c=PU(0.03, 1.1))
    C(W(279, 'mirror'), 'set', room='bus', view='cab', set=dict(B9N, drive=16.0), rim=DASH9, cut='white', quiet_cut=True,
      ppl=[P('della', 'driver', kind='seat', expr='shout', act=_A(drive, pose(-9, None, 0.1, lean=-0.15, h_tilt=-10.0)))],
      sfx=[(W(279, 'mirror') + 0.02, 'metal_rip', 2, 0.6, 'outside')], post_fn=lambda tt: dict(glitch=max(0.0, 0.3 - (tt - W(279, 'mirror')))),
      c=PU(0.02, 1.08, hit=[(W(279, 'mirror') + 0.02, 9.0)]))
    # 280 "The road ahead is empty."  281-283 "And the other mirror is full of amber." "His windows, glowing." "He's behind us."
    C(T(280), 'set', room='bus', view='windshield', set=dict(B9N, drive=16.0), rim=DASH9, c=PU(0.02))
    C(T(281), 'set', room='road', view='behind', set=dict(his_win=1.0, mirror_r=False, speed=16.0), rim=AMBER, sfx=[(T(281) + 0.1, 'sting_low', -6, 0, None)], c=PU(0.03))
    C(T(282), 'set', room='road', view='behind', set=dict(his_win=1.0, mirror_r=False, speed=16.0), rim=AMBER, c=PU(0.05, 1.5, x=930, y=530))
    bust(T(283), 'mina_bare', ('bus', 'seat1'), RAD, 'terrified_call', AMBER, cx=960, cy=640, scale=0.9, turn=0.6,
         act=_A(lambda a, s: a.look_at(s.t0, (1700, 500), dur=0.15, body=0.5)), z=0.02)
    # 284 "Fweet-fweet."
    wbust(T(284), ('road', 'behind'), dict(his_win=1.0, mirror_r=False, speed=16.0), cx=960, cy=840, scale=1.0, act=lambda a, s: a.blow_whistle(T(284) + 0.05, 'two', -1), z=0.03)
    # 285 "Two forty-one."
    C(T(285), 'set', room='road', view='behind', set=dict(his_win=1.0, mirror_r=False, speed=16.0), rim=AMBER,
      tags=[tagc(WD(285, 'two'), '2:41 AM', 'alert', 960, 170, 1.2)], c=PU(0.03, 1.2, x=930, y=530))


# ==================================================================================================== RULE 7: THE LAST STOP (286-369)
def plan_rule7(F):
    t, e, C = F.t, F.e, F.cut
    C(T(286), 'rule', n=7)
    # 290-293 "Two fifty-seven." "Larkfield Elementary." "Dark windows." "A flag rope, clinking."
    C(T(290), 'set', room='school', view='wide', set=dict(SCH0), rim=NIGHT,
      tags=[tagc(WD(290, 'two'), '2:57 AM', 'alert', 960, 170, 1.0), tagc(WD(291, 'larkfield'), 'LARKFIELD ELEMENTARY', 'pill', 960, 170, 1.6)], c=PU(0.015))
    C(T(292), 'set', room='school', view='clock', set=dict(SCH0), rim=NIGHT, c=PU(0.03))
    C(T(293), 'set', room='school', view='flag', set=dict(SCH0, wind=1.3), rim=NIGHT, sfx=[(T(293) + 0.1, 'flag_rope_clink', -4, 0, 'outside', dict(dur=1.6))], c=PU(0.02))
    # 294-296 "His bus is already parked at the doors." "Cobwebs in the wipers." "Like it's been waiting since 1994."
    C(T(294), 'set', room='school', view='doors', set=dict(SCH0), rim=AMBER, c=PU(0.015))
    C(T(295), 'set', room='school', view='doors', set=dict(SCH0), rim=AMBER, c=PU(0.03, 2.0, x=1010, y=560))
    C(T(296), 'set', room='school', view='doors', set=dict(SCH0), rim=AMBER, post_fn=lambda tt: dict(glitch=0.25 if abs(tt - WD(296, '1994')) < 0.12 else 0.0),
      tags=[tagc(WD(296, '1994'), '1994', 'red', 960, 170, 1.2)], c=PU(0.02, 1.4, x=980, y=580))
    # 297-298 "Doors open." "Amber light."
    op = lambda tt: ease_in_out(clamp((tt - WD(297, 'doors')) / 0.7))
    C(T(297), 'set', room='school', view='doors', set=dict(SCH0, his_door=op), rim=AMBER, sfx=[(WD(297, 'doors'), 'bus_door_fold', -2, 0, 'outside')], c=PU(0.03, 1.4, x=930, y=600))
    # 299 "He's at the top of the steps, with his clipboard."  (her eyes, from the bottom step) he skips in from the aisle
    SO = dict(kind='his', door=1.0)
    C(T(298), 'set', room='school', view='doors', set=dict(SCH0, his_door=1.0), rim=AMBER, cut='vhs',
      ppl=[ws('his_top', face='bottom_step', act=_A(lambda a, s: a.clipboard(W(299, 'clipboard') - 0.4, 1), lambda a, s: a.head_tilt(T(299) + 0.2, 14.0, 0.6),
                                                   wlook(T(298) + 0.3, (900, 760))))],
      sfx=[(T(298), 'amber_hum', -10, 0, 'bus', dict(dur=3.0)), (T(298), 'tape_skip', -4, 0, None)], c=PU(0.02, 2.7, x=958, y=590))
    # 300 W "Last stop! Everybody counted?"
    wbust(T(300), ('bus', 'step_out'), SO, cx=960, cy=860, scale=0.95,
          act=_A(lambda a, s: a.clipboard(-9, 1), pose(T(300) + 0.1, None, 1.0, ws_bend=0.35), lambda a, s: a.head_tilt(W(300, 'everybody'), 16.0, 0.6)), z=0.025)
    # 301 "I stop at the bottom step."
    SD = dict(clock=(2, 57), his_door=1.0, heads9=1.0)
    C(T(301), 'set', room='school', view='doors', set=SD, rim=HEADS9,
      ppl=[P('mina_bare', (-2.01, -5.35), path=[(T(301), (-2.0, -6.4)), (T(301) + 1.0, 'bottom_step')], face='his_top', expr='resolve'),
           ws('his_top', face='bottom_step', act=_A(lambda a, s: a.clipboard(-9, 1), pose(-9, None, 0.1, ws_bend=0.3), lambda a, s: a.head_tilt(T(301) + 0.8, 10.0, 0.6)))],
      c=PU(0.02, 1.7, x=930, y=630))
    # 302 "SAMI!"  (Mina, lip sync)
    bust(T(302), 'mina_bare', ('school', 'reverse'), SD, 'terrified_call', HEADS9, cx=960, cy=650, scale=0.9, turn=-0.1, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.15),
         hit=[T(302) + 0.05])
    # 303 "From inside, right behind him, my own voice:"  the fake me far down the aisle; Sami in seat 4
    C(T(303), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={4: 1.0, 22: 0.8}), rim=AMBER,
      ppl=[P('sami', 'seat4', kind='seat', expr='dazed', act=lambda a, s: a.look_at(T(303) + 0.3, scr(s.sp, 'aisle5', dy=-150), dur=0.4)),
           P('mina_bare', (0.18, 6.6), face='top_step', expr='tender', light=FAKE, id='fake', act=lambda a, s: a.look_at(-9, scr(s.sp, 'seat4', dy=-120), dur=0.3)),
           ws((-0.2, 3.4), face='top_step', act=_A(lambda a, s: a.clipboard(-9, 1), lambda a, s: a.head_tilt(T(303) + 0.5, -14.0, 0.6)))],
      post_fn=lambda tt: dict(glitch=0.08 if (tt * 5.0) % 1.0 < 0.15 else 0.0), c=PU(0.02))
    # 304 W "Sami! Back here!"  the fake me (no lips: it's his voice)
    bust(T(304), 'mina_bare', ('bus', 'aisle'), HIS, 'tender', FAKE, cx=960, cy=640, scale=0.85, turn=0.1, act=_A(lambda a, s: a.look_at(s.t0, (1500, 700), dur=0.2), lambda a, s: a.head_tilt(T(304) + 0.2, 14.0, 0.6)),
         post_fn=lambda tt: dict(glitch=0.18 if (tt * 6.0) % 1.0 < 0.2 else 0.04), cut='vhs')
    # 305 "Two of me."  (the real one, white headlights)
    bust(T(305), 'mina_bare', ('school', 'reverse'), SD, 'fear', HEADS9, cx=960, cy=650, scale=0.95, turn=-0.1, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.15))
    # 306 "Sami turns toward the fake me."
    C(T(306), 'set', room='bus', view='seat4', set=dict(HIS, seat_lit={4: 1.0, 22: 0.8}), rim=AMBER,
      ppl=[P('sami', 'seat4', kind='seat', expr='dazed', act=lambda a, s: a.look_at(T(306) + 0.3, (-500, 700), dur=0.7, body=0.6))], c=PU(0.015))
    # 307 "My foot lifts onto the first step."  (from inside, down the steps: her foot on the first step)
    C(T(307), 'set', room='school', view='doors', set=SD, rim=HEADS9, c=PU(0.02, 3.0, x=905, y=640),
      ppl=[P('mina_bare', 'bottom_step', face='his_top', expr='tempted', act=lambda a, s: a.step_up(T(307) + 0.3, 1, up=0.9, hold=3.0, back=0.5))],
      sfx=[(T(307) + 1.1, 'step_touch', -4, 0, 'bus')])
    # 308 "Not even for Sami."  (rule 7, a white flash)
    C(T(308), 'ins', name='rules', kw=dict(show=7, hl=7), cut='white', sfx=[(T(308), 'sting_rule', -2, 0, None)], c=dict(mv='push', rate=0.03))
    # 309 "I pull it back... and SCREAM his name."
    C(T(309), 'set', room='school', view='doors', set=SD, rim=HEADS9, c=PU(0.02, 3.0, x=905, y=640),
      ppl=[P('mina_bare', 'bottom_step', face='his_top', expr='resolve', act=lambda a, s: a.step_up(T(309) - 1.5, 1, up=0.9, hold=1.6, back=0.5))],
      sfx=[(T(309) + 0.2, 'step_off', -4, 0, 'bus')])
    bust(W(309, 'scream'), 'mina_bare', ('school', 'reverse'), SD, 'terrified_call', HEADS9, cx=960, cy=650, scale=1.0, turn=-0.1,
         act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1), c=BZ(0.03, hit=[(WD(309, 'scream'), 5.0)]))
    # 310-311 "Sami looks down the step." "At a face he knows."  312 S "HERE!"
    bust(T(310), 'sami', ('bus', 'aisle'), HIS, 'dazed', AMBER, cx=960, cy=660, scale=0.85, turn=0.25,
         act=_A(lambda a, s: a.look_at(s.t0, (1300, 1000), dur=0.4), ex('proud_grin', T(311) + 0.3, None, 0.4), blinks(T(311))))
    bust(T(312), 'sami', ('bus', 'aisle'), HIS, 'shout_here', AMBER, cx=960, cy=660, scale=0.95, turn=0.2, act=lambda a, s: a.look_at(s.t0, (1300, 1000), dur=0.1),
         hit=[WD(312, 'here')], c=BZ(0.03, hit=[(WD(312, 'here'), 4.0)]))
    # 313-314 "He scrambles for the door." "A glove snaps shut on his pajamas."
    tail_pt = lambda s: (lambda tt: (s.A['sami'].where(tt, 'hip', post=False)[0] + 0.25 * s.A['sami'].height,
                                     s.A['sami'].where(tt, 'hip', post=False)[1] + 0.12 * s.A['sami'].height))
    C(T(313), 'set', room='bus', view='aisle', set=dict(HIS, door=1.0), rim=AMBER,
      ppl=[P('sami', (0.0, 4.6), path=[(T(313), (0.0, 4.6)), (WD(314, 'snaps') + 0.1, (0.0, 3.0))], run=True, surface='inside', expr='shout_here'),
           ws('aisle5', face='top_step', act=_A(lambda a, s: a.snap_glove(WD(314, 'snaps'), -1, tail_pt(s), t1=WD(314, 'snaps') + 0.5),
                                                          lambda a, s: a.ws_hold(WD(314, 'snaps') + 0.5, -1, 'tail_piece', None, 'snap'),
                                                          lambda a, s: a.look_at(T(313), (s.A['sami'], 'eyes'), dur=0.05, snap=True)))],
      c=PU(0.02))
    # 315 "Rip."
    C(T(315), 'ins', name='tail', kw=dict(), hit=[T(315) + 0.02], sfx=[(T(315), 'fabric_rip', 2, 0, 'close')], c=dict(mv='push', rate=0.05, hit=[(T(315) + 0.02, 5.0)]))
    # 316 "He tumbles into my arms, half his dinosaur tail gone."
    C(T(316), 'set', room='school', view='doors', set=SD, rim=HEADS9,
      ppl=[P('sami_torn', 'his_step', path=[(T(316), 'his_step'), (T(316) + 0.55, (-2.0, -5.15))], run=True, surface='asphalt', expr='cry'),
           P('mina_bare', (-2.0, -5.5), face='his_step', expr='terrified_call',
             act=_A(lambda a, s: a.crouch(T(316) + 0.2, 0.6, None, 0.4),
                    lambda a, s: a.reach_to(T(316) + 0.45, 1, (s.A['sami_torn'], 'chest'), dur=0.3, contact='palm', shape='open', z=60.0),
                    lambda a, s: a.reach_to(T(316) + 0.5, -1, (s.A['sami_torn'], 'belly'), dur=0.3, contact='palm', shape='open', z=70.0),
                    ex('relief', T(316) + 1.4, None, 0.5))),
           ws('his_top', face='bottom_step', act=_A(lambda a, s: a.ws_hold(-9, -1, 'tail_piece', None, 'snap'), lambda a, s: a.head_tilt(T(316) + 0.6, 18.0, 0.8)))],
      sfx=[(T(316) + 0.55, 'body_catch', -2, 0, 'outside')], c=PU(0.02, 2.8, x=920, y=640))
    # 317 "Two fifty-eight."
    C(T(317), 'ins', name='clock', kw=dict(time=(2, 58)), sfx=[(T(317) + 0.1, 'clock_tick', -6, 0, 'close')], c=dict(mv='push', rate=0.04))
    # 318-319 "At the back, seat twenty-two glows." "The boy in the yellow raincoat."
    glow22 = lambda tt: 0.3 + 0.7 * ease_in_out(clamp((tt - T(318)) / 1.0))
    C(T(318), 'set', room='bus', view='seat22', set=dict(HIS, seat_lit={22: glow22}), rim=AMBER,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', alpha=0.7, act=blinks(T(318) + 1.2))], c=PU(0.02))
    bust(T(319), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'lonely', AMBER, cx=960, cy=640, scale=0.85, turn=0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 560), dur=0.4), blinks(T(319) + 0.9)))
    # 320 "One impossibly long arm reaches down the aisle, and a glove settles on his shoulder."
    C(T(320), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={22: 1.0}), rim=AMBER,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', alpha=0.7),
           ws('aisle2', face='seat22', act=_A(lambda a, s: a.set(-1.0, None, 0.01, ws_bend=0.1),
                                              lambda a, s: a.reach_far(T(320) + 0.3, 1, lambda tt: s.A['theo'].where(tt, 'shoulder_r', post=False), t1=None,
                                                                       dur=max(1.6, W(320, 'glove') - T(320) - 0.2), z=-40.0, shape='hang', ease=ease_in_out)))],
      sfx=[(T(320) + 0.3, 'arm_stretch_creak', -4, 0, 'bus', dict(dur=2.0))], c=PU(0.02))
    # 321-322 W "Nobody knows his name," he says.  323 W "Not his mother. Not Della. Not you. Every morning ... nobody asks."
    wbust(T(321), ('bus', 'aisle'), HIS, cx=900, cy=860, scale=0.9, act=_A(pose(-9, None, 0.1, h_tilt=-12.0), lambda a, s: a.head_tilt(T(321) + 0.3, 18.0, 1.0)))
    SH = (1210, 760)

    def theo_glove(t_on, press=(0.0, 0.0), dur=0.5):
        return lambda A, sh, sp: [glove_on(SH[0], SH[1], 4.4, press[0], press[1], t_on, t_on + dur, curl=0.45)]
    bust(W(323, 'every'), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'lonely', AMBER, cx=960, cy=620, scale=0.8, turn=0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 700), dur=0.4), blinks(W(323, 'every') + 1.2)), acts=theo_glove(-9))
    bust(W(323, 'one'), 'mina_bare', ('school', 'reverse'), SD, 'fear', HEADS9, cx=960, cy=650, scale=0.9, turn=-0.1, act=_A(lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.2), blinks(W(323, 'chance'))))
    wbust(W(323, 'and'), ('bus', 'step_out'), SO, cx=960, cy=880, scale=1.15, cut='vhs', act=_A(pose(-9, None, 0.1, ws_bend=0.45), lambda a, s: a.head_tilt(W(323, 'nobody') - 0.2, -16.0, 0.5)),
          sfx=[(W(323, 'and'), 'tape_skip', -2, 0, None)])
    # 324 "He bends down, and down, until the grin is a foot from my face."  (her eyes: he leans out of the door at the lens)
    C(T(324), 'set', room='bus', view='step_out', set=SO, rim=AMBER,
      ppl=[ws('top_step', face='bottom_step', act=_A(lambda a, s: a.clipboard(-9, 1), lambda a, s: a.lean_to(T(324) + 0.2, (900, 1180), gap=30.0, dur=2.8, beats=2),
                                                      wlook(T(324), (900, 1300), snap=False, dur=0.6)))],
      sfx=[(T(324) + 0.2, 'joint_creak', -6, 0, 'bus', dict(dur=2.6))], c=PU(0.02))
    # 325 "Soft."  326 "Kind."
    wbust(T(325), ('school', 'doors'), SD, cx=960, cy=960, scale=1.45, light=dict(AMBER, under='#ffb040', under_a=80), act=_A(pose(-9, None, 0.1, h_tilt=14.0), lambda a, s: a.head_tilt(T(325) + 0.1, 22.0, 1.2)), z=0.01)
    bust(T(326), 'mina_bare', ('school', 'reverse'), SD, 'tempted', HEADS9, cx=700, cy=650, scale=0.9, turn=0.3, act=_A(lambda a, s: a.look_at(s.t0, (1500, 520), dur=0.3), blinks(T(326) + 0.3)),
         busts=[dict(who='whistle', cx=1500, cy=820, scale=1.1, turn=-0.4, light=AMBER, depth=0.97, act=lambda a, s: a.head_tilt(T(326), 20.0, 0.8))])
    # 327 W "Trade seats with him, Mina. He goes home to his mother tonight. You'd do that for a friend. Hurry. Just you. Our secret."
    wbust(T(327), ('school', 'doors'), SD, cx=1000, cy=900, scale=1.25, act=_A(pose(-9, None, 0.1, h_tilt=18.0), lambda a, s: a.head_tilt(W(327, 'mina') - 0.1, -10.0, 0.8)))
    bust(W(327, 'he'), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'lonely', AMBER, cx=960, cy=620, scale=0.8, turn=0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 600), dur=0.4)), acts=theo_glove(-9))
    bust(W(327, 'you'), 'mina_bare', ('school', 'reverse'), SD, 'tempted', HEADS9, cx=960, cy=650, scale=0.95, turn=-0.1, act=_A(lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.3), pose(W(327, 'friend'), None, 0.6, lean=0.06)))
    wbust(W(327, 'hurry'), ('school', 'doors'), SD, cx=960, cy=980, scale=1.6, cut='vhs', light=dict(AMBER, under='#ffb040', under_a=90),
          act=_A(pose(-9, None, 0.1, h_tilt=20.0), lambda a, s: a.head_tilt(W(327, 'secret') - 0.1, -8.0, 0.4)), sfx=[(W(327, 'hurry'), 'tape_skip', -4, 0, None)],
          tags=[tagc(WD(327, 'hurry'), 'HURRY', 'red', 960, 170, 0.8), tagc(WD(327, 'just'), 'JUST YOU', 'red', 960, 170, 0.8), tagc(WD(327, 'our'), 'OUR SECRET', 'red', 960, 170, 1.0)])
    # 328 "For one second... I want to."  (her foot creeps toward the step)
    bust(T(328), 'mina_bare', ('school', 'reverse'), SD, 'tempted', HEADS9, cx=960, cy=650, scale=1.0, turn=-0.1,
         act=_A(lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.3), pose(W(328, 'want'), None, 0.6, lean=0.1), blinks(T(328) + 0.4)), z=0.025)
    # 329 "Behind me, Grandma."  330 "The real one."  331 D "Mina. Step back. Stay where I can see you."
    C(T(329), 'set', room='school', view='doors', set=SD, rim=HEADS9,
      ppl=[P('della', 'behind_mina', path=[(T(329), (-0.6, -7.8)), (T(329) + 1.1, (-1.45, -6.0))], surface='asphalt', expr='calm_firm', face='bottom_step'),
           P('mina_bare', 'bottom_step', face='his_top', expr='tempted', act=lambda a, s: a.look_at(T(329) + 0.7, scr(s.sp, 'behind_mina', dy=-160), dur=0.4, body=0.3)),
           P('sami_torn', (-2.6, -5.9), face='his_top', expr='cry'),
           ws('his_top', face='bottom_step', act=_A(pose(-9, None, 0.1, ws_bend=0.75), lambda a, s: a.look_at(T(329) + 0.6, scr(s.sp, 'behind_mina', dy=-160), dur=0.08, snap=True)))],
      c=PU(0.02, 1.7, x=900, y=620))
    bust(T(330), 'della', ('school', 'reverse'), SD, 'calm_firm', HEADS9_L, cx=960, cy=640, scale=0.85, turn=-0.25, act=_A(lambda a, s: a.look_at(s.t0, (1500, 620), dur=0.3)))
    bust(T(331), 'della', ('school', 'reverse'), SD, 'calm_firm', HEADS9_L, cx=960, cy=640, scale=0.92, turn=-0.25,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 640), dur=0.3), lambda a, s: a.head_tilt(W(331, 'stay'), -6.0, 0.6)), z=0.015)
    # 332 "Hurry. Just you. Our secret."  333 "Nobody who loves you says those words."  (the type beat over her face)
    bust(T(332), 'mina_bare', ('school', 'reverse'), SD, 'resolve', HEADS9, cx=960, cy=680, scale=0.9, turn=-0.1,
         act=_A(lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.3), blinks(T(333) + 0.2)),
         tags=[tagc(WD(332, 'hurry'), 'HURRY.', 'red', 600, 170, 2.6), tagc(WD(332, 'just'), 'JUST YOU.', 'red', 960, 170, 2.0), tagc(WD(332, 'our'), 'OUR SECRET.', 'red', 1340, 170, 1.6),
               tagc(WD(333, 'nobody'), 'NOBODY WHO LOVES YOU SAYS THOSE WORDS', 'pill', 960, 250, 2.2)])
    # 334 "I step back."
    C(T(334), 'set', room='school', view='doors', set=SD, rim=HEADS9,
      ppl=[P('della', (-1.45, -6.0), face='bottom_step', expr='calm_firm'),
           P('mina_bare', 'bottom_step', path=[(T(334), 'bottom_step'), (T(334) + 0.7, (-1.75, -5.65))], surface='asphalt', face='his_top', expr='resolve'),
           P('sami_torn', (-2.6, -5.9), face='his_top', expr='cry'),
           ws('his_top', face='bottom_step', act=_A(pose(-9, None, 0.1, ws_bend=0.75), lambda a, s: a.set(T(334) + 0.3, None, 0.5, ws_bend=0.35)))],
      c=PU(0.02, 1.7, x=900, y=620))
    # 335 W "Call him, then. Go on. You can't."  (his glove reaches for the lens)
    gl_reach = lambda A, sh, sp: [glove_on(1400, 900, 3.0, 0.0, 0.0, T(335), T(335) + 1.2, curl=0.2, down=False,
                                           drift=lambda tt: (-300 * ease_in_out(clamp((tt - T(335)) / 1.6)), -150 * ease_in_out(clamp((tt - T(335)) / 1.6))), name='reach')]
    wbust(T(335), ('bus', 'step_out'), SO, cx=960, cy=880, scale=1.1, act=_A(pose(-9, None, 0.1, ws_bend=0.4), lambda a, s: a.head_tilt(W(335, 'go'), 16.0, 0.5)), acts=gl_reach)
    # 336 "Two fifty-nine."
    C(T(336), 'ins', name='clock', kw=dict(time=(2, 59)), sfx=[(T(336) + 0.1, 'clock_tick', -6, 0, 'close')], c=dict(mv='push', rate=0.05))
    # 337 T "Hi, Mina." (memory: morning, seat 22)  338-340 "Every single morning." "He knew my name." "I never asked his."
    bust(T(337), 'theo', ('bus', 'seat22'), B9M, 'kind_smile', MORNING, era='morning', cx=900, cy=640, scale=0.8, turn=0.25,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 480), dur=0.3), lambda a, s: a.wave(s.t0 + 0.05, E(337) + 0.4, 1)), cut='white')
    bust(T(338), 'mina_bare', ('school', 'reverse'), SD, 'guilt', HEADS9, cx=960, cy=650, scale=0.9, turn=-0.1, act=_A(lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.3), blinks(T(339) + 0.2)))
    bust(T(340), 'mina_bare', ('school', 'reverse'), SD, 'guilt', HEADS9, cx=960, cy=650, scale=1.0, turn=-0.05,
         act=_A(lambda a, s: a.look_at(s.t0, (900, 800), dur=0.3), lambda a, s: a.look_at(E(340) - 0.3, (960, 330), dur=0.3), ex('resolve', E(340) - 0.2, None, 0.4)), z=0.02)
    # 341 "From the bottom step, I call up the aisle."  (her eyes: him in the door, Theo far back under the glove)
    C(T(341), 'set', room='bus', view='step_out', set=dict(SO, seat_lit={22: 1.0}), rim=AMBER,
      ppl=[P('theo', 'seat22', kind='seat', expr='lonely', alpha=0.75),
           ws('top_step', face='bottom_step', act=_A(pose(-9, None, 0.1, ws_bend=0.3),
                                                     lambda a, s: a.reach_far(-9, 1, lambda tt: s.A['theo'].where(tt, 'shoulder_r', post=False), dur=0.01, z=-40.0, shape='hang'),
                                                     lambda a, s: a.look_at(T(341) + 0.4, (900, 1200), dur=0.3)))],
      c=PU(0.02))
    # 342 "What's your name?"  (Mina, lip sync)
    bust(T(342), 'mina_bare', ('school', 'reverse'), SD, 'kind_ask', HEADS9, cx=960, cy=650, scale=0.95, turn=-0.1, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.3))
    # 343 "Fweet-fweet."
    wbust(T(343), ('bus', 'step_out'), SO, cx=960, cy=860, scale=1.0, act=lambda a, s: a.blow_whistle(T(343) + 0.02, 'two', -1), z=0.03)
    # 344 "The doors start folding shut."  345 "Grandma jams our porch broom between them."  346 "The handle bends."  (+ 353 cracks)
    cls = lambda tt: lerp(1.0, 0.45, ease_in_out(clamp((tt - T(344) - 0.1) / 1.6)))
    C(T(344), 'set', room='bus', view='doors', set=dict(HIS, door=cls), rim=AMBER, sfx=[(T(344) + 0.1, 'door_motor', -2, 0, 'bus', dict(dur=1.6))], c=PU(0.02))
    jam = lambda tt: 1.0 if tt >= WD(345, 'jams') + 0.25 else 0.0
    C(T(345), 'set', room='school', view='doors', set=dict(SD, his_door=0.45, broom9=jam), rim=HEADS9,
      ppl=[P('della', (-1.8, -5.15), face='his_step', expr='set_jaw',
             act=_A(lambda a, s: a.reach_to(T(345) + 0.1, 1, scr(s.sp, 'his_door', dy=-150), dur=0.4, contact='grip', shape='grip', z=40.0),
                    lambda a, s: a.reach_to(T(345) + 0.15, -1, scr(s.sp, 'his_door', dx=-40, dy=-110), dur=0.4, contact='grip', shape='grip', z=40.0),
                    pose(WD(345, 'jams'), None, 0.2, lean=0.15))),
           P('mina_bare', (-1.55, -5.75), face='his_step', expr='resolve'),
           P('sami_torn', (-2.6, -5.9), face='his_top', expr='cry')],
      sfx=[(WD(345, 'jams') + 0.25, 'broom_jam', 0, 0, 'outside')], c=PU(0.02, 2.0, x=930, y=630, hit=[(WD(345, 'jams') + 0.25, 4.0)]))
    bnd = lambda tt: 0.6 * ease_in_out(clamp((tt - T(346)) / 1.0))
    C(T(346), 'set', room='bus', view='doors', set=dict(HIS, door=0.42, broom=1.0, bend=bnd), rim=AMBER, sfx=[(T(346) + 0.1, 'wood_creak', -2, 0, 'bus', dict(dur=1.0))], c=PU(0.03, 1.2))
    # 347 "From inside, in MY voice:"  348 W "Don't answer her. She never talked to you before."
    C(T(347), 'set', room='bus', view='back', set=dict(HIS, door=0.42, broom=1.0, bend=0.6, seat_lit={22: 1.0}), rim=AMBER,
      ppl=[P('mina_bare', 'aisle8', face='aisle_back', expr='tender', light=FAKE, id='fake', act=lambda a, s: a.head_tilt(T(347) + 0.4, 14.0, 0.8)),
           ws('aisle2', face='aisle_back', act=_A(lambda a, s: a.reach_far(-9, 1, (-400, 900), dur=0.01, z=-40.0, shape='hang'), lambda a, s: a.head_tilt(T(347) + 0.2, -12.0, 0.7)))],
      post_fn=lambda tt: dict(glitch=0.06 if (tt * 5.0) % 1.0 < 0.15 else 0.0), c=PU(0.02))
    bust(T(348), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'lonely', AMBER, cx=820, cy=620, scale=0.8, turn=0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 520), dur=0.4), blinks(T(348) + 1.4)), acts=theo_glove(-9),
         busts=[dict(who='mina_bare', cx=1520, cy=600, scale=0.6, turn=-0.5, expr='tender', light=FAKE, act=lambda a, s: a.head_tilt(T(348) + 0.3, 16.0, 1.0))])
    # 349-351 "The glove squeezes his shoulder." "He looks at it." "Then at me."
    bust(T(349), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'lonely', AMBER, cx=900, cy=620, scale=0.92, turn=0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 640), dur=0.3), lambda a, s: a.look_at(T(350) + 0.05, (1200, 860), dur=0.4), lambda a, s: a.look_at(T(351) + 0.05, (300, 560), dur=0.4)),
         acts=lambda A, sh, sp: [glove_on(1290, 800, 4.8, 0.0, 1.0, T(349) + 0.2, T(349) + 1.0, curl=0.45)], sfx=[(T(349) + 0.3, 'glove_squeeze', -4, 0, 'close')])
    # 352 T "Nobody's asked me that in a really long time..."
    bust(T(352), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'kind_smile', AMBER, cx=900, cy=620, scale=0.88, turn=0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 560), dur=0.3), blinks(T(352) + 1.5)), acts=lambda A, sh, sp: [glove_on(1290, 800, 4.6, 1.0, 1.0, -9, 0.0, curl=0.45)])
    # 353 "The broom cracks."
    crk = lambda tt: 1.0 if tt >= WD(353, 'cracks') else 0.0
    C(T(353), 'set', room='bus', view='doors', set=dict(HIS, door=0.4, broom=1.0, bend=0.75, crack=crk), rim=AMBER,
      sfx=[(WD(353, 'cracks'), 'wood_crack', 2, 0, 'bus')], c=PU(0.03, 1.25, hit=[(WD(353, 'cracks'), 5.0)]))
    # 354 T "Theo."
    bust(T(354), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'brave', AMBER, cx=960, cy=620, scale=0.95, turn=0.2,
         act=_A(lambda a, s: a.look_at(s.t0, (300, 560), dur=0.2)), acts=lambda A, sh, sp: [glove_on(1330, 800, 4.6, 1.0, 1.0, -9, 0.0, curl=0.45)])
    # 355-356 "Grandma can't see him." "She calls anyway."  357 "All three of us:"  358 "THEO!"
    bust(T(355), 'della', ('school', 'reverse'), SD, 'calm_firm', HEADS9_L, cx=960, cy=640, scale=0.88, turn=-0.25,
         act=_A(lambda a, s: a.look_at(s.t0, (1300, 560), dur=0.3), lambda a, s: a.look_at(T(355) + 0.7, (1650, 640), dur=0.3), lambda a, s: a.look_at(T(356) + 0.2, (1500, 600), dur=0.3),
                pose(T(356) + 0.3, None, 0.4, breath=1.0)))
    C(T(357), 'set', room='school', view='doors', set=dict(SD, his_door=0.4, broom9=1.0, bend=0.75, crack=1.0), rim=HEADS9,
      ppl=[P('della', (-1.45, -5.9), face='his_step', expr='set_jaw'), P('mina_bare', (-1.85, -5.6), face='his_step', expr='resolve'),
           P('sami_torn', (-2.35, -5.75), face='his_step', expr='dazed', act=lambda a, s: a.look_at(T(357) + 0.3, scr(s.sp, 'his_top', dy=-60), dur=0.3))],
      c=PU(0.02, 2.0, x=910, y=640))
    bust(T(358), 'mina_bare', ('school', 'reverse'), SD, 'terrified_call', HEADS9, cx=960, cy=660, scale=0.75, turn=-0.1, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1),
         busts=[dict(who='della', cx=560, cy=600, scale=0.7, turn=0.25, expr='shout', light=HEADS9_L, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1)),
                dict(who='sami_torn', cx=1380, cy=760, scale=0.62, turn=-0.25, expr='shout_here', light=HEADS9, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1))],
         hit=[T(358) + 0.05], c=BZ(0.03, hit=[(T(358) + 0.05, 4.0)]))
    # 359 "The grin swings to the school clock."
    wbust(T(359), ('bus', 'step_out'), SO, cx=900, cy=860, scale=1.0, act=_A(pose(-9, None, 0.1, ws_bend=0.3), lambda a, s: a.look_at(T(359) + 0.3, (1700, 200), dur=0.06, snap=True)),
          sfx=[(T(359) + 0.3, 'neck_tick', -2, 0, 'bus')])
    C(W(359, 'clock'), 'set', room='school', view='clock', set=dict(SD, clock=(2, 59, 52), his_door=0.4, broom9=1.0, bend=0.75, crack=1.0), rim=NIGHT, sfx=[(W(359, 'clock') + 0.1, 'clock_tick', -4, 0, 'outside')], c=PU(0.05, 1.3))
    # 360 "He blows the whistle, long and loud, to drown us out."
    wbust(T(360), ('bus', 'step_out'), SO, cx=960, cy=860, scale=1.05, act=lambda a, s: a.blow_whistle(T(360) + 0.1, 'long', 1), z=0.03)
    bust(W(360, 'drown'), 'mina_bare', ('school', 'reverse'), SD, 'terrified_call', HEADS9, cx=760, cy=660, scale=0.8, turn=0.1,
         act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1),
         busts=[dict(who='della', cx=1300, cy=620, scale=0.75, turn=-0.3, expr='shout', light=HEADS9_L, act=lambda a, s: a.look_at(s.t0, (1020, 450), dur=0.1))])
    # 361 T "...HERE!"
    bust(T(361), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'shout_here', AMBER, cx=960, cy=620, scale=1.0, turn=0.15,
         act=lambda a, s: a.look_at(s.t0, (300, 560), dur=0.1), acts=lambda A, sh, sp: [glove_on(1340, 800, 4.6, 1.0, 0.6, -9, 0.0, curl=0.45)], hit=[WD(361, 'here')],
         c=BZ(0.03, hit=[(WD(361, 'here'), 5.0)]))
    # 362 "Theo twists out from under the glove, and through the gap."
    bust(T(362), 'theo', ('bus', 'seat22'), dict(HIS, seat_lit={22: 1.0}), 'brave', AMBER, cx=lambda tt: 960 - 500 * ease_in_cubic(clamp((tt - T(362) - 0.2) / 0.8)), cy=620, scale=0.95, turn=-0.4,
         act=lambda a, s: a.look_at(s.t0, (200, 600), dur=0.1),
         acts=lambda A, sh, sp: [glove_on(1340, 800, 4.6, 0.6, 1.4, T(362) + 0.2, T(362) + 0.6, curl=0.5)], sfx=[(T(362) + 0.25, 'glove_snap', -2, 0, 'close')])
    C(W(362, 'through'), 'set', room='school', view='doors', set=dict(SD, his_door=0.4, broom9=1.0, bend=0.75, crack=1.0), rim=HEADS9,
      ppl=[P('theo', 'his_step', path=[(W(362, 'through'), 'his_step'), (W(362, 'through') + 0.7, (-2.0, -5.3))], run=True, surface='asphalt', expr='brave', alpha=0.8),
           P('mina_bare', (-1.85, -5.75), face='his_step', expr='terrified_call'), P('della', (-1.4, -6.0), face='his_step', expr='set_jaw')],
      c=PU(0.03, 2.0, x=920, y=630))
    # 363 "The doors slam on an empty aisle."
    C(T(363), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={22: 0.0, 4: 0.0}), rim=AMBER, sfx=[(T(363) + 0.05, 'door_slam_bus', 2, 0, 'bus')],
      c=PU(0.02, hit=[(T(363) + 0.05, 6.0)]))
    # 364 "Three o'clock."  365 "The school bell rings."
    C(T(364), 'ins', name='clock', kw=dict(time=(3, 0)), sfx=[(T(364) + 0.05, 'clock_tick', -2, 0, 'close')], c=dict(mv='push', rate=0.05))
    C(T(365), 'set', room='school', view='wide', set=dict(SD, clock=(3, 0), his_door=0.4, broom9=1.0, bend=0.75, crack=1.0), rim=NIGHT, sfx=[(T(365) + 0.1, 'school_bell', 0, 0, 'outside', dict(dur=2.4))],
      c=PU(0.01, hit=[(T(365) + 0.1, 3.0)]))
    # 366 "His bus is empty."  (him alone in the aisle, head snapping round: nobody)
    C(T(366), 'set', room='bus', view='aisle', set=dict(HIS, seat_lit={22: 0.0, 4: 0.0}), rim=AMBER,
      ppl=[ws('aisle5', face='top_step', act=_A(lambda a, s: a.clipboard(-9, 1), lambda a, s: a.look_at(T(366) + 0.2, (300, 600), dur=0.06, snap=True),
                                                 lambda a, s: a.look_at(T(366) + 0.7, (1600, 600), dur=0.06, snap=True)))],
      c=PU(0.02))
    # 367-368 "And the grin doesn't fit his face." "It slips."
    wbust(T(367), ('bus', 'step_out'), SO, cx=960, cy=860, scale=1.1, act=_A(pose(T(367) + 0.3, None, 1.4, ws_slip=0.35)), z=0.02)
    wbust(T(368), ('bus', 'step_out'), SO, cx=960, cy=880, scale=1.3, act=_A(pose(-9, None, 0.1, ws_slip=0.35), pose(T(368) + 0.05, None, 0.35, ws_slip=1.0)), cut='vhs',
          sfx=[(T(368), 'tape_warble', 0, 0, None)], z=0.02)
    # 369 "Tracking lines tear through him, and the bus rewinds into the dark."
    C(T(369), 'set', room='school', view='doors', set=dict(SD, clock=(3, 0), his_door=0.4, broom9=1.0, bend=0.75, crack=1.0), rim=AMBER,
      ppl=[ws('his_top', face='bottom_step', act=_A(lambda a, s: a.clipboard(-9, 1), lambda a, s: a.defeat(T(369) + 0.05, 0.3, max(1.2, W(369, 'bus') - T(369)))))],
      c=PU(0.03, 1.6, x=950, y=560))
    C(W(369, 'rewinds'), 'set', room='school', view='wide', set=dict(SD, clock=(3, 0), his=False), rim=NIGHT, cut='vhs',
      post_fn=lambda tt: dict(glitch=max(0.0, 0.8 - 1.2 * (tt - W(369, 'rewinds'))), static=max(0.0, 0.4 - 0.8 * (tt - W(369, 'rewinds')))),
      sfx=[(W(369, 'rewinds'), 'tape_rewind', 0, 0, None)], c=PU(0.01))


# ==================================================================================================== AFTER: THEO HOME, THE CLIPBOARD, THE MORNING, THE STING, RULE 8 (370-400)
def plan_after(F):
    t, e, C = F.t, F.e, F.cut
    LOT = dict(clock=(3, 1), his=False, heads9=1.0, clipboard=True, tail=True, police=True)
    # 370 "His clipboard clatters onto the asphalt."
    C(T(370), 'set', room='school', view='lot', set=LOT, rim=HEADS9, sfx=[(T(370) + 0.2, 'clipboard_clatter', 0, 0, 'outside')], c=PU(0.03, 1.5, x=760, y=700, hit=[(T(370) + 0.2, 3.0)]))
    # 371 "Grandma gasps."
    bust(T(371), 'della', ('school', 'lot'), LOT, 'shout', HEADS9_L, cx=960, cy=640, scale=0.88, turn=0.2, act=_A(lambda a, s: a.look_at(s.t0, (1300, 760), dur=0.15), ex('tender', T(371) + 0.8, None, 0.5)))
    # 372-373 "Now she can see Theo." "She kneels."
    C(T(372), 'set', room='school', view='lot', set=LOT, rim=HEADS9,
      ppl=[P('theo_color', (-1.4, -5.45), face='lot_kneel', expr='kind_smile'),
           P('della', 'lot_kneel', kind='stand', face=(-1.4, -5.45), expr='tender', act=lambda a, s: a.kneel_down(T(373) + 0.05, 0.9)),
           P('mina_bare', (-0.6, -6.6), face=(-1.4, -5.45), expr='relief'),
           P('sami_torn', (-0.25, -6.3), face=(-1.4, -5.45), expr='dazed')],
      c=PU(0.015, 1.25, x=760, y=640))
    # 374 D "Six mornings, you said thank you. And I never asked your name."
    bust(T(374), 'della', ('school', 'lot'), LOT, 'tender', HEADS9_L, cx=900, cy=680, scale=0.85, turn=0.35, act=_A(lambda a, s: a.look_at(s.t0, (1500, 520), dur=0.3), blinks(T(374) + 1.0)))
    bust(W(374, 'and'), 'theo_color', ('school', 'lot'), LOT, 'kind_smile', HEADS9, cx=1000, cy=620, scale=0.85, turn=-0.3, act=_A(lambda a, s: a.look_at(s.t0, (500, 760), dur=0.3), blinks(W(374, 'name'))))
    # 375-377 "She still knows his stop." "She won't pull away until the porch light comes on." "And for the first time in thirty-two years... it does."
    C(T(375), 'set', room='theo', view='wide', set=dict(porch=0.0), rim=NIGHT, c=PU(0.015))
    on = lambda tt: ease_out_cubic(clamp((tt - WD(377, 'does')) / 0.25))
    C(T(376), 'set', room='theo', view='house', set=dict(porch=on), rim=PORCH,
      ppl=[P('theo_color', 'walk', path=[(T(376), 'walk'), (T(376) + 2.4, 'door')], surface='porch', expr='kind_smile',
             act=lambda a, s: a.look_at(T(377) + 0.5, (960, 900), dur=0.5, body=0.4))],
      sfx=[(WD(377, 'does'), 'porch_light', -2, 0, 'outside', dict(kind='click'))], c=PU(0.012))
    # 378-385 the clipboard: names, "Sat alone.", crossed out; the last page: today's date, one name
    C(T(378), 'ins', name='clipboard', kw=dict(page='list'), sfx=[(T(378) + 0.1, 'paper_flip', -6, 0, 'close')], c=dict(mv='push', rate=0.02))
    C(T(380), 'ins', name='clipboard', kw=dict(page='list'), motion=lambda u: (0.0, -40.0 * ease_in_out(clamp(u / 3.0)), 0.3, 0.0),
      tags=[tagc(WD(380, 'sat'), 'SAT ALONE', 'red', 1500, 300, 1.0)], c=dict(mv='push', rate=0.0))
    C(T(383), 'ins', name='clipboard', kw=dict(page='last'), sfx=[(T(383), 'page_turn', -4, 0, 'close')], c=dict(mv='push', rate=0.03))
    C(T(384), 'ins', name='clipboard', kw=dict(page='last'), motion=lambda u: (0.0, 0.0, 0.35, 0.0), c=dict(mv='push', rate=0.03))
    # 386 "In the morning, I delete the post, and tell Grandma I'm sorry."  387 "She hugs me."  388 D "Brakes, mirrors, names."
    C(T(386), 'ins', name='post', kw=dict(show=2), era='morning', strike=(WD(386, 'delete') + 0.1, 560, 520, 1360, 560), sfx=[(WD(386, 'delete') + 0.1, 'phone_tap', -6, 0, 'close')],
      c=dict(mv='push', rate=0.02))
    LM = dict(LIV_EVE, backpack='wall')
    C(W(386, 'tell'), 'set', room='living', view='couch3q', set=LM, rim=MORNING, era='morning',
      ppl=[P('della', 'couch_left', kind='seat', expr='tender', act=lambda a, s: a.look_at(-9, (s.A['mina'], 'eyes') if 'mina' in s.A else scr(s.sp, 'couch_mid', dy=-300), dur=0.3)),
           P('mina', 'couch_mid', kind='seat', expr='guilt',
             act=_A(lambda a, s: a.look_at(-9, (s.A['della'], 'eyes'), dur=0.3),
                    lambda a, s: a.reach_to(T(387) + 0.1, 1, (s.A['della'], 'chest'), dur=0.5, contact='palm', shape='open', z=40.0),
                    ex('relief', T(387) + 0.4, None, 0.5)))],
      acts=_hug_acts,
      c=PU(0.015, 1.15))
    bust(T(388), 'della', ('living', 'couch3q'), LM, 'warm', MORNING, era='morning', cx=880, cy=640, scale=0.85, turn=0.35,
         act=_A(lambda a, s: a.look_at(s.t0, (1450, 640), dur=0.3), lambda a, s: a.head_tilt(W(388, 'names'), 8.0, 0.6)),
         busts=[dict(who='mina', cx=1450, cy=700, scale=0.7, turn=-0.45, expr='relief', light=MORNING, act=lambda a, s: a.look_at(s.t0, (880, 600), dur=0.3))])
    # 389-390 "In seat twenty-one, a new girl sits alone." "No name on her backpack."
    C(T(389), 'set', room='bus', view='seat21', set=B9M, rim=MORNING, era='morning',
      ppl=[P('new_girl', 'seat21_win', kind='seat', expr='lonely', act=_A(lambda a, s: a.hug_prop(-9, 'backpack'), lambda a, s: a.look_at(T(389) + 0.3, scr(s.sp, 'window21'), dur=0.6)))],
      c=PU(0.015))
    C(T(390), 'set', room='bus', view='seat21', set=B9M, rim=MORNING, era='morning',
      ppl=[P('new_girl', 'seat21_win', kind='seat', expr='lonely', act=_A(lambda a, s: a.hug_prop(-9, 'backpack'), lambda a, s: a.look_at(-9, scr(s.sp, 'window21'), dur=0.01)))],
      c=PU(0.03, 1.6, x=830, y=760))
    # 391 "I walk past my usual seat, and sit down next to her."
    C(T(391), 'set', room='bus', view='aisle', set=B9M, rim=MORNING, era='morning',
      ppl=[P('mina', 'aisle2', path=[(T(391), 'aisle2'), (W(391, 'sit') - 0.1, (0.0, 9.45))], surface='bus', expr='resolve')],
      sfx=[(T(391) + 0.2, 'bus_ambience', -12, 0, 'bus', dict(dur=2.0, kind='bus9_morning'))], c=PU(0.015))
    C(W(391, 'sit'), 'set', room='bus', view='seat21', set=B9M, rim=MORNING, era='morning',
      ppl=[P('new_girl', 'seat21_win', kind='seat', expr='lonely', act=_A(lambda a, s: a.hug_prop(-9, 'backpack'), lambda a, s: a.look_at(W(391, 'sit') + 0.4, scr(s.sp, 'seat21_aisle', dy=-150), dur=0.4))),
           P('mina', 'seat21_aisle', kind='seat', sit_t=W(391, 'sit') + 0.05, sit_dur=0.8, expr='kind_ask',
             act=lambda a, s: a.look_at(W(391, 'sit') + 0.6, scr(s.sp, 'seat21_win', dy=-140), dur=0.4))],
      c=PU(0.015))
    # 392 "Hi. I'm Mina. What's your name?"  (lip sync)  393 "She tells me."
    bust(T(392), 'mina', ('bus', 'seat21'), B9M, 'kind_ask', MORNING, era='morning', cx=820, cy=640, scale=0.82, turn=0.4,
         act=_A(lambda a, s: a.look_at(s.t0, (1500, 680), dur=0.3), lambda a, s: a.wave(s.t0 + 0.05, s.t0 + 0.8, 1)),
         busts=[dict(who='new_girl', cx=1460, cy=720, scale=0.62, turn=-0.4, expr='lonely', light=MORNING, act=lambda a, s: a.look_at(s.t0 + 0.6, (820, 600), dur=0.4))])
    bust(T(393), 'new_girl', ('bus', 'seat21'), B9M, 'kind_smile', MORNING, era='morning', cx=980, cy=660, scale=0.85, turn=-0.3,
         act=_A(lambda a, s: a.look_at(s.t0, (400, 620), dur=0.3), lambda a, s: a.talk([(T(393) + 0.05, E(393) + 0.2, 'my name is')], env=None, words=None)))
    # 394 "It's the name on his last page."
    C(T(394), 'ins', name='clipboard', kw=dict(page='last'), cut='white', motion=lambda u: (0.0, 0.0, 0.4, 0.0), sfx=[(T(394), 'sting_name', 0, 0, None)], c=dict(mv='push', rate=0.04))
    # 395 "Out the back window, something very tall in a crooked yellow hat lifts a new clipboard."  396 "Draws a line ... and starts writing the next."
    C(T(395), 'set', room='bus', view='back_window', set=B9M, rim=MORNING, era='morning', c=PU(0.04, 1.0, x=980, y=520),
      post_fn=lambda tt: dict(glitch=0.12 if (tt * 3.0) % 1.0 < 0.06 else 0.0))
    C(W(395, 'lifts'), 'set', room='bus', view='back_window', set=B9M, rim=MORNING, era='morning', cut='vhs', c=PU(0.04, 2.2, x=980, y=520),
      sfx=[(W(395, 'lifts'), 'tape_skip', -4, 0, None)])
    C(T(396), 'ins', name='clipboard', kw=lambda u: dict(page='last', write=clamp((u - 0.3) / 2.8)), cut='vhs', sfx=[(T(396) + 0.3, 'pencil_line', -4, 0, 'close', dict(dur=2.8))],
      c=dict(mv='push', rate=0.03))
    # 397 "That night, under Grandma's seven, I write one more."
    C(T(397), 'set', room='hall', view='doorclose', set=dict(HALL_NIGHT, hall=1.0, porch=1.0, rules=True, eighth=True), rim=LAMP,
      ppl=[P('mina', 'door_inside', face=(-3.95, 0.0), expr='resolve',
             act=_A(lambda a, s: a.hold_prop('pen', 1, -9, None), lambda a, s: a.reach_to(T(397) + 0.2, 1, scr(s.sp, 'rules', dy=60), dur=0.5, contact='grip', shape='grip', z=20.0),
                    lambda a, s: a.look_at(T(397), scr(s.sp, 'rules', dy=40), dur=0.4)))],
      sfx=[(T(397) + 0.8, 'marker_write', -6, 0, 'inside', dict(dur=2.0))], c=PU(0.02))
    C(T(398), 'rule', n=8)


def _hug_acts(A, sh, sp):
    """387 'She hugs me.': Grandma's arms round Mina (both hands land on her shoulders); no extra layers."""
    A['della'].reach_to(T(387) + 0.05, 1, (A['mina'], 'shoulder_r'), dur=0.5, contact='palm', shape='open', z=-20.0)
    A['della'].reach_to(T(387) + 0.12, -1, (A['mina'], 'shoulder_l'), dur=0.5, contact='palm', shape='open', z=40.0)
    return []


# ==================================================================================================== OUTRO (401-418)
def plan_outro(F):
    t, e, C = F.t, F.e, F.cut
    O = dict(era='outro')
    C(T(401), 'outro', mode='nohim', keys=dict(x=W(401, 'whistlestop')), sfx=[(W(401, 'whistlestop'), 'marker_x', -4, 0, 'close')], **O)
    C(T(402), 'outro', mode='tricks', keys=dict(k0=W(402, 'every'), k1=W(402, 'trick'), k2=W(402, 'used')), **O)
    stops = [403, 404, 405, 406, 407, 408, 410, 411]
    C(T(403), 'outro', mode='route', keys=dict(stops=[WD(i, F.L[i]['en'].split()[0].strip('".,').lower()) - 0.05 for i in stops], tell=WD(409, "that's")), **O)
    C(T(413), 'outro', mode='yes', keys=dict(press=WD(413, 'yes'), wanted=WD(414, 'exactly')), **O)
    C(T(415), 'outro', mode='like', keys=dict(stop=WD(415, 'like'), theo=WD(415, 'theo')), **O)
    C(T(416), 'outro', mode='subscribe', keys=dict(arm=WD(416, 'subscribe'), door=WD(416, 'door')), **O)
    C(T(417), 'outro', mode='next', keys=dict(truck=WD(417, 'ice'), winter=WD(417, 'winter'), dont=WD(418, "don't")), **O)
    C(E(418) + 0.6, 'outro', mode='end', keys=dict(), **O)


def plan_partb(F):
    plan_rule5(F)
    plan_rule6(F)
    plan_rule7(F)
    plan_after(F)
    plan_outro(F)
    g = F.globals
    g.append({'t': round(T(375), 3), 'type': 'jingle', 'level': 0.2, 'len': round(F.t(386) - T(375), 2), 'version': 'music_box_warm'})
    g.append({'t': round(T(386), 3), 'type': 'jingle', 'level': 0.18, 'len': round(F.t(393) - T(386), 2), 'version': 'morning_warm'})
    g.append({'t': round(T(394), 3), 'type': 'sting', 'level': 0.5, 'len': 2.0, 'version': 'name_sting'})
    g.append({'t': round(T(401), 3), 'type': 'jingle', 'level': 0.22, 'len': round(F.duration - T(401), 2), 'version': 'outro_warm'})


# ==================================================================================================== film-wide music
def plan_globals(F):
    """Film-wide music cues keyed to lines: the 'Ride Right with Mister Whistlestop!' theme (the returning tune) by version."""
    g = F.globals
    n = len(F.L)
    g.append({'t': round(T(0) + 0.2, 3), 'type': 'drone', 'level': 0.35, 'len': round(F.t(5) - T(0), 2), 'version': 'cold_open'})
    g.append({'t': round(T(22), 3), 'type': 'jingle', 'level': 0.18, 'len': round(F.t(29) - T(22), 2), 'version': 'music_box_warm'})
    g.append({'t': round(T(67), 3), 'type': 'jingle', 'level': 0.3, 'len': round(F.t(79) - T(67), 2), 'version': 'loudspeaker_detuned', 'loop': True})
    g.append({'t': round(T(88), 3), 'type': 'jingle', 'level': 0.28, 'len': round(F.t(122) - T(88), 2), 'version': 'slowed_tape', 'loop': True})
    g.append({'t': round(T(161), 3), 'type': 'jingle', 'level': 0.22, 'len': round(F.t(180) - T(161), 2), 'version': 'walkie_far', 'loop': True})
    if n > 286:
        g.append({'t': round(T(286), 3), 'type': 'jingle', 'level': 0.45, 'len': round(F.t(364) - T(286), 2), 'version': 'climax_warped', 'loop': True})


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

