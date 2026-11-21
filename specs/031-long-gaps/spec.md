# Spec 031: several periods of one target across long gaps (stress split)

Owner 2026-11-20: option 3 of spec 030's panel order, "a stress split with longer gaps and more
periods, where a carried state is the realistic option". A study, not a gate; nothing trained;
CPU only. Cites SRD §7 (time-late) and Annex B (target and ownship manoeuvres).

## Where we are

- Spec 025: the joint solve (`ctl` over the span, the gaps' bearings marked missing) is the
  standing time-late system for two or three periods of one target, within gaps of 5–30 min.
- Spec 027: a carried *start* does not substitute for joining.
- Spec 030: a carried *prior* (k4) helps against `ctl` alone where a period cannot answer
  alone; against the joint solve it is on the line (1.40 [0.98, 2.01]).
- A per-period consistency flag was judged not worth registering
  (`experiments/20261120-tl11-flag-look/`).

All of that is within gaps of 5–30 minutes. Over long gaps the joint solve must bridge an hour
or more of unobserved manoeuvres (Annex B: about two an hour). Its single history over a span of
several hours meets `ctl`'s cap of ten manoeuvres, and its cost grows with the span. That is
where carrying a state, rather than joining, could become the better choice.

## What this spec does

- **Data:** the long simulator (specs 023–026): 6-hour engagements, Annex B targets, an
  ownship turning at each 20–40 min leg, keeping the target at 3–25 km. No realism layer: one
  contact, steering on the true target, no sensor gaps.
- **Layout** (spec 025's, own stream): 2 to 4 periods of 15–30 min with gaps of **30–90 min**.
- **Systems:** spec 030's `run10`, unchanged:
  - `ctl` alone;
  - the joint solve;
  - spec 027's carried start;
  - the uninflated carried prior;
  - k4.
- **Readings** (periods after an engagement's first, spec 025's rows, engagement bootstrap):
  - alone ÷ joint, k4 ÷ joint and alone ÷ k4;
  - each by gap length and by whether the period has its own ownship turn;
  - each on own rows;
  - the joint solve's cost and how often it meets the manoeuvre cap;
  - the carried prior's coverage.

## Order

1. Development on the long simulator's spent seed 348 (`configs/long/gaps-dev.json`,
   `configs/timelate/tl-q-dev.json`), 40 engagements, to size the effects and the cost.
2. Then a proposal to the owner: register on fresh seeds (365 onward) with a rule fixed
   beforehand, or stop.

## Changes to shared code

- `Period.ownship_turns()` reads the long simulator's full list of ownship turns when its meta
  carries one. Generator 0.6.0 meta has no such list, so every earlier study is unchanged.
- `tma2-tlsolve` takes a split's `long` config: whole engagements from the long simulator, in
  place of a pack.

## Limits known before any result

- C″'s start, which `ctl` uses, reads the first ownship turn of the whole engagement only
  (`points.py`), as everywhere in the time-late track.
- `ctl` caps a history at ten manoeuvres. Over spans of 3–4 hours the joint solve may need more.
  That is measured, not changed.
- The long simulator's ownship steers on the true target: the geometry is kinder than a real
  ownship's.
- Seeds: 348 was spent by spec 023 in the long simulator. The next fresh seed is 365.
