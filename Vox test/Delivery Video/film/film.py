"""film.py: the shot list, editor and cue sheets for "If A Delivery Driver Rings Your Doorbell At 3 AM... DON'T SIGN FOR IT".

Built the way the police film was ("If A Police Officer Knocks At Midnight...", film_police_ref.py): the same format,
craft and pace, the same engine, cast system and set system, the police header / rule cards / captions and global look.

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration 640.7 s + tail)
    F.shots                          # [Shot(t0, t1, kind, p)] ~250 shots, hard cuts (a few static / glitch / white flashes)
    F.cues(out_dir=None) -> (sfx, music)   writes W/cues/sfx_cues.json + music_cues.json (ARCHITECTURE contract)
    python3 film.py --cues | --sheet PREFIX [--range a b] | --list | --bench N [--size 2560x1440]

Shot kinds (builders B_<kind>):
  street   house 144 from across the street, the NIGHTLINE van at the curb, hazards (era='memory': 21 years ago)
  door     the doorbell camera (fisheye, fixed camera, post-push into the footage, people leaning into the lens bulge):
           the driver staged (ring the bell, tablet up, tilt the box, tap the label, lean close, listen, eyeshine,
           slow look to the side, set the box down, photo flash, walk to the van), the acting box beside his boots, the
           box against the door later; doorbell HUD with the story clock (3:07 -> 3:40), the 3:09/3:08 flicker
  peep     the peephole (subjects ease toward the lens)
  bust     face close-ups over a blurred, darkened set (driver on the porch, you / mom in the hall, you with the thing
           standing behind you in the hall, Lily in her room, dad in memory); framings rotate (BUST_FRAMES)
  hall     the front hall facing the door (stairs, key bowl): you and mom staged, knocks at chest height, the box's
           shadow under the door; grade 'memory' for dad 21 years ago
  hallback the hall seen from the door into the house (behind you): the far end, the stairs, the 3:11 clock, the dark
           figure standing at the end of the hall
  upstairs the upstairs corridor to Lily's door (a crack of moon glow, pushed open)
  lily     Lily's room (moon nightlight, the window open, the bed empty) or her window view (the van pulling away)
  side     the side of the house under Lily's window
  photo    the 3:41 delivery photo full screen (sets.photo_lily_scene, the same still the app shows: from below, Lily leaning
           out of her open sash, the driver from behind holding his tablet up to her sill and grinning back over his
           shoulder into the flash, her small finger on the signature box; crops full / lily / arm / finger)
  doorway  the front door open from inside (night: the box backlit; memory: dad going out; dawn: mom opens it)
  box      the tall taped box close (knocks from inside bulge and jolt it; the tape cut at sunrise)
  ins      prop inserts (label, label_to, tablet_sign, tablet_lily, key_bowl(_dad), box_keys, van_seat, lock_inside)
  keys     the rusted keyring on the D-A-D keychain lifted out of the box at sunrise
  hand     mom's hand shaking at the door chain (and your hand catching her wrist)
  phone    the Nightline app on your phone over the blurred house (notification, order, photo, tracker, Return complete)
  wave     the doorbell microphone waveform panel (police B_wave format: the voice in the box, the lips coming late)
  kitchen / living / latch   the rule-7 window montage (kitchen, living room, bathroom, mom's room)
  rule     rule card over a blurred live scene (the police card style, these 7 rules)
  black    the hard cut to black after the last knock

Plan conventions (plan() at the end of the file, as in the police film): F.cut(t, kind, **p) starts a shot; it ends at
the next cut. Times come from the timeline (F.t(i) line start, F.e(i) line end, F.w(i, 'word') ASR word start inside
line i). Common p keys: cam=dict(mv='push'|'fast'|'creep'|'pull'|'drift'|'move'|'hand', x, y, z, rate, x1, y1, z1,
snap=(t, k), hit=[t], opt=k, d=depth); ppl=[P(who, at=anchor|(x, y, depth, h)|('v', X, D), act=f(acting, shot),
lean=True, path=...)]; tags=[(t, text, x, y, style, hold[, pin])]; sfx=[(t, name, gain_db, pan, space, params)];
music=[(t, type, level, len)]; cut='static'|'glitch'|'white' (quiet_cut=True: no impact on it); post={...}; post_fn=f(t)->{...}.
Continuous moves instead of cuts (fix 3): cam=dict(mv='keys', keys=[(t, x, y, z[, ease[, f]])]) is one multi-key move
(KeyCam: z = dolly, f = optical zoom, so deep sets can be pushed right up to their far wall; DP(x, y, d) centres a point
of a depth-d layer); door shots take posts=[(t0, t1, z0, z1, x, y[, ease])] (chained pushes into the footage); phone
shots zkeys=[(t, scale, zx, zy[, ease])] (the phone comes up / the push travels down the screen) and sig=0..1|f(t)
(Lily's signature hidden until the reveal); the 3:41 photo path=[(t, cx, cy, width[, ease])] (one move over the live
still); handheld_hz, steps_fade (dB), tag_sound=False, phone_glow=t, pov_push=t (upstairs: your hand opens her door),
clock=seconds (doorbell HUD override). Lens shots on the deep sets (DEEP_SETS) get a 2.8 %/s post push + drift.
The box (F.boxa, one characters.BoxActing for the whole film) knocks on the film clock: every shot that shows it jolts
on the same hits and the cue sheet gets one box_knock per hit (space by the shot on screen).
The driver's smile follows characters.DRIVER_ARC on the film clock (S0 a fixed uncanny grin with a line of teeth -> S1 66 s ->
S2 139 s -> S3 185 s -> S4 341 s -> OFF 436 s -> S5 446 s); he talks through it (talk 0.72) and his mouth lags his voice
0.2 s; escalate() adds the cast's twitch / tremble arc.
Global look (glob_fx): per-family exposure, the last 35 % creeping into red_alert, a faster climax ramp from rule 7
(508 s: redder, darker) with the van's hazards washing the frame in blinking red (engine.post.Spill) until they stop at
T_HZ_OFF, a second ramp over the last minute, scare flashes, fade in / out (the police film's global look). Measured
(480x270, every 3 s): red pixels 4.5 % over the last 35 % (<= 0.6 % before), luma 39 vs 44 in the first 65 %.

Measured (W/tests/film/): 235 shots (fix 3), median 2.41 s (p10 1.36, p90 4.19), 644.22 s; before fix 3 (254 shots), 2560x1440, one process, one OpenCV thread,
160 frames over 40 shots: 0.38 s/frame mean incl. cold caches, 0.28 s steady, heaviest shot 0.45 s steady; heaviest chosen
shot (doorway 122) 0.54 s steady (shared machine with the mix running; police budget 0.6). Preview 640x360 / 30 fps with 2
workers: see README.md.
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

W = os.path.join(HERE, '_work')                                         # this film's work dir
ALIGN = os.path.join(W, 'align')
CUES_DIR = os.path.join(W, 'cues')
TESTS = os.path.join(W, 'tests', 'film')
WORDS = os.path.join(ALIGN, 'asr_cache.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
GLOBAL_PPUSH = 0.02              # uniform post push (per second) added to every non-lens shot
DEEP_SETS = ('upstairs', 'side', 'hallback', 'lily')        # lens shots on deep sets: they get their own post push (fix 3)
WHO = {'D': 'driver', 'M': 'mom'}          # X = the voice in the box / behind you: no mouth on screen
H._hand = CH.hud_phone_hand      # the character module's hand on the phone UI
DOORBELL = get_lens('doorbell')
DOORBELL_IR = get_lens('doorbell_ir')
AMBER = '#ffa232'

RULES = {1: "Don't *open the door* to sign.",
         2: "Don't say *anyone's name* out loud.",
         3: "If the delivery photo shows the *inside of your house*, *don't turn around*.",
         4: "Don't let *anyone else* sign for you.",
         5: "*Don't answer* the box.",
         6: "If he leaves the package, *don't bring it inside* before *sunrise*.",
         7: "If the knocking stops and the van is still outside, *check every window* in the house."}

# story beats (film seconds)
T_RING = 34.37 + 1.3             # the doorbell rings
T_BOX_DOOR = 462.4               # the box stands against the front door from here
T_IN_VAN = 470.4                 # the driver is in the cab (silhouette at the wheel)
T_SEAT_EMPTY = 496.0             # ... and gone from it
T_HZ_OFF = 591.65                # "you see the van's hazard lights STOP blinking" (on the word)
T_VAN_GO = (593.4, 597.6)        # the van pulls away (headlights off)
T_DAWN = 598.1                   # 6:12 the sun comes up
T_STING = 618.9                  # the next night, 3:07


def _hms(h, m, s=0): return h * 3600 + m * 60 + s


# the story clock (doorbell HUD, header corner): 3:07 when the phone lights up, 3:11 by the photo, real time through the
# night, cut-jumps to 3:40 ("the knocking stops"), 3:41 (Lily's photo), 6:12 (sunrise), then the next night at 3:07
CLOCK = [(0.0, 26.04, _hms(3, 6, 48), _hms(3, 7, 0)), (26.04, 205.0, _hms(3, 7, 0), _hms(3, 11, 0)),
         (205.0, 488.0, _hms(3, 11, 0), _hms(3, 15, 43)), (488.0, 497.79, _hms(3, 39, 50), _hms(3, 40, 0)),
         (497.79, 549.0, _hms(3, 40, 0), _hms(3, 41, 10)), (549.0, T_DAWN, _hms(3, 41, 10), _hms(3, 42, 2)),
         (T_DAWN, T_STING, _hms(6, 12, 0), _hms(6, 12, 21)), (T_STING, 700.0, _hms(3, 7, 0), _hms(3, 8, 21))]


def story_clock(t):
    for a, b, s0, s1 in CLOCK:
        if a <= t < b: return s0 + (s1 - s0) * (t - a) / (b - a)
    return CLOCK[-1][3]


def clock_hm(t):
    s = int(story_clock(t)); h, m = (s // 3600) % 24, (s // 60) % 60
    return '%d:%02d AM' % ((h % 12) or 12, m)


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


# ==================================================================================================== lights
def hz_default(t):
    """The van's flashers on the film clock (on from the start, off when Lily sees them stop)."""
    return ST.hazard(t, 1.25, None, T_HZ_OFF)


def porch_light(t, hz=None, base='#ffcf9a', key=0.1, k=1.0, side=1):
    """Rim light on the porch: the warm lantern, swapped for the van's amber flash while the hazards blink."""
    h = (hz or hz_default)(t)
    if h > 0.25:
        return dict(rim=AMBER, rim_a=int(55 + 105 * h * k), side=side, key=key)
    return dict(rim=base, rim_a=70, side=-side, key=key)


def warm_light(t): return dict(rim='#ffcf9a', rim_a=60, side=-1, key=0.15)


def room_light(t): return dict(rim='#8fa6d8', rim_a=55, side=1, key=0.0)


def phone_light(t): return dict(rim='#8fa6d8', rim_a=60, side=1, key=-0.05, under='#bcd2ff', under_a=150)


def moon_light(t): return dict(rim='#c9b8f0', rim_a=85, side=1, key=0.0)


def memory_light(t): return dict(rim='#ffd9a0', rim_a=70, side=-1, key=0.2)


def dawn_light(t): return dict(rim='#ffd2a8', rim_a=90, side=1, key=0.25)


def van_cfg(t0, t1=None, **kw):
    """The van for a shot at film time t0: the driver's silhouette is in the cab only after he climbs back in and
    before his seat is found empty; the flashers stop at T_HZ_OFF."""
    t1 = t0 + 6 if t1 is None else t1
    d = dict(driver=(T_IN_VAN <= t0 < T_SEAT_EMPTY))
    d.update(kw)
    return d


def hz_cfg(t0, t1):
    return dict(t_off=T_HZ_OFF) if t1 > T_HZ_OFF - 6 else True


# ==================================================================================================== the film
class Film:
    def __init__(self, tl):
        self.tl = tl
        self.L = tl['lines']
        self.duration = float(tl.get('duration_en', 640.72)) + 3.5     # fix 3: +1.5 s black so the end cadence fits
        self.words = []
        if os.path.exists(WORDS):
            try:
                self.words = [(w.strip().lower().strip('.,?!;:"“”'), float(t)) for w, t in json.load(open(WORDS))['en_words']]
            except Exception:
                self.words = []
        self._wt = [t for _, t in self.words]
        self.shots = []
        self.globals = []                    # extra global cues (beds, music)
        self.boxa = CH.BoxActing(3)          # the box, on the film clock
        self.box_events = []
        self.ts_flicker = []                 # (t, clock seconds shown) doorbell timestamp overrides
        plan(self)
        self.box_hits = sorted(h for h, _ in self.boxa.hits)
        self.knock_door = ST.knock_pulse([h for h in self.box_hits if h >= T_BOX_DOOR - 0.5])
        self.shots.sort(key=lambda s: s.t0)
        for k, s in enumerate(self.shots):
            s.idx = k
            s.t1 = self.shots[k + 1].t0 if k + 1 < len(self.shots) else self.duration
        self._starts = [s.t0 for s in self.shots]
        assign_bust_framings(self)
        assign_door_framings(self)
        self.rules = [(s.t0, s.p['n']) for s in self.shots if s.kind == 'rule']
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

    def lines_in(self, t0, t1, codes):
        return [l for l in self.L if l.get('found_en', True) and l['who'] in codes and l['end'] > t0 - 0.2 and l['t'] < t1 + 0.2]

    def speaking(self, t, codes):
        return any(l['t'] - 0.05 <= t <= l['end'] + 0.05 for l in self.lines_in(t, t, codes))

    def knocks_in(self, t0, t1):
        return [h for h in self.box_hits if t0 <= h < t1] if hasattr(self, 'box_hits') else \
            [h for h, _ in self.boxa.hits if t0 <= h < t1]

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
        if sh.kind != 'door' and sh.p.get('posts') and isinstance(spec.cam, Cam):   # chained pushes into the finished image
            for q in sh.p['posts']: spec.cam.post_push(q[0], q[1], q[2], q[3], q[6] if len(q) > 6 else 'push', x=q[4], y=q[5])
        if (spec.lens is None and isinstance(spec.cam, Cam) and not spec.cam.posts and mv != 'pull'
                and sh.kind not in ('rule', 'black') and not sh.p.get('no_ppush')):
            spec.cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + GLOBAL_PPUSH) ** max(0.3, sh.d), ease='push')
        elif (sh.kind in DEEP_SETS and isinstance(spec.cam, Cam) and not spec.cam.posts and mv not in ('pull', 'keys')
              and sh.p.get('view') != 'window' and not sh.p.get('no_ppush')):
            # fix 3: these sets are 3-5 m deep, so a dolly push of 3 %/s moved their far wall < 1 %/s (shots read static):
            # add a uniform 2.8 %/s push into the image with a slow lateral drift
            sgn = 1 if sh.idx % 2 else -1
            spec.cam.post_push(sh.t0, sh.t1, 1.0, 1.028 ** max(0.3, sh.d), ease='push', x=sgn * 9.0 * sh.d, y=-3.0 * sh.d)
            if sh.kind == 'upstairs':
                spec.cam.shake, spec.cam.shake_hz = max(spec.cam.shake, 3.4), 0.75
        if len(self._built) > 3: self._built.clear()
        self._built[sh.idx] = spec
        return spec

    # ---------------------------------------------------------------- frame
    def frame(self, t, i):
        sh = self.shot_at(t)
        spec = self._build(sh)
        fx = spec.fx(t) if spec.fx else {}
        fx = dict(fx or {})
        glob_fx(self, sh, t, fx)
        cs = spec.cam.at(t) if spec.cam is not None else None

        def hud_all(cv, tt):
            if spec.hud: spec.hud(cv, tt)
            self.overlay(cv, tt, sh)
        return render_frame(spec.layers, cs, t, i, focus=spec.focus, dof=spec.dof, lens=spec.lens, grade=spec.grade, post=fx, hud=hud_all)

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
        # one clock for the whole film: the story clock drives the doorbell HUD's timestamp and the header corner; on
        # doorbell shots the doorbell HUD owns the top corners, so the header is left out there
        if sh.kind == 'black': return
        if sh.kind not in ('door', 'photo'):
            H.header(cv, self.header_text(t), clock_hm(t))
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
        sfx.extend(box_cues(self))
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


def shot_table(F):
    """The cut list for the sound team: [{i, t0, t1, kind, space, loc}]."""
    out = []
    for s in F.shots:
        sp = bust_space(s) if s.kind in ('bust',) else SPACE.get(s.kind)
        out.append({'i': s.idx, 't0': round(s.t0, 3), 't1': round(s.t1, 3), 'kind': s.kind, 'space': sp,
                    'loc': LOC.get(s.kind), 'era': s.p.get('era', 'now'), 'cut': s.p.get('cut')})
    return out


# ==================================================================================================== camera
class KeyCam(Cam):
    """Cam whose keys also carry an optical zoom f (no parallax): a deep set (Lily's room, 3.4 m to the window) can be
    pushed right up to its far wall while the dolly part keeps the parallax. fkeys [(t, f, ease)] interpolate like the keys
    (geometric, the same per-segment eases)."""
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
    if t > 560: return 0.034
    if t > 430: return 0.03
    if t > 275: return 0.027
    return 0.024


def mkcam(sh, mv='push', x=960, y=540, z=1.0, rate=None, dx=0.0, dy=0.0, shake=1.6, roll=0.0, x1=None, y1=None, z1=None,
          snap=None, hit=None, opt=None, d=None, keys=None):
    """opt: constant optical zoom (no parallax; frames far layers); d: x, y (and x1, y1) are points on a layer at depth d.
    mv='keys': one continuous move through keys=[(t, x, y, z[, ease])] (absolute film seconds; ease of the segment arriving
    at the key, default 'in_out'; the first key's time may precede the shot), so a push, a hold-creep and a pan can live in
    one shot instead of three cuts."""
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
    elif mv == 'move':                        # explicit start / end framing
        c = Cam([(t0, x, y, z, roll), (t1, x1 if x1 is not None else x, y1 if y1 is not None else y, z1 or z * (1 + r * sh.d), roll, 'push')],
                shake=shake, seed=sh.idx)
    elif mv == 'keys':                        # one continuous multi-key move (push -> creep -> pan ...)
        ks, fk = [], []
        for k in keys:
            kx, ky = (960 + d * (k[1] - 960), 540 + d * (k[2] - 540)) if d is not None else (k[1], k[2])
            ks.append((k[0], kx, ky, k[3], roll, k[4] if len(k) > 4 else None))
            fk.append((k[0], k[5] if len(k) > 5 else 1.0, k[4] if len(k) > 4 else None))
        c = KeyCam(ks, fk, shake=shake, seed=sh.idx)
    elif mv == 'hand':                        # nervous handheld + slow push
        c = push_in(t0, t1, x, y, z, rate=r * 0.8, drift=(dx, dy), shake=4.5, seed=sh.idx)
        c.shake_hz = 0.9
    else:
        c = hold(x, y, z, shake=shake, seed=sh.idx)
    if opt: c.snap(t0 - 30.0, opt, 0.001)
    if snap:                                  # fix 3: an eased 0.24 s push-in (was a 0.1 s overshooting pop: read as a jump cut)
        c.snap_back = False; c.snap(snap[0], snap[1] if len(snap) > 1 else 1.25, 0.24)
    if hit:
        for h in (hit if isinstance(hit, (list, tuple)) else [hit]): c.hit(h, 7.0)
    return c


def cam_from(F, sh, d):
    d = dict(d or {})
    return mkcam(sh, **d)


# ==================================================================================================== actors
def acting(F, sh, who, act=None, seed=0, height=700.0, expr=None, talk=True, blink=None):
    a = CH.Acting(who, seed=seed + sh.idx * 3, height=height, expr=expr or 'neutral', blink=blink)
    if act: act(a, sh)
    escalate(a, sh, who)
    if talk and sh.p.get('era', 'now') != 'memory':
        codes = [c for c, w in WHO.items() if w == who]
        iv = [(l['t'], l['end'], l['en']) for l in F.lines_in(sh.t0, sh.t1, codes)]
        if iv: a.talk(iv)
    sh.actors.append(a)
    return a


def _walk_legs(a, legs, surface='porch'):
    """Walk cycle for one or more walks per actor (police film): legs [(t0, t1, units, facing)]; footstep events.
    surface 'inside' / 'porch'; '<surface>_run' = a run (3.6 steps/s, ~0.28 s a step, leaning in); a '_quiet' suffix drops
    the footstep events (a shot whose explicit run / stairs cue carries the steps)."""
    info = []
    run = '_run' in surface
    quiet = surface.endswith('_quiet')
    stairs = '_stairs' in surface                     # mom down the stairs in slippers: soft, stepped
    base = surface.split('_')[0]
    for (t0, t1, units, face) in legs:
        n = max(2, int(round((t1 - t0) * (3.6 if run else 1.9))))
        cyc = n / 2.0
        info.append((t0, t1, cyc, face))
        if quiet: continue
        for k in range(1, n + 1):
            a._ev(t0 + (t1 - t0) * (k - 0.5) / n, 'footsteps_wood_inside' if base == 'inside' else 'footsteps_porch',
                  -2.0 if run else (-7.0 if stairs else -4.0), pan=0.0, n=1, foot='L' if k % 2 else 'R',
                  **({'run': True} if run else {}), **({'stairs': True, 'slippers': True} if stairs else {}))

    def fn(P, t):
        for (t0, t1, cyc, face) in info:
            if t0 - 0.45 <= t <= t1 + 0.45:
                amt = ease_in_out(clamp((t - t0 + 0.15) / 0.3)) * ease_in_out(clamp((t1 + 0.15 - t) / 0.3))
                w = ease_in_out(clamp((t - t0 + 0.4) / 0.4)) * ease_in_out(clamp((t1 + 0.45 - t) / 0.45))
                P.walk_amt = max(P.walk_amt, amt)
                if run: P.lean += 0.14 * amt
                P.walk_ph = cyc * clamp((t - t0) / max(1e-3, t1 - t0))
                P.turn = lerp(P.turn, face, w)
                P.lean += 0.05 * amt
    a._add(legs[0][0] - 0.5, legs[-1][1] + 0.6, fn)


def escalate(a, sh, who):
    """The film-wide acting arc (characters.escalate on the film clock): the driver twitches / jerks more each act (none
    while his face is perfectly still), you and mom tremble harder as the night goes on. Memory shots and cards: none."""
    if sh.kind in ('rule',) or sh.p.get('era') == 'memory': return
    if who in ('driver', 'you', 'mom'):
        CH.escalate(a, sh.t0, sh.t1, sh.kind)


