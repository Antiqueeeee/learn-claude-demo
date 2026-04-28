# Tool Loader And Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hard-coded tool list and function registry in `tooling.py` with a class-based tool system that loads built-in tools by module rule and formats them for OpenAI through a provider-facing interface.

**Architecture:** Introduce a new `agent_tools/` package containing a `BaseTool` abstraction, a directory loader, and a registry. Keep the existing `tools/` functions as the execution backend for now, and keep `tooling.py` as a compatibility façade that loads enabled tools and dispatches execution through the registry.

**Tech Stack:** Python 3.13, standard library (`abc`, `importlib`, `pathlib`, `unittest`), existing local tool functions, OpenAI-style function tools.

---

## File Map

- Create: `agent_tools/__init__.py`
  Expose the public registry and loading helpers used by `tooling.py`.
- Create: `agent_tools/base.py`
  Define the provider-agnostic `BaseTool` contract and default OpenAI formatter.
- Create: `agent_tools/loader.py`
  Scan `agent_tools/builtins/`, import tool modules, validate `TOOL`, and filter by `enabled`.
- Create: `agent_tools/registry.py`
  Provide lookup and execution for loaded tool instances.
- Create: `agent_tools/builtins/__init__.py`
  Mark the built-ins directory as a package.
- Create: `agent_tools/builtins/search_docs.py`
  Wrap `tools.docs.search_docs` in a `BaseTool` subclass.
- Create: `agent_tools/builtins/fx_convert.py`
  Wrap `tools.fx.fx_convert` in a `BaseTool` subclass.
- Create: `agent_tools/builtins/unit_convert.py`
  Wrap `tools.units.unit_convert` in a `BaseTool` subclass.
- Modify: `tooling.py`
  Replace hard-coded tool JSON and callable registry with delegating compatibility helpers.
- Create: `tests/test_tooling.py`
  Cover tool formatting, loader behavior, registry execution, and compatibility façade behavior.

### Task 1: Add regression tests for the new tool abstraction and compatibility façade

**Files:**
- Create: `tests/test_tooling.py`

- [ ] **Step 1: Write the failing test file**

```python
import unittest

from tooling import load_tools, run_tool


class ToolingCompatibilityTests(unittest.TestCase):
    def test_load_tools_returns_openai_function_tools(self) -> None:
        tools = load_tools()

        self.assertIsInstance(tools, list)
        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            {"search_docs", "fx_convert", "unit_convert"},
        )
        self.assertTrue(all(tool["type"] == "function" for tool in tools))

    def test_run_tool_executes_registered_tool(self) -> None:
        result = run_tool(
            "unit_convert",
            {"value": 1, "from_unit": "m", "to_unit": "cm"},
        )

        self.assertEqual(result["category"], "length")
        self.assertEqual(result["result"], 100.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify the starting point**

Run: `python -m unittest -v tests.test_tooling`

Expected: PASS on the compatibility tests, confirming the current public behavior before refactoring.

- [ ] **Step 3: Extend the test file with failing tests for the new abstraction**

```python
from agent_tools.base import BaseTool
from agent_tools.loader import load_builtin_tools
from agent_tools.registry import ToolRegistry


class DummyTool(BaseTool):
    name = "dummy"
    description = "Dummy tool"
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def run(self, **kwargs):
        return {"ok": True, "kwargs": kwargs}


class ToolingArchitectureTests(unittest.TestCase):
    def test_base_tool_formats_for_openai(self) -> None:
        tool = DummyTool()

        formatted = tool.to_provider_format("openai", model="gpt-5.2")

        self.assertEqual(formatted["type"], "function")
        self.assertEqual(formatted["function"]["name"], "dummy")
        self.assertFalse(formatted["function"]["parameters"]["additionalProperties"])

    def test_loader_discovers_enabled_builtin_tools(self) -> None:
        tools = load_builtin_tools()

        self.assertEqual(
            {tool.name for tool in tools},
            {"search_docs", "fx_convert", "unit_convert"},
        )

    def test_registry_executes_loaded_tool(self) -> None:
        registry = ToolRegistry(load_builtin_tools())

        result = registry.execute(
            "search_docs",
            {"query": "agent loop"},
        )

        self.assertEqual(result["query"], "agent loop")

    def test_registry_rejects_disabled_tool_execution(self) -> None:
        tool = DummyTool()
        tool.enabled = False
        registry = ToolRegistry([tool])

        with self.assertRaises(ValueError):
            registry.execute("dummy", {})
