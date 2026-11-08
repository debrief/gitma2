"""Figures for progress reports: track plots and per-scenario error curves.

A track plot shows the truth (ownship blue, target red) and where each estimator thought the
target was: its per-timestep trail from the first plausible row after the zig, a marker with a
1-σ position ellipse at each requested time, and the ownship's zig. Rows that fail
``plausible_row`` are masked (before the zig the physics layer returns "plausible" states whose
range sd ≫ range; those are hidden by the ``--from`` time, default the zig). Axes are east/north
in kilometres with equal aspect.

Every figure is written as SVG next to a ``.json`` sidecar naming the truth file, the
prediction files and their digests, the scenario and the command line, so a figure in a post
can be regenerated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

from tma2.eval.errors import Truth, plausible_row

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Ellipse  # noqa: E402

OWNSHIP = "#1f5fbf"  # blue
TARGET = "#c6322e"  # red
# Estimators: a colour-blind-safe set distinct from the two truth colours.
ESTIMATORS = ["#2a9d8f", "#e9a23b", "#7b4fa3", "#6c757d", "#8c564b", "#17becf"]
STYLE: dict[Any, Any] = {
    "figure.dpi": 100,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "legend.frameon": False,
    "svg.fonttype": "none",
}


@dataclass
class EstimatorRows:
    """One estimator's rows for one scenario, as read from its prediction file."""

    label: str
    rows: list[dict[str, Any]]
    mode: str = "per_timestep"
    colour: str = ESTIMATORS[0]

    def at(self, t: float, tol: float) -> dict[str, Any] | None:
        best = None
        for r in self.rows:
            d = abs(float(r["timestamp_s"]) - t)
            if d <= tol and (best is None or d < abs(float(best["timestamp_s"]) - t)):
                best = r
        return best


@dataclass
class TrackPlotOptions:
    at_s: tuple[float, ...] = ()
    from_s: float | None = None  # trail starts here (default the zig)
    title: str | None = None
    ellipses: bool = True
    width_in: float = 7.0
    height_in: float = 6.0
    notes: list[str] = field(default_factory=list)


def ellipse_from_cov(row: dict[str, Any]) -> tuple[float, float, float] | None:
    """(width, height, angle°) of the 1-σ position ellipse from ``cov_xyvv``, or None."""
    cov = row.get("cov_xyvv")
    if not cov or len(cov) != 10 or row.get("cov_ok") is False:
        return None
    sxx, sxy, syy = float(cov[0]), float(cov[1]), float(cov[4])
    if not all(math.isfinite(v) for v in (sxx, sxy, syy)) or sxx <= 0 or syy <= 0:
        return None
    m = np.array([[sxx, sxy], [sxy, syy]])
    w, v = np.linalg.eigh(m)
    if w[0] <= 0:
        return None
    angle = math.degrees(math.atan2(v[1, 1], v[0, 1]))
    return 2 * math.sqrt(w[1]), 2 * math.sqrt(w[0]), angle


def _km(a: np.ndarray) -> np.ndarray:
    return a / 1000.0


def _trail(est: EstimatorRows, from_s: float) -> np.ndarray:
    pts = [
        (float(r["timestamp_s"]), float(r["x_m"]), float(r["y_m"]))
        for r in est.rows
        if float(r["timestamp_s"]) >= from_s and plausible_row(r)
    ]
    return np.array(pts).reshape(-1, 3)


