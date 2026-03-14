# AGENTS.md

This repository is a small Python project that demonstrates an agent loop calling
whitelisted tools via the OpenAI SDK.

If you are an agentic coding assistant working in this repo, follow this file.

## Project Layout

- `main.py`: example entrypoint that calls `modes.the_agent_loop.naive_run()`
- `modes/the_agent_loop.py`: streaming chat loop + tool-call plumbing
- `tooling.py`: tool specs (`load_tools`) + tool whitelist/runner (`TOOL_REGISTRY`, `run_tool`)
- `engines/llmEngine.py`: OpenAI client wrapper (`llm_engine`)
- `engines/configEngine.py`: settings loaded from `.env` via `pydantic-settings`
- `tools/`: local tools (`fx_convert`, `unit_convert`, `search_docs`)

## Setup

- Python: repo currently runs on Python 3.13 (see `python -V`).
- Environment:
  - `.vscode/settings.json` suggests using conda.
  - `.env` is used at runtime; do not commit secrets.

Required `.env` variables (see `engines/configEngine.py`):

- `LLM_DEFAULT_BASE_URL`
- `LLM_DEFAULT_API_KEY`

Optional (used with `getattr` in `engines/llmEngine.py`):

- `LLM_DEFAULT_TIMEOUT` (seconds)
- `LLM_DEFAULT_MAX_RETRIES`

## Commands (Build / Lint / Test)

There is no dedicated build system checked in (no `pyproject.toml`, `pytest.ini`,
`Makefile`, etc.). Use the commands below.

### Run

- Run the example program: `python main.py`

### “Build” (syntax/type sanity)

- Fast syntax check (compiles all modules): `python -m compileall -q .`

### Tests

No tests are currently present, but `unittest` discovery works.

- Run all unittest tests (if/when added): `python -m unittest discover -v`
- Run a single unittest test (recommended pattern):
  - By dotted path: `python -m unittest -v tests.test_module.TestClass.test_name`

If the repo later adopts pytest (not currently configured), typical equivalents:

- All tests: `pytest -q`
- Single file: `pytest -q tests/test_module.py`
- Single test: `pytest -q tests/test_module.py::test_name`
- Match by substring: `pytest -q -k "name_substring"`

### Lint / Format

No lint/format tooling is configured in-repo. If you add tooling, prefer:

- Ruff (lint + import sorting): `ruff check .` and `ruff check . --fix`
- Black (format): `black .`
- Mypy/pyright (types): `mypy .` or `pyright`

When adding these, also add config + a short section here with exact commands.

## Code Style Guidelines

### Imports

- Group imports in this order, with a blank line between groups:
  1) stdlib
  2) third-party
  3) local (`engines.*`, `modes.*`, `tools.*`)
- Avoid wildcard imports.
- Prefer explicit imports from local modules (as done in `tooling.py`).

### Formatting

- Use 4-space indentation.
- Prefer double quotes for JSON-like keys/strings; keep it consistent per file.
- Keep lines reasonably short; wrap long strings with parentheses.
- Use f-strings for interpolation.

### Types

- Add type hints for public functions and any non-trivial internal helpers.
- Prefer `from __future__ import annotations` for modules that define many hints
  (already used in multiple files).
- Use `Any` only at integration boundaries (LLM responses, JSON blobs, SDK
  payloads). Narrow types as soon as practical.
- For JSON-like structures, use `dict[str, Any]` / `list[dict[str, Any]]` on
  Python 3.9+.

### Naming

- Modules/files: `snake_case.py`
- Functions/vars: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` (see `MAX_LOOPS`, `RATES`)

### Error Handling

- Raise `ValueError` for invalid user/tool inputs, with a clear message that
  includes the failing values and the allowed/expected shape.
- Do not silently swallow exceptions. If you must catch, either:
  - re-raise with context, or
  - return a structured error object (the agent loop already wraps tool errors
    into `{"error": ...}` tool responses).
- Keep exception scopes tight (catch only what you can handle).

### Logging / Printing

- The code currently uses `print()` for debugging (payload and loop dumps).
- If you introduce logging, prefer `logging` and keep debug logs behind a flag.
- Never print secrets (API keys, full `.env` contents).

## Tooling and Agent Loop Conventions

- Tools must be whitelisted in `tooling.py` (`TOOL_REGISTRY`).
  - Do not use `globals()`, `eval`, dynamic imports, or arbitrary execution.
- Keep tool argument schemas strict:
  - Set `additionalProperties: False` in tool JSON schema (already done).
  - Validate and normalize inputs in tool functions (see `fx_convert`).
- Tool outputs should be JSON-serializable dicts with stable keys.

### Streaming / Resource Safety

- When iterating `chat_stream()`, always close the stream if a `close()` method
  exists (already done in `modes/the_agent_loop.py`). Keep that pattern.
- When assembling tool call arguments from streamed chunks, treat arguments as
  incremental text and only parse JSON at the end (already done).

## Security / Secrets

- `.env` contains secrets; do not commit it or paste it into logs.
- When adding documentation or examples, use placeholder values.

## Cursor / Copilot Rules

- No Cursor rules found (`.cursor/rules/` or `.cursorrules`).
- No Copilot instructions found (`.github/copilot-instructions.md`).

If these are added later, copy the relevant constraints into this file and
prioritize them when they conflict with generic guidance.
