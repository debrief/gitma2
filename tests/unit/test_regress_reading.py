"""Spec 012 FR-021/FR-022: the readings on synthetic errors with known answers."""

from __future__ import annotations

import numpy as np

from tma2.regress.reading import after_manoeuvres, efficiency, held_course, paired_difference


def _rows(n_scen: int = 300, per: int = 4, seed: int = 0):  # type: ignore[no-untyped-def]
    rng = np.random.default_rng(seed)
    ordinal = np.repeat(np.arange(n_scen), per)
    sd = np.abs(rng.normal(1.0, 0.3, (ordinal.size, 3))) + 0.2
    z = rng.standard_normal((ordinal.size, 3))
    return rng, ordinal, sd, z


def test_efficiency_of_an_efficient_estimator_is_one() -> None:
    _, _, sd, z = _rows()
    assert abs(efficiency((z * sd)[:, 0], sd[:, 0]) - 1.0) < 0.1


def test_held_course_readings() -> None:
    _, ordinal, sd, z = _rows()
    held = np.ones(ordinal.size, dtype=bool)
    assert held_course(z * sd, sd, ordinal, held, resamples=300)["reading"] == "reaches"
    # a flat floor: error independent of geometry, three times the typical bound
    flat = 3.0 * z * np.median(sd, axis=0)
    r = held_course(flat, sd, ordinal, held, resamples=300)
    assert r["reading"] == "floor" and r["range"]["lo"] > 2.0
    by = r["range"]["by_geometry_best_to_worst"]
    assert by[0] > by[3]  # worst relative to the bound where the bound is smallest
    # 1.6 × the bound everywhere: neither
    assert held_course(1.6 * z * sd, sd, ordinal, held, resamples=300)["reading"] == "partial"
    # three times the bound but tracking geometry: above the floor line, yet not flat
    r3 = held_course(3.0 * z * sd, sd, ordinal, held, resamples=300)
    assert r3["reading"] in ("partial", "floor") and r3["range"]["lo"] > 2.0
    assert held_course(z * sd, sd, ordinal, ~held)["reading"] == "no rows"


def test_paired_difference_and_manoeuvring() -> None:
    rng, ordinal, _, _ = _rows()
    n = ordinal.size
    base = np.abs(rng.normal(0.1, 0.03, (n, 3)))
    errs = {"reg": base * 0.8, "c2": base, "imm": base * 1.5}
    man = np.ones(n, dtype=bool)
    d = paired_difference(errs["reg"][:, 0], errs["c2"][:, 0], ordinal, man, resamples=300)
    assert d["difference"] < 0 and d["hi"] < 0
    rng_m = rng.uniform(5e3, 4e4, n)
    out = after_manoeuvres(errs, "reg", ["c2", "imm"], ordinal, man, rng_m, resamples=200)
    assert out["imm"]["range"]["all_rows"]["hi"] < 0
    assert out["c2"]["range_m"]["difference"] < 0
    assert len(out["c2"]["range_by_true_range_quartile"]) == 4
    assert sum(q["rows"] for q in out["c2"]["range_by_true_range_quartile"]) == n
