"""Spec 020 slides: figures from the viewer's shipped data and a conformance-leg result.

    uv run python scripts/research/viewer_charts.py --data site/static/viewer \\
        --leg <viewer results.json> --out-dir site/static/img/<slug>

* ``tracks.svg``: the busy engagement and the one where E loses to C″, at the last scored
  time. Ownship blue, target red, E's trail (Python's onnxruntime outputs, which the browser
  matches; its dashed 1-σ ellipse at the last time is overconfident, Gate 3), C″'s and the IMM's
  trails.
* ``errors.svg``: range error against time since the zig, every engagement, every system.
* ``conformance.svg``: per checked row, the browser's largest relative difference from Python
  (state element-wise; covariance element-wise and on its own scale), against 1e-5.
* ``timing.svg``: the browser's time per row by engagement, and the graph's load time.

Reads the manifest, the engagement files and the leg's ``results.json``; writes
``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COL = {"e": "#2ca02c", "one_leg": "#7f7f7f", "imm": "#ff7f0e", "c": "#9467bd", "c2": "#8c564b"}
NAME = {"e": "E", "one_leg": "one leg", "imm": "IMM", "c": "C", "c2": "C″"}
OWN, TGT = "#1f77b4", "#d62728"


def load(data: Path) -> tuple[dict[str, Any], list[tuple[dict[str, Any], Any]]]:
    import numpy as np

    man = json.loads((data / "manifest.json").read_text())
    out = []
    for e in man["engagements"]:
        doc = json.loads(gzip.decompress((data / e["json"]).read_bytes()))
        v = np.frombuffer(gzip.decompress((data / e["binary"]).read_bytes()), dtype="<f8")
        lay = {L["name"]: L for L in doc["layout"]}
        st, cv = lay["state"], lay["cov"]
        e_state: list[Any] = [None] * len(doc["rows"])
        e_cov: list[Any] = [None] * len(doc["rows"])
        for r, q in enumerate(doc["e_rows"]):
            e_state[q] = v[st["offset"] + 4 * r : st["offset"] + 4 * r + 4]
            e_cov[q] = v[cv["offset"] + 16 * r : cv["offset"] + 16 * r + 16].reshape(4, 4)
        doc["e_state"], doc["e_cov"] = e_state, e_cov
        out.append((e, doc))
    return man, out


def e_row(doc: dict[str, Any], q: int) -> dict[str, float] | None:
    s = doc["e_state"][q]
    if s is None:
        return None
    k = doc["rows"][q]
    ox, oy = doc["own"][k]
    return {
        "x_m": float(s[0]),
        "y_m": float(s[1]),
        "range_m": math.hypot(s[0] - ox, s[1] - oy),
        "course_rad": math.atan2(s[2], s[3]) % (2 * math.pi),
        "speed_mps": math.hypot(s[2], s[3]),
    }


def answered(r: dict[str, float] | None) -> bool:
    if r is None:
        return False
    vals = [r[k] for k in ("range_m", "course_rad", "speed_mps", "x_m", "y_m")]
    return all(math.isfinite(x) for x in vals) and 0 < r["range_m"] <= 1e5 and r["speed_mps"] <= 25


def rows_of(doc: dict[str, Any], s: str) -> list[dict[str, float] | None]:
    if s == "e":
        return [e_row(doc, q) for q in range(len(doc["rows"]))]
    return list(doc["systems"][s])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--leg", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Ellipse

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import STYLE

    g = read_git_provenance()
    data, out = Path(a.data), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    man, engs = load(data)
    leg = json.loads(Path(a.leg).read_text())
    data_inputs = [data / "manifest.json"] + [
        data / f for f in man["files"] if f.startswith("engagement-")
    ]
    used: dict[str, list[Path]] = {}

    with plt.rc_context(STYLE):
        # 1. two engagements as tracks
        want = [
            next(i for i, (e, _) in enumerate(engs) if e["reason"] == "busy"),
            next(i for i, (e, _) in enumerate(engs) if e["reason"].startswith("E worse")),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
        for ax, i in zip(axes, want, strict=True):
            e, doc = engs[i]
            own = np.array(doc["own"]) / 1000
            tgt = np.array(doc["target"])[:, :2] / 1000
            q = len(doc["rows"]) - 1
            k = doc["rows"][q]
            ax.plot(own[:, 0], own[:, 1], color=OWN, lw=1.4, label="ownship")
            ax.plot(tgt[:, 0], tgt[:, 1], color=TGT, lw=1.6, label="target (truth)")
            ax.plot(*own[k], "o", color=OWN, ms=5)
            ax.plot(*tgt[k], "o", color=TGT, ms=5)
            for s in ("e", "c2", "imm"):
                pts = [(r["x_m"] / 1000, r["y_m"] / 1000) for r in rows_of(doc, s) if answered(r)]
                if pts:
                    p = np.array(pts)
                    ax.plot(p[:, 0], p[:, 1], color=COL[s], lw=1.1, label=NAME[s])
                    ax.plot(*p[-1], "o", color=COL[s], ms=4)
            last = e_row(doc, q)
            cov = doc["e_cov"][q]
            if answered(last) and cov is not None:
                assert last is not None
                w, vec = np.linalg.eigh(cov[:2, :2])
                if (w > 0).all():
                    ang = math.degrees(math.atan2(vec[1, 1], vec[0, 1]))
                    ax.add_patch(
                        Ellipse(
                            (last["x_m"] / 1000, last["y_m"] / 1000),
                            2 * math.sqrt(w[1]) / 1000,
                            2 * math.sqrt(w[0]) / 1000,
                            angle=ang,
                            fill=False,
                            ls="--",
                            color=COL["e"],
                        )
                    )
            box = np.vstack([own, tgt])
            lo, hi = box.min(0), box.max(0)
            pad = 0.15 * (hi - lo).max() + 1
            ax.set_xlim(lo[0] - pad, hi[0] + pad)
            ax.set_ylim(lo[1] - pad, hi[1] + pad)
            ax.set_aspect("equal", adjustable="datalim")
            mins = (k - doc["zig_index"]) * doc["dt_s"] / 60
            ax.set_title(
                f"{e['reason']}: ordinal {doc['ordinal']}, zig + {mins:.0f} min", fontsize=9
            )
            ax.set_xlabel("east (km)")
        axes[0].set_ylabel("north (km)")
        axes[0].legend(frameon=False, fontsize=7)
        fig.text(
            0.5,
            0.01,
            "Dashed: E's stated 1-σ ellipse, overconfident (Gate 3: 95% coverage 0.60).",
            ha="center",
            fontsize=8,
        )
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.savefig(out / "tracks.svg")
        plt.close(fig)
        used["tracks.svg"] = data_inputs

        # 2. range error against time, every engagement
        n = len(engs)
        fig, axes = plt.subplots(1, n, figsize=(2.3 * n, 3.0), sharey=True)
        for ax, (e, doc) in zip(np.atleast_1d(axes), engs, strict=True):
            t = [(k - doc["zig_index"]) * doc["dt_s"] / 60 for k in doc["rows"]]
            for s in ("one_leg", "imm", "c", "c2", "e"):
                err = []
                for q, r in enumerate(rows_of(doc, s)):
                    k = doc["rows"][q]
                    ox, oy = doc["own"][k]
                    tx, ty = doc["target"][k][:2]
                    true = math.hypot(tx - ox, ty - oy)
                    err.append(abs(r["range_m"] - true) / true if answered(r) else np.nan)
                ax.plot(t, err, color=COL[s], lw=1.6 if s == "e" else 1.0, label=NAME[s])
            ax.set_yscale("log")
            ax.set_ylim(1e-3, 3)
            ax.set_title(f"{e['id'] + 1}: {e['reason']}", fontsize=8)
            ax.set_xlabel("min since zig", fontsize=8)
        np.atleast_1d(axes)[0].set_ylabel("relative range error")
        np.atleast_1d(axes)[0].legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "errors.svg")
        plt.close(fig)
        used["errors.svg"] = data_inputs

        # 3. conformance per row
        rows = leg["per_row"]
        fig, ax = plt.subplots(figsize=(8, 3.4))
        x = np.arange(len(rows))
        for key, lab, col, m in (
            ("state", "state, element-wise", "#2ca02c", "o"),
            ("cov", "covariance, element-wise (reported)", "#bbbbbb", "x"),
            ("cov_scaled", "covariance on its own scale", "#9467bd", "."),
        ):
            y = [max(r["outputs"][key]["max_rel_diff"], 1e-17) for r in rows]
            ax.scatter(x, y, s=10, marker=m, color=col, label=lab)
        ax.axhline(1e-5, color="#d62728", lw=1, ls="--", label="tolerance 1e-5")
        ax.set_yscale("log")
        ax.set_xlabel("checked row (engagements in order)")
        ax.set_ylabel("browser vs Python, max relative difference")
        ax.set_title(
            f"{len(rows)} rows; flags identical on every row ({leg.get('browser', '')[:40]}…)",
            fontsize=9,
        )
        ax.legend(frameon=False, fontsize=7, loc="lower right")
        fig.tight_layout()
        fig.savefig(out / "conformance.svg")
        plt.close(fig)
        used["conformance.svg"] = [Path(a.leg)]

        # 4. timing
        fig, ax = plt.subplots(figsize=(6.5, 3.0))
        by: dict[int, list[float]] = {}
        for r in rows:
            by.setdefault(r["engagement"], []).append(r["ms"])
        ax.boxplot(list(by.values()), tick_labels=[f"{e + 1}" for e in by], showfliers=True)
        ax.set_xlabel("engagement")
        ax.set_ylabel("ms per row (one WASM thread)")
        tot = {e: sum(v) / 1000 for e, v in by.items()}
        ax.set_title(
            f"graph load {leg['load_ms'] / 1000:.1f} s; first estimate "
            f"{leg['first_estimate_ms'] / 1000:.1f} s after the page opens; a whole engagement "
            f"{min(tot.values()):.0f} to {max(tot.values()):.0f} s",
            fontsize=8,
        )
        fig.tight_layout()
        fig.savefig(out / "timing.svg")
        plt.close(fig)
        used["timing.svg"] = [Path(a.leg)]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/viewer_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
