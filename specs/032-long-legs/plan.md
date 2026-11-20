# Plan: spec 032

## Code

New code only. The systems, the simulator, and the bound files of specs 028, 029 and 031 are
unchanged.

- **`long/study32.py`** (`tma2-long study32`). The scorer reads two parts:
  - (a), `<stem>-c1-carry2-<i>`: `carry2` at 7200/1800 s;
  - (c), `<stem>-c1-jointheld-<i>`: `jointheld` at 7200/1800 s.

  On each held 2-hour window it takes median errors over the window's rows (`study27.load27` for
  (a); `study30._load_joint` for (c)). It then computes E1, E2, the harm reading, the readings
  beside, and soundness S1–S3.
- **`tma2-long jointheld`** always writes its `.npz`, even when it holds no windows (spec 031
  panel).
- **Configs and run files:**
  - configs `configs/long/legs-{tuning,val,test}.json` (seeds 366 spent, 367, 368);
  - run files `configs/long/runs/legs-{tuning,val,test}.json`, two jobs per engagement, each with
    window_s 7200 and overlap_s 1800.

## Order

1. Tuning on spent seed 366 (6 + 6 engagements), giving costs and forecasts.
2. Decision record `experiments/<date>-legs-decision/`: digests
   (`scripts/research/legs_digests.py`) and forecasts.
3. Validation on seed 367: soundness S1–S3.
4. Test on seed 368, scored once.
5. Panel, then write-up and slides, AGENTS.md and the PR.

## Cost

Spec 031's 2-hour `carry2` ran at about 0.09 runner-hours per engagement-hour. `jointheld` on
3.5-hour unions is the larger unknown and is measured on tuning.
