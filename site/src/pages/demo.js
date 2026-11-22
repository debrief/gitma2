// The interactive TMA demonstrator (spec 035). Stakeholders drag an ownship (blue) and a target
// (red) track, add steady turns, narrow the analysis window, and see a time-late solution
// recomputed on release with its dashboard. Solvers run in a worker (static/demo-data/worker.js);
// the track, bearing and dashboard code is static/demo-data/js/, shared with the Node tests.
// Nothing here is a result: one noise draw at a time, in a toy two-vessel world.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import BrowserOnly from "@docusaurus/BrowserOnly";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import * as T from "../../static/demo-data/js/track.js";
import { bearings, windowRows, problemOf, targetManoeuvresIn, ownTurnsIn, SCHEMA_VERSION } from "../../static/demo-data/js/scenario.js";
import { evaluate, observability, compareLegs, OBS_GREEN, OBS_AMBER, OBS_SIGMA_DEG } from "../../static/demo-data/js/metrics.js";
import { PRESETS, DEFAULT_SCENARIO, clone, normaliseScenario } from "../../static/demo-data/js/presets.js";
import { SOLVER_LIST, SPLITTER_LIST } from "../../static/demo-data/js/solver-info.js";
import { encodeFragment, decodeFragment, checkScenario } from "../../static/demo-data/js/codec.js";
import styles from "./demo.module.css";

const OWN = "#1f77b4";
const TGT = "#d62728";
const EST = "#2ca02c";
const BRG = "#bcbd22";
const AMBER = "#ff9800";
const FOUND = "#ff7f0e"; // spec 036: the leg splitter's manoeuvre spans
const W = 760, H = 520;
const NM = T.NM, KT = T.KT, DEG = T.DEG;
const OBS_COLOUR = { green: "#2ca02c", amber: AMBER, red: "#d62728" };

const fmt = (x, d = 1) => (Number.isFinite(x) ? x.toFixed(d) : x === Infinity ? "∞" : "–");
const fmtMin = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;

// 1-σ ellipse of the position block of a 4 × 4 covariance (row-major), metres
function ellipse(cov) {
  const a = cov[0], b = cov[1], d = cov[5];
  if (![a, b, d].every(Number.isFinite)) return null;
  const tr = (a + d) / 2;
  const det = Math.sqrt(Math.max(((a - d) / 2) ** 2 + b * b, 0));
  const l1 = tr + det, l2 = tr - det;
  if (!(l1 > 0 && l2 > 0)) return null;
  // angle of the major axis from +x (east), radians
  const ang = b === 0 ? (a >= d ? 0 : Math.PI / 2) : Math.atan2(l1 - a, b);
  return { rx: Math.sqrt(l1), ry: Math.sqrt(l2), ang };
}

function fitView(sc, w = W, h = H) {
  const pts = [];
  for (const tr of [sc.ownship, sc.target]) {
    pts.push(...T.waypoints(tr));
  }
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const [x, y] of pts) {
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  }
  const span = Math.max(x1 - x0, y1 - y0, 2) * 1.15;
  return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, ppn: Math.min(w, h) / span };
}

// the pixel size of an element (the plot and each chart draw at their box's own size, so text
// keeps its size and a hidden chart lets the others widen without growing taller)
function useSize(ref) {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver(([e]) => {
      const r = e.contentRect;
      setSize((s) => (Math.abs(s.w - r.width) < 1 && Math.abs(s.h - r.height) < 1 ? s : { w: Math.round(r.width), h: Math.round(r.height) }));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}
function ChartBox({ render }) {
  const ref = useRef(null);
  const { w, h } = useSize(ref);
  return <div ref={ref} className={styles.chartBox}>{w > 40 && h > 80 ? render(w, h) : null}</div>;
}

// ---------- small charts: time runs down the left, the value across (owner, 2026-11-21) ----------
// series points are [t, value]; bands [t, lo, hi]; marks [t0, t1, colour] shade time spans.
const CW = 330;
function Chart({ title, xDomain, yLabel, series, bands = [], marks = [], height = 440, testid, yClip = null, width = CW }) {
  const PADL = 44, PADR = 10, PADT = 40, PADB = 10;
  const vs = [];
  for (const s of series) for (const p of s.points) if (Number.isFinite(p[1])) vs.push(p[1]);
  for (const b of bands) for (const p of b.points) if (Number.isFinite(p[1]) && Number.isFinite(p[2])) vs.push(p[1], p[2]);
  let v0 = vs.length ? Math.min(...vs) : -1, v1 = vs.length ? Math.max(...vs) : 1;
  if (yClip) {
    v0 = Math.max(v0, yClip[0]);
    v1 = Math.min(v1, yClip[1]);
  }
  if (v1 - v0 < 1e-9) { v0 -= 1; v1 += 1; }
  const pad = (v1 - v0) * 0.05;
  v0 -= pad; v1 += pad;
  const [ta, tb] = xDomain;
  const sy = (t) => PADT + ((t - ta) / (tb - ta || 1)) * (height - PADT - PADB);
  const sx = (v) => PADL + ((Math.min(Math.max(v, v0), v1) - v0) / (v1 - v0)) * (width - PADL - PADR);
  const path = (pts) => pts.filter((p) => Number.isFinite(p[1])).map((p, i) => `${i ? "L" : "M"}${sx(p[1]).toFixed(1)},${sy(p[0]).toFixed(1)}`).join("");
  const ticksV = width < 260 ? [v0 + pad, v1 - pad] : [v0 + pad, (v0 + v1) / 2, v1 - pad];
  const nt = 8;
  const lab = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : Number(v.toPrecision(3)).toString());
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height} className={styles.chart} data-testid={testid} role="img" aria-label={title}>
      <text x={4} y={12} fontSize={11} fill="currentColor">{title}</text>
      <text x={PADL} y={PADT - 16} fontSize={10} fill="currentColor"><title>{yLabel}</title>{yLabel.length * 5.5 > width - PADL ? yLabel.slice(0, Math.max(4, Math.floor((width - PADL) / 5.5) - 1)) + "…" : yLabel}</text>
      <rect x={PADL} y={PADT} width={width - PADL - PADR} height={height - PADT - PADB} fill="none" stroke="currentColor" strokeOpacity={0.2} />
      {marks.map((m, i) => (
        // m[3]: "left" or "right" draws a solid strip at that edge (a detection) instead of shading
        m[3] ? (
          <rect key={i} x={m[3] === "left" ? PADL : width - PADR - 7} y={sy(m[0])} height={Math.max(sy(m[1]) - sy(m[0]), 2)} width={7} fill={m[2] || "#888"} fillOpacity={0.85} />
        ) : (
          <rect key={i} x={PADL} y={sy(m[0])} height={Math.max(sy(m[1]) - sy(m[0]), 1)} width={width - PADL - PADR} fill={m[2] || "#888"} fillOpacity={0.12} />
        )
      ))}
      {v0 < 0 && v1 > 0 && <line y1={PADT} y2={height - PADB} x1={sx(0)} x2={sx(0)} stroke="currentColor" strokeOpacity={0.35} />}
      {bands.map((b, i) => {
        const ok = b.points.filter((p) => Number.isFinite(p[1]) && Number.isFinite(p[2]));
        if (!ok.length) return null;
        const d = ok.map((p, k) => `${k ? "L" : "M"}${sx(p[2]).toFixed(1)},${sy(p[0]).toFixed(1)}`).join("") + ok.slice().reverse().map((p) => `L${sx(p[1]).toFixed(1)},${sy(p[0]).toFixed(1)}`).join("") + "Z";
        return <path key={i} d={d} fill={b.colour} fillOpacity={0.18} stroke="none" />;
      })}
      {series.map((s, i) =>
        s.dots ? (
          <g key={i}>{s.points.filter((p) => Number.isFinite(p[1])).map((p, k) => <circle key={k} cy={sy(p[0])} cx={sx(p[1])} r={1.3} fill={(s.colourAt && s.colourAt(p)) || s.colour} />)}</g>
        ) : (
          <path key={i} d={path(s.points)} fill="none" stroke={s.colour} strokeWidth={s.width || 1.5} strokeDasharray={s.dash} />
        )
      )}
      {ticksV.map((v, i) => (
        <text key={i} x={sx(v)} y={PADT - 4} fontSize={10} textAnchor="middle" fill="currentColor">{lab(v)}</text>
      ))}
      {Array.from({ length: nt + 1 }, (_, i) => ta + ((tb - ta) * i) / nt).map((t, i) => (
        <text key={i} x={PADL - 4} y={sy(t) + 3} fontSize={10} textAnchor="end" fill="currentColor">{`${Math.round(t / 60)} min`}</text>
      ))}
    </svg>
  );
}

