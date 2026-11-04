# Quickstart: spec 006 validation scenarios

Contracts: [contracts/cli.md](contracts/cli.md).

## 1. Nothing old changes

```bash
uv run pytest -q tests/golden tests/conformance
uv run tma2-generate --seed 304 --count 10000 --out /tmp/regen304 --ranges tests/fixtures/gitma/phase4-seed777/ranges.json --heldout-ranges tests/fixtures/gitma/phase4-seed777/heldout-ranges.json --format f32pack
```

Expected: all golden and gitma-conformance tests pass; `/tmp/regen304/digests.json` matches the
committed digests of `data/gd-val` (seed 304).

## 2. The MAN2 model

```bash
uv run tma2-ranges --describe configs/man2-ranges.json --sample 10000 --seed 314
```

Expected: leg-length 5th/50th/95th percentiles about 10 / 25 / 40 min; 4–6% of complete legs at
or under 10 min; transition median 60–180 s; ≥ 60% of engagements with two or more changes;
wander kinds about 40 / 30 / 30%.

## 3. Wander stays in band and is separable

```bash
uv run pytest -q tests/unit/test_wander.py tests/unit/test_leg_plan.py tests/unit/test_both_kind.py tests/unit/test_zig_plan_man2.py
```

Expected: every wander row within 5° of the leg course; a scenario regenerated with wander
weights set to none differs only in the ownship track; the "both" kind's end state matches the
analytic turn-then-accelerate limits; the zig is planned from the simulated target position.

## 4. Data, gate, references

```bash
uv run tma2-generate --seed 314 --count 10000 --out data/man2-val --ranges configs/man2-ranges.json --heldout-ranges configs/man2-heldout.json --format f32pack
uv run tma2-generate --seed 316 --count 10000 --out data/man2-g0 --ranges configs/man2-noise-free.json --heldout-ranges configs/man2-heldout.json --format f32pack
uv run tma2-p0 --experiment experiments/<date>-g0-man2 --oracle-data data/man2-val
uv run tma2-tune --in data/man2-val/validation.f32pack --out experiments/<date>-man2-tune
OMP_NUM_THREADS=1 uv run python scripts/research/leg_spike.py stats --validation data/man2-val/validation.f32pack --work <work>
```

Expected: the gate passes by panel verdict (`review.md`); frozen IMM and EKF names recorded; the
GLR + confirm report on seed 314 written to `experiments/<date>-man2-refs/`.
