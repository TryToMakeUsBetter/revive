"""LLM 客户端抽象基类，定义所有模型提供商必须实现的接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from .tools import ToolRegistry


class BaseLLMClient(ABC):
    """大语言模型客户端抽象基类。

    所有模型提供商（DeepSeek、OpenAI、Claude 等）都必须继承此类并实现 _send()。

    内置 ToolRegistry，支持 function calling / tool_use。
    """

    VALID_ROLES = frozenset({"system", "user", "assistant", "tool"})

    def __init__(self, api_key: str, model: str, base_url: str,
                 timeout: float = 30.0, max_retries: int = 2,
                 max_tool_rounds: int = 10):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_tool_rounds = max_tool_rounds  # tool_use 最大循环轮数
        self._messages: list[dict] = []
        self._tool_registry = ToolRegistry()

    # ── 公共方法 ──────────────────────────────────────────────

    def register_tool(self, func: Callable, name: str | None = None,
                      description: str = "") -> None:
        """注册一个函数为 LLM 可调用的工具。

        Args:
            func: Python 函数。
            name: 工具名称，默认使用函数名。
            description: 描述，帮助模型理解何时调用。
        """
        self._tool_registry.register(func, name=name, description=description)

    def add_message(self, role: str, content: str) -> None:
        """向对话历史中添加一条消息，支持所有标准 role。

        Args:
            role: 消息角色，支持 system / user / assistant / tool。
            content: 消息内容。
        """
        if role not in self.VALID_ROLES:
            raise ValueError(
                f"无效的 role: {role}，可选: {', '.join(sorted(self.VALID_ROLES))}"
            )
        self._messages.append({"role": role, "content": content})

    def chat(self, content: str, system: str | None = None,
             use_tools: bool = False) -> str:
        """发送一条用户消息并返回模型回复。

        当 use_tools=True 且模型决定调用工具时，自动执行工具并将结果送回，
        循环直到模型输出最终文本回复。

        Args:
            content: 用户消息内容。
            system: 可选的系统提示词，仅在对话历史为空时生效。
            use_tools: 是否启用已注册的工具。

        Returns:
            模型的最终文本回复。
        """
        if system and not self._messages:
            self.add_message("system", system)
        self.add_message("user", content)

        tools = self._tool_registry.to_openai_format() if use_tools else None

        for _ in range(self.max_tool_rounds):
            msg = self._send(tools=tools)
            tool_calls = msg.get("tool_calls")

            if not tool_calls:
                reply = msg.get("content", "")
                self.add_message("assistant", reply)
                return reply

            # 模型请求调用工具 → 执行 → 结果追加到消息历史
            self._messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls,
            })
            for tc in tool_calls:
                fn = tc["function"]
                result = self._tool_registry.execute(fn["name"], fn["arguments"])
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        # 超限兜底
        self.add_message("user", "请根据以上工具调用结果直接给出最终回复，不要再调用工具。")
        return self._send(tools=None).get("content", "")

    def reset(self) -> None:
        """清空对话历史。"""
        self._messages.clear()

    @property
    def history(self) -> list[dict]:
        """返回当前对话历史（只读副本）。"""
        return list(self._messages)

    @property
    def tools(self) -> list[str]:
        """已注册工具名称列表。"""
        return self._tool_registry.list_names()

    # ── 子类必须实现 ──────────────────────────────────────────

    @abstractmethod
    def _send(self, tools: list[dict] | None = None) -> dict:
        """调用 API 发送当前 _messages 并返回原始消息对象。

        Args:
            tools: OpenAI 格式的工具定义列表，None 表示不启用 tool_use。

        Returns:
            dict，包含:
                content:    str | None — 文本回复（tool_use 时为 None）
                tool_calls: list | None — 工具调用列表（OpenAI 标准格式），每项含:
                    id:       str
                    type:     "function"
                    function: {"name": str, "arguments": str}
        """
        ...
