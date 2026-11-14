"""``tma2-rtrain``: train the regressor control (spec 012 contracts/cli.md) or, with a
configuration whose ``data`` is "periods", the whole-period model (spec 016). ``--config`` is a
configuration or a plan that carries one."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-rtrain", description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume", help="a directory with state.pt and run.json")
    ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    ap.add_argument("--limit-seconds", type=int)
    a = ap.parse_args(argv)
    from tma2.regress.model import RegressorConfig
    from tma2.regress.train import train

    raw = json.loads(Path(a.config).read_text())
    cfg = RegressorConfig(**raw.get("config", raw))
    rec = train(cfg, Path(a.out), a.device, Path(a.resume) if a.resume else None, a.limit_seconds)
    print(
        f"{rec['stopped']}: {rec['updates']} updates, {rec['scenarios_seen']} {cfg.data}, "
        f"{rec['scenarios_per_second']:.0f} per second"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
