// Time-late TMA (spec 022): whole-period tracks from spec 016's test record, shown beside the
// truth and the old system, with true and declared manoeuvres. Precomputed in Python by
// scripts/research/timelate_viewer_data.py; this page computes no estimate.
import React, { useEffect, useMemo, useState } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import BrowserOnly from "@docusaurus/BrowserOnly";
import { usePlotZoom, scaleBar, ZoomControls } from "../components/PlotZoom";

const KT = 0.514444;
const OWN = "#1f77b4";
const TGT = "#d62728";
const COLOURS = { "ctl-d1-q0.01": "#9467bd", c2: "#8c564b", "history-best": "#2ca02c", "learned-s1-arc": "#ff7f0e" };
const SHORT = { "ctl-d1-q0.01": "standing control", c2: "C″ (old system)", "history-best": "true-history fit", "learned-s1-arc": "learned (stopped)" };

async function fetchJsonGz(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const stream = res.body.pipeThrough(new DecompressionStream("gzip"));
  return JSON.parse(await new Response(stream).text());
}

const fmt = (v, d = 1) => (v === null || v === undefined || !Number.isFinite(v) ? "–" : v.toFixed(d));
const median = (a) => {
  const b = a.filter(Number.isFinite).sort((x, y) => x - y);
  if (!b.length) return NaN;
  const m = Math.floor(b.length / 2);
  return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2;
};

// Each system's track is one solution fitted to the whole period; ticks every 10 minutes along
// every track let the reader match positions in time (spec 022, owner 2026-11-16: no
// moment-by-moment view in time-late).
const TICK_S = 600;
function Tracks({ p, shown }) {
  const W = 640, H = 480, PAD = 26;
  const box = useMemo(() => {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const r of p.truth) for (const [x, y] of [[r[0], r[1]], [r[4], r[5]]]) {
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    const span = Math.max(x1 - x0, y1 - y0) * 1.2 + 2000;
    return { x0: (x0 + x1) / 2 - span / 2, y0: (y0 + y1) / 2 - span / 2, span };
  }, [p]);
  const zoom = usePlotZoom(box, W, H, PAD);
  const { sx, sy, scale } = zoom;
  const line = (pts) => pts.filter((r) => r && Number.isFinite(r[0])).map((r) => `${sx(r[0]).toFixed(1)},${sy(r[1]).toFixed(1)}`).join(" ");
  const every = Math.max(1, Math.round(TICK_S / p.step_s));
  const ticks = (rows, col, key) =>
    rows.map((r, i) => (i % every === 0 && r && Number.isFinite(r[0]) ? <circle key={`${key}-${i}`} cx={sx(r[0])} cy={sy(r[1])} r={2.4} fill={col} /> : null));
  const first = p.truth[0], last = p.truth[p.truth.length - 1];
  // true manoeuvres drawn thick on the target track
  const inMan = (i) => p.true_spans.some(([a, b]) => i * p.step_s >= a && i * p.step_s <= b);
  const manSegs = [];
  let cur = [];
  p.truth.forEach((r, i) => {
    if (inMan(i)) cur.push([r[0], r[1]]);
    else if (cur.length) { manSegs.push(cur); cur = []; }
  });
  if (cur.length) manSegs.push(cur);
  const bar = scaleBar(scale, W, PAD);
  return (
    <>
    <svg viewBox={`0 0 ${W} ${H}`} {...zoom.svgProps} style={{ width: "100%", maxWidth: W, border: "1px solid var(--ifm-color-emphasis-300)", borderRadius: 6, background: "var(--ifm-background-surface-color)", ...zoom.svgProps.style }} role="img" aria-label="Whole-period tracks">
      <defs><clipPath id="tlclip"><rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD} /></clipPath></defs>
      <g clipPath="url(#tlclip)">
        <polyline points={line(p.truth.map((r) => [r[4], r[5]]))} fill="none" stroke={OWN} strokeWidth={1.5} />
        <polyline points={line(p.truth)} fill="none" stroke={TGT} strokeWidth={1.6} />
        {manSegs.map((s, i) => <polyline key={i} points={line(s)} fill="none" stroke={TGT} strokeWidth={5} opacity={0.35} />)}
        {Object.keys(COLOURS).filter((s) => shown[s]).map((s) => (
          <polyline key={s} points={line(p.systems[s].track)} fill="none" stroke={COLOURS[s]} strokeWidth={1.3} strokeDasharray={s === "history-best" ? "5 3" : undefined} />
        ))}
        {ticks(p.truth.map((r) => [r[4], r[5]]), OWN, "own")}
        {ticks(p.truth, TGT, "tgt")}
        {Object.keys(COLOURS).filter((s) => shown[s]).map((s) => ticks(p.systems[s].track, COLOURS[s], s))}
        <circle cx={sx(first[0])} cy={sy(first[1])} r={5} fill="none" stroke={TGT} strokeWidth={1.5} />
        <rect x={sx(last[0]) - 4} y={sy(last[1]) - 4} width={8} height={8} fill="none" stroke={TGT} strokeWidth={1.5} />
      </g>
      <line x1={W - PAD - bar.m * scale} y1={H - 10} x2={W - PAD} y2={H - 10} stroke="currentColor" />
      <text x={W - PAD} y={H - 14} textAnchor="end" fontSize={11} fill="currentColor">{bar.label}</text>
      <text x={PAD} y={16} fontSize={11} fill="currentColor">north up · thick red: true manoeuvres · dots every 10 min · ○ start, □ end</text>
    </svg>
    <ZoomControls zoom={zoom} />
    </>
  );
}

