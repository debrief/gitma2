# Model artefact

A directory per carried model:

- `model.onnx`: one graph; inputs bearing, valid, own (x, y), t [B, R] in double, sigma [B],
  k [B] int64, theta_grid [B, 4]; outputs state [B, 4], cov [B, 4, 4], plausible [B],
  cov_ok [B]; the physics iteration is an ONNX `Loop` over K = 100; dynamic batch, fixed R.
- `model.safetensors`: the weights.
- `manifest.json`: a `PhysicsModelManifest`.
- `golden/`: inputs and PyTorch outputs for the conformance legs (spec 002's harness).

Conformance: the Python, browser (WASM) and Java legs agree with PyTorch to 1e-5 in double, and
each runtime loads the graph in under a minute.
