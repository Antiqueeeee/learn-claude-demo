# tools/units.py
from __future__ import annotations

def unit_convert(value: float, from_unit: str, to_unit: str):
    fu = _norm(from_unit)
    tu = _norm(to_unit)

    # 温度单独处理（非线性）
    if fu in TEMP_UNITS and tu in TEMP_UNITS:
        c = to_celsius(value, fu)
        out = from_celsius(c, tu)
        return {
            "category": "temperature",
            "value": value, "from_unit": from_unit,
            "result": out, "to_unit": to_unit,
        }

    # 线性单位：长度/重量
    if fu in LENGTH_TO_M and tu in LENGTH_TO_M:
        base = value * LENGTH_TO_M[fu]      # -> meters
        out = base / LENGTH_TO_M[tu]
        return {
            "category": "length",
            "value": value, "from_unit": from_unit,
            "result": out, "to_unit": to_unit,
        }

    if fu in MASS_TO_KG and tu in MASS_TO_KG:
        base = value * MASS_TO_KG[fu]       # -> kilograms
        out = base / MASS_TO_KG[tu]
        return {
            "category": "weight",
            "value": value, "from_unit": from_unit,
            "result": out, "to_unit": to_unit,
        }

    raise ValueError(f"Incompatible or unknown units: {from_unit} -> {to_unit}")


def _norm(u: str) -> str:
    return u.strip().lower().replace(" ", "")

# ---- Length (to meters)
LENGTH_TO_M = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,

    "cm": 0.01,
    "mm": 0.001,
    "km": 1000.0,

    "in": 0.0254,
    "inch": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "yd": 0.9144,
    "yard": 0.9144,
    "mi": 1609.344,
    "mile": 1609.344,
}

# ---- Mass (to kilograms)
MASS_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "pound": 0.45359237,
    "oz": 0.028349523125,
}

# ---- Temperature
TEMP_UNITS = {"c", "°c", "celsius", "f", "°f", "fahrenheit", "k", "kelvin"}

def to_celsius(v: float, unit: str) -> float:
    u = _norm(unit)
    if u in {"c", "°c", "celsius"}:
        return v
    if u in {"f", "°f", "fahrenheit"}:
        return (v - 32.0) * 5.0 / 9.0
    if u in {"k", "kelvin"}:
        return v - 273.15
    raise ValueError(f"Unknown temperature unit: {unit}")

def from_celsius(c: float, unit: str) -> float:
    u = _norm(unit)
    if u in {"c", "°c", "celsius"}:
        return c
    if u in {"f", "°f", "fahrenheit"}:
        return c * 9.0 / 5.0 + 32.0
    if u in {"k", "kelvin"}:
        return c + 273.15
    raise ValueError(f"Unknown temperature unit: {unit}")
