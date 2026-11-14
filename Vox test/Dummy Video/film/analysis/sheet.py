"""Contact sheet with time labels from 1 fps frames. Args: va_dir name t0 t1 cols rows out [tilew]"""
import sys, numpy as np, cv2
va,name,t0,t1,cols,rows,out=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]),sys.argv[7]
tw=int(sys.argv[8]) if len(sys.argv)>8 else 200; th=tw*9//16
ts=np.linspace(t0,t1,cols*rows); tiles=[]
for t in ts:
    im=cv2.imread(f'{va}/{name}/f{int(t)+1:04d}.jpg'); im=cv2.resize(im,(tw,th),interpolation=cv2.INTER_AREA)
    cv2.putText(im,f'{int(t)}',(3,14),0,0.45,(0,255,255),1); tiles.append(im)
g=np.vstack([np.hstack(tiles[r*cols:(r+1)*cols]) for r in range(rows)]); cv2.imwrite(out,g,[1,82])
