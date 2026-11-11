# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261112-tl-prior)
import json,glob,sys,numpy as np
D=sys.argv[1]
fs=sorted(glob.glob(D+'/retest-*.json'), key=lambda f:int(f.split('-')[-1][:-5]))
R=[]
for f in fs:
    rs=json.load(open(f)); d=np.load(f.replace('.json','.npz')); B=d['B']; per=d['per']; det=np.isfinite(B[:,0])&(B[:,0]<0.5)
    for i,r in enumerate(rs):
        k=det&(per==i); r['det']=int(k.sum())
        for n in d.files:
            if n not in('B','per'): r['e_'+n]=float(np.median(d[n][k,0])) if k.any() else np.nan
        R.append(r)
R=[r for r in R if r['det']>0]
print("periods",len(R))
for n in ('arc-true','truth-fit','chord-c2','retest-c2','retest-c2-k','retest-none','retest-none-k'):
    e=np.array([r['e_'+n] for r in R]); print(f"{n:14s} median period err {np.nanmedian(e):.4f}  over10% {np.mean(e>0.1):.2f}")
for key,nm in (('retest_c2','retest-c2-k'),('retest_none','retest-none-k')):
    rows=[r for r in R if key in r and 'ev' in r[key]]
    d=np.array([r['truth_ev']['total']-r[key]['ev']['total'] for r in rows])
    parts={p:np.array([r['truth_ev'][p]-r[key]['ev'][p] for r in rows]) for p in ('fit','legs','changes','state','occam')}
    bad=np.array([r['e_'+nm]>2*max(r['e_truth-fit'],0.01) for r in rows])
    print(key,"n",len(rows),"truth minus retest log evidence: median",round(float(np.median(d)),1),"share truth wins by >3:",round(float((d>3).mean()),2),"share retest wins by >3:",round(float((d<-3).mean()),2))
    print("   where the retest's error is over twice the truth fit's (n=%d): median diff %.1f, truth wins by >3 in %.2f, retest wins by >3 in %.2f"%(bad.sum(),np.median(d[bad]),(d[bad]>3).mean(),(d[bad]<-3).mean()))
    print("   parts (median, bad periods):",{p:round(float(np.median(v[bad])),1) for p,v in parts.items()})
    print("   elsewhere (n=%d): median diff %.1f"%((~bad).sum(),np.median(d[~bad])))
# oracle selection: of truth, retest-c2-k, retest-none-k pick highest evidence between the two retests
sel=[];best=[]
for r in R:
    c=[(r[k]['ev']['total'],r['e_'+n]) for k,n in (('retest_c2','retest-c2-k'),('retest_none','retest-none-k')) if k in r and 'ev' in r[k]]
    if c: sel.append(max(c)[1]); best.append(min(x[1] for x in c))
print("pick the re-test history with the higher evidence: median err %.4f; the better of the two in hindsight: %.4f"%(np.median(sel),np.median(best)))
