# CLI contracts: spec 010

```
tma2-generate --seed S --count N --out DIR --mismatch configs/gateh/conditions.json#<id>
```
Writes the split and `<split>.mismatch.npz`. Without `--mismatch`, or with `#off`, the data bytes
equal generator 0.6.0's and no side file is written.

```
tma2-hpredict ceiling --in SPLIT --mismatch-truth FILE --kind attainable|realisation --out PRED
tma2-hpredict robust  --in SPLIT --plan configs/gateh/gh-a.json [--only huber|sigma|whiten]
                      --segmentation truth|FILE --out PRED
```
`ceiling` refuses to run without the truth file and checks its digest against the split.
`robust` refuses a `--mismatch-truth` argument (it has none) and never opens the side file.

```
tma2-gh --truth SPLIT --plan configs/gateh/gh-a.json --decision DIR --split tuning|validation|test
        --condition <id> --predictions PRED... --out DIR
```
As `tma2-gs`, plus `headroom.json`. Exit 3: a soundness check failed. Refuses `--split test` on
fewer than every scenario of the primary condition, or without the decision record.
