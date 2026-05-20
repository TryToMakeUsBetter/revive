"""命令行入口：python -m revive 或 revive (装包后)。"""

import logging
import os

from .bot import ChatBot
from .config import default_whitelist_path, load_full_config
from .llm import DeepSeek
from .wechat import ItchatClient

DEFAULT_SYSTEM_PROMPT = "你是一个友好的助手，用简短自然的口语回复。"


def _setup_logging() -> None:
    level = os.environ.get("REVIVE_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # itchat 自己很啰嗦，压到 WARNING 不让它淹没我们自己的日志
    logging.getLogger("itchat").setLevel(logging.WARNING)


def main() -> None:
    _setup_logging()
    log = logging.getLogger("revive.cli")

    cfg = load_full_config()
    log.info(
        "config loaded: whitelist_enabled=%s friends=%d groups=%d",
        cfg.whitelist.enabled,
        len(cfg.whitelist.friends),
        len(cfg.whitelist.groups),
    )
    if cfg.whitelist.enabled and not cfg.whitelist.friends and not cfg.whitelist.groups:
        log.warning(
            "白名单已启用但 %s 为空或不存在，机器人不会回复任何消息。",
            default_whitelist_path(),
        )

    bot = ChatBot(
        llm=DeepSeek(api_key=cfg.deepseek_api_key),
        client=ItchatClient(),
        whitelist_enabled=cfg.whitelist.enabled,
        friend_whitelist=cfg.whitelist.friends,
        group_whitelist=cfg.whitelist.groups,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )
    log.info("bot starting…")
    bot.run()


if __name__ == "__main__":
    main()
