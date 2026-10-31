# Contract: in-memory batch interface

```python
from tma2.features.batch import Batch, generate_batch, rows_for

R = rows_for(ranges)  # floor(window_s.max / dt_s)
batch: Batch = generate_batch(
    seed=777,
    batch_index=3,
    batch_size=256,
    ranges=ranges,
    start=0,
    end=80_000,  # index range this stream covers (a split)
    noise_free=False,
    workers=None,  # None: numba's thread count
)
```

- **Indices**: `start + batch_index · batch_size … min(start + (batch_index + 1) · batch_size, end)`;
  the last batch may be short; `batch_index` beyond the range raises `IndexError`.
- **Arrays**: as `data-model.md` "Batch"; all `numpy.ndarray`, C-contiguous, owned by the batch.
- **Equality guarantees** (tested):
  - `generate_batch(... batch_size=B)[k]` equals the rows of `generate_scenario(seed, index)` for
    the same index, and equals the rows decoded from a file written by `tma2-generate` for the
    same seed and ranges, field for field.
  - The result does not depend on `batch_size`, `workers`, or the order in which batches are
    requested.
- **Performance**: 256 scenarios of ≤ 360 rows in under 0.5 s on 4 cores after warm-up
  (first call compiles; `tma2.sim.warm_up()` triggers it explicitly).
- **Pure**: no module-level state besides numba's compiled cache; calling from several processes
  is safe.
- **Scenario objects**: `generate_scenario(seed, index, ranges, noise_free=False) -> GeneratedScenario`
  (`scenario: Scenario` Pydantic model, `redraws: int`) is the single-scenario, metadata-carrying
  path used by the file writer and by tests.
