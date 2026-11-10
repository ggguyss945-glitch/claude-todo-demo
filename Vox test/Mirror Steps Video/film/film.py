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
    timeline). Bodies are re-seated on the set's floor (`seat`: the plan's x, y are kept as the aim, the height and layer
    depth come from the room's 3D camera, named anchors where the plan names a place); `reflection` entries are drawn
    mirrored, cool and faint inside the glass, `in_glass` / `through_glass` / `inside` entries are clipped to the glass or
    the phone screen, `soft_focus` entries are blurred;
  - the camera: the plan keys (pushes about 3 %/s, pull-outs, whips, dutch roll in the climax), snaps (punch-ins), hits,
    handheld for shake >= 8;
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
SEPIA_WIPE = 0.20                     # the paper wipe into / out of a memory, from the cut
H._hand = CH.hud_phone_hand           # the cast's hand on the phone UI
_ERR = set()

WORLD_GRADE = {'ours': 'night_v2', 'stairs': 'stairs_v2', 'theirs': 'dawn_v2', 'theirs_break': 'dawn_break_v2',
               'memory': 'memory_sepia', 'climax': 'climax_v2', 'ending': 'ending_v2', 'ui': 'phone_dark', 'black': 'neutral'}


def _warn(key, msg):
    if key in _ERR: return
    _ERR.add(key)
    print('[film] ' + msg, file=sys.stderr, flush=True)


# ==================================================================================================== camera
def make_cam(sh, idx, t_shift=0.0):
    """Cam from the plan keys. The plan's shake is a handheld amplitude: 2 = breathing tripod, 15-26 = nervous hand.
    Linear pushes are extrapolated 0.5 s past both ends (wipes and dissolves never freeze); snaps, hits.
    t_shift moves the whole move in time (MONTAGE tiles replay a framing at its source time)."""
    c = sh['cam']
    ks = [list(map(float, k)) + [0.0] * (5 - len(k)) for k in c['keys']]
    for k in ks: k[0] += t_shift
    ease_ = {'lin': 'lin', 'out': 'out', 'in_out': 'in_out', 'push': 'push'}.get(c.get('ease', 'lin'), 'lin')
    if ease_ == 'lin' and len(ks) >= 2:
        a, b = ks[0], ks[-1]; dt = max(1e-3, b[0] - a[0]); e = 0.5
        rz = math.log(b[3] / a[3]) / dt
        ks = [[a[0] - e, a[1] - (b[1] - a[1]) / dt * e, a[2] - (b[2] - a[2]) / dt * e, a[3] * math.exp(-rz * e), a[4]]] + ks + \
             [[b[0] + e, b[1] + (b[1] - a[1]) / dt * e, b[2] + (b[2] - a[2]) / dt * e, b[3] * math.exp(rz * e), b[4]]]
    elif len(ks) >= 2:
        ks = [[ks[0][0] - 0.5] + ks[0][1:]] + ks + [[ks[-1][0] + 0.5] + ks[-1][1:]]
    shake = float(c.get('shake', 2.0) or 0.0)
    if shake >= 8: amp, hz, rs = shake * 0.45, 0.95, 0.22
    else: amp, hz, rs = max(1.6, shake), 0.6, 0.0
    keys = [tuple(k[:5]) + ((ease_,) if j else ()) for j, k in enumerate(ks)]
    cam = Cam(keys, ease=ease_, shake=amp, shake_hz=hz, seed=idx * 3 + 1, roll_shake=rs)
    if c.get('snap'):
        s = c['snap']; cam.snap(float(s[0]) + t_shift, float(s[1]) if len(s) > 1 else 1.25, float(s[2]) if len(s) > 2 else 0.1)
    for h in c.get('hit') or []:
        cam.hit(float(h[0]) + t_shift, float(h[1]) * 0.75, 0.32, 13.0)
    return cam


