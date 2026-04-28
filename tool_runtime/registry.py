from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.loader import load_builtin_tools


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool]):
        self._tools = list(tools)
        self._tools_by_name: dict[str, BaseTool] = {}

        for tool in self._tools:
            if tool.name in self._tools_by_name:
                raise ValueError(f"Duplicate tool name: {tool.name}")
            self._tools_by_name[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools_by_name[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name}") from exc

    def format_tools(
        self,
        *,
        provider: str,
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        return [
            tool.to_provider_format(provider, model=model)
            for tool in self._tools
        ]

    def execute(self, name: str, args: Mapping[str, Any]) -> Any:
        tool = self.get(name)
        if not tool.enabled:
            raise ValueError(f"Disabled tool: {name}")

        normalized_args = self._normalize_args(args)
        return tool.run(**normalized_args)

    @staticmethod
    def _normalize_args(args: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(args, Mapping):
            raise ValueError("Tool arguments must be a mapping")

        normalized_args = dict(args)
        for key in normalized_args:
            if not isinstance(key, str):
                raise ValueError("Tool argument keys must be strings")

        return normalized_args


def build_builtin_registry(*, include_disabled: bool = False) -> ToolRegistry:
    return ToolRegistry(load_builtin_tools(include_disabled=include_disabled))
