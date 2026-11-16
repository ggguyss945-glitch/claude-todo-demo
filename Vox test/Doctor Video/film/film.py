"""film.py: the shot list, editor and cue sheets for "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND".

Built in the machinery of the Bunnyman film (film_bunny_ref.py), the police film (film_police_ref.py) and the dummy film
(film_dummy_ref.py): the same engine, cast system (characters.py + characters_doctor.py) and set system (sets.py +
sets_doctor.py), the police header / rule cards / captions / tags, a global look with a climax ramp, and cue sheets
derived from the picture. The shot map this list follows line by line is W/shotmap.md (every timeline line -> the
picture that shows it). EVERY time in the plan is keyed to timeline.json (line starts / ends and word times): there is
no absolute time anywhere, so a re-edit of the narration moves the picture with its lines.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + TAIL: the end card holds for the outro)
    F.shots                          # [Shot(t0, t1, kind, p)] hard cuts
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --frames PREFIX | --lipcheck | --bench N [--shots ..]

THE OWNER'S NOTES, MADE INTO CODE:
  * Staging lives on Ruth's house plan (sets_doctor: one plan in metres for the living room, hall, kitchen, bathroom, the
    porch and Larch Street). Every figure in a set shot stands on a plan point (an anchor Spot or (x, y[, Y])): its
    height from the px-per-metre there, its feet on the floor point, its draw order from sp.order_at() (furniture between
    it and the camera is drawn over it), its light from sp.light_kw(). Seats, kneels, floor sits come from the spot's
    kind (nobody stands on furniture, nothing floats). Doctor Later on a seat is perched with his own rig (perch).
  * Mediums and two-shots are real cameras on the same plan (cam=cm(eye, look, S, sx, sy)): a cut keeps every wall,
    door, chair and person where they were. Prefer cuts; camera moves are short pushes while people act.
  * Contact: look_at / reach_to / pick_up / put_down / receiver_to_ear / hand_over / tap / pull_cord / strike_match land
    on their targets; props are PropTracks (resting or held, never both, never teleporting).
  * Lip sync on character lines only (VOICE: G Ruth, H Halverson, K Milo, M Mom, U the ER nurse); narrator lines (N) move
    no mouths; Doctor Later (W) never moves a mouth (a head dip / pen click on his lines); the recording (R) is the phone.
  * escalate(): no "scared jiggle"; tension shows as wider eyes, raised brows and faster breath for the kids, stiller
    stillness for Ruth; Milo's illness is his own expression state per beat (thirsty -> dazed).

Shot kinds (builders B_<kind>):
  set      a set view (sets_doctor dr_* builders) with figures placed on the plan: room 'living' | 'hall' | 'kitchen' |
           'bath' | 'front' | 'clinic' | 'office' | 'car' | 'er' | 'er_bay' | 'er_wait' | 'hosp_hall' | 'cardio' | 'run' |
           'outro'; view = the builder's view; cam = None (the view's own camera) or cm(...); set = builder kwargs
           (state, era, tod, lights, doors, phone, cord, ring, fire, cabinet, card ...); ppl = [P(who, at, ...)];
           acts = f(A, shot, sp) -> [extra layers]; c = camera move (see scam)
  bust     a face close-up (CH.draw_bust) over the blurred set (bg=(room, view[, cam]) + set=dict(..)); busts=[..] more
           faces; hands=[..]; acts; plain=(c1, c2) a plain gradient instead of a set
  ins      a prop insert: sets_doctor dr_insert(name, kw, motion); kw = dict or f(time since the cut) -> dict; hands=[..]
  rule     the police rule card over the yellow typed card from the medicine cabinet (rule n lit)
  pause    the comment prompt as a phone HOLD screen over the frozen last frame (stage 'hold' | 'word' | 'ask' | 'dont')
  card     plain graphic cards (placeholders for the outro: part B builds them)
  black    black (with an optional line of text)
Plan conventions: F.cut(t, kind, **p) starts a shot that ends at the next cut. F.t(i) / F.e(i) line start / end,
F.w(i, 'word') the ASR start of a word inside line i; T(i) = F.t(i) - LEAD (cuts land 0.1 s before the word),
W(i, 'word') = F.w(i, 'word') - LEAD. Common p keys: c=dict(mv='push'|'keys'|'hold', f, rate, x, y, keys=[(t, x, y, z,
ease, f)], hit=[t]), tags=[(t, text, x, y, style, hold)], sfx=[(t, name, gain_db, pan, space, params)], music=[(t, type,
level, len, extra)], cut='white'|'static', era='now'|'1979'|'outro', grade, post, post_fn, focus (or focus_on=who), dof.
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
TAIL = 10.0                      # the end card holds after the last line ("It's probably just your doctor.")
TITLE = "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"
BASE = 'If_Your_Doctor_Calls_At_3_AM'
CHANNEL = 'NIGHT POLICY'           # the channel's name on every card
H._hand = CH.hud_phone_hand
PART_B = 213                       # part A = lines 0..212 (cold open .. rule 5), part B = lines 213..455


# ---------------------------------------------------------------- timing: everything is keyed to timeline.json
# There are no authored absolute times in this film: every table below names timeline LINES (and words), turned into
# seconds by the Film when it is built. at() / authored() stay as identities for the shared machinery.
def set_retime(lines, duration): return None


def at(t): return t


def authored(t): return t


_FILM = [None]                     # the Film being built (the line-keyed tables read their times through it)


def LT(i, off=0.0):
    """Line i's start on the current timeline (+ off)."""
    return _FILM[0].L[i]['t'] + off


# who speaks which timeline lines (code, fx or None): narrator lines (N) move no mouths; Doctor Later (W) never does.
VOICE = {'ruth': [('G', None)], 'ruth_sick': [('G', None)], 'halverson': [('H', None)], 'halverson_rain': [('H', None)],
         'milo': [('K', None)], 'milo_sick': [('K', None)], 'mom_rn': [('M', None)], 'er_nurse': [('U', None)]}
WHISPER = ('whisper',)


# ---------------------------------------------------------------- the story clock (header corner), keyed to lines
def _hm(h, m): return h * 60 + m


CLOCK_KEYS = [(66, _hm(2, 59)), (67, _hm(3, 0)), (92, _hm(3, 2)), (103, _hm(3, 2)), (119, _hm(3, 5)), (120, _hm(3, 15)), (127, _hm(3, 20)),
              (149, _hm(3, 40)), (182, _hm(4, 0)), (195, _hm(4, 10)), (213, _hm(4, 14)), (252, _hm(4, 20)), (303, _hm(4, 28)),
              (348, _hm(4, 47)), (361, _hm(5, 10))]
CORNER = [(0, '3:00 AM'), (15, 'LARCH STREET'), (18, '1979'), (32, 'YEARS LATER'), (40, 'THAT SPRING'), (56, 'THAT NIGHT'), (58, 'SUNDOWN'),
          (65, None), (362, 'NOW'), (365, 'SUNRISE'), (371, 'SUNRISE'), (379, 'NOW'), (383, '3:00 AM'), (401, CHANNEL)]


def clock_str(t):
    F = _FILM[0]
    lab = None
    for i, s in CORNER:
        if t >= F.t(i) - LEAD: lab = (s,)
    if lab and lab[0] is not None: return lab[0]
    if F.t(92) - LEAD <= t < F.t(103) - LEAD: t = F.t(92) - LEAD          # on hold: the clock stops
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
LAMP = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.1)
LAMP_R = dict(rim='#ffcf8f', rim_a=60, side=1, key=0.1)
NIGHT = dict(rim='#8fa6e8', rim_a=70, side=1, key=-0.25)
NIGHT_L = dict(rim='#8fa6e8', rim_a=70, side=-1, key=-0.25)
DARK = dict(rim='#8fa6e8', rim_a=40, side=1, key=-0.45)
PORCH = dict(rim='#ffc888', rim_a=80, side=-1, key=-0.15)
RAIN = dict(rim='#b8c8ec', rim_a=90, side=1, key=-0.2)
HEADL = dict(rim='#fff2d6', rim_a=110, side=-1, key=-0.15)            # Halverson's headlights through the picture window
SUN79 = dict(rim='#ffbe72', rim_a=110, side=-1, key=0.15)
HARVEST = dict(rim='#ffd08a', rim_a=70, side=-1, key=0.05)              # 1979 lamp light
EVE = dict(rim='#ffd6a0', rim_a=60, side=1, key=0.12)                   # the house in the evening, lights on
HOSP = dict(rim='#e8f4f0', rim_a=55, side=1, key=0.14)                  # the doctors' world: bright, warm, safe
OFFICE = dict(rim='#ffe6b8', rim_a=70, side=-1, key=0.02)               # the desk lamp at 3 AM
WAITR = dict(rim='#d8f2a0', rim_a=75, side=1, key=-0.12)                # the villain's fluorescent green-yellow
FIRE = dict(rim='#ff9a48', rim_a=120, side=1, key=-0.05)
DASH = dict(rim='#9fd0ff', rim_a=60, side=1, key=-0.3)                  # inside the car at night


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
        if t >= self.t(401) - LEAD: cur = 'THE END'
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
ROOMS = {'living': 'dr_living', 'hall': 'dr_hall', 'kitchen': 'dr_kitchen', 'bath': 'dr_bath', 'front': 'dr_front', 'clinic': 'dr_clinic',
         'office': 'dr_office', 'er_bay': 'dr_er_bay', 'er_wait': 'dr_er_wait', 'er': 'dr_er_entrance', 'hosp_hall': 'dr_hosp_hall',
         'cardio': 'dr_cardio', 'car': 'dr_car', 'run': 'dr_run', 'outro': 'dr_outro'}
_PRE = {'hall': 'dr_hall_', 'kitchen': 'dr_kit_', 'bath': 'dr_bath_', 'front': 'dr_ext_', 'clinic': 'dr_clinic_', 'office': 'dr_office_',
        'car': 'dr_car_', 'run': 'dr_run_', 'outro': 'dr_outro_'}
_CAMN = {('er_bay', 'bay'): 'dr_er_bay', ('er_bay', 'side'): 'dr_er_bay_side', ('er_bay', 'monitor'): 'dr_er_monitor', ('er_wait', 'wide'): 'dr_er_wait',
         ('er_wait', 'chairs'): 'dr_er_wait_chairs', ('er_wait', 'desk'): 'dr_er_desk', ('er', 'ext'): 'dr_er_ext', ('er', 'doors'): 'dr_er_doors',
         ('hosp_hall', 'hall'): 'dr_hosp_hall', ('hosp_hall', 'chair'): 'dr_hosp_hall_chair', ('cardio', 'side'): 'dr_cardio', ('cardio', 'ruth'): 'dr_cardio_ruth'}


def base_cam(room, view, kw):
    """The CAMS name the builder uses for (room, view, state)."""
    if room == 'living':
        if kw.get('state') == 'wait' and ('dr_wait_' + view) in ST.CAMS: return 'dr_wait_' + view
        return 'dr_liv_' + view
    if room in _PRE: return _PRE[room] + view
    return _CAMN[(room, view)]


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
                CH.draw_torch_beam(pen, lx, ly, ang, L_ * 1.05, torch.get('spread', 12.0), torch.get('a', 0.9), t)
                pw = max(18.0, 0.55 * hh * torch.get('pool', 0.5))
                pen.glow(gx, gy, pw, '#fff1c8', 85 * torch.get('a', 0.9))
                pen.fill(oval(gx, gy, pw * 0.95, pw * 0.16), '#fff4d8', 42 * torch.get('a', 0.9), blur=6)
            else:
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
# brows and breath of the kids (the narrator, Milo); Ruth grows stiller (fewer blinks, a locked jaw) as the night goes on.
KID_ARC = [(0, 0.35), (15, 0.0), (65, 0.15), (67, 0.35), (88, 0.45), (107, 0.5), (127, 0.55), (138, 0.7), (149, 0.6), (187, 0.75),
           (195, 0.8), (213, 0.85), (252, 0.95), (295, 0.6), (306, 0.4), (348, 0.2), (362, 0.0)]
RUTH_ARC = [(0, 0.3), (15, 0.1), (58, 0.25), (67, 0.5), (88, 0.65), (117, 0.7), (167, 0.75), (201, 0.6), (303, 0.0)]


def _arc(arc, t):
    F = _FILM[0]
    return float(np.interp(t, [F.t(i) for i, _ in arc], [b for _, b in arc]))


def escalate(a, sh, who):
    """Kids: wide eyes, raised brows, faster shallow breath with the night's tension. Ruth (until the rescue): stillness.
    1979 / outro shots and rule cards: nothing."""
    if sh.kind in ('rule', 'card', 'black', 'pause') or sh.p.get('era') in ('1979', 'outro'): return
    if who in ('narr14',):
        k = _arc(KID_ARC, sh.t0)
        if k <= 0.02: return

        def fn(P_, t, k=k):
            P_.wide += 0.2 * k; P_.brow_up += 0.12 * k; P_.brow_sad += 0.08 * k
            per = 3.9 - 1.5 * k
            P_.breath = 0.5 + (0.45 + 0.1 * k) * math.sin(2 * math.pi * t / per + a.seed)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)
    elif who in ('ruth', 'ruth_sick'):
        k = _arc(RUTH_ARC, sh.t0)

        def fn(P_, t, k=k):
            P_.lock = max(P_.lock, 0.5 * k)
        a._add(sh.t0 - 1.0, sh.t1 + 1.0, fn, real=True)


