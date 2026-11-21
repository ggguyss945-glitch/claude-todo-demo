"""film.py: the shot list, editor and cue sheets for "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"
(Night Policy).

Built in the machinery of the bus film (now W/film_bus_old.py) and the film_*_ref.py references: the same engine, cast
system (characters.py + characters_ice.py) and set system (sets.py + sets_ice.py), the police header / rule cards /
captions / tags, a global look with a climax ramp, and cue sheets derived from the picture. The shot map this list
follows line by line is W/shotmap.md (every timeline line -> the picture that shows it). EVERY time in the plan is keyed
to timeline.json (line starts / ends and word times): there is no absolute time anywhere, so a re-edit of the narration
moves the picture with its lines.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + TAIL)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --bench N [--shots ..]

THE OWNER'S NOTES, MADE INTO CODE:
  * Staging lives on the sets' plan (sets_ice: our house, Birch Lane and Mr. Kessler's house on one plan in metres, the
    truck at A / B). Every figure in a set shot stands on a plan point (an anchor or (x, y[, Y])): its height from the
    px-per-metre there, feet in the snow (IC_FOOT: sunk, never floating), draw order from sp.order_at(), light from
    sp.light_kw(). Seats come from the spot's kind (nobody stands on furniture).
  * Prefer cuts; the camera only pushes a little while people act.
  * MISTER SHIVER is ACTIVE in every beat: he leans, waves his over-long wave, looks, snaps his eyes, reaches, bends
    down impossibly, transforms (one continuous transform() keyed to the narration's words across every cut), pours out,
    stabs, scuttles, drops. He never lip-syncs and never breathes a cloud (breath puffs are drawn for everyone else
    outside or in the cold house: cold=True on a shot).
  * Lip sync on character lines only (VOICE: D Dad, L Lina, K Kessler; Adam's quoted lines inside the narration are
    'NQ'); narrator lines move no mouths; his voice (S) moves no mouth (truck voice / mimic on the radio or the door).
  * escalate(): no "scared jiggle"; tension shows as wider eyes, raised brows and faster breath for the kids.

Shot kinds (builders B_<kind>):
  set      a set view (sets_ice ic_* builders) with figures on the plan: room 'street' | 'living' | 'hall' | 'kitchen' |
           'bath' | 'y58' | 'morning' | 'town'; view = the builder's view; cam = None (the view's own camera) or cm(...);
           set = builder kwargs; ppl = [P(who, at, ...)]; acts = f(A, shot, sp) -> [layers]; cold=True (breath puffs)
  bust     a face close-up over a blurred set (bg=(room, view[, cam]) + set=dict(..)); busts=[..]; hands=[..]; plain=(c1, c2)
  ins      a prop insert: sets_ice ic_insert(name, kw, motion); kw = dict or f(time since the cut) -> dict; hands=[..]
  rule     the police rule card over Mr. Kessler's rules paper taped inside our front door (rule n lit)
  pause    the comment prompt (stage 'stop' | 'ask'): the screen frosts over; INSIDE / OUTSIDE; his glove cursor
  card     plain graphic cards (part B: the outro)
  black    black (with an optional line of text)
Plan conventions: F.cut(t, kind, **p) starts a shot that ends at the next cut. F.t(i) / F.e(i) line start / end,
F.w(i, 'word') the ASR start of a word inside line i; T(i) = F.t(i) - LEAD, W(i, 'word') = F.w(i, 'word') - LEAD,
WD(i, 'word') = the word itself. Common p keys: c=dict(mv='push'|'keys'|'hold', f, rate, x, y, keys=[(t, x, y, z, ease,
f)], hit=[t]), tags=[(t, text, x, y, style, hold)], sfx=[(t, name, gain_db, pan, space, params)], music=[(t, type,
level, len, extra)], cut='white'|'static'|'blink', era='now'|'memory'|'morning'|'outro', grade, post, post_fn, focus
(or focus_on=who), dof. See W/handoff/film_a.md for the helpers.
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
TAIL = 4.0                       # the end card holds after the last line
TITLE = "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"
BASE = 'If_The_Ice_Cream_Truck_Plays_In_Winter'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card

PART_B = 263                       # part A = lines 0..262 (cold open .. "Shivering means you're fighting."), part B = 263..
def set_retime(lines, duration): return None


def at(t): return t


def authored(t): return t


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (code, fx or None): narrator lines (N) move no mouths; Mister Shiver (S: the truck
# voice, the mimic on the radio / at the door) moves NO mouth. 'NQ' = Adam's own quoted lines inside the narration.
VOICE = {'adam': [('NQ', None)], 'adam_in': [('NQ', None)], 'adam_sock': [('NQ', None)], 'lina': [('L', None)], 'lina_pj': [('L', None)],
         'dad': [('D', None)], 'kessler': [('K', None)], 'kessler_out': [('K', None)], 'kessler_am': [('K', None)], 'kessler_wrap': [('K', None)],
         'shiver': [], 'shiver_mom': [], 'walter58': [], 'benny': [], 'mom_photo': [], 'medic_a': [], 'medic_b': []}
WHISPER = ('whisper',)
KIDS = ('adam', 'adam_in', 'adam_sock', 'lina', 'lina_pj')
# ---------------------------------------------------------------- the story clock (header corner), keyed to lines
def _hm(h, m): return h * 60 + m


CLOCK_KEYS = [(43, _hm(23, 2)), (117, _hm(23, 47)), (168, _hm(26, 10)), (267, _hm(27, 5))]
TEMP_KEYS = [(43, -33), (168, -38), (277, -40)]
CORNER = [(0, 'BIRCH LANE'), (9, 'LARKFIELD'), (20, 'EVERY MORNING'), (26, '1958'), (31, 'BIRCH LANE'), (34, 'YESTERDAY'),
          (35, 'THIS MORNING'), (38, 'TONIGHT'), (43, None), (395, 'THE MORNING AFTER'), (399, 'TWO NIGHTS LATER'), (402, 'BIRCH LANE'),
          (407, CHANNEL)]


def clock_str(t):
    F = _FILM[0]
    lab = None
    for i, s in CORNER:
        if i < len(F.L) and t >= F.t(i) - LEAD: lab = (s,)
    if lab and lab[0] is not None: return lab[0]
    if F.t(87) - LEAD <= t < F.t(92) - LEAD: t = F.t(87) - LEAD          # the comment prompt: the clock stops
    ks = [(i, m) for i, m in CLOCK_KEYS if i < len(F.L)]
    ts = [F.t(i) for i, _ in ks]; ms = [m for _, m in ks]
    m = float(np.interp(t, ts, ms))
    h, mm = int(m // 60) % 24, int(m % 60)
    tk = [(i, c) for i, c in TEMP_KEYS if i < len(F.L)]
    deg = int(round(float(np.interp(t, [F.t(i) for i, _ in tk], [c for _, c in tk]))))
    return '%d:%02d %s   %d°' % ((h % 12) or 12, mm, 'AM' if h < 12 else 'PM', deg)


def header(cv, right, corner, alpha=255):
    """The police header with this film's left label."""
    left = 'RULES FOR A COLD SNAP'
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
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.25)                   # frost-blue moonlight
NIGHT_L = dict(rim='#8fa6e8', rim_a=70, side=-1, key=-0.25)
DARK = dict(rim='#8fa6e8', rim_a=40, side=1, key=-0.45)                   # the house after the power dies
PINK = dict(rim='#ff9ec8', rim_a=130, side=1, key=-0.15)                  # HIS window's warm pink (the lure)
PINK_L = dict(rim='#ff9ec8', rim_a=130, side=-1, key=-0.15)
PINK_D = dict(rim='#ff9ec8', rim_a=90, side=1, key=-0.38)                 # pink through the curtains, the dark house
BEACON = dict(rim='#ffa030', rim_a=130, side=-1, key=-0.2)                # Dad's orange beacon
AMBER = BEACON
PHONE = dict(rim='#dfeaff', rim_a=80, side=1, key=-0.35)                  # a phone screen in the dark
MORNING = dict(rim='#fff0c8', rim_a=60, side=1, key=0.16)                 # the morning after: warm and safe
SEPIA = dict(rim='#e8d4b0', rim_a=60, side=1, key=0.0)                    # 1958
SH_PINK = dict(rim='#ff9ec8', rim_a=110, side=1, key=-0.05, under='#ff9ec8', under_a=55)   # him in his window
SH_NIGHT = dict(rim='#9fb6ff', rim_a=90, side=1, key=-0.3)                # him out in the snow (moonlight)
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

# ==================================================================================================== sets on the plan
ROOMS = {'street': 'ic_street', 'living': 'ic_living', 'hall': 'ic_hall', 'kitchen': 'ic_kitchen', 'bath': 'ic_bath', 'y58': 'ic_1958',
         'morning': 'ic_morning', 'town': 'ic_town'}
_PRE = {'street': 'ic_ext_', 'living': 'ic_liv_', 'hall': 'ic_hall_', 'kitchen': 'ic_kit_', 'bath': 'ic_bath_', 'y58': 'ic_ext_',
        'morning': 'ic_ext_', 'town': 'ic_ext_'}


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
    if q.get('act'):
        try: q['act'](a, sh)
        except KeyError:                                    # it reaches an actor not placed yet: run it after all are placed
            if getattr(sh, '_defer', None) is None: raise
            sh._defer.append((q['act'], a))
    child = None
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
            if child is not None and t >= cq_.get('t0', -9.0) and (cq_.get('t1') is None or t < cq_['t1']):
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
# The film-wide acting arc, keyed to timeline lines. NO tremble ("scared jiggle") as filler: tension shows in the kids'
# eyes, brows and breath. Lina has her own arc: the cold makes her calm, sleepy and dazed (rule 4), never wide-eyed.
KID_ARC = [(0, 0.3), (9, 0.0), (40, 0.15), (54, 0.25), (65, 0.45), (84, 0.6), (96, 0.55), (110, 0.8), (116, 0.9), (125, 0.6), (144, 0.75),
           (152, 0.85), (165, 0.6), (172, 0.85), (195, 1.0), (234, 0.9), (250, 0.6), (258, 0.4), (263, 0.6), (281, 0.9), (298, 0.95),
           (312, 0.7), (351, 0.9), (371, 0.5), (386, 0.2), (395, 0.0)]
LINA_ARC = [(0, 0.2), (9, 0.0), (84, 0.4), (110, 0.6), (116, 0.8), (130, 0.5), (136, 0.2), (139, 0.0), (146, 0.6), (151, 0.1), (170, 0.0),
            (186, 0.0), (195, 0.9), (234, 0.8), (250, 0.3), (258, 0.5), (263, 0.5), (281, 0.9), (298, 0.95), (312, 0.6), (351, 0.8),
            (371, 0.4), (386, 0.1), (395, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    pts = [(F.t(i), b) for i, b in arc if i < len(F.L)]
    return float(np.interp(t, [p[0] for p in pts], [p[1] for p in pts]))


def escalate(a, sh, who):
    if sh.kind in ('rule', 'card', 'black', 'pause') or sh.p.get('era') in ('memory', 'outro', 'morning'): return
    if who in KIDS:
        k = _arc(LINA_ARC if who.startswith('lina') else KID_ARC, sh.t0)
        if k <= 0.02: return

        def fn(P_, t, k=k):
            P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
            per = 3.9 - 1.5 * k
            P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)

# ==================================================================================================== builders: sets
ROOM_RIM = {'street': NIGHT, 'living': LAMP, 'hall': NIGHT, 'kitchen': LAMP, 'bath': DARK, 'y58': SEPIA, 'morning': MORNING, 'town': NIGHT}
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



ALIAS = {'adam': ('adam', 'adam_in', 'adam_sock'), 'lina': ('lina', 'lina_pj'), 'kessler': ('kessler', 'kessler_out', 'kessler_am'),
         'shiver': ('shiver', 'shiver_mom')}
class ADict(dict):
    """The shot's actors by id; 'adam' / 'lina' / 'kessler' also find the costume variant placed in the shot."""
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
        if cold and q.get('breath', True) is not False and not q['who'].startswith('shiver'): ex_.append(puffs())
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
                        light=p.get('light', ROOM_RIM.get((p.get('bg') or ['x'])[0], LAMP)), seed=p.get('seed', 0), blink=p.get('blink'))
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
    sp = ST.ic_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
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


# ==================================================================================================== rule cards
# Mr. Kessler's paper taped inside our front door (signed W.K.): the card text is the narration's words; the key clause
# is starred (rendered in the accent colour; no asterisk ever reaches the screen).
RULE_TEXT = {1: "When you hear his song, *close every curtain.* If he can't see you, he can't call you.",
             2: "If he leaves you a free one, *don't touch it, don't bring it in, and never taste it.* Nothing he gives is free.",
             3: "If the heat goes out, put on every layer you own, and *get under one blanket together.* Nobody sleeps alone tonight.",
             4: "If you stop shivering, *tell someone right away.* Shivering means you're still fighting.",
             5: "If someone you love knocks, *look for their breath.* In this cold, everyone's breath makes a cloud. His doesn't.",
             6: "If the house gets as cold as outside, it isn't inside anymore. *Find the smallest room, shut the door, and block the drafts.*",
             7: "*Don't go outside before sunrise.* Not for anyone. Not for anything. Not even for me.",
             8: "*Never go out for him. Go out for each other.* Together, with a grown-up."}


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
    """The police rule card over Mr. Kessler's rules taped inside our front door (blurred, dimmed; rule n lit; rule 8 in
    Adam's hand under them); the sentence being read is underlined as it is read."""
    p = sh.p
    n = p['n']
    sp = ST.ic_insert('rules', dict(show=7, hl=n if n <= 7 else 0, eighth=(n == 8), door='ours'))
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
                    if L_ > 0: pen.fill(rrect(x0, y_ + 9, L_, 4, 2), '#9fd8ff', 230 * k_)
        tm_ = H.rule_times(RULE_TEXT[n], None)        # (owner's-eyes: the plate fades in with the typing, never an empty bar first)
        pa_ = 255 * 0.86 * clamp((tt_ - tm_['type0'] + 0.15) / 0.3)
        if pa_ > 0:
            lines_ = H.wrap_rich(RULE_TEXT[n].upper(), 800, 31, 760, 0.045)
            pw_ = max(H.text_width(l_.replace('*', ''), 800, 31, 0.045) for l_ in lines_) + 96
            Pen(cv).fill(rrect(DW / 2 - pw_ / 2, 600, pw_, (len(lines_) - 1) * 44 + 76, 18), '#0b0c12', pa_)
        H.rule_card(cv, n, RULE_TEXT[n], tt_, total=8 if n == 8 else 7, icon=None, scrim=0.45, accent='#9fd8ff', plate=0.0)
        # the frost creeping in from the card's corners (the cold film's touch): a soft ring that grows with the read
        u = clamp(tt_ / 4.0)
        Pen(cv).radial(None, DW / 2, DH / 2, 1250, [(0.62, '#cfe4ff', 0), (1.0, '#cfe4ff', 70 * u)], sy=0.62)
    cam = scam(sh, None, dict(mv='push', rate=0.012, free=True))

    def fx(t):
        d = dict(blur=6, dim=0.45)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(list(sp), cam, None, 'ic_ins', 1.0, 0.0, fx=fx, hud=hud)
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


def _house_icon(pen, x, y, s, a=255, light=1.0, t=0.0):
    """INSIDE: a small warm house, a lit window, smoke from the chimney."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    pen.glow(0, -200, 300, '#ffb860', 70 * light * a / 255)
    pen.fill(rect(-200, -400, 400, 400), '#c9b28c', a)
    pen.fill(poly([(-240, -400), (0, -560), (240, -400)]), '#6a3a2a', a)
    pen.fill(poly([(-250, -395), (0, -572), (250, -395), (250, -380), (0, -552), (-250, -380)]), '#f4f8ff', a)    # snow on it
    pen.fill(rect(110, -540, 50, 110), '#6a3a2a', a)
    for k in range(3):
        u = ((t * 0.35 + k / 3.0) % 1.0)
        pen.fill(oval(135 + 30 * math.sin(u * 5 + k), -560 - 160 * u, 26 + 30 * u), '#e8e8f0', a * 0.6 * (1 - u))
    pen.fill(rrect(-150, -300, 140, 120, 8), '#ffd890', a * (0.5 + 0.5 * light))
    pen.fill(rrect(40, -260, 110, 260, 8), '#5a3a5a', a)
    cv.restore()


def _truck_icon(pen, x, y, s, a=255, t=0.0):
    """OUTSIDE: his pink-and-white striped step van, the frosted snowflake on the roof, the warm pink window."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    body = rrect(-270, -260, 400, 250, 26)
    pen.fill(body, '#f7f2f4', a)
    cv.save(); cv.clipPath(body, skia.ClipOp.kIntersect, True)
    for k in range(-6, 8, 2):
        pen.fill(rect(k * 36, -270, 36, 270), '#e58fb4', a)
    cv.restore()
    pen.fill(rrect(130, -190, 130, 180, 24), '#e8e2e6', a)                        # the cab
    pen.fill(rrect(150, -175, 90, 70, 10), '#1c2436', a)
    pen.glow(-80, -150, 170, '#ff9ec8', 110 * a / 255)
    pen.fill(rrect(-200, -200, 230, 100, 10), '#ff9ec8', a)                      # the serving window: warm pink
    for k in range(6):
        pen.fill(rrect(-185 + k * 36, -192 + 10 * math.sin(k * 1.3), 20, 26, 7), ('#e8e8f0', '#9fd8ff', '#f4b4cf', '#c8e0a0', '#ffd890', '#d8262e')[k], a)
    cx_, cy_ = -70, -320
    for k in range(6):                                                           # the snowflake on the roof
        ang = k * math.pi / 3 + 0.2 * math.sin(t)
        pen.seg((cx_, cy_), (cx_ + 60 * math.cos(ang), cy_ + 60 * math.sin(ang)), 10, '#ddebf5', a)
    pen.fill(oval(cx_, cy_, 16), '#c9d6e3', a)
    pen.seg((cx_, cy_ + 40), (cx_, -262), 8, '#c9d6e3', a)
    for wx in (-180, 170):
        pen.fill(oval(wx, -6, 40), '#1a1816', a)
    cv.restore()


def B_pause(F, sh):
    """The comment prompt (lines 87-91): stage 'stop' = the picture freezes and frost creeps over the screen from the
    edges ("Stop."); stage 'ask' = "His song is playing outside your house right now." -> ONE WORD IN THE COMMENTS ->
    INSIDE (a warm house) or OUTSIDE (his truck) with his white glove cursor drifting toward OUTSIDE; on "Remember your
    answer." the frost closes in. p: stage, t_word (ONE WORD), t_q (INSIDE... OR OUTSIDE?), t_rem (remember), freeze_t."""
    p = sh.p
    t0 = sh.t0
    st_ = p.get('stage', 'ask')
    sp = ST.ic_street('house', win=dict(liv=0.9, kitchen=0.5))
    layers = list(sp)
    tw, tq, tr = p.get('t_word', t0 + 3.0), p.get('t_q', t0 + 4.6), p.get('t_rem', t0 + 6.4)

    def frost(pen, k, t):
        if k <= 0: return
        pen.radial(None, 960, 540, 1300, [(0.35 + 0.3 * (1 - k), '#e6f1ff', 0), (1.0, '#e6f1ff', 230 * k)], sy=0.6)
        rng = np.random.default_rng(7)
        for i in range(70):
            ang = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.75, 1.1)
            L_ = rng.uniform(60, 220) * k
            x0, y0 = 960 + math.cos(ang) * 1150 * r0, 540 + math.sin(ang) * 700 * r0
            x1, y1 = x0 - math.cos(ang) * L_, y0 - math.sin(ang) * L_
            pen.seg((x0, y0), (x1, y1), 2.0, '#ffffff', 150 * k)

    def hud(cv, t):
        pen = Pen(cv)
        u = t - t0
        if st_ == 'stop':
            frost(pen, ease_out_cubic(clamp(u / 0.5)) * 0.8, t)
            text(cv, 'STOP.', 960, 590, 900, 150, '#ffffff', 255 * clamp(u / 0.12), 0.06, 'center', 0.7)
            return
        pen.fill(rect(0, 0, DW, 1080), '#06070c', 150 * clamp(u / 0.3))
        frost(pen, 0.8 + 0.2 * ease_in_out(clamp((t - tr) / 0.8)), t)
        if t < tw:                                   # "His song is playing outside your house right now."
            k = clamp(u / 0.3)
            _truck_icon(pen, 960 + 60 * math.sin(u * 0.8), 700, 1.15, 255 * k, t)
            for j in range(3):                       # the chime's notes drifting out of the snowflake horn
                v_ = ((u * 0.5 + j / 3.0) % 1.0)
                text(cv, '♪', 880 + 40 * j + 60 * v_, 320 - 160 * v_, 700, 56, '#ffd6ea', 230 * k * (1 - v_), 0.0, 'center', 0.0)
            text(cv, 'RIGHT NOW', 960, 860, 900, 56, '#ffd6ea', 235 * clamp((u - 0.6) / 0.3), 0.18, 'center', 0.5)
            return
        kw = clamp((t - tw) / 0.25)
        kr = clamp((t - tr) / 0.3) if t >= tr else 0.0                  # "Remember your answer." takes the headline's place
        text(cv, 'ONE WORD IN THE COMMENTS', 960, 230, 800, 52, '#ffffff', 245 * kw * (1 - kr), 0.2, 'center', 0.5)
        if t < tq: return
        kb = ease_out_back(clamp((t - tq) / 0.4))
        sel = ease_in_out(clamp((t - tq - 0.8) / 1.6))
        for x_, lab, warm in ((620, 'INSIDE', True), (1300, 'OUTSIDE', False)):
            s_ = max(0.01, kb)
            if warm: _house_icon(pen, x_, 700, 0.55 * s_, 255 * clamp(kb), 1.0, t)
            else: _truck_icon(pen, x_ + 40, 690, 0.62 * s_, 255 * clamp(kb), t)
            c_ = '#ffd890' if warm else '#ff9ec8'
            pulse = 0.5 + 0.5 * math.sin((t - tq) * 6.0)
            if not warm: pen.glow(x_, 560, 260, '#ff6aa8', 40 * sel * pulse)
            text(cv, lab, x_, 860, 900, 84 * s_, c_, 255 * clamp(kb), 0.08, 'center', 0.6)
        text(cv, 'OR', 960, 600, 700, 40, '#c8ccd8', 220 * clamp(kb), 0.3, 'center', 0.4)
        # HIS glove cursor: it drifts in from the right toward OUTSIDE, hovers... and on "Remember your answer." it backs off
        back = ease_in_out(clamp((t - tr) / 0.7))
        gx = lerp(1780, 1330, sel) + 420 * back; gy = lerp(1000, 640, sel) + 300 * back
        _glove_cursor(pen, gx, gy, 1.6, 255 * clamp((t - tq - 0.5) / 0.3) * (1 - back), press=0.0, curl=0.1 * math.sin(t * 3) ** 2)
        if t >= tr:
            text(cv, 'REMEMBER YOUR ANSWER.', 960, 230, 800, 52, '#e6f1ff', 245 * kr, 0.2, 'center', 0.5)
    c = dict(mv='push', f=1.15, rate=0.01, x=880, y=560, free=True)
    cam = scam(sh, sp.info.get('cam_env'), c)

    def fx(t):
        d = dict((sp.fx(t) if hasattr(sp, 'fx') else None) or {})
        d['blur'] = 5 if st_ == 'ask' else 0
        if t - t0 < 0.1 and st_ == 'stop': d['white'] = 0.5
        return d
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=fx, hud=hud)

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



BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}

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
DARK_LIFT = 0.35
DARK_LIFT_ROOM = dict(hall=0.7, bath=0.55)          # requests: the dead-house hall read near-black (no window light there)

def glob_fx(F, sh, t, fx):
    """Per-frame global effects (keyed to lines): cut flashes ('white', 'static', 'blink' = the lights going out); grain
    that rises with the night; the house going cold blue after the power dies (L116); the climax ramp (the crossing,
    L351 .. the defeat, L385): pink edge pulses on the chime's 3/4 tempo, less colour, more grain; 1958, the morning
    and the outro clean; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'blink' and u < 0.12: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - u / 0.12)
    ek = EXPO.get(sh.kind, 0.0)
    if sh.kind == 'set' and (sh.p.get('set') or {}).get('blackout') and sh.p.get('room') in ('living', 'hall', 'kitchen', 'bath'):
        ek += DARK_LIFT_ROOM.get(sh.p.get('room'), DARK_LIFT)   # the dead house: dark, but the action must read (bus-film lesson)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('outro', 'morning') or sh.kind in ('rule', 'black', 'card', 'pause')
    if not clean:
        ui = 0.5 if sh.kind == 'ins' else 1.0
        g = 0.05 + 0.1 * clamp((t - F.t(43)) / max(1.0, F.t(351) - F.t(43))) if len(F.L) > 351 else 0.08
        fx['grain'] = max(fx.get('grain', 0.0), g)
        if len(F.L) > 386 and F.t(351) - LEAD <= t < F.t(385) + 1.5:
            ramp = clamp((t - F.t(351)) / 3.0) * (1.0 - clamp((t - F.t(385) - 0.5) / 1.0))
            bpm = lerp(72, 120, clamp((t - F.t(351)) / max(1.0, F.t(372) - F.t(351))))
            ph = ((t - F.t(351)) * bpm / 60.0) % 1.0
            beat = math.exp(-ph * 9.0)
            if 'flash' not in fx:
                fx['flash'] = _epost.Spill(0.26 * ramp * clamp(beat) * ui, side=-1.0 if sh.idx % 2 else 1.0, color=(1.0, 0.55, 0.75), reach=0.8)
            fx['sat'] = fx.get('sat', 1.0) * (1.0 - 0.2 * ramp)
            fx['grain'] = fx.get('grain', 0.0) + 0.08 * ramp
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)

# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names): the house warm (house_hum) until
    the power dies (L116), then the dead cold house (house_cold); the frozen street outside (cold_night) all night; HIS
    truck idling at our kerb from when the song stops (L84) until it rolls across (L307), then at Kessler's until it
    glides into the white (L388); 1958 (frozen_still); the morning (part B)."""
    D = F.duration
    n = len(F.L)
    t = lambda i: F.t(min(i, n - 1))
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(0.0, t(9) - 0.1, 'cold_night', -16, 'outside', wind=0.5)
    bed(t(9) - 0.1, t(26) - 0.1, 'house_hum', -16, 'inside')
    bed(t(26) - 0.1, t(31) - 0.1, 'frozen_still', -18, 'memory')
    bed(t(31) - 0.1, t(116), 'house_hum', -14, 'inside')
    bed(t(31) - 0.1, t(395) - 0.1, 'cold_night', -20, 'outside', wind=0.6, through_walls=True)
    bed(t(116), t(395) - 0.1, 'house_cold', -12, 'inside')
    bed(t(84), t(307), 'truck_idle', -22, 'outside', far=True, through_walls=True)
    if n > 388: bed(t(307), t(388), 'truck_idle', -24, 'outside', far=True, through_walls=True)
    if n > 395: bed(t(395) - 0.1, D, 'house_hum', -14, 'inside', kind='morning')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.6), (2, 0.75), (3, 0.9), (4, 0.7), (5, 0.35), (9, 0.2), (17, 0.35), (19, 0.15), (26, 0.4), (30, 0.6), (31, 0.4), (35, 0.5),
    (38, 0.6), (39, 0.75), (40, 0.5), (45, 0.55), (49, 0.65), (53, 0.7), (55, 0.5), (57, 0.75), (59, 0.85), (61, 0.5), (65, 0.7),
    (69, 0.8), (74, 0.85), (77, 0.7), (79, 0.85), (82, 1.0), (84, 0.8), (86, 0.9), (87, 0.3), (92, 0.6), (96, 0.75), (99, 0.85),
    (102, 0.8), (105, 0.9), (107, 0.95), (110, 1.0), (112, 0.8), (114, 0.95), (118, 0.9), (119, 1.0), (121, 0.85), (125, 0.6),
    (128, 0.7), (136, 0.6), (139, 0.65), (143, 0.8), (144, 0.9), (146, 0.85), (151, 0.9), (153, 1.0), (155, 0.6), (158, 0.85),
    (159, 1.0), (163, 0.8), (165, 0.55), (170, 0.6), (172, 0.85), (174, 0.95), (177, 0.9), (184, 1.0), (189, 0.95), (192, 1.0),
    (195, 1.0), (197, 0.9), (199, 0.85), (201, 0.9), (208, 1.0), (214, 1.0), (221, 0.9), (224, 1.0), (227, 1.0), (236, 1.0),
    (239, 1.0), (242, 0.95), (243, 0.8), (246, 0.85), (250, 0.6), (258, 0.45), (262, 0.35), (263, 0.6), (268, 0.85), (281, 1.0),
    (286, 0.6), (290, 0.9), (294, 1.0), (298, 0.95), (301, 1.0), (305, 0.7), (307, 0.6), (312, 0.75), (320, 0.85), (322, 0.5),
    (329, 0.6), (331, 0.6), (343, 0.8), (350, 0.85), (354, 1.0), (358, 1.0), (362, 0.85), (367, 0.9), (371, 0.7), (374, 0.9),
    (377, 0.6), (385, 0.4), (388, 0.3), (392, 0.2), (395, 0.1), (399, 0.45), (402, 0.3), (407, 0.15)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY if i < len(F.L)]
    pts.append([round(F.duration, 2), 0.0])
    return pts


HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(3, -0.6, 0.5), (57, -0.3, 0.6), (82, -0.4, 0.5), (119, -0.5, 0.6), (153, -0.4, 0.6), (159, -0.3, 0.4), (189, -0.4, 0.6),
             (208, -0.4, 0.5), (216, -0.3, 0.4), (239, -0.4, 0.5), (281, -0.5, 0.5), (294, -0.5, 0.5), (301, -0.5, 0.5), (358, -0.6, 0.6)]
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
    plan_setup(F)
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


# set states (the prop / light continuity of the shot map, W/shotmap.md)
FOOT = ST.IC_FOOT                                                          # feet in the lawn / street snow (sunk, never floating)
LIV_EVE = dict(lamp=1.0, ceil=0.6, truck=None, curtains=1.0)              # before the song: lamps on, curtains open
LIV_SHUT = dict(lamp=1.0, ceil=0.6, truck=None, curtains=0.0)             # after Adam closes every curtain (L54)
LIV_CRACK = dict(lamp=1.0, ceil=0.6, truck='A', curtains=0.04)            # Lina's crack (L64); the truck parked at A (L69+)
LIV_BLACK = dict(blackout=True, truck='A', curtains=0.04)                 # the power dead (L116), the crack still open
LIV_COLD = dict(blackout=True, truck='A', curtains=0.0)                   # the crack yanked shut (L124)
LIV_FROST = dict(LIV_COLD, frost=1.0)                                     # frost on the inside (L128+)
LIV_NEST = dict(LIV_FROST, blanket=True)                                  # one blanket, both of us (L135+)
HALL_ON = dict(hall=1.0, lamp=0.6, truck=None)
HALL_A = dict(hall=1.0, lamp=0.6, truck='A')
HALL_BLACK = dict(blackout=True, truck='A')
KIT_ON = dict(kitchen_light=1.0, truck=None)
KIT_A = dict(kitchen_light=1.0, truck='A')
ST_NONE = dict(truck=None, win=dict(liv=0.9, kitchen=0.5))                # Birch Lane before the truck (our lights on)
ST_A = dict(truck='A', win=dict(liv=0.6, kitchen=0.3))                    # the truck at A, our lights on (curtains drawn)
ST_DARK = dict(truck='A', blackout=True, our_smoke=0.0)                   # after the power dies
ST._GR.setdefault('ic_1958_red', dict(ST._GR['ic_1958'], mono=0.32, sat=0.85))   # 1958, but Benny's mitten stays RED


# ---------------------------------------------------------------- cut helpers
def S(t, room, view, ppl=(), st=None, **p):
    """A set shot: room / view, figures ppl, set kwargs st."""
    _FILM[0].cut(t, 'set', room=room, view=view, set=dict(st or {}), ppl=list(ppl), **p)


def BU(t, who, room, view, st=None, **p):
    """A face close-up over the blurred set (room, view, st); room None = a plain gradient (p['plain'])."""
    if room is None: _FILM[0].cut(t, 'bust', who=who, **p)
    else: _FILM[0].cut(t, 'bust', who=who, bg=(room, view), set=dict(st or {}), **p)


def RIN(t, kw, who='adam', motion=None, **p):
    """Review B1 (the radio jumped between Adam's hand and a table): the radio insert while ADAM HOLDS IT: no table,
    his gloved hand gripping it from below (the cast's hand, his sleeve), radio and hand bobbing together."""
    t_ = t
    bob = lambda u: (5.0 * math.sin(u * 2.1 + 0.4), 4.0 * math.sin(u * 1.6), 0.0, 0.0)
    mot = (lambda u: tuple(a_ + b_ for a_, b_ in zip(bob(u), motion(u)))) if motion else bob
    kw_ = (lambda u, f=kw: dict(f(u), held=True)) if callable(kw) else dict(kw or {}, held=True)

    def fn(tt):
        dx, dy, ds, _ = mot(tt - t_)
        x, y = 1135.0, 935.0
        return (960 + dx + (x - 960) * (1 + ds), 540 + dy + (y - 540) * (1 + ds), 166.0, 1.0, 600.0 * (1 + ds))
    p.setdefault('c', dict(mv='hold'))
    return IN(t, 'radio', kw_, motion=mot, hands=[dict(who=who, fn=fn, size=600.0, shape='grip', side=1, sleeve_from=(1480, 1700))], **p)


def IN(t, name, kw=None, **p):
    _FILM[0].cut(t, 'ins', name=name, kw=kw, **p)


def RULE(t, n): _FILM[0].cut(t, 'rule', n=n)


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


def wavef(t0, t1, side=1, slow=True): return lambda a, s: a.wave(t0, t1, side, slow=slow)


def radio(t0, t1, side=1): return lambda a, s: a.radio_to_mouth(t0, t1, side)


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


