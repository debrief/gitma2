"""Spec 029 slides: SVG figures from the test record experiments/20261119-hold/.

    uv run python scripts/research/hold_charts.py \\
        [--record experiments/20261119-hold] [--config configs/long/hold-test.json] \\
        [--out-dir site/static/img/2026-11-19-held-course-slides]

* ``classes.svg``: ctl ÷ ctl-prior (range, course, speed) and ctl-carry ÷ ctl-prior on held and
  one-turn windows, geometric means with engagement intervals, against 1.
* ``windows.svg``: the per-window ratios ctl ÷ ctl-prior by class (log scale), with medians.
* ``errors.svg``: median range error per window by system and class (ctl, ctl-carry, ctl-prior,
  the fit told the true history).
* ``track.svg``: the held test window at the median of ctl ÷ ctl-prior among held windows:
  truth, ownship, ``ctl`` and ``ctl-prior``, and the carried 1-σ ellipse at the hand-over.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _sidecar(path: Path, inputs: list[Path], extra: dict[str, Any] | None = None) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/hold_charts.py",
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
    ap.add_argument("--record", default="experiments/20261119-hold")
    ap.add_argument("--config", default="configs/long/hold-test.json")
    ap.add_argument("--out-dir", default="site/static/img/2026-11-19-held-course-slides")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    from tma2.long.study import engagements
    from tma2.long.study27 import load27
    from tma2.long.study29 import klass, turns_in

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    rec = ROOT / a.record
    out = ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    study = json.loads((rec / "study.json").read_text())
    cfg = (ROOT / a.config).resolve()
    inputs = [rec / "study.json", ROOT / a.config]
    classes = ("held", "one")
    names = {"held": "no ownship turn\n(registered)", "one": "one ownship turn"}

    # classes
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    cols = {"range": "#1f77b4", "course": "#ff7f0e", "speed": "#2ca02c"}
    for i, k in enumerate(classes):
        for j, q in enumerate(("range", "course", "speed")):
            r = study["rule"]["by_class"][k][q]
            lo, hi = r["interval"]
            ax.errorbar(
                i + (j - 1.5) * 0.15,
                r["gm"],
                yerr=[[r["gm"] - lo], [hi - r["gm"]]],
                fmt="o",
                color=cols[q],
                capsize=3,
                label=f"ctl ÷ ctl-prior, {q}" if i == 0 else None,
            )
        r = study["beside"][k]["ctl-carry/ctl-prior"]
        lo, hi = r["interval"]
        ax.errorbar(
            i + 1.5 * 0.15,
            r["gm"],
            yerr=[[r["gm"] - lo], [hi - r["gm"]]],
            fmt="s",
            color="#9467bd",
            capsize=3,
            label="ctl-carry ÷ ctl-prior, range" if i == 0 else None,
        )
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_xticks(range(len(classes)), [names[k] for k in classes])
    ax.set_ylabel("ratio (above 1: the prior helps)")
    ax.set_title("Test, seed 364: geometric means and 95% engagement intervals", fontsize=8)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    p = out / "classes.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # load windows
    loads = []
    for e in engagements(cfg, 1):
        c = load27(rec / "raw", f"{cfg.stem}-c1", e, 1)
        if c:
            for w in c["windows"]:
                w["klass"] = klass(turns_in(e, int(w["first"]), int(w["rows"])))
            loads.append((c, e))

    def scored(w: dict[str, Any]) -> bool:
        return bool(w["index"] > 0 and w["carried"] is not None)

    # windows
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    g = np.random.default_rng(0)
    held_ratios = []
    for i, k in enumerate(classes):
        r = []
        for c, e in loads:
            for w in c["windows"]:
                if not scored(w) or w["klass"] != k:
                    continue
                x, y = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
                if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0:
                    r.append(x / y)
                    if k == "held":
                        held_ratios.append((x / y, c, e, w))
        v = np.clip(np.array(r), 0.1, 30.0)
        ax.scatter(i + g.uniform(-0.3, 0.3, v.size), v, s=5, alpha=0.4, color="#1f77b4")
        ax.plot([i - 0.35, i + 0.35], [np.median(v)] * 2, color="#d62728", lw=1.5)
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4, 8, 16], ["0.25", "0.5", "1", "2", "4", "8", "16"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(len(classes)), [names[k] for k in classes])
    ax.set_ylabel("ctl ÷ ctl-prior per window")
    ax.set_title("Every scored window (red: median)", fontsize=8)
    fig.tight_layout()
    p = out / "windows.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # errors
    me = study["beside"]["median_error"]
    systems = (
        ("ctl-d1-q0.01", "ctl", "#7f7f7f"),
        ("ctl-carry", "ctl-carry", "#9467bd"),
        ("ctl-prior", "ctl-prior", "#2ca02c"),
        ("history-map", "fit told the true history", "#d62728"),
    )
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    x = np.arange(len(classes))
    for j, (s, lab, col) in enumerate(systems):
        ax.bar(x + (j - 1.5) * 0.2, [100 * me[k][s] for k in classes], 0.2, color=col, label=lab)
    ax.set_xticks(x, [names[k].replace("\n", " ") for k in classes])
    ax.set_ylabel("median range error per window, %")
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "errors.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # track: the held window at the median ratio
    held_ratios.sort(key=lambda t: t[0])
    ratio, c, e, w = held_ratios[len(held_ratios) // 2]
    z = np.load(rec / "raw" / f"{cfg.stem}-c1-carry2-{e.index}.npz")
    j = w["index"]
    a0, a1 = int(w["first"]), int(w["first"]) + int(w["rows"])
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    km = 1e-3
    ax.plot(e.own[a0:a1, 1] * km, e.own[a0:a1, 2] * km, color="#1f77b4", lw=1, label="ownship")
    ax.plot(e.tgt[a0:a1, 1] * km, e.tgt[a0:a1, 2] * km, color="#d62728", lw=1.5, label="target")
    for s, col, lab in (("ctl-d1-q0.01", "#7f7f7f", "ctl"), ("ctl-prior", "#2ca02c", "ctl-prior")):
        st = z[f"w{j}_{s}"]
        ax.plot(st[:, 0] * km, st[:, 1] * km, color=col, lw=1, ls="--", label=lab)
    h = w["carried"]["h"]
    mean = np.array(h["mean"])
    cov = np.array(h["cov"])[:2, :2]
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
        f"Engagement {e.index}, window {j} (no ownship turn): the median held window, "
        f"ctl ÷ ctl-prior {ratio:.2f}",
        fontsize=7,
    )
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "track.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {"engagement": e.index, "window": j})
    print(sorted(x.name for x in out.glob("*.svg")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
