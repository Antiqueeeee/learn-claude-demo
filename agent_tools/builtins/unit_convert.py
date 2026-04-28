from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.units import unit_convert as unit_convert_impl


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

    def run(self, **kwargs: Any) -> Any:
        return unit_convert_impl(**kwargs)


TOOL = UnitConvertTool()
