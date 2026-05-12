import importlib
import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class S03AgentMainTests(unittest.TestCase):
    def _import_agent_module(self):
        fake_llm_module = SimpleNamespace(
            llm_engine=lambda: SimpleNamespace(chat_stream=None)
        )
        modes_package = sys.modules.get("modes")
        original_module = sys.modules.pop("modes.the_s03_agent", None)
        original_attr = (
            getattr(modes_package, "the_s03_agent")
            if modes_package is not None and hasattr(modes_package, "the_s03_agent")
            else None
        )
        had_attr = modes_package is not None and hasattr(modes_package, "the_s03_agent")

        def cleanup() -> None:
            if original_module is not None:
                sys.modules["modes.the_s03_agent"] = original_module
            else:
                sys.modules.pop("modes.the_s03_agent", None)
            if modes_package is not None:
                if had_attr:
                    setattr(modes_package, "the_s03_agent", original_attr)
                elif hasattr(modes_package, "the_s03_agent"):
                    delattr(modes_package, "the_s03_agent")

        self.addCleanup(cleanup)

        with patch.dict(sys.modules, {"engines.llmEngine": fake_llm_module}):
            return importlib.import_module("modes.the_s03_agent")

    def test_main_uses_cli_prompt_and_prints_result(self) -> None:
        agent_module = self._import_agent_module()
        stdout = io.StringIO()

        with (
            patch.object(agent_module, "naive_run", return_value="ok") as naive_run,
            patch("sys.stdout", stdout),
        ):
            exit_code = agent_module.main(["请读取", "README.md"])

        self.assertEqual(exit_code, 0)
        naive_run.assert_called_once_with(
            [{"role": "user", "content": "请读取 README.md"}]
        )
        self.assertEqual(stdout.getvalue().strip(), "ok")

    def test_main_uses_default_smoke_prompt_without_cli_args(self) -> None:
        agent_module = self._import_agent_module()
        stdout = io.StringIO()

        with (
            patch.object(agent_module, "naive_run", return_value="ready") as naive_run,
            patch("sys.stdout", stdout),
        ):
            agent_module.main([])

        prompt = naive_run.call_args.args[0][0]["content"]
        self.assertIn("read_file", prompt)
        self.assertIn("README.md", prompt)


if __name__ == "__main__":
    unittest.main()
