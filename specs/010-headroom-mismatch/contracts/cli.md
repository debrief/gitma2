# CLI contracts: spec 010

```
tma2-generate --seed S --count N --out DIR --mismatch configs/gateh/conditions.json#<id>
```
Writes the split and `<split>.mismatch.npz`. Without `--mismatch`, or with `#off`, the data bytes
equal generator 0.6.0's and no side file is written.

```
tma2-hpredict --in SPLIT --kind attainable|realisation --mismatch-truth FILE --start S --count N --out PRED
tma2-hpredict --in SPLIT --kind robust --plan configs/gateh/gh-a.json [--only huber|sigma|whiten]
              [--segmentation truth|c2] --start S --count N --out PRED
tma2-hpredict --in SPLIT --kind nominal [--segmentation truth|c2 --plan ...] --start S --count N --out PRED
```
A ceiling refuses to run on a mismatch split without the truth file and checks it against the
split; on a split without a mismatch it is the plain oracle and takes no truth file. `robust`
and `nominal` refuse `--mismatch-truth` and never open the side file. `c2` is the classical C″
hand-over (C at the nominal σ, zig veto, fixed fade).

```
tma2-gh --truth SPLIT --start S --count N --predictions PRED... [--mismatch-truth FILE]
        [--imm NAME --ekf NAME] [--split tuning|validation|test --decision DIR --plan PLAN] --out DIR
```
Writes `errors.npz` and `headroom.json` (R with intervals, closure, operational units). The
truth file is used for the Cramér–Rao bound only. Refuses a validation or test scoring without
the decision record binding the plan, a test scoring of the primary condition on fewer than
every scenario, and prediction files made from another split.
