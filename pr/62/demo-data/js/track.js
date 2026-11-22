// Spec 035: a vessel's track (FR-001..006). A track is a start point and legs (course, speed,
// duration, turn rate at the leg's end) in the page's units (NM, kt, degrees, seconds). The
// truth path joins legs by steady-rate arcs of radius v/omega tangent to both legs (FR-005); an
// arc that does not fit in half of either adjoining leg is clamped to a tighter radius and its
// waypoint marked amber. The vessel runs the path in order: the straight part of a leg at the
// leg's speed, a turn at the incoming leg's speed. Internally metres and seconds; x east, y north.
export const NM = 1852.0;
export const KT = 1852.0 / 3600.0;
export const DEG = Math.PI / 180.0;

const wrap180 = (d) => {
  const w = ((((d + 180) % 360) + 360) % 360) - 180;
  return w === -180 ? 180 : w;
};
export const wrap360 = (d) => ((d % 360) + 360) % 360;
const heading = (psi) => [Math.sin(psi), Math.cos(psi)];

// waypoint positions (NM): W0 = start, W(i+1) = W(i) + leg i
export function waypoints(track) {
  const out = [[track.start_x_nm, track.start_y_nm]];
  for (const leg of track.legs) {
    const [x, y] = out[out.length - 1];
    const d = (leg.speed_kt * leg.duration_s) / 3600.0;
    out.push([x + d * Math.sin(leg.course_deg * DEG), y + d * Math.cos(leg.course_deg * DEG)]);
  }
  return out;
}

// The truth path: pieces in time order, each {kind: "line"|"arc", t0, t1, ...}, joins with their
// turn spans, and the end time. Positions in metres.
export function buildPath(track) {
  const W = waypoints(track).map(([x, y]) => [x * NM, y * NM]);
  const L = track.legs.length;
  const v = track.legs.map((l) => l.speed_kt * KT);
  const len = track.legs.map((l, i) => v[i] * l.duration_s);
  // tangent distances at each join j (between leg j-1 and leg j), j = 1..L-1
  const joins = [];
  for (let j = 1; j < L; j++) {
    const a = track.legs[j - 1], b = track.legs[j];
    const dpsi = wrap180(b.course_deg - a.course_deg);
    const th = Math.abs(dpsi) * DEG;
    const omega = a.turn_rate_dps * DEG;
    let r = v[j - 1] / omega;
    let d = th > 1e-9 && v[j - 1] > 0 ? r * Math.tan(th / 2) : 0;
    const room = Math.min(len[j - 1], len[j]) / 2;
    let clamped = false;
    if (d > room || !Number.isFinite(d)) {
      d = room;
      r = th > 1e-9 ? d / Math.tan(th / 2) : 0;
      clamped = th > 1e-9;
    }
    if (th >= Math.PI - 1e-9) {
      // a reversal has no tangent arc: a turn on the spot, marked amber
      d = 0;
      r = 0;
      clamped = true;
    }
    joins.push({ j, dpsi, th, r, d, clamped, speedChange: Math.abs(b.speed_kt - a.speed_kt) > 1e-9, courseChange: th > 1e-9 });
  }
  const pieces = [];
  let t = 0;
  for (let i = 0; i < L; i++) {
    const psi = track.legs[i].course_deg * DEG;
    const h = heading(psi);
    const dIn = i > 0 ? joins[i - 1].d : 0;
    const dOut = i < L - 1 ? joins[i].d : 0;
    const p0 = [W[i][0] + dIn * h[0], W[i][1] + dIn * h[1]];
    const straight = Math.max(len[i] - dIn - dOut, 0);
    const dur = v[i] > 0 ? straight / v[i] : track.legs[i].duration_s;
    pieces.push({ kind: "line", leg: i, t0: t, t1: t + dur, p0, vel: [v[i] * h[0], v[i] * h[1]], speed: v[i], psi });
    t += dur;
    if (i < L - 1) {
      const J = joins[i];
      const s = J.dpsi >= 0 ? 1 : -1;
      J.t0 = t;
      if (J.r > 0 && J.th > 1e-9) {
        const P = [W[i + 1][0] - dOut * h[0], W[i + 1][1] - dOut * h[1]];
        const nR = [Math.cos(psi), -Math.sin(psi)];
        const C = [P[0] + s * J.r * nR[0], P[1] + s * J.r * nR[1]];
        const w = v[i] / J.r; // the turn's actual rate, rad/s
        const dur2 = J.th / w;
        pieces.push({ kind: "arc", join: J.j, t0: t, t1: t + dur2, C, r: J.r, s, psi0: psi, w, speed: v[i] });
        t += dur2;
      }
      J.t1 = t;
      J.rate_dps = J.r > 0 && J.th > 1e-9 ? v[i] / J.r / DEG : Infinity;
    }
  }
  return { pieces, joins, end: t, W };
}