# ---------------------------------------------------------------- the cold: breath, mittens, the cone (drawn on the actor)
def puffs(k=1.0, per=3.2):
    """Visible cold breath out of the mouth, a soft cloud every `per` s (never on him)."""
    def fx(pen, t, a):
        hh = a.height
        try:
            mx, my = a.where(t, 'mouth')
            hx, hy = a.where(t, 'head')
        except Exception:
            return
        dx = (mx - hx) * 3.0
        for j in range(2):
            ph = ((t + a.seed * 0.37) / per + j * 0.5) % 1.0
            if ph > 0.55: continue
            u = ph / 0.55
            r = hh * (0.012 + 0.04 * u)
            x = mx + dx * u * 1.6 + hh * 0.01 * math.sin(t + j)
            y = my - hh * (0.006 + 0.04 * u)
            al = 150 * k * (1 - u) * clamp(u * 5.0)
            pen.fill(oval(x, y, r * 1.2, r * 0.8), '#eef4ff', al, blur=max(1.0, r * 0.45))
    return fx


def mitts(c=ST.IC_LINA_MITTEN):                  # Lina's yellow mittens (the same pair that ends up on his string)
    """Lina's mittens on her hands (L134-L173)."""
    def fx(pen, t, a):
        s = a.height * 0.034
        for part in ('hand_l', 'hand_r'):
            try: x, y = a.where(t, part)
            except Exception: continue
            m = rrect(x - s, y - s * 0.9, 2 * s, 2.2 * s, s * 0.9)
            pen.fill(m, c); pen.line(m, max(1.0, s * 0.12), '#1a1418')
            pen.fill(rect(x - s * 1.05, y - s * 1.1, 2.1 * s, s * 0.5), '#f4f0f2')
    return fx


CONE_UP = (1092, 700)                     # Lina on couch_right (couch3q): her hands hold the cone up at her chin (design px)


def cone_fx(part='hand_r', s=1.0, t_gone=None):
    """The pink-and-white swirl cone held in a hand (wafer down, the swirl up), steaming with cold."""
    def fx(pen, t, a):
        if t_gone is not None and t >= t_gone: return
        try: x, y = a.where(t, part)
        except Exception: return
        k = a.height * 0.05 * s
        y0 = y - k * 0.25
        wafer = poly([(x - k * 0.55, y0), (x + k * 0.55, y0), (x, y0 + k * 1.7)])
        pen.fill(wafer, '#d9a86a'); pen.line(wafer, max(1.0, k * 0.06), '#1a1418')
        for j in range(3):
            pen.seg((x - k * 0.45 + j * k * 0.3, y0 + k * 0.1), (x - k * 0.1 + j * k * 0.2, y0 + k * 1.2), max(0.8, k * 0.04), '#a8743a')
        for j, (c_, r_) in enumerate((('#f4b4cf', 0.62), ('#ffffff', 0.5), ('#e58fb4', 0.38), ('#ffffff', 0.24))):
            pen.fill(oval(x, y0 - k * (0.2 + 0.32 * j), k * r_ * 1.05, k * r_ * 0.7), c_)
        for j in range(2):
            u = ((t * 0.6 + j * 0.5) % 1.0)
            pen.fill(oval(x + k * 0.3 * math.sin(t * 2 + j), y0 - k * (1.3 + 1.2 * u), k * (0.25 + 0.3 * u)), '#eef6ff', 90 * (1 - u), blur=k * 0.2)
    return fx


def held_mitten(part, c=ST.IC_LINA_MITTEN, t0=-99.0, t1=None):
    """One of Lina's mittens on his leg tip / in a hand (the pluck, L243)."""
    def fx(pen, t, a):
        if t < t0 or (t1 is not None and t >= t1): return
        try: x, y = a.where(t, part)
        except Exception: return
        s = a.height * 0.045                             # the size of the mitten lying in the snow
        m = rrect(x - s, y, 2 * s, 2.3 * s, s * 0.9)
        pen.fill(m, c); pen.line(m, max(1.0, s * 0.12), '#1a1418')
    return fx


# ---------------------------------------------------------------- Mister Shiver on the sets
def SH(at='truck_vendor', act=None, lean=0.0, light=SH_PINK, clip='truck_window', face=(-1.2, -2.0), nolegs=None, **k):
    """Mister Shiver: in his serving window (feet on the truck floor at truck_vendor), seen only above the sill
    (clip = the sill anchor); leaning out (lean = ws_bend) he is drawn in front of the truck's wall."""
    acts = [pose(-9, None, 0.1, ws_bend=lean, sh_nolegs=(1.0 if clip else 0.0) if nolegs is None else nolegs)]
    if act: acts.append(act)
    d = dict(light=light, act=_A(*acts), clip=clip, talk=False, face=face, breath=False)
    if clip: d['dorder'] = -2.5
    d.update(k)
    return P('shiver', at, **d)


def TF():
    """THE TRANSFORMATION, keyed to the narration: one transform() curve for every cut from L199 to L220, so each shot
    shows the same state at the same moment (waving -> smile past the cheeks -> long white bone -> eyes sink -> red ->
    jaw to the chest -> the uniform splits, legs punch out -> planted on the roof)."""
    return [WD(201, 'and'), E(203), E(207), WD(208, 'and'), WD(208, 'red'), WD(210, 'chest'), WD(216, 'punches'), E(220)]


def tf(a, s): a.transform(TF()[0], TF())


def roof_legs(sp, t_list):
    """Plant his legs on the truck roof (screen points of this set), two per click word."""
    def f(a, s):
        f_, b_ = scr(sp, 'truck_roof_front'), scr(sp, 'truck_roof_back')
        for j, tt in enumerate(t_list):
            tg = {}
            for i in (2 * j, 2 * j + 1):
                u = (i + 0.5) / 8.0
                tg[i] = (lerp(f_[0], b_[0], u), lerp(f_[1], b_[1], u) + 2)
            a.legs_plant(tt, tg, stagger=0.06, dur=0.2)
    return f


def truck_live(sp, xf, y=None, fa=-90.0, win=1.0):
    """His truck gliding (no tire tracks): xf(t) -> plan x along the kerb lane y (heading west, fa -90 = to A)."""
    v = sp.view
    y = ST.IC_TRUCK_A[1] if y is None else y
    o = dict(tod='night', truck=None, truck_win=1.0, truck_open=0.0, mittens=None, lina_mitten=False, truck_heads=0.0, street=1.0,
             porch=0.0, kporch=0.0, porches=None, win={}, smoke=0.0, walk='buried', kwalk='buried', tracks=None, props=None, plow=None,
             door_open=False, kdoor_open=False, blackout=False, dust=True, no_veil=True)
    main = ST.IcStreet(o)
    amb, steady, var = main.lights(o)
    dep = lambda t: max(0.3, v.d(xf(t), y))
    lay = ST.live_layer('truck_live', v, (xf(0.0), ST.IC_G + 1.5, y), lambda pen, v_, t: ST.draw_parts(pen, v_, ST.ic_truck_parts(xf(t), y, fa)),
                        amb, steady, var)
    lay.depth = dep; lay.order = lambda t: v.d(xf(t), y)
    glow = Layer(dep, lambda pen, t: ST.ic_truck_emit(pen, v, xf(t), y, fa, win=win, t=t), 'truck_glow', blur=None)
    glow.order = lambda t: v.d(xf(t), y) - 0.02
    return [lay, glow]


def glide(t0, t1, x0, x1):
    """Plan x of the gliding truck: eases in and settles (it never skids: no tracks)."""
    return lambda t: lerp(x0, x1, ease_out_cubic(clamp((t - t0) / max(0.1, t1 - t0))))


def frost_air(n=60, seed=4):
    """Frozen air: fine ice glints drifting in front of a close-up (his breath shows nothing at all)."""
    rng = np.random.default_rng(seed)
    pts = [(rng.uniform(0, 1920), rng.uniform(0, 1080), rng.uniform(1.0, 3.2), rng.uniform(0.2, 1.0)) for _ in range(n)]

    def draw(pen, t):
        for (x, y, r, s_) in pts:
            xx = (x + 22 * t * s_) % 1960 - 20; yy = (y + 9 * t * s_ + 8 * math.sin(t * s_ + x)) % 1100 - 10
            pen.fill(oval(xx, yy, r), '#eef6ff', 170 * s_)
    return Layer(0.9, draw, 'frost_air', blur=0)


def plane_layer(sp, at, draw, name='plane', front=0.02, depth=None):
    """A layer drawn in the set's screen space at the depth of plan point `at` (a hand behind a window, a fog bloom, a
    shadow on the curtain)."""
    s = spot_of(sp, at)
    d = depth if depth is not None else s.depth
    lay = Layer(d, draw, name, ref_depth=d, blur=None)
    lay.order = sp.order_at(s.X, s.Yp) - front
    return lay


def sill_cone(sp, at='sill_out'):
    """The free cone standing on the OUTSIDE kitchen sill (drawn at the sill's plan point, behind the glass: the set's own
    sill cone draws as a thin bar, see W/handoff/requests.md)."""
    s_ = spot_of(sp, at)
    x, y = scr(sp, at)
    k = 0.11 * s_.ppm
    x += 0.38 * s_.ppm                                   # right of the tap, in the lower right pane
    return plane_layer(sp, at, lambda pen, t: _cone_screen(pen, x, y - 1.7 * k, k, t), 'sill_cone', front=-0.01)


def NEST_BACK(look_t=None, adam_act=None, lina_expr='sleepy', adam_expr='fear'):
    """Review M2 (the kids vanished from the couch in the window wides): both kids on the couch, seen from behind (its
    back to the window), under the one blanket; they look at the window from look_t."""
    la = [lk(look_t, 'curtain_crack', dur=0.4, body=0.3)] if look_t is not None else []
    return [adam('couch_mid', who='adam', kind='seat', expr=adam_expr, act=_A(*(la + ([adam_act] if adam_act else [])))),
            lina('couch_right', who='lina', kind='seat', expr=lina_expr, seed=2, extras=[mitts()], act=_A(*la))]


def nest_blanket(ids=('adam', 'lina'), c='#3b3150', c2='#56496e', empty=0.0, t_in=None, under=()):
    """acts: ONE blanket over the kids on the couch (L135+): a quilt laid over them from the chest to the knees, drawn in
    front of their figures and following their bodies (breathing, leaning); empty > 0 keeps a hollow on the right where
    Lina slept (L173: the blanket beside me is cold)."""
    def acts(A, sh, sp):
        who = [k for k in ids if k in A]
        if not who: return []
        lays = [sh.I[k]['layer'] for k in sh.I if k in who or any(k in ALIAS.get(w, ()) for w in who)]
        def draw(pen, t):
            if t_in is not None and t < t_in: return       # wrapped on at t_in (Adam's hands arrive)
            pts = []
            for k in who:
                a = A[k]
                try:
                    cx, cy = a.where(t, 'chest'); hx, hy = a.where(t, 'hip'); fx, fy = a.where(t, 'foot_l')
                except Exception:
                    continue
                w_ = 0.16 * a.height
                pts.append((cx, cy + 0.03 * a.height, hx, hy, lerp(hy, fy, 0.55), w_))
            if not pts: return
            pts.sort()
            xl = pts[0][0] - pts[0][5] * 1.1; xr = pts[-1][0] + pts[-1][5] * (1.1 + 2.2 * empty)
            top = [(xl, pts[0][1] + 10)] + [(p_[0], p_[1]) for p_ in pts] + [(xr, pts[-1][1] + 14 + 30 * empty)]
            bot = max(p_[4] for p_ in pts)
            path = smooth(top + [(xr + 10, bot), (xl - 10, bot + 6)], True)
            pen.fill(moved(path, 0, 12), '#05040a', 90, blur=14)
            pen.fill(path, c); pen.texture(path, 'fabric', 0.35, 'overlay', 0.6)
            for j in range(1, 5):                                     # quilt seams
                x_ = lerp(xl, xr, j / 5.0)
                pen.seg((x_, min(p_[1] for p_ in pts) + 20), (x_ + 6, bot - 4), 1.6, c2, 150)
            pen.seg((xl + 10, lerp(top[1][1], bot, 0.5)), (xr - 10, lerp(top[-2][1], bot, 0.5)), 1.6, c2, 150)
            pen.line(path, 2.2, '#140f1c', 200)
        dd = lambda t: min((l_.depth(t) if callable(l_.depth) else l_.depth) for l_ in lays) - 0.01
        l0 = lays[0]
        lay = Layer(dd(sh.t0), draw, 'blanket', ref_depth=getattr(l0, 'ref_depth', None), blur=None)
        lay.depth = dd
        if getattr(l0, 'ref_depth', None) is not None: lay.ref_depth = l0.ref_depth   # same design space as the figures
        o_ = [l_.order for l_ in lays]
        lay.order = lambda t: min((o(t) if callable(o) else o) for o in o_) - 0.02
        uo = [sh.I[k]['layer'].order for k in under if k in sh.I]
        if uo:                                              # stay behind these nearer figures (Adam kneeling in front)
            ov = lambda o, t: o(t) if callable(o) else o
            lay.order = lambda t: 0.5 * (min(ov(o, t) for o in o_) + max(ov(o, t) for o in uo))
            ud = [sh.I[k]['layer'] for k in under if k in sh.I]
            lay.depth = lambda t: 0.5 * (dd(t) + 0.01 + max(ov(l_.depth, t) for l_ in ud))
        return [lay]
    return acts


def leg_shadow(sp, t0, t1, at='curtain_crack'):
    """Glimpse 3: the shadow of long jointed legs sliding across the shut curtains on the pink light (L153-154)."""
    s = spot_of(sp, at)
    k = s.ppm

    def draw(pen, t):
        u = clamp((t - t0) / max(0.1, t1 - t0))
        if u <= 0 or u >= 1: return
        a = math.sin(u * math.pi)
        x0 = s.x + (u - 0.5) * 3.2 * k
        pen.cv.save(); pen.cv.clipRect(skia.Rect.MakeLTRB(470, 280, 1285, 790), skia.ClipOp.kIntersect, True)   # the lit curtain only (window view)
        sy = s.y + 0.7 * k
        for i in range(4):
            bx = x0 + (i - 1.5) * 0.42 * k
            ph = t * 5.0 + i * 1.7
            p1 = (bx, sy - 0.9 * k)
            p2 = (bx + 0.35 * k + 0.08 * k * math.sin(ph), sy - 1.45 * k)
            p3 = (bx + 0.55 * k, sy + 0.15 * k + 0.05 * k * math.sin(ph))
            p4 = (bx + 0.62 * k, sy + 0.95 * k)
            pen.line(poly([p1, p2, p3, p4], False), 0.065 * k, '#1a0a14', 215 * a)
            pen.fill(oval(p2[0], p2[1], 0.04 * k), '#1a0a14', 200 * a)
            pen.fill(oval(p3[0], p3[1], 0.035 * k), '#1a0a14', 200 * a)
        pen.fill(oval(x0, sy - 0.85 * k, 0.4 * k, 0.28 * k), '#1a0a14', 170 * a, blur=0.06 * k)
        pen.cv.restore()
    return plane_layer(sp, at, draw, 'leg_shadow', front=0.03)            # ON the shut curtain (it was hidden behind it)


def window_hand(sp, at, t0, t1, who='kessler', fog=None):
    """An old pale hand rising slowly behind his window glass (L57-58), and a breath fog blooming on the inside (L59)."""
    s = spot_of(sp, at)
    k = s.ppm

    def draw(pen, t):
        cv = pen.cv
        cv.save(); cv.clipPath(rrect(s.x - 0.66 * k, s.y - 0.62 * k, 1.32 * k, 1.12 * k, 0.03 * k), skia.ClipOp.kIntersect, True)
        u = ease_in_out(clamp((t - t0) / max(0.1, t1 - t0)))
        if u > 0:
            x, y = s.x - 0.05 * k, s.y + 0.55 * k - 0.62 * k * u
            hero_hand(pen, who, x, y, 0.2 * k, 'open', 180.0, 1, (x + 0.08 * k, y + 0.8 * k), dict(NIGHT, key=-0.5), 0.0, t)
            pen.fill(rect(s.x - 0.7 * k, s.y - 0.7 * k, 1.4 * k, 1.3 * k), '#0c1424', 120)
        if fog is not None:
            f = ease_out_cubic(clamp((t - fog) / 1.2))
            if f > 0:
                pen.fill(oval(s.x + 0.12 * k, s.y - 0.05 * k, 0.32 * k * f, 0.24 * k * f), '#dfe8f6', 170 * f, blur=0.08 * k)
        cv.restore()
    return plane_layer(sp, at, draw, 'window_hand', front=0.05)


# ---------------------------------------------------------------- figures on the plan (shortcuts)
def kid(who, at, **k):
    return P(who, at, **k)


def adam(at, **k): return P(k.pop('who', 'adam_in'), at, **k)


def lina(at, **k): return P(k.pop('who', 'lina_pj'), at, **k)


# ==================================================================================================== COLD OPEN (0-8)
def plan_open(F):
    C = F.cut
    # 0 "If the ice cream truck plays its song in the middle of winter... don't go outside."
    gx = glide(T(0), W(0, "don't") + 0.6, 34.0, 12.0)
    S(T(0), 'street', 'lane', st=dict(ST_NONE, truck=None), acts=lambda A, sh, sp: truck_live(sp, gx),
      cam=cm((-6.0, -11.6, 0.6), (14.0, -9.55, 0.9), 1900, sy=640), c=Z(1.0, 0.03),     # (owner's-eyes: open close on the truck gliding in, long lens down the lane)
      sfx=[(T(0), 'truck_glide', -8, 0.3, 'outside', dict(dur=4.0)), (T(0), 'cold_night', -10, 0, 'outside', dict(dur=5.0))])
    S(W(0, "don't"), 'hall', 'doorclose', st=dict(HALL_A, hall=0.25, lamp=0.0, pink=1.0), c=Z(1.0, 0.03))
    # 1 "If he leaves a free one on your porch... don't touch it."
    IN(T(1), 'doormat', dict(wrapper=True), c=dict(mv='push', rate=0.04), sfx=[(T(1) + 0.1, 'cone_set', -10, 0, 'close')])
    td = WD(1, "don't")
    IN(W(1, "don't"), 'doormat', dict(wrapper=True), c=dict(mv='push', f=1.25, rate=0.03),
       hands=[dict(who='lina_pj', fn=slide(td - 0.3, td + 0.45, (1900, 760), (1410, 700), 118, 108,     # (review: from the right, stops in the air beside the cone, never on it)
                                           extra=lambda t, r: (r[0] + 320 * ease_in_out(clamp((t - td - 0.75) / 0.45)), r[1] + 30 * ease_in_out(clamp((t - td - 0.75) / 0.45)), r[2], r[3])),
                   size=260, shape='open', side=-1, sleeve_from=(2150, 820))])
    # 2 "And if Mom knocks... and her breath doesn't show... don't open the door."
    S(T(2), 'hall', 'doorclose', st=dict(HALL_A, hall=0.3, lamp=0.0, pink=1.0),       # her shadow on the frosted glass (drawn over the door, faint)
      ppl=[P('shiver_mom', (-2.1, -0.45, 0.0), face=(-2.1, 2.0), sil=0.5, sil_rim='#ff9ec8', sil_rim_a=0.25, dorder=-6.0,
             light=PINK, talk=False, breath=False, act=_A(lambda a, s: a.knock(T(2) + 0.12, 3, 0.3)))],
      sfx=[(T(2) + 0.12 + 0.3 * k, 'door_tap', -2 + 2 * (k == 2), 0, 'inside', dict(kind='knock', n=1, index=k)) for k in range(3)], c=Z(1.0, 0.02))
    BU(W(2, 'breath'), 'shiver_mom', 'hall', 'doorclose', dict(HALL_A, hall=0.2, lamp=0.0), cx=960, cy=560, scale=0.7, light=PINK_D, cold=False,
       act=_A(lk(T(2) - 1, (960, 700))), c=BZ(0.025), post=dict(blur=0))
    C(W(2, "don't"), 'set', room='hall', view='door', set=dict(HALL_A, hall=0.55, lamp=0.0, pink=1.0),       # (review: the deadbolt hit reads)
      ppl=[adam('door_in', face=(-1.74, 0.0), expr='stern_afraid', act=_A(reach(W(2, "don't") + 0.05, 1, 'lock', dur=0.3, shape='pinch')))],
      sfx=[(F.w(2, 'door') + 0.0, 'deadbolt', 0, -0.2, 'inside', dict(kind='throw'))], c=Z(1.0, 0.02, hit=[F.w(2, 'door')]))
    # 3 S "Who's cold? Who wants a free one? Just come to the window!"  (his voice: no lip sync; he is busy at the window)
    stw = dict(truck_open=1.0)
    BU(T(3), 'shiver', 'street', 'window_close', stw, cx=960, cy=600, scale=0.78, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, ws_bend=0.18), lambda a, s: a.slow_wave(s.t0, s.t1 + 1, 1), lk(T(3) + 0.3, (1500, 600), dur=0.25, snap=True),
              lk(W(3, 'who', 1) + 0.1, (500, 640), dur=0.25, snap=True), lk(W(3, 'just') - 0.2, (960, 560), dur=0.2, snap=True)),
       c=BZ(0.03), sfx=[(T(3) - 0.05, 'serving_window', -6, 0, 'outside')])
    BU(W(3, 'just'), 'shiver', 'street', 'window_close', stw, cx=960, cy=640, scale=1.15, light=SH_PINK, sill=1015.0,
       act=_A(pose(-9, None, 0.1, ws_bend=0.3), lambda a, s: a.reach_far(s.t0 + 0.05, 1, (980, 900), dur=0.8, z=80.0)), c=BZ(0.04))
    # 4 "That's Mister Shiver."
    S(T(4), 'street', 'truck', st=ST_A, ppl=[SH(lean=0.22, act=_A(lambda a, s: a.slow_wave(s.t0, s.t1 + 1, 1), lk(T(4), (960, 760))))],
      tags=[tagc(WD(4, 'mister'), 'MISTER SHIVER', 'red', 960, 170, 2.0)], c=Z(1.5, 0.03, 900, 470))
    # 5-8
    S(T(5), 'street', 'house', st=ST_A, c=Z(1.3, 0.03, 820, 540),
      tags=[tagc(WD(5, 'birch'), 'BIRCH LANE', 'pill', 960, 170, 2.0)])
    S(T(6), 'street', 'lane_e', st=dict(ST_NONE, win=dict(liv=0.9, kitchen=0.6, his=0.0)), c=Z(1.1, 0.03))
    IN(T(7), 'rules', dict(show=7, door='ours'), c=dict(mv='push', f=1.05, rate=0.04))
    S(T(8), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.0)), c=Z(1.6, 0.04, 860, 500))


# ==================================================================================================== LARKFIELD, DAD, KESSLER, 1958 (9-39)
def plan_setup(F):
    t9 = T(9)
    IN(t9, 'card', lambda u: dict(time_='Larkfield.', temp='Minus thirty-one.' if u + t9 >= F.t(10) - 0.05 else None,
                                  sub='Sunrise: seven fifty-one.' if u + t9 >= F.t(11) - 0.05 else None), c=dict(mv='push', rate=0.015))
    # 12 Mom's on night shift
    S(T(12), 'kitchen', 'wide', st=KIT_ON, ppl=[adam((-5.2, 3.0, 0.0), face='fridge_photo', expr='wistful',
                                                     act=_A(lk(T(12), 'fridge_photo'), reach(T(12) + 0.5, 1, 'fridge_photo', dur=0.7, shape='flat', contact='palm')))],
      c=Z(1.35, 0.02, 1150, 560))
    # 13 Dad plows snow all night
    S(T(13), 'street', 'plow', st=dict(truck=None, plow=dict(x=lambda t: -12.0 + 4.5 * clamp(t - T(13), 0.0, 6.0), y=-11.0, dir=1, beacon=1.0)), c=Z(1.0, 0.02),
      sfx=[(T(13), 'plow_pass', -6, 0, 'outside', dict(dur=2.5))])
    # 14 He handed me a radio
    tx = WD(14, 'radio') - 0.05
    S(T(14), 'hall', 'door', st=HALL_ON, cam=cm((-2.1, 4.6, 1.35), (-2.05, 0.9, 1.0), 900),
      ppl=[P('dad', (-2.35, 0.95, 0.0), face=(-1.75, 2.1), expr='warm_smile', id='dad',
             act=_A(reach(T(14), 1, ('adam', 'hand_l'), t1=tx + 0.25, dur=0.45, prop='walkie'))),
           adam((-1.75, 2.15, 0.0), face=(-2.35, 0.95), expr='neutral', id='adam',
                act=_A(lk(T(14), ('dad', 'head')), reach(tx - 0.1, -1, ('dad', 'hand_r'), dur=0.3, prop='walkie'),
                       lambda a, s: a.reach_to(tx + 0.35, -1, (a, 'chest'), dur=0.4, prop='walkie')))],
      c=Z(1.05, 0.02))
    # 15 D "Channel three. Say 'over' when you're done. Over."
    RIN(T(15), dict(talk=0.0, static=0.0), 'adam_in', c=dict(mv='push', rate=0.03))
    BU(W(15, 'say'), 'dad', 'hall', 'door', HALL_ON, cx=1000, cy=600, scale=0.8, turn=-0.3, light=LAMP, expr='warm_smile',
       act=_A(radio(WD(15, 'over', 1) - 0.25, E(15) + 0.2, 1), lk(W(15, 'say'), (760, 700))), c=BZ(0.015))
    # 16 D "My orange light passes every hour. Need a grown-up? Mr. Kessler's right across the street."
    BU(T(16), 'dad', 'hall', 'door', HALL_ON, cx=900, cy=600, scale=0.85, turn=0.25, light=LAMP, expr='kind_smile',
       act=_A(lk(T(16), (1300, 700)), lk(WD(16, 'kessler') - 0.6, (1700, 560), dur=0.4)), c=BZ(0.015))
    S(W(16, 'kessler'), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.12)), c=Z(1.4, 0.03, 860, 520))
    # 17 Nobody goes to Old Man Kessler's.
    BU(T(17), 'adam_in', 'living', 'window', LIV_EVE, cx=980, cy=620, scale=0.85, turn=-0.4, light=LAMP_R, expr='suspicious',
       act=_A(lk(T(17), (300, 450), dur=0.4)), c=BZ(0.02))
    # 18-19 Lina
    S(T(18), 'living', 'couch3q', st=LIV_EVE, ppl=[lina('couch_right', kind='seat', expr='kid_grin', act=_A(lk(T(18), (1300, 700))))],
      tags=[tagc(WD(18, 'lina'), 'LINA, 6', 'pill', 960, 170, 2.0)], c=Z(1.5, 0.02, 1000, 650))
    BU(T(19), 'lina_pj', 'living', 'couch3q', LIV_EVE, cx=960, cy=620, scale=0.9, light=LAMP, expr='kid_grin', act=_A(tilt(T(19) + 0.2, 10.0)), c=BZ(0.02))
    tm = WD(19, 'mittens')
    BU(W(19, 'mittens'), 'lina_pj', 'living', 'couch3q', LIV_EVE, cx=1000, cy=640, scale=0.95, light=LAMP, expr='stern', act=_A(shake_head(tm, 3)),
       hands=[dict(who='lina_pj', fn=slide(tm, tm + 0.5, (900, 1000), (420, 1300), 20, 70), size=140, shape='fist', side=1, sleeve_from=(1000, 1400))],
       c=BZ(0.02))
    # 20-23 Mr. Kessler's shovel at six; every walk clear; "the town does it"
    S(T(20), 'street', 'house', st=dict(truck=None, win=dict(liv=0.0, kitchen=0.0), walk='shoveled'),
      ppl=[P('kessler_am', (-4.0, -7.3, FOOT), face=(-3.0, -7.3), sil=0.85, light=NIGHT, act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.25)))],
      c=Z(1.9, 0.02, 760, 600), sfx=[(T(20) + 0.6 + 1.1 * k, 'shovel_scrape', -10, -0.2, 'outside') for k in range(3)])
    S(T(21), 'street', 'door', st=dict(truck=None, walk='shoveled'), c=Z(1.2, 0.03, 960, 760),
      sfx=[(WD(21, 'scrape'), 'shovel_scrape', -2, 0, 'outside')])
    S(T(22), 'morning', 'lane', st={}, c=Z(1.05, 0.02), era='morning')
    BU(T(23), 'dad', 'morning', 'house', {}, cx=960, cy=600, scale=0.82, light=MORNING, expr='warm_smile', era='morning',
       act=_A(tilt(T(23) + 0.3, 9.0, 1.4)), c=BZ(0.015))
    # 24-25 the rules taped up; signed W.K.
    tk = T(24) + 0.6
    IN(T(24), 'rules', dict(show=7, door='ours'), c=dict(mv='push', f=1.0, rate=0.02),
       hands=[dict(who='kessler', fn=slide(tk - 0.5, tk, (1900, 120), (1540, 160), 125, 135,
                                           extra=lambda t, r: (r[0] - 8 * math.sin(clamp((t - tk) / 0.6) * math.pi), r[1], r[2], r[3] * (1 - clamp((t - tk - 1.6) / 0.4)))),
                   size=300, shape='flat', side=-1, sleeve_from=(2200, -200))], sfx=[(tk, 'tape_press', -8, 0.3, 'close')])
    IN(T(25), 'rules', dict(show=7, door='ours'), motion=lambda u: (-560 * ease_in_out(clamp(u / 0.9)), -400 * ease_in_out(clamp(u / 0.9)),
                                                                    0.9 * ease_in_out(clamp(u / 0.9)), 0.0), c=dict(mv='hold'))
    # 26-30 1958 (memory, sepia)
    def walk58(who, t0, t1, a0, a1, seed=0, expr='neutral', **k):
        return P(who, a0, path=[(t0, a0), (t1, a1)], surface='snow', expr=expr, seed=seed, light=SEPIA, **k)
    S(T(26), 'y58', 'kout', st={}, ppl=[walk58('walter58', T(26), E(26) + 0.4, (1.4, -21.6, FOOT), (0.2, -18.8, FOOT), expr='tempted')], era='memory',
      tags=[tagc(WD(26, '1958'), '1958', 'pill', 960, 170, 2.2)], c=Z(1.1, 0.02), cold=True)
    S(T(27), 'y58', 'kout', st={}, ppl=[walk58('walter58', T(27) - 2, T(27) + 1.0, (0.4, -19.0, FOOT), (-0.6, -17.7, FOOT)),
                                         walk58('benny', T(27), E(27) + 0.3, (1.4, -22.2, FOOT), (0.9, -20.2, FOOT), seed=3, expr='little_girl')],
      era='memory', c=Z(1.2, 0.02), cold=True)
    S(T(28), 'y58', 'kporch', st={}, ppl=[walk58('walter58', T(28), E(28) + 0.2, (1.2, -19.6, FOOT), (1.4, -22.6, -0.17), expr='terror', run=True)],
      era='memory', c=Z(1.1, 0.02), cold=True)
    S(T(29), 'y58', 'kout', st={}, era='memory', c=Z(1.25, 0.03, 900, 600))
    S(T(30), 'y58', 'mitten', st={}, era='memory', grade='ic_1958_red', c=Z(1.9, 0.03, 912, 380))
    # 31 Walter never told anyone how he got away.  (old Mr. Kessler now, in his dark window)
    BU(T(31), 'kessler', 'street', 'kessler', dict(truck=None, win=dict(his=0.1)), cx=960, cy=600, scale=0.8, light=dict(NIGHT, key=-0.4), expr='haunted',
       act=_A(lk(T(31), (300, 640))), c=BZ(0.015))
    S(T(32), 'street', 'lane', st=dict(truck=None), c=Z(1.15, 0.02))
    IN(T(33), 'rules', dict(show=7, hl=7, door='ours'), motion=lambda u: (0.0, -260.0, 0.35, 0.0), c=dict(mv='push', rate=0.02))
    # 34 Yesterday, the rules went up.
    S(T(34), 'hall', 'door', st=HALL_ON, ppl=[adam('door_in', face='rules', expr='focused', act=_A(lk(T(34), 'rules')))], c=Z(1.4, 0.02, 960, 600))
    # 35-37 this morning: no scrape, our walk buried, no smoke
    S(T(35), 'street', 'door', st=dict(truck=None, walk='buried', porch=0.6), ppl=[kid('adam', 'porch_out', face=(-2.1, -8.0), expr='suspicious',
                                                                                     act=_A(tilt(T(35) + 0.3, 12.0)))], cold=True, c=Z(1.1, 0.02))
    S(T(36), 'street', 'yard', st=dict(truck=None, walk='buried'), ppl=[kid('adam', (-2.1, -4.0, FOOT - 0.22), face=(-2.1, -7.0), expr='sad',
                                                                            act=_A(lk(T(36), (-2.1, -5.0, FOOT)), lambda a, s: a.set(-9, None, 0.1, lean=0.15)))],
      cold=True, c=Z(2.6, 0.02, 520, 600))
    S(T(37), 'street', 'kessler', st=dict(truck=None, smoke=0.0), c=Z(1.2, 0.0, 900, 520, x1=1000, y1=420, f1=2.2))
    # 38 The plow pulled away.  39 ...under the radio static... three slow notes.
    S(T(38), 'street', 'plow', st=dict(truck=None, plow=dict(x=lambda t: 0.0 + 6.0 * clamp(t - T(38), 0.0, 6.0), y=-11.0, dir=1, beacon=1.0)), c=Z(1.0, 0.01),
      sfx=[(T(38), 'plow_pass', -8, 0.4, 'outside', dict(dur=2.0))])
    S(T(39), 'living', 'radio', st=dict(LIV_EVE, lamp=0.7), c=Z(1.0, 0.03), sfx=[(T(39), 'radio_static', -8, 0, 'close', dict(dur=2.0))])
    IN(W(39, 'three'), 'radio', lambda u: dict(talk=0.5 + 0.5 * math.sin(u * 4.0), static=0.4), c=dict(mv='push', f=1.2, rate=0.04),
       music=[(WD(39, 'three'), 'jingle', 0.4, 2.6, dict(version='three'))])


