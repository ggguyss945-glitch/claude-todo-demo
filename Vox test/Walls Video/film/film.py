"""film.py: the shot list, editor and cue sheets for "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH"
(Night Policy).

Built in the machinery of the Ice Cream film (film_ice_ref.py: the Film class, plan(), the shot builders, BUILDERS,
captions, header, cue sheets) on this film's cast (characters.py + characters_walls.py) and sets (sets.py + sets_walls.py:
14 Larkspur Lane on one plan in metres). EVERY time in the plan is keyed to timeline.json (line starts / ends and word
times): there is no absolute time anywhere, so a re-edit of the narration moves the picture with its lines.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + TAIL)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --still T,T

THE OWNER'S NOTES, MADE INTO CODE:
  * Every figure in a set shot stands on a plan point of the set (an anchor or (x, y, Y)): height from the px-per-metre
    there, draw order from sp.order_at(), light from sp.light_kw(); seats / lying from the anchor's kind. Inside the
    walls (kind 'wall') the figure stands on the cavity's bottom plate (WALL_FLOOR); tools/validate.py checks both.
  * Prefer cuts; the camera only pushes a little while people act.
  * MR. PELL is ACTIVE in every beat: he watches through the crack, the vent and the closet crack, crawls fast inside the
    walls, turns the deadbolt, eats our food, takes the drawings, tucks Theo in, kneels, tilts his head, shushes, slides
    the closet's back wall, scratches round the bedroom and sings through the vent. He never hurts anyone.
  * Continuity: Dad wears the red flannel ('dad') only on moving day (L12-L27); after that 'dad_tee' / 'dad_pj', and
    the flannel is on Pell. Sam ('sam_pj') and Theo (pyjamas) at night. Pell's face beats in 3/4. Lying figures only in
    close / medium shots. The doorway figure is Pell's silhouette with Dad's tilt (WALLS_TILT), the same each time.
  * Lip sync on character lines only (VOICE: the timeline's `who`); the narrator (the grown-up Sam) is never drawn and
    moves no mouth. Captions come out clean (no markup).

Shot kinds (builders B_<kind>):
  set   a set view (sets_walls wl_* builders) with figures on the plan: room 'street' | 'living' | 'kitchen' | 'hall' |
        'boys' | 'parents' | 'dead'; view = the builder's view; set = builder kwargs; ppl = [P(who, at, ...)]; acts
  bust  a face close-up over the blurred set (bg=(room, view) + set=dict(..)); rot=90 for a face on a pillow
  ins   a prop insert: sets_walls wl_insert(name, kw, motion); kw = dict or f(time since the cut); hands=[..]; layers
  wall  inside the walls: a cutaway of the cavity (mode 'wall' | 'attic' | 'chase'), figures on its plate (ppl=[W_(..)])
  prop  a drawn prop close-up (Dad's hound mask, the GONE FOREVER box)
  rule  Theo's dinosaur notebook: rule n written large, its words appearing as they are read (7: the blank line)
  pause the comment prompt (stage 'ask' L54-L60 | 'return' L296-L304)
  list  the outro checklist (L285-L295), every item legible while it is read
  card  plain text cards (the outro: none of this happened, subscribe, the end)
  black black
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
FPS = 60
LEAD = 0.10                      # cut a moment before the word
TAIL = 4.0                       # the end card holds after the last line
TITLE = "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH"
BASE = 'If_Your_Little_Brother_Says_Someone_Lives_In_The_Walls'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card
PART_B = 186                       # tools/validate.py --part: A = lines 0..185 (.. rule six), B = 186..
def set_retime(lines, duration): return None


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (the timeline's `who`, fx or None). The narrator ('narrator', the grown-up Sam) is never
# drawn. Pell speaks from the ceiling, the wall, the mask, the vent and outdoors: his lips move on all of them.
VOICE = {'sam': [('sam', None)], 'sam_pj': [('sam', None)], 'theo': [('theo', None)], 'mom': [('mom', None)], 'mom_pj': [('mom', None)],
         'dad': [('dad', None)], 'dad_tee': [('dad', None)], 'dad_pj': [('dad', None)], 'pell': [('pell', None)],
         'pell_bare': [('pell', None)], 'dabrowski': [('dabrowski', None)], 'reyes': [('officer', None)], 'officer_w': []}
KIDS = ('sam', 'sam_pj', 'theo')
# ---------------------------------------------------------------- the header corner (place / time), keyed to lines
CORNER = [(0, '3:00 AM'), (4, '14 LARKSPUR LANE'), (11, 'THE MORNING AFTER'), (12, 'AUGUST'), (28, 'NIGHT ONE   3:00 AM'), (36, 'MORNING'),
          (38, 'THE NEXT NIGHT'), (54, '14 LARKSPUR LANE'), (65, 'EVERY NIGHT'), (70, 'EVERY MORNING'), (74, 'NIGHT FIVE   2:00 AM'),
          (88, 'AUGUST'), (99, 'THAT NIGHT'), (111, 'MORNING'), (116, 'EVERY MORNING'), (130, 'AT NIGHT'), (135, '14 LARKSPUR LANE'),
          (136, 'SATURDAY'), (143, '2:00 AM'), (156, '14 LARKSPUR LANE'), (166, 'THAT NIGHT'), (186, '3:00 AM'), (242, '3:09 AM'),
          (262, 'THE NEXT MORNING'), (269, "THEO'S RULES"), (276, CHANNEL)]


def clock_str(t):
    F = _FILM[0]
    lab = ''
    for i, s in CORNER:
        if i < len(F.L) and t >= F.t(i) - LEAD: lab = s
    return lab


def header(cv, right, corner, alpha=255):
    """The police header with this film's left label."""
    left = "THEO'S RULES"
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
    if q.get('hush'):                                   # Sam carries Theo, his hand over Theo's mouth (characters_walls)
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
    sp = ST.wl_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
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


def wavef(t0, t1, side=1, slow=True): return lambda a, s: a.wave(t0, t1, side, slow=slow)


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




# ==================================================================================================== this film: rooms, light, arcs
ROOMS = {'street': 'wl_street', 'living': 'wl_living', 'kitchen': 'wl_kitchen', 'hall': 'wl_hall', 'boys': 'wl_boys', 'parents': 'wl_parents',
         'dead': 'wl_dead'}
_PRE = {'street': 'wl_ext_', 'living': 'wl_liv_', 'kitchen': 'wl_kit_', 'hall': 'wl_hall_', 'boys': 'wl_boys_', 'parents': 'wl_par_', 'dead': 'wl_dead_'}
ROOM_RIM = {'street': NIGHT, 'living': NIGHT, 'kitchen': NL, 'hall': NL, 'boys': NIGHT, 'parents': NIGHT, 'dead': PHONE}
ALIAS = {'sam': ('sam', 'sam_pj'), 'mom': ('mom', 'mom_pj'), 'dad': ('dad', 'dad_tee', 'dad_pj'), 'pell': ('pell', 'pell_bare')}
SPACE = {'street': 'outside', 'living': 'inside', 'kitchen': 'inside', 'hall': 'inside', 'boys': 'inside', 'parents': 'inside', 'dead': 'wall'}
DAYK = ('day', 'morning')


def shot_space(s):
    if s.kind in ('rule', 'black', 'card', 'list'): return None
    if s.kind in ('pause', 'ins', 'prop'): return 'close'
    if s.kind == 'wall': return 'wall'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return {'street': 'outside'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('memory', 'outro', 'morning'): return s.p['era']
    if s.kind in ('rule', 'card', 'black', 'pause', 'list'): return s.kind
    if s.kind == 'wall': return 'wall'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    return 'outside' if room == 'street' else 'house'


# The kids' tension arc (no "scared jiggle": wider eyes, raised brows, faster breath), keyed to lines.
KID_ARC = [(0, 0.5), (4, 0.0), (28, 0.5), (36, 0.0), (74, 0.5), (84, 0.1), (99, 0.6), (111, 0.2), (143, 0.6), (155, 0.2), (166, 0.6),
           (183, 0.3), (186, 0.8), (226, 1.0), (242, 0.6), (254, 0.2), (262, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    pts = [(F.t(i), v) for i, v in arc if i < len(F.L)]
    return float(np.interp(t, [p_[0] for p_ in pts], [p_[1] for p_ in pts]))


def escalate(a, sh, who):
    if sh.kind in ('rule', 'card', 'black', 'pause', 'list') or sh.p.get('era') in ('memory', 'outro', 'morning'): return
    if who in KIDS:
        k = _arc(KID_ARC, sh.t0)
        if k <= 0.02: return

        def fn(P_, t, k=k):
            P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
            per = 3.9 - 1.5 * k
            P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)


def _c_on(sh, sp, c, A):
    """A camera dict whose centre is an anchor / plan point (on='theo_bed') or an actor (on='@pell', part='head') at the
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


def _header_text(self, t):
    cur = 'INTRODUCTION'
    for t0, n in self.rules:
        if t >= t0: cur = 'RULE %d OF 7' % n
    for i, s in ((285, 'THE REAL LIST'), (296, 'YOUR WORD'), (305, CHANNEL)):
        if i < len(self.L) and t >= self.t(i) - LEAD: cur = s
    return cur


def _clean(s):
    """Caption text comes out clean: no markup characters ever reach the screen."""
    import re
    return re.sub(r'[\*_\[\]\{\}<>#`~|]', '', s).replace('  ', ' ').strip()


def _overlay(self, cv, t, sh):
    if sh.kind == 'black' and not sh.p.get('caption'): return
    if sh.kind != 'black': header(cv, self.header_text(t), clock_str(t))
    if sh.kind in ('rule', 'list') or sh.p.get('no_caption'): return
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


Film.header_text = _header_text
Film.overlay = _overlay


# ==================================================================================================== inside the walls
WALL_FLOOR = {'wall': 930.0, 'attic': 900.0, 'chase': 930.0}       # the cavity's plate top (design y): feet / knees on it


def _food(pen, kind, x, y, s=1.0, ang=0.0):
    """What he eats, in his hand (drawn at the hand every frame: never left behind)."""
    cv = pen.cv; cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s, s)
    if kind == 'bread':
        pen.fill(rrect(-34, -40, 68, 62, 18), '#e0b070'); pen.fill(rrect(-27, -33, 54, 50, 14), '#f6e6c0'); pen.line(rrect(-34, -40, 68, 62, 18), 2.4, '#6a4a2a')
    elif kind == 'yogurt':
        pen.fill(poly([(-26, -46), (26, -46), (20, 22), (-20, 22)]), '#f4f2ec'); pen.fill(rect(-26, -50, 52, 8), '#c8d0d8')
        pen.fill(rect(-22, -30, 44, 18), '#e86a8a'); pen.line(poly([(-26, -46), (26, -46), (20, 22), (-20, 22)]), 2.4, '#5a5a60')
    elif kind == 'cereal':
        pen.fill(rect(-36, -86, 72, 104), '#a8582a'); pen.fill(rect(-28, -74, 56, 30), '#f2c040'); pen.fill(oval(0, -10, 18, 14), '#5a2e18')
        pen.line(rect(-36, -86, 72, 104), 2.4, '#3a1e10')
    elif kind == 'chicken':
        pen.fill(oval(0, -16, 44, 32), '#c8823a'); pen.fill(rrect(-6, 8, 12, 34, 6), '#f0e6d0'); pen.fill(oval(0, 44, 11, 9), '#f0e6d0')
        pen.line(oval(0, -16, 44, 32), 2.4, '#6a3a18')
    cv.restore()


def _cavity_bg(pen, mode, seed=0):
    """The inside of the wall: the back of the next room's lath with plaster keys squeezed through, the studs, the plates,
    an old pipe and a cable; for the attic the joists and the hatch's glowing outline; for the chase a low crawl space."""
    fl = WALL_FLOOR[mode]
    pen.fill(rect(-400, -300, 2720, 1680), '#140e0a')
    if mode in ('wall', 'chase'):
        top = 120.0 if mode == 'wall' else 430.0
        for k in range(int((fl - top) / 44) + 2):                                     # the lath
            y = top + k * 44
            c = ['#3e2c1f', '#46321f', '#3a2919'][(k + seed) % 3]
            pen.fill(rect(-400, y, 2720, 32), c)
            for j in range(26):
                x = -380 + ((j * 211 + k * 97 + seed * 31) % 2700)
                pen.fill(oval(x, y + 36, 26 + (j * 7) % 20, 9), '#6e6457', 210)        # plaster keys between the strips
        pen.texture(rect(-400, top, 2720, fl - top), 'wood', 0.35, 'overlay', 1.0, 90)
        for x in range(-260 + (seed * 70) % 300, 2300, 470):                           # studs (against the back)
            pen.fill(rect(x, top - 40, 64, fl - top + 60), '#5a4230')
            pen.fill(rect(x + 50, top - 40, 14, fl - top + 60), '#2e2016', 200)
            pen.texture(rect(x, top - 40, 64, fl - top + 60), 'wood', 0.5, 'overlay', 1.0, 0)
        pen.fill(rect(-400, top - 70, 2720, 60), '#4e3a2a')                             # top plate / the floor above
        pen.fill(rect(-400, 340 if mode == 'wall' else top + 40, 2720, 16), '#6a6a70', 200)   # an old pipe
        pen.line(smooth([(-400, 600), (500, 640), (1200, 610), (2320, 660)], False), 5, '#1a1a1a', 220)   # a cable
    else:                                                                              # the attic over the hall
        pen.linear(rect(-400, -300, 2720, 1680), 0, 0, 0, 1080, ['#1e1610', '#0c0806'])
        for k in range(7):                                                             # rafters
            x = -300 + k * 420
            pen.fill(poly([(x, -300), (x + 70, -300), (x + 520, fl - 40), (x + 450, fl - 40)]), '#3a2a1c')
        pen.fill(rect(-400, 360, 2720, 50), '#35261a', 230)
    pen.fill(rect(-400, fl, 2720, 70), '#6a5038')                                       # the bottom plate / joist tops
    pen.fill(rect(-400, fl, 2720, 8), '#8a6a4a')
    pen.fill(rect(-400, fl + 70, 2720, 900), '#0a0705')
    pen.texture(rect(-400, fl, 2720, 70), 'wood', 0.5, 'overlay', 1.0, 0)
    pen.radial(None, 960, 560, 1300, [(0.4, '#000000', 0), (1.0, '#000000', 170)])


def _slits(pen, t, slits, mode):
    """Light through cracks in the room-side plaster: thin warm lines and the soft beams they throw across him."""
    for (x, y0, y1, a) in slits:
        fl = 0.85 + 0.15 * math.sin(t * 1.7 + x)
        pen.line(poly([(x, y0), (x + 10, (y0 + y1) / 2), (x - 6, y1)], False), 3.2, '#ffe2a8', 230 * a * fl)
        pen.fill(poly([(x - 4, y0), (x + 8, y0), (x + 320, y1 + 240), (x - 240, y1 + 240)]), '#ffd890', 22 * a * fl, blur=30)
    for j in range(24):                                                                  # dust in the beams
        u = (t * 0.03 + j * 0.137) % 1.0
        x = (j * 331) % 1920; y = 1050 - u * 1000
        pen.fill(oval(x + 30 * math.sin(t * 0.5 + j), y, 2.4, 2.4), '#e8d8b8', 60 * math.sin(math.pi * u))


def _hole_frame(pen, seed=0):
    """The ragged edge of broken plaster round the frame: we look into the wall through a hole."""
    rng = np.random.RandomState(seed + 7)
    pts = []
    for k in range(64):
        a_ = 2 * math.pi * k / 64
        r = 1.0 + 0.04 * rng.randn()
        pts.append((960 + 1130 * r * math.cos(a_), 540 + 700 * r * math.sin(a_)))
    hole = smooth(pts, True)
    out = rect(-600, -500, 3120, 2080)
    edge = skia.Op(out, hole, skia.PathOp.kDifference_PathOp) or out
    pen.fill(edge, '#cfc6b6'); pen.texture(edge, 'grunge', 0.4, 'overlay', 1.0)
    pen.line(hole, 10, '#5a5248', 230); pen.line(hole, 3, '#efe8dc', 160)
    pen.fill(edge, '#000000', 110)


def WP(who='pell', x=960.0, h=None, **k):
    """A figure inside the walls: x (design px) on the cavity plate, height h (px; default from the mode), act, expr,
    turn / h_turn, food=(kind, side, t0, t1), light."""
    return dict(who=who, x=x, h=h, **k)


def B_wall(F, sh):
    p = sh.p
    mode = p.get('mode', 'wall')
    fl = WALL_FLOOR[mode]
    seed = p.get('seed', sh.idx % 5)
    layers = [Layer(1.6, lambda pen, t, m=mode, s=seed: _cavity_bg(pen, m, s), 'cavity', cache='film:cavity:%s:%d' % (mode, seed),
                    bounds=(-400, -300, 2320, 1380), blur=0)]
    A = ADict(); sh.A = A; sh._ground = []
    for k, q in enumerate(p.get('ppl', [])):
        who = q['who']
        hh = q.get('h') or {'wall': 800.0, 'attic': 700.0, 'chase': 760.0}[mode]
        a = CH.Acting(who, seed=q.get('seed', 0) + k * 11 + sh.idx * 3, height=hh, expr=q.get('expr', 'neutral'), blink=q.get('blink'))
        a.place(q['x'], fl + q.get('dy', 0.0))
        if q.get('turn') is not None: a.face(q['turn'], q.get('h_turn', 0.0))
        A[q.get('id', who)] = a
        if q.get('act'): q['act'](a, sh)
        if q.get('talk', True):
            for l in F.voice_lines(sh.t0, sh.t1, VOICE.get(who, [])):
                a.talk([(l['t'], l['end'], l['en'])], intensity=q.get('talk_k', 0.8))
        sh.actors.append(a)
        sh._ground.append((a, fl, q.get('ground', 'feet')))           # (validate: contacts on the plate, not on fl + dy)
        m = _Memo(a); lt = q.get('light', SLIT); food = q.get('food')

        def draw(pen, t, a=a, m=m, lt=lt, food=food, who=who):
            P_ = m(t)
            CH.draw(pen, who, a.x0, a.y0, a.height, P_, light=lt(t) if callable(lt) else lt, t=t)
            if food and food[2] <= t < (food[3] if len(food) > 3 and food[3] is not None else 1e9):
                hx, hy = a.where(t, 'hand_r' if food[1] < 0 else 'hand_l')
                _food(pen, food[0], hx, hy - 0.03 * a.height, a.height / 800.0, -10.0 * food[1])
        layers.append(Layer(1.0, draw, 'w_%s' % who, blur=0))
    if p.get('acts'): layers += [l for l in (p['acts'](A, sh, None) or []) if l is not None]
    slits = p.get('slits', [(520, 200, 700, 1.0), (1500, 260, 820, 0.8)] if mode != 'attic' else [])
    hatch = p.get('hatch')                                    # the attic: the hatch's outline glowing below him (f(t) or level)

    def fx_draw(pen, t):
        _slits(pen, t, slits, mode)
        if mode == 'attic' and hatch is not None:
            lv_ = lvl(hatch, t)
            if lv_ > 0.01:
                q_ = poly([(560, fl + 6), (1360, fl + 6), (1440, fl + 60), (480, fl + 60)])
                pen.line(q_, 7, '#ffd870', 240 * lv_); pen.glow(960, fl + 30, 520, '#ffcf60', 60 * lv_)
        for fn in p.get('fx_draw', []): fn(pen, t)
    layers.append(Layer(0.98, fx_draw, 'slits', blur=0))
    if p.get('frame', True):
        layers.append(Layer(0.55, lambda pen, t, s=seed: _hole_frame(pen, s), 'hole_frame', blur=0, screen=True))   # fixed in the frame
    c = dict(p.get('c') or dict(mv='push', rate=0.012))
    c.setdefault('free', True)
    if c.get('on') is not None:
        c = _c_on(sh, None, c, A)
    cam = scam(sh, None, c)
    return Spec(layers, cam, None, p.get('grade', 'neutral'), 1.0, 0.0, fx=lambda t: dict(p.get('post', {}), exposure=0.12), hud=p.get('hud'))


# ==================================================================================================== his eye at a crack / vent / door
def eye_layer(F, sh, x, y, k, t_in, t_out=None, clip=None, blinks_=(), part='eye_l', talk=False, light=None, yaw=0.3, lean=60.0,
              name='eye', depth=0.95, dark='#050403'):
    """HIS eye (the mask's heavy lid, his own eye blinking in the hole) leaning into a gap: x, y design px of the part,
    k px per head unit, clip = rect (x, y, w, h) | polygon points (the gap), lean = how far it slides in."""
    a = CH.Acting('pell', seed=sh.idx * 5 + 1, height=600.0)
    a.set(sh.t0 - 3, None, 0.1, h_turn=yaw)
    for tb in blinks_: a.blink(tb, 0.16)
    if talk:
        for l in F.voice_lines(sh.t0, sh.t1, VOICE['pell']):
            a.talk([(l['t'], l['end'], l['en'])], intensity=0.8)
    sh.actors.append(a)
    m = _Memo(a)

    def draw(pen, t):
        if t < t_in or (t_out is not None and t > t_out + 0.6): return
        u = ease_out_cubic(clamp((t - t_in) / 0.7))
        if t_out is not None: u *= 1.0 - ease_in_cubic(clamp((t - t_out) / 0.35))
        cv = pen.cv; cv.save()
        if clip is not None:
            pth = clip if isinstance(clip, skia.Path) else (rect(*clip) if len(clip) == 4 and not isinstance(clip[0], (tuple, list)) else poly(clip))
            cv.clipPath(pth, skia.ClipOp.kIntersect, True)
            pen.fill(pth, dark)
        CH.draw_head_at(pen, 'pell', m(t), x + lean * (1 - u), y, k, part, t=t, light=light or SLIT, yaw=None)
        cv.restore()
    return Layer(depth, draw, name, blur=0)


# ==================================================================================================== drawn props (the mask, the box)
def _gone_box(pen, x, y, s=1.0, lid=0.0, tape=1.0, cut=0.0, night=False, empty=False, mask=False, write=1.0):
    """The box Dad taped the mask into: GONE FOREVER in marker on the lid's front edge; lid 0 shut .. 1 open; cut 0..1 the
    tape slit; empty / mask inside."""
    cv = pen.cv; cv.save(); cv.translate(x, y); cv.scale(s, s)
    c1, c2, c3 = ('#c89a62', '#a87c48', '#e0b87e') if not night else ('#7a6a58', '#5a4c3e', '#8a7a66')
    pen.fill(oval(0, 250, 430, 40), '#000000', 120, blur=20)
    front = rect(-380, -40, 760, 290); side = poly([(380, -40), (470, -110), (470, 190), (380, 250)])
    pen.fill(front, c1); pen.fill(side, c2); pen.texture(front, 'paper', 0.5, 'multiply', 1.0)
    pen.line(front, 3, '#4a3420'); pen.line(side, 3, '#4a3420')
    if lid < 0.05:
        top = poly([(-380, -40), (380, -40), (470, -110), (-290, -110)])
        pen.fill(top, c3); pen.line(top, 3, '#4a3420')
        if tape > 0:
            pen.fill(poly([(-40, -40), (40, -40), (85, -110), (5, -110)]), '#d8d0b8', 200 * tape)
            pen.fill(rect(-40, -40, 80, 150), '#d8d0b8', 200 * tape)
            if cut > 0: pen.line(poly([(0, -40), (45 * cut, -110 * cut)], False), 3, '#2a2018', 230)
    else:
        pen.fill(poly([(-290, -110), (470, -110), (380, -40), (-380, -40)]), '#2a1e14')          # the open mouth of the box
        if mask and not empty:
            CH.draw_prop3(pen, 'hound_mask', 40, -150, 4.0)
        fl_ = poly([(-380, -40), (380, -40), (330, -40 - 300 * lid), (-430, -40 - 300 * lid)])
        pen.fill(fl_, c3); pen.line(fl_, 3, '#4a3420')
        pen.fill(rect(-40, -40, 80, 150), '#d8d0b8', 160)
        pen.line(poly([(0, -40), (0, 110)], False), 3, '#2a2018', 200)                        # the slit tape
    if write > 0:
        txt = 'GONE FOREVER'; n = int(math.ceil(len(txt) * clamp(write)))
        text(cv, txt[:n], -330, 120, 900, 92, '#141414', 235, 0.02, 'left')
    cv.restore()


SHELF_Y = 780.0                       # the garage shelf's top edge (design y): what stands on it stands HERE
BOX_BASE = 250.0                      # _gone_box: its bottom edge below its anchor, per unit of scale


def crack_poly(w=1.0, x=960.0, y0=300.0, y1=780.0):
    """The crack's opening (design px): a jagged slit about 34 * w px wide."""
    L, Rr = [], []
    for k in range(9):
        y = y0 + (y1 - y0) * k / 8.0
        cx = x + 26.0 * math.sin(k * 1.7) + (10.0 if k % 2 else -8.0)
        hw = (6.0 + 17.0 * math.sin(math.pi * k / 8.0)) * w
        L.append((cx - hw, y)); Rr.append((cx + hw, y))
    return L + Rr[::-1]


def vent_gaps(jx=0.0):
    """The parents' vent grille (wl_insert 'vent'): the dark gaps between its louvres, as one clip path."""
    pth = skia.Path()
    pth.addRect(skia.Rect.MakeXYWH(960 + jx - 560, 355, 20, 410))
    for k in range(15):
        pth.addRect(skia.Rect.MakeXYWH(960 + jx - 500 + 72 * k, 355, 32, 410))
    return pth


def _gap_bg(pen, what, w=1.0):
    """A close-up of a gap he looks through: 'crack' (the pantry plaster behind the cereal) | 'doorgap' (the hall closet
    door open just a crack: its edge, the frame and the dark between)."""
    if what == 'crack':
        pen.fill(rect(-600, -500, 3120, 2080), '#cfc8ba'); pen.texture(rect(-600, -500, 3120, 2080), 'grunge', 0.5, 'overlay', 1.0)
        q = poly(crack_poly(w))
        pen.fill(q, '#000000', 60, blur=14); pen.line(q, 3, '#6a6256', 200)
        for k in range(6):
            a_ = k * 1.1
            pen.line(poly([(960 + 40 * math.cos(a_), 540 + 220 * math.sin(a_)), (960 + 150 * math.cos(a_), 540 + 300 * math.sin(a_))], False), 2, '#8a8276', 160)
    else:
        pen.fill(rect(-600, -500, 3120, 2080), '#3a3e4c')
        pen.fill(rect(560, -500, 380, 2080), '#c8c4b8'); pen.fill(rect(990, -500, 800, 2080), '#b8b4a8')   # the frame | the door's edge
        pen.texture(rect(-600, -500, 3120, 2080), 'wood', 0.3, 'overlay', 1.0, 90)
        pen.fill(rect(940, -500, 50 * w, 2080), '#050505')
        pen.fill(rect(-600, -500, 3120, 2080), '#0a1020', 120)


def B_prop(F, sh):
    """A drawn prop close-up: p draw = f(pen, t) | 'mask' | 'box' (+ box=dict), bg colours, hands, shelf."""
    p = sh.p
    c1, c2 = p.get('bg', ('#3a3430', '#141110'))
    t0 = sh.t0

    def bg(pen, t):
        pen.linear(rect(-600, -500, 3120, 2080), 0, -200, 0, 1300, [c1, c2])
        pen.texture(rect(-600, -500, 3120, 2080), 'grunge', 0.35, 'overlay', 1.0)
        if p.get('shelf', True):
            pen.fill(rect(-600, SHELF_Y - 20, 3120, 20), '#7a5e42'); pen.fill(rect(-600, SHELF_Y, 3120, 46), '#6a5038')
            pen.fill(rect(-600, SHELF_Y + 46, 3120, 30), '#2a1e14')
    what = p.get('draw', 'box')

    def body(pen, t):
        if what == 'mask':                                   # hung by its crown on a nail in the garage wall
            sw = 2.0 * math.sin((t - t0) * 1.3)
            ny = p.get('y', 300)
            pen.fill(oval(960, ny - 4, 9, 9), '#2a2622'); pen.line(poly([(960, ny - 4), (960, ny + 22)], False), 3, '#3a3026')
            CH.draw_prop3(pen, 'hound_mask', 960, ny + 22, p.get('k', 13.0), angle=sw, t=t)
        elif what == 'box':
            kw = {k_: (v_(t - t0) if callable(v_) else v_) for k_, v_ in (p.get('box') or {}).items()}
            k_ = p.get('k', 1.1)
            _gone_box(pen, 960, (SHELF_Y if p.get('shelf', True) else 860.0) - BOX_BASE * k_, k_, **kw)
        elif what in ('crack', 'doorgap'):
            _gap_bg(pen, what, p.get('open', 1.0))
        else:
            what(pen, t)
    layers = [Layer(3.0, bg, 'prop_bg', blur=0), Layer(1.0, body, 'prop', blur=0)]
    if what == 'box':                                    # (name, its base, the line it stands on) for tools/validate.py
        k_ = p.get('k', 1.1); gy = SHELF_Y if p.get('shelf', True) else 860.0
        sh._props = [('box', (gy - BOX_BASE * k_) + BOX_BASE * k_, gy)]
    elif what == 'mask':
        sh._props = [('mask (on its nail)', p.get('y', 300) - 4, p.get('y', 300) - 4)]
    for hd in p.get('hands', []):
        layers.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                 hd.get('sleeve_from'), False, hd.get('name', 'hand')))
    for lf in p.get('layers', []): layers.append(lf(F, sh))
    cam = scam(sh, None, dict(p.get('c') or dict(mv='push', rate=0.025), free=True))
    return Spec(layers, cam, None, p.get('grade', 'wl_ins_night' if p.get('night') else 'wl_ins'), 1.0, 0.0, fx=lambda t: dict(p.get('post', {})),
                hud=p.get('hud'))


