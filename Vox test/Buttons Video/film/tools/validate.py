"""tools/validate.py: the staging validator for "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (film.py).

    python3 tools/validate.py --fps 8             # every check on every shot at 8 fps; exit code 1 on any ERROR
    python3 tools/validate.py --shots 100-140     # a range (the cut / state checks still look at the neighbours)
    python3 tools/validate.py --part A            # lines 0-211 (.. rule five); --part B the rest

It reads the plan the way the renderer builds it (Film(timeline) -> shots -> builders: sets with their anchors, floors and
furniture footprints, the microwave-door reflections, inserts with their props, actors with their clips) and checks what
can be checked without looking at pixels. EVERY shot type is covered (the owner's rule, 23 Nov):

  ANCHOR   every standing / seat / kneel anchor of a set lies on the floor of its level (the apartment BT_UP, the street /
           lobby / school ground 0, the narrator's home BT_UP)
  FLOOR    feet inside a room's floor and clear of furniture footprints (sp.walkable), sampled along every walk path;
           seated figures on seat anchors; nobody standing on a seat anchor
  LEVEL    feet at the floor height of where they stand
  GROUND   the ground LINE, sampled at --fps: a standing / kneeling figure's lowest contact (soles, knee caps) sits on
           its feet line (tolerance 4 px + 1.2 % of the figure's height); close shots: the rolling buttons and the flat
           cardigan on the floor line, a button dropped into the jar lands inside the jar's mouth (inserts)
  VEHICLE  a figure's plan point inside the silver car's rectangle (the school lane; the driver sits at 'driver')
  OVERLAP  two figures closer than 0.32 m on the plan (bodies inside each other)
  REACH    reach / hold contacts that miss their target at full weight (Acting.misses, > 20 design px)
  PROP     a prop held by two hands at once; a prop drawn by the set AND held (the tablet on the bed, the headset on the
           desk); the music box / phone / tablet held in a hand that is not there
  KIDSAFE  form 3's fingertips closer than 2.5 cm to Owen's head, neck or hands (her fingers always stop short)
  LIEFRAME a lying figure in a wide shot
  VANISH   a person in the shots before AND after (same room) missing from a people shot between them
  NEAR     a strong push (f >= 2) on a perspective set with people: WARN
  CEILING  form 3 (unfolded) touches the apartment ceiling at her plan point: neck / crown not through it, not in mid-air
  ROOF     the driver's head top under the silver car's roof (1.43 m above the road)
  BUSTLIE  a bust turned >= 45 degrees used as a lying figure (lying figures are drawn lying, on the bed)
  PROPGONE the red coat missing from a set shot of the Blank between two shots that show it (it never pops away / back)
  HANDFACE the Blank's hand (any form) within 2.5 cm of Owen's face or neck (kid-safe; < 0.5 cm is an ERROR)
  CUTPOS   the same person jumping > 0.8 m across a cut on the same plan
  STATE    the story's states (see states()): who wears what (Owen in pyjamas at night, the green coat outdoors), which
           form of the Blank in which beat, Mom's glasses (glare until L277, the two circles only L195-L197), the headset
           lady grey from L205 to "Mom" (L232), Owen's fade level (readable: <= 0.8; gone from the microwave door only in
           rule six), the Brave List's pale rules (R1 after L61, R2 after L93, R4 after L171, all but three after L204,
           blue again by the end of L280)
  CAM      a move > 4.2 s; only the camera moving over still figures; an empty set under a moving camera
  LEN      shot lengths + the median / cuts per minute
  LIP      lips move only on the actor's own lines (film.lip_check)
Severity: ERROR (a visible mistake: fix it), WARN (look at it on the strips), INFO. Allowed exceptions are listed in ALLOW
with the reason. The result table goes to stdout and --json.
"""
import argparse, json, math, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--shots', default=None)
ap.add_argument('--fps', type=float, default=8.0, help='sampling rate of the acting checks')
ap.add_argument('--json', default=os.path.join(HERE, '_work', 'tests', 'polish', 'validate.json'))
ap.add_argument('--quiet', action='store_true')
ap.add_argument('--no-lip', action='store_true')
ap.add_argument('--part', default=None, help='A (lines 0-211) or B (212-384)')
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
    ('LIP', lambda s, who: who.startswith('blank') and _during(115, 208, 209, 210)(s), "the Blank hums the song (a closed mouth): L115 the car, L208-L210 the windowsill"),
    ('CUTPOS', _during(144, 154, 172, 185, 208, 227, 231, 259, 267, 270, 288, 309, 312), "a time ellipsis or a move between cuts the narration covers (that night; I went; after school; standing in my own kitchen; he ran; he walked back to the board)"),
    ('KIDSAFE', _during(273), "the lunge sweeps the counter behind him: the fingertips cross his head on screen a metre behind him in depth"),
    ('LIP', lambda s, who: bool(s.p.get('no_lip')), "a held open mouth (a shout pose): a pose, not speech"),
    ('LIP', lambda s, who: who == 'mom' and _during(219)(s), "L219 is four short phrases with long pauses: the mouth rests in the gaps (it moves on every phrase)"),
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
APT = ('apt', 'owen')
HOUSE = ('apt', 'owen', 'now')
PLAN_OF = {'apt': 'apt', 'owen': 'apt', 'street': 'block', 'lobby': 'block', 'school': 'school', 'now': 'now'}
LEVELS = {}


