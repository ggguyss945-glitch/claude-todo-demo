"""characters_evie.py: Evie ("Like forever"), the villain of "If a Girl Is OBSESSED With Being Your Only Friend...
DON'T WRITE YOUR NAME", and her staging tools.

Not imported on its own: characters.py runs it in its own namespace at the end of the module (exec), so everything here
is part of `characters` (import characters as CH). Evie is a v3 cast entry on the existing people rig (faces, lip sync,
poses, look_at, reach_to, hands, props) with her own hair (two braids), outfit (white blouse, navy pinafore), chalk smile,
automatic arc on the film clock (EVIE_ARC) and four forms (normal, obsessed, creepy, drain). See EVIE_API and CAST.md.
"""
# NOTE: runs inside characters.py's globals (math, np, skia, Ctx, HeadMap, Body, CAST, Pose, Acting, _figure3 ... exist).

EVIE_API = """
Evie film cast id: 'evie' (12, shorter than Adam: 1.40 m). One id for every form; her look is driven by EVIE_ARC (film
clock) and pose fields. draw / draw_bust / Acting work as for any cast member.
Arc: EVIE_ARC = [(t, stage, transition)], stages 'mon' 'wed' 'r1'..'r7' 'drain' (EVIE_STAGES). The film sets the real
  times once from the timeline: set_evie_arc({'wed': t, 'r1': t, ...}) or evie_arc_from_lines(lines) (EVIE_CUES = the
  narration line that opens each stage). a.stage(t0, name, t1) overrides one window.
Pose fields: e_chalk 0..1 (chalk smile width; 0 = her real gap-tooth smile), e_unravel 0..1 (braids), e_dust 0..1,
  e_flatn 0..1 (chalk-flat colour at night, used when e_night = 1: a.night()), e_flat 0..1 (extra flatness, any time),
  e_lie 0..1 (lying flat on the ground as a chalk drawing; e_flatk = ground foreshortening, e_lie_dir deg),
  e_neck (neck stretch, body units; e_neck_dx sideways), e_glow 0..1 (phone glow under the chin), e_drain 0..1,
  e_scale (size, for slides in depth), e_stub 0/1 (the chalk stub in her right hand), e_trail (slide smear).
Clips: bounce, laugh_away, wave_hi, blink_now | head_tilt_hold, lens_lock, hold_smile, phone_glow, type_phone,
  one_inch, block_wide, hold_out_bracelet, swing_ride (+ draw_swing), sing_song | lie_flat, slide_flat,
  stand_from_ground, neck_up, drain_away | chalk_tap, night, stage.
Free functions: draw_chalk_girl, draw_sneaker_print, draw_chalk_stub, draw_swing, draw_slot_smile, chalk_word,
  LetterboxFingers (the long fingers through a slot writing on a floor), StubDrop (the stub falling through the slot).
Colours: KEEPING_RED (the Keeping Square, her ribbons, the one sunset), CHALK.
"""

KEEPING_RED = '#b0584f'          # the Keeping Square's faded red: the square, her ribbons, the sunset glow. Nothing else.
KEEPING_RED_SH = '#843f39'
CHALK = '#f2f0e9'
CHALK_SH = '#cbc9c2'
CHALK_DK = '#8f8e8a'

POSE_DEFAULTS.update(e_chalk=0.0, e_unravel=0.0, e_dust=0.0, e_flatn=0.0, e_night=0.0, e_flat=0.0, e_lie=0.0,
                     e_flatk=0.24, e_lie_dir=0.0, e_neck=0.0, e_neck_dx=0.0, e_glow=0.0, e_drain=0.0, e_scale=1.0,
                     e_stub=1.0, e_trail=0.0, e_tx=0.0, e_ty=0.0, e_wind=1.0, _noblink=0.0)

# ====================================================================================================== the cast entry
# Evie, "about 12": shorter than Adam, a round freckled face, a gap-tooth grin, pale grey-blue eyes that open a little too
# wide, two dark braids from a centre parting tied with faded red ribbons, a long-sleeved white blouse with a high round
# collar under an ankle-length navy pinafore (bib, straps, a chalky bib pocket), navy leggings, white sneakers. A worn
# chalk stub always in her right hand, chalk dust on her fingertips.
_EVIE_BODY = dict(sh=84, ch=84, wa=78, hip=82, arm=(34, 29), leg=(39, 32), neck=27, hand=0.8, arm_k=0.9)
_EVIE_FACE = dict(hair='braids', sex='f', hh=226.0, child=True, m=1.40, head_ws=[0, 56, 82, 96, 100, 100, 95, 82, 61, 33, 0],
                  eye_dx=40, eye_y=4, eye_r=21.5, iris_c='#6a8496', iris_k=0.7, lid_rest=0.05, pupil=1.0, brow_th=6.5,
                  nose_len=13, mouth_y=64, mouth_w=16, nose='button', ears=1.0, skin='#f2d0b8', skin_sh='#cba28c',
                  skin_dp='#88645c', blush='#efa497', lip='#c98680', lips=0.15, hair_c='#2a1c17', brow_c='#24170f',
                  bags=0.05, age=0.0, blink_rate=0.35, lashes=0.7, part=0, freckles=1.5, gap=True, kidface=True, fold_k=0.0,
                  mouth_in='#5a2a30', mouth_dk=0.55, mouth_line='#4a2428', tuck_a=110, evie=True)
_EVIE_CL = dict(top='#f3f0e8', top_sh='#c9c3b6', top_hi='#ffffff', collar='#fbf9f3', collar_sh='#d2ccbf',
                pina='#2b3760', pina_sh='#1a2242', pina_hi='#46548c', button='#ece7da', trousers='#243055',
                trousers_sh='#151c36', shoes='#f1efe8', shoes_sh='#bdb9ae', socks='#f1efe8', socks_sh='#c9c5bc', tie=KEEPING_RED)
CAST['evie'] = _v3cast(outfit='pinafore', feet='shoes', body=dict(_EVIE_BODY), cloth=dict(_EVIE_CL), **_EVIE_FACE)
EVIE_CAST = ('evie',)

EXPR.update({
    'evie_grin': dict(smile=0.9, teeth=1.0, m_open=0.32, m_wide=0.25, brow_up=0.3, squint=0.15, pupil=1.05),   # Monday
    'evie_laugh': dict(smile=1.0, teeth=1.0, m_open=0.5, m_wide=0.3, brow_up=0.45, squint=0.7, eye_open=0.45),
    'evie_hold': dict(smile=0.85, teeth=0.75, m_open=0.12, m_wide=0.2, brow_up=0.32, wide=0.3, pupil=0.82),  # too long
    'evie_hurt': dict(smile=0.35, teeth=0.2, brow_sad=0.65, brow_up=0.4, wide=0.2, pupil=0.9),               # "Don't you trust me?"
    'evie_flat': dict(smile=0.25, brow_up=0.12, wide=0.35, pupil=0.62, still=0.7),                           # flat delight
    'evie_hope': dict(smile=0.7, teeth=0.4, m_open=0.08, brow_up=0.6, brow_sad=0.15, wide=0.25),             # "Write your name?"
})

# ====================================================================================================== the arc
# Stages on the film clock (like WINKS_ARC). Width of the chalk smile per the bible's table (R1 her real smile; R2 just
# past the corners; R3 mid-cheek; R4 wider; R5 almost at her ears; R6-R7 ear to ear); blinking stops from Wednesday (the
# OBSESSED form); the braids unravel; more chalk dust; at night (a.night()) her colour goes chalk-flat by e_flatn.
_EV_KEYS = ('e_chalk', '_noblink', 'e_unravel', 'e_dust', 'e_flatn', 'h_tilt', 'wide')
EVIE_STAGES = {
    'mon':   dict(e_chalk=0.00, _noblink=0.0, e_unravel=0.00, e_dust=0.12, e_flatn=0.00, h_tilt=0.0, wide=0.0),
    'wed':   dict(e_chalk=0.00, _noblink=1.0, e_unravel=0.08, e_dust=0.25, e_flatn=0.30, h_tilt=9.0, wide=0.14),
    'r1':    dict(e_chalk=0.00, _noblink=1.0, e_unravel=0.16, e_dust=0.35, e_flatn=0.45, h_tilt=10.0, wide=0.16),
    'r2':    dict(e_chalk=0.25, _noblink=1.0, e_unravel=0.30, e_dust=0.45, e_flatn=0.52, h_tilt=11.0, wide=0.18),
    'r3':    dict(e_chalk=0.42, _noblink=1.0, e_unravel=0.42, e_dust=0.55, e_flatn=0.60, h_tilt=12.0, wide=0.20),
    'r4':    dict(e_chalk=0.58, _noblink=1.0, e_unravel=0.55, e_dust=0.66, e_flatn=0.68, h_tilt=13.0, wide=0.22),
    'r5':    dict(e_chalk=0.80, _noblink=1.0, e_unravel=0.70, e_dust=0.78, e_flatn=0.76, h_tilt=14.0, wide=0.24),
    'r6':    dict(e_chalk=1.00, _noblink=1.0, e_unravel=0.84, e_dust=0.90, e_flatn=0.84, h_tilt=15.0, wide=0.26),
    'r7':    dict(e_chalk=1.00, _noblink=1.0, e_unravel=0.92, e_dust=1.00, e_flatn=0.88, h_tilt=15.0, wide=0.26),
    'drain': dict(e_chalk=1.00, _noblink=1.0, e_unravel=0.95, e_dust=1.00, e_flatn=0.92, h_tilt=12.0, wide=0.26),
}
# the narration line that opens each stage (the film looks up its start time; set_evie_arc takes the times)
EVIE_CUES = {'mon': 'That day, a new girl sat behind me.', 'wed': "Wednesday, at my shoulder... she didn't blink.",
             'r1': 'Rule number one.', 'r2': 'Rule number two.', 'r3': 'Rule number three.', 'r4': 'Rule number four.',
             'r5': 'Rule number five.', 'r6': 'Rule number six.', 'r7': 'Rule number seven.',
             'drain': 'Evie was on our doormat, smiling ear to ear.'}
_EV_ORDER = ('mon', 'wed', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'drain')
# placeholder times (word-count estimates) until the film calls set_evie_arc with the timeline's
_EV_T0 = {'mon': 92.0, 'wed': 118.0, 'r1': 132.0, 'r2': 205.0, 'r3': 250.0, 'r4': 296.0, 'r5': 365.0, 'r6': 420.0,
          'r7': 468.0, 'drain': 560.0}
EVIE_ARC = []


def set_evie_arc(times, transition=0.0):
    """Set EVIE_ARC in place from {stage: start time} (missing stages keep their placeholder). Stages change on cuts
    (between days and nights), so the default transition is 0; Acting objects made earlier see the new arc."""
    tt = dict(_EV_T0); tt.update({k: float(v) for k, v in times.items() if k in EVIE_STAGES and v is not None})
    arc = [(-1e9, 'mon', 0.0)] + [(tt[k], k, transition) for k in _EV_ORDER[1:]]
    arc.sort(key=lambda a: a[0])
    EVIE_ARC[:] = arc
    return EVIE_ARC


def evie_arc_from_lines(lines, transition=0.0):
    """Arc from a timeline's lines: a list of dicts with the line text ('text') and its start ('t0' / 'start' / 't')."""
    def norm(s): return ''.join(ch for ch in s.lower() if ch.isalnum())
    found = {}
    for st, cue in EVIE_CUES.items():
        nc = norm(cue)
        for ln in lines:
            tx = norm(str(ln.get('text', '')))
            if tx and (nc in tx or tx in nc and len(tx) > 8):
                found[st] = ln.get('t0', ln.get('start', ln.get('t')))
                break
    return set_evie_arc(found, transition)


def evie_stage(t, arc=None):
    """Evie's arc parameters at film time t (dict of _EV_KEYS)."""
    return stage_at(t, EVIE_ARC if arc is None else arc, EVIE_STAGES, _EV_KEYS)


set_evie_arc({})
CAST['evie'].update(arc=EVIE_ARC, stages=EVIE_STAGES, stage_keys=_EV_KEYS)


# ====================================================================================================== small helpers
def _cr(pts, n=48):
    """Catmull-Rom spline through pts -> (n, 2) array (end points kept)."""
    p = np.asarray(pts, float)
    if len(p) < 2: return p
    p = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    segs = len(p) - 3
    out = []
    for k in range(n):
        u = k / (n - 1) * segs
        i = min(int(u), segs - 1); s = u - i
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    return np.array(out)


def _arclen(a):
    d = np.hypot(np.diff(a[:, 0]), np.diff(a[:, 1]))
    return np.concatenate([[0.0], np.cumsum(d)])


def _at_len(a, s, L=None):
    """Point and unit tangent at arc length s along polyline a."""
    L = _arclen(a) if L is None else L
    s = min(max(s, 0.0), L[-1])
    i = int(np.searchsorted(L, s, side='right') - 1); i = min(max(i, 0), len(a) - 2)
    seg = L[i + 1] - L[i] or 1e-6
    u = (s - L[i]) / seg
    p = a[i] + (a[i + 1] - a[i]) * u
    tg = a[i + 1] - a[i]; tg = tg / (np.hypot(*tg) or 1e-6)
    return p, tg


def _sub_curve(a, s0, s1, n=24, L=None):
    L = _arclen(a) if L is None else L
    return np.array([_at_len(a, s, L)[0] for s in np.linspace(s0, s1, n)])


def _smoothstep(a, b, x):
    u = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return u * u * (3 - 2 * u)


