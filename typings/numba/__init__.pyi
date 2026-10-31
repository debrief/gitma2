"""Minimal numba stubs for mypy --strict (numba ships none). Only what tma2 uses."""

from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

def njit(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...
def prange(*args: int) -> range: ...
def get_num_threads() -> int: ...
def set_num_threads(n: int) -> None: ...

uint32: Any
uint64: Any
int64: Any
float64: Any
boolean: Any
