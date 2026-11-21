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


CLOCK_KEYS = [(43, _hm(23, 2)), (168, _hm(26, 10)), (267, _hm(27, 5))]
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
    sh.A = ADict({who: a})
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
        H.rule_card(cv, n, RULE_TEXT[n], tt_, total=8 if n == 8 else 7, icon=None, scrim=0.45, accent='#9fd8ff', plate=0.86)
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
        text(cv, 'ONE WORD IN THE COMMENTS', 960, 230, 800, 52, '#ffffff', 245 * kw, 0.2, 'center', 0.5)
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
            text(cv, 'REMEMBER YOUR ANSWER.', 960, 900, 800, 40, '#e6f1ff', 240 * clamp((t - tr) / 0.3), 0.22, 'center', 0.5)
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
    if s.kind in ('rule', 'black', 'card', 'outro'): return None
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
        ek += DARK_LIFT                     # the dead house: dark, but the action must read (bus-film lesson: night shots too dark)
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


def mitts(c='#e87aa4'):
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


def held_mitten(part, c='#e87aa4', t0=-99.0, t1=None):
    """One of Lina's mittens on his leg tip / in a hand (the pluck, L243)."""
    def fx(pen, t, a):
        if t < t0 or (t1 is not None and t >= t1): return
        try: x, y = a.where(t, part)
        except Exception: return
        s = a.height * 0.022
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