def draw_track(ax: Axes, truth: Truth, ests: list[EstimatorRows], opts: TrackPlotOptions) -> None:
    own, tgt = truth.own, truth.tgt
    ax.plot(_km(own[:, 1]), _km(own[:, 2]), color=OWNSHIP, lw=1.8, label="ownship (truth)")
    ax.plot(_km(tgt[:, 1]), _km(tgt[:, 2]), color=TARGET, lw=1.8, label="target (truth)")
    for arr, c in ((own, OWNSHIP), (tgt, TARGET)):
        ax.plot(_km(arr[0, 1]), _km(arr[0, 2]), marker="o", color=c, ms=5, mfc="white")
        ax.plot(_km(arr[-1, 1]), _km(arr[-1, 2]), marker=">", color=c, ms=6)
    zi = truth.zig_index
    if 0 <= zi < truth.samples:
        ax.plot(
            _km(own[zi, 1]),
            _km(own[zi, 2]),
            marker="D",
            color=OWNSHIP,
            ms=6,
            mfc="white",
            label=f"ownship zig ({truth.zig_time_s:.0f} s)",
        )
    from_s = truth.zig_time_s if opts.from_s is None else opts.from_s
    tol = truth.dt / 2
    for i, est in enumerate(ests):
        c = est.colour if est.colour else ESTIMATORS[i % len(ESTIMATORS)]
        trail = _trail(est, from_s)
        if est.mode == "per_timestep" and len(trail) > 1:
            sparse = len(trail) < 10  # e.g. the oracle answers only at the G5 points
            ax.plot(
                _km(trail[:, 1]),
                _km(trail[:, 2]),
                color=c,
                lw=1.2,
                ls="--",
                alpha=0.9,
                marker="." if sparse else None,
                label=f"{est.label} (estimate trail)",
            )
        elif len(trail) == 1:
            ax.plot(_km(trail[0, 1]), _km(trail[0, 2]), marker="x", color=c, ms=8, label=est.label)
        for t in opts.at_s:
            r = est.at(t, tol)
            if r is None or not plausible_row(r):
                continue
            x, y = float(r["x_m"]) / 1000, float(r["y_m"]) / 1000
            ax.plot(x, y, marker="x", color=c, ms=8, mew=2)
            ax.annotate(
                f"{est.label} @ {t:.0f} s",
                (x, y),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
                color=c,
            )
            e = ellipse_from_cov(r) if opts.ellipses else None
            if e is not None:
                w, h, ang = e
                ax.add_patch(
                    Ellipse(
                        (x, y), w / 1000, h / 1000, angle=ang, fill=False, ec=c, lw=1.0, alpha=0.8
                    )
                )
            k = truth.row_index(float(r["timestamp_s"]))
            ax.plot(_km(tgt[k, 1]), _km(tgt[k, 2]), marker="o", color=TARGET, ms=5, mfc=TARGET)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("east (km)")
    ax.set_ylabel("north (km)")
    p = truth.meta.get("parameters", {})
    sub = (
        f"σ = {math.degrees(float(p.get('noise_sigma_rad', 0))):.1f}°, "
        f"window {truth.samples * truth.dt:.0f} s, dt {truth.dt:.0f} s"
    )
    ax.set_title(
        f"{opts.title or f'Truth and estimate, scenario {truth.index}'}\n{sub}",
        loc="left",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=8)
    for i, n in enumerate(opts.notes):
        ax.text(0.01, 0.02 + 0.045 * i, n, transform=ax.transAxes, fontsize=8, color="#555")


def track_figure(truth: Truth, ests: list[EstimatorRows], opts: TrackPlotOptions) -> Any:
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(opts.width_in, opts.height_in))
        draw_track(ax, truth, ests, opts)
        fig.tight_layout()
    return fig


def _errors(truth: Truth, est: EstimatorRows, from_s: float) -> np.ndarray:
    """[n,4] t, |range error|/range, |course error| deg, |speed error| m/s on plausible rows."""
    out = []
    for r in est.rows:
        t = float(r["timestamp_s"])
        if t < from_s or not plausible_row(r):
            continue
        k = truth.row_index(t)
        o, g = truth.own[k], truth.tgt[k]
        rng = math.hypot(g[1] - o[1], g[2] - o[2])
        dc = (float(r["course_rad"]) - g[3] + math.pi) % (2 * math.pi) - math.pi
        out.append(
            (
                t,
                abs(float(r["range_m"]) - rng) / rng,
                abs(math.degrees(dc)),
                abs(float(r["speed_mps"]) - g[4]),
            )
        )
    return np.array(out).reshape(-1, 4)


def errors_figure(truth: Truth, ests: list[EstimatorRows], opts: TrackPlotOptions) -> Any:
    """Three panels against time since the zig: relative range, course and speed errors."""
    from_s = truth.zig_time_s if opts.from_s is None else opts.from_s
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(3, 1, figsize=(opts.width_in, opts.height_in), sharex=True)
        names = ("range error / range", "course error (°)", "speed error (m/s)")
        for i, est in enumerate(ests):
            c = est.colour if est.colour else ESTIMATORS[i % len(ESTIMATORS)]
            e = _errors(truth, est, from_s)
            if len(e) == 0:
                continue
            for j, ax in enumerate(axes):
                ax.plot(
                    (e[:, 0] - truth.zig_time_s) / 60,
                    e[:, j + 1],
                    color=c,
                    lw=1.3,
                    label=est.label if j == 0 else None,
                )
        for ax, n in zip(axes, names, strict=True):
            ax.set_ylabel(n, fontsize=9)
            if ax.has_data():
                ax.set_yscale("log")
        axes[-1].set_xlabel("minutes after the ownship zig")
        axes[0].set_title(
            opts.title or f"Errors against time, scenario {truth.index}", loc="left", fontsize=11
        )
        axes[0].legend(fontsize=8)
        fig.tight_layout()
    return fig


def save(fig: Any, out: str | Path, sidecar: dict[str, Any]) -> Path:
    """Write the figure (format from the suffix, SVG recommended) and its provenance sidecar."""
    from tma2.data.canonical import canonical_json
    from tma2.data.io import AtomicFile

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, metadata={"Date": None} if out.suffix == ".svg" else None)
    plt.close(fig)
    f = AtomicFile(out.with_suffix(out.suffix + ".json"))
    f.write((canonical_json(sidecar) + "\n").encode("utf-8"))
    f.commit()
    return out
