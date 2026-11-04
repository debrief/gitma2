"""tma2-gs: score segmentations (spec 005 contracts/cli.md; diagnostic mode).

    uv run tma2-gs --truth <split.f32pack> --start S --count N
        --segmentations NAME=<seg.ndjson> … [--glr-confirm WORK:CONFIG] --imm <frozen IMM>
        [--modes gap chord] --experiment <dir>

On the σ = 1° G5 rows of ordinals S … S + N − 1 (the rows a segmentation file covers must
include them), every segmenter is scored beside one leg (batch least squares), the oracle and
the frozen IMM, and GLR + confirm when given:
* **downstream:** median and P90 range (relative), course (°), speed (kt) error, all rows and
  settled rows; ratios to the IMM and to one leg with scenario-clustered paired 97.5% intervals;
* **gap recovered** in range, course and speed, with intervals, and each segmenter's difference
  from GLR + confirm (S2's measure);
* **segmentation:** contamination (median, P90), coverage, false-split rate, leg-count accuracy,
  boundary hits at ± 60 s and ± 3 min, from each segmentation's intervals.

Writes ``metrics.json`` and ``report.md``. Gate mode (``--decision``) is tasks T037.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

LEVEL = 0.975
RESAMPLES = 2000
COLS = ("range", "course_deg", "speed_kt")


def _q(v: np.ndarray, q: float) -> float:
    v = v[np.isfinite(v)] if np.isinf(v).all() else v
    return float(np.quantile(np.where(np.isfinite(v), v, np.inf), q, method="inverted_cdf"))


def read_segmentations(path: str) -> tuple[dict[str, Any], dict[tuple[int, int], list[Any]]]:
    from tma2.segment import KIND_CODE, Interval
    from tma2.types.generated.tma import SegmentKind

    with open(path, encoding="utf-8") as f:
        header = json.loads(f.readline())
        segs = {}
        for line in f:
            r = json.loads(line)
            segs[(int(r["ordinal"]), int(r["prefix_row"]))] = [
                Interval(
                    KIND_CODE[SegmentKind(iv["kind"])],
                    int(iv["start_index"]),
                    int(iv["end_index"]),
                    bool(iv["open"]),
                )
                for iv in r["intervals"]
            ]
    return header, segs


def main(argv: list[str] | None = None) -> int:
    import torch

    from tma2.eval.bootstrap import (
        bootstrap_clustered_quantile_ratio,
        bootstrap_clustered_statistic,
    )
    from tma2.eval.errors import Truth
    from tma2.eval.rows import settled_row
    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment import TRANSITION, default_parameters
    from tma2.segment import score as sc
    from tma2.types.generated.tma import SegmentParameters

    ap = argparse.ArgumentParser(prog="tma2-gs")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--segmentations", nargs="*", default=[], metavar="NAME=PATH")
    ap.add_argument(
        "--modes",
        nargs="*",
        choices=["gap", "chord"],
        help="score each segmentation in these hand-over modes (NAME-gap, NAME-chord) instead "
        "of the mode its header names",
    )
    ap.add_argument("--glr-confirm", metavar="WORK:CONFIG")
    ap.add_argument("--imm", required=True)
    ap.add_argument("--experiment", required=True)
    a = ap.parse_args(argv)
    torch.set_default_dtype(torch.float64)
    t0 = time.time()

    data, metas, truths = {}, {}, {}
    for j, m, own, tgt, obs in sc.iter_selected(a.truth, a.start, a.count):
        data[j] = bearing_data_from_arrays(m, own, obs)
        metas[j] = m
        truths[j] = Truth.from_block(m, own, tgt)
    rows = [
        sc.Row(j, k, settled_row(metas[j], k))
        for j in sorted(data)
        for k in sc.g5_rows(metas[j], data[j].n)
    ]
    cluster = np.array([r.ordinal for r in rows], dtype=np.int64)
    settled = np.array([r.settled for r in rows])
    layer = PhysicsLayer()
    errs: dict[str, np.ndarray] = {
        "one_leg": sc.layer_errors(layer, rows, data, metas, truths, sc.one_leg),
        "oracle": sc.layer_errors(layer, rows, data, metas, truths, sc.oracle),
        "imm": sc.imm_errors(rows, data, truths, a.imm),
    }
    print(f"references [{time.time() - t0:.0f} s]", flush=True)
    params: dict[str, SegmentParameters] = {}
    seg_ivs: dict[str, dict[tuple[int, int], list[tuple[int, int]]]] = {}
    for spec in a.segmentations:
        name, _, path = spec.partition("=")
        header, segs = read_segmentations(path)
        p = SegmentParameters.model_validate(header["parameters"])
        missing = [(r.ordinal, r.k) for r in rows if (r.ordinal, r.k) not in segs]
        if missing:
            print(
                f"{name}: {len(missing)} scored rows missing, e.g. {missing[:3]}", file=sys.stderr
            )
            return 2
        trs = {
            key: [(iv.start, iv.end) for iv in ivs if iv.kind == TRANSITION]
            for key, ivs in segs.items()
        }
        # each requested hand-over mode is scored as its own segmenter (R3, FR-031)
        for mode in a.modes or [str(p.mode)]:
            nm = name if not a.modes else f"{name}-{mode}"
            params[nm] = p.model_copy(update={"mode": mode})
            errs[nm] = sc.layer_errors(
                layer, rows, data, metas, truths, sc.from_segmentations(segs, mode)
            )
            seg_ivs[nm] = trs
            print(f"{nm} downstream [{time.time() - t0:.0f} s]", flush=True)
    if a.glr_confirm:
        work, _, cfg = a.glr_confirm.partition(":")
        acc = sc.load_confirmed(work, cfg)
        errs["glr_confirm"] = sc.layer_errors(layer, rows, data, metas, truths, sc.glr_confirm(acc))
        p0 = next(iter(params.values()), default_parameters())
        seg_ivs["glr_confirm"] = {
            (r.ordinal, r.k): sc.glr_confirm_intervals(acc.get(r.ordinal, []), r.k, p0.t_min_rows)
            for r in rows
        }
        print(f"glr_confirm downstream [{time.time() - t0:.0f} s]", flush=True)

    def summary(e: np.ndarray, mask: np.ndarray) -> dict[str, float]:
        out: dict[str, float] = {}
        for c, name in enumerate(COLS):
            v = e[mask, c]
            out[f"{name}_median"] = _q(v, 0.5) if v.size else math.nan
            out[f"{name}_p90"] = _q(v, 0.9) if v.size else math.nan
        return out

    def ratio(x: str, y: str, c: int, mask: np.ndarray) -> dict[str, float]:
        ri = bootstrap_clustered_quantile_ratio(
            errs[x][mask, c], errs[y][mask, c], cluster[mask], 0.5, LEVEL, RESAMPLES
        )
        return {"ratio": ri.ratio, "lo": ri.lo, "hi": ri.hi}

    def gap(name: str, c: int, minus: str | None = None) -> dict[str, float]:
        cols = {k: errs[k] for k in ("one_leg", "oracle", name)}
        if minus:
            cols[minus] = errs[minus]

        def stat(cc: dict[str, np.ndarray]) -> float:
            g = sc.gap_recovered_cols(cc, name, c)
            return g - sc.gap_recovered_cols(cc, minus, c) if minus else g

        si = bootstrap_clustered_statistic(cols, cluster, stat, LEVEL, RESAMPLES)
        return {"value": si.value, "lo": si.lo, "hi": si.hi}

    everyone = np.ones(len(rows), dtype=bool)
    result: dict[str, Any] = {
        "truth": a.truth,
        "ordinals": [a.start, a.start + a.count - 1],
        "scenarios": len(data),
        "rows": len(rows),
        "settled_rows": int(settled.sum()),
        "imm": a.imm,
        "level": LEVEL,
        "resamples": RESAMPLES,
        "segmenters": {},
    }
    for name, e in errs.items():
        rec: dict[str, Any] = {"all": summary(e, everyone), "settled": summary(e, settled)}
        if name not in ("imm",):
            rec["vs_imm"] = {c: ratio(name, "imm", i, everyone) for i, c in enumerate(COLS)}
        if name not in ("one_leg",):
            rec["vs_one_leg_settled"] = {
                c: ratio(name, "one_leg", i, settled) for i, c in enumerate(COLS)
            }
        if name not in ("one_leg", "oracle", "imm"):
            rec["gap_recovered"] = {c: gap(name, i) for i, c in enumerate(COLS)}
            if "glr_confirm" in errs and name != "glr_confirm":
                rec["gap_minus_glr_confirm"] = {
                    c: gap(name, i, "glr_confirm") for i, c in enumerate(COLS)
                }
        if name in seg_ivs:
            p = params.get(name, next(iter(params.values()), default_parameters()))
            pm = [
                sc.prefix_metrics(seg_ivs[name][(r.ordinal, r.k)], metas[r.ordinal], r.k, p)
                for r in rows
            ]
            cont = np.array([x.contamination for x in pm])
            cov = np.array([x.coverage for x in pm])
            fs = [x.false_split for x in pm if x.false_split is not None]
            lc = [x.leg_count_ok for x in pm if x.leg_count_ok is not None]
            h60 = [h for x in pm for h in x.hits60]
            h180 = [h for x in pm for h in x.hits180]
            rec["segmentation"] = {
                "contamination_median": float(np.nanmedian(cont)),
                "contamination_p90": float(np.nanquantile(cont, 0.9)),
                "coverage_median": float(np.nanmedian(cov)),
                "false_split_rate": float(np.mean(fs)) if fs else math.nan,
                "false_split_rows": len(fs),
                "leg_count_accuracy": float(np.mean(lc)) if lc else math.nan,
                "hits_60s": float(np.mean(h60)) if h60 else math.nan,
                "hits_3min": float(np.mean(h180)) if h180 else math.nan,
                "changes": len(h60),
            }
        result["segmenters"][name] = rec
    out = Path(a.experiment)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        f"# Segmentation scoring: {a.truth}, ordinals {a.start}–{a.start + a.count - 1}",
        "",
        f"{len(data)} scenarios, {len(rows)} G5 rows ({int(settled.sum())} settled); "
        f"frozen IMM `{a.imm}`; intervals {LEVEL:.1%}, {RESAMPLES} resamples, clustered.",
        "",
        "| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) "
        "| Contam. P90 | False split |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, rec in result["segmenters"].items():
        al = rec["all"]
        vi = rec.get("vs_imm", {}).get("range")
        gp = rec.get("gap_recovered", {}).get("range")
        sg = rec.get("segmentation", {})
        lines.append(
            f"| {name} | {al['range_median']:.3f} | {al['course_deg_median']:.2f} | "
            f"{al['speed_kt_median']:.2f} | "
            + (f"{vi['ratio']:.3f} [{vi['lo']:.3f}, {vi['hi']:.3f}]" if vi else "—")
            + " | "
            + (f"{gp['value']:.3f} [{gp['lo']:.3f}, {gp['hi']:.3f}]" if gp else "—")
            + " | "
            + (f"{sg['contamination_p90']:.3f}" if sg else "—")
            + " | "
            + (f"{sg['false_split_rate']:.3f}" if sg else "—")
            + " |"
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out} [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
