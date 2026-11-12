"""film.py: the shot list, editor and cue sheets for "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH".

Built the way the police film ("If A Police Officer Knocks At Midnight...", film_police_ref.py) and the delivery film
(film_delivery_ref.py) were: the same format, craft and pace, the same engine, cast system and set system, the police
header / rule cards / captions and global look with the red climax ramp, and cue sheets derived from the picture.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration 707.5 s + 3 s tail)
    F.shots                          # [Shot(t0, t1, kind, p)] ~270 shots, hard cuts (a few static / glitch / white flashes)
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json + shots.json (ARCHITECTURE contract)
    python3 film.py --list | --cues | --sheet PREFIX [--range a b] | --bench N | --frames PREFIX | --check

Shot kinds (builders B_<kind>; every set is one of sets.py's dummy-film builders, one floor plan for Grandpa's house):
  hall      the front hall from the front door down to the kitchen opening (gp_hall 'kitchen'): the bench with the black
            case, Grandpa's coat, the grandfather clock (its hands run on the story clock), the kitchen light, Mister Winks in
            Grandpa's chair seen through the opening (winks=...), the knee-high flashlight beam coming down the hall (beam=)
  hdoor     the hall facing the front door (gp_hall 'door'): the family arriving at night, the museum man at 8 AM
  stairs    up the stairs (gp_hall 'stairs'): Mister Winks three steps up with the flashlight in your face, the grab
  kitchen   the kitchen (gp_kitchen 'table' | 'chair'): him in Grandpa's chair, the steaming mug, Mom smelling it, the joke,
            the glove, standing on the chair, the flicker, the empty chair; tod='morning' for the new Owen's coffee
  living    the living room (gp_living 'tv' = from the couch: the CRT and the kitchen doorway with his chair | 'couch' = the
            couch under the lamp and the bookcase): the family on the couch, the TV turning on (the 1974 tape plays live on
            the CRT with Walter and the dummy drawn by the cast), him on top of the bookcase
  den       Grandpa's den (gp_den): Owen in the armchair with the dummy on his knee, Mom pulling, you kneeling, the lamp
            going out, the dummy face down on the rug
  studio    "Saturday Morning with Walter Kemp", 1974, full frame through the VHS / CRT look (gp_studio): young Walter with
            the dummy on his knee (draw_lap), the audience shaking with laughter waves, the dummy turning to the camera
  hospital  the hospital room last week (hospital): Grandpa in bed with the dummy on his lap, the real Walter's grab, the ECG
  stage62   the Palace, 1962 (stage_1962, sepia): the first show, "Say goodnight, Mister Winks"
  museum    the museum vitrine (museum): Mister Winks behind glass trying to wink
  street    8 AM (street_morning): the new Owen waving at the window as the museum van pulls away
  bedroom   your bedroom months later (bedroom_doorway): the new Owen in the backlit doorway
  bust      face close-ups over a blurred, darkened set (framings rotate: BUST_FRAMES); ghost= puts a figure in the blurred
            set behind (the dummy on the bookcase behind Mom)
  lap       a person with the dummy on the knee, large, over a blurred set (draw_lap): Owen in the den, Grandpa in bed, Walter
  carry     you holding the dummy in your arms, large (draw_carry): "In my arms, Mister Winks opens his eyes"
  portrait  Mister Winks full figure, large, one camera move over him (the cold open's description: hair, freckles, jacket,
            the flashlight clicking on in one white glove)
  hands     hand close-ups (Grandpa's three squeezes, the wrist grab, Mom's hand finding yours, catching Mom's wrist)
  ins       prop inserts (sets.gp_insert: letter, letter_close, envelope, ps, latches, case_open, mug, back_slot, squeeze,
            family_photo, poster_1962, vcr)
  rule      the police rule card over a blurred live scene (these 7 rules); recall=True cards (rule two's false 'LIE?',
            rule six torn by the lie) do not change the header
  black     the hard cut to black after the last line

Plan conventions (plan() at the end of the file, as in the police and delivery films): F.cut(t, kind, **p) starts a shot;
it ends at the next cut. Times come from the timeline (F.t(i) line start, F.e(i) line end, F.w(i, 'word') ASR word start
inside line i). Common p keys: cam=dict(mv='push'|'fast'|'creep'|'pull'|'drift'|'move'|'hand'|'keys', x, y, z, rate, x1,
y1, z1, snap=(t, k), hit=[t], opt=k, d=depth, keys=[(t, x, y, z[, ease[, f]])] (KeyCam: z = dolly <= 1.3 on the 2.5D
interiors, f = optical zoom)); ppl=[P(who, at=anchor | (x, y, depth, h) | ('h', x, y[, Y]) (a point on the house plan),
act=f(acting, shot), path=...)]; winks=dict(at=..., act=..., torch=...) (Mister Winks on the set); tags=[(t, text, x, y,
style, hold)]; sfx=[(t, name, gain_db, pan, space, params)]; music=[(t, type, level, len)]; cut='static'|'glitch'|'white'
(quiet_cut=True: no impact on it); post={...}; post_fn=f(t)->{...}.
Speech: every actor talks only on its own lines (VOICE: mom M, owen / owen_new O, grandpa / walter G 'memory', Mister
Winks K, G 'dummy', U 'dummy'; the tape's dummy R); narrator lines move no mouths. The dummy's hinged jaw drops and snaps
on each syllable of his lines (characters talk on 'winks'), and stays shut otherwise: the jaw actions the narration
describes (hanging open 254 s, the slow close and clack 257.8 s, 'jaw going up and down' on the bookcase 423 s, the
clacks) are explicit clips. The tape dummy's jaw follows the TV's own voice (tv_voice: a replay of his joke from the
recording, played low through the TV under the narration at 440-445 s: the cue sheet carries it as 'tv_voice' with the
source span), so young Walter's unmoving lips read against a talking dummy.
Global look (glob_fx): per-family exposure, the last 35 % creeping into red (from 460 s), a faster climax ramp from Mom's
scream (543.7 s) with a red heartbeat wash (engine.post.Spill) until Owen's eyes close, the reveal held dark, the 8 AM
and museum scenes clean, a last red creep in the doorway, scare flashes, fade in / out.
"""
import bisect, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *                                                    # noqa: F401,F403
from engine import hud as H
from engine import post as _epost
from engine.core import DW, DH, clamp, lerp, ease_in_out, ease_out_cubic, noise1, hash01, prog
import characters as CH
import sets as ST

W = os.path.join(HERE, '_work')                                         # this film's work dir (film/_work)
ALIGN = os.path.join(W, 'align')
CUES_DIR = os.path.join(W, 'cues')
TESTS = os.path.join(W, 'tests', 'film')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
GLOBAL_PPUSH = 0.02              # uniform post push (per second) added to every non-lens shot
DEEP_PPUSH = 0.022               # interiors (2.5D, lens): a gentle push into the finished image + a slow drift
DEEP_SETS = ('hall', 'hdoor', 'stairs', 'kitchen', 'living', 'den', 'hospital', 'museum', 'street', 'bedroom', 'stage62')
TITLE = "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"
H._hand = CH.hud_phone_hand

RULES = {1: "Keep him *in the case*.",
         2: "He *does voices*.",
         3: "*Don't laugh* at his jokes.",
         4: "Never put your *hand inside* him.",
         5: "If someone is talking and their *lips don't move*, it *isn't them* talking.",
         6: "If he's ever on someone's lap, *don't pull him off*.",
         7: "Never say *goodnight* to him."}

# who speaks which timeline lines (code, fx or None): narrator lines (N) move no mouths
VOICE = {'mom': [('M', None)], 'owen': [('O', None)], 'owen_new': [('O', None)], 'grandpa': [('G', 'memory')],
         'walter': [('G', 'memory')], 'winks': [('K', None), ('G', 'dummy'), ('U', 'dummy')]}
TAPE_VOICE = [('R', None)]                       # the dummy on the 1974 tape (the real Walter crying inside)
HEIGHT_M = {'winks': CH.DUMMY_M, 'you': 1.74, 'mom': 1.65, 'owen': 1.32, 'owen_new': 1.32, 'grandpa': 1.72, 'grandpa_bed': 1.72,
            'walter': 1.72, 'walter74': 1.78}

# ---------------------------------------------------------------- story beats (film seconds, from the timeline)
T_KIT_ON = 168.85                # the kitchen light comes on by itself ("You don't have to go looking.")
T_TV_ON = 294.98                 # the TV turns on by itself
T_FLICK = 324.08                 # the lamp flickers ... and goes out
T_BACK = 325.3                   # ... comes back on: the chair is empty
T_BEAM = 329.3                   # a little flashlight clicks on (knee high) at the kitchen end of the hall
T_3AM = 351.8                    # the flashlight comes back
T_GRAB = 359.05                  # you grab him on the stairs
T_SWAP = 567.06                  # "Owen's eyes close": from here the boy is owen_new
T_LAMP_OUT = (569.12, 570.38)    # the den lamp goes out ... and comes back on
T_JUMP = 573.2                   # Owen jumps up out of the armchair, the dummy falls face down on the rug
T_PICK = 598.6                   # you pick the dummy up off the rug
T_OPEN = 655.6                   # in your arms, Mister Winks opens his eyes
T_8AM = 665.13                   # 8 AM: the museum
T_MUSEUM = 677.38                # behind glass
T_HOME = 691.11                  # the boy who came home with us
CHAIR_UP = ('h', -0.95, 8.85, 0.74)   # Mister Winks in Grandpa's chair, sitting up on the red cushion (shoulders over the table)


def _hms(h, m, s=0): return h * 3600 + m * 60 + s


# the story clock (the header corner and the grandfather clock's hands): the night at Grandpa's house runs from the arrival
# (11:52 PM) through 1:15 ("At 1:15, Mom's voice calls from upstairs") and 3:00 ("At three in the morning") to the
# reveal; 8 AM for the museum van; the museum and the last night are later
CLOCK = [(0.0, 110.61, _hms(23, 47, 10), _hms(23, 48, 30)), (110.61, 218.35, _hms(23, 52), _hms(25, 15)),
         (218.35, 351.76, _hms(25, 15), _hms(26, 59, 50)), (351.76, 409.41, _hms(27, 0), _hms(27, 8, 40)),
         (409.41, 582.23, _hms(27, 9), _hms(27, 41)), (582.23, 665.13, _hms(27, 41), _hms(27, 58)),
         (665.13, 677.38, _hms(32, 0), _hms(32, 3)), (677.38, 693.79, _hms(14, 12), _hms(14, 13)),
         (693.79, 800.0, _hms(21, 41), _hms(21, 44))]


def story_clock(t):
    for a, b, s0, s1 in CLOCK:
        if a <= t < b: return s0 + (s1 - s0) * (t - a) / (b - a)
    return CLOCK[-1][3]


def clock_hm(t):
    s = int(story_clock(t)); h, m = (s // 3600) % 24, (s // 60) % 60
    return '%d:%02d %s' % ((h % 12) or 12, m, 'AM' if h < 12 else 'PM')


def clock_minutes(t):
    """The grandfather clock's hands: minutes past midnight (12 h dial)."""
    return (story_clock(t) / 60.0) % 1440.0


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
        self.spec = None
        self.actors = []

    @property
    def d(self): return self.t1 - self.t0

    def at(self, f): return self.t0 + f * self.d

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


# ==================================================================================================== light
def lvl(f, t):
    return float(f(t)) if callable(f) else float(f if f is not None else 1.0)


def house_light(level=1.0, rim='#ffcf8f', side=-1, base=0.12, cold=-0.35):
    """A cast light that follows a room's lamp level (sets' level f(t)): warm key and rim when lit, cold and dark when off."""
    def f(t):
        k = lvl(level, t)
        return dict(rim=rim if k > 0.2 else '#8fa6d8', rim_a=int(30 + 45 * k), side=side, key=lerp(cold, base, clamp(k)))
    return f


def tv_light(sp, base=None):
    """The TV's blue flicker on faces (gp_living's tv level), on top of the lamp."""
    tvf = sp.info.get('tv') if sp is not None and sp.info else None
    lf = sp.info.get('lamp') if sp is not None and sp.info else None

    def f(t):
        tv = ST.tv_level(tvf, t) if tvf is not None else 0.0
        lk = lvl(lf, t) if lf is not None else 0.0
        if tv > 0.05:
            return dict(rim='#9fd0ff', rim_a=int(50 + 110 * tv), side=1, key=lerp(-0.4, -0.05, clamp(tv)) + 0.1 * lk)
        return dict(rim='#ffcf8f' if lk > 0.2 else '#8fa6d8', rim_a=int(30 + 40 * lk), side=-1, key=lerp(-0.35, 0.1, clamp(lk)))
    return f


WARM = dict(rim='#ffcf8f', rim_a=60, side=-1, key=0.12)
NIGHT = dict(rim='#8fa6d8', rim_a=60, side=1, key=-0.25)
HOSP = dict(rim='#d8f0ea', rim_a=60, side=1, key=0.05)
MEMORY = dict(rim='#ffd9a0', rim_a=75, side=-1, key=0.25)
MORNING = dict(rim='#f4f2ec', rim_a=70, side=1, key=0.1)
TORCH = dict(under='#fff1c8', under_a=210, rim='#8fa6d8', rim_a=40, side=1, key=-0.3)
TAPE = dict(rim='#fff2c8', rim_a=70, side=-1, key=0.15)
MUSEUM = dict(rim='#fff0d8', rim_a=80, side=-1, key=0.05)
BACKLIT = dict(rim='#ffe0b0', rim_a=150, side=1, key=-0.55)


def as_fn(v):
    return v if callable(v) else (lambda t, v=v: v)


# ==================================================================================================== the film
class Film:
    def __init__(self, tl):
        self.tl = tl
        self.L = tl['lines']
        self.duration = float(tl.get('duration_en', 707.52)) + 3.0      # black after "He never will." for the end hit
        self.words = []
        if os.path.exists(WORDS):
            try:
                self.words = [(w.strip().lower().strip('.,?!;:"“”'), float(t)) for w, t in json.load(open(WORDS))['en_words']]
            except Exception:
                self.words = []
        self._wt = [t for _, t in self.words]
        self.shots = []
        self.globals = []                    # extra global cues (beds, music)
        self.tv_voices = []                  # [(t_at, src0, src1)] the tape's own voice (a replay from the recording)
        plan(self)
        self.shots.sort(key=lambda s: s.t0)
        for k, s in enumerate(self.shots):
            s.idx = k
            s.t1 = self.shots[k + 1].t0 if k + 1 < len(self.shots) else self.duration
        self._starts = [s.t0 for s in self.shots]
        assign_bust_framings(self)
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
        mv = (sh.p.get('cam') or {}).get('mv', 'push')
        if sh.p.get('handheld_hz') and isinstance(spec.cam, Cam): spec.cam.shake_hz = sh.p['handheld_hz']
        if sh.p.get('posts') and isinstance(spec.cam, Cam):            # chained pushes into the finished image
            for q in sh.p['posts']: spec.cam.post_push(q[0], q[1], q[2], q[3], q[6] if len(q) > 6 else 'push', x=q[4], y=q[5])
        if (spec.lens is None and isinstance(spec.cam, Cam) and not spec.cam.posts and mv not in ('pull', 'keys')
                and sh.kind not in ('rule', 'black') and not sh.p.get('no_ppush')):
            spec.cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + GLOBAL_PPUSH) ** max(0.3, sh.d), ease='push')
        elif (sh.kind in DEEP_SETS and isinstance(spec.cam, Cam) and not spec.cam.posts and mv not in ('pull', 'keys')
              and not sh.p.get('no_ppush')):
            # the 2.5D interiors are deep: a dolly of 2-3 %/s barely moves their far wall, so a uniform push into the image
            # with a slow lateral drift keeps every shot alive (offset stays inside the zoom's margin: no mirrored edges)
            sgn = 1 if sh.idx % 2 else -1
            z1 = (1.0 + DEEP_PPUSH) ** max(0.3, sh.d)
            spec.cam.post_push(sh.t0, sh.t1, 1.0, z1, ease='push', x=sgn * 6.0 * sh.d, y=-2.0 * sh.d)
        if len(self._built) > 3: self._built.clear()
        self._built[sh.idx] = spec
        return spec

    # ---------------------------------------------------------------- frame
    def frame(self, t, i, bg='#000000'):
        sh = self.shot_at(t)
        spec = self._build(sh)
        fx = spec.fx(t) if spec.fx else {}
        fx = dict(fx or {})
        glob_fx(self, sh, t, fx)
        cs = spec.cam.at(t) if spec.cam is not None else None
        if cs is not None: cs = safe_post(cs)

        def hud_all(cv, tt):
            if spec.hud: spec.hud(cv, tt)
            self.overlay(cv, tt, sh)
        return render_frame(spec.layers, cs, t, i, focus=spec.focus, dof=spec.dof, lens=spec.lens, grade=spec.grade, post=fx,
                            hud=hud_all, bg=bg)

    # ---------------------------------------------------------------- captions + header (police / v1 logic)
    def header_text(self, t):
        cur = 'INTRODUCTION'
        for t0, n in self.rules:
            if t >= t0: cur = 'RULE %d OF 7' % n
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
            if cur.endswith((',', '.', '?', '!')) and len(cur) > 22: out.append(cur); cur = ''
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
        if sh.kind == 'black': return
        if sh.kind == 'studio':
            vhs_osd(cv, t, sh)
        else:
            H.header(cv, self.header_text(t), clock_hm(t))
        if sh.kind == 'rule': return
        l = self.line_at(t)
        if not l or not l.get('found_en', True): return
        k, ch = self.chunk_at(l, t)
        txt = ch[k]
        if l['who'] != 'N' or l.get('fx') == 'letter':
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
    """Keep the post offset inside the post zoom's margin (|px| <= 960 (1 - 1/pz), |py| <= 540 (1 - 1/pz)): the post move pads
    with a reflection, so an offset past the margin would show a mirrored copy of the set at the frame edge (the trap from
    the last film)."""
    if not (cs.px or cs.py): return cs
    pz = max(1.0, cs.pz)
    mx, my = 960.0 * (1 - 1 / pz), 540.0 * (1 - 1 / pz)
    px, py = clamp(cs.px, -mx, mx), clamp(cs.py, -my, my)
    if px == cs.px and py == cs.py: return cs
    return CamState(cs.x, cs.y, cs.zoom, cs.roll, cs.fz, cs.pz, px, py, cs.vx, cs.vy)