// ---------- solve progress ----------
// E reports stages (spec 021's pipeline); its confirmation and estimates carry counts. The
// weights are rough shares of its run time on a two-hour window (search about 1%, confirmation
// about 75%, estimates about 17%), so the bar moves about evenly.
const STAGE_SPAN = { "least squares": [0, 0.01], "GLR statistic": [0.01, 0.02], "ownship legs (O)": [0.02, 0.025], "E-s evidence": [0.025, 0.03], search: [0.03, 0.08], confirmation: [0.08, 0.83], estimates: [0.83, 1], done: [1, 1] };
function progressFraction(p) {
  if (p && p.stage === "C: confirmation" && p.nominations > 0) return 0.1 + 0.85 * (p.decided / p.nominations);
  if (!p || !p.stage || !STAGE_SPAN[p.stage]) return null;
  const [a, b] = STAGE_SPAN[p.stage];
  let f = 0;
  if (p.stage === "confirmation" && p.nominations > 0) f = p.decided / p.nominations;
  else if (p.stage === "estimates" && p.of > 0) f = p.done / p.of;
  return a + (b - a) * f;
}
function progressStage(p) {
  if (!p || !p.stage) return "";
  if (p.note) return p.note;
  if ((p.stage === "confirmation" || p.stage === "C: confirmation") && p.nominations) return `${p.stage}: ${p.decided} of ${p.nominations} nominations`;
  if (p.stage === "estimates" && p.of) return `estimates: ${p.done} of ${p.of} rows`;
  return p.stage;
}
function ProgressBar({ fraction, stage, seconds, onCancel }) {
  const det = fraction !== null && fraction !== undefined;
  return (
    <div data-testid="solve-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={det ? Math.round(100 * fraction) : undefined} aria-label="Solver progress">
      <div className={styles.bar}>
        <div className={det ? styles.barFill : styles.barIndet} style={det ? { width: `${(100 * fraction).toFixed(1)}%` } : undefined} />
      </div>
      <div className={styles.small}>
        Solving{det ? ` ${Math.round(100 * fraction)}%` : "…"}{stage ? `: ${stage}` : ""}; {seconds.toFixed(seconds < 10 ? 1 : 0)} s{" "}
        {seconds > 2 && <button className="button button--sm button--link" style={{ padding: 0 }} onClick={onCancel} data-testid="solve-cancel">cancel</button>}
      </div>
    </div>
  );
}

