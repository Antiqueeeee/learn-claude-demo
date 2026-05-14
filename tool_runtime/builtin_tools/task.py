from __future__ import annotations

import json
from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.builtin_tools.bash import TOOL as BASH_TOOL
from tool_runtime.builtin_tools.edit_file import TOOL as EDIT_FILE_TOOL
from tool_runtime.builtin_tools.read_file import TOOL as READ_FILE_TOOL
from tool_runtime.builtin_tools.write_file import TOOL as WRITE_FILE_TOOL

DEFAULT_MODEL = "gpt-5.2"
MAX_SUBAGENT_LOOPS = 30
TASK_TOOLS = [BASH_TOOL, READ_FILE_TOOL, WRITE_FILE_TOOL, EDIT_FILE_TOOL]
TASK_TOOL_SPECS = [
    tool.to_provider_format("openai", model=DEFAULT_MODEL)
    for tool in TASK_TOOLS
]
TASK_TOOLS_BY_NAME = {tool.name: tool for tool in TASK_TOOLS}


class TaskTool(BaseTool):
    name = "task"
    description = "Run a subtask in a clean context and return a summary."
    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
        },
        "required": ["prompt"],
        "additionalProperties": False,
    }

    def run(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ValueError("Prompt must not be empty")

        return {"summary": run_subagent(normalized_prompt)}


def run_subagent(prompt: str) -> str:
    from engines.llmEngine import llm_engine

    messages = [{"role": "user", "content": prompt}]
    llm_handler = llm_engine()

    for _ in range(MAX_SUBAGENT_LOOPS):
        response = llm_handler.chat(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=TASK_TOOL_SPECS,
        )
        message = response.choices[0].message
        assistant_text = message.content or ""
        tool_calls = list(getattr(message, "tool_calls", None) or [])
        assistant_msg = {"role": "assistant", "content": assistant_text}

        if tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments or "{}",
                    },
                }
                for tool_call in tool_calls
            ]

        messages.append(assistant_msg)

        if not tool_calls:
            return assistant_text

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments or "{}"
            try:
                args = json.loads(raw_arguments)
            except Exception as exc:
                tool_out = {"error": f"Invalid JSON arguments: {exc}", "raw": raw_arguments}
            else:
                try:
                    tool = TASK_TOOLS_BY_NAME[tool_name]
                except KeyError:
                    tool_out = {"error": f"Unknown tool: {tool_name}", "tool": tool_name, "args": args}
                else:
                    try:
                        tool_out = tool.run(**args)
                    except Exception as exc:
                        tool_out = {"error": str(exc), "tool": tool_name, "args": args}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_out, ensure_ascii=False),
                }
            )

    return f"(stopped) reached MAX_SUBAGENT_LOOPS={MAX_SUBAGENT_LOOPS}"


TOOL = TaskTool()