# ==================================================================================================== RULE 1: THE SONG, THE CURTAINS, THE TRUCK (40-86)
def plan_rule1(F):
    RULE(T(40), 1)
    IN(T(43), 'card', lambda u: dict(time_='Eleven-oh-two.', temp='Minus thirty-three.' if u + T(43) >= F.t(44) - 0.05 else None), c=dict(mv='push', rate=0.015))
    # 45 Far away... a chime.
    S(T(45), 'street', 'lane', st=dict(truck=None), acts=lambda A, sh, sp: truck_live(sp, lambda t: 60.0, fa=-90.0, win=1.0), c=Z(1.6, 0.03, 1010, 540))
    # 46 D (radio) "Hearing a song out on Elm... in this cold? Over."
    BU(T(46), 'dad', None, None, plain=('#2a1c14', '#0a0706'), cx=960, cy=600, scale=0.85, turn=0.3, expr='focused',
       light=lambda t: dict(BEACON, rim_a=int(70 + 80 * (0.5 + 0.5 * math.sin(t * 8.2)))), act=_A(radio(T(46) - 0.5, E(46) + 0.3, 1), lk(T(46), (1500, 520))),
       c=BZ(0.015))
    # 47-49 Maple. Cedar. Closer.
    BU(T(47), 'lina_pj', 'living', 'couch3q', LIV_EVE, cx=900, cy=620, scale=0.88, light=LAMP, expr='kid_grin', act=_A(lk(T(47), (200, 500), dur=0.3)), c=BZ(0.02))
    BU(T(48), 'adam_in', 'living', 'couch3q', LIV_EVE, cx=1040, cy=620, scale=0.88, light=LAMP_R, expr='nervous', act=_A(lk(T(48), (200, 480), dur=0.25)), c=BZ(0.02))
    S(T(49), 'living', 'window', st=dict(LIV_EVE, pink=lambda t: clamp((t - T(49)) / 1.2) * 0.6), c=Z(1.2, 0.04))
    # 50-52 Sweet. Too slow. Out of tune.  (Lina hums along, swaying)
    BU(T(51) - 0.15, 'lina_pj', 'living', 'couch3q', LIV_EVE, cx=960, cy=620, scale=0.95, light=LAMP, expr='still_smile',
       act=_A(hum(T(51), E(52)), tilt(T(51), 8.0, 1.8)), c=BZ(0.02))
    # 53 a gap where the last note should be
    BU(T(53), 'adam_in', 'living', 'couch3q', LIV_EVE, cx=980, cy=620, scale=0.92, light=LAMP_R, expr='suspicious',
       act=_A(lk(T(53), (300, 460)), tilt(WD(53, 'gap'), -8.0)), c=BZ(0.02), music=[(WD(53, 'gap'), 'silence', 0.0, 0.9)])
    # 54 I close every curtain.
    tc = T(54) + 0.3
    S(T(54), 'living', 'window', st=dict(LIV_EVE, curtains=lambda t: 1.0 - ease_in_out(clamp((t - tc) / 1.0))),
      ppl=[adam((3.3, 0.6, 0.0), face=(3.4, -1.0), act=_A(reach(tc - 0.1, 1, 'curtain_l', t1=tc + 1.0, dur=0.3, shape='grip')))], c=Z(1.0, 0.02),
      sfx=[(tc, 'curtain_yank', -10, 0, 'inside', dict(soft=True))])
    # 55-56 Lina waves at Kessler's dark window.  Like every night.
    S(T(55), 'living', 'window', st=dict(LIV_SHUT, curtains=0.18), ppl=[lina((3.5, 0.45, 0.0), face=(3.4, -2.0), act=_A(wavef(T(55) + 0.4, E(56) + 1, 1)))],
      c=Z(1.2, 0.02, 940, 620))
    S(W(55, 'kessler'), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.0)), c=Z(2.0, 0.02, 860, 520))
    BU(T(56), 'lina_pj', 'living', 'window', dict(LIV_SHUT, curtains=0.18), cx=960, cy=620, scale=0.9, turn=0.2, light=NIGHT, expr='warm_smile',
       act=_A(wavef(T(56) - 0.5, E(56) + 1, 1), lk(T(56), (960, 300))), c=BZ(0.02))
    # 57-60 A hand lifts. Slowly. And a small cloud of breath fogs his glass. From the inside.
    kc = cm((4.3, -17.6, 1.5), (4.3, -23.98, 1.5), 1500)
    S(T(57), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.05)), cam=kc,
      acts=lambda A, sh, sp: [window_hand(sp, 'kwindow', T(57) + 0.2, E(58), fog=WD(59, 'cloud'))], c=Z(1.0, 0.015))
    S(W(59, 'fogs'), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.05)), cam=cm((4.3, -21.0, 1.5), (4.3, -23.98, 1.5), 1500),
      acts=lambda A, sh, sp: [window_hand(sp, 'kwindow', T(57) + 0.2, E(58), fog=WD(59, 'fogs') - 0.3)], c=Z(1.0, 0.02))
    BU(T(60), 'adam_in', 'living', 'window', dict(LIV_SHUT, curtains=0.18), cx=1000, cy=620, scale=0.9, turn=-0.3, light=NIGHT_L, expr='stern_afraid',
       act=_A(lk(T(60), (600, 420))), c=BZ(0.02))
    # 61-62 "Old people like it cold," I say.
    S(T(61), 'living', 'window', st=dict(LIV_SHUT, curtains=0.18),
      ppl=[adam((3.0, 0.75, 0.0), face=(3.5, 0.45), expr='calm_firm', id='adam', act=_A(lk(T(61), ('lina', 'head')), reach(E(61) - 0.2, 1, ('lina', 'shoulder_r'), dur=0.4))),
           lina((3.5, 0.45, 0.0), face=(3.4, -2.0), id='lina', act=_A(lk(E(61) - 0.1, ('adam', 'head'), dur=0.4)))], c=Z(1.15, 0.02, 920, 600))
    # 63 Lina sneaks back.  64 She leaves the curtain open a crack.
    S(T(63), 'living', 'wide', st=LIV_SHUT, ppl=[lina((2.9, 2.9, 0.0), path=[(T(63), (2.9, 2.9, 0.0)), (T(63) + 0.35 * (E(63) - T(63)), (2.05, 2.45, 0.0)), (T(63) + 0.7 * (E(63) - T(63)), (2.1, 0.95, 0.0)), (E(63) - 0.05, (3.4, 0.55, 0.0))], surface='inside_quiet',
                                                      expr='kid_grin')], c=Z(1.15, 0.02, 900, 580))
    tcr = T(64) + 0.5
    S(T(64), 'living', 'window', st=dict(LIV_SHUT, curtains=lambda t: 0.075 * ease_in_out(clamp((t - tcr) / 0.6))),
      ppl=[lina((3.45, 0.5, 0.0), face=(3.4, -2.0), act=_A(reach(tcr - 0.2, 1, 'curtain_crack', t1=tcr + 0.9, dur=0.3, shape='pinch')))], c=Z(1.9, 0.02, 860, 520))
    # 65-68 the truck glides in (no tracks); pink and white; the warm pink window; no tire tracks
    g65 = glide(T(65), E(66) + 0.3, 24.0, ST.IC_TRUCK_A[0])
    S(T(65), 'street', 'lane', st=dict(truck=None, win=dict(liv=0.6)), acts=lambda A, sh, sp: truck_live(sp, g65), c=Z(1.2, 0.02, 900, 560),
      sfx=[(T(65), 'truck_glide', -4, 0.2, 'outside', dict(dur=2.5))], music=[(T(65), 'jingle', 0.45, round(WD(84, 'stops') + 0.25 - T(65), 2), dict(version='outside', loop=True))])
    S(T(66), 'street', 'truck', st=dict(truck=None, win=dict(liv=0.6)), acts=lambda A, sh, sp: truck_live(sp, g65), c=Z(1.0, 0.02))    # (review: it glides INTO frame and stops)
    S(T(67), 'street', 'window_close', st=dict(truck='A'), c=Z(1.0, 0.03))
    S(T(68), 'street', 'lane', st=ST_A, c=Z(1.4, 0.03, 1000, 600))
    # 69 He leans out.
    S(T(69), 'street', 'truck', st=ST_A, ppl=[SH(act=_A(pose(T(69), None, 0.6, ws_bend=0.28), lk(T(69), (960, 820))))], c=Z(2.8, 0.02, 925, 300, free=True),
      sfx=[(T(69) + 0.1, 'serving_window', -8, 0, 'outside')])
    # 70-73 Bald. Chalk-white. Tiny blue eyes. A smile too wide, front teeth sticking out.
    wc = dict(truck_open=1.0)
    BU(T(70), 'shiver', 'street', 'window_close', wc, cx=960, cy=420, scale=0.9, light=SH_PINK, act=_A(pose(-9, None, 0.1, ws_bend=0.2, h_tilt=-8.0),
       lk(T(70), (1300, 900), dur=0.3)), c=BZ(0.03), face_fix=False)
    BU(T(71), 'shiver', 'street', 'window_close', wc, cx=1000, cy=600, scale=1.1, turn=-0.2, light=SH_PINK, act=_A(lk(T(71), (700, 600), dur=0.2, snap=True)), c=BZ(0.03))
    BU(T(72), 'shiver', 'street', 'window_close', wc, cx=960, cy=820, scale=2.2, light=SH_PINK,
       act=_A(lk(T(72), (500, 560), dur=0.1, snap=True), lk(T(72) + 0.45, (1400, 560), dur=0.1, snap=True)), c=BZ(0.02))
    BU(T(73), 'shiver', 'street', 'window_close', wc, cx=960, cy=360, scale=1.9, light=SH_PINK,
       act=_A(lk(T(73), (960, 700)), lambda a, s: a.set(T(73) + 0.3, None, 1.2, sh_smile=0.12)), c=BZ(0.02), face_fix=False)
    # 74-76 the mittens
    IN(T(74), 'mittens', dict(), motion=lambda u: (300 - 600 * ease_in_out(clamp(u / max(1.0, T(75) - T(74)))), 0.0, 0.08, 0.0), c=dict(mv='hold'))   # the pan stays inside the bunting
    IN(T(75), 'mittens', dict(), motion=lambda u: (lambda k: (687 * (1 + 0.9 * k) * k, 150 * (1 + 0.9 * k) * k, 0.9 * k, 0.0))(ease_in_out(clamp(u / 0.8))), c=dict(mv='hold'))   # onto the small red one (plan x 273, y 356)
    IN(T(76), 'mittens', dict(), motion=lambda u: (687 * (2.9 + 0.1 * u), 150 * (2.9 + 0.1 * u), 1.9 + 0.1 * u, 0.0), c=dict(mv='hold'))
    # 77 He looks across at Kessler's window.  78 Like an old friend.
    S(T(77), 'street', 'kessler', st=ST_A, ppl=[SH(face=(-0.5, -2.0), lean=0.15, act=_A(lk(T(77) + 0.3, 'kwindow', dur=0.7, body=0.3)))], c=Z(2.7, 0.02, 1235, 520))
    BU(T(78), 'shiver', 'street', 'window_close', wc, cx=1000, cy=640, scale=1.0, turn=0.35, light=SH_PINK,
       act=_A(lk(T(78), (300, 520)), lambda a, s: a.set(T(78), None, 0.6, sh_smile=0.06), lambda a, s: a.slow_wave(T(78) + 0.2, E(78) + 1, -1)), c=BZ(0.02))
    # 79 Then at Lina, through the crack.  (POV through the crack: his eyes snap to us)
    S(T(79), 'street', 'gap', st=ST_A, ppl=[SH(lean=0.18, act=_A(lk(T(79) - 0.5, 'kwindow'), lk(WD(79, 'lina'), (960, 520), dur=0.1, snap=True)))],
      c=Z(1.9, 0.03, 975, 440))
    BU(T(80), 'shiver', 'street', 'window_close', wc, cx=960, cy=560, scale=1.3, light=SH_PINK,
       act=_A(lk(T(80), (960, 520)), lambda a, s: a.set(T(80) + 0.2, None, 1.3, sh_smile=0.32)), c=BZ(0.035))
    # 81-83 the streetlight flickers; GLIMPSE 1
    fl = ST.ic_flicker(WD(81, 'flickers'), n=4, gap=0.45)
    S(T(81), 'street', 'truck', st=dict(ST_A, street=fl), ppl=[SH(lean=0.2, act=_A(lk(T(81), (960, 800))))], c=Z(2.1, 0.02, 920, 430),
      sfx=[(WD(81, 'flickers'), 'streetlight_buzz', -8, -0.4, 'outside')])
    tg = WD(82, 'flicker') + 0.05
    BU(T(82), 'shiver', 'street', 'window_close', dict(wc, street=ST.ic_flicker(tg - 0.1, n=2, gap=WD(82, 'long') - tg + 0.04)), cx=960, cy=600, scale=1.2,
       light=lambda t: dict(SH_PINK, rim_a=30) if abs(t - tg - 0.07) < 0.1 else SH_PINK,
       act=_A(lambda a, s: a.glimpse(tg, 0.16), lambda a, s: a.set(WD(82, 'long') - 0.06, E(82) + 0.6, 0.05, sh_glim=1.0)),   # 'long and white': the face IS
       post_fn=lambda t: dict(fade=0.55) if abs(t - tg - 0.07) < 0.1 else {}, c=BZ(0.02), sfx=[(tg, 'stinger', -2, 0, None, dict(kind='glimpse'))])
    BU(T(83), 'shiver', 'street', 'window_close', wc, cx=960, cy=760, scale=2.4, light=dict(SH_PINK, rim_a=40),
       act=_A(lambda a, s: a.set(T(83), E(83) - 0.15, 0.04, sh_glim=1.0)), c=BZ(0.01, hit=[T(83) + 0.1]), hit=T(83) + 0.1)
    # 84 The song stops.  85 Right outside our house.  86 And that smile breathes no cloud at all.
    S(T(84), 'street', 'house', st=ST_A, c=Z(1.5, 0.01, 820, 560), music=[(WD(84, 'stops'), 'jingle_stop', 0.0)],
      sfx=[(WD(84, 'stops'), 'truck_idle', -14, 0, 'outside', dict(dur=3.0))])
    S(T(85), 'living', 'couch', st=dict(LIV_CRACK, lamp=0.6), ppl=[lina('couch_mid', kind='seat', expr='tempted', act=_A(lk(T(85) + 0.2, 'curtain_crack', body=0.4)))],
      c=Z(1.25, 0.02, 960, 620))
    BU(T(86), 'shiver', 'street', 'window_close', wc, cx=960, cy=580, scale=1.25, turn=0.1, light=SH_PINK, act=_A(lk(T(86), (960, 520))),
       acts=lambda A, sh, sp: [frost_air()], c=BZ(0.025))


# ==================================================================================================== THE COMMENT PROMPT (87-91)
def plan_pause(F):
    F.cut(T(87), 'pause', stage='stop', sfx=[(T(87), 'stinger', -6, 0, None, dict(kind='freeze')), (T(87) + 0.05, 'frost_creep', -6, 0, 'close')])
    F.cut(T(88), 'pause', stage='ask', t_word=T(89) + 0.05, t_q=T(90) + 0.05, t_rem=T(91) + 0.05,
          sfx=[(T(89) + 0.05, 'ui_pop', -6, 0, 'close'), (T(90) + 0.05, 'ui_pop', -4, 0, 'close'), (T(91), 'frost_creep', -8, 0, 'close')])


# ==================================================================================================== RULE 2: THE FREE ONE (92-124)
def plan_rule2(F):
    RULE(T(92), 2)
    # 95 I look across at Kessler's dark window.
    BU(T(95), 'adam_in', 'living', 'window', LIV_CRACK, cx=1000, cy=620, scale=0.88, turn=-0.35, light=PINK_L, expr='nervous', act=_A(lk(T(95), (500, 430))), c=BZ(0.02))
    S(W(95, 'kessler'), 'street', 'kessler', st=dict(ST_A, win=dict(his=0.0)), c=Z(1.15, 0.02))   # his dark window past the truck
    # 96 Then... a soft tap at the front door.
    ttap = WD(96, 'tap')
    S(T(96), 'living', 'couch3q', st=LIV_CRACK, ppl=[adam((3.2, 0.75, 0.0), face=(3.4, -1.0), act=_A(lk(ttap - 0.05, 'door_in', dur=0.15, body=0.5, snap=True)))],
      c=Z(1.3, 0.02, 760, 560), sfx=[(ttap, 'door_tap', -4, -0.4, 'inside', dict(kind='soft'))])
    S(W(96, 'front'), 'hall', 'doorclose', st=HALL_A, c=Z(1.0, 0.02))
    # 97-99 the cone on the doormat; it steams with cold; the wrapper
    IN(T(97), 'doormat', dict(wrapper=True), c=dict(mv='push', rate=0.03))
    IN(T(98), 'doormat', dict(wrapper=True), motion=lambda u: (0.0, 120.0, 0.6, 0.0), c=dict(mv='push', rate=0.03))
    IN(T(99), 'wrapper', dict(), c=dict(mv='push', rate=0.025))
    # 100 I don't open the door.  101 I leave it there.
    S(T(100), 'hall', 'door', st=HALL_A, cam=cm((-2.1, 2.9, 1.3), (-1.9, 0.0, 1.0), 950),
      ppl=[adam('door_in', face=(-1.74, 0.0), expr='stern_afraid', act=_A(reach(T(100) + 0.1, 1, 'knob_in', t1=WD(100, 'door'), dur=0.4)))], c=Z(1.05, 0.02))
    BU(T(101), 'adam_in', 'hall', 'door', HALL_A, cx=1000, cy=620, scale=0.88, turn=0.45, light=dict(PINK_L, rim_a=80), expr='set_jaw',
       act=_A(lk(T(101), (1500, 600)), lk(T(101) + 0.5, (200, 640), dur=0.5, body=0.4)), c=BZ(0.02))
    # 102-103 Five minutes later, it's on the kitchen windowsill. Outside.
    S(T(102), 'kitchen', 'window', st=dict(KIT_A), acts=lambda A, sh, sp: [sill_cone(sp)], c=Z(1.0, 0.02))
    # 103 "Outside." holds on the same frame (a push makes the drawn sill cone drift against the set)
    # 104 I check every lock.
    S(T(104), 'hall', 'door', st=HALL_A, cam=cm((-1.7, 2.0, 1.3), (-1.8, 0.0, 1.1), 1000),
      ppl=[adam('door_in', face=(-1.74, 0.0), expr='focused', act=_A(reach(T(104) + 0.1, 1, 'lock', dur=0.35, shape='pinch')))],
      sfx=[(T(104) + 0.45, 'deadbolt', -2, 0, 'inside', dict(kind='throw'))], c=Z(1.05, 0.02))
    # 105-106 the window open a crack, the cone gone; Lina's step-stool under it
    S(T(105), 'kitchen', 'wide', st=dict(KIT_A, sash=0.28, stool='window'), ppl=[adam('doorway', face='sill_out', expr='shock', act=_A(lk(T(105), 'sill_out')))],
      c=Z(2.1, 0.03, 250, 480, free=True), sfx=[(T(105) + 0.2, 'window_crack', -12, -0.3, 'inside')])
    S(T(106), 'kitchen', 'window', st=dict(KIT_A, sash=0.28, stool='window', table=False), c=Z(1.0, 0.02, 960, 820, free=True))     # (review: the stool in frame, above the caption)
    # 107-109 Lina on the couch holding the cone; tongue out; an inch away
    TG108, TG109 = (470, 695, 960), (330, 671, 1035)          # bust cy, her mouth y, the cone's swirl base y
    S(T(107), 'living', 'couch3q', st=LIV_CRACK, ppl=[lina('couch_right', kind='seat', expr='tempted',
                                                           act=_A(lambda a, s: a.reach_to(-9, 1, CONE_UP, dur=0.01, shape='grip'),
                                                                  lambda a, s: a.reach_to(-9, -1, (CONE_UP[0] - 14, CONE_UP[1] + 6), dur=0.01, shape='grip'),
                                                                  lk(T(107), (CONE_UP[0], CONE_UP[1] - 20))),
                                                           hands='lap', extras=[cone_fx('hand_r', 2.0)])], c=Z(1.7, 0.02, 1040, 700))
    # (the face sits high so the cone is held just BELOW her mouth, her tongue reaching for it: an inch of air between)
    BU(T(108), 'lina_pj', 'living', 'couch3q', LIV_CRACK, cx=960, cy=TG108[0], scale=0.95, light=LAMP, expr='thirsty', act=_A(lk(T(108), (960, 900))),
       on=[_tongue_fx(960, TG108[1], 34, 40, T(108) + 0.15)],
       hands=[dict(who='lina_pj', fn=lambda t: (1000, 1040, 175.0, 1.0), size=170, shape='grip', side=-1, sleeve_from=(1200, 1400))],
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: _cone_screen(pen, 960, TG108[2] + 40 * (1 - ease_in_out(clamp((t - sh.t0) / 0.6))), 150, t), 'cone')], c=BZ(0.0))
    BU(T(109), 'lina_pj', 'living', 'couch3q', LIV_CRACK, cx=960, cy=TG109[0], scale=1.5, light=LAMP, expr='thirsty', act=_A(lk(T(109), (960, 1000))),
       on=[_tongue_fx(960, TG109[1], 50, 60)],
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: _cone_screen(pen, 960, TG109[2], 200, t), 'cone')], c=BZ(0.0))
    # 110 I slap it.  111 It hits the floor and shatters like glass.
    tsl = WD(110, 'slap')
    lift = lambda a, s: [a.reach_to(-9, 1, CONE_UP, t1=tsl + 0.05, dur=0.01, shape='grip'), a.reach_to(-9, -1, (CONE_UP[0] - 14, CONE_UP[1] + 6), t1=tsl + 0.05, dur=0.01, shape='grip')]
    # (review M3: the slap as a readable close: Lina's face and the cone, ADAM's hand sweeps in and knocks it out of her
    # hand; the cone tumbles away toward the floor, her hand jerks open)
    def _slap_cone(pen, t, t0=tsl + 0.04):
        u = max(0.0, t - t0)
        x, y = 960 - 1500 * u, TG108[2] + 40 + 900 * u * u - 260 * u
        if u <= 0: return _cone_screen(pen, 960, TG108[2], 150, t)
        if y > 1500: return
        pen.cv.save(); pen.cv.translate(x, y); pen.cv.rotate(-420 * u); pen.cv.translate(-x, -y)
        _cone_screen(pen, x, y, 150, t); pen.cv.restore()
    BU(T(110), 'lina_pj', 'living', 'couch3q', LIV_CRACK, cx=960, cy=TG108[0], scale=0.95, light=LAMP, expr='shock', act=_A(lk(T(110), (960, 900)), lk(tsl + 0.08, (300, 1000), dur=0.15)),
       hands=[dict(who='lina_pj', fn=lambda t: (1000 - 60 * ease_out_cubic(clamp((t - tsl - 0.04) / 0.15)), 1040 + 60 * ease_out_cubic(clamp((t - tsl - 0.04) / 0.15)),
                                                175.0 - 25 * ease_out_cubic(clamp((t - tsl - 0.04) / 0.15)), 1.0), size=170, shape='grip', side=-1, sleeve_from=(1200, 1400)),
              dict(who='adam_in', fn=slide(tsl - 0.16, tsl + 0.12, (2050, 860), (700, 1000), 70, 85, ease=ease_in_out), size=330, shape='flat', side=1, sleeve_from=(2500, 1000))],
       acts=lambda A, sh, sp: [Layer(0.85, _slap_cone, 'cone')], c=BZ(0.0), sfx=[(tsl + 0.06, 'slap', 0, 0, 'inside')])
    IN(T(111), 'shatter', lambda u: dict(brk=clamp((u + T(111) - WD(111, 'floor')) / 0.25)), c=dict(mv='push', rate=0.02),
       sfx=[(WD(111, 'floor'), 'cone_shatter', 2, 0, 'close')])
    # 112 It was inside.  113 Brought in.
    S(T(112), 'living', 'couch3q', st=dict(LIV_CRACK, cone='floor'), ppl=[lina('couch_right', kind='seat', expr='shock', act=_A(lk(T(112), 'floor_cone'))),
                                                                          adam((3.0, 2.45, 0.0), face='floor_cone', expr='fear', act=_A(lk(T(112), 'floor_cone')))],
      c=Z(1.3, 0.02, 960, 760))
    BU(T(113), 'adam_in', 'living', 'couch3q', dict(LIV_CRACK, cone='floor'), cx=960, cy=600, scale=1.0, light=LAMP, expr='shock_shut',
       act=_A(lk(T(113), (960, 1000)), lambda a, s: a.blink(T(113) + 0.4)), c=BZ(0.03))
    # 114 Click.  115 The furnace stops.  116 Every light in the house goes out.  117 No bars.
    tck = WD(114, 'click')
    S(T(114), 'living', 'wide', st=dict(LIV_CRACK, cone='floor'), ppl=[adam((3.0, 2.45, 0.0), face=(3.4, 0.0), expr='fear', act=_A(lk(tck, 'opening', dur=0.15, snap=True))),
                                                                  lina('couch_right', kind='seat', expr='shock', act=_A(lk(tck + 0.08, 'opening', dur=0.2)))],
      c=Z(1.1, 0.01), sfx=[(tck, 'furnace_die', 0, 0, 'inside', dict(click=True))])
    S(T(115), 'hall', 'back', st=dict(hall=lambda t: 1.0 - 0.6 * clamp((t - T(115) - 0.6) / 0.3) * (0.5 + 0.5 * math.sin(t * 40)), truck='A'), c=Z(1.0, 0.01),
      sfx=[(T(115) + 0.1, 'furnace_die', -2, 0, 'inside')])
    S(T(116), 'street', 'house', st=ST_A, c=Z(1.5, 0.0, 820, 560))
    S(W(116, 'out'), 'street', 'house', st=ST_DARK, cut='blink', c=Z(1.5, 0.0, 820, 560), sfx=[(WD(116, 'out'), 'power_cut', 0, 0, 'outside')])
    IN(T(117), 'phone', dict(time_='11:47', bars=0), c=dict(mv='push', rate=0.03), sfx=[(WD(117, 'bars'), 'phone_buzz', -10, 0, 'close')])
    # 118-120 the black TV: us; GLIMPSE 2: the skull in the crack; red eyes
    tsk = WD(119, 'skull') - 0.4
    S(T(118), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=0.0), c=Z(1.0, 0.02))
    S(T(119), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=lambda t: ease_in_out(clamp((t - tsk) / 0.6))), c=Z(1.2, 0.16, 960, 470))     # (review: the push in finds the skull)
    S(T(120), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=1.0), c=Z(3.4, 0.02, 960, 440, hit=[WD(120, 'red')]), hit=WD(120, 'red'))
    # 121 I spin around.
    S(T(121), 'living', 'couch', st=dict(LIV_BLACK, cone='floor'), ppl=[adam('couch_mid', kind='seat', expr='terror', act=_A(lk(T(121) + 0.05, 'curtain_crack', dur=0.18, body=0.9, snap=True))),
                                                                        lina('couch_right', kind='seat', expr='fear', act=_A(lk(T(121) + 0.3, 'curtain_crack', dur=0.3, body=0.5)))],
      c=Z(1.2, 0.02, 960, 680), cold=False, sfx=[(T(121) + 0.05, 'whoosh', -10, 0, None, dict(kind='soft'))])
    # 122-123 Just the smiling man. Waving.  (POV through the crack)
    S(T(122), 'street', 'gap', st=ST_DARK, ppl=[SH(lean=0.2, act=_A(lambda a, s: a.slow_wave(T(122), E(123) + 1, 1), lk(T(122), (960, 520))))], c=Z(1.3, 0.02, 975, 470))
    # 124 I yank the curtain shut.
    ty = T(124) + 0.15
    S(T(124), 'living', 'window', st=dict(LIV_BLACK, curtains=lambda t: 0.13 * (1 - ease_in_cubic(clamp((t - ty) / 0.2)))),
      ppl=[adam((3.3, 0.55, 0.0), face=(3.4, -1.0), act=_A(reach(ty - 0.1, 1, 'curtain_crack', t1=ty + 0.6, dur=0.12)))], c=Z(1.3, 0.02, 920, 600),
      sfx=[(ty, 'curtain_yank', 0, 0, 'inside')])


def _cone_screen(pen, x, y, k, t):
    """The cone drawn big in screen space (close-ups of Lina): the swirl up, steam rising."""
    y0 = y
    wafer = poly([(x - k * 0.55, y0), (x + k * 0.55, y0), (x, y0 + k * 1.7)])
    pen.fill(wafer, '#d9a86a'); pen.line(wafer, max(1.0, k * 0.03), '#1a1418')
    for j in range(4):
        pen.seg((x - k * 0.45 + j * k * 0.25, y0 + k * 0.1), (x - k * 0.05 + j * k * 0.12, y0 + k * 1.3), max(0.8, k * 0.02), '#a8743a')
    for j, (c_, r_) in enumerate((('#f0aecb', 0.62), ('#ece2e6', 0.5), ('#e08ab0', 0.38), ('#ece2e6', 0.24))):   # off-white: no bloom
        pen.fill(oval(x, y0 - k * (0.2 + 0.32 * j), k * r_ * 1.05, k * r_ * 0.7), c_)
        pen.line(oval(x, y0 - k * (0.2 + 0.32 * j), k * r_ * 1.05, k * r_ * 0.7), max(1.0, k * 0.012), '#b0607f', 120)
    for j in range(3):
        u = ((t * 0.5 + j / 3.0) % 1.0)
        pen.fill(oval(x + k * 0.3 * math.sin(t * 2 + j), y0 - k * (1.3 + 1.4 * u), k * (0.2 + 0.3 * u)), '#eef6ff', 110 * (1 - u), blur=k * 0.12)


def _tongue_fx(mx, my, w, ln, t0=-99.0, dur=0.25):
    """Lina's tongue poking out of her mouth toward the cone (busts L108-109): bust design px of the mouth centre."""
    def fx(pen, t, a):
        u = ease_out_cubic(clamp((t - t0) / dur))
        if u <= 0.01: return
        L = ln * u
        tg = union(oval(mx, my + L * 0.45, w * 0.5, L * 0.55), rect(mx - w * 0.5, my - w * 0.05, w, L * 0.4))
        pen.fill(tg, '#e8707e'); pen.line(tg, max(1.0, w * 0.05), '#6a2030', 220)
        pen.seg((mx, my + L * 0.15), (mx, my + L * 0.6), max(1.0, w * 0.04), '#b8485a', 180)
        pen.fill(oval(mx, my, w * 0.62, w * 0.16), '#4a1420', 230)          # the open lips' dark line over the root
    return fx


def _tv_skull_screen(pen, v, o, k=0.0, skull=0.0, t=0.0, _orig=ST.ic_tv_screen):
    """GLIMPSE 2 (L119-120): the set's TV reflection, then a long white skull in the curtain crack drawn big enough to
    read: bone-white mask, dark sockets with red eyes, the jaw hanging with icicle teeth, frost cracks; the curtain edges
    cover its sides (it is outside the window, seen through the crack)."""
    _orig(pen, v, o, k, 0.0, t)
    if skull <= 0.01 or k > 0.01: return
    q = ST._ic_tv_quad()
    if v.d(ST.IC_TV[0], ST.IC_TV[1]) < 0.3 or not v.visible(q[0], (0, 0, -1)): return
    path = v.poly3(q)
    if path.isEmpty(): return
    b = path.computeTightBounds(); W, H = b.width(), b.height()
    a = 235 * skull
    cx = b.left() + W * 0.5
    wy0, wy1 = b.top() + H * 0.12, b.top() + H * 0.62
    sy = wy0 + H * 0.11 + (1.0 - skull) * H * 0.12                                  # it rises into the crack
    pen.cv.save(); pen.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    pen.cv.save(); pen.cv.clipRect(skia.Rect.MakeLTRB(b.left(), wy0, b.right(), b.top() + H * 0.6), skia.ClipOp.kIntersect, True)
    head = union(oval(cx, sy, W * 0.04, H * 0.1), poly([(cx - W * 0.036, sy + H * 0.02), (cx + W * 0.036, sy + H * 0.02),
                                                       (cx + W * 0.022, sy + H * 0.3), (cx - W * 0.022, sy + H * 0.3)]))
    pen.fill(head, '#e6e2d8', a); pen.line(head, max(1.0, W * 0.002), '#6a6878', a * 0.8)
    ey = sy + H * 0.035
    for dx in (-1, 1):
        pen.fill(oval(cx + dx * W * 0.014, ey, W * 0.011, H * 0.034), '#120a12', a)
        pen.fill(oval(cx + dx * W * 0.014, ey + H * 0.004, W * 0.0045, H * 0.012), '#ff2a2a', 255 * skull)
        pen.glow(cx + dx * W * 0.014, ey, W * 0.02, '#ff2020', 110 * skull)
    pen.fill(poly([(cx, ey + H * 0.045), (cx - W * 0.005, ey + H * 0.075), (cx + W * 0.005, ey + H * 0.075)]), '#2a2030', a)
    my0, my1 = sy + H * 0.15, sy + H * 0.28                                         # the jaw dropped: no throat, just dark and teeth
    pen.fill(rrect(cx - W * 0.017, my0, W * 0.034, my1 - my0, W * 0.008), '#07040a', a)
    for j in range(5):
        x_ = cx - W * 0.014 + j * W * 0.007
        pen.fill(poly([(x_ - W * 0.003, my0), (x_ + W * 0.003, my0), (x_, my0 + H * 0.03)]), '#dfe8f0', a)
        pen.fill(poly([(x_ - W * 0.003, my1), (x_ + W * 0.003, my1), (x_, my1 - H * 0.025)]), '#dfe8f0', a)
    for (x0, y0, x1, y1) in ((-0.03, -0.06, -0.012, 0.0), (0.02, -0.08, 0.03, -0.02), (0.01, 0.1, 0.022, 0.13)):
        pen.seg((cx + W * x0, sy + H * y0), (cx + W * x1, sy + H * y1), max(1.0, W * 0.0015), '#8fa4bc', a * 0.8)
    for (a0, a1) in ((b.left(), cx - W * 0.03), (cx + W * 0.03, b.right())):          # the curtains either side of the crack
        pen.fill(rect(a0, wy0 - H * 0.04, a1 - a0, wy1 - wy0 + H * 0.08), '#1a1014', 215)
    pen.cv.restore()
    pen.linear(path, b.left(), b.top(), b.right(), b.bottom(), [(0, '#ffffff', 0), (0.35, '#ffffff', 22), (0.42, '#ffffff', 0)])
    pen.cv.restore()


ST.ic_tv_screen = _tv_skull_screen


def _fence_capped(pen, v, *a, _orig=ST.ic_fence, **k):
    """The picket fence with its lighting capped: under his pink window the lit pickets (dense, near the lens) blew out
    into a white slab with bloom (L69, L81, L177-178, L191, L214-226: W/handoff/requests.md, sets 2). Same fence, the
    brightest channel held to 0.74."""
    ol = ST.lit

    def capped(c, *aa, **kk):
        r = ol(c, *aa, **kk)
        try:
            h = r.lstrip('#'); rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        except Exception: return r
        m = max(rgb)
        if m <= 189: return r
        return '#%02x%02x%02x' % tuple(int(x * 189 / m) for x in rgb)
    ST.lit = capped
    try: return _orig(pen, v, *a, **k)
    finally: ST.lit = ol


