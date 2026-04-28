import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tool_runtime import build_registry

EXPECTED_TOOL_NAMES = {"search_docs", "fx_convert", "unit_convert"}


class ToolRuntimeTests(unittest.TestCase):
    def test_build_registry_loads_builtin_tools_by_default(self) -> None:
        registry = build_registry()

        tools = registry.format_tools(provider="openai", model="gpt-5.2")

        self.assertEqual(len(tools), len(EXPECTED_TOOL_NAMES))
        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            EXPECTED_TOOL_NAMES,
        )
        self.assertTrue(all(tool["type"] == "function" for tool in tools))
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "search_docs"
            ),
            ["query"],
        )
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "unit_convert"
            ),
            ["value", "from_unit", "to_unit"],
        )
        fx_schema = next(
            tool["function"]["parameters"]
            for tool in tools
            if tool["function"]["name"] == "fx_convert"
        )
        self.assertEqual(
            fx_schema["properties"]["from_currency"]["enum"],
            ["USD", "JPY", "KRW", "VND", "IDR"],
        )
        self.assertEqual(
            fx_schema["properties"]["to_currency"]["enum"],
            ["USD", "JPY", "KRW", "VND", "IDR"],
        )

    def test_build_registry_accepts_extra_tools(self) -> None:
        extra_tool = ToolRuntimeArchitectureTests()._make_dummy_tool()

        registry = build_registry(extra_tools=[extra_tool])

        tools = registry.format_tools(provider="openai", model="gpt-5.2")

        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            EXPECTED_TOOL_NAMES | {"dummy"},
        )

    def test_build_registry_supports_pure_manual_tool_sets(self) -> None:
        manual_tool = ToolRuntimeArchitectureTests()._make_dummy_tool()

        registry = build_registry(
            include_builtin=False,
            extra_tools=[manual_tool],
        )

        tools = registry.format_tools(provider="openai", model="gpt-5.2")

        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            {"dummy"},
        )

    def test_build_registry_rejects_unsupported_provider(self) -> None:
        registry = build_registry()

        with self.assertRaises(ValueError):
            registry.format_tools(provider="anthropic", model="claude-sonnet-4")

    def test_build_registry_executes_search_docs(self) -> None:
        registry = build_registry()

        result = registry.execute("search_docs", {"query": "agent loop"})

        self.assertEqual(result, {"hits": [], "query": "agent loop"})


class ToolRuntimeArchitectureTests(unittest.TestCase):
    def _make_dummy_tool(self):
        from tool_runtime.base import BaseTool

        class DummyTool(BaseTool):
            name = "dummy"
            description = "Dummy tool"
            input_schema = {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            }

            def run(self, **kwargs):
                return {"ok": True, "kwargs": kwargs}

        return DummyTool()

    def test_base_tool_formats_as_openai_function_spec(self) -> None:
        tool = self._make_dummy_tool()

        formatted = tool.to_provider_format("openai", model="gpt-5.2")

        self.assertEqual(formatted["type"], "function")
        self.assertEqual(formatted["function"]["name"], "dummy")
        self.assertFalse(formatted["function"]["parameters"]["additionalProperties"])

    def test_tool_registry_executes_registered_tool(self) -> None:
        from tool_runtime.registry import ToolRegistry

        registry = ToolRegistry([self._make_dummy_tool()])

        self.assertEqual(registry.execute("dummy", {}), {"ok": True, "kwargs": {}})

    def test_tool_registry_rejects_disabled_tool(self) -> None:
        from tool_runtime.registry import ToolRegistry

        tool = self._make_dummy_tool()
        tool.enabled = False
        registry = ToolRegistry([tool])

        with self.assertRaises(ValueError):
            registry.execute("dummy", {})

    def test_naive_run_uses_registry_for_tool_specs(self) -> None:
        captured: dict[str, str] = {}
        fake_llm_module = SimpleNamespace(llm_engine=lambda: SimpleNamespace(chat_stream=None))
        fake_registry = SimpleNamespace()

        def fake_format_tools(*, provider: str, model: str | None):
            captured["provider"] = provider
            captured["model"] = model or ""
            return []

        def fake_chat_stream(*, model: str, messages, tools):
            self.assertEqual(model, agent_loop.model)
            self.assertEqual(messages, [{"role": "user", "content": "hello"}])
            self.assertEqual(tools, [])

            def stream():
                yield SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="done", tool_calls=None)
                        )
                    ]
                )

            return stream()

        fake_registry.format_tools = fake_format_tools
        fake_registry.execute = lambda name, arguments: None

        modes_package = sys.modules.get("modes")
        original_agent_loop_attr = (
            getattr(modes_package, "the_agent_loop")
            if modes_package is not None and hasattr(modes_package, "the_agent_loop")
            else None
        )
        had_agent_loop_attr = (
            modes_package is not None and hasattr(modes_package, "the_agent_loop")
        )
        original_agent_loop = sys.modules.pop("modes.the_agent_loop", None)
        original_llm_module = sys.modules.get("engines.llmEngine")

        try:
            sys.modules["engines.llmEngine"] = fake_llm_module
            agent_loop = importlib.import_module("modes.the_agent_loop")
            with (
                patch.object(
                    agent_loop,
                    "build_registry",
                    return_value=fake_registry,
                ),
                patch.object(
                    agent_loop.llm_handler,
                    "chat_stream",
                    side_effect=fake_chat_stream,
                ),
            ):
                result = agent_loop.naive_run([{"role": "user", "content": "hello"}])
        finally:
            if original_llm_module is not None:
                sys.modules["engines.llmEngine"] = original_llm_module
            else:
                sys.modules.pop("engines.llmEngine", None)
            if original_agent_loop is not None:
                sys.modules["modes.the_agent_loop"] = original_agent_loop
            else:
                sys.modules.pop("modes.the_agent_loop", None)
            if modes_package is not None:
                if had_agent_loop_attr:
                    setattr(modes_package, "the_agent_loop", original_agent_loop_attr)
                elif hasattr(modes_package, "the_agent_loop"):
                    delattr(modes_package, "the_agent_loop")

        self.assertEqual(result, "done")
        self.assertEqual(
            captured,
            {"provider": "openai", "model": agent_loop.model},
        )
