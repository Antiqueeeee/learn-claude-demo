import json
import sys
from collections.abc import Sequence

from engines.llmEngine import llm_engine
from tool_runtime import build_registry

llm_handler = llm_engine()
model = "gpt-5.2"
PROVIDER = "openai"

# `main()` 里会优先读取命令行参数：
# - 运行 `python modes/the_s03_agent.py 请读取 README.md`
# - 此时 `args == ["请读取", "README.md"]`
# - `" ".join(args).strip()` 会得到 `"请读取 README.md"`
# - 这个字符串会作为 user message 传给 `naive_run()`
# 如果你不传任何参数，就会退回到下面这个默认 smoke prompt。
#
# 可手动测试的 prompt 示例（按需复制到命令行，或临时替换 DEFAULT_SMOKE_PROMPT）：
# 1. 只读文件 case
#    "请先使用 read_file 读取 README.md 的前 20 行，再用中文简要说明这个仓库是做什么的。"
#    预期：触发 `read_file`，最后给出摘要。
#
# 2. 文档搜索 case
#    "请使用 search_docs 搜索 tool loader，并如实说明命中结果。"
#    预期：触发 `search_docs`；当前实现大概率返回空 hits。
#
# 3. 单位换算 case
#    "请使用 unit_convert 把 72 Fahrenheit 转成 Celsius，再把 5 km 转成 mi。"
#    预期：可能连续触发两次 `unit_convert`。
#
# 4. 汇率换算 case
#    "请使用 fx_convert 把 10 USD 转成 JPY，并说明这个工具的限制。"
#    预期：触发 `fx_convert`；支持相邻币种换算。
#
# 5. bash case
#    "请使用 bash 执行 pwd 和 ls modes，并告诉我当前工作目录和 modes 下面有哪些文件。"
#    预期：触发 `bash`；适合观察命令执行结果如何回填到下一轮对话。
#
# 6. 写入再读取 case（会改动工作区）
#    "请使用 write_file 在 tmp/s03_demo.txt 写入 hello agent\\n，再用 read_file 读回来确认内容。"
#    预期：先触发 `write_file`，再触发 `read_file`。
#
# 7. 编辑文件 case（会改动工作区）
#    "请使用 edit_file 把 tmp/s03_demo.txt 里的 hello 替换成 hi，再用 read_file 读取确认。"
#    预期：触发 `edit_file` 和 `read_file`。
#
# 8. 错误处理 case
#    "请尝试使用 fx_convert 把 10 USD 直接转成 KRW；如果失败，请解释失败原因。"
#    预期：工具返回错误，因为当前只支持相邻币种直接兑换。
DEFAULT_SMOKE_PROMPT = (
    "请先使用 read_file 读取 README.md 的前 20 行，"
    "再用中文简要说明这个仓库是做什么的。"
)
# One user request may require several tool calls plus one final assistant
# response. Keep this comfortably above the expected number of tool steps.
MAX_LOOPS = 999


def naive_run(messages):
    loops = 0
    registry = build_registry(extra_tools=[])

    while loops < MAX_LOOPS:
        print(f"loops : {loops}\nmessages:\n{json.dumps(messages,ensure_ascii=False,indent=2)}")
        loops += 1
        stream = llm_handler.chat_stream(
            model=model,
            messages=messages,
            tools=registry.format_tools(provider=PROVIDER, model=model),
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
    # `args` 来自命令行参数列表；有参数时优先使用参数拼出来的 prompt，
    # 没参数时才回退到 DEFAULT_SMOKE_PROMPT。
    prompt = " ".join(args).strip() or DEFAULT_SMOKE_PROMPT
    result = naive_run([{"role": "user", "content": prompt}])
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
