// The browser viewer on the exported artefact (spec 020). Runs the carried Gate 2 model's
// exported E-w graph in ONNX Runtime Web, in a worker, on demo engagements whose host-side
// inputs (C's segmentation with E-s's evidence, and C's hand-over) were built in Python and
// shipped as data. Comparison estimates are Python's, shipped beside. Nothing here is a result.
import React, { useEffect, useMemo, useRef, useState } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import BrowserOnly from "@docusaurus/BrowserOnly";

const KT = 0.514444;
const COLOURS = {
  e: "#2ca02c",
  one_leg: "#7f7f7f",
  imm: "#ff7f0e",
  c: "#9467bd",
  c2: "#8c564b",
  live: "#17becf",
};
const OWN = "#1f77b4";
const TGT = "#d62728";
const MAX_RANGE = 100000;
const MAX_SPEED = 25;

// ---------- data ----------

async function fetchGz(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const raw = await res.arrayBuffer();
  const plain = await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
  return { raw, plain };
}

async function sha256Hex(buf) {
  const h = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(h), (b) => b.toString(16).padStart(2, "0")).join("");
}

function prod(a) {
  return a.reduce((x, y) => x * y, 1);
}

// The graph's feeds for E's r-th row, from the engagement's layout and binary values.
function feedsFor(eng, values, r) {
  const feeds = {};
  for (const L of eng.layout) {
    if (L.kind !== "input") continue;
    const per = prod(L.shape);
    const start = L.offset + (L.shared ? 0 : r * per);
    feeds[L.name] = { dtype: L.dtype, shape: L.shape, data: values.subarray(start, start + per) };
  }
  return feeds;
}

function pythonOutputs(eng, values, r) {
  const out = {};
  for (const L of eng.layout) {
    if (L.kind !== "output") continue;
    const per = prod(L.shape);
    out[L.name] = values.subarray(L.offset + r * per, L.offset + (r + 1) * per);
  }
  return out;
}

// ---------- estimates and errors (as eval.errors.row_error and plausible_row) ----------

function fromState(s, own) {
  const [x, y, vx, vy] = s;
  return {
    x_m: x,
    y_m: y,
    range_m: Math.hypot(x - own[0], y - own[1]),
    course_rad: ((Math.atan2(vx, vy) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI),
    speed_mps: Math.hypot(vx, vy),
  };
}

function answered(r) {
  if (!r) return false;
  const v = [r.range_m, r.course_rad, r.speed_mps, r.x_m, r.y_m];
  if (!v.every(Number.isFinite)) return false;
  return r.range_m > 0 && r.range_m <= MAX_RANGE && r.speed_mps <= MAX_SPEED;
}

function angleDiffDeg(a, b) {
  let d = ((a - b) * 180) / Math.PI;
  d = ((d % 360) + 540) % 360 - 180;
  return Math.abs(d);
}

function errors(r, truth, own) {
  const rng = Math.hypot(truth[0] - own[0], truth[1] - own[1]);
  return {
    range_pct: (100 * Math.abs(r.range_m - rng)) / rng,
    course_deg: angleDiffDeg(r.course_rad, truth[2]),
    speed_kt: Math.abs(r.speed_mps - truth[3]) / KT,
  };
}

function bearingDeg(r, own) {
  return (((Math.atan2(r.x_m - own[0], r.y_m - own[1]) * 180) / Math.PI) + 360) % 360;
}

// 1-σ ellipse of the position block of a 4 × 4 covariance (row-major).
function ellipse(cov) {
  const a = cov[0], b = cov[1], d = cov[5];
  if (![a, b, d].every(Number.isFinite)) return null;
  const tr = (a + d) / 2;
  const det = Math.sqrt(Math.max(((a - d) / 2) ** 2 + b * b, 0));
  const l1 = tr + det, l2 = tr - det;
  if (!(l1 > 0 && l2 > 0)) return null;
  const angle = Math.atan2(l1 - a, b === 0 ? 1e-300 : b); // direction of the major axis
  return { rx: Math.sqrt(l1), ry: Math.sqrt(l2), angle: b === 0 ? (a >= d ? 0 : Math.PI / 2) : angle };
}

// ---------- the compute engine (shared by the page and the conformance leg) ----------

class Engine {
  constructor(workerUrl, ortBase, models) {
    this.worker = new Worker(workerUrl, { type: "module" });
    this.pending = new Map();
    this.next = 0;
    this.ready = new Promise((resolve, reject) => {
      this.worker.onmessage = (ev) => {
        const m = ev.data;
        if (m.type === "ready") {
          this.loadMs = m.loadMs;
          resolve();
        } else if (m.type === "progress") {
          const p = this.pending.get(m.id);
          if (p && p.onProgress) p.onProgress(m);
        } else if (m.type === "result" || m.type === "live-done" || m.type === "error") {
          const p = this.pending.get(m.id);
          if (p) {
            this.pending.delete(m.id);
            if (m.type === "error") p.reject(new Error(m.message));
            else p.resolve(m);
          } else if (m.type === "error") reject(new Error(m.message));
        }
      };
      this.worker.onerror = (e) => {
        const err = new Error(e.message || "worker failed");
        for (const p of this.pending.values()) p.reject(err); // a crash fails what is waiting
        this.pending.clear();
        this.failed = err;
        reject(err);
      };
    });
    this.worker.postMessage({ type: "init", ortBase, models });
  }
  // live mode (spec 021): the whole model from a scenario's arrays; cancel() stops it
  live(scenario, onProgress) {
    if (this.failed) return { done: Promise.reject(this.failed), cancel: () => {} };
    const id = this.next++;
    const done = new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, onProgress });
      this.worker.postMessage({ type: "live", id, scenario });
    });
    return { done, cancel: () => this.worker.postMessage({ type: "cancel", id }) };
  }
  run(feeds) {
    if (this.failed) return Promise.reject(this.failed);
    const id = this.next++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ type: "run", id, feeds });
    });
  }
}

