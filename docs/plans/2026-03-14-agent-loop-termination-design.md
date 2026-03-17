# Agent Loop Termination Design

**Goal:** Ensure `naive_run()` runs until the model stops requesting tools (i.e., returns no `tool_calls`), without prematurely stopping between the last tool call and the final natural-language answer.

## Problem

The agent loop currently uses a single `MAX_LOOPS` counter to limit iterations. A typical request may require N tool calls plus one final assistant turn (no tool calls) to summarize results.

When `MAX_LOOPS` is too small (e.g., equals N), the loop stops after executing the last tool call but before the final assistant response, returning a string like:

`(stopped) reached MAX_LOOPS=...`

This is not an exception, but it looks like an error and prevents a complete answer.

## Requirements

- Continue looping as long as the model returns tool calls.
- Return only when the model returns a normal assistant response with no tool calls.
- Keep a safety limit to prevent infinite loops.
- Keep return type as `str` for compatibility, and keep `messages` in a valid tool-calling state so the caller can continue the conversation.

## Approach (Recommended)

Separate counters:

- `MAX_TOOL_ROUNDS`: maximum number of tool-execution rounds allowed.
- `MAX_MODEL_TURNS`: maximum number of model calls allowed.

Rules:

- Each model call increments `model_turns`.
- Only a round where tool calls are executed increments `tool_rounds`.
- If the model returns no tool calls: return the assistant text.
- If the model returns tool calls but `tool_rounds` has hit its cap:
  - Do not append an assistant message containing `tool_calls` (avoid leaving unmatched tool calls in `messages`).
  - Append a plain assistant message describing the stop condition.
  - Return that stop message (string), preserving conversation consistency.

## Non-Goals

- Changing the overall message format or adopting a new framework.
- Adding new tools or changing tool schemas.
