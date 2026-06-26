# llm — 大语言模型客户端

统一的 LLM 客户端抽象，通过工厂模式支持多种模型提供商。

## 架构

```
llm/
├── base.py        # BaseLLMClient 抽象基类
├── deepseek.py    # DeepSeek API 实现
├── openai.py      # OpenAI API 实现（预留）
└── factory.py     # 工厂 + 提供商注册表
```

## 设计

```
                  ┌─────────────────┐
                  │  BaseLLMClient  │  ← 抽象基类
                  │                 │    · add_message(role, content) 注入任意角色
                  │                 │    · chat(content, system)     发送用户消息
                  │                 │    · reset() / history          历史管理
                  │                 │    · _send()  ← 子类唯一需实现
                  └────────┬────────┘
           ┌───────────────┼───────────────┐
           │                               │
   ┌───────┴───────┐               ┌───────┴───────┐
   │ DeepSeekClient│               │ OpenAIClient  │   ← 各自实现 _send()
   └───────────────┘               └───────────────┘
           │                               │
           └───────────────┬───────────────┘
                   ┌───────┴───────┐
                   │   factory.py  │  ← create_client() 工厂函数
                   └───────────────┘
```

## 使用

```python
from llm import create_client

client = create_client()             # 使用默认提供商（config.toml 中配置）
client = create_client("deepseek")   # 指定提供商

# 便捷对话
reply = client.chat("你好")                        # 自动 user → API → assistant
reply = client.chat("你好", system="你是翻译官")    # 带系统提示词

# 手动注入任意角色
client.add_message("system", "你是一个数学老师")
client.add_message("user", "1+1=?")
client.add_message("assistant", "答案是 2")
client.add_message("user", "那 2+2 呢？")
reply = client._send()                             # 直接调 API
client.add_message("assistant", reply)

client.reset()  # 清空历史
```

## 添加新模型

1. 新建 `llm/your_provider.py`，继承 `BaseLLMClient`，**只需实现 `_send()`**
2. 在 `factory.py` 的 `_PROVIDER_REGISTRY` 中注册：
   ```python
   from .your_provider import YourProviderClient
   _PROVIDER_REGISTRY["your_provider"] = YourProviderClient
   ```
3. 在 `config.toml` 的 `[providers.your_provider]` 中配置 api_key 和 base_url