ST.ic_fence = _fence_capped


# ==================================================================================================== RULE 3: THE COLD HOUSE, THE FAKE DAD (125-164)
def plan_rule3(F):
    RULE(T(125), 3)
    # 128-129 Frost creeps across the windows. On the inside.
    tf0 = T(128) + 0.2
    # (the living-room curtains are shut since L124: the frost is seen creeping over the bare kitchen window, power dead)
    KIT_FROST = dict(kitchen_light=0.0, truck='A', frost=lambda t: ease_in_out(clamp((t - tf0) / (E(129) - tf0))))
    S(T(128), 'kitchen', 'window', st=KIT_FROST, c=Z(1.0, 0.02),
      sfx=[(tf0, 'frost_creep', -4, 0, 'inside', dict(dur=round(E(129) - tf0, 2)))])
    S(T(129), 'kitchen', 'window', st=KIT_FROST, c=Z(1.8, 0.02, 960, 470))
    # 130 Our breath clouds in the living room.
    S(T(130), 'living', 'couch3q', st=dict(LIV_FROST, cone='floor'), ppl=[adam('couch_mid', kind='seat', expr='fear', act=_A(lk(T(130), (700, 520)))),
                                                                          lina('couch_right', kind='seat', expr='sad', seed=2)], cold=True, c=Z(1.6, 0.02, 1000, 720))
    # 131-134 Coats. Hats. Two pairs of socks. Mittens, even for Lina.
    S(T(131), 'hall', 'door', st=HALL_BLACK, cam=cm((-2.0, 2.9, 1.4), (-2.6, 0.9, 1.2), 950),
      ppl=[adam('coats', face=(-2.8, 0.85), act=_A(reach(T(131) + 0.05, 1, (-2.78, 0.75, 1.5), dur=0.3), reach(T(131) + 0.4, -1, (-2.78, 1.0, 1.5), dur=0.3)))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(131) + 0.3, 'coat_rustle', -6, 0, 'inside')])
    BU(T(132), 'lina', 'living', 'couch3q', LIV_FROST, cx=960, cy=620, scale=0.9, light=PINK_D, expr='sad', cold=True,
       act=_A(lambda a, s: a.head_tilt(T(132) + 0.1, -9.0, 0.6)), c=BZ(0.02))
    S(T(133), 'living', 'couch3q', st=LIV_FROST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='focused', act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.35),
                                                                                                                       reach(T(133), 1, (3.3, 1.95, 0.1), dur=0.3)))],
      cold=True, c=Z(2.2, 0.02, 1000, 760), post=dict(exposure=0.6))     # (owner's-eyes: lit, closer on the socks he grabs)
    BU(T(134), 'lina', 'living', 'couch3q', LIV_FROST, cx=960, cy=600, scale=0.9, light=PINK_D, expr='stern', cold=True, act=_A(shake_head(WD(134, 'lina'), 2, dur=0.7)),
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: [_mitten_screen(pen, 760, 1000 - 20 * math.sin(t * 2), 70, -15), _mitten_screen(pen, 1160, 1000 - 20 * math.sin(t * 2 + 1), 70, 15)], 'mitts')],
       c=BZ(0.02))
    # 135 One blanket, both of us.
    S(T(135), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='brave'), lina('couch_right', who='lina', kind='seat', expr='sad', seed=2,
                                                                                                                   extras=[mitts()])],
      cold=True, acts=nest_blanket(), c=Z(1.5, 0.02, 1000, 720))
    # 136-138 The song comes back. Softer. A lullaby.
    S(T(136), 'street', 'house', st=ST_DARK, c=Z(1.6, 0.01, 820, 560),
      music=[(T(136), 'jingle', 0.3, round(E(139) - T(136) + 1, 2), dict(version='lullaby'))])
    S(T(137), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.6 + 0.4 * math.sin((t - T(137)) * 1.6)), ppl=NEST_BACK(), acts=nest_blanket(), cold=True, c=Z(1.1, 0.02))
    # 139 Lina's eyes droop.
    BU(T(139), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sleepy', cold=True, act=_A(sleepyf(T(139) + 0.2)), c=BZ(0.02))
    # 140 Dad said if we needed a grown-up...  141 I pull on my boots.  142 "We're going to Mr. Kessler's."
    BU(T(140), 'adam', 'living', 'couch3q', LIV_NEST, cx=1000, cy=620, scale=0.9, turn=-0.35, light=PINK_D, expr='determined', cold=True,
       act=_A(lk(T(140), (350, 500), dur=0.5)), c=BZ(0.02))
    S(T(141), 'hall', 'door', st=HALL_BLACK, cam=cm((-2.0, 3.0, 1.2), (-2.5, 1.4, 0.6), 950),
      ppl=[adam('bench', who='adam', kind='seat', face=(-2.0, 1.5), expr='set_jaw', act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.4),
                                                                                      reach(T(141), 1, (-2.4, 1.75, 0.15), dur=0.35), reach(T(141), -1, (-2.45, 1.65, 0.2), dur=0.35)))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(141) + 0.4, 'boot_on', -6, 0, 'inside')])
    BU(T(142), 'adam', 'hall', 'door', HALL_BLACK, cx=960, cy=620, scale=0.9, turn=0.3, light=PINK_D, expr='resolve', cold=True, act=_A(lk(T(142), (1300, 640))), c=BZ(0.02))
    # 143 The radio crackles.  144 the fake Dad: "Separate rooms."
    RIN(T(143), lambda u: dict(talk=0.0, static=0.5 + 0.5 * abs(math.sin(u * 9))), c=dict(mv='push', rate=0.04), sfx=[(T(143), 'radio_squelch', -2, 0, 'close')])
    RIN(T(144), lambda u: dict(talk=0.7 + 0.3 * math.sin(u * 7), static=0.15), c=dict(mv='push', rate=0.02))
    BU(W(144, 'stay'), 'adam', 'hall', 'door', HALL_BLACK, cx=1000, cy=620, scale=0.92, light=PINK_D, expr='suspicious', cold=True,
       act=_A(lk(W(144, 'stay'), (1100, 760))), c=BZ(0.02))          # listening: the face reads (no radio over it)
    RIN(W(144, 'separate'), lambda u: dict(talk=0.7 + 0.3 * math.sin(u * 7), static=0.15), motion=lambda u: (0.0, 0.0, 0.5 + 0.06 * u, 0.0), c=dict(mv='hold'))
    # 145 I almost go.  146 Lina grabs my coat.
    S(T(145), 'hall', 'door', st=HALL_BLACK, ppl=[adam((-2.1, 2.4, 0.0), who='adam', path=[(T(145), (-2.1, 2.4, 0.0)), (E(145) + 0.3, (-2.1, 0.8, 0.0))],
                                                        expr='set_jaw', act=_A(reach(E(145) - 0.1, 1, 'knob_in', dur=0.35)))], cold=True, c=Z(1.4, 0.02, 960, 640))
    tgr = WD(146, 'grabs')
    S(T(146), 'hall', 'door', st=HALL_BLACK, cam=cm((-1.6, 3.4, 1.2), (-2.1, 0.8, 1.0), 1000),
      ppl=[adam((-2.1, 0.8, 0.0), who='adam', id='adam', face=(-2.1, 0.0), expr='set_jaw', act=_A(lk(tgr + 0.2, ('lina', 'head'), dur=0.3, body=0.5))),
           lina((-1.9, 2.2, 0.0), who='lina', id='lina', path=[(T(146), (-1.9, 2.2, 0.0)), (tgr, (-2.0, 1.2, 0.0))], run=True, expr='pleading',
                act=_A(reach(tgr - 0.05, 1, ('adam', 'hip'), dur=0.25)))], cold=True, c=Z(1.0, 0.02))
    BU(T(147), 'lina', 'hall', 'door', HALL_BLACK, cx=960, cy=600, scale=0.95, light=PINK_D, expr='pleading', cold=True, act=_A(lk(T(147), (960, 300))), c=BZ(0.02))
    # 148-149 "The rule says one blanket," I tell the radio.
    BU(T(148), 'adam', 'hall', 'door', HALL_BLACK, cx=980, cy=620, scale=0.9, turn=-0.2, light=PINK_D, expr='brave', cold=True,
       act=_A(radio(T(148) - 0.3, E(149) + 0.5, 1)), c=BZ(0.02))
    # 150 Silence.  151 "Then keep her warm, kiddo. Close your eyes. Sleep is warm."
    RIN(T(150), dict(talk=0.0, static=0.0), c=dict(mv='push', rate=0.01))
    RIN(T(151), lambda u: dict(talk=0.6 + 0.4 * math.sin(u * 6), static=0.1), c=dict(mv='push', rate=0.02))
    BU(W(151, 'close'), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sleepy', cold=True,
       act=_A(sleepyf(W(151, 'close'))), c=BZ(0.02))
    # 152-154 Pink light sweeps the curtain. A shadow. Long, jointed legs.  (GLIMPSE 3)
    S(T(152), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.4 + 0.6 * ease_in_out(clamp((t - T(152)) / 1.0))), ppl=NEST_BACK(T(152) + 0.3), acts=nest_blanket(), cold=True, c=Z(1.0, 0.02))
    tls = T(153)
    S(T(153), 'living', 'window', st=dict(LIV_FROST, pink=1.0), ppl=NEST_BACK(T(153) - 1.0, adam_expr='terror'), cold=True,
      acts=lambda A, sh, sp: nest_blanket()(A, sh, sp) + [leg_shadow(sp, tls, E(154) + 0.3)], c=Z(1.05, 0.02),
      sfx=[(tls + 0.2, 'scuttle', -10, 0, 'outside', dict(surface='roof'))])
    S(T(154), 'living', 'window', st=dict(LIV_FROST, pink=1.0), acts=lambda A, sh, sp: [leg_shadow(sp, tls, E(154) + 0.3)], c=Z(1.8, 0.02, 1000, 520, hit=[T(154) + 0.1]),
      hit=T(154) + 0.1)
    # 155 Then an orange light sweeps the street.
    S(T(155), 'street', 'plow', st=dict(truck=None, plow=dict(x=lambda t: -14.0 + 7.0 * clamp(t - T(155), 0.0, 6.0), y=-11.0, dir=1, beacon=1.0)), c=Z(1.0, 0.01),
      sfx=[(T(155), 'plow_pass', -2, 0, 'outside', dict(dur=3.0))])
    # 156 D "Adam? Passing our street. All good? Over."
    dadcab = lambda: dict(plain=('#2a1c14', '#0a0706'), bg_fn=cab_bg(), light=lambda t: dict(BEACON, rim_a=int(70 + 80 * (0.5 + 0.5 * math.sin(t * 8.2)))))
    BU(T(156), 'dad', None, None, cx=960, cy=600, scale=0.85, turn=0.3, expr='kind_smile', act=_A(radio(T(156) - 0.5, E(156) + 0.3, 1)), c=BZ(0.015), **dadcab())
    BU(T(157), 'adam', 'living', 'window', LIV_FROST, cx=1000, cy=620, scale=0.92, light=PINK_D, expr='asking', cold=True, act=_A(radio(T(157) - 0.3, E(157) + 0.5, 1)), c=BZ(0.02))
    BU(T(158), 'dad', None, None, cx=960, cy=600, scale=0.9, turn=0.3, expr='suspicious', act=_A(radio(T(158) - 0.5, E(158) + 0.3, 1)), c=BZ(0.015), **dadcab())
    BU(W(158, 'hour'), 'adam', 'living', 'window', LIV_FROST, cx=980, cy=620, scale=1.0, light=PINK_D, expr='shock', cold=True,
       act=_A(radio(T(157), W(158, 'hour') + 0.05, 1)), c=BZ(0.03))      # the radio drops from his mouth: it sinks in
    BU(T(159), 'adam', 'living', 'window', LIV_FROST, cx=960, cy=600, scale=1.1, light=PINK_D, expr='terrified_call', cold=True,
       act=_A(radio(T(159) - 0.4, E(159) + 0.5, 1)), c=BZ(0.03))
    # 160 Static.  161 Bells.
    RIN(T(160), lambda u: dict(talk=0.0, static=1.0), cut='static', c=dict(mv='push', rate=0.04), sfx=[(T(160), 'radio_static', 0, 0, 'close', dict(dur=1.0))])
    RIN(T(161), lambda u: dict(talk=0.5 + 0.5 * math.sin(u * 30), static=0.9), motion=lambda u: (0.0, 0.0, 0.4, 0.0), c=dict(mv='hold'),
       sfx=[(WD(161, 'bells'), 'radio_bells', -2, 0, 'close')], post_fn=lambda t: dict(mix=('ic_ext', 0.0)))
    BU(T(162), 'dad', None, None, cx=960, cy=600, scale=0.85, turn=0.3, expr='suspicious', act=_A(radio(T(162) - 0.5, E(162) + 0.3, 1)), c=BZ(0.015),
       post_fn=lambda t: dict(static=0.25 + 0.2 * abs(math.sin(t * 13))), **dadcab())
    # 163 The orange light fades.  164 The pink one doesn't.
    tb = T(163) - 0.4
    S(T(163), 'living', 'window', st=dict(LIV_FROST, pink=0.8, beacon=lambda t: 1.0 - clamp((t - tb) / 1.6)), ppl=NEST_BACK(T(163)), acts=nest_blanket(), cold=True, c=Z(1.0, 0.01))
    S(T(164), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.9 + 0.1 * math.sin(t * 2)), ppl=NEST_BACK(T(164) - 1.0), acts=nest_blanket(), cold=True, c=Z(1.3, 0.02, 940, 600))


def _mitten_screen(pen, x, y, s, rot):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    m = rrect(-s, -1.2 * s, 2 * s, 2.4 * s, s * 0.9)
    pen.fill(m, ST.IC_LINA_MITTEN); pen.line(m, max(1.0, s * 0.06), '#1a1418')
    th = rrect(-1.45 * s, -0.4 * s, 0.7 * s, 1.0 * s, 0.35 * s)
    pen.fill(th, ST.IC_LINA_MITTEN); pen.line(th, max(1.0, s * 0.06), '#1a1418')
    pen.fill(rrect(-1.05 * s, 0.9 * s, 2.1 * s, 0.55 * s, 0.2 * s), '#f4f0f2'); pen.line(rrect(-1.05 * s, 0.9 * s, 2.1 * s, 0.55 * s, 0.2 * s), max(1.0, s * 0.05), '#1a1418')
    cv.restore()


