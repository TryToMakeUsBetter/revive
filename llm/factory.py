"""LLM 客户端工厂：根据配置创建对应的模型客户端。"""

from config import get_default_config, get_provider_config

from .base import BaseLLMClient
from .deepseek import DeepSeekClient
from .openai import OpenAIClient

# 提供商注册表：添加新模型只需在此注册即可
_PROVIDER_REGISTRY: dict[str, type[BaseLLMClient]] = {
    "deepseek": DeepSeekClient,
    "openai": OpenAIClient,
}


def create_client(provider: str | None = None) -> BaseLLMClient:
    """根据配置创建 LLM 客户端。

    Args:
        provider: 提供商名称（"deepseek", "openai" 等）。为 None 时使用默认配置。

    Returns:
        对应提供商的客户端实例。

    Raises:
        ValueError: 提供商未注册或配置缺失。
    """
    default_cfg = get_default_config()
    if provider is None:
        provider = default_cfg.get("provider", "deepseek")

    client_cls = _PROVIDER_REGISTRY.get(provider)
    if client_cls is None:
        available = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(f"未知的提供商: {provider}，可选: {available}")

    provider_cfg = get_provider_config(provider)
    api_key = provider_cfg.get("api_key", "")
    if not api_key:
        raise ValueError(
            f"提供商 '{provider}' 未配置 api_key，请在 config.toml 中设置 "
            f"或设置环境变量 {provider.upper()}_API_KEY"
        )
    model = provider_cfg.get("model", "deepseek-chat")

    return client_cls(
        api_key=api_key,
        model=model,
        base_url=provider_cfg.get("base_url", ""),
        timeout=provider_cfg.get("timeout", 30.0),
        max_retries=provider_cfg.get("max_retries", 2),
        organization=provider_cfg.get("organization"),
        project=provider_cfg.get("project"),
    )


def list_providers() -> list[str]:
    """列出所有已注册的提供商。"""
    return list(_PROVIDER_REGISTRY.keys())
