"""Spec 025: the panel's readings beside the registered rules (experiments/20261118-ls/).

    uv run python scripts/research/long_study_supplement.py > experiments/20261118-ls/supplement.json

None of these decides anything; they narrow what the rules' outputs may be taken to mean.

* E1 without each chain's first window (where ``ctl-carry`` is ``ctl`` by construction), and on
  the windows where the two differ only; the search CPU on windows that had a carried start.
* E3 with unanswered rows counted as failures (error = +inf), and with hours 2–6 as the base.
* E2 in 2-km sub-bands of the registered bands (geometric mean over sub-bands with at least 50
  rows on both contacts).
Intervals: the registered bootstrap over engagements (2,000 resamples, seed 25).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tma2.long.study import _boot, engagements, load_carry, load_imm

ROOT = Path(__file__).resolve().parents[2]
CFG = (ROOT / "configs/long/study-test.json").resolve()
RAW = ROOT / "experiments/20261118-ls/raw"


def gm(us: list[np.ndarray]) -> float:
    return float(np.exp(np.concatenate(us).mean())) if us else math.nan


def main() -> int:
    out: dict[str, object] = {}
    e1s = engagements(CFG, 1)
    e2s = engagements(CFG, 2)
    c1 = [load_carry(RAW, "study-test-c1", e) for e in e1s]
    c2 = [load_carry(RAW, "study-test-c2", e) for e in e2s]
    nf, df = [], []
    none_s = carry_s = 0.0
    for c in c1:
        assert c is not None
        r = [
            (j, w["ctl"] / w["carry"])
            for j, w in enumerate(c["per_window"])
            if w["ctl"] > 0 and w["carry"] > 0
        ]
        a = [math.log(x) for j, x in r if j > 0]
        b = [math.log(x) for _j, x in r if x != 1.0]
        if a:
            nf.append(np.array(a))
        if b:
            df.append(np.array(b))
        for j, w in enumerate(c["per_window"]):
            if j > 0:
                none_s += w["none_s"]
                carry_s += w["carry_s"]
    est, lo, hi = _boot(nf, gm)
    out["E1_without_first_windows"] = {
        "windows": int(sum(u.size for u in nf)),
        "gm": est,
        "interval": [lo, hi],
    }
    est, lo, hi = _boot(df, gm)
    out["E1_differing_windows_only"] = {
        "windows": int(sum(u.size for u in df)),
        "gm": est,
        "interval": [lo, hi],
    }
    out["search_cpu_h_on_carried_windows"] = {
        "from_nothing": none_s / 3600,
        "from_carry": carry_s / 3600,
        "saving": 1 - carry_s / none_s,
    }

    imm = [
        u for u in (load_imm(RAW, "study-test-c1", e) for e in e1s if e.meta["hours"] == 12.0) if u
    ]

    def e3(us: list[dict[str, np.ndarray]], early_from: float, fail: bool) -> float:
        if not us:
            return math.nan
        late = np.concatenate([u["error"][(u["hours"] >= 6) & (u["hours"] < 12)] for u in us])
        early = np.concatenate(
            [u["error"][(u["hours"] >= early_from) & (u["hours"] < 6)] for u in us]
        )
        if fail:
            late = np.where(np.isfinite(late), late, np.inf)
            early = np.where(np.isfinite(early), early, np.inf)
        else:
            late, early = late[np.isfinite(late)], early[np.isfinite(early)]
        return float(np.median(late) / np.median(early))

    for key, ef, fail in (
        ("E3_unanswered_as_failures", 0.0, True),
        ("E3_base_hours_2_6", 2.0, False),
    ):
        est, lo, hi = _boot(imm, lambda us, ef=ef, fail=fail: e3(us, ef, fail))
        out[key] = {"estimate": est, "interval": [lo, hi]}

    units = []
    for a, b in zip(c1, c2, strict=True):
        if a is None or b is None:
            continue
        ra = (
            np.hypot(a["truth"][:, 0] - a["truth"][:, 4], a["truth"][:, 1] - a["truth"][:, 5]) / 1e3
        )
        rb = (
            np.hypot(b["truth"][:, 0] - b["truth"][:, 4], b["truth"][:, 1] - b["truth"][:, 5]) / 1e3
        )
        units.append((ra, a["errors"]["ctl-d1-q0.01"], rb, b["errors"]["ctl-d1-q0.01"]))
    edges = np.arange(2.0, 40.01, 2.0)

    def e2(us: list[tuple[np.ndarray, ...]]) -> float:
        logs = []
        for lo_km, hi_km in zip(edges[:-1], edges[1:], strict=True):
            ea = np.concatenate([u[1][(u[0] >= lo_km) & (u[0] < hi_km)] for u in us])
            eb = np.concatenate([u[3][(u[2] >= lo_km) & (u[2] < hi_km)] for u in us])
            ea, eb = ea[np.isfinite(ea)], eb[np.isfinite(eb)]
            if ea.size >= 50 and eb.size >= 50:
                logs.append(math.log(np.median(eb) / np.median(ea)))
        return math.exp(float(np.mean(logs))) if logs else math.nan

    est, lo, hi = _boot(units, e2)
    out["E2_2km_sub_bands"] = {"estimate": est, "interval": [lo, hi]}
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