# ==================================================================================================== RULE 4: THE WALK OUT, THE TRANSFORMATION, THE CHASE (165-262)
def plan_rule4(F):
    RULE(T(165), 4)
    IN(T(168), 'card', lambda u: dict(time_='Two-ten.', temp='Minus thirty-eight.' if u + T(168) >= F.t(169) - 0.05 else None), c=dict(mv='push', rate=0.015))
    # 170 Cold makes you sleepy.  171 That's how it gets you.  172 I wake up.  173 The blanket beside me is cold.
    S(T(170), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='sleep'), lina('couch_right', who='lina', kind='seat', expr='sleep', seed=2,
                                                                                                                      extras=[mitts()])],
      cold=True, acts=nest_blanket(), c=Z(1.5, 0.02, 1000, 720))
    BU(T(171), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sleep', cold=True, c=BZ(0.02))
    BU(T(172), 'adam', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sleep', cold=True,
       act=_A(ex('shock_shut', WD(172, 'wake'), None, 0.15), lambda a, s: a.lids(WD(172, 'wake') - 0.05, None, 0.0, 0.12),
              lk(WD(172, 'wake') + 0.1, (1300, 700), dur=0.2)), c=BZ(0.02))
    S(T(173), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='fear',
                                                          act=_A(lk(T(173), 'couch_right', body=0.3), reach(T(173) + 0.2, -1, (2.84, 1.68, 0.5), dur=0.4, shape='flat')))],
      cold=True, acts=nest_blanket(('adam',), empty=1.0), c=Z(1.6, 0.02, 1000, 720))
    # 174 The front door is swinging open.
    S(T(174), 'hall', 'door', st=dict(HALL_BLACK, door=lambda t: 55.0 + 18.0 * math.sin((t - T(174)) * 1.7)), cold=True, c=Z(1.2, 0.02, 960, 600),
      sfx=[(T(174), 'door_creak', -4, 0, 'inside'), (T(174), 'wind_gust', -6, 0, 'outside')])
    # 175 In the snow, a mitten.  176 Then the other one.
    trk = [('child', [(-2.1, -0.6), (-2.1, -2.3), (-2.0, -4.5), (-1.2, -6.8), (-0.6, -7.7)])]
    S(T(175), 'street', 'door', st=dict(ST_DARK, porch=0.0, tracks=trk, props=[('mitten', -2.0, -2.55), ('mitten', -1.75, -3.6)], door_open=True),
      cam=cm((-1.55, -4.3, 0.45), (-2.0, -2.55, FOOT), 1500, sy=560), c=Z(1.0, 0.02))   # low and close: her mitten in the snow, the open door behind
    S(T(176), 'street', 'door', st=dict(ST_DARK, tracks=trk, props=[('mitten', -2.0, -2.55), ('mitten', -1.75, -3.6)], door_open=True),
      cam=cm((-1.3, -5.6, 0.5), (-1.75, -3.6, FOOT), 1400, sy=560), c=Z(1.0, 0.02))   # down the walk: the second mitten nearer the street
    # 177 Lina is walking toward the pink window.
    MIT = [('mitten', -2.0, -2.55), ('mitten', -1.75, -3.6)]
    S(T(177), 'street', 'truck', st=dict(ST_DARK, tracks=trk, props=MIT),
      ppl=[lina((-1.9, -5.0, FOOT), who='lina', path=[(T(177) - 1.0, (-1.9, -5.0, FOOT)), (E(178) + 1.5, (-0.6, -7.6, FOOT))], surface='snow', expr='dazed',
                act=_A(hum(T(177), E(180)))),
           SH(lean=0.2, act=_A(lambda a, s: a.slow_wave(T(177), E(177) + 1.0, 1), lk(T(177), (900, 820))))], cold=True, c=Z(1.6, 0.02, 920, 500))
    S(T(178), 'street', 'truck', st=dict(ST_DARK, tracks=trk, props=MIT), cam=cm((-0.9, -9.6, -0.1), (-1.2, -6.6, 0.4), 1000),
      ppl=[lina((-1.5, -6.2, FOOT), who='lina', path=[(T(178) - 1.0, (-1.5, -6.2, FOOT)), (E(178) + 0.6, (-0.95, -7.3, FOOT))], surface='snow', expr='dazed',
                act=_A(hum(T(178), E(178))), light=PINK)], cold=True, c=Z(1.0, 0.02))
    BU(T(179), 'lina', 'street', 'truck', dict(ST_DARK, props=MIT), cx=960, cy=600, scale=0.95, light=PINK, expr='dazed', cold=True,
       act=_A(hum(T(179), E(180) + 0.5), tilt(T(179) + 0.2, 7.0, 2.0)), c=BZ(0.02))
    BU(T(180), 'lina', 'street', 'truck', dict(ST_DARK, props=MIT), cx=960, cy=520, scale=1.4, light=PINK, expr='still_smile', cold=True,
       act=_A(hum(T(180) - 0.5, E(180) + 0.5)), c=BZ(0.02))
    # 181-183 L "I'm warm, Adam," she calls back. "I'm not even shivering."
    BU(T(181), 'lina', 'street', 'truck', dict(ST_DARK, props=MIT), cx=1000, cy=600, scale=0.95, turn=0.45, h_turn=0.3, light=PINK, expr='still_smile', cold=True,
       act=_A(lk(T(181), (1700, 640), dur=0.5)), c=BZ(0.015))
    # 184 I run.  185 Knee-deep snow.  186 Air that hurts to breathe.
    S(T(184), 'street', 'door', st=dict(ST_DARK, door_open=True, props=MIT, tracks=trk),
      ppl=[kid('adam', 'porch_out', path=[(T(184), (-2.1, -0.5, 0.0)), (T(184) + 0.45, (-2.1, -1.75, -0.33)), (E(184) + 0.6, (-2.0, -3.4, FOOT - 0.12))],
               run=True, surface='snow', expr='terrified_call')], cold=True, c=Z(1.1, 0.03))
    S(T(185), 'street', 'yard', st=dict(ST_DARK, props=MIT, tracks=trk), cam=cm((-4.6, -8.6, 0.2), (-1.8, -5.2, 0.1), 950),
      ppl=[kid('adam', (-2.0, -3.8, FOOT - 0.22), path=[(T(185) - 0.3, (-2.0, -3.6, FOOT - 0.22)), (E(185) + 0.4, (-1.5, -6.0, FOOT - 0.22))],
               run=True, surface='snow', expr='terrified_call')], cold=True, c=Z(1.0, 0.03))
    BU(T(186), 'adam', 'street', 'yard', dict(ST_DARK), cx=960, cy=600, scale=0.95, light=PINK_L, expr='terrified_call', cold=True,
       act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.2)), on=[puffs(1.6, 1.0)], c=BZ(0.03, shake=2.2))
    # 187 The serving window slides open.  188 Warm pink light.
    two = T(187) + 0.2
    S(T(187), 'street', 'curb', st=dict(ST_DARK, truck_open=lambda t: ease_in_out(clamp((t - two) / 1.0))),
      ppl=[SH(lean=0.12, act=_A(lk(T(187), (1000, 1100))))], c=Z(1.0, 0.02), sfx=[(two, 'serving_window', 0, 0, 'outside')])
    BU(T(188), 'lina', 'street', 'curb', dict(ST_DARK, truck_open=1.0), cx=960, cy=640, scale=0.95, light=dict(PINK, rim_a=200, key=0.0), expr='dazed', cold=True,
       act=_A(lk(T(188), (1000, 200), dur=0.5)), c=BZ(0.02))
    # 189-191 He leans down. Down. Further than a man can bend.
    STO = dict(ST_DARK, truck_open=1.0)

    def bend(t0, t1, b0, b1):
        def f(a, s):
            def fn(P_, t):
                u = ease_in_out(clamp((t - t0) / max(0.1, t1 - t0)))
                P_.ws_bend = max(P_.ws_bend, lerp(b0, b1, u)); P_.ws_face_up = 0.9
                P_.sh_neck += 10.0 * clamp((lerp(b0, b1, u) - 0.6) / 0.6)
            a._add(-1e9, None, fn)
        return f
    BEND = lambda: bend(T(189), E(191), 0.2, 1.3)
    S(T(189), 'street', 'curb', st=STO, ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(BEND(), lk(T(189), (1150, 1100))))], c=Z(1.0, 0.02),
      sfx=[(T(189) + 0.2, 'skin_stretch', -10, 0, 'outside', dict(kind='creak'))])
    S(T(190), 'street', 'curb', st=STO, ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(BEND(), lk(T(190), (1150, 1100))))], c=Z(1.25, 0.02, 1000, 560))
    S(T(191), 'street', 'truck', st=STO, ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(BEND(), lk(T(191), 'lina_window'))),
                                              lina('lina_window', who='lina', face=(0.27, -8.4), expr='dazed', light=PINK, act=_A(lk(T(191), ('shiver', 'eyes'))))],
      cold=True, c=Z(2.0, 0.03, 920, 560))          # (review: 'further than a man can bend' close on the bend over her)
    # 192 S "Who's the coldest? YOU are! Free for whoever's coldest!"
    BU(T(192), 'shiver', 'street', 'curb', STO, cx=960, cy=560, scale=1.0, light=SH_PINK, rot=-12,
       act=_A(pose(-9, None, 0.1, ws_bend=0.4), lambda a, s: a.slow_wave(T(192), E(192) + 1, 1), lk(T(192), (960, 700))), c=BZ(0.02))
    BU(W(192, 'you'), 'shiver', 'street', 'curb', STO, cx=960, cy=-210, scale=1.5, light=SH_PINK, rot=-14, face_fix=False,
       act=_A(pose(-9, None, 0.1, ws_bend=0.45), lambda a, s: a.set(W(192, 'you'), None, 0.3, sh_smile=0.15), lk(W(192, 'you'), (960, 760), snap=True, dur=0.1)),
       c=BZ(0.03))
    # 193-194 Lina's bare hand reaches up. His glove reaches down.  (the gap closing)
    t193, t194 = WD(193, 'hand'), WD(194, 'glove')
    S(T(193), 'street', 'curb', st=STO,
      ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(pose(-9, None, 0.1, ws_bend=1.3, ws_face_up=0.9),
                                              lambda a, s: a.reach_far(t194 - 0.2, 1, lambda t: (s.A['lina'].where(t, 'hand_r')[0] - 10, s.A['lina'].where(t, 'hand_r')[1] - 60),
                                                                       dur=1.4, z=30.0))),
           lina((-0.05, -7.65, FOOT), who='lina', id='lina', face=(0.27, -8.6), expr='dazed', light=PINK,
                act=_A(lk(T(193), ('shiver', 'eyes')), reach(t193 - 0.1, 1, (0.2, -8.2, 1.05), dur=1.2, shape='reach', z=60.0)))],
      cold=True, c=Z(1.35, 0.01, 1000, 640))
    # 195 An inch from his fingers, I yank her into my arms.
    LINA_PULL, LINA_LIFT = -80.0, 120.0                                 # (screen px: she slides right, toward Adam, as he grabs)
    tyk = WD(195, 'yank')
    S(T(195), 'street', 'truck', st=STO,
      ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(pose(-9, None, 0.1, ws_bend=1.3, ws_face_up=0.9),
                                              lambda a, s: a.reach_far(T(195) - 1, 1, (scr(s.sp, 'lina_window')[0] + 20, scr(s.sp, 'lina_window')[1] - 0.95 * spot_of(s.sp, 'lina_window').ppm),
                                                                       t1=tyk + 0.2, dur=0.5, z=30.0))),
           lina('lina_window', who='lina', id='lina', face=(0.27, -8.6), expr='dazed', light=PINK,
                act=_A(reach(T(195) - 1, 1, (0.15, -8.15, 1.0), t1=tyk - 0.12, dur=0.4, shape='reach'), ex('fear', tyk + 0.05), lambda a, s: a._add(tyk, None, _pull(tyk, LINA_PULL, 0.2, LINA_LIFT))),
                until=tyk + 0.2, dorder=-0.6),  # in front of Adam while she slides into his arms                                     # yanked: from here she is in Adam's arms (carry)
           kid('adam', (-1.6, -6.4, FOOT), id='adam', path=[(T(195) - 0.3, (-1.9, -6.0, FOOT)), (tyk, (-0.9, -7.45, FOOT)), (E(195) + 0.4, (-1.4, -6.9, FOOT))],
               run=True, surface='snow', expr='terrified_call', act=_A(reach(tyk - 0.25, -1, ('lina', 'chest'), t1=tyk + 0.1, dur=0.15)),
               carry=dict(who='lina', t0=tyk + 0.2, expr='fear'))],
      cold=True, c=Z(1.7, 0.01, 900, 500, hit=[tyk + 0.05]), sfx=[(tyk, 'cloth_grab', -2, 0, 'outside')])
    # 196 I step back.  (Adam, Lina in his arms; from here he carries her)
    S(T(196), 'street', 'truck', st=STO,
      ppl=[SH(lean=0.25, act=_A(lambda a, s: a.slow_wave(T(196), E(200) + 2, 1), lk(T(196), ('adam', 'head')))),
           kid('adam', (-1.15, -7.2, FOOT), id='adam', face=(0.27, -8.6), expr='terror', carry=dict(who='lina', t0=-9.0, expr='fear'),
               act=_A(lambda a, s: a._add(T(196) + 0.2, None, _step_back(T(196) + 0.2, 40.0))))],
      cold=True, c=Z(1.35, 0.01, 920, 560))
    # 197-198 My boot doesn't move. Frozen to the snow.
    IN(T(197), 'boot', dict(), layers=[frozen_boot(T(197), 0.03, (T(197) + 0.25, E(197) + 0.1))], c=dict(mv='hold'), sfx=[(T(197) + 0.2, 'boot_stuck', -2, 0, 'close')])
    IN(T(198), 'boot', dict(), layers=[frozen_boot(T(198) - 1.2, 0.0, None, z0=1.45, zr=0.05)], c=dict(mv='hold'),
       sfx=[(T(198) + 0.1, 'frost_creep', -8, 0, 'close')])
    # 199-213 THE TRANSFORMATION (face), one transform() curve across every cut; he keeps waving throughout
    TFW = lambda: _A(tf, lambda a, s: a.slow_wave(T(199) - 2, E(223) + 2, 1))
    BU(T(199), 'shiver', 'street', 'window_close', STO, cx=960, cy=620, scale=1.0, light=SH_PINK, act=_A(TFW(), lk(T(199), (960, 620))), c=BZ(0.02))
    BU(T(201), 'shiver', 'street', 'window_close', STO, cx=960, cy=600, scale=1.25, light=SH_PINK, act=_A(TFW(), lk(T(201), (960, 620))), c=BZ(0.02),
       sfx=[(T(201) + 0.2, 'skin_stretch', -6, 0, 'outside')])
    BU(T(202), 'shiver', 'street', 'window_close', STO, cx=960, cy=560, scale=1.6, light=SH_PINK, act=_A(TFW(), lk(T(202), (960, 600))), c=BZ(0.02))
    BU(T(204), 'shiver', 'street', 'window_close', STO, cx=960, cy=640, scale=1.2, light=SH_PINK, act=_A(TFW(), lk(T(204), (960, 600))), c=BZ(0.03))
    BU(T(206), 'shiver', 'street', 'window_close', STO, cx=980, cy=560, scale=1.5, turn=0.2, light=SH_PINK, act=_A(TFW(), lk(T(206), (900, 600))), c=BZ(0.02),
       sfx=[(WD(206, 'hard'), 'bone_crack', -2, 0, 'outside')])
    # (review: the monster busts' mfit clamp turned these ECUs into a static medium: mscale / meye frame them as ECUs)
    BU(T(208), 'shiver', 'street', 'window_close', STO, cx=960, cy=820, scale=2.3, light=SH_PINK, act=_A(TFW(), lk(T(208), (960, 600))), c=BZ(0.015),
       mscale=1.15, meye=470.0,
       hit=WD(208, 'red') + 0.05)
    BU(T(209), 'shiver', 'street', 'window_close', STO, cx=960, cy=520, scale=1.1, light=SH_PINK, act=_A(TFW(), lk(T(209), (960, 600))),
       mscale=0.56, meye=300.0, c=dict(mv='push', f=1.0, rate=0.0, x=960, y=560, z1=1.18),
       sfx=[(WD(209, 'drops'), 'jaw_drop', 0, 0, 'outside')])
    BU(T(211), 'shiver', 'street', 'window_close', STO, cx=960, cy=360, scale=1.7, light=SH_PINK, act=_A(TFW(), lk(T(211), (960, 600))), face_fix=False,
       mscale=0.6, meye=390.0, c=dict(mv='push', f=1.0, rate=0.0, x=960, y=560, z1=1.9))       # the push INTO the mouth: no throat, just dark, and teeth
    # 214-220 the uniform bulges, splits; legs punch out; click... they plant on the truck roof  (wide)
    trl = [WD(217, 'click'), WD(218, 'another'), WD(219, 'click'), WD(219, 'click', 1)]
    S(T(214), 'street', 'truck', st=STO, ppl=[SH(lean=0.18, act=_A(TFW(), lk(T(214), (1300, 700))))],     # (owner's-eyes: a medium on him, not a 7 s wide)
      cold=True, c=Z(2.3, 0.03, 925, 290, free=True), sfx=[(WD(215, 'splits'), 'uniform_tear', 0, 0, 'outside')])
    S(T(216), 'street', 'truck', st=STO, ppl=[SH(lean=0.18, clip='truck_window', act=_A(TFW(), lambda a, s: roof_legs(s.sp, trl)(a, s), lk(T(216), (960, 820))))],
      cold=True, c=Z(1.05, 0.0, 925, 420, x1=925, y1=360, f1=2.3, hit=[WD(216, 'punches')]), hit=WD(216, 'punches'), sfx=[(WD(216, 'punches'), 'leg_punch', 2, 0, 'outside')])
    S(T(217), 'street', 'house', st=dict(ST_DARK, truck_open=1.0), ppl=[SH(lean=0.18, act=_A(TFW(), lambda a, s: roof_legs(s.sp, trl)(a, s)))],
      c=Z(2.2, 0.0, 820, 520))
    # 221-223 And the song keeps playing. Sweet. Cheerful.  (hold on the full monster in the warm pink window)
    S(T(221), 'street', 'curb', st=STO, ppl=[SH(lean=0.15, act=_A(TFW(), lambda a, s: roof_legs(s.sp, [T(221) - 3] * 4)(a, s), lk(T(221), (1000, 1000))))],
      c=Z(1.0, 0.02))
    # 224-226 He pours out of the window. Head first. Legs last.
    def pour(a, s):
        v_ = scr(s.sp, 'truck_vendor'); w_ = scr(s.sp, 'truck_window'); g_ = scr(s.sp, 'truck_curb')
        a.pour_out(T(224) + 0.1, E(226) - T(224), sill_dy=-(v_[1] - w_[1]) * 0.55, ground_dy=g_[1] - v_[1])
    # (review B2: the kids stay in the set-up, the camera closer on the pour; he lands at LAND and closes in after the cut)
    S(T(224), 'street', 'truck', st=STO, ppl=[SH(clip=None, dorder=-3.0, act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), pour)),
                                              kid('adam', (-1.55, -7.0, FOOT), id='adam', face=(0.27, -8.6), expr='terror', carry=dict(who='lina', t0=-9.0, expr='fear'),
                                                  act=_A(lk(T(224), (900, 560)), lk(W(225, 'head') + 0.3, (930, 760), dur=0.4)))],
      cold=True, c=Z(1.3, 0.025, 960, 600), sfx=[(T(224) + 0.2, 'scuttle', -2, 0, 'outside', dict(surface='truck'))])
    LAND = (-0.55, -7.7, -0.48)
    # 227 I rip my foot out of the boot and run.  228 One sock.  229 Lina in my arms.
    S(T(227), 'street', 'truck', st=dict(STO, props=[('boot', -1.25, -7.15)]),
      ppl=[kid('adam_sock', (-1.25, -7.1, FOOT), id='adam', path=[(T(227) + 0.3, (-1.25, -7.1, FOOT)), (E(227) + 0.8, (-4.4, -6.7, FOOT))], run=True, surface='snow',
               expr='terrified_call', carry=dict(who='lina', t0=-9.0, expr='fear')),
           P('shiver', LAND, light=SH_PINK, talk=False, breath=False, face=(-3.0, -7.0),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.75),
                    lambda a, s: a.scuttle(T(227) + 0.35, T(228) + 0.4, _line(s.sp, LAND, (-2.2, -7.25, FOOT)), None), lk(T(227), ('adam', 'head'))))],
      cold=True, c=Z(1.2, 0.02, 940, 620), sfx=[(T(227) + 0.2, 'boot_rip', 0, 0, 'outside')])
    # (he cuts up the walk and veers right into the yard: he must NOT reach the door yet, he ducks under him there at L242)
    # (review B2: reversed, from our porch back to the street: Adam runs at us up the walk, HE scuttles after him from the kerb)
    S(T(228), 'street', 'door', st=dict(STO, props=[('mitten', -1.75, -3.6)], door_open=True), cam=cm((-0.35, -1.2, 1.25), (-1.9, -6.8, 0.7), 1000),
      ppl=[kid('adam_sock', (-3.55, -6.9, FOOT), id='adam', path=[(T(228) - 0.15, (-3.55, -6.9, FOOT)), (E(229) + 0.3, (0.1, -3.75, FOOT))], run=True, surface='snow', expr='terror',
               carry=dict(who='lina', t0=-9.0, expr='fear')),
           P('shiver', (-3.0, -7.9, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(-1.0, -2.6),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.75),
                    lambda a, s: a.scuttle(T(228) - 0.2, E(229) + 0.6, _line(s.sp, (-3.0, -7.9, FOOT), (-2.4, -5.0, FOOT)), None), lk(T(228), ('adam', 'head'))))],
      cold=True, c=Z(1.0, 0.02))
    # 230-233 Legs stab the snow. One spears my coat. I tear free. Another pries at Lina.
    yc = cm((3.5, -5.6, 0.45), (0.2, -3.9, 0.45), 1000)      # (review: inside the fence, low and close: the stabs read)
    adam_run = lambda t0, t1, a0, a1, **k: kid('adam_sock', a0, id='adam', path=[(t0, a0), (t1, a1)], run=True, surface='snow', expr='terror',
                                               carry=dict(who='lina', t0=-9.0, expr='fear'), **k)
    S(T(230), 'street', 'yard', st=dict(ST_DARK), cam=yc,
      ppl=[adam_run(T(230) - 0.2, E(233) + 0.5, (0.0, -3.8, FOOT), (3.2, -3.0, FOOT)),
           P('shiver', (-2.4, -4.6, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(3.0, -3.2),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.75), lambda a, s: a.scuttle(T(230) - 0.2, E(233) + 0.5, _line(s.sp, (-2.4, -4.6, FOOT), (1.4, -4.0, FOOT)), None),
                    lambda a, s: a.leg_to(WD(230, 'stab'), 0, lambda t: (s.A['adam'].where(t, 'foot_l')[0] - 40, s.A['adam'].where(t, 'foot_l')[1]), dur=0.15, hold=0.25, back=0.25),
                    lambda a, s: a.leg_to(WD(230, 'snow'), 6, lambda t: (s.A['adam'].where(t, 'foot_r')[0] + 50, s.A['adam'].where(t, 'foot_r')[1]), dur=0.15, hold=0.25, back=0.25),
                    lambda a, s: a.leg_to(WD(231, 'spears'), 2, lambda t: s.A['adam'].where(t, 'hip'), dur=0.18, hold=max(0.2, WD(232, 'tear') - WD(231, 'spears')), back=0.3, ev='leg_spear_coat'),
                    lambda a, s: a.leg_to(WD(233, 'pries'), 4, lambda t: s.A['adam'].where(t, 'chest'), dur=0.25, hold=0.6, back=0.4, ev='leg_pry')))],
      cold=True, c=Z(1.0, 0.02), sfx=[(WD(232, 'tear'), 'cloth_tear', 0, 0, 'outside')])
    S(T(231), 'street', 'yard', st=dict(ST_DARK), cam=cm((4.7, -5.7, 0.5), (2.0, -3.6, 0.5), 1050),
      ppl=[adam_run(T(230) - 0.2, E(233) + 0.5, (0.0, -3.8, FOOT), (3.2, -3.0, FOOT)),
           P('shiver', (-2.4, -4.6, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(3.0, -3.2),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.75), lambda a, s: a.scuttle(T(230) - 0.2, E(233) + 0.5, _line(s.sp, (-2.4, -4.6, FOOT), (1.4, -4.0, FOOT)), None),
                    lambda a, s: a.leg_to(WD(231, 'spears'), 2, lambda t: s.A['adam'].where(t, 'hip'), dur=0.18, hold=max(0.2, WD(232, 'tear') - WD(231, 'spears')), back=0.3, ev='leg_spear_coat'),
                    lambda a, s: a.leg_to(WD(233, 'pries'), 4, lambda t: s.A['adam'].where(t, 'chest'), dur=0.25, hold=0.6, back=0.4, ev='leg_pry')))],
      cold=True, c=Z(1.0, 0.02, hit=[WD(231, 'spears')]))
    # 234 He can't take her while I'm holding her.  235 So he wants me to let go.
    BU(T(234), 'adam_sock', 'street', 'yard', dict(ST_DARK), cx=900, cy=600, scale=0.9, light=dict(NIGHT, rim_a=110), expr='terror', cold=True,
       busts=[dict(who='lina', cx=1180, cy=760, scale=0.7, expr='fear', light=NIGHT, act=_A(lk(T(234), (900, 500))))], act=_A(lk(T(234), (1500, 400))), c=BZ(0.02))
    BU(T(235), 'shiver', 'street', 'yard', dict(ST_DARK), cx=960, cy=600, scale=1.0, light=SH_NIGHT,
       act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), lambda a, s: a.jaw_gape(T(235), E(235) + 1), lk(T(235), (960, 900))), c=BZ(0.03))
    # 236-238 He scuttles along our fence. Over Dad's car. Up onto our roof.
    def scut(a, s, t0, t1, pts):
        sp_ = s.sp
        P_ = [scr(sp_, q) for q in pts]
        L_ = [0.0]
        for p0, p1 in zip(P_, P_[1:]): L_.append(L_[-1] + math.hypot(p1[0] - p0[0], p1[1] - p0[1]))

        def path(u):
            d = u * L_[-1]
            for j in range(len(P_) - 1):
                if d <= L_[j + 1] or j == len(P_) - 2:
                    w = clamp((d - L_[j]) / max(1e-6, L_[j + 1] - L_[j]))
                    return (lerp(P_[j][0], P_[j + 1][0], w), lerp(P_[j][1], P_[j + 1][1], w))
            return P_[-1]
        a.place(*P_[0])
        a.scuttle(t0, t1, path, None, lift=40.0)
    S(T(236), 'street', 'yard', st=dict(ST_DARK),
      ppl=[P('shiver', (1.7, -6.3, 0.5), light=SH_NIGHT, talk=False, breath=False, face=(6.0, -6.3), dorder=-0.5,
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.7), lambda a, s: scut(a, s, T(236) - 0.1, E(237) + 0.2, [(1.7, -6.3, 0.5), 'fence4', 'car_hood', 'car_roof'])))],
      c=Z(1.9, 0.02, 1000, 560),        # (review: fence2-3 run behind the truck at A: the run starts past it, framed close)
      sfx=[(T(236) + 0.2, 'scuttle', 0, -0.4, 'outside', dict(surface='fence', dur=1.6)), (WD(237, 'car') - 0.1, 'scuttle', 0, 0.3, 'outside', dict(surface='car'))])
    S(T(238), 'street', 'roof', st=dict(ST_DARK),
      ppl=[P('shiver', 'eave', light=SH_NIGHT, talk=False, breath=False, face=(-2.1, -0.3),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.7), lambda a, s: scut(a, s, T(238), E(238) + 0.3, ['eave', 'roof_edge_door'])))],
      c=Z(1.15, 0.02, 1200, 190, free=True), sfx=[(T(238) + 0.1, 'scuttle', -2, 0, 'outside', dict(surface='roof', dur=1.2))])
    # 239-241 And drops. Right in front of our door. Jaw hanging.
    S(T(239), 'street', 'door', st=dict(ST_DARK, props=MIT),
      ppl=[P('shiver', 'drop', light=SH_NIGHT, talk=False, breath=False, face=(-2.1, -8.0), act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_lift=80.0),
                                                                                                   lambda a, s: a.drop_to(WD(239, 'drops') - 0.1, 0.4, from_dy=-650.0),
                                                                                                   lambda a, s: a.jaw_gape(WD(239, 'drops') + 0.6, E(241) + 1)))],
      c=Z(1.0, 0.02, hit=[WD(239, 'drops') + 0.3]), hit=WD(239, 'drops') + 0.3, sfx=[(WD(239, 'drops') + 0.3, 'leg_stab_snow', 2, 0, 'outside', dict(n=8))])
    BU(T(241), 'shiver', 'street', 'door', dict(ST_DARK), cx=960, cy=560, scale=1.1, light=SH_NIGHT, mscale=0.26, meye=320.0,
       act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), lambda a, s: a.jaw_gape(T(241) - 1, E(241) + 2), lk(T(241), (960, 900))), c=BZ(0.025))
    # 242 I duck under him, get inside, and slam the door.
    S(T(242), 'street', 'door', st=dict(ST_DARK, props=MIT, door_open=True), cam=cm((-1.4, -6.0, 0.6), (-2.1, -0.8, 0.9), 900),
      ppl=[P('shiver', 'drop', light=SH_NIGHT, talk=False, breath=False, face=(-2.1, -8.0), dorder=-0.3,
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_lift=80.0), lambda a, s: a.jaw_gape(T(242) - 2, E(242) + 1))),
           kid('adam_sock', (-1.4, -3.0, FOOT), path=[(T(242), (-1.4, -3.0, FOOT)), (T(242) + 0.6, (-1.9, -1.75, -0.33)), (WD(242, 'inside'), (-2.1, -0.2, 0.0))],
               run=True, surface='snow', expr='terror', carry=dict(who='lina', t0=-9.0, expr='fear'),
               act=_A(lambda a, s: a._add(T(242), WD(242, 'inside'), _duck(T(242) + 0.2, WD(242, 'inside')))))],
      cold=True, c=Z(1.0, 0.02))
    tsm = WD(242, 'slam')
    S(W(242, 'slam'), 'hall', 'door', st=dict(HALL_BLACK, door=lambda t: 70.0 * (1 - ease_in_cubic(clamp((t - (tsm - 0.25)) / 0.25)))), cold=True,
      c=Z(1.2, 0.02, 960, 600, hit=[tsm]), sfx=[(tsm, 'door_slam', 2, 0, 'inside')])
    # 243 One leg plucks Lina's mitten from the snow.
    mx = (-1.75, -3.6, -0.15)                                  # where her mitten lies (the prop): the leg spears it there

    def pluck(a, s):
        a.leg_to(T(243) + 0.3, 1, scr(s.sp, mx), dur=0.3, hold=0.2, back=None)
        a.leg_to(T(243) + 0.8, 1, (scr(s.sp, mx)[0] + 120, scr(s.sp, mx)[1] - 420), dur=0.8, hold=3.0, back=None, ev='leg_lift')
    for t_, pr in ((T(243), [('mitten', -1.75, -3.6)]), (T(243) + 0.6, [])):       # the same set-up: at the spear the ground mitten
        S(t_, 'street', 'door', st=dict(ST_DARK, props=pr), cam=cm((-0.6, -4.6, 0.4), (-2.0, -1.4, 0.4), 1000),   # goes onto his leg tip
          ppl=[P('shiver', 'drop', light=SH_NIGHT, talk=False, breath=False, face=(-2.05, -1.6), act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_lift=60.0), pluck,
                                                                                                        lk(T(243), mx)),
                 extras=[held_mitten('leg1', t0=T(243) + 0.6)])],
          c=Z(1.0, 0.0), sfx=[(T(243) + 0.6, 'leg_stab_snow', -4, 0, 'outside')] if pr else [])
    # 244-245 Onto his string. Saving her a place.
    IN(T(244), 'mittens', lambda u: dict(lina=u + T(244) >= WD(244, 'string') - 0.1), c=dict(mv='push', rate=0.02))
    IN(T(245), 'mittens', dict(lina=True), motion=lambda u: (-700 * ease_in_out(clamp(u / 0.8)), 0.0, 1.0 * ease_in_out(clamp(u / 0.8)), 0.0), c=dict(mv='hold'))
    # 246 I grab the radio.  247 "Dad!"  248 Static.  249 And bells.
    # 246 I grab the radio: the bust brings it up (a lone insert hand in the dark read as floating)
    BU(T(246), 'adam_sock', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='shout', cold=True, act=_A(radio(T(246) + 0.15, E(249) + 0.5, 1)),
       c=BZ(0.03), sfx=[(T(246) + 0.15, 'radio_grab', -4, 0, 'close')])
    RIN(T(248), dict(talk=0.0, static=1.0), 'adam_sock', cut='static', c=dict(mv='push', rate=0.03), sfx=[(T(248), 'radio_static', 0, 0, 'close', dict(dur=1.5))])
    RIN(T(249), lambda u: dict(talk=0.5 + 0.5 * math.sin(u * 30), static=0.9), 'adam_sock', motion=lambda u: (0.0, 0.0, 0.4, 0.0), c=dict(mv='hold'),
       sfx=[(WD(249, 'bells'), 'radio_bells', -2, 0, 'close')])
    # 250-252 Her fingertips are white. Waxy. I don't rub them.
    IN(T(250), 'fingers', dict(waxy=1.0), c=dict(mv='push', rate=0.03))
    IN(T(251), 'fingers', dict(waxy=1.0), motion=lambda u: (0.0, 60.0, 0.5 + 0.05 * u, 0.0), c=dict(mv='hold'))
    tr0 = T(252)
    IN(T(252), 'fingers', dict(waxy=1.0), c=dict(mv='push', rate=0.02),
       hands=[dict(who='adam_sock', fn=slide(tr0, tr0 + 0.5, (1500, 1300), (1250, 820), -130, -140, extra=lambda t, r: (r[0] + 160 * ease_in_out(clamp((t - tr0 - 0.75) / 0.4)), r[1] + 120 * ease_in_out(clamp((t - tr0 - 0.75) / 0.4)), r[2], r[3])),
                   size=280, shape='open', side=1, sleeve_from=(1800, 1500))])
    FA_KEY = dict(rim='#ffb0d0', rim_a=160, side=-1, key=0.08)     # (owner's-eyes: the first aid lit: pink through the curtains, brighter)
    # 253 I tuck them under my arms.  254-255 Wet socks off. Dry ones on.  256 Blanket around her middle.
    S(T(253), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam_sock', light=FA_KEY,  kind='seat', id='adam', expr='fierce_kind', face=(2.84, 1.68),
                                                          act=_A(lk(T(253), ('lina', 'head')), lambda a, s: a.hold_close(T(253) + 0.2, None, -1))),
                                                     lina('couch_right', who='lina', light=FA_KEY,  kind='seat', id='lina', expr='sad', seed=2, face=(3.4, 1.68),
                                                          act=_A(reach(T(253) + 0.1, 1, ('adam', 'chest'), dur=0.4), reach(T(253) + 0.1, -1, ('adam', 'chest'), dur=0.4)))],
      cold=True, c=Z(2.6, 0.02, 1060, 640), post=dict(exposure=0.55))
    S(T(254), 'living', 'couch3q', st=LIV_NEST, ppl=[lina('couch_right', who='lina_pj', light=FA_KEY,  kind='seat', id='lina', expr='sad', seed=2),
                                                     adam((3.0, 2.35, 0.0), who='adam_sock', light=FA_KEY,  kind='kneel', id='adam', face=(2.84, 1.68), expr='focused',
                                                          act=_A(reach(T(254) + 0.1, 1, ('lina', 'foot_l'), t1=E(255), dur=0.35), lk(T(254), ('lina', 'foot_l'))))],
      cold=True, cam=cm((4.9, 3.3, 0.55), (3.35, 1.9, 0.25), 1500), c=Z(1.0, 0.02), post=dict(exposure=0.55), sfx=[(T(254) + 0.4, 'sock_pull', -8, 0, 'inside'), (T(255) + 0.3, 'sock_pull', -8, 0, 'inside')])
    S(T(256), 'living', 'couch3q', st=LIV_NEST, ppl=[lina('couch_right', who='lina_pj', light=FA_KEY,  kind='seat', expr='sad', seed=2),
                                                     adam((3.0, 2.35, 0.0), who='adam_sock', light=FA_KEY,  kind='kneel', id='adam', face=(2.84, 1.68), expr='fierce_kind',
                                                          act=_A(reach(T(256) + 0.1, 1, (2.84, 1.8, 0.65), dur=0.45), reach(T(256) + 0.1, -1, (2.9, 1.55, 0.65), dur=0.45)))],
      cold=True, acts=nest_blanket(('lina',), c='#45332c', c2='#5e4639', t_in=T(256) + 0.55, under=('adam',)), c=Z(2.5, 0.02, 1060, 700), post=dict(exposure=0.55),
      sfx=[(T(256) + 0.3, 'blanket_wrap', -6, 0, 'inside')])
    # 257 Zipped inside my coat with me.  258-259 Then she shivers. Hard.  260-262 "Good," I whisper. "Shivering means you're fighting."
    two_shot = lambda t, lina_act=None, sc=0.85: BU(t, 'adam_sock', 'living', 'couch3q', LIV_NEST, cx=840, cy=560, scale=sc, turn=0.3, light=PINK_D, expr='fierce_kind',
                                                     cold=True, busts=[dict(who='lina', cx=1120, cy=700, scale=sc * 0.8, turn=-0.3, expr='sad', light=PINK_D, act=lina_act)],
                                                     act=_A(lk(t, (1120, 640))), c=BZ(0.015))
    two_shot(T(257), sc=0.85)
    BU(T(258), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sad', cold=True, act=_A(tremblef(WD(258, 'shivers'), None, 1.0)), c=BZ(0.02))
    BU(T(259), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=560, scale=1.35, light=PINK_D, expr='cry_shut', cold=True, act=_A(tremblef(T(259) - 1, None, 1.8)), c=BZ(0.02))
    two_shot(T(260), lina_act=_A(tremblef(T(258), None, 1.4)), sc=0.95)


def frozen_boot(t0, push=0.0, tug=None, z0=1.0, zr=None):
    """INSERT L197-198 (drawn over ic_insert('boot'), see W/handoff/requests.md sets 5): Adam's boot, side view, his jeans
    going into it, sunk in the snow with an ICE COLLAR frozen round it and frost creeping up; tug = (ta, tb) he pulls and
    it does not move (a strained jiggle, the ice cracks); push = zoom per second toward the ice."""
    import random as _rnd
    _g = _rnd.Random(1958); rnd = [_g.random() for _ in range(400)]

    def draw(pen, t):
        cv = pen.cv
        u = max(0.0, t - t0)
        sc = z0 * (1.0 + (push if zr is None else zr) * u)
        cv.save(); cv.translate(960, 660); cv.scale(sc, sc); cv.translate(-960, -660)
        pen.linear(rect(-400, -300, 2720, 1700), 0, -200, 0, 1200, [(0, '#24304e', 255), (0.55, '#5a6c98', 255), (1, '#aebbd8', 255)])
        pen.glow(1700, 80, 900, '#ff9ec8', 60)                               # his window's pink from behind, top right
        dy = 0.0; strain = 0.0
        if tug:
            ta, tb = tug
            strain = clamp((t - ta) / 0.2) * (1 - clamp((t - tb) / 0.25))
            dy = -7.0 * strain * (0.5 + 0.5 * math.sin(t * 46.0))
        # his jeans into the boot, the boot (toe left), the fur cuff, the laces
        pen.linear(rect(885, -40, 185, 300), 885, 0, 1070, 0, [(0, '#3c4d78', 255), (1, '#22304e', 255)])
        shaft = rrect(860, 255 + dy, 232, 470, 34)
        foot = rrect(690, 585 + dy, 410, 175, 82)
        boot = union(shaft, foot)
        pen.linear(boot, 700, 0, 1095, 0, [(0, '#6a4a3a', 255), (0.6, '#4a3228', 255), (1, '#2a1c18', 255)])
        pen.line(boot, 4.0, '#140c0a')
        pen.seg((1089, 300 + dy), (1089, 690 + dy), 6.0, '#ff9ec8', 110)                     # pink rim light
        cuff = rrect(842, 222 + dy, 266, 82, 38)
        pen.fill(cuff, '#d9d0c2'); pen.line(cuff, 3.0, '#6a6058')
        for i in range(26):
            pen.fill(oval(852 + rnd[i] * 246, 232 + dy + rnd[i + 40] * 62, 7, 5), '#b8ad9c', 200)
        for k in range(6):
            y_ = 330 + k * 46 + dy
            pen.seg((878, y_), (928, y_ + 30), 5.0, '#d8c8a8'); pen.seg((878, y_ + 30), (928, y_), 5.0, '#d8c8a8')
        # frost creeping up the leather: speckles below a rising line
        fl = 690 - 260 * clamp(u / 2.6)
        for i in range(120):
            x_ = 700 + rnd[i] * 395; y_ = 470 + rnd[i + 120] * 270
            if y_ > fl and (x_ > 862 or y_ > 595):
                pen.fill(oval(x_, y_ + dy, 3 + 4 * rnd[i + 200], 3 + 4 * rnd[i + 200]), '#eef6ff', 200)
        # the snow, up over the sole, a crust heaped against the boot
        pts = [(-400, 1500), (-400, 722)]
        for i in range(0, 25):
            x_ = -400 + i * 113
            rise = max(0.0, 1.0 - abs(x_ - 900) / 330.0)
            pts.append((x_, 722 - 70 * rise - 14 * rnd[i + 300]))
        pts += [(2320, 722), (2320, 1500)]
        snow = poly(pts)
        pen.linear(snow, 0, 640, 0, 1100, [(0, '#d2dcec', 255), (1, '#9eaccc', 255)])
        pen.line(snow, 3.0, '#8a9ac0', 180)
        for i in range(70):
            pen.fill(oval(rnd[i + 10] * 1920, 700 + rnd[i + 90] * 380, 2.5, 2.5), '#ffffff', 230)
        # the ice collar frozen round the ankle + icy spikes up the leather; cracks while he tugs
        col = rrect(812, 610, 310, 112, 46)
        pen.fill(col, '#bcd8f4', 140); pen.line(col, 4.0, '#e8f4ff', 200)
        pen.linear(rrect(830, 620, 274, 30, 14), 0, 620, 0, 650, [(0, '#ffffff', 160), (1, '#ffffff', 0)])
        for k in range(9):
            x_ = 830 + k * 33; h_ = 40 + 50 * rnd[k + 50]
            pen.fill(poly([(x_ - 10, 618), (x_ + 10, 618), (x_ + 2 * (rnd[k] - 0.5) * 8, 618 - h_)]), '#e6f4ff', 190)
        if tug and t > tug[0]:
            kc = clamp((t - tug[0]) / 0.5)
            for (a_, b_) in (((840, 650), (900, 700)), ((960, 615), (985, 690)), ((1060, 640), (1110, 700))):
                pen.seg(a_, (lerp(a_[0], b_[0], kc), lerp(a_[1], b_[1], kc)), 3.0, '#ffffff', 230)
        cv.restore()
    return lambda F, sh: Layer(0.5, draw, 'frozen_boot')


def _pull(t0, dx, dur=0.3, lift=0.0):
    """Lina yanked out of his reach into Adam's arms: her body slides toward Adam and up (lift) to where the carry
    takes her, so the hand-over to the carry does not pop."""
    def fn(P_, t):
        u = ease_in_out(clamp((t - t0) / dur)); P_.dx -= dx * u; P_.dy -= lift * u
        if lift: P_.turn *= 1.0 - u                    # she swings round to face out as he lifts her (the carry faces out)
    return fn


def _shrink_curve(t0, dur):
    """L386 (review: the shrink read as a 0.2 s pop): sh_m over the same span as shrink_back (its cues stay), but it
    lingers through 1.0 -> 0.9 where the head shrinks, so the shrink plays over about a second."""
    def fn(P_, t):
        x = clamp((t - t0) / max(0.1, dur))
        if t < t0: return
        if x < 0.5: m = lerp(1.0, 0.9, x / 0.5)      # the head shrinks between 0.98 and 0.9: spread evenly over ~1 s
        else: m = lerp(0.9, 0.0, ease_in_out((x - 0.5) / 0.5))
        P_.sh_m = m
    return fn


def _step_back(t0, dx):
    def fn(P_, t):
        u = ease_in_out(clamp((t - t0) / 0.6)); P_.dx -= dx * u
    return fn


def _duck(t0, t1):
    def fn(P_, t):
        u = math.sin(math.pi * clamp((t - t0) / max(0.1, t1 - t0)))
        P_.lean += 0.35 * u
    return fn


def _line(sp, a0, a1):
    p0, p1 = scr(sp, a0), scr(sp, a1)
    return lambda u: (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))


# ==================================================================================================== PART B (263-427)
# continuity (W/shotmap.md): power dead, frost inside, truck at A (monster) until 306, rolls to B 307-311 (vendor form again
# at 319-320, monster from 354, shrinks back 386, gone 388); Adam in one sock (`adam_sock`), Lina in her coat with bare hands
# (one mitten on his string, the other in our yard); the radio with Adam; the hatch shut until 294; towels in the gap 300+.
ST_B = dict(truck='B', blackout=True, our_smoke=0.0, smoke=0.0, kdoor_open=True, win=dict(his=0.0))          # truck at B (L310+)
STB_O = dict(ST_B, truck_open=1.0)
STO_B = dict(ST_DARK, truck='B', truck_open=1.0)                          # bust backgrounds at his window (B)
BATH = dict(phone=0.0)
HALL_PINK = dict(HALL_BLACK, pink=1.0)
KD = (1.4, -23.75)                                                         # Kessler's doorway (plan)


def shovel_fx(c='#c8402a'):
    """A snow shovel in both hands (the long handle from the upper hand through the lower one, the blade at the snow)."""
    def fx(pen, t, a):
        try:
            hl, hr = a.where(t, 'hand_l'), a.where(t, 'hand_r'); fy = max(a.where(t, 'foot_l')[1], a.where(t, 'foot_r')[1])
        except Exception:
            return
        up, lo = (hl, hr) if hl[1] < hr[1] else (hr, hl)
        dx, dy = lo[0] - up[0], lo[1] - up[1]
        if dy < 4: dx, dy = 0.3 * a.height * 0.2, a.height * 0.2
        k = clamp((fy - a.height * 0.03 - up[1]) / dy, 1.0, 3.5)
        tip = (up[0] + dx * k, up[1] + dy * k)
        w = max(1.5, a.height * 0.014)
        pen.seg((up[0] - dx * 0.12, up[1] - dy * 0.12), tip, w, '#7a5a3a'); pen.seg((up[0] - dx * 0.12, up[1] - dy * 0.12), tip, w * 0.35, '#a88a5a', 160)
        n = math.hypot(dx, dy) or 1.0; px, py = -dy / n, dx / n
        bw = a.height * 0.075
        bl = poly([(tip[0] + px * bw, tip[1] + py * bw), (tip[0] - px * bw, tip[1] - py * bw),
                   (tip[0] - px * bw + dx / n * bw * 1.1, tip[1] - py * bw + dy / n * bw * 1.1), (tip[0] + px * bw + dx / n * bw * 1.1, tip[1] + py * bw + dy / n * bw * 1.1)])
        pen.fill(bl, c); pen.line(bl, max(1.0, w * 0.5), '#1a1418')
        pen.fill(oval(tip[0] + dx / n * bw * 0.7, tip[1] + dy / n * bw * 0.5, bw * 0.8, bw * 0.3), '#f4f8ff', 220)
    return fx


def mug_fx(part='hand_r', s=1.0):
    """A cocoa mug in a hand (steaming: warm)."""
    def fx(pen, t, a):
        try: x, y = a.where(t, part)
        except Exception: return
        k = a.height * 0.035 * s
        m = rrect(x - k, y - k * 1.4, 2 * k, 2.1 * k, k * 0.25)
        pen.fill(m, '#c8402a'); pen.line(m, max(1.0, k * 0.1), '#1a1418')
        pen.fill(oval(x, y - k * 1.4, k * 0.95, k * 0.28), '#5a2e1a')
        for j in range(2):
            u = (t * 0.5 + j * 0.5) % 1.0
            pen.fill(oval(x + k * 0.4 * math.sin(t * 2 + j), y - k * (1.8 + 2.0 * u), k * (0.35 + 0.4 * u)), '#fff4e8', 110 * (1 - u), blur=k * 0.3)
    return fx


def cloak(ids, c='#6a3b52', c2='#8a5670', pull=None, hood=True):
    """acts: ONE big blanket over standing people (the crossing, the huddle): over their heads behind (hood) and round
    their shoulders down to the knees in front, faces clear; pull(t) -> (dx, dy) px: the hooked leg tugging it."""
    def acts(A, sh, sp):
        who = [k for k in ids if k in A]
        if not who: return []
        lays = [sh.I[k]['layer'] for k in sh.I if k in who or any(k in ALIAS.get(w, ()) for w in who)]

        def pts(t):
            out = []
            for k in who:
                a = A[k]
                try:
                    hx, hy = a.where(t, 'head'); cx, cy = a.where(t, 'chest'); px_, py_ = a.where(t, 'hip')
                    fy = max(a.where(t, 'foot_l')[1], a.where(t, 'foot_r')[1])
                except Exception:
                    continue
                out.append((cx, cy, hx, hy, lerp(py_, fy, 0.45), 0.17 * a.height, a.height))
            out.sort()
            return out

        def off(t):
            return pull(t) if pull else (0.0, 0.0)

        def front(pen, t):
            P_ = pts(t)
            if not P_: return
            ox, oy = off(t)
            xl = P_[0][0] - P_[0][5] * 1.2 + ox; xr = P_[-1][0] + P_[-1][5] * 1.2 + ox
            top = [(xl, P_[0][1] - 0.02 * P_[0][6] + oy)] + [(p[0] + ox * 0.6, p[1] - 0.03 * p[6] + oy * 0.5) for p in P_] + [(xr, P_[-1][1] - 0.02 * P_[-1][6] + oy)]
            bot = max(p[4] for p in P_)
            path = smooth(top + [(xr + 8 + ox * 0.3, bot), (xl - 8 + ox * 0.3, bot + 6)], True)
            pen.fill(path, c); pen.texture(path, 'fabric', 0.35, 'overlay', 0.6)
            for j in range(1, 5):
                x_ = lerp(xl, xr, j / 5.0)
                pen.seg((x_, min(p[1] for p in P_)), (x_ + 4, bot - 4), 1.6, c2, 150)
            pen.line(path, 2.2, '#140f1c', 200)

        def back(pen, t):
            if not hood: return
            P_ = pts(t)
            if not P_: return
            ox, oy = off(t)
            xl = P_[0][0] - P_[0][5] * 1.25 + ox; xr = P_[-1][0] + P_[-1][5] * 1.25 + ox
            top = min(p[3] - 0.085 * p[6] for p in P_) + oy
            mid = max(p[1] for p in P_)
            path = smooth([(xl, mid + 10), (xl + 0.15 * (xr - xl), top + 14), (0.5 * (xl + xr), top), (xr - 0.15 * (xr - xl), top + 14), (xr, mid + 10)], True)
            pen.fill(path, _mix_hex(c, '#000000', 0.25)); pen.line(path, 2.0, '#140f1c', 180)
        l0 = lays[0]
        dd = lambda t: min((l_.depth(t) if callable(l_.depth) else l_.depth) for l_ in lays) - 0.01
        o_ = [l_.order for l_ in lays]
        ov = lambda o, t: o(t) if callable(o) else o
        out = []
        for fn, nm, sgn in ((back, 'cloak_back', 1), (front, 'cloak', -1)):
            lay = Layer(dd(sh.t0), fn, nm, ref_depth=getattr(l0, 'ref_depth', None), blur=None)
            lay.depth = dd
            if sgn < 0: lay.order = lambda t: min(ov(o, t) for o in o_) - 0.02
            else: lay.order = lambda t: max(ov(o, t) for o in o_) + 0.02
            out.append(lay)
        return out
    return acts


def frosted_glass():
    """The frosted panel of our front door in front of a close-up (his long face behind it): a pink-lit veil, frost
    feathers, and the clear strip's dark frame bars above and below."""
    import random as _r
    g = _r.Random(5); pts = [(g.uniform(0, 1920), g.uniform(0, 1080), g.uniform(20, 90), g.uniform(0, 6.28)) for _ in range(60)]

    def draw(pen, t):
        pen.fill(rect(0, 0, 1920, 1080), '#f0dcea', 70)
        for (x, y, L, a) in pts:
            pen.seg((x, y), (x + L * math.cos(a), y + L * math.sin(a)), 2.0, '#ffffff', 90)
        pen.fill(rect(0, 0, 1920, 70), '#120c14', 230); pen.fill(rect(0, 1010, 1920, 70), '#120c14', 230)
    return Layer(0.8, draw, 'frosted_glass', blur=None)


def orange_sweep(t0, dur=2.4):
    """Dad's beacon passing: an orange light sweeping across the frame (through a window)."""
    def draw(pen, t):
        u = (t - t0) / dur
        if u <= 0 or u >= 1: return
        k = math.sin(u * math.pi)
        pen.glow(lerp(-200, 2100, u), 420, 900, '#ffa030', 190 * k)
        pen.fill(rect(0, 0, 1920, 1080), '#ff9030', 75 * k * (0.6 + 0.4 * abs(math.sin(t * 8.2))))
    return Layer(0.85, draw, 'orange_sweep', blur=None)


