"""Grid of full-res 1 fps frames with labels: python3 -I grid.py <data_dir> <out.jpg> <cols> <name:sec> [<name:sec> ...] (sec may be fractional -> nearest second)"""
import sys, cv2, numpy as np
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3])
ims = []
for spec in sys.argv[4:]:
    n, s = spec.split(":"); s = int(round(float(s)))
    im = cv2.imread(f"{d}/{n}/f1/f{s:04d}.jpg")
    lab = f"{n} {s//60}:{s%60:02d}"
    cv2.putText(im, lab, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(im, lab, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
    ims.append(im)
h, w = ims[0].shape[:2]
rows = (len(ims) + cols - 1) // cols
g = np.full((rows * h, cols * w, 3), 255, np.uint8)
for k, im in enumerate(ims):
    r, c = divmod(k, cols); g[r * h:(r + 1) * h, c * w:(c + 1) * w] = im
cv2.imwrite(out, g, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out, g.shape)