def _chalk_paint(c_, a, w, dash=None, blur=0.0):
    p = skia.Paint(Color=col(c_, a), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                   StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0.0))
    if blur > 0: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _chalk_stroke(cv, path, w, a=1.0, c_=CHALK, seed=0):
    """A chalk line on cv (path already in canvas coords): a soft dusty halo, a broken core (the grain of chalk on a
    rough surface), and a thin bright centre."""
    if a <= 0.004: return
    cv.drawPath(path, _chalk_paint(c_, 60 * a, w * 1.9, blur=w * 0.35))
    d = max(w * 0.9, 1.0)
    cv.drawPath(path, _chalk_paint(c_, 215 * a, w, dash=(d * 3.1, d * 0.55, d * 1.7, d * 0.4)))
    cv.drawPath(path, _chalk_paint(c_, 150 * a, w * 0.45, dash=(d * 2.3, d * 0.9)))


# ====================================================================================================== hair: two braids
_HAIR3 = _HAIR3 + ('braids',)
_hairline_ev_prev = _hairline


def _hairline(style, part):
    """'braids': a centre parting, combed back behind the ears to two low braids."""
    if style != 'braids': return _hairline_ev_prev(style, part)
    def yf(ph):
        a = np.abs(ph)
        return np.maximum(np.interp(a, [0, 0.35, 0.8, 1.15, 1.35, 1.6, 1.9, 2.3, PI], [-80, -77, -58, -30, -16, -12, 36, 70, 84]),
                          _nape(ph))
    return yf, 8.0


def _ev_braid_curve(hm, side, P, t):
    """Screen points (head units, head frame) and depths of one braid: from behind the ear, down over the front of the
    shoulder, to the chest. Lower points swing a little with the body (secondary motion)."""
    sw = 6.0 * P.sec_x + 2.2 * math.sin(t * 1.3 + side * 1.7)
    L3 = [(side * 86, 30, -46), (side * 90, 96, -34), (side * 86, 162, 6), (side * 77, 226, 44), (side * 70, 292, 54),
          (side * 66, 352, 56)]
    xs = np.array([q[0] for q in L3], float); ys = np.array([q[1] for q in L3], float); zs = np.array([q[2] for q in L3], float)
    X, Y, Z = _rot_head(hm, xs, ys, zs)
    k = np.array([0, 0, 0.3, 0.6, 0.85, 1.0])
    X = X + sw * k
    # the braids hang from the head but lie on her chest: undo most of the head's roll toward the bottom (gravity)
    roll = -math.radians(P.tilt + P.h_tilt) * np.array([0, 0.2, 0.55, 0.85, 1.0, 1.0])
    dX, dY = X - X[0], Y - Y[0]
    X, Y = X[0] + dX * np.cos(roll) - dY * np.sin(roll), Y[0] + dX * np.sin(roll) + dY * np.cos(roll)
    return _cr(list(zip(X, Y)), 40), Z


def _ev_braid_draw(c, a, L, s0, s1, sp, P, det, t, side, cut_head=None):
    """Draw arc-length range [s0, s1] of a braid curve a: the plait (herringbone lobes), the faded red ribbon at the plait's
    end, and below it (pose.e_unravel) the loosened hair."""
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.45); hhi = mix(hc, '#ffffff', 0.3)
    tie = sp['cloth'].get('tie', KEEPING_RED)
    un = clamp(P.e_unravel)
    S = L[-1]
    sp_end = S * (1.0 - 0.5 * un)                    # the plait loosens from the bottom up
    ctx = c.clip(cut_head, diff=True) if cut_head is not None else _noop()
    with ctx:
        # loose part first (under the ribbon)
        if un > 0.02 and s1 > sp_end:
            lo = max(s0, sp_end - 4)
            base = _sub_curve(a, lo, S, 16, L)
            nrm = np.array([[-tg[1], tg[0]] for tg in (_at_len(a, s, L)[1] for s in np.linspace(lo, S, 16))])
            for j in (-1.0, 0.0, 1.0):
                u = np.linspace(0, 1, 16)
                off = (j * (8 + 16 * un) * u + 3.0 * np.sin(u * 7.0 + j * 2 + t * 0.8) * u)[:, None] * nrm
                pts = base + off
                q = _tube([tuple(pts[i]) for i in (0, 3, 6, 9, 12, 15)], [12, 11, 10, 8, 6, 3], 0.9)
                c.fill(q, hc); c.line(q, c.lw * 0.7)
            if det >= 1:
                for j in (-0.5, 0.5):
                    off = (j * (10 + 12 * un) * np.linspace(0, 1, 16))[:, None] * nrm
                    c.line(_pts_path((base + off)[:, 0], (base + off)[:, 1], False, 0.8), c.lw * 0.3, hsh, 160)
        # the plait
        e = min(s1, sp_end)
        if e > s0 + 2:
            seg = _sub_curve(a, s0, e, 14, L)
            ws = [24 - 6 * (s / max(S, 1.0)) for s in np.linspace(s0, e, 14)]
            ws[-1] *= 0.82
            q = _tube([tuple(p) for p in seg[::2]] + [tuple(seg[-1])], ws[::2] + [ws[-1]], 0.9)
            c.fill(q, hc)
            c.fill(_crescent(q, side * 4, -2), hsh, 120)
            if det >= 1:
                n = max(2, int((e - s0) / 15.0))
                lob, hi = [], []
                for i in range(n):
                    s = s0 + (i + 0.5) * (e - s0) / n
                    p, tg = _at_len(a, s, L)
                    nx, ny = -tg[1], tg[0]
                    w = (24 - 6 * s / max(S, 1.0)) * 0.5
                    sd = 1 if i % 2 == 0 else -1
                    p0 = (p[0] + nx * sd * w * 0.95 - tg[0] * 6, p[1] + ny * sd * w * 0.95 - tg[1] * 6)
                    pm = (p[0] + nx * sd * w * 0.35 + tg[0] * 2, p[1] + ny * sd * w * 0.35 + tg[1] * 2)
                    p1 = (p[0] - nx * sd * w * 0.15 + tg[0] * 9, p[1] - ny * sd * w * 0.15 + tg[1] * 9)
                    lob.append(smooth([p0, pm, p1], False))
                    hi.append(smooth([(p[0] + nx * sd * w * 0.55, p[1] + ny * sd * w * 0.55),
                                      (p[0] + nx * sd * w * 0.25 + tg[0] * 5, p[1] + ny * sd * w * 0.25 + tg[1] * 5)], False))
                c.line(_multi(lob), c.lw * 0.5, hsh, 200)
                c.line(_multi(hi), c.lw * 0.45, hhi, 110)
                # flyaways: more as the braid loosens
                fl = []
                for i in range(int(1 + 7 * un)):
                    s = s0 + (e - s0) * hash01(i, 71 + side)
                    p, tg = _at_len(a, s, L)
                    sd = 1 if hash01(i, 72) > 0.5 else -1
                    nx, ny = -tg[1] * sd, tg[0] * sd
                    ln = 8 + 10 * hash01(i, 73)
                    fl.append(smooth([(p[0] + nx * 10, p[1] + ny * 10), (p[0] + nx * (12 + ln * 0.6) + tg[0] * ln * 0.4,
                                       p[1] + ny * (12 + ln * 0.6) + tg[1] * ln * 0.4), (p[0] + nx * (10 + ln) + tg[0] * ln,
                                       p[1] + ny * (10 + ln) + tg[1] * ln)], False))
                if fl: c.line(_multi(fl), c.lw * 0.35, hc, 210)
            c.line(q, c.lw)
        # the ribbon at the plait's end: a neat bow, drooping as the braid loosens, at the end a loose hanging strip
        if s0 <= sp_end <= s1 + 1:
            p, tg = _at_len(a, sp_end, L)
            nx, ny = -tg[1], tg[0]
            tsh = KEEPING_RED_SH if tie == KEEPING_RED else mix(tie, '#000000', 0.3)
            if un < 0.78:
                droop = clamp(un / 0.78)
                for sd in (-1, 1):
                    if droop > 0.55 and sd > 0: continue            # one loop has slipped out
                    ang = sd * (1.0 - 0.75 * droop)
                    lx, ly = nx * ang + tg[0] * (0.25 + 0.6 * droop), ny * ang + tg[1] * (0.25 + 0.6 * droop)
                    ll = 17 * (1.0 - 0.25 * droop)
                    loop = smooth([(p[0], p[1]), (p[0] + lx * ll - tg[0] * 7, p[1] + ly * ll - tg[1] * 7),
                                   (p[0] + lx * ll * 1.15 + tg[0] * 5, p[1] + ly * ll * 1.15 + tg[1] * 5), (p[0] + tg[0] * 3, p[1] + tg[1] * 3)], True, 0.7)
                    c.fill(loop, tie); c.fill(_crescent(loop, 2, 2), tsh, 150); c.line(loop, c.lw * 0.7)
                for sd, ln in ((-1, 22 + 18 * droop), (1, 18 + 10 * droop)):
                    tl = smooth([(p[0], p[1]), (p[0] + nx * sd * 5 + tg[0] * ln * 0.5, p[1] + ny * sd * 5 + tg[1] * ln * 0.5),
                                 (p[0] + nx * sd * 8 + tg[0] * ln, p[1] + ny * sd * 8 + tg[1] * ln)], False)
                    c.line(tl, 6.5, LINE); c.line(tl, 4.6, tie)
                c.shape(oval(p[0], p[1], 5.0, 4.2), mix(tie, '#ffffff', 0.12), c.lw * 0.6)
            else:
                ln = 46.0
                tl = smooth([(p[0] - nx * 6, p[1] - ny * 6), (p[0] + nx * 4 + tg[0] * ln * 0.4, p[1] + ny * 4 + tg[1] * ln * 0.4),
                             (p[0] - nx * 2 + tg[0] * ln, p[1] - ny * 2 + tg[1] * ln)], False)
                c.line(tl, 7.0, LINE); c.line(tl, 5.0, tie)


def _ev_braids(c, hm, sp, P, det, t, behind):
    """Both braids. behind=True (before the neck): every braid's top (behind the ear, beside the neck) plus the lower part
    of a braid that hangs behind the body; behind=False (with the hair): the lower part of each braid that lies on the
    front of the shoulder and chest, clipped behind the jaw."""
    for side in (-1, 1):
        a, Z = _ev_braid_curve(hm, side, P, t)
        L = _arclen(a)
        s_cut = L[-1] * 0.28
        front = float(Z[3]) > 0.0
        if behind:
            _ev_braid_draw(c, a, L, 0.0, s_cut + 6.0 if front else L[-1], sp, P, det, t, side)
        elif front:
            grow = _hairline('braids', 0)[1]
            _ev_braid_draw(c, a, L, s_cut, L[-1], sp, P, det, t, side, cut_head=hm.silhouette(grow=grow + 2.0))


_hair3_back_ev_prev = _hair3_back


def _hair3_back(c, hm, sp, P, det, t):
    if sp.get('hair') != 'braids': return _hair3_back_ev_prev(c, hm, sp, P, det, t)
    _ev_braids(c, hm, sp, P, det, t, behind=True)


_hair_region_ev_prev = _hair_region


def _hair_region(c, hm, sp, P, det, sil, t):
    r = _hair_region_ev_prev(c, hm, sp, P, det, sil, t)
    if sp.get('hair') != 'braids': return r
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.4)
    grow = _hairline('braids', 0)[1]
    if det >= 1:
        L_ = []
        for k in range(1, 6):                       # combed back from the centre parting toward the braids
            for sd in (-1, 1):
                L_.append((sd * np.linspace(0.05 + 0.02 * k, 0.55 + 0.22 * k, 7), np.linspace(-119.0, -86.0 + 13 * k, 7)))
        _strands(c, hm, L_, grow * 0.5, c.lw * 0.32, hsh, 160)
        X, Y, V = _sph(hm, np.zeros(6), np.linspace(-119.0, -82.0, 6), grow * 0.6)
        m = V > 0.05
        if m.sum() > 2:                               # the parting: a thin line of scalp
            c.line(_pts_path(X[m], Y[m], False, 0.8), c.lw * 0.8, mix(sp['skin'], hc, 0.35), 200)
    _ev_braids(c, hm, sp, P, det, t, behind=False)
    return r


# ====================================================================================================== outfit: blouse + pinafore
_DOC_ROWS['pinafore'] = (12, 0.87, 0, 2, 2, 0, 2, 4)
_SLEEVES3['pinafore'] = 'long'
_EV = {'P': None, 'body': None}


