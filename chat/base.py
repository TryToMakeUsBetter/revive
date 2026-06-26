"""LLM 客户端抽象基类，定义所有模型提供商必须实现的接口。"""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """大语言模型客户端抽象基类。

    所有模型提供商（DeepSeek、OpenAI、Claude 等）都必须继承此类并实现全部抽象方法。
    """

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._messages: list[dict] = []

    @abstractmethod
    def chat(self, prompt: str, system: str | None = None) -> str:
        """发送一条消息并返回模型回复。

        Args:
            prompt: 用户输入。
            system: 可选的系统提示词，仅首次对话时生效。

        Returns:
            模型的文本回复。
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """清空对话历史。"""
        ...

    @property
    def history(self) -> list[dict]:
        """返回当前对话历史（只读副本）。"""
        return list(self._messages)
