"""Find peephole frames (dark ring around bright disc) in 1 fps frames; fit circle; measure ring/vignette radial profile."""
import numpy as np, cv2, glob, sys
va=sys.argv[1]
for name in ['fire','hotel','class']:
    fs=sorted(glob.glob(f'{va}/{name}/f*.jpg')); hits=[]
    for k,f in enumerate(fs):
        im=cv2.imread(f,0)
        if im is None: continue
        if im[:, :200].mean()<8 and im[:, -200:].mean()<8 and im[200:520,500:780].mean()>25:
            hits.append(k)
    print(name,'peephole-like seconds',len(hits),hits[:60])
