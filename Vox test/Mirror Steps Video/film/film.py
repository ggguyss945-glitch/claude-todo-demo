"""film.py: the assembler for "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH" (v2).

    from film import Film
    F = Film(timeline_dict)            # engine set_render_size(...) first (render.py does it)
    F.frame(t, i) -> uint8 RGB         # one frame at the engine render size
    F.duration                         # 700.0 s (plan meta)
    F.shots                            # the 449 v2 plan shots (plan/shots.json, PLAN_V2.md)
    F.events(path=None)                # writes _work/align/film_events.json for audio/cues.py (picture-synced SFX)

    python3 film.py --sheet OUT_PREFIX [--size 960x540] [--tile 320] [--cols 5] [--per 40] [--part k/n] [--keep DIR] [ids...]
    python3 film.py --events           # -> _work/align/film_events.json
    python3 film.py --bench [ids...]   # full-size warm s/frame per shot (sets + cast + HUD), heaviest first
    python3 film.py --list

Everything comes from plan/shots.json (PLAN_V2.md):
  - the set: one SetPiece per shot from sets.build_shot (sets_v2.py room3d views: layers, anchors, bokeh plates behind the
    close-ups, the per-tenth light arc in its fx). Rule cards build their live `bg` plate, TYPE / DIAGRAM shots their
    blurred `plate`, SPLIT shots both panels; DOC shots add the paper object (ui_v2.doc_layer);
  - the grade: the shot's v2 look (night_v2, stairs_v2, dawn_v2, dawn_queen_v2, dawn_break_v2, memory_sepia, climax_v2,
    ending_v2, phone_dark); rule cards take the grade of their background world. The cast is never dimmed (the v2 grades
    do not lift exposure);
  - the cast: one characters.CharRig layer per chars[] entry (stages, acting clips on the word, lip-sync from the
    timeline), staged on the set (`stage`: kneels and sits become clips, seated people on the other side sit on Noah's
    mattress from the room's 3D camera, H2's glide ends in her seat, standing sizes kept within 0.75-1.33x of what the
    room says at the feet, the section's figures on its treads, `SEAT` per-shot overrides, `EXTRA_CHARS` for the cast the
    plan leaves out) and placed in depth (`place`: just in front of the room's distance band that holds their feet;
    busts, hands, feet and OTS figures in front of the room; the DOF focus follows the subject). `reflection` entries
    are drawn mirrored, cool and faint inside the glass (behind the lipstick), `in_glass` / `through_glass` / `inside`
    entries are clipped to the glass or the phone screen, `soft_focus` entries are blurred;
  - the camera: the plan keys (pushes about 3 %/s, pull-outs, whips, dutch roll in the climax), snaps (punch-ins), hits,
    handheld for shake >= 8, plus a uniform 1.4 %/s post push (pull on pull-outs) because the dolly's parallax scales
    the far layers less than the nominal rate;
  - the light: the set's arc_fx plus LIGHT_TRIM (tenths 1-2 and the ending measured dark on the preview), a 1.06
    saturation lift outside the climax, half bloom on people's close-ups;
  - transitions: cut, glint (the 3-frame glass glint, ui_v2), white (3-frame flash), glitch (2 frames of static + RGB
    split), rewind (tear + back-scrub, ui_v2), sepia (a 0.2 s paper wipe into and out of the memories), smear (the card's
    finger-wipe carried over, ui_v2), black; in-shot fx_post white / glitch / static / rewind / pixel_sort;
  - MONTAGE shots render the sill at each tile's source time (props of that moment), SPLIT shots come composed by the sets;
  - the HUD: ui_v2.UI (captions, header, chips, Tess's ring badge and giant numbers, tags, red X, labels, diagrams D1-D10,
    documents' marks, type beats, the kinetic title, the seven mirror rule cards, the phone, teasers), then ui_v2's
    picture effects (RGB split, rewind tear, pixel sort).
"""
import bisect, json, math, os, sys, time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine import hud as H
from engine.core import (DW, DH, CFG, Pen, clamp, lerp, ease_in_out, hash01, noise1, surface_for)
from characters import smoothstep
from engine.camera import Cam
from engine.post import GRADES, get_grade
from engine.scene import Layer, render_frame
import characters as CH
import sets as ST
import ui_v2

WORK = os.path.join(HERE, '_work')
PLAN = os.path.join(HERE, 'plan', 'shots.json')
SOUND = os.path.join(HERE, 'plan', 'sound_plan.json')
TIMELINE = os.path.join(WORK, 'align', 'timeline.json')
EVENTS = os.path.join(WORK, 'align', 'film_events.json')
FPS = 60
DISSOLVE = 0.30                       # centred on the cut
SEPIA_WIPE = 0.45                     # the paper dissolve into / out of a memory (0.2 s before the cut, 0.25 s after)
FLOW = 0.50                           # the travel dissolve between two places (centred on the cut)
# transition windows (before, after the cut) for the blended transitions
PAN = 0.45                            # the turn of the head between two places (a whip pan, centred on the cut)
TR_WIN = {'dissolve': (DISSOLVE / 2, DISSOLVE / 2), 'sepia': (0.20, 0.25), 'flow': (FLOW / 2, FLOW / 2), 'pan': (PAN / 2, PAN / 2)}
POST_RATE = 0.014                     # uniform post push per second on every shot (see make_cam)
H._hand = CH.hud_phone_hand           # the cast's hand on the phone UI
_ERR = set()

# exposure trims (stops) by world and film time, on top of sets_v2.arc_fx: the first preview measured tenths 1-2 at luma
# p50 84 / 91 (target 95-110) and the last at 87 (90-100)
SAT_LIFT = 1.06
LIGHT_TRIM = {'ours': [(0.0, 140.0, 0.22)], 'stairs': [(0.0, 140.0, 0.15)], 'ending': [(629.0, 700.0, 0.12)]}
WORLD_GRADE = {'ours': 'night_v2', 'stairs': 'stairs_v2', 'theirs': 'dawn_v2', 'theirs_break': 'dawn_break_v2',
               'memory': 'memory_sepia', 'climax': 'climax_v2', 'ending': 'ending_v2', 'ui': 'phone_dark', 'black': 'neutral'}


def _warn(key, msg):
    if key in _ERR: return
    _ERR.add(key)
    print('[film] ' + msg, file=sys.stderr, flush=True)


# ==================================================================================================== camera
def _mono(xs, ys, x):
    """Monotone cubic through (xs, ys) at x, extended linearly with the end tangents (dissolves render past the ends)."""
    from engine.room3d import mono_cubic
    if len(xs) == 1: return float(ys[0])
    if x < xs[0] or x > xs[-1]:
        j = 0 if x < xs[0] else len(xs) - 1
        e = 1e-3 * max(1e-3, xs[-1] - xs[0])
        x0 = xs[0] + e if j == 0 else xs[-1] - e
        sl = (mono_cubic(xs, ys, x0) - ys[j]) / (x0 - xs[j])
        return float(ys[j] + sl * (x - xs[j]))
    return mono_cubic(xs, ys, x)


class PathCam(Cam):
    """A camera move through several keys as ONE move (merged shots, travelling moves): x, y, log zoom and roll follow a
    monotone cubic through the keys (no overshoot, continuous speed, no stop at the keys) under a glide time warp (the
    speed eases up from v0 of the cruise speed and down to v1 over `ramp` s: alive at the cut, no jerk inside)."""

    def __init__(self, keys, warp, **kw):
        super().__init__([tuple(k[:5]) for k in keys], ease='lin', **kw)
        self.warp = warp
        self.kt = [k[0] for k in self.keys]
        self.kv = [[k[1] for k in self.keys], [k[2] for k in self.keys], [math.log(max(1e-3, k[3])) for k in self.keys],
                   [k[4] for k in self.keys]]

    def _raw(self, u):
        return np.array([_mono(self.kt, ch, u) for ch in self.kv])

    def _base(self, t):
        u = self.warp(t)
        if len(self.kt) > 2 and self.kt[0] < u < self.kt[-1]:      # review round 2 (M20): no stop at a key (room3d.ArcBlend)
            if not hasattr(self, '_arc'):
                from engine.room3d import ArcBlend
                self._arc = ArcBlend(self.kt, self._raw, (1 / 300.0, 1 / 300.0, 1 / 0.12, 1 / 6.0))
            u = self._arc(u)
        x, y, lz, r = (_mono(self.kt, ch, u) for ch in self.kv)
        return x, y, math.exp(lz), r


def make_cam(sh, idx, t_shift=0.0):
    """Cam from the plan keys. The plan's shake is a handheld amplitude: 2 = breathing tripod, 15-26 = nervous hand.
    - ease 'glide' (merged shots, multi-key moves) or more than two keys: one PathCam move through every key (see PathCam);
      cam['glide'] = [v0, v1, ramp] sets the speed at the ends;
    - two-key linear pushes stay linear and are extrapolated 0.5 s past both ends (wipes and dissolves never freeze);
    - snaps only where the plan keeps one (the three hits), `accel` = [t, factor, dur]: an eased push acceleration (an
      optical zoom with an in-out ease, no jolt); hits;
    - the uniform post push (POST_RATE) only on the holds (H1-H10): every other shot moves by its own keys.
    t_shift moves the whole move in time (MONTAGE tiles replay a framing at its source time)."""
    from engine.room3d import glide
    c = sh['cam']
    ks = [list(map(float, k)) + [0.0] * (5 - len(k)) for k in c['keys']]
    if sh.get('cam3'):                     # a travelling shot: the move is the 3D camera's; the 2.5D camera stays home
        ks = [[sh['t0'], 960.0, 540.0, 1.0, float(c['keys'][0][4]) if len(c['keys'][0]) > 4 else 0.0]]
    for k in ks: k[0] += t_shift
    ease_ = {'lin': 'lin', 'out': 'out', 'in_out': 'in_out', 'push': 'push', 'glide': 'glide'}.get(c.get('ease', 'lin'), 'lin')
    shake = float(c.get('shake', 2.0) or 0.0)
    if shake >= 8: amp, hz, rs = shake * 0.45, 0.95, 0.22
    else: amp, hz, rs = max(1.6, shake), 0.6, 0.0
    if ease_ == 'glide' or len(ks) > 2:
        v0, v1, ramp = (list(c.get('glide') or []) + [0.45, 0.6, 0.8][len(c.get('glide') or []):])[:3]
        a_, b_ = ks[0][0], ks[-1][0]
        cam = PathCam(ks, glide(a_, b_, v0, v1, ramp), shake=amp, shake_hz=hz, seed=idx * 3 + 1, roll_shake=rs)
    else:
        if ease_ == 'lin' and len(ks) >= 2:
            a, b = ks[0], ks[-1]; dt = max(1e-3, b[0] - a[0]); e = 0.5
            rz = math.log(b[3] / a[3]) / dt
            ks = [[a[0] - e, a[1] - (b[1] - a[1]) / dt * e, a[2] - (b[2] - a[2]) / dt * e, a[3] * math.exp(-rz * e), a[4]]] + ks + \
                 [[b[0] + e, b[1] + (b[1] - a[1]) / dt * e, b[2] + (b[2] - a[2]) / dt * e, b[3] * math.exp(rz * e), b[4]]]
        elif len(ks) >= 2:
            ks = [[ks[0][0] - 0.5] + ks[0][1:]] + ks + [[ks[-1][0] + 0.5] + ks[-1][1:]]
        keys = [tuple(k[:5]) + ((ease_,) if j else ()) for j, k in enumerate(ks)]
        cam = Cam(keys, ease=ease_, shake=amp, shake_hz=hz, seed=idx * 3 + 1, roll_shake=rs)
    if c.get('snap'):
        s = c['snap']; cam.snap(float(s[0]) + t_shift, float(s[1]) if len(s) > 1 else 1.25, float(s[2]) if len(s) > 2 else 0.1)
    for ac in c.get('accel') or []:
        ta, fa, da = float(ac[0]) + t_shift, float(ac[1]), float(ac[2]) if len(ac) > 2 else 0.6
        cam.post_push(ta - da * 0.35, ta + da * 0.65, 1.0, fa, ease='in_out')
    for h in c.get('hit') or []:
        cam.hit(float(h[0]) + t_shift, float(h[1]) * 0.75, 0.32, 13.0)
    # the holds keep a slow post push on top of the dolly (the dolly scales the far layers less than the nominal rate)
    if sh.get('hold') and sh.get('side') != 'black' and POST_RATE > 0:
        a, b = sh['t0'] - 0.5 + t_shift, sh['t1'] + 0.5 + t_shift
        zz = (1.0 + POST_RATE) ** (b - a)
        if c.get('move') in ('pull', 'reveal'): cam.post_push(a, b, zz, 1.0, ease='lin')
        else: cam.post_push(a, b, 1.0, zz, ease='lin')
    return cam


