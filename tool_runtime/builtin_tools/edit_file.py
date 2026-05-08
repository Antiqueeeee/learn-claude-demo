from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool
from tool_runtime.workspace import resolve_workspace_path


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Replace exact text in a workspace file."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Workspace-relative file path.",
            },
            "old_text": {
                "type": "string",
                "description": "Exact text to replace.",
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace every match instead of the first one only.",
            },
        },
        "required": ["path", "old_text", "new_text"],
        "additionalProperties": False,
    }

    def run(
        self,
        path: str,
        old_text: str,
        new_text: str,
        replace_all: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        if not old_text:
            raise ValueError("old_text must not be empty")

        file_path = resolve_workspace_path(path)
        content = file_path.read_text(encoding="utf-8")
        occurrence_count = content.count(old_text)
        if occurrence_count == 0:
            raise ValueError(f"Text not found in {path}")

        replacements = occurrence_count if replace_all else 1
        updated_content = content.replace(old_text, new_text, replacements)
        file_path.write_text(updated_content, encoding="utf-8")

        return {
            "path": path,
            "replacements": replacements,
            "replace_all": replace_all,
            "bytes_written": len(updated_content.encode("utf-8")),
        }


TOOL = EditFileTool()
