# 集成测试

对 revive 项目进行端到端验证，覆盖配置读取、工厂创建、DeepSeek API 真实调用、抽象接口约束。

## 运行测试

```bash
# 在项目根目录下执行（需要 revive conda 环境）
conda run -n revive python -m unittest tests.test_integration -v

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
| `TestToolUse` | 工具注册、天气查询、数学计算、tool_use 循环、历史记录 | **是**（真实 API） |
| `TestBaseLLMClient` | 抽象类不可实例化、接口完整性、history 隔离、add_message 全 role 支持、预置对话注入 | 否 |

### 图表工具测试 (`test_chart_tool.py`)

```bash
# 仅单元测试（不调 API）
python -m pytest tests/test_chart_tool.py -v -k "not Conversation"

# 含端到端测试（需 API key）
python -m pytest tests/test_chart_tool.py -v
```

| 测试类 | 说明 | 是否需要网络 |
|---|---|---|
| `TestUtilityFunctions` | 扩展名处理、`_normalize_list` 字符串→列表归一化、合法类型校验 | 否 |
| `TestChartTool` | 饼图/柱状图/折线图静态方法、单数据点、负值、颜色/标记自定义、压力测试 | 否 |
| `TestGenerateChart` | `generate_chart()` 统一入口、正常/异常路径、扩展参数 | 否 |
| `TestChartToolRegistry` | ToolRegistry 注册、执行、OpenAI schema 生成、缺参报错 | 否 |
| `TestChartToolInConversation` | 端到端：5 种方式验证 LLM 对话中 tool 是否被调用 | **是**（真实 API） |

## 前提条件

- `config.toml` 中存在有效的 DeepSeek API Key
- 网络可访问 `https://api.deepseek.com`

## 文件结构

```
tests/
├── __init__.py
├── README.md
├── test_integration.py   # 配置/工厂/客户端/工具调用集成测试
└── test_chart_tool.py    # 图表工具单元测试 + 端到端测试
```

## 添加新测试

1. 在 `tests/` 下新建 `test_xxx.py` 或在已有文件中新增 `unittest.TestCase` 子类
2. 如需真实 API 调用，参考 `TestDeepSeekIntegration` 使用 `setUpClass` + `setUp`
3. 工具类单元测试参考 `test_chart_tool.py`，无需网络即可运行
