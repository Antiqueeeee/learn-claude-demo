# Tool System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the repository's tool management from hard-coded JSON and function maps into an extensible tool system with explicit registration, provider formatting, and per-loop selection hooks.

**Architecture:** Introduce a new top-level `agent_tools/` package containing a base tool abstraction, explicit registry, OpenAI formatter, and concrete built-in tools. Keep `tooling.py` as a compatibility façade so existing loop code can continue to call `load_tools()` and `run_tool()` while the internals become structured and extensible.

**Tech Stack:** Python 3.13, standard library, existing local tool functions, OpenAI-style function tools.

---

### Task 1: Add a focused regression test scaffold for tool loading and dispatch

**Files:**
- Create: `tests/test_tooling.py`

**Step 1: Write the failing test for tool loading**

```python
from tooling import load_tools


def test_load_tools_returns_openai_function_tools() -> None:
    tools = load_tools()

    assert isinstance(tools, list)
    assert {tool["function"]["name"] for tool in tools} >= {
        "search_docs",
        "fx_convert",
        "unit_convert",
    }
    assert all(tool["type"] == "function" for tool in tools)
```

**Step 2: Write the failing test for tool dispatch**

```python
from tooling import run_tool


def test_run_tool_executes_registered_tool() -> None:
    result = run_tool("unit_convert", {"value": 1, "from_unit": "m", "to_unit": "cm"})

    assert isinstance(result, dict)
```

**Step 3: Run the test file to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because the `tests/` package or test module does not exist yet, or because assertions need the refactor in place.

### Task 2: Create the base tool abstraction

**Files:**
- Create: `agent_tools/__init__.py`
- Create: `agent_tools/base.py`

**Step 1: Write the failing test for base tool behavior**

Add a test in `tests/test_tooling.py` that defines a tiny dummy subclass and verifies it exposes a standard internal definition.

```python
from agent_tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy"
    description = "Dummy tool"
    input_schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

    def run(self, **kwargs):
        return {"ok": True}


def test_base_tool_exposes_definition() -> None:
    tool = DummyTool()

    assert tool.definition()["name"] == "dummy"
```

**Step 2: Run the specific test and verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because `agent_tools.base` does not exist.

**Step 3: Write minimal base abstraction**

Implement a `BaseTool` class that provides:

- class-level metadata fields (`name`, `description`, `input_schema`)
- optional metadata such as `tags` and `enabled_by_default`
- `definition()` method returning the internal tool representation
- abstract-like `run(**kwargs)` contract

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Base-tool-related tests pass or move to the next missing dependency.

### Task 3: Create the explicit registry

**Files:**
- Create: `agent_tools/registry.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write the failing registry tests**

Add tests covering:

- register tool instance
- lookup by name
- duplicate registration raises `ValueError`
- execution by name routes to the tool

Example:

```python
from agent_tools.registry import ToolRegistry


def test_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    registry.register(DummyTool())

    with self.assertRaises(ValueError):
        registry.register(DummyTool())
```

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because `ToolRegistry` does not exist.

**Step 3: Implement the registry**

Create a registry that supports:

- `register(tool)`
- `get(name)`
- `list_tools()`
- `execute(name, args)`

Keep registration explicit and deterministic.

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Registry tests pass.

### Task 4: Add the OpenAI formatter

**Files:**
- Create: `agent_tools/formatters.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write the failing formatter test**

Add a test verifying that a tool definition is converted to the current OpenAI-style format:

```python
from agent_tools.formatters import format_tool_for_openai


def test_format_tool_for_openai() -> None:
    formatted = format_tool_for_openai(DummyTool())

    assert formatted["type"] == "function"
    assert formatted["function"]["name"] == "dummy"
```

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because formatter does not exist.

**Step 3: Implement formatter**

Add a small function that maps the internal tool definition to the same OpenAI structure that `tooling.py` currently returns.

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Formatter tests pass.

### Task 5: Convert current built-in tools into tool objects

**Files:**
- Create: `agent_tools/builtins/__init__.py`
- Create: `agent_tools/builtins/search_docs.py`
- Create: `agent_tools/builtins/fx_convert.py`
- Create: `agent_tools/builtins/unit_convert.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write failing tests for built-in tool metadata**

Add tests asserting that the converted tools expose the same names and core schema fields as today.

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because built-in tool classes do not exist.

**Step 3: Implement built-in tool classes**

For each existing tool:

- wrap current metadata into a tool class
- delegate execution to the existing underlying function
- preserve current schema semantics

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Built-in tool tests pass.

### Task 6: Add explicit default registration

**Files:**
- Modify: `agent_tools/__init__.py`
- Create or Modify: `agent_tools/defaults.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write the failing test for default registry contents**

Add a test that asks for the default registry and asserts the three current tools are present.

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because there is no default registry builder.

**Step 3: Implement default registration**

Create a function that constructs a registry and explicitly registers:

- `SearchDocsTool()`
- `FxConvertTool()`
- `UnitConvertTool()`

No scanning yet.

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Default-registration tests pass.

### Task 7: Refactor `tooling.py` into a compatibility façade

**Files:**
- Modify: `tooling.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write the failing compatibility tests**

Add tests asserting:

- `load_tools()` still returns a list of OpenAI-style tools
- `run_tool(name, args)` still executes the registered tool
- unknown tool names still raise a clear `ValueError`

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because `tooling.py` still uses the old hard-coded path.

**Step 3: Implement compatibility façade**

Update `tooling.py` so:

- `load_tools()` gets tools from the default registry and formats them through the OpenAI formatter
- `run_tool()` delegates to registry execution

Keep the public function names stable.

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Compatibility tests pass.

### Task 8: Add a simple selection hook for future loop versions

**Files:**
- Create: `agent_tools/selectors.py`
- Modify: `tests/test_tooling.py`

**Step 1: Write the failing selector test**

Add a test for a small helper that filters registry tools by explicit allowlist names.

**Step 2: Run tests to verify failure**

Run: `python -m unittest -v tests.test_tooling`

Expected: FAIL because selector helper does not exist.

**Step 3: Implement minimal selector**

Create a helper such as `select_tools_by_name(registry, names)` that returns tools in a stable order.

This is enough for loop versions to load different tool subsets now, while leaving room for tag- or stage-based policies later.

**Step 4: Re-run tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: Selector tests pass.

### Task 9: Verify repository compatibility

**Files:**
- Modify: `modes/the_agent_loop.py` only if required

**Step 1: Run targeted tests**

Run: `python -m unittest -v tests.test_tooling`

Expected: PASS

**Step 2: Run syntax verification**

Run: `python -m compileall -q .`

Expected: PASS with no syntax errors

**Step 3: Run the existing demo entrypoint**

Run: `python main.py`

Expected: Existing flow still runs using the compatibility `tooling.py` layer

### Task 10: Document follow-up boundaries

**Files:**
- Modify: `docs/plans/2026-03-18-tool-system-design.md` only if design intent needs a tiny clarification after implementation

**Step 1: Record what remains intentionally out of scope**

- directory scanning
- automatic discovery
- progressive disclosure
- non-OpenAI formatters

**Step 2: Keep the first refactor minimal**

Do not add plugin machinery unless a test forces it.