def nest_blanket(ids=('adam', 'lina'), c='#3b3150', c2='#56496e', empty=0.0):
    """acts: ONE blanket over the kids on the couch (L135+): a quilt laid over them from the chest to the knees, drawn in
    front of their figures and following their bodies (breathing, leaning); empty > 0 keeps a hollow on the right where
    Lina slept (L173: the blanket beside me is cold)."""
    def acts(A, sh, sp):
        who = [k for k in ids if k in A]
        if not who: return []
        lays = [sh.I[k]['layer'] for k in sh.I if k in who or any(k in ALIAS.get(w, ()) for w in who)]
        def draw(pen, t):
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
    S(T(0), 'street', 'lane', st=dict(ST_NONE, truck=None), acts=lambda A, sh, sp: truck_live(sp, gx), c=Z(1.25, 0.03, 980, 560),
      sfx=[(T(0), 'truck_glide', -8, 0.3, 'outside', dict(dur=4.0)), (T(0), 'cold_night', -10, 0, 'outside', dict(dur=5.0))])
    S(W(0, "don't"), 'hall', 'doorclose', st=dict(HALL_A, hall=0.25, lamp=0.0, pink=1.0), c=Z(1.0, 0.03))
    # 1 "If he leaves a free one on your porch... don't touch it."
    IN(T(1), 'doormat', dict(wrapper=True), c=dict(mv='push', rate=0.04), sfx=[(T(1) + 0.1, 'cone_set', -10, 0, 'close')])
    td = WD(1, "don't")
    IN(W(1, "don't"), 'doormat', dict(wrapper=True), c=dict(mv='push', f=1.25, rate=0.03),
       hands=[dict(who='lina_pj', fn=slide(td - 0.3, td + 0.45, (1180, 1300), (1010, 760), 160, 168,
                                           extra=lambda t, r: (r[0] + 60 * ease_in_out(clamp((t - td - 0.75) / 0.45)), r[1] + 200 * ease_in_out(clamp((t - td - 0.75) / 0.45)), r[2], r[3])),
                   size=260, shape='open', side=-1, sleeve_from=(1400, 1500))])
    # 2 "And if Mom knocks... and her breath doesn't show... don't open the door."
    S(T(2), 'hall', 'doorclose', st=dict(HALL_A, hall=0.3, lamp=0.0, pink=1.0),       # her shadow on the frosted glass (drawn over the door, faint)
      ppl=[P('shiver_mom', (-2.1, -0.45, 0.0), face=(-2.1, 2.0), sil=0.5, sil_rim='#ff9ec8', sil_rim_a=0.25, dorder=-6.0,
             light=PINK, talk=False, breath=False, act=_A(lambda a, s: a.knock(T(2) + 0.12, 3, 0.3)))],
      sfx=[(T(2) + 0.12 + 0.3 * k, 'door_tap', -2 + 2 * (k == 2), 0, 'inside', dict(kind='knock', n=1, index=k)) for k in range(3)], c=Z(1.0, 0.02))
    BU(W(2, 'breath'), 'shiver_mom', 'hall', 'doorclose', dict(HALL_A, hall=0.2, lamp=0.0), cx=960, cy=560, scale=0.7, light=PINK_D, cold=False,
       act=_A(lk(T(2) - 1, (960, 700))), c=BZ(0.025), post=dict(blur=0))
    C(W(2, "don't"), 'set', room='hall', view='door', set=dict(HALL_A, hall=0.25, lamp=0.0, pink=1.0),
      ppl=[adam('door_in', face=(-1.74, 0.0), expr='stern_afraid', act=_A(reach(W(2, "don't") + 0.05, 1, 'lock', dur=0.3, shape='pinch')))],
      sfx=[(F.w(2, 'door') + 0.0, 'deadbolt', 0, -0.2, 'inside', dict(kind='throw'))], c=Z(1.0, 0.02, hit=[F.w(2, 'door')]))
    # 3 S "Who's cold? Who wants a free one? Just come to the window!"  (his voice: no lip sync; he is busy at the window)
    stw = dict(truck_open=1.0)
    BU(T(3), 'shiver', 'street', 'window_close', stw, cx=960, cy=600, scale=0.78, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, ws_bend=0.18), lambda a, s: a.slow_wave(s.t0, s.t1 + 1, 1), lk(T(3) + 0.3, (1500, 600), dur=0.25, snap=True),
              lk(W(3, 'who', 1) + 0.1, (500, 640), dur=0.25, snap=True), lk(W(3, 'just') - 0.2, (960, 560), dur=0.2, snap=True)),
       c=BZ(0.03), sfx=[(T(3) - 0.05, 'serving_window', -6, 0, 'outside')])
    BU(W(3, 'just'), 'shiver', 'street', 'window_close', stw, cx=960, cy=640, scale=1.15, light=SH_PINK,
       act=_A(pose(-9, None, 0.1, ws_bend=0.3), lambda a, s: a.reach_far(s.t0 + 0.05, 1, (980, 900), dur=0.8, z=80.0)), c=BZ(0.04))
    # 4 "That's Mister Shiver."
    S(T(4), 'street', 'truck', st=ST_A, ppl=[SH(lean=0.22, act=_A(lambda a, s: a.slow_wave(s.t0, s.t1 + 1, 1), lk(T(4), (960, 760))))],
      tags=[tagc(WD(4, 'mister'), 'MISTER SHIVER', 'red', 960, 170, 2.0)], c=Z(1.5, 0.03, 900, 470))
    # 5-8
    S(T(5), 'street', 'house', st=ST_A, ppl=[SH(lean=0.1, light=SH_PINK)], c=Z(1.3, 0.03, 820, 540),
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
    IN(T(15), 'radio', dict(talk=0.0, static=0.0), c=dict(mv='push', rate=0.05))
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
    S(T(30), 'y58', 'mitten', st={}, era='memory', grade='ic_1958_red', c=Z(1.0, 0.03))
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
    S(T(63), 'living', 'wide', st=LIV_SHUT, ppl=[lina((2.9, 2.9, 0.0), path=[(T(63), (2.9, 2.9, 0.0)), (E(63) + 0.5, (3.4, 0.55, 0.0))], surface='inside_quiet',
                                                      expr='kid_grin')], c=Z(1.15, 0.02, 900, 580))
    tcr = T(64) + 0.5
    S(T(64), 'living', 'window', st=dict(LIV_SHUT, curtains=lambda t: 0.04 * ease_in_out(clamp((t - tcr) / 0.6))),
      ppl=[lina((3.45, 0.5, 0.0), face=(3.4, -2.0), act=_A(reach(tcr - 0.2, 1, 'curtain_crack', t1=tcr + 0.9, dur=0.3, shape='pinch')))], c=Z(1.4, 0.02, 900, 600))
    # 65-68 the truck glides in (no tracks); pink and white; the warm pink window; no tire tracks
    g65 = glide(T(65), E(66) + 0.3, 24.0, ST.IC_TRUCK_A[0])
    S(T(65), 'street', 'lane', st=dict(truck=None, win=dict(liv=0.6)), acts=lambda A, sh, sp: truck_live(sp, g65), c=Z(1.2, 0.02, 900, 560),
      sfx=[(T(65), 'truck_glide', -4, 0.2, 'outside', dict(dur=2.5))], music=[(T(65), 'jingle', 0.45, round(WD(84, 'stops') + 0.25 - T(65), 2), dict(version='outside', loop=True))])
    S(T(66), 'street', 'yard', st=dict(truck=None, win=dict(liv=0.6)), acts=lambda A, sh, sp: truck_live(sp, g65), c=Z(1.3, 0.02, 640, 470))
    S(T(67), 'street', 'window_close', st=dict(truck='A'), c=Z(1.0, 0.03))
    S(T(68), 'street', 'lane', st=ST_A, c=Z(1.4, 0.03, 1000, 600))
    # 69 He leans out.
    S(T(69), 'street', 'truck', st=ST_A, ppl=[SH(act=_A(pose(T(69), None, 0.6, ws_bend=0.28), lk(T(69), (960, 820))))], c=Z(1.6, 0.02, 880, 470),
      sfx=[(T(69) + 0.1, 'serving_window', -8, 0, 'outside')])
    # 70-73 Bald. Chalk-white. Tiny blue eyes. A smile too wide, front teeth sticking out.
    wc = dict(truck_open=1.0)
    BU(T(70), 'shiver', 'street', 'window_close', wc, cx=960, cy=760, scale=0.9, light=SH_PINK, act=_A(pose(-9, None, 0.1, ws_bend=0.2, h_tilt=-8.0),
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
    S(T(77), 'street', 'kessler', st=ST_A, ppl=[SH(face=(-0.5, -2.0), lean=0.15, act=_A(lk(T(77) + 0.3, 'kwindow', dur=0.7, body=0.3)))], c=Z(1.2, 0.02, 1100, 520))
    BU(T(78), 'shiver', 'street', 'window_close', wc, cx=1000, cy=640, scale=1.0, turn=0.35, light=SH_PINK,
       act=_A(lk(T(78), (300, 520)), lambda a, s: a.set(T(78), None, 0.6, sh_smile=0.06), lambda a, s: a.slow_wave(T(78) + 0.2, E(78) + 1, -1)), c=BZ(0.02))
    # 79 Then at Lina, through the crack.  (POV through the crack: his eyes snap to us)
    S(T(79), 'street', 'gap', st=ST_A, ppl=[SH(lean=0.18, act=_A(lk(T(79) - 0.5, 'kwindow'), lk(WD(79, 'lina'), (960, 520), dur=0.1, snap=True)))],
      c=Z(1.3, 0.02, 975, 470))
    BU(T(80), 'shiver', 'street', 'window_close', wc, cx=960, cy=560, scale=1.3, light=SH_PINK,
       act=_A(lk(T(80), (960, 520)), lambda a, s: a.set(T(80) + 0.2, None, 1.3, sh_smile=0.32)), c=BZ(0.035))
    # 81-83 the streetlight flickers; GLIMPSE 1
    fl = ST.ic_flicker(WD(81, 'flickers'), n=4, gap=0.45)
    S(T(81), 'street', 'truck', st=dict(ST_A, street=fl), ppl=[SH(lean=0.2, act=_A(lk(T(81), (960, 800))))], c=Z(1.4, 0.02, 900, 480),
      sfx=[(WD(81, 'flickers'), 'streetlight_buzz', -8, -0.4, 'outside')])
    tg = WD(82, 'flicker') + 0.05
    BU(T(82), 'shiver', 'street', 'window_close', dict(wc, street=ST.ic_flicker(tg - 0.1, n=2, gap=0.5)), cx=960, cy=600, scale=1.2,
       light=lambda t: dict(SH_PINK, rim_a=30) if abs(t - tg - 0.07) < 0.1 else SH_PINK, act=_A(lambda a, s: a.glimpse(tg, 0.16)),
       post_fn=lambda t: dict(fade=0.55) if abs(t - tg - 0.07) < 0.1 else {}, c=BZ(0.02), sfx=[(tg, 'stinger', -2, 0, None, dict(kind='glimpse'))])
    BU(T(83), 'shiver', 'street', 'window_close', wc, cx=960, cy=760, scale=2.4, light=dict(SH_PINK, rim_a=40),
       act=_A(lambda a, s: a.set(T(83), E(83) - 0.15, 0.04, sh_glim=1.0)), c=BZ(0.01, hit=[T(83) + 0.1]), hit=T(83) + 0.1)
    # 84 The song stops.  85 Right outside our house.  86 And that smile breathes no cloud at all.
    S(T(84), 'street', 'house', st=ST_A, ppl=[SH(lean=0.1)], c=Z(1.5, 0.01, 820, 560), music=[(WD(84, 'stops'), 'jingle_stop', 0.0)],
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
    S(W(95, 'kessler'), 'street', 'kessler', st=dict(ST_A, win=dict(his=0.0)), ppl=[SH(lean=0.12, act=_A(lk(T(95), 'kwindow')))], c=Z(1.15, 0.02))   # his dark window past the truck
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
    S(T(105), 'kitchen', 'wide', st=dict(KIT_A, sash=0.12, stool='window'), ppl=[adam('doorway', face='sill_out', expr='shock', act=_A(lk(T(105), 'sill_out')))],
      c=Z(1.2, 0.02, 760, 600), sfx=[(T(105) + 0.2, 'window_crack', -12, -0.3, 'inside')])
    S(T(106), 'kitchen', 'window', st=dict(KIT_A, sash=0.12, stool='window'), c=Z(1.4, 0.02, 960, 800))
    # 107-109 Lina on the couch holding the cone; tongue out; an inch away
    S(T(107), 'living', 'couch3q', st=LIV_CRACK, ppl=[lina('couch_right', kind='seat', expr='tempted',
                                                           act=_A(lambda a, s: a.reach_to(-9, 1, CONE_UP, dur=0.01, shape='grip'),
                                                                  lambda a, s: a.reach_to(-9, -1, (CONE_UP[0] - 14, CONE_UP[1] + 6), dur=0.01, shape='grip'),
                                                                  lk(T(107), (CONE_UP[0], CONE_UP[1] - 20))),
                                                           hands='lap', extras=[cone_fx('hand_r', 2.0)])], c=Z(1.7, 0.02, 1040, 700))
    BU(T(108), 'lina_pj', 'living', 'couch3q', LIV_CRACK, cx=960, cy=600, scale=0.95, light=LAMP, expr='thirsty', act=_A(lk(T(108), (960, 860))),
       on=[cone_fx('hand_r', 1.0)], hands=[dict(who='lina_pj', fn=lambda t: (1020, 980, 175.0, 1.0), size=170, shape='grip', side=-1, sleeve_from=(1200, 1400))],
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: _cone_screen(pen, 990, 860 - 30 * ease_in_out(clamp((t - sh.t0) / 0.6)), 150, t), 'cone')], c=BZ(0.03))
    BU(T(109), 'lina_pj', 'living', 'couch3q', LIV_CRACK, cx=960, cy=420, scale=1.5, light=LAMP, expr='thirsty',
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: _cone_screen(pen, 960, 780, 230, t), 'cone')], c=BZ(0.02))
    # 110 I slap it.  111 It hits the floor and shatters like glass.
    tsl = WD(110, 'slap')
    lift = lambda a, s: [a.reach_to(-9, 1, CONE_UP, t1=tsl + 0.05, dur=0.01, shape='grip'), a.reach_to(-9, -1, (CONE_UP[0] - 14, CONE_UP[1] + 6), t1=tsl + 0.05, dur=0.01, shape='grip')]
    S(T(110), 'living', 'couch3q', st=LIV_CRACK, ppl=[lina('couch_right', kind='seat', id='lina', expr='shock', act=_A(lift), extras=[cone_fx('hand_r', 2.0, t_gone=tsl + 0.08)]),
                                                       adam((3.0, 2.45, 0.0), face=(2.84, 1.68), id='adam', expr='shout',
                                                            act=_A(reach(tsl - 0.12, 1, ('lina', 'hand_r'), dur=0.18, shape='flat')))],
      c=Z(1.5, 0.02, 1050, 700), sfx=[(tsl + 0.06, 'slap', 0, 0, 'inside')])
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
    S(T(116), 'street', 'house', st=ST_A, ppl=[SH(lean=0.1)], c=Z(1.5, 0.0, 820, 560))
    S(W(116, 'out'), 'street', 'house', st=ST_DARK, ppl=[SH(lean=0.1)], cut='blink', c=Z(1.5, 0.0, 820, 560), sfx=[(WD(116, 'out'), 'power_cut', 0, 0, 'outside')])
    IN(T(117), 'phone', dict(time_='11:47', bars=0), c=dict(mv='push', rate=0.03), sfx=[(WD(117, 'bars'), 'phone_buzz', -10, 0, 'close')])
    # 118-120 the black TV: us; GLIMPSE 2: the skull in the crack; red eyes
    tsk = WD(119, 'skull') - 0.4
    S(T(118), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=0.0), c=Z(1.0, 0.02))
    S(T(119), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=lambda t: ease_in_out(clamp((t - tsk) / 0.6))), c=Z(1.1, 0.03))
    S(T(120), 'living', 'tv', st=dict(LIV_BLACK, cone='floor', skull=1.0), c=Z(2.6, 0.02, 960, 470, hit=[WD(120, 'red')]), hit=WD(120, 'red'))
    # 121 I spin around.
    S(T(121), 'living', 'couch', st=dict(LIV_BLACK, cone='floor'), ppl=[adam('couch_mid', kind='seat', expr='terror', act=_A(lk(T(121) + 0.05, 'curtain_crack', dur=0.18, body=0.9, snap=True))),
                                                                        lina('couch_right', kind='seat', expr='fear', act=_A(lk(T(121) + 0.3, 'curtain_crack', dur=0.3, body=0.5)))],
      c=Z(1.2, 0.02, 960, 680), cold=False, sfx=[(T(121) + 0.05, 'whoosh', -10, 0, None, dict(kind='soft'))])
    # 122-123 Just the smiling man. Waving.  (POV through the crack)
    S(T(122), 'street', 'gap', st=ST_DARK, ppl=[SH(lean=0.2, act=_A(lambda a, s: a.slow_wave(T(122), E(123) + 1, 1), lk(T(122), (960, 520))))], c=Z(1.3, 0.02, 975, 470))
    # 124 I yank the curtain shut.
    ty = T(124) + 0.15
    S(T(124), 'living', 'window', st=dict(LIV_BLACK, curtains=lambda t: 0.04 * (1 - ease_in_cubic(clamp((t - ty) / 0.18)))),
      ppl=[adam((3.3, 0.55, 0.0), face=(3.4, -1.0), act=_A(reach(ty - 0.1, 1, 'curtain_crack', t1=ty + 0.6, dur=0.12)))], c=Z(1.3, 0.02, 920, 600),
      sfx=[(ty, 'curtain_yank', 0, 0, 'inside')])


