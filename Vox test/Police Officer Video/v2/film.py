"""film.py: the v2 shot list, editor and cue sheets for "If A Police Officer Knocks..." (director / integrator).

    from film import Film
    F = Film(timeline_dict)          # engine set_render_size(...) must be called first (render.py does it)
    F.frame(t, i) -> uint8 RGB       # one frame at the engine render size
    F.duration                       # seconds (narration + tail)
    F.shots                          # [Shot(t0, t1, kind, p)] ~240 shots, hard cuts (a few static / white scare flashes)
    F.cues(out_dir=None) -> (sfx, music)   writes $S/pov2/cues/sfx_cues.json + music_cues.json (ARCHITECTURE contract)
    F.sheet(path_prefix, cols=8)     one 960x540 still per shot (mid-shot) as contact sheets
    python3 film.py --cues | --sheet | --list | --bench N

Shot kinds (builders B_<kind>): street (house 144 across the street), door (doorbell fisheye / IR), peep (peephole),
bust (face close-up with DOF background: porch, hall, mumroom, mumext, car), car (back-seat window), hall (hallway from
inside), ins (prop inserts from sets.insert), hands (ring / thumb close-ups), kitchen, living (living-room window), mumext,
mumroom, phone (phone UI over a blurred room), wave (radio waveform panel), rule (rule card over a blurred scene).
Every shot has a moving camera (push / drift / pull / tilt / post-push into doorbell footage), people acting with
characters.Acting (speakers' mouths follow their timeline lines; the narrator's lines move no mouths), HUD tags and the v1
captions (<= 40 characters per chunk, timed proportionally, quotes for dialogue, none on rule cards) plus the header.
Cue sheets are derived from the picture: acting events (knocks, footsteps, radio clicks, bodycam beeps, paper, breath),
car doors, radio squelch/static on radio lines, phone states, tag pops, rule stings and typing, whooshes on fast moves,
hits and silences on reveals and scare cuts, beds per location, a music intensity curve with risers, pulses and stingers.

Plan conventions (plan() at the end of the file): F.cut(t, kind, **p) starts a shot; it ends at the next cut. Times come
from the timeline (F.t(i) line start, F.e(i) line end, F.w(i, 'word') ASR word start inside line i). Common p keys:
cam=dict(mv='push'|'fast'|'creep'|'pull'|'drift'|'move'|'hand', x, y, z, rate, x1, y1, z1, snap=(t, k), hit=[t], opt=k
(optical zoom), d=depth (x, y given on a layer at that depth)); ppl=[P(who, at=anchor|(x, y, depth, h), act=f(a, shot),
lean=True, path=(t0, t1, [anchors]))]; act=f(acting, shot) for bust/hall/car; tags=[(t, text, x, y, style, hold)];
sfx=[(t, name, gain_db, pan, space, params)]; music=[(t, type, level, len)]; cut='static'|'glitch'|'white' (scare flash);
post={...} (engine post fx); without=(layer names) to drop near set layers. Global look (glob_fx): per-family exposure,
the last 35 % creeping into red_alert (+60 % saturation, -0.3 stop), scare flashes, fade in / out.
Measured (tests in $S/pov2/tests/film/): 261 shots, median 2.55 s (p10 1.44, p90 4.07); 2560x1440 one process, one
OpenCV thread, 120 frames over 30 shots: 0.54 s/frame mean incl. cold caches, 0.37 s steady (shared machine); red share per tenth
<= 1.3 % until the climax, 2.9 / 5.3 / 6.2 % in the last three tenths.

v2.1 (film fixer, after the owner / critic review; tests in $S/pov2/tests/filmfix/)
- Doorbell: every door shot is staged (approach up the path, step closer, lean into the lens so the fisheye bulges the
  face, knock on the door beside the camera (side -1) or on the lens (side 0) with the doorbell jolting, step out of
  frame and back, turn to the car, raise the radio, the double stepping past the officer, unison leans). Walkers' layer
  depth follows their path (they sort against the railing and grow like a real approach); path may be a list of legs
  [(t0, t1, [anchors], facing), ...]. DA(X, D) / PA / HA / MA / MX give anchors in the doorbell, peephole, hall,
  mum's-room and mum's-street views. IR only for the 143 s grin and the 557 s flashback. Grade doorbell_night is full
  colour now. The motion box follows lay._box(t) (dynamic depth, lean aim).
- Acting layers: creep() (tilt drift, sway, twitch, loosened stillness), sway(), tremble() (jitter + blink bursts),
  knk / knk_at (door or lens knocks), pt (point, dx=0 at the lens), radio, turned / turn_to, hand_mouth, jerk_at, frz;
  escalate() adds twitches / jerks to the creepy cast from 450 s and tremble to you (300 s+) / mum (584 s+).
- Peephole subjects lean in over the shot (45 % -> ~70 % of the disc); push 4.5 %/s. Inserts push 4.5 %/s plus a uniform
  post push (_post_push); phone UI and waveform panels push / drift / shake on the canvas (hud_push).
- B_wave: panel >= 60 % W over a sharp lit background (officer bust left / right / low, live doorbell footage, the
  radio insert), red / blue split rows and flashing markers ('PAUSE TOO LONG', 'BREATH', 'COUGH').
- B_bust: framings rotate (BUST_FRAMES, no (who, bg, framing) repeat within 60 s), 3/4 views with the head back to the
  lens, the camera sits off the face, the crown never leaves the frame (_head_guard; ecu=True for eye close-ups).
- Tags may be pinned to a subject point: (t, text, dx, dy, style, hold, dict(at=(x, y) | f(t), d=depth)) -> projected
  through the shot camera with a leader line (SCAR, RING, WRONG / CORRECT HAND).
- B_hands uses characters.draw_hands_lap (ring on the ring finger, thread, rubbing thumb); the car palm is
  characters.draw_palm_on_glass beside the face; B_curtain (mum pulls her curtain: the figure outside in the strobe);
  B_black (hard cut to black after the final static hit).
- The phone call (537-681 s) is ~60 shots of varied coverage: phone UI full screen with a live waveform, mum's room
  wide / medium / over her shoulder walking to her door, her street with the two men coming up her path, the knock seen
  at her door, the curtain insert, your hall pacing hand-held, eye close-ups, the double's face intercut; one scream.
- Climax: a second grade ramp over the last minute (red share >= 3 %, saturation +50 %, luma -15 %); the ending is the
  double walking up mum's path in red, the knock at your door, the peephole grin, the call failing, his grin in the
  car, the double leaning into your doorbell lens, a static hit and black on 'home'.
- Rule cards: icon, live background (the officer swaying behind the blur, the light bar), push camera, long cards cut
  after ~4.5 s into an illustration shot. Header: hidden on doorbell shots, clock shared with the doorbell HUD.
"""
import bisect, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *                                                    # noqa: F401,F403
from engine import hud as H
from engine.core import DW, DH, clamp, lerp, ease_in_out, ease_out_cubic, noise1, hash01
from engine.lens import Lens
import characters as CH
import sets as ST

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
CUES_DIR = os.path.join(S, 'pov2', 'cues')
WORDS = os.path.join(S, 'pov2', 'align', 'asr_cache.json')
FPS = 60
LEAD = 0.10                      # cut a moment before the word
GLOBAL_PPUSH = 0.02              # uniform post push (per second) added to every non-lens shot
WHO = {'O': 'officer', 'D': 'double', 'M': 'mum', 'F': 'officer2', 'Y': 'you'}
H._hand = CH.hud_phone_hand      # the character agent's hand on the phone UI
DOORBELL = get_lens('doorbell')
DOORBELL_IR = get_lens('doorbell_ir')

RULES = {1: "Keep your *identification* on *your side* of the door.",
         2: "If the officer asks you to *repeat* something, *don't give him a second recording*.",
         3: "If you hear someone you love on the *police radio*, *don't speak* to them through it.",
         4: "If he shows you a *complaint*, read the *name* of the person who made it.",
         5: "*Don't correct* anything the other man gets *wrong*.",
         6: "Whatever they promise, *don't step outside* voluntarily.",
         7: "When they leave, keep your door *locked* and *call your family* again."}


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
def porch_light(t, police=True, base='#9fb6ff', key=-0.15, k=1.0):
    """Rim light for characters on the porch: cool moon rim, swapped for red / blue when the light bar sweeps."""
    if police:
        r, b = ST.lightbar(t)
        if max(r, b) > 0.25:
            return dict(rim='#ff3040' if r >= b else '#4a6cff', rim_a=int(60 + 110 * max(r, b) * k), side=-1 if r >= b else 1, key=key)
    return dict(rim=base, rim_a=70, side=1, key=key)


def warm_light(t): return dict(rim='#ffcf9a', rim_a=60, side=-1, key=0.15)


def room_light(t): return dict(rim='#8fa6d8', rim_a=55, side=1, key=0.0)


