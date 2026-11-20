# Plan: spec 030

## Code

New code only. `ctl`, `ctl-carry`, `ctl-prior`, the simulator, and the bound files of specs 028
and 029 are unchanged.

- **`tma2-long jointheld`** (`cli/long.py`). For each 1-hour window j ≥ 1 with no ownship turn, it
  runs `timelate.run_windows` (`ctl`, C″ and the true-history fit `history-best`) on the union of
  windows j − 1 and j. It keeps the rows of window j and writes `<stem>-c1-jointheld-<i>`.
- **`long/study30.py`** (`tma2-long study30`). This is the scorer:
  - (a) is the 1-hour `carry2`;
  - (b) is the 2-hour `carry2`, run with `--tag <stem>-2h` and stitched with `timelate.stitch`;
  - (c) is `jointheld`.

  On each held 1-hour window it takes each system's median error over that window's rows, then
  computes D1 and D2, the readings beside, and soundness S1–S3.
- **`long.yml`** passes `tag`, which also names the artifacts.
- **Configs and run files:**
  - configs `configs/long/cmp-{val,test}.json` (seeds 365 and 366);
  - run files `configs/long/runs/cmp-{tuning,val,test}.json`;
  - tuning runs (b) and (c) only, on spent seed 364's engagements 0–5 and 30–35, using
    `hold-test.json`, and reuses (a) from spec 029's test record.

## Order

1. Tuning on spent seed 364, giving costs and forecasts.
2. Decision record: digests (`scripts/research/cmp_digests.py`) and forecasts.
3. Validation on seed 365: soundness S1–S3.
4. Test on seed 366, scored once.
5. Panel, then write-up and slides, AGENTS.md and the PR.

## Cost

About 1.6 runner-hours per engagement across the three parts, so about 100 h for the test and
33 h for validation.