function Timeline({ p, shown }) {
  const W = 640, ROW = 20, L = 130, T = p.seconds;
  const rows = [["truth", p.true_spans, TGT], ...["ctl-d1-q0.01", "c2", "learned-s1-arc"].filter((s) => shown[s]).map((s) => [SHORT[s], p.systems[s].declared || [], COLOURS[s]])];
  const x = (s) => L + (s / T) * (W - L - 10);
  return (
    <svg viewBox={`0 0 ${W} ${rows.length * ROW + 26}`} style={{ width: "100%", maxWidth: W }} role="img" aria-label="Manoeuvre timeline">
      {rows.map(([name, spans, col], i) => (
        <g key={name}>
          <text x={L - 6} y={i * ROW + 14} textAnchor="end" fontSize={11} fill="currentColor">{name}</text>
          <line x1={L} y1={i * ROW + 10} x2={W - 10} y2={i * ROW + 10} stroke="var(--ifm-color-emphasis-300)" />
          {spans.map(([a, b], j) => <rect key={j} x={x(a)} y={i * ROW + 4} width={Math.max(x(b) - x(a), 2)} height={12} fill={col} opacity={0.75} />)}
        </g>
      ))}
      {[0, 0.25, 0.5, 0.75, 1].map((f) => (
        <text key={f} x={x(f * T)} y={rows.length * ROW + 18} textAnchor="middle" fontSize={10} fill="currentColor">{Math.round((f * T) / 60)} min</text>
      ))}
    </svg>
  );
}

