from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from agent_tools.loader import load_builtin_tools
from agent_tools.registry import ToolRegistry


def _registry(*, include_disabled: bool = False) -> ToolRegistry:
    return ToolRegistry(load_builtin_tools(include_disabled=include_disabled))


def load_tools(
    provider: str = "openai",
    model: str | None = None,
) -> list[dict[str, Any]]:
    if provider != "openai":
        raise ValueError(f"Unsupported provider: {provider}")

    registry = _registry()
    return [
        tool.to_provider_format(provider, model=model)
        for tool in registry.list_tools()
    ]


def _coerce_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, str):
        if not arguments:
            raise ValueError("Tool arguments payload is required")
        parsed = json.loads(arguments)
        if not isinstance(parsed, dict):
            raise ValueError("Tool arguments JSON must decode to an object")
        return parsed

    if arguments is None:
        raise ValueError("Tool arguments payload is required")

    if isinstance(arguments, Mapping):
        return dict(arguments)

    raise ValueError("Tool arguments must be a JSON object string or mapping")


def run_tool(name: str, arguments: Any) -> Any:
    registry = _registry()
    args = _coerce_arguments(arguments)
    return registry.execute(name, args)
