"""tools/validate.py: the staging validator for "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (film.py).

    python3 tools/validate.py                      # every check on every shot at 8 fps; exit code 1 on any ERROR
    python3 tools/validate.py --shots 100-140      # a range (the cut / state checks still look at the neighbours)
    python3 tools/validate.py --part A             # lines 0-185 (.. rule six); --part B the rest
    python3 tools/validate.py --json _work/tests/polish/validate.json --fps 8

It reads the plan the way the renderer builds it (Film(timeline) -> shots -> builders: sets with their anchors, floors and
furniture footprints, the cutaway inside the walls with its plate, prop close-ups with their shelf, actors with their clips)
and checks what can be checked without looking at pixels. EVERY shot type is covered (the owner's rule, 23 Nov):

  ANCHOR  set anchors lie on a floor of their level
  FLOOR   feet inside a room's floor and clear of furniture footprints (sp.walkable); seated figures on seat anchors
  LEVEL   feet at the floor height of where they stand (ground floor 0, upstairs WL_UP, yards WL_G, road WL_ROAD, porch)
  GROUND  the ground LINE, sampled at --fps: a standing figure's lower ankle sits at its feet line (ankle = 0.038 h above
          the sole), a kneeling figure's knees on the floor, inside the walls the feet / knees / hands on the cavity's
          plate (B_wall: sh._ground), a prop close-up's box base on its shelf (B_prop: sh._props); tolerance 4 px +
          1.2 % of the figure's height (design px): floating or sinking past it is an ERROR
  VEHICLE a figure's plan point inside a police car's rectangle (street shots with the cruisers at the kerb)
  OVERLAP two figures closer than 0.32 m on the plan (bodies inside each other)
  REACH   reach / hand-over contacts that miss their target at full weight (Acting.misses, > 20 design px)
  PROP    a prop held by two hands at once; a prop drawn by the set AND held (the note, the phone, the pie)
  LIEFRAME a lying figure in a wide shot (lying figures only in close or medium shots: on screen >= 30 % of the width)
  LIEBED  a lying figure on a bed (review 1): its body along the bed's long axis on screen (not across it), its head on the
          bed's top, under the duvet; seen from the bed's foot (kind 'pillow') it must be clipped at the quilt's hem
  VANISH  a person in the shots before AND after (same room, same scene) missing from a people shot between them
  NEAR    a strong push (f >= 2) on a perspective set: near-plane geometry can sweep across a face (review 1 #146): WARN
  FACE    Pell's face beats in 3/4 (a bust of him in profile, |h_turn| > 0.7, is a WARN)
  CUTPOS  the same person jumping > 0.8 m across a cut on the same plan
  STATE   the story's states (see states()): the red flannel on Dad only on moving day (L12-L27), then on Pell; Sam in
          pyjamas at night; Pell masked until Reyes pulls the mask off (L251), bare after; rule seven's line blank until
          "Believe me." (L275); the closet's back wall still before L210; no police light before the sirens (L242) but in
          the flash-forward (L11); the parents' door locked from L220 to the police
  CAM     a move > 4.2 s; only the camera moving over still figures; an empty set under a moving camera
  LEN     shot lengths + the median / cuts per minute
  LIP     lips move only on the actor's own lines (film.lip_check)
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
ap.add_argument('--part', default=None, help='A (lines 0-185) or B (186-311)')
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


def _ws(s, who):
    """Mister Shiver never lip-syncs (his voice comes from the truck / the door / the radio); his jaw drops as acting."""
    return who.startswith('shiver')


def _lines(*ii):
    return lambda s, who=None: any(s.t0 - 0.05 <= F.t(i) < s.t1 for i in ii)


def _during(*ii):
    """The shot starts inside one of these lines, or one of them starts inside the shot."""
    return lambda s, who=None: any(F.t(i) - 0.3 <= s.t0 <= F.e(i) + 0.3 or s.t0 <= F.t(i) < s.t1 for i in ii)


ALLOW = [
    ('LIP', lambda s, who: who.startswith('dad') and _during(9, 26)(s), "Dad laughs (L9 the explanations, L26 'and laughed'): a laugh, not speech"),
    ('CUTPOS', _during(70, 131, 154, 215, 219, 220, 255), "a time ellipsis in the narration (the next morning; another night; he walked there; the memory montage)"),
    ('LIP', lambda s, who: who.startswith('pell') and bool(s.p.get('chew')), "he chews (his own teeth in the mask's slit): acting, not speech"),
    ('LIP', lambda s, who: bool(s.p.get('no_lip')), "a held open mouth (the teeth L200, the snore L193, 'I almost said' L191): a pose, not speech"),
    ('LIP', lambda s, who: who == 'theo' and any(s.t0 - 0.05 <= F.t(i) < s.t1 for i in (162, 163, 164)), "Theo hums his song (a closed mouth)"),
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
HOUSE = ('living', 'kitchen', 'hall', 'boys', 'parents', 'dead')
UPSTAIRS = ('hall', 'boys', 'parents', 'dead')
PLAN_OF = {r: 'house' for r in HOUSE}
PLAN_OF.update(street='street')
LEVELS = {}
STAIR = None


def stair_Y(x, y):
    """The stairs are never walked on camera in this film."""
    return None


def ice_level(sp, room, X, Yp, Y):
    """Expected feet height at plan (X, Yp): the ground floor 0, upstairs WL_UP; outside the yards WL_G or the road
    WL_ROAD, the porch deck 0 and anything within 0.7 m of a staging anchor at its own height (steps, the kerb)."""
    if room in UPSTAIRS: return [ST.WL_UP]
    if room in HOUSE: return [0.0]
    out = [ST.WL_G, ST.WL_ROAD]
    x0, x1, y0, y1 = ST.WL_PORCH
    if x0 - 0.05 <= X <= x1 + 0.05 and y0 - 0.05 <= Yp <= y1 + 0.05: out.append(0.0)
    for nm, s_ in sp.anchors.items():
        if '.' not in nm and s_.kind in ('stand', 'seat') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.7: out.append(s_.Y)
    return out


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


def check_anchors(k, sp):
    key = (sp.name, sp.room)
    if key in seen_sets: return
    seen_sets.add(key)
    rooms = sp.info.get('rooms') or {}
    if not rooms or not any(nm in LEVELS for nm in rooms): return
    for nm, s in sp.anchors.items():
        if '.' in nm: continue
        if s.kind not in ('point', 'stand', 'kneel', 'surface'): continue
        ok = False; cands = []
        for rn, q in rooms.items():
            if rn not in LEVELS: continue
            if in_poly((s.X, s.Yp), q, pad=0.2):
                L = LEVELS[rn]; cands.append(rn)
                st = stair_Y(s.X, s.Yp)
                lo, hi = L - 0.3, L + 2.75
                if st is not None and rn == 'hall': hi = 2.85 + 2.75
                if lo <= s.Y <= hi: ok = True
        if cands and not ok:
            add('ERROR', k, 'ANCHOR', 'set %s anchor %r at plan (%.2f, %.2f) height %.2f m is not on the floor level of %s (y and height swapped?)'
                % (sp.name, nm, s.X, s.Yp, s.Y, '/'.join(cands)))


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
            if a_ is None or q.get('path') or q.get('hush'): continue
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
            if kind in ('lie', 'pillow') and isinstance(q.get('at'), str) and 'bed' in q['at'] or q.get('kind') == 'pillow':
                liebed(k, sh, sp, q, a_, kind, ident)
        cm_ = p.get('c') or {}
        if cm_.get('mv') == 'push' and float(cm_.get('f', 1.0)) >= 2.0 and p.get('ppl'):
            add('WARN', k, 'NEAR', 'push x%.1f on a perspective set with people: check near-plane geometry crossing a face' % float(cm_['f']))
        if p['room'] == 'street' and (p.get('set') or {}).get('police'):            # VEHICLE: nobody inside a cruiser
            cars = [(s_.X, s_.Yp) for nm, s_ in sp.anchors.items() if nm.startswith('police_')]
            for ident, (p0, p1, walks) in (getattr(sh, '_plan_pos', None) or {}).items():
                for (X, Yp, Y) in (p0, p1):
                    for (cx, cy) in cars:
                        if abs(X - cx) < 2.45 and abs(Yp - cy) < 1.0:
                            add('ERROR', k, 'VEHICLE', '%s stands inside a police car at plan (%.2f, %.2f)' % (ident, X, Yp))
        st = p.get('set') or {}
        if p['room'] == 'kitchen' and st.get('note') and 'note' in held:
            add('ERROR', k, 'PROP', "Pell's note lies on the counter (note=True) AND is in %s's hand" % ', '.join(sorted(w for w, _ in held['note'])))
        if p['room'] == 'parents' and st.get('phone_on_stand') and 'phone' in held:
            add('ERROR', k, 'PROP', "Mom's phone is on the nightstand AND in a hand")
    for (a_, line, kind) in getattr(sh, '_ground', None) or []:                  # inside the walls: the cavity's plate
        _ground_one(k, a_, line, kind, ts, a_.who, 'inside the wall')
    for (name, bottom, line) in getattr(sh, '_props', None) or []:               # prop close-ups: the shelf
        if abs(bottom - line) > 3.0:
            add('ERROR', k, 'GROUND', '%s %s %.0f px %s its shelf' % (sh.kind, name, abs(bottom - line), 'below' if bottom > line else 'above'))
    if sh.kind == 'bust' and p.get('who') == 'pell' and abs(p.get('h_turn', 0.0)) > 0.7:
        add('WARN', k, 'FACE', "Pell's face in profile (h_turn %.2f): his face beats are 3/4" % p.get('h_turn', 0.0))



_BEDS = {'theo_bed': 'WL_TBED', 'sam_bed': 'WL_SBED', 'bed_dad': 'WL_PBED', 'bed_mom': 'WL_PBED', 'pillow_dad': 'WL_PBED',
         'pillow_mom': 'WL_PBED', 'theo_head': 'WL_TBED'}


def liebed(k, sh, sp, q, a_, kind, ident):
    """LIEBED (review 1 blocker 1): a lying figure lies ALONG its bed, head on it, under the bedding."""
    B = getattr(ST, _BEDS.get(q.get('at'), ''), None)
    if B is None: return
    if kind == 'pillow':
        if q.get('clip') is None and q.get('hem') is None:
            add('ERROR', k, 'LIEBED', '%s lies in bed seen from its foot without the quilt over the body (no hem clip)' % ident)
        return
    v = sp.view; Y = B.Y1
    h0, h1 = v.p(*B.at(0, -B.d / 2, Y)), v.p(*B.at(0, B.d / 2, Y))         # the bed's long axis (head .. foot) on screen
    tm = (sh.t0 + sh.t1) / 2
    hd = a_.where(tm, 'head'); fl, fr = a_.where(tm, 'foot_l'), a_.where(tm, 'foot_r')
    ft = ((fl[0] + fr[0]) / 2, (fl[1] + fr[1]) / 2)
    bx, by = h1[0] - h0[0], h1[1] - h0[1]; fx, fy = ft[0] - hd[0], ft[1] - hd[1]
    nb, nf = math.hypot(bx, by), math.hypot(fx, fy)
    if nb < 5 or nf < 5: return
    ang = math.degrees(math.acos(min(1.0, abs(bx * fx + by * fy) / (nb * nf))))
    if ang > 35.0:
        add('ERROR', k, 'LIEBED', '%s lies %.0f deg across the bed on screen (lying figures lie along the bed)' % (ident, ang))
    corners = [v.p(*B.at(sx * B.w / 2, sy * B.d / 2, Y)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    pad = 0.12 * max(max(xs) - min(xs), max(ys) - min(ys)) + 0.15 * a_.height
    if not (min(xs) - pad <= hd[0] <= max(xs) + pad and min(ys) - pad - 0.2 * a_.height <= hd[1] <= max(ys) + pad):
        add('ERROR', k, 'LIEBED', "%s's head is off the bed (screen %.0f, %.0f)" % (ident, hd[0], hd[1]))
    if q.get('cover') is False:
        add('WARN', k, 'LIEBED', '%s lies on the bed with no duvet over the body' % ident)


_CANON = {'sam_pj': 'sam', 'mom_pj': 'mom', 'dad_pj': 'dad', 'dad_tee': 'dad', 'pell_bare': 'pell', 'pell_own': 'pell'}


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
        rows.append((k, sh.p['room'], sh.p.get('view'), sh.t0, sh.t1, ids, sh.p.get('era', 'now')))
    for i, (k, room, view, t0, t1, ids, era) in enumerate(rows):
        if not ids and view not in ('wide', 'bed'): continue
        prev = next((r for r in reversed(rows[:i]) if r[1] == room and r[6] == era and r[5]), None)
        nxt = next((r for r in rows[i + 1:] if r[1] == room and r[6] == era and r[5]), None)
        if prev is None or nxt is None or t0 - prev[4] > 25.0 or nxt[3] - t1 > 25.0: continue
        gone = (prev[5] & nxt[5]) - ids
        if view not in ('wide', 'bed') and view != prev[2]: continue       # a detail of the room (a bed, the door) may leave people out
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
        check_anchors(k, sp)
        ppl = p.get('ppl', [])
        pos_end = {}
        for j, q in enumerate(ppl):
            who = q['who']; ident = q.get('id', who)
            kind, s0 = figure_kind(sp, q)
            room_ok = PLAN_OF.get(p['room']) == 'house'
            for t in ([sh.t0 + 0.01, (sh.t0 + sh.t1) / 2, sh.t1 - 0.01] if q.get('path') else [sh.t0 + 0.01]):
                X, Yp, Y = plan_pos(sp, q, t)
                outdoors = p['room'] in HOUSE and Yp < -0.05
                if kind in ('stand', 'kneel', 'floor') and not q.get('sil') and q.get('check', True) and not outdoors:
                    ok, why = sp.walkable(X, Yp) if hasattr(sp, 'walkable') else (True, '')
                    if not ok and stair_Y(X, Yp) is not None and 'stairs' in why: ok = True        # standing on the treads
                    if not ok and 'porch' in why and (Y > -0.15 or any(nm.startswith('porch') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.3
                                                                      for nm, s_ in sp.anchors.items())): ok = True   # on the porch deck / its steps
                    if not ok and any(nm.endswith(('_step', '_top', '_door')) and math.hypot(s_.X - X, s_.Yp - Yp) < 0.75
                                      for nm, s_ in sp.anchors.items() if '.' not in nm and ('his_' in nm or 'b9_' in nm)):
                        ok = True                                  # on a bus's door steps (the footprint covers its steps)
                    if not ok and who.startswith('shiver') and 'truck' in why: ok = True     # in his truck (the window, the cab)
                    if not ok and who.startswith('kessler') and 'kessler' in why and any(nm.startswith('kdoor') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.75
                                                                                    for nm, s_ in sp.anchors.items()): ok = True   # in his doorway
                    if not ok and (sp.info.get('floors')):
                        add('ERROR', k, 'FLOOR', '%s at plan (%.2f, %.2f): %s' % (who, X, Yp, why), t)
                    if kind == 'stand' and not q.get('sil') and not who.startswith('shiver'):     # he climbs fences, cars, roofs
                        Ls = ice_level(sp, p['room'], X, Yp, Y)
                        if p['room'] != 'town' and min(abs(L_ - Y) for L_ in Ls) > (0.12 if p['room'] in HOUSE else 0.3):
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
        if len(holders) > 1 and pr not in ('basket', 'ticket'):        # every waiting-room ghost holds a ticket of their own
            # two holders over a shot is fine when it changes hands (give); check the same instant
            for t in ts:
                now = [(act.who, side) for act in acts for side, pre in ((1, 'hl_'), (-1, 'hr_')) if getattr(act.at(t), pre + 'prop', None) == pr]
                if len(now) > 1:
                    add('ERROR', k, 'PROP', '%s is held by %s at the same time' % (pr, ' and '.join('%s %s hand' % (w, 'left' if s > 0 else 'right') for w, s in now)), t)
                    break
    st = p.get('set', {}) or {}
    if sh.kind == 'set':
        if st.get('egg') and any(pr.startswith('egg') for pr in held):
            add('ERROR', k, 'PROP', 'the egg is drawn by the set (egg=True) AND held by %s' % ', '.join(sorted(w for pr in held if pr.startswith('egg') for w, _ in held[pr])))
        if p['room'] == 'june' and st.get('dress', True) and 'dress_new' in held:
            add('ERROR', k, 'PROP', 'the new yellow dress is on the closet door AND in a hand')
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
                    if ident == 'shiver' and plan0 == 'street': pass       # he scuttles fast between cuts (window -> snow -> roof)
                    elif plan0 == plan and era0 == era and gap < 8.0 and era not in ('recall',) and not sh.p.get('cut') in ('static', 'white') \
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


def states():
    """The story's states against the lines (see the docstring)."""
    t_move0, t_move1 = T(12) - 0.2, F.e(27) + 0.3
    t_unmask = F.w(251, 'pulled') + 1.7
    t_believe = F.w(275, 'believe') - 0.2
    t_slide, t_police = T(210) - 0.2, T(242) - 0.2
    t_lock0, t_lock1 = F.w(220, 'locked') + 0.6, T(242)
    for k in KS:
        sh = SH[k]; p = sh.p
        era = p.get('era', 'now')
        st = p.get('set', {}) or {}
        room = p.get('room') or ((p.get('bg') or [None])[0])
        who = [q['who'] for q in p.get('ppl', [])] + ([p.get('who')] if sh.kind == 'bust' else []) + [b['who'] for b in p.get('busts', [])]
        if era == 'now':
            if 'dad' in who and not (t_move0 <= sh.t0 <= t_move1):
                add('ERROR', k, 'STATE', "Dad in the red flannel ('dad') off moving day: after L27 it is on Pell (use dad_tee / dad_pj)")
            if any(w in ('dad_tee', 'dad_pj') for w in who) and t_move0 <= sh.t0 <= t_move1:
                add('ERROR', k, 'STATE', 'Dad out of his red flannel on moving day (L12-L27)')
            if 'pell_bare' in who and sh.t0 < t_unmask - 1.8:
                add('ERROR', k, 'STATE', 'Pell unmasked before Reyes pulls the mask off (L251)')
            if 'pell' in who and sh.t0 > t_unmask:
                add('ERROR', k, 'STATE', 'Pell masked after Reyes pulled the mask off (L251): pell_bare')
        night = sh.kind in ('set', 'bust') and room not in (None, 'street') and st.get('tod', 'night') not in ('day', 'morning')
        if night and 'sam' in who and era == 'now':
            add('ERROR', k, 'STATE', "Sam in his day tee at night: 'sam_pj'")
        if sh.kind == 'ins' and sh.t0 < t_believe:
            kw = p.get('kw')
            kw0 = kw(0.0) if callable(kw) else (kw or {})
            kw1 = kw(max(0.0, sh.d - 0.05)) if callable(kw) else (kw or {})
            if (p.get('name') == 'rules' and max(kw0.get('seven', 0), kw1.get('seven', 0)) > 0) or \
               (p.get('name') == 'rule' and kw1.get('n') == 7 and kw1.get('write', 0) > 0 and sh.t0 + sh.d * 0.0 < t_believe - 0.5):
                add('ERROR', k, 'STATE', "rule seven's line written before \"Believe me.\" (L275)")
        if room == 'boys' and sh.kind == 'set' and sh.t0 < t_slide and _lv(st.get('slide', 0.0), sh.t0) > 0.01:
            add('ERROR', k, 'STATE', "the closet's back wall slid before L210")
        if sh.kind == 'set' and st.get('police') and T(12) < sh.t0 < t_police:
            add('ERROR', k, 'STATE', 'police light before the sirens (L242)')
        if room == 'parents' and sh.kind == 'set' and t_lock0 < sh.t0 < t_lock1 and not _lv(st.get('lock', 0.0), sh.t0):
            add('ERROR', k, 'STATE', "the parents' door unlocked after Sam locked it (L220)")


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
