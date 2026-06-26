# llm — 大语言模型客户端

统一的 LLM 客户端抽象，基于 [openai](https://pypi.org/project/openai/) 官方 SDK，通过工厂模式支持多种模型提供商。

## 依赖

```bash
pip install openai
```

## 架构

```
llm/
├── base.py        # BaseLLMClient 抽象基类
├── deepseek.py    # DeepSeek API 实现
├── openai.py      # OpenAI API 实现
├── factory.py     # 工厂 + 提供商注册表
└── tools/         # 工具定义与注册
    ├── __init__.py
    └── registry.py  # ToolRegistry + @tool 装饰器
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

# ── 便捷对话 ──
reply = client.chat("你好")                        # 自动 user → API → assistant
reply = client.chat("你好", system="你是翻译官")    # 带系统提示词

# ── 手动注入任意角色 ──
client.add_message("system", "你是一个数学老师")
client.add_message("user", "1+1=?")
client.add_message("assistant", "答案是 2")
client.add_message("user", "那 2+2 呢？")
msg = client._send()                               # 返回 {"content": ..., "tool_calls": ...}
client.add_message("assistant", msg["content"])

# ── Tool Use（function calling）──
def get_weather(city: str) -> str:
    weather = {"北京": "晴天 25°C", "上海": "多云 28°C"}
    return weather.get(city, "未知城市")

client.register_tool(get_weather, description="获取指定城市的天气")
reply = client.chat("北京天气怎么样？", use_tools=True)
# 模型会自动调用 get_weather("北京")，将结果送回，最终输出自然语言回复

client.reset()  # 清空历史
```

## 添加新模型

1. 新建 `llm/your_provider.py`，继承 `BaseLLMClient`，**只需实现 `_send()`**：
   ```python
   from openai import OpenAI
   from .base import BaseLLMClient

   class YourProviderClient(BaseLLMClient):
       def __init__(self, api_key, model, base_url, timeout=30.0,
                    max_retries=2, **kwargs):
           super().__init__(api_key=api_key, model=model, base_url=base_url,
                            timeout=timeout, max_retries=max_retries)
           self._client = OpenAI(api_key=self.api_key, base_url=self.base_url,
                                 timeout=self.timeout, max_retries=self.max_retries,
                                 **kwargs)

       def _send(self) -> str:
           response = self._client.chat.completions.create(
               model=self.model, messages=self._messages,
           )
           return response.choices[0].message.content
   ```
2. 在 `factory.py` 的 `_PROVIDER_REGISTRY` 中注册：
   ```python
   from .your_provider import YourProviderClient
   _PROVIDER_REGISTRY["your_provider"] = YourProviderClient
   ```
3. 在 `config.toml` 中添加提供商配置：
   ```toml
   [providers.your_provider]
   model = "your-model-name"
   api_key = "sk-xxx"
   base_url = "https://your.api.com/v1"
   timeout = 30.0
   max_retries = 2
   # 以下为 openai SDK 专有字段，可选
   organization = ""
   project = ""
   ```
