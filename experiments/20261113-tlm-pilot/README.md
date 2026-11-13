# Spec 016: the whole-period model's pilot on a T4 (2026-11-13)

Workflow run 43496013487 (`gputrain/tlm-pilot`, commit ab0509e, plan
`configs/regress/tlm-pilot.json`), results branch `results/gputrain-tlm-pilot-43496013487`.
`run.json` is its record. A throughput and loss-curve reading; the weights are not carried.

- **Throughput**: 6,000 updates of 256 periods (1.54 million periods) in 3,388 s of
  training: 453 periods a second (435 over the whole record). Generation on the
  container's CPU is the limit, as forecast (spec 012's stream gave 635 a second).
- **It trains**, with mixed precision and the padding mask: on the monitor slice of the
  stream (mixed conditions) the median absolute error of ln range fell from 0.24 at 500
  updates to 0.095 at 6,000; the manoeuvre term from 0.30 to 0.21.
- **The container was replaced once** (at update 1,819) and the run resumed from its
  checkpoint on the volume and completed. The record's `gpu_seconds` (2,468) counts only
  the second container: the first, about 930 s of training and its start-up, is billed and
  not recorded. **The ledger under-counts a run that is restarted.** The true cost of this
  pilot is about $0.70, against $0.47 recorded.
- **Two earlier launches failed** at container start-up (the launcher's functions, built
  in a loop and serialised by spec 012's addendum 1, had never been run and could not be
  imported in the container). They did no training; what Modal billed for the failed
  starts is not visible from here. The launcher is back to the form spec 012's runs used,
  and the workflow now gives up at the segment's limit plus 25 minutes.

## What it sets

Three seeds within the ledger's cap ($45 of the owner's $50; $26.35 recorded before the
training runs): two segments of 15,600 s each, at most 9 h with allowances, $6.12 a seed,
$18.36 for three. At 453 periods a second with a tenth held back for restarts and
monitoring: 49,000 updates, 12.5 million periods a seed (spec 012's regressor saw 21.8
million scenarios).
