# 目的

本项目想要实现一个根据对话内容模拟对方语气和内容的agent
希望通过此项目使自己熟悉记忆系统、agent开发和prompt相关的内容

## 项目结构

```
revive/
├── src/revive/         # 后端包（pip install -e . 后可作为 revive 导入）
│   ├── bot.py          # 消息编排
│   ├── cli.py          # 命令行入口（itchat 模式）
│   ├── server.py       # FastAPI + 前端静态托管
│   ├── config.py       # config.toml / whitelist.txt 加载
│   ├── llm/            # LLM 抽象与 DeepSeek 实现
│   └── wechat/         # WeChat 抽象与 itchat 实现
├── frontend/           # Vue 前端
├── tests/              # 单元测试 + 集成测试
├── pyproject.toml
├── config.toml.example
└── whitelist.txt.example
```

## 快速开始

```bash
# 1. 装依赖（editable 安装，保留改代码即生效的体验）
pip install -e .

# 2. 复制配置模板并填好 DeepSeek key / 白名单
cp config.toml.example config.toml
cp whitelist.txt.example whitelist.txt   # 仅在启用白名单时需要

# 3. 跑命令行版（终端扫码）
revive
# 等价于： python -m revive

# 4. 跑带前端的服务（先 build 前端，再启 server）
cd frontend && npm install && npm run build && cd ..
revive-server
# 等价于： python -m revive.server
```

环境变量覆盖：`REVIVE_CONFIG`（指定 config.toml 路径）、`REVIVE_WHITELIST`、`REVIVE_FRONTEND_DIST`。

## 测试

```bash
python -m unittest discover tests
```