# ==================================================================================================== the film
class Film:
    def __init__(self, tl):
        self.tl = tl
        self.L = tl['lines']
        self.duration = float(tl.get('duration_en', 697.5)) + 2.0
        self.words = []
        if os.path.exists(WORDS):
            try:
                self.words = [(w.strip().lower().strip('.,?!;:"“”'), float(t)) for w, t in json.load(open(WORDS))['en_words']]
            except Exception:
                self.words = []
        self._wt = [t for _, t in self.words]
        self.shots = []
        self.globals = []                    # extra global cues (beds, music)
        self.countdown = None                # (t0, step, n): ten-to-zero numerals over the shots
        plan(self)
        self.shots.sort(key=lambda s: s.t0)
        for k, s in enumerate(self.shots):
            s.idx = k
            s.t1 = self.shots[k + 1].t0 if k + 1 < len(self.shots) else self.duration
        self._starts = [s.t0 for s in self.shots]
        assign_bust_framings(self)
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

    # ---------------------------------------------------------------- shot lookup / build
    def shot_at(self, t):
        k = max(0, bisect.bisect_right(self._starts, t) - 1)
        return self.shots[k]

    def _build(self, sh):
        if sh.idx in self._built: return self._built[sh.idx]
        sh.sfx, sh.music, sh.actors = [], [], []
        spec = BUILDERS[sh.kind](self, sh)
        shot_common(self, sh, spec)
        # v2.1: a gentle uniform push on the finished image on top of every dolly push (the dolly barely zooms the far
        # layers, so measured zoom sat at ~1 %/s; the references push 2-3 %/s). Lens shots, pulls and cards are left alone.
        mv = (sh.p.get('cam') or {}).get('mv', 'push')
        if (spec.lens is None and isinstance(spec.cam, Cam) and not spec.cam.posts and mv != 'pull'
                and sh.kind not in ('rule', 'black') and not sh.p.get('no_ppush')):
            spec.cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + GLOBAL_PPUSH) ** max(0.3, sh.d), ease='push')
        if len(self._built) > 3: self._built.clear()
        self._built[sh.idx] = spec
        return spec

    # ---------------------------------------------------------------- frame
    def frame(self, t, i):
        sh = self.shot_at(t)
        spec = self._build(sh)
        fx = spec.fx(t) if spec.fx else {}
        fx = dict(fx)
        glob_fx(self, sh, t, fx)
        cs = spec.cam.at(t) if spec.cam is not None else None

        def hud_all(cv, tt):
            if spec.hud: spec.hud(cv, tt)
            self.overlay(cv, tt, sh)
        return render_frame(spec.layers, cs, t, i, focus=spec.focus, dof=spec.dof, lens=spec.lens, grade=spec.grade, post=fx, hud=hud_all)

    # ---------------------------------------------------------------- captions + header (v1 logic)
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
        # one clock for the whole film: the doorbell HUD's running timestamp (12:35:37 AM + t) drives the header corner too;
        # on doorbell shots the doorbell HUD owns the top corners, so the header is left out there
        if sh.kind == 'black': return
        if sh.kind != 'door':
            hh, mm, _ = (lambda tot: ((tot // 3600) % 24, (tot // 60) % 60, tot % 60))(int(35 * 60 + 37 + t))
            H.header(cv, self.header_text(t), '%d:%02d AM' % ((hh % 12) or 12, mm))
        cd = self.countdown
        if cd and cd[0] <= t < cd[0] + cd[1] * (cd[2] + 1) and sh.kind != 'rule':
            k = int((t - cd[0]) / cd[1]); n = cd[2] - k; u = t - cd[0] - k * cd[1]
            sc = 1.0 + 0.35 * max(0.0, 1.0 - u / 0.1)
            text(cv, '%d' % n, 1790, 205, 900, 120 * sc, '#ffffff' if n > 3 else '#e3262e', 235, 0.0, 'right', 0.9)
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
        sfx.sort(key=lambda e: (e['t'], e['name']))
        mus.sort(key=lambda e: e['t'])
        music = {'duration': round(self.duration, 2), 'intensity': intensity_curve(self), 'events': mus}
        if write:
            out_dir = out_dir or CUES_DIR
            os.makedirs(out_dir, exist_ok=True)
            json.dump(sfx, open(os.path.join(out_dir, 'sfx_cues.json'), 'w'), indent=0)
            json.dump(music, open(os.path.join(out_dir, 'music_cues.json'), 'w'), indent=0)
        return sfx, music


# ==================================================================================================== camera
def push_rate(t):
    """Push-in speed grows toward the climaxes (reference median 2.3-2.8 %/s, p90 6-8 %/s)."""
    if t > 600: return 0.034
    if t > 455: return 0.03
    if t > 300: return 0.027
    return 0.024


def mkcam(sh, mv='push', x=960, y=540, z=1.0, rate=None, dx=0.0, dy=0.0, shake=1.6, roll=0.0, x1=None, y1=None, z1=None,
          snap=None, hit=None, opt=None, d=None):
    """opt: constant optical zoom (no parallax; frames far layers); d: x, y (and x1, y1) are points on a layer at depth d."""
    t0, t1 = sh.t0, sh.t1
    if d is not None:
        x, y = 960 + d * (x - 960), 540 + d * (y - 540)
        if x1 is not None: x1 = 960 + d * (x1 - 960)
        if y1 is not None: y1 = 540 + d * (y1 - 540)
    r = rate if rate is not None else push_rate(t0)
    if mv == 'push':
        c = push_in(t0, t1, x, y, z, rate=r, drift=(dx, dy), roll=roll, shake=shake, seed=sh.idx)
    elif mv == 'fast':
        c = push_in(t0, t1, x, y, z, rate=r * 2.6, drift=(dx, dy), shake=shake + 0.8, seed=sh.idx)
    elif mv == 'creep':
        c = push_in(t0, t1, x, y, z, rate=r * 0.5, drift=(dx, dy), shake=shake * 0.6, seed=sh.idx)
    elif mv == 'pull':
        c = pull_out(t0, t1, x, y, z * (1 + max(0.06, r * 2.2 * sh.d)), z, shake=shake, seed=sh.idx)
    elif mv == 'drift':
        c = drift(t0, t1, x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2, zoom=z, z1=z * (1 + r * 0.5 * sh.d), shake=shake, seed=sh.idx)
    elif mv == 'move':                        # explicit start / end framing
        c = Cam([(t0, x, y, z, roll), (t1, x1 if x1 is not None else x, y1 if y1 is not None else y, z1 or z * (1 + r * sh.d), roll, 'push')],
                shake=shake, seed=sh.idx)
    elif mv == 'hand':                        # nervous handheld + slow push
        c = push_in(t0, t1, x, y, z, rate=r * 0.8, drift=(dx, dy), shake=4.5, seed=sh.idx)
        c.shake_hz = 0.9
    else:
        c = hold(x, y, z, shake=shake, seed=sh.idx)
    if opt: c.snap(t0 - 30.0, opt, 0.001)
    if snap: c.snap(snap[0], snap[1] if len(snap) > 1 else 1.25, 0.1)
    if hit:
        for h in (hit if isinstance(hit, (list, tuple)) else [hit]): c.hit(h, 7.0)
    return c


def cam_from(F, sh, d):
    """d: dict(mv=..., x=..., ...) or None -> default push."""
    d = dict(d or {})
    return mkcam(sh, **d)


# ==================================================================================================== actors
def acting(F, sh, who, act=None, seed=0, height=700.0, expr=None, talk=True, blink=None):
    a = CH.Acting(who, seed=seed + sh.idx * 3, height=height, expr=expr or 'neutral', blink=blink)
    if act: act(a, sh)
    escalate(a, sh, who)
    if talk:
        codes = [c for c, w in WHO.items() if w == who]
        iv = []
        for l in F.lines_in(sh.t0, sh.t1, codes):
            if l['who'] == 'Y' and l.get('fx'): continue          # your recorded voice on the radio: no mouth
            iv.append((l['t'], l['end'], l['en']))
        if iv: a.talk(iv)
    sh.actors.append(a)
    return a


def _walk_legs(a, legs, surface='porch'):
    """Walk cycle for one or more walks per actor: legs [(t0, t1, units, facing)] (units = Acting.walk's design distance).
    One clip drives walk_amt / walk_ph / turn (Acting.walk handles a single walk per actor cleanly: a later walk resets the
    phase of an earlier one); heel-strike footstep events at every half cycle."""
    info = []
    for (t0, t1, units, face) in legs:
        n = max(2, int(round((t1 - t0) * 1.9)))           # a real walking cadence (~1.9 steps/s), not screen distance
        cyc = n / 2.0
        info.append((t0, t1, cyc, face))
        for k in range(1, n + 1):
            a._ev(t0 + (t1 - t0) * (k - 0.5) / n, 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch', -4.0,
                  pan=0.0, n=1, foot='L' if k % 2 else 'R')

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


def escalate(a, sh, who):
    """v2.1 global acting arc: from 450 s the creepy cast twitch / jerk every 1.5-2.5 s (on top of the character module's
    idle life), the protagonist trembles in every shot from 300 s (harder after 450 s), mum trembles once police are at
    her door (584 s+). Shots that already layer creep() / tremble() keep their own."""
    if sh.kind in ('rule',): return
    if who in ('officer', 'double', 'officer2') and sh.t0 >= 450.0 and sh.d > 1.2:
        ts, k = [], sh.t0 + 0.5 + 0.8 * float(hash01(sh.idx, 71))
        while k < sh.t1 - 0.25:
            ts.append(k); k += 1.5 + float(hash01(int(k * 10), 72))
        if ts:
            a.twitch(ts[::2], 0.8 if getattr(a, '_creep', False) else 1.0)
            for tj in ts[1::2]: a.jerk(tj, 0.5)
    elif who == 'you' and sh.t0 >= 300.0 and not getattr(a, '_trem', False):
        tremble(0.45 if sh.t0 < 450 else 0.8)(a, sh)
    elif who == 'mum' and sh.t0 >= 584.0 and not getattr(a, '_trem', False):
        tremble(0.4)(a, sh)


def figure(F, sh, who, x, y, depth, height, act=None, seed=0, expr=None, light=None, aim=None, lean=False, k=0.55, name=None,
           path=None, detail=None, talk=True, alpha=1.0, facing=0.0):
    """Full-body character layer. path = (t0, t1, [(x, y, depth, height), ...]) walks along anchors with a real walk cycle.
    v2.1: the walker's LAYER DEPTH follows the path (it sorts against the railing, posts and porch correctly and grows the
    way a person walking up to a doorbell camera does, fisheye bulge included); lean=True still works at the end of a
    walk (depth x (1 - k * approach)). facing: body yaw while walking (0 = toward the lens, +-1 = sideways)."""
    a = acting(F, sh, who, act, seed, height, expr, talk)
    m = _Memo(a)
    lt = light
    if path is not None:
        legs = [path] if (len(path) == 3 and not isinstance(path[0], (list, tuple))) else list(path)
        L_ = []                                            # (t0, t1, pts, seg lengths, total, facing)
        for lg in legs:
            q0, q1, pts_ = lg[0], lg[1], [tuple(q) for q in lg[2]]
            fc = lg[3] if len(lg) > 3 else facing
            sg = [math.hypot(pts_[j + 1][0] - pts_[j][0], pts_[j + 1][1] - pts_[j][1]) + abs(pts_[j + 1][3] - pts_[j][3]) * 1.5
                  for j in range(len(pts_) - 1)]
            L_.append((q0, q1, pts_, sg, sum(sg) or 1.0, fc))
        _walk_legs(a, [(q0, q1, tot_ * 1.4 / (a.height / 1000.0), fc) for (q0, q1, _, _, tot_, fc) in L_])
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
        R = pts[-1][2]                                     # reference depth: the end of the walk

        def dfun(t):
            d = pos(t)[2]
            return d * (1.0 - k * clamp(m(t).approach)) if lean else d

        def local(t):
            px, py, pd, ph = pos(t); s = pd / R          # layer-local coords that land on (px, py) at depth pd
            return 960 + (px - 960) * s, 540 + (py - 540) * s, ph * s

        def draw(pen, t):
            P = m(t).copy(); P.dx = 0.0
            lx, ly, lh = local(t)
            CH.draw(pen, who, lx, ly, lh, P, light=lt(t) if callable(lt) else lt, t=t, detail=detail, aim=aim)
        lay = Layer(dfun, draw, name or who, ref_depth=R, alpha=alpha)
        lay._pos = pos

        def box(t):
            lx, ly, lh = local(t)
            return (lx - lh * 0.25, ly - lh * 1.05, lh * 0.5, lh * 1.07)
        lay._box = box
        return lay, a
    dfun = a.depth(depth, k) if lean else depth

    def draw(pen, t):
        CH.draw(pen, who, x, y, height, m(t), light=lt(t) if callable(lt) else lt, t=t, aim=aim, detail=detail)
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
    a = sp.anchors[name]; return (a.x, a.y, a.depth, a.height)


def people(F, sh, sp, ppl, light):
    """ppl: list of dicts {who, at (anchor name or tuple), act, lean, aim, path=(t0, t1, [anchor names]), expr, seed}."""
    L, A = [], []
    for k, q in enumerate(ppl or []):
        who = q['who']
        at = q.get('at') or 'officer'
        if q.get('path') and (not isinstance(at, str) or at not in sp.anchors):    # walkers start on their path
            pq = q['path']; first = (pq if not isinstance(pq[0], (list, tuple)) else pq[0])[2][0]
            at = first
        x, y, d, h = anc(sp, at) if isinstance(at, str) else at
        path = None
        if q.get('path'):
            pq = q['path']
            legs = [pq] if not isinstance(pq[0], (list, tuple)) else pq
            path = [tuple([lg[0], lg[1], [anc(sp, n) if isinstance(n, str) else n for n in lg[2]]] + list(lg[3:])) for lg in legs]
        lay, a = figure(F, sh, who, x, y, d, h, q.get('act'), seed=k * 11 + q.get('seed', 0), expr=q.get('expr'),
                        light=q.get('light', light), aim=q.get('aim'), lean=q.get('lean', False), k=q.get('k', 0.55),
                        name='p%d_%s' % (k, who), path=path, detail=q.get('detail'), talk=q.get('talk', True),
                        facing=q.get('facing', 0.0), alpha=q.get('alpha', 1.0))
        L.append(lay); A.append((q, lay, a))
    return L, A


def dimmed(sp, k, keep=()):
    for l in sp:
        if l.name not in keep and not callable(l.dim): l.dim = max(l.dim if isinstance(l.dim, float) else 0.0, k)
    return sp


# ==================================================================================================== builders
def _police(p, default=True):
    pol = p.get('police', default)
    if pol is True: pol = dict(mode='sweep')
    return pol


def B_street(F, sh):
    p = sh.p
    pol = _police(p)
    sp = ST.street_wide(car=p.get('car', True), police=pol, drive=p.get('drive'), doors=p.get('doors'),
                        figures=p.get('figures', ('driver', 'back')), bedroom_lit=p.get('bedroom', 0.0), living_lit=p.get('living', 1.0),
                        mist=p.get('mist', True), head=p.get('head', False))
    L, A = people(F, sh, sp, p.get('ppl'), lambda t: porch_light(t, bool(pol), k=0.6))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    return Spec(sp.add(*L), cam, None, p.get('grade', 'night_blue'), 1.1, 0.0,
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def _doorbell_hud(F, sh, cam, lens, A, p):
    ir = lens is DOORBELL_IR
    tracked = [lay for (q, lay, a) in A if q.get('track', True)]

    def hud(cv, t):
        box = None
        if tracked and p.get('box', True):
            lay = tracked[0]
            try:
                box = project_box(lay._box(t), lay.depth_at(t), cam.at(t), lens, lay.ref_depth)
                x0, y0, w0, h0 = box
                x1, y1 = min(DW - 30, x0 + w0), min(DH - 60, y0 + h0); x0, y0 = max(30, x0), max(110, y0)
                box = (x0, y0, x1 - x0, y1 - y0) if (x1 - x0 > 40 and y1 - y0 > 40) else None
            except Exception:
                box = None
        H.doorbell_hud(cv, t, name=p.get('cam_name', 'FRONT DOOR'), clock=(0, 35, 37), motion=box, ir=ir,
                       talk=p.get('talk_btn', False))
        if p.get('hud'): p['hud'](cv, t)
    return hud


def B_door(F, sh):
    """Doorbell camera: the camera is FIXED (a real doorbell); motion comes from the people and a post-push into the
    footage (zooming the app view), plus the lens bulging anyone who comes close."""
    p = sh.p
    pol = _police(p)
    sp = ST.porch_doorbell(car=p.get('car', True), police=pol, drive_in=p.get('drive_in'), doors=p.get('doors'),
                           figures=p.get('figures', ('driver', 'back')), ir=p.get('ir', False), mist=p.get('mist', True))
    ppl = p.get('ppl', [dict(who='officer', at='officer')])
    for q in ppl:
        q.setdefault('aim', (960, 470))
        q['_xyzh'] = anc(sp, q['at']) if isinstance(q.get('at'), str) else q.get('at', anc(sp, 'officer'))
    L, A = people(F, sh, sp, ppl, lambda t: porch_light(t, bool(pol), k=0.8))
    lens = DOORBELL_IR if p.get('ir') else DOORBELL
    z1 = p.get('z1', 1.0 + push_rate(sh.t0) * 1.9 * sh.d)
    px, py = p.get('px', 0.0), p.get('py', -40.0)
    cam = Cam([(sh.t0, 960, 540, 1.0)], shake=0.0, seed=sh.idx).post_push(sh.t0, sh.t1, p.get('z0', 1.0), z1, x=px, y=py)
    if p.get('hit'):
        for h in p['hit']: cam.hit(h, 5.0)
    hud = _doorbell_hud(F, sh, cam, lens, A, p)
    return Spec(sp.add(*L), cam, lens, 'ir_night' if p.get('ir') else 'doorbell_night', 1.0, 0.0,
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=hud)


def B_peep(F, sh):
    """Peephole. v2.1: the camera pushes at 4.5 %/s by default, and every standing subject who is not already walking or
    leaning eases toward the lens over the shot (lean_in -> the fisheye grows the head from ~45 % toward ~70 % of the
    disc, VISUAL_SPEC d); p['approach']=False keeps a subject at its distance."""
    p = sh.p
    pol = _police(p)
    sp = ST.porch_peephole(car=p.get('car', True), police=pol, drive_in=p.get('drive_in'), doors=p.get('doors'),
                           figures=p.get('figures', ('driver', 'back')), mist=p.get('mist', True))
    ppl = [dict(q) for q in p.get('ppl', [dict(who='officer', at='officer')])]
    for q in ppl:
        q.setdefault('aim', (960, 520))
        if p.get('approach', True) and not q.get('path') and not q.get('lean') and q.get('track', True) is not False:
            amt = 0.4 if q.get('at') == 'officer_close' else 0.7
            q['act'] = _A(q.get('act'), lambda a, s, amt=amt: a.lean_in(s.t0 - 0.15, max(1.2, (s.t1 - s.t0) * 0.9), amount=amt))
            q['lean'] = True
    L, A = people(F, sh, sp, ppl, lambda t: porch_light(t, bool(pol), base='#ffcf9a', key=0.1, k=0.7))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=520)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = max(0.045, push_rate(sh.t0) * 1.5)
    cd['z'] = cd.get('z', 1.0) * p.get('zk', 1.14)
    cam = cam_from(F, sh, cd)
    return Spec(sp.add(*L), cam, 'peephole', p.get('grade', 'porch_warm'), 1.0, 0.0,
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def _bg(F, sh, name, p):
    """Background set for close-ups (drawn at its own depths, blurred by DOF and darkened 30 %)."""
    pol = p.get('police', name not in ('mumroom',) or sh.t0 > 588.0)
    if pol is True: pol = dict(mode='strobe') if name == 'mumext' else dict(mode='sweep')
    if name == 'porch':
        sp = ST.porch_peephole(car=p.get('car', True), police=pol, mist=True)
        light = lambda t: porch_light(t, bool(pol), base='#ffcf9a', key=-0.05)
    elif name == 'hall':
        sp = ST.hallway(police=pol, lamp=p.get('lamp', 1.0), coats=p.get('coats', True)).without('near_frame')
        light = lambda t: dict(rim='#ff3040', rim_a=90, side=-1, key=-0.1) if pol and ST.lightbar(t)[0] > 0.6 else room_light(t)
    elif name == 'mumroom':
        sp = ST.mother_room(police=pol, phone_ring=p.get('ring'))
        light = warm_light
    elif name == 'mumext':
        sp = ST.mother_exterior(police=pol, car=True)
        light = lambda t: porch_light(t, bool(pol), key=-0.1)
    elif name == 'kitchen':
        sp = ST.kitchen(police=pol).without('table')
        light = room_light
    elif name == 'car':
        sp = ST.car_backseat_window(police=pol)
        light = lambda t: porch_light(t, bool(pol), key=-0.2)
    else:
        sp = ST.street_wide(police=pol)
        light = lambda t: porch_light(t, bool(pol))
    return dimmed(sp, p.get('bg_dim', 0.3)), light


# v2.1 bust framings per character: (cx, cy, scale, body turn, head turn relative to the body). Rotated so the same
# (who, bg, framing) never repeats within 60 s (assign_bust_framings); the creepy ones keep the face toward the lens.
BUST_FRAMES = {
    'officer': [(960, 560, 1.0, 0.0, 0.0), (760, 590, 0.9, 0.38, -0.3), (1180, 570, 1.08, -0.4, 0.3), (960, 610, 0.8, 0.0, 0.0),
                (700, 560, 1.12, 0.28, -0.22), (1220, 610, 0.86, -0.55, 0.42)],
    'double': [(960, 570, 1.0, 0.0, 0.0), (1180, 600, 0.92, -0.4, 0.32), (740, 580, 1.06, 0.4, -0.3), (960, 620, 0.82, 0.0, 0.0),
               (1220, 560, 1.1, -0.3, 0.22)],
    'officer2': [(960, 570, 1.0, 0.0, 0.0), (760, 590, 0.9, 0.38, -0.3), (1180, 600, 0.88, -0.45, 0.35)],
    'you': [(960, 580, 1.0, 0.0, 0.0), (1180, 610, 0.9, -0.55, 0.0), (720, 580, 1.08, 0.5, -0.2), (960, 640, 0.78, 0.0, 0.0),
            (1240, 560, 1.15, -0.35, 0.1), (680, 620, 0.88, 0.75, -0.15)],
    'mum': [(960, 580, 1.0, 0.0, 0.0), (720, 600, 0.9, 0.55, 0.0), (1200, 590, 1.06, -0.45, 0.1), (960, 650, 0.78, 0.0, 0.0),
            (680, 560, 1.14, 0.35, -0.1), (1240, 620, 0.86, -0.75, 0.15)],
}


def assign_bust_framings(F):
    """Deterministic framing rotation over the bust shots (time order): a framing is reused for the same (who, bg) only
    after 60 s. Shots with an explicit cx keep their own framing."""
    last, ctr = {}, {}
    for sh in F.shots:
        if sh.kind != 'bust' or 'cx' in sh.p: continue
        who = sh.p.get('who', 'officer'); bg = sh.p.get('bg', 'porch')
        opts = BUST_FRAMES.get(who, BUST_FRAMES['officer'])
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
    """Face close-up over a blurred, darkened set. v2.1: framings rotate (BUST_FRAMES: off-centre thirds, 3/4 views
    with the head back toward the lens, wider and tighter scales), the camera sits off the face so the composition is not
    always centred, and the crown never leaves the frame (_head_guard) unless p['ecu'] asks for an eye close-up."""
    p = sh.p
    sp, light = _bg(F, sh, p.get('bg', 'porch'), p)
    who = p.get('who', 'officer')
    fr = p.get('_frame')
    cx = p.get('cx', fr[0] if fr else 960)
    cy = p.get('cy', fr[1] if fr else 560)
    sc = p.get('scale', fr[2] if fr else 1.0)
    view = None
    if fr and (fr[3] or fr[4]) and not p.get('no_view'):
        view = lambda a, s, v=(fr[3], fr[4]): a.set(s.t0 - 3, None, 0.1, turn=v[0], h_turn=v[1])
    lay, a = bust(F, sh, who, cx, cy, sc, _A(view, p.get('act')), expr=p.get('expr'), light=p.get('light', light))
    extra = []
    if p.get('prop'):                                        # a prop held up in front of the face (depth 0.8)
        nm, kw = p['prop']
        extra.append(Layer(0.8, lambda pen, t: ST.draw_prop(pen, nm, t=t, cache=True, **kw), 'prop', blur=0))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=cy - 20)))
    if fr and 'x' in cd and cd['x'] == 960: cd['x'] = 960 + (cx - 960) * 0.3     # keep the off-centre composition
    if not p.get('ecu'): cd = _head_guard(cd, cy - 330 * sc, sh.d)
    cam = cam_from(F, sh, cd)
    grade = p.get('grade', 'face_close')
    return Spec(sp.add(lay, *extra), cam, None, grade, 1.0, p.get('dof', 6.75),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_car(F, sh):
    """Back-seat window of the patrol car: the man (the double) seated, lit by the light bar."""
    p = sh.p
    pol = _police(p)
    sp = ST.car_backseat_window(police=pol, fog=p.get('fog'))
    lay, a = bust(F, sh, 'double', p.get('cx', 985), p.get('cy', 455), p.get('scale', 0.4), p.get('act'), seed=5, expr=p.get('expr'),
                  light=lambda t: porch_light(t, bool(pol), key=-0.25, k=0.9), depth=1.2)
    lay.blur = None
    extra = []
    if p.get('hand'):                                         # his palm pressed on the glass beside his face (depth 0.99)
        hx, hy, hs = p['hand']
        ht0 = p.get('hand_t', sh.t0)

        def palm(pen, t):
            u = clamp((t - ht0) / 0.35)
            y = hy - 40 * (1 - ease_out_cubic(u)) + 6.0 * clamp((t - ht0 - 0.4) / 3.0)      # lands, then slides down 6 px
            if hasattr(CH, 'draw_palm_on_glass'):                                             # 5 spread fingers, pressed pads
                CH.draw_palm_on_glass(pen, 'double', hx, y, hs, press=u, t=t, angle=4.0, side=-1, halo=u)
            else:
                pen.radial(None, hx, y - hs * 0.45, hs * 0.85, [(0, '#c9d6f0', 70 * u), (0.6, '#c9d6f0', 30 * u), (1, '#c9d6f0', 0)], sy=1.15, clip=False)
                ST.draw_hand(pen, hx, y, hs / 520.0, 4.0, 'flat', CH.CAST['double']['skin'], '#6f7177', -1)
        extra.append(Layer(0.99, palm, 'palm', blur=0, alpha=lambda t: 0.92 * clamp((t - ht0) / 0.2)))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=980, y=470)))
    return Spec(sp.add(lay, *extra), cam, None, p.get('grade', 'night_blue'), 1.2, p.get('dof', 2.0),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_hall(F, sh):
    p = sh.p
    pol = p.get('police', True)
    sp = ST.hallway(police=pol, lamp=p.get('lamp', 1.0), feet=p.get('feet'), chain=p.get('chain', 0.0),
                    slot_open=p.get('slot'), coats=p.get('coats', True), sweep=p.get('sweep'), flick=p.get('flick')).without(*p.get('without', ()))
    L = []
    if p.get('you', True):
        q = dict(who='you', at=p.get('at', 'you'), act=p.get('act'), expr=p.get('expr', 'nervous'),
                 light=lambda t: dict(rim='#ff3040', rim_a=110, side=-1, key=-0.2) if (pol and ST.lightbar(t)[0] > 0.55) else room_light(t))
        if p.get('you_at'): q['at'] = p['you_at']
        L, _ = people(F, sh, sp, [q], None)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    return Spec(sp.add(*L), cam, p.get('lens', 'lens'), p.get('grade', 'interior_dim'), p.get('focus', 2.0), p.get('dof', 2.5),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def _post_push(cam, sh, rate):
    """Uniform 2D push on the finished image (all depths alike) on top of the dolly: inserts and UI read as moving."""
    if rate: cam.post_push(sh.t0, sh.t1, 1.0, (1.0 + rate) ** max(0.3, sh.d), ease='push')
    return cam


def hud_push(sh, rate=0.03, cx=960, cy=540, dx=0.0, dy=0.0, shake=0.0, hz=0.9):
    """Canvas transform for HUD-drawn shots (phone UI, waveform panels): the graphic itself pushes in at `rate`/s about
    (cx, cy), drifts by (dx, dy) over the shot and shakes like a hand-held phone. Returns f(cv, t) -> restore()."""
    def apply(cv, t):
        u = clamp((t - sh.t0) / max(0.1, sh.d))
        k = (1.0 + rate) ** max(0.0, t - sh.t0 + 0.15)
        ox = dx * (0.2 + 0.8 * u) + shake * noise1(t * hz, sh.idx * 7 + 1)
        oy = dy * (0.2 + 0.8 * u) + shake * 0.8 * noise1(t * hz * 1.13, sh.idx * 7 + 2)
        cv.save(); cv.translate(cx + ox, cy + oy); cv.rotate(0.35 * shake * noise1(t * hz * 0.7, sh.idx * 7 + 3) if shake else 0.0)
        cv.scale(k, k); cv.translate(-cx, -cy)
        return cv.restore
    return apply


def B_ins(F, sh):
    """Prop insert. v2.1 default: push at 4.5 %/s (dolly) plus a uniform post push, so the prop itself visibly grows."""
    p = sh.p
    sp = ST.insert(p['name'], t0=sh.t0, prop_kw=p.get('kw'), motion=p.get('motion'), hand=p.get('hand'), police=p.get('police', True))
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = 0.045
    cam = _post_push(cam_from(F, sh, cd), sh, p.get('ppush', 0.02))
    return Spec(sp, cam, None, p.get('grade', sp.grade or 'face_close'), sp.focus, sp.dof,
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def _ring_point(x, y, sc, rot, side, frac=0.3):
    """Design position of the ring on the ring finger of sets.draw_hand('flat') placed at (x, y, sc, rot, side)."""
    fx, fy, ang, ln = 20.0, -50.0, 3.0, 155.0
    lx = fx + math.sin(math.radians(ang)) * frac * ln; ly = fy - math.cos(math.radians(ang)) * frac * ln
    lx *= sc * side; ly *= sc
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return x + c * lx - s_ * ly, y + s_ * lx + c * ly


def _draw_ring(pen, x, y, sc, rot, side, t, glint_t=0.0):
    """A gold band ON the ring finger (same transform as the hand), back half hidden, a moving glint."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc * side, sc); cv.translate(20, -50); cv.rotate(3)
    yb = -0.3 * 155
    pen.shape(rrect(-21, yb - 9, 42, 18, 8), '#d8b25a', 5)
    pen.fill(rrect(-17, yb - 6, 34, 5, 2.5), '#fff4cf', 200)
    g = (t * 0.7 + glint_t) % 1.0
    pen.fill(oval(-14 + 28 * g, yb - 3, 4.5), '#ffffff', 230 * math.sin(g * math.pi))
    cv.restore()


LAP_SIZE = 330.0


def B_hands(F, sh):
    """Close-up of the hands in a lap (the double's grey coat / your hoodie), seen from above: two hands with real fingers
    folded over each other, the top hand's thumb rubbing (the nervous habit), the ring as a gold band ON the ring finger
    (ring > 0: the screen-right hand, <= 0: the screen-left hand), the loose thread hanging from the cuff inside the frame.
    Uses characters.draw_hands_lap when the character module provides it."""
    p = sh.p
    who = p.get('who', 'double')
    sp, light = _bg(F, sh, p.get('bg', 'car' if who == 'double' else 'hall'), p)
    rub = p.get('rub', True)
    coat = '#6f7177' if who == 'double' else '#34443f'
    trou = '#23252d' if who == 'double' else '#273049'
    skin = CH.CAST[who]['skin']
    ring = p.get('ring')
    HL = (690, 600, 0.95, 92.0, 1)            # screen-left hand: x, y, scale, rot (fingers to the right), side
    HR = (1235, 650, 0.95, -88.0, -1)         # screen-right hand (on top): fingers to the left

    def lap(pen, t):
        pen.linear(rect(-200, 200, 2320, 1100), 0, 200, 0, 1300, [trou, '#0c0d12'])
        pen.shape(rrect(250, 380, 700, 900, 160), trou, 8); pen.shape(rrect(970, 380, 700, 900, 160), trou, 8)
        pen.linear(rect(200, 330, 1520, 950), 0, 330, 0, 1300, [(0, '#000000', 30), (1, '#000000', 170)])
        pen.shape(poly([(-200, 150), (430, 260), (380, 1300), (-200, 1300)]), coat, 8)
        pen.shape(poly([(2120, 150), (1490, 260), (1540, 1300), (2120, 1300)]), coat, 8)
        pen.radial(None, 960, 300, 900, [(0, '#ffd9a0', 40), (1, '#ffd9a0', 0)], clip=False)
        pen.linear(rect(-200, 150, 2320, 300), 0, 150, 0, 450, [(0, '#000000', 200), (1, '#000000', 0)])

    def hands(pen, t):
        u = t - sh.t0
        r = math.sin(u * 4.2) if rub else 0.0
        if hasattr(CH, 'draw_hands_lap'):
            rs = None if ring is None else (1 if ring > 0 else -1)
            CH.draw_hands_lap(pen, who, 960, 600, LAP_SIZE, rub_phase=u * 4.6, ring_side=rs, t=t, thread=bool(p.get('thread')), rub=bool(rub))
            return
        x, y, sc, rot, sd = HL
        ST.draw_hand(pen, x, y, sc, rot, 'flat', skin, coat, sd, '#8b8d92' if p.get('thread') else None)
        if ring is not None and ring <= 0: _draw_ring(pen, x, y, sc, rot, sd, t)
        x, y, sc, rot, sd = HR
        x += 10 * r; rot += 4.0 * r                                   # the top hand rocks: the thumb rubs the knuckles
        ST.draw_hand(pen, x, y, sc, rot, 'flat', skin, coat, sd)
        if ring is not None and ring > 0: _draw_ring(pen, x, y, sc, rot, sd, t)
        if p.get('thread'):                                           # loose thread from the cuff, lit, inside the frame
            sw = 14 * math.sin(u * 2.3)
            pen.line(smooth([(420, 470), (430 + sw * 0.3, 560), (420 + sw * 0.7, 660), (432 + sw, 760)], False), 5, '#c9ccd2', 230)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=620, z=1.05, rate=0.045)))
    _post_push(cam, sh, 0.015)
    return Spec([Layer(1.05, lap, 'lap', blur=0, cache='film_lap2_' + who), Layer(1.0, hands, 'hands', blur=0)], cam, None, 'face_close', 1.0, 6.75,
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


_RING = {}


def ring_at(ring, who='double'):
    """Tag anchor (design point at depth 1) of the ring in B_hands: found by drawing the lap hands once off-screen at
    1/4 size and locating the gold band (follows characters.draw_hands_lap's layout); the fallback layout otherwise."""
    rs = 1 if ring > 0 else -1
    if not hasattr(CH, 'draw_hands_lap'):
        x, y, sc, rot, sd = (1235, 650, 0.95, -88.0, -1) if rs > 0 else (690, 600, 0.95, 92.0, 1)
        return _ring_point(x, y, sc, rot, sd)
    key = (who, rs)
    if key not in _RING:
        try:
            import cv2
            surf = skia.Surface(480, 270); cv = surf.getCanvas(); cv.clear(skia.ColorBLACK); cv.scale(0.25, 0.25)
            r_ = CH.draw_hands_lap(Pen(cv), who, 960, 600, LAP_SIZE, rub_phase=0.0, ring_side=rs, t=0.0)
            if isinstance(r_, dict) and r_.get('ring_xy'):
                _RING[key] = tuple(float(v) for v in r_['ring_xy']); return _RING[key]
            img = surf.makeImageSnapshot().toarray()[..., :3]                    # BGRA -> BGR
            hsv = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_BGR2HSV)
            m = (hsv[..., 0] >= 15) & (hsv[..., 0] <= 30) & (hsv[..., 1] > 110) & (hsv[..., 2] > 120)
            ys, xs = np.nonzero(m)
            _RING[key] = (float(xs.mean()) * 4 + 2, float(ys.mean()) * 4 + 2) if len(xs) > 3 else (960.0, 660.0)
        except Exception:
            _RING[key] = (960.0, 660.0)
    return _RING[key]


def B_kitchen(F, sh):
    p = sh.p
    sp = ST.kitchen(police=p.get('police', True), sweep=p.get('sweep')).without(*p.get('without', ()))
    L = []
    if p.get('ppl'):
        L, _ = people(F, sh, sp, p['ppl'], room_light)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=520)))
    return Spec(sp.add(*L), cam, None, 'interior_dim', p.get('focus', 1.2), p.get('dof', 3.0),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_living(F, sh):
    p = sh.p
    sp = ST.living_room_window(car=p.get('car', True), police=p.get('police', True), drive=p.get('drive'),
                               figures=p.get('figures', ('driver', 'back')), head=p.get('head', False))
    L = []
    if p.get('you', True):
        L, _ = people(F, sh, sp, [dict(who='you', at='you_window', act=p.get('act', lambda a, s: a.set(s.t0 - 1, None, 0.1, turn=2.0, h_turn=0.0)),
                                       light=room_light)], None)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=1000, y=560)))
    return Spec(sp.add(*L), cam, None, 'interior_dim', p.get('focus', 1.8), p.get('dof', 2.0),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_mumext(F, sh):
    p = sh.p
    pol = p.get('police', dict(mode='strobe'))
    sp = ST.mother_exterior(car=p.get('car', True), police=pol, drive=p.get('drive'), doors=p.get('doors'),
                            figures=p.get('figures', ('driver',)), window_lit=p.get('window', 1.0), silhouette=p.get('sil', False))
    L, _ = people(F, sh, sp, p.get('ppl'), lambda t: porch_light(t, bool(pol), k=0.6))
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=1000, y=640)))
    return Spec(sp.add(*L), cam, None, 'night_blue', 1.1, 0.0, fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_mumroom(F, sh):
    p = sh.p
    pol = p.get('police', dict(mode='strobe', strength=1.3) if sh.t0 > 588.0 else False)       # police at her door
    sp = ST.mother_room(police=pol, phone_ring=p.get('ring'), knock=p.get('knock'), door_glow=p.get('glow', 1.0)).without(*p.get('without', ()))
    L, _ = people(F, sh, sp, p.get('ppl'), warm_light)
    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=560)))
    return Spec(sp.add(*L), cam, None, p.get('grade', 'interior_dim'), p.get('focus', 1.6), p.get('dof', 2.5),
                fx=lambda t: dict(sp.fx(t), **p.get('post', {})), hud=p.get('hud'))


