# 集成测试

对 revive 项目进行端到端验证，覆盖配置读取、工厂创建、DeepSeek API 真实调用、抽象接口约束。

## 运行测试

```bash
# 在项目根目录下执行
python -m unittest tests.test_integration -v

# 只跑某个测试类
python -m unittest tests.test_integration.TestDeepSeekIntegration -v

# 只跑某个用例
python -m unittest tests.test_integration.TestConfigModule.test_load_config_returns_dict -v
```

## 测试范围

| 测试类 | 说明 | 是否需要网络 |
|---|---|---|
| `TestConfigModule` | 配置加载、默认值、环境变量覆盖、异常路径 | 否 |
| `TestFactory` | 客户端工厂创建、提供商注册、空 key 校验 | 否 |
| `TestDeepSeekIntegration` | 单轮/多轮对话、上下文记忆、system prompt、reset 等 | **是**（真实 API） |
| `TestBaseLLMClient` | 抽象类不可实例化、接口完整性、history 隔离 | 否 |

## 前提条件

- `config.toml` 中存在有效的 DeepSeek API Key
- 网络可访问 `https://api.deepseek.com`

## 添加新测试

1. 在 `tests/test_integration.py` 中新增 `unittest.TestCase` 子类
2. 如需真实 API 调用，参考 `TestDeepSeekIntegration` 使用 `setUpClass` + `setUp`
3. 工厂相关测试参考 `TestFactory`，无需网络即可运行
