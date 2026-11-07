"""Gate 2 panel, round 1 (geometry major): does a classical rule match E-s on its own objective?

The rule shifts C's confirmation threshold by ``b`` everywhere and by +τ/2 (E-s's largest shift)
for candidates whose evidence rows touch the ownship zig ± W rows. Its hard decision-table loss is
compared with E-s's on the validation tuning tables (seed 314 ordinals 0–499, where E-s
early-stopped) and checked on the training stream's tables (seed 318).

    uv run python scripts/research/g2_zig_veto_tables.py <dir> <seed-314 validation.f32pack> \
        <seed-318 train.f32pack>

``<dir>`` holds ``tval/`` and ``tstream/`` (the ``tma2-dtables`` shards of
results/dtables-g2-val-tune-42288137249 and results/dtables-g2-stream-42295008170) and
``runs/<model>/best.safetensors`` (results/g2-g2-a-42352638177).
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file

from tma2.gate2.es import ESExample, ESSettings, example_of, forward, make_net, shifts
from tma2.gate2.tables import load_tables
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment.evidence import scenario_features
from tma2.segment.score import iter_selected
from tma2.types.generated.tma import SegmentParameters

ROOT = Path(__file__).resolve().parents[2]
TAU = 13.8
BASES = [-TAU / 2, -TAU / 4, 0.0, TAU / 4]
WINDOWS = [-1, 0, 3, 6, 12, 24]  # -1: no veto

Arrays = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]


def load(
    tabdir: Path, pack: str, count: int, p: SegmentParameters, feats: bool
) -> tuple[list[ESExample], dict[int, int]]:
    tabs = {}
    for f in sorted(glob.glob(str(tabdir / "shard-*.npz"))):
        tabs.update(load_tables(f)[1])
    xs, zig = [], {}
    for j, m, own, _tgt, obs in iter_selected(pack, 0, count):
        if j not in tabs:
            continue
        zig[j] = int(m["zig_index"])
        d = bearing_data_from_arrays(m, own, obs)
        f = scenario_features(d, own, p) if feats else np.zeros((1, own.shape[0]))
        xs.append(example_of(j, f, tabs[j]))
    return xs, zig


def arrays(xs: list[ESExample], zig: dict[int, int]) -> Arrays:
    def cat(f: str) -> np.ndarray:
        return np.concatenate([getattr(x, f) for x in xs])

    z = np.concatenate([np.full(x.start.size, zig[x.ordinal]) for x in xs])
    return cat("margin"), cat("e_with"), cat("e_without"), cat("start"), cat("end"), z


def rule_loss(a: Arrays, b: float, w: int) -> float:
    m, ew, eo, s, e, z = a
    shift = np.where((s <= z + w) & (e >= z - w), TAU / 2, b) if w >= 0 else np.full(m.size, b)
    return float(np.where(m - shift > 0, ew, eo).mean())


def es_loss(xs: list[ESExample], weights: Path, plan: dict[str, object]) -> float:
    net = make_net(ESSettings(**{**plan["es"], "seed": 1}), xs[0].feats.shape[0])  # type: ignore[dict-item]
    net.load_state_dict(load_file(str(weights)))
    net.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(xs), 16):
            part = [x for x in xs[i : i + 16] if x.start.size]
            for ev, x in zip(forward(net, part), part, strict=True):
                sh = shifts(ev, x).numpy()
                out.append(np.where(x.margin - sh > 0, x.e_with, x.e_without))
    return float(np.concatenate(out).mean())


def main() -> None:
    torch.set_default_dtype(torch.float64)
    root, val, stream = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    gs = json.loads((ROOT / "configs/segment/gs-plan.json").read_text())
    p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
    plan = json.loads((ROOT / "configs/gate2/g2-a.json").read_text())
    for label, tabdir, pack, count, feats in (
        ("tuning", root / "tval", val, 500, True),
        ("stream", root / "tstream", stream, 9930, False),
    ):
        xs, zig = load(tabdir, pack, count, p, feats)
        a = arrays(xs, zig)
        print(f"{label}: {len(xs)} scenarios, {a[0].size} rows; C {rule_loss(a, 0.0, -1):.4f}")
        for b in BASES:
            cells = " ".join(f"W{w}:{rule_loss(a, b, w):.4f}" for w in WINDOWS)
            print(f"  b={b:+.2f} {cells}")
        if feats:
            for n in ("es-s1", "es-s2", "es-s3", "es-shuffled"):
                print(f"  {n}: {es_loss(xs, root / 'runs' / n / 'best.safetensors', plan):.4f}")


if __name__ == "__main__":
    main()
