from __future__ import annotations

from typing import Any

from agent_tools.base import BaseTool
from tools.docs import search_docs as search_docs_impl


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

    def run(self, **kwargs: Any) -> Any:
        return search_docs_impl(**kwargs)


TOOL = SearchDocsTool()
