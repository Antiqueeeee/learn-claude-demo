from __future__ import annotations

import subprocess
from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.workspace import current_workspace, truncate_text

DEFAULT_TIMEOUT_SECONDS = 120
BLOCKED_SNIPPETS = (
    "rm -rf /",
    "shutdown",
    "reboot",
    "mkfs",
    "> /dev/",
)


class BashTool(BaseTool):
    name = "bash"
    description = "Run a shell command inside the current workspace."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to run from the workspace root.",
            },
            "timeout_seconds": {
                "type": "integer",
                "minimum": 1,
                "maximum": DEFAULT_TIMEOUT_SECONDS,
                "description": "Optional timeout in seconds. Defaults to 120.",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    def run(
        self,
        command: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        normalized_command = command.strip()
        if not normalized_command:
            raise ValueError("Command must not be empty")

        if any(snippet in normalized_command for snippet in BLOCKED_SNIPPETS):
            raise ValueError("Dangerous command blocked")

        try:
            completed = subprocess.run(
                normalized_command,
                shell=True,
                cwd=current_workspace(),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout, stdout_truncated = truncate_text(exc.stdout or "")
            stderr, stderr_truncated = truncate_text(exc.stderr or "")
            return {
                "command": normalized_command,
                "exit_code": None,
                "stdout": stdout,
                "stdout_truncated": stdout_truncated,
                "stderr": stderr,
                "stderr_truncated": stderr_truncated,
                "timed_out": True,
            }

        stdout, stdout_truncated = truncate_text(completed.stdout)
        stderr, stderr_truncated = truncate_text(completed.stderr)
        return {
            "command": normalized_command,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stdout_truncated": stdout_truncated,
            "stderr": stderr,
            "stderr_truncated": stderr_truncated,
            "timed_out": False,
        }


TOOL = BashTool()
