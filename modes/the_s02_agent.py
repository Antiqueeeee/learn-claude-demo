import json

from engines.llmEngine import llm_engine
from tool_runtime import build_registry

llm_handler = llm_engine()
model = "gpt-5.2"
PROVIDER = "openai"
# One user request may require several tool calls plus one final assistant
# response. Keep this comfortably above the expected number of tool steps.
MAX_LOOPS = 8

def naive_run(messages):
    loops = 0
    registry = build_registry()

    while loops < MAX_LOOPS:
        print(f"loops : {loops}\nmessages:\n{json.dumps(messages,ensure_ascii=False,indent=2)}")
        loops += 1
        stream = llm_handler.chat_stream(
            model=model,
            messages=messages,
            tools=registry.format_tools(provider=PROVIDER, model=model),
        )

        tool_calls = {}  # idx -> {"id","name","arguments"}
        final_text = []
        try:
            for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                choice = choices[0]
                delta = getattr(choice, "delta", None)

                # 文本
                if delta and getattr(delta, "content", None):
                    final_text.append(delta.content)

                # 工具调用（拼接 arguments）
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
            print(f"tool_calls :\n", tool_calls)
            assistant_text = "".join(final_text).strip()

            # 1) 先把 assistant 这轮产物写回 messages（重要：包含 tool_calls）
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

            # 2) 结束条件：模型不再调用工具 => 返回最终文本
            if not tool_calls:
                return assistant_text

            # 3) 模型调用了工具：执行工具，把结果以 role=tool 回填，再继续下一轮
            for idx in sorted(tool_calls):
                c = tool_calls[idx]

                try:
                    args = json.loads(c["arguments"]) if c["arguments"] else {}
                except Exception as e:
                    tool_out = {"error": f"Invalid JSON arguments: {e}", "raw": c["arguments"]}
                else:
                    try:
                        tool_out = registry.execute(c["name"], args)
                    except Exception as e:
                        tool_out = {"error": str(e), "tool": c["name"], "args": args}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": c["id"],  # 必须和该 tool_call 的 id 对上
                        "content": json.dumps(tool_out, ensure_ascii=False),
                    }
                )
            print("\n\n")
        finally : 
            if hasattr(stream, "close"):
                stream.close()

    return f"(stopped) reached MAX_LOOPS={MAX_LOOPS}"