def _cone_screen(pen, x, y, k, t):
    """The cone drawn big in screen space (close-ups of Lina): the swirl up, steam rising."""
    y0 = y
    wafer = poly([(x - k * 0.55, y0), (x + k * 0.55, y0), (x, y0 + k * 1.7)])
    pen.fill(wafer, '#d9a86a'); pen.line(wafer, max(1.0, k * 0.03), '#1a1418')
    for j in range(4):
        pen.seg((x - k * 0.45 + j * k * 0.25, y0 + k * 0.1), (x - k * 0.05 + j * k * 0.12, y0 + k * 1.3), max(0.8, k * 0.02), '#a8743a')
    for j, (c_, r_) in enumerate((('#f4b4cf', 0.62), ('#ffffff', 0.5), ('#e58fb4', 0.38), ('#ffffff', 0.24))):
        pen.fill(oval(x, y0 - k * (0.2 + 0.32 * j), k * r_ * 1.05, k * r_ * 0.7), c_)
        pen.line(oval(x, y0 - k * (0.2 + 0.32 * j), k * r_ * 1.05, k * r_ * 0.7), max(1.0, k * 0.012), '#b0607f', 120)
    for j in range(3):
        u = ((t * 0.5 + j / 3.0) % 1.0)
        pen.fill(oval(x + k * 0.3 * math.sin(t * 2 + j), y0 - k * (1.3 + 1.4 * u), k * (0.2 + 0.3 * u)), '#eef6ff', 110 * (1 - u), blur=k * 0.12)


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
      cold=True, c=Z(1.6, 0.02, 950, 740))
    BU(T(134), 'lina', 'living', 'couch3q', LIV_FROST, cx=960, cy=600, scale=0.9, light=PINK_D, expr='stern', cold=True, act=_A(shake_head(WD(134, 'lina'), 2, dur=0.7)),
       acts=lambda A, sh, sp: [Layer(0.85, lambda pen, t: [_mitten_screen(pen, 760, 1000 - 20 * math.sin(t * 2), 70, -15), _mitten_screen(pen, 1160, 1000 - 20 * math.sin(t * 2 + 1), 70, 15)], 'mitts')],
       c=BZ(0.02))
    # 135 One blanket, both of us.
    S(T(135), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='brave'), lina('couch_right', who='lina', kind='seat', expr='sad', seed=2,
                                                                                                                   extras=[mitts()])],
      cold=True, acts=nest_blanket(), c=Z(1.5, 0.02, 1000, 720))
    # 136-138 The song comes back. Softer. A lullaby.
    S(T(136), 'street', 'house', st=ST_DARK, ppl=[SH(lean=0.12, act=_A(lambda a, s: a.slow_wave(T(136), E(136) + 1, 1)))], c=Z(1.6, 0.01, 820, 560),
      music=[(T(136), 'jingle', 0.3, round(E(139) - T(136) + 1, 2), dict(version='lullaby'))])
    S(T(137), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.6 + 0.4 * math.sin((t - T(137)) * 1.6)), c=Z(1.1, 0.02))
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
    IN(T(143), 'radio', lambda u: dict(talk=0.0, static=0.5 + 0.5 * abs(math.sin(u * 9))), c=dict(mv='push', rate=0.04), sfx=[(T(143), 'radio_squelch', -2, 0, 'close')])
    IN(T(144), 'radio', lambda u: dict(talk=0.7 + 0.3 * math.sin(u * 7), static=0.15), c=dict(mv='push', rate=0.02))
    BU(W(144, 'stay'), 'adam', 'hall', 'door', HALL_BLACK, cx=1000, cy=620, scale=0.92, light=PINK_D, expr='suspicious', cold=True,
       act=_A(radio(W(144, 'stay') - 0.5, E(144) + 0.5, 1), lk(W(144, 'stay'), (1100, 760))), c=BZ(0.02))
    IN(W(144, 'separate'), 'radio', lambda u: dict(talk=0.7 + 0.3 * math.sin(u * 7), static=0.15), motion=lambda u: (0.0, 0.0, 0.5 + 0.06 * u, 0.0), c=dict(mv='hold'))
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
    IN(T(150), 'radio', dict(talk=0.0, static=0.0), c=dict(mv='push', rate=0.01))
    IN(T(151), 'radio', lambda u: dict(talk=0.6 + 0.4 * math.sin(u * 6), static=0.1), c=dict(mv='push', rate=0.02))
    BU(W(151, 'close'), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sleepy', cold=True,
       act=_A(sleepyf(W(151, 'close'))), c=BZ(0.02))
    # 152-154 Pink light sweeps the curtain. A shadow. Long, jointed legs.  (GLIMPSE 3)
    S(T(152), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.4 + 0.6 * ease_in_out(clamp((t - T(152)) / 1.0))), c=Z(1.0, 0.02))
    tls = T(153)
    S(T(153), 'living', 'window', st=dict(LIV_FROST, pink=1.0), acts=lambda A, sh, sp: [leg_shadow(sp, tls, E(154) + 0.3)], c=Z(1.05, 0.02),
      sfx=[(tls + 0.2, 'scuttle', -10, 0, 'outside', dict(surface='roof'))])
    S(T(154), 'living', 'window', st=dict(LIV_FROST, pink=1.0), acts=lambda A, sh, sp: [leg_shadow(sp, tls, E(154) + 0.3)], c=Z(1.8, 0.02, 1000, 520, hit=[T(154) + 0.1]),
      hit=T(154) + 0.1)
    # 155 Then an orange light sweeps the street.
    S(T(155), 'street', 'plow', st=dict(truck=None, plow=dict(x=lambda t: -14.0 + 7.0 * clamp(t - T(155), 0.0, 6.0), y=-11.0, dir=1, beacon=1.0)), c=Z(1.0, 0.01),
      sfx=[(T(155), 'plow_pass', -2, 0, 'outside', dict(dur=3.0))])
    # 156 D "Adam? Passing our street. All good? Over."
    dadcab = lambda: dict(plain=('#2a1c14', '#0a0706'), light=lambda t: dict(BEACON, rim_a=int(70 + 80 * (0.5 + 0.5 * math.sin(t * 8.2)))))
    BU(T(156), 'dad', None, None, cx=960, cy=600, scale=0.85, turn=0.3, expr='kind_smile', act=_A(radio(T(156) - 0.5, E(156) + 0.3, 1)), c=BZ(0.015), **dadcab())
    BU(T(157), 'adam', 'living', 'window', LIV_FROST, cx=1000, cy=620, scale=0.92, light=PINK_D, expr='asking', cold=True, act=_A(radio(T(157) - 0.3, E(157) + 0.5, 1)), c=BZ(0.02))
    BU(T(158), 'dad', None, None, cx=960, cy=600, scale=0.9, turn=0.3, expr='suspicious', act=_A(radio(T(158) - 0.5, E(158) + 0.3, 1)), c=BZ(0.015), **dadcab())
    BU(W(158, 'hour'), 'adam', 'living', 'window', LIV_FROST, cx=980, cy=620, scale=1.0, light=PINK_D, expr='shock', cold=True,
       act=_A(radio(T(157), E(159) + 0.5, 1)), c=BZ(0.03))
    BU(T(159), 'adam', 'living', 'window', LIV_FROST, cx=960, cy=600, scale=1.1, light=PINK_D, expr='terrified_call', cold=True,
       act=_A(radio(T(157), E(159) + 0.5, 1)), c=BZ(0.03))
    # 160 Static.  161 Bells.
    IN(T(160), 'radio', lambda u: dict(talk=0.0, static=1.0), cut='static', c=dict(mv='push', rate=0.04), sfx=[(T(160), 'radio_static', 0, 0, 'close', dict(dur=1.0))])
    IN(T(161), 'radio', lambda u: dict(talk=0.5 + 0.5 * math.sin(u * 30), static=0.9), motion=lambda u: (0.0, 0.0, 0.4, 0.0), c=dict(mv='hold'),
       sfx=[(WD(161, 'bells'), 'radio_bells', -2, 0, 'close')], post_fn=lambda t: dict(mix=('ic_ext', 0.0)))
    BU(T(162), 'dad', None, None, cx=960, cy=600, scale=0.85, turn=0.3, expr='suspicious', act=_A(radio(T(162) - 0.5, E(162) + 0.3, 1)), c=BZ(0.015),
       post_fn=lambda t: dict(static=0.25 + 0.2 * abs(math.sin(t * 13))), **dadcab())
    # 163 The orange light fades.  164 The pink one doesn't.
    tb = T(163) - 0.4
    S(T(163), 'living', 'window', st=dict(LIV_FROST, pink=0.8, beacon=lambda t: 1.0 - clamp((t - tb) / 1.6)), c=Z(1.0, 0.01))
    S(T(164), 'living', 'window', st=dict(LIV_FROST, pink=lambda t: 0.9 + 0.1 * math.sin(t * 2)), c=Z(1.3, 0.02, 940, 520))