# ==================================================================================================== rule cards: Theo's notebook
RULE_LINES = {1: (62, 64), 2: (85, 87), 3: (115, 115), 4: (133, 134), 5: (157, 158), 6: (184, 185), 7: (275, 275)}


def rule_write(F, n, lead=0.3):
    """write(t) 0..1 for rule n: the share of the rule's words already read (+ a lead, so a word is on the page as it is
    said). Words come from the lines' own word times; a line without them is spread evenly."""
    i0, i1 = RULE_LINES[n]
    total = len((dict(ST.WL_RULES).get(n) or ST.WL_RULE7).split())
    ts = []
    for i in range(i0, i1 + 1):
        l = F.L[i]; nw = len(l['en'].split()); ww = l.get('words') or []
        if len(ww) == nw: ts += [w_[1] for w_ in ww]
        else: ts += [l['t'] + (l['end'] - l['t']) * j / max(1, nw) for j in range(nw)]
    ts = ts[:total] + [ts[-1]] * max(0, total - len(ts))
    return lambda t: sum(1 for x in ts if x <= t + lead) / float(total)


def B_rule(F, sh):
    """Rule n large on Theo's dinosaur-notebook page ("RULE NUMBER ONE" ...), in Sam's printing, each word appearing as it is
    read (rule_write); n 7 = the blank line (write stays 0 unless p['write'] is given)."""
    p = sh.p
    n = p['n']
    wf = p.get('write') or (rule_write(F, n) if n <= 6 else (lambda t: 0.0))
    t0 = sh.t0
    mo = lambda t: (6.0 * math.sin((t - t0) * 0.6), 4.0 * math.sin((t - t0) * 0.45), 0.012 * clamp((t - t0) / 6.0), 0.0)
    sp = ST.wl_insert('rule', lambda t: dict(n=n, write=wf(t)), mo, t0=0.0)
    layers = list(sp)
    for hd in p.get('hands', []):
        layers.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                 hd.get('sleeve_from'), False, hd.get('name', 'hand'), held_pen=hd.get('pen', False)))
    cam = scam(sh, None, dict(mv='push', rate=0.008, free=True))
    return Spec(layers, cam, None, 'wl_ins', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def rule_cues(F, sh):
    sh.sfx.append(_ev(sh.t0 + 0.02, 'page_flip', -8, 0, 'close'))
    n = sh.p['n']
    if n <= 6:
        i0, i1 = RULE_LINES[n]
        sh.sfx.append(_ev(F.t(i0), 'pen_scratch', -14, 0, 'close', dur=round(F.e(i1) - F.t(i0), 2)))
        sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.7})


# ==================================================================================================== the comment prompt
def _word_pop(cv, s, x, y, size, c, t, ta, a=255, dur=0.25):
    if t < ta: return
    k = ease_out_back(clamp((t - ta) / dur))
    text(cv, s, x, y, 900, size * (0.6 + 0.4 * k), c, a * clamp((t - ta) / 0.12), 0.06, 'center', 0.6)


def _ghost_icon(pen, x, y, s, a=255, t=0.0):
    b = y + 6 * math.sin(t * 2.2)
    body = smooth([(x - 60 * s, b + 70 * s), (x - 64 * s, b - 20 * s), (x - 30 * s, b - 80 * s), (x + 30 * s, b - 80 * s), (x + 64 * s, b - 20 * s),
                   (x + 60 * s, b + 70 * s), (x + 30 * s, b + 50 * s), (x, b + 72 * s), (x - 30 * s, b + 50 * s)], True)
    pen.fill(body, '#eef2ff', a); pen.line(body, 4 * s, '#8a93b0', a)
    for dx in (-22, 22): pen.fill(oval(x + dx * s, b - 20 * s, 9 * s, 13 * s), '#1a1d2a', a)


def _pipe_icon(pen, x, y, s, a=255, t=0.0):
    jig = 3 * s * math.sin(t * 30) * (1 if (t % 1.2) < 0.15 else 0)
    pen.fill(rrect(x - 110 * s + jig, y - 22 * s, 160 * s, 44 * s, 10 * s), '#a8adb6', a)
    pen.fill(rrect(x + 30 * s + jig, y - 22 * s, 44 * s, 130 * s, 10 * s), '#a8adb6', a)
    for (xx, yy, w_, h_) in ((-120, -30, 22, 60), (22, -30, 60, 22), (22, 86, 60, 22)):
        pen.fill(rrect(x + xx * s + jig, y + yy * s, w_ * s, h_ * s, 5 * s), '#7a808a', a)


def _comment_box(pen, cv, x, y, w, txt, caret, a=255, t=0.0, sub=None):
    pen.fill(rrect(x, y, w, 150 if sub is None else 220, 22), '#1b1e27', 235 * a / 255)
    pen.line(rrect(x, y, w, 150 if sub is None else 220, 22), 2, '#4a5068', a)
    pen.fill(oval(x + 60, y + 60, 30, 30), '#5a7ab0', a)
    text(cv, '@you', x + 110, y + 50, 700, 26, '#9aa3bb', a, 0.04, 'left')
    wd = text(cv, txt, x + 110, y + 104, 800, 44, '#ffffff', a, 0.02, 'left')
    if caret and (t * 2.0) % 1.0 < 0.6: pen.fill(rect(x + 116 + wd, y + 70, 4, 44), '#ffffff', a)
    if sub is not None:
        text(cv, sub, x + 110, y + 172, 700, 34, '#ffd890', a, 0.02, 'left')


def B_pause(F, sh):
    """The comment prompt over the boys' room at night (blurred). stage 'ask' (L54-L60): ONE WORD IN THE COMMENTS / when
    something knocks inside your wall at night / GHOST or PIPES? / CHOOSE FAST (a ring drains) / that's what everybody
    does. stage 'return' (L296-L304): the word you left / GHOST or PIPES? / both let you go back to sleep / a third word /
    PERSON. / your comment edited to "person" with a name under it. Every word on screen is the word being read."""
    p = sh.p
    st_ = p.get('stage', 'ask')
    sp = ST.wl_boys('sam_wall', sam_bed='turned')
    layers = list(sp)
    w = lambda i, wd, k=0: F.w(i, wd, k) - 0.05
    tl = lambda i: F.t(i) - 0.05

    def hud(cv, t):
        pen = Pen(cv)
        u = t - sh.t0
        pen.fill(rect(0, 0, DW, 1080), '#06070c', 150 * clamp(u / 0.3))
        if st_ == 'ask':
            if t < tl(56):
                _word_pop(cv, 'ONE WORD', 960, 470, 150, '#ffffff', t, w(55, 'one'))
                _word_pop(cv, 'IN THE COMMENTS', 960, 600, 70, '#ffd890', t, w(55, 'comments'))
                return
            if t < tl(57):
                _word_pop(cv, 'SOMETHING KNOCKS', 960, 430, 96, '#ffffff', t, tl(56))
                _word_pop(cv, 'INSIDE YOUR WALL AT NIGHT.', 960, 540, 64, '#c8ccd8', t, w(56, 'inside'))
                _word_pop(cv, 'WHAT IS IT?', 960, 680, 84, '#ffd890', t, w(56, 'what'))
                for j, tk in enumerate((w(56, 'knocks') + 0.1, w(56, 'knocks') + 0.35)):
                    if tk <= t < tk + 0.5:
                        pen.line(oval(960, 300, 40 + 300 * (t - tk), 20 + 150 * (t - tk)), 4, '#ffffff', 200 * (1 - (t - tk) / 0.5))
                return
            kb = ease_out_back(clamp((t - tl(57)) / 0.4))
            _ghost_icon(pen, 600, 520, 1.6 * max(0.01, kb), 255 * clamp(kb), t)
            _pipe_icon(pen, 1340, 500, 1.4 * max(0.01, kb), 255 * clamp(kb), t)
            _word_pop(cv, 'GHOST', 600, 770, 104, '#eef2ff', t, tl(57))
            _word_pop(cv, 'OR', 960, 560, 48, '#c8ccd8', t, w(57, 'or'))
            _word_pop(cv, 'PIPES', 1340, 770, 104, '#c8d0dc', t, w(57, 'pipes'))
            if t >= tl(58):
                _word_pop(cv, 'ONE WORD.' if t < tl(59) else 'CHOOSE FAST.', 960, 940, 64, '#ffd890', t, tl(58) if t < tl(59) else tl(59))
            if tl(59) <= t:
                k_ = clamp((t - tl(59)) / max(0.5, F.e(60) - tl(59)))
                pen.line(_arc_path(960, 220, 60, -90, 360 * (1 - k_)), 10, '#ffd890', 230)
            if t >= tl(60):
                text(cv, "THAT'S WHAT EVERYBODY DOES.", 960, 1010, 700, 34, '#9aa3bb', 220 * clamp((t - tl(60)) / 0.3), 0.12, 'center', 0.5)
            return
        # ---- return
        if t < tl(298):
            _word_pop(cv, 'NOW.', 960, 380, 120, '#ffffff', t, tl(296))
            if t >= tl(297):
                _comment_box(pen, cv, 560, 520, 800, 'ghost  /  pipes', False, 255 * clamp((t - tl(297)) / 0.3), t)
                _word_pop(cv, 'THE WORD YOU LEFT BEFORE RULE TWO', 960, 780, 46, '#ffd890', t, w(297, 'word'))
            return
        if t < tl(301):
            dim = 1.0 - 0.6 * clamp((t - tl(299)) / 0.6) if t >= tl(299) else 1.0
            _ghost_icon(pen, 560, 470, 1.3, 255 * dim, t)
            _pipe_icon(pen, 1360, 460, 1.15, 255 * dim, t)
            text(cv, 'GHOST', 560, 690, 900, 92, '#eef2ff', 255 * dim, 0.06, 'center', 0.6)
            text(cv, 'PIPES', 1360, 690, 900, 92, '#c8d0dc', 255 * dim, 0.06, 'center', 0.6)
            if t >= tl(299):
                text(cv, 'BOTH LET YOU GO BACK TO SLEEP.', 960, 860, 700, 44, '#c8ccd8', 230 * clamp((t - tl(299)) / 0.3), 0.1, 'center', 0.5)
                for j in range(3):
                    v_ = ((t - tl(299)) * 0.6 + j / 3.0) % 1.0
                    text(cv, 'z', 960 + 40 * j + 30 * v_, 520 - 160 * v_, 800, 40 + 20 * j, '#9aa3bb', 200 * (1 - v_), 0.0, 'center', 0.0)
            if t >= tl(300):
                _word_pop(cv, '?', 960, 560, 160, '#ff6a6a', t, w(300, 'third'))
            return
        if t < tl(302):
            _word_pop(cv, 'PERSON.', 960, 580, 190, '#ff5a5a', t, tl(301), dur=0.3)
            return
        typed = 'person' if t >= w(303, 'person') else ('ghost / pipes' if t < w(302, 'comment') else '')
        if w(303, 'person') <= t:
            n_ = int(clamp((t - w(303, 'person')) / 0.5) * 6); typed = 'person'[:max(1, n_)]
        sub = None
        if t >= tl(304): sub = 'always believed me:  ' + '_' * int(1 + 12 * clamp((t - w(304, 'name')) / 1.2))
        _comment_box(pen, cv, 520, 430, 880, typed, True, 255, t, sub)
        _word_pop(cv, 'EDIT YOUR COMMENT', 960, 330, 56, '#ffd890', t, tl(302))
    c = dict(mv='push', f=1.1, rate=0.006, free=True)
    cam = scam(sh, sp.info.get('cam_env'), c)

    def fx(t):
        d = dict((sp.fx(t) if hasattr(sp, 'fx') else None) or {})
        d['blur'] = 7
        return d
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=fx, hud=hud)