# ==================================================================================================== built shot
class Built:
    __slots__ = ('sh', 'idx', 'sp', 'layers', 'cam', 'grade', 'focus', 'dof', 'rigs', 'post', 'dyn')

    def fx(self, t):
        return self.sp.fx(t)


def _neighbour(film, sh, pred, reach=(-1, 1, -2, 2, -3, 3)):
    k0 = film.index.get(sh['id'])
    if k0 is None: return None
    for d in reach:
        k = k0 + d
        if 0 <= k < len(film.shots) and pred(film.shots[k]): return film.shots[k]
    return None


def card_grade(film, sh):
    """Rule cards: the grade of the neighbouring shot that shows the card's background set, else the bg world's look."""
    bg = sh.get('bg') or {}
    o = _neighbour(film, sh, lambda o: (o['set'], o['view'], o['var']) == (bg.get('set'), bg.get('view'), bg.get('var'))
                   and o['grade'] in GRADES)
    if o is not None: return o['grade']
    if bg.get('var') == 'dawn_queen': return 'dawn_queen_v2'
    return WORLD_GRADE.get(bg.get('world'), 'night_v2')


def _card_chars(film, sh):
    """Cast for a rule card's live background: the neighbouring shot on the same set view, acts dropped (they breathe,
    blink and hold their expression behind the blur)."""
    bg = sh.get('bg') or {}
    o = _neighbour(film, sh, lambda o: (o['set'], o['view']) == (bg.get('set'), bg.get('view')) and o['chars'])
    if o is None: return []
    out = []
    for c in o['chars']:
        c2 = {kk: v for kk, v in c.items() if kk not in ('acts', 'clip_id')}
        c2['acts'] = [a for a in (c.get('acts') or []) if a[1] in ('expr', 'flashlight', 'stage')]
        out.append(c2)
    return out


def _glass_path(sp):
    """The clip for anything seen in or through the glass / the phone: a skia Path in design px, or None."""
    scr = sp.info.get('screen')
    if scr is not None: return scr
    g = sp.info.get('glass')
    if g is None or len(g) < 3: return None
    p = skia.Path(); p.moveTo(float(g[0][0]), float(g[0][1]))
    for q in g[1:]: p.lineTo(float(q[0]), float(q[1]))
    p.close()
    return p


def _char_layer(rig, at, mode, store, sh, spec, sp):
    d = float(at[3]) if (mode in ('body', 'legs', 'silhouette') and isinstance(at, (list, tuple)) and len(at) > 3) else 1.0
    if spec.get('_depth'): d = float(spec['_depth'])
    refl = bool(spec.get('reflection'))
    clip = _glass_path(sp) if (refl or spec.get('in_glass') or spec.get('through_glass') or spec.get('inside')) else None
    mx = float(at[0]) if isinstance(at, (list, tuple)) else DW / 2
    atf = None
    if spec.get('path2d') and isinstance(at, (list, tuple)):
        # review round 2 (M2): a figure moving in depth on a 2D set (walking up the path, away from the camera): keys
        # [[t, x, y_feet, h], ...] through a monotone cubic, the layer depth kept
        from engine.room3d import mono_cubic
        pk = sorted(spec['path2d'], key=lambda k_: float(k_[0]))
        pts = [float(k_[0]) for k_ in pk]; cols = [[float(k_[j]) for k_ in pk] for j in (1, 2, 3)]
        rest = list(at[3:])
        def atf(t):
            tt = min(max(t, pts[0]), pts[-1])
            return [mono_cubic(pts, c_, tt) if len(pts) > 1 else c_[0] for c_ in cols] + rest

    def draw(pen, t):
        cv = pen.cv
        n = 0
        try:
            if clip is not None:
                cv.save(); cv.clipPath(clip, skia.ClipOp.kIntersect, True); n += 1
            if refl:                                            # a reflection: mirrored about its own x
                cv.save(); cv.translate(mx, 0); cv.scale(-1, 1); cv.translate(-mx, 0); n += 1
            if spec.get('_rot') and isinstance(at, (list, tuple)):   # lying along a mattress seen at an angle
                cv.save(); cv.rotate(float(spec['_rot']), float(at[0]), float(at[1])); n += 1
            info = rig.draw(pen, t, at=atf(t) if atf is not None else at)
            if store is not None: store['last'] = (t, info)
        except Exception as e:                                  # never kill a render on one bad pose
            _warn((sh['id'], rig.who, type(e).__name__), 'char draw failed %s %s: %r' % (sh['id'], rig.who, e))
        finally:
            for _ in range(n): cv.restore()
    L_ = Layer(d, draw, 'char_' + rig.who, ref_depth=d)
    if refl:
        L_.alpha = 0.34; L_.tint = ('#a9b6ff', 0.5)
        if mode == 'hands':                  # critic M15: the hand's reflection read as a second, equally bright hand
            L_.alpha = 0.18; L_.blur = 4.0
    if spec.get('soft_focus'):
        L_.blur = 5.0
    return L_


def _hook_beam(sp, rig, at, layer, store):
    """Tess's beam starts at her flashlight when she is in the frame (same depth plane as the beam: no parallax error)."""
    B = sp.info.get('beam')
    if B is None or getattr(B, 'fn', None) is None: return
    try: bl = sp.layer('beam')
    except KeyError: return
    if callable(bl.depth) or abs(float(bl.depth) - float(layer.ref_depth)) > 0.12: return
    fn0 = B.fn
    null = skia.Surface(8, 8)
    h = float(at[2]) if len(at) > 2 else 600.0

    def ov(t):
        r = fn0(t)
        if r is None: return None
        sx, sy, ax, ay, k = r
        last = store.get('last')
        if last is None or abs(last[0] - t) > 0.04:
            try:
                last = (t, rig.draw(Pen(null.getCanvas()), t, at=at)); store['last'] = last
            except Exception:
                return r
        hands = (last[1] or {}).get('hands') or {}
        hp = hands.get(-1) or hands.get('-1')
        # critic B8: the flare toggled to the default source on frames where the hand was not reported; it now stays on the
        # last known hand, eased toward a new one (no jumps)
        if hp: hp = (float(hp[0]), float(hp[1]))
        else: hp = store.get('hp')
        if not hp: return r
        prev = store.get('hp_s')
        if prev is not None and abs(store.get('hp_t', t) - t) < 0.1:
            hp = (prev[0] + (hp[0] - prev[0]) * 0.6, prev[1] + (hp[1] - prev[1]) * 0.6)
        store['hp'] = hp; store['hp_s'] = hp; store['hp_t'] = t
        hx, hy = float(hp[0]), float(hp[1])
        dx, dy = ax - hx, ay - hy; L = math.hypot(dx, dy) or 1.0
        off = 0.07 * h
        return (hx + dx / L * off, hy + dy / L * off, ax, ay, k)
    B.override = ov


class _NoSet:
    """A set stand-in for stage() when only the acting matters (events)."""
    info, anchors = {}, {}


# ==================================================================================================== cast the plan leaves out
def _knot_echo(film, sh):
    """S281 (the ECU of the knot under the 14 YEARS echo): the same hands on the same half-tied lace as S241."""
    src = film.shot_at(362.6)                       # the knot ECU of rule 4 (S241 in v2)
    out = []
    for c in src['chars']:
        c2 = json.loads(json.dumps(c))
        c2['acts'] = [[sh['t0'] - 0.4, a[1], a[2]] for a in c2.get('acts') or []]
        if sh.get('cam3'):                     # the pull-out leaves the knot: the hands fade as the room opens
            c2['acts'].append([sh['t0'] + 1.6, 'hide', {'fade': 0.35}])
        out.append(c2)
    return out


def _glass_pair(film, sh):
    """The mirror reads as glass (error 33): your and Tess's reflections stand in it, faint and cool (placed on the glass
    polygon in build: `_glass_rel` = [x, y, size] as fractions of the glass bbox)."""
    return [dict(who='tess', mode='bust', view='q_right', expr='tense', acts=[], reflection=True, _glass_rel=[0.36, 0.25, 0.085]),
            dict(who='you', mode='bust', view='q_left', expr='dread', acts=[], reflection=True, _glass_rel=[0.64, 0.23, 0.095])]


def _tape_off(film, sh):
    """S361 (error 5): the empty blue tape loop slides off the lengthened fingers and drops."""
    return [dict(who='noah13', mode='hands', view='front', expr='neutral', tape=True, at=[960, 470, 600],
                 acts=[[sh['t0'] - 1.7, 'age', {'part': 'hand', 'dur': 1.6}], [sh['t0'] + 0.15, 'slip_tape', {'dur': 0.6}]])]


def _bunk_pair(film, sh):
    """S258 (389, the THEIRS master as the loop resets): Noah on his bunk and the Queen in the window corner (critic B6:
    the master showed neither)."""
    return [dict(who='noah13', mode='body', view='q_right', expr='calm_kid', seated=True, at=[700, 860, 390],
                 acts=[[sh['t0'], 'tie_loop', {'period': 2.4}]]),
            dict(who='queen', mode='body', view='q_left', expr='queen_drawn', stage='S2', at=[1300, 760, 380],
                 acts=[[sh['t0'], 'still', {}]], light=dict(key_c='#e8ecff', key_from='below_front', rim='#ff3b5c', rim_a=140))]


