import json

from engines.llmEngine import llm_engine
from tool_runtime import build_registry

llm_handler = llm_engine()
model = "gpt-5.2"
PROVIDER = "openai"
# One user request may require several tool calls plus one final assistant
# response. Keep this comfortably above the expected number of tool steps.
MAX_LOOPS = 8

def agent_run(messages):
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