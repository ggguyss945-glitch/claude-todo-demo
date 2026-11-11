"""tools/ui_v2_sheet.py: contact sheets of every on-screen device of the v2 film (ui_v2, ui_v2_card, ui_v2_diag).

    python3 tools/ui_v2_sheet.py [groups...] [--size 1280x720] [--out _work/ui_v2]
    groups: cards (7 strips at 6 fps, card1..card7), title, type, countdown, chips, marks, diagrams, docs, phone, fx, all

Each tile is a real frame: the shot's set through its v1 fallback view (the v2 sets replace it later) with the cast,
the camera, the grade and the frame effects, then the v2 HUD on top (UI.hud + UI.frame_fx; DOC shots also get
ui_v2.doc_layer). Tiles are 640x360, the size the brief's legibility check asks for ("every text legible at 640x360").
A label on each tile gives the film time, the shot, the device and the words spoken.
"""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
import cv2
from engine.core import set_render_size

OUT = os.path.join(HERE, '_work', 'ui_v2')
TW, TH = 640, 360


def words_at(L, t, span=0.6):
    out = []
    for l in L:
        for w, wt in l.get('words', []):
            if wt is not None and t - span <= wt <= t + 0.05: out.append(w)
    return ' '.join(out[-5:])


class Renderer:
    def __init__(self):
        import film as FM
        import ui_v2
        self.FM, self.U = FM, ui_v2
        self.F = FM.Film()
        self.UI = ui_v2.UI(self.F.P, self.F.tl)
        self.cache_k = None

    def frame(self, t, sid=None, hud=True, extra=None):
        F = self.F
        k = F.index[sid] if sid else F.idx_at(t)
        sh = F.shots[k]
        if self.cache_k != k:
            F._built.clear()
            F.shots[k] = dict(sh, **sh['v1'])
            if sh.get('v1', {}).get('bg'): F.shots[k]['bg'] = sh['v1']['bg']
            try:
                B = F.build(k)
            finally:
                F.shots[k] = sh
            B.sh = sh
            dl = self.U.doc_layer(sh)
            if dl is not None: B.layers = list(B.layers) + [dl]
            self.B, self.cache_k = B, k
        B = self.B
        from engine.scene import render_frame
        cs = B.cam.at(t)
        fx = F.fx_at(B, t, k)
        if sh.get('plate') and sh['plate'].get('post'):
            fx = dict(fx); fx['blur'] = sh['plate']['post'].get('blur', 0); fx['dim'] = sh['plate']['post'].get('dim', 0)
        if sh['set'] == 'rule_mirror':
            fx = dict(fx); fx['blur'] = 8; fx['dim'] = 0.3
        i = int(round(t * 60))
        def hf(cv, tt):
            if extra is not None: extra(cv, tt)
            if hud: self.UI.hud(cv, tt, sh, cs, F)
        img = render_frame(B.layers, cs, t, i, focus=B.focus, dof=B.dof, lens=None, grade=B.grade, post=fx, hud=hf)
        return self.UI.frame_fx(img, t, sh, i), sh


