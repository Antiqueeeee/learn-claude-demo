from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.workspace import resolve_workspace_path


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write UTF-8 text to a file inside the current workspace."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Workspace-relative file path.",
            },
            "content": {
                "type": "string",
                "description": "Text content to write.",
            },
            "append": {
                "type": "boolean",
                "description": "Append instead of replacing the file contents.",
            },
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    }

    def run(
        self,
        path: str,
        content: str,
        append: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        file_path = resolve_workspace_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        existed = file_path.exists()

        mode = "a" if append else "w"
        with file_path.open(mode, encoding="utf-8") as handle:
            handle.write(content)

        return {
            "path": path,
            "bytes_written": len(content.encode("utf-8")),
            "appended": append,
            "created": not existed,
        }


TOOL = WriteFileTool()
