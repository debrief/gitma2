"""Spec 037: the registered readings M1-M5, Y1, Y2 of the test record, with their outcomes.

    uv run python scripts/research/rmis_readings.py experiments/<record> --errors-dir <dir> \
        --fit experiments/<validation>/interval-fit.json

``<dir>/<condition>/errors.npz`` are the scoring jobs' per-row errors (on the results branches;
too large to commit). M1 and M2 are read from each job's ``reading-ft.json``. M3, M4, Y1 and Y2
pool same-seed log ratios within an engagement here (addendum 3). M5 reads each job's coverage
and pools the interval score over the three decided conditions from ``interval-rows.npz``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.regress import mread

DECIDED = {"clean": "off", "primary": "all-central", "held_out": "ho-both"}
COLS = mread.COLS


def same_seed(
    errs: dict[str, np.ndarray], ordinal: np.ndarray, pairs: list[tuple[str, str]]
) -> dict[str, Any]:
    """numerator_k ÷ denominator_k per engagement, the pairs pooled by the mean log ratio."""
    out: dict[str, Any] = {}
    for c, col in enumerate(COLS):
        logs = []
        each = {}
        for num, den in pairs:
            ids, lr, _ = mread.scenario_log_ratio(errs[num][:, c], errs[den][:, c], ordinal)
            logs.append(dict(zip(ids.tolist(), lr.tolist(), strict=True)))
            each[f"{num}/{den}"] = mread.summarise(lr)
        common = sorted(set.intersection(*(set(d) for d in logs)))
        pooled = np.array([np.mean([d[u] for d in logs]) for u in common])
        out[col] = {"pooled": mread.summarise(pooled), "each": each}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("record")
    ap.add_argument("--errors-dir", required=True)
    ap.add_argument("--fit", required=True)
    a = ap.parse_args()
    rec = Path(a.record)
    temp = json.loads(Path(a.fit).read_text())["temperature"]
    E: dict[str, Any] = {}
    for c in DECIDED.values():
        z = np.load(Path(a.errors_dir) / c / "errors.npz")
        E[c] = ({k[4:]: z[k] for k in z.files if k.startswith("err_")}, z["ordinal"])
    F = {
        c: json.loads((rec / "runs" / c / "reading-ft.json").read_text()) for c in DECIDED.values()
    }
    R = {c: json.loads((rec / "runs" / c / "reading.json").read_text()) for c in DECIDED.values()}
    ft = [f"ft-s{k}" for k in (1, 2, 3)]
    out: dict[str, Any] = {}
    out["M1"] = {k: F["all-central"]["paired"]["c2-robust"][k]["pooled"] for k in COLS}
    out["M1"]["each_seed_range"] = {
        n: F["all-central"]["paired"]["c2-robust"]["range"][n] for n in ft
    }
    out["M2"] = {k: F["ho-both"]["paired"]["c2-robust"][k]["pooled"] for k in COLS}
    out["M2"]["each_seed_range"] = {n: F["ho-both"]["paired"]["c2-robust"]["range"][n] for n in ft}
    reg_ft = [(f"reg-s{k}", f"ft-s{k}") for k in (1, 2, 3)]
    out["M3"] = {c: same_seed(*E[c], reg_ft) for c in ("all-central", "ho-both")}
    m4 = same_seed(*E["off"], reg_ft)
    m4["no_cost"] = bool(m4["range"]["pooled"]["lo"] >= 0.95)
    out["M4"] = m4
    cov: dict[str, Any] = {}
    for c in DECIDED.values():
        cov[c] = {}
        for col in COLS:
            xs = [R[c]["coverage"][n][col]["all"] for n in ft]
            cov[c][col] = {
                "coverage_each": [x["coverage"] for x in xs],
                "lo_min": min(x["lo"] for x in xs),
                "hi_max": max(x["hi"] for x in xs),
                "normalised_error_median": float(
                    np.mean([x["normalised_error_median"] for x in xs])
                ),
                "stated_share": float(np.mean([x["stated_share"] for x in xs])),
                "honest": bool(all(0.90 <= x["lo"] and x["hi"] <= 0.99 for x in xs)),
            }
    score: dict[str, Any] = {}
    for ci, col in enumerate(COLS):
        head, ctl, ordn = [], [], []
        for j, c in enumerate(DECIDED.values()):
            z = np.load(rec / "runs" / c / "interval-rows.npz")
            for k, n in enumerate(ft):
                err, half = z[f"{n}__err"][:, ci], z[f"{n}__half"][:, ci]
                th = mread.temperature_half(temp, z[f"{n}__est_range_m"])[:, ci]
                head.append(mread.winkler(err, half))
                ctl.append(np.where(np.isfinite(half), mread.winkler(err, th), np.nan))
                # engagements are the bootstrap unit: the same engagement under another
                # condition or seed is the same unit
                ordn.append(z["ordinal"])
                _ = (j, k)
        score[col] = mread.score_ratio(
            np.concatenate(head), np.concatenate(ctl), np.concatenate(ordn)
        )
    out["M5"] = {"coverage": cov, "interval_score_head_over_temperature": score}
    hyb = [("c2-robust", f"hyb-s{k}") for k in (1, 2, 3)]
    fth = [(f"ft-s{k}", f"hyb-s{k}") for k in (1, 2, 3)]
    out["Y1"] = {c: same_seed(*E[c], hyb) for c in ("off", "all-central")}
    out["Y2"] = {c: same_seed(*E[c], fth) for c in ("off", "all-central")}
    out["Y_harm"] = bool(any(out["Y1"]["off"][col]["pooled"]["hi"] < 1 for col in COLS))
    out["c2_prior"] = {
        c: {
            "c2-robust/c2-prior": same_seed(*E[c], [("c2-robust", "c2-prior")]),
            "c2-prior/hybrid": same_seed(*E[c], [("c2-prior", f"hyb-s{k}") for k in (1, 2, 3)]),
        }
        for c in ("off", "all-central")
    }
    out["answered"] = {
        c: {n: float(np.isfinite(E[c][0][n]).all(axis=1).mean()) for n in sorted(E[c][0])}
        for c in DECIDED.values()
    }
    (rec / "readings.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    def iv(r: dict[str, Any]) -> str:
        return f"{r['ratio']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}] {r['outcome']}"

    L = ["# Registered readings (generated by `scripts/research/rmis_readings.py`)", ""]
    L += ["| Reading | Condition | Range | Course | Speed |", "|---|---|---|---|---|"]
    L.append(
        "| M1 C″-robust ÷ fine-tuned | all-central | "
        + " | ".join(iv(out["M1"][c]) for c in COLS)
        + " |"
    )
    L.append(
        "| M2 C″-robust ÷ fine-tuned | ho-both | "
        + " | ".join(iv(out["M2"][c]) for c in COLS)
        + " |"
    )
    for c in ("all-central", "ho-both"):
        L.append(
            f"| M3 unchanged ÷ fine-tuned | {c} | "
            + " | ".join(iv(out["M3"][c][k]["pooled"]) for k in COLS)
            + " |"
        )
    L.append(
        "| M4 unchanged ÷ fine-tuned | off | "
        + " | ".join(iv(out["M4"][k]["pooled"]) for k in COLS)
        + f" | no cost: {out['M4']['no_cost']}"
    )
    for c in ("off", "all-central"):
        L.append(
            f"| Y1 C″-robust ÷ hybrid | {c} | "
            + " | ".join(iv(out["Y1"][c][k]["pooled"]) for k in COLS)
            + " |"
        )
    for c in ("off", "all-central"):
        L.append(
            f"| Y2 fine-tuned ÷ hybrid | {c} | "
            + " | ".join(iv(out["Y2"][c][k]["pooled"]) for k in COLS)
            + " |"
        )
    for c in ("off", "all-central"):
        L.append(
            f"| (C″-robust ÷ C″ + static range prior) | {c} | "
            + " | ".join(iv(out["c2_prior"][c]["c2-robust/c2-prior"][k]["pooled"]) for k in COLS)
            + " |"
        )
        L.append(
            f"| (static-prior comparator ÷ hybrid) | {c} | "
            + " | ".join(iv(out["c2_prior"][c]["c2-prior/hybrid"][k]["pooled"]) for k in COLS)
            + " |"
        )
    L += [
        "",
        f"Hybrid harm on clean data (any of range, course, speed wholly below 1): **{out['Y_harm']}**",
        "",
    ]
    L += ["## M5: coverage of the stated 95% intervals, three fine-tuned seeds", ""]
    L += [
        "| Condition | Quantity | Coverage by seed | Widest interval over seeds | Normalised error | Stated share | Honest |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in DECIDED.values():
        for col in COLS:
            x = cov[c][col]
            L.append(
                f"| {c} | {col} | "
                + ", ".join(f"{v:.3f}" for v in x["coverage_each"])
                + f" | [{x['lo_min']:.3f}, {x['hi_max']:.3f}] | "
                f"{x['normalised_error_median']:.2f} | {x['stated_share']:.2f} | {x['honest']} |"
            )
    L += [
        "",
        "## M5: interval score, head ÷ temperature control, pooled over the three decided conditions",
        "",
    ]
    L += ["| Quantity | Ratio | Outcome (for the head) | Rows |", "|---|---|---|---|"]
    for col in COLS:
        x = score[col]
        L.append(
            f"| {col} | {x['ratio']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}] | {x['outcome']} | {x['rows']} |"
        )
    (rec / "readings.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
