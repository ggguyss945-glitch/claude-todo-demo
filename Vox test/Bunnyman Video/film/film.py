"""film.py: the shot list, editor and cue sheets for "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN".

Built the way the police film (film_police_ref.py) and the dummy film (film_dummy_ref.py) were: the same engine, cast
system (characters.py + characters_bunny.py) and set system (sets.py + sets_bunny.py), the police header / rule cards /
captions / tags, a global look with a climax ramp, and cue sheets derived from the picture. The shot map this list follows
line by line is W/shotmap.md (every timeline line -> the picture that shows it).

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration 1079.16 s + TAIL 9.85 s: the end card holds for the outro song)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts (a few white flashes / static / VHS cuts)
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --bench N [--shots ..]

THE OWNER'S NOTES, MADE INTO CODE (what this file does differently from the last film):
  * Staging lives on the house plan. Every figure in a set shot stands on a plan point (an anchor Spot or (x, y[, Y]) in
    metres) of the same floor plan the set is drawn from: its height comes from the px-per-metre there
    (CH.height_px(who, spot.ppm)), its feet from the floor point, its draw order from sp.order_at() (furniture between it
    and the camera is drawn over it), its light from sp.light_kw(). Seats, kneels and lies come from the spot's kind, so
    nobody stands on a couch and nothing floats. Facing is a plan direction (face=(x, y)) turned into the cast's turn by
    the view (sp.turn_for), so eyelines point at what the character looks at.
  * Mediums are real cameras on the same plan (cam=dict(eye=(x, y, Y), look=(x, y, Y), S=focal, sx, sy)): the set is
    redrawn from that point of view (ST.cam overrides, cached under their own key), so a cut from a wide to a medium keeps
    every wall, door and person where they were. No long camera fly-throughs: moves are short pushes while people act.
  * Contact: every actor is placed (Acting.place) with the x, y, height it is drawn with, so look_at / reach_to / give /
    hand_over / hold_hand land on their targets; shot-level acts(A, s, sp) stage the interactions between actors and the
    props (PropTrack: a prop rests or is held, never both, never teleports).
  * Lip sync on character lines only (VOICE); narrator lines move no mouths. The Bunnyman's mask never moves its mouth.
  * escalate() is the film-wide acting arc WITHOUT the "scared jiggle": tension shows as wider eyes, raised brows and
    faster breathing for the kids, stiller and stiller stillness for Mom; flinches only on a real sound.

Shot kinds (builders B_<kind>):
  set      a set view (sets_bunny ob_* builders) with figures placed on the plan: room 'living' | 'hall' | 'up' | 'june' |
           'bath' | 'attic' | 'kitchen' | 'yard' | 'front' | 'woods' | 'hosp' | 'parade', view = the builder's view name,
           cam = None (the set's own camera) or a custom camera on the plan; set = builder kwargs (lights, doors ...);
           ppl = [P(who, at, ...)], acts = f(A, shot, sp) -> [extra layers], props, cam moves (c=dict(...))
  bust     a face close-up (CH.draw_bust) over a blurred set background (bg=(room, view[, cam]) + set kwargs); extra busts,
           a hand over the eyes / the mouth, a prop held beside the face, the hand toward the lens
  ins      a prop insert: sets_bunny ob_insert(name, ...) or one of this file's own inserts (INS_CUSTOM)
  rule     the police rule card over the blurred laminated sheet on the fridge (rule n highlighted); recall=True re-shows a
           card (no header change, the key words pulsing)
  pause    the comment prompt: the VHS PAUSE over a frozen frame (src=t), the split MOM | THE BUNNYMAN, ONE WORD, PLAY
  card     graphic cards (the outro: the trick, the eye, the like, the next-episode phone, the end)
  black    black (with an optional line of text)
Plan conventions (plan() at the end): F.cut(t, kind, **p) starts a shot that ends at the next cut. F.t(i) / F.e(i) line
start / end, F.w(i, 'word') the ASR start of a word inside line i; T(i) = F.t(i) - LEAD (cuts land 0.1 s before the word).
Common p keys: c=dict(mv='push'|'keys'|'hold', f, rate, x, y, keys=[(t, x, y, z, ease, f)], hit=[t], shake), tags=[(t, text, x,
y, style, hold)], sfx=[(t, name, gain_db, pan, space, params)], music=[(t, type, level, len)], cut='white'|'static'|'vhs',
era='now'|'1987'|'memory'|'recall'|'outro', grade, post, post_fn, focus (or focus_on=who), dof. Busts: bg_near (the draw
order a background layer needs to stay behind the face, default 1.3), hands=[dict(who, fn(t) -> (x, y, angle, alpha[, size]),
size, shape, side, sleeve_from, scratch)] (the Bunnyman's hands are paws). Inserts: kw = dict or f(time since the cut).
"""
import bisect, hashlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *                                                    # noqa: F401,F403
from engine import hud as H
from engine import post as _epost
from engine.core import DW, DH, CFG, clamp, lerp, ease_in_out, ease_out_cubic, ease_out_back, noise1, hash01, prog, image_from
import characters as CH
import sets as ST

W = os.path.join(HERE, '_work')                                         # this film's work dir (film/_work)
ALIGN = os.path.join(W, 'align')
CUES_DIR = os.path.join(W, 'cues')
TESTS = os.path.join(W, 'tests', 'film')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
TAIL = 9.85                      # the outro: the jingle's outro runs 9.75 s from e(411) + 0.1 (audio/music_plan.py), the end card holds for it
TITLE = "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN"
BASE = 'If_The_Bunnyman_Asks_You_To_Close_Your_Eyes'
CHANNEL = 'NIGHT POLICY'           # the channel's name on the cards (the owner renamed it after the build started)
H._hand = CH.hud_phone_hand

# who speaks which timeline lines (code, fx or None): narrator lines (N) move no mouths. The Bunnyman's L lines (the
# little girl's voice) only nod the mask (the cast's talk on 'bunny'); D ("Mama.") is Dale's face under the half-off head.
VOICE = {'mom': [('M', None)], 'june': [('J', None)], 'june_dress': [('J', None)], 'grandma': [('G', None)],
         'bunny': [('L', None), ('D', None)], 'narrator_neat': [('X', None)], 'narrator_new': [('X', None)]}
WHISPER = ('whisper',)

# ---------------------------------------------------------------- the story clock (header corner)
def _hm(h, m): return h * 60 + m


CLOCK_KEYS = [(187.6, _hm(19, 42)), (200.42, _hm(23, 7)), (287.62, _hm(24, 0)), (369.06, _hm(25, 13)), (425.38, _hm(25, 40)),
              (508.57, _hm(26, 47)), (600.0, _hm(28, 30)), (709.2, _hm(30, 12)), (913.0, _hm(30, 24)), (950.0, _hm(30, 58))]
CORNER = [(0.0, 'EASTER EVE'), (65.75, 'APRIL 1987'), (122.2, 'EVERY EASTER'), (153.5, 'LAST EASTER'), (171.1, 'THIS EASTER'),
          (187.6, None), (950.7, 'NOW'), (993.8, CHANNEL)]


def clock_str(t):
    for k in range(len(CORNER) - 1, -1, -1):
        if t >= CORNER[k][0]:
            if CORNER[k][1] is not None: return CORNER[k][1]
            break
    ts = [a for a, _ in CLOCK_KEYS]; ms = [b for _, b in CLOCK_KEYS]
    m = float(np.interp(t, ts, ms))
    if 258.0 <= t < 279.6: m = float(np.interp(257.0, ts, ms))         # paused
    h, mm = int(m // 60) % 24, int(m % 60)
    return '%d:%02d %s' % ((h % 12) or 12, mm, 'AM' if h < 12 else 'PM')


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
LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.1)
LAMP_R = dict(rim='#ffcf8f', rim_a=60, side=1, key=0.1)
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.25)
NIGHT_L = dict(rim='#8fa6e8', rim_a=70, side=-1, key=-0.25)
MOON = dict(rim='#a8bcff', rim_a=110, side=1, key=-0.35)
DARK = dict(rim='#8fa6e8', rim_a=40, side=1, key=-0.45)
PORCH = dict(rim='#ffc888', rim_a=80, side=-1, key=-0.15)
DAWN = dict(rim='#ffc070', rim_a=95, side=1, key=0.12)
DAWN_L = dict(rim='#ffc070', rim_a=95, side=-1, key=0.12)
MEMORY = dict(rim='#ffd9a0', rim_a=70, side=-1, key=0.25)
VHS87 = dict(rim='#fff2d0', rim_a=50, side=-1, key=0.3)
SUN87 = dict(rim='#ffd08a', rim_a=110, side=1, key=0.2)
HOSP = dict(rim='#e8f4f0', rim_a=55, side=1, key=0.12)
FIRE = dict(rim='#ff9a48', rim_a=120, side=1, key=-0.1)
POLICE = dict(rim='#ff3a4a', rim_a=90, side=-1, key=-0.1)
BULB = dict(rim='#ffcf8f', rim_a=75, side=-1, key=-0.05)
TORCH = dict(rim='#fff1c8', rim_a=60, side=1, key=-0.1)


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
        self.words = []
        if os.path.exists(WORDS):
            try:
                self.words = [(w.strip().lower().strip('.,?!;:"“”…'), float(t)) for w, t in json.load(open(WORDS))['en_words']]
            except Exception:
                self.words = []
        self._wt = [t for _, t in self.words]
        self.shots = []
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
            if t >= t0: cur = 'RULE %d OF 7' % n
        if t >= 993.8: cur = 'THE END'
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
        if sh.p.get('era') == '1987' and sh.kind in ('set', 'bust') and sh.p.get('vhs', True) and sh.p.get('osd', True):
            ST.vhs_stamp(cv, t - sh.t0 + sh.p.get('tape0', 0.0), date=sh.p.get('date', 'APR.19 1987'), clock=sh.p.get('clock_osd', '10:42 AM'), play=False)
        elif sh.kind not in ('black',):
            H.header(cv, self.header_text(t), clock_str(t))
        if sh.kind == 'rule': return
        l = self.line_at(t)
        if not l or not l.get('found_en', True): return
        k, ch = self.chunk_at(l, t)
        txt = ch[k]
        if l['who'] != 'N':
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


# ==================================================================================================== sets on the plan
YARD_CAM = {'woods': 'yard_woods', 'house': 'yard_house', 'wide': 'yard_wide', 'close': 'treeline_close', 'barrel': 'barrel'}
FRONT_CAM = {'house': 'front_house', 'porch': 'porch', 'egg': 'porch_egg', 'peephole': 'peephole'}
ROOMS = {'living': ('ob_living', 'liv_'), 'hall': ('ob_hall', 'hall_'), 'up': ('ob_upstairs', 'up_'), 'june': ('ob_june', 'june_'),
         'bath': ('ob_bath', 'bath_'), 'attic': ('ob_attic', 'attic_'), 'kitchen': ('ob_kitchen', 'kit_'), 'yard': ('ob_yard', YARD_CAM),
         'front': ('ob_front', FRONT_CAM), 'woods': ('ob_woods', 'woods_'), 'hosp': ('ob_hospital', 'hosp_'), 'parade': ('ob_parade', 'parade_')}
_SETS = {}


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
    ov = dict(S=S, h=h, eye=eY, x=ex, y=ey, yaw=yaw, cx=sx)
    ov['env'] = cam.get('env', dict(ENV0))
    if cam.get('pitch'): ov['pitch'] = cam['pitch']
    return ov


def make_set(room, view, cam=None, **kw):
    """The set `room` seen from `view` (the builder's own camera) or from a custom camera on the same plan (cam dict, see
    cam_over). Built through the sets' own builders, so the far rooms, the outside and the lights are the view's; a
    custom camera gets its own cache key."""
    fn_name, pre = ROOMS[room]
    builder = getattr(ST, fn_name)
    base = (pre + view) if isinstance(pre, str) else pre[view]
    if cam is None:
        key = (room, view, json.dumps(kw, sort_keys=True, default=str))
        return builder(view, **kw)
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


def STEP(k, dx=0.0):
    """Plan point standing on stair tread k (1..15) of the hall flight."""
    return (0.82 + dx, 0.9 + (k - 1) * 0.26 + 0.15, k * 0.19)


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


def figure(F, sh, sp, q, k=0, rim=None):
    """One figure on a set (P entry q) -> (Layer, Acting, info). Static figures stand / sit / kneel / lie on their Spot;
    walkers follow plan keys (depth, scale and order follow the plan point)."""
    who = q['who']
    v = sp.view
    path = q.get('path')
    s0 = spot_of(sp, q['at'] if q.get('at') is not None else path[0][1], kind=q.get('kind'))
    kind = q.get('kind') or {'seat': 'seat', 'kneel': 'kneel', 'lie': 'lie'}.get(s0.kind, 'stand')
    Yf = s0.Y if s0.kind != 'seat' else s0.Y
    h0 = CH.height_px(who, s0.ppm) * q.get('hk', 1.0)
    a = CH.Acting(who, seed=q.get('seed', 0) + k * 11 + sh.idx * 3, height=h0, expr=q.get('expr', 'neutral'), blink=q.get('blink'))
    a.place(s0.x, s0.y + q.get('dy', 0.0))
    tr = q.get('turn')
    if tr is None and q.get('face') is not None: tr = _turn_for(sp, s0.X, s0.Yp, q['face'])
    if tr is None: tr = s0.turn
    if tr is not None: a.face(tr, q.get('h_turn', 0.0))
    if kind == 'seat':
        seat_y = s0.seat_y
        if seat_y is None:
            seat_y = v.p(s0.X, s0.Y + q.get('seat', 0.45), s0.Yp)[1]
        if q.get('sit_t') is not None:
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
            lx, ly, ang = CH.torch_pos3(a, t, torch.get('side', 1))
            CH.draw_torch_beam(pen, lx, ly, ang, torch.get('length', 4.0) * hh, torch.get('spread', 12.0), torch.get('a', 0.9), t)
        if sil:
            CH.draw_silhouette(pen, who, x, y, hh, P_, t=t, colr=q.get('sil_c', '#04060c'), a=sil, rim=q.get('sil_rim', '#9fb6ff'),
                               rim_a=q.get('sil_rim_a', 0.5), rim_side=q.get('sil_side', 1), eyes=q.get('sil_eyes', 0.0))
        else:
            CH.draw(pen, who, x, y, hh, P_, light=lt(t) if callable(lt) else lt, t=t)
        if torch and not torch.get('behind'):
            lx, ly, ang = CH.torch_pos3(a, t, torch.get('side', 1))
            CH.draw_torch_beam(pen, lx, ly, ang, torch.get('length', 4.0) * hh, torch.get('spread', 12.0), torch.get('a', 0.9), t)
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

        def draw(pen, t):
            s_ = sp_at(t)
            kk = max(0.25, s_.depth) / R
            hh = CH.height_px(who, s_.ppm) * q.get('hk', 1.0)
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
# The film-wide acting arc on the film clock. NO tremble ("scared jiggle") as filler: tension shows in the eyes, brows and
# breath of the kids; Mom grows stiller (fewer blinks, a locked smile) as the night goes on.
KID_ARC = [(0.0, 0.0), (200.0, 0.15), (247.0, 0.35), (287.0, 0.3), (340.0, 0.45), (425.0, 0.5), (508.0, 0.55), (600.0, 0.75),
           (616.0, 0.9), (690.0, 0.8), (709.0, 0.6), (737.0, 0.85), (770.0, 0.9), (913.0, 0.0)]
MOM_ARC = [(0.0, 0.2), (176.0, 0.35), (247.0, 0.55), (343.0, 0.65), (444.0, 0.7), (580.0, 0.8), (737.0, 0.9), (913.0, 0.0)]


def _arc(arc, t):
    return float(np.interp(t, [a for a, _ in arc], [b for _, b in arc]))


def escalate(a, sh, who):
    """Kids (narrator, June): wide eyes, raised brows, faster shallow breath with the night's tension. Mom (until the
    swap): stillness, fewer blinks. Memory / 1987 / recall / outro shots and rule cards: nothing."""
    if sh.kind in ('rule', 'card', 'black') or sh.p.get('era') in ('memory', '1987', 'outro', 'recall'): return
    if who in ('narrator', 'june', 'june_dress'):
        k = _arc(KID_ARC, sh.t0) * (0.6 if who != 'narrator' else 1.0)
        if k <= 0.02: return

        def fn(P_, t, k=k):
            P_.wide += 0.22 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.1 * k
            per = 3.9 - 1.7 * k
            P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)
    elif who == 'mom' and sh.t0 < 913.0:
        k = _arc(MOM_ARC, sh.t0)

        def fn(P_, t, k=k):
            P_.lock = max(P_.lock, 0.5 * k)
            P_.smile = max(P_.smile, 0.12 * k)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)


# ==================================================================================================== builders: sets
ROOM_RIM = {'living': LAMP, 'hall': LAMP, 'up': NIGHT, 'june': MOON, 'bath': DARK, 'attic': BULB, 'kitchen': LAMP_R,
            'yard': MOON, 'front': PORCH, 'woods': MOON, 'hosp': HOSP, 'parade': VHS87}


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
    if p.get('curtains_fn') is not None and p['room'] == 'living':
        # the front curtains drawn live (closing): the cached curtain piece is swapped for a live layer under the room light
        cf = p['curtains_fn']
        info = sp.info
        sp = sp.without(*[l.name for l in sp if l.name.startswith('curtains_front')])
        lay = ST.live_layer('curtains_live', sp.view, (-3.3, 1.5, 0.12),
                            lambda pen, v_, t, cf=cf: ST.curtain_pair(pen, v_, (-1.4, 0.0), (-5.0, 0.0), -1.4 - ST.LWIN_F[1], -1.4 - ST.LWIN_F[0],
                                                                      ST.LWIN_F[3], 2.0, 0.0, cf(t), ST.P_['drape'], seed=1),
                            info['amb'], info['lights'], info['var_lights'])
        sp = sp.add(lay)
    sh.sp = sp
    rim = p.get('rim', ROOM_RIM.get(p['room']))
    L, A, I = [], {}, {}
    for k, q in enumerate(p.get('ppl', [])):
        lay, a, info = figure(F, sh, sp, q, k, rim)
        L.append(lay); key = q.get('id', q['who']); A[key] = a; I[key] = info
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
    if p.get('era') == '1987' and p['room'] != 'parade' and p.get('vhs'):
        grade = p.get('grade', 'ob_vhs87')
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
    bx, by, bh = bust_place(who, cx, cy, scale)
    pre = lambda a_, s_: a_.place(bx, by, bh)
    a = acting(F, sh, who, (lambda a_, s_: (pre(a_, s_), act and act(a_, s_))), seed=seed, expr=expr, voice=voice, talk=talk, blink=blink)
    m = _Memo(a)
    lt = light

    def draw(pen, t):
        CH.draw_bust(pen, who, cx, cy, scale, m(t), light=lt(t) if callable(lt) else lt, t=t)
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


def _fluffy_tube(x0, y0, x1, y1, w0, w1, fl, n=40):
    """A tube with plush, tufted edges (the Bunnyman's furry arm)."""
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    left, right = [], []
    for j in range(n + 1):
        u_ = j / n; w_ = lerp(w0, w1, u_)
        px, py = x0 + ux * L * u_, y0 + uy * L * u_
        a_ = fl * (0.6 + 0.4 * math.sin(j * 2.1)) * (1 if j % 2 else -0.4)
        b_ = fl * (0.6 + 0.4 * math.cos(j * 1.7)) * (1 if (j + 1) % 2 else -0.4)
        left.append((px + nx * (w_ + a_), py + ny * (w_ + a_)))
        right.append((px - nx * (w_ + b_), py - ny * (w_ + b_)))
    return poly(left + right[::-1])


def hero_paw(pen, who, x, y, size, shape='paw_flat', angle=0.0, side=1, sleeve_to=None, light=None, t=0.0, shadow=None):
    """The Bunnyman's paw seen big: a plush mitten (the cast's paw geometry) with shaded fur, tufts along the edge, the
    pads and, on the filthy suit, mud and matting; the furry arm runs to sleeve_to."""
    sp = CH.CAST[who if who in CH.CAST else 'bunny']
    cl = sp['cloth']; dirt = sp.get('dirt', 0.0)
    k = size / 66.0 * sp['body'].get('hand', 1.0)
    shp = shape if str(shape).startswith('paw') else 'paw_flat'
    u, grooves, pad = CH._paw_geom(shp, side)
    m = skia.Matrix(); m.setTranslate(x, y); m.preRotate(angle); m.preScale(k, k)
    hu = skia.Path(u); hu.transform(m)
    dxa, dya = _arm_dir(angle)
    ex, ey = sleeve_to if sleeve_to is not None else (x + dxa * size * 3.0, y + dya * size * 3.0)
    arm = _fluffy_tube(x + dxa * 4 * k, y + dya * 4 * k, ex, ey, 25 * k, 31 * k, 2.2 * k)
    if shadow:
        sdx, sdy, sbl, sa = shadow
        pen.fill(moved(hu, sdx, sdy), '#100806', sa, blur=sbl)
        pen.fill(moved(arm, sdx, sdy), '#100806', sa * 0.8, blur=sbl)
    # the arm: plush fur, shaded, matted streaks
    L = math.hypot(ex - x, ey - y) or 1.0
    ux, uy = (ex - x) / L, (ey - y) / L; nx, ny = -uy, ux
    pen.fill(arm, cl['fur'])
    pen.linear(arm, x + nx * 26 * k, y + ny * 26 * k, x - nx * 26 * k, y - ny * 26 * k,
               [(0, cl.get('fur_hi', '#ffffff'), 90), (0.4, cl['fur'], 0), (1, cl['fur_sh'], 200)])
    try:
        pen.texture(arm, 'fabric', 0.45, 'overlay', max(0.8, k * 0.5))
    except Exception:
        pass
    rng = np.random.default_rng(11)
    for j in range(int(26 + 30 * dirt)):
        uu = rng.uniform(0.05, 0.95) * min(L, 300 * k); oo = rng.uniform(-0.9, 0.9) * 24 * k
        px, py = x + ux * uu + nx * oo, y + uy * uu + ny * oo
        ln = rng.uniform(5, 12) * k
        pen.seg((px, py), (px + ux * ln, py + uy * ln), max(0.8, 0.6 * k), cl['fur_dp'] if j % 3 else cl.get('fur_hi', cl['fur']), 90)
    if dirt > 0.2:
        pen.fill(arm, cl.get('mud', '#3b2f24'), 70 * dirt)
    pen.line(arm, max(1.6, 1.1 * k), CH.LINE, 230)
    # the paw
    c = CH.Ctx(pen, m, 1.0)
    c.fill(u, cl['fur'])
    c.grad(u, 26, 0, -26, 50, [(0, cl.get('fur_hi', '#ffffff'), 85), (0.45, cl['fur'], 0), (1, cl['fur_sh'], 190)])
    c.fill(CH._crescent(u, -4, -2.5), cl['fur_sh'], 120)
    if dirt > 0.2:
        bb = u.getBounds()
        c.grad(u, 0, bb.top(), 0, bb.bottom(), [(0, cl.get('mud', '#3b2f24'), 40 * dirt), (1, cl.get('mud', '#3b2f24'), 170 * dirt)])
    if pad == 'pads':
        pc = cl['inner'] if dirt < 0.5 else CH.mix(cl['inner'], '#5a4040', 0.45)
        for (px, py, rx, ry) in ((0, 26, 15, 12), (-15, 50, 5.5, 6.5), (-5, 57, 5.5, 6.5), (6, 57, 5.5, 6.5), (16, 50, 5.5, 6.5)):
            c.fill(oval(px, py, rx, ry), pc)
            c.fill(oval(px - rx * 0.25, py - ry * 0.3, rx * 0.45, ry * 0.35), '#ffffff', 60)
            c.line(oval(px, py, rx, ry), 0.45, CH.mix(pc, '#000000', 0.35), 200)
    if grooves:
        c.line(CH._multi(grooves), 0.6, cl['fur_dp'], 200)
    # fur tufts along the silhouette
    pm = skia.PathMeasure(u, True)
    Ln = pm.getLength()
    if Ln > 1:
        n = int(Ln / 4.5)
        for j in range(n):
            pt, tg = pm.getPosTan(Ln * j / n)
            nx2, ny2 = tg.y(), -tg.x()
            l2 = 2.6 + 1.6 * ((j * 7) % 5) / 5.0
            c.line(poly([(pt.x() - nx2 * 1.2, pt.y() - ny2 * 1.2), (pt.x() + nx2 * l2, pt.y() + ny2 * l2)], False), 0.55, cl['fur_sh'], 170)
    c.line(u, max(0.75, 1.5 / max(0.4, k)), CH.LINE, 235)


def hand_layer(who, fn, size, shape='open', side=1, depth=0.9, sleeve_from=None, scratch=False, name='hand', paw=False,
               light=None, shadow=True, bare=None):
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
        if paw or CH.CAST[who_].get('bunny'):
            hero_paw(pen, who_, x, y, sz, shape if str(shape).startswith('paw') else 'paw_flat', ang, side, sf, lt, t, shd)
        else:
            b = bare if bare is not None else (34.0 if scratch else 0.0)
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
                                hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand')))
    if p.get('acts'):
        extra += [l for l in (p['acts'](sh.A, sh, None) or []) if l is not None]
    c = dict(p.get('c') or dict(mv='push', x=960 + (cx - 960) * 0.25, y=cy - 40, rate=0.0))
    c.setdefault('free', True)
    if c.get('mv', 'push') == 'push' and 'z1' not in c:
        c['z1'] = (1.0 + c.get('zrate', 0.022)) ** max(0.3, sh.d)
    cam = scam(sh, None, c)

    def fx(t):
        d = dict((sfx_fn.fx(t) if sfx_fn is not None else None) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(layers + [lay] + extra, cam, lens, grade, 1.0, p.get('dof', 6.75), fx=fx, hud=p.get('hud'))


# ==================================================================================================== builders: inserts
def _fur_bg(pen, c1='#a7abb5', c2='#7a7f8b', c3='#ced2da', seed=3):
    pen.fill(rect(-400, -300, 2720, 1680), c1)
    pen.texture(rect(-400, -300, 2720, 1680), 'fabric', 0.55, 'overlay', 3.0)
    rng = np.random.default_rng(seed)
    for k in range(900):
        x, y = rng.uniform(-300, 2220), rng.uniform(-200, 1280)
        a = rng.uniform(-0.6, 0.6) + math.pi / 2
        L_ = rng.uniform(14, 40)
        pen.seg((x, y), (x + math.cos(a) * L_, y + math.sin(a) * L_), rng.uniform(2, 4), c2 if k % 3 else c3, 90)


def ins_badge(pen, t, **kw):
    """Dale's Pemberton's name badge pinned on the mascot's grey fur (1987)."""
    _fur_bg(pen)
    cv = pen.cv
    cv.save(); cv.translate(960, 560); cv.rotate(-4.0)
    b = rrect(-430, -190, 860, 380, 28)
    pen.fill(moved(b, 14, 22), '#000000', 110, blur=16)
    pen.fill(b, '#fbfaf4'); pen.line(b, 5, '#3a3036')
    top = rrect(-430, -190, 860, 120, 28)
    pen.fill(inter(top, b), '#c8323a')
    ST.btext(pen, "Pemberton's", 0, -105, 'script', 92, '#fbfaf4', 255, 'center')
    ST.btext(pen, 'DALE', 0, 60, 'head', 150, '#1c1a20', 250, 'center', spacing=0.06)
    ST.btext(pen, 'STOCK ROOM  ·  SINCE 1985', 0, 140, 'sans_b', 40, '#5a525a', 230, 'center', spacing=0.08)
    pen.linear(b, -430, -190, 430, 190, [(0, '#ffffff', 0), (0.42, '#ffffff', 0), (0.5, '#ffffff', 70), (0.58, '#ffffff', 0), (1, '#ffffff', 0)])
    pen.fill(oval(-380, -150, 12), '#c9b06a'); pen.fill(oval(380, -150, 12), '#c9b06a')
    cv.restore()


def ins_poster(pen, t, **kw):
    """MISSING: Dale Whitlock, 19, on a telephone pole (rain-faded, staples)."""
    pen.fill(rect(-400, -300, 2720, 1680), '#3a2c22')
    pen.texture(rect(-400, -300, 2720, 1680), 'wood', 0.9, 'overlay', 1.5, 90)
    for k in range(9):
        x = 200 + k * 190
        pen.seg((x, -300), (x + 20, 1380), 6, '#2a1e16', 120)
    cv = pen.cv
    cv.save(); cv.translate(960, 540); cv.rotate(2.0)
    paper = rect(-420, -470, 840, 940)
    pen.fill(moved(paper, 12, 18), '#000000', 120, blur=14)
    pen.fill(paper, '#e8e0c8'); pen.texture(paper, 'paper', 0.6, 'overlay', 1.0)
    ST.btext(pen, 'MISSING', 0, -330, 'head', 150, '#1a1414', 245, 'center', spacing=0.05)
    ph = rect(-200, -270, 400, 380)
    pen.fill(ph, '#8a8278'); pen.texture(ph, 'paper', 0.4, 'overlay', 1.0)
    pen.fill(oval(0, -120, 90, 110), '#5a524a'); pen.fill(rrect(-150, -20, 300, 130, 60), '#4a423a')
    ST.btext(pen, 'DALE WHITLOCK, 19', 0, 190, 'head', 74, '#1a1414', 240, 'center')
    for k, s_ in enumerate(['LAST SEEN EASTER SUNDAY, APRIL 19, 1987', "PEMBERTON'S EASTER PARADE, MAIN STREET", 'WEARING A GREY RABBIT COSTUME',
                            'CALL HOLLOWAY POLICE  555-0143']):
        ST.btext(pen, s_, 0, 260 + k * 46, 'sans_b', 31, '#2a2420', 230, 'center')
    for y0 in (-450, 440):
        for x0 in (-390, 390):
            pen.seg((x0 - 14, y0), (x0 + 14, y0 + 3), 4, '#8a8a90', 230)
    pen.linear(paper, 0, -470, 0, 470, [(0, '#3a2a1a', 0), (0.7, '#3a2a1a', 30), (1, '#3a2a1a', 90)])
    cv.restore()


def _frame_photo(pen, x, y, w, h, wood='#6a4426', mat='#efe6d0'):
    pen.fill(moved(rect(x - w / 2 - 40, y - h / 2 - 40, w + 80, h + 80), 12, 20), '#000000', 110, blur=18)
    fr = rect(x - w / 2 - 40, y - h / 2 - 40, w + 80, h + 80)
    pen.fill(fr, wood); pen.texture(fr, 'wood', 0.6, 'overlay', 1.2); pen.line(fr, 4, '#2a1a10')
    pen.fill(rect(x - w / 2 - 10, y - h / 2 - 10, w + 20, h + 20), mat)


def ins_wedding(pen, t, **kw):
    """Mom and Dad's wedding photo on the mantel (framed): grew up, married my dad."""
    pen.fill(rect(-400, -300, 2720, 1680), '#c8a8b0'); pen.texture(rect(-400, -300, 2720, 1680), 'paper', 0.4, 'overlay', 1.0)
    pen.fill(rect(-400, 880, 2720, 600), '#5a3a28'); pen.texture(rect(-400, 880, 2720, 600), 'wood', 0.7, 'overlay', 1.4)
    pen.radial(None, 700, 200, 1500, [(0, '#ffd8a0', 70), (1, '#000000', 120)])
    x, y, w, h = 960, 500, 640, 760
    _frame_photo(pen, x, y, w, h)
    cv = pen.cv
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h))
    pen.linear(rect(x - w / 2, y - h / 2, w, h), 0, y - h / 2, 0, y + h / 2, ['#e8dcc4', '#bfae90'])
    P1 = CH.Pose(); P1.smile = 0.7; P1.teeth = 0.3; P1.turn = 0.25
    P2 = CH.Pose(); P2.smile = 0.6; P2.teeth = 0.2; P2.turn = -0.3; P2.h_tilt = 6.0
    CH.draw_bust(pen, 'dad', x + 120, y - 10, 0.42, P2, light=MEMORY, t=0.0)
    CH.draw_bust(pen, 'mom', x - 120, y + 40, 0.38, P1, light=MEMORY, t=0.0)
    pen.fill(rect(x - w / 2, y - h / 2, w, h), '#d8b888', 60)
    cv.restore()
    pen.linear(rect(x - w / 2, y - h / 2, w, h), x - w / 2, y - h / 2, x + w / 2, y + h / 2,
               [(0, '#ffffff', 0), (0.35, '#ffffff', 0), (0.42, '#ffffff', 45), (0.5, '#ffffff', 0), (1, '#ffffff', 0)])


def ins_gran_photo(pen, t, **kw):
    """Grandma's framed portrait on the hall console, a black ribbon across the corner (dead six years)."""
    pen.fill(rect(-400, -300, 2720, 1680), '#9aa8c8'); pen.texture(rect(-400, -300, 2720, 1680), 'paper', 0.4, 'overlay', 1.0)
    pen.fill(rect(-400, 900, 2720, 600), '#4a3020'); pen.texture(rect(-400, 900, 2720, 600), 'wood', 0.7, 'overlay', 1.4)
    pen.radial(None, 960, 300, 1300, [(0, '#ffd8a0', 60), (1, '#000000', 150)])
    x, y, w, h = 960, 520, 560, 680
    _frame_photo(pen, x, y, w, h, wood='#3a2a1a')
    cv = pen.cv
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h))
    pen.linear(rect(x - w / 2, y - h / 2, w, h), 0, y - h / 2, 0, y + h / 2, ['#c8b8d8', '#8a7a9a'])
    P1 = CH.Pose(); P1.smile = 0.55; P1.squint = 0.15
    CH.draw_bust(pen, 'grandma', x, y + 60, 0.5, P1, light=MEMORY, t=0.0)
    cv.restore()
    rib = poly([(x + w / 2 - 170, y - h / 2 - 40), (x + w / 2 - 70, y - h / 2 - 40), (x + w / 2 + 40, y - h / 2 + 70), (x + w / 2 + 40, y - h / 2 + 170)])
    pen.fill(rib, '#0c0a0c'); pen.line(rib, 2, '#2a2a2a')


def ins_wristband(pen, t, **kw):
    """The hospital wristband on the narrator's new (Mom's) wrist: PRICE, LAURIE."""
    pen.fill(rect(-400, -300, 2720, 1680), '#c8d4d0'); pen.texture(rect(-400, -300, 2720, 1680), 'fabric', 0.5, 'overlay', 2.0)
    arm = poly([(-300, 700), (2300, 420), (2300, 900), (-300, 1180)])
    pen.fill(arm, '#e8c0a8'); pen.linear(arm, 0, 420, 0, 1180, [(0, '#ffffff', 40), (0.5, '#000000', 0), (1, '#000000', 70)]); pen.line(arm, 4, '#7a5040')
    band = poly([(380, 560), (1540, 440), (1560, 720), (400, 840)])
    pen.fill(moved(band, 10, 18), '#000000', 90, blur=12)
    pen.fill(band, '#fbfbf8'); pen.line(band, 4, '#8a8a90')
    cv = pen.cv
    cv.save(); cv.translate(960, 640); cv.rotate(-6.0)
    ST.btext(pen, 'PRICE, LAURIE', -480, -10, 'mono', 76, '#141414', 245, 'left')
    ST.btext(pen, 'F  43Y   RM 11   DR. HALVERSON', -480, 60, 'mono', 40, '#2a2a2a', 230, 'left')
    for k in range(28):
        bw = 4 + 6 * hash01(k, 7)
        pen.fill(rect(260 + k * 11, -70, bw, 120), '#141414', 230)
    cv.restore()


def ins_report(pen, t, **kw):
    """A report card: straight A's (the narrator's old body, doing great)."""
    pen.fill(rect(-400, -300, 2720, 1680), '#5a4636'); pen.texture(rect(-400, -300, 2720, 1680), 'wood', 0.7, 'overlay', 1.2)
    cv = pen.cv
    cv.save(); cv.translate(960, 540); cv.rotate(-3.0)
    paper = rect(-520, -470, 1040, 940)
    pen.fill(moved(paper, 14, 20), '#000000', 110, blur=16)
    pen.fill(paper, '#f6f2e6'); pen.texture(paper, 'paper', 0.5, 'overlay', 1.0)
    ST.btext(pen, 'HOLLOWAY HIGH SCHOOL', 0, -380, 'serif_b', 54, '#1a2a4a', 240, 'center')
    ST.btext(pen, 'REPORT CARD  ·  SPRING TERM', 0, -320, 'sans_b', 34, '#3a4a6a', 230, 'center', spacing=0.06)
    subj = ['ENGLISH', 'ALGEBRA II', 'BIOLOGY', 'U.S. HISTORY', 'SPANISH', 'ART']
    for k, s_ in enumerate(subj):
        yy = -210 + k * 108
        pen.seg((-440, yy + 30), (440, yy + 30), 2, '#8a96aa', 200)
        ST.btext(pen, s_, -420, yy, 'sans_b', 40, '#1a1a24', 235, 'left')
        u = clamp((t - 0.15 * k) / 0.25)
        if u > 0:
            ST.btext(pen, 'A', 330, yy + 6, 'head', 74, '#c8262e', 255 * u, 'center')
            pen.line(oval(330, yy - 18, 52 * u + 4, 44 * u + 4), 5, '#c8262e', 220 * u)
    ST.btext(pen, 'ABSENCES: 0     TARDIES: 0', -420, 450, 'sans_b', 34, '#2a2a34', 230, 'left')
    cv.restore()


def ins_knuckles(pen, t, hits=(), **kw):
    """Grandma's knuckles knocking on the kitchen table (memory): the fist lifts and comes down on each hit time (s from
    the start of the shot)."""
    pen.fill(rect(-400, -300, 2720, 1680), '#d8c8a0')
    top = poly([(-400, 520), (2320, 480), (2320, 1380), (-400, 1380)])
    pen.fill(top, '#a87a4a'); pen.texture(top, 'wood', 0.8, 'overlay', 1.4, 0)
    pen.linear(rect(-400, -300, 2720, 900), 0, -300, 0, 600, [(0, '#fff2d8', 255), (1, '#e8d4b0', 255)])
    pen.fill(rect(-400, 470, 2720, 40), '#6a4a2a', 200)
    lift = 1.0
    for th in hits:
        dt = t - th
        if -0.16 < dt < 0.0: lift = min(lift, -dt / 0.16)
        elif 0.0 <= dt < 0.2: lift = min(lift, dt / 0.2)
    y = 760 - 120 * ease_in_out(lift)
    sc = SLEEVE['grandma']
    sl = _sleeve_poly(1060, y - 40, 1900, y - 330, 120, 170)
    pen.fill(sl, sc[0]); pen.line(sl, 5, '#2a2030', 230)
    pen.fill(oval(960, 790, 230 - 40 * lift, 34), '#000000', 90 - 50 * lift, blur=16)
    CH.draw_hand(pen, 'grandma', 1000, y - 40, 420, 'fist', 70.0, 1)


def ins_desk(pen, t, **kw):
    """A very ordinary cup of coffee steaming beside a notebook (the script) and a pen, under a desk lamp."""
    pen.fill(rect(-400, -300, 2720, 1680), '#6a4a32'); pen.texture(rect(-400, -300, 2720, 1680), 'wood', 0.8, 'overlay', 1.3, 0)
    pen.radial(None, 1300, 200, 1400, [(0, '#ffe2b0', 120), (1, '#000000', 160)])
    cv = pen.cv
    cv.save(); cv.translate(700, 560); cv.rotate(-7.0)
    nb = rect(-420, -330, 840, 660)
    pen.fill(moved(nb, 12, 18), '#000000', 110, blur=14)
    pen.fill(nb, '#f4efe0'); pen.texture(nb, 'paper', 0.5, 'overlay', 1.0)
    for k in range(11): pen.seg((-400, -240 + k * 52), (400, -240 + k * 52), 2, '#9ab0d0', 200)
    pen.seg((-330, -330), (-330, 330), 2, '#d88a8a', 200)
    ST.btext(pen, 'Night Policy', -300, -262, 'hand', 52, '#1a2a5a', 240, 'left')
    for k, s_ in enumerate(['the bunnyman - easter', 'seven rules on the fridge', 'mom hums. always.', "don't count to seven",
                            'the trick = the swap ?', 'ending: the hospital']):
        ST.btext(pen, s_, -300, -158 + k * 52, 'hand', 40, '#1a2a5a', 220, 'left')
    pen.seg((-300, 70), (60, 70), 4, '#1a2a5a', 200)
    cv.restore()
    pen.seg((1120, 900), (1460, 690), 18, '#2a2a34'); pen.seg((1440, 702), (1470, 684), 18, '#c8a24a')
    mx, my = 1380, 520
    pen.fill(oval(mx + 20, my + 190, 210, 50), '#000000', 110, blur=16)
    body = rrect(mx - 170, my - 120, 340, 300, 40)
    pen.fill(body, '#e8e4dc'); pen.linear(body, mx - 170, 0, mx + 170, 0, [(0, '#ffffff', 90), (0.6, '#000000', 0), (1, '#000000', 80)]); pen.line(body, 5, '#3a3430')
    pen.line(oval(mx + 200, my + 20, 70, 90), 26, '#e8e4dc'); pen.line(oval(mx + 200, my + 20, 70, 90), 4, '#3a3430')
    pen.fill(oval(mx, my - 120, 170, 42), '#d8d2c8'); pen.fill(oval(mx, my - 116, 148, 32), '#3a2216')
    pen.fill(oval(mx - 30, my - 122, 60, 10), '#8a5a3a', 140)
    for k in range(3):
        ph = t * 0.6 + k * 0.33
        u = ph % 1.0
        sx = mx - 50 + k * 50 + 30 * math.sin(ph * 6.0 + k)
        sy = my - 150 - 260 * u
        pen.fill(oval(sx, sy, 34 + 40 * u, 60 + 50 * u), '#ffffff', 60 * (1 - u) * min(1.0, u * 4), blur=18)


def ins_hanger(pen, t, back=False, zip_t=None, **kw):
    """The Bunnyman is just a costume: the clean suit hanging empty on a rail in a wardrobe room (back=True: from behind,
    the zipper; zip_t = s when the pull slides down)."""
    pen.fill(rect(-400, -300, 2720, 1680), '#2a2630'); pen.texture(rect(-400, -300, 2720, 1680), 'plaster', 0.5, 'overlay', 1.0)
    pen.radial(None, 960, 120, 1300, [(0, '#fff0d0', 120), (1, '#000000', 140)])
    pen.fill(rect(-400, 100, 2720, 26), '#8a8a90'); pen.line(rect(-400, 100, 2720, 26), 3, '#2a2a30')
    P_ = CH.Pose(); P_.turn = 2.0 if back else 0.05; P_.still = 1.0; P_.life = 0.0
    for side in ('hl_', 'hr_'):
        setattr(P_, side + 'down', 330.0); setattr(P_, side + 'out', -6.0); setattr(P_, side + 'fwd', 20.0)
    P_.h_nod = 0.35; P_.h_tilt = 6.0 * math.sin(t * 0.8)
    pen.seg((960, 100), (960, 190), 6, '#b8b8c0')
    pen.line(poly([(860, 230), (960, 175), (1060, 230)], False), 7, '#b8b8c0')
    sway = 4.0 * math.sin(t * 0.9)
    cv = pen.cv
    cv.save(); cv.rotate(0.3 * math.sin(t * 0.9)); cv.translate(sway, 0)
    CH.draw(pen, 'bunny87', 960, 1240, 1180, P_, light=dict(rim='#fff0d0', rim_a=60, side=-1, key=0.0), t=t)
    if back and zip_t is not None:
        u = ease_in_out(clamp((t - zip_t) / 1.2))
        x0, y0 = 960, 420
        pen.seg((x0, y0), (x0, y0 + 520), 6, '#3a3a40', 200)
        zy = y0 + 470 * u
        pen.fill(poly([(x0 - 14, y0), (x0 + 14, y0), (x0 + 30 * u, zy), (x0 - 30 * u, zy)]), '#16121a', 220)
        pen.fill(rrect(x0 - 11, zy, 22, 54, 6), '#c8c8d0'); pen.line(rrect(x0 - 11, zy, 22, 54, 6), 3, '#3a3a40')
    cv.restore()


def ins_lens_hand(pen, t, **kw):
    pass


# ---------------------------------------------------------------- polish pass: inserts rebuilt around the cast's hands
_TIPC = {}


def hand_tip(shape, side):
    """Local hand point (hand units, wrist at the origin) of the fingertip farthest from the wrist: the index tip of
    'point', the middle fingertip of an open hand, the knuckles' far edge of a fist."""
    key = (shape, side)
    if key not in _TIPC:
        u = CH._hand_cached(shape, side, 0.0)['union']
        pm = skia.PathMeasure(u, True); L = pm.getLength(); best = (0.0, 0.0)
        for j in range(240):
            p_, _ = pm.getPosTan(L * j / 240)
            if p_.y() > best[1]: best = (p_.x(), p_.y())
        _TIPC[key] = best
    return _TIPC[key]


def hand_low(shape, side, angle, size, who='mom'):
    """Design offset (dx, dy) from the wrist of the LOWEST point of a hand drawn at `angle` (where a knocking fist meets
    the table)."""
    k = size / 66.0 * CH.CAST[who]['body'].get('hand', 1.0)
    u = skia.Path(CH._hand_cached(shape, side, 0.0)['union'])
    m = skia.Matrix(); m.setRotate(angle); m.preScale(k, k); u.transform(m)
    pm = skia.PathMeasure(u, True); L = pm.getLength(); best = (0.0, -1e9)
    for j in range(240):
        p_, _ = pm.getPosTan(L * j / 240)
        if p_.y() > best[1]: best = (p_.x(), p_.y())
    return best


def wrist_for(tip, shape, side, angle, size, who='mom'):
    """The wrist position that puts the fingertip of a hand (shape, side, angle, size) on design point `tip`."""
    lx, ly = hand_tip(shape, side)
    k = size / 66.0 * CH.CAST[who]['body'].get('hand', 1.0)
    a = math.radians(angle)
    return tip[0] - (lx * math.cos(a) - ly * math.sin(a)) * k, tip[1] - (lx * math.sin(a) + ly * math.cos(a)) * k


def switch_finger(t0, on, who, t_flip=0.55, dur=0.22, hold=0.55, size=600.0):
    """A fn for hand_layer: a finger that comes in, lands ON the toggle's lever tip, pushes it (up for on, down for off)
    in step with the switch insert's flip, rests a moment and leaves; the wrist follows the fingertip (no floating
    finger). Times are film time; the insert's toggle tip runs 680 -> 420 (on) / 420 -> 680 (off) at x 960."""
    ang = 172.0 if on else 18.0
    shape = 'point'
    side = -1

    def fn(tt):
        r = tt - t0
        a_in = ease_in_out(clamp((r - (t_flip - 0.55)) / 0.5))
        a_out = ease_in_out(clamp((r - (t_flip + dur + hold)) / 0.45))
        if a_in <= 0.0 or a_out >= 1.0: return None
        f = ease_in_out(clamp((r - t_flip) / dur))
        ty = (lerp(694, 434, f) if on else lerp(406, 666, f))
        tip = (962.0, ty)
        wx, wy = wrist_for(tip, shape, side, ang, size, who)
        # in from / out to the lower right (on) or the upper right (off), along the forearm
        dxa, dya = _arm_dir(ang)
        off = (1.0 - a_in) + a_out
        return (wx + dxa * 900 * off, wy + dya * 900 * off, ang, 1.0, size)
    return fn


def ins_knuckles2(pen, t, hits=(), **kw):
    """Grandma's family knock, close (memory, warm daylight): her fist (the cast's hand: knuckles, the gold band, her
    lavender cardigan's ribbed cuff) knocks the 2-3-2 on the red-and-white checked tablecloth of the kitchen table (the
    same cloth as the wide), the cloth dimpling under each hit; a glass of milk and the narrator's small hands at the
    far edge of the table."""
    pen.fill(rect(-400, -300, 2720, 1680), '#e8d8b8')
    pen.linear(rect(-400, -300, 2720, 900), 0, -300, 0, 600, [(0, '#fff2d8', 255), (1, '#e2cfaa', 255)])
    # the far wall: the kitchen's yellow wallpaper and the counter edge, out of focus
    pen.fill(rect(-400, -300, 2720, 640), '#d9b878')
    for i in range(-2, 12):
        pen.fill(oval(i * 210 + 40, 160, 46, 30), '#e4c590', 150, blur=10)
    pen.fill(rect(-400, 300, 2720, 70), '#8a6a42', 200, blur=8)
    # the tablecloth in perspective: rows of checks growing toward us
    Yh = 300.0
    for j in range(16):
        y0 = Yh + 340 * ((j / 16.0) ** 1.8); y1 = Yh + 340 * (((j + 1) / 16.0) ** 1.8)
        y0 = 420 + (y0 - Yh) * 3.1; y1 = 420 + (y1 - Yh) * 3.1
        for i in range(-20, 21):
            def X(xx, yy): return 960 + (xx - 960) * (0.45 + 0.55 * (yy - 420) / 1060.0 + 0.55)
            xa, xb = 960 + i * 120, 960 + (i + 1) * 120
            q = [(X(xa, y0), y0), (X(xb, y0), y0), (X(xb, y1), y1), (X(xa, y1), y1)]
            if (i + j) % 2 == 0: pen.fill(poly(q), '#c8323a')
            else: pen.fill(poly(q), '#f6efe2')
    cloth = rect(-400, 420, 2720, 1300)
    pen.texture(cloth, 'fabric', 0.45, 'overlay', 2.2)
    pen.linear(cloth, 0, 420, 0, 1400, [(0, '#000000', 60), (0.25, '#000000', 0), (1, '#3a2010', 70)])
    pen.fill(rect(-400, 412, 2720, 14), '#5a3a22', 160, blur=6)                 # the cloth's far edge on the table
    # the glass of milk and the six-year-old's hands at the far edge
    g = rrect(470, 250, 120, 210, 18)
    pen.fill(moved(g, 8, 10), '#000000', 60, blur=10)
    pen.fill(g, '#f8f6f0', 235); pen.fill(rrect(478, 300, 104, 152, 14), '#ffffff', 255); pen.line(g, 3, '#7a7060', 200)
    # the knock: lift between hits, the knuckles land on the cloth at each hit time
    lift = 1.0
    for th in hits:
        dt = t - th
        if -0.15 < dt < 0.0: lift = min(lift, ease_in_out(-dt / 0.15))
        elif 0.0 <= dt < 0.2: lift = min(lift, ease_in_out(dt / 0.2))
    contact_y = 760.0
    ang = 78.0; size = 560.0
    lo = hand_low('fist', 1, ang, size, 'grandma')
    wx, wy = 1030.0 - lo[0], contact_y - lo[1] - 150.0 * lift
    hit_k = max([0.0] + [math.exp(-abs(t - th) * 18.0) for th in hits])
    pen.fill(oval(1010, contact_y + 12, 190 - 60 * lift, 30 - 8 * lift), '#2a0808', 120 - 80 * lift, blur=14)
    if hit_k > 0.05:
        pen.line(oval(1010, contact_y + 6, 150 + 60 * hit_k, 16 + 6 * hit_k), 3.0, '#7a1a1e', 120 * hit_k)
    hero_hand(pen, 'grandma', wx, wy, size, 'fist', ang, 1, (2150, wy - 700), dict(side=-1, key=0.15),
              shadow=None, ring=True)


def ins_egg_gold_hands(pen, t, **kw):
    """'She was holding a golden plastic egg.': Laurie's small hands (the cast's hands, bare forearms under the puffed
    sleeves of the 1987 dress) cupping the golden Pemberton's egg against the yellow bodice, the white collar above,
    sunrise light from the left, the egg's highlight moving as she breathes."""
    cv = pen.cv
    pen.fill(rect(-400, -300, 2720, 1680), '#e8b83a')
    body = rect(-400, -300, 2720, 1680)
    pen.texture(body, 'fabric', 0.55, 'overlay', 2.0)
    pen.linear(body, -300, 0, 2300, 0, [(0, '#fff2c0', 120), (0.45, '#f2c84b', 0), (1, '#a8781c', 150)])
    for k in range(-6, 8):                                                  # the bodice's gathers
        pen.line(smooth([(k * 190 + 60, 260), (k * 190 + 90, 700), (k * 190 + 40, 1300)], False), 3.0, '#c99a24', 90)
    col = smooth([(-300, -300), (2220, -300), (2220, 120), (1500, 210), (960, 250), (420, 210), (-300, 120)], True, 0.6)
    pen.fill(moved(col, 0, 16), '#7a5a10', 70, blur=12)
    pen.fill(col, '#fbf8ee'); pen.texture(col, 'fabric', 0.3, 'overlay', 1.4)
    for k in range(26):
        pen.fill(oval(-280 + k * 98, 150 + 70 * math.sin(k / 25 * math.pi), 34, 22), '#fbf8ee'); pen.line(oval(-280 + k * 98, 150 + 70 * math.sin(k / 25 * math.pi), 34, 22), 2, '#c9c4b2', 160)
    pen.line(col, 3.5)
    sash = rect(-400, 960, 2720, 160)
    pen.fill(sash, '#fbf8ee'); pen.texture(sash, 'fabric', 0.3, 'overlay', 1.4); pen.line(sash, 3.5)
    bob = 6.0 * math.sin(t * 2.0 * math.pi / 3.6)
    cv.save(); cv.translate(0, bob)
    lt = dict(side=-1, key=0.2)
    # both small hands cupped under the egg, palms up, fingers curling up its sides; the egg rests in them
    pen.fill(oval(965, 900, 300, 70), '#5a3a08', 110, blur=20)
    hero_hand(pen, 'laurie87', 760, 1010, 360, 'relaxed', 205.0, 1, (380, 1600), lt, bare=999.0, shadow=(10, 16, 16, 80))
    hero_hand(pen, 'laurie87', 1170, 1010, 360, 'relaxed', 155.0, -1, (1550, 1600), lt, bare=999.0, shadow=(10, 16, 16, 80))
    ST.draw_egg(pen, 965, 610, 470, rot=-6.0, gold=True, stamp=True, shine=1.0)
    pen.radial(None, 860 + 30 * math.sin(t * 0.7), 480, 140, [(0, '#ffffff', 110), (1, '#ffffff', 0)], clip=False)
    cv.restore()


def _new_dress(pen, cx, top, s=1.0, age=0.0):
    """June's new yellow Easter dress on a white wire hanger (the dress_new insert's design, drawn on anything)."""
    y = CH.mix('#f2c84b', '#b9b4a2', 0.72 * age); ysh = CH.mix('#c99a24', '#8a8676', 0.72 * age); wc = '#fbfaf4'
    cv = pen.cv; cv.save(); cv.translate(cx, top); cv.scale(s, s)
    pen.line(poly([(-150, 70), (0, 0), (150, 70)], False), 8, '#e8e8ec'); pen.line(oval(0, -40, 34), 7, '#e8e8ec')
    bod = smooth([(-130, 40), (130, 40), (150, 200), (140, 330), (-140, 330), (-150, 200)], True, 0.5)
    sk = smooth([(-140, 320), (140, 320), (330, 760), (160, 830), (0, 840), (-160, 830), (-330, 760)], True, 0.55)
    pen.fill(moved(union(bod, sk), 18, 26), '#000000', 90, blur=18)
    for sd in (-1, 1):
        sl = ST._blob(sd * 190, 110, 90, 80, 9, 2 + sd, 0.12); pen.fill(sl, y); pen.line(sl, 4)
    pen.fill(sk, y); pen.texture(sk, 'fabric', 0.5, 'overlay', 1.2)
    pen.linear(sk, -330, 0, 330, 0, [(0, '#fff2c0', 70), (0.5, y, 0), (1, ysh, 140)])
    for k in range(-4, 5): pen.line(poly([(k * 30, 340), (k * 70, 800)], False), 3, ysh, 180)
    pen.fill(bod, y); pen.texture(bod, 'fabric', 0.5, 'overlay', 1.2)
    for k in range(17):
        lc = oval(-320 + k * 40, 800 + 30 * math.sin(k / 16 * math.pi), 26, 18); pen.fill(lc, wc); pen.line(lc, 2, '#8a8676', 160)
    pen.fill(rect(-145, 300, 290, 42), wc); pen.line(rect(-145, 300, 290, 42), 3)
    for sd in (-1, 1):
        bw = ST._blob(sd * 90, 320, 70, 40, 8, 5 + sd, 0.2); pen.fill(bw, wc); pen.line(bw, 3)
        cp = smooth([(0, 50), (sd * 110, 40), (sd * 125, 100), (sd * 25, 95)], True, 0.8); pen.fill(cp, wc); pen.line(cp, 3)
    pen.line(sk, 4); pen.line(bod, 4)
    cv.restore()


def ins_dress_photo(pen, t, push=0.0, **kw):
    """'Exactly like the one in the photo.': June's new yellow dress on its hanger on her closet door, and taped to the
    door beside it the Courier clipping Mom kept, the 1987 photo of Laurie in the same dress holding the mascot's paw:
    the same collar, the same sash, the same pleats."""
    pen.fill(rect(-400, -300, 2720, 1680), '#4a4a7a')
    door = rect(-400, -300, 2720, 1680)
    pen.texture(door, 'wood', 0.25, 'overlay', 3.0, 90)
    for (x0, y0, w0, h0) in ((60, -120, 620, 560), (1240, -120, 620, 560), (60, 560, 620, 760), (1240, 560, 620, 760)):
        pen.line(rect(x0, y0, w0, h0), 6, '#2a2a50', 150); pen.line(rect(x0 + 8, y0 + 8, w0, h0), 3, '#7a7aa8', 110)
    pen.radial(None, 700, 240, 1500, [(0, '#ffe0b0', 130), (0.6, '#000000', 0), (1, '#000000', 150)], clip=False)
    _new_dress(pen, 640, 120, 1.0)
    # the clipping: newsprint, the photo, the caption, a strip of tape
    cv = pen.cv
    cv.save(); cv.translate(1390, 470); cv.rotate(3.5)
    pw, ph = 560, 420
    pen.fill(rect(-pw / 2 + 12, -ph / 2 + 18, pw, ph + 120), '#000000', 110, blur=14)
    pen.fill(rect(-pw / 2 - 26, -ph / 2 - 26, pw + 52, ph + 140), '#e9e2cc'); pen.texture(rect(-pw / 2 - 26, -ph / 2 - 26, pw + 52, ph + 140), 'paper', 0.6, 'overlay', 1.2)
    pen.fill(rect(-pw / 2, -ph / 2, pw, ph), '#8a8a84')
    cv.save(); cv.clipPath(rect(-pw / 2, -ph / 2, pw, ph), skia.ClipOp.kIntersect, True)
    ST._courier_photo(pen, -pw / 2, -ph / 2, pw, ph, t)
    cv.restore()
    pen.line(rect(-pw / 2, -ph / 2, pw, ph), 2.0, '#141414')
    ST.btext(pen, 'Laurie Price, 7, holds the paw of the Pemberton\'s', -pw / 2, ph / 2 + 42, 'serif_i', 24, '#1a1a1a', 230)
    ST.btext(pen, 'Bunnyman at Thursday\'s Easter parade.', -pw / 2, ph / 2 + 72, 'serif_i', 24, '#1a1a1a', 230)
    tape = poly([(-90, -ph / 2 - 60), (90, -ph / 2 - 52), (84, -ph / 2 + 4), (-96, -ph / 2 - 4)])
    pen.fill(tape, '#efe4b8', 210); pen.texture(tape, 'paper', 0.4, 'overlay', 0.8)
    cv.restore()


def _stairs_side(pen, ox, oy, n=7, run=330.0, rise=230.0, t=0.0):
    """The hall flight seen from the side (a cutaway, rising to the right): the white stringer and risers, the treads with
    the red runner, the brass stair rods at each nose, the dark under the flight."""
    pts = [(ox - 2 * run, oy + 3 * rise)]
    for k in range(-2, n + 1):
        x0, y0 = ox + k * run, oy - k * rise
        pts += [(x0, y0 + rise), (x0, y0)]
    pts += [(ox + (n + 1) * run, oy - n * rise), (ox + (n + 1) * run, oy + 3 * rise + 2000), (ox - 2 * run, oy + 3 * rise + 2000)]
    body = poly(pts)
    pen.fill(body, '#8c8a9c'); pen.texture(body, 'wood', 0.25, 'overlay', 2.0)                 # the white-painted stringer, at night
    pen.linear(body, 0, oy - n * rise, 0, oy + 3 * rise, [(0, '#000000', 0), (1, '#000000', 120)])
    for k in range(-2, n + 1):
        x0, y0 = ox + k * run, oy - k * rise
        riser = rect(x0 - 6, y0, 18, rise)
        pen.fill(riser, '#e8e2d4'); pen.line(riser, 2.5, '#1a1010', 200)
        tread = rect(x0, y0 - 14, run, 28)
        pen.fill(tread, '#8a2a32'); pen.texture(tread, 'fabric', 0.9, 'overlay', 2.0); pen.line(tread, 3, '#1a1010', 220)
        pen.fill(rect(x0 - 10, y0 - 10, 26, rise * 0.85), '#7a2a30', 230)                    # the runner over the nose
        rod = rrect(x0 - 16, y0 - 22, 34, 18, 9)
        pen.fill(rod, '#d8b45a'); pen.line(rod, 2, '#5a4010')
    pen.linear(body, ox, 0, ox + n * run, 0, [(0, '#000000', 40), (1, '#000000', 0)])


def _hatchet(pen, x, y, ang, s=1.0, blood=0.7):
    """The old hatchet: the head at (x, y) (blade toward local +x), the worn hickory handle along local -x; red paint
    band on the handle (the woodpile's), rust, old blood."""
    cv = pen.cv; cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s, s)
    hdl = poly([(-40, -22), (-760, -40), (-760, 18), (-40, 22)])
    pen.fill(moved(hdl, 8, 14), '#000000', 90, blur=10)
    pen.fill(hdl, '#8a6440'); pen.texture(hdl, 'wood', 0.8, 'overlay', 2.0)
    pen.fill(poly([(-40, 6), (-760, -4), (-760, 18), (-40, 22)]), '#5e4128', 170)
    pen.fill(poly([(-470, -32), (-420, -31), (-420, 20), (-470, 20)]), '#b8282e', 230)              # the red paint band
    pen.line(hdl, 4)
    hd = poly([(-70, -48), (40, -50), (170, -110), (196, 6), (170, 128), (40, 56), (-70, 50)])
    pen.fill(moved(hd, 8, 14), '#000000', 100, blur=10)
    pen.fill(hd, '#5f6268'); pen.texture(hd, 'grunge', 0.8, 'overlay', 1.4)
    pen.fill(poly([(150, -100), (170, -110), (196, 6), (170, 128), (150, 118)]), '#a8adb4')
    pen.fill(ST._blob(10, 0, 60, 40, 9, 3, 0.4), '#7b3a20', 170)
    pen.fill(ST._blob(110, 40, 34, 26, 9, 4, 0.4), '#5a1414', 200 * blood)
    pen.line(hd, 4)
    cv.restore()


def ins_hatchet_steps(pen, t, hits=(), **kw):
    """'And behind them, something hard knocking against every step.': the flight from the side (rising to the right),
    the hatchet dragged UP it by a matted paw ahead and above: its head trails on the tread below, is pulled up over each
    riser and drops onto the next tread on each hit time (a puff of dust); the frame climbs with it."""
    run, rise = 330.0, 230.0
    k_ = 0.0; ph = 0.0
    for j, th in enumerate(hits):
        if t >= th - 0.5:
            u = clamp((t - (th - 0.5)) / 0.5)
            k_ = j + ease_in_out(u); ph = u if u < 1.0 else 0.0
    cv = pen.cv
    pen.fill(rect(-400, -300, 2720, 1680), '#2c3350'); pen.texture(rect(-400, -300, 2720, 1680), 'fabric', 0.35, 'overlay', 3.0)   # the hall wallpaper
    ox, oy = 300.0, 980.0
    hx = ox + k_ * run + 150.0
    hy = oy - k_ * rise - 16.0 - 70.0 * math.sin(clamp(ph) * math.pi)
    cv.save(); cv.translate(820 - hx, 640 - hy)
    _stairs_side(pen, ox, oy, 9, run, rise, t)
    ang = 148.0 - 14.0 * math.sin(clamp(ph) * math.pi)
    _hatchet(pen, hx, hy, ang, 0.8)
    a = math.radians(ang)
    gx, gy = hx - math.cos(a) * 560, hy - math.sin(a) * 560                     # the end of the handle (the grip)
    for th in hits:
        dt = t - th
        if 0.0 <= dt < 0.5:
            for q in range(8):
                aa = math.pi * (0.08 + 0.84 * q / 7)
                r_ = 30 + 220 * dt
                pen.fill(oval(hx - 40 + math.cos(aa) * r_, hy + 6 - math.sin(aa) * r_ * 0.5, 9 - 12 * dt), '#c8b8a0', 210 * (1 - dt / 0.5))
    hero_paw(pen, 'bunny', gx + 26, gy - 20, 215, 'paw_grip', 228.0, -1, (gx + 900, gy - 900), dict(side=-1, key=-0.3))
    cv.restore()
    pen.linear(rect(-400, -300, 2720, 1680), 0, -300, 0, 1380, [(0, '#000000', 110), (0.45, '#000000', 0), (1, '#000000', 150)])


def ins_hatchet_thunk(pen, t, hit_t=0.6, **kw):
    """'Thunk.': extreme close on one tread's nose: the blade comes down and bites the runner on the brass rod, carpet
    fibres and wood splinters jump, the rod dents."""
    pen.fill(rect(-400, -300, 2720, 1680), '#140a0c')
    face = rect(-400, 520, 2720, 1200)
    pen.fill(face, '#e8e2d4'); pen.texture(face, 'wood', 0.3, 'overlay', 2.0)
    pen.linear(face, 0, 520, 0, 1380, [(0, '#000000', 40), (1, '#000000', 180)])
    top = poly([(-400, 520), (2320, 520), (2320, 120), (-400, 120)])
    pen.fill(top, '#8a2a32'); pen.texture(top, 'fabric', 1.0, 'overlay', 3.0)
    pen.fill(rrect(-400, 470, 2720, 70, 30), '#d8b45a'); pen.linear(rrect(-400, 470, 2720, 70, 30), 0, 470, 0, 540, [(0, '#fff0b8', 200), (1, '#6a4a1a', 200)])
    pen.line(rrect(-400, 470, 2720, 70, 30), 4, '#3a2a10')
    u = clamp((t - (hit_t - 0.25)) / 0.25)
    dt = t - hit_t
    by = lerp(-420, 330, ease_in_out(u)) if dt < 0 else 330 + 8 * math.exp(-dt * 10)
    _hatchet(pen, 1160, by, 78.0, 1.6)
    if dt >= 0:
        pen.fill(oval(1080, 470, 70 + 30 * min(1, dt * 6), 16), '#3a2a10', 200)
        rng = np.random.default_rng(5)
        for q in range(26):
            a_ = rng.uniform(0.15, 2.95); sp_ = rng.uniform(260, 900)
            x = 1080 + math.cos(a_) * sp_ * dt; y = 450 - math.sin(a_) * sp_ * dt + 1400 * dt * dt
            c_ = '#8a2a32' if q % 3 else '#c8a878'
            pen.seg((x, y), (x + math.cos(a_) * 16, y - math.sin(a_) * 16), 4, c_, 240 * clamp(1 - dt / 0.7))
    pen.radial(None, 1000, 400, 1400, [(0, '#000000', 0), (1, '#000000', 170)], clip=False)


def ins_hatchet_pile(pen, t, **kw):
    """'The old hatchet from our woodpile.': the hatchet dragged along the upstairs runner by a filthy, matted paw: the
    worn hickory handle with the red paint band Dad put on everything from the woodpile, wood chips and bark still stuck
    in the old blood on the head; it slides slowly out of frame."""
    pen.fill(rect(-400, -300, 2720, 1680), '#3a3040')
    floor = poly([(-400, 380), (2320, 300), (2320, 1380), (-400, 1380)])
    pen.fill(floor, '#6a4628'); pen.texture(floor, 'wood', 0.8, 'overlay', 2.4)
    run_ = poly([(-400, 520), (2320, 450), (2320, 1180), (-400, 1240)])
    pen.fill(run_, '#2c3a6a'); pen.texture(run_, 'fabric', 0.9, 'overlay', 2.6)
    for k in range(12):
        pen.line(poly([(-400 + k * 260, 560), (-400 + k * 260 + 30, 1210)], False), 3, '#1a2448', 120)
    pen.linear(rect(-400, -300, 2720, 1680), 0, -300, 0, 1380, [(0, '#ffd8b0', 40), (0.6, '#000000', 0), (1, '#000000', 160)])
    dx = -70.0 * t
    _hatchet(pen, 1280 + dx, 820, -8.0, 1.25)
    rng = np.random.default_rng(9)
    for q in range(9):
        cx_, cy_ = 1280 + dx + rng.uniform(-60, 180), 820 + rng.uniform(-90, 110)
        pen.fill(poly([(cx_, cy_), (cx_ + rng.uniform(14, 30), cy_ + rng.uniform(-6, 6)), (cx_ + rng.uniform(4, 20), cy_ + rng.uniform(8, 16))]), '#c8a070', 230)
    hero_paw(pen, 'bunny', 330 + dx, 760, 320, 'paw_grip', 262.0, -1, (-700 + dx, 600), dict(side=-1, key=-0.2), shadow=(10, 16, 16, 90))
    pen.fill(oval(1100 + dx, 905, 520, 40), '#000000', 70, blur=16)


INS_CUSTOM_EXTRA = {'egg_gold_hands': (ins_egg_gold_hands, 'ob_sunrise87'), 'dress_photo': (ins_dress_photo, 'ins_lamp'),
                    'hatchet_steps': (ins_hatchet_steps, 'ins_dark'), 'hatchet_thunk': (ins_hatchet_thunk, 'ins_dark'),
                    'hatchet_pile': (ins_hatchet_pile, 'ins_dark')}


INS_CUSTOM = {'badge': (ins_badge, 'ins_memory'), 'poster': (ins_poster, 'ins_memory'), 'wedding': (ins_wedding, 'ins_lamp'),
              'gran_photo': (ins_gran_photo, 'ins_lamp'), 'wristband': (ins_wristband, 'ins_hosp'), 'report': (ins_report, 'ins_lamp'),
              'knuckles': (ins_knuckles2, 'ins_memory'), 'desk': (ins_desk, 'ins_lamp'), 'hanger': (ins_hanger, 'ins_lamp')}
INS_CUSTOM.update(INS_CUSTOM_EXTRA)


def strike_layer(t0, x0, y0, x1, y1, w=26.0, dur=0.45, c='#d8262e'):
    """A red marker line struck through something (the outro: no Holloway, no Pemberton's)."""
    def draw(pen, t):
        u = ease_out_cubic(clamp((t - t0) / dur))
        if u <= 0: return
        pen.seg((x0, y0), (lerp(x0, x1, u), lerp(y0, y1, u)), w, c, 235)
    return Layer(0.99, draw, 'strike', blur=0)


def B_ins(F, sh):
    """A prop insert: name in sets_bunny INSERTS_B (ob_insert) or in INS_CUSTOM; kw = dict | f(t_rel) -> dict; motion;
    strike=(t, x0, y0, x1, y1) a red strike-through; c = camera (default a 3 %/s optical push)."""
    p = sh.p
    name = p['name']
    t0 = sh.t0
    if name in INS_CUSTOM:
        fn, gr = INS_CUSTOM[name]
        kw = p.get('kw') or {}
        static = not callable(kw) and not p.get('anim', False)

        def draw(pen, t, fn=fn, kw=kw):
            k_ = kw(t - t0) if callable(kw) else kw
            fn(pen, t - t0, **k_)
        lay = Layer(1.0, draw, 'insert', cache=('film:ins:%s:%s' % (name, json.dumps(kw, sort_keys=True, default=str))) if static else False,
                    bounds=(-460, -320, 2380, 1400), blur=0)
        layers = [lay]; grade = p.get('grade', gr); lens = None; sp = None
    else:
        kw = p.get('kw')
        if callable(kw):                                  # the plan's kw functions take the time since the cut
            kw = (lambda tt, f=kw: f(tt - t0))
        sp = ST.ob_insert(name, kw, p.get('motion'), t0=t0)
        layers = list(sp); grade = p.get('grade', sp.grade); lens = sp.lens
    if p.get('strike'):
        s_ = p['strike']
        layers.append(strike_layer(*s_))
    for hd in p.get('hands', []):
        layers.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                 hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand')))
    c = dict(p.get('c') or dict(mv='push', rate=0.03))
    c.setdefault('free', True)
    cam = scam(sh, None, c)
    return Spec(layers, cam, lens, grade, 1.0, 0.0, fx=_fx(sp, p), hud=p.get('hud'))


# ==================================================================================================== rule cards
RECALL_TEXT = {6: "Don't open it for anybody. *Not even me.*", 7: "Whatever happens, never close your eyes *before sunrise.*"}


def B_rule(F, sh):
    """The police rule card over the laminated sheet on the fridge (blurred, dimmed; rule n highlighted). recall=True
    re-shows the card typed out at once (no header change) with its key words pulsing red."""
    p = sh.p
    n = p['n']
    sp = ST.ob_insert('rules', dict(hl=n, show=7))
    t0 = sh.t0
    rec = p.get('recall')

    def hud(cv, t):
        if rec:
            ST.rule_card_bunny(cv, n, max(0.0, t - t0) + (6.0 if rec else 0.0), text_=RECALL_TEXT.get(n))
            u = 0.5 + 0.5 * math.sin((t - t0) * 7.0)
            pen = Pen(cv)
            pen.fill(rrect(DW / 2 - 300, 590, 600, 6, 3), H.RED, 120 + 120 * u)
        else:
            ST.rule_card_bunny(cv, n, t - t0)
    cam = scam(sh, None, dict(mv='push', rate=0.012, free=True))

    def fx(t):
        d = dict(blur=7, dim=0.42)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(list(sp), cam, None, 'ins_lamp', 1.0, 0.0, fx=fx, hud=hud)


# ==================================================================================================== the VHS pause (comment prompt)
def _img_layer(F, key_fn, name='freeze', depth=1.0, xform=None):
    """Draws a pre-rendered frame (F.freeze(t_src)) filling the design frame; xform(t) -> (dx, dy, scale) for jitter."""
    cache = {}

    def draw(pen, t):
        ts = key_fn(t)
        img = F.freeze(ts)
        k = (ts, img.shape)
        if cache.get('k') != k:
            rgba = np.dstack([img, np.full(img.shape[:2], 255, np.uint8)])
            cache['img'] = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)
            cache['k'] = k
        cv = pen.cv
        dx, dy, s = xform(t) if xform else (0.0, 0.0, 1.0)
        cv.save(); cv.translate(960 + dx, 540 + dy); cv.scale(s, s); cv.translate(-960, -540)
        cv.drawImageRect(cache['img'], skia.Rect.MakeWH(DW, DH), skia.SamplingOptions(skia.FilterMode.kLinear))
        cv.restore()
    return Layer(depth, draw, name, blur=0)


def _vhs_osd(cv, t, mode='pause', counter=258.0):
    pen = Pen(cv)
    blink = (t * 1.2) % 1.0 < 0.65
    if mode == 'pause':
        if blink:
            ST.btext(pen, 'PAUSE', 150, 130, 'vhs', 76, '#f2f2f2', 240, 'left')
            pen.fill(rect(90, 78, 18, 56), '#f2f2f2', 240); pen.fill(rect(118, 78, 18, 56), '#f2f2f2', 240)
    elif mode == 'play':
        ST.btext(pen, 'PLAY', 150, 130, 'vhs', 76, '#f2f2f2', 240, 'left')
        pen.fill(poly([(92, 76), (136, 106), (92, 136)]), '#f2f2f2', 240)
    elif mode == 'rew':
        ST.btext(pen, 'REW', 190, 130, 'vhs', 76, '#f2f2f2', 240, 'left')
        for k in range(2):
            x = 92 + k * 44
            pen.fill(poly([(x + 40, 76), (x, 106), (x + 40, 136)]), '#f2f2f2', 240)
    s = int(counter)
    ST.btext(pen, 'SP  %d:%02d:%02d' % (s // 3600, (s // 60) % 60, s % 60), 1820, 130, 'vhs', 64, '#f2f2f2', 225, 'right')


def _comment_cue(cv, t, alpha=1.0):
    """A plain comment box (no platform branding): a speech-bubble icon, 'Add a comment...' and a blinking cursor."""
    if t < 0: return
    pen = Pen(cv)
    u = ease_out_back(clamp(t / 0.45), 1.6)
    y = lerp(1180, 820, u)
    a = 255 * alpha * clamp(t / 0.2)
    box = rrect(560, y - 52, 800, 104, 52)
    pen.fill(moved(box, 0, 10), '#000000', 0.45 * a, blur=14)
    pen.fill(box, '#f4f4f2', a); pen.line(box, 3, '#d0d0d4', a)
    bub = rrect(600, y - 26, 62, 44, 12)
    pen.fill(bub, '#c0161c', a); pen.fill(poly([(612, y + 16), (604, y + 34), (630, y + 16)]), '#c0161c', a)
    for k in range(3): pen.fill(oval(616 + k * 15, y - 4, 4.5), '#ffffff', a)
    text(cv, 'Add a comment...', 690, y + 12, 600, 34, '#5a5a62', a, 0.0, 'left')
    if (t * 1.6) % 1.0 < 0.55:
        pen.fill(rect(1000, y - 22, 4, 44), '#16171c', a)


def B_pause(F, sh):
    """The comment prompt as a VHS PAUSE: mode 'freeze' (src = film time of the frozen frame; cue = s when the comment box
    slides up; push = slow zoom), 'split' (srcs=(left, right) with the labels MOM | THE BUNNYMAN; hl = 'L' | 'R' lights one;
    flicker), 'word' (ONE WORD. typed over the split, dim), 'play' (PLAY, a tracking roll and the tape running again),
    'rew' (rewinding: srcs flick backwards)."""
    p = sh.p
    mode = p.get('mode', 'freeze')
    t0 = sh.t0
    L = []
    srcs = p.get('srcs') or (p.get('src'),)
    sh.pre = [s for s in srcs if s is not None]

    def jitter(t):
        k = int(t * 12)
        return (0.0, 1.6 * (hash01(k, 3) - 0.5) * 2.0, 1.0)
    if mode in ('freeze', 'play', 'word'):
        src = p['src']
        push = p.get('push', 0.0)
        xf = (lambda t: (0.0, jitter(t)[1], 1.0 + push * clamp((t - t0) / max(0.5, sh.d))))
        if mode == 'play':
            xf = (lambda t: (0.0, (-1080.0 * ease_in_out(clamp((t - t0 - 0.25) / 0.5)) if t < t0 + 0.75 else 0.0) + jitter(t)[1], 1.0))
        L.append(_img_layer(F, lambda t, s=src: s, 'freeze', xform=xf))
        if mode == 'play':
            L.append(_img_layer(F, lambda t, s=src: s, 'freeze2', depth=1.01,
                                xform=lambda t: (0.0, 1080.0 - 1080.0 * ease_in_out(clamp((t - t0 - 0.25) / 0.5)) if t < t0 + 0.75 else 3000.0, 1.0)))
    elif mode == 'split':
        sl, sr = srcs
        for k, (s_, side) in enumerate(((sl, -1), (sr, 1))):
            def draw(pen, t, s_=s_, side=side):
                img = F.freeze(s_)
                cache = draw.__dict__.setdefault('c', {})
                if cache.get('k') != (s_, img.shape):
                    rgba = np.dstack([img, np.full(img.shape[:2], 255, np.uint8)])
                    cache['img'] = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType); cache['k'] = (s_, img.shape)
                cv = pen.cv
                x0 = 0 if side < 0 else 960
                ofs = p.get('ofs', (0.0, 0.0))[0 if side < 0 else 1]
                cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, 0, 960, 1080))
                cv.drawImageRect(cache['img'], skia.Rect.MakeXYWH(x0 - 480 + ofs, 0, DW, DH), skia.SamplingOptions(skia.FilterMode.kLinear))
                cv.restore()
            L.append(Layer(1.0 + 0.01 * k, draw, 'split%d' % k, blur=0))
        L.append(Layer(0.98, lambda pen, t: pen.fill(rect(954, -10, 12, 1100), '#0a0a0e'), 'split_line', blur=0))
    elif mode == 'rew':
        ss = list(srcs)
        per = p.get('per', 0.16)
        L.append(_img_layer(F, lambda t: ss[min(len(ss) - 1, int(max(0.0, t - t0) / per))], 'rew', xform=jitter))

    def hud(cv, t):
        u = t - t0
        osd = {'freeze': 'pause', 'split': 'pause', 'word': 'pause', 'play': 'play', 'rew': 'rew'}[mode]
        pen = Pen(cv)
        if mode != 'play' or u < 1.0:
            _vhs_osd(cv, t, osd, p.get('counter', 4 * 60 + 18) + (u if mode == 'play' else 0.0) - (u * 12 if mode == 'rew' else 0.0))
        if mode in ('split', 'word'):
            hl = p.get('hl')
            for side, lab in ((-1, 'MOM'), (1, 'THE BUNNYMAN')):
                x = 480 if side < 0 else 1440
                lit = (hl == 'L' and side < 0) or (hl == 'R' and side > 0)
                fl = p.get('flicker') == ('L' if side < 0 else 'R') and (int(u * 9) % 3 == 0)
                st = 'red' if lit else 'white'
                if not fl: H.tag(cv, lab, x, 830, st, u - (0.0 if side < 0 else 0.15), size=46)
            if mode == 'split' and not p.get('no_or'):
                text(cv, 'OR', 960, 560, 900, 64, '#ffffff', 230 * clamp(u / 0.3), 0.0, 'center', 0.8)
        if mode == 'word':
            s = 'ONE WORD.'
            n = int(clamp(u / 0.5) * len(s))
            pen.fill(rect(0, 0, DW, DH), '#000000', 120)
            text(cv, s[:n], 960, 600, 900, 150, '#ffffff', 255, 0.02, 'center', 0.8)
        if p.get('cue') is not None:
            _comment_cue(cv, t - p['cue'])
        if p.get('label'):
            for (tl, lab, x, y, st) in p['label']:
                H.tag(cv, lab, x, y, st, t - tl, size=46)
        if p.get('reply') is not None:
            _reply_cue(cv, t - p['reply'], p.get('reply_side', -1))
        # tracking noise band
        k = (t * 0.7) % 1.0
        yb = 900 + 140 * math.sin(t * 1.3)
        pen.fill(rect(0, yb, DW, 18 + 10 * k), '#ffffff', 26)
        for j in range(14):
            xx = (hash01(int(t * 30) * 17 + j, 5)) * DW
            pen.fill(rect(xx, yb + 4 + 3 * j % 18, 60 + 120 * hash01(j, 9), 2), '#ffffff', 90)

    def fx(t):
        d = dict(vhs=dict(t=t, k=0.6, curve=0.0, track=0.35 if mode != 'rew' else 1.2, bezel=0.0, glass=0.0, scan=0.5, tube=False, noise=0.8),
                 sat=0.82)
        if mode == 'play' and t - t0 < 0.8: d['vhs']['track'] = 2.2
        return d
    cam = scam(sh, None, dict(mv='hold', free=True, shake=0.0))
    spec = Spec(L, cam, None, p.get('grade', 'neutral'), 1.0, 0.0, fx=fx, hud=hud)
    spec.pre = sh.pre
    return spec


def _reply_cue(cv, t, side=-1):
    if t < 0: return
    pen = Pen(cv)
    a = 255 * clamp(t / 0.3)
    x = 480 if side < 0 else 1440
    y = 690
    pen.line(smooth([(x + 70, y - 60), (x - 40, y - 60), (x - 80, y - 20), (x - 80, y + 30)], False), 10, '#ffffff', a)
    pen.fill(poly([(x - 110, y + 20), (x - 50, y + 20), (x - 80, y + 64)]), '#ffffff', a)
    text(cv, 'REPLY', x + 40, y + 46, 800, 38, '#ffffff', a, 0.1, 'left', 0.6)


# ==================================================================================================== cards (outro) + black
def _eye_icon(pen, x, y, s, look=(0.0, 0.0), lid=0.0, a=255):
    up = poly([(x - s, y), (x - s * 0.5, y - s * 0.55 * (1 - lid)), (x + s * 0.5, y - s * 0.55 * (1 - lid)), (x + s, y)], False)
    pen.fill(smooth([(x - s, y), (x - s * 0.5, y - s * 0.56 * (1 - lid)), (x, y - s * 0.62 * (1 - lid)), (x + s * 0.5, y - s * 0.56 * (1 - lid)), (x + s, y),
                     (x + s * 0.5, y + s * 0.5 * (1 - lid)), (x, y + s * 0.56 * (1 - lid)), (x - s * 0.5, y + s * 0.5 * (1 - lid))], True, 0.9), '#f4f4f2', a)
    if lid < 0.9:
        cx, cy = x + look[0] * s * 0.35, y + look[1] * s * 0.2
        pen.fill(oval(cx, cy, s * 0.36 * (1 - lid * 0.5)), '#3a6a8a', a); pen.fill(oval(cx, cy, s * 0.17), '#0a0a10', a)
        pen.fill(oval(cx - s * 0.1, cy - s * 0.1, s * 0.06), '#ffffff', a)
    pen.line(smooth([(x - s, y), (x - s * 0.5, y - s * 0.56 * (1 - lid)), (x, y - s * 0.62 * (1 - lid)), (x + s * 0.5, y - s * 0.56 * (1 - lid)), (x + s, y),
                     (x + s * 0.5, y + s * 0.5 * (1 - lid)), (x, y + s * 0.56 * (1 - lid)), (x - s * 0.5, y + s * 0.5 * (1 - lid))], True, 0.9), 10, '#ffffff', a)


def _thumb(pen, x, y, s, a=255):
    pen.fill(rrect(x - s * 0.62, y - s * 0.05, s * 0.3, s * 0.72, s * 0.06), '#ffffff', a)
    pen.fill(smooth([(x - s * 0.25, y - s * 0.05), (x - s * 0.05, y - s * 0.6), (x + s * 0.12, y - s * 0.62), (x + s * 0.08, y - s * 0.2),
                     (x + s * 0.55, y - s * 0.2), (x + s * 0.6, y + s * 0.05), (x + s * 0.45, y + s * 0.62), (x - s * 0.25, y + s * 0.67)], True, 0.5), '#ffffff', a)


def B_card(F, sh):
    """Graphic cards: mode 'trick' (THE TRICK: close your eyes / count to seven), 'eye' (an open eye looking round), 'safe'
    (so you never did), 'like' (a like that lands like a knock: hit at p['hit_t']), 'next' (next time: a phone ringing on a
    nightstand at 3:00 AM, the doctor), 'title' (the channel: NIGHT POLICY), 'end'."""
    p = sh.p
    mode = p['mode']
    t0 = sh.t0
    bgc = p.get('bgc', ('#141622', '#06070c'))
    L = [Layer(3.0, lambda pen, t: pen.linear(rect(-600, -400, 3120, 1880), 0, -400, 0, 1480, list(bgc)), 'card_bg',
               cache='film:card_bg:%s' % (bgc,), bounds=(-600, -400, 2520, 1480))]

    def hud(cv, t):
        u = t - t0
        pen = Pen(cv)
        if mode == 'trick':
            text(cv, 'THE TRICK ONLY WORKS IF YOU', 960, 330, 800, 44, '#b8b8c4', 255 * clamp(u / 0.3), 0.12, 'center', 0.6)
            for k, (tk, s_) in enumerate(p['steps']):
                if t >= tk: H.tag(cv, s_, 960, 520 + k * 150, 'white', t - tk, size=58)
        elif mode == 'eye':
            look = (math.sin(u * 2.1) * 0.9, 0.3 * math.sin(u * 1.3))
            _eye_icon(pen, 960, 520, 300, look, 0.0, 255 * clamp(u / 0.25))
        elif mode == 'safe':
            _eye_icon(pen, 960, 430, 220, (0.0, 0.0), 0.0, 255)
            if u > 0.2:
                text(cv, 'SO YOU NEVER DID.', 960, 800, 900, 78, '#ffffff', 255 * clamp((u - 0.2) / 0.2), 0.04, 'center', 0.7)
        elif mode == 'like':
            th = p.get('hit_t', t0 + 0.4)
            v = t - th
            if v > -0.25:
                s = 1.0 + 0.55 * clamp(-v / 0.25) if v < 0 else 1.0 + 0.06 * math.exp(-v * 9) * math.cos(v * 40)
                a = 255 * clamp((v + 0.25) / 0.12)
                cv.save(); cv.translate(960, 520); cv.scale(s, s); cv.translate(-960, -520)
                pen.fill(oval(960, 520, 230), H.RED, a); _thumb(pen, 960, 520, 230, a)
                cv.restore()
                if v > 0.05: text(cv, 'LIKE', 960, 870, 900, 70, '#ffffff', 255 * clamp((v - 0.05) / 0.2), 0.2, 'center', 0.6)
        elif mode == 'next':
            text(cv, 'NEXT TIME ON', 960, 150, 800, 34, '#a8a8b8', 255 * clamp(u / 0.3), 0.3, 'center', 0.6)
            text(cv, CHANNEL, 960, 225, 900, 64, '#ffffff', 255 * clamp(u / 0.4), 0.12, 'center', 0.7)
            H.phone(cv, 'incoming', u, name='DR. HALVERSON', x=960, y=640, scale=0.72, hand=False)
            text(cv, '3:00 AM', 960, 335, 800, 44, '#e3262e', 255 * clamp((u - 0.6) / 0.3), 0.2, 'center', 0.6)   # above the phone (at 1000 the caption covered it)
        elif mode == 'title':
            text(cv, CHANNEL, 960, 560, 900, 96, '#ffffff', 255 * clamp(u / 0.6) * (1 - clamp((u - sh.d + 0.6) / 0.5)), 0.12, 'center', 0.7)
        elif mode == 'end':
            pass
    cam = scam(sh, None, dict(mv='hold', free=True, shake=0.0))
    return Spec(L, cam, None, 'neutral', 1.0, 0.0, fx=lambda t: dict(p.get('post', {})), hud=hud)


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
SPACE = {'living': 'inside', 'hall': 'inside', 'up': 'inside', 'june': 'inside', 'bath': 'bath', 'attic': 'attic', 'kitchen': 'inside',
         'yard': 'outside', 'front': 'outside', 'woods': 'woods', 'hosp': 'hospital', 'parade': 'vhs'}


def shot_space(s):
    if s.kind in ('rule', 'black', 'card'): return None
    if s.kind == 'pause': return 'vhs'
    if s.kind == 'ins': return 'close'
    if s.p.get('era') == '1987' and (s.p.get('room') == 'parade' or (s.p.get('bg') or [''])[0] == 'parade'): return 'vhs'
    if s.p.get('era') == 'memory': return 'memory'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind == 'bust': return {'hosp': 'hospital', 'yard': 'outside', 'front': 'outside', 'woods': 'woods', 'parade': 'vhs'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('1987', 'memory', 'outro', 'recall'): return s.p['era']
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if room in ('hosp',): return 'hospital'
    if room in ('woods',): return 'woods'
    if s.kind in ('rule', 'card', 'black', 'pause'): return s.kind
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
                if e['name'].startswith('footsteps') and a.who in ('bunny', 'bunny87'): pr['heavy'] = True
                sh.sfx.append(_ev(e['t'], e['name'], g, e.get('pan', 0.0), space, **pr))
    c = p.get('c') or {}
    if c.get('snap'):
        sh.sfx.append(_ev(c['snap'][0], 'whoosh', -4, 0, None, kind='hard'))
    for tg in p.get('tags', []):
        if p.get('tag_sound', True): sh.sfx.append(_ev(tg[0], 'ui_pop', -6, 0, 'close'))
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
        tm = H.rule_times(ST.RULE_CARDS[n])
        sh.sfx.append(_ev(sh.t0 + tm['pop'], 'ui_pop', 0, 0, 'close'))
        if not p.get('recall'):
            sh.sfx.append(_ev(sh.t0 + tm['type0'], 'typing', -6, 0, 'close', dur=round(tm['type1'] - tm['type0'], 2), cps=14))
            sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.75})
            sh.music.append({'t': round(sh.t0, 3), 'type': 'riser', 'level': 0.5, 'len': 3.5})
            sh.sfx.append(_ev(sh.t0 + 0.02, 'magnet_click', -8, 0, 'close'))
        else:
            sh.sfx.append(_ev(sh.t0 + 0.05, 'stinger', -6, 0, None, kind='recall'))
    if sh.kind == 'pause':
        mode = p.get('mode')
        if mode in ('freeze',) and p.get('first'):
            sh.sfx.append(_ev(sh.t0, 'vhs_pause', 0, 0, 'vhs', kind='pause'))
            sh.music.append({'t': round(sh.t0, 3), 'type': 'silence', 'level': 0.0, 'len': round(min(19.0, F.t(100) - sh.t0 - 1.0), 2), 'kind': 'pause'})
        if mode == 'play':
            sh.sfx.append(_ev(sh.t0 + 0.2, 'vhs_pause', 0, 0, 'vhs', kind='play'))
        if mode == 'rew':
            sh.sfx.append(_ev(sh.t0, 'vhs_pause', 0, 0, 'vhs', kind='rewind', dur=round(sh.d, 2)))
        if p.get('cue') is not None:
            sh.sfx.append(_ev(p['cue'], 'ui_pop', -4, 0, 'close', kind='comment'))
    if sh.kind == 'card' and p['mode'] == 'like':
        sh.sfx.append(_ev(p.get('hit_t', sh.t0 + 0.4), 'knock_door', 2, 0, 'close', n=1, kind='like'))
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
EXPO = {'ins': -0.05}


def glob_fx(F, sh, t, fx):
    """Per-frame global effects: cut flashes; the night creeping into red from the window smash (600 s) to the slam, a
    gold dawn that holds it back, then the climax ramp from Mom's hand over June's eyes (770 s) through the counts with
    a red heartbeat wash at the frame edge until "Seven." (912.7 s: a white flash); the aftermath drained; 1987 / memory /
    hospital / outro clean; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    elif c == 'vhs' and u < 0.18: fx['glitch'] = 0.6 * (1 - u / 0.18)
    ek = EXPO.get(sh.kind, 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('1987', 'memory', 'outro') or sh.kind in ('rule', 'black', 'card', 'pause') or (sh.p.get('room') == 'hosp') or \
        ((sh.p.get('bg') or [''])[0] == 'hosp')
    if not clean:
        ui = 0.5 if sh.kind in ('ins',) or era == 'recall' else 1.0
        dawn = clamp((t - 709.0) / 3.0) * (1.0 - clamp((t - 770.0) / 10.0))
        k = clamp((t - 600.0) / 80.0) * (1.0 - 0.75 * dawn)
        k2 = clamp((t - 664.0) / 16.0) * (1.0 - clamp((t - 683.0) / 6.0))
        k3 = clamp((t - 770.0) / 18.0) if t < 913.0 else 0.0
        kk = max(k, k3)
        if kk > 0 or k2 > 0:
            fx['red'] = fx.get('red', 0.0) + (0.38 * kk + 0.3 * k2 + 0.12 * k3) * ui
            fx['sat'] = fx.get('sat', 1.0) * (1 + (0.4 * kk + 0.25 * k2) * ui)
            fx['exposure'] = fx.get('exposure', 0.0) - (0.25 * kk + 0.3 * k2) * ui
        if 783.6 <= t < 912.7 and 'flash' not in fx:
            bpm = lerp(72, 138, clamp((t - 783.6) / 128.0))
            ph = ((t - 783.6) * bpm / 60.0) % 1.0
            beat = math.exp(-ph * 9.0) + 0.6 * math.exp(-max(0.0, ph - 0.18) * 11.0) * (ph >= 0.18)
            ramp = clamp((t - 783.6) / 3.0) * (0.5 + 0.5 * clamp((t - 884.0) / 25.0))
            fx['flash'] = _epost.Spill(0.4 * ramp * clamp(beat) * ui, side=-1.0 if sh.idx % 2 else 1.0, color=(0.06, 0.08, 0.9), reach=0.8)
        if 913.0 <= t < 950.0:
            fx['sat'] = fx.get('sat', 1.0) * 0.72
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time (the sound step maps the names): the night outside, the house's room tone, the 1987
    parade crowd on the camcorder, the woods, the hospital hum, the dawn birds, the tape hiss under the VHS pause."""
    t, e = F.t, F.e
    D = F.duration
    out = []
    out.append(_ev(0.0, 'ambience_night', -10, 0, 'outside', dur=round(t(3) - 0.2, 2), crickets=0.5, wind=0.5, dog=0.1))
    out.append(_ev(t(3) - 0.1, 'crowd_parade', -6, 0, 'vhs', dur=round(t(8) - t(3) + 0.1, 2), cheer=1.0, vhs=True))
    out.append(_ev(t(8), 'room_tone', -14, 0, 'inside', dur=round(t(16) - t(8), 2)))
    out.append(_ev(t(16) - 0.1, 'room_tone', -8, 0, 'hospital', dur=round(t(19) - t(16), 2), kind='hospital_hum'))
    out.append(_ev(t(19) - 0.1, 'crowd_parade', -6, 0, 'vhs', dur=round(t(29) - t(19) + 0.1, 2), cheer=0.8, vhs=True))
    out.append(_ev(t(29) - 0.1, 'ambience_woods', -10, 0, 'woods', dur=round(t(39) - t(29), 2), tod='day', birds=0.4))
    out.append(_ev(t(39) - 0.1, 'ambience_night', -8, 0, 'outside', dur=round(t(54) - t(39), 2), crickets=0.6, wind=0.6, dog=0.15))
    out.append(_ev(t(54) - 0.1, 'room_tone', -10, 0, 'inside', dur=round(t(61) - t(54), 2), kind='house_evening'))
    house0 = t(61) - 0.1
    out.append(_ev(house0, 'room_tone', -6, 0, 'inside', dur=round(t(322) - house0, 2), kind='house_night'))
    out.append(_ev(house0, 'ambience_night', -16, 0, 'outside', dur=round(t(286) - house0, 2), crickets=0.5, wind=0.7, dog=0.1, through_walls=True))
    out.append(_ev(t(286), 'ambience_dawn', -12, 0, 'outside', dur=round(t(371) - t(286), 2), birds=0.7, through_walls=True))
    out.append(_ev(t(371) - 0.1, 'room_tone', -8, 0, 'hospital', dur=round(t(386) - t(371), 2), kind='hospital_hum'))
    out.append(_ev(t(386) + 1.0, 'room_tone', -14, 0, 'inside', dur=round(D - t(386) - 1.0, 2), kind='warm_room'))
    out.append(_ev(t(92) - 0.1, 'tape_hiss', -10, 0, 'vhs', dur=round(t(100) - t(92), 2)))
    # the song from the woods: slow and tinny, a speaker with dying batteries (heard outside, through the glass)
    out.append(_ev(F.w(65, 'starts'), 'jingle', -8, 0.2, 'outside', dur=round(t(91) - F.w(65, 'starts'), 2), version='tinny_woods', loop=True))
    out.append(_ev(t(206) - 0.2, 'bulb_hum', -14, 0, 'attic', dur=round(t(232) - t(206), 2)))
    out.append(_ev(t(370) - 0.2, 'sirens', -10, 0, 'outside', dur=6.0, far=True))
    out.append(_ev(t(370) + 2.0, 'police_radio', -16, 0, 'outside', dur=6.0))
    return out


INTENSITY = [  # (seconds, level): the story's tension, read off the beats
    (0.0, 0.55), (10.8, 0.65), (16.9, 0.7), (17.9, 0.4), (26.8, 0.35), (33.3, 0.55), (38.4, 0.5), (44.8, 0.45), (54.7, 0.6),
    (58.5, 0.4), (65.9, 0.3), (84.8, 0.35), (93.2, 0.5), (99.7, 0.6), (103.3, 0.5), (113.9, 0.6), (117.8, 0.55), (122.3, 0.6),
    (127.0, 0.7), (134.1, 0.65), (136.3, 0.35), (145.5, 0.4), (149.6, 0.5), (153.6, 0.55), (160.8, 0.7), (162.3, 0.6), (168.7, 0.65),
    (171.2, 0.4), (176.8, 0.5), (183.9, 0.55), (187.7, 0.6), (191.6, 0.65), (200.4, 0.6), (208.3, 0.7), (215.8, 0.65), (219.3, 0.8),
    (227.2, 0.75), (230.2, 0.6), (239.1, 0.8), (245.4, 0.9), (248.6, 1.0), (257.1, 0.95), (258.1, 0.2), (279.6, 0.6), (287.6, 0.55),
    (294.4, 0.65), (303.2, 0.5), (314.6, 0.55), (317.8, 0.7), (323.4, 0.75), (328.2, 0.9), (336.6, 0.6), (340.2, 0.75), (343.4, 0.85),
    (352.9, 0.7), (356.5, 0.8), (359.1, 0.65), (369.1, 0.7), (376.5, 0.85), (383.1, 0.8), (386.0, 0.45), (397.0, 0.55), (404.0, 0.7),
    (406.9, 0.85), (410.5, 0.9), (416.4, 0.65), (425.4, 0.75), (435.4, 0.9), (444.8, 0.75), (455.4, 0.65), (461.0, 0.8), (466.0, 0.85),
    (473.3, 0.95), (479.3, 0.85), (484.3, 0.7), (488.5, 0.75), (494.8, 0.8), (496.6, 0.65), (503.5, 0.5), (508.6, 0.7), (513.1, 0.85),
    (520.1, 0.8), (522.8, 0.65), (547.3, 0.75), (561.6, 0.85), (571.3, 0.95), (575.3, 0.85), (580.2, 0.95), (586.8, 0.9), (589.9, 0.7),
    (600.0, 1.0), (608.4, 0.95), (611.8, 0.8), (616.6, 0.9), (623.7, 1.0), (628.5, 0.9), (635.9, 0.95), (640.7, 0.8), (659.6, 0.85),
    (664.4, 0.9), (670.1, 1.0), (680.5, 1.0), (683.1, 0.3), (687.5, 0.55), (692.3, 0.7), (698.2, 0.6), (709.2, 0.5), (716.5, 0.6),
    (725.1, 0.75), (731.2, 0.85), (737.2, 0.8), (743.0, 0.85), (750.9, 0.9), (766.6, 1.0), (768.5, 0.7), (770.4, 0.8), (776.9, 0.85),
    (783.7, 0.9), (789.0, 0.75), (791.6, 0.6), (816.6, 0.65), (830.9, 0.7), (844.6, 0.8), (853.0, 0.75), (884.4, 0.9), (889.5, 0.95),
    (897.5, 1.0), (911.0, 1.0), (912.7, 1.0), (914.4, 0.85), (931.2, 0.9), (937.2, 0.95), (939.2, 0.6), (950.8, 0.4), (962.9, 0.45),
    (973.6, 0.6), (979.0, 0.75), (986.4, 0.9), (989.5, 0.95), (993.9, 0.15), (1005.5, 0.2), (1028.5, 0.25), (1046.9, 0.3),
    (1063.4, 0.45), (1072.2, 0.2), (1077.4, 0.1)]


def intensity_curve(F):
    pts = [[round(t, 2), round(v, 3)] for t, v in INTENSITY]
    pts.append([round(F.duration, 2), 0.0])
    return pts


HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left): (time, length)
EXTRA_SIL = [(247.6, 0.9), (327.4, 0.8), (369.4, 1.2), (434.6, 0.8), (519.3, 0.8), (600.6, 0.9), (669.1, 1.0), (682.9, 1.6),
             (729.9, 1.0), (749.9, 1.0), (765.8, 0.8), (910.0, 0.9), (912.2, 0.5), (985.6, 0.9)]
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
    for t, ln in EXTRA_SIL:
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
    if os.environ.get('FILM_DEV'):
        return plan_dev(F)
    return plan_film(F)


def plan_dev(F):
    """Staging calibration: one shot per builder (FILM_DEV=1)."""
    C = F.cut
    C(0.0, 'set', room='living', view='wide2', set=dict(lamp=1.0),
      ppl=[P('narrator', 'couch_left', expr='haunted'), P('june', 'couch_mid')])
    C(3.0, 'bust', who='mom', bg=('kitchen', 'back'), set=dict(kitchen=1.0), expr='too_still', cx=960, cy=600, scale=0.8)
    C(6.0, 'ins', name='egg', kw=dict(rattle=lambda t: math.sin(t * 20) * clamp(t - 1.0)))
    C(9.0, 'rule', n=1)
    C(12.0, 'ins', name='badge')
    C(15.0, 'card', mode='like', hit_t=15.5)
    C(18.0, 'black')


def plan_film(F):
    plan_open(F)
    plan_1987(F)
    plan_since(F)
    plan_rule1(F)
    plan_pause(F)
    plan_rule2(F)
    plan_rule3(F)
    plan_rule4(F)
    plan_rule5(F)
    plan_rule6(F)
    plan_rule7(F)
    plan_reveal(F)
    plan_after(F)
    plan_outro(F)
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


# ==================================================================================================== PLAN (sections below)
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


def VHS_STREET(t0, t1, y0, y1):
    return lambda tt: lerp(y0, y1, clamp((tt - t0) / max(0.1, t1 - t0)))


# ==================================================================================================== COLD OPEN (0 - 65.75)
def plan_open(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    # 0 "If you ever see a man in a bunny suit standing at the edge of the woods on Easter night, don't wave at him."
    tcut = w(0, 'on', 1) if w(0, 'on', 1) > 3.0 else w(0, 'easter') - 0.3
    tw = w(0, 'wave')
    C(0.0, 'set', room='yard', view='woods', set=dict(tod='night'), rim=MOON,
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.25, act=pose(-9, None, 0.1, h_tilt=-3.0))],
      c=dict(mv='push', f=2.45, rate=0.035), music=[(0.0, 'drone', 0.45, 7.0)],
      sfx=[(0.3, 'wind_gust', -8, 0, 'outside')])
    C(tcut - LEAD, 'set', room='yard', view='close', rim=MOON,
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15,
             act=_A(tilt(tcut + 0.3, -9.0, 1.6), lambda a, s: a.wave(tw - 0.15, s.t1 + 1.5, side=1, slow=True)))],
      c=dict(mv='push', f=1.3, rate=0.02))
    # 1 "If he leaves an egg on your porch, don't open it."   (the egg rocks once on 'open')
    to = w(1, 'open')
    C(T(1), 'set', room='front', view='egg', cam=cm((-0.18, -1.05, 0.30), (-0.38, -0.36, 0.0), S=1700, sx=960, sy=640),
      set=dict(egg=True, egg_rattle=lambda tt, to=to: 0.9 * math.sin((tt - to) * 24.0) * math.exp(-max(0.0, tt - to) * 3.5) * (tt > to)),
      c=dict(mv='push', f=1.0, rate=0.035), sfx=[(to + 0.02, 'egg_rattle', -4, 0, 'outside', dict(n=3))])
    # 2 "And if anyone, anyone at all, asks you to close your eyes and count to seven... don't."  Mom, too still, leans in;
    #   her open hand comes up toward the lens on 'close your eyes' and covers it on 'seven'; black on "don't"
    tc, ts = w(2, 'close'), w(2, 'seven')

    def lens_hand(tt, tc=tc, ts=ts):
        # her open hand rises from below frame toward the lens; as it nears the glass it goes soft (out of focus) and dark
        # (it blocks the light), and the palm covers the frame on 'seven'
        if tt < tc - 0.1: return None
        u = ease_in_out(clamp((tt - tc) / max(0.4, ts + 0.45 - tc)))
        size = lerp(470.0, 2700.0, u ** 1.8)
        blur = 34.0 * clamp((size - 1100.0) / 1500.0)
        dark = 0.75 * clamp((size - 1300.0) / 1400.0)
        return (lerp(1250.0, 990.0, u), lerp(1380.0, 560.0 + size * 0.40, u), 182.0, 1.0, size, blur, dark)
    C(T(2), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.0), bg_dim=0.5, expr='too_still', cx=960, cy=610, scale=0.88, long_ok=True,
      act=_A(pose(t(2), None, 3.5, approach=0.16), tilt(w(2, 'anyone', 1), 9.0, 1.7), lookxy(960, 540, t(2) - 0.5, None, 0.5, z=400.0)),
      light=dict(rim='#ffcf8f', rim_a=55, side=-1, key=-0.3),
      hands=[dict(who='mom', fn=lens_hand, size=430, shape='open', side=-1, sleeve_from=lambda tt: (1560, 1500), depth=0.5)],
      post_fn=lambda tt, ts=ts: dict(fade=clamp((tt - ts - 0.25) / 0.3)), c=dict(mv='push', zrate=0.01),
      sfx=[(tc, 'cloth_rustle', -8, 0, 'close')], music=[(ts + 0.3, 'silence', 0.0, 1.2)])

    # 3-6 the jingle on the camcorder tape: the Pemberton's Easter parade, April 1987 (VHS), the cheering crowd
    t3, t4, t5, t6, t7 = T(3), T(4), T(5), T(6), T(7)
    fy = VHS_STREET(t3, t4, 21.0, 16.5)
    C(t3, 'set', room='parade', view='street', era='1987', cut='vhs', set=dict(float_y=fy),
      ppl=[P('bunny87', (0.0, fy(t3) + 2.2, 1.25), path=[(t3, (0.0, fy(t3) + 2.2, 1.25)), (t4, (0.0, fy(t4) + 2.2, 1.25))], no_walk=True,
             linear=True, turn=0.1, act=_A(lambda a, s: a.hold_prop('basket', -1), lambda a, s: a.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01),
                                           lambda a, s: a.wave(s.t0, s.t1 + 1.0, side=1, speed=0.8)), room_light=False)],
      c=dict(mv='push', f=2.1, rate=0.02),
      music=[(t3, 'jingle', 0.9, 8.5, dict(version='vhs_parade'))], sfx=[(t3 + 0.05, 'crowd_cheer', -2, 0, 'vhs')])
    C(t4, 'set', room='parade', view='photo', era='1987', tape0=1.7,
      ppl=[P('bunny87', 'float_deck', turn=0.25, room_light=False,
             act=_A(lambda a, s: a.hold_prop('basket', -1), lambda a, s: a.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01),
                    lambda a, s: a.wave(s.t0 - 0.5, s.t1 + 0.5, side=1, speed=0.9)))],
      c=dict(mv='push', f=1.35, rate=0.02))
    # "Close your eyes and count to seven." the mascot covers his glass eyes with both paws (peek-a-boo), then drops them
    pk1 = e(5) - 0.35
    C(t5, 'set', room='parade', view='photo', era='1987', tape0=3.8,
      cam=cm((-2.3, 20.9, 2.2), (0.0, 24.2, 2.55), S=1500, sx=960, sy=560),
      ppl=[P('bunny87', 'float_deck', turn=-0.1, room_light=False,
             act=_A(lambda a, s: a.reach_to(t(5) + 0.05, 1, (a, 'eye_l'), t1=pk1, dur=0.45, contact='palm', shape='paw_flat', z=110.0, fade=0.35),
                    lambda a, s: a.reach_to(t(5) + 0.1, -1, (a, 'eye_r'), t1=pk1, dur=0.45, contact='palm', shape='paw_flat', z=110.0, fade=0.35),
                    tilt(pk1 + 0.1, 12.0, 1.2)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # "Find an egg that fell from heaven." he lifts a plastic egg out of his basket and tosses it up over the crowd
    tt_ = w(6, 'egg') - 0.25

    def toss_acts(A, s, sp, tt_=tt_):
        a = A['bunny87']
        a.hold_prop('egg', 1, s.t0 - 1.0, tt_ + 0.45)
        a.reach(s.t0 + 0.1, tt_ + 0.6, 1, out=60.0, down=120.0, fwd=170.0, shape='grip', up=0.0, fade=0.35)
        a.reach(tt_, tt_ + 0.9, 1, out=110.0, down=-160.0, fwd=120.0, shape='paw_open', up=1.0, fade=0.4)

        def egg(pen, tt):
            if tt < tt_ + 0.45: return
            u = tt - (tt_ + 0.45)
            x0, y0 = a.grip_point(tt_ + 0.45, 1, 'egg')
            x = x0 + 520.0 * u; y = y0 - 700.0 * u + 900.0 * u * u
            ST.draw_egg(pen, x, y, 120.0, rot=200.0 * u, col='#f4a8c4', stamp=False)
        lay = Layer(spot_of(sp, 'float_deck').depth, egg, 'toss_egg', blur=0)
        lay.order = 0.5
        return [lay]
    C(t6, 'set', room='parade', view='photo', era='1987', tape0=6.1, cam=cm((-2.9, 19.9, 2.0), (0.0, 24.2, 2.35), S=1150, sx=900, sy=560),
      ppl=[P('bunny87', 'float_deck', turn=0.3, room_light=False,
             act=_A(lambda a, s: a.hold_prop('basket', -1), lambda a, s: a.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01)))],
      acts=toss_acts, c=dict(mv='push', f=1.0, rate=0.015), sfx=[(tt_ + 0.5, 'crowd_cheer', -4, 0, 'vhs', dict(kind='kids'))])
    # 7 "That's the jingle from Pemberton's Department Store, Easter of 1987." the float passes the store
    fy7 = VHS_STREET(t7, T(8), 14.0, 27.0)
    C(t7, 'set', room='parade', view='store', era='1987', tape0=9.0, set=dict(float_y=fy7),
      ppl=[P('bunny87', (0.0, fy7(t7) + 2.2, 1.25), path=[(t7, (0.0, fy7(t7) + 2.2, 1.25)), (T(8), (0.0, fy7(T(8)) + 2.2, 1.25))], no_walk=True,
             linear=True, turn=1.0, room_light=False,
             act=_A(lambda a, s: a.hold_prop('basket', -1), lambda a, s: a.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01),
                    lambda a, s: a.wave(s.t0, s.t1 + 1.0, side=1, speed=0.7)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 8 the Holloway Courier: GIRL, 7, MISSING AFTER EASTER PARADE;  9 "She was seven years old." -> the photo
    C(T(8), 'ins', name='courier', cut='vhs', c=dict(mv='keys', keys=[(T(8), 960, 330, 1.0, None, 1.55), (T(9), 960, 345, 1.0, 'push', 1.7)]),
      sfx=[(T(8) + 0.05, 'paper', -10, 0, 'close', dict(kind='newspaper'))])
    C(T(9), 'ins', name='courier', c=dict(mv='keys', keys=[(T(9), 735, 660, 1.0, None, 1.75), (T(10), 740, 655, 1.0, 'push', 1.95)]))
    # 10 "Three days later, she walked out of the woods." 1987 sunrise, the woods' edge: little Laurie walks out alone
    C(T(10), 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      ppl=[P('laurie87', (-2.55, 41.6, -0.45), path=[(T(10), (-2.55, 41.6, -0.45)), (T(11) + 0.4, (-2.6, 38.0, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False, act=_A(lambda a, s: a.hold_prop('egg_gold', 1), lambda a, s: a.reach(-1.0, None, 1, out=0.0, down=160.0, fwd=130.0, shape='grip', up=0.0, fade=0.01), hum(t(10), None, 0.6)))],
      c=dict(mv='push', f=1.75, rate=0.02))
    # 11 "And she has been humming it ever since." Mom (now) humming in the kitchen, far away
    C(T(11), 'bust', who='mom', bg=('kitchen', 'back'), set=dict(kitchen=1.0), expr='too_still', cx=900, cy=620, scale=0.82, turn=0.3, h_turn=0.05,
      act=_A(hum(t(11) - 0.3, None), lookxy(1500, 520, t(11) - 1.0, None, 0.5, z=500.0)), light=LAMP,
      music=[(t(11), 'jingle', 0.5, 3.0, dict(version='hum'))], sfx=[(t(11) - 0.2, 'hum', -8, 0, 'close', dict(who='mom', dur=2.8))])
    # 12 "Every Easter Eve, my mother taped seven rules to our fridge."  Mom presses the laminated sheet under the bunny magnet
    tm = w(12, 'taped')

    def fridge_acts(A, s, sp, tm=tm):
        m = A['mom']
        tgt = scr(sp, 'fridge_rules', 0, -10)
        sheet = scr(sp, (-4.21, 7.74, 0.86))                      # the sheet as the fridge draws it (the anchor sits 0.6 m too high)
        magnet = scr(sp, (-4.21, 7.74, 1.09))
        m.reach_to(tm - 0.35, -1, sheet, t1=e(12) + 0.2, dur=0.55, contact='palm', shape='flat', z=-60.0)
        m.reach_to(tm - 0.05, 1, magnet, t1=e(12) + 0.2, dur=0.5, contact='tips', shape='point', z=-60.0)
        m.look_at(s.t0, sheet, None, 0.4)
        return []
    C(T(12), 'set', room='kitchen', view='fridge', set=dict(kitchen=1.0, rules=1.0), rim=LAMP_R, cam=cm((-2.35, 6.35, 1.5), (-4.25, 7.75, 1.25), S=980, sx=900, sy=560),
      ppl=[P('mom', 'fridge', expr='too_still', act=hum(t(12), None, 0.6))], acts=fridge_acts,
      c=dict(mv='push', f=1.1, rate=0.02), sfx=[(tm + 0.25, 'magnet_click', -4, 0, 'inside'), (tm, 'paper', -10, 0, 'inside', dict(kind='laminate'))])
    C(w(12, 'seven') - 0.15, 'ins', name='rules', kw=dict(hl=0, show=7), c=dict(mv='keys', keys=[(w(12, 'seven') - 0.15, 960, 430, 1.0, None, 1.15), (T(13), 960, 470, 1.0, 'push', 1.25)]))
    # 13-14 "We followed every one of them. Every single rule was true." the sheet; the highlighter band runs down it
    C(T(13), 'ins', name='rules', kw=dict(hl=0, show=7), c=dict(mv='keys', keys=[(T(13), 960, 520, 1.0, None, 1.4), (T(14), 960, 640, 1.0, 'push', 1.5)]))
    C(T(14), 'ins', name='rules', kw=lambda tr: dict(hl=1 + min(6, int(tr / 0.27)), show=7),
      c=dict(mv='keys', keys=[(T(14), 960, 400, 1.0, None, 1.3), (T(15), 960, 760, 1.0, 'lin', 1.3)]))
    # 15 "And not one of them was written to protect us from him."  the Bunnyman at the treeline
    C(T(15), 'set', room='yard', view='close', set=dict(tod='night'), rim=MOON,
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.2, act=_A(pose(-9, None, 0.1, h_tilt=6.0), lambda a, s: a.head_down(t(15) + 1.2, None, 0.25, 1.4)))],
      c=dict(mv='push', f=1.6, rate=0.03),
      music=[(e(15) - 0.3, 'hit', 0.6)])
    # 16 "I'm telling you this from a hospital."  a woman in a gown on the bed, her back to us, facing the window
    C(T(16), 'set', room='hosp', view='room', era='now', rim=HOSP,
      ppl=[P('mom_hosp', 'window', expr='haunted', act=pose(-9, None, 0.1, h_nod=0.12))], c=dict(mv='push', f=1.1, rate=0.015),
      sfx=[(T(16), 'heart_monitor', -16, 0.3, 'hospital', dict(kind='far'))])
    # 17 "The doctors here are very kind."  the doctor in the doorway with his clipboard, a kind smile, a nod
    C(T(17), 'set', room='hosp', view='room', rim=HOSP, cam=cm((10.9, 6.5, 1.5), (9.45, 2.75, 1.35), S=950, sx=960, sy=520),
      ppl=[P('doctor', 'door', face=(10.3, 5.0), expr='warm_smile', act=_A(lambda a, s: a.hold_prop('clipboard', -1),
                                                          lambda a, s: a.reach(-1.0, None, -1, out=10.0, down=160.0, fwd=190.0, shape='grip', up=0.0, fade=0.01),
                                                          lambda a, s: a.head_down(t(17) + 0.4, t(17) + 1.0, 0.35, 0.4)))],
      c=dict(mv='push', f=1.15, rate=0.015))
    # 18 "They just don't believe a word I say."  the doctor's kind smile; he writes without looking up
    C(T(18), 'bust', who='doctor', bg=('hosp', 'room'), expr='warm_smile', cx=1000, cy=600, scale=0.78, turn=-0.25, light=HOSP,
      act=_A(lambda a, s: a.hold_prop('clipboard', -1), lambda a, s: a.reach(-1.0, None, -1, out=10.0, down=60.0, fwd=210.0, shape='grip', up=0.0, fade=0.01),
             lambda a, s: a.head_down(t(18) + 0.6, None, 0.5, 0.5)),
      sfx=[(t(18) + 0.7, 'pen_write', -10, 0, 'hospital')])


# ==================================================================================================== 1987 (65.75 - 122.2)
BASKET = lambda a, s: (a.hold_prop('basket', -1), a.reach(-1.0, None, -1, out=40.0, down=230.0, fwd=150.0, shape='grip', up=0.0, fade=0.01))
PHOTO_CAM = None
# the Courier photo's two-shot, IN FRONT of the float (the old 'photo' anchor stood them behind it: the float's deck hid
# them): Laurie and the mascot by the float's front corner, Pemberton's behind them
PHOTO_TWO = cm((0.25, 18.4, 1.2), (2.6, 21.6, 1.0), S=1150, sx=960, sy=560)
PHOTO_TRICK = cm((0.6, 19.0, 1.0), (2.65, 21.65, 0.85), S=1500, sx=960, sy=560)


def plan_1987(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    # 19 "In 1987, at the Easter parade in Holloway, the Bunnyman rode the last float, handing out plastic eggs."
    th = w(19, 'handing')
    fy = VHS_STREET(T(19), th, 22.0, 17.5)
    C(T(19), 'set', room='parade', view='street', era='1987', cut='vhs', tape0=40.0, set=dict(float_y=fy),
      ppl=[P('bunny87', (0.0, fy(T(19)) + 2.2, 1.25), path=[(T(19), (0.0, fy(T(19)) + 2.2, 1.25)), (th, (0.0, fy(th) + 2.2, 1.25))], no_walk=True,
             linear=True, turn=0.15, room_light=False, act=_A(BASKET, lambda a, s: a.wave(s.t0, s.t1 + 1.0, side=1, speed=0.8)))],
      c=dict(mv='push', f=2.0, rate=0.02), sfx=[(T(19) + 0.05, 'crowd_cheer', -4, 0, 'vhs')],
      music=[(T(19), 'jingle', 0.55, 7.0, dict(version='vhs_parade', distant=True))])
    # ... handing out plastic eggs: he kneels at the edge of the float and holds an egg out to the crowd
    C(th - 0.1, 'set', room='parade', view='photo', era='1987', tape0=46.0, cam=cm((-2.6, 20.2, 1.9), (0.0, 24.2, 2.2), S=1500, sx=960, sy=560),
      ppl=[P('bunny87', 'float_deck', turn=0.55, room_light=False,
             act=_A(BASKET, lambda a, s: a.kneel_down(s.t0 - 0.6, 0.5, knees=0), lambda a, s: a.hold_prop('egg', 1, s.t0 - 1.0, s.t1 + 1.0),
                    lambda a, s: a.reach(s.t0 + 0.1, None, 1, out=150.0, down=120.0, fwd=170.0, shape='grip', up=0.0, fade=0.5), tilt(th + 0.3, 8.0, 1.5)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 20 "Big grey suit."  the mascot full figure on the deck, arms out wide
    C(T(20), 'set', room='parade', view='photo', era='1987', tape0=48.0, cam=cm((-2.2, 20.3, 1.8), (0.0, 24.2, 2.25), S=1300, sx=960, sy=540),
      ppl=[P('bunny87', 'float_deck', turn=0.05, room_light=False,
             act=_A(lambda a, s: a.reach(t(20) - 0.1, None, 1, out=230.0, down=-20.0, fwd=40.0, shape='paw_open', up=0.0, fade=0.45),
                    lambda a, s: a.reach(t(20), None, -1, out=230.0, down=-20.0, fwd=40.0, shape='paw_open', up=0.0, fade=0.45)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 21 "Black glass eyes."   22 "Buck teeth and a stitched-on smile."  (the clean mascot, close, on the tape)
    C(T(21), 'bust', who='bunny87', bg=('parade', 'photo'), era='1987', tape0=50.0, cx=960, cy=700, scale=1.25, light=VHS87,
      act=tilt(t(21) + 0.2, 6.0, 1.4), post=dict(vhs=dict(k=0.55, curve=0.0, track=0.25, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.6)),
      post_fn=lambda tt: {'vhs': dict(t=tt, k=0.55, curve=0.0, track=0.25, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.6)})
    C(T(22), 'bust', who='bunny87', bg=('parade', 'photo'), era='1987', tape0=52.0, cx=960, cy=300, scale=2.0, light=VHS87,
      act=pose(t(22), None, 0.6, h_tilt=-5.0), c=dict(mv='push', x=960, y=620, zrate=0.025),
      post_fn=lambda tt: {'vhs': dict(t=tt, k=0.55, curve=0.0, track=0.25, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.6)})
    # 23 "Inside it was a nineteen-year-old stock boy named Dale Whitlock."  his Pemberton's name badge on the fur
    C(T(23), 'ins', name='badge', era='1987', c=dict(mv='keys', keys=[(T(23), 960, 560, 1.0, None, 1.0), (T(24), 960, 550, 1.0, 'push', 1.08)]))
    # 24 "There's a photo from that morning."  the Courier photo
    C(T(24), 'ins', name='courier', c=dict(mv='keys', keys=[(T(24), 760, 640, 1.0, None, 1.45), (T(25), 745, 660, 1.0, 'push', 1.6)]),
      sfx=[(T(24) + 0.05, 'paper', -12, 0, 'close', dict(kind='newspaper'))])
    # 25 "A little girl in a yellow Easter dress, holding his paw."  the photo, live: Laurie holds the mascot's paw; the flash
    tf = w(25, 'paw') + 0.35

    def photo_acts(A, s, sp):
        # posing for the Courier's photographer: hand in paw, Laurie looks up at him and back to the lens, he waves his
        # free paw at the crowd; the flash pops on 'paw'
        b, l = A['bunny87'], A['laurie87']
        b.hold_hand(s.t0 - 1.0, -1, l, 1, dur=0.01)
        l.look_at(s.t0 - 0.5, (b, 'eyes'), tf - 0.9, 0.35)
        l.look_at(tf - 0.8, (900, 380), None, 0.35, z=500.0)
        b.look_at(s.t0 - 0.5, (1500, 420), tf - 0.7, 0.4, z=400.0)
        b.look_at(tf - 0.6, (900, 380), None, 0.4, z=500.0)
        b.wave(s.t0 + 0.2, tf - 0.4, side=1, speed=0.9, height=1.0)
        l.expr('kid_grin', tf - 0.7, None, 0.3)
        return []
    C(T(25), 'set', room='parade', view='photo', era='1987', tape0=58.0, cam=PHOTO_TWO,
      ppl=[P('bunny87', (2.95, 21.75, 0.0), turn=-0.15, room_light=False, dorder=-4.0),
           P('laurie87', (2.25, 21.45, 0.0), turn=0.2, expr='warm_smile', room_light=False, dorder=-4.0)],
      acts=photo_acts, c=dict(mv='push', f=1.0, rate=0.012),
      post_fn=lambda tt, tf=tf: dict(white=0.9 * clamp(1.0 - (tt - tf) / 0.25) if tt >= tf else 0.0),
      sfx=[(tf, 'camera_flash', -2, 0, 'vhs')])
    # 26 "Laurie Price."   27 "My mom."  (the same face, now)
    C(T(26), 'bust', who='laurie87', bg=('parade', 'photo'), era='1987', tape0=62.0, cx=960, cy=600, scale=0.95, light=VHS87, expr='warm_smile',
      act=tilt(t(26) + 0.1, 7.0, 1.2), post_fn=lambda tt: {'vhs': dict(t=tt, k=0.5, curve=0.0, track=0.22, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.5)})
    C(T(27), 'bust', who='mom', bg=('living', 'wide'), set=dict(lamp=1.0), cx=960, cy=600, scale=0.95, light=LAMP, expr='too_still', era='now')
    # 28 "He showed her a magic trick."  he kneels to her and makes a plastic egg appear by her ear, then gives it to her
    tg = t(28) + 0.15

    def trick_acts(A, s, sp, tg=tg):
        b, l = A['bunny87'], A['laurie87']
        egg = CH.PropTrack('egg', 0, 0, sp.anchors['photo'].ppm / 100.0)
        egg.held(-1e9, b, 1)
        b.hold_prop('egg', 1, -1e9, None)
        b.reach_to(tg - 0.6, 1, (l, 'eye_l'), t1=tg + 0.25, dur=0.45, contact='grip', shape='grip', prop='egg', z=70.0, fade=0.3)
        b.give(egg, tg + 0.4, 1, l, -1, dur=0.9)
        l.look_at(tg - 0.6, (b, 'hand_l'), tg + 1.3, 0.25)
        l.look_at(tg + 1.4, (b, 'eyes'), None, 0.35)
        b.look_at(s.t0 - 1.0, (l, 'eyes'), None, 0.3)
        l.expr('kid_grin', tg + 0.3, None, 0.3)
        return []
    C(T(28), 'set', room='parade', view='photo', era='1987', tape0=64.0, cam=PHOTO_TRICK,
      ppl=[P('bunny87', (3.05, 21.8, 0.0), turn=-0.6, kind='kneel', knees=0, room_light=False, dorder=-4.0),
           P('laurie87', (2.25, 21.45, 0.0), turn=0.55, expr='warm_smile', room_light=False, dorder=-4.0)],
      acts=trick_acts, c=dict(mv='push', f=1.0, rate=0.012), sfx=[(tg + 0.2, 'magic_sparkle', -10, 0, 'vhs')])
    # 29 "Then he walked off into Holloway Woods."  30 "And she followed him."  (1987, overcast)
    C(T(29), 'set', room='woods', view='path', set=dict(tod='day87'), era='1987', vhs=False, rim=MEMORY, grade='ob_memory',
      ppl=[P('bunny87', (-4.6, -2.6, 0.0), path=[(T(29), (-4.6, -2.6, 0.0)), (T(30) + 0.3, (-1.8, 4.6, 0.0))], surface='grass', room_light=False, dimk=0.1)],
      c=dict(mv='push', f=1.1, rate=0.02))
    C(T(30), 'set', room='woods', view='path', set=dict(tod='day87'), era='1987', vhs=False, rim=MEMORY, grade='ob_memory',
      cam=cm((-6.3, -5.2, 0.9), (-2.4, 3.0, 0.7), S=1000, sx=960, sy=600),
      ppl=[P('bunny87', (-2.0, 4.1, 0.0), path=[(T(30), (-2.0, 4.1, 0.0)), (T(31), (-1.3, 7.6, 0.0))], surface='grass_quiet', room_light=False, dimk=0.35),
           P('laurie87', (-4.9, -2.4, 0.0), path=[(T(30), (-4.9, -2.4, 0.0)), (T(31) + 0.2, (-3.0, 2.6, 0.0))], surface='grass', room_light=False)],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 31 "The search dogs lost her scent at the old railroad bridge."  the trestle, overcast; then the Courier's sub-headline
    tb = w(31, 'old') - 0.1
    C(T(31), 'set', room='woods', view='bridge', set=dict(tod='day87'), era='1987', vhs=False, rim=MEMORY, grade='ob_memory',
      ppl=[P('cop', (-5.4, 6.6, 0.0), face=(0.0, 9.0), expr='sad', room_light=False, act=lookp((0.0, 9.0, 1.0), -1.0, None, 0.3))],
      c=dict(mv='push', f=1.15, rate=0.02), sfx=[(T(31) + 0.2, 'dogs_bark_far', -10, 0.4, 'woods')])
    C(tb, 'ins', name='courier', c=dict(mv='keys', keys=[(tb, 1300, 470, 1.0, None, 2.2), (T(32), 1300, 470, 1.0, 'push', 2.4)]))
    # 32 "Three days later, at sunrise on Easter morning, she walked out of the trees alone."
    tsw = w(32, 'walked') - 0.1
    LAURIE_EGG = _A(lambda a, s: a.hold_prop('egg_gold', 1), lambda a, s: a.reach(-1.0, None, 1, out=0.0, down=160.0, fwd=130.0, shape='grip', up=0.0, fade=0.01))
    C(T(32), 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      ppl=[P('laurie87', (-2.5, 44.6, -0.45), path=[(T(32) + 0.2, (-2.5, 44.6, -0.45)), (tsw, (-2.5, 42.9, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False, act=LAURIE_EGG)],
      c=dict(mv='push', f=1.45, rate=0.012), sfx=[(T(32) + 0.3, 'birds_dawn', -8, 0, 'outside')])
    C(tsw, 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      cam=cm((-2.62, 36.2, 0.7), (-2.55, 41.0, 0.35), S=1250, sx=960, sy=600),
      ppl=[P('laurie87', (-2.5, 42.9, -0.45), path=[(tsw, (-2.5, 42.9, -0.45)), (T(33) + 0.2, (-2.6, 39.0, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False, act=LAURIE_EGG)],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 33 "Her dress was spotless."  medium, walking toward us in the gold light
    C(T(33), 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      cam=cm((-2.62, 34.6, 0.6), (-2.6, 38.2, 0.2), S=1300, sx=960, sy=600),
      ppl=[P('laurie87', (-2.6, 38.9, -0.45), path=[(T(33), (-2.6, 38.9, -0.45)), (T(34), (-2.6, 37.6, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False, act=LAURIE_EGG)],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 34 the golden plastic egg;  35 "And she was humming."  36 "She didn't remember a thing."
    C(T(34), 'ins', name='egg_gold_hands', era='1987', anim=True, c=dict(mv='push', rate=0.025))
    C(T(35), 'bust', who='laurie87', bg=('yard', 'close', None), set=dict(tod='sunrise87'), era='1987', vhs=False, cx=960, cy=590, scale=0.9,
      light=SUN87, expr='too_still', act=hum(t(35) - 0.2, None), grade='ob_sunrise87',
      sfx=[(t(35), 'hum', -10, 0, 'outside', dict(who='laurie87', dur=1.4))], music=[(t(35), 'jingle', 0.5, 2.0, dict(version='hum_child'))])
    C(T(36), 'bust', who='laurie87', bg=('yard', 'close', None), set=dict(tod='sunrise87'), era='1987', vhs=False, cx=1100, cy=640, scale=1.0,
      turn=-0.55, light=SUN87, expr='too_still', grade='ob_sunrise87',
      act=_A(pose(t(36) + 0.5, None, 0.8, smile=0.35, still=0.6), lookxy(960, 520, t(36) - 1.0, None, 0.3, z=500.0)))
    # 37 "Dale Whitlock was never found."  the missing poster;  38 "Neither was the suit."  the empty woods at night
    C(T(37), 'ins', name='poster', era='1987', c=dict(mv='keys', keys=[(T(37), 960, 520, 1.0, None, 1.05), (T(38), 960, 600, 1.0, 'push', 1.3)]))
    C(T(38), 'set', room='woods', view='path', set=dict(tod='night', flashlight=0.0), rim=MOON, c=dict(mv='push', f=1.2, rate=0.03),
      sfx=[(T(38) + 0.2, 'wind_gust', -10, 0, 'woods')])


# ==================================================================================================== EVERY EASTER SINCE / THE HOUSE / DAD / THIS EASTER (122.2 - 191.5)
BELLY_CAM = cm((-2.6, 37.3, 0.65), (-2.6, 39.6, 0.55), S=1500, sx=960, sy=520)


def plan_since(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    # 39 "But every Easter since, somebody sees him at the edge of the woods."  through June's window: him at the treeline
    C(T(39), 'set', room='june', view='out', set=dict(curtains=1.0), rim=MOON,
      ppl=[P('bunny', 'bunny_treeline', room_light=False, dimk=0.3, act=pose(-9, None, 0.1, h_tilt=-5.0))],
      c=dict(mv='push', f=2.2, rate=0.03), music=[(T(39), 'swell', 0.5, 6.0)])
    # 40 "Fur matted dark."  41 "One ear snapped."  (close, moonlight)
    C(T(40), 'bust', who='bunny', bg=('yard', 'close'), cx=960, cy=560, scale=1.15, light=MOON, act=pose(-9, None, 0.1, h_turn=0.15))
    C(T(41), 'bust', who='bunny', bg=('yard', 'close'), cx=900, cy=650, scale=0.9, turn=0.45, light=MOON, act=tilt(t(41), 14.0, 1.4))
    # 42 "The belly stained rust-brown."  a medium on the belly, the chest breathing
    C(T(42), 'set', room='yard', view='close', cam=BELLY_CAM, rim=MOON,
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15)], c=dict(mv='push', f=1.0, rate=0.02))
    # 43 "Just standing there."  44 "Watching the houses."  (over his shoulder to the lit house)
    C(T(43), 'set', room='yard', view='close', rim=MOON, ppl=[P('bunny', 'treeline', room_light=False, dimk=0.2)], c=dict(mv='push', f=1.1, rate=0.012))
    C(T(44), 'set', room='yard', view='house', set=dict(kitchen=1.0, june_light=0.8), rim=MOON,
      ppl=[P('bunny', (-2.05, 39.95, -0.45), turn=1.92, room_light=False, dimk=0.35, act=pose(-9, None, 0.1, h_tilt=4.0))],
      c=dict(mv='push', f=1.0, rate=0.02), focus=10.0)
    # 45 "Mom grew up, married my dad, and moved us into her childhood home: the last house on Orchard Road, where the backyard
    #    ends at the woods."  the wedding photo on the mantel; the house on Orchard Road; the yard and the woods
    tmv, twh = w(45, 'moved') - 0.1, w(45, 'where') - 0.1
    C(T(45), 'ins', name='wedding', c=dict(mv='keys', keys=[(T(45), 960, 520, 1.0, None, 1.0), (tmv, 960, 500, 1.0, 'push', 1.12)]))
    C(tmv, 'set', room='front', view='house', set=dict(front_light=1.0), c=dict(mv='push', f=1.0, rate=0.02),
      tags=[(w(45, 'last') - 0.05, 'ORCHARD ROAD', 960, 230, 'white', 2.4)])
    C(twh, 'set', room='yard', view='wide', set=dict(kitchen=1.0), c=dict(mv='push', f=1.0, rate=0.02))
    # 46 "Every Easter, Grandma left the porch light on all night."  her hand flips it on; the light burning over the yard
    t46 = T(46); tp = w(46, 'porch') - 0.1

    def gran_finger(on):
        def fn(tt):
            u = ease_in_out(clamp((tt - t46 - 0.15) / 0.45)); v = ease_in_out(clamp((tt - t46 - 1.2) / 0.45))
            k = u * (1.0 - v)
            if k <= 0: return None
            y = (lerp(560, 470, ease_in_out(clamp((tt - t46 - 0.55) / 0.25))) if on else lerp(470, 600, ease_in_out(clamp((tt - t46 - 0.55) / 0.25))))
            return (lerp(1500, 975, k), y + (1 - k) * 300, 168.0 if on else 200.0, 1.0)
        return fn
    # her finger lands on the lever's tip and pushes it up (the wrist follows the fingertip, the cardigan sleeve to the
    # frame edge): no floating finger
    C(t46, 'ins', name='switch', era='memory', grade='ins_memory', kw=lambda tr: dict(flip=lambda tt: ease_in_out(clamp((tt - 0.55) / 0.22))),
      hands=[dict(who='grandma', fn=switch_finger(t46, True, 'grandma'), size=600, shape='point', side=-1,
                  sleeve_from=lambda tt: (2250, 1500))],
      c=dict(mv='push', rate=0.02), sfx=[(t46 + 0.6, 'light_switch', -2, 0, 'close')])
    C(tp, 'set', room='yard', view='house', set=dict(back_light=1.0, kitchen=0.6), era='memory', grade='ob_ext', c=dict(mv='push', f=1.4, rate=0.02))
    # 47 "And every Easter, Mom switched it off."  her finger pushes the switch down; the porch light dies
    t47 = T(47); toff = w(47, 'switched')
    C(t47, 'ins', name='switch', kw=lambda tr, a=toff - t47: dict(flip=lambda tt: 1.0 - ease_in_out(clamp((tt - a) / 0.22))),
      hands=[dict(who='mom', fn=switch_finger(t47, False, 'mom', t_flip=toff - t47, hold=0.7), size=600, shape='point', side=-1,
                  sleeve_from=lambda tt: (2300, -500))],
      c=dict(mv='push', rate=0.02), sfx=[(toff + 0.02, 'light_switch', -2, 0, 'close')])
    C(toff + 0.45, 'set', room='yard', view='house', set=dict(back_light=dict(off=toff + 0.85), kitchen=0.6), c=dict(mv='push', f=1.4, rate=0.02),
      sfx=[(toff + 0.85, 'bulb_tink', -10, 0, 'outside')])
    # 48 "Last Easter, Dad walked out to the treeline with a flashlight."  down the yard, the beam swinging ahead of him
    t48 = T(48)
    C(t48, 'set', room='yard', view='woods', set=dict(tod='night'), rim=MOON, era='memory',
      ppl=[P('dad', (-3.25, 13.6, -0.45), path=[(t48, (-3.25, 13.6, -0.45)), (T(49) + 0.6, (-3.0, 19.5, -0.45))], surface='grass', room_light=False, dimk=0.1,
             torch=dict(side=1, length=1.3, spread=13.0, a=0.85),
             act=_A(lambda a, s: a.hold_prop('maglite', 1), lambda a, s: a.reach(-1.0, None, 1, out=40.0, down=180.0, fwd=200.0, shape='grip', up=0.0, fade=0.01),
                    pose(-1.0, None, 0.01, torch_ang=8.0)))],
      c=dict(mv='push', f=1.15, rate=0.02), sfx=[(t48 + 0.1, 'flashlight_click', -6, 0, 'outside')])
    # 49 "He said he was going to talk to it."  Dad on the back porch, the flashlight up, his eyes on the woods (lips still)
    C(T(49), 'bust', who='dad', bg=('yard', 'woods'), era='memory', cx=880, cy=600, scale=0.85, turn=1.4, h_turn=-0.55, expr='determined', light=TORCH,
      act=_A(lambda a, s: a.hold_prop('maglite', 1), lambda a, s: a.reach(-1.0, None, 1, out=40.0, down=60.0, fwd=220.0, shape='grip', up=0.0, fade=0.01)))
    # 50 "He never came back."  the beam at the treeline goes in among the trees and is gone
    t50 = T(50)
    C(t50, 'set', room='yard', view='woods', set=dict(tod='night'), rim=MOON, era='memory', montage=True,
      ppl=[P('dad', (-2.75, 36.5, -0.45), path=[(t50, (-2.75, 36.5, -0.45)), (T(51) + 0.2, (-2.5, 41.6, -0.45))], surface='grass_quiet', room_light=False, dimk=0.35,
             torch=dict(side=1, length=1.4, spread=13.0, a=0.8),
             act=_A(lambda a, s: a.hold_prop('maglite', 1), lambda a, s: a.reach(-1.0, None, 1, out=40.0, down=180.0, fwd=200.0, shape='grip', up=0.0, fade=0.01),
                    pose(-1.0, None, 0.01, torch_ang=4.0)))],
      c=dict(mv='push', f=2.6, rate=0.03))
    # 51 "The police found his flashlight under the railroad bridge, still on."
    C(T(51), 'set', room='woods', view='under', set=dict(flashlight=1.0), rim=MOON, c=dict(mv='push', f=1.0, rate=0.025),
      sfx=[(T(51) + 0.2, 'creek', -10, 0, 'woods', dict(dur=3.8))])
    # 52 "Mom told them he'd left us."  the house at dawn, two patrol cars, the light bars sweeping
    C(T(52), 'set', room='front', view='house', set=dict(tod='blue', police=dict(mode='sweep', strength=0.5)), c=dict(mv='push', f=1.15, rate=0.02),
      sfx=[(T(52), 'police_radio', -14, 0, 'outside', dict(dur=1.6))])
    # 53 "Mom told them a lot of things."  her face in the red / blue light, the smallest smile
    C(T(53), 'bust', who='mom', bg=('front', 'porch'), set=dict(tod='blue'), cx=1000, cy=600, scale=0.9, turn=-0.3, expr='too_still', light=POLICE,
      act=pose(t(53) + 0.5, None, 0.8, smile=0.5), post_fn=lambda tt: {'flash': _epost.police_flash(tt, 0.35, 1.0, 'sweep')})
    # 54 "This Easter, my little sister June turned seven."  June on her bed, beaming
    # sitting on the edge of her bed, legs dangling, seen from the doorway at 3/4 (front-on, a seated child read as
    # standing ON the bed)
    C(T(54), 'set', room='june', view='bed', set=dict(lamp=1.0, nightlight=1.0), rim=LAMP, cam=cm((0.55, 6.05, 3.95), (1.8, 7.7, 3.45), S=1050, sx=960, sy=540),
      ppl=[P('june', (2.05, 7.85, 3.37), kind='floor', face=(0.55, 6.05), expr='kid_grin', check=False, seat_ok=True,
             act=_A(lambda a, s: a.wave(t(54) + 0.3, t(54) + 1.6, side=1, speed=1.2), lookxy(600, 420, -9, None, 0.3, z=400.0)))],
      tags=[(w(54, 'seven') - 0.1, 'JUNE  ·  7', 960, 200, 'white', 2.0)], c=dict(mv='push', f=1.0, rate=0.02))
    # 55 "The same age Mom was."  Laurie in 1987 -> June now, the same framing
    tm = w(55, 'mom') - 0.15
    C(T(55), 'bust', who='laurie87', bg=('parade', 'photo', PHOTO_CAM), era='1987', vhs=True, osd=False, cx=960, cy=600, scale=0.9, light=VHS87, expr='warm_smile',
      post_fn=lambda tt: {'vhs': dict(t=tt, k=0.5, curve=0.0, track=0.22, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.5)})
    C(tm, 'bust', who='june', bg=('june', 'bed'), set=dict(lamp=1.0), cx=960, cy=600, scale=0.9, light=LAMP, expr='warm_smile')
    # 56 "All week, Mom's been humming that jingle."  Mom at the kitchen sink, her back to us, swaying on the beat
    C(T(56), 'set', room='kitchen', view='back', set=dict(kitchen=1.0), rim=LAMP_R, cam=cm((-1.6, 6.4, 1.55), (-1.4, 9.0, 1.2), S=1050, sx=960, sy=560),
      ppl=[P('mom', 'sink', expr='too_still', act=_A(hum(t(56) - 0.3, None), lambda a, s: a.reach(-1.0, None, 1, out=10.0, down=150.0, fwd=180.0, shape='relaxed', up=0.0, fade=0.01),
                                                     lambda a, s: a.reach(-1.0, None, -1, out=10.0, down=150.0, fwd=180.0, shape='relaxed', up=0.0, fade=0.01)))],
      c=dict(mv='push', f=1.0, rate=0.02), sfx=[(t(56) - 0.2, 'hum', -8, 0, 'inside', dict(who='mom', dur=2.6)), (T(56), 'water_tap', -14, 0, 'inside', dict(dur=2.5))],
      music=[(t(56), 'jingle', 0.5, 2.6, dict(version='hum'))])
    # 57 "And yesterday, she bought June a new Easter dress."  58 "Yellow."  59 "Exactly like the one in the photo."
    C(T(57), 'set', room='june', view='door', set=dict(dress=True, lamp=1.0), rim=LAMP, cam=cm((0.75, 7.75, 4.15), (-0.37, 6.45, 3.95), S=1000, sx=760, sy=520),
      c=dict(mv='push', f=1.0, rate=0.02))
    C(T(58), 'ins', name='dress_new', c=dict(mv='push', rate=0.03))
    # the new dress on the closet door and, taped beside it, the 1987 clipping: the same dress (a short move from one to
    # the other, on 'photo')
    C(T(59), 'ins', name='dress_photo', c=dict(mv='keys', keys=[(T(59), 860, 560, 1.0, None, 1.08), (w(59, 'photo') - 0.2, 860, 560, 1.0, None, 1.08),
                                                             (T(60), 1240, 520, 1.0, 'in_out', 1.45)]))
    # 60 "At sundown, the rules went up on the fridge."  her hand presses the bunny magnet onto the sheet
    t60 = T(60); tup = w(60, 'rules')
    C(t60, 'ins', name='rules', kw=dict(hl=0, show=7, magnet=True),
      hands=[dict(who='mom', fn=(lambda tt, a=tup: (lerp(1500, 1010, ease_in_out(clamp((tt - a + 0.4) / 0.5))),
                                                     lerp(-150, 60, ease_in_out(clamp((tt - a + 0.4) / 0.5))), 160.0,
                                                     1.0 - ease_in_out(clamp((tt - a - 1.0) / 0.4)))), size=480, shape='flat', side=-1, sleeve_from=lambda tt: (2000, -300))],
      c=dict(mv='keys', keys=[(t60, 960, 360, 1.0, None, 1.25), (T(61), 960, 420, 1.0, 'push', 1.35)]),
      grade='ins_lamp', post=dict(exposure=-0.05), sfx=[(tup + 0.1, 'magnet_click', -2, 0, 'close')])


# ==================================================================================================== RULE 1: THE TREELINE (191.5 - 258.0)
JUNE_FROM_WINDOW = cm((1.55, 9.55, 4.15), (0.95, 6.6, 3.95), S=900, sx=960, sy=500)        # inside June's room, back to the window


CURT0 = 0.8                         # the front curtains before 11:07: open, their edges within a teenager's reach of the middle


def curtains_close(t0, dur=1.25):
    return lambda tt: CURT0 * (1.0 - ease_in_out(clamp((tt - t0) / dur)))


def plan_rule1(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(61), 'rule', n=1)
    # 65 "At 11:07, the song starts."  the kitchen clock;  66 "From the woods."  the dark treeline
    C(T(65), 'ins', name='clock', kw=dict(time=(11, 7)), c=dict(mv='push', rate=0.03), sfx=[(T(65) + 0.1, 'clock_tick', -10, 0, 'close', dict(dur=2.4))])
    C(T(66), 'set', room='yard', view='woods', set=dict(tod='night'), c=dict(mv='push', f=2.0, rate=0.03))
    # 67 "Slow and tinny, like a speaker with dying batteries."  the narrator alone on the couch looks up toward the back
    C(T(67), 'set', room='living', view='wide2', set=dict(lamp=1.0, curtains=CURT0), rim=LAMP,
      ppl=[P('narrator', 'couch_mid', turn=0.62, expr='haunted', act=_A(lookxy(1700, 420, t(67) + 0.2, None, 0.45, z=400.0), blinks(t(67) + 1.6)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    # 68 "Hop... hop... hop along."  close: listening, eyes to the back of the house
    C(T(68), 'bust', who='narrator', bg=('living', 'wide2'), set=dict(lamp=1.0, curtains=CURT0), cx=900, cy=600, scale=0.85, turn=0.4, h_turn=0.15, expr='haunted', light=LAMP,
      act=_A(lookxy(1750, 480, t(68) - 0.5, None, 0.4, z=500.0), blinks(t(68) + 1.3)))
    # 69 "I close the curtains downstairs, then run up to June's room."
    tcl = w(69, 'close') + 0.1; trun = w(69, 'then') - 0.1
    cf = curtains_close(tcl + 0.3)

    def curtain_acts(A, s, sp, cf=cf, tcl=tcl):
        n = A['narrator']
        cl, cr, mid = plan_xy(sp, 'curtain_front_l'), plan_xy(sp, 'curtain_front_r'), (-3.3, 0.12, 1.3)
        fl = lambda tt: scr(sp, tuple(lerp(cl[j], mid[j], 1.0 - cf(tt)) for j in range(3)), 30.0, 0)
        fr = lambda tt: scr(sp, tuple(lerp(cr[j], mid[j], 1.0 - cf(tt)) for j in range(3)), -30.0, 0)
        # facing the window (back to us) her LEFT hand is on the east curtain (screen left), her right on the west one
        # (the hands used to cross over to the far curtains and missed them by a hand's length)
        n.reach_to(tcl - 0.1, 1, fl, t1=s.t1 + 0.5, dur=0.4, contact='palm', shape='grip', z=-90.0)
        n.reach_to(tcl - 0.05, -1, fr, t1=s.t1 + 0.5, dur=0.4, contact='palm', shape='grip', z=-90.0)
        return []
    C(T(69), 'set', room='living', view='window', set=dict(lamp=1.0, curtains=CURT0), curtains_fn=cf, rim=LAMP,
      ppl=[P('narrator', 'window_front', expr='haunted')], acts=curtain_acts, c=dict(mv='push', f=1.05, rate=0.02),
      sfx=[(tcl + 0.3, 'curtain_draw', -4, 0, 'inside', dict(dur=1.2))])
    C(trun, 'set', room='hall', view='foot', set=dict(hall=1.0, upstairs=1.0), rim=LAMP,
      ppl=[P('narrator', (-1.6, 2.35, 0.0), path=[(trun, (-1.6, 2.35, 0.0)), (trun + 0.75, (0.8, 1.2, 0.19)), (T(70) + 0.15, 'step13')], run=True, surface='stairs',
             turn=1.95, enter=True)],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 70 "June is at her window in her pajamas, waving."  (the narrator comes in behind her)
    C(T(70), 'set', room='june', view='window', set=dict(nightlight=1.0, curtains=1.0, hall=1.0), rim=MOON,
      ppl=[P('june', 'window', expr='warm_smile', act=lambda a, s: a.wave(s.t0 - 0.5, s.t1 + 1.0, side=1, speed=0.8, height=1.1)),
           P('narrator', (0.95, 6.75, 2.85), path=[(T(70) + 0.1, (0.95, 6.75, 2.85)), (T(70) + 1.9, 'window_side')], expr='haunted', turn=-1.8, enter=True)],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='june')
    # 71 "At the treeline, under the moon, there he is."  through her window
    C(T(71), 'set', room='june', view='out', set=dict(curtains=1.0), rim=MOON,
      ppl=[P('bunny', 'bunny_treeline', room_light=False, dimk=0.25)], c=dict(mv='keys', keys=[(T(71), 960, 540, 1.0, None, 1.0), (w(71, 'there') + 0.6, 960, 540, 1.0, 'in_out', 2.4), (T(72), 960, 540, 1.0, 'lin', 2.5)]),
      music=[(w(71, 'there'), 'hit', 0.55)])
    # 72 "Taller than my dad."  73 "Black glass eyes that don't reflect anything."
    # low, at his feet, looking up: he towers (taller than Dad); his head tips down toward the house
    C(T(72), 'set', room='yard', view='close', rim=MOON, cam=cm((-2.5, 36.6, 0.05), (-2.6, 39.6, 1.05), S=1150, sx=960, sy=600),
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15, act=_A(pose(-9, None, 0.1, h_tilt=-4.0), lambda a, s: a.head_down(t(72) + 0.2, None, 0.3, 1.0)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(73), 'bust', who='bunny', bg=('yard', 'close'), cx=960, cy=640, scale=1.5, light=MOON, c=dict(mv='push', x=960, y=540, zrate=0.025),
      act=pose(-9, None, 0.1, h_tilt=-3.0))
    # 74-75 "And he's waving back. Slowly."
    C(T(74), 'set', room='yard', view='close', rim=MOON, cam=cm((-2.6, 33.5, 1.0), (-2.6, 39.6, 1.0), S=1700, sx=960, sy=520),
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15, act=lambda a, s: a.wave(t(74) - 0.1, s.t1 + 3.0, side=1, slow=True))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 76-79 June whispers at the window: "That's Mister Bunny ... He waves at me every year. He's sad."  (lips on J only)
    C(T(76), 'bust', who='june', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0), cx=900, cy=600, scale=0.88, turn=-0.15, h_turn=0.0,
      expr='warm_smile', light=MOON, act=_A(lookxy(1100, 380, -9, None, 0.3, z=700.0), ex('sad', t(79) - 0.2, None, 0.5),
                                              lambda a, s: a.wave(s.t0 - 1.0, w(78, 'every'), side=1, speed=0.7, height=0.9)))
    # 80 "Every year."  81 "Nobody ever told me."
    C(T(80), 'bust', who='narrator', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0), cx=1020, cy=600, scale=0.85, turn=0.2,
      expr='haunted', light=MOON, act=_A(lookxy(700, 640, t(80) - 0.4, t(81) - 0.1, 0.35, z=300.0), lookxy(1000, 380, t(81), None, 0.4, z=700.0)))
    # 82-83 "Then the Bunnyman stops waving. He lifts one paw and points."
    tl = w(83, 'lifts')
    C(T(82), 'set', room='yard', view='close', rim=MOON, cam=cm((-2.6, 33.5, 1.0), (-2.6, 39.6, 1.0), S=1700, sx=960, sy=520),
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15,
             act=_A(lambda a, s: a.wave(s.t0 - 2.0, t(82) + 0.5, side=1, slow=True),
                    lambda a, s: a.point_at(tl, (960, 470), None, side=-1, dur=0.9, z=900.0)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 84 "Not at June."  85 "Not at me."  86 "Past us."
    C(T(84), 'bust', who='june', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0), cx=900, cy=610, scale=0.9, turn=-0.15, expr='nervous',
      light=MOON, act=lookxy(1100, 360, -9, None, 0.3, z=700.0))
    C(T(85), 'bust', who='narrator', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0), cx=1040, cy=610, scale=0.9, turn=0.15, expr='haunted',
      light=MOON, act=lookxy(1000, 360, -9, None, 0.3, z=700.0))
    C(T(86), 'set', room='yard', view='close', rim=MOON, cam=cm((-5.2, 35.6, 1.2), (-2.6, 39.6, 1.25), S=1500, sx=1080, sy=500),
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.1, turn=-0.35,
             act=lambda a, s: a.point_at(s.t0 - 2.0, (140, 600), None, side=-1, dur=0.01, z=300.0))],
      c=dict(mv='push', f=1.0, rate=0.03))
    # 87 "I turn around."  the narrator turns from the window to the room; behind, in the lit doorway, Mom (focus pulls to her)
    tt87 = t(87)
    MOM_DOOR = P('mom', 'doorway', expr='too_still', turn=0.05, act=_A(pose(-9, None, 0.1, still=0.6)))
    C(T(87), 'bust', who='narrator', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0, hall=1.0), cx=1060, cy=600, scale=0.88, turn=0.1,
      expr='haunted', light=MOON, act=_A(lambda a, s: a.turn(tt87 + 0.05, 0.95, 0.45), pose(tt87 + 0.1, None, 0.45, h_turn=0.7)),
      sfx=[(tt87 + 0.05, 'cloth_rustle', -10, 0, 'close')])
    C(T(88), 'set', room='june', view='door', set=dict(nightlight=1.0, hall=1.0), rim=MOON, cam=cm((1.6, 9.8, 4.15), (0.85, 6.0, 3.95), S=880, sx=960, sy=520),
      ppl=[MOM_DOOR, P('june', (0.55, 9.3, 2.85), turn=-1.6, expr='nervous', dimk=0.2)],
      focus=3.9, c=dict(mv='push', f=1.15, rate=0.03), music=[(t(88), 'hit', 0.7)])
    C(T(89), 'set', room='june', view='door', set=dict(nightlight=1.0, hall=1.0), rim=LAMP, cam=cm((1.0, 8.2, 4.2), (0.8, 5.95, 4.0), S=1350, sx=960, sy=500),
      ppl=[dict(MOM_DOOR, act=_A(pose(-9, None, 0.1, still=0.6), tilt(t(89) + 0.4, 6.0, 1.8)))], focus_on='mom', c=dict(mv='push', f=1.0, rate=0.02))
    C(T(90), 'bust', who='mom', bg=('june', 'door', cm((0.95, 7.6, 4.2), (0.8, 5.6, 4.1), S=900)), set=dict(hall=1.0), cx=960, cy=600, scale=0.9,
      expr='too_still', light=dict(rim='#ffcf8f', rim_a=90, side=-1, key=-0.25), act=_A(pose(t(90), None, 0.9, smile=0.62), lookxy(960, 520, -9, None, 0.3, z=600.0)))
    C(T(91), 'bust', who='mom', bg=('june', 'door', cm((0.95, 7.6, 4.2), (0.8, 5.6, 4.1), S=900)), set=dict(hall=1.0), cx=960, cy=640, scale=1.08,
      expr='too_still', light=dict(rim='#ffcf8f', rim_a=90, side=-1, key=-0.25),
      act=_A(pose(-9, None, 0.1, smile=0.6), tilt(t(91) + 0.1, 9.0, 1.6), lookxy(960, 520, -9, None, 0.3, z=600.0)), music=[(e(91) + 0.3, 'hit', 0.8)])


# ==================================================================================================== THE COMMENT PROMPT: VHS PAUSE (258.0 - 279.5)
def plan_pause(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    src_mom = T(92) - 0.06                              # the last frame of "I told you not to look at the treeline."
    src_bun = T(74) + 1.9                                # the Bunnyman at the treeline, waving back
    src_door = T(105) + 0.6                              # the front door from inside (midnight)
    era = dict(era='pause')
    C(T(92), 'pause', mode='freeze', src=src_mom, first=True, **era)
    C(T(93), 'pause', mode='freeze', src=src_mom, cue=w(93, 'comments') - 0.3, **era)
    C(T(94), 'pause', mode='freeze', src=src_mom, push=0.22, **era)
    C(T(95), 'pause', mode='split', srcs=(src_mom, src_bun), ofs=(0.0, 0.0), **era)
    C(T(96), 'pause', mode='freeze', src=src_door, label=[(w(96, 'who') - 0.1, 'MOM', 640, 830, 'white'), (w(96, 'who') + 0.05, 'THE BUNNYMAN', 1280, 830, 'white')],
      cue=None, **era)
    C(T(97), 'pause', mode='word', src=src_mom, **era)
    C(T(98), 'pause', mode='split', srcs=(src_mom, src_bun), flicker='L', **era)
    C(T(99), 'pause', mode='play', src=src_mom, **era)


# ==================================================================================================== RULE 2: THE EGG (279.5 - 359.0)
HALL_MED = cm((-0.2, 2.6, 1.5), (-0.45, 0.8, 1.35), S=1150, sx=960, sy=470)        # two-shot by the front door, from the hall
HALL_IN_MED = cm((-0.4, 0.12, 1.55), (-0.35, 1.6, 1.45), S=820, sx=960, sy=500)    # from the door, looking into the hall
OVEN = lambda a, s: (a.set(-9, None, 0.01, hl_shape='oven', hr_shape='oven'),
                     a.reach(-9, None, -1, out=-34.0, down=180.0, fwd=210.0, shape='oven', up=0.0, fade=0.01),
                     a.reach(-9, None, 1, out=-34.0, down=180.0, fwd=210.0, shape='oven', up=0.0, fade=0.01))


def plan_rule2(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(100), 'rule', n=2)
    # 104 "At midnight, there's one soft tap on the front door."
    ttap = w(104, 'tap') + 0.05
    C(T(104), 'ins', name='clock', kw=dict(time=(12, 0)), c=dict(mv='push', rate=0.03))
    # the door in the middle of the frame (it is what the line is about); the narrator at the side of the hall, knees up,
    # turning toward it at the tap
    C(w(104, 'one') - 0.1, 'set', room='hall', view='door', set=dict(hall=0.3, porch=0.0), rim=NIGHT,
      ppl=[P('narrator', (-0.95, 2.45, 0.0), path=[(ttap + 0.3, (-0.95, 2.45, 0.0)), (T(105) + 0.05, (-0.62, 1.15, 0.0))], face=(0.3, 2.0), expr='haunted',
             act=lambda a, s: a.flinch(ttap + 0.05, 0.6))],
      acts=lambda A, s, sp: [A['narrator'].turn(ttap + 0.12, sp.view.turn_for(-0.95, 2.45, 0.55, -2.45), 0.45),
                             A['narrator'].look_at(ttap + 0.1, scr(sp, (-0.4, 0.0, 1.2)), None, 0.3)] and [],
      c=dict(mv='push', f=1.0, rate=0.015, hit=[(ttap, 1.2)]), focus=2.6,
      sfx=[(ttap, 'egg_tap', 0, 0, 'outside', dict(kind='one_tap'))], music=[(ttap, 'silence', 0.0, 1.0)])
    # 105 "Through the peephole, the porch is empty."  the eye to the peephole, then the fisheye porch
    tpo = w(105, 'porch') - 0.25

    def peep_acts(A, s, sp):
        # two steps to the door, the palm flat on it, the eye to the peephole
        n = A['narrator']
        pe = scr(sp, 'peephole')
        ta = s.t0 + 0.72
        n.head_to(ta, pe, 'eyes', dur=0.32, max_lean=0.25)
        n.reach_to(ta - 0.12, 1, (pe[0] - 0.15 * sp.anchors['peephole'].ppm, pe[1] + 0.2 * sp.anchors['peephole'].ppm), dur=0.35, contact='palm', shape='flat', z=-60.0)
        n.set(ta + 0.25, None, 0.15, lid_l=0.85)
        return []
    C(T(105), 'set', room='hall', view='door', set=dict(hall=0.3), rim=NIGHT, cam=HALL_MED,
      ppl=[P('narrator', 'peephole_eye', path=[(T(105), (-0.62, 1.15, 0.0)), (T(105) + 0.78, 'peephole_eye')], expr='haunted')], acts=peep_acts,
      c=dict(mv='push', f=1.0, rate=0.02))
    C(tpo, 'set', room='front', view='peephole', set=dict(egg=True, front_light=1.0), c=dict(mv='keys', keys=[(tpo, 960, 540, 1.0, None, 1.0), (w(106, 'egg'), 960, 560, 1.0, 'in_out', 1.15), (T(107), 960, 565, 1.0, 'lin', 1.2)]),
      music=[(w(106, 'egg'), 'hit', 0.45)])
    # 107 "Old pink plastic, faded by the sun."  108 "Stamped on the side: Pemberton's."
    C(T(107), 'set', room='front', view='egg', cam=cm((-0.18, -1.05, 0.30), (-0.38, -0.36, 0.0), S=1700, sx=960, sy=640), set=dict(egg=True),
      c=dict(mv='push', f=1.0, rate=0.03))
    C(T(108), 'ins', name='egg', c=dict(mv='keys', keys=[(T(108), 960, 560, 1.0, None, 1.15), (T(109), 1040, 570, 1.0, 'push', 1.65)]))
    # 109 "Every Easter, Mom carries the egg to the burn barrel in oven mitts and sets it on fire, unopened."
    tset = w(109, 'sets') - 0.1

    def barrel_acts(A, s, sp, tset=tset):
        m = A['mom']
        egg = CH.PropTrack('egg', 0, 0, sp.anchors['barrel'].ppm / 100.0)
        egg.held(-1e9, m, -1)
        m.hold_prop('egg', -1, -1e9, tset - 0.15)
        egg.gone(tset - 0.15)
        top = scr(sp, 'barrel_top')
        m.reach_to(tset - 0.9, -1, top, t1=tset + 0.3, dur=0.6, contact='grip', shape='oven', prop='egg', z=60.0, fade=0.5)
        m.reach_to(tset - 0.85, 1, (top[0] + 30, top[1] - 10), t1=tset + 0.3, dur=0.6, contact='palm', shape='oven', z=60.0, fade=0.5)
        m.look_at(s.t0, top, None, 0.4)
        return []
    C(T(109), 'set', room='yard', view='barrel', set=dict(fire=1.0), era='memory', rim=FIRE,
      ppl=[P('mom', (-5.6, 25.4, -0.45), path=[(T(109), (-5.6, 25.4, -0.45)), (tset - 1.0, 'barrel')], surface='grass', face=(-7.6, 26.3), expr='too_still', act=OVEN)],
      acts=barrel_acts, c=dict(mv='push', f=1.0, rate=0.02), sfx=[(T(109), 'fire_crackle', -6, 0, 'outside', dict(dur=6.3))])
    C(tset + 0.25, 'ins', name='egg_fire', kw=lambda tr: dict(melt=0.05 + 0.04 * tr), c=dict(mv='push', rate=0.03), sfx=[(tset + 0.25, 'fire_whoosh', -4, 0, 'close')])
    # 110 "Nine years."  111 "Nine eggs."  112 "They smell sweet when they melt."
    C(T(110), 'set', room='yard', view='barrel', set=dict(fire=1.0), era='memory', rim=FIRE,
      ppl=[P('mom', 'barrel', face=(-7.6, 26.3), expr='too_still', act=_A(lambda a, s: a.set(-9, None, 0.01, hl_shape='oven', hr_shape='oven'),
                                                                          lambda a, s: a.reach(-9, None, 1, out=10.0, down=200.0, fwd=150.0, shape='oven', up=0.0, fade=0.01),
                                                                          lambda a, s: a.reach(-9, None, -1, out=10.0, down=200.0, fwd=150.0, shape='oven', up=0.0, fade=0.01)))],
      c=dict(mv='push', f=1.3, rate=0.02))
    C(T(111), 'ins', name='egg_fire', kw=dict(melt=0.35), c=dict(mv='push', rate=0.035))
    C(T(112), 'ins', name='egg_fire', kw=lambda tr: dict(melt=0.45 + 0.3 * tr), c=dict(mv='push', rate=0.03))
    # 113 "This year, Mom is upstairs tucking June in."
    # Mom at the foot end (her back to us), both hands smoothing the quilt up to June's shoulders; June asleep on the pillow
    C(T(113), 'set', room='june', view='bed', set=dict(bed='over', nightlight=1.0, lamp=0.6), rim=LAMP,
      ppl=[P('june', 'bed_lie', expr='sleep', lie_face='up', arms='side', talk=False),
           P('mom', (1.45, 7.35, 2.85), face=(2.3, 8.8), expr='warm_smile', act=_A(hum(t(113), None, 0.8), pose(-9, None, 0.3, lean=0.3, crouch=0.15)))],
      acts=lambda A, s, sp: [A['mom'].reach_to(t(113) - 0.2, 1, scr(sp, (2.0, 8.3, 3.47)), t1=None, dur=0.7, contact='palm', shape='flat', z=60.0),
                             A['mom'].reach_to(t(113) - 0.05, -1, scr(sp, (1.95, 8.0, 3.45)), t1=None, dur=0.7, contact='palm', shape='flat', z=60.0)] and [],
      c=dict(mv='push', f=1.05, rate=0.02), sfx=[(t(113), 'hum', -10, 0, 'inside', dict(who='mom', dur=2.6, far=True))])
    # 114 "And out on the doormat, the egg rattles."  115 "Like something inside wants out."
    tr0 = w(114, 'rattles')
    C(T(114), 'set', room='front', view='egg', cam=cm((-0.18, -1.05, 0.30), (-0.38, -0.36, 0.0), S=1700, sx=960, sy=640),
      set=dict(egg=True, egg_rattle=lambda tt, a=tr0: 0.8 * math.sin((tt - a) * 31.0) * (tt > a) * (0.6 + 0.4 * math.sin((tt - a) * 3.0))),
      c=dict(mv='push', f=1.0, rate=0.04), sfx=[(tr0, 'egg_rattle', -2, 0, 'outside', dict(dur=1.4))])
    C(T(115), 'ins', name='egg', kw=dict(rattle=lambda tt: math.sin(tt * 38.0) * (0.7 + 0.3 * math.sin(tt * 5.0))), c=dict(mv='push', rate=0.05),
      sfx=[(T(115), 'egg_rattle', 0, 0, 'close', dict(dur=1.7, hard=True))])
    # 116 "I open the door."  117 "Just a crack."  from the foot of the stairs: the deadbolt, the knob, the door opens a crack
    # (the porch light in the gap) and the narrator leans to it (the egg is picked up off screen: the next shot has it)
    tdb = t(116) + 0.05; tcr = w(117, 'crack') - 0.25

    def door_acts(A, s, sp):
        n = A['narrator']
        n.reach_to(tdb - 0.25, 1, scr(sp, 'deadbolt'), t1=tdb + 0.35, dur=0.3, contact='tips', shape='grip', z=-40.0)
        n.reach_to(tdb + 0.35, 1, scr(sp, 'knob'), t1=None, dur=0.3, contact='palm', shape='grip', z=-40.0)
        n.head_to(tcr + 0.45, scr(sp, (0.08, -0.05, 1.42)), 'eyes', dur=0.55, max_lean=0.18)
        return []
    C(T(116), 'set', room='hall', view='door', cam=cm((0.25, 1.75, 1.45), (-0.3, 0.0, 1.0), S=900, sx=960, sy=500),
      set=dict(hall=0.3, porch=1.0, door=lambda tt, a=tcr: 20.0 * ease_in_out(clamp((tt - a) / 0.6))), rim=NIGHT,
      ppl=[P('narrator', (-0.2, 0.5, 0.0), face=(-0.2, 0.0), expr='haunted')], acts=door_acts, c=dict(mv='push', f=1.0, rate=0.02),
      sfx=[(tdb, 'deadbolt', -4, 0, 'inside'), (tcr, 'door_creak', -4, 0, 'inside', dict(kind='front_door', crack=True))])
    # ... the egg is picked up through the crack: low on the doormat, the door ajar above, the narrator's hand (hoodie
    # cuff) comes down out of the gap, closes on the egg and takes it inside
    tpk = e(117) - 0.32

    def pick_acts(A, s, sp, tpk=tpk):
        v = sp.view
        ex, ey, eY = ST.FD_CX + 0.02, -0.36, -0.03 + 0.012
        px, py = v.p(ex, eY + 0.031, ey)
        k_ = v.s(ex, ey) / 1000.0 * 1.0
        size = 0.175 * v.s(ex, ey)
        tg = tpk + 0.34                                   # the grip

        def wrist(tt):
            u_in = ease_out_cubic(clamp((tt - tpk) / 0.32))
            u_out = ease_in_out(clamp((tt - tg - 0.06) / 0.38))
            gx, gy = px + 0.02 * size, py - 0.62 * size     # wrist above the egg so the palm closes on it
            return gx + 0.25 * size * (1 - u_in), gy - 1.6 * size * (1 - u_in) - 1.9 * size * u_out
        # the crack: the door stands open a hand's width, the hall's warm light in the gap down to the threshold
        gx0, gy0 = v.p(ex + 0.06, -0.03 + 2.0, -0.01); gx1, gy1 = v.p(ex + 0.06, -0.03, -0.01)
        # (the gap is where the arm comes through: on the arm's line at the threshold, as wide as the arm and a bit)
        k_h = size / 66.0
        gwx, gwy = px + 0.02 * size, py - 0.62 * size
        xc = gwx - 0.3 * size * (gwy - gy1) / (3.5 * size)
        gx0, gx1 = xc + (gx0 - gx1) * 0.0, xc

        def draw(pen, tt):
            wx, wy = wrist(tt)
            held = tt >= tg
            w_ = 27.0 * k_h
            crack = poly([(gx0 - w_, gy0), (gx0 + w_, gy0), (gx1 + w_, gy1), (gx1 - w_, gy1)])
            pen.fill(crack, '#120c08', 235)
            pen.fill(poly([(gx0 - w_ * 0.45, gy0), (gx0 + w_ * 0.45, gy0), (gx1 + w_ * 0.45, gy1), (gx1 - w_ * 0.45, gy1)]), '#ffcf8f', 150)
            pen.fill(poly([(gx1 - w_ * 3, gy1), (gx1 + w_ * 3, gy1), (gx1 + w_ * 9, gy1 + w_ * 5), (gx1 - w_ * 9, gy1 + w_ * 5)]), '#ffcf8f', 60, blur=w_)
            if not held:
                ST.porch_egg(pen, v, ex, ey, eY, rattle=0.0)
            shape = 'grip' if held else 'open'
            hero_hand(pen, 'narrator', wx, wy, size, shape, 6.0, 1, (wx - 0.3 * size, wy - 3.5 * size), dict(side=-1, key=-0.1),
                      shadow=(0.03 * size, 0.05 * size, 0.06 * size, 80) if not held else None)
            if held:
                ST.draw_egg(pen, wx + 0.06 * size, wy + 0.62 * size, 0.38 * size, rot=-80.0, col='#e9a8b6', shine=0.8)
                hero_hand(pen, 'narrator', wx, wy, size, 'grip', 6.0, 1, (wx - 0.3 * size, wy - 3.5 * size), dict(side=-1, key=-0.1))
        lay = Layer(0.5, draw, 'pick_egg', blur=0)
        lay.order = -1.0
        return [lay]
    C(tpk, 'set', room='front', view='egg', cam=cm((-0.18, -1.05, 0.30), (-0.38, -0.36, 0.0), S=1700, sx=960, sy=640), set=dict(egg=False, front_light=1.0),
      acts=pick_acts, c=dict(mv='hold', f=1.0, shake=0.6), sfx=[(tpk + 0.34, 'egg_set', -6, 0, 'outside', dict(kind='pick_up'))])
    # 118 "And I open the egg."  (turned to us, the egg in front of the chest, the halves come apart)
    tsplit = w(118, 'egg') - 0.4

    def open_acts(A, s, sp):
        n = A['narrator']
        ts_, ev = n.open_egg(tsplit - 0.6, dur=1.3)
        n.look_at(s.t0, lambda tt: n.grip_point(tt, -1, 'egg', post=False), None, 0.3)
        return []
    C(T(118), 'set', room='hall', view='door', cam=cm((-0.9, 1.7, 1.45), (-0.3, 0.6, 1.2), S=1350, sx=960, sy=520),
      set=dict(hall=0.3, porch=1.0, door=14.0), rim=PORCH,
      ppl=[P('narrator', (-0.45, 0.85, 0.0), turn=0.25, expr='haunted')], acts=open_acts, c=dict(mv='push', f=1.0, rate=0.025))
    # 119 "Inside, rolling around, is a gold ring."  120 "My dad's wedding ring."  121 "Engraved on the inside: M and L, forever."
    C(T(119), 'ins', name='egg_halves', kw=lambda tr: dict(k_open=ease_out_cubic(clamp(0.6 + tr / 1.2))), c=dict(mv='keys', keys=[(T(119), 860, 600, 1.0, None, 1.1), (T(120), 800, 620, 1.0, 'push', 1.6)]),
      sfx=[(T(119) + 0.3, 'ring_roll', -4, 0, 'close', dict(dur=1.6))], music=[(w(119, 'gold'), 'hit', 0.6)])
    C(T(120), 'ins', name='ring', c=dict(mv='push', rate=0.035))
    C(T(121), 'ins', name='ring_inside', c=dict(mv='keys', keys=[(T(121), 960, 470, 1.0, None, 1.0), (T(122), 980, 440, 1.0, 'push', 1.35)]))
    # 122 "He never took it off."  Dad, a memory
    C(T(122), 'bust', who='dad', bg=('kitchen', 'table'), set=dict(tod='memory'), era='memory', grade='ob_memory', cx=960, cy=600, scale=0.88, turn=-0.2,
      expr='warm_smile', light=MEMORY, act=pose(t(122), None, 0.6, smile=0.65))
    # 123 "Not once."  124 "The Bunnyman has my father's wedding ring."  the ring pinched beside the face, tears
    C(T(123), 'bust', who='narrator', bg=('hall', 'door'), set=dict(hall=0.3, porch=1.0, door=14.0), cx=960, cy=560, scale=0.82, light=PORCH, expr='shock',
      act=_A(lambda a, s: a.hold_prop('ring', 1, -1.0, None), lambda a, s: a.reach(-1.0, None, 1, out=55.0, down=-80.0, fwd=220.0, shape='grip', up=0.0, fade=0.01),
             lambda a, s: a.reach(t(123) + 0.3, None, 1, out=45.0, down=-92.0, fwd=235.0, shape='grip', up=0.0, fade=2.4),
             pose(-1.0, None, 0.01, h_nod=0.05, h_turn=-0.1, look_x=-0.42, look_y=0.05, _gaze=1.0), ex('cry', t(124) - 0.3, None, 1.2)),
      c=dict(mv='push', x=960, y=540, zrate=0.025))
    # 125 M "You opened it."  Mom on the stairs, looking down
    C(T(125), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.3, upstairs=1.0), cx=960, cy=640, scale=0.92, turn=0.15, expr='too_still', light=LAMP,
      act=_A(pose(-9, None, 0.1, h_nod=0.35), lookxy(900, 900, -9, None, 0.3, z=300.0)), music=[(t(125), 'hit', 0.6)])
    # 126 "Mom is on the stairs."  the narrator's view up the hall: Mom standing on the stairs
    # 127 "She walks down, takes the ring out of my hand, and stares at it for a very long time."
    # one shot up the flight from the bottom: Mom standing on the 9th step, then coming down toward us
    ttk = w(127, 'takes') - 0.1
    C(T(126), 'set', room='hall', view='foot', set=dict(hall=0.3, upstairs=1.0), rim=LAMP,
      ppl=[P('mom', 'step9', path=[(T(127) - 0.05, 'step9'), (ttk + 0.1, 'step2')], surface='stairs', expr='too_still',
             act=lookxy(960, 980, -9, None, 0.3, z=200.0))],
      c=dict(mv='push', f=1.0, rate=0.015))

    def ring_acts(A, s, sp, tg=ttk + 0.2):
        n, m = A['narrator'], A['mom']
        ring = CH.PropTrack('ring', 0, 0, sp.anchors['door_inside'].ppm / 100.0 if 'door_inside' in sp.anchors else 3.0)
        ring.held(-1e9, n, 1)
        n.hold_prop('ring', 1, -1e9, tg + 0.6)
        n.reach(-1.0, tg + 0.1, 1, out=40.0, down=150.0, fwd=210.0, shape='grip', up=0.0, fade=0.5)
        n.look_at(s.t0, (m, 'eyes'), None, 0.3)
        m.look_at(s.t0, (n, 'hand_l'), tg + 1.2, 0.35)
        tc = n.give(ring, tg, 1, m, -1, dur=1.2)
        held = lambda tt: (m.where(tt, 'eyes', post=False)[0] + 0.07 * m.height, m.where(tt, 'eyes', post=False)[1] + 0.06 * m.height)
        m.reach_to(tc + 0.4, -1, held, t1=None, dur=0.8, contact='grip', prop='ring', z=170.0, fade=0.6)
        m.look_at(tc + 0.6, ring, None, 0.6)
        m.expr('dead_stare', tc + 1.0, None, 0.8)
        return []
    # (the front door still ajar behind them: nobody has shut it yet; Mom comes off the bottom step to the narrator)
    C(ttk, 'set', room='hall', view='door', cam=HALL_MED, set=dict(hall=0.3, porch=1.0, door=14.0), rim=LAMP,
      ppl=[P('narrator', (-0.6, 0.85, 0.0), face=(-0.05, 1.2), expr='haunted'),
           P('mom', (0.62, 1.05, 0.0), path=[(ttk, (0.62, 1.05, 0.0)), (ttk + 0.75, (-0.05, 1.2, 0.0))], face=(-0.6, 0.85), expr='too_still')],
      acts=ring_acts, c=dict(mv='push', f=1.0, rate=0.015), focus_on='mom')
    # 128 "Then she doesn't throw it in the fire."  her stare at the ring, held beside her face
    C(T(128), 'bust', who='mom', bg=('hall', 'door'), set=dict(hall=0.3, porch=1.0, door=14.0), cx=1000, cy=600, scale=0.85, turn=-0.25, expr='dead_stare', light=LAMP,
      act=_A(lambda a, s: a.hold_prop('ring', -1, -1.0, None), lambda a, s: a.reach(-1.0, None, -1, out=60.0, down=-70.0, fwd=230.0, shape='grip', up=0.0, fade=0.01),
             pose(-1.0, None, 0.01, look_x=0.45, look_y=0.1, _gaze=1.0)), c=dict(mv='push', x=980, y=560, zrate=0.02))
    # 129 "She puts it in her pocket."
    tpk = t(129) + 0.15

    def pocket_acts(A, s, sp, tpk=tpk):
        n, m = A['narrator'], A['mom']
        m.hold_prop('ring', -1, -9.0, tpk + 0.45)
        m.reach(-1.0, tpk - 0.1, -1, out=60.0, down=40.0, fwd=210.0, shape='grip', up=0.0, fade=0.3)
        pk = lambda tt: (m.where(tt, 'hip', post=False)[0] + 0.02 * m.height, m.where(tt, 'hip', post=False)[1] + 0.01 * m.height)
        m.reach_to(tpk, -1, pk, t1=tpk + 0.8, dur=0.45, contact='tips', z=90.0, fade=0.5)
        m.look_at(tpk + 0.5, (n, 'eyes'), None, 0.5)
        n.look_at(s.t0, (m, 'hand_r'), None, 0.3)
        return []
    C(T(129), 'set', room='hall', view='door', cam=HALL_MED, set=dict(hall=0.3, porch=1.0, door=14.0), rim=LAMP,
      ppl=[P('narrator', (-0.6, 0.85, 0.0), face=(-0.05, 1.2), expr='haunted'), P('mom', (-0.05, 1.2, 0.0), face=(-0.6, 0.85), expr='too_still')],
      acts=pocket_acts, c=dict(mv='push', f=1.05, rate=0.02), focus_on='mom', sfx=[(tpk + 0.45, 'cloth_rustle', -8, 0, 'inside', dict(kind='pocket'))])


# ==================================================================================================== RULE 3: THE KNOCK (359.0 - 416.2)
KNOCK_TAGS = [(-340, -150), (340, -150), (-380, 40), (0, -260), (380, 40), (-300, 230), (300, 230)]
GRAN_CAM = cm((-0.75, 5.95, 1.25), (-0.75, 8.45, 0.95), S=1100, sx=960, sy=560)


def plan_rule3(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(130), 'rule', n=3)
    # the knocks: 2 . pause . 3 . pause . 2 (each group in the gap just before the line that names it)
    g1 = [e(135) + 0.1, e(135) + 0.36]
    g2 = [e(137) + 0.04, e(137) + 0.22, e(137) + 0.4]
    g3 = [e(139) + 0.05, e(139) + 0.25]
    knocks = g1 + g2 + g3
    F.knocks = knocks
    ksfx = [(tk, 'knock_door', -1, 0, 'inside', dict(group=gi, index=k, pattern='2-3-2'))
            for k, (tk, gi) in enumerate(zip(knocks, [0, 0, 1, 1, 1, 2, 2]))]
    C(T(135), 'ins', name='clock', kw=dict(time=(1, 13)), c=dict(mv='push', rate=0.03))
    # "he knocks": the two of them in the hall, facing the front door
    FAM = [P('mom', (-0.75, 1.4, 0.0), turn=1.9, expr='too_still'), P('narrator', (0.05, 1.55, 0.0), turn=1.95, expr='haunted')]
    th = w(135, 'he') - 0.1
    C(th, 'set', room='hall', view='door', set=dict(hall=0.4), rim=LAMP, ppl=FAM, c=dict(mv='push', f=1.15, rate=0.02, hit=[(k, 3.0) for k in g1]),
      tags=[(g1[0], '1', 960 + KNOCK_TAGS[0][0], 540 + KNOCK_TAGS[0][1], 'white', 7.0), (g1[1], '2', 960 + KNOCK_TAGS[1][0], 540 + KNOCK_TAGS[1][1], 'white', 7.0)],
      tag_sound=False, sfx=ksfx[:2])
    # the door, close: three more (and the count runs on); a pause; two; "Seven."
    tags = [(knocks[k], str(k + 1), 960 + KNOCK_TAGS[k][0], 540 + KNOCK_TAGS[k][1], 'white' if k < 6 else 'red', 9.0) for k in range(7)]
    C(T(136), 'set', room='hall', view='door', set=dict(hall=0.4), rim=LAMP, c=dict(mv='push', f=2.0, rate=0.012, hit=[(k, 4.0) for k in g2 + g3]),
      tags=[tg for tg in tags if tg[0] < T(137) + 2.6], tag_sound=False, sfx=ksfx[2:5])
    C(T(139) - 0.25, 'set', room='hall', view='door', set=dict(hall=0.4), rim=LAMP, ppl=FAM, c=dict(mv='push', f=1.35, rate=0.015, hit=[(k, 3.5) for k in g3]),
      tags=[(tg[0] if tg[0] > T(139) - 0.25 else T(139) - 0.25, ) + tg[1:] for tg in tags], tag_sound=False, sfx=ksfx[5:],
      music=[(t(141), 'hit', 0.65)])
    # 142 "Mom nods."  143-144 M "That's him. That's how he knocks, every year."
    C(T(142), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.4), cx=960, cy=610, scale=0.9, expr='too_still', light=LAMP,
      act=_A(lambda a, s: a.head_down(t(142) + 0.1, t(142) + 0.45, 0.45, 0.3), lambda a, s: a.head_down(t(142) + 0.6, t(142) + 0.9, 0.35, 0.3),
             lookxy(860, 560, -9, None, 0.3, z=500.0)))
    C(T(143), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.4), cx=1000, cy=640, scale=1.0, turn=-0.15, expr='too_still', light=LAMP,
      act=lookxy(760, 560, -9, None, 0.3, z=500.0))
    # 145 "But my stomach drops, because I know that knock."
    C(T(145), 'bust', who='narrator', bg=('hall', 'door'), set=dict(hall=0.4), cx=930, cy=600, scale=0.88, turn=0.15, expr='haunted', light=LAMP,
      act=_A(ex('shock', w(145, 'drops') - 0.1, None, 0.25), lookxy(960, 500, w(145, 'know') - 0.2, None, 0.4, z=700.0)))
    # 146 "Grandma taught it to me when I was six."  (memory: Grandma's daylight kitchen, the narrator at six beside her)
    GK = [P('grandma', 'kchair2', turn=0.0, expr='warm_smile', hands='lap'),
          P('narrator_kid', 'kchair3', turn=-0.15, expr='neutral', hands='lap')]
    C(T(146), 'set', room='kitchen', view='table', set=dict(tod='memory', kitchen=0.0), era='memory', grade='ob_memory', rim=MEMORY, cam=GRAN_CAM,
      ppl=[dict(GK[0], act=lambda a, s: None), dict(GK[1])],
      acts=lambda A, s, sp: [A['grandma'].look_at(s.t0, (A['narrator_kid'], 'eyes'), None, 0.3), A['narrator_kid'].look_at(s.t0, (A['grandma'], 'eyes'), None, 0.3)] and [],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 147-148 G "This is our family knock," she said.  her knuckles on the tabletop, two, three, two
    tk0 = t(147) + 0.1

    def gran_knock(A, s, sp, tk0=tk0):
        g, k = A['grandma'], A['narrator_kid']
        evs = g.knock_pattern(tk0, (2, 3, 2), side=-1, beat=0.18, gap=0.34, target=scr(sp, (-0.95, 8.0, 0.77)), z=120.0, kind='table')
        k.look_at(s.t0, scr(sp, (-0.95, 8.0, 0.77)), tk0 + 1.6, 0.3)
        k.look_at(tk0 + 1.7, (g, 'eyes'), None, 0.35)
        g.look_at(s.t0, (k, 'eyes'), None, 0.3)
        return []
    C(T(147), 'set', room='kitchen', view='table', set=dict(tod='memory', kitchen=0.0), era='memory', grade='ob_memory', rim=MEMORY,
      cam=cm((-0.75, 6.4, 1.15), (-0.75, 8.4, 0.95), S=1350, sx=960, sy=600), ppl=GK, acts=gran_knock, c=dict(mv='push', f=1.0, rate=0.015))
    # 149-150 G "If anyone ever knocks like this, it's family. I taught it to your mother when she was little."
    C(T(149), 'bust', who='grandma', bg=('kitchen', 'table', GRAN_CAM), set=dict(tod='memory'), era='memory', grade='ob_memory', cx=930, cy=600, scale=0.85,
      turn=0.25, expr='warm_smile', light=MEMORY, act=lookxy(1500, 640, -9, None, 0.3, z=300.0))
    # 151 "Then she got very quiet."   152-154 G "She never used it again. Not once. Not after the woods."
    C(T(151), 'bust', who='grandma', bg=('kitchen', 'table', GRAN_CAM), set=dict(tod='memory'), era='memory', grade='ob_memory', cx=960, cy=620, scale=1.0,
      turn=0.2, expr='warm_smile', light=MEMORY, act=_A(ex('haunted', t(151) + 0.2, None, 0.8), lambda a, s: a.head_down(t(151) + 0.3, None, 0.45, 0.9)))
    C(T(152), 'bust', who='grandma', bg=('kitchen', 'table', GRAN_CAM), set=dict(tod='memory'), era='memory', grade='ob_memory', cx=1000, cy=660, scale=1.15,
      turn=0.15, expr='haunted', light=MEMORY, act=_A(pose(-9, None, 0.1, h_nod=0.25), lookxy(1300, 900, -9, None, 0.3, z=300.0)))
    # 155-157 "Two. Three. Two."  her knuckles on the table, on each word
    hits = []
    for i, n_ in ((155, 2), (156, 3), (157, 2)):
        a0 = t(i) + 0.02
        hits += [a0 + 0.17 * k for k in range(n_)]
    C(T(155), 'ins', name='knuckles', era='memory', anim=True, kw=lambda tr, h=tuple(hh - T(155) for hh in hits): dict(hits=h),
      c=dict(mv='push', rate=0.02), sfx=[(hh, 'knock_door', -3, 0, 'memory', dict(kind='table', index=k)) for k, hh in enumerate(hits)])
    # 158 "Somebody at our front door knows my grandmother's secret knock."
    C(T(158), 'set', room='hall', view='door', set=dict(hall=0.4), rim=LAMP, ppl=FAM, c=dict(mv='push', f=1.3, rate=0.03))
    # 159 "And my mother, standing right next to me, doesn't recognize it at all."  from the door: both faces; I look at her
    tmo = w(159, 'mother')
    C(T(159), 'set', room='hall', view='in', set=dict(hall=0.4), rim=LAMP, cam=HALL_IN_MED,
      ppl=[P('mom', (-0.75, 1.4, 0.0), turn=0.08, expr='too_still', act=lookxy(980, 470, -9, None, 0.3, z=400.0)),
           P('narrator', (0.05, 1.55, 0.0), turn=-0.12, expr='haunted')],
      acts=lambda A, s, sp: [A['narrator'].look_at(tmo, (A['mom'], 'eyes'), None, 0.45, body=0.2)] and [], c=dict(mv='push', f=1.0, rate=0.012), focus_on='mom')
    # "... doesn't recognize it at all.": her face, blank, polite, waiting (nothing in it knows that knock)
    trc = w(159, 'recognize') - 0.35
    C(trc, 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.4), cx=960, cy=620, scale=0.95, turn=-0.05, expr='too_still', light=LAMP, blink=False,
      act=_A(pose(-9, None, 0.1, still=0.9), lookxy(980, 520, -9, None, 0.3, z=600.0), lambda a, s: a.head_tilt(trc + 0.4, 5.0, 1.4)),
      c=dict(mv='push', x=960, y=580, zrate=0.012))


# ==================================================================================================== RULE 4: THE MAIL SLOT (416.2 - 496.5)
PORCH_CAM = cm((1.05, -2.15, 1.45), (-0.38, -0.3, 0.75), S=1050, sx=960, sy=540)
SLOT_OUT_WIDE = cm((1.35, -1.05, 1.3), (-0.3, -0.5, 1.0), S=900, sx=960, sy=560)     # on the porch: the Bunnyman at the slot in profile
SLOT_OUT_CLOSE = cm((1.0, -0.6, 1.2), (-0.3, -0.5, 1.2), S=1000, sx=900, sy=600)     # closer: the mask's profile at the flap
SLOT_SIDE = cm((-1.28, 1.25, 1.3), (-0.3, 0.3, 0.8), S=1050, sx=960, sy=560)       # in the hall by the wall: the door at 3/4


def bunny_at_slot(cry_t=None, tilt_t=None):
    """The Bunnyman crouched at the front door, a paw holding the mail slot flap open (outside, on the porch)."""
    def act(a, s):
        a.crouch(-9, 0.85, None, 0.01)
        a.reach_to(-9, -1, s.sp and scr(s.sp, (-0.40, -0.05, 0.95)), dur=0.01, contact='tips', shape='paw_flat', z=0.0)
        a.set(-9, None, 0.01, h_tilt=-8.0, h_nod=0.2)
        if tilt_t is not None: a.head_tilt(tilt_t, -16.0, 1.6)
        if cry_t is not None:
            def sob(P_, tt, c0=cry_t):
                if tt < c0: return
                k = min(1.0, (tt - c0) / 0.8)
                ph = (tt - c0) / 0.72
                beat = math.exp(-((ph % 1.0) * 5.0)) * k
                P_.h_nod += 0.18 * k + 0.08 * beat; P_.hunch += 0.25 * k + 0.12 * beat; P_.tilt += 1.5 * beat
            a._add(cry_t - 0.5, None, sob, real=True)
    return act


def plan_rule4(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(160), 'rule', n=4)
    # 164 "At 1:40, the brass flap of the mail slot creaks open, and a voice comes through."
    tfl = w(164, 'creaks')
    C(T(164), 'ins', name='clock', kw=dict(time=(1, 40)), c=dict(mv='push', rate=0.03))
    C(w(164, 'brass') - 0.1, 'set', room='hall', view='slot', set=dict(hall=0.3, flap=lambda tt, a=tfl: ease_in_out(clamp((tt - a) / 1.3))),
      c=dict(mv='push', f=1.0, rate=0.03), sfx=[(tfl, 'mail_slot', -2, 0, 'inside', dict(kind='creak_open', dur=1.3))], music=[(tfl, 'silence', 0.0, 1.2)])
    # 165 "A little girl's voice."  166 "Small, and scared."
    C(T(165), 'ins', name='slot', kw=dict(flap=1.0, eyes=0.0), c=dict(mv='push', rate=0.03))
    # "Small, and scared.": its source, not a reaction: the brass flap held up from outside, trembling on the dark gap
    C(T(166), 'ins', name='slot', kw=lambda tr: dict(flap=0.9 + 0.06 * math.sin(tr * 31.0) * (0.6 + 0.4 * math.sin(tr * 4.3)), eyes=0.0),
      c=dict(mv='push', rate=0.03))
    # 167 L "Mama?"  the dark slot, a wet glint far in
    C(T(167), 'ins', name='slot', kw=dict(flap=1.0, eyes=0.7), c=dict(mv='push', rate=0.045), music=[(t(167), 'hit', 0.5)])
    # 168 "Grandma has been dead for six years."
    C(T(168), 'ins', name='gran_photo', c=dict(mv='push', rate=0.03))
    # 169-171 L "Mama, it's Laurie. I lost my egg. Can I come home now?"  outside: the Bunnyman crouched at the mail slot
    C(T(169), 'set', room='front', view='porch', cam=SLOT_OUT_WIDE, set=dict(front_light=1.0), rim=PORCH,
      ppl=[P('bunny', (-0.32, -0.62, -0.03), face=(-0.38, 0.0), expr='neutral', act=bunny_at_slot(tilt_t=t(171)), talk_k=0.6)],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 172 "Mom's face doesn't move."  173-175 M "It took my voice," she says, very calmly. "When I was seven."
    C(T(172), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.3, flap=1.0), cx=960, cy=620, scale=0.95, expr='too_still', light=NIGHT_L, blink=False,
      act=pose(-9, None, 0.1, still=0.85, lock=1.0))
    C(T(173), 'bust', who='mom', bg=('hall', 'in'), set=dict(hall=0.3, flap=1.0), cx=1000, cy=620, scale=0.9, turn=-0.2, expr='too_still', light=NIGHT_L,
      act=lookxy(760, 560, -9, None, 0.3, z=500.0))
    # 176 M "It's been using it for thirty-six years to make children open doors."  two-shot by the door
    C(T(176), 'set', room='hall', view='door', cam=HALL_MED, set=dict(hall=0.3, flap=1.0), rim=NIGHT,
      ppl=[P('narrator', (-0.6, 0.85, 0.0), face=(-0.05, 1.2), expr='haunted'), P('mom', (-0.05, 1.2, 0.0), face=(-0.6, 0.85), expr='too_still')],
      acts=lambda A, s, sp: [A['narrator'].look_at(s.t0, (A['mom'], 'eyes'), None, 0.3), A['mom'].look_at(s.t0, (A['narrator'], 'eyes'), None, 0.3)] and [],
      c=dict(mv='push', f=1.05, rate=0.02), focus_on='mom')
    # 177-179 "It makes sense. It makes perfect sense. I want it to make sense."
    C(T(177), 'bust', who='narrator', bg=('hall', 'door'), set=dict(hall=0.3, flap=1.0), cx=960, cy=600, scale=0.9, turn=0.1, expr='haunted', light=NIGHT,
      act=_A(lookxy(800, 520, -9, w(179, 'want') - 0.1, 0.3, z=400.0), lookxy(980, 700, w(179, 'want'), None, 0.5, z=300.0), blinks(t(178) + 0.2)))
    # 180 "But June has crept down the stairs in her socks, and she kneels at the mail slot."
    tkn = w(180, 'kneels') - 0.1
    # up the flight from the bottom: June creeping down toward us in her socks, a hand on the rail
    C(T(180), 'set', room='hall', view='foot', set=dict(hall=0.3, upstairs=0.6, flap=1.0), rim=NIGHT,
      ppl=[P('june', STEP(12), path=[(T(180) + 0.1, STEP(12)), (tkn - 0.75, STEP(1)), (tkn - 0.3, (0.82, 0.62, 0.0))], surface='stairs_quiet', expr='neutral',
             act=_A(lambda a, s: a.set(-9, None, 0.1, lean=0.12, crouch=0.15), lookxy(700, 900, -9, None, 0.3, z=300.0)))],
      c=dict(mv='push', f=1.0, rate=0.015), sfx=[(T(180) + 0.3, 'stairs_creak', -12, 0.3, 'inside', dict(soft=True))])
    # from the side of the hall, low (a kneeling child seen from behind reads as standing): June comes off the stairs,
    # pads to the door and kneels at the slot in profile
    t160 = tkn - 0.55
    C(t160, 'set', room='hall', view='door', cam=cm((-1.32, 0.66, 0.55), (-0.15, 0.32, 0.5), S=720, sx=1000, sy=600), set=dict(hall=0.3, flap=1.0), rim=NIGHT,
      ppl=[P('june', 'mail_slot_kneel', path=[(t160, (0.78, 0.6, 0.0)), (t160 + 0.85, 'mail_slot_kneel')], surface='inside_quiet', kind='kneel', knees=2,
             kneel_t=t160 + 0.9, kneel_dur=0.6, expr='neutral', face=(-0.4, 0.0), act=pose(t160 + 1.4, None, 0.4, lean=0.15, h_nod=0.15))],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='june')
    # 181-183 J "Laurie's my mom," she says. "She's right here."  June at the slot, her cheek near the door
    C(T(181), 'bust', who='june', bg=('hall', 'door', SLOT_SIDE), set=dict(hall=0.3, flap=1.0), cx=1100, cy=660, scale=0.92, turn=-0.75, h_turn=-0.15,
      expr='neutral', light=NIGHT_L, act=pose(-9, None, 0.1, h_nod=0.15))
    # 184 "Silence."  185-186 "Then the little voice whispers," L "Is she humming?"
    C(T(184), 'set', room='hall', view='slot', set=dict(hall=0.3, flap=1.0), c=dict(mv='push', f=1.05, rate=0.03))
    C(T(185), 'set', room='front', view='porch', cam=SLOT_OUT_CLOSE, set=dict(front_light=1.0), rim=PORCH,
      ppl=[P('bunny', (-0.32, -0.62, -0.03), face=(-0.38, 0.0), act=bunny_at_slot(tilt_t=t(186) - 0.3), talk_k=0.6)],
      c=dict(mv='push', f=1.0, rate=0.03))
    # 187 "June looks back at Mom."  188 J "Yeah."
    C(T(187), 'bust', who='june', bg=('hall', 'door', SLOT_SIDE), set=dict(hall=0.3, flap=1.0), cx=1080, cy=660, scale=0.92, turn=-0.75, expr='neutral', light=NIGHT_L,
      act=_A(lambda a, s: a.turn(t(187) + 0.1, 0.35, 0.6), pose(t(187) + 0.15, None, 0.6, h_turn=0.4), lookxy(1700, 360, t(187) + 0.2, None, 0.5, z=300.0)))
    # 189 "And on the other side of the door, the little girl starts to cry."  190-191 "Not like a monster. Like a kid ..."
    C(T(189), 'set', room='front', view='porch', cam=SLOT_OUT_CLOSE, set=dict(front_light=1.0), rim=PORCH,
      ppl=[P('bunny', (-0.32, -0.62, -0.03), face=(-0.38, 0.0), act=bunny_at_slot(cry_t=w(189, 'cry') - 0.2))],
      c=dict(mv='push', f=1.05, rate=0.02), sfx=[(w(189, 'cry') - 0.2, 'girl_cry', 0, 0, 'outside', dict(dur=8.5, through_door=True))])
    C(T(190), 'bust', who='bunny', bg=('front', 'porch', PORCH_CAM), set=dict(front_light=1.0), cx=960, cy=640, scale=0.95, turn=-0.55, h_turn=-0.1,
      light=PORCH, act=_A(pose(-9, None, 0.1, h_nod=0.3, h_tilt=-12.0), bunny_cry_bust(t(190) - 1.0)))
    # 192 "Mom closes the mail slot."  193 "She smooths June's hair."  (one move: the fingertips push the flap shut, the hand on her hair)
    tcl = t(192) + 0.25

    def close_acts(A, s, sp, tcl=tcl):
        m, j = A['mom'], A['june']
        m.reach_to(tcl - 0.5, -1, scr(sp, (-0.37, 0.02, 0.95)), t1=tcl + 0.35, dur=0.5, contact='tips', shape='flat', z=-30.0)
        m.crouch(tcl - 0.6, 0.55, tcl + 0.6, 0.4)
        m.smooth_hair(t(193) - 0.1, 1, j, n=2, stroke=0.7)
        m.look_at(s.t0, (j, 'crown'), None, 0.3)
        j.look_at(s.t0, scr(sp, (-0.4, 0.0, 0.95)), t(193), 0.3)
        return []
    C(T(192), 'set', room='hall', view='door', cam=cm((-1.3, 2.35, 1.35), (-0.25, 0.45, 0.95), S=820, sx=960, sy=600),
      set=dict(hall=0.3, flap=lambda tt, a=tcl: 1.0 - ease_in_out(clamp((tt - a) / 0.2))), rim=NIGHT,
      ppl=[P('june', 'mail_slot_kneel', kind='kneel', knees=2, expr='sad', face=(-0.4, 0.0)),
           P('mom', (0.02, 0.72, 0.0), face=(-0.4, 0.2), expr='too_still')],
      acts=close_acts, c=dict(mv='push', f=1.0, rate=0.02), focus_on='mom', sfx=[(tcl, 'mail_slot', -2, 0, 'inside', dict(kind='close'))])
    # 194 M "Bedtime, bunny."  195 "She's humming."
    C(T(194), 'bust', who='mom', bg=('hall', 'door', SLOT_SIDE), set=dict(hall=0.3), cx=960, cy=620, scale=0.92, turn=-0.3, expr='warm_smile', light=NIGHT_L,
      act=_A(lookxy(760, 900, -9, None, 0.3, z=300.0), hum(e(194) + 0.3, None)), sfx=[(t(195), 'hum', -6, 0, 'close', dict(who='mom', dur=2.0))],
      music=[(t(195), 'jingle', 0.6, 2.0, dict(version='hum'))])


def bunny_cry_bust(c0):
    def act(a, s):
        def sob(P_, tt):
            if tt < c0: return
            ph = (tt - c0) / 0.72
            beat = math.exp(-((ph % 1.0) * 5.0))
            P_.h_nod += 0.06 * beat; P_.tilt += 1.2 * beat; P_.h_tilt += 2.0 * beat
        a._add(c0 - 0.5, None, sob, real=True)
    return act


# ==================================================================================================== RULE 5: THE ATTIC (496.5 - 589.8)
BACKDOOR_POV = cm((-3.3, 6.55, 1.2), (-3.3, 4.4, 0.9), S=1050, sx=960, sy=560)
ATTIC_MED = cm((-0.6, 6.4, 6.4), (0.6, 7.55, 5.75), S=1200, sx=960, sy=560)


def plan_rule5(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(196), 'rule', n=5)
    # 199 "June and I sleep on the couch, with Mom in the armchair facing the back door."
    twm = w(199, 'with') - 0.1
    SLEEP = lambda a, s: a.set(-9, None, 0.1, h_tilt=-14.0, lean=-0.08, h_nod=0.15)
    JSLEEP = lambda a, s: a.set(-9, None, 0.1, h_tilt=18.0, lean=-0.1, h_nod=0.3)
    C(T(199), 'set', room='living', view='wide2', set=dict(lamp=0.0, chair_lamp=0.5, curtains=0.0, blanket=True), rim=NIGHT,
      ppl=[P('narrator', 'couch_left', expr='sleep', act=SLEEP), P('june', 'couch_mid', expr='sleep', act=JSLEEP)],
      c=dict(mv='push', f=1.45, rate=0.012))
    C(twm, 'set', room='living', view='back', cam=BACKDOOR_POV, set=dict(lamp=0.0, chair_lamp=0.5, curtains=0.0), rim=LAMP,
      ppl=[P('mom', 'armchair', expr='too_still', blink=False, hands='arms', act=_A(pose(-9, None, 0.1, still=0.8), lookxy(960, 380, -9, None, 0.3, z=900.0))),
           P('narrator', 'couch_left', expr='sleep', act=SLEEP), P('june', 'couch_mid', expr='sleep', act=JSLEEP)],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='mom')
    # 200 "At 2:47, I wake up."
    C(T(200), 'ins', name='clock', kw=dict(time=(2, 47)), c=dict(mv='push', rate=0.03))
    twk = w(200, 'i') - 0.1
    C(twk, 'bust', who='narrator', bg=('living', 'couch'), set=dict(lamp=0.0, chair_lamp=0.0, curtains=0.0, blanket=True), cx=940, cy=620, scale=0.9, turn=0.3,
      expr='sleep', light=NIGHT, act=_A(ex('haunted', twk + 0.35, None, 0.2), pose(twk + 0.35, None, 0.25, lid_l=0.0, lid_r=0.0)), sfx=[(twk + 0.35, 'breath', -8, 0, 'close', dict(kind='gasp'))])
    # 201 "June's blanket is still warm."  the empty seat beside the narrator, the hand on the blanket
    C(T(201), 'set', room='living', view='couch', set=dict(lamp=0.0, chair_lamp=0.0, curtains=0.0, blanket=True), rim=NIGHT,
      ppl=[P('narrator', 'couch_left', expr='haunted', turn=0.45)],
      acts=lambda A, s, sp: [A['narrator'].reach_to(t(201), -1, scr(sp, (-3.3, 1.25, 0.45)), dur=0.6, contact='palm', shape='flat', z=40.0),
                             A['narrator'].look_at(t(201) - 0.3, scr(sp, (-3.3, 1.25, 0.45)), None, 0.3)] and [],
      c=dict(mv='push', f=1.05, rate=0.02))
    # 202 "June is gone."  203 "Mom's chair is empty."
    C(T(202), 'bust', who='narrator', bg=('living', 'couch'), set=dict(lamp=0.0, curtains=0.0, blanket=True), cx=980, cy=620, scale=0.9, turn=0.35,
      expr='haunted', light=NIGHT, act=_A(lookxy(1600, 600, t(202), t(202) + 0.6, 0.25, z=300.0), lookxy(300, 600, t(202) + 0.7, None, 0.3, z=300.0)))
    # (dof 0: the whole dark room in focus; the set's own depth of field put a several-screen layer through the dynamic blur
    # path on every frame, 1.7 s/frame at 2560)
    C(T(203), 'set', room='living', view='chair', set=dict(lamp=0.0, chair_lamp=0.0, kitchen=0.0, curtains=0.0), rim=NIGHT, dof=0.0, c=dict(mv='push', f=1.2, rate=0.03))
    # 204 "And every door is still locked from the inside."  the back door (bolt + chain), then the front door's deadbolt
    C(T(204), 'set', room='kitchen', view='door', set=dict(kitchen=0.0, locked=1.0), c=dict(mv='push', f=1.3, rate=0.02))
    C(w(204, 'locked') - 0.1, 'set', room='hall', view='peep', set=dict(hall=0.0), c=dict(mv='push', f=1.0, rate=0.03))
    # 205 "There's a light under the attic door."
    C(T(205), 'set', room='up', view='hall', set=dict(upstairs=0.0, attic_gap=1.0), c=dict(mv='push', f=1.8, rate=0.03),
      sfx=[(T(205) + 0.2, 'house_settle', -12, 0, 'inside')])
    # 206 "June is sitting on the attic floor in front of Mom's old toy chest."
    C(T(206), 'set', room='attic', view='chest', set=dict(bulb=1.0, chest='open'), rim=BULB,
      ppl=[P('june', 'chest_floor', kind='floor', turn=-1.2, expr='neutral', act=_A(lambda a, s: a.hold_prop('diary', -1),
                                                                                lambda a, s: a.reach(-9, None, -1, out=-30.0, down=230.0, fwd=210.0, shape='grip', up=0.0, fade=0.01)))],
      c=dict(mv='push', f=1.15, rate=0.025), sfx=[(T(206), 'bulb_hum', -12, 0, 'attic', dict(dur=4.0))])
    # 207 "She's holding a tiny yellow dress, stiff and grey with age."
    C(T(207), 'set', room='attic', view='chest', cam=ATTIC_MED, set=dict(bulb=1.0, chest='open'), rim=BULB,
      ppl=[P('june', 'chest_floor', kind='floor', turn=-0.9, expr='neutral',
             act=_A(lambda a, s: a.hold_prop('dress_tiny', 1), lambda a, s: a.reach(-9, None, 1, out=40.0, down=-10.0, fwd=200.0, shape='grip', up=0.0, fade=0.01),
                    lambda a, s: a.hold_prop('diary', -1), lambda a, s: a.reach(-9, None, -1, out=-30.0, down=230.0, fwd=210.0, shape='grip', up=0.0, fade=0.01),
                    lambda a, s: a.look_at(-9, lambda tt: a.grip_point(tt, 1, 'dress_tiny', post=False), None, 0.3)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(w(207, 'stiff') - 0.1, 'ins', name='dress_old', c=dict(mv='push', rate=0.03))
    # 208 the diary with the pink plastic lock;  209 "Laurie Price, age seven."
    C(T(208), 'ins', name='diary', c=dict(mv='keys', keys=[(T(208), 960, 560, 1.0, None, 1.0), (T(209), 1100, 560, 1.0, 'push', 1.25)]))
    C(T(209), 'ins', name='diary', c=dict(mv='keys', keys=[(T(209), 960, 410, 1.0, None, 1.7), (T(210), 960, 410, 1.0, 'push', 1.9)]))
    # 210 "The first half is crayon."  211 "Huge, crooked letters."  212-214 I love Mama. / I love my dog Biscuit. / Tomorrow is the Easter parade.
    C(T(210), 'ins', name='diary_crayon', c=dict(mv='push', rate=0.025), sfx=[(T(210) + 0.05, 'page_flip', -6, 0, 'close')])
    C(T(211), 'ins', name='diary_crayon', c=dict(mv='keys', keys=[(T(211), 960, 540, 1.0, None, 1.25), (T(212), 980, 540, 1.0, 'push', 1.35)]))
    C(T(212), 'ins', name='diary_crayon', c=dict(mv='keys', keys=[(T(212), 560, 300, 1.0, None, 1.9), (T(213), 560, 300, 1.0, 'lin', 1.95)]))
    C(T(213), 'ins', name='diary_crayon', c=dict(mv='keys', keys=[(T(213), 580, 560, 1.0, None, 1.75), (T(214), 600, 560, 1.0, 'lin', 1.8)]))
    C(T(214), 'ins', name='diary_crayon', c=dict(mv='keys', keys=[(T(214), 1300, 420, 1.0, None, 1.6), (T(215), 1300, 440, 1.0, 'lin', 1.65)]))
    # 215 "Then Easter, 1987."  216 "And the handwriting changes."  217 "Perfect, slanted cursive."
    C(T(215), 'ins', name='diary_flip', c=dict(mv='keys', keys=[(T(215), 640, 420, 1.0, None, 1.6), (T(216), 650, 430, 1.0, 'push', 1.7)]),
      sfx=[(T(215) + 0.05, 'page_flip', -4, 0, 'close')], music=[(t(215), 'hit', 0.45)])
    C(T(216), 'ins', name='diary_flip', c=dict(mv='keys', keys=[(T(216), 960, 540, 1.0, None, 1.05), (T(217), 1280, 500, 1.0, 'in_out', 1.6)]))
    C(T(217), 'ins', name='diary_cursive', c=dict(mv='keys', keys=[(T(217), 1300, 400, 1.0, None, 1.7), (T(218), 1290, 420, 1.0, 'lin', 1.8)]),
      sfx=[(T(217) + 0.05, 'page_flip', -6, 0, 'close')])
    # 218 "Grown-up handwriting, from a seven-year-old."  June reading it under the bulb
    C(T(218), 'bust', who='june', bg=('attic', 'chest'), set=dict(bulb=1.0), cx=960, cy=560, scale=0.88, turn=-0.3, expr='neutral', light=BULB,
      act=_A(pose(-9, None, 0.1, h_nod=0.45), lambda a, s: [a.look_at(-9, (900 + 120 * k, 1100), None, 0.2, z=200.0) for k in range(1)]))
    # 219 "The same sentence, over and over, page after page."  220-223 "I am Laurie." x 4
    C(T(219), 'ins', name='diary_cursive', c=dict(mv='keys', keys=[(T(219), 700, 300, 1.0, None, 1.5), (T(220), 700, 800, 1.0, 'lin', 1.5)]),
      sfx=[(T(219) + 1.2, 'page_flip', -8, 0, 'close'), (T(219) + 2.2, 'page_flip', -8, 0, 'close')])
    for k, (i, x, y) in enumerate(((220, 560, 220), (221, 1210, 400), (222, 640, 588), (223, 1260, 818))):
        C(T(i), 'ins', name='diary_cursive', c=dict(mv='keys', keys=[(T(i), x, y, 1.0, None, 2.6 + 0.15 * k), (T(i + 1), x + 20, y, 1.0, 'lin', 2.7 + 0.15 * k)]),
          post=dict(exposure=-0.03 * k))
    # 224 "And on the very last page, in that same perfect hand:"  225 "It is so nice to be small again."
    C(T(224), 'ins', name='diary_last', c=dict(mv='keys', keys=[(T(224), 960, 540, 1.0, None, 1.05), (T(225), 1300, 600, 1.0, 'in_out', 1.4)]),
      sfx=[(T(224) + 0.1, 'page_flip', -4, 0, 'close')])
    C(T(225), 'ins', name='diary_last', c=dict(mv='keys', keys=[(T(225), 1330, 600, 1.0, None, 2.0), (T(226), 1330, 600, 1.0, 'push', 2.2)]),
      music=[(t(225), 'stinger', 0.6)])
    # 226 "June smiles up at me."  227-228 J "Mom says I can wear the yellow dress tomorrow. For the magic trick."
    C(T(226), 'bust', who='june', bg=('attic', 'chest'), set=dict(bulb=1.0), cx=960, cy=640, scale=0.92, turn=-0.25, expr='neutral', light=BULB,
      act=_A(pose(-9, None, 0.1, h_nod=-0.15), lookxy(1000, 260, -9, None, 0.3, z=300.0), ex('warm_smile', t(226) + 0.1, None, 0.5),
             lambda a, s: a.hold_prop('dress_tiny', 1), lambda a, s: a.reach(-9, None, 1, out=40.0, down=60.0, fwd=200.0, shape='grip', up=0.0, fade=0.01)))
    # 229 "And from the dark corner of the attic, behind the boxes, Mom says,"  230 M "Back to bed, you two."
    # behind the boxes, in the dark corner: Mom in the old rocker, a shape in the shadow, rocking very slowly; only the edge of
    # the bulb's light finds her (a rim on her shoulder and her eyes); on 'Mom says' her head turns to the two of them
    tms = w(229, 'mom') - 0.2

    def rock(a, s):
        def fn(P_, tt):
            P_.lean += 0.06 * math.sin((tt - s.t0) * 2.0 * math.pi / 2.6)
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
    C(T(229), 'set', room='attic', view='corner', set=dict(bulb=1.0), rim=dict(rim='#ffcf8f', rim_a=30, side=-1, key=-0.55),
      cam=cm((-1.35, 6.25, 6.55), (-4.15, 8.1, 6.0), S=1050, sx=960, sy=560),
      ppl=[P('mom', 'corner_seat', turn=0.62, expr='too_still', blink=False, hands='knees', sil=0.86, sil_c='#07050a', sil_rim='#ffcf8f', sil_rim_a=0.45,
             sil_side=1, sil_eyes=0.9, room_light=False,
             act=_A(rock, lookxy(1500, 640, -9, tms, 0.3, z=300.0), lookxy(1650, 700, tms, None, 0.9, z=300.0)))],
      c=dict(mv='push', f=1.0, rate=0.012), focus_on='mom')

    def dark_corner(eye_y, side=-1):
        # the bust in the dark: black all round, a soft band of the bulb's light across her eyes from one side
        def draw(pen, tt):
            full = rect(-500, -400, 2920, 1880)
            pen.linear(full, 0, eye_y - 260, 0, eye_y + 260, [(0, '#030206', 238), (0.36, '#030206', 150), (0.5, '#030206', 35), (0.62, '#030206', 150),
                                                               (1, '#030206', 245)])
            pen.linear(full, 960 + side * 700, 0, 960 - side * 700, 0, [(0, '#030206', 0), (0.55, '#030206', 60), (1, '#030206', 200)])
        lay = Layer(0.3, draw, 'dark_corner', blur=0)
        return lay
    C(T(230), 'bust', who='mom', bg=('attic', 'corner'), set=dict(bulb=1.0), bg_dim=0.85, cx=960, cy=620, scale=0.92, turn=0.35, expr='too_still', blink=False,
      light=dict(rim='#ffcf8f', rim_a=90, side=-1, key=-0.55), act=_A(lookxy(1500, 640, -9, None, 0.3, z=300.0), pose(-9, None, 0.1, still=0.9)),
      acts=lambda A, s, sp: [dark_corner(bust_eyes('mom', 960, 620, 0.92)[1])], c=dict(mv='push', x=960, y=600, zrate=0.012), music=[(t(230), 'hit', 0.75)])
    # 231 "I never saw her sitting there."  from her corner: past the boxes to June at the chest, the narrator at the top of the stairs
    C(T(231), 'set', room='attic', view='mom', set=dict(bulb=1.0), rim=BULB,
      ppl=[P('june', 'chest_floor', kind='floor', turn=-0.6, expr='neutral', act=_A(lookxy(400, 500, t(231) + 0.2, None, 0.5, z=200.0))),
           P('narrator', 'stair_top', expr='haunted', face='chest_floor', act=_A(lookxy(300, 520, t(231) - 0.2, None, 0.6, z=200.0), ex('shock', t(231) + 0.3, None, 0.6)))],
      c=dict(mv='push', f=1.15, rate=0.015))


# ==================================================================================================== RULE 6: THE BATHROOM (589.8 - 698.1)
TUB_CAM = cm((-2.55, 6.3, 4.15), (-2.0, 8.2, 3.55), S=1050, sx=960, sy=560)            # into the tub from the left of the door
FLOOR_CAM = cm((-2.15, 8.0, 0.22), (-3.05, 9.3, 0.18), S=900, sx=960, sy=720)            # low on the kitchen floor by the back door
UPMID = cm((1.7, 5.17, 4.3), (4.3, 5.17, 4.15), S=1250, sx=960, sy=520)                    # down the corridor to the east end (Mom)
# sitting in the tub side by side, close enough for the narrator's hand to cover June's mouth (the anchors left 0.74 m)
TUB_KIDS = [P('narrator', (-2.25, 8.22, 2.93), kind='seat', seat=0.0, seat_ok=True, expr='terror', turn=-0.35),
            P('june', (-1.8, 8.22, 2.93), kind='seat', seat=0.0, seat_ok=True, expr='terror', turn=-0.3)]


def feet_gap(t0, t1, u=(0.42, 0.62), wob=0.03):
    """Two foot shadows in the light under the bathroom door between t0 and t1 (fractions of the gap)."""
    def f(tt):
        if not (t0 <= tt <= t1): return []
        s_ = math.sin(tt * 1.3) * wob
        return [(u[0] + s_, u[0] + 0.08 + s_), (u[1] + s_, u[1] + 0.08 + s_)]
    return f


def tub_hand(A, s, sp, t0=None):
    n, j = A['narrator'], A['june']
    n.hand_over(s.t0 - 2.0 if t0 is None else t0, -1, j, 'mouth', dur=0.01 if t0 is None else 0.5)
    n.reach_to(s.t0 - 2.0, 1, (j, 'chest'), dur=0.01, contact='palm', shape='relaxed', z=80.0)
    gz = scr(sp, (-1.62, 5.85, 3.3))
    n.look_at(s.t0 - 2.0, gz, None, 0.01, z=300.0); j.look_at(s.t0 - 2.0, gz, None, 0.01, z=300.0)
    return []


def plan_rule6(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(232), 'rule', n=6)
    # 236 "At 4:30, the kitchen window explodes."
    tsm = w(236, 'explodes') + 0.05
    C(T(236), 'ins', name='clock', kw=dict(time=(4, 30)), c=dict(mv='push', rate=0.03))
    C(w(236, 'the') - 0.1, 'set', room='kitchen', view='back', set=dict(kitchen=0.0, smash_t=tsm), c=dict(mv='push', f=1.15, rate=0.02, hit=[(tsm, 9.0)]),
      sfx=[(tsm, 'window_smash', 3, 0, 'inside')], music=[(tsm, 'hit', 0.9)])
    # 237 "The back door crashes open."
    tcr = w(237, 'crashes') + 0.05
    C(T(237), 'set', room='kitchen', view='door', set=dict(kitchen=0.0, crash_t=tcr), c=dict(mv='push', f=1.1, rate=0.02, hit=[(tcr, 10.0)]),
      sfx=[(tcr, 'door_crash', 3, 0, 'inside')], music=[(tcr, 'hit', 0.85)])
    # 238 "Something heavy comes inside."  a huge dark shape fills the doorway and steps down into the kitchen
    C(T(238), 'set', room='kitchen', view='door', set=dict(kitchen=0.0, back_door=100.0, mud=0.4), rim=MOON,
      ppl=[P('bunny', (-3.3, 10.9, 0.45), path=[(T(238) + 0.2, (-3.3, 10.9, 0.45)), (T(238) + 1.0, (-3.3, 10.15, 0.45)), (T(239), (-3.25, 9.35, 0.0))],
             surface='heavy', sil=0.9, sil_rim='#9fb6ff', sil_rim_a=0.55, turn=0.0, act=lambda a, s: a.drag_hatchet(-9, None, side=-1))],
      c=dict(mv='push', f=1.0, rate=0.02), sfx=[(T(238) + 1.0, 'floor_creak_heavy', -2, 0, 'inside')])
    # 239 "Wet."  240 "Dragging."  low on the floor: filthy wet feet, the hatchet head dragging on the linoleum
    C(T(239), 'set', room='kitchen', view='back', cam=FLOOR_CAM, set=dict(kitchen=0.0, mud=1.0, smash=1.0, back_door=100.0), rim=MOON,
      ppl=[P('bunny', (-3.2, 9.6, 0.0), path=[(T(239), (-3.2, 9.6, 0.0)), (T(241), (-2.55, 8.45, 0.0))], surface='heavy', dimk=0.35, room_light=False,
             act=lambda a, s: a.drag_hatchet(-9, None, side=-1))],
      c=dict(mv='push', f=1.0, rate=0.02), focus=1.4, sfx=[(t(239), 'wet_step', 0, 0, 'inside'), (t(240) - 0.05, 'wet_drag', 0, 0, 'inside', dict(dur=1.0, hatchet=True))])
    # 241 "I grab June and run."  down the corridor toward us, to the bathroom
    C(T(241), 'set', room='up', view='west', set=dict(upstairs=0.0, june_door=70.0), rim=NIGHT,
      ppl=[P('narrator', (0.7, 5.45, 2.85), path=[(T(241), (0.7, 5.45, 2.85)), (T(242) + 0.3, (-1.25, 5.42, 2.85))], run=True, expr='terror'),
           P('june', (1.05, 5.15, 2.85), path=[(T(241) + 0.1, (1.05, 5.15, 2.85)), (T(242) + 0.35, (-0.95, 5.12, 2.85))], run=True, expr='terror')],
      c=dict(mv='push', f=1.1, rate=0.02))
    # 242 "Bathroom."  they dash in, the door swings shut
    tdoor = T(242) + 0.45
    C(T(242), 'set', room='up', view='bath', set=dict(upstairs=0.0, bath_door=lambda tt, a=tdoor: 75.0 * (1.0 - ease_in_out(clamp((tt - a) / 0.25)))),
      rim=NIGHT, ppl=[P('june', (-1.1, 5.35, 2.85), path=[(T(242), (-1.1, 5.35, 2.85)), (tdoor - 0.05, (-1.95, 6.65, 2.85))], run=True, surface='inside_quiet'),
                      P('narrator', (-0.75, 5.3, 2.85), path=[(T(242), (-0.75, 5.3, 2.85)), (tdoor, (-1.55, 6.2, 2.85))], run=True, surface='inside_quiet')],
      c=dict(mv='push', f=1.0, rate=0.02), sfx=[(tdoor + 0.25, 'door_slam', -2, 0, 'inside', dict(kind='bathroom'))])
    # 243 "Lock."
    tlk = t(243)
    C(T(243), 'ins', name='lock', kw=lambda tr, a=tlk - T(243): dict(lock=lambda tt: ease_in_out(clamp((tt - a) / 0.15)), knob=0.0, key=0.0),
      c=dict(mv='push', rate=0.04), sfx=[(tlk + 0.05, 'lock_turn', 0, 0, 'close', dict(kind='thumb_bolt'))])
    # 244 "We sit in the dark, in the empty bathtub, my hand over her mouth."
    C(T(244), 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=0.6, bath_light=0.0), rim=DARK, montage=True,
      ppl=TUB_KIDS, acts=lambda A, s, sp: tub_hand(A, s, sp, t0=w(244, 'hand') - 0.2), c=dict(mv='push', f=1.0, rate=0.02))
    # 245-246 "Footsteps on the stairs. Slow."  down the flight from the top: he climbs toward us, the hatchet hanging
    steps = ['step1', 'step3', 'step5', 'step7']
    t0s = T(245)
    keys = [(t0s + 0.1 + 0.85 * k, st) for k, st in enumerate(steps)]
    C(T(245), 'set', room='hall', view='top', set=dict(hall=0.0, upstairs=0.0), rim=NIGHT,
      ppl=[P('bunny', 'step1', path=keys, surface='stairs', step_gain=-2.0, dimk=0.4, room_light=False, act=lambda a, s: a.drag_hatchet(-9, None, side=-1))],
      c=dict(mv='push', f=1.0, rate=0.02), sfx=[(kk[0] + 0.3, 'hatchet_thunk', -3, 0, 'inside', dict(step=i)) for i, kk in enumerate(keys[1:])])
    # 247 "And behind them, something hard knocking against every step."  248 "Thunk."  249 "Thunk."  250 the old hatchet
    # three different pictures for the three hatchet lines: the flight from the side, the head knocking up each riser
    # (dragged by the matted paw); the blade biting one tread's nose on "Thunk."; the hatchet dragged along the
    # corridor runner on "the old hatchet from our woodpile" (the red paint band from the woodpile)
    hits247 = [T(247) + 0.5 + 0.85 * k for k in range(4)]
    C(T(247), 'ins', name='hatchet_steps', kw=dict(hits=tuple(round(x - T(247), 3) for x in hits247)), anim=True,
      c=dict(mv='hold', shake=0.8, hit=[(x, 4.0) for x in hits247]), sfx=[(x, 'hatchet_thunk', 0, 0, 'close', dict(step=k)) for k, x in enumerate(hits247)])
    C(T(248), 'ins', name='hatchet_thunk', kw=dict(hit_t=round(t(248) - T(248), 3)), anim=True,
      c=dict(mv='hold', shake=0.5, hit=[(t(248), 9.0)]), sfx=[(t(248), 'hatchet_thunk', 2, 0, 'close')])
    C(T(249), 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=0.6), rim=DARK, ppl=TUB_KIDS,
      acts=lambda A, s, sp: (tub_hand(A, s, sp), A['narrator'].flinch(t(249) + 0.02, 0.8), A['june'].flinch(t(249) + 0.04, 1.0)) and [],
      c=dict(mv='push', f=1.05, rate=0.02, hit=[(t(249), 4.0)]), sfx=[(t(249), 'hatchet_thunk', 0, 0, 'inside', dict(far=True))])
    C(T(250), 'ins', name='hatchet_pile', anim=True, c=dict(mv='push', rate=0.012), sfx=[(T(250) + 0.1, 'wet_drag', -6, 0, 'inside', dict(dur=1.8, hatchet=True))])
    # 251 "The doorknob turns."  252 "Gently."
    tkn = t(251) + 0.3
    C(T(251), 'set', room='bath', view='lock', set=dict(gap=0.6, lock=1.0, knob=lambda tt, a=tkn: 38.0 * math.sin(math.pi * clamp((tt - a) / 2.6))), rim=DARK,
      c=dict(mv='push', f=1.0, rate=0.025), sfx=[(tkn, 'knob_turn', -2, 0, 'close', dict(dur=2.6, gentle=True))], music=[(tkn - 0.2, 'silence', 0.0, 1.0)])
    # 253 "And the little girl's voice comes through the crack under the door."  254-256 L "Don't let her do the trick. Please. Don't close your eyes."
    C(T(253), 'set', room='bath', view='gap', set=dict(gap=1.0, feet=feet_gap(T(253) + 0.4, T(258) + 2.0)), c=dict(mv='push', f=1.0, rate=0.012))
    # "Don't let her do the trick.": in tight on the crack, the two shadows of its feet shifting in the light (the voice's
    # source, close)
    C(t(254) - 0.1, 'set', room='bath', view='gap', set=dict(gap=1.0, feet=feet_gap(T(253) + 0.4, T(258) + 2.0, wob=0.05)),
      c=dict(mv='push', f=1.7, rate=0.012, y=250))
    C(w(255, 'please') - 0.1, 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=0.6), rim=DARK, ppl=TUB_KIDS,
      acts=lambda A, s, sp: (tub_hand(A, s, sp), A['june'].look_at(s.t0 + 0.2, scr(sp, (-1.62, 5.85, 3.0)), None, 0.5, body=0.15)) and [],
      c=dict(mv='push', f=1.05, rate=0.02))
    # 257 "Something slides under the door."  258-264 the crayon drawing, part by part
    C(T(257), 'ins', name='drawing', kw=lambda tr: dict(slide=ease_out_cubic(clamp((tr - 0.2) / 1.2))), anim=True, c=dict(mv='push', rate=0.02),
      sfx=[(T(257) + 0.2, 'paper_slide', 0, 0, 'close', dict(dur=1.2))])
    C(T(258), 'ins', name='drawing', kw=dict(slide=1.0), c=dict(mv='keys', keys=[(T(258), 960, 560, 1.0, None, 1.05), (T(259), 960, 560, 1.0, 'push', 1.15)]))
    DR = {259: (770, 470, 2.1), 260: (760, 640, 2.0), 261: (930, 520, 2.1), 262: (1080, 520, 2.2), 263: (780, 280, 2.2), 264: (800, 270, 2.6)}
    for i, (x, y, f) in DR.items():
        C(T(i), 'ins', name='drawing', kw=dict(slide=1.0), c=dict(mv='keys', keys=[(T(i), x, y, 1.0, None, f), (T(i + 1), x, y, 1.0, 'push', f * 1.06)]),
          music=[(t(264), 'stinger', 0.7)] if i == 264 else [])
    # 265 "Then Mom's voice, from the end of the hall."  266 "A voice I've never heard her use."  267 M "GET OUT OF MY HOUSE."
    C(T(265), 'set', room='up', view='west', set=dict(upstairs=0.0), rim=NIGHT,
      ppl=[P('mom', 'hall_east', turn=-0.05, expr='determined', dimk=0.35, room_light=False)], c=dict(mv='push', f=1.5, rate=0.03))
    C(T(266), 'set', room='up', view='west', cam=UPMID, set=dict(upstairs=0.0), rim=NIGHT_L,
      ppl=[P('mom', 'hall_east', turn=0.0, expr='determined', act=_A(pose(-9, None, 0.1, brow_angry=0.8), lookxy(960, 500, -9, None, 0.3, z=500.0)))],
      c=dict(mv='push', f=1.0, rate=0.03))
    C(T(267), 'bust', who='mom', bg=('up', 'west', UPMID), set=dict(upstairs=0.0), cx=960, cy=620, scale=1.0, expr='determined', light=NIGHT_L,
      act=_A(pose(-9, None, 0.1, brow_angry=1.0, wide=0.4), lookxy(960, 520, -9, None, 0.3, z=500.0)), c=dict(mv='push', x=960, y=580, zrate=0.05),
      music=[(t(267), 'hit', 0.9)])
    # 268 "And the little girl screams back,"  269 L "IT'S MY HOUSE!"
    C(T(268), 'set', room='up', view='hall', set=dict(upstairs=0.0), rim=NIGHT,
      ppl=[P('bunny', (-0.7, 5.25, 2.85), turn=1.95, dimk=0.25, room_light=False,
             act=_A(lambda a, s: a.drag_hatchet(-9, None, side=-1), lambda a, s: a.turn(t(268) + 0.2, 0.05, 0.5)))],
      c=dict(mv='push', f=1.6, rate=0.02))
    C(T(269), 'bust', who='bunny', bg=('up', 'hall'), set=dict(upstairs=0.0), cx=960, cy=640, scale=1.05, light=NIGHT,
      act=_A(lambda a, s: a.flinch(t(269), 1.0), pose(t(269), None, 0.15, h_nod=-0.15, approach=0.2)), c=dict(mv='push', x=960, y=600, zrate=0.06, shake=3.0))
    # 270 "The whole hallway shakes."  271 "Something slams into the bathroom door."  272 "Screaming."  273 "A wet, heavy crack."
    tsl = w(271, 'slams') + 0.05
    C(T(270), 'set', room='bath', view='door', set=dict(gap=0.8, feet=feet_gap(T(270), T(272), (0.3, 0.6), 0.12)), c=dict(mv='push', f=1.0, rate=0.02, shake=3.0,
                                                                                                                        hit=[(t(270) + 0.1, 7.0), (t(270) + 0.7, 5.0)]),
      sfx=[(t(270), 'struggle', 2, 0, 'inside', dict(dur=1.6, through_door=True))])
    C(T(271), 'set', room='bath', view='door', set=dict(gap=0.8, slam=tsl), c=dict(mv='push', f=1.05, rate=0.02, shake=2.0, hit=[(tsl, 12.0)]),
      sfx=[(tsl, 'door_slam', 4, 0, 'inside', dict(kind='body'))], music=[(tsl, 'hit', 0.95)])
    C(T(272), 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=0.6), rim=DARK, ppl=TUB_KIDS,
      acts=lambda A, s, sp: (tub_hand(A, s, sp), A['narrator'].eyes_shut(s.t0, None, 1.0), A['june'].eyes_shut(s.t0, None, 1.0)) and [],
      c=dict(mv='push', f=1.05, rate=0.02, shake=2.0), sfx=[(T(272), 'scream_far', 0, 0, 'inside', dict(through_door=True, dur=0.9))])
    tck = t(273) + 0.1
    C(T(273), 'set', room='bath', view='gap', set=dict(gap=lambda tt, a=tck: 1.0 - 0.75 * ease_in_out(clamp((tt - a) / 0.15)),
                                                     feet=lambda tt, a=tck: [(0.05, 0.95)] if tt > a else [(0.35, 0.45), (0.55, 0.65)]),
      c=dict(mv='push', f=1.0, rate=0.02, hit=[(tck, 6.0)]), sfx=[(tck, 'wet_crack', 4, 0, 'inside')], music=[(tck, 'sub_drop', 0.9)])
    # 274 "Then nothing."  275 "Then, softly, Mom's voice."  276-278 M "It's over, sweetheart. It's gone. You can open the door now."
    C(T(274), 'set', room='bath', view='door', set=dict(gap=0.35), c=dict(mv='hold', f=1.05, shake=0.4), music=[(T(274), 'silence', 0.0, 2.2)])
    C(T(275), 'set', room='bath', view='gap', set=dict(gap=0.6, feet=feet_gap(T(275) + 0.6, T(279) + 2.0, (0.44, 0.58), 0.0)), c=dict(mv='push', f=1.0, rate=0.015))
    C(T(276), 'set', room='bath', view='door', set=dict(gap=0.6, feet=feet_gap(T(276), T(279) + 2.0, (0.44, 0.58), 0.0)), c=dict(mv='push', f=1.0, rate=0.02))
    # 279-280 "Rule six. Not even me."  281 "I don't open it."
    C(T(279), 'rule', n=6, recall=True)
    C(T(281), 'bust', who='narrator', bg=('bath', 'tub', TUB_CAM), set=dict(gap=0.6), cx=940, cy=620, scale=0.9, turn=-0.25, expr='determined', light=DARK,
      act=lookxy(900, 420, -9, None, 0.3, z=500.0))


# ==================================================================================================== RULE 7: SUNRISE (698.1 - 788.9)
UP_DAWN = cm((-2.9, 5.1, 4.25), (-0.4, 5.25, 3.7), S=1100, sx=960, sy=520)                 # the wrecked corridor at dawn, toward June's door
FLOOR_BG = ('#3a281c', '#1a110c')


def dale_bust(F, C, t0, scale, cy, act, c=None, **kw):
    """Dale's face under the half-off head, seen from above (he lies on his back at the foot of the stairs, dawn)."""
    C(t0, 'bust', who='bunny', plain=FLOOR_BG, cx=960, cy=cy, scale=scale, expr='little_girl', light=DAWN, grade='ob_dawn',
      act=_A(pose(-9, None, 0.01, unmask=1.0, h_turn=0.1), act), c=c, **kw)


def plan_rule7(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    C(T(282), 'rule', n=7)
    # 284 "So we don't."  285 "We sit in that bathtub and stare at the door."
    C(T(284), 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=0.5), rim=DARK, ppl=TUB_KIDS,
      acts=lambda A, s, sp: (tub_hand(A, s, sp), A['narrator'].set(s.t0, None, 0.3, wide=0.5), A['june'].set(s.t0, None, 0.3, wide=0.5)) and [],
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(285), 'set', room='bath', view='door', set=dict(gap=0.5), c=dict(mv='push', f=1.0, rate=0.012))
    # 286 "At 6:12, the light under the door turns gold."
    tgd = w(286, 'gold') - 0.2
    C(T(286), 'ins', name='clock', kw=dict(time=(6, 12), kind='digital'), c=dict(mv='push', rate=0.03))
    C(w(286, 'the') - 0.1, 'set', room='bath', view='gap', set=dict(gap=lambda tt, a=tgd: 0.35 + 0.65 * ease_in_out(clamp((tt - a) / 1.0)), gap_col=ST.DAWN_C, tod='dawn'),
      c=dict(mv='push', f=1.0, rate=0.02), music=[(tgd, 'swell', 0.5, 4.0)])
    # 287 "Sunrise."  288 "Easter morning."
    C(T(287), 'set', room='yard', view='woods', set=dict(tod='dawn'), c=dict(mv='push', f=1.3, rate=0.02), sfx=[(T(287), 'birds_dawn', -6, 0, 'outside')])
    C(T(288), 'set', room='front', view='house', set=dict(tod='dawn', front_light=0.0), c=dict(mv='push', f=1.0, rate=0.02))
    # 289 "Mom knocks, softly."  290-293 M "It's sunrise, babies. You did it. You followed every single rule. I'm so proud of you."
    kn = [t(289) + 0.95, t(289) + 1.2, t(289) + 1.45] if e(289) + 0.4 < t(290) else [e(289) + 0.05, e(289) + 0.2, e(289) + 0.35]
    C(T(289), 'set', room='bath', view='door', set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn', feet=feet_gap(T(289), T(294), (0.44, 0.58), 0.0)),
      c=dict(mv='push', f=1.0, rate=0.015, hit=[(k, 2.0) for k in kn]),
      sfx=[(k, 'knock_door', -6, 0, 'inside', dict(soft=True, index=i)) for i, k in enumerate(kn)])
    C(T(290), 'set', room='bath', view='gap', set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn', feet=feet_gap(T(290), T(294), (0.44, 0.58), 0.0)),
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(292), 'set', room='bath', view='tub', cam=TUB_CAM, set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn'), rim=DAWN, ppl=TUB_KIDS,
      acts=lambda A, s, sp: (A['june'].set(t(292) + 0.2, None, 0.5, lean=0.25, crouch=-0.2),
                             A['narrator'].reach_to(t(292) + 0.6, -1, (A['june'], 'shoulder_l'), dur=0.4, contact='palm', shape='grip', z=60.0),
                             A['june'].look_at(s.t0, scr(sp, (-1.62, 5.85, 3.2)), None, 0.3), A['narrator'].look_at(s.t0, (A['june'], 'eyes'), None, 0.3)) and [],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 294 "Before sunrise."  295 "That's what the rule said."  296 "And it isn't before sunrise anymore."
    C(T(294), 'bust', who='narrator', bg=('bath', 'tub', TUB_CAM), set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn'), cx=960, cy=620, scale=0.95, turn=-0.2,
      expr='haunted', light=DAWN_L, act=_A(pose(t(294) + 0.15, None, 0.45, wide=1.0, brow_up=0.95, brow_sad=0.35, blink=0.0), lookxy(1100, 380, -9, None, 0.3, z=600.0)))
    C(T(295), 'rule', n=7, recall=True)
    C(T(296), 'set', room='bath', view='gap', set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn', feet=feet_gap(T(296), T(297) + 1, (0.44, 0.58), 0.0)),
      c=dict(mv='push', f=1.05, rate=0.02))
    # 297 "The lock turns by itself."  298 "From the outside."  299 "Mom has a key."
    tl0 = t(297) + 0.3
    C(T(297), 'ins', name='lock', kw=lambda tr, a=tl0 - T(297): dict(lock=lambda tt: 1.0 - ease_in_out(clamp((tt - a) / 0.9)), key=0.0), anim=True,
      c=dict(mv='push', rate=0.035), sfx=[(tl0, 'lock_turn', 0, 0, 'close', dict(kind='by_itself', dur=0.9))], music=[(tl0, 'hit', 0.6)])
    C(T(298), 'ins', name='lock', kw=lambda tr: dict(lock=0.0, key=ease_in_out(clamp((tr - 0.2) / 0.7))), anim=True,
      c=dict(mv='keys', keys=[(T(298), 960, 700, 1.0, None, 1.4), (T(299), 960, 720, 1.0, 'push', 1.6)]), sfx=[(T(298) + 0.2, 'key_in_lock', 0, 0, 'close')])
    # "Mom has a key.": the reverse, from the wrecked corridor in the dawn light: Mom at the bathroom door, the key in the
    # keyhole (the keyhole anchor had its plan y and height swapped: her reach went to the wrong height), she turns it,
    # pushes the door open and smiles in at them
    top = t(299) + 0.45
    MOMD = lambda a, s: (a.set(-9, None, 0.01, scratch=1.0, mess=0.6), a.hold_prop('dress_tiny', 1),
                         a.reach(-9, None, 1, out=30.0, down=200.0, fwd=140.0, shape='grip', up=0.0, fade=0.01))

    def key_acts(A, s, sp):
        m = A['mom']
        kh = scr(sp, 'bath_keyhole')
        m.hold_prop('key', -1, -9.0, top + 0.1)
        m.reach_to(s.t0 - 0.5, -1, kh, t1=top - 0.05, dur=0.3, contact='grip', shape='grip', prop='key', z=-40.0, rot=-30.0)
        m.reach_to(top - 0.05, -1, lambda tt: scr(sp, (-1.6 + 0.35 * ease_in_out(clamp((tt - top) / 1.0)), 5.79, 3.82)), t1=top + 0.9, dur=0.25,
                   contact='palm', shape='flat', z=-40.0)
        m.look_at(s.t0, kh, top - 0.1, 0.3)
        m.look_at(top + 0.2, scr(sp, (-1.9, 6.6, 3.9)), None, 0.5)
        m.expr('proud', top + 0.3, None, 0.6)
        return []
    C(T(299), 'set', room='up', view='west', cam=cm((0.55, 5.05, 4.2), (-1.45, 5.75, 3.85), S=980, sx=960, sy=540),
      set=dict(wrecked=1.0, tod='dawn', bath_door=lambda tt, a=top: 70.0 * ease_in_out(clamp((tt - a) / 1.0))), rim=DAWN,
      ppl=[P('mom', (-1.05, 5.38, 2.85), face=(-1.4, 5.8), expr='too_still', act=_A(MOMD))], acts=key_acts,
      c=dict(mv='push', f=1.0, rate=0.012), sfx=[(top - 0.15, 'key_turn', -4, 0, 'inside'), (top, 'door_creak', -2, 0, 'inside', dict(kind='bathroom_open'))])
    # 300 "The hallway is wrecked."  301 "Mom's arms are scratched to ribbons, and she's smiling."
    C(T(300), 'set', room='up', view='hall', set=dict(wrecked=1.0, tod='dawn', bath_door=70.0), c=dict(mv='push', f=1.15, rate=0.03))
    # her bare forearms first (the cardigan pushed up, scratched to ribbons, the little dress in her fist), then on
    # 'smiling' her face
    tsm2 = w(301, 'smiling') - 0.35
    C(T(301), 'set', room='up', view='west', cam=cm((-1.45, 5.3, 3.85), (-0.35, 5.2, 3.75), S=1700, sx=960, sy=520), set=dict(wrecked=1.0, tod='dawn', bath_door=70.0),
      rim=DAWN, ppl=[P('mom', (-0.35, 5.2, 2.85), turn=-0.15, expr='proud',
                       act=_A(MOMD, lookxy(960, 420, -9, None, 0.3, z=500.0),
                              lambda a, s: a.reach(t(301) + 0.1, None, -1, out=40.0, down=150.0, fwd=180.0, shape='open', up=0.0, fade=0.6)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(tsm2, 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=dict(wrecked=1.0, tod='dawn'), cx=960, cy=630, scale=1.0, turn=0.1, expr='proud', light=DAWN,
      act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6), pose(tsm2 + 0.2, None, 0.8, smile=0.85), lookxy(960, 480, -9, None, 0.3, z=600.0)),
      c=dict(mv='push', x=960, y=590, zrate=0.012))
    # 302 "At the bottom of the stairs, the Bunnyman lies on his back, not moving."  303 "The head of the suit has come halfway off."
    BODY = lambda u: P('bunny', 'stairs_bottom_body', kind='lie', lie_face='up', arms='out', expr='little_girl',
                       act=_A(pose(-9, None, 0.01, unmask=u), lambda a, s: a.dead(-9, 0.01), lambda a, s: a.face(1.0)))
    C(T(302), 'set', room='hall', view='top', cam=cm((0.82, 4.45, 4.1), (0.6, 0.6, 0.15), S=1150, sx=960, sy=560), set=dict(tod='dawn', hall=0.0, upstairs=0.0),
      rim=DAWN, ppl=[BODY(0.6)], c=dict(mv='hold', f=1.0, shake=0.5))
    dale_bust(F, C, T(303), 0.8, 640, pose(-9, None, 0.01, unmask=0.6, look_x=0.2, look_y=-0.7, _gaze=1.0), c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 304 "Inside, there's no monster."  305-306 "It's a man. Maybe fifty-five."  307-308 "Grey stubble. Skin and bone."
    dale_bust(F, C, T(304), 0.9, 600, pose(-9, None, 0.01, look_x=0.2, look_y=-0.7, _gaze=1.0), c=dict(mv='push', x=960, y=560, zrate=0.02))
    dale_bust(F, C, T(305), 1.2, 600, pose(-9, None, 0.01, look_x=0.2, look_y=-0.7, _gaze=1.0), c=dict(mv='push', x=960, y=560, zrate=0.02))
    dale_bust(F, C, T(307), 1.6, 480, pose(-9, None, 0.01, look_x=0.2, look_y=-0.7, _gaze=1.0), c=dict(mv='push', x=960, y=640, zrate=0.02))
    # 309 "He's staring up at June's bedroom door with the eyes of a terrified little girl."  the eyes; what they look at
    dale_bust(F, C, T(309), 1.35, 640, pose(-9, None, 0.01, look_x=0.1, look_y=-0.85, _gaze=1.0, wet=1.0, tears=0.8), c=dict(mv='push', x=960, y=480, zrate=0.025))
    C(w(309, "june's") - 0.1, 'set', room='hall', view='foot', set=dict(tod='dawn', hall=0.0, upstairs=0.0), c=dict(mv='push', f=1.6, rate=0.03))
    C(w(309, 'eyes') - 0.15, 'bust', who='bunny', plain=FLOOR_BG, cx=960, cy=720, scale=1.8, expr='little_girl', light=DAWN, grade='ob_dawn',
      act=pose(-9, None, 0.01, unmask=1.0, h_turn=0.1, look_x=0.1, look_y=-0.85, _gaze=1.0, wet=1.0, tears=1.0), c=dict(mv='push', x=960, y=540, zrate=0.02))
    # 310 "His lips move one last time."  311 D "Mama."  312 "Then he's still."
    def mama(a, s, t0=t(311), t1=e(311)):
        # the suit's cast has no talking mouth (the mask); Dale's own lips shape the two syllables of "Mama." by hand
        def fn(P_, tt):
            if t0 - 0.05 <= tt <= t1 + 0.1:
                u = clamp((tt - t0 + 0.05) / max(0.2, t1 - t0 + 0.15))
                P_.m_open += 0.28 * abs(math.sin(u * 2.0 * math.pi)) * (1.0 - 0.3 * u)
        a._add(t0 - 0.1, t1 + 0.2, fn, real=True)
    DALE_EYES = pose(-9, None, 0.01, look_x=0.1, look_y=-0.8, _gaze=1.0, wet=1.0, tears=0.9)
    dale_bust(F, C, T(310), 1.5, 520, _A(DALE_EYES, mama), c=dict(mv='push', x=960, y=600, zrate=0.012))
    dale_bust(F, C, t(311) - 0.25, 2.1, 330, _A(DALE_EYES, mama), c=dict(mv='hold', x=960, y=560, shake=0.3), music=[(e(311) + 0.2, 'sub_drop', 0.7)])
    dale_bust(F, C, T(312), 1.25, 600, _A(DALE_EYES, lambda a, s: a.dead(t(312) + 0.2, 1.2)), c=dict(mv='hold', x=960, y=560, shake=0.2))
    # 313 "Mom kneels in front of June, holding the little yellow dress, and gently puts one hand over June's eyes."
    tpu = w(313, 'puts') - 0.1
    C(T(313), 'set', room='up', view='west', cam=UP_DAWN, set=dict(wrecked=1.0, tod='dawn', bath_door=70.0), rim=DAWN,
      ppl=[P('june', (-0.05, 5.35, 2.85), face=(-0.55, 5.1), expr='neutral'),
           P('mom', (-0.55, 5.05, 2.85), path=[(T(313), (-1.0, 4.95, 2.85)), (T(313) + 1.0, (-0.6, 5.05, 2.85))], face=(-0.05, 5.35), expr='proud', kind='stand',
             act=_A(MOMD, lambda a, s: a.kneel_down(T(313) + 1.1, 0.8, knees=0))),
           P('narrator', (0.55, 5.55, 2.85), face=(-0.3, 5.2), expr='haunted')],
      acts=lambda A, s, sp: [A['mom'].look_at(s.t0, (A['june'], 'eyes'), None, 0.3), A['june'].look_at(s.t0, (A['mom'], 'eyes'), None, 0.3)] and [],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='mom')

    def eyes_acts(A, s, sp):
        m, j, n = A['mom'], A['june'], A['narrator']
        m.hand_over(tpu + 0.1, -1, j, 'eyes', dur=0.8)
        m.look_at(s.t0, (j, 'eyes'), None, 0.3); j.look_at(s.t0, (m, 'eyes'), tpu + 0.5, 0.3)
        n.look_at(s.t0, (m, 'hand_r'), None, 0.4)
        return []
    C(tpu, 'set', room='up', view='west', cam=cm((-1.6, 5.75, 4.0), (-0.3, 5.2, 3.85), S=1350, sx=960, sy=520), set=dict(wrecked=1.0, tod='dawn', bath_door=70.0), rim=DAWN,
      ppl=[P('june', (-0.05, 5.35, 2.85), face=(-0.55, 5.1), expr='neutral'),
           P('mom', (-0.6, 5.05, 2.85), face=(-0.05, 5.35), expr='proud', kind='kneel', knees=0, act=MOMD),
           P('narrator', (0.5, 5.6, 2.85), face=(-0.3, 5.2), expr='haunted')],
      acts=eyes_acts, c=dict(mv='push', f=1.0, rate=0.025), focus_on='mom')
    # 314-315 M "Happy Easter, bunny. Want to see a magic trick?"  316-317 M "Close your eyes. And count to seven."
    C(T(314), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=dict(wrecked=1.0, tod='dawn'), cx=900, cy=640, scale=0.95, turn=0.35, expr='proud', light=DAWN,
      act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6), lookxy(1500, 640, -9, None, 0.3, z=300.0), pose(-9, None, 0.1, h_nod=0.15)))
    C(T(316), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=dict(wrecked=1.0, tod='dawn'), cx=980, cy=660, scale=1.12, turn=0.3, expr='too_still', light=DAWN,
      act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6, smile=0.7), lookxy(1500, 680, -9, None, 0.3, z=300.0)), music=[(t(317), 'pulse_on', 0.6)])
    # 318-321 J "One," June whispers. "Two. Three."  Mom's hand over her eyes
    C(T(318), 'bust', who='june', bg=('up', 'west', UP_DAWN), set=dict(wrecked=1.0, tod='dawn'), cx=940, cy=620, scale=0.95, turn=-0.2, expr='neutral', light=DAWN_L,
      act=lambda a, s: a.eyes_shut(-9, None, 0.0),
      hands=[dict(who='mom', fn=paw_eyes('june', 940, 620, 0.95, side=-1, size=430), size=430, shape='open', side=-1, sleeve_from=lambda tt: (-260, 1000),
                  scratch=True, depth=0.95)],
      c=dict(mv='push', x=940, y=560, zrate=0.02))


# ==================================================================================================== THE REVEAL (788.9 - 914.3)
TRADE_CAM = cm((-3.05, -1.3, 1.0), (-3.05, 1.6, 0.85), S=1100, sx=960, sy=560)      # the woods, 1987: the mascot kneels to Laurie
UNDER_CAM = cm((-2.8, 7.6, 0.3), (-0.6, 9.6, -1.6), S=1000, sx=960, sy=560)         # down the bank to the gravel under the bridge
UNDER_TOP = cm((-1.55, 7.75, 1.75), (-0.6, 9.65, -2.05), S=880, sx=960, sy=620)       # from under the trestle, steeply down at the gravel
UNDER_SIDE = cm((-0.4, 7.0, ST._bank_Y(7.0) + 1.5), (-0.4, 9.8, ST._bank_Y(9.8) + 1.0), S=1000, sx=960, sy=560)
WOODS_PATH = cm((-6.3, -5.2, 0.9), (-2.4, 3.0, 0.7), S=1000, sx=960, sy=600)
D87 = dict(era='1987', vhs=False, rim=MEMORY, grade='ob_memory')
RECALL = dict(era='recall', post=dict(sat=0.45, exposure=-0.05))
BY = ST._bank_Y


def paw_eyes(who, cx, cy, sc, t_in=None, side=-1, size=560):
    """A paw (or a hand) laid over the eyes of a bust drawn at (cx, cy, sc), coming in from the side: the wrist sits
    0.6 of the hand's length out from the eyes, so the fingers end just past the far eye."""
    def fn(tt):
        # the palm lies over BOTH eyes, its lower edge on the bridge of the nose: the mouth stays free (June's counting
        # lips) and the hand comes from the side and from below, where the kneeling arm is
        ex_, ey_ = bust_eyes(who, cx, cy, sc)
        k = 1.0 if t_in is None else ease_out_cubic(clamp((tt - t_in) / 0.5))
        x = ex_ + side * (0.58 * size + 600.0 * (1.0 - k))
        y = ey_ - 0.07 * size + 220.0 * (1.0 - k)
        return (x, y, 264.0 if side < 0 else 96.0, 1.0)
    return fn


def plan_reveal(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    UPD = dict(wrecked=1.0, tod='dawn')
    # 322 "And that's when I finally understand all of it."
    C(T(322), 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=610, scale=0.95, turn=0.1, expr='haunted', light=DAWN_L,
      act=_A(ex('shock', t(322) + 0.9, None, 0.6), lookxy(1100, 640, -9, None, 0.3, z=400.0)), c=dict(mv='push', x=960, y=560, zrate=0.03),
      music=[(t(322), 'riser', 0.6, 3.0)])
    # 323 "In 1987, the Bunnyman didn't take my mother."  the parade photo, live on the tape: Laurie holding the mascot's paw
    C(T(323), 'ins', name='courier', cut='static', c=dict(mv='keys', keys=[(T(323), 760, 640, 1.0, None, 1.5), (T(324), 745, 660, 1.0, 'push', 1.8)]),
      sfx=[(T(323) + 0.05, 'paper', -12, 0, 'close', dict(kind='newspaper'))])
    # 324 "He traded with her."  the woods, 1987: he kneels and lays his paw over her eyes
    def trade(A, s, sp):
        b, l = A['bunny87'], A['laurie87']
        b.hand_over(t(324) + 0.15, -1, l, 'eyes', dur=0.6)
        b.look_at(s.t0 - 0.5, (l, 'eyes'), None, 0.3); l.look_at(s.t0 - 0.5, (b, 'eyes'), t(324) + 0.5, 0.3)
        return []
    C(T(324), 'set', room='woods', view='path', cam=TRADE_CAM, set=dict(tod='day87'), **D87,
      ppl=[P('bunny87', (-3.5, 1.6, 0.0), face=(-2.7, 1.6), kind='kneel', knees=0, room_light=False),
           P('laurie87', (-2.75, 1.6, 0.0), face=(-3.5, 1.6), expr='warm_smile', room_light=False)],
      acts=trade, c=dict(mv='push', f=1.0, rate=0.02), sfx=[(T(324), 'ambience_woods', -14, 0, 'woods', dict(dur=3.0, tod='day'))])
    # 325 "That's the trick."  her face under the paw;  326 "Whoever closes their eyes and counts to seven under its hand opens
    # them somewhere else."  the paw, the count (her lips), a white flash, and the eyes that open are not hers
    cx_, cy_, sc_ = 960, 600, 0.95
    C(T(325), 'bust', who='laurie87', bg=('woods', 'path', TRADE_CAM), set=dict(tod='day87'), **dict(D87, rim=None), cx=cx_, cy=cy_, scale=sc_,
      expr='warm_smile', light=MEMORY, act=lambda a, s: a.eyes_shut(-9, None, 0.0),
      hands=[dict(who='bunny87', fn=paw_eyes('laurie87', cx_, cy_, sc_, size=330), size=330, shape='paw', side=-1, sleeve_from=lambda tt: (-260, 980), depth=0.95)],
      c=dict(mv='push', x=960, y=560, zrate=0.02))
    top = w(326, 'opens') - 0.05
    C(T(326), 'bust', who='laurie87', bg=('woods', 'path', TRADE_CAM), set=dict(tod='day87'), **dict(D87, rim=None), cx=cx_, cy=cy_ + 20, scale=sc_ * 1.12,
      expr='neutral', light=MEMORY, act=_A(lambda a, s: a.eyes_shut(-9, top, 0.0), pose(-9, None, 0.1, squint=0.6, brow_sad=0.3)),
      hands=[dict(who='bunny87', fn=paw_eyes('laurie87', cx_, cy_ + 20, sc_ * 1.12, size=370), size=370, shape='paw', side=-1, sleeve_from=lambda tt: (-260, 980), depth=0.95)],
      c=dict(mv='push', x=960, y=560, zrate=0.025), music=[(w(326, 'seven'), 'heartbeat', 0.4, 1.6)])
    C(top, 'bust', who='laurie87', bg=('woods', 'path', TRADE_CAM), set=dict(tod='day87'), **dict(D87, rim=None), cx=cx_, cy=cy_ + 20, scale=sc_ * 1.12,
      expr='too_still', light=MEMORY, cut='white', act=_A(pose(-9, None, 0.01, still=0.9), lookxy(960, 560, -9, None, 0.01, z=600.0)),
      c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 327 "In someone else."  the mascot looking down at its own paws
    C(T(327), 'bust', who='bunny87', bg=('woods', 'path', TRADE_CAM), set=dict(tod='day87'), **dict(D87, rim=None), cx=960, cy=560, scale=0.9,
      light=MEMORY, act=_A(pose(-9, None, 0.3, h_nod=0.6), lookxy(960, 1020, -9, None, 0.3, z=200.0),
                           lambda a, s: a.reach(-9, None, 1, out=50.0, down=70.0, fwd=220.0, shape='paw_open', up=0.0, fade=0.4),
                           lambda a, s: a.reach(-9, None, -1, out=50.0, down=70.0, fwd=220.0, shape='paw_open', up=0.0, fade=0.4)),
      c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 328 "Dale Whitlock's body walked into those woods with a little girl."  hand in paw, into the trees
    C(T(328), 'set', room='woods', view='path', cam=WOODS_PATH, set=dict(tod='day87'), **D87,
      ppl=[P('bunny87', (-4.4, -2.6, 0.0), path=[(T(328), (-4.4, -2.6, 0.0)), (T(329), (-2.7, 2.4, 0.0))], surface='grass_quiet', room_light=False, dimk=0.1),
           P('laurie87', (-4.95, -2.4, 0.0), path=[(T(328), (-4.95, -2.4, 0.0)), (T(329), (-3.25, 2.6, 0.0))], surface='grass_quiet', room_light=False)],
      acts=lambda A, s, sp: [A['bunny87'].hold_hand(s.t0 - 1.0, 1, A['laurie87'], -1, dur=0.01)] and [],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 329 "And a little girl's body walked out."  330 "Clean."  331 "Calm."  332 "Humming."
    C(T(329), 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      ppl=[P('laurie87', (-2.5, 42.6, -0.45), path=[(T(329), (-2.5, 42.6, -0.45)), (T(330) + 0.2, (-2.6, 39.4, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False)],
      c=dict(mv='push', f=1.45, rate=0.02))
    C(T(330), 'set', room='yard', view='close', set=dict(tod='sunrise87'), era='1987', vhs=False, rim=SUN87, grade='ob_sunrise87',
      cam=cm((-2.62, 34.6, 0.6), (-2.6, 38.2, 0.2), S=1300, sx=960, sy=600),
      ppl=[P('laurie87', (-2.6, 39.6, -0.45), path=[(T(330), (-2.6, 39.6, -0.45)), (T(331) + 0.3, (-2.6, 38.6, -0.45))], surface='grass_quiet', turn=0.0,
             expr='too_still', room_light=False)],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(T(331), 'bust', who='laurie87', bg=('yard', 'close', None), set=dict(tod='sunrise87'), era='1987', vhs=False, cx=960, cy=590, scale=0.9,
      light=SUN87, expr='too_still', grade='ob_sunrise87', act=pose(-9, None, 0.1, still=0.8), c=dict(mv='push', x=960, y=560, zrate=0.02))
    C(T(332), 'bust', who='laurie87', bg=('yard', 'close', None), set=dict(tod='sunrise87'), era='1987', vhs=False, cx=1000, cy=620, scale=1.05, turn=-0.2,
      light=SUN87, expr='too_still', grade='ob_sunrise87', act=hum(t(332) - 0.1, None), c=dict(mv='push', x=980, y=580, zrate=0.02),
      sfx=[(t(332), 'hum', -10, 0, 'outside', dict(who='laurie87', dur=1.4))], music=[(t(332), 'jingle', 0.45, 1.6, dict(version='hum_child'))])
    # 333 "The real Laurie woke up under a railroad bridge, in a grown man's body, inside a bunny suit she was too scared to take off."
    tg = w(333, 'grown') - 0.15
    # seen from under the trestle, looking DOWN at the gravel: the mascot curled on its side, knees drawn up, one paw under
    # the head (the figure in profile, folded, lying on the ground: a body, not a starfish), the bridge's dark beams
    # framing the top; on 'woke' the head lifts a little and the paws stir
    C(T(333), 'set', room='woods', view='under', cam=UNDER_TOP, set=dict(tod='day87'), montage=True, **D87,
      ppl=[P('bunny87', 'under_bridge', kind='lie', lie_face='up', arms='side', turn=1.0, room_light=False, check=False,
             act=_A(pose(-9, None, 0.1, crouch=1.6, hunch=0.8, h_nod=0.45), pose(w(333, 'woke'), None, 0.8, h_nod=0.15, h_turn=-0.25),
                    lambda a, s: a.reach(-9, None, 1, out=-20.0, down=200.0, fwd=60.0, shape='paw', up=0.0, fade=0.01),
                    lambda a, s: a.reach(-9, None, -1, out=-10.0, down=230.0, fwd=90.0, shape='paw', up=0.0, fade=0.01),
                    lambda a, s: a.reach(w(333, 'woke') + 0.4, None, -1, out=10.0, down=120.0, fwd=200.0, shape='paw_open', up=0.0, fade=0.8),
                    blinks(w(333, 'woke') + 0.1)))],
      c=dict(mv='hold', f=1.0, shake=0.5), sfx=[(T(333), 'creek', -12, 0, 'woods', dict(dur=3.0))])
    tlift = w(333, 'take') - 0.4
    C(tg, 'bust', who='bunny87', bg=('woods', 'under', UNDER_CAM), set=dict(tod='day87'), **dict(D87, rim=None), cx=960, cy=580, scale=0.95, light=MEMORY,
      act=_A(pose(-9, None, 0.3, h_nod=0.5), lookxy(960, 1000, -9, tlift, 0.3, z=200.0), lookxy(1300, 500, tlift, None, 0.4, z=500.0),
             lambda a, s: a.reach(-9, None, 1, out=50.0, down=70.0, fwd=220.0, shape='paw_open', up=0.0, fade=0.4),
             lambda a, s: a.reach(-9, None, -1, out=50.0, down=70.0, fwd=220.0, shape='paw_open', up=0.0, fade=0.4)),
      c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 334 "For thirty-six years, she lived in those woods."  (now: the filthy suit, alone among the trees at night)
    C(T(334), 'set', room='woods', view='path', cam=WOODS_PATH, set=dict(tod='night', flashlight=0.0), rim=MOON,
      ppl=[P('bunny', (-3.4, 0.4, 0.0), path=[(T(334), (-3.4, 0.4, 0.0)), (T(335) + 0.4, (-2.9, 2.6, 0.0))], surface='grass_quiet', room_light=False, dimk=0.15)],
      c=dict(mv='push', f=1.0, rate=0.015), sfx=[(T(334), 'wind_gust', -12, 0, 'woods')])
    # 335 "She never grew up."  the masked head tilted, the paws held together like a child's
    C(T(335), 'bust', who='bunny', bg=('woods', 'path', WOODS_PATH), set=dict(tod='night', flashlight=0.0), cx=960, cy=600, scale=0.95, light=MOON,
      act=_A(pose(-9, None, 0.3, h_tilt=-14.0, h_nod=0.15), lambda a, s: a.reach(-9, None, 1, out=-10.0, down=40.0, fwd=210.0, shape='paw', up=0.0, fade=0.3),
             lambda a, s: a.reach(-9, None, -1, out=-10.0, down=40.0, fwd=210.0, shape='paw', up=0.0, fade=0.3)),
      c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 336 "She only knew one song."  under the bridge, swaying to it
    def sway(a, s):
        def fn(P_, tt):
            P_.h_tilt += 9.0 * math.sin((tt - s.t0) * 2.4); P_.tilt += 2.0 * math.sin((tt - s.t0) * 2.4 + 0.6)
        a._add(s.t0 - 0.5, None, fn, real=True)
    C(T(336), 'set', room='woods', view='under', cam=UNDER_SIDE, set=dict(tod='night', flashlight=0.0), rim=MOON, montage=True,
      ppl=[P('bunny', (-0.4, 10.0, BY(10.0)), face=(-0.4, 7.0), room_light=False, dimk=0.15, act=_A(sway, hum(T(336), None)))],
      c=dict(mv='push', f=1.05, rate=0.02), music=[(t(336) + 0.3, 'jingle', 0.45, 2.0, dict(version='hum', distant=True))])
    # 337 "And every Easter, she came home to the last house on Orchard Road, knocked her mother's knock, and waved at the little girl in the window."
    tkk = w(337, 'knocked') - 0.15; twv = w(337, 'waved') - 0.25
    C(T(337), 'set', room='yard', view='house', set=dict(kitchen=0.6, june_light=0.8), rim=MOON, montage=True,
      ppl=[P('bunny', 'treeline', face=(-2.6, 30.0), room_light=False, dimk=0.2)], c=dict(mv='push', f=1.0, rate=0.015))
    kt = [tkk + 0.15 + d for d in (0.0, 0.17, 0.55, 0.72, 0.89, 1.27, 1.44)]

    def knock_acts(A, s, sp):
        b = A['bunny']
        tgt = scr(sp, (-0.15, -0.03, 1.25))
        b.reach_to(tkk - 0.1, 1, tgt, t1=None, dur=0.25, contact='tips', shape='paw_grip', z=-30.0)
        def rap(P_, tt):
            for k in kt:
                if k - 0.08 <= tt <= k + 0.1: P_.hl_fwd = getattr(P_, 'hl_fwd', 0.0) - 26.0 * math.sin(clamp((tt - k + 0.08) / 0.18) * math.pi)
        b._add(tkk, None, rap, real=True)
        return []
    C(tkk, 'set', room='front', view='porch', cam=SLOT_OUT_WIDE, set=dict(front_light=1.0), rim=PORCH, montage=True,
      ppl=[P('bunny', (-0.3, -0.62, -0.03), face=(-0.3, 0.0), room_light=False)], acts=knock_acts, c=dict(mv='push', f=1.0, rate=0.02),
      sfx=[(k, 'knock_door', -3, 0, 'outside', dict(index=i, pattern='2-3-2', soft=True)) for i, k in enumerate(kt)])
    C(twv, 'set', room='yard', view='close', rim=MOON, montage=True, cam=cm((-2.6, 33.5, 1.0), (-2.6, 39.6, 1.0), S=1700, sx=960, sy=520),
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.15, act=lambda a, s: a.wave(s.t0 - 0.2, s.t1 + 2.0, side=1, slow=True))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 338 "Her daughter."  June at her window, waving back
    C(T(338), 'bust', who='june', bg=('june', 'door', JUNE_FROM_WINDOW), set=dict(nightlight=1.0), cx=900, cy=600, scale=0.88, turn=-0.15,
      expr='warm_smile', light=MOON, act=_A(lookxy(1100, 380, -9, None, 0.3, z=700.0), lambda a, s: a.wave(s.t0 - 1.0, s.t1 + 1.0, side=1, speed=0.7, height=0.9)))
    # 339 "Born from the body that was stolen from her."
    C(T(339), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=620, scale=0.95, expr='too_still', light=DAWN,
      act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6), pose(-9, None, 0.1, still=0.85), lookxy(1300, 700, -9, None, 0.3, z=300.0)),
      c=dict(mv='push', x=960, y=580, zrate=0.025))
    # 340 "Last Easter, Dad went to the bridge and talked to her."
    C(T(340), 'set', room='woods', view='under', cam=UNDER_SIDE, set=dict(tod='night', flashlight=0.0), era='memory', rim=MOON,
      ppl=[P('bunny', (0.45, 9.9, BY(9.9)), face=(-1.2, 9.7), room_light=False, dimk=0.15, act=tilt(t(340) + 1.0, -10.0, 2.0)),
           P('dad', (-1.2, 9.7, BY(9.7)), face=(0.45, 9.9), expr='determined', room_light=False, talk=False,
             act=lambda a, s: a.reach(-9, None, -1, out=40.0, down=60.0, fwd=150.0, shape='open', up=0.0, fade=0.6))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 341 "And the thing that called itself my mother followed him there."
    C(T(341), 'set', room='woods', view='path', cam=WOODS_PATH, set=dict(tod='night', flashlight=0.0), era='memory', rim=MOON,
      ppl=[P('mom', (-5.4, -3.4, 0.0), path=[(T(341), (-5.4, -3.4, 0.0)), (T(342), (-4.2, -0.6, 0.0))], expr='too_still', surface='grass_quiet',
             room_light=False, dimk=0.1)],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 342 "Every rule was true."  the laminated rules, each one lighting in turn
    C(T(342), 'ins', name='rules', kw=lambda tr: dict(hl=1 + min(6, int(tr / 0.2)), show=7), c=dict(mv='push', rate=0.03), music=[(t(342), 'hit', 0.6)])
    # 343 "Don't look at the treeline, so we'd never see who she was pointing at."
    C(T(343), 'set', room='yard', view='close', cam=cm((-5.2, 35.6, 1.2), (-2.6, 39.6, 1.25), S=1500, sx=1080, sy=500), set=dict(tod='night'), **RECALL, rim=MOON,
      ppl=[P('bunny', 'treeline', room_light=False, dimk=0.1, turn=-0.35, act=lambda a, s: a.point_at(s.t0 - 2.0, (140, 600), None, side=-1, dur=0.01, z=300.0))],
      c=dict(mv='push', f=1.0, rate=0.03), cut='static')
    C(w(343, 'who') - 0.1, 'set', room='june', view='door', set=dict(nightlight=1.0, hall=1.0), **RECALL, rim=LAMP,
      cam=cm((1.0, 8.2, 4.2), (0.8, 5.95, 4.0), S=1350, sx=960, sy=500),
      ppl=[P('mom', 'doorway', expr='too_still', turn=0.05, act=pose(-9, None, 0.1, still=0.6, smile=0.5))], focus_on='mom', c=dict(mv='push', f=1.0, rate=0.02))
    # 344 "Don't open the egg, so we'd never see her proof."
    C(T(344), 'ins', name='egg_halves', kw=dict(k_open=1.0), **RECALL, cut='static', c=dict(mv='keys', keys=[(T(344), 860, 600, 1.0, None, 1.3), (T(345), 820, 610, 1.0, 'push', 1.6)]))
    # 345 "Count the knocks in your head, so by morning, counting to seven would feel like nothing."  the door and the count
    k0 = T(345) + 0.4
    C(T(345), 'set', room='hall', view='door', set=dict(hall=0.4), **RECALL, rim=LAMP, cut='static', c=dict(mv='push', f=2.0, rate=0.012),
      tags=[(k0 + 0.42 * k, str(k + 1), 960 + KNOCK_TAGS[k][0], 540 + KNOCK_TAGS[k][1], 'white' if k < 6 else 'red', 9.0) for k in range(7)],
      tag_sound=False, sfx=[(k0 + 0.42 * k, 'knock_door', -10, 0, 'inside', dict(index=k, soft=True, memory=True)) for k in range(7)])
    # 346 "Don't answer the little girl, because she was the real Laurie."
    C(T(346), 'set', room='front', view='porch', cam=SLOT_OUT_CLOSE, set=dict(front_light=1.0), **RECALL, rim=PORCH, cut='static',
      ppl=[P('bunny', (-0.32, -0.62, -0.03), face=(-0.38, 0.0), act=bunny_at_slot(cry_t=T(346) - 1.0))], c=dict(mv='push', f=1.0, rate=0.02))
    C(w(346, 'because') - 0.1, 'bust', who='laurie87', bg=('yard', 'close', None), set=dict(tod='sunrise87'), era='1987', vhs=False, cx=960, cy=600, scale=0.92,
      light=SUN87, expr='sad', grade='ob_sunrise87', act=lookxy(960, 520, -9, None, 0.3, z=600.0), c=dict(mv='push', x=960, y=560, zrate=0.02))
    # 347 "Keep June in sight, so June would never leave this house."  June with the tiny dress, in the attic
    C(T(347), 'set', room='attic', view='chest', cam=ATTIC_MED, set=dict(bulb=1.0, chest='open'), **RECALL, rim=BULB, cut='static',
      ppl=[P('june', 'chest_floor', kind='floor', turn=-0.9, expr='neutral',
             act=_A(lambda a, s: a.hold_prop('dress_tiny', 1), lambda a, s: a.reach(-9, None, 1, out=40.0, down=-10.0, fwd=200.0, shape='grip', up=0.0, fade=0.01)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    # 348 "Lock yourselves in, so we wouldn't see what it did to her."
    C(T(348), 'set', room='bath', view='door', set=dict(gap=0.5, slam=T(348) + 0.35), **RECALL, cut='static', c=dict(mv='push', f=1.1, rate=0.02, hit=[(T(348) + 0.35, 5.0)]),
      sfx=[(T(348) + 0.35, 'door_slam', -6, 0, 'inside', dict(memory=True))])
    C(w(348, 'what') - 0.1, 'set', room='hall', view='bottom', cam=cm((-0.9, 2.6, 1.6), (0.45, 0.45, 0.2), S=950, sx=960, sy=580), set=dict(tod='dawn', hall=0.0),
      **RECALL, rim=DAWN, ppl=[P('bunny', 'stairs_bottom_body', kind='lie', lie_face='up', arms='out', act=_A(pose(-9, None, 0.01, unmask=0.6), lambda a, s: a.dead(-9, 0.01)))],
      c=dict(mv='push', f=1.0, rate=0.03))
    # 349 "And never close your eyes before sunrise..."  the gold under the door
    C(T(349), 'set', room='bath', view='gap', set=dict(gap=1.0, gap_col=ST.DAWN_C, tod='dawn'), **RECALL, cut='static', c=dict(mv='push', f=1.0, rate=0.02))
    # 350 "So the first time June closed them on Easter morning, it would be for Mom."  back to now: the hand over June's eyes, Mom's smile
    C(T(350), 'set', room='up', view='west', cam=cm((-1.6, 5.75, 4.0), (-0.3, 5.2, 3.85), S=1350, sx=960, sy=520), set=UPD, rim=DAWN, cut='white', quiet_cut=True,
      ppl=[P('june', (-0.05, 5.35, 2.85), face=(-0.55, 5.1), expr='neutral', act=lambda a, s: a.eyes_shut(-9, None, 0.0)),
           P('mom', (-0.6, 5.05, 2.85), face=(-0.05, 5.35), expr='proud', kind='kneel', knees=0,
             act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6, smile=0.75), lambda a, s: a.hold_prop('dress_tiny', 1),
                    lambda a, s: a.reach(-9, None, 1, out=30.0, down=200.0, fwd=140.0, shape='grip', up=0.0, fade=0.01))),
           P('narrator', (0.5, 5.6, 2.85), face=(-0.3, 5.2), expr='haunted')],
      acts=lambda A, s, sp: [A['mom'].hand_over(s.t0 - 2.0, -1, A['june'], 'eyes', dur=0.01), A['mom'].look_at(s.t0 - 1.0, (A['june'], 'eyes'), None, 0.3),
                             A['narrator'].look_at(s.t0 - 1.0, (A['mom'], 'eyes'), None, 0.3)] and [],
      c=dict(mv='push', f=1.0, rate=0.025), focus_on='mom')
    # 351-353 J "Four," June whispers. "Five."  June under the hand (lips: J)
    jx, jy, js = 940, 620, 0.95
    C(T(351), 'bust', who='june', bg=('up', 'west', UP_DAWN), set=UPD, cx=jx, cy=jy, scale=js, turn=-0.2, expr='neutral', light=DAWN_L,
      act=lambda a, s: a.eyes_shut(-9, None, 0.0),
      hands=[dict(who='mom', fn=paw_eyes('june', jx, jy, js, side=-1, size=430), size=430, shape='open', side=-1, sleeve_from=lambda tt: (-260, 1000),
                  scratch=True, depth=0.95)],
      c=dict(mv='push', x=940, y=560, zrate=0.02))
    # 354 "If it was going to take one of us, it wasn't going to be her."
    C(T(354), 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=980, cy=610, scale=0.95, turn=0.15, expr='determined', light=DAWN_L,
      act=_A(lookxy(760, 640, -9, None, 0.3, z=300.0), pose(t(354) + 1.2, None, 0.6, brow_angry=0.4)), c=dict(mv='push', x=970, y=560, zrate=0.03),
      music=[(t(354), 'swell', 0.6, 3.5)])
    # 355 "I pull June's face out from under that hand, and I push my own face into it, and I squeeze my eyes shut."
    tpl = w(355, 'pull') - 0.05; tpu = w(355, 'push') - 0.15

    def pull_acts(A, s, sp):
        n, j, m = A['narrator'], A['june'], A['mom']
        m.hand_over(s.t0 - 2.0, -1, j, 'eyes', dur=0.01)
        n.reach_to(tpl, 1, (j, 'shoulder_r'), t1=tpl + 1.0, dur=0.35, contact='palm', shape='grip', z=60.0)
        n.reach_to(tpl + 0.05, -1, (j, 'shoulder_l'), t1=tpl + 1.0, dur=0.35, contact='palm', shape='grip', z=60.0)
        n.head_to(tpl + 1.3, lambda tt: m.where(tt, 'hand_r', post=False), 'eyes', dur=0.6, max_lean=0.25)
        n.look_at(s.t0, (j, 'eyes'), None, 0.3)
        m.look_at(s.t0 - 1.0, (j, 'eyes'), None, 0.3)
        return []
    C(T(355), 'set', room='up', view='west', cam=cm((-1.6, 5.75, 4.0), (-0.3, 5.2, 3.85), S=1350, sx=960, sy=520), set=UPD, rim=DAWN,
      ppl=[P('june', (-0.05, 5.35, 2.85), path=[(tpl + 0.35, (-0.05, 5.35, 2.85)), (tpl + 1.1, (0.55, 5.85, 2.85))], no_walk=True, face=(-0.55, 5.1), expr='terror',
             act=lambda a, s: a.eyes_shut(-9, tpl + 0.5, 0.0)),
           P('mom', (-0.6, 5.05, 2.85), face=(-0.05, 5.35), expr='proud', kind='kneel', knees=0,
             act=_A(lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6, smile=0.75), lambda a, s: a.hold_prop('dress_tiny', 1),
                    lambda a, s: a.reach(-9, None, 1, out=30.0, down=200.0, fwd=140.0, shape='grip', up=0.0, fade=0.01))),
           P('narrator', (0.45, 5.6, 2.85), path=[(tpl - 0.35, (0.45, 5.6, 2.85)), (tpl + 0.1, (0.22, 5.5, 2.85)), (tpl + 0.95, (0.22, 5.5, 2.85)),
                                                  (tpl + 1.55, (-0.02, 5.37, 2.85))], no_walk=True, face=(-0.3, 5.2), expr='determined')],
      acts=pull_acts, c=dict(mv='push', f=1.0, rate=0.02), focus_on='narrator', sfx=[(tpl + 0.3, 'cloth_rustle', -6, 0, 'close')])
    nx, ny, ns = 980, 600, 1.0
    C(tpu, 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=nx, cy=ny, scale=ns, turn=0.1, expr='determined', light=DAWN_L,
      act=_A(lambda a, s: a.eyes_shut(w(355, 'squeeze') + 0.1, None, 0.15), pose(w(355, 'squeeze') + 0.1, None, 0.25, squint=0.8, brow_angry=0.5)),
      hands=[dict(who='mom', fn=paw_eyes('narrator', nx, ny, ns, t_in=tpu + 0.2, side=-1, size=500), size=500, shape='open', side=-1,
                  sleeve_from=lambda tt: (-220, 940), scratch=True, depth=0.95)],
      c=dict(mv='push', x=980, y=560, zrate=0.03))
    # 356 "I've been counting to seven in my head all night."  357 "It's the easiest thing in the world."  358 "Six."  359 "Seven."
    C(T(356), 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=nx, cy=ny + 40, scale=ns * 1.25, turn=0.1, expr='determined', light=DAWN_L,
      act=_A(lambda a, s: a.eyes_shut(-9, None, 0.0), pose(-9, None, 0.1, squint=0.8, brow_angry=0.5)),
      hands=[dict(who='mom', fn=paw_eyes('narrator', nx, ny + 40, ns * 1.25, side=-1, size=620), size=620, shape='open', side=-1,
                  sleeve_from=lambda tt: (-260, 1000), scratch=True, depth=0.95)],
      c=dict(mv='push', x=980, y=560, zrate=0.02))
    # "It's the easiest thing in the world.": the narrator's own face, eyes squeezed shut under Mom's scratched hand,
    # from the other side (3/4, her wrist and forearm across the frame): who is under the hand is never in doubt
    C(T(357), 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=1010, cy=ny + 60, scale=ns * 1.35, turn=-0.3, h_turn=-0.05,
      expr='determined', light=DAWN_L,
      act=_A(lambda a, s: a.eyes_shut(-9, None, 0.0), pose(-9, None, 0.1, squint=0.9, brow_angry=0.55, h_nod=0.08)),
      hands=[dict(who='mom', fn=paw_eyes('narrator', 1010, ny + 60, ns * 1.35, side=-1, size=680), size=680, shape='open', side=-1,
                  sleeve_from=lambda tt: (-320, 1150), scratch=True, depth=0.95)],
      c=dict(mv='push', x=990, y=560, zrate=0.012))
    C(T(358), 'bust', who='narrator', bg=('up', 'west', UP_DAWN), set=UPD, cx=nx, cy=ny + 80, scale=ns * 1.5, turn=0.1, expr='determined', light=DAWN_L,
      act=_A(lambda a, s: a.eyes_shut(-9, None, 0.0), pose(-9, None, 0.1, squint=1.0, brow_angry=0.6)),
      hands=[dict(who='mom', fn=paw_eyes('narrator', nx, ny + 80, ns * 1.5, side=-1, size=740), size=740, shape='open', side=-1,
                  sleeve_from=lambda tt: (-300, 1080), scratch=True, depth=0.95)],
      c=dict(mv='push', x=980, y=540, zrate=0.03), music=[(t(358), 'heartbeat', 0.7, 1.6)])
    C(T(359), 'black', cut='white', quiet_cut=True, caption=True, sfx=[(t(359) + 0.05, 'impact_hit', 0, 0, None, dict(size=1.2))],
      music=[(t(359) + 0.05, 'sub_drop', 0.9), (t(359) + 0.1, 'silence', 0.0, 1.2)])


# ==================================================================================================== AFTER: THE HOSPITAL (914.3 - 993.9)
LOW_UP = cm((-0.75, 5.1, 3.95), (0.35, 5.5, 4.25), S=1100, sx=960, sy=520)       # from Mom's eyes on her knees, up at the narrator's body
SCREAM = lambda k=1.0: _A(ex('terror', -9, None, 0.05), pose(-9, None, 0.08, m_open=1.0 * k, m_round=0.0, wide=1.0, brow_up=0.9, brow_sad=0.6, tremble=0.0, h_nod=-0.15))
SCREAM_CAM = cm((1.25, 5.45, 4.25), (-0.6, 5.1, 3.85), S=1000, sx=960, sy=540)     # past the narrator's body and June, at Mom on her knees


def plan_after(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    UPD = dict(wrecked=1.0, tod='dawn')
    MOMK = lambda a, s: a.set(-9, None, 0.01, scratch=1.0, mess=0.6)
    NEW = lambda: P('narrator_new', (0.35, 5.5, 2.85), face=(-0.6, 5.05), expr='wrong_smile',
                    act=_A(pose(-9, None, 0.1, h_nod=0.25), lookxy(760, 820, -9, None, 0.3, z=300.0)))
    JUNE_H = lambda: P('june', (0.6, 5.15, 2.85), face=(-0.6, 5.05), expr='neutral', act=lookxy(760, 820, -9, None, 0.3, z=300.0))
    hand_in_hand = lambda A, s, sp: [A['narrator_new'].hold_hand(s.t0 - 1.0, -1, A['june'], 1, dur=0.01)] and []
    # 360 "When I open my eyes, I'm on my knees in the hallway, my arms are scratched to ribbons, and I'm looking at myself."
    top = w(360, 'open') + 0.15
    C(T(360), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=620, scale=1.0, expr='terror', light=DAWN,
      act=_A(MOMK, lambda a, s: a.eyes_shut(-9, top, 0.0), lookxy(1100, 300, top, None, 0.25, z=300.0)), c=dict(mv='push', x=960, y=580, zrate=0.03),
      sfx=[(top, 'breath', -4, 0, 'close', dict(kind='gasp'))], music=[(top, 'stinger', 0.5)])
    tar = w(360, 'arms') - 0.15

    def arms_acts(A, s, sp):
        m = A['mom']
        m.reach(-9, None, 1, out=40.0, down=150.0, fwd=210.0, shape='open', up=0.0, fade=0.01)
        m.reach(-9, None, -1, out=40.0, down=150.0, fwd=210.0, shape='open', up=0.0, fade=0.01)
        m.look_at(-9, lambda tt: m.where(tt, 'hand_r', post=False), None, 0.01)
        return []
    C(tar, 'set', room='up', view='west', cam=cm((0.5, 4.75, 4.05), (-0.6, 5.05, 3.7), S=950, sx=960, sy=560), set=UPD, rim=DAWN,
      ppl=[P('mom', (-0.6, 5.05, 2.85), face=(0.35, 5.5), expr='terror', kind='kneel', knees=0, act=_A(MOMK, pose(-9, None, 0.1, h_nod=0.5)))],
      acts=arms_acts, c=dict(mv='push', f=1.0, rate=0.02))
    C(w(360, 'looking') - 0.2, 'set', room='up', view='west', cam=LOW_UP, set=UPD, rim=DAWN_L, ppl=[NEW(), JUNE_H()], acts=hand_in_hand,
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='narrator_new')
    # 361 "Sixteen years old."  362 "Holding June's hand."  363 "Smiling."  364 "My own face looks down at me."  365 "And it hums."
    C(T(361), 'set', room='up', view='west', cam=cm((-0.6, 5.15, 3.9), (0.35, 5.5, 4.35), S=1500, sx=960, sy=560), set=UPD, rim=DAWN_L, ppl=[NEW(), JUNE_H()],
      acts=hand_in_hand, c=dict(mv='push', f=1.0, rate=0.02), focus_on='narrator_new')
    C(T(362), 'set', room='up', view='west', cam=cm((-0.5, 5.2, 3.75), (0.5, 5.35, 3.75), S=1300, sx=960, sy=520), set=UPD, rim=DAWN_L, ppl=[NEW(), JUNE_H()],
      acts=hand_in_hand, c=dict(mv='push', f=1.0, rate=0.02))
    C(T(363), 'bust', who='narrator_new', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=600, scale=0.95, expr='wrong_smile', light=DAWN_L,
      act=_A(pose(-9, None, 0.1, h_nod=0.2), pose(t(363), None, 0.6, smile=0.9), lookxy(860, 860, -9, None, 0.3, z=300.0)), c=dict(mv='push', x=960, y=560, zrate=0.02))
    C(T(364), 'bust', who='narrator_new', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=560, scale=1.1, expr='wrong_smile', light=DAWN_L,
      act=_A(pose(-9, None, 0.1, h_nod=0.4, smile=0.8), lookxy(960, 980, -9, None, 0.3, z=250.0)), c=dict(mv='push', x=960, y=540, zrate=0.025))
    C(T(365), 'bust', who='narrator_new', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=600, scale=1.25, expr='wrong_smile', light=DAWN_L,
      act=_A(pose(-9, None, 0.1, h_nod=0.35), hum(t(365) - 0.1, None), lookxy(960, 980, -9, None, 0.3, z=250.0)), c=dict(mv='push', x=960, y=560, zrate=0.02),
      sfx=[(t(365), 'hum', -8, 0, 'close', dict(who='narrator_new', dur=2.2))], music=[(t(365), 'jingle', 0.5, 2.2, dict(version='hum'))])
    # 366 "So I did the only thing I could."  367 "I screamed."  368 "I screamed that I was sixteen."  369 "I screamed my own name."
    C(T(366), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=620, scale=1.0, expr='terror', light=DAWN,
      act=_A(MOMK, lookxy(1100, 300, -9, None, 0.3, z=300.0)), c=dict(mv='push', x=960, y=580, zrate=0.02))
    C(T(367), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=640, scale=1.1, expr='terror', light=DAWN,
      act=_A(MOMK, SCREAM(1.0), lookxy(1100, 300, -9, None, 0.3, z=300.0)), c=dict(mv='push', x=960, y=600, zrate=0.04, shake=0.6),
      music=[(t(367), 'braam', 0.8)])
    C(T(368), 'bust', who='mom', bg=('up', 'west', UP_DAWN), set=UPD, cx=960, cy=680, scale=1.35, expr='terror', light=DAWN,
      act=_A(MOMK, SCREAM(0.9), lookxy(1100, 300, -9, None, 0.3, z=300.0)), c=dict(mv='push', x=960, y=620, zrate=0.03, shake=0.5))
    # (screen-space looks are camera-bound: from behind the two, they look at Mom's eyes on the plan)
    C(T(369), 'set', room='up', view='west', cam=SCREAM_CAM, set=UPD, rim=DAWN,
      ppl=[P('mom', (-0.6, 5.05, 2.85), face=(0.35, 5.5), expr='terror', kind='kneel', knees=0, act=_A(MOMK, SCREAM(0.9))),
           P('narrator_new', (0.35, 5.5, 2.85), face=(-0.6, 5.05), expr='wrong_smile'), P('june', (0.6, 5.15, 2.85), face=(-0.6, 5.05), expr='neutral')],
      acts=lambda A, s, sp: [A['narrator_new'].hold_hand(s.t0 - 1.0, -1, A['june'], 1, dur=0.01),
                             A['narrator_new'].look_at(s.t0 - 1.0, (A['mom'], 'eyes'), None, 0.3), A['june'].look_at(s.t0 - 1.0, (A['mom'], 'eyes'), None, 0.3),
                             A['mom'].look_at(s.t0 - 1.0, (A['narrator_new'], 'eyes'), None, 0.3)] and [],
      c=dict(mv='push', f=1.0, rate=0.015), focus_on='mom')
    # 370 "When the police came, they found a dead man in a bunny suit who'd been missing since 1987, and a mother who had
    # fought him off to save her children, and then lost her mind."
    C(T(370), 'set', room='front', view='house', set=dict(tod='dawn', police=dict(mode='sweep', strength=0.55)), c=dict(mv='push', f=1.15, rate=0.02))
    C(w(370, 'dead') - 0.15, 'set', room='hall', view='bottom', cam=cm((-1.0, 2.9, 1.5), (0.2, 0.4, 0.7), S=850, sx=960, sy=600), set=dict(tod='dawn', hall=0.0, door=60.0),
      rim=POLICE, ppl=[P('bunny', 'stairs_bottom_body', kind='lie', lie_face='up', arms='out', act=_A(pose(-9, None, 0.01, unmask=0.6), lambda a, s: a.dead(-9, 0.01))),
                       P('cop', (-0.3, 0.12, 0.0), path=[(w(370, 'dead') - 0.1, (-0.3, 0.12, 0.0)), (w(370, 'dead') + 1.3, (0.0, 0.42, 0.0))], face=(0.5, 0.45),
                         expr='sad', act=_A(lookp((0.55, 0.45, 0.2), -9, None, 0.3),
                                            lambda a, s: a.crouch(w(370, 'dead') + 1.5, 0.9, None, 0.8),
                                            lambda a, s: a.head_down(w(370, 'since') - 0.2, None, 0.35, 0.8)))],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='cop', sfx=[(w(370, 'dead') - 0.1, 'police_radio', -16, 0.4, 'inside', dict(dur=3.0))])
    C(w(370, 'mother') - 0.25, 'bust', who='mom', bg=('front', 'house'), set=dict(tod='dawn', police=dict(mode='sweep', strength=0.55)), cx=960, cy=620, scale=0.95,
      expr='dead_stare', light=POLICE, act=_A(MOMK, pose(-9, None, 0.1, still=0.9, h_nod=0.2), lookxy(1150, 700, -9, None, 0.3, z=300.0)),
      c=dict(mv='push', x=960, y=580, zrate=0.02))
    # 371 "That's where I am now."  372 "Holloway State Hospital."  373 "The doctors are very kind."  374 "They call me Laurie."
    C(T(371), 'set', room='hosp', view='room', rim=HOSP,
      ppl=[P('mom_hosp', 'window', expr='haunted', act=pose(-9, None, 0.1, h_nod=0.12))], c=dict(mv='push', f=1.1, rate=0.015))
    C(T(372), 'set', room='hosp', view='corridor', rim=HOSP, c=dict(mv='push', f=1.0, rate=0.02),
      tags=[(t(372) + 0.1, 'HOLLOWAY STATE HOSPITAL', 960, 760, 'white', 2.6)])
    C(T(373), 'set', room='hosp', view='room', rim=HOSP, cam=cm((10.9, 6.5, 1.5), (9.45, 2.75, 1.35), S=950, sx=960, sy=520),
      ppl=[P('doctor', 'door', face=(10.3, 5.0), expr='warm_smile', act=_A(lambda a, s: a.hold_prop('clipboard', -1),
                                                          lambda a, s: a.reach(-1.0, None, -1, out=10.0, down=160.0, fwd=190.0, shape='grip', up=0.0, fade=0.01),
                                                          lambda a, s: a.head_down(t(373) + 0.4, t(373) + 1.0, 0.35, 0.4)))],
      c=dict(mv='push', f=1.15, rate=0.015))
    C(T(374), 'ins', name='wristband', c=dict(mv='push', rate=0.03))
    # 375 "They say I'm forty-three, and that the trauma made me believe I'm my own child."
    C(T(375), 'bust', who='doctor', bg=('hosp', 'room'), expr='warm_smile', cx=1000, cy=600, scale=0.8, turn=-0.25, light=HOSP,
      act=_A(lambda a, s: a.hold_prop('clipboard', -1), lambda a, s: a.reach(-1.0, None, -1, out=10.0, down=60.0, fwd=210.0, shape='grip', up=0.0, fade=0.01),
             lambda a, s: a.head_down(t(375) + 0.5, t(375) + 0.9, 0.3, 0.3)))
    C(w(375, 'and') - 0.1, 'bust', who='mom_hosp', bg=('hosp', 'room'), cx=940, cy=610, scale=0.95, turn=0.15, expr='haunted', light=HOSP,
      act=lookxy(1200, 560, -9, None, 0.3, z=400.0), c=dict(mv='push', x=950, y=560, zrate=0.02))
    # 376 "Every Sunday, June visits."  377 "She comes with my old body, which is doing great."
    C(T(376), 'set', room='hosp', view='visit', cam=cm((20.5, 8.0, 1.6), (15.4, 3.4, 1.2), S=1000, sx=960, sy=540), rim=HOSP,
      ppl=[P('june', (15.1, 2.9, 0.0), path=[(T(376) + 0.2, (15.1, 2.9, 0.0)), (T(377), (16.0, 4.1, 0.0))], expr='neutral'),
           P('narrator_neat', (15.5, 2.75, 0.0), path=[(T(376) + 0.3, (15.5, 2.75, 0.0)), (T(377) + 0.2, (16.5, 3.9, 0.0))], expr='too_still')],
      acts=lambda A, s, sp: [A['narrator_neat'].hold_hand(s.t0 - 1.0, -1, A['june'], 1, dur=0.01)] and [],
      c=dict(mv='push', f=1.1, rate=0.015))
    C(T(377), 'set', room='hosp', view='visit', cam=cm((18.2, 5.9, 1.5), (16.4, 3.95, 1.45), S=1200, sx=960, sy=520), rim=HOSP,
      ppl=[P('narrator_neat', (16.5, 3.9, 0.0), face=(18.2, 5.9), expr='too_still', act=pose(-9, None, 0.1, still=0.7, smile=0.3)),
           P('june', (16.0, 4.1, 0.0), face=(18.2, 5.9), expr='neutral')],
      acts=lambda A, s, sp: [A['narrator_neat'].hold_hand(s.t0 - 1.0, -1, A['june'], 1, dur=0.01)] and [],
      c=dict(mv='push', f=1.0, rate=0.02), focus_on='narrator_neat')
    # 378 "Straight A's."  379 "Never late."  380 "Hums all the time."
    C(T(378), 'ins', name='report', anim=True, c=dict(mv='push', rate=0.035))
    C(T(379), 'bust', who='narrator_neat', bg=('hosp', 'visit'), cx=960, cy=600, scale=0.92, expr='too_still', light=HOSP,
      act=_A(pose(-9, None, 0.1, still=0.8, smile=0.35), lookxy(960, 560, -9, None, 0.3, z=600.0)), c=dict(mv='push', x=960, y=560, zrate=0.02))
    C(T(380), 'bust', who='narrator_neat', bg=('hosp', 'visit'), cx=980, cy=620, scale=1.05, turn=-0.2, expr='too_still', light=HOSP,
      act=_A(hum(t(380) - 0.1, None), lookxy(700, 560, -9, None, 0.3, z=600.0)), c=dict(mv='push', x=970, y=580, zrate=0.02),
      sfx=[(t(380), 'hum', -8, 0, 'hospital', dict(who='narrator_neat', dur=1.6))], music=[(t(380), 'jingle', 0.45, 1.8, dict(version='hum'))])
    # 381 "Last Sunday, June climbed into my lap, put her mouth against my ear, and whispered,"  382 J "I know it's you."
    # a close two-shot: June on her lap, leaning in to her ear (June's bust lower and in front, turned to her)
    def lap(t_lean, k=1.0):
        return [dict(who='june', cx=780, cy=700, scale=0.82 * k, turn=0.55, expr='neutral', light=HOSP, depth=0.98,
                     act=_A(pose(t_lean, None, 0.6, h_tilt=8.0, h_nod=0.1, approach=0.25), lookxy(1200, 560, -9, None, 0.3, z=200.0)))]
    C(T(381), 'bust', who='mom_hosp', bg=('hosp', 'table'), cx=1150, cy=600, scale=0.9, turn=-0.3, expr='haunted', light=HOSP,
      act=lookxy(1500, 560, -9, None, 0.3, z=400.0), busts=lap(w(381, 'put')), c=dict(mv='push', x=1000, y=580, zrate=0.02))
    C(T(382), 'bust', who='mom_hosp', bg=('hosp', 'table'), cx=1180, cy=620, scale=1.0, turn=-0.3, expr='haunted', light=HOSP,
      act=_A(lookxy(1500, 560, -9, None, 0.3, z=400.0), pose(t(382) + 0.4, None, 0.5, wide=0.6)), busts=lap(-9, 1.12), c=dict(mv='push', x=1000, y=600, zrate=0.02))
    # 383 "Then she told me what my old body asked her in the car, on the way over."  384 X "Want to see a magic trick?"
    C(T(383), 'bust', who='mom_hosp', bg=('hosp', 'table'), cx=960, cy=620, scale=1.05, expr='haunted', light=HOSP,
      act=_A(pose(t(383) + 1.5, None, 1.2, wide=0.7, brow_up=0.6), lookxy(960, 560, -9, None, 0.3, z=600.0)), c=dict(mv='push', x=960, y=580, zrate=0.025))
    C(T(384), 'bust', who='narrator_neat', bg=('hosp', 'visit'), cx=960, cy=620, scale=1.15, expr='too_still', light=HOSP, talk_k=0.35,
      act=_A(pose(-9, None, 0.1, still=0.85, smile=0.45), lookxy(960, 540, -9, None, 0.3, z=600.0)), c=dict(mv='push', x=960, y=580, zrate=0.03),
      music=[(t(384), 'stinger', 0.7)])
    # 385 "Easter is in nine days."
    C(T(385), 'ins', name='calendar', c=dict(mv='keys', keys=[(T(385), 960, 540, 1.0, None, 1.0), (T(386) - 0.1, 760, 960, 1.0, 'in_out', 1.9)]),
      music=[(e(385) + 0.2, 'sub_drop', 0.6)])


# ==================================================================================================== OUTRO (993.9 - end)
MOM_DOOR_BG = ('june', 'door', cm((0.95, 7.6, 4.2), (0.8, 5.6, 4.1), S=900))


def _vhs_fn(k=0.55):
    return lambda tt: {'vhs': dict(t=tt, k=k, curve=0.0, track=0.25, bezel=0.0, glass=0.0, scan=0.45, tube=False, noise=0.6)}


def plan_outro(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    O = dict(era='outro')
    # 386 "Okay."  387 "Breathe."  black, a breath
    C(T(386) - 0.4, 'black', caption=True, sfx=[(t(387) + 0.1, 'breath', -12, 0, 'close', dict(kind='calm_exhale'))], music=[(T(386) - 0.4, 'silence', 0.0, 2.0)])
    # 388 "You can turn a light on now."  the switch flips ON; the frame floods warm
    ton = w(388, 'on') - 0.05
    C(T(388), 'ins', name='switch', **O, kw=lambda tr, a=ton - T(388): dict(flip=lambda tt: ease_in_out(clamp((tt - a) / 0.15))),
      post_fn=lambda tt, a=ton: dict(exposure=0.22 * ease_in_out(clamp((tt - a) / 0.5))), c=dict(mv='push', rate=0.02),
      sfx=[(ton, 'light_switch', -2, 0, 'close')], music=[(ton + 0.1, 'outro_warm', 0.4, 30.0)])
    # 389 "None of this happened."  the living room, every lamp on, empty and warm
    C(T(389), 'set', room='living', view='wide', set=dict(lamp=1.0, chair_lamp=1.0, curtains=0.0), **O, rim=LAMP, c=dict(mv='push', f=1.0, rate=0.012))
    # 390 "There's no Holloway."  391 "No Pemberton's."  (struck through in red marker)
    C(T(390), 'ins', name='courier', **O, strike=(w(390, 'holloway') + 0.1, 690, 70, 1120, 40),
      c=dict(mv='keys', keys=[(T(390), 960, 190, 1.0, None, 1.7), (T(391), 960, 190, 1.0, 'lin', 1.75)]), sfx=[(w(390, 'holloway') + 0.1, 'marker_strike', -4, 0, 'close')])
    C(T(391), 'ins', name='egg', **O, strike=(w(391, 'pemberton') + 0.05, 985, 465, 1150, 640),
      c=dict(mv='keys', keys=[(T(391), 1060, 540, 1.0, None, 1.5), (T(392), 1060, 540, 1.0, 'lin', 1.55)]), sfx=[(w(391, 'pemberton') + 0.05, 'marker_strike', -4, 0, 'close')])
    # 392 "No bridge at the end of Orchard Road."  just a bridge, in daylight
    C(T(392), 'set', room='woods', view='bridge', set=dict(tod='day87'), **O, rim=MEMORY, grade='ob_ext', c=dict(mv='push', f=1.1, rate=0.015),
      sfx=[(T(392), 'birds_day', -12, 0, 'woods', dict(dur=2.5))])
    # 393 "Laurie, June and the little girl in the suit were made up by someone drinking a very ordinary cup of coffee."
    # the notebook with the story's notes ('made up by someone'), then a cut to the very ordinary cup of coffee
    tdr = w(393, 'drinking') - 0.15
    C(T(393), 'ins', name='desk', **O, c=dict(mv='keys', keys=[(T(393), 820, 600, 1.0, None, 1.15), (tdr, 840, 600, 1.0, 'push', 1.2)]))
    C(tdr, 'ins', name='desk', **O, c=dict(mv='keys', keys=[(tdr, 1240, 520, 1.0, None, 1.35), (T(394), 1240, 520, 1.0, 'push', 1.42)]),
      sfx=[(w(393, 'cup') - 0.2, 'mug_set_down', -8, 0, 'close')])
    # 394 "The Bunnyman is just a costume."  395 "It has a zipper in the back, where zippers go."
    C(T(394), 'ins', name='hanger', **O, c=dict(mv='push', rate=0.02))
    C(T(395), 'ins', name='hanger', **O, kw=dict(back=True, zip_t=w(395, 'zipper') - T(395)), anim=True,
      c=dict(mv='keys', keys=[(T(395), 960, 540, 1.0, None, 1.0), (T(396), 960, 600, 1.0, 'in_out', 1.3)]), sfx=[(w(395, 'zipper'), 'zipper', -4, 0, 'close')])
    # 396 "...the trick only works if you close your eyes and count to seven."  397 "You've been watching this whole time."  398 "So you never did."
    C(T(396), 'card', mode='trick', steps=[(w(396, 'close') - 0.05, '1. CLOSE YOUR EYES'), (w(396, 'count') - 0.05, '2. COUNT TO SEVEN')], **O)
    C(T(397), 'card', mode='eye', **O)
    C(T(398), 'card', mode='safe', **O)
    # 399 "Now, go back to the comment you left before rule two."  the tape rewinds to the pause
    src_mom = T(92) - 0.06; src_bun = T(74) + 1.9
    C(T(399), 'pause', mode='rew', srcs=[T(357) + 0.3, T(267) + 0.3, T(169) + 1.0, T(119) + 0.5, T(104) + 0.5, src_mom],
      per=max(0.3, (T(400) - T(399)) / 6.0), era='pause')
    # 400 "If you said the Bunnyman, you're the only one who would have let Laurie come home."
    C(T(400), 'pause', mode='split', srcs=(src_mom, src_bun), hl='R', era='pause')
    # 401-403 "Find someone who said Mom, and reply to them. Gently. They're going to need it."
    C(T(401), 'pause', mode='split', srcs=(src_mom, src_bun), hl='L', reply=w(401, 'reply') - 0.1, reply_side=-1, era='pause')
    # 404 "And if you said Mom... don't worry."  405 "She liked you too."  (the frozen frame, then it plays: the smile widens, the eyes come to us)
    C(T(404), 'pause', mode='freeze', src=src_mom, era='pause')
    C(T(405), 'bust', who='mom', bg=MOM_DOOR_BG, set=dict(hall=1.0), cx=960, cy=640, scale=1.08, expr='too_still', era='pause',
      light=dict(rim='#ffcf8f', rim_a=90, side=-1, key=-0.25), post_fn=_vhs_fn(),
      act=_A(pose(-9, None, 0.1, smile=0.6), pose(t(405) + 0.2, None, 0.8, smile=0.95), lookxy(700, 560, -9, t(405) + 0.3, 0.3, z=600.0),
             lookxy(960, 520, t(405) + 0.35, None, 0.5, z=600.0)),
      c=dict(mv='push', x=960, y=600, zrate=0.03), music=[(t(405) + 0.3, 'stinger', 0.45)])
    # 406 "If this story made you glance at a window, even once, leave a like, so I know the trick worked."
    C(T(406), 'set', room='living', view='window', set=dict(lamp=0.0, curtains=1.0), rim=NIGHT, **O, c=dict(mv='push', f=1.0, rate=0.02))
    # the LIKE lands like a knock in the comma after "like," (the final mix: on "like" itself the knock sat 5.3 LU over
    # the word's end), so the icon slams in with the knock, just before "so I know the trick worked"
    C(w(406, 'leave') - 0.1, 'card', mode='like', hit_t=w(406, 'so') - 0.17, **O)
    # 407 "And subscribe."  Grandma's porch light switches on
    C(T(407), 'set', room='yard', view='house', set=dict(back_light=dict(on=t(407) + 0.35), kitchen=0.0), **O, rim=MOON, c=dict(mv='push', f=1.6, rate=0.015),
      sfx=[(t(407) + 0.35, 'light_switch', -6, 0, 'outside', dict(kind='porch'))])
    # 408 "...the next story comes to you, so you never have to go looking for it in the woods."
    C(T(408), 'set', room='yard', view='woods', set=dict(back_light=1.0), **O, rim=PORCH, c=dict(mv='push', f=1.0, rate=0.012))
    C(w(408, 'next') - 0.1, 'set', room='yard', view='house', set=dict(back_light=1.0, kitchen=0.6), **O, rim=MOON, c=dict(mv='push', f=2.2, rate=0.012))
    # 409 "Next time... if your doctor calls at three in the morning ..."  (the card: NEXT TIME ON NIGHT POLICY)
    C(T(409), 'card', mode='next', **O, sfx=[(w(409, 'doctor') + 0.3, 'phone_ring', -6, 0, 'close', dict(kind='old_nightstand', dur=3.0))])
    # 410 "Sleep well."  411 "And if you hear a little song tonight... that's just the outro."
    C(T(410), 'card', mode='title', **O)
    C(T(411), 'black', caption=True, **O)
    # the song IS the outro (the sound step's jingle 'outro' from e(411) + 0.1, 9.75 s, its last phrase a soft hum): the
    # channel's end card holds for it and fades out with the film
    C(e(411) + 0.35, 'card', mode='title', **O, music=[(e(411) + 0.1, 'jingle', 0.6, 9.75, dict(version='outro', stop='fade'))])


# ==================================================================================================== global music + extra beds
def plan_globals(F):
    """Music events that run across cuts (the Pemberton's jingle by version, the climax heartbeat / pulse, swells) and the
    beds the reveal and the aftermath need (the 1987 woods, the night woods, police, the hospital)."""
    t, e, w = F.t, F.e, F.w
    G = F.globals
    m = lambda tt, typ, lv, **k: G.append(dict({'t': round(tt, 3), 'type': typ, 'level': lv}, **k))
    # the jingle: the 1987 parade on the tape, the hums, the tinny one from the woods, the broken girl's version, the outro
    # (the parade tape is cued by its shot; the tinny one from the woods is a bed in beds())
    m(t(255) - 0.2, 'jingle', 0.3, len=round(t(258) - t(255) + 0.4, 2), version='girl_broken')
    # the climax: the pulse from Mom's hand over June's eyes, the heartbeat under the counts, stopped dead at "Seven."
    m(t(313), 'pulse_on', 0.5)
    m(t(318) - 0.05, 'heartbeat', 0.45, len=round(t(359) - t(318) + 0.1, 2), bpm0=72, bpm1=138)
    m(t(359) + 0.05, 'pulse_off', 0.0)
    m(t(323), 'swell', 0.4, len=8.0)
    m(t(350), 'riser', 0.6, len=round(t(351) - t(350), 2))
    m(t(355), 'riser', 0.75, len=round(t(358) - t(355), 2))
    m(t(370), 'swell', 0.35, len=10.0, kind='sorrow')
    m(t(386) - 0.4, 'silence', 0.0, len=2.0)
    # the count: one soft heartbeat thump under each number June (and the narrator) says, the last one cut off by the swap
    for k, i in enumerate((318, 320, 321, 351, 353, 358, 359)):
        G.append(_ev(t(i) - 0.02, 'count_thump', -8 + 0.8 * k, 0, 'close', n=k + 1, of=7, word=F.L[i]['en'].strip(' ,.')))
    # the trick itself: 1987 (the flash on "opens them") and now (the white flash on "Seven.")
    G.append(_ev(F.w(326, 'opens') - 0.05, 'swap', -4, 0, None, kind='1987'))
    G.append(_ev(t(359) + 0.05, 'swap', 0, 0, None, kind='now'))
    # beds the shots need on top of beds(): woods (1987 day / night), the police morning, the hospital
    G.append(_ev(t(324) - 0.1, 'ambience_woods', -10, 0, 'woods', dur=round(t(329) - t(324), 2), tod='day', birds=0.4))
    G.append(_ev(t(333) - 0.1, 'ambience_woods', -10, 0, 'woods', dur=round(t(334) - t(333), 2), tod='day', birds=0.3, creek=0.6))
    G.append(_ev(t(334) - 0.1, 'ambience_woods', -10, 0, 'woods', dur=round(t(337) - t(334), 2), tod='night', creek=0.4))
    G.append(_ev(t(340) - 0.1, 'ambience_woods', -10, 0, 'woods', dur=round(t(342) - t(340), 2), tod='night', creek=0.4))
    G.append(_ev(t(370) - 0.1, 'police_radio', -18, 0.3, 'outside', dur=6.0))


# ==================================================================================================== main
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
