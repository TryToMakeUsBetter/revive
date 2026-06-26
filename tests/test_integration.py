"""集成测试：覆盖配置读取、工厂创建、DeepSeek API 真实调用、抽象接口。

运行方式：
    python -m pytest tests/ -v
    python -m unittest tests.test_integration -v
"""

import os
import unittest

from config import (
    load_config,
    get_default_config,
    get_provider_config,
    get_current_provider,
)
from llm import BaseLLMClient, create_client, list_providers
from llm.deepseek import DeepSeekClient
from llm.openai import OpenAIClient


# ── 配置模块测试 ──────────────────────────────────────────────

class TestConfigModule(unittest.TestCase):
    """测试 config.py 的配置读取功能。"""

    def test_load_config_returns_dict(self):
        cfg = load_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn("default", cfg)
        self.assertIn("providers", cfg)

    def test_get_default_config(self):
        default = get_default_config()
        self.assertEqual(default["provider"], "deepseek")
        self.assertEqual(default["model"], "deepseek-chat")
        self.assertIn("system_prompt", default)

    def test_get_provider_config_deepseek(self):
        cfg = get_provider_config("deepseek")
        self.assertIn("api_key", cfg)
        self.assertIn("base_url", cfg)
        self.assertTrue(cfg["api_key"].startswith("sk-"))
        self.assertEqual(cfg["base_url"], "https://api.deepseek.com/v1")

    def test_get_provider_config_default_provider(self):
        cfg = get_provider_config()  # 不传参，用默认
        self.assertIn("api_key", cfg)
        self.assertTrue(cfg["api_key"].startswith("sk-"))

    def test_get_provider_config_nonexistent_raises(self):
        with self.assertRaises(ValueError):
            get_provider_config("nonexistent_provider")

    def test_get_current_provider(self):
        self.assertEqual(get_current_provider(), "deepseek")

    def test_env_var_overrides_api_key(self):
        """环境变量 {PROVIDER}_API_KEY 优先于配置文件。"""
        os.environ["DEEPSEEK_API_KEY"] = "sk-env-override-test"
        try:
            cfg = get_provider_config("deepseek")
            self.assertEqual(cfg["api_key"], "sk-env-override-test")
        finally:
            del os.environ["DEEPSEEK_API_KEY"]


# ── 工厂模块测试 ──────────────────────────────────────────────

class TestFactory(unittest.TestCase):
    """测试 llm/factory.py 的工厂创建逻辑。"""

    def test_list_providers(self):
        providers = list_providers()
        self.assertIn("deepseek", providers)
        self.assertIn("openai", providers)

    def test_create_client_default(self):
        client = create_client()
        self.assertIsInstance(client, DeepSeekClient)
        self.assertEqual(client.model, "deepseek-chat")
        self.assertEqual(client.base_url, "https://api.deepseek.com/v1")

    def test_create_client_explicit_deepseek(self):
        client = create_client("deepseek")
        self.assertIsInstance(client, DeepSeekClient)

    def test_create_client_unknown_provider_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_client("unknown_provider")
        self.assertIn("未知的提供商", str(ctx.exception))

    def test_create_client_openai_raises_without_key(self):
        """OpenAI 没有配置 api_key 时应报错。"""
        with self.assertRaises(ValueError):
            create_client("openai")


# ── DeepSeek API 集成测试（真实 API 调用）────────────────────