def _ev_bodice(c, sp, B, P, det):
    """The navy pinafore over the white blouse (drawn on the body frame, after the torso): sides from the armpits down,
    the bib (a chalky patch pocket) with two straps over the shoulders and two buttons; the back panel with crossed
    straps; then the high round collar."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    rows = _rows3(sp, B)
    torso, L_, R_ = _torso_path(B, rows)
    back = B.ct < -0.15
    ya = B.y_ch - 2
    yb = B.y_sh + 26
    bw = b['ch'] * 0.5
    Xa, Ya, _, _ = B.p3(0, ya, 0)
    with c.clip(torso):
        c.fill(rect(-900, Ya, 1800, 1400), cl['pina'])
        c.grad(rect(-900, Ya, 1800, 1400), L_[3][0] - 10, 0, R_[3][0] + 10, 0,
               [(0, cl['pina_hi'], 70), (0.4, cl['pina'], 0), (0.75, cl['pina_sh'], 80), (1, cl['pina_sh'], 200)])
        if det >= 1: c.texture(torso, 'fabric', 0.06, 0.6)
    straps = []
    if not back:
        bib, v = _surf_poly(B, rows, [(-bw, yb), (bw, yb), (bw * 1.06, ya + 6), (-bw * 1.06, ya + 6)], dz=2)
        if v > -0.2:
            q = smooth(bib, True, 0.15); c.fill(q, cl['pina']); c.fill(_crescent(q, 0, 5), cl['pina_sh'], 90); c.line(q, lw * 0.7)
            pk, v2 = _surf_poly(B, rows, [(-bw * 0.42, yb + 26), (bw * 0.42, yb + 26), (bw * 0.4, yb + 62), (-bw * 0.4, yb + 62)], dz=3)
            if v2 > 0.1 and det >= 1:
                qk = smooth(pk, True, 0.25); c.line(qk, lw * 0.45, cl['pina_sh'], 230)
                X, Y, vv, s_ = B.surf(bw * 0.12, yb + 30, 4, False, rows)
                c.glow(X, Y, 14 * s_, 6 * s_, CHALK, 60 + 90 * clamp(P.e_dust))     # chalk dust on the pocket lip
        for sd in (-1, 1):
            st_, v = _surf_poly(B, rows, [(sd * bw * 0.58, yb + 3), (sd * (bw * 0.58 + 15), yb + 3),
                                          (sd * (b['sh'] * 0.6 + 9), B.y_sh - 14), (sd * (b['sh'] * 0.6 - 7), B.y_sh - 15)], dz=3)
            if v > -0.1: straps.append((sd, st_))
    else:
        for sd in (-1, 1):                              # crossed straps on the back
            st_, v = _surf_poly(B, rows, [(sd * (b['sh'] * 0.6 - 7), B.y_sh - 15), (sd * (b['sh'] * 0.6 + 9), B.y_sh - 14),
                                          (-sd * bw * 0.55, ya + 6), (-sd * (bw * 0.55 + 15), ya + 6)], back=True, dz=3)
            if v > -0.1: straps.append((sd, st_))
    for sd, st_ in straps:
        q = smooth(st_, True, 0.1); c.fill(q, cl['pina']); c.fill(_crescent(q, -sd * 2, 0), cl['pina_sh'], 110); c.line(q, lw * 0.6)
        if not back:
            X, Y, vv, s_ = B.surf(sd * (bw * 0.58 + 7.5), yb + 10, 4, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 4.2 * s_), cl['button'], lw * 0.4)
    # the high round collar (a band hugging the neck)
    nw = b['neck']
    co, v = _surf_poly(B, rows, [(-nw - 8, B.y_sh - 42), (nw + 8, B.y_sh - 42), (nw + 12, B.y_sh - 22), (0, B.y_sh - 15),
                                 (-nw - 12, B.y_sh - 22)], back=back, dz=5)
    if v > -0.4:
        q = smooth(co, True, 0.6); c.fill(q, cl['collar']); c.fill(_crescent(q, 0, -3), cl['collar_sh'], 130); c.line(q, lw * 0.6)


_skirts3_ev_prev = _skirts3


def _skirts3(c, sp, B, P, det, t, rows):
    """The pinafore's skirt: ankle length; seated (the swing) it drapes over both thighs and hangs below the knees."""
    if sp.get('outfit') != 'pinafore': return _skirts3_ev_prev(c, sp, B, P, det, t, rows)
    cl = sp['cloth']; b = sp['body']
    st = clamp(B.sit + 0.8 * B.kneel + getattr(B, 'floor', 0.0))
    if st > 0.25:
        pts = []
        for side in (-1, 1):
            X, Y, s_, _ = B.p3(side * b['wa'] * 1.04, B.y_wa + 8, 0)
            pts.append((X, Y))
            H, K, A, pitch = _leg_chain(sp, B, P, side)
            lw_ = b['leg'][0] * 0.95
            for dx, dy in ((side * lw_, 0.0), (side * lw_, -lw_ * 0.6), (side * lw_ * 1.15, 150.0), (-side * lw_ * 0.7, 150.0)):
                Q = K + np.array([dx, dy, 0.0])
                X, Y, _, _ = B.p3(Q[0], Q[1] - B.bob, Q[2], upper=False)
                pts.append((X, Y))
            X, Y, _, _ = B.p3(H[0] + side * lw_, H[1] - B.bob, H[2], upper=False)
            pts.append((X, Y))
        sk = smooth(_hull(pts), True, 0.5)
        c.fill(sk, cl['pina']); _cloth_shade(c, sk, cl['pina_sh'], 150, 1.0, 20); c.line(sk, c.lw)
        return
    hem = -74.0
    p = _skirt(c, sp, B, det, B.y_wa + 6, hem, b['wa'] * 1.04, b['hip'] * 1.36, cl['pina'], cl['pina_sh'], t=t, P=P)
    if det >= 1 and P.e_dust > 0.05 and p is not None:      # chalk dust caught on the hem
        X1, Y1, s1, _ = B.p3(0, hem, 0, upper=False)
        hw = b['hip'] * 1.3 * s1
        with c.clip(p):
            for k in range(7):
                u = (k + 0.5) / 7.0
                c.glow(X1 - hw + 2 * hw * u + 6 * hash01(k, 91), Y1 - 8 - 10 * hash01(k, 92), 16 * s1, 7 * s1, CHALK,
                       30 + 70 * clamp(P.e_dust) * hash01(k, 93))


_limb_cols3_ev_prev = _limb_cols3


def _limb_cols3(sp):
    if sp.get('outfit') == 'pinafore':
        cl = sp['cloth']
        return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    return _limb_cols3_ev_prev(sp)


# ====================================================================================================== neck: the stretch
_neck3_ev_prev = _neck3


def _neck3(c, sp, B, skin, skin_sh):
    r = _neck3_ev_prev(c, sp, B, skin, skin_sh)
    if not sp.get('evie'): return r
    P = _EV['P']
    _EV['body'] = (c, B)
    if P is None or P.e_neck < 2.0: return r
    # the stretched neck: a smooth rubbery tube from the collar to the head (no joints, no crack), a little thinner in the
    # middle, swaying gently; drawn behind the torso and the head
    hx, hy, hrot, hs = _head_xf(sp, B, P)
    ra = math.radians(hrot)
    top = (hx - math.sin(ra) * 96 * hs, hy + math.cos(ra) * 96 * hs)
    nb = B.p3(0, B.y_sh - 30, 0)
    base = (nb[0], nb[1])
    dx, dy = top[0] - base[0], top[1] - base[1]
    Ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / Ln, dy / Ln; px, py = -uy, ux
    nw = sp['body']['neck'] * nb[2]
    wob = min(Ln, 900.0) * 0.05
    t = P.t
    ctrl = [base]
    for k, f in enumerate((0.22, 0.45, 0.7, 0.9)):
        o = wob * math.sin(t * 1.4 + k * 1.9) * math.sin(PI * f)
        ctrl.append((base[0] + dx * f + px * o, base[1] + dy * f + py * o))
    ctrl.append(top)
    k_ = clamp(P.e_neck / 600.0)
    ws = [nw * 2.0, nw * (2.0 - 0.35 * k_), nw * (2.0 - 0.5 * k_), nw * (2.0 - 0.4 * k_), nw * 1.9, nw * 1.85]
    tube = _tube(ctrl, ws, 0.9)
    c.fill(tube, skin)
    a_ = _cr(ctrl, 24)
    off = np.array([px, py]) * nw * 0.55
    c.line(_pts_path(a_[:, 0] + off[0], a_[:, 1] + off[1], False, 0.8), nw * 0.5, skin_sh, 110)
    c.line(_pts_path(a_[:, 0] - off[0] * 0.8, a_[:, 1] - off[1] * 0.8, False, 0.8), nw * 0.18, mix(skin, '#ffffff', 0.5), 120)
    c.line(tube, c.lw)
    return r


