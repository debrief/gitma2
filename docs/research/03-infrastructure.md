# Infrastructure: training compute, stack and portable model artefacts

Research made on 31 October 2026 for gitma2. The owner's constraints: keep training on GitHub
CI if practical; the training stack may be pure Python (or C++); the trained model's structure and
weights must be transferable across diverse technologies (browser JS, Python, Java, C++).

## 1. GitHub Actions compute

| Runner | Spec | Price | Notes |
| --- | --- | --- | --- |
| `ubuntu-latest`, public repo | 4 vCPU, 16 GB, 14 GB SSD | free | 6 h job limit; what gitma used |
| Larger CPU runners | 8 / 16 / 32 / 64 core | $0.022 / 0.042 / 0.082 / 0.162 per min | never free, org/Team plan only ([pricing](https://docs.github.com/en/enterprise-cloud@latest/billing/reference/actions-runner-pricing)) |
| `linux_4_core_gpu` | 4 vCPU, 1 × T4 16 GB, 28 GB RAM | $0.052 / min = $3.12 / h | only GPU SKU; [GA July 2024](https://github.blog/changelog/2024-07-08-github-actions-gpu-hosted-runners-are-now-generally-available); larger GPU SKUs were [cancelled Dec 2025](https://github.com/github/roadmap/issues/1054) |

- GPU and larger runners are created through runner groups in an **organisation on a Team or
  Enterprise plan** with a card on file. A personal-account public repo cannot use them directly;
  `debrief` is an organisation, so a Team plan (about $4 per user per month) is the entry ticket.
- The 6-hour job limit applies to GPU runners too, so gitma's chained-job-with-checkpoints pattern
  stays. With a T4 an epoch of gitma's largest model takes under a minute, so a single job covers a
  whole training run and the chaining becomes a safety net rather than the norm.
- Cache is 10 GB per repo (raisable on paid plans); artifacts are 500 MB on Free. Committing
  results and weights to `results/*` branches, as gitma does, avoids both quotas.
- Alternatives that keep Actions as the orchestrator: **Modal** (T4 $0.59 / h, L4 $0.80 / h,
  per-second billing, $30 / month free credit, no 6 h limit; the Actions job calls `modal run`
  and waits), RunPod (L4 from $0.44 / h), Lambda (A10 $1.29 / h), or ephemeral self-hosted runners
  in your own AWS account via RunsOn / Cirun (T4 spot about $0.20–0.30 / h, free licences for open
  source). Self-hosted runners carry no GitHub fee today; a fee was announced and shelved in
  December 2025.
- **Cost for 50 GPU-hours a month:** GitHub T4 ≈ $156 plus the Team plan; Modal T4 ≈ $30, mostly
  inside the free credit. Both are small against the engineering time gitma spent on CPU chaining.

## 2. Throughput

Estimates for gitma's 2 × 128 LSTM (0.45 GFLOP per sequence forward + backward, 36 TFLOP per
80,000-sequence epoch):

| Platform | Epoch time | Compared with gitma's tfjs-node 4-core (≈ 60 min) |
| --- | --- | --- |
| PyTorch CPU, 4 cores, oneDNN LSTM | 8–20 min | 3–7 × |
| 16-core larger runner | perhaps 3 × better again | latency-bound, scales poorly |
| T4, cuDNN LSTM, batch 256 | 20–40 s | 100 × |
| Small transformer (4 × d128, 360 tokens) on T4 | about 1 min | far better suited to GPU than CPU |

- cuDNN handles `nn.LSTM`/`nn.GRU` automatically; `torch.compile` does not fuse them (graph
  break) but does help transformers and hand-written per-step layers.
- A hand-written recurrence (a filter layer) in eager PyTorch is 5–20 × slower than cuDNN; in JAX
  `lax.scan` under `jit` is the idiomatic, fast answer, and `vmap` gives batched filters for free.
  JAX on CPU runners works with the standard wheels.
- A differentiable Gauss-Newton solve over a 360-row window is a few small batched linear solves
  per iteration; on a GPU it is negligible next to the encoder.

## 3. Portable model artefacts

**ONNX is the only format with first-party runtimes in all four target technologies.** ONNX
Runtime 1.31 ships Python, C/C++, Java (Maven `com.microsoft.onnxruntime`), C# and
`onnxruntime-web` (WASM, WebGPU, WebNN).

- **Operator coverage.** LSTM/GRU/RNN, `Scan`, `Loop` and `If` are standard ops, fully supported by
  the ORT CPU execution provider, which also backs the browser **WASM** path ("all ONNX operators
  are supported by WASM"). The browser **WebGPU** provider lacks LSTM/GRU/Scan/Loop in its JSEP
  table (an LSTM kernel landed in the newer native WebGPU EP in 2026). For a model of this size,
  scored a few hundred times a second, WASM with SIMD and threads is adequate; treat WebGPU as an
  optimisation. Attention, LayerNorm and MatMul are covered everywhere, which favours a
  transformer or MLP encoder over a recurrent one for portability.
- **Custom recursions** (a Kalman-style layer, or an unrolled Gauss-Newton refinement in ordinary
  tensor ops) export two ways: unrolled (a large but plain graph; runs everywhere) or as `Scan`
  (compact; ORT CPU/WASM/Java/C++ but not browser GPU). A **fixed number of unrolled iterations**
  with no data-dependent control flow is the portable choice. Mamba-style selective scan has no
  standard op: avoid it, or accept an unrolled graph.
- **Exporter pitfalls.** The PyTorch dynamo exporter gained LSTM/GRU only in November 2025 and still
  reports gate-order and dynamic-dimension bugs; the legacy TorchScript exporter is reliable for
  fixed layouts. ONNX LSTM is `[seq, batch, feat]` by default (transpose for batch-first). Export
  with a fixed sequence length (360) and a dynamic batch.
- **Keras 3** exports ONNX from any backend, but the TF.js converter still does not accept `.keras`
  v3 files; TF.js is a dead end for a non-TF training stack.
- **Second sources.** safetensors (weights only, trivial loaders in every language) plus a JSON
  architecture manifest, so a reference implementation can be written by hand if ONNX ever fails;
  tract (Rust → WASM, runs ONNX LSTM/GRU/Scan) and burn-onnx as insurance. GGUF and ExecuTorch do
  not fit.
- **Conformance in CI.** Export, then compare ORT Python, ORT-web (WASM under Playwright) and
  ORT-Java outputs against the training framework on a golden batch to 1e-5. This replaces gitma's
  "byte-identical golden files across ports" for the model, which is what the owner's transfer
  requirement actually needs.

## 4. Simulation stack in Python

- **Stone Soup 1.9.1** (Dstl, MIT): EKF/UKF/CKF/PF/Rao-Blackwellised multi-model predictors and a
  bearings-only example, but **no classical IMM** and an object-per-state design that its own
  docs call unoptimised. Right for spot-checking a handful of reference trackers; wrong for
  generating 10^6 scenarios per epoch. FilterPy 2.0 (October 2026) is a textbook-clear cross-check
  only.
- **Vectorised generation** is the practical route: arrays of shape [N, T, …] in JAX (`vmap` +
  `lax.scan`, counter-based `jax.random` so a seed determines a batch regardless of order) or
  numba with a per-scenario PCG64 stream. Either gives ≥ 10^5 scenarios per second on 4 cores, so
  on-the-fly generation during training is not the bottleneck. gitma's generator ran at about
  550–1,000 scenarios per second single-threaded in Node.
- gitma's tuned IMM/EKF and batch LS must be re-implemented vectorised; Stone Soup/FilterPy
  provide independent values to test them against (a stronger check than gitma had).

## 5. Reproducibility

PyTorch does not guarantee reproducibility across releases, platforms or CPU/GPU; cuDNN RNNs are
non-deterministic on some versions. Within one platform and version, `torch.manual_seed`,
`torch.use_deterministic_algorithms(True)`, `cudnn.benchmark = False` and
`CUBLAS_WORKSPACE_CONFIG` give repeatable runs. The practice that fits gitma's constitution:
record seeds, library versions, device and data digests in the manifest; treat committed weights as
the artefact of record; **verify by re-scoring frozen weights** (ORT CPU inference is deterministic
at a fixed thread count), never by re-training; gate on statistical intervals that absorb run
jitter. gitma already does all but the first in spirit (`cpu_model` in each manifest).

## Recommended stack

- **Simulation and references:** a Python package of pure, vectorised functions (JAX, or NumPy +
  numba) implementing the generator, batch least squares, EKF, IMM and the Fisher information,
  with Stone Soup/FilterPy as independent checks and golden files regenerated from gitma's
  generator for the handful of fixed scenarios that pin the frame conventions.
- **Training:** PyTorch 2.x for a transformer/MLP encoder; JAX if most of the model is custom
  recursion. (A middle path: write the model in PyTorch and the differentiable solver as unrolled
  batched tensor ops, which both frameworks and ONNX handle.)
- **Artefact:** ONNX (opset 17–18, fixed length, dynamic batch, standard ops only) plus
  safetensors and a JSON manifest; conformance test across ORT Python, ORT-web WASM and ORT-Java
  in CI.
- **Runtimes:** `onnxruntime` (Python), `onnxruntime-web` WASM (browser viewer), ORT Java, ORT C
  API.
- **CI compute:** `ubuntu-latest` for tests, generation, scoring and conformance. For training,
  either the `linux_4_core_gpu` T4 runner under a Team plan (one vendor, one audit trail, 6 h jobs
  with checkpoint chaining kept as a safety net) or an Actions job that drives Modal (4–5 × cheaper,
  no job limit, personal account works). The owner's call; both keep "push a plan branch, get a
  results branch".

## Top risks

1. Recurrent-layer ONNX export from the new dynamo exporter: pin the exporter path and gate on
   conformance.
2. Browser GPU coverage for recurrent and scan ops: plan on WASM.
3. Custom filter or solver layers must be unrolled with fixed iteration counts to stay portable.
4. GPU runner access is organisation-only with a single T4 SKU.
5. Determinism becomes statistical on GPU: keep CPU re-scoring of frozen weights as the proof.
6. No IMM in Stone Soup: the reference trackers are re-implemented and cross-checked, not imported.
