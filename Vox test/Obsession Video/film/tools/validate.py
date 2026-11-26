"""tools/validate.py: the staging validator for "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR
NAME" (film.py).

    python3 tools/validate.py --fps 8             # every check on every shot at 8 fps; exit code 1 on any ERROR
    python3 tools/validate.py --shots 100-140     # a range (the cut / state checks still look at the neighbours)
    python3 tools/validate.py --part A            # lines 0..212 (.. rule six); --part B the rest

It reads the plan the way the renderer builds it (Film(timeline) -> shots -> builders: sets with their anchors, the
inserts, the tape, actors with their clips) and checks what can be checked without looking at pixels, on EVERY shot type:

  FLOOR    feet clear of furniture footprints (sp.walkable where the set has floors), seated figures on seat anchors,
           nobody standing on a seat anchor (on the furniture)
  LEVEL    feet at the height of a floor of the set (the levels of its stand anchors: the house's two floors, the path,
           the step, the stairs' treads)
  GROUND   the ground LINE at --fps: a standing / kneeling figure's lowest contact (soles, knee caps) sits on its feet
           line (tolerance 4 px + 1.2 % of the figure's height), also in the door shots seen from above (foreshortened)
  OVERLAP  two figures closer than 0.32 m on the plan (bodies inside each other)
  REACH    reach / hold contacts that miss their target at full weight (Acting.misses, > 20 design px)
  PROP     a prop held by two hands at once; a held prop that changes hands by jumping
  TOUCH    Evie never touches anyone: her hands / body within 3 % of a figure's height of anyone else's head, chest or
           hands at any sample is an ERROR (her first limit)
  CUTPOS   the same person jumping > 0.8 m across a cut on the same plan
  STATE    the story's states (states()): Adam's hoodie sleeves chalk-white only at Danny's blue door; Evie's stage and
           smile width per EVIE_ARC (or the flash-forward's own stage); her night flatness in night shots; the chalk
           tracker ONLY ME at its night's place (OM_TRACK) and Evie standing ON it; the card (rule n written in order,
           ADAM shows through the scribble only under the landing bulb); grown-ups looking at Evie only in the beats
           where their look holds her back (the porch light, the floodlight, Mom's chair, Mom at the door)
  CAM      a move > 4.2 s; only the camera moving over still figures; an empty set under a moving camera
  LEN      shot lengths + the median / cuts per minute
  LIP      lips move only on the actor's own lines (film.lip_check)
Severity: ERROR (a visible mistake: fix it), WARN (look at it on the strips), INFO. Allowed exceptions are listed in ALLOW
with the reason. The result table goes to stdout and --json (W/shots/validate.json).
"""
import argparse, json, math, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--shots', default=None)
ap.add_argument('--fps', type=float, default=8.0, help='sampling rate of the acting checks')
ap.add_argument('--json', default=os.path.join(HERE, '_work', 'shots', 'validate.json'))
ap.add_argument('--quiet', action='store_true')
ap.add_argument('--no-lip', action='store_true')
ap.add_argument('--part', default=None, help='A (lines 0-212) or B (213-382)')
a = ap.parse_args()

from engine.core import set_render_size
set_render_size(960, 540)
import film as FM
import characters as CH
import sets as ST

t_start = time.time()
F = FM.Film(json.load(open(os.path.join(FM.ALIGN, 'timeline.json'))))
SH = F.shots
N = len(SH)


def sel():
    if not a.shots: return list(range(N))
    out = []
    for part in a.shots.split(','):
        if '-' in part:
            x, y = part.split('-'); out += list(range(int(x), int(y) + 1))
        else: out.append(int(part))
    return [k for k in out if 0 <= k < N]


KS = sel()
if a.part:
    tb = F.t(FM.PART_B) - FM.LEAD - 0.01
    KS = [k for k in KS if (SH[k].t0 < tb) == (a.part.upper() == 'A')]
issues = []


def add(sev, k, check, msg, t=None):
    issues.append(dict(sev=sev, shot=k, t=None if t is None else round(float(t), 2), check=check, msg=msg,
                       t0=round(SH[k].t0, 2) if k is not None else None))


# ---------------------------------------------------------------------------------------------------- allowed exceptions
# (check, shot predicate, reason): an exception is written down here with the reason, never silently skipped
def _line_shot(i):
    return lambda s: s.t0 <= F.t(i) < s.t1


def _lines(*ii):
    return lambda s, who=None: any(s.t0 - 0.05 <= F.t(i) < s.t1 for i in ii)


def _during(*ii):
    """The shot starts inside one of these lines, or one of them starts inside the shot."""
    return lambda s, who=None: any(F.t(i) - 0.3 <= s.t0 <= F.e(i) + 0.3 or s.t0 <= F.t(i) < s.t1 for i in ii)



