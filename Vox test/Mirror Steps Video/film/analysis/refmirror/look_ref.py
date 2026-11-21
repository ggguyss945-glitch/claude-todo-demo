"""Look statistics per scene family from 1 fps 854x480 frames (caption band y > 0.86 H dropped).

Usage: python3 -I look_ref.py <data_dir> <out.json> <sheet_dir>
Per family: luma p1/p5/p50/p95/p99.5, contrast (std), HSV sat mean/p90, mean hue of saturated px,
k-means palette (most frequent first), vignette (mean-frame luma at r = .4/.6/.8/.95 of corner distance
relative to r < .15). Also writes a verification thumbnail strip per family to <sheet_dir>/fam_<family>.jpg.
"""
import sys, json, cv2, numpy as np

FAM = {
 "diver_tank_gallery": [("diver", s) for s in (0, 1, 2, 9, 10, 18, 19, 20, 28, 29, 32, 38, 40, 42, 64, 66, 124, 126)],
 "diver_dark_water": [("diver", s) for s in (78, 79, 80, 154, 156, 166, 316, 318)],
 "diver_ocean_tunnel": [("diver", s) for s in (232, 234, 240, 242, 268, 270, 272, 280, 300, 302, 320, 322, 324)],
 "diver_entity_dark": [("diver", s) for s in (334, 336, 338, 340, 344, 360, 616, 620, 622, 624)],
 "diver_stairwell": [("diver", s) for s in (370, 372, 374, 396, 398, 414, 416, 420, 424, 430)],
 "diver_lobby": [("diver", s) for s in (460, 462, 480, 482, 484, 486, 488, 490)],
 "diver_service_corridor": [("diver", s) for s in (508, 510, 512, 514, 520, 522)],
 "diver_red_emergency": [("diver", s) for s in (560, 562, 564, 570, 572, 574, 592, 594, 596, 600)],
 "diver_rule_card": [("diver", s) for s in (120, 200, 202, 292, 293, 364, 366, 458, 558, 682, 684)],
 "diver_document": [("diver", s) for s in (252, 254, 264, 266, 526)],
 "diver_face_closeup": [("diver", s) for s in (5, 44, 100, 186, 548, 550, 590)],
 "hazmat_exterior_night": [("hazmat", s) for s in (0, 1, 2, 24, 25, 38, 40, 44, 50, 52, 126, 128, 130, 428, 430, 442, 444)],
 "hazmat_bright_aisle": [("hazmat", s) for s in (8, 9, 22, 23, 34, 36, 64, 68, 70, 72, 120, 122, 124, 184, 186, 250, 252, 262, 264)],
 "hazmat_dim_emergency": [("hazmat", s) for s in (74, 75, 76, 312, 238)],
 "hazmat_rule_card": [("hazmat", s) for s in (83, 84, 135, 136, 196, 254, 318, 388, 460, 462)],
 "hazmat_face_closeup": [("hazmat", s) for s in (48, 62, 112, 154, 216, 228, 236, 334, 336, 358, 454)],
}

def palette(im, k=6):
    sm = cv2.resize(im, (160, 80), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
    _, lab, cen = cv2.kmeans(sm, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    w = np.bincount(lab.ravel(), minlength=k) / len(lab)
    return [(cen[i][::-1], float(w[i])) for i in np.argsort(-w)]

def vignette(meanf):
    g = cv2.cvtColor(meanf.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = g.shape; yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / np.sqrt(2)  # 1 = corner
    c = g[r < 0.15].mean()
    return [round(float(g[(r > q - 0.04) & (r < q + 0.04)].mean() / c), 2) for q in (0.4, 0.6, 0.8, 0.95)]

def main(d, out, sd):
    res = {}
    for fam, lst in FAM.items():
        L, P, M, thumbs = [], [], [], []
        for name, s in lst:
            im = cv2.imread(f"{d}/{name}/f1/f{s:04d}.jpg")
            if im is None: continue
            thumbs.append(cv2.resize(im, (214, 120), interpolation=cv2.INTER_AREA))
            im = im[: int(480 * 0.86)]
            M.append(im.astype(np.float32))
            g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
            sat = hsv[..., 1]; hue = hsv[..., 0][sat > 80]
            hm = float(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(hue.astype(float) * 2)))))) % 360 if len(hue) else np.nan
            L.append([*np.percentile(g, [1, 5, 50, 95, 99.5]), g.std(), sat.mean(), np.percentile(sat, 90), hm])
            P += palette(im, 5)
        L = np.array(L, float); mL = np.nanmedian(L, 0)
        cols = np.array([c for c, _ in P], np.float32); ws = np.array([w for _, w in P])
        rep = np.repeat(cols, np.maximum(1, (ws * 20).astype(int)), 0)
        _, lab, cen = cv2.kmeans(rep, 7, None, (3, 30, 0.5), 4, cv2.KMEANS_PP_CENTERS)
        cnt = np.bincount(lab.ravel(), minlength=7); o = np.argsort(-cnt)
        pal = ["#%02x%02x%02x" % tuple(int(v) for v in cen[i]) for i in o]
        vg = vignette(np.mean(M, 0))
        res[fam] = dict(n=len(L), p1=mL[0], p5=mL[1], p50=mL[2], p95=mL[3], p995=mL[4], contrast=mL[5], sat_mean=mL[6],
                        sat_p90=mL[7], hue_sat_px_deg=mL[8], vignette_r40_60_80_95=vg, palette=pal)
        print(f"{fam:24s} n{len(L):2d} luma {mL[0]:.0f}/{mL[1]:.0f}/{mL[2]:.0f}/{mL[3]:.0f}/{mL[4]:.0f} std {mL[5]:.0f} sat {mL[6]:.0f}/{mL[7]:.0f} hue {mL[8]:.0f} vig {vg} | {' '.join(pal)}")
        strip = np.hstack(thumbs[:10]) if thumbs else None
        if strip is not None: cv2.imwrite(f"{sd}/fam_{fam}.jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 85])
    # whole-video mean-frame vignette
    for name, nmax in (("diver", 685), ("hazmat", 465)):
        acc = np.zeros((int(480 * 0.86), 854, 3), np.float64)
        for s in range(0, nmax, 3): acc += cv2.imread(f"{d}/{name}/f1/f{s:04d}.jpg")[: int(480 * 0.86)]
        vg = vignette(acc / len(range(0, nmax, 3))); res[f"{name}_whole_video_vignette"] = vg
        print(name, "whole-video mean-frame vignette r=.4/.6/.8/.95:", vg)
    json.dump(res, open(out, "w"), indent=1, default=float)

if __name__ == "__main__":
    main(*sys.argv[1:4])
