import logging
import time
from pathlib import Path

import requests

from ..config import load_config
from .base import LLM, Message

log = logging.getLogger("revive.llm.deepseek")


class DeepSeek(LLM):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 60.0,
        config_path: Path | str | None = None,
    ):
        if api_key is None:
            cfg = load_config(Path(config_path) if config_path else None)
            api_key = cfg.deepseek_api_key
            if not api_key:
                raise ValueError(
                    "未在 config.toml 的 [deepseek] 段中找到 api_key，"
                    "请参考 config.toml.example 创建配置文件，"
                    "或通过 REVIVE_CONFIG 环境变量指定路径。"
                )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 1.0,
        **kwargs,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            **kwargs,
        }
        log.info("POST /chat/completions model=%s msgs=%d", self.model, len(messages))
        t0 = time.monotonic()
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException:
            log.exception("HTTP error to DeepSeek (after %.2fs)", time.monotonic() - t0)
            raise
        elapsed = time.monotonic() - t0
        if resp.status_code != 200:
            log.error("DeepSeek %d in %.2fs: %s", resp.status_code, elapsed, resp.text[:300])
            resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        log.info(
            "DeepSeek 200 in %.2fs tokens=%s/%s",
            elapsed, usage.get("prompt_tokens"), usage.get("completion_tokens"),
        )
        return data["choices"][0]["message"]["content"]
