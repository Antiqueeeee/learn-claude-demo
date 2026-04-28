# Learn Claude Demo

一个用 Python 写的小型 Agent Loop 示例。它会把本地白名单工具以 function calling 的形式暴露给 LLM 使用。

## 目录结构

```text
main.py
modes/
  the_s02_agent.py
tool_runtime/
  base.py
  loader.py
  registry.py
  builtin_tools/
    search_docs.py
    fx_convert.py
    unit_convert.py
tests/
  test_tool_runtime.py
```

### 各部分职责

- `tool_runtime/base.py`
  定义共享的 `BaseTool` 接口。
- `tool_runtime/builtin_tools/*.py`
  每个文件就是一个完整工具，包含名称、描述、schema 和执行逻辑。
- `tool_runtime/loader.py`
  自动发现 `tool_runtime/builtin_tools/` 里的内建工具。
- `tool_runtime/registry.py`
  构建运行时 registry，把工具转成模型可用的格式，并按名称执行工具。
- `modes/the_s02_agent.py`
  当前使用的流式 agent loop，会把工具定义发给模型，并把工具结果回填进 `messages`。

## Tool Runtime API

主要入口是：

```python
from tool_runtime import build_registry
```

### 1. 只加载内建工具

```python
registry = build_registry()
```

这会加载 `tool_runtime/builtin_tools/` 里自动发现的全部工具。

### 2. 内建工具 + 手动附加工具

```python
registry = build_registry(extra_tools=[MyDebugTool(), MyWeatherTool()])
```

这会保留内建工具，并把你手动传入的工具实例追加进去。

### 3. 纯手动工具集合

```python
registry = build_registry(
    include_builtin=False,
    extra_tools=[MyDebugTool(), MyWeatherTool()],
)
```

这会跳过自动发现，只使用你显式传入的工具实例。

### 可选参数

```python
registry = build_registry(
    include_builtin=True,
    extra_tools=None,
    include_disabled=False,
)
```

- `include_builtin`
  是否自动加载 `tool_runtime/builtin_tools/` 下的工具
- `extra_tools`
  额外追加的 `BaseTool` 实例
- `include_disabled`
  是否连 disabled 的内建工具也一起加载

## 常见用法

把工具格式化成模型可用的 function tools：

```python
registry = build_registry()
tools = registry.format_tools(provider="openai", model="gpt-5.2")
```

执行模型选中的工具：

```python
result = registry.execute("search_docs", {"query": "agent loop"})
```

## Agent Loop 集成方式

当前 `modes/the_s02_agent.py` 的接入方式是：

```python
registry = build_registry()

stream = llm_handler.chat_stream(
    model=model,
    messages=messages,
    tools=registry.format_tools(provider=PROVIDER, model=model),
)

tool_out = registry.execute(tool_name, args)
```

推荐的运行流程就是：

1. 构建一个 registry
2. 按当前 provider/model 把工具格式化
3. 让模型选择工具和参数
4. 按名称执行工具
5. 把工具结果回写到 `messages`

## 新增一个工具

在 `tool_runtime/builtin_tools/` 下创建一个新文件：

```python
from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "Return the given text."
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
        "additionalProperties": False,
    }

    def run(self, text: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {"text": text}


TOOL = EchoTool()
```

loader 会自动把它发现并加载进来。

## 测试

运行全部测试：

```bash
python -m unittest discover -v
```

只运行 tool runtime 相关测试：

```bash
python -m unittest -v tests.test_tool_runtime
```

运行语法检查：

```bash
python -m compileall -q .
```