def vhs_osd(cv, t, sh):
    """The VCR's on-screen display over the full-frame tape (in place of the house header)."""
    pen = Pen(cv)
    tape_t = max(0.0, t - sh.p.get('tape0', T_TV_ON)) + sh.p.get('counter0', 734.0)
    blink = (t * 1.0) % 1.0 < 0.7
    if blink:
        text(cv, 'PLAY', 96, 92, 800, 30, '#f2f2f2', 225, 0.12, 'left', 0.9)
        pen.fill(poly([(70, 66), (88, 77), (70, 88)]), '#f2f2f2', 225)
    s = int(tape_t)
    text(cv, 'SP  %d:%02d:%02d' % (s // 3600, (s // 60) % 60, s % 60), DW - 90, 92, 800, 26, '#f2f2f2', 210, 0.12, 'right', 0.9)


def shot_table(F):
    """The cut list for the sound team: [{i, t0, t1, kind, space, loc, era, cut}]."""
    out = []
    for s in F.shots:
        out.append({'i': s.idx, 't0': round(s.t0, 3), 't1': round(s.t1, 3), 'kind': s.kind, 'space': shot_space(s),
                    'loc': shot_loc(s), 'era': s.p.get('era', 'now'), 'cut': s.p.get('cut')})
    return out


# ==================================================================================================== camera
class KeyCam(Cam):
    """Cam whose keys also carry an optical zoom f (no parallax): the deep interiors are pushed with f while the dolly part
    (z <= 1.3) keeps the parallax. fkeys [(t, f, ease)] interpolate like the keys (geometric, the same per-segment eases)."""
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


def push_rate(t):
    """Push-in speed grows toward the climaxes (reference median 2.3-2.8 %/s, p90 6-8 %/s)."""
    if t > 540: return 0.034
    if t > 400: return 0.03
    if t > 240: return 0.027
    return 0.024


def mkcam(sh, mv='push', x=960, y=540, z=1.0, rate=None, dx=0.0, dy=0.0, shake=1.6, roll=0.0, x1=None, y1=None, z1=None,
          snap=None, hit=None, opt=None, d=None, keys=None):
    """opt: constant optical zoom (no parallax; frames far layers); d: x, y (and x1, y1) are points on a layer at depth d.
    mv='keys': one continuous move through keys=[(t, x, y, z[, ease[, f]])] (absolute film seconds; ease of the segment
    arriving at the key, default 'in_out'; f = optical zoom), so a push, a hold-creep and a pan live in one shot."""
    t0, t1 = sh.t0, sh.t1
    if d is not None:
        x, y = 960 + d * (x - 960), 540 + d * (y - 540)
        if x1 is not None: x1 = 960 + d * (x1 - 960)
        if y1 is not None: y1 = 540 + d * (y1 - 540)
    r = rate if rate is not None else push_rate(t0)
    if mv == 'push':
        c = push_in(t0, t1, x, y, z, rate=r, drift=(dx, dy), roll=roll, shake=shake, seed=sh.idx)
    elif mv == 'fast':
        c = push_in(t0, t1, x, y, z, rate=r * 2.6, drift=(dx, dy), roll=roll, shake=shake + 0.8, seed=sh.idx)
    elif mv == 'creep':
        c = push_in(t0, t1, x, y, z, rate=r * 0.5, drift=(dx, dy), roll=roll, shake=shake * 0.6, seed=sh.idx)
    elif mv == 'pull':
        c = pull_out(t0, t1, x, y, z * (1 + max(0.06, r * 2.2 * sh.d)), z, shake=shake, seed=sh.idx)
    elif mv == 'drift':
        c = drift(t0, t1, x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2, zoom=z, z1=z * (1 + r * 0.5 * sh.d), shake=shake, seed=sh.idx)
    elif mv == 'move':
        c = Cam([(t0, x, y, z, roll), (t1, x1 if x1 is not None else x, y1 if y1 is not None else y, z1 or z * (1 + r * sh.d), roll, 'push')],
                shake=shake, seed=sh.idx)
    elif mv == 'keys':
        ks, fk = [], []
        for k in keys:
            kx, ky = (960 + d * (k[1] - 960), 540 + d * (k[2] - 540)) if d is not None else (k[1], k[2])
            ks.append((k[0], kx, ky, k[3], roll, k[4] if len(k) > 4 else None))
            fk.append((k[0], k[5] if len(k) > 5 else 1.0, k[4] if len(k) > 4 else None))
        c = KeyCam(ks, fk, shake=shake, seed=sh.idx)
    elif mv == 'hand':
        c = push_in(t0, t1, x, y, z, rate=r * 0.8, drift=(dx, dy), shake=4.5, seed=sh.idx)
        c.shake_hz = 0.9
    else:
        c = hold(x, y, z, shake=shake, seed=sh.idx)
    if opt: c.snap(t0 - 30.0, opt, 0.001)
    if snap:                                  # an eased 0.24 s push-in (a 0.1 s overshooting pop reads as a jump cut)
        c.snap_back = False; c.snap(snap[0], snap[1] if len(snap) > 1 else 1.25, 0.24)
    if hit:
        for h in (hit if isinstance(hit, (list, tuple)) else [hit]): c.hit(h, 7.0)
    return c


def cam_from(F, sh, d, default=None):
    d = dict(d or default or {})
    return mkcam(sh, **d)


# ==================================================================================================== actors
def acting(F, sh, who, act=None, seed=0, height=700.0, expr=None, talk=True, blink=None, voice=None, arc=None, worked=False):
    a = CH.Acting(who, seed=seed + sh.idx * 3, height=height, expr=expr or 'neutral', blink=blink, arc=arc)
    if act: act(a, sh)
    escalate(a, sh, who, worked)
    if talk:
        v = voice if voice is not None else VOICE.get(who, [])
        ls = F.voice_lines(sh.t0, sh.t1, v) if v else []
        if ls: a.talk([(l['t'], l['end'], l['en']) for l in ls])
        if who == 'winks' and voice is TAPE_VOICE:                    # the tape's own voice (a replay under the narration)
            for (ta, s0, s1, cut) in F.tv_voices:
                if ta + (s1 - s0) > sh.t0 - 0.2 and ta < sh.t1 + 0.2:
                    a.talk([(ta, ta + min(s1 - s0, cut), None)], env=tv_env(ta, s0, s1, cut), words=None)
    sh.actors.append(a)
    return a


_TVENV = {}


def tv_env(ta, s0, s1, cut=99.0):
    """The voice envelope with the source span [s0, s1) of the recording copied to film time ta (cut short after `cut` s):
    the tape dummy's jaw follows the TV's replay of his own voice."""
    key = (round(ta, 3), round(s0, 3), round(s1, 3), round(cut, 3))
    if key in _TVENV: return _TVENV[key]
    E = CH.voice_envelope()
    if E is None: return None
    out = np.full_like(E, -90.0)
    fps = CH.ENV_FPS
    a0, a1 = int(s0 * fps), int(min(s1, s0 + cut) * fps)
    b0 = int(ta * fps)
    n = min(a1 - a0, len(out) - b0)
    if n > 0: out[b0:b0 + n] = E[a0:a0 + n]
    _TVENV[key] = out
    return out


def escalate(a, sh, who, worked=False):
    """The film-wide acting arc (characters.escalate on the film clock): Mister Winks's wooden ticks come more often as the
    night goes on (none on a lap, on the tape or while he sleeps); you / Mom / Owen tremble harder (FEAR_ARC). Memory,
    tape, 1962 shots and rule cards: none."""
    if sh.kind in ('rule',) or sh.p.get('era') in ('memory', 'tape', '1962', 'later'): return
    if who in ('winks', 'you', 'mom', 'owen'):
        CH.escalate(a, sh.t0, sh.t1, 'worked' if worked else sh.kind)


def _beam_layer(m, x, y, h, depth, length=900.0, lens=False, name='beam', side=1, k=1.0):
    """The dummy's flashlight beam (characters.draw_torch_beam) from the glove he holds it in, while P.torch is on."""
    def draw(pen, t):
        P = m(t)
        if P.torch <= 0.01: return
        lx, ly, ang = CH.torch_pos('winks', P, side, x=x, y_feet=y, height=h)
        CH.draw_torch_beam(pen, lx, ly, ang, length * h / 400.0, a=P.torch * k, t=t, lens=P.torch_lens if lens else 0.0)
    return Layer(depth - 0.01 if not callable(depth) else (lambda t: depth(t) - 0.01), draw, name, blur=0)


def figure(F, sh, who, x, y, depth, height, act=None, seed=0, expr=None, light=None, name=None, path=None, talk=True,
           alpha=1.0, facing=0.0, shadow=0.0, surface='inside', voice=None, arc=None, dim=None, worked=False, torch=None,
           blink=None):
    """Full-body character layer. path walks along anchors with a real walk cycle and the layer depth follows the path.
    shadow 0..1 draws a dark silhouette. dim = f(t) | k darkens the figure with the room (set light levels). torch = dict(
    side, length, lens) draws Mister Winks's flashlight beam while it is on."""
    a = acting(F, sh, who, act, seed, height, expr, talk, voice=voice, arc=arc, worked=worked, blink=blink)
    m = _Memo(a)
    lt = light

    def put(pen, t, lx, ly, lh, P):
        if shadow > 0:
            cv = pen.cv
            cv.saveLayer(None, None)
            CH.draw(pen, who, lx, ly, lh, P, light=None, t=t)
            cv.drawPaint(skia.Paint(Color=skia.Color4f(0.012, 0.012, 0.025, shadow), BlendMode=skia.BlendMode.kSrcATop))
            cv.restore()
        else:
            CH.draw(pen, who, lx, ly, lh, P, light=lt(t) if callable(lt) else lt, t=t)

    if path is not None:
        legs = [path] if (len(path) == 3 and not isinstance(path[0], (list, tuple))) else list(path)
        L_ = []
        for lg in legs:
            q0, q1, pts_ = lg[0], lg[1], [tuple(q) for q in lg[2]]
            fc = lg[3] if len(lg) > 3 else facing
            sg = [math.hypot(pts_[j + 1][0] - pts_[j][0], pts_[j + 1][1] - pts_[j][1]) + abs(pts_[j + 1][3] - pts_[j][3]) * 1.5
                  for j in range(len(pts_) - 1)]
            L_.append((q0, q1, pts_, sg, sum(sg) or 1.0, fc))
        _walk_legs(a, [(q0, q1, tot_ * 1.4 / (a.height / 1000.0), fc) for (q0, q1, _, _, tot_, fc) in L_], surface)
        pts = L_[-1][2]

        def pos(t):
            leg = L_[0]
            for lg in L_:
                if t >= lg[0]: leg = lg
            q0, q1, pts_, sg, tot_, _ = leg
            u = clamp((t - q0) / max(1e-3, q1 - q0)); u = u * u * (3 - 2 * u) * 0.25 + u * 0.75
            dd = u * tot_
            for j, g in enumerate(sg):
                if dd <= g or j == len(sg) - 1:
                    f = clamp(dd / max(1e-6, g)); A, B = pts_[j], pts_[j + 1]
                    return tuple(A[q] + (B[q] - A[q]) * f for q in range(4))
                dd -= g
            return pts_[-1]
        R = pts[-1][2]

        def dfun(t): return pos(t)[2]

        def local(t):
            px, py, pd, ph = pos(t); s = pd / R
            return 960 + (px - 960) * s, 540 + (py - 540) * s, ph * s

        def draw(pen, t):
            P = m(t).copy(); P.dx = 0.0
            lx, ly, lh = local(t)
            put(pen, t, lx, ly, lh, P)
        lay = Layer(dfun, draw, name or who, ref_depth=R, alpha=alpha, dim=dim or 0.0)
        lay._pos = pos
        return lay, a

    def draw(pen, t):
        P = m(t)
        put(pen, t, x, y, height, P)
        if torch and P.torch > 0.01:
            lx, ly, ang = CH.torch_pos('winks', P, torch.get('side', 1), x=x, y_feet=y, height=height)
            CH.draw_torch_beam(pen, lx, ly, ang, torch.get('length', 2.2) * height, a=P.torch * torch.get('k', 1.0), t=t,
                               lens=P.torch_lens if torch.get('lens') else 0.0)
    lay = Layer(depth, draw, name or who, ref_depth=depth, alpha=alpha, dim=dim or 0.0)
    lay._m = m
    return lay, a


def _walk_legs(a, legs, surface='inside'):
    """Walk cycle for one or more walks per actor: legs [(t0, t1, units, facing)]; footstep events (inside: wood floor).
    '_quiet' suffix drops the footstep events."""
    info = []
    quiet = surface.endswith('_quiet')
    for (t0, t1, units, face) in legs:
        n = max(2, int(round((t1 - t0) * 1.9)))
        info.append((t0, t1, n / 2.0, face))
        if quiet: continue
        for k in range(1, n + 1):
            a._ev(t0 + (t1 - t0) * (k - 0.5) / n, 'footsteps_wood_inside', -6.0, pan=0.0, n=1, foot='L' if k % 2 else 'R')

    def fn(P, t):
        for (t0, t1, cyc, face) in info:
            if t0 - 0.45 <= t <= t1 + 0.45:
                amt = ease_in_out(clamp((t - t0 + 0.15) / 0.3)) * ease_in_out(clamp((t1 + 0.15 - t) / 0.3))
                w = ease_in_out(clamp((t - t0 + 0.4) / 0.4)) * ease_in_out(clamp((t1 + 0.45 - t) / 0.45))
                P.walk_amt = max(P.walk_amt, amt)
                P.walk_ph = cyc * clamp((t - t0) / max(1e-3, t1 - t0))
                P.turn = lerp(P.turn, face, w)
                P.lean += 0.05 * amt
    a._add(legs[0][0] - 0.5, legs[-1][1] + 0.6, fn)


def bust(F, sh, who, cx=960, cy=560, scale=1.0, act=None, seed=0, expr=None, light=None, depth=1.0, talk=True, name=None,
         voice=None, arc=None, worked=False, blink=None):
    a = acting(F, sh, who, act, seed, 700.0, expr, talk, voice=voice, arc=arc, worked=worked, blink=blink)
    m = _Memo(a)

    def draw(pen, t):
        CH.draw_bust(pen, who, cx, cy, scale, m(t), light=light(t) if callable(light) else light, t=t)
    lay = Layer(depth, draw, name or who, blur=0)
    lay._m = m
    return lay, a


def anc(sp, name):
    """Anchor -> (x, y, depth, height of a 1.85 m adult there). name: a set anchor, (x, y, d, h), or ('h', x, y[, Y]) a point on
    the house plan (HView sets) / ('v', X, D[, Y]) on a View set."""
    if isinstance(name, tuple) and name and name[0] in ('h', 'v'):
        v = sp.info['view']; a = v.anchor(name[1], name[2], name[3] if len(name) > 3 else 0.0)
        return (a.x, a.y, a.depth, a.height)
    if not isinstance(name, str): return name
    a = sp.anchors[name]; return (a.x, a.y, a.depth, a.height)


def people(F, sh, sp, ppl, light, dim=None):
    """ppl: list of dicts {who, at (anchor / tuple / ('h', x, y)), act, path, expr, seed, light, shadow, dy, dx, hk}.
    Anchor heights are a 1.85 m adult; each figure is scaled to its own height (HEIGHT_M)."""
    L, A = [], []
    for k, q in enumerate(ppl or []):
        who = q['who']
        at = q.get('at')
        if q.get('path') and at is None:
            pq = q['path']; at = (pq if not isinstance(pq[0], (list, tuple)) else pq[0])[2][0]
        x, y, d, h = anc(sp, at)
        hk = q.get('hk', HEIGHT_M.get(who, 1.85) / 1.85)
        x += q.get('dx', 0.0) * h; y += q.get('dy', 0.0) * h
        path = None
        if q.get('path'):
            pq = q['path']
            legs = [pq] if not isinstance(pq[0], (list, tuple)) else pq
            path = []
            for lg in legs:
                pts = []
                for n in lg[2]:
                    ax, ay, ad, ah = anc(sp, n)
                    pts.append((ax, ay, ad, ah * hk))
                path.append(tuple([lg[0], lg[1], pts] + list(lg[3:])))
        lay, a = figure(F, sh, who, x, y, d + q.get('dd', 0.0), h * hk, q.get('act'), seed=k * 11 + q.get('seed', 0), expr=q.get('expr'),
                        light=q.get('light', light), name='p%d_%s' % (k, who), path=path, talk=q.get('talk', True),
                        facing=q.get('facing', 0.0), alpha=q.get('alpha', 1.0), shadow=q.get('shadow', 0.0),
                        surface=q.get('surface', 'inside'), voice=q.get('voice'), arc=q.get('arc'), dim=q.get('dim', dim),
                        worked=q.get('worked', False), torch=q.get('torch'), blink=q.get('blink'))
        L.append(lay); A.append((q, lay, a))
    return L, A


def dimmed(sp, k, keep=()):
    for l in sp:
        if l.name not in keep and not callable(l.dim): l.dim = max(l.dim if isinstance(l.dim, float) else 0.0, k)
    return sp


def room_dim(level, lo=0.0, hi=0.62):
    """A figure's layer dim from a room light level f(t): lit 0 -> dark hi."""
    return lambda t: lerp(hi, lo, clamp(lvl(level, t)))


def P(who, at=None, act=None, **k):
    return dict(who=who, at=at, act=act, **k)


def W_(at='kitchen_chair', act=None, **k):
    """Mister Winks on a set (people() entry): dead still unless he acts; he talks only on his own lines."""
    return dict(who='winks', at=at, act=act, **k)


# ==================================================================================================== acting presets
def winks_chair(torch_up=True, look=0.85, t_turned=None, hands='table'):
    """Mister Winks in Grandpa's chair: sitting up straight, hands on the table, the flashlight in his left glove pointed at
    the ceiling; his head looks down the hall (h_turn = look, seen from the couch) until t_turned, then it has turned all
    the way toward you (the camera)."""
    def f(a, s):
        a.sit_dummy(hands=hands)
        if torch_up: a.torch_on(-1e9 + 1, 0.0, 1, hold='up')
        if look:
            a.set(-1e9, t_turned, 0.05, h_turn=look, lock=0.0)
    return f


def _A(*fns):
    return lambda a, s: [f(a, s) for f in fns if f]


def stare(d=-1.0): return lambda a, s: a.stare(s.t0 + d)
def ex(name, d=-1.0, t1=None): return lambda a, s: a.expr(name, s.t0 + d, t1)
def at_(t, **kw): return lambda a, s: a.set(t, None, kw.pop('fade', 0.3), **kw)
def setp(d=-2.0, fade=0.1, **kw): return lambda a, s: a.set(s.t0 + d, None, fade, **kw)
def turned(to=2.0, h=0.0): return lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=to, h_turn=h)
def tilt(d=0.3, ang=14.0, dur=1.6): return lambda a, s: a.head_tilt(s.t0 + d, ang, dur)
def down(d=-1.0, amt=1.0): return lambda a, s: a.head_down(s.t0 + d, None, amt)
def look_side(t, h=0.85, fade=0.45): return lambda a, s: a.set(t, None, fade, h_turn=h, lock=0.0, look_x=0.6 if h > 0 else -0.6)
def turn_to(t, to, dur=0.6): return lambda a, s: a.turn(t, to, dur)
def sitp(d=-3.0): return lambda a, s: a.set(s.t0 + d, None, 0.1, sit=1.0, perch=1.0)
def tremble(amp=0.6): return lambda a, s: a.tremble(s.t0 - 0.5, s.t1 + 0.5, amp)
def flinch_at(*ts, amp=1.0): return lambda a, s: [a.flinch(t, amp) for t in ts]
def blink_at(*ts): return lambda a, s: [a.blink(t) for t in ts]
def stage(n, d=-2.0, t1=None): return lambda a, s: a.smile_stage(s.t0 + d, n, t1)       # Mister Winks: hold an arc stage


def sway(amp=5.0, per=3.3, tilt=2.5, ph=0.0):
    def f(a, s):
        def fn(P, t):
            u = math.sin(2 * math.pi * (t - s.t0) / per + ph)
            P.sway += amp * u; P.tilt += 0.7 * u; P.h_tilt -= tilt * u
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
    return f


def creep(tilt=6.0, dur=None):
    """A slow head-tilt drift over the shot (the creepy cast's unease: Grandpa, the new Owen)."""
    def f(a, s):
        d = max(0.6, (dur or (s.t1 - s.t0)))

        def fn(P, t):
            P.h_tilt += tilt * ease_in_out(clamp((t - s.t0 + 0.3) / (d + 0.3)))
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
    return f


def jaw_chatter(t0, t1, rate=1.7, amount=0.55):
    """'jaw going up and down' in silence (the bookcase): a slow mechanical drop and clack, over and over (dummy_jaw /
    dummy_clack events on each)."""
    def f(a, s):
        k = t0
        while k < t1 - 0.3:
            a.jaw_drop(k, amount, 0.14)
            a.clack(k + 0.5 / rate + 0.05, 0.12)
            k += 1.0 / rate
    return f


# ==================================================================================================== builders: the house
def _fx(sp, p):
    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return fx


def _focus(p, sp, A, default=None):
    if p.get('focus') is not None: return p['focus']
    for q, lay, a in A:
        if q['who'] != 'winks' or q.get('focus_on'):
            return lay.depth_at(0.0) if not callable(lay.depth) else lay.ref_depth
    return default if default is not None else sp.focus


def _winks_entry(p, sp, light, dim):
    """p['winks'] (a dict or True) -> a people() entry for Mister Winks on this set."""
    wv = p.get('winks')
    if not wv: return None
    q = dict(who='winks', at=CHAIR_UP, act=winks_chair(), light=light, dim=dim, torch=dict(side=1, length=2.4))
    if isinstance(wv, dict): q.update(wv)
    return q


def B_hall(F, sh):
    """Down the front hall to the kitchen opening (gp_hall 'kitchen'). Mister Winks in Grandpa's chair through the opening
    (winks=True | dict), the knee-high beam (beam=), the family at the bench (ppl)."""
    p = sh.p
    sp = ST.gp_hall('kitchen', light=p.get('light', 1.0), kitchen=p.get('kitchen', 1.0), living=p.get('living', 0.6),
                    case=p.get('case', 'closed'), envelope=p.get('envelope', True), latch=p.get('latch', 0.0), den=p.get('den', 0.0),
                    clock=clock_minutes, beam=p.get('beam'), steam=p.get('steam', 1.0), mug=p.get('mug', True))
    hf, kf = sp.info['hall_light'], sp.info['kitchen']
    ppl = [dict(q) for q in p.get('ppl', [])]
    wq = _winks_entry(p, sp, house_light(kf, side=1), room_dim(kf, 0.1, 0.8))
    if wq: ppl.append(wq)
    L, A = people(F, sh, sp, ppl, p.get('light_fn') or house_light(hf), dim=room_dim(hf, 0.0, 0.5))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=560))
    grade = p.get('grade', 'gp_house' if lvl(hf, sh.t0 + 0.1) > 0.3 else 'gp_dark')
    return Spec(sp.add(*L), cam, 'lens', grade, _focus(p, sp, A), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def B_hdoor(F, sh):
    """The hall facing the front door (gp_hall 'door'): door 0..1 | f(t), tod 'night' | 'morning'."""
    p = sh.p
    sp = ST.gp_hall('door', light=p.get('light', 1.0), case=p.get('case', 'closed'), envelope=p.get('envelope', True),
                    tod=p.get('tod', 'night'), door=p.get('door', 0.0))
    hf = sp.info['hall_light']
    lt = (lambda t: MORNING) if p.get('tod') == 'morning' else house_light(hf)
    L, A = people(F, sh, sp, p.get('ppl', []), p.get('light_fn') or lt, dim=None if p.get('tod') == 'morning' else room_dim(hf, 0.0, 0.5))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=560))
    grade = p.get('grade', sp.grade if p.get('tod') == 'morning' else ('gp_house' if lvl(hf, sh.t0 + 0.1) > 0.3 else 'gp_dark'))
    return Spec(sp.add(*L), cam, 'lens', grade, _focus(p, sp, A), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def pov_hands(t0, t1=None, reach=(1000, 760), size=330, grab=None, shape='grip', dark=0.55, depth=0.5, both=True):
    """Your hands (POV) coming up into the frame from the bottom: denim cuffs, reaching to `reach` (design px) at t0 and holding
    there until t1 (then dropping out of frame). grab = t: the fingers close (grip) at t."""
    sl = CH.CAST['you']['cloth']

    def draw(pen, t):
        u_in = ease_out_cubic(clamp((t - t0) / 0.38))
        u_out = ease_in_out(clamp((t - t1) / 0.45)) if t1 is not None else 0.0
        if u_in <= 0 or u_out >= 1: return
        k = u_in * (1 - u_out)
        for sd in ((-1, 1) if both else (1,)):
            bx, by = reach[0] + sd * size * 0.95, reach[1]
            x = lerp(bx + sd * 520, bx, k); y = lerp(by + 900, by, k) + 6 * math.sin(t * 7 + sd)
            ang = 200.0 if sd < 0 else 160.0
            cv = pen.cv
            arm = poly([(x - 0.42 * size, y + 0.25 * size), (x + 0.42 * size, y + 0.3 * size), (x + sd * 0.6 * size + 0.5 * size, 1500),
                        (x + sd * 0.6 * size - 0.55 * size, 1500)])
            pen.shape(arm, sl['top'], 6); pen.fill(_crescent_x(arm, -sd * 30), sl['top_sh'], 150)
            pen.shape(rrect(x - 0.45 * size, y + 0.12 * size, 0.9 * size, 0.28 * size, 0.1 * size), sl['top_hi'], 5)
            shp = shape if (grab is None or t >= grab) else 'open'
            CH.draw_hand(pen, 'you', x, y + 0.14 * size, size, shp, ang, sd)
        if dark > 0:
            pen.cv.drawPaint(skia.Paint(Color=skia.Color4f(0.03, 0.035, 0.07, dark * 0.0)))
    return Layer(depth, draw, 'pov_hands', blur=0, dim=dark)


def _crescent_x(path, dx):
    m = skia.Matrix(); m.setTranslate(dx, 0)
    q = skia.Path(path); q.transform(m)
    return minus(path, q)


def B_stairs(F, sh):
    """Up the stairs (gp_hall 'stairs'): Mister Winks three steps up (winks=dict(...), default at 'step3' with the flashlight in
    your face), your POV hands (pov=dict(t0, t1, reach, grab))."""
    p = sh.p
    sp = ST.gp_hall('stairs', light=p.get('light', 0.0), beam=p.get('beam'))
    ppl = [dict(q) for q in p.get('ppl', [])]
    wv = p.get('winks')
    if wv:
        q = dict(who='winks', at='step3', act=lambda a, s: a.sit_dummy(hands='knees'), light=NIGHT, torch=dict(side=-1, length=2.0, lens=True))
        if isinstance(wv, dict): q.update(wv)
        ppl.append(q)
    L, A = people(F, sh, sp, ppl, p.get('light_fn') or (lambda t: NIGHT))
    if p.get('pov'):
        L.append(pov_hands(**p['pov']))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=560))
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'gp_dark'), _focus(p, sp, A, 1.43 if wv else None), p.get('dof', sp.dof),
                fx=_fx(sp, p), hud=p.get('hud'))


def _kitchen_set(p, view):
    kw = dict(kitchen=p.get('kitchen', 1.0), steam=p.get('steam', 1.0), chair=True, tod=p.get('tod', 'night'), sway=p.get('sway', 0.0))
    t_off = p.get('mug_off')
    if t_off is None:
        return ST.gp_kitchen(view, mug=p.get('mug', True), **kw)
    kw['steam'] = dict(off=t_off)
    a = ST.gp_kitchen(view, mug=True, **kw)
    b = ST.gp_kitchen(view, mug=False, **kw)
    ta = a.layer('k_table'); tb = b.layer('k_table')
    ta.alpha = lambda t, t_=t_off: 1.0 if t < t_ else 0.0
    tb.alpha = lambda t, t_=t_off: 0.0 if t < t_ else 1.0
    tb.name = 'k_table_nomug'
    return a.add(tb)


def B_kitchen(F, sh):
    """The kitchen (gp_kitchen 'table' | 'chair'): Mister Winks in Grandpa's chair (winks=), Mom picking up the mug
    (mug_off = t: the set's mug vanishes as she lifts hers), the new Owen at 8 AM / the last morning (tod='morning')."""
    p = sh.p
    view = p.get('view', 'table')
    sp = _kitchen_set(p, view)
    kf = sp.info['kitchen']
    morning = p.get('tod') == 'morning'
    lt = (lambda t: MORNING) if morning else house_light(kf, side=1)
    ppl = [dict(q) for q in p.get('ppl', [])]
    wq = _winks_entry(dict(p, winks=p.get('winks') and dict(dict(at=CHAIR_UP), **(p['winks'] if isinstance(p['winks'], dict) else {}))),
                      sp, lt, None if morning else room_dim(kf, 0.0, 0.85))
    if wq: ppl.append(wq)
    L, A = people(F, sh, sp, ppl, p.get('light_fn') or lt, dim=None if morning else room_dim(kf, 0.0, 0.85))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    grade = p.get('grade', sp.grade)
    return Spec(sp.add(*L), cam, 'lens', grade, _focus(p, sp, A, sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


# ---------------------------------------------------------------------------------------------------- the 1974 tape
LAUGH_T = []                     # laugh-wave times on the film clock (plan() fills it): studio laughter = applause = he moves


def laugh_fn(F):
    return ST.laugh_waves(sorted(set(LAUGH_T)), 2.6, 1.0) if LAUGH_T else (lambda t: 0.0)


def tape_figures(F, sh, w_act=None, d_act=None, light=TAPE, scale=1.0, cx=960, cy=760, h=None):
    """Young Walter on the stool with Mister Winks on his knee, as the tape shows them (drawn in the studio's 1920x1080 space;
    the same function draws them full frame and on the living-room CRT). Walter's lips never move; the dummy's jaw talks on
    the tape's lines (R) and on the tape's own replayed voice (tv_voice)."""
    hh = (h or 760.0 * HEIGHT_M['walter74'] / 1.85) * scale
    wa = acting(F, sh, 'walter74', _A(lambda a, s: a.vent_pose(side=1), lambda a, s: a.set(-1e9, None, 0.1, perch=1.0, turn=0.45),
                                      lambda a, s: a.showman(s.t0 - 2, s.t1 + 2), w_act), talk=False, worked=True)
    da = acting(F, sh, 'winks', _A(lambda a, s: a.sit_dummy(), d_act or (lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.8))),
                voice=TAPE_VOICE, arc=CH.WINKS_TAPE_ARC, worked=True)
    mw, md = _Memo(wa), _Memo(da)

    def figures(pen, t):
        CH.draw_lap(pen, 'walter74', cx, cy, hh, mw(t), md(t), side=1, m=HEIGHT_M['walter74'], light=light)
    return figures, wa, da


def B_studio(F, sh):
    """'Saturday Morning with Walter Kemp', 1974, full frame through the VHS / CRT look: the stage, the figures (tape_figures),
    the audience shaking with the laughter waves (LAUGH_T). view 'full' | 'close' (the studio camera tighter: cam keys)."""
    p = sh.p
    lf = laugh_fn(F)
    sp = ST.gp_studio(p.get('view', 'full'), laugh=lf, bezel=p.get('bezel', 0.0), track=p.get('track', 0.35))
    L = []
    if p.get('figures', True):
        fig, wa, da = tape_figures(F, sh, p.get('w_act'), p.get('d_act'))
        L.append(Layer(1.0, lambda pen, t: fig(pen, t), 'tape_figures', blur=0))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=560, rate=0.03))
    sh.p.setdefault('era', 'tape')

    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('track_fn') and isinstance(d.get('vhs'), dict): d['vhs'] = dict(d['vhs'], track=p['track_fn'](t))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(*L), cam, None, p.get('grade', 'vhs74'), 1.0, 0.0, fx=fx, hud=p.get('hud'))