def B_phone(F, sh):
    """Your phone held up to the camera over the dark, blurred hallway (or mum's room). v2.1: the phone itself pushes in
    (~4 %/s), drifts and shakes in the hand (handheld 2.5), the room behind pushes too; p['full']=True fills ~70 % H."""
    p = sh.p
    sp, _ = _bg(F, sh, p.get('bg', 'hall'), p)
    states = p.get('states', [(sh.t0, 'calling')])
    cd = dict(p.get('cam', dict(mv='push', x=960, y=540)))
    if cd.get('mv', 'push') == 'push' and 'rate' not in cd: cd['rate'] = 0.045
    cd.setdefault('shake', 2.5)
    cam = cam_from(F, sh, cd)
    sc = p.get('scale', 1.0) * (1.25 if p.get('full') else 1.0)
    hp = hud_push(sh, p.get('prate', 0.04), p.get('x', 960), p.get('y', 560), p.get('pdx', -30 if sh.idx % 2 else 30), p.get('pdy', -12),
                  shake=p.get('pshake', 5.0))

    def hud(cv, t):
        st, ts = states[0][1], states[0][0]
        for (tt, s_) in states:
            if t >= tt: st, ts = s_, tt
        restore = hp(cv, t)
        H.phone(cv, st, t - ts, name=p.get('name', 'MUM'), x=p.get('x', 960), y=p.get('y', 560), scale=sc,
                timer=(t - ts) if st in ('connected',) else None)
        if p.get('wave'):                                     # live call waveform on the screen
            H.waveform(cv, p.get('x', 960) - 150 * sc, p.get('y', 560) + 70 * sc, 300 * sc, 60 * sc, t, p['wave'], 41 + sh.idx)
        restore()
        if p.get('hud'): p['hud'](cv, t)
    return Spec(sp, cam, None, 'phone_dark', 1.0, 9.0, fx=lambda t: dict(sp.fx(t), dim=0.25, **p.get('post', {})), hud=hud)


def B_curtain(F, sh):
    """Insert: mum's hand draws her curtain aside (the scrape of the rings) and the night outside her bay window shows a
    dark figure in the red / blue strobe. Layers: the street outside (depth 3, blurred), the window frame (1.05), lace and
    drape sliding (1.0), her hand gripping the drape edge (0.95). p['t_open'] = when the pull starts."""
    p = sh.p
    lf = ST._lights_fn(dict(mode='strobe', strength=1.2))
    t_open = p.get('t_open', sh.t0 + 0.3)

    def k_open(t): return ease_in_out(clamp((t - t_open) / 1.3))

    def outside(pen, t):
        pen.linear(rect(-500, -400, 2920, 1880), 0, -400, 0, 1480, ['#05070f', '#101c38', '#0a0c14'])
        r_, b_ = lf(t)
        pen.radial(None, 520, 760, 900, [(0, '#ff2a2a', 170 * r_), (1, '#ff2a2a', 0)], clip=False)
        pen.radial(None, 1420, 700, 900, [(0, '#3a5cff', 170 * b_), (1, '#3a5cff', 0)], clip=False)
        pen.fill(rect(-500, 820, 2920, 700), '#07080c')
        pen.fill(rrect(860, 330, 250, 760, 110), '#020306'); pen.fill(oval(985, 280, 82, 96), '#020306')       # the man outside
        pen.fill(oval(960, 270, 9), '#e8eef8', 90 + 120 * max(r_, b_)); pen.fill(oval(1012, 270, 9), '#e8eef8', 90 + 120 * max(r_, b_))

    def frame(pen, t):
        wood = '#3a2a24'
        pen.fill(minus(rect(-500, -400, 2920, 1880), rect(260, 90, 1400, 880)), '#241a18')
        pen.texture(minus(rect(-500, -400, 2920, 1880), rect(260, 90, 1400, 880)), 'plaster', 0.3, 'overlay', 1.0)
        pen.shape(minus(rect(230, 60, 1460, 940), rect(270, 100, 1380, 860)), wood, 6)
        pen.shape(rect(940, 100, 40, 860), wood, 5); pen.shape(rect(270, 510, 1380, 30), wood, 5)
        pen.fill(rect(150, 1000, 1620, 70), '#4a3a30'); pen.line(rect(150, 1000, 1620, 70), 5, LINE)
        pen.radial(None, 120, 1100, 1300, [(0, '#ffcf8f', 60), (1, '#ffcf8f', 0)], clip=False)            # her lamp behind

    def drapes(pen, t):
        k = k_open(t)
        lace_x = 260 + 1380 * 0.55 * k
        pen.cv.save(); pen.cv.clipRect(skia.Rect.MakeLTRB(lace_x, 80, 1680, 1000))
        pen.fill(rect(lace_x, 80, 1500, 920), '#e8e2d8', 120)
        for j in range(0, 22):
            pen.line(oval(lace_x + 40 + (j % 6) * 230, 160 + (j // 6) * 230, 60), 3, '#ffffff', 90)
        pen.cv.restore()
        dx = 1080 * k
        ST._curtain(pen, 120 + dx, 20, 760, 1040, t, -1, '#6a3a4a', 0.4, 11, folds=6)
        ST._curtain(pen, 1480, 20, 440, 1040, t + 2, 1, '#6a3a4a', 0.4, 13, folds=5)
        ST.draw_hand(pen, 860 + dx, 600, 0.9, -32.0, 'hold', CH.CAST['mum']['skin'], '#7a5a6a', 1)

    cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=980, y=560, z=1.05, rate=0.05, dx=60)))
    L = [Layer(3.2, outside, 'outside'), Layer(1.05, frame, 'frame', cache='film_curtain_frame', blur=0), Layer(1.0, drapes, 'drapes', blur=0)]
    return Spec(L, cam, None, 'interior_dim', 1.0, 6.75, fx=lambda t: dict(p.get('post', {})), hud=p.get('hud'))


def B_black(F, sh):
    """Hard cut to black (the ending): only the scare-cut static flash on its first frames."""
    return Spec([], None, None, 'neutral', 1.0, 0.0, fx=lambda t: dict(sh.p.get('post', {})), hud=None)


WAVE_LAYOUTS = ('officer_l', 'door', 'officer_r', 'radio', 'officer_low')


def B_wave(F, sh):
    """Radio waveform panel (reference 'waveform_panels'). v2.1: the panel is >= 60 % W, pushes in and drifts, and sits
    over a SHARP, lit background that varies shot to shot: 'officer_l' / 'officer_r' (officer bust in focus beside the
    panel, head tilted to his shoulder radio), 'officer_low' (bust above, panel low), 'door' (live doorbell footage of
    him at the door), 'radio' (the shoulder radio insert, in focus), or 'mumroom' etc. (any _bg set, blurred).
    p['layout'] picks one; bg='officer' rotates the officer layouts; no bg rotates all five."""
    p = sh.p
    bgk = p.get('bg')
    k_ = sum(1 for s_ in F.shots if s_.kind == 'wave' and s_.t0 < sh.t0)
    lay_ = p.get('layout') or (('officer_l', 'officer_r', 'officer_low')[k_ % 3] if bgk == 'officer' else
                              (WAVE_LAYOUTS[k_ % len(WAVE_LAYOUTS)] if bgk in (None, 'radio') else bgk))
    lens, grade, focus, dof, dim = None, 'phone_dark', 1.0, 6.75, 0.12
    pw = p.get('w', 1180)
    px0, py0 = 960 - pw / 2, p.get('y', 380)
    side = 1
    if lay_ in ('officer_l', 'officer_r', 'officer_low'):
        sp, light = _bg(F, sh, 'porch', p)
        side = 1 if lay_ == 'officer_l' else -1
        cx, cy, sc = (500, 600, 0.95) if lay_ == 'officer_l' else ((1420, 600, 0.95) if lay_ == 'officer_r' else (960, 360, 0.72))
        act = p.get('act', _A(stare(-1), lambda a, s: a.set(s.t0 + 0.2, None, 0.8, h_turn=0.22 * side, h_tilt=-9 * side, look_x=0.3 * side),
                              creep(5 * side, 3, None)))
        lay, a = bust(F, sh, 'officer', cx, cy, sc, act, light=light, talk=False)
        sp = sp.add(lay)
        if lay_ == 'officer_l': px0 = 1880 - pw
        elif lay_ == 'officer_r': px0 = 40
        else: py0 = 600
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960 + (cx - 960) * 0.25, y=540, rate=push_rate(sh.t0) * 1.6, dx=-60 * side, dy=-10)))
    elif lay_ == 'door':
        sp = ST.porch_doorbell(police=True)
        L, A = people(F, sh, sp, [dict(who='officer', at=DA(0.15, 1.0), act=_A(stare(-1), radio(0.2, max(1.0, sh.d - 0.6)), creep(6, 4, None)),
                                       aim=(960, 470))], lambda t: porch_light(t, True, k=0.8))
        sp = sp.add(*L); lens, grade, focus, dof, dim = DOORBELL, 'doorbell_night', 1.0, 0.0, 0.2
        cam = Cam([(sh.t0, 960, 540, 1.0)], shake=0.0, seed=sh.idx).post_push(sh.t0, sh.t1, 1.0, 1.0 + push_rate(sh.t0) * 2.4 * sh.d, x=0, y=-120)
        py0 = 640
    elif lay_ == 'radio':
        sp = ST.insert('radio', t0=sh.t0, police=True); focus, dof = sp.focus, sp.dof
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=600, rate=push_rate(sh.t0) * 1.6, dx=50)))
        _post_push(cam, sh, 0.02)
        py0 = 120
    else:
        sp, _ = _bg(F, sh, lay_, p); dim = 0.3
        cam = cam_from(F, sh, p.get('cam', dict(mv='push', x=960, y=540, rate=push_rate(sh.t0) * 1.6, dx=60)))
    rows = p.get('rows', [dict(label='PLAY 1', color='blue', seed=1)])
    hgt = p.get('h', 150 + 95 * len(rows))
    if py0 + hgt > 880: py0 = 880 - hgt
    t_app = p.get('appear', sh.t0)
    play = p.get('play')                     # (t0, t1) playhead sweep
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
        H.waveform_panel(cv, px0, py0, pw, hgt, p.get('title', 'SHOULDER RADIO'), rr, t, playhead=ph, appear=t - t_app)
        restore()
        if p.get('hud'): p['hud'](cv, t)
    return Spec(sp, cam, lens, grade, focus, dof, fx=lambda t: dict(sp.fx(t), dim=dim, **p.get('post', {})), hud=hud)


def _icon(n):
    """Small white line icons for the rule cards (reference: the card shows a small icon): f(pen, x, y, size, alpha)."""
    def f(pen, x, y, sz, a):
        k = sz / 120.0; w = 7 * k
        if n == 1:                                                          # ID card
            pen.line(rrect(x - 52 * k, y - 34 * k, 104 * k, 68 * k, 8 * k), w, '#ffffff', a)
            pen.line(oval(x - 24 * k, y - 4 * k, 12 * k), w * 0.8, '#ffffff', a)
            for j in range(3): pen.seg((x + 2 * k, y - 14 * k + j * 14 * k), (x + 38 * k, y - 14 * k + j * 14 * k), w * 0.7, '#ffffff', a)
        elif n == 2:                                                        # recording waveform
            for j, hgt in enumerate((14, 30, 46, 26, 40, 18, 10)):
                xx = x - 48 * k + j * 16 * k; pen.seg((xx, y - hgt * k), (xx, y + hgt * k), w, '#ffffff', a)
            pen.fill(oval(x + 50 * k, y - 40 * k, 9 * k), RED_ICON, a)
        elif n == 3:                                                        # shoulder radio
            pen.line(rrect(x - 30 * k, y - 36 * k, 60 * k, 80 * k, 10 * k), w, '#ffffff', a)
            pen.seg((x + 14 * k, y - 36 * k), (x + 14 * k, y - 60 * k), w, '#ffffff', a)
            for j in range(3): pen.seg((x - 16 * k, y - 14 * k + j * 14 * k), (x + 16 * k, y - 14 * k + j * 14 * k), w * 0.7, '#ffffff', a)
        elif n == 4:                                                        # complaint sheet
            pen.line(poly([(x - 34 * k, y - 50 * k), (x + 18 * k, y - 50 * k), (x + 36 * k, y - 32 * k), (x + 36 * k, y + 50 * k),
                           (x - 34 * k, y + 50 * k)]), w, '#ffffff', a)
            for j in range(4): pen.seg((x - 20 * k, y - 22 * k + j * 18 * k), (x + 22 * k, y - 22 * k + j * 18 * k), w * 0.7, '#ffffff', a)
        elif n == 5:                                                        # speech bubble with a cross
            pen.line(rrect(x - 50 * k, y - 40 * k, 100 * k, 64 * k, 14 * k), w, '#ffffff', a)
            pen.line(poly([(x - 20 * k, y + 24 * k), (x - 30 * k, y + 46 * k), (x, y + 24 * k)], False), w, '#ffffff', a)
            pen.seg((x - 16 * k, y - 22 * k), (x + 16 * k, y + 6 * k), w, RED_ICON, a); pen.seg((x + 16 * k, y - 22 * k), (x - 16 * k, y + 6 * k), w, RED_ICON, a)
        elif n == 6:                                                        # door with a stop bar
            pen.line(rrect(x - 30 * k, y - 50 * k, 60 * k, 100 * k, 4 * k), w, '#ffffff', a)
            pen.fill(oval(x + 16 * k, y + 4 * k, 5 * k), '#ffffff', a)
            pen.seg((x - 52 * k, y + 52 * k), (x + 52 * k, y - 52 * k), w, RED_ICON, a)
        else:                                                               # padlock
            pen.line(rrect(x - 36 * k, y - 8 * k, 72 * k, 58 * k, 8 * k), w, '#ffffff', a)
            pen.line(smooth([(x - 22 * k, y - 8 * k), (x - 22 * k, y - 40 * k), (x, y - 56 * k), (x + 22 * k, y - 40 * k), (x + 22 * k, y - 8 * k)], False), w,
                     '#ffffff', a)
            pen.fill(oval(x, y + 18 * k, 7 * k), '#ffffff', a)
    return f


RED_ICON = '#e3262e'


def B_rule(F, sh):
    """Rule card over a dimmed, blurred LIVE scene (v2.1): the camera pushes at the house rate, the officer sways at the
    door behind the blur (porch / door backgrounds), the light bar sweeps; the card carries a small icon. Cards are capped
    near 4.5 s in the plan (the rest of the narration plays over the next shot)."""
    p = sh.p
    n = p['n']; text_ = RULES[n]
    bgk = p.get('bg', 'porch')
    L = []
    if bgk == 'door':
        sp = ST.porch_doorbell(police=True); kw = dict(lens=DOORBELL, grade='doorbell_night', focus=1.0, dof=0.0)
        L, _ = people(F, sh, sp, [dict(who='officer', at=DA(0.1, 1.05), act=_A(stare(-1), sway(10, 2.6, 5), creep(8, 4, None)), talk=False)],
                      lambda t: porch_light(t, True, k=0.8))
    elif bgk == 'street':
        sp = ST.street_wide(police=dict(mode='sweep', strength=1.3)); kw = dict(lens=None, grade='night_blue', focus=1.1, dof=0.0)
    else:
        sp, _ = _bg(F, sh, bgk, p); kw = dict(lens=None, grade='night_blue', focus=1.0, dof=0.0)
        if bgk == 'porch':
            L, _ = people(F, sh, sp, [dict(who='officer', at='officer', act=_A(stare(-1), sway(12, 2.4, 6), creep(10, 4, None)), talk=False)],
                          lambda t: porch_light(t, True, base='#ffcf9a', key=0.1, k=0.7))
    cam = mkcam(sh, 'push', 960, 540, 1.03, rate=push_rate(sh.t0))
    t0 = sh.t0
    icon = _icon(n)

    def hud(cv, t):
        H.rule_card(cv, n, text_, t - t0, icon=icon)
    return Spec(sp.add(*L), cam, kw['lens'], kw['grade'], kw['focus'], kw['dof'],
                fx=lambda t: dict(sp.fx(t), blur=6, dim=0.35), hud=hud)


BUILDERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith('B_')}

SPACE = {'street': 'street', 'door': 'outside', 'peep': 'outside', 'car': 'street', 'hall': 'inside', 'kitchen': 'inside',
         'living': 'inside', 'mumext': 'phone', 'mumroom': 'phone', 'ins': 'close', 'hands': 'close', 'phone': 'close',
         'wave': 'radio', 'rule': None, 'curtain': 'phone', 'black': None}


