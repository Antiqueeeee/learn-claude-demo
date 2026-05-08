from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.workspace import resolve_workspace_path, truncate_text

DEFAULT_MAX_LINES = 200


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read UTF-8 text from a file inside the current workspace."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Workspace-relative file path.",
            },
            "start_line": {
                "type": "integer",
                "minimum": 1,
                "description": "1-based starting line number.",
            },
            "max_lines": {
                "type": "integer",
                "minimum": 1,
                "description": "Maximum number of lines to return. Defaults to 200.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    }

    def run(
        self,
        path: str,
        start_line: int = 1,
        max_lines: int = DEFAULT_MAX_LINES,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        if start_line < 1:
            raise ValueError("start_line must be >= 1")
        if max_lines < 1:
            raise ValueError("max_lines must be >= 1")

        file_path = resolve_workspace_path(path)
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        if total_lines == 0:
            return {
                "path": path,
                "content": "",
                "start_line": 1,
                "end_line": 0,
                "total_lines": 0,
                "truncated": False,
            }

        if start_line > total_lines:
            raise ValueError(
                f"start_line {start_line} is beyond the end of {path} ({total_lines} lines)"
            )

        start_index = start_line - 1
        selected_lines = lines[start_index : start_index + max_lines]
        selected_content = "".join(selected_lines)
        truncated_content, was_char_truncated = truncate_text(selected_content)
        end_line = start_index + len(selected_lines)
        return {
            "path": path,
            "content": truncated_content,
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": total_lines,
            "truncated": was_char_truncated or end_line < total_lines,
        }


TOOL = ReadFileTool()
