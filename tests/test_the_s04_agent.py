import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class S04AgentTests(unittest.TestCase):
    def _import_agent_module(self):
        fake_llm_module = SimpleNamespace(
            llm_engine=lambda: SimpleNamespace(chat_stream=None)
        )
        modes_package = sys.modules.get("modes")
        original_module = sys.modules.pop("modes.the_s04_agent", None)
        original_attr = (
            getattr(modes_package, "the_s04_agent")
            if modes_package is not None and hasattr(modes_package, "the_s04_agent")
            else None
        )
        had_attr = modes_package is not None and hasattr(modes_package, "the_s04_agent")

        def cleanup() -> None:
            if original_module is not None:
                sys.modules["modes.the_s04_agent"] = original_module
            else:
                sys.modules.pop("modes.the_s04_agent", None)
            if modes_package is not None:
                if had_attr:
                    setattr(modes_package, "the_s04_agent", original_attr)
                elif hasattr(modes_package, "the_s04_agent"):
                    delattr(modes_package, "the_s04_agent")

        self.addCleanup(cleanup)

        with patch.dict(sys.modules, {"engines.llmEngine": fake_llm_module}):
            return importlib.import_module("modes.the_s04_agent")

    def test_format_manual_tools_uses_builtin_tool_instances(self) -> None:
        agent_module = self._import_agent_module()

        tools = agent_module.format_manual_tools()

        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            {tool.name for tool in agent_module.MANUAL_TOOLS},
        )
        task_tool = next(
            tool for tool in tools if tool["function"]["name"] == "task"
        )
        self.assertEqual(
            task_tool["function"]["parameters"],
            agent_module.TASK_TOOL.input_schema,
        )

    def test_naive_run_injects_manually_loaded_tools(self) -> None:
        agent_module = self._import_agent_module()
        captured = {}

        def fake_chat_stream(*, model, messages, tools):
            captured["model"] = model
            captured["messages"] = messages
            captured["tools"] = tools

            def stream():
                yield SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="done", tool_calls=None)
                        )
                    ]
                )

            return stream()

        fake_registry = SimpleNamespace(execute=lambda name, args: None)
        fake_tools = [{"type": "function", "function": {"name": "sentinel"}}]

        with (
            patch.object(agent_module.llm_handler, "chat_stream", side_effect=fake_chat_stream),
            patch.object(agent_module, "build_registry", return_value=fake_registry) as build_registry,
            patch.object(agent_module, "format_manual_tools", return_value=fake_tools) as format_manual_tools,
        ):
            result = agent_module.naive_run([{"role": "user", "content": "hello"}])

        self.assertEqual(result, "done")
        self.assertEqual(captured["model"], agent_module.model)
        self.assertIs(captured["tools"], fake_tools)
        build_registry.assert_called_once_with(
            include_builtin=False,
            extra_tools=agent_module.MANUAL_TOOLS,
        )
        format_manual_tools.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
