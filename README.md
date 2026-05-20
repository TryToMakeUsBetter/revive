# Revive

一个轻量级对话助手 —— FastAPI + Vue + DeepSeek。

## 项目结构

```
revive/
├── src/revive/         # 后端包（pip install -e . 后可作为 revive 导入）
│   ├── bot.py          # 消息编排（ChatBot）
│   ├── server.py       # FastAPI + 前端静态托管 + /api/chat
│   ├── config.py       # config.toml 加载
│   ├── chat/           # 聊天客户端抽象 + Web 实现
│   └── llm/            # LLM 抽象与 DeepSeek 实现
├── frontend/           # Vue 前端
├── tests/              # 单元测试 + 集成测试
├── pyproject.toml
└── config.toml.example
```

## 快速开始

```bash
# 1. 装后端（editable 安装，改代码即生效）
pip install -e .

# 2. 复制配置模板并填 DeepSeek key
cp config.toml.example config.toml

# 3. build 前端
cd frontend && npm install && npm run build && cd ..

# 4. 启动服务
revive-server
# 等价于： python -m revive.server
```

启动后浏览器自动打开 http://127.0.0.1:8000，点首页"开始对话"即可。

环境变量：
- `REVIVE_CONFIG`：config.toml 路径
- `REVIVE_FRONTEND_DIST`：前端产物目录
- `REVIVE_LOG_LEVEL`：日志级别（默认 INFO）

## 测试

```bash
python -m unittest discover tests
```
