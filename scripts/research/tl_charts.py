"""Spec 013 slides: the time-late study in four SVG figures.

    uv run python scripts/research/tl_charts.py --out-dir <dir> [--data <dir with train.f32pack>]

* ``efficiency.svg``: error against the bound for the chord and arc solves told the true
  manoeuvre times (`experiments/20261111-tl-arc/pooled.txt`) and the arc fit told only the
  history (`experiments/20261112-tl-prior/pooled.txt`).
* ``systems.svg``: median period range error of every system
  (`experiments/20261111-tl-retest/pooled.txt`, `experiments/20261112-tl-prior/pooled.txt`).
* ``evidence.svg``: log evidence of the true history minus the re-test's, per period
  (`experiments/20261112-tl-prior/histories.json`).
* ``ambiguity.svg`` (with ``--data``: seed 329, count 400, `configs/timelate/tl-ranges.json`):
  one period where a history with no manoeuvre fits the bearings as well as the true one; both
  tracks are refitted here by `timelate.retest`.

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARC = Path("experiments/20261111-tl-arc/pooled.txt")
RETEST = Path("experiments/20261111-tl-retest/pooled.txt")
ENS = Path("experiments/20261112-tl-prior/pooled.txt")
HIST = Path("experiments/20261112-tl-prior/histories.json")
AMBIGUOUS = 12  # ordinal: one true manoeuvre, none found, evidence within 3


def pooled(p: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in (ROOT / p).read_text().splitlines():
        name, _, rest = line.partition(" ")
        if rest.strip().startswith("{"):
            out[name] = ast.literal_eval(rest.strip())
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import ESTIMATORS, STYLE

    g = read_git_provenance()  # before writing anything
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    used: dict[str, list[Path]] = {}
    extra: dict[str, dict[str, Any]] = {}
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    arc, ret, ens = pooled(ARC), pooled(RETEST), pooled(ENS)

    with plt.rc_context(STYLE):
        # 1. efficiency told the truth
        rows = [
            ("chord solve\ntrue times", arc["chord-true"]["eff"], grey),
            ("arc solve\ntrue times, kind judged", arc["arc-true"]["eff"], orange),
            ("arc solve\ntrue times, kind told", arc["arc-kind-true"]["eff"], purple),
            ("arc solve\ntrue history, times free", ens["truth-fit"]["eff"], green),
        ]
        fig, ax = plt.subplots(figsize=(8.0, 3.8))
        x = np.arange(3)
        for i, (lab, eff, col) in enumerate(rows):
            ax.bar(x + (i - 1.5) * 0.2, eff, 0.2, color=col, label=lab.replace("\n", ", "))
        ax.axhline(1.0, color="k", lw=0.8, ls="--")
        ax.set_xticks(x, ["range", "course", "speed"])
        ax.set_ylabel("error ÷ Cramér–Rao bound")
        ax.set_title(
            "Told the manoeuvres, the arc model reaches the bound (tuning seed 329, 57 periods)",
            fontsize=10,
        )
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "efficiency.svg")
        plt.close(fig)
        used["efficiency.svg"] = [ARC, ENS]

        # 2. every system
        sysrows = [
            ("true history,\nbearings only", ens["truth-fit"], green),
            ("true history,\nwith the prior", ens["truth-map"], green),
            ("chord solve,\ntrue times", ret["chord-true"], grey),
            ("C″ read\nas a track", ret["chord-c2"], orange),
            ("re-test from C″,\nbearings only", ret["retest-c2"], grey),
            ("re-test from C″,\nwith the prior", ens["retest-c2-k"], purple),
            ("re-test from nothing,\nwith the prior", ens["retest-none-k"], purple),
        ]
        fig, ax = plt.subplots(figsize=(8.4, 3.8))
        xs = np.arange(len(sysrows))
        ax.bar(xs, [r["med_period"] for _, r, _ in sysrows], 0.6, color=[c for *_, c in sysrows])
        for xi, (_, r, _) in zip(xs, sysrows, strict=True):
            ax.text(xi, r["med_period"] + 0.003, f"{r['med_period']:.3f}", ha="center", fontsize=8)
        ax.set_xticks(xs, [lab for lab, *_ in sysrows], fontsize=8)
        ax.set_ylabel("median period range error (relative)")
        ax.set_title(
            "Annex B's statistics in the fit halve the error (purple; nothing trained; 57 periods)",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(out / "systems.svg")
        plt.close(fig)
        used["systems.svg"] = [RETEST, ENS]

        # 3. evidence
        hist = json.loads((ROOT / HIST).read_text())
        d = np.array(
            [
                r["truth_ev"]["total"] - r["retest_none"]["ev"]["total"]
                for r in hist
                if "retest_none" in r and "ev" in r["retest_none"]
            ]
        )
        fig, ax = plt.subplots(figsize=(8.0, 3.6))
        ax.hist(np.clip(d, -30, 30), bins=np.arange(-30, 31, 3), color=grey)
        ax.axvline(0, color="k", lw=0.8)
        ax.axvspan(-3, 3, color=orange, alpha=0.25, label="within 3: not separated")
        ax.set_xlabel(
            "log evidence: true history − history found by the re-test "
            "(clipped at ±30; right favours the truth)"
        )
        ax.set_ylabel("periods")
        ax.set_title(
            f"Fitted with the prior, the true history is usually preferred ({d.size} periods: "
            f"{int((d > 3).sum())} favour truth, {int((d < -3).sum())} the other)",
            fontsize=10,
        )
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(out / "evidence.svg")
        plt.close(fig)
        used["evidence.svg"] = [HIST]

        # 4. one ambiguous period
        if a.data:
            from tma2.timelate.arc import fit_arc, start_from_track
            from tma2.timelate.periods import iter_periods
            from tma2.timelate.retest import joint_fit, retest
            from tma2.timelate.score import truth_rows

            p = next(iter(iter_periods(Path(a.data) / "train.f32pack", AMBIGUOUS, 1)))
            i0, i1 = p.first, p.first + p.rows
            t = p.own[i0:i1, 0].astype(float) - float(p.own[i0, 0])
            ox, oy = p.own[i0:i1, 1].astype(float), p.own[i0:i1, 2].astype(float)
            z, v = p.obs[i0:i1, 1].astype(float), p.obs[i0:i1, 2] != 0
            sigma = float(p.meta["parameters"]["noise_sigma_rad"])
            pb = (t, ox, oy, z, v, sigma)
            tr = truth_rows(p)
            tt = np.stack(
                [tr[:, 0], tr[:, 1], tr[:, 3] * np.sin(tr[:, 2]), tr[:, 3] * np.cos(tr[:, 2])],
                axis=1,
            )
            sp = [s for s in p.spans() if s["end_index"] > s["start_index"]]
            spt = np.array(
                [[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp]
            ).reshape(-1, 2)
            true_fit = joint_fit(pb, start_from_track(tt, t, spt), spt)
            none = np.zeros((0, 2))
            best = None
            for c0 in (0.0, 1.57, 3.14, 4.71):
                th0 = np.array(
                    [ox[0] + 8000 * np.sin(z[v][0]), oy[0] + 8000 * np.cos(z[v][0]), c0, 5.0]
                )
                f = fit_arc(t, ox, oy, z, v, sigma, none, th0)
                if best is None or f.cost < best.cost:
                    best = f
            assert best is not None
            found = retest(pb, best.theta, none, 20.0)
            fig, ax = plt.subplots(figsize=(6.4, 6.4))
            km = 1e-3
            ax.plot(ox * km, oy * km, color="#1f77b4", lw=1.5, label="ownship")
            ax.plot(tr[:, 0] * km, tr[:, 1] * km, color="#d62728", lw=2, label="target (truth)")
            ax.plot(
                true_fit.states[:, 0] * km,
                true_fit.states[:, 1] * km,
                color=green,
                lw=1.3,
                ls="--",
                label=f"fit told the true history (cost {true_fit.cost:.0f})",
            )
            ax.plot(
                found.states[:, 0] * km,
                found.states[:, 1] * km,
                color=purple,
                lw=1.3,
                ls="--",
                label=f"history the re-test found: {found.spans.shape[0]} manoeuvres "
                f"(cost {found.cost:.0f})",
            )
            ax.plot(ox[0] * km, oy[0] * km, "o", color="#1f77b4", ms=4)
            ax.plot(tr[0, 0] * km, tr[0, 1] * km, "o", color="#d62728", ms=4)
            ax.set_aspect("equal")
            ax.set_xlabel("east (km)")
            ax.set_ylabel("north (km)")
            ax.set_title(
                f"Two histories, the same bearings ({int(v.sum())} bearings, "
                f"{t[-1] / 60:.0f} min; dots mark the start)",
                fontsize=10,
            )
            ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12))
            fig.tight_layout()
            fig.savefig(out / "ambiguity.svg", bbox_inches="tight")
            plt.close(fig)
            used["ambiguity.svg"] = []
            extra["ambiguity.svg"] = {
                "data": "seed 329, count 400, configs/timelate/tl-ranges.json, train split",
                "ordinal": AMBIGUOUS,
                "bearings": int(v.sum()),
                "cost_true_history": true_fit.cost,
                "cost_found_history": found.cost,
                "found_manoeuvres": int(found.spans.shape[0]),
                "true_manoeuvres": int(spt.shape[0]),
                "threshold": 20.0,
            }

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
            **extra.get(name, {}),
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