def B_living(F, sh):
    """The living room (gp_living): 'tv' from the couch (the CRT plays the tape live with the cast on it; the kitchen
    doorway with Mister Winks in Grandpa's chair: winks=), 'couch' (the family on the couch under the lamp, Mom at the
    bookcase, Mister Winks on the bookcase top: winks=dict(at='bookcase_top', ...))."""
    p = sh.p
    view = p.get('view', 'tv')
    tv = p.get('tv')
    content = None
    if tv is not None and p.get('tape', True):
        fig, wa, da = tape_figures(F, sh, p.get('w_act'), p.get('d_act'))
        content = ST.studio_content(figures=fig, laugh=laugh_fn(F))
    sp = ST.gp_living(view, lamp=p.get('lamp', 1.0), tv=tv, kitchen=p.get('kitchen', 1.0), steam=p.get('steam', 1.0),
                      mug=p.get('mug', True), content=content, tod=p.get('tod', 'night'))
    lf = sp.info.get('lamp'); kf = sp.info.get('kitchen')
    lt = p.get('light_fn') or tv_light(sp)
    ppl = [dict(q) for q in p.get('ppl', [])]
    if p.get('winks'):
        wv = p['winks']
        if view == 'tv':
            q = dict(who='winks', at=CHAIR_UP, act=winks_chair(), light=house_light(kf, side=1), dim=room_dim(kf, 0.1, 0.85),
                     torch=dict(side=1, length=2.4))
        else:
            q = dict(who='winks', at='bookcase_top', act=lambda a, s: a.sit_dummy(hands='limp'), light=TORCH, torch=dict(side=1, length=1.2))
        if isinstance(wv, dict): q.update(wv)
        ppl.append(q)
    L, A = people(F, sh, sp, ppl, lt, dim=room_dim(lambda t: max(lvl(lf, t), 0.6 * ST.tv_level(sp.info.get('tv'), t)), 0.05, 0.55))
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    on = tv is not None and ST.tv_level(sp.info.get('tv'), sh.t0 + 0.5) > 0.05
    grade = p.get('grade', 'tv_glow' if on else ('gp_house' if lvl(lf, sh.t0 + 0.1) > 0.3 else 'gp_dark'))
    return Spec(sp.add(*L), cam, 'lens', grade, _focus(p, sp, A, sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def lap_layer(F, sh, who, x, y, height, act=None, dact=None, side=1, depth=1.0, light=None, dlight=None, between=None,
              dvoice=None, d_arc=None, jerk=None, name='lap', release=None, fall=None, seed=0):
    """A person sitting with Mister Winks on the knee (characters.draw_lap). y = the seat surface (the person perches).
    jerk = f(t) -> dx px (Mom pulling at him); release = t: from then the person is drawn alone (they slide the hand out
    and jump up) and the dummy falls face down to fall = (x, y, h) (the rug)."""
    m = HEIGHT_M.get(who, 1.7)
    pa = acting(F, sh, who, _A(lambda a, s: a.set(-1e9, None, 0.1, perch=1.0, turn=0.45 * side), act), seed=seed)
    da = acting(F, sh, 'winks', _A(lambda a, s: a.sit_dummy(), dact), voice=dvoice, arc=d_arc, worked=True, seed=seed + 5)
    mp, md = _Memo(pa), _Memo(da)
    st = {}

    def draw(pen, t):
        Pp, Pd = mp(t), md(t)
        lt = light(t) if callable(light) else light
        dl = dlight(t) if callable(dlight) else (dlight or lt)
        if release is not None and t >= release:
            if 'k' not in st:
                Q, D = mp(release), md(release)
                ax, ay = CH.lap_anchor(who, Q, side, x, y, height)
                st['k'] = (ax, ay - 0.05 * height, height * CH.DUMMY_M / m)
            CH.draw(pen, who, x, y, height, Pp, light=lt, t=t)
            ax, ay, dh = st['k']
            if fall:
                u = ease_in_out(clamp((t - release) / 0.45))
                fx_, fy_, fh_ = fall
                D = Pd.copy()
                D.sit = lerp(1.0, 0.0, u); D.perch = 1.0 - u
                CH.draw(pen, 'winks', lerp(ax, fx_, u), lerp(ay, fy_, u), lerp(dh, fh_, u), D, light=dl, t=t)
            return
        dx = jerk(t) if jerk else 0.0
        CH.draw_lap(pen, who, x, y, height, Pp, Pd, side=side, m=m, light=lt, dlight=dl, between=between, dx=dx)
    lay = Layer(depth, draw, name, ref_depth=depth if not callable(depth) else None)
    return lay, pa, da


def B_den(F, sh):
    """Grandpa's den (gp_den): Owen in the armchair with the dummy on his knee (lap=dict(...)), Mom, you kneeling (ppl), the
    lamp going out (lamp=dict(out=...)), the dummy face down on the rug (rug=True)."""
    p = sh.p
    sp = ST.gp_den(lamp=p.get('lamp', 1.0), hall=p.get('hall', 0.5))
    lf = sp.info['lamp']
    lt = p.get('light_fn') or house_light(lf, side=-1)
    dim = room_dim(lf, 0.0, 0.78)
    L, A = people(F, sh, sp, p.get('ppl', []), lt, dim=dim)
    if p.get('lap'):
        q = dict(p['lap'])
        x, y, d, h = anc(sp, q.pop('at', 'armchair'))
        who = q.pop('who', 'owen')
        hh = h * HEIGHT_M[who] / 1.85
        fall = None
        if q.get('release') is not None:
            rx, ry, rd, rh = anc(sp, 'rug')
            fall = (rx + 0.1 * rh, ry, rh * CH.DUMMY_M / 1.85)
        lay, pa, da = lap_layer(F, sh, who, x + q.pop('dx', 0.0) * h, y, hh, q.pop('act', None), q.pop('dact', None), side=q.pop('side', 1),
                                depth=d, light=lt, dvoice=VOICE['winks'], fall=fall, **q)
        lay.dim = dim
        L.append(lay)
    if p.get('rug'):
        rv = p['rug'] if isinstance(p['rug'], dict) else {}
        L2, A2 = people(F, sh, sp, [dict(dict(who='winks', at='rug', act=lambda a, s: a.face_down(), dx=0.1), **rv)], lt, dim=dim)
        L += L2
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=560))
    grade = p.get('grade', 'gp_house' if lvl(lf, sh.t0 + 0.1) > 0.3 else 'gp_dark')
    return Spec(sp.add(*L), cam, 'lens', grade, p.get('focus', sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


# ---------------------------------------------------------------------------------------------------- elsewhere
def blanket_fn(x0, y0, w, h, c='#a9c3d6'):
    """The hospital blanket over the legs (drawn between the person and the dummy)."""
    def f(pen):
        b = smooth([(x0 - w * 0.5, y0 + h * 0.15), (x0 - w * 0.45, y0 - h * 0.05), (x0, y0 - h * 0.12), (x0 + w * 0.45, y0 - h * 0.02),
                    (x0 + w * 0.55, y0 + h * 0.3), (x0 + w * 0.5, y0 + h), (x0 - w * 0.5, y0 + h)], True, 0.7)
        pen.shape(b, c, 4); pen.fill(_crescent_x(b, 30), '#7894aa', 140)
        for k in range(3):
            pen.line(smooth([(x0 - w * 0.35 + k * w * 0.3, y0), (x0 - w * 0.3 + k * w * 0.3, y0 + h * 0.6)], False), 3, '#7894aa', 120)
    return f


def B_hospital(F, sh):
    """The hospital room last week (hospital 'bed' | 'close'): Grandpa (bed='grandpa_bed' | 'walter') sitting up in bed
    (with the dummy on his lap: lap=True | limp beside him: dummy='bed' | in the visitor chair: dummy='chair'), you at the
    bedside (ppl), the live ECG (bpm, flat)."""
    p = sh.p
    view = p.get('view', 'bed')
    sp = ST.hospital(view, bpm=p.get('bpm', 72.0), flat=p.get('flat'), light=p.get('light', 1.0))
    hv = sp.info['view']
    L = []
    who = p.get('bed', 'grandpa_bed')
    seat = hv.anchor(0.0, 3.35, 0.62)
    hh = seat.height * HEIGHT_M[who] / 1.85
    bd = sp.layer('hp_bed').depth_at(0.0) - 0.03            # in front of the bed (he sits up against the pillows)
    bl = blanket_fn(seat.x + 0.02 * hh, seat.y - 0.02 * hh, 0.55 * hh, 0.42 * hh)
    act = _A(lambda a, s: a.in_bed(), p.get('bed_act'))
    if p.get('lap'):
        lay, pa, da = lap_layer(F, sh, who, seat.x, seat.y, hh, _A(act, lambda a, s: a.vent_pose(side=1), lambda a, s: a.set(-9, None, 0.1, turn=0.12)),
                                p.get('dact', lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.7)), side=1, depth=bd,
                                light=HOSP, between=bl, dvoice=VOICE['winks'])
        L.append(lay)
    else:
        lay, a = figure(F, sh, who, seat.x, seat.y, bd, hh, _A(lambda a, s: a.set(-9, None, 0.1, perch=1.0), act), light=HOSP,
                        name='bed_' + who, voice=VOICE.get(who))
        L.append(lay)
        L.append(Layer(bd - 0.01, lambda pen, t: bl(pen), 'blanket', blur=None))
        if p.get('dummy') == 'bed':
            bq = hv.anchor(0.32, 3.0, 0.62)
            L2, _ = people(F, sh, sp, [dict(who='winks', at=(bq.x, bq.y, bd - 0.02, bq.height),
                                            act=_A(lambda a, s: a.sit_dummy(hands='limp', slump=1.0), p.get('dact')), light=HOSP)], HOSP)
            L += L2
    if p.get('dummy') == 'chair':
        L2, _ = people(F, sh, sp, [dict(who='winks', at='chair', act=_A(lambda a, s: a.sit_dummy(), p.get('dact')), light=HOSP)], HOSP)
        L += L2
    L2, A = people(F, sh, sp, p.get('ppl', []), HOSP)
    L += L2
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'hospital'), p.get('focus', bd), p.get('dof', sp.dof), fx=_fx(sp, p),
                hud=p.get('hud'))


def B_stage62(F, sh):
    """The Palace, 1962 (stage_1962, sepia): young Walter on the stool with Mister Winks on his knee."""
    p = sh.p
    sp = ST.stage_1962(spot=p.get('spot', 1.0), curtain=p.get('curtain', 1.0))
    a_ = sp.anchors['stool']
    hh = a_.height * HEIGHT_M['walter74'] / 1.85
    lay, wa, da = lap_layer(F, sh, 'walter74', a_.x, a_.y, hh, _A(lambda a, s: a.vent_pose(side=1), lambda a, s: a.set(-9, None, 0.1, turn=0.45),
                                                                 p.get('w_act')),
                            p.get('d_act'), side=1, depth=a_.depth, light=dict(rim='#fff2d0', rim_a=90, side=-1, key=0.2), name='walter62')
    sh.p.setdefault('era', '1962')
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    return Spec(sp.add(lay), cam, 'lens', p.get('grade', 'memory'), a_.depth, p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def B_museum(F, sh):
    """The museum vitrine (museum 'case' | 'wide'): Mister Winks behind the glass (the 'owen' stage: Owen inside him)."""
    p = sh.p
    sp = ST.museum(p.get('view', 'case'), spot=p.get('spot', 1.0))
    gl = sp.layer('mu_glass')
    a_ = sp.anchors['display']
    gd = gl.depth_at(0.0)
    L, A = people(F, sh, sp, [dict(who='winks', at=(a_.x, a_.y, max(gd + 0.02, a_.depth), a_.height),
                                   act=_A(lambda a, s: a.sit_dummy(), p.get('act')), light=MUSEUM)], MUSEUM)
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    sh.p.setdefault('era', 'later')
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'museum'), p.get('focus', sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def B_street(F, sh):
    """8 AM (street_morning 'window' | 'outside'): the new Owen waving as the museum van pulls away."""
    p = sh.p
    view = p.get('view', 'window')
    sp = ST.street_morning(view, van=p.get('van'))
    ppl = [dict(q) for q in p.get('ppl', [])]
    L, A = people(F, sh, sp, ppl, lambda t: MORNING)
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    sh.p.setdefault('era', 'later')
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'morning'), p.get('focus', sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


def B_bedroom(F, sh):
    """Your bedroom months later (bedroom_doorway): the new Owen stops in the backlit doorway."""
    p = sh.p
    sp = ST.bedroom_doorway(hall=p.get('hall', 1.0), door=p.get('door', 0.85))
    L, A = people(F, sh, sp, p.get('ppl', []), lambda t: BACKLIT)
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    sh.p.setdefault('era', 'later')
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'gp_dark'), p.get('focus', sp.focus), p.get('dof', sp.dof), fx=_fx(sp, p), hud=p.get('hud'))


# ==================================================================================================== close-ups
def _bg(F, sh, name, p):
    """Background set for close-ups (drawn at its own depths, blurred by DOF and darkened): -> (setpiece, light, grade)."""
    if name == 'hall':
        sp = ST.gp_hall('kitchen', light=p.get('light', 1.0), kitchen=p.get('kitchen', 1.0), case=p.get('case', 'closed'), clock=clock_minutes)
        lt, gr = house_light(sp.info['hall_light']), 'face_close'
    elif name == 'hall_dark':
        sp = ST.gp_hall('kitchen', light=0.0, kitchen=p.get('kitchen', 0.0), living=0.0, case=p.get('case', 'open'), clock=clock_minutes,
                        beam=p.get('beam'))
        lt, gr = (lambda t: NIGHT), 'gp_dark'
    elif name == 'hdoor':
        sp = ST.gp_hall('door', light=p.get('light', 1.0), tod=p.get('tod', 'night'), door=p.get('door', 0.0))
        lt, gr = ((lambda t: MORNING), 'morning') if p.get('tod') == 'morning' else (house_light(sp.info['hall_light']), 'face_close')
    elif name == 'kitchen':
        sp = _kitchen_set(dict(p, mug=p.get('mug', True)), 'chair')
        lt, gr = house_light(sp.info['kitchen'], side=1), 'face_close'
    elif name == 'kitchen_table':
        sp = _kitchen_set(dict(p, mug=p.get('mug', True)), 'table')
        lt, gr = house_light(sp.info['kitchen'], side=1), 'face_close'
    elif name in ('kitchen_morning', 'memory_kitchen'):
        sp = ST.gp_kitchen('table', tod='morning', steam=p.get('steam', 1.0))
        lt, gr = ((lambda t: MEMORY), 'memory') if name == 'memory_kitchen' else ((lambda t: MORNING), 'morning')
    elif name in ('living', 'living_tv'):
        tv = p.get('tv')
        content = None
        if tv is not None:
            fig, _, _ = tape_figures(F, sh)
            content = ST.studio_content(figures=fig, laugh=laugh_fn(F))
        sp = ST.gp_living('couch' if name == 'living' else 'tv', lamp=p.get('lamp', 1.0), tv=tv, content=content)
        lt, gr = tv_light(sp), ('tv_glow' if tv is not None else 'face_close')
    elif name == 'stairs':
        sp = ST.gp_hall('stairs', light=p.get('light', 0.0))
        lt, gr = (lambda t: NIGHT), 'gp_dark'
    elif name == 'den':
        sp = ST.gp_den(lamp=p.get('lamp', 1.0), hall=0.5)
        lt, gr = house_light(sp.info['lamp']), 'face_close'
    elif name == 'hospital':
        sp = ST.hospital(p.get('hview', 'bed'), bpm=p.get('bpm', 72.0), flat=p.get('flat'))
        lt, gr = (lambda t: HOSP), 'hospital'
    elif name == 'studio':
        sp = ST.gp_studio('full', laugh=laugh_fn(F), bezel=p.get('bezel', 0.0), track=p.get('track', 0.35))
        lt, gr = (lambda t: TAPE), 'vhs74'
    elif name == 'memory_bed':
        sp = ST.bedroom_doorway(hall=1.0, door=0.4)
        lt, gr = (lambda t: MEMORY), 'memory'
    elif name == 'bedroom':
        sp = ST.bedroom_doorway(hall=1.0, door=0.85)
        lt, gr = (lambda t: BACKLIT), 'gp_dark'
    elif name == 'museum':
        sp = ST.museum('case')
        lt, gr = (lambda t: MUSEUM), 'museum'
    elif name == 'stage62':
        sp = ST.stage_1962()
        lt, gr = (lambda t: dict(rim='#fff2d0', rim_a=90, side=-1, key=0.2)), 'memory'
    elif name == 'street':
        sp = ST.street_morning('window')
        lt, gr = (lambda t: MORNING), 'morning'
    else:
        raise KeyError(name)
    return dimmed(sp, p.get('bg_dim', 0.3)), lt, gr


# bust framings per character: (cx, cy, scale, body turn, head turn relative to the body). Rotated so the same
# (who, bg, framing) never repeats within 60 s (assign_bust_framings); Mister Winks keeps his glass eyes on the lens.
BUST_FRAMES = {
    'winks': [(960, 560, 1.0, 0.0, 0.0), (800, 590, 0.92, 0.3, -0.3), (1140, 570, 1.08, -0.3, 0.3), (960, 610, 0.84, 0.0, 0.0),
              (760, 560, 1.12, 0.22, -0.22), (1180, 600, 0.9, -0.35, 0.35)],
    'you': [(960, 580, 1.0, 0.0, 0.0), (1180, 610, 0.9, -0.55, 0.0), (720, 580, 1.08, 0.5, -0.2), (960, 640, 0.78, 0.0, 0.0),
            (1240, 560, 1.15, -0.35, 0.1), (680, 620, 0.88, 0.75, -0.15)],
    'mom': [(960, 590, 1.0, 0.0, 0.0), (720, 600, 0.92, 0.55, 0.0), (1200, 590, 1.06, -0.45, 0.1), (960, 650, 0.8, 0.0, 0.0),
            (680, 570, 1.12, 0.35, -0.1), (1240, 620, 0.88, -0.75, 0.15)],
    'owen': [(960, 620, 1.0, 0.0, 0.0), (1180, 640, 0.92, -0.4, 0.1), (740, 630, 1.06, 0.4, -0.1), (960, 660, 0.86, 0.0, 0.0)],
    'owen_new': [(960, 620, 1.0, 0.0, 0.0), (1160, 640, 0.92, -0.3, 0.3), (760, 630, 1.06, 0.3, -0.3)],
    'grandpa': [(960, 580, 1.0, 0.0, 0.0), (1180, 600, 0.92, -0.45, 0.1), (720, 590, 1.06, 0.45, -0.1)],
    'grandpa_bed': [(960, 580, 1.0, 0.0, 0.0), (1160, 600, 0.94, -0.35, 0.1), (760, 590, 1.04, 0.35, -0.1)],
    'walter': [(960, 580, 1.0, 0.0, 0.0), (1160, 600, 0.94, -0.35, 0.1), (760, 590, 1.04, 0.35, -0.1)],
    'walter74': [(960, 580, 1.0, 0.0, 0.0), (1160, 600, 0.94, -0.3, 0.2), (760, 590, 1.04, 0.3, -0.2)],
}


def assign_bust_framings(F):
    last, ctr = {}, {}
    for sh in F.shots:
        if sh.kind != 'bust' or 'cx' in sh.p: continue
        who = sh.p.get('who', 'you'); bg = sh.p.get('bg', 'hall')
        opts = BUST_FRAMES.get(who, BUST_FRAMES['you'])
        k0 = ctr.get(who, 0); k = k0 % len(opts)
        for j in range(len(opts)):
            k = (k0 + j) % len(opts)
            if sh.t0 - last.get((who, bg, k), -1e9) >= 60.0: break
        ctr[who] = k + 1; last[(who, bg, k)] = sh.t0
        sh.p['_frame'] = opts[k]


def _head_guard(cd, top, d):
    """Keep the crown (design y `top` at depth 1) >= 24 px inside the frame over the whole camera move."""
    z0 = cd.get('z', 1.0)
    mv = cd.get('mv', 'push')
    r = cd.get('rate', 0.03)
    z1 = cd.get('z1') or (z0 * (1 + r * (2.6 if mv == 'fast' else 1.0)) ** d if mv in ('push', 'fast', 'hand', 'creep') else z0)
    k = cd['snap'][1] if cd.get('snap') and len(cd['snap']) > 1 else (1.25 if cd.get('snap') else 1.0)
    zmax = max(z0, z1) * k
    lim = top + 516.0 / zmax
    if cd.get('y', 540) > lim: cd['y'] = lim
    if cd.get('y1') is not None and cd['y1'] > lim: cd['y1'] = lim
    return cd


def B_bust(F, sh):
    """Face close-up over a blurred, darkened set; framings rotate; the crown never leaves the frame unless p['ecu'].
    p['ghost'] = [people() entries] puts figures in the blurred set behind (the dummy on the bookcase behind Mom)."""
    p = sh.p
    bgn = p.get('bg', 'hall')
    sp, light, gr = _bg(F, sh, bgn, p)
    who = p.get('who', 'you')
    fr = p.get('_frame')
    cx = p.get('cx', fr[0] if fr else 960)
    cy = p.get('cy', fr[1] if fr else 560)
    sc = p.get('scale', fr[2] if fr else 1.0)
    view = None
    if fr and (fr[3] or fr[4]) and not p.get('no_view'):
        view = lambda a, s, v=(fr[3], fr[4]): a.set(s.t0 - 3, None, 0.1, turn=v[0], h_turn=v[1])
    base = None
    if who == 'winks':
        base = lambda a, s: a.sit_dummy(hands=p.get('hands', 'knees'))
    voice = TAPE_VOICE if p.get('tape') else None
    arc = CH.WINKS_TAPE_ARC if p.get('tape') else None
    lay, a = bust(F, sh, who, cx, cy, sc, _A(base, view, p.get('act')), expr=p.get('expr'), light=p.get('light', light), voice=voice, arc=arc,
                  worked=bool(p.get('tape') or p.get('worked')))
    extra = []
    if p.get('ghost'):
        L2, _ = people(F, sh, sp, p['ghost'], light)
        extra += L2
    if p.get('torch_glow'):                                   # the flashlight under his chin, in frame below the face
        tg = p['torch_glow']

        def glow(pen, t, tg=tg):
            k = clamp((t - tg) / 0.06) if isinstance(tg, (int, float)) else 1.0
            if k <= 0: return
            x, y = cx + 30 * sc, cy + 420 * sc
            pen.glow(x, y, 220 * sc, '#fff1c8', 170 * k); pen.glow(x, y, 60 * sc, '#ffffff', 230 * k)
        extra.append(Layer(0.95, glow, 'torch_glow', blur=0))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=cy - 20)))
    if fr and 'x' in cd and cd['x'] == 960: cd['x'] = 960 + (cx - 960) * 0.3
    if not p.get('ecu') and cd.get('mv') != 'keys': cd = _head_guard(cd, cy - 330 * sc, sh.d)
    cam = cam_from(F, sh, cd)
    grade = p.get('grade', gr)
    if bgn == 'studio': sh.p.setdefault('era', 'tape')

    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('track_fn') and isinstance(d.get('vhs'), dict): d['vhs'] = dict(d['vhs'], track=p['track_fn'](t))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(lay, *extra), cam, None, grade, 1.0, p.get('dof', 6.75), fx=fx, hud=p.get('hud'))


def B_lap(F, sh):
    """A person with Mister Winks on the knee, large (draw_lap), over a blurred set: who 'owen' (the den), 'grandpa_bed'
    (hospital, the blanket between), 'walter74' (the tape / 1962). x, y (seat), h (person height px)."""
    p = sh.p
    bgn = p.get('bg', 'den')
    sp, light, gr = _bg(F, sh, bgn, p)
    who = p.get('who', 'owen')
    x, y, h = p.get('x', 900), p.get('y', 900), p.get('h', 1500)
    between = blanket_fn(x + 0.03 * h, y - 0.02 * h, 0.55 * h, 0.42 * h) if who in ('grandpa_bed', 'walter') else None
    lay, pa, da = lap_layer(F, sh, who, x, y, h, p.get('act'), p.get('dact'), side=p.get('side', 1), depth=1.0, light=p.get('light', light),
                            between=between, dvoice=TAPE_VOICE if p.get('tape') else VOICE['winks'], d_arc=CH.WINKS_TAPE_ARC if p.get('tape') else None,
                            jerk=p.get('jerk'))
    if bgn in ('studio',): sh.p.setdefault('era', 'tape')
    if bgn in ('stage62',): sh.p.setdefault('era', '1962')
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    return Spec(sp.add(lay), cam, None, p.get('grade', gr), 1.0, p.get('dof', 6.75), fx=_fx(sp, p), hud=p.get('hud'))


def B_carry(F, sh):
    """You holding Mister Winks in your arms, large (draw_carry), over the blurred den: 'In my arms, he opens his eyes'."""
    p = sh.p
    sp, light, gr = _bg(F, sh, p.get('bg', 'den'), p)
    x, y, h = p.get('x', 900), p.get('y', 2300), p.get('h', 2400)
    ya = acting(F, sh, 'you', _A(lambda a, s: a.hold_dummy(), p.get('act')))
    da = acting(F, sh, 'winks', _A(lambda a, s: a.carried(), p.get('dact')))
    my, md = _Memo(ya), _Memo(da)
    lt = p.get('light', light)

    def draw(pen, t):
        l_ = lt(t) if callable(lt) else lt
        CH.draw_carry(pen, 'you', x, y, h, my(t), md(t), m=HEIGHT_M['you'], light=l_)
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    return Spec(sp.add(Layer(1.0, draw, 'carry', blur=0)), cam, None, p.get('grade', gr), 1.0, p.get('dof', 6.75), fx=_fx(sp, p), hud=p.get('hud'))


