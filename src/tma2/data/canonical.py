"""Canonical JSON: sorted keys, no whitespace, JavaScript number formatting.

gitma writes every record with ``JSON.stringify`` and sorted keys
(``packages/data/src/canonical.ts``), so a file written here must be byte-identical to gitma's for
the same record. Python's ``repr`` gives the same shortest round-trip digits as ECMAScript
``Number::toString``; only the layout differs (integral doubles, exponent thresholds and exponent
spelling), which ``js_number`` fixes.

``canonical_json`` is a general recursive serialiser; ``scenario_json`` is the fast path for the
scenario record shape (hundreds of states per scenario), built from templates.
"""

from __future__ import annotations

import json
import math
from typing import Any


def js_number(x: float) -> str:
    """Format a finite double as ECMAScript ``Number.prototype.toString()`` would."""
    if math.isnan(x) or math.isinf(x):
        raise ValueError("JSON cannot hold NaN or infinity")
    if x == 0:
        return "0"
    r = repr(float(x))
    sign = ""
    if r.startswith("-"):
        sign = "-"
        r = r[1:]
    if "e" in r:
        mant, exp_s = r.split("e")
        exp = int(exp_s)
    else:
        mant, exp = r, 0
    if "." in mant:
        int_part, frac_part = mant.split(".")
    else:
        int_part, frac_part = mant, ""
    stripped_int = int_part.lstrip("0")
    if stripped_int:
        n = len(stripped_int) + exp
    else:
        n = exp - (len(frac_part) - len(frac_part.lstrip("0")))
    digits = (int_part + frac_part).lstrip("0").rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    e = n - 1
    exp_str = ("+" if e >= 0 else "-") + str(abs(e))
    if k == 1:
        return sign + digits + "e" + exp_str
    return sign + digits[0] + "." + digits[1:] + "e" + exp_str


def _fast_float(x: float) -> str:
    """``js_number`` with a fast path for the common positional cases."""
    r = repr(x)
    if r.endswith(".0"):
        return r[:-2] if r != "-0.0" else "0"
    if "e" in r:
        return js_number(x)
    return r


def _ser(value: Any, out: list[str]) -> None:
    if value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif value is None:
        out.append("null")
    elif isinstance(value, int):
        out.append(str(value))
    elif isinstance(value, float):
        out.append(js_number(value))
    elif isinstance(value, str):
        out.append(json.dumps(value, ensure_ascii=False))
    elif isinstance(value, dict):
        out.append("{")
        first = True
        for k in sorted(value):
            if not first:
                out.append(",")
            first = False
            out.append(json.dumps(str(k), ensure_ascii=False))
            out.append(":")
            _ser(value[k], out)
        out.append("}")
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for i, v in enumerate(value):
            if i:
                out.append(",")
            _ser(v, out)
        out.append("]")
    else:
        raise TypeError(f"cannot canonicalise {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Serialise ``value`` (dicts, lists, str, int, float, bool, None) canonically."""
    out: list[str] = []
    _ser(value, out)
    return "".join(out)


def _num(v: Any) -> str:
    return str(v) if isinstance(v, int) else _fast_float(v)


def scenario_json(record: dict[str, Any]) -> str:
    """Canonical JSON of a scenario record dict, by template (same bytes as ``canonical_json``)."""
    states = []
    for key in ("ownship", "target"):
        rows = record[key]["states"]
        states.append(
            ",".join(
                "{"
                f'"course_rad":{_num(s["course_rad"])},'
                f'"speed_mps":{_num(s["speed_mps"])},'
                f'"timestamp_s":{_num(s["timestamp_s"])},'
                f'"x_m":{_num(s["x_m"])},'
                f'"y_m":{_num(s["y_m"])}'
                "}"
                for s in rows
            )
        )
    obs = ",".join(
        "{"
        f'"bearing_rad":{_num(o["bearing_rad"])},'
        f'"timestamp_s":{_num(o["timestamp_s"])},'
        f'"valid":{"true" if o["valid"] else "false"}'
        "}"
        for o in record["observations"]
    )
    return (
        '{"metadata":'
        + canonical_json(record["metadata"])
        + ',"observations":['
        + obs
        + '],"ownship":{"id":"ownship","states":['
        + states[0]
        + ']},"record":"scenario","target":{"id":"target","states":['
        + states[1]
        + "]}}"
    )


def _num_list(values: list[float]) -> list[str]:
    return [_fast_float(v) for v in values]


def scenario_json_arrays(metadata: dict[str, Any], own: Any, tgt: Any, obs: Any) -> str:
    """``scenario_json`` from float arrays own/tgt [S, 5] (t, x, y, course, speed), obs [S, 3].

    The arrays hold float32-rounded values as float64 (or float32, converted exactly).
    """
    parts: list[str] = []
    for a in (own, tgt):
        cols = [_num_list(c) for c in a.T.astype("float64").tolist()]
        t_s, x_s, y_s, c_s, v_s = cols
        parts.append(
            ",".join(
                '{"course_rad":'
                + c
                + ',"speed_mps":'
                + v
                + ',"timestamp_s":'
                + t
                + ',"x_m":'
                + x
                + ',"y_m":'
                + y
                + "}"
                for t, x, y, c, v in zip(t_s, x_s, y_s, c_s, v_s, strict=True)
            )
        )
    ocols = obs.T.astype("float64").tolist()
    ot, ob = _num_list(ocols[0]), _num_list(ocols[1])
    ov = ["true" if v != 0 else "false" for v in ocols[2]]
    obs_s = ",".join(
        '{"bearing_rad":' + b + ',"timestamp_s":' + t + ',"valid":' + v + "}"
        for t, b, v in zip(ot, ob, ov, strict=True)
    )
    return (
        '{"metadata":'
        + canonical_json(metadata)
        + ',"observations":['
        + obs_s
        + '],"ownship":{"id":"ownship","states":['
        + parts[0]
        + ']},"record":"scenario","target":{"id":"target","states":['
        + parts[1]
        + "]}}"
    )
