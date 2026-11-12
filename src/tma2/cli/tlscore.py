"""``tma2-tlscore``: Gate T's readings from the shards of one run (spec 013). Merges each
split's shards, summarises every system (median over periods of the period's median error on
determined rows; efficiency against the bound), the ratios the gate reads, the candidate
tracks' reliability, and the checks. Exit 3 when ``--gate`` is given and a check fails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-tlscore", description=__doc__)
    ap.add_argument("--shards", required=True, help="directory of <split>.<shard>.npz/.json")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gate", action="store_true", help="exit 3 if a pass/fail check fails")
    a = ap.parse_args(argv)
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    import numpy as np

    from tma2.segment.gate import sha256_file
    from tma2.timelate.gate import candidate_reading, period_medians, ratio, verdicts
    from tma2.timelate.score import COLS, UNDETERMINED, Q

    plan = json.loads(Path(a.plan).read_text())
    digest = sha256_file(a.plan)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    reading: dict[str, Any] = {}
    for split in plan["splits"]:
        files = sorted(
            Path(a.shards).glob(f"{split}.*.json"), key=lambda p: int(p.name.split(".")[1])
        )
        if not files:
            continue
        periods: list[dict[str, Any]] = []
        headers = []
        arrays: dict[str, list[np.ndarray]] = {}
        for f in files:
            j = json.loads(f.read_text())
            if j["header"]["plan_sha256"] != digest:
                raise SystemExit(f"{f}: made with another plan ({j['header']['plan_sha256'][:8]})")
            headers.append(j["header"])
            periods += j["periods"]
            z = np.load(f.with_suffix(".npz"))
            for k in z.files:
                arrays.setdefault(k, []).append(z[k])
        arr = {k: np.concatenate(v) for k, v in arrays.items()}
        if len({r["ordinal"] for r in periods}) != len(periods):
            raise SystemExit(f"{split}: a period appears in two shards")
        period, bound = arr["period"], arr["bound"].astype(np.float64)
        det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
        systems: dict[str, Any] = {}
        meds: dict[str, np.ndarray] = {}
        for k in sorted(arr):
            if not k.startswith("err_"):
                continue
            name, e = k[4:], arr[k].astype(np.float64)
            _ids, m = period_medians(e, period, bound)
            meds[name] = m
            rec: dict[str, Any] = {
                "median_period_range": float(np.median(m)) if m.size else float("nan"),
                "periods_over_10pct": float(np.mean(m > 0.1)) if m.size else float("nan"),
                "rows_without_state": int((det & ~np.isfinite(e[:, 0])).sum()),
            }
            for c, col in enumerate(COLS[:3]):
                ok = det & np.isfinite(e[:, c]) & np.isfinite(bound[:, c]) & (bound[:, c] > 0)
                rec[f"median_rows_{col}"] = float(np.median(e[ok, c])) if ok.any() else float("nan")
                rec[f"efficiency_{col.split('_')[0]}"] = (
                    float(np.median(e[ok, c] / bound[ok, c]) / Q) if ok.any() else float("nan")
                )
            systems[name] = rec
        ratios = {
            "c2_over_search": ratio(meds["c2"], meds["search"]),
            "c2_over_search_none": ratio(meds["c2"], meds["search-none"]),
            "search_over_truth": ratio(meds["search"], meds["truth-map"]),
        }
        reading[split] = {
            "periods": len(periods),
            "periods_with_determined_rows": int(meds["c2"].size),
            "scored_rows": int(period.size),
            "determined_rows": int(det.sum()),
            "dataset_digest": sorted({h["dataset_digest"] for h in headers}),
            "seed": sorted({h["seed"] for h in headers}),
            "search_code_sha256": sorted({h["search_code_sha256"] for h in headers}),
            "git_commit": sorted({h["git_commit"] for h in headers}),
            "git_dirty": any(h["git_dirty"] for h in headers),
            "systems": systems,
            "ratios": ratios,
            "candidates": candidate_reading(periods, float(plan["temperature"]), int(plan["top"])),
        }
        payload: dict[str, Any] = dict(arr)
        np.savez_compressed(out / f"{split}.errors.npz", **payload)
        (out / f"{split}.periods.json").write_text(json.dumps(periods) + "\n")
    if "man2" not in reading:
        raise SystemExit("no man2 shards")
    checks = verdicts(reading, plan["criteria"])
    summary = {
        "plan": a.plan,
        "plan_sha256": digest,
        "scorer_git_commit": g.commit,
        "scorer_git_dirty": g.dirty,
        "criteria": plan["criteria"],
        "checks": checks,
        "splits": reading,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    for split, r in reading.items():
        print(f"{split}: {r['periods']} periods, {r['periods_with_determined_rows']} scored")
        for name, s in r["systems"].items():
            print(
                f"  {name:12s} median {s['median_period_range']:.4f}  over 10% "
                f"{s['periods_over_10pct']:.2f}  eff {s['efficiency_range']:.2f} "
                f"{s['efficiency_course']:.2f} {s['efficiency_speed']:.2f}"
            )
        for name, v in r["ratios"].items():
            print(f"  {name}: {v['value']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}]")
        c = r["candidates"]
        print(f"  candidates: {json.dumps({k: v for k, v in c.items() if k != 'bins'})}")
    failed = [k for k, v in checks.items() if v.get("pass") is False]
    for k, v in checks.items():
        print(k, json.dumps(v))
    return 3 if a.gate and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