// ---------- live mode (spec 021) ----------

const sameIvs = (a, b) =>
  JSON.stringify(a.map((iv) => [iv.kind, iv.start, iv.end, !!iv.open])) === JSON.stringify(b.map((iv) => [iv[0], iv[1], iv[2], !!iv[3]]));

// Live results against Python: the segmentation against Python's E run alone (the scenario
// file), the estimate against the shipped Python outputs (Gate 2's chunked segmentation).
function compareLive(eng, values, scen, result) {
  const rows = result.rows.length;
  let segSame = 0, estSame = 0, estRows = 0, worst = 0;
  const differ = [];
  for (let q = 0; q < rows; q++) {
    const k = result.rows[q];
    const py = scen.python_e_intervals[String(k)];
    const same = py && sameIvs(result.intervals[q], py);
    if (same) segSame++;
    else differ.push(k);
    const r = eng.e_rows.indexOf(q);
    const est = result.estimates[q];
    if (r >= 0 && est) {
      estRows++;
      const pyo = pythonOutputs(eng, values, r);
      let w = 0;
      for (let i = 0; i < 4; i++) w = Math.max(w, Math.abs(est.state[i] - pyo.state[i]) / Math.max(Math.abs(pyo.state[i]), 1));
      worst = Math.max(worst, w);
      if (w <= 1e-5) estSame++;
    }
  }
  const pyDec = scen.python_e_decisions.map((d) => [d[0], d[1], d[2], d[3], d[6]]);
  const dec = result.decisions.map((d) => [d.row, d.start, d.length, d.source, d.accepted]);
  return { rows, segmentation_same: segSame, rows_differ: differ, estimate_rows: estRows, estimate_same: estSame, estimate_max_rel: worst, decisions_same: JSON.stringify(dec) === JSON.stringify(pyDec), decisions: dec.length, min_abs_score: Math.min(...result.decisions.map((d) => Math.abs(d.score))) };
}

// ---------- plot ----------

