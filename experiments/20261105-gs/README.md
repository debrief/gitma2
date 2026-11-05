# Gate S on seed 315 (spec 005 T038)

Machine verdict: **S1 pass, S2 pass, S3 pass, S4 inconclusive; reference C** (exit 3). The
decision record counts inconclusive as not passed for the follow-on, so C carries into Gate 2 and
learning is recorded as not shown (FR-072). The panel's verdict is in `review.md`.

- Data: seed 315 test split (`data/gs-test/test.f32pack`, digest 1a8d55fe…), generated at a38f61b
  after the decision record; σ = 1° ordinals 0–5058 (5,059 scenarios, 19,921 G5 rows, 14,670
  settled).
- Inputs: C and L segmentations (CI, clean tree at 90dcbc4; C's segmenter digest equals the
  decision's parameter digest, L's equals the carried seed 3's expected digest), GLR + confirm
  from 64 confirm shards (`glr-q0.2-t13.8`), the frozen IMM and EKF (`experiments/20261104-man2-refs/`).
- Decision `experiments/20261104-gs-decision/decision.json` (sha256 668712…), plan
  `configs/segment/gs-plan.json` (921c2b…), amendments `carried.json` and
  `seed315-digests.json` listed by digest in `manifest.json`.

| Check | Statistic | Result |
| --- | --- | --- |
| S1 | O's contamination P90 on ownship legs, limit 0.02 | 0.000 [0.000, 0.000] pass |
| S2 | C − GLR + confirm, gap recovered (range) | +0.755 [+0.711, +0.798] pass |
| S3 | L − C contamination median / P90 (limit +0.01); false split (limit +0.05) | 0.000 [−0.008, 0.000] / −0.0005 [−0.0056, +0.0034]; 0 [0, 0] pass |
| S4 | L − C, gap recovered (range) | +0.0014 [−0.0030, +0.0051] inconclusive |

Full tables: `report.md`, `metrics.json`. `errors.npz` (per-row errors) is gitignored.

## Two runs, one record

The first run (at aa8bd6b, clean tree at launch) recorded `git_dirty: true`: `tma2-gs` read
`git status` after writing `metrics.json` and `report.md` into this untracked folder. Fixed in
e648f8b (status read before any output), and the gate re-run from that clean commit with the same
inputs. Its `metrics.json`, `report.md` and `verdict.json` are byte-identical to the first
run's; the manifests differ only in `git_commit` and `git_dirty`. The first run's manifest
(sha256 b2824c33bb529f45e7168d51d18fe913315e1e4b84a61679ca1d731928067dab) is not committed. This record is the re-run.
