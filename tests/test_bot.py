"""ChatBot 编排逻辑单元测试 —— 用 fake LLM + fake WeChatClient，不依赖外部服务。"""

import unittest

from revive import (
    ChatBot,
    IncomingMessage,
    LLM,
    Message,
    MessageHandler,
    WeChatClient,
)


class FakeLLM(LLM):
    def __init__(self, reply: str = "OK"):
        self.reply = reply
        self.calls: list[list[Message]] = []

    def chat(self, messages: list[Message], **kwargs) -> str:
        self.calls.append([Message(role=m.role, content=m.content) for m in messages])
        return self.reply


class FakeClient(WeChatClient):
    def __init__(self):
        self.sent: list[tuple[str, str]] = []
        self.handler: MessageHandler | None = None

    def login(self) -> None:
        pass

    def register_handler(self, handler: MessageHandler) -> None:
        self.handler = handler

    def send_text(self, text: str, to_id: str) -> None:
        self.sent.append((to_id, text))

    def run(self) -> None:
        pass


_MISSING = object()


def friend_msg(
    name: str,
    text: str,
    sender_id: str | None = None,
    sender_wxid=_MISSING,
) -> IncomingMessage:
    wxid = f"wxid_{name}" if sender_wxid is _MISSING else sender_wxid
    return IncomingMessage(
        sender_id=sender_id or f"@{name}",
        sender_name=name,
        sender_wxid=wxid,
        text=text,
        is_group=False,
        group_name=None,
        is_at_me=False,
    )


def group_msg(group: str, sender: str, text: str, is_at_me: bool) -> IncomingMessage:
    return IncomingMessage(
        sender_id=f"@@{group}",
        sender_name=sender,
        sender_wxid=None,
        text=text,
        is_group=True,
        group_name=group,
        is_at_me=is_at_me,
    )


class TestChatBot(unittest.TestCase):
    def _make(
        self,
        friends: set[str] | None = None,
        groups: set[str] | None = None,
        enabled: bool = True,
        **kwargs,
    ) -> tuple[ChatBot, FakeLLM, FakeClient]:
        llm = FakeLLM(reply=kwargs.pop("reply", "回复"))
        client = FakeClient()
        bot = ChatBot(
            llm=llm,
            client=client,
            whitelist_enabled=enabled,
            friend_whitelist=friends or set(),
            group_whitelist=groups or set(),
            **kwargs,
        )
        return bot, llm, client

    def test_friend_in_whitelist_gets_reply(self):
        bot, llm, client = self._make(friends={"wxid_张三"})
        bot.handle(friend_msg("张三", "你好"))
        self.assertEqual(client.sent, [("@张三", "回复")])
        self.assertEqual(len(llm.calls), 1)

    def test_friend_not_in_whitelist_ignored(self):
        bot, llm, client = self._make(friends={"wxid_张三"})
        bot.handle(friend_msg("李四", "你好"))
        self.assertEqual(client.sent, [])
        self.assertEqual(llm.calls, [])

    def test_friend_without_wxid_ignored_when_whitelist_on(self):
        bot, llm, client = self._make(friends={"wxid_张三"})
        bot.handle(friend_msg("张三", "你好", sender_wxid=None))
        self.assertEqual(client.sent, [])

    def test_whitelist_disabled_allows_all_friends(self):
        bot, llm, client = self._make(enabled=False)
        bot.handle(friend_msg("陌生人", "hi", sender_wxid=None))
        self.assertEqual(len(client.sent), 1)

    def test_whitelist_disabled_still_requires_at_in_group(self):
        bot, llm, client = self._make(enabled=False)
        bot.handle(group_msg("任何群", "张三", "随便聊", is_at_me=False))
        self.assertEqual(client.sent, [])
        bot.handle(group_msg("任何群", "张三", "@bot 在吗", is_at_me=True))
        self.assertEqual(len(client.sent), 1)

    def test_group_without_at_ignored(self):
        bot, llm, client = self._make(groups={"测试群"})
        bot.handle(group_msg("测试群", "张三", "随便聊聊", is_at_me=False))
        self.assertEqual(client.sent, [])

    def test_group_with_at_replied(self):
        bot, llm, client = self._make(groups={"测试群"})
        bot.handle(group_msg("测试群", "张三", "@bot 在吗", is_at_me=True))
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0][0], "@@测试群")

    def test_group_not_in_whitelist_ignored_even_with_at(self):
        bot, llm, client = self._make(groups={"另一个群"})
        bot.handle(group_msg("测试群", "张三", "@bot 在吗", is_at_me=True))
        self.assertEqual(client.sent, [])

    def test_history_accumulates_per_sender(self):
        bot, llm, client = self._make(friends={"wxid_张三", "wxid_李四"})
        bot.handle(friend_msg("张三", "第一句"))
        bot.handle(friend_msg("张三", "第二句"))
        bot.handle(friend_msg("李四", "你好"))
        zhang_second_call = llm.calls[1]
        self.assertEqual(len(zhang_second_call), 3)
        self.assertEqual(zhang_second_call[0].content, "第一句")
        self.assertEqual(zhang_second_call[1].role, "assistant")
        self.assertEqual(zhang_second_call[2].content, "第二句")
        li_call = llm.calls[2]
        self.assertEqual(len(li_call), 1)
        self.assertEqual(li_call[0].content, "你好")

    def test_system_prompt_inserted_once(self):
        bot, llm, client = self._make(
            friends={"wxid_张三"}, system_prompt="你是助手"
        )
        bot.handle(friend_msg("张三", "嗨"))
        bot.handle(friend_msg("张三", "再次嗨"))
        first = llm.calls[0]
        second = llm.calls[1]
        self.assertEqual(first[0].role, "system")
        self.assertEqual(first[0].content, "你是助手")
        system_count = sum(1 for m in second if m.role == "system")
        self.assertEqual(system_count, 1)

    def test_history_trimmed_but_system_kept(self):
        bot, llm, client = self._make(
            friends={"wxid_张三"}, system_prompt="你是助手", max_history=5
        )
        for i in range(10):
            bot.handle(friend_msg("张三", f"第{i}句"))
        hist = bot.histories["@张三"]
        self.assertLessEqual(len(hist), 5)
        self.assertEqual(hist[0].role, "system")
        self.assertEqual(hist[0].content, "你是助手")


if __name__ == "__main__":
    unittest.main(verbosity=2)