def stair_Y(x, y):
    """No stairs are walked on camera in this film."""
    return None


def film_level(sp, room, X, Yp, Y):
    """Expected feet height at plan (X, Yp): the apartment and the narrator's home at BT_UP; the street, the lobby and the
    school lane at ground 0 (the road -0.15)."""
    if room in HOUSE: return [ST.BT_UP]
    return [ST.BT_G, ST.BT_ROAD]


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


def extra_checks(k, sh, ts, acts, held):
    p = sh.p
    if sh.kind == 'set':
        sp = sh.sp
        for q in p.get('ppl', []):
            ident = q.get('id', q['who']); a_ = (getattr(sh, 'A', None) or {}).get(ident)
            if a_ is None or q.get('path') or q['who'] == 'blank3': continue
            kind, s0 = figure_kind(sp, q)
            if kind in ('stand', 'kneel'):
                _ground_one(k, a_, a_.y0, kind, ts, ident)
            if kind == 'lie':                                                # LIEFRAME: lying figures only close / medium
                try:
                    cs = sh.spec_cam.at((sh.t0 + sh.t1) / 2)
                    mag = cs.zoom * cs.fz * cs.pz
                except Exception:
                    mag = 1.0
                L_ = a_.height * mag
                if L_ < 0.30 * 1920:
                    add('ERROR', k, 'LIEFRAME', '%s lies in a wide shot (%.0f px long on screen; lying figures only in close or medium shots)' % (ident, L_))
        for q in p.get('ppl', []):                                           # form 3: her feet on the floor line
            a_ = (getattr(sh, 'A', None) or {}).get(q.get('id', q['who']))
            if a_ is None or q['who'] != 'blank3': continue
            for t in ts[::3]:
                if getattr(a_.at(t), 'b3_collapse', 0.0) > 0.05: continue
                fy = CH.b3_point(a_, t, 'foot')[1]
                if abs(fy - a_.y0) > _tol(a_.height * 0.6):
                    add('ERROR', k, 'GROUND', 'form 3 %s %.0f px %s her floor line at %.2f s' % (q.get('id'), abs(fy - a_.y0), 'below' if fy > a_.y0 else 'above', t), t); break
        cm_ = p.get('c') or {}
        if cm_.get('mv') == 'push' and float(cm_.get('f', 1.0)) >= 2.0 and p.get('ppl'):
            add('WARN', k, 'NEAR', 'push x%.1f on a perspective set with people: check near-plane geometry crossing a face' % float(cm_['f']))
        st = p.get('set') or {}
        if p['room'] == 'school' and st.get('car', True):                    # VEHICLE: nobody inside the silver car but its driver
            cx, cy = ST.SC_CAR
            for ident, (p0, p1, walks) in (getattr(sh, '_plan_pos', None) or {}).items():
                q = next((q_ for q_ in p.get('ppl', []) if q_.get('id', q_['who']) == ident), {})
                if q.get('at') == 'driver': continue
                for (X, Yp, Y) in (p0, p1):
                    if abs(X - cx) < 2.35 and abs(Yp - cy) < 0.95:
                        add('ERROR', k, 'VEHICLE', '%s stands inside the silver car at plan (%.2f, %.2f)' % (ident, X, Yp))
        tabs = [pr for pr in held if pr.startswith('tab')]
        if p['room'] in ('owen', 'now') and st.get('tablet_bed') and tabs:
            add('ERROR', k, 'PROP', 'the tablet lies on the bed (tablet_bed) AND is in %s' % ', '.join(sorted(w for pr in tabs for w, _ in held[pr])))
        if p['room'] == 'now' and st.get('headset') and 'headset' in held:
            add('ERROR', k, 'PROP', 'the headset is on the desk AND in a hand')
        if p['room'] == 'apt' and st.get('carton') and any(w in ('owen', 'owen_pj') for pr in tabs for w, _ in held[pr]):
            add('WARN', k, 'PROP', "Owen holds a tablet while his tablet stands on the milk carton")
        # KIDSAFE: form 3's fingertips never within 2.5 cm of Owen's skin (head, neck, hands)
        A = getattr(sh, 'A', None) or {}
        b3 = [a_ for a_ in acts if a_.who == 'blank3']
        kids = [a_ for a_ in acts if a_.who in ('owen', 'owen_pj', 'owen_coat') and not getattr(a_, '_mirror', False)]
        for b in b3:
            for o in kids:
                ppc = o.height / 145.0
                worst = None
                for t in ts:
                    Pb = b.at(t)
                    if getattr(Pb, 'b3_collapse', 0.0) > 0.05: continue
                    for tip in ('tips_l', 'tips_r'):
                        try: tx, ty = CH.b3_point(b, t, tip)
                        except Exception: continue
                        for part in ('head', 'neck', 'hand_l', 'hand_r'):
                            px, py = o.where(t, part)
                            r = (0.09 if part == 'head' else 0.03) * o.height
                            d = (math.hypot(tx - px, ty - py) - r) / ppc
                            if worst is None or d < worst[0]: worst = (d, t, tip, part)
                if worst and worst[0] < 2.5:
                    why_ = allowed('KIDSAFE', sh)
                    add('INFO' if why_ else ('ERROR' if worst[0] < 0.5 else 'WARN'), k, 'KIDSAFE', "form 3's %s is %.1f cm from Owen's %s at %.2f s (her fingers stop short: >= 2.5 cm)" % (worst[2], worst[0], worst[3], worst[1]), worst[1])
    for (name, x, y, box) in getattr(sh, '_lands', None) or []:                  # inserts: a dropped button lands in the jar
        if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
            add('ERROR', k, 'GROUND', '%s lands at (%.0f, %.0f), outside the jar mouth %s' % (name, x, y, box))
    for (name, bottom, line) in getattr(sh, '_props', None) or []:               # floor props: on the floor line
        if abs(bottom - line) > 3.0:
            add('ERROR', k, 'GROUND', '%s %s %.0f px %s its floor line' % (sh.kind, name, abs(bottom - line), 'below' if bottom > line else 'above'))


