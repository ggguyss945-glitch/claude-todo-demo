"""Contact sheets from 1 fps frames: python3 -I sheets.py <ref_dir> <name> <step_s> <t0> <t1> <cols> <thumb_w> <out.jpg>"""
import sys, cv2, numpy as np
ref, name, step, t0, t1, cols, tw, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), sys.argv[8]
th = int(tw * 480 / 854)
ts = np.arange(t0, t1, step)
rows = int(np.ceil(len(ts) / cols))
sheet = np.full((rows * (th + 2), cols * (tw + 2), 3), 255, np.uint8)
for k, t in enumerate(ts):
    im = cv2.imread(f"{ref}/data/{name}/f1/f{int(t):04d}.jpg")
    if im is None: continue
    im = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
    lab = f"{int(t)//60}:{int(t)%60:02d}"
    cv2.putText(im, lab, (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(im, lab, (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
    r, c = divmod(k, cols)
    sheet[r * (th + 2):r * (th + 2) + th, c * (tw + 2):c * (tw + 2) + tw] = im
cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out, sheet.shape)