def sock_layer(x=1500, y=760, s=1.0, c='#f2a8c4'):
    """Lina's pink sock on the floor by the gap (the insert): her foot, the sock's ribbed cuff."""
    def draw(pen, t):
        dx = 6 * math.sin(t * 7.0)                     # she flinches back a little, trembling
        f = rrect(x + dx - 140 * s, y - 50 * s, 300 * s, 120 * s, 55 * s)
        pen.fill(moved(f, 0, 14), '#000000', 90, blur=10); pen.fill(f, c); pen.line(f, 3, '#1a1418')
        cuff = rrect(x + dx + 110 * s, y - 70 * s, 90 * s, 150 * s, 22 * s)
        pen.fill(cuff, '#e590b0'); pen.line(cuff, 3, '#1a1418')
        for j in range(4): pen.seg((x + dx + (122 + 20 * j) * s, y - 60 * s), (x + dx + (122 + 20 * j) * s, y + 70 * s), 2, '#c87090', 200)
    return lambda F_, sh: Layer(0.6, draw, 'sock')


def _mix_hex(a, b, k):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(lerp(x, y, k)) for x, y in zip(ca, cb))


def gap_leg(sp, t0, t1, reach_px=(420.0, 120.0), back=None, at='gap'):
    """Under the bathroom door: a needle-thin brown jointed leg tip sliding in over the floor (frost on the joint),
    feeling side to side; back = time it pulls out."""
    x0, y0 = scr(sp, at)

    def draw(pen, t):
        u = ease_in_out(clamp((t - t0) / max(0.1, t1 - t0)))
        if back is not None: u *= 1.0 - ease_in_cubic(clamp((t - back) / 0.35))
        if u <= 0.01: return
        feel = math.sin((t - t0) * 2.4) * 30.0 * clamp((t - t1) / 0.4)
        tip = (x0 + reach_px[0] * u, y0 + reach_px[1] * u + feel)
        j = (x0 + reach_px[0] * u * 0.55, y0 + reach_px[1] * u * 0.4 - 18)
        pen.line(smooth([(x0 - 30, y0 - 4), j, tip], False), 9.0, '#5a3a26')
        pen.line(smooth([(x0 - 30, y0 - 4), j, tip], False), 2.5, '#8a6448', 200)
        pen.fill(oval(j[0], j[1], 9, 7), '#3a2418'); pen.fill(oval(j[0], j[1] - 4, 8, 4), '#e8f4ff', 220)
        pen.seg((lerp(j[0], tip[0], 0.7), lerp(j[1], tip[1], 0.7)), tip, 3.0, '#e3e9ee')
    return plane_layer(sp, at, draw, 'gap_leg', front=0.05)


def jleg(pen, pts, w0=24.0, hook=False, rim=None):
    """Review (the leg read as a thin rope): ONE jointed spider leg in screen px, root -> joints -> needle tip: tapered
    dark-brown chitin segments with a lit edge and an outline, dark ball joints with frost crusted on top, the last
    segment a needle fading from brown to pale (hook=True curls the tip into a hook)."""
    n = len(pts) - 1
    for j in range(n):
        a_, b_ = pts[j], pts[j + 1]
        wa, wb = w0 * (1.0 - 0.62 * j / n), w0 * (1.0 - 0.62 * (j + 1) / n)
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        L_ = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L_, dx / L_
        if j == n - 1:                                     # the needle: brown into pale, to a point
            mid = (lerp(a_[0], b_[0], 0.45), lerp(a_[1], b_[1], 0.45))
            q = poly([(a_[0] + nx * wa * 0.5, a_[1] + ny * wa * 0.5), (mid[0] + nx * wa * 0.32, mid[1] + ny * wa * 0.32), b_,
                      (mid[0] - nx * wa * 0.32, mid[1] - ny * wa * 0.32), (a_[0] - nx * wa * 0.5, a_[1] - ny * wa * 0.5)], True)
            pen.fill(q, '#4a3020'); pen.line(q, 2.0, '#140c08')
            pen.seg(mid, b_, max(2.0, wa * 0.22), '#dfe6ec', 235)
            if hook:
                pen.line(smooth([b_, (b_[0] + 0.5 * wa + 6, b_[1] + 0.9 * wa + 8), (b_[0] + 1.3 * wa + 12, b_[1] + 0.4 * wa)], False), max(3.0, wa * 0.25), '#dfe6ec')
            continue
        q = poly([(a_[0] + nx * wa * 0.5, a_[1] + ny * wa * 0.5), (b_[0] + nx * wb * 0.5, b_[1] + ny * wb * 0.5),
                  (b_[0] - nx * wb * 0.5, b_[1] - ny * wb * 0.5), (a_[0] - nx * wa * 0.5, a_[1] - ny * wa * 0.5)], True)
        pen.fill(q, '#5a3a26')
        pen.seg((a_[0] + nx * wa * 0.22, a_[1] + ny * wa * 0.22), (b_[0] + nx * wb * 0.22, b_[1] + ny * wb * 0.22), max(1.5, wa * 0.18), '#9a7454', 210)
        if rim: pen.seg((a_[0] - nx * wa * 0.38, a_[1] - ny * wa * 0.38), (b_[0] - nx * wb * 0.38, b_[1] - ny * wb * 0.38), max(1.2, wa * 0.1), rim, 170)
        pen.line(q, 2.2, '#140c08')
        for u in (0.86, 0.93):                             # telescoping rings near the far end
            cx_, cy_ = lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u); w_ = lerp(wa, wb, u) * 0.5
            pen.seg((cx_ + nx * w_, cy_ + ny * w_), (cx_ - nx * w_, cy_ - ny * w_), 1.6, '#2a1810', 200)
    for j in range(1, n):                                  # ball joints, frost on top, a short icicle
        x_, y_ = pts[j]; r_ = w0 * (1.0 - 0.62 * j / n) * 0.62
        pen.fill(oval(x_, y_, r_, r_ * 0.9), '#3a2418'); pen.line(oval(x_, y_, r_, r_ * 0.9), 1.8, '#140c08')
        pen.fill(oval(x_, y_ - r_ * 0.55, r_ * 0.95, r_ * 0.42), '#eef6ff', 230)
        pen.fill(poly([(x_ - r_ * 0.25, y_ + r_ * 0.6), (x_ + r_ * 0.2, y_ + r_ * 0.6), (x_, y_ + r_ * 1.6)], True), '#e8f2ff', 200)


def blanket_hook(sp, t0, tgt, src, knee=None, w0=30.0):
    """A jointed leg (root src: screen px or f(t) -> px, e.g. his body) hooking the blanket at tgt(t) and PULLING (L355);
    also the leg stabbing down between the kids (L296-297)."""
    def draw(pen, t):
        u = ease_out_cubic(clamp((t - t0) / 0.25))
        if u <= 0: return
        s_ = src(t) if callable(src) else src
        tx, ty = tgt(t)
        tip = (lerp(s_[0], tx, u), lerp(s_[1], ty, u))
        if knee is None:
            kn = (lerp(s_[0], tip[0], 0.45) + 40, min(s_[1], tip[1]) - 170)
        else:
            k_ = knee(t) if callable(knee) else knee
            kn = (lerp(k_[0], tip[0], 0.15), lerp(k_[1], tip[1], 0.15))
        an = (lerp(kn[0], tip[0], 0.55) + 0.08 * (tip[1] - kn[1]), lerp(kn[1], tip[1], 0.55) - 0.08 * (tip[0] - kn[0]))
        jleg(pen, [s_, kn, an, tip], w0, hook=True, rim='#ff9ccc')
    lay = Layer(0.85, draw, 'hook_leg', blur=None)
    lay.order = -99.0
    return lay


# review (the morning read grey-mauve, not warm): a golden sunrise grade for the morning after
_epost.GRADES.setdefault('ic_morning_gold', dict(exposure=0.06, contrast=1.03, pivot=0.26, gamma=1.06, sat=1.2, wb=(1.13, 1.0, 0.83), floor='#18100a',
                                                bloom=0.9, bloom_thr=228, vignette=0.4, grain=0.35, shoulder=0.55))


def door_glow(sp, dx, yf, t0, who_x=-0.12, w=0.9, h=2.05, z0=0.0):
    """A neighbour's front door opening (L380 "Doors open."): the warm lit doorway widening as the door swings in, and a
    neighbour's dark figure stepping into it (the set's neighbour doors cannot open)."""
    def draw(pen, t):
        u = ease_in_out(clamp((t - t0) / 0.5))
        if u <= 0.01: return
        xa = dx - 0.5 * w
        q = [FM_scr(sp, (xa, yf, z0)), FM_scr(sp, (xa + w * u, yf, z0)), FM_scr(sp, (xa + w * u, yf, z0 + h)), FM_scr(sp, (xa, yf, z0 + h))]
        pen.glow(0.5 * (q[0][0] + q[1][0]), 0.5 * (q[0][1] + q[2][1]), 2.2 * abs(q[2][1] - q[0][1]), '#ffc888', 70 * u)
        pen.fill(poly(q, True), '#ffd8a0', 245)
        pen.fill(poly([q[0], q[1], (q[1][0] + 0.6 * (q[1][0] - q[0][0]), q[1][1] + 0.25 * abs(q[2][1] - q[1][1])), (q[0][0] - 0.2 * (q[1][0] - q[0][0]), q[0][1] + 0.25 * abs(q[2][1] - q[1][1]))], True), '#ffd8a0', 90 * u)
        k = clamp((t - t0 - 0.35) / 0.4)
        if k > 0:                                          # a neighbour in the doorway (coat over pyjamas), stepping out
            fx_, fy = FM_scr(sp, (dx + who_x, yf + 0.1 * k, z0))
            hx, hy = FM_scr(sp, (dx + who_x, yf + 0.1 * k, z0 + 1.72))
            hh = fy - hy
            body = rrect(fx_ - 0.15 * hh, hy + 0.17 * hh, 0.3 * hh, 0.83 * hh, 0.08 * hh)
            pen.fill(body, '#1a1418', 235 * k); pen.fill(oval(fx_, hy + 0.08 * hh, 0.08 * hh, 0.095 * hh), '#1a1418', 235 * k)
    return plane_layer(sp, (dx, yf + 0.05, z0), draw, 'door_glow', front=0.05)


def FM_scr(sp, p):
    return scr(sp, p)


def mitten_fall(sp, at, t_land, h_px=520.0):
    """Lina's yellow mitten falling into the snow and landing (L389), a puff of powder where it lands."""
    s0 = spot_of(sp, at)

    def draw(pen, t):
        x, y = scr(sp, at)
        sz = max(6.0, 0.075 * s0.ppm)
        u = clamp((t - (t_land - 0.3)) / 0.3)
        if u <= 0: return
        yy = y - h_px * (1 - u * u); rot = 140 * (1 - u) + 12
        k = clamp((t - t_land) / 0.6)
        if t >= t_land:
            pen.fill(oval(x, y + 0.3 * sz, 1.8 * sz, 0.4 * sz), '#5a6a9a', 80, blur=6)
            for j in range(7):
                a_ = j / 7.0 * math.pi
                pen.fill(oval(x + math.cos(a_) * sz * (1.2 + 2.4 * k), y - math.sin(a_) * sz * 1.4 * k, 0.35 * sz * (1 - k)), '#ffffff', 220 * (1 - k))
        _mitten_screen(pen, x, yy - 0.5 * sz * (1 - u), sz, rot)
        if t >= t_land: pen.fill(oval(x, y + 0.9 * sz, 1.4 * sz, 0.45 * sz), '#eef4ff', 200)       # half sunk in the powder
    return plane_layer(sp, at, draw, 'mitten_fall', front=0.05)


def legs_front(sid='shiver', over=('adam', 'lina'), light=None):
    """acts: his spider legs drawn AGAIN in front of the people he cages (the cast's sh_legs_only pass), so the legs arch
    OVER them instead of splaying behind (review C2 M9)."""
    import copy as _copy

    def acts(A, sh, sp):
        if sid not in A or sid not in sh.I: return []
        a = A[sid]; L0 = sh.I[sid]['layer']
        lays = [sh.I[k]['layer'] for k in over if k in sh.I]
        lt = light or SH_NIGHT

        def draw(pen, t):
            P_ = _copy.copy(a.at(t)); P_.sh_legs_only = 1.0
            CH.draw(pen, a.who, a.x0, a.y0, a.height, P_, light=lt, t=t)
        lay = Layer(L0.depth, draw, 'legs_front', ref_depth=L0.ref_depth, blur=None)
        ov = lambda o, t: o(t) if callable(o) else o
        o_ = [l_.order for l_ in lays] or [L0.order]
        lay.order = lambda t: min(ov(o, t) for o in o_) - 0.05
        return [lay]
    return acts


def blanket_fg(y0=860.0, c='#6a3b52', c2='#8a5670', lift=None):
    """A bust's foreground: the ONE big blanket over the kids' shoulders (the crossing): knit fabric from the frame bottom up
    over the shoulders, rising at both edges where it is held round them (review: the blanket vanished in the busts)."""
    def draw(pen, t):
        dy = lift(t) if lift else 0.0
        top = [(-40, y0 - 250 + dy), (300, y0 - 60 + dy), (700, y0 + 10 + dy), (1220, y0 + 25 + dy), (1640, y0 - 40 + dy), (1960, y0 - 230 + dy)]
        path = smooth(top + [(1960, 1120), (-40, 1120)], True)
        pen.fill(moved(path, 0, -10), '#05040a', 110, blur=16)
        pen.fill(path, c); pen.texture(path, 'fabric', 0.35, 'overlay', 0.6)
        for j in range(1, 7):
            x_ = lerp(-40, 1960, j / 7.0)
            pen.seg((x_, y0 + 40 + dy), (x_ + 18, 1100), 2.2, c2, 150)
        pen.line(smooth(top, False), 9.0, c2, 220); pen.line(path, 2.6, '#140f1c', 210)
    return Layer(0.95, draw, 'blanket_fg', blur=None)


def cab_bg(t0=0.0):
    """Dad's bust background: inside the plow cab at night: dark cab, the side window with snow streaking past and the
    street lights sliding by, the orange beacon pulsing on the snow outside (review: Dad busts sat on a black void)."""
    import random as _r
    g = _r.Random(9); fl = [(g.uniform(0, 1), g.uniform(0, 1), g.uniform(0.5, 1.0)) for _ in range(70)]

    def draw(pen, t):
        pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, ['#2a1c14', '#0a0706'])
        win = rrect(120, 150, 1680, 640, 40)
        pen.linear(win, 0, 150, 0, 790, ['#1a2a4a', '#3a4a6a'])
        k = 0.5 + 0.5 * math.sin(t * 8.2)
        pen.fill(rect(120, 600, 1680, 190), '#c8d4ec', 200)                             # the snow outside, lit
        pen.fill(rect(120, 600, 1680, 190), '#ff9030', 70 * k)
        for j in range(3):                                                            # street lights sliding past
            x_ = (1900 - ((t - t0) * 420 + j * 700) % 2100)
            pen.glow(x_, 330, 70, '#ffd8a0', 110)
        for (x, y, s_) in fl:                                                         # snow streaks
            xx = 120 + ((x * 1680 - (t - t0) * 900 * s_) % 1680); yy = 150 + ((y * 640 + (t - t0) * 160 * s_) % 640)
            pen.seg((xx, yy), (xx + 26 * s_, yy - 5 * s_), 2.2 * s_, '#ffffff', 170)
        pen.glow(1500, 700, 520, '#ff9030', 90 * k)
        pen.line(win, 26, '#120c0a'); pen.line(win, 4, '#3a2a20')
        pen.seg((980, 150), (980, 790), 22, '#120c0a')
    return draw


def _beckon(t0, t1):
    """His glove curls 'come here' beside the window (slow, cheerful)."""
    return lambda a, s: a.slow_wave(t0, t1, 1)


# cast round 3 (film pass): in the far street wides (house / kessler views) his face would be 2-3 % of the frame, under the
# 8 % bar, so those shots show only his glowing window; every shot that is ABOUT him frames him at >= 8 %.
def SHB(act=None, m=0.0, lean=0.18, legs=False, **k):
    """Him in his window at B (vendor m=0 / monster m=1, legs planted on the roof)."""
    acts = [pose(-9, None, 0.1, sh_m=m)]
    if legs: acts.append(lambda a, s: roof_legs(s.sp, [s.t0 - 3.0] * 4)(a, s))
    if act: acts.append(act)
    return SH(lean=lean, act=_A(*acts), **k)


def kess(at, who='kessler_out', **k):
    return P(who, at, **k)


def plan_partb(F):
    plan_rule5(F)
    plan_rule6(F)
    plan_twist(F)
    plan_rule7(F)
    plan_dawn(F)
    plan_outro(F)


# ==================================================================================================== RULE 5: MOM AT THE DOOR (263-285)
def plan_rule5(F):
    RULE(T(263), 5)
    IN(T(267), 'card', dict(time_='Three-oh-five.', temp=None), c=dict(mv='push', rate=0.015))
    # 268 Pounding on the door.  (her shadow on the frosted glass, fists)
    mom_sil = lambda t0, n=5: P('shiver_mom', (-2.1, -0.45, 0.0), face=(-2.1, 2.0), sil=0.5, sil_rim='#ff9ec8', sil_rim_a=0.25, dorder=-6.0,
                                light=PINK, talk=False, breath=False, act=_A(lambda a, s: a.knock(t0, n, 0.2, strength=1.6)))
    tp = T(268) + 0.1
    S(T(268), 'hall', 'doorclose', st=HALL_PINK, ppl=[mom_sil(tp, 5)], c=Z(1.0, 0.02, shake=2.0),
      sfx=[(tp + 0.2 * k, 'door_pound', 0 if k % 2 else -3, 0, 'inside', dict(n=1, index=k)) for k in range(5)])
    # 269 S mimic "Adam! It's Mom! They let me off early! Open up, baby, I'm freezing!"
    BU(T(269), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=960, cy=580, scale=0.72, light=PINK_D, cold=False,
       act=_A(lk(T(269), (960, 760)), lambda a, s: a.head_tilt(W(269, 'open'), 8.0, 1.2)), c=BZ(0.02))
    hk = cm((-1.6, 3.4, 1.2), (-2.1, 0.8, 1.0), 1000)
    S(W(269, 'open'), 'hall', 'door', st=HALL_PINK, cam=hk,
      ppl=[adam((-2.0, 1.6, 0.0), who='adam_sock', id='adam', face=(-2.1, 0.0), expr='fear', act=_A(lk(W(269, 'open'), 'door_glass_in'))),
           lina((-1.6, 2.1, 0.0), who='lina', id='lina', face=(-2.1, 0.0), expr='pleading', act=_A(lk(W(269, 'open'), 'door_glass_in')))],
      cold=True, c=Z(1.05, 0.02))
    # 270-271 Through the clear strip of glass: Mom's hospital coat.  Her scarf.
    BU(T(270), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=960, cy=420, scale=0.95, light=PINK_D, cold=False, act=_A(lk(T(270), (960, 760))), c=BZ(0.02))
    BU(T(271), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=980, cy=300, scale=1.35, light=PINK_D, cold=False, act=_A(lk(T(271), (960, 760))), c=BZ(0.02))
    # 272 Lina scrambles for the lock.  273 "Wait!"  274 I catch her hand.
    tl = T(272)
    S(T(272), 'hall', 'door', st=HALL_PINK, cam=hk,
      ppl=[adam((-2.0, 1.6, 0.0), who='adam_sock', id='adam', face=(-2.1, 0.0), expr='fear', act=_A(lk(tl + 0.2, ('lina', 'head'), dur=0.3))),
           lina((-1.6, 2.1, 0.0), who='lina', id='lina', path=[(tl, (-1.6, 2.1, 0.0)), (E(272) + 0.1, (-1.9, 0.75, 0.0))], run=True, expr='pleading',
                act=_A(lk(tl, 'lock'), reach(E(272) - 0.3, 1, 'lock', dur=0.3, shape='pinch')))],
      cold=True, c=Z(1.0, 0.02))
    BU(T(273), 'adam_sock', 'hall', 'door', HALL_PINK, cx=960, cy=600, scale=0.95, turn=0.25, light=PINK_D, expr='shout', cold=True,
       act=_A(lk(T(273), (1350, 700), dur=0.15, snap=True)), c=BZ(0.03))
    tc = WD(274, 'catch')
    tl4 = T(274) - 0.1
    IN(T(274), 'doorknob', dict(frost=0.0), c=dict(mv='push', rate=0.03),
       hands=[dict(who='lina', fn=slide(tl4, tl4 + 0.35, (1500, 1250), (1150, 640), 150, 160,
                                         extra=lambda t, r: (r[0] + 140 * ease_in_out(clamp((t - tc - 0.05) / 0.3)), r[1] + 120 * ease_in_out(clamp((t - tc - 0.05) / 0.3)), r[2], r[3])),
                   size=200, shape='open', side=-1, sleeve_from=(1700, 1500)),
              dict(who='adam_sock', fn=slide(tc - 0.2, tc + 0.05, (1900, 1300), (1330, 760), 150, 155,
                                             extra=lambda t, r: (r[0] + 140 * ease_in_out(clamp((t - tc - 0.05) / 0.3)), r[1] + 120 * ease_in_out(clamp((t - tc - 0.05) / 0.3)), r[2], r[3])),
                   size=280, shape='grip', side=-1, sleeve_from=(2100, 1500))],
       sfx=[(tc, 'cloth_grab', -6, 0, 'inside')])
    # 275 No cloud.  276 Not a wisp.  277 At minus forty.  (his copy breathes nothing; the kids' breath clouds)
    BU(T(275), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=960, cy=560, scale=0.95, light=PINK_D, cold=False, act=_A(lk(T(275), (960, 760))),
       acts=lambda A, sh, sp: [frost_air(50, 7)], c=BZ(0.02))
    BU(T(276), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=960, cy=470, scale=1.5, light=PINK_D, cold=False, act=_A(lk(T(276), (960, 760))),
       acts=lambda A, sh, sp: [frost_air(50, 8)], c=BZ(0.02))
    BU(T(277), 'adam_sock', 'hall', 'door', HALL_PINK, cx=720, cy=580, scale=0.85, turn=0.3, light=PINK_D, expr='fear', cold=True,
       busts=[dict(who='lina', cx=1220, cy=700, scale=0.68, turn=-0.3, expr='fear', light=PINK_D, act=_A(lk(T(277), (700, 500))))],
       act=_A(lk(T(277), (1500, 500))), on=[puffs(1.6, 1.4)], c=BZ(0.015))
    # 278 "Breathe, Mom," I say.  279 Silence.  280 S "...Let me in, baby. I'm so cold."
    BU(T(278), 'adam_sock', 'hall', 'door', HALL_PINK, cx=980, cy=600, scale=0.95, turn=-0.25, light=PINK_D, expr='stern_afraid', cold=True,
       act=_A(lk(T(278), (500, 560))), c=BZ(0.02))
    S(T(279), 'hall', 'doorclose', st=HALL_PINK, ppl=[P('shiver_mom', (-2.1, -0.45, 0.0), face=(-2.1, 2.0), sil=0.5, sil_rim='#ff9ec8', sil_rim_a=0.25,
                                                         dorder=-6.0, light=PINK, talk=False, breath=False)], c=Z(1.0, 0.0))
    BU(T(280), 'shiver_mom', 'hall', 'doorclose', HALL_PINK, cx=960, cy=560, scale=0.9, light=PINK_D, cold=False,
       act=_A(lambda a, s: a.head_tilt(T(280), -12.0, 1.6), lk(T(280), (960, 760))), c=BZ(0.025))
    # 281-284 Slowly, a face slides up the glass. Long. White. Red eyes.
    tfa = T(281) + 0.2
    face = lambda t: (1.0, ease_in_out(clamp((t - tfa) / (E(281) - tfa))))
    S(T(281), 'hall', 'doorclose', st=dict(HALL_PINK, face=face), c=Z(1.0, 0.0, 960, 560, x1=960, y1=500, f1=1.3), sfx=[(tfa, 'glass_squeak', -6, 0, 'inside', dict(dur=2.2))])
    def glass_face(t, sc, cy, red=None):
        acts_ = [lambda a, s: a.set(-9, None, 0.1, sh_long=1.0, sh_smile=1.0, sh_sink=1.0, sh_red=0.0 if red else 1.0), lk(t, (960, 760))]
        if red: acts_.append(lambda a, s: a.set(red - 0.05, None, 0.08, sh_red=1.0))
        BU(t, 'shiver', 'hall', 'doorclose', HALL_PINK, cx=960, cy=cy, scale=sc, light=dict(PINK_D, rim_a=60), act=_A(*acts_), face_fix=False,
           acts=lambda A, sh, sp: [frosted_glass()], c=BZ(0.03), **({'hit': red + 0.05} if red else {}))
    glass_face(T(282), 0.95, 600, red=WD(284, 'red'))
    glass_face(T(283), 1.3, 560, red=WD(284, 'red'))
    glass_face(T(284), 1.9, 640, red=WD(284, 'red'))
    # 285 The doorknob grows frost.
    tk = T(285)
    IN(T(285), 'doorknob', lambda u: dict(frost=ease_in_out(clamp((u - 0.1) / 1.6))), c=dict(mv='push', rate=0.03),
       sfx=[(tk + 0.1, 'frost_creep', -2, 0, 'close', dict(dur=1.8))])


# ==================================================================================================== RULE 6: THE ATTIC, THE BATHROOM (286-311)
def plan_rule6(F):
    RULE(T(286), 6)
    # 289 The house is as cold as the street.
    S(T(289), 'hall', 'door', st=HALL_BLACK, cam=cm((-1.6, 3.4, 1.2), (-2.1, 0.8, 1.0), 1000),
      ppl=[adam((-2.25, 1.9, 0.0), who='adam_sock', id='adam', face=(-1.9, 2.1), expr='fear', act=_A(lk(T(289), (-2.1, 0.0, 1.3)))),
           lina((-1.85, 2.1, 0.0), who='lina', id='lina', face=(-2.25, 1.9), expr='sad', act=_A(lk(T(289), ('adam', 'head')), tremblef(T(289), None, 0.4)))],
      cold=True, c=Z(1.2, 0.02, 960, 560))
    # 290-291 Click. Click. Click. Across the ceiling.
    hb = cm((-2.1, 3.9, 1.0), (-2.1, 1.6, 1.25), 1000)
    tcl = [WD(290, 'click'), WD(290, 'click', 1), WD(290, 'click', 2)]
    ceil = lambda k: (-2.1, 1.0 + 1.4 * k, 2.45)
    S(T(290), 'hall', 'back', st=HALL_BLACK, cam=hb,
      ppl=[adam((-2.25, 2.0, 0.0), who='adam_sock', id='adam', face=(-2.1, 4.0), expr='fear',
                act=_A(*[lk(tt, ceil(j), dur=0.2, snap=True) for j, tt in enumerate(tcl)])),
           lina((-1.85, 2.2, 0.0), who='lina', id='lina', face=(-2.1, 4.0), expr='fear',
                act=_A(*[lk(tt + 0.08, ceil(j), dur=0.2) for j, tt in enumerate(tcl)]))],
      cold=True, c=Z(1.0, 0.02), sfx=[(tt, 'attic_click', -2 + 2 * j, 0, 'inside') for j, tt in enumerate(tcl)])
    S(T(291), 'hall', 'back', st=HALL_BLACK, cam=hb,
      ppl=[adam((-2.25, 2.0, 0.0), who='adam_sock', id='adam', face=(-2.1, 4.0), expr='fear', act=_A(lk(T(291), ceil(2.2), dur=1.0))),
           lina((-1.85, 2.2, 0.0), who='lina', id='lina', face=(-2.1, 4.0), expr='fear', act=_A(lk(T(291), ceil(2.4), dur=1.0)))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(291) + 0.2, 'attic_scuttle', -6, 0, 'inside', dict(dur=1.0))])
    # 292 He's in the attic.  293 Following us.
    S(T(292), 'hall', 'hatch', st=dict(HALL_BLACK, hatch=lambda t: 0.04 * abs(math.sin((t - T(292)) * 9.0)) * clamp((t - T(292)) / 0.3)), c=Z(1.5, 0.03, 960, 620),
      sfx=[(T(292) + 0.2, 'hatch_rattle', -4, 0, 'inside')])
    BU(T(293), 'lina', 'hall', 'back', HALL_BLACK, cx=960, cy=640, scale=0.95, light=PINK_D, expr='fear', cold=True,
       act=_A(lk(T(293), (900, 120), dur=0.5)), c=BZ(0.02), sfx=[(T(293), 'attic_click', -6, 0, 'inside')])
    # 294 The hallway hatch drops open.  (HIT)
    td = WD(294, 'drops')
    S(T(294), 'hall', 'hatch', st=dict(HALL_BLACK, hatch=lambda t: ease_in_cubic(clamp((t - td) / 0.22))), c=Z(1.8, 0.02, 960, 640, hit=[td + 0.2]), hit=td + 0.2,
      sfx=[(td + 0.2, 'hatch_drop', 2, 0, 'inside')])
    # 295 His face lowers, upside down.  (the hatch view; his inverted face lowers out of the hole)
    th5 = T(295) + 0.1
    BU(T(295), 'shiver', 'hall', 'hatch', dict(HALL_BLACK, hatch=1.0), cx=960, cy=lambda t: lerp(640, 430, ease_in_out(clamp((t - th5) / 1.4))), scale=0.85, rot=180,
       light=dict(SH_NIGHT, rim_a=120), act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_legcap=2.0), lk(T(295), (960, 300))), face_fix=False, bg_dim=0.05,
       c=BZ(0.02), sfx=[(th5, 'skin_stretch', -6, 0, 'inside', dict(kind='creak'))])
    # 296-297 A leg reaches between us. Prying.  (low two-shot, the leg stabs down between them)
    tlg = WD(296, 'leg')
    # review (the leg read as a rope and crossed Lina's face): a real jointed leg stabs straight DOWN between them from the
    # open hatch above; they recoil apart from it (Adam left, Lina right) and it pries in the gap
    leg_dn = lambda t0, pry=0.0: [blanket_hook(None, t0, lambda t: (1010 + pry * 34 * math.sin((t - t0) * 9.0), 860 + pry * 22 * abs(math.sin((t - t0) * 9.0))),
                                               (1150, -260), knee=(1170, 200), w0=90.0)]
    kids2 = lambda t, ex_, t_leg, pry, k_=0.0: BU(t, 'adam_sock', 'hall', 'back', HALL_BLACK, cx=lambda tt: 680 - k_ * 90 * ease_out_cubic(clamp((tt - t_leg - 0.1) / 0.3)) - (1 - k_) * 90,
                                              cy=620, scale=0.85, turn=0.35, light=PINK_D, expr=ex_, cold=True,
                                              busts=[dict(who='lina', cx=lambda tt: 1290 + k_ * 80 * ease_out_cubic(clamp((tt - t_leg - 0.12) / 0.3)) + (1 - k_) * 80,
                                                          cy=720, scale=0.7, turn=-0.3, expr=ex_, light=PINK_D, act=_A(lk(t, (1010, 500))))],
                                              act=_A(lk(t, (1010, 500))), acts=lambda A, sh, sp: leg_dn(t_leg, pry), c=BZ(0.03, shake=1.5 * pry),
                                              sfx=[(t_leg + 0.15, 'leg_pry' if pry else 'leg_stab', -2, 0, 'inside')])
    kids2(T(296), 'terror', tlg - 0.1, 0.0, 1.0)
    kids2(T(297), 'terror', T(297) - 0.6, 1.0)
    # 298 We dive into the bathroom, the smallest room.
    tb = T(298)
    S(T(298), 'hall', 'bathdoor', st=HALL_BLACK,
      ppl=[lina((-2.1, 3.0, 0.0), who='lina', id='lina', path=[(tb, (-2.1, 3.0, 0.0)), (tb + 1.3, (-1.75, 1.4, 0.0)), (tb + 1.8, (-1.2, 1.35, 0.0))], run=True, expr='terror'),
           adam((-2.2, 3.6, 0.0), who='adam_sock', id='adam', path=[(tb + 0.2, (-2.2, 3.6, 0.0)), (tb + 1.6, (-1.95, 1.6, 0.0)), (tb + 2.2, (-1.75, 1.45, 0.0))], run=True,
                expr='terror')],
      cold=True, c=Z(1.5, 0.03, 900, 600), sfx=[(tb + 0.2, 'footsteps_run', -6, 0, 'inside', dict(dur=2.0))])
    # 299 Door shut.  300 Towels in the gap.
    # review (the kids were absent, a black frame): the two of them backed against the door they just slammed
    BU(T(299), 'adam_sock', 'bath', 'door', dict(BATH, towels='rack', door=0.0), cx=lambda t: 720 + 40 * (1 - ease_out_cubic(clamp((t - T(299)) / 0.35))), cy=600,
       scale=0.85, turn=0.3, light=PINK_D, expr='terror', cold=True, act=_A(lk(T(299), (1500, 560), dur=0.2)),
       busts=[dict(who='lina', cx=1240, cy=700, scale=0.7, turn=-0.3, expr='terror', light=PINK_D, act=_A(lk(T(299) + 0.1, (1500, 560))))],
       c=BZ(0.015, shake=2.5, hit=[T(299) + 0.35]), sfx=[(T(299) + 0.35, 'door_slam', 0, 0, 'inside')])
    t30 = T(300) + 0.1
    IN(T(300), 'towel', dict(press=0.0, tip=0.0), motion=lambda u: (0.0, 260.0 * (1 - ease_out_cubic(clamp(u / 0.5))), 0.0, 0.0), c=dict(mv='push', rate=0.02),
       hands=[dict(who='adam_sock', fn=slide(t30, t30 + 0.45, (700, -100), (900, 520), 100, 95), size=300, shape='flat', side=1, sleeve_from=(560, -400)),
              dict(who='adam_sock', fn=slide(t30 + 0.05, t30 + 0.5, (1300, -100), (1150, 520), 80, 85), size=300, shape='flat', side=-1, sleeve_from=(1450, -400))],
       sfx=[(t30 + 0.2, 'towel_stuff', -6, 0, 'inside')])
    # 301-302 Under the door, a needle-thin leg tip slides in. Feeling for Lina's sock.
    tt = T(301) + 0.3
    IN(T(301), 'towel', lambda u: dict(press=0.0, tip=ease_in_out(clamp((u - 0.3) / 2.4))), c=dict(mv='push', rate=0.02),
       sfx=[(tt, 'leg_slide', -4, 0, 'close', dict(dur=2.4))])
    IN(T(302), 'towel', lambda u: dict(press=0.0, tip=0.92 + 0.08 * math.sin(u * 5.0)), c=dict(mv='push', f=1.1, rate=0.03), layers=[sock_layer(1560, 780)])
    # 303 I jam the towel down on it.  304 Hard.  305 It pulls back.
    tj = WD(303, 'jam')
    IN(T(303), 'towel', lambda u: dict(press=ease_out_back(clamp((u + T(303) - tj) / 0.3)), tip=1.0), c=dict(mv='push', rate=0.02),
       hands=[dict(who='adam_sock', fn=slide(tj - 0.25, tj + 0.05, (900, 120), (1000, 560), 95, 90), size=300, shape='flat', side=1, sleeve_from=(760, -300))],
       sfx=[(tj + 0.05, 'towel_jam', 0, 0, 'close')])
    IN(T(304), 'towel', dict(press=1.0, tip=1.0), c=dict(mv='push', f=1.3, rate=0.02, x=960, y=560, shake=3.0, hit=[T(304) + 0.1]), hit=T(304) + 0.1,
       hands=[dict(who='adam_sock', fn=slide(T(304), T(304) + 0.1, (1000, 560), (1000, 580), 90, 90), size=300, shape='flat', side=1, sleeve_from=(760, -300))])
    IN(T(305), 'towel', lambda u: dict(press=1.0, tip=1.0 - ease_in_cubic(clamp((u - 0.1) / 0.4))), c=dict(mv='push', rate=0.02),
       sfx=[(T(305) + 0.15, 'leg_withdraw', -2, 0, 'close')])
    # 306 The clicking stops.  307 Then the song moves.  308 Away from our house.
    bw = dict(BATH, towels='jammed')
    two = lambda t, ex_a='fear', ex_l='fear', look=(960, 420), **k: BU(t, 'adam_sock', 'bath', 'wide', bw, cx=720, cy=600, scale=0.85, turn=0.3, light=PINK_D,
                                                                   expr=ex_a, cold=True, act=_A(lk(t, look)),
                                                                   busts=[dict(who='lina', cx=1220, cy=700, scale=0.7, turn=-0.3, expr=ex_l, light=PINK_D, act=_A(lk(t + 0.1, look)))],
                                                                   c=BZ(0.015), **k)
    two(T(306), look=(1300, 900))
    two(T(307), ex_a='suspicious', look=(400, 300))
    S(T(308), 'street', 'house', st=dict(ST_DARK, truck=None), acts=lambda A, sh, sp: truck_live(sp, glide(T(308) - 0.3, E(308) + 2.0, -0.6, -9.0)), c=Z(1.0, 0.01),
      sfx=[(T(308), 'truck_glide', -6, -0.3, 'outside', dict(dur=2.5))])
    # 309 I wipe frost off the bathroom window.
    tw_ = T(309) + 0.2
    S(T(309), 'bath', 'window', st=dict(bw, wipe=lambda t: ease_in_out(clamp((t - tw_) / 1.6))),
      ppl=[adam('window_wipe', who='adam_sock', id='adam', face=(-0.5, 0.0), expr='focused',
                act=_A(lambda a, s: a.reach_to(tw_, 1, lambda t: scr(s.sp, (-0.5 + 0.18 * math.sin((t - tw_) * 6.0), 0.03, 1.5)), t1=E(309) + 0.2, dur=0.3, shape='flat')))],
      cold=True, c=Z(1.0, 0.02), sfx=[(tw_, 'frost_wipe', -4, 0, 'inside', dict(dur=1.6))])
    # 310-311 The truck has rolled across the street. To Kessler's door.
    S(T(310), 'street', 'bathout', st=dict(ST_B, truck_open=1.0), c=Z(1.0, 0.02))
    S(T(311), 'street', 'kout', st=dict(ST_B, truck_open=1.0), ppl=[SHB(m=1.0, legs=True, act=lk(T(311), 'kdoor'))], c=Z(1.4, 0.02, 820, 560))