def bust_space(sh):
    return {'porch': 'outside', 'hall': 'inside', 'kitchen': 'inside', 'mumroom': 'phone', 'mumext': 'phone', 'car': 'street'}.get(sh.p.get('bg', 'porch'), 'outside')


# ==================================================================================================== per-shot cues + fx
def shot_common(F, sh, spec):
    """Collect the shot's SFX / music events from its acting, camera, tags and explicit cue lists."""
    p = sh.p
    space = bust_space(sh) if sh.kind in ('bust', 'hands') else SPACE.get(sh.kind)
    for a in sh.actors:
        for e in a.events:
            if sh.t0 - 0.05 <= e['t'] <= sh.t1 + 0.4 and e['name']:
                pr = dict(e.get('params') or {})
                g = e.get('gain_db', 0.0)
                if e['name'].startswith('footsteps') and sh.kind in ('street', 'mumext'): g -= 5
                sh.sfx.append(_ev(e['t'], e['name'], g, e.get('pan', 0.0), space if space != 'radio' else 'outside', **pr))
    mv = (p.get('cam') or {}).get('mv')
    if mv in ('fast', 'pull') or (p.get('cam') or {}).get('snap'):
        sh.sfx.append(_ev(sh.t0 + 0.02, 'whoosh', -6 if mv == 'fast' else -4, 0, None, kind='soft' if mv != 'pull' else 'hard'))
    if (p.get('cam') or {}).get('snap'):
        sh.sfx.append(_ev(p['cam']['snap'][0], 'whoosh', -3, 0, None, kind='hard'))
    for tg in p.get('tags', []):
        sh.sfx.append(_ev(tg[0], 'ui_pop', -3, 0, 'close'))
    if p.get('cut') in ('static', 'glitch'):
        sh.sfx.append(_ev(sh.t0, 'glitch', -4, 0, None, dur=0.25, amount=0.8))
    if p.get('cut') == 'white':
        sh.sfx.append(_ev(sh.t0, 'impact_hit', 0, 0, None, size=1.1))
    if p.get('hit'):
        for h in (p['hit'] if isinstance(p['hit'], (list, tuple)) else [p['hit']]):
            if sh.kind == 'door': continue                  # doorbell hits = the camera jolting on knocks (knock SFX come
            sh.sfx.append(_ev(h, 'impact_hit', -2, 0, None, size=1.0))   # from the acting events), not score hits
            sh.music.append({'t': round(h, 3), 'type': 'hit', 'level': 0.75})
    for c in p.get('sfx', []):                   # explicit (t, name, gain, pan, space, params)
        t, name = c[0], c[1]
        g = c[2] if len(c) > 2 else 0.0; pan = c[3] if len(c) > 3 else 0.0
        sp_ = c[4] if len(c) > 4 else space
        pr = c[5] if len(c) > 5 else {}
        sh.sfx.append(_ev(t, name, g, pan, sp_ if sp_ != 'radio' else 'outside', **pr))
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
        for k, (tt, st) in enumerate(p.get('states', [(sh.t0, 'calling')])):
            if st == 'calling': sh.sfx.append(_ev(tt + 0.25, 'phone_ring', -4, 0, 'phone', kind='ringback', dur=round(min(4.0, sh.t1 - tt), 2)))
            elif st == 'busy': sh.sfx.append(_ev(tt, 'phone_busy', -4, 0, 'phone', dur=round(min(3.0, sh.t1 - tt), 2)))
            elif st == 'connected': sh.sfx.append(_ev(tt, 'phone_pickup', -2, 0, 'close'))
            elif st == 'incoming': sh.sfx.append(_ev(tt, 'phone_vibrate', -4, 0, 'close', n=2))
            sh.sfx.append(_ev(tt, 'ui_pop', -8, 0, 'close'))
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
                if an:                                   # pinned to a subject point: project it through this shot's camera
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
    sh.spec_kind = sh.kind


EXPO = {'hall': -0.45, 'kitchen': -0.45, 'mumroom': -0.4, 'living': -0.4, 'door': -0.2, 'bust_hall': -0.2, 'bust_mumroom': -0.2,
        'bust_porch': -0.1, 'ins': -0.15, 'hands': -0.1}         # stops: sit the families on the reference medians (VISUAL_SPEC a)


def glob_fx(F, sh, t, fx):
    """Per-frame global effects: scare-cut flashes, the climax creeping into red, the end fade."""
    u = t - sh.t0
    c = sh.p.get('cut')
    if c == 'static' and u < 0.09: fx['static'] = 0.85 - u * 6
    elif c == 'glitch' and u < 0.12: fx['glitch'] = 0.9; fx['static'] = 0.3
    elif c == 'white' and u < 0.1: fx['white'] = 0.85 * (1 - u / 0.1)
    ek = EXPO.get(sh.kind if sh.kind != 'bust' else 'bust_' + sh.p.get('bg', 'porch'), 0.0)
    if ek: fx['exposure'] = fx.get('exposure', 0.0) + ek
    if sh.kind not in ('rule', 'black'):
        # the last 35 %: darker, redder, more saturated (VISUAL_SPEC g/h10), then a second ramp over the last minute
        # into the climax (red share >= 3 %, saturation +40 %, luma -15 % or more); UI / insert shots take half of it
        k = clamp((t - 455.0) / 190.0)
        k2 = clamp((t - 636.0) / 30.0)
        if k > 0:
            ui = 0.5 if sh.kind in ('phone', 'wave', 'ins', 'hands', 'curtain') else 1.0
            ext = sh.kind in ('mumext', 'door', 'street', 'car', 'peep') or sh.p.get('bg') in ('mumext', 'porch')
            fx['red'] = fx.get('red', 0.0) + ((0.42 + (0.18 if ext else 0.0)) * k + 0.28 * k2) * ui
            fx['sat'] = fx.get('sat', 1.0) * (1 + (0.6 * k + 0.25 * k2) * ui)
            fx['exposure'] = fx.get('exposure', 0.0) - (0.3 * k + 0.25 * k2) * ui
    if t > F.duration - 2.6: fx['fade'] = clamp((t - (F.duration - 2.6)) / 1.6)
    if t < 0.35: fx['fade'] = max(fx.get('fade', 0.0), 1 - t / 0.35)


# ==================================================================================================== beds + music curve
LOC = {'street': 'ext', 'door': 'ext', 'peep': 'ext', 'car': 'ext', 'bust': 'ext', 'hall': 'int', 'kitchen': 'int',
       'living': 'int', 'ins': 'int', 'hands': 'int', 'phone': 'int', 'wave': 'int', 'rule': None, 'mumext': 'mum',
       'mumroom': 'mum', 'curtain': 'mum', 'black': None}


def beds(F):
    """Ambience beds: the night outside runs under the whole house story (heard through the walls inside), room tone
    inside, the idling patrol car while it sits at the curb, mum's room through the phone, a wall clock in the kitchen."""
    out = []
    D = F.duration
    t_call = F.t(221)                                       # she answers
    out.append(_ev(0.0, 'ambience_night', -2, 0, 'outside', dur=round(t_call + 4, 1), dog=0.5, wind=0.45, buzz=0.5))
    out.append(_ev(0.0, 'room_tone', -4, 0, 'inside', dur=round(D, 1)))
    out.append(_ev(F.t(9), 'car_idle', -6, -0.4, 'street', dur=round(F.t(219) + 2 - F.t(9), 1)))
    out.append(_ev(t_call, 'ambience_night', -9, 0, 'phone', dur=round(D - t_call, 1), dog=0.3, wind=0.6, buzz=0.0))
    # mum's room tone and clock through the phone, kitchen clock
    for sh in F.shots:
        if sh.kind == 'mumroom' and sh.d > 1.5:
            out.append(_ev(sh.t0, 'clock_tick', -10, 0.3, 'phone', dur=round(sh.d, 2), bpm=60))
        if sh.kind == 'kitchen':
            out.append(_ev(sh.t0, 'clock_tick', -6, 0.4, 'inside', dur=round(sh.d, 2), bpm=60))
    return out


INTENSITY = [  # (line index or seconds, level): the story's tension, read off the beats
    (0.0, 0.42), (9.3, 0.38), (23.5, 0.3), (27.0, 0.4), (39.9, 0.38), (59.0, 0.5), (69.0, 0.55), (78.0, 0.62), (86.0, 0.5),
    (91.0, 0.36), (112.8, 0.45), (118.0, 0.55), (128.7, 0.62), (139.3, 0.6), (148.2, 0.66), (153.6, 0.5), (160.0, 0.38),
    (175.8, 0.48), (186.3, 0.6), (192.9, 0.66), (205.2, 0.6), (209.4, 0.5), (215.0, 0.4), (232.3, 0.55), (250.2, 0.58),
    (256.2, 0.7), (263.1, 0.62), (270.0, 0.55), (278.2, 0.5), (284.0, 0.42), (303.8, 0.6), (306.4, 0.72), (312.9, 0.6),
    (322.5, 0.72), (326.3, 0.8), (338.6, 0.72), (346.6, 0.75), (355.8, 0.55), (365.5, 0.5), (379.1, 0.68), (392.9, 0.6),
    (410.2, 0.66), (421.6, 0.78), (427.4, 0.7), (435.5, 0.55), (440.7, 0.5), (459.9, 0.62), (465.2, 0.72), (473.9, 0.78),
    (478.4, 0.86), (485.1, 0.7), (495.7, 0.72), (507.9, 0.8), (512.1, 0.62), (522.3, 0.55), (528.2, 0.5), (537.4, 0.48),
    (544.9, 0.45), (557.5, 0.55), (569.3, 0.62), (583.7, 0.7), (588.6, 0.82), (601.5, 0.86), (606.2, 0.8), (618.0, 0.88),
    (623.6, 0.92), (640.6, 0.86), (643.2, 0.95), (647.1, 0.82), (665.0, 0.9), (673.8, 0.96), (679.3, 1.0), (681.3, 0.7),
    (686.4, 0.8), (689.4, 0.7), (692.9, 0.85), (695.5, 0.97), (697.5, 0.5)]


def intensity_curve(F):
    pts = [[round(t, 2), v] for t, v in INTENSITY]
    pts.append([round(F.duration, 2), 0.0])
    return pts


# ==================================================================================================== the shot plan
# ---------------------------------------------------------------------------------------------------- acting shorthands
def _A(*fns):
    return lambda a, s: [f(a, s) for f in fns if f]


def stare(d=-1.0): return lambda a, s: a.stare(s.t0 + d)
def ex(name, d=-1.0, t1=None): return lambda a, s: a.expr(name, s.t0 + d, t1)
def smile(d=0.2, dur=3.0, amt=1.0): return lambda a, s: a.creep_smile(s.t0 + d, dur, amount=amt)
def grin(d=-1.0): return lambda a, s: (a.stare(s.t0 - 1), a.wide_grin(s.t0 + d))
def tilt(d=0.3, ang=26.0, dur=1.6, back='ease'): return lambda a, s: a.head_tilt(s.t0 + d, ang, dur)
def lean(d=0.1, dur=2.4, amt=1.0): return lambda a, s: a.lean_in(s.t0 + d, dur, amount=amt)
def snap(t, frm=0.9, to=0.0): return lambda a, s: a.snap_turn(t, frm, to)
def nod(d=0.3): return lambda a, s: a.set(s.t0 + d, s.t0 + d + 0.5, 0.25, h_nod=0.22)
def look_side(t, h=0.85, fade=0.45): return lambda a, s: a.set(t, None, fade, h_turn=h, lock=0.0, look_x=0.6 if h > 0 else -0.6)
def down(d=-1.0, amt=1.0): return lambda a, s: a.head_down(s.t0 + d, None, amt)
def back_view(): return lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=2.0)
def twitch(*ds): return lambda a, s: a.twitch([s.t0 + d for d in ds])
def blink_at(*ds): return lambda a, s: [a.blink(s.t0 + d) for d in ds]


# ---- v2.1 acting layers: life in every door / peep shot (owner: "they should act weirdly and creepy")
def sway(amp=7.0, per=3.3, tilt=3.0, ph=0.0):
    """Weight shift: hips rock amp design px with period per, the head counter-tilts (unsettling slow rocking)."""
    def f(a, s):
        def fn(P, t):
            u = math.sin(2 * math.pi * (t - s.t0) / per + ph)
            P.sway += amp * u; P.tilt += 0.9 * u; P.h_tilt -= tilt * u
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
    return f


def creep(tilt=9.0, amp=6.0, tw=0.55, loosen=0.5, per=3.6):
    """The creepy layer for officers and the double: a slow head-tilt drift over the whole shot (to `tilt` degrees),
    weight-shift sway, one twitch at fraction `tw` of the shot (None = no twitch), and the body's stillness loosened
    (the face keeps its locked stare; breathing and sway continue). Add it LAST in an act list."""
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


def tremble(amp=1.0):
    """Fear tremble for 'you' / mum: fast head jitter (8-12 Hz), shoulder shiver, quick nervous blink bursts."""
    def f(a, s):
        a._trem = True
        def fn(P, t):
            P.h_dx += 1.2 * amp * math.sin(t * 61.0) + 0.8 * amp * noise1(t * 9.0, a.seed + 77)
            P.h_tilt += 0.9 * amp * math.sin(t * 47.0 + 1.0)
            P.shrug += 0.04 * amp * (1 + math.sin(t * 23.0))
            P.jitter = max(P.jitter, 0.35 * amp)
        a._add(s.t0 - 1.0, s.t1 + 1.0, fn, real=True)
        k = s.t0 + 0.35
        while k < s.t1 - 0.3:                                  # blink bursts: 2-4 rapid blinks every ~1.4 s
            nb = 2 + int(hash01(int(k * 10), a.seed) * 3)
            if hasattr(a, 'blink_burst'): a.blink_burst(k, nb, 0.12 * nb)
            else:
                for j in range(nb): a.blink(k + j * 0.12, 0.06)
            k += 1.1 + 0.8 * float(hash01(int(k * 7), a.seed + 3))
    return f


def hand_mouth(d=0.3, dur=None, side=-1):
    """Shock / grief: the free hand comes up over the mouth (fingers up), eases back down after dur."""
    def f(a, s):
        sh_ = a.sp['body']['sh']; t0 = s.t0 + d; t1 = None if dur is None else t0 + dur

        def fn(P, t):
            w = ease_in_out(clamp((t - t0) / 0.35)) * (1.0 if t1 is None else 1.0 - ease_in_out(clamp((t - t1) / 0.4)))
            if w > 0: a._arm(P, side, w, -(sh_ - 17) + sh_ * 0.32, -42.0, 190.0, 'relaxed', up=1.0)
        a._add(t0 - 0.1, None if t1 is None else t1 + 0.5, fn)
    return f


def knk(d=0.3, n=3, sp=0.3, side=-1, strength=1.0):
    """Knock on the door beside the doorbell (side -1: door to screen left, +1 right, 0 = the lens)."""
    return lambda a, s: a.knock(s.t0 + d, n, sp, side, strength=strength)


def knk_at(t, n=3, sp=0.3, side=-1, strength=1.0):
    return lambda a, s: a.knock(t - 0.34, n, sp, side, strength=strength)


def pt(d=0.3, dur=1.6, side=-1, dx=1.0, dy=0.0):
    """Point: dx=0 points straight at the lens (at you)."""
    return lambda a, s: a.point(s.t0 + d, s.t0 + d + dur, side, dx, dy)


def radio(d=0.2, dur=1.6, side=1):
    return lambda a, s: a.radio_to_mouth(s.t0 + d, s.t0 + d + dur, side)


def turn_to(d, to, dur=0.6): return lambda a, s: a.turn(s.t0 + d, to, dur)


def turned(to=2.0): return lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=to)


def jerk_at(d, amp=1.0): return lambda a, s: a.jerk(s.t0 + d, amp)


def frz(d0, d1): return lambda a, s: a.freeze(s.t0 + d0, s.t0 + d1)


_PDB = {}


def DA(X, D, Y=None):
    """Doorbell-view anchor (x, y, depth, height) at lateral X m and depth D (porch floor Y=0 in front of the steps,
    the yard / path Y=-0.72 beyond them). Depth 0.45-0.62 = leaning into the lens (fisheye bulge)."""
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
    """Your-hallway anchor (x, y, depth, height): X lateral m, D depth (the door is at ~2.6)."""
    if 'h' not in _PDB: _PDB['h'] = ST.View(620, 430, 1.5)
    a = _PDB['h'].anchor(X, D, Y); return (a.x, a.y, a.depth, a.height)


def MA(X, D, Y=0.0):
    """Mum's-room anchor (x, y, depth, height); the window is to the right at depth ~2.2, her hall door far left."""
    if 'm' not in _PDB: _PDB['m'] = ST.View(600, 450, 1.5)
    a = _PDB['m'].anchor(X, D, Y); return (a.x, a.y, a.depth, a.height)


def MX(name):
    """mother_exterior anchor tuple by name."""
    if 'mx' not in _PDB: _PDB['mx'] = ST.mother_exterior(car=False).anchors
    a = _PDB['mx'][name]; return (a.x, a.y, a.depth, a.height)


def phone_ear(side=1, d=-2.0):
    """Phone pressed to the ear (characters v2.1 Acting.phone_to_ear: wrist under the ear, elbow forward and down)."""
    def f(a, s):
        if hasattr(a, 'phone_to_ear'): return a.phone_to_ear(s.t0 + d, None, side)
        sh_ = a.sp['body']['sh']
        a._add(s.t0 + d, None, lambda P, t: (a._arm(P, side, 1.0, -(sh_ - 17) + sh_ * 0.85, -30.0, 40.0, 'grip', up=0.95, prop='phone'),
                                             setattr(P, 'h_tilt', P.h_tilt + 5 * side)))
    return f


def hold_prop(prop, d=0.0, side=-1, t1=None):
    return lambda a, s: a.hold_up(prop, s.t0 + d, (t1 if t1 is not None else s.t1 + 1.0), side)


def P(who, at='officer', act=None, **k):
    return dict(who=who, at=at, act=act, **k)


def disp(t0, title, lines, x=1290, y=170, w=540):
    return lambda cv, t: H.dispatch_panel(cv, x, y, title, lines, t - t0, w=w)


def doors_open(t_open, part='rear', dur=0.7, t_close=None):
    def f(t):
        k = ease_in_out(clamp((t - t_open) / dur))
        if t_close is not None: k *= 1 - ease_in_out(clamp((t - t_close) / 0.5))
        return {part: k}
    return f