def _towel_drop_pair(film, sh):
    """256.9 (critic B5): the towel drops and there is no glass behind it: you and Tess stand in the profile, recoiling."""
    return [dict(who='tess', mode='body', view='q_right', expr='fear', at='tess_beside', acts=[[sh['t0'] + 0.1, 'flinch', {}]]),
            dict(who='you', mode='body', view='q_right', expr='fear', at='you_floor', acts=[[sh['t0'] + 0.15, 'flinch', {}]])]


def _you_ots_mirror(film, sh):
    """249.1-252.3 (critic B5): you stand at the mirror in the OTS (you were absent while Tess snatched the towel)."""
    return [dict(who='you', mode='body', view='back', expr='fear', at=[1450, 1230, 1040], acts=[])]


def _you_at_doorway(film, sh):
    """282.6 (critic B5): you stay in front of the doorway (S185 had you in it; the next shot was empty): your shoulder at the
    frame's left edge while it rises."""
    return [dict(who='you', mode='body', view='back', expr='fear', at=[250, 1420, 1250], acts=[])]


def _dip_pair(film, sh):
    """470.5 (critic B5): the dip is not empty: her black satin settles beside Noah's knees (the bunk chart's seats)."""
    return [dict(who='noah13', mode='body', view='q_right', expr='calm_kid', seated=True, at=[900, 900, 400],
                 acts=[[sh['t0'], 'tie_loop', {'period': 2.4}]]),
            dict(who='queen', mode='body', view='q_right', expr='queen_drawn', stage='S2', seated=True, at=[700, 900, 400],
                 acts=[[sh['t0'], 'still', {}]], light=dict(key_c='#e8ecff', key_from='below_front', rim='#ff3b5c', rim_a=140))]


def _ending_pair(film, sh):
    """643.4 (critic B8): one ending blocking: you and grown Noah stay sitting on our floor (the floor_wide shot's cast),
    you reach for your phone."""
    src = film.shot_at(633.0)
    out = []
    for c in src['chars']:
        c2 = {k: v for k, v in c.items() if k not in ('acts', 'clip_id')}
        c2['acts'] = [a for a in (c.get('acts') or []) if a[1] in ('expr', 'sit', 'kneel')]
        if c2['who'] == 'you': c2['acts'] = c2['acts'] + [[sh['t0'] + 0.2, 'reach', {'side': 1}]]
        out.append(c2)
    return out


REPLACE_CHARS_T = {643.5: _ending_pair}      # shots whose cast is replaced (by a film time inside the shot)
REPLACE_CHARS = {}


# per-shot extras and overrides are keyed by a film time inside the shot (ids change when shots merge): _by_time()
EXTRA_CHARS_T = {425.0: _knot_echo, 90.9: _glass_pair, 108.8: _glass_pair, 388.5: _bunk_pair, 257.0: _towel_drop_pair,
                 250.0: _you_ots_mirror, 282.7: _you_at_doorway}     # review round 2: 470.6 (_dip_pair) is inside H2's one set-up now


# ==================================================================================================== staging the cast
SEAT_T = {      # per-shot overrides: {(a film time inside the shot, who): {spec keys}} (from the shot checks)
    (338.8, 'tess'): {'at': 'tess_doorway', 'scale': 0.9}, (340.3, 'tess'): {'at': 'tess_doorway', 'scale': 0.9},
    (347.7, 'tess'): {'at': 'tess_doorway', 'scale': 0.9}, (449.8, 'tess'): {'at': 'tess_doorway', 'scale': 0.9},
    (451.3, 'tess'): {'at': 'tess_doorway', 'scale': 0.9},
    # B9: back on our side Tess stands IN the doorway frame and turns to the front door (seen from behind her)
    (453.5, 'tess'): {'at': [760, 1250, 1050], 'view': 'back'},
    # H1: she leans out of the doorway at the mirror spot, half in our blue, half in their gold (the doorway behind her)
    (283.7, 'queen'): {'at': [985, 610, 0.74]},
    # the set presses her fingertips through the towel; the loose arm read as a club
    (253.7, 'queen'): {'skip': True},
    # he rises into the top rail (error 6): big enough that his shoulder meets the rail
    (572.1, 'noah_grown'): {'at': [960, 1230, 1000]}, (573.4, 'noah_grown'): {'at': [960, 1230, 1040]},
}
SEAT, EXTRA_CHARS = {}, {}          # by shot id, filled from SEAT_T / EXTRA_CHARS_T for the plan in use (Film.__init__)


def _by_time(shots):
    """Re-key the time-keyed overrides by the ids of the plan in use."""
    def sid_at(tt):
        for s_ in shots:
            if s_['t0'] <= tt < s_['t1']: return s_['id']
        return None
    SEAT.clear(); EXTRA_CHARS.clear(); REPLACE_CHARS.clear()
    for tt, fn in REPLACE_CHARS_T.items():
        sid = sid_at(tt)
        if sid: REPLACE_CHARS[sid] = fn
    for (tt, who), v in SEAT_T.items():
        sid = sid_at(tt)
        if sid: SEAT[(sid, who)] = v
    for tt, fn in EXTRA_CHARS_T.items():
        sid = sid_at(tt)
        if sid: EXTRA_CHARS[sid] = fn
FLOOR_SETS = ('cabin_now', 'cabin_dawn', 'mirror', 'memory')
# standing heights (m) for the room3d views (CAST.md: the queen 1.12x the adults, grown Noah 1.08x you, Noah13 ~0.8x)
HEIGHT_M = {'you': 1.76, 'tess': 1.68, 'noah13': 1.42, 'noah_grown': 1.90, 'queen': 1.97, 'you_kid': 1.30, 'kids': 1.30,
            'counselor': 1.74, 'extras': 1.74, 'mom': 1.66}
# THEIRS: Noah's bunk along the left wall (x 0.08-0.92, z 4.25-6.3); hips on the mattress edge, feet on the floor in front
# review round 2 (M9): Noah's seat moved 0.4 m down the mattress, away from the foot of the stairs (from most bunk angles his
# seated figure overlapped the bottom treads and read as sitting on the stairs); the Queen's seat beside him follows
THEIRS_SEAT = {'noah13': 4.68, 'queen': 5.32, 'you': 4.3, 'noah_grown': 4.95}
SEAT_VIEWS = ('queen_3s', 'master')   # views whose plan guesses miss the mattress (bunk_2s / ots_noah guesses read right)
SEAT_X, FEET_X = 0.85, 1.24
H2_START = (3.95, 0.0, 5.6)           # where she stands before the H2 glide: the window corner (DIRECTION_V2 372)
QUEEN_CORNER = (3.95, 0.0, 5.6)
YOU_FOOT = (1.3, 0.0, 3.7)            # you stand at the foot end of Noah's bunk (left of them from every bunk angle)


def bunk_chart(who, t):
    """One blocking chart for the THEIRS bunk, 382-500 s (critic B6): Noah sits on his mattress; the Queen sits beside him
    (382.4-388.6, the first sight), stands in the window corner from 388.6, glides to his side in H2 (464.6-466.4) and sits
    there; you stand at the foot end. The two of them never overlap. -> (world point, seated) or None."""
    if not (382.0 <= t < 500.5): return None
    if who == 'noah13': return (FEET_X, 0.0, THEIRS_SEAT['noah13'] if t >= 468.6 else 4.95), True   # he scoots over in H2
    if who == 'queen':
        if t < 388.3 or t >= 467.7: return (FEET_X, 0.0, THEIRS_SEAT['queen']), True
        return QUEEN_CORNER, False
    if who == 'you': return YOU_FOOT, False
    return None


def _ray_floor(sp, x, y, yplane=0.0):
    """The floor point (world) under design point (x, y) of a room3d view, or None when the ray misses the cabin floor."""
    cam3 = sp.info.get('cam3')
    if cam3 is None: return None
    qx, qy = (x - cam3.cx) / cam3.f, -(y - cam3.cy) / cam3.f
    dirv = cam3.R.T @ np.array([qx, qy, 1.0])
    if abs(dirv[1]) < 1e-6: return None
    s = (yplane - cam3.C[1]) / dirv[1]
    if s <= 0.15: return None
    P = cam3.C + dirv * s
    if not (-0.05 <= P[0] <= 5.65 and -0.05 <= P[2] <= 6.45): return None    # outside the cabin's floor (behind a wall)
    return P


def _anchor_at(sp, P, who):
    cam3, d0 = sp.info['cam3'], sp.info['d0']
    if cam3.dist(P) < 0.4: return None
    x, y, h, dep = cam3.anchor(np.asarray(P, np.float64), HEIGHT_M.get(who, 1.74), d0)
    return [float(x), float(y), float(h)]