# ==================================================================================================== builders: sets
ROOM_RIM = {'living': NIGHT, 'hall': NIGHT, 'kitchen': NIGHT_L, 'bath': NIGHT, 'front': RAIN, 'clinic': HOSP, 'office': OFFICE,
            'er': HOSP, 'er_bay': HOSP, 'er_wait': HOSP, 'hosp_hall': WAITR, 'cardio': HOSP, 'car': DASH, 'run': SUN79, 'outro': LAMP}

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
                                hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand')))
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
    """A prop insert from sets_doctor DR_INSERTS: name, kw = dict | f(time since the cut) -> dict, motion = f(time since
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
    sp = ST.dr_insert(p['name'], kwf, mof, t0=t0, grade=p.get('grade'))
    layers = list(sp)
    if p.get('strike'):
        layers.append(strike_layer(*p['strike']))
    for hd in p.get('hands', []):
        layers.append(hand_layer(hd['who'], hd['fn'], hd['size'], hd.get('shape', 'open'), hd.get('side', 1), hd.get('depth', 0.9),
                                 hd.get('sleeve_from'), hd.get('scratch', False), hd.get('name', 'hand')))
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
# The police rule card (RULE, the numeral, the red line, the rule typed on with its key words in red, the seven dashes)
# over the yellow typed card from the medicine cabinet, rule n lit on it (blurred, dimmed); a small line icon per rule.
RULE_TEXT = {1: "If the doctor calls after midnight, *don't ask what they found.*",
             2: "If they put you on hold, *don't hang up. Ever.*",
             3: "Never say what hurts *out loud* after dark. *He's listening.*",
             4: "If someone in a white coat knocks, *don't open the door.* Real doctors don't make house calls.",
             5: "Nobody goes to the hospital *before sunrise.* It can wait.",
             6: "If you see him sitting in the chair, *take a number,* and wait your turn.",
             7: "Never, ever let him *take your pulse.*"}


def _ic_phone(pen, x, y, s, a):
    pen.line(smooth([(x - s * 0.34, y - s * 0.18), (x - s * 0.2, y - s * 0.34), (x + s * 0.2, y - s * 0.34), (x + s * 0.34, y - s * 0.18)], False, 0.8), 6, '#ffffff', a)
    pen.line(rrect(x - s * 0.24, y - s * 0.08, s * 0.48, s * 0.4, 10), 5, '#ffffff', a)
    pen.line(oval(x, y + s * 0.12, s * 0.09), 4, '#ffffff', a)


def _ic_note(pen, x, y, s, a):
    for dx in (-0.16, 0.18):
        pen.fill(oval(x + dx * s, y + s * 0.26, s * 0.1, s * 0.075), '#ffffff', a)
        pen.line(poly([(x + dx * s + s * 0.09, y + s * 0.24), (x + dx * s + s * 0.09, y - s * 0.26)], False), 4, '#ffffff', a)
    pen.line(poly([(x - s * 0.07, y - s * 0.26), (x + s * 0.27, y - s * 0.32)], False), 7, '#ffffff', a)


def _ic_ear(pen, x, y, s, a):
    pen.line(smooth([(x - s * 0.1, y + s * 0.3), (x - s * 0.22, y), (x - s * 0.12, y - s * 0.3), (x + s * 0.12, y - s * 0.32), (x + s * 0.22, y - s * 0.08),
                     (x + s * 0.04, y + s * 0.12), (x + s * 0.02, y + s * 0.3)], False, 0.8), 5, '#ffffff', a)


def _ic_door(pen, x, y, s, a):
    pen.line(rrect(x - s * 0.22, y - s * 0.38, s * 0.44, s * 0.76, 6), 5, '#ffffff', a)
    pen.fill(oval(x + s * 0.12, y + s * 0.02, 5), '#ffffff', a)
    pen.line(oval(x, y - s * 0.18, s * 0.05), 3, '#ffffff', a)


def _ic_sun(pen, x, y, s, a):
    pen.line(poly([(x - s * 0.4, y + s * 0.18), (x + s * 0.4, y + s * 0.18)], False), 4, '#ffffff', a)
    pen.line(smooth([(x - s * 0.2, y + s * 0.18), (x - s * 0.14, y - s * 0.02), (x, y - s * 0.08), (x + s * 0.14, y - s * 0.02), (x + s * 0.2, y + s * 0.18)], False, 0.8), 5, '#ffffff', a)
    for k in range(5):
        ang = math.radians(-160 + k * 35)
        pen.line(poly([(x + math.cos(ang) * s * 0.28, y + s * 0.1 + math.sin(ang) * s * 0.28), (x + math.cos(ang) * s * 0.38, y + s * 0.1 + math.sin(ang) * s * 0.38)], False), 4, '#ffffff', a)


def _ic_ticket(pen, x, y, s, a):
    pen.line(rrect(x - s * 0.3, y - s * 0.18, s * 0.6, s * 0.36, 6), 5, '#ffffff', a)
    pen.line(poly([(x - s * 0.08, y - s * 0.18), (x - s * 0.08, y + s * 0.18)], False), 2, '#ffffff', a * 0.7)
    text(pen.cv, '79', x + s * 0.1, y + s * 0.08, 200, s * 0.2, '#ffffff', a, 0.0, 'center')


def _ic_pulse(pen, x, y, s, a):
    pts = [(x - s * 0.4, y), (x - s * 0.15, y), (x - s * 0.08, y - s * 0.28), (x + s * 0.02, y + s * 0.26), (x + s * 0.1, y), (x + s * 0.4, y)]
    pen.line(poly(pts, False), 5, '#ffffff', a)


RULE_ICON = {1: _ic_phone, 2: _ic_note, 3: _ic_ear, 4: _ic_door, 5: _ic_sun, 6: _ic_ticket, 7: _ic_pulse}


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
    """The police rule card over the yellow card in the medicine cabinet (blurred, dimmed; rule n lit on the card); the
    sentence being read is marked on the card as it is read."""
    p = sh.p
    n = p['n']
    sp = ST.dr_insert('card', dict(hl=n, show=7))
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
        H.rule_card(cv, n, RULE_TEXT[n], tt_, icon=RULE_ICON.get(n), scrim=0.35)
    cam = scam(sh, None, dict(mv='push', rate=0.012, free=True))

    def fx(t):
        d = dict(blur=6, dim=0.45)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(list(sp), cam, None, 'dr_ins', 1.0, 0.0, fx=fx, hud=hud)


# ==================================================================================================== the comment prompt: a call on hold
def _img_layer(F, key_fn, name='freeze', depth=1.0, xform=None):
    """Draws a pre-rendered frame (F.freeze(t_src)) filling the design frame; xform(t) -> (dx, dy, scale)."""
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


def _comment_cue(cv, t, alpha=1.0, y1=820, typed=''):
    """A plain comment box (no platform branding): a speech-bubble icon, 'Add a comment...' (or the typed word) and a
    blinking cursor."""
    if t < 0: return
    pen = Pen(cv)
    u = ease_out_back(clamp(t / 0.45), 1.6)
    y = lerp(1180, y1, u)
    a = 255 * alpha * clamp(t / 0.2)
    box = rrect(560, y - 52, 800, 104, 52)
    pen.fill(moved(box, 0, 10), '#000000', 0.45 * a, blur=14)
    pen.fill(box, '#f4f4f2', a); pen.line(box, 3, '#d0d0d4', a)
    bub = rrect(600, y - 26, 62, 44, 12)
    pen.fill(bub, '#c0161c', a); pen.fill(poly([(612, y + 16), (604, y + 34), (630, y + 16)]), '#c0161c', a)
    for k in range(3): pen.fill(oval(616 + k * 15, y - 4, 4.5), '#ffffff', a)
    if typed:
        w_ = text(cv, typed, 690, y + 12, 600, 38, '#16171c', a, 0.04, 'left', 0.7)
        cx = 696 + w_
    else:
        text(cv, 'Add a comment...', 690, y + 12, 600, 34, '#5a5a62', a, 0.0, 'left')
        cx = 1000
    if (t * 1.6) % 1.0 < 0.55:
        pen.fill(rect(cx, y - 22, 4, 44), '#16171c', a)


def _hold_key(pen, cv, x, y, label, t, lit=0.0, press=0.0, a=255):
    """One big phone key (ASK / DON'T)."""
    s = 1.0 - 0.06 * press
    w, h = 300 * s, 132 * s
    r = rrect(x - w / 2, y - h / 2 + 6 * press, w, h, 30)
    pen.fill(moved(r, 0, 10), '#000000', 0.5 * a, blur=12)
    pen.fill(r, '#e8262e' if lit > 0.5 else '#f4f4f2', a)
    pen.line(r, 3, '#ffffff' if lit > 0.5 else '#c8c8d0', a)
    text(cv, label, x, y + 20 + 6 * press, 400, 58, '#ffffff' if lit > 0.5 else '#16171c', a, 0.1, 'center', 0.8)


def B_pause(F, sh):
    """The comment prompt as a phone call on hold: the last frame of the story freezes, drains and dims, and a HOLD
    screen slides over it (ON HOLD, the elapsed time, a little equalizer), then by stage: 'hold' YOUR CALL IS IMPORTANT
    TO US; 'word' ONE WORD + the comment box + BEFORE RULE 2; 'ask' the question and the two keys ASK / DON'T;
    'dont' DON'T lit red and the years counter (1979 -> 2019: forty years on hold). p: src (the frozen time), t_hold
    (when the hold began: the timer), stage."""
    p = sh.p
    src = p['src']
    th = p.get('t_hold', sh.t0)
    stage = p.get('stage', 'hold')
    t0 = sh.t0
    first = p.get('first', False)
    lay = _img_layer(F, lambda t: src, 'freeze', 1.0, lambda t: (0.0, 0.0, 1.0 + 0.01 * clamp((t - th) / 20.0)))

    def hud(cv, t):
        pen = Pen(cv)
        u = t - th
        ap = ease_out_cubic(clamp(u / 0.6)) if first else 1.0
        y0 = lerp(1100, 0, ap)
        cv.save(); cv.translate(0, y0)
        # the hold panel
        panel = rrect(560, 150, 800, 300, 40)
        pen.fill(moved(panel, 0, 14), '#000000', 120, blur=20)
        pen.fill(panel, '#11141c', 235); pen.line(panel, 2, '#3a4052', 255)
        text(cv, 'ON HOLD', 960, 228, 700, 46, '#ffffff', 245, 0.3, 'center', 0.8)
        s_ = max(0.0, u)
        text(cv, '%02d:%02d' % (int(s_ // 60), int(s_ % 60)), 960, 290, 700, 34, '#9aa4b8', 230, 0.2, 'center', 0.5)
        for k in range(9):                                      # the hold music's little equalizer
            hgt = 10 + 34 * abs(math.sin(t * (1.3 + 0.21 * k) + k * 1.7)) * (0.6 + 0.4 * hash01(k))
            pen.fill(rrect(870 + k * 22, 380 - hgt, 12, hgt, 4), '#d8f2a0', 200)
        if stage == 'hold':
            n_ = int(clamp((t - p.get('t_type', t0)) / 1.3) * 29)
            text(cv, 'YOUR CALL IS IMPORTANT TO US'[:n_], 960, 560, 1500, 54, '#ffffff', 240, 0.12, 'center', 0.8)
        cv.restore()
        if stage == 'word':
            text(cv, 'ONE WORD', 960, 560, 1500, 74, '#ffffff', 245 * clamp((t - t0) / 0.3), 0.14, 'center', 0.9)
            text(cv, 'BEFORE RULE 2', 960, 640, 1500, 34, '#d8f2a0', 230 * clamp((t - p.get('t_rule', t0 + 2.0)) / 0.3), 0.3, 'center', 0.6)
            _comment_cue(cv, t - p.get('t_box', t0 + 0.6), 1.0, 860)
        if stage in ('ask', 'dont'):
            q_a = clamp((t - t0) / 0.3)
            text(cv, 'WOULD YOU HAVE ASKED', 960, 560, 1500, 50, '#ffffff', 240 * q_a, 0.12, 'center', 0.8)
            text(cv, 'WHAT THEY FOUND?', 960, 622, 1500, 50, '#ffffff', 240 * q_a, 0.12, 'center', 0.8)
            ka = clamp((t - p.get('t_keys', t0 + 0.5)) / 0.35) if stage == 'ask' else 1.0
            pulse = 0.5 + 0.5 * math.sin((t - t0) * 5.0) if stage == 'ask' and t > p.get('t_pulse', 1e9) else 0.0
            if ka > 0:
                lit = clamp((t - p.get('t_press', 1e9)) / 0.12) if stage == 'dont' else 0.0
                _hold_key(pen, cv, 760, 800, 'ASK', t, 0.0, 0.0, 255 * ka * (1.0 - 0.6 * lit))
                _hold_key(pen, cv, 1160, 800, "DON'T", t, lit, lit * (1 - clamp((t - p.get('t_press', 1e9) - 0.15) / 0.2)) + 0.25 * pulse, 255 * ka)
            if stage == 'dont':
                tp = p.get('t_press', t0)
                yr = int(lerp(1979, 2019, ease_in_out(clamp((t - tp - 0.3) / 2.0))))
                ya = clamp((t - tp - 0.2) / 0.3)
                text(cv, '1979  >  %d' % yr, 960, 905, 1500, 44, '#ff6a6a', 235 * ya, 0.2, 'center', 0.7)
                text(cv, 'FORTY YEARS ON HOLD', 960, 948, 1500, 26, '#ffffff', 200 * clamp((t - tp - 2.3) / 0.4), 0.3, 'center', 0.6)
    cam = scam(sh, None, dict(mv='hold', free=True))

    def fx(t):
        k = clamp((t - th) / 0.5) if first else 1.0
        d = dict(blur=4.0 * k, dim=0.5 * k, sat=1.0 - 0.75 * k)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    sp_ = Spec([lay], cam, None, 'neutral', 1.0, 0.0, fx=fx, hud=hud)
    sp_.pre = [src]
    return sp_


# ==================================================================================================== cards (placeholders: part B builds the outro)
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
SPACE = {'living': 'inside', 'hall': 'inside', 'kitchen': 'inside', 'bath': 'bath', 'front': 'outside', 'clinic': 'clinic', 'office': 'office',
         'er': 'outside', 'er_bay': 'hospital', 'er_wait': 'hospital', 'hosp_hall': 'hospital', 'cardio': 'clinic', 'car': 'car', 'run': 'outside',
         'outro': 'inside'}


def shot_space(s):
    if s.kind in ('rule', 'black', 'card'): return None
    if s.kind == 'pause': return 'phone'
    if s.kind == 'ins': return 'close'
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if room == 'living' and (s.p.get('set') or {}).get('state') == 'wait': return 'wait'
    if s.kind == 'bust': return {'front': 'outside', 'car': 'car', 'clinic': 'clinic', 'office': 'office', 'er_bay': 'hospital',
                                 'er_wait': 'hospital', 'hosp_hall': 'hospital'}.get(room, 'close')
    return SPACE.get(room, 'inside')


def shot_loc(s):
    if s.p.get('era') in ('1979', 'outro'): return s.p['era']
    room = s.p.get('room') or (s.p.get('bg') or [None])[0]
    if s.kind in ('rule', 'card', 'black', 'pause'): return s.kind
    if room in ('clinic', 'office', 'er', 'er_bay', 'er_wait', 'hosp_hall', 'cardio'): return 'hospital'
    if room == 'car': return 'car'
    if room == 'living' and (s.p.get('set') or {}).get('state') == 'wait': return 'waiting_room'
    if room == 'front': return 'outside'
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
    if sh.kind == 'pause':
        st_ = p.get('stage')
        if p.get('first'):
            sh.sfx.append(_ev(sh.t0, 'hold_click', 0, 0, 'phone'))
            sh.music.append({'t': round(sh.t0, 3), 'type': 'hold', 'level': 0.5, 'len': round(F.t(103) - sh.t0 - 0.5, 2), 'version': 'onhold_clean'})
        if st_ == 'word':
            sh.sfx.append(_ev(p.get('t_box', sh.t0 + 0.6), 'ui_pop', -4, 0, 'close', kind='comment'))
        if st_ == 'ask':
            sh.sfx.append(_ev(p.get('t_keys', sh.t0 + 0.5), 'ui_pop', -6, 0, 'close'))
        if st_ == 'dont':
            sh.sfx.append(_ev(p.get('t_press', sh.t0), 'key_press', -2, 0, 'close'))
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
DOCTOR_ROOMS = ('clinic', 'office', 'er', 'er_bay', 'er_wait', 'cardio', 'run')


def glob_fx(F, sh, t, fx):
    """Per-frame global effects (keyed to lines): cut flashes; the house slowly turning the villain's sickly
    fluorescent green-yellow as the hold music spreads (from rule 2's hold music, L110, to the waiting room); the
    waiting room fully his; the climax (the pulse count, L255 .. "I pulled my wrist free", L295) with a green heartbeat
    wash at the frame edge that slows with every count; the rescue / hospital / clinic / doctors' scenes bright, warm and
    clean; fade in / out."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.14: fx['white'] = 0.95 * (1 - u / 0.14)
    ek = EXPO.get(sh.kind, 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    room = sh.p.get('room') or (sh.p.get('bg') or [''])[0]
    if room in DOCTOR_ROOMS and sh.kind in ('set', 'bust'):
        fx['exposure'] = fx.get('exposure', 0.0) + 0.04                # the doctors' world: bright and safe
    clean = era in ('1979', 'outro') or sh.kind in ('rule', 'black', 'card', 'pause') or room in DOCTOR_ROOMS
    if not clean:
        ui = 0.5 if sh.kind == 'ins' else 1.0
        # the hold music creeping through the house: 0 at "Just music." (L110) -> 0.32 by rule 6 (L213); it lifts for the rescue
        k = 0.32 * clamp((t - F.t(110)) / max(1.0, F.t(213) - F.t(110)))
        if t >= F.t(303) - LEAD: k *= 1.0 - clamp((t - F.t(303)) / 3.0)
        if k > 0.004:
            fx['mix'] = ('dr_wait', k * ui)
        # the climax: the count (L255 "So he took my wrist") .. the wrist pulled free (L295)
        if F.t(255) - LEAD <= t < F.t(295) + 1.5:
            ramp = clamp((t - F.t(255)) / 2.0) * (1.0 - clamp((t - F.t(295) - 0.5) / 1.0))
            bpm = lerp(66, 38, clamp((t - F.t(255)) / max(1.0, F.t(270) - F.t(255))))          # he slows the heart down
            if t > F.t(270): bpm = lerp(38, 120, clamp((t - F.t(270)) / max(1.0, F.t(295) - F.t(270))))   # the questions: fighting back
            ph = ((t - F.t(255)) * bpm / 60.0) % 1.0
            beat = math.exp(-ph * 9.0) + 0.6 * math.exp(-max(0.0, ph - 0.18) * 11.0) * (ph >= 0.18)
            if 'flash' not in fx:
                fx['flash'] = _epost.Spill(0.35 * ramp * clamp(beat) * ui, side=-1.0 if sh.idx % 2 else 1.0, color=(0.55, 0.95, 0.35), reach=0.8)
            fx['sat'] = fx.get('sat', 1.0) * (1.0 - 0.25 * ramp)
    if t > F.duration - 3.0: fx['fade'] = clamp((t - (F.duration - 3.0)) / 1.8)
    if t < 0.4: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.4)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds by place and time, keyed to lines (the sound step maps the names): the house at night, the 1979
    house, the clinic by day, the office at 3 AM, the rain from rule 4, Halverson's car idling in the driveway, the hold
    music from the receiver on the counter (and later from every room), the waiting room's buzzing tubes."""
    t, e = F.t, F.e
    D = F.duration
    out = []

    def bed(t0, t1, name, g, space, **k):
        if t1 > t0: out.append(_ev(t0, name, g, 0, space, dur=round(t1 - t0, 2), **k))
    bed(0.0, t(15) - 0.2, 'room_tone', -12, 'inside', kind='house_night')
    bed(t(18) - 0.1, t(32) - 0.1, 'room_tone', -12, 'inside', kind='house_1979')
    bed(t(32) - 0.1, t(49) - 0.1, 'room_tone', -14, 'inside', kind='house_evening')
    bed(t(49) - 0.1, t(56) - 0.1, 'room_tone', -10, 'clinic', kind='clinic_day')
    bed(t(56) - 0.1, t(213) - 0.1, 'room_tone', -8, 'inside', kind='house_night')
    bed(t(56) - 0.1, t(149) - 0.1, 'ambience_night', -18, 'outside', crickets=0.4, wind=0.4, through_walls=True)
    bed(t(145) - 0.5, t(306), 'rain', -16, 'outside', through_walls=True)
    bed(t(154) - 0.1, t(307), 'car_idle', -20, 'outside', far=True)
    bed(t(213) - 0.1, t(303) - 0.1, 'fluorescent_buzz', -10, 'wait')
    bed(t(303) - 0.1, t(348) - 0.1, 'rain', -12, 'car', inside_car=True)
    bed(t(348) - 0.1, t(362) - 0.1, 'room_tone', -8, 'hospital', kind='er_busy')
    bed(t(362) - 0.1, D, 'room_tone', -14, 'inside', kind='warm_room')
    return out


INTENSITY = [  # (line, level): the story's tension, read off the beats
    (0, 0.6), (2, 0.75), (4, 0.9), (6, 0.8), (9, 0.5), (12, 0.65), (13, 0.75), (14, 0.7), (15, 0.25), (18, 0.4), (26, 0.55), (29, 0.45),
    (30, 0.5), (32, 0.3), (40, 0.2), (49, 0.15), (50, 0.3), (56, 0.3), (58, 0.4), (65, 0.55), (67, 0.6), (72, 0.75), (80, 0.85), (83, 0.9),
    (88, 0.8), (89, 0.6), (92, 0.25), (103, 0.55), (107, 0.7), (110, 0.6), (117, 0.6), (121, 0.75), (123, 0.8), (124, 0.6), (127, 0.6),
    (134, 0.75), (138, 0.9), (141, 0.7), (145, 0.55), (146, 0.6), (149, 0.7), (155, 0.6), (162, 0.75), (167, 0.7), (171, 0.55),
    (179, 0.65), (182, 0.5), (187, 0.85), (191, 0.9), (192, 0.7), (195, 0.75), (201, 0.8), (208, 0.85), (211, 0.9), (212, 1.0),
    (213, 0.85), (217, 0.9), (224, 0.85), (235, 0.95), (250, 1.0), (252, 0.9), (258, 1.0), (268, 0.95), (276, 0.9), (281, 0.95),
    (294, 1.0), (295, 0.8), (303, 0.75), (309, 0.6), (319, 0.45), (331, 0.7), (335, 0.9), (344, 0.8), (348, 0.5), (355, 0.35),
    (359, 0.55), (362, 0.2), (379, 0.3), (397, 0.55), (399, 0.45), (401, 0.15), (455, 0.05)]


def intensity_curve(F):
    pts = [[round(F.t(i), 2), round(v, 3)] for i, v in INTENSITY]
    pts.append([round(F.duration, 2), 0.0])
    return pts


HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left): (line, offset from its start, length)
EXTRA_SIL = [(4, -0.9, 0.8), (13, 3.0, 0.6), (72, -0.6, 0.6), (88, -0.5, 0.6), (138, 1.6, 0.9), (149, -0.6, 0.7), (187, 6.5, 1.0),
             (212, -0.8, 0.8), (235, 5.0, 1.0), (250, -0.8, 0.8), (258, -0.7, 0.7), (269, -0.6, 0.6), (281, -0.6, 0.6), (335, -0.7, 0.7)]
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
    plan_family(F)
    plan_rule1(F)
    plan_pause(F)
    plan_rule2(F)
    plan_rule3(F)
    plan_rule4(F)
    plan_rule5(F)
    plan_partb(F)
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

# ==================================================================================================== PLAN helpers (this film)
def T(i, off=0.0):
    """Cut time for line i: 0.1 s before its first word."""
    return _FILM[0].t(i) - LEAD + off


def W(i, word, k=0, off=0.0):
    """Cut time for a word inside line i (its ASR start, 0.1 s early)."""
    return _FILM[0].w(i, word, k) - LEAD + off


def WD(i, word, k=0, off=0.0):
    """The word's own start (for actions that land ON the word)."""
    return _FILM[0].w(i, word, k) + off


AT_PHONE = (-1.58, 7.42)           # standing at the kitchen wall phone, facing it (east)
PHONE_PT = (-1.2, 7.45)            # the phone on the east wall
NARR_PHONE = (-2.3, 6.75)          # the narrator a step behind Grandma at the phone
RECV_ANG = 90.0                    # the handset hung vertically on its hook
NIGHT_HOUSE = dict(tod='night')
KIT = dict(hood=1.0, ceiling=0.0)
KIT_EVE = dict(hood=1.0, ceiling=1.0)                       # the kitchen in the evening, lights on
KIT79 = dict(era='1979', hood=1.0, ceiling=0.25)
LIV79 = dict(state='1979', lamp=1.0)
FIG_LIGHT = {}

# custom cameras on the plan (eye (x, y, Y), look (x, y, Y))
K_PHONE_TWO = cm((-1.34, 8.55, 1.5), (-1.95, 7.05, 1.25), S=760, sx=1000, sy=560)       # by the wall, north of the phone: Ruth's face 3/4, the narrator beyond
K_PHONE_MED = cm((-1.36, 8.35, 1.5), (-1.62, 7.42, 1.45), S=900, sx=820, sy=560)        # closer on Ruth at the phone
K_PHONE_LOW = cm((-2.55, 7.2, 0.75), (-1.3, 7.75, 0.45), S=820, sx=960, sy=560)          # low: her hand at the jack
K_MILO_TWO = cm((-3.2, 6.15, 1.2), (-2.15, 7.3, 1.05), S=820, sx=960, sy=560)           # Milo and Ruth by the table
K_FLOOR_MED = cm((-2.75, 6.3, 1.35), (-2.1, 8.3, 0.5), S=820, sx=960, sy=560)          # the three on the kitchen floor
K_FLOOR_NARR = cm((-1.6, 7.35, 0.95), (-2.45, 8.45, 0.6), S=820, sx=980, sy=560)        # over the narrator kneeling, toward Ruth
OFFICE_C = dict(mv='push', f=1.7, x=900, y=430, rate=0.012)                               # the office view, optically closer on Halverson at her desk
HOSP_FAR = cm((1.3, 21.5, 1.45), (1.3, 31.37, 1.0), S=1500, sx=960, sy=520)             # down the corridor: him in the last chair, the empty chairs
K_MILO_SIDE = cm((-3.05, 7.75, 1.2), (-2.3, 7.68, 1.0), S=700, sx=960, sy=560)            # Milo and Ruth in profile, from the table
K_TABLE = cm((-2.55, 6.35, 1.3), (-3.25, 7.65, 0.8), S=900, sx=960, sy=560)              # the kitchen table: asleep at dinner
RUTH_FLOOR = (-2.1, 8.5, 0.0)          # Ruth on the kitchen floor, her back to the counter corner, facing the room (SW)
FLOOR_FACE = (-3.1, 7.1)
NARR_KNEEL = (-1.6, 7.55, 0.0)         # the narrator kneeling beside them (east), facing Ruth
CLINIC_TWO = cm((1.4, 3.6, 1.35), (2.6, 1.8, 1.1), S=760, sx=960, sy=560)               # Halverson and Mom beside the exam table
HALL_DOOR_MED = cm((-0.35, 2.4, 1.5), (-0.4, 0.6, 1.3), S=900, sx=960, sy=520)          # Ruth at the front door, from the hall
HALL_KNOCK = cm((-0.2, 3.6, 1.45), (-0.4, 0.05, 1.2), S=820, sx=960, sy=520)            # the front door down the hall
PORCH_MED = cm((0.45, -0.1, 1.5), (-0.45, -0.75, 1.35), S=650, sx=900, sy=520)            # Halverson at the door, her face 3/4 (from beside the door)
HALL79_PHONE = cm((-1.36, 8.35, 1.5), (-1.7, 7.2, 1.35), S=820, sx=900, sy=560)          # 1979: Ruth79 at the phone, Grandpa beyond
LIV79_MED = cm((-2.75, 2.85, 1.2), (-3.95, 1.0, 0.85), S=900, sx=960, sy=560)            # 1979 sunrise: the chair, Ruth79 beside it
HOSP_CLOSE = cm((1.3, 28.9, 1.15), (1.3, 31.37, 1.0), S=1050, sx=960, sy=560)            # the last plastic chair, close
HOSP_MED = cm((1.15, 29.6, 1.35), (1.3, 31.37, 1.25), S=1000, sx=960, sy=520)
BUS_MED = cm((-44.6, -23.4, 0.9), (-46.0, -20.5, 0.7), S=900, sx=960, sy=560)             # the bus-stop bench, closer
CAR_MED = cm((-7.0, -2.9, 0.75), (-7.67, -4.65, 0.55), S=1000, sx=960, sy=560)            # Halverson in the driver's seat through the side glass


def ring_times(t0, t1, n):
    """n rings spread from t0 to t1 (absolute)."""
    return [t0 + (t1 - t0) * k / max(1, n - 1) for k in range(n)]


def ring_tags(times, labels, x=1640, y=210, hold=1.0):
    return [(t_, s_, x, y, 'pill', hold) for t_, s_ in zip(times, labels)]


def ring_sfx(times, first_index=1, gain=-2.0, space='inside'):
    return [(t_, 'phone_ring', gain, 0.0, space, dict(index=first_index + k)) for k, t_ in enumerate(times)]


class PhoneState:
    """The wall phone's handset over one shot: 'hung' until the grab, 'off' (in her hand) until it is put somewhere
    ('hung' again or 'counter'). The set reads it as phone=f(t); the shot's acts fill the times."""
    def __init__(self, start='hung'):
        self.keys = [(-1e9, start)]

    def at(self, t):
        s = self.keys[0][1]
        for tk, sk in self.keys:
            if t >= tk: s = sk
        return s

    def __call__(self, t): return self.at(t)


def phone_rig(who='ruth', st=None, pick=None, tilt=None, toward=None, hang=None, counter=None, side=1, held=False, hold_ear=True,
              cord_light=1.0):
    """acts at the kitchen wall phone: pick (t: reach for the handset on its hook, contact 0.55 s later, to the ear);
    held=True: the handset is already at her ear; tilt (t): tilted out toward `toward` (an actor id); hang (t): back on
    its hook; counter (t): laid down on the counter like a sleeping baby (bending, both hands). The coil cord is drawn
    from the hand (or the resting handset) to the base."""
    def acts(A, s, sp):
        a = A[who]
        base = scr(sp, 'phone_cord_base')
        hook = scr(sp, 'phone_hook')
        ppc = spot_of(sp, 'phone_hook').ppm / 100.0
        rec = CH.PropTrack('receiver', hook[0], hook[1] + 9 * ppc, ppc, RECV_ANG)
        t_away = hang if hang is not None else counter
        if held:
            rec.held(-1e9, a, side); a.hold_prop('receiver', side, -1e9, None)
            a.receiver_to_ear(s.t0 - 2.0, t_away, side, fade=0.01)
        elif pick is not None:
            a.look_at(pick - 0.3, hook, t1=pick + 0.8, dur=0.3)
            tc = a.pick_up(rec, pick, side=side, dur=1.0)
            st.keys.append((tc, 'off'))
            a.receiver_to_ear(tc + 0.1, t_away, side)
        if tilt is not None:
            a.receiver_to_ear(tilt, None, side, tilt_out=1.0, fade=0.7, toward=A.get(toward))
        lay_ = []
        if hang is not None:
            a.look_at(hang - 0.2, hook, dur=0.3)
            tc = a.put_down(rec, hang, side, hook[0], hook[1] + 9 * ppc, dur=1.0, angle=RECV_ANG)
            st.keys.append((tc, 'hung'))
        if counter is not None:
            rp = scr(sp, 'receiver_counter')
            a.look_at(counter - 0.3, rp, dur=0.4)
            a.crouch(counter, 0.12, counter + 2.4, 0.8)
            tc = a.put_down(rec, counter, side, rp[0], rp[1] - 4 * ppc, dur=1.8, angle=-80.0)
            st.keys.append((tc, 'off'))                                       # the track draws it on the counter

            def rdraw(pen, t, rec=rec, tc=tc):
                if t >= tc: rec.draw(pen, t)
            lr = Layer(spot_of(sp, 'receiver_counter').depth, rdraw, 'receiver_rest', ref_depth=spot_of(sp, 'receiver_counter').depth)
            rs = spot_of(sp, 'receiver_counter')
            lr.order = sp.order_at(rs.X, rs.Yp) - 0.05
            lay_.append(lr)
        fl = s.I[who]['layer']

        def cord(pen, t):
            stt = st.at(t) if st is not None else 'off'
            if stt == 'hung': return
            h = rec.holder(t)
            e = CH.receiver_cord_end(a, t, side) if h else rec.pos(t)
            CH.draw_coil_cord(pen, e[0], e[1], base[0], base[1], ppc, 0.32, t)
        lc = Layer(fl.depth_at(0.0) - 0.02, cord, 'coil_cord', ref_depth=fl.depth_at(0.0) - 0.02)
        lc.order = (fl.order(0.0) if callable(fl.order) else fl.order) - 0.02
        return lay_ + [lc]
    return acts


def notes_at(anchor_or_xy, t0, t1=None, **k):
    """acts: hold-music notes drifting from an anchor / plan point / screen point."""
    def acts(A, s, sp):
        if isinstance(anchor_or_xy, str) or (isinstance(anchor_or_xy, tuple) and len(anchor_or_xy) == 3):
            src = scr(sp, anchor_or_xy)
        else:
            src = anchor_or_xy
        return [notes_layer(src, t0, t1, **k)]
    return acts


def _AA(*fns):
    """Several shot-level acts in one."""
    def acts(A, s, sp):
        out = []
        for f in fns:
            if f: out += [l for l in (f(A, s, sp) or []) if l is not None]
        return out
    return acts


def card_tap_hand(t_in, taps, who='ruth', x=905, y=505):
    """An insert hand: Ruth's index finger comes in from the lower right and taps the card (taps = absolute times)."""
    def fn(t):
        u = clamp((t - t_in) / 0.45)
        if u <= 0: return None
        e = ease_out_cubic(u)
        dy = 0.0
        for tp in taps:
            d = t - tp
            if -0.12 <= d <= 0.16: dy = max(dy, (1 - abs(d - 0.02) / 0.14) * 26.0)
        return (lerp(x + 520, x, e), lerp(y + 560, y, e) + 26.0 - dy, 152.0, 1.0)
    return dict(who=who, fn=fn, size=420.0, shape='point', side=1, sleeve_from=(x + 900, y + 1100))


# ==================================================================================================== COLD OPEN (0-14)
def plan_open(F):
    t, e, C = F.t, F.e, F.cut
    # 0 "If your doctor calls at three in the morning to tell you your test results came back... don't ask what they found."
    r0 = ring_times(t(0) + 0.15, W(0, 'three') - 0.4, 2)
    C(T(0), 'ins', name='phone', kw=dict(state='hung', ring=ring_fn(r0, T(0)), cord='in'), c=dict(mv='push', rate=0.035),
      sfx=ring_sfx(r0, 1, -3, 'close'))
    C(W(0, 'three'), 'ins', name='clock', kw=lambda u: dict(time=(2, 59, 50 + 10 * clamp(u / 1.0)), bg='kitchen'), c=dict(mv='push', rate=0.03),
      sfx=[(WD(0, 'three') + 0.6, 'clock_tick', -10, 0, 'close', dict(dur=1.6))])
    C(W(0, 'test'), 'set', room='office', view='desk', set=dict(owner='halverson'), rim=OFFICE,
      ppl=[P('halverson', 'desk_chair', expr='exhausted',
             act=_A(lambda a, s: (a.phone_to_ear(-1.0, None, side=-1), a.hold_prop('cell', -1, -1.0, None)),
                    lambda a, s: a.look_at(s.t0, scr(s.sp, 'results'), dur=0.3), blinks(W(0, 'test') + 0.9)))],
      c=OFFICE_C)
    C(W(0, "don't"), 'ins', name='card', kw=dict(hl=1, show=7), motion=lambda u: (0.0, -60.0 * ease_in_out(clamp(u / 2.5)), 0.25, 0.0), c=dict(mv='push', rate=0.02))
    # 1 "If they put you on hold... don't hang up."
    C(T(1), 'ins', name='phone_counter', kw=dict(music=1.0), c=dict(mv='push', rate=0.03), music=[(T(1), 'hold', 0.45, 3.0, dict(version='tinny_receiver'))])
    # 2 the waiting room; the tall man folded into a plastic chair; the clipboard; the tape
    C(T(2), 'set', room='hall', view='livdoor', set=dict(living_state='wait', door=95.0, hall=0.1),
      rim=WAITR, c=dict(mv='push', f=1.0, rate=0.03), sfx=[(T(2) + 0.35, 'door_creak', -6, 0, 'inside', dict(dur=1.6))])
    C(W(2, 'very'), 'set', room='hosp_hall', view='chair', rim=WAITR,
      ppl=[P('later', 'last_chair', act=_A(lambda a, s: a.click_pen([W(2, 'very') + 1.6]), pose(-9, None, 0.1, h_tilt=12.0)))],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(W(2, 'knees'), 'set', room='hosp_hall', view='chair', cam=HOSP_CLOSE, rim=WAITR,
      ppl=[P('later', 'last_chair', act=_A(pose(-9, None, 0.1, h_tilt=14.0), lambda a, s: a.click_pen([s.t0 + 1.2])))],
      c=dict(mv='push', f=1.0, rate=0.015))
    C(W(2, 'clipboard'), 'ins', name='clipboard', kw=dict(click=lambda u: 1.0 if 0.9 < u < 1.05 else 0.0), c=dict(mv='push', rate=0.03),
      sfx=[(W(2, 'clipboard') + 1.0, 'pen_click', -4, 0, 'close')])
    C(W(2, 'head'), 'bust', who='later', bg=('hosp_hall', 'chair'), cx=960, cy=760, scale=0.62, light=WAITR,
      act=_A(pose(-9, None, 0.1, h_tilt=18.0), lambda a, s: a.set(-9, None, 0.1, look_y=0.1)), c=dict(mv='push', rate=0.0, zrate=0.02, y=600))
    # 3 "and he looks up at you and says, very kindly,"
    C(T(3), 'set', room='hosp_hall', view='chair', cam=HOSP_MED, rim=WAITR,
      ppl=[P('later', 'last_chair', act=_A(pose(-9, None, 0.1, h_tilt=-16.0), pose(t(3) + 0.3, None, 1.6, h_tilt=8.0),
                                            lambda a, s: a.look_at(t(3) + 0.3, (960, 380), dur=1.6, z=600.0)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 4-5 "Take a seat." "It can wait."  his own voice from behind the tape: head dips, pen clicks
    C(T(4), 'bust', who='later', bg=('hosp_hall', 'chair'), cx=960, cy=600, scale=0.42, turn=0.0, light=WAITR,
      act=_A(pose(-9, None, 0.1, h_tilt=16.0), pose(t(4) + 0.05, t(4) + 0.6, 0.25, h_nod=0.12), pose(t(5) + 0.05, None, 1.2, h_tilt=24.0),
             lambda a, s: a.click_pen([t(4) - 0.4, e(5) + 0.3])),
      c=dict(mv='push', rate=0.0, zrate=0.012))
    # 6 "Don't sit down."  the long corridor, him tiny in the last chair
    C(T(6), 'set', room='hosp_hall', view='hall', cam=HOSP_FAR, rim=WAITR, ppl=[P('later', 'last_chair', act=pose(-9, None, 0.1, h_tilt=10.0))],
      c=dict(mv='push', f=1.0, rate=0.01))
    # 7-8 the recording
    C(T(7), 'ins', name='phone_counter', kw=dict(music=1.0), c=dict(mv='push', rate=0.025))
    C(T(8), 'set', room='kitchen', view='phone_side', set=dict(KIT, phone='counter'), c=dict(mv='push', f=1.0, rate=0.015),
      acts=notes_at('receiver_counter', T(8), None, slow=1.4, size=26.0))
    # 9 "My grandmother had seven rules..."  10 "...taped inside the medicine cabinet, behind the mirror, ... already sick."
    C(T(9), 'set', room='bath', view='cabinet', set=dict(cabinet=1.0, vanity=1.0), rim=NIGHT, c=dict(mv='push', f=1.0, rate=0.02))
    C(W(9, 'seven'), 'ins', name='card', kw=dict(hl=0, show=7), c=dict(mv='push', rate=0.025))
    t_open = W(10, 'behind') - 0.9
    C(T(10), 'set', room='bath', view='sink', set=dict(cabinet=lambda tt: ease_in_out(clamp((tt - t_open) / 1.0)), vanity=1.0), rim=NIGHT,
      ppl=[P('narr14', 'sink', face=(2.8, 6.75), expr='fear',
             act=_A(lambda a, s: a.reach_to(t_open - 0.55, 1, scr(s.sp, 'mirror', -60, 40), t1=t_open + 0.35, dur=0.5, contact='palm', shape='flat', z=-40.0),
                    lambda a, s: a.look_at(T(10) + 0.2, scr(s.sp, 'mirror'), dur=0.4), blinks(T(10) + 1.4)))],
      c=dict(mv='push', f=1.0, rate=0.015), sfx=[(t_open + 0.1, 'cabinet_open', -6, 0, 'bath')])
    C(W(10, 'behind'), 'ins', name='card', kw=dict(hl=0, show=7), motion=lambda u: (0.0, 0.0, -0.25 + 0.05 * u, 0.0), c=dict(mv='push', rate=0.02))
    # 11 "Every one of those rules was about waiting."
    C(T(11), 'ins', name='card', kw=dict(hl=0, show=7), motion=lambda u: (40.0 * u, 0.0, 0.03 * u, 0.0), c=dict(mv='push', rate=0.02))
    # 12 "...the night my little brother almost died..."  flash-forward: Grandma rocking Milo on the kitchen floor
    C(T(12), 'set', room='kitchen', view='floor', cam=K_FLOOR_MED, set=dict(KIT, phone='counter'), rim=NIGHT_L,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='grief_still', act=lambda a, s: a.rock(s.t0 - 1.0, None, 1.0, 0.45, hum=False)),
           P('milo_sick', (-2.45, 8.15, 0.0), kind='floor', face=FLOOR_FACE, expr='dazed',
             act=_A(lambda a, s: a.rock(s.t0 - 1.0, None, 0.8, 0.45, hum=False), lambda a, s: a.breathe_fast(s.t0, None, 0.95),
                    pose(-9, None, 0.1, lean=-0.18, h_tilt=-8.0)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 13 "By sunrise, there would be a doctor knocking at our door, a stranger sitting in my grandfather's chair, and a phone..."
    C(T(13), 'set', room='front', view='porch', set=dict(rain=1.0, car=True, headlights=1.0), rim=RAIN,
      ppl=[P('halverson_rain', 'porch_door', expr='pleading', face=(-0.4, 0.2),
             act=lambda a, s: a.knock(WD(13, 'knocking') - 0.2, n=3, spacing=0.34, side=0.0))],
      c=dict(mv='push', f=1.0, rate=0.02))
    C(W(13, 'stranger'), 'set', room='living', view='him', set=dict(state='wait'), rim=WAITR,
      ppl=[P('later', 'armchair', act=_A(pose(-9, None, 0.1, h_tilt=10.0), lambda a, s: a.click_pen([s.t0 + 1.1])))],
      c=dict(mv='push', f=1.0, rate=0.02))
    rr = ring_times(WD(13, 'phone') + 0.2, e(13) + 0.4, 2)
    C(W(13, 'phone'), 'ins', name='phone', kw=dict(state='hung', cord='out', ring=ring_fn(rr, W(13, 'phone'))), c=dict(mv='push', rate=0.03),
      sfx=ring_sfx(rr, 1, -4, 'close'))
    # 14 "...the difference between a scary voice... and a dangerous one."
    C(T(14), 'bust', who='halverson', bg=('office', 'desk'), set=dict(owner='halverson'), cx=1040, cy=600, scale=0.8, turn=-0.3, h_turn=-0.1,
      expr='exhausted', light=OFFICE, act=_A(lambda a, s: a.phone_to_ear(-1.0, None, side=-1), lambda a, s: a.hold_prop('cell', -1, -1.0, None), blinks(T(14) + 1.2)))
    C(W(14, 'and'), 'bust', who='later', bg=('living', 'him', None), set=dict(state='wait'), cx=960, cy=600, scale=0.45, light=WAITR,
      act=_A(pose(-9, None, 0.1, h_tilt=18.0), lambda a, s: a.click_pen([e(14) + 0.2])), c=dict(mv='push', rate=0.0, zrate=0.02),
      music=[(W(14, 'dangerous'), 'hit', 0.6)])


# ==================================================================================================== 1979 AND THE FAMILY (15-64)
def plan_family(F):
    t, e, C = F.t, F.e, F.cut
    # 15-17 Grandma Ruth, the word "hospital", "that place"
    C(T(15), 'bust', who='ruth', bg=('kitchen', 'wide'), set=KIT_EVE, cx=900, cy=600, scale=0.82, turn=0.25, expr='stern', light=EVE,
      act=_A(blinks(T(15) + 1.6)), tags=[(T(15) + 0.3, 'GRANDMA RUTH', 1340, 380, 'white', 2.6)])
    C(T(16), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('ruth', 'sink', face=(-3.3, 9.6), expr='stern', act=_A(lambda a, s: a.turn(T(16) + 0.2, a.at(s.t0).turn + 0.0, 0.5)))],
      c=dict(mv='push', f=1.1, rate=0.02))
    C(T(17), 'bust', who='ruth', bg=('kitchen', 'wide'), set=KIT_EVE, cx=1040, cy=610, scale=0.86, turn=-0.3, expr='stern', light=EVE,
      act=_A(lookxy(300, 420, T(17) + 0.2, None, 0.5, z=300.0)), tags=[(W(17, 'that') + 0.1, '"THAT PLACE"', 560, 380, 'white', 1.6)])
    # 18 1979: three in the morning, chest pain
    C(T(18), 'ins', name='clock', kw=dict(time=(3, 0, 0), bg='kitchen'), era='1979', grade='dr_1979', c=dict(mv='push', rate=0.03))
    C(W(18, 'grandfather'), 'set', room='kitchen', view='wide', set=KIT79, era='1979', rim=HARVEST,
      ppl=[P('grandpa79', (-3.0, 8.0, 0.0), face=(-2.2, 7.2), expr='stern_afraid',
             act=_A(lambda a, s: a.hand_on(s.t0 - 0.5, 'chest', side=-1), lambda a, s: a.set(WD(18, 'pain'), None, 0.5, lean=0.08))),
           P('ruth79', (-2.25, 7.35, 0.0), face=(-3.0, 8.0), expr='stern_afraid')], focus_on='grandpa79',
      acts=lambda A, s, sp: (A['ruth79'].look_at(s.t0 + 0.2, (A['grandpa79'], 'eyes'), dur=0.4), [])[-1],
      c=dict(mv='push', f=1.05, rate=0.02))
    st19 = PhoneState('hung')
    C(T(19), 'set', room='kitchen', view='phone', set=dict(KIT79, phone=st19), era='1979', rim=HARVEST,
      ppl=[P('ruth79', AT_PHONE, face=PHONE_PT, expr='stern_afraid')], acts=phone_rig('ruth79', st19, pick=T(19) + 0.1), c=dict(mv='push', f=1.05, rate=0.02))
    C(T(20), 'set', room='kitchen', view='phone', cam=HALL79_PHONE, set=dict(KIT79, phone='off'), era='1979', rim=HARVEST,
      ppl=[P('ruth79', AT_PHONE, face=PHONE_PT, expr='stern_afraid', act=lookxy(1500, 430, T(20) + 0.4, None, 0.6, z=200.0))],
      acts=phone_rig('ruth79', None, held=True), c=dict(mv='push', f=1.0, rate=0.015))
    C(T(21), 'ins', name='phone', kw=dict(state='off', era='1979'), era='1979', c=dict(mv='push', rate=0.03),
      music=[(T(21), 'hold', 0.4, 6.0, dict(version='tinny_1979'))])
    C(T(22), 'bust', who='ruth79', bg=('kitchen', 'phone'), set=dict(KIT79, phone='off'), era='1979', cx=960, cy=610, scale=0.84, turn=0.35, h_turn=0.1,
      expr='stern_afraid', light=HARVEST,
      act=_A(lambda a, s: a.receiver_to_ear(-1.0, None, 1, fade=0.01), lambda a, s: a.hold_prop('receiver', 1, -1.0, None),
             lookxy(1300, 420, T(22) + 0.3, None, 0.5, z=300.0), ex('fear', T(22) + 0.4, None, 0.5), ex('neutral', T(24), None, 0.8),
             ex('warm', T(25), None, 0.9), blinks(T(23) + 0.3, T(25) + 0.2)))
    C(T(26), 'set', room='kitchen', view='phone', cam=HALL79_PHONE, set=dict(KIT79, phone='off'), era='1979', rim=HARVEST,
      ppl=[P('ruth79', AT_PHONE, face=PHONE_PT, expr='warm', act=lookxy(700, 520, T(26) + 0.6, None, 0.6, z=200.0)),
           P('grandpa79', (-2.4, 6.6, 0.0), face=(-1.58, 7.42), expr='stern_afraid', act=lambda a, s: a.hand_on(s.t0 - 0.5, 'chest', side=-1))],
      acts=phone_rig('ruth79', None, held=True), c=dict(mv='push', f=1.0, rate=0.015))
    # 27-28 they waited; Grandpa sits down in the brown armchair by the window
    C(T(27), 'set', room='living', view='wide', set=LIV79, era='1979', rim=HARVEST,
      ppl=[P('grandpa79', 'door', path=[(T(27) + 0.1, 'door'), (e(27) + 0.4, (-3.9, 1.4, 0.0))], expr='stern_afraid', enter=True,
             act=lambda a, s: a.hand_on(s.t0 - 0.5, 'chest', side=-1))],
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(28), 'set', room='living', view='chair', set=LIV79, era='1979', rim=HARVEST,
      ppl=[P('grandpa79', 'armchair', expr='stern_afraid', sit_t=WD(28, 'sat') - 0.3, sit_dur=1.1, hands='lap',
             act=_A(lambda a, s: a.hand_on(s.t0 - 0.5, 'chest', side=-1, t1=WD(28, 'wait') + 0.4),
                    lambda a, s: a.look_at(WD(28, 'window'), scr(s.sp, 'window_glass'), dur=0.9)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 29-31 sunrise: the coffee; still sitting there; still waiting (gently)
    C(T(29), 'set', room='living', view='sunrise', set=dict(state='1979', tod='sunrise', coffee=False), era='1979', rim=SUN79,
      ppl=[P('grandpa79', 'armchair', expr='neutral', act=lambda a, s: a.gone(-5.0, 0.1)),
           P('ruth79', 'door', path=[(T(29) + 0.1, 'door'), (e(29) + 0.3, (-3.15, 1.85, 0.0))], expr='warm',
             act=_A(lambda a, s: a.hold_prop('mug', -1, -1.0, None),
                    lambda a, s: a.reach(-1.0, None, -1, out=-30.0, down=130.0, fwd=170.0, shape='grip', up=0.0, fade=0.01),
                    lambda a, s: a.look_at(T(29) + 0.3, scr(s.sp, 'armchair', 0, -260), dur=0.5)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(30), 'set', room='living', view='sunrise', cam=LIV79_MED, set=dict(state='1979', tod='sunrise', coffee=False), era='1979', rim=SUN79,
      ppl=[P('grandpa79', 'armchair', expr='neutral', act=lambda a, s: a.gone(-5.0, 0.1)),
           P('ruth79', (-3.15, 1.85, 0.0), face=(-3.95, 0.94), expr='stern_afraid',
             act=_A(lambda a, s: a.hold_prop('mug', -1, -1.0, None),
                    lambda a, s: a.reach(-1.0, None, -1, out=-30.0, down=130.0, fwd=170.0, shape='grip', up=0.0, fade=0.01)))],
      acts=lambda A, s, sp: (A['ruth79'].look_at(T(30), (A['grandpa79'], 'head'), dur=0.4),
                             A['ruth79'].reach_to(T(30) + 0.8, 1, (A['grandpa79'], 'shoulder_l'), dur=0.9, z=60.0, contact='palm', shape='open'), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(31), 'ins', name='coffee', kw=dict(steam=0.0, cold=1.0), era='1979', c=dict(mv='push', rate=0.02))
    # 32-35 years later: no record of the call; she never forgave the doctors
    C(T(32), 'set', room='kitchen', view='phone', cam=K_PHONE_MED, set=dict(KIT_EVE, phone='off'), rim=EVE,
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern', act=_A(ex('set_jaw', WD(32, 'no'), None, 0.5), blinks(T(32) + 1.0)))],
      acts=phone_rig('ruth', None, held=True), c=dict(mv='push', f=1.0, rate=0.015))
    C(T(33), 'bust', who='ruth', bg=('kitchen', 'wide'), set=KIT_EVE, cx=960, cy=610, scale=0.86, turn=0.2, expr='stern', light=EVE,
      act=_A(ex('set_jaw', T(34), None, 0.5), lambda a, s: a.set(T(34), None, 0.4, lid_l=0.2, lid_r=0.2), blinks(T(33) + 0.8)))
    C(T(35), 'set', room='living', view='chair', set=dict(lamp=1.0), rim=LAMP,
      ppl=[P('ruth', (-3.35, 1.7, 0.0), face=(-3.95, 0.94), expr='grief_still',
             act=lambda a, s: a.reach_to(T(35) + 0.3, 1, scr(s.sp, 'armchair', 30, -300), dur=0.8, contact='palm', shape='open', z=40.0))],
      c=dict(mv='push', f=1.0, rate=0.015))
    # 36-39 Mom: the rules in the cabinet, a nurse anyway, Larkfield General, a year of silence
    C(T(36), 'ins', name='card', kw=dict(hl=0, show=7), motion=lambda u: (-200.0 + 40 * u, 0.0, -0.3, 1.0), c=dict(mv='push', rate=0.02))
    C(T(37), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('mom_rn', (-2.6, 6.75, 0.0), face=(-3.5, 8.0), expr='calm_firm',
             act=_A(lambda a, s: a.reach_to(T(37) + 0.3, 1, (a, 'chest'), dur=0.6, contact='grip', shape='pinch', z=80.0, t1=T(37) + 1.5),
                    lambda a, s: a.look_at(T(37) + 0.3, (a, 'chest'), t1=T(37) + 1.5, dur=0.3)))],
      tags=[(T(37) + 0.4, 'MOM', 1300, 360, 'white', 1.8)], c=dict(mv='push', f=1.1, rate=0.02))
    C(T(38), 'set', room='er', view='ext', set=dict(doors=0.0, rain=False), rim=HOSP, c=dict(mv='push', f=1.0, rate=0.02),
      tags=[(T(38) + 0.3, 'LARKFIELD GENERAL', 960, 300, 'white', 2.0)])
    C(T(39), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('ruth', 'sink', face=(-3.3, 9.6), expr='stern'),
           P('mom_rn', (-2.0, 7.7, 0.0), face=(-3.3, 8.6), expr='calm_firm', act=_A(blinks(T(39) + 1.0), ex('neutral', T(39) + 1.2, None, 0.6)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    # 40-46 Milo: seven, thirsty all the time, up at night, asleep everywhere, the jeans
    C(T(40), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('milo_jeans', (-2.7, 7.0, 0.0), face=(-1.6, 6.4), expr='kid_grin', act=blinks(T(40) + 1.4))],
      tags=[(T(40) + 0.4, 'MILO, 7', 1300, 420, 'white', 2.0)], c=dict(mv='push', f=1.15, rate=0.02))
    C(T(41), 'set', room='kitchen', view='wide', cam=K_MILO_TWO, set=KIT_EVE, rim=EVE,
      ppl=[P('milo_jeans', (-2.7, 7.0, 0.0), face=(-3.6, 6.3), expr='thirsty',
             act=_A(lambda a, s: a.drink(T(41) + 0.2, W(43, 'ask') - 0.3, side=1, gulps=6),
                    lambda a, s: a.look_at(W(43, 'ask'), (500, 420), dur=0.4, z=200.0)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(W(43, 'ask'), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('milo_jeans', (-2.9, 7.3, 0.0), face=(-2.0, 7.7), expr='thirsty',
             act=_A(lambda a, s: a.hold_prop('bottle', 1, -1.0, None),
                    lambda a, s: a.reach(W(43, 'ask'), None, 1, out=60.0, down=150.0, fwd=260.0, shape='grip', up=0.0, fade=0.4))),
           P('mom_rn', (-2.0, 7.7, 0.0), face=(-2.9, 7.3), expr='warm')],
      acts=lambda A, s, sp: (A['milo_jeans'].look_at(s.t0, (A['mom_rn'], 'eyes'), dur=0.3), A['mom_rn'].look_at(s.t0 + 0.2, (A['milo_jeans'], 'eyes'), dur=0.4), [])[-1],
      c=dict(mv='push', f=1.1, rate=0.012))
    C(T(44), 'set', room='hall', view='back', set=dict(hall=0.15, kitchen=0.1, bath_door=60.0), rim=NIGHT,
      ppl=[P('milo', 'hall_mid', path=[(T(44) + 0.1, 'hall_mid'), (e(44) + 0.3, (-0.2, 6.3, 0.0))], expr='sleepy', surface='inside_quiet')],
      tags=[(WD(44, 'four'), '4', 1500, 330, 'white', 0.8), (WD(44, 'five'), '5', 1560, 330, 'white', 1.0)], c=dict(mv='push', f=1.0, rate=0.01))
    C(T(45), 'bust', who='milo_jeans', plain=('#d8a838', '#7a5a20'), cx=960, cy=620, scale=0.9, turn=0.3, h_turn=0.1, expr='sleepy', light=SUN79,
      act=_A(lambda a, s: a.set(-9, None, 0.1, lid_l=1.0, lid_r=1.0, h_tilt=-14.0), lambda a, s: a.set(s.t0, None, 0.01, breath=0.6)))
    C(W(45, 'dinner'), 'set', room='kitchen', view='wide', cam=K_TABLE, set=KIT_EVE, rim=EVE,
      ppl=[P('milo_jeans', 'kchair1', expr='sleepy', hands='lap',
             act=_A(lambda a, s: a.set(-9, None, 0.1, lid_l=1.0, lid_r=1.0, h_tilt=12.0, lean=0.25)))],
      c=dict(mv='push', f=1.2, rate=0.015))
    C(W(45, 'bath'), 'bust', who='milo', bg=('bath', 'sink'), set=dict(ceiling=1.0, cabinet=0.0), cx=1000, cy=640, scale=0.86, turn=-0.3, expr='sleepy', light=EVE,
      act=_A(lambda a, s: a.set(-9, None, 0.1, lid_l=1.0, lid_r=1.0, h_tilt=16.0)))
    C(T(46), 'set', room='kitchen', view='wide', cam=K_MILO_TWO, set=KIT_EVE, rim=EVE,
      ppl=[P('milo_jeans', (-2.7, 7.0, 0.0), face=(-3.6, 6.3), expr='sleepy',
             act=_A(lambda a, s: a.sag(T(46) + 0.2, None, 1.0, 0.9), lambda a, s: a.look_at(T(46) + 0.5, (a, 'hip'), t1=T(46) + 2.2, dur=0.3),
                    lambda a, s: a.hold_up(T(46) + 1.1, None, side=1), lambda a, s: a.set(T(46) + 1.8, None, 0.4, sag=0.35)))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(47), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('mom_rn', (-2.0, 7.7, 0.0), face=(-2.9, 7.3), expr='calm_firm', act=blinks(T(47) + 0.6)),
           P('milo_jeans', (-2.9, 7.3, 0.0), face=(-3.6, 8.0), expr='sleepy', act=lambda a, s: a.hold_up(-1.0, None, side=1))],
      c=dict(mv='push', f=1.1, rate=0.015))
    C(T(48), 'bust', who='mom_rn', bg=('kitchen', 'wide'), set=KIT_EVE, cx=900, cy=600, scale=0.84, turn=0.35, h_turn=0.1, expr='calm_firm', light=EVE,
      act=_A(lookxy(1500, 640, T(48), None, 0.4, z=300.0), lambda a, s: a.set(T(48) + 0.6, None, 0.5, lid_l=0.22, lid_r=0.22, brow_in=0.3)))
    # 49 the clinic: Doctor Halverson, the coffee-stained scrubs, the dinosaur stickers, every kid's favourite dinosaur
    C(T(49), 'set', room='clinic', view='wide', rim=HOSP,
      ppl=[P('halverson', 'stand_table', face=(1.1, 2.35), expr='kind_smile', act=blinks(T(49) + 1.2)),
           P('mom_rn', (0.9, 2.3, 0.0), face=(2.45, 2.1), expr='warm'),
           P('milo_jeans', (1.3, 2.5, 0.0), face=(2.45, 2.1), expr='sleepy')],
      tags=[(WD(49, 'Halverson'), 'DR. ANNA HALVERSON', 1400, 330, 'white', 2.2)], c=dict(mv='push', f=1.0, rate=0.015))
    C(W(49, 'coffee'), 'bust', who='halverson', bg=('clinic', 'wide'), cx=960, cy=420, scale=0.7, turn=-0.25, expr='kind_smile', light=HOSP,
      act=_A(lookxy(560, 520, W(49, 'coffee'), None, 0.4, z=300.0), blinks(W(49, 'coffee') + 0.9)))
    C(W(49, 'dinosaur'), 'ins', name='badge', kw=dict(wet=0.0), c=dict(mv='push', rate=0.03))
    C(W(49, 'knew'), 'set', room='clinic', view='wide', rim=HOSP,
      ppl=[P('milo_jeans', 'exam_table', face=(2.45, 2.1), expr='kid_grin', hands='lap'),
           P('halverson', 'stand_table', face=(3.05, 1.7), expr='kid_grin', act=blinks(W(49, 'knew') + 1.0))],
      acts=lambda A, s, sp: (A['milo_jeans'].look_at(s.t0, (A['halverson'], 'eyes'), dur=0.3), A['halverson'].look_at(s.t0, (A['milo_jeans'], 'eyes'), dur=0.3), [])[-1],
      c=dict(mv='push', f=1.35, x=1050, y=650, rate=0.012))
    # 50 her smile went careful
    C(T(50), 'bust', who='halverson', bg=('clinic', 'table'), cx=1000, cy=610, scale=0.86, turn=-0.3, h_turn=-0.1, expr='kid_grin', light=HOSP,
      act=_A(lookxy(560, 640, T(50), None, 0.4, z=300.0), ex('careful_smile', WD(50, 'smile') - 0.2, None, 0.7), blinks(T(50) + 0.9)))
    # 51 she took some blood
    C(T(51), 'set', room='clinic', view='wide', rim=HOSP,
      ppl=[P('milo_jeans', 'exam_table', face=(2.45, 2.1), expr='brave', hands='lap',
             act=_A(lambda a, s: a.reach(T(51), None, 1, out=20.0, down=200.0, fwd=230.0, shape='open', up=0.0, fade=0.4),
                    lambda a, s: a.look_at(T(51) + 0.6, (1500, 380), dur=0.3))),
           P('halverson', 'stand_table', face=(3.05, 1.7), expr='careful_smile',
             act=_A(lambda a, s: a.hold_prop('vial', 1, -1.0, None),
                    lambda a, s: a.reach(T(51) + 0.3, None, 1, out=-30.0, down=120.0, fwd=200.0, shape='grip', up=0.0, fade=0.5)))],
      acts=lambda A, s, sp: (A['halverson'].reach_to(T(51) + 0.2, -1, (A['milo_jeans'], 'elbow_l'), dur=0.6, z=80.0, contact='palm', shape='grip'),
                             A['halverson'].look_at(T(51) + 0.2, (A['milo_jeans'], 'elbow_l'), dur=0.3), [])[-1],
      c=dict(mv='push', f=1.4, x=1050, y=650, rate=0.012))
    # 52-55 "I'll call you the second the results come in... Day or night. I mean it."
    C(T(52), 'bust', who='halverson', bg=('clinic', 'wide'), cx=1060, cy=610, scale=0.84, turn=-0.4, h_turn=-0.15, expr='careful_smile', light=HOSP,
      act=_A(lookxy(400, 560, T(52), None, 0.4, z=300.0), blinks(e(53) - 0.2)))
    C(T(54), 'set', room='clinic', view='wide', cam=CLINIC_TWO, rim=HOSP,
      ppl=[P('halverson', (2.6, 2.2, 0.0), face=(1.6, 1.85), expr='fierce_kind'),
           P('mom_rn', (1.6, 1.85, 0.0), face=(2.6, 2.2), expr='calm_firm', act=lambda a, s: a.set(WD(55, 'mean'), WD(55, 'mean') + 0.6, 0.25, h_nod=0.2))],
      acts=lambda A, s, sp: (A['halverson'].look_at(s.t0, (A['mom_rn'], 'eyes'), dur=0.3), A['mom_rn'].look_at(s.t0, (A['halverson'], 'eyes'), dur=0.3), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.012))
    # 56 that night, Mom had a shift   57 Grandma was watching us
    C(T(56), 'set', room='hall', view='door', set=dict(hall=0.6, porch=1.0), rim=LAMP,
      ppl=[P('mom_rn', (-0.4, 3.2, 0.0), path=[(T(56) + 0.1, (-0.4, 3.2, 0.0)), (e(56) + 0.2, (-0.4, 1.0, 0.0))], expr='calm_firm', surface='inside')],
      c=dict(mv='push', f=1.0, rate=0.01))
    C(T(57), 'set', room='kitchen', view='wide', set=KIT_EVE, rim=EVE,
      ppl=[P('ruth', (-2.0, 8.6, 0.0), face=(-3.5, 7.65), expr='stern', act=blinks(T(57) + 0.9)),
           P('narr14', 'kchair1', expr='neutral', hands='lap'), P('milo_jeans', 'kchair0', expr='sleepy', hands='lap')],
      c=dict(mv='push', f=1.05, rate=0.015))
    # 58 at sundown: the cabinet opened, the mirror swung aside, the card tapped
    t_sw = W(58, 'swung')
    C(T(58), 'set', room='bath', view='sink', set=dict(cabinet=0.0, ceiling=1.0), rim=EVE,
      ppl=[P('ruth', 'sink', face=(2.8, 6.75), expr='stern', enter=True,
             act=_A(lambda a, s: a.reach_to(WD(58, 'opened') - 0.3, 1, scr(s.sp, 'mirror', -60, 40), dur=0.5, contact='grip', shape='grip', z=-40.0),
                    lambda a, s: a.look_at(T(58) + 0.2, scr(s.sp, 'mirror'), dur=0.4)))],
      c=dict(mv='push', f=1.05, rate=0.015))
    C(t_sw, 'set', room='bath', view='cabinet', set=dict(cabinet=lambda tt: ease_in_out(clamp((tt - t_sw - 0.15) / 0.9)), ceiling=1.0), rim=EVE,
      c=dict(mv='push', f=1.0, rate=0.02), sfx=[(t_sw + 0.2, 'cabinet_open', -4, 0, 'bath')])
    taps = [WD(58, 'tapped') + 0.5 + 0.28 * k for k in range(3)]
    C(W(58, 'tapped'), 'ins', name='card', kw=dict(hl=0, show=7), hands=[card_tap_hand(W(58, 'tapped') + 0.05, taps)], c=dict(mv='push', rate=0.02),
      sfx=[(tp, 'card_tap', -6, 0, 'close') for tp in taps])
    # 59-61 seven rules, typed, the colour of weak tea
    C(T(59), 'ins', name='card', kw=dict(hl=0, show=7), c=dict(mv='push', rate=0.02))
    C(T(60), 'ins', name='card', kw=dict(hl=0, show=7), motion=lambda u: (-120.0, 80.0, 0.7 + 0.02 * u, 0.0), c=dict(mv='push', rate=0.02))
    C(T(61), 'ins', name='card', kw=dict(hl=0, show=7), motion=lambda u: (420.0 - 30 * u, 200.0, 0.9, -1.0), c=dict(mv='push', rate=0.02))
    # 62-64 "Same as always," Grandma said. "Nobody gets sick in this house after dark."
    C(T(62), 'bust', who='ruth', bg=('bath', 'sink'), set=dict(cabinet=1.0, ceiling=1.0), cx=900, cy=600, scale=0.84, turn=0.4, h_turn=0.1, expr='stern', light=EVE,
      act=_A(lookxy(1600, 640, T(62) - 0.2, None, 0.4, z=300.0), blinks(e(62) + 0.1)))
    C(T(63), 'bust', who='ruth', bg=('bath', 'sink'), set=dict(cabinet=1.0, ceiling=1.0), cx=720, cy=600, scale=0.8, turn=0.45, h_turn=0.15, expr='stern', light=EVE,
      act=_A(lookxy(1400, 700, T(63), None, 0.4, z=250.0), blinks(T(64) - 0.2)),
      busts=[dict(who='narr14', cx=1300, cy=640, scale=0.66, turn=-0.4, expr='neutral', light=EVE, depth=1.03,
                  act=lambda a, s: a.look_at(T(63), (720, 520), dur=0.4, z=250.0)),
             dict(who='milo', cx=1600, cy=720, scale=0.62, turn=-0.45, expr='sleepy', light=EVE, depth=1.05,
                  act=lambda a, s: a.look_at(T(63) + 0.2, (720, 520), dur=0.4, z=250.0))])


# ==================================================================================================== RULE 1 (65-91)
def plan_rule1(F):
    t, e, C = F.t, F.e, F.cut
    C(T(65), 'rule', n=1)
    rings = ring_times(WD(67, 'phone') + 0.15, WD(72, 'seven') + 0.5, 7)
    lab = ['RING %d' % (k + 1) for k in range(7)]
    tg = ring_tags(rings, lab)
    rsx = ring_sfx(rings, 1, -2, 'inside')

    def tags_in(t0, t1): return [x for x in tg if t0 <= x[0] < t1]
    C(T(67), 'ins', name='clock', kw=lambda u: dict(time=(2, 59, 57 + 3 * clamp(u / 0.9)), bg='kitchen'), c=dict(mv='push', rate=0.03),
      sfx=[(T(67) + 0.2, 'clock_tick', -10, 0, 'close', dict(dur=1.2))])
    C(W(67, 'phone'), 'set', room='kitchen', view='phone', set=dict(KIT, ring=ring_fn(rings, 0.0)), c=dict(mv='push', f=1.0, rate=0.02),
      tags=tags_in(W(67, 'phone'), T(68)), sfx=rsx)
    C(T(68), 'ins', name='phone', kw=dict(state='hung', cord='in', ring=ring_fn(rings, T(68))), c=dict(mv='push', rate=0.03), tags=tags_in(T(68), T(69)))
    C(T(69), 'set', room='kitchen', view='hall', set=dict(KIT, ring=ring_fn(rings, 0.0)),
      ppl=[P('narr14', 'milo_enter', path=[(T(69), (-0.9, 6.45, 0.0)), (e(69) + 0.3, (-1.75, 6.5, 0.0))], expr='fear', surface='inside_quiet')],
      tags=tags_in(T(69), T(70)), c=dict(mv='push', f=1.0, rate=0.012))
    C(T(70), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, ring=ring_fn(rings, 0.0)),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern', act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'phone_hook'), dur=0.2))),
           P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear')],
      tags=tags_in(T(70), T(71)), c=dict(mv='push', f=1.0, rate=0.012))
    C(T(71), 'bust', who='ruth', bg=('kitchen', 'phone', K_PHONE_TWO), set=KIT, cx=880, cy=610, scale=0.88, turn=0.45, h_turn=0.15, expr='stern', light=NIGHT_L,
      act=_A(lookxy(1500, 460, T(71) - 0.3, None, 0.3, z=300.0), lambda a, s: a.set(-9, None, 0.1, lid_l=0.1, lid_r=0.1)), tags=tags_in(T(71), T(72)))
    C(T(72), 'ins', name='phone', kw=dict(state='hung', cord='in', ring=ring_fn(rings, T(72))), c=dict(mv='push', rate=0.035), tags=tags_in(T(72), T(73)))
    # 73 she picks it up and tilts it so I can hear
    st73 = PhoneState('hung')
    C(T(73), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, phone=st73),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern'),
           P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear', act=_A(lambda a, s: a.set(WD(73, 'tilted') + 0.4, None, 0.8, lean=0.18, h_tilt=-10.0)))],
      acts=_AA(phone_rig('ruth', st73, pick=T(73) + 0.15, tilt=WD(73, 'tilted') + 0.1, toward='narr14'),
               lambda A, s, sp: (A['narr14'].look_at(T(73), (A['ruth'], 'hand_r'), dur=0.3), [])[-1]),
      c=dict(mv='push', f=1.0, rate=0.012), sfx=[(T(73) + 0.7, 'phone_pickup', -4, 0, 'inside')])
    # 74 a woman's voice (the narrator's ear at the tilted receiver)
    C(T(74), 'bust', who='narr14', bg=('kitchen', 'phone', K_PHONE_TWO), set=dict(KIT, phone='off'), cx=1000, cy=620, scale=0.88, turn=-0.45, h_turn=-0.2,
      expr='neutral', light=NIGHT_L, act=_A(lambda a, s: a.set(-9, None, 0.1, h_tilt=-10.0), lookxy(500, 600, T(74), None, 0.3, z=250.0), blinks(T(74) + 0.7)))
    # 75-79 Halverson in her office at 3 AM: rough, out of breath; "This is Doctor Halverson. I'm so sorry about the hour."
    HAL_PHONE = _A(lambda a, s: a.phone_to_ear(-1.0, None, side=-1), lambda a, s: a.hold_prop('cell', -1, -1.0, None))
    C(T(75), 'set', room='office', view='desk', set=dict(owner='halverson'), rim=OFFICE,
      ppl=[P('halverson', 'desk_chair', expr='exhausted', act=_A(HAL_PHONE, pose(-9, None, 0.1, lean=0.12), blinks(T(75) + 0.9)))],
      c=OFFICE_C)
    C(T(77), 'bust', who='halverson', bg=('office', 'desk'), set=dict(owner='halverson'), cx=1020, cy=600, scale=0.86, turn=-0.35, h_turn=-0.1, expr='exhausted',
      light=OFFICE, act=_A(HAL_PHONE, lambda a, s: a.set(-9, None, 0.1, lid_l=0.35, lid_r=0.35), blinks(T(77) + 1.2, T(77) + 2.6)))
    C(T(78), 'set', room='office', view='desk', set=dict(owner='halverson'), rim=OFFICE,
      ppl=[P('halverson', 'desk_chair', expr='exhausted', act=_A(HAL_PHONE, lambda a, s: a.look_at(s.t0, scr(s.sp, 'results'), dur=0.4)))],
      c=dict(OFFICE_C, f=2.0, y=420))
    C(T(79), 'bust', who='halverson', bg=('office', 'desk'), set=dict(owner='halverson'), cx=980, cy=610, scale=0.9, turn=-0.25, expr='pleading', light=OFFICE,
      act=_A(HAL_PHONE, blinks(e(79) + 0.1)))
    # 80 "Milo's results came back, and I need you to..."  her voice from the tilted receiver; Ruth's face hardens
    C(T(80), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, phone='off'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern', act=_A(ex('set_jaw', WD(80, 'results'), None, 0.5))),
           P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear', act=lambda a, s: a.set(-9, None, 0.1, lean=0.18, h_tilt=-10.0))],
      acts=_AA(phone_rig('ruth', None, held=True), lambda A, s, sp: (A['ruth'].receiver_to_ear(s.t0 - 2, None, 1, tilt_out=1.0, fade=0.01, toward=A['narr14']),
                                                                       A['ruth'].receiver_to_ear(e(80) - 0.3, None, 1, tilt_out=0.0, fade=0.4), [])[-1]),
      c=dict(mv='push', f=1.0, rate=0.012))
    # 81-83 "Don't tell me," Grandma said. "Don't you dare tell me what you found."
    C(T(81), 'set', room='kitchen', view='phone', cam=K_PHONE_MED, set=dict(KIT, phone='off'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='set_jaw')], acts=phone_rig('ruth', None, held=True), c=dict(mv='push', f=1.0, rate=0.02))
    C(T(83), 'bust', who='ruth', bg=('kitchen', 'phone', K_PHONE_MED), set=dict(KIT, phone='off'), cx=900, cy=610, scale=0.92, turn=0.5, h_turn=0.15, expr='set_jaw',
      light=NIGHT_L, act=_A(lambda a, s: a.receiver_to_ear(-1.0, None, 1, fade=0.01), lambda a, s: a.hold_prop('receiver', 1, -1.0, None)))
    # 84 she hung up
    st84 = PhoneState('off')
    C(T(84), 'set', room='kitchen', view='phone', cam=K_PHONE_MED, set=dict(KIT, phone=st84),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='set_jaw')], acts=phone_rig('ruth', st84, held=True, hang=T(84) + 0.05),
      c=dict(mv='push', f=1.0, rate=0.012), sfx=[(T(84) + 0.6, 'phone_hangup', 0, 0, 'inside')])
    # 85-87 it rang again, and again, nine times
    r2 = ring_times(WD(85, 'rang'), WD(87, 'times') + 0.6, 9)
    tg2 = ring_tags(r2, ['RING %d' % (k + 1) for k in range(9)])
    C(T(85), 'ins', name='phone', kw=dict(state='hung', cord='in', ring=ring_fn(r2, T(85))), c=dict(mv='push', rate=0.03),
      tags=[x for x in tg2 if x[0] < T(86)], sfx=ring_sfx(r2, 1, -1, 'inside'))
    C(T(86), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, ring=ring_fn(r2, 0.0)),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='set_jaw', act=lambda a, s: a.look_at(s.t0, scr(s.sp, 'phone_hook'), dur=0.2)),
           P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear')],
      tags=[x for x in tg2 if T(86) <= x[0] < T(87)], c=dict(mv='push', f=1.0, rate=0.012))
    C(T(87), 'ins', name='phone', kw=dict(state='hung', cord='in', ring=ring_fn(r2, T(87))), motion=lambda u: (0.0, 0.0, 0.08 * u, 0.0),
      c=dict(mv='push', rate=0.03), tags=[x for x in tg2 if T(87) <= x[0]])
    # 88 she pulls the cord out of the wall; the house goes quiet
    C(T(88), 'set', room='kitchen', view='phone', set=dict(KIT, cord=lambda tt: 'in' if tt < T(88) + 0.65 * 1.6 + 0.05 else 'out'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='set_jaw')],
      acts=lambda A, s, sp: (A['ruth'].look_at(T(88), scr(sp, 'jack'), dur=0.3), A['ruth'].pull_cord(T(88) + 0.05, 1, scr(sp, 'jack'), dur=1.6), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(W(88, 'house'), 'ins', name='phone_cord', c=dict(mv='push', rate=0.015))
    # 89 the scariest voice   90-91 I was wrong: the dark hall
    C(T(89), 'bust', who='narr14', bg=('kitchen', 'phone', K_PHONE_TWO), set=dict(KIT, cord='out'), cx=980, cy=620, scale=0.88, turn=-0.35, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(560, 520, T(89), None, 0.4, z=300.0), blinks(T(89) + 1.4)))
    C(T(90), 'set', room='hall', view='back', set=dict(hall=0.0, kitchen=0.05), rim=DARK, c=dict(mv='push', f=1.0, rate=0.02))


# ==================================================================================================== THE COMMENT PROMPT (92-102)
def plan_pause(F):
    t, e, C = F.t, F.e, F.cut
    src = T(92) - 0.4                                     # the dark hall, frozen
    th = T(92)
    C(T(92), 'pause', src=src, t_hold=th, stage='hold', first=True, t_type=WD(94, 'your') - 0.05)
    C(T(95), 'pause', src=src, t_hold=th, stage='word', t_box=WD(96, 'comments') - 0.2, t_rule=WD(97, 'before'))
    C(T(98), 'pause', src=src, t_hold=th, stage='ask', t_keys=WD(99, 'ask') - 0.1, t_pulse=T(100))
    C(T(102), 'pause', src=src, t_hold=th, stage='dont', t_press=WD(102, 'chose') + 0.3)


# ==================================================================================================== RULE 2 (103-123)
def plan_rule2(F):
    t, e, C = F.t, F.e, F.cut
    C(T(103), 'rule', n=2)
    C(T(106), 'ins', name='phone_cord', c=dict(mv='push', rate=0.02))
    r = ring_times(WD(107, 'rang'), WD(107, 'rang') + 2.2, 2)
    C(T(107), 'set', room='kitchen', view='phone', set=dict(KIT, cord='out', ring=ring_fn(r, 0.0)), c=dict(mv='push', f=1.05, rate=0.02),
      sfx=ring_sfx(r, 1, 0, 'inside'), music=[(WD(107, 'rang'), 'stinger', 0.5)])
    st108 = PhoneState('hung')
    C(T(108), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, cord='out', phone=st108, ring=ring_fn(r, 0.0)),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern_afraid'), P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear')],
      acts=_AA(phone_rig('ruth', st108, pick=T(108) + 0.05), lambda A, s, sp: (A['narr14'].look_at(T(108), (A['ruth'], 'hand_r'), dur=0.3), [])[-1]),
      c=dict(mv='push', f=1.0, rate=0.012), sfx=[(T(108) + 0.6, 'phone_pickup', -4, 0, 'inside')])
    RUTH_EAR = _A(lambda a, s: a.receiver_to_ear(-1.0, None, 1, fade=0.01), lambda a, s: a.hold_prop('receiver', 1, -1.0, None))
    C(T(109), 'bust', who='ruth', bg=('kitchen', 'phone', K_PHONE_TWO), set=dict(KIT, cord='out', phone='off'), cx=900, cy=610, scale=0.88, turn=0.5, h_turn=0.15,
      expr='stern_afraid', light=NIGHT_L, act=_A(RUTH_EAR, lookxy(1500, 520, T(109), None, 0.4, z=300.0), blinks(T(110) + 0.3)),
      acts=lambda A, s, sp: [notes_layer((1240, 520), WD(110, 'music'), None, rate=1.4, size=40.0, depth=0.9)],
      music=[(WD(110, 'music'), 'hold', 0.55, 12.0, dict(version='receiver_close'))])
    C(T(112), 'set', room='kitchen', view='phone', cam=K_PHONE_TWO, set=dict(KIT, cord='out', phone='off'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern_afraid'), P('narr14', NARR_PHONE, face=AT_PHONE, expr='fear',
                                                                     act=lambda a, s: a.set(-9, None, 0.1, lean=0.12, h_tilt=-8.0))],
      acts=_AA(phone_rig('ruth', None, held=True), lambda A, s, sp: [notes_layer(lambda tt: A['ruth'].where(tt, 'head'), T(112), None, rate=1.0, size=30.0, slow=1.8)]),
      c=dict(mv='push', f=1.0, rate=0.012))
    C(W(112, 'so', 1), 'bust', who='narr14', bg=('kitchen', 'phone', K_PHONE_TWO), set=dict(KIT, cord='out', phone='off'), cx=1000, cy=620, scale=0.88, turn=-0.45,
      h_turn=-0.15, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(560, 560, W(112, 'so', 1), None, 0.4, z=300.0), lambda a, s: a.set(W(112, 'so', 1) + 0.4, None, 1.2, lid_l=0.35, lid_r=0.35)))
    C(T(113), 'bust', who='narr14', bg=('kitchen', 'phone', K_PHONE_TWO), set=dict(KIT, cord='out', phone='off'), cx=920, cy=620, scale=0.92, turn=-0.5, h_turn=-0.25,
      expr='neutral', light=NIGHT_L, act=_A(lambda a, s: a.set(-9, None, 0.1, h_tilt=-12.0, lean=0.1), lookxy(400, 560, T(113), None, 0.3, z=250.0)))
    C(T(114), 'set', room='kitchen', view='phone', cam=K_PHONE_MED, set=dict(KIT, cord='out', phone='off'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern_afraid', act=blinks(T(115) + 0.2))], acts=phone_rig('ruth', None, held=True),
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(116), 'set', room='kitchen', view='phone', cam=K_PHONE_MED, set=dict(KIT, cord='out', phone='off'),
      ppl=[P('ruth', AT_PHONE, face=PHONE_PT, expr='stern_afraid')],
      acts=_AA(phone_rig('ruth', None, held=True), lambda A, s, sp: (A['ruth'].look_at(T(116) + 0.3, scr(sp, 'phone_hook'), t1=e(116) + 0.2, dur=0.4), [])[-1]),
      c=dict(mv='push', f=1.0, rate=0.012))
    # 117 she lays the receiver on the counter like a sleeping baby
    st117 = PhoneState('off')
    C(T(117), 'set', room='kitchen', view='phone', set=dict(KIT, cord='out', phone=st117),
      ppl=[P('ruth', (-1.62, 7.8, 0.0), face=(-1.5, 8.3), expr='grief_still')], acts=phone_rig('ruth', st117, held=True, counter=T(117) + 0.2),
      c=dict(mv='push', f=1.0, rate=0.012))
    C(W(117, 'like'), 'ins', name='phone_counter', kw=dict(music=1.0), c=dict(mv='push', rate=0.02))
    C(T(119), 'ins', name='clock', kw=lambda u: dict(time=(3, 5 + 10 * ease_in_out(clamp(u / 1.2)), 0), bg='kitchen'), c=dict(mv='push', rate=0.02))
    C(T(120), 'bust', who='narr14', bg=('kitchen', 'hall'), set=dict(KIT, cord='out', phone='counter'), cx=960, cy=620, scale=0.88, turn=0.3, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(1300, 560, T(120) + 0.2, None, 0.3, z=300.0), lambda a, s: a.turn(WD(120, 'coming') - 0.2, 0.85, 0.7),
             lookxy(1700, 520, WD(120, 'coming'), None, 0.5, z=300.0)))
    C(T(121), 'set', room='hall', view='back', set=dict(hall=0.0, kitchen=0.08), rim=DARK, acts=notes_at((960, 600), T(121), None, rate=1.0, size=24.0, rise=-90.0, slow=1.6),
      c=dict(mv='push', f=1.0, rate=0.02))
    C(T(122), 'set', room='living', view='wide', set=dict(lamp=0.0), rim=DARK, acts=notes_at((900, 560), T(122) - 0.5, None, rate=1.2, size=24.0, slow=1.6),
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(123), 'set', room='living', view='chair', set=dict(lamp=0.0), rim=DARK, acts=notes_at('armchair', T(123) - 0.6, None, rate=1.6, size=34.0, slow=1.5),
      c=dict(mv='push', f=1.0, rate=0.02))


# ==================================================================================================== RULE 3 (124-145)
def plan_rule3(F):
    t, e, C = F.t, F.e, F.cut
    K3 = dict(KIT, cord='out', phone='counter')
    C(T(124), 'rule', n=3)
    C(T(127), 'ins', name='clock', kw=dict(time=(3, 20, 0), bg='kitchen'), c=dict(mv='push', rate=0.03))
    C(W(127, 'Milo'), 'set', room='kitchen', view='hall', set=K3,
      ppl=[P('milo_sick', (-0.9, 6.45, 0.0), path=[(W(127, 'Milo') + 0.1, (-0.9, 6.45, 0.0)), (e(127) + 0.4, (-1.95, 6.7, 0.0))], expr='thirsty', surface='inside_quiet')],
      focus_on='milo_sick', c=dict(mv='push', f=1.0, rate=0.012))
    C(T(128), 'bust', who='milo_sick', bg=('kitchen', 'wide'), set=K3, cx=960, cy=560, scale=1.05, turn=0.15, expr='thirsty', light=NIGHT_L,
      act=_A(lookxy(1300, 380, T(128), None, 0.3, z=300.0), blinks(T(128) + 1.0)))
    C(T(129), 'bust', who='milo_sick', bg=('kitchen', 'wide'), set=K3, cx=1000, cy=640, scale=1.2, turn=0.25, expr='dazed', light=NIGHT_L,
      act=_A(lookxy(1400, 300, T(129), None, 0.3, z=300.0), lambda a, s: a.set(-9, None, 0.1, wide=0.4)))
    C(T(130), 'set', room='kitchen', view='wide', cam=K_MILO_SIDE, set=K3,
      ppl=[P('milo_sick', (-2.25, 7.25, 0.0), face=(-2.35, 7.95), expr='thirsty', act=_A(lambda a, s: a.hand_on(s.t0 - 0.5, 'belly', side=-1))),
           P('ruth', (-2.35, 7.95, 0.0), face=(-2.25, 7.25), expr='stern_afraid')],
      acts=lambda A, s, sp: (A['milo_sick'].look_at(s.t0, (A['ruth'], 'eyes'), dur=0.3), A['ruth'].look_at(s.t0, (A['milo_sick'], 'eyes'), dur=0.3), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(132), 'bust', who='milo_sick', bg=('kitchen', 'wide', K_MILO_SIDE), set=K3, cx=1000, cy=600, scale=1.0, turn=-0.4, h_turn=-0.1, expr='thirsty', light=NIGHT_L,
      act=_A(lookxy(560, 380, T(132), None, 0.3, z=300.0), lambda a, s: a.hand_on(s.t0 - 0.5, 'belly', side=-1)))
    C(T(134), 'set', room='kitchen', view='wide', cam=K_MILO_SIDE, set=K3,
      ppl=[P('milo_sick', (-2.25, 7.25, 0.0), face=(-2.35, 7.95), expr='thirsty', act=_A(lambda a, s: a.hand_on(s.t0 - 0.5, 'belly', side=-1))),
           P('ruth', (-2.35, 7.95, 0.0), face=(-2.25, 7.25), expr='stern_afraid')],
      acts=lambda A, s, sp: (A['milo_sick'].look_at(s.t0, (A['ruth'], 'eyes'), dur=0.3), A['ruth'].look_at(s.t0, (A['milo_sick'], 'eyes'), dur=0.3),
                             A['ruth'].hand_over(WD(134, 'clapped') - 0.15, 1, A['milo_sick'], 'mouth', dur=0.22),
                             A['milo_sick'].expr('fear', WD(134, 'clapped'), None, 0.2), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.012), sfx=[(WD(134, 'clapped') + 0.08, 'hand_slap_soft', -6, 0, 'inside')])
    C(T(135), 'bust', who='ruth', bg=('kitchen', 'wide', K_MILO_TWO), set=K3, cx=1000, cy=600, scale=0.88, turn=-0.3, h_turn=-0.1, expr='stern_afraid', light=NIGHT_L,
      act=_A(lookxy(560, 700, T(135), None, 0.3, z=200.0), lookxy(1500, 480, T(137) + 0.1, None, 0.5, z=300.0)))
    # 138 the pen click from the dark hallway
    C(T(138), 'set', room='kitchen', view='hall', set=K3, rim=DARK, c=dict(mv='push', f=1.0, rate=0.02))
    C(W(138, 'pen'), 'ins', name='pen', kw=dict(click=lambda u: 1.0 if 0.25 < u < 0.4 else 0.0), grade='dr_ins_wait', c=dict(mv='push', rate=0.03),
      sfx=[(W(138, 'pen') + 0.27, 'pen_click', 0, 0, 'close')], music=[(W(138, 'pen') + 0.27, 'hit', 0.6)])
    C(T(139), 'set', room='hall', view='back', set=dict(hall=0.0, kitchen=0.05), rim=DARK, c=dict(mv='push', f=1.0, rate=0.02),
      sfx=[(T(139) + 0.5, 'pen_scratch', -6, 0.2, 'inside', dict(dur=2.6))])
    C(T(140), 'bust', who='narr14', bg=('kitchen', 'hall'), set=K3, cx=760, cy=640, scale=0.8, turn=0.35, expr='neutral', light=NIGHT_L,
      act=lookxy(1500, 520, T(140), None, 0.3, z=300.0),
      busts=[dict(who='ruth', cx=1300, cy=600, scale=0.78, turn=0.2, expr='stern_afraid', light=NIGHT_L, depth=1.04,
                  act=lambda a, s: a.look_at(T(140) + 0.2, (1700, 520), dur=0.4, z=300.0))])
    C(T(141), 'bust', who='milo_sick', bg=('kitchen', 'wide'), set=K3, cx=960, cy=600, scale=1.0, turn=0.2, expr='dazed', light=NIGHT_L,
      act=_A(lambda a, s: a.set(WD(141, 'breathed') - 0.1, WD(141, 'breathed') + 1.0, 0.3, m_open=0.25), blinks(T(141) + 2.0)))
    C(T(142), 'bust', who='narr14', bg=('kitchen', 'wide'), set=K3, cx=980, cy=620, scale=0.9, turn=-0.3, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(500, 640, T(142), None, 0.3, z=250.0), lambda a, s: a.set(T(142) + 0.1, T(143) + 1.4, 0.3, brow_in=0.4, nose=0.5)))
    C(T(144), 'bust', who='narr14', bg=('kitchen', 'wide'), set=K3, cx=1120, cy=630, scale=0.84, turn=-0.5, h_turn=-0.2, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(400, 720, T(144), None, 0.5, z=250.0), lambda a, s: a.set(T(144) + 0.3, None, 0.6, brow_sad=0.4)))
    C(T(145), 'set', room='office', view='desk', set=dict(owner='halverson'), rim=OFFICE,
      ppl=[P('halverson', 'desk_chair', expr='focused', stand_t=T(145) + 0.6,
             act=_A(lambda a, s: a.look_at(s.t0, scr(s.sp, 'results'), dur=0.3)))],
      c=dict(OFFICE_C, f=1.5, y=400))


# ==================================================================================================== RULE 4 (146-191)
def plan_rule4(F):
    t, e, C = F.t, F.e, F.cut
    K4 = dict(KIT, cord='out', phone='counter')
    HALLN = dict(hall=0.0, porch=1.0, kitchen=0.08, headlights=0.6)
    FRONT = dict(rain=1.0, car=True, headlights=1.0)
    C(T(146), 'rule', n=4)
    C(T(149), 'ins', name='clock', kw=dict(time=(3, 40, 0), bg='kitchen'), c=dict(mv='push', rate=0.03))
    kn = [WD(149, 'knocked') + 0.05 + 0.34 * k for k in range(3)]
    C(W(149, 'someone'), 'set', room='hall', view='door', cam=HALL_KNOCK, set=HALLN, rim=PORCH, c=dict(mv='push', f=1.0, rate=0.015, hit=kn),
      tags=[(k_, 'KNOCK', 960 + (j - 1) * 260, 420 + 40 * j, 'white', 0.8) for j, k_ in enumerate(kn)],
      sfx=[(k_, 'knock_door', 0, 0, 'inside', dict(n=1, index=j)) for j, k_ in enumerate(kn)])
    C(T(150), 'set', room='hall', view='door', set=HALLN, rim=PORCH,
      ppl=[P('narr14', 'hall_mid', path=[(T(150), (-0.4, 1.6, 0.0)), (T(150) + 1.0, 'peephole_eye')], expr='fear', surface='inside_quiet',
             act=_A(lambda a, s: a.head_to(T(150) + 1.0, scr(s.sp, 'peephole'), 'eyes', dur=0.6, max_lean=0.2),
                    lambda a, s: a.reach_to(T(150) + 0.9, 1, scr(s.sp, 'peephole', -60, 70), dur=0.5, contact='palm', shape='flat', z=-60.0)))],
      c=dict(mv='push', f=1.0, rate=0.015), sfx=[(T(150) + 1.2, 'peephole_cover', -8, 0, 'inside')])
    C(W(150, 'woman'), 'set', room='front', view='peephole', set=FRONT, rim=PORCH,
      ppl=[P('halverson_rain', 'porch_step', path=[(W(150, 'woman') + 0.3, 'porch_step'), (T(151) - 0.1, (-0.4, -1.3, 0.0))], face=(-0.38, 0.0), expr='pleading', surface='porch')],
      c=dict(mv='hold'))
    C(T(151), 'set', room='front', view='porch', cam=PORCH_MED, set=FRONT, rim=RAIN,
      ppl=[P('halverson_rain', (-0.4, -1.3, 0.0), path=[(T(151), (-0.4, -1.3, 0.0)), (T(151) + 0.9, 'porch_door')], face=(-0.4, 0.2), expr='pleading', surface='porch',
             act=blinks(T(151) + 1.4))], c=dict(mv='push', f=1.0, rate=0.015))
    C(T(152), 'bust', who='halverson_rain', bg=('front', 'porch', PORCH_MED), set=FRONT, cx=960, cy=600, scale=0.88, turn=0.3, h_turn=0.1, expr='pleading',
      light=RAIN, act=_A(lookxy(1300, 520, T(152), None, 0.3, z=300.0), blinks(T(152) + 0.8)))
    C(T(153), 'ins', name='badge', kw=dict(wet=1.0), c=dict(mv='push', rate=0.025))
    C(T(154), 'set', room='front', view='driveway', set=FRONT, rim=RAIN, c=dict(mv='push', f=1.0, rate=0.015))
    C(T(155), 'set', room='front', view='peephole', set=FRONT, rim=PORCH,
      ppl=[P('halverson_rain', 'porch_step', face=(-0.38, 0.0), expr='pleading', act=lambda a, s: a.knock(T(155) - 0.6, n=2, spacing=0.32, side=0.0))],
      c=dict(mv='hold'))
    C(T(158), 'bust', who='halverson_rain', bg=('front', 'porch', PORCH_MED), set=FRONT, cx=1000, cy=610, scale=0.9, turn=0.25, h_turn=0.1, expr='pleading',
      light=RAIN, act=_A(lookxy(1250, 480, T(158), None, 0.3, z=300.0), blinks(e(158) + 0.1)),
      tags=[(WD(158, 'six'), 'BLOOD SUGAR: 612', 560, 360, 'red', 3.2)])
    C(T(160), 'set', room='front', view='porch', cam=PORCH_MED, set=FRONT, rim=RAIN,
      ppl=[P('halverson_rain', 'porch_door', face=(-0.4, 0.2), expr='pleading',
             act=_A(lambda a, s: a.reach_to(T(160) + 0.1, 1, scr(s.sp, 'porch_knock', 40, 40), dur=0.5, contact='palm', shape='flat', z=0.0)))],
      c=dict(mv='push', f=1.0, rate=0.015))
    C(T(161), 'bust', who='halverson_rain', bg=('front', 'porch', PORCH_MED), set=FRONT, cx=960, cy=600, scale=0.96, turn=0.2, expr='set_jaw', light=RAIN,
      act=lookxy(1250, 480, T(161), None, 0.3, z=300.0))
    C(T(162), 'bust', who='ruth', bg=('hall', 'back'), set=dict(hall=0.0, kitchen=0.08), cx=960, cy=610, scale=0.88, turn=0.1, expr='stern_afraid', light=PORCH,
      act=_A(lookxy(960, 560, T(162) - 0.2, None, 0.3, z=500.0), ex('set_jaw', T(162) + 0.3, None, 0.5), blinks(e(163) - 0.3)))
    C(T(164), 'bust', who='halverson_rain', bg=('front', 'porch', PORCH_MED), set=FRONT, cx=1000, cy=600, scale=0.9, turn=0.3, h_turn=0.1, expr='exhausted',
      light=RAIN, act=_A(lookxy(1250, 480, T(164), None, 0.3, z=300.0), ex('fierce_kind', T(166), None, 0.5)))
    C(T(167), 'set', room='hall', view='door', cam=HALL_DOOR_MED, set=HALLN, rim=PORCH,
      ppl=[P('ruth', 'door_inside', face=(-0.4, 0.0), expr='stern_afraid',
             act=_A(lambda a, s: a.reach_to(-1.0, 1, scr(s.sp, 'deadbolt'), dur=0.01, contact='grip', shape='pinch', z=0.0))),
           P('narr14', (0.12, 1.9, 0.0), face=(-0.4, 0.5), expr='fear')],
      acts=lambda A, s, sp: (A['narr14'].look_at(s.t0, (A['ruth'], 'head'), dur=0.3), [])[-1], c=dict(mv='push', f=1.0, rate=0.012))
    # 168-178 the paper under the door: the results, the marker note, every warning sign legible as it is read
    C(T(168), 'ins', name='results', kw=lambda u: dict(show=8, slide=ease_out_cubic(clamp(u / 1.5)), bg='floor'), c=dict(mv='hold'),
      sfx=[(T(168) + 0.1, 'paper_slide', -2, 0, 'inside')])
    C(T(169), 'ins', name='results', kw=dict(show=0, slide=1.0, bg='hand'), c=dict(mv='push', rate=0.02))
    sign_t = [WD(171 + k, F.L[171 + k]['en'].split()[0].lower().strip('.,')) for k in range(6)] + [WD(177, 'if'), WD(178, "i'll")]
    C(T(170), 'ins', name='note', kw=lambda u, st_=sign_t, t0_=T(170): dict(show=sum(1 for x in st_ if u + t0_ >= x - 0.15)),
      motion=lambda u: (120.0, 260.0, 0.0, 0.0), c=dict(mv='push', rate=0.012),
      sfx=[(T(170) + 0.3, 'paper_rustle', -10, 0, 'close')])
    C(T(174), 'ins', name='note', kw=lambda u, st_=sign_t, t0_=T(174): dict(show=sum(1 for x in st_ if u + t0_ >= x - 0.15)),
      motion=lambda u: (80.0, 140.0, 0.05, 0.0), c=dict(mv='push', rate=0.012))
    C(T(177), 'ins', name='note', kw=lambda u, st_=sign_t, t0_=T(177): dict(show=sum(1 for x in st_ if u + t0_ >= x - 0.15)),
      motion=lambda u: (0.0, -260.0, 0.2, 0.0), c=dict(mv='push', rate=0.012))
    # 179 Grandma burns it in the sink
    def burn_acts(A, s, sp):
        a = A['ruth']
        ts_ = a.strike_match(T(179) + 0.1, side=1, dur=1.2)
        tsk = ts_[0] if isinstance(ts_, tuple) else ts_
        a.look_at(T(179) + 0.1, lambda tt: a.grip_point(tt, 1, 'match'), t1=T(179) + 1.3, dur=0.3)
        a.reach_to(T(179) + 1.4, 1, scr(sp, 'sink_bowl'), dur=0.8, contact='grip', shape='pinch', z=80.0, prop='match_lit')
        a.look_at(T(179) + 1.4, scr(sp, 'sink_bowl'), dur=0.4)
        return []
    C(T(179), 'set', room='kitchen', view='sink', set=dict(K4, fire=lambda tt: clamp((tt - T(179) - 2.2) / 0.6)), rim=FIRE,
      ppl=[P('ruth', (-3.3, 8.55, 0.0), face=(-3.3, 9.6), expr='stern')], acts=burn_acts, c=dict(mv='push', f=1.0, rate=0.012))
    C(W(179, 'lit'), 'ins', name='burn', kw=lambda u: dict(burn=clamp((u - 0.3) / 3.0), match=1.0 - clamp((u - 1.5) / 0.6)), c=dict(mv='push', rate=0.02),
      sfx=[(W(179, 'lit') + 0.2, 'paper_burn', -4, 0, 'inside', dict(dur=4.0))])
    # 180-186 the window: Halverson in her car at 4 AM, nineteen hours awake, calling again and again
    LIVH = dict(lamp=0.0, headlights=1.0, rain=1.0, car=True)
    C(T(180), 'set', room='living', view='wide', set=LIVH, rim=HEADL,
      ppl=[P('narr14', 'door', path=[(T(180), 'door'), (e(180) + 0.6, (-2.6, 0.75, 0.0))], expr='fear', surface='inside_quiet')],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(181), 'set', room='living', view='window', set=LIVH, rim=HEADL, c=dict(mv='push', f=1.0, rate=0.015))
    HAL_CAR = _A(lambda a, s: a.phone_to_ear(-1.0, None, side=1), lambda a, s: a.hold_prop('cell', 1, -1.0, None))
    CARP = dict(speed=0.0, rain=1.0, dome=0.0)
    C(T(182), 'set', room='car', view='front', set=CARP, rim=DASH,
      ppl=[P('halverson_rain', 'driver', expr='exhausted', act=_A(HAL_CAR, blinks(T(182) + 1.3)))], tags=[(T(182) + 0.3, '4:00 AM', 1500, 300, 'white', 2.0)],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(W(182, 'nineteen'), 'bust', who='halverson_rain', bg=('car', 'front'), set=CARP, cx=980, cy=610, scale=0.86, turn=0.35, h_turn=0.1, expr='exhausted',
      light=DASH, act=_A(HAL_CAR, lambda a, s: a.set(-9, None, 0.1, lid_l=0.4, lid_r=0.4), blinks(W(182, 'nineteen') + 1.0)),
      tags=[(WD(182, 'nineteen'), '19 HOURS AWAKE', 600, 360, 'white', 2.0)])
    C(T(183), 'set', room='car', view='driver', set=CARP, rim=DASH,
      ppl=[P('halverson_rain', 'driver', expr='exhausted', act=HAL_CAR)], c=dict(mv='push', f=1.0, rate=0.012))
    C(T(184), 'bust', who='halverson_rain', bg=('car', 'front'), set=CARP, cx=1000, cy=610, scale=0.9, turn=0.4, h_turn=0.1, expr='pleading', light=DASH,
      act=_A(HAL_CAR, blinks(T(184) + 0.9)),
      tags=[(T(184) + 0.2, 'CALLING...', 560, 360, 'pill', 0.9), (WD(184, 'again', 1), 'CALLING...', 600, 420, 'pill', 0.9)])
    C(T(185), 'set', room='front', view='driveway', set=FRONT, rim=RAIN, c=dict(mv='push', f=1.0, rate=0.012))
    C(T(186), 'set', room='living', view='wide', set=LIVH, rim=HEADL,
      ppl=[P('narr14', (-2.6, 0.75, 0.0), face=(-2.6, -2.0), expr='fear')], c=dict(mv='push', f=1.15, rate=0.012))
    # 187-191 the bus stop: someone very tall, folded up, knees above his head. Waiting.
    C(T(187), 'set', room='front', view='street', set=FRONT, rim=RAIN, c=dict(mv='push', f=1.0, rate=0.012))
    C(W(187, 'bus'), 'set', room='living', view='window_bus', set=LIVH, rim=HEADL, c=dict(mv='push', f=1.0, rate=0.01))
    C(W(187, 'someone'), 'set', room='front', view='bus', set=FRONT, rim=RAIN,
      ppl=[P('later', 'bus_bench', knee=1.1, act=_A(pose(-9, None, 0.1, h_tilt=-10.0)))], c=dict(mv='push', f=1.0, rate=0.012),
      music=[(WD(187, 'someone'), 'stinger', 0.55)])
    C(T(188), 'set', room='front', view='bus', cam=BUS_MED, set=FRONT, rim=RAIN,
      ppl=[P('later', 'bus_bench', knee=1.15, act=_A(pose(-9, None, 0.1, h_tilt=-8.0), lambda a, s: a.click_pen([T(190) + 0.4])))],
      c=dict(mv='push', f=1.0, rate=0.012))
    C(T(191), 'set', room='front', view='bus_far', set=FRONT, rim=RAIN, ppl=[P('later', 'bus_bench', knee=1.1)], c=dict(mv='push', f=1.0, rate=0.01))


# ==================================================================================================== RULE 5 (192-212)
def plan_rule5(F):
    t, e, C = F.t, F.e, F.cut
    K5 = dict(KIT, cord='out', phone='counter', fire=1.0)
    RUTH_ROCK = lambda t1=None: (lambda a, s: a.rock(s.t0 - 1.0, t1, 1.0, 0.45))
    MILO_LAP = lambda: _A(lambda a, s: a.rock(s.t0 - 1.0, None, 0.8, 0.45, hum=False), lambda a, s: a.breathe_fast(s.t0 - 1.0, None, 0.95),
                          pose(-9, None, 0.1, lean=-0.18, h_tilt=-8.0))
    MILO_AT = (-2.45, 8.15, 0.0)
    C(T(192), 'rule', n=5)
    C(T(195), 'ins', name='clock', kw=dict(time=(4, 10, 0), bg='kitchen'), c=dict(mv='push', rate=0.03))
    C(W(195, 'Milo'), 'set', room='kitchen', view='floor', cam=K_FLOOR_MED, set=K5,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='stern_afraid', act=RUTH_ROCK()), P('milo_sick', MILO_AT, kind='floor', face=FLOOR_FACE, expr='dazed', act=MILO_LAP())],
      acts=lambda A, s, sp: (A['ruth'].look_at(s.t0, (A['milo_sick'], 'head'), dur=0.3), [])[-1], c=dict(mv='push', f=1.4, x=900, y=560, rate=0.012))
    C(T(196), 'bust', who='milo_sick', bg=('kitchen', 'floor'), set=K5, cx=960, cy=600, scale=1.0, turn=0.3, expr='dazed', light=NIGHT_L,
      act=_A(lambda a, s: a.breathe_fast(s.t0 - 1.0, None, 1.0), lambda a, s: a.set(T(198), None, 0.8, lid_l=1.0, lid_r=1.0, h_tilt=-10.0)))
    C(T(199), 'set', room='kitchen', view='wide', cam=K_FLOOR_MED, set=K5,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='stern_afraid', act=RUTH_ROCK()), P('milo_sick', MILO_AT, kind='floor', face=FLOOR_FACE, expr='dazed', act=MILO_LAP())],
      acts=_AA(notes_at('receiver_counter', T(199) - 1.0, None, slow=1.6, size=22.0)), c=dict(mv='push', f=1.4, x=900, y=560, rate=0.012))
    C(T(200), 'bust', who='milo_sick', bg=('kitchen', 'floor'), set=K5, cx=1000, cy=620, scale=1.05, turn=-0.35, h_turn=-0.15, expr='dazed', light=NIGHT_L,
      act=_A(lambda a, s: a.breathe_fast(s.t0 - 1.0, None, 1.0), lookxy(500, 600, WD(200, 'looked'), None, 0.6, z=250.0),
             lambda a, s: a.set(WD(200, 'asked'), None, 0.6, brow_in=0.4)))
    C(T(201), 'set', room='kitchen', view='floor', cam=K_FLOOR_MED, set=K5,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='grief_still', act=_A(RUTH_ROCK(), lambda a, s: a.hand_on(e(201) - 0.6, 'chest', side=-1, t1=e(201) + 0.4))),
           P('milo_sick', MILO_AT, kind='floor', face=FLOOR_FACE, expr='dazed', act=MILO_LAP())],
      acts=lambda A, s, sp: (A['ruth'].look_at(s.t0, (A['milo_sick'], 'head'), dur=0.3), [])[-1], c=dict(mv='push', f=1.4, x=900, y=560, rate=0.012),
      music=[(T(201), 'hold', 0.5, 9.0, dict(version='hummed'))])
    C(T(202), 'bust', who='ruth', bg=('kitchen', 'floor', K_FLOOR_MED), set=K5, cx=960, cy=620, scale=0.9, turn=-0.25, expr='grief_still', light=NIGHT_L,
      act=_A(lambda a, s: a.rock(s.t0 - 1.0, None, 0.6, 0.45, hum=False), lookxy(760, 820, T(202), None, 0.4, z=200.0)))
    C(T(205), 'bust', who='ruth', bg=('kitchen', 'floor', K_FLOOR_MED), set=K5, cx=900, cy=640, scale=0.9, turn=0.3, h_turn=0.1, expr='grief_still', light=NIGHT_L,
      act=_A(lambda a, s: a.rock(s.t0 - 1.0, None, 0.6, 0.45, hum=False), lookxy(760, 820, T(205) - 0.2, None, 0.3, z=200.0),
             lookxy(1500, 330, WD(205, 'grandma') + 0.15, None, 0.5, z=300.0)))
    C(T(206), 'bust', who='ruth', bg=('kitchen', 'floor', K_FLOOR_MED), set=K5, cx=1000, cy=620, scale=0.92, turn=-0.4, h_turn=-0.1, expr='grief_still', light=NIGHT_L,
      act=_A(lambda a, s: a.rock(s.t0 - 1.0, None, 0.6, 0.45, hum=False), lookxy(560, 560, T(206), None, 0.4, z=250.0), ex('stern_afraid', WD(206, '1979'), None, 0.6)))
    C(T(207), 'set', room='kitchen', view='floor', cam=K_FLOOR_MED, set=K5,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='stern_afraid', act=_A(RUTH_ROCK(WD(207, 'stopped') + 0.2), lambda a, s: a.hand_on(T(207) + 0.6, 'chest', side=-1, t1=e(207) + 0.6))),
           P('milo_sick', MILO_AT, kind='floor', face=FLOOR_FACE, expr='dazed', act=_A(lambda a, s: a.rock(s.t0 - 1.0, WD(207, 'stopped') + 0.2, 0.8, 0.45, hum=False),
                                                                                     lambda a, s: a.breathe_fast(s.t0 - 1.0, None, 0.95), pose(-9, None, 0.1, lean=-0.18, h_tilt=-8.0))),
           ],
      acts=lambda A, s, sp: (A['ruth'].look_at(s.t0, (1500, 330), dur=0.5, z=300.0), [])[-1], c=dict(mv='push', f=1.4, x=900, y=560, rate=0.012))
    C(T(208), 'bust', who='ruth', bg=('kitchen', 'floor', K_FLOOR_MED), set=K5, cx=980, cy=610, scale=0.95, turn=-0.4, h_turn=-0.15, expr='fear', light=NIGHT_L,
      act=lookxy(560, 560, T(208), None, 0.4, z=250.0))
    C(T(209), 'bust', who='narr14', bg=('kitchen', 'floor', K_FLOOR_MED), set=K5, cx=940, cy=620, scale=0.9, turn=0.3, expr='neutral', light=NIGHT_L,
      act=_A(lookxy(1300, 600, T(209), None, 0.4, z=250.0), lambda a, s: a.turn(WD(209, 'hear'), 0.8, 0.8), lookxy(1750, 480, WD(209, 'hear'), None, 0.7, z=300.0),
             lambda a, s: a.set(WD(209, 'hear'), None, 0.8, h_tilt=-8.0)))
    C(T(211), 'ins', name='phone_counter', kw=dict(music=1.0), c=dict(mv='push', rate=0.025))
    C(W(211, 'every'), 'set', room='hall', view='back', set=dict(hall=0.0, kitchen=0.08), rim=DARK, acts=notes_at((960, 600), W(211, 'every'), None, size=22.0, slow=1.8),
      c=dict(mv='push', f=1.0, rate=0.02))
    C(W(211, 'soft'), 'set', room='living', view='chair', set=dict(lamp=0.0), rim=DARK, acts=notes_at('armchair', W(211, 'soft') - 0.5, None, size=30.0, slow=1.8),
      c=dict(mv='push', f=1.0, rate=0.02))
    C(T(212), 'set', room='kitchen', view='wide', cam=K_FLOOR_MED, set=K5,
      ppl=[P('ruth', RUTH_FLOOR, kind='floor', face=FLOOR_FACE, expr='fear'), P('milo_sick', MILO_AT, kind='floor', face=FLOOR_FACE, expr='dazed', act=MILO_LAP())],
      acts=lambda A, s, sp: (A['ruth'].look_at(s.t0 + 0.1, (1500, 380), dur=0.6, z=300.0), [])[-1],
      c=dict(mv='push', f=1.0, rate=0.015), music=[(T(212), 'hit', 0.7)])


# ==================================================================================================== PART B (213-455): placeholders, one set view per scene
PARTB_SCENES = [  # (line, kind, params): part B rebuilds these as real shots following W/shotmap.md
    (213, 'rule', dict(n=6)), (215, 'set', dict(room='living', view='door', set=dict(lamp=0.0))),
    (216, 'set', dict(room='hall', view='livdoor', set=dict(living_state='wait', door=95.0))), (217, 'set', dict(room='living', view='wide', set=dict(state='wait'))),
    (222, 'ins', dict(name='sign')), (224, 'set', dict(room='living', view='front', set=dict(state='wait'))),
    (233, 'set', dict(room='living', view='grandpa', set=dict(state='wait'))), (235, 'set', dict(room='living', view='him', set=dict(state='wait'))),
    (241, 'bust', dict(who='later', bg=('living', 'him'), set=dict(state='wait'), cx=960, cy=700, scale=0.6, light=WAITR)), (243, 'ins', dict(name='clipboard')), (245, 'set', dict(room='living', view='machine', set=dict(state='wait'))),
    (247, 'ins', dict(name='ticket', kw=dict(text='MILO'))), (252, 'rule', dict(n=7)), (255, 'ins', dict(name='wrist')),
    (261, 'ins', dict(name='clock', kw=dict(time=(4, 21, 0), slow=1.0))), (262, 'set', dict(room='living', view='wide', set=dict(state='wait'))),
    (276, 'bust', dict(who='later', bg=('living', 'him'), set=dict(state='wait'), cx=960, cy=640, scale=0.5, light=WAITR)), (280, 'set', dict(room='living', view='him', set=dict(state='wait'))),
    (296, 'set', dict(room='bath', view='cabinet', set=dict(cabinet=1.0, card=False))), (297, 'ins', dict(name='card_back')),
    (299, 'set', dict(room='kitchen', view='phone', set=dict(era='1979'), era='1979')), (303, 'set', dict(room='kitchen', view='floor', set=dict(phone='counter', cord='out'))),
    (306, 'set', dict(room='hall', view='door', set=dict(front_door=90.0, headlights=1.0))), (307, 'set', dict(room='front', view='porch', set=dict(rain=1.0, car=True, headlights=1.0))),
    (308, 'set', dict(room='car', view='back')), (319, 'set', dict(room='car', view='driver')), (331, 'set', dict(room='car', view='mirror')),
    (332, 'set', dict(room='car', view='back', set=dict(dome=0.4))), (340, 'set', dict(room='er_wait', view='wide')), (347, 'set', dict(room='car', view='windshield')),
    (348, 'set', dict(room='er', view='doors', set=dict(doors=1.0))), (349, 'set', dict(room='er', view='ext', set=dict(doors=1.0))),
    (350, 'set', dict(room='er_bay', view='bay')), (354, 'set', dict(room='er_bay', view='monitor')), (356, 'set', dict(room='er_wait', view='wide')),
    (359, 'set', dict(room='er_wait', view='chairs', set=dict(rock=6.0))), (362, 'set', dict(room='run', view='side')), (364, 'ins', dict(name='glucose')),
    (365, 'set', dict(room='living', view='sunrise', set=dict(tod='sunrise'))), (367, 'ins', dict(name='ticket', kw=dict(text='RUTH', bg='dawn'))),
    (371, 'set', dict(room='kitchen', view='phone', set=dict(tod='sunrise'))), (375, 'set', dict(room='cardio', view='ruth')),
    (378, 'ins', dict(name='burn', kw=dict(burn=0.6, match=0.0))), (379, 'set', dict(room='office', view='desk', set=dict(owner='narrator'))),
    (397, 'set', dict(room='hosp_hall', view='hall')), (398, 'set', dict(room='hosp_hall', view='chair')), (401, 'set', dict(room='outro', view='table', set=dict(lamp=0.0), era='outro')),
    (403, 'set', dict(room='outro', view='table', set=dict(lamp=1.0), era='outro')), (405, 'set', dict(room='bath', view='cabinet', set=dict(cabinet=1.0, card=False, cab_empty=True))),
    (407, 'set', dict(room='outro', view='wide', era='outro')), (408, 'card', dict(text="IT'S PROBABLY NOTHING.\nIT CAN WAIT.", era='outro')),
    (416, 'ins', dict(name='advice', kw=dict(show=5), era='outro')), (430, 'set', dict(room='er_bay', view='side', era='outro')),
    (434, 'card', dict(text='ASK', sub='write the first name of a doctor or nurse who helped you', era='outro')),
    (447, 'set', dict(room='outro', view='phone', era='outro')), (449, 'card', dict(text='SUBSCRIBE', sub=CHANNEL, era='outro')),
    (452, 'card', dict(text='NEXT TIME', sub="if the school bus stops outside your house at midnight... don't get on.", era='outro')),
    (453, 'set', dict(room='outro', view='phone', era='outro')), (455, 'card', dict(text=CHANNEL, era='outro'))]


def plan_partb(F):
    for (i, kind, p) in PARTB_SCENES:
        p = dict(p)
        if kind == 'set':
            p.setdefault('c', dict(mv='push', f=1.0, rate=0.01))
            p.setdefault('rim', WAITR if (p.get('set') or {}).get('state') == 'wait' else ROOM_RIM.get(p['room']))
        p['placeholder'] = True
        F.cut(T(i), kind, **p)


def plan_globals(F):
    """Film-wide music cues keyed to lines: the HOLD MUSIC (the film's original returning tune) by version."""
    g = F.globals
    g.append({'t': round(T(117) + 1.5, 3), 'type': 'hold', 'level': 0.35, 'len': round(F.t(127) - T(117) - 1.5, 2), 'version': 'receiver_far', 'loop': True})
    g.append({'t': round(T(120), 3), 'type': 'hold', 'level': 0.4, 'len': round(F.t(124) - T(120), 2), 'version': 'every_room', 'loop': True})
    g.append({'t': round(T(127), 3), 'type': 'hold', 'level': 0.3, 'len': round(F.t(201) - T(127), 2), 'version': 'receiver_far_slow', 'loop': True})
    g.append({'t': round(T(211), 3), 'type': 'hold', 'level': 0.55, 'len': round(F.t(213) - T(211), 2), 'version': 'every_room_warped', 'loop': True})


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
