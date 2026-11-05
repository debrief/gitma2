import json, math, sys, numpy as np
from tma2.segment import score as sc
from tma2.eval.slices import zig_band
from tma2.segment.metrics import gap_recovered
z = np.load(sys.argv[1], allow_pickle=False)
ords, ks = z["ordinal"], z["k"]
names = [k[4:] for k in z.files if k.startswith("err_")]
E = {n: z[f"err_{n}"][:, 0] for n in names}
meta = {}
for j, m, *_ in sc.iter_selected("data/gs-test/test.f32pack", 0, 5059):
    meta[j] = m
def q(v): v = np.where(np.isfinite(v), v, np.inf); return float(np.quantile(v, 0.5, method="inverted_cdf")) if v.size else math.nan
zb = np.array([zig_band(abs(math.degrees(float(meta[o]["parameters"]["zig_angle_rad"])))) for o in ords])
tz = np.array([f"zig+{round((k - int(meta[o]['zig_index'])) * float(meta[o]['parameters']['dt_s']) / 60)}min" for o, k in zip(ords, ks)])
segs = [n for n in names if n not in ("one_leg", "oracle", "imm", "ekf", "naive")]
out = {"finite_rows": {}, "zig_band": {}, "time_since_zig": {}}
allfin = np.all([np.isfinite(E[n]) for n in names], axis=0)
onefin = np.isfinite(E["one_leg"])
for label, mask in (("all", np.ones_like(allfin)), ("one_leg_answers", onefin), ("every_estimator_answers", allfin)):
    one, ora = q(E["one_leg"][mask]), q(E["oracle"][mask]); nav = q(E["naive"][mask])
    out["finite_rows"][label] = {"rows": int(mask.sum()), **{n: {"range_median": q(E[n][mask]), "gap_recovered": gap_recovered(one, q(E[n][mask]), ora), "gap_from_naive": gap_recovered(nav, q(E[n][mask]), ora)} for n in segs}}
for key, vals in (("zig_band", zb), ("time_since_zig", tz)):
    for v in sorted(set(vals.tolist())):
        mask = vals == v
        one, ora = q(E["one_leg"][mask]), q(E["oracle"][mask])
        out[key][v] = {"rows": int(mask.sum()), **{n: {"range_median": q(E[n][mask]), "gross_rate": float(np.mean(~(E[n][mask] <= 0.5))), **({"gap_recovered": gap_recovered(one, q(E[n][mask]), ora)} if n in segs else {})} for n in names}}
json.dump(out, open(sys.argv[2], "w"), indent=2)
fr = out["finite_rows"]
for label in fr: print(label, fr[label]["rows"], {n: (round(fr[label][n]["gap_recovered"], 3), round(fr[label][n]["gap_from_naive"], 3)) for n in segs})
for key in ("zig_band", "time_since_zig"):
    for v, c in out[key].items(): print(key, v, c["rows"], "C gap", round(c["C"]["gap_recovered"], 3), "L-C", round(c["L"]["gap_recovered"] - c["C"]["gap_recovered"], 4), "one", round(c["one_leg"]["range_median"], 3), "C", round(c["C"]["range_median"], 3))