# ====================================================================================================== mouth: the chalk smile
def _ev_chalk_smile(c, hm, sp, P, det, t, skin=None):
    """The smile from rule 2 on: a smooth white chalk line drawn over her mouth (the real mouth is gone), wider each
    night: e_chalk 0.25 just past the corners, 0.42 mid-cheek, 0.58 wider, 0.8 almost at her ears, 1.0 ear to ear, ends
    curling up a little. Never a cut: no red, no teeth. Talking (m_open) parts the line in the middle like a drawn mouth."""
    w = clamp(P.e_chalk)
    my = sp['mouth_y']
    # (the width stays on the front of the face, so the ends curl UP the cheeks toward the ears instead of wrapping round
    # the jaw like an outline)
    phm = float(np.interp(w, [0, 0.25, 0.42, 0.58, 0.8, 1.0], [0.14, 0.27, 0.40, 0.52, 0.66, 0.78]))
    rise = float(np.interp(w, [0, 0.25, 0.42, 0.58, 0.8, 1.0], [2, 6, 12, 18, 27, 36]))
    sag = 6.0 + 4.0 * w
    q = np.linspace(-1.0, 1.0, 41)
    ys = my + sag * (1 - q * q) - rise * q ** 4
    ph = q * phm
    curl = np.array([1.05, 1.1])
    ph = np.concatenate([-curl[::-1] * phm, ph, curl * phm])
    yc_ = my - rise - np.array([5.0, 12.0]) * (0.6 + 0.6 * w)
    ys = np.concatenate([yc_[::-1], ys, yc_])
    X, Y, V = _sph(hm, ph, ys, 1.2)
    m = V > -0.02
    if m.sum() < 3: return
    # Owner, 27 Nov (second note): like Mister Winks's painted grin and Grandpa's too-still smile, not a drawing on top:
    # her own lips stretched far too wide and tight, thin and pale, closed, the corners pulled up into the cheeks with
    # creases hooking up from them; wider every night and dead still. Talking parts the lips on a strip of teeth.
    skin = skin or sp.get('skin', '#f3d2bd')
    lipc = mix('#9a3f48', skin, 0.32)
    line_c = mix('#3a2226', skin, 0.12)
    crease_c = mix(sp.get('skin_dp', '#88645c'), '#3a2226', 0.25)
    o = clamp(P.m_open) * 0.75 + 0.25 * clamp(P.m_wide) * clamp(P.m_open)
    qq = np.concatenate([np.full(2, -1.1), q, np.full(2, 1.1)])
    env = np.clip(1.0 - qq ** 2, 0, None) ** 0.6          # the lips thin out toward the stretched corners
    tu = (4.4 - 1.0 * w) * hm.cp                            # stretched tight: thinner the wider it gets
    tl = (6.4 - 1.2 * w) * hm.cp
    Yl = Y + 16.0 * o * env * hm.cp
    mm = np.where(m)[0]
    if len(mm) < 3: return
    Xm = X[mm]
    def band(top, bot):
        return _pts_path(np.concatenate([Xm, Xm[::-1]]), np.concatenate([top[mm], bot[mm][::-1]]), True, 0.8)
    if o > 0.03:
        c.fill(band(Y, Yl), '#24161a', 240)
        c.fill(band(Y, Y + 0.42 * (Yl - Y)), '#efe9e0', 225)  # a strip of teeth, like the dummy's when his jaw dropped
    c.fill(band(Y - tu * env, Y), lipc, 200)
    c.fill(band(Yl, Yl + tl * env), lipc, 215)
    c.line(_pts_path(Xm, (Yl + 0.45 * tl * env)[mm], False, 0.8), 0.9, mix(lipc, '#ffffff', 0.4), 90)
    c.line(_pts_path(Xm, Y[mm], False, 0.8), 2.0 + 0.8 * w, line_c, 240)
    if o > 0.03: c.line(_pts_path(Xm, Yl[mm], False, 0.8), 1.2, line_c, 200)
    # creases hooking up from the corners (Winks's painted creases), deeper each night, and a dimple shadow
    k = (1.2 + 1.3 * w) * hm.cp
    mid = X[len(X) // 2]
    for e_ in (mm[0], mm[-1]):
        xc, yc = X[e_], Y[e_]
        sx = 1.0 if xc > mid else -1.0
        cr = _pts_path(np.array([xc + sx * 1.0 * k, xc + sx * 4.5 * k, xc + sx * 6.0 * k, xc + sx * 4.8 * k]),
                       np.array([yc + 1.5 * k, yc - 2.0 * k, yc - 8.0 * k, yc - 13.0 * k]), False, 0.8)
        c.line(cr, 1.8 + 0.8 * w, crease_c, 150 + 90 * w)
        c.fill(_pts_path(np.array([xc - 1.6 * k, xc + 1.6 * k, xc + 1.6 * k, xc - 1.6 * k]) + sx * 1.2 * k,
                         np.array([yc - 1.2 * k, yc - 1.2 * k, yc + 1.6 * k, yc + 1.6 * k]), True, 0.8), crease_c, 70 * w)


_mouth_ev_prev = _mouth


def _mouth(c, hm, sp, P, det, t, skin, sh):
    if sp.get('evie') and getattr(P, 'e_chalk', 0.0) > 0.01:
        return _ev_chalk_smile(c, hm, sp, P, det, t, skin)
    return _mouth_ev_prev(c, hm, sp, P, det, t, skin, sh)


# ====================================================================================================== head prelude
_dhl_ev_prev = draw_head_local


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    sp = sp or CAST[who]
    if sp.get('evie') and _EV['body'] is not None:
        bc, B = _EV['body']; _EV['body'] = None
        _ev_bodice(bc, sp, B, P, det)                  # the pinafore and collar go on after the torso, before the head
    return _dhl_ev_prev(c, who, P, yaw, pitch, det, t, light, sp)


# ====================================================================================================== hands: chalk dust
_draw_arm3_ev_prev = _draw_arm3


def _draw_arm3(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    r = _draw_arm3_ev_prev(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light)
    if not sp.get('evie') or det < 1 or P.e_lie > 0.5: return r
    S, E, Wr = _arm_data(sp, B, P, side)
    e2 = B.p3(*E); w2 = B.p3(*Wr)
    dx, dy = w2[0] - e2[0], w2[1] - e2[1]
    d = math.hypot(dx, dy) or 1.0
    hl = 74.0 * sp['body']['hand'] * w2[2]
    tx, ty = w2[0] + dx / d * hl, w2[1] + dy / d * hl
    du = 0.35 + 0.65 * clamp(P.e_dust)
    s_ = w2[2]
    c.glow(tx, ty, 15 * s_, 11 * s_, CHALK, 95 * du)
    dots = []
    for k in range(6):
        a_ = 2 * PI * hash01(k, 41 + side)
        rr = (5 + 9 * hash01(k, 42)) * s_
        dots.append(oval(tx + math.cos(a_) * rr, ty + math.sin(a_) * rr, 1.6 * s_, 1.6 * s_))
    c.fill(_multi(dots), CHALK, 170 * du)
    mot = []                                             # a little dust always drifting down from her fingers
    for k in range(int(2 + 3 * du)):
        ph = (t * (0.32 + 0.1 * hash01(k, 44)) + hash01(k, 45)) % 1.0
        mot.append(oval(tx + (hash01(k, 46) - 0.5) * 18 * s_ + 6 * s_ * math.sin(t * 2 + k), ty + ph * 150 * s_, 1.8 * s_, 1.8 * s_))
        if ph > 0.85: mot.pop()
    if mot: c.fill(_multi(mot), CHALK, 120 * du)
    return r


# ====================================================================================================== props
def _p_chalk_stub(c, det, t, P=None):
    """Her worn chalk stub (4.5 cm, a little crooked in the fingers): white, one end worn round and grey with use."""
    k = c.sub(0, 0, 22.0)
    body = rrect(-0.6, -2.6, 1.2, 4.8, 0.55)
    k.fill(body, CHALK)
    k.fill(rrect(-0.6, 1.2, 1.2, 1.0, 0.5), CHALK_SH, 170)
    if det >= 1: k.line(poly([(-0.25, -2.2), (-0.25, 1.0)], False), k.lw * 0.5, '#ffffff', 200)
    k.line(body, k.lw)


def _p_evie_phone(c, det, t, P=None, screen=False):
    """Her phone, held upright: back view (pale case, the screen's glow round the edge) or screen=True (lit thread)."""
    body = rrect(-3.6, -7.4, 7.2, 14.8, 1.2)
    if screen:
        c.fill(body, '#20232c'); c.fill(rrect(-3.0, -6.6, 6.0, 13.0, 0.6), '#dfe9ff')
        for k_, (x0, w_) in enumerate(((-2.4, 3.4), (-0.6, 3.0), (-2.4, 4.0), (-0.2, 2.6))):
            c.fill(rrect(x0, -5.6 + k_ * 2.8, w_, 1.7, 0.8), '#ffffff' if k_ % 2 == 0 else '#9cc0ff')
    else:
        c.glow(0, 0, 7.5, 10.5, '#d8e6ff', 120)
        c.fill(body, '#e6e2ea'); c.fill(oval(-1.8, -5.6, 0.9, 0.9), '#3a3a44')
    c.line(body, c.lw)


def _p_evie_bracelet(c, det, t, P=None):
    """The woven bracelet, green and gold, chalk dust on it (it hangs from her fingers)."""
    ring = oval(0, 3.4, 3.2, 3.6)
    c.line(ring, 1.5, LINE); c.line(ring, 1.1, '#3f8a4a')
    if det >= 1:
        d = []
        for k in range(14):
            a_ = 2 * PI * k / 14
            x, y = 3.2 * math.cos(a_), 3.4 + 3.6 * math.sin(a_)
            d.append(poly([(x - 0.35, y - 0.35), (x + 0.35, y + 0.35)], False))
        c.line(_multi(d), 0.35, '#e0b84a', 255)
        c.glow(1.5, 5.8, 2.2, 1.2, CHALK, 140)


PROPS3.update({
    'chalk_stub': (_p_chalk_stub, 'upright', (0.0, 0.0)),
    'evie_phone': (_p_evie_phone, 'upright', (0.0, 0.0)),
    'evie_phone_screen': (lambda c, d, t, P=None: _p_evie_phone(c, d, t, P, True), 'upright', (0.0, 0.0)),
    'evie_bracelet': (_p_evie_bracelet, 'hang', (0.0, 0.0)),
})


def draw_chalk_stub(pen, x, y, px_per_cm, angle=0.0, detail=2, alpha=1.0):
    """The chalk stub lying on a surface (x, y = its centre), angle in degrees."""
    c = Ctx(pen, skia.Matrix(), _lw_for(px_per_cm * 22.0)).sub(x, y, angle - 22.0 + 90.0, px_per_cm)
    _p_chalk_stub(c, detail, 0.0)


# ====================================================================================================== chalk-flat colour
def _ev_matrix(f, w=0.0):
    """Colour matrix toward flat chalk at night: every colour goes to a flat grey-blue of its own lightness (skin a mid
    grey-blue, about 0.70 at most, so her white chalk smile and dark lines still read on it). w (the drain) takes it on
    to the pale chalk-white of the drain."""
    lw_ = (0.2126, 0.7152, 0.0722)
    k_, b_ = 0.80 - 0.40 * w, 0.06 + 0.50 * w
    m = []
    for i, ti in enumerate((0.90 + 0.085 * w, 0.96 + 0.03 * w, 1.06 - 0.06 * w)):
        row = [0.0] * 5
        for j, lj in enumerate(lw_):
            row[j] = (1.0 - f) * (1.0 if i == j else 0.0) + f * k_ * ti * lj
        row[4] = f * b_ * ti
        m += row
    return m + [0, 0, 0, 1, 0]


def _ev_layer(pen, f, a=1.0, bounds=None, w=0.0):
    if f < 0.005 and a > 0.995: return False
    paint = skia.Paint(Alphaf=clamp(a))
    if f >= 0.005: paint.setColorFilter(skia.ColorFilters.Matrix(_ev_matrix(clamp(f), clamp(w))))
    pen.cv.saveLayer(bounds, paint)
    return True


def _ev_flat(P):
    return clamp(P.e_flatn * clamp(P.e_night) + P.e_flat + ease_in_out(clamp(P.e_drain / 0.4)))


def _ev_prep(P, light):
    """Pose and light adjustments every Evie draw makes: the neck stretch, the chalk stub kept in her right hand, the
    phone glow under her chin."""
    P = P.copy()
    if P.e_neck > 0:
        P.h_dy -= P.e_neck; P.h_dx += P.e_neck_dx
    if P.e_stub > 0.5 and P.hr_prop is None and P.hr_shape in ('mitt', 'relaxed', 'grip', 'fist', None):
        P.hr_prop = 'chalk_stub'; P.hr_shape = 'grip'
    if P.e_glow > 0.01:
        light = dict(light or {})
        light['under'] = '#d4e2ff'; light['under_a'] = max(light.get('under_a', 0) if light.get('under') else 0, 120 * clamp(P.e_glow))
    return P, light


_draw_ev_prev = draw


def draw(pen, who, *a, **k):
    """draw() with Evie's looks: chalk-flat colour, lying flat as a chalk drawing (e_lie), the slide smear, the neck
    stretch, the phone glow, and the drain (colour to chalk-white, then blown away as dust)."""
    sp = CAST.get(who, {})
    if not sp.get('evie'): return _draw_ev_prev(pen, who, *a, **k)
    names = ('x', 'y_feet', 'height', 'pose', 'detail', 'light', 't', 'aim')
    kw = dict(zip(names, a)); kw.update(k)
    P0 = _as_pose(kw.get('pose'))
    t = P0.t if kw.get('t') is None else kw['t']
    P, light = _ev_prep(P0, kw.get('light'))
    x, y = kw['x'], kw['y_feet']
    h = kw['height'] * P.e_scale
    fx, fy = x + P.dx, y + P.dy                           # her feet
    lie = P.e_lie
    if P.e_trail > 0.01:                                  # the slide's chalk smear on the ground
        _ev_smear(pen, x + P.e_tx, y + P.e_ty, fx, fy, h, P.e_trail * clamp(1.0 - 0.6 * (1.0 - abs(lie))), t)
    cv = pen.cv
    tr = abs(lie) > 1e-3
    if tr:
        kf = 1.0 + (P.e_flatk - 1.0) * lie
        cv.save(); cv.translate(fx, fy); cv.scale(1.0, max(kf, 0.02))
        if P.e_lie_dir: cv.rotate(P.e_lie_dir * clamp(lie))
        cv.translate(-fx, -fy)
    try:
        dr_a = _smoothstep(0.3, 0.75, lie)
        if dr_a > 0.01:
            draw_chalk_girl(pen, fx, fy, h, alpha=dr_a, smile=max(0.75, P.e_chalk), t=t, unravel=P.e_unravel)
        fig_a = 1.0 - _smoothstep(0.55, 0.9, lie)
        if fig_a <= 0.01: return None
        f = _ev_flat(P)

        nk = max(0.0, P.e_neck) * h / 1000.0
        bnd = skia.Rect.MakeLTRB(fx - 0.95 * h - abs(P.e_neck_dx) * h / 1000.0, fy - 1.3 * h - 1.2 * nk, fx + 0.95 * h + abs(P.e_neck_dx) * h / 1000.0, fy + 0.12 * h)

        def fig(pn):
            lay = _ev_layer(pn, f, fig_a, bnd, ease_in_out(clamp(P.e_drain / 0.4)))
            _EV['P'] = P
            try:
                return _draw_ev_prev(pn, who, x, y, h, P, kw.get('detail'), light, t, kw.get('aim'))
            finally:
                _EV['P'] = None; _EV['body'] = None
                if lay: pn.cv.restore()
        u = clamp((P.e_drain - 0.4) / 0.6)
        if u > 0.0:
            return _ev_dust_dissolve(pen, fig, fx, fy, h, u, t, wind=P.e_wind)
        return fig(pen)
    finally:
        if tr: cv.restore()


_draw_bust_ev_prev = draw_bust


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    sp = CAST.get(who, {})
    if not sp.get('evie'): return _draw_bust_ev_prev(pen, who, cx, cy, scale, pose, detail, light, t)
    P, light = _ev_prep(_as_pose(pose), light)
    lay = _ev_layer(pen, _ev_flat(P), 1.0, w=ease_in_out(clamp(P.e_drain / 0.4)))
    _EV['P'] = P
    try:
        return _draw_bust_ev_prev(pen, who, cx, cy, scale, P, detail, light, t)
    finally:
        _EV['P'] = None; _EV['body'] = None
        if lay: pen.cv.restore()


def _ev_smear(pen, x0, y0, x1, y1, h, a, t):
    """The faint chalk smear a flat Evie leaves as she slides (a few dusty streaks, widest where she lies now)."""
    if math.hypot(x1 - x0, y1 - y0) < 2: return
    cv = pen.cv
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
    for k in range(5):
        o = (k - 2) * h * 0.035
        q = smooth([(x0 + nx * o * 0.4, y0 + ny * o * 0.4), (x0 + dx * 0.55 + nx * o * 0.8, y0 + dy * 0.55 + ny * o * 0.8),
                    (x1 + nx * o, y1 + ny * o)], False)
        cv.drawPath(q, _chalk_paint(CHALK, 34 * a * (1.0 - abs(k - 2) * 0.2), h * (0.03 + 0.012 * hash01(k, 3)),
                                    dash=(h * 0.08, h * 0.03 + h * 0.02 * hash01(k, 4)), blur=h * 0.01))


# ====================================================================================================== drain: blown away as dust
_DUST_NOISE = {}


def _ev_noise(w, h, seed):
    key = (w, h, seed)
    if key not in _DUST_NOISE:
        import cv2
        rng = np.random.default_rng(seed)
        a = cv2.resize(rng.random((14, 8)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        b = cv2.resize(rng.random((70, 40)).astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        if len(_DUST_NOISE) > 8: _DUST_NOISE.clear()
        _DUST_NOISE[key] = np.clip(0.75 * a + 0.25 * b, 0, 1)
    return _DUST_NOISE[key]


def _ev_dust_dissolve(pen, fig, fx, fy, h, u, t, wind=1.0, seed=11):
    """The drain's second half: the figure (already flat chalk-white) comes apart into dust from the downwind edge and
    the top first, and the wind lifts the dust up and away. She never falls or crumbles: what is left stays upright.
    Renders the figure off-screen at device resolution, masks it, adds the drifting dust, and composites it back."""
    cv = pen.cv
    M = cv.getTotalMatrix()
    bb = M.mapRect(skia.Rect.MakeLTRB(fx - 0.6 * h, fy - 1.12 * h, fx + 0.6 * h, fy + 0.05 * h))
    sz = cv.getBaseLayerSize()
    W0, H0 = sz.width(), sz.height()
    wd = 1.0 if wind >= 0 else -1.0
    L = max(0.0, bb.left() - (0.15 if wd > 0 else 1.1) * bb.width()); R = min(W0, bb.right() + (1.1 if wd > 0 else 0.15) * bb.width())
    T = max(0.0, bb.top() - 0.7 * bb.height()); Bm = min(H0, bb.bottom() + 2)
    W, H = int(R - L) + 1, int(Bm - T) + 1
    if W < 4 or H < 4: return None
    surf = skia.Surface(W, H)
    c2 = surf.getCanvas(); c2.translate(-L, -T); c2.concat(M)
    fig(Pen(c2, pen.lw))
    img = surf.makeImageSnapshot()
    arr = img.toarray()
    alpha0 = arr[:, :, 3].astype(np.float32) / 255.0
    # figure-normalised coordinates
    bw, bh = max(bb.width(), 1.0), max(bb.height(), 1.0)
    cols = np.where(alpha0.max(axis=0) > 0.1)[0]; rows_ = np.where(alpha0.max(axis=1) > 0.1)[0]
    if len(cols) < 2 or len(rows_) < 2: return None
    xs = (np.arange(W, dtype=np.float32) - cols[0]) / max(1.0, cols[-1] - cols[0])     # the figure's own extent
    ys = (np.arange(H, dtype=np.float32) - rows_[0]) / max(1.0, rows_[-1] - rows_[0])
    xd = xs if wd > 0 else 1.0 - xs                       # 0 upwind .. 1 downwind
    nz = _ev_noise(W, H, seed)
    field = 0.45 * (1.0 - np.clip(xd, 0, 1))[None, :] + 0.27 * np.clip(ys, 0, 1)[:, None] + 0.28 * nz
    th = u * 1.08 - 0.04
    mask = np.clip((field - th) / 0.05, 0.0, 1.0)
    out = (arr.astype(np.float32) * mask[:, :, None]).astype(np.uint8)
    img2 = skia.Image.fromarray(np.ascontiguousarray(out), colorType=img.colorType(), alphaType=img.alphaType())
    surf2 = skia.Surface(W, H); c3 = surf2.getCanvas()
    c3.drawImage(img2, 0, 0)
    # dust: fixed particles on the figure, each released when the front passes it, then carried up and downwind
    rng = np.random.default_rng(seed + 5)
    n = 2600
    px = rng.random(n); py = rng.random(n) * 1.12 - 0.02
    ix = np.clip(((px * bw + bb.left() - L)).astype(int), 0, W - 1); iy = np.clip(((py * bh + bb.top() - T)).astype(int), 0, H - 1)
    on = alpha0[iy, ix] > 0.3
    fv = field[iy, ix]
    age = (th - fv) / 1.08
    sel = on & (age > 0) & (age < 0.55)
    if sel.any():
        ag = age[sel]; k = np.arange(n)[sel]
        dist = ag * 2.2 * bh
        sx = ix[sel] + wd * dist * (0.85 + 0.3 * rng.random(n)[sel]) + np.sin(ag * 9.0 + k) * 0.04 * bh
        sy = iy[sel] - dist * (0.35 + 0.25 * rng.random(n)[sel]) - ag * ag * 0.6 * bh + np.cos(ag * 7.0 + k * 1.3) * 0.03 * bh
        a_ = np.clip(1.0 - ag / 0.55, 0, 1) * (0.55 + 0.45 * rng.random(n)[sel])
        r_ = (0.0016 + 0.0028 * rng.random(n)[sel]) * bh * (1.0 - 0.5 * ag)
        pt = skia.Paint(AntiAlias=True)
        for x_, y_, aa, rr in zip(sx, sy, a_, r_):
            pt.setColor(col(CHALK, int(230 * aa)))
            c3.drawCircle(float(x_), float(y_), float(max(rr, 0.6)), pt)
    cv.save(); cv.resetMatrix()
    cv.drawImage(surf2.makeImageSnapshot(), L, T)
    cv.restore()
    return None


# ====================================================================================================== the chalk girl drawing
def _chalk_girl_paths(smile=1.0, unravel=0.0):
    """Line paths of the chalk girl (a child's sidewalk drawing of Evie) in units: feet at y 0, 1000 tall, centred on x 0.
    Two braids with little bows, a pinafore, stick arms with mitten hands (a chalk stub in one), stick legs, dot eyes,
    freckles, and a smile that doesn't stop: it runs on past the face's outline and curls up."""
    L_, F_ = [], []
    L_.append(oval(0, -800, 118, 126))
    for sd in (-1, 1):
        br = [(sd * 100, -778), (sd * 136, -706), (sd * 152, -630), (sd * (158 + 30 * unravel), -566 + 30 * unravel)]
        L_.append(smooth(br, False))
        for k in range(4):
            u = 0.15 + 0.2 * k
            i = min(int(u * 3), 2); s = u * 3 - i
            x_ = br[i][0] + (br[i + 1][0] - br[i][0]) * s; y_ = br[i][1] + (br[i + 1][1] - br[i][1]) * s
            L_.append(poly([(x_ - 9, y_ - 4), (x_ + 9, y_ + 4)], False))
        bx, by = br[-1]
        for lp in (-1, 1):
            L_.append(smooth([(bx, by), (bx + lp * 30, by - 18), (bx + lp * 30, by + 14)], True, 0.7))
        L_.append(poly([(bx, by), (bx - 10, by + 40)], False)); L_.append(poly([(bx, by), (bx + 12, by + 36)], False))
    L_.append(poly([(0, -674), (0, -640)], False))
    L_.append(smooth([(-72, -642), (72, -642), (200, -170), (-200, -170)], True, 0.18))
    L_.append(poly([(-44, -642), (-46, -540), (46, -540), (44, -642)], False))
    for sd in (-1, 1):
        L_.append(smooth([(sd * 70, -630), (sd * 130, -545), (sd * 172, -440)], False))
        L_.append(oval(sd * 180, -420, 22, 22))
        for f in (-1, 0, 1):
            L_.append(poly([(sd * 180 + f * 11, -400), (sd * 182 + f * 14, -378)], False))
        L_.append(poly([(sd * 58, -170), (sd * 60, -52)], False))
        L_.append(oval(sd * 74, -38, 36, 17))
        F_.append(oval(sd * 44, -815, 13, 15))
        for k in range(4):
            F_.append(oval(sd * (34 + 12 * k), -772 - 7 * (k % 2), 3.6, 3.6))
    L_.append(rect(196, -470, 14, 34))                       # the chalk stub in her right hand (screen right)
    L_.append(smooth([(-8, -768), (0, -758), (8, -768)], False))
    w = 70.0 + 140.0 * clamp(smile)
    rise = 18 + 40 * clamp(smile)
    L_.append(smooth([(-w - 14, -772 - rise - 22), (-w, -760 - rise), (-w * 0.5, -726), (0, -716), (w * 0.5, -726), (w, -760 - rise),
                      (w + 14, -772 - rise - 22)], False))
    return L_, F_


def draw_chalk_girl(pen, x, y_feet, height, alpha=1.0, smile=1.0, t=0.0, unravel=0.0, flat_k=1.0, angle=0.0, lw=None,
                    colr=CHALK):
    """The chalk girl: (x, y_feet) her feet, height her drawn size. flat_k < 1 lays the drawing on the ground (the ground's
    foreshortening at that spot; the setup's drawing in the Keeping Square), angle (deg) turns it on the ground. Evie's
    draw() uses it when she lies flat (e_lie) and when she stands up out of the ground."""
    if alpha <= 0.004: return
    cv = pen.cv
    cv.save(); cv.translate(x, y_feet)
    if flat_k < 0.999: cv.scale(1.0, flat_k)
    if angle: cv.rotate(angle)
    s = height / 1000.0
    cv.scale(s, s)
    w = (lw or max(2.2, height * 0.012)) / s
    L_, F_ = _chalk_girl_paths(smile, unravel)
    for k, p in enumerate(L_):
        _chalk_stroke(cv, p, w, alpha, colr, k)
    pt = skia.Paint(Color=col(colr, int(215 * alpha)), AntiAlias=True)
    for p in F_: cv.drawPath(p, pt)
    cv.restore()


def draw_sneaker_print(pen, x, y, px_per_cm, angle=0.0, alpha=1.0, squash=0.45, side=1):
    """One white chalk sneaker print on the ground (x, y = the print's centre, angle = the way the toe points, deg,
    0 = up the screen = away from the camera; squash = the ground's foreshortening). The prints point where she went."""
    cv = pen.cv
    cv.save(); cv.translate(x, y); cv.scale(1.0, squash); cv.rotate(angle); cv.scale(px_per_cm, px_per_cm)
    sole = smooth([(-3.2 * side, 10.5), (3.0 * side, 10.0), (3.8 * side, 2.0), (4.2 * side, -6.0), (2.4 * side, -10.8),
                   (-1.8 * side, -11.0), (-4.0 * side, -6.0), (-3.4 * side, 2.0)], True, 0.8)
    cv.drawPath(sole, _chalk_paint(CHALK, 150 * alpha, 0.55))
    cv.drawPath(sole, skia.Paint(Color=col(CHALK, int(60 * alpha)), AntiAlias=True))
    tread = []
    for k in range(7):
        yy = -9.0 + k * 2.6
        tread.append(poly([(-2.6, yy), (0.0, yy + 1.1), (2.6, yy)], False))
    p = skia.Path()
    for q in tread: p.addPath(q)
    cv.drawPath(p, _chalk_paint(CHALK, 170 * alpha, 0.5))
    cv.drawPath(oval(0.2 * side, 7.4, 2.4, 1.9), _chalk_paint(CHALK, 150 * alpha, 0.45))
    cv.restore()


def draw_slot_smile(pen, slot, t=0.0, amount=1.0, hum=0.0, alpha=1.0):
    """What shows in the letterbox slot (x, y, w, h = the opening, design px): only her chalk smile, ear to ear, its ends
    curling up; humming makes the line shiver. Clipped to the opening (draw the slot's dark first)."""
    x0, y0, w, h = slot
    cv = pen.cv
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h), skia.ClipOp.kIntersect, True)
    cx, cy = x0 + w / 2, y0 + h * 0.42
    hw = w * (0.18 + 0.30 * clamp(amount))
    pts = []
    for k in range(25):
        q = k / 24.0 * 2 - 1
        yy = cy + h * 0.22 * (1 - q * q) - h * 0.28 * q ** 4 + hum * h * 0.03 * math.sin(t * 42.0 + q * 9.0)
        pts.append((cx + q * hw, yy))
    pts = [(cx - hw * 1.06, cy - h * 0.42)] + pts + [(cx + hw * 1.06, cy - h * 0.42)]
    _chalk_stroke(cv, smooth(pts, False), max(1.5, h * 0.11), alpha, CHALK, 1)
    cv.restore()


def draw_swing(pen, pivot, length, angle=0.0, px_per_cm=10.0, sep=0.35, seat_w_cm=46.0, part='all'):
    """A playground swing: two chains from the bar at pivot (x, y) to a rubber seat, swung by angle (deg, side view:
    + = toward screen right). sep = how far apart the chains read (0 side view .. 1 front view). part 'back' / 'front'
    draw the far / near chain only (seat with 'back'), so a rider sits between them."""
    a = math.radians(angle)
    sx, sy = pivot[0] + math.sin(a) * length, pivot[1] + math.cos(a) * length
    hw = seat_w_cm * 0.5 * px_per_cm * sep + 6.0 * px_per_cm * (1 - sep)
    lw = max(1.5, 0.9 * px_per_cm)
    chains = {'back': [(-1, 0.96)], 'front': [(1, 1.0)], 'all': [(-1, 0.96), (1, 1.0)]}[part]
    for sd, k in chains:
        p0 = (pivot[0] + sd * hw, pivot[1]); p1 = (sx + sd * hw, sy)
        n = max(6, int(length / (3.2 * px_per_cm)))
        path = skia.Path()
        for i in range(n):
            u0, u1 = i / n, (i + 0.8) / n
            path.moveTo(p0[0] + (p1[0] - p0[0]) * u0, p0[1] + (p1[1] - p0[1]) * u0)
            path.lineTo(p0[0] + (p1[0] - p0[0]) * u1, p0[1] + (p1[1] - p0[1]) * u1)
        pen.line(path, lw * 1.9, '#1d1e22'); pen.line(path, lw, mix('#9aa0a8', '#000000', 1 - k))
    if part in ('all', 'back'):
        seat = rrect(sx - hw - 3 * px_per_cm, sy - 2.2 * px_per_cm, 2 * hw + 6 * px_per_cm, 4.4 * px_per_cm, 1.6 * px_per_cm)
        pen.fill(seat, '#3a3b42'); pen.line(seat, lw * 1.2, LINE)
    return sx, sy


# ====================================================================================================== acting: her vocabulary
# NORMAL (Mon, Tue, daylight): bounce, blink, look away and laugh, wave hi. OBSESSED (from Wednesday): head tilt, never
# blinks (the arc), eye lock to the lens, holds her smile too long, phone glow under her chin, typing, one inch too close,
# arms wide across a doorway or gate (never touching), the bracelet held out, the swing and the song. CREEPY (nights):
# lies flat as a chalk drawing and slides, stands up out of the ground, the neck stretch. DRAIN: colour to chalk-white,
# then the wind takes her as dust. Every clip has a clear start and end; feet stay on the ground (the bounce is on her
# toes, never a hop off the ground).
def _ev_night(self, t0=-INF, t1=None, amount=1.0, fade=0.3):
    """Night: her colour goes chalk-flat by the arc's e_flatn (more each night)."""
    return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(dict(e_night=amount), _env(t, t0, t1, fade, fade)))


def _ev_stage(self, t0, name, t1=None, fade=0.3):
    """Override the arc with stage `name` for a window (e.g. a flash-forward, or the R2 locker beat at R2's smile)."""
    d = EVIE_STAGES[name]
    return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))


