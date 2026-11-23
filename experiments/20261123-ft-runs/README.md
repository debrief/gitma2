# Spec 037: the three fine-tunes did not finish (2026-11-23)

Runs 45108906382 (ft-s1), 45109019065 (ft-s2) and 45109133362 (ft-s3) started at 03:57 to
04:00 UTC from commit d386257, plans as bound by `../20261123-rmis-decision/`. All three ended
at **05:52:18 to 05:52:20 UTC** in the client with

    ConflictError: workspace ac-3hmiUEgPzBufZR3WIHKjr2 is disabled

No run record or checkpoint reached GitHub: the workflow publishes only what a finished call
returns. Nothing was relaunched.

## What is known

- Each container trained for about 1 h 53 min of a planned 3 h: by the pilot's throughput
  (621 scenarios a second) roughly **16,000 of 26,000 updates**, with the learning rate at about
  a third of its peak (the cosine schedule had not come down).
- Training saves a checkpoint to the Modal volume `gitma2-regress` every 15 minutes
  (`/vol/ft-sK-<run id>/checkpoint.safetensors`, `state.pt`, `run.json`), so a checkpoint no
  more than 15 minutes old should be there for each seed. **Not verified**: the workspace
  refuses every call.
- Money: about 3 × 1.92 h × $0.68 ≈ **$3.9**, which takes the total to about **$44.8**. The
  ledger still reads $40.89, because it counts published run records only.

## The cause, as far as it can be read from here

The workspace was disabled at about $45 of spend. `gputrain.yml`'s guard had been $45 with the
comment "kept under what Modal's limits enforce"; on 2026-11-22 the owner raised it to $49 on
this agent's recommendation, which read the $5 as a margin for charges the ledger does not see.
It was the distance to a limit set on Modal's side. The recommendation was wrong, and the
comment that said so was in the file. The limit itself (a workspace budget, or the free credit
plus a spending cap) can only be read in Modal's dashboard.

## What it leaves

- The decision record's three fine-tuned seeds do not exist. Validation seed 370 and test seed
  371 are untouched and not generated.
- The pilot checkpoint (seed 1, 4,000 updates; `results/gputrain-ft-pilot-45101050454`) exists.
  A development reading with it on spent seed 321 is run on CPU while the owner decides
  (`configs/headroom/rm-pilot-321.json`): it is one seed of a shorter schedule and is not the
  registered model.
- Whether to re-enable the workspace, and for how much, is the owner's.

## Update, 2026-11-23 22:25 UTC: the saved state is secured; the resume was refused

The owner chose to resume. A read-only check of the volume (`modal-check/volume`, no container)
found each run's saved state, and `modal-fetch/ft` copied each checkpoint and run record to
`results/ftpartial-<run>` with the checkpoint's digest checked against its record
(`partial/<run>/run.json` here):

| Run | Updates saved (of 26,000) | Last monitor at | Monitor under the mix, start → then | Clean monitor, start → then | Checkpoint |
|---|---|---|---|---|---|
| ft-s1-45108906382 | 14,075 | 14,000 | 0.114 → 0.101 | 0.085 → 0.086 | `6cbaeab4ff92…` |
| ft-s2-45109019065 | 16,476 | 16,000 | 0.118 → 0.100 | 0.086 → 0.090 | `ec513fd0bc57…` |
| ft-s3-45109133362 | 12,389 | 12,000 | 0.120 → 0.106 | 0.087 → 0.094 | `8ac019f34322…` |

(Median absolute error of ln range on the runs' own monitors: development figures.)

Re-running the three failed jobs at 22:02 UTC (same run ids, so the same folders on the volume
and a resume, not a restart) was refused before any container started: "Workspace … has
exceeded its spend limit". Nothing was charged. The workspace can be read but cannot spend
until its limit is raised in Modal's dashboard, which is the owner's. Finishing needs about
35,000 updates in all, about 4 T4-hours, about $2.90.
