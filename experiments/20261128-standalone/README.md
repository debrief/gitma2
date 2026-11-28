# Stand-alone steady-leg investigation: the scripts (a record; not repository code)

The nine scripts behind `docs/research/15-steady-leg-theory-note.md`, as the owner supplied them
on 28 November 2026 from an investigation run outside this repository. They are kept unmodified
as a record, with a `.txt` suffix so that the repository's linters and importers leave them
alone; `SHA256SUMS` gives the digests of the original `.py` files.

- They use their own simulator (`sim.py`), a re-implementation of the brief's section 4, not
  generator 0.6.0; their own solve, not the physics layer; and they have not been run here.
- Repository code must not import them. Spec 040 ports what it needs and re-measures each
  figure against the generator, segmenter C″ and the physics layer.
- They need NumPy and SciPy and write JSON results beside themselves or to a fixed path from
  the original session.

| File | What it is |
|---|---|
| `sim.py` | simulator and joined-leg model |
| `experiments.py` | detectability and delay (`detect`), null distribution of the scan (`null`) |
| `e1.py` | cross-ratio check, Jacobian rank, knot-placement profiles |
| `detector.py` | prototype whole-window split test with editing and noise correction |
| `win.py` | effect of window length on the null |
| `solve.py` | structure-given solves (knot, arc, bounds, detectable-only, late) |
| `refine.py` | re-estimating transition times inside the solve |
| `v1.py`, `v2.py` | truth-free causal detectors, scored end to end |
