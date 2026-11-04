"""Spec 006 G0-MAN2 panel round 1 (statistics reviewer): the share of *complete* target legs at or
under 10 min that a correct generator 0.6.0 shows inside 40–120 min windows.

Draws the declared law directly (legs N(1500, 546) s clipped at 300 s after a uniform phase;
change kinds 0.8 / 0.1 / 0.1 with the MAN2 turn and speed-change rates) with no kernel, keeps only
legs whose both ends fall inside the window, and prints the share at or under 10 min, the leg
P5 / P50 / P95 in minutes and the share of engagements with two or more changes. Measured on the
gate's data: 7.0%, 8.7 / 23.3 / 38.2 min, 93.5%; this script gives about 6.4% continuous (6.8–6.9%
with the row rounding shown in the first line), 8.9 / 23.5 / 38.2 min, 93.7%.

    uv run python scripts/research/man2_window_bias.py
"""

import numpy as np

rng = np.random.default_rng(1)
N = 200000
legs_all = []
nchg = []
W = rng.uniform(2400, 7200, N)


def dur():
    k = rng.choice(3, p=[0.8, 0.1, 0.1])
    tc = np.radians(rng.uniform(30, 120)) / np.radians(rng.uniform(0.25, 1))
    ts = rng.uniform(1.0289, 3.0867) / rng.uniform(0.01, 0.05)
    return tc if k == 0 else ts if k == 1 else max(tc, ts)


def leg():
    return max(rng.normal(1500, 546), 300)


cnt = []
for i in range(N // 10):
    w = W[i]
    t = rng.uniform(0, leg())
    ends = []
    starts = []
    while t < w:
        d = dur()
        starts.append(t)
        ends.append(t + d)
        t = t + d + leg()
    cnt.append(len(starts))
    for j in range(1, len(starts)):
        if ends[j - 1] < w:
            legs_all.append(starts[j] - ends[j - 1])
x = np.array(legs_all) / 60
print(np.mean(x <= 10 + 15 / 60), np.mean(x <= 10 + 20 / 60))
print(len(x), np.percentile(x, [5, 50, 95]), np.mean(x <= 10), np.mean(np.array(cnt) >= 2))