function TrackPlot({ eng, q, show, eRows, showEllipse }) {
  const W = 640, H = 520, PAD = 30;
  const k = eng.rows[q];
  const box = useMemo(() => {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const p of [...eng.own, ...eng.target]) {
      x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]);
      y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]);
    }
    const span = Math.max(x1 - x0, y1 - y0) * 1.25 + 2000;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    return { x0: cx - span / 2, y0: cy - span / 2, span };
  }, [eng]);
  const sx = (x) => PAD + ((x - box.x0) / box.span) * (W - 2 * PAD);
  const sy = (y) => H - PAD - ((y - box.y0) / box.span) * (H - 2 * PAD);
  const scale = (W - 2 * PAD) / box.span;
  const line = (pts) => pts.map((p) => `${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`).join(" ");
  const trails = [];
  const markers = [];
  for (const [name, rows] of Object.entries(show)) {
    if (!rows) continue;
    const segs = [];
    let cur = [];
    for (let i = 0; i <= q; i++) {
      const r = rows[i];
      if (answered(r)) cur.push([r.x_m, r.y_m]);
      else if (cur.length) { segs.push(cur); cur = []; }
    }
    if (cur.length) segs.push(cur);
    segs.forEach((s, j) =>
      trails.push(<polyline key={`${name}-${j}`} points={line(s)} fill="none" stroke={COLOURS[name]} strokeWidth={1.4} opacity={0.85} />)
    );
    const r = rows[q];
    if (answered(r)) {
      markers.push(<circle key={`m-${name}`} cx={sx(r.x_m)} cy={sy(r.y_m)} r={4.5} fill={COLOURS[name]} stroke="white" strokeWidth={1} />);
    }
  }
  let ell = null;
  if (showEllipse && eRows && eRows.cov[q]) {
    const e = ellipse(eRows.cov[q]);
    const r = show.e && show.e[q];
    if (e && answered(r)) {
      ell = (
        <ellipse
          cx={sx(r.x_m)} cy={sy(r.y_m)} rx={e.rx * scale} ry={e.ry * scale}
          transform={`rotate(${(-e.angle * 180) / Math.PI} ${sx(r.x_m)} ${sy(r.y_m)})`}
          fill={COLOURS.e} fillOpacity={0.12} stroke={COLOURS.e} strokeDasharray="4 3" data-testid="ellipse"
        />
      );
    }
  }
  const z = eng.zig_index;
  const target = box.span / 5; // a round length near a fifth of the plot: 1, 2 or 5 × 10^n m
  const p10 = Math.pow(10, Math.floor(Math.log10(target)));
  const km = [5, 2, 1].map((f) => f * p10).find((v) => v <= target) || p10;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: W, background: "var(--ifm-background-surface-color)", border: "1px solid var(--ifm-color-emphasis-300)", borderRadius: 6 }} role="img" aria-label="Track plot">
      <defs>
        <clipPath id="plotclip"><rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD} /></clipPath>
      </defs>
      <g clipPath="url(#plotclip)">
        <polyline points={line(eng.own)} fill="none" stroke={OWN} strokeWidth={1.6} />
        <polyline points={line(eng.target)} fill="none" stroke={TGT} strokeWidth={1.8} />
        <circle cx={sx(eng.own[z][0])} cy={sy(eng.own[z][1])} r={3} fill={OWN} />
        <circle cx={sx(eng.own[k][0])} cy={sy(eng.own[k][1])} r={5} fill={OWN} />
        <circle cx={sx(eng.target[k][0])} cy={sy(eng.target[k][1])} r={5} fill={TGT} />
        <line x1={sx(eng.own[k][0])} y1={sy(eng.own[k][1])} x2={sx(eng.target[k][0])} y2={sy(eng.target[k][1])} stroke="#999" strokeDasharray="2 3" />
        {trails}
        {ell}
        {markers}
      </g>
      <line x1={W - PAD - km * scale} y1={H - 12} x2={W - PAD} y2={H - 12} stroke="currentColor" />
      <text x={W - PAD} y={H - 16} textAnchor="end" fontSize={11} fill="currentColor">{km / 1000} km</text>
      <text x={PAD} y={18} fontSize={11} fill="currentColor">north up; small blue dot: ownship at its zig</text>
    </svg>
  );
}

// ---------- page ----------

function fmt(v, d = 1) {
  return Number.isFinite(v) ? v.toFixed(d) : "–";
}

