# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-arc)
import sys, glob, json, numpy as np

Q = 0.6744897501960817
fs = sorted(glob.glob(sys.argv[1]))
names = None
E = {}
B = []
per = []
off = 0
for f in fs:
    d = np.load(f)
    names = [k for k in d.files if k not in ("B", "per")]
    B.append(d["B"])
    per.append(d["per"] + off)
    off += int(d["per"].max()) + 1
    for n in names:
        E.setdefault(n, []).append(d[n])
B = np.concatenate(B)
per = np.concatenate(per)
det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
E = {n: np.concatenate(v) for n, v in E.items()}
print(
    "periods",
    off,
    "determined rows",
    int(det.sum()),
    "periods with determined rows",
    len(set(per[det])),
)
rng = np.random.default_rng(0)
ids = np.array(sorted(set(per[det])))


def pm(e):
    return np.array(
        [
            np.median(e[det & (per == i), 0])
            if np.isfinite(e[det & (per == i), 0]).all()
            else np.inf
            for i in ids
        ]
    )


out = {}
for n, e in E.items():
    ok = det & np.isfinite(e[:, 0])
    m = pm(e)
    out[n] = dict(
        eff=[round(float(np.median(e[ok, c] / B[ok, c]) / Q), 2) for c in range(3)],
        med_rows=round(float(np.median(e[ok, 0])), 4),
        med_period=round(float(np.median(m)), 4),
        p90_period=round(float(np.quantile(m, 0.9)), 4),
        over10pct=round(float((m > 0.1).mean()), 3),
        course_med=round(float(np.median(e[ok, 1])), 2),
        speed_med=round(float(np.median(e[ok, 2])), 2),
    )
    print(f"{n:14s}", out[n])


def ratio(a, b):
    ma, mb = pm(E[a]), pm(E[b])
    bs = []
    for _ in range(2000):
        k = rng.integers(0, len(ids), len(ids))
        bs.append(np.median(ma[k]) / np.median(mb[k]))
    return round(float(np.median(ma) / np.median(mb)), 2), [
        round(float(x), 2) for x in np.quantile(bs, [0.025, 0.975])
    ]


for a, b in (
    ("chord-true", "arc-true"),
    ("chord-c2", "arc-c2"),
    ("arc-c2", "arc-true"),
    ("chord-c2", "chord-true"),
    ("arc-true", "arc-kind-true"),
):
    if a in E and b in E:
        print(a, "/", b, ratio(a, b))
