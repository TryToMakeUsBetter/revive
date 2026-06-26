"""DeepSeek API 客户端实现。"""

from openai import OpenAI

from .base import BaseLLMClient


class DeepSeekClient(BaseLLMClient):
    """DeepSeek API 聊天客户端，基于 openai SDK。

    DeepSeek 提供与 OpenAI 兼容的 API，可直接使用 openai 官方 SDK 接入。
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com/v1", timeout: float = 30.0,
                 max_retries: int = 2, **kwargs):
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries)
        self._client = OpenAI(
            api_key=self.api_key, base_url=self.base_url,
            timeout=self.timeout, max_retries=self.max_retries,
            **kwargs,
        )

    def _send(self) -> str:
        """调用 DeepSeek API，发送当前消息历史并返回回复文本。"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=self._messages,
            stream=False,
        )
        return response.choices[0].message.content
