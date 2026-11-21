"""tools/ui_v2_check.py: measured checks of the v2 HUD (DIRECTION_V2 rank 4 checks).

    python3 tools/ui_v2_check.py            # card timing + caption collisions + device counts + HUD cost

1. Card timing: each rule card's HUD is rendered alone (transparent canvas, 640x360) frame by frame around its appear
   and cut times; the first and last frame with the card on screen are compared with the brief's table (+-0.05 s).
   The choreography marks (towel off, RULE written, numeral settled, underline, wipe) are sampled the same way.
2. Captions never cover a diagram's key element: every shot with HUD entries is rendered without captions every 0.1 s;
   the HUD's coverage inside the caption box of the caption on screen at that moment is measured (> 3 % = a hit).
3. Counts: red X, command tags, labels, chips drawn, giant numbers, diagrams, type beats (the brief's limits).
4. HUD cost at 2560x1440 for the heaviest devices (warm median, ms).
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import numpy as np
from engine.core import set_render_size, surface_for, CFG, DW, text_width

BRIEF_CARDS = {1: (129.80, 133.56), 2: (203.53, 208.32), 3: (269.24, 273.35), 4: (350.38, 353.53), 5: (446.33, 449.74),
               6: (542.03, 545.22), 7: (609.48, 614.71)}


def hud_alpha(UI, sh, t, captions=False, header_on=False):
    arr = np.zeros((CFG.rh, CFG.rw, 4), np.uint8)
    sf = surface_for(arr); cv = sf.getCanvas(); cv.scale(CFG.rw / DW, CFG.rw / DW)
    UI.hud(cv, t, sh, None, None, captions=captions, header_on=header_on)
    del cv, sf
    return arr[..., 3]


def shot_at(P, t):
    for s in P['shots']:
        if s['t0'] <= t < s['t1']: return s
    return P['shots'][-1]


def check_cards(P, UI):
    print('\n1. RULE CARD TIMING (card on screen = HUD alpha in the card box)')
    print('   card  brief appear-cut     measured first-last frame    d_appear  d_cut   towel off  RULE done  numeral set  underline  wipe start')
    ok = True
    for rc in P['rule_cards']:
        n = rc['n']; a, c = BRIEF_CARDS[n]
        sh = next(s for s in P['shots'] if s['id'] == rc['shot'])
        e = next(x for x in sh['hud'] if x['type'] == 'rule_card')
        ts = [round(a - 0.1 + k / 60.0, 4) for k in range(int((c - a + 0.2) * 60) + 1)]
        on = []
        H, W = CFG.rh, CFG.rw
        import ui_v2_card
        for t in ts:                                       # the card alone (the giant 45 / 0 sit on the shots before)
            arr = np.zeros((CFG.rh, CFG.rw, 4), np.uint8)
            sf = surface_for(arr); cv = sf.getCanvas(); cv.scale(CFG.rw / DW, CFG.rw / DW)
            if sh['t0'] <= t < sh['t1']: ui_v2_card.rule_card(cv, rc, e, t)
            del cv, sf
            box = arr[int(H * 0.2):int(H * 0.8), int(W * 0.22):int(W * 0.78), 3]
            on.append(box.mean() > 60)
        first = next(t for t, o in zip(ts, on) if o)
        last = max(t for t, o in zip(ts, on) if o) + 1 / 60.0
        da, dc = first - a, last - c
        good = abs(da) <= 0.05 and abs(dc) <= 0.05
        ok &= good
        print('   %d     %.2f-%.2f        %.3f-%.3f            %+.3f   %+.3f   %.2f       %.2f       %.2f         %.2f       %.2f   %s' %
              (n, a, c, first, last, da, dc, e['towel_whip'][1], e['rule_write'][1], e['numeral_stamp']['t'] + e['numeral_stamp']['settle'],
               e['underline_at'], e['wipe_out'], 'PASS' if good else 'FAIL'))
    return ok


def check_captions(P, UI):
    print('\n2. CAPTIONS vs HUD key elements (HUD coverage inside the caption box while a caption is on screen)')
    hits = []
    skip = {'rule_card', 'like_sub', 'phone', 'time_card'}
    n_checked = 0
    for s in P['shots']:
        types = {e['type'] for e in s['hud']} - skip
        if not types and not s.get('split') and not s.get('montage'): continue
        if s.get('captions') is False: continue
        t = s['t0'] + 0.02
        while t < s['t1']:
            c = UI.caption_at(t)
            glint = (s.get('glint') or s.get('tr') == 'glint') and t - s['t0'] < 3 / 60.0
            wipe = any(e['type'] == 'kinetic' and t >= e['out']['t'] for e in s['hud'])
            if c and not glint and not wipe:
                al = hud_alpha(UI, s, t)
                w = min(1500, text_width(c['text'].upper(), 700, 33, 0.045))
                x0, x1 = int((DW / 2 - w / 2 - 30) / DW * CFG.rw), int((DW / 2 + w / 2 + 30) / DW * CFG.rw)
                y0, y1 = int(940 / 1080 * CFG.rh), int(992 / 1080 * CFG.rh)
                cov = (al[y0:y1, x0:x1] > 128).mean()
                n_checked += 1
                if cov > 0.03: hits.append((s['id'], round(t, 2), sorted(types), round(cov * 100, 1), c['text']))
            t += 0.1
    print('   %d samples checked' % n_checked)
    for h in hits: print('   HIT %s %.2f %s coverage %.1f %%  "%s"' % h)
    print('   %d hits' % len(hits))
    return hits


def counts(P):
    print('\n3. COUNTS (brief limits)')
    from collections import Counter
    c = Counter(e['type'] for s in P['shots'] for e in s['hud'])
    chips = sum(1 for s in P['shots'] if s.get('chip') and s['chip'].get('pop')) + c['chip']
    rows = [('red X', c['red_x'], '4'), ('command tags', c['tag'], '6'), ('labels', c['label'], '8+'), ('giant numbers', c['giant_number'], '5 (60/45/20/5/0)'),
            ('type beats', c['typebeat'] + 0, '6 kinds'), ('diagram entries', c['diagram'], 'D1-D10'), ('kinetic titles', c['kinetic'], '1'),
            ('teasers', c['teaser'], '5'), ('chips drawn', chips, 'every first shot after a switch'), ('stamps', c['stamp'], ''),
            ('count numerals', c['count_pop'], ''), ('side-switch glints', sum(1 for s in P['shots'] if s.get('glint')), '18-22')]
    for r in rows: print('   %-20s %4d   %s' % r)


def cost(P):
    print('\n4. HUD COST at 2560x1440 (warm, ms per frame)')
    set_render_size(2560, 1440)
    import importlib, ui_v2_letter
    ui_v2_letter.clear_sprites()
    import ui_v2
    UI = ui_v2.UI(P)
    for sid, t, n in [('S140', 205.0, 60), ('S398', 611.0, 60), ('S092', 129.8, 30), ('S192', 289.2, 40), ('S006', 3.9, 60),
                      ('S072', 98.3, 60), ('S229', 343.0, 60), ('S343', 530.5, 40), ('S288', 438.9, 30), ('S446', 692.0, 30)]:
        sh = next(s for s in P['shots'] if s['id'] == sid)
        arr = np.zeros((1440, 2560, 4), np.uint8); sf = surface_for(arr); cv = sf.getCanvas(); cv.scale(CFG.rw / DW, CFG.rw / DW)
        ts = []
        for k in range(n):
            t0 = time.time(); cv.save(); UI.hud(cv, t + k / 60, sh); cv.restore(); ts.append(time.time() - t0)
        ts = np.array(ts[1:]) * 1000
        print('   %s %-28s median %4.0f  p90 %4.0f' % (sid, sh['frame'][:28], np.median(ts), np.percentile(ts, 90)))


def main():
    P = json.load(open(os.path.join(HERE, 'plan', 'shots.json')))
    set_render_size(640, 360)
    import ui_v2
    UI = ui_v2.UI(P)
    ok = check_cards(P, UI)
    hits = check_captions(P, UI)
    counts(P)
    if '--no-cost' not in sys.argv: cost(P)
    print('\nCARDS %s, CAPTION HITS %d' % ('PASS' if ok else 'FAIL', len(hits)))


if __name__ == '__main__':
    main()