# ---------------------------------------------------------------------------------------------------- the plan
def plan(F):
    t, e, w, C = F.t, F.e, F.w, F.cut
    T = lambda i, off=0.0: F.t(i) - LEAD + off
    O, D, Y, M, O2 = 'officer', 'double', 'you', 'mum', 'officer2'
    G = F.globals
    red_rim = lambda t_: dict(rim='#ff3040', rim_a=150, side=-1, key=-0.2)

    # ============================================================ COLD OPEN (0 - 23.7)
    kn = w(0, 'knocks')
    C(0.0, 'street', cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.035), music=[(0.3, 'motif', 0.45, 6)])
    C(kn - 0.45, 'door', ppl=[P(O, at=DA(0.4, 1.05), act=_A(ex('calm_smirk'), stare(-1), knk_at(kn + 0.05, 3, 0.3, -1), lean(1.55, 0.9, 0.55),
                                                           tilt(1.4, 14, 1.0), creep(4, 5, None)), lean=True)], py=-60, px=40,
      hit=[kn + 0.05, kn + 0.35, kn + 0.65])
    C(w(0, 'tells') - 0.1, 'peep', ppl=[P(O, act=_A(stare(), smile(0.4, 3.2)))], cam=dict(mv='push', x=960, y=470, z=1.05))
    C(w(0, 'not') - 0.35, 'hall', act=_A(ex('nervous'), back_view()), cam=dict(mv='fast', x=960, y=520),
      tags=[(w(0, 'step'), 'DO NOT STEP OUTSIDE', 960, 150, 'alert')])
    C(T(1), 'street', bedroom=1.0, cam=dict(mv='move', x=930, y=520, z=1.25, x1=1010, y1=470, z1=1.42))
    C(T(2), 'ins', name='licence', cam=dict(mv='push', x=960, y=560, z=1.0))
    C(T(3), 'bust', who=O, cy=470, scale=0.9, act=_A(stare(), smile(0.2, 2.4, 0.5)), cam=dict(mv='move', x=960, y=520, z=1.0, y1=700, z1=1.25),
      tags=[(t(3) + 0.35, 'RECORDING', 1270, 820, 'red')])
    C(T(4), 'door', ppl=[P(O, path=(T(4) - 0.2, T(4) + 1.5, [DA(-0.35, 1.6), DA(0.0, 0.95)]),
                          act=_A(stare(), lean(1.5, 1.4, 0.95), tilt(1.2, 18, 2.0), creep(4, 4, None)), lean=True)], py=-80, z1=1.12)
    C(w(4, 'remember') - 0.15, 'car', act=_A(lambda a, s: a.head_down(s.t0 - 2, s.t0 + 1.2, 1.0), stare(1.1)),
      expr='dead_stare', cam=dict(mv='push', x=985, y=450, z=1.1))
    C(w(4, 'listening') - 0.2, 'wave', layout='officer_l', title='BODYCAM  -  AUDIO', rows=[dict(label='REC  00:36:12', color='split', split=0.55, seed=4)],
      play=(w(4, 'listening') - 0.6, e(4) + 0.6), sfx=[(w(4, 'listening'), 'radio_static', -14, 0.1, 'outside', dict(dur=2.0, amount=0.3))])

    # ============================================================ THE KNOCK (23.7 - 86)
    C(T(5), 'kitchen', cam=dict(mv='move', x=1405, y=245, x1=1430, y1=228, z=1.0, z1=1.06, d=2.29, opt=2.1), police=False,
      without=('room', 'headlights', 'police_spill', 'pendant_light', 'pendant', 'table'))
    kk = w(5, 'knocking')
    C(kk - 0.3, 'hall', you=False, feet=lambda t_: [0.44, 0.58], cam=dict(mv='push', x=960, y=560, z=1.08, rate=0.05, hit=[kk + 0.05, kk + 0.33, kk + 0.61]),
      sfx=[(kk + 0.05, 'knock_door', 0, 0, 'inside', dict(n=3, spacing=0.28, force=0.85))], hit=None,
      music=[(kk - 0.6, 'silence', 0.0, 0.55)])
    C(T(6), 'hall', act=_A(ex('nervous'), back_view()), cam=dict(mv='push', x=960, y=480, z=1.0, rate=0.04),
      sfx=[(t(6) + 0.2, 'footsteps_wood_inside', -4, 0, 'inside', dict(n=3, rate=1.6, approach=1))])
    C(w(6, 'police') - 0.1, 'peep', ppl=[P(O, act=_A(stare(), ex('polite')))], cam=dict(mv='push', x=960, y=500, z=1.0))
    C(T(7), 'bust', who=O, cy=420, scale=0.85, act=_A(ex('polite'), stare(0.2)), cam=dict(mv='move', x=960, y=470, z=0.95, x1=1060, y1=760, z1=1.45),
      tags=[(t(8) + 0.25, 'BADGE  4471', 1300, 700, 'white')])
    C(T(9), 'street', cam=dict(mv='move', x=1380, y=650, z=1.35, x1=1600, y1=640, z1=2.4), police=dict(mode='sweep', strength=1.2))
    C(T(10, -0.2), 'door', ppl=[P(O, at=DA(-0.45, 1.15), act=_A(ex('polite'), turned(1.6), turn_to(0.3, 0.0, 0.7), tilt(1.3, 10, 1.2), nod(1.7),
                                                                creep(5, 4, None)))], py=-70, px=-60)
    C(T(12), 'peep', ppl=[P(O, act=_A(ex('polite'), smile(1.2, 3.0, 0.6), lean(0.2, 2.0, 0.35)), lean=True)], cam=dict(mv='push', x=960, y=480))
    C(w(12, 'unauthorized') - 0.1, 'bust', who=O, act=_A(ex('talk_smile'), stare(0.0)), cam=dict(mv='push', x=960, y=540),
      hud=disp(w(12, 'unauthorized'), 'DISPATCH  -  CALL 24-1187', ['UNAUTHORIZED PERSON', 'ADDRESS: 144 ELM ST', 'CALLER: HOMEOWNER'], x=60, y=640),
      sfx=[(w(12, 'unauthorized'), 'ui_pop', -5, -0.4, 'close'), (w(12, 'unauthorized') + 0.3, 'typing', -12, -0.4, 'close', dict(dur=1.6, cps=16))])
    C(T(13), 'hall', act=_A(ex('nervous'), lambda a, s: a.set(s.t0 - 1, None, 0.1, turn=1.6, h_turn=0.3)), cam=dict(mv='push', x=900, y=520, z=1.05))
    C(T(14), 'bust', who=O, cy=380, scale=0.85, act=_A(stare(), lambda a, s: a.press_bodycam(s.t0 + 0.25)), cam=dict(mv='push', x=1000, y=700, z=1.25, rate=0.04),
      tags=[(t(14) + 0.75, 'BODYCAM', 1330, 760, 'red')])
    C(T(15), 'door', ppl=[P(O, at=DA(0.0, 0.8), act=_A(stare(), lean(-0.3, 0.9, 1.0), tilt(0.05, 16, 0.7), creep(4, 3, None)), lean=True)], py=-100)
    C(T(16), 'bust', who=Y, bg='hall', act=_A(ex('fear')), cam=dict(mv='hand', x=960, y=560, z=1.0))
    C(T(17), 'peep', ppl=[P(O, act=_A(stare(), nod(0.25), look_side(w(17, 'looks') - 0.1, 0.9)))], cam=dict(mv='push', x=980, y=500))
    C(T(18), 'bust', who=O, act=_A(look_side(-2, 0.9, 0.1), snap(t(18) + 0.15, 0.9, 0.0), smile(0.4, 2.0, 0.7)), cam=dict(mv='push', x=960, y=540),
      sfx=[(t(18) + 0.15, 'whoosh', -10, 0, None, dict(kind='soft'))])
    C(T(19), 'peep', ppl=[P(O, act=_A(look_side(-2, 0.9, 0.1)))], cam=dict(mv='move', x=1000, y=520, z=1.0, x1=1240, y1=640, z1=1.7))
    C(w(19, 'someone') - 0.1, 'car', act=_A(down(-2), lambda a, s: a.set(t(21) - 0.6, None, 0.6, hl_down=300, hr_down=300, hl_fwd=60, hr_fwd=60)),
      expr='dead_stare', cam=dict(mv='move', x=985, y=450, z=1.0, x1=985, y1=600, z1=1.45), hit=w(19, 'someone'),
      music=[(w(19, 'someone') - 1.2, 'silence', 0.0, 1.1)])
    C(T(22), 'hands', who=D, cam=dict(mv='push', x=980, y=600, z=1.1, rate=0.035))
    C(T(23), 'hands', who=Y, bg='hall', cam=dict(mv='push', x=960, y=620, z=1.1, rate=0.03), music=[(t(23), 'motif', 0.5, 4)])
    C(T(24), 'door', ppl=[P(O, path=(T(24) - 0.15, T(24) + 1.7, [DA(0.15, 1.9), DA(0.0, 0.9)]),
                           act=_A(stare(), smile(1.0, 2.0, 0.6), lean(1.75, 1.0, 0.8), creep(3, 3, None)), lean=True)], py=-60)
    C(T(25), 'peep', ppl=[P(O, at='officer_close', act=_A(stare(), smile(-0.5, 2.5, 1.0)))], cam=dict(mv='push', x=960, y=440, z=1.0, rate=0.04))
    C(w(25, 'which') - 0.1, 'bust', who=O, scale=1.15, act=_A(grin(-0.5), tilt(0.5, 22, 1.6)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.05))
    C(T(26), 'street', cam=dict(mv='pull', x=960, y=560, z=1.0), police=dict(mode='strobe'), music=[(t(26) + 0.1, 'braam', 0.8)],
      tags=[(w(26, 'seven'), '7  RULES', 960, 200, 'white', 2.4)])
    C(T(27), 'hall', act=_A(ex('fear'), back_view()), cam=dict(mv='fast', x=960, y=500))
    C(w(27, 'never') - 0.15, 'car', act=_A(lambda a, s: a.head_down(s.t0 - 2, s.t0 + 0.2, 1.0), stare(0.15), smile(0.6, 1.8, 0.6)),
      expr='dead_stare', scale=0.5, cam=dict(mv='push', x=985, y=440, z=1.25, rate=0.05), cut='static', music=[(w(27, 'never'), 'stinger', 0.8)])



    # ============================================================ RULE 1 (86.1 - 153.6): the licence
    C(T(28), 'rule', n=1, bg='porch')
    C(T(30), 'door', ppl=[P(O, at=DA(0.25, 1.0), act=_A(ex('polite'), pt(0.35, 1.9, -1, 0.0), lean(0.6, 1.6, 0.45), creep(7, 5, 0.85)), lean=True)],
      py=-60, px=40)
    C(T(31), 'ins', name='mail_slot', kw=lambda t_, t0=t(31): dict(feed=0.0, item='licence', flap=ease_in_out(clamp((t_ - t0 - 0.4) / 0.5))),
      cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.03), sfx=[(t(31) + 0.45, 'mail_slot', -2, 0, 'inside', dict(paper=False))])
    C(T(32), 'peep', ppl=[P(O, at='officer_close', act=_A(ex('polite'), tilt(0.3, 14, 1.4)))], cam=dict(mv='push', x=960, y=480, z=1.05))
    C(T(34), 'hall', you_at=(900, 1524, 0.85, 1349), act=_A(ex('nervous'), hold_prop('card', 0.3)), cam=dict(mv='push', x=930, y=520))
    C(T(35), 'ins', name='licence', motion=lambda t_: (0, 4 * math.sin(t_ * 2.0), 0.0, 0.6 * math.sin(t_ * 1.3)), cam=dict(mv='push', x=960, y=540, z=1.08))
    C(T(36), 'door', ppl=[P(O, path=(T(36) + 0.3, T(36) + 1.4, [DA(-0.3, 1.25), DA(-0.1, 0.95)]), act=_A(ex('polite'), tilt(1.0, 14, 1.4), smile(1.4, 1.2, 0.6), creep(4, 3, None)))],
      py=-60, px=-40)
    C(T(37), 'door', ppl=[P(O, at=DA(-0.2, 1.05), act=_A(ex('polite'), lambda a, s: a.turn(w(37, 'turn') - 0.1, 1.7, 0.7),
                                                       lambda a, s: a.point(w(37, 'gesture') - 0.4, w(37, 'gesture') + 1.0, 1, 1.0, 0.2),
                                                       lambda a, s: a.turn(s.t1 - 0.9, 0.0, 0.45), smile(3.2, 1.0, 0.7), creep(4, 4, None)))],
      py=-40, px=120, z1=1.15)
    C(T(38), 'car', act=_A(stare(), hold_prop('card', 0.8, -1)), expr='dead_stare', cam=dict(mv='push', x=985, y=470, z=1.05),
      sfx=[(t(38) + 0.9, 'paper', -8, -0.3, 'street', dict(dur=0.6))])
    C(T(39), 'ins', name='licence_window', cam=dict(mv='move', x=960, y=540, z=1.0, x1=880, y1=520, z1=1.3))
    C(w(40, 'corner') - 0.2, 'ins', name='licence_window', cam=dict(mv='push', x=1130, y=440, z=1.32, rate=0.04, snap=(w(40, 'corner'), 1.12)),
      music=[(w(40, 'corner'), 'stinger', 0.6)])
    C(T(41), 'ins', name='licence', cam=dict(mv='move', x=960, y=540, z=1.02, x1=1150, y1=430, z1=1.38), grade='neutral', post=dict(sat=0.35, exposure=0.15), cut='white',
      sfx=[(w(41, 'door'), 'car_door_close', -6, 0.2, 'close')])
    C(T(43), 'car', act=_A(stare(), lambda a, s: a.hold_up('card', s.t0 - 2.0, s.t1 + 1, -1)), expr='dead_stare', scale=0.5,
      cam=dict(mv='push', x=900, y=420, z=1.3, rate=0.04))
    C(w(43, 'missing') - 0.1, 'ins', name='licence', cam=dict(mv='push', x=1060, y=470, z=1.1, rate=0.05), hit=w(43, 'missing'),
      music=[(w(43, 'missing') - 0.9, 'silence', 0.0, 0.85)])
    C(T(44), 'hall', you_at=HA(-0.25, 0.95), act=_A(ex('fear'), back_view(), down(0.1, 0.8), hold_prop('card', -0.5, -1), tremble(0.4)),
      cam=dict(mv='push', x=860, y=480, z=1.05, rate=0.05))
    C(T(45), 'hall', act=_A(ex('fear'), back_view()), cam=dict(mv='fast', x=960, y=520, z=1.0))
    C(w(45, 'open') - 0.1, 'ins', name='lock_inside', kw=dict(turn=0.0, chain=1.0), hand=None, cam=dict(mv='push', x=960, y=540, z=1.05, rate=0.04),
      sfx=[(w(45, 'open') + 0.4, 'chain_lock', -8, 0, 'close', dict(action='unlock'))])
    C(T(46), 'peep', ppl=[P(O, act=_A(look_side(-2, 0.7, 0.1), snap(t(46) + 0.35, 0.7, 0.0), smile(0.5, 1.5)))],
      cam=dict(mv='push', x=960, y=470, z=1.1, rate=0.05))
    C(T(47), 'bust', who=O, scale=1.1, act=_A(grin(-0.5)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04))
    C(T(49), 'door', ir=True, ppl=[P(O, at=DA(0.0, 0.9), act=_A(grin(-1), lean(-0.2, 1.4, 1.0), tilt(0.5, 14, 1.2)), lean=True)], py=-110)
    C(T(50), 'car', act=_A(stare(), lambda a, s: a.hold_up('card', s.t0 - 2.0, s.t0 + 0.5, -1)), expr='dead_stare', cam=dict(mv='push', x=985, y=470, z=1.1))
    C(T(51), 'car', act=_A(stare(), creep(4, 2, None)), expr='dead_stare', hand=(1205, 620, 230), hand_t=t(51) + 0.55,
      cam=dict(mv='move', x=1000, y=450, z=1.05, x1=1060, y1=430, z1=1.55), music=[(t(52), 'motif', 0.5, 3)],
      sfx=[(t(51) + 0.6, 'knock_door', -10, -0.3, 'street', dict(n=1, material='glass', force=0.3))])

    # ============================================================ RULE 2 (153.6 - 209.4): the second recording
    C(T(53), 'rule', n=2, bg='door')
    C(T(53, 4.5), 'peep', ppl=[P(O, at='officer_close', act=_A(stare(), tilt(0.1, -18, 1.2), creep(0, 3, None)))], cam=dict(mv='push', x=960, y=470, z=1.02))
    C(T(55), 'bust', who=O, cy=420, scale=0.9, act=_A(ex('polite'), lambda a, s: a.press_bodycam(s.t0 + 1.0)), cam=dict(mv='push', x=990, y=640, z=1.1),
      tags=[(t(55) + 1.4, 'BODYCAM', 1330, 760, 'red')])
    C(T(56), 'door', ppl=[P(O, at=DA(-0.3, 0.95), act=_A(ex('talk_smile'), pt(0.3, 1.3, 1, 0.0), lean(0.2, 1.8, 0.6), creep(8, 5, None)), lean=True)],
      py=-90)
    C(w(56, 'say') - 0.1, 'peep', ppl=[P(O, at='officer_close', act=_A(stare(), smile(-1, 1.0, 0.5)))], cam=dict(mv='push', x=960, y=440, z=1.0, rate=0.04))
    C(T(57), 'bust', who=Y, bg='hall', act=_A(ex('fear'), lambda a, s: a.set(s.t0, None, 0.2, m_press=1.0, blink=0.0)), cam=dict(mv='hand', x=960, y=560, z=1.05),
      tags=[(t(57) + 0.05, 'STAY QUIET', 960, 150, 'alert')], music=[(t(57), 'silence', 0.0, 1.0)])
    C(T(58), 'peep', ppl=[P(O, at='officer_close', act=_A(ex('polite'), tilt(1.2, 20, 1.2)))], cam=dict(mv='push', x=960, y=480))
    C(T(60), 'bust', who=O, act=_A(stare(), smile(0.2, 2.6, 0.8), lean(0.8, 2.4, 0.3)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.035))
    C(T(62), 'ins', name='radio', cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04),
      sfx=[(w(62, 'crackle'), 'police_radio_squelch', -2, 0.2, 'outside', dict(kind='burst')),
           (w(62, 'crackle'), 'radio_static', -6, 0.2, 'outside', dict(dur=2.2, amount=0.7))])
    C(T(63), 'bust', who=Y, bg='hall', act=_A(ex('shock')), cam=dict(mv='fast', x=960, y=560, z=1.0))
    C(T(64, -0.2), 'wave', layout='door', title='SHOULDER RADIO', rows=[dict(label='PLAY 1  -  YOUR VOICE', color='blue', seed=7, p=(t(64), e(64)))],
      play=(t(64), e(64)), tags=[(t(64), 'YOUR VOICE', 960, 300, 'red', 1.6)])
    C(T(65), 'door', ppl=[P(O, at=DA(0.3, 1.35), act=_A(stare(), ex('calm_smirk'), hold_prop('radio', 0.1, 1), creep(6, 4, None)))], py=-60, px=60, z1=1.25)
    C(T(66), 'wave', layout='officer_r', title='SHOULDER RADIO', rows=[dict(label='PLAY 1', color='blue', seed=7),
                                                             dict(label='PLAY 2', color='blue', seed=7, p=(t(66), t(66) + 1.4))], play=(t(66), t(66) + 1.4))
    C(T(67), 'peep', ppl=[P(O, act=_A(stare(), lambda a, s: a.radio_to_mouth(s.t0 + 0.2, s.t1 + 3)))], cam=dict(mv='push', x=960, y=470, z=1.05))
    C(T(68), 'wave', layout='radio', title='SHOULDER RADIO', rows=[dict(label='PLAY 1', color='blue', seed=7),
                                                         dict(label='PLAY 2', color='split', split=0.42, seed=9, p=(t(69), e(69)), marker=(0.42, 0.62, 'PAUSE TOO LONG'))],
      play=(t(69), e(69)))
    C(T(70), 'peep', ppl=[P(O, act=_A(look_side(-2, 0.6, 0.1)))], approach=False, cam=dict(mv='move', x=1060, y=540, z=1.1, x1=1250, y1=640, z1=1.8))
    C(w(70, 'see') - 0.1, 'car', act=_A(stare(), lean(0.0, 1.4, 0.45), lambda a, s: a.talk([(s.t0 + 0.2, s.t1 + 0.3, 'i live here i live here')], intensity=0.5)),
      expr='whisper', scale=0.46, cam=dict(mv='push', x=985, y=450, z=1.1, rate=0.05))
    C(T(71), 'car', act=_A(stare(), lean(0.0, 1.0, 0.25), lambda a, s: a.talk([(s.t0 + 0.1, s.t1 + 0.3, 'i live here i live here')], intensity=0.6)),
      expr='whisper', scale=0.5, cam=dict(mv='push', x=985, y=450, z=1.3, rate=0.05))
    C(T(72), 'bust', who=O, cx=900, cy=470, scale=0.86, act=_A(stare(), lambda a, s: a.radio_to_mouth(s.t0 + 0.3, s.t0 + 2.2), smile(1.2, 1.6, 0.6)),
      cam=dict(mv='push', x=980, y=520, z=1.0, rate=0.045))
    C(T(73), 'door', ppl=[P(O, at=DA(0.3, 0.8), act=_A(grin(-0.5), knk(0.0, 2, 0.28, -1, 1.3), tilt(0.2, 18, 1.0)))], py=-90,
      hit=[T(73) + 0.34, T(73) + 0.62])
    C(T(75), 'wave', layout='officer_low', title='SHOULDER RADIO', rows=[dict(label='PLAY 1', color='blue', seed=7), dict(label='PLAY 2', color='red', seed=9),
                                                               dict(label='PLAY 3', color='blue', seed=7, p=(t(75) + 0.9, t(75) + 1.8))], play=(t(75) + 0.9, t(75) + 1.8))
    C(T(77), 'car', act=_A(stare(), smile(0.1, 1.4, 0.8)), expr='dead_stare', scale=0.5, cam=dict(mv='push', x=985, y=450, z=1.25))
    C(T(78), 'peep', ppl=[P(O, act=_A(look_side(-2, 0.8, 0.1), snap(w(78, 'back'), 0.8, 0.0), grin(0.3)))], cam=dict(mv='push', x=960, y=470, z=1.1))
    C(T(79), 'bust', who=O, scale=1.15, act=_A(grin(-1), tilt(0.4, 15, 1.0)), cam=dict(mv='fast', x=960, y=520, z=1.0))

    # ============================================================ RULE 3 (209.4 - 278.2): mother on the radio
    C(T(80), 'rule', n=3, bg='street')
    C(T(80, 4.4), 'ins', name='radio', kw=dict(led=1.0), cam=dict(mv='push', x=960, y=520, z=1.1, rate=0.05))
    C(T(82), 'door', ppl=[P(O, path=(T(82) - 0.1, T(82) + 1.3, [DA(0.5, 1.6), DA(0.1, 1.05)]),
                           act=_A(stare(), ex('dead_stare'), lambda a, s: a.set(s.t0 + 1.6, None, 0.6, h_turn=0.3, h_tilt=-14, look_x=0.5, lock=0.0),
                                  creep(0, 4, 0.92)))], py=-120, px=60, z1=1.3)
    C(T(83), 'bust', who=Y, bg='hall', act=_A(ex('shock')), cam=dict(mv='fast', x=960, y=560), hit=t(83) + 0.1)
    C(T(84), 'wave', layout='officer_l', title='SHOULDER RADIO', rows=[dict(label='INCOMING  -  MUM?', color='red', seed=12, p=(t(84), e(85)))], play=(t(85), e(85)))
    C(T(85, 0.3), 'ins', name='radio', kw=dict(led=0.0, talk=1.0), cam=dict(mv='push', x=980, y=500, z=1.25, rate=0.04),
      tags=[(t(85) + 0.4, 'MUM', 1260, 330, 'white', 2.0)])
    C(T(86), 'bust', who=Y, bg='hall', act=_A(ex('sad'), lambda a, s: a.cry(s.t0 + 0.4, None)), cam=dict(mv='push', x=960, y=540))
    C(T(87), 'wave', layout='door', title='SHOULDER RADIO',
      rows=[dict(label='MUM', color='red', seed=12, p=(t(87), e(88)),
                 marker=(clamp((w(87, 'breath') - t(87)) / (e(88) - t(87))) - 0.04, clamp((w(87, 'breath') - t(87)) / (e(88) - t(87))) + 0.1, 'BREATH'))],
      play=(t(87), e(88)))
    C(T(88), 'mumroom', police=False, cam=dict(mv='push', x=520, y=740, z=1.0, rate=0.03), grade=Grade('interior_dim', sat=0.4, exposure=-0.2),
      tags=[(w(88, 'cough'), 'COUGH', 960, 300, 'pill', 2.0)])
    C(T(89), 'ins', name='lock_inside', kw=dict(turn=0.0, chain=1.0), motion=lambda t_: (2 * math.sin(t_ * 31), 1.5 * math.sin(t_ * 23), 0, 0),
      cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.06), tags=[(w(90, 'without'), "DON'T TURN IT", 960, 150, 'alert')])
    C(T(91), 'door', ppl=[P(O, act=_A(ex('sad'), stare(0.0), creep(5, 3, None)),
                           path=[(T(91) + 0.35, T(91) + 1.35, [DA(0.0, 1.0), DA(3.0, 0.55)], 1.0), (T(91) + 2.4, T(91) + 3.5, [DA(3.0, 0.55), DA(0.15, 0.85)], -1.0)])],
      py=-70, hud=disp(w(91, 'emergency'), 'DISPATCH  -  CALL 24-1187', ['EMERGENCY CONTACT: MOTHER', 'NOTE: SUBJECT NOT HIMSELF'], x=1280, y=160))
    C(T(92), 'peep', ppl=[P(O, at='officer_close', act=_A(ex('sad'), tilt(0.4, 12, 1.2)))], cam=dict(mv='push', x=960, y=480))
    C(T(93), 'car', act=_A(down(-2), lambda a, s: a.head_down(s.t0 - 2, s.t0 + 0.8, 1.0), stare(0.8), smile(1.0, 1.6, 0.7)), expr='dead_stare',
      cam=dict(mv='push', x=985, y=450, z=1.15))
    C(T(94), 'peep', ppl=[P(O, act=_A(ex('talk_smile'), hold_prop('radio', 0.0, 1), creep(6, 3, None)))], cam=dict(mv='push', x=960, y=480, z=1.04))
    C(T(96), 'door', ppl=[P(O, at=DA(0.0, 0.95), act=_A(ex('talk_smile'), hold_prop('radio', -0.3, 1), lean(0.2, 1.6, 0.7), creep(10, 4, None)), lean=True)],
      py=-90)
    C(T(97), 'peep', ppl=[P(O, act=_A(stare(), smile(-1, 1, 0.6), hold_prop('radio', 0.0, 1)))], cam=dict(mv='push', x=960, y=500, z=1.05, rate=0.04))
    C(T(98), 'wave', layout='officer_r', title='SHOULDER RADIO', rows=[dict(label='PLAY 1  -  MUM', color='blue', seed=21, p=(t(98), e(98))),
                                                             dict(label='PLAY 2', color='blue', seed=21, p=(t(99), e(99) + 1.6))], play=(t(98), e(99) + 1.6))
    C(T(100), 'wave', layout='radio', title='SHOULDER RADIO', rows=[dict(label='PLAY 1', color='blue', seed=21, marker=(0.54, 0.64, 'COUGH')),
                                                           dict(label='PLAY 2', color='red', seed=21, marker=(0.54, 0.64, 'COUGH'))],
      play=(w(100, 'cough') - 0.58 * 2.6, w(100, 'cough') + 0.42 * 2.6))
    C(T(101), 'ins', name='radio', kw=dict(led=1.0), cam=dict(mv='push', x=960, y=500, z=1.5, rate=0.05), cut='glitch',
      sfx=[(w(101, 'click'), 'radio_click', 0, 0.2, 'outside'), (w(101, 'click') + 0.15, 'glitch', -6, 0.2, 'outside', dict(dur=0.5, amount=0.6))],
      music=[(w(101, 'click') - 0.7, 'silence', 0.0, 0.7)], post=dict(glitch=0.0))
    C(T(102), 'door', ppl=[P(O, path=(T(102) + 0.6, T(102) + 1.6, [DA(0.0, 0.8), DA(-0.2, 1.2)]),
                            act=_A(stare(), lambda a, s: a.hold_up('radio', s.t0 - 2, s.t0 + 0.25, 1), twitch(0.45, 0.8), creep(-6, 4, None)))], py=-60)
    C(T(103), 'door', ppl=[P(O, at=DA(0.2, 0.9), act=_A(ex('polite'), radio(0.0, 0.9), twitch(0.5), smile(0.4, 0.8, 0.7)))], py=-90)
    C(T(104), 'phone', states=[(t(104) - 0.1, 'calling'), (t(105) - 0.1, 'busy')], cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.03))
    C(T(106), 'phone', states=[(t(106) - 0.1, 'calling'), (w(106, 'busy') - 0.2, 'busy')], scale=1.08)
    C(T(107), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), phone_ear(1)), cam=dict(mv='push', x=960, y=560))
    C(T(108), 'peep', ppl=[P(O, at='officer_close', act=_A(ex('talk_smile'), hold_prop('radio', -1.0, 1)))], cam=dict(mv='push', x=960, y=500, z=1.05),
      tags=[(w(108, 'radio'), "DON'T USE THE RADIO", 960, 150, 'alert')])

    # ============================================================ RULE 4 (278.2 - 355.8): the complaint, the double
    C(T(109), 'rule', n=4, bg='hall')
    C(T(111), 'door', ppl=[P(O, path=(T(111) - 0.1, T(111) + 1.0, [DA(0.35, 1.25), DA(-0.15, 0.82)]),
                            act=_A(ex('polite'), lambda a, s: a.set(s.t0 + 1.0, None, 0.8, crouch=0.6, lean=0.35), hold_prop('card', 0.6, -1),
                                   lambda a, s: a.set(s.t0 + 2.0, None, 0.4, look_y=-0.6, h_nod=-0.15)))], py=60, z1=1.2)
    C(w(111, 'mail') - 0.1, 'ins', name='mail_slot', kw=lambda t_, t0=w(111, 'mail'): dict(feed=clamp((t_ - t0 - 0.3) / 2.2), item='complaint', flap=1.0),
      cam=dict(mv='push', x=960, y=600, z=1.0, rate=0.03), sfx=[(w(111, 'mail') + 0.2, 'mail_slot', 0, 0, 'inside', dict(paper=True))])
    C(T(112), 'door', ppl=[P(O, at=DA(-0.1, 0.8), act=_A(ex('polite'), lambda a, s: a.set(s.t0 - 0.5, None, 0.6, crouch=0.6, lean=0.35),
                                                        hold_prop('card', -0.3, -1), creep(6, 3, None)))], py=80, z1=1.15)
    C(T(113), 'ins', name='complaint', kw=dict(highlight='address'), cam=dict(mv='push', x=960, y=380, z=1.3, rate=0.03))
    C(T(114), 'ins', name='complaint', kw=dict(highlight='description'), cam=dict(mv='move', x=880, y=520, z=1.4, x1=1060, y1=540, z1=1.5))
    C(T(115), 'ins', name='complaint', kw=dict(highlight='description'), cam=dict(mv='push', x=820, y=560, z=1.9, rate=0.04))
    C(T(116), 'bust', who=Y, bg='hall', cy=640, act=_A(ex('nervous'), lambda a, s: a.look(s.t0, 0.0, -0.8, 0.3)), cam=dict(mv='push', x=960, y=420, z=1.1))
    C(T(117), 'hall', you_at=(960, 1700, 0.85, 1349), act=_A(ex('fear'), down(0.0, 0.7)), cam=dict(mv='move', x=960, y=480, z=1.0, y1=640, z1=1.08))
    C(T(118), 'ins', name='complaint', kw=dict(highlight=None), motion=lambda t_: (3 * math.sin(t_ * 9), 2 * math.sin(t_ * 7), 0, 0.4 * math.sin(t_ * 5)),
      cam=dict(mv='push', x=960, y=540, z=1.1), sfx=[(t(118) + 0.1, 'paper', -8, 0, 'close', dict(dur=0.8))])
    C(T(119), 'ins', name='complaint_name', cam=dict(mv='creep', x=960, y=540, z=1.0, snap=(t(120) + 0.05, 1.3)), hit=t(120) + 0.05,
      music=[(t(120) - 0.6, 'silence', 0.0, 0.6), (t(120) + 0.05, 'stinger', 0.85)])
    C(T(121), 'ins', name='complaint', kw=dict(highlight='signature'), cam=dict(mv='move', x=900, y=780, z=1.5, x1=1040, y1=800, z1=2.3),
      tags=[(w(121, 'letter'), 'SAME MISTAKE', 960, 200, 'red', 1.8)])
    C(T(122), 'street', doors=doors_open(w(122, 'opens') - 0.2), figures=('driver',),
      ppl=[P(D, act=_A(stare(), ex('dead_stare')), path=(w(122, 'opens') + 0.45, w(122, 'opens') + 3.2, ['car_rear_door', 'gate']), facing=-1.0,
             alpha=lambda t_, k0=w(122, 'opens') + 0.3: clamp((t_ - k0) / 0.35))],
      cam=dict(mv='push', x=1460, y=700, z=1.6, rate=0.04),
      sfx=[(w(122, 'opens'), 'car_door_open', 0, -0.4, 'street')], music=[(t(122), 'riser', 0.5, 4.0)])
    C(T(123), 'door', ppl=[P(D, act=_A(stare(), ex('dead_stare')), path=(t(123) - 0.3, e(124) + 0.6, [DA(1.3, 4.25), 'gate', 'path_mid', 'steps', 'double']), detail=1),
                           P(O, at=DA(-1.0, 1.1), act=_A(stare(), turned(1.4), lambda a, s: a.set(s.t0 + 0.8, None, 0.6, h_turn=0.4), creep(0, 3, None)), track=False)],
      doors=lambda t_: {'rear': 1.0}, figures=('driver',), py=-10, z1=1.4, box=True,
      sfx=[(t(123) - 0.2, 'car_door_close', -6, -0.5, 'street')])
    C(T(124), 'peep', ppl=[P(D, act=_A(stare(), ex('dead_stare'), lean(e(124) + 0.65 - T(124), 1.4, 0.8)), lean=True,
                            path=(t(123) - 0.3, e(124) + 0.6, ['car_rear_door', 'gate', 'path_mid', 'steps', PA(0.1, 0.72)]))],
      figures=('driver',), cam=dict(mv='push', x=960, y=600, z=1.0, rate=0.045))
    C(T(125), 'hands', who=D, bg='porch', rub=False, thread=True, cam=dict(mv='push', x=700, y=620, z=1.25, rate=0.035))
    C(T(126), 'peep', ppl=[P(D, act=_A(stare(), down(-2, 0.5), lean(0.4, 1.2, 0.7)), lean=True, path=(t(126) - 0.2, w(126, 'face') + 0.1, ['steps', PA(0.25, 0.72)]))],
      figures=('driver',), cam=dict(mv='push', x=1000, y=520, z=1.05, rate=0.045), music=[(w(126, 'face') - 1.3, 'silence', 0.0, 1.25)])
    C(w(126, 'face') - 0.05, 'bust', who=D, cx=960, cy=590, scale=1.05, act=_A(stare(-1), smile(0.6, 2.0, 0.6), creep(6, 3, None)),
      cam=dict(mv='push', x=960, y=560, z=1.0, rate=0.035, snap=(w(126, 'face') + 0.02, 1.12)), hit=w(126, 'face'),
      music=[(w(126, 'face'), 'sub_drop', 0.9)], sfx=[(w(126, 'face'), 'sub_drop', -2, 0, None)])
    C(T(128), 'bust', who=D, cx=1000, scale=1.08, cy=590, act=_A(stare(-1), lambda a, s: a.set(s.t0 - 2, None, 0.1, turn=0.0, h_turn=0.18), creep(5, 3, None)),
      cam=dict(mv='push', x=980, y=580, z=1.04, rate=0.03),
      tags=[(w(128, 'scar'), 'SCAR', -230, -150, 'red', 1.8, dict(at=(1000 - 66 * 1.08, 590 + 172 * 1.08)))])
    C(T(129), 'hands', who=D, bg='porch', rub=False, ring=1, cam=dict(mv='push', x=1010, y=640, z=1.35, rate=0.035),
      tags=[(w(129, 'wrong'), 'WRONG HAND', 120, -260, 'red', 1.6, dict(at=ring_at(1)))])
    C(T(130), 'bust', who=D, act=_A(stare(-1), smile(0.6, 3.4, 0.8)), cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.03))
    C(T(131), 'peep', ppl=[P(O, at='officer2', act=_A(stare(), look_side(-2, 0.7, 0.1)), track=False),
                            P(D, at='double', act=_A(stare(), sway(9, 2.2, 4),
                                                     lambda a, s: a.set(s.t0 + 0.3, s.t0 + 1.0, 0.18, h_turn=0.85, lock=0.0, look_x=0.8),
                                                     jerk_at(1.25, 1.0), twitch(1.9), lean(1.3, 0.8, 0.6)), lean=True)], cam=dict(mv='push', x=1080, y=480, z=1.1))
    C(T(132), 'bust', who=D, act=_A(stare(-1), ex('angry', 0.0)), cam=dict(mv='push', x=960, y=520, z=1.05, rate=0.035))
    C(T(134), 'door', ppl=[P(O, at='officer2', act=_A(stare(), turned(0.6), creep(6, 3, None)), track=False),
                            P(D, path=(T(134) - 0.1, T(134) + 0.9, [DA(0.75, 1.15), DA(0.2, 0.72)]), act=_A(ex('angry'), pt(0.6, 1.5, -1, 0.0), lean(1.0, 0.8, 0.5)),
                              lean=True)], px=60, py=-40)
    C(T(135), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), down(0.0, 0.8)), cam=dict(mv='push', x=960, y=600))
    C(T(136), 'ins', name='complaint_verified', cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.035),
      tags=[(w(136, 'empty'), 'EMPTY', 1200, 640, 'red', 1.6)], music=[(w(136, 'empty'), 'hit', 0.6)])
    C(T(137), 'bust', who=O, cy=440, act=_A(stare(), hold_prop('notebook', 0.3, 1)), cam=dict(mv='push', x=980, y=640, z=1.05),
      sfx=[(w(137, 'pen') + 0.3, 'pen_click', -2, 0.1, 'outside', dict(n=1))])
    C(T(138), 'bust', who=O, scale=1.15, act=_A(grin(-0.6), tilt(0.5, 16, 1.2)), cam=dict(mv='push', x=960, y=520, z=1.0, rate=0.04))
    C(T(140), 'peep', ppl=[P(O, at='officer_close', act=_A(grin(-1)))], cam=dict(mv='push', x=960, y=440, z=1.0, rate=0.05))

    # ============================================================ RULE 5 (355.8 - 435.5): the questions
    C(T(141), 'rule', n=5, bg='porch')
    C(T(143), 'door', ppl=[P(O, path=(T(143) + 0.2, T(143) + 1.4, [DA(-0.9, 1.25), DA(-0.45, 0.9)]), act=_A(ex('polite'), hold_prop('notebook', 1.2, 1), creep(6, 4, None))),
                            P(D, at='double', act=_A(ex('polite'), lambda a, s: a.nervous_glance(s.t0 + 0.6, 2, -1), sway(5, 3.0)), track=False)],
      px=-60, py=-40)
    C(T(144), 'ins', name='notebook', cam=dict(mv='push', x=960, y=540, z=1.05),
      sfx=[(t(144) + 0.2, 'paper', -10, 0.1, 'outside', dict(dur=0.7)), (t(144) + 0.8, 'pen_click', -8, 0.1, 'outside')])
    C(T(145), 'bust', who=D, act=_A(ex('polite'), nod(0.3), nod(1.0)), cam=dict(mv='push', x=960, y=540))
    C(T(146, -0.3), 'peep', ppl=[P(O, act=_A(ex('talk_smile'), tilt(0.3, 12, 1.2), creep(5, 3, None))),
                                    P(D, at='double', act=_A(stare(), sway(6, 2.6)), track=False)], cam=dict(mv='push', x=1000, y=490, z=1.08))
    C(T(147), 'kitchen', cam=dict(mv='move', x=700, y=420, x1=760, y1=440, z=1.0, z1=1.08, d=2.3, opt=1.6),
      without=('room', 'headlights', 'pendant_light', 'pendant', 'table'))
    C(T(148, -0.1), 'bust', who=D, act=_A(ex('polite'), stare(0.0)), cam=dict(mv='push', x=960, y=540, z=1.05),
      hud=lambda cv, t_, t0=t(148): H.speech_bubble(cv, ['*Green.*'], 1340, 300, t_ - t0))
    C(T(150), 'ins', name='tiles', cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.03), tags=[(w(150, 'blue'), 'BLUE', 960, 200, 'white', 1.6)])
    C(T(151), 'bust', who=Y, bg='hall', act=_A(ex('nervous'), lambda a, s: a.set(s.t0 + 0.5, None, 0.4, m_open=0.35), lambda a, s: a.set(t(152), None, 0.5, breath=1.0)),
      cam=dict(mv='move', x=960, y=600, z=1.0, y1=560, z1=1.35), sfx=[(t(152) + 0.3, 'breath', -4, 0, 'close', dict(kind='held', dur=1.4))],
      music=[(t(152) + 0.2, 'silence', 0.0, 1.2)])
    C(T(153), 'peep', ppl=[P(O, at='officer2', act=_A(ex('polite')), track=False),
                           P(D, at='double', act=_A(stare(), look_side(-2, -0.8, 0.1), lambda a, s: a.set(w(153, 'stops'), None, 0.3, h_turn=0.0, lock=1.0)))],
      cam=dict(mv='push', x=1100, y=500, z=1.15, rate=0.03))
    C(T(154), 'bust', who=D, scale=1.25, act=_A(stare(-1), ex('dead_stare')), cam=dict(mv='creep', x=960, y=520, z=1.05))
    C(T(156), 'door', ppl=[P(O, at=DA(-0.5, 1.05), act=_A(stare(), smile(0.2, 1.8, 0.7), lean(0.1, 1.6, 0.9), creep(8, 3, None)), lean=True, aim=(900, 470)),
                            P(D, at='double', act=_A(stare(), sway(6, 2.8)), track=False)], px=-100, py=-40)
    C(T(157), 'ins', name='notebook', cam=dict(mv='push', x=900, y=500, z=1.35, rate=0.03),
      sfx=[(t(157) + 0.15, 'paper', -10, 0.1, 'outside', dict(dur=0.6)), (t(157) + 0.9, 'pen_click', -9, 0.1, 'outside')])
    C(T(158), 'bust', who=D, act=_A(stare(), ex('talk_smile')), cam=dict(mv='push', x=960, y=540, z=1.1),
      hud=lambda cv, t_, t0=t(158) + 0.3: H.speech_bubble(cv, ['Westbrook High.'], 1340, 300, t_ - t0))
    C(T(159), 'mumroom', ppl=[P(M, at='mum_standing', act=_A(ex('sad'), look_side(-2, -0.5, 0.1)))], cam=dict(mv='push', x=1100, y=560, z=1.1))
    C(T(160), 'bust', who=D, act=_A(stare(), smile(0.2, 1.6, 0.6)), cam=dict(mv='push', x=960, y=540))
    C(T(161), 'bust', who=Y, bg='hall', act=_A(ex('sweaty'), twitch(1.2)), cam=dict(mv='hand', x=960, y=560, z=1.05),
      sfx=[(t(161) + 0.3, 'breath', -5, 0, 'close', dict(kind='nervous', dur=3.0)), (t(161), 'heartbeat', -8, 0, None, dict(bpm=80, bpm_end=96, dur=4.5))])
    C(T(162), 'peep', ppl=[P(D, at='double', act=_A(stare(), ex('dead_stare')))], cam=dict(mv='push', x=1040, y=470, z=1.2, rate=0.04),
      tags=[(t(162), "DON'T", 960, 150, 'alert')], music=[(t(162), 'hit', 0.7)])
    C(T(163), 'peep', ppl=[P(O, at='officer2', act=_A(stare()), track=False), P(D, at='double', act=_A(ex('nervous'), twitch(0.5, 1.4, 2.2, 2.6)))],
      cam=dict(mv='push', x=1080, y=480, z=1.15), sfx=[(t(163) + 1.4, 'footsteps_porch', -8, 0.2, 'outside', dict(n=1, creak=0.8, weight=0.5))])
    C(T(164), 'hands', who=D, bg='porch', ring=0, rub=True, cam=dict(mv='push', x=960, y=640, z=1.15))
    C(T(165), 'door', ppl=[P(O, at='officer2', act=_A(stare(), lambda a, s: a.set(s.t0 + 0.5, None, 0.9, h_turn=0.45, lock=0.0, look_x=0.7), creep(5, 3, None)),
                              track=False),
                            P(D, path=(T(165) + 0.1, T(165) + 1.0, [DA(0.75, 1.15), DA(0.5, 0.9)]),
                              act=_A(ex('nervous'), lambda a, s: a.nervous_glance(s.t0 + 1.2, 3, -1, 1.8), tremble(0.6)))], px=100, py=-40, z1=1.22)
    C(T(166), 'hall', you=False, cam=dict(mv='move', x=1250, y=430, z=1.0, x1=1480, y1=340, z1=1.5, d=1.5), without=('near_frame',),
      sfx=[(t(166) + 0.4, 'footsteps_wood_inside', -8, 0.3, 'inside', dict(n=3, rate=1.4))])
    C(T(167), 'ins', name='photo', cam=dict(mv='push', x=960, y=540, z=1.05, snap=(t(167) + 0.2, 1.2)))
    C(T(168), 'door', ppl=[P(O, at='officer2', act=_A(ex('calm_smirk'), lambda a, s: a.set(s.t0 + 0.3, None, 0.5, h_turn=0.45, lock=0.0), creep(5, 3, None))),
                             P(D, at='double', act=_A(ex('nervous'), lambda a, s: a.nervous_glance(s.t0 + 0.4, 2, -1)), track=False)], px=60, py=-40)
    C(T(169), 'bust', who=D, act=_A(stare(), ex('polite', 0.0)), cam=dict(mv='push', x=960, y=540, z=1.05),
      hud=lambda cv, t_, t0=t(170): H.speech_bubble(cv, ['*My mother.*'], 1340, 300, t_ - t0))
    C(T(171), 'ins', name='photo', cam=dict(mv='push', x=960, y=500, z=1.4, rate=0.04), music=[(t(171), 'stinger', 0.8)], hit=t(171))
    C(T(172), 'kitchen', ppl=[P(Y, at='you_seated', act=_A(ex('fear'), lambda a, s: a.set(s.t0, None, 0.6, hl_down=260, hr_down=260, hl_fwd=150, hr_fwd=150,
                                                                                         hl_shape='fist', hr_shape='fist', jitter=0.6)))],
      cam=dict(mv='push', x=960, y=560, z=1.05, rate=0.04))
    C(T(173), 'peep', ppl=[P(O, at='officer_close', act=_A(stare(), ex('dead_stare')))], cam=dict(mv='creep', x=960, y=480, z=1.1))
    C(T(174), 'bust', who=O, cy=400, act=_A(stare(), lambda a, s: a.press_bodycam(w(174, 'turns'), on=False)), cam=dict(mv='push', x=1000, y=660, z=1.15),
      tags=[(w(174, 'off'), 'REC  OFF', 1320, 760, 'white', 1.6)])
    C(T(175), 'door', ppl=[P(O, at=DA(0.2, 0.85), act=_A(ex('angry'), knk(0.0, 3, 0.24, -1, 1.4), lean(0.95, 0.8, 0.5), creep(-8, 4, None)), lean=True)],
      py=-80, hit=[T(175) + 0.34, T(175) + 0.58, T(175) + 0.82])
    C(T(177), 'bust', who=D, act=_A(ex('nervous'), lambda a, s: a.set(s.t0 + 0.5, None, 1.0, sweat=1.0)), cam=dict(mv='push', x=960, y=540, z=1.05))

    # ============================================================ RULE 6 (435.5 - 522.3): the key, the countdown, the bag
    C(T(178), 'rule', n=6, bg='street')
    C(T(180), 'bust', who=O, act=_A(ex('angry'), stare(0.0)), cam=dict(mv='creep', x=960, y=530, z=1.05))
    C(T(181), 'door', ppl=[P(O, path=(T(181) + 0.1, T(181) + 1.1, [DA(-0.9, 1.25), DA(-0.35, 0.95)]), act=_A(ex('talk_smile'), pt(1.2, 1.4, 1, 0.6, -0.6), creep(7, 4, None))),
                            P(D, at='double', act=_A(stare(), smile(0.5, 2.0, 0.6), sway(5, 3.1)), track=False)], px=-40, py=-40)
    C(T(182), 'door', ppl=[P(O, at=DA(-0.1, 0.85), act=_A(ex('talk_smile'), pt(0.0, 1.2, -1, 0.0), lean(0.0, 0.9, 0.9), creep(10, 3, None)), lean=True)],
      py=-90)
    C(T(183), 'peep', ppl=[P(D, at='double', act=_A(ex('polite'), smile(0.2, 1.0, 0.4)))], cam=dict(mv='push', x=1060, y=480, z=1.15))
    C(T(184), 'street', cam=dict(mv='push', x=1640, y=650, z=2.5, rate=0.03))
    C(T(185), 'door', ppl=[P(O, at=DA(0.0, 0.95), act=_A(ex('talk_smile'), pt(0.1, 1.2, -1, 0.0), pt(0.1, 1.2, 1, 0.0), lean(0.5, 1.0, 0.6)), lean=True)], py=-90)
    C(T(186), 'peep', ppl=[P(O, act=_A(stare(), lean(0.2, 2.6, 0.7)), lean=True)], cam=dict(mv='push', x=960, y=480, z=1.0, rate=0.03))
    C(T(187), 'bust', who=O, scale=1.1, act=_A(stare(), ex('calm_smirk')), cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.035))
    C(w(187, 'homeowner') - 0.1, 'door', ppl=[P(O, at='officer2', act=_A(ex('calm_smirk'), lambda a, s: a.set(s.t0 + 0.6, None, 0.8, h_turn=0.5, lock=0.0),
                                                                   creep(5, 3, None)), track=False),
                                               P(D, path=(w(187, 'homeowner') + 0.3, w(187, 'homeowner') + 2.0, [DA(0.75, 1.15), DA(0.3, 0.75)]),
                                                 act=_A(stare(), smile(0.0, 2.6, 0.9), creep(6, 3, None)))], px=140, py=-60, z1=1.25)
    C(T(188), 'door', ppl=[P(O, at='officer2', act=_A(stare(), creep(4, 3, None)), track=False),
                            P(D, at=DA(0.35, 0.8), act=_A(stare(), hold_prop('key', 0.5, 1), lean(1.2, 1.2, 0.5), creep(6, 3, None)), lean=True)], px=100, py=-40,
      sfx=[(t(188) + 0.6, 'key_in_lock', -10, 0.2, 'outside')])
    C(T(189), 'ins', name='key_outside', kw=lambda t_, t0=t(190): dict(key_in=0.4 * clamp((t_ - t0 - 0.4) / 1.6)), cam=dict(mv='push', x=960, y=540, z=1.1, snap=(t(189) + 0.1, 1.15)),
      sfx=[(t(190) + 0.6, 'key_in_lock', -4, 0.1, 'outside')], music=[(t(190), 'pulse_on', 0.5)])
    C(w(190, 'turn') - 0.1, 'ins', name='lock_inside', kw=dict(turn=0.0, chain=1.0), cam=dict(mv='push', x=960, y=540, z=1.2, rate=0.04))
    C(T(191), 'hall', act=_A(ex('fear'), back_view()), cam=dict(mv='fast', x=960, y=520), tags=[(t(191), "DON'T TOUCH IT", 960, 150, 'alert')])
    C(T(192), 'bust', who=O, scale=1.15, act=_A(ex('shout')), cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.05), hit=w(192, 'force'),
      post=dict(exposure=-0.1))
    C(T(193), 'door', ppl=[P(O, at=DA(0.0, 0.8), act=_A(ex('angry'), lean(0.0, 1.0, 1.0), tilt(0.3, -14, 1.0), creep(0, 4, None)), lean=True)], py=-110)
    CDT = [t(193) + 0.95 + k_ * 0.66 for k_ in range(11)]                 # the countdown numbers: the door jolts on each
    C(T(194), 'hall', you=False, feet=lambda t_: [0.47 + 0.004 * math.sin(t_ * 9), 0.55], flick=[(c_, 0.12) for c_ in CDT],
      cam=dict(mv='push', x=960, y=560, z=1.1, rate=0.05, hit=[c_ for c_ in CDT if T(194) <= c_ < T(195)]))
    C(T(195), 'bust', who=Y, bg='hall', act=_A(ex('fear'), lambda a, s: a.set(s.t0, None, 0.25, eye_open=1.15, pupil=0.5, wide=0.6, sweat=1.0), tremble(1.2)),
      cam=dict(mv='hand', x=960, y=560, z=1.1, hit=[c_ for c_ in CDT if T(195) <= c_ < T(196)]))
    C(T(196), 'peep', ppl=[P(O, at='officer_close', act=_A(stare(), ex('dead_stare')))], cam=dict(mv='push', x=960, y=440, z=1.1, rate=0.05))
    C(T(197), 'hall', you=False, feet=lambda t_: [0.47 + 0.01 * math.sin(t_ * 2), 0.55], flick=[(c_, 0.12) for c_ in CDT],
      cam=dict(mv='push', x=960, y=640, z=1.3, rate=0.05, hit=[c_ for c_ in CDT if T(197) <= c_ < T(198)]),
      sfx=[(w(197, 'breathing'), 'breath', -4, 0, 'outside', dict(kind='panting', dur=2.4))])
    C(T(198), 'street', doors=doors_open(w(198, 'out') - 0.3, 'front'), figures=('back',),
      ppl=[P(O2, at='car_front_door', act=_A(ex('dead_stare')), seed=3)], cam=dict(mv='push', x=1560, y=640, z=1.9, rate=0.03),
      sfx=[(w(198, 'out'), 'car_door_open', -2, -0.4, 'street'), (e(198) + 0.2, 'car_door_close', -4, -0.4, 'street')],
      )
    C(T(199), 'door', figures=('back',), ppl=[P(O2, act=_A(ex('dead_stare'), hold_prop('card', -1, 1)),
                                                 path=(t(199) - 0.4, e(199) + 0.8, ['gate', 'path_mid', 'steps', DA(-0.6, 1.3)]), detail=1),
                                               P(O, at=DA(1.1, 0.95), act=_A(stare(), turned(1.5), creep(0, 3, None)), track=False)], py=-20, z1=1.4)
    C(T(200), 'ins', name='keys_neighbour', cam=dict(mv='move', x=960, y=540, z=1.0, x1=1120, y1=600, z1=1.7, snap=(w(201, 'orange'), 1.15)),
      sfx=[(t(200) + 0.3, 'paper', -10, 0, 'outside', dict(dur=1.0))], tags=[(w(201, 'orange'), 'ORANGE KEY RING', 960, 190, 'white', 1.8)])
    C(T(202), 'street', police=dict(mode='sweep', strength=0.6), cam=dict(mv='move', x=900, y=560, z=1.1, x1=280, y1=520, z1=1.35))
    C(T(203), 'bust', who=O2, act=_A(ex('calm_smirk'), stare(0.0), tilt(0.2, 4, 1.0), creep(3, 2, None)), cam=dict(mv='push', x=960, y=540))
    C(T(205), 'door', ppl=[P(O, act=_A(ex('angry'), lambda a, s: a.set(s.t0 + 0.2, None, 0.5, h_turn=-0.55, lock=0.0, look_x=-0.7),
                                   lambda a, s: a.point(s.t0 + 0.4, s.t1, 1, -1.0, 0.3), creep(-5, 3, None))),
                            P(O2, at='officer2', act=_A(stare(), frz(0.6, 2.4)), track=False)], px=-60, py=-40)
    C(T(206), 'peep', ppl=[P(O2, at='officer2', act=_A(stare(), ex('dead_stare'))), P(O, act=_A(stare()))], cam=dict(mv='push', x=820, y=480, z=1.15))
    C(T(207), 'bust', who=O2, scale=1.1, act=_A(stare(), smile(0.3, 1.6, 0.9)), cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.035))
    C(T(208), 'door', ppl=[P(O, act=_A(stare(), lean(0.2, 1.9, 0.45), tilt(0.2, 12, 1.8)), lean=True),
                            P(O2, at='officer2', act=_A(stare(), lean(0.2, 1.9, 0.45), tilt(0.2, 12, 1.8)), lean=True, track=False, aim=(700, 470)),
                            P(D, at='double', act=_A(stare(), lean(0.2, 1.9, 0.45), tilt(0.2, 12, 1.8)), lean=True, track=False, aim=(1220, 470))],
      py=-40, music=[(t(208), 'silence', 0.0, 1.6)])
    C(T(209), 'street', ppl=[P(O, act=_A(stare())), P(O2, at='officer2', act=_A(stare())), P(D, at='double', act=_A(stare()))],
      cam=dict(mv='push', x=930, y=600, z=1.6, rate=0.025), figures=())
    C(T(210), 'door', ppl=[P(O, at=DA(-0.4, 1.2), act=_A(stare(), creep(5, 3, None)), track=False),
                            P(D, act=_A(stare(), lambda a, s: a.hold_up('key', s.t0 - 2, s.t0 + 0.8, 1), smile(0.6, 1.4, 0.8)),
                              path=[(T(210) + 1.7, T(210) + 3.4, [DA(0.4, 0.9), DA(0.3, 1.9)], 2.0)])], px=80, py=-40)
    C(T(211, -0.4), 'bust', who=D, act=_A(stare(), smile(0.2, 1.2, 0.7)), cam=dict(mv='push', x=960, y=540, z=1.05))
    C(T(213), 'bust', who=O, cy=400, act=_A(stare(), smile(0.3, 1.4, 0.8), lambda a, s: a.press_bodycam(s.t0 + 0.3, on=True)), cam=dict(mv='push', x=1000, y=640, z=1.1),
      tags=[(t(213) + 0.8, 'REC', 1320, 760, 'red', 1.4)])

    # ============================================================ RULE 7 (522.3 - 681): the call, mum's door
    C(T(214), 'rule', n=7, bg='hall')
    C(T(214, 4.5), 'ins', name='lock_inside', kw=lambda t_, t0=T(214, 4.5): dict(turn=1.0 - ease_in_out(clamp((t_ - t0 - 0.1) / 0.6)), chain=1.0),
      cam=dict(mv='push', x=960, y=540, z=1.08, rate=0.05), sfx=[(T(214, 4.65), 'lock_turn', -4, 0, 'close')])
    C(T(216), 'street', figures=('driver',), doors=lambda t_: {'rear': 1.0},
      ppl=[P(D, act=_A(stare()), path=(t(216) - 0.2, e(217) + 0.3, ['double', 'steps', 'path_mid', 'gate', 'car_rear_door'])),
           P(O, act=_A(stare()), path=(t(216) + 0.4, e(217) + 1.5, ['officer', 'steps', 'path_mid', 'gate']), seed=2)],
      cam=dict(mv='push', x=1100, y=640, z=1.25, rate=0.025))
    C(T(217), 'street', figures=('driver', 'back'), doors=doors_open(t(217) - 2, 'rear', 0.3, w(217, 'back')), cam=dict(mv='push', x=1470, y=700, z=1.8, rate=0.03),
      sfx=[(w(217, 'back') + 0.4, 'car_door_close', -2, -0.4, 'street')])
    C(T(218), 'car', act=_A(stare(), lambda a, s: a.set(s.t0, w(218, 'bedroom') + 0.5, 0.35, look_y=-0.8, h_nod=-0.15, lock=0.0)), expr='dead_stare', scale=0.48,
      cam=dict(mv='push', x=985, y=450, z=1.2, rate=0.04))
    C(w(218, 'bedroom') - 0.1, 'street', bedroom=1.0, cam=dict(mv='move', x=1060, y=470, z=1.6, x1=1090, y1=450, z1=1.9), police=dict(mode='sweep', strength=0.8),
      music=[(w(218, 'bedroom'), 'stinger', 0.6)])
    C(T(219), 'living', drive=('out', w(219, 'watching'), e(219) + 1.0, 1.2, 15.0), cam=dict(mv='push', x=1060, y=600, z=1.1, rate=0.03),
      sfx=[(w(219, 'watching'), 'car_pass', -4, 0.3, 'street', dict(dist=2.0, direction=1)), (e(219) - 0.5, 'siren_far', -12, 0.6, 'street', dict(dur=6, dist=3))])
    # ---- the call (v2.1): varied coverage, pace building: phone UI, mum's room wide / medium / over her shoulder, her
    # hall, mum's street with the two men coming up her path, your hall pacing hand-held, inserts, eye close-ups, and
    # busts in rotating framings; one scream only (T(278)), the double's crying grin intercut as the strongest face.
    C(T(220), 'phone', full=True, states=[(t(220), 'calling'), (w(221, 'answers'), 'connected')], wave='#5b7fe0', prate=0.05)
    C(w(221, 'answers') - 0.1, 'mumroom', ppl=[P(M, at='mum_chair', act=_A(ex('nervous'), lambda a, s: a.sit(s.t0 - 2), phone_ear(1, 0.15), tremble(0.4)))],
      ring=lambda t_, k0=w(221, 'answers'): 1.0 if t_ < k0 else 0.0, cam=dict(mv='push', x=520, y=640, z=1.0, rate=0.04, dx=40, opt=1.45))
    C(T(222), 'bust', who=M, bg='mumroom', act=_A(ex('sad'), phone_ear(1), tremble(0.5)))
    C(T(223), 'hall', you_at=HA(0.35, 1.7), act=_A(ex('nervous'), phone_ear(1), lambda a, s: a.walk(s.t0 + 0.1, s.t1 + 0.4, -260.0, 300.0, facing=1.0, surface='inside'),
                                                  tremble(0.6)), cam=dict(mv='hand', x=1000, y=520, z=1.05, dx=120))
    C(T(224), 'bust', who=M, bg='mumroom', cx=960, cy=640, scale=1.75, ecu=True, act=_A(ex('sad'), stare(-1), lambda a, s: a.freeze(s.t0 + 0.2, s.t1)),
      cam=dict(mv='creep', x=960, y=560, z=1.0), music=[(t(224), 'silence', 0.0, 1.3)])
    C(T(225), 'mumroom', ppl=[P(M, at='mum_chair', act=_A(ex('nervous'), lambda a, s: a.sit(s.t0 - 2), phone_ear(1, -2), lambda a, s: a.set(s.t0 + 0.2, None, 0.5, lean=0.25),
                                                       tremble(0.4)))], cam=dict(mv='push', x=470, y=600, z=1.0, rate=0.05, dx=-30, opt=1.9))
    C(T(226), 'phone', full=True, states=[(t(221), 'connected')], wave='#5b7fe0', prate=0.06, pshake=9.0, x=980,
      tags=[(t(226) + 0.6, 'MUM  -  CONNECTED', 960, 150, 'dark', 1.8)])
    C(T(227), 'mumroom', ppl=[P(M, at='mum_standing', act=_A(ex('nervous'), phone_ear(1)), path=(t(227) + 0.1, t(227) + 1.9, ['mum_standing', MA(1.25, 1.65)]), facing=1.0)],
      cam=dict(mv='drift', x=1080, y=560, z=1.15, dx=160))
    C(T(228), 'door', ir=True, car=True, figures=('driver',), ppl=[P(D, path=(T(228) + 0.2, T(228) + 2.6, ['path_mid', 'steps', DA(0.1, 0.8)]),
                                                                    act=_A(stare(), smile(2.0, 2.0, 1.0), lean(2.8, 1.2, 0.8)), lean=True)], py=-60,
      post=dict(sat=0.0), hud=lambda cv, t_: H.tag(cv, 'EARLIER', 960, 220, 'dark'))
    C(T(229), 'bust', who=O, act=_A(ex('talk_smile'), phone_ear(-1), creep(6, 3, None)), post=dict(sat=0.5))
    C(T(230), 'ins', name='notebook', cam=dict(mv='push', x=900, y=480, z=1.35), post=dict(sat=0.5))
    C(T(231), 'street', police=False, car=False, cam=dict(mv='push', x=960, y=520, z=1.2, rate=0.04), post=dict(sat=0.4))
    C(T(232), 'ins', name='photo', cam=dict(mv='push', x=1080, y=520, z=1.1))
    C(T(233), 'bust', who=Y, bg='hall', cx=960, cy=640, scale=1.7, ecu=True, act=_A(ex('sad'), lambda a, s: a.set(s.t0 + 0.15, None, 0.25, eye_open=0.0, blink=1.0)),
      cam=dict(mv='creep', x=960, y=560, z=1.0))
    C(T(234), 'hall', you_at=HA(-0.2, 1.4), act=_A(ex('nervous'), phone_ear(1), turned(-0.8), lambda a, s: a.turn(s.t0 + 0.9, 0.3, 0.6), tremble(0.7)),
      cam=dict(mv='hand', x=820, y=500, z=1.12, dx=-60))
    C(T(235), 'mumroom', ppl=[P(M, at='mum_standing', act=_A(ex('nervous'), phone_ear(1), lambda a, s: a.set(s.t0 + 0.4, None, 0.5, h_turn=-0.3)))],
      cam=dict(mv='push', x=1200, y=520, z=1.0, rate=0.045, opt=1.75))
    C(T(237), 'mumext', drive=('in', t(237) - 0.3, t(237) + 2.6, -14.0, 4.2), police=False, cam=dict(mv='push', x=1000, y=640, z=1.15, rate=0.04),
      sfx=[(t(237), 'car_pass', -8, -0.3, 'phone', dict(dist=2.5, direction=1))])
    C(T(238), 'mumext', police=dict(mode='strobe'), figures=('driver',),
      ppl=[P(O, path=(t(238) - 0.6, e(238) + 1.0, ['car_front_door', 'gate', 'path_mid']), act=_A(stare())),
           P(D, path=(t(238) - 0.2, e(238) + 1.6, ['car_rear_door', 'gate', 'path_mid']), act=_A(stare(), smile(1.0, 2.0, 0.8)))],
      cam=dict(mv='push', x=980, y=640, z=1.35, rate=0.04, dx=-60))
    C(T(239), 'hall', act=_A(ex('fear'), phone_ear(1), back_view(), tremble(0.6)), cam=dict(mv='pull', x=960, y=540, z=1.0))
    C(T(240), 'mumroom', ppl=[P(M, at='mum_standing', act=_A(ex('nervous'), phone_ear(1), look_side(t(240) + 0.6, -0.8)))],
      cam=dict(mv='push', x=1300, y=540, z=1.25, rate=0.04), sfx=[(w(240, 'quiet') - 0.2, 'tv_off', -4, 0, 'phone')], music=[(w(240, 'quiet'), 'silence', 0.0, 1.6)])
    C(T(241), 'bust', who=M, bg='mumroom', act=_A(ex('whisper'), phone_ear(1), tremble(0.4)), cam=dict(mv='creep', x=960, y=560))
    kn2 = w(242, 'knocking')
    C(T(242), 'mumext', police=dict(mode='strobe'), figures=('driver',),
      ppl=[P(O, at='door', act=_A(stare(), knk_at(kn2 + 0.05, 3, 0.33, 1, 1.2), creep(5, 3, None))),
           P(D, at=(lambda a_: (a_[0] - 160, a_[1] + 6, a_[2], a_[3]))(MX('door')), act=_A(stare(), sway(6, 2.6)))],
      cam=dict(mv='push', x=1080, y=600, z=1.9, rate=0.045, hit=[kn2 + 0.05, kn2 + 0.38, kn2 + 0.71]), music=[(kn2, 'hit', 0.7)])
    C(T(243), 'bust', who=Y, bg='hall', act=_A(ex('shout'), phone_ear(1), tremble(1.0)), cam=dict(mv='fast', x=960, y=560), cut='static')
    C(T(244), 'mumroom', ppl=[P(M, act=_A(ex('nervous'), phone_ear(1)), path=(t(244) + 0.4, e(244) + 0.3, [MA(-0.2, 1.05), MA(0.9, 1.75)]), facing=1.6)],
      cam=dict(mv='drift', x=860, y=520, z=1.1, dx=200))
    C(T(245), 'mumroom', ppl=[P(M, act=_A(ex('nervous'), phone_ear(1)), path=(t(245) - 0.2, e(245) + 0.6, [MA(0.9, 1.75), MA(1.3, 2.05)]), facing=1.4)],
      cam=dict(mv='push', x=1330, y=760, z=1.0, rate=0.045, opt=1.6, dx=60), sfx=[(t(245) + 0.3, 'footsteps_wood_inside', -10, 0.3, 'phone', dict(n=4, rate=1.6))])
    C(T(246), 'curtain', t_open=w(246, 'scrape') - 0.15, sfx=[(w(246, 'scrape') - 0.1, 'door_creak', -12, 0.3, 'phone', dict(dur=0.6))])
    C(T(247), 'mumext', ppl=[P(O, at='door', act=_A(stare(), creep(6, 3, None))), P(D, at='window', act=_A(stare(), lean(0.5, 2.0, 0.4), smile(1.0, 1.6, 0.7)))],
      sil=True, cam=dict(mv='push', x=700, y=600, z=1.9, rate=0.045), music=[(t(247), 'silence', 0.0, 2.0)])
    C(T(248), 'bust', who=M, bg='mumroom', no_view=True, act=_A(ex('sad'), phone_ear(1), lambda a, s: a.cry(s.t0 + 0.4), hand_mouth(0.5, None), tremble(0.6)))
    C(T(249), 'mumext', ppl=[P(D, at='window', act=_A(stare(), smile(-0.5, 1.0, 0.9), lambda a, s: a.cry(s.t0 - 1, None, smile=True)))], sil=True,
      cam=dict(mv='push', x=660, y=560, z=2.5, rate=0.05))
    C(T(250), 'bust', who=D, bg='mumext', cx=940, scale=1.06, cy=600, act=_A(stare(), lambda a, s: a.set(s.t0 - 2, None, 0.1, h_turn=0.2), creep(6, 3, None)),
      cam=dict(mv='move', x=940, y=560, z=1.02, y1=600, z1=1.1),
      tags=[(t(250) + 0.3, 'SCAR', -230, -150, 'red', 1.4, dict(at=(940 - 66 * 1.06, 600 + 172 * 1.06)))])
    C(T(251), 'hands', who=Y, bg='hall', ring=-1, rub=False, cam=dict(mv='push', x=860, y=620, z=1.3, rate=0.05),
      tags=[(t(251) + 0.05, 'RING', -120, -230, 'white', 1.2, dict(at=ring_at(-1)))])
    C(T(252), 'hall', you_at=HA(0.3, 1.6), act=_A(ex('sweaty'), phone_ear(1), lambda a, s: a.walk(s.t0, s.t1 + 0.3, 260.0, -200.0, facing=-1.0, surface='inside'),
                                                 tremble(0.8)), cam=dict(mv='hand', x=980, y=520, z=1.1, dx=-120))
    C(T(253), 'phone', full=True, states=[(t(221), 'connected')], wave='#e0444c', prate=0.05, pshake=7.0,
      sfx=[(t(253) + 0.2, 'breath', -6, 0, 'phone', dict(kind='nervous', dur=1.4))])
    C(T(254), 'hands', who=D, bg='mumext', ring=-1, rub=False, cam=dict(mv='push', x=900, y=640, z=1.4, rate=0.04),
      tags=[(w(254, 'correct'), 'CORRECT HAND', -140, -260, 'red', 1.8, dict(at=ring_at(-1)))], music=[(w(254, 'correct'), 'stinger', 0.8)])
    C(T(256), 'bust', who=D, bg='mumext', scale=1.1, act=_A(stare(), smile(0.0, 1.8, 0.9), lambda a, s: a.set(s.t0 + 0.3, None, 0.6, hl_down=-40, hl_fwd=140, hl_out=60)),
      cam=dict(mv='push', x=960, y=560, z=1.05, rate=0.045))
    C(T(257), 'bust', who=M, bg='mumroom', act=_A(ex('shock'), phone_ear(1), hand_mouth(-0.2, None), lambda a, s: a.freeze(s.t0 + 0.25, s.t1)), cam=dict(mv='push', x=960, y=540, z=1.1),
      music=[(t(257), 'silence', 0.0, 1.0)])
    C(T(258), 'mumext', ppl=[P(O, at='door', act=_A(stare(), creep(5, 3, None))), P(D, at='window', act=_A(stare(), lean(0.3, 2.0, 0.5)))],
      cam=dict(mv='push', x=820, y=620, z=1.7, rate=0.05))
    C(T(259), 'bust', who=Y, bg='hall', act=_A(ex('shock'), phone_ear(1), tremble(1.0)), cam=dict(mv='fast', x=960, y=560), cut='static', hit=t(259) + 0.05)
    C(T(260), 'bust', who=D, bg='mumext', act=_A(ex('cry'), lambda a, s: a.cry(s.t0 - 1, None, smile=True), grin(t(261) - t(260)), creep(8, 3, None)),
      cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.05), light=red_rim)
    C(T(263), 'wave', bg='mumroom', title='CALL  -  MUM  -  6 YEARS AGO', rows=[dict(label='YOU', color='blue', seed=31),
                                                                                    dict(label='HIM', color='red', seed=31, p=(t(263), e(263)))],
      play=(t(263), e(263)), post=dict(sat=0.5))
    C(T(264), 'hall', you_at=HA(0.0, 1.15), act=_A(ex('fear'), phone_ear(1), back_view(), lambda a, s: a.set(s.t0 + 0.3, None, 0.5, hr_down=-150, hr_fwd=260, hr_shape='flat'),
                                                  tremble(1.0)), cam=dict(mv='push', x=960, y=480, z=1.1, rate=0.05))
    C(T(265), 'mumext', ppl=[P(O, at='door', act=_A(ex('talk_smile'), lean(0.4, 1.6, 0.5), creep(6, 3, None)), lean=True),
                             P(D, at='window', act=_A(stare(), sway(6, 2.4)))], cam=dict(mv='push', x=1010, y=660, z=2.1, rate=0.04),
      sfx=[(t(265) + 0.3, 'crowd_whisper', -14, 0.2, 'phone', dict(dur=2.5, density=1))])
    C(T(266), 'mumroom', ppl=[P(M, at=MA(1.3, 2.05), act=_A(ex('fear'), phone_ear(1), turned(1.4), lambda a, s: a.turn(s.t0 + 0.4, 0.0, 0.5), tremble(0.6)))],
      cam=dict(mv='push', x=1340, y=470, z=1.0, rate=0.05, opt=1.65))
    C(T(267), 'bust', who=D, bg='mumext', cx=980, cy=700, scale=0.72, act=_A(stare(), smile(0.0, 1.0, 0.9), creep(-8, 3, None)),
      cam=dict(mv='move', x=980, y=760, z=1.0, y1=640, z1=1.12))
    C(T(268), 'hall', you=True, act=_A(ex('fear'), lambda a, s: a.set(s.t0 - 1, None, 0.1, turn=1.4, h_turn=0.4)),
      cam=dict(mv='move', x=900, y=520, z=1.0, x1=420, y1=460, z1=1.12), sfx=[(t(268) + 0.1, 'whoosh', -8, -0.3, None, dict(kind='soft'))])
    C(T(269), 'hall', you=False, coats=False, cam=dict(mv='push', x=420, y=470, z=1.2, snap=(t(269) + 0.1, 1.25)), hit=t(269) + 0.1,
      music=[(t(269) + 0.1, 'braam', 0.9), (t(269) - 1.2, 'riser', 0.6, 1.2)], sfx=[(t(269) + 0.4, 'tinnitus', -6, 0, None, dict(dur=4))])
    C(T(270), 'hall', you=True, act=_A(ex('neutral'), lambda a, s: a.set(s.t0 - 1, None, 0.1, turn=1.3, h_turn=0.3)), coats=True, police=False,
      cam=dict(mv='drift', x=700, y=520, z=1.05, dx=-100), grade=Grade('interior_dim', sat=0.15, exposure=0.15), cut='white')
    C(T(271), 'living', cam=dict(mv='push', x=1060, y=600, z=1.1, rate=0.035))
    C(w(271, 'sitting') - 0.1, 'car', act=_A(down(-2), lambda a, s: a.head_down(s.t0 - 2, w(271, 'knocking'), 1.0), stare(0.0), creep(5, 2, None)),
      expr='dead_stare', scale=0.62, cam=dict(mv='push', x=985, y=450, z=1.15, rate=0.045))
    C(T(272), 'mumroom', ppl=[P(M, at=MA(1.3, 2.05), act=_A(ex('nervous'), phone_ear(1), turned(1.2), lambda a, s: a.turn(s.t0 + 1.6, -1.2, 0.7)))],
      cam=dict(mv='push', x=1300, y=480, z=1.0, rate=0.045, opt=1.35))
    C(T(273), 'mumroom', ppl=[P(M, act=_A(ex('nervous'), phone_ear(1)), path=(t(273) - 0.2, e(273) + 1.0, [MA(0.25, 0.95), 'mum_door']), facing=2.0)],
      cam=dict(mv='push', x=960, y=520, z=1.1, rate=0.05))
    C(T(274), 'bust', who=Y, bg='hall', act=_A(ex('fear'), phone_ear(1), tremble(1.2)), cam=dict(mv='hand', x=960, y=560, z=1.05))
    C(T(275), 'mumroom', ppl=[P(M, at='mum_door', act=_A(ex('sad'), turned(2.0), lambda a, s: a.hold_up('phone', s.t0 - 2, s.t0 + 0.6, 1)))],
      cam=dict(mv='push', x=955, y=520, z=1.0, rate=0.05, opt=2.3))
    C(T(276), 'phone', full=True, states=[(t(221), 'connected')], wave='#e0444c', prate=0.06, pshake=8.0,
      tags=[(t(276) + 0.4, 'OFFICER', 960, 150, 'red', 2.0)])
    C(T(277), 'bust', who=O, bg='mumext', act=_A(ex('talk_smile'), stare(0.0), smile(2.0, 2.0, 1.0), creep(8, 3, 0.6)), cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.05),
      light=red_rim)
    C(T(278), 'bust', who=Y, bg='hall', act=_A(ex('scream'), phone_ear(1), lambda a, s: a.scream(s.t0 + 0.05, s.t1)), cam=dict(mv='hand', x=960, y=560, z=1.05))
    C(T(279), 'bust', who=D, bg='mumext', scale=1.2, act=_A(lambda a, s: a.cry(s.t0 - 2, None, smile=True), grin(-1), tilt(0.6, 20, 1.6), creep(0, 4, None)),
      cam=dict(mv='push', x=960, y=540, z=1.0, rate=0.05), light=red_rim, music=[(t(279), 'braam', 0.8)])
    C(T(280), 'bust', who=M, bg='mumroom', act=_A(ex('cry'), lambda a, s: a.cry(s.t0 - 2), tremble(0.5)), cam=dict(mv='creep', x=960, y=540, z=1.05))
    C(T(282), 'ins', name='lock_inside', kw=lambda t_, t0=w(282, 'key'): dict(turn=ease_in_out(clamp((t_ - t0 - 0.1) / 0.9)), chain=0.0),
      police=True, cam=dict(mv='push', x=960, y=540, z=1.1, rate=0.05), music=[(e(282) - 0.2, 'hit', 1.0), (w(282, 'key') - 1.0, 'riser', 0.8, 1.2)],
      sfx=[(w(282, 'key') + 0.1, 'key_in_lock', 0, 0, 'phone'), (w(282, 'key') + 0.8, 'lock_turn', 0, 0, 'phone'),
           (e(282) - 0.2, 'impact_hit', 2, 0, None, dict(size=1.4))])

    # ============================================================ OUTRO (681.3 - end) v2.1: the climax builds to the end
    # red light, longer slow pushes, the double walking up mum's path, the knock at YOUR door again, the call dropping,
    # his grin in the car, and the last image: the double leaning into your doorbell lens grinning, a static hit, black.
    C(e(282) + 0.1, 'mumext', police=dict(mode='strobe', strength=1.4), figures=('driver',), cut='white',
      ppl=[P(D, path=(e(282) + 0.2, w(283, 'knocks') + 0.2, ['gate', 'path_mid', 'door']), act=_A(stare(), smile(0.4, 2.0, 1.0))),
           P(O, at='car_rear_door', act=_A(stare(), creep(6, 3, None)), track=False)],
      cam=dict(mv='push', x=1040, y=600, z=1.0, rate=0.05, dx=40, opt=1.45), music=[(e(282) + 0.3, 'motif', 0.5, 6)])
    C(w(283, 'knocks') - 0.1, 'door', ppl=[P(O, at=DA(0.0, 0.95), act=_A(stare(), knk(0.0, 3, 0.3, 0, 1.4), lean(1.3, 1.6, 0.9), smile(1.4, 1.6, 0.9)),
                                             lean=True)], py=-80, hit=[w(283, 'knocks') + 0.24, w(283, 'knocks') + 0.54, w(283, 'knocks') + 0.84])
    C(w(283, 'keep') - 0.1, 'peep', ppl=[P(O, at='officer_close', act=_A(grin(-1), tilt(0.4, 16, 2.0), creep(0, 3, None)))],
      cam=dict(mv='push', x=960, y=460, z=1.02, rate=0.05))
    C(T(284), 'phone', full=True, states=[(t(284) - 0.1, 'calling'), (w(284, 'still') - 0.1, 'busy')], prate=0.05, pshake=6.0,
      tags=[(w(284, 'still'), 'CALL FAILED', 960, 150, 'red', 1.6)])
    C(T(285), 'car', act=_A(lambda a, s: a.head_down(s.t0 - 2, s.t0 + 0.7, 1.0), stare(0.3), smile(0.5, 1.4, 1.0), grin(1.6)),
      expr='dead_stare', scale=0.82, cy=470, cam=dict(mv='push', x=985, y=470, z=1.05, rate=0.06), music=[(w(285, 'learning'), 'stinger', 0.7)])
    C(w(285, 'learning') - 0.1, 'door', ppl=[P(O, at=DA(-0.75, 1.25), act=_A(grin(-1), lean(0.6, 1.4, 0.6)), lean=True, track=False, aim=(820, 470)),
                                            P(D, at=DA(0.2, 0.95), act=_A(grin(-1), knk(0.0, 3, 0.28, 0, 1.3), lean(0.8, 1.1, 1.0)), lean=True, k=0.64)],
      py=-90, hit=[w(285, 'learning') + 0.24, w(285, 'learning') + 0.52, w(285, 'learning') + 0.8], music=[(e(285) + 0.4, 'end', 0.8, 3.0)])
    C(w(285, 'home') + 0.42, 'black', cut='static', music=[(w(285, 'home') + 0.42, 'hit', 1.0)],
      sfx=[(w(285, 'home') + 0.42, 'impact_hit', 0, 0, None, dict(size=1.3))])

    # ============================================================ global cues
    for l in F.L:                                                     # radio voices: key, static bed, unkey
        if l.get('fx') == 'radio' and l.get('found_en', True):
            G.append(_ev(l['t'] - 0.22, 'police_radio_squelch', -4, 0.15, 'outside', kind='key'))
            G.append(_ev(l['t'] - 0.1, 'radio_static', -9, 0.15, 'outside', dur=round(l['end'] - l['t'] + 0.4, 2), amount=0.6))
            G.append(_ev(l['end'] + 0.08, 'police_radio_squelch', -5, 0.15, 'outside', kind='unkey'))
    F.countdown = (t(193) + 0.95, 0.66, 10)
    c0, st, n0 = F.countdown
    for k in range(n0 + 1):
        G.append(_ev(c0 + k * st, 'countdown_tick', -4 + (2 if k == n0 else 0), 0.0, 'outside', rise=0))
    G.append({'t': round(c0 + st * (n0 + 1), 3), 'type': 'pulse_off', 'level': 0.5})
    G.append(_ev(c0 + st * n0 + 0.3, 'heartbeat', -4, 0, None, bpm=96, dur=3.0))
    G.append(_ev(t(25) + 0.2, 'heartbeat', -8, 0, None, bpm=70, bpm_end=84, dur=6))
    G.append(_ev(t(122) - 2.0, 'heartbeat', -8, 0, None, bpm=74, bpm_end=92, dur=8))
    G.append(_ev(t(258), 'heartbeat', -6, 0, None, bpm=88, bpm_end=118, dur=10))
    for i_, kind in ((1, 'motif'), (23, 'swell'), (45, 'swell'), (86, 'swell'), (130, 'swell'), (160, 'motif'), (215, 'swell'), (248, 'swell'), (263, 'motif'),
                     (271, 'swell'), (284, 'swell')):
        G.append({'t': round(t(i_), 3), 'type': kind, 'level': 0.6, 'len': 6.0 if kind == 'swell' else 4.0})
    for i_ in (5, 63, 126, 228, 242, 258, 268):                       # risers into the reveals
        G.append({'t': round(t(i_) + 0.4, 3), 'type': 'riser', 'level': 0.6, 'len': 3.0})