def stage(sp, spec, sh):
    """The plan's cast entry, staged on this set: kneels and sits become acting clips, seated people on the other side
    sit on Noah's mattress (feet on the floor in front of it, sizes from the room camera), H2's glide ends in her seat,
    people sitting on our floor drop by a shin, a standing person's size is kept within 0.75-1.33x of what the room
    says at their feet, and the section's small figures stand on its treads."""
    s = dict(spec)
    # an act that starts after the shot ends can only hurt it (a clip that is not yet running still writes its rest pose:
    # the 'will not open' fist of S418 at 646.9 opened the hand for the whole shot)
    acts = [list(a) for a in (s.get('acts') or []) if float(a[0]) <= sh['t1'] + 0.05]
    who, mode = s['who'], s.get('mode', 'body')
    at = s.get('at')
    t_pre = sh['t0'] - 1.0
    if mode == 'bust':                                   # tying the lace in a close-up drops the head out of the frame
        acts = [[a[0], 'head_down', {'amount': 0.3}] if a[1] == 'tie_loop' else a for a in acts]
    names = [a[1] for a in acts]
    s['acts'] = acts
    lt = s.get('light')
    if isinstance(lt, dict) and lt.get('flash') and mode == 'bust':      # the beam's hot spot on a face: a warm cheek, not a
        s['light'] = dict(lt, flash_a=min(float(lt.get('flash_a', 0.2)), 0.07))   # bloom that makes the fear eyes glow
    if s.get('tiny') and sh['view'] == 'phone_screen' and 'bottom_step' in sp.anchors:
        an = sp.anchors['bottom_step']
        s['at'] = [an.x, an.y + 4.0, 46.0, 0.99]; s['inside'] = 'phone_screen'
        return s
    if mode != 'body' or not isinstance(at, (list, tuple)) or len(at) < 3:
        return s
    at = [float(v) for v in at]
    if s.get('kneel') and 'kneel' not in names:
        acts.insert(0, [t_pre, 'kneel', {}])
    seated = bool(s.get('seated'))
    if seated and who != 'queen' and not any(n in ('sit', 'sit_beside', 'glide_sit') for n in names):
        acts.insert(0, [t_pre, 'sit', {}])
    if seated and s.get('view', 'front') == 'front':          # a straight-on sit reads as standing: turn three-quarter
        s['view'] = 'q_right'
    cam3 = sp.info.get('cam3')
    ch_ = bunk_chart(who, sh['t0'] + 0.01) if (sh['set'] == 'cabin_dawn' and cam3 is not None and 'sit_beside' not in names) else None
    if ch_ is not None and sh['view'] not in ('bokeh',):              # the bunk chart wins over the plan's guesses
        a2 = _anchor_at(sp, ch_[0], who)
        if a2 is None or a2[2] > 2.6 * DH:                              # the chart puts them behind / right at the lens
            s['_skip'] = True; return s                                 # (M9: up to 2.6 H she is a cropped foreground figure, not gone)
        if a2 is not None:
            seated = ch_[1]
            s['seated'] = seated
            if seated and who != 'queen' and not any(n in ('sit', 'sit_beside', 'glide_sit') for n in names):
                acts.insert(0, [t_pre, 'sit', {}])
            if not seated: acts[:] = [a for a in acts if a[1] not in ('sit',)]
            if who == 'queen': s['view'] = 'q_right' if seated else 'q_left'
            s['at'] = a2 + at[3:4]; s['acts'] = acts; s['_chart'] = True
            return s
    if sh['set'] == 'cabin_dawn' and cam3 is not None and 'stairs_foot' in sp.anchors:
        B = ST.sets_v2.B_LOW
        if seated and s.get('view') != 'back' and who in THEIRS_SEAT and sh['view'] in SEAT_VIEWS:
            a2 = _anchor_at(sp, (FEET_X, 0.0, THEIRS_SEAT[who]), who)
            if a2 is not None:
                at = a2 + at[3:4]
                if who == 'queen' and s.get('view', 'front') == 'front': s['view'] = 'q_right'
        if who == 'queen' and 'sit_beside' in names:                       # H2: from the stairs' foot onto the bunk
            a0 = _anchor_at(sp, H2_START, who); a1 = _anchor_at(sp, (FEET_X, 0.0, THEIRS_SEAT['queen']), who)
            if a0 is not None and a1 is not None:
                at = a0 + at[3:4]
                for a in acts:
                    if a[1] == 'sit_beside':
                        dur = float((a[2] or {}).get('dur', 1.2))
                        a[1] = 'glide_sit'; a[2] = {'to': a1, 'dur': dur, 'bob': 0.0}
                s['view'] = 'q_right'
                s['_y_floor'] = at[1]
    elif seated and sh['set'] == 'cabin_now':                              # sitting on our floor: the hips on the boards
        s['_y_floor'] = at[1]
        at = [at[0], at[1] + 0.26 * at[2]] + at[2:]
    elif sh['set'] == 'stairs' and sh['view'] == 'section':                # the dollhouse: small figures on the treads
        tr = sorted([an for k, an in sp.anchors.items() if k.startswith('tread')], key=lambda an: an.x)
        if tr:
            if at[0] < tr[0].x - 40: y = sp.anchors['you_top'].y if 'you_top' in sp.anchors else at[1]
            elif at[0] > tr[-1].x + 60: y = sp.anchors['gold_floor'].y if 'gold_floor' in sp.anchors else at[1]
            else: y = min(tr, key=lambda an: abs(an.x - at[0])).y
            at = [at[0], y, at[2] * 1.7, 0.95]                                # in front of the cutaway's layers
    if sh['set'] in FLOOR_SETS and cam3 is not None and not seated and not s.get('kneel') and at[1] < 1040 \
            and not (s.get('in_glass') or s.get('through_glass') or s.get('reflection') or s.get('tiny')) \
            and not (sh['set'] == 'mirror' and who == 'queen') and s.get('_y_floor') is None:
        P = _ray_floor(sp, at[0], at[1])
        if P is not None:
            a2 = _anchor_at(sp, P, who)
            if a2 is not None and a2[2] > 30:
                at[2] = min(max(at[2], 0.75 * a2[2]), 1.33 * a2[2])
    s['at'] = at; s['acts'] = acts
    return s


def place(sp, spec, at, sh):
    """Layer depth for a cast member in a room3d view. The rooms are cached in distance bands (near / mid / far); a person
    goes just in front of the band that holds the floor under their feet (or, off the cabin floor, the nearest named
    anchor: the treads, the doorway), so the furniture behind them stays behind and the near occluders stay in front.
    Busts, hands and inserts go just in front of the mid band. Returns None to keep the plan's depth."""
    cam3 = sp.info.get('cam3')
    bm = getattr(cam3, '_bandmap', None) if cam3 is not None else None
    if not bm or sh['set'] not in FLOOR_SETS + ('stairs',): return None
    if spec.get('in_glass') or spec.get('through_glass') or spec.get('reflection') or spec.get('inside') or spec.get('tiny'):
        return None
    if sh['set'] == 'mirror' and spec['who'] == 'queen': return None
    bands = [l for l in list(sp)[:len(bm)]]
    if len(bands) < len(bm) or any(callable(l.depth) for l in bands): return None
    mode = spec.get('mode', 'body')
    i = 1 if len(bm) > 1 else 0
    near = min(float(l.depth) for l in bands)
    if mode not in ('body', 'legs', 'silhouette'):          # busts, hands, feet: in front of the whole room
        return max(0.3, near - 0.012) if near < 1.0 else None
    if isinstance(at, (list, tuple)) and len(at) >= 3 and float(spec.get('_y_floor', at[1])) >= 1040:
        return max(0.3, near - 0.012)                       # feet below the frame: a foreground (OTS) figure
    if isinstance(at, (list, tuple)) and len(at) >= 3:
        x, y = float(at[0]), float(spec.get('_y_floor', at[1]))
        d = None
        if sh['set'] in FLOOR_SETS:
            P = _ray_floor(sp, x, y)
            if P is not None: d = cam3.dist(P)
        if d is None and sp.anchors:
            an = min(sp.anchors.values(), key=lambda an: math.hypot(an.x - x, (an.y - y) * 1.5))
            if math.hypot(an.x - x, an.y - y) < 500: d = an.depth * float(sp.info.get('d0') or 1.0)
        if d is not None:
            for j, (a, b, _ld) in enumerate(bm):
                if (a <= d or a <= -1e8) and d < b: i = j; break
    return max(0.3, float(bands[i].depth) - 0.012)


# ==================================================================================================== travelling shots (cam3)
def _cam3_spec(set_, spec):
    """A cam3 key -> (pos, look, fov, roll) in the set's world: a view name of the set (its plan camera), or a dict
    {view?, pos?, look?, fov?, roll?, dp?, dl?} (dp / dl move the view's position / look point by metres)."""
    import sets_v2 as S2
    from engine.room3d import Cam3, v3
    base = None
    vname = spec if isinstance(spec, str) else spec.get('view')
    if vname:
        if set_ == 'cabin_now': base = S2.OURS_CAMS[vname]
        elif set_ == 'cabin_dawn': base = S2.THEIRS_CAMS[vname]
        elif set_ == 'stairs': base = S2.STAIRS_CAMS['ots_climb_down' if vname == 'ots_climb' else vname]
        elif set_ == 'mirror':
            c = S2.mirror_cam(vname); base = (tuple(c.C), tuple(c.C + c.R[2]), c.fov, 0.0)
        else: raise KeyError('cam3 view %s/%s' % (set_, vname))
    if isinstance(spec, dict) and spec.get('mview'):              # a mirror view's camera, in the cabin (OURS) model
        c = S2.mirror_cam(spec['mview']); base = (tuple(c.C), tuple(c.C + c.R[2]), c.fov, 0.0)
    pos, look, fov, roll = base if base is not None else (None, None, 70.0, 0.0)
    if isinstance(spec, dict):
        pos = spec.get('pos', pos); look = spec.get('look', look)
        fov = spec.get('fov', fov); roll = spec.get('roll', roll)
        if spec.get('dp'): pos = tuple(np.asarray(pos, float) + np.asarray(spec['dp'], float))
        if spec.get('dl'): look = tuple(np.asarray(look, float) + np.asarray(spec['dl'], float))
    return tuple(map(float, pos)), tuple(map(float, look)), float(fov), float(roll or 0.0)


def campath_of(sh):
    """The CamPath3 of a travelling shot: monotone cubic through the keys under a glide (alive at both cuts, no stops)."""
    from engine.room3d import CamPath3, glide
    c3 = sh['cam3']
    keys = [(float(t),) + _cam3_spec(sh['set'], spec) for t, spec in c3['keys']]
    g = list(c3.get('glide') or [])
    v0, v1, ramp = (g + [0.45, 0.6, 0.8][len(g):])[:3]
    return CamPath3(keys, warp=glide(keys[0][0], keys[-1][0], v0, v1, ramp), lam=float(c3.get('arc', 0.6)))


def _ray_floor_cam(cam3, x, y, yplane=0.0):
    qx, qy = (x - cam3.cx) / cam3.f, -(y - cam3.cy) / cam3.f
    dirv = cam3.R.T @ np.array([qx, qy, 1.0])
    if abs(dirv[1]) < 1e-6: return None
    s_ = (yplane - cam3.C[1]) / dirv[1]
    if s_ <= 0.15: return None
    return cam3.C + dirv * s_