```

- [ ] **Step 4: Run the tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL with `ModuleNotFoundError: No module named 'agent_tools'`.

- [ ] **Step 5: Commit the red test scaffold**

```bash
git add tests/test_tooling.py
git commit -m "test: add tool system regression coverage"
```

### Task 2: Implement the base tool abstraction with OpenAI formatting

**Files:**
- Create: `agent_tools/__init__.py`
- Create: `agent_tools/base.py`
- Test: `tests/test_tooling.py`

- [ ] **Step 1: Implement the package export**

```python
from agent_tools.base import BaseTool

__all__ = ["BaseTool"]
```

- [ ] **Step 2: Implement `agent_tools/base.py`**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    input_schema: ClassVar[dict[str, Any]]
    enabled: bool = True

    def to_provider_format(
        self,
        provider: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        if provider == "openai":
            return self._to_openai_format()
        raise ValueError(f"Unsupported tool provider: {provider}")

    def _to_openai_format(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
```

- [ ] **Step 3: Run the focused tests**

Run: `python -m unittest -v tests.test_tooling.ToolingArchitectureTests.test_base_tool_formats_for_openai`

Expected: FAIL because loader and registry modules still do not exist, but the import error should move past `agent_tools.base`.

- [ ] **Step 4: Commit the base abstraction**

```bash
git add agent_tools/__init__.py agent_tools/base.py
git commit -m "feat: add base tool abstraction"
```

### Task 3: Implement built-in tool wrappers and directory loading

**Files:**
- Create: `agent_tools/builtins/__init__.py`
- Create: `agent_tools/builtins/search_docs.py`
- Create: `agent_tools/builtins/fx_convert.py`
- Create: `agent_tools/builtins/unit_convert.py`
- Create: `agent_tools/loader.py`
- Test: `tests/test_tooling.py`

- [ ] **Step 1: Implement the built-ins package marker**

```python
__all__ = []
```

- [ ] **Step 2: Implement `agent_tools/builtins/search_docs.py`**

```python
from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.docs import search_docs


class SearchDocsTool(BaseTool):
    name = "search_docs"
    description = "Search internal docs by query."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    }

    def run(self, **kwargs: Any) -> Any:
        return search_docs(**kwargs)


TOOL = SearchDocsTool()
```

- [ ] **Step 3: Implement `agent_tools/builtins/fx_convert.py`**

```python
from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.fx import fx_convert


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
        return fx_convert(**kwargs)


TOOL = FxConvertTool()
```

- [ ] **Step 4: Implement `agent_tools/builtins/unit_convert.py`**

```python
from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.units import unit_convert


class UnitConvertTool(BaseTool):
    name = "unit_convert"
    description = "Convert units (length/weight/temperature)."
    input_schema = {
        "type": "object",
        "properties": {
            "value": {"type": "number"},
            "from_unit": {"type": "string"},
            "to_unit": {"type": "string"},
        },
        "required": ["value", "from_unit", "to_unit"],
        "additionalProperties": False,
    }

    def run(self, **kwargs: Any) -> Any:
        return unit_convert(**kwargs)


TOOL = UnitConvertTool()
```

- [ ] **Step 5: Implement `agent_tools/loader.py`**

```python
from __future__ import annotations

import importlib
from pathlib import Path

from agent_tools.base import BaseTool


BUILTINS_PACKAGE = "agent_tools.builtins"
BUILTINS_DIR = Path(__file__).with_name("builtins")


def load_builtin_tools(*, include_disabled: bool = False) -> list[BaseTool]:
    tools: list[BaseTool] = []
    seen_names: set[str] = set()

    for path in sorted(BUILTINS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue

        module = importlib.import_module(f"{BUILTINS_PACKAGE}.{path.stem}")
        tool = getattr(module, "TOOL", None)
        if tool is None:
            raise ValueError(f"Built-in tool module missing TOOL: {module.__name__}")
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Built-in tool module has invalid TOOL: {module.__name__}")
        if tool.name in seen_names:
            raise ValueError(f"Duplicate tool name: {tool.name}")
        seen_names.add(tool.name)
        if include_disabled or tool.enabled:
            tools.append(tool)

    return tools
```

