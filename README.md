# gitma2

A second attempt at target motion analysis (TMA) from bearings alone with machine learning,
starting from what [debrief/Gitma](https://github.com/debrief/Gitma) established.

gitma showed that a plain recurrent regressor learns usable range, course and speed from
simulated bearings, is more robust than least squares in near-unobservable geometry, and beats a
tuned IMM tracker after a target turn, but that it stays about 3 × the Cramér–Rao bound on straight
legs and gives back its post-turn gains when the target holds course. gitma2 keeps the network for
judgement (when the target manoeuvred, how much to trust each bearing, where to start) and lets a
differentiable piecewise-constant-velocity batch solve do the numerics.

- **Requirements**: [`docs/SRD.md`](docs/SRD.md), [Annex A: steady-leg detector](docs/SRD-annex-A.md)
- **Principles**: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- **Research**: [`docs/research/`](docs/research/) (retrospective, literature, infrastructure,
  proposal, oracle-segmentation ceiling)
- **Specs**: [`specs/`](specs/) (Spec Kit); agents: [`AGENTS.md`](AGENTS.md)

## Status

| Step | State |
| --- | --- |
| Spec 001, types and generator | implemented: the Python generator reproduces gitma's files byte for byte (3 fixtures, 220 scenarios, zero one-ulp residuals) |
| Spec 002, references, physics layer, P0 | implemented: gitma's references and evaluation reproduced; physics layer equals batch least squares and reproduces the oracle ceiling; exported graph agrees across Python, browser and Java runtimes within the 1e-5 gate in double (observed about 1e-11); **P0 passed** (agent panel round 3, `experiments/20261101-p0-r4/`) |

## Quick start

Requires Python 3.12 (via [uv](https://docs.astral.sh/uv/)); Node 22 for the site only.

```bash
uv sync
uv run pytest -q
uv run tma2-generate --seed 777 --count 1000 --out data/demo \
  --ranges tests/fixtures/gitma/phase4-seed777/ranges.json \
  --heldout-ranges tests/fixtures/gitma/phase4-seed777/heldout-ranges.json
```

Types are generated from `schema/tma.yaml` (`uv run python scripts/gen_types.py`; CI fails if
stale). Walkthrough: [`specs/001-types-generator/quickstart.md`](specs/001-types-generator/quickstart.md).

All data is simulated; nothing above OFFICIAL belongs in this repository.
