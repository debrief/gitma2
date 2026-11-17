// Long engagements (spec 023, issue #42): the standing systems on one simulated engagement each
// of 6, 12, 24 and 48 hours, precomputed in Python (scripts/research/long_viewer_data.py). Used by
// /viewer (mode "realtime": estimates every 10 minutes from the bearings so far) and /timelate
// (mode "timelate": one stitched track from 2-hour windows). The page computes no estimate.
import React, { useEffect, useMemo, useState } from "react";
import useBaseUrl from "@docusaurus/useBaseUrl";

const OWN = "#1f77b4";
const TGT = "#d62728";
const COLOURS = {
  e: "#ff7f0e",
  c2: "#8c564b",
  one_leg: "#7f7f7f",
  imm: "#17becf",
  "ctl-d1-q0.01": "#9467bd",
  "history-best": "#2ca02c",
};
const DEFAULT_SHOWN = { e: true, c2: true, one_leg: false, imm: true, "ctl-d1-q0.01": true, "history-best": false };

async function fetchJsonGz(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const stream = res.body.pipeThrough(new DecompressionStream("gzip"));
  return JSON.parse(await new Response(stream).text());
}

const fmt = (v, d = 1) => (v === null || v === undefined || !Number.isFinite(v) ? "–" : v.toFixed(d));
const hours = (s) => s / 3600;

function TrackPlot({ doc, part, systems, shown, mode }) {
  const W = 640, H = 520, PAD = 24;
  const box = useMemo(() => {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const [tx, ty, ox, oy] of doc.truth) for (const [x, y] of [[tx, ty], [ox, oy]]) {
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    const span = Math.max(x1 - x0, y1 - y0) * 1.08 + 2000;
    return { x0: (x0 + x1) / 2 - span / 2, y0: (y0 + y1) / 2 - span / 2, span };
  }, [doc]);
  const sx = (x) => PAD + ((x - box.x0) / box.span) * (W - 2 * PAD);
  const sy = (y) => H - PAD - ((y - box.y0) / box.span) * (H - 2 * PAD);
  const inBox = (r) => r && r[0] > box.x0 - box.span && r[0] < box.x0 + 2 * box.span && r[1] > box.y0 - box.span && r[1] < box.y0 + 2 * box.span;
  const pts = (rows) => rows.filter(inBox).map((r) => `${sx(r[0]).toFixed(1)},${sy(r[1]).toFixed(1)}`).join(" ");
  const scale = (W - 2 * PAD) / box.span;
  const target = box.span / 5, p10 = Math.pow(10, Math.floor(Math.log10(target)));
  const bar = [5, 2, 1].map((f) => f * p10).find((v) => v <= target) || p10;
  // a line per run of answered rows, so gaps stay gaps
  const runs = (rows) => {
    const out = []; let cur = [];
    for (const r of rows) { if (inBox(r)) cur.push(r); else if (cur.length) { out.push(cur); cur = []; } }
    if (cur.length) out.push(cur);
    return out;
  };
  const hourTicks = [];
  const every = Math.round(3600 / doc.dt_truth_s);
  for (let i = 0; i < doc.truth.length; i += every) hourTicks.push(doc.truth[i]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: W, border: "1px solid var(--ifm-color-emphasis-300)", borderRadius: 6, background: "var(--ifm-background-surface-color)" }} role="img" aria-label="Long-engagement tracks">
      <defs><clipPath id={`lgclip-${mode}`}><rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD} /></clipPath></defs>
      <g clipPath={`url(#lgclip-${mode})`}>
        <polyline points={pts(doc.truth.map((r) => [r[2], r[3]]))} fill="none" stroke={OWN} strokeWidth={1} opacity={0.8} />
        <polyline points={pts(doc.truth)} fill="none" stroke={TGT} strokeWidth={1.4} />
        {systems.filter((s) => shown[s]).map((s) =>
          runs(part.systems[s].states).map((r, i) => (
            <polyline key={`${s}-${i}`} points={pts(r)} fill="none" stroke={COLOURS[s]} strokeWidth={mode === "realtime" ? 1 : 1.2} opacity={0.85} strokeDasharray={s === "history-best" ? "5 3" : undefined} />
          )),
        )}
        {mode === "realtime" && systems.filter((s) => shown[s]).map((s) =>
          part.systems[s].states.map((r, i) => (inBox(r) ? <circle key={`${s}-p${i}`} cx={sx(r[0])} cy={sy(r[1])} r={1.6} fill={COLOURS[s]} /> : null)),
        )}
        {hourTicks.map((r, i) => <circle key={`t${i}`} cx={sx(r[0])} cy={sy(r[1])} r={2.2} fill={TGT} />)}
        <circle cx={sx(doc.truth[0][0])} cy={sy(doc.truth[0][1])} r={5} fill="none" stroke={TGT} strokeWidth={1.5} />
        <rect x={sx(doc.truth[doc.truth.length - 1][0]) - 4} y={sy(doc.truth[doc.truth.length - 1][1]) - 4} width={8} height={8} fill="none" stroke={TGT} strokeWidth={1.5} />
      </g>
      <line x1={W - PAD - bar * scale} y1={H - 8} x2={W - PAD} y2={H - 8} stroke="currentColor" />
      <text x={W - PAD} y={H - 12} textAnchor="end" fontSize={11} fill="currentColor">{bar >= 1000 ? `${bar / 1000} km` : `${bar} m`}</text>
      <text x={PAD} y={15} fontSize={11} fill="currentColor">north up · red: target, blue: ownship · red dots every hour · ○ start, □ end</text>
    </svg>
  );
}

