"""``tma2-rmread``: paired readings of regressors against a control on one scoring run (spec
037): control ÷ system per scenario, system summaries, and the coverage of stated intervals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-rmread", description=__doc__)
    ap.add_argument("--errors", required=True, help="errors.npz of the scoring run")
    ap.add_argument("--truth", required=True, help="the scored split (row timestamps)")
    ap.add_argument("--systems", required=True, help="comma-separated: the systems compared")
    ap.add_argument("--controls", required=True, help="comma-separated: each is a numerator")
    ap.add_argument(
        "--stated", nargs="*", default=[], metavar="NAME=PATH", help="rows with intervals"
    )
    ap.add_argument("--temperature", help="interval-fit.json: score the head against the control")
    ap.add_argument("--condition", default="")
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import numpy as np

    from tma2.regress import mread
    from tma2.sim.geometry import f32

    z = np.load(a.errors)
    errs = {k[4:]: z[k] for k in z.files if k.startswith("err_")}
    ordinal, ks, true_range = z["ordinal"], z["k"], z["true_range_m"]
    bound = z["bound"] if "bound" in z.files else None
    systems = [s for s in a.systems.split(",") if s]
    controls = [s for s in a.controls.split(",") if s]
    missing = [s for s in systems + controls if s not in errs]
    if missing:
        raise SystemExit(f"not in {a.errors}: {', '.join(missing)}")
    cuts = np.quantile(true_range, [1 / 3, 2 / 3])
    band = np.searchsorted(cuts, true_range, side="right")
    res: dict[str, Any] = {
        "record": "regressor-mismatch-reading",
        "condition": a.condition,
        "rows": int(ordinal.size),
        "scenarios": int(np.unique(ordinal).size),
        "range_band_cuts_m": [float(c) for c in cuts],
        "systems": {n: mread.system_summary(e, ordinal, bound) for n, e in sorted(errs.items())},
        "paired": {},
        "paired_by_range_band": {},
        "coverage": {},
        "interval_score": {},
        "temperature_coverage": {},
    }
    terms: dict[str, dict[str, Any]] = {}
    temp = json.loads(Path(a.temperature).read_text())["temperature"] if a.temperature else None
    for c in controls:
        res["paired"][c] = mread.paired(errs, c, systems, ordinal, resamples=a.resamples)
        res["paired_by_range_band"][c] = [
            mread.paired(errs, c, systems, ordinal, band == b, a.resamples)["range"]
            for b in range(3)
        ]
    if a.stated:
        from tma2.segment import score as sc

        t_of: dict[tuple[int, float], int] = {}
        want = {int(u): set(ks[ordinal == u].tolist()) for u in np.unique(ordinal)}
        for j, _m, own, _tgt, _obs in sc.iter_selected(a.truth, 0, 1 << 30):
            for k in want.get(j, ()):
                t_of[(j, f32(float(own[k, 0])))] = int(k)
        for spec in a.stated:
            name, _, path = spec.partition("=")
            stated: dict[tuple[int, int], dict[str, float]] = {}
            with open(path, encoding="utf-8") as fh:
                fh.readline()
                for line in fh:
                    rec = json.loads(line)
                    for x in rec["rows"]:
                        k = t_of.get((int(rec["ordinal"]), float(x["timestamp_s"])))
                        if k is not None:
                            stated[(int(rec["ordinal"]), k)] = x
            hz = mread.interval_rows(stated, ordinal, ks, errs[name], true_range)
            terms[name] = mread.row_terms(stated, ordinal, ks, errs[name], true_range)
            res["coverage"][name] = {
                col: {
                    "all": mread.coverage(h, zz, ordinal, resamples=a.resamples),
                    "by_range_band": [
                        mread.coverage(
                            h[band == b], zz[band == b], ordinal[band == b], resamples=a.resamples
                        )
                        for b in range(3)
                    ],
                }
                for col, (h, zz) in hz.items()
            }
            if temp is not None:
                tm = terms[name]
                th = mread.temperature_half(temp, tm["est_range_m"])
                res["interval_score"][name] = {}
                res["temperature_coverage"][name] = {}
                for c, col in enumerate(mread.COLS):
                    e_c, h_c = tm["err"][:, c], tm["half"][:, c]
                    head = mread.winkler(e_c, h_c)
                    ctl = np.where(np.isfinite(h_c), mread.winkler(e_c, th[:, c]), np.nan)
                    res["interval_score"][name][col] = mread.score_ratio(
                        head, ctl, ordinal, a.resamples
                    )
                    okc = np.isfinite(e_c)
                    res["temperature_coverage"][name][col] = float(np.mean(e_c[okc] <= th[okc, c]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    if terms:  # per-row terms, for fitting scales on validation and pooling over conditions
        arrays = {"ordinal": ordinal}
        for name, tm in terms.items():
            for key, v in tm.items():
                arrays[f"{name}__{key}"] = v
        np.savez_compressed(out.with_name("interval-rows.npz"), **arrays)
    for c in controls:
        for s, r in res["paired"][c]["range"].items():
            if r.get("scenarios"):
                iv = f"[{r['lo']:.3f}, {r['hi']:.3f}]"
                print(f"{c} / {s}: {r['ratio']:.3f} {iv} n={r['scenarios']} {r['outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
