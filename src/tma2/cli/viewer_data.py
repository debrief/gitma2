"""tma2-viewer-data: the browser viewer's demo data (spec 020).

    uv run python -m tma2.gate2.export --out <export> --plan configs/gate2/g2-a.json \\
        --weights experiments/20261107-g2-val/models/ew-s3/best.safetensors
    uv run tma2-viewer-data --split <seed 319 dir>/test.f32pack --export <export> \\
        --out site/static/viewer-data

Seed 319's test split (Gate 2's, used; generate it with the command in
``experiments/20261107-g2-decision/seed319-digests.json``). Refuses an export whose weights are
not the carried E-w's, E-s weights that are not the carried E-s's, or a checkout whose segmenter
code is not the plan's C. Writes ``model.onnx`` (the export's, unchanged), one
``engagement-<i>.json.gz`` and ``engagement-<i>.bin.gz`` per demo engagement, and
``manifest.json`` binding them all by SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

from tma2.data.provenance import read_git_provenance

ROOT = Path(__file__).resolve().parents[3]
PLAN = "configs/gate2/g2-a.json"
CARRIED = "experiments/20261107-g2-decision/carried.json"
EW = "experiments/20261107-g2-val/models/ew-s3/best.safetensors"
ES = "experiments/20261107-g2-val/models/es-s3/best.safetensors"
SEED319 = "experiments/20261107-g2-decision/seed319-digests.json"
GATE2_POST = "/blog/2026/11/08/gate-2"
GATE3_RECORD = "experiments/20261108-g3-val/"
LIMIT = 200
# Gate 2's g2predict cut seed 319's 4,983 σ = 1° ordinals into 16 shards of 312 and chunked each
# from its own start; the builder's chunks (multiples of 16) match only within the first shard.
MAX_LIMIT = 312


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-viewer-data", description=__doc__)
    ap.add_argument("--split", required=True, help="seed 319's test.f32pack")
    ap.add_argument("--export", required=True, help="gate2.export's output, carried weights")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=LIMIT)
    a = ap.parse_args(argv)
    if not 0 < a.limit <= MAX_LIMIT:
        ap.error(f"--limit must be in 1..{MAX_LIMIT}: beyond it the chunks are not Gate 2's")

    from tma2.segment.codeid import code_digest
    from tma2.viewer.build import SYSTEM_LABELS, Builder, pack_engagement, sha256
    from tma2.viewer.choose import ORDER, choose

    t0 = time.time()
    g = read_git_provenance()  # before any output
    carried = json.loads((ROOT / CARRIED).read_text())
    plan_bytes = (ROOT / PLAN).read_bytes()
    plan = json.loads(plan_bytes)
    export = Path(a.export)
    leg = json.loads((export / "python_leg.json").read_text())
    bad = []
    if sha_file(ROOT / EW) != carried["ew_weights_sha256"]:
        bad.append(f"{EW} is not the carried E-w")
    if sha_file(ROOT / ES) != carried["es_weights_sha256"]:
        bad.append(f"{ES} is not the carried E-s")
    if Path(leg.get("weights", "")).resolve() != (ROOT / EW).resolve():
        bad.append(f"{export} was not exported with {EW}")
    if leg.get("calibration_head"):
        bad.append(f"{export} carries a calibration head; the viewer runs E-w alone")
    if sha_file(export / "model.onnx") != leg["onnx_sha256"]:
        bad.append(f"{export}/model.onnx is not the export's")
    if code_digest() != plan["c"]["code_sha256"]:
        bad.append("this checkout's segmenter code is not the plan's C (code_sha256)")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2

    b = Builder(Path(a.split), export, ROOT / PLAN, ROOT / ES)
    picks, missing = choose(b.candidates(a.limit), b.e_loses, lambda j: any(b.engagement(j).have_e))
    print(f"picked {[(p.ordinal, p.reason) for p in picks]}; missing {missing}", flush=True)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(export / "model.onnx", out / "model.onnx")
    files = {"model.onnx": sha_file(out / "model.onnx")}
    engagements = []
    for i, p in enumerate(picks):
        eng = b.engagement(p.ordinal)
        js, bn = pack_engagement(eng, p.reason, b.dtypes)
        for suffix, blob in (("json.gz", js), ("bin.gz", bn)):
            name = f"engagement-{i}.{suffix}"
            (out / name).write_bytes(blob)
            files[name] = sha256(blob)
        engagements.append(
            {
                "id": i,
                "ordinal": p.ordinal,
                "scenario_index": int(eng.meta["index"]),
                "reason": p.reason,
                "manoeuvres": p.manoeuvres,
                "rows": len(eng.rows),
                "e_rows": int(sum(eng.have_e)),
                "json": f"engagement-{i}.json.gz",
                "binary": f"engagement-{i}.bin.gz",
            }
        )
        print(f"engagement {i}: ordinal {p.ordinal} [{time.time() - t0:.0f} s]", flush=True)
    seed = json.loads((ROOT / SEED319).read_text())
    manifest = {
        "what": (
            "Demo data for the browser viewer (spec 020): the carried Gate 2 model E's exported "
            "E-w graph and its inputs on a few simulated engagements. A demonstration, not a "
            "result."
        ),
        "model": {
            "file": "model.onnx",
            "sha256": files["model.onnx"],
            "exported_by": "python -m tma2.gate2.export --plan configs/gate2/g2-a.json "
            f"--weights {EW}",
            "ew_weights_sha256": carried["ew_weights_sha256"],
            "es_weights_sha256": carried["es_weights_sha256"],
            "carried": CARRIED,
            "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
            "c_code_sha256": plan["c"]["code_sha256"],
            "c_parameters_sha256": plan["c"]["parameters_sha256"],
            "python_leg": {k: leg[k] for k in ("max_rel_diff", "runtime", "nodes", "iterations")},
            "window_rows": leg["window_rows"],
        },
        "data": {
            "seed": 319,
            "split": "test",
            "used_by": "Gate 2's test record (experiments/20261107-g2/)",
            "generate": seed["command"],
            "generator_version": seed["generator_version"],
            "split_sha256_at_generation": seed["test.f32pack"],
            "selection": {
                "rule": "tma2.viewer.choose (spec 020 research R2)",
                "order": list(ORDER),
                "limit": a.limit,
                "missing": missing,
            },
        },
        "rows": "every 60 s from the first G5 row (zig + 5 min) to the end of the window",
        "systems": SYSTEM_LABELS,
        "uncertainty_warning": (
            "E's stated covariance is overconfident: its 95% intervals held the truth on 0.60 "
            f"of rows, not 0.95 (Gate 3, {GATE3_RECORD}). The ellipse is not a calibrated "
            "uncertainty."
        ),
        "links": {"gate2": GATE2_POST, "gate3": GATE3_RECORD},
        "engagements": engagements,
        "files": files,
        "built": {
            "command": "tma2-viewer-data " + " ".join(sys.argv[1:] if argv is None else argv),
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "seconds": round(time.time() - t0, 1),
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    total = sum((out / f).stat().st_size for f in files)
    print(f"wrote {out}: {len(picks)} engagements, {total / 1e6:.2f} MB [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
