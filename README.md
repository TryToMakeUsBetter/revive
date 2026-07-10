# revive Chat — LLM 对话 + 可视化工具

基于 FastAPI + React 的 LLM 对话应用，支持 Function Calling 工具调用（图表生成）。

## 项目结构

```
revive/
├── start.sh              # 一键启动脚本
├── server.py             # FastAPI 后端 (Python, :8080)
├── config.toml           # API Key 配置
├── llm/                  # LLM 客户端库
│   ├── base.py           #   抽象基类
│   ├── deepseek.py       #   DeepSeek 实现
│   ├── openai.py         #   OpenAI 实现
│   ├── factory.py        #   工厂模式
│   └── tools/            #   工具集
│       ├── registry.py   #     工具注册表
│       └── chart.py      #     图表生成 (饼/柱/折线图)
├── prompts/              # 系统提示词预设（可自定义）
│   ├── default.md
│   ├── data-analyst.md
│   ├── code-reviewer.md
│   ├── translator.md
│   └── creative-writer.md
├── frontend/             # React + Vite + TypeScript (:5173)
│   └── src/
│       ├── App.tsx       #   主组件
│       ├── components/   #   UI 组件
│       └── api.ts        #   API 客户端
├── tests/
│   ├── test_integration.py
│   └── test_chart_tool.py
└── charts_output/        # 生成的图表（自动创建）
```

## 快速启动

```bash
# 方式1：一键启动
./start.sh

# 方式2：分别启动
# 终端1 — 后端
python server.py                          # → http://localhost:8080

# 终端2 — 前端
cd frontend && npm install && npm run dev # → http://localhost:5173
```

打开浏览器访问 **http://localhost:5173**。

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/chat` | 发送消息（含 `system_prompt` + `use_tools`） |
| `POST` | `/api/reset` | 重置对话 |
| `GET` | `/api/tools` | 已注册工具列表 |
| `GET` | `/api/prompts` | 提示词列表 |
| `POST` | `/api/prompts` | 保存自定义提示词 |
| `DELETE` | `/api/prompts/{id}` | 删除自定义提示词 |
| `GET` | `/charts/{file}` | 图表静态文件 |

## 测试

```bash
# 单元测试（无需网络）
python -m pytest tests/ -v -k "not Conversation and not Integration and not ToolUse"

# 端到端测试（需 API Key）
python -m pytest tests/test_chart_tool.py -v
```