class TestDeepSeekIntegration(unittest.TestCase):
    """端到端测试：通过 DeepSeek API 验证聊天功能。

    这些测试会真实调用 DeepSeek API，需要有效的 api_key。
    """

    @classmethod
    def setUpClass(cls):
        cls.client = create_client("deepseek")

    def setUp(self):
        self.client.reset()

    def test_single_chat_returns_non_empty_string(self):
        reply = self.client.chat("回复'OK'，不要其他内容")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply.strip()), 0)
        self.assertIn("OK", reply)

    def test_multi_turn_conversation_preserves_context(self):
        """多轮对话应记住上文。"""
        self.client.chat("我接下来会问你一个问题，请记住我的名字叫小明")
        reply = self.client.chat("我叫什么名字？")
        self.assertIn("小明", reply)
        self.assertGreaterEqual(len(self.client.history), 4)  # 2 user + 2 assistant

    def test_history_grows_with_each_message(self):
        self.assertEqual(len(self.client.history), 0)
        self.client.chat("你好")
        self.assertEqual(len(self.client.history), 2)  # user + assistant
        self.client.chat("再见")
        self.assertEqual(len(self.client.history), 4)

    def test_reset_clears_history(self):
        self.client.chat("你好")
        self.assertGreater(len(self.client.history), 0)
        self.client.reset()
        self.assertEqual(len(self.client.history), 0)

    def test_system_prompt_is_effective(self):
        """系统提示词应该影响模型行为。"""
        self.client.reset()
        reply = self.client.chat(
            "请用中文回复'收到'",
            system="你是一个只会说法语的助手，无论如何都只用法语回复",
        )
        # 法语助手应该用法语回复，不应该出现"收到"
        self.assertNotIn("收到", reply)

    def test_system_prompt_only_applied_first_time(self):
        """系统提示词只在首次对话时生效，reset 后可重新设置。"""
        self.client.chat("记住：1+1=3", system="你是一个数学白痴，1+1=3")
        self.client.chat("1+1=?")
        reply = self.client.chat("再确认一次，1+1=?")
        self.assertIn("3", reply)

    def test_chat_with_wrong_api_key_raises(self):
        bad_client = DeepSeekClient(api_key="sk-invalid-key", model="deepseek-chat")
        with self.assertRaises(Exception):
            bad_client.chat("你好")


# ── 抽象基类接口测试 ──────────────────────────────────────────

class TestBaseLLMClient(unittest.TestCase):
    """测试 BaseLLMClient 抽象接口约束。"""

    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            BaseLLMClient(api_key="sk-test", model="test", base_url="https://test.com")  # type: ignore[abstract]

    def test_concrete_clients_are_subclasses(self):
        self.assertTrue(issubclass(DeepSeekClient, BaseLLMClient))
        self.assertTrue(issubclass(OpenAIClient, BaseLLMClient))

    def test_concrete_clients_have_required_methods(self):
        for cls in (DeepSeekClient, OpenAIClient):
            self.assertTrue(hasattr(cls, "_send"), f"{cls.__name__} 缺少 _send 方法")
            self.assertTrue(hasattr(cls, "chat"), f"{cls.__name__} 缺少 chat 方法")
            self.assertTrue(hasattr(cls, "add_message"), f"{cls.__name__} 缺少 add_message 方法")

    def test_history_returns_copy_not_reference(self):
        client = create_client("deepseek")
        client.chat("嗨")
        hist = client.history
        hist.clear()
        # 原历史不应受影响
        self.assertGreater(len(client.history), 0)
        client.reset()

    # ── add_message 通用消息注入 ─────────────────────────────

    def test_add_message_valid_roles(self):
        client = create_client("deepseek")
        for role in ("system", "user", "assistant", "tool"):
            client.reset()
            client.add_message(role, f"test {role}")
            self.assertEqual(len(client.history), 1)
            self.assertEqual(client.history[0]["role"], role)
        client.reset()

    def test_add_message_invalid_role_raises(self):
        client = create_client("deepseek")
        with self.assertRaises(ValueError):
            client.add_message("invalid_role", "test")

    def test_add_message_injects_prebuilt_history(self):
        """通过 add_message 注入预置对话，模型应感知上下文。"""
        client = create_client("deepseek")
        client.reset()
        # 注入一段完整对话
        client.add_message("system", "你的名字是小Q，只会说中文")
        client.add_message("user", "请问我的名字是什么？")
        client.add_message("assistant", "对不起，我还不知道你的名字，能告诉我吗？")
        client.add_message("user", "我叫小明")
        client.add_message("assistant", "好的小明，我记住了！")
        # 现在问 —— 不走 chat 的 system 参数，直接用 _send
        client.add_message("user", "我叫什么名字？你的名字是什么？")
        reply = client._send()
        client.add_message("assistant", reply)
        self.assertIn("小明", reply)
        self.assertIn("小Q", reply)
        client.reset()


# ── 运行入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
