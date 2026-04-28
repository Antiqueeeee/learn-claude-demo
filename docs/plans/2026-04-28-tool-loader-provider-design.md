# Tool Loader And Provider Design

**Goal:** Replace the hard-coded tool list in `tooling.py` with a structured tool system built around a shared base class, directory-based loading, and provider-specific formatting.

## Current Problem

Today `tooling.py` combines four separate responsibilities:

1. Declaring tool metadata
2. Formatting tools for OpenAI
3. Registering whitelisted tool call targets
4. Dispatching tool execution by name

That works for three tools, but it makes the next step awkward:

- adding new tools still requires editing central hard-coded JSON
- provider-specific tool formatting has no extension point
- load-time enablement rules do not exist yet

## Requirements

- Keep the repository simple and easy to inspect
- Preserve the whitelist boundary for executable tools
- Move tool metadata and behavior into tool classes
- Support provider-specific tool formatting
- Default to OpenAI formatting only
- Load tools by rule instead of hard-coding a central list
- Allow tools to be enabled or disabled without changing the loop code
- Keep `tooling.py` as a compatibility layer for existing callers

## Recommended Architecture

### 1. Base Tool Abstraction

Add a `BaseTool` class under `agent_tools/base.py`.

Each concrete tool instance should expose:

- `name`
- `description`
- `input_schema`
- `enabled`
- `run(**kwargs)`
- `to_provider_format(provider: str, model: str | None = None)`

The internal abstraction is provider-agnostic. It represents a tool once, then formats it on demand for the caller's model provider.

### 2. Concrete Tool Modules

Move built-in tools into `agent_tools/builtins/`.

Each module should define exactly one module-level export:

```python
TOOL = SearchDocsTool()
```

This makes discovery explicit without maintaining a central hard-coded tool list.

The existing implementation functions in `tools/` may stay in place. Concrete tool classes can delegate to those functions instead of duplicating business logic.

### 3. Directory-Based Loader

Add a loader that scans `agent_tools/builtins/` and collects tools using the following rules:

- scan only `.py` files in that directory
- skip `__init__.py`
- import each module
- require a module-level `TOOL`
- require `TOOL` to be a `BaseTool` instance
- reject duplicate tool names
- return only enabled tools by default

This provides rule-based loading without introducing uncontrolled execution. Discovery is constrained to a fixed package and a fixed export name.

### 4. Registry Layer

Add a registry responsible for:

- loading discovered tools
- indexing them by name
- retrieving tools by name
- executing enabled tools by name

`run_tool(name, args)` should delegate to this registry so the agent loop keeps a stable execution API.

### 5. Provider Formatting

Provider conversion should be driven by a single method:

```python
to_provider_format(provider: str, model: str | None = None) -> dict[str, Any]
```

The first implementation only needs OpenAI support.

`BaseTool` should provide:

- `to_provider_format(...)` as the public dispatch method
- `_to_openai_format()` as the default OpenAI conversion

If a future provider or model needs special handling, a concrete tool may override `to_provider_format(...)` or a provider-specific helper. The `model` parameter should exist now even if the first version does not branch on it yet.

## Loading And Enablement Rules

The initial enablement mechanism should stay simple:

- each tool instance has `enabled: bool = True` by default
- normal loading returns only enabled tools
- loader may optionally support `include_disabled=True` for inspection use cases
- registry execution should reject disabled tools

This prevents a mismatch where a tool is hidden from the model but still executable through the dispatcher.

## Compatibility Strategy

Keep `tooling.py` as a façade for existing code.

- `load_tools(provider="openai", model=None)` should load enabled tools and convert them to provider format
- `run_tool(name, arguments)` should delegate to the new registry

This keeps `modes/the_agent_loop.py` changes minimal or unnecessary.

## Recommended Directory Shape

```text
agent_tools/
  __init__.py
  base.py
  loader.py
  registry.py
  builtins/
    __init__.py
    search_docs.py
    fx_convert.py
    unit_convert.py
```

## Non-Goals

- automatic loading from arbitrary directories
- plugin installation
- immediate support for multiple providers
- model-specific branching in the first implementation
- large changes to the current agent loop

## Success Criteria

- adding a tool means creating a built-in tool module with a `TOOL` export
- `tooling.py` no longer contains raw hard-coded OpenAI tool JSON for each tool
- tools can be enabled or disabled centrally through tool instances
- the system can format tools for OpenAI through a provider-facing API
- existing loop code can keep using `load_tools()` and `run_tool()`
