# Addendum 1 to the spec 012 decision record: a look at the hardware's limits

Written 2026-11-11 after the three seeds were trained and scored on **validation** (held
course: range 1.15–1.19 × the bound, course 1.8, speed 1.4; worst in the best-observed quarter
of rows) and **before the test seed is scored**. The registered experiment and its readings are
unchanged; nothing here alters the plans bound in `decision.json`.

Owner, 2026-11-11: spending within the $50 budget needs no further approval, and the spike
should also show what the hardware can do. $25.81 is spent (Modal's usage page; the ledger says
$25.88). The ledger now counts dollars by GPU type and caps at $45, what Modal's limits enforce.

## Step 1: throughput probes (about $2)

Ten minutes each, nothing scored, plans `configs/regress/probe-*.json`:

- Model A (the carried 8 layers × 256, 6.4 million parameters) on an L4 and an A10. The T4
  figure is known: 581 scenarios a second with the held-course share.
- Model B (12 layers × 512, feed-forward 2,048, about 38 million parameters) on a T4, an L4, an
  A10, an L40S and an A100 (40 GB).

Reported: scenarios a second and, from the listed prices, scenarios per dollar.

## Step 2: one run of model B (at most $14), registered now

- **Question**: does more capacity close the gap to the bound on the well-observed rows?
- **Run**: model B, training seed 1, the same stream, loss and schedule shape as the carried
  model, on the GPU type with the most scenarios per dollar in step 1, sized from 90% of its
  measured rate to fit $14 (the plan and its digest are added in addendum 2 before launch).
- **Reading**: the same held-course and after-manoeuvres readings, on validation and then once
  on test seed 328, beside the carried seeds. One training seed, so it is **exploratory**: it
  can show a large effect and cannot establish a small one.
- **Forecast**: range efficiency moves little (it is already near 1.2); course and speed
  improve by less than the gap between the carried model and the bound halves.
- If model B is slower than 100 scenarios a second on every GPU type within reach, step 2 is
  not run and the write-up says what the hardware allows.

## Paused by the owner, 2026-11-11 (20:19 UTC)

The owner asked for GPU training to pause while a time-late strategy is agreed. Step 1 stopped
after one probe was launched (model B on a T4, run 43093184330): it had not published after 25
minutes against a 10-minute limit and was cancelled, so it gives no figure, and why it ran long
is not established. The other six probes were never launched. Step 2 (the larger model) is not
run. Nothing in this addendum produced a result.
