"""ChatBot 编排逻辑单元测试 —— 用 fake LLM + fake ChatClient，不依赖外部服务。"""

import unittest

from revive import (
    ChatBot,
    ChatClient,
    IncomingMessage,
    LLM,
    Message,
    MessageHandler,
)


class FakeLLM(LLM):
    def __init__(self, reply: str = "OK"):
        self.reply = reply
        self.calls: list[list[Message]] = []

    def chat(self, messages: list[Message], **kwargs) -> str:
        self.calls.append([Message(role=m.role, content=m.content) for m in messages])
        return self.reply


class FakeClient(ChatClient):
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


def friend_msg(name: str, text: str, sender_id: str | None = None) -> IncomingMessage:
    return IncomingMessage(
        sender_id=sender_id or f"@{name}",
        sender_name=name,
        sender_account=f"acct_{name}",
        text=text,
        is_group=False,
        group_name=None,
        is_at_me=False,
    )


def group_msg(group: str, sender: str, text: str, is_at_me: bool) -> IncomingMessage:
    return IncomingMessage(
        sender_id=f"@@{group}",
        sender_name=sender,
        sender_account=None,
        text=text,
        is_group=True,
        group_name=group,
        is_at_me=is_at_me,
    )


class TestChatBot(unittest.TestCase):
    def _make(self, **kwargs) -> tuple[ChatBot, FakeLLM, FakeClient]:
        llm = FakeLLM(reply=kwargs.pop("reply", "回复"))
        client = FakeClient()
        bot = ChatBot(llm=llm, client=client, **kwargs)
        return bot, llm, client

    def test_friend_message_gets_reply(self):
        bot, llm, client = self._make()
        bot.handle(friend_msg("张三", "你好"))
        self.assertEqual(client.sent, [("@张三", "回复")])
        self.assertEqual(len(llm.calls), 1)

    def test_group_without_at_ignored(self):
        bot, llm, client = self._make()
        bot.handle(group_msg("某群", "张三", "随便聊聊", is_at_me=False))
        self.assertEqual(client.sent, [])

    def test_group_with_at_replied(self):
        bot, llm, client = self._make()
        bot.handle(group_msg("某群", "张三", "@bot 在吗", is_at_me=True))
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0][0], "@@某群")

    def test_history_accumulates_per_sender(self):
        bot, llm, client = self._make()
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
        bot, llm, client = self._make(system_prompt="你是助手")
        bot.handle(friend_msg("张三", "嗨"))
        bot.handle(friend_msg("张三", "再次嗨"))
        first = llm.calls[0]
        second = llm.calls[1]
        self.assertEqual(first[0].role, "system")
        self.assertEqual(first[0].content, "你是助手")
        system_count = sum(1 for m in second if m.role == "system")
        self.assertEqual(system_count, 1)

    def test_history_trimmed_but_system_kept(self):
        bot, llm, client = self._make(system_prompt="你是助手", max_history=5)
        for i in range(10):
            bot.handle(friend_msg("张三", f"第{i}句"))
        hist = bot.histories["@张三"]
        self.assertLessEqual(len(hist), 5)
        self.assertEqual(hist[0].role, "system")
        self.assertEqual(hist[0].content, "你是助手")


if __name__ == "__main__":
    unittest.main(verbosity=2)