# ==================================================================================================== the outro checklist
LIST_ITEMS = [(286, 286, 'Lock every door and window, every night, including the garage door and the basement.'),
              (287, 288, 'When you move in, change the locks and the codes. No key under the frog.'),
              (289, 290, "Food gone, things moved, doors unlocked, lights you didn't touch? Tell your family, and check together, in daylight."),
              (291, 292, "If you think someone is inside, don't look for him. Get out, or lock yourself in a room with a phone, and call 911."),
              (293, 293, 'Know your address by heart.'),
              (294, 295, "Grown-ups: when a kid says something's wrong, listen. Then check.")]


def B_list(F, sh):
    """The real list on Theo's notebook paper (warm morning light): each item appears when it is read, the one being read
    is bright and highlighted, a tick lands when it has been read; everything stays legible."""
    p = sh.p
    sp = ST.wl_living('wide', tod='morning')
    layers = list(sp)

    def hud(cv, t):
        pen = Pen(cv)
        pen.fill(rect(0, 0, DW, 1080), '#0b0c12', 165)
        text(cv, 'THE REAL LIST', 960, 140, 900, 58, '#ffd890', 245 * clamp((t - sh.t0) / 0.3), 0.18, 'center', 0.5)
        y = 220
        for k, (i0, i1, s) in enumerate(LIST_ITEMS):
            ta, tb = F.t(i0) - 0.15, F.e(i1)
            lines = _wrap_txt(s, 66)
            hh = 50 * len(lines) + 26
            if t >= ta:
                a = clamp((t - ta) / 0.25)
                cur = ta <= t < (F.t(LIST_ITEMS[k + 1][0]) - 0.15 if k + 1 < len(LIST_ITEMS) else 1e9)
                if cur: pen.fill(rrect(250, y - 40, 1420, hh, 14), '#ffffff', 26 * a)
                box = rrect(270, y - 26, 36, 36, 6)
                pen.line(box, 3, '#ffd890', 230 * a)
                if t >= tb: pen.line(poly([(277, y - 8), (288, y + 4), (302, y - 20)], False), 5, '#7ee08a', 255 * clamp((t - tb) / 0.2))
                for j, ln in enumerate(lines):
                    text(cv, ln, 336, y + j * 50, 700 if cur else 600, 40, '#ffffff' if cur else '#c8ccd8', (255 if cur else 175) * a, 0.0, 'left', 0.5)
            y += hh
    cam = scam(sh, sp.info.get('cam_env'), dict(mv='push', rate=0.004, free=True))
    return Spec(layers, cam, sp.lens, sp.grade, 1.0, 0.0, fx=lambda t: dict(blur=8), hud=hud)


# ==================================================================================================== cards
def _thumb(pen, x, y, s, a=255):
    pen.fill(rrect(x - 70 * s, y - 10 * s, 40 * s, 110 * s, 8 * s), '#ffffff', a)
    pen.fill(smooth([(x - 22 * s, y - 10 * s), (x + 6 * s, y - 90 * s), (x + 30 * s, y - 84 * s), (x + 24 * s, y - 20 * s), (x + 80 * s, y - 16 * s),
                     (x + 76 * s, y + 92 * s), (x - 22 * s, y + 100 * s)], True), '#ffffff', a)


def B_card(F, sh):
    """Plain cards: p text (lines split by \\n), sub, strikes=[(t, line index)], icon 'thumb' | 'bell' (pops at icon_t),
    bg (c1, c2) or bgset=(room, view, kw) blurred."""
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


def _arc_path(x, y, r, start, sweep):
    pth = skia.Path(); pth.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), start, sweep)
    return pth


# ==================================================================================================== the global look
EXPO = {'ins': -0.02, 'wall': 0.0}
NIGHT_LIFT = 0.12                    # night interiors: dark, but the action must read (bus-film lesson)


def glob_fx(F, sh, t, fx):
    """Per-frame global effects keyed to lines: cut flashes; a night lift; grain that rises with the nights; the 3 a.m.
    climax (L186 .. the sirens L242): a slow cold pulse at the frame edge; the outro clean; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'blink' and u < 0.12: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - u / 0.12)
    ek = EXPO.get(sh.kind, 0.0)
    st = sh.p.get('set') or {}
    if sh.kind in ('set', 'bust') and st.get('tod', 'night') not in DAYK and (sh.p.get('room') or (sh.p.get('bg') or ['street'])[0]) != 'street':
        ek += NIGHT_LIFT
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('outro',) or sh.kind in ('rule', 'black', 'card', 'pause', 'list')
    if era == 'memory': fx['sat'] = fx.get('sat', 1.0) * 0.6; fx['grain'] = max(fx.get('grain', 0.0), 0.12)
    if not clean:
        n = len(F.L)
        g = 0.05 + 0.07 * clamp((t - F.t(min(28, n - 1))) / max(1.0, F.t(min(240, n - 1)) - F.t(min(28, n - 1))))
        fx['grain'] = max(fx.get('grain', 0.0), g)
        if n > 242 and F.t(186) - LEAD <= t < F.t(242):
            ramp = clamp((t - F.t(186)) / 4.0) * (1.0 - clamp((t - F.t(242) + 1.0) / 1.0))
            ph = ((t - F.t(186)) * 0.9) % 1.0
            beat = math.exp(-ph * 6.0)
            if 'flash' not in fx:
                fx['flash'] = _epost.Spill(0.12 * ramp * beat, side=-1.0 if sh.idx % 2 else 1.0, color=(0.55, 0.65, 1.0), reach=0.7)
            fx['sat'] = fx.get('sat', 1.0) * (1.0 - 0.12 * ramp)
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names): the August house at night (fans,
    the fridge, the house settling), the day street, the sirens' night street, the morning."""
    D = F.duration
    n = len(F.L)
    t = lambda i: F.t(min(i, n - 1))
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(0.0, t(12) - 0.1, 'house_night', -16, 'inside', fans=True)
    bed(t(12) - 0.1, t(28) - 0.1, 'ambience_suburb', -18, 'outside', heat=True)
    bed(t(28) - 0.1, t(36) - 0.1, 'house_night', -16, 'inside', fans=True)
    bed(t(36) - 0.1, t(38) - 0.1, 'room_tone_house', -18, 'inside')
    bed(t(38) - 0.1, t(54) - 0.1, 'house_night', -17, 'inside', fans=True)
    bed(t(61) - 0.1, t(242), 'house_night', -16, 'inside', fans=True)
    bed(t(242), t(262) - 0.1, 'ambience_night', -18, 'outside', crickets=True)
    bed(t(262) - 0.1, t(276) - 0.1, 'ambience_dawn', -20, 'outside')
    bed(t(276) - 0.1, D, 'room_tone_house', -22, 'inside')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.6), (2, 0.8), (3, 0.9), (4, 0.4), (9, 0.3), (10, 0.55), (11, 0.75), (12, 0.15), (19, 0.25), (24, 0.2), (27, 0.3), (28, 0.6),
    (29, 0.8), (33, 0.7), (35, 0.85), (36, 0.4), (38, 0.5), (40, 0.75), (43, 0.6), (47, 0.8), (49, 0.5), (52, 0.85), (53, 0.5),
    (54, 0.3), (61, 0.45), (65, 0.4), (70, 0.55), (74, 0.65), (76, 0.85), (79, 1.0), (82, 0.8), (84, 0.5), (88, 0.45), (93, 0.4),
    (97, 0.6), (99, 0.7), (103, 0.8), (106, 0.95), (109, 1.0), (110, 0.95), (111, 0.5), (114, 0.45), (118, 0.7), (122, 0.6),
    (127, 0.75), (130, 0.8), (132, 0.5), (136, 0.3), (143, 0.7), (146, 0.9), (147, 1.0), (148, 0.8), (155, 0.5), (156, 0.4),
    (166, 0.7), (168, 0.85), (172, 0.95), (176, 0.95), (177, 0.8), (181, 0.85), (183, 0.6), (186, 0.8), (191, 0.9), (193, 1.0),
    (195, 1.0), (201, 0.9), (205, 0.95), (206, 1.0), (209, 0.95), (212, 0.9), (215, 0.95), (219, 0.85), (224, 0.8), (226, 0.9),
    (229, 0.8), (234, 0.85), (236, 1.0), (240, 1.0), (241, 1.0), (242, 0.7), (245, 0.6), (250, 0.65), (252, 0.4), (259, 0.45),
    (262, 0.4), (266, 0.7), (268, 0.8), (269, 0.6), (275, 0.9), (276, 0.2), (285, 0.25), (296, 0.35), (301, 0.7), (305, 0.25),
    (309, 0.2), (311, 0.35)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY if i < len(F.L)]
    pts.append([round(F.duration, 2), 0.0])
    return pts


# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(3, -0.5, 0.5), (79, -0.4, 0.5), (106, -0.4, 0.5), (109, -0.3, 0.4), (147, -0.4, 0.5), (172, -0.4, 0.5), (193, -0.4, 0.5),
             (195, -0.3, 0.4), (206, -0.3, 0.4), (241, -0.4, 0.5), (275, -0.5, 0.6), (301, -0.4, 0.5)]


# ==================================================================================================== plan helpers (this film)
def WL(t, mode='wall', ppl=(), **p):
    """Inside the walls (kind 'wall')."""
    _FILM[0].cut(t, 'wall', mode=mode, ppl=list(ppl), **p)


def PR(t, draw='box', **p): _FILM[0].cut(t, 'prop', draw=draw, **p)


def CARD(t, text_, **p): _FILM[0].cut(t, 'card', text=text_, **p)


def ZO(f, on, rate=0.015, **k):
    """A push framed on an anchor / plan point / '@actor' (screen point at its depth)."""
    return dict(mv='push', f=f, rate=rate, on=on, **k)


def EYE(x, y, k, t_in, t_out=None, clip=None, **kw):
    """An acts / layers entry: his eye in a gap (see eye_layer)."""
    return lambda F_, sh: eye_layer(F_, sh, x, y, k, t_in, t_out, clip, **kw)


def sil_door(t0=-9.0):
    """The doorway figure: Pell standing exactly like Dad (WALLS_TILT), arms hanging, dead still."""
    return lambda a, s: a.doorway(t0)


def pdur(i, k=0.5):
    """A time k of the way through line i."""
    F = _FILM[0]
    return F.t(i) + k * (F.e(i) - F.t(i))


# set states (keyed to the story)
DAYS = dict(tod='day')
MORN = dict(tod='morning')
B_NIGHT = dict(theo_bed='turned', sam_bed='turned')                       # the boys asleep (the covers turned)
B_EMPTY = dict(theo_bed='empty', sam_bed='turned')
KIT_N = dict(bolt=1.0)                                                    # the kitchen at night: locked, the nightlight on
KIT_D = dict(tod='day', bolt=0.0, note=False)                             # a morning: the door from the garage unlocked
HALL_N = dict(nightlight=1.0, par_door=70.0, boys_door=80.0)
PAR_N = dict(lamp=0.0, door=70.0)



# ==================================================================================================== the shot plan
# Line by line (timeline.json): every cut at T(i) (a moment before line i) or W(i, 'word'); every event at WD / pdur.
SAMW = (5.6, 2.85, 2.9)                       # beside Sam's bed (the wall by it), standing room
THEO_CAM = cm((1.05, 2.75, 4.05), (2.0, 0.95, 3.35), 900)        # Theo's bed from its foot corner: Pell kneeling faces us at 3/4
DOOR_CAM = cm((3.2, 3.2, 4.2), (0.78, 4.0, 4.0), 1100)                # the doorway from inside the room (he stands in it)
BL = dict(theo_bed='empty', sam_bed='empty')                            # the boys IN bed (the duvet drawn over the lying figure)
BLH = dict(BL, hall_light=0.7)                                          # ... and the hall light behind the doorway figure


def MC(at, ang, d=2.4, h=1.45, lh=1.0, S=1000.0, sy=560.0):
    """A camera d metres from plan point `at` (x, y, Y) in compass direction ang (deg: 0 = +y north, 90 = +x east), the
    eye h above the floor, looking at the point lh above it (which lands at screen (960, sy))."""
    X, Yp, Y = at
    a = math.radians(ang)
    return cm((X + d * math.sin(a), Yp + d * math.cos(a), Y + h), (X, Yp, Y + lh), S, sy=sy)


KIDCAM = MC((3.9, 1.75, 2.9), 0, 2.4, h=1.35, lh=0.75, S=1000)          # the boys' room: the two of them by the window
KCAM = MC((3.1, 8.2, 0.0), 200, 2.7, h=1.55, lh=1.0, S=1000)            # the kitchen: the counter, the fridge, the family
KDOOR = MC((5.4, 4.6, 0.0), 300, 2.3, h=1.5, lh=1.1, S=1000)            # the door from the garage
KSINK = MC((2.7, 8.2, 0.0), 140, 2.6, h=1.5, lh=1.0, S=1000)            # 2 a.m. at the sink
CHAIRCAM = MC((-3.25, 2.85, 0.0), 200, 2.2, h=1.3, lh=0.8, S=1000)        # Mr. Pell's armchair and whoever is at it
CHAIRFRONT = MC((-3.62, 3.22, 0.0), 135, 2.4, h=1.3, lh=0.9, S=1000)    # the armchair from the room (seated in it)


def door_pell(t0=-9.0, sil=0.85, acts=(), **k):
    """The doorway figure (Pell, Dad's flannel, Dad's tilt), facing Sam's bed."""
    return P('pell', 'doorway', face='sam_pillow', sil=sil, sil_rim='#ffc884', sil_rim_a=0.6, act=_A(sil_door(t0), *acts), id='pell', **k)


def sam_bed(expr='sleep', **k): return P('sam_pj', 'sam_bed', kind='lie', lie_face='down', expr=expr, id='sam', **k)


def theo_bed(expr='sleep', **k): return P('theo', 'theo_bed', kind='lie', lie_face='down', expr=expr, id='theo', **k)


def lie_bust(t, who, expr='sleep', act=None, **k):
    """A face on the pillow (a close shot of a lying figure): the bust turned 90 degrees over the blurred bed."""
    room, view, st = k.pop('bg', ('boys', 'sam_wall', B_NIGHT))
    BU(t, who, room, view, st, rot=k.pop('rot', 90), cx=k.pop('cx', 960), cy=k.pop('cy', 560), scale=k.pop('scale', 0.9), expr=expr, act=act,
       light=k.pop('light', NIGHT), **k)


def note_kw(i=25):
    """Pell's note with the sentence being read highlighted (Dad reading it out, L25)."""
    F = _FILM[0]
    keys = [F.w(i, wd) - 0.1 for wd in ('welcome', 'few', 'settles', 'pipes', 'mice', 'one', 'attic', 'happy', 'pell')]

    def kw(u, t0):
        t = t0 + u
        k = max([j for j, tk in enumerate(keys) if t >= tk] or [0])
        return dict(hl=k)
    return kw


def chew(t0, t1):
    """Slow, careful chewing (his own teeth in the mask's slit)."""
    def f(a, s):
        def fn(P_, t):
            if t0 <= t <= t1: P_.m_open = max(P_.m_open, 0.06 + 0.12 * abs(math.sin((t - t0) * 3.4)))
        a._add(t0 - 0.1, t1 + 0.1, fn)
    return f


def to_mouth(times, side=-1, hold=0.7):
    """His hand brings the food to the mask's mouth slit and back."""
    def f(a, s):
        for tk in times:
            a.reach_to(tk, side, a.where(tk, 'mouth'), t1=tk + hold, dur=0.35, shape='grip', lean=False)
    return f


