from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool


class SearchDocsTool(BaseTool):
    name = "search_docs"
    description = "Search internal docs by query."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {"hits": [], "query": query}


TOOL = SearchDocsTool()
