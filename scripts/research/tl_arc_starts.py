# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-arc)
import sys, numpy as np, torch
torch.set_default_dtype(torch.float64)
from tma2.timelate.arc import fit_arc, fit_arc_search, start_from_track, arc_states
from tma2.timelate.periods import iter_periods
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors, Q
from tma2.timelate.systems import solve_systems, c_parameters
p, c2 = c_parameters("configs/gateh/gh-a.json")
ps = list(iter_periods(sys.argv[1] + "/train.f32pack", 0, int(sys.argv[2]), whole=sys.argv[3]=="whole"))
res = solve_systems(ps, ["reference"], p, c2)
E={"chord":[], "arc-chordstart":[], "arc-truthstart":[], "truthmodel":[],"arc-multi":[],"arc2-search":[]}; B=[]
for i,x in enumerate(ps):
    a,b=x.first,x.first+x.rows
    t=x.own[a:b,0].astype(float)-float(x.own[a,0]); ox=x.own[a:b,1].astype(float); oy=x.own[a:b,2].astype(float)
    z=x.obs[a:b,1].astype(float); v=x.obs[a:b,2]!=0; sig=float(x.meta["parameters"]["noise_sigma_rad"])
    tr=truth_rows(x); B.append(period_bound(x))
    sp=[s for s in x.spans() if s["end_index"]>s["start_index"]]
    spans=np.array([[t[max(s["start_index"]-1,0)],t[s["end_index"]]] for s in sp]).reshape(-1,2)
    kinds=[s["kind"] for s in sp]
    tf=np.array([[k in (0,2,"course","both"), k in (1,2,"speed","both")] for k in kinds]).reshape(-1,2)
    ref=res["reference"][i].states
    truth_track=np.stack([tr[:,0],tr[:,1],tr[:,3]*np.sin(tr[:,2]),tr[:,3]*np.cos(tr[:,2])],axis=1)
    tht=start_from_track(truth_track,t,spans); tht[4:][~tf.reshape(-1)]=0
    # how well does the arc model reproduce the truth itself?
    E["truthmodel"].append(row_errors(arc_states(tht,t,spans),tr))
    ft=fit_arc(t,ox,oy,z,v,sig,spans,tht,tf)
    thc=start_from_track(ref,t,spans); thc[4:][~tf.reshape(-1)]=0
    fc=fit_arc(t,ox,oy,z,v,sig,spans,thc,tf)
    best,nf=fit_arc_search(t,ox,oy,z,v,sig,spans,thc,tf)
    f2,nf2=fit_arc_search(t,ox,oy,z,v,sig,spans,start_from_track(ref,t,spans))
    E["arc2-search"].append(row_errors(f2.states,tr))
    E["arc-multi"].append(row_errors(best.states,tr)); print("   search",round(best.cost),nf,"arc2",round(f2.cost),nf2)
    E["chord"].append(row_errors(ref,tr)); E["arc-chordstart"].append(row_errors(fc.states,tr)); E["arc-truthstart"].append(row_errors(ft.states,tr))
    nv=int(v.sum())
    r0=((z-np.arctan2(tr[:,0]-tr[:,4],tr[:,1]-tr[:,5])+np.pi)%(2*np.pi)-np.pi)[v]/sig
    print(i,"rows",x.rows,"mans",len(sp),kinds,"cost truth",round(float(r0@r0)),"truthstart",round(ft.cost),ft.iterations,"chordstart",round(fc.cost),fc.iterations,"nvalid",nv,flush=True)
B=np.concatenate(B); det=np.isfinite(B[:,0])&(B[:,0]<0.5)
for n,e in E.items():
    e=np.concatenate(e); ok=det&np.isfinite(e[:,0])
    print(n,[round(float(np.median(e[ok,c]/B[ok,c])/Q),2) for c in range(3)], "med range",round(float(np.median(e[ok,0])),4),"med pos m",round(float(np.median(e[ok,3])),1))
