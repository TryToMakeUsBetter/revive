"""工具注册表：提供 @tool 装饰器，将 Python 函数注册为 LLM 可调用的工具。"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


class ToolRegistry:
    """工具注册表，管理已注册的函数并提供 OpenAI 兼容的工具定义。"""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, func: Callable, name: str | None = None,
                 description: str = "") -> None:
        """注册一个函数为可用工具。

        Args:
            func: 要注册的函数。
            name: 工具名称，默认使用函数名。
            description: 工具描述，供模型理解用途。
        """
        tool_name = name or func.__name__
        self._tools[tool_name] = func
        # 将元数据附加到函数对象上
        func._tool_name = tool_name  # type: ignore[attr-defined]
        func._tool_description = description  # type: ignore[attr-defined]

    def execute(self, name: str, arguments: str | dict) -> str:
        """按名称执行工具函数。

        Args:
            name: 工具名称。
            arguments: JSON 字符串或字典形式的参数。

        Returns:
            函数的字符串返回值。

        Raises:
            KeyError: 工具未注册。
        """
        func = self._tools.get(name)
        if func is None:
            return json.dumps({"error": f"未知工具: {name}"})
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        try:
            result = func(**arguments)
            return str(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def to_openai_format(self) -> list[dict]:
        """转为 OpenAI Chat Completions API 的 tools 格式。

        依赖函数签名中的参数类型注解来推断参数 schema。
        """
        tools = []
        for name, func in self._tools.items():
            desc = getattr(func, "_tool_description", "")
            props = _infer_parameters(func)
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": list(props.keys()),
                    },
                },
            })
        return tools

    def list_names(self) -> list[str]:
        """列出所有已注册工具的名称。"""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ── 辅助函数 ──────────────────────────────────────────────────

def _infer_parameters(func: Callable) -> dict[str, dict]:
    """从函数类型注解推断 OpenAI tool parameters schema。"""
    import inspect

    props = {}
    type_map = {
        str: "string", int: "integer", float: "number",
        bool: "boolean", list: "array", dict: "object",
    }
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        py_type = param.annotation if param.annotation is not inspect.Parameter.empty else str
        json_type = type_map.get(py_type, "string")
        props[param_name] = {"type": json_type, "description": f"{param_name} 参数"}
    return props