def _world_fn(sh, spec, sp0):
    """Where a cast member stands in a travelling shot: f(t) -> world floor point, or None (busts, hands, feet and POV
    entries keep their screen place). spec['w'] = [x, y, z] or keys [[t, x, y, z], ...] (a walk); a seat on Noah's bunk
    (THEIRS); a named anchor of the set; else the plan's screen point cast onto the floor through the view it was
    framed in (spec['_view'], default the shot's view)."""
    import sets_v2 as S2
    from engine.room3d import Cam3, mono_cubic
    mode = spec.get('mode', 'body')
    if mode not in ('body', 'legs', 'silhouette'):
        # hands, busts and feet framed in a view (not POV): pinned to the glass (mirror) or to a plane at the subject's
        # distance, so they stay put in the room while the camera travels (projected, and scaled by distance)
        at = spec.get('at')
        if (spec.get('pov') and not spec.get('pin')) or not isinstance(at, (list, tuple)) or len(at) < 3: return None
        vname = spec.get('_view') or sh['view']
        try:
            pos, look, fov, roll = _cam3_spec(sh['set'], vname)
        except KeyError:
            return None
        c0 = Cam3(pos, look=look, fov=fov, roll=roll)
        if spec.get('w') is not None:                                  # pinned at a world point, at[2] = size seen from the view
            P = np.asarray(spec['w'], float)
            f = lambda t: P
            f.plane = (max(0.05, c0.dist(P)), float(at[2]), list(at[3:]))
            return f
        qx, qy = (float(at[0]) - c0.cx) / c0.f, -(float(at[1]) - c0.cy) / c0.f
        dirv = c0.R.T @ np.array([qx, qy, 1.0])
        if sh['set'] == 'mirror':
            O, U, V, w_, h_, n = S2.mirror_plane(0.0)
            den = float(np.dot(dirv, n))
            if abs(den) < 1e-6: return None
            s_ = float(np.dot(O - c0.C, n)) / den
        else:
            s_ = float(sp0.info.get('d0') or 1.0)
        if s_ <= 0.05: return None
        P = c0.C + dirv * s_
        dref = c0.dist(P)
        f = lambda t: P
        f.plane = (dref, float(at[2]), list(at[3:]))
        return f
    w = spec.get('w')
    if w is not None:
        if isinstance(w[0], (list, tuple)):
            ts = [float(k[0]) for k in w]; cols = [[float(k[j]) for k in w] for j in (1, 2, 3)]
            return lambda t: np.array([mono_cubic(ts, c, t) for c in cols])
        P = np.asarray(w, float); return lambda t: P
    who = spec['who']
    ch_ = bunk_chart(who, sh['t0'] + 0.01) if sh['set'] == 'cabin_dawn' else None
    if ch_ is not None:
        P = np.asarray(ch_[0], float); return lambda t: P
    if spec.get('seated') and sh['set'] == 'cabin_dawn' and who in THEIRS_SEAT:
        P = np.array([FEET_X, 0.0, THEIRS_SEAT[who]]); return lambda t: P
    at = spec.get('at')
    pts = S2.OURS_PTS if sh['set'] in ('cabin_now', 'mirror') else (S2.THEIRS_PTS if sh['set'] == 'cabin_dawn' else {})
    if isinstance(at, str):
        if at in pts:
            P = np.asarray(pts[at][0], float); return lambda t: P
        return None
    if not isinstance(at, (list, tuple)) or len(at) < 3 or sh['set'] not in ('cabin_now', 'cabin_dawn'): return None
    vname = spec.get('_view') or sh['view']
    try:
        pos, look, fov, roll = _cam3_spec(sh['set'], vname)
    except KeyError:
        return None
    P = _ray_floor_cam(Cam3(pos, look=look, fov=fov, roll=roll), float(at[0]), float(at[1]))
    if P is None: return None
    return lambda t: P


