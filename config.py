"""配置模块：从 config.toml 读取应用配置，支持多模型提供商。"""

import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _get_config_path() -> str:
    """获取 config.toml 的绝对路径。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")


def load_config() -> dict:
    """加载并返回 config.toml 中的所有配置。"""
    config_path = _get_config_path()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_default_config() -> dict:
    """获取 [default] 段的配置（provider, model, system_prompt 等）。"""
    return load_config().get("default", {})


def get_provider_config(provider: str | None = None) -> dict:
    """获取指定提供商的配置。

    Args:
        provider: 提供商名称（如 "deepseek", "openai"）。为 None 时使用默认提供商。

    Returns:
        包含 api_key, base_url 等字段的字典。
    """
    config = load_config()
    if provider is None:
        provider = config.get("default", {}).get("provider", "deepseek")

    provider_cfg = config.get("providers", {}).get(provider, {})
    if not provider_cfg:
        raise ValueError(f"未找到提供商配置: {provider}")

    # 环境变量优先：{PROVIDER}_API_KEY，如 DEEPSEEK_API_KEY
    env_key = os.getenv(f"{provider.upper()}_API_KEY")
    if env_key:
        provider_cfg = {**provider_cfg, "api_key": env_key}

    return provider_cfg


def get_current_provider() -> str:
    """获取当前默认使用的提供商名称。"""
    return get_default_config().get("provider", "deepseek")