def _ev_bounce(self, t0, t1, rate=1.9, amp=1.0):
    """NORMAL: bouncing on her toes, too happy to stand still (heels up on each beat, the head bobbing a beat late, the
    braids swinging). Her toes never leave the ground."""
    def fn(P, t):
        w = _env(t, t0, t1, 0.3, 0.4)
        if w <= 0: return
        ph = (t - t0) * rate
        b = abs(math.sin(PI * ph)) ** 1.5
        P.tiptoe = max(getattr(P, 'tiptoe', 0.0), 0.85 * amp * b * w)
        P.h_nod += 0.05 * amp * w * math.sin(2 * PI * ph - 0.9)
        P.sway += 2.5 * amp * w * math.sin(PI * ph)
        P.sec_x += 0.4 * w * math.sin(2 * PI * ph)
    return self._add(t0, t1 + 0.5, fn)


def _ev_laugh_away(self, t0, dur=1.5, side=1):
    """NORMAL: she looks away and laughs (eyes squeezed, shoulders bouncing, the head turned and tipped), then back."""
    def fn(P, t):
        w = _env(t, t0, t0 + dur, 0.25, 0.4)
        if w <= 0: return
        P.mix(EXPR['evie_laugh'], w)
        P.h_turn += side * 0.38 * w; P.h_tilt += side * 9.0 * w; P.h_nod += 0.08 * w
        sh = max(0.0, math.sin(2 * PI * (t - t0) * 4.2)) * w * (1.0 - prog(t, t0, t0 + dur))
        P.shrug += 0.35 * sh; P.bob += 4.0 * sh
        P.look_x += side * 0.5 * w
    return self._add(t0, t0 + dur + 0.6, fn)


def _ev_wave_hi(self, t0, t1, side=1):
    """NORMAL: 'Hi!' A quick bright wave with her free (left) hand, the gap-tooth grin, a little bounce."""
    self.wave(t0, t1, side=side, speed=1.3, height=0.9)
    self.expr('evie_grin', t0, t1, 0.25)
    return self.bounce(t0, t1, rate=1.6, amp=0.6)


