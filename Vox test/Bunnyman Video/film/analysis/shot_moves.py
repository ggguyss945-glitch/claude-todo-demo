"""Per-shot camera move stats: total zoom, profile (ease), share of shots with moves. Args: va_dir"""
import sys, json, numpy as np
va = sys.argv[1]
for name in ['fire','hotel','class']:
    R = json.load(open(f'{va}/motion_{name}.json')); n=len(R)
    z = np.array([r.get('zoom', 0) for r in R]); tx = np.array([r.get('tx', 0) for r in R])*4; ty=np.array([r.get('ty',0) for r in R])*4
    cuts = (np.loadtxt(f'{va}/cuts2_{name}.txt')*6).astype(int)
    edges = np.concatenate([[0], cuts, [n]])
    tot=[]; prof=[]; pantot=[]; kinds={'push':0,'pull':0,'pan':0,'static':0,'push+pan':0}
    for a,b in zip(edges[:-1],edges[1:]):
        a2,b2=a+2,b-1
        if b2-a2<6: continue
        zz=z[a2:b2]; zz=np.clip(zz,-0.05,0.05)
        Z=np.exp(np.sum(np.log1p(zz)))-1; P=np.hypot(tx[a2:b2].sum(),ty[a2:b2].sum())
        tot.append(Z*100); pantot.append(P)
        dur=(b2-a2)/6
        push = abs(Z)*100/dur>0.8; pan=P/dur>8
        k='push+pan' if (push and pan) else 'push' if (push and Z>0) else 'pull' if push else 'pan' if pan else 'static'
        kinds[k]+=1
        if Z>0.04 and b2-a2>=15:
            c=np.cumsum(zz); c/=c[-1] if c[-1]!=0 else 1
            prof.append(np.interp(np.linspace(0,1,6),np.linspace(0,1,len(c)),c))
    tot=np.array(tot); N=len(tot)
    print(name, 'shots>=1.5s:',N, {k:round(v/N,2) for k,v in kinds.items()})
    print('  total zoom per shot %% p25/50/75/90/max', np.round(np.percentile(tot,[25,50,75,90,100]),1), ' pan px@1280 p50/90', np.round(np.percentile(pantot,[50,90]),0))
    if prof: print('  mean cumulative push profile at 0,.2,.4,.6,.8,1:', np.round(np.mean(prof,0),2), 'n', len(prof))