def figure(F, sh, who, x, y, depth, height, act=None, seed=0, expr=None, light=None, aim=None, lean=False, k=0.55, name=None,
           path=None, detail=None, talk=True, alpha=1.0, facing=0.0, shadow=0.0, surface='porch'):
    """Full-body character layer (police film). path walks along anchors with a real walk cycle and the layer depth
    follows the path. shadow 0..1 draws the figure as a dark silhouette (the thing in the hall)."""
    a = acting(F, sh, who, act, seed, height, expr, talk)
    m = _Memo(a)
    lt = light

    def put(pen, t, lx, ly, lh, P):
        if shadow > 0:
            cv = pen.cv
            # a cold backlight behind it (the kitchen doorway / the stairwell) so the silhouette reads as a shape
            pen.radial(None, lx, ly - lh * 0.55, lh * 0.75, [(0, '#8ea2d8', 70), (0.55, '#5a6a9a', 30), (1, '#5a6a9a', 0)], sy=1.25, clip=False)
            cv.saveLayer(None, None)
            CH.draw(pen, who, lx, ly, lh, P, light=None, t=t, detail=detail, aim=aim)
            cv.drawPaint(skia.Paint(Color=skia.Color4f(0.012, 0.012, 0.025, shadow), BlendMode=skia.BlendMode.kSrcATop))
            cv.restore()
            ey = ly - lh * 0.915; ex = lh * 0.028
            gl = 0.55 + 0.45 * math.sin(t * 1.7)
            for sx in (-1, 1):
                pen.fill(oval(lx + sx * ex, ey, max(2.2, lh * 0.009)), '#e8f0ff', 170 * gl)
                pen.fill(oval(lx + sx * ex, ey, max(5.0, lh * 0.024)), '#c9d6ff', 26 * gl)
        else:
            CH.draw(pen, who, lx, ly, lh, P, light=lt(t) if callable(lt) else lt, t=t, detail=detail, aim=aim)

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

        def dfun(t):
            d = pos(t)[2]
            return d * (1.0 - k * clamp(m(t).approach)) if lean else d

        def local(t):
            px, py, pd, ph = pos(t); s = pd / R
            return 960 + (px - 960) * s, 540 + (py - 540) * s, ph * s

        def draw(pen, t):
            P = m(t).copy(); P.dx = 0.0
            lx, ly, lh = local(t)
            put(pen, t, lx, ly, lh, P)
        lay = Layer(dfun, draw, name or who, ref_depth=R, alpha=alpha)
        lay._pos = pos

        def box(t):
            lx, ly, lh = local(t)
            return (lx - lh * 0.25, ly - lh * 1.05, lh * 0.5, lh * 1.07)
        lay._box = box
        return lay, a
    dfun = a.depth(depth, k) if lean else depth

    def draw(pen, t):
        put(pen, t, x, y, height, m(t))
    lay = Layer(dfun, draw, name or who, ref_depth=depth, alpha=alpha)

    def box(t):
        P = m(t); dx = P.dx
        if aim is not None and P.approach > 0:
            kk = ease_in_out(clamp(P.approach)); dx += (aim[0] - (x + P.dx)) * kk
        return (x + dx - height * 0.27, y - height * 1.08, height * 0.54, height * 1.1)
    lay._box = box
    return lay, a


def bust(F, sh, who, cx=960, cy=560, scale=1.0, act=None, seed=0, expr=None, light=None, depth=1.0, talk=True, name=None):
    a = acting(F, sh, who, act, seed, 700.0, expr, talk)
    m = _Memo(a)

    def draw(pen, t):
        CH.draw_bust(pen, who, cx, cy, scale, m(t), light=light(t) if callable(light) else light, t=t)
    return Layer(depth, draw, name or who, blur=0), a


def anc(sp, name):
    if isinstance(name, tuple) and name and name[0] == 'v':              # ('v', X, D[, Y]) on the set's view
        v = sp.info['view']; a = v.anchor(name[1], name[2], name[3] if len(name) > 3 else 0.0)
        return (a.x, a.y, a.depth, a.height)
    if not isinstance(name, str): return name
    a = sp.anchors[name]; return (a.x, a.y, a.depth, a.height)


HEIGHT_K = {'driver': 1.0, 'you': 1.8 / 1.85, 'mom': 1.62 / 1.85, 'lily': 1.28 / 1.85, 'dad': 1.82 / 1.85}


def people(F, sh, sp, ppl, light):
    """ppl: list of dicts {who, at (anchor name / tuple / ('v', X, D)), act, lean, aim, path, expr, seed, light, shadow}.
    Anchor heights are a 1.85 m adult; each figure is scaled to its own height (Lily 1.28 m ...)."""
    L, A = [], []
    for k, q in enumerate(ppl or []):
        who = q['who']
        at = q.get('at') or 'driver'
        if q.get('path') and (not isinstance(at, str) or at not in sp.anchors):
            pq = q['path']; first = (pq if not isinstance(pq[0], (list, tuple)) else pq[0])[2][0]
            at = first
        x, y, d, h = anc(sp, at)
        hk = q.get('hk', HEIGHT_K.get(who, 1.0))
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
        lay, a = figure(F, sh, who, x, y, d, h * hk, q.get('act'), seed=k * 11 + q.get('seed', 0), expr=q.get('expr'),
                        light=q.get('light', light), aim=q.get('aim'), lean=q.get('lean', False), k=q.get('k', 0.55),
                        name='p%d_%s' % (k, who), path=path, detail=q.get('detail'), talk=q.get('talk', True),
                        facing=q.get('facing', 0.0), alpha=q.get('alpha', 1.0), shadow=q.get('shadow', 0.0),
                        surface=q.get('surface', 'porch'))
        L.append(lay); A.append((q, lay, a))
    return L, A


def dimmed(sp, k, keep=()):
    for l in sp:
        if l.name not in keep and not callable(l.dim): l.dim = max(l.dim if isinstance(l.dim, float) else 0.0, k)
    return sp


# ==================================================================================================== the box
def box_layer(F, sh, x, y, h, depth, view=-0.35, light=None, ref=None, st=None, to='', sender='RETURN', tape=1.0):
    """The acting box (characters.draw_box) on the film clock: F.boxa's knocks bulge and jolt it in every shot."""
    def draw(pen, t):
        s_ = st(t) if callable(st) else (st if st is not None else F.boxa.at(t))
        CH.draw_box(pen, x, y, h, s_, t=t, view=view, light=light(t) if callable(light) else light, to=to, sender=sender, tape=tape)
    return Layer(depth, draw, 'box_acting', ref_depth=ref or depth)


def box_light(t, hz=None):
    h = (hz or hz_default)(t)
    return dict(key='#ffd9a0', rim=AMBER if h > 0.25 else '#9fb6ff', k=0.6 + 0.4 * h)


# ==================================================================================================== builders
def _porch(F, sh, p, view='doorbell'):
    """delivery_porch for a shot: the van's driver flag and flashers on the film clock, the box placement."""
    era = p.get('era', 'now'); tod = p.get('tod', 'night')
    van = p.get('van', van_cfg(sh.t0, sh.t1))
    if p.get('drive'): van = dict(van or {}, drive=p['drive'])
    hz = p.get('hazard', hz_cfg(sh.t0, sh.t1))
    bx = p.get('box', 'boots' if (sh.t0 < T_BOX_DOOR and era == 'now' and tod == 'night') else 'door')
    sbox = None
    if bx == 'door' and tod == 'night':
        sbox = dict(at='door', knock=F.knock_door)
    elif bx == 'door' and tod == 'dawn':
        sbox = dict(at='door', state='open')
    elif isinstance(bx, dict):
        sbox = bx
    if tod == 'dawn':
        sp = ST.delivery_porch(view, van=False, box=sbox if view == 'doorbell' else None, tod='dawn', ir=p.get('ir', False))
    else:
        sp = ST.delivery_porch(view, van=van, hazard=hz, box=sbox if view == 'doorbell' else None, ir=p.get('ir', False), era=era)
    return sp, bx


def B_street(F, sh):
    p = sh.p
    era = p.get('era', 'now')
    if p.get('novan'):
        sp = ST.street_wide(car=False, police=False, vehicle=None, era=era, living_lit=p.get('living', 0.0), bedroom_lit=p.get('bedroom', 0.0),
                            upstairs_left=p.get('upstairs', 0.0))
    else:
        van = p.get('van', van_cfg(sh.t0, sh.t1))
        if p.get('drive'): van = dict(van, drive=p['drive'])
        sp = ST.delivery_street(van=van, hazard=p.get('hazard', hz_cfg(sh.t0, sh.t1)), era=era, bedroom_lit=p.get('bedroom', 0.0),
                                living_lit=p.get('living', 0.0), upstairs_left=p.get('upstairs', 0.0))
    hz = sp.info.get('hazard') if sp.info else None
    L, A = people(F, sh, sp, p.get('ppl'), lambda t: porch_light(t, hz, k=0.6))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    grade = p.get('grade', 'memory' if era == 'memory' else 'night_blue')
    return Spec(sp.add(*L), cam, None, grade, 1.1, 0.0, fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def _doorbell_hud(F, sh, cam, lens, A, p):
    ir = lens is DOORBELL_IR
    tracked = [lay for (q, lay, a) in A if q.get('track', True)]
    flick = p.get('flicker')                     # [(t, clock seconds)] timestamp overrides (3:09 3:09 3:08)

    def hud(cv, t):
        box = None
        if tracked and p.get('mbox', True):
            lay = tracked[0]
            try:
                box = project_box(lay._box(t), lay.depth_at(t), cam.at(t), lens, lay.ref_depth)
                x0, y0, w0, h0 = box
                x1, y1 = min(DW - 30, x0 + w0), min(DH - 60, y0 + h0); x0, y0 = max(30, x0), max(110, y0)
                box = (x0, y0, x1 - x0, y1 - y0) if (x1 - x0 > 40 and y1 - y0 > 40) else None
            except Exception:
                box = None
        secs = story_clock(t) if p.get('clock') is None else p['clock'] + (t - sh.t0)
        glitch = 0.0
        if flick:
            for (tf, s_) in flick:
                if t >= tf: secs = s_ + (t - tf); glitch = max(0.0, 1.0 - (t - tf) / 0.18)
        restore = None
        if p.get('hud_follow'):                   # the app overlay zooms with the footage (timestamp close-up)
            cs = cam.at(t); cv.save(); restore = cv.restore
            cv.translate(960, 540); cv.scale(cs.pz, cs.pz); cv.translate(-960 - cs.px, -540 - cs.py)
        date = 'NOV 12' if t >= T_STING else 'NOV 11'
        H.doorbell_hud(cv, t, name=p.get('cam_name', 'FRONT DOOR'), clock=(0, 0, secs - t), date=date, motion=box, ir=ir,
                       talk=p.get('talk_btn', False))
        if flick and glitch > 0:
            pen = Pen(cv)
            pen.fill(rect(DW - 330, 34, 300, 42), '#ff2a2a', 120 * glitch)
        if restore: restore()
        if p.get('hud'): p['hud'](cv, t)
    return hud


def B_door(F, sh):
    """Doorbell camera: the camera is FIXED (a real doorbell); motion comes from the people, the box and a post-push
    into the footage (zooming the app view), plus the lens bulging anyone who comes close."""
    p = sh.p
    sp, bx = _porch(F, sh, p, 'doorbell')
    hz = sp.info.get('hazard')
    ppl = [dict(q) for q in p.get('ppl', [])]
    for q in ppl:
        q.setdefault('aim', (960, 470))
    lt = (lambda t: dawn_light(t)) if p.get('tod') == 'dawn' else (lambda t: porch_light(t, hz, k=0.8))
    L, A = people(F, sh, sp, ppl, lt)
    if bx == 'boots':
        a = sp.anchors['box_boots']
        L.append(box_layer(F, sh, a.x + p.get('box_dx', 0), a.y, a.height * 0.865, a.depth, -0.35, lambda t: box_light(t, hz),
                           sender=p.get('sender', 'RETURN')))
    if p.get('box_move'):                                         # he carries the box over to the front door
        L.append(_carried_box(F, sh, p['box_move'], hz))
    lens = DOORBELL_IR if p.get('ir') else DOORBELL
    z0, z1 = p.get('z0', 1.0), p.get('z1', 1.0 + push_rate(sh.t0) * 1.9 * sh.d)
    px, py = p.get('px', 0.0), p.get('py', -40.0)
    off = p.get('post_off')
    fr = p.get('frame')
    if fr in ('med', 'close') and A and off is None:              # frame the first person: chest (med) or face (close)
        q0, lay0, a0 = A[0]
        bx, by, bw, bh = lay0._box(sh.t0 + 0.5 * sh.d)
        tx, ty = bx + bw / 2, by + bh * (0.36 if fr == 'med' else 0.1)
        try:
            X, Y = project(tx, ty, lay0.depth_at(sh.t0), None, lens, lay0.ref_depth)
            X, Y = float(X), float(Y)
        except Exception:
            X, Y = tx, ty
        zc = 1.45 if fr == 'med' else 2.05
        z0, z1 = zc, zc * (1.0 + push_rate(sh.t0) * 1.2 * sh.d)
        hw, hh = 960 / z0, 540 / z0
        off = (clamp(X, hw, DW - hw) - 960, clamp(Y + (40 if fr == 'close' else 0), hh, DH - hh) - 540)
        px, py = p.get('px', 0.0) * 0.3, p.get('py', -20.0) * 0.3
    cam = Cam([(sh.t0, 960, 540, 1.0)], shake=0.0, seed=sh.idx)
    if off: cam.post_push(sh.t0 - 20.0, sh.t0 - 19.99, 1.0, 1.0, 'lin', x=off[0], y=off[1])
    if p.get('posts'):                    # merged shots: chained post pushes [(t0, t1, z0, z1, x, y[, ease])] (zooms multiply, offsets add)
        for q in p['posts']: cam.post_push(q[0], q[1], q[2], q[3], q[6] if len(q) > 6 else 'push', x=q[4], y=q[5])
    else:
        cam.post_push(sh.t0, sh.t1, z0, z1, x=px, y=py)
    hits = list(p.get('hit') or [])
    if bx == 'boots' or (bx == 'door' and sh.t0 >= T_BOX_DOOR - 1):
        hits += [h for h in F.knocks_in(sh.t0, sh.t1)]
    for h in hits: cam.hit(h, 5.0)
    hud = _doorbell_hud(F, sh, cam, lens, A, p)
    grade = 'ir_night' if p.get('ir') else ('dawn' if p.get('tod') == 'dawn' else ('memory' if p.get('era') == 'memory' else 'doorbell_night'))

    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(*L), cam, lens, p.get('grade', grade), 1.0, 0.0, fx=fx, hud=hud)


def _carried_box(F, sh, mv, hz):
    """The acting box carried across the porch from beside his boots to the front door (mv = (t0, t1, (X0, D0), (X1, D1))):
    its layer depth follows the move, so it grows and bulges in the fisheye as it comes up to the door beside the lens."""
    t0, t1, (X0, D0), (X1, D1) = mv
    A0, A1 = DA(X0, D0), DA(X1, D1)
    R = A1[2]

    def pos(t):
        u = ease_in_out(clamp((t - t0) / max(1e-3, t1 - t0)))
        lift = 18.0 * math.sin(math.pi * u)
        return tuple(A0[k] + (A1[k] - A0[k]) * u for k in range(4)), lift

    def dfun(t): return pos(t)[0][2]

    def draw(pen, t):
        (x, y, d, h), lift = pos(t); s_ = d / R
        lx, ly, lh = 960 + (x - 960) * s_, 540 + (y - 540) * s_, h * s_ * 0.865
        CH.draw_box(pen, lx, ly - lift * s_, lh, F.boxa.at(t), t=t, view=-0.35, light=box_light(t, hz))
    return Layer(dfun, draw, 'box_carried', ref_depth=R)


