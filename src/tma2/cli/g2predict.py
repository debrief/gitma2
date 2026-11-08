"""tma2-g2predict: E's per-row predictions (spec 007 T020, contracts/cli.md).

    uv run tma2-g2predict --in <split.f32pack> --segmentations <C.ndjson> --plan <plan.json>
        --model <id> [--ew-weights <best.safetensors>] [--es-weights <best.safetensors>]
        --start S --count N --out <pred.ndjson> [--workers 4]

``--model`` names a plan model; its ``kind`` (``e``: E-s then E-w; ``ew``: E-w alone; ``es``:
E-s alone, the physics layer on its segmentation; ``veto``: the classical controls, C with
candidates at the ownship zig ± ``window`` rows vetoed (``window`` −1: no veto), then E-w if the
model names one in ``ew`` or a fixed fading memory if it gives ``fade`` [a, b]) says which weights
it needs. Untrained weights
reproduce C. The header is an ``EPredictionHeader`` with the prediction file's ``estimator`` and
``mode``; ``weights_sha256`` is the SHA-256 of the weights files' digests joined by ``+`` in the
order E-s, E-w (each also recorded alone).

Refuses a segmentation file or checkout whose C digests are not the plan's.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tma2.data.provenance import read_git_provenance

CHUNK = 16  # as cli.segment


Task = tuple[int, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]


def _task(args: tuple[Any, ...]) -> list[Task]:
    import torch

    from tma2.gate2.es import ESSettings, make_net
    from tma2.gate2.model import EWeights
    from tma2.gate2.predict import e_rows, es_segmentations, veto_segmentations
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment import TRANSITION
    from tma2.segment.evidence import CHANNELS
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.sim.geometry import f32
    from tma2.types.generated.tma import PhysicsModelConfig, SegmentParameters

    path, start, count, params_json, plan, model_id, ew, es, segs, want_feats = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    p = SegmentParameters.model_validate_json(params_json)
    data, metas, owns, rows, ords, tgts = [], [], [], [], [], []
    for j, m, own, tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if ks:
            data.append(d)
            metas.append(m)
            owns.append(own)
            rows.append(ks)
            ords.append(j)
            tgts.append(tgt)
    if not data:
        return []
    from safetensors.torch import load_file

    veto = plan["models"][model_id].get("kind") == "veto"
    if veto:
        sg = veto_segmentations(data, rows, p, int(plan["models"][model_id]["window"]))
    elif es:
        net = make_net(ESSettings(**plan["es"]), CHANNELS)
        net.load_state_dict(load_file(es))
        net.eval()
        sg = es_segmentations(net, data, owns, rows, p)
    else:
        sg = [
            {k: segs[(j, k)] for k in ks if (j, k) in segs}
            for j, ks in zip(ords, rows, strict=True)
        ]
    model = None
    if ew:
        cfg = PhysicsModelConfig.model_validate(
            {**plan["encoder"], "id": model_id, "seed": plan["models"][model_id]["seed"]}
        )
        model = EWeights(cfg).double()
        model.load_state_dict(load_file(ew))
    c = plan["c"]
    f = plan["models"][model_id].get("fade")
    fade = (float(f[0]), float(f[1])) if f else None
    feats: dict[tuple[int, int], dict[str, Any]] | None = {} if want_feats else None
    out = e_rows(model, data, rows, sg, c["mode"], c.get("open_handover"), fade=fade, feats=feats)
    res: list[Task] = []
    for i, (j, m, r) in enumerate(zip(ords, metas, out, strict=True)):
        frows = []
        for q, k in enumerate(rows[i]):
            if feats is None or (i, q) not in feats:
                continue
            f = feats[(i, q)]
            ivs = sg[i].get(k) or []
            frows.append(
                {
                    "ordinal": j,
                    "k": k,
                    "t": f32(float(data[i].t[k])),
                    **f,
                    "truth": _truth_state(tgts[i], k),
                    "own": (float(data[i].ox[k]), float(data[i].oy[k])),
                    "plausible": bool(r[q]["converged"]),
                    "cov_ok": bool(r[q].get("cov_ok", False)),
                    "minute": int(
                        round((k - int(m["zig_index"])) * float(data[i].t[1] - data[i].t[0]) / 60.0)
                    ),
                    "open": bool(ivs) and ivs[-1].kind == TRANSITION and bool(ivs[-1].open),
                }
            )
        res.append((j, m, r, frows))
    return res


def _truth_state(tgt: Any, k: int) -> tuple[float, float, float, float]:
    import math

    _, x, y, c, sp = (float(v) for v in tgt[k])
    return (x, y, sp * math.sin(c), sp * math.cos(c))


def write_features(path: Path, frows: list[dict[str, Any]], header: dict[str, Any]) -> None:
    """The calibration head's feature cache (spec 008 data-model): one entry per scored row with
    E-w's encoder state; the header binds the prediction header's digests."""
    import numpy as np

    from tma2.physics.uncertainty import pack_cov

    frows = sorted(frows, key=lambda f: (f["ordinal"], f["k"]))
    np.savez_compressed(
        path,
        header=np.array(json.dumps(header, sort_keys=True)),
        ordinal=np.array([f["ordinal"] for f in frows], dtype=np.int64),
        k=np.array([f["k"] for f in frows], dtype=np.int64),
        t=np.array([f["t"] for f in frows], dtype=np.float64),
        h=np.array([f["h"] for f in frows], dtype=np.float64),
        cov=np.array([pack_cov(f["cov"]) for f in frows], dtype=np.float64),
        state=np.array([f["state"] for f in frows], dtype=np.float64),
        truth=np.array([f["truth"] for f in frows], dtype=np.float64),
        own=np.array([f["own"] for f in frows], dtype=np.float64),
        code_k=np.array([f["code_k"] for f in frows], dtype=np.float64),
        plausible=np.array([f["plausible"] for f in frows]),
        cov_ok=np.array([f["cov_ok"] for f in frows]),
        minute=np.array([f["minute"] for f in frows], dtype=np.int64),
        open=np.array([f["open"] for f in frows]),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g2predict", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--segmentations", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--ew-weights")
    ap.add_argument("--es-weights")
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--features", help="spec 008: the calibration head's feature cache (.npz)")
    a = ap.parse_args(argv)

    from tma2.cli.gs import read_segmentations
    from tma2.segment.codeid import code_digest
    from tma2.segment.gate import sha256_file
    from tma2.types.generated.tma import EPredictionHeader, RecordKind, SegmentParameters

    t0 = time.time()
    gp = read_git_provenance()  # before any output
    raw = Path(a.plan).read_bytes()
    plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    c = plan["c"]
    m = plan["models"].get(a.model)
    bad = []
    if m is None:
        bad.append(f"{a.model} is not a plan model")
    else:
        kind = m.get("kind", "e")
        need = {
            "e": ("es", "ew"),
            "ew": ("ew",),
            "es": ("es",),
            "veto": ("ew",) if m.get("ew") else (),
        }[kind]
        for w in ("es", "ew"):
            given = getattr(a, f"{w}_weights") is not None
            if given != (w in need):
                verb = "needs" if w in need else "takes no"
                bad.append(f"{a.model} ({kind}) {verb} --{w}-weights")
    header, segs = read_segmentations(a.segmentations)
    for key, want in (
        ("segmenter_sha256", c["parameters_sha256"]),
        ("code_sha256", c["code_sha256"]),
    ):
        if header.get(key) != want:
            bad.append(f"{a.segmentations}: {key} is not the plan's C")
    if code_digest() != c["code_sha256"]:
        bad.append("this checkout's segmenter code is not the plan's C (code_sha256)")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    p = SegmentParameters.model_validate(header["parameters"])
    digests = {
        w: sha256_file(getattr(a, f"{w}_weights"))
        for w in ("es", "ew")
        if getattr(a, f"{w}_weights")
    }
    joined = "+".join(digests[w] for w in ("es", "ew") if w in digests)
    wsha = hashlib.sha256(joined.encode()).hexdigest()
    h = EPredictionHeader(
        record=RecordKind.header,
        schema_version=header["schema_version"],
        model=a.model,
        weights_sha256=wsha,
        plan_sha256=plan_sha,
        dataset_digest=sha256_file(a.inp),
        parameters_sha256=c["parameters_sha256"],
        code_sha256=c["code_sha256"],
        git_commit=gp.commit,
        git_dirty=gp.dirty,
        model_settings=json.dumps(m, sort_keys=True, separators=(",", ":")),
        segmentation_sha256=sha256_file(a.segmentations),
    ).model_dump(mode="json", exclude_none=True)
    h |= {f"{w}_weights_sha256": v for w, v in digests.items()}
    h |= {"estimator": f"E-{a.model}", "mode": "per_timestep"}
    chunks = [
        (
            a.inp,
            s,
            min(CHUNK, a.start + a.count - s),
            p.model_dump_json(),
            plan,
            a.model,
            a.ew_weights,
            a.es_weights,
            {key: v for key, v in segs.items() if s <= key[0] < s + CHUNK},
            a.features is not None,
        )
        for s in range(a.start, a.start + a.count, CHUNK)
    ]
    from tma2.data.canonical import canonical_json

    recs: list[tuple[int, dict[str, Any], list[dict[str, Any]]]] = []
    frows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for part in ex.map(_task, chunks):
            for j, meta, rws, fr in part:
                recs.append((j, meta, rws))
                frows += fr
            print(f"{len(recs)} scenarios [{time.time() - t0:.0f} s]", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(canonical_json(h) + "\n")
        for j, meta, rows in sorted(recs, key=lambda r: r[0]):
            f.write(
                canonical_json(
                    {
                        "record": "prediction",
                        "ordinal": j,
                        "scenario_index": int(meta["index"]),
                        "estimator": h["estimator"],
                        "mode": "per_timestep",
                        "rows": rows,
                    }
                )
                + "\n"
            )
    if a.features:
        write_features(Path(a.features), frows, h)
    print(f"wrote {out}: {len(recs)} scenarios [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
