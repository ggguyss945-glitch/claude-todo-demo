"""Global look stats per scene family from 1 fps 1280x720 frames. Prints compact table + JSON to argv[2]."""
import numpy as np, cv2, json, sys
va = sys.argv[1]
FAM = {
 'night_exterior': [('fire',27),('fire',63),('fire',234),('fire',405),('fire',486),('fire',243),('fire',423)],
 'porch_light_doorway': [('fire',45),('fire',180),('fire',198),('fire',207),('fire',252)],
 'peephole': [('fire',0),('fire',72),('fire',99),('fire',351),('fire',414),('fire',432),('hotel',283)],
 'dim_interior': [('fire',18),('fire',90),('fire',117),('fire',225),('fire',459),('fire',468),('class',353)],
 'warm_interior_hotel': [('hotel',9),('hotel',78),('hotel',176),('hotel',205),('hotel',254),('hotel',401)],
 'classroom': [('class',22),('class',45),('class',114),('class',296),('class',559)],
 'red_alert': [('fire',288),('fire',360),('fire',369),('fire',378),('fire',477)],
 'phone_ui': [('fire',270),('fire',387),('fire',396),('hotel',361),('hotel',528),('class',262),('class',513)],
 'rule_card': [('fire',297),('fire',342),('hotel',234),('hotel',391),('class',331)],
 'face_closeup': [('hotel',48),('hotel',58),('hotel',88),('hotel',166),('class',194),('class',205),('class',456),('fire',441)],
}
def rise_width(g, frac=0.004):
    """median 10-90% edge rise distance (px) across strongest edges"""
    gf = g.astype(np.float32)
    gx = cv2.Sobel(gf, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(gf, cv2.CV_32F, 0, 1, ksize=3)
    m = np.hypot(gx, gy); m[:8] = 0; m[-8:] = 0; m[:, :8] = 0; m[:, -8:] = 0
    th = np.quantile(m, 1 - frac); ys, xs = np.where(m >= th)
    if len(ys) > 400: sel = np.random.default_rng(0).choice(len(ys), 400, replace=False); ys, xs = ys[sel], xs[sel]
    out = []
    s = np.linspace(-6, 6, 49)
    for y, x in zip(ys, xs):
        d = np.array([gx[y, x], gy[y, x]]); d /= np.linalg.norm(d) + 1e-6
        px = (x + s * d[0]).astype(np.float32); py = (y + s * d[1]).astype(np.float32)
        p = cv2.remap(gf, px[None], py[None], cv2.INTER_LINEAR)[0]
        lo, hi = p[:8].mean(), p[-8:].mean()
        if hi - lo < 40: continue
        q = (p - lo) / (hi - lo)
        try:
            a = s[np.where(q >= 0.1)[0][0]]; b = s[np.where(q >= 0.9)[0][0]]; out.append(b - a)
        except IndexError: pass
    return float(np.median(out)) if out else None
def grain(g):
    gf = g.astype(np.float32); hp = gf - cv2.GaussianBlur(gf, (0, 0), 2.0)
    lm = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(gf,(0,0),1.5), cv2.CV_32F)), (0, 0), 4)
    flat = lm < np.quantile(lm, 0.25)
    return float(hp[flat].std())
def palette(im, k=6):
    sm = cv2.resize(im, (160, 90), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
    _, lab, cen = cv2.kmeans(sm, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    w = np.bincount(lab.ravel(), minlength=k) / len(lab)
    o = np.argsort(-w)
    return [('#%02x%02x%02x' % tuple(int(v) for v in cen[i][::-1]), round(float(w[i]), 2)) for i in o]
def main():
    res = {}
    for fam, lst in FAM.items():
        L = []; P = []
        for name, t in lst:
            im = cv2.imread(f'{va}/{name}/f{t+1:04d}.jpg'); im = im[:640]  # drop caption band
            g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
            L.append([*np.percentile(g, [1, 5, 50, 95, 99.5]), g.std(), hsv[..., 1].mean(), np.percentile(hsv[...,1],90), grain(g), rise_width(g) or np.nan])
            P += palette(im, 5)
        L = np.array(L, float); mL = np.nanmedian(L, 0)
        # merged palette by weight (cluster across frames again)
        cols = np.array([[int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)] for h,_ in P], np.float32); ws = np.array([w for _,w in P])
        _, lab, cen = cv2.kmeans(np.repeat(cols, np.maximum(1,(ws*20).astype(int)), 0), 7, None, (3, 30, 0.5), 4, cv2.KMEANS_PP_CENTERS)
        cnt = np.bincount(lab.ravel(), minlength=7); o = np.argsort(-cnt)
        pal = ['#%02x%02x%02x' % tuple(int(v) for v in cen[i]) for i in o]
        res[fam] = dict(p1=mL[0], p5=mL[1], p50=mL[2], p95=mL[3], p995=mL[4], contrast_std=mL[5], sat_mean=mL[6], sat_p90=mL[7], grain_std=mL[8], edge_rise_px1280=mL[9], palette=pal)
        print(f'{fam:22s} luma p1 {mL[0]:.0f} p5 {mL[1]:.0f} p50 {mL[2]:.0f} p95 {mL[3]:.0f} p99.5 {mL[4]:.0f} | std {mL[5]:.0f} | sat {mL[6]:.0f} p90 {mL[7]:.0f} | grain {mL[8]:.2f} | rise {mL[9]:.2f}px | {" ".join(pal)}')
    json.dump(res, open(sys.argv[2], 'w'), indent=1, default=float)

if __name__ == '__main__':
    main()
