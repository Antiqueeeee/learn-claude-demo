import json

from engines.llmEngine import llm_engine
from tool_runtime import build_registry

llm_handler = llm_engine()
model = "gpt-5.2"
PROVIDER = "openai"
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
