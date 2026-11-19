"""Spec 028 slides: SVG figures from the test record experiments/20261119-cp/.

    uv run python scripts/research/cp_charts.py \\
        [--record experiments/20261119-cp] [--config configs/long/cp-test.json] \\
        [--out-dir site/static/img/2026-11-19-carry-prior-slides]

* ``splits.svg``: ctl ÷ ctl-prior (range, course, speed) and ctl-carry ÷ ctl-prior by split,
  geometric means with engagement intervals, against 1.
* ``windows.svg``: the per-window ratios ctl ÷ ctl-prior by split (log scale), with medians.
* ``coverage.svg``: coverage of the carried 95% region by contact on tuning, validation and test.
* ``track.svg``: one test window where the prior helped most on contact 1: truth, ownship,
  ``ctl`` and ``ctl-prior``, and the carried 1-σ ellipse at the hand-over.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _sidecar(path: Path, inputs: list[Path], extra: dict | None = None) -> None:  # type: ignore[type-arg]
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/cp_charts.py",
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
                **(extra or {}),
            },
            indent=1,
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", default="experiments/20261119-cp")
    ap.add_argument("--config", default="configs/long/cp-test.json")
    ap.add_argument("--out-dir", default="site/static/img/2026-11-19-carry-prior-slides")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    from tma2.long.study import engagements
    from tma2.long.study27 import _splits, load27

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    rec = ROOT / a.record
    out = ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    study = json.loads((rec / "study.json").read_text())
    cfg = (ROOT / a.config).resolve()
    inputs = [rec / "study.json", ROOT / a.config]
    splits = ("weak", "other", "contact1", "contact2")
    names = {
        "weak": "weak geometry\n(registered)",
        "other": "other",
        "contact1": "contact 1",
        "contact2": "contact 2",
    }

    # splits
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    cols = {"range": "#1f77b4", "course": "#ff7f0e", "speed": "#2ca02c"}
    for i, s in enumerate(splits):
        for k, q in enumerate(("range", "course", "speed")):
            r = study["rule"]["by_split"][s][q]
            lo, hi = r["interval"]
            x = i + (k - 1.5) * 0.17
            ax.errorbar(
                x,
                r["gm"],
                yerr=[[r["gm"] - lo], [hi - r["gm"]]],
                fmt="o",
                color=cols[q],
                capsize=3,
                label=f"ctl ÷ ctl-prior, {q}" if i == 0 else None,
            )
        r = study["beside"][s]["ctl-carry/ctl-prior"]
        lo, hi = r["interval"]
        ax.errorbar(
            i + 1.5 * 0.17,
            r["gm"],
            yerr=[[r["gm"] - lo], [hi - r["gm"]]],
            fmt="s",
            color="#9467bd",
            capsize=3,
            label="ctl-carry ÷ ctl-prior, range" if i == 0 else None,
        )
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_xticks(range(len(splits)), [names[s] for s in splits])
    ax.set_ylabel("ratio (above 1: the prior helps)")
    ax.set_title("Test, seed 356: geometric means and 95% engagement intervals", fontsize=8)
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    p = out / "splits.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # windows
    loads = []
    for contact in (1, 2):
        for e in engagements(cfg, contact):
            c = load27(rec / "raw", f"{cfg.stem}-c{contact}", e, contact)
            if c:
                loads.append((c, e))
    sp = _splits()
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    g = np.random.default_rng(0)
    for i, s in enumerate(splits):
        r = []
        for c, _e in loads:
            for w in c["windows"]:
                if w["index"] == 0 or not sp[s](c, w):
                    continue
                x, y = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
                if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0:
                    r.append(x / y)
        v = np.clip(np.array(r), 0.1, 10.0)
        ax.scatter(i + g.uniform(-0.3, 0.3, v.size), v, s=4, alpha=0.35, color="#1f77b4")
        ax.plot([i - 0.35, i + 0.35], [np.median(v)] * 2, color="#d62728", lw=1.5)
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(len(splits)), [names[s] for s in splits])
    ax.set_ylabel("ctl ÷ ctl-prior per window")
    ax.set_title("Every window (red: median)", fontsize=8)
    fig.tight_layout()
    p = out / "windows.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # coverage
    recs = {
        "tuning (scale 2)": ROOT / "experiments/20261118-cp-tuning/study.json",
        "validation": ROOT / "experiments/20261119-cp-val/study.json",
        "test": rec / "study.json",
    }
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    for k, (lab, f) in enumerate(recs.items()):
        st = json.loads(f.read_text())
        for j, c in enumerate(("contact1", "contact2")):
            cv = st["coverage"][c]
            lo, hi = cv["interval"]
            x = j + (k - 1) * 0.22
            ax.errorbar(
                x,
                cv["coverage"],
                yerr=[[cv["coverage"] - lo], [hi - cv["coverage"]]],
                fmt="o",
                color=("#7f7f7f", "#1f77b4", "#d62728")[k],
                capsize=3,
                label=lab if j == 0 else None,
            )
    ax.axhline(0.95, color="#888", lw=0.8, ls="--")
    ax.axhspan(0.80, 0.99, color="#2ca02c", alpha=0.08)
    ax.set_xticks([0, 1], ["contact 1 (registered band shaded)", "contact 2"])
    ax.set_ylabel("share of hand-overs inside\nthe carried 95% region")
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "coverage.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, list(recs.values()))

    # track: the contact-1 window (not a chain's first) where ctl ÷ ctl-prior is largest
    best = None
    for c, e in loads:
        if c["contact"] != 1:
            continue
        for w in c["windows"]:
            if w["index"] == 0 or w["carried"] is None:
                continue
            x, y = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
            if np.isfinite(x) and np.isfinite(y) and y > 0 and (best is None or x / y > best[0]):
                best = (x / y, c, e, w)
    assert best is not None
    ratio, c, e, w = best
    z = np.load(rec / "raw" / f"{cfg.stem}-c1-carry2-{e.index}.npz")
    j = w["index"]
    rows = z[f"w{j}_rows"]
    a0, a1 = int(w["first"]), int(w["first"]) + int(w["rows"])
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    km = 1e-3
    ax.plot(e.own[a0:a1, 1] * km, e.own[a0:a1, 2] * km, color="#1f77b4", lw=1, label="ownship")
    ax.plot(e.tgt[a0:a1, 1] * km, e.tgt[a0:a1, 2] * km, color="#d62728", lw=1.5, label="target")
    for s, col, lab in (
        ("ctl-d1-q0.01", "#7f7f7f", "ctl"),
        ("ctl-prior", "#2ca02c", "ctl-prior"),
    ):
        st = z[f"w{j}_{s}"]
        ax.plot(st[:, 0] * km, st[:, 1] * km, color=col, lw=1, ls="--", label=lab)
    cw = w["carried"]
    mean = np.array(cw["h"]["mean"])
    cov = np.array(cw["h"]["cov"])[:2, :2]
    vals, vecs = np.linalg.eigh(cov)
    t = np.linspace(0, 2 * math.pi, 100)
    ell = (vecs @ np.diag(np.sqrt(np.maximum(vals, 0))) @ np.stack([np.cos(t), np.sin(t)])).T
    ax.plot(
        (mean[0] + ell[:, 0]) * km,
        (mean[1] + ell[:, 1]) * km,
        color="#9467bd",
        lw=1,
        label="carried 1-σ at hand-over",
    )
    ax.set_aspect("equal")
    ax.set_xlabel("x, km")
    ax.set_ylabel("y, km")
    ax.set_title(
        f"Engagement {e.index}, window {j}: ctl ÷ ctl-prior {ratio:.2f} (the best contact-1 window)",
        fontsize=8,
    )
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "track.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {"engagement": e.index, "window": j, "rows": [int(rows[0]), int(rows[-1])]})
    print(sorted(x.name for x in out.glob("*.svg")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
