import unittest

from tooling import load_tools, run_tool

EXPECTED_BUILTIN_TOOL_NAMES = {"search_docs", "fx_convert", "unit_convert"}


class ToolingCompatibilityTests(unittest.TestCase):
    def test_load_tools_returns_openai_function_specs(self) -> None:
        tools = load_tools()

        self.assertEqual(len(tools), len(EXPECTED_BUILTIN_TOOL_NAMES))
        self.assertEqual(
            {tool["function"]["name"] for tool in tools},
            EXPECTED_BUILTIN_TOOL_NAMES,
        )
        self.assertEqual(len({tool["function"]["name"] for tool in tools}), len(tools))
        self.assertTrue(all(tool["type"] == "function" for tool in tools))
        self.assertTrue(
            all(
                tool["function"]["parameters"]["additionalProperties"] is False
                for tool in tools
            )
        )
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

    def test_run_tool_dispatches_search_docs(self) -> None:
        result = run_tool(
            "search_docs",
            '{"query": "agent loop"}',
        )

        self.assertEqual(result, {"hits": [], "query": "agent loop"})

    def test_run_tool_rejects_unknown_tool(self) -> None:
        with self.assertRaises(ValueError):
            run_tool("does_not_exist", "{}")


class ToolingArchitectureTests(unittest.TestCase):
    def _make_dummy_tool(self):
        from agent_tools.base import BaseTool

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

    def test_load_builtin_tools_discovers_enabled_tools(self) -> None:
        from agent_tools.loader import load_builtin_tools

        tools = load_builtin_tools()

        self.assertEqual(
            {tool.name for tool in tools},
            EXPECTED_BUILTIN_TOOL_NAMES,
        )

    def test_tool_registry_executes_registered_tool(self) -> None:
        from agent_tools.registry import ToolRegistry

        registry = ToolRegistry([self._make_dummy_tool()])

        self.assertEqual(registry.execute("dummy", {}), {"ok": True, "kwargs": {}})

    def test_tool_registry_rejects_disabled_tool(self) -> None:
        from agent_tools.registry import ToolRegistry

        tool = self._make_dummy_tool()
        tool.enabled = False
        registry = ToolRegistry([tool])

        with self.assertRaises(ValueError):
            registry.execute("dummy", {})
