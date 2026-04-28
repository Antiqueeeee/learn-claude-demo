from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from typing import Any

from agent_tools.base import BaseTool


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

    def list_tools(self) -> list[BaseTool]:
        return [copy.deepcopy(tool) for tool in self._tools]

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