ALLOW = [
    ('CUTPOS', _during(56, 67, 71, 104, 119, 123, 126, 181, 201, 206, 227, 231, 245, 251, 262, 288, 290, 302), "a time ellipsis or a move between cuts the narration covers (the next dawn, a memory)"),
    ('CUTPOS', lambda s, who='': s.p.get('era') == 'trailer', "the trailer's jump cuts: ONLY ME (and Evie on it) one stretch nearer on every cut"),
    ('LIP', lambda s, who: who == 'evie' and _during(148, 149)(s), "she sings his song on the swings (the score's sung take, not a voice line)"),
    ('LIP', lambda s, who: s.d < 0.5, "a shot under half a second: the mouth-motion rate is noise"),
    ('PROP', _during(302, 303), "two scrubbing brushes (Mom's and Adam's), one bucket"),
    ('LIP', lambda s, who: who == 'evie' and _during(188, 220, 221, 222)(s), "Evie's lips move at the dark window (L188 'Evie's lips moved') / she hums through the slot"),
    ('LIP', lambda s, who: who == 'adam7', "little Adam sings on the tape (his sung line; the tape's lip sync is the song's syllables)"),
    ('STATE', lambda s, who='': s.p.get('era') in ('trailer', 'memory'), "a flash-forward / flashback: the beat's own state"),
]

def allowed(check, sh, who=''):
    for (chk, pred, reason) in ALLOW:
        if chk != check: continue
        try:
            if pred(sh, who): return reason
        except Exception:
            pass
    return None

# ---------------------------------------------------------------------------------------------------- build helpers

PLAN_OF = {'front': 'house', 'room': 'house', 'hall': 'house', 'kitchen': 'house', 'school': 'school', 'play': 'play'}
HOUSE = ('front', 'room', 'hall', 'kitchen')


def stair_Y(x, y): return 0.0          # the stairs' footprint is walkable on its treads (walkers go step anchor to step anchor)


def film_level(sp, room, X, Yp, Y):
    """The set's floor heights: the levels of its stand / kneel anchors (rounded to the centimetre)."""
    lv = sorted({round(s_.Y, 2) for nm, s_ in sp.anchors.items() if '.' not in nm and s_.kind in ('stand', 'kneel')})
    return lv or [0.0]

def in_poly(pt, q, pad=0.0):
    if pad:
        xs = [p[0] for p in q]; ys = [p[1] for p in q]
        if not (min(xs) - pad <= pt[0] <= max(xs) + pad and min(ys) - pad <= pt[1] <= max(ys) + pad): return False
        # a padded axis-aligned test is enough for the house's rectangular rooms
        return True
    return ST.sets_bunny._in_poly(pt, q) if hasattr(ST, 'sets_bunny') else _in_poly(pt, q)


