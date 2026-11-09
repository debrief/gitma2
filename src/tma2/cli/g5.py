"""tma2-g5: Gate 5's verdict from one scoring run (spec 010 FR-030…FR-033; T006, T016).

    uv run tma2-g5 --scoring <tma2-g2 output dir> --decision <decision.json> --split validation|test
        --head NAME=PATH --temperature NAME=PATH --classical NAME=PATH --raw NAME=PATH
        [--encshuf NAME=PATH …] --out <dir>

The scoring run has already written per-row arrays (``errors.npz``, with the slice labels) and the
inputs' digests (``inputs.json``); nothing is re-solved. Each NAME=PATH is a file that run scored.

* ``--head``: the carried stated E; ``--temperature`` and ``--classical``: the classical controls
  (the one with the lower summed score is the control of record); ``--raw``: E without a
  statement (G5-e).
* **Validation:** writes ``validation.json`` with the criteria, the per-slice table and the
  encoder-shuffle rule (``--encshuf`` at best and last epoch: if either beats the control of
  record wholly, a G5-d pass on test is void).
* **Test:** refuses unless the truth is the test digest beside the decision, the rows cover the
  whole σ = 1° split and the head carries the carried weights; reads the rule from the validation
  record by the digest in ``carried.json``; writes ``verdict.json``. Exit 3 when not passed.

Both records name the producing commit, its dirty flag and the CPU (read before writing).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from tma2.calib.gate import all_of, shuffled_rule_from


def _cpu() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    import platform

    return platform.processor() or platform.machine()


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
    roles = {"head": a.head, "temperature": a.temperature, "classical": a.classical, "raw": a.raw}
    for i, sh in enumerate(a.encshuf or []):
        roles[f"encshuf{i}"] = sh
    for role, (name, path) in roles.items():
        role = role.rstrip("0123456789")
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
                bad.append("--head: not the carried statement head")
            for role in ("head", "raw"):
                if _header(roles[role][1]).get("weights_sha256") != decision["carried_e_weights"]:
                    bad.append(f"--{role}: not the carried E's weights")
    if inputs.get("truth") != want:
        bad.append(f"the scoring run's truth is not the decision's {a.split} split")
    return bad, carried


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g5", description=__doc__)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--split", choices=("validation", "test"), required=True)
    for r in ("head", "temperature", "classical", "raw"):
        ap.add_argument(f"--{r}", type=_pair, required=True)
    ap.add_argument("--encshuf", type=_pair, action="append")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    from tma2.calib import gate5 as gate
    from tma2.calib.gate4 import scale_of, score_difference
    from tma2.data.provenance import read_git_provenance
    from tma2.segment.gate import sha256_file
    from tma2.types.generated.tma import Gate5Decision

    g = read_git_provenance()  # before anything is written
    producing = {"producing_commit": g.commit, "git_dirty": g.dirty, "cpu_model": _cpu()}
    sdir = Path(a.scoring)
    decision = Gate5Decision.model_validate_json(Path(a.decision).read_text()).model_dump()
    inputs = json.loads((sdir / "inputs.json").read_text())
    z = dict(np.load(sdir / "errors.npz"))
    if a.split == "validation" and a.encshuf is None:
        print("validation needs --encshuf (the encoder-shuffle rule)", file=sys.stderr)
        return 2
    bad, carried = preflight(a, decision, inputs, z)
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    level, n = float(decision["bootstrap_level"]), int(decision["bootstrap_resamples"])
    cluster = z["ordinal"]
    slices = {k[len("slice_") :]: z[k] for k in z if k.startswith("slice_")}
    slices = {k: v for k, v in slices.items() if k in set(decision["slices"])}
    controls = {a.temperature[0]: z[f"cal_{a.temperature[0]}"],
                a.classical[0]: z[f"cal_{a.classical[0]}"]}  # fmt: skip
    head_cal = z[f"cal_{a.head[0]}"]
    mass = float(_header(a.head[1]).get("calibration", {}).get("max_mass_error", 0.0))
    res = gate.criteria(head_cal, controls, z[f"err_{a.head[0]}"], z[f"err_{a.raw[0]}"],
                        cluster, slices, decision["criteria"], "pass", level, n, mass)  # fmt: skip
    ref = controls[res["control_of_record"]]
    if a.split == "validation":
        sh = {nm: score_difference(z[f"cal_{nm}"], ref, scale_of(ref), cluster, level, n)
              for nm, _ in a.encshuf}  # fmt: skip
        rule = gate.encshuf_rule(sh)
    else:
        assert carried is not None
        vpath = Path(a.decision).parent / carried["validation_record"]
        rule = shuffled_rule_from(vpath, carried["validation_sha256"])
        sh = None
    if res["g5d"] == gate.PASS and rule != gate.PASS:
        res["g5d"] = gate.FAIL  # void: recorded as not passed
    res["encshuf_rule"] = rule
    res["overall"] = all_of([res[k] for k in ("g5a", "g5b", "g5c", "g5d", "g5e")])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {
        "split": a.split,
        **producing,
        "decision_sha256": sha256_file(a.decision),
        "scoring_inputs": inputs,
        "rows": int(cluster.size),
        "scenarios": int(np.unique(cluster).size),
        "roles": {r: getattr(a, r)[0] for r in ("head", "temperature", "classical", "raw")},
        **res,
    }
    if a.split == "validation":
        rec["roles"]["encshuf"] = [nm for nm, _ in a.encshuf]
        rec["encshuf_minus_control"] = sh
        rec["shuffled_rule"] = rule  # read by the test split (shuffled_rule_from)
        (out / "validation.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(json.dumps({"encshuf_rule": rule, "overall_on_validation": res["overall"]}))
        return 0
    rec["decided_by"] = "agent review panel (pending)"
    (out / "verdict.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: res[k] for k in ("g5a", "g5b", "g5c", "g5d", "g5e", "overall")}))
    return 0 if res["overall"] == gate.PASS else 3


if __name__ == "__main__":
    raise SystemExit(main())