function Page() {
  const base = useBaseUrl("/timelate-data/");
  const account = useBaseUrl("/blog/2026/11/15/time-late-synthesis");
  const [man, setMan] = useState(null);
  const [split, setSplit] = useState("man2");
  const [data, setData] = useState({});
  const [pi, setPi] = useState(0);
  const [shown, setShown] = useState({ "ctl-d1-q0.01": true, c2: true, "history-best": false, "learned-s1-arc": false });
  const [error, setError] = useState(null);
  useEffect(() => {
    fetch(base + "manifest.json").then((r) => r.json()).then(setMan).catch((e) => setError(String(e)));
  }, [base]);
  useEffect(() => {
    if (!man || data[split]) return;
    fetchJsonGz(base + man.splits[split].file).then((d) => setData((x) => ({ ...x, [split]: d }))).catch((e) => setError(String(e)));
  }, [man, split, data, base]);
  const d = data[split];
  const p = d ? d.periods[Math.min(pi, d.periods.length - 1)] : null;
  if (error) return <p>The time-late data could not be loaded: {error}</p>;
  if (!man) return <p>Loading…</p>;
  const pooled = d
    ? Object.keys(man.systems).map((s) => [s, median(d.periods.map((x) => x.systems[s].median.range))])
    : [];
  const better = d ? d.periods.filter((x) => x.systems["ctl-d1-q0.01"].median.range < x.systems.c2.median.range).length : 0;
  return (
    <>
      <p>
        <strong>Time-late</strong> means after the fact: given every bearing of a period (20 to 120 minutes of
        5-second bearings), find the one track and manoeuvre history that best explain the whole period. Each track
        below is a single solution fitted to all of the period's bearings at once, so what the later legs reveal about
        range also fixes the early track; nothing is estimated moment by moment. The standing system is a
        classical control: wild bearings are edited, error correlation is estimated, manoeuvre histories are searched
        by their evidence under two manoeuvre priors, and a history is declared at a margin. Nothing in it is learned.
        These periods come from spec 016's test record (<code>{man.record}</code>, seed {man.seed}, used). They are the
        first 20 stored periods of each kind, not a selection. The three kinds are the same 20 engagements under
        different conditions, so they are not independent samples. The figures of record are in{" "}
        <a href={account}>the time-late account</a> and its <a href={man.tables}>table of record</a>.
      </p>
      <p><small>{man.note}</small></p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", margin: "0.6rem 0" }}>
        {Object.entries(man.splits).map(([k, v]) => (
          <button key={k} className={`button button--sm ${k === split ? "button--primary" : "button--secondary"}`} onClick={() => { setSplit(k); setPi(0); }}>{v.label}</button>
        ))}
      </div>
      {d && (
        <>
          <p style={{ fontSize: "0.9rem" }}>
            Over these {d.periods.length} periods, median of each period's median range error:{" "}
            {pooled.map(([s, v]) => <span key={s} style={{ marginRight: "0.8rem" }}><span style={{ color: COLOURS[s] }}>●</span> {SHORT[s]} {fmt(100 * v)}%</span>)}
            · the control beats C″ in {better} of {d.periods.length} periods.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", marginBottom: "0.8rem" }} data-testid="periods">
            {d.periods.map((x, i) => {
              const r = x.systems.c2.median.range / x.systems["ctl-d1-q0.01"].median.range;
              return (
                <button key={x.ordinal} className={`button button--sm ${i === pi ? "button--primary" : "button--outline button--secondary"}`} onClick={() => setPi(i)} title={`C″ ÷ control ${fmt(r, 2)}`}>
                  {x.ordinal} <small>({fmt(r, 1)}×)</small>
                </button>
              );
            })}
          </div>
          <p><small>Each button is a period; in brackets, C″'s median range error ÷ the control's (above 1: the control is better).</small></p>
        </>
      )}
      {p && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1.2rem" }}>
          <div style={{ flex: "1 1 100%", maxWidth: 660 }}>
            <Tracks p={p} shown={shown} />
            <Timeline p={p} shown={shown} />
          </div>
          <div style={{ flex: "1 1 100%" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ fontSize: "0.85rem", whiteSpace: "nowrap" }} data-testid="errors">
                <thead><tr><th>system</th><th>median range err</th><th>course err °</th><th>speed err kt</th><th>manoeuvres</th></tr></thead>
                <tbody>
                  <tr style={{ color: TGT }}><td>truth</td><td /><td /><td /><td>{p.true_spans.length}</td></tr>
                  {Object.entries(man.systems).map(([s, label]) => {
                    const m = p.systems[s].median;
                    return (
                      <tr key={s}>
                        <td><label><input type="checkbox" checked={shown[s]} onChange={() => setShown({ ...shown, [s]: !shown[s] })} /> <span style={{ color: COLOURS[s] }}>●</span> {label}</label></td>
                        <td>{fmt(100 * m.range)}%</td>
                        <td>{fmt(m.course_deg)}</td>
                        <td>{fmt(m.speed_kt)}</td>
                        <td>{p.systems[s].declared ? p.systems[s].declared.length : "told"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p><small>
              Period {p.ordinal}, {Math.round(p.seconds / 60)} minutes{p.edited ? `, ${p.edited} wild bearings edited by the control` : ""}. The true-history fit is told
              the manoeuvres; it is a reference, not a bound. The learned model was stopped by its registered study (spec 016); it is shown
              for completeness.
            </small></p>
          </div>
        </div>
      )}
    </>
  );
}

export default function TimelatePage() {
  return (
    <Layout title="Time-late TMA" description="Whole-period tracks of the standing time-late system beside the truth and the old system">
      <div className="container margin-vert--lg" style={{ maxWidth: 1100 }}>
        <h1>Time-late TMA: the whole track after the fact</h1>
        <BrowserOnly fallback={<p>This page needs JavaScript.</p>}>{() => <Page />}</BrowserOnly>
      </div>
    </Layout>
  );
}
