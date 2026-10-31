# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**gitma2: TMA via ML, second attempt.** Can a learned component, trained end to end with explicit
bearing geometry, match batch least squares wherever the constant-velocity model holds and beat a
tuned IMM wherever it does not? It starts from [debrief/Gitma](https://github.com/debrief/Gitma).

- Principles: `.specify/memory/constitution.md` (v1.0.0). Plans MUST pass its checks.
- Research and the owner's decisions: `docs/research/` (notes 01–05; decisions in 04 §6).
- Requirements: `docs/SRD.md` (to be written; until then the proposal in `docs/research/04-proposal.md` stands in).

## Spec-driven workflow (GitHub Spec Kit)

Spec Kit is installed (`.specify/`, skills in `.claude/skills/speckit-*`). Feature work follows
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`. Specs live under
`specs/<NNN-feature>/` and cite the SRD section(s) they implement.

## Stack (owner decisions, 2026-10-31)

Python throughout: PyTorch models, NumPy/numba generator and reference estimators, LinkML →
Pydantic types, `uv`, `pytest`, `ruff`, `mypy --strict`. Training on free 4-core GitHub runners.
Models export to ONNX (standard ops, fixed window, dynamic batch) with a cross-runtime conformance
test. Sites and process as gitma: Docusaurus site, pre-registered decision records, fresh test
seeds, agent review panel for every gate.

## Hard rules

See the constitution. In short: types once in LinkML; seeded randomness only; the reported
estimate comes from a declared physics layer; no result without naive, batch least squares, the
tuned IMM/EKF and the oracle ceiling on the same rows; efficiency (error / CRB) per slice; three
seeds per carried configuration; nothing above OFFICIAL, mock data only.