def B_peep(F, sh):
    """Peephole: the camera pushes at 4.5 %/s and standing subjects ease toward the lens over the shot."""
    p = sh.p
    sp, bx = _porch(F, sh, p, 'peephole')
    hz = sp.info.get('hazard')
    ppl = [dict(q) for q in p.get('ppl', [])]
    for q in ppl:
        q.setdefault('aim', (960, 520))
        if p.get('approach', True) and not q.get('path') and not q.get('lean') and q.get('track', True) is not False:
            amt = 0.4 if q.get('at') == 'driver_close' else 0.7
            q['act'] = _A(q.get('act'), lambda a, s, amt=amt: a.lean_in(s.t0 - 0.15, max(1.2, (s.t1 - s.t0) * 0.9), amount=amt))
            q['lean'] = True
    L, A = people(F, sh, sp, ppl, lambda t: porch_light(t, hz, base='#ffcf9a', key=0.1, k=0.7))
    if bx == 'boots' and p.get('show_box', True):
        a = sp.anchors['box_boots']
        L.append(box_layer(F, sh, a.x, a.y, a.height * 0.865, a.depth, -0.3, lambda t: box_light(t, hz)))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=520)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = max(0.045, push_rate(sh.t0) * 1.5)
    cd['z'] = cd.get('z', 1.0) * p.get('zk', 1.14)
    cam = cam_from(F, sh, cd)
    for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 6.0)
    grade = p.get('grade', 'memory' if p.get('era') == 'memory' else 'porch_warm')
    return Spec(sp.add(*L), cam, 'peephole', grade, 1.0, 0.0, fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def _bg(F, sh, name, p):
    """Background set for close-ups (drawn at its own depths, blurred by DOF and darkened 30 %)."""
    if name == 'porch':
        sp, _ = _porch(F, sh, dict(p, box=None), 'peephole')
        hz = sp.info.get('hazard')
        light = lambda t: porch_light(t, hz, base='#ffcf9a', key=-0.05)
    elif name == 'dawn':
        sp = ST.sunrise_porch('doorway')
        light = dawn_light
    elif name == 'hall':
        sp = ST.delivery_hall(lamp=p.get('lamp', 0.0), bowl=p.get('bowl', 'house'), outside=p.get('outside')).without('near_frame')
        light = p.get('light_fn') or phone_light
    elif name == 'hall_back':
        sp = ST.hall_back(lamp=p.get('lamp', 0.0), bowl=p.get('bowl', 'house'), kitchen_clock=p.get('clock', '3:11'))
        light = phone_light
    elif name == 'upstairs':
        sp = ST.upstairs_hall(lily_door=p.get('lily_door', 0.07))
        light = moon_light
    elif name == 'lily':
        sp = ST.lily_room(window_open=p.get('window_open', False), bed=p.get('bed', 'sleeping'), hazard=p.get('hz_room'))
        light = moon_light
    elif name == 'memory':
        sp = ST.delivery_hall(lamp=1.0, bowl='house').without('near_frame')
        light = memory_light
    elif name == 'memory_porch':
        sp = ST.memory_porch('doorway')
        light = memory_light
    elif name == 'side':
        sp = ST.side_yard()
        light = moon_light
    else:
        sp = ST.delivery_street(van=van_cfg(sh.t0, sh.t1), hazard=hz_cfg(sh.t0, sh.t1))
        light = lambda t: porch_light(t)
    return dimmed(sp, p.get('bg_dim', 0.3)), light


# bust framings per character: (cx, cy, scale, body turn, head turn relative to the body). Rotated so the same
# (who, bg, framing) never repeats within 60 s (assign_bust_framings); the driver keeps his face to the lens.
BUST_FRAMES = {
    'driver': [(960, 570, 1.0, 0.0, 0.0), (760, 600, 0.9, 0.38, -0.3), (1180, 580, 1.08, -0.4, 0.3), (960, 620, 0.82, 0.0, 0.0),
               (700, 570, 1.12, 0.28, -0.22), (1220, 610, 0.86, -0.55, 0.42)],
    'you': [(960, 580, 1.0, 0.0, 0.0), (1180, 610, 0.9, -0.55, 0.0), (720, 580, 1.08, 0.5, -0.2), (960, 640, 0.78, 0.0, 0.0),
            (1240, 560, 1.15, -0.35, 0.1), (680, 620, 0.88, 0.75, -0.15)],
    'mom': [(960, 590, 1.0, 0.0, 0.0), (720, 600, 0.92, 0.55, 0.0), (1200, 590, 1.06, -0.45, 0.1), (960, 650, 0.8, 0.0, 0.0),
            (680, 570, 1.12, 0.35, -0.1), (1240, 620, 0.88, -0.75, 0.15)],
    'lily': [(960, 600, 1.0, 0.0, 0.0), (1180, 620, 0.92, -0.4, 0.1), (740, 610, 1.06, 0.4, -0.1)],
    'dad': [(960, 580, 1.0, 0.0, 0.0), (1180, 600, 0.92, -0.45, 0.1), (720, 590, 1.06, 0.45, -0.1)],
}


DOOR_FRAMES = ('med', 'wide', 'close', 'med', 'wide', 'med', 'close', 'wide')


def assign_door_framings(F):
    """Door shots without an explicit framing (no px / z0 / frame / hud zoom) and no one leaning into the lens rotate
    through wide / medium / close crops of the doorbell feed (the app's pinch zoom), so the fixed camera reads varied."""
    k = 0
    for sh in F.shots:
        p = sh.p
        if sh.kind != 'door' or 'frame' in p or 'px' in p or 'z0' in p or p.get('hud_follow') or not p.get('ppl'): continue
        if any(q.get('lean') or q.get('path') for q in p['ppl']): p['frame'] = 'wide'; continue
        p['frame'] = DOOR_FRAMES[k % len(DOOR_FRAMES)]; k += 1


def assign_bust_framings(F):
    last, ctr = {}, {}
    for sh in F.shots:
        if sh.kind != 'bust' or 'cx' in sh.p: continue
        who = sh.p.get('who', 'driver'); bg = sh.p.get('bg', 'porch')
        opts = BUST_FRAMES.get(who, BUST_FRAMES['driver'])
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
    p['ghost'] = (X, D) puts the dark figure standing behind you in the hall (bg 'hall_back'), out of focus."""
    p = sh.p
    bgn = p.get('bg', 'porch')
    sp, light = _bg(F, sh, bgn, p)
    who = p.get('who', 'driver')
    fr = p.get('_frame')
    cx = p.get('cx', fr[0] if fr else 960)
    cy = p.get('cy', fr[1] if fr else 560)
    sc = p.get('scale', fr[2] if fr else 1.0)
    view = None
    if fr and (fr[3] or fr[4]) and not p.get('no_view'):
        view = lambda a, s, v=(fr[3], fr[4]): a.set(s.t0 - 3, None, 0.1, turn=v[0], h_turn=v[1])
    lay, a = bust(F, sh, who, cx, cy, sc, _A(view, p.get('act')), expr=p.get('expr'), light=p.get('light', light))
    extra = []
    if p.get('ghost'):
        g = p['ghost']
        at = g if isinstance(g, str) else ('v', g[0], g[1])
        gt = p.get('ghost_tilt', 10)
        L, _ = people(F, sh, sp, [dict(who='dad', at=at, shadow=0.84, talk=False,
                                       act=_A(stare(-1), lambda a_, s_: a_.set(s_.t0 - 2, None, 0.1, h_tilt=gt), sway(3, 4.4, 2)))], None)
        extra += L
    if p.get('tablet'):                                       # the tablet held up beside the face (depth 0.8)
        tx, ty, ts_ = p['tablet']
        def tab(pen, t, tx=tx, ty=ty, ts_=ts_):            # fix 3: his gloved hand holds it from below (it floated before)
            yy = ty + 6 * math.sin(t * 1.7)
            CH.draw_tablet(pen, tx, yy, ts_, screen='sign', sig=p.get('sig', 'initial'), ink=1.0, t=t, ts=clock_hm(t))
            CH.draw_hand(pen, 'driver', tx + ts_ * 0.04, yy + ts_ * 0.62, ts_ * 0.5, 'grip', 180.0, 1)
            pen.fill(rrect(tx - ts_ * 0.13, yy + ts_ * 0.86, ts_ * 0.3, ts_ * 0.6, ts_ * 0.06), '#4a3424')       # the brown sleeve
            pen.line(rrect(tx - ts_ * 0.13, yy + ts_ * 0.86, ts_ * 0.3, ts_ * 0.6, ts_ * 0.06), 4, '#1d1f26')
        extra.append(Layer(0.8, tab, 'tablet', blur=0))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=cy - 20)))
    if fr and 'x' in cd and cd['x'] == 960: cd['x'] = 960 + (cx - 960) * 0.3
    if not p.get('ecu'): cd = _head_guard(cd, cy - 330 * sc, sh.d)
    cam = cam_from(F, sh, cd)
    if who == 'driver' or bgn in ('porch',):
        for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 4.0)
    grade = p.get('grade', 'memory' if p.get('era') == 'memory' else 'face_close')

    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(lay, *extra), cam, None, grade, 1.0, p.get('dof', 6.75), fx=fx, hud=p.get('hud'))


def B_hall(F, sh):
    """The front hall facing the door (stairs on the left, key bowl): you / mom staged with HA anchors; knocks from the
    box against the door jolt the camera at chest height; the box's shadow in the light gap under the door."""
    p = sh.p
    era = p.get('era', 'now')
    feet = p.get('feet')
    if feet is None and era == 'now' and T_BOX_DOOR - 1 <= sh.t0 < T_DAWN:
        feet = lambda t: [0.36, 0.5]
    kw = dict(lamp=p.get('lamp', 1.0 if era == 'memory' else 0.0), bowl=p.get('bowl', 'house'), feet=feet, chain=p.get('chain', 1.0),
              door_open=p.get('door_open', 0.0))
    if p.get('police'):
        sp = ST.hallway(police=p['police'], stairs=True, coats=False, **kw)
    else:
        sp = ST.delivery_hall(**kw)
    sp = sp.without(*p.get('without', ()))
    lt = memory_light if era == 'memory' else (p.get('light') or phone_light)
    ppl = p.get('ppl')
    if ppl is None:
        ppl = [dict(who='you', at=p.get('at', 'you'), act=p.get('act', _A(ex('nervous'), back_view())), surface='inside')]
    for q in ppl: q.setdefault('surface', 'inside')
    L, A = people(F, sh, sp, ppl, lt)
    if p.get('phone_glow') is not None and 'you' in sp.anchors:   # your phone lights up in the dark: a cold glow round you
        a_ = sp.anchors['you']; tg = p['phone_glow']

        def pglow(pen, t, a_=a_):
            k_ = clamp((t - tg) / 0.12) * (0.9 + 0.1 * math.sin(t * 9.0))
            if k_ <= 0: return
            pen.radial(None, a_.x + 30, a_.y - a_.height * 0.6, a_.height * 0.75, [(0, '#c8dcff', 120 * k_), (0.45, '#8aa8e8', 50 * k_),
                                                                                (1, '#8aa8e8', 0)], clip=False)
        L.append(Layer(a_.depth + 0.05, pglow, 'phone_glow', blur=0))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    if era == 'now':
        for h in F.knocks_in(sh.t0, sh.t1):
            if h >= T_BOX_DOOR - 0.5: cam.hit(h, 6.0)
    grade = p.get('grade', 'memory' if era == 'memory' else 'interior_dim')
    return Spec(sp.add(*L), cam, p.get('lens', 'lens'), grade, p.get('focus', 2.0), p.get('dof', 2.5),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_hallback(F, sh):
    """The hall from the front door into the house: the stairs, the side table, the dark far end with the kitchen clock.
    p['ghost'] = anchor of the dark figure standing at the end of the hall."""
    p = sh.p
    sp = ST.hall_back(lamp=p.get('lamp', 0.0), bowl=p.get('bowl', 'house'), kitchen_clock=p.get('clock', '3:11'),
                      upstairs=p.get('upstairs', 0.0), stairs_light=p.get('stairs_light', 0.0))
    ppl = list(p.get('ppl', []))
    for q in ppl: q.setdefault('surface', 'inside')
    if p.get('ghost'):
        ppl.append(dict(who='dad', at=p['ghost'], shadow=p.get('shadow', 0.93), talk=False, track=False,
                        act=_A(stare(-1), lambda a, s: a.set(s.t0 - 2, None, 0.1, h_tilt=p.get('ghost_tilt', 10)), sway(4, 4.0, 2))))
    L, A = people(F, sh, sp, ppl, p.get('light', phone_light))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=900, y=560)))
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'interior_dim'), p.get('focus', 1.2), p.get('dof', 2.0),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_upstairs(F, sh):
    p = sh.p
    sp = ST.upstairs_hall(lily_door=p.get('lily_door', 0.07), window_open=p.get('window_open', True), hall_light=p.get('hall_light', 0.0),
                          mom_door=p.get('mom_door', 0.0))
    ppl = list(p.get('ppl', []))
    for q in ppl: q.setdefault('surface', 'inside')
    L, A = people(F, sh, sp, ppl, moon_light)
    if p.get('pov_push') is not None:                # fix 3: your hand comes up into frame and pushes her door open
        tp = p['pov_push']

        def pov(pen, t):
            u_in = ease_out_cubic(clamp((t - (tp - 0.45)) / 0.45))
            u_push = ease_in_out(clamp((t - tp) / 0.6))
            u_out = ease_in_out(clamp((t - tp - 0.55) / 0.45))
            if u_in <= 0 or u_out >= 1: return
            x = lerp(1560, 1075, u_in) + 150 * u_push + 260 * u_out
            y = lerp(1300, 600, u_in) + 40 * u_push + 520 * u_out
            sz = 430 * (1.0 - 0.18 * u_push)
            cv = pen.cv; cv.saveLayer(skia.Rect(x - sz * 1.2, y - sz * 1.4, x + sz * 1.2, y + sz * 1.4), None)   # bounded: cheap at 2560
            CH.draw_hand(pen, 'you', x, y, sz, 'open', 172.0 - 14 * u_push, -1)
            cv.drawPaint(skia.Paint(Color=skia.Color4f(0.06, 0.07, 0.16, 0.62), BlendMode=skia.BlendMode.kSrcATop))   # the dark hall
            cv.drawPaint(skia.Paint(Color=skia.Color4f(1.0, 0.94, 0.76, 0.16 * u_push), BlendMode=skia.BlendMode.kSrcATop))   # her glow
            cv.restore()
        L.append(Layer(0.5, pov, 'pov_hand', blur=0, screen=True))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'nightlight'), p.get('focus', 4.6), p.get('dof', 2.0),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_lily(F, sh):
    p = sh.p
    view = p.get('view', 'room')
    hz = p.get('hz', hz_cfg(sh.t0, sh.t1) if sh.t0 < T_HZ_OFF + 1 else False)
    if view == 'window':
        sp = ST.lily_room('window', hazard=hz, drive=p.get('drive'), van=van_cfg(sh.t0, sh.t1))
    else:
        sp = ST.lily_room('room', window_open=p.get('window_open', False), bed=p.get('bed', 'sleeping'), hazard=hz if p.get('window_open') else None,
                          nightlight=p.get('nightlight', 1.0))
    ppl = list(p.get('ppl', []))
    L, A = people(F, sh, sp, ppl, moon_light)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=540)))
    return Spec(sp.add(*L), cam, sp.lens, p.get('grade', 'nightlight'), p.get('focus', sp.focus), p.get('dof', sp.dof),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_side(F, sh):
    p = sh.p
    sp = ST.side_yard(window_open=p.get('window_open', True), hazard=p.get('hz', hz_cfg(sh.t0, sh.t1)))
    ppl = list(p.get('ppl', []))
    L, A = people(F, sh, sp, ppl, lambda t: porch_light(t, sp.info.get('hazard'), base='#c9b8f0', k=0.7))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=540)))
    return Spec(sp.add(*L), cam, 'lens', p.get('grade', 'nightlight'), p.get('focus', 2.4), p.get('dof', 1.5),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


# ---- the 3:41 delivery photo (sets.photo_lily_scene: the same still the app shows, full screen)
def B_photo(F, sh):
    """The 3:41 delivery photo, full screen: one still (sets.photo_lily_scene, shared with the in-app thumbnail) seen through
    four crops: comp 'full' (from below: the wall, Lily's lit window, the driver from behind with his tablet raised to her
    sill, his face turned back over his shoulder into the flash), 'lily' (Lily leaning out of the open lower sash, her hand
    a short way out over the sill), 'arm' (his raised arm and the glowing tablet up at her sill) and 'finger' (her small
    finger on the signature box). The photo is a still: the life comes from the camera moving over it (like a phone being
    pinched), the flash falloff and the DELIVERY PHOTO / 3:41 AM stamp. The crop is baked into one cached layer, so the
    camera never zooms optically past ~1.3."""
    p = sh.p
    comp = p.get('comp', 'lily')
    sc = ST.photo_lily_scene()
    if p.get('path'):                     # fix 3: ONE continuous move over the photo (full -> Lily -> the tablet and his grin ->
        keys = p['path']                  # her finger): crop keys [(t, cx, cy, width, ease)] in photo design coords, drawn live
        # (vector, sharp at any zoom; ~0.15 s/frame at 2560) instead of four cuts over a baked crop

        def crop_at(t):
            if t <= keys[0][0]: k0 = keys[0]; return k0[1], k0[2], k0[3]
            for a, b in zip(keys, keys[1:]):
                if a[0] <= t <= b[0]:
                    u = ease_fn(b[4] if len(b) > 4 and b[4] else 'in_out')((t - a[0]) / max(1e-9, b[0] - a[0]))
                    return lerp(a[1], b[1], u), lerp(a[2], b[2], u), math.exp(lerp(math.log(a[3]), math.log(b[3]), u))
            k1 = keys[-1]; return k1[1], k1[2], k1[3]

        def draw(pen, t):
            cx_, cy_, cw_ = crop_at(t)
            k = DW / cw_
            cv = pen.cv
            cv.save(); cv.clipRect(skia.Rect(0, 0, DW, DH))
            cv.scale(k, k); cv.translate(-(cx_ - cw_ / 2), -(cy_ - cw_ * 9.0 / 32.0))
            sc['draw'](pen, 0.0)
            cv.restore()
        L = [Layer(1.0, draw, 'photo341', blur=0)]
    else:
        x0, y0, x1, y1 = sc['crops'][comp]
        k = DW / (x1 - x0)

        def draw(pen, t):
            cv = pen.cv
            cv.save(); cv.scale(k, k); cv.translate(-x0, -y0)
            sc['draw'](pen, 0.0)
            cv.restore()
        L = [Layer(1.0, draw, 'photo341', blur=0, cache='photo341_' + comp, bounds=(0, 0, DW, DH), cache_res=1.3)]

    def flash(pen, t):
        pen.radial(None, 960, 600, 1300, [(0, '#ffffff', 40), (0.5, '#ffffff', 10), (1, '#000000', 120)], clip=False)
    L.append(Layer(0.5, flash, 'flash', blur=0))
    dflt = {'full': dict(mv='move', x=960, y=700, z=1.22, x1=960, y1=470, z1=1.12),
            'lily': dict(mv='push', x=960, y=500, z=1.0, rate=0.035),
            'arm': dict(mv='move', x=900, y=760, z=1.18, x1=1000, y1=420, z1=1.22),
            'finger': dict(mv='push', x=980, y=560, z=1.0, rate=0.03)}[comp]
    if p.get('path'): dflt = dict(mv='hold', x=960, y=540, z=1.0, shake=1.2)
    cam = cam_from(F, sh, p.get('cam', dflt))
    t_in = sh.t0

    def hud(cv, t):
        pen = Pen(cv)
        pen.line(rect(26, 26, DW - 52, DH - 52), 3, '#ffffff', 90)
        text(cv, 'DELIVERY PHOTO', 60, 74, 800, 22, '#ffffff', 210, 0.18, 'left', 0.8)
        text(cv, 'NIGHTLINE  /  PROOF OF DELIVERY', 60, 102, 700, 15, '#c9cfdc', 170, 0.18, 'left', 0.6)
        text(cv, '3:41 AM', DW - 60, 90, 800, 40, '#ff9a3a', 235, 0.06, 'right', 0.9)          # top right: clear of faces / captions
        if p.get('hud'): p['hud'](cv, t)

    def fx(t):
        d = dict(p.get('post', {}))
        if p.get('pop'):                                                  # the photo arriving: a flash pop
            d['white'] = max(d.get('white', 0.0), 0.55 * math.exp(-max(0.0, t - t_in) / 0.12))
        return d
    return Spec(L, cam, None, p.get('grade', 'nightlight'), 1.0, 0.0, fx=fx, hud=hud)


def B_doorway(F, sh):
    """The front door open, from inside the hall: night (the box backlit at the threshold), memory (21 years ago: the
    van, dad going out to sign), dawn (mom opens the door; the box on the porch, its tape cut)."""
    p = sh.p
    tod = p.get('tod', 'night'); era = p.get('era', 'now')
    dop = p.get('door_open', 0.92)
    van = p.get('van', None if tod == 'dawn' else van_cfg(sh.t0, sh.t1))
    bx = p.get('box', 'door')
    sp = ST.porch_doorway(tod=tod, era=era, box=bx, van=van if van else (False if tod == 'dawn' else None), door_open=dop)
    lt = dawn_light if tod == 'dawn' else (memory_light if era == 'memory' else room_light)
    ppl = list(p.get('ppl', []))
    for q in ppl: q.setdefault('surface', 'inside')
    L, A = people(F, sh, sp, ppl, lt)
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540, rate=0.02)))
    # the doorway's frame-sized walls sit in the DOF blur: a fast optical zoom re-blurs them every frame (> 0.6 s/frame
    # at 2560), so the dolly stays slow and the global post push carries the move
    if cd.get('mv') == 'move': cd = dict(mv='push', x=cd.get('x1', cd['x']), y=cd.get('y1', cd['y']), z=cd.get('z', 1.0))
    cd['rate'] = min(cd.get('rate', 0.02), 0.02)
    cam = cam_from(F, sh, cd)
    return Spec(sp.add(*L), cam, None, p.get('grade', sp.grade), sp.focus, sp.dof,
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_box(F, sh):
    """The tall taped box close over the blurred porch: knocks from inside (F.boxa) bulge it at chest height and jolt it
    (camera hits on the same frames); tod 'dawn' (the tape cut), era 'memory' (21 years ago, the box that talked)."""
    p = sh.p
    tod = p.get('tod', 'night'); era = p.get('era', 'now')
    if tod == 'dawn':                                     # fix 3: on the porch (the peephole porch at dawn), not in the hall
        sp, _ = _porch(F, sh, dict(p, box=None, tod='dawn'), 'peephole'); sp = dimmed(sp, 0.35)
        lt = lambda t: dict(key='#ffe0b8', rim='#ffd2a8', k=1.0)
        st = lambda t: dict(F.boxa.at(t), cut=1.0)
    else:
        sp, _ = _porch(F, sh, dict(p, box=None), 'peephole')
        sp = dimmed(sp, 0.4)
        hz = sp.info.get('hazard')
        lt = lambda t: box_light(t, hz)
        st = None
        if p.get('breath'):                                   # the box 'talking' (21 years ago / the voice): soft swells
            st = lambda t: dict(F.boxa.at(t), bulge=max(F.boxa.at(t)['bulge'], 0.22 * (0.5 + 0.5 * math.sin(t * 7.0)) * p['breath']))
    bh = p.get('h', 1500.0)
    L = [box_layer(F, sh, p.get('bx', 960), p.get('by', 1500), bh, 1.0, p.get('view', 0.3), lt, st=st, to=p.get('to', ''),
                   sender=p.get('sender', 'RETURN'))]
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560, z=1.0, rate=0.035)))
    for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 9.0)
    grade = p.get('grade', 'dawn' if tod == 'dawn' else ('memory' if era == 'memory' else 'face_close'))
    return Spec(sp.add(*L), cam, None, grade, 1.0, 6.75, fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def _post_push(cam, sh, rate):
    if rate: cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + rate) ** max(0.3, sh.d), ease='push')
    return cam


def keyed(keys, t):
    """Interpolate [(t, v1, v2, ...[, ease])] at t (holds outside; per-segment ease, default in_out). Returns a tuple."""
    n = len(keys[0]) - 1
    if isinstance(keys[0][-1], str): n -= 1
    if t <= keys[0][0]: return tuple(keys[0][1:1 + n])
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            e = b[1 + n] if len(b) > 1 + n else 'in_out'
            u = ease_fn(e)((t - a[0]) / max(1e-9, b[0] - a[0]))
            return tuple(lerp(a[1 + j], b[1 + j], u) for j in range(n))
    return tuple(keys[-1][1:1 + n])


def hud_push(sh, rate=0.03, cx=960, cy=540, dx=0.0, dy=0.0, shake=0.0, hz=0.9):
    """Canvas transform for HUD-drawn shots (phone UI, waveform panels): the graphic pushes in at `rate`/s, drifts and
    shakes like a hand-held phone. cx / cy may be functions of t (a merged shot travels over the screen). Returns
    f(cv, t) -> restore()."""
    cx_, cy_ = cx, cy
    def apply(cv, t):
        u = clamp((t - sh.t0) / max(0.1, sh.d))
        k = (1.0 + rate) ** max(0.0, t - sh.t0 + 0.15)
        cx, cy = (cx_(t), cy_(t)) if callable(cx_) else (cx_, cy_)
        ox = dx * (0.2 + 0.8 * u) + shake * noise1(t * hz, sh.idx * 7 + 1)
        oy = dy * (0.2 + 0.8 * u) + shake * 0.8 * noise1(t * hz * 1.13, sh.idx * 7 + 2)
        cv.save(); cv.translate(cx + ox, cy + oy); cv.rotate(0.35 * shake * noise1(t * hz * 0.7, sh.idx * 7 + 3) if shake else 0.0)
        cv.scale(k, k); cv.translate(-cx, -cy)
        return cv.restore
    return apply


def B_ins(F, sh):
    """Prop insert: push at 4.5 %/s (dolly) plus a uniform post push, so the prop itself visibly grows."""
    p = sh.p
    sp = ST.insert(p['name'], t0=sh.t0, prop_kw=p.get('kw'), motion=p.get('motion'), hand=p.get('hand'), police=False, lens=p.get('lens'))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = 0.045
    cam = cam_from(F, sh, cd)
    if sp.lens is None: _post_push(cam, sh, p.get('ppush', 0.02))
    for h in p.get('knock_hits', []): cam.hit(h, 6.0)
    extra = []
    if p.get('ghost_hand'):                                    # the hand that sets the keys down (nobody there)
        g0 = p['ghost_hand']

        def gh(pen, t):
            u = clamp((t - g0) / 0.9)
            if u <= 0 or u >= 1: return
            a_ = math.sin(math.pi * u) * 0.8
            cv = pen.cv; cv.saveLayerAlpha(None, int(255 * a_))
            CH.draw_hand(pen, 'dad', 900, 200 + 120 * ease_out_cubic(min(1, u * 1.6)), 300, 'open', 180.0, 1)
            cv.drawPaint(skia.Paint(Color=skia.Color4f(0.03, 0.03, 0.05, 0.75), BlendMode=skia.BlendMode.kSrcATop))
            cv.restore()
        extra.append(Layer(0.95, gh, 'ghost_hand', blur=0))
    grade = p.get('grade', sp.grade or 'face_close')

    def fx(t):
        d = dict(sp.fx(t) or {}, **p.get('post', {}))
        if p.get('post_fn'): d.update(p['post_fn'](t))
        return d
    return Spec(sp.add(*extra) if extra else sp, cam, sp.lens, grade, sp.focus, sp.dof, fx=fx, hud=p.get('hud'))


