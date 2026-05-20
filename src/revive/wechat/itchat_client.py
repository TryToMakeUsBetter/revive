import logging

from .base import WeChatClient, IncomingMessage, MessageHandler

log = logging.getLogger("revive.wechat.itchat")


class ItchatClient(WeChatClient):
    def __init__(self, hot_reload: bool = True, enable_cmd_qr: int = 2):
        self.hot_reload = hot_reload
        self.enable_cmd_qr = enable_cmd_qr
        self._handler: MessageHandler | None = None
        self._itchat = None
        self._started_at: int = 0

    def login(self) -> None:
        import time
        import itchat
        from itchat import content  # noqa: F401  ensure itchat.content is loaded
        self._itchat = itchat
        self._started_at = int(time.time())
        log.info("itchat.auto_login started (hot_reload=%s)", self.hot_reload)
        itchat.auto_login(hotReload=self.hot_reload, enableCmdQR=self.enable_cmd_qr)
        log.info("itchat login finished")

    def register_handler(self, handler: MessageHandler) -> None:
        if self._itchat is None:
            raise RuntimeError("login() must be called before register_handler()")
        self._handler = handler
        itchat = self._itchat
        from itchat import content

        @itchat.msg_register(
            [content.TEXT],
            isFriendChat=True,
            isGroupChat=True,
        )
        def _dispatch(msg):
            create_time = int(msg.get("CreateTime", 0) or 0)
            from_user = msg.get("FromUserName", "") or ""
            preview = (msg.get("Text", "") or "")[:80]
            if create_time and create_time < self._started_at:
                log.debug(
                    "drop stale msg from=%s create_time=%d started_at=%d text=%r",
                    from_user, create_time, self._started_at, preview,
                )
                return
            log.info("recv msg from=%s text=%r", from_user, preview)
            try:
                incoming = self._to_incoming(msg)
                assert self._handler is not None
                self._handler(incoming)
            except Exception:
                log.exception("dispatch failed for msg from=%s", from_user)

    def send_text(self, text: str, to_id: str) -> None:
        if self._itchat is None:
            raise RuntimeError("login() must be called before send_text()")
        log.info("send_text to=%s text=%r", to_id, text[:80])
        self._itchat.send(text, toUserName=to_id)

    def run(self) -> None:
        if self._itchat is None:
            raise RuntimeError("login() must be called before run()")
        self._itchat.run(blockThread=True)

    @staticmethod
    def _to_incoming(msg) -> IncomingMessage:
        from_user = msg.get("FromUserName", "") or ""
        is_group = from_user.startswith("@@")
        user = msg.get("User", {}) or {}
        user_nick = user.get("NickName", "") or ""
        if is_group:
            sender_name = msg.get("ActualNickName", "") or ""
            group_name = user_nick
            sender_wxid = None
        else:
            sender_name = user_nick
            group_name = None
            alias = user.get("Alias", "") or ""
            sender_wxid = alias or None
        return IncomingMessage(
            sender_id=from_user,
            sender_name=sender_name,
            sender_wxid=sender_wxid,
            text=msg.get("Text", "") or "",
            is_group=is_group,
            group_name=group_name,
            is_at_me=bool(msg.get("IsAt", False)),
        )
