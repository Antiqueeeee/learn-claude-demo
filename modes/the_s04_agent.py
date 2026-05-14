import json
import sys
from collections.abc import Sequence

from engines.llmEngine import llm_engine
from tool_runtime import ToolRegistry, build_registry
from tool_runtime.builtin_tools.bash import TOOL as BASH_TOOL
from tool_runtime.builtin_tools.edit_file import TOOL as EDIT_FILE_TOOL
from tool_runtime.builtin_tools.fx_convert import TOOL as FX_CONVERT_TOOL
from tool_runtime.builtin_tools.grep import TOOL as GREP_TOOL
from tool_runtime.builtin_tools.read_file import TOOL as READ_FILE_TOOL
from tool_runtime.builtin_tools.search_docs import TOOL as SEARCH_DOCS_TOOL
from tool_runtime.builtin_tools.task import TOOL as TASK_TOOL
from tool_runtime.builtin_tools.unit_convert import TOOL as UNIT_CONVERT_TOOL
from tool_runtime.builtin_tools.write_file import TOOL as WRITE_FILE_TOOL

llm_handler = llm_engine()
model = "gpt-5.2"
PROVIDER = "openai"
MANUAL_TOOLS = [
    BASH_TOOL,
    EDIT_FILE_TOOL,
    FX_CONVERT_TOOL,
    GREP_TOOL,
    READ_FILE_TOOL,
    SEARCH_DOCS_TOOL,
    TASK_TOOL,
    UNIT_CONVERT_TOOL,
    WRITE_FILE_TOOL,
]

DEFAULT_SMOKE_PROMPT = (
    "请先使用 read_file 读取 README.md 的前 20 行，"
    "再用中文简要说明这个仓库是做什么的。"
)
MAX_LOOPS = 999


def format_manual_tools() -> list[dict]:
    return ToolRegistry(MANUAL_TOOLS).format_tools(provider=PROVIDER, model=model)


def naive_run(messages):
    loops = 0
    registry = build_registry(include_builtin=False, extra_tools=MANUAL_TOOLS)
    tools = format_manual_tools()

    while loops < MAX_LOOPS:
        print(f"loops : {loops}\nmessages:\n{json.dumps(messages,ensure_ascii=False,indent=2)}")
        loops += 1
        stream = llm_handler.chat_stream(
            model=model,
            messages=messages,
            tools=tools,
        )
        tool_calls = {}
        final_text = []
        try:
            for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                choice = choices[0]
                delta = getattr(choice, "delta", None)

                if delta and getattr(delta, "content", None):
                    final_text.append(delta.content)

                if delta and getattr(delta, "tool_calls", None):
                    for tc in delta.tool_calls:
                        idx = tc.index
                        tool_calls.setdefault(idx, {"id": "", "name": "", "arguments": ""})

                        if getattr(tc, "id", None):
                            tool_calls[idx]["id"] = tc.id
                        if tc.function and getattr(tc.function, "name", None):
                            tool_calls[idx]["name"] = tc.function.name
                        if tc.function and getattr(tc.function, "arguments", None):
                            tool_calls[idx]["arguments"] += tc.function.arguments

            assistant_text = "".join(final_text).strip()
            assistant_msg = {"role": "assistant", "content": assistant_text}

            if tool_calls:
                assistant_msg["tool_calls"] = []
                for idx in sorted(tool_calls):
                    c = tool_calls[idx]
                    assistant_msg["tool_calls"].append(
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {
                                "name": c["name"],
                                "arguments": c["arguments"],
                            },
                        }
                    )

            messages.append(assistant_msg)

            if not tool_calls:
                return assistant_text

            for idx in sorted(tool_calls):
                c = tool_calls[idx]

                try:
                    args = json.loads(c["arguments"]) if c["arguments"] else {}
                except Exception as exc:
                    tool_out = {"error": f"Invalid JSON arguments: {exc}", "raw": c["arguments"]}
                else:
                    try:
                        tool_out = registry.execute(c["name"], args)
                    except Exception as exc:
                        tool_out = {"error": str(exc), "tool": c["name"], "args": args}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": c["id"],
                        "content": json.dumps(tool_out, ensure_ascii=False),
                    }
                )
        finally:
            if hasattr(stream, "close"):
                stream.close()

    return f"(stopped) reached MAX_LOOPS={MAX_LOOPS}"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    prompt = " ".join(args).strip() or DEFAULT_SMOKE_PROMPT
    result = naive_run([{"role": "user", "content": prompt}])
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
