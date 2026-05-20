"""加载 config.toml。

默认从当前工作目录读取，可通过 REVIVE_CONFIG 环境变量覆盖。
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


def default_config_path() -> Path:
    env = os.environ.get("REVIVE_CONFIG")
    return Path(env) if env else Path.cwd() / "config.toml"


@dataclass
class AppConfig:
    deepseek_api_key: str | None


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or default_config_path()
    data: dict = {}
    if path.exists():
        with path.open("rb") as f:
            data = tomllib.load(f)
    deepseek = data.get("deepseek", {}) or {}
    return AppConfig(deepseek_api_key=deepseek.get("api_key"))