def _ev_lens_lock(self, t0, t1=None, fade=0.25):
    """OBSESSED: her eyes lock to the lens (to Adam, to us) and stay, the head dead still, small pupils."""
    d = dict(lock=1.0, still=0.75, pupil=0.72, _noblink=1.0)
    return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))


def _ev_hold_smile(self, t0, t1=None, fade=0.4):
    """OBSESSED: the smile held too long (before rule 2 the real one; after, the chalk line just stays), no blink, still."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        P.mix(EXPR['evie_hold'], w)
        P.still = max(P.still, 0.8 * w); P._noblink = max(P._noblink, w)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ev_tilt_hold(self, t0, angle=24.0, dur=1.4, t1=None):
    """OBSESSED: the slow head tilt, held (the arc already tilts her a little from Wednesday)."""
    return self.head_tilt(t0, angle, dur, t1, back='ease', back_dur=1.0)


def _ev_phone_glow(self, t0, t1=None, side=1, fade=0.5, look='up'):
    """OBSESSED: in the background before Adam notices her: the phone held just under her chin, its glow lighting her
    face from below; look='up' (eyes over the phone at Adam) or 'phone'."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        self._arm(P, side, w, -50.0, 34.0, 150.0, 'grip', up=0.9, prop='evie_phone')
        P.e_glow = max(P.e_glow, w)
        P.h_nod += 0.1 * w
        if look == 'up': P.look_y += -0.35 * w
        else: P.look_y += 0.7 * w
        P.still = max(P.still, 0.6 * w)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ev_type_phone(self, t0, t1, side=1, rate=5.5, gain=-22.0):
    """OBSESSED: typing on her phone (one-handed, the thumb tapping; the screen lights her face); 'phone_tap' events."""
    def fn(P, t):
        w = _env(t, t0, t1, 0.4, 0.4)
        if w <= 0: return
        tap = max(0.0, math.sin(2 * PI * (t - t0) * rate * 0.5)) ** 3
        self._arm(P, side, w, -46.0, 128.0 - 6.0 * tap, 150.0, 'grip', up=0.6, prop='evie_phone',
                  rot=side * 6.0 * tap)
        P.e_glow = max(P.e_glow, 0.65 * w)
        P.h_nod += 0.16 * w; P.look_y += 0.75 * w
    self._add(t0, t1 + 0.4, fn)
    tt = t0 + 0.45
    while tt < t1:
        self._ev(tt, 'phone_tap', gain + 3.0 * (hash01(int(tt * 100), 5) - 0.5)); tt += (1.0 + 0.5 * hash01(int(tt * 37), 6)) / rate
    return self


def _ev_one_inch(self, t0, t1=None, toward=1, fade=0.6):
    """OBSESSED: suddenly one inch from his shoulder: leaning in, head tilted toward him, very still (the film places
    her; she never touches)."""
    def fn(P, t):
        w = _env(t, t0, t1, fade, fade)
        if w <= 0: return
        P.lean += 5.0 * w; P.h_tilt += toward * 7.0 * w; P.h_dx += toward * 6.0 * w
        P.still = max(P.still, 0.7 * w)
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ev_block_wide(self, t0, t1=None, dur=0.8, fade=0.7):
    """OBSESSED / CREEPY: arms spread wide at shoulder height across a doorway or gate, palm open, the stub still in her
    right hand; she comes as close as she is let, never touching."""
    def fn(P, t):
        w = ease_in_out(prog(t, t0, t0 + dur)) * (1.0 if t1 is None or t < t1 else 1.0 - ease_in_out(prog(t, t1, t1 + fade)))
        if w <= 0: return
        self._arm(P, 1, w, 310.0, 12.0, 26.0, 'open', up=0.0)
        self._arm(P, -1, w, 310.0, 12.0, 26.0, 'grip', up=0.0)
        P.shrug += 0.12 * w
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ev_hold_out_bracelet(self, t0, t1=None, side=1, target=None, dur=0.7, fade=0.5):
    """OBSESSED: the woven bracelet held out on her fingers ('I made it myself. For you.'), toward target if given (it
    stops short: a gift is never pressed into a hand)."""
    if target is not None:
        return self.reach_to(t0, side, target, t1=t1, dur=dur, z=60.0, contact='tips', shape='relaxed', fade=fade,
                             prop='evie_bracelet')
    def fn(P, t):
        w = _env(t, t0, t1, dur, fade)
        if w <= 0: return
        self._arm(P, side, w, 40.0, 140.0, 250.0, 'relaxed', up=0.0, prop='evie_bracelet')
    return self._add(t0, None if t1 is None else t1 + fade, fn)


def _ev_swing_ride(self, t0, t1, pivot, length, amp=20.0, period=2.3, sep=0.35, ramp=1.5, gain=-22.0):
    """OBSESSED: on a swing (side view, swinging across the screen). The actor must sit on the swing's seat at rest:
    call a.seated(pivot[1] + length) first; this moves her along the arc, leans her with it, and keeps both hands on the
    chains. a.swing_state(t) -> (angle deg, seat point) to draw the swing with draw_swing at the same angle.
    'swing_creak' at each end of the swing."""
    self._swing = (t0, t1, pivot, length, amp, period, ramp)
    ppc = self.height / (self.sp['m'] * 100.0)
    def ang(t):
        if t < t0: return 0.0
        e = ease_in_out(prog(t, t0, t0 + ramp)) * (1.0 - ease_in_out(prog(t, t1 - ramp, t1)))
        return amp * e * math.sin(2 * PI * (t - t0) / period)
    self._swing_ang = ang
    def fn(P, t):
        a = math.radians(ang(t))
        P.dx += math.sin(a) * length
        P.dy += -length * (1.0 - math.cos(a))
        P.tilt += math.degrees(a) * 0.35
        P.lean += -4.0 * math.sin(a)
    self._add(t0 - 0.01, t1 + 0.01, fn)
    for sd in (1, -1):
        def chain(t, sd=sd):
            a = math.radians(ang(t))
            hy = 0.24 * self.height                       # she grips the chains a hand above her lap
            sx, sy = pivot[0] + math.sin(a) * length, pivot[1] + math.cos(a) * length
            hw = 46.0 * 0.5 * ppc * sep + 6.0 * ppc * (1 - sep)   # where draw_swing puts the chains
            return (sx - math.sin(a) * hy + sd * hw * math.cos(a), sy - math.cos(a) * hy + sd * hw * math.sin(a))
        self.reach_to(t0, sd, chain, t1=t1, dur=0.5, z=0.0, contact='grip', shape='grip', fade=0.5)
    tt = t0 + period / 4.0
    while tt < t1:
        if abs(ang(tt)) > 4.0: self._ev(tt, 'swing_creak', gain + 4.0 * (abs(ang(tt)) / max(amp, 1.0) - 1.0))
        tt += period / 2.0
    return self


def _ev_swing_state(self, t):
    """(angle deg, seat point) of the swing swing_ride set up (angle 0 and the rest seat before it starts)."""
    t0, t1, pivot, length, amp, period, ramp = self._swing
    a = self._swing_ang(t)
    r = math.radians(a)
    return a, (pivot[0] + math.sin(r) * length, pivot[1] + math.cos(r) * length)


_STICK_SYLL = [4, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 4, 3, 4]     # "Me and you, / and you and me, / stick like glue ..." in beats


def _ev_sing_song(self, t0, beat=0.42, n=32, amount=0.55, taps=False, gain=-18.0):
    """Mouth for "Stick Like Glue" (one syllable per beat, a held note at each phrase end), for when the sung take is not
    lip-synced with talk(). taps=True also emits one soft 'chalk_tap' per beat (the motif's tap)."""
    def fn(P, t):
        if t < t0 or t > t0 + n * beat + 0.3: return
        u = (t - t0) / beat
        k = int(u); f = u - k
        held = (k % 8) == 7
        o = amount * (math.sin(PI * min(1.0, f / 0.8)) if not held else 0.8)
        P.m_open = max(P.m_open, o * (0.8 + 0.2 * math.sin(k * 1.7)))
        P.m_round = max(P.m_round, 0.35 * o * (k % 3 == 0))
        P.h_tilt += 3.0 * math.sin(2 * PI * u / 4.0)
    self._add(t0, t0 + n * beat + 0.5, fn)
    if taps:
        for k in range(n): self._ev(t0 + k * beat, 'chalk_tap', gain - 2.0 * (k % 4 != 0), kind='beat')
    return self


def _ev_lie_flat(self, t0, dur=0.9, flat_k=None, direction=0.0, gain=-18.0):
    """CREEPY: she lies down flat, like a chalk drawing: the figure folds down into the ground plane (hinged at her feet)
    and turns into the chalk girl drawing lying on the ground. flat_k = the ground's foreshortening there."""
    def fn(P, t):
        u = ease_in_cubic(prog(t, t0, t0 + dur)) if t < t0 + dur else 1.0
        P.e_lie = max(P.e_lie, u)
        if flat_k is not None: P.e_flatk = flat_k
        P.e_lie_dir = direction
        P.still = max(P.still, 0.8)
    self._add(t0, None, fn)
    self._ev(t0 + dur * 0.55, 'chalk_scrape', gain, kind='flatten', dur=round(dur * 0.6, 3))
    return self


def _ev_flat_drawing(self, t0=-INF, t1=None, flat_k=None, direction=0.0):
    """CREEPY / setup: she is the chalk drawing on the ground (the little chalk girl in the Keeping Square)."""
    def fn(P, t):
        if t1 is not None and t > t1: return
        P.e_lie = 1.0; P.e_lie_dir = direction
        if flat_k is not None: P.e_flatk = flat_k
    return self._add(t0, t1, fn)


def _ev_slide_flat(self, t0, dur, to, scale_to=None, gain=-15.0, trail=True):
    """CREEPY: flat on the ground, she slides away (to = where her feet end up, design px; scale_to = her size there, for
    a slide in depth), smoothly and never running, leaving a faint chalk smear. 'chalk_scrape' (kind slide)."""
    def fn(P, t):
        u = ease_in_out(prog(t, t0, t0 + dur))
        x0, y0 = self.x0 + P.dx, self.y0 + P.dy
        P.dx += (to[0] - x0) * u; P.dy += (to[1] - y0) * u
        if scale_to is not None: P.e_scale *= 1.0 + (scale_to - 1.0) * u
        if trail:
            P.e_trail = max(P.e_trail, min(1.0, u * 6.0) * (1.0 - 0.6 * prog(t, t0 + dur, t0 + dur + 2.0)))
            P.e_tx, P.e_ty = x0 - self.x0, y0 - self.y0
    self._add(t0, None, fn)
    self._ev(t0, 'chalk_scrape', gain, kind='slide', dur=round(dur, 3))
    return self


def _ev_stand_from_ground(self, t0, dur=1.4, gain=-14.0):
    """CREEPY: the chalk drawing stands up out of the ground into Evie: it peels up from the feet, the drawing turns into
    her, a rubbery overshoot past upright and a settle. Set e_lie = 1 before (flat_drawing / lie_flat)."""
    def fn(P, t):
        if t < t0: return
        u = prog(t, t0, t0 + dur)
        v = ease_in_out(u) + 0.1 * math.sin(PI * clamp((u - 0.5) / 0.5))       # slow peel up, rubbery overshoot, settle
        P.e_lie = min(P.e_lie, 1.0 - v) if u < 1 else min(P.e_lie, 0.0)
        P.still = max(P.still, 0.8 * (1.0 - u))
    self._add(t0, None, fn)
    self._ev(t0, 'chalk_scrape', gain, kind='rise', dur=round(dur * 0.85, 3))
    self._ev(t0 + dur * 0.8, 'chalk_tap', gain - 2.0, kind='land')
    return self


def _ev_neck_up(self, t0, dur, length, dx=0.0, grow=0.0, t1=None, back_dur=1.6, gain=-24.0):
    """CREEPY (R5): her neck stretches smoothly up toward his window, 'Up... and up...': length in body units (1000 = her
    height; 900 lifts her head almost her own height), dx sideways, grow = the head's size gain toward a high camera.
    Rubbery and smooth: no joints, no crack, no cracking sound (only a long soft chalk drag)."""
    def fn(P, t):
        u = ease_in_out(prog(t, t0, t0 + dur))
        if t1 is not None and t > t1: u *= 1.0 - ease_in_out(prog(t, t1, t1 + back_dur))
        P.e_neck += length * u; P.e_neck_dx += dx * u
        P.h_scale *= 1.0 + grow * u
        P.h_tilt += -0.5 * P.h_tilt * u + 4.0 * math.sin(t * 0.9) * u
        P.still = max(P.still, 0.9 * u)
    self._add(t0, None if t1 is None else t1 + back_dur, fn)
    self._ev(t0, 'chalk_scrape', gain, kind='stretch', dur=round(dur, 3))
    return self


def _ev_drain_away(self, t0, flat_dur=1.6, dust_dur=2.8, wind=1.0, gain=-12.0):
    """DRAIN (R7, on the doormat at full smile): her colour drains to flat chalk-white over flat_dur, then the wind lifts
    her away as dust over dust_dur (wind +1 blows toward screen right). She never crumbles or falls. 'chalk_dust_whoosh'."""
    def fn(P, t):
        u1 = prog(t, t0, t0 + flat_dur); u2 = prog(t, t0 + flat_dur, t0 + flat_dur + dust_dur)
        P.e_drain = max(P.e_drain, 0.4 * u1 + 0.6 * u2)
        P.e_wind = wind
        P.still = max(P.still, 0.9 * u1)
        P._noblink = 1.0
    self._add(t0, None, fn)
    self._ev(t0 + flat_dur * 0.9, 'chalk_dust_whoosh', gain, kind='drain', dur=round(dust_dur + 0.6, 3))
    return self