# ==================================================================================================== built shot
class Built:
    __slots__ = ('sh', 'idx', 'sp', 'layers', 'cam', 'grade', 'focus', 'dof', 'rigs', 'post')

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

    def draw(pen, t):
        cv = pen.cv
        n = 0
        try:
            if clip is not None:
                cv.save(); cv.clipPath(clip, skia.ClipOp.kIntersect, True); n += 1
            if refl:                                            # a reflection: mirrored about its own x
                cv.save(); cv.translate(mx, 0); cv.scale(-1, 1); cv.translate(-mx, 0); n += 1
            info = rig.draw(pen, t, at=at)
            if store is not None: store['last'] = (t, info)
        except Exception as e:                                  # never kill a render on one bad pose
            _warn((sh['id'], rig.who, type(e).__name__), 'char draw failed %s %s: %r' % (sh['id'], rig.who, e))
        finally:
            for _ in range(n): cv.restore()
    L_ = Layer(d, draw, 'char_' + rig.who, ref_depth=d)
    if refl:
        L_.alpha = 0.42; L_.tint = ('#a9b6ff', 0.45)
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
        if not hp: return r
        hx, hy = float(hp[0]), float(hp[1])
        dx, dy = ax - hx, ay - hy; L = math.hypot(dx, dy) or 1.0
        off = 0.07 * h
        return (hx + dx / L * off, hy + dy / L * off, ax, ay, k)
    B.override = ov


# ==================================================================================================== cast the plan leaves out
def _knot_echo(film, sh):
    """S281 (the ECU of the knot under the 14 YEARS echo): the same hands on the same half-tied lace as S241."""
    src = film.shots[film.index['S241']]
    out = []
    for c in src['chars']:
        c2 = json.loads(json.dumps(c))
        c2['acts'] = [[sh['t0'] - 0.4, a[1], a[2]] for a in c2.get('acts') or []]
        out.append(c2)
    return out


def _glass_pair(film, sh):
    """The mirror reads as glass (error 33): your and Tess's reflections stand in it, faint and cool (placed on the glass
    polygon in build: `_glass_rel` = [x, y, size] as fractions of the glass bbox)."""
    return [dict(who='tess', mode='bust', view='q_right', expr='tense', acts=[], reflection=True, _glass_rel=[0.36, 0.34, 0.15]),
            dict(who='you', mode='bust', view='q_left', expr='dread', acts=[], reflection=True, _glass_rel=[0.64, 0.31, 0.17])]


EXTRA_CHARS = {'S281': _knot_echo, 'S067': _glass_pair, 'S078': _glass_pair}


# ==================================================================================================== staging the cast
SEAT = {        # per-shot overrides: {(shot id, who): {spec keys}} (from the shot checks)
    ('S226', 'tess'): {'at': 'tess_doorway', 'scale': 0.9}, ('S227', 'tess'): {'at': 'tess_doorway', 'scale': 0.9},
    ('S232', 'tess'): {'at': 'tess_doorway', 'scale': 0.9}, ('S295', 'tess'): {'at': 'tess_doorway', 'scale': 0.9},
    # H1: she leans out of the doorway at the mirror spot, half in our blue, half in their gold (the doorway behind her)
    ('S190', 'queen'): {'at': [985, 610, 0.74]},
    ('S173', 'queen'): {'skip': True},      # the set presses her fingertips through the towel; the loose arm read as a club
}
FLOOR_SETS = ('cabin_now', 'cabin_dawn', 'mirror', 'memory')
# standing heights (m) for the room3d views (CAST.md: the queen 1.12x the adults, grown Noah 1.08x you, Noah13 ~0.8x)
HEIGHT_M = {'you': 1.76, 'tess': 1.68, 'noah13': 1.42, 'noah_grown': 1.90, 'queen': 1.97, 'you_kid': 1.30, 'kids': 1.30,
            'counselor': 1.74, 'extras': 1.74, 'mom': 1.66}
# THEIRS: Noah's bunk along the left wall (x 0.08-0.92, z 4.25-6.3); hips on the mattress edge, feet on the floor in front
THEIRS_SEAT = {'noah13': 5.35, 'queen': 4.45, 'you': 4.3, 'noah_grown': 5.2}
SEAT_VIEWS = ('queen_3s', 'master')   # views whose plan guesses miss the mattress (bunk_2s / ots_noah guesses read right)
SEAT_X, FEET_X = 0.85, 1.24
H2_START = (1.45, 0.0, 5.25)          # where she stands before the H2 glide (by the foot of the stairs, in frame)


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


