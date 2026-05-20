"""Integration tests that hit the real DeepSeek API.

API key is loaded from tests/deepseek_test.config (gitignored via *_test.config).
File format: KEY=VALUE per line. Falls back to DEEPSEEK_API_KEY env var.

Tests are skipped automatically when no key is found.
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm import DeepSeek, Message


CONFIG_PATH = Path(__file__).parent / "deepseek_test.config"


def _load_api_key() -> str | None:
    if CONFIG_PATH.exists():
        for line in CONFIG_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "DEEPSEEK_API_KEY":
                return value.strip()
    return os.environ.get("DEEPSEEK_API_KEY")


API_KEY = _load_api_key()
HAS_KEY = bool(API_KEY)


@unittest.skipUnless(HAS_KEY, "DEEPSEEK_API_KEY not set")
class TestDeepSeekIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = DeepSeek(api_key=API_KEY)

    def test_basic_chat(self):
        """模型能返回一个非空字符串。"""
        reply = self.client.chat(
            [Message(role="user", content="说一句问候语")],
            max_tokens=64,
        )
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply.strip()), 0)
        print(f"\n[basic_chat] -> {reply!r}")

    def test_system_prompt_is_respected(self):
        """system 指令能影响输出 —— 强制只输出一个固定 token。"""
        reply = self.client.chat(
            [
                Message(
                    role="system",
                    content="无论用户说什么，你只回复两个字：收到。不要加标点、不要解释。",
                ),
                Message(role="user", content="今天天气怎么样？"),
            ],
            temperature=0.0,
            max_tokens=16,
        )
        print(f"\n[system_prompt] -> {reply!r}")
        self.assertIn("收到", reply)

    def test_multi_turn_context(self):
        """多轮上下文有效 —— 模型能记住之前提到的名字。"""
        history = [
            Message(role="user", content="请记住一个名字：陈彼得。"),
            Message(role="assistant", content="好的，我已经记住了陈彼得这个名字。"),
            Message(role="user", content="刚才我让你记的名字是什么？只回名字本身。"),
        ]
        reply = self.client.chat(history, temperature=0.0, max_tokens=32)
        print(f"\n[multi_turn] -> {reply!r}")
        self.assertIn("陈彼得", reply)

    def test_max_tokens_limits_output(self):
        """max_tokens 透传生效 —— 输出不会无限长。"""
        reply = self.client.chat(
            [Message(role="user", content="请写一段 500 字的散文，描述秋天。")],
            max_tokens=20,
        )
        print(f"\n[max_tokens] -> {reply!r} (len={len(reply)})")
        # 20 tokens 折算成中文字符，远小于 500
        self.assertLess(len(reply), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
