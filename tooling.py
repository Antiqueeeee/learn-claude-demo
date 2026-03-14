import json
from typing import Any, Callable, Dict

from tools.docs import search_docs
from tools.fx import fx_convert
from tools.units import unit_convert

def load_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "search_docs",
                "description": "Search internal docs by query.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fx_convert",
                "description": (
                    "Convert currency using ONLY adjacent pairs on a fixed path: "
                    "USD->JPY->KRW->VND->IDR. "
                    "Direct non-adjacent conversions are not supported."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Amount in from_currency."
                        },
                        "from_currency": {
                            "type": "string",
                            "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                            "description": "Source currency code."
                        },
                        "to_currency": {
                            "type": "string",
                            "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                            "description": "Target currency code (must be adjacent to from_currency on the path)."
                        },
                    },
                    "required": ["amount", "from_currency", "to_currency"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "unit_convert",
                "description": "Convert units (length/weight/temperature).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number"},
                        "from_unit": {"type": "string"},
                        "to_unit": {"type": "string"},
                    },
                    "required": ["value", "from_unit", "to_unit"],
                    "additionalProperties": False,
                },
            },
        },
    ]

# 白名单注册表（关键：不要用 globals()/eval 动态执行）
TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "search_docs": search_docs,
    "fx_convert": fx_convert,
    "unit_convert": unit_convert,
}

def run_tool(name: str, arguments_json: str) -> Any:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")

    args = json.loads(arguments_json) if arguments_json and isinstance(arguments_json, str) else arguments_json

    return TOOL_REGISTRY[name](**args)
