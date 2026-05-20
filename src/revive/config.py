"""集中处理 config.toml + whitelist.txt 的加载。

默认配置/白名单从当前工作目录读取，方便用户在项目根目录运行 `python -m revive` 或
`uvicorn revive.server:app`。也可以通过环境变量 REVIVE_CONFIG / REVIVE_WHITELIST 覆盖。
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


def default_config_path() -> Path:
    env = os.environ.get("REVIVE_CONFIG")
    return Path(env) if env else Path.cwd() / "config.toml"


def default_whitelist_path() -> Path:
    env = os.environ.get("REVIVE_WHITELIST")
    return Path(env) if env else Path.cwd() / "whitelist.txt"


@dataclass
class WhitelistConfig:
    enabled: bool = False
    friends: set[str] = field(default_factory=set)
    groups: set[str] = field(default_factory=set)


@dataclass
class AppConfig:
    deepseek_api_key: str | None
    whitelist: WhitelistConfig


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or default_config_path()
    data: dict = {}
    if path.exists():
        with path.open("rb") as f:
            data = tomllib.load(f)
    deepseek = data.get("deepseek", {}) or {}
    whitelist_section = data.get("whitelist", {}) or {}
    return AppConfig(
        deepseek_api_key=deepseek.get("api_key"),
        whitelist=WhitelistConfig(enabled=bool(whitelist_section.get("enabled", False))),
    )


def load_whitelist_file(path: Path | None = None) -> tuple[set[str], set[str]]:
    p = path or default_whitelist_path()
    if not p.exists():
        return set(), set()
    friends: set[str] = set()
    groups: set[str] = set()
    section = "friends"
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section == "groups":
            groups.add(line)
        else:
            friends.add(line)
    return friends, groups


def load_full_config(
    config_path: Path | None = None,
    whitelist_path: Path | None = None,
) -> AppConfig:
    cfg = load_config(config_path)
    if cfg.whitelist.enabled:
        cfg.whitelist.friends, cfg.whitelist.groups = load_whitelist_file(whitelist_path)
    return cfg
