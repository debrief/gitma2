# Usage: uv run python scripts/research/g2_zig_veto_tables.py <dir with tval/ tstream/ (tma2-dtables shards of results/dtables-g2-val-tune-42288137249 and results/dtables-g2-stream-42295008170) and runs/<model>/best.safetensors (results/g2-g2-a-42352638177)> <seed 314 validation.f32pack> <seed 318 train.f32pack>
"""Panel round 1, geometry major: does a classical rule (threshold shift b everywhere, +tau/2 veto
for candidates within W rows of the ownship zig) match E-s on its own objective (hard loss on
decision tables)? Tuned on the tuning tables, checked on the stream tables."""
import glob, json, sys
from pathlib import Path
import numpy as np, torch
from safetensors.torch import load_file
torch.set_default_dtype(torch.float64)
from tma2.gate2.tables import load_tables
from tma2.gate2.es import example_of, ESSettings, make_net, forward, shifts
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment.evidence import scenario_features
from tma2.segment.score import iter_selected
from tma2.types.generated.tma import SegmentParameters

S = Path(sys.argv[1]); R = Path('/home/user/gitma2')
p = SegmentParameters.model_validate(json.loads((R/'configs/segment/gs-plan.json').read_text())['segmenter']['parameters'])
plan = json.loads((R/'configs/gate2/g2-a.json').read_text())
TAU = 13.8

def load(tabdir, pack, start, count, feats_needed):
    tabs = {}
    for f in sorted(glob.glob(str(tabdir)+'/shard-*.npz')):
        _, t = load_tables(f); tabs.update(t)
    xs, zig = [], {}
    for j, m, own, tgt, obs in iter_selected(str(pack), start, count):
        if j not in tabs: continue
        zig[j] = int(m['zig_index'])
        f = scenario_features(bearing_data_from_arrays(m, own, obs), own, p) if feats_needed else np.zeros((1, own.shape[0]))
        xs.append(example_of(j, f, tabs[j]))
    return xs, zig

def arrays(xs, zig):
    M = np.concatenate([x.margin for x in xs]); W = np.concatenate([x.e_with for x in xs]); O = np.concatenate([x.e_without for x in xs])
    s = np.concatenate([x.start for x in xs]); e = np.concatenate([x.end for x in xs])
    z = np.concatenate([np.full(x.start.size, zig[x.ordinal]) for x in xs])
    return M, W, O, s, e, z

def rule_loss(M, W, O, s, e, z, b, Wz):
    near = (s <= z + Wz) & (e >= z - Wz)
    sh = np.where(near, TAU/2, b)
    return np.where(M - sh > 0, W, O).mean()

def es_loss(xs, name):
    net = make_net(ESSettings(**{**plan['es'], 'seed': 1}), xs[0].feats.shape[0])
    net.load_state_dict(load_file(str(S/'runs'/name/'best.safetensors'))); net.eval()
    sh, M, W, O = [], [], [], []
    with torch.no_grad():
        for i in range(0, len(xs), 16):
            part = [x for x in xs[i:i+16] if x.start.size]
            if not part: continue
            for ev, x in zip(forward(net, part), part):
                sh.append(shifts(ev, x).numpy()); M.append(x.margin); W.append(x.e_with); O.append(x.e_without)
    sh, M, W, O = map(np.concatenate, (sh, M, W, O))
    return np.where(M - sh > 0, W, O).mean()

grid_b = [-TAU/2, -TAU/4, 0.0, TAU/4]
grid_w = [-1, 0, 3, 6, 12, 24]  # -1: no veto
for label, tabdir, pack, a, c, feats in [('tuning', S/'tval', sys.argv[2], 0, 500, True), ('stream', S/'tstream', sys.argv[3], 0, 9930, False)]:
    xs, zig = load(tabdir, pack, a, c, feats)
    M, W, O, s, e, z = arrays(xs, zig)
    print(f'{label}: {len(xs)} scenarios, {M.size} decision rows; C (no shift) {np.where(M>0,W,O).mean():.4f}')
    for b in grid_b:
        print('  b=%+.2f ' % b + ' '.join(f'W{w}:{(np.where(M-b>0,W,O).mean() if w<0 else rule_loss(M,W,O,s,e,z,b,w)):.4f}' for w in grid_w))
    if feats:
        for n in ['es-s1', 'es-s2', 'es-s3', 'es-shuffled']:
            print(f'  {n}: {es_loss(xs, n):.4f}')
