# gitma2

A second attempt at target motion analysis (TMA) from bearings alone with machine learning,
starting from what [debrief/Gitma](https://github.com/debrief/Gitma) established.

gitma showed that a plain recurrent regressor learns usable range, course and speed from
simulated bearings, is more robust than least squares in near-unobservable geometry, and beats a
tuned IMM tracker after a target turn, but that it stays about 3 × the Cramér–Rao bound on straight
legs and gives back its post-turn gains when the target holds course. gitma2 proposes to keep the
network for judgement (when the target manoeuvred, how much to trust each bearing, where to start)
and to let a differentiable piecewise-constant-velocity batch solve do the numerics.

## Research notes

| Note | Content |
| --- | --- |
| [01 Retrospective](docs/research/01-gitma-retrospective.md) | What gitma established, why it stalled, what to keep and change |
| [02 Literature](docs/research/02-literature.md) | Learned estimators for bearings-only TMA and manoeuvring targets, 2019–2026, with a ranked shortlist |
| [03 Infrastructure](docs/research/03-infrastructure.md) | GitHub Actions GPU options, Python stack, ONNX as the portable artefact, reproducibility |
| [04 Proposal](docs/research/04-proposal.md) | The "segment, weight, solve" design, gates, risks, plan and the decisions for the owner |
| [05 Oracle segmentation](docs/research/05-oracle-segmentation.md) | Measured ceiling for the design on gitma's phase-4 data: segmented batch least squares against the frozen IMM |

`scripts/research/oracle_segmented_ls.py` reproduces note 05 from gitma's own generator and
tracker outputs.

Nothing here is a product. All data is simulated; nothing above OFFICIAL belongs in this
repository.