def plan_open(F):
    # 0 If your little brother says someone lives in the walls... don't laugh.
    S(T(0), 'boys', 'sam_wall', st=BL, ppl=[sam_bed('neutral', act=_A(lk(T(0) + 0.5, ('theo', 'head')))),
                                                 P('theo', SAMW, face=(6.0, 2.85), id='theo', act=_A(reach(T(0) + 0.6, -1, (5.98, 2.85, 3.75), dur=0.6, shape='flat', contact='palm')))],
      c=ZO(1.35, SAMW, h=0.8))
    WL(W(0, "don't"), 'wall', [WP('pell', 1080, turn=-0.55, h_turn=-0.2, act=_A(lambda a, s: a.head_to(WD(0, "don't") + 0.1, (720, 300), 'eye_l', dur=0.9), tilt(E(0) - 0.3, 14, 1.6)))],
       slits=[(720, 220, 640, 1.0)], c=Z(1.3, 0.02, 900, 420), sfx=[(WD(0, 'laugh'), 'knock_door', -14, 0.3, 'wall', dict(n=1, soft=True))])
    # 1 If the armchair is warm in the morning, and nobody sat in it... don't say it's the heater.
    S(T(1), 'living', 'wide', st=dict(), cam=CHAIRFRONT, ppl=[P('pell', 'armchair', id='pell', expr='neutral', stand_t=W(1, 'nobody') - 0.5, act=_A(tilt(T(1) + 0.4, 12, 1.4)))],
      c=Z(1.05, 0.01))
    S(W(1, 'nobody'), 'living', 'chair', st=MORN, c=ZO(1.25, 'armchair', ody=-100, rate=0.02))
    S(W(1, "don't"), 'living', 'vent', st=MORN, c=Z(1.0, 0.02))
    # 2 ... your dad stands in your bedroom doorway at three in the morning, in his red flannel shirt, head tilted, just watching you sleep... don't say goodnight.
    S(T(2), 'boys', 'door_pov', st=BLH, ppl=[door_pell()], c=ZO(2.6, '@pell', part='chest', rate=0.01))
    S(W(2, 'red'), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[door_pell(sil=0.5)], c=Z(1.5, 0.01, 930, 640))
    S(W(2, 'just'), 'boys', 'sam_wall', st=BL, ppl=[sam_bed()], c=ZO(1.8, 'sam_pillow'))
    S(W(2, "don't"), 'boys', 'door_pov', st=BLH, ppl=[door_pell()], c=ZO(3.0, '@pell', part='head', rate=0.02))
    # 3 Your dad is asleep.
    S(T(3), 'parents', 'bed', st=PAR_N, ppl=[P('dad_pj', 'bed_dad', kind='lie', expr='sleep'), P('mom_pj', 'bed_mom', kind='lie', expr='sleep')],
      c=ZO(1.6, 'bed_dad', ody=-40), hit=E(3) - 0.05)
    # 4-8 Theo's seven rules; he was six; the dinosaur notebook; I was twelve; the silliest rules
    S(T(4), 'boys', 'wide', st=dict(MORN, theo_bed='made', sam_bed='made'), cam=KIDCAM,
      ppl=[P('theo', (3.1, 2.0, 2.9), face=(4.3, 3.4), expr='kid_grin', id='theo', act=_A(lk(T(4), ('sam', 'head')))),
           P('sam', 'sam_edge', face=(3.6, 3.3), expr='neutral', id='sam', act=_A(lk(T(4) + 0.3, ('theo', 'head'))))], c=Z(1.0, 0.012))
    BU(T(5), 'theo', 'boys', 'wide', dict(MORN), cx=980, cy=600, scale=0.9, h_turn=0.25, expr='proud_grin', light=MORNING, c=BZ(0.02))
    IN(T(6), 'rules', lambda u: dict(show=min(6, int(1 + u * 1.5)), seven=0.0), c=dict(mv='push', rate=0.02))
    BU(T(7), 'sam', 'boys', 'wide', dict(MORN), cx=940, cy=600, scale=0.9, h_turn=-0.25, expr='calm_smirk', light=MORNING, c=BZ(0.02))
    S(T(8), 'boys', 'wide', st=dict(MORN, theo_bed='made', sam_bed='made'), cam=KIDCAM,
      ppl=[P('theo', (3.1, 2.0, 2.9), face=(4.3, 3.4), expr='kid_grin', id='theo'), P('sam', 'sam_edge', face=(3.6, 3.3), expr='calm_smirk', id='sam',
                                                                                     act=_A(lk(T(8), ('theo', 'head')), tilt(pdur(8, 0.4), -8, 1.2)))],
      c=Z(1.15, 0.012))
    IN(W(8, 'ever'), 'vent', dict(rattle=0.0), layers=[EYE(960, 560, 9.0, W(8, 'ever') + 0.35, clip=vent_gaps(), blinks_=(E(8) - 0.2,))],
       c=dict(mv='push', rate=0.03))
    # 9-10 Every grown-up had an explanation. Every explanation was wrong.
    S(T(9), 'kitchen', 'wide', st=KIT_D, cam=KCAM, ppl=[P('dad_tee', (3.5, 8.5, 0.0), face=(2.4, 5.8), expr='talk_smile', id='dad', act=_A(lambda a, s: a.laugh(T(9) + 0.4, 1.4))),
                                               P('mom', (2.6, 8.2, 0.0), face=(3.4, 7.0), expr='kind_smile', id='mom')], c=Z(1.0, 0.012))
    WL(T(10), 'wall', [WP('pell', 900, turn=0.45, h_turn=0.35, act=_A(tilt(T(10) + 0.3, 16, 1.8)))], slits=[(1250, 260, 760, 1.0)], c=Z(1.25, 0.02, 960, 380))
    # 11 By morning: three police cars, a hole in my closet wall, a man with a dog's face on our curb in handcuffs ... living in his house.
    S(T(11), 'street', 'house', st=dict(police=ST.wl_police(T(11) - 3), win=dict(boys=0.6, par=0.6)), c=Z(1.2, 0.015, 1000, 560))
    S(W(11, 'hole'), 'boys', 'closet_sam', st=dict(sam_closet=140.0, hole=True, flash=0.5, flash_at=(4.3, 4.3, 3.9), police=True), c=Z(1.2, 0.02))
    S(W(11, 'man'), 'street', 'curb', st=dict(police=True), ppl=[P('pell', 'curb_sit', id='pell', hands=None, act=_A(lambda a, s: a.cuffed(), lk(W(11, 'telling'), (300, 380), dur=0.8))),
                                                              P('reyes', 'curb_officer', face='curb_sit', expr='calm_firm', id='reyes', act=_A(lk(W(11, 'man'), ('pell', 'head'))))],
      c=ZO(1.8, 'curb_sit', h=0.7), cut='blink')
    BU(W(11, 'living'), 'pell', 'street', 'curb', dict(police=True), cx=980, cy=560, scale=0.95, h_turn=0.4, light=POLICE,
       act=_A(tilt(W(11, 'living') + 0.2, 14, 1.4), lookxy(1500, 300, W(11, 'living'))), c=BZ(0.02))


def plan_moving(F):
    # 12-14 We moved into fourteen Larkspur Lane in August. A heat wave. Fans in every window.
    fam = [P('dad', 'walk', face='porch_out', id='dad', path=[(T(12), (0.2, -6.0, -0.5)), (E(12) + 0.4, 'walk')], surface='grass'),
           P('mom', (1.1, -6.6, -0.5), id='mom', path=[(T(12) + 0.2, (1.3, -7.2, -0.5)), (E(12) + 0.4, (1.0, -5.3, -0.5))], surface='grass'),
           P('sam', (-0.4, -7.0, -0.5), id='sam', path=[(T(12) + 0.1, (-0.5, -7.6, -0.5)), (E(12) + 0.4, (-0.3, -5.9, -0.5))], surface='grass'),
           P('theo', (1.8, -6.3, -0.5), id='theo', expr='kid_grin', path=[(T(12), (2.4, -7.0, -0.5)), (E(12) + 0.3, (1.8, -5.6, -0.5))], surface='grass', run=True)]
    S(T(12), 'street', 'house', st=dict(DAYS), ppl=fam, c=Z(1.7, 0.01, 1000, 600))
    BU(T(13), 'dad', 'street', 'porch', DAYS, cx=960, cy=600, scale=0.9, h_turn=0.2, expr='sweaty', light=DAY, act=_A(lk(T(13), (960, 120)), blinks(T(13) + 0.4)), c=BZ(0.02))
    S(T(14), 'living', 'window', st=DAYS, c=Z(1.1, 0.02))
    # 15-19 The old owner had just walked away. Left everything. His big green armchair. His curtains. A stone frog ... a key under it.
    S(T(15), 'street', 'house', st=DAYS, c=Z(1.15, 0.015, 1000, 520))
    S(T(16), 'living', 'wide', st=dict(DAYS, boxes=True), c=Z(1.1, 0.015))
    S(T(17), 'living', 'chair', st=DAYS, c=ZO(1.3, 'armchair', ody=-120))
    S(T(18), 'living', 'window', st=DAYS, c=Z(1.3, 0.02, 960, 460))
    S(T(19), 'street', 'frog', st=dict(DAYS, frog_lift=lambda t: 0.6 * ease_in_out(clamp((t - W(19, 'key')) / 0.6))), c=Z(1.1, 0.02))
    IN(W(19, 'under'), 'frog', lambda u: dict(lift=0.7 * ease_out_cubic(clamp(u / 0.5)), key=True, tod='day'), c=dict(mv='push', rate=0.03))
    # 20 "Handy," Dad said, and left it there.
    BU(T(20), 'dad', 'street', 'porch', DAYS, cx=960, cy=620, scale=0.95, h_turn=0.3, expr='talk_smile', light=DAY, act=_A(lookxy(700, 900, T(20) - 0.5), tilt(T(20) + 0.1, 8, 0.9)),
       c=BZ(0.015))
    # 21-23 The garage had a keypad. It still opened on Mr. Pell's old code. Dad said he'd change it this weekend.
    S(T(21), 'street', 'garage', st=DAYS, c=Z(1.1, 0.02))
    code = '4815'
    IN(T(22), 'keypad', lambda u: dict(press=code[min(3, int(u / 0.38))] if u < 1.6 else None, tod='day'), c=dict(mv='push', rate=0.03),
       sfx=[(T(22) + 0.05 + 0.38 * k, 'keypad_beep', -12, 0, 'close') for k in range(4)] + [(T(22) + 1.75, 'garage_door', -10, 0, 'outside')])
    S(T(23), 'street', 'garage', st=DAYS, ppl=[P('dad', 'keypad_stand', face='keypad', expr='talk_smile', id='dad',
                                                act=_A(lk(T(23), 'keypad'), lambda a, s: a.walls_tilt(pdur(23, 0.5), None, 0.6)))], c=ZO(2.0, 'keypad_stand', h=1.1))
    # 24 On the kitchen counter, there was a note for us, in shaky handwriting.
    S(T(24), 'kitchen', 'wide', st=dict(DAYS, note=True), cam=KCAM, ppl=[P('dad', (3.5, 8.6, 0.0), face='note', id='dad', act=_A(lk(T(24), 'note'))),
                                                               P('mom', (2.7, 8.4, 0.0), face='note', id='mom', act=_A(lk(T(24) + 0.3, 'note')))],
      c=Z(1.0, 0.012))
    IN(W(24, 'shaky'), 'note', dict(show=9), c=dict(mv='push', rate=0.03))
    # 25 Dad reads the note out (word for word, the sentence lit)
    kw = note_kw(25)
    IN(T(25), 'note', (lambda u, t0=T(25): kw(u, t0)), c=dict(mv='push', rate=0.012))
    BU(W(25, 'settles'), 'dad', 'kitchen', 'wide', DAYS, cx=980, cy=600, scale=0.92, h_turn=0.3, expr='talk_smile', light=DAY,
       act=_A(lookxy(760, 820, W(25, 'settles'))), c=BZ(0.015))
    WL(W(25, 'mice'), 'wall', [WP('pell', 860, turn=0.5, h_turn=0.4, act=_A(tilt(W(25, 'mice') + 0.2, 18, 1.6)))], slits=[(1300, 200, 760, 0.9)],
       c=Z(1.4, 0.02, 900, 360))
    IN(W(25, 'one'), 'note', (lambda u, t0=W(25, 'one'): kw(u, t0)), c=dict(mv='push', rate=0.02))
    S(W(25, 'be'), 'kitchen', 'wide', st=dict(DAYS, note=False), cam=KCAM, ppl=[P('dad', 'counter_front', face=(2.4, 5.8), id='dad', expr='talk_smile',
                                                                     act=_A(lambda a, s: a.read_note(W(25, 'be') - 0.6, E(27) + 2, side=-1)))],
      c=ZO(1.6, 'counter_front', h=1.3))
    # 26 Dad read it out loud, and laughed.  27 "Well, that's every noise explained."
    S(T(26), 'kitchen', 'wide', st=dict(DAYS, note=False), cam=KCAM,
      ppl=[P('dad', 'counter_front', face=(2.4, 5.8), id='dad', act=_A(lambda a, s: a.read_note(T(26) - 2, E(27) + 2, side=-1), lambda a, s: a.laugh(W(26, 'laughed'), 1.6))),
           P('mom', (3.1, 8.5, 0.0), face='counter_front', expr='warm_smile', id='mom'), P('sam', (2.5, 7.8, 0.0), face='counter_front', expr='calm_smirk', id='sam')],
      c=Z(1.0, 0.012))
    BU(T(27), 'dad', 'kitchen', 'wide', DAYS, cx=960, cy=600, scale=0.92, h_turn=0.25, expr='talk_smile', light=DAY, act=_A(lookxy(400, 520, T(27))), c=BZ(0.015))


def plan_night1(F):
    # 28-35 the first night: "Dad" in the doorway
    lie_bust(T(28), 'sam_pj', 'neutral', act=_A(blinks(T(28) + 0.5), lookxy(400, 300, pdur(28, 0.6), dur=0.5)))
    S(T(29), 'boys', 'door_pov', st=BLH, ppl=[door_pell()], c=ZO(2.6, '@pell', part='chest'))
    S(T(30), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[door_pell(sil=0.5)], c=Z(1.6, 0.01, 930, 660))
    S(T(31), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[door_pell(sil=0.85)], c=Z(2.6, 0.01, 930, 420))
    S(T(32), 'boys', 'theo', st=BL, ppl=[theo_bed()], c=ZO(2.4, 'theo_pillow', h=0.2))
    lie_bust(T(33), 'sam_pj', 'sleepy', act=_A(lookxy(300, 300, T(33))))
    S(T(34), 'boys', 'door_pov', st=BLH, ppl=[door_pell()], c=ZO(2.6, '@pell', part='head'))
    S(T(35), 'boys', 'door_pov', st=B_NIGHT, ppl=[P('pell', 'doorway', face='sam_pillow', sil=0.85, sil_rim='#ffc884', id='pell', no_walk=True,
                                                  path=[(W(35, 'backed'), 'doorway'), (E(35) + 0.2, (0.2, 4.6, 2.9))], act=_A(sil_door(), lambda a, s: a.back_away(W(35, 'backed'), E(35), 4)))],
      c=ZO(2.0, 'doorway', h=1.0))
    # 36-37 In the morning, Dad couldn't find his red flannel shirt. He said it got lost in the move.
    S(T(36), 'living', 'wide', st=dict(MORN, boxes=True), ppl=[P('dad_tee', 'room_mid', face=(-3.4, 1.4), id='dad', expr='grumpy',
                                                                 act=_A(lambda a, s: a.crouch(T(36) + 0.2, 0.6, E(36) + 0.5), lk(T(36), (-3.4, 1.4, 0.3))))],
      c=ZO(1.9, 'room_mid', h=0.7))
    BU(T(37), 'dad_tee', 'living', 'wide', MORN, cx=960, cy=600, scale=0.92, h_turn=-0.2, expr='tired_kind', light=MORNING, act=_A(lookxy(1300, 500, T(37))), c=BZ(0.015))
    WL(W(37, 'lost'), 'wall', [WP('pell', 960, turn=0.4, h_turn=0.3, act=_A(lambda a, s: a.reach_to(W(37, 'lost') + 0.2, 1, a.where(W(37, 'lost'), 'chest'), t1=E(37) + 0.6, dur=0.5, shape='flat'),
                                                                        tilt(E(37) - 0.4, 12, 1.2)))], slits=[(560, 220, 720, 0.9), (1380, 300, 820, 0.7)], c=Z(1.3, 0.02, 960, 460))
    # 38-40 The next night, Theo told us about Hushabye. "He lives in the wall," "He sings hush-a-bye ... He has a sad dog face."
    KN = dict(kitchen_light=1.0, bolt=1.0)
    S(T(38), 'kitchen', 'wide', st=KN, cam=KCAM, ppl=[P('theo', (2.5, 7.7, 0.0), face=(3.4, 8.3), expr='nervous', id='theo'),
                                           P('dad_tee', (3.5, 8.5, 0.0), face=(2.5, 7.7), expr='kind_smile', id='dad'),
                                           P('mom', (3.0, 8.9, 0.0), face=(2.5, 7.7), expr='kind_smile', id='mom')], c=Z(1.0, 0.012))
    BU(T(39), 'theo', 'kitchen', 'wide', KN, cx=960, cy=620, scale=0.95, h_turn=-0.3, expr='nervous', light=LAMP,
       act=_A(lambda a, s: a.point(T(39) + 0.2, E(39) + 0.4, -1, 1.0, -0.1), lookxy(200, 500, T(39))), c=BZ(0.015))
    BU(T(40), 'theo', 'kitchen', 'wide', KN, cx=900, cy=600, scale=1.05, h_turn=0.2, expr='nervous', light=LAMP, c=BZ(0.02))
    WL(W(40, 'he', 1), 'wall', [WP('pell', 1000, turn=-0.3, h_turn=0.35, act=_A(tilt(W(40, 'sad') - 0.2, 18, 1.4)))], slits=[(700, 240, 700, 1.0)],
       c=ZO(2.0, '@pell', part='head', ody=40))
    # 41-42 Mom and Dad looked at each other. Because they knew where a sad dog face came from.
    BU(T(41), 'mom', 'kitchen', 'wide', KN, cx=700, cy=620, scale=0.8, h_turn=0.45, expr='nervous', light=LAMP, act=_A(lookxy(1300, 470, T(41) + 0.2)),
       busts=[dict(who='dad_tee', cx=1260, cy=600, scale=0.8, h_turn=-0.45, expr='guilt', act=_A(lookxy(600, 470, T(41) + 0.35)))], c=BZ(0.012))
    BU(T(42), 'dad_tee', 'kitchen', 'wide', KN, cx=980, cy=600, scale=0.95, h_turn=-0.15, expr='guilt', light=LAMP, act=_A(lookxy(960, 900, pdur(42, 0.5))), c=BZ(0.02))
    # 43-48 Dad's old Halloween mask. A rubber hound. Long droopy ears. Heavy, sad eyes. Real teeth. It gave Theo nightmares for a year.
    PR(T(43), 'mask', era='memory', k=13.0, y=300, shelf=False, bg=('#4a4038', '#1a1512'), c=dict(mv='push', rate=0.03))
    BU(T(44), 'pell', 'boys', 'doorway', B_NIGHT, cx=960, cy=560, scale=0.95, h_turn=0.35, light=NIGHT, c=BZ(0.02))
    BU(T(45), 'pell', 'boys', 'doorway', B_NIGHT, cx=1060, cy=620, scale=1.3, h_turn=0.45, light=NIGHT, act=_A(tilt(T(45) + 0.1, 14, 1.0)), c=BZ(0.02))
    BU(T(46), 'pell', 'boys', 'doorway', B_NIGHT, cx=960, cy=700, scale=1.9, h_turn=0.3, light=NIGHT, act=_A(blinks(pdur(46, 0.7))), c=BZ(0.015))
    BU(T(47), 'pell', 'boys', 'doorway', B_NIGHT, cx=960, cy=360, scale=1.9, h_turn=0.3, light=NIGHT, act=_A(pose(T(47) + 0.1, E(47) + 0.5, 0.3, m_open=0.32)),
       c=BZ(0.015), no_lip=True)
    lie_bust(T(48), 'theo', 'fear', era='memory', act=_A(blinks(T(48) + 0.3)))
    # 49 So Dad taped it into a box, wrote GONE FOREVER on the lid, and put it on the top shelf in the garage.
    PR(T(49), 'box', era='memory', box=dict(lid=lambda u: 0.0, tape=lambda u, t0=T(49): clamp((t0 + u - W(49, 'taped')) / 0.5),
                                            write=lambda u, t0=T(49): clamp((t0 + u - W(49, 'wrote')) / 1.2)),
       sfx=[(WD(49, 'taped'), 'tape_rip', -10, 0, 'close'), (WD(49, 'wrote'), 'marker', -12, 0, 'close'), (WD(49, 'shelf'), 'box_set', -10, 0, 'close')])
    # 50-51 "It's a nightmare, buddy," "The mask is in the garage. Taped shut."
    S(T(50), 'kitchen', 'wide', st=KN, cam=KCAM, ppl=[P('theo', (2.6, 7.7, 0.0), face=(3.2, 8.3), expr='nervous', id='theo'),
                                           P('dad_tee', (3.2, 8.3, 0.0), kind='kneel', face=(2.6, 7.7), expr='kind_smile', id='dad',
                                             act=_A(reach(T(50) + 0.4, 1, ('theo', 'shoulder_l'), dur=0.5, shape='flat')))], c=ZO(1.5, (2.9, 8.0, 0.0), h=0.6))
    BU(T(51), 'dad_tee', 'kitchen', 'wide', KN, cx=960, cy=600, scale=0.92, h_turn=0.3, expr='kind_smile', light=LAMP, c=BZ(0.015))
    # 52 Nobody checked.  (the box in the dark garage: the tape slit, the lid up, empty)
    PR(T(52), 'box', night=True, box=dict(lid=0.25, empty=True, night=True), bg=('#1a1c24', '#07080c'), hit=WD(52, 'checked') + 0.1, c=dict(mv='push', rate=0.04))
    # 53 That's when Theo made his rules.
    S(T(53), 'boys', 'wide', st=dict(B_NIGHT, lamp=1.0), cam=KIDCAM, ppl=[P('theo', (3.1, 2.0, 2.9), face=(4.3, 3.4), expr='determined', id='theo',
                                                               act=_A(lambda a, s: a.point(T(53) + 0.3, E(53) + 0.5, 1, 0.4, 0.3))),
                                                             P('sam_pj', 'sam_edge', face=(3.6, 3.3), expr='calm_smirk', id='sam', act=_A(lk(T(53), ('theo', 'head'))))],
      c=Z(1.0, 0.012))