function Timeline({ doc, part, mode, shown }) {
  const W = 640, ROW = 18, L = 120, T = doc.hours * 3600;
  const x = (s) => L + (s / T) * (W - L - 10);
  const rows = [["ownship turns", doc.turns_s, OWN], ["target manoeuvres", doc.true_s, TGT]];
  if (mode === "timelate") {
    for (const s of ["ctl-d1-q0.01", "c2"]) if (shown[s]) rows.push([`declared: ${s === "c2" ? "C″" : "ctl"}`, part.declared_s[s] || [], COLOURS[s]]);
  }
  const H = rows.length * ROW + (mode === "timelate" ? 22 : 0) + 22;
  const step = doc.hours <= 12 ? 1 : doc.hours <= 24 ? 2 : 4;
  const ticks = []; for (let h = 0; h <= doc.hours; h += step) ticks.push(h);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: W }} role="img" aria-label="Timeline">
      {rows.map(([name, spans, col], i) => (
        <g key={name}>
          <text x={L - 6} y={i * ROW + 13} textAnchor="end" fontSize={10.5} fill="currentColor">{name}</text>
          <line x1={L} y1={i * ROW + 9} x2={W - 10} y2={i * ROW + 9} stroke="var(--ifm-color-emphasis-300)" />
          {spans.map(([a, b], j) => <rect key={j} x={x(a)} y={i * ROW + 3} width={Math.max(x(b) - x(a), 1.5)} height={12} fill={col} opacity={0.75} />)}
        </g>
      ))}
      {mode === "timelate" && (
        <g>
          <text x={L - 6} y={rows.length * ROW + 13} textAnchor="end" fontSize={10.5} fill="currentColor">2-h windows</text>
          {part.windows.map((w, j) => (
            <rect key={j} x={x(w.from_s)} y={rows.length * ROW + 3 + (j % 2) * 7} width={x(w.to_s) - x(w.from_s)} height={6} fill="var(--ifm-color-emphasis-500)" opacity={0.6}>
              <title>{`window ${j}: ${fmt(hours(w.from_s), 2)}–${fmt(hours(w.to_s), 2)} h, ${w.minutes} min to solve`}</title>
            </rect>
          ))}
        </g>
      )}
      {ticks.map((h) => <text key={h} x={x(h * 3600)} y={H - 4} textAnchor="middle" fontSize={10} fill="currentColor">{h} h</text>)}
    </svg>
  );
}

function ErrorChart({ doc, part, systems, shown }) {
  const W = 640, H = 200, L = 46, B = 22, T = doc.hours * 3600;
  const ymax = 1.0; // relative range error, clipped at 100%
  const x = (s) => L + (s / T) * (W - L - 10);
  const y = (v) => H - B - (Math.min(v, ymax) / ymax) * (H - B - 10);
  const paths = systems.filter((s) => shown[s]).map((s) => {
    const e = part.systems[s].range_err;
    let d = "", pen = false;
    e.forEach((v, i) => {
      if (v === null) { pen = false; return; }
      d += `${pen ? "L" : "M"}${x(part.times_s[i]).toFixed(1)},${y(v).toFixed(1)}`; pen = true;
    });
    return <path key={s} d={d} fill="none" stroke={COLOURS[s]} strokeWidth={1.1} />;
  });
  const step = doc.hours <= 12 ? 1 : doc.hours <= 24 ? 2 : 4;
  const ticks = []; for (let h = 0; h <= doc.hours; h += step) ticks.push(h);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: W }} role="img" aria-label="Relative range error against time">
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - 10} y1={y(v)} y2={y(v)} stroke="var(--ifm-color-emphasis-200)" />
          <text x={L - 4} y={y(v) + 3} textAnchor="end" fontSize={10} fill="currentColor">{Math.round(v * 100)}%</text>
        </g>
      ))}
      {paths}
      {ticks.map((h) => <text key={h} x={x(h * 3600)} y={H - 6} textAnchor="middle" fontSize={10} fill="currentColor">{h} h</text>)}
      <text x={L} y={10} fontSize={10.5} fill="currentColor">relative range error (clipped at 100%)</text>
    </svg>
  );
}

