# CLI contracts: spec 038

```
tma2-hpredict --segmentation c2e --edit '{"wild": true, "effective_sd": true}' ...   # C″ on edited data
tma2-hpredict --segmentation c2r --robust-confirm '{"robust": false, "tau_factor": 2}' ...
tma2-rdecomp --errors <errors.npz> --truth <split> --protocol configs/gd/protocol.json \
  --condition <id> --split <in|shift|far> [--segments <c2 dump>] [--mismatch-truth <npz>] --out decomp.json
```

`tma2-rdecomp` exits non-zero if a named system is absent from `errors.npz`. It never writes a
reading for a system the protocol does not name.
