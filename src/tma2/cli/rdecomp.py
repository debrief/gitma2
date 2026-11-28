"""tma2-rdecomp: spec 038's readings of one scoring run (``regress.decomp``).

Reads ``errors.npz`` of a ``tma2-gh`` run, the scored split (true target changes, row times),
optionally the mismatch truth (whether the first bearing is an outlier) and C″'s dumped
segmentations (whether its structure was right at the first scored row). Writes ``decomp.json``
and ``decomp-logs.npz`` (per-engagement log ratios, for comparisons between splits).
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-rdecomp", description=__doc__)
    ap.add_argument("--errors", required=True)
    ap.add_argument("--truth", required=True, help="the scored split's f32pack")
    ap.add_argument("--names", required=True, help="JSON: comparator, regressors, own, ...")
    ap.add_argument("--condition", default="")
    ap.add_argument("--split", default="")
    ap.add_argument("--mismatch-truth", help="the split's truth side file (first-bearing slice)")
    ap.add_argument("--segments", help="glob of C″'s dumped segmentations (structure slice)")
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import numpy as np

    from tma2.data.f32pack import read_pack_header
    from tma2.regress import decomp as dc
    from tma2.regress.mread import COLS, system_summary
    from tma2.segment import score as sc

    txt = a.names
    names: dict[str, Any] = json.loads(
        txt if txt.lstrip().startswith("{") else Path(txt).read_text()
    )
    z = np.load(a.errors)
    errs = {k[4:]: z[k] for k in z.files if k.startswith("err_")}
    ordinal, ks = z["ordinal"], z["k"]
    bound = z["bound"] if "bound" in z.files else None
    need = [names["comparator"], *names["regressors"]]
    missing = [s for s in need if s not in errs]
    if missing:
        raise SystemExit(f"not in {a.errors}: {', '.join(missing)}")
    optional = [
        *names.get("unchanged", []),
        *names.get("hybrids", []),
        *names.get("hardened", []),
        *(names[k] for k in ("own", "own_hybrid", "true") if names.get(k)),
    ]
    absent = [s for s in optional if s not in errs]
    named = [s for s in [*need, *optional] if s in errs]

    index_start = read_pack_header(a.truth).index_start
    outlier = np.load(a.mismatch_truth)["outlier"] if a.mismatch_truth else None
    want = set(np.unique(ordinal).tolist())
    since: dict[tuple[int, int], float] = {}
    first_wild: dict[int, bool] = {}
    metas: dict[int, dict[str, Any]] = {}
    for j, m, _own, _tgt, obs in sc.iter_selected(a.truth, 0, 1 << 30):
        if j not in want:
            continue
        metas[j] = m
        dt = float(m["parameters"]["dt_s"])
        for k in ks[ordinal == j].tolist():
            since[(j, k)] = dc.since_last_change(m["manoeuvres"], int(k), dt)
        if outlier is not None:
            v = np.flatnonzero(obs[:, 2] > 0) if obs.shape[1] > 2 else np.arange(obs.shape[0])
            first_wild[j] = bool(v.size and outlier[int(m["index"]) - index_start, v[0]])
    band = np.array(
        [dc.since_band(since[(int(u), int(k))]) for u, k in zip(ordinal, ks, strict=True)]
    )
    k0 = {int(u): int(ks[ordinal == u].min()) for u in want}
    later = np.array([int(k) > k0[int(u)] for u, k in zip(ordinal, ks, strict=True)])

    res: dict[str, Any] = {
        "record": "gain-decomposition-reading",
        "condition": a.condition,
        "split": a.split,
        "rows": int(ordinal.size),
        "scenarios": len(want),
        "names": names,
        "absent": absent,
        "since_bands_s": list(dc.SINCE_BANDS_S),
        "all": dc.comparisons(errs, names, ordinal, None, a.resamples),
        "slices": {},
    }
    rows_common = dc.common_rows(errs, named)
    res["common_rows"] = {
        "rows": int(rows_common.sum()),
        **dc.comparisons(errs, names, ordinal, rows_common, a.resamples),
    }
    res["slices"]["since_change"] = [
        {"rows": int((band == b).sum()), **dc.comparisons(errs, names, ordinal, band == b)}
        for b in range(len(dc.SINCE_BANDS_S) + 1)
    ]
    if outlier is not None:
        fw = dc.by_engagement(first_wild, ordinal, False).astype(bool)
        res["slices"]["first_bearing_wild"] = {
            str(v): {
                "scenarios": int(np.unique(ordinal[fw == v]).size),
                **dc.comparisons(errs, names, ordinal, fw == v, a.resamples),
            }
            for v in (False, True)
            if (fw == v).any()
        }
    if a.segments:
        right: dict[int, bool] = {}
        for path in sorted(glob.glob(a.segments)):
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    j = int(r["ordinal"])
                    if j in k0 and int(r["prefix_row"]) == k0[j]:
                        declared = [
                            (int(i["start_index"]), int(i["end_index"]))
                            for i in r["intervals"]
                            if i["kind"] == "transition"
                        ]
                        dt = float(metas[j]["parameters"]["dt_s"])
                        right[j] = dc.structure_right(declared, metas[j]["manoeuvres"], k0[j], dt)
        if right:
            known = dc.by_engagement({j: True for j in right}, ordinal, False).astype(bool)
            ok = dc.by_engagement(right, ordinal, False).astype(bool)
            res["slices"]["structure_at_first_row"] = {
                "classified": len(right),
                "right_share": float(np.mean(list(right.values()))),
                "match_tolerance_s": dc.MATCH_TOL_S,
                **{
                    label: {
                        "scenarios": int(np.unique(ordinal[known & later & (ok == v)]).size),
                        **dc.comparisons(
                            errs, names, ordinal, known & later & (ok == v), a.resamples
                        ),
                    }
                    for label, v in (("right", True), ("wrong", False))
                    if (known & later & (ok == v)).any()
                },
            }
    res["systems"] = {n: system_summary(errs[n], ordinal, bound) for n in sorted(errs)}
    res["systems_common_rows"] = {
        n: system_summary(errs[n], ordinal, bound, rows_common) for n in named
    }
    if bound is not None:
        res["by_bound_third"] = {}
        for c, col in enumerate(COLS):
            b = bound[:, c]
            fin = np.isfinite(b) & (b > 0)
            cuts = np.quantile(b[fin], [1 / 3, 2 / 3])
            third = np.searchsorted(cuts, b, side="right")
            res["by_bound_third"][col] = {
                "cuts": [float(v) for v in cuts],
                "thirds": [
                    {
                        n: system_summary(errs[n], ordinal, bound, fin & (third == q))[col]
                        for n in named
                    }
                    for q in range(3)
                ],
            }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    arrays: dict[str, np.ndarray] = {}
    for c, col in enumerate(COLS):
        lg = dc.pooled_logs(errs, names["comparator"], list(names["regressors"]), ordinal, c)
        arrays[f"ordinal_{col}"] = np.array(sorted(lg), dtype=np.int64)
        arrays[f"log_{col}"] = np.array([lg[u] for u in sorted(lg)])
    np.savez_compressed(out.with_name("decomp-logs.npz"), **arrays)  # type: ignore[arg-type]
    for g, r in res["all"]["ratios"]["range"].items():
        if r.get("scenarios"):
            print(
                f"{names['comparator']} / {g}: {r['ratio']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]"
                f" n={r['scenarios']}"
            )
    for kind in ("gap_closed", "prior_share"):
        for g, r in res["all"][kind]["range"].items():
            if r.get("defined"):
                print(f"{kind} {g}: {r['share']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
