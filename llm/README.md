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
                  │  BaseLLMClient  │  ← 抽象基类：chat() / reset() / history
                  └────────┬────────┘
           ┌───────────────┼───────────────┐
           │                               │
   ┌───────┴───────┐               ┌───────┴───────┐
   │ DeepSeekClient│               │ OpenAIClient  │   ← 具体实现
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

reply = client.chat("你好")
client.reset()
```

## 添加新模型

1. 新建 `llm/your_provider.py`，继承 `BaseLLMClient`，实现 `chat()` 和 `reset()`
2. 在 `factory.py` 的 `_PROVIDER_REGISTRY` 中注册：
   ```python
   from .your_provider import YourProviderClient
   _PROVIDER_REGISTRY["your_provider"] = YourProviderClient
   ```
3. 在 `config.toml` 的 `[providers.your_provider]` 中配置 api_key 和 base_url
