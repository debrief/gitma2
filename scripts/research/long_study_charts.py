"""Spec 026 slides: SVG figures from the test record experiments/20261118-ls/.

    uv run python scripts/research/long_study_charts.py \\
        [--record experiments/20261118-ls] [--config configs/long/study-test.json] \\
        [--out-dir site/static/img/2026-11-18-long-study-slides]

* ``e1.svg``: ctl ÷ ctl-carry window by window (contact 1, by length; contact 2 beside), with
  the geometric means and their intervals against the 0.95 line.
* ``e2.svg``: ctl's median range error on each contact by range band.
* ``e3.svg``: the IMM's median error and share answered by 2-hour bin (12-hour engagements).

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _sidecar(path: Path, inputs: list[Path]) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/long_study_charts.py",
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
            },
            indent=1,
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", default="experiments/20261118-ls")
    ap.add_argument("--config", default="configs/long/study-test.json")
    ap.add_argument("--out-dir", default="site/static/img/2026-11-18-long-study-slides")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    from tma2.long.study import engagements, load_carry

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    rec = ROOT / a.record
    out = ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    study = json.loads((rec / "study.json").read_text())
    inputs = [rec / "study.json", ROOT / a.config]
    cfg = (ROOT / a.config).resolve()

    # E1: window by window
    groups = []
    for contact in (1, 2):
        for e in engagements(cfg, contact):
            c = load_carry(rec / "raw", f"{cfg.stem}-c{contact}", e)
            if not c:
                continue
            r = [w["ctl"] / w["carry"] for w in c["per_window"] if w["ctl"] > 0 and w["carry"] > 0]
            key = f"contact {contact}, {e.meta['hours']:g} h" if contact == 1 else "contact 2, both"
            groups.append((key, [x for x in r if np.isfinite(x)]))
    by: dict[str, list[float]] = {}
    for k, r in groups:
        by.setdefault(k, []).extend(r)
    labels = ["contact 1, 6 h", "contact 1, 12 h", "contact 2, both"]
    est = {
        "contact 1, 6 h": study["by_duration"]["6h"]["E1"],
        "contact 1, 12 h": study["by_duration"]["12h"]["E1"],
        "contact 2, both": study["E1_contact2_reported"],
    }
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    g = np.random.default_rng(0)
    for i, k in enumerate(labels):
        r = np.clip(np.array(by.get(k, [])), 0.2, 5.0)
        ax.scatter(
            i + g.uniform(-0.25, 0.25, r.size),
            r,
            s=5,
            alpha=0.35,
            color="#9467bd" if i < 2 else "#e377c2",
        )
        e1 = est[k]
        lo, hi = e1["interval"]
        ax.errorbar(
            i + 0.38,
            e1["gm_ctl_over_carry"],
            yerr=[[e1["gm_ctl_over_carry"] - lo], [hi - e1["gm_ctl_over_carry"]]],
            fmt="s",
            color="#222",
            capsize=3,
        )
    e1 = study["E1"]
    lo, hi = e1["interval"]
    ax.errorbar(
        3.0,
        e1["gm_ctl_over_carry"],
        yerr=[[e1["gm_ctl_over_carry"] - lo], [hi - e1["gm_ctl_over_carry"]]],
        fmt="D",
        color="#d62728",
        capsize=4,
    )
    ax.axhline(1.0, color="#888", lw=0.7)
    ax.axhline(0.95, color="#d62728", lw=0.8, ls="--")
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 0.95, 1, 2, 4], ["0.25", "0.5", "0.95", "1", "2", "4"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks([0, 1, 2, 3], labels + ["E1 (registered:\ncontact 1, pooled)"])
    ax.set_ylabel("ctl ÷ ctl-carry per window\n(above 1: carry better)")
    ax.set_title(
        "E1: geometric mean and 95% interval (squares); dashed: the 0.95 margin", fontsize=8
    )
    fig.tight_layout()
    p = out / "e1.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # E2: by band
    bands = study["E2"]["bands"]
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    x = np.arange(len(bands))
    ax.bar(
        x - 0.2,
        [100 * b["median_c1"] for b in bands],
        0.4,
        color="#9467bd",
        label="contact 1 (tended)",
    )
    ax.bar(
        x + 0.2,
        [100 * b["median_c2"] for b in bands],
        0.4,
        color="#e377c2",
        label="contact 2 (untended)",
    )
    ax.set_xticks(x, [f"{b['band_km'][0]:g}–{b['band_km'][1]:g} km" for b in bands])
    ax.set_ylabel("ctl median range error, %")
    e2 = study["E2"]
    ax.set_title(
        f"E2 = {e2['gm_c2_over_c1']:.2f} [{e2['interval'][0]:.2f}, {e2['interval'][1]:.2f}]",
        fontsize=9,
    )
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "e2.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # E3: by bin
    bins = study["E3"]["bins"]
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    xs = [f"{b['hours'][0]}–{b['hours'][1]} h" for b in bins]
    ax.plot(
        xs,
        [100 * b["median"] for b in bins],
        "o-",
        color="#17becf",
        label="IMM median range error, %",
    )
    ax.set_ylabel("median range error, %")
    ax2 = ax.twinx()
    ax2.plot(
        xs, [100 * b["answered"] for b in bins], "s--", color="#444", label="share answered, %"
    )
    ax2.set_ylabel("share answered, %")
    ax2.set_ylim(0, 100)
    ax.set_ylim(0, None)
    e3 = study["E3"]
    ax.set_title(
        f"E3 = {e3['late_over_early']:.2f} [{e3['interval'][0]:.2f}, {e3['interval'][1]:.2f}] (12-hour engagements)",
        fontsize=9,
    )
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="lower left")
    fig.tight_layout()
    p = out / "e3.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)
    print(sorted(x.name for x in out.glob("*.svg")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