def B_portrait(F, sh):
    """Mister Winks full figure, large, over a dark red velvet backdrop (the case lining), lit like a museum piece; one
    camera move travels over him (cam keys): the painted hair, the freckles, the jacket and brass buttons, the flashlight
    clicking on in one white glove."""
    p = sh.p
    x, y, h = p.get('x', 960), p.get('y', 3000), p.get('h', 2600)
    a = acting(F, sh, 'winks', _A(lambda a_, s: a_.set(-9, None, 0.1, h_tilt=-4.0), p.get('act')))
    m = _Memo(a)

    def back(pen, t):
        pen.radial(None, 960, 900, 2600, [(0, '#5a141c'), (0.55, '#300a10'), (1, '#0c0204')], clip=False)
        pen.texture(rect(-1500, -1500, 4920, 5080), 'fabric', 0.35, 'overlay', 2.0, 90)
        for k in range(14):
            yy = -900 + k * 380
            pen.line(smooth([(-1500, yy), (0, yy + 60), (1500, yy - 30), (3400, yy + 40)], False), 30, '#000000', 40)

    def draw(pen, t):
        P = m(t)
        CH.draw(pen, 'winks', x, y, h, P, light=dict(rim='#fff0d8', rim_a=110, side=-1, key=0.15), t=t)
        if P.torch > 0.01:
            lx, ly, ang = CH.torch_pos('winks', P, 1, x=x, y_feet=y, height=h)
            CH.draw_torch_beam(pen, lx, ly, ang, 0.6 * h, a=P.torch, t=t)

    def key(pen, t):
        pen.radial(None, 1200, 300, 1600, [(0, '#fff0d8', 34), (1, '#fff0d8', 0)], clip=False)
    L = [Layer(2.2, back, 'velvet', cache='film:portrait:velvet', bounds=(-1500, -1500, 3420, 3580)), Layer(1.0, draw, 'winks'),
         Layer(0.9, key, 'key', blur=0)]
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=960, y=540))
    return Spec(L, cam, None, p.get('grade', 'face_close'), 1.0, p.get('dof', 2.0), fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def _sleeve(pen, who, x, y, ang, size, length=1400.0):
    """A sleeve running from a hand's wrist (x, y) back along the arm (ang = the hand's angle: 0 = fingers down, 90 = left,
    180 = up) off frame: a tapered tube in the character's top colour with a cuff band and a shade side."""
    cl = CH.CAST[who].get('cloth', {})
    c, csh = cl.get('top', '#555555'), cl.get('top_sh', '#333333')
    a = math.radians(ang)
    dx, dy = -math.sin(a), math.cos(a)                 # the direction the fingers point
    pts = [(x - dx * size * f, y - dy * size * f) for f in (0.02, 0.6, 1.6, length / max(1.0, size))]
    tube = CH._tube(pts, [0.42 * size, 0.5 * size, 0.62 * size, 0.8 * size], 0.9)
    pen.shape(tube, c, max(3.0, size * 0.016))
    nx, ny = -dy, dx
    sh_ = CH._tube([(px + nx * size * 0.16, py + ny * size * 0.16) for px, py in pts], [0.14 * size, 0.18 * size, 0.24 * size, 0.3 * size], 0.9)
    pen.cv.save(); pen.cv.clipPath(tube, skia.ClipOp.kIntersect, True); pen.fill(sh_, csh, 150); pen.cv.restore()
    cuff = CH._tube([(x - dx * size * 0.04, y - dy * size * 0.04), (x - dx * size * 0.24, y - dy * size * 0.24)], [0.46 * size, 0.5 * size], 0.9)
    pen.shape(cuff, cl.get('top_hi', c), max(3.0, size * 0.014))


def B_hands(F, sh):
    """Hand close-ups over a blurred set: mode 'squeeze' (Grandpa's old hand closing over yours, three squeezes: squeeze=[t]),
    'grab' (the real Walter's hand clamps your wrist), 'find' (Mom's hand finds yours on the couch), 'catch' (your hand
    catches Mom's wrist on the dummy). Every squeeze / grab returns its sound."""
    p = sh.p
    mode = p.get('mode', 'squeeze')
    bgn = p.get('bg', {'squeeze': 'memory_bed', 'grab': 'hospital', 'find': 'living', 'catch': 'den'}[mode])
    sp, light, gr = _bg(F, sh, bgn, p)
    t0 = sh.t0
    tg = p.get('tg', t0 + 0.4)
    sq = p.get('squeeze', [])

    def pulse(t):
        v = 0.0
        for s_ in sq:
            u = t - s_
            if 0 <= u < 0.4: v = max(v, math.sin(math.pi * u / 0.4))
        return v

    def draw(pen, t):
        shake = p.get('shake', 0.0)
        jx = shake * (4 * math.sin(t * 43) + 2 * noise1(t * 9, 3)); jy = shake * (3 * math.sin(t * 37 + 1))
        if mode == 'squeeze':
            yx, yy = 1000, 760                                                    # your small hand on the quilt
            _sleeve(pen, 'you', yx + 60, yy - 140, 200, 300)
            CH.draw_hand(pen, 'you', yx, yy, 300, 'relaxed', 200.0, -1)
            u = ease_out_cubic(clamp((t - tg) / 0.7))
            gx, gy = lerp(1500, 1040, u), lerp(250, 640, u) + 14 * pulse(t)
            _sleeve(pen, 'grandpa', gx + 50, gy - 120, 145, 380)
            CH.draw_hand(pen, 'grandpa', gx, gy, 380, 'grip' if pulse(t) > 0.3 else 'relaxed', 145.0 + 6 * pulse(t), 1)
        elif mode == 'grab':
            yx, yy = 980, 700
            _sleeve(pen, 'you', yx - 100, yy - 160, 235, 320)
            CH.draw_hand(pen, 'you', yx, yy, 320, 'open', 235.0, -1)
            u = ease_out_cubic(clamp((t - tg) / 0.16))
            gx, gy = lerp(1650, 930 + jx, u), lerp(1200, 620 + jy, u)
            _sleeve(pen, 'grandpa_bed', gx + 80, gy + 150, 20, 360)
            CH.draw_hand(pen, 'grandpa_bed', gx, gy, 360, 'grip' if u > 0.85 else 'open', 20.0, 1)
        elif mode == 'find':
            yx, yy = 980, 700
            _sleeve(pen, 'you', yx - 80, yy - 120, 215, 300)
            CH.draw_hand(pen, 'you', yx, yy, 300, 'relaxed', 215.0, -1)
            u = ease_in_out(clamp((t - tg) / 1.1))
            mx, my = lerp(1600, 1050, u), lerp(900, 690, u)
            _sleeve(pen, 'mom', mx + 90, my + 60, 60, 320)
            CH.draw_hand(pen, 'mom', mx, my, 320, 'grip' if u > 0.9 else 'relaxed', 60.0, 1)
        else:                                                                     # catch: Mom's wrist on the dummy
            u = 1.0 - 0.15 * math.sin((t - t0) * 9.0) * clamp((tg - t) / 0.4)
            mx, my = 900 + jx, 640 + jy
            _sleeve(pen, 'mom', mx - 90, my - 150, 210, 330)
            CH.draw_hand(pen, 'mom', mx, my, 330, 'grip', 210.0, -1)
            c = ease_out_cubic(clamp((t - tg) / 0.22))
            if c > 0:
                yx, yy = lerp(1550, mx + 120, c), lerp(1150, my - 90, c)
                _sleeve(pen, 'you', yx + 70, yy + 120, 30, 340)
                CH.draw_hand(pen, 'you', yx, yy, 340, 'grip' if c > 0.85 else 'open', 30.0, 1)
    lay = Layer(0.95, draw, 'hands', blur=0)
    cam = cam_from(F, sh, p.get('cam'), dict(mv='push', x=980, y=600, z=1.05, rate=0.045))
    if mode == 'grab': cam.hit(tg + 0.16, 6.0)
    if mode == 'squeeze':
        for s_ in sq: sh.sfx.append(_ev(s_, 'hand_squeeze', -9, 0.1, 'close', who='grandpa'))
    elif mode == 'grab':
        sh.sfx.append(_ev(tg + 0.14, 'cloth_rustle', -2, 0.2, 'close', kind='grab'))
    elif mode == 'find':
        sh.sfx.append(_ev(tg + 0.9, 'cloth_rustle', -14, 0.2, 'close', kind='touch'))
    else:
        sh.sfx.append(_ev(tg + 0.2, 'cloth_rustle', -4, 0.2, 'close', kind='grab'))
    grade = p.get('grade', gr if gr not in ('gp_dark',) else 'face_close')
    return Spec(sp.add(lay), cam, None, grade, 1.0, 6.75, fx=_fx(sp, p), hud=p.get('hud'))


def B_ins(F, sh):
    """Prop insert (sets.gp_insert): push at 4.5 %/s (dolly) plus a uniform post push, so the prop itself visibly grows."""
    p = sh.p
    sp = ST.insert(p['name'], t0=sh.t0, prop_kw=p.get('kw'), motion=p.get('motion'), hand=p.get('hand'))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = 0.045
    cam = cam_from(F, sh, cd)
    if sp.lens is None and cd.get('mv') != 'keys': cam.post_push(sh.t0, sh.t1, 1.0, (1.02) ** max(0.3, sh.d), ease='push')
    grade = p.get('grade', sp.grade or 'face_close')
    return Spec(sp, cam, sp.lens, grade, sp.focus, sp.dof, fx=_fx(sp, p), hud=p.get('hud'))


def B_black(F, sh):
    return Spec([], None, None, 'neutral', 1.0, 0.0, fx=lambda t: dict(sh.p.get('post', {})), hud=None)


RED_ICON = '#e3262e'


def _icon(n):
    """Small white line icons for the rule cards: f(pen, x, y, size, alpha)."""
    def f(pen, x, y, sz, a):
        k = sz / 120.0; w = 7 * k
        if n == 1:                                                          # the case with a padlock
            pen.line(rrect(x - 52 * k, y - 26 * k, 104 * k, 64 * k, 8 * k), w, '#ffffff', a)
            pen.line(smooth([(x - 16 * k, y - 26 * k), (x - 16 * k, y - 46 * k), (x + 16 * k, y - 46 * k), (x + 16 * k, y - 26 * k)], False), w * 0.8, '#ffffff', a)
            pen.fill(rrect(x - 12 * k, y - 4 * k, 24 * k, 20 * k, 4 * k), RED_ICON, a)
        elif n == 2:                                                        # a speech bubble with a voice wave
            pen.line(rrect(x - 52 * k, y - 40 * k, 104 * k, 64 * k, 14 * k), w, '#ffffff', a)
            pen.line(poly([(x - 20 * k, y + 24 * k), (x - 30 * k, y + 46 * k), (x, y + 24 * k)], False), w, '#ffffff', a)
            for j, hh in enumerate((10, 22, 14, 26, 8)):
                xx = x - 30 * k + j * 15 * k
                pen.seg((xx, y - 8 * k - hh * k / 2), (xx, y - 8 * k + hh * k / 2), w * 0.6, RED_ICON if j == 3 else '#ffffff', a)
        elif n == 3:                                                        # a laughing mouth, crossed
            pen.line(smooth([(x - 44 * k, y - 12 * k), (x, y + 30 * k), (x + 44 * k, y - 12 * k)], False), w, '#ffffff', a)
            pen.seg((x - 44 * k, y - 12 * k), (x + 44 * k, y - 12 * k), w, '#ffffff', a)
            pen.seg((x - 54 * k, y + 50 * k), (x + 54 * k, y - 50 * k), w, RED_ICON, a)
        elif n == 4:                                                        # a hand going into a slot, crossed
            pen.line(rrect(x - 12 * k, y - 50 * k, 24 * k, 60 * k, 6 * k), w * 0.8, '#ffffff', a)
            pen.line(smooth([(x - 30 * k, y + 52 * k), (x - 24 * k, y + 10 * k), (x - 4 * k, y - 4 * k), (x + 22 * k, y + 8 * k), (x + 28 * k, y + 52 * k)], False),
                     w * 0.8, '#ffffff', a)
            pen.seg((x - 54 * k, y + 52 * k), (x + 54 * k, y - 52 * k), w, RED_ICON, a)
        elif n == 5:                                                        # closed lips with a sound coming out
            pen.line(smooth([(x - 46 * k, y), (x - 20 * k, y - 16 * k), (x, y - 8 * k), (x + 20 * k, y - 16 * k), (x + 46 * k, y)], False), w, '#ffffff', a)
            pen.line(smooth([(x - 46 * k, y), (x, y + 22 * k), (x + 46 * k, y)], False), w, '#ffffff', a)
            for j in range(3):
                pen.line(smooth([(x + 52 * k + j * 12 * k, y - 18 * k - j * 6 * k), (x + 60 * k + j * 12 * k, y), (x + 52 * k + j * 12 * k, y + 18 * k + j * 6 * k)], False),
                         w * 0.6, RED_ICON, a)
        elif n == 6:                                                        # a knee with a little figure on it
            pen.line(smooth([(x - 54 * k, y + 40 * k), (x - 10 * k, y + 10 * k), (x + 50 * k, y + 14 * k)], False), w, '#ffffff', a)
            pen.line(oval(x + 8 * k, y - 34 * k, 14 * k), w * 0.8, '#ffffff', a)
            pen.seg((x + 8 * k, y - 20 * k), (x + 8 * k, y + 8 * k), w * 0.8, '#ffffff', a)
            pen.fill(oval(x + 8 * k, y - 34 * k, 5 * k), RED_ICON, a)
        else:                                                               # a crescent moon, crossed (no goodnight)
            pen.line(minus(oval(x, y, 40 * k), oval(x + 18 * k, y - 12 * k, 34 * k)), w * 0.8, '#ffffff', a)
            pen.seg((x - 54 * k, y + 52 * k), (x + 54 * k, y - 52 * k), w, RED_ICON, a)
    return f


def B_rule(F, sh):
    """Rule card over a dimmed, blurred LIVE scene (the police style). recall=True: a card recalled later (rule two's
    'LIE?' flicker, rule six torn by the lie: mode / reveal), which does not change the header."""
    p = sh.p
    n = p['n']; text_ = RULES[n]
    bgk = p.get('bg', 'hall')
    sp, light, gr = _bg(F, sh, bgk, dict(p, bg_dim=0.0))
    L = []
    if p.get('ghost'):
        L, _ = people(F, sh, sp, p['ghost'], light)
    cam = mkcam(sh, 'push', 960, 540, 1.03, rate=push_rate(sh.t0))
    t0 = sh.t0
    icon = _icon(n)
    mode, reveal = p.get('mode'), p.get('reveal')

    def hud(cv, t):
        if mode:
            ST.rule_card_lie(cv, n, text_, t - t0, reveal=None if reveal is None else reveal - t0, mode=mode, icon=icon)
        else:
            H.rule_card(cv, n, text_, t - t0, icon=icon)
    if bgk == 'studio': sh.p.setdefault('era', 'tape')

    def fx(t):
        d = dict(sp.fx(t) or {}, blur=6, dim=0.35)
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(*L), cam, None, gr if gr not in ('face_close',) else 'gp_house', 1.0, 0.0, fx=fx, hud=hud)


BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}


# ==================================================================================================== spaces + per-shot cues
SPACE = {'hall': 'inside', 'hdoor': 'inside', 'stairs': 'inside', 'kitchen': 'inside', 'living': 'inside', 'den': 'inside',
         'studio': 'tv', 'hospital': 'hospital', 'stage62': 'memory', 'museum': 'museum', 'street': 'inside', 'bedroom': 'inside',
         'lap': 'close', 'carry': 'close', 'portrait': 'close', 'hands': 'close', 'ins': 'close', 'rule': None, 'black': None}
LOC = {'hall': 'house', 'hdoor': 'house', 'stairs': 'house', 'kitchen': 'house', 'living': 'house', 'den': 'house', 'studio': 'tape',
       'hospital': 'hospital', 'stage62': '1962', 'museum': 'museum', 'street': 'house', 'bedroom': 'home'}
BG_LOC = {'studio': 'tape', 'hospital': 'hospital', 'stage62': '1962', 'museum': 'museum', 'bedroom': 'home', 'memory_bed': 'memory',
          'memory_kitchen': 'memory'}


def shot_loc(s):
    if s.p.get('era') == 'memory': return 'memory'
    if s.kind in LOC: return LOC[s.kind]
    return BG_LOC.get(s.p.get('bg'), 'house')


def shot_space(s):
    if s.kind in ('bust', 'lap', 'carry', 'hands'):
        return {'studio': 'tv', 'hospital': 'hospital', 'museum': 'museum', 'memory_bed': 'memory', 'memory_kitchen': 'memory',
                'stage62': 'memory'}.get(s.p.get('bg'), 'close')
    return SPACE.get(s.kind)


def shot_common(F, sh, spec):
    """Collect the shot's SFX / music events from its acting, camera, tags and explicit cue lists."""
    p = sh.p
    space = shot_space(sh)
    for a in sh.actors:
        for e in a.events:
            if sh.t0 - 0.05 <= e['t'] <= sh.t1 + 0.4 and e['name']:
                pr = dict(e.get('params') or {})
                if e.get('who'): pr['who'] = e['who']
                if p.get('era') in ('memory', 'tape', '1962'): pr['era'] = p['era']
                sh.sfx.append(_ev(e['t'], e['name'], e.get('gain_db', 0.0), e.get('pan', 0.0), space, **pr))
    if (p.get('cam') or {}).get('snap'):
        sh.sfx.append(_ev(p['cam']['snap'][0], 'whoosh', -3, 0, None, kind='hard'))
    elif (p.get('cam') or {}).get('mv') == 'pull':
        sh.sfx.append(_ev(sh.t0 + 0.02, 'whoosh', -4, 0, None, kind='soft'))
    for tg in p.get('tags', []):
        if p.get('tag_sound', True): sh.sfx.append(_ev(tg[0], 'ui_pop', -6, 0, 'close'))
    if p.get('cut') in ('static', 'glitch'):
        sh.sfx.append(_ev(sh.t0, 'glitch', -4, 0, None, dur=0.25, amount=0.8))
    if p.get('cut') == 'white' and not p.get('quiet_cut'):
        sh.sfx.append(_ev(sh.t0, 'impact_hit', 0, 0, None, size=1.1))
    if p.get('hit'):
        for h in (p['hit'] if isinstance(p['hit'], (list, tuple)) else [p['hit']]):
            sh.sfx.append(_ev(h, 'impact_hit', -2, 0, None, size=1.0))
            sh.music.append({'t': round(h, 3), 'type': 'hit', 'level': 0.75})
    for c in p.get('sfx', []):                   # explicit (t, name, gain, pan, space, params)
        t, name = c[0], c[1]
        g = c[2] if len(c) > 2 else 0.0; pan = c[3] if len(c) > 3 else 0.0
        sp_ = c[4] if len(c) > 4 else space
        pr = c[5] if len(c) > 5 else {}
        sh.sfx.append(_ev(t, name, g, pan, sp_, **pr))
    for m in p.get('music', []):
        e = {'t': round(m[0], 3), 'type': m[1], 'level': m[2] if len(m) > 2 else 0.7}
        if len(m) > 3: e['len'] = m[3]
        sh.music.append(e)
    if sh.kind == 'rule':
        tm = H.rule_times(RULES[sh.p['n']])
        sh.sfx.append(_ev(sh.t0 + tm['pop'], 'ui_pop', 0, 0, 'close'))
        if not p.get('recall'):
            sh.sfx.append(_ev(sh.t0 + tm['type0'], 'typing', -6, 0, 'close', dur=round(tm['type1'] - tm['type0'], 2), cps=14))
            sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.75})
            sh.music.append({'t': round(sh.t0, 3), 'type': 'riser', 'level': 0.55, 'len': 4.0})
        if p.get('reveal') is not None:
            sh.sfx.append(_ev(p['reveal'], 'rule_lie', 0, 0, 'close', mode=p.get('mode')))
            sh.music.append({'t': round(p['reveal'], 3), 'type': 'stinger' if p.get('mode') != 'flicker' else 'hit', 'level': 0.9})
    if sh.kind == 'hospital':                        # the heart monitor: one beep per beat while it runs, the flatline tone
        for tb in ST.monitor_beeps(sh.t0, sh.t1, p.get('bpm', 72.0), p.get('flat')):
            sh.sfx.append(_ev(tb, 'heart_monitor', -12 if sh.p.get('view', 'bed') == 'bed' else -9, 0.35, 'hospital', kind='beep'))
        if p.get('flat') is not None and sh.t0 <= p['flat'] < sh.t1 + 0.2:
            sh.sfx.append(_ev(p['flat'], 'heart_monitor', -6, 0.35, 'hospital', kind='flatline', dur=round(max(1.0, sh.t1 - p['flat'] + 1.5), 2)))
    if sh.kind in ('hall',) and isinstance(p.get('beam'), dict) and p['beam'].get('on') is not None and sh.t0 - 0.05 <= p['beam']['on'] < sh.t1:
        sh.sfx.append(_ev(p['beam']['on'], 'flashlight_click', -4, 0.0, 'inside', kind='on', far=True))
    tags = p.get('tags')
    if tags:
        prev = spec.hud

        def hud(cv, t, prev=prev, tags=tags):
            if prev: prev(cv, t)
            for tg in tags:
                t0, txt, x, y, style = tg[:5]
                hold_ = tg[5] if len(tg) > 5 else (1.2 if style == 'alert' else 2.6)
                if t0 <= t <= t0 + hold_: H.tag(cv, txt, x, y, style, t - t0)
        spec.hud = hud


EXPO = {'hall': -0.2, 'hdoor': -0.2, 'stairs': 0.0, 'kitchen': -0.2, 'living': -0.15, 'den': -0.15, 'ins': -0.1, 'hands': -0.1}


