"""Web 调试对话客户端 —— 实现 WeChatClient 接口，让 ChatBot 不改一行就能跑。

Web 是请求/响应模式，跟 IM "客户端主动 push" 不同：
- 用户 POST 一条消息 → 我们构造 IncomingMessage → 同步调 ChatBot.handle()
- handle() 内部会调 client.send_text(reply, sender_id) —— 我们把 reply 暂存到当前线程
- 处理完后从线程局部空间取出 reply 返回给前端

线程局部存储是为了让多个并发请求不串话（FastAPI 同步路由会跑在 threadpool）。
"""

import threading
from typing import Optional

from .wechat import IncomingMessage, MessageHandler, WeChatClient


class WebChatClient(WeChatClient):
    def __init__(self):
        self._handler: Optional[MessageHandler] = None
        self._tls = threading.local()

    def login(self) -> None:
        return

    def register_handler(self, handler: MessageHandler) -> None:
        self._handler = handler

    def send_text(self, text: str, to_id: str) -> None:
        replies = getattr(self._tls, "replies", None)
        if replies is None:
            replies = []
            self._tls.replies = replies
        replies.append(text)

    def run(self) -> None:
        return

    def deliver(self, sender_id: str, sender_name: str, text: str) -> list[str]:
        """同步处理一条来自 Web 的消息，返回 ChatBot 产生的回复列表。"""
        if self._handler is None:
            raise RuntimeError("ChatBot handler 未注册")
        self._tls.replies = []
        msg = IncomingMessage(
            sender_id=sender_id,
            sender_name=sender_name,
            sender_wxid=sender_id,
            text=text,
            is_group=False,
            group_name=None,
            is_at_me=False,
        )
        self._handler(msg)
        replies = list(getattr(self._tls, "replies", []))
        self._tls.replies = []
        return replies