def _ev_chalk_tap(self, t, gain=-16.0, side=-1):
    """One soft chalk tap (her stub on a surface, on a beat she chooses): the right hand flicks down; 'chalk_tap'."""
    def fn(P, tt):
        k = math.exp(-((tt - t) / 0.07) ** 2)
        pre = 'hl_' if side > 0 else 'hr_'
        P.__dict__[pre + 'down'] = P.__dict__.get(pre + 'down', 336.0) + 10.0 * k
    self._add(t - 0.3, t + 0.3, fn)
    self._ev(t, 'chalk_tap', gain, kind='tap')
    return self


for _n, _f in (('night', _ev_night), ('stage', _ev_stage), ('bounce', _ev_bounce), ('laugh_away', _ev_laugh_away),
               ('wave_hi', _ev_wave_hi), ('lens_lock', _ev_lens_lock), ('hold_smile', _ev_hold_smile),
               ('tilt_hold', _ev_tilt_hold), ('phone_glow', _ev_phone_glow), ('type_phone', _ev_type_phone),
               ('one_inch', _ev_one_inch), ('block_wide', _ev_block_wide), ('hold_out_bracelet', _ev_hold_out_bracelet),
               ('swing_ride', _ev_swing_ride), ('swing_state', _ev_swing_state), ('sing_song', _ev_sing_song),
               ('lie_flat', _ev_lie_flat), ('flat_drawing', _ev_flat_drawing), ('slide_flat', _ev_slide_flat),
               ('stand_from_ground', _ev_stand_from_ground), ('neck_up', _ev_neck_up), ('drain_away', _ev_drain_away),
               ('chalk_tap', _ev_chalk_tap)):
    if hasattr(Acting, _n): raise RuntimeError('characters_evie: Acting.%s already exists' % _n)
    setattr(Acting, _n, _f)


# ====================================================================================================== handwriting in chalk
# Adam's handwriting (Evie writes in it: she only has what he has): round letters, curly M's. Strokes in a unit box
# (x 0..1 right, y 0..1 down), traced in order.
_LETTERS = {
    'O': [[(0.62, 0.06), (0.24, 0.12), (0.05, 0.5), (0.24, 0.92), (0.6, 0.95), (0.92, 0.6), (0.84, 0.16), (0.55, 0.04), (0.36, 0.13)]],
    'N': [[(0.02, 0.9), (0.1, 0.98), (0.1, 0.5), (0.12, 0.04), (0.5, 0.52), (0.86, 0.95), (0.88, 0.5), (0.9, 0.03)]],
    'L': [[(0.2, 0.02), (0.16, 0.5), (0.14, 0.94), (0.5, 0.95), (0.86, 0.88)]],
    'Y': [[(0.06, 0.04), (0.3, 0.32), (0.5, 0.5)], [(0.94, 0.04), (0.7, 0.3), (0.5, 0.5), (0.4, 0.76), (0.3, 0.98)]],
    'M': [[(-0.02, 0.86), (0.08, 0.98), (0.1, 0.6), (0.12, 0.2), (0.2, 0.05), (0.31, 0.1), (0.41, 0.46), (0.5, 0.62),
           (0.57, 0.4), (0.66, 0.08), (0.78, 0.05), (0.88, 0.28), (0.9, 0.82), (0.98, 0.98), (1.08, 0.86)]],
    'E': [[(0.88, 0.07), (0.22, 0.06), (0.15, 0.5), (0.13, 0.94), (0.88, 0.94)], [(0.15, 0.5), (0.7, 0.5)]],
    'A': [[(0.05, 0.98), (0.5, 0.02), (0.95, 0.98)], [(0.24, 0.62), (0.76, 0.62)]],
    'D': [[(0.14, 0.02), (0.13, 0.98)], [(0.14, 0.03), (0.62, 0.07), (0.92, 0.46), (0.66, 0.92), (0.13, 0.97)]],
}


def _homography(quad):
    """3x3 map from the unit floor square (u across, v away from the camera) to the quad's screen points
    [near-left (0,0), near-right (1,0), far-right (1,1), far-left (0,1)]."""
    A, b = [], []
    for (u, v), (x, y) in zip(((0, 0), (1, 0), (1, 1), (0, 1)), quad):
        A.append([u, v, 1, 0, 0, 0, -u * x, -v * x]); b.append(x)
        A.append([0, 0, 0, u, v, 1, -u * y, -v * y]); b.append(y)
    h = np.linalg.solve(np.array(A, float), np.array(b, float))
    return np.append(h, 1.0).reshape(3, 3)


def _hmap(H, uv):
    uv = np.atleast_2d(np.asarray(uv, float))
    q = np.hstack([uv, np.ones((len(uv), 1))]) @ H.T
    return q[:, :2] / q[:, 2:3]


def _chalk_layout(text, box, axis='u'):
    """Letters of text as stroke lists in floor (u, v) coordinates inside box (u0, v0, u1, v1). axis 'u': side by side
    across the floor; 'v': one after another along v (M... E... creeping toward the kitchen). Letter tops face +v."""
    u0, v0, u1, v1 = box
    chars = [ch for ch in text.upper() if ch in _LETTERS]
    n = max(1, len(chars))
    out = []
    for i, ch in enumerate(chars):
        if axis == 'u':
            du = (u1 - u0) / n
            ua, ub, va, vb = u0 + i * du + 0.1 * du, u0 + (i + 1) * du - 0.1 * du, v0, v1
        else:
            dv = (v1 - v0) / n
            ua, ub, va, vb = u0, u1, v0 + i * dv + 0.12 * dv, v0 + (i + 1) * dv - 0.12 * dv
        strokes = []
        for st in _LETTERS[ch]:
            p = _cr(st, max(12, 6 * len(st)))
            uv = np.column_stack([ua + p[:, 0] * (ub - ua), max(va, vb) - p[:, 1] * abs(vb - va)])
            strokes.append(uv)
        out.append((ch, strokes))
    return out


def _floor_scale(H, uv, size_cm):
    """Screen px per cm across the floor (u direction) at floor point uv."""
    a = _hmap(H, [(uv[0] - 0.01, uv[1]), (uv[0] + 0.01, uv[1])])
    return float(np.hypot(*(a[1] - a[0]))) / (0.02 * size_cm[0])


