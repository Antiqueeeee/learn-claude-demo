import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tool_runtime.builtin_tools import task


class TaskToolTests(unittest.TestCase):
    def test_run_uses_fresh_context_and_child_tools(self) -> None:
        captured = {}

        class FakeLlmEngine:
            def chat(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content="subtask summary",
                                tool_calls=None,
                            )
                        )
                    ]
                )

        with patch("engines.llmEngine.llm_engine", return_value=FakeLlmEngine()):
            result = task.TOOL.run(" inspect files ")

        self.assertEqual(result, {"summary": "subtask summary"})
        self.assertEqual(captured["model"], task.DEFAULT_MODEL)
        self.assertEqual(
            captured["messages"],
            [
                {"role": "user", "content": "inspect files"},
                {"role": "assistant", "content": "subtask summary"},
            ],
        )
        self.assertIs(captured["tools"], task.TASK_TOOL_SPECS)
        self.assertEqual(
            {tool["function"]["name"] for tool in captured["tools"]},
            {"bash", "read_file", "write_file", "edit_file"},
        )

    def test_run_executes_child_tool_calls_until_summary(self) -> None:
        captured_messages = []
        responses = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="",
                            tool_calls=[
                                SimpleNamespace(
                                    id="call_1",
                                    function=SimpleNamespace(
                                        name="read_file",
                                        arguments='{"path": "notes.txt"}',
                                    ),
                                )
                            ],
                        )
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="found notes",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        class FakeLlmEngine:
            def chat(self, **kwargs):
                captured_messages.append([dict(message) for message in kwargs["messages"]])
                return responses.pop(0)

        with (
            patch("engines.llmEngine.llm_engine", return_value=FakeLlmEngine()),
            patch.object(task.READ_FILE_TOOL, "run", return_value={"content": "hello"}) as read_file,
        ):
            result = task.TOOL.run("read notes")

        self.assertEqual(result, {"summary": "found notes"})
        read_file.assert_called_once_with(path="notes.txt")
        self.assertEqual(captured_messages[0], [{"role": "user", "content": "read notes"}])
        self.assertEqual(captured_messages[1][1]["role"], "assistant")
        self.assertEqual(captured_messages[1][1]["tool_calls"][0]["function"]["name"], "read_file")
        self.assertEqual(captured_messages[1][2]["role"], "tool")
        self.assertEqual(captured_messages[1][2]["tool_call_id"], "call_1")


if __name__ == "__main__":
    unittest.main()