// ---------- the page ----------
function Demo() {
  const base = useBaseUrl("/demo-data/");
  const ownOrt = useBaseUrl("/ort/");
  const timelateUrl = useBaseUrl("/timelate");
  const cLayerUrl = useBaseUrl("/viewer-data/layer.onnx");
  const { siteConfig } = useDocusaurusContext();
  const ortBase = siteConfig.customFields.ortBase || ownOrt;

  const [schema, setSchema] = useState(null);
  const [hist, setHist] = useState({ past: [], sc: normaliseScenario(clone(DEFAULT_SCENARIO)), future: [] });
  const sc = hist.sc;
  const scRef = useRef(sc);
  scRef.current = sc;
  const [draft, setDraft] = useState(null); // a scenario while dragging (not solved)
  const [sel, setSel] = useState(null); // {vessel: "ownship"|"target", kind: "wp"|"leg", index}
  const plotBoxRef = useRef(null);
  const plotSize = useSize(plotBoxRef);
  const W = plotSize.w || 760, H = plotSize.h || 520; // the plot's own pixels
  const [view, setView] = useState(() => fitView(DEFAULT_SCENARIO));
  const [winDraft, setWinDraft] = useState(null);
  const [sigmaDraft, setSigmaDraft] = useState(null);
  const [solve, setSolve] = useState({ status: "idle" });
  const [now, setNow] = useState(0);
  const [nonce, setNonce] = useState(0); // "solve again" after a cancel
  const [quantity, setQuantity] = useState("position");
  const [kinQ, setKinQ] = useState("course"); // spec 036 follow-up: course, speed or both
  const [showCharts, setShowCharts] = useState({ error: true, bearings: true, residuals: true, kinematics: true });
  const [importErrors, setImportErrors] = useState(null);
  const [notice, setNotice] = useState(null);
  const [dragLabel, setDragLabel] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [tlInfo, setTlInfo] = useState(null);
  const [cmp, setCmp] = useState(null); // spec 036: {key, id, status, rows: {splitter: solution}, progress}

  const commit = useCallback((next) => {
    setHist((h) => (JSON.stringify(h.sc) === JSON.stringify(next) ? h : { past: [...h.past.slice(-99), h.sc], sc: next, future: [] }));
  }, []);
  const undo = useCallback(() => setHist((h) => (h.past.length ? { past: h.past.slice(0, -1), sc: h.past[h.past.length - 1], future: [h.sc, ...h.future] } : h)), []);
  const redo = useCallback(() => setHist((h) => (h.future.length ? { past: [...h.past, h.sc], sc: h.future[0], future: h.future.slice(1) } : h)), []);

  // ---- schema, the URL fragment and the worker ----
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const s = await (await fetch(base + "demo-scenario.schema.json")).json();
        if (!alive) return;
        setSchema(s);
        fetch(base + "tl-layer.json").then((r) => r.json()).then((j) => alive && setTlInfo(j)).catch(() => {});
        if (window.location.hash.length > 3) {
          try {
            const got = await decodeFragment(window.location.hash);
            const errs = got ? checkScenario(s, got) : ["no scenario in the link"];
            if (errs.length) setNotice(`The link's scenario was not loaded: ${errs.slice(0, 3).join("; ")}`);
            else {
              setHist({ past: [], sc: normaliseScenario(got), future: [] });
              setView(fitView(got, W, H));
            }
          } catch (e) {
            setNotice(`The link's scenario could not be read (${e.message}).`);
          }
        }
      } finally {
        if (alive) setLoaded(true);
      }
    })();
    return () => { alive = false; };
  }, [base]);

  const worker = useRef(null);
  const latest = useRef(-1);
  const latestCmp = useRef(-1);
  const nextId = useRef(0);
  useEffect(() => {
    const w = new Worker(base + "worker.js", { type: "module" });
    w.postMessage({
      type: "init",
      ortBase: new URL(ortBase, window.location.origin).href,
      models: {
        "tl-layer": new URL(base + "tl-layer.onnx", window.location.origin).href,
        "tlm-s1": new URL(base + "tlm-s1.onnx", window.location.origin).href,
        "tlm-s2": new URL(base + "tlm-s2.onnx", window.location.origin).href,
        "tlm-s3": new URL(base + "tlm-s3.onnx", window.location.origin).href,
        "c-layer": new URL(cLayerUrl, window.location.origin).href,
      },
    });
    w.onmessage = (ev) => {
      const m = ev.data;
      if (m.id !== undefined && m.id === latestCmp.current) {
        // spec 036: the comparison of leg splitters runs beside the solve
        if (m.type === "progress") setCmp((c) => (c ? { ...c, progress: m } : c));
        else if (m.type === "compared-one") setCmp((c) => (c ? { ...c, rows: { ...c.rows, [m.splitter]: m.solution } } : c));
        else if (m.type === "compared") setCmp((c) => (c ? { ...c, status: "done", progress: null } : c));
        else if (m.type === "error") setCmp((c) => (c ? { ...c, status: "error", error: m.message } : c));
        return;
      }
      if (m.id === undefined || m.id !== latest.current) return; // a stale result: discarded (FR-023)
      // a graph-loading note keeps the last stage's place on the bar
      if (m.type === "progress") setSolve((s) => ({ ...s, progress: m.stage.startsWith("loading") && s.progress ? { ...s.progress, note: m.stage } : m }));
      else if (m.type === "solved") setSolve((s) => ({ ...s, status: "done", solution: m.solution }));
      else if (m.type === "error") setSolve((s) => ({ ...s, status: "error", error: m.message }));
    };
    w.onerror = (e) => setSolve({ status: "error", error: e.message || "worker failed" });
    worker.current = w;
    return () => w.terminate();
  }, [base, ortBase, cLayerUrl]);

  // ---- derived from the committed scenario ----
  const derived = useMemo(() => {
    const b = bearings(sc);
    const rows = windowRows(sc, b);
    if (rows.length < 4) return { b, rows, problem: null };
    const { problem, origin, t0 } = problemOf(sc, b, rows);
    const kn = targetManoeuvresIn(sc, b);
    const obs = observability(sc, b, rows, kn);
    return { b, rows, problem, origin, t0, kn, obs, ownTurns: ownTurnsIn(sc, b) };
  }, [sc]);
  const info = SOLVER_LIST.find((s) => s.name === sc.solver) || SOLVER_LIST[0];
  const splitterName = sc.splitter || "none";
  const sInfo = SPLITTER_LIST.find((x) => x.name === splitterName) || SPLITTER_LIST[0];
  // the splitter is part of the solve only for a solver that accepts knots
  const key = useMemo(() => JSON.stringify(info.accepts_knots ? sc : { ...sc, splitter: undefined }), [sc, info.accepts_knots]);
  // the comparison depends on everything but the chosen solver and splitter
  const cmpKey = useMemo(() => JSON.stringify({ ...sc, solver: undefined, splitter: undefined, show_ellipses: undefined }), [sc]);

  // FR-022: recompute on every committed change (drag release, slider release, sigma, reseed, solver)
  useEffect(() => {
    if (!worker.current || !loaded) return;
    if (latest.current >= 0) worker.current.postMessage({ type: "cancel", id: latest.current });
    if (!derived.problem) {
      latest.current = -1;
      setSolve({ status: "error", error: "fewer than four bearings in the window", key });
      return;
    }
    const id = nextId.current++;
    latest.current = id;
    setSolve({ status: "solving", key, id, t0: performance.now() });
    worker.current.postMessage({ type: "solve", id, solver: sc.solver, splitter: splitterName, problem: derived.problem });
  }, [key, loaded, derived, sc.solver, splitterName, nonce]);

  // spec 036: run every leg splitter through the physics layer on this window
  const startCompare = (only = null) => {
    if (!worker.current || !derived.problem) return;
    if (latestCmp.current >= 0) worker.current.postMessage({ type: "cancel", id: latestCmp.current });
    const id = nextId.current++;
    latestCmp.current = id;
    const names = only || SPLITTER_LIST.map((x) => x.name);
    setCmp({ key: cmpKey, id, status: "running", rows: {}, names, t0: performance.now() });
    worker.current.postMessage({ type: "compare", id, solver: "layer", splitters: names, problem: derived.problem });
  };
  const cancelCompare = () => {
    if (worker.current && latestCmp.current >= 0) worker.current.postMessage({ type: "cancel", id: latestCmp.current });
    latestCmp.current = -1;
    setCmp((c) => (c ? { ...c, status: "cancelled" } : c));
  };
  // a changed scenario makes a comparison stale: stop it
  useEffect(() => {
    if (cmp && cmp.key !== cmpKey && cmp.status === "running") cancelCompare();
  }, [cmpKey]);

  // progress: an elapsed clock while a solve runs
  useEffect(() => {
    if (solve.status !== "solving" && !(cmp && cmp.status === "running")) return undefined;
    const h = setInterval(() => setNow(performance.now()), 250);
    return () => clearInterval(h);
  }, [solve.status, cmp && cmp.status]);
  const cancelSolve = () => {
    if (worker.current && latest.current >= 0) worker.current.postMessage({ type: "cancel", id: latest.current });
    latest.current = -1;
    setSolve((s) => ({ ...s, status: "cancelled" }));
  };

  // FR-042: the scenario in the URL fragment
  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    encodeFragment(sc).then((f) => alive && window.history.replaceState(null, "", "#" + f));
    return () => { alive = false; };
  }, [key, loaded]);

  const ev = useMemo(() => {
    if (solve.status !== "done" || solve.key !== key || !derived.problem) return null;
    return evaluate(sc, derived.b, derived.rows, derived.origin, derived.t0, solve.solution, derived.kn);
  }, [solve, key, derived]);

  // ---- plot geometry ----
  const shown = draft || sc;
  const paths = useMemo(() => ({ ownship: T.buildPath(shown.ownship), target: T.buildPath(shown.target) }), [shown]);
  const sx = (x) => W / 2 + (x - view.cx) * view.ppn;
  const sy = (y) => H / 2 - (y - view.cy) * view.ppn;
  const toWorld = (px, py) => [view.cx + (px - W / 2) / view.ppn, view.cy - (py - H / 2) / view.ppn];
  const clampPx = (v) => Math.max(-1e5, Math.min(1e5, v));
  const poly = (pts) => pts.map(([x, y], i) => `${i ? "L" : "M"}${clampPx(sx(x / NM)).toFixed(1)},${clampPx(sy(y / NM)).toFixed(1)}`).join("");

  // refit when the plot's box is first measured or resized
  useEffect(() => {
    if (plotSize.w) setView(fitView(scRef.current, plotSize.w, plotSize.h));
  }, [plotSize.w, plotSize.h]);
  const svgRef = useRef(null);
  const drag = useRef(null);
  const toSvg = (e) => {
    const r = svgRef.current.getBoundingClientRect();
    return [((e.clientX - r.left) * W) / r.width, ((e.clientY - r.top) * H) / r.height];
  };

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return undefined;
    const onWheel = (e) => {
      e.preventDefault();
      const [px, py] = toSvg(e);
      const f = Math.exp(-(e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY) * 0.0015);
      setView((v) => {
        const wx = v.cx + (px - W / 2) / v.ppn, wy = v.cy - (py - H / 2) / v.ppn;
        const ppn = Math.min(Math.max(v.ppn * f, 0.2), 5000);
        return { ppn, cx: wx - (px - W / 2) / ppn, cy: wy + (py - H / 2) / ppn };
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  });

  const onPointerDown = (e) => {
    if (e.button !== 0) return;
    const t = e.target;
    const kind = t.getAttribute("data-kind");
    const vessel = t.getAttribute("data-vessel");
    const index = Number(t.getAttribute("data-index"));
    const p = toSvg(e);
    svgRef.current.setPointerCapture(e.pointerId);
    // spec 036 follow-up: ctrl-click (cmd-click) deletes a waypoint (not the start or the end)
    if (kind === "wp" && (e.ctrlKey || e.metaKey)) {
      const tr = sc[vessel];
      if (index >= 1 && index < tr.legs.length) {
        commit({ ...sc, [vessel]: T.deleteWaypoint(tr, index) });
        setSel(null);
      }
      return;
    }
    if (kind === "wp" || kind === "handle" || kind === "leg") {
      drag.current = { kind, vessel, index, p0: p, moved: false };
      if (kind !== "leg") setSel({ vessel, kind: kind === "wp" ? "wp" : "leg", index });
    } else {
      drag.current = { kind: "pan", p0: p, cx: view.cx, cy: view.cy, moved: false };
    }
  };
  const onPointerMove = (e) => {
    const d = drag.current;
    if (!d) return;
    const p = toSvg(e);
    if (Math.hypot(p[0] - d.p0[0], p[1] - d.p0[1]) > 3) d.moved = true;
    if (!d.moved) return;
    if (d.kind === "pan" || d.kind === "leg") {
      if (d.kind === "leg") { d.kind = "pan"; d.cx = view.cx; d.cy = view.cy; }
      setView((v) => ({ ...v, cx: d.cx - (p[0] - d.p0[0]) / v.ppn, cy: d.cy + (p[1] - d.p0[1]) / v.ppn }));
      return;
    }
    const [wx, wy] = toWorld(p[0], p[1]);
    const tr = sc[d.vessel];
    let next = tr;
    if (d.kind === "wp") {
      // spec 036 follow-up: a waypoint drag keeps the adjacent legs' speeds, so their durations change
      next = T.moveWaypoint(tr, d.index, wx, wy, "speed");
      if (d.index === 0) {
        // the start point moves the whole track
        next = { ...tr, start_x_nm: wx, start_y_nm: wy };
        setDragLabel(null);
      } else {
        const legs = [d.index - 1, d.index].filter((i) => i < next.legs.length);
        setDragLabel({ x: p[0], y: p[1], text: legs.map((i) => `${fmt(next.legs[i].duration_s / 60, 1)} min`).join(" | ") });
      }
    } else if (d.kind === "handle") {
      const v = T.velocityFromHandle(tr, d.index, wx, wy);
      next = T.setLegVelocity(tr, d.index, v.course_deg, Math.min(v.speed_kt, 40));
      setDragLabel({ x: p[0], y: p[1], text: `${fmt(next.legs[d.index].speed_kt, 1)} kt, ${fmt(next.legs[d.index].course_deg, 0)}°` });
    }
    setDraft({ ...sc, [d.vessel]: next });
  };
  const onPointerUp = (e) => {
    const d = drag.current;
    drag.current = null;
    setDragLabel(null);
    if (!d) return;
    if (d.kind === "leg" && !d.moved) {
      // FR-004: a click on a leg inserts a waypoint there
      const [wx, wy] = toWorld(...toSvg(e));
      const tr = sc[d.vessel];
      const near = T.nearestOnLegs(tr, wx, wy);
      if (near && near.f > 0.02 && near.f < 0.98) {
        commit({ ...sc, [d.vessel]: T.insertWaypoint(tr, near.leg, near.f) });
        setSel({ vessel: d.vessel, kind: "wp", index: near.leg + 1 });
      }
      return;
    }
    if (d.kind === "pan" && !d.moved) setSel(null);
    if (draft) {
      commit(draft);
      setDraft(null);
    }
  };

  const deleteSelected = useCallback(() => {
    if (!sel || sel.kind !== "wp") return;
    const tr = sc[sel.vessel];
    if (sel.index < 1 || sel.index >= tr.legs.length) return;
    commit({ ...sc, [sel.vessel]: T.deleteWaypoint(tr, sel.index) });
    setSel(null);
  }, [sel, sc, commit]);

  useEffect(() => {
    const onKey = (e) => {
      const tag = (e.target && e.target.tagName) || "";
      if (["INPUT", "SELECT", "TEXTAREA"].includes(tag)) return;
      if ((e.key === "Delete" || e.key === "Backspace") && sel) {
        e.preventDefault();
        deleteSelected();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        redo();
      } else if (e.key === "Escape") setSel(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sel, deleteSelected, undo, redo]);

  // ---- window and sigma sliders: commit on release (the native change event) ----
  const startRef = useRef(null), endRef = useRef(null), sigmaRef = useRef(null);
  const period = derived.b.period;
  const win = winDraft || sc.window;
  const winRef = useRef(win);
  winRef.current = win;
  useEffect(() => {
    const onChange = () => {
      const w = winRef.current;
      setWinDraft(null);
      commit({ ...scRef.current, window: { start_s: w.start_s, end_s: w.end_s } });
    };
    const onSigma = (e) => {
      setSigmaDraft(null);
      commit({ ...scRef.current, sigma_deg: Number(e.target.value) });
    };
    const els = [startRef.current, endRef.current];
    els.forEach((el) => el && el.addEventListener("change", onChange));
    if (sigmaRef.current) sigmaRef.current.addEventListener("change", onSigma);
    return () => {
      els.forEach((el) => el && el.removeEventListener("change", onChange));
      if (sigmaRef.current) sigmaRef.current.removeEventListener("change", onSigma);
    };
  }, [commit, loaded]);
  const dtWin = Math.max(sc.interval_s, 5);
  const setWinEnd = (which, v) => {
    const w = { ...winRef.current };
    if (which === "start") w.start_s = Math.min(v, w.end_s - 4 * sc.interval_s);
    else w.end_s = Math.max(v, w.start_s + 4 * sc.interval_s);
    w.start_s = Math.max(0, w.start_s);
    w.end_s = Math.min(w.end_s, Math.ceil(period / dtWin) * dtWin);
    winRef.current = w;
    setWinDraft(w);
  };

  // ---- import / export ----
  const fileRef = useRef(null);
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(sc, null, 2) + "\n"], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `demo-scenario-${(sc.name || "scenario").toLowerCase().replace(/[^a-z0-9]+/g, "-")}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  const importText = useCallback((text) => {
    let obj;
    try {
      obj = JSON.parse(text);
    } catch (e) {
      setImportErrors([`not JSON: ${e.message}`]);
      return false;
    }
    const errs = schema ? checkScenario(schema, obj) : ["the schema has not loaded yet"];
    if (errs.length) {
      setImportErrors(errs);
      return false;
    }
    setImportErrors(null);
    commit(normaliseScenario(obj));
    setView(fitView(obj, W, H));
    return true;
  }, [schema, commit]);
  const onFile = async (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) importText(await f.text());
    e.target.value = "";
  };

  const loadPreset = (id) => {
    const p = PRESETS.find((q) => q.id === id);
    if (!p) return;
    // a preset that names a splitter (spec 036) brings its solver too
    const next = normaliseScenario({ ...clone(p.scenario), solver: p.scenario.splitter ? p.scenario.solver : sc.solver, splitter: p.scenario.splitter || sc.splitter, show_ellipses: sc.show_ellipses });
    commit(next);
    setView(fitView(next, W, H));
    setSel(null);
  };

  // ---- test hooks (the Playwright check drives the page through these) ----
  const hooks = useRef({});
  hooks.current = {
    scenario: () => sc,
    status: () => solve.status,
    solution: () => (solve.key === key ? solve.solution : null),
    summary: () => (ev ? ev.summary : null),
    observability: () => derived.obs,
    mismatch: () => !!(oneLeg && derived.kn && derived.kn.length),
    set: (next) => { const n = normaliseScenario(next); commit(n); setView(fitView(n, W, H)); },
    legs: () => legs,
    compare: () => cmp,
    startCompare: (only) => startCompare(only || null),
    importText,
    fragment: () => window.location.hash,
  };
  useEffect(() => {
    window.__demo = {};
    for (const k of Object.keys(hooks.current)) window.__demo[k] = (...a) => hooks.current[k](...a);
  }, []);

  // ---- render pieces ----
  const b = derived.b;
  const inWin = (t) => t >= win.start_s - 1e-9 && t <= win.end_s + 1e-9;
  const step = Math.max(1, Math.ceil(b.n / 48));
  const bearingLines = [];
  for (let i = 0; i < b.n; i += step) {
    const r = Math.hypot(b.tx[i] - b.ox[i], b.ty[i] - b.oy[i]) * 1.15;
    const x1 = b.ox[i] + r * Math.sin(b.z[i]), y1 = b.oy[i] + r * Math.cos(b.z[i]);
    bearingLines.push(<line key={i} x1={sx(b.ox[i] / NM)} y1={sy(b.oy[i] / NM)} x2={sx(x1 / NM)} y2={sy(y1 / NM)} stroke={inWin(b.t[i]) ? BRG : "#999"} strokeOpacity={inWin(b.t[i]) ? 0.55 : 0.25} strokeWidth={0.8} />);
  }
  const windowPart = (path) => T.pathPointsBetween(path, Math.max(0, win.start_s), Math.min(win.end_s, path.end));


  const vesselLayer = (name, colour) => {
    const tr = shown[name];
    const path = paths[name];
    const Wp = T.waypoints(tr);
    const amber = new Set(path.joins.filter((J) => J.clamped).map((J) => J.j));
    const isSel = (k, i) => sel && sel.vessel === name && sel.kind === k && sel.index === i;
    return (
      <g key={name}>
        <path d={poly(T.pathPoints(path))} fill="none" stroke={colour} strokeWidth={1.2} strokeOpacity={0.6} />
        {(() => {
          // spec 036 follow-up: an arrowhead at the track's end, along its final course
          const end = T.stateAt(path, path.end);
          const X = clampPx(sx(end.x / NM)), Y = clampPx(sy(end.y / NM));
          const sp = Math.hypot(end.vx, end.vy);
          if (!(sp > 0)) return null;
          const ux = end.vx / sp, uy = -end.vy / sp; // screen y runs down
          // beyond the end waypoint's circle, so the circle does not hide it
          const L = 12, Wd = 6, off = 9;
          const base = [X + ux * off, Y + uy * off], tip = [X + ux * (off + L), Y + uy * (off + L)];
          const pts = [tip, [base[0] - uy * Wd, base[1] + ux * Wd], [base[0] + uy * Wd, base[1] - ux * Wd]];
          return <polygon data-testid={`arrow-${name}`} points={pts.map((q) => q.map((v) => v.toFixed(1)).join(",")).join(" ")} fill={colour} pointerEvents="none"><title>{`${name === "ownship" ? "Ownship" : "Target"} heading ${fmt(((Math.atan2(end.vx, end.vy) / DEG) + 360) % 360, 0)}° at the end of the scenario`}</title></polygon>;
        })()}
        <path d={poly(windowPart(path))} fill="none" stroke={colour} strokeWidth={3} />
        {/* faint polyline between waypoints: click to insert a waypoint (FR-004) */}
        {Wp.slice(0, -1).map((w, i) => (
          <line key={`leg${i}`} data-kind="leg" data-vessel={name} data-index={i} x1={sx(w[0])} y1={sy(w[1])} x2={sx(Wp[i + 1][0])} y2={sy(Wp[i + 1][1])} stroke="transparent" strokeWidth={12} style={{ cursor: "copy" }}>
            <title>Click to insert a waypoint</title>
          </line>
        ))}
        {tr.legs.map((l, i) => {
          const [hx, hy] = T.handleOf(tr, i);
          return (
            <rect key={`h${i}`} data-kind="handle" data-vessel={name} data-index={i} data-testid={`handle-${name}-${i}`} x={sx(hx) - 5} y={sy(hy) - 5} width={10} height={10} fill="#fff" stroke={colour} strokeWidth={isSel("leg", i) ? 3 : 1.5} style={{ cursor: "grab" }}>
              <title>{`Leg ${i + 1}: ${fmt(l.course_deg, 0)}°, ${fmt(l.speed_kt, 1)} kt, ${fmt(l.duration_s / 60, 1)} min. Drag to change course and speed; the rest of the track swings with it.`}</title>
            </rect>
          );
        })}
        {tr.legs.map((l, i) => {
          // the leg's speed, beside its middle on the side away from the handle's drag line
          const [ax, ay] = Wp[i], [bx, by] = Wp[i + 1];
          const dx = sx(bx) - sx(ax), dy = sy(by) - sy(ay);
          const len = Math.hypot(dx, dy) || 1;
          const nx = -dy / len, ny = dx / len;
          const mx = (sx(ax) + sx(bx)) / 2 + nx * 12, my = (sy(ay) + sy(by)) / 2 + ny * 12;
          const anchor = nx > 0.3 ? "start" : nx < -0.3 ? "end" : "middle";
          if (len < 40) return null;
          return (
            <text key={`s${i}`} x={mx} y={my + (ny > 0.3 ? 10 : ny < -0.3 ? -2 : 4)} fontSize={11} textAnchor={anchor} fill={colour} pointerEvents="none" data-testid={`speed-${name}-${i}`} style={{ paintOrder: "stroke", stroke: "var(--ifm-background-color)", strokeWidth: 3 }}>
              {`${fmt(l.speed_kt, 1)} kt`}
            </text>
          );
        })}
        {Wp.map((w, i) => (
          <circle key={`w${i}`} data-kind="wp" data-vessel={name} data-index={i} data-testid={`wp-${name}-${i}`} cx={sx(w[0])} cy={sy(w[1])} r={i === 0 ? 7 : 5.5} fill={amber.has(i) ? AMBER : i === 0 ? colour : "#fff"} stroke={colour} strokeWidth={isSel("wp", i) ? 3.5 : 1.5} style={{ cursor: "move" }}>
            <title>{i === 0 ? "Start: drag to move the whole track" : `Waypoint ${i}: drag to move it alone${amber.has(i) ? " (turn clamped: the arc does not fit at this rate)" : ""}; select and press Delete to remove`}</title>
          </circle>
        ))}
      </g>
    );
  };

  let estimate = null;
  if (ev && ev.ex.length) {
    const pts = ev.ex.map((x, k) => [x, ev.ey[k]]);
    const last = pts[pts.length - 1];
    let ell = null;
    if (sc.show_ellipses && solve.solution.cov_end && !info.learned) {
      const e1 = ellipse(solve.solution.cov_end);
      if (e1) {
        const cx = sx(last[0] / NM), cy = sy(last[1] / NM);
        ell = [1, 2].map((k) => (
          <ellipse key={k} cx={cx} cy={cy} rx={Math.min((k * e1.rx * view.ppn) / NM, 1e5)} ry={Math.min((k * e1.ry * view.ppn) / NM, 1e5)} transform={`rotate(${(-e1.ang * 180) / Math.PI} ${cx} ${cy})`} fill="none" stroke={EST} strokeDasharray={k === 2 ? "4 3" : undefined} />
        ));
      }
    }
    estimate = (
      <g data-testid="estimate">
        {info.time_late ? (
          <path d={poly(pts)} fill="none" stroke={EST} strokeWidth={2} strokeDasharray="6 3" />
        ) : (
          pts.map((p, k) => <circle key={k} cx={clampPx(sx(p[0] / NM))} cy={clampPx(sy(p[1] / NM))} r={2} fill={EST} />)
        )}
        <circle cx={clampPx(sx(last[0] / NM))} cy={clampPx(sy(last[1] / NM))} r={5} fill={EST} stroke="#fff" />
        {ell}
        {(solve.solution.splitter_spans || []).map((f, j) => {
          // spec 036: where the splitter put each manoeuvre, on the estimated track
          const tc = (f.start_s + f.end_s) / 2 + derived.t0;
          let k = 0;
          while (k < ev.t.length - 1 && ev.t[k] < tc) k++;
          const X = clampPx(sx(pts[k][0] / NM)), Y = clampPx(sy(pts[k][1] / NM));
          return <path key={`kn${j}`} data-testid="found-knot" d={`M${X},${Y - 6}L${X + 6},${Y}L${X},${Y + 6}L${X - 6},${Y}Z`} fill={FOUND} stroke="#fff" strokeWidth={1}><title>{`The splitter's manoeuvre ${j + 1}: ${fmtMin(f.start_s + derived.t0)}–${fmtMin(f.end_s + derived.t0)}`}</title></path>;
        })}
      </g>
    );
  }

  // scale bar
  const niceNm = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100].find((x) => x * view.ppn > 80) || 100;

  const s = ev ? ev.summary : null;
  const obs = derived.obs;
  // one leg: a single-leg solver, or the layer given no spans by its splitter
  const oneLeg = info.single_leg || (info.accepts_knots && splitterName === "none");
  const mismatch = oneLeg && derived.kn && derived.kn.length > 0;
  const sol = solve.key === key ? solve.solution : null;
  // spec 036: the splitter's spans in scenario time, and how they match the truth's
  const trueSpans = derived.problem ? derived.problem.knots : [];
  const found = sol && sol.splitter_spans ? sol.splitter_spans : null;
  const legs = found ? compareLegs(trueSpans, found) : null;
  const foundMarks = found && splitterName !== "truth" ? found.map((f) => [f.start_s + derived.t0, Math.max(f.end_s + derived.t0, f.start_s + derived.t0 + 20), FOUND]) : [];
  const trueMarks = derived.kn ? derived.kn.map((m) => [m.t0, m.t1, TGT]) : [];
  // the comparison's rows, evaluated once per result (the clock re-renders the page while it runs)
  const cmpRows = useMemo(() => {
    if (!cmp || cmp.key !== cmpKey) return [];
    return (cmp.names || []).map((name) => {
      const solx = cmp.rows[name];
      const lab = (SPLITTER_LIST.find((x) => x.name === name) || {}).label || name;
      if (!solx) return { name, lab };
      const e = derived.problem ? evaluate(sc, derived.b, derived.rows, derived.origin, derived.t0, solx, derived.kn) : null;
      const lg = solx.splitter_spans ? compareLegs(derived.problem.knots, solx.splitter_spans) : null;
      return { name, lab, solx, sum: e ? e.summary : null, lg };
    });
  }, [cmp && cmp.rows, cmp && cmp.key, cmpKey, derived]);

  // error-vs-time series
  const qdef = {
    position: { label: "position error (NM)", f: (k) => ev.position[k] / NM, band: null },
    range: { label: "range error (NM)", f: (k) => ev.range[k] / NM, band: "range", bs: 1 / NM },
    bearing: { label: "bearing error (°)", f: (k) => ev.bearing[k] / DEG, band: "bearing", bs: 1 / DEG },
    course: { label: "course error (°)", f: (k) => ev.course[k] / DEG, band: "course", bs: 1 / DEG },
    speed: { label: "speed error (kt)", f: (k) => ev.speed[k] / KT, band: "speed", bs: 1 / KT },
  };
  const q = qdef[quantity];
  const xDom = [sc.window.start_s, Math.min(sc.window.end_s, period)];
  // the learned model's own statement of where the target manoeuvred (probability over 0.5)
  const modelSpans = [];
  if (sol && sol.manoeuvre_prob) {
    let start = null;
    sol.manoeuvre_prob.forEach((pr, j) => {
      const t = sol.manoeuvre_t_s[j] + derived.t0;
      if (pr > 0.5 && start === null) start = j ? sol.manoeuvre_t_s[j - 1] + derived.t0 : derived.t0;
      if ((pr <= 0.5 || j === sol.manoeuvre_prob.length - 1) && start !== null) {
        modelSpans.push([start, t, "#9467bd"]);
        start = null;
      }
    });
  }
  let errChart = null;
  if (ev) {
    const pts = ev.t.map((t, k) => [t, q.f(k)]);
    const bands = [];
    if (q.band) {
      const tIdx = new Map(derived.rows.map((i, k) => [Math.round(b.t[i] * 1000), k]));
      const bp = ev.t.map((t) => {
        const k = tIdx.get(Math.round(t * 1000));
        const v = k === undefined ? NaN : ev.bound[q.band][k] * q.bs;
        return [t, -2 * v, 2 * v];
      });
      bands.push({ colour: "#888", points: bp });
    }
    const big = Math.max(...pts.map((p) => Math.abs(p[1])).filter(Number.isFinite), 1e-9);
    errChart = (w, h) => (
      <Chart width={w} height={h} testid="chart-error" title="" yLabel={`${q.label}${q.band ? "; grey ±2 × bound" : ""}${modelSpans.length ? "; purple: model's manoeuvres" : ""}${foundMarks.length ? "; orange: splitter's" : ""}`} xDomain={xDom} series={[{ points: pts, colour: EST, width: 1.8 }]} bands={bands} marks={[...trueMarks, ...modelSpans, ...foundMarks]} yClip={[-big, big]} />
    );
  }
  let brgChart = null;
  if (ev || derived.problem) {
    // bearings drawn around their circular mean, so a track across north does not jump 360°
    let cs = 0, cc = 0;
    for (let i = 0; i < b.n; i++) { cs += Math.sin(b.z[i]); cc += Math.cos(b.z[i]); }
    const mean = Math.atan2(cs, cc);
    const unwrap = (z) => (mean + Math.atan2(Math.sin(z - mean), Math.cos(z - mean))) / DEG;
    const meas = Array.from(b.t, (t, i) => [t, unwrap(b.z[i])]);
    const pred = ev ? ev.predicted.map(([t, z]) => [t, unwrap(z)]) : [];
    const res = ev ? ev.residual : [];
    brgChart = {
      bearings: (w, h) => <Chart width={w} height={h} testid="chart-bearings" title="Bearings" xDomain={[0, period]} yLabel="° (dots measured, line solution)" series={[{ points: meas, dots: true, colour: BRG, colourAt: (p) => (inWin(p[0]) ? "#8c8c00" : "#bbb") }, { points: pred, colour: EST, width: 1.5 }]} marks={[[win.start_s, win.end_s, "#2ca02c"], ...trueMarks, ...foundMarks]} />,
      residuals: (w, h) => <Chart width={w} height={h} testid="chart-residuals" title="Residuals" xDomain={[0, period]} yLabel="÷ σ (±2 dashed)" series={[{ points: res, dots: true, colour: EST }, { points: [[0, 2], [period, 2]], colour: "#888", dash: "3 3", width: 1 }, { points: [[0, -2], [period, -2]], colour: "#888", dash: "3 3", width: 1 }]} marks={[[win.start_s, win.end_s, "#2ca02c"], ...trueMarks, ...foundMarks]} yClip={[-8, 8]} />,
    };
  }

  // spec 036 follow-up: both vessels' course and speed over the scenario, with true and detected turns
  let kinChart = null;
  {
    const own = [], tgt = [];
    for (let i = 0; i < b.n; i++) {
      own.push([b.t[i], Math.atan2(b.ovx[i], b.ovy[i]), Math.hypot(b.ovx[i], b.ovy[i]) / KT]);
      tgt.push([b.t[i], Math.atan2(b.tvx[i], b.tvy[i]), Math.hypot(b.tvx[i], b.tvy[i]) / KT]);
    }
    const est = sol && sol.t_s && sol.status !== "failed" ? sol.t_s.map((t, k) => [t + derived.t0, Math.atan2(sol.vx_mps[k], sol.vy_mps[k]), Math.hypot(sol.vx_mps[k], sol.vy_mps[k]) / KT]) : [];
    // courses drawn around their circular mean, so a course across north does not jump 360°
    let cs = 0, cc = 0;
    for (const p of [...own, ...tgt]) { cs += Math.sin(p[1]); cc += Math.cos(p[1]); }
    const mean = Math.atan2(cs, cc);
    const unwrapC = (c) => (mean + Math.atan2(Math.sin(c - mean), Math.cos(c - mean))) / DEG;
    const trueTgt = T.manoeuvres(b.paths.tgt).map((m) => [m.t0, m.t1, TGT]);
    const trueOwn = T.manoeuvres(b.paths.own).map((m) => [m.t0, m.t1, OWN]);
    const detTgt = (sol && sol.splitter_spans && splitterName !== "truth" ? sol.splitter_spans : []).map((f) => [f.start_s + derived.t0, Math.max(f.end_s, f.start_s + 20) + derived.t0, FOUND, "right"]);
    const detOwn = (sol && sol.splitter_ownship_spans ? sol.splitter_ownship_spans : []).map((f) => [f.start_s + derived.t0, Math.max(f.end_s, f.start_s + 20) + derived.t0, "#17becf", "left"]);
    const modelStrips = modelSpans.map((m) => [m[0], m[1], m[2], "right"]);
    const marks = [[win.start_s, win.end_s, "#2ca02c"], ...trueOwn, ...trueTgt, ...detTgt, ...detOwn, ...modelStrips];
    const detected = detTgt.length || detOwn.length || modelStrips.length;
    const note = detected ? "; strips: detected" : "";
    kinChart = {
      course: (w, h) => <Chart width={w} height={h} testid="chart-course" title={kinQ === "both" ? "Course" : ""} xDomain={[0, period]} yLabel={`° (blue own, red target, green est.)${note}`} series={[{ points: own.map((p) => [p[0], unwrapC(p[1])]), colour: OWN }, { points: tgt.map((p) => [p[0], unwrapC(p[1])]), colour: TGT }, { points: est.map((p) => [p[0], unwrapC(p[1])]), colour: EST, dash: "4 3" }]} marks={marks} />,
      speed: (w, h) => <Chart width={w} height={h} testid="chart-speed" title={kinQ === "both" ? "Speed" : ""} xDomain={[0, period]} yLabel={`kt${note}`} series={[{ points: own.map((p) => [p[0], p[2]]), colour: OWN }, { points: tgt.map((p) => [p[0], p[2]]), colour: TGT }, { points: est.map((p) => [p[0], p[2]]), colour: EST, dash: "4 3" }]} marks={marks} yClip={[0, 40]} />,
    };
  }

  // spec 036 follow-up: the preset the scenario matches (the drop-down shows it; "custom" once edited)
  const presetShown = (() => {
    const pick = (x) => JSON.stringify([x.ownship, x.target, x.sigma_deg, x.interval_s, x.seed, x.window]);
    const k = pick(sc);
    const hit = PRESETS.find((pr) => pick(pr.scenario) === k);
    return hit ? hit.id : "custom";
  })();

  const selTrack = sel ? sc[sel.vessel] : null;
  const editor = sel && selTrack ? (
    <div className={styles.panel} data-testid="panel-edit">
      <h4>{sel.vessel === "ownship" ? "Ownship" : "Target"} {sel.kind === "wp" ? `waypoint ${sel.index}` : `leg ${sel.index + 1}`}</h4>
      {sel.kind === "wp" && sel.index >= 1 && sel.index < selTrack.legs.length && (
        <>
          <label>Turn rate (°/s, 0.25–3){" "}
            <input type="number" min={0.25} max={3} step={0.25} value={selTrack.legs[sel.index - 1].turn_rate_dps} data-testid="turn-rate" onChange={(e) => { const v = Number(e.target.value); if (v >= 0.25 && v <= 3) commit({ ...sc, [sel.vessel]: T.setTurnRate(selTrack, sel.index - 1, v) }); }} style={{ width: "5rem" }} />
          </label>
          <div className={styles.small}>Radius at {fmt(selTrack.legs[sel.index - 1].speed_kt, 1)} kt: {fmt((selTrack.legs[sel.index - 1].speed_kt * KT) / (selTrack.legs[sel.index - 1].turn_rate_dps * DEG) / NM, 2)} NM.</div>
          <button className="button button--sm button--outline button--danger margin-top--sm" onClick={deleteSelected} data-testid="delete-wp">Delete waypoint</button>
        </>
      )}
      {sel.kind === "wp" && sel.index === 0 && <div className={styles.small}>The start point: dragging it moves the whole track.</div>}
      {sel.kind === "wp" && sel.index === selTrack.legs.length && <div className={styles.small}>The track's end. Click on a leg to add a waypoint.</div>}
      {sel.kind === "leg" && (
        <table>
          <tbody>
            {[["course_deg", "Course (°)", 0, 360, 1], ["speed_kt", "Speed (kt)", 0, 40, 0.5], ["duration_s", "Duration (s)", 60, 43200, 60]].map(([f, label, mn, mx, st]) => (
              <tr key={f}>
                <td>{label}</td>
                <td>
                  <input type="number" min={mn} max={mx} step={st} defaultValue={Number(selTrack.legs[sel.index][f].toFixed(2))} key={`${key}-${f}`} style={{ width: "6rem" }}
                    onBlur={(e) => {
                      const v = Number(e.target.value);
                      if (!(v >= mn && v <= mx)) return;
                      const next = f === "course_deg" ? T.setLegVelocity(selTrack, sel.index, v, selTrack.legs[sel.index].speed_kt) : T.setLegField(selTrack, sel.index, f, v);
                      commit({ ...sc, [sel.vessel]: next });
                    }}
                    onKeyDown={(e) => e.key === "Enter" && e.target.blur()} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  ) : null;

  return (
    <div>
      {notice && <div className="alert alert--warning margin-bottom--sm">{notice}</div>}
      <div className={styles.toolbar}>
        <label>Preset{" "}
          <select data-testid="preset" value={presetShown} onChange={(e) => loadPreset(e.target.value)}>
            <option value="custom" disabled>custom (edited)</option>
            {PRESETS.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
          </select>
        </label>
        <span className={styles.solverBox}>
          <label title={info.accepts_knots ? sInfo.assumptions : "This TMA solver does not take legs from a splitter."}>Leg splitter{" "}
            <select data-testid="splitter" value={splitterName} disabled={!info.accepts_knots} onChange={(e) => commit({ ...sc, splitter: e.target.value })}>
              {SPLITTER_LIST.map((x) => <option key={x.name} value={x.name}>{x.label}</option>)}
            </select>
          </label>
          <span aria-hidden="true">→</span>
          <label title={info.assumptions}>TMA solver{" "}
            <select data-testid="solver" value={sc.solver} onChange={(e) => commit({ ...sc, solver: e.target.value })}>
              {SOLVER_LIST.map((x) => <option key={x.name} value={x.name}>{x.label}{x.accepts_knots ? " ← legs" : ""}</option>)}
            </select>
          </label>
        </span>
        <button className="button button--sm button--secondary" onClick={undo} disabled={!hist.past.length} title="Ctrl+Z">Undo</button>
        <button className="button button--sm button--secondary" onClick={redo} disabled={!hist.future.length} title="Ctrl+Y">Redo</button>
        <button className="button button--sm button--secondary" onClick={() => setView(fitView(sc, W, H))}>Fit view</button>
        <label><input type="checkbox" checked={!!sc.show_ellipses} onChange={(e) => commit({ ...sc, show_ellipses: e.target.checked })} /> 1σ/2σ ellipses</label>
        <button className="button button--sm button--outline button--primary" onClick={exportJson}>Export JSON</button>
        <button className="button button--sm button--outline button--primary" onClick={() => fileRef.current && fileRef.current.click()}>Import JSON</button>
        <input ref={fileRef} type="file" accept="application/json,.json" style={{ display: "none" }} onChange={onFile} data-testid="import-file" />
        <button className="button button--sm button--outline button--primary" onClick={() => navigator.clipboard && navigator.clipboard.writeText(window.location.href)}>Copy link</button>
      </div>
      {importErrors && (
        <div className="alert alert--danger margin-bottom--sm" data-testid="import-errors">
          The file was not loaded; it does not match the LinkML DemoScenario schema ({SCHEMA_VERSION}):
          <ul>{importErrors.slice(0, 8).map((e, i) => <li key={i}><code>{e}</code></li>)}</ul>
        </div>
      )}
      <div className={styles.app}>
        <div className={styles.plotCol}>
          <div ref={plotBoxRef} className={styles.plotBox}>
          <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className={styles.plot} width={W} height={H} data-testid="plot" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onContextMenu={(e) => {
            const t = e.target;
            if (t.getAttribute("data-kind") === "wp") {
              e.preventDefault();
              const vessel = t.getAttribute("data-vessel"), index = Number(t.getAttribute("data-index"));
              const tr = sc[vessel];
              if (index >= 1 && index < tr.legs.length) {
                commit({ ...sc, [vessel]: T.deleteWaypoint(tr, index) });
                setSel(null);
              }
            }
          }}>
            <rect x={0} y={0} width={W} height={H} fill="transparent" />
            {(() => {
              // a faint grid in NM from the scenario's origin, about ten lines across
              const stepNm = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100].find((x) => x * view.ppn >= W / 12) || 100;
              const [x0, y1] = toWorld(0, 0), [x1, y0] = toWorld(W, H);
              const lines = [];
              for (let x = Math.ceil(x0 / stepNm) * stepNm; x <= x1; x += stepNm) {
                lines.push(<line key={`gx${x.toFixed(3)}`} x1={sx(x)} x2={sx(x)} y1={0} y2={H} stroke="currentColor" strokeOpacity={Math.abs(x) < 1e-9 ? 0.18 : 0.07} />);
                lines.push(<text key={`tx${x.toFixed(3)}`} x={sx(x) + 2} y={H - 4} fontSize={9} fill="currentColor" fillOpacity={0.45}>{Number(x.toFixed(2))}</text>);
              }
              for (let y = Math.ceil(y0 / stepNm) * stepNm; y <= y1; y += stepNm) {
                lines.push(<line key={`gy${y.toFixed(3)}`} x1={0} x2={W} y1={sy(y)} y2={sy(y)} stroke="currentColor" strokeOpacity={Math.abs(y) < 1e-9 ? 0.18 : 0.07} />);
                lines.push(<text key={`ty${y.toFixed(3)}`} x={3} y={sy(y) - 2} fontSize={9} fill="currentColor" fillOpacity={0.45}>{Number(y.toFixed(2))}</text>);
              }
              return <g pointerEvents="none" data-testid="grid">{lines}<text x={W - 4} y={46} fontSize={10} textAnchor="end" fill="currentColor" fillOpacity={0.6}>grid {stepNm} NM</text></g>;
            })()}
            <g>{bearingLines}</g>
            {vesselLayer("target", TGT)}
            {vesselLayer("ownship", OWN)}
            {estimate}
            {solve.status === "solving" && (
              <g pointerEvents="none" data-testid="plot-solving">
                <rect x={W - 210} y={26} width={200} height={20} rx={4} fill="var(--ifm-background-color)" stroke="currentColor" strokeOpacity={0.3} />
                <rect x={W - 206} y={40} width={192 * (progressFraction(solve.progress) ?? ((((now || 0) / 1000) % 1.5) / 1.5))} height={3} fill={EST} />
                <text x={W - 204} y={37} fontSize={11} fill="currentColor">Solving{progressFraction(solve.progress) !== null ? ` ${Math.round(100 * progressFraction(solve.progress))}%` : "…"} · {Math.max(0, ((now || performance.now()) - solve.t0) / 1000).toFixed(0)} s</text>
              </g>
            )}
            {dragLabel && (
              <g pointerEvents="none">
                <rect x={dragLabel.x + 10} y={dragLabel.y - 24} width={120} height={18} fill="var(--ifm-background-color)" stroke="currentColor" strokeOpacity={0.4} rx={3} />
                <text x={dragLabel.x + 16} y={dragLabel.y - 11} fontSize={12} fill="currentColor">{dragLabel.text}</text>
              </g>
            )}
            <g pointerEvents="none">
              <line x1={W - 20 - niceNm * view.ppn} x2={W - 20} y1={H - 18} y2={H - 18} stroke="currentColor" strokeWidth={2} />
              <text x={W - 20} y={H - 24} fontSize={11} textAnchor="end" fill="currentColor">{niceNm} NM</text>
              <text x={8} y={30} fontSize={11} fill="currentColor" fillOpacity={0.75}>click a leg to add a waypoint · drag a circle: speed kept, time changes · drag a square: time kept, speed changes · ctrl-click a circle to delete</text>
              <text x={8} y={16} fontSize={11} fill="currentColor">north up; blue ownship, red target (thick: inside the window); green dashed: the solution; olive: bearings</text>
            </g>
          </svg>
          </div>
          <div className="margin-top--sm" data-testid="window-slider">
            <div className={styles.small}>
              Analysis window {fmtMin(win.start_s)} – {fmtMin(Math.min(win.end_s, period))} of {fmtMin(period)} (min:s); {derived.rows.length} bearings go to the solver. Drag either end; the solve runs on release.
            </div>
            <div className={styles.dual}>
              <div className={styles.track}>
                <div className={styles.trackOn} style={{ left: `${(100 * win.start_s) / period}%`, width: `${(100 * (Math.min(win.end_s, period) - win.start_s)) / period}%` }} />
              </div>
              <input ref={startRef} type="range" min={0} max={Math.ceil(period / dtWin) * dtWin} step={dtWin} value={win.start_s} aria-label="Window start (s)" data-testid="win-start" onChange={(e) => setWinEnd("start", Number(e.target.value))} />
              <input ref={endRef} type="range" min={0} max={Math.ceil(period / dtWin) * dtWin} step={dtWin} value={Math.min(win.end_s, Math.ceil(period / dtWin) * dtWin)} aria-label="Window end (s)" data-testid="win-end" onChange={(e) => setWinEnd("end", Number(e.target.value))} />
            </div>
          </div>
          <div className={styles.toolbar}>
            <label>Bearing noise σ {fmt(sigmaDraft ?? sc.sigma_deg, 2)}°{" "}
              <input ref={sigmaRef} type="range" min={0} max={5} step={0.05} value={sigmaDraft ?? sc.sigma_deg} data-testid="sigma" onChange={(e) => setSigmaDraft(Number(e.target.value))} />
            </label>
            <button className="button button--sm button--secondary" data-testid="reseed" onClick={() => commit({ ...sc, seed: Math.floor(Math.random() * 4294967296) })}>Reseed</button>
            <span className={styles.small}>seed {sc.seed}</span>
            <label>Interval (s){" "}
              <input type="number" min={1} max={120} step={1} defaultValue={sc.interval_s} key={`iv-${sc.interval_s}`} style={{ width: "4.5rem" }} onBlur={(e) => { const v = Number(e.target.value); if (v >= 1 && v <= 120) commit({ ...sc, interval_s: v }); }} onKeyDown={(e) => e.key === "Enter" && e.target.blur()} />
            </label>
          </div>
        </div>
        <div className={styles.chartsCol}>
          <div className={styles.toolbar} data-testid="chart-toggles">
            <b>Charts</b> (time runs down):
            {[["error", "error vs time"], ["bearings", "bearings"], ["residuals", "residuals"], ["kinematics", "course & speed"]].map(([k, label]) => (
              <label key={k}><input type="checkbox" checked={showCharts[k]} data-testid={`toggle-${k}`} onChange={(e) => setShowCharts({ ...showCharts, [k]: e.target.checked })} /> {label}</label>
            ))}
          </div>
          <div className={styles.chartRow}>
            {showCharts.error && (
              <div className={`${styles.chartPanel} ${styles.overlayHost}`} data-testid="panel-error-time">
                <select className={styles.chartSelect} data-testid="error-quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} aria-label="Error quantity">
                  {Object.keys(qdef).map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
                {errChart ? <ChartBox render={errChart} /> : <span className={styles.small}>no solution yet</span>}
              </div>
            )}
            {showCharts.bearings && <div className={styles.chartPanel} data-testid="panel-bearings">{brgChart ? <ChartBox render={brgChart.bearings} /> : null}</div>}
            {showCharts.residuals && <div className={styles.chartPanel} data-testid="panel-residuals">{brgChart ? <ChartBox render={brgChart.residuals} /> : null}</div>}
            {showCharts.kinematics && (
              <div className={styles.chartPanel} data-testid="panel-kinematics">
                <div className={styles.overlayHost} style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
                  <select className={styles.chartSelect} data-testid="kinematics-quantity" value={kinQ} onChange={(e) => setKinQ(e.target.value)} aria-label="Course or speed">
                    <option value="course">course</option>
                    <option value="speed">speed</option>
                    <option value="both">both</option>
                  </select>
                  {kinQ === "both" ? (
                    <div className={styles.subCharts}>
                      <ChartBox render={kinChart.course} />
                      <ChartBox render={kinChart.speed} />
                    </div>
                  ) : <ChartBox render={kinChart[kinQ]} />}
                </div>
              </div>
            )}
            {!showCharts.error && !showCharts.bearings && !showCharts.residuals && !showCharts.kinematics && <div className={styles.small}>All charts hidden.</div>}
          </div>
        </div>
        <div className={styles.dashCol}>
          <div className={styles.panel} data-testid="panel-status">
            <h4>Solver</h4>
            {info.accepts_knots && <div data-testid="splitter-label"><b>{sInfo.label}</b> → </div>}
            <div><b>{info.label}</b></div>
            <div className={styles.small}>{info.assumptions}</div>
            <div className="margin-top--xs" data-testid="solve-status">
              {solve.status === "solving" && (
                <ProgressBar fraction={progressFraction(solve.progress)} stage={progressStage(solve.progress)} seconds={Math.max(0, ((now || performance.now()) - solve.t0) / 1000)} onCancel={cancelSolve} />
              )}
              {solve.status === "cancelled" && (
                <span data-testid="solve-cancelled">Cancelled.{" "}
                  <button className="button button--sm button--link" style={{ padding: 0 }} onClick={() => setNonce((n) => n + 1)}>Solve again</button>
                </span>
              )}
              {solve.status === "error" && <span style={{ color: "#d62728" }}>Failed: {solve.error}</span>}
              {solve.status === "done" && sol && (
                <>
                  <b style={{ color: sol.status === "converged" ? "#2ca02c" : "#d62728" }}>{sol.status.replace("_", " ")}</b>
                  {sol.message ? ` (${sol.message})` : ""}
                  {sol.iterations !== undefined ? `; ${sol.iterations} iterations` : ""}; {fmt(sol.runtime_ms, 0)} ms
                  {s && <>; normalised RMS residual <b data-testid="nrms">{fmt(s.nrms, 2)}</b> (≈1 is a consistent fit)</>}
                  {sol.stride > 1 && <div className={styles.small}>Every {sol.stride}th bearing used (the graph takes at most 720).</div>}
                  {!info.time_late && s && <div className={styles.small}>{s.answered} real-time estimates in the window.</div>}
                  {sol.manoeuvre_prob && (
                    <div className={styles.small} data-testid="model-manoeuvres">
                      The model states {modelSpans.length} target {modelSpans.length === 1 ? "manoeuvre" : "manoeuvres"} (probability over 0.5; shaded purple on the error chart, the truth's red); the truth has {derived.kn.length} in the window.
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
          <div className={styles.panel} data-testid="panel-observability">
            <h4>Observability</h4>
            {obs ? (
              <div data-level={obs.level} data-testid="obs-level">
                <span className={styles.dot} style={{ background: OBS_COLOUR[obs.level] }} />
                <b>{obs.level}</b>: the Cramér–Rao bound on range at the window end is {Number.isFinite(obs.rel) ? `${fmt(100 * obs.rel, 1)}% of range` : "unbounded (the geometry cannot fix range)"} at σ = {fmt(obs.sigma_deg, 2)}°
                <div className={styles.small}>Green under {100 * OBS_GREEN}%, amber under {100 * OBS_AMBER}% (σ floored at {OBS_SIGMA_DEG}° so a noise-free run still shows its geometry). Condition number of the solution's information: {sol && Number.isFinite(sol.condition_number) ? sol.condition_number.toExponential(1) : "∞"}. Shown, never blocking.</div>
              </div>
            ) : "–"}
          </div>
          {mismatch && (
            <div className={`${styles.panel} ${styles.flag}`} data-testid="panel-mismatch">
              <h4>Model mismatch</h4>
              The target manoeuvres inside the window ({derived.kn.length} {derived.kn.length === 1 ? "change" : "changes"}, shaded red on the error chart) and this solver assumes one constant-velocity leg: its answer is biased by design. Narrow the window to one target leg, or give the segmented solver a leg splitter.
            </div>
          )}
          {info.accepts_knots && (
            <div className={styles.panel} data-testid="panel-legs">
              <h4>Target legs</h4>
              {legs ? (
                <>
                  <div className={styles.small}>{sInfo.assumptions}</div>
                  <table>
                    <thead><tr><th></th><th>manoeuvres</th><th>found</th><th>missed</th><th>false</th><th>timing</th></tr></thead>
                    <tbody>
                      <tr><td>{sInfo.told_truth ? "told" : "stated"}</td><td data-testid="legs-stated">{legs.stated}</td><td data-testid="legs-found">{legs.matched} of {legs.truth}</td><td data-testid="legs-missed">{legs.missed}</td><td data-testid="legs-false">{legs.false_}</td><td>{Number.isFinite(legs.median_offset_s) ? `${fmt(legs.median_offset_s, 0)} s` : "–"}</td></tr>
                    </tbody>
                  </table>
                  <div className={styles.small}>
                    Truth (red): {trueSpans.length ? trueSpans.map((m) => `${fmtMin(m.start_s + derived.t0)}–${fmtMin(m.end_s + derived.t0)}`).join(", ") : "none in the window"}.{" "}
                    {splitterName !== "truth" && <>Splitter (orange): {found.length ? found.map((f) => `${fmtMin(f.start_s + derived.t0)}–${fmtMin(f.end_s + derived.t0)}${Number.isFinite(f.stat) ? ` (${fmt(f.stat, 0)})` : ""}`).join(", ") : "none"}.</>}{" "}
                    Found: a stated span within 2 min of a true one, each used once; timing is the median offset of their centres. Splitter {fmt(sol.splitter_runtime_ms / 1000, 1)} s{sol.splitter_message ? `; ${sol.splitter_message}` : ""}.
                  </div>
                </>
              ) : <span className={styles.small}>{solve.status === "solving" ? "waiting for the splitter" : "–"}</span>}
            </div>
          )}
          <div className={styles.panel} data-testid="panel-compare">
            <h4>Compare leg splitters</h4>
            {(() => {
              const fresh = cmp && cmp.key === cmpKey;
              const running = fresh && cmp.status === "running";
              const rows = fresh ? cmpRows : [];
              return (
                <>
                  <div>
                    <button className="button button--sm button--primary" data-testid="compare-run" disabled={running || !derived.problem} onClick={() => startCompare()}>Run all splitters</button>{" "}
                    {running && <><span className={styles.small}>{cmp.progress ? (cmp.progress.splitter ? `${cmp.progress.splitter}: ` : "") + (progressStage(cmp.progress) || "") : "starting"} · {fmt(Math.max(0, ((now || performance.now()) - cmp.t0) / 1000), 0)} s</span>{" "}<button className="button button--sm button--link" style={{ padding: 0 }} onClick={cancelCompare}>cancel</button></>}
                    {cmp && !fresh && <span className={styles.small}>The scenario changed since the last comparison.</span>}
                  </div>
                  {fresh && (
                    <table data-testid="compare-table">
                      <thead><tr><th>splitter → layer</th><th>found / missed / false</th><th>range RMS (%)</th><th>course RMS (°)</th><th>speed RMS (kt)</th><th>s</th></tr></thead>
                      <tbody>
                        {rows.map((r) => (
                          <tr key={r.name} data-testid={`compare-${r.name}`}>
                            <td>{r.lab}</td>
                            {!r.solx ? <td colSpan={5} className={styles.small}>{running ? "…" : "–"}</td> : r.solx.status === "failed" ? <td colSpan={5} className={styles.small}>failed: {r.solx.message}</td> : (
                              <>
                                <td>{r.lg ? `${r.lg.matched} / ${r.lg.missed} / ${r.lg.false_}` : "–"}</td>
                                <td>{r.sum ? fmt(r.sum.range_pct.rms, 1) : "–"}</td>
                                <td>{r.sum ? fmt(r.sum.course_deg.rms, 1) : "–"}</td>
                                <td>{r.sum ? fmt(r.sum.speed_kt.rms, 2) : "–"}</td>
                                <td>{fmt(((r.solx.splitter_runtime_ms || 0) + (r.solx.runtime_ms || 0)) / 1000, 1)}</td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <div className={styles.small}>Each splitter's spans go to the segmented physics layer on this window and this noise draw; errors read at every bearing time, as above. One draw: Reseed and run again before reading much into a difference. C takes minutes (cancel stops it).</div>
                </>
              );
            })()}
          </div>
          <div className={styles.panel} data-testid="panel-errors">
            <h4>Errors across the window</h4>
            {s ? (
              <table>
                <thead><tr><th></th><th>RMS</th><th>worst</th><th>bound (RMS)</th></tr></thead>
                <tbody>
                  <tr><td>Range (NM)</td><td data-testid="err-range">{fmt(s.range_m.rms / NM, 3)}</td><td>{fmt(s.range_m.max / NM, 3)}</td><td>{fmt(s.range_m.crb / NM, 3)}</td></tr>
                  <tr><td>Range (% of range)</td><td data-testid="err-range-pct">{fmt(s.range_pct.rms, 2)}</td><td>{fmt(s.range_pct.max, 2)}</td><td></td></tr>
                  <tr><td>Bearing (°)</td><td>{fmt(s.bearing_deg.rms, 2)}</td><td>{fmt(s.bearing_deg.max, 2)}</td><td>{fmt(s.bearing_deg.crb, 2)}</td></tr>
                  <tr><td>Course (°)</td><td>{fmt(s.course_deg.rms, 2)}</td><td>{fmt(s.course_deg.max, 2)}</td><td>{fmt(s.course_deg.crb, 2)}</td></tr>
                  <tr><td>Speed (kt)</td><td>{fmt(s.speed_kt.rms, 2)}</td><td>{fmt(s.speed_kt.max, 2)}</td><td>{fmt(s.speed_kt.crb, 2)}</td></tr>
                  <tr><td>Position (NM)</td><td>{fmt(s.position_nm.rms, 3)}</td><td>{fmt(s.position_nm.max, 3)}</td><td></td></tr>
                </tbody>
              </table>
            ) : <span className={styles.small}>{solve.status === "solving" ? "waiting for the solver" : "no solution"}</span>}
            <div className={styles.small}>Time-late: each error is read at every bearing time in the window{info.time_late ? "" : " where the real-time model answered"}. The bound assumes the target's manoeuvre times are known; an error far under it was a lucky noise draw, far over it a poor fit. One draw only: press Reseed to see another.</div>
          </div>
          {editor}
          <details>
            <summary>How to use it, and what is running</summary>
            <ul className={styles.small}>
              <li>Drag a <b>waypoint</b> (circle) to move it alone: the legs either side keep their speeds, so their lengths and durations change (later waypoints stay put but are reached later or sooner). Drag the <b>start</b> (filled circle) to move a whole track. Ctrl-click (⌘-click) a waypoint to delete it.</li>
              <li>Drag a leg's <b>square handle</b> to change its course and speed: the leg keeps its duration, so its length follows the speed, and every later leg swings round with it, so the rest of the track can move a long way.</li>
              <li>Click a leg to insert a waypoint; select a waypoint and press Delete (or right-click or ctrl-click it) to remove it. Undo with Ctrl+Z. Amber waypoints: the turn does not fit at its rate and is drawn tighter.</li>
              <li>Wheel to zoom, drag empty space to pan. The link in the address bar restores this exact scenario, noise draw and solver.</li>
              <li>Leg splitters (spec 036): none; told the truth (an oracle); Debrief's 2015 arctan slicing (one split per steady ownship leg, ZigRatio); a multi-leg arctan slicing with independent slices; the arctan law with joined legs, searched over the whole window; and C, the project's classical segmenter (spec 005, spec 021's port). Their spans go to the segmented physics layer; "Run all splitters" compares them on this window.</li>
              <li>Solvers: JavaScript batch least squares (spec 021's port of the Python reference); the physics layer of Gates 1–2 as an ONNX graph (<code>tl-layer.onnx</code>{tlInfo ? <> , SHA-256 <code>{tlInfo.onnx_sha256.slice(0, 16)}…</code></> : null}), with one leg or told the true manoeuvre times; and spec 016's whole-period learned model (three training seeds, 26 MB each, loaded on first use), which reads the whole window at once and also states where it thinks the target manoeuvred. For the time-late studies' standing system see <a href={timelateUrl}>Time-late</a>.</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
}

export default function DemoPage() {
  return (
    <Layout title="Demonstrator" description="Drag an ownship and a target track and watch a time-late TMA solution respond (spec 035).">
      <main className={styles.main}>
        <div className={styles.header}>
          <h1>TMA demonstrator</h1>
          <span className={`${styles.small} ${styles.oneLine}`}>
            Drag the tracks, narrow the window, and see the target solved from bearings alone over that window against the truth. A toy two-vessel world with Gaussian bearing noise, one draw at a time: a feel for the solvers, not a result.
          </span>
        </div>
        <BrowserOnly fallback={<p>Loading…</p>}>{() => <Demo />}</BrowserOnly>
      </main>
    </Layout>
  );
}