def extra_checks2(k, sh, ts, acts):
    """Review round 1 (Buttons): CEILING, ROOF, BUSTLIE, HANDFACE (see the module doc)."""
    p = sh.p
    if sh.kind == 'bust' and abs(float(p.get('rot', 0.0) or 0.0)) >= 45.0:
        add('ERROR', k, 'BUSTLIE', 'a %s bust turned %.0f deg stands in for a lying figure' % (p.get('who'), float(p['rot'])))
    if sh.kind != 'set': return
    sp = sh.sp; A = getattr(sh, 'A', None) or {}
    for q in p.get('ppl', []):
        ident = q.get('id', q['who']); a_ = A.get(ident)
        if a_ is None: continue
        if q['who'] == 'blank3' and p.get('room') == 'apt' and not q.get('path'):
            s0 = FM.spot_of(sp, q['at'])
            ceil = sp.view.p(s0.X, ST.BT_UP + ST.BT_CEIL, s0.Yp)[1]
            tol = 3.0 + 0.012 * a_.height
            for t in ts[::2]:
                P_ = a_.at(t)
                if getattr(P_, 'b3_collapse', 0.0) > 0.02 or getattr(P_, 'b3_unfold', 1.0) < 0.99: continue
                G = CH._b3_geom(a_.x0 + P_.dx, a_.y0, a_.height, P_, t)
                top = min(min(y for _, y in G['neck']) - G['nr'], G['head'][1] - 0.5 * G['head_h'])
                if top < ceil - tol:
                    add('ERROR', k, 'CEILING', "form 3's head / neck %.0f px through the ceiling at %.2f s" % (ceil - top, t), t); break
                if top > ceil + tol:
                    add('ERROR', k, 'CEILING', "form 3's head stops %.0f px under the ceiling at %.2f s (it must touch it)" % (top - ceil, t), t); break
        if q.get('at') == 'driver' and p.get('room') == 'school':
            s0 = FM.spot_of(sp, 'driver')
            roof = sp.view.p(s0.X, ST.SC_ROAD + 1.43, s0.Yp)[1]
            for t in ts[::3]:
                hy = a_.where(t, 'head')[1] - 0.075 * a_.height
                if hy < roof - 2.0:
                    add('ERROR', k, 'ROOF', "the driver's head is %.0f px above the car roof line at %.2f s" % (roof - hy, t), t); break
    kids = [a_ for a_ in acts if a_.who in ('owen', 'owen_pj', 'owen_coat') and not getattr(a_, '_mirror', False)]
    blanks = [a_ for a_ in acts if a_.who in ('blank1', 'blank1_shades', 'blank2', 'blank3') and not getattr(a_, '_mirror', False)]
    for b in blanks:
        for o in kids:
            ppc = o.height / 145.0; worst = None
            for t in ts:
                if b.who == 'blank3':
                    if getattr(b.at(t), 'b3_collapse', 0.0) > 0.05: continue
                    hands = [CH.b3_point(b, t, n) for n in ('tips_l', 'tips_r', 'hand_l', 'hand_r')]
                else:
                    hands = [b.where(t, n) for n in ('hand_l', 'hand_r')]
                for (hx, hy) in hands:
                    for part, r in (('head', 0.09), ('neck', 0.035)):
                        px, py = o.where(t, part)
                        d = (math.hypot(hx - px, hy - py) - r * o.height) / ppc
                        if worst is None or d < worst[0]: worst = (d, t, part)
            if worst and worst[0] < 2.5:
                why_ = allowed('HANDFACE', sh)
                add('INFO' if why_ else ('ERROR' if worst[0] < 0.5 else 'WARN'), k, 'HANDFACE', "the Blank's hand is %.1f cm from Owen's %s at %.2f s" % (worst[0], worst[2], worst[1]), worst[1])


