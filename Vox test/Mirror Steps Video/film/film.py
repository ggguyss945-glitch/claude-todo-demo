"""film.py: the assembler for "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN".

    from film import Film
    F = Film(timeline_dict)            # engine set_render_size(...) first (render.py does it)
    F.frame(t, i) -> uint8 RGB         # one frame at the engine render size
    F.duration                         # 700.0 s (plan meta)
    F.shots                            # the 317 plan shots (plan/shots.json dicts)
    F.events(path=None)                # writes _work/align/film_events.json for audio/cues.py (picture-synced SFX)

    python3 film.py --sheet OUT_PREFIX [--size 960x540] [--tile 320] [--cols 5] [--per 40] [--part k/n] [ids...]
    python3 film.py --events           # -> _work/align/film_events.json
    python3 film.py --bench [ids...]   # full-size warm s/frame per shot (sets + cast + HUD), heaviest first
    python3 film.py --list

Everything comes from plan/shots.json (PLAN.md): one SetPiece per shot from sets.build_shot (layers, anchors, grade,
focus / dof, per-frame fx), the cast from characters.CharRig (acting from chars[].acts, lip-sync on the timeline's line
envelopes), a Cam from cam.keys (+ snaps, hits, handheld, 2 %/s post push on inserts and UI), transitions (cut, glitch,
white, 0.3 s centred dissolve, black) and fx_post, and the HUD:
  - captions (shots.json captions[]: 33 px uppercase at y 964, soft halo; hidden on cards and black),
  - the header (left label at 20 %, "RULE n OF 7" at 35 %; right: the in-world running timecode of the side the camera
    is on: ours from 23:57:00 at 19.40 s, running backward 278.97-281.81 s with a glitch; theirs 06:59:40 looping every
    19.48 s with a 2-frame snap; stuck 07:00:00:00 after the real bell; memory "14 YEARS AGO"),
  - Tess's countdown pill (dilated steps that land on her calls, pops on 60 / 45 / 20 / 5, red 0),
  - the 11:57 PM time card, command tags, red X, pinned labels (projected through the shot camera),
  - the phone (Mom's text thread, the voicemail list and the voicemail, calling / connected with a waveform that follows
    Mom's real line, goes flat in the pause and spikes on the chair scrape),
  - the seven rule cards: lipstick on a flashlight-lit silver mirror pane, title at +1.0 s, the statement written word by
    word on the narrator's word times, a 7-step stair marker, a finger-wipe exit; LIKE / SUBSCRIBE on cards 1-2.
Tess's beam follows her flashlight hand when she is in the frame (sets Beam.override); the queen in the phone is clipped
to the screen; rule cards keep the neighbouring shot's cast breathing behind the blur.
"""
import bisect, json, math, os, sys, time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import cv2
import skia
from engine import hud as H
from engine.core import (DW, DH, CFG, LINE, Pen, col, mix, clamp, lerp, prog, ease, ease_in_out, ease_out_cubic,
                         ease_out_back, noise1, hash01, text, text_width, rrect, rect, oval, poly, smooth, union, minus,
                         surface_for, wrap as wrap_text)
from engine.camera import Cam
from engine.post import GRADES
from engine.scene import Layer, render_frame, project
import characters as CH
import sets as ST

WORK = os.path.join(HERE, '_work')
PLAN = os.path.join(HERE, 'plan', 'shots.json')
SOUND = os.path.join(HERE, 'plan', 'sound_plan.json')
TIMELINE = os.path.join(WORK, 'align', 'timeline.json')
EVENTS = os.path.join(WORK, 'align', 'film_events.json')
FPS = 60
DISSOLVE = 0.30                       # centred on the cut
H._hand = CH.hud_phone_hand           # the cast's hand on the phone UI