# ==================================================================================================== THE TWIST: KESSLER (312-330)
KESS_K = dict(rim='#ff9ec8', rim_a=150, side=1, key=-0.42)     # (owner's-eyes: Kessler shaded, not a pale outline ghost)


def plan_twist(F):
    KP = dict(ST_B, truck_open=1.0)
    # 312 His door opens.
    S(T(312), 'street', 'kporch', st=dict(KP, kdoor_open=False), c=Z(1.3, 0.02, 960, 560))
    S(W(312, 'opens'), 'street', 'kporch', st=KP, ppl=[kess('kdoor_in', face=(1.4, -20.0), expr='dazed', light=dict(NIGHT, rim_a=50, key=-0.5))],
      c=Z(1.9, 0.02, 960, 560), sfx=[(WD(312, 'opens'), 'door_creak', -4, 0, 'outside')])
    # 313 Mr. Kessler shuffles out.  (slow, slippers on the boards; he looks at the pink window, not at us)
    S(T(313), 'street', 'kporch', st=KP, ppl=[kess('kdoor_in', path=[(T(313), (1.4, -24.3, 0.0)), (E(313) + 0.6, (1.35, -23.0, 0.0))], face=(-3.6, -15.1),
                                                   expr='dazed', light=KESS_K, act=_A(lk(T(313), (-3.6, -15.1, 1.6))))], cold=True, c=Z(1.9, 0.02, 960, 600),
      sfx=[(T(313) + 0.2, 'slipper_shuffle', -6, 0, 'outside', dict(dur=1.6))])
    # 314 Slippers.  315 Undershirt.  316 No coat.  317 Not shivering.  318 Smiling.
    S(T(314), 'street', 'kporch', st=KP, cam=cm((1.7, -21.9, 0.25), (1.35, -23.0, 0.12), 1500),
      ppl=[kess((1.35, -23.0, 0.0), face=(-3.6, -15.1), expr='dazed', light=KESS_K,
                act=_A(lambda a, s: a._add(T(314), None, lambda P_, t: setattr(P_, 'dx', P_.dx + 18.0 * ease_in_out(clamp((t - T(314) - 0.1) / 0.5))))))], cold=True,
      c=Z(1.0, 0.02))
    BU(T(315), 'kessler_out', 'street', 'kporch', KP, cx=960, cy=360, scale=0.62, turn=-0.25, light=PINK_L, expr='dazed', cold=True, act=_A(lk(T(315), (300, 400))), c=BZ(0.015))
    S(T(316), 'street', 'kporch', st=KP, ppl=[kess((1.35, -23.0, 0.0), face=(-3.6, -15.1), expr='dazed', light=KESS_K, act=_A(lk(T(316), (-3.6, -15.1, 1.6))))],
      cold=True, c=Z(2.1, 0.02, 960, 540))
    BU(T(317), 'kessler_out', 'street', 'kporch', KP, cx=960, cy=600, scale=0.95, turn=-0.25, light=PINK_L, expr='sleepy', cold=True,
       act=_A(lk(T(317), (300, 450))), c=BZ(0.015))
    BU(T(318), 'kessler_out', 'street', 'kporch', KP, cx=960, cy=560, scale=1.2, turn=-0.25, light=PINK_L, expr='still_smile', cold=True,
       act=_A(lk(T(318), (300, 450))), c=BZ(0.02))
    # 319 From the pink window:  320 S "Walter! Look who's been waiting!"
    # film pass (cast r3): at set scale in the 'kout' view his figure was thin and ~4 % of the frame, and a push cannot
    # reach the far window (parallax): a medium of him in the window instead, cut in to the close-up on L320
    BU(T(319), 'shiver', 'street', 'window_close', STO_B, cx=900, cy=520, scale=0.62, light=SH_PINK, face_fix=False,
       act=_A(pose(-9, None, 0.1, ws_bend=0.15), lambda a, s: a.slow_wave(T(319), E(320) + 1, 1), lk(T(319), (1300, 560))), c=BZ(0.02))
    BU(T(320), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=0.95, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, ws_bend=0.25), lambda a, s: a.slow_wave(T(320), E(320) + 1, 1), lk(T(320), (1500, 700)),
              lambda a, s: a.set(WD(320, 'look'), None, 0.4, sh_smile=0.25)), c=BZ(0.025))
    # 321 Mr. Kessler takes one step off his porch.
    S(T(321), 'street', 'kporch', st=KP, ppl=[kess((1.35, -23.0, 0.0), path=[(T(321) + 0.4, (1.35, -23.0, 0.0)), (E(321) + 0.2, (1.35, -22.2, -0.17))],
                                                   face=(-3.6, -15.1), expr='still_smile', light=KESS_K)], cold=True, c=Z(1.9, 0.02, 960, 600),
      sfx=[(E(321) - 0.2, 'snow_step', -4, 0, 'outside')])
    # 322-323 The town never shoveled our walks. He did.  (memory: before dawn, every morning, our walk)
    sv = lambda: P('kessler_am', (-4.0, -7.3, FOOT), face=(-3.0, -7.3), sil=0.35, light=NIGHT, extras=[shovel_fx()],
                   act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.3), reach(-9, 1, (-3.45, -7.3, FOOT + 0.35), dur=0.1), reach(-9, -1, (-3.75, -7.3, FOOT + 0.9), dur=0.1),
                          lambda a, s: a._add(-1e9, None, lambda P_, t: setattr(P_, 'lean', P_.lean + 0.1 * math.sin(t * 3.2)))))
    S(T(322), 'street', 'house', st=dict(truck=None, walk='shoveled', win=dict(liv=0.0, kitchen=0.0)), ppl=[sv()], era='memory', cold=True, c=Z(1.9, 0.02, 760, 600),
      sfx=[(T(322) + 0.3 + 0.95 * k, 'shovel_scrape', -6, 0, 'outside') for k in range(2)])
    BU(T(323), 'kessler_am', 'street', 'door', dict(truck=None, walk='shoveled'), cx=960, cy=600, scale=0.85, turn=0.3, light=NIGHT, expr='tender', era='memory', cold=True,
       act=_A(lk(T(323), (1300, 640))), c=BZ(0.015), sfx=[(T(323), 'shovel_scrape', -4, 0, 'outside')])
    # 324 His furnace died last night.  325 And nobody checked.
    S(T(324), 'street', 'kporch', st=dict(ST_B, kdoor_open=True), c=Z(1.0, 0.0, 960, 500, x1=960, y1=330, f1=1.6))
    S(T(325), 'street', 'lane_e', st=dict(ST_B, win=dict(his=0.0)), c=Z(1.2, 0.02))
    # 326 Another step.  (from his doorway: his back, the pink window ahead)
    S(T(326), 'street', 'kout', st=KP, ppl=[kess((1.4, -21.9, -0.2), path=[(T(326) - 0.3, (1.4, -21.9, -0.2)), (E(326) + 0.5, (1.0, -20.75, -0.3))], face=(-3.6, -15.1),
                                                  expr='still_smile', light=KESS_K),
                                             SHB(m=0.0, lean=0.25, act=_A(lambda a, s: a.slow_wave(T(326) - 1, E(326) + 1, 1), lk(T(326), 'kwalk_mid')))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(326) + 0.4, 'snow_step', -4, 0, 'outside')])
    # 327 Every night, he broke his own first rule.  328 Just to wave back at Lina.  (memory)
    S(T(327), 'street', 'kessler', st=dict(truck=None, win=dict(his=0.05)), cam=cm((4.3, -18.6, 1.5), (4.3, -23.98, 1.5), 1500), era='memory',
      acts=lambda A, sh, sp: [window_hand(sp, 'kwindow', T(327) + 0.1, T(327) + 1.2)], c=Z(1.0, 0.02))
    S(T(328), 'living', 'window', st=dict(LIV_SHUT, curtains=0.18), ppl=[lina((3.5, 0.45, 0.0), face=(3.4, -2.0), expr='kid_grin', act=_A(wavef(T(328), E(328) + 1, 1)))],
      era='memory', c=Z(1.9, 0.02, 830, 560))
    # 329 Every time I turned toward Kessler's... Mister Shiver gave me something closer to be scared of.  (recall cuts)
    BU(T(329), 'adam_in', 'living', 'window', dict(LIV_SHUT, curtains=0.18), cx=1000, cy=620, scale=0.9, turn=-0.3, light=NIGHT_L, expr='suspicious', era='memory',
       act=_A(lk(T(329), (600, 420))), c=BZ(0.02))
    S(W(329, 'mister'), 'hall', 'doorclose', st=dict(HALL_A, hall=0.25, lamp=0.0, pink=1.0), cut='blink', era='memory', c=Z(1.1, 0.03),
      sfx=[(WD(329, 'mister') + 0.2, 'door_tap', -6, 0, 'inside', dict(kind='tap', n=1))])
    RIN(W(329, 'closer'), lambda u: dict(talk=0.7 + 0.3 * math.sin(u * 7), static=0.15), 'adam_in', cut='blink', era='memory', c=dict(mv='push', rate=0.03))
    # 330 Whoever's coldest... was across the street.
    BU(T(330), 'kessler_out', 'street', 'kout', KP, cx=960, cy=600, scale=0.9, turn=0.6, light=PINK, expr='still_smile', cold=True, act=_A(lk(T(330), (300, 560))), c=BZ(0.02))
    S(W(330, 'across'), 'street', 'kout', st=KP, ppl=[kess((0.9, -20.6, -0.32), path=[(T(330), (1.1, -21.0, -0.3)), (E(330) + 1.0, (0.6, -20.4, -0.32))], face=(-3.6, -15.1),
                                                           expr='still_smile', light=KESS_K),
                                                      SHB(m=0.0, lean=0.25, act=_A(lambda a, s: a.slow_wave(T(330) - 1, E(330) + 1, 1)))],
      cold=True, c=Z(1.0, 0.01))


# ==================================================================================================== RULE 7, THE CROSSING, THE HUDDLE (331-373)
def plan_rule7(F):
    KP = dict(ST_B, truck_open=1.0)
    RULE(T(331), 7)
    # 336 Sixty-eight years, he taped that to our doors.  337 When it's my turn... don't come.
    tk = T(336) + 0.6
    IN(T(336), 'rules', dict(show=7, hl=7, door='ours'), c=dict(mv='push', f=1.0, rate=0.02),
       hands=[dict(who='kessler', fn=slide(tk - 0.5, tk, (1900, 120), (1540, 160), 125, 135,
                                           extra=lambda t, r: (r[0] - 8 * math.sin(clamp((t - tk) / 0.6) * math.pi), r[1], r[2], r[3] * (1 - clamp((t - tk - 1.4) / 0.4)))),
                   size=300, shape='flat', side=-1, sleeve_from=(2200, -200))], sfx=[(tk, 'tape_press', -8, 0.3, 'close')])
    IN(T(337), 'rules', dict(show=7, hl=7, door='kessler'), motion=lambda u: (0.0, -300.0 * ease_in_out(clamp(u / 1.5)), 0.45 * ease_in_out(clamp(u / 1.5)), 0.0),
       c=dict(mv='hold'))
    # 338 So no kid would ever follow him out.  339 Like Benny did.  (1958)
    w58 = lambda who, t0, t1, a0, a1, seed=0, expr='neutral': P(who, a0, path=[(t0, a0), (t1, a1)], surface='snow', expr=expr, seed=seed, light=SEPIA)
    S(T(338), 'y58', 'kout', st={}, ppl=[w58('benny', T(338) - 0.5, E(338) + 0.5, (1.4, -22.2, FOOT), (0.7, -19.8, FOOT), seed=3, expr='little_girl')],
      era='memory', c=Z(1.2, 0.02), cold=True)
    S(T(339), 'y58', 'mitten', st={}, era='memory', grade='ic_1958_red', c=Z(1.15, 0.03))
    # 340 A rule to save children.  341 Mister Shiver's favourite.
    S(T(340), 'street', 'lane', st=dict(ST_B, win=dict(liv=0.0, his=0.0)), c=Z(1.15, 0.02))
    BU(T(341), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=1.05, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, ws_bend=0.2), lambda a, s: a.slow_wave(T(341) - 1, E(341) + 1, 1), lk(T(341), (1500, 760)),
              lambda a, s: a.set(T(341) + 0.3, None, 0.8, sh_smile=0.35)), c=BZ(0.03))
    # 342 Because everybody inside... means somebody alone.
    S(T(342), 'street', 'lane_e', st=dict(ST_B, win=dict(his=0.0)), c=Z(1.1, 0.02))
    S(W(342, 'somebody'), 'street', 'kout', st=KP, ppl=[kess((0.4, -20.2, -0.32), face=(-3.6, -15.1), expr='still_smile', light=KESS_K,
                                                             path=[(T(342), (0.5, -20.3, -0.32)), (E(342) + 2, (0.2, -20.0, -0.32))]),
                                                        SHB(m=0.0, lean=0.25, act=_A(lambda a, s: a.slow_wave(T(342), E(342) + 1, 1)))],
      cold=True, c=Z(1.0, 0.0, 960, 560, x1=820, y1=560, f1=0.85))
    # 343 Mr. Kessler is halfway to the window.
    S(T(343), 'street', 'kout', st=KP, ppl=[kess('kessler_half', face=(-3.6, -15.1), expr='still_smile', light=KESS_K,
                                                 path=[(T(343) - 0.3, (0.2, -20.05, -0.32)), (E(343) + 1.5, (-0.95, -19.25, -0.32))]),
                                            SHB(m=0.0, lean=0.35, act=_A(lambda a, s: a.slow_wave(T(343) - 1, E(343) + 1, 1), lk(T(343), 'kessler_half')))],
      cold=True, c=Z(1.5, 0.02, 760, 520), sfx=[(T(343) + 0.3, 'snow_step', -6, 0, 'outside')])
    # 344 I grab the radio.  345 No bells in the static.  346 He's busy.  347 "Dad! Kessler's outside, no coat. Call an ambulance. Over."
    bw = dict(BATH, towels='jammed', wipe=1.0)
    BU(T(344), 'adam_sock', 'bath', 'window', bw, cx=960, cy=600, scale=0.95, light=PINK_D, expr='resolve', cold=True, act=_A(radio(T(344) + 0.1, E(347) + 0.5, 1)),
       c=BZ(0.02), sfx=[(T(344) + 0.1, 'radio_grab', -4, 0, 'close')])
    RIN(T(345), lambda u: dict(talk=0.0, static=0.55 + 0.1 * math.sin(u * 13)), 'adam_sock', c=dict(mv='push', rate=0.03), sfx=[(T(345), 'radio_static', -4, 0, 'close', dict(dur=1.2))])
    # film pass (cast r3): "He's busy" is about HIM: a medium in his window, bent toward Kessler below, the glove reaching
    BU(T(346), 'shiver', 'street', 'window_close', STO_B, cx=1000, cy=470, scale=0.62, light=SH_PINK, face_fix=False,
       act=_A(pose(-9, None, 0.1, ws_bend=0.4), lambda a, s: a.slow_wave(T(346) - 0.5, E(346) + 1, 1), lk(T(346), (600, 980), dur=0.2)), c=BZ(0.02))
    BU(T(347), 'adam_sock', 'bath', 'window', bw, cx=980, cy=600, scale=1.0, turn=-0.2, light=PINK_D, expr='terrified_call', cold=True,
       act=_A(radio(T(347) - 0.3, E(347) + 0.4, 1)), c=BZ(0.02))
    BU(W(347, 'call'), 'adam_sock', 'bath', 'window', bw, cx=960, cy=580, scale=1.25, light=PINK_D, expr='shout', cold=True,
       act=_A(radio(T(347) - 1, E(347) + 0.4, 1)), c=BZ(0.025))
    # 348 Orange light sweeps the window.  349 It's really him.
    S(T(348), 'bath', 'window', st=dict(bw, beacon=ST.ic_pass(T(348) - 0.2, 3.5)), acts=lambda A, sh, sp: [orange_sweep(T(348) + 0.1, 2.2)], c=Z(1.0, 0.02))
    S(T(349), 'street', 'plow', st=dict(truck=None, plow=dict(x=lambda t: -14.0 + 7.0 * clamp(t - T(349), 0.0, 6.0), y=-11.0, dir=1, beacon=1.0)), c=Z(1.0, 0.01),
      sfx=[(T(349), 'plow_pass', -6, 0, 'outside', dict(dur=2.0))])
    # 350 D "Two minutes out. He can't wait two minutes. Go together. Hold on to each other. Don't let go. Over."
    dadcab = lambda: dict(plain=('#2a1c14', '#0a0706'), bg_fn=cab_bg(), light=lambda t: dict(BEACON, rim_a=int(70 + 80 * (0.5 + 0.5 * math.sin(t * 8.2)))))
    BU(T(350), 'dad', None, None, cx=960, cy=600, scale=0.85, turn=0.3, expr='grim_drive', act=_A(radio(T(350) - 0.5, E(350) + 0.3, 1)), c=BZ(0.015), **dadcab())
    BU(W(350, 'go'), 'adam_sock', 'bath', 'window', bw, cx=980, cy=620, scale=0.95, turn=-0.2, light=PINK_D, expr='determined', cold=True,
       act=_A(lk(W(350, 'go'), (1300, 760))), c=BZ(0.02))
    BU(W(350, 'hold'), 'dad', None, None, cx=960, cy=580, scale=1.0, turn=0.3, expr='fierce_kind', act=_A(radio(T(350) - 1, E(350) + 0.3, 1)), c=BZ(0.02), **dadcab())
    # 351 Every layer.  352 The big blanket over both of us.
    S(T(351), 'hall', 'door', st=HALL_BLACK, cam=cm((-2.0, 2.9, 1.4), (-2.6, 0.9, 1.2), 950),
      ppl=[adam('coats', who='adam_sock', face=(-2.8, 0.85), act=_A(reach(T(351) + 0.05, 1, (-2.78, 0.75, 1.5), dur=0.3))),
           lina((-2.2, 1.6, 0.0), who='lina', face=(-2.8, 0.9), expr='brave', act=_A(lambda a, s: a.head_tilt(T(351) + 0.2, 8.0, 0.6)))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(351) + 0.2, 'coat_rustle', -6, 0, 'inside')])
    hk = cm((-1.6, 3.4, 1.2), (-2.1, 0.8, 1.0), 1000)
    S(T(352), 'hall', 'door', st=HALL_BLACK, cam=hk,
      ppl=[lina((-1.85, 1.2, 0.0), who='lina', id='lina', face=(-2.1, 0.0), expr='brave'),
           adam((-2.3, 1.3, 0.0), who='adam_sock', id='adam', face=(-2.1, 0.0), expr='determined', act=_A(lambda a, s: a.hold_hand(T(352), 1, s.A['lina'], -1)))],
      acts=cloak(('adam', 'lina')), cold=True, c=Z(1.5, 0.02, 960, 560), sfx=[(T(352) + 0.1, 'blanket_wrap', -6, 0, 'inside')])
    # 353 We cross, holding on.  (one blanket, the street, his truck at B on the left)
    xc = cm((3.6, -17.6, 1.1), (0.6, -12.6, 0.4), 1000)
    pair = lambda t0, t1, a0, a1, **k: [lina(a0, who='lina', id='lina', path=[(t0, a0), (t1, a1)], surface='snow', expr=k.get('el', 'fear'), act=k.get('la')),
                                       adam((a0[0] + 0.45, a0[1] + 0.1, a0[2]), who='adam_sock', id='adam', path=[(t0, (a0[0] + 0.45, a0[1] + 0.1, a0[2])), (t1, (a1[0] + 0.45, a1[1] + 0.1, a1[2]))],
                                            surface='snow', expr=k.get('ea', 'determined'), act=_A(lambda a, s: a.hold_hand(t0 - 1, 1, s.A['lina'], -1), *(k.get('aa') or [])))]
    S(T(353), 'street', 'kout', st=KP, cam=xc, ppl=pair(T(353) - 0.5, E(353) + 1.0, (0.7, -11.4, FOOT - 0.15), (0.9, -12.9, FOOT - 0.15)),
      acts=cloak(('adam', 'lina')), cold=True, c=Z(1.0, 0.02), sfx=[(T(353) + 0.2, 'snow_steps', -6, 0, 'outside', dict(dur=1.6))])
    # 354 Legs stab the snow around us.
    def stabs(times):
        def f(a, s):
            for j, (tt, dx) in enumerate(times):
                a.leg_to(tt, (j * 3) % 8, lambda t, dx=dx: (s.A['lina'].where(t, 'foot_l')[0] + dx, s.A['lina'].where(t, 'foot_l')[1] + 6), dur=0.15, hold=0.3, back=0.25)
        return f
    t54 = WD(354, 'stab')
    S(T(354), 'street', 'kout', st=KP, cam=xc,
      ppl=pair(T(354) - 1.0, E(355) + 1.0, (0.9, -12.9, FOOT - 0.15), (1.1, -14.6, FOOT - 0.15)) +
          [P('shiver', (-0.5, -12.2, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(1.0, -13.5),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.8), lambda a, s: a.scuttle(T(354) - 0.3, E(354) + 0.3, _line(s.sp, (-0.8, -11.8, FOOT), (-0.1, -12.8, FOOT)), None),
                    stabs([(t54, -140), (t54 + 0.25, 160), (t54 + 0.5, -60), (t54 + 0.75, 230)])))],
      acts=cloak(('adam', 'lina')), cold=True, c=Z(1.0, 0.02, hit=[t54]))
    # 355 One hooks the blanket and PULLS.
    th = WD(355, 'hooks'); tpu = WD(355, 'pulls')
    pullf = lambda t: (-150.0 * ease_out_cubic(clamp((t - tpu) / 0.25)) * (1 - 0.6 * clamp((t - tpu - 0.6) / 0.6)), -30.0 * ease_out_cubic(clamp((t - tpu) / 0.25)))
    xc2 = cm((2.4, -16.4, 1.0), (1.0, -13.8, 0.6), 1100)
    # review (a rope from off frame, him absent, the kids calm): HE is in the shot, low beside them on the snow, and a real
    # jointed leg from his body hooks the blanket's top edge and yanks; the kids lurch with it
    hk_sh = P('shiver', (-0.5, -14.8, FOOT), id='shiver', light=SH_NIGHT, talk=False, breath=False, face=(1.0, -14.0),
              act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.8), lambda a, s: a.scuttle(T(355) - 0.6, th, _line(s.sp, (-1.3, -15.2, FOOT), (-0.5, -14.8, FOOT)), None),
                     lambda a, s: a.jaw_gape(th - 0.2, E(355) + 1)))
    S(T(355), 'street', 'kout', st=KP, cam=xc2, ppl=pair(T(355) - 1.0, E(355) + 1.5, (1.0, -13.9, FOOT - 0.15), (1.1, -14.4, FOOT - 0.15), el='terror', ea='terror',
                                                       la=_A(lambda a, s: a._add(tpu, None, lambda P_, t: setattr(P_, 'lean', P_.lean - 0.25 * ease_out_cubic(clamp((t - tpu) / 0.25)) * (1 - clamp((t - tpu - 0.6) / 0.6)))))) + [hk_sh],
      acts=lambda A, sh, sp: cloak(('adam', 'lina'), pull=pullf)(A, sh, sp) + [blanket_hook(sp, th - 0.1, lambda t: (lambda q: (q[0] - 40 + pullf(t)[0], q[1] - 30 + pullf(t)[1]))(A['adam'].where(t, 'head')),
                                                                                      lambda t: A['shiver'].where(t, 'chest'), w0=30.0)],
      cold=True, c=Z(1.0, 0.02, shake=1.5, hit=[tpu]), hit=tpu, sfx=[(th, 'leg_hook', -2, 0, 'outside'), (tpu, 'cloth_tear', 0, 0, 'outside')])
    # 356 My fingers are numb.  357 Am I still holding her?
    tn = T(356)
    # "My fingers are numb": ADAM'S hand big in the foreground (stiff, trembling on the blanket edge), Lina behind it
    BU(T(356), 'lina', 'street', 'kout', KP, cx=760, cy=500, scale=0.7, turn=-0.3, light=SH_NIGHT, expr='terror', cold=True, act=_A(lk(T(356), (1250, 760))),
       hands=[dict(who='adam_sock', fn=lambda t: (1290 + 5 * math.sin(t * 31.0), 840 + 22 * ease_in_out(clamp((t - tn - 0.3) / 0.8)), -20.0, 1.0), size=560, shape='grip', side=1,
                   sleeve_from=(1750, 1300))],
       acts=lambda A, sh, sp: [blanket_fg(880.0, lift=lambda t: 22 * ease_in_out(clamp((t - tn - 0.3) / 0.8)))], c=BZ(0.02))
    BU(T(357), 'adam_sock', 'street', 'kout', KP, cx=960, cy=560, scale=1.0, light=SH_NIGHT, expr='terror', cold=True,
       act=_A(lk(T(357), (1100, 1000), dur=0.2, snap=True)), acts=lambda A, sh, sp: [blanket_fg(900.0)], c=BZ(0.03))
    # 358 He swings around, jaw down, legs arched over us like a cage.  359 S "Inside, children. Rule seven."
    tcg = WD(358, 'arched')
    xc3 = cm((1.6, -22.6, 1.3), (-0.5, -17.6, 1.2), 950)
    cage_sh = lambda t_sw: P('shiver', (-1.5, -17.4, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(-0.3, -21.0), dorder=-0.5,
                             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), lambda a, s: a.scuttle(t_sw - 0.8, t_sw + 0.2, _line(s.sp, (-1.9, -16.6, FOOT), (-0.6, -18.1, FOOT)), None),
                                    lambda a, s: a.cage(t_sw, scr(s.sp, (-0.5, -18.6, FOOT))[0], 1.55 * spot_of(s.sp, 'cage').ppm, scr(s.sp, (-0.5, -18.9, FOOT))[1], dur=0.5, lift=150.0),
                                    lambda a, s: a.jaw_gape(WD(358, 'jaw'), E(359) + 3)))
    kids_c = lambda t0, ea='terror', el='terror': pair(t0 - 2, t0 - 1, (-0.4, -18.3, FOOT - 0.15), (-0.4, -18.4, FOOT - 0.15), el=el, ea=ea)
    cage_acts = lambda A, sh, sp: cloak(('adam', 'lina'))(A, sh, sp) + legs_front()(A, sh, sp)      # review: the legs arch OVER them
    S(T(358), 'street', 'kout', st=KP, cam=xc3, ppl=[cage_sh(tcg)] + kids_c(T(358)), acts=cage_acts, cold=True,
      c=Z(1.0, 0.02, hit=[tcg + 0.4]), hit=tcg + 0.4, sfx=[(tcg, 'leg_stab_snow', 0, 0, 'outside', dict(n=8))])
    BU(T(359), 'shiver', 'street', 'kout', KP, cx=960, cy=520, scale=1.05, light=SH_NIGHT, mscale=0.26, meye=320.0,
       act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), lambda a, s: a.jaw_gape(T(359) - 2, E(359) + 1), lk(T(359), (960, 980))), c=BZ(0.03))
    # 360 I lock my arm through Lina's.  361 We walk right between his legs.
    S(T(360), 'street', 'kout', st=KP, cam=cm((0.6, -20.6, 1.0), (-0.4, -18.4, 0.8), 1200), ppl=[cage_sh(T(358) + 1.0)] + kids_c(T(360), ea='fierce_kind', el='brave'),
      acts=cage_acts, cold=True, c=Z(1.0, 0.02))
    S(T(361), 'street', 'kout', st=KP, cam=xc3, ppl=[cage_sh(T(358) + 1.0)] + pair(T(361), E(361) - 0.1, (-0.4, -18.4, FOOT - 0.15), (0.95, -21.4, -0.2), ea='fierce_kind', el='brave'),
      acts=cage_acts, cold=True, c=Z(1.0, 0.02), sfx=[(T(361) + 0.2, 'snow_steps', -6, 0, 'outside', dict(dur=1.6))])
    # 362 We pull Mr. Kessler into his doorway, out of the wind.  363 The blanket goes around all three of us.  364 Lina hugs him.
    S(T(362), 'street', 'kporch', st=KP,
      ppl=[kess((1.3, -21.6, -0.2), id='kessler', face=(-3.6, -15.1), expr='dazed', light=PINK_L, path=[(T(362) + 0.3, (1.3, -21.6, -0.2)), (E(362) + 0.3, (1.4, -23.5, 0.0))]),
           lina((1.0, -21.4, -0.2), who='lina', id='lina', face=(1.3, -21.6), expr='brave', path=[(T(362) + 0.3, (1.0, -21.4, -0.2)), (E(362) + 0.3, (1.05, -23.2, 0.0))],
                act=_A(reach(T(362), 1, ('kessler', 'hand_r'), dur=0.3))),
           adam((1.75, -21.3, -0.2), who='adam_sock', id='adam', face=(1.3, -21.6), expr='fierce_kind', path=[(T(362) + 0.3, (1.75, -21.3, -0.2)), (E(362) + 0.3, (1.8, -23.1, 0.0))],
                act=_A(reach(T(362), -1, ('kessler', 'hand_l'), dur=0.3)))],
      acts=cloak(('adam', 'lina', 'kessler')), cold=True, c=Z(2.0, 0.02, 960, 640), sfx=[(T(362) + 0.4, 'snow_steps', -6, 0, 'outside', dict(dur=2.0))])
    huddle = lambda kex='dazed', lex='kind_smile', lact=None, kact=None, **k: [
        kess((1.4, -23.55, 0.0), id='kessler', face=(1.4, -20.0), expr=kex, light=k.get('light', PINK_L), act=kact),
        lina((1.1, -23.25, 0.0), who='lina', id='lina', face=(1.4, -23.6), expr=lex, light=k.get('light', PINK_L),
             act=lact or _A(reach(-9, 1, ('kessler', 'hip'), dur=0.2), reach(-9, -1, ('kessler', 'hip'), dur=0.2))),
        adam((1.8, -23.2, 0.0), who='adam_sock', id='adam', face=(1.4, -23.6), expr='fierce_kind', light=k.get('light', PINK_L))]
    S(T(363), 'street', 'kdoor', st=KP, ppl=huddle(lact=_A()), acts=cloak(('adam', 'lina', 'kessler')), cold=True, c=Z(1.0, 0.02),
      sfx=[(T(363) + 0.1, 'blanket_wrap', -4, 0, 'outside')])
    BU(T(364), 'kessler_out', 'street', 'kdoor', KP, cx=1150, cy=470, scale=0.8, turn=-0.35, light=PINK_L, expr='dazed', cold=True,
       act=_A(lk(T(364) + 0.3, (800, 760), dur=0.6)),
       busts=[dict(who='lina', cx=820, cy=760, scale=0.8, turn=0.5, expr='cry_shut', light=PINK_L,
                   act=_A(lambda a, s: a._add(T(364), None, lambda P_, t: setattr(P_, 'dx', P_.dx + 60 * ease_out_back(clamp((t - T(364) - 0.1) / 0.4))))))],
       c=BZ(0.02))
    # 365 From the window, a little boy's voice.  366 Copied, like Mom's.  367 S mimic "Walter, I'm cold. Come to the window."
    BU(T(365), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=1.0, light=SH_PINK, mscale=0.27, meye=330.0,
       act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.2), lambda a, s: a.slow_wave(T(365), E(367) + 1, 1), lk(T(365), (700, 760))), c=BZ(0.02))
    sbm = lambda t, sc, cy, **k: BU(t, 'shiver', 'street', 'window_close', STO_B, cx=960, cy=cy, scale=sc, light=SH_PINK,
                                    act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.2), lambda a, s: a.slow_wave(t - 1, t + 4, 1), lk(t, (900, 820)), *(k.pop('acts_', []))), c=BZ(0.02), **k)
    sbm(T(366), 0.9, 620, acts_=[lambda a, s: a.head_tilt(T(366), 14.0, 1.2)])
    sbm(T(367), 1.1, 600)
    # 368 Mr. Kessler leans toward it.  369 Lina holds on tighter.  370 L "I'm Lina. You're not by yourself."  371 And the old man starts to shiver.
    S(T(368), 'street', 'kdoor', st=KP, ppl=huddle(kact=_A(lambda a, s: a.set(T(368) + 0.2, None, 0.8, lean=0.25), lk(T(368), (-3.6, -15.1, 1.6), dur=0.6))),
      acts=cloak(('adam', 'lina', 'kessler')), cold=True, c=Z(1.7, 0.02, 960, 520))
    BU(T(369), 'lina', 'street', 'kdoor', KP, cx=960, cy=620, scale=1.0, turn=0.3, light=PINK_L, expr='cry_shut', cold=True, act=_A(lambda a, s: a.head_tilt(T(369), -8.0, 0.8)),
       c=BZ(0.02))
    BU(T(370), 'lina', 'street', 'kdoor', KP, cx=960, cy=620, scale=0.95, turn=0.3, light=PINK_L, expr='kind_smile', cold=True, act=_A(lk(T(370), (1300, 200), dur=0.4)),
       c=BZ(0.015))
    BU(T(371), 'kessler_out', 'street', 'kdoor', KP, cx=960, cy=600, scale=0.95, turn=-0.3, light=PINK_L, expr='sad', cold=True,
       act=_A(lk(T(371), (700, 900), dur=0.6), tremblef(WD(371, 'shiver') - 0.1, None, 3.2)), c=BZ(0.02, shake=1.6))
    # 372 The song reaches the empty beat... and hangs there.  373 His jaw gapes for the last note... and can't close.
    S(T(372), 'street', 'kout', st=KP, ppl=[SHB(m=1.0, legs=True, lean=0.25, act=_A(lambda a, s: a.slow_wave(T(372) - 1, WD(372, 'hangs'), 1), lk(T(372), 'kdoor')))],
      c=Z(1.6, 0.03, 640, 520))
    # review (the hung note played on a static far wide): on "hangs" a cut to him FROZEN in his window, glove stuck mid-wave,
    # the jaw dropping for the note that never comes, the head ticking sideways
    th_ = W(372, 'hangs')
    BU(th_, 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=0.9, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.2), lambda a, s: a.slow_wave(th_ - 2, E(372) + 2, 1, period=60.0), lk(th_, (960, 760)),
              lambda a, s: a.jaw_gape(th_ + 0.1, E(372) + 2), lambda a, s: a.head_tilt(th_ + 0.3, 9.0, 0.25)), c=BZ(0.03))
    sbm(T(373), 1.0, 640, mscale=0.26, meye=320.0, acts_=[lambda a, s: a.jaw_gape(WD(373, 'gapes') - 0.1, E(373) + 2)])


