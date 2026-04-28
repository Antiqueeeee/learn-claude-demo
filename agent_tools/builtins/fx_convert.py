from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.fx import fx_convert as fx_convert_impl


class FxConvertTool(BaseTool):
    name = "fx_convert"
    description = (
        "Convert currency using ONLY adjacent pairs on a fixed path: "
        "USD->JPY->KRW->VND->IDR. "
        "Direct non-adjacent conversions are not supported."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Amount in from_currency.",
            },
            "from_currency": {
                "type": "string",
                "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                "description": "Source currency code.",
            },
            "to_currency": {
                "type": "string",
                "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                "description": (
                    "Target currency code (must be adjacent to from_currency on the path)."
                ),
            },
        },
        "required": ["amount", "from_currency", "to_currency"],
        "additionalProperties": False,
    }

    def run(self, **kwargs: Any) -> Any:
        return fx_convert_impl(**kwargs)


TOOL = FxConvertTool()
