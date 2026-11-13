# CLI contract: spec 014

`tma2-tlsolve` (additions; defaults reproduce Gate T):

- `--prior-version 1|2`, `--prior flat|annex-b|broad`
- `--systems a,b,...` (adds `search2`, `search-flat`, `c2-refit`, `ekf-rts`)
- `--thin drop:N | fixed:N | adaptive:TOL[:robust]`
- `--classify` (fit the true history's structure without true states; write class inputs)

`tma2-tlscore` (additions):

- `--study <criteria json>`: gain shares, classes, composites, headroom, false-manoeuvre
  rates, the recommendation; exit 0 always (a study, not a gate); exit 3 only if the soundness
  stop fails on a run marked validation.
- `--errors`: write `errors.npz`.
- `--tolerances 60,120,240`.

Workflow `timelate.yml`: a run file may name `condition` (spec 010 id) and a ranges file per
split; generation applies the mismatch overlay from its own stream.

Run files: `configs/timelate/runs/tl-c-{smoke,tune,val,test}.json`; plan
`configs/timelate/tl-c.json` (bound by digest in the decision record, never edited after).
