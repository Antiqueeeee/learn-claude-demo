from __future__ import annotations

import copy
import importlib
from pathlib import Path

from tool_runtime.base import BaseTool

BUILTIN_TOOLS_PACKAGE = "tool_runtime.builtin_tools"


def load_builtin_tools(*, include_disabled: bool = False) -> list[BaseTool]:
    tools: list[BaseTool] = []
    seen_names: set[str] = set()

    package = importlib.import_module(BUILTIN_TOOLS_PACKAGE)
    package_path = Path(package.__file__).resolve().parent
    module_names = sorted(
        path.stem
        for path in package_path.glob("*.py")
        if path.name != "__init__.py"
    )

    for module_name in module_names:
        module = importlib.import_module(f"{BUILTIN_TOOLS_PACKAGE}.{module_name}")
        tool = getattr(module, "TOOL", None)
        if tool is None:
            raise ValueError(f"Built-in tool module missing TOOL: {module.__name__}")
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Built-in tool module has invalid TOOL: {module.__name__}")
        if tool.name in seen_names:
            raise ValueError(f"Duplicate built-in tool name: {tool.name}")

        seen_names.add(tool.name)
        if include_disabled or tool.enabled:
            tools.append(copy.deepcopy(tool))

    return tools