# ==================================================================================================== the film
class Film:
    def __init__(self, tl=None, plan_path=PLAN):
        self.tl = tl if tl is not None else (json.load(open(TIMELINE)) if os.path.exists(TIMELINE) else {'lines': []})
        self.P = json.load(open(plan_path))
        self.shots = self.P['shots']
        self.index = {s['id']: k for k, s in enumerate(self.shots)}
        _by_time(self.shots)
        self._starts = [s['t0'] for s in self.shots]
        self.duration = float(self.P['meta']['duration'])
        self.cards = {rc['n']: rc for rc in self.P['rule_cards']}
        self.counter = self.P['counter']
        self.L = self.tl.get('lines', [])
        self.UI = ui_v2.UI(self.P, self.tl)
        self._built = OrderedDict()

    # ---------------------------------------------------------------- lookup / build
    def idx_at(self, t):
        return max(0, min(len(self.shots) - 1, bisect.bisect_right(self._starts, t) - 1))

    def shot_at(self, t): return self.shots[self.idx_at(t)]

    def built(self, k):
        if k in self._built:
            self._built.move_to_end(k); return self._built[k]
        b = self.build(k)
        self._built[k] = b
        while len(self._built) > 4: self._built.popitem(last=False)
        return b

    def shot_grade(self, sh, sp=None):
        g = sh.get('grade') or sh.get('look')
        if sh['set'] == 'rule_mirror': return card_grade(self, sh)
        if g in GRADES: return g
        if sp is not None and sp.grade in GRADES: return sp.grade
        return WORLD_GRADE.get(sh.get('world'), 'neutral')

    def build(self, k, sh=None, t_shift=0.0):
        sh = sh or self.shots[k]
        chars = sh['chars']
        if sh['set'] == 'rule_mirror' and not chars:
            chars = _card_chars(self, sh)
        if sh['id'] in REPLACE_CHARS:
            chars = REPLACE_CHARS[sh['id']](self, sh)
        if sh['id'] in EXTRA_CHARS:
            chars = list(chars) + EXTRA_CHARS[sh['id']](self, sh)
        s2 = dict(sh, chars=chars) if chars is not sh['chars'] else sh
        s_set = dict(s2, chars=[c for c in chars if not c.get('_glass_rel')]) if any(c.get('_glass_rel') for c in chars) else s2
        sp = ST.build_shot(s_set)
        B = Built(); B.sh, B.idx, B.sp = sh, k, sp
        B.dyn = None
        if sh.get('cam3'):
            return self._build_dyn(B, k, sh, s2, s_set, chars, t_shift)
        layers = list(sp); rigs = []; subj = []
        for spec in chars:
            spec2 = dict(spec)
            if spec2.get('_glass_rel'):
                g = sp.info.get('glass')
                if g is None or len(g) < 3: continue
                gx = [float(q[0]) for q in g]; gy = [float(q[1]) for q in g]
                fx_, fy_, fs_ = spec2['_glass_rel']
                gh = max(gy) - min(gy)
                spec2['at'] = [min(gx) + fx_ * (max(gx) - min(gx)), min(gy) + fy_ * gh, fs_ * gh / 600.0]
            ov = SEAT.get((sh['id'], spec2['who']))
            if ov and ov.get('skip'): continue
            if ov: spec2.update({k_: v_ for k_, v_ in ov.items() if k_ not in ('scale', 'skip')})
            try:
                at = ST.resolve_at(sp, spec2)
            except KeyError as e:
                _warn((sh['id'], 'at'), 'anchor %s: %s' % (sh['id'], e)); continue
            if ov and ov.get('scale') and isinstance(at, (list, tuple)):
                at = list(at); at[2] = float(at[2]) * float(ov['scale'])
            spec2['at'] = at
            try:
                spec2 = stage(sp, spec2, sh); at = spec2['at']
            except Exception as e:
                _warn((sh['id'], 'stage'), 'stage %s: %r' % (sh['id'], e))
            if spec2.get('_skip'): continue
            if spec2.get('mode') == 'lying' and spec2.get('lie') and sp.info.get('cam3') is not None:
                # review round 2 (B17): a person lying in a bunk of a room view: the body runs along the mattress (head end ->
                # feet end, world points), sized by the room camera (the plan's at[2] was a scale, so nobody was drawn)
                c3_ = sp.info['cam3']
                Ph, Pf = (np.asarray(p_, float) for p_ in spec2['lie'])
                if c3_.dist(Ph) > 0.2 and c3_.dist(Pf) > 0.2:
                    (hx_, hy_), (fx_, fy_) = c3_.pt(Ph), c3_.pt(Pf)
                    L_body = float(spec2.get('lie_k', 0.95)) * math.hypot(fx_ - hx_, fy_ - hy_)
                    at = [(hx_ + fx_) / 2, (hy_ + fy_) / 2, L_body]
                    spec2['_rot'] = math.degrees(math.atan2(fy_ - hy_, fx_ - hx_))
                    if abs(spec2['_rot']) > 90: spec2['_rot'] -= 180.0 * (1 if spec2['_rot'] > 0 else -1); spec2['_facing'] = -1
                    spec2['at'] = at
            try:
                dep = place(sp, spec2, at, sh)
            except Exception as e:
                dep = None; _warn((sh['id'], 'place'), 'place %s: %r' % (sh['id'], e))
            if dep is not None and isinstance(at, (list, tuple)) and not spec.get('_depth'):
                # (an explicit _depth in the plan wins: review round 2, B12: the taped hand belongs at the railing's depth; in
                # front of the whole room a 1.8x dolly blew it up and swept it off the frame)
                if spec2.get('mode', 'body') in ('body', 'legs', 'silhouette'):
                    at = list(at[:3]) + [dep]
                else:
                    spec2['_depth'] = dep
            spec2['at'] = at
            try:
                rig = CH.CharRig(spec2, s2)
            except Exception as e:
                _warn((sh['id'], spec['who'], 'rig'), 'rig failed %s %s: %r' % (sh['id'], spec['who'], e)); continue
            mode = spec2.get('mode', 'body')
            st_ = {} if (rig.who == 'tess' and mode == 'body') else None
            if spec2.get('reflection') and sh['set'] == 'mirror':            # in the glass: behind the lipstick on it
                try: spec2['_depth'] = float(sp.layer('lipstick').depth) + 0.001
                except KeyError: pass
            if spec2.get('reflection') and mode == 'hands':                 # the hand on the glass AND its reflection
                real = dict(spec2, reflection=False); real.pop('_depth', None)
                layers.append(_char_layer(rig, at, mode, None, sh, real, sp))
                at = [float(at[0]) + 0.34 * float(at[2]), float(at[1]) - 0.04 * float(at[2])] + list(at[2:])
            L_ = _char_layer(rig, at, mode, st_, sh, spec2, sp)
            if st_ is not None: _hook_beam(sp, rig, at, L_, st_)
            layers.append(L_); rigs.append(rig)
            if not spec2.get('reflection') and not spec2.get('ots'): subj.append((mode, L_))   # an OTS shoulder is never the focus
        layers += self._split_replays(sh)
        dl = ui_v2.doc_layer(sh)
        if dl is not None: layers.append(dl)
        B.layers, B.rigs = layers, rigs
        B.cam = make_cam(sh, k, t_shift)
        B.grade, B.focus, B.dof = self.shot_grade(sh, sp), sp.focus, sp.dof
        if subj and B.dof:                     # the subject is in focus wherever its layer sits (busts in front of the room)
            pick = [L_ for m_, L_ in subj if m_ in ('bust', 'hands', 'feet', 'lying')] or [L_ for m_, L_ in subj]
            if not callable(pick[0].depth): B.focus = float(pick[0].depth)
        B.post = None
        if sh.get('cls') == 'face' and not any(c['who'] == 'queen' for c in chars):
            try: B.post = 0.5 * float(get_grade(B.grade).p['bloom'])
            except Exception: B.post = None
        return B

    def _build_dyn(self, B, k, sh, s2, s_set, chars, t_shift=0.0):
        """A travelling shot: the camera (CamPath3) moves through the 3D room; the view is rebuilt for every frame's camera
        (sets_v2.MOVE) and the cast stands at world points (or walks along world keys), projected per frame."""
        sp = B.sp
        d0 = float(sp.info.get('d0') or 1.0)
        B.dyn = dict(path=campath_of(sh), d0=d0, memo={}, s_set=s_set, chars=[])
        for spec in chars:
            spec2 = dict(spec)
            if spec2.get('_glass_rel'): continue
            ov = SEAT.get((sh['id'], spec2['who']))
            if ov and ov.get('skip'): continue
            if ov: spec2.update({k_: v_ for k_, v_ in ov.items() if k_ not in ('scale', 'skip')})
            wf = _world_fn(sh, spec2, sp)
            if wf is None:
                try:
                    at = ST.resolve_at(sp, spec2)
                except KeyError:
                    at = [960, 540, 600]
                spec2['at'] = at
                try: spec2 = stage(sp, spec2, sh)
                except Exception as e: _warn((sh['id'], 'stage'), 'stage %s: %r' % (sh['id'], e))
            else:
                spec2['at'] = [960, 900, 600]
                try: spec2 = stage(_NoSet(), spec2, sh)
                except Exception as e: _warn((sh['id'], 'stage'), 'stage %s: %r' % (sh['id'], e))
            try:
                rig = CH.CharRig(spec2, s2)
            except Exception as e:
                _warn((sh['id'], spec['who'], 'rig'), 'rig failed %s %s: %r' % (sh['id'], spec['who'], e)); continue
            hm = HEIGHT_M.get(spec2['who'], 1.74) * float((ov or {}).get('scale', 1.0))
            B.dyn['chars'].append((rig, wf, hm, spec2))
        B.layers, B.rigs = list(sp), [c[0] for c in B.dyn['chars']]
        B.cam = make_cam(sh, k, t_shift)
        B.grade, B.focus, B.dof = self.shot_grade(sh, sp), sp.focus, sp.dof
        B.post = None
        return B

    def _dyn_layers(self, B, t):
        """The layers of a travelling shot at film time t (see _build_dyn)."""
        import sets_v2 as S2
        D = B.dyn
        cam = D['path'](t)
        s_set = D['s_set']
        ch = (s_set.get('props') or {}).get('changes_in_shot')
        if ch:                                    # the props as they are at t (the towel comes off, the mirror appears)
            pr = {k: v for k, v in s_set['props'].items() if k != 'changes_in_shot'}
            for tt, kw in ch:
                if tt <= t: pr.update(kw)
            s_set = dict(s_set, props=pr)
        S2.MOVE = {'cam': cam, 'd0': D['d0'], 'memo': D['memo']}
        try:
            sp = ST.build_shot(s_set)
        finally:
            S2.MOVE = None
        L = list(sp)
        for l in L: l.cache = False
        bm = getattr(cam, '_bandmap', None) or []
        d0 = D['d0']
        for rig, wf, hm, spec in D['chars']:
            mode = spec.get('mode', 'body')
            if wf is None:
                at = spec['at']
                if mode not in ('body', 'legs', 'silhouette') and not spec.get('_depth'):
                    # review round 2: POV hands / feet / busts on screen ride in front of the room (at depth 1.0 they were
                    # drawn behind the near band of a travelling shot: your finger vanished behind the glass)
                    spec = dict(spec, _depth=0.32)
                L.append(_char_layer(rig, at, mode, None, B.sh, spec, sp))
                continue
            P = wf(t)
            dist = cam.dist(P)
            pl = getattr(wf, 'plane', None)
            if pl is not None:                                             # pinned to the glass / a plane: scale by distance
                if dist < 0.08: continue
                x, y = cam.pt(P)
                at_ = [x, y, pl[1] * pl[0] / dist] + pl[2]
                spec_ = dict(spec, _depth=0.58)
                if spec.get('reflection') and B.sh['set'] == 'mirror':
                    try: spec_['_depth'] = float(sp.layer('lipstick').depth) + 0.001
                    except KeyError: pass
                    if mode == 'hands':                                    # the hand on the glass AND its reflection
                        real = dict(spec, reflection=False, _depth=0.58)
                        L.append(_char_layer(rig, at_, mode, None, B.sh, real, sp))
                        at_ = [float(at_[0]) + 0.34 * float(at_[2]), float(at_[1]) - 0.04 * float(at_[2])] + list(at_[2:])
                L.append(_char_layer(rig, at_, mode, None, B.sh, spec_, sp))
                continue
            # review round 2 (B8): a figure the camera passes close to fades out over the last half metre (it was culled in
            # one frame at 0.3 m: Tess's jacket filled the frame and vanished); the fade follows the camera's distance to the
            # nearest of the feet, the middle and the head, so it is as smooth as the camera move
            dnear = min(cam.dist(np.asarray(P, float) + np.array([0.0, fr_ * hm, 0.0])) for fr_ in (0.0, 0.55, 0.92))
            nf = smoothstep(clamp((dnear - 0.2) / 0.3)) if spec.get('mode', 'body') in ('body', 'legs', 'silhouette') else 1.0
            if nf <= 0.01: continue
            if dist < 0.35:
                # feet behind the lens (she looms over you): place the figure by its middle, else by its head
                for fr in (0.55, 0.92):
                    Pm = np.asarray(P, float) + np.array([0.0, fr * hm, 0.0])
                    dm = cam.dist(Pm)
                    if dm >= 0.3: break
                if dm < 0.3: continue                                      # the camera passes through / behind them
                xm, ym = cam.pt(Pm); h = hm * cam.f / dm
                x, y, dist = xm, ym + fr * h, dm
            else:
                x, y, h, _ = cam.anchor(P, hm, d0)
            dep = 1.0
            for (a, b, ld) in bm:                 # in front of its band; nearer people in front of farther ones
                if (a <= dist or a <= -1e8) and dist < b: dep = max(0.3, float(ld) - 0.02 + 0.0008 * min(dist, 10.0)); break
            if spec.get('front') and bm:          # review round 2 (B10): standing on the tread just below the camera, she belongs in
                dep = max(0.3, min(float(ld_) for (_a, _b, ld_) in bm) - 0.03)   # front of the near band (the treads hid her feet)
            Lc = _char_layer(rig, [x, y, h, dep], mode, None, B.sh, spec, sp)
            if nf < 0.999: Lc.alpha = float(Lc.alpha) * nf
            L.append(Lc)
        return L

    def _split_replays(self, sh):
        """SPLIT panels that replay a film time (src_t, the loop twins): the cast of the source shot, drawn at
        src_t + (t - t0) inside that panel's half (the set panels are composed by sets.split_view the same way)."""
        out = []
        if not sh.get('split') or sh['chars']: return out
        for j, pan in enumerate((sh['split'].get('panels') or [])[:2]):
            if pan.get('src_t') is None: continue
            src = float(pan['src_t'])
            so = self.shot_at(src + 0.02)
            dt = src - sh['t0']
            ox = -480.0 if j == 0 else 480.0
            for spec in so['chars']:
                if spec.get('mode') != 'bust' or isinstance(spec.get('at'), str): continue
                try:
                    rig = CH.CharRig(dict(spec), so)
                except Exception as e:
                    _warn((sh['id'], 'split'), 'split replay %s: %r' % (sh['id'], e)); continue
                at = list(spec['at'])

                def draw(pen, t, rig=rig, at=at, ox=ox, j=j, dt=dt):
                    cv = pen.cv; cv.save()
                    cv.clipRect(skia.Rect.MakeLTRB(-2000 if j == 0 else 960, -2000, 960 if j == 0 else 4000, 4000))
                    cv.translate(ox, 0)
                    try: rig.draw(pen, t + dt, at=at)
                    except Exception as e: _warn((sh['id'], 'splitdraw'), 'split draw %s: %r' % (sh['id'], e))
                    cv.restore()
                out.append(Layer(1.0, draw, 'char_split%d_%s' % (j, rig.who), ref_depth=1.0))
        return out

    # ---------------------------------------------------------------- montage tiles
    def _montage_built(self, k, j, src):
        key = ('montage', k, j)
        if key in self._built:
            self._built.move_to_end(key); return self._built[key]
        sh = self.shots[k]; tile = sh['montage'][j]
        so = self.shot_at(src)
        ref = so if so['set'] == 'cabin_now' else None
        if ref is None:
            for o in reversed(self.shots[:self.idx_at(src) + 1]):
                if o['set'] == 'cabin_now' and o['var'] in ('night', 'doorway_glow', 'red'): ref = o; break
        var = 'red' if (ref and ref['var'] == 'red') else 'night'      # the doorway's gold spill blows the sill out
        dt = src - tile['t']
        props = dict(so['props'], doorway='none', mirror='glass')             # only the sill is in shot
        s2 = dict(sh, id='%s_m%d' % (sh['id'], j), t0=round(sh['t0'] + dt, 3), t1=round(sh['t1'] + dt, 3), props=props,
                  var=var, world='climax' if var == 'red' else 'ours', grade='climax_v2' if var == 'red' else 'night_v2',
                  montage=None, hud=[], chars=[])
        B = self.build(k, s2, t_shift=dt)
        B.sh = sh
        self._built[key] = B
        while len(self._built) > 6: self._built.popitem(last=False)
        return B

    # ---------------------------------------------------------------- frame
    def fx_at(self, B, t, k):
        fx = B.fx(t)
        sh = B.sh; u = t - sh['t0']
        if B.post is not None and 'bloom' not in fx:              # people's close-ups: half bloom (white fear eyes glowed)
            fx['bloom'] = B.post
        if 'sat' not in fx and sh.get('world') != 'climax':           # colourfulness p50 measured 44 (target >= 45);
            fx['sat'] = SAT_LIFT                                       # the climax keeps its red share (19 % lifted)
        tr_ = LIGHT_TRIM.get(sh.get('world'))                      # the light arc, measured on the preview (DIRECTION 2.1)
        if tr_:
            for (a_, b_, ev) in tr_:
                if a_ <= t < b_: fx['exposure'] = fx.get('exposure', 0.0) + ev
        tr = sh['tr']
        if tr == 'glitch' and u < 2.0 / FPS + 1e-6:
            fx['glitch'] = 0.95; fx['static'] = max(fx.get('static', 0.0), 0.5)
            fx['white'] = max(fx.get('white', 0.0), 0.5)          # a hard pop of light on the stinger frame
        elif tr == 'white' and u < 3.0 / FPS + 1e-6:
            fx['white'] = max(fx.get('white', 0.0), 0.9 * (1.0 - u / (3.5 / FPS)))
        for e in sh.get('fx_post') or []:
            d = e.get('dur', 0.08)
            if e['t'] <= t < e['t'] + d:
                uu = (t - e['t']) / max(1e-3, d)
                for key, v in e.items():
                    if key in ('t', 'dur', 'note', 'rewind', 'pixel_sort'): continue
                    if not isinstance(v, (int, float)): continue
                    if key == 'white': v = v * (1.0 - 0.75 * uu)
                    fx[key] = fx.get(key, 0.0) + v if key == 'exposure' else max(fx.get(key, 0.0), v)
        return fx

    def _render(self, k, t, i, hud=True, B=None, tr=None):
        B = B or self.built(k)
        cs = B.cam.at(t if tr is None else tr)
        fx = self.fx_at(B, t if tr is None else tr, k)
        sh = self.shots[k]
        hf = (lambda cv, tt: self.UI.hud(cv, t, sh, cs, self)) if hud else None
        layers = self._dyn_layers(B, t if tr is None else tr) if B.dyn else B.layers
        img = render_frame(layers, cs, t if tr is None else tr, i, focus=B.focus, dof=B.dof, lens=None, grade=B.grade,
                           post=fx, hud=hf)
        return img

    def _shot_frame(self, k, t, i, hud=True):
        """One shot's picture at t (HUD optional), montage tiles resolved."""
        sh = self.shots[k]
        if sh.get('montage'):
            src = ui_v2.montage_source_t(sh, t)
            if src is not None:
                j = max(jj for jj, tl in enumerate(sh['montage']) if t >= tl['t'])
                B = self._montage_built(k, j, src)
                return self._render(k, t, i, hud, B=B, tr=src)
        return self._render(k, t, i, hud)

    def _blend_ok(self, k):
        """Shot k may blend with the shot before it (no blend out of a card, a black or into one)."""
        sh = self.shots[k]
        if k <= 0 or sh['tr'] not in TR_WIN: return False
        if sh['tr'] == 'flow' and sh['side'] == 'card': return self.shots[k - 1]['side'] not in ('black', 'card')   # into the mirror
        return self.shots[k - 1]['side'] not in ('black', 'card') and sh['side'] not in ('black', 'card')

    def frame(self, t, i=None):
        if i is None: i = int(round(t * FPS))
        k = self.idx_at(t); sh = self.shots[k]
        other, u, kind, kin = None, None, None, None
        if self._blend_ok(k):
            pre, post = TR_WIN[sh['tr']]
            if t < sh['t0'] + post:
                other, kind, kin = k - 1, sh['tr'], k
                u = (t - (sh['t0'] - pre)) / (pre + post)
        if other is None and k + 1 < len(self.shots) and self._blend_ok(k + 1):
            nx = self.shots[k + 1]
            pre, post = TR_WIN[nx['tr']]
            if t >= sh['t1'] - pre:
                other, kind, kin = k + 1, nx['tr'], k + 1
                u = (t - (nx['t0'] - pre)) / (pre + post)
        if other is None:
            img = self._shot_frame(k, t, i)
        else:
            u = clamp(u)
            a = self._shot_frame(min(k, other), t, i, hud=False)
            b = self._shot_frame(max(k, other), t, i, hud=False)
            if kind == 'dissolve':
                w = ease_in_out(u)
                img = cv2.addWeighted(a, 1.0 - w, b, w, 0.0)
            elif kind == 'flow':
                img = flow_blend(a, b, u, self.shots[kin].get('flow'))
            elif kind == 'pan':
                img = pan_blend(a, b, u, float(self.shots[kin].get('pan_dir', 1.0)))
            else:
                img = paper_dissolve(a, b, u, self.shots[kin]['side'] == 'memory')
            B = self.built(k)
            cs = B.cam.at(t)
            img = overlay_hud(img, lambda cv, tt: self.UI.hud(cv, t, sh, cs, self), t)
        return self.UI.frame_fx(img, t, sh, i)

    # ---------------------------------------------------------------- picture events for the final SFX sync
    def events(self, path=EVENTS, write=True):
        """film_events.json (audio/cues.py --events): actual cut times, the picture's actions as SFX cues (acting clips)
        matched to the plan's cue ids (retimed when the picture differs by >= 10 ms, new cues where the plan has none,
        plan walk cues replaced by the picture's own steps) and the picture's hit times (camera hits, punch-ins, white /
        glitch cuts, tags, red X, cards, giant numbers, stamps). The v2 plan already carries every HUD device cue
        (cards, ring ticks, stamps, glints, rewinds); they are kept at their plan times."""
        SP = json.load(open(SOUND))
        plan = {}; kc = {}
        for c in SP['sfx']:
            key = (c['shot'], c['name']); k = kc.get(key, 0); kc[key] = k + 1
            plan.setdefault(key, []).append(dict(id='%s:%s:%d' % (c['shot'], c['name'], k), t=c['t'], used=False, params=c.get('params') or {}, name=c['name']))
        FAM = {'footsteps_porch': 'footsteps', 'footsteps_gravel': 'footsteps', 'footsteps_wood_inside': 'footsteps',
               'footsteps_run': 'footsteps', 'bare_foot_step': 'footsteps', 'wet_footstep': 'footsteps',
               'cloth_grab': 'cloth', 'towel_cloth': 'cloth', 'jacket_cloth': 'cloth', 'cloth_press': 'cloth', 'towel_whip': 'cloth',
               'glass_tap': 'glass', 'nail_click_glass': 'glass', 'glass_wipe': 'glass', 'lipstick_smear': 'glass',
               'impact_hit': 'hit', 'stinger': 'hit', 'braam': 'hit', 'sub_drop': 'hit', 'flash_hit': 'hit', 'number_thump': 'hit',
               'bell_cracked': 'bell', 'bell_clean': 'bell', 'mattress_creak': 'bed', 'bed_creak': 'bed', 'whoosh': 'whoosh',
               'glint_whoosh': 'whoosh'}
        famidx = {}
        for (sid, name), lst in plan.items():
            famidx.setdefault((sid, FAM.get(name, name)), []).extend(lst)
        out_sfx, hits, actions, drop = [], [], [], []

        def span(c):
            p_ = c['params']
            if p_.get('dur'): return float(p_['dur'])
            return 0.45 * (int(p_.get('n', 1)) - 1) if int(p_.get('n', 1) or 1) > 1 else 0.0

        def drop_walks(sid, evs):
            byfam = {}
            for (name, t) in evs: byfam.setdefault(FAM.get(name, name), []).append(t)
            for fam, ts in byfam.items():
                if fam != 'footsteps' or len(ts) < 2: continue
                for cand in famidx.get((sid, fam), []):
                    sp_ = span(cand)
                    if sp_ <= 0 or cand['used']: continue
                    inside = [t for t in ts if cand['t'] - 0.25 <= t <= cand['t'] + sp_ + 0.25]
                    if len(inside) >= 2:
                        cand['used'] = True; cand['dropped'] = True; drop.append(cand['id'])

        def match(sid, name, t, ev):
            for cand in plan.get((sid, name), []):
                if not cand['used'] and abs(cand['t'] - t) <= 0.3:
                    cand['used'] = True
                    if abs(cand['t'] - t) >= 0.01: out_sfx.append({'id': cand['id'], 't': round(t, 4)})
                    return
            for cand in famidx.get((sid, FAM.get(name, name)), []):
                if cand.get('dropped'): continue
                if abs(cand['t'] - t) <= 0.25: return            # the plan already sounds this action
            for o in out_sfx:                                    # two walkers in step: one louder cue, not two
                if 'id' not in o and o['name'] == name and abs(o['t'] - t) < 0.02:
                    o['gain_db'] = round(o.get('gain_db', 0.0) + 2.0, 1); return
            e = dict(ev); e['t'] = round(t, 4); e['name'] = name; e.setdefault('shot', sid)
            out_sfx.append(e)

        for k, sh in enumerate(self.shots):
            sid = sh['id']
            rigs_ = []
            chars_ = list(sh['chars'] or []) + (EXTRA_CHARS[sid](self, sh) if sid in EXTRA_CHARS else [])
            for spec in chars_:
                if spec.get('_glass_rel') or (SEAT.get((sid, spec['who'])) or {}).get('skip'): continue
                try:
                    sp0 = dict(spec, at=spec['at'] if not isinstance(spec.get('at'), str) else [960, 540, 600, 1.0])
                    sp0 = stage(_NoSet(), sp0, sh)                  # the same acting as the picture (no set geometry)
                    rigs_.append(CH.CharRig(sp0, sh))
                except Exception:
                    continue
            drop_walks(sid, [(e['name'], float(e['t'])) for r_ in rigs_ for e in r_.events
                             if e.get('name') and sh['t0'] - 0.05 <= float(e['t']) <= sh['t1'] + 0.3])
            for rig in rigs_:
                for e in rig.events:
                    t = float(e['t'])
                    if not (sh['t0'] - 0.05 <= t <= sh['t1'] + 0.3) or not e.get('name'): continue
                    ev = {'gain_db': round(float(e.get('gain_db', -6.0)), 1), 'pan': round(float(e.get('pan', 0.0)), 2),
                          'space': 'close', 'params': dict(e.get('params') or {}), 'hit': False}
                    actions.append({'t': round(t, 3), 'shot': sid, 'what': '%s %s' % (rig.who, e['name'])})
                    match(sid, e['name'], t, ev)
            c = sh['cam']
            for h in c.get('hit') or []: hits.append(float(h[0])); actions.append({'t': h[0], 'shot': sid, 'what': 'camera hit'})
            if c.get('snap'): hits.append(float(c['snap'][0])); actions.append({'t': c['snap'][0], 'shot': sid, 'what': 'punch-in'})
            if sh['tr'] in ('glitch', 'white', 'glint', 'rewind'):
                actions.append({'t': sh['t0'], 'shot': sid, 'what': sh['tr'] + ' cut'})
                if sh['tr'] in ('glitch', 'white'): hits.append(sh['t0'])
            for e in sh.get('fx_post') or []:
                for kk in ('white', 'glitch', 'rewind', 'pixel_sort'):
                    if e.get(kk): actions.append({'t': e['t'], 'shot': sid, 'what': 'in-shot ' + kk}); hits.append(e['t']) if kk in ('white', 'glitch') else None
            for e in sh['hud']:
                ty = e['type']
                if ty == 'tag':
                    hits.append(e['t']); actions.append({'t': e['t'], 'shot': sid, 'what': 'tag ' + e['text']})
                elif ty == 'red_x':
                    hits.append(e['t']); actions.append({'t': e['t'], 'shot': sid, 'what': 'red X'})
                    match(sid, 'stinger', e['t'], {'gain_db': -3.0, 'space': None, 'hit': True})
                elif ty == 'label':
                    actions.append({'t': e['t'], 'shot': sid, 'what': 'label ' + e['text']})
                elif ty == 'rule_card':
                    rc = self.cards[e['n']]
                    hits.append(rc['appear'])
                    actions.append({'t': rc['appear'], 'shot': sid, 'what': 'rule card %d in' % e['n']})
                    ns = (e.get('numeral_stamp') or {}).get('t')
                    if ns: hits.append(float(ns)); actions.append({'t': ns, 'shot': sid, 'what': 'rule card %d numeral stamp' % e['n']})
                    for w_, tw in e.get('words') or []:
                        actions.append({'t': tw, 'shot': sid, 'what': 'card word ' + w_})
                elif ty == 'giant_number':
                    hits.append(e['t']); actions.append({'t': e['t'], 'shot': sid, 'what': 'giant %s' % e.get('value')})
                elif ty == 'stamp':
                    hits.append(round(e['t'] + 0.09, 3)); actions.append({'t': round(e['t'] + 0.09, 3), 'shot': sid, 'what': 'stamp ' + e.get('text', '')})
                elif ty in ('kinetic', 'typebeat', 'diagram', 'doc', 'count_pop', 'chip', 'teaser', 'map', 'sound_rings', 'dials',
                            'eye_line', 'highlight', 'circle', 'balloon', 'level_guide', 'time_card', 'like_sub'):
                    actions.append({'t': e['t'], 'shot': sid, 'what': ty + (' ' + str(e.get('id') or e.get('text') or e.get('n') or '')).rstrip()})
                elif ty == 'phone':
                    actions.append({'t': e['t'], 'shot': sid, 'what': 'phone ' + e['state']})
                    if e['state'] == 'message':
                        for bb in e.get('bubbles', []):
                            match(sid, 'phone_message', bb['t'], {'gain_db': -6.0, 'space': 'close', 'hit': False})
                    elif e['state'] == 'connected' and abs(e['t'] - e.get('timer_from', -1)) < 0.05:
                        match(sid, 'phone_pickup', e['t'], {'gain_db': -4.0, 'space': 'close', 'hit': False})
        for (tc, v, kind) in self.counter['steps']:
            sh = self.shot_at(tc); sid = sh['id']
            actions.append({'t': tc, 'shot': sid, 'what': 'countdown %d (%s)' % (v, kind)})
        hits = sorted(set(round(h, 3) for h in hits))
        out = {'version': 2, 'duration': self.duration,
               'shots': [{'id': s['id'], 't0': s['t0'], 't1': s['t1'], 'tr': s['tr']} for s in self.shots],
               'sfx': sorted(out_sfx, key=lambda e: e['t']), 'drop': sorted(set(drop)), 'music': [], 'hits': hits,
               'actions': sorted(actions, key=lambda a: a['t'])}
        if write:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            json.dump(out, open(path, 'w'), indent=0)
        return out


