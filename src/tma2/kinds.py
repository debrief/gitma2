"""Target manoeuvre kinds (schema ``ManoeuvreKind``) and what each one changes.

A small module with no dependencies, so evaluation code can classify kinds without importing the
generator or the batch kernels. Codes match the generator's manoeuvre table (``TM_KIND``)."""

from __future__ import annotations

KIND_COURSE = 0
KIND_SPEED = 1
KIND_BOTH = 2  # generator 0.6.0: a turn and a speed change at once
KIND_NAMES = ("course", "speed", "both")


def is_turn_kind(kind: int | str) -> bool:
    """A manoeuvre that changes course: "course", or generator 0.6.0's "both"."""
    return kind in (KIND_COURSE, KIND_BOTH, "course", "both")


def is_speed_kind(kind: int | str) -> bool:
    """A manoeuvre that changes speed: "speed", or generator 0.6.0's "both"."""
    return kind in (KIND_SPEED, KIND_BOTH, "speed", "both")