def B_keys(F, sh):
    """Sunrise: mom's fingers lift the rusted keyring out of the box (the D-A-D bead keychain he was given in second
    grade), over the blurred dawn porch; the ring turns and jangles."""
    p = sh.p
    sp = dimmed(ST.delivery_porch('peephole', van=False, tod='dawn'), 0.35)
    t0 = sh.t0

    size = p.get('size', 560)
    robe = CH.CAST['mom']['cloth']

    def keys(pen, t):
        u = ease_out_cubic(clamp((t - t0 - p.get('lift', 0.0)) / 1.6))
        x, y = 960 + 4 * math.sin(t * 1.1), 600 - 150 * u
        sw = 6 * math.sin((t - t0) * 2.2) * (1 - 0.5 * u)
        CH.draw_keyring(pen, x, y, size, t=t, rust=1.0, angle=sw, jangle=0.6 * (1 - u) + 0.15)
        # mom's hand pinching the ring from above, her robe sleeve running up out of frame
        rt = y - 0.11 * size                                       # the top of the ring
        hs = 230.0
        wx, wy = x + 30, rt - 0.5 * hs
        sl = poly([(wx - 62, wy + 10), (wx + 58, wy + 18), (wx + 150, -400), (wx - 10, -400)])
        pen.shape(sl, robe['top'], 5); pen.fill(_crescent_x(sl, 26), robe['top_sh'], 160)
        pen.shape(poly([(wx - 66, wy - 8), (wx + 62, wy), (wx + 58, wy + 26), (wx - 62, wy + 18)]), robe['top_hi'], 4)
        CH.draw_hand(pen, 'mom', wx, wy + 14, hs, 'grip', 8.0, 1)
    L = [Layer(1.0, keys, 'keys', blur=0)]
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=520, z=1.0, rate=0.04)))
    return Spec(sp.add(*L), cam, None, 'dawn', 1.0, 6.75, fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def _crescent_x(path, dx):
    """The part of `path` not covered by itself shifted dx (a shade band on one side)."""
    m = skia.Matrix(); m.setTranslate(dx, 0)
    q = skia.Path(path); q.transform(m)
    return minus(path, q)


def B_hand(F, sh):
    """Mom's hand at the door chain, shaking (the chain rattles), and your hand closing on her wrist (p['catch'] = t)."""
    p = sh.p
    sp = ST.insert('lock_inside', t0=sh.t0, prop_kw=dict(turn=0.0, chain=1.0), hand=False, police=False,
                   motion=lambda tt: (1.5 * math.sin(tt * 31), 1.0 * math.sin(tt * 23), 0, 0) if p.get('rattle', True) else (0, 0, 0, 0))
    t0 = sh.t0; tc = p.get('catch')
    reach = p.get('reach', 1.0)

    def hands(pen, t):
        sh_ = p.get('shake', 1.0)
        jx = sh_ * (5 * math.sin(t * 47) + 3 * noise1(t * 9, 3)); jy = sh_ * (4 * math.sin(t * 39 + 1) + 2 * noise1(t * 8, 4))
        u = ease_out_cubic(clamp((t - t0 + 0.2) / 0.8)) * reach
        if p.get('letgo'): u *= 1 - ease_in_out(clamp((t - p['letgo']) / 0.7))
        hx, hy = 1500 - 420 * u + jx, 820 - 260 * u + jy
        CH.draw_hand(pen, 'mom', hx, hy, 360, 'grip' if u > 0.85 else 'open', 140.0, -1)
        if tc is not None:
            c = ease_out_cubic(clamp((t - tc) / 0.25))
            if c > 0: CH.draw_hand(pen, 'you', hx + 420 - 240 * c, hy + 300 - 140 * c, 380, 'grip', 120.0, 1)
    L = [Layer(0.93, hands, 'hands', blur=0)]
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=980, y=540, z=1.05, rate=0.05)))
    return Spec(sp.add(*L), cam, None, 'face_close', 1.0, 6.75, fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_phone(F, sh):
    """Your phone (the Nightline app, sets.app_phone) held up to the camera over the dark, blurred house; the phone
    pushes in, drifts and shakes in the hand. states = [(t, screen)]; p['full'] fills ~70 % H."""
    p = sh.p
    sp = ST.phone_bg(p.get('bg', 'hall'))
    dimmed(sp, 0.2)
    states = p.get('states', [(sh.t0, 'notify_delivered')])
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = 0.045
    cd.setdefault('shake', 2.5)
    cam = cam_from(F, sh, cd)
    sc0 = p.get('scale', 1.25) * (1.3 if p.get('full') else 1.0)
    px_, py_ = p.get('x', 960), p.get('y', 560)
    zk = p.get('zkeys')                   # merged shots: [(t, scale, zx, zy[, ease])] the phone comes up / the push travels
    if zk:
        hp = hud_push(sh, p.get('prate', 0.04), lambda t: keyed(zk, t)[1], lambda t: keyed(zk, t)[2], p.get('pdx', -30 if sh.idx % 2 else 30),
                      p.get('pdy', -12), shake=p.get('pshake', 5.0))
    else:
        hp = hud_push(sh, p.get('prate', 0.04), p.get('zx', px_), p.get('zy', py_), p.get('pdx', -30 if sh.idx % 2 else 30), p.get('pdy', -12),
                      shake=p.get('pshake', 5.0))
    snap = p.get('psnap')

    def hud(cv, t):
        st, ts = states[0][1], states[0][0]
        for (tt, s_) in states:
            if t >= tt: st, ts = s_, tt
        restore = hp(cv, t)
        sc = keyed(zk, t)[0] if zk else sc0
        if snap and t >= snap[0]:                 # fix 3: an eased 0.25 s push, not a 0.1 s pop (read as a jump cut)
            k = 1 + (snap[1] - 1) * ease_in_out(clamp((t - snap[0]) / 0.25))
            cv.save(); cv.translate(snap[2], snap[3]); cv.scale(k, k); cv.translate(-snap[2], -snap[3])
        sg = p.get('sig', 1.0)
        ST.app_phone(cv, st, t - ts, x=px_, y=py_, scale=sc, photo_k=clamp((t - ts) / 0.6) if st.startswith('photo') else 1.0,
                     sig_k=sg(t) if callable(sg) else sg)
        if snap and t >= snap[0]: cv.restore()
        restore()
        if p.get('hud'): p['hud'](cv, t)
    return Spec(sp, cam, None, 'phone_dark', 1.0, 9.0, fx=lambda t: dict(sp.fx(t) or {}, dim=0.25, **p.get('post', {})), hud=hud)


def B_black(F, sh):
    return Spec([], None, None, 'neutral', 1.0, 0.0, fx=lambda t: dict(sh.p.get('post', {})), hud=None)


WAVE_LAYOUTS = ('driver_l', 'door', 'driver_r', 'box', 'driver_low')


def B_wave(F, sh):
    """Doorbell-microphone waveform panel (the police waveform panels): the panel >= 60 % W pushes in over a sharp, lit
    background: 'driver_l' / 'driver_r' / 'driver_low' (his bust beside the panel), 'door' (live doorbell footage),
    'box' (the box close), or any _bg set name (blurred)."""
    p = sh.p
    k_ = sum(1 for s_ in F.shots if s_.kind == 'wave' and s_.t0 < sh.t0)
    lay_ = p.get('layout') or WAVE_LAYOUTS[k_ % len(WAVE_LAYOUTS)]
    lens, grade, focus, dof, dim = None, 'phone_dark', 1.0, 6.75, 0.12
    pw = p.get('w', 1180)
    px0, py0 = 960 - pw / 2, p.get('y', 380)
    side = 1
    if lay_ in ('driver_l', 'driver_r', 'driver_low'):
        sp, light = _bg(F, sh, 'porch', p)
        side = 1 if lay_ == 'driver_l' else -1
        cx, cy, sc = (500, 600, 0.95) if lay_ == 'driver_l' else ((1420, 600, 0.95) if lay_ == 'driver_r' else (960, 360, 0.72))
        act = p.get('act', _A(stare(-1), lambda a, s: a.set(s.t0 + 0.2, None, 0.8, h_turn=0.18 * side, h_tilt=-9 * side), creep(5 * side, 3, None)))
        lay, a = bust(F, sh, 'driver', cx, cy, sc, act, light=light, talk=p.get('talk', False))
        sp = sp.add(lay)
        if lay_ == 'driver_l': px0 = 1880 - pw
        elif lay_ == 'driver_r': px0 = 40
        else: py0 = 600
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960 + (cx - 960) * 0.25, y=540, rate=push_rate(sh.t0) * 1.6, dx=-60 * side, dy=-10)))
    elif lay_ == 'door':
        sp, bx = _porch(F, sh, p, 'doorbell')
        hz = sp.info.get('hazard')
        ppl = p.get('ppl', [dict(who='driver', at=DA(-0.2, 1.0), act=_A(stare(-1), creep(6, 4, None)), aim=(960, 470))])
        L, A = people(F, sh, sp, ppl, lambda t: porch_light(t, hz, k=0.8))
        if bx == 'boots':
            a_ = sp.anchors['box_boots']
            L.append(box_layer(F, sh, a_.x, a_.y, a_.height * 0.865, a_.depth, -0.35, lambda t: box_light(t, hz)))
        sp = sp.add(*L); lens, grade, focus, dof, dim = DOORBELL, 'doorbell_night', 1.0, 0.0, 0.2
        cam = Cam([(sh.t0, 960, 540, 1.0)], shake=0.0, seed=sh.idx).post_push(sh.t0, sh.t1, 1.0, 1.0 + push_rate(sh.t0) * 2.4 * sh.d, x=0, y=-120)
        for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 5.0)
        py0 = 640
    elif lay_ == 'box':
        sp, _ = _porch(F, sh, dict(p, box=None), 'peephole')
        sp = dimmed(sp, 0.4); hz = sp.info.get('hazard')
        sp = sp.add(box_layer(F, sh, 1300, 1450, 1350, 1.0, 0.3, lambda t: box_light(t, hz)))
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=1100, y=520, rate=push_rate(sh.t0) * 1.6, dx=50)))
        for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 8.0)
        px0 = 60; py0 = 160
    else:
        sp, _ = _bg(F, sh, lay_, p); dim = 0.3
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=540, rate=push_rate(sh.t0) * 1.6, dx=60)))
    rows = p.get('rows', [dict(label='FRONT DOOR MIC', color='blue', seed=1)])
    hgt = p.get('h', 150 + 95 * len(rows))
    if py0 + hgt > 880: py0 = 880 - hgt
    t_app = p.get('appear', sh.t0)
    play = p.get('play')
    hp = hud_push(sh, 0.022, px0 + pw / 2, py0 + hgt / 2, dx=-40 * side, dy=-8)

    def hud(cv, t):
        rr = []
        for r in rows:
            r = dict(r)
            if 'p' in r:
                a0, a1 = r.pop('p'); r['progress'] = clamp((t - a0) / max(1e-3, a1 - a0)); r['live'] = a0 <= t <= a1
            rr.append(r)
        ph = clamp((t - play[0]) / max(1e-3, play[1] - play[0])) if play else None
        restore = hp(cv, t)
        H.waveform_panel(cv, px0, py0, pw, hgt, p.get('title', 'FRONT DOOR  -  MIC'), rr, t, playhead=ph, appear=t - t_app)
        restore()
        if p.get('hud'): p['hud'](cv, t)
    return Spec(sp, cam, lens, p.get('grade', grade), focus, dof, fx=lambda t: dict(sp.fx(t) or {}, dim=dim, **p.get('post', {})), hud=hud)


def B_kitchen(F, sh):
    p = sh.p
    sp = ST.kitchen(police=False).without(*p.get('without', ()))
    L = []
    if p.get('ppl'):
        L, _ = people(F, sh, sp, p['ppl'], room_light)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=520)))
    return Spec(sp.add(*L), cam, None, 'interior_dim', p.get('focus', 1.2), p.get('dof', 3.0),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_living(F, sh):
    p = sh.p
    sp = ST.living_room_window(car=False, police=False, lamp=p.get('lamp', 0.0))
    L = []
    if p.get('you', False):
        L, _ = people(F, sh, sp, [dict(who='you', at='you_window', act=p.get('act', lambda a, s: a.set(s.t0 - 1, None, 0.1, turn=2.0, h_turn=0.0)),
                                       light=room_light)], None)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=1000, y=560)))
    return Spec(sp.add(*L), cam, None, 'interior_dim', p.get('focus', 1.8), p.get('dof', 2.0),
                fx=lambda t: dict(sp.fx(t) or {}, **p.get('post', {})), hud=p.get('hud'))


def B_latch(F, sh):
    """A window's sash lock, close: your hand snaps the latch over (locked), the night outside the glass with the van's
    amber flashes on the frame. win 'kitchen' | 'bath' (frosted glass) | 'mom' (lace)."""
    p = sh.p
    kind = p.get('win', 'bath')
    t_lock = p.get('t_lock', sh.t0 + 0.35)

    def outside(pen, t):
        pen.linear(rect(-500, -400, 2920, 1880), 0, -400, 0, 1480, ['#04060e', '#0c1430', '#080a12'])
        h = hz_default(t)
        if h > 0.02: pen.radial(None, 1700, 760, 1100, [(0, AMBER, 120 * h), (1, AMBER, 0)], clip=False)
        pen.fill(oval(520, 260, 22), '#e8ecff', 140)
        if kind == 'bath':
            pen.fill(rect(-500, -400, 2920, 1880), '#9aa8c0', 60)
            for k in range(60):
                pen.fill(oval(-200 + (k * 137) % 2400, -100 + (k * 241) % 1300, 40 + (k % 5) * 12), '#ffffff', 10)

    def frame(pen, t):
        wood = '#d9d4c8' if kind != 'mom' else '#c8b8a4'
        pen.fill(minus(rect(-500, -400, 2920, 1880), rect(200, 60, 1520, 900)), '#2a2830')
        pen.texture(minus(rect(-500, -400, 2920, 1880), rect(200, 60, 1520, 900)), 'plaster', 0.3, 'overlay', 1.0)
        pen.shape(minus(rect(170, 30, 1580, 960), rect(210, 70, 1500, 880)), wood, 6)
        pen.shape(rect(170, 470, 1580, 70), wood, 5)                                     # the meeting rail
        if kind == 'mom':                                              # her lace curtains drawn back to the jambs
            for s_ in (-1, 1):
                x0 = 210 if s_ < 0 else 1710
                sw = 10 * math.sin(t * 1.1 + s_)
                cur = smooth([(x0, 70), (x0 - s_ * 400 + sw, 70), (x0 - s_ * 300 + sw, 330), (x0 - s_ * 250, 520),
                              (x0 - s_ * 330 + sw * 0.6, 760), (x0 - s_ * 400 + sw, 950), (x0, 950)], True, 0.7)
                pen.fill(cur, '#f4eee4', 62)
                pen.cv.save(); pen.cv.clipPath(cur, skia.ClipOp.kIntersect, True)
                for j in range(70):                                    # rosettes
                    rx, ry = x0 - s_ * (30 + (j * 53) % 380), 100 + (j * 97) % 840
                    pen.line(oval(rx, ry, 13), 2, '#ffffff', 70); pen.fill(oval(rx, ry, 4), '#ffffff', 60)
                for k in range(6):                                     # folds
                    fx_ = x0 - s_ * (40 + k * 60)
                    pen.line(smooth([(fx_, 70), (fx_ + s_ * 18, 520), (fx_ - s_ * 10, 950)], False), 3, '#000000', 40)
                pen.cv.restore()
                pen.line(cur, 2.5, '#ffffff', 90)
        h = hz_default(t)
        if h > 0.02: pen.radial(None, 1700, 500, 900, [(0, AMBER, 60 * h), (1, AMBER, 0)], clip=False)

    def latch(pen, t):
        u = ease_out_cubic(clamp((t - t_lock) / 0.18))
        cx, cy = 960, 505
        pen.shape(rrect(cx - 120, cy - 24, 240, 48, 12), '#b89a52', 5)
        pen.fill(rrect(cx - 110, cy - 20, 220, 14, 7), '#f0d890', 160)
        ang = -70 + 70 * u
        cv = pen.cv; cv.save(); cv.translate(cx - 40, cy); cv.rotate(ang)
        pen.shape(rrect(-14, -14, 170, 28, 14), '#c9a64a', 5); pen.fill(oval(0, 0, 18), '#7a5a22')
        cv.restore()
        hx = cx + 120 - 30 * u; hy = cy + 110 - 20 * u
        CH.draw_hand(pen, 'you', hx, hy, 300, 'grip' if u < 1 else 'relaxed', 200.0, -1)
    L = [Layer(3.0, outside, 'outside'), Layer(1.05, frame, 'frame', blur=0), Layer(0.95, latch, 'latch', blur=0)]
    cam = cam_from(F, sh, p.get('cam', dict(mv='fast', x=980, y=540, z=1.1, dx=-40)))
    cam.hit(t_lock + 0.12, 4.0)
    return Spec(L, cam, None, 'interior_dim', 1.0, 6.75, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def _icon(n):
    """Small white line icons for the rule cards: f(pen, x, y, size, alpha)."""
    def f(pen, x, y, sz, a):
        k = sz / 120.0; w = 7 * k
        if n == 1:                                                          # a door with a stylus crossed out
            pen.line(rrect(x - 30 * k, y - 52 * k, 60 * k, 104 * k, 4 * k), w, '#ffffff', a)
            pen.fill(oval(x + 16 * k, y + 4 * k, 5 * k), '#ffffff', a)
            pen.seg((x - 50 * k, y + 40 * k), (x - 8 * k, y - 2 * k), w * 0.8, '#ffffff', a)
            pen.seg((x - 52 * k, y + 52 * k), (x + 52 * k, y - 52 * k), w, RED_ICON, a)
        elif n == 2:                                                        # speech bubble with a crossed-out name
            pen.line(rrect(x - 52 * k, y - 40 * k, 104 * k, 64 * k, 14 * k), w, '#ffffff', a)
            pen.line(poly([(x - 20 * k, y + 24 * k), (x - 30 * k, y + 46 * k), (x, y + 24 * k)], False), w, '#ffffff', a)
            pen.seg((x - 30 * k, y - 8 * k), (x + 30 * k, y - 8 * k), w * 0.7, '#ffffff', a)
            pen.seg((x - 36 * k, y + 6 * k), (x + 36 * k, y - 22 * k), w, RED_ICON, a)
        elif n == 3:                                                        # a photo with a turn-around arrow crossed
            pen.line(rrect(x - 50 * k, y - 40 * k, 100 * k, 80 * k, 6 * k), w, '#ffffff', a)
            pen.line(smooth([(x - 26 * k, y + 12 * k), (x - 20 * k, y - 16 * k), (x + 10 * k, y - 20 * k), (x + 24 * k, y - 4 * k)], False), w * 0.8, '#ffffff', a)
            pen.line(poly([(x + 14 * k, y - 8 * k), (x + 25 * k, y - 2 * k), (x + 30 * k, y - 14 * k)], False), w * 0.8, '#ffffff', a)
            pen.seg((x - 52 * k, y + 52 * k), (x + 52 * k, y - 52 * k), w, RED_ICON, a)
        elif n == 4:                                                        # a signature line with a second hand
            pen.seg((x - 52 * k, y + 30 * k), (x + 52 * k, y + 30 * k), w * 0.7, '#ffffff', a)
            pen.line(smooth([(x - 44 * k, y + 18 * k), (x - 30 * k, y - 20 * k), (x - 18 * k, y + 14 * k), (x - 2 * k, y - 26 * k),
                             (x + 10 * k, y + 12 * k), (x + 34 * k, y - 6 * k)], False), w * 0.8, '#ffffff', a)
            pen.seg((x - 30 * k, y - 46 * k), (x + 30 * k, y + 50 * k), w, RED_ICON, a)
            pen.seg((x + 30 * k, y - 46 * k), (x - 30 * k, y + 50 * k), w, RED_ICON, a)
        elif n == 5:                                                        # the box with knock marks
            pen.line(rrect(x - 26 * k, y - 50 * k, 52 * k, 100 * k, 4 * k), w, '#ffffff', a)
            for j in (-1, 1):
                pen.line(smooth([(x + j * 40 * k, y - 22 * k), (x + j * 52 * k, y), (x + j * 40 * k, y + 22 * k)], False), w * 0.7, '#ffffff', a)
            pen.seg((x - 56 * k, y + 52 * k), (x + 56 * k, y - 52 * k), w, RED_ICON, a)
        elif n == 6:                                                        # the box under a rising sun
            pen.line(rrect(x - 22 * k, y - 20 * k, 44 * k, 74 * k, 4 * k), w, '#ffffff', a)
            pen.line(smooth([(x - 46 * k, y - 30 * k), (x - 32 * k, y - 58 * k), (x, y - 66 * k), (x + 32 * k, y - 58 * k), (x + 46 * k, y - 30 * k)], False),
                     w * 0.8, '#ffd23a', a)
            pen.seg((x - 58 * k, y - 30 * k), (x + 58 * k, y - 30 * k), w * 0.7, '#ffffff', a)
        else:                                                               # a window
            pen.line(rrect(x - 44 * k, y - 50 * k, 88 * k, 100 * k, 4 * k), w, '#ffffff', a)
            pen.seg((x, y - 50 * k), (x, y + 50 * k), w * 0.7, '#ffffff', a)
            pen.seg((x - 44 * k, y), (x + 44 * k, y), w * 0.7, '#ffffff', a)
            pen.fill(oval(x + 26 * k, y + 26 * k, 8 * k), RED_ICON, a)
    return f


RED_ICON = '#e3262e'


def B_rule(F, sh):
    """Rule card over a dimmed, blurred LIVE scene (the police style): the camera pushes, the driver sways at the door
    behind the blur ('door' / 'porch'), the flashers blink; the card carries a small icon."""
    p = sh.p
    n = p['n']; text_ = RULES[n]
    bgk = p.get('bg', 'porch')
    L = []
    if bgk == 'door':
        sp, bx = _porch(F, sh, p, 'doorbell'); hz = sp.info.get('hazard')
        kw = dict(lens=DOORBELL, grade='doorbell_night', focus=1.0, dof=0.0)
        if p.get('driver', True):
            L, _ = people(F, sh, sp, [dict(who='driver', at=DA(-0.2, 1.0), act=_A(stare(-1), sway(10, 2.6, 5), creep(8, 4, None)), talk=False)],
                          lambda t: porch_light(t, hz, k=0.8))
        if bx == 'boots':
            a_ = sp.anchors['box_boots']
            L.append(box_layer(F, sh, a_.x, a_.y, a_.height * 0.865, a_.depth, -0.35, lambda t: box_light(t, hz)))
    elif bgk == 'street':
        sp = ST.delivery_street(van=van_cfg(sh.t0, sh.t1), hazard=hz_cfg(sh.t0, sh.t1)); kw = dict(lens=None, grade='night_blue', focus=1.1, dof=0.0)
    else:
        sp, _ = _bg(F, sh, bgk, p); kw = dict(lens=None, grade='night_blue', focus=1.0, dof=0.0)
        if bgk == 'porch':
            hz = sp.info.get('hazard')
            L, _ = people(F, sh, sp, [dict(who='driver', at='driver', act=_A(stare(-1), sway(12, 2.4, 6), creep(10, 4, None)), talk=False)],
                          lambda t: porch_light(t, hz, base='#ffcf9a', key=0.1, k=0.7))
    cam = mkcam(sh, 'push', 960, 540, 1.03, rate=push_rate(sh.t0))
    for h in F.knocks_in(sh.t0, sh.t1): cam.hit(h, 4.0)
    t0 = sh.t0
    icon = _icon(n)

    def hud(cv, t):
        H.rule_card(cv, n, text_, t - t0, icon=icon)
    return Spec(sp.add(*L), cam, kw['lens'], kw['grade'], kw['focus'], kw['dof'],
                fx=lambda t: dict(sp.fx(t) or {}, blur=6, dim=0.35), hud=hud)


BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}

SPACE = {'street': 'street', 'door': 'doorbell_mic', 'peep': 'outside', 'hall': 'inside', 'hallback': 'inside', 'upstairs': 'inside',
         'lily': 'inside', 'side': 'outside', 'photo': 'close', 'doorway': 'outside', 'box': 'outside', 'ins': 'close', 'keys': 'close',
         'hand': 'close', 'phone': 'close', 'wave': 'doorbell_mic', 'kitchen': 'inside', 'living': 'inside', 'latch': 'close',
         'rule': None, 'black': None}


def bust_space(sh):
    return {'porch': 'outside', 'hall': 'inside', 'hall_back': 'inside', 'upstairs': 'inside', 'lily': 'inside', 'memory': 'inside',
            'memory_porch': 'outside', 'dawn': 'outside', 'side': 'outside'}.get(sh.p.get('bg', 'porch'), 'outside')


# ==================================================================================================== per-shot cues + fx
def shot_common(F, sh, spec):
    """Collect the shot's SFX / music events from its acting, camera, tags and explicit cue lists."""
    p = sh.p
    space = bust_space(sh) if sh.kind == 'bust' else SPACE.get(sh.kind)
    for a in sh.actors:
        for e in a.events:
            if sh.t0 - 0.05 <= e['t'] <= sh.t1 + 0.4 and e['name']:
                pr = dict(e.get('params') or {})
                g = e.get('gain_db', 0.0)
                if e['name'].startswith('footsteps') and sh.kind in ('street',): g -= 5
                if e['name'].startswith('footsteps') and p.get('steps_fade'):     # walking away from the mic
                    g -= p['steps_fade'] * clamp((e['t'] - sh.t0) / max(0.3, sh.d))
                sp_e = space if space not in ('radio',) else 'outside'
                if e['name'] == 'doorbell_chime':                   # the chime rings inside the house; the button click on the mic
                    sh.sfx.append(_ev(e['t'], 'doorbell_chime', g, 0.0, 'inside', kind='ding_dong'))
                    if sh.kind == 'door': sh.sfx.append(_ev(e['t'] - 0.05, 'ui_pop', -8, 0.0, 'doorbell_mic'))   # the button (-14: buried)
                    if p.get('era', 'now') != 'memory':             # and the doorbell app chimes on your phone
                        sh.sfx.append(_ev(e['t'] + 0.3, 'doorbell_cam_chime', g - 3, 0.0, 'close'))
                    continue
                if p.get('era') == 'memory': pr['memory'] = True
                sh.sfx.append(_ev(e['t'], e['name'], g, e.get('pan', 0.0), sp_e, **pr))
    mv = (p.get('cam') or {}).get('mv')
    if (p.get('cam') or {}).get('snap'):
        sh.sfx.append(_ev(p['cam']['snap'][0], 'whoosh', -3, 0, None, kind='hard'))
    elif mv == 'pull':
        sh.sfx.append(_ev(sh.t0 + 0.02, 'whoosh', -4, 0, None, kind='hard'))
    for tg in p.get('tags', []):
        if p.get('tag_sound', True):                  # fix 3: none in the hushed beats (after "Mar?", dad's keys ...)
            sh.sfx.append(_ev(tg[0], 'ui_pop', -3, 0, 'close'))
    if p.get('cut') in ('static', 'glitch'):
        sh.sfx.append(_ev(sh.t0, 'glitch', -4, 0, None, dur=0.25, amount=0.8))
    if p.get('cut') == 'white' and not p.get('quiet_cut'):
        sh.sfx.append(_ev(sh.t0, 'impact_hit', 0, 0, None, size=1.1))
    if p.get('hit'):
        for h in (p['hit'] if isinstance(p['hit'], (list, tuple)) else [p['hit']]):
            if sh.kind == 'door': continue
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
        sh.sfx.append(_ev(sh.t0 + tm['type0'], 'typing', -6, 0, 'close', dur=round(tm['type1'] - tm['type0'], 2), cps=14))
        sh.music.append({'t': round(sh.t0, 3), 'type': 'rule', 'level': 0.75})
        sh.music.append({'t': round(sh.t0, 3), 'type': 'riser', 'level': 0.55, 'len': 4.0})
    if sh.kind == 'phone':
        for k, (tt, st) in enumerate(p.get('states', [])):
            if not (sh.t0 - 0.05 <= tt < sh.t1 + 0.4): continue
            if st.startswith('notify'):
                sh.sfx.append(_ev(tt, 'phone_vibrate', -4, 0, 'close', n=2))
                sh.sfx.append(_ev(tt + 0.05, 'text_notification', -6, 0, 'close'))
            else:
                sh.sfx.append(_ev(tt - 0.08, 'touch_tap', -3, 0, 'close'))        # final mix: -8 / -8 were 20 LU under
                sh.sfx.append(_ev(tt, 'ui_pop', -5, 0, 'close'))
    if sh.kind == 'hand':                                       # her shaking hand rattles the door chain
        sh.sfx.append(_ev(sh.t0 + 0.15, 'chain_lock', -3, 0.15, 'close', kind='rattle', dur=round(min(1.6, sh.d), 2)))
    if sh.kind == 'latch':
        sh.sfx.append(_ev(p.get('t_lock', sh.t0 + 0.35), 'window_latch', -2, 0.1, 'close'))
    if sh.kind == 'photo' and p.get('pop'):                     # the photo arriving full screen (the other crops cut silently)
        sh.sfx.append(_ev(sh.t0, 'camera_shutter', -4, 0, 'close'))             # final mix: -10 was 23 LU under
    # van / flashers: relay ticks while the van is in view with its hazards on
    if False and sh.kind in ('door', 'street', 'peep', 'lily', 'side') and p.get('era', 'now') == 'now' and p.get('tod', 'night') == 'night':
        if sh.kind != 'lily' or p.get('view') == 'window':          # (fix 3: one continuous hazard_ticks bed in beds())
            g = {'door': -16, 'street': -12, 'peep': -18, 'lily': -18, 'side': -20}[sh.kind]
            for tt, kd in ST.hazard_ticks(sh.t0, sh.t1, t_off=T_HZ_OFF):
                sh.sfx.append(_ev(tt, 'hazard_tick', g, 0.5, space, kind=kd))
    # tags in the HUD
    tags = p.get('tags')
    if tags:
        prev = spec.hud
        cam_, lens_ = spec.cam, spec.lens

        def hud(cv, t, prev=prev, tags=tags):
            if prev: prev(cv, t)
            for tg in tags:
                t0, txt, x, y, style = tg[:5]
                hold_ = tg[5] if len(tg) > 5 else (1.2 if style == 'alert' else 2.6)
                if not (t0 <= t <= t0 + hold_): continue
                an = tg[6] if len(tg) > 6 else None
                if an:
                    ax, ay = an['at'](t) if callable(an['at']) else an['at']
                    try:
                        X, Y = project(ax, ay, an.get('d', 1.0), cam_.at(t) if cam_ is not None else None, lens_, an.get('ref', an.get('d', 1.0)))
                        X, Y = float(X), float(Y)
                    except Exception:
                        X, Y = ax, ay
                    tx, ty = clamp(X + x, 160, DW - 160), clamp(Y + y, 130, 860)
                    k = clamp((t - t0) / 0.15)
                    pen = Pen(cv)
                    pen.seg((X, Y), (X + (tx - X) * k, Y + (ty - Y) * k), 3.0, '#ffffff', 220)
                    pen.fill(oval(X, Y, 7), '#ffffff', 235); pen.line(oval(X, Y, 13), 2.5, '#ffffff', 160 * k)
                    H.tag(cv, txt, tx, ty, style, t - t0)
                else:
                    H.tag(cv, txt, x, y, style, t - t0)
        spec.hud = hud


