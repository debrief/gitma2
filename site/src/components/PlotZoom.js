// Mouse zoom and pan for the site's track plots (issue 41). The plot keeps its own data box;
// this hook turns it into a view (centre and metres per pixel, equal on both axes) that the
// wheel zooms about the cursor, a drag pans and a double click resets. Markers, line widths and
// the scale bar are drawn in screen units, so they keep their size while the view zooms.
import React, { useCallback, useEffect, useRef, useState } from "react";

const Z_MAX = 200;

// box: {x0, y0, span} in metres (a square around everything plotted); W, H, PAD in SVG units
export function usePlotZoom(box, W, H, PAD) {
  const svgRef = useRef(null);
  const [zoom, setZoom] = useState({ z: 1, cx: null, cy: null });
  // a new box (another engagement or period) starts unzoomed
  useEffect(() => setZoom({ z: 1, cx: null, cy: null }), [box]);

  const baseMpp = box.span / Math.min(W - 2 * PAD, H - 2 * PAD);
  const z = zoom.z;
  const cx = zoom.cx ?? box.x0 + box.span / 2;
  const cy = zoom.cy ?? box.y0 + box.span / 2;
  const mpp = baseMpp / z;
  const sx = (x) => W / 2 + (x - cx) / mpp;
  const sy = (y) => H / 2 - (y - cy) / mpp;
  const scale = 1 / mpp; // SVG units per metre

  // client coordinates to SVG units (the SVG keeps its viewBox's aspect)
  const toSvg = (ev) => {
    const r = svgRef.current.getBoundingClientRect();
    return [((ev.clientX - r.left) * W) / r.width, ((ev.clientY - r.top) * H) / r.height];
  };

  // zoom by factor f about the SVG point (px, py), or the centre
  const zoomBy = useCallback(
    (f, px = W / 2, py = H / 2) =>
      setZoom((s) => {
        const sCx = s.cx ?? box.x0 + box.span / 2;
        const sCy = s.cy ?? box.y0 + box.span / 2;
        const nz = Math.min(Math.max(s.z * f, 1), Z_MAX);
        if (nz === 1) return { z: 1, cx: null, cy: null };
        const m0 = baseMpp / s.z, m1 = baseMpp / nz;
        // the point under the cursor stays put
        const mx = sCx + (px - W / 2) * m0, my = sCy - (py - H / 2) * m0;
        return { z: nz, cx: mx - (px - W / 2) * m1, cy: my + (py - H / 2) * m1 };
      }),
    [box, baseMpp, W, H]
  );

  // the wheel listener must be non-passive to keep the page from scrolling under the plot
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return undefined;
    const onWheel = (ev) => {
      ev.preventDefault();
      const [px, py] = toSvg(ev);
      const d = ev.deltaMode === 1 ? ev.deltaY * 16 : ev.deltaY;
      zoomBy(Math.exp(-d * 0.002), px, py);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  });

  const drag = useRef(null);
  const onPointerDown = (ev) => {
    if (ev.button !== 0 || z === 1) return;
    drag.current = { p: toSvg(ev), cx, cy };
    ev.currentTarget.setPointerCapture(ev.pointerId);
  };
  const onPointerMove = (ev) => {
    if (!drag.current) return;
    const [px, py] = toSvg(ev);
    const d = drag.current;
    setZoom((s) => ({ ...s, cx: d.cx - (px - d.p[0]) * mpp, cy: d.cy + (py - d.p[1]) * mpp }));
  };
  const onPointerUp = () => { drag.current = null; };
  const reset = () => setZoom({ z: 1, cx: null, cy: null });

  const svgProps = {
    ref: svgRef,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel: onPointerUp,
    onDoubleClick: reset,
    style: { cursor: z > 1 ? "grab" : "zoom-in", touchAction: z > 1 ? "none" : "auto", userSelect: "none" },
  };
  return { sx, sy, scale, z, zoomBy, reset, svgProps };
}

// a round length near a fifth of the plot's width: 1, 2 or 5 × 10^n m
export function scaleBar(scale, W, PAD) {
  const target = (W - 2 * PAD) / scale / 5;
  const p10 = Math.pow(10, Math.floor(Math.log10(target)));
  const m = [5, 2, 1].map((f) => f * p10).find((v) => v <= target) || p10;
  return { m, label: m >= 1000 ? `${m / 1000} km` : `${m} m` };
}

export function ZoomControls({ zoom }) {
  return (
    <div style={{ display: "flex", gap: "0.3rem", alignItems: "center", margin: "0.3rem 0", fontSize: "0.8rem" }} data-testid="zoom-controls">
      <button className="button button--sm button--secondary" onClick={() => zoom.zoomBy(1.5)} aria-label="zoom in">+</button>
      <button className="button button--sm button--secondary" onClick={() => zoom.zoomBy(1 / 1.5)} aria-label="zoom out" disabled={zoom.z <= 1}>−</button>
      <button className="button button--sm button--secondary" onClick={zoom.reset} disabled={zoom.z <= 1}>reset</button>
      <span style={{ opacity: 0.75 }}>
        {zoom.z > 1 ? `× ${zoom.z.toFixed(1)} · ` : ""}wheel to zoom, drag to pan, double click to reset
      </span>
    </div>
  );
}