def plan_prompt(F):
    F.cut(T(54), 'pause', stage='ask', no_caption=False, sfx=[(WD(56, 'knocks') + 0.1, 'knock_door', -6, 0, 'close', dict(n=2))],
          music=[(T(54), 'silence', 0.0, 0.8)])


def plan_rule1(F):
    RULE(T(61), 1)
    # 65-69 So Mom did. Front door. Back door. The door from the garage into the kitchen. Every night, she checked every lock, and Theo checked behind her.
    S(T(65), 'kitchen', 'door', st=dict(KIT_N, bolt=0.0), cam=KDOOR, ppl=[P('mom', (5.4, 4.35, 0.0), face=(5.98, 4.48), id='mom', expr='focused')], c=Z(1.0, 0.012))
    IN(T(66), 'deadbolt', lambda u: dict(turn=ease_in_out(clamp((u - 0.2) / 0.4))), sfx=[(T(66) + 0.35, 'deadbolt', -8, 0, 'close')], c=dict(mv='push', rate=0.02))
    IN(T(67), 'deadbolt', lambda u: dict(turn=ease_in_out(clamp((u - 0.1) / 0.3))), motion=lambda u: (0.0, 0.0, 0.1, 6.0), sfx=[(T(67) + 0.25, 'deadbolt', -8, 0, 'close')])
    tb = WD(68, 'kitchen') - 0.2
    S(T(68), 'kitchen', 'door', st=dict(KIT_N, bolt=lambda t: ease_in_out(clamp((t - tb - 0.3) / 0.4))), cam=KDOOR,
      ppl=[P('mom', (5.4, 4.35, 0.0), face=(5.98, 4.48), id='mom', expr='focused', act=_A(reach(tb, 1, 'deadbolt', t1=tb + 1.0, dur=0.4, shape='grip', contact='fingers')))],
      c=Z(1.25, 0.012, 1000, 480), sfx=[(tb + 0.5, 'deadbolt', -8, 0, 'inside')])
    tt = W(69, 'theo') + 0.2
    S(T(69), 'kitchen', 'door', st=dict(KIT_N, bolt=1.0), cam=KDOOR,
      ppl=[P('mom', (4.85, 4.0, 0.0), face=(3.5, 5.6), id='mom', expr='kind_smile', act=_A(lk(tt, ('theo', 'head')))),
           P('theo', (5.45, 4.75, 0.0), face=(5.98, 4.48), id='theo', expr='determined', act=_A(reach(tt, 1, 'knob', t1=tt + 1.2, dur=0.45, shape='grip', contact='fingers')))],
      c=Z(1.0, 0.012), sfx=[(tt + 0.5, 'doorknob', -10, 0, 'inside')])
    # 70-72 And every morning, one door was unlocked. Always the same one. The door from the garage into the kitchen.
    S(T(70), 'kitchen', 'wide', st=KIT_D, cam=MC((4.9, 5.0, 0.0), 250, 2.4), ppl=[P('mom', (4.6, 5.2, 0.0), face=(5.98, 4.48), id='mom', expr='suspicious', act=_A(lk(T(70) + 0.3, 'deadbolt')))],
      c=Z(1.0, 0.012))
    IN(T(71), 'deadbolt', dict(turn=0.0), c=dict(mv='push', rate=0.03))
    IN(W(71, 'same'), 'keypad', lambda u: dict(press='4815'[min(3, int(u / 0.3))] if u < 1.2 else None), c=dict(mv='push', rate=0.04), era='memory',
       hands=[dict(who='pell', fn=slide(W(71, 'same'), W(71, 'same') + 0.5, (1300, 1250), (1010, 720), -30.0), size=520.0, shape='point', side=1, sleeve_from=(1700, 1500))],
       sfx=[(W(71, 'same') + 0.15 + 0.3 * k, 'keypad_beep', -14, 0, 'outside') for k in range(4)])
    S(T(72), 'kitchen', 'door', st=KIT_D, c=ZO(1.6, 'deadbolt', ody=60, rate=0.025))
    # 73 "You forgot,"
    S(T(73), 'kitchen', 'wide', st=KIT_D, cam=MC((4.1, 5.4, 0.0), 250, 2.5), ppl=[P('dad_tee', (3.6, 5.6, 0.0), face=(4.6, 5.2), expr='calm_smirk', id='dad', act=_A(lk(T(73), ('mom', 'head')))),
                                              P('mom', (4.6, 5.2, 0.0), face=(3.6, 5.6), id='mom', expr='grumpy', act=_A(lk(T(73) + 0.2, ('dad', 'head'))))],
      c=Z(1.0, 0.012))
    # 74-83 the fifth night, two in the morning: the deadbolt turns by itself
    S(T(74), 'kitchen', 'water', st=KIT_N, cam=KSINK, ppl=[P('sam_pj', (2.75, 8.6, 0.0), id='sam', path=[(T(74), (2.0, 7.4, 0.0)), (E(74) - 0.4, (2.7, 8.6, 0.0))],
                                                surface='inside_quiet', expr='sleepy')], c=Z(1.0, 0.012))
    S(T(75), 'kitchen', 'wide', st=KIT_N, cam=KSINK, ppl=[P('sam_pj', (2.7, 8.6, 0.0), id='sam', face=(5.98, 4.48), expr='neutral', act=_A(lk(T(75) + 0.4, 'deadbolt', dur=0.7)))],
      c=Z(1.1, 0.012))
    BU(T(76), 'sam_pj', 'kitchen', 'water', KIT_N, cx=980, cy=600, scale=0.95, h_turn=0.35, expr='fear', light=NL_R, act=_A(lookxy(1500, 520, T(76))), c=BZ(0.02))
    tturn = (WD(76, 'turn'), WD(79, 'click'))
    turnf = lambda t: 1.0 - 0.8 * ease_in_out(clamp((t - tturn[0]) / max(0.5, tturn[1] - tturn[0] - 0.15))) - 0.2 * clamp((t - tturn[1]) / 0.08)
    S(W(76, 'turn'), 'kitchen', 'water', st=dict(KIT_N, bolt=turnf), c=ZO(1.9, 'deadbolt', ody=20, rate=0.03))
    IN(T(77), 'deadbolt', lambda u, t0=T(77): dict(turn=turnf(t0 + u)), c=dict(mv='push', rate=0.035), sfx=[(T(77), 'deadbolt', -16, 0, 'close', dict(slow=True, dur=1.8))])
    IN(T(79), 'deadbolt', lambda u, t0=T(79): dict(turn=turnf(t0 + u)), c=dict(mv='push', f=1.25, rate=0.02), sfx=[(WD(79, 'click'), 'deadbolt', -4, 0, 'close', dict(click=True))],
       hit=WD(79, 'click') + 0.05)
    S(T(80), 'kitchen', 'door', st=dict(KIT_N, bolt=0.0), c=ZO(1.4, 'deadbolt', ody=150, rate=0.02))
    S(T(81), 'kitchen', 'water', st=dict(KIT_N, bolt=0.0), c=ZO(1.5, 'deadbolt', ody=60, rate=0.02))
    S(T(82), 'kitchen', 'wide', st=dict(KIT_N, bolt=0.0), cam=KSINK, ppl=[P('sam_pj', (2.7, 8.6, 0.0), id='sam', face=(5.98, 4.48), expr='fear', act=_A(lk(T(82), 'kitchen_mid', dur=0.6), lk(pdur(82, 0.6), 'door_in')))],
      c=Z(1.0, 0.01))
    # 83 Nobody I could see.  (he is in the wall by the door, an inch of plaster away, his finger at the mask's mouth)
    WL(T(83), 'wall', [WP('pell', 1020, turn=-0.4, h_turn=0.3, act=_A(lambda a, s: a.shush(T(83) + 0.2, None, side=1)))], slits=[(560, 240, 760, 1.0)],
       c=Z(1.5, 0.02, 1000, 380))


def plan_rule2(F):
    RULE(T(84), 2)
    # 88-92 Things went missing. Half a loaf. Four yogurts. Theo's chocolate cereal. A whole roast chicken...
    S(T(88), 'kitchen', 'wide', st=dict(KIT_D, bread='open'), cam=KCAM, ppl=[P('mom', 'fridge', face=(2.6, 6.0), expr='suspicious', id='mom', act=_A(lk(T(88) + 0.2, 'bread')))],
      c=Z(1.05, 0.012))
    IN(T(89), 'bread', dict(state='open'), c=dict(mv='push', rate=0.03))
    WL(T(90), 'wall', [WP('pell', 960, turn=0.6, h_turn=0.35, food=('yogurt', -1, T(90) - 1), act=_A(to_mouth([T(90) + 0.3]), chew(T(90) + 0.7, E(90) + 0.3)))],
       chew=True, c=ZO(1.9, '@pell', part='head', ody=40, rate=0.008))
    WL(T(91), 'wall', [WP('pell', 900, turn=0.5, h_turn=0.3, food=('cereal', -1, T(91) - 1), act=_A(to_mouth([T(91) + 0.25]), chew(T(91) + 0.6, E(91) + 0.3)))],
       chew=True, seed=2, c=ZO(1.9, '@pell', part='head', ody=40, rate=0.008))
    WL(T(92), 'wall', [WP('pell', 1000, turn=0.55, h_turn=0.4, food=('chicken', -1, T(92) - 1), act=_A(to_mouth([T(92) + 0.3, pdur(92, 0.7)]),
                                                                                                    chew(T(92) + 0.7, E(92) + 0.3)))], chew=True, seed=3, c=ZO(1.9, '@pell', part='head', ody=40, rate=0.008))
    # 93-95 "Mice," "The note said."  "Mice don't twist the bread bag shut,"
    S(T(93), 'kitchen', 'wide', st=dict(KIT_D, bread='twisted'), cam=KCAM, ppl=[P('dad_tee', (3.5, 8.5, 0.0), face=(2.5, 7.7), expr='talk_smile', id='dad'),
                                                                     P('sam', (2.5, 7.7, 0.0), face=(3.5, 8.5), expr='suspicious', id='sam', act=_A(lk(T(93), ('dad', 'head'))))],
      c=Z(1.05, 0.012))
    BU(T(95), 'sam', 'kitchen', 'wide', KIT_D, cx=960, cy=600, scale=0.95, h_turn=-0.3, expr='stern', light=DAY_L, act=_A(lookxy(1400, 500, T(95))), c=BZ(0.015))
    # 96-98 Because that's what we found... The bag, folded neatly, twisted shut again. Like someone polite had been eating our food.
    IN(T(96), 'bread', dict(state='twisted'), c=dict(mv='push', rate=0.03))
    IN(T(97), 'bread', lambda u: dict(state='twisted'), grade='wl_ins_night', c=dict(mv='push', f=1.15, rate=0.03),
       hands=[dict(who='pell', fn=lambda t, t0=T(97): (1260 + 30 * math.sin((t - t0) * 4.0), 560, -70.0 + 25 * math.sin((t - t0) * 4.0), 1.0), size=430.0, shape='grip', side=1,
                   sleeve_from=(1900, 700))], sfx=[(T(97) + 0.3, 'plastic_bag', -12, 0, 'close')])
    WL(T(98), 'wall', [WP('pell', 960, turn=0.45, h_turn=0.3, food=('bread', -1, T(98) - 1), act=_A(to_mouth([T(98) + 0.4]),
                                                                                                  chew(T(98) + 0.8, E(98) + 0.4), tilt(pdur(98, 0.6), 10, 1.0)))], chew=True, seed=4,
       c=ZO(1.9, '@pell', part='head', ody=40, rate=0.008))
    # 99-102 That night, I heard chewing. Inside the pantry wall. Slow. Careful.
    S(T(99), 'kitchen', 'pantry', st=dict(KIT_N, pantry_light=0.5, crack=0.4), ppl=[P('sam_pj', 'pantry_mid', face=(6.0, 9.42), id='sam', expr='fear',
                                                                                     act=_A(lk(T(99) + 0.3, 'crack', dur=0.6)))], c=Z(1.1, 0.015))
    S(T(100), 'kitchen', 'crack', st=dict(KIT_N, crack=0.4), c=Z(1.0, 0.02))
    WL(T(101), 'wall', [WP('pell', 960, h=900, turn=0.3, h_turn=0.35, food=('bread', -1, T(101) - 1), act=_A(to_mouth([T(101) - 0.4]), chew(T(101), E(102) + 0.3)))],
       chew=True, slits=[(1350, 260, 760, 1.0)], c=ZO(2.1, '@pell', part='head', ody=60, rate=0.006))
    # 103-105 a crack in the plaster behind the cereal boxes; wide enough for light; I leaned in
    S(T(103), 'kitchen', 'pantry', st=dict(KIT_N, pantry_light=0.5, crack=1.0), c=Z(1.2, 0.02))
    S(T(104), 'kitchen', 'crack', st=dict(KIT_N, crack=1.0), c=Z(1.15, 0.025))
    S(T(105), 'kitchen', 'pantry', st=dict(KIT_N, pantry_light=0.5, crack=1.0),
      ppl=[P('sam_pj', 'crack_lean', face=(6.0, 9.42), id='sam', expr='fear', act=_A(lambda a, s: a.head_to(T(105) + 0.2, scr(s.sp, 'crack', 0, 45), 'eye_l', dur=0.8)))],
      c=ZO(1.5, 'crack', ody=60))
    # 106-109 An eye leaned in on the other side. A heavy, droopy, sad eye. In a face made of rubber. It blinked.
    PR(T(106), 'crack', open=1.0, shelf=False, layers=[EYE(985, 520, 9.0, WD(106, 'eye') - 0.1, clip=crack_poly(1.0), lean=80.0)], hit=WD(106, 'eye'),
       c=dict(mv='push', rate=0.03))
    PR(T(107), 'crack', open=1.9, shelf=False, layers=[EYE(985, 540, 15.0, T(107) - 0.8, clip=crack_poly(1.9))], c=dict(mv='push', f=1.1, rate=0.02))
    PR(T(108), 'crack', open=3.2, shelf=False, layers=[EYE(1000, 520, 6.5, T(108) - 0.8, clip=crack_poly(3.2), part='eye_l', yaw=0.35)],
       c=dict(mv='push', rate=0.015))
    PR(T(109), 'crack', open=1.9, shelf=False, layers=[EYE(985, 540, 15.0, T(109) - 0.8, clip=crack_poly(1.9), blinks_=(WD(109, 'blinked') + 0.05,))],
       c=dict(mv='push', f=1.15, rate=0.01), sfx=[(WD(109, 'blinked') + 0.05, 'eyelid_click', -12, 0, 'close')])
    PR(T(110), 'crack', open=1.0, shelf=False, layers=[EYE(985, 520, 9.0, T(110) - 3, t_out=T(110) + 0.2, clip=crack_poly(1.0))], c=dict(mv='push', rate=0.02))
    tcw = W(110, 'something')
    WL(tcw, 'chase', [WP('pell', 200, dy=-4.0, act=_A(lambda a, s: a.crawl(tcw + 0.1, W(110, 'up') + 0.2, -150, 2050, facing=1)))], seed=1,
       sfx=[(tcw + 0.15, 'scuttle', -6, 0.3, 'wall', dict(dur=round(W(110, 'up') - tcw, 2)))], c=dict(mv='hold'))
    S(W(110, 'up'), 'kitchen', 'wide', st=KIT_N, c=Z(1.0, 0.03, 1000, 420), sfx=[(WD(110, 'ceiling'), 'attic_crawl', -10, 0, 'wall')])
    # 111-113 I told Dad. Dad said I was dreaming. The note said mice.
    S(T(111), 'kitchen', 'wide', st=KIT_D, cam=KCAM, ppl=[P('sam', (2.5, 7.7, 0.0), face=(3.5, 8.5), id='sam', expr='pleading', act=_A(lk(T(111), ('dad', 'head')))),
                                               P('dad_tee', (3.5, 8.5, 0.0), face=(2.5, 7.7), id='dad', expr='tired_kind')], c=Z(1.05, 0.012))
    BU(T(112), 'dad_tee', 'kitchen', 'wide', KIT_D, cx=960, cy=600, scale=0.92, h_turn=0.3, expr='tired_kind', light=DAY,
       act=_A(lambda a, s: a.sigh(T(112) + 0.1, 1.2), lookxy(500, 640, T(112))), c=BZ(0.015))
    IN(T(113), 'note', dict(hl=4), c=dict(mv='push', f=1.15, rate=0.02))


