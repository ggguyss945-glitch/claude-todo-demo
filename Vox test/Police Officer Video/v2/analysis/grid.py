"""Grid of crops: args out tilew spec... where spec=name:t[:x0,y0,x1,y1 in 1280x720]"""
import sys, numpy as np, cv2
va='/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work/pov2/va'
out,tw,cols=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); tiles=[]
for sp in sys.argv[4:]:
    p=sp.split(':'); im=cv2.imread(f'{va}/{p[0]}/f{int(p[1])+1:04d}.jpg')
    if len(p)>2: x0,y0,x1,y1=map(int,p[2].split(',')); im=im[y0:y1,x0:x1]
    th=int(tw*im.shape[0]/im.shape[1]); im=cv2.resize(im,(tw,th),interpolation=cv2.INTER_AREA)
    cv2.putText(im,f'{p[0][0]}{p[1]}',(3,16),0,0.5,(0,255,255),1); tiles.append(im)
H=max(t.shape[0] for t in tiles); tiles=[np.pad(t,((0,H-t.shape[0]),(0,0),(0,0))) for t in tiles]
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]),[1,85])
