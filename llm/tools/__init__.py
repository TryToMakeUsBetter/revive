"""tools 子包：LLM 工具调用（function calling / tool_use）。

提供 @tool 装饰器，将 Python 函数暴露给 LLM 调用。
"""

from .registry import ToolRegistry

__all__ = ["ToolRegistry"]
