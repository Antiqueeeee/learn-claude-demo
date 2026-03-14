from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Union

from engines.configEngine import SETTINGS
from openai import OpenAI

ToolSpec = Dict[str, Any]


class llm_engine:
    """
    - model 不耦合在 init：每次请求传入 model
    - 自动重试：交给 OpenAI SDK（max_retries）
    - 流式输出：chat_stream()
    - 工具调用：tools/tool_choice 作为可选参数，原样透传给模型（不做“自动执行工具”）
    """

    def __init__(
        self,
        api_key: str = SETTINGS.llm_default_api_key,
        base_url: str = SETTINGS.llm_default_base_url,
        timeout: int = getattr(SETTINGS, "llm_default_timeout", 60),
        max_retries: int = getattr(SETTINGS, "llm_default_max_retries", 3),
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,  # 交给 SDK 自动重试
        )

    def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolSpec]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        stream: bool = False,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        非流式：返回 ChatCompletion
        流式：返回可迭代 stream（你自己 for chunk in resp）
        kwargs 透传：temperature/top_p/max_tokens/response_format/... 都可放这里
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }
        
        print("payload.stream =", payload.get("stream"))
        print("payload.model =", payload.get("model"))
        print("payload keys =", payload.keys())

        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if extra:
            payload.update(extra)

        return self.client.chat.completions.create(**payload)

    def chat_stream(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolSpec]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        流式输出版本（等价于 chat(..., stream=True)）
        """
        return self.chat(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
            extra=extra,
            **kwargs,
        )