def plan_rule3(F):
    RULE(T(114), 3)
    S(T(116), 'living', 'chair', st=MORN, c=ZO(1.2, 'armchair', ody=-120))
    S(T(117), 'living', 'chair', st=MORN, cam=CHAIRCAM, ppl=[P('sam', (-3.0, 2.62, 0.0), face='armchair', id='sam', expr='suspicious',
                                                act=_A(reach(T(117) + 0.3, 1, (-3.38, 2.98, 0.5), t1=E(117) + 0.5, dur=0.5, shape='flat', contact='palm')))],
      c=Z(1.0, 0.012))
    # 118 Warm like someone had just stood up.  (he rises out of the chair in the dark and folds himself away)
    S(T(118), 'living', 'wide', st=dict(), cam=CHAIRFRONT, ppl=[P('pell', 'armchair', id='pell', stand_t=T(118) + 0.4, act=_A(tilt(T(118) - 0.4, 10, 0.8)))],
      c=Z(1.0, 0.01))
    # 119 "Vent's right under it,"
    S(T(119), 'living', 'wide', st=MORN, cam=MC((-3.0, 2.6, 0.0), 120, 2.3), ppl=[P('dad_tee', 'chair_front', face=(-1.2, 1.5), id='dad', expr='talk_smile',
                                               act=_A(lambda a, s: a.point(T(119) + 0.1, E(119) + 0.4, 1, -0.3, 0.8)))], c=Z(1.0, 0.012))
    S(T(120), 'living', 'window', st=MORN, c=Z(1.2, 0.02))
    S(T(121), 'living', 'vent', st=MORN, c=Z(1.1, 0.02))
    # 122-123 I lifted the seat cushion. Under it, folded very small, were Theo's drawings.
    S(T(122), 'living', 'chair', st=MORN, cam=CHAIRCAM, ppl=[P('sam', (-3.0, 2.62, 0.0), face='armchair', id='sam', expr='focused',
                                                act=_A(reach(T(122) + 0.2, 1, (-3.35, 2.92, 0.52), t1=E(122) + 1.0, dur=0.45, shape='grip'),
                                                       reach(T(122) + 0.3, -1, (-3.42, 3.05, 0.52), t1=E(122) + 1.0, dur=0.45, shape='grip')))],
      c=Z(1.05, 0.012))
    IN(T(123), 'drawings', dict(state='folded'), c=dict(mv='push', rate=0.03))
    # 124-126 The ones that kept falling off the fridge. We never found them. We thought Theo lost them.
    S(T(124), 'kitchen', 'wide', st=KIT_D, cam=KCAM, ppl=[P('theo', (2.5, 7.75, 0.0), face='fridge', id='theo', expr='sad', act=_A(lk(T(124), 'fridge')))], c=ZO(1.4, (2.4, 8.1, 0.0), h=0.8))
    BU(T(125), 'theo', 'kitchen', 'wide', KIT_D, cx=960, cy=620, scale=0.95, h_turn=0.25, expr='sad', light=DAY, act=_A(lookxy(900, 860, T(125))), c=BZ(0.015))
    BU(T(126), 'mom', 'kitchen', 'wide', KIT_D, cx=960, cy=600, scale=0.9, h_turn=-0.3, expr='kind_smile', light=DAY, act=_A(lookxy(500, 800, T(126))), c=BZ(0.015))
    # 127-129 Every drawing was the same. A tall man, inside a wall, with a sad dog face. In a red shirt.
    IN(T(127), 'drawings', dict(state='spread'), c=dict(mv='push', rate=0.02))
    IN(T(128), 'drawings', dict(state='spread'), c=dict(mv='push', f=1.6, rate=0.03, x=820, y=480))
    WL(T(129), 'wall', [WP('pell', 960, h=900, turn=0.15, h_turn=0.3, act=_A(tilt(T(129) + 0.1, 12, 1.0)))], slits=[(600, 240, 800, 1.0)], c=ZO(1.5, '@pell', part='chest', ody=-60))
    # 130-131 Somebody had been taking them down. So that we would never see all of them together.
    S(T(130), 'kitchen', 'wide', st=dict(KIT_N, kitchen_light=0.0), cam=KCAM, ppl=[P('pell', (2.45, 7.9, 0.0), face='fridge', id='pell', light=NL,
                                                                                   act=_A(reach(T(130) + 0.3, -1, (2.2, 8.75, 1.4), t1=E(130) + 0.5, dur=0.6, shape='grip')))],
      c=ZO(1.3, (2.4, 8.1, 0.0), h=1.0))
    S(T(131), 'living', 'chair', st=dict(), cam=CHAIRCAM, ppl=[P('pell', 'chair_front', kind='kneel', face='armchair', id='pell',
                                                   act=_A(reach(T(131) + 0.3, 1, 'chair_seat', t1=E(131) + 0.4, dur=0.6, shape='flat'), tilt(pdur(131, 0.6), 12, 1.0)))],
      c=Z(1.05, 0.012))


def plan_rule4(F):
    RULE(T(132), 4)
    IN(T(135), 'switch', dict(on=0), c=dict(mv='push', rate=0.03))
    # 136-142 Mrs. Dabrowski and her pie; "Your attic light's on every night," "Right around two." / "We don't have an attic light," "It's sealed."
    PD = [P('mom', (0.85, -0.45, 0.0), turn=-0.4, id='mom', expr='polite'),
          P('dabrowski', (0.2, -1.25, 0.0), turn=0.35, id='dab', expr='kind_smile', act=_A(lambda a, s: a.offer_pie(T(136) + 0.6, 0.9, facing=1)))]
    S(T(136), 'street', 'porch', st=DAYS, ppl=PD, c=ZO(2.1, (0.55, -0.85, 0.0), h=1.1))
    BU(T(137), 'dabrowski', 'street', 'porch', DAYS, cx=960, cy=600, scale=0.9, h_turn=-0.3, expr='kind_smile', light=DAY, c=BZ(0.015))
    BU(T(138), 'dabrowski', 'street', 'porch', DAYS, cx=920, cy=600, scale=0.95, h_turn=-0.15, expr='suspicious', light=DAY,
       act=_A(lookxy(1500, 420, T(138) + 0.15, dur=0.3)), c=BZ(0.02))
    BU(T(139), 'dabrowski', 'street', 'porch', DAYS, cx=960, cy=600, scale=0.92, h_turn=-0.3, expr='talk_smile', light=DAY, c=BZ(0.015))
    S(T(140), 'street', 'house', st=dict(attic=1.0), c=ZO(2.2, 'attic_window', ody=60))
    BU(T(141), 'mom', 'street', 'porch', DAYS, cx=960, cy=600, scale=0.92, h_turn=0.3, expr='polite', light=DAY, c=BZ(0.015))
    # 143-147 two a.m.: the switch that does nothing; the line of light; the voice in the ceiling: "Off."
    tf = W(143, 'flipped') + 0.1
    S(T(143), 'hall', 'down', st=HALL_N, ppl=[P('sam_pj', 'switch_stand', face='switch', id='sam', expr='nervous')], c=ZO(2.2, 'switch_stand', h=1.0))
    S(W(143, 'flipped'), 'hall', 'switch', st=dict(HALL_N, switch=lambda t: 1.0 if t >= tf + 0.25 else 0.0),
      ppl=[P('sam_pj', 'switch_stand', face='switch', id='sam', expr='nervous', act=_A(lambda a, s: a.flip_switch(tf, 1, scr(s.sp, 'switch'))))],
      c=ZO(1.7, 'switch_stand', h=1.1), sfx=[(tf + 0.25, 'light_switch', -8, 0, 'inside')])
    ton = WD(144, 'light')
    S(T(144), 'hall', 'switch', st=dict(HALL_N, switch=1.0, attic=lambda t: clamp((t - ton) / 0.3)),
      ppl=[P('sam_pj', 'switch_stand', face='switch', id='sam', expr='fear', act=_A(lk(T(144) + 0.4, 'ceiling', dur=0.7), lk(ton + 0.1, 'closet_door', dur=0.4)))],
      c=Z(1.1, 0.015))
    S(T(145), 'hall', 'closet', st=dict(HALL_N, switch=1.0, attic=1.0), c=Z(1.1, 0.02))
    S(W(145, 'hatch'), 'hall', 'hatch', st=dict(HALL_N, switch=1.0, attic=1.0), c=Z(1.1, 0.02))
    BU(T(146), 'sam_pj', 'hall', 'down', dict(HALL_N, attic=1.0), cx=960, cy=640, scale=0.95, h_turn=0.15, expr='fear', light=ATTIC,
       act=_A(lookxy(960, 0, T(146) + 0.3, dur=0.8)), c=BZ(0.02))
    WL(T(147) - 0.25, 'attic', [WP('pell', 960, h=900, turn=0.1, h_turn=0.3, light=ATTIC, act=_A(lambda a, s: a.crouch(T(147) - 2, 1.0), tilt(T(147) - 0.2, 10, 1.0)))],
       hatch=1.0, c=ZO(1.8, '@pell', part='head', ody=60), hit=WD(147, 'off') + 0.05)
    # 148-152 I wanted to open that closet so badly. Rule four. Not alone. Not at night. I didn't open it.
    S(T(148), 'hall', 'closet', st=dict(HALL_N, switch=1.0, attic=1.0), ppl=[P('sam_pj', (0.15, 5.5, 2.9), face='closet_door', id='sam', expr='nervous',
                                                                                act=_A(reach(T(148) + 0.5, 1, (0.79, 5.75, 3.85), t1=E(148), dur=1.0, shape='grip')))],
      c=Z(1.2, 0.015))
    IN(T(149), 'rules', dict(show=6, hl=4, seven=0.0), c=dict(mv='push', f=1.2, rate=0.02, x=960, y=600))
    BU(T(152), 'sam_pj', 'hall', 'closet', dict(HALL_N, switch=1.0, attic=1.0), cx=960, cy=620, scale=0.95, h_turn=-0.2, expr='set_jaw', light=ATTIC, c=BZ(0.015))
    # 153-155 I flipped the switch off. I walked, I did not run, to my parents' room, and I told my dad everything. "Old wiring, Sam."
    toff = T(153) + 0.45
    S(T(153), 'hall', 'switch', st=dict(HALL_N, switch=lambda t: 0.0 if t >= toff + 0.25 else 1.0, attic=lambda t: 0.0 if t >= toff + 0.25 else 1.0),
      ppl=[P('sam_pj', 'switch_stand', face='switch', id='sam', expr='set_jaw', act=_A(lambda a, s: a.flip_switch(toff, 1, scr(s.sp, 'switch'))))],
      c=ZO(1.7, 'switch_stand', h=1.1), sfx=[(toff + 0.25, 'light_switch', -8, 0, 'inside')])
    S(T(154), 'hall', 'back', st=HALL_N, ppl=[P('sam_pj', (0.1, 7.6, 2.9), id='sam', expr='set_jaw', path=[(T(154), (-0.05, 5.2, 2.9)), (W(154, 'told') - 0.2, (0.0, 7.55, 2.9))])],
      c=ZO(1.5, (0.0, 7.0, 2.9), h=1.0))
    S(W(154, 'told'), 'parents', 'bed', st=dict(PAR_N, lamp=0.4), ppl=[P('dad_pj', 'bed_dad', kind='lie', expr='sleepy', id='dad'),
                                                                     P('sam_pj', (-5.2, 5.65, 2.9), face='bed_dad', id='sam', expr='pleading')],
      c=ZO(1.4, 'bed_dad', ody=-80))
    BU(T(155), 'dad_pj', 'parents', 'bed', dict(PAR_N, lamp=0.4), rot=90, cx=960, cy=560, scale=0.9, expr='sleepy', light=LAMP,
       act=_A(lambda a, s: a.sigh(T(155) - 0.3, 1.0)), c=BZ(0.015))


def plan_rule5(F):
    RULE(T(156), 5)
    # 159-165 Theo's song: fifty times a day; in the bath; at dinner; in his sleep; it drove us crazy
    BU(T(159), 'theo', 'living', 'wide', MORN, cx=960, cy=620, scale=0.95, h_turn=0.25, expr='kid_grin', light=MORNING, c=BZ(0.015))
    S(T(160), 'living', 'wide', st=MORN, cam=MC((-2.5, 1.8, 0.0), 75, 1.8, h=1.2, lh=0.7), ppl=[P('theo', 'room_mid', id='theo', expr='kid_grin',
                                               path=[(T(160), (-2.0, 1.9, 0.0)), (pdur(160, 0.5), (-2.9, 2.0, 0.0)), (E(160), (-2.4, 1.4, 0.0))])],
      acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['theo']: a.where(t, 'mouth'), T(160), E(160), c='#ffe8a0')], c=Z(1.0, 0.012))
    BU(W(160, 'that'), 'theo', 'living', 'wide', MORN, cx=960, cy=620, scale=0.95, h_turn=-0.2, expr='kid_grin', light=MORNING, c=BZ(0.015))
    BU(T(161), 'sam', 'living', 'wide', MORN, cx=960, cy=600, scale=0.92, h_turn=0.3, expr='grumpy', light=MORNING, act=_A(blinks(T(161) + 0.6)), c=BZ(0.015))
    BU(T(162), 'theo', None, None, plain=('#7ab0c8', '#3a6a86'), cx=960, cy=620, scale=0.95, h_turn=0.15, expr='kid_grin', light=DAY, act=_A(hum(T(162), E(162))),
       acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['theo']: a.where(t, 'mouth'), T(162), E(162), c='#ffffff')], c=BZ(0.015))
    S(T(163), 'kitchen', 'wide', st=dict(kitchen_light=1.0, bolt=1.0), cam=MC((3.3, 6.4, 0.0), 250, 1.8, h=1.3, lh=0.7),
      ppl=[P('theo', 'table_s', id='theo', expr='kid_grin', act=_A(hum(T(163), E(163) + 0.3))), P('mom', 'table_n', id='mom', expr='tired_kind')],
      acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['theo']: a.where(t, 'mouth'), T(163), E(163), c='#ffe8a0')], c=Z(1.0, 0.012))
    lie_bust(T(164), 'theo', 'sleep', act=_A(hum(T(164), E(164) + 0.3)), bg=('boys', 'theo', B_NIGHT),
             acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['theo']: a.where(t, 'mouth'), T(164), E(164), c='#c8d8ff')])
    BU(T(165), 'sam', 'living', 'wide', MORN, cx=960, cy=600, scale=0.92, h_turn=-0.3, expr='grumpy', light=MORNING,
       act=_A(lambda a, s: a.hand_over(T(165) + 0.1, 1, a, part='eyes', t1=E(165) + 0.5)), c=BZ(0.015))
    # 166-172 That night, through the wall by my bed: not Theo's voice. A man's. Slow. Low. Wrong. "Fourteen Larkspur Lane... that's my house."
    S(T(166), 'boys', 'sam_wall', st=BL, ppl=[sam_bed('neutral', act=_A(lk(pdur(166, 0.5), 'sam_wall', dur=0.8)))],
      acts=lambda A, sh, sp: [notes_layer(lambda t, sp=sp: scr(sp, 'sam_wall', 0, -40), pdur(166, 0.5), E(166) + 0.3, c='#c8d8ff', a=120)], c=ZO(1.6, 'sam_pillow'))
    lie_bust(T(167), 'sam_pj', 'fear', act=_A(lookxy(1600, 300, T(167) + 0.2)))
    sing = lambda i: WP('pell', 960, h=900, turn=-0.2, h_turn=-0.35, act=_A(lambda a, s: a.head_to(T(i) - 0.3, (700, 300), 'mouth', dur=1.0), tilt(T(i), 14, 1.4)))
    WL(T(168), 'wall', [sing(168)], slits=[(700, 200, 760, 0.8)], c=ZO(1.7, '@pell', part='head', ody=80))
    lie_bust(T(169), 'sam_pj', 'fear', act=_A(lookxy(1600, 300, T(169))), cx=1000, scale=1.05)
    WL(T(170), 'wall', [sing(170)], slits=[(700, 200, 760, 0.8)], c=ZO(2.4, '@pell', part='head', ody=40))
    lie_bust(T(171), 'sam_pj', 'terror', act=_A(lookxy(1600, 300, T(171))), cx=980, scale=1.15)
    WL(T(172), 'wall', [sing(172)], slits=[(700, 200, 760, 0.8)], c=ZO(1.9, '@pell', part='head', ody=70),
       acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['pell']: a.where(t, 'mouth'), T(172), E(172), c='#a8b8e8', slow=0.6)])
    S(W(172, 'that'), 'boys', 'sam_wall', st=BL, ppl=[sam_bed('terror', act=_A(lk(T(172), 'sam_wall')))],
      acts=lambda A, sh, sp: [notes_layer(lambda t, sp=sp: scr(sp, 'sam_wall', 0, -40), W(172, 'that'), E(172) + 0.4, c='#a8b8e8', a=150, slow=0.6)],
      c=ZO(1.7, 'sam_pillow', ody=-20))
    # 173-176 Then the knocking started. And the voice in the wall started talking. And it said things I had heard before.
    kn = [WD(173, 'knocking') + 0.1 + 0.32 * k for k in range(3)]
    S(T(173), 'boys', 'sam_wall', st=BL, ppl=[sam_bed('terror', act=_A(*[lambda a, s, tk=tk: a.flinch(tk, 0.6) for tk in kn]))],
      c=dict(mv='push', f=1.6, rate=0.01, on='sam_pillow', hit=[(tk, 3.0) for tk in kn]), sfx=[(tk, 'knock_door', -6, 0.4, 'wall', dict(n=1)) for tk in kn])
    WL(T(174), 'wall', [WP('pell', 960, h=900, turn=-0.2, h_turn=-0.3, act=_A(tilt(T(174), 16, 1.6)))], slits=[(700, 200, 760, 0.8)], c=ZO(2.0, '@pell', part='head', ody=70))
    lie_bust(T(175), 'sam_pj', 'fear', act=_A(lookxy(1600, 300, T(175))))
    WL(T(176), 'wall', [WP('pell', 960, h=900, turn=-0.2, h_turn=-0.35, act=_A(lambda a, s: a.head_to(T(176) - 0.3, (700, 300), 'mouth', dur=1.0)))],
       slits=[(700, 200, 760, 0.8)], c=ZO(2.0, '@pell', part='head', ody=70, rate=0.008))
    S(W(176, "it's"), 'boys', 'sam_wall', st=BL, ppl=[sam_bed('terror')],
      c=ZO(1.9, 'sam_pillow', ody=-10))
    WL(W(176, 'go'), 'wall', [WP('pell', 960, h=900, turn=-0.2, h_turn=-0.35, act=_A(lambda a, s: a.head_to(W(176, 'go') - 0.5, (700, 300), 'mouth', dur=0.4),
                                                                                         lambda a, s: a.shush(W(176, 'sleep'), None, side=1)))],
       slits=[(700, 200, 760, 0.8)], c=ZO(2.4, '@pell', part='head', ody=60))
    # 177-182 It wasn't Dad's voice. They were Dad's words. No. They were the note's words. ... By the man who wanted us to have an excuse for every sign he left.
    lie_bust(T(177), 'sam_pj', 'haunted', act=_A(blinks(T(177) + 0.6)))
    BU(T(178), 'dad_tee', 'kitchen', 'wide', KIT_D, era='memory', cx=960, cy=600, scale=0.92, h_turn=0.3, expr='talk_smile', light=DAY, c=BZ(0.015))
    IN(T(179), 'note', dict(hl=None), c=dict(mv='push', rate=0.03))
    IN(T(180), 'note', lambda u, t0=T(180): dict(hl=2 + min(4, int((u) / 0.3))), c=dict(mv='push', f=1.1, rate=0.02))
    IN(T(181), 'note', dict(hl=None), grade='wl_ins_night', c=dict(mv='push', f=1.05, rate=0.025),
       hands=[dict(who='pell', fn=lambda t, t0=T(181): (1240 + 120 * math.sin((t - t0) * 1.3), 700 + 30 * math.sin((t - t0) * 5.1), -40.0, 1.0), size=420.0,
                   shape='grip', side=1, sleeve_from=(1900, 1300), pen=True)], sfx=[(T(181) + 0.3, 'pen_scratch', -12, 0, 'close', dict(dur=3.5))])
    WL(T(182), 'wall', [WP('pell', 960, turn=0.4, h_turn=0.35, act=_A(tilt(T(182) + 0.3, 18, 1.8)))], slits=[(1250, 220, 760, 1.0)], c=Z(1.5, 0.02, 960, 420))