# ==================================================================================================== transitions
_WIPE = {}


def sepia_wipe(a, b, u, into_memory=True):          # v2's 0.2 s wipe (kept for reference; paper_dissolve replaced it)
    """The paper wipe: the new picture slides in behind a soft diagonal edge with a cream burn, left to right into a
    memory, right to left out of it, in SEPIA_WIPE seconds from the cut."""
    h, w = a.shape[:2]
    key = (w, h)
    if key not in _WIPE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _WIPE[key] = (xx / w + 0.18 * (yy / h - 0.5))
    g = _WIPE[key] if into_memory else (1.0 - _WIPE[key])
    e = ease_in_out(u) * 1.36 - 0.18                    # the edge position (diagonal), passes the whole frame
    soft = 0.05
    m = np.clip((e - g) / soft + 0.5, 0.0, 1.0)[..., None]
    burn = np.exp(-((g - e) / 0.035) ** 2)[..., None]
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    out += burn * np.array([255, 236, 196], np.float32) * 0.55
    return np.clip(out, 0, 255).astype(np.uint8)


_PAPER = {}


def paper_dissolve(a, b, u, into_memory=True):
    """Into / out of a memory (0.45 s): the new picture soaks through the old like ink through paper (a soft, uneven
    dissolve led by a low-frequency paper grain, sweeping left to right into a memory, right to left out of it) with a
    faint cream burn on the soaking edge. No hard edge, no wipe line."""
    h, w = a.shape[:2]
    key = (w, h)
    if key not in _PAPER:
        rng = np.random.RandomState(7)
        n = cv2.resize(rng.rand(9, 16).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.rand(36, 64).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = xx / w + 0.12 * (yy / h - 0.5)
        _PAPER[key] = (np.clip(0.55 * g + 0.3 * n + 0.15 * n2, 0, 1), np.clip(0.55 * (1 - g) + 0.3 * n + 0.15 * n2, 0, 1))
    g = _PAPER[key][0 if into_memory else 1]
    e = ease_in_out(u) * 1.5 - 0.25                 # the soaking front passes the whole frame
    m = np.clip((e - g) / 0.22 + 0.5, 0.0, 1.0)
    m = (m * m * (3 - 2 * m))[..., None]
    burn = (np.exp(-((g - e) / 0.06) ** 2) * math.sin(math.pi * u))[..., None]
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    out += burn * (np.array([255, 236, 196], np.float32) - out) * 0.28
    return np.clip(out, 0, 255).astype(np.uint8)


def flow_blend(a, b, u, focus=None):
    """The travel dissolve (0.5 s) between two places on one move: the outgoing picture keeps travelling and accelerates
    into the focus point (the glass, the doorway, the window: the camera goes through it) while the incoming shot, already
    moving on its own keys, fades up under it."""
    h, w = a.shape[:2]
    fx, fy = (focus or (960.0, 540.0))[:2]
    cx, cy = fx * w / DW, fy * h / DH
    za = 1.0 + 0.45 * u ** 1.6
    M = np.float32([[za, 0, cx * (1 - za)], [0, za, cy * (1 - za)]])
    a2 = cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wgt = ease_in_out(clamp((u - 0.1) / 0.8))
    return cv2.addWeighted(a2, 1.0 - wgt, b, wgt, 0.0)


def pan_blend(a, b, u, d=1.0):
    """The turn between two places that stand side by side (review round 2, merge 1: the notice on the fence, the cabins beyond
    it, back to Tess at the gate): a whip pan in 0.45 s. The outgoing picture slides out (d = +1: the camera turns right, the
    picture moves left) and the incoming one slides in from the other side, both smeared along the pan by a motion blur that
    peaks mid-turn; they cross-fade in the middle third."""
    h, w = a.shape[:2]
    e = ease_in_out(u)
    off_a = -d * e * 0.55 * w
    off_b = d * (1.0 - e) * 0.55 * w
    speed = math.sin(math.pi * u)                         # the blur peaks mid-turn
    k = int(round(speed * 0.09 * w)) | 1
    def shift(img, off):
        M = np.float32([[1, 0, off], [0, 1, 0]])
        out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return cv2.blur(out, (k, 1)) if k > 2 else out
    wgt = ease_in_out(clamp((u - 0.33) / 0.34))
    return cv2.addWeighted(shift(a, off_a), 1.0 - wgt, shift(b, off_b), wgt, 0.0)


def overlay_hud(img, fn, t):
    o4 = cv2.cvtColor(img, cv2.COLOR_RGB2BGRA)
    s = surface_for(o4); cv = s.getCanvas()
    cv.scale(CFG.rw / DW, CFG.rw / DW)
    fn(cv, t)
    del cv, s
    return cv2.cvtColor(o4, cv2.COLOR_BGRA2RGB)


# ==================================================================================================== CLI tools
def _label(img, lab, sub=''):
    cv2.putText(img, lab, (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img, lab, (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (80, 255, 255), 1, cv2.LINE_AA)
    if sub:
        cv2.putText(img, sub[:64], (3, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, sub[:64], (3, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def _sheet(F, ids, prefix, size, tile, cols, per, keep=None):
    tiles = []
    if keep: os.makedirs(keep, exist_ok=True)
    for sid in ids:
        sid, _, tt = sid.partition('@')
        sh = F.shots[F.index[sid]]
        t = float(tt) if tt else round((sh['t0'] + sh['t1']) / 2, 3)
        t_ = time.perf_counter()
        try:
            img = F.frame(t, int(round(t * FPS)))
        except Exception as e:
            import traceback; traceback.print_exc()
            img = np.zeros((CFG.rh, CFG.rw, 3), np.uint8)
            cv2.putText(img, 'ERR %r' % e, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
        dt = time.perf_counter() - t_
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        if keep: cv2.imwrite(os.path.join(keep, '%s_%07.2f.jpg' % (sid, t)), bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
        th = cv2.resize(bgr, (tile, tile * 9 // 16), interpolation=cv2.INTER_AREA)
        _label(th, '%s %.1f %s/%s/%s' % (sid, t, sh['set'], sh['view'], sh['var']), sh.get('frame', '')[:64])
        tiles.append((sid, th))
        print('%s t=%.2f %.2fs luma %.0f' % (sid, t, dt, float(np.median(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)))), flush=True)
        while len(F._built) > 2: F._built.popitem(last=False)
    for pg in range(0, len(tiles), per):
        tl = tiles[pg:pg + per]
        rows = int(math.ceil(len(tl) / cols)); h_, w_ = tl[0][1].shape[:2]
        sheet = np.zeros((rows * h_, cols * w_, 3), np.uint8)
        for j, (_, im) in enumerate(tl): sheet[(j // cols) * h_:(j // cols + 1) * h_, (j % cols) * w_:(j % cols + 1) * w_] = im
        o = '%s_%s_%s.jpg' % (prefix, tl[0][0], tl[-1][0])
        cv2.imwrite(o, sheet, [cv2.IMWRITE_JPEG_QUALITY, 86]); print(o, flush=True)


def _bench(F, ids, n=int(os.environ.get('BENCH_N', '5'))):
    res = []
    for sid in ids:
        sh = F.shots[F.index[sid]]
        ts = [sh['t0'] + (sh['t1'] - sh['t0']) * (j + 0.5) / n for j in range(n)]
        tt = []
        for t in ts:
            a = time.perf_counter(); F.frame(t, int(round(t * FPS))); tt.append(time.perf_counter() - a)
        warm = sorted(tt[1:])
        res.append((sid, sh['set'] + '/' + sh['view'] + '/' + sh['var'], tt[0], warm[len(warm) // 2], warm[-1]))
        print('%s %-40s first %.2fs warm median %.3fs max %.3fs' % res[-1], flush=True)
    res.sort(key=lambda r: -r[3])
    print('HEAVIEST:', ', '.join('%s %.3f' % (r[0], r[3]) for r in res[:10]))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--keep', default=None)
    ap.add_argument('--events', action='store_true')
    ap.add_argument('--bench', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--size', default='960x540')
    ap.add_argument('--tile', type=int, default=320)
    ap.add_argument('--cols', type=int, default=5)
    ap.add_argument('--per', type=int, default=40)
    ap.add_argument('--part', default=None)
    ap.add_argument('ids', nargs='*')
    A = ap.parse_args()
    from engine.core import set_render_size
    if A.bench:
        A.size = '2560x1440' if A.size == '960x540' else A.size
        cv2.setNumThreads(1)              # as in a render worker
    set_render_size(*(int(v) for v in A.size.split('x')))
    F = Film()
    ids = A.ids or [s['id'] for s in F.shots]
    if A.part:
        kk, nn = (int(v) for v in A.part.split('/'))
        chunk = int(math.ceil(len(ids) / nn)); ids = ids[(kk - 1) * chunk: kk * chunk]
    if A.list:
        for s in F.shots: print(s['id'], s['t0'], s['t1'], s['set'], s['view'], s['var'], s['type'], [c['who'] for c in s['chars']])
    elif A.events:
        o = F.events(); print(EVENTS, len(o['sfx']), 'sfx entries', len(o['hits']), 'hits', len(o['actions']), 'actions')
    elif A.bench:
        _bench(F, ids)
    elif A.sheet:
        _sheet(F, ids, A.sheet, A.size, A.tile, A.cols, A.per, A.keep)