def tile(img, label, sub=''):
    im = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (TW, TH), interpolation=cv2.INTER_AREA)
    bar = np.full((34, TW, 3), 18, np.uint8)
    cv2.putText(bar, label, (6, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bar, sub[:80], (6, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (170, 190, 255), 1, cv2.LINE_AA)
    return np.vstack([bar, im])


def sheet(tiles, path, cols=4, title=''):
    if not tiles: return
    h, w = tiles[0].shape[:2]
    rows = []
    for i in range(0, len(tiles), cols):
        r = tiles[i:i + cols]
        r = r + [np.zeros_like(tiles[0])] * (cols - len(r))
        rows.append(np.hstack(r))
    img = np.vstack(rows)
    if title:
        bar = np.full((40, img.shape[1], 3), 10, np.uint8)
        cv2.putText(bar, title, (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 220, 255), 2, cv2.LINE_AA)
        img = np.vstack([bar, img])
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(path, img.shape[1], 'x', img.shape[0], flush=True)


def run_list(R, items, path, title, cols=4):
    tiles = []
    for it in items:
        t, sid, lab = it[:3]
        extra = it[3] if len(it) > 3 else None
        t0 = time.time()
        try:
            img, sh = R.frame(t, sid, extra=extra)
            tiles.append(tile(img, '%.2f  %s  %s' % (t, sh['id'], lab), words_at(R.F.L, t)))
        except Exception as e:
            import traceback; traceback.print_exc()
            bad = np.zeros((TH + 34, TW, 3), np.uint8)
            cv2.putText(bad, 'ERR %s %.2f %r' % (sid, t, e)[:70], (6, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            tiles.append(bad)
    sheet(tiles, path, cols, title)


def G_cards(R):
    for rc in R.F.P['rule_cards']:
        n = rc['n']
        t0, t1 = rc['appear'] - 0.17, rc['cut'] + 0.34
        ts = [round(t0 + j / 6.0, 3) for j in range(int((t1 - t0) * 6) + 1)]
        items = [(t, None, 'card %d' % n) for t in ts]
        run_list(R, items, os.path.join(OUT, 'card%d_6fps.jpg' % n), 'RULE CARD %d at 6 fps  (%s; reflection %s; glass: %s)' %
                 (n, rc['command'], rc['reflection']['pose'], rc['glass']), 6)


def by_type(P, ty):
    out = []
    for s in P['shots']:
        for e in s['hud']:
            if e['type'] == ty: out.append((s, e))
    return out


def G_title(R):
    items = [(t, 'S006', 'kinetic title') for t in (3.80, 3.93, 3.98, 4.12, 4.26, 4.42, 4.6, 4.80, 4.817, 4.84, 4.95, 5.2, 5.33, 5.37)]
    items += [(t, 'S449', 'end card (type beat 6)') for t in (698.7, 698.85, 699.0, 699.2, 699.45, 699.9)]
    run_list(R, items, os.path.join(OUT, 'title_and_end.jpg'), 'KINETIC TITLE  WIPE THE GLASS CLEAN.  +  END CARD  DON\'T MAKE A WISH.', 5)


def G_type(R):
    items = [(t, 'S017', 'type 2: 14 YEARS stamp') for t in (14.70, 14.75, 14.80, 14.9, 15.4)]
    items += [(t, 'S281', '14 YEARS echo') for t in (426.12, 426.2, 426.8)]
    items += [(t, 'S087', 'steps light 1-7 (count_pop red)') for t in (121.2, 121.5, 121.95)]
    items += [(t, 'S088', 'type 3: 7 RULES') for t in (122.85, 122.92, 123.0, 123.3, 123.7)]
    items += [(t, 'S089', 'RULE 4 circled') for t in (124.95, 125.1, 125.3)]
    items += [(t, 'S348', 'type 5: 7:00 AM + D9') for t in (538.3, 538.68, 538.75, 538.85, 539.1)]
    items += [(t, 'S288', 'CANCELED stamp') for t in (438.9, 439.0, 439.3)]
    run_list(R, items, os.path.join(OUT, 'type_beats.jpg'), 'TYPE BEATS: 14 YEARS, 7 RULES + RULE 4 circle, 7:00 AM, CANCELED', 5)


def G_countdown(R):
    items = []
    for t in (289.2, 289.3, 289.6, 289.78, 289.95, 290.4):
        items.append((t, None, 'giant 60 -> badge'))
    for t in (349.8, 350.1, 350.3, 351.0 + 3.0):
        items.append((t, None, 'giant 45 / badge'))
    for t in (502.37, 502.6, 502.95, 503.4):
        items.append((t, None, 'giant 20'))
    for t in (585.63, 585.9, 586.2, 586.6):
        items.append((t, None, 'giant 5'))
    for t in (608.98, 609.1, 609.4):
        items.append((t, None, 'giant 0'))
    items += [(t, None, 'badge ticking') for t in (330.0, 400.0, 560.0)]
    run_list(R, items, os.path.join(OUT, 'countdown.jpg'), "TESS'S COUNTDOWN: giant numbers 60/45/20/5/0 (38 % H) flying into the ring badge", 5)


def G_chips(R):
    P = R.F.P
    items = []
    seen = set()
    for s in P['shots']:
        ch = s.get('chip')
        if ch and ch.get('pop') and (ch['text'], ch['style']) not in seen and len(items) < 9:
            seen.add((ch['text'], ch['style'])); items.append((s['t0'] + 0.5, s['id'], 'chip %s' % ch['style']))
    for s in P['shots']:
        if s.get('teaser'): items.append((s['t0'] + 0.08, s['id'], 'teaser %s' % s['teaser']))
    for s, e in by_type(P, 'chip'):
        if e['style'] in ('loop',) and len([i for i in items if 'loop' in i[2]]) < 2: items.append((e['t'] + 0.3, s['id'], 'chip loop'))
    items.append((19.9, 'S021', 'time card'))
    items.append((21.0, 'S021', 'time card'))
    run_list(R, items, os.path.join(OUT, 'chips_teasers.jpg'), 'PLACE / TIME CHIPS (ours, theirs, memory stamp, loop) + TEASERS (red border, chip, RGB split) + time card', 4)


def G_marks(R):
    P = R.F.P
    items = []
    for s, e in by_type(P, 'red_x'): items += [(e['t'] + 0.03, s['id'], 'red X %d' % e['n']), (e['t'] + 0.2, s['id'], 'red X %d' % e['n'])]
    for s, e in by_type(P, 'tag'): items += [(e['t'] + 0.02, s['id'], 'tag'), (e['t'] + 0.3, s['id'], 'tag %s' % e['text'])]
    for s, e in by_type(P, 'label')[:6]: items.append((e['t'] + 0.3, s['id'], 'label %s' % e['text']))
    for s, e in by_type(P, 'highlight'): items += [(e['t'] + 0.15, s['id'], 'highlighter'), (e['t'] + 0.6, s['id'], 'highlighter')]
    for s, e in by_type(P, 'balloon'): items.append((e['t'] + 0.3, s['id'], 'balloon'))
    run_list(R, items, os.path.join(OUT, 'marks_tags_labels.jpg'), 'RED X (4) + COMMAND TAGS (6, lipstick, no box) + LABELS + HIGHLIGHTER + BALLOONS', 4)


def G_diagrams(R):
    items = [(t, 'S072', 'D1 game') for t in (98.25, 98.6, 99.0, 99.4, 99.75, 100.3)]
    items += [(t, None, 'D2 count') for t in (1.97, 2.5, 135.1, 139.7, 618.9, 620.7, 685.7)]
    items += [(t, 'S101', 'D3 side view') for t in (143.7, 144.1, 144.5, 144.9)]
    items += [(t, 'S103', 'level guide') for t in (146.75, 147.2, 147.9)]
    items += [(t, 'S122', 'D4 floors') for t in (176.75, 177.2, 178.0)]
    items += [(t, 'S139', 'D5 eye line') for t in (202.45, 202.8, 203.3)]
    items += [(t, 'S229', 'D6 dials') for t in (343.1, 343.8, 344.6)]
    items += [(t, 'S019', 'D7 loop clock') for t in (17.7, 17.94, 18.0, 18.15)]
    items += [(t, 'S257', 'D7 clock climbing') for t in (387.0, 388.2)]
    items += [(t, 'S051', 'D8 plant: clean + rattle') for t in (66.4, 66.9, 67.3)]
    items += [(t, 'S332', 'fake bell rings') for t in (513.8,)]
    items += [(t, 'S338', 'D8 clean note') for t in (524.1,)]
    items += [(t, 'S343', 'D8 split') for t in (530.7, 531.2)]
    items += [(t, 'S346', 'real bell: broken rings') for t in (535.5, 535.8)]
    items += [(t, 'S348', 'D9 7:00:00') for t in (538.4, 538.72, 539.0)]
    items += [(t, 'S280', 'loop split') for t in (422.6, 423.5)]
    items += [(t, 'S295', 'D10 map') for t in (450.0, 450.6, 451.2)]
    items += [(t, 'S065', 'watch 6:45 -> 4:45') for t in (87.5, 87.8, 88.4)]
    items += [(t, 'S437', 'face-up montage') for t in (677.42, 677.8, 678.2, 678.6)]
    run_list(R, items, os.path.join(OUT, 'diagrams.jpg'), 'DIAGRAMS D1-D10 + count numerals + level guide + loop split + watch + montage', 5)


def G_docs(R):
    items = [(13.4, 'S016', 'poster'), (14.3, 'S016', 'poster'), (25.6, 'S023', 'notice'), (26.8, 'S023', 'notice underline'),
             (35.5, 'S030', 'poster ECU'), (36.3, 'S030', 'highlighter'), (57.5, 'S045', 'stencil'), (58.8, 'S045', 'museum tag flip'),
             (95.8, 'S070', 'playing card'), (221.8, 'S150', 'polaroid'), (316.2, 'S211', 'Dad photo'),
             (438.3, 'S288', 'menu'), (438.85, 'S288', 'CANCELED chalk'), (439.2, 'S288', 'CANCELED stamp'), (444.2, 'S292', 'CAMP CLOSED')]
    run_list(R, items, os.path.join(OUT, 'documents.jpg'), 'EVIDENCE DOCUMENTS (doc_layer): poster, notice, stencil, card, polaroid, Dad photo, menu, sign', 4)


def G_phone(R):
    items = [(46.5, 'S038', 'texts'), (47.9, 'S039', 'texts 2 (text fit)'), (187.0, 'S127', 'voicemail list'),
             (189.0, 'S128', 'voicemail inset'), (654.4, 'S423', 'calling inset'), (657.5, 'S425', 'call, Mom\'s waveform'),
             (663.0, 'S428', 'flat waveform'), (665.8, 'S429', 'chair-scrape spike')]
    import ui_v2_diag as D
    from engine.core import Pen

    def scr(steps, eighth, red=0.0):
        def f(cv, tt):
            Pen(cv)
            cv.drawRoundRect(__import__('skia').Rect.MakeLTRB(960 - 330, 40, 960 + 330, 1040), 60, 60, D.paint('#1a1c22', 255))
            D.phone_screen(Pen(cv), 960, 540, 600, 960, tt, 'steps', steps=steps, eighth=eighth, red=red)
        return f
    items += [(685.0, 'S442', "new state 'steps' (set side: phone_screen)", scr(1.0, 0.0)),
              (690.3, 'S445', "'steps' + the 8th line", scr(1.0, 1.0, 0.3)),
              (692.5, 'S446', "8th line glowing (H10 plate)", scr(1.0, 1.0, 0.6))]
    run_list(R, items, os.path.join(OUT, 'phone.jpg'), 'PHONE UI (kept states, bubbles text-fitted) + the new screen state for the face-up phone', 4)


def G_fx(R):
    P = R.F.P
    items = []
    gl = [s for s in P['shots'] if s.get('glint')][:3]
    for s in gl: items += [(s['t0'] + 0.002, s['id'], 'glint f1'), (s['t0'] + 0.018, s['id'], 'glint f2'), (s['t0'] + 0.035, s['id'], 'glint f3')]
    items += [(t, 'S019', 'rewind (fx_post)') for t in (17.96, 18.0, 18.08)]
    items += [(t, 'S239', 'rewind cut') for t in (359.79, 359.85, 359.95)]
    items += [(t, 'S448', 'pixel sort 697.95') for t in (698.0, 698.1, 698.2)]
    items += [(t, 'S093', 'card 1 smear carry') for t in (133.58, 133.65, 133.72)]
    items += [(t, 'S001', 'flash-forward + glitch out') for t in (0.02, 0.2, 0.38)]
    run_list(R, items, os.path.join(OUT, 'transitions_fx.jpg'), 'TRANSITIONS: side-switch glint (3 frames), rewind, pixel sort, card smear carry, teaser glitch', 6)


GROUPS = dict(cards=G_cards, title=G_title, type=G_type, countdown=G_countdown, chips=G_chips, marks=G_marks,
              diagrams=G_diagrams, docs=G_docs, phone=G_phone, fx=G_fx)


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument('groups', nargs='*', default=['all'])
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    w, h = map(int, a.size.split('x'))
    set_render_size(w, h)
    R = Renderer()
    gs = list(GROUPS) if 'all' in a.groups else a.groups
    for g in gs:
        t0 = time.time()
        GROUPS[g](R)
        print('group %s %.0fs' % (g, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