LIPSTICK, LIP_DK, LIP_HI, LIP_GLOW = '#c63449', '#7e1a28', '#ec7d8a', '#ff4060'
RED = '#e3262e'
NUMW = {1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR', 5: 'FIVE', 6: 'SIX', 7: 'SEVEN'}
_ERR = set()
# shots whose plan entry has no cast although the picture needs it (S055: "you and Tess tiny at the mirror")
EXTRA_CHARS = {'S055': [dict(who='you', at='you_mirror', mode='body', view='q_right', expr='dread',
                             acts=[[120.98, 'grip_frame', {}]]),
                        dict(who='tess', at='tess_mirror', mode='body', view='q_left', expr='tense',
                             acts=[[120.0, 'flashlight', {'aim': 'floor', 'sweep': 0.4}]])],
               # the bunk hit reads as boards alone: grown Noah's shoulder and face take the hit, then rise under the bunk
               'S259': [dict(who='noah_grown', at=[1290, 610, 0.62], mode='bust', view='q_left', expr='shaken',
                             acts=[[573.54, 'stand_hit', {'what': 'bunk'}], [573.62, 'expr', {'name': 'shock'}]])],
               'S260': [dict(who='noah_grown', at=[1260, 1400, 1300, 1.0], mode='body', view='q_left', expr='fear',
                             acts=[[574.6, 'look_at_hands', {}]])]}
# acts added to plan cast entries: grown Noah is "sitting on the floor" in the ending (the plan left him standing)
FLOOR_SIT = [[-1.0, 'sit', {}]]
PATCH_ACTS = {('S058', 'noah_grown'): FLOOR_SIT, ('S289', 'noah_grown'): FLOOR_SIT, ('S290', 'noah_grown'): FLOOR_SIT,
              ('S304', 'noah_grown'): FLOOR_SIT}
HAND_FLASH = dict(rim='#fff2d6', rim_a=120, side=-1, key=0.18)


def _warn(key, msg):
    if key in _ERR: return
    _ERR.add(key)
    print('[film] ' + msg, file=sys.stderr, flush=True)


# ==================================================================================================== camera
def make_cam(sh, idx):
    """Cam from the plan keys. The plan's shake is a handheld amplitude: 2 = breathing tripod, 15-26 = nervous hand.
    Linear pushes are extrapolated 0.5 s past both ends (centred dissolves never freeze); snaps, hits, post push."""
    c = sh['cam']
    ks = [list(map(float, k)) + [0.0] * (5 - len(k)) for k in c['keys']]
    ease_ = {'lin': 'lin', 'out': 'out', 'in_out': 'in_out', 'push': 'push'}.get(c.get('ease', 'lin'), 'lin')
    if ease_ == 'lin' and len(ks) >= 2:
        a, b = ks[0], ks[-1]; dt = max(1e-3, b[0] - a[0]); e = 0.5
        rz = math.log(b[3] / a[3]) / dt
        ks = [[a[0] - e, a[1] - (b[1] - a[1]) / dt * e, a[2] - (b[2] - a[2]) / dt * e, a[3] * math.exp(-rz * e), a[4]]] + ks + \
             [[b[0] + e, b[1] + (b[1] - a[1]) / dt * e, b[2] + (b[2] - a[2]) / dt * e, b[3] * math.exp(rz * e), b[4]]]
    elif len(ks) >= 2:
        ks = ks + [[ks[-1][0] + 0.5] + ks[-1][1:]]
    shake = float(c.get('shake', 2.0) or 0.0)
    if shake >= 8: amp, hz, rs = shake * 0.45, 0.95, 0.22
    else: amp, hz, rs = max(1.6, shake), 0.6, 0.0
    keys = [tuple(k[:5]) + ((ease_,) if j else ()) for j, k in enumerate(ks)]
    cam = Cam(keys, ease=ease_, shake=amp, shake_hz=hz, seed=idx * 3 + 1, roll_shake=rs)
    if c.get('snap'):
        s = c['snap']; cam.snap(float(s[0]), float(s[1]) if len(s) > 1 else 1.25, float(s[2]) if len(s) > 2 else 0.1)
    for h in c.get('hit') or []:
        cam.hit(float(h[0]), float(h[1]) * 0.75, 0.32, 13.0)
    if sh['type'] in ('INSERT', 'UI') or sh['side'] == 'ui':
        cam.post_push(sh['t0'] - 0.5, sh['t1'] + 0.5, 1.0, 1.02 ** (sh['dur'] + 1.0), ease='lin')
    return cam


# ==================================================================================================== built shot
class Built:
    __slots__ = ('sh', 'idx', 'sp', 'layers', 'cam', 'grade', 'focus', 'dof', 'rigs', 'store')

    def fx(self, t):
        return self.sp.fx(t)


def _bg_grade(film, sh):
    """Rule cards: the grade of the neighbouring shot that shows the card's background set."""
    bg = sh.get('bg') or {}
    for d in (-1, 1, -2, 2):
        k = film.index[sh['id']] + d
        if 0 <= k < len(film.shots):
            o = film.shots[k]
            if (o['set'], o['view']) == (bg.get('set'), bg.get('view')) and o['grade'] not in ('rule_card',): return o['grade']
    return ST.DEFAULT_GRADE.get(bg.get('var'), 'cabin_flash')


def _card_chars(film, sh):
    """Cast for a rule card's live background: the neighbouring shot on the same set view, acts dropped (they breathe,
    blink and hold their expression behind the blur)."""
    bg = sh.get('bg') or {}
    for d in (-1, 1, -2, 2):
        k = film.index[sh['id']] + d
        if 0 <= k < len(film.shots):
            o = film.shots[k]
            if (o['set'], o['view']) == (bg.get('set'), bg.get('view')) and o['chars']:
                out = []
                for c in o['chars']:
                    c2 = {kk: v for kk, v in c.items() if kk not in ('acts', 'clip_id')}
                    c2['acts'] = [a for a in (c.get('acts') or []) if a[1] in ('expr', 'flashlight')]
                    out.append(c2)
                return out
    return []


def _char_layer(rig, at, mode, store, sh):
    d = float(at[3]) if (mode in ('body', 'legs', 'silhouette') and isinstance(at, (list, tuple)) and len(at) > 3) else 1.0

    def draw(pen, t):
        try:
            info = rig.draw(pen, t, at=at)
            if store is not None: store['last'] = (t, info)
        except Exception as e:                                  # never kill a render on one bad pose
            _warn((sh['id'], rig.who, type(e).__name__), 'char draw failed %s %s: %r' % (sh['id'], rig.who, e))
    return Layer(d, draw, 'char_' + rig.who, ref_depth=d)


def _hook_beam(sp, rig, at, layer, store):
    """Tess's beam starts at her flashlight when she is in the frame (same depth plane as the beam: no parallax error)."""
    B = sp.info.get('beam')
    if B is None or B.fn is None: return
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


# ==================================================================================================== the film
class Film:
    def __init__(self, tl=None, plan_path=PLAN):
        self.tl = tl if tl is not None else (json.load(open(TIMELINE)) if os.path.exists(TIMELINE) else {'lines': []})
        self.P = json.load(open(plan_path))
        self.shots = self.P['shots']
        self.index = {s['id']: k for k, s in enumerate(self.shots)}
        self._starts = [s['t0'] for s in self.shots]
        self.duration = float(self.P['meta']['duration'])
        self.caps = sorted(self.P['captions'], key=lambda c: c['t0'])
        self._cap0 = [c['t0'] for c in self.caps]
        self.cards = {rc['n']: rc for rc in self.P['rule_cards']}
        self.counter = self.P['counter']
        self._csteps = [s[0] for s in self.counter['steps']]
        self.L = self.tl.get('lines', [])
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
        while len(self._built) > 3: self._built.popitem(last=False)
        return b

    def build(self, k):
        sh = self.shots[k]
        chars = sh['chars'] or EXTRA_CHARS.get(sh['id'], [])
        if sh['set'] == 'rule_mirror' and not chars:
            chars = _card_chars(self, sh)
        s2 = dict(sh, chars=chars) if chars is not sh['chars'] else sh
        if sh['var'] == 'old_cabin':                 # the wet footprints stay: earlier prints of the sequence carry over
            prev = [c for o in self.shots[max(0, k - 8):k] if o['var'] == 'old_cabin'
                    for c in o['sfx'] if c['name'] == 'wet_footstep']
            if prev: s2 = dict(s2, sfx=prev + list(s2['sfx']))
        sp = ST.build_shot(s2)
        B = Built(); B.sh, B.idx, B.sp = sh, k, sp
        layers = list(sp); rigs = []; store = None
        gname = sp.grade if sp.grade not in (None, 'rule_card') else _bg_grade(self, sh)
        try: expo = float(GRADES.get(gname, {}).get('exposure', 0.0))
        except Exception: expo = 0.0
        for spec in chars:
            spec2 = dict(spec)
            try:
                at = ST.resolve_at(sp, spec2)
            except KeyError as e:
                _warn((sh['id'], 'at'), 'anchor %s: %s' % (sh['id'], e)); continue
            spec2['at'] = at
            pa = PATCH_ACTS.get((sh['id'], spec2['who']))
            if pa and spec2.get('mode') == 'body' and len(at) > 2:      # seat on the boards: drop by the shin length
                at = [at[0], at[1] + 0.26 * at[2]] + list(at[2:]); spec2['at'] = at
            if pa: spec2['acts'] = [[sh['t0'] + a_[0] if a_[0] < 0 else a_[0]] + list(a_[1:]) for a_ in pa] + list(spec2.get('acts') or [])
            if spec2.get('mode') in ('hands', 'feet') and not spec2.get('light') and spec2['who'] != 'queen' \
                    and sh['side'] in ('ours', 'mirror') and sh['t0'] < 534.4 \
                    and str(s2['props'].get('flashlight', '')).startswith('tess_on'):
                spec2['light'] = HAND_FLASH          # a hand in the beam is warm skin, not the cool night key (no lilac mittens)
            try:
                rig = CH.CharRig(spec2, s2)
            except Exception as e:
                _warn((sh['id'], spec['who'], 'rig'), 'rig failed %s %s: %r' % (sh['id'], spec['who'], e)); continue
            mode = spec2.get('mode', 'body')
            st_ = {} if (rig.who == 'tess' and mode == 'body') else None
            L_ = _char_layer(rig, at, mode, st_, sh)
            if rig.who != 'queen' and expo > 0.5:    # the night grades lift the dark sets ~1 stop: keep skin from blowing out
                L_.dim = 1.0 - 2.0 ** (-0.6 * expo)
            if sh['view'] == 'phone_screen' and rig.who == 'queen' and sp.info.get('screen') is not None:
                ST.clip_layer(L_, sp.info['screen'])
            if st_ is not None: _hook_beam(sp, rig, at, L_, st_)
            layers.append(L_); rigs.append(rig)
        layers += extra_layers(self, sh, sp)
        B.layers, B.rigs, B.store = layers, rigs, store
        B.cam = make_cam(sh, k)
        g = sp.grade
        if g == 'rule_card' or g is None: g = _bg_grade(self, sh) if sh['set'] == 'rule_mirror' else 'neutral'
        B.grade, B.focus, B.dof = g, sp.focus, sp.dof
        return B

    # ---------------------------------------------------------------- frame
    def fx_at(self, B, t, k):
        fx = B.fx(t)
        sh = B.sh; u = t - sh['t0']
        tr = sh['tr']
        if tr == 'glitch' and u < 2.0 / FPS + 1e-6:
            fx['glitch'] = 0.95; fx['static'] = max(fx.get('static', 0.0), 0.5)
        elif tr == 'white' and u < 3.0 / FPS + 1e-6:
            fx['white'] = max(fx.get('white', 0.0), 0.9 * (1.0 - u / (3.5 / FPS)))
        for e in sh.get('fx_post') or []:
            if e['t'] <= t < e['t'] + e.get('dur', 0.08):
                for key, v in e.items():
                    if key in ('t', 'dur'): continue
                    fx[key] = fx.get(key, 0.0) + v if key == 'exposure' else max(fx.get(key, 0.0), v)
        if t < 0.22: fx['fade'] = max(fx.get('fade', 0.0), 1.0 - t / 0.22)
        return fx

    def _render(self, k, t, i, hud=True):
        B = self.built(k)
        cs = B.cam.at(t)
        fx = self.fx_at(B, t, k)
        hf = (lambda cv, tt: self.hud(cv, tt, B, cs)) if hud else None
        return render_frame(B.layers, cs, t, i, focus=B.focus, dof=B.dof, lens=None, grade=B.grade, post=fx, hud=hf)

    def frame(self, t, i=None):
        if i is None: i = int(round(t * FPS))
        k = self.idx_at(t); sh = self.shots[k]
        other, u = None, None
        if sh['tr'] == 'dissolve' and k > 0 and t < sh['t0'] + DISSOLVE / 2:
            other, u = k - 1, 0.5 + (t - sh['t0']) / DISSOLVE
        elif k + 1 < len(self.shots) and self.shots[k + 1]['tr'] == 'dissolve' and t >= sh['t1'] - DISSOLVE / 2:
            other, u = k + 1, 0.5 - (sh['t1'] - t) / DISSOLVE
        if other is None:
            return self._render(k, t, i)
        # centred dissolve: both pictures (no HUD), blended, then the HUD of the shot under the cut once
        a = self._render(min(k, other), t, i, hud=False)
        b = self._render(max(k, other), t, i, hud=False)
        w = ease_in_out(clamp(u))
        img = cv2.addWeighted(a, 1.0 - w, b, w, 0.0)
        B = self.built(k)
        cs = B.cam.at(t)
        return overlay_hud(img, lambda cv, tt: self.hud(cv, tt, B, cs), t)

    # ---------------------------------------------------------------- HUD
    def caption_at(self, t):
        j = bisect.bisect_right(self._cap0, t) - 1
        if j < 0: return None
        c = self.caps[j]
        return c['text'] if t < c['t1'] else None

    def hud(self, cv, t, B, cs):
        sh = B.sh
        if sh['side'] == 'black': return
        card = None
        for e in sh['hud']:
            if e['type'] == 'rule_card': card = e
        draw_header(cv, sh, t)
        if card is None and sh['side'] != 'card':
            draw_counter(cv, self.counter, self._csteps, sh, t)
        for e in sh['hud']:
            ty = e['type']; u = t - e['t']
            if ty == 'phone': continue
            if u < 0: continue
            if ty == 'tag':
                hold = e.get('hold', 1.2)
                if u <= hold: cmd_tag(cv, e['text'], e.get('x', 960), e.get('y', 120), u, hold, e.get('style', 'cmd'))
            elif ty == 'red_x':
                hold = e.get('hold', 0.8)
                if u <= hold + 0.1: red_x(cv, e.get('x', 960), e.get('y', 600), e.get('r', 160), u, hold)
            elif ty == 'label':
                hold = e.get('hold', 1.0)
                if u <= hold + 0.12: pin_label(cv, e, u, hold, cs, sh)
            elif ty == 'time_card':
                if u <= e.get('hold', 2.6) + 0.25: time_card(cv, e, t)
            elif ty == 'rule_card':
                rule_card(cv, self.cards[e['n']], e, t)
            elif ty == 'like_sub':
                if u <= e.get('hold', 2.0) + 0.2: like_sub(cv, u, e.get('hold', 2.0))
        ph = [e for e in sh['hud'] if e['type'] == 'phone']
        if ph:
            cur = None
            for e in ph:
                if e['t'] <= t + 1e-6 or (cur is None and e['t'] - sh['t0'] < 0.35): cur = e
            if cur is not None: phone_ui(cv, cur, t, sh, self)
        if sh.get('captions', True) and card is None:
            c = self.caption_at(t)
            if c: draw_caption(cv, c)

    # ---------------------------------------------------------------- picture events for the final SFX sync
    def events(self, path=EVENTS, write=True):
        """film_events.json (audio/cues.py --events): actual cut times, the picture's actions as SFX cues (acting clips,
        HUD pops, card writes, counter ticks) matched to the plan's cue ids (retimed when the picture differs by >= 10 ms,
        new cues where the plan has none) and the picture's hit times (camera hits, punch-ins, tags, red X, cards)."""
        SP = json.load(open(SOUND))
        plan = {}; kc = {}
        for c in SP['sfx']:
            key = (c['shot'], c['name']); k = kc.get(key, 0); kc[key] = k + 1
            plan.setdefault(key, []).append(dict(id='%s:%s:%d' % (c['shot'], c['name'], k), t=c['t'], used=False, params=c.get('params') or {}, name=c['name']))
        FAM = {'footsteps_porch': 'footsteps', 'footsteps_gravel': 'footsteps', 'footsteps_wood_inside': 'footsteps',
               'footsteps_run': 'footsteps', 'bare_foot_step': 'footsteps', 'wet_footstep': 'footsteps',
               'cloth_grab': 'cloth', 'towel_cloth': 'cloth', 'jacket_cloth': 'cloth', 'cloth_press': 'cloth',
               'glass_tap': 'glass', 'nail_click_glass': 'glass', 'glass_wipe': 'glass', 'lipstick_smear': 'glass',
               'impact_hit': 'hit', 'stinger': 'hit', 'braam': 'hit', 'sub_drop': 'hit', 'bell_cracked': 'bell',
               'bell_clean': 'bell', 'mattress_creak': 'bed', 'bed_creak': 'bed', 'whoosh': 'whoosh'}
        famidx = {}
        for (sid, name), lst in plan.items():
            famidx.setdefault((sid, FAM.get(name, name)), []).extend(lst)
        out_sfx, hits, actions, drop = [], [], [], []

        def span(c):
            p_ = c['params']
            if p_.get('dur'): return float(p_['dur'])
            return 0.45 * (int(p_.get('n', 1)) - 1) if int(p_.get('n', 1) or 1) > 1 else 0.0

        def drop_walks(sid, evs):
            # a plan walk cue (dur / n steps, rendered with its own step timing) is replaced by the picture's own steps
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
            chars = sh['chars'] if sh['chars'] else []
            rigs_ = []
            for spec in chars:
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
            if sh['tr'] in ('glitch', 'white'): actions.append({'t': sh['t0'], 'shot': sid, 'what': sh['tr'] + ' cut'})
            for e in sh['hud']:
                ty = e['type']
                if ty == 'tag':
                    hits.append(e['t']); actions.append({'t': e['t'], 'shot': sid, 'what': 'tag ' + e['text']})
                    match(sid, 'ui_pop', e['t'], {'gain_db': -4.0, 'space': 'close', 'hit': False})
                elif ty == 'red_x':
                    hits.append(e['t']); actions.append({'t': e['t'], 'shot': sid, 'what': 'red X'})
                    match(sid, 'stinger', e['t'], {'gain_db': -3.0, 'space': None, 'hit': True})
                elif ty == 'label':
                    actions.append({'t': e['t'], 'shot': sid, 'what': 'label ' + e['text']})
                    match(sid, 'ui_pop', e['t'], {'gain_db': -10.0, 'space': 'close', 'hit': False})
                elif ty == 'time_card':
                    actions.append({'t': e['t'], 'shot': sid, 'what': 'time card'})
                    match(sid, 'ui_pop', e['t'], {'gain_db': -8.0, 'space': 'close', 'hit': False})
                    match(sid, 'clock_tick', e.get('flip_at', e['t'] + 0.24), {'gain_db': -6.0, 'space': 'close', 'hit': False})
                elif ty == 'rule_card':
                    rc = self.cards[e['n']]
                    hits.append(rc['appear'])
                    actions.append({'t': rc['appear'], 'shot': sid, 'what': 'rule card %d in' % e['n']})
                    match(sid, 'glitch', rc['appear'], {'gain_db': -4.0, 'space': None, 'hit': False, 'params': {'dur': 0.05}})
                    match(sid, 'lipstick_draw', rc['title_at'], {'gain_db': -4.0, 'space': 'close', 'hit': False})
                    for w_, tw in e.get('words') or []:
                        actions.append({'t': tw, 'shot': sid, 'what': 'card word ' + w_})
                    match(sid, 'glass_wipe', rc['sentence_end'], {'gain_db': -6.0, 'space': 'close', 'hit': False,
                                                                  'params': {'dur': round(rc['cut'] - rc['sentence_end'] + 0.2, 2)}})
                elif ty == 'like_sub':
                    match(sid, 'ui_pop', e['t'] + 0.9, {'gain_db': -10.0, 'space': 'close', 'hit': False})
                elif ty == 'phone':
                    actions.append({'t': e['t'], 'shot': sid, 'what': 'phone ' + e['state']})
                    if e['state'] == 'message':
                        for bb in e.get('bubbles', []):
                            match(sid, 'phone_message', bb['t'], {'gain_db': -6.0, 'space': 'close', 'hit': False})
                    elif e['state'] == 'connected' and abs(e['t'] - e.get('timer_from', -1)) < 0.05:
                        match(sid, 'phone_pickup', e['t'], {'gain_db': -4.0, 'space': 'close', 'hit': False})
                elif ty in ('counter_in', 'counter_call'):
                    hits.append(e['t']) if ty == 'counter_call' else None
        for (tc, v, kind) in self.counter['steps']:
            sh = self.shot_at(tc); sid = sh['id']
            actions.append({'t': tc, 'shot': sid, 'what': 'countdown %d (%s)' % (v, kind)})
            match(sid, 'countdown_tick', tc, {'gain_db': -14.0 if kind == 'step' else -8.0, 'space': 'close', 'hit': False})
        hits = sorted(set(round(h, 3) for h in hits))
        out = {'version': 1, 'duration': self.duration,
               'shots': [{'id': s['id'], 't0': s['t0'], 't1': s['t1']} for s in self.shots],
               'sfx': sorted(out_sfx, key=lambda e: e['t']), 'drop': sorted(set(drop)), 'music': [], 'hits': hits,
               'actions': sorted(actions, key=lambda a: a['t'])}
        if write:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            json.dump(out, open(path, 'w'), indent=0)
        return out


# ==================================================================================================== extra picture layers
def extra_layers(film, sh, sp):
    """Small live layers the plan asks for that neither the set nor the cast draws."""
    L = []
    if sh['id'] == 'S070':                           # a red glint crawling down the queen's dress
        q = [c for c in sh['chars'] if c['who'] == 'queen']
        if q and isinstance(q[0].get('at'), (list, tuple)) or (q and q[0].get('at') in sp.anchors):
            at = ST.resolve_at(sp, q[0])
            x, y, hgt = float(at[0]), float(at[1]), float(at[2])
            d = float(at[3]) if len(at) > 3 else 1.0

            def glint(pen, t):
                u = ((t - sh['t0']) / 1.8) % 1.0
                gy = y - hgt * (0.80 - 0.72 * u); gx = x - hgt * 0.06 + hgt * 0.025 * math.sin(u * 7.0)
                pen.radial(None, gx, gy, hgt * 0.022, [(0, '#ff4060', 120), (1, '#ff4060', 0)], sy=2.4, blend='add', clip=False)
                pen.fill(oval(gx, gy, hgt * 0.0025, hgt * 0.009), '#ffd0d6', 210)
            L.append(Layer(d * 0.99, glint, 'dress_glint', blur=0, ref_depth=d * 0.99))
    return L


def overlay_hud(img, fn, t):
    o4 = cv2.cvtColor(img, cv2.COLOR_RGB2BGRA)
    s = surface_for(o4); cv = s.getCanvas()
    cv.scale(CFG.rw / DW, CFG.rw / DW)
    fn(cv, t)
    del cv, s
    return cv2.cvtColor(o4, cv2.COLOR_BGRA2RGB)


# ==================================================================================================== captions + header
_MF = {}


def _blur(r):
    if r not in _MF: _MF[r] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r)
    return _MF[r]


