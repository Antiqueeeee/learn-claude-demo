# Agent Loop Termination Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prevent `naive_run()` from stopping after the last tool call but before the final assistant response.

**Architecture:** Replace the single `MAX_LOOPS` counter with separate model/tool limits so the loop can always include the final non-tool assistant turn.

**Tech Stack:** Python 3.13, OpenAI SDK streaming, local tool whitelist.

---

### Task 1: Update loop termination logic

**Files:**
- Modify: `modes/the_agent_loop.py`

**Step 1: Change counters**

- Replace `MAX_LOOPS` with:
  - `MAX_TOOL_ROUNDS` (e.g., 16)
  - `MAX_MODEL_TURNS` (e.g., 32)
- Track `tool_rounds` and `model_turns`.

**Step 2: Ensure no unmatched tool calls**

- If the model returns tool calls when `tool_rounds` is already at the cap:
  - Append a plain `{"role": "assistant", "content": ...}` message (no `tool_calls`).
  - Return the same string.

**Step 3: Keep return value stable**

- Ensure `naive_run()` returns a string both on success and when stopped by a limit.

**Step 4: Tighten types (optional but recommended)**

- Annotate `messages` and internal dicts with `Any` to avoid accidental type narrowing.
- Call `run_tool()` with JSON argument strings (or update signature consistently).

**Step 5: Verify**

Run:

- `python -m compileall -q .`
- `python main.py`

Expected:

- The example completes with a final natural-language answer (not a `(stopped)` message).
