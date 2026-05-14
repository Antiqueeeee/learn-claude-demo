from __future__ import annotations

import subprocess
from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.workspace import current_workspace, truncate_text

DEFAULT_MAX_MATCHES = 50


class GrepTool(BaseTool):
    name = "grep"
    description = "Search workspace files for a text pattern using grep."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Text or grep pattern to search for.",
            },
            "path": {
                "type": "string",
                "description": "Workspace-relative file or directory path. Defaults to current workspace.",
            },
            "max_matches": {
                "type": "integer",
                "minimum": 1,
                "maximum": DEFAULT_MAX_MATCHES,
                "description": "Maximum number of matching lines to return. Defaults to 50.",
            },
        },
        "required": ["pattern"],
        "additionalProperties": False,
    }

    def run(
        self,
        pattern: str,
        path: str = ".",
        max_matches: int = DEFAULT_MAX_MATCHES,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        normalized_pattern = pattern.strip()
        if not normalized_pattern:
            raise ValueError("Pattern must not be empty")
        if max_matches < 1:
            raise ValueError("max_matches must be >= 1")

        completed = subprocess.run(
            ["grep", "-R", "-n", "-m", str(max_matches), normalized_pattern, path],
            cwd=current_workspace(),
            capture_output=True,
            text=True,
        )
        if completed.returncode not in (0, 1):
            raise ValueError((completed.stderr or "grep failed").strip())

        stdout, stdout_truncated = truncate_text(completed.stdout)
        return {
            "pattern": normalized_pattern,
            "path": path,
            "matches": stdout,
            "matched": completed.returncode == 0,
            "truncated": stdout_truncated,
        }


TOOL = GrepTool()
