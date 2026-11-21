"""Summarize motion_*.json into pacing/motion stats (prints compact text). Args: va_dir ref2_dir"""
import sys, json, numpy as np
va, ref = sys.argv[1], sys.argv[2]
for name in ['fire','hotel','class']:
    R = json.load(open(f'{va}/motion_{name}.json'))
    t = np.array([r['t'] for r in R]); n=len(R)
    g = lambda k: np.array([r.get(k, np.nan) for r in R])
    hd, gd = g('hdiff'), g('gdiff')
    sc = np.loadtxt(f'{ref}/cuts_{name}.txt', usecols=0)
    merged = np.loadtxt(f'{va}/cuts2_{name}.txt')
    dur = t[-1]
    edges = np.concatenate([[0], merged, [dur]]); sl = np.diff(edges); sl = sl[sl > 0.3]
    near = np.zeros(n, bool)
    for c in merged: near |= np.abs(t - c) < 0.35
    ok = ~near & ~np.isnan(g('zoom'))
    zoom = g('zoom')[ok] * 6 * 100  # % per second
    tx = g('tx')[ok] * 4 * 6; ty = g('ty')[ok] * 4 * 6  # px/s at 1280
    sp = np.hypot(tx, ty)
    res = g('resid90')[ok] * 4 * 6
    cam_moving = (np.abs(zoom) > 0.8) | (sp > 8)
    print(f'== {name} dur {dur:.0f}s cuts scdet {len(sc)} merged {len(merged)} shots {len(sl)}')
    print(' shot len pct10/25/50/75/90:', np.round(np.percentile(sl,[10,25,50,75,90]),2), 'mean', round(sl.mean(),2))
    print(' cam moving share %.2f, zoom-in share %.2f zoom-out %.2f, pan share %.2f' % (cam_moving.mean(), (zoom>0.8).mean(), (zoom<-0.8).mean(), (sp>8).mean()))
    zi = zoom[zoom > 0.8]; print(' push-in %%/s pct25/50/75/90:', np.round(np.percentile(zi,[25,50,75,90]),2))
    zo = -zoom[zoom < -0.8]; print(' pull-out %%/s pct50/90:', np.round(np.percentile(zo,[50,90]),2) if len(zo) else None)
    ps = sp[sp > 8]; print(' pan px/s@1280 pct25/50/75/90:', np.round(np.percentile(ps,[25,50,75,90]),1))
    # shake: high-pass of tx within shots
    txr = g('tx') * 24; hp = txr - np.convolve(np.nan_to_num(txr), np.ones(7)/7, 'same')
    print(' shake (hp tx std px/s) %.2f' % np.nanstd(hp[ok]))
    print(' subject resid90 px/s pct50/75/90: ', np.round(np.percentile(res,[50,75,90]),1), ' share >30px/s %.2f' % (res>30).mean())
    # tone arc in 10 bins
    bins = np.linspace(0, dur, 11)
    L, Sa, Rd, Bl = g('luma'), g('sat'), g('red'), g('blue')
    arc = []
    for a, b in zip(bins[:-1], bins[1:]):
        m = (t >= a) & (t < b); mm = m & ~np.isnan(g('zoom')) & ~near
        nc = ((merged >= a) & (merged < b)).sum()
        arc.append((round(L[m].mean()), round(Sa[m].mean()), round(100*Rd[m].mean(),1), round(100*Bl[m].mean(),1), nc,
                    round(np.mean(np.abs(g('zoom')[mm])*600),2), round(np.nanmean(g('resid90')[mm]*24),1)))
    print(' arc (luma,sat,red%,blue%,cuts,|zoom|%/s,subj px/s):', arc)

    print(' (per-shot block printed above)')