def box_cues(F):
    """One box_knock per F.boxa hit: heard through the front door (outside) while the box stands on the porch; on the
    door itself (inside, at chest height) once it stands against it; the doorbell mic layer when the door camera is up."""
    out = []
    t_two = F.w(283, 'two') - 0.15                              # the sting's "Two knocks." (the box is at the door again)
    for e in F.boxa.events:
        t = e['t']; pr = dict(e.get('params') or {})
        sh = F.shot_at(t)
        on_door = t >= T_BOX_DOOR - 0.5
        pr['on'] = 'door' if on_door else 'porch'
        if t > T_DAWN:
            pr['small'] = True                                  # small knuckles (the sting)
        if T_STING < t < t_two:
            # "Somewhere down the street, you can already hear it. Small knuckles on cardboard.": far off and soft, so
            # the knock that follows at the door reads as two, a pause, one (fix 3: +6 dB, they were 10-15 LU under)
            pr['on'] = 'porch'
            out.append(_ev(t, e['name'], e.get('gain_db', 0.0) + 3.0, -0.35, 'street', **pr))
            continue
        if F.t(256) - 0.2 <= t < F.t(258):                         # what Lily heard: through her bedroom vent
            pr['on'] = 'vent'
            out.append(_ev(t, e['name'], e.get('gain_db', 0.0) - 4.0, 0.35, 'upstairs', **pr))
            continue
        out.append(_ev(t, e['name'], e.get('gain_db', 0.0), -0.25, 'inside' if on_door else 'outside', **pr))
        if sh.kind in ('door', 'box', 'wave', 'peep'):
            out.append(_ev(t, e['name'], e.get('gain_db', 0.0) - (2 if sh.kind == 'box' else 6), 0.1, 'doorbell_mic' if sh.kind == 'door' else 'close', **pr))
    return out


EXPO = {'hall': -0.45, 'hallback': -0.4, 'kitchen': -0.45, 'living': -0.4, 'upstairs': -0.2, 'door': -0.2, 'bust_hall': -0.2,
        'bust_hall_back': -0.2, 'bust_porch': -0.1, 'ins': -0.15, 'box': -0.1}


def glob_fx(F, sh, t, fx):
    """Per-frame global effects: scare-cut flashes, the climax creeping into red, the end fade."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.1: fx['white'] = 0.85 * (1 - u / 0.1)
    ek = EXPO.get(sh.kind if sh.kind != 'bust' else 'bust_' + sh.p.get('bg', 'porch'), 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    if sh.kind not in ('rule', 'black') and sh.p.get('era', 'now') != 'memory' and sh.p.get('tod', 'night') != 'dawn' and not (T_DAWN <= sh.t0 < T_STING):
        # the last 35 %: darker, redder, more saturated, then a second ramp over the last minute into the climax; UI /
        # insert shots take half of it (police global look)
        k = clamp((t - 418.0) / 175.0)
        k2 = clamp((t - 590.0) / 50.0) if t < T_DAWN else clamp((t - 612.0) / 28.0)
        # fix 3: rule 7 (the knocking stops, the search, Lily's photo) is the climax: from 508 s a second, faster ramp
        # deeper into red and dark, and the van's hazards wash the house in blinking red until they stop (T_HZ_OFF)
        k7 = clamp((t - 508.0) / 10.0) if t < T_DAWN else 0.0
        if k > 0:
            ui = 0.5 if sh.kind in ('phone', 'wave', 'ins', 'hand', 'latch') else 1.0      # the 3:41 photo takes the full ramp
            ext = sh.kind in ('door', 'street', 'peep', 'side', 'box') or sh.p.get('bg') in ('porch',)
            fx['red'] = fx.get('red', 0.0) + ((0.42 + (0.18 if ext else 0.0)) * k + 0.28 * k2 + 0.16 * k7) * ui
            fx['sat'] = fx.get('sat', 1.0) * (1 + (0.6 * k + 0.25 * k2 + 0.2 * k7) * ui)
            fx['exposure'] = fx.get('exposure', 0.0) - (0.42 * k + 0.3 * k2 + 0.8 * k7) * ui
        if k7 > 0 and 'flash' not in fx:
            hz = ST.hazard(t, t_off=T_HZ_OFF)
            if hz > 0.01:
                ui = 0.45 if sh.kind in ('phone', 'wave', 'ins', 'hand', 'latch', 'photo') else 1.0
                fx['flash'] = _epost.Spill(0.55 * k7 * hz * ui, side=-1.0 if sh.idx % 2 else 1.0)
    if t > F.duration - 2.6: fx['fade'] = clamp((t - (F.duration - 2.6)) / 1.6)
    if t < 0.35: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.35)


# ==================================================================================================== beds + music curve
LOC = {'street': 'ext', 'door': 'ext', 'peep': 'ext', 'box': 'ext', 'side': 'ext', 'photo': 'ext', 'bust': 'int', 'hall': 'int',
       'hallback': 'int', 'upstairs': 'int', 'lily': 'int', 'doorway': 'int', 'kitchen': 'int', 'living': 'int', 'latch': 'int',
       'ins': 'int', 'keys': 'ext', 'hand': 'int', 'phone': 'int', 'wave': 'ext', 'rule': None, 'black': None}


def beds(F):
    """Ambience beds: the night outside under the whole house story (through the walls inside), room tone, the van's
    diesel idle while it sits at the curb, a clock in the hall during the long wait, dawn birds, the second night."""
    out = []
    D = F.duration
    out.append(_ev(0.0, 'ambience_night', -2, 0, 'outside', dur=round(T_DAWN, 1), dog=0.3, wind=0.5, buzz=0.4, crickets=0.6))
    out.append(_ev(0.0, 'room_tone', -4, 0, 'inside', dur=round(D, 1)))
    # fix 3: the diesel was inaudible (measured -34.6 LU on the van shots): a continuous idle at the indoor level, plus a
    # second idle layer on every exterior shot while the van is at the curb (-26 LU outside / -32 inside), and the
    # pull-away 4 dB up, so its leaving is the engine you heard all night going away
    out.append(_ev(0.0, 'car_idle', -5, 0.4, 'street', dur=round(T_VAN_GO[0] + 0.5, 1), kind='diesel'))
    for sh in F.shots:
        if (sh.kind in ('street', 'door', 'peep', 'side', 'box') and sh.p.get('era', 'now') == 'now' and sh.p.get('tod', 'night') == 'night'
                and sh.t0 < T_VAN_GO[0] and not (sh.kind == 'street' and sh.p.get('drive'))):
            t1_ = min(sh.t1, T_VAN_GO[0] + 0.3)
            out.append(_ev(sh.t0, 'van_idle', -1, 0.4, 'street', dur=round(t1_ - sh.t0 + 0.15, 2)))   # (own name: not merged with the bed)
    out.append(_ev(T_VAN_GO[0], 'van_pull_away', 6, 0.5, 'window', dur=round(T_VAN_GO[1] - T_VAN_GO[0] + 1.5, 1)))
    # the van's hazard relay: one continuous bed, phase-locked to the picture's blink, until they stop on "stop"
    out.append(_ev(0.0, 'hazard_ticks', -4, 0.45, 'outside', dur=round(T_HZ_OFF + 0.2, 2), t_off=T_HZ_OFF))
    # the dawn (fix 3: it sat under the night bed): heard through the door, then the open porch from the door creak on
    t_open = F.t(264) + 0.25
    out.append(_ev(T_DAWN, 'ambience_dawn', 9, 0, 'outside', dur=round(t_open - T_DAWN + 0.6, 1), birds=0.7))
    out.append(_ev(t_open, 'ambience_dawn', 6, 0, 'porch', dur=round(T_STING - t_open, 1), birds=0.9))
    out.append(_ev(T_STING, 'ambience_night', -4, 0, 'outside', dur=round(D - T_STING, 1), dog=0.2, wind=0.6, buzz=0.3, crickets=0.6))
    out.append(_ev(488.0, 'clock_tick', -6, 0.3, 'inside', dur=10.0, bpm=60))
    # Lily's room: the window stands wide open from "The window is wide open." to the sunrise cut; you stay in the room
    # (final mix: the night air and the curtains, so the open window is heard, not only seen)
    tw = F.t(242) - 0.1
    out.append(_ev(tw, 'ambience_suburb', -2, 0.3, 'window', dur=round(T_DAWN - tw, 1), dog=0.1, wind=0.7, traffic=0.2))
    out.append(_ev(tw + 0.3, 'curtain_flutter', -7, 0.25, 'close', dur=round(T_DAWN - tw - 0.3, 1), wind=0.7))
    return out


INTENSITY = [  # (seconds, level): the story's tension, read off the beats
    (0.0, 0.5), (6.8, 0.45), (13.1, 0.55), (17.5, 0.62), (19.1, 0.35), (23.4, 0.5), (26.0, 0.35), (30.7, 0.42), (35.6, 0.5),
    (40.4, 0.45), (47.1, 0.55), (51.1, 0.5), (57.5, 0.48), (66.2, 0.58), (70.0, 0.62), (78.0, 0.55), (84.3, 0.7), (89.5, 0.6),
    (92.9, 0.66), (98.6, 0.6), (104.2, 0.62), (111.1, 0.5), (118.2, 0.55), (126.9, 0.66), (129.2, 0.7), (137.0, 0.72), (141.8, 0.66),
    (151.9, 0.72), (155.8, 0.55), (161.0, 0.58), (168.8, 0.5), (178.5, 0.55), (184.8, 0.65), (186.9, 0.72), (196.5, 0.66),
    (202.2, 0.7), (206.4, 0.6), (210.4, 0.55), (215.7, 0.62), (218.1, 0.75), (224.7, 0.7), (231.4, 0.8), (243.8, 0.9),
    (248.2, 0.8), (257.8, 0.7), (265.1, 0.6), (267.9, 0.55), (273.3, 0.6), (279.6, 0.45), (292.5, 0.55), (296.0, 0.65),
    (305.7, 0.5), (314.1, 0.58), (324.8, 0.62), (329.0, 0.66), (331.4, 0.72), (338.2, 0.55), (340.9, 0.7), (346.0, 0.76),
    (353.2, 0.8), (357.5, 0.74), (365.6, 0.66), (370.8, 0.82), (378.0, 0.92), (382.3, 0.86), (387.4, 0.78), (395.6, 0.95),
    (402.4, 0.86), (407.7, 0.8), (417.6, 0.84), (421.4, 0.9), (428.1, 0.8), (431.0, 0.96), (435.8, 0.6), (440.9, 0.68), (446.4, 0.9),
    (450.9, 0.84), (455.5, 0.72), (460.9, 0.66), (465.7, 0.72), (470.6, 0.6), (477.5, 0.55), (485.2, 0.7), (490.8, 0.6),
    (497.8, 0.75), (503.7, 0.7), (508.3, 0.85), (510.8, 0.75), (517.2, 0.78), (521.0, 0.88), (530.3, 0.8), (534.4, 0.62),
    (541.0, 0.78), (542.6, 0.9), (549.2, 0.86), (551.4, 0.94), (555.5, 0.86), (563.4, 0.9), (568.2, 0.88), (571.6, 1.0),
    (572.1, 0.72), (578.1, 0.78), (585.2, 0.62), (588.5, 0.7), (592.7, 0.8), (598.2, 0.35), (604.3, 0.45), (606.9, 0.6),
    (608.5, 0.66), (613.2, 0.42), (618.9, 0.6), (623.1, 0.7), (630.4, 0.9), (633.5, 0.82), (636.7, 0.92), (638.5, 0.97),
    (640.6, 1.0), (641.4, 0.5)]


def intensity_curve(F):
    pts = []
    for t, v in INTENSITY:
        if 160.0 <= t <= 300.0:              # the second quarter is the calm one (AUDIO_SPEC 3)
            v = min(0.5, 0.3 + (v - 0.4) * 0.5) if v > 0.4 else max(0.28, v - 0.1)
        elif t < 160.0:
            v = min(1.0, v + 0.04)
        pts.append([round(t, 2), round(v, 3)])
    pts.append([round(F.duration, 2), 0.0])
    return pts


# ---------------------------------------------------------------------------------------------------- cue polish
HIT_SFX = ('impact_hit', 'stinger', 'braam', 'sub_drop')
HIT_MUS = ('hit', 'stinger', 'braam', 'sub_drop')
# drop-outs under the ominous lines before the scares
EXTRA_SIL = [(83.3, 1.0), (136.4, 1.5), (216.9, 1.2), (242.6, 1.2), (394.6, 1.0), (441.0, 2.2), (498.6, 1.8),
             (570.4, 1.2), (605.4, 1.2), (638.9, 0.8)]
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
        if e['name'] in HIT_SFX and not (e.get('params') or {}).get('kind') == 'eye_flash': e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] in HIT_MUS: e['t'] = round(retime(e['t']), 3)
    for e in mus:
        if e['type'] != 'braam': continue
        ln = line_at(e['t'] + 0.02)
        if ln and ln[0] < e['t'] - 0.02:
            nxt = [c for c in cuts if ln[1] - 0.05 <= c <= ln[1] + 1.0]
            e['t'] = round(min(nxt) if nxt else ln[1] + 0.05, 3)

    ht = [e['t'] for e in mus if e['type'] in HIT_MUS] + [e['t'] for e in sfx if e['name'] in HIT_SFX]
    wh = [e for e in sfx if e['name'] == 'whoosh']
    pri = lambda e: (0 if any(abs(e['t'] - sn) < 0.06 for sn in snaps) else 1 if any(abs(e['t'] - h) < 0.4 for h in ht) else 2)
    keep = []
    for e in sorted(wh, key=lambda e: (pri(e), e['t'])):
        if all(abs(e['t'] - k['t']) >= WHOOSH_GAP for k in keep): keep.append(e)
    kid = set(map(id, keep))
    sfx = [e for e in sfx if e['name'] != 'whoosh' or id(e) in kid]

    for t, ln in EXTRA_SIL:
        if not any(e['type'] == 'silence' and abs(e['t'] - t) < 3 for e in mus):
            mus.append({'t': t, 'type': 'silence', 'level': 0.0, 'len': ln})
    hts = sorted(e['t'] for e in mus if e['type'] in HIT_MUS + ('rule',))
    for e in mus:
        if e['type'] != 'silence': continue
        ln = max(1.7, float(e.get('len', 1.7)))
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
    rules = sorted(e['t'] for e in mus if e['type'] == 'rule')
    cand = sorted(set([round(h - 0.9, 2) for h in hts if h > 16] + [round(r - 0.4, 2) for k, r in enumerate(rules) if k % 2 == 0]))
    want = int(F.duration / 60 * 2.5)
    for pk in cand:
        if len(peaks) >= want: break
        if any(abs(pk - q) < 14 for q in peaks): continue
        if any(a - 0.5 <= pk <= b + 0.5 for a, b in sil): continue
        mus.append({'t': round(pk - 13.0, 3), 'type': 'swell', 'level': 0.6, 'len': 13.0}); peaks.append(pk)
    iv = intensity_curve(F)
    for t, v in sorted(iv, key=lambda p: -p[1]):
        if len(peaks) >= want: break
        if t < 16 or t > F.duration - 4: continue
        if any(abs(t - q) < 20 for q in peaks) or any(a - 0.5 <= t <= b + 0.5 for a, b in sil): continue
        mus.append({'t': round(t - 13.0, 3), 'type': 'swell', 'level': 0.5, 'len': 13.0}); peaks.append(t)

    out = []
    kk = lambda e: (e['name'], str(e.get('space')) if e['name'] in ('box_knock', 'knock_door') else '')
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
# ---------------------------------------------------------------------------------------------------- acting shorthands
def _A(*fns):
    return lambda a, s: [f(a, s) for f in fns if f]


def stare(d=-1.0): return lambda a, s: a.stare(s.t0 + d)
def ex(name, d=-1.0, t1=None): return lambda a, s: a.expr(name, s.t0 + d, t1)
def smile(d=0.2, dur=3.0, amt=1.0): return lambda a, s: a.creep_smile(s.t0 + d, dur, amount=amt)
def grin(d=-1.0): return lambda a, s: (a.stare(s.t0 - 1), a.wide_grin(s.t0 + d))
def tilt(d=0.3, ang=26.0, dur=1.6): return lambda a, s: a.head_tilt(s.t0 + d, ang, dur)
def lean(d=0.1, dur=2.4, amt=1.0): return lambda a, s: a.lean_in(s.t0 + d, dur, amount=amt)
def snap(t, frm=0.9, to=0.0): return lambda a, s: a.snap_turn(t, frm, to)
def nod(d=0.3): return lambda a, s: a.set(s.t0 + d, s.t0 + d + 0.5, 0.25, h_nod=0.22)
def look_side(t, h=0.85, fade=0.45): return lambda a, s: a.set(t, None, fade, h_turn=h, lock=0.0, look_x=0.6 if h > 0 else -0.6)
def down(d=-1.0, amt=1.0): return lambda a, s: a.head_down(s.t0 + d, None, amt)
def back_view(): return lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=2.0)
def twitch(*ds): return lambda a, s: a.twitch([s.t0 + d for d in ds])
def stage(n, d=-2.0): return lambda a, s: a.smile_stage(s.t0 + d, n)          # driver: hold a smile stage
def carry(t1=None): return lambda a, s: a.carry_tablet(t1=t1)
def tab_up(d=0.0, dur=None, screen='sign'): return lambda a, s: a.hold_tablet_up(s.t0 + d, s.t1 + 1 if dur is None else s.t0 + d + dur, 1, screen)
def phone_look(d=-2.0): return lambda a, s: a.look_at_phone(s.t0 + d)
def eyes_shut(d=0.0): return lambda a, s: a.set(s.t0 + d, None, 0.2, eye_open=0.0, squint=1.0, brow_sad=1.0, brow_up=0.8, m_press=0.75, shrug=0.35,
                                                 sweat=1.0, tremble=0.9, smile=-0.5, pale=0.5)
def terror(d=-1.0): return lambda a, s: a.set(s.t0 + d, None, 0.2, wide=0.75, brow_up=0.7, brow_sad=0.6, pupil=0.7, m_open=0.1)


def sway(amp=7.0, per=3.3, tilt=3.0, ph=0.0):
    """Weight shift: hips rock, the head counter-tilts (unsettling slow rocking)."""
    def f(a, s):
        def fn(P, t):
            u = math.sin(2 * math.pi * (t - s.t0) / per + ph)
            P.sway += amp * u; P.tilt += 0.9 * u; P.h_tilt -= tilt * u
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
    return f


def creep(tilt=9.0, amp=6.0, tw=0.55, loosen=0.5, per=3.6):
    """The creepy layer (police film): a slow head-tilt drift over the shot, weight-shift sway, one twitch at fraction
    `tw` (None = no twitch), the body's stillness loosened (the face keeps its locked stare). Add it LAST."""
    def f(a, s):
        d = max(0.6, s.t1 - s.t0); a._creep = True

        def fn(P, t):
            P.h_tilt += tilt * ease_in_out(clamp((t - s.t0 + 0.3) / (d + 0.3)))
            u = math.sin(2 * math.pi * (t - s.t0) / per + a.seed)
            P.sway += amp * u; P.tilt += 0.7 * u
            P.still = min(P.still, loosen)
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
        if tw is not None: a.twitch([s.t0 + tw * d], 1.0)
    return f


def hand_mouth(d=0.3, dur=None, side=-1):
    def f(a, s):
        sh_ = a.sp['body']['sh']; t0 = s.t0 + d; t1 = None if dur is None else t0 + dur

        def fn(P, t):
            w = ease_in_out(clamp((t - t0) / 0.35)) * (1.0 if t1 is None else 1.0 - ease_in_out(clamp((t - t1) / 0.4)))
            if w > 0: a._arm(P, side, w, -(sh_ - 17) + sh_ * 0.32, -42.0, 190.0, 'relaxed', up=1.0)
        a._add(t0 - 0.1, None if t1 is None else t1 + 0.5, fn)
    return f


def pt(d=0.3, dur=1.6, side=-1, dx=1.0, dy=0.0):
    return lambda a, s: a.point(s.t0 + d, s.t0 + d + dur, side, dx, dy)


def turn_to(d, to, dur=0.6): return lambda a, s: a.turn(s.t0 + d, to, dur)
def turned(to=2.0): return lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=to)
def jerk_at(d, amp=1.0): return lambda a, s: a.jerk(s.t0 + d, amp)
def frz(d0, d1): return lambda a, s: a.freeze(s.t0 + d0, s.t0 + d1)