def _in_poly(pt, q):
    x, y = pt; ins = False; n = len(q)
    for i in range(n):
        x1, y1 = q[i]; x2, y2 = q[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / ((y2 - y1) or 1e-12)
            if x < xi: ins = not ins
    return ins


def floor_level(sp, x, y, Y):
    """Expected floor height at plan (x, y) for a figure whose feet are at Y: the stairs' tread, else the level of a room
    containing the point that is closest to Y (the hall and the upstairs corridor overlap on the plan)."""
    s = stair_Y(x, y)
    if s is not None and sp.room in ('hall', 'up', None) and abs(Y - s) < 0.6: return s
    rooms = (sp.info.get('rooms') or {})
    best = None
    for nm, q in rooms.items():
        if nm not in LEVELS: continue
        if _in_poly((x, y), q):
            L = LEVELS[nm]
            if best is None or abs(L - Y) < abs(best - Y): best = L
    return best


def plan_pos(sp, q, t):
    """(X, Yp, Y) of a P entry at time t (static spot or the path's linear interpolation)."""
    path = q.get('path')
    if not path:
        s = FM.spot_of(sp, q['at'], kind=q.get('kind'))
        return (s.X, s.Yp, s.Y)
    keys = []
    for (tk, at) in path:
        s = FM.spot_of(sp, at); keys.append((float(tk), s.X, s.Yp, s.Y))
    if t <= keys[0][0]: return keys[0][1:]
    if t >= keys[-1][0]: return keys[-1][1:]
    for ka, kb in zip(keys, keys[1:]):
        if ka[0] <= t <= kb[0]:
            u = (t - ka[0]) / max(1e-6, kb[0] - ka[0])
            return tuple(ka[j] + (kb[j] - ka[j]) * u for j in (1, 2, 3))
    return keys[-1][1:]


def figure_kind(sp, q):
    s0 = FM.spot_of(sp, q['at'] if q.get('at') is not None else q['path'][0][1], kind=q.get('kind'))
    return q.get('kind') or {'seat': 'seat', 'kneel': 'kneel', 'lie': 'lie'}.get(s0.kind, 'stand'), s0


def cam_mag(cs):
    return cs.zoom * cs.fz * cs.pz


# ---------------------------------------------------------------------------------------------------- ANCHOR: the sets' staging points
seen_sets = set()


def check_anchors(k, sp, room):
    key = (sp.name, room)
    if key in seen_sets: return
    seen_sets.add(key)
    lv = film_level(sp, room, 0, 0, 0)
    for nm, s_ in sp.anchors.items():
        if '.' in nm or s_.kind not in ('stand', 'seat', 'kneel') or nm == 'driver': continue      # the driver sits in the car
        if room == 'now' and nm == 'lamp_spot': lv_ = [ST.BT_G]
        elif room in APT and s_.Yp < -0.05: lv_ = [ST.BT_G, ST.BT_ROAD]
        else: lv_ = lv
        if min(abs(s_.Y - L) for L in lv_) > 0.05:
            add('ERROR', k, 'ANCHOR', 'set %s anchor %r at plan (%.2f, %.2f) stands at %.2f m, its floor is at %s' % (sp.name, nm, s_.X, s_.Yp, s_.Y, '/'.join('%.2f' % L for L in lv_)))


# ---------------------------------------------------------------------------------------------------- per-shot checks
SAMPLE = {}


def sample_times(sh, fps=None):
    fps = fps or a.fps
    n = max(3, int(sh.d * fps))
    return [sh.t0 + 0.02 + (sh.d - 0.04) * j / (n - 1) for j in range(n)]


PARTS = ('head', 'hand_l', 'hand_r', 'foot_l', 'foot_r')
POSEK = ('turn', 'h_turn', 'h_nod', 'look_x', 'look_y', 'smile', 'm_open', 'lean', 'crouch', 'kneel', 'sit', 'walk_amt', 'blink_x')


def acting_amount(acts, ts):
    """How much the actors act over the shot (0 = statues): body parts move (fraction of the figure's height) + pose
    parameters change (turns, looks, mouths, sits)."""
    best = 0.0
    for act in acts:
        if not hasattr(act, 'x0'): continue
        h = max(1.0, getattr(act, 'height', 700.0))
        pts = {p: [] for p in PARTS}; pv = {p: [] for p in POSEK}
        for t in ts:
            P = act.at(t)
            for p in PARTS:
                try: pts[p].append(act.where(t, p))
                except Exception: pass
            for p in POSEK:
                pv[p].append(float(getattr(P, p, 0.0) or 0.0))
        m = 0.0
        for p, xs in pts.items():
            if len(xs) < 2: continue
            arr = np.array(xs)
            m = max(m, float(np.max(np.linalg.norm(arr - arr[0], axis=1))) / h)
        par = max([max(v) - min(v) for v in pv.values() if v] + [0.0])
        best = max(best, m * 4.0, par)
    return best


LIERS = {}
LIE_HALF = 0.85                          # half the length of a lying figure along its axis (m)


ANKLE = 0.038                  # the rig's ankle point above the sole, per unit of figure height (all cast ids)
KNEE = 0.017                   # a kneeling figure's knee point above the floor


def _tol(h): return 4.0 + 0.012 * h


def _ground_one(k, a, line, kind, ts, who, where='set'):
    """Worst gap (+ sinking, - floating) of a figure's ground contact against its ground line over the samples."""
    worst = (0.0, None)
    for t in ts:
        P = a.at(t)
        if abs(getattr(P, 'lie', 0.0)) > 0.05 or getattr(P, 'sit', 0.0) > 0.3 or getattr(P, 'walk_amt', 0.0) > 0.1: continue
        if abs(getattr(P, 'dy', 0.0)) > 2.0: continue            # a clip that carries the figure to another ground point (her chalk slide)
        h = a.height
        # the lowest ground contact (soles, knee caps, and on all fours the palms) must sit ON the line
        cs = [a.where(t, 'foot_l')[1] + ANKLE * h, a.where(t, 'foot_r')[1] + ANKLE * h,
              a.where(t, 'knee_l')[1] + KNEE * h, a.where(t, 'knee_r')[1] + KNEE * h]
        if kind == 'crawl' or getattr(P, 'crawl', 0.0) > 0.5:
            cs += [a.where(t, 'hand_l')[1] - 0.02 * h, a.where(t, 'hand_r')[1] - 0.02 * h]
        # kneeling, the knees and the soles lie at different depths (in a back 3/4 view the soles are nearer the lens and
        # lower on screen): their mean is the ground footprint; standing / on all fours, the lowest contact
        # standing, the two soles straddle the anchor in depth (a 3/4 stance puts the near foot lower): their mean
        if getattr(P, 'kneel', 0.0) > 0.5: g = sum(cs[:4]) / 4.0 - line
        elif len(cs) > 4: g = max(cs) - line
        else: g = max((cs[0] + cs[1]) / 2.0, max(cs[2:4])) - line
        if abs(g) > abs(worst[0]): worst = (g, t)
    g, t = worst
    if t is not None and abs(g) > _tol(a.height):
        sev = 'ERROR' if abs(g) > 2 * _tol(a.height) else 'WARN'
        add(sev, k, 'GROUND', '%s (%s, %s) %s %.0f design px %s its ground line at %.2f s' % (who, kind, where, 'sinks' if g > 0 else 'floats', abs(g),
                                                                                          'below' if g > 0 else 'above', t), t)



def ground_check(k, sh, ts):
    """GROUND: every standing / kneeling figure of a set shot keeps its lowest contact ON its feet line (its spot's
    screen y), sampled at --fps; the door shots seen from above included (the figure is drawn foreshortened on its spot)."""
    if sh.kind != 'set': return
    I = getattr(sh, 'I', {}) or {}; A = getattr(sh, 'A', {}) or {}
    for q in sh.p.get('ppl', []):
        ident = q.get('id', q['who'])
        if q.get('path') or ident not in I or q.get('check') is False: continue
        kind, s0 = figure_kind(sh.sp, q)
        if kind not in ('stand', 'kneel'): continue
        a_ = dict.get(A, ident)
        if a_ is None: continue
        _ground_one(k, a_, s0.y + q.get('dy', 0.0), kind, ts, q['who'])


TOUCH_PARTS = ('head', 'chest', 'hand_l', 'hand_r', 'neck')


def touch_check(k, sh, ts, acts):
    """TOUCH: Evie's hands and head never come within 3 % of a figure's height of anyone else's head, neck, chest or hands
    (in the same shot, both drawn): she cannot touch anyone (her first limit; kid-safe)."""
    ev = [x for x in acts if getattr(x, 'who', '') == 'evie']
    others = [x for x in acts if getattr(x, 'who', '') not in ('evie',) and hasattr(x, 'x0')]
    pp = getattr(sh, '_plan_pos', None) or {}
    for e_ in ev:
        for o in others:
            if 'evie' in pp:                              # on a plan: only figures that stand near her in depth can touch
                oo = pp.get(o.who) or pp.get('adam' if o.who in ('adam', 'adam_night') else o.who)
                if oo is not None and math.hypot(oo[0][0] - pp['evie'][0][0], oo[0][1] - pp['evie'][0][1]) > 0.45: continue
            h = max(40.0, min(e_.height, o.height))
            for t in ts:
                try:
                    ep = [e_.where(t, p_) for p_ in ('hand_l', 'hand_r', 'head')]
                    op = [o.where(t, p_) for p_ in TOUCH_PARTS]
                except Exception:
                    continue
                d = min(math.hypot(a_[0] - b_[0], a_[1] - b_[1]) for a_ in ep for b_ in op)
                if d < 0.03 * h:
                    add('ERROR', k, 'TOUCH', 'Evie within %.0f design px of %s at %.2f s (she never touches anyone)' % (d, o.who, t), t)
                    break

def check_shot(k):
    sh = SH[k]
    p = sh.p
    spec = F._build(sh)
    sh.spec_cam = spec.cam
    ts = sample_times(sh)
    # ---- camera
    try:
        c0 = spec.cam.at(sh.t0 + 0.01); c1 = spec.cam.at(sh.t1 - 0.01)
        mag = abs(math.log(max(1e-6, cam_mag(c1)) / max(1e-6, cam_mag(c0))))
        pan = math.hypot((c1.x + c1.px) - (c0.x + c0.px), (c1.y + c1.py) - (c0.y + c0.py))
    except Exception:
        mag, pan = 0.0, 0.0
    moving = mag > 0.10 or pan > 120.0
    if moving and sh.d > 4.2 and sh.kind in ('set', 'bust', 'ins'):
        add('WARN', k, 'CAM', 'a camera move of %.0f %% zoom / %.0f px over %.1f s (keep moves under ~4 s)' % (mag * 100, pan, sh.d))
    acts = list(getattr(sh, 'actors', []) or [])
    if sh.kind == 'set':
        amt = acting_amount(acts, ts) if acts else 0.0
        if acts and sh.d > 3.0 and (mag > 0.05 or pan > 60) and amt < 0.08:
            add('ERROR', k, 'CAM', 'only the camera moves: %.0f %% zoom over %.1f s while nobody in frame acts (acting %.3f)' % (mag * 100, sh.d, amt))
        if not acts and sh.d > 5.0 and (mag > 0.06 or pan > 80):
            add('WARN', k, 'CAM', 'an empty set held %.1f s under a moving camera (%.0f %% zoom)' % (sh.d, mag * 100))
        SAMPLE[k] = dict(amt=round(amt, 3), mag=round(mag, 3), pan=round(pan, 1))
    # ---- staging on the plan
    if sh.kind == 'set':
        sp = sh.sp
        ppl = p.get('ppl', [])
        pos_end = {}
        for j, q in enumerate(ppl):
            who = q['who']; ident = q.get('id', who)
            kind, s0 = figure_kind(sp, q)
            for t in ([sh.t0 + 0.01 + (sh.d - 0.02) * j / 8.0 for j in range(9)] if q.get('path') else [sh.t0 + 0.01]):
                X, Yp, Y = plan_pos(sp, q, t)
                outdoors = p['room'] in ('front', 'play') or (p['room'] == 'hall' and Yp < 0.06)
                if kind in ('stand', 'kneel', 'floor') and not q.get('sil') and q.get('check', True) and not outdoors:
                    ok, why = sp.walkable(X, Yp) if hasattr(sp, 'walkable') else (True, '')
                    if not ok and stair_Y(X, Yp) is not None and 'stairs' in why: ok = True        # standing on the treads
                    if not ok and 'porch' in why and (Y > -0.15 or any(nm.startswith('porch') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.3
                                                                      for nm, s_ in sp.anchors.items())): ok = True   # on the porch deck / its steps
                    if not ok and any(nm.endswith(('_step', '_top', '_door')) and math.hypot(s_.X - X, s_.Yp - Yp) < 0.75
                                      for nm, s_ in sp.anchors.items() if '.' not in nm and ('his_' in nm or 'b9_' in nm)):
                        ok = True                                  # on a bus's door steps (the footprint covers its steps)
                    if not ok and 'off the floor' in why and p['room'] in ('street', 'lobby', 'school'): ok = True     # outdoors: the sidewalk is no room
                    if not ok and (sp.info.get('floors')):
                        add('ERROR', k, 'FLOOR', '%s at plan (%.2f, %.2f): %s' % (who, X, Yp, why), t)
                    if kind == 'stand' and not q.get('sil') and q.get('surface') != 'stairs':
                        Ls = film_level(sp, p['room'], X, Yp, Y)
                        if min(abs(L_ - Y) for L_ in Ls) > 0.12 and not (p['room'] == 'hall' and Yp < 0.06):
                            add('ERROR', k, 'LEVEL', '%s feet at %.2f m, expected %s (plan %.2f, %.2f)' % (who, Y, '/'.join('%.2f' % L_ for L_ in Ls), X, Yp), t)
                    if False:
                        L = floor_level(sp, X, Yp, Y)
                        tol = 0.2 if stair_Y(X, Yp) is not None else 0.12          # a ramp up the treads is within a riser
                        if L is not None and abs(L - Y) > tol:
                            add('ERROR', k, 'LEVEL', '%s feet at %.2f m, the floor there is at %.2f m (plan %.2f, %.2f)' % (who, Y, L, X, Yp), t)
            if kind == 'seat':
                at = q.get('at')
                if not (isinstance(at, str) and sp.anchors.get(at) is not None and sp.anchors[at].kind == 'seat'):
                    if not q.get('seat_ok'):
                        add('WARN', k, 'FLOOR', '%s sits at a plan point %r, not on a seat anchor (check there is a seat under them)' % (who, at))
            if kind == 'stand' and isinstance(q.get('at'), str) and sp.anchors.get(q['at']) is not None and sp.anchors[q['at']].kind == 'seat':
                add('ERROR', k, 'FLOOR', '%s STANDS on the seat anchor %r (on the furniture)' % (who, q['at']))
            pos_end[ident] = (plan_pos(sp, q, sh.t0 + 0.01), plan_pos(sp, q, sh.t1 - 0.01), bool(q.get('path')))
            if kind == 'lie': LIERS[ident] = True
        # overlaps (fix round 1, fixer C: a lying body is a 1.8 m segment along its axis, not a point: the cop crouched
        # INTO the body at the foot of the stairs and passed, because only its centre was checked)
        ids = list(pos_end)

        def gap(A_, B_, a_lies, b_lies):
            if not (a_lies or b_lies): return math.hypot(A_[0] - B_[0], A_[1] - B_[1]), 0.32
            L_, P_ = (A_, B_) if a_lies else (B_, A_)
            x0_, x1_ = L_[0] - LIE_HALF, L_[0] + LIE_HALF          # the bodies lie along plan x (the anchors' note)
            cx_ = min(max(P_[0], x0_), x1_)
            return math.hypot(P_[0] - cx_, P_[1] - L_[1]), 0.36
        for i1 in range(len(ids)):
            for i2 in range(i1 + 1, len(ids)):
                for w_ in (0, 1):
                    A_, B_ = pos_end[ids[i1]][w_], pos_end[ids[i2]][w_]
                    d_, lim_ = gap(A_, B_, LIERS.get(ids[i1], False), LIERS.get(ids[i2], False))
                    if abs(A_[2] - B_[2]) < 0.5 and d_ < lim_:
                        add('ERROR', k, 'OVERLAP', '%s and %s are %.2f m apart on the plan (inside each other%s)' % (ids[i1], ids[i2], d_,
                            ', the lying body counted along its length' if lim_ > 0.33 else ''))
                        break
        LIERS.clear()
        sh._plan_pos = pos_end
    # ---- contact (reach misses) and props
    for act in acts:
        act.misses = []
    for t in ts:
        for act in acts:
            try: act.at(t)
            except Exception as ex_: add('ERROR', k, 'REACH', '%s pose failed at %.2f: %r' % (act.who, t, ex_), t)
    for act in acts:
        bad = [m for m in (getattr(act, 'misses', None) or []) if m[2] > 20.0 and sh.t0 <= m[0] <= sh.t1]
        if bad:
            worst = max(bad, key=lambda m: m[2])
            why_ = allowed('REACH', sh)
            add('INFO' if why_ else ('ERROR' if worst[2] > 45 else 'WARN'), k, 'REACH', (('(allowed: %s) ' % why_) if why_ else '') + '%s: %d samples miss their contact target (worst %.0f design px at %.2f s, %s hand)'
                % (act.who, len(bad), worst[2], worst[0], 'left' if worst[1] > 0 else 'right'), worst[0])
    # props held by actors, props drawn by the set
    held = {}
    for act in acts:
        for t in ts:
            P = act.at(t)
            for side, pre in ((1, 'hl_'), (-1, 'hr_')):
                pr = getattr(P, pre + 'prop', None)
                if pr: held.setdefault(pr, set()).add((act.who, side))
    for pr, holders in held.items():
        if len(holders) > 1:
            # two holders over a shot is fine when it changes hands (give); check the same instant
            for t in ts:
                now = [(act.who, side) for act in acts for side, pre in ((1, 'hl_'), (-1, 'hr_')) if getattr(act.at(t), pre + 'prop', None) == pr]
                if len(now) > 1 and not allowed('PROP', sh):
                    add('ERROR', k, 'PROP', '%s is held by %s at the same time' % (pr, ' and '.join('%s %s hand' % (w, 'left' if s > 0 else 'right') for w, s in now)), t)
                    break
    # PropTracks inside acts: jumps at state changes are checked through their keys
    for tr in getattr(sh, '_tracks', []) or []:
        prev = None
        for (tk, stt) in tr.keys[1:]:
            if not (sh.t0 - 0.5 <= tk <= sh.t1): continue
            try:
                before = tr.pos(tk - 1.0 / 60); after = tr.pos(tk + 1.0 / 60)
            except Exception:
                continue
            if before[0] > -1e5 and after[0] > -1e5:
                d = math.hypot(after[0] - before[0], after[1] - before[1])
                if d > 40: add('ERROR', k, 'PROP', '%s jumps %.0f design px when it changes state (%s) at %.2f s' % (tr.name, d, stt[0], tk), tk)
    touch_check(k, sh, ts, acts)
    ground_check(k, sh, ts)
    # ---- length
    if sh.d < 0.6 and sh.kind not in ('black',) and not p.get('flash'):
        add('WARN', k, 'LEN', 'a %.2f s shot (too short to read?)' % sh.d)
    lim = 10.5 if sh.kind in ('rule', 'card', 'pause') else (24.0 if sh.kind == 'outro' else 7.0)
    if sh.d > lim and not p.get('long_ok'):
        add('WARN', k, 'LEN', 'a %.2f s %s shot (long: does it keep acting?)' % (sh.d, sh.kind))


# ---------------------------------------------------------------------------------------------------- across cuts
def check_cuts():
    last = {}                           # ident -> (shot k, t1, plan, (X, Yp, Y), era)
    for k in range(N):
        sh = SH[k]
        pos = getattr(sh, '_plan_pos', None)
        if sh.kind == 'set' and pos is not None:
            plan = PLAN_OF.get(sh.p['room'])
            if plan == 'bus': plan = 'bus:%s' % (sh.p.get('set', {}) or {}).get('kind', 'his')      # two buses on one plan
            era = sh.p.get('era', 'now')
            for ident, (p0, p1, walks) in pos.items():
                if ident in last:
                    k0, t1, plan0, pp, era0 = last[ident]
                    gap = sh.t0 - t1
                    entering = any(q.get('enter') and q.get('id', q['who']) == ident for q in sh.p.get('ppl', []))
                    if plan0 == plan and era0 == era and gap < 8.0 and era not in ('recall',) and not sh.p.get('cut') in ('static', 'white') \
                            and not entering and not sh.p.get('montage') and sh.p.get('cut') != 'blink' and True:
                        d = math.hypot(p0[0] - pp[0], p0[1] - pp[1])
                        dY = abs(p0[2] - pp[2])
                        if (d > 0.8 or dY > 0.5) and k in KS:
                            sev = 'ERROR' if gap < 0.05 else 'WARN'
                            if allowed('CUTPOS', sh): sev = 'INFO'
                            add(sev, k, 'CUTPOS', '%s jumps %.2f m (%.2f m up/down) across the cut from shot %d (plan (%.2f, %.2f) -> (%.2f, %.2f), %.1f s between)'
                                % (ident, d, dY, k0, pp[0], pp[1], p0[0], p0[1], gap))
                last[ident] = (k, sh.t1, plan, p1, era)
        # a long stretch of other places resets the memory
        if sh.kind == 'set':
            plan = PLAN_OF.get(sh.p['room'])
            for ident in list(last):
                if last[ident][2] != plan and sh.t0 - last[ident][1] > 3.0: last.pop(ident, None)


# ---------------------------------------------------------------------------------------------------- the story's states

# ---------------------------------------------------------------------------------------------------- the story's states
def T(i): return F.t(i)


TRACK_AT = [(56, 74, 'street'), (104, 108, 'half'), (119, 127, 'foot'), (181, 184, 'step'), (201, 210, 'door'), (213, 302, 'mat')]
ADULTS = ('mom', 'rahman', 'caretaker')
LOOK_OK = [(72, 74), (176, 180), (256, 260), (288, 302), (187, 197)]      # porch light, floodlight, Mom's chair / the door; dinner (her back to the window)


def _in_lines(rngs, t):
    return any(T(i0) - 0.3 <= t < (T(i1) if i1 < len(F.L) else F.duration) for i0, i1 in rngs)


def states():
    for k in KS:
        sh = SH[k]; p = sh.p
        if sh.kind not in ('set', 'bust', 'tape', 'ins', 'rule'): continue
        why = allowed('STATE', sh)
        F._build(sh)
        acts = list(getattr(sh, 'actors', []) or [])
        tm = sh.t0 + 0.5 * sh.d
        for x in acts:
            if not hasattr(x, 'at'): continue
            P = x.at(tm)
            if x.who in ('adam', 'adam_night'):
                ch = float(getattr(P, 'ob_chalk', 0.0) or 0.0)
                want = float(p.get('chalk', 0.0))
                if abs(ch - want) > 0.5:
                    add('ERROR', k, 'STATE', "Adam's hoodie sleeves chalk %.1f, the beat wants %.1f" % (ch, want))
                if ch > 0.5 and (p.get('set') or {}).get('house') != 'danny' and not why:
                    add('ERROR', k, 'STATE', "Adam's sleeves chalk-white away from Danny's blue door")
            if x.who == 'evie':
                exp = CH.evie_stage(tm)
                got = float(getattr(P, 'e_chalk', exp.get('e_chalk', 0.0)) or 0.0)
                if p.get('stage') is None and abs(got - exp.get('e_chalk', got)) > 0.06 and not why:
                    add('ERROR', k, 'STATE', 'Evie smile width %.2f at %.1f s, EVIE_ARC wants %.2f' % (got, tm, exp['e_chalk']))
                fl = float(getattr(P, 'e_night', getattr(P, 'night', 0.0)) or 0.0)
                if FM.is_night(sh) and sh.kind in ('set', 'bust') and fl < 0.05 and p.get('night_k', 1.0) > 0.5 and hasattr(P, 'e_night'):
                    add('WARN', k, 'STATE', 'Evie in a night shot without her chalk-flat night look')
        # the chalk tracker and Evie standing ON it
        if sh.kind == 'set' and p.get('room') == 'front' and (p.get('set') or {}).get('house', 'adam') == 'adam' and not why:
            st = p.get('set') or {}
            tr = st.get('track'); tod = st.get('tod', 'night')
            for i0, i1, want in TRACK_AT:
                if T(i0) - 0.3 <= sh.t0 < T(i1) and tod == 'night' and tr != want:
                    add('ERROR', k, 'STATE', 'the tracker is %r on this night, OM_TRACK wants %r' % (tr, want))
            for q in p.get('ppl', []):
                if q['who'] == 'evie' and tr and q.get('at') != 'on_' + tr:
                    add('ERROR', k, 'STATE', 'Evie at %r, not ON the tracker (on_%s)' % (q.get('at'), tr))
        # the card
        if sh.kind == 'ins' and p.get('name') == 'card':
            kw = p.get('kw'); kw = kw(0.5) if callable(kw) else (kw or {})
            bl = float(kw.get('backlit', 0.0) or 0.0)
            if bl > 0.01 and not (T(233) - 0.3 <= sh.t0 < T(239)):
                add('ERROR', k, 'STATE', 'the card backlit (ADAM through the scribble) outside the landing-bulb beat')
        # grown-ups whose look would hold her back
        if sh.kind == 'set' and any(q['who'] == 'evie' for q in p.get('ppl', [])):
            ad = [q['who'] for q in p.get('ppl', []) if q['who'] in ADULTS]
            if ad and not _in_lines(LOOK_OK, sh.t0):
                add('ERROR', k, 'STATE', '%s in frame with Evie outside the beats where a grown-up\'s look holds her back' % '/'.join(ad))
    # the rule cards in order, each on its own lines
    rs = [(SH[k].t0, SH[k].p['n']) for k in range(N) if SH[k].kind == 'rule']
    if [n for _, n in rs] != list(range(1, 8)):
        add('ERROR', None, 'STATE', 'rule cards out of order: %s' % [n for _, n in rs])
    for t0, n in rs:
        i0 = FM.RULE_LINES[n][0] - 1
        if abs(t0 - (T(i0) - FM.LEAD)) > 0.6: add('WARN', None, 'STATE', 'rule %d card cut at %.2f, its line starts %.2f' % (n, t0, T(i0)))

def check_lips():
    rows = FM.lip_check(F)
    for r in rows:
        if r['shot'] not in KS: continue
        bad = r['move_off'] > 0.35 or (r['lines'] and r['move_on'] < 0.4)
        if not bad: continue
        sh = SH[r['shot']]
        why = None
        for (chk, pred, reason) in ALLOW:
            if chk == 'LIP':
                try:
                    if pred(sh, r['who']): why = reason
                except Exception:
                    pass
        if why:
            add('INFO', r['shot'], 'LIP', '%s: on %.2f off %.2f (allowed: %s)' % (r['who'], r['move_on'], r['move_off'], why))
        else:
            add('ERROR', r['shot'], 'LIP', '%s: mouth moves %.2f/s on its lines, %.2f/s off them (lips only on character lines)' % (r['who'], r['move_on'], r['move_off']))


# ---------------------------------------------------------------------------------------------------- run
for k in KS:
    try:
        check_shot(k)
    except Exception as ex_:
        import traceback; traceback.print_exc(limit=-3)
        add('ERROR', k, 'BUILD', 'the check failed: %r' % ex_)
    F._built.clear()
check_cuts()
states()
if not a.no_lip: check_lips()

ds = np.array([s.d for s in SH])
summary = dict(shots=N, median=round(float(np.median(ds)), 2), p10=round(float(np.percentile(ds, 10)), 2), p90=round(float(np.percentile(ds, 90)), 2),
               cuts_per_min=round(N / F.duration * 60, 1), duration=round(F.duration, 2))
if not (2.0 <= summary['median'] <= 3.0): add('WARN', None if not KS else KS[0], 'LEN', 'median shot %.2f s (target 2-3 s)' % summary['median'])
order = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
issues.sort(key=lambda d: (order[d['sev']], d['check'], d['shot'] if d['shot'] is not None else -1))
cnt = {s: sum(1 for d in issues if d['sev'] == s) for s in order}
by = {}
for d in issues: by.setdefault((d['sev'], d['check']), 0); by[(d['sev'], d['check'])] += 1
if not a.quiet:
    for d in issues:
        if d['sev'] == 'INFO': continue
        print('%-5s %-7s #%-4s %7s  %s' % (d['sev'], d['check'], d['shot'], ('%.2f' % d['t0']) if d['t0'] is not None else '', d['msg']))
print('summary: %s' % json.dumps(summary))
print('by check: %s' % ', '.join('%s %s %d' % (s, c, n) for (s, c), n in sorted(by.items(), key=lambda x: (order[x[0][0]], x[0][1]))))
print('ERROR %d  WARN %d  INFO %d  (%d shots checked in %.0f s)' % (cnt['ERROR'], cnt['WARN'], cnt['INFO'], len(KS), time.time() - t_start))
os.makedirs(os.path.dirname(a.json), exist_ok=True)
json.dump(dict(summary=summary, counts=cnt, issues=issues, camera=SAMPLE), open(a.json, 'w'), indent=1)
sys.exit(1 if cnt['ERROR'] else 0)