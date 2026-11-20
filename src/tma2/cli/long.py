"""tma2-long: the standing systems on long engagements (spec 023, issue #42).

    uv run tma2-long realtime --index 0 --out <dir>    # E, C″, one leg, IMM every 10 min
    uv run tma2-long timelate --index 0 --out <dir>    # ctl on a chain of 2-hour windows
    uv run tma2-long scaling --index 2 --out <dir>     # ctl on single periods of growing length
    uv run tma2-long realtime-inc --index 0 --out <dir>   # spec 024: the incremental C
    uv run tma2-long carry --index 0 --out <dir>          # spec 024: ctl and ctl carrying state
    uv run tma2-long carry2 --index 0 --out <dir>         # spec 027: and ctl carrying a prior
    uv run tma2-long study27 --raw <dir> --config <study config> --out <dir>   # spec 027's study
    uv run tma2-long study29 --raw <dir> --config <hold config> --out <dir>    # spec 029's study
    uv run tma2-long jointheld --index 0 --window-s 3600 --overlap-s 900 --out <dir>   # spec 030
    uv run tma2-long study30 --raw <dir> --config <config> --out <dir>         # spec 030's study
    ... --config configs/long/realistic.json --contact 2  # spec 024: realism; the second contact

The engagement is ``configs/long/long.json``'s ``index``-th (in order of duration). Writes
``<part>-<index>.npz`` (arrays) and ``<part>-<index>.json`` (provenance, timings, histories).
An investigation's measurement, never a gate result.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.provenance import read_git_provenance

CONFIG = "configs/long/long.json"


def _engagement(index: int, config: str, contact: int = 1) -> tuple[Any, dict[str, Any]]:
    from tma2.long.sim import generate

    cfg = json.loads(Path(config).read_text())
    R = json.loads(Path(cfg["target_ranges"]).read_text())
    hours = [float(h) for h in cfg["hours"] for _ in range(int(cfg["engagements_per_duration"]))]
    e = generate(int(cfg["seed"]), index, hours[index], cfg, R)
    if contact == 2:
        if e.other is None:
            raise SystemExit(f"{config} has no second contact")
        e = e.other
    return e, cfg


def _cpu() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-long", description=__doc__)
    ap.add_argument(
        "part",
        choices=(
            "realtime",
            "realtime-inc",
            "timelate",
            "carry",
            "carry2",
            "jointpair",
            "jointheld",
            "scaling",
            "imm",
            "study",
            "study27",
            "study29",
            "study30",
        ),
    )
    ap.add_argument("--indices", default="", help="imm: engagements a-b (inclusive)")
    ap.add_argument("--raw", default="", help="study: the run's outputs")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=CONFIG)
    ap.add_argument("--contact", type=int, default=1, choices=(1, 2), help="spec 024 realism")
    ap.add_argument("--block-s", type=float, default=7200.0, help="realtime-inc: block length")
    ap.add_argument(
        "--carry-settings", default="configs/long/carry2.json", help="carry2: scale, tail, alpha"
    )
    ap.add_argument("--pair", type=int, default=1, help="jointpair: windows pair-1 and pair")
    ap.add_argument("--tag", default="", help="a name for the outputs (default: the config's)")
    ap.add_argument("--step-s", type=float, default=600.0, help="realtime: evaluation interval")
    ap.add_argument("--limit", type=int, default=0, help="realtime: first N evaluations only")
    ap.add_argument(
        "--shard",
        default="0/1",
        help="realtime, timelate: i/n, a contiguous share of evaluations or windows",
    )
    ap.add_argument("--window-s", type=float, default=7200.0, help="timelate: window length")
    ap.add_argument("--overlap-s", type=float, default=1800.0, help="timelate: overlap")
    ap.add_argument("--max-windows", type=int, default=0, help="timelate: first N windows only")
    ap.add_argument("--lengths", default="1800,3600,5400,7200,10800,14400", help="scaling, s")
    ap.add_argument("--start-s", type=float, default=3600.0, help="scaling: where periods start")
    a = ap.parse_args(argv)

    g = read_git_provenance()  # before any output
    t0 = time.time()
    if a.part == "study":
        from tma2.long.study import score

        res = score(Path(a.raw).resolve(), Path(a.config).resolve())
        res["git_commit"], res["git_dirty"] = g.commit, g.dirty
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "study.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        print(
            json.dumps(
                {k: res[k] for k in ("soundness", "E1", "E2", "E3")}, indent=1, default=float
            )
        )
        return 0
    if a.part == "study27":
        from tma2.long.study27 import score27

        res = score27(Path(a.raw).resolve(), Path(a.config).resolve())
        res["git_commit"], res["git_dirty"] = g.commit, g.dirty
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "study.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        print(json.dumps(res["rule"], indent=1, default=float))
        return 0
    if a.part == "study30":
        from tma2.long.study30 import score30

        res = score30(Path(a.raw).resolve(), Path(a.config).resolve())
        res["git_commit"], res["git_dirty"] = g.commit, g.dirty
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "study.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        print(json.dumps(res["soundness"], indent=1, default=float))
        print(json.dumps(res["outcome"], default=float))
        return 0
    if a.part == "study29":
        from tma2.long.study29 import score29

        res = score29(Path(a.raw).resolve(), Path(a.config).resolve())
        res["git_commit"], res["git_dirty"] = g.commit, g.dirty
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "study.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        print(json.dumps({k: res[k] for k in ("soundness", "classes")}, indent=1, default=float))
        print(res["rule"]["outcome"])
        return 0
    if a.part == "imm":
        from tma2.long.realtime import IMM, imm_states

        lo, hi = (int(x) for x in a.indices.split("-"))
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        tag = a.tag or Path(a.config).stem
        for i in range(lo, hi + 1):
            e, _cfg = _engagement(i, a.config, a.contact)
            r = imm_states(e)
            np.savez_compressed(
                out / f"{tag}-c{a.contact}-imm-{i}.npz",
                times_s=r["times_s"],
                truth=r["truth"],
                state_imm=r["state_imm"],
            )
            print(json.dumps({"part": "imm", "index": i, "seconds": round(r["seconds"], 1)}))
        (out / f"{tag}-c{a.contact}-imm-{lo}-{hi}.json").write_text(
            json.dumps(
                {"imm": IMM, "git_commit": g.commit, "git_dirty": g.dirty, "cpu_model": _cpu()},
                indent=1,
            )
            + "\n"
        )
        return 0
    e, cfg = _engagement(a.index, a.config, a.contact)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    head: dict[str, Any] = {
        "part": a.part,
        "index": a.index,
        "hours": e.meta["hours"],
        "seed": cfg["seed"],
        "config": a.config,
        "contact": a.contact,
        "engagement": {k: v for k, v in e.meta.items() if k != "parameters"}
        | {
            "parameters": {
                k: v for k, v in e.meta["parameters"].items() if k != "target_manoeuvres"
            }
        },
        "target_manoeuvres": e.meta["parameters"]["target_manoeuvres"],
        "git_commit": g.commit,
        "git_dirty": g.dirty,
        "cpu_model": _cpu(),
    }
    arrays: dict[str, Any] = {}
    if a.part == "realtime":
        from tma2.long.realtime import RealTime

        i_sh, n_sh = (int(x) for x in a.shard.split("/"))
        r = RealTime().run(e, step_s=a.step_s, limit=a.limit, shard=(i_sh, n_sh))
        head["shard"] = [i_sh, n_sh]
        arrays = {"rows": r["rows"], "times_s": r["times_s"], "truth": r["truth"]}
        arrays.update({f"state_{s}": v for s, v in r["states"].items()})
        head["seconds"] = r["seconds"]
        head["step_s"] = a.step_s
    elif a.part == "realtime-inc":
        from tma2.long.incremental import Incremental

        i_sh, n_sh = (int(x) for x in a.shard.split("/"))
        r = Incremental().run_incremental(
            e, step_s=a.step_s, block_s=a.block_s, limit=a.limit, shard=(i_sh, n_sh)
        )
        head["shard"] = [i_sh, n_sh]
        arrays = {"rows": r["rows"], "times_s": r["times_s"], "truth": r["truth"]}
        arrays.update({f"state_{s}": v for s, v in r["states"].items()})
        head["seconds"] = r["seconds"]
        head["step_s"], head["block_s"] = a.step_s, a.block_s
    elif a.part == "carry":
        from tma2.long import carry as cm
        from tma2.long.timelate import chain, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        spans = chain(e, a.window_s, a.overlap_s)
        i_sh, n_sh = (int(x) for x in a.shard.split("/"))
        lo, hi = len(spans) * i_sh // n_sh, len(spans) * (i_sh + 1) // n_sh
        if a.max_windows:
            hi = min(hi, lo + a.max_windows)
        wins = cm.run_chain(e, spans, lo, hi, s, priors, cp, c2)
        for w in wins:
            j = w["index"]
            arrays[f"w{j}_rows"] = w["rows_abs"]
            for k in cm.SYSTEMS:
                arrays[f"w{j}_{k}"] = w["tracks"][k]
        head["chain"] = spans
        head["shard"] = [i_sh, n_sh]
        head["systems"] = list(cm.SYSTEMS)
        head["windows"] = [
            {
                k: w[k]
                for k in (
                    "index",
                    "first",
                    "rows",
                    "seconds",
                    "parts",
                    "search_s",
                    "bearings",
                    "declared",
                    "true",
                )
            }
            for w in wins
        ]
        head["window_s"], head["overlap_s"] = a.window_s, a.overlap_s
        head["settings"] = s
    elif a.part == "carry2":
        from tma2.long import carry2 as c2m
        from tma2.long.timelate import chain, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        cs = json.loads(Path(a.carry_settings).read_text())
        spans = chain(e, a.window_s, a.overlap_s)
        if a.max_windows:
            spans = spans[: a.max_windows]
        wins = c2m.run_chain2(e, spans, s, priors, cp, c2, cs)
        for w in wins:
            j = w["index"]
            arrays[f"w{j}_rows"] = w["rows_abs"]
            for k in c2m.SYSTEMS2:
                arrays[f"w{j}_{k}"] = w["tracks"][k]
        head["chain"] = spans
        head["systems"] = list(c2m.SYSTEMS2)
        head["carry_settings"] = cs
        head["windows"] = [
            {
                k: w[k]
                for k in (
                    "index",
                    "first",
                    "rows",
                    "seconds",
                    "parts",
                    "search_s",
                    "bearings",
                    "declared",
                    "true",
                    "handed",
                    "guard",
                )
            }
            for w in wins
        ]
        head["window_s"], head["overlap_s"] = a.window_s, a.overlap_s
        head["settings"] = s
    elif a.part == "jointpair":
        from tma2.long.timelate import SYSTEMS, chain, run_windows, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        spans = chain(e, a.window_s, a.overlap_s)
        (a0, _r0), (a1, r1) = spans[a.pair - 1], spans[a.pair]
        wins = run_windows(e, [(a0, a1 + r1 - a0)], s, priors, cp, c2)
        w = wins[0]
        keep = np.asarray(w["rows_abs"]) >= a1
        arrays["rows"] = np.asarray(w["rows_abs"])[keep]
        for k in SYSTEMS:
            arrays[k] = w["tracks"][k][keep]
        head["pair"] = a.pair
        head["union"] = [a0, a1 + r1 - a0]
        head["second"] = [a1, r1]
        head["seconds"] = w["seconds"]
        head["parts"] = w["parts"]
        head["declared"] = w["declared"]
    elif a.part == "jointheld":
        from tma2.long.study29 import turns_in
        from tma2.long.timelate import SYSTEMS, chain, run_windows, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        spans = chain(e, a.window_s, a.overlap_s)
        done: list[dict[str, Any]] = []
        for j in range(1, len(spans)):
            a1, r1 = spans[j]
            if turns_in(e, a1, r1) != 0:
                continue
            if a.max_windows and len(done) >= a.max_windows:
                break
            a0 = spans[j - 1][0]
            w = run_windows(e, [(a0, a1 + r1 - a0)], s, priors, cp, c2)[0]
            keep = np.asarray(w["rows_abs"]) >= a1
            arrays[f"w{j}_rows"] = np.asarray(w["rows_abs"])[keep]
            for k in SYSTEMS:
                arrays[f"w{j}_{k}"] = w["tracks"][k][keep]
            done.append(
                {
                    "index": j,
                    "first": int(a1),
                    "rows": int(r1),
                    "union": [int(a0), int(a1 + r1 - a0)],
                    "seconds": float(w["seconds"]),
                    "declared": w["declared"],
                }
            )
        head["chain"] = spans
        head["systems"] = list(SYSTEMS)
        head["windows"] = done
        head["window_s"], head["overlap_s"] = a.window_s, a.overlap_s
        head["settings"] = s
    elif a.part == "timelate":
        from tma2.long.timelate import SYSTEMS, chain, run_windows, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        spans = chain(e, a.window_s, a.overlap_s)
        i_sh, n_sh = (int(x) for x in a.shard.split("/"))
        lo, hi = len(spans) * i_sh // n_sh, len(spans) * (i_sh + 1) // n_sh
        if a.max_windows:
            hi = min(hi, lo + a.max_windows)
        wins = run_windows(e, spans[lo:hi], s, priors, cp, c2)
        for j, w in zip(range(lo, hi), wins, strict=True):
            arrays[f"w{j}_rows"] = w["rows_abs"]
            for k in SYSTEMS:
                arrays[f"w{j}_{k}"] = w["tracks"][k]
        head["chain"] = spans
        head["shard"] = [i_sh, n_sh]
        head["windows"] = [
            {"index": j}
            | {
                k: w[k]
                for k in ("first", "rows", "seconds", "parts", "bearings", "declared", "true")
            }
            for j, w in zip(range(lo, hi), wins, strict=True)
        ]
        head["window_s"], head["overlap_s"] = a.window_s, a.overlap_s
        head["settings"] = s
    else:
        from tma2.long.timelate import scaling, settings_and_priors

        s, priors, cp, c2 = settings_and_priors()
        lengths = [float(x) for x in a.lengths.split(",")]
        head["scaling"] = scaling(e, lengths, a.start_s, s, priors, cp, c2)
    head["wall_s"] = time.time() - t0
    tag = a.tag or Path(a.config).stem
    stem = f"{a.part}-{a.index}"
    if tag != "long" or a.contact != 1:  # spec 023's names stay as they were
        stem = f"{tag}-c{a.contact}-{stem}"
    if a.part == "scaling":
        stem += "-" + a.lengths.replace(",", "_")
    elif a.part == "jointpair":
        stem += f"-p{a.pair}"
    elif a.shard != "0/1":
        stem += "-" + a.shard.replace("/", "of")
    if arrays:
        np.savez_compressed(out / f"{stem}.npz", **arrays)
    (out / f"{stem}.json").write_text(json.dumps(head, indent=1, default=float) + "\n")
    print(json.dumps({"part": a.part, "index": a.index, "wall_s": round(head["wall_s"], 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
