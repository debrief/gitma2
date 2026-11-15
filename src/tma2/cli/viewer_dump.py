"""tma2-viewer-dump: every intermediate of C and E on the port's check scenarios (spec 021).

    uv run tma2-viewer-dump --split <seed 319 dir>/test.f32pack --out <dir> [--extra 24]

The check scenarios are the viewer's six demo engagements (``site/static/viewer-data/
manifest.json``) and the next ``--extra`` eligible σ = 1° ordinals of the split after the
largest demo ordinal, in order (spec 021 plan). One ``scenario-<ordinal>.json.gz`` each
(``tma2.viewer.dump``) and ``index.json``.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tma2.data.provenance import read_git_provenance

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "site/static/viewer-data/manifest.json"
PLAN = "configs/gate2/g2-a.json"
ES = "experiments/20261107-g2-val/models/es-s3/best.safetensors"


def _one(args: tuple[str, int, str]) -> tuple[int, float]:
    import torch
    from safetensors.torch import load_file

    from tma2.gate2.es import ESSettings, make_net
    from tma2.segment.evidence import CHANNELS
    from tma2.segment.score import iter_selected
    from tma2.types.generated.tma import SegmentParameters
    from tma2.viewer.build import grid_rows
    from tma2.viewer.dump import dump_scenario, write

    split, j, out = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    plan = json.loads((ROOT / PLAN).read_text())
    gs = json.loads((ROOT / plan["c"]["parameters_from"]).read_text())
    p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
    net = make_net(ESSettings(**plan["es"]), CHANNELS)
    net.load_state_dict(load_file(str(ROOT / ES)))
    net.eval()
    t0 = time.time()
    for jj, meta, own, _tgt, obs in iter_selected(split, j, 1):
        doc = dump_scenario(jj, meta, own, obs, grid_rows(meta, obs.shape[0]), net, p)
        write(Path(out) / f"scenario-{jj}.json.gz", doc)
    return j, time.time() - t0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-viewer-dump", description=__doc__)
    ap.add_argument("--split", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", help="comma-separated ordinals (development)")
    a = ap.parse_args(argv)

    from tma2.segment.score import iter_selected
    from tma2.viewer.build import eligible

    g = read_git_provenance()
    man = json.loads((ROOT / MANIFEST).read_text())
    demos = [e["ordinal"] for e in man["engagements"]]
    if a.only:
        ords = [int(x) for x in a.only.split(",")]
    else:
        extra: list[int] = []
        for j, m, _o, _t, obs in iter_selected(a.split, max(demos) + 1, 400):
            if len(extra) == a.extra:
                break
            if eligible(m, obs.shape[0]):
                extra.append(j)
        ords = sorted(demos) + extra
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    times: dict[str, Any] = {}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for j, s in ex.map(_one, [(a.split, j, str(out)) for j in ords]):
            times[str(j)] = round(s, 1)
            print(f"ordinal {j}: {s:.0f} s", flush=True)
    (out / "index.json").write_text(
        json.dumps(
            {
                "ordinals": ords,
                "demos": demos,
                "seconds": times,
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "split": "seed 319 test (used)",
                "r_max": 720,
            },
            indent=1,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
