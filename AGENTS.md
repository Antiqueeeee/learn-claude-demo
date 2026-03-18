# AGENTS.md

This file is for agentic coding assistants working in this repository.

Follow these repository-specific instructions when they conflict with generic
assistant habits.

## Scope and Intent

- Small Python repository demonstrating an agent loop that calls a whitelist of
  local tools through an LLM client.
- Keep changes small and easy to inspect.
- Prefer improving existing files over adding new abstractions unless clearly needed.

## Repository Layout

- `main.py`: entrypoint calling `modes.the_agent_loop.naive_run()`
- `modes/the_agent_loop.py`: streaming agent loop, tool-call assembly, and loop control
- `tooling.py`: tool schema definitions, whitelist registry, and tool dispatch
- `engines/llmEngine.py`: LLM client wrapper
- `engines/configEngine.py`: environment/config loading
- `tools/`: local tools for currency conversion, unit conversion, and docs search
- `docs/plans/`: design notes and implementation plans

## Environment and Setup

- The repo is plain Python without checked-in `pyproject.toml`, `pytest.ini`,
  `setup.cfg`, `Makefile`, or package manager lockfile.
- Python in this workspace is expected to be 3.13.
- Runtime configuration comes from environment variables loaded via `.env`.
- `.env.example` may be used as a non-secret reference if present.

## Run / Build / Test Commands

### Run

- `python main.py`

### Build / Syntax Sanity

- There is no formal build pipeline in-repo.
- Fast whole-repo syntax check: `python -m compileall -q .`

### Tests

- No automated tests are currently checked in.
- If tests are added with `unittest`, run all tests with:
  - `python -m unittest discover -v`

### Run a Single Test

- Preferred pattern: `python -m unittest -v tests.test_module.TestClass.test_name`
- Single module: `python -m unittest -v tests.test_module`
- Single class: `python -m unittest -v tests.test_module.TestClass`

Do not assume `pytest` is configured unless its dependency and config are added.

## Lint / Format / Type Check Status

- No lint, formatter, or static type checker is currently configured in-repo.
- Do not claim that `ruff`, `black`, `mypy`, `pyright`, or `pytest` are project
  standards unless their config or dependencies are added.

## Code Style Guidelines

### Imports

- Group imports in this order: standard library, third-party packages, local
  modules.
- Separate groups with a blank line when there are multiple groups.
- Prefer explicit imports over wildcard imports.
- Keep local imports direct.

### Formatting

- Use 4-space indentation.
- Match the surrounding file's style if it already exists.
- Keep lines reasonably short; wrap long literals with parentheses.
- Prefer clarity over clever formatting.
- Preserve readable JSON and dict literals when editing tool schemas.

### Types

- Add type hints for public functions and non-trivial helpers you touch.
- Use `Any` only at dynamic boundaries such as LLM payloads, tool arguments, and
  JSON-like responses.
- Narrow loose data to clearer shapes as soon as practical.

### Naming

- Modules and files: `snake_case.py`
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Use descriptive names that reflect tool behavior and loop state.

### Error Handling

- Raise clear exceptions for invalid tool names, invalid arguments, or invalid user input.
- Prefer `ValueError` for validation failures when the caller supplied a bad value.
- Keep exception scopes tight.
- Do not silently swallow exceptions.
- If catching an exception to return structured data, return stable keys in a
  JSON-serializable dict.

### Logging and Debug Output

- The current code uses `print()` for loop/debug output.
- Avoid adding noisy debug output unless it is directly useful.
- Never print secrets, tokens, API keys, or raw `.env` contents.

## Agent-Specific Repository Rules

### Tool Registry and Execution

- Only call tools that are explicitly whitelisted in `tooling.py`.
- Do not introduce `eval`, `globals()`, arbitrary dynamic imports, or other
  non-whitelisted execution paths.
- Tool outputs should stay JSON-serializable and use stable field names.

### Tool Schema Discipline

- Keep tool parameter schemas strict.
- Preserve `additionalProperties: False` for function tool schemas unless there
  is a strong repo-specific reason to change it.
- Validate and normalize incoming tool arguments in the tool implementation.

### Streaming Loop Conventions

- Accumulate streamed tool-call argument chunks and parse JSON only after the
  full argument string is assembled.
- Preserve the assistant/tool message ordering expected by tool-calling APIs.
- Keep loop termination behavior explicit and bounded by safety limits.

## Security and Secrets

- Treat `.env` as sensitive.
- **Do not read `.env` contents unless the user explicitly asks and gives a
  clear reason.**
- Do not quote, summarize, log, print, or copy `.env` values into output, docs,
  commit messages, or debugging notes.
- If you need to understand configuration keys, inspect:
  - `engines/configEngine.py`
  - `.env.example`
- When discussing configuration, refer to variable names only, never real values.
- Do not commit secrets or credentials.

## Docs and Planning

- Put new design or implementation plans under `docs/plans/`.
- Prefer concise documentation that helps the next agent act correctly.

## Cursor / Copilot Rules

- No Cursor rules were found in `.cursor/rules/`.
- No `.cursorrules` file was found.
- No Copilot instructions were found in `.github/copilot-instructions.md`.
- If any of those files are added later, incorporate their repo-specific
  constraints into this document and follow the more specific rule.

## Practical Defaults for Agents

- Before making code changes, inspect the relevant file and preserve local style.
- Prefer minimal patches over broad refactors.
- Validate syntax with `python -m compileall -q .` after non-trivial edits.
- If tests are added, run the narrowest relevant test first, then broader checks.
