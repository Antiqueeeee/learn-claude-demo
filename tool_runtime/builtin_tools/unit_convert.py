from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool

LENGTH_TO_METERS = {
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

MASS_TO_KILOGRAMS = {
    "kg": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "pound": 0.45359237,
    "oz": 0.028349523125,
}

TEMPERATURE_UNITS = {"c", "°c", "celsius", "f", "°f", "fahrenheit", "k", "kelvin"}


class UnitConvertTool(BaseTool):
    name = "unit_convert"
    description = "Convert units (length/weight/temperature)."
    input_schema = {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
            },
            "from_unit": {
                "type": "string",
            },
            "to_unit": {
                "type": "string",
            },
        },
        "required": ["value", "from_unit", "to_unit"],
        "additionalProperties": False,
    }

    def run(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        normalized_from = _normalize_unit(from_unit)
        normalized_to = _normalize_unit(to_unit)

        if (
            normalized_from in TEMPERATURE_UNITS
            and normalized_to in TEMPERATURE_UNITS
        ):
            celsius = _to_celsius(value, normalized_from)
            return {
                "category": "temperature",
                "value": value,
                "from_unit": from_unit,
                "result": _from_celsius(celsius, normalized_to),
                "to_unit": to_unit,
            }

        if normalized_from in LENGTH_TO_METERS and normalized_to in LENGTH_TO_METERS:
            base_value = value * LENGTH_TO_METERS[normalized_from]
            return {
                "category": "length",
                "value": value,
                "from_unit": from_unit,
                "result": base_value / LENGTH_TO_METERS[normalized_to],
                "to_unit": to_unit,
            }

        if normalized_from in MASS_TO_KILOGRAMS and normalized_to in MASS_TO_KILOGRAMS:
            base_value = value * MASS_TO_KILOGRAMS[normalized_from]
            return {
                "category": "weight",
                "value": value,
                "from_unit": from_unit,
                "result": base_value / MASS_TO_KILOGRAMS[normalized_to],
                "to_unit": to_unit,
            }

        raise ValueError(f"Incompatible or unknown units: {from_unit} -> {to_unit}")


def _normalize_unit(unit: str) -> str:
    return unit.strip().lower().replace(" ", "")


def _to_celsius(value: float, unit: str) -> float:
    if unit in {"c", "°c", "celsius"}:
        return value
    if unit in {"f", "°f", "fahrenheit"}:
        return (value - 32.0) * 5.0 / 9.0
    if unit in {"k", "kelvin"}:
        return value - 273.15
    raise ValueError(f"Unknown temperature unit: {unit}")


def _from_celsius(value: float, unit: str) -> float:
    if unit in {"c", "°c", "celsius"}:
        return value
    if unit in {"f", "°f", "fahrenheit"}:
        return value * 9.0 / 5.0 + 32.0
    if unit in {"k", "kelvin"}:
        return value + 273.15
    raise ValueError(f"Unknown temperature unit: {unit}")


TOOL = UnitConvertTool()
