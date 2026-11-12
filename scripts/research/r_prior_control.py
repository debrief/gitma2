"""Spec 012 panel control: C″ combined with a range prior, nothing trained.

    uv run python scripts/research/r_prior_control.py --dir <scored man2 dir> [--fit | --apply rule.json] --out out.json

``<dir>`` holds a scoring run's ``errors.npz`` and ``c2``, ``reg-own``, ``reg-s1`` prediction
files (from a ``results/rscore-*-man2-*`` branch). Per scored row the control combines C″'s
ln range (sd = T × its stated ``log_range_sd``, floored) with a prior on ln range by precision
weighting. Two priors:

* ``static``: one mean and sd of ln range for every row (fitted with ``--fit``).
* ``own``: the ownship-only regressor's ln range and its stated sd (what range is usual given
  the ownship's track alone; trained in spec 012, nothing new).

``--fit`` chooses T (and the static prior's two numbers) on the given run to minimise the
median relative range error on rows C″ answers, and writes the rule. ``--apply`` applies a
rule unchanged and reports medians and engagement-clustered bootstrap differences.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

T_GRID = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0)
SD_FLOOR = 0.02
DRAWS = 2000
ROW_S = 10  # the scorer's rows are 10 s apart; prediction rows carry timestamp_s


def rows_of(path: Path, sd_key: str) -> dict[tuple[int, int], tuple[float, float]]:
    out: dict[tuple[int, int], tuple[float, float]] = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("record") != "prediction":
                continue
            for r in rec["rows"]:
                rng, sd = r.get("range_m"), r.get(sd_key)
                if rng is None or sd is None or not r.get("converged", True):
                    continue
                if not (np.isfinite(rng) and np.isfinite(sd) and rng > 0 and sd > 0):
                    continue
                out[(int(rec["ordinal"]), int(r["timestamp_s"]))] = (float(rng), float(sd))
    return out


def load(d: Path) -> dict[str, np.ndarray]:
    e = np.load(d / "errors.npz")
    c2 = rows_of(d / "c2.ndjson.gz", "log_range_sd")
    own = rows_of(d / "reg-own.ndjson.gz", "sd_log_range")
    n = e["ordinal"].shape[0]
    a = {k: np.full(n, np.nan) for k in ("c_ln", "c_sd", "o_ln", "o_sd")}
    for i in range(n):
        key = (int(e["ordinal"][i]), int(e["k"][i]) * ROW_S)
        if key in c2:
            a["c_ln"][i], a["c_sd"][i] = np.log(c2[key][0]), c2[key][1]
        if key in own:
            a["o_ln"][i], a["o_sd"][i] = np.log(own[key][0]), own[key][1]
    a["true_ln"] = np.log(e["true_range_m"])
    a["ordinal"] = e["ordinal"]
    a["err_c2"] = e["err_c2"][:, 0]
    a["err_reg"] = e["err_reg-s1"][:, 0]
    a["err_own"] = e["err_reg-own"][:, 0]
    return a


def combine(a: dict[str, np.ndarray], t: float, m: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Relative range error of the precision-weighted combination (NaN where C″ is silent)."""
    wc = 1.0 / np.maximum(t * a["c_sd"], SD_FLOOR) ** 2
    wp = 1.0 / s**2
    ln = (wc * a["c_ln"] + wp * m) / (wc + wp)
    out: np.ndarray = np.abs(np.exp(ln - a["true_ln"]) - 1.0)
    return out


def boot(x: np.ndarray, y: np.ndarray, ordinal: np.ndarray, seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    ids = np.unique(ordinal)
    groups = [np.flatnonzero(ordinal == i) for i in ids]
    d = []
    for _ in range(DRAWS):
        pick = np.concatenate([groups[j] for j in rng.integers(0, len(ids), len(ids))])
        d.append(float(np.median(x[pick]) - np.median(y[pick])))
    lo, hi = np.quantile(d, [0.025, 0.975])
    return [float(np.median(x) - np.median(y)), float(lo), float(hi)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--apply")
    ap.add_argument("--out", required=True)
    g = ap.parse_args(argv)
    a = load(Path(g.dir))
    ok = np.isfinite(a["c_ln"]) & np.isfinite(a["o_ln"]) & np.isfinite(a["err_c2"])
    ok &= np.isfinite(a["err_reg"])
    mine = np.abs(np.exp(a["c_ln"] - a["true_ln"]) - 1.0)
    check = float(np.nanmax(np.abs(mine[ok] - a["err_c2"][ok])))
    if g.fit:
        mu, sd = float(np.mean(a["true_ln"][ok])), float(np.std(a["true_ln"][ok]))
        rule = {"static": {"mean_ln_range": mu, "sd_ln_range": sd}, "sd_floor": SD_FLOOR}
        grid = {}
        for name in ("static", "own"):
            m = np.full(ok.shape, mu) if name == "static" else a["o_ln"]
            s = np.full(ok.shape, sd) if name == "static" else a["o_sd"]
            med = {t: float(np.median(combine(a, t, m, s)[ok])) for t in T_GRID}
            grid[name] = med
            rule[f"t_{name}"] = min(med, key=lambda t: med[t])
        rule["grid"] = {k: {str(t): v for t, v in m.items()} for k, m in grid.items()}
    else:
        loaded = json.loads(Path(g.apply).read_text())
        rule = loaded.get("rule", loaded)  # a --fit output wraps the rule
    res = {"rows": int(ok.sum()), "engagements": int(np.unique(a["ordinal"][ok]).size)}
    res["c2_row_check_max_abs"] = check
    res["median"] = {
        "c2": float(np.median(a["err_c2"][ok])),
        "regressor_s1": float(np.median(a["err_reg"][ok])),
        "ownship_only": float(np.median(a["err_own"][ok])),
    }
    for name in ("static", "own"):
        st = rule["static"]
        m = np.full(ok.shape, st["mean_ln_range"]) if name == "static" else a["o_ln"]
        s = np.full(ok.shape, st["sd_ln_range"]) if name == "static" else a["o_sd"]
        err = combine(a, float(rule[f"t_{name}"]), m, s)
        res["median"][f"c2_plus_{name}_prior"] = float(np.median(err[ok]))
        o = a["ordinal"][ok]
        res[f"{name}_minus_c2"] = boot(err[ok], a["err_c2"][ok], o)
        res[f"regressor_minus_{name}"] = boot(a["err_reg"][ok], err[ok], o)
        q = np.quantile(a["true_ln"][ok], [0.25, 0.5, 0.75])
        band = np.digitize(a["true_ln"][ok], q)
        res[f"{name}_by_range_quartile"] = [
            {
                "c2": float(np.median(a["err_c2"][ok][band == b])),
                "control": float(np.median(err[ok][band == b])),
                "regressor": float(np.median(a["err_reg"][ok][band == b])),
            }
            for b in range(4)
        ]
    res["regressor_minus_c2"] = boot(a["err_reg"][ok], a["err_c2"][ok], a["ordinal"][ok])
    Path(g.out).write_text(json.dumps({"rule": rule, "result": res}, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