_PROPS = {}


def check_propgone():
    """PROPGONE: the red coat in a set shot with the Blank before AND after (< 20 s apart, same room) must be in the
    set shots of the Blank between them (it never vanishes and comes back within a scene)."""
    rows = sorted((k, v) for k, v in _PROPS.items())
    for i, (k, (room, t0, t1, has_b, coat)) in enumerate(rows):
        if not has_b or coat: continue
        prev = next((r for r in reversed(rows[:i]) if r[1][0] == room and r[1][3] and r[1][4]), None)
        nxt = next((r for r in rows[i + 1:] if r[1][0] == room and r[1][3] and r[1][4]), None)
        if prev and nxt and t0 - prev[1][2] < 20.0 and nxt[1][1] - t1 < 20.0:
            add('ERROR', k, 'PROPGONE', 'the red coat is in shots %d and %d but not here (the Blank holds it)' % (prev[0], nxt[0]))


_CANON = {'owen_pj': 'owen', 'owen_coat': 'owen', 'blank1': 'blank', 'blank1_shades': 'blank', 'blank2': 'blank', 'blank3': 'blank'}


def check_vanish():
    """VANISH (review 1 M11): within one scene (same room, < 25 s apart), a person in the room's people shots before AND
    after must not be missing from a people shot (or a wide / bed view) between them."""
    rows = []
    for k in range(N):
        sh = SH[k]
        if sh.kind != 'set': continue
        ids = set()
        for q in sh.p.get('ppl', []):
            if q.get('until') is not None and q['until'] < sh.t1 - 0.2: continue
            ids.add(_CANON.get(q.get('id', q['who']), q.get('id', q['who'])))
            if q.get('hush') or q.get('carry'): ids.add((q.get('hush') or q.get('carry'))['who'])
        rows.append((k, sh.p['room'], 'cam' if sh.p.get('cam') is not None else sh.p.get('view'), sh.t0, sh.t1, ids, sh.p.get('era', 'now')))
    for i, (k, room, view, t0, t1, ids, era) in enumerate(rows):
        if not ids and view not in ('wide',): continue
        prev = next((r for r in reversed(rows[:i]) if r[1] == room and r[6] == era and r[5]), None)
        nxt = next((r for r in rows[i + 1:] if r[1] == room and r[6] == era and r[5]), None)
        if prev is None or nxt is None or t0 - prev[4] > 25.0 or nxt[3] - t1 > 25.0: continue
        gone = (prev[5] & nxt[5]) - ids
        if view not in ('wide',) and view != prev[2]: continue       # a detail of the room (a bed, the door) may leave people out
        if gone and k in KS:
            add('ERROR' if nxt[3] - prev[4] < 12.0 else 'WARN', k, 'VANISH', '%s in shots %d and %d but missing here (%s, %s)' % (', '.join(sorted(gone)), prev[0], nxt[0], room, view))


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
        check_anchors(k, sp, p['room'])
        ppl = p.get('ppl', [])
        pos_end = {}
        for j, q in enumerate(ppl):
            who = q['who']; ident = q.get('id', who)
            kind, s0 = figure_kind(sp, q)
            for t in ([sh.t0 + 0.01 + (sh.d - 0.02) * j / 8.0 for j in range(9)] if q.get('path') else [sh.t0 + 0.01]):
                X, Yp, Y = plan_pos(sp, q, t)
                outdoors = (p['room'] in HOUSE and Yp < -0.05) or (p['room'] == 'now' and q.get('at') == 'lamp_spot')
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
                    if kind == 'stand' and not q.get('sil') :
                        Ls = film_level(sp, p['room'], X, Yp, Y)
                        if min(abs(L_ - Y) for L_ in Ls) > (0.12 if p['room'] in HOUSE else 0.3):
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
                if len(now) > 1:
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
    extra_checks(k, sh, ts, acts, held)
    extra_checks2(k, sh, ts, acts)
    if sh.kind == 'set':
        nms = [getattr(l, 'name', '') or '' for l in (spec.layers or [])]
        has_b = any(q['who'] == 'blank3' for q in p.get('ppl', []))
        coat = any(n.startswith('coat') or n == 'fallen_coat' for n in nms)
        _PROPS[k] = (p.get('room'), sh.t0, sh.t1, has_b, coat)
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
def T(i): return F.t(i)