// state at time t (clamped to the path): {x, y, vx, vy} in metres and m/s
export function stateAt(path, t) {
  const ps = path.pieces;
  let p = ps[ps.length - 1];
  if (t <= ps[0].t0) p = ps[0];
  else {
    // binary search over pieces
    let lo = 0, hi = ps.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (ps[mid].t1 < t) lo = mid + 1;
      else hi = mid;
    }
    p = ps[lo];
  }
  const tt = Math.min(Math.max(t, p.t0), p.t1);
  const dt = tt - p.t0;
  // beyond the path's end the vessel keeps its last leg's velocity
  const extra = t > path.end ? t - path.end : 0;
  if (p.kind === "line") {
    return { x: p.p0[0] + p.vel[0] * (dt + extra), y: p.p0[1] + p.vel[1] * (dt + extra), vx: p.vel[0], vy: p.vel[1] };
  }
  const psi = p.psi0 + p.s * p.w * dt;
  const nR = [Math.cos(psi), -Math.sin(psi)];
  const h = heading(psi);
  return { x: p.C[0] - p.s * p.r * nR[0] + p.speed * h[0] * extra, y: p.C[1] - p.s * p.r * nR[1] + p.speed * h[1] * extra, vx: p.speed * h[0], vy: p.speed * h[1] };
}

// polyline of the path for drawing (metres), about one point per `step` seconds on arcs
export function pathPoints(path, step = 2) {
  const out = [];
  for (const p of path.pieces) {
    const n = p.kind === "arc" ? Math.max(2, Math.ceil((p.t1 - p.t0) / step)) : 1;
    for (let k = 0; k <= n; k++) {
      const s = stateAt(path, p.t0 + ((p.t1 - p.t0) * k) / n);
      out.push([s.x, s.y]);
    }
  }
  return out;
}

// polyline of the path between times a and e (metres): straight pieces by their ends, arcs every
// `step` seconds, so turns draw round at any zoom
export function pathPointsBetween(path, a, e, step = 2) {
  const out = [];
  const push = (t) => {
    const s = stateAt(path, t);
    out.push([s.x, s.y]);
  };
  push(a);
  for (const p of path.pieces) {
    const t0 = Math.max(p.t0, a), t1 = Math.min(p.t1, e);
    if (t1 <= t0) continue;
    if (p.kind === "arc") {
      const n = Math.max(2, Math.ceil((t1 - t0) / step));
      for (let k = 1; k <= n; k++) push(t0 + ((t1 - t0) * k) / n);
    } else push(t1);
  }
  return out;
}

// manoeuvres of a path: [{t0, t1, course, speed}] (a speed change alone is instantaneous)
export function manoeuvres(path) {
  return path.joins.filter((J) => J.courseChange || J.speedChange).map((J) => ({ t0: J.t0, t1: J.t1, course: J.courseChange, speed: J.speedChange, clamped: J.clamped }));
}

// ---------- edits (all return a new track) ----------

const copy = (track) => ({ ...track, legs: track.legs.map((l) => ({ ...l })) });
const legFrom = (a, b, duration_s) => {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  return { course_deg: wrap360(Math.atan2(dx, dy) / DEG), speed_kt: (Math.hypot(dx, dy) / duration_s) * 3600.0 };
};

