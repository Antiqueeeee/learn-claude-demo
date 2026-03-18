# Tool System Design

**Goal:** Replace the current hard-coded tool JSON list and function registry with a more extensible tool system that supports explicit registration now and richer selection/formatting strategies later.

## Current Problem

Today `tooling.py` mixes several responsibilities:

1. Tool metadata definition (`name`, `description`, JSON schema)
2. Tool registration (`TOOL_REGISTRY`)
3. OpenAI-style tool formatting
4. Tool dispatch by name

This is workable for a few tools, but it will become awkward as the project evolves into multiple agent-loop versions (`v1`, `v2`, `v3`, etc.) with different tool exposure strategies.

## Requirements

- Keep the current project simple and understandable.
- Support explicit tool registration as the default behavior.
- Allow different loop versions to load different tool sets.
- Avoid hard-coding OpenAI tool JSON inside every loading path.
- Preserve a clean execution path for `run_tool(name, args)`.
- Leave room for future directory scanning, filtering, and progressive disclosure.
- Maintain a clear whitelist boundary; do not weaken safety with uncontrolled dynamic execution.

## Recommended Architecture

Split the current tooling concerns into four layers.

### 1. Tool Definition Layer

Each tool should be represented as a structured object or class with a uniform internal shape.

Suggested fields:

- `name`
- `description`
- `input_schema`
- `tags`
- `enabled_by_default`
- `run(**kwargs)`

Optional future fields:

- `risk_level`
- `visible_to_model`
- `stage`
- `version`

This layer defines what a tool is, not when or why it should be exposed.

### 2. Tool Registry Layer

A central registry should:

- register tool instances explicitly
- retrieve tools by name
- execute a tool by name and args
- list all registered tools
- support filtered views of tools

This keeps the whitelist explicit and auditable.

### 3. Tool Formatter Layer

The internal tool definition should be converted into provider-specific structures by dedicated formatters.

Examples:

- OpenAI formatter
- future Anthropic formatter
- future custom/internal formatter

This avoids binding the core tool abstraction to one provider's schema format.

### 4. Tool Selection Layer

Different loop versions should decide which tools to expose by policy.

Examples:

- fixed allowlist for early loop versions
- tag-based filtering
- stage-based exposure
- future progressive disclosure

This keeps selection logic separate from tool definition and tool execution.

## Recommended Directory Shape

A new top-level tool system directory is appropriate because tools are now a core architectural concept, not just helper functions.

Example:

```text
agent_tools/
  __init__.py
  base.py
  registry.py
  formatters.py
  selectors.py
  builtins/
    __init__.py
    search_docs.py
    fx_convert.py
    unit_convert.py
```

Suggested responsibilities:

- `base.py`: base tool abstraction
- `registry.py`: explicit registration, lookup, execution
- `formatters.py`: provider-specific formatting
- `selectors.py`: tool-loading policies for loop versions
- `builtins/`: concrete tool implementations

## Compatibility Strategy

Do not force all loop versions to change immediately.

Instead, keep `tooling.py` as a compatibility façade:

- `load_tools()` → get selected tools from the registry, then format them for OpenAI
- `run_tool()` → delegate to registry execution

This lets existing loop files continue to work while the internals evolve.

## Why Explicit Registration First

Explicit registration is the right first step because it preserves a strong safety boundary and makes debugging straightforward.

Benefits:

- clear whitelist
- predictable tool exposure
- easier debugging
- lower accidental risk
- supports per-version selection immediately

Future directory scanning can be added later, but it should not replace explicit control until the project genuinely needs it.

## Future Extensions

Once the base architecture exists, the project can add:

- controlled directory scanning
- tag-based filtering
- risk-based filtering
- progressive disclosure
- provider-specific formatting for more LLM backends

The important constraint is that discovery must not automatically imply exposure.

## Non-Goals for the First Refactor

- building a full plugin framework
- automatic loading of every file in a directory
- supporting every LLM provider immediately
- mixing loop-state policy into the base tool abstraction

## Recommended First Implementation Step

Start with a minimal refactor:

1. Introduce a base tool abstraction.
2. Convert the three existing tools into tool objects/classes.
3. Add a registry with explicit registration.
4. Add an OpenAI formatter only.
5. Keep `tooling.py` as a compatibility layer.

This delivers immediate architectural improvement without over-engineering.

## Success Criteria

- Adding a new tool no longer requires hand-writing raw tool JSON in `tooling.py`.
- Loop versions can choose different tool-loading strategies without redefining every tool.
- The whitelist remains explicit.
- Existing loop code can continue to function with minimal changes.
- The architecture leaves clear extension points for filtering and progressive disclosure.