def _lv(v, t):
    return v(t) if callable(v) else v


NIGHT_PJ = [(0, 11), (34, 77), (93, 107), (143, 146), (150, 171), (208, 211), (212, 316)]     # Owen in pyjamas
COAT = [(25, 30), (111, 140)]                                                                  # Owen outdoors: the green coat
FORMS = {'blank1_shades': [(115, 136)], 'blank1': [(155, 159)], 'blank2': [(2, 3), (62, 77), (160, 182), (189, 211), (327, 339)],
         'blank3': [(237, 297)]}


def _in(rngs, t):
    return any(T(a_) - 0.6 <= t <= F.e(b_) + 0.6 for a_, b_ in rngs)


def states():
    """The story's states against the lines (see the docstring)."""
    for k in KS:
        sh = SH[k]; p = sh.p
        era = p.get('era', 'now')
        tm = (sh.t0 + sh.t1) / 2
        who = [q['who'] for q in p.get('ppl', [])] + ([p.get('who')] if sh.kind == 'bust' else [])
        who += [q['who'] for q in (p.get('mirror') or [])]
        if era == 'now' and sh.kind in ('set', 'bust'):
            for w in who:
                if w in ('owen', 'owen_pj', 'owen_coat'):
                    want = 'owen_pj' if _in(NIGHT_PJ, tm) else ('owen_coat' if _in(COAT, tm) else 'owen')
                    if w != want: add('ERROR', k, 'STATE', 'Owen as %r here, the story has %r (pyjamas at night, the green coat outdoors)' % (w, want))
                if w in FORMS and not _in(FORMS[w], tm):
                    add('ERROR', k, 'STATE', 'the Blank as %r outside its beats (%s)' % (w, ', '.join('L%d-L%d' % r for r in FORMS[w])))
        for a_ in getattr(sh, 'actors', []) or []:
            if sh.kind not in ('set', 'bust'): continue
            for t in (sh.t0 + 0.05, tm, sh.t1 - 0.05):
                P = a_.at(t)
                d = P.__dict__
                if a_.who in ('owen', 'owen_pj', 'owen_coat'):
                    if d.get('faded', 0.0) > 0.82: add('ERROR', k, 'STATE', 'Owen faded %.2f at %.2f s: the viewer must still read him (<= 0.8)' % (d['faded'], t), t)
                    if d.get('refl_hide', 0.0) > 0.5 and not (T(219) <= t <= F.e(222) + 0.5):
                        add('ERROR', k, 'STATE', 'Owen gone from the microwave door outside rule six (L220-L222)', t)
                    if getattr(a_, '_mirror', False) and T(219) <= t <= F.e(222) and d.get('refl_hide', 0.0) < 0.5:
                        add('ERROR', k, 'STATE', 'Owen still in the microwave door at L220-L222 ("I couldn\'t see me")', t)
                if a_.who == 'mom' and era == 'now':
                    g = d.get('pgrey', 0.0)
                    if T(206) <= t <= F.w(232, 'mom') - 0.2 and g < 0.9 and p.get('pgrey') is None:
                        add('ERROR', k, 'STATE', 'the headset lady not pencil grey (%.2f) between L205 and "Mom" (L232)' % g, t)
                    if t >= F.w(232, 'mom') + 1.5 and g > 0.05:
                        add('ERROR', k, 'STATE', 'Mom still grey (%.2f) after he says "Mom" (L232)' % g, t)
                    if d.get('circles', 0.0) > 0.05 and not (T(195) - 0.5 <= t <= F.e(197) + 0.5):
                        add('ERROR', k, 'STATE', "Mom's glasses as two black circles outside L195-L197", t)
                    if d.get('specs', 1.0) < 0.5 and t < T(277) - 0.2:
                        add('ERROR', k, 'STATE', 'Mom without her glasses (green eyes) before she pulls them off (L277)', t)
                    if d.get('specs', 1.0) > 0.5 and t > F.e(277) + 1.0:
                        add('ERROR', k, 'STATE', 'Mom wearing her glasses again after L277', t)
    # the Brave List: pale rules stay pale on later cards; rule three stays blue; all blue again by the end of L280
    INK = FM.INK
    for i, pale, blue in ((81, [1], [2, 3]), (108, [1, 2], [3, 4]), (147, [1, 2], [3, 4]), (183, [1, 2, 4], [3, 5]),
                          (212, [1, 2, 4, 5, 6, 7], [3]), (243, [1, 2, 4, 5, 6, 7], [3])):
        ink = INK(T(i))
        for n in pale:
            if ink[n - 1] > 0.05: add('ERROR', None if not KS else KS[0], 'STATE', 'rule %d not pale on the card at L%d (ink %.2f)' % (n, i, ink[n - 1]))
        for n in blue:
            if ink[n - 1] < 0.95: add('ERROR', None if not KS else KS[0], 'STATE', 'rule %d not blue on the card at L%d (ink %.2f)' % (n, i, ink[n - 1]))
    if min(INK(F.e(280) + 0.5)) < 0.95: add('ERROR', None if not KS else KS[0], 'STATE', 'the Brave List not all blue again after L280')
    if min(INK(T(276))[n] for n in (2,)) < 0.95: add('ERROR', None if not KS else KS[0], 'STATE', 'rule three not blue at the climax')


# ---------------------------------------------------------------------------------------------------- lips
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
check_vanish()
check_propgone()
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