def glob_fx(F, sh, t, fx):
    """Per-frame global effects: scare-cut flashes, the night creeping into red over the last 35 %, the climax ramp with the
    red heartbeat wash (Mom's scream to Owen's eyes closing), the end fade."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.1: fx['white'] = 0.85 * (1 - u / 0.1)
    ek = EXPO.get(sh.kind, 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    era = sh.p.get('era', 'now')
    clean = era in ('memory', '1962', 'later') or sh.kind in ('rule', 'black', 'studio') or (T_8AM <= t < T_HOME)
    if not clean:
        ui = 0.5 if sh.kind in ('ins', 'hands') or era == 'tape' else 1.0
        # the last 35 %: darker, redder, more saturated; a faster ramp from Mom's scream into the goodnight; the reveal
        # holds it; the doorway at the very end creeps back in
        k = clamp((t - 460.0) / 80.0) if t < T_8AM else clamp((t - 696.0) / 8.0)
        k2 = clamp((t - 543.7) / 12.0) * (1.0 - 0.45 * clamp((t - 575.0) / 8.0)) if t < T_8AM else 0.0
        if k > 0:
            fx['red'] = fx.get('red', 0.0) + (0.42 * k + 0.32 * k2) * ui
            fx['sat'] = fx.get('sat', 1.0) * (1 + (0.5 * k + 0.3 * k2) * ui)
            fx['exposure'] = fx.get('exposure', 0.0) - (0.35 * k + 0.45 * k2) * ui
        # the heartbeat: a red wash pulsing in from the frame edge, faster and stronger until Owen's eyes close
        if 543.7 <= t < T_SWAP + 0.4 and 'flash' not in fx:
            bpm = lerp(78, 132, clamp((t - 543.7) / 22.0))
            ph = ((t - 543.7) * bpm / 60.0) % 1.0
            beat = math.exp(-ph * 9.0) + 0.6 * math.exp(-max(0.0, ph - 0.18) * 11.0) * (ph >= 0.18)
            fx['flash'] = _epost.Spill(0.42 * clamp((t - 543.7) / 3.0) * clamp(beat) * ui, side=-1.0 if sh.idx % 2 else 1.0,
                                       color=(0.06, 0.08, 0.9), reach=0.8)
    if t > F.duration - 2.6: fx['fade'] = clamp((t - (F.duration - 2.6)) / 1.6)
    if t < 0.35: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.35)


# ==================================================================================================== beds + music curve
def beds(F):
    """Ambience beds: the old house at night (room tone, the wind round the eaves), the grandfather clock ticking in the hall,
    the tape's TV hiss and crowd murmur while the TV is on, the hospital's corridor hum, 8 AM street, the museum hush."""
    out = []
    D = F.duration
    house = [(110.61, T_8AM)]
    out.append(_ev(0.0, 'room_tone', -6, 0, 'inside', dur=round(D, 1)))
    out.append(_ev(110.61, 'ambience_night', -10, 0, 'outside', dur=round(T_8AM - 110.61, 1), wind=0.6, crickets=0.3, dog=0.1, house=True))
    # the hall clock: heard through the whole house at night, louder in the hall shots (one bed, phase-locked to the pendulum)
    out.append(_ev(110.61, 'clock_tick', -16, -0.2, 'inside', dur=round(T_8AM - 110.61, 1), bpm=60, phase=0.5, kind='grandfather'))
    for sh in F.shots:
        if sh.kind == 'hall' or (sh.kind == 'bust' and sh.p.get('bg') in ('hall', 'hall_dark')):
            out.append(_ev(sh.t0, 'clock_tick', -9, -0.2, 'inside', dur=round(sh.d, 2), bpm=60, phase=0.5, kind='grandfather', near=True))
    # the TV: the tape's hiss and the crowd under the narration while it plays (the laughter waves are separate events)
    out.append(_ev(T_TV_ON, 'tv_bed', -12, -0.3, 'tv', dur=round(471.6 - T_TV_ON, 1), kind='vhs_hiss_crowd'))
    out.append(_ev(75.9, 'room_tone', -8, 0, 'hospital', dur=round(110.6 - 75.9, 1), kind='hospital_hum'))
    out.append(_ev(486.0, 'room_tone', -8, 0, 'hospital', dur=12.0, kind='hospital_hum'))
    out.append(_ev(632.6, 'room_tone', -8, 0, 'hospital', dur=14.6, kind='hospital_hum'))
    out.append(_ev(T_8AM, 'ambience_morning', -6, 0.2, 'outside', dur=round(T_MUSEUM - T_8AM, 1), birds=0.6, traffic=0.3))
    out.append(_ev(T_MUSEUM, 'room_tone', -6, 0, 'museum', dur=round(T_HOME - T_MUSEUM, 1), kind='gallery_hush'))
    return out


INTENSITY = [  # (seconds, level): the story's tension, read off the beats
    (0.0, 0.5), (4.3, 0.55), (10.2, 0.45), (16.3, 0.55), (18.6, 0.4), (26.6, 0.5), (31.3, 0.6), (33.0, 0.35), (39.6, 0.4),
    (47.6, 0.5), (50.3, 0.3), (61.5, 0.4), (68.2, 0.35), (73.9, 0.45), (76.0, 0.4), (86.6, 0.5), (96.9, 0.75), (104.2, 0.85),
    (106.8, 0.6), (110.6, 0.35), (118.8, 0.4), (124.4, 0.5), (131.1, 0.55), (134.7, 0.65), (139.2, 0.6), (147.0, 0.35),
    (151.7, 0.45), (155.3, 0.7), (159.2, 0.75), (162.7, 0.6), (164.9, 0.72), (169.4, 0.65), (174.0, 0.8), (181.0, 0.6),
    (184.4, 0.7), (188.3, 0.75), (192.3, 0.6), (199.0, 0.6), (210.4, 0.4), (215.3, 0.5), (218.4, 0.62), (221.9, 0.7), (229.7, 0.75),
    (233.9, 0.7), (238.8, 0.72), (243.5, 0.9), (247.1, 0.85), (250.4, 0.95), (257.8, 0.9), (258.4, 0.6), (264.9, 0.55),
    (271.3, 0.62), (277.5, 0.7), (278.9, 0.45), (283.5, 0.6), (286.6, 0.85), (290.2, 0.75), (292.4, 0.7), (294.9, 0.8),
    (299.6, 0.6), (305.2, 0.7), (312.3, 0.8), (314.7, 0.92), (320.7, 0.8), (324.1, 0.85), (325.3, 0.95), (327.6, 0.9),
    (333.2, 0.6), (338.1, 0.45), (351.8, 0.6), (354.6, 0.85), (359.0, 0.9), (360.2, 0.75), (367.7, 0.85), (373.7, 0.7),
    (378.0, 0.62), (384.6, 0.72), (396.0, 0.8), (397.6, 0.85), (401.9, 0.9), (404.7, 0.6), (409.4, 0.6), (415.0, 0.6),
    (417.9, 0.82), (420.6, 0.9), (423.1, 1.0), (428.5, 0.8), (434.1, 0.6), (439.9, 0.7), (445.3, 0.8), (448.6, 0.92),
    (457.5, 0.95), (462.2, 0.85), (469.4, 0.7), (476.9, 0.8), (478.4, 0.75), (486.2, 0.65), (492.5, 0.7), (498.1, 0.6),
    (503.8, 0.5), (506.3, 0.6), (518.4, 0.55), (521.4, 0.8), (523.4, 0.85), (532.9, 0.75), (539.1, 0.92), (543.7, 1.0),
    (552.3, 0.92), (555.0, 0.85), (559.8, 0.9), (565.9, 1.0), (567.1, 0.75), (569.1, 0.85), (570.3, 0.6), (575.5, 0.5),
    (578.5, 0.45), (582.2, 0.6), (589.3, 0.7), (594.5, 0.8), (598.2, 0.7), (608.7, 0.85), (615.5, 0.8), (619.3, 0.6),
    (627.8, 0.8), (631.1, 0.9), (632.7, 0.65), (643.5, 0.75), (647.3, 0.8), (651.1, 0.95), (655.5, 0.85), (660.2, 1.0),
    (663.2, 0.7), (665.1, 0.35), (673.8, 0.4), (677.4, 0.5), (682.1, 0.55), (688.7, 0.6), (691.1, 0.65), (693.8, 0.7),
    (696.9, 0.8), (701.9, 0.9), (703.3, 1.0), (706.4, 0.95), (707.4, 0.5)]


def intensity_curve(F):
    pts = [[round(t, 2), round(v, 3)] for t, v in INTENSITY]
    pts.append([round(F.duration, 2), 0.0])
    return pts


HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs before the big scares (the music goes out and the room tone is left)
EXTRA_SIL = [(154.0, 1.3), (167.4, 1.4), (242.3, 1.2), (249.2, 1.2), (293.6, 1.4), (325.0, 0.9), (366.3, 1.4), (420.4, 1.0),
             (447.4, 1.2), (456.4, 1.0), (520.6, 0.8), (564.6, 1.2), (568.9, 1.4), (650.0, 1.0), (659.9, 0.8), (702.0, 1.2)]
WHOOSH_GAP = 40.0


def polish_cues(F, sfx, mus):
    """Cue-sheet pass after the shots (police film): hits land on the reveal cut, braams leave the reveal line clear,
    whooshes are rationed, silences sit before the big scares, swells breathe, duplicates are merged."""
    cuts = sorted(sh.t0 for sh in F.shots)
    snaps = [sh.p['cam']['snap'][0] for sh in F.shots if (sh.p.get('cam') or {}).get('snap')]
    lines = [(l['t'], l['end']) for l in F.L]

    def line_at(t):
        for a, b in lines:
            if a - 0.02 <= t <= b: return (a, b)
        return None

    def retime(t):
        if any(abs(t - sn) < 0.06 for sn in snaps): return t
        prev = [c for c in cuts if 0.0 < t - c <= 0.25]
        if prev: return max(prev)
        ln = line_at(t); nxt = [c for c in cuts if 0.0 < c - t <= 0.35]
        if ln and nxt and ln[1] <= nxt[0] + 0.02: return min(nxt)
        return t

    for e in sfx:
        if e['name'] in HIT_SFX: e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] in HIT_MUS: e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] != 'braam': continue
        ln = line_at(e['t'] + 0.02)
        if ln and ln[0] < e['t'] - 0.02:
            nxt = [c for c in cuts if ln[1] - 0.05 <= c <= ln[1] + 1.0]
            e['t'] = round(min(nxt) if nxt else ln[1] + 0.05, 3)

    ht = [e['t'] for e in mus if e['type'] in HIT_MUS] + [e['t'] for e in sfx if e['name'] in HIT_SFX]
    wh = [e for e in sfx if e['name'] == 'whoosh' and (e.get('params') or {}).get('kind') != 'soft' or e['name'] == 'whoosh' and not e.get('params')]
    pri = lambda e: (0 if any(abs(e['t'] - sn) < 0.06 for sn in snaps) else 1 if any(abs(e['t'] - h) < 0.4 for h in ht) else 2)
    keep = []
    for e in sorted(wh, key=lambda e: (pri(e), e['t'])):
        if all(abs(e['t'] - k['t']) >= WHOOSH_GAP for k in keep): keep.append(e)
    kid = set(map(id, keep)) | set(id(e) for e in sfx if e['name'] == 'whoosh' and e not in wh)
    sfx = [e for e in sfx if e['name'] != 'whoosh' or id(e) in kid]

    for t, ln in EXTRA_SIL:
        if not any(e['type'] == 'silence' and abs(e['t'] - t) < 3 for e in mus):
            mus.append({'t': t, 'type': 'silence', 'level': 0.0, 'len': ln})
    hts = sorted(e['t'] for e in mus if e['type'] in HIT_MUS + ('rule',))
    for e in mus:
        if e['type'] != 'silence': continue
        ln = max(1.0, float(e.get('len', 1.4)))
        h = [x for x in hts if e['t'] < x <= e['t'] + ln + 0.6]
        if h:
            end = min(h) - 0.04
            start = max(end - ln, e['t'] - 1.2)
            e['t'] = round(start, 3); ln = end - start
        e['len'] = round(max(0.6, ln), 2)

    for e in mus:
        if e['type'] == 'swell' and float(e.get('len', 12)) < 12:
            pk = e['t'] + float(e.get('len', 6)); e['len'] = 13.0; e['t'] = round(max(0.5, pk - 13.0), 3)
    peaks = [e['t'] + e['len'] for e in mus if e['type'] == 'swell']
    sil = [(e['t'], e['t'] + e['len']) for e in mus if e['type'] == 'silence']
    want = int(F.duration / 60 * 2.5)
    iv = intensity_curve(F)
    for t, v in sorted(iv, key=lambda p: -p[1]):
        if len(peaks) >= want: break
        if t < 16 or t > F.duration - 4: continue
        if any(abs(t - q) < 20 for q in peaks) or any(a - 0.5 <= t <= b + 0.5 for a, b in sil): continue
        mus.append({'t': round(t - 13.0, 3), 'type': 'swell', 'level': 0.5, 'len': 13.0}); peaks.append(t)

    out = []
    kk = lambda e: (e['name'], str(e.get('space')), str((e.get('params') or {}).get('who')))
    for e in sorted(sfx, key=lambda e: kk(e) + (e['t'],)):
        if out and kk(out[-1]) == kk(e) and e['t'] - out[-1]['t'] < 0.06:
            if e['gain_db'] > out[-1]['gain_db']: out[-1] = e
            continue
        out.append(e)
    mo = []
    for e in sorted(mus, key=lambda e: (e['type'], e['t'])):
        if mo and mo[-1]['type'] == e['type'] and e['type'] != 'silence' and e['t'] - mo[-1]['t'] < 0.06:
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
    C, t, w = F.cut, F.t, F.w
    LAUGH_T[:] = [303.0, 305.6, 309.6, 312.2, 313.5, 314.8]
    C(0.0, 'hall', winks=True, ppl=[P('mom', at='bench_stand'), P('owen', at=('h', -0.2, 1.7)), P('you', at=('h', 0.3, 1.5))])
    C(3.0, 'hall', winks=True, cam=dict(mv='keys', keys=[(3.0, 960, 560, 1.0, None, 1.0), (6.0, 900, 560, 1.15, 'in_out', 2.6)]))
    C(6.0, 'hdoor', door=0.85, ppl=[P('mom', at='mid'), P('owen', at='bench_stand')])
    C(9.0, 'stairs', winks=dict(act=lambda a, s: (a.sit_dummy(hands='knees'), a.torch_on(9.3, 0.0, -1, hold='lens'))))
    C(12.0, 'kitchen', view='table', winks=True, ppl=[P('mom', at='beside', act=lambda a, s: a.smell_mug(12.5, None, -1, pale_at=13.5))])
    C(15.0, 'kitchen', view='chair', winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.glove_lift(15.5))))
    C(18.0, 'living', view='tv', winks=dict(act=winks_chair(look=0.85)))
    C(21.0, 'living', view='tv', tv=dict(on=20.0, snow=0.0), lamp=0.25, winks=dict(act=winks_chair(look=0.0)))
    C(24.0, 'living', view='couch', ppl=[P('owen', at='couch_r', act=_A(sitp(), setp(turn=0.5))), P('you', at='couch_m', act=_A(sitp(), setp(turn=0.35))),
                                         P('mom', at='couch_l', act=_A(sitp(), setp(turn=-0.5)))],
      winks=dict())
    C(27.0, 'den', lap=dict(who='owen', act=lambda a, s: a.vent_pose(side=1), dact=lambda a, s: a.puppet(26, 31, look=-1)),
      ppl=[P('mom', at='mom'), P('you', at=('h', 0.45, 1.85), act=_A(turned(1.55), lambda a, s: a.kneel(27.0)))])
    C(30.0, 'den', rug=True, lamp=1.0)
    C(33.0, 'studio')
    C(36.0, 'hospital', lap=True, ppl=[P('you', at='bedside', act=turned(-0.6))])
    C(39.0, 'hospital', view='close', bed='walter', dummy='bed', ppl=[P('you', at='bedside')])
    C(42.0, 'stage62')
    C(45.0, 'museum', act=lambda a, s: a.smile_stage(-9, 'owen'))
    C(48.0, 'street', van=dict(drive=('out', 48.5, 51.0, -5.5, -14.0)), ppl=[P('owen_new', at='owen', act=_A(turned(2.0), lambda a, s: a.wave(48.2, 51)))])
    C(51.0, 'street', view='outside', ppl=[P('owen_new', at='owen_window', act=lambda a, s: a.wave(51.2, 54))])
    C(54.0, 'bedroom', ppl=[P('owen_new', at='doorway')])
    C(57.0, 'bust', who='winks', bg='kitchen')
    C(60.0, 'bust', who='mom', bg='living', ghost=[dict(who='winks', at='bookcase_top', act=_A(lambda a, s: a.sit_dummy(hands='limp'),
                                                                                                lambda a, s: a.torch_on(60.0, 0, 1, hold='chin')), light=TORCH)])
    C(63.0, 'lap', who='owen', bg='den', x=880, y=980, h=1350, act=lambda a, s: a.vent_pose(side=1), dact=lambda a, s: a.puppet(62, 67, look=-1))
    C(66.0, 'carry', act=None, dact=lambda a, s: a.smile_stage(-9, 'owen'))
    C(69.0, 'portrait', cam=dict(mv='keys', keys=[(69.0, 960, 900, 1.0), (72.0, 960, 2000, 1.0)]),
      act=lambda a, s: a.torch_on(70.5, 30.0, 1, hold='side'))
    C(72.0, 'hands', mode='squeeze', squeeze=[73.0, 73.5, 74.0])
    C(75.0, 'hands', mode='grab', tg=75.3)
    C(78.0, 'ins', name='letter', kw=dict(hl=4))
    C(81.0, 'rule', n=6, bg='den')
    C(84.0, 'rule', n=6, bg='den', recall=True, mode='tear', reveal=85.5)
    C(87.0, 'bust', who='walter74', bg='studio', cam=dict(mv='push', x=960, y=560))
    C(90.0, 'black')


def plan_film(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    Y, M, O, ON = 'you', 'mom', 'owen', 'owen_new'
    G = F.globals

    def KP(t0, t1, x0, y0, f0, x1, y1, f1, z0=1.0, z1=1.06, ease='in_out', shake=1.4):
        """One continuous interior move: dolly z0 -> z1 (<= 1.3) and optical zoom f0 -> f1."""
        return dict(mv='keys', shake=shake, keys=[(t0, x0, y0, z0, None, f0), (t1, x1, y1, z1, ease, f1)])
    plan_open(F, t, e, w, C, T, KP)
    plan_night(F, t, e, w, C, T, KP)
    plan_rules34(F, t, e, w, C, T, KP)
    plan_rules56(F, t, e, w, C, T, KP)
    plan_end(F, t, e, w, C, T, KP)
    plan_globals(F, t, e, w, G)


TVL = dict(rim='#9fd0ff', rim_a=150, side=1, key=-0.2)           # the TV's blue light on faces
LIMP = lambda a, s: a.set(-9, None, 0.1, h_tilt=14.0, h_nod=0.12)
DOOR_WALK = []


def door_swing(t_open, dur=1.4, k0=0.0, k1=0.85):
    return lambda t: k0 + (k1 - k0) * ease_in_out(clamp((t - t_open) / dur))


def plan_open(F, t, e, w, C, T, KP):
    Y, M, O = 'you', 'mom', 'owen'
    # the studio audience: every laugh is applause, and applause lets him move (film clock; the kitchen dummy moves on them)
    LAUGH_T[:] = [11.4, 14.3, 35.3, 37.9, 64.4, 66.9, 302.95, 305.45, 309.2, 312.1, 313.45, 314.85, 316.9, 318.7, 321.0, 322.5,
                  443.6, 462.4, 464.5, 480.3, 485.0]
    # the tape's own voice under the narration (the joke replayed from the recording, low through the TV): the dummy's jaw on
    # the tape follows it, so young Walter's unmoving lips read against a talking dummy; it stops in the middle of the joke
    F.tv_voices = [(440.05, F.t(118), F.e(118), 99.0), (444.0, F.t(121), F.e(121), 0.62)]

    # ============================================================ COLD OPEN (0 - 75.9)
    # his glass eyes in the dark, the flashlight under his chin; a wooden wink on "jokes"
    C(0.0, 'bust', who='winks', bg='hall_dark', cx=960, cy=640, scale=1.45, ecu=True, light=TORCH, torch_glow=True,
      act=_A(stage(3), lambda a, s: a.wink(w(0, 'jokes') + 0.1)), cam=dict(mv='creep', x=960, y=500, z=1.0),
      music=[(0.2, 'motif', 0.5, 5)])
    C(T(1), 'ins', name='back_slot', kw=lambda tt: dict(hand=0.4 * ease_in_out(clamp((tt - 0.2) / 1.3))), cam=dict(mv='push', x=960, y=560, rate=0.05))
    # in Grandpa's chair under the flickering pendant: on "goodnight" the light dies and only his flashlight is left
    tg = w(2, 'goodnight')
    C(T(2), 'kitchen', view='chair', kitchen=dict(flick=[(T(2) + 0.7, 1.0), (tg - 0.45, 0.4)], out=[(tg + 0.05, 99.0)]), sway=0.03,
      winks=dict(act=_A(winks_chair(look=0.0), stage(3))), cam=KP(T(2), T(3), 960, 560, 1.0, 960, 520, 1.55, 1.0, 1.1),
      sfx=[(tg + 0.05, 'lamp_out', -3, 0.1, 'inside', dict(kind='pop')), (T(2) + 0.7, 'bulb_flicker', -10, 0.1, 'inside', dict(dur=1.0))])
    # the tape: two seats; one of them talks; the other one gets worked; it is very tired of being worked
    C(T(3), 'studio', track=0.5, cam=dict(mv='keys', keys=[(T(3), 960, 600, 1.0), (T(5), 990, 580, 1.2, 'in_out')]),
      music=[(T(3), 'theme', 0.3, 5.0)])
    C(T(5), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(5), 1010, 600, 1.6), (T(6), 1040, 610, 1.9, 'in_out')]))
    tg6 = w(6, 'tired')
    C(T(6), 'bust', who='winks', bg='studio', tape=True, cx=960, cy=580, scale=1.1,
      act=_A(lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.7), lambda a, s: a.smile_stage(tg6 + 0.1, 'tape', tg6 + 0.75, fade=0.05)),
      track_fn=lambda tt, a=tg6: 0.35 + 2.4 * math.exp(-max(0.0, tt - a - 0.1) * 4.0) * (tt > a + 0.05),
      cam=dict(mv='creep', x=960, y=520), sfx=[(tg6 + 0.1, 'tape_glitch', -6, 0, 'tv', dict(dur=0.7))])
    # the greatest ventriloquist who ever lived; sixty years and nobody saw his lips move
    C(T(7), 'ins', name='family_photo', cam=dict(mv='push', x=960, y=540, rate=0.04), music=[(t(7), 'motif', 0.5, 5)])
    C(T(8), 'bust', who='walter74', bg='studio', cx=960, cy=600, scale=1.15, act=lambda a, s: a.showman(s.t0 - 2, s.t1 + 2, look=0.3),
      cam=dict(mv='keys', keys=[(T(8), 960, 500, 1.0), (T(9), 960, 600, 1.35, 'in_out')]))
    C(T(9), 'bust', who='walter74', bg='studio', ecu=True, cx=960, cy=380, scale=1.7, act=lambda a, s: a.showman(s.t0 - 2, s.t1 + 2, look=0.0),
      cam=dict(mv='creep', x=960, y=560))
    # last week we buried him: the black case in the dark hall like a little coffin
    C(T(10), 'ins', name='latches', kw=dict(latch=0.0), cam=dict(mv='push', x=960, y=560, rate=0.035), music=[(t(10), 'silence', 0.0, 1.0)])
    # why his lips never moved: his jaw hangs open in the dark ... and clacks shut on "moved"
    tm = w(11, 'moved')
    C(T(11), 'bust', who='winks', bg='hall_dark', cx=960, cy=640, scale=1.25, light=TORCH, torch_glow=True,
      act=_A(stage(3), lambda a, s: a.jaw_hang(s.t0 - 1, 0.55), lambda a, s: a.clack(tm + 0.2, 0.09)),
      cam=dict(mv='creep', x=960, y=520), hit=tm + 0.2)
    C(T(12), 'ins', name='poster_1962', cam=dict(mv='push', x=960, y=520, rate=0.04))
    # Saturday mornings: from the TV's bezel into the cheerful show; on "Mister Winks" the dummy snaps round to the camera
    tmw = w(13, 'mr')
    C(T(13), 'studio', bezel=1.0, track=0.3, cam=dict(mv='keys', keys=[(T(13), 960, 560, 1.0), (w(13, 'dummy') - 0.1, 975, 575, 1.2, 'in_out')]),
      music=[(t(13), 'theme', 0.55, 6.0)])
    C(w(13, 'dummy') - 0.1, 'studio', track=0.3, cam=dict(mv='keys', keys=[(w(13, 'dummy') - 0.1, 1030, 600, 1.7), (e(13), 1040, 590, 2.0, 'in_out')]),
      d_act=lambda a, s: (a.puppet(s.t0 - 2, tmw - 0.3, look=-1, rate=0.8), a.head_snap(tmw + 0.1, 0.0)))
    # painted red hair, freckles, the usher's jacket and brass buttons, the little flashlight in one white glove: one move
    tf = w(16, 'flashlight')
    C(T(14), 'portrait', x=960, y=3050, h=2700, act=_A(stage(1), lambda a, s: a.torch_on(tf + 0.2, 35.0, 1, hold='side')),
      cam=dict(mv='keys', keys=[(T(14), 990, 420, 1.0), (t(15) - 0.05, 1010, 780, 1.12, 'in_out'), (t(16) + 0.4, 960, 1350, 1.0, 'in_out'),
                                (w(16, 'brass'), 940, 1560, 1.05, 'in_out'), (tf, 1180, 1900, 1.0, 'in_out'), (T(17), 1210, 1960, 1.05, 'lin')]))
    C(T(17), 'bust', who='winks', bg='kitchen', cx=960, cy=620, scale=1.3, ecu=True, act=_A(stage(1), lambda a, s: a.wink(w(17, 'winked') + 0.05)),
      cam=dict(mv='creep', x=960, y=480))
    # Owen and the tapes: practising the wink his whole life; both eyes close, every time
    C(T(18), 'bust', who=O, bg='living', lamp=0.15, light=TVL, act=_A(ex('kid_grin'), sway(3, 2.4)), cam=dict(mv='push', x=960, y=580))
    C(w(18, 'every') - 0.1, 'living', view='tv', tv=dict(on=-10.0, snow=0.0), lamp=0.2, era='memory', cam=KP(w(18, 'every') - 0.1, T(19), 930, 570, 1.25, 900, 585, 1.7))
    C(T(19), 'bust', who=O, bg='living', lamp=0.15, light=TVL, act=_A(ex('kid_grin'), lambda a, s: a.try_wink_kid(w(20, 'wink'), 0.45)),
      cam=dict(mv='push', x=960, y=570))
    C(T(21), 'bust', who=O, bg='living', lamp=0.15, light=TVL, ecu=True, cx=960, cy=660, scale=1.3,
      act=_A(ex('kid_grin'), lambda a, s: a.try_wink_kid(w(22, 'both') + 0.15, 0.9)), cam=dict(mv='creep', x=960, y=520))
    # Grandpa: one strange habit; he never said goodnight, not to his audience (the end of the show: a wave, no goodnight)
    C(T(23), 'bust', who='grandpa', bg='memory_kitchen', era='memory', expr='still_smile', act=creep(4), cam=dict(mv='creep', x=960, y=540))
    C(T(24), 'studio', track=0.3, cam=dict(mv='pull', x=960, y=560, z=1.2), w_act=lambda a, s: a.wave(t(25) + 0.5, e(25), side=-1))
    # every night he'd tuck me in, squeeze my hand three times (I love you), and say ...
    C(T(26), 'bust', who='grandpa', bg='memory_bed', era='memory', expr='still_smile', cx=1000, cy=560, scale=1.0,
      act=_A(lambda a, s: a.tuck_in(s.t0 + 0.2), setp(h_nod=0.2)), cam=dict(mv='push', x=980, y=540))
    sq = [w(26, 'three') - 0.05, w(26, 'three') + 0.38, w(26, 'times') + 0.4]
    C(w(26, 'squeeze') - 0.2, 'hands', mode='squeeze', squeeze=sq, tg=w(26, 'squeeze'), era='memory', grade='memory')
    C(T(27), 'bust', who='grandpa', bg='memory_bed', era='memory', expr='still_smile', cx=960, cy=590, scale=1.2, ecu=True, act=creep(3),
      cam=dict(mv='creep', x=960, y=480), music=[(t(27), 'motif', 0.5, 4)])

    # ============================================================ THE HOSPITAL (75.9 - 110.6)
    bed_a = _A(ex('still_smile'), setp(pupil=0.7, still=0.8))
    C(T(28), 'hospital', bed_act=bed_a, cam=KP(T(28), T(29), 960, 540, 1.0, 990, 520, 1.3), music=[(t(28), 'silence', 0.0, 0.8)])
    C(T(29), 'hospital', bed_act=bed_a, dummy='chair', dact=stage(0), cam=KP(T(29), T(30), 920, 560, 1.1, 880, 590, 1.55))
    C(T(30), 'bust', who=Y, bg='hospital', act=_A(lambda a, s: a.hold_mug(s.t0 - 1), ex('sad')), cam=dict(mv='push', x=960, y=580))
    # Mister Winks on Grandpa's lap, the old hand inside him: one last show (his head works; his jaw stays shut)
    tgh = w(32, 'hand') - 0.25
    C(T(32), 'hospital', lap=True, bed_act=bed_a, cam=KP(T(32), tgh, 960, 540, 1.0, 1000, 545, 1.9, 1.0, 1.1))
    C(tgh, 'lap', who='grandpa_bed', bg='hospital', x=880, y=930, h=1300, act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), bed_a,
                                                                          setp(turn=0.15)),
      dact=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.8), cam=dict(mv='keys', keys=[(tgh, 960, 560, 1.0), (T(33), 960, 500, 1.2, 'in_out')]))
    C(T(33), 'bust', who=Y, bg='hospital', act=_A(ex('sad'), setp(d=0.4, fade=0.8, smile=0.25)), cam=dict(mv='push', x=960, y=580))
    # the real Walter: the grab, the look, the whisper; the flatline
    tg35 = w(35, 'grabbed') + 0.05
    wl = _A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), setp(turn=0.15), ex('fear'))
    C(T(35), 'hospital', view='close', bed='walter', lap=True, bpm=104, bed_act=_A(wl, lambda a, s: a.grab_wrist(tg35, None, side=-1)), dact=LIMP,
      ppl=[P(Y, at='bedside', act=_A(turned(-0.55), ex('fear', 0.0)))], cam=KP(T(35), w(35, 'hard') - 0.2, 940, 560, 1.0, 900, 560, 1.25), hit=tg35 + 0.12)
    C(w(35, 'hard') - 0.25, 'hands', mode='grab', tg=w(35, 'hard') - 0.15, shake=1.0, bpm=104)
    C(T(36), 'bust', who='walter', bg='hospital', hview='close', act=_A(ex('lucid'), tremble(0.8)), cam=dict(mv='creep', x=960, y=560))
    C(T(37), 'bust', who='walter', bg='hospital', hview='close', ecu=True, cx=960, cy=640, scale=1.35, act=_A(ex('lucid'), tremble(1.0)),
      cam=dict(mv='creep', x=960, y=520), music=[(t(37), 'silence', 0.0, 1.0)])
    tflat = w(39, 'gone') + 0.15
    C(T(39), 'hospital', view='close', bed='walter', lap=True, bpm=60, flat=tflat, bed_act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1),
                                                                                         setp(turn=0.15, eye_open=0.25, smile=-0.1, still=1.0)),
      dact=LIMP, cam=KP(T(39), T(40), 960, 540, 1.0, 1000, 560, 1.4))
    C(T(40), 'hospital', bed='walter', lap=True, bpm=60, flat=tflat, light=0.6,
      bed_act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), setp(turn=0.15, eye_open=0.2, still=1.0)),
      dact=_A(LIMP, stage(1), lambda a, s: a.doll_turn(t(40) + 0.6, -0.05, 0.9, 3, frm=0.4)), cam=KP(T(40), T(41), 980, 540, 1.2, 1000, 550, 1.9))

    # ============================================================ TONIGHT: GRANDPA'S HOUSE (110.6 - 139.2)
    td = t(41) + 0.45
    C(T(41), 'hdoor', light=dict(on=t(42) - 0.6), door=door_swing(td, 1.5, 0.0, 0.85),
      ppl=[P(M, path=(td + 0.7, td + 3.1, ['outside', 'door', ('h', -0.65, 1.55)]), act=ex('sad')),
           P(O, path=(td + 1.2, td + 3.5, ['outside', 'door', ('h', -0.05, 1.9)]), act=ex('nervous')),
           P(Y, path=(td + 1.7, td + 3.9, ['outside', 'door', ('h', 0.45, 1.45)]))],
      cam=KP(T(41), T(42), 960, 560, 1.0, 960, 560, 1.2), focus=2.2,
      sfx=[(T(41) + 0.05, 'car_door', -10, -0.3, 'outside', dict(n=3, spacing=0.45)), (td - 0.5, 'key_in_lock', -6, 0, 'inside'),
           (td, 'door_creak', -4, 0, 'inside', dict(kind='front_door')), (t(42) - 0.6, 'light_switch', -6, -0.3, 'inside')])
    C(T(42), 'hall', kitchen=0.0, ppl=[P(M, at=('h', -0.75, 1.55), act=turned(2.0, -0.3)), P(O, at=('h', -0.15, 1.9), act=turned(2.0)),
                                      P(Y, at=('h', 0.35, 1.25), act=turned(2.0, 0.2))],
      cam=KP(T(42), T(43), 960, 560, 1.0, 950, 520, 1.25), focus=1.6, tags=[(w(42, 'eight') + 0.1, '8:00 AM   MUSEUM PICKUP', 960, 170, 'white', 2.4)])
    C(T(43), 'hall', kitchen=0.0, cam=KP(T(43), T(44), 900, 560, 1.0, 790, 600, 1.75, 1.0, 1.08), focus=1.7)
    C(T(44), 'ins', name='latches', kw=dict(latch=0.0), cam=dict(mv='move', x=700, y=560, z=1.15, x1=1080, y1=540, z1=1.32))
    C(T(46), 'ins', name='envelope', cam=dict(mv='keys', keys=[(T(46), 960, 560, 1.0), (T(47), 960, 545, 1.22, 'in_out'), (T(48), 990, 560, 1.55, 'in_out')]))
    t4 = w(49, 'fourth')
    C(T(48), 'ins', name='letter', kw=lambda tt, a=t4 - T(48): dict(hl=4 if tt >= a else 0),
      cam=dict(mv='keys', keys=[(T(48), 960, 540, 1.0), (t4, 930, 560, 1.4, 'in_out'), (T(50), 925, 565, 1.5, 'lin')]))
    C(T(50), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), down(-1, 0.4)), cam=dict(mv='push', x=960, y=580))
    C(T(51), 'hall', kitchen=0.0, cam=KP(T(51), T(52), 960, 530, 1.0, 950, 500, 1.15, 1.0, 1.1), focus=5.0,
      music=[(t(51), 'swell', 0.5, 3.0)])


def plan_night(F, t, e, w, C, T, KP):
    Y, M, O = 'you', 'mom', 'owen'
    HALL3 = lambda tt=None, a=(0.6, 0.3, -0.5): [P(M, at=('h', -0.75, 1.75), act=turned(a[0])), P(O, at=('h', -0.15, 2.0), act=turned(a[1])),
                                                 P(Y, at=('h', 0.4, 1.7), act=turned(a[2]))]
    # ============================================================ RULE 1 (139.2 - 199.0): keep him in the case
    C(T(52), 'rule', n=1, bg='hall', case='closed')
    C(T(54), 'ins', name='letter_close', kw=dict(hl=1), cam=dict(mv='push', x=960, y=470, rate=0.035))
    C(T(55), 'hall', kitchen=0.0, light=dict(flick=[(t(55) + 0.9, 0.5)]), ppl=HALL3(), focus=1.6,
      cam=KP(T(55), T(56), 960, 600, 1.0, 960, 590, 1.25), sfx=[(t(55) + 0.9, 'bulb_flicker', -12, 0, 'inside', dict(dur=0.5))])
    C(T(56), 'bust', who=M, bg='hall', act=_A(lambda a, s: a.laugh_soft(t(56) + 0.05, 1.5), ex('sad', 2.4)), cam=dict(mv='push', x=960, y=580))
    tl = w(59, 'pops') + 0.1
    C(T(59), 'ins', name='latches', kw=lambda tt, a=tl - T(59): dict(latch=(clamp((tt - a) / 0.08), clamp((tt - a - 0.26) / 0.08))),
      cam=dict(mv='push', x=960, y=560, rate=0.05), sfx=[(tl, 'case_latch', -2, -0.15, 'close'), (tl + 0.26, 'case_latch', -2, 0.15, 'close')])
    C(w(59, 'show') - 0.12, 'bust', who=O, bg='hall', act=_A(ex('nervous'), setp(d=0.0, fade=0.5, h_nod=0.12)), cam=dict(mv='push', x=960, y=600))
    # the case is empty: the shape of him pressed into the red velvet ... and the velvet is still warm
    C(T(60), 'ins', name='case_open', kw=dict(warm=0.0), cam=dict(mv='keys', keys=[(T(60), 960, 540, 1.0), (T(62), 960, 560, 1.32, 'in_out')]),
      sfx=[(t(60) - 0.2, 'case_lid', -3, 0, 'close', dict(kind='open'))], hit=t(60) + 0.04, music=[(t(60), 'stinger', 0.75)])
    C(T(62), 'ins', name='case_open', kw=lambda tt: dict(warm=clamp(tt / 0.9)), hand=('mom', 1240, 760, 320, 'open', 150.0, 1),
      cam=dict(mv='push', x=1040, y=600, z=1.2, rate=0.04), tags=[(w(62, 'warm'), 'STILL WARM', 960, 170, 'red', 1.6)])
    # from the kitchen, a sound: a spoon stirring in a cup. Clink. Clink. Clink.
    C(T(63), 'hall', case='open', kitchen=0.0, focus=1.6, ppl=[P(M, at=('h', -0.75, 1.75), act=_A(turned(0.6), turn_to(t(63) + 0.4, 1.7, 0.7))),
                                                         P(O, at=('h', -0.15, 2.0), act=_A(turned(0.3), turn_to(t(63) + 0.6, 2.0, 0.6))),
                                                         P(Y, at=('h', 0.4, 1.7), act=_A(turned(-0.5), turn_to(t(63) + 0.3, 2.2, 0.6)))],
      cam=KP(T(63), T(64), 960, 580, 1.0, 950, 540, 1.25, 1.0, 1.08),
      sfx=[(w(64, 'spoon') - 0.1, 'spoon_clink', -6, -0.1, 'kitchen_far', dict(kind='stir', dur=1.8))])
    C(T(64), 'hall', case='open', kitchen=0.0, focus=6.0, cam=KP(T(64), T(65), 950, 520, 1.0, 945, 505, 2.6, 1.0, 1.06))
    clinks = [w(65, 'clink', 0), w(65, 'clink', 1), w(65, 'clink', 2)]
    C(T(65), 'bust', who=Y, bg='hall', case='open', act=_A(ex('fear'), flinch_at(*[c + 0.05 for c in clinks], amp=0.6)), cam=dict(mv='creep', x=960, y=580),
      sfx=[(c, 'spoon_clink', -3, -0.1, 'kitchen_far', dict(kind='clink')) for c in clinks], music=[(t(65) - 0.3, 'silence', 0.0, 2.2)])
    # you don't have to go looking: the kitchen light comes on by itself; down the hall: Mister Winks in Grandpa's chair
    C(T(66), 'hall', case='open', kitchen=dict(on=T_KIT_ON), focus=8.0, cam=KP(T(66), T(67), 960, 540, 1.0, 950, 520, 1.3, 1.0, 1.05),
      sfx=[(T_KIT_ON - 0.05, 'light_switch', -8, -0.1, 'kitchen_far', dict(kind='pull_chain')), (T_KIT_ON, 'bulb_buzz', -14, -0.1, 'kitchen_far', dict(dur=6.0))])
    C(T(67), 'hall', case='open', winks=dict(act=winks_chair(look=0.0)), focus=8.6,
      cam=dict(mv='keys', shake=1.2, keys=[(T(67), 950, 530, 1.0, None, 1.3), (t(68), 860, 515, 1.05, 'in_out', 2.2),
                                           (w(68, 'up'), 815, 512, 1.08, 'in_out', 3.0)]),
      music=[(t(68), 'braam', 0.8)], hit=t(68) + 0.02)
    C(w(68, 'little') - 0.15, 'kitchen', view='table', winks=dict(act=winks_chair(look=0.0)),
      cam=KP(w(68, 'little') - 0.15, T(69), 950, 520, 1.0, 960, 470, 1.5, 1.0, 1.08))
    C(T(69), 'ins', name='mug', cam=dict(mv='keys', keys=[(T(69), 960, 540, 1.0), (T(71), 960, 470, 1.35, 'in_out')]))
    # Mom picks it up, smells it, and all the colour leaves her face
    tp = w(71, 'picks') + 0.15; tpale = w(71, 'color')
    C(T(71), 'kitchen', view='table', mug_off=tp + 0.35, winks=dict(act=winks_chair(look=0.0)),
      ppl=[P(M, at='beside', act=_A(turned(-0.55), lambda a, s: a.smell_mug(tp, None, -1, pale_at=tpale)))],
      cam=KP(T(71), tpale - 0.3, 960, 560, 1.0, 900, 540, 1.2), focus=1.65)
    C(tpale - 0.3, 'bust', who=M, bg='kitchen_table', mug=False, act=lambda a, s: a.smell_mug(s.t0 - 2.0, None, -1, pale_at=tpale),
      cam=dict(mv='creep', x=960, y=560))
    C(T(72), 'ins', name='mug', cam=dict(mv='keys', keys=[(T(72), 900, 640, 1.3), (T(73), 860, 680, 1.55, 'in_out')]),
      tags=[(t(72) + 0.05, 'TWO SUGARS', 960, 170, 'white', 1.6)])
    C(T(73), 'bust', who='grandpa', bg='memory_kitchen', era='memory', expr='still_smile',
      act=_A(lambda a, s: a.hold_mug(s.t0 - 1, None, sip=[t(73) + 0.9])), cam=dict(mv='push', x=960, y=560))
    C(T(74), 'kitchen', view='chair', winks=dict(act=winks_chair(look=0.0)), cam=KP(T(74), T(75), 960, 520, 1.0, 960, 480, 1.25))
    C(T(75), 'bust', who='winks', bg='kitchen', hands='table', act=lambda a, s: a.torch_on(-1e9 + 1, 0.0, 1, hold='up'),
      cam=dict(mv='keys', keys=[(T(75), 960, 560, 1.0), (T(77), 960, 470, 1.4, 'in_out')]), music=[(t(76), 'swell', 0.55, 3.0)])

    # ============================================================ RULE 2 (199.0 - 264.9): he does voices
    C(T(77), 'rule', n=2, bg='kitchen', ghost=[dict(who='winks', at=CHAIR_UP, act=winks_chair(look=0.0), light=WARM, torch=dict(side=1, length=2.4))])
    C(T(79), 'ins', name='letter_close', kw=dict(hl=2), cam=dict(mv='push', x=960, y=500, rate=0.035))
    C(T(80), 'ins', name='letter', cam=dict(mv='keys', keys=[(T(80), 940, 450, 1.25), (T(82), 930, 660, 1.45, 'in_out')]))   # ... down to rule six's colder hand
    C(T(82), 'kitchen', view='table', winks=dict(act=winks_chair(look=0.0)), ppl=[P(M, at='beside', act=_A(turned(-0.5), turn_to(t(82) + 0.2, -1.6, 0.8)))],
      cam=KP(T(82), T(83), 960, 540, 1.1, 960, 540, 1.0, 1.05, 1.0), focus=1.65)
    # the couch under the lamp; through the doorway you can see him; he doesn't move
    couch = lambda extra=None: [P(M, at='couch_r', act=_A(sitp(), setp(turn=0.45), extra and extra.get(M))),
                                P(Y, at='couch_m', act=_A(sitp(), setp(turn=0.15), extra and extra.get(Y))),
                                P(O, at='couch_l', act=_A(sitp(), setp(turn=-0.45), extra and extra.get(O)))]
    C(T(83), 'living', view='couch', ppl=couch(), cam=KP(T(83), T(84), 1000, 560, 1.0, 980, 600, 1.4), focus=2.85)
    C(T(84), 'living', view='tv', winks=dict(act=winks_chair(look=0.85)), cam=KP(T(84), T(86), 1060, 540, 1.0, 1110, 530, 1.3, 1.0, 1.05),
      posts=[(T(84), T(86), 1.0, 1.32, 230, -10, 'in_out')])
    # 1:15: Mom's voice calls from upstairs ("Honey? Can you come up here a second?"); nobody on screen speaks
    C(T(86), 'stairs', light=0.0, cam=KP(T(86), T(87), 960, 600, 1.0, 960, 500, 1.55, 1.0, 1.08), focus=4.8,
      tags=[(w(86, '1:15'), '1:15 AM', 960, 170, 'white', 1.8)], sfx=[(w(86, '1:15') + 0.1, 'clock_chime', -6, -0.2, 'inside', dict(kind='quarter'))],
      music=[(t(87) - 0.5, 'silence', 0.0, 1.0)])
    C(T(87), 'bust', who=M, bg='living', act=_A(ex('fear'), lambda a, s: a.set(t(87) + 0.3, None, 0.5, h_turn=0.35, look_y=-0.4, wide=0.5)),
      cam=dict(mv='creep', x=960, y=580))
    C(T(89), 'living', view='couch', ppl=couch(), cam=KP(T(89), T(90), 900, 600, 1.6, 880, 610, 1.85), focus=2.85)
    C(T(90), 'hands', mode='find', tg=t(90) + 0.1)
    C(T(91), 'stairs', light=0.0, cam=KP(T(91), T(93), 960, 470, 1.45, 960, 455, 1.8, 1.0, 1.08), focus=4.8)
    C(T(93), 'bust', who=Y, bg='living', lamp=1.0, act=_A(ex('fear'), lambda a, s: a.set(t(93), None, 0.4, h_turn=-0.25, look_y=-0.3)),
      cam=dict(mv='creep', x=960, y=580))
    C(T(96), 'bust', who=M, bg='living', act=_A(ex('fear'), lambda a, s: a.set(t(96) + 0.1, None, 0.7, h_turn=-0.45, lock=1.0, pupil=0.7)),
      cam=dict(mv='creep', x=960, y=580))
    C(T(97), 'bust', who=Y, bg='living', act=_A(ex('nervous'), setp(h_turn=0.3)), cam=dict(mv='creep', x=960, y=580))
    C(T(98), 'bust', who=M, bg='living', ecu=True, cx=960, cy=640, scale=1.35, act=_A(ex('fear'), setp(h_turn=-0.3, lock=1.0, pupil=0.62, squint=0.3)),
      cam=dict(mv='creep', x=960, y=520))
    # a third voice from the kitchen: old, warm, a little rough: "See you in the morning, kiddo." (his jaw talks)
    C(T(99), 'living', view='tv', winks=dict(act=winks_chair(look=0.85)), cam=KP(T(99), T(100), 1080, 540, 1.0, 1120, 520, 1.3, 1.0, 1.05),
      posts=[(T(99), T(100), 1.0, 1.35, 250, -10, 'in_out')])
    C(T(100), 'kitchen', view='table', winks=dict(act=winks_chair(look=0.0)), cam=KP(T(100), T(103), 960, 500, 1.3, 960, 470, 1.7, 1.0, 1.04),
      music=[(t(102), 'silence', 0.0, 1.1)])
    C(T(103), 'bust', who='winks', bg='kitchen', hands='table', cx=880, cy=600, scale=1.05,
      act=_A(lambda a, s: a.torch_on(-1e9 + 1, 0.0, 1, hold='up'), setp(h_turn=0.55, lock=0.0, look_x=0.5)),
      cam=dict(mv='creep', x=920, y=540))
    C(T(104), 'bust', who=M, bg='living', act=_A(ex('shock'), lambda a, s: a.hand_to_mouth(w(104, 'hand') - 0.15, t(105) - 0.25)),
      cam=dict(mv='push', x=960, y=580))
    C(T(106), 'living', view='couch', ppl=couch({M: lambda a, s: (a.set(t(106) + 0.2, t(107) + 0.4, 0.5, sit=0.0, perch=0.0, lean=0.15),
                                                                   a.expr('shock', s.t0 - 1)),
                                                Y: lambda a, s: a.reach(t(107) + 0.1, None, 1, 0.5 * a._alen(), 0.2 * a._alen(), 0.3 * a._alen(), 'grip')}),
      cam=KP(T(106), T(108), 960, 580, 1.2, 960, 600, 1.4), focus=2.85, sfx=[(t(106) - 0.4, 'wood_creak', -12, -0.2, 'kitchen_far', dict(kind='grind', dur=2.6))])
    # his head has turned all the way towards you; his jaw hangs open; it closes, very slowly. Clack.
    C(T(108), 'living', view='tv', winks=dict(act=_A(winks_chair(look=0.0), stage(2))), cam=KP(T(108), T(109), 1100, 530, 1.0, 1120, 520, 1.45, 1.0, 1.06),
      posts=[(T(108), T(109), 1.12, 1.45, 260, -14, 'in_out')], hit=t(108) + 0.05, music=[(t(108), 'braam', 0.85)])
    C(T(109), 'bust', who='winks', bg='kitchen', hands='table', cx=960, cy=640, scale=1.2,
      act=_A(lambda a, s: a.torch_on(-1e9 + 1, 0.0, 1, hold='up'), lambda a, s: a.jaw_hang(s.t0 - 1.0, 0.75, 0.1),
             lambda a, s: a.clack(w(111, 'clack') + 0.02, 1.9)),
      cam=dict(mv='keys', keys=[(T(109), 960, 560, 1.0), (w(111, 'clack'), 960, 500, 1.3, 'in_out'), (T(112), 960, 498, 1.32, 'lin')]),
      music=[(w(111, 'clack') + 0.02, 'hit', 0.7)])
    C(T(112), 'bust', who=Y, bg='living', act=_A(ex('fear'), lambda a, s: a.set(s.t0 + 1.0, None, 0.8, wet=0.6)), cam=dict(mv='push', x=960, y=580))
    C(T(114), 'bust', who='grandpa', bg='memory_bed', era='memory', expr='still_smile', act=_A(lambda a, s: a.tuck_in(s.t0 - 1), creep(5)),
      cam=dict(mv='creep', x=960, y=560), music=[(t(114), 'motif', 0.5, 3)])


def plan_rules34(F, t, e, w, C, T, KP):
    Y, M, O = 'you', 'mom', 'owen'
    couch = lambda extra=None: [P(M, at='couch_r', act=_A(sitp(), setp(turn=0.45), extra and extra.get(M))),
                                P(Y, at='couch_m', act=_A(sitp(), setp(turn=0.15), extra and extra.get(Y))),
                                P(O, at='couch_l', act=_A(sitp(), setp(turn=-0.45), extra and extra.get(O)))]
    W_ON = lambda a, s: a.torch_on(-1e9 + 1, 0.0, 1, hold='up')
    TVON = dict(on=T_TV_ON, snow=0.6)
    # ============================================================ RULE 3 (264.9 - 333.2): don't laugh at his jokes
    C(T(115), 'rule', n=3, bg='kitchen', ghost=[dict(who='winks', at=CHAIR_UP, act=_A(winks_chair(look=0.0), stage(2)), light=WARM,
                                                    torch=dict(side=1, length=2.4))])
    C(T(117), 'ins', name='letter_close', kw=dict(hl=3), cam=dict(mv='push', x=960, y=540, rate=0.035))
    C(T(118), 'bust', who='winks', bg='kitchen', hands='table', act=W_ON, cam=dict(mv='creep', x=960, y=540))
    C(T(119), 'living', view='couch', ppl=couch({O: lambda a, s: a.set(s.t0, None, 0.4, m_press=1.0, smile=0.3, squint=0.3)}),
      cam=KP(T(119), T(121), 960, 600, 1.35, 960, 610, 1.6), focus=2.85)
    C(T(121), 'kitchen', view='chair', winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.tick(e(121) + 0.1, 8.0))),
      cam=KP(T(121), T(122), 960, 480, 1.35, 960, 470, 1.6, 1.0, 1.04))
    # Grandpa told it at breakfast every time Owen visited (memory: the morning kitchen, little Owen laughing)
    C(T(122), 'kitchen', view='table', tod='morning', era='memory', grade='memory', mug=True,
      ppl=[P('grandpa', at='chair', act=_A(sitp(), ex('still_smile'), setp(turn=0.1))), P(O, at=('h', -1.75, 7.75), act=_A(turned(0.7),
                                                                                                               lambda a, s: a.laugh_soft(s.t0 + 1.2, 2.2)))],
      cam=KP(T(122), T(124), 960, 520, 1.0, 940, 520, 1.3), focus=2.6, sfx=[(t(122) + 1.3, 'kid_laugh', -10, -0.3, 'memory')])
    C(T(124), 'bust', who=O, bg='living', act=_A(ex('fear'), lambda a, s: a.snort(w(124, 'snorts') - 0.35)), cam=dict(mv='push', x=960, y=600))
    # Clack. One of his little white gloves lifts off the table.
    tcl = w(127, 'clack') + 0.02
    C(T(127), 'kitchen', view='chair', winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.jaw_drop(tcl - 0.32, 0.6, 0.12), lambda a, s: a.clack(tcl),
                                                         lambda a, s: a.glove_lift(w(128, 'lifts') - 0.3, -1, 0.4, 1.5))),
      cam=dict(mv='keys', shake=1.2, keys=[(T(127), 960, 470, 1.0, None, 1.4), (tcl + 0.4, 950, 480, 1.03, 'in_out', 1.5),
                                           (T(129), 900, 560, 1.08, 'in_out', 2.0)]), hit=tcl, music=[(tcl, 'stinger', 0.8)])
    C(T(129), 'living', view='couch', ppl=couch({Y: lambda a, s: a.clamp_mouth(w(129, 'clamp') + 0.1, None, side=1),
                                                O: lambda a, s: (a.expr('fear', s.t0 - 1), a.set(w(129, 'clamp') + 0.3, None, 0.2, wide=0.6))}),
      cam=KP(T(129), T(130), 920, 600, 1.55, 940, 610, 1.85), focus=2.85)
    C(T(130), 'living', view='tv', winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.glove_lift(s.t0 - 5, -1, 0.4, 0.2))),
      cam=KP(T(130), T(132), 1060, 540, 1.0, 1100, 530, 1.2, 1.0, 1.04), posts=[(T(130), T(132), 1.0, 1.3, 220, -8, 'in_out')],
      music=[(t(131), 'silence', 0.0, 1.0)])
    # the TV turns on by itself: the tape in Grandpa's old VCR; Saturday Morning with Walter Kemp, 1974
    C(T(132), 'living', view='tv', tv=TVON, lamp=0.6, cam=KP(T(132), T(133), 960, 560, 1.0, 900, 580, 1.4), hit=T_TV_ON + 0.02,
      sfx=[(T_TV_ON, 'tv_on', 0, -0.3, 'inside', dict(kind='crt')), (T_TV_ON, 'tv_static', -6, -0.3, 'inside', dict(dur=0.6))],
      music=[(T_TV_ON, 'stinger', 0.75)])
    C(T(133), 'ins', name='vcr', kw=dict(tape=1.0, play=True), cam=dict(mv='push', x=960, y=540, rate=0.045),
      sfx=[(t(133) + 0.2, 'vcr', -6, -0.3, 'close', dict(kind='play', dur=2.0))])
    C(T(134), 'studio', bezel=1.0, track=0.5, cam=dict(mv='keys', keys=[(T(134), 960, 560, 1.0), (T(135), 970, 570, 1.22, 'in_out')]),
      music=[(t(134), 'theme', 0.6, 6.0)])
    C(T(135), 'studio', track=0.35, cam=dict(mv='keys', keys=[(T(135), 960, 640, 1.25), (T(136), 960, 600, 1.1, 'in_out')]))
    # a huge roaring wave of laughter fills the dark house; with every wave something in the kitchen moves
    C(T(136), 'living', view='tv', tv=TVON, lamp=0.6, winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.tick(305.95, -6.0))),
      cam=KP(T(136), T(137), 900, 560, 1.3, 1080, 540, 1.1, 1.05, 1.0))
    C(T(137), 'living', view='tv', tv=TVON, lamp=0.6, winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.tick(309.75, 7.0, 0.05))),
      cam=KP(T(137), T(138), 1080, 540, 1.0, 1110, 530, 1.25, 1.0, 1.05), posts=[(T(137), T(138), 1.05, 1.42, 250, -10, 'in_out')])
    C(T(138), 'kitchen', view='chair', winks=dict(act=_A(winks_chair(look=0.0), lambda a, s: a.fingers_curl(w(138, 'curl') - 0.05, -1),
                                                         lambda a, s: a.elbow_bend(w(139, 'bends') - 0.1, -1, 0.3))),
      cam=KP(T(138), T(140), 880, 600, 1.7, 870, 590, 2.1, 1.0, 1.04))
    tst = w(140, 'puts')
    C(T(140), 'kitchen', view='table', winks=dict(act=_A(lambda a, s: a.sit_dummy(-1e9, tst + 0.4, hands='table'),
                                                         lambda a, s: a.torch_on(-1e9 + 1, 0.0, 1, t1=tst - 0.2, hold='up'),
                                                         lambda a, s: a.stand_on_chair(tst + 0.3, 3.0, 3))),
      cam=KP(T(140), T(141), 960, 520, 1.0, 960, 470, 1.35, 1.0, 1.05), music=[(w(140, 'stands'), 'braam', 0.85)])
    C(T(141), 'bust', who=Y, bg='living', tv=TVON, lamp=0.5, light=TVL, act=ex('fear'), cam=dict(mv='push', x=960, y=580))
    C(T(142), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(142), 960, 820, 1.7), (T(143), 940, 800, 1.95, 'in_out')]))
    # the lamp flickers; when it comes back on, the chair is empty; a little flashlight clicks on, knee high, down the hall
    STAND = lambda a, s: (a.sit_dummy(-1e9, 317.2, hands='table'), a.stand_on_chair(317.1, 0.2, 1))
    C(T(143), 'living', view='tv', tv=dict(on=T_TV_ON, snow=0.6), lamp=dict(k=0.6, flick=[(T_FLICK, 0.9)], out=[(T_FLICK + 0.85, T_BACK)]),
      kitchen=dict(flick=[(T_FLICK, 0.9)], out=[(T_FLICK + 0.85, T_BACK)]), winks=dict(act=STAND),
      cam=KP(T(143), T(144), 1060, 540, 1.1, 1100, 530, 1.25, 1.0, 1.04), posts=[(T(143), T(144), 1.1, 1.3, 230, -8, 'in_out')],
      sfx=[(T_FLICK, 'bulb_flicker', -4, -0.2, 'inside', dict(dur=0.9)), (T_FLICK + 0.85, 'lamp_out', -6, -0.2, 'inside', dict(kind='buzz_off'))])
    C(T(144), 'kitchen', view='table', kitchen=dict(on=T_BACK), cam=KP(T(144), T(145), 960, 520, 1.0, 960, 480, 1.5, 1.0, 1.06),
      hit=w(144, 'empty') + 0.05, music=[(w(144, 'empty'), 'stinger', 0.85)], sfx=[(T_BACK, 'bulb_buzz', -10, 0, 'inside', dict(kind='on'))])
    C(T(145), 'hall', light=0.0, living=0.0, kitchen=0.5, case='open', focus=4.0,
      beam=dict(keys=[(T_BEAM + 0.6, -0.4, 5.6), (334.0, -0.75, 3.7)], Y=0.42, on=w(145, 'clicks') + 0.1),
      cam=KP(T(145), T(148), 960, 540, 1.0, 950, 560, 1.35, 1.0, 1.06),
      sfx=[(w(146, 'knee'), 'footsteps_wood_inside', -16, -0.1, 'inside', dict(n=8, rate=2.6, kind='tiny'))])

    # ============================================================ RULE 4 (333.2 - 409.4): never put your hand inside him
    C(T(148), 'rule', n=4, bg='hall_dark', beam=dict(keys=[(333.0, -0.75, 3.75), (336.5, -0.85, 3.6)], Y=0.42, on=330.0))
    C(T(150), 'bust', who=Y, bg='living', tv=TVON, lamp=0.6, light=TVL, act=_A(ex('nervous'), down(-1, 0.3)), cam=dict(mv='push', x=960, y=580))
    C(T(152), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(152), 980, 600, 1.3), (T(153), 1020, 610, 1.6, 'in_out')]))
    C(T(153), 'ins', name='back_slot', kw=lambda tt: dict(hand=0.65 * ease_in_out(clamp((tt - 0.5) / 2.5))), cam=dict(mv='push', x=960, y=560, rate=0.04))
    C(T(154), 'bust', who=Y, bg='living', tv=TVON, lamp=0.6, light=TVL, act=_A(ex('sweaty'), lambda a, s: a.set(s.t0 + 0.4, None, 0.6, m_press=0.7)),
      cam=dict(mv='push', x=960, y=580))
    C(T(155, 0.6), 'ins', name='case_open', kw=dict(warm=0.0), cam=dict(mv='push', x=960, y=560, z=1.15, rate=0.035))
    # 3 AM: the flashlight comes back; he's on the stairs, three steps up, pointing it right at my face
    C(T(156), 'hall', light=0.0, living=0.0, kitchen=0.3, case='open', focus=3.0,
      beam=dict(keys=[(351.0, -1.0, 4.2), (354.6, 0.55, 1.55)], Y=0.42, on=350.0), cam=KP(T(156), T(157), 940, 560, 1.05, 990, 560, 1.2),
      tags=[(w(156, 'three') + 0.1, '3:00 AM', 960, 170, 'white', 1.8)],
      sfx=[(w(156, 'three') + 0.05 + k * 1.1, 'clock_chime', -8, -0.2, 'inside', dict(kind='hour')) for k in range(3)])
    C(T(157), 'stairs', winks=dict(act=_A(lambda a, s: a.sit_dummy(hands='knees'), lambda a, s: a.torch_on(353.6, 0.0, -1, t1=T_GRAB + 0.3, hold='lens'),
                                          stage(3))),
      cam=KP(T(157), T(158), 960, 560, 1.0, 960, 600, 1.55, 1.0, 1.08), music=[(t(157), 'braam', 0.8)])
    C(T(158), 'stairs', winks=dict(act=_A(lambda a, s: a.sit_dummy(hands='knees'), lambda a, s: a.torch_on(353.6, 0.0, -1, t1=T_GRAB + 0.3, hold='lens'),
                                          stage(3))),
      pov=dict(t0=T_GRAB - 0.1, reach=(960, 860), size=300, grab=T_GRAB + 0.25, depth=0.9),
      cam=KP(T(158), T(159), 960, 600, 1.6, 960, 640, 1.8, 1.04, 1.1, shake=4.0), hit=T_GRAB + 0.25)
    C(T(159), 'ins', name='back_slot', kw=lambda tt: dict(hand=ease_in_out(clamp((tt - 0.35) / 2.0))), cam=dict(mv='push', x=960, y=560, rate=0.04))
    # inside him: a stick, and a hand; it lets go of the stick and takes my hand; it squeezes once, twice, three times
    C(T(160), 'ins', name='squeeze', kw=dict(take=0.0, squeeze=lambda tt: 0.0), cam=dict(mv='push', x=960, y=560, rate=0.035),
      music=[(t(161) - 0.2, 'silence', 0.0, 1.0)])
    tk = w(163, 'lets')
    C(T(161), 'ins', name='squeeze', kw=dict(take=0.0, squeeze=0.0), cam=dict(mv='push', x=960, y=560, z=1.08, rate=0.03), music=[(t(161), 'swell', 0.55, 4.0)])
    C(T(162), 'bust', who=Y, bg='stairs', light=NIGHT, act=_A(ex('shock'), setp(wet=0.6)), cam=dict(mv='creep', x=960, y=580))
    C(T(163), 'ins', name='squeeze', kw=lambda tt, a=tk - T(163): dict(take=ease_in_out(clamp((tt - a) / 2.3)), squeeze=0.0),
      cam=dict(mv='push', x=960, y=560, z=1.15, rate=0.03))
    sq = [w(165, 'once') + 0.05, w(166, 'twice') + 0.05, w(167, 'three') + 0.1]
    sqf = ST.squeeze_pulses(sq)
    C(T(164), 'ins', name='squeeze', kw=lambda tt, a=T(164): dict(take=1.0, squeeze=sqf(tt + a)), cam=dict(mv='push', x=980, y=580, z=1.3, rate=0.03),
      sfx=[(s_, 'hand_squeeze', -6, 0, 'close') for s_ in sq], music=[(t(168), 'motif', 0.55, 4)])
    C(T(169), 'bust', who=Y, bg='stairs', light=NIGHT, act=_A(ex('sad'), lambda a, s: a.set(s.t0, None, 0.5, wet=1.0, tears=0.6), lambda a, s: a.squeezed(sq)),
      cam=dict(mv='push', x=960, y=580))
    C(T(170), 'stairs', winks=dict(act=_A(lambda a, s: a.sit_dummy(hands='limp'), stage(3), setp(h_nod=-0.1))),
      pov=dict(t0=T(170) - 1.0, reach=(1080, 760), size=300, both=False, depth=1.46), cam=KP(T(170), T(172), 960, 560, 1.5, 960, 560, 1.7))
    # "Kiddo," says Grandpa's voice, very softly ... his jaw talks only on his words
    WST = lambda: _A(stage(3), setp(h_nod=-0.12))
    C(T(172), 'bust', who='winks', bg='stairs', light=dict(NIGHT, under='#ffd9a0', under_a=60), act=WST(), cam=dict(mv='creep', x=960, y=540))
    C(T(174), 'bust', who='winks', bg='stairs', light=dict(NIGHT, under='#ffd9a0', under_a=60), act=WST(), cam=dict(mv='push', x=960, y=520))
    C(w(176, 'behind') - 0.1, 'bust', who=Y, bg='stairs', light=NIGHT, act=_A(ex('sad'), setp(wet=1.0)), cam=dict(mv='creep', x=960, y=580))
    C(T(178), 'bust', who='winks', bg='stairs', light=dict(NIGHT, under='#ffd9a0', under_a=60), act=WST(), cam=dict(mv='push', x=960, y=520))
    C(T(181), 'bust', who='winks', bg='stairs', ecu=True, cx=960, cy=640, scale=1.35, light=dict(NIGHT, under='#ffd9a0', under_a=60), act=WST(),
      cam=dict(mv='creep', x=960, y=500))
    C(w(182, 'rule') - 0.25, 'rule', n=2, bg='stairs', recall=True, mode='flicker', reveal=w(182, 'two') + 0.05)
    C(T(183), 'bust', who='winks', bg='stairs', light=dict(NIGHT, under='#ffd9a0', under_a=60), act=WST(), cam=dict(mv='push', x=960, y=520))
    C(T(184), 'ins', name='back_slot', kw=lambda tt: dict(hand=1.0 - ease_in_out(clamp((tt - 0.1) / 0.7))), cam=dict(mv='push', x=960, y=560, rate=0.05),
      sfx=[(t(184) + 0.2, 'cloth_rustle', -6, 0, 'close', dict(kind='slot'))])
    tcs = w(185, 'clacks') + 0.05
    C(T(185), 'bust', who='winks', bg='stairs', cx=960, cy=560, scale=1.15, light=dict(NIGHT, under='#ffd9a0', under_a=60),
      act=_A(setp(h_nod=-0.25), lambda a, s: a.jaw_hang(s.t0 - 0.6, 0.45, 0.2), lambda a, s: a.clack(tcs, 0.08)),
      cam=dict(mv='keys', keys=[(T(185), 960, 620, 1.0), (T(186), 960, 560, 1.25, 'in_out')]), hit=tcs, music=[(tcs, 'stinger', 0.75)])
    C(T(186), 'bust', who=Y, bg='stairs', light=NIGHT, act=_A(ex('sad'), setp(wet=1.0, tears=0.8)), cam=dict(mv='push', x=960, y=580))
    C(T(188), 'bust', who='winks', bg='stairs', ecu=True, cx=960, cy=660, scale=1.4, light=dict(NIGHT, under='#ffd9a0', under_a=60),
      act=setp(h_nod=-0.2), cam=dict(mv='creep', x=960, y=520), music=[(t(189), 'swell', 0.55, 3.0)])


def plan_rules56(F, t, e, w, C, T, KP):
    Y, M, O, ON = 'you', 'mom', 'owen', 'owen_new'
    TVON = dict(on=T_TV_ON, snow=0.6)
    BOOK = lambda extra=None, torch_t=417.55: dict(act=_A(lambda a, s: a.sit_dummy(hands='limp'), lambda a, s: a.torch_on(torch_t, 0.0, 1, hold='chin'),
                                                          stage(4), extra), light=TORCH, torch=dict(side=1, length=0.6))
    # ============================================================ RULE 5 (409.4 - 506.3): if their lips don't move, it isn't them
    C(T(190), 'rule', n=5, bg='living', tv=TVON, lamp=0.6)
    C(413.55, 'bust', who='winks', bg='living', tv=TVON, lamp=0.4, ecu=True, cx=960, cy=250, scale=1.9, light=TORCH, act=stage(4),
      cam=dict(mv='creep', x=960, y=560))
    C(T(192), 'living', view='couch', tv=TVON, lamp=0.6, winks=BOOK(), focus=3.45,
      ppl=[P(M, at='mom', act=_A(turned(0.35), lambda a, s: a.grab_keys(w(192, 'grabs') + 0.15, 1), ex('fear'))),
           P(O, at='couch_l', act=_A(sitp(), setp(turn=-0.45), ex('fear')))],
      cam=KP(T(192), T(193), 960, 560, 1.0, 1000, 560, 1.3))
    C(T(193), 'bust', who=M, bg='living', tv=TVON, lamp=0.6, cx=820, cy=600, scale=0.95, dof=3.2, act=_A(ex('blank'), setp(lock=1.0, pupil=0.75)),
      ghost=[dict(who='winks', at='bookcase_top', **BOOK())], cam=dict(mv='creep', x=900, y=560))
    C(T(196), 'bust', who=M, bg='living', tv=TVON, lamp=0.6, ecu=True, cx=960, cy=330, scale=1.75, act=_A(ex('blank'), setp(lock=1.0)),
      cam=dict(mv='creep', x=960, y=560), hit=t(196) + 0.05, music=[(t(196), 'stinger', 0.8)])
    C(T(197), 'bust', who=Y, bg='living', tv=TVON, lamp=0.6, act=_A(ex('fear'), lambda a, s: a.spin_around(w(197, 'spin'), 2.0, 0.32)),
      cam=dict(mv='fast', x=960, y=580))
    C(T(198), 'living', view='couch', tv=TVON, lamp=0.6, winks=BOOK(jaw_chatter(t(198) - 0.2, 429.0, 1.7, 0.5)), focus=4.55,
      ppl=[P(M, at='mom', act=_A(turned(0.35), ex('fear')))],
      cam=KP(T(198), w(198, 'under') - 0.4, 1150, 470, 1.0, 1200, 455, 1.85, 1.0, 1.05), posts=[(T(198), w(198, 'under') - 0.4, 1.0, 1.4, 260, -40, 'in_out')],
      music=[(t(198), 'braam', 0.85)], hit=t(198) + 0.04)
    C(w(198, 'under') - 0.4, 'bust', who='winks', bg='living', tv=TVON, lamp=0.6, light=TORCH, torch_glow=True, cx=960, cy=600, scale=1.15,
      act=_A(lambda a, s: a.torch_on(417.55, 0.0, 1, hold='chin'), stage(4), jaw_chatter(t(198) - 0.2, 429.0, 1.7, 0.55)),
      cam=dict(mv='creep', x=960, y=520))
    C(T(199), 'bust', who=M, bg='living', tv=TVON, lamp=0.6, act=_A(ex('fear'), setp(h_turn=-0.2)), cam=dict(mv='push', x=960, y=580))
    C(T(202), 'living', view='couch', tv=TVON, lamp=0.6, winks=BOOK(), focus=3.45, ppl=[P(M, at='mom', act=_A(turned(0.35), ex('fear')))],
      cam=KP(T(202), T(203), 1060, 520, 1.3, 1080, 510, 1.55))
    # the tape: young Walter smiling with Mister Winks on his knee; his lips never move; the dummy stops mid-joke, turns to the
    # camera, and an old man's voice cries out of him
    C(T(203), 'living', view='tv', tv=TVON, lamp=0.6, cam=KP(T(203), T(204), 940, 560, 1.0, 900, 580, 1.5))
    C(T(204), 'studio', track=0.35, cam=dict(mv='keys', keys=[(T(204), 960, 600, 1.0), (T(205), 990, 520, 1.45, 'in_out')]))
    C(T(205), 'studio', track=0.3, cam=dict(mv='keys', keys=[(T(205), 1000, 480, 1.75), (T(208), 1010, 470, 2.15, 'in_out')]))
    C(T(208), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(208), 990, 540, 1.4), (T(209), 1000, 530, 1.55, 'in_out')]))
    tsn = w(210, 'turns') + 0.05
    C(T(209), 'bust', who='winks', bg='studio', tape=True, cx=1000, cy=600, scale=1.0,
      act=_A(lambda a, s: a.puppet(s.t0 - 2, 445.0, look=-1, rate=0.8), lambda a, s: a.set(445.3, None, 0.2, h_turn=-0.35)),
      track_fn=lambda tt: 0.35 + 0.5 * clamp((tt - 446.0) / 2.4), cam=dict(mv='creep', x=980, y=540))
    C(T(210), 'bust', who='winks', bg='studio', tape=True, cx=960, cy=600, scale=1.1,
      act=_A(lambda a, s: a.set(-9, None, 0.1, h_turn=-0.35, lock=0.0), lambda a, s: a.head_snap(tsn, 0.0, -0.35)),
      track_fn=lambda tt: 0.85 + 1.5 * math.exp(-max(0.0, tt - tsn) * 3) * (tt > tsn), cam=dict(mv='push', x=960, y=520, rate=0.03), hit=tsn,
      music=[(tsn, 'braam', 0.9)])
    C(w(210, 'his') - 0.1, 'living', view='tv', tv=TVON, lamp=0.4, d_act=lambda a, s: a.set(-9, None, 0.1, h_turn=0.0, lock=1.0),
      cam=KP(w(210, 'his') - 0.1, T(211), 930, 580, 1.4, 890, 600, 2.2))
    C(T(211), 'bust', who='winks', bg='studio', tape=True, ecu=True, cx=960, cy=640, scale=1.35, cam=dict(mv='creep', x=960, y=520), track_fn=lambda tt: 0.6)
    C(T(214), 'bust', who='winks', bg='studio', tape=True, cx=960, cy=600, scale=1.15, cam=dict(mv='creep', x=960, y=520), music=[(t(214), 'silence', 0.0, 0.0)])
    C(T(216), 'bust', who='walter74', bg='studio', cx=960, cy=600, scale=1.2, act=lambda a, s: a.showman(s.t0 - 2, s.t1 + 2, look=0.0),
      cam=dict(mv='creep', x=960, y=640))
    C(T(217), 'bust', who='winks', bg='studio', tape=True, ecu=True, cx=960, cy=660, scale=1.4, cam=dict(mv='creep', x=960, y=520))
    C(T(218), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(218), 960, 600, 1.1), (T(220), 960, 620, 1.0, 'in_out')]))
    C(T(220), 'bust', who='walter74', bg='studio', ecu=True, cx=960, cy=560, scale=1.45, act=lambda a, s: a.showman(s.t0 - 2, s.t1 + 2, look=0.0),
      cam=dict(mv='creep', x=960, y=600))
    C(T(221), 'living', view='tv', tv=TVON, lamp=0.35, cam=KP(T(221), T(222), 900, 580, 1.2, 880, 590, 1.6))
    C(T(222), 'ins', name='family_photo', cam=dict(mv='push', x=960, y=520, rate=0.04))
    C(T(223), 'bust', who='grandpa', bg='memory_bed', era='memory', expr='still_smile', act=_A(lambda a, s: a.tuck_in(s.t0 - 1), creep(4)),
      cam=dict(mv='push', x=960, y=560), post_fn=lambda tt, a=T(223): dict(sat=1.0 - 0.6 * clamp((tt - a) / 3.4)))
    C(T(224), 'bust', who='grandpa', bg='hall_dark', ecu=True, cx=960, cy=600, scale=1.35, light=NIGHT, act=_A(ex('still_smile'), setp(lock=1.0, pupil=0.6)),
      cam=dict(mv='creep', x=960, y=520), hit=t(224) + 0.05, music=[(t(224), 'stinger', 0.85)])
    C(T(225), 'studio', track=0.4, cam=dict(mv='keys', keys=[(T(225), 960, 600, 1.0), (w(225, 'knee'), 1010, 560, 1.5, 'in_out')]))
    C(w(225, 'knee') - 0.05, 'bust', who='winks', bg='studio', tape=True, ecu=True, cx=960, cy=640, scale=1.35, cam=dict(mv='creep', x=960, y=520))
    C(T(226), 'studio', track=0.3, cam=dict(mv='keys', keys=[(T(226), 960, 820, 1.7), (T(227), 960, 800, 1.95, 'in_out')]))
    # last week, the real Walter back in his body for one hour: long enough to tell me, to write me a letter, to die
    WB = _A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), setp(turn=0.15), ex('lucid'))
    C(T(227), 'hospital', bed='walter', lap=True, bpm=104, bed_act=_A(WB, tremble(0.6)), dact=LIMP, era='memory',
      cam=KP(T(227), w(228, 'one') - 0.3, 960, 540, 1.0, 990, 540, 1.6))
    C(w(228, 'one') - 0.3, 'bust', who='walter', bg='hospital', era='memory', act=_A(ex('lucid'), tremble(0.8)), cam=dict(mv='creep', x=960, y=560))
    C(T(229), 'hands', mode='grab', tg=t(229) + 0.25, shake=1.0, era='memory')
    C(T(230), 'ins', name='letter', era='memory', cam=dict(mv='push', x=960, y=540, rate=0.05))
    C(T(231), 'hospital', view='close', bed='walter', lap=True, bpm=60, flat=t(231) + 0.7, era='memory',
      bed_act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), setp(turn=0.15, eye_open=0.3, still=1.0)), dact=LIMP,
      cam=KP(T(231), T(232), 960, 540, 1.2, 980, 540, 1.5))
    sq2 = [w(232, 'three') - 0.25, w(232, 'three') + 0.17, w(232, 'times') + 0.35]
    sqf2 = ST.squeeze_pulses(sq2)
    C(T(232), 'ins', name='squeeze', kw=lambda tt, a=T(232): dict(take=1.0, squeeze=sqf2(tt + a)), cam=dict(mv='push', x=960, y=560, z=1.1, rate=0.035),
      sfx=[(s_, 'hand_squeeze', -9, 0, 'close') for s_ in sq2])
    C(w(232, "wasn't") - 0.1, 'bust', who='grandpa', bg='memory_bed', era='memory', act=_A(lambda a, s: a.tuck_in(s.t0 - 1), setp(smile=0.6, brow_sad=0.3)),
      cam=dict(mv='push', x=960, y=560))
    C(T(233), 'bust', who=Y, bg='living', tv=TVON, lamp=0.5, light=TVL, act=_A(ex('sad'), setp(wet=1.0, tears=1.0)), cam=dict(mv='creep', x=960, y=580),
      music=[(t(233), 'motif', 0.55, 3)])

    # ============================================================ RULE 6 (506.3 - 582.2): don't pull him off; have them say goodnight
    C(T(234), 'rule', n=6, bg='living', tv=TVON, lamp=0.5)
    C(T(236), 'ins', name='letter_close', kw=dict(hl=6), cam=dict(mv='push', x=960, y=620, z=1.05, rate=0.03))
    C(T(238), 'ins', name='letter', kw=dict(hl=6), cam=dict(mv='keys', keys=[(T(238), 940, 640, 1.3), (T(240), 950, 680, 1.55, 'in_out')]))
    C(T(240), 'bust', who='winks', bg='living', tv=TVON, lamp=0.5, light=TORCH, torch_glow=True, act=_A(lambda a, s: a.torch_on(417.55, 0.0, 1, hold='chin'), stage(4)),
      cam=dict(mv='creep', x=960, y=540))
    C(T(241), 'bust', who=Y, bg='living', tv=TVON, lamp=0.5, light=TVL, act=_A(ex('sad'), setp(d=0.3, fade=0.8, brow_sad=0.2, m_press=0.0)),
      cam=dict(mv='push', x=960, y=580))
    # when I turn around, Owen is gone (and so is the dummy on the bookcase)
    C(T(242), 'living', view='couch', tv=TVON, lamp=0.5, focus=2.85, ppl=[P(M, at='couch_r', act=_A(sitp(), setp(turn=0.45), ex('fear')))],
      cam=KP(T(242), T(243), 1000, 560, 1.0, 1080, 540, 1.3), hit=w(242, 'gone') + 0.05, music=[(w(242, 'gone'), 'stinger', 0.85)])
    # the den: Owen in Grandpa's armchair, the dummy on his knee, his hand inside up to the wrist, grinning
    OL = lambda **k: dict(dict(who=O, side=-1, act=_A(lambda a, s: a.vent_pose(side=-1), ex('kid_grin')),
                               dact=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=1, rate=0.9)), **k)
    C(T(243), 'den', lap=OL(), cam=KP(T(243), T(245), 960, 560, 1.0, 900, 580, 1.55), music=[(t(243), 'braam', 0.75)])
    C(T(245), 'ins', name='back_slot', kw=dict(hand=1.0), cam=dict(mv='push', x=960, y=600, rate=0.04))
    C(w(245, 'way', 1) - 0.1, 'studio', track=0.4, cam=dict(mv='keys', keys=[(w(245, 'way', 1) - 0.1, 1000, 560, 1.5), (T(246), 1020, 580, 1.7, 'in_out')]))
    LAP_O = dict(who=O, bg='den', x=760, y=960, h=1350, side=-1)
    C(T(246), 'lap', **LAP_O, act=_A(lambda a, s: a.vent_pose(side=-1), ex('kid_grin')), dact=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=1, rate=0.9),
      cam=dict(mv='push', x=900, y=520))
    C(T(247), 'lap', **LAP_O, act=_A(lambda a, s: a.vent_pose(side=-1), ex('kid_grin')), dact=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=1, rate=1.1),
      cam=dict(mv='keys', keys=[(T(247), 880, 560, 1.0), (T(250), 860, 480, 1.22, 'in_out')]))
    C(T(250), 'bust', who=M, bg='den', act=_A(ex('fear'), lambda a, s: a.hand_to_mouth(s.t0 + 0.2, None)), cam=dict(mv='push', x=960, y=580))
    C(T(251), 'bust', who='winks', bg='den', cx=960, cy=600, scale=1.15, worked=True, act=_A(lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=1, rate=0.5)),
      cam=dict(mv='creep', x=960, y=520), music=[(t(251), 'stinger', 0.8)])
    C(T(252), 'bust', who=O, bg='den', act=_A(ex('nervous'), setp(h_turn=0.35, look_x=0.5)), cam=dict(mv='creep', x=960, y=600))
    C(T(253), 'bust', who='winks', bg='den', cx=900, cy=600, scale=1.25, worked=True, act=setp(h_turn=-0.1), cam=dict(mv='push', x=930, y=520))
    # Mom screams and grabs him to pull him off; Owen shrieks; his hand won't come out; "Pull, and his hand comes with me."
    tp0, tp1 = w(254, 'grabs'), w(256, 'out') + 0.4
    pulls = [tp0 + 0.4 + (tp1 - tp0 - 0.6) * k / 3 for k in range(3)]
    jerk = lambda tt: sum(-26.0 * math.exp(-max(0.0, tt - p_) * 5.0) * (tt >= p_) for p_ in pulls)
    C(T(254), 'den', lap=OL(act=_A(lambda a, s: a.vent_pose(side=-1), lambda a, s: a.cry(t(255))), jerk=jerk),
      ppl=[P(M, at=('h', -0.85, 2.15), act=_A(turned(-0.6), lambda a, s: a.pull_dummy(tp0, tp1), lambda a, s: a.scream(w(254, 'screams'), w(254, 'grabs') + 1.6)))],
      cam=KP(T(254), T(255), 900, 580, 1.25, 860, 600, 1.6, shake=3.0),
      sfx=[(w(254, 'screams'), 'scream', -2, -0.2, 'inside', dict(who='mom'))], music=[(w(254, 'screams'), 'hit', 0.9)])
    C(T(255), 'lap', **LAP_O, act=_A(lambda a, s: a.vent_pose(side=-1), lambda a, s: a.expr('scream', s.t0 - 0.3), lambda a, s: a.cry(s.t0)),
      jerk=lambda tt: jerk(tt) * 2.5, cam=dict(mv='hand', x=880, y=540), sfx=[(t(255) + 0.05, 'shriek', -3, 0.1, 'inside', dict(who='owen'))])
    C(T(257), 'bust', who='winks', bg='den', cx=960, cy=600, scale=1.15, worked=True, act=_A(lambda a, s: a.set(-9, None, 0.1, h_turn=0.15)),
      cam=dict(mv='hand', x=960, y=520))
    C(T(258), 'bust', who=M, bg='den', act=_A(ex('scream'), lambda a, s: a.pull_dummy(s.t0 - 1, s.t1 + 0.5)), cam=dict(mv='hand', x=960, y=580))
    C(T(259), 'bust', who='winks', bg='den', ecu=True, cx=960, cy=640, scale=1.35, worked=True, act=setp(h_turn=0.1), cam=dict(mv='hand', x=960, y=520))
    C(T(260), 'hands', mode='catch', tg=w(260, 'catch') + 0.05, shake=1.2)
    C(T(261), 'rule', n=6, bg='den', recall=True)
    C(T(262), 'den', lap=OL(act=_A(lambda a, s: a.vent_pose(side=-1), lambda a, s: a.cry(s.t0 - 1)), dact=None),
      ppl=[P(Y, at=('h', 0.4, 1.95), act=_A(turned(1.55), lambda a, s: a.kneel(w(262, 'kneel')))),
           P(M, at=('h', -0.95, 2.05), act=_A(turned(-0.5), lambda a, s: a.hands_over_mouth(s.t0 - 0.5, None, 0.4, True)))],
      cam=KP(T(262), T(263), 960, 580, 1.0, 940, 590, 1.35))
    C(T(263), 'bust', who=O, bg='den', act=_A(lambda a, s: a.cry(s.t0 - 1)), cam=dict(mv='creep', x=960, y=600))
    C(T(264), 'lap', **LAP_O, act=_A(lambda a, s: a.vent_pose(side=-1), lambda a, s: a.cry(s.t0 - 1)), cam=dict(mv='creep', x=900, y=500))
    tw = w(266, 'click') - 0.03
    C(T(265), 'bust', who='winks', bg='den', cx=960, cy=600, scale=1.2, worked=True,
      act=_A(lambda a, s: a.doll_turn(w(265, 'turns'), 0.8, 1.0, 3), lambda a, s: a.wink(tw, 1, 0.45)),
      cam=dict(mv='keys', keys=[(T(265), 960, 560, 1.0), (tw, 960, 520, 1.22, 'in_out'), (T(268), 960, 515, 1.25, 'lin')]), music=[(tw, 'hit', 0.6)])
    C(T(268), 'lap', **LAP_O, act=_A(lambda a, s: a.vent_pose(side=-1), lambda a, s: a.cry(s.t0 - 1)),
      dact=lambda a, s: a.set(-9, None, 0.1, h_turn=0.8), cam=dict(mv='keys', keys=[(T(268), 860, 470, 1.25), (T(269), 860, 460, 1.32, 'in_out')]),
      music=[(t(268) - 0.6, 'silence', 0.0, 0.5)])
    C(T(269), 'bust', who=O, bg='den', ecu=True, cx=960, cy=640, scale=1.3, act=_A(lambda a, s: a.cry(s.t0 - 1),
                                                                                lambda a, s: a.lids(T_SWAP, None, 1.0, 0.55)),
      cam=dict(mv='creep', x=960, y=520), music=[(T_SWAP, 'sub_drop', 0.9)])
    C(T(271), 'den', lamp=dict(out=[(T_LAMP_OUT[0], T_LAMP_OUT[1])]), lap=dict(who=ON, side=-1, act=_A(lambda a, s: a.vent_pose(side=-1), setp(eye_open=0.0)),
                                                                                   dact=None),
      ppl=[P(Y, at=('h', 0.4, 1.95), act=_A(turned(1.55), lambda a, s: a.kneel(s.t0 - 2))), P(M, at=('h', -0.95, 2.05), act=turned(-0.5))],
      cam=KP(T(271), T(272), 940, 580, 1.2, 940, 580, 1.3), sfx=[(T_LAMP_OUT[0], 'lamp_out', -2, 0.1, 'inside', dict(kind='pop')),
                                                                  (T_LAMP_OUT[1], 'lamp_on', -6, 0.1, 'inside', dict(kind='buzz_on'))],
      music=[(T_LAMP_OUT[0], 'silence', 0.0, 1.2)])
    # the lamp comes back: Owen slides his hand out like it's nothing, jumps up, hugs Mom; the dummy drops face down on the rug
    C(T(272), 'lap', who=ON, bg='den', x=760, y=960, h=1350, side=-1,
      act=_A(lambda a, s: a.vent_pose(-1e9, w(272, 'slides') + 0.2, side=-1), lambda a, s: a.set(w(272, 'slides'), None, 0.5, smile=0.5, grin=0.1)),
      cam=dict(mv='push', x=880, y=540), music=[(t(272) + 0.6, 'motif', 0.45, 3)])
    C(w(272, 'jumps') - 0.2, 'den', lap=dict(who=ON, side=-1, act=_A(lambda a, s: a.set(-9, None, 0.1, smile=0.6, grin=0.15), lambda a, s: a.jump_hug(T_JUMP)),
                                               dact=None, release=T_JUMP + 0.1),
      ppl=[P(Y, at=('h', 0.4, 1.95), act=_A(turned(1.55), lambda a, s: a.kneel(s.t0 - 2))), P(M, at=('h', -0.95, 2.05), act=_A(turned(-0.5), ex('shock')))],
      cam=KP(w(272, 'jumps') - 0.2, T(273), 960, 580, 1.15, 940, 580, 1.25), sfx=[(T_JUMP + 0.55, 'dummy_thud', -2, -0.1, 'inside', dict(kind='rug'))])
    C(T(273), 'bust', who=ON, bg='den', act=_A(lambda a, s: a.set(-9, None, 0.1, smile=0.8, grin=0.3, teeth=0.5), setp(turn=0.3)), cam=dict(mv='push', x=960, y=600))
    C(T(275), 'bust', who=Y, bg='den', act=_A(ex('shock'), setp(h_turn=0.3)), cam=dict(mv='push', x=960, y=580))
    C(T(276), 'den', rug=True, focus=1.8, cam=KP(T(276), T(279), 960, 620, 1.0, 960, 640, 1.9, 1.0, 1.08), music=[(t(277), 'silence', 0.0, 1.2)])


def plan_end(F, t, e, w, C, T, KP):
    Y, M, O, ON = 'you', 'mom', 'owen', 'owen_new'
    # ============================================================ RULE 7 (582.2 - 655.5): never say goodnight to him
    C(T(279), 'rule', n=7, bg='den', lamp=1.0)
    C(T(283), 'ins', name='letter', kw=dict(hl=0), motion=lambda tt: (2.0 * math.sin(tt * 17), 1.5 * math.sin(tt * 13), 0, 0.3 * math.sin(tt * 11)),
      cam=dict(mv='push', x=960, y=540, rate=0.04))
    t7 = w(285, 'seven')
    C(T(285), 'ins', name='letter_close', kw=lambda tt, a=t7 - T(285): dict(hl=7 if tt >= a else 6),
      cam=dict(mv='keys', keys=[(T(285), 960, 640, 1.15), (t7, 960, 700, 1.25, 'in_out'), (T(286), 960, 760, 1.35, 'in_out')]))
    C(T(286), 'ins', name='letter_close', kw=dict(hl=6), cam=dict(mv='push', x=960, y=640, z=1.2, rate=0.03))
    C(T(287), 'den', lap=None, rug=True, ppl=[P(M, at=('h', -0.95, 2.05), act=_A(turned(-0.4), ex('sad'))),
                                              P(ON, at=('h', -0.55, 2.0), act=_A(turned(1.8), lambda a, s: a.set(t(288), None, 0.9, h_turn=-1.5, lock=1.0, smile=0.6)))],
      cam=KP(T(287), T(290), 940, 560, 1.15, 860, 520, 1.6), focus=2.0, music=[(t(289), 'swell', 0.55, 3.0)])
    # I pick the dummy up off the rug; something slides out of the slot in his back: the torn P.S.
    C(T(290), 'carry', bg='den', x=900, y=2350, h=2400, dact=lambda a, s: a.smile_stage(-9, 'asleep'), cam=dict(mv='push', x=960, y=520))
    C(w(290, 'something') - 0.1, 'ins', name='back_slot', kw=lambda tt, a=w(290, 'slides') - w(290, 'something') + 0.1: dict(paper=0.9 * ease_in_out(clamp((tt - a) / 1.3))),
      cam=dict(mv='push', x=960, y=620, rate=0.045), sfx=[(w(290, 'slides'), 'paper', -6, 0, 'close', dict(kind='slide', dur=1.3))])
    C(T(291), 'ins', name='ps', cam=dict(mv='keys', keys=[(T(291), 960, 560, 1.0), (T(292), 960, 540, 1.2, 'in_out')]),
      sfx=[(t(291) + 0.5, 'paper', -8, 0, 'close', dict(kind='unfold'))])
    C(T(292), 'ins', name='letter', cam=dict(mv='keys', keys=[(T(292), 960, 760, 1.35), (T(293), 960, 820, 1.55, 'in_out')]))
    C(T(293), 'ins', name='ps', cam=dict(mv='keys', keys=[(T(293), 880, 440, 1.45), (T(295), 920, 520, 1.55, 'in_out')]), music=[(t(293), 'motif', 0.55, 4)])
    C(T(295), 'bust', who=Y, bg='den', act=_A(ex('fear'), setp(wet=0.8)), cam=dict(mv='creep', x=960, y=580))
    C(T(297), 'ins', name='ps', cam=dict(mv='keys', keys=[(T(297), 1040, 640, 1.5), (T(299), 1060, 650, 1.7, 'in_out')]))
    C(T(299), 'bust', who=Y, bg='den', act=_A(ex('shock'), setp(wet=0.8)), cam=dict(mv='push', x=960, y=580))
    # 1962: the end of his very first show; "Say goodnight, Mister Winks." His knee. His hand. His goodnight. They traded places.
    C(T(300), 'stage62', cam=KP(T(300), w(300, 'young') - 0.1, 960, 560, 1.0, 960, 540, 1.25), tags=[(w(300, '1962'), '1962', 960, 170, 'white', 2.0)],
      music=[(t(300), 'motif', 0.5, 6)], d_act=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.7))
    C(w(300, 'young') - 0.1, 'stage62', cam=KP(w(300, 'young') - 0.1, w(300, 'said') - 0.1, 950, 500, 1.3, 970, 480, 1.6),
      d_act=lambda a, s: a.puppet(s.t0 - 2, s.t1 + 2, look=-1, rate=0.7))
    C(w(300, 'said') - 0.1, 'bust', who='walter74', bg='stage62', era='1962', grade='memory', act=lambda a, s: a.showman(s.t0 - 2, s.t1 + 2, look=0.3),
      cam=dict(mv='creep', x=960, y=560))
    C(T(301), 'lap', who='walter74', bg='stage62', x=880, y=980, h=1400, grade='memory', d_act=None,
      dact=lambda a, s: a.doll_turn(t(301) + 0.2, -0.8, 0.8, 2), cam=dict(mv='creep', x=940, y=480))
    C(w(302, 'knee') - 0.12, 'lap', who='walter74', bg='stage62', x=880, y=700, h=1400, grade='memory',
      dact=lambda a, s: a.set(-9, None, 0.1, h_turn=-0.8), cam=dict(mv='push', x=980, y=760, z=1.2))
    C(w(303, 'hand') - 0.12, 'ins', name='back_slot', kw=dict(hand=1.0), grade='memory', cam=dict(mv='push', x=960, y=560, z=1.1))
    C(w(304, 'good') - 0.15, 'bust', who='winks', bg='stage62', cx=960, cy=600, scale=1.2, worked=True, era='1962', grade='memory',
      act=_A(lambda a, s: a.set(-9, None, 0.1, h_turn=-0.6), stage(1), lambda a, s: a.wink(w(304, 'night') + 0.05, 1, 0.3)), cam=dict(mv='creep', x=960, y=520))
    C(T(305), 'stage62', cut='white', cam=KP(T(305), T(306), 970, 480, 1.6, 970, 470, 1.6), hit=w(305, 'traded'),
      d_act=lambda a, s: (a.set(-9, None, 0.1, h_turn=-0.6), a.head_snap(w(305, 'traded') + 0.05, 0.0)),
      w_act=lambda a, s: a.set(w(305, 'traded'), None, 0.05, smile=0.6, still=1.0, lock=1.0), music=[(w(305, 'traded'), 'braam', 0.9)])
    # sixty years later: the thing in his body felt it dying; asked for its dummy, sat him on its lap, said the word
    C(T(306), 'hospital', bpm=52, bed_act=_A(ex('still_smile'), setp(pupil=0.7, still=0.8, eye_open=0.6)),
      cam=KP(T(306), w(306, 'felt') - 0.1, 960, 540, 1.0, 990, 530, 1.3))
    C(w(306, 'felt') - 0.1, 'bust', who='grandpa_bed', bg='hospital', expr='still_smile', act=setp(pupil=0.65, lock=1.0, eye_open=0.7),
      cam=dict(mv='creep', x=960, y=560))
    C(T(307), 'hospital', lap=True, bpm=52, bed_act=_A(ex('still_smile'), setp(pupil=0.7, still=0.8)), cam=KP(T(307), w(307, 'and', 1) - 0.1, 960, 540, 1.2, 1000, 545, 1.9))
    C(w(307, 'and', 1) - 0.1, 'lap', who='grandpa_bed', bg='hospital', x=880, y=930, h=1300,
      act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1), ex('still_smile'), setp(turn=0.15)),
      dact=_A(lambda a, s: a.set(-9, None, 0.1, h_turn=-0.6), lambda a, s: a.wink(w(307, 'word') + 0.1, 1, 0.4)), cam=dict(mv='creep', x=940, y=500))
    C(T(308), 'hospital', view='close', bed='walter', lap=True, bpm=118, bed_act=_A(lambda a, s: a.in_bed(), lambda a, s: a.vent_pose(side=1),
                                                                                 setp(turn=0.15), ex('lucid'), tremble(0.8)),
      dact=LIMP, cam=KP(T(308), T(309), 960, 540, 1.0, 990, 540, 1.5))
    # it came home in a box to wait for a new one. A young one.
    C(T(309), 'hall', light=0.0, living=0.0, kitchen=0.0, case='closed', envelope=False, focus=1.7,
      cam=KP(T(309), T(310), 900, 570, 1.0, 800, 600, 1.8, 1.0, 1.08))
    C(T(310), 'bust', who=ON, bg='den', lamp=0.6, act=setp(lock=1.0, pupil=0.62, still=1.0), cam=dict(mv='fast', x=960, y=600), hit=t(310) + 0.05)
    # it told me rule two was the lie, so I'd never doubt the one it actually wrote: rule six tears
    C(T(311), 'rule', n=6, bg='den', recall=True, mode='tear', reveal=w(311, 'actually') - 0.05)

    # ============================================================ THE END (655.5 - 710.5)
    # in my arms he opens his eyes, looks up at me, tries to wink: both eyelids close. Click, click. Owen can't wink.
    C(T(312), 'carry', bg='den', x=900, y=2350, h=2400, cam=dict(mv='keys', keys=[(T(312), 960, 560, 1.0), (T(314), 960, 470, 1.3, 'in_out')]),
      music=[(T_OPEN, 'hit', 0.6)])
    tw2 = w(315, 'both') + 0.1
    C(T(314), 'bust', who='winks', bg='den', ecu=True, cx=960, cy=660, scale=1.4, act=_A(setp(h_nod=-0.2), lambda a, s: a.try_wink(tw2, 0.5, 2.0, 0.8)),
      cam=dict(mv='creep', x=960, y=520), music=[(tw2, 'stinger', 0.8)])
    C(T(317), 'bust', who=O, bg='living', lamp=0.15, light=TVL, era='memory', cx=960, cy=640, scale=1.2,
      act=_A(ex('kid_grin'), lambda a, s: a.try_wink_kid(w(317, 'wink') + 0.05, 0.8)), cam=dict(mv='creep', x=960, y=540))
    # 8 AM: the museum; you tell Mom everything; she thinks it's grief; Owen waves at the window as the van pulls away
    C(T(319), 'hdoor', tod='morning', light=0.0, door=door_swing(t(319) + 0.4, 1.6, 0.0, 0.85), case=None, focus=3.0,
      cam=KP(T(319), T(320), 960, 560, 1.0, 960, 540, 1.25), sfx=[(t(319) + 0.4, 'door_creak', -4, 0, 'inside', dict(kind='front_door'))])
    C(T(320), 'bust', who=Y, bg='hdoor', tod='morning', door=0.85, light=MORNING, act=_A(ex('fear'), lambda a, s: a.scream(w(321, 'scream') - 0.4, e(321))),
      cam=dict(mv='hand', x=960, y=580))
    C(T(322), 'bust', who=M, bg='hdoor', tod='morning', door=0.85, light=MORNING, act=_A(ex('sad'), down(-1, 0.3)), cam=dict(mv='push', x=960, y=580))
    tv0 = w(324, 'van') - 0.6
    C(T(324), 'street', van=dict(drive=('out', tv0, tv0 + 4.5, -5.5, -14.0)),
      ppl=[P(ON, at='owen', act=_A(turned(2.0), lambda a, s: a.wave(w(324, 'waves') - 0.1, 678.0)))],
      cam=KP(T(324), w(324, 'pulls'), 960, 540, 1.0, 960, 540, 1.3), focus=3.75, sfx=[(tv0, 'van_pull_away', 0, 0.3, 'outside', dict(dur=5.0))])
    C(w(324, 'pulls'), 'street', view='outside', van=dict(drive=('out', tv0, tv0 + 4.5, -5.5, 14.0)),
      ppl=[P(ON, at='owen_window', act=_A(lambda a, s: a.wave(s.t0 - 2, 678.0), lambda a, s: a.set(-9, None, 0.1, smile=0.5, lock=1.0)))],
      cam=KP(w(324, 'pulls'), T(325), 960, 540, 1.6, 900, 560, 2.4), focus=17.6)
    # behind glass, three states away: he'll try to wink at you. He can't. Wink back.
    C(T(325), 'museum', view='wide', act=stage('owen'), cam=KP(T(325), T(326), 960, 520, 1.0, 950, 500, 1.6), tags=[(t(325) + 1.0, 'THREE STATES AWAY', 960, 170, 'white', 2.2)])
    tw3 = w(326, 'wink') + 0.05
    C(T(326), 'museum', act=_A(stage('owen'), lambda a, s: a.try_wink(tw3, 0.45, 0.9, 0.7)), cam=KP(T(326), T(327), 960, 520, 1.0, 960, 470, 1.7))
    C(T(327), 'bust', who='winks', bg='museum', ecu=True, cx=960, cy=640, scale=1.4, light=MUSEUM, era='later',
      act=_A(stage('owen'), lambda a, s: a.try_wink(t(327) + 0.1, 0.4, 0.6, 0.5)), cam=dict(mv='creep', x=960, y=520))
    C(T(328), 'museum', act=stage('owen'), cam=KP(T(328), T(330), 960, 470, 1.6, 960, 450, 2.35, 1.0, 1.08))
    # the boy who came home with us doesn't laugh any more; coffee with two sugars; he's nine; the doorway; "kiddo"
    C(T(330), 'bust', who=ON, bg='living', tv=dict(on=-10.0, snow=0.0), lamp=0.3, light=TVL, act=setp(lock=1.0, pupil=0.62, still=1.0, smile=0.0),
      cam=dict(mv='creep', x=960, y=590), sfx=[(t(330) + 0.3, 'studio_laughter', -16, -0.3, 'tv', dict(dur=2.4, level=0.7))])
    C(T(331), 'kitchen', view='chair', tod='morning', mug=False, era='later', grade='morning',
      ppl=[P(ON, at='chair', act=_A(sitp(), lambda a, s: a.hold_mug(s.t0 - 1, None, side=1, sip=[w(331, 'coffee') - 0.3]), setp(lock=1.0, still=1.0)))],
      cam=KP(T(331), T(332), 960, 560, 1.0, 960, 520, 1.45), focus=1.95)
    C(T(332), 'ins', name='mug', era='later', grade='morning', kw=dict(stir=lambda tt: 0.8 * tt), cam=dict(mv='push', x=900, y=640, z=1.3, rate=0.04),
      sfx=[(t(332) + 0.15, 'spoon_clink', -8, 0, 'close', dict(kind='clink')), (t(332) + 0.55, 'spoon_clink', -10, 0, 'close', dict(kind='clink'))])
    C(T(333), 'bedroom', hall=1.0, door=0.85, ppl=[P(ON, path=(t(333) + 0.6, t(333) + 2.4, [('h', 1.3, 3.45), 'doorway'], 0.0), act=setp(lock=1.0, still=0.8),
                                                    surface='inside')],
      cam=KP(T(333), T(334), 960, 560, 1.0, 960, 540, 1.3), focus=3.45, music=[(t(333), 'drone', 0.6, 8.0)])
    C(T(334), 'bedroom', hall=1.0, door=0.85, ppl=[P(ON, at='doorway', act=lambda a, s: a.doorway_smile(t(334), e(335) - t(334) + 0.3))],
      cam=KP(T(334), T(336), 960, 540, 1.3, 980, 520, 2.4, 1.0, 1.06), focus=3.45)
    C(T(336), 'bust', who=ON, bg='bedroom', light=BACKLIT, ecu=True, cx=960, cy=600, scale=1.3,
      act=lambda a, s: a.doorway_smile(s.t0 - 5.0, 4.0), cam=dict(mv='creep', x=960, y=540), music=[(t(336), 'silence', 0.0, 0.0)])
    C(T(337), 'bedroom', hall=lambda tt: 1.0 - 0.75 * ease_in_out(clamp((tt - t(338) - 0.2) / 1.0)), door=0.85,
      ppl=[P(ON, at='doorway', act=lambda a, s: a.doorway_smile(t(334), 4.0))], cam=KP(T(337), e(338) + 0.25, 980, 520, 2.2, 980, 520, 2.4), focus=3.45,
      sfx=[(t(338) + 0.2, 'light_switch', -10, 0.1, 'inside')])
    C(e(338) + 0.25, 'black', cut='static', sfx=[(e(338) + 0.25, 'impact_hit', 4, 0, None, dict(size=1.4)), (e(338) + 0.25, 'sub_drop', 0, 0, None)],
      music=[(e(338) + 0.25, 'end', 0.8, 2.6)])


def plan_globals(F, t, e, w, G):
    """Film-wide cues: the studio laughter waves (applause = he moves), the clack and voice moments, music colour."""
    for lt in LAUGH_T:
        tv = 294.0 < lt < 500.0
        G.append(_ev(lt, 'studio_laughter', -4 if not tv else -2, -0.3 if tv else 0.0, 'tv', dur=2.6, level=1.0 if lt in (305.45, 314.85, 485.0) else 0.75,
                     roar=lt in (305.45, 314.85)))
        if tv and 300 < lt < 330:
            G.append(_ev(lt + 0.05, 'applause', -10, -0.3, 'tv', dur=2.2))
    for (ta, s0, s1, cut) in F.tv_voices:                        # the tape's own voice: a replay of the recording through the TV
        G.append(_ev(ta, 'tv_voice', -14, -0.3, 'tv', src_t0=round(s0, 3), src_t1=round(min(s1, s0 + cut), 3), cut=cut < 50))
    G.append(_ev(445.25, 'tape_stop', -8, -0.3, 'tv', kind='warble', dur=0.5))
    G.append(_ev(t(36) - 0.5, 'heartbeat', -8, 0, None, bpm=96, bpm_end=118, dur=8.0))
    G.append(_ev(t(157), 'heartbeat', -6, 0, None, bpm=84, bpm_end=120, dur=8.0))
    G.append(_ev(543.7, 'heartbeat', -4, 0, None, bpm=78, bpm_end=132, dur=round(T_SWAP - 543.7, 2)))
    G.append(_ev(t(193) - 0.3, 'breath', -10, 0.0, 'close', kind='held', dur=2.4))
    for ti, kind in ((7, 'motif'), (28, 'swell'), (41, 'motif'), (63, 'swell'), (99, 'swell'), (145, 'swell'), (156, 'swell'), (198, 'swell'),
                     (210, 'swell'), (225, 'swell'), (243, 'swell'), (254, 'swell'), (300, 'motif'), (312, 'swell'), (330, 'swell')):
        G.append({'t': round(t(ti), 3), 'type': kind, 'level': 0.6, 'len': 6.0 if kind == 'swell' else 4.0})
    for tr in (t(60), t(68), w(108, 'turned'), T_TV_ON, w(144, 'empty'), t(157), w(161, 'hand'), t(196), w(210, 'camera'), w(242, 'gone'),
               t(268), w(311, 'actually'), w(315, 'eyelids'), t(336)):   # risers peak ON the reveal
        G.append({'t': round(tr, 3), 'type': 'riser', 'level': 0.6, 'len': 3.0})
    G.append({'t': round(543.7, 3), 'type': 'pulse_on', 'level': 0.8})
    G.append({'t': round(T_SWAP, 3), 'type': 'pulse_off', 'level': 0.5})
    G.append({'t': 299.5, 'type': 'theme', 'level': 0.6, 'len': 6.0})


# ==================================================================================================== tools
def contact_sheets(F, prefix, cols=8, rows=6, size=(960, 540), tile=240, ts=None):
    import cv2
    ts = ts if ts is not None else [(s.t0 + s.t1) / 2 for s in F.shots]
    tiles = []
    for k, t in enumerate(ts):
        try:
            img = F.frame(t, int(t * FPS))
        except Exception as ex_:
            import traceback; print('FRAME ERROR t=%.2f shot %s: %r' % (t, F.shot_at(t), ex_)); traceback.print_exc(limit=-3)
            img = np.zeros((size[1], size[0], 3), np.uint8); img[..., 0] = 120
        im = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (tile, tile * 9 // 16), interpolation=cv2.INTER_AREA)
        sh = F.shot_at(t)
        cv2.putText(im, '%d %s %.1f' % (sh.idx, sh.kind, t), (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    paths = []
    per = cols * rows
    for s0 in range(0, len(tiles), per):
        tl = tiles[s0:s0 + per]
        while len(tl) % cols: tl.append(np.zeros_like(tiles[0]))
        sheet = np.vstack([np.hstack(tl[i:i + cols]) for i in range(0, len(tl), cols)])
        p = '%s_%02d.jpg' % (prefix, s0 // per)
        cv2.imwrite(p, sheet, [cv2.IMWRITE_JPEG_QUALITY, 82]); paths.append(p)
    return paths



def cut_frames(F, prefix, size=(480, 270), rng=None, cols=4):
    """Every cut as a pair: the last frame of shot k | the first frame of shot k+1 (pops between cuts), rendered over MAGENTA
    so a camera aimed past a set plate shows as magenta (holes are counted per frame -> prefix_holes.json)."""
    import cv2
    ks = range(len(F.shots) - 1) if rng is None else range(rng[0], min(rng[1], len(F.shots) - 1))
    pairs, holes = [], []
    for k in ks:
        a, b = F.shots[k], F.shots[k + 1]
        ims = []
        for tt, sh in ((b.t0 - 1.0 / FPS, a), (b.t0, b)):
            img = F.frame(tt, int(round(tt * FPS)), bg='#ff00ff')
            mag = float(np.mean((img[..., 0] > 200) & (img[..., 1] < 60) & (img[..., 2] > 200)))
            if mag > 0.0005: holes.append(dict(shot=sh.idx, kind=sh.kind, t=round(tt, 3), hole=round(mag, 4)))
            im = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), size, interpolation=cv2.INTER_AREA)
            cv2.putText(im, '%d %s %.2f' % (sh.idx, sh.kind, tt), (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 255, 255), 1, cv2.LINE_AA)
            ims.append(im)
        pair = np.hstack([ims[0], np.full((size[1], 4, 3), 255, np.uint8), ims[1]])
        pairs.append(pair)
    paths = []
    per = cols * 6
    for s0 in range(0, len(pairs), per):
        tl = pairs[s0:s0 + per]
        while len(tl) % cols: tl.append(np.zeros_like(pairs[0]))
        rows = [np.hstack([np.pad(x, ((4, 4), (6, 6), (0, 0))) for x in tl[i:i + cols]]) for i in range(0, len(tl), cols)]
        p = '%s_%02d.jpg' % (prefix, s0 // per)
        cv2.imwrite(p, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80]); paths.append(p)
    json.dump(holes, open(prefix + '_holes.json', 'w'), indent=1)
    return paths, holes


def lip_check(F, fps=30.0):
    """Mouths move only on their own lines: for every shot and actor, sample the pose and measure the mouth (m_open for
    people, the jaw for Mister Winks) inside and outside its own voice lines. Explicit jaw actions (jaw_hang / jaw_drop /
    clack / the bookcase chatter) are listed separately. Returns rows and prints the offenders."""
    rows = []
    for sh in F.shots:
        F._build(sh)
        for a in sh.actors:
            who = a.who
            lines = []
            if who == 'winks':
                v = TAPE_VOICE if a._arc is CH.WINKS_TAPE_ARC else VOICE['winks']
                lines = [(l['t'], l['end']) for l in F.voice_lines(sh.t0, sh.t1, v)]
                if v is TAPE_VOICE: lines += [(ta, ta + min(s1 - s0, c)) for ta, s0, s1, c in F.tv_voices]
            else:
                lines = [(l['t'], l['end']) for l in F.voice_lines(sh.t0, sh.t1, VOICE.get(who, []))]
            base = None
            on, off, n_on, n_off = 0.0, 0.0, 0, 0
            for tt in np.arange(sh.t0 + 0.02, sh.t1 - 0.02, 1.0 / fps):
                P_ = a.at(float(tt))
                mv = P_.jaw if who == 'winks' else P_.m_open
                inside = any(l0 - 0.08 <= tt <= l1 + 0.12 for l0, l1 in lines)
                if inside: on = max(on, mv); n_on += 1
                else: off = max(off, mv); n_off += 1
            rows.append(dict(shot=sh.idx, t0=round(sh.t0, 2), kind=sh.kind, who=who, lines=len(lines), mouth_on=round(on, 3), mouth_off=round(off, 3)))
        F._built.clear()
    return rows

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--timeline', default=os.path.join(ALIGN, 'timeline.json'))
    ap.add_argument('--cues', action='store_true')
    ap.add_argument('--out', default=None, help='cue sheet dir (default W/cues)')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--range', nargs=2, type=int, default=None)
    ap.add_argument('--size', default='960x540')
    ap.add_argument('--tile', type=int, default=240)
    ap.add_argument('--cols', type=int, default=8)
    ap.add_argument('--bench', type=int, default=0, help='N shots x 4 frames at --size (use 2560x1440), one process')
    ap.add_argument('--shots', default=None, help='comma-separated shot indices for --bench')
    ap.add_argument('--threads', type=int, default=None)
    ap.add_argument('--frames', default=None, help='cut pairs (last | first frame) over magenta -> PREFIX_NN.jpg + PREFIX_holes.json')
    ap.add_argument('--lipcheck', action='store_true')
    a = ap.parse_args()
    if a.threads is not None:
        import cv2; cv2.setNumThreads(a.threads)
    W_, H_ = (int(v) for v in a.size.split('x'))
    set_render_size(W_, H_)
    t_ = time.time()
    F = Film(json.load(open(a.timeline)))
    print('%d shots built in %.1fs' % (len(F.shots), time.time() - t_))
    if a.list:
        for s in F.shots: print('%3d %7.2f %5.2f %-8s' % (s.idx, s.t0, s.d, s.kind))
        ds = np.array([s.d for s in F.shots])
        print('shots %d  median %.2f  p10 %.2f  p90 %.2f  min %.2f' % (len(ds), np.median(ds), np.percentile(ds, 10), np.percentile(ds, 90), ds.min()))
    if a.cues:
        sfx, mus = F.cues(a.out)
        print('sfx %d, music events %d -> %s' % (len(sfx), len(mus['events']), a.out or CUES_DIR))
    if a.bench:
        idx = [int(v) for v in a.shots.split(',')] if a.shots else np.linspace(0, len(F.shots) - 1, a.bench).round().astype(int)
        rows, t_all = [], time.time()
        for k in idx:
            s_ = F.shots[k]
            for j in range(4):
                tt = s_.t0 + min(s_.d - 0.02, 0.1 + j * max(0.05, (s_.d - 0.2) / 3))
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
        print(paths); print('holes:', len(holes), holes[:20])
    if a.lipcheck:
        rows = lip_check(F)
        os.makedirs(TESTS, exist_ok=True)
        json.dump(rows, open(os.path.join(TESTS, 'lipcheck.json'), 'w'), indent=0)
        bad = [r for r in rows if (r['who'] != 'winks' and r['mouth_off'] > 0.12) or (r['lines'] and r['mouth_on'] < 0.08)]
        for r in bad: print('CHECK', r)
        print('lipcheck: %d actor-shots, %d flagged -> %s' % (len(rows), len(bad), os.path.join(TESTS, 'lipcheck.json')))
    if a.sheet:
        sh = F.shots[a.range[0]:a.range[1]] if a.range else F.shots
        print(contact_sheets(F, a.sheet, cols=a.cols, tile=a.tile, ts=[(s.t0 + s.t1) / 2 for s in sh]))