def plan_rule6(F):
    RULE(T(183), 6)
    # 186-191 three a.m.: "Dad" in the doorway again (the same tilt)
    lie_bust(T(186), 'sam_pj', 'neutral', act=_A(blinks(T(186) + 0.4), lookxy(400, 300, pdur(186, 0.6), dur=0.5)))
    S(T(187), 'boys', 'door_pov', st=BLH, ppl=[door_pell()], c=ZO(2.6, '@pell', part='chest'))
    S(T(188), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[door_pell(sil=0.5)], c=Z(1.6, 0.01, 930, 660))
    S(T(189), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[door_pell(sil=0.85)], c=Z(2.6, 0.01, 930, 420))
    S(T(190), 'boys', 'theo', st=BL, ppl=[theo_bed()], c=ZO(2.4, 'theo_pillow', h=0.2))
    lie_bust(T(191), 'sam_pj', 'sleepy', act=_A(lookxy(300, 300, T(191)), pose(pdur(191, 0.3), pdur(191, 0.7), 0.2, m_open=0.12)), no_lip=True)
    # 192-193 from down the hall, through my parents' open door... I heard my dad snore.
    S(T(192), 'hall', 'down', st=HALL_N, c=ZO(1.6, 'par_door', ody=-150, rate=0.02))
    S(T(193), 'parents', 'bed', st=PAR_N, ppl=[P('dad_pj', 'bed_dad', kind='lie', expr='sleep', act=_A(pose(T(193) - 1, None, 0.3, m_open=0.18))),
                                               P('mom_pj', 'bed_mom', kind='lie', expr='sleep')], c=ZO(1.7, 'bed_dad', ody=-40),
      sfx=[(WD(193, 'snore'), 'snore', -10, 0, 'inside')], hit=E(193) + 0.05, no_lip=True)
    # 194 The man in the doorway stepped into our room.
    S(T(194), 'boys', 'doorway', st=BLH, cam=DOOR_CAM, ppl=[P('pell', 'doorway', face='sam_pillow', id='pell', sil=0.0, path=[(T(194) + 0.2, 'doorway'), (E(194), (1.6, 3.6, 2.9))],
                                                   surface='inside_quiet', act=_A(sil_door()))], c=Z(1.1, 0.01, 960, 560))
    # 195-200 The moonlight hit his face. Long droopy ears. Heavy sad eyes. A wet black rubber nose. A mouth that wasn't rubber. Human teeth.
    mlt = lambda t: dict(NIGHT, rim_a=int(40 + 120 * clamp((t - T(195) - 0.3) / 1.0)), key=-0.5 + 0.3 * clamp((t - T(195) - 0.3) / 1.0))
    BU(T(195), 'pell', 'boys', 'doorway', B_NIGHT, cx=960, cy=560, scale=0.95, h_turn=0.35, light=mlt, c=BZ(0.02))
    BU(T(196), 'pell', 'boys', 'doorway', B_NIGHT, cx=1100, cy=640, scale=1.35, h_turn=0.45, light=NIGHT, act=_A(tilt(T(196), 12, 1.0)), c=BZ(0.02))
    BU(T(197), 'pell', 'boys', 'doorway', B_NIGHT, cx=960, cy=720, scale=2.0, h_turn=0.3, light=NIGHT, act=_A(blinks(pdur(197, 0.6))), c=BZ(0.015))
    BU(T(198), 'pell', 'boys', 'doorway', B_NIGHT, cx=900, cy=420, scale=1.9, h_turn=0.35, light=NIGHT, c=BZ(0.015))
    BU(T(199), 'pell', 'boys', 'doorway', B_NIGHT, cx=920, cy=380, scale=1.7, h_turn=0.3, light=NIGHT, c=BZ(0.015))
    BU(T(200), 'pell', 'boys', 'doorway', B_NIGHT, cx=900, cy=300, scale=2.1, h_turn=0.3, light=NIGHT, act=_A(pose(T(200), E(200) + 0.4, 0.25, m_open=0.38)),
       c=BZ(0.015), hit=WD(200, 'teeth') + 0.05, no_lip=True)
    # 201-204 He knelt down beside Theo's bed. And he tucked Theo in. Gently. Like he'd done it a hundred times.
    tk = T(201) + 0.4
    PK = lambda **k: P('pell', 'theo_kneel', face='theo_pillow', id='pell', **k)
    S(T(201), 'boys', 'theo', st=BL, ppl=[theo_bed(), PK(kind='kneel', knees=1)], c=ZO(1.5, 'theo_kneel', h=0.8))
    tt_ = T(202) + 0.2
    S(T(202), 'boys', 'theo', st=BL, ppl=[theo_bed(), PK(snap=True, act=_A(lambda a, s: a.tuck_blanket(tt_, scr(s.sp, (1.75, 0.6, 3.45)), scr(s.sp, (1.75, 1.25, 3.45)), dur=2.2, knees=1)))],
      c=ZO(1.7, (1.9, 0.8, 2.9), h=0.6), sfx=[(tt_ + 0.4, 'cloth_rustle', -14, 0, 'inside')])
    lie_bust(T(203), 'theo', 'sleep', bg=('boys', 'theo', B_NIGHT), rot=-90,
             hands=[dict(who='pell', fn=lambda t, t0=T(203): (1150 + 60 * math.sin((t - t0) * 1.6), 760, -100.0, 1.0), size=380.0, shape='flat', side=-1, sleeve_from=(1900, 1100))])
    BU(T(204), 'pell', 'boys', 'theo', B_NIGHT, cx=960, cy=560, scale=1.05, h_turn=-0.4, light=NIGHT, act=_A(tilt(T(204) + 0.1, 16, 1.6), lookxy(500, 900, T(204))), c=BZ(0.015))
    # 205 "Hush-a-bye,"  206 Then the dog face turned, very slowly, toward me.
    BU(T(205), 'pell', 'boys', 'theo', B_NIGHT, cx=960, cy=560, scale=1.2, h_turn=-0.4, light=NIGHT, act=_A(lookxy(500, 900, T(205) - 1)), c=BZ(0.012))
    BU(T(206), 'pell', 'boys', 'theo', B_NIGHT, cx=960, cy=560, scale=1.1, h_turn=-0.45, light=NIGHT,
       act=_A(pose(W(206, 'turned'), E(206), 1.8, h_turn=0.12), lookxy(960, 560, W(206, 'turned'), dur=2.0)), c=BZ(0.02))
    # 207-208 And he lifted one finger to where his lips should be. "Shhh. Just the pipes."
    BU(T(207), 'pell', 'boys', 'theo', B_NIGHT, cx=960, cy=560, scale=1.1, h_turn=0.15, light=NIGHT, act=_A(lambda a, s: a.shush(W(207, 'lifted'), None, side=1)), c=BZ(0.015))
    BU(T(208), 'pell', 'boys', 'theo', B_NIGHT, cx=960, cy=560, scale=1.15, h_turn=0.15, light=NIGHT, act=_A(lambda a, s: a.shush(T(208) - 1, None, side=1)), c=BZ(0.012))
    # 209-211 He stood up, and he went into my closet. I heard the back wall of my closet slide. Then nothing.
    S(T(209), 'boys', 'closets', st=dict(BL, sam_closet=lambda t: 95.0 * ease_in_out(clamp((t - W(209, 'went')) / 0.6))),
      ppl=[P('pell', (2.9, 3.2, 2.9), id='pell', path=[(T(209) + 0.2, (2.9, 3.0, 2.9)), (W(209, 'closet') - 0.2, (4.1, 4.3, 2.9)), (E(209) + 0.3, 'sam_closet_in')],
             surface='inside_quiet')], c=ZO(1.5, (3.6, 3.8, 2.9), h=1.0))
    S(T(210), 'boys', 'closet_sam', st=dict(B_NIGHT, sam_closet=95.0, slide=lambda t: ease_in_out(clamp((t - T(210) - 0.4) / 1.4))), c=Z(1.2, 0.02),
      sfx=[(T(210) + 0.4, 'glass_slide', -10, 0, 'wall', dict(wood=True, dur=1.4))])
    S(T(211), 'boys', 'closet_sam', st=dict(B_NIGHT, sam_closet=95.0, slide=0.0), c=Z(1.3, 0.01))
    # 212-214 I did not scream. I did not follow him. I didn't look for him.
    BU(T(212), 'sam_pj', 'boys', 'sam_wall', B_NIGHT, cx=960, cy=600, scale=0.95, h_turn=0.3, expr='hush_fear', light=NIGHT,
       act=_A(lambda a, s: a.hand_over(T(212), 1, a, part='mouth', t1=E(212) + 0.3)), c=BZ(0.015))
    S(T(213), 'boys', 'closets', st=dict(B_NIGHT, sam_closet=95.0), c=ZO(1.6, 'sam_closet', ody=-200, rate=0.01))
    BU(T(214), 'sam_pj', 'boys', 'wide', B_NIGHT, cx=960, cy=620, scale=0.95, h_turn=-0.35, expr='set_jaw', light=NIGHT, act=_A(lookxy(300, 600, T(214) + 0.3)), c=BZ(0.015))
    # 215 I picked Theo up, blanket and all, with my hand over his mouth, and I walked down that hall, past the closet, where the door had opened just a crack.
    S(T(215), 'boys', 'theo', st=dict(B_NIGHT, theo_bed='empty'),
      cam=MC((2.1, 1.2, 2.9), 50, 2.4, h=1.3, lh=0.9), ppl=[P('sam_pj', (2.15, 1.05, 2.9), face=(3.5, 2.4), id='sam', expr='hush_fear', hush=dict(who='theo', t0=T(215) + 0.3, expr='sleepy'))],
      c=Z(1.0, 0.01))
    S(W(215, 'walked'), 'hall', 'down', st=dict(HALL_N, closet=7.0), ppl=[P('sam_pj', (0.45, 4.0, 2.9), id='sam', expr='hush_fear', hush=dict(who='theo'),
                                                                                path=[(W(215, 'walked'), (0.45, 4.1, 2.9)), (E(216), (0.0, 6.9, 2.9))], surface='inside_quiet')],
      c=Z(1.2, 0.01))
    S(W(215, 'closet'), 'hall', 'closet', st=dict(HALL_N, closet=7.0), c=ZO(1.5, 'closet_door', ody=-40, rate=0.02))
    # 216 Just enough to watch me go.  (his eye in the crack of the closet door)
    PR(T(216), 'doorgap', open=1.8, shelf=False, layers=[EYE(985, 470, 10.0, T(216) + 0.1, clip=(940, -500, 90, 2080), light=NL)], hit=T(216) + 0.4,
       c=dict(mv='push', rate=0.03))
    BU(T(217), 'sam_pj', 'hall', 'back', HALL_N, cx=960, cy=620, scale=0.95, h_turn=0.05, expr='hush_fear', light=NL, c=BZ(0.02))
    S(T(218), 'hall', 'back', st=dict(HALL_N, closet=7.0), ppl=[P('sam_pj', (0.1, 7.6, 2.9), id='sam', expr='hush_fear', hush=dict(who='theo'),
                                                                   path=[(T(218), (0.05, 6.6, 2.9)), (E(218) + 0.3, (0.0, 7.6, 2.9))], surface='inside_quiet')], c=Z(1.15, 0.01))
    # 219-220 Mom and Dad's door. I slipped in, shut it, locked it, and shook my dad awake.
    S(T(219), 'parents', 'door', st=dict(PAR_N, door=lambda t: 70.0 if t < W(220, 'shut') else 70.0 * (1 - ease_in_out(clamp((t - W(220, 'shut')) / 0.4))),
                                         lock=lambda t: 1.0 if t >= WD(220, 'locked') + 0.1 else 0.0),
      ppl=[P('sam_pj', (-1.4, 7.1, 2.9), id='sam', expr='hush_fear', hush=dict(who='theo'), path=[(T(219), (-0.9, 7.25, 2.9)), (W(220, 'slipped') + 0.4, (-1.6, 7.0, 2.9))])],
      c=ZO(1.2, 'lock', ody=100), sfx=[(WD(220, 'shut') + 0.3, 'door_close', -10, 0, 'inside', dict(soft=True)), (WD(220, 'locked') + 0.1, 'lock_turn', -8, 0, 'inside')])
    ts_ = W(220, 'shook')
    S(ts_, 'parents', 'bed', st=PAR_N, ppl=[P('dad_pj', 'bed_dad', kind='lie', expr='sleep', id='dad', act=_A(ex('shock', E(220) + 0.4, None, 0.3))),
                                            P('sam_pj', (-5.2, 5.65, 2.9), face='bed_dad', id='sam', expr='hush_fear', act=_A(lambda a, s: a.shake_awake(ts_ + 0.1, E(220) + 0.6, s.A['dad'])))],
      c=ZO(1.5, 'bed_dad', ody=-60))
    # 221-223 "Sam, it's just the..." / "Dad," "Your shirt is upstairs. He's wearing it."
    BU(T(221), 'dad_pj', 'parents', 'bed', PAR_N, rot=90, cx=960, cy=560, scale=0.92, expr='sleepy', light=NIGHT, c=BZ(0.015))
    BU(T(222), 'sam_pj', 'parents', 'bed', PAR_N, cx=960, cy=620, scale=1.0, h_turn=0.3, expr='hush_fear', light=NIGHT, c=BZ(0.012))
    # 224-225 My dad looked at my face. And for the first time all summer, he didn't explain anything.
    BU(T(224), 'dad_pj', 'parents', 'bed', PAR_N, rot=90, cx=960, cy=560, scale=1.0, expr='shock', light=NIGHT, act=_A(blinks(T(224) + 0.4)), c=BZ(0.02))
    BU(T(225), 'dad_pj', 'parents', 'bed', PAR_N, cx=960, cy=600, scale=0.95, h_turn=-0.2, expr='resolve', light=NIGHT, c=BZ(0.015))
    # 226-233 Mom grabbed her phone and dialed nine-one-one. "What's the address of your emergency?" ... Theo could. "Fourteen Larkspur Lane..."
    PH = dict(PAR_N, phone=1.0, phone_at=(-4.4, 3.7, 7.2), door=0.0, lock=1.0)
    S(T(226), 'parents', 'bed', st=PH, ppl=[P('mom_pj', 'bed_huddle', id='mom', expr='terrified_call', act=_A(lambda a, s: a.phone_to_ear(W(226, 'dialed') + 0.6, None, side=1)))],
      c=ZO(1.9, 'bed_huddle', h=0.5))
    IN(W(226, 'dialed'), 'phone', lambda u: dict(state='dial'), c=dict(mv='push', rate=0.02), sfx=[(WD(226, 'nine'), 'dial_911', -8, 0, 'close')])
    IN(T(227), 'phone', lambda u: dict(state='call', secs=int(u)), c=dict(mv='push', rate=0.02))
    BU(T(228), 'mom_pj', 'parents', 'bed', PH, cx=960, cy=600, scale=0.95, h_turn=0.3, expr='terrified_call', light=PHONE,
       act=_A(lambda a, s: a.phone_to_ear(T(228) - 1, None, side=1), blinks(pdur(228, 0.5))), c=BZ(0.02))
    BU(T(229), 'theo', 'parents', 'bed', PH, cx=960, cy=640, scale=0.95, h_turn=-0.3, expr='determined', light=PHONE, act=_A(lookxy(1500, 500, T(229))), c=BZ(0.015))
    S(T(230), 'parents', 'bed', st=PH, cam=MC((-3.9, 6.6, 2.9), 120, 2.2, h=1.3, lh=0.7), ppl=[P('mom_pj', 'bed_huddle', id='mom', expr='terrified_call', act=_A(lambda a, s: a.phone_to(T(230) - 0.4, 1, s.A['theo']))),
                                            P('theo', (-3.8, 7.25, 2.9), face='bed_huddle', id='theo', expr='determined')],
      acts=lambda A, sh, sp: [notes_layer(lambda t, a=A['theo']: a.where(t, 'mouth'), T(230), E(231), c='#ffe8a0', a=150)], c=Z(1.0, 0.012))
    BU(T(231), 'theo', 'parents', 'bed', PH, cx=960, cy=640, scale=1.0, h_turn=-0.3, expr='determined', light=PHONE, c=BZ(0.015))
    IN(T(232), 'phone', lambda u, t0=T(232): dict(state='call', secs=int(t0 + u - T(227))), c=dict(mv='push', rate=0.015))
    S(W(233, 'officers'), 'parents', 'door', st=dict(PH, door=0.0, lock=1.0), c=ZO(1.6, 'lock', ody=40, rate=0.02))
    BU(W(233, 'stay', 0), 'mom_pj', 'parents', 'bed', PH, cx=960, cy=600, scale=0.95, h_turn=0.3, expr='resolve', light=PHONE,
       act=_A(lambda a, s: a.phone_to_ear(T(233) - 1, None, side=1)), c=BZ(0.015))
    # 234-241 So we stayed. And the man in the walls came looking for us: scratching, behind the dresser, the headboard; the vent rattles: "Hush-a-bye. That's my house."
    FAM = lambda: [P('mom_pj', 'bed_huddle', id='mom', expr='fear'), P('sam_pj', (-3.55, 7.3, 2.9), face=(-5.0, 7.0), id='sam', expr='hush_fear'),
                   P('theo', (-3.6, 6.25, 2.9), face=(-5.0, 7.0), id='theo', expr='fear'), P('dad_pj', 'room_mid', face=(-0.6, 7.2), id='dad', expr='resolve')]
    S(T(234), 'parents', 'wide', st=dict(PAR_N, door=0.0, lock=1.0), ppl=FAM(), c=Z(1.2, 0.012))
    WL(T(235), 'chase', [WP('pell', 200, dy=-4.0, act=_A(lambda a, s: a.crawl(T(235) + 0.1, E(235), -100, 2000, facing=1)))], seed=2, c=dict(mv='hold'),
       sfx=[(T(235) + 0.1, 'scuttle', -8, 0.2, 'wall', dict(dur=round(E(235) - T(235), 2)))])
    scr_ = lambda t0, n=4: [(t0 + 0.25 * k, 'scratch', -10, -0.3 + 0.2 * k, 'wall') for k in range(n)]
    S(T(236), 'parents', 'wide', st=dict(PAR_N, door=0.0, lock=1.0), ppl=[P(q['who'], q['at'], **{k_: v_ for k_, v_ in q.items() if k_ not in ('who', 'at')}) for q in FAM()],
      c=Z(1.35, 0.015, 1000, 520), sfx=scr_(T(236) + 0.2))
    WL(T(237), 'wall', [WP('pell', 960, h=900, turn=0.8, h_turn=0.3, act=_A(reach(T(237) + 0.1, 1, (1250, 430), t1=E(237) + 0.3, dur=0.3, shape='point'),
                                                                            lambda a, s: a.crouch(T(237), 0.5)))], seed=3, slits=[(1650, 260, 700, 0.8)], c=Z(1.5, 0.01, 1000, 460),
       sfx=scr_(T(237) + 0.1, 3))
    S(T(238), 'parents', 'wide', st=dict(PAR_N, door=0.0, lock=1.0), c=ZO(1.8, 'dresser', ody=40, rate=0.02), sfx=scr_(T(238) + 0.1, 3))
    S(T(239), 'parents', 'bed', st=dict(PAR_N, door=0.0, lock=1.0), ppl=[P('mom_pj', 'bed_huddle', id='mom', expr='terror', act=_A(lk(T(239) + 0.1, 'headboard', dur=0.25)))],
      c=ZO(1.5, 'headboard', ody=60), sfx=scr_(T(239) + 0.1, 3))
    rat = lambda t: 0.9 * clamp((t - WD(240, 'rattled')) / 0.2) * (1 - clamp((t - WD(240, 'rattled') - 1.6) / 0.6))
    S(T(240), 'parents', 'vent', st=dict(PAR_N, door=0.0, lock=1.0), c=Z(1.1, 0.02), sfx=[(WD(240, 'rattled'), 'vent_rattle', -6, 0, 'inside', dict(dur=1.8))])
    IN(W(240, 'through'), 'vent', dict(rattle=rat), layers=[EYE(960, 560, 9.0, W(240, 'through') + 0.4, clip=vent_gaps(), part='eye_l', yaw=0.3)],
       c=dict(mv='push', rate=0.02))
    IN(T(241), 'vent', dict(rattle=0.15), layers=[EYE(960, 560, 9.0, T(241) - 1, clip=vent_gaps(), part='mouth', yaw=0.3, talk=True)],
       c=dict(mv='push', f=1.15, rate=0.015), hit=E(241) + 0.05)


