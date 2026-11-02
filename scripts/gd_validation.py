"""Gate D validation report (spec 004 T023; decision record, Annex A §A.5).

    uv run python scripts/gd_validation.py --decision experiments/<id>/decision.json \
        --plan configs/gate-d/plan.json --validation <validation.f32pack> \
        --models <dir with <id>/{meta.json,validation.ndjson.gz,validation.detector.ndjson.gz}> \
        --lsq p --imm p --ekf p --oracle p --out experiments/<date>-gd-a-val

1. Carried rule: per variant (causal, time-late), the seed whose validation D-downstream-all ratio
   (median relative range error over σ = 1° G5 rows of its downstream estimate ÷ the frozen
   IMM's) is the median of the three; ties to the lower seed.
2. Each carried seed's held-leg G5 false-alarm fraction at p_change ≥ 0.5 on validation.
3. Controls (``tma2-controls tune``) tuned to that fraction per carried variant: CUSUM and GLR on
   the per-timestep least squares (gated), the IMM's μ_CT and the EKF-innovation CUSUM (reported);
   plus the IMM's μ_CT at its natural 0.5 (D3, reported). Each is run on validation.
4. ``amendment.json``: every control's settings, by value (``tma2-gd`` refuses control files whose
   settings no amendment lists); its digest goes in the report.
5. ``tma2-gd --split validation``: the validation rule per carried variant.

Exit 0: at least one variant is carried and the test split may be generated; exit 3: the phase
stops at validation.
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from tma2.cli.controls import main as controls_main
from tma2.cli.gd import load_g5_predictions, score_detector_file
from tma2.cli.gd import main as gd_main
from tma2.data.f32pack import iter_pack_raw
from tma2.data.io import file_digest
from tma2.detect.matching import summary
from tma2.eval.errors import Truth
from tma2.eval.gd import downstream_rows, g5_rows
from tma2.eval.rows import G5_SLICE_SIGMA_RAD
from tma2.eval.stats import ascending, percentile
from tma2.models.train import load_plan
from tma2.types import parse_record
from tma2.types.generated.tma import DetectorVariant, GateDDecision


def _plain(path: Path, work: Path) -> Path:
    """An uncompressed copy of ``path`` (``.gz`` or not) under ``work``."""
    if path.suffix != ".gz":
        return path
    out = work / f"{path.parent.name}-{path.stem}"
    with gzip.open(path, "rb") as src, open(out, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--validation", required=True)
    ap.add_argument("--models", required=True)
    for b in ("lsq", "imm", "ekf", "oracle"):
        ap.add_argument(f"--{b}", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    decision = parse_record(GateDDecision, json.loads(Path(a.decision).read_text()), a.decision, 1)
    plan, _ = load_plan(a.plan)
    models = Path(a.models)
    truths: list[Truth] = []
    sigma1: dict[int, dict[str, Any]] = {}
    for _, m, own, tgt, _obs in iter_pack_raw(a.validation):
        t = Truth.from_block(m, own, tgt)
        truths.append(t)
        if abs(float(m["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) <= 1e-6:
            sigma1[t.index] = m
    wanted: dict[int, set[float]] = {}
    for t, k, _ in g5_rows(truths):
        wanted.setdefault(t.index, set()).add(float(t.own[k, 0]))
    imm = load_g5_predictions(a.imm, wanted)
    report: dict[str, Any] = {"seeds": {}, "carried": {}, "controls": {}}
    by_variant: dict[str, list[str]] = {}
    files: dict[str, tuple[Path, Path, Path]] = {}
    for d in plan.detectors or []:
        mdir = models / d.id
        det = _plain(mdir / "validation.detector.ndjson.gz", work)
        down = _plain(mdir / "validation.ndjson.gz", work)
        files[d.id] = (mdir / "meta.json", det, down)
        rows = downstream_rows(truths, {"imm": imm, "det": load_g5_predictions(str(down), wanted)})
        med_d = percentile(ascending(rows.errors["det"]["range_rel"]), 0.5)
        med_i = percentile(ascending(rows.errors["imm"]["range_rel"]), 0.5)
        scores = score_detector_file(det, sigma1, d.id, decision)
        s = summary(scores)
        report["seeds"][d.id] = {
            "variant": DetectorVariant(d.variant).value,
            "downstream_all_ratio": med_d / med_i,
            "median_range_rel": med_d,
            "held_leg_g5_false_alarm": s["held_leg_g5_false_alarm"],
            "summary": s,
        }
        if d.id in decision.carried_variants:
            by_variant.setdefault(DetectorVariant(d.variant).value, []).append(d.id)
    report["imm_median_range_rel"] = med_i
    amend: dict[str, Any] = {"controls": [], "carried": {}}
    ls = ["--least-squares", a.lsq]
    for variant, ids in sorted(by_variant.items()):
        ranked = sorted(ids, key=lambda i: (report["seeds"][i]["downstream_all_ratio"], i))
        carried = ranked[(len(ranked) - 1) // 2]
        far = report["seeds"][carried]["held_leg_g5_false_alarm"]
        report["carried"][variant] = {"detector": carried, "held_leg_g5_false_alarm": far}
        amend["carried"][variant] = carried
        for kind, extra in (
            ("cusum", ls),
            ("glr", ls),
            ("imm_mode", ["--imm", decision.imm]),
            ("cusum_ekf", ["--ekf", decision.ekf]),
        ):
            st = work / f"{carried}-{kind}.json"
            args = ["tune", "--kind", kind, "--validation", a.validation, *extra]
            if controls_main([*args, "--target-far", repr(float(far)), "--out", str(st)]) != 0:
                return 2
            amend["controls"].append(json.loads(st.read_text()))
            rows_out = work / f"{carried}-{kind}.ndjson"
            run = ["run", "--settings", str(st), "--truth", a.validation, "--out", str(rows_out)]
            if kind in ("cusum", "glr"):
                run += ls
            if controls_main(run) != 0:
                return 2
            report["controls"][f"{carried}:{kind}"] = json.loads(st.read_text())
    # D3: the IMM's mode probability at its natural threshold, reported.
    nat = work / "imm_mode-natural.json"
    nat.write_text(
        json.dumps({"kind": "imm_mode", "threshold": 0.5, "imm": decision.imm}, sort_keys=True)
    )
    nat_rows = work / "imm_mode-natural.ndjson"
    if controls_main(
        ["run", "--settings", str(nat), "--truth", a.validation, "--out", str(nat_rows)]
    ):
        return 2
    amend["controls"].append(json.loads(nat.read_text()))
    am_path = out / "amendment.json"
    am_path.write_text(json.dumps(amend, indent=2, sort_keys=True) + "\n")
    report["amendment_sha256"] = file_digest(am_path)
    cmd = ["--decision", a.decision, "--plan", a.plan, "--split", "validation"]
    cmd += ["--truth", a.validation]
    for c in report["carried"].values():
        vid = c["detector"]
        meta, det, down = files[vid]
        cmd += ["--variant", f"{vid}={meta},{det},{down}"]
        for kind in ("cusum", "glr", "imm_mode", "cusum_ekf"):
            cmd += ["--control", f"{vid}:{kind}={work / f'{vid}-{kind}.ndjson'}"]
    cmd += ["--control", f"imm_mode={nat_rows}"]
    cmd += ["--least-squares", a.lsq, "--imm", a.imm, "--ekf", a.ekf, "--oracle", a.oracle]
    # The record's own folder: Experiment excludes it from the dirty check, so the files this
    # script writes beside the record (work/, amendment.json) do not mark the tree dirty (panel
    # round 1 of the spec 004 validation stop found git_dirty true with the record in out/gd).
    cmd += ["--amendment", str(am_path), "--experiment", str(out)]
    status = gd_main(cmd)
    metrics = json.loads((out / "metrics.json").read_text())
    report["validation_carried"] = metrics["reported"].get("validation_carried", [])
    report["variant_results"] = metrics["reported"].get("variant_results", {})
    (out / "validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=float) + "\n"
    )
    (out / "validation.md").write_text(_markdown(report, out))
    print(json.dumps({"carried": report["validation_carried"], "status": status}))
    if status not in (0, 3):
        return status
    return 0 if report["validation_carried"] else 3


def _markdown(rep: dict[str, Any], gd: Path) -> str:
    verdict = json.loads((gd / "verdict.json").read_text())
    lines = [
        "# Gate D validation report",
        "",
        "Seeds (validation seed 304, σ = 1° G5 rows; ratio = median range error ÷ the IMM's "
        f"{rep['imm_median_range_rel']:.4f}):",
        "",
        "| Detector | Variant | D-downstream-all ratio | Held-leg G5 false alarms |",
        "| --- | --- | --- | --- |",
    ]
    for k, v in sorted(rep["seeds"].items()):
        lines.append(
            f"| {k} | {v['variant']} | {v['downstream_all_ratio']:.4f} | "
            f"{v['held_leg_g5_false_alarm']:.4%} |"
        )
    lines += [
        "",
        "Carried: " + ", ".join(f"{k}: {v['detector']}" for k, v in rep["carried"].items()),
    ]
    lines += [
        "",
        "| Check | Result | Value | Interval | Limit |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in verdict["checks"]:
        lo, hi = c.get("ci_low"), c.get("ci_high")
        iv = f"[{lo:.4g}, {hi:.4g}]" if lo is not None and hi is not None else ""
        lim = c.get("threshold")
        val = c.get("value")
        lines.append(
            f"| {c['name']} | {c['result']} | {'' if val is None else f'{val:.4g}'} | {iv} | "
            f"{'' if lim is None else f'{lim:.4g}'} |"
        )
    carried = rep["validation_carried"]
    lines += [
        "",
        "Validation rule (Annex A §A.5): "
        + (
            f"carried to test: {', '.join(carried)}."
            if carried
            else "no variant is carried; the "
            "phase stops at validation and the test split stays unscored."
        ),
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
