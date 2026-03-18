# AGENTS.md Design

**Goal:** Improve the repository root `AGENTS.md` so agentic coding assistants can work safely and effectively in this codebase using only instructions that reflect the repo's current state.

## Repository facts discovered

- The repo is a small Python project centered on `main.py`, `modes/the_agent_loop.py`, `tooling.py`, `engines/`, and `tools/`.
- A root-level `AGENTS.md` already exists and is exactly the file that should be improved.
- No Cursor rules were found in `.cursor/rules/` or `.cursorrules`.
- No Copilot instructions were found in `.github/copilot-instructions.md`.
- No `pyproject.toml`, `pytest.ini`, `package.json`, `Cargo.toml`, or other build/test config files were found.
- `.env` exists, `.env.example` exists, and `.gitignore` excludes `.env`.

## Scope

The new `AGENTS.md` should:

1. Document build/lint/test commands that are actually supported today.
2. Emphasize how to run a single test, even though no tests are currently checked in.
3. Capture code style conventions inferred from the repository's Python files.
4. Include repo-specific guidance for tool execution, streaming loop behavior, and JSON schema discipline.
5. Include any Cursor or Copilot rules if they exist; otherwise state clearly that none were found.
6. Add a clear security rule that agents must not read `.env` contents by default.

## Recommended approach

Revise the existing root `AGENTS.md` in place rather than replacing it wholesale. Keep the structure practical for agents:

- overview and layout
- setup/environment facts
- commands that work now
- code style rules inferred from code
- tool/loop conventions specific to this repo
- security guidance
- external instruction files status

This approach preserves useful existing content while making the document more explicit, safer, and more actionable.

## Key decisions

- Keep the document strictly descriptive of the current repository state; do not present unconfigured tools as project standards.
- Mention optional future tools only when clearly labeled as absent today, or omit them entirely if they add noise.
- Add an explicit rule: do not read `.env` contents unless the user explicitly requests it and explains why.
- Direct agents to inspect `.env.example` and `engines/configEngine.py` to learn environment variable names instead of reading real secrets.

## Content outline

1. Purpose and scope
2. Project layout
3. Environment and setup notes
4. Build / run / test commands
5. Single-test command patterns
6. Lint/format/type-check status
7. Code style guidelines
   - imports
   - formatting
   - types
   - naming
   - error handling
   - logging / printing
8. Repo-specific agent guidance
9. Security and secrets
10. Cursor / Copilot rules status

## Success criteria

- `AGENTS.md` remains around the requested length (~150 lines).
- All commands are accurate for the current repo.
- The file clearly states that no Cursor/Copilot rules were found.
- The file includes a strong prohibition against reading `.env` contents by default.
- The file is useful to a coding agent with no prior repo context.