- [ ] **Step 6: Run the loader tests**

Run: `python -m unittest -v tests.test_tooling.ToolingArchitectureTests.test_loader_discovers_enabled_builtin_tools`

Expected: PASS

- [ ] **Step 7: Commit the built-in wrappers and loader**

```bash
git add agent_tools/builtins/__init__.py agent_tools/builtins/search_docs.py agent_tools/builtins/fx_convert.py agent_tools/builtins/unit_convert.py agent_tools/loader.py
git commit -m "feat: load built-in tools from modules"
```

### Task 4: Implement the registry and compatibility façade

**Files:**
- Create: `agent_tools/registry.py`
- Modify: `tooling.py`
- Test: `tests/test_tooling.py`

- [ ] **Step 1: Implement `agent_tools/registry.py`**

```python
from __future__ import annotations

from typing import Any, Iterable

from agent_tools.base import BaseTool


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool]):
        self._tools = {tool.name: tool for tool in tools}

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def execute(self, name: str, args: dict[str, Any]) -> Any:
        tool = self.get(name)
        if not tool.enabled:
            raise ValueError(f"Tool is disabled: {name}")
        return tool.run(**args)
```

- [ ] **Step 2: Replace `tooling.py` with a compatibility façade**

```python
from __future__ import annotations

from typing import Any

from agent_tools.loader import load_builtin_tools
from agent_tools.registry import ToolRegistry


def _registry(*, include_disabled: bool = False) -> ToolRegistry:
    return ToolRegistry(load_builtin_tools(include_disabled=include_disabled))


def load_tools(provider: str = "openai", model: str | None = None) -> list[dict[str, Any]]:
    return [
        tool.to_provider_format(provider, model=model)
        for tool in _registry().list_tools()
    ]


def run_tool(name: str, arguments: dict[str, Any]) -> Any:
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise ValueError(f"Tool arguments must be a dict for {name}")
    return _registry(include_disabled=True).execute(name, arguments)
```

- [ ] **Step 3: Run the full test module**

Run: `python -m unittest -v tests.test_tooling`

Expected: PASS

- [ ] **Step 4: Run a syntax sanity check**

Run: `python -m compileall -q .`

Expected: no output

- [ ] **Step 5: Commit the integration layer**

```bash
git add agent_tools/registry.py tooling.py
git commit -m "refactor: route tooling through tool registry"
```

### Task 5: Keep the loop compatible and tighten the regression coverage

**Files:**
- Modify: `tests/test_tooling.py`
- Optional Modify: `modes/the_agent_loop.py`

- [ ] **Step 1: Add an explicit provider argument regression test**

```python
    def test_load_tools_accepts_provider_and_model(self) -> None:
        tools = load_tools(provider="openai", model="gpt-5.2")

        self.assertEqual(len(tools), 3)
        self.assertEqual(tools[0]["type"], "function")
```

- [ ] **Step 2: Add an unsupported provider regression test**

```python
    def test_load_tools_rejects_unsupported_provider(self) -> None:
        with self.assertRaises(ValueError):
            load_tools(provider="anthropic", model="claude-sonnet-4")
```

- [ ] **Step 3: Only modify `modes/the_agent_loop.py` if needed**

```python
stream = llm_handler.chat_stream(
    model=model,
    messages=messages,
    tools=load_tools(provider="openai", model=model),
)
```

Expected: no behavioral change; only add the explicit arguments if that makes the callsite clearer.

- [ ] **Step 4: Run the full regression suite again**

Run: `python -m unittest discover -v`

Expected: PASS

- [ ] **Step 5: Commit the final regression tightening**

```bash
git add tests/test_tooling.py modes/the_agent_loop.py
git commit -m "test: cover provider-based tool loading"
```

## Self-Review

- Spec coverage:
  The plan covers `BaseTool`, `TOOL` module export scanning, `enabled` filtering, OpenAI-only provider formatting, and `tooling.py` compatibility. No spec section is left without a task.
- Placeholder scan:
  No `TODO`, `TBD`, or implicit “handle edge cases” steps remain. Every code-writing step includes concrete file content.
- Type consistency:
  The same names are used throughout: `BaseTool`, `load_builtin_tools`, `ToolRegistry`, `to_provider_format`, `load_tools`, `run_tool`, and `enabled`.