def _mitten_screen(pen, x, y, s, rot):
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    m = rrect(-s, -1.2 * s, 2 * s, 2.4 * s, s * 0.9)
    pen.fill(m, '#e87aa4'); pen.line(m, max(1.0, s * 0.06), '#1a1418')
    th = rrect(-1.45 * s, -0.4 * s, 0.7 * s, 1.0 * s, 0.35 * s)
    pen.fill(th, '#e87aa4'); pen.line(th, max(1.0, s * 0.06), '#1a1418')
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
       act=_A(ex('shock', WD(172, 'wake'), None, 0.15), lk(WD(172, 'wake') + 0.1, (1300, 700), dur=0.2)), c=BZ(0.02))
    S(T(173), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam', kind='seat', expr='fear',
                                                          act=_A(lk(T(173), 'couch_right', body=0.3), reach(T(173) + 0.2, -1, (2.84, 1.68, 0.5), dur=0.4, shape='flat')))],
      cold=True, acts=nest_blanket(('adam',), empty=1.0), c=Z(1.6, 0.02, 1000, 720))
    # 174 The front door is swinging open.
    S(T(174), 'hall', 'door', st=dict(HALL_BLACK, door=lambda t: 55.0 + 18.0 * math.sin((t - T(174)) * 1.7)), cold=True, c=Z(1.2, 0.02, 960, 600),
      sfx=[(T(174), 'door_creak', -4, 0, 'inside'), (T(174), 'wind_gust', -6, 0, 'outside')])
    # 175 In the snow, a mitten.  176 Then the other one.
    trk = [('child', [(-2.1, -0.6), (-2.1, -2.3), (-2.0, -4.5), (-1.2, -6.8), (-0.6, -7.7)])]
    S(T(175), 'street', 'door', st=dict(ST_DARK, porch=0.0, tracks=trk, props=[('mitten', -2.05, -1.6), ('mitten', -1.9, -3.0)], door_open=True), c=Z(1.6, 0.02, 973, 780))
    S(T(176), 'street', 'door', st=dict(ST_DARK, tracks=trk, props=[('mitten', -2.05, -1.6), ('mitten', -1.9, -3.0)], door_open=True), c=Z(1.5, 0.02, 1000, 920))   # down the walk: the second mitten nearer the street
    # 177 Lina is walking toward the pink window.
    MIT = [('mitten', -2.05, -1.6), ('mitten', -1.9, -3.0)]
    S(T(177), 'street', 'truck', st=dict(ST_DARK, tracks=trk, props=MIT),
      ppl=[lina((-1.9, -5.0, FOOT), who='lina', path=[(T(177) - 1.0, (-1.9, -5.0, FOOT)), (E(178) + 1.5, (-0.6, -7.6, FOOT))], surface='snow', expr='dazed',
                act=_A(hum(T(177), E(180)))),
           SH(lean=0.2, act=_A(lambda a, s: a.slow_wave(T(177), E(177) + 1.0, 1), lk(T(177), (900, 820))))], cold=True, c=Z(1.25, 0.02, 900, 560))
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
      cold=True, c=Z(1.3, 0.02, 900, 520))
    # 192 S "Who's the coldest? YOU are! Free for whoever's coldest!"
    BU(T(192), 'shiver', 'street', 'curb', STO, cx=960, cy=560, scale=1.0, light=SH_PINK, rot=-12,
       act=_A(pose(-9, None, 0.1, ws_bend=0.4), lambda a, s: a.slow_wave(T(192), E(192) + 1, 1), lk(T(192), (960, 700))), c=BZ(0.02))
    BU(W(192, 'you'), 'shiver', 'street', 'curb', STO, cx=960, cy=640, scale=1.5, light=SH_PINK, rot=-14,
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
    tyk = WD(195, 'yank')
    S(T(195), 'street', 'truck', st=STO,
      ppl=[SH(clip=None, nolegs=1.0, dorder=-3.0, act=_A(pose(-9, None, 0.1, ws_bend=1.3, ws_face_up=0.9),
                                              lambda a, s: a.reach_far(T(195) - 1, 1, (scr(s.sp, 'lina_window')[0] + 20, scr(s.sp, 'lina_window')[1] - 0.95 * spot_of(s.sp, 'lina_window').ppm),
                                                                       t1=tyk + 0.2, dur=0.5, z=30.0))),
           lina('lina_window', who='lina', id='lina', face=(0.27, -8.6), expr='dazed', light=PINK,
                act=_A(reach(T(195) - 1, 1, (0.15, -8.15, 1.0), t1=tyk, dur=0.4, shape='reach'), ex('fear', tyk + 0.1), lambda a, s: a._add(tyk, None, _pull(tyk, 220.0)))),
           kid('adam', (-1.6, -6.4, FOOT), id='adam', path=[(T(195) - 0.3, (-1.9, -6.0, FOOT)), (tyk, (-0.9, -7.45, FOOT)), (E(195) + 0.4, (-1.4, -6.9, FOOT))],
               run=True, surface='snow', expr='terrified_call', act=_A(reach(tyk - 0.1, -1, ('lina', 'chest'), t1=tyk + 0.3, dur=0.2)))],
      cold=True, c=Z(1.35, 0.01, 920, 560, hit=[tyk + 0.05]), sfx=[(tyk, 'cloth_grab', -2, 0, 'outside')])
    # 196 I step back.  (Adam, Lina in his arms; from here he carries her)
    S(T(196), 'street', 'truck', st=STO,
      ppl=[SH(lean=0.25, act=_A(lambda a, s: a.slow_wave(T(196), E(200) + 2, 1), lk(T(196), ('adam', 'head')))),
           kid('adam', (-1.15, -7.2, FOOT), id='adam', face=(0.27, -8.6), expr='terror', carry=dict(who='lina', t0=-9.0, expr='fear'),
               act=_A(lambda a, s: a._add(T(196) + 0.2, None, _step_back(T(196) + 0.2, 40.0))))],
      cold=True, c=Z(1.35, 0.01, 920, 560))
    # 197-198 My boot doesn't move. Frozen to the snow.
    IN(T(197), 'boot', dict(), c=dict(mv='push', rate=0.03), sfx=[(T(197) + 0.2, 'boot_stuck', -2, 0, 'close')])
    IN(T(198), 'boot', dict(), motion=lambda u: (0.0, 140.0, 0.55 + 0.05 * u, 0.0), c=dict(mv='hold'), sfx=[(T(198) + 0.1, 'frost_creep', -8, 0, 'close')])
    # 199-213 THE TRANSFORMATION (face), one transform() curve across every cut; he keeps waving throughout
    TFW = lambda: _A(tf, lambda a, s: a.slow_wave(T(199) - 2, E(223) + 2, 1))
    BU(T(199), 'shiver', 'street', 'window_close', STO, cx=960, cy=620, scale=1.0, light=SH_PINK, act=_A(TFW(), lk(T(199), (960, 620))), c=BZ(0.02))
    BU(T(201), 'shiver', 'street', 'window_close', STO, cx=960, cy=600, scale=1.25, light=SH_PINK, act=_A(TFW(), lk(T(201), (960, 620))), c=BZ(0.02),
       sfx=[(T(201) + 0.2, 'skin_stretch', -6, 0, 'outside')])
    BU(T(202), 'shiver', 'street', 'window_close', STO, cx=960, cy=560, scale=1.6, light=SH_PINK, act=_A(TFW(), lk(T(202), (960, 600))), c=BZ(0.02))
    BU(T(204), 'shiver', 'street', 'window_close', STO, cx=960, cy=640, scale=1.2, light=SH_PINK, act=_A(TFW(), lk(T(204), (960, 600))), c=BZ(0.03))
    BU(T(206), 'shiver', 'street', 'window_close', STO, cx=980, cy=560, scale=1.5, turn=0.2, light=SH_PINK, act=_A(TFW(), lk(T(206), (900, 600))), c=BZ(0.02),
       sfx=[(WD(206, 'hard'), 'bone_crack', -2, 0, 'outside')])
    BU(T(208), 'shiver', 'street', 'window_close', STO, cx=960, cy=820, scale=2.3, light=SH_PINK, act=_A(TFW(), lk(T(208), (960, 600))), c=BZ(0.015),
       hit=WD(208, 'red') + 0.05)
    BU(T(209), 'shiver', 'street', 'window_close', STO, cx=960, cy=520, scale=1.1, light=SH_PINK, act=_A(TFW(), lk(T(209), (960, 600))), c=BZ(0.02),
       sfx=[(WD(209, 'drops'), 'jaw_drop', 0, 0, 'outside')])
    BU(T(211), 'shiver', 'street', 'window_close', STO, cx=960, cy=360, scale=1.7, light=SH_PINK, act=_A(TFW(), lk(T(211), (960, 600))), c=BZ(0.02), face_fix=False)
    # 214-220 the uniform bulges, splits; legs punch out; click... they plant on the truck roof  (wide)
    trl = [WD(217, 'click'), WD(218, 'another'), WD(219, 'click'), WD(219, 'click', 1)]
    S(T(214), 'street', 'truck', st=STO, ppl=[SH(lean=0.18, act=_A(TFW(), lk(T(214), ('adam', 'head')))),
                                              kid('adam', (-1.3, -7.0, FOOT), id='adam', face=(0.27, -8.6), expr='terror', carry=dict(who='lina', t0=-9.0, expr='fear'))],
      cold=True, c=Z(1.25, 0.02, 920, 520), sfx=[(WD(215, 'splits'), 'uniform_tear', 0, 0, 'outside')])
    S(T(216), 'street', 'truck', st=STO, ppl=[SH(lean=0.18, clip='truck_window', act=_A(TFW(), lambda a, s: roof_legs(s.sp, trl)(a, s), lk(T(216), (960, 820))))],
      cold=True, c=Z(1.05, 0.02, 920, 480, hit=[WD(216, 'punches')]), hit=WD(216, 'punches'), sfx=[(WD(216, 'punches'), 'leg_punch', 2, 0, 'outside')])
    S(T(217), 'street', 'house', st=dict(ST_DARK, truck_open=1.0), ppl=[SH(lean=0.18, act=_A(TFW(), lambda a, s: roof_legs(s.sp, trl)(a, s)))],
      c=Z(2.2, 0.0, 820, 520))
    # 221-223 And the song keeps playing. Sweet. Cheerful.  (hold on the full monster in the warm pink window)
    S(T(221), 'street', 'curb', st=STO, ppl=[SH(lean=0.15, act=_A(TFW(), lambda a, s: roof_legs(s.sp, [T(221) - 3] * 4)(a, s), lk(T(221), (1000, 1000))))],
      c=Z(1.0, 0.02))
    # 224-226 He pours out of the window. Head first. Legs last.
    def pour(a, s):
        v_ = scr(s.sp, 'truck_vendor'); w_ = scr(s.sp, 'truck_window'); g_ = scr(s.sp, 'truck_curb')
        a.pour_out(T(224) + 0.1, E(226) - T(224), sill_dy=-(v_[1] - w_[1]) * 0.55, ground_dy=g_[1] - v_[1])
    S(T(224), 'street', 'truck', st=STO, ppl=[SH(clip=None, dorder=-3.0, act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0), pour))],
      cold=True, c=Z(1.0, 0.02), sfx=[(T(224) + 0.2, 'scuttle', -2, 0, 'outside', dict(surface='truck'))])
    # 227 I rip my foot out of the boot and run.  228 One sock.  229 Lina in my arms.
    S(T(227), 'street', 'truck', st=dict(STO, props=[('boot', -1.25, -7.15)]),
      ppl=[kid('adam_sock', (-1.25, -7.1, FOOT), id='adam', path=[(T(227) + 0.3, (-1.25, -7.1, FOOT)), (E(227) + 0.8, (-2.4, -4.2, FOOT))], run=True, surface='snow',
               expr='terrified_call', carry=dict(who='lina', t0=-9.0, expr='fear'))],
      cold=True, c=Z(1.2, 0.02, 940, 620), sfx=[(T(227) + 0.2, 'boot_rip', 0, 0, 'outside')])
    S(T(228), 'street', 'yard', st=dict(ST_DARK, props=[('boot', -1.25, -7.15)]),
      ppl=[kid('adam_sock', (-2.4, -4.4, FOOT), path=[(T(228) - 0.2, (-2.3, -4.6, FOOT)), (E(229) + 0.4, (0.6, -3.6, FOOT))], run=True, surface='snow', expr='terror',
               carry=dict(who='lina', t0=-9.0, expr='fear'))],
      cold=True, c=Z(2.0, 0.02, 520, 600))
    # 230-233 Legs stab the snow. One spears my coat. I tear free. Another pries at Lina.
    yc = cm((3.6, -9.0, 0.6), (1.4, -4.0, 0.2), 950)
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
    S(T(231), 'street', 'yard', st=dict(ST_DARK), cam=cm((1.2, -7.4, 0.5), (1.4, -3.6, 0.3), 1100),
      ppl=[adam_run(T(230) - 0.2, E(233) + 0.5, (0.0, -3.8, FOOT), (3.2, -3.0, FOOT)),
           P('shiver', (-2.4, -4.6, FOOT), light=SH_NIGHT, talk=False, breath=False, face=(3.0, -3.2),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.75), lambda a, s: a.scuttle(T(230) - 0.2, E(233) + 0.5, _line(s.sp, (-2.4, -4.6, FOOT), (1.4, -4.0, FOOT)), None),
                    lambda a, s: a.leg_to(WD(231, 'spears'), 2, lambda t: s.A['adam'].where(t, 'hip'), dur=0.18, hold=max(0.2, WD(232, 'tear') - WD(231, 'spears')), back=0.3, ev='leg_spear_coat'),
                    lambda a, s: a.leg_to(WD(233, 'pries'), 4, lambda t: s.A['adam'].where(t, 'chest'), dur=0.25, hold=0.6, back=0.4, ev='leg_pry')))],
      cold=True, c=Z(1.0, 0.02, hit=[WD(231, 'spears')]))
    # 234 He can't take her while I'm holding her.  235 So he wants me to let go.
    BU(T(234), 'adam_sock', 'street', 'yard', dict(ST_DARK), cx=900, cy=600, scale=0.9, light=dict(NIGHT, rim_a=110), expr='fierce_kind', cold=True,
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
      ppl=[P('shiver', 'fence2', light=SH_NIGHT, talk=False, breath=False, face=(6.0, -6.3), dorder=-0.5,
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.7), lambda a, s: scut(a, s, T(236), E(237) + 0.2, ['fence2', 'fence3', 'fence4', 'car_hood', 'car_roof'])))],
      c=Z(1.5, 0.02, 700, 540), sfx=[(T(236) + 0.2, 'scuttle', 0, -0.4, 'outside', dict(surface='fence', dur=1.6)), (WD(237, 'car') - 0.1, 'scuttle', 0, 0.3, 'outside', dict(surface='car'))])
    S(T(238), 'street', 'roof', st=dict(ST_DARK),
      ppl=[P('shiver', 'eave', light=SH_NIGHT, talk=False, breath=False, face=(-2.1, -0.3),
             act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_spread=0.7), lambda a, s: scut(a, s, T(238), E(238) + 0.3, ['eave', 'roof_edge_door'])))],
      c=Z(1.0, 0.02), sfx=[(T(238) + 0.1, 'scuttle', -2, 0, 'outside', dict(surface='roof', dur=1.2))])
    # 239-241 And drops. Right in front of our door. Jaw hanging.
    S(T(239), 'street', 'door', st=dict(ST_DARK, props=MIT),
      ppl=[P('shiver', 'drop', light=SH_NIGHT, talk=False, breath=False, face=(-2.1, -8.0), act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_lift=80.0),
                                                                                                   lambda a, s: a.drop_to(WD(239, 'drops') - 0.1, 0.4, from_dy=-650.0),
                                                                                                   lambda a, s: a.jaw_gape(WD(239, 'drops') + 0.6, E(241) + 1)))],
      c=Z(1.0, 0.02, hit=[WD(239, 'drops') + 0.3]), hit=WD(239, 'drops') + 0.3, sfx=[(WD(239, 'drops') + 0.3, 'leg_stab_snow', 2, 0, 'outside', dict(n=8))])
    BU(T(241), 'shiver', 'street', 'door', dict(ST_DARK), cx=960, cy=560, scale=1.1, light=SH_NIGHT,
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
    mx = (-2.05, -1.6, -0.15)

    def pluck(a, s):
        a.leg_to(T(243) + 0.3, 1, scr(s.sp, mx), dur=0.3, hold=0.2, back=None)
        a.leg_to(T(243) + 0.8, 1, (scr(s.sp, mx)[0] + 120, scr(s.sp, mx)[1] - 420), dur=0.8, hold=3.0, back=None, ev='leg_lift')
    S(T(243), 'street', 'door', st=dict(ST_DARK, props=[('mitten', -1.9, -3.0)]), cam=cm((-0.6, -4.6, 0.4), (-2.0, -1.4, 0.4), 1000),
      ppl=[P('shiver', 'drop', light=SH_NIGHT, talk=False, breath=False, face=(-2.05, -1.6), act=_A(lambda a, s: a.set(-9, None, 0.1, sh_m=1.0, sh_lift=60.0), pluck,
                                                                                                    lk(T(243), mx)),
             extras=[held_mitten('leg1', t0=T(243) + 0.6)])],
      c=Z(1.0, 0.02), sfx=[(T(243) + 0.6, 'leg_stab_snow', -4, 0, 'outside')])
    # 244-245 Onto his string. Saving her a place.
    IN(T(244), 'mittens', lambda u: dict(lina=u + T(244) >= WD(244, 'string') - 0.1), c=dict(mv='push', rate=0.02))
    IN(T(245), 'mittens', dict(lina=True), motion=lambda u: (-700 * ease_in_out(clamp(u / 0.8)), 0.0, 1.0 * ease_in_out(clamp(u / 0.8)), 0.0), c=dict(mv='hold'))
    # 246 I grab the radio.  247 "Dad!"  248 Static.  249 And bells.
    S(T(246), 'living', 'radio', st=dict(LIV_NEST), cold=True,
      acts=lambda A, sh, sp: [hand_layer('adam_sock', slide(sh.t0, sh.t0 + 0.25, (1700, 1200), (scr(sp, 'radio')[0] + 40, scr(sp, 'radio')[1] + 30), -120, -150,
                                                            extra=lambda t, r: (r[0] + 400 * ease_in_cubic(clamp((t - sh.t0 - 0.5) / 0.3)), r[1] + 300 * ease_in_cubic(clamp((t - sh.t0 - 0.5) / 0.3)), r[2], r[3])),
                                         260, 'grip', 1, sleeve_from=(1900, 1500))], c=Z(1.0, 0.02), sfx=[(T(246) + 0.25, 'radio_grab', -4, 0, 'close')])
    BU(T(247), 'adam_sock', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='shout', cold=True, act=_A(radio(T(247) - 0.4, E(249) + 0.5, 1)),
       c=BZ(0.03))
    IN(T(248), 'radio', dict(talk=0.0, static=1.0), cut='static', c=dict(mv='push', rate=0.03), sfx=[(T(248), 'radio_static', 0, 0, 'close', dict(dur=1.5))])
    IN(T(249), 'radio', lambda u: dict(talk=0.5 + 0.5 * math.sin(u * 30), static=0.9), motion=lambda u: (0.0, 0.0, 0.4, 0.0), c=dict(mv='hold'),
       sfx=[(WD(249, 'bells'), 'radio_bells', -2, 0, 'close')])
    # 250-252 Her fingertips are white. Waxy. I don't rub them.
    IN(T(250), 'fingers', dict(waxy=1.0), c=dict(mv='push', rate=0.03))
    IN(T(251), 'fingers', dict(waxy=1.0), motion=lambda u: (0.0, 60.0, 0.5 + 0.05 * u, 0.0), c=dict(mv='hold'))
    tr0 = T(252)
    IN(T(252), 'fingers', dict(waxy=1.0), c=dict(mv='push', rate=0.02),
       hands=[dict(who='adam_sock', fn=slide(tr0, tr0 + 0.5, (1500, 1300), (1250, 820), -130, -140, extra=lambda t, r: (r[0] + 160 * ease_in_out(clamp((t - tr0 - 0.75) / 0.4)), r[1] + 120 * ease_in_out(clamp((t - tr0 - 0.75) / 0.4)), r[2], r[3])),
                   size=280, shape='open', side=1, sleeve_from=(1800, 1500))])
    # 253 I tuck them under my arms.  254-255 Wet socks off. Dry ones on.  256 Blanket around her middle.
    S(T(253), 'living', 'couch3q', st=LIV_NEST, ppl=[adam('couch_mid', who='adam_sock', kind='seat', id='adam', expr='fierce_kind', face=(2.84, 1.68),
                                                          act=_A(lk(T(253), ('lina', 'head')), lambda a, s: a.hold_close(T(253) + 0.2, None, -1))),
                                                     lina('couch_right', who='lina', kind='seat', id='lina', expr='sad', seed=2, face=(3.4, 1.68),
                                                          act=_A(reach(T(253) + 0.1, 1, ('adam', 'chest'), dur=0.4), reach(T(253) + 0.1, -1, ('adam', 'chest'), dur=0.4)))],
      cold=True, c=Z(1.7, 0.02, 1000, 700))
    S(T(254), 'living', 'couch3q', st=LIV_NEST, ppl=[lina('couch_right', who='lina_pj', kind='seat', id='lina', expr='sad', seed=2),
                                                     adam((3.0, 2.35, 0.0), who='adam_sock', kind='kneel', id='adam', face=(2.84, 1.68), expr='focused',
                                                          act=_A(reach(T(254) + 0.1, 1, ('lina', 'foot_l'), t1=E(255), dur=0.35), lk(T(254), ('lina', 'foot_l'))))],
      cold=True, c=Z(1.8, 0.02, 1050, 800), sfx=[(T(254) + 0.4, 'sock_pull', -8, 0, 'inside'), (T(255) + 0.3, 'sock_pull', -8, 0, 'inside')])
    S(T(256), 'living', 'couch3q', st=LIV_NEST, ppl=[lina('couch_right', who='lina_pj', kind='seat', expr='sad', seed=2),
                                                     adam((3.0, 2.35, 0.0), who='adam_sock', kind='kneel', id='adam', face=(2.84, 1.68), expr='fierce_kind',
                                                          act=_A(reach(T(256) + 0.1, 1, (2.84, 1.8, 0.65), dur=0.45), reach(T(256) + 0.1, -1, (2.9, 1.55, 0.65), dur=0.45)))],
      cold=True, c=Z(1.6, 0.02, 1050, 760), sfx=[(T(256) + 0.3, 'blanket_wrap', -6, 0, 'inside')])
    # 257 Zipped inside my coat with me.  258-259 Then she shivers. Hard.  260-262 "Good," I whisper. "Shivering means you're fighting."
    two_shot = lambda t, lina_act=None, sc=0.85: BU(t, 'adam_sock', 'living', 'couch3q', LIV_NEST, cx=840, cy=560, scale=sc, turn=0.3, light=PINK_D, expr='fierce_kind',
                                                     cold=True, busts=[dict(who='lina', cx=1120, cy=700, scale=sc * 0.8, turn=-0.3, expr='sad', light=PINK_D, act=lina_act)],
                                                     act=_A(lk(t, (1120, 640))), c=BZ(0.015))
    two_shot(T(257), sc=0.85)
    BU(T(258), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=600, scale=1.0, light=PINK_D, expr='sad', cold=True, act=_A(tremblef(WD(258, 'shivers'), None, 1.0)), c=BZ(0.02))
    BU(T(259), 'lina', 'living', 'couch3q', LIV_NEST, cx=960, cy=560, scale=1.35, light=PINK_D, expr='cry_shut', cold=True, act=_A(tremblef(T(259) - 1, None, 1.8)), c=BZ(0.02))
    two_shot(T(260), lina_act=_A(tremblef(T(258), None, 1.4)), sc=0.95)


def _pull(t0, dx):
    """Lina yanked out of his reach into Adam's arms: her body slides toward Adam."""
    def fn(P_, t):
        u = ease_in_out(clamp((t - t0) / 0.3)); P_.dx -= dx * u
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

