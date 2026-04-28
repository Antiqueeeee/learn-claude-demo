from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: dict[str, Any] | None = None
    enabled: bool = True

    def to_provider_format(
        self,
        provider: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        if provider != "openai":
            raise ValueError(f"Unsupported provider: {provider}")

        return self._to_openai_format(model=model)

    def _to_openai_format(self, model: str | None = None) -> dict[str, Any]:
        parameters = copy.deepcopy(self.input_schema)
        if parameters is None:
            parameters = {}

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