# ==================================================================================================== THE PLOW, THE PORCH LIGHTS, BYE BENNY, MORNING (374-401)
def plan_dawn(F):
    KP = dict(ST_B, truck_open=1.0)
    # 374 Dad's plow roars onto Birch Lane.  375 Orange light.  376 Horn blaring, again and again.
    # review (a tiny static speck): it roars down the lane toward the lens and pulls up close
    pl = lambda t0: dict(x=lambda t: 18.0 - 21.0 * ease_out_cubic(clamp((t - t0) / 2.2)), y=-11.4, dir=-1, beacon=1.0)
    S(T(374), 'street', 'lane', st=dict(KP, plow=pl(T(374))), c=Z(1.2, 0.03, 900, 540), sfx=[(T(374), 'plow_roar', 2, 0, 'outside', dict(dur=3.0))])
    BU(T(375), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=1.0,
       light=dict(BEACON, rim_a=210, key=-0.05),
       act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.1), lambda a, s: a.jaw_gape(T(375) - 2, E(376) + 1), lk(T(375), (820, 780), dur=0.15, snap=True)), c=BZ(0.02))
    th = [WD(376, 'horn'), WD(376, 'again') , WD(376, 'again', 1)]
    BU(T(376), 'dad', None, None, cx=960, cy=600, scale=0.9, turn=0.3, expr='fierce_kind', plain=('#2a1c14', '#0a0706'), bg_fn=cab_bg(),
       light=dict(BEACON, rim_a=190), act=_A(lambda a, s: a.set(T(376), None, 0.2, lean=0.15), *[(lambda tt: lambda a, s: a.head_tilt(tt - 0.05, 7.0, 0.3))(tt) for tt in th]),
       hands=[dict(who='dad', fn=lambda t: (1180, 990 + 70 * max([math.exp(-((t - tt) / 0.12) ** 2) for tt in th]), -95.0, 1.0), size=300, shape='fist', side=1, sleeve_from=(1500, 1400))],
       c=BZ(0.02, shake=1.2), sfx=[(tt, 'plow_horn', 2, 0, 'outside') for tt in th])
    # 377 Porch lights click on.  378 One.  379 Another.  380 Doors open.
    on = lambda t1: (lambda t: clamp((t - t1) / 0.12))
    pt = [WD(377, 'click'), WD(378, 'one'), WD(379, 'another'), WD(380, 'doors')]
    # review (the porch lights and doors were unreadable): the far porches down the lane click on at "click", the house
    # across the lane at "One.", the one on our side at "Another.", then lit doorways open with neighbours stepping out
    PL = lambda: dict(KP, porches=[on(pt[2]), on(pt[0] + 0.25), on(pt[1]), on(pt[0])], plow=dict(x=-3.0, y=-11.4, dir=-1, beacon=1.0))
    S(T(377), 'street', 'lane', st=PL(), c=Z(1.5, 0.02, 1000, 520), sfx=[(tt, 'porch_light_click', -2, 0, 'outside') for tt in pt[:3]])
    S(T(378), 'street', 'lane', st=PL(), cam=cm((-8.6, -15.6, 1.6), (-10.0, -23.6, 1.2), 1000), c=Z(1.0, 0.02))
    S(T(379), 'street', 'lane', st=PL(), cam=cm((-14.0, -8.8, 1.6), (-14.8, -0.4, 1.2), 1000), c=Z(1.0, 0.02))
    S(T(380), 'street', 'lane', st=dict(PL(), kporch=1.0), cam=cm((-8.0, -13.8, 1.7), (-11.2, -23.0, 1.1), 950),
      acts=lambda A, sh, sp: [door_glow(sp, -11.0, -24.0, WD(380, 'doors') - 0.1)], c=Z(1.0, 0.02), sfx=[(WD(380, 'doors'), 'door_open_far', -6, 0, 'outside')])
    # 381 Cold.  382 Alone.  383 He needs both.  384 Mr. Kessler isn't either anymore.
    sbf = lambda t, sc, cy, **k: BU(t, 'shiver', 'street', 'window_close', STO_B, cx=960, cy=cy, scale=sc,
                                    light=dict(BEACON, rim_a=200, key=-0.05),
                                    act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.1), lambda a, s: a.jaw_gape(t - 2, t + 4), *(k.pop('acts_', []))), c=BZ(0.03), **k)
    sbf(T(381), 1.0, 600)
    S(T(382), 'street', 'kdoor', st=dict(KP, kporch=1.0), ppl=huddleB(), acts=cloak(('adam', 'lina', 'kessler')), cold=True, c=Z(1.2, 0.02))
    sbf(T(383), 1.25, 560, acts_=[lambda a, s: a.head_tilt(T(383), -10.0, 0.6)])
    S(T(384), 'street', 'kdoor', st=dict(KP, kporch=1.0), ppl=huddleB(kact=_A(tremblef(T(384) - 2, None, 1.2))), acts=cloak(('adam', 'lina', 'kessler')), cold=True,
      c=Z(1.0, 0.02, 960, 560, x1=960, y1=560, f1=1.25))
    # 385 The song falls apart.  386 The skull shrinks back into the smile.  387 S "See you when it's this cold again!"
    S(T(385), 'street', 'kout', st=dict(KP, kporch=1.0), ppl=[SHB(m=1.0, legs=True, lean=0.2, act=_A(lambda a, s: a.jaw_gape(T(385) - 2, E(385) + 1), lk(T(385), 'kdoor')))],
      c=Z(1.5, 0.02, 640, 520))
    BU(T(386), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=1.05, light=dict(SH_PINK, rim='#ffa040'),
       act=_A(pose(-9, None, 0.1, sh_m=1.0, ws_bend=0.1), lambda a, s: a.shrink_back(T(386) + 0.1, E(386) - T(386)),
              lambda a, s: a._add(T(386) + 0.1, None, _shrink_curve(T(386) + 0.1, E(386) - T(386)))),
       # review (it read as a cut to a medium): the camera pushes in WITH the shrink, holding on the skull as it shrinks
       # back into the smile, landing on his face (the L387 close-up's size)
       c=dict(mv='push', x=960, y=430, rate=0.0, z1=2.2, free=True),
       sfx=[(T(386) + 0.1, 'skin_stretch', -4, 0, 'outside')])
    BU(T(387), 'shiver', 'street', 'window_close', STO_B, cx=960, cy=600, scale=0.95, light=dict(SH_PINK, rim='#ffa040'),
       act=_A(pose(-9, None, 0.1, ws_bend=0.2), lambda a, s: a.slow_wave(T(387), E(387) + 1, 1), lk(T(387), (1400, 700))), c=BZ(0.02))
    # 388 The truck glides into the white.
    S(T(388), 'street', 'kout', st=dict(KP, truck=None, porches=1.0, kporch=1.0),
      acts=lambda A, sh, sp: truck_live(sp, glide(T(388) - 0.2, E(388) + 2.5, ST.IC_TRUCK_B[0], -30.0), y=ST.IC_TRUCK_B[1], fa=-90.0),
      post_fn=lambda t: dict(white=0.55 * ease_in_out(clamp((t - T(388) - 0.5) / 1.2))), c=Z(1.0, 0.02), sfx=[(T(388), 'truck_glide', -4, 0.3, 'outside', dict(dur=3.0))])
    # 389 Lina's mitten drops into the snow.  390 The red one stays.  391 Swinging.
    td = WD(389, 'drops')
    IN(T(389), 'mittens', lambda u: dict(lina=True, drop=clamp((u + T(389) - td + 0.25) / 0.5)), c=dict(mv='push', rate=0.02),
       sfx=[(td + 0.3, 'mitten_drop', -6, 0, 'outside')])
    # review (it blinked off the string): it slips off the peg and tumbles out of frame, then lands in the snow where his
    # truck stood (on the sound)
    mland = (-2.3, -15.8, FOOT)
    S(td + 0.22, 'street', 'kout', st=dict(KP, truck=None, porches=1.0, kporch=1.0), cam=cm((-2.3, -17.7, 0.5), (-2.3, -15.8, -0.4), 1100),
      acts=lambda A, sh, sp: [mitten_fall(sp, mland, td + 0.3)], c=Z(1.0, 0.02))
    IN(T(390), 'mittens', dict(lina=True, drop=1.0), motion=lambda u: (700 * ease_in_out(clamp(u / 0.8)), 0.0, 0.9 * ease_in_out(clamp(u / 0.8)), 0.0), c=dict(mv='hold'))
    IN(T(391), 'mittens', dict(lina=True, drop=1.0), motion=lambda u: (700.0, 0.0, 1.1, 4.0 * math.sin(u * 4.0)), c=dict(mv='hold'))
    # 392 Mr. Kessler whispers,  393 K "Bye, Benny."
    BU(T(392), 'kessler_out', 'street', 'kdoor', dict(KP, truck=None, kporch=1.0), cx=960, cy=600, scale=0.9, turn=-0.3, light=dict(LAMP, rim_a=90), expr='sad', cold=True,
       act=_A(lk(T(392), (300, 500), dur=0.8), tremblef(T(392) - 2, None, 0.8)), c=BZ(0.015))
    BU(T(393), 'kessler_out', 'street', 'kdoor', dict(KP, truck=None, kporch=1.0), cx=960, cy=580, scale=1.2, turn=-0.3, light=dict(LAMP, rim_a=90), expr='tender', cold=True,
       act=_A(lk(T(393), (300, 500)), tremblef(T(393) - 2, None, 0.6)), c=BZ(0.015))
    # 394 Paramedics said twenty more minutes, and he wouldn't have woken up.
    S(T(394), 'street', 'kdoor', st=dict(KP, truck=None, kporch=1.0, porches=1.0),
      ppl=[kess((1.4, -23.55, 0.0), id='kessler', face=(1.4, -20.0), expr='tender', light=dict(rim='#ff5050', rim_a=110, side=1, key=-0.15)),
           P('medic_a', (0.85, -23.1, 0.0), face=(1.4, -23.55), expr='focused', path=[(T(394) - 0.2, (0.45, -22.3, -0.17)), (T(394) + 0.7, (0.85, -23.1, 0.0))],
             act=_A(reach(T(394) + 0.8, 1, ('kessler', 'chest'), dur=0.5))),
           P('medic_b', (2.0, -23.0, 0.0), face=(1.4, -23.55), expr='kind_smile', path=[(T(394), (2.45, -22.2, -0.17)), (T(394) + 0.9, (2.0, -23.0, 0.0))],
             act=_A(reach(T(394) + 1.0, -1, ('kessler', 'shoulder_r'), dur=0.5)))],
      acts=cloak(('kessler',), c='#6a3b52'), cold=True, c=Z(1.0, 0.02), sfx=[(T(394), 'ambulance_far', -8, 0, 'outside', dict(dur=3.0))])
    # 395 In the morning, Dad, Lina and I shovel his walk.  396 His chimney smokes again.  397 Lina brings him cocoa.
    # review (a static row, nobody shovelling): each one scoops and throws in their own rhythm (the hands drive the shovel:
    # low hand pushes the blade out along the walk and lifts, the body leans into it), staggered in depth on the walk
    def shv(who, at, seed, **k):
        fx_, fy_ = 0.6, 0.4
        ph, w = seed * 1.7, 3.6 + 0.35 * seed
        h = {'dad': 1.8, 'adam': 1.4}.get(who, 1.15)                  # within arm's reach of each one's shoulders
        lo = lambda s: (lambda t: scr(s.sp, (at[0] + fx_ * h * (0.26 + 0.06 * math.sin(w * t + ph)), at[1] + fy_ * h * (0.26 + 0.06 * math.sin(w * t + ph)),
                                             FOOT + h * (0.44 + 0.06 * max(0.0, math.sin(w * t + ph + 1.3))))))
        hi = lambda s: (lambda t: scr(s.sp, (at[0] + fx_ * h * (0.1 + 0.03 * math.sin(w * t + ph)), at[1] + fy_ * h * (0.1 + 0.03 * math.sin(w * t + ph)),
                                             FOOT + h * (0.66 + 0.03 * math.sin(w * t + ph + 1.3)))))
        return P(who, at, face=(at[0] + fx_, at[1] + fy_), seed=seed, extras=[shovel_fx(k.pop('sc', '#c8402a'))],
                 act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.3),
                        lambda a, s: a.reach_to(-9, 1, lo(s), t1=None, dur=0.2, shape='grip'), lambda a, s: a.reach_to(-9, -1, hi(s), t1=None, dur=0.2, shape='grip'),
                        lambda a, s: a._add(-1e9, None, lambda P_, t: setattr(P_, 'lean', P_.lean + 0.22 * math.sin(w * t + ph)))), **k)
    MG = 'ic_morning_gold'
    S(T(395), 'morning', 'kporch', st={}, era='morning', cold=True, grade=MG,
      ppl=[shv('dad', (0.8, -19.7, FOOT), 1, expr='warm_smile'), shv('adam', (1.9, -20.6, FOOT), 2, expr='kid_grin', sc='#3a6ac8'),
           shv('lina', (1.1, -21.5, FOOT), 3, expr='kid_grin', sc='#e8a020')],
      c=Z(1.5, 0.02, 1000, 680), sfx=[(T(395) + 0.3 + 0.7 * k, 'shovel_scrape', -6, 0.2 * (k - 1), 'outside') for k in range(4)])
    # review (neither the chimney nor its smoke was in frame): from our yard across the lane, his chimney smoking
    S(T(396), 'morning', 'kessler', st={}, era='morning', grade=MG, c=Z(1.9, 0.03, 720, 400))
    S(T(397), 'morning', 'kporch', st={}, era='morning', cold=True, grade=MG,
      ppl=[kess('kporch', who='kessler_am', id='kessler', face=(1.4, -21.0), expr='tender', act=_A(lk(T(397), ('lina', 'head')))),
           lina((1.2, -21.9, -0.17), who='lina', id='lina', face=(1.4, -23.1), expr='kid_grin', extras=[mug_fx('hand_r')],
                path=[(T(397) - 0.3, (1.2, -21.3, -0.3)), (E(397) + 0.2, (1.2, -22.55, -0.1))],
                act=_A(lk(T(397), ('kessler', 'head')), reach(T(397) - 0.2, 1, ('kessler', 'hip'), dur=0.6)))], c=Z(1.3, 0.02, 960, 620))
    # 398 K "Sixty-eight years I taped rules on every door on this street. First time anyone knocked on mine."
    BU(T(398), 'kessler_am', 'morning', 'kporch', {}, cx=960, cy=600, scale=0.9, turn=-0.3, light=MORNING, expr='tender', era='morning', cold=True, grade=MG,
       act=_A(lk(T(398), (500, 760))), c=BZ(0.012))
    S(W(398, 'first'), 'morning', 'kporch', st={}, era='morning', cold=True, grade=MG, cam=cm((0.4, -20.6, 1.0), (1.35, -23.0, 1.0), 1250),
      ppl=[kess('kporch', who='kessler_am', id='kessler', face=(1.0, -22.6), expr='tender', extras=[mug_fx('hand_l')],
                act=_A(lk(W(398, 'first'), ('lina', 'head')), reach(-9, -1, ('kessler', 'chest'), dur=0.1))),
           lina((1.0, -22.6, -0.1), who='lina', id='lina', face=(1.4, -23.1), expr='kid_grin', act=_A(lk(W(398, 'first'), ('kessler', 'head'))))],
      c=Z(1.0, 0.015))
    # 399 Two nights later, across town... a chime.  400 Ending on a note that isn't there.  401 The truck slows at a house with no chimney smoke.
    # the live layer is anchored (and culled) at x(0.0): answer the kerb stop there, so the truck is never culled off-frame
    tx = lambda t0, t1: (lambda t: ST.IC_TRUCK_B[0] - 4.5 if t <= 0.0 else lerp(ST.IC_TRUCK_B[0] - 14.0, ST.IC_TRUCK_B[0] - 4.5, ease_out_cubic(clamp((t - t0) / max(0.1, t1 - t0)))))
    S(T(399), 'town', 'town', st=dict(truck=False), acts=lambda A, sh, sp: truck_live(sp, tx(T(399), E(401)), y=ST.IC_TRUCK_B[1], fa=90.0), c=Z(1.0, 0.02))
    S(T(400), 'town', 'town', st=dict(truck=False), acts=lambda A, sh, sp: truck_live(sp, tx(T(399), E(401)), y=ST.IC_TRUCK_B[1], fa=90.0), c=Z(1.25, 0.02, 1000, 520))
    S(T(401), 'town', 'town', st=dict(truck=False), acts=lambda A, sh, sp: truck_live(sp, tx(T(399), E(401)), y=ST.IC_TRUCK_B[1], fa=90.0), c=Z(1.35, 0.03, 820, 470), sfx=[(T(401) + 0.3, 'truck_glide', -6, 0, 'outside', dict(dur=2.0))])


def huddleB(kact=None):
    return [kess((1.4, -23.55, 0.0), id='kessler', face=(1.4, -20.0), expr='sad', light=dict(LAMP, rim_a=90), act=kact),
            lina((1.1, -23.25, 0.0), who='lina', id='lina', face=(1.4, -23.6), expr='kind_smile', light=dict(LAMP, rim_a=90),
                 act=_A(reach(-9, 1, ('kessler', 'hip'), dur=0.2), reach(-9, -1, ('kessler', 'hip'), dur=0.2))),
            adam((1.8, -23.2, 0.0), who='adam_sock', id='adam', face=(1.4, -23.6), expr='fierce_kind', light=dict(LAMP, rim_a=90))]


# ==================================================================================================== RULE 8 AND THE OUTRO (402-427)
def plan_outro(F):
    IN(T(402), 'rules', dict(show=7, eighth=True, door='ours'), motion=lambda u: (0.0, -320.0 * ease_in_out(clamp(u / 1.2)), 0.4 * ease_in_out(clamp(u / 1.2)), 0.0),
       c=dict(mv='hold'), sfx=[(T(402) + 0.2, 'pencil_write', -8, 0, 'close', dict(dur=1.0))])
    RULE(T(403), 8)
    # 407 There's no Mister Shiver.  408 But real cold hunts the same way.  409 Whoever's alone.
    S(T(407), 'morning', 'lane', st={}, era='outro', c=Z(1.05, 0.02))
    S(T(408), 'town', 'town', st=dict(truck=False), c=Z(1.0, 0.02))
    S(T(409), 'town', 'town', st=dict(truck=False), c=Z(1.6, 0.02, 820, 500))
    # 410-420 the advice, legible while it is read
    zin = lambda dy: (lambda u: (0.0, dy * ease_in_out(clamp(u / 0.5)), 0.3 * ease_in_out(clamp(u / 0.5)), 0.0))
    for i0, n, mo in ((410, 0, None), (411, 0, zin(170)), (412, 0, zin(-70)), (413, 1, None), (414, 1, zin(150)), (416, 2, None), (417, 3, None), (418, 3, zin(60))):
        IN(T(i0), 'outro', dict(n=n), era='outro', motion=mo, c=dict(mv='push', rate=0.012))
    F.cut(T(420), 'endB', mode='knock', era='outro', t_k=WD(420, 'knock'), sfx=[(WD(420, 'knock') + 0.25 * j, 'knock_door', -4, 0, 'close', dict(n=1, kind='warm', index=j)) for j in range(3)])
    # 421 Said "inside"? Good.  423 Now... who on your street is inside alone?
    F.cut(T(421), 'endB', mode='inside', t_good=WD(422, 'good'), t_q=WD(423, 'who'), era='outro', sfx=[(WD(422, 'good'), 'ui_pop', -6, 0, 'close'), (WD(423, 'who'), 'ui_pop', -6, 0, 'close')])
    F.cut(T(424), 'endB', mode='like', era='outro', hit_t=WD(424, 'like') + 0.25,
          sfx=[(WD(424, 'like') + 0.25 + d_, 'knock_door', 2 if d_ == 0 else -2, 0, 'close', dict(n=1, kind='like', index=j)) for j, d_ in enumerate((-0.36, -0.18, 0.0))])
    F.cut(T(425), 'endB', mode='sub', era='outro', t_sub=WD(425, 'subscribe'), sfx=[(WD(425, 'subscribe'), 'ui_pop', -4, 0, 'close'), (WD(425, 'subscribe') + 0.2, 'blanket_wrap', -8, 0, 'close')])
    F.cut(T(426), 'endB', mode='next', era='outro', t_dont=WD(427, "don't"), sfx=[(T(426) + 0.3, 'wind_gust', -10, 0, 'outside')])


def B_endB(F, sh):
    """The outro's own cards (warm, short): 'inside' (Said INSIDE? GOOD. -> a row of houses, one alone), 'like' (a warm
    door knocked on three times -> LIKE), 'sub' (SUBSCRIBE: one blanket round a little house), 'next' (the next-time card:
    a snowman overnight, facing a lit window)."""
    p = sh.p
    t0 = sh.t0
    mode = p['mode']
    warm = ('#3a2418', '#120a08') if mode != 'next' else ('#16203a', '#05070e')
    layers = [Layer(4.0, lambda pen, t: pen.linear(rect(-1200, -900, 4320, 2880), 0, -400, 0, 1480, [warm[0], warm[1]]), 'card_bg', blur=0)]

    def snow(pen, t, n=70, a=150):
        rng = np.random.default_rng(11)
        for i in range(n):
            x, y, s_ = rng.uniform(0, 1920), rng.uniform(0, 1080), rng.uniform(0.4, 1.0)
            pen.fill(oval((x + 15 * math.sin(t * 0.6 + i)) % 1920, (y + 40 * t * s_) % 1080, 2.0 + 2.5 * s_), '#ffffff', a * s_)

    def hud(cv, t):
        pen = Pen(cv)
        u = t - t0
        k = clamp(u / 0.35)
        snow(pen, t)
        if mode == 'inside':
            tg, tq = p['t_good'], p['t_q']
            if t < tq:
                _house_icon(pen, 960, 760, 0.8, 255 * k, 1.0, t)
                text(cv, 'SAID "INSIDE"?', 960, 250, 1400, 76, '#ffd890', 250 * k, 0.1, 'center', 0.6)
                kg = ease_out_back(clamp((t - tg) / 0.3))
                if t >= tg: text(cv, 'GOOD.', 960, 870, 900, 64 * max(0.3, kg), '#ffffff', 250 * clamp(kg), 0.15, 'center', 0.6)
            else:
                kq = clamp((t - tq) / 0.4)
                xs = [260, 610, 960, 1310, 1660]
                for j, x_ in enumerate(xs):
                    alone = (j == 3)
                    _house_icon(pen, x_, 800, 0.5, 255 * kq, 0.15 if alone else 1.0, t + j)
                    if alone:
                        pulse = 0.5 + 0.5 * math.sin((t - tq) * 4.0)
                        pen.glow(x_, 660, 220, '#ffd890', 60 + 60 * pulse)
                        pen.line(oval(x_, 680, 190, 200), 4.0, '#ffd890', 200 * kq * (0.6 + 0.4 * pulse))
                text(cv, 'WHO ON YOUR STREET IS', 960, 230, 1600, 60, '#ffffff', 245 * kq, 0.15, 'center', 0.5)
                text(cv, 'INSIDE ALONE?', 960, 320, 1600, 84, '#ffd890', 250 * kq, 0.1, 'center', 0.6)
        elif mode == 'knock':
            tk_ = p['t_k']
            card = rrect(200, 170, 1520, 740, 40)
            pen.fill(moved(card, 14, 22), '#000000', 120 * k, blur=24); pen.fill(card, '#f6eedf', 255 * k); pen.line(card, 4, '#a87a48', 255 * k)
            door = rrect(1380, 330, 220, 420, 12)
            pen.fill(door, '#6a3a24', 255 * k); pen.line(door, 4, '#2a160c', 255 * k); pen.fill(oval(1560, 560, 10), '#d8b060', 255 * k)
            for j in range(3):
                kk = clamp((t - tk_ - 0.25 * j) / 0.08) * (1 - clamp((t - tk_ - 0.25 * j - 0.25) / 0.3))
                pen.glow(1490, 470, 90, '#ffb860', 130 * kk)
            text(cv, 'This week, with a grown-up:', 790, 300, 1000, 40, '#3a2a20', 240 * k, 0.0, 'center', 0.4)
            text(cv, 'KNOCK ON THE DOOR', 790, 470, 1000, 76, '#b8322a', 250 * k, 0.04, 'center', 0.6)
            text(cv, 'OF SOMEONE', 790, 570, 1000, 76, '#b8322a', 250 * k, 0.04, 'center', 0.6)
            text(cv, 'WHO LIVES ALONE.', 790, 670, 1000, 76, '#b8322a', 250 * k, 0.04, 'center', 0.6)
        elif mode == 'like':
            th = p['hit_t']
            door = rrect(760, 220, 400, 700, 16)
            pen.fill(door, '#6a3a24', 255 * k); pen.line(door, 5, '#2a160c', 255 * k)
            pen.fill(oval(1100, 600, 18), '#d8b060', 255 * k)
            for j, tk in enumerate((th - 0.36, th - 0.18, th)):
                kk = clamp((t - tk) / 0.08) * (1 - clamp((t - tk - 0.3) / 0.3))
                pen.glow(960, 520 - 40 * j, 120, '#ffd890', 120 * kk)
            kb = ease_out_back(clamp((t - th) / 0.35))
            if t >= th:
                cv.save(); cv.translate(960, 560); cv.scale(max(0.01, kb), max(0.01, kb))
                pen.fill(rrect(-170, -40, 120, 200, 20), '#ffd890'); pen.line(rrect(-170, -40, 120, 200, 20), 6, '#2a160c')
                th_ = smooth([(-40, 160), (-40, -40), (20, -60), (40, -180), (90, -170), (90, -60), (180, -50), (170, 160)], True)
                pen.fill(th_, '#ffd890'); pen.line(th_, 6, '#2a160c')
                cv.restore()
                text(cv, 'LIKE', 1440, 580, 600, 80, '#ffffff', 250 * clamp(kb), 0.2, 'center', 0.6)
            text(cv, "IF YOU'D HAVE CROSSED THE STREET", 960, 140, 1600, 46, '#ffd890', 240 * k, 0.15, 'center', 0.5)
        elif mode == 'sub':
            ts = p['t_sub']
            _house_icon(pen, 960, 640, 0.6, 255 * k, 1.0, t)
            kw = ease_in_out(clamp((t - ts - 0.2) / 0.7))
            pen.fill(smooth([(760, 680 - 380 * kw), (1160, 680 - 380 * kw), (1190, 680), (730, 680)], True), '#6a3b52', 230 * kw)     # the blanket round the house
            kb = ease_out_back(clamp((t - ts) / 0.35))
            b = rrect(660, 730, 600, 120, 60)
            pen.fill(b, '#c8402a', 255 * clamp(kb)); pen.line(b, 4, '#ffd890', 200 * clamp(kb))
            text(cv, 'SUBSCRIBE', 960, 790, 600, 58, '#ffffff', 255 * clamp(kb), 0.15, 'center', 0.6)
            text(cv, "SO NOBODY'S LEFT OUT IN THE COLD", 960, 150, 1600, 46, '#ffd890', 240 * k, 0.15, 'center', 0.5)
        else:
            win = rrect(1160, 300, 360, 300, 10)
            pen.fill(rect(0, 760, 1920, 320), '#3a4a70', 255 * k)
            pen.fill(rect(1060, 200, 860, 560), '#2a3048', 255 * k)
            pen.fill(win, '#ffd890', 230 * k); pen.line(win, 8, '#14182a', 255 * k)
            pen.seg((1340, 300), (1340, 600), 6, '#14182a', 255 * k); pen.seg((1160, 450), (1520, 450), 6, '#14182a', 255 * k)
            sx, sy = 640, 760
            for (dy, r) in ((-110, 120), (-300, 90), (-440, 66)):
                pen.fill(oval(sx, sy + dy, r), '#eef4ff', 255 * k); pen.line(oval(sx, sy + dy, r), 3, '#8a9ac0', 200 * k)
            for ex_ in (-22, 22):                                     # coal eyes, turned toward the window
                pen.fill(oval(sx + 30 + ex_, sy - 452, 8), '#14141a', 255 * k)
            pen.fill(poly([(sx + 40, sy - 430), (sx + 120, sy - 420), (sx + 40, sy - 414)]), '#e87a2a', 255 * k)
            pen.line(smooth([(sx + 10, sy - 400), (sx + 40, sy - 392), (sx + 70, sy - 400)], False), 4, '#14141a', 255 * k)
            text(cv, 'NEXT TIME', 960, 120, 900, 44, '#9fd8ff', 230 * k, 0.4, 'center', 0.5)
            td = p.get('t_dont')
            if td and t >= td:
                text(cv, "DON'T KNOCK IT DOWN.", 960, 840, 1600, 64, '#ffffff', 250 * clamp((t - td) / 0.25), 0.12, 'center', 0.6)
        text(cv, CHANNEL, 960, 1040, 600, 22, '#c8ccd8', 170 * k, 0.4, 'center', 0.4)
    return Spec(layers, scam(sh, None, dict(mv='hold', free=True)), None, 'neutral', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=hud)


BUILDERS['endB'] = B_endB


# ==================================================================================================== film-wide music (the chime by version)
def plan_globals(F):
    """Film-wide music cues keyed to lines: HIS chime (the returning tune) by version (W/mix/chime_ice: burst, three, far,
    closer, outside, lullaby, warped, climax, stinger, warm, bells)."""
    g = F.globals
    n = len(F.L)

    def J(i0, i1, version, level, off0=0.0, **k):
        if i1 >= n: return
        g.append(dict({'t': round(T(i0) + off0, 3), 'type': 'jingle', 'level': level, 'len': round(F.t(i1) - T(i0) - off0, 2), 'version': version}, **k))
    g.append({'t': round(T(0) + 0.2, 3), 'type': 'drone', 'level': 0.35, 'len': round(F.t(4) - T(0), 2), 'version': 'cold_open'})
    J(3, 4, 'burst', 0.5)
    J(45, 47, 'far', 0.25)
    J(47, 54, 'closer', 0.35)
    J(144, 145, 'bells', 0.12)
    J(151, 152, 'bells', 0.12)
    J(160, 163, 'bells', 0.4)
    J(174, 199, 'warped', 0.28, loop=True)             # the song she walks out humming (the door swinging open .. the transformation)
    J(199, 227, 'outside', 0.45, loop=True)            # cheerful and undistorted through the whole transformation
    J(248, 250, 'bells', 0.4)
    # part B: the song at our door and in the attic, moving away, at Kessler's door, the crossing, the hung note, across town
    J(268, 286, 'warped', 0.22, loop=True)
    J(289, 306, 'warped', 0.18, loop=True)
    J(307, 312, 'outside', 0.3)
    J(312, 331, 'outside', 0.35, loop=True)
    J(336, 372, 'warped', 0.3, loop=True)
    J(372, 386, 'climax', 0.55)
    J(395, 399, 'warm', 0.3)
    J(399, 402, 'far', 0.32)
    J(407, 421, 'warm', 0.2, loop=True)




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

