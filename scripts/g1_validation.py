"""Gate 1 validation report (spec 003 T019): every trained model and the baselines on the same
validation gate rows, the decision record's carried rule and its validation rule.

    uv run python scripts/g1_validation.py --decision experiments/<id>/decision.json \
        --validation <validation.f32pack> --models <dir with <model>/validation.ndjson[.gz]> \
        --lsq p --naive p --ekf p --imm p --out experiments/<date>-g1-a-val

Writes validation.json and validation.md. Exit 0: the validation rule is met and the test split
may be generated; exit 3: the phase stops at validation (the test split stays unscored).
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from tma2.cli.g1 import load_truths
from tma2.eval.g1 import RATIO_LIMIT, score
from tma2.eval.oracle_check import load_rows
from tma2.types import parse_record
from tma2.types.generated.tma import Gate1Decision

# Amendment 1 (owner, 2026-11-01; experiments/20261101-g1-decision/amendment-1.md): the
# shuffled-label control runs through the physics layer, so it is checked against batch least
# squares, not naive: a leak is a range-ratio interval wholly below 1.
SHUFFLED_LEAK_LIMIT = 1.0


def _rows(path: Path) -> Any:
    if path.suffix == ".gz":
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as tmp:
            with gzip.open(path, "rb") as src:
                shutil.copyfileobj(src, tmp)
        try:
            return load_rows(tmp.name)
        finally:
            Path(tmp.name).unlink()
    return load_rows(str(path))


def _find(models: Path, mid: str) -> Path:
    for name in ("validation.ndjson.gz", "validation.ndjson"):
        p = models / mid / name
        if p.exists():
            return p
    raise FileNotFoundError(f"no validation predictions for {mid} under {models}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", required=True)
    ap.add_argument("--validation", required=True)
    ap.add_argument("--models", required=True)
    for b in ("lsq", "naive", "ekf", "imm"):
        ap.add_argument(f"--{b}", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dec = parse_record(Gate1Decision, json.loads(Path(a.decision).read_text()), a.decision, 1)
    truths, bounds, _ = load_truths(a.validation)
    lsq = load_rows(a.lsq)
    base = {"naive": load_rows(a.naive), "ekf": load_rows(a.ekf), "imm": load_rows(a.imm)}
    per: dict[str, Any] = {}
    reported: dict[str, Any] = {}
    for n, mid in enumerate([*dec.carried_models, *dec.control_models]):
        res = score(
            truths,
            _rows(_find(Path(a.models), mid)),
            lsq,
            bounds,
            base if n == 0 else {},  # the baselines are the same rows for every model
            dec.bootstrap_level,
            dec.bootstrap_resamples,
        )
        per[mid] = {
            "checks": {
                c.name: {"result": c.result, "value": c.value, "lo": c.lo, "hi": c.hi}
                for c in res.checks
            },
            "median": res.reported["model"],
        }
        if n == 0:
            reported = res.reported
    baselines = {k: v for k, v in reported.items() if k != "model"}
    # Carried rule: the seed whose validation median range error at zig + 5 min is the median.
    seeds = sorted(dec.carried_models, key=lambda m: (per[m]["median"]["median-range"], m))
    carried = seeds[len(seeds) // 2]
    c = per[carried]["checks"]
    rule: dict[str, Any] = {
        f"carried-{m}-below-{RATIO_LIMIT}": c[f"ratio-{m}"]["value"] < RATIO_LIMIT
        for m in ("range", "course", "speed")
    }
    shuffled = next((m for m in dec.control_models if "shuffled" in m), None)
    timelate = next((m for m in dec.control_models if "timelate" in m), None)
    if shuffled:
        rule["shuffled-no-better-than-least-squares"] = (
            per[shuffled]["checks"]["ratio-range"]["hi"] >= SHUFFLED_LEAK_LIMIT
        )
    if timelate:
        causal = dec.carried_models[0]
        rule["timelate-at-least-as-good"] = (
            per[timelate]["median"]["median-range"] <= per[causal]["median"]["median-range"]
        )
    proceed = all(rule.values())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "decision": a.decision,
        "carried": carried,
        "seed_order_by_range": seeds,
        "validation_rule": rule,
        "proceed_to_test": proceed,
        "models": per,
        "baselines": baselines,
    }
    (out / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Gate 1 validation report",
        "",
        f"Decision record: `{a.decision}`. Validation split: seed 302, σ = 1° gate rows "
        "(zig + 5 min for range and course, zig + 10 min for speed).",
        "",
        "| Estimator | Range (median, ratio to LS) | Course (°) | Speed (m/s) | Gross | "
        "Efficiency range / course / speed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    def row(name: str, med: dict[str, Any], chk: dict[str, Any] | None) -> str:
        def ratio(m: str) -> str:
            if chk is None:
                return ""
            r = chk[f"ratio-{m}"]
            return f" ({r['value']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}])"

        eff = (
            " / ".join(
                f"{chk[f'efficiency-{m}']['value']:.3f}" for m in ("range", "course", "speed")
            )
            if chk
            else " / ".join(
                f"{med.get(f'efficiency-{m}') or float('nan'):.3f}"
                for m in ("range", "course", "speed")
            )
        )
        return (
            f"| {name} | {100 * med['median-range']:.2f}%{ratio('range')} | "
            f"{med['median-course']:.2f}{ratio('course')} | "
            f"{med['median-speed']:.3f}{ratio('speed')} | {100 * med['gross']:.2f}% | {eff} |"
        )

    for mid, rec in per.items():
        lines.append(
            row(mid + (" (carried)" if mid == carried else ""), rec["median"], rec["checks"])
        )
    for name, rec in baselines.items():
        lines.append(row(name, rec, None))
    lines += [
        "",
        f"Carried by rule (median seed by median range error): **{carried}** "
        f"(order {', '.join(seeds)}).",
        "",
        "Validation rule:",
        "",
        *[f"- {k}: {'met' if v else '**not met**'}" for k, v in rule.items()],
        "",
        "**"
        + (
            "Proceed to the test split (seed 303)."
            if proceed
            else "Stop at validation: the test split stays unscored and reserved."
        )
        + "**",
        "",
    ]
    (out / "validation.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0 if proceed else 3


if __name__ == "__main__":
    sys.exit(main())