function Viewer() {
  const base = useBaseUrl("/viewer-data/");
  const ortBase = useBaseUrl("/ort/");
  const gate2Url = useBaseUrl("/blog/2026/11/08/gate-2");
  const [manifest, setManifest] = useState(null);
  const [digestState, setDigestState] = useState({});
  const [error, setError] = useState(null);
  const [engIdx, setEngIdx] = useState(0);
  const [eng, setEng] = useState(null);
  const [values, setValues] = useState(null);
  const [q, setQ] = useState(0);
  const [eRows, setERows] = useState(null);
  const [progress, setProgress] = useState({ done: 0, total: 0, ms: [] });
  const [shown, setShown] = useState({ one_leg: false, imm: true, c: false, c2: true });
  const [showEllipse, setShowEllipse] = useState(false);
  const [runtime, setRuntime] = useState("loading the runtime…");
  const [live, setLive] = useState(null); // {engIdx, status, progress, result, compare, seconds}
  const liveRun = useRef(null);
  const engine = useRef(null);
  const job = useRef(0);

  // manifest, model digest, engine
  useEffect(() => {
    (async () => {
      try {
        const m = await (await fetch(base + "manifest.json")).json();
        setManifest(m);
        const model = await (await fetch(base + "model.onnx")).arrayBuffer();
        const got = await sha256Hex(model);
        setDigestState((s) => ({ ...s, "model.onnx": got === m.files["model.onnx"] }));
        if (got !== m.files["model.onnx"]) throw new Error(`model.onnx digest ${got.slice(0, 12)}… is not the manifest's`);
        const blobUrl = URL.createObjectURL(new Blob([model]));
        // spec 021's graphs: E-s's evidence and the physics layer at confirmation's settings
        const models = { ew: blobUrl };
        for (const [key, file] of [["es", "es.onnx"], ["layer", "layer.onnx"]]) {
          if (!m.files[file]) continue;
          const buf = await (await fetch(base + file)).arrayBuffer();
          const ok = (await sha256Hex(buf)) === m.files[file];
          setDigestState((st) => ({ ...st, [file]: ok }));
          if (ok) models[key] = URL.createObjectURL(new Blob([buf]));
        }
        engine.current = new Engine(base + "worker.js", window.location.origin + ortBase, models);
        await engine.current.ready;
        setRuntime(`ONNX Runtime Web (WASM, one thread); graph loaded in ${fmt(engine.current.loadMs, 0)} ms`);
      } catch (e) {
        setError(String(e.message || e));
        setRuntime("the runtime did not load: the truth and the Python comparisons are still shown");
      }
    })();
  }, [base, ortBase]);

  // a live run belongs to its engagement: switching cancels it
  useEffect(() => {
    if (liveRun.current) liveRun.current.cancel();
    liveRun.current = null;
    setLive(null);
  }, [engIdx]);

  async function loadScenario(meta) {
    const sc = await fetchGz(base + meta.scenario);
    if ((await sha256Hex(sc.raw)) !== manifest.files[meta.scenario]) throw new Error(`${meta.scenario}: digest is not the manifest's`);
    return JSON.parse(new TextDecoder().decode(sc.plain));
  }

  async function startLive() {
    const meta = manifest.engagements[engIdx];
    const mine = engIdx;
    try {
      const scen = await loadScenario(meta);
      setLive({ engIdx: mine, status: "running", progress: null });
      const t0 = performance.now();
      const handle = engine.current.live(scen, (p) => setLive((l) => (l && l.engIdx === mine && l.status === "running" ? { ...l, progress: p } : l)));
      liveRun.current = handle;
      const res = await handle.done;
      if (liveRun.current !== handle) return; // switched away
      const compare = eng && values ? compareLive(eng, values, scen, res.result) : null;
      setLive({ engIdx: mine, status: "done", result: res.result, compare, seconds: (performance.now() - t0) / 1000 });
    } catch (err) {
      setLive((l) => (l && l.engIdx === mine ? { ...l, status: "failed", error: String(err.message || err) } : l));
    }
  }

  // engagement data
  useEffect(() => {
    if (!manifest) return;
    const meta = manifest.engagements[engIdx];
    let cancelled = false;
    (async () => {
      try {
        setEng(null); setValues(null); setERows(null);
        const js = await fetchGz(base + meta.json);
        const bn = await fetchGz(base + meta.binary);
        const okJ = (await sha256Hex(js.raw)) === manifest.files[meta.json];
        const okB = (await sha256Hex(bn.raw)) === manifest.files[meta.binary];
        setDigestState((s) => ({ ...s, [meta.json]: okJ, [meta.binary]: okB }));
        if (!okJ || !okB) throw new Error(`${okJ ? meta.binary : meta.json}: digest is not the manifest's; estimates are not shown`);
        if (cancelled) return;
        const e = JSON.parse(new TextDecoder().decode(js.plain));
        setEng(e);
        setValues(new Float64Array(bn.plain));
        setQ(Math.min(e.rows.length - 1, Math.round(e.rows.length / 2)));
      } catch (err) {
        setError(String(err.message || err));
      }
    })();
    return () => { cancelled = true; };
  }, [manifest, engIdx, base]);

  // run E in the browser: the current row first, then the rest in order
  useEffect(() => {
    const my = ++job.current; // any earlier loop stops writing from here on
    if (!eng || !values || !engine.current) return undefined;
    const R = eng.rows.length;
    const pos = new Map(eng.e_rows.map((qq, r) => [qq, r]));
    const state = new Array(R).fill(null);
    const cov = new Array(R).fill(null);
    const flags = new Array(R).fill(null);
    const ms = [];
    const order = [...eng.e_rows].sort((a, b) => (a === q ? -1 : b === q ? 1 : a - b));
    setERows({ state, cov, flags, browser: true });
    setProgress({ done: 0, total: order.length, ms: [] });
    (async () => {
      try {
        await engine.current.ready;
        for (const qq of order) {
          if (job.current !== my) return;
          const res = await engine.current.run(feedsFor(eng, values, pos.get(qq)));
          if (job.current !== my) return; // the engagement changed while this row ran
          state[qq] = Array.from(res.outputs.state);
          cov[qq] = Array.from(res.outputs.cov);
          flags[qq] = { plausible: res.outputs.plausible[0] === 1, cov_ok: res.outputs.cov_ok[0] === 1 };
          ms.push(res.ms);
          if (window.__viewerFirstMs === undefined) window.__viewerFirstMs = performance.now();
          setERows({ state: [...state], cov: [...cov], flags: [...flags], browser: true });
          setProgress({ done: ms.length, total: order.length, ms: [...ms] });
        }
      } catch (err) {
        if (job.current === my) setError(String(err.message || err));
      }
    })();
    return () => {
      job.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eng, values, runtime]);

  // the conformance leg drives the same code: every E row, browser against Python
  useEffect(() => {
    window.__viewer = {
      manifest: () => manifest,
      digests: () => digestState,
      async checkAll() {
        const out = [];
        for (const meta of manifest.engagements) {
          const js = await fetchGz(base + meta.json);
          const bn = await fetchGz(base + meta.binary);
          const e = JSON.parse(new TextDecoder().decode(js.plain));
          const v = new Float64Array(bn.plain);
          await engine.current.ready;
          for (let r = 0; r < e.e_rows.length; r++) {
            const res = await engine.current.run(feedsFor(e, v, r));
            const py = pythonOutputs(e, v, r);
            let worst = 0;
            const by = {};
            for (const name of Object.keys(py)) {
              const a = res.outputs[name], b = py[name];
              by[name] = { max_rel_diff: 0, at: -1, browser: null, python: null };
              for (let i = 0; i < b.length; i++) {
                if (Number.isNaN(a[i]) && Number.isNaN(b[i])) continue;
                const d = Math.abs(a[i] - b[i]) / Math.max(Math.abs(b[i]), 1);
                if (!(d <= by[name].max_rel_diff)) by[name] = { max_rel_diff: d, at: i, browser: a[i], python: b[i] };
              }
              worst = Math.max(worst, by[name].max_rel_diff);
            }
            // the covariance on its own scale: |Δ P_ij| / max(sqrt(|P_ii P_jj|), 1) (spec 020 R6)
            {
              const a = res.outputs.cov, b = py.cov;
              let w = 0;
              for (let i = 0; i < 4; i++)
                for (let j = 0; j < 4; j++) {
                  const s = Math.max(Math.sqrt(Math.abs(b[i * 4 + i] * b[j * 4 + j])), 1);
                  w = Math.max(w, Math.abs(a[i * 4 + j] - b[i * 4 + j]) / s);
                }
              by.cov_scaled = { max_rel_diff: w };
            }
            out.push({ engagement: meta.id, row: e.rows[e.e_rows[r]], max_rel_diff: worst, ms: res.ms, outputs: by });
          }
        }
        return { rows: out, loadMs: engine.current.loadMs, userAgent: navigator.userAgent };
      },
      // spec 021: live mode on engagement i, compared with Python
      async live(i) {
        const meta = manifest.engagements[i];
        const js = await fetchGz(base + meta.json);
        const bn = await fetchGz(base + meta.binary);
        const e = JSON.parse(new TextDecoder().decode(js.plain));
        const v = new Float64Array(bn.plain);
        const scen = await loadScenario(meta);
        await engine.current.ready;
        const stages = [];
        const t0 = performance.now();
        const res = await engine.current.live(scen, (p) => {
          if (!stages.length || stages[stages.length - 1].stage !== p.stage) stages.push({ stage: p.stage, seconds: p.seconds });
        }).done;
        return { engagement: i, ordinal: meta.ordinal, seconds: (performance.now() - t0) / 1000, stages, ...compareLive(e, v, scen, res.result) };
      },
    };
  }, [manifest, digestState, base]);

  if (!manifest) return <p>{error ? `The viewer could not load its data: ${error}` : "Loading…"}</p>;
  const meta = manifest.engagements[engIdx];

  // rows of every system at each scored time
  const show = {};
  if (eng) {
    if (eRows) show.e = eng.rows.map((k, i) => (eRows.state[i] ? fromState(eRows.state[i], eng.own[k]) : null));
    for (const s of Object.keys(shown)) if (shown[s]) show[s] = eng.systems[s];
    if (live && live.engIdx === engIdx && live.status === "done") {
      show.live = live.result.estimates.map((x, i) => (x ? fromState(x.state, eng.own[live.result.rows[i]]) : null));
    }
  }
  const k = eng ? eng.rows[q] : 0;
  const minutes = eng ? ((k - eng.zig_index) * eng.dt_s) / 60 : 0;
  const tableRows = eng
    ? [["e", show.e], ...(show.live ? [["live", show.live]] : []), ...Object.keys(shown).map((s) => [s, eng.systems[s]])].map(([s, rows]) => {
        const r = rows ? rows[q] : null;
        const ok = answered(r);
        const err = ok ? errors(r, eng.target[k], eng.own[k]) : null;
        let note = "";
        if (s === "e") {
          if (!eng.e_rows.includes(q)) note = "no input: C's hand-over has no valid bearing";
          else if (!eRows || !eRows.state[q]) note = "computing…";
          else if (!ok) note = "no answer (implausible solve)";
          if (eng.open[q]) note += (note ? "; " : "") + "the last transition (C with E-s's evidence) is still open";
        } else if (!ok) note = "no answer";
        return { s, r, ok, err, note };
      })
    : [];
  const median = (a) => { const b = [...a].sort((x, y) => x - y); return b.length ? b[Math.floor(b.length / 2)] : NaN; };

  return (
    <div className="container margin-vert--lg" style={{ maxWidth: 1100 }}>
      <h1>Browser viewer: the carried model, running here</h1>
      <p>
        This page runs the exported graph of Gate 2's carried model E in your browser and draws its estimate of a
        simulated target. The graph is E-w: learned per-bearing weights and a start correction feeding the declared
        physics layer. It is a demonstration on a handful of engagements, not a result. The figures of record are in
        the <a href={gate2Url}>Gate 2 write-up</a>. All data are simulated: mock data, nothing
        above OFFICIAL. C's segmentation, with E-s's learned evidence, ran in Python ahead of time and is shipped as
        data. The other systems' estimates were also computed in Python.
      </p>
      {error && <div className="alert alert--danger" role="alert">{error}</div>}
      <p><small>{runtime}</small></p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", margin: "0.8rem 0" }}>
        {manifest.engagements.map((m) => (
          <button key={m.id} className={`button button--sm ${m.id === engIdx ? "button--primary" : "button--secondary"}`} onClick={() => setEngIdx(m.id)}>
            {m.id + 1}: {m.reason} (ordinal {m.ordinal})
          </button>
        ))}
      </div>
      {manifest.data.selection.missing.length > 0 && (
        <p><small>No engagement within the rule's limit for: {manifest.data.selection.missing.join(", ")}.</small></p>
      )}

      {eng ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1.2rem" }}>
          <div style={{ flex: "1 1 100%", minWidth: 0, maxWidth: 680 }}>
            <TrackPlot eng={eng} q={q} show={show} eRows={eRows} showEllipse={showEllipse} />
            <div style={{ marginTop: "0.5rem" }}>
              <label htmlFor="t">
                Time: zig + {fmt(minutes, 0)} min (row {k} of {eng.samples}); estimates start 5 minutes after the ownship's
                zig, because before it the state is undetermined.
              </label>
              <input id="t" type="range" min={0} max={eng.rows.length - 1} value={q} onChange={(ev) => setQ(Number(ev.target.value))} style={{ width: "100%" }} />
            </div>
            <p><small>
              E in your browser: {progress.done} of {progress.total} rows
              {progress.ms.length ? `, median ${fmt(median(progress.ms), 0)} ms a row` : ""}.
            </small></p>
          </div>
          <div style={{ flex: "1 1 100%", minWidth: 0 }}>
            <p>
              Engagement {meta.id + 1}: {meta.reason}. The target manoeuvres {meta.manoeuvres} time(s) while
              estimates are shown ({eng.manoeuvres.length} in the whole window). Seed 319, ordinal {eng.ordinal}.
            </p>
            <div style={{ overflowX: "auto" }}>
              <table style={{ fontSize: "0.85rem", whiteSpace: "nowrap" }}>
                <thead>
                  <tr><th>system</th><th>range km</th><th>bearing °</th><th>course °</th><th>speed kt</th><th>range err %</th><th>course err °</th><th>speed err kt</th></tr>
                </thead>
                <tbody>
                  <tr style={{ color: TGT }}>
                    <td>truth</td>
                    <td>{fmt(Math.hypot(eng.target[k][0] - eng.own[k][0], eng.target[k][1] - eng.own[k][1]) / 1000, 2)}</td>
                    <td>{fmt(bearingDeg({ x_m: eng.target[k][0], y_m: eng.target[k][1] }, eng.own[k]), 1)}</td>
                    <td>{fmt((eng.target[k][2] * 180) / Math.PI, 1)}</td>
                    <td>{fmt(eng.target[k][3] / KT, 1)}</td>
                    <td /><td /><td />
                  </tr>
                  {tableRows.map(({ s, r, ok, err, note }) => (
                    <tr key={s}>
                      <td>
                        <span style={{ color: COLOURS[s] }}>●</span>{" "}
                        {s === "e" ? "E" : s === "live" ? "E live (all in your browser)" : <label><input type="checkbox" checked={shown[s]} onChange={() => setShown({ ...shown, [s]: !shown[s] })} /> {manifest.systems[s].split(",")[0].split(" (")[0]}</label>}
                        {note && <div><small>{note}</small></div>}
                      </td>
                      {ok ? (
                        <>
                          <td>{fmt(r.range_m / 1000, 2)}</td>
                          <td>{fmt(bearingDeg(r, eng.own[k]), 1)}</td>
                          <td>{fmt((r.course_rad * 180) / Math.PI, 1)}</td>
                          <td>{fmt(r.speed_mps / KT, 1)}</td>
                          <td>{fmt(err.range_pct, 1)}</td>
                          <td>{fmt(err.course_deg, 1)}</td>
                          <td>{fmt(err.speed_kt, 1)}</td>
                        </>
                      ) : (
                        <td colSpan={7}><small>{s === "e" && !eRows ? "" : "no answer"}</small></td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p><small>
              {Object.entries(manifest.systems).map(([s, label]) => (
                <span key={s} style={{ display: "block" }}><span style={{ color: COLOURS[s] }}>●</span> {label}</span>
              ))}
            </small></p>
            {meta.scenario && (
              <div className="margin-vert--sm" data-testid="live-panel">
                {!live || live.engIdx !== engIdx ? (
                  <button className="button button--sm button--outline button--primary" onClick={startLive} disabled={!engine.current}>
                    Run live: the whole model from bearings, in your browser
                  </button>
                ) : live.status === "running" ? (
                  <p><small>
                    Live: {live.progress ? live.progress.stage : "starting"}
                    {live.progress && live.progress.stage === "confirmation" ? ` (${live.progress.decided} of ${live.progress.nominations} nominations decided)` : ""}
                    {live.progress && live.progress.stage === "estimates" ? ` (${live.progress.done} of ${live.progress.of} rows)` : ""}
                    {live.progress ? `, ${fmt(live.progress.seconds, 0)} s` : ""}.{" "}
                    <button className="button button--sm button--link" onClick={() => { liveRun.current && liveRun.current.cancel(); liveRun.current = null; setLive(null); }}>cancel</button>
                  </small></p>
                ) : live.status === "failed" ? (
                  <p><small>Live mode failed: {live.error}</small></p>
                ) : (
                  <p data-testid="live-summary"><small>
                    Live, in {fmt(live.seconds, 0)} s: the segmenter C, E-s's evidence and E-w all ran here from the bearings.
                    {live.compare && (
                      <> Segmentation identical to Python's at {live.compare.segmentation_same} of {live.compare.rows} rows
                      {live.compare.rows_differ.length ? ` (differs at rows ${live.compare.rows_differ.join(", ")})` : ""};
                      estimate within 1e-5 of the shipped Python estimate at {live.compare.estimate_same} of {live.compare.estimate_rows} rows.</>
                    )}
                  </small></p>
                )}
              </div>
            )}
            <label>
              <input type="checkbox" checked={showEllipse} onChange={() => setShowEllipse(!showEllipse)} data-testid="ellipse-toggle" /> show E's 1-σ
              position ellipse
            </label>
            {showEllipse && (
              <div className="alert alert--warning" role="alert" data-testid="ellipse-warning" style={{ marginTop: "0.5rem" }}>
                {manifest.uncertainty_warning}
              </div>
            )}
          </div>
        </div>
      ) : (
        !error && <p>Loading the engagement…</p>
      )}

      <details style={{ marginTop: "1.5rem" }}>
        <summary>What is running, by digest</summary>
        <ul style={{ fontSize: "0.85rem" }}>
          {Object.entries(manifest.files).map(([f, d]) => (
            <li key={f}>
              <code>{f}</code> <code>{d.slice(0, 16)}…</code>{" "}
              {f in digestState ? (digestState[f] ? "checked here ✓" : "MISMATCH") : "not loaded yet"}
            </li>
          ))}
          <li>E-w weights <code>{manifest.model.ew_weights_sha256.slice(0, 16)}…</code>, E-s weights{" "}
            <code>{manifest.model.es_weights_sha256.slice(0, 16)}…</code> ({manifest.model.carried})</li>
          <li>C's code <code>{manifest.model.c_code_sha256.slice(0, 16)}…</code>; Gate 2 plan <code>{manifest.model.plan_sha256.slice(0, 16)}…</code></li>
          <li>Data: seed {manifest.data.seed}, {manifest.data.split} split ({manifest.data.used_by}); <code>{manifest.data.generate}</code></li>
          <li>Built by <code>{manifest.built.command}</code> at commit <code>{manifest.built.git_commit.slice(0, 10)}</code>{manifest.built.git_dirty ? " (dirty tree)" : ""}</li>
        </ul>
      </details>
    </div>
  );
}

export default function ViewerPage() {
  return (
    <Layout title="Browser viewer" description="The carried model's exported graph, running in your browser">
      <BrowserOnly fallback={<div className="container margin-vert--lg"><p>The viewer needs JavaScript.</p></div>}>
        {() => <Viewer />}
      </BrowserOnly>
    </Layout>
  );
}