# ==================================================================================================== tools
def contact_sheets(F, prefix, cols=8, rows=6, size=(960, 540), tile=240, ts=None):
    import cv2
    ts = ts if ts is not None else [(s.t0 + s.t1) / 2 for s in F.shots]
    tiles = []
    for k, t in enumerate(ts):
        try:
            img = F.frame(t, int(t * FPS))
        except Exception as ex_:
            import traceback; print('FRAME ERROR t=%.2f shot %s: %r' % (t, F.shot_at(t), ex_)); traceback.print_exc(limit=-2)
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
    ap.add_argument('--timeline', default=os.path.join(S, 'pov2', 'align', 'timeline.json'))
    ap.add_argument('--cues', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--range', nargs=2, type=int, default=None)
    ap.add_argument('--size', default='960x540')
    ap.add_argument('--bench', type=int, default=0, help='N shots x 4 frames at --size (use 2560x1440), one process')
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
    if a.cues:
        sfx, mus = F.cues()
        print('sfx %d, music events %d' % (len(sfx), len(mus['events'])))
    if a.bench:
        idx = np.linspace(0, len(F.shots) - 1, a.bench).round().astype(int)
        rows, t_all = [], time.time()
        for k in idx:
            s_ = F.shots[k]
            for j in range(4):
                tt = s_.t0 + min(s_.d - 0.02, 0.1 + j * max(0.05, (s_.d - 0.2) / 3))
                t1_ = time.perf_counter(); F.frame(tt, int(tt * FPS)); rows.append((s_.kind, j, time.perf_counter() - t1_))
        tot = np.mean([r[2] for r in rows]); steady = np.mean([r[2] for r in rows if r[1] > 0])
        kinds = sorted(set(r[0] for r in rows))
        res = {'size': a.size, 'frames': len(rows), 'mean_s': round(float(tot), 3), 'steady_mean_s': round(float(steady), 3),
               'max_s': round(float(max(r[2] for r in rows)), 3),
               'by_kind': {k_: round(float(np.mean([r[2] for r in rows if r[0] == k_])), 3) for k_ in kinds}}
        print(json.dumps(res))
        out = os.path.join(S, 'pov2', 'tests', 'film', 'speed_%s.json' % a.size)
        json.dump(res, open(out, 'w'), indent=1); print(out)
    if a.sheet:
        sh = F.shots[a.range[0]:a.range[1]] if a.range else F.shots
        print(contact_sheets(F, a.sheet, ts=[(s.t0 + s.t1) / 2 for s in sh]))