def chalk_word(pen, text, quad, box=(0.05, 0.1, 0.95, 0.9), u=1.0, size_cm=(100.0, 100.0), width_cm=1.7, axis='u',
               alpha=1.0, colr=CHALK):
    """Chalk letters in Adam's handwriting (round, curly M's) on a floor or path: quad = the floor rectangle's screen
    corners [near-left, near-right, far-right, far-left] (size_cm its real size), box = where the word goes in it
    (u0, v0, u1, v1 in 0..1), u = how much is written (0..1, stroke by stroke). ONLY ME, ADAM, DANNY."""
    H = _homography(quad)
    lay = _chalk_layout(text, box, axis)
    allst = [st for _, sts in lay for st in sts]
    lens = [float(_arclen(st)[-1]) for st in allst]
    tot = sum(lens) or 1.0
    done = u * tot
    cv = pen.cv
    for st, ln in zip(allst, lens):
        if done <= 0: break
        part = st if done >= ln else _sub_curve(st, 0.0, done, max(3, int(len(st) * done / ln) + 2))
        done -= ln
        xy = _hmap(H, part)
        w = width_cm * _floor_scale(H, st[len(st) // 2], size_cm)
        _chalk_stroke(cv, _pts_path(xy[:, 0], xy[:, 1], False, 0.6), max(w, 1.0), alpha, colr)


class LetterboxFingers:
    """The long chalk-white fingers (R6 and R7): they slide in through the letterbox, run down the inside of the door to
    the floor, creep across it and write the text in chalk, stroke by stroke, in Adam's handwriting.

    slot = (x, y, w): the slot's centre and width on the inside face of the door (design px); door_base = the floor point
    under it; floor_quad / size_cm: the hall floor (see chalk_word); box / axis: where the text goes; px_per_cm = scale
    at the door. Timing: t_in (fingertips appear), t_write (first stroke; default t_in + reach), letter_times (each
    letter's start, e.g. on the narrator's 'O. N. L. Y.'), letter_dur, t_out (they slide back out; None = they stay).
    Use: f.draw_chalk(pen, t) on the floor layer (the letters stay written), f.draw(pen, t) over it (the fingers),
    f.tip(t) (the writing fingertip), f.events ('chalk_scrape' per stroke, kind write; kind creep while they come in).
    Four fingers, too long, impossibly many soft knuckle creases, rounded tips, no nails; chalk dust at the tips."""

    def __init__(self, slot, door_base, floor_quad, text='ONLY', box=(0.2, 0.3, 0.8, 0.62), size_cm=(100.0, 140.0),
                 px_per_cm=8.0, t_in=0.0, reach=1.4, t_write=None, letter_times=None, letter_dur=0.85, t_out=None,
                 out_dur=1.2, axis='u', width_cm=1.7, finger_cm=1.9, gain=-13.0, seed=0):
        self.slot, self.base, self.quad = slot, door_base, floor_quad
        self.H = _homography(floor_quad)
        self.size_cm, self.ppc, self.wcm, self.fcm = size_cm, px_per_cm, width_cm, finger_cm
        self.t_in, self.t_out, self.out_dur, self.seed = t_in, t_out, out_dur, seed
        self.t_write = t_in + reach if t_write is None else t_write
        lay = _chalk_layout(text, box, axis)
        n = len(lay)
        lt = list(letter_times) if letter_times else [self.t_write + i * (letter_dur + 0.25) for i in range(n)]
        self.strokes = []                     # (t_start, t_end, uv array)
        for i, (ch, sts) in enumerate(lay):
            avail = (lt[i + 1] - lt[i] - 0.15) if i + 1 < n else letter_dur
            d = max(0.25, min(letter_dur, avail))
            lens = [float(_arclen(s)[-1]) for s in sts]
            tot = sum(lens) or 1.0
            tt = lt[i]
            lift = 0.08 if len(sts) > 1 else 0.0
            for s, ln in zip(sts, lens):
                dd = (d - lift * (len(sts) - 1)) * ln / tot
                self.strokes.append((tt, tt + dd, s)); tt += dd + lift
        self.events = []
        self.events.append(dict(t=round(t_in, 4), name='chalk_scrape', gain_db=gain - 9.0, pan=0.0,
                                params=dict(kind='creep', dur=round(self.t_write - t_in, 3)), who='evie'))
        for (a, b, s) in self.strokes:
            self.events.append(dict(t=round(a, 4), name='chalk_scrape', gain_db=gain, pan=0.0,
                                    params=dict(kind='write', dur=round(b - a, 3)), who='evie'))
        if t_out is not None:
            self.events.append(dict(t=round(t_out, 4), name='chalk_scrape', gain_db=gain - 8.0, pan=0.0,
                                    params=dict(kind='creep', dur=round(out_dur, 3)), who='evie'))

    # ---------------------------------------------------------------- geometry
    def _xy(self, uv): return _hmap(self.H, uv)[0]

    def _approach(self):
        sx, sy, sw = self.slot
        bx, by = self.base
        first = self._xy(self.strokes[0][2][0]) if self.strokes else np.array([bx, by + 40.0])
        return _cr([(sx, sy + 2), (sx, sy + 0.25 * (by - sy)), (sx + (bx - sx) * 0.7, sy + 0.8 * (by - sy)), (bx, by),
                    ((bx + first[0]) / 2, (by + first[1]) / 2), tuple(first)], 60)

    def tip(self, t):
        """(x, y, on_floor_uv or None, writing) of the writing fingertip at t (None before t_in)."""
        if t < self.t_in: return None
        a = self._approach(); L = _arclen(a)
        if t < self.t_write:
            p, _ = _at_len(a, L[-1] * ease_in_out(prog(t, self.t_in, self.t_write)), L)
            return float(p[0]), float(p[1]), None, False
        cur = None
        for k, (ta, tb, s) in enumerate(self.strokes):
            if t < ta:
                if k == 0: cur = (s[0], False)
                else:
                    pe, pa = self.strokes[k - 1][2][-1], s[0]
                    u = ease_in_out(prog(t, self.strokes[k - 1][1], ta))
                    cur = (pe + (pa - pe) * u, False)
                break
            if t <= tb:
                ln = _arclen(s)
                p, _ = _at_len(s, ln[-1] * prog(t, ta, tb), ln)
                cur = (p, True)
                break
        if cur is None: cur = (self.strokes[-1][2][-1], False)
        xy = self._xy(cur[0])
        return float(xy[0]), float(xy[1]), cur[0], cur[1]

    # ---------------------------------------------------------------- drawing
    def draw_chalk(self, pen, t, alpha=1.0):
        cv = pen.cv
        for (ta, tb, s) in self.strokes:
            if t <= ta: break
            part = s if t >= tb else _sub_curve(s, 0.0, float(_arclen(s)[-1]) * prog(t, ta, tb), max(3, int(len(s) * prog(t, ta, tb)) + 2))
            xy = _hmap(self.H, part)
            w = self.wcm * _floor_scale(self.H, s[len(s) // 2], self.size_cm)
            _chalk_stroke(cv, _pts_path(xy[:, 0], xy[:, 1], False, 0.6), max(w, 1.0), alpha)

    def draw(self, pen, t, detail=2):
        tp = self.tip(t)
        if tp is None: return
        sx, sy, sw = self.slot
        bx, by = self.base
        tx, ty, uv, writing = tp
        back = 0.0
        if self.t_out is not None and t > self.t_out:
            back = ease_in_out(prog(t, self.t_out, self.t_out + self.out_dur))
            if back >= 1.0: return
        ptip = self._xy(uv) if uv is not None else None
        sc_tip = _floor_scale(self.H, uv, self.size_cm) if uv is not None else self.ppc
        a_ap = self._approach()
        on_floor = uv is not None
        cv = pen.cv
        fl = []
        for j in range(4):                                     # index (writes) .. little finger
            off_slot = (j - 1.5) * self.fcm * 1.2 * self.ppc
            if on_floor:
                d = np.array([tx - bx, ty - by]); dl = np.hypot(*d) or 1.0
                nrm = np.array([-d[1], d[0]]) / dl
                wig = np.array([math.sin(t * 3.1 + j * 1.7), math.cos(t * 2.3 + j)]) * 0.6 * sc_tip * (j > 0)
                tipj = np.array([tx, ty]) + nrm * j * self.fcm * 2.6 * sc_tip * (1 if self.seed % 2 == 0 else -1) \
                    - d / dl * j * 3.0 * sc_tip + wig
                lift = 0.0 if writing or j else 0.6 * sc_tip
                mx_, my_ = (bx + tipj[0]) / 2 + off_slot * 0.3, (by + tipj[1]) / 2 - lift
                arch = (1.6 if j == 0 else 1.1) * self.fcm * sc_tip          # the writing curl: the last joint arches
                kx, ky = mx_ + (tipj[0] - mx_) * 0.8, my_ + (tipj[1] - lift - my_) * 0.8 - arch
                pts = [(sx + off_slot, sy + 2), (sx + off_slot, sy + 0.25 * (by - sy)), (bx + off_slot * 0.8, by - 0.12 * (by - sy)),
                       (bx + off_slot * 0.7, by), (mx_, my_), (kx, ky), (tipj[0], tipj[1] - lift)]
                c_ = _cr(pts, 64)
            else:
                Lp = _arclen(a_ap)
                sfrac = math.hypot(tx - a_ap[0][0], ty - a_ap[0][1])
                k = int(np.argmin(np.hypot(a_ap[:, 0] - tx, a_ap[:, 1] - ty)))
                c_ = a_ap[:max(k, 1) + 1].copy()
                c_[:, 0] += off_slot * np.linspace(1.0, 0.8, len(c_))
                c_ = c_[:max(2, len(c_) - j)]
            if back > 0:                                        # sliding back out: the curve shortens from the tip
                Lc = _arclen(c_)
                c_ = _sub_curve(c_, 0.0, Lc[-1] * (1.0 - back), max(4, int(len(c_) * (1.0 - back))), Lc)
            fl.append(c_)
        for j in (3, 2, 1, 0):
            self._finger(cv, fl[j], self.ppc, sc_tip if on_floor else self.ppc, j, t, detail)
        # the hand: a long narrow palm and the wrist hanging down the inside of the door from the slot, the four fingers
        # growing out of its knuckles
        if back < 0.98:
            pc, F_ = self.ppc, self.fcm
            ph = (13.0 * pc) * (1.0 - back)
            hw0, hw1 = 2.2 * F_ * pc, 2.9 * F_ * pc
            palm = [(sx - hw0, sy - 1.0 * pc), (sx + hw0, sy - 1.0 * pc), (sx + hw1, sy + ph * 0.75), (sx + hw1 * 0.92, sy + ph),
                    (sx + hw1 * 0.45, sy + ph + 0.8 * pc), (sx, sy + ph + 1.0 * pc), (sx - hw1 * 0.45, sy + ph + 0.8 * pc),
                    (sx - hw1 * 0.92, sy + ph), (sx - hw1, sy + ph * 0.75)]
            pp = smooth(palm, True, 0.5)
            cv.drawPath(pp, skia.Paint(Color=col('#edebe3', 255), AntiAlias=True))
            cv.drawPath(pp, _chalk_paint('#77766f', 230, max(1.0, 0.22 * pc)))
            kk = skia.Path()                                   # the knuckle line and two tendons
            for q_ in (-0.75, -0.25, 0.25, 0.75):
                x_ = sx + q_ * hw1 * 0.95; y_ = sy + ph + 0.35 * pc * (1.0 - abs(q_))
                kk.addCircle(x_, y_ - 0.2 * pc, 0.55 * F_ * pc * 0.5)
                kk.moveTo(x_ * 0.8 + sx * 0.2, sy + 0.5 * pc); kk.lineTo(x_, y_ - 0.9 * pc)
            cv.drawPath(kk, _chalk_paint(CHALK_DK, 110, max(1.0, 0.16 * pc)))
        # the back of the hand, pressed into the slot (knuckles across it)
        kn = rrect(sx - 2.4 * self.fcm * self.ppc, sy - 1.1 * self.ppc, 4.8 * self.fcm * self.ppc, 2.6 * self.ppc, 1.2 * self.ppc)
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(sx - sw / 2, sy - 2.0 * self.ppc, sw, 4.0 * self.ppc), skia.ClipOp.kIntersect, True)
        pen.fill(kn, '#e9e7df'); pen.line(kn, max(1.0, 0.25 * self.ppc), '#6e6d69')
        cv.restore()

    def _finger(self, cv, c_, s0, s1, j, t, detail):
        if len(c_) < 2: return
        L = _arclen(c_)
        if L[-1] < 1.0: return
        n = len(c_)
        ws = np.interp(np.linspace(0, 1, n), [0, 0.35, 1.0], [s0, s0 * 0.9 + s1 * 0.1, s1]) * self.fcm * (1.0 - 0.1 * j) * 0.5
        J1, J2 = 0.62, 0.84                                     # two knuckle joints: a bulge at each, tapering to the tip
        ws = ws * np.interp(np.linspace(0, 1, n), [0, 0.3, J1 - 0.05, J1, J1 + 0.05, J2 - 0.04, J2, J2 + 0.04, 0.95, 1.0],
                            [1.25, 1.02, 0.9, 1.04, 0.86, 0.8, 0.9, 0.74, 0.76, 0.72])
        tg = np.gradient(c_, axis=0); tg /= (np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-6)
        nr = np.column_stack([-tg[:, 1], tg[:, 0]])
        left = c_ + nr * ws[:, None]; right = c_ - nr * ws[:, None]
        ang0 = math.atan2(tg[-1, 1], tg[-1, 0])
        cap = [(c_[-1, 0] + math.cos(ang0 + a) * ws[-1], c_[-1, 1] + math.sin(ang0 + a) * ws[-1]) for a in np.linspace(PI / 2, -PI / 2, 9)]
        pts = [tuple(p) for p in left] + cap + [tuple(p) for p in right[::-1]]
        path = poly(pts, True)
        lw = max(1.0, 0.22 * s1)
        cv.drawPath(path, skia.Paint(Color=col('#edebe3', 255), AntiAlias=True))
        sh = _pts_path((c_ - nr * ws[:, None] * 0.55)[:, 0], (c_ - nr * ws[:, None] * 0.55)[:, 1], False, 0.6)
        cv.drawPath(sh, _chalk_paint(CHALK_SH, 150, float(np.mean(ws)) * 0.6))
        if detail >= 1:                                         # soft knuckle creases, far too many of them
            cr = skia.Path()
            step = 3.2 * float(np.mean([s0, s1]))
            s = step * 1.3
            while s < L[-1] - step * 0.6:
                p, tgv = _at_len(c_, s, L)
                w = float(np.interp(s, L, ws)) * 0.7
                nx, ny = -tgv[1], tgv[0]
                cr.moveTo(p[0] + nx * w, p[1] + ny * w)
                cr.quadTo(p[0] + tgv[0] * w * 0.35, p[1] + tgv[1] * w * 0.35, p[0] - nx * w, p[1] - ny * w)
                s += step
            cv.drawPath(cr, _chalk_paint(CHALK_DK, 40, lw * 0.8))
        jk = skia.Path()                                        # the two joints: strong creases across the finger
        for jf in (J1, J2):
            p, tgv = _at_len(c_, L[-1] * jf, L)
            w = float(np.interp(L[-1] * jf, L, ws)) * 0.85
            nx, ny = -tgv[1], tgv[0]
            for dd_ in (-0.25, 0.25):
                ox, oy = tgv[0] * w * dd_, tgv[1] * w * dd_
                jk.moveTo(p[0] + nx * w + ox, p[1] + ny * w + oy)
                jk.quadTo(p[0] + tgv[0] * w * 0.4 + ox, p[1] + tgv[1] * w * 0.4 + oy, p[0] - nx * w + ox, p[1] - ny * w + oy)
        cv.drawPath(jk, _chalk_paint('#77766f', 170, lw * 0.9))
        cv.drawPath(path, _chalk_paint('#77766f', 230, lw))
        tx, ty = c_[-1]
        cv.drawCircle(float(tx + math.cos(ang0) * ws[-1] * 0.6), float(ty + math.sin(ang0) * ws[-1] * 0.6), float(ws[-1] * 1.6),
                      skia.Paint(Color=col(CHALK, 70), AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, float(ws[-1] * 0.6))))


class StubDrop:
    """The chalk stub dropping through the letterbox (R6): it falls from the slot to the floor at the door, bounces once,
    and rolls to the bottom stair. slot_xy = where it drops from, floor_y = the floor's screen y under the slot, stop_xy =
    where it comes to rest (against the bottom stair), px_per_cm = scale at the door. pos(t) -> (x, y, angle) or None;
    draw(pen, t); events: 'chalk_stub_drop' (kind drop, bounce), 'chalk_roll' (dur), 'chalk_tap' (kind stop)."""

    def __init__(self, t0, slot_xy, floor_y, stop_xy, px_per_cm=8.0, roll_dur=1.5, gain=-10.0):
        self.t0, self.p0, self.fy, self.p1, self.ppc, self.rd = t0, slot_xy, floor_y, stop_xy, px_per_cm, roll_dur
        hm = max(0.05, (floor_y - slot_xy[1]) / (px_per_cm * 100.0))
        self.tf = math.sqrt(2 * hm / 9.81)
        self.tb = 0.2
        self.events = [dict(t=round(t0 + self.tf, 4), name='chalk_stub_drop', gain_db=gain, pan=0.0, params=dict(kind='drop'), who='evie'),
                       dict(t=round(t0 + self.tf + self.tb, 4), name='chalk_stub_drop', gain_db=gain - 8.0, pan=0.0,
                            params=dict(kind='bounce'), who='evie'),
                       dict(t=round(t0 + self.tf + self.tb, 4), name='chalk_roll', gain_db=gain - 9.0, pan=0.0,
                            params=dict(dur=round(roll_dur, 3)), who='evie'),
                       dict(t=round(t0 + self.tf + self.tb + roll_dur, 4), name='chalk_tap', gain_db=gain - 6.0, pan=0.0,
                            params=dict(kind='stop'), who='evie')]

    def pos(self, t):
        if t < self.t0: return None
        x0, y0 = self.p0; x1, y1 = self.p1
        dt = t - self.t0
        if dt < self.tf:
            u = dt / self.tf
            return x0, y0 + (self.fy - y0) * u * u, 90.0 + 160.0 * u
        dt -= self.tf
        land = (x0, self.fy)
        if dt < self.tb:
            u = dt / self.tb
            return land[0] + (x1 - land[0]) * 0.05 * u, self.fy - 4.0 * self.ppc * math.sin(PI * u) + (y1 - self.fy) * 0.05 * u, 250.0 + 40 * u
        dt -= self.tb
        u = ease_out_cubic(prog(dt, 0.0, self.rd))
        k = 0.05 + 0.95 * u
        return land[0] + (x1 - land[0]) * k, self.fy + (y1 - self.fy) * k, 290.0 + 260.0 * u

    def draw(self, pen, t, detail=2):
        p = self.pos(t)
        if p is None: return
        draw_chalk_stub(pen, p[0], p[1], self.ppc, p[2], detail)


# ====================================================================================================== self-test
def _selftest_evie():
    """Evie: arc stages, every form draws (front, 3/4, back, bust, flat drawing, neck, drain), clips and events."""
    from engine.core import set_render_size
    set_render_size(640, 360)
    s = skia.Surface(640, 360); cv = s.getCanvas(); pen = Pen(cv)
    st = [evie_stage(_EV_T0[k] + 0.5)['e_chalk'] for k in _EV_ORDER]
    assert st == sorted(st) and st[-1] == 1.0 and st[2] == 0.0, st
    assert evie_stage(_EV_T0['wed'] + 1)['_noblink'] == 1.0 and evie_stage(_EV_T0['mon'] + 1)['_noblink'] == 0.0
    a = Acting('evie', height=300.0).place(320, 340)
    a.bounce(0.0, 1.0); a.laugh_away(1.0); a.wave_hi(2.0, 3.0); a.phone_glow(3.0, 4.0); a.type_phone(4.0, 5.0)
    a.block_wide(5.0, 6.0); a.lie_flat(6.0); a.slide_flat(7.0, 1.0, (200, 330)); a.stand_from_ground(8.5)
    a.neck_up(10.0, 2.0, 600.0); a.drain_away(12.5)
    for t in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 9.2, 11.5, 13.0, 14.5, 15.5):
        P = a.at(t)
        for tr in (0.0, 0.5, 1.6):
            P.turn = tr
            draw(pen, 'evie', 320, 340, 300, P, t=t)
    draw_bust(pen, 'evie', 320, 180, 1.0, Pose(e_chalk=1.0, m_open=0.4), t=1.0)
    names = {e['name'] for e in a.events}
    assert {'phone_tap', 'chalk_scrape', 'chalk_tap', 'chalk_dust_whoosh'} <= names, names
    f = LetterboxFingers((320, 120, 60), (330, 300), [(150, 350), (500, 350), (440, 250), (210, 250)], t_in=0.0)
    for t in (0.3, 1.0, 2.0, 3.0, 5.0): f.draw_chalk(pen, t); f.draw(pen, t)
    sd = StubDrop(0.0, (320, 130), 300, (200, 330))
    for t in (0.1, 0.5, 1.0, 3.0): sd.draw(pen, t)
    return True


_selftest_ev_prev = _selftest


def _selftest():
    _selftest_ev_prev()
    _selftest_evie()
    print('evie self-test ok (arc stages, every form in 3 views, bust, flat drawing, neck, drain dust, letterbox, stub)')