// FR-002: move waypoint j (1..L) to (x, y) NM; adjacent legs keep their durations, downstream
// waypoints stay put. Waypoint 0 (the start) moves the whole track.
// keep: "time" keeps each adjacent leg's duration (its speed changes); "speed" (spec 036 follow-up, the page's
// waypoint drag) keeps each adjacent leg's speed, so its duration follows its new length (a leg at
// rest keeps its duration).
export function moveWaypoint(track, j, x, y, keep = "time") {
  const out = copy(track);
  if (j === 0) {
    out.start_x_nm = x;
    out.start_y_nm = y;
    return out;
  }
  const W = waypoints(track);
  W[j] = [x, y];
  for (const i of [j - 1, j]) {
    if (i < 0 || i >= out.legs.length) continue;
    let dur = out.legs[i].duration_s;
    if (keep === "speed" && out.legs[i].speed_kt > 0) {
      const lenNm = Math.hypot(W[i + 1][0] - W[i][0], W[i + 1][1] - W[i][1]);
      dur = Math.min(43200, Math.max(1, (lenNm / out.legs[i].speed_kt) * 3600.0));
    }
    Object.assign(out.legs[i], legFrom(W[i], W[i + 1], dur), { duration_s: dur });
  }
  return out;
}

// FR-003: set leg i's course and speed; every downstream leg turns by the same angle, so the
// downstream track moves and rotates rigidly with the leg's end (decision 10).
export function setLegVelocity(track, i, course_deg, speed_kt) {
  const out = copy(track);
  const dc = course_deg - out.legs[i].course_deg;
  out.legs[i].course_deg = wrap360(course_deg);
  out.legs[i].speed_kt = Math.max(0, Math.min(40, speed_kt));
  for (let k = i + 1; k < out.legs.length; k++) out.legs[k].course_deg = wrap360(out.legs[k].course_deg + dc);
  return out;
}

// the velocity handle of leg i sits at its midpoint (NM)
export function handleOf(track, i) {
  const W = waypoints(track);
  return [(W[i][0] + W[i + 1][0]) / 2, (W[i][1] + W[i + 1][1]) / 2];
}

// course and speed for leg i with its handle dragged to (x, y) NM
export function velocityFromHandle(track, i, x, y) {
  const W = waypoints(track);
  return legFrom(W[i], [2 * x - W[i][0], 2 * y - W[i][1]], track.legs[i].duration_s);
}

// FR-004: split leg i at fraction f of its duration
export function insertWaypoint(track, i, f) {
  const out = copy(track);
  const leg = out.legs[i];
  const a = { ...leg, duration_s: Math.max(1, Math.round(leg.duration_s * f)) };
  const b = { ...leg, duration_s: Math.max(1, leg.duration_s - a.duration_s) };
  out.legs.splice(i, 1, a, b);
  return out;
}

// FR-004: delete waypoint j (1..L-1): legs j-1 and j become one leg between their outer ends
export function deleteWaypoint(track, j) {
  if (j < 1 || j >= track.legs.length) return track;
  const out = copy(track);
  const W = waypoints(track);
  const T = out.legs[j - 1].duration_s + out.legs[j].duration_s;
  const merged = { ...out.legs[j], duration_s: T, ...legFrom(W[j - 1], W[j + 1], T) };
  out.legs.splice(j - 1, 2, merged);
  return out;
}

export function setTurnRate(track, i, rate) {
  const out = copy(track);
  out.legs[i].turn_rate_dps = Math.max(0.25, Math.min(3, rate));
  return out;
}

export function setLegField(track, i, field, value) {
  const out = copy(track);
  out.legs[i][field] = value;
  return out;
}

// nearest point on a track's legs (polyline of waypoints) to (x, y) NM: {leg, f, dist}
export function nearestOnLegs(track, x, y) {
  const W = waypoints(track);
  let best = null;
  for (let i = 0; i < W.length - 1; i++) {
    const [ax, ay] = W[i], [bx, by] = W[i + 1];
    const dx = bx - ax, dy = by - ay;
    const L2 = dx * dx + dy * dy;
    const f = L2 > 0 ? Math.min(Math.max(((x - ax) * dx + (y - ay) * dy) / L2, 0), 1) : 0;
    const d = Math.hypot(ax + f * dx - x, ay + f * dy - y);
    if (!best || d < best.dist) best = { leg: i, f, dist: d };
  }
  return best;
}
