"""L's training loss: the semi-Markov likelihood of the truth segmentation (spec 005 FR-042,
research R6).

The lattice is the search's (``search.py``): legs on grid points [grid[i], grid[j]] of at least
L_min rows, transitions of ``t_min`` … ``t_max`` rows between legs, and the prefix may end inside
a transition. A segmentation's score is −½ × the search's cost:

    Σ_legs (−½ cost[i, j] + Σ_leg e)
      + Σ_trans (−½ trans_cost · n_valid − Σ_trans e) − ½ penalty · (legs − 1)

so the most probable segmentation is the search's answer and the evidence e (per row, the
log-likelihood ratio of steady against transition) enters linearly. The loss is
log Z − score(truth path), with Z the sum over all lattice segmentations (a log-sum-exp forward
recursion). Both terms are differentiable in e; at e = 0 the gradient is the difference between
the model's expected per-row labels and the truth path's, generally non-zero (SC-003).

The **truth path** is the lattice segmentation that agrees with the most truth-labelled rows
(rows the truth marks unknown are ignored) and, among those, scores best at zero evidence; found
by the same recursion with max-plus on (agreement, score) pairs.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import Tensor

from . import STEADY, TRANSITION

NEG = -1e30  # log of an impossible configuration (finite, so gradients stay finite)


def _cum(x: Tensor) -> Tensor:
    return torch.cat([x.new_zeros(1), torch.cumsum(x, 0)])


class Lattice:
    """Precomputed lattice for one prefix: grid, finite legs, transitions and their fixed
    scores (from the cost table, bearings' validity and the penalty)."""

    def __init__(
        self,
        grid: np.ndarray,
        cost: np.ndarray,
        valid: np.ndarray,
        penalty: float,
        t_min: int,
        t_max: int,
        trans_cost: float = 1.0,
    ) -> None:
        g = int(grid.shape[0])
        self.g = g
        self.grid = [int(x) for x in grid]
        last = self.grid[-1]
        cv = np.concatenate([[0.0], np.cumsum(valid[: last + 1].astype(np.float64))])
        # legs: (i, j, −½ cost)
        self.legs: list[tuple[int, int, float]] = [
            (i, j, -0.5 * float(cost[i, j]))
            for i in range(g)
            for j in range(i + 1, g)
            if math.isfinite(cost[i, j])
        ]
        # transitions between a leg ending at p and one starting at i: rows grid[p]+1 … grid[i]−1
        self.trans: list[tuple[int, int, float]] = []
        for i in range(1, g):
            for p in range(i):
                gap = self.grid[i] - self.grid[p] - 1
                if t_min <= gap <= t_max:
                    nt = cv[self.grid[i]] - cv[self.grid[p] + 1]
                    self.trans.append((p, i, -0.5 * (trans_cost * nt + penalty)))
        # open endings after a leg ending at p: rows grid[p]+1 … last
        self.open: list[tuple[int, float]] = []
        for p in range(g - 1):
            gap = last - self.grid[p]
            if t_min <= gap <= t_max:
                nt = cv[last + 1] - cv[self.grid[p] + 1]
                self.open.append((p, -0.5 * (trans_cost * nt + penalty)))
        self.trans_into: dict[int, list[tuple[int, float]]] = {}
        for p, i, s in self.trans:
            self.trans_into.setdefault(i, []).append((p, s))
        self.legs_into: dict[int, list[tuple[int, float]]] = {}
        for i, j, s in self.legs:
            self.legs_into.setdefault(j, []).append((i, s))

    def _leg_e(self, ce: Tensor, i: int, j: int) -> Tensor:
        return ce[self.grid[j] + 1] - ce[self.grid[i]]

    def _trans_e(self, ce: Tensor, p: int, i: int) -> Tensor:
        return ce[self.grid[i]] - ce[self.grid[p] + 1]

    def _index(self) -> None:
        """Per grid point j, the legs and transitions ending there as index arrays (built once,
        on first use)."""
        if hasattr(self, "_legs_j"):
            return
        gr = np.asarray(self.grid, dtype=np.int64)
        self._legs_j: dict[int, tuple[Tensor, Tensor, Tensor, Tensor]] = {}
        for j, lst in self.legs_into.items():
            i = np.array([x for x, _ in lst], dtype=np.int64)
            self._legs_j[j] = (
                torch.as_tensor(i),
                torch.as_tensor(np.array([v for _, v in lst])),
                torch.as_tensor(gr[i]),
                torch.as_tensor(i == 0),
            )
        self._trans_j: dict[int, tuple[Tensor, Tensor, Tensor]] = {}
        for j, lst in self.trans_into.items():
            q = np.array([x for x, _ in lst], dtype=np.int64)
            self._trans_j[j] = (
                torch.as_tensor(q),
                torch.as_tensor(np.array([v for _, v in lst])),
                torch.as_tensor(gr[q] + 1),
            )

    def log_partition(self, evidence: Tensor) -> Tensor:
        """log Z over every lattice segmentation of [0, grid[−1]] (vectorised over the legs and
        transitions ending at each grid point)."""
        self._index()
        ce = _cum(evidence)
        last = self.grid[-1]
        neg = evidence.new_full((), NEG)
        alpha: list[Tensor] = [neg] * self.g  # log-sum over segmentations with a leg ending at j
        beta: list[Tensor] = [neg] * self.g  # … with a transition ending just before grid[i]
        for j in range(1, self.g):
            if j in self._trans_j:
                q, s, r0 = self._trans_j[j]
                al = torch.stack(alpha[:j])[q]
                beta[j] = torch.logsumexp(al + s - (ce[self.grid[j]] - ce[r0]), 0)
            if j in self._legs_j:
                i, s, r0, first = self._legs_j[j]
                be = torch.stack(beta[:j])[i]
                base = torch.where(first, torch.zeros_like(be), be)
                alpha[j] = torch.logsumexp(base + s + ce[self.grid[j] + 1] - ce[r0], 0)
        ends = [alpha[self.g - 1]]
        for p, s_ in self.open:
            ends.append(alpha[p] + s_ - (ce[last + 1] - ce[self.grid[p] + 1]))
        z = torch.logsumexp(torch.stack(ends), 0)
        if float(z.detach()) < NEG / 2:
            raise ValueError("no lattice segmentation covers the prefix")
        return z

    def log_partition_reference(self, evidence: Tensor) -> Tensor:
        """The unvectorised recursion (documentation of record; tests compare the two)."""
        ce = _cum(evidence)
        last = self.grid[-1]
        alpha: dict[int, Tensor] = {}
        beta: dict[int, Tensor] = {}
        for j in range(1, self.g):
            tb = [
                alpha[p] + s - self._trans_e(ce, p, j)
                for p, s in self.trans_into.get(j, [])
                if p in alpha
            ]
            if tb:
                beta[j] = torch.logsumexp(torch.stack(tb), 0)
            terms = []
            for i, s in self.legs_into.get(j, []):
                le = s + self._leg_e(ce, i, j)
                if i == 0:
                    terms.append(le)
                elif i in beta:
                    terms.append(beta[i] + le)
            if terms:
                alpha[j] = torch.logsumexp(torch.stack(terms), 0)
        ends = [alpha[self.g - 1]] if self.g - 1 in alpha else []
        for p, s in self.open:
            if p in alpha:
                ends.append(alpha[p] + s - (ce[last + 1] - ce[self.grid[p] + 1]))
        if not ends:
            raise ValueError("no lattice segmentation covers the prefix")
        return torch.logsumexp(torch.stack(ends), 0)

    def path_score(self, legs: list[tuple[int, int]], open_end: bool, evidence: Tensor) -> Tensor:
        """The score of the segmentation given as legs (grid indices, in order); with
        ``open_end`` the prefix ends in a transition after the last leg."""
        ce = _cum(evidence)
        last = self.grid[-1]
        leg_s = {(i, j): s for i, j, s in self.legs}
        tr_s = {(p, i): s for p, i, s in self.trans}
        op_s = dict(self.open)
        total = evidence.new_zeros(())
        for q, (i, j) in enumerate(legs):
            total = total + leg_s[(i, j)] + self._leg_e(ce, i, j)
            if q > 0:
                p = legs[q - 1][1]
                total = total + tr_s[(p, i)] - self._trans_e(ce, p, i)
        if open_end:
            p = legs[-1][1]
            total = total + op_s[p] - (ce[last + 1] - ce[self.grid[p] + 1])
        return total

    def truth_path(self, codes: np.ndarray) -> tuple[list[tuple[int, int]], bool]:
        """The lattice segmentation agreeing with the most truth-labelled rows; among those, the
        one with the best score at zero evidence (max-plus, compared lexicographically). Rows
        the truth marks unknown (before the zig, short legs) are then decided by the cost, not
        by the order of the recursion."""
        last = self.grid[-1]
        st = np.concatenate([[0], np.cumsum(codes[: last + 1] == STEADY)])
        tr = np.concatenate([[0], np.cumsum(codes[: last + 1] == TRANSITION)])
        g = self.g
        ninf = (-np.inf, -np.inf)
        a: list[tuple[float, float]] = [ninf] * g
        a_back: list[tuple[int, int] | None] = [None] * g  # (leg start i, previous leg end p or −1)
        b: list[tuple[float, float]] = [ninf] * g
        b_back = np.full(g, -1, dtype=np.int64)
        for j in range(1, g):
            for p, s in self.trans_into.get(j, []):
                v = (a[p][0] + float(tr[self.grid[j]] - tr[self.grid[p] + 1]), a[p][1] + s)
                if v > b[j]:
                    b[j], b_back[j] = v, p
            for i, s in self.legs_into.get(j, []):
                le = float(st[self.grid[j] + 1] - st[self.grid[i]])
                v = (le, s) if i == 0 else (b[i][0] + le, b[i][1] + s)
                if v > a[j]:
                    a[j] = v
                    a_back[j] = (i, -1 if i == 0 else int(b_back[i]))
        best, end_p = a[-1], -1
        for p, s in self.open:
            v = (a[p][0] + float(tr[last + 1] - tr[self.grid[p] + 1]), a[p][1] + s)
            if v > best:
                best, end_p = v, p
        if not np.isfinite(best[0]):
            raise ValueError("no lattice segmentation covers the prefix")
        legs: list[tuple[int, int]] = []
        j = end_p if end_p >= 0 else g - 1
        while j >= 0:
            bk = a_back[j]
            assert bk is not None
            legs.append((bk[0], j))
            j = bk[1]
        legs.reverse()
        return legs, end_p >= 0

    def nll(self, evidence: Tensor, codes: np.ndarray) -> Tensor:
        legs, open_end = self.truth_path(codes)
        return self.log_partition(evidence) - self.path_score(legs, open_end, evidence)


def aux_loss(evidence: Tensor, codes: np.ndarray, rows: int) -> Tensor:
    """Per-bearing auxiliary term (R6, weight 0.1 in the plan): binary cross-entropy of
    σ(e) against steady on truth-labelled rows ≤ ``rows`` − 1."""
    c = torch.as_tensor(codes[:rows])
    known = (c == STEADY) | (c == TRANSITION)
    if not bool(known.any()):
        return evidence.new_zeros(())
    target = (c[known] == STEADY).to(evidence.dtype)
    return torch.nn.functional.binary_cross_entropy_with_logits(evidence[:rows][known], target)
