"""tma2-plot: figures for progress reports (track plots, error curves).

    tma2-plot track  --truth <split> --predictions <pred>... --scenario <index> \
        [--at 300,600] [--from <s>] [--labels a,b] [--title ...] --out fig.svg
    tma2-plot errors --truth <split> --predictions <pred>... --scenario <index> --out fig.svg

Each figure gets a ``<out>.json`` sidecar (truth and prediction digests, scenario, command line,
code commit) so a post's figure can be regenerated. Exit 2 on a usage or data error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tma2.data.io import file_digest
from tma2.data.provenance import read_git_provenance
from tma2.eval.errors import Truth
from tma2.eval.predictions import iter_predictions_raw
from tma2.report.plots import (
    ESTIMATORS,
    EstimatorRows,
    TrackPlotOptions,
    errors_figure,
    save,
    track_figure,
)
from tma2.types import RecordError

from .estimators import open_split


def load_truth(split: str, index: int) -> Truth:
    _, blocks = open_split(split)
    for _, meta, own, tgt, _obs in blocks:
        if int(meta["index"]) == index:
            return Truth.from_block(meta, own, tgt)
    raise ValueError(f"scenario {index} is not in {split}")


def load_rows(
    path: str,
    truth_path: str,
    index: int,
    label: str | None,
    colour: str,
    bound_to: str | None = None,
) -> EstimatorRows:
    """The rows for one scenario. The file must be bound (``dataset_digest``) to the truth file,
    or to ``bound_to``: the split a demo split was cut from (``scripts/research/g3_demo_split.py``).
    Gate 2's E files carry their own header type (``EPredictionHeader``), read as JSON here."""
    with open(path, encoding="utf-8") as fh:
        h = json.loads(fh.readline())
    ok = {file_digest(truth_path)} | ({file_digest(bound_to)} if bound_to else set())
    if h.get("dataset_digest") not in ok:
        raise RecordError(path, 1, f"dataset_digest is not {truth_path}'s (or --bound-to's)")
    mode = str(h.get("mode", "per_timestep"))
    for _, p in iter_predictions_raw(path):
        if int(p["scenario_index"]) == index:
            return EstimatorRows(label or str(h.get("estimator")), list(p["rows"]), mode, colour)
    raise ValueError(f"{path}: no prediction for scenario {index}")


def _floats(text: str | None) -> tuple[float, ...]:
    return tuple(float(x) for x in text.split(",") if x) if text else ()


def sidecar(a: argparse.Namespace, argv: list[str]) -> dict[str, Any]:
    g = read_git_provenance()
    return {
        "command": "tma2-plot " + " ".join(argv),
        "truth": {"path": a.truth, "sha256": file_digest(a.truth)},
        "predictions": [{"path": p, "sha256": file_digest(p)} for p in a.predictions],
        "scenario_index": a.scenario,
        "bound_to": (
            {"path": a.bound_to, "sha256": file_digest(a.bound_to)} if a.bound_to else None
        ),
        "code_git_commit": g.commit,
        "code_git_dirty": g.dirty,
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="tma2-plot")
    sub = ap.add_subparsers(dest="kind", required=True)
    for kind in ("track", "errors"):
        p = sub.add_parser(kind)
        p.add_argument("--truth", required=True)
        p.add_argument("--predictions", nargs="+", required=True)
        p.add_argument("--scenario", type=int, required=True)
        p.add_argument("--labels", help="comma-separated, one per prediction file")
        p.add_argument("--at", help="comma-separated times (s) to mark, track plots")
        p.add_argument("--from", dest="from_s", type=float, help="trail start (s); default the zig")
        p.add_argument("--no-ellipses", action="store_true")
        p.add_argument("--title")
        p.add_argument("--note", action="append", default=[])
        p.add_argument("--out", required=True, help=".svg (recommended) or .png")
        p.add_argument(
            "--bound-to",
            help="the split a demo split was cut from: predictions bound to it are accepted",
        )
    a = ap.parse_args(argv)
    try:
        labels = a.labels.split(",") if a.labels else [None] * len(a.predictions)
        if len(labels) != len(a.predictions):
            raise ValueError("--labels must name one label per prediction file")
        truth = load_truth(a.truth, a.scenario)
        ests = [
            load_rows(p, a.truth, a.scenario, lab, ESTIMATORS[i % len(ESTIMATORS)], a.bound_to)
            for i, (p, lab) in enumerate(zip(a.predictions, labels, strict=True))
        ]
        opts = TrackPlotOptions(
            at_s=_floats(a.at),
            from_s=a.from_s,
            title=a.title,
            ellipses=not a.no_ellipses,
            notes=list(a.note),
        )
        fig = (
            track_figure(truth, ests, opts)
            if a.kind == "track"
            else errors_figure(truth, ests, opts)
        )
        out = save(fig, Path(a.out), sidecar(a, argv))
    except (RecordError, ValueError, OSError, KeyError) as e:
        print(f"tma2-plot: {e}", file=sys.stderr)
        return 2
    print(str(out))
    return 0