_PDB = {}


def DA(X, D, Y=None):
    """Doorbell-view anchor (x, y, depth, height) at lateral X m and depth D (porch floor Y=0 in front of the steps,
    the yard Y=-0.72 beyond them). Depth 0.45-0.62 = leaning into the lens (fisheye bulge)."""
    if 'v' not in _PDB: _PDB['v'] = ST.View(405, 380, 1.45, ground=-0.72)
    if Y is None: Y = 0.0 if D < 1.9 else -0.72
    a = _PDB['v'].anchor(X, D, Y)
    return (a.x, a.y, a.depth, a.height)


def PA(X, D, Y=None):
    """Peephole-view anchor (same world, eye height 1.6 m)."""
    if 'p' not in _PDB: _PDB['p'] = ST.View(600, 560, 1.6, ground=-0.72)
    if Y is None: Y = 0.0 if D < 1.9 else -0.72
    a = _PDB['p'].anchor(X, D, Y)
    return (a.x, a.y, a.depth, a.height)


def HA(X, D, Y=0.0):
    """Front-hall anchor (x, y, depth, height): X lateral m, D depth (the door is at ~2.6)."""
    if 'h' not in _PDB: _PDB['h'] = ST.View(620, 430, 1.5)
    a = _PDB['h'].anchor(X, D, Y); return (a.x, a.y, a.depth, a.height)


def P(who, at='driver', act=None, **k):
    return dict(who=who, at=at, act=act, **k)


def door_swing(t_open, dur=1.4, k0=0.0, k1=0.92):
    return lambda t: k0 + (k1 - k0) * ease_in_out(clamp((t - t_open) / dur))