def draw_caption(cv, s):
    """REF_MIRROR: white bold uppercase, letter-spaced, one line centred on y 0.893 H, cap height 2.1 % H, soft halo."""
    s = s.upper()
    size, sp = 33, 0.045
    w = text_width(s, 700, size, sp)
    if w > 1500:
        size = 33 * 1500 / w; w = 1500
    yb = 976
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(DW / 2 - w / 2 - 30, yb - 36, w + 60, 50), 24, 24),
                 skia.Paint(Color=skia.Color4f(0, 0, 0, 0.55).toColor(), AntiAlias=True, MaskFilter=_blur(18.0)))
    text(cv, s, DW / 2, yb, 700, size, '#ffffff', 255, sp, 'center', 1.0)


def _tc(sec, frac_fps=30):
    sec = sec % 86400.0
    hh, mm, ss = int(sec // 3600), int(sec // 60) % 60, int(sec) % 60
    ff = int((sec - math.floor(sec)) * frac_fps) % frac_fps
    return '%02d:%02d:%02d:%02d' % (hh, mm, ss, ff)


def draw_header(cv, sh, t):
    hd = sh.get('header') or {}
    left = hd.get('left') or ''
    size, y, sp = 15.5, 61, 0.22
    if '//' in left:
        a_, b_ = left.split('//', 1)
        w = text(cv, a_.rstrip() + '  //  ', 44, y, 600, size, '#ffffff', 255 * 0.20, sp, 'left')
        text(cv, b_.strip(), 44 + w + sp * size, y, 700, size, '#ffffff', 255 * 0.36, sp, 'left')
    else:
        text(cv, left, 44, y, 600, size, '#ffffff', 255 * 0.2, sp, 'left')
    mode = hd.get('clock_mode', 'hidden')
    if mode == 'hidden' or t < 19.1: return
    a, dx, c = 0.22, 0.0, '#ffffff'
    if mode == 'ours':
        s = _tc(ST.clock_ours(t))
        if 278.97 <= t < 281.81:                       # the clock runs backward: flicker, jitter, a red cast
            a = 0.22 + 0.45 * (hash01(int(t * 30), 5) > 0.55); dx = 6.0 * (hash01(int(t * 30), 6) - 0.5); c = '#ff9aa4'
    elif mode == 'theirs':
        sec = 6 * 3600 + ST.clock_theirs(t)
        s = _tc(sec)
        ph = (t - 297.59) % 19.48
        if ph < 2.0 / FPS + 1e-4 and t > 297.6:        # the 2-frame snap back to :40
            a, dx = 0.6, 9.0
    elif mode == 'stuck':
        s = '07:00:00:00'
        a = 0.22 + 0.06 * math.sin(t * 9.0)
    elif mode == 'memory':
        s = '14 YEARS AGO'
    else:
        return
    text(cv, s, DW - 44 + dx, y, 600, size, c, 255 * a, sp, 'right')


# ==================================================================================================== Tess's countdown
def draw_counter(cv, C, steps_t, sh, t):
    v0, v1 = C['visible']
    if not (v0 <= t < v1 + 0.6): return
    j = bisect.bisect_right(steps_t, t) - 1
    if j < 0: return
    ts, val, kind = C['steps'][j]
    dim = 0.6 if sh['side'] == 'memory' else 1.0
    a_in = ease_out_cubic(clamp((t - v0) / 0.25))
    a_out = 1.0 - clamp((t - v1) / 0.5)
    a = 255 * dim * a_in * a_out
    if a <= 1: return
    u = t - ts
    sc = 1.0
    flash = 0.0
    if kind in ('call', 'zero'):
        sc = 1.0 + 0.35 * (1.0 - ease_out_cubic(clamp(u / 0.25))) if u < 0.25 else 1.0
        flash = 1.0 - clamp(u / 0.35)
    else:
        sc = 1.0 + 0.12 * (1.0 - clamp(u / 0.12))
    if kind == 'zero': flash = max(flash, 0.55 + 0.45 * math.sin(u * 18.0) if u < 0.6 else 0.6)
    pen = Pen(cv)
    cx, cy = 1760, 122
    cv.save(); cv.translate(cx, cy); cv.scale(sc * (0.85 + 0.15 * a_in), sc * (0.85 + 0.15 * a_in))
    box = rrect(-74, -48, 148, 96, 20)
    pen.shadow(box, 0, 6, 16, '#000000', a * 0.45)
    pen.fill(box, '#0b1822', a * 0.8)
    if flash > 0: pen.line(box, 10, RED, a * 0.45 * flash, blur=10)
    pen.line(box, 2.2, RED, a * (0.75 + 0.25 * flash))
    text(cv, 'TESS', 0, -20, 700, 14, '#ffffff', a * 0.35, 0.3, 'center')
    nc = mix('#ffffff', '#ff4b55', clamp(flash)) if kind != 'zero' else '#ff3b46'
    text(cv, '%d' % val, 0, 33, 800, 46, nc, a, 0.02, 'center', 0.0,
         glow=(RED, 160 * flash, 12) if flash > 0 else None)
    cv.restore()


# ==================================================================================================== tags, red X, labels
def cmd_tag(cv, s, x, y, u, hold, style='cmd'):
    """Command tag: red bold text in a near-black box with a red outline and glow; pops over 4 frames with an overshoot
    and lands on the word; out in 3 frames."""
    pen = Pen(cv)
    k_in = clamp(u / (4.0 / FPS))
    sc = 1.0 + 0.32 * (1.0 - ease_out_back(clamp(u / 0.12), 2.4)) if u < 0.12 else 1.0
    a = 255 * min(k_in, clamp((hold - u) / (3.0 / FPS) + 0.0))
    if a <= 0: return
    size, sp = 46, 0.085
    tw = text_width(s, 800, size, sp)
    bw, bh = tw + 64, 78
    white = style == 'white'
    edge = '#f2f2f2' if white else RED
    tc = '#f4f4f4' if white else '#ff3a44'
    cv.save(); cv.translate(x, y); cv.scale(sc, sc); cv.rotate(-1.2 if not white else 0.0)
    box = rrect(-bw / 2, -bh / 2, bw, bh, 8)
    pen.shadow(box, 0, 8, 18, '#000000', a * 0.6)
    pen.fill(box, '#0a090c', a * 0.92)
    pen.line(box, 12, edge, a * 0.35, blur=12)
    pen.line(box, 3.5, edge, a)
    text(cv, s, 0, size * 0.36, 800, size, tc, a, sp, 'center', 0.0, glow=(edge, 150, 14))
    cv.restore()


def red_x(cv, x, y, r, u, hold):
    pen = Pen(cv)
    if u < 1.5 / FPS:
        pen.fill(rect(-50, -50, DW + 100, DH + 100), '#ff1020', 60)
    out = 1.0 - clamp((u - hold) / 0.1)
    a = 255 * out
    if a <= 0: return
    kr = ease_out_cubic(clamp(u / 0.09))
    ring = skia.Path(); ring.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), -90, 360 * kr)
    pen.line(ring, 26, '#ff1a28', a * 0.3, blur=14)
    pen.line(ring, 11, '#e3262e', a)
    k1 = ease_out_cubic(clamp((u - 0.03) / 0.085)); k2 = ease_out_cubic(clamp((u - 0.1) / 0.085))
    d = r * 0.62
    for (k, (ax, ay, bx, by)) in ((k1, (x - d, y - d, x + d, y + d)), (k2, (x + d, y - d, x - d, y + d))):
        if k <= 0: continue
        ex, ey = lerp(ax, bx, k), lerp(ay, by, k)
        pen.seg((ax, ay), (ex, ey), 30, '#ff1a28', a * 0.3)
        pen.seg((ax, ay), (ex, ey), 15, '#e3262e', a)


