import logging

from .llm import LLM, Message
from .wechat import WeChatClient, IncomingMessage

log = logging.getLogger("revive.bot")


class ChatBot:
    def __init__(
        self,
        llm: LLM,
        client: WeChatClient,
        whitelist_enabled: bool,
        friend_whitelist: set[str],
        group_whitelist: set[str],
        system_prompt: str | None = None,
        max_history: int = 20,
    ):
        self.llm = llm
        self.client = client
        self.whitelist_enabled = whitelist_enabled
        self.friend_whitelist = friend_whitelist
        self.group_whitelist = group_whitelist
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.histories: dict[str, list[Message]] = {}

    def _allowed(self, m: IncomingMessage) -> bool:
        if m.is_group:
            if not m.is_at_me:
                log.debug("drop group msg without @ from=%s group=%s", m.sender_name, m.group_name)
                return False
            if not self.whitelist_enabled:
                return True
            ok = m.group_name in self.group_whitelist
            if not ok:
                log.info("group not in whitelist: %s", m.group_name)
            return ok
        if not self.whitelist_enabled:
            return True
        if not m.sender_wxid:
            log.info("friend has no wxid, drop: name=%s", m.sender_name)
            return False
        ok = m.sender_wxid in self.friend_whitelist
        if not ok:
            log.info("friend not in whitelist: name=%s wxid=%s", m.sender_name, m.sender_wxid)
        return ok

    def handle(self, m: IncomingMessage) -> None:
        if not self._allowed(m):
            return
        log.info(
            "handle msg group=%s sender=%s wxid=%s text=%r",
            m.group_name, m.sender_name, m.sender_wxid, m.text[:80],
        )
        hist = self.histories.setdefault(m.sender_id, [])
        if self.system_prompt and not hist:
            hist.append(Message(role="system", content=self.system_prompt))
        hist.append(Message(role="user", content=m.text))
        try:
            log.info("calling LLM (history_len=%d)", len(hist))
            reply = self.llm.chat(hist)
            log.info("LLM reply: %r", reply[:80])
        except Exception:
            log.exception("LLM call failed; rolling back last user msg")
            hist.pop()
            return
        hist.append(Message(role="assistant", content=reply))
        self._trim(hist)
        try:
            self.client.send_text(reply, m.sender_id)
        except Exception:
            log.exception("send_text failed for to=%s", m.sender_id)

    def _trim(self, hist: list[Message]) -> None:
        if len(hist) <= self.max_history:
            return
        head: list[Message] = []
        body = hist
        if hist and hist[0].role == "system":
            head = [hist[0]]
            body = hist[1:]
        keep = self.max_history - len(head)
        hist[:] = head + body[-keep:]

    def run(self) -> None:
        self.client.login()
        self.client.register_handler(self.handle)
        self.client.run()
