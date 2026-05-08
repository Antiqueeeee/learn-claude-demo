import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tool_runtime import build_registry

EXPECTED_TOOL_NAMES = {
    "bash",
    "edit_file",
    "fx_convert",
    "read_file",
    "search_docs",
    "unit_convert",
    "write_file",
}


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
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "bash"
            ),
            ["command"],
        )
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "read_file"
            ),
            ["path"],
        )
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "write_file"
            ),
            ["path", "content"],
        )
        self.assertEqual(
            next(
                tool["function"]["parameters"]["required"]
                for tool in tools
                if tool["function"]["name"] == "edit_file"
            ),
            ["path", "old_text", "new_text"],
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

    def test_build_registry_executes_bash(self) -> None:
        registry = build_registry()

        result = registry.execute("bash", {"command": "printf hello"})

        self.assertEqual(result["command"], "printf hello")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"], "hello")
        self.assertEqual(result["stderr"], "")
        self.assertFalse(result["timed_out"])

    def test_build_registry_executes_read_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            file_path = temp_path / "notes.txt"
            file_path.write_text("alpha\nbeta\n", encoding="utf-8")

            original_cwd = Path.cwd()
            os.chdir(temp_path)
            try:
                registry = build_registry()
                result = registry.execute("read_file", {"path": "notes.txt"})
            finally:
                os.chdir(original_cwd)

        self.assertEqual(result["path"], "notes.txt")
        self.assertEqual(result["content"], "alpha\nbeta\n")
        self.assertEqual(result["start_line"], 1)
        self.assertEqual(result["end_line"], 2)
        self.assertFalse(result["truncated"])

    def test_build_registry_executes_write_and_edit_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            original_cwd = Path.cwd()
            os.chdir(temp_path)
            try:
                registry = build_registry()
                write_result = registry.execute(
                    "write_file",
                    {"path": "draft.txt", "content": "hello world\n"},
                )
                edit_result = registry.execute(
                    "edit_file",
                    {
                        "path": "draft.txt",
                        "old_text": "world",
                        "new_text": "agent",
                    },
                )
                content = (temp_path / "draft.txt").read_text(encoding="utf-8")
            finally:
                os.chdir(original_cwd)

        self.assertEqual(write_result["path"], "draft.txt")
        self.assertEqual(write_result["bytes_written"], len("hello world\n"))
        self.assertFalse(write_result["appended"])
        self.assertEqual(edit_result["path"], "draft.txt")
        self.assertEqual(edit_result["replacements"], 1)
        self.assertEqual(content, "hello agent\n")

    def test_file_tools_reject_paths_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            original_cwd = Path.cwd()
            os.chdir(temp_path)
            try:
                registry = build_registry()
                with self.assertRaises(ValueError):
                    registry.execute("read_file", {"path": "../outside.txt"})
                with self.assertRaises(ValueError):
                    registry.execute(
                        "write_file",
                        {"path": "../outside.txt", "content": "nope"},
                    )
            finally:
                os.chdir(original_cwd)


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
