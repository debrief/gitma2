"""tma2-g3: Gate 3's verdict from one scoring run (spec 008 FR-030…FR-033, FR-063; T027).

    uv run tma2-g3 --scoring <tma2-g2 output dir> --decision <decision.json> --split validation|test
        --head NAME=PATH --temperature NAME=PATH --raw NAME=PATH [--shuffled NAME=PATH] --out <dir>

The scoring run (``tma2-g2``/``tma2-gs`` with the calibrated prediction files as ``--e``) has
already written per-row errors and calibration arrays (``errors.npz``) and the inputs' digests
(``inputs.json``); nothing is re-solved here. Each NAME=PATH names a prediction file the run
scored: its digest must be the one in ``inputs.json``.

* ``--head``: the carried calibrated E (calibration head); ``--temperature``: the classical
  control (E with the per-slice temperature); ``--raw``: E uncalibrated (G3-d).
* **Validation:** writes ``validation.json`` with the criteria on validation and the shuffled rule
  (``--shuffled``: the shuffled head's interval score minus the temperature's, wholly below zero →
  the rule fails and a G3-c pass on test would be void).
* **Test:** refuses unless the truth is the test digest beside the decision, the rows cover the
  whole σ = 1° split (FR-032), and the head and raw files carry the carried weights; reads the
  shuffled rule from the validation record by the digest in ``carried.json`` (FR-063); writes
  ``verdict.json``. Exit 3 when the gate is not passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


def _pair(spec: str) -> tuple[str, Path]:
    name, _, path = spec.partition("=")
    if not name or not path:
        raise argparse.ArgumentTypeError(f"{spec}: expected NAME=PATH")
    return name, Path(path)


def _header(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        h: dict[str, Any] = json.loads(fh.readline())
    return h


def preflight(
    a: argparse.Namespace, decision: dict[str, Any], inputs: dict[str, Any], z: Any
) -> tuple[list[str], dict[str, Any] | None]:
    from tma2.segment.gate import sha256_file

    bad: list[str] = []
    dpath = Path(a.decision)
    preds = inputs.get("predictions", {})
    roles = {"head": a.head, "temperature": a.temperature, "raw": a.raw}
    if a.shuffled:
        roles["shuffled"] = a.shuffled
    for role, (name, path) in roles.items():
        if preds.get(name) != sha256_file(path):
            bad.append(f"--{role} {name}: {path} is not the file the scoring run read")
        if f"cal_{name}" not in z or f"err_{name}" not in z:
            bad.append(f"--{role} {name}: not in the scoring run's errors.npz")
    want = decision["validation_digest"]
    carried = None
    if a.split == "test":
        td = dpath.parent / "test-digest.json"
        tdj = json.loads(td.read_text()) if td.exists() else {}
        want = tdj.get("dataset_digest", "")
        if not want:
            bad.append("test-digest.json is not beside the decision")
        else:
            n = tdj.get("sigma1_scenarios")
            ords = np.unique(z["ordinal"])
            if n is None or not np.array_equal(ords, np.arange(n)):
                bad.append(f"the scored rows do not cover the σ = 1° test split ({n} scenarios)")
        cp = dpath.parent / "carried.json"
        if not cp.exists():
            bad.append("carried.json is not beside the decision")
        else:
            carried = json.loads(cp.read_text())
            hh = _header(a.head[1]).get("calibration", {})
            if hh.get("weights_sha256") != carried.get("head_weights_sha256"):
                bad.append("--head: not the carried calibration head")
            for role in ("head", "raw"):
                if _header(roles[role][1]).get("weights_sha256") != decision["carried_e_weights"]:
                    bad.append(f"--{role}: not the carried E's weights")
    if inputs.get("truth") != want:
        bad.append(f"the scoring run's truth is not the decision's {a.split} split")
    return bad, carried


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g3", description=__doc__)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--split", choices=("validation", "test"), required=True)
    ap.add_argument("--head", type=_pair, required=True)
    ap.add_argument("--temperature", type=_pair, required=True)
    ap.add_argument("--raw", type=_pair, required=True)
    ap.add_argument("--shuffled", type=_pair)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    from tma2.calib import gate
    from tma2.segment.gate import sha256_file
    from tma2.types.generated.tma import Gate3Decision

    sdir = Path(a.scoring)
    decision = Gate3Decision.model_validate_json(Path(a.decision).read_text()).model_dump()
    inputs = json.loads((sdir / "inputs.json").read_text())
    z = dict(np.load(sdir / "errors.npz"))
    if a.split == "validation" and a.shuffled is None:
        print("validation needs --shuffled (the shuffled rule)", file=sys.stderr)
        return 2
    bad, carried = preflight(a, decision, inputs, z)
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    level, n = float(decision["bootstrap_level"]), int(decision["bootstrap_resamples"])
    cluster = z["ordinal"]
    if a.split == "validation":
        sh = gate.score_difference(
            z[f"cal_{a.shuffled[0]}"], z[f"cal_{a.temperature[0]}"], cluster, level, n
        )
        rule = gate.shuffled_rule(sh)
    else:
        assert carried is not None
        vpath = Path(a.decision).parent / carried["validation_record"]
        rule = gate.shuffled_rule_from(vpath, carried["validation_sha256"])
        sh = None
    res = gate.criteria(
        z[f"cal_{a.head[0]}"],
        z[f"cal_{a.temperature[0]}"],
        z[f"err_{a.head[0]}"],
        z[f"err_{a.raw[0]}"],
        cluster,
        decision["criteria"],
        rule,
        level,
        n,
    )
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {
        "split": a.split,
        "decision_sha256": sha256_file(a.decision),
        "scoring_inputs": inputs,
        "rows": int(cluster.size),
        "scenarios": int(np.unique(cluster).size),
        "roles": {r: getattr(a, r)[0] for r in ("head", "temperature", "raw")},
        **res,
    }
    if a.split == "validation":
        rec["roles"]["shuffled"] = a.shuffled[0]
        rec["shuffled_minus_temperature"] = sh
        (out / "validation.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(json.dumps({"shuffled_rule": rule, "overall_on_validation": res["overall"]}))
        return 0
    rec["decided_by"] = "agent review panel (pending)"
    (out / "verdict.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: res[k] for k in ("g3a", "g3b", "g3c", "g3d", "overall")}))
    return 0 if res["overall"] == gate.PASS else 3


if __name__ == "__main__":
    raise SystemExit(main())
