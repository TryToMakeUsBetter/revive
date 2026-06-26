"""OpenAI API 客户端实现（预留）。"""

import httpx

from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """OpenAI API 聊天客户端。

    支持标准 OpenAI Chat Completions API，也兼容其他 OpenAI 格式的 API。
    """

    def __init__(self, api_key: str, model: str = "gpt-4o",
                 base_url: str = "https://api.openai.com/v1", timeout: float = 30.0):
        super().__init__(api_key=api_key, model=model, base_url=base_url, timeout=timeout)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def reset(self) -> None:
        """清空对话历史。"""
        self._messages.clear()

    def chat(self, prompt: str, system: str | None = None) -> str:
        """发送一条消息并返回模型回复。"""
        if system and not self._messages:
            self._messages.append({"role": "system", "content": system})

        self._messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": self._messages,
            "stream": False,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            )
            resp.raise_for_status()

        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        self._messages.append({"role": "assistant", "content": reply})
        return reply