# ---------------------------------------------------------------------------------------------------- the plan
def plan(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    DP = lambda x, y, d: (960 + d * (x - 960), 540 + d * (y - 540))      # camera point that centres (x, y) of a depth-d layer
    DR, Y, M, LI, DAD = 'driver', 'you', 'mom', 'lily', 'dad'
    G = F.globals
    B = F.boxa

    # ============================================================ the box's knocks on the film clock (BoxActing)
    kn0 = w(5, 'knocking')
    F.box_events += B.knock(kn0 + 0.05, (2, 1), 0.26, 0.62, 0.9)                         # cold open
    F.box_events += B.knock(w(164, 'knocks') + 0.12)                                       # "Then the box knocks."
    F.box_events += B.knock(w(167, 'two') - 0.02, (2,), 0.3)                               # "Two knocks."
    F.box_events += B.knock(w(169, 'one') - 0.02, (1,))                                    # "One more."
    F.box_events += B.knock(w(172, 'two') - 0.02, (2, 1), 0.3, 0.8)                        # "Two, then one."
    F.box_events += B.knock(e(185) + 0.05, (2, 1), 0.28, 0.6, 0.8)                         # "It knows the knock."
    F.box_events += B.knock(t(194) + 0.2, (2, 1), 0.2, 0.36)                               # "The knocking gets faster."
    for k in range(3):                                                                     # "Two, then one." x3
        F.box_events += B.knock(w(195, 'two', k) - 0.02, (2, 1), 0.16, 0.33, 1.05)
    t2_ = w(218, 'two') - 0.02                                                                    # all night, on the door
    F.box_events += B.knock_loop(t(217) + 0.3, t2_ - 1.2 - 1.0, period=2.6, accel=0.0, strength=0.9)
    F.box_events += B.knock(t2_, (2, 1), 0.3, 0.7)
    F.box_events += B.knock_loop(t2_ + 1.0 + 1.3, e(220) - 1.2, period=2.6, accel=0.0, strength=0.9)
    F.box_events += B.knock(w(221, 'three') - 0.3, (2, 1), 0.3, 0.75, 0.75)                 # the last one before 3:40
    F.box_events += B.knock(w(257, 'two') - 0.02, (2, 1), 0.36, 0.85, 0.7)                  # what Lily heard
    F.box_events += B.knock(w(282, 'knuckles') + 0.35, (1, 1), 0.22, 0.32, 0.45)            # small knuckles
    F.box_events += B.knock(w(283, 'two') - 0.02, (2,), 0.3, strength=0.75)
    F.box_events += B.knock(w(285, 'one') + 0.0, (1,), strength=0.9)

    # ============================================================ COLD OPEN (0 - 26.0)
    C(0.0, 'street', cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.035), music=[(0.3, 'motif', 0.45, 6)])
    rg = w(0, 'rings')
    C(rg - 0.35, 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stage(3), stare(-1), lambda a, s: a.ring_bell(rg - 0.05), lambda a, s: a.hold_tablet_up(w(0, 'signature') - 0.3, s.t1 + 1),
                                                            creep(4, 4, None)))],
      py=-60, z1=1.15)
    C(w(0, 'not') - 0.2, 'peep', ppl=[P(DR, act=_A(stage(4), stare(), tilt(0.4, 14, 1.4)))], cam=dict(mv='push', x=960, y=470, z=1.05))
    C(T(1), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stage(3), stare(-1), tab_up(-0.3), creep(5, 3, None)))], py=-50, z1=1.12)
    C(T(2), 'ins', name='label', cam=dict(mv='push', x=980, y=560, z=1.05, rate=0.05))
    C(T(3), 'ins', name='tablet_sign', lens='doorbell', cam=dict(mv='push', x=960, y=560, z=1.1, rate=0.05))
    C(T(4), 'bust', who=Y, bg='hall', act=_A(ex('fear'), lambda a, s: a.set(s.t0, None, 0.2, m_press=1.0)), cam=dict(mv='hand', x=960, y=560, z=1.0),
      tags=[(w(4, 'name') - 0.1, 'SAY NOTHING', 960, 150, 'alert')])
    C(T(5), 'box', cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04), music=[(kn0 - 0.5, 'silence', 0.0, 0.5)])
    C(w(5, 'remember') - 0.1, 'hall', ppl=[], cam=dict(mv='push', x=960, y=540, z=1.08, rate=0.05), lamp=0.0)
    C(T(6), 'door', ppl=[P(DR, at=DA(0.0, 0.85), act=_A(stage(5), grin(-1), lean(-0.2, 1.0, 1.0), tilt(0.2, 16, 0.8)), lean=True)], py=-110,
      cut='static', music=[(t(6), 'stinger', 0.8)])
    C(T(7), 'doorway', era='memory', tod='night', ppl=[P(DAD, at='threshold', act=_A(back_view()), talk=False)],
      cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.03), music=[(t(7), 'motif', 0.5, 5)])
    C(T(8), 'street', era='memory', novan=True, cam=dict(mv='pull', x=960, y=560, z=1.0))
    C(T(9), 'door', ppl=[P(DR, at=DA(-0.25, 1.0), act=_A(stage(3), stare(-1), carry(), creep(6, 4, None)))], px=180, py=40, z1=1.3,
      music=[(w(9, 'back') + 0.1, 'braam', 0.85)])

    # ============================================================ 3:07 (26.0 - 111.1)
    C(T(10), 'hall', ppl=[P(Y, at='you', act=_A(ex('nervous'), back_view(), phone_look(w(10, 'lights') - T(10) - 0.2)))], lamp=0.0,
      phone_glow=w(10, 'phone') - 0.25,
      cam=dict(mv='push', x=900, y=540, z=1.0, rate=0.04), music=[(t(10), 'silence', 0.0, 1.0)])
    C(w(10, 'lights') - 0.05, 'phone', states=[(w(10, 'lights'), 'notify_delivered')], full=True)
    C(T(12), 'bust', who=Y, bg='hall', act=_A(ex('suspicious'), phone_look()), light=phone_light, cam=dict(mv='push', x=960, y=560))
    C(T(13), 'hall', act=_A(ex('nervous'), back_view(), phone_look(-3)), cam=dict(mv='push', x=900, y=540, z=1.0, rate=0.03))
    # fix 3: ring -> the feed comes live -> "a driver is standing under your porch light": one doorbell shot, one glitch
    C(w(13, 'doorbell') - 0.3, 'door', ppl=[P(DR, at=DA(-0.2, 0.97), act=_A(stare(-1), carry(), lambda a, s: a.ring_bell(w(13, 'doorbell') - 0.1),
                                                                     creep(4, 4, None)))],
      cut='glitch', posts=[(w(13, 'doorbell') - 0.3, T(14), 1.0, 1.05, 0, -20), (T(14), T(16), 1.0, 1.14, 0, -60)],
      tags=[(t(14) + 0.3, 'FRONT DOOR  -  LIVE', 960, 170, 'red', 1.6)])
    C(T(16), 'bust', who=DR, cx=960, cy=420, scale=0.9, act=_A(stare(-1), carry()), cam=dict(mv='move', x=960, y=760, z=1.2, y1=330, z1=1.4),
      tags=[(t(16) + 0.3, 'NIGHTLINE', -260, 120, 'white', 1.6, dict(at=(960 - 0.9 * 120, 360 + 0.9 * 420)))])
    C(T(18), 'door', ppl=[P(DR, path=(T(19) + 0.2, T(19) + 1.4, [DA(-0.2, 1.0), DA(-0.05, 0.8)]), act=_A(stare(-1), carry(), lean(1.5, 1.6, 0.6), creep(3, 3, None)),
                           lean=True)], py=-90, z1=1.2)
    C(w(19, 'exactly') - 0.1, 'bust', who=DR, ecu=True, cx=960, cy=560, scale=1.5, act=_A(stare(-1)), cam=dict(mv='creep', x=960, y=420, z=1.3))
    C(T(20), 'door', ppl=[P(DR, at=DA(-0.2, 1.0), act=_A(stare(-1), carry(), creep(3, 3, None)))], px=200, py=60, z1=1.35)
    C(T(21), 'box', cam=dict(mv='move', x=960, y=1050, z=1.15, y1=380, z1=1.15))
    C(T(22), 'door', ppl=[P(DR, at=DA(-0.2, 1.0), act=_A(stare(-1), carry(), creep(3, 3, None)))], z0=1.12, z1=1.0, py=0)
    C(T(23), 'street', cam=dict(mv='move', x=1300, y=640, z=1.3, x1=1440, y1=640, z1=1.7))
    C(w(24, 'faded') - 0.2, 'street', cam=dict(mv='push', x=1450, y=700, z=2.4, rate=0.03),
      tags=[(w(24, 'nightline'), 'NIGHTLINE DELIVERY', 960, 200, 'white', 2.0)])
    C(T(26), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), creep(3, 3, None)))], frame='close',
      music=[(t(26), 'motif', 0.55, 4)])
    C(T(27), 'bust', who=DR, act=_A(stare(-1), creep(6, 3, None)), cam=dict(mv='creep', x=960, y=520, z=1.05))
    C(T(28), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), tilt(0.3, 10, 1.2), creep(3, 3, None)))], py=-80, z1=1.15)
    C(T(31), 'phone', states=[(t(31) + 0.2, 'order')], scale=1.2)
    C(T(32, 0.9), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), phone_look()), light=phone_light, cam=dict(mv='push', x=960, y=560))
    C(T(33), 'phone', states=[(t(31) + 0.2, 'order')], full=True, x=960, y=530, prate=0.06,
      zkeys=[(T(33), 1.625, 960, 420), (t(35), 1.625, 960, 470), (t(36) + 0.6, 1.625, 960, 640), (T(37), 1.625, 960, 650, 'lin')])
    C(T(37), 'ins', name='label', cam=dict(mv='keys', keys=[(T(37), 900, 480, 1.3), (t(37) + 0.35, 900, 478, 1.58, 'out'), (T(38), 905, 476, 1.66, 'lin')]),
      hit=t(37) + 0.05,
      music=[(t(37) + 0.05, 'stinger', 0.85)])
    C(T(38), 'door', talk_btn=True, ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), lambda a, s: a.listen_tilt(t(38) + 1.0, e(38), 1, 14)))],
      py=-60, z1=1.12,     # "You press the button": the talk button (final mix: it had no sound)
      sfx=[(w(38, 'press') + 0.1, 'touch_tap', -6, 0, 'close'), (w(38, 'press') + 0.16, 'ui_pop', -9, 0, 'close')])
    C(T(39), 'peep', ppl=[P(DR, act=_A(stare(), carry()))], cam=dict(mv='push', x=960, y=480, z=1.05))
    C(T(42), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stare(-1), carry(), lean(0.5, 1.8, 0.5), creep(6, 4, None)), lean=True)], py=-90)
    C(T(43), 'bust', who=DR, cx=760, cy=590, scale=0.95, act=_A(stare(-1), creep(5, 3, None)), tablet=(1360, 700, 520), cam=dict(mv='push', x=1000, y=560, z=1.0))
    C(T(44), 'ins', name='label', cam=dict(mv='move', x=760, y=780, z=1.8, x1=820, y1=770, z1=2.0),
      tags=[(t(44) + 0.1, 'EXCHANGE', 960, 200, 'red', 1.2)])
    C(T(46), 'doorway', tod='night', cam=dict(mv='push', x=980, y=600, z=1.0, rate=0.04))
    C(T(47), 'street', cam=dict(mv='pull', x=960, y=560, z=1.0), music=[(t(47) + 0.1, 'braam', 0.8)],
      tags=[(w(47, 'seven'), '7  RULES', 960, 200, 'white', 2.4)])
    C(T(48), 'upstairs', lily_door=0.07, cam=dict(mv='creep', x=960, y=560, z=1.0), music=[(t(48), 'motif', 0.5, 4)])

    # ============================================================ RULE 1 (111.1 - 168.8): don't open the door
    C(T(49), 'rule', n=1, bg='door')
    C(T(51, 0.7), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), pt(0.3, 1.6, -1, 0.0), creep(5, 4, None)))], py=-70)
    C(T(52), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stare(-1), tab_up(0.3), creep(3, 3, None)))], px=-40, py=-40, z1=1.35)
    C(T(53), 'peep', ppl=[P(DR, act=_A(stare(), tab_up(-1.0)))], cam=dict(mv='push', x=960, y=480, z=1.05))
    # fix 3: one insert over 12.9 s: the empty-looking line -> it isn't empty (push) -> the first letter -> where the stroke stops
    tsi = w(55, "isn't")
    C(T(54), 'ins', name='tablet_sign', kw=lambda tt, t_=tsi - 0.35 - T(54): dict(sig='initial', ink=clamp((tt - t_) / 0.5)),   # tt: shot time
      cam=dict(mv='keys', keys=[(T(54), 960, 540, 1.0), (tsi - 0.1, 950, 548, 1.08, 'push'), (tsi + 0.45, 930, 560, 1.32, 'in_out'),
                                (t(56) + 0.4, 900, 590, 1.45, 'lin'), (w(56, 'handwriting'), 880, 600, 1.62, 'in_out'),
                                (t(57) + 0.5, 990, 630, 1.95, 'in_out'), (T(58), 1010, 640, 2.15, 'lin')]),
      hit=tsi, music=[(tsi, 'stinger', 0.8)], tags=[(w(57, 'halfway'), 'STOPS HALFWAY', 960, 200, 'red', 1.8)])
    C(T(58), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stare(-1), tab_up(-0.5), lean(0.4, 1.4, 0.5), creep(6, 3, None)), lean=True)], py=-90)
    C(T(61), 'bust', who=Y, bg='hall', act=_A(ex('suspicious'), phone_look()), cam=dict(mv='push', x=960, y=560))
    C(T(62), 'bust', who=DR, ecu=True, cx=960, cy=420, scale=1.45, act=_A(stare(-1), lambda a, s: a.talk([(t(62) + 0.5, t(62) + 2.1, "it's easier when you finish it")])),
      cam=dict(mv='creep', x=960, y=640, z=1.25))
    C(T(63), 'wave', layout='driver_l', title='FRONT DOOR  -  MIC  /  CAMERA',
      rows=[dict(label='VOICE', color='blue', seed=7, p=(t(63), t(63) + 1.5)), dict(label='LIPS', color='red', seed=7, p=(t(63) + 0.5, t(63) + 2.1),
                                                                                     marker=(0.05, 0.3, 'LATE'))],
      play=(t(63), e(64)), act=_A(stare(-1), lambda a, s: a.talk([(t(63) + 0.1, t(63) + 1.6, 'it is easier when you finish it')])))
    C(T(64), 'bust', who=DR, ecu=True, cx=960, cy=400, scale=1.5, act=_A(stare(-1), lambda a, s: a.talk([(t(64) - 0.2, t(64) + 1.2, 'just finish it')])),
      cam=dict(mv='creep', x=960, y=700, z=1.3))
    ts9 = _hms(3, 9, 0)
    F.ts_flicker = [(w(66, '309') - 0.02, ts9 + 41), (w(66, 'three', 0) - 0.02, ts9 + 42), (w(66, 'three', 1) - 0.02, ts9 - 17)]
    C(T(65), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), creep(3, 3, None)))], hud_follow=True,
      posts=[(T(65), w(66, '309') - 0.1, 1.0, 2.6, 610, -332, 'in_out'), (w(66, '309') - 0.1, T(67), 1.0, 1.12, 0, 0, 'lin')],
      flicker=F.ts_flicker, post_fn=lambda t_: dict(glitch=0.7) if any(0 <= t_ - tf < 0.12 for tf, _ in F.ts_flicker) else {},
      music=[(w(66, 'three', 1), 'stinger', 0.7)], sfx=[(tf, 'glitch', -4, 0.4, 'close', dict(dur=0.15, amount=0.6)) for tf, _ in F.ts_flicker])
    C(T(67), 'ins', name='lock_inside', kw=dict(turn=0.0, chain=1.0), hand=False, cam=dict(mv='push', x=960, y=540, z=1.05, rate=0.04))
    C(T(68), 'bust', who=DR, cx=760, cy=590, scale=0.95, act=_A(stare(-1), tilt(0.4, 10, 1.2), creep(5, 3, None)), tablet=(1360, 690, 560),
      cam=dict(mv='push', x=1040, y=560, z=1.0),
      tags=[(w(68, 'key'), 'A KEY', 960, 200, 'red', 1.4), (t(69), "DON'T SIGN", 960, 150, 'alert')])
    C(T(70), 'door', ppl=[P(DR, at=DA(-0.12, 0.93), act=_A(stare(-1), lambda a, s: a.hold_tablet_up(s.t0 - 2, t(70) + 0.7), carry(),
                                                             lambda a, s: a.look_at_box(t(71) + 0.2, w(71, 'back') - 0.1),
                                                             lambda a, s: a.snap_turn(w(71, 'back'), None, 0.0, hold=0.1)))],
      posts=[(T(70), T(71), 1.0, 1.06, 0, -30), (T(71), T(72), 1.0, 1.18, 60, -70)])
    C(T(72), 'peep', ppl=[P(DR, act=_A(stare(), carry(), tilt(0.5, -12, 1.0)))], cam=dict(mv='push', x=960, y=480, z=1.05))
    C(w(74, 'right') - 0.15, 'bust', who=DR, scale=1.1, act=_A(stare(-1), tilt(0.2, 18, 1.2), creep(0, 3, None)), cam=dict(mv='push', x=960, y=520, rate=0.05))

    # ============================================================ RULE 2 (168.8 - 210.4): don't say anyone's name
    C(T(75), 'rule', n=2, bg='porch')
    C(e(76) + 1.0, 'ins', name='label', cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.045))
    C(T(79), 'door', ppl=[P(DR, path=(T(80) - 0.4, T(80) + 0.4, [DA(-0.1, 0.9), DA(-0.05, 0.95)]),
                           act=_A(stare(-1), carry(T(80) + 0.2), pt(0.4, 1.6, -1, 0.0), lean(0.3, 2.0, 0.5), creep(6, 4, None),
                                  lambda a, s: a.tilt_box(t(80) + 0.3, e(82) + 1.0, 1)), lean=True)],
      posts=[(T(79), T(80), 1.0, 1.08, 0, -60), (T(80), T(81), 1.0, 1.2, 140, 80)])
    B.tilt(t(80) + 0.5, e(82) + 1.2, angle=-6.0, turn=0.7)
    C(T(81), 'ins', name='label_to', cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.04))
    C(T(82), 'door', ppl=[P(DR, at=DA(-0.05, 0.95), act=_A(stare(-1), lambda a, s: a.tilt_box(s.t0 - 2, e(82) + 1.0, 1),
                                                              lambda a, s: a.tap_label(t(82) + 0.35, 2)))], px=260, py=60, z0=1.3, z1=1.6)
    C(T(83), 'bust', who=DR, act=_A(stare(-1), tilt(0.3, 14, 1.0), creep(6, 3, None)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04))
    C(T(85), 'peep', ppl=[P(DR, act=_A(stare(), carry(), tilt(0.4, -10, 1.0)))], cam=dict(mv='push', x=960, y=470, z=1.05))
    C(w(85, 'anyone') - 0.15, 'upstairs', lily_door=0.07, cam=dict(mv='push', x=960, y=560, z=1.15, rate=0.05), music=[(w(85, 'upstairs'), 'hit', 0.55)])
    C(T(86), 'bust', who=Y, bg='hall', act=_A(ex('angry'), lambda a, s: a.set(s.t0 + 0.5, None, 0.3, m_open=0.3)), cam=dict(mv='push', x=960, y=560))
    C(T(87), 'bust', who=Y, bg='hall', act=_A(ex('fear'), lambda a, s: a.hands_over_mouth(s.t0 + 0.4, None, sob=False)), cam=dict(mv='hand', x=960, y=560), music=[(t(88), 'silence', 0.0, 1.0)])
    C(T(89), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), frz(0.0, 1.4)))], py=-100, z1=1.12)
    C(T(91), 'bust', who=DR, act=_A(stare(-1), frz(0.6, 4.0)), cam=dict(mv='creep', x=960, y=520, z=1.0))
    C(w(91, 'not') - 0.1, 'peep', ppl=[P(DR, at='driver_close', act=_A(stare(), frz(0.0, 3.0)))], approach=False, cam=dict(mv='push', x=960, y=440, z=1.0, rate=0.03))
    C(T(92), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stare(-1), carry(), lean(0.2, 2.6, 0.75), tilt(2.4, 16, 1.0), creep(6, 3, None)), lean=True)], py=-130, z1=1.25)
    C(T(96), 'phone', states=[(w(96, 'buzzes'), 'notify_photo')], full=True, pshake=9.0)

    # ============================================================ RULE 3 (210.4 - 275.9): don't turn around
    C(T(98), 'rule', n=3, bg='hall')
    C(T(100), 'phone', states=[(t(100) + 0.2, 'photo_hall')], prate=0.03, y=600,
      zkeys=[(T(100), 1.2, 960, 560), (t(101) + 0.3, 1.45, 960, 560), (t(102) + 0.05, 1.75, 960, 470, 'in_out'), (T(103), 1.82, 960, 460, 'lin')],
      hit=t(102) + 0.05, music=[(t(102) + 0.05, 'stinger', 0.85)])
    C(T(103), 'hall', act=_A(ex('nervous'), back_view(), phone_look(-3)), cam=dict(mv='creep', x=900, y=520, z=1.0), music=[(t(103), 'silence', 0.0, 0.8)])
    C(w(103, 'holding') - 0.1, 'bust', who=Y, bg='hall', act=_A(ex('fear'), phone_look(-2)), light=phone_light, cam=dict(mv='push', x=960, y=560))
    C(T(104), 'hallback', cam=dict(mv='push', x=920, y=600, z=1.0, rate=0.045), music=[(t(104), 'swell', 0.6, 6)])
    C(T(105), 'phone', states=[(t(100) + 0.2, 'photo_hall')], full=True, zx=1100, zy=680, prate=0.07,
      tags=[(t(105) + 0.4, '3:11 AM', 1350, 690, 'red', 1.6)])
    C(T(106), 'hallback', dof=0.8, cam=dict(mv='keys', keys=[(T(106), 925, 520, 1.0, None, 1.0), (t(106) + 0.9, 925, 470, 1.25, 'in_out', 1.6),
                                                     (T(107), 925, 466, 1.3, 'lin', 1.75)]),
      tags=[(w(106, '3') + 0.2, '3:11 AM', 960, 170, 'white', 1.4)])
    C(T(107), 'bust', who=Y, bg='hall', act=_A(ex('fear'), phone_look(-2), lambda a, s: a.freeze(w(107, 'something'), s.t1 + 2)),
      cam=dict(mv='creep', x=960, y=560, z=1.0))
    kd = w(107, 'keys')
    C(kd - 0.5, 'ins', name='key_bowl_dad', kw=lambda tt, k0=kd - 0.45 - (kd - 0.5): dict(drop=clamp((tt - k0) / 0.55)), ghost_hand=kd - 0.6,
      cam=dict(mv='push', x=960, y=560, z=1.05, rate=0.04),
      sfx=[(kd - 0.45 + 0.55 * 0.8, 'keys_drop', 0, 0.2, 'inside', dict(bowl=True))], music=[(kd - 0.55, 'silence', 0.0, 0.5), (kd + 0.0, 'hit', 0.6)])
    C(T(108), 'bust', who=Y, bg='hall', act=_A(ex('sad'), lambda a, s: a.cry(s.t0 + 0.4, None)), cam=dict(mv='push', x=960, y=560))
    C(T(109), 'hall', era='memory', ppl=[P(DAD, path=(T(109) - 0.2, T(109) + 1.8, [HA(0.2, 2.2), HA(0.35, 1.5)]), act=_A(lambda a, s: a.drop_keys(T(109) + 2.0)),
                                           talk=False)], cam=dict(mv='push', x=1100, y=560, z=1.0, rate=0.03))
    C(w(109, 'every') - 0.1, 'ins', name='key_bowl', kw=lambda tt: dict(drop=clamp((tt - 0.2) / 0.55)), grade='memory',
      sfx=[(w(109, 'every') + 0.1 + 0.44, 'keys_drop', -4, 0.2, 'inside', dict(bowl=True, memory=True))], cam=dict(mv='push', x=960, y=560, z=1.05))
    C(t(110) - 0.25, 'bust', who=Y, bg='hall_back', ghost=(-0.12, 4.55), ghost_tilt=12, cx=1230, cy=600, scale=0.95, act=_A(ex('fear'), phone_look(-2), lambda a, s: a.freeze(t(110), s.t1 + 1)),
      cam=dict(mv='creep', x=960, y=560, z=1.0), music=[(t(110), 'sub_drop', 0.8)], sfx=[(t(110), 'sub_drop', -4, 0, None)])
    C(T(111, 0.6), 'hallback', ppl=[P(Y, at=('v', -0.45, 0.95), act=_A(ex('fear'), phone_look(-2), terror()), talk=False)], ghost='hall_end',
      cam=dict(mv='push', x=900, y=520, z=1.0, rate=0.035))
    C(T(113), 'phone', states=[(t(100) + 0.2, 'photo_hall')], full=True, zx=960, zy=560, prate=0.05,
      tags=[(t(113) + 0.5, 'PROOF OF DELIVERY', 960, 170, 'white', 2.0)])
    C(T(114), 'bust', who=Y, bg='hall_back', ghost=(-0.3, 3.3), ghost_tilt=18, cx=1230, cy=620, scale=0.95, act=_A(ex('fear'), eyes_shut(0.0)), cam=dict(mv='creep', x=960, y=560, z=1.05))
    C(w(114, 'standing') - 0.1, 'hallback', ghost=('v', 0.2, 2.6), ghost_tilt=18, cam=dict(mv='push', x=960, y=480, z=1.0, rate=0.05),
      music=[(w(114, 'standing'), 'braam', 0.8)], tags=[(w(114, 'received'), "DON'T TURN AROUND", 960, 150, 'alert')], tag_sound=False)
    C(T(115), 'bust', who=Y, bg='hall', act=_A(ex('fear'), eyes_shut(0.0)), cam=dict(mv='push', x=960, y=560, z=1.1))
    C(T(116), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), creep(4, 3, None)))], py=-60, z1=1.1)
    C(T(117, 0.4), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), lambda a, s: a.listen_tilt(w(117, 'tilts'), None, 1, 24)))],
      py=-120, z1=1.3)
    C(T(118), 'bust', who=Y, bg='hall', act=_A(ex('fear'), eyes_shut(0.0), lambda a, s: a.talk([(s.t0 + 0.2, s.t1, 'one two three four five six seven')], intensity=0.35)),
      cam=dict(mv='push', x=960, y=560))
    C(T(119), 'hallback', cam=dict(mv='creep', x=920, y=560, z=1.0), music=[(t(119), 'silence', 0.0, 1.4)])
    C(T(120), 'phone', states=[(T(120), 'photo_hall'), (w(120, 'gone') - 0.3, 'photo_gone')], prate=0.03, y=600,
      zkeys=[(T(120), 1.2, 960, 560), (w(120, 'gone') + 0.2, 1.45, 960, 540), (T(122), 1.65, 960, 520, 'in_out')])
    C(T(122), 'hall', ppl=[], cam=dict(mv='push', x=520, y=420, z=1.15, rate=0.04))

    # ============================================================ RULE 4 (275.9 - 379.3): don't let anyone else sign
    C(T(123), 'rule', n=4, bg='hall')
    C(T(125), 'hallback', ppl=[P(M, path=(T(125) - 0.2, e(125) + 0.2, ['stairs_mid', 'stairs_low']), act=_A(lambda a, s: a.squint_light(s.t0 - 1)), facing=0.4,
                                 surface='inside_stairs')],
      cam=dict(mv='move', x=1150, y=430, z=1.6, x1=1220, y1=520, z1=1.75))
    C(T(126), 'bust', who=M, bg='hall', act=_A(lambda a, s: a.squint_light(s.t0 - 2)), light=warm_light, cam=dict(mv='push', x=960, y=560))
    C(T(128), 'hall', ppl=[P(Y, at=HA(-0.3, 1.0), act=_A(ex('nervous'), lambda a, s: a.hold_up('phone', s.t0 + 0.2, s.t1 + 1, 1), turned(0.5))),
                           P(M, at=HA(0.35, 1.2), act=_A(ex('nervous'), turned(-0.6), lambda a, s: a.set(s.t0 + 0.4, None, 0.5, h_nod=0.2, look_y=0.4)))],
      cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.035))
    C(T(129), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), creep(5, 3, None)))], px=280, py=60, z1=1.4)
    C(w(129, 'faded') - 0.1, 'street', cam=dict(mv='push', x=1460, y=690, z=2.6, rate=0.035))
    C(T(130), 'bust', who=M, bg='hall', act=_A(ex('shock'), lambda a, s: a.set(s.t0 + 0.3, None, 1.2, m_open=0.25)), light=phone_light,
      cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.04), post_fn=lambda t_, t0=t(130): dict(sat=1.0 - 0.75 * ease_in_out(clamp((t_ - t0) / 2.2))))
    C(T(131), 'bust', who=M, bg='hall', act=_A(ex('fear'), lambda a, s: a.talk([(t(131), e(131), "that's the van")], intensity=0.4)), light=phone_light,
      cam=dict(mv='push', x=960, y=560, z=1.1), post=dict(sat=0.35))
    C(T(133), 'street', era='memory', cam=dict(mv='push', x=1400, y=680, z=1.6, rate=0.04), cut='white', music=[(t(133), 'hit', 0.6)])
    C(T(134), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), look_side(-1, -0.5)), cam=dict(mv='push', x=960, y=560))
    C(T(135), 'hall', ppl=[P(M, at=HA(0.3, 1.25), act=_A(ex('fear'), turned(-0.5), lambda a, s: a.set(s.t0, None, 0.3, look_y=0.5, h_nod=0.15)), light=phone_light),
                           P(Y, at=HA(-0.35, 1.05), act=_A(ex('nervous'), lambda a, s: a.hold_up('phone', s.t0 - 1, s.t1 + 1, 1), turned(0.55)))],
      cam=dict(mv='push', x=980, y=500, z=1.05, rate=0.03))
    C(w(135, 'without') - 0.1, 'bust', who=M, bg='hall', act=_A(ex('fear'), lambda a, s: a.set(s.t0, None, 0.3, look_y=0.45, lock=1.0)), light=phone_light,
      cam=dict(mv='creep', x=960, y=560, z=1.05))
    C(T(136), 'street', era='memory', drive=('in', t(136) - 0.2, t(136) + 3.2, -14.0, 3.6), cam=dict(mv='push', x=1100, y=620, z=1.2, rate=0.03),
      sfx=[(t(136), 'car_pass', 4, 0.4, 'street', dict(kind='arrive', memory=True))], music=[(t(136), 'motif', 0.5, 5)])
    C(T(136, 3.4), 'hall', era='memory', ppl=[P(DAD, at=HA(-0.2, 1.6), act=_A(back_view(), lambda a, s: a.set(s.t0, None, 0.4, h_turn=0.3)), talk=False)],
      cam=dict(mv='push', x=960, y=520, z=1.05, rate=0.03))
    C(T(137), 'peep', era='memory', ppl=[P(DR, act=_A(stare(), lambda a, s: a.ring_bell(t(137) + 0.6)))], show_box=False,
      cam=dict(mv='push', x=960, y=480, z=1.05))
    C(T(138), 'doorway', era='memory', tod='night', door_open=0.62, cam=dict(mv='push', x=960, y=600, z=1.15, rate=0.04))
    C(w(138, 'tall') - 0.1, 'box', era='memory', breath=1.0, cam=dict(mv='push', x=960, y=440, z=1.1, rate=0.04),
      sfx=[(w(138, 'talking') - 0.2, 'box_voice', 18, 0, 'box', dict(dur=3.2, memory=True)),
           (w(138, 'talking'), 'crowd_whisper', -4, 0, 'outside', dict(dur=2.8, density=2, memory=True))])
    C(T(139), 'bust', who=DAD, bg='memory', era='memory', act=_A(ex('shock'), lambda a, s: a.expr('sad', t(140), None)), cam=dict(mv='push', x=960, y=560))
    C(T(141), 'hall', era='memory', ppl=[P(DAD, at=HA(0.0, 2.1), act=_A(back_view()), talk=False),
                                          P(M, at=HA(-0.4, 1.3), act=_A(ex('fear'), turned(0.6), lambda a, s: a.reach(s.t0 + 0.3, None, 1, 260, 40, 240, 'open')), talk=False)],
      cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.035))
    C(T(142), 'bust', who=DAD, bg='memory', era='memory', act=_A(ex('polite'), nod(0.6)), cam=dict(mv='push', x=960, y=560))
    C(T(143), 'doorway', era='memory', tod='night', door_open=door_swing(t(143) + 0.2, 1.2, 0.0, 0.92),
      ppl=[P(DR, at='porch_out', act=_A(stare(), stage(4)), talk=False)], cam=dict(mv='push', x=980, y=560, z=1.05, rate=0.04),
      sfx=[(t(143) + 0.2, 'door_creak', -4, 0, 'inside', dict(memory=True))])
    C(T(144), 'street', era='memory', van=dict(driver=False, door=lambda tt, t0=w(144, 'slide'): 1.0 - ease_in_out(clamp((tt - t0) / 0.6))),
      cam=dict(mv='push', x=1440, y=690, z=1.9, rate=0.04), sfx=[(w(144, 'shut'), 'van_door_slide', 6, 0.4, 'street', dict(kind='close', memory=True))])
    C(T(145), 'ins', name='box_keys', kw=dict(keys=False), grade='memory', post=dict(sat=0.6),           # the box was empty
      cam=dict(mv='move', x=960, y=480, z=1.1, x1=960, y1=560, z1=1.4))
    C(T(146), 'bust', who=M, bg='hall', act=_A(ex('sad'), lambda a, s: a.cry(s.t0 + 0.5, None)), light=phone_light, cam=dict(mv='push', x=960, y=560))
    C(T(147), 'box', era='memory', breath=0.4, cam=dict(mv='move', x=960, y=900, z=1.1, y1=500, z1=1.2))
    C(T(148), 'door', ppl=[P(DR, at=DA(-0.1, 0.95), act=_A(stare(-1), carry(), lambda a, s: a.lean_close(t(148) + 0.3, 2.4, None, 8)), lean=True, k=0.62)],
      py=-130, z1=1.15, music=[(t(148) + 0.3, 'riser', 0.6, 2.4)])
    C(T(149), 'peep', ppl=[P(DR, at='driver_close', act=_A(stare()))], approach=False, cam=dict(mv='push', x=960, y=420, z=1.0, rate=0.04))
    C(T(152, 0.3), 'bust', who=DR, scale=1.15, act=_A(stare(-1), tilt(0.2, 10, 1.4), creep(4, 3, None)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04))
    C(T(153), 'peep', ppl=[P(DR, at='driver_close', act=_A(stare(), tilt(0.2, -14, 1.0)))], approach=False, cam=dict(mv='push', x=960, y=420, z=1.05))
    C(T(155), 'hall', ppl=[P(M, at=HA(0.15, 1.6), act=_A(ex('fear'), back_view(), lambda a, s: a.reach_chain(t(155) + 0.3, e(156) + 0.5, -1))),
                           P(Y, at=HA(-0.35, 1.0), act=_A(ex('fear'), back_view()))], cam=dict(mv='push', x=960, y=500, z=1.05, rate=0.04))
    C(T(156), 'hand', reach=1.0, catch=t(156) + 0.25, shake=1.3, cam=dict(mv='fast', x=1100, y=560, z=1.05),
      sfx=[(t(156) + 0.25, 'cloth_rustle', -4, 0, 'close')], hit=t(156) + 0.3)
    C(T(157), 'ins', name='tablet_sign', kw=dict(sig='initial', ink=1.0), lens='doorbell', cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04))
    C(T(158), 'bust', who=M, bg='hall', act=_A(ex('shock')), light=phone_light, cam=dict(mv='fast', x=960, y=560))
    C(T(159), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), tab_up(0.2), creep(6, 4, None)))], py=-60, z1=1.15)
    C(w(159, 'whoever') - 0.1, 'street', van=dict(driver=False, door=1.0), cam=dict(mv='push', x=1440, y=700, z=2.2, rate=0.06),
      music=[(w(159, 'goes'), 'hit', 0.6)])
    C(T(160), 'hand', reach=1.0, letgo=t(160) + 0.3, shake=1.0, cam=dict(mv='push', x=1000, y=540, z=1.05, rate=0.04))
    C(T(161), 'bust', who=M, bg='hall', act=_A(ex('cry'), lambda a, s: a.shaking_hand(s.t0, None, 1, 1.0)), light=phone_light, cam=dict(mv='push', x=960, y=600, z=0.95))
    C(T(162), 'bust', who=DR, scale=1.12, act=_A(stare(-1), frz(0.0, 3.0)), cam=dict(mv='creep', x=960, y=520, z=1.0))
    ef = w(163, 'shine') - 0.2
    C(T(163), 'door', ppl=[P(DR, at=DA(-0.05, 0.75), act=_A(stare(-1), lambda a, s: a.lean_close(s.t0 - 2, 0.5, None, 6, amount=0.6),
                                                             lambda a, s: a.eye_flash(ef, 0.5)), lean=True)], py=-140, z1=1.25,
      music=[(ef, 'stinger', 0.85), (ef - 1.0, 'silence', 0.0, 0.95)])
    C(w(163, 'like') - 0.1, 'bust', who=DR, ecu=True, cx=960, cy=470, scale=1.5, act=_A(stare(-1), lambda a, s: (a.eye_flash(s.t0 + 0.6, 0.35, 0.6), a.events.pop())),   # the flash, no second stinger
      cam=dict(mv='creep', x=960, y=520, z=1.3))
    C(T(164), 'box', cam=dict(mv='push', x=960, y=640, z=1.45, rate=0.05, roll=-3), music=[(w(164, 'knocks') + 0.42, 'hit', 0.5)])

    # ============================================================ RULE 5 (379.3 - 455.5): don't answer the box
    C(T(165), 'rule', n=5, bg='door')
    C(T(167), 'box', by=1340, view=-0.35, cam=dict(mv='push', x=980, y=720, z=1.2, rate=0.05))
    C(T(168), 'hall', ppl=[P(M, at=HA(0.2, 1.4), act=_A(ex('fear'), turned(-0.4))), P(Y, at=HA(-0.35, 1.05), act=_A(ex('fear'), turned(0.5)))],
      cam=dict(mv='creep', x=960, y=520, z=1.05, hit=[w(169, 'one') - 0.02]), music=[(t(168), 'silence', 0.0, 0.9)])
    C(T(170), 'bust', who=M, bg='hall', act=_A(ex('cry'), lambda a, s: a.set(s.t0 + 0.3, None, 0.2, m_open=0.5)), light=phone_light,
      cam=dict(mv='fast', x=960, y=560), sfx=[(t(170) + 0.4, 'breath', -2, 0, 'inside', dict(kind='sob'))])
    C(T(172), 'box', cam=dict(mv='push', x=1010, y=420, z=1.85, rate=0.04))
    C(T(173), 'upstairs', era='memory', grade='memory', hall_light=1.0, lily_door=0.0,
      ppl=[P(DAD, at=('v', -0.3, 1.7), act=_A(turned(1.3), lambda a, s: a.knock(w(173, 'knock') + 0.1, 2, 0.3, 1),
                                                lambda a, s: a.knock(w(173, 'knock') + 0.95, 1, 0.3, 1)), talk=False)],
      cam=dict(mv='push', x=900, y=540, z=1.15, rate=0.03))
    C(w(173, 'every') - 0.1, 'bust', who=DAD, bg='memory', era='memory', act=_A(ex('polite'), smile(0.3, 2.0, 0.5)), cam=dict(mv='push', x=960, y=560))
    C(t(174) - 0.25, 'wave', layout='door', title='FRONT DOOR  -  MIC', rows=[dict(label='VOICE  -  INSIDE THE BOX', color='red', seed=14, p=(t(174), e(174)))],
      play=(t(174), e(176)), tags=[(t(175) + 0.2, 'INSIDE THE BOX', 960, 300, 'red', 1.6)])
    C(T(176), 'bust', who=M, bg='hall', act=_A(ex('shock'), lambda a, s: a.set(s.t0, None, 0.2, m_open=0.45)), light=phone_light, cam=dict(mv='fast', x=960, y=560))
    C(T(177), 'box', breath=1.0, view=0.5, cam=dict(mv='push', x=960, y=470, z=1.25, rate=0.04, roll=2))
    C(T(179), 'bust', who=M, bg='hall', act=_A(ex('cry'), lambda a, s: a.hands_over_mouth(t(179) + 0.3)), light=phone_light, cam=dict(mv='push', x=960, y=560))
    C(T(180), 'box', h=1080, by=1290, cam=dict(mv='creep', x=960, y=560, z=1.0), music=[(t(180), 'braam', 0.7)])
    C(T(181), 'door', ppl=[P(DR, at=DA(-0.2, 1.0), act=_A(stare(-1), carry(), creep(3, 3, None)))], px=160, py=0, z1=1.25)
    C(T(183), 'wave', layout='box', title='VOICE MATCH', rows=[dict(label='DAD  -  21 YEARS AGO', color='blue', seed=21),
                                                                   dict(label='THE BOX  -  TONIGHT', color='red', seed=21, p=(t(183), e(183)))],
      play=(t(183), e(183)), post=dict(sat=0.6))
    C(T(184), 'box', cam=dict(mv='push', x=960, y=600, z=1.35, rate=0.04), tags=[(w(184, 'nickname'), '“MAR”', 960, 200, 'red', 1.6)], tag_sound=False)
    C(T(186), 'hall', ppl=[P(M, at=HA(0.15, 1.75), act=_A(ex('fear'), back_view())), P(Y, at=HA(-0.4, 1.1), act=_A(ex('fear'), back_view()))],
      cam=dict(mv='push', x=960, y=480, z=1.0, rate=0.045))
    C(t(187) - 0.2, 'bust', who=Y, bg='hall', act=_A(ex('shock')), cam=dict(mv='fast', x=960, y=560), music=[(t(187), 'hit', 0.7)])
    C(T(189), 'box', breath=0.8, view=-0.5, cam=dict(mv='push', x=900, y=480, z=1.3, rate=0.04, roll=-2))
    C(T(190), 'bust', who=Y, bg='hall', act=_A(ex('cry'), lambda a, s: a.cry(s.t0, None)), cam=dict(mv='push', x=960, y=560))
    C(T(191), 'door', ppl=[P(DR, at=DA(-0.1, 0.9), act=_A(stare(-1), tab_up(0.2), lean(0.5, 1.2, 0.5)), lean=True)], py=-60, z1=1.25)
    C(T(192), 'hall', ppl=[P(M, at=HA(0.05, 1.3), act=_A(ex('cry'), turned(0.4))),
                           P(Y, at=HA(-0.3, 1.2), act=_A(ex('cry'), turned(0.7), lambda a, s: a.hold_close(s.t0 + 0.2, None, 1)))],
      cam=dict(mv='push', x=900, y=500, z=1.05, rate=0.035))
    C(T(194), 'box', cam=dict(mv='fast', x=960, y=600, z=1.15, roll=3))
    C(T(195), 'hall', ppl=[], lamp=0.0, cam=dict(mv='push', x=960, y=520, z=1.1, rate=0.06))
    C(w(195, 'two', 1) - 0.1, 'box', cam=dict(mv='push', x=960, y=640, z=2.0, rate=0.06, roll=-4))
    C(T(196), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), frz(0.3, 3.0)))], py=-130, z1=1.3)
    C(T(197), 'bust', who=DR, scale=1.15, act=_A(stare(-1), frz(0.0, 3.0)), cam=dict(mv='creep', x=960, y=520, z=1.0))
    C(T(198), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), lambda a, s: a.slow_look_side(t(198) + 0.2, 3.2, -1, back=t(199) + 0.05)))],
      py=-80, z1=1.15)
    C(w(198, 'backyard') - 0.1, 'side', window_open=False, cam=dict(mv='push', x=960, y=480, z=1.1, rate=0.035))
    C(T(199), 'door', ppl=[P(DR, at=DA(-0.15, 0.95), act=_A(stare(-1), carry(), lambda a, s: a.slow_look_side(s.t0 - 4.0, 0.5, -1, back=t(199) + 0.05)))],
      py=-130, z1=1.3, music=[(t(199), 'stinger', 0.8)])
    C(w(199, 'wider') - 0.1, 'bust', who=DR, scale=1.2, act=_A(stare(-1), tilt(0.2, 20, 1.6), creep(0, 4, None)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.05),
      hit=w(199, 'wider'))
    C(T(200), 'peep', ppl=[P(DR, act=_A(stare(), carry(), tilt(2.4, 14, 1.0)))], cam=dict(mv='push', x=960, y=470, z=1.05))

    # ============================================================ RULE 6 (455.5 - 510.8): don't bring it inside before sunrise
    C(T(204), 'rule', n=6, bg='door')
    C(T(206), 'door', box=None, box_move=(T(206) + 0.25, T(206) + 1.75, (0.58, 1.02), (-0.8, 0.42)),
      ppl=[P(DR, path=[(T(206) + 0.2, T(206) + 1.7, [DA(-0.1, 0.95), DA(-0.62, 0.66)], -1.0)],
             act=_A(stare(-1), lambda a, s: a.reach(T(206), T(206) + 1.75, 1, 230, 40, 120, 'open'), lambda a, s: a.set_box_down(T(206) + 1.5, 1.4, 1)), k=0.5)],
      z0=1.0, z1=1.08, py=0)
    C(T(207), 'hall', ppl=[], feet=lambda tt, t0=t(207): [0.36 + 0.06 * clamp((tt - t0 - 0.2) / 1.0), 0.5], cam=dict(mv='push', x=960, y=900, z=1.3, rate=0.04),
      sfx=[(t(207) + 0.3, 'box_scrape', -2, -0.2, 'inside', dict(dur=1.0))])
    C(T(208), 'door', box='door', ppl=[P(DR, at=DA(-0.45, 1.1), act=_A(stare(-1), lambda a, s: a.take_photo(t(208) + 0.3, 1)))], py=-40, z1=1.12,
      post_fn=lambda t_, tf=t(208) + 0.3 + 1.6 * 0.55: dict(white=0.5 * math.exp(-((t_ - tf) / 0.05) ** 2)))
    C(T(209), 'door', box='door', steps_fade=10.0, ppl=[P(DR, act=_A(stare(-1), carry(), lambda a, s: a.climb_in(t(209) + 2.1)), track=True,
                                         path=[(T(209), T(209) + 2.1, [DA(-0.45, 1.1), 'steps', 'path_mid', 'gate', 'van_cab'], 2.0)])],
      py=0, z1=1.08,
      # the cab door (climb_in's own event lands after the cut to the app, where shot_common drops it)
      sfx=[(t(209) + 2.1 + 1.2 + 0.35, 'car_door_close', -3, 0.45, 'street')])
    C(T(210), 'phone', states=[(t(210) + 0.15, 'attempted')], prate=0.03, y=560,
      zkeys=[(T(210), 1.2, 960, 540), (t(212), 1.45, 960, 520), (t(213) + 0.3, 1.62, 960, 680, 'in_out'), (T(214), 1.7, 960, 700, 'lin')],
      tags=[(w(213, '6') + 0.1, '6:12 AM', 960, 170, 'red', 1.8)])
    C(T(214), 'street', cam=dict(mv='push', x=960, y=480, z=1.0, rate=0.03), tags=[(t(214) + 0.4, 'SUNRISE  6:12', 960, 200, 'white', 1.8)])
    C(T(215), 'doorway', tod='night', door_open=0.0, cam=dict(mv='push', x=980, y=880, z=1.15, rate=0.04), tags=[(w(215, 'threshold'), 'THE THRESHOLD', 960, 200, 'red', 1.6)])
    C(T(216), 'door', box='door', ppl=[], px=-520, py=120, z0=1.25, z1=1.55)
    C(T(217), 'hall', ppl=[], lamp=0.0, cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.045))
    C(w(217, 'height') - 0.1, 'bust', who=Y, bg='hall', act=_A(ex('fear')), cam=dict(mv='hand', x=960, y=560))
    C(T(219), 'hall', ppl=[P(M, at='wall_sit', act=_A(ex('cry'), turned(-0.6), lambda a, s: a.sit_floor(s.t0 - 2))),
                           P(Y, at=HA(0.62, 1.3), act=_A(ex('fear'), turned(-0.55), lambda a, s: a.sit_floor(w(219, 'next') - 0.35)))],
      cam=dict(mv='push', x=1260, y=640, z=1.05, rate=0.03))
    C(T(220), 'bust', who=M, bg='hall', act=_A(ex('cry'), down(-1, 0.4)), light=phone_light, cam=dict(mv='push', x=960, y=600, z=1.0))
    C(T(221), 'hall', ppl=[], lamp=0.0, cam=dict(mv='creep', x=960, y=520, z=1.1), tags=[(w(221, 'three'), '3:40 AM', 960, 170, 'white', 1.6)], tag_sound=False,
      music=[(w(221, 'stops') + 0.1, 'silence', 0.0, 1.8)])
    C(T(222), 'bust', who=Y, bg='hall', act=_A(ex('fear'), phone_look(0.2)), light=phone_light, cam=dict(mv='push', x=960, y=600))
    C(T(223), 'door', box='door', ppl=[], post_off=(-420, 60), px=800, py=0, z0=1.3, z1=1.6)
    C(T(225), 'street', cam=dict(mv='push', x=1110, y=600, z=2.6, rate=0.03))
    C(T(226), 'ins', name='van_seat', cam=dict(mv='creep', x=960, y=540, z=1.0, snap=(w(226, 'empty'), 1.25)), hit=w(226, 'empty'),
      music=[(w(226, 'empty'), 'stinger', 0.9)])

    # ============================================================ RULE 7 (510.8 - end): check every window
    C(T(227), 'rule', n=7, bg='street')
    C(T(229), 'door', box='door', ppl=[], py=-60, z1=1.15)
    C(T(230), 'side', window_open=False, ppl=[P(DR, at=('v', -2.2, 2.2), act=_A(stare(-1), turned(1.2)), shadow=0.88, talk=False, track=False)],
      cam=dict(mv='push', x=820, y=620, z=1.1, rate=0.04), music=[(t(230), 'hit', 0.55)])
    C(T(231), 'hallback', ppl=[P(Y, path=(T(231) - 0.1, T(231) + 1.25, [('v', 0.1, 1.1), 'arch']), act=_A(ex('fear')), facing=2.0,
                                 surface='inside_run')],
      cam=dict(mv='keys', shake=7.0, keys=[(T(231), 900, 600, 1.0), (T(232), 1010, 470, 1.42, 'in')]), handheld_hz=1.7)
    C(T(232), 'kitchen', cam=dict(mv='fast', x=960, y=330, z=1.75), without=('headlights', 'police_spill', 'pendant_light', 'pendant'),
      tags=[(w(232, 'locked'), 'LOCKED', 960, 200, 'white', 0.9)], sfx=[(w(232, 'locked'), 'window_latch', -4, 0.2, 'inside'),
                                                                        (T(232) + 0.05, 'footsteps_wood_inside', -5, 0.0, 'inside',
                                                                         dict(n=13, rate=3.5, run=True))])
    C(T(233), 'living', cam=dict(mv='fast', x=960, y=480, z=1.1), tags=[(w(233, 'locked'), 'LOCKED', 960, 200, 'white', 0.9)],
      sfx=[(w(233, 'locked'), 'window_latch', -4, -0.2, 'inside')])
    C(T(234), 'latch', win='bath', t_lock=w(234, 'locked') - 0.05, tags=[(w(234, 'locked'), 'LOCKED', 960, 200, 'white', 0.9)])
    C(T(235), 'hallback', ppl=[P(Y, path=(T(235), T(235) + 1.5, ['stairs_low', 'stairs_mid']), act=_A(ex('fear')), facing=2.0,
                                 surface='inside_run_quiet')],
      cam=dict(mv='keys', shake=6.0, keys=[(T(235), 1100, 520, 1.05), (T(236), 1190, 430, 1.3, 'in_out')]), handheld_hz=1.5,
      sfx=[(T(235) + 0.1, 'footsteps_wood_inside', -2, 0.3, 'inside', dict(n=5, rate=3.5, stairs=True, run=True))])
    C(T(236), 'latch', win='mom', t_lock=w(236, 'locked') - 0.05, tags=[(w(236, 'locked'), 'LOCKED', 960, 200, 'white', 0.9)])
    C(T(237), 'upstairs', lily_door=0.07, cam=dict(mv='move', x=960, y=560, z=1.0, x1=960, y1=520, z1=1.5), music=[(t(237), 'silence', 0.0, 1.0)])
    C(T(239), 'bust', who=LI, bg='lily', act=_A(lambda a, s: a.sleepy(s.t0 - 2), smile(0.4, 2.0, 0.3)), cam=dict(mv='push', x=960, y=560), music=[(t(239), 'motif', 0.5, 4)])
    C(T(240), 'lily', bed='sleeping', cam=dict(mv='push', x=820, y=620, z=1.05, rate=0.035))
    C(w(240, 'window') - 0.1, 'side', window_open=True, cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.03))
    tpush = t(241) + 0.45
    C(T(241), 'upstairs', lily_door=lambda tt, t0=tpush: 0.07 + 0.83 * ease_in_out(clamp((tt - t0) / 1.1)), pov_push=tpush, dof=0.6,
      cam=dict(mv='keys', shake=3.0, keys=[(T(241), 960, 531, 1.15, None, 1.3), (tpush, 960, 531, 1.4, 'in_out', 1.3),
                                           (T(242), 960, 531, 1.6, 'lin', 1.3)]),        # constant optical zoom: no re-bakes
      posts=[(T(241), tpush, 1.0, 1.12, 0, 0, 'in_out'), (tpush, T(242), 1.0, 1.25, 0, 0, 'lin')],    # the push into the image
      sfx=[(tpush, 'door_creak', -2, 0, 'inside'), (tpush - 0.05, 'cloth_rustle', -10, 0.3, 'close')])
    # one continuous shot (fix 3): the door swings in on the open window, push to the black gap and the blowing curtains,
    # then pan down to the empty bed ("the window is wide open / the curtains are moving / her bed is empty")
    C(T(242), 'lily', bed='empty', window_open=True, dof=0.7,                  # (low DOF: the optical push stays in budget)
      cam=dict(mv='keys', shake=2.2, keys=[(T(242), *DP(1000, 500, 3.4), 1.05, None, 1.0),
                                           (w(242, 'open') + 0.25, *DP(1039, 470, 3.4), 1.4, 'push', 1.9),
                                           (e(243) - 0.05, *DP(1039, 462, 3.4), 1.5, 'lin', 2.15),
                                           (w(244, 'empty') + 0.45, *DP(690, 650, 2.0), 1.45, 'in_out', 1.6),
                                           (w(244, 'still') + 0.3, *DP(700, 655, 2.0), 1.5, 'out', 1.7)]),
      hit=w(242, 'wide'),
      sfx=[(t(243), 'cloth_rustle', -6, 0.2, 'inside', dict(kind='curtain', dur=1.2))],
      music=[(w(242, 'wide'), 'braam', 0.85)])
    C(w(244, 'still') - 0.1, 'bust', who=Y, bg='lily', act=_A(ex('shock')), light=moon_light, cam=dict(mv='fast', x=960, y=560))
    C(T(245), 'phone', bg='lily_room', states=[(w(245, 'buzzes'), 'notify_return')], full=True, pshake=9.0, psnap=(t(246) + 0.05, 1.4, 960, 470),
      hit=t(246) + 0.05, music=[(t(246), 'stinger', 0.85)])
    C(T(247), 'phone', bg='lily_room', states=[(t(247) + 0.3, 'photo_lily')], scale=1.2, sig=0.0)    # the name stays hidden till 571 s
    ph = ST.photo_lily_scene()
    (tbx, tby), (hdx, hdy) = ph['tablet'], ph['head']
    wx0_, wy0_, wx1_, wy1_ = ph['window']
    C(T(249), 'photo', pop=True, tags=[(w(249, '3:41'), '3:41 AM', 960, 200, 'red', 1.4)], music=[(t(250), 'motif', 0.5, 4)],
      path=[(T(249), 975, 752, 1080), (e(249) - 0.2, 972, 728, 930, 'push'),                              # the whole photo
            (w(250, 'leaning') + 0.25, (wx0_ + wx1_) / 2 + 2, wy0_ + 92, 440, 'in_out'), (t(251), (wx0_ + wx1_) / 2, wy0_ + 98, 405, 'lin'),
            (w(251, 'tablet') + 0.3, (tbx + hdx) / 2, (tby + hdy) / 2 + 22, 540, 'in_out'), (t(252), (tbx + hdx) / 2, (tby + hdy) / 2 + 20, 505, 'lin'),
            (w(252, 'finger') + 0.3, tbx, tby - 28, 255, 'in_out'), (T(253) + 0.1, tbx, tby - 30, 236, 'lin')])
    C(T(253), 'phone', bg='lily_room', states=[(t(247) + 0.3, 'photo_lily')], full=True, zx=960, zy=700, prate=0.07,
      sig=lambda tt, t0=w(253, 'signature'): 0.5 * clamp((tt - t0) / 0.6))          # the SIGNED BY row, its line still empty
    C(t(254) - 0.15, 'ins', name='tablet_lily', cam=dict(mv='creep', x=960, y=600, z=1.2, snap=(t(254) + 0.02, 1.35)), hit=t(254) + 0.02,
      music=[(t(254) + 0.02, 'sub_drop', 1.0), (t(254) - 1.2, 'silence', 0.0, 1.15)], sfx=[(t(254) + 0.02, 'sub_drop', -2, 0, None)])
    C(T(255), 'bust', who=LI, bg='lily', act=_A(lambda a, s: a.set(s.t0 - 1, None, 0.2, look_x=0.6, look_y=0.1, lock=1.0, wide=0.4)), cam=dict(mv='push', x=960, y=560))
    C(T(256), 'lily', bed='sleeping', dof=0.7, cam=dict(mv='keys', keys=[(T(256), *DP(1180, 700, 2.4), 1.15, None, 1.05),
                                                               (T(257), *DP(1415, 780, 2.4), 1.4, 'in_out', 1.7)]),
      sfx=[(w(256, 'knock'), 'box_knock', -2, 0.4, 'inside', dict(on='vent', n_in_pattern=1))])
    C(T(257), 'door', box='door', ppl=[], px=-480, py=100, z0=1.2, z1=1.45, clock=_hms(3, 39, 41))
    C(T(258), 'bust', who=LI, bg='lily', act=_A(lambda a, s: a.set(s.t0 - 1, None, 0.2, look_x=0.5, lock=1.0, wide=0.3, brow_sad=0.4)),
      cam=dict(mv='creep', x=960, y=560, z=1.05))
    C(w(258, 'cold') - 0.2, 'side', window_open=True, cam=dict(mv='push', x=960, y=520, z=1.6, rate=0.035))
    C(w(258, 'sign') - 0.2, 'photo', comp='lily', pop=True, cam=dict(mv='push', x=960, y=560, z=1.06, rate=0.04))
    C(T(260), 'bust', who=LI, bg='side', act=_A(lambda a, s: a.lean_out(s.t0 - 2, None, -1, reach_t=s.t0 + 0.6), smile(0.4, 1.6, 0.4)),
      cam=dict(mv='push', x=960, y=560))
    C(T(261), 'lily', view='window', hz=dict(t_off=T_HZ_OFF), drive=('out', T_VAN_GO[0], T_VAN_GO[1], -9.0, 14.0),
      cam=dict(mv='keys', keys=[(T(261), 780, 480, 1.18), (T_HZ_OFF + 0.6, 790, 480, 1.36, 'push'), (T(262) + 1.2, 800, 490, 1.42, 'lin'),
                                (w(262, 'turns') - 0.1, 900, 500, 1.46, 'in_out')]),
      music=[(T_HZ_OFF, 'silence', 0.0, 1.4)])
    C(w(262, 'turns') - 0.1, 'street', hazard=dict(t_off=T_HZ_OFF), drive=('out', T_VAN_GO[0], T_VAN_GO[1], 3.6, 26.0), cam=dict(mv='pull', x=960, y=560, z=1.0),
      music=[(w(262, 'gone'), 'hit', 0.5)])

    # ============================================================ SUNRISE (598.2 - 618.9)
    C(T(263), 'door', tod='dawn', box='door', ppl=[], py=-30, z1=1.12, cut='white', quiet_cut=True,
      music=[(t(263), 'motif', 0.45, 6), (t(263) - 0.2, 'swell', 0.45, 5.0)])
    C(T(264), 'doorway', tod='dawn', door_open=door_swing(t(264) + 0.2, 1.4, 0.0, 0.92), box=dict(at='door', state='open'),
      ppl=[P(M, at='hall_near', act=_A(back_view(), ex('sad')), light=dawn_light)], cam=dict(mv='move', x=980, y=560, z=1.0, x1=980, y1=760, z1=1.3),
      sfx=[(t(264) + 0.25, 'door_creak', -3, 0, 'inside'), (t(264) + 0.1, 'chain_lock', 0, 0, 'inside', dict(action='unlock'))])
    C(T(266), 'box', tod='dawn', cam=dict(mv='push', x=960, y=520, z=1.1, rate=0.04), sfx=[(t(266) + 0.13, 'tape_rip', -4, 0, 'close', dict(kind='cut', dur=0.9))])
    C(T(267), 'ins', name='box_keys', cam=dict(mv='move', x=640, y=420, z=1.5, x1=990, y1=560, z1=1.9), music=[(w(268, 'ring'), 'hit', 0.55)],
      sfx=[(t(267) + 0.05, 'box_open', -2, 0, 'close', dict(keys=True)), (w(268, 'keys') + 0.2, 'keys_drop', -10, 0, 'close', dict(jingle=True))])
    C(T(269), 'keys', cam=dict(mv='move', x=960, y=480, z=1.0, x1=960, y1=600, z1=1.35), sfx=[(t(269) + 0.2, 'keys_drop', -8, 0, 'close', dict(jingle=True, lift=True))],
      tags=[(w(269, 'second'), 'D - A - D', 960, 200, 'white', 2.0)], tag_sound=False)
    C(T(270), 'hall', police=dict(mode='sweep', strength=0.7), ppl=[P(M, at='stairs_low', act=_A(ex('sad'), lambda a, s: a.sit_floor(s.t0 - 2), down(-1, 0.4)))],
      lamp=1.0, cam=dict(mv='push', x=700, y=560, z=1.05, rate=0.03))
    C(T(271), 'bust', who=M, bg='hall', lamp=1.0, act=_A(ex('sad'), down(-1, 0.3)), light=warm_light, cam=dict(mv='push', x=960, y=560))
    C(T(272), 'upstairs', lily_door=0.9, hall_light=0.6, cam=dict(mv='push', x=960, y=540, z=1.1, rate=0.035))
    C(T(273), 'bust', who=Y, bg='hall', lamp=1.0, act=_A(ex('sweaty'), lambda a, s: a.set(s.t0, None, 0.3, eye_open=0.75)), light=warm_light,
      cam=dict(mv='creep', x=960, y=560, z=1.05))

    # ============================================================ THE NEXT NIGHT (618.9 - end)
    C(T(274), 'hall', ppl=[P(Y, at='you', act=_A(ex('fear'), back_view(), phone_look(-3)))], lamp=0.0, cam=dict(mv='push', x=900, y=540, z=1.0, rate=0.04),
      music=[(t(274), 'silence', 0.0, 1.2)])
    C(w(274, 'phone') - 0.1, 'phone', states=[(w(274, 'lights'), 'notify_on_way')], full=True, pshake=8.0)
    C(T(276), 'bust', who=Y, bg='hall', act=_A(ex('fear'), phone_look(-2)), light=phone_light, cam=dict(mv='hand', x=960, y=560))
    C(T(277), 'phone', states=[(t(277) + 0.2, 'on_way')], prate=0.03, y=560,
      zkeys=[(T(277), 1.2, 960, 540), (t(278) + 0.2, 1.5, 960, 470), (t(279) + 0.6, 1.62, 960, 560, 'in_out'),
             (w(280, 'child'), 1.62, 960, 600, 'lin'), (w(280, 'lily') + 0.02, 1.95, 960, 640, 'in_out'), (T(281), 2.02, 960, 645, 'lin')],
      hit=w(280, 'lily') + 0.02, music=[(w(280, 'lily'), 'stinger', 0.95)])
    # fix 3: "somewhere down the street": the van's hazards far down the block, turning in toward us (not parked at 144)
    C(T(281), 'street', hazard=True, drive=('pass', t(281) - 0.6, e(281) + 0.6, -14.5, -6.6), cam=dict(mv='push', x=760, y=560, z=1.2, rate=0.03))
    C(T(282), 'box', by=1360, view=-0.3, sender='Lily', cam=dict(mv='push', x=960, y=760, z=1.4, rate=0.05))
    C(T(283), 'door', box='boots', sender='Lily', ppl=[P(DR, at=DA(-0.05, 0.9), act=_A(stage(5), grin(-1), lean(0.1, 0.8, 1.0), tilt(0.2, 16, 1.0)), lean=True, k=0.62)],
      py=-110, z1=1.12)
    C(T(284), 'peep', ppl=[P(DR, at='driver_close', act=_A(stage(5), grin(-1), frz(0.1, 1.0)))], approach=False, cam=dict(mv='push', x=960, y=420, z=1.05, rate=0.04),
      music=[(t(284), 'silence', 0.0, 0.7)])
    # fix 3: the last knock lands in the silence after "A pause."; the hit follows it 0.15 s later (it buried the knock)
    t_end = e(285) + 0.3
    C(w(285, 'one') - 0.12, 'box', sender='Lily', cam=dict(mv='push', x=960, y=620, z=1.6, rate=0.07, roll=-3),
      music=[(w(285, 'one') + 0.15, 'hit', 0.85), (t_end, 'end', 0.8, round(min(3.0, F.duration - t_end - 0.3), 2))])
    C(e(285) + 0.28, 'black', cut='static', sfx=[(e(285) + 0.28, 'impact_hit', 6, 0, None, dict(size=1.5)),   # final mix: at the limiter's ceiling (+6 -> +2.5 LU)
                                               (e(285) + 0.28, 'sub_drop', 0, 0, None)])

    # ============================================================ global cues
    last_end = -10.0
    for l in F.L:                                                     # the doorbell speaker: a click before he talks
        if l.get('fx') == 'doorbell' and l.get('found_en', True):
            if l['t'] - last_end > 2.0:                               # fix 3: not on mid-sentence resumes
                G.append(_ev(l['t'] - 0.12, 'ui_pop', -10, 0.0, 'doorbell_mic', kind='speaker'))   # final mix: -16 was 30 LU under
            last_end = l['end']
    G.append(_ev(t(122), 'footsteps_wood_inside', -6, -0.3, 'inside', n=6, rate=1.4, stairs=True, slippers=True))
    G.append(_ev(t(219) - 1.0, 'heartbeat', -8, 0, None, bpm=64, bpm_end=72, dur=8.0))
    G.append(_ev(t(242), 'heartbeat', -6, 0, None, bpm=88, bpm_end=120, dur=10.0))
    G.append(_ev(t(110) - 0.3, 'breath', -8, 0.0, 'inside', kind='held', dur=2.0))
    G.append(_ev(t(264) + 0.25, 'birds', -2, 0.2, 'porch', dur=round(T_STING - t(264) - 0.25, 1)))
    for i_, kind in ((10, 'motif'), (47, 'swell'), (91, 'swell'), (136, 'motif'), (148, 'swell'), (183, 'swell'), (198, 'swell'),
                     (219, 'swell'), (239, 'motif'), (249, 'swell'), (263, 'motif'), (274, 'swell')):
        G.append({'t': round(t(i_), 3), 'type': kind, 'level': 0.6, 'len': 6.0 if kind == 'swell' else 4.0})
    for tr in (w(13, 'rings'), w(55, 'empty'), w(163, 'shine'), t(221) + 0.4, w(242, 'wide'), w(280, 'lily')):   # risers peak ON the reveal
        G.append({'t': round(tr, 3), 'type': 'riser', 'level': 0.6, 'len': 3.0})
    G.append({'t': round(t(194), 3), 'type': 'pulse_on', 'level': 0.7})
    G.append({'t': round(t(196), 3), 'type': 'pulse_off', 'level': 0.5})


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
    if a.sheet:
        sh = F.shots[a.range[0]:a.range[1]] if a.range else F.shots
        print(contact_sheets(F, a.sheet, cols=a.cols, tile=a.tile, ts=[(s.t0 + s.t1) / 2 for s in sh]))