export default function LongEngagements({ mode }) {
  const base = useBaseUrl("/long-data/");
  const note = "https://github.com/debrief/gitma2/blob/main/docs/research/12-long-engagements.md";
  const record = "https://github.com/debrief/gitma2/blob/main/experiments/20261117-long/tables.md";
  const [man, setMan] = useState(null);
  const [which, setWhich] = useState(0);
  const [docs, setDocs] = useState({});
  const [shown, setShown] = useState(DEFAULT_SHOWN);
  const [error, setError] = useState(null);
  useEffect(() => {
    fetch(base + "manifest.json").then((r) => r.json()).then(setMan).catch((e) => setError(String(e)));
  }, [base]);
  useEffect(() => {
    if (!man || docs[which]) return;
    const m = man.engagements[which];
    fetchJsonGz(base + m.file).then((d) => setDocs((x) => ({ ...x, [which]: d }))).catch((e) => setError(String(e)));
  }, [man, which, docs, base]);
  if (error) return <p>The long-engagement data could not be loaded: {error}</p>;
  if (!man) return <p>Loading the long engagements…</p>;
  const doc = docs[which];
  const systems = mode === "realtime" ? man.realtime_systems : man.timelate_systems;
  const part = doc ? doc[mode] : null;
  return (
    <div data-testid={`long-${mode}`}>
      <p>
        {mode === "realtime"
          ? "The same real-time systems on much longer engagements: every 10 minutes, each system estimates the target from the bearings it has. E, C″ and one leg see only a recent window (E's exported graph takes exactly two hours of 10-second bearings; one leg the last 30 minutes); the IMM filters the whole engagement. C″'s zig veto is applied at every ownship turn."
          : "The standing time-late control on much longer engagements. It was built for periods of 20 to 120 minutes, so it runs on a chain of 2-hour windows overlapping by 30 minutes; each part of the long track comes from the window whose centre is nearest."}{" "}
        One simulated engagement per duration (seed 348): a feasibility measurement, not a result. Computed in Python, not in your browser.
        The challenges are in the <a href={note}>research note</a>; the numbers in the <a href={record}>record's tables</a>.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", margin: "0.6rem 0" }}>
        {man.engagements.map((m, i) => (
          <button key={m.index} className={`button button--sm ${i === which ? "button--primary" : "button--secondary"}`} onClick={() => setWhich(i)}>{m.hours} hours</button>
        ))}
      </div>
      {!doc && <p>Loading…</p>}
      {doc && !part && <p>This engagement has no {mode} run in the record.</p>}
      {doc && part && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1.2rem" }}>
          <div style={{ flex: "1 1 100%", maxWidth: 660 }}>
            <TrackPlot doc={doc} part={part} systems={systems} shown={shown} mode={mode} />
            <Timeline doc={doc} part={part} mode={mode} shown={shown} />
            <ErrorChart doc={doc} part={part} systems={systems} shown={shown} />
          </div>
          <div style={{ flex: "1 1 100%" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ fontSize: "0.85rem", whiteSpace: "nowrap" }}>
                <thead><tr><th>system</th><th>median range err</th><th>course °</th><th>speed kt</th><th>answered</th></tr></thead>
                <tbody>
                  {systems.map((s) => {
                    const st = part.systems[s].stats;
                    return (
                      <tr key={s}>
                        <td><label><input type="checkbox" checked={!!shown[s]} onChange={() => setShown({ ...shown, [s]: !shown[s] })} /> <span style={{ color: COLOURS[s] }}>●</span> {man.labels[s]}</label></td>
                        <td>{fmt(100 * st.range_rel)}%</td>
                        <td>{fmt(st.course_deg)}</td>
                        <td>{fmt(st.speed_kt)}</td>
                        <td>{fmt(100 * st.answered, 0)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p><small>
              {doc.hours} hours: {doc.summary.manoeuvres} target manoeuvres, {doc.summary.ownship_turns} ownship turns, range {fmt(doc.summary.range_km[0])} to {fmt(doc.summary.range_km[2])} km (median {fmt(doc.summary.range_km[1])}).{" "}
              {mode === "realtime"
                ? `Run time per estimate on one CPU core: E ${fmt(part.seconds_per_evaluation.e)} s, C″ ${fmt(part.seconds_per_evaluation.c2)} s (C's confirmation over the two-hour window, re-run every time).`
                : `${part.windows.length} windows, ${fmt(part.windows.reduce((a, w) => a + w.minutes, 0) / 60, 1)} CPU-hours in all.${part.windows_missing.length ? ` Windows ${part.windows_missing.join(", ")} did not finish.` : ""}`}{" "}
              Medians are over the rows each system answered.
            </small></p>
          </div>
        </div>
      )}
    </div>
  );
}
