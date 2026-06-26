"""LLM 客户端抽象基类，定义所有模型提供商必须实现的接口。"""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """大语言模型客户端抽象基类。

    所有模型提供商（DeepSeek、OpenAI、Claude 等）都必须继承此类并实现 _send()。
    """

    VALID_ROLES = frozenset({"system", "user", "assistant", "tool"})

    def __init__(self, api_key: str, model: str, base_url: str,
                 timeout: float = 30.0, max_retries: int = 2):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._messages: list[dict] = []

    # ── 公共方法 ──────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        """向对话历史中添加一条消息，支持所有标准 role。

        Args:
            role: 消息角色，支持 system / user / assistant / tool。
            content: 消息内容。
        """
        if role not in self.VALID_ROLES:
            raise ValueError(f"无效的 role: {role}，可选: {', '.join(sorted(self.VALID_ROLES))}")
        self._messages.append({"role": role, "content": content})

    def chat(self, content: str, system: str | None = None) -> str:
        """发送一条用户消息并返回模型回复（便利方法）。

        等价于 add_message("user", content) + 调用 API + add_message("assistant", reply)。

        Args:
            content: 用户消息内容。
            system: 可选的系统提示词，仅在对话历史为空时生效。

        Returns:
            模型的文本回复。
        """
        if system and not self._messages:
            self.add_message("system", system)
        self.add_message("user", content)
        reply = self._send()
        self.add_message("assistant", reply)
        return reply

    def reset(self) -> None:
        """清空对话历史。"""
        self._messages.clear()

    @property
    def history(self) -> list[dict]:
        """返回当前对话历史（只读副本）。"""
        return list(self._messages)

    # ── 子类必须实现 ──────────────────────────────────────────

    @abstractmethod
    def _send(self) -> str:
        """调用 API 发送当前 _messages 并返回模型回复文本。

        子类只需实现此方法，无需处理消息拼接和历史管理。
        """
        ...
