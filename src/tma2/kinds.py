"""Target manoeuvre kinds (schema ``ManoeuvreKind``) and what each one changes.

A small module (NumPy only), so evaluation code can classify kinds without importing the generator
or the batch kernels. Codes match the generator's manoeuvre table (``TM_KIND``)."""

from __future__ import annotations

from typing import Any

import numpy as np

KIND_COURSE = 0
KIND_SPEED = 1
KIND_BOTH = 2  # generator 0.6.0: a turn and a speed change at once
KIND_NAMES = ("course", "speed", "both")
KIND_CODES = {name: code for code, name in enumerate(KIND_NAMES)}


def kind_name(kind: object) -> str:
    """The schema name of a kind given as a name, an enum member or its repr."""
    return str(getattr(kind, "value", kind)).split(".")[-1]


def is_turn_kind(kind: object) -> bool:
    """A manoeuvre that changes course: "course", or generator 0.6.0's "both" (a code, a name or
    an enum member)."""
    if isinstance(kind, int | np.integer):
        return int(kind) in (KIND_COURSE, KIND_BOTH)
    return kind_name(kind) in ("course", "both")


def is_speed_kind(kind: object) -> bool:
    """A manoeuvre that changes speed: "speed", or generator 0.6.0's "both" (a code, a name or an
    enum member)."""
    if isinstance(kind, int | np.integer):
        return int(kind) in (KIND_SPEED, KIND_BOTH)
    return kind_name(kind) in ("speed", "both")


def manoeuvre_table(plan: list[dict[str, Any]]) -> np.ndarray:
    """The generator's manoeuvre table [M, 6] (kind code, start_time_s, change, rate, change2,
    rate2) from a scenario's ``parameters.target_manoeuvres``; change2/rate2 are 0 except for
    "both"."""
    rows = [
        [
            float(KIND_CODES[kind_name(m["kind"])]),
            float(m["start_time_s"]),
            float(m["change"]),
            float(m["rate"]),
            float(m.get("change2") or 0.0),
            float(m.get("rate2") or 0.0),
        ]
        for m in plan
    ]
    return np.array(rows, dtype=np.float64).reshape(len(rows), 6)