def pin_label(cv, e, u, hold, cs, sh):
    px, py = e['pin']
    try:
        X, Y = project(px, py, float(e.get('d', 1.0)), cs)
        X, Y = float(X), float(Y)
    except Exception:
        X, Y = px, py
    tx, ty = clamp(X + e.get('dx', 0), 170, DW - 170), clamp(Y + e.get('dy', 0), 130, 880)
    out = 1.0 - clamp((u - hold) / 0.12)
    k = ease_out_cubic(clamp(u / 0.15))
    pen = Pen(cv)
    a = 255 * out
    pen.seg((X, Y), (X + (tx - X) * k, Y + (ty - Y) * k), 3.0, '#ffffff', a * 0.9)
    pen.fill(oval(X, Y, 7), '#ffffff', a)
    pen.line(oval(X, Y, 14 + 6 * math.sin(u * 8.0)), 2.5, '#ffffff', a * 0.55 * k)
    if u > 0.08:
        H.tag(cv, e['text'], tx, ty, 'white', u - 0.08, alpha=a, size=24)


# ==================================================================================================== time card, like / sub
def time_card(cv, e, t):
    u = t - e['t']; hold = e.get('hold', 2.6)
    a = 255 * ease_out_cubic(clamp(u / 0.2)) * (1.0 - clamp((u - hold) / 0.25))
    if a <= 0: return
    pen = Pen(cv)
    x0, y0 = e.get('x', 110) - 60 * (1 - ease_out_cubic(clamp(u / 0.25))), e.get('y', 170)
    w, h = 560, 176
    box = rrect(x0, y0, w, h, 14)
    pen.shadow(box, 0, 10, 24, '#000000', a * 0.5)
    pen.fill(box, '#0b1822', a * 0.82)
    pen.line(box, 2, '#3a5068', a * 0.9)
    # clock icon with a running second hand
    cx, cy, r = x0 + 72, y0 + 88, 42
    pen.line(oval(cx, cy, r), 4, '#e9eef5', a)
    for k in range(12):
        an = k * math.pi / 6; pen.seg((cx + math.cos(an) * r * 0.8, cy + math.sin(an) * r * 0.8), (cx + math.cos(an) * r * 0.92, cy + math.sin(an) * r * 0.92), 2.5, '#e9eef5', a * 0.8)
    mm = (57 + clamp((t - e.get('flip_at', e['t'])) * 50)) if t >= e.get('flip_at', e['t']) else 56
    ah = math.radians(-90 + (11 + mm / 60.0) * 30); am = math.radians(-90 + mm * 6)
    asec = math.radians(-90 + (t * 6.0 % 60) * 6)
    pen.seg((cx, cy), (cx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5), 5, '#e9eef5', a)
    pen.seg((cx, cy), (cx + math.cos(am) * r * 0.74, cy + math.sin(am) * r * 0.74), 3.5, '#e9eef5', a)
    pen.seg((cx, cy), (cx + math.cos(asec) * r * 0.8, cy + math.sin(asec) * r * 0.8), 2, RED, a)
    text(cv, e.get('day', 'FRIDAY'), x0 + 140, y0 + 48, 700, 17, '#9fb6d6', a, 0.3, 'left')
    # big time; the minute flips 56 -> 57 at flip_at
    fa = e.get('flip_at', e['t'] + 0.24)
    base = e.get('time', '11:57 PM')
    hhmm, ampm = base.split(' ') if ' ' in base else (base, '')
    pre, last = hhmm[:-1], hhmm[-1]
    prev_last = str((int(last) - 1) % 10) if last.isdigit() else last
    wx = text(cv, pre, x0 + 140, y0 + 120, 800, 66, '#ffffff', a, 0.02, 'left')
    fx_ = x0 + 140 + wx + 66 * 0.02
    fl = clamp((t - fa) / 0.14)
    if fl <= 0:
        text(cv, prev_last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
    elif fl < 1:
        cv.save(); cv.translate(0, y0 + 98); cv.scale(1, abs(math.cos(fl * math.pi))); cv.translate(0, -(y0 + 98))
        text(cv, prev_last if fl < 0.5 else last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
        cv.restore()
    else:
        text(cv, last, fx_, y0 + 120, 800, 66, '#ffffff', a, 0.0, 'left')
    lw = text_width(last, 800, 66, 0.0)
    text(cv, ampm, fx_ + lw + 14, y0 + 120, 700, 30, '#c9d6e6', a, 0.06, 'left')
    text(cv, e.get('sub', ''), x0 + 140, y0 + 152, 600, 14.5, '#9fb6d6', a * 0.9, 0.2, 'left')


def like_sub(cv, u, hold):
    pen = Pen(cv)
    a = 255 * ease_out_cubic(clamp(u / 0.2)) * (1.0 - clamp((u - hold) / 0.2))
    if a <= 0: return
    x0, y0 = 70 - 40 * (1 - ease_out_cubic(clamp(u / 0.25))), 955
    lb = rrect(x0, y0, 170, 58, 29)
    pen.shadow(lb, 0, 6, 12, '#000000', a * 0.5); pen.fill(lb, '#f4f4f2', a)
    thumb = smooth([(x0 + 30, y0 + 44), (x0 + 30, y0 + 26), (x0 + 40, y0 + 24), (x0 + 47, y0 + 12), (x0 + 53, y0 + 14),
                    (x0 + 51, y0 + 26), (x0 + 62, y0 + 26), (x0 + 63, y0 + 44)], True, 0.5)
    liked = u > 0.75
    pen.fill(thumb, '#1f6fe0' if liked else '#2a2b30', a)
    text(cv, 'LIKE', x0 + 78, y0 + 37, 800, 22, '#16171c', a, 0.08, 'left')
    sx = x0 + 186
    sb = rrect(sx, y0, 236, 58, 29)
    subd = u > 1.15
    pen.shadow(sb, 0, 6, 12, '#000000', a * 0.5)
    pen.fill(sb, '#3a3b40' if subd else '#d3222a', a)
    text(cv, 'SUBSCRIBED' if subd else 'SUBSCRIBE', sx + 118, y0 + 37, 800, 21, '#ffffff', a, 0.08, 'center')
    # pointer: to LIKE, click, to SUBSCRIBE, click
    pts = [(0.0, x0 + 300, y0 + 120), (0.6, x0 + 52, y0 + 36), (0.85, x0 + 52, y0 + 36), (1.05, sx + 120, y0 + 36), (9, sx + 120, y0 + 36)]
    for i in range(len(pts) - 1):
        if pts[i][0] <= u < pts[i + 1][0]:
            k = ease_in_out((u - pts[i][0]) / (pts[i + 1][0] - pts[i][0]))
            px, py = lerp(pts[i][1], pts[i + 1][1], k), lerp(pts[i][2], pts[i + 1][2], k); break
    else:
        px, py = pts[-1][1], pts[-1][2]
    for tc in (0.72, 1.12):
        if 0 <= u - tc < 0.25:
            pen.line(oval(px, py, 14 + 60 * (u - tc)), 3, '#ffffff', a * (1 - (u - tc) / 0.25))
    arrow = poly([(px, py), (px, py + 34), (px + 9, py + 26), (px + 16, py + 40), (px + 22, py + 37), (px + 15, py + 23), (px + 26, py + 23)])
    pen.fill(arrow, '#ffffff', a); pen.line(arrow, 2.5, '#16171c', a)


# ==================================================================================================== phone UI
def _phone_body(pen, W_, Hh, a):
    body = rrect(-W_ / 2, -Hh / 2, W_, Hh, 46)
    pen.radial(None, 0, 24, W_ * 0.95, [(0, '#000000', 170 * a / 255), (0.6, '#000000', 90 * a / 255), (1, '#000000', 0)],
               sy=Hh * 0.62 / (W_ * 0.95), clip=False)
    pen.fill(body, '#15161b', a); pen.line(body, 6, LINE, a)
    scr = rrect(-W_ / 2 + 12, -Hh / 2 + 12, W_ - 24, Hh - 24, 36)
    return scr


def _status(cv, pen, W_, Hh, a, t):
    sec = ST.clock_ours(t) % 86400.0
    hh, mm = int(sec // 3600), int(sec // 60) % 60
    text(cv, '%d:%02d' % ((hh % 12) or 12, mm), -W_ / 2 + 44, -Hh / 2 + 44, 700, 13, '#e9edf7', a, 0.02, 'left')
    for k in range(4):
        hh_ = 4 + k * 2.6
        pen.fill(rrect(W_ / 2 - 84 + k * 6, -Hh / 2 + 44 - hh_, 4, hh_, 1.2), '#e9edf7', a * (0.95 if k < 2 else 0.35))
    pen.line(rrect(W_ / 2 - 52, -Hh / 2 + 34, 22, 11, 3), 1.5, '#e9edf7', a)
    pen.fill(rrect(W_ / 2 - 50, -Hh / 2 + 36, 6, 7, 1.5), RED, a)


def _bubble(cv, pen, txt, x, y, maxw, a, sc=1.0, incoming=True):
    lines = wrap_text(txt, 600, 16, maxw - 28, 0.0)
    lh = 21
    bw = max(text_width(l, 600, 16, 0.0) for l in lines) + 28
    bh = lh * len(lines) + 18
    cv.save(); cv.translate(x, y + bh); cv.scale(sc, sc); cv.translate(-x, -(y + bh))
    box = rrect(x, y, bw, bh, 16)
    pen.fill(box, '#2b3245' if incoming else '#2f6fe0', a)
    for i, l in enumerate(lines):
        text(cv, l, x + 14, y + 25 + i * lh, 600, 16, '#eef2fb', a, 0.0, 'left')
    cv.restore()
    return bh


def phone_ui(cv, ev, t, sh, film):
    st = ev['state']; u = t - ev['t']
    pen = Pen(cv); a = 255
    W_, Hh = 300.0, 600.0
    x, y, sc = ev.get('x', 960), ev.get('y', 560), ev.get('scale', 1.0) * 1.22
    # the phone is held: it grows with the shot's push and floats with the hand
    k = 1.015 ** max(0.0, t - sh['t0'])
    seed = int(sh['id'][1:])
    ox = 7.0 * noise1(t * 0.9, seed * 5 + 1) + 2.0 * noise1(t * 3.3, seed * 5 + 2)
    oy = 6.0 * noise1(t * 0.8, seed * 5 + 3) + 2.0 * noise1(t * 2.9, seed * 5 + 4)
    rot = 1.1 * noise1(t * 0.6, seed * 5 + 5)
    cv.save(); cv.translate(x + ox, y + oy); cv.rotate(rot); cv.scale(sc * k, sc * k)
    H._hand(pen, W_, Hh, '#c9aa98', a, False)
    scr = _phone_body(pen, W_, Hh, a)
    top, bot = {'voicemail': ('#14161f', '#0b0c12'), 'voicemail_list': ('#14161f', '#0b0c12'),
                'message': ('#10141f', '#0a0c12')}.get(st, ('#121a2e', '#0a0d16'))
    pen.linear(scr, 0, -Hh / 2, 0, Hh / 2, [top, bot], a / 255)
    pen.fill(rrect(-38, -Hh / 2 + 24, 76, 20, 10), '#050506', a)
    cv.save(); cv.clipPath(scr, skia.ClipOp.kIntersect, True)
    _status(cv, pen, W_, Hh, a, t)

    def T(s, yy, size, c='#ffffff', w=800, sp=0.02, aa=1.0, al='center', xx=0.0):
        text(cv, s, xx, yy, w, size, c, a * aa, sp, al, 0.0)

    if st == 'message':
        pen.fill(rect(-W_ / 2, -Hh / 2 + 56, W_, 70), '#161b29', a)
        pen.seg((-W_ / 2, -Hh / 2 + 126), (W_ / 2, -Hh / 2 + 126), 1.2, '#2a3248', a)
        T('<', -Hh / 2 + 100, 26, '#6f95ff', 600, 0.0, 1.0, 'left', -W_ / 2 + 22)
        pen.fill(oval(-38, -Hh / 2 + 92, 19), '#3a4466', a)
        T('M', -Hh / 2 + 99, 18, '#d6dcf0', 800, 0.0, 1.0, 'center', -38)
        T(ev.get('name', 'MOM'), -Hh / 2 + 99, 20, '#ffffff', 800, 0.06, 1.0, 'left', -8)
        T('TODAY 11:57 PM', -Hh / 2 + 152, 10.5, '#7f8aa6', 700, 0.2)
        # bubbles stack from the bottom; each new one pushes the rest up
        items = []
        for b in ev.get('bubbles', []):
            if b.get('typing_from') is not None and b['typing_from'] <= t < b['t']:
                items.append(('typing', None, b['typing_from']))
            if t >= b['t']: items.append(('msg', b['text'], b['t']))
        ybot = Hh / 2 - 74
        hs = []
        for kind, txt, tb in items:
            hb = 40 if kind == 'typing' else (21 * len(wrap_text(txt, 600, 16, 196 - 28, 0.0)) + 18)
            hs.append(hb)
        yy = ybot
        for (kind, txt, tb), hb in reversed(list(zip(items, hs))):
            ua = t - tb
            slide = 1.0 - ease_out_cubic(clamp(ua / 0.2))
            yy -= hb + 10
            sc_b = 0.85 + 0.15 * ease_out_back(clamp(ua / 0.18), 2.0)
            if kind == 'typing':
                box = rrect(-W_ / 2 + 22, yy + slide * 30, 70, 40, 18); pen.fill(box, '#2b3245', a)
                for j in range(3):
                    ph = 0.5 + 0.5 * math.sin(t * 9.0 - j * 0.9)
                    pen.fill(oval(-W_ / 2 + 41 + j * 16, yy + slide * 30 + 20 - 3 * ph, 4.5), '#c9d0e4', a * (0.45 + 0.55 * ph))
            else:
                _bubble(cv, pen, txt, -W_ / 2 + 22, yy + slide * 30, 196, a * clamp(ua / 0.08), sc_b)
        pen.fill(rrect(-W_ / 2 + 18, Hh / 2 - 60, W_ - 36, 34, 17), '#1b2131', a)
        T('Message', Hh / 2 - 37, 13, '#5d6782', 600, 0.02, 1.0, 'left', -W_ / 2 + 36)
    elif st == 'voicemail_list':
        T('VOICEMAIL', -Hh / 2 + 96, 13, '#9aa3b8', 700, 0.24)
        slide = 30 * (1.0 - ease_out_cubic(clamp(u / 0.5))) - 8.0 * clamp(u / 2.0)
        for j, it in enumerate(ev.get('items', [])):
            ry = -Hh / 2 + 130 + j * 64 + slide
            hl = j == 0
            if hl:
                pulse = 0.5 + 0.5 * math.sin(u * 5.0)
                pen.fill(rrect(-W_ / 2 + 16, ry, W_ - 32, 56, 10), '#232a3d', a * (0.7 + 0.3 * pulse))
                pen.fill(oval(-W_ / 2 + 30, ry + 28, 5), '#3d7bff', a)
            parts = [p.strip() for p in it.split('·')]
            T(parts[0], ry + 26, 17, '#ffffff' if hl else '#c5cbe0', 800, 0.04, 1.0, 'left', -W_ / 2 + 44)
            T('  '.join(parts[1:]), ry + 46, 11.5, '#8f9ab5', 600, 0.08, 1.0, 'left', -W_ / 2 + 44)
            pen.seg((-W_ / 2 + 44, ry + 60), (W_ / 2 - 16, ry + 60), 1.0, '#2a3248', a)
        tap = sh['t1'] - 0.45
        if 0 <= t - tap < 0.35:
            q = (t - tap) / 0.35
            pen.fill(oval(0, -Hh / 2 + 158 + slide, 16 + 50 * q), '#ffffff', a * 0.3 * (1 - q))
    elif st == 'voicemail':
        T('VOICEMAIL', -Hh / 2 + 96, 13, '#9aa3b8', 700, 0.24)
        T(ev.get('name', 'NOAH'), -Hh / 2 + 146, 34)
        T('JUL 18  ·  14 YEARS AGO', -Hh / 2 + 172, 11.5, '#8f9ab5', 700, 0.16)
        dur = 9.0
        t0s = 3.0
        tm = ev.get('timer')
        if tm and ':' in tm: t0s = int(tm.split(':')[0]) * 60 + int(tm.split(':')[1])
        pos = clamp((t0s + u) / dur)
        T('0:%02d' % int(pos * dur), -Hh / 2 + 212, 20, RED, 800, 0.04)
        H.waveform(cv, -112, 10, 224, 104, 0.0, '#e0444c', ev.get('waveform', {}).get('seed', 13), pos, False, a, 3.0, 2.2, dim='#5a5e6e')
        pen.seg((-112, 104), (112, 104), 4, '#3a3e4c', a)
        pen.seg((-112, 104), (-112 + 224 * pos, 104), 4, '#f2f2f2', a)
        pen.fill(oval(-112 + 224 * pos, 104, 8), '#ffffff', a)
        H._button(pen, 0, Hh / 2 - 100, 36, '#f2f2f2', a, 'pause')
    else:   # calling / connected
        T('CALLING' if st == 'calling' else 'CONNECTED', -Hh / 2 + 92, 13, '#9aa3b8', 700, 0.22)
        T(ev.get('name', 'MOM'), -Hh / 2 + 146, 40)
        av = (0, -40)
        if st == 'calling':
            for j in range(3):
                ph = (u * 0.8 + j / 3.0) % 1.0
                pen.line(oval(av[0], av[1], 62 + ph * 70), 2.2, '#8fb0ff', a * (1 - ph) * 0.6)
        pen.fill(oval(av[0], av[1], 62), '#2a3350', a)
        T('M', av[1] + 18, 52, '#d6dcf0', 800)
        if st == 'calling':
            T('calling' + '.' * (1 + int(u * 2.5) % 3), 92, 19, '#c5cbe0', 600, 0.02)
        else:
            clk = max(0.0, t - ev.get('timer_from', ev['t']))
            T('%02d:%02d' % (int(clk) // 60, int(clk) % 60), 92, 22, '#c5cbe0', 600, 0.06)
            _call_wave(cv, pen, ev.get('waveform') or {}, t, film, a)
        H._button(pen, 0, Hh / 2 - 92, 36, '#e0343b', a, 'end')
    cv.restore()
    pen.radial(scr, -W_ * 0.3, -Hh * 0.45, Hh * 0.9, [(0, '#ffffff', 16), (1, '#ffffff', 0)], a / 255)
    H._hand(pen, W_, Hh, '#c9aa98', a, True)
    cv.restore()


def _call_wave(cv, pen, wv, t, film, a):
    x0, y0, w, h = -100.0, 140.0, 200.0, 46.0
    n = 36; bar = w / n * 0.6
    if wv.get('flat'):
        pen.seg((x0, y0), (x0 + w, y0), 2.5, '#6f95ff', a * 0.8)
        return
    env = CH.voice_envelope()
    amps = []
    for j in range(n):
        tj = t - (n - 1 - j) * 0.035
        if env is not None and wv.get('follow_line') is not None:
            v = float(env[min(len(env) - 1, max(0, int(tj * 100)))]); amp = clamp((v + 52.0) / 34.0)
        else:
            amp = 0.15 + 0.5 * abs(noise1(tj * 6.0, 3)) * (0.6 + 0.4 * noise1(tj * 1.3, 4))
        sa = wv.get('spike_at')
        if sa is not None:
            amp = 0.08 + 0.06 * abs(noise1(tj * 9.0, 5))
            if 0 <= tj - sa < 0.35: amp = 1.0 - (tj - sa) / 0.35 * 0.6
        amps.append(amp)
    p = skia.Path()
    for j, amp in enumerate(amps):
        bx = x0 + j * w / n; hh = max(2.0, amp * h / 2)
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, y0 - hh, bar, hh * 2), bar / 2, bar / 2))
    pen.fill(p, '#6f95ff', a)


# ==================================================================================================== rule card: lipstick on glass
def _tokens(s):
    out, red = [], False
    for part in s.split('*'):
        for w in part.split():
            if out and all(ch in '.,!?;:' for ch in w):
                out[-1][0] += w
            else:
                out.append([w, red])
        red = not red
    return out


def _lip_text(cv, s, x, y, size, a, weight=900, sp=0.04, align='left', glow=1.0):
    """Waxy lipstick lettering: a dark wax edge, the colour, a cool highlight and the widest red glow."""
    if glow > 0: text(cv, s, x, y, weight, size, LIP_GLOW, a * 0.22 * glow, sp, align, 0.0, glow=(LIP_GLOW, 120 * glow, size * 0.22))
    text(cv, s, x + size * 0.025, y + size * 0.035, weight, size, LIP_DK, a * 0.95, sp, align)
    text(cv, s, x, y, weight, size, LIPSTICK, a, sp, align)
    cv.save(); cv.clipRect(skia.Rect.MakeLTRB(-4000, y - size * 0.75, 4000, y - size * 0.52))
    text(cv, s, x - size * 0.01, y - size * 0.012, weight, size, LIP_HI, a * 0.55, sp, align)
    cv.restore()


_SPR = {}
_LINS = skia.SamplingOptions(skia.FilterMode.kLinear)


def sprite(key, box, draw, dens=1.0):
    """Draw once at the render density into an image over the design box (x0, y0, x1, y1); reused every frame (the rule
    card's glass, lipstick letters and words carry blurred glows that cost ~0.4 s per frame at 2560 when redrawn)."""
    kk = (key, CFG.rw)
    e = _SPR.get(kk)
    if e is None:
        if len(_SPR) > 160: _SPR.clear()
        k = CFG.rw / DW * dens
        x0, y0, x1, y1 = box
        w, h = max(1, int(math.ceil((x1 - x0) * k))), max(1, int(math.ceil((y1 - y0) * k)))
        arr = np.zeros((h, w, 4), np.uint8); sf = surface_for(arr); c = sf.getCanvas()
        c.scale(w / (x1 - x0), h / (y1 - y0)); c.translate(-x0, -y0); draw(c)
        del c, sf
        from engine.core import image_from
        e = (image_from(arr), box, arr, w, h); _SPR[kk] = e
    return e


def blit(cv, e, alpha=255.0):
    img, (x0, y0, x1, y1), _, w, h = e
    p = skia.Paint(); p.setAlphaf(clamp(alpha / 255.0))
    cv.drawImageRect(img, skia.Rect.MakeWH(w, h), skia.Rect.MakeLTRB(x0, y0, x1, y1), _LINS, p, skia.Canvas.kFast_SrcRectConstraint)


CARD_W, CARD_H = 1140.0, 640.0


def _card_static(c, n):
    """The pane without anything that moves: shadow, flashlight-lit silver glass, streaks, desilvering, breath fog, the
    7-step marker and the story mirror's white chipped frame (pane-local coordinates, centre 0, 0)."""
    pen = Pen(c)
    W_, Hh = CARD_W, CARD_H
    x0, y0, x1, y1 = -W_ / 2, -Hh / 2, W_ / 2, Hh / 2
    pane = rect(x0, y0, W_, Hh)
    pen.shadow(rrect(x0 - 30, y0 - 30, W_ + 60, Hh + 60, 6), 0, 22, 46, '#000000', 190)
    pen.linear(pane, x0, y0, x1, y1, [(0, '#e4e7eb'), (0.45, '#cfd4da'), (1, '#8f99a4')])
    pen.radial(pane, 0, 0, 760, [(0, '#5a636e', 0), (0.62, '#5a636e', 0), (1, '#3e4650', 150)], sy=0.62)
    c.save(); c.clipPath(pane, skia.ClipOp.kIntersect, True)
    for j, (sx_, w_) in enumerate(((-380, 90), (-250, 34), (300, 60))):
        band = poly([(sx_ + 140, y0 - 20), (sx_ + 140 + w_, y0 - 20), (sx_ - 260 + w_, y1 + 20), (sx_ - 260, y1 + 20)])
        pen.fill(band, '#ffffff', 26 if j != 1 else 18)
    for j in range(46):
        cxj = x0 + (hash01(j, 11) ** 2.2) * 200 if j % 2 else x1 - (hash01(j, 12) ** 2.2) * 200
        cyj = y0 + hash01(j, 13) * Hh
        pen.fill(oval(cxj, cyj, 2 + 9 * hash01(j, 14), 2 + 6 * hash01(j, 15)), '#4a525c', 60 + 70 * hash01(j, 16))
    for j in range(7):                                          # breath fog behind the words
        fx, fy = -380 + j * 128 + 30 * math.sin(j * 1.7), 70 + 40 * math.sin(j * 2.3)
        pen.radial(None, fx, fy, 230, [(0, '#f4f6f8', 95), (1, '#f4f6f8', 0)], sy=0.55, clip=False)
    bx, by = x1 - 230, y1 - 52                                  # the tiny 7-step staircase, step n filled
    for j in range(7):
        sx_, sy_ = bx + j * 26, by - j * 15
        filled = (j + 1) == n
        if filled: pen.fill(oval(sx_ + 10, sy_, 20, 10), LIP_GLOW, 60)
        pen.seg((sx_, sy_), (sx_ + 20, sy_), 5, LIPSTICK if filled else '#59626d', 255 if filled else 150)
        pen.seg((sx_ + 20, sy_), (sx_ + 20, sy_ - 15), 3, LIPSTICK if filled else '#59626d', 200 if filled else 110)
    text(c, '%d / 7' % n, bx + 90, by + 34, 700, 15, '#59626d', 200, 0.2, 'center')
    c.restore()
    try:
        ST.mirror_frame(pen, x0, y0, x1, y1, 30.0, 1.0, 0.9, night=False)
    except Exception:
        pen.line(rect(x0 - 14, y0 - 14, W_ + 28, Hh + 28), 28, '#d8d4c8', 255)


def _card_layout(rc, e):
    toks = _tokens(rc['text'])
    wts = [w_[1] for w_ in (e.get('words') or [])]
    if len(wts) != len(toks):
        ws, we = rc['title_at'] + 0.6, rc['sentence_end']
        wts = [ws + (we - ws) * j / max(1, len(toks)) for j in range(len(toks))]
    size, sp = 56, 0.015
    space = text_width(' ', 800, size, sp) + 6
    lines, cur, curw = [], [], 0.0
    for j, (w_, red) in enumerate(toks):
        ww = text_width(w_.upper(), 800, size, sp)
        if cur and curw + space + ww > 960:
            lines.append((cur, curw)); cur, curw = [], 0.0
        curw = curw + space + ww if cur else ww
        cur.append((j, w_.upper(), red, ww))
    if cur: lines.append((cur, curw))
    out = []
    ly0 = 20 if len(lines) == 1 else -18
    for li, (ws_, lw) in enumerate(lines):
        xx = -lw / 2; yy = ly0 + li * 76 + 40
        for (j, w_, red, ww) in ws_:
            out.append((j, w_, red, ww, xx, yy, wts[j])); xx += ww + space
    return out, size, sp


CARD_TILT = -2.0


def _rot(x, y, deg):
    r = math.radians(deg); c, s_ = math.cos(r), math.sin(r)
    return x * c - y * s_, x * s_ + y * c


def _rotated(draw, deg):
    def d(c):
        c.save(); c.rotate(deg); draw(c); c.restore()
    return d


def rule_card(cv, rc, e, t):
    """Lipstick on glass: slides up in 0.17 s, title at +1.0 s letter by letter, the statement word by word on the
    narrator's word times (clear glass through breath fog, keywords in lipstick), a finger-wipe exit before the cut.
    Speed: the pane, letters and words are cached sprites with the -2 deg tilt baked in, blitted axis-aligned (a rotated
    full-pane blit costs 0.1 s per frame at 2560)."""
    u = t - rc['appear']
    if u < 0 or t >= rc['cut'] + 0.02: return
    pen = Pen(cv)
    n = rc['n']
    W_, Hh = CARD_W, CARD_H
    x0, y0, x1, y1 = -W_ / 2, -Hh / 2, W_ / 2, Hh / 2
    TL = CARD_TILT
    slide = ease_out_back(clamp(u / 0.17), 1.15)
    oy = (1.0 - slide) * 760.0
    drift = 1.0 + 0.012 * u
    cv.save(); cv.translate(960, 540 + oy); cv.scale(drift, drift)
    if slide < 0.999: cv.rotate(-3.0 * (1 - slide))
    blit(cv, sprite(('card', n), (x0 - 130, y0 - 110, x1 + 130, y1 + 150), _rotated(lambda c: _card_static(c, n), TL)))
    hx, hy = _rot(-260 + 180 * math.sin(u * 0.55) + 60 * u, -120 + 40 * math.sin(u * 0.8), TL)
    spot = sprite(('cardspot',), (-560, -450, 560, 450),
                  lambda c: Pen(c).radial(None, 0, 0, 540, [(0, '#ffffff', 135), (0.45, '#fff6e6', 55), (1, '#ffffff', 0)], sy=0.8, clip=False), 0.4)
    cv.save(); cv.translate(hx, hy); blit(cv, spot); cv.restore()
    p = skia.Path()
    for j in range(26):                                         # dust drifting through the beam
        dx_ = x0 + ((hash01(j, 21) * W_ + u * (14 + 20 * hash01(j, 22))) % W_)
        dy_ = y0 + ((hash01(j, 23) * Hh - u * (6 + 10 * hash01(j, 24))) % Hh)
        dx_, dy_ = _rot(dx_, dy_, TL)
        p.addOval(skia.Rect.MakeXYWH(dx_ - 2, dy_ - 2, 3.2 + 2 * hash01(j, 25), 3.2 + 2 * hash01(j, 25)))
    pen.fill(p, '#ffffff', 150)
    # the title in lipstick, written letter by letter from +1.0 s (its line leans a further -3 deg)
    ut = t - rc['title_at']
    if ut > 0:
        title = 'RULE ' + NUMW[n]
        k = clamp(ut / 0.32)
        nshow = len(title) * k
        tw = text_width(title, 900, 98, 0.05)
        acc = 0.0
        for ci, ch in enumerate(title):
            cw = text_width(ch, 900, 98, 0.0)
            if ci < nshow and ch != ' ':
                kk = clamp(nshow - ci)
                spr = sprite(('ch', ch), (-cw / 2 - 52, -98 - 46, cw / 2 + 52, 56),
                             _rotated(lambda c, ch=ch, cw=cw: _lip_text(c, ch, -cw / 2, 0, 98, 255, 900, 0.0), TL - 3.0))
                px, py = _rot(*_rot(-tw / 2 + acc + cw / 2, -150 + 150, -3.0), TL)
                px, py = px + _rot(0, -150, TL)[0], py + _rot(0, -150, TL)[1]
                cv.save(); cv.translate(px, py); sc_ = 1.0 + 0.25 * (1 - kk); cv.scale(sc_, sc_)
                blit(cv, spr, 255 * kk)
                cv.restore()
            acc += cw + 0.05 * 98
        ku = ease_out_cubic(clamp((ut - 0.2) / 0.3))
        a_ = _rot(*_rot(-tw / 2 + 10, 24, -3.0), TL); b_ = _rot(*_rot(-tw / 2 + 10 + (tw - 20) * ku, 28, -3.0), TL)
        o_ = _rot(0, -150, TL)
        if ku > 0: pen.seg((a_[0] + o_[0], a_[1] + o_[1]), (b_[0] + o_[0], b_[1] + o_[1]), 7, LIPSTICK, 230)
    # the statement
    lay, size, sp = _card_layout(rc, e)
    wipe = clamp((t - rc['sentence_end']) / max(0.05, rc['cut'] - rc['sentence_end']))
    if wipe > 0:
        wx = lerp(x0 - 300, x1 + 300, ease_in_out(wipe))
        clip = poly([(wx + 140, y0 - 50), (x1 + 400, y0 - 50), (x1 + 400, y1 + 50), (wx - 140, y1 + 50)])
        cv.save(); cv.rotate(TL); cv.clipPath(clip, skia.ClipOp.kIntersect, True); cv.rotate(-TL)
    for (j, w_, red, ww, xx, yy, tw_) in lay:
        uw = t - tw_ + 0.06
        if uw <= 0: continue
        kk = ease_out_cubic(clamp(uw / 0.16))

        def dw(c, w_=w_, red=red):
            if red:
                _lip_text(c, w_, 0, 0, size, 255, 900, sp, 'left', 0.8)
            else:
                text(c, w_, 0, 0, 800, size, '#fbfcfd', 120, sp, 'left', 0.0, glow=('#ffffff', 170, 7))
                text(c, w_, 0, 0, 800, size, '#3b4652', 245, sp, 'left')
        spr = sprite(('w', n, j), (-30, -size - 40, ww + 36, size * 0.45 + 40), _rotated(dw, TL))
        px, py = _rot(xx, yy, TL)
        cv.save(); cv.translate(px, py); cv.scale(0.9 + 0.1 * kk, 1.0)
        blit(cv, spr, 255 * kk)
        cv.restore()
    if wipe > 0:
        cv.restore()
        cv.save(); cv.rotate(TL)
        pane = rect(x0, y0, W_, Hh)
        band = poly([(wx + 140, y0 - 50), (wx + 300, y0 - 50), (wx + 20, y1 + 50), (wx - 140, y1 + 50)])
        cv.clipPath(pane, skia.ClipOp.kIntersect, True)
        pen.fill(band, '#e9ecef', 150)
        for j in range(6):
            o = -60 + j * 26
            pen.seg((wx + 140 + o, y0 - 50), (wx - 140 + o, y1 + 50), 5, '#c86a78' if j % 2 else '#ffffff', 60)
        cv.restore()
    cv.restore()


# ==================================================================================================== CLI tools
def _sheet(F, ids, prefix, size, tile, cols, per):
    from engine.core import set_render_size
    tiles = []
    for sid in ids:
        sid, _, tt = sid.partition('@')
        sh = F.shots[F.index[sid]]
        t = float(tt) if tt else round((sh['t0'] + sh['t1']) / 2, 3)
        t_ = time.perf_counter()
        img = F.frame(t, int(round(t * FPS)))
        dt = time.perf_counter() - t_
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        th = cv2.resize(bgr, (tile, tile * 9 // 16), interpolation=cv2.INTER_AREA)
        lab = '%s %.1f %s/%s' % (sid, t, sh['view'], sh['var'])
        cv2.putText(th, lab, (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(th, lab, (3, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (80, 255, 255), 1, cv2.LINE_AA)
        tiles.append((sid, th))
        print('%s t=%.2f %.2fs luma %.0f' % (sid, t, dt, float(np.median(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)))), flush=True)
    for pg in range(0, len(tiles), per):
        tl = tiles[pg:pg + per]
        rows = int(math.ceil(len(tl) / cols)); h_, w_ = tl[0][1].shape[:2]
        sheet = np.zeros((rows * h_, cols * w_, 3), np.uint8)
        for j, (_, im) in enumerate(tl): sheet[(j // cols) * h_:(j // cols + 1) * h_, (j % cols) * w_:(j % cols + 1) * w_] = im
        o = '%s_%s_%s.jpg' % (prefix, tl[0][0], tl[-1][0])
        cv2.imwrite(o, sheet, [cv2.IMWRITE_JPEG_QUALITY, 86]); print(o, flush=True)


def _bench(F, ids, n=int(os.environ.get('BENCH_N', '5'))):
    from engine import scene as SC
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
        _sheet(F, ids, A.sheet, A.size, A.tile, A.cols, A.per)