# ==================================================================================================== the film
class Film:
    def __init__(self, tl=None, plan_path=PLAN):
        self.tl = tl if tl is not None else (json.load(open(TIMELINE)) if os.path.exists(TIMELINE) else {'lines': []})
        self.P = json.load(open(plan_path))
        self.shots = self.P['shots']
        self.index = {s['id']: k for k, s in enumerate(self.shots)}
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
        if sh['id'] in EXTRA_CHARS:
            chars = list(chars) + EXTRA_CHARS[sh['id']](self, sh)
        s2 = dict(sh, chars=chars) if chars is not sh['chars'] else sh
        sp = ST.build_shot(s2)
        B = Built(); B.sh, B.idx, B.sp = sh, k, sp
        layers = list(sp); rigs = []; subj = []
        for spec in chars:
            spec2 = dict(spec)
            if spec2.get('_glass_rel'):
                g = sp.info.get('glass')
                if g is None or len(g) < 3: continue
                gx = [float(q[0]) for q in g]; gy = [float(q[1]) for q in g]
                fx_, fy_, fs_ = spec2['_glass_rel']
                gh = max(gy) - min(gy)
                spec2['at'] = [min(gx) + fx_ * (max(gx) - min(gx)), min(gy) + fy_ * gh, fs_ * gh / 600.0 * 1.6]
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
            try:
                dep = place(sp, spec2, at, sh)
            except Exception as e:
                dep = None; _warn((sh['id'], 'place'), 'place %s: %r' % (sh['id'], e))
            if dep is not None and isinstance(at, (list, tuple)):
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
            L_ = _char_layer(rig, at, mode, st_, sh, spec2, sp)
            if st_ is not None: _hook_beam(sp, rig, at, L_, st_)
            layers.append(L_); rigs.append(rig); subj.append((mode, L_))
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
        tr = sh['tr']
        if tr == 'glitch' and u < 2.0 / FPS + 1e-6:
            fx['glitch'] = 0.95; fx['static'] = max(fx.get('static', 0.0), 0.5)
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
        img = render_frame(B.layers, cs, t if tr is None else tr, i, focus=B.focus, dof=B.dof, lens=None, grade=B.grade,
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

    def frame(self, t, i=None):
        if i is None: i = int(round(t * FPS))
        k = self.idx_at(t); sh = self.shots[k]
        other, u, kind = None, None, None
        if sh['tr'] == 'dissolve' and k > 0 and t < sh['t0'] + DISSOLVE / 2:
            other, u, kind = k - 1, 0.5 + (t - sh['t0']) / DISSOLVE, 'dissolve'
        elif k + 1 < len(self.shots) and self.shots[k + 1]['tr'] == 'dissolve' and t >= sh['t1'] - DISSOLVE / 2:
            other, u, kind = k + 1, 0.5 - (sh['t1'] - t) / DISSOLVE, 'dissolve'
        elif sh['tr'] == 'sepia' and k > 0 and t < sh['t0'] + SEPIA_WIPE and self.shots[k - 1]['side'] not in ('black', 'card'):
            other, u, kind = k - 1, (t - sh['t0']) / SEPIA_WIPE, 'sepia'
        if other is None:
            img = self._shot_frame(k, t, i)
        else:
            a = self._shot_frame(min(k, other), t, i, hud=False)
            b = self._shot_frame(max(k, other), t, i, hud=False)
            if kind == 'dissolve':
                w = ease_in_out(clamp(u))
                img = cv2.addWeighted(a, 1.0 - w, b, w, 0.0)
            else:
                img = sepia_wipe(a, b, clamp(u), sh['side'] == 'memory')
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
            for spec in sh['chars'] or []:
                try:
                    rigs_.append(CH.CharRig(dict(spec, at=spec['at'] if not isinstance(spec.get('at'), str) else [960, 540, 600, 1.0]), sh))
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


def sepia_wipe(a, b, u, into_memory=True):
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