def plan_police(F):
    # 242-244 Then sirens. Blue light on the ceiling. Heavy boots on the stairs.
    S(T(242), 'street', 'house', st=dict(police=ST.wl_police(T(242)), win=dict(par=0.5)), c=Z(1.1, 0.02), sfx=[(T(242), 'sirens_arrive', -4, 0, 'outside')])
    S(T(243), 'parents', 'bed', st=dict(PAR_N, door=0.0, lock=1.0, police=True), ppl=[P('mom_pj', 'bed_huddle', id='mom', expr='relief', act=_A(lk(T(243) + 0.2, 'ceiling')))],
      c=Z(1.15, 0.015, 960, 380))
    OFF = lambda t0, **k: [P('reyes', (0.1, 3.6, 2.9), id='reyes', expr='calm_firm', path=[(t0, (0.1, 3.6, 2.9)), (t0 + 1.6, (0.15, 5.0, 2.9))], surface='heavy',
                             torch=dict(side=1, a=0.85)),
                           P('officer_w', (0.45, 3.2, 2.9), id='off', expr='focused', path=[(t0 + 0.4, (0.45, 3.2, 2.9)), (t0 + 2.0, (0.4, 4.3, 2.9))], surface='heavy')]
    S(T(244), 'hall', 'down', st=dict(HALL_N, police=True), ppl=OFF(T(244)), c=Z(1.1, 0.015))
    # 245-249 the dead space between my closet and Theo's: a sleeping bag, Dad's flashlight, our bread bags, the GONE FOREVER box. Empty.
    S(T(245), 'boys', 'closet_sam', st=dict(sam_closet=140.0, hole=True, flash=0.7, flash_at=(4.3, 4.3, 3.9), police=True), c=Z(1.2, 0.015))
    S(T(246), 'dead', 'slot', st=dict(police=True), c=Z(1.1, 0.02))
    S(T(247), 'dead', 'hole', st=dict(police=True), c=Z(1.1, 0.02))
    S(T(248), 'dead', 'slot', st=dict(police=True), c=ZO(1.8, 'sleeping_bag', ody=-30, rate=0.02))
    S(W(248, 'flashlight'), 'dead', 'slot', st=dict(police=True), c=ZO(2.2, 'flashlight', rate=0.02))
    S(W(248, 'bread'), 'dead', 'slot', st=dict(police=True), c=ZO(2.2, 'bread_bags', rate=0.02))
    S(W(248, 'box'), 'dead', 'slot', st=dict(police=True), c=ZO(2.4, 'gone_forever', ody=-20, rate=0.02))
    PR(T(249), 'box', night=True, box=dict(lid=1.0, empty=True, night=True), bg=('#1a1c24', '#07080c'), shelf=False, c=dict(mv='push', f=1.1, rate=0.03))
    # 250-253 He was wearing the mask, and my dad's red flannel shirt. Reyes pulls the mask off: a tired old man, blinking. "Lawrence Pell,"
    UN = lambda **k: [P('pell', (0.2, 5.6, 2.9), face=(0.1, 3.0), id='pell', act=_A(*k.pop('pact', ()))),
                      P('reyes', (0.35, 4.75, 2.9), face=(0.2, 5.6), id='reyes', expr='calm_firm', act=_A(*k.pop('ract', ()))),
                      P('officer_w', (-0.25, 6.1, 2.9), face=(0.2, 5.6), id='off', expr='focused')]
    S(T(250), 'hall', 'down', st=dict(HALL_N, police=True), ppl=UN(), c=ZO(2.0, (0.2, 5.4, 2.9), h=1.3))
    S(T(251), 'hall', 'down', st=dict(HALL_N, police=True), ppl=UN(ract=(lambda a, s: a.lift_mask(W(251, 'pulled'), s.A['pell'], dur=1.6),)),
      c=ZO(2.4, (0.25, 5.2, 2.9), h=1.5))
    BU(T(252), 'pell_bare', 'hall', 'down', dict(HALL_N, police=True), cx=960, cy=600, scale=1.0, h_turn=0.35, expr='exhausted', light=PHONE,
       act=_A(blinks(T(252) + 0.5, pdur(252, 0.55), pdur(252, 0.85)), lookxy(600, 400, T(252))), c=BZ(0.015))
    BU(T(253), 'reyes', 'hall', 'down', dict(HALL_N, police=True), cx=960, cy=600, scale=0.95, h_turn=-0.3, expr='calm_firm', light=POLICE, c=BZ(0.015))
    # 254-258 He never walked away. Out the front door for the movers, back in through the garage. The key under the frog. His old code. Four months.
    BU(T(254), 'pell_bare', 'hall', 'down', dict(HALL_N, police=True), cx=1000, cy=600, scale=0.95, h_turn=0.4, expr='lonely', light=POLICE, c=BZ(0.015))
    S(T(255), 'street', 'porch', st=dict(DAYS), era='memory', ppl=[P('pell_bare', 'porch_out', id='pell', sil=1.0, sil_rim='#fff0c8',
                                                                   path=[(T(255) + 0.1, 'porch_out'), (W(255, 'right') - 0.2, 'walk')], surface='porch')], c=Z(1.05, 0.015))
    S(W(255, 'right'), 'street', 'garage', st=dict(), era='memory', ppl=[P('pell_bare', 'keypad_stand', face='keypad', id='pell', sil=0.9,
                                                                              act=_A(reach(W(255, 'right') + 0.3, 1, 'keypad', t1=E(255) + 0.5, dur=0.4, shape='point')))],
      c=ZO(1.5, 'keypad_stand', ody=-200))
    IN(T(256), 'frog', lambda u: dict(lift=0.7 * ease_out_cubic(clamp((u - 0.3) / 0.5)), key=u < 0.9, tod='night'), era='memory',
       hands=[dict(who='pell', fn=slide(T(256) + 0.3, T(256) + 0.9, (1400, 1150), (1200, 860), -20.0), size=480.0, shape='grip', side=1, sleeve_from=(1900, 1500))])
    IN(T(257), 'keypad', lambda u: dict(press='4815'[min(3, int(u / 0.3))] if u < 1.2 else None), era='memory', c=dict(mv='push', rate=0.03),
       hands=[dict(who='pell', fn=slide(T(257), T(257) + 0.4, (1300, 1250), (1010, 720), -30.0), size=520.0, shape='point', side=1, sleeve_from=(1700, 1500))])
    WL(T(258), 'wall', [WP('pell', 960, turn=0.45, h_turn=0.35, food=('bread', -1, T(258) - 1), act=_A(to_mouth([T(258) + 0.3]), chew(T(258) + 0.7, E(258)),
                                                                                                  tilt(pdur(258, 0.6), 12, 1.0)))], era='memory', chew=True, c=Z(1.2, 0.012))
    # 259-261 On the way to the car, he looked up at my window. "That was my room," "When I was a boy."
    S(T(259), 'street', 'curb', st=dict(police=True), ppl=[P('pell_bare', (1.6, -7.2, -0.5), face=(0.4, -8.4), id='pell', expr='lonely',
                                                               act=_A(lk(W(259, 'looked'), (3.4, -0.02, 4.35), dur=1.0))),
                                                             P('reyes', (2.3, -7.0, -0.5), face=(1.6, -7.2), id='reyes', expr='calm_firm')], c=ZO(1.5, (1.8, -7.2, -0.5), ody=-200))
    S(W(259, 'window'), 'street', 'up', st=dict(police=True, win=dict(boys=0.4)), c=ZO(1.6, 'boys_window', ody=40, rate=0.02))
    BU(T(260), 'pell_bare', 'street', 'curb', dict(police=True), cx=960, cy=580, scale=1.0, h_turn=0.35, expr='lonely', light=POLICE,
       act=_A(lookxy(1400, 100, T(260) - 1)), c=BZ(0.012))
    BU(W(261, 'boy'), 'pell_bare', 'street', 'curb', dict(police=True), cx=1000, cy=560, scale=1.15, h_turn=0.4, expr='lonely', light=POLICE,
       act=_A(lookxy(1400, 100, T(260) - 1), blinks(E(261) - 0.1)), c=BZ(0.012))
    # 262-268 The next morning, the pencil marks on my doorframe. L, age four / eight / twelve. One more, higher than all of them. Fresh pencil. Dated last week.
    S(T(262), 'boys', 'doorframe', st=dict(MORN, marks=True, fresh=True), cam=MC((1.2, 3.4, 2.9), 120, 2.3, h=1.4, lh=1.0), ppl=[P('sam', (1.45, 3.4, 2.9), face='marks', id='sam', expr='haunted',
                                                                                 act=_A(lk(T(262) + 0.3, 'marks')))], c=Z(1.1, 0.015))
    mk = lambda y, f=1.4: dict(mv='push', f=f, rate=0.02, x=960, y=y)
    IN(T(263), 'marks', dict(fresh=1.0), c=mk(860))
    IN(T(264), 'marks', dict(fresh=1.0), c=mk(700))
    IN(T(265), 'marks', dict(fresh=1.0), c=mk(520))
    IN(T(266), 'marks', dict(fresh=1.0), c=mk(380, 1.4))
    IN(T(267), 'marks', dict(fresh=1.0), c=mk(260, 1.8))
    IN(T(268), 'marks', dict(fresh=1.0), c=mk(260, 2.3), hit=E(268) + 0.05)


def plan_rule7(F):
    RULE(T(269), 7)
    IN(T(270), 'rules', dict(show=6, hl=7, seven=0.0), c=dict(mv='push', f=1.1, rate=0.02, x=960, y=760))
    # 271-272 Theo told it to me that first night, and I didn't write it down. I said we ran out of room.
    S(T(271), 'boys', 'wide', st=dict(B_NIGHT, lamp=1.0), era='memory', cam=KIDCAM, ppl=[P('theo', (3.1, 2.0, 2.9), face=(4.3, 3.4), expr='pleading', id='theo'),
                                                                                P('sam_pj', 'sam_edge', face=(3.6, 3.3), expr='calm_smirk', id='sam', act=_A(lk(T(271), ('theo', 'head'))))],
      c=Z(1.05, 0.012))
    BU(T(272), 'sam_pj', 'boys', 'wide', dict(B_NIGHT, lamp=1.0), era='memory', cx=960, cy=600, scale=0.92, h_turn=-0.25, expr='calm_smirk', light=LAMP, c=BZ(0.015))
    # 273 Every night, Theo tapped the empty line at the bottom of the page, and I never asked him why.
    taps = [W(273, 'tapped') + 0.35 * k for k in range(3)]

    def tapfn(t):
        d = min([abs(t - tk) for tk in taps] + [9.0])
        return (1010, 815 - 30 * clamp(1 - d / 0.15), -170.0, 1.0)
    IN(T(273), 'rules', dict(show=6, hl=7, seven=0.0), c=dict(mv='push', f=1.15, rate=0.015, x=960, y=700),
       hands=[dict(who='theo', fn=tapfn, size=330.0, shape='point', side=1, sleeve_from=(1700, 1250))],
       sfx=[(tk, 'paper', -14, 0, 'close', dict(tap=True)) for tk in taps])
    IN(T(274), 'rule', dict(n=7, write=0.0), c=dict(mv='push', rate=0.02))
    IN(T(275) - 0.3, 'rule', lambda u, t0=T(275) - 0.3: dict(n=7, write=clamp((t0 + u - WD(275, 'believe') + 0.15) / 0.8)), c=dict(mv='push', rate=0.015),
       sfx=[(WD(275, 'believe'), 'pen_scratch', -10, 0, 'close', dict(dur=0.9))], music=[(WD(275, 'believe'), 'hit', 0.5)])


def plan_outro(F):
    # 276-278 Okay. Breathe. You can turn a light on now.
    S(T(276), 'living', 'wide', st=dict(lamp=lambda t: 1.0 if t >= WD(278, 'light') + 0.1 else 0.0), era='outro', c=Z(1.05, 0.01),
      sfx=[(WD(278, 'light') + 0.1, 'light_switch', -10, 0, 'inside')])
    # 279-280 None of this happened. No Larkspur Lane, no Mr. Pell, no hound mask in our garage.
    CARD(T(279), 'NONE OF THIS HAPPENED.', era='outro', size=78)
    CARD(T(280), 'LARKSPUR LANE\nMR. PELL\nTHE HOUND MASK', era='outro', size=64, y=520,
         line_t={0: WD(280, 'larkspur') - 0.2, 1: WD(280, 'pell') - 0.3, 2: WD(280, 'hound') - 0.2},
         strikes=[(WD(280, 'lane') + 0.2, 0), (WD(280, 'pell') + 0.3, 1), (WD(280, 'garage') + 0.1, 2)])
    # 281-282 someone who got up at two in the morning to check a noise... and found a fan, and felt very silly. Feeling silly is fine.
    S(T(281), 'living', 'window', st=dict(), era='outro', c=Z(1.05, 0.02))
    S(W(281, 'found'), 'living', 'window', st=dict(), era='outro', c=Z(1.6, 0.02, 960, 560))
    S(T(282), 'living', 'window', st=MORN, era='outro', c=Z(1.2, 0.015))
    # 283-284 Most noises really are the house. Stop explaining signs away.
    WL(T(283), 'wall', [], era='outro', slits=[(700, 200, 760, 0.7)], c=Z(1.2, 0.015), sfx=[(pdur(283, 0.5), 'pipe_knock', -10, 0, 'wall')])

    def strikes_note(F_, sh):
        t0 = W(284, 'stop')

        def draw(pen, t):
            cv = pen.cv; cv.save(); cv.translate(960, 540); cv.rotate(-2.0); cv.scale(0.92, 0.92)
            for j, i in enumerate(range(2, 7)):
                u = ease_out_cubic(clamp((t - t0 - 0.18 * j) / 0.3))
                if u <= 0: continue
                ln = ST.WL_NOTE_LINES[i]; wd = ST.btext_width(ln, 'hand', 58)
                pen.fill(rrect(-460, -388 + 92 * i - 24, (wd + 20) * u, 9, 4), '#d8262e', 230)
            cv.restore()
        return Layer(0.9, draw, 'strikes', blur=0)
    IN(T(284), 'note', dict(hl=None), era='outro', layers=[strikes_note], c=dict(mv='push', rate=0.012))
    # 285-295 So here's the real list.
    F.cut(T(285), 'list', era='outro')
    # 296-304 the word you left before rule two
    F.cut(T(296), 'pause', stage='return', era='outro', sfx=[(WD(301, 'person'), 'impact_hit', -6, 0, None)], music=[(WD(301, 'person'), 'hit', 0.55)])
    # 305 If this story made you go check your back door, leave a like, so I know you did.
    tl_ = W(305, 'back') + 0.3
    S(T(305), 'kitchen', 'door', st=dict(KIT_N, bolt=lambda t: ease_in_out(clamp((t - tl_) / 0.4))), era='outro', c=ZO(1.3, 'deadbolt', ody=80, rate=0.01),
      sfx=[(tl_ + 0.2, 'deadbolt', -8, 0, 'inside')],
      hud=lambda cv, t: _thumb(Pen(cv), 1500, 330, 1.1 * max(0.01, ease_out_back(clamp((t - WD(305, 'like')) / 0.35))), 255 * clamp((t - WD(305, 'like')) / 0.2)) if t >= WD(305, 'like') else None)
    # 306-308 And subscribe. On Night Policy, the next story comes to you. You'll never have to go looking for it in the walls.
    CARD(T(306), CHANNEL, era='outro', size=96, icon='sub', icon_t=WD(306, 'subscribe') - 0.1, sub='THE NEXT STORY COMES TO YOU', bg=('#1a1420', '#07080c'))
    WL(T(308), 'wall', [], era='outro', slits=[(700, 200, 760, 0.7), (1400, 260, 820, 0.6)], c=Z(1.15, 0.015))
    # 309-311 Sleep well. And if your little brother tells you something tonight... Believe him.
    S(T(309), 'boys', 'theo', st=dict(BL, lamp=0.4), era='outro', ppl=[theo_bed('sleep')], c=ZO(2.4, 'theo_pillow', h=0.2))
    S(T(310), 'boys', 'theo', st=dict(BL, lamp=0.6), era='outro',
      ppl=[theo_bed('kid_grin', act=_A(lk(T(310), ('sam', 'head')))), P('sam_pj', 'theo_kneel', kind='kneel', face='theo_pillow', id='sam', expr='tender',
                                                                         act=_A(lk(T(310) + 0.2, ('theo', 'head'))))], c=ZO(1.5, 'theo_kneel', h=0.6))
    BU(T(311), 'sam_pj', 'boys', 'theo', dict(B_NIGHT, lamp=0.6), era='outro', cx=960, cy=600, scale=0.95, h_turn=0.3, expr='warm_smile', light=LAMP,
       act=_A(pose(WD(311, 'believe') + 0.2, None, 0.4, h_nod=0.15)), c=BZ(0.012))
    IN(E(311) + 0.5, 'rule', dict(n=7, write=1.0), era='outro', c=dict(mv='push', rate=0.012))


def plan(F):
    plan_open(F); plan_moving(F); plan_night1(F); plan_prompt(F); plan_rule1(F); plan_rule2(F); plan_rule3(F)
    plan_rule4(F); plan_rule5(F); plan_rule6(F); plan_police(F); plan_rule7(F); plan_outro(F)
    plan_globals(F)


def plan_globals(F):
    """Film-wide music cues keyed to lines: Theo's address song (our motif) by version: 'theo' (sweet, his own), 'wall'
    (warped, slow and low inside the walls), 'lullaby' (ending on hush-a-bye), 'calm' (the end); drones under the nights."""
    g = F.globals
    n = len(F.L)

    def J(i0, i1, version, level, off0=0.0, **k):
        if i1 >= n: return
        g.append(dict({'t': round(T(i0) + off0, 3), 'type': 'jingle', 'level': level, 'len': round(F.e(i1) - T(i0) - off0, 2), 'version': version}, **k))
    g.append({'t': round(T(0) + 0.2, 3), 'type': 'drone', 'level': 0.35, 'len': round(F.t(4) - T(0), 2), 'version': 'cold_open'})
    J(160, 160, 'theo', 0.18)
    J(166, 171, 'wall', 0.22)
    J(172, 172, 'wall', 0.3)
    J(176, 176, 'wall', 0.18, loop=True)
    J(205, 205, 'lullaby', 0.2)
    J(230, 231, 'theo', 0.12)
    J(240, 241, 'lullaby', 0.32)
    J(309, 311, 'calm', 0.2)


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

