"""revive Chat — FastAPI 后端服务。

提供 REST API 供前端调用 LLM 对话 + Tool Use。
启动方式：
    python server.py
    uvicorn server:app --reload --port 8080
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm import create_client
from llm.tools import register_chart_tools

# ── 目录 ──────────────────────────────────────────────────────

CHARTS_DIR = Path(__file__).parent / "charts_output"
CHARTS_DIR.mkdir(exist_ok=True)

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path(__file__).parent / "frontend"
STATIC_DIR.mkdir(exist_ok=True)

# ── LLM 客户端 ────────────────────────────────────────────────

client = create_client("deepseek")
register_chart_tools(client._tool_registry, charts_dir=str(CHARTS_DIR))

# 默认系统提示词（不提及具体工具名——LLM 通过 function calling API 自行发现）
_DEFAULT_SYSTEM_PROMPT = (
    "你是一个有用的 AI 助手。请用中文回答。"
    "当你看到可以量化的数据时，主动将其可视化。"
)

# 当前激活的提示词（可在对话开始时通过 API 切换）
_active_prompt: str | None = None


# ── 提示词加载 ────────────────────────────────────────────────

def _load_prompts() -> list[dict]:
    """从 prompts/ 目录加载所有 .md 提示词文件。

    文件格式：
        # 显示名称
        提示词正文...

    Returns:
        [{"id": "default", "name": "通用助手", "content": "..."}, ...]
    """
    prompts: list[dict] = []
    if not PROMPTS_DIR.is_dir():
        return prompts

    for fpath in sorted(PROMPTS_DIR.glob("*.md")):
        text = fpath.read_text(encoding="utf-8").strip()
        if not text:
            continue

        lines = text.split("\n")
        # 第一行以 # 开头的是名称，其余为正文
        if lines[0].startswith("# "):
            name = lines[0][2:].strip()
            content = "\n".join(lines[1:]).strip()
        else:
            name = fpath.stem
            content = text

        prompts.append({
            "id": fpath.stem,
            "name": name,
            "content": content,
            "custom": fpath.stem.startswith("custom_"),
        })

    return prompts

# ── FastAPI 应用 ──────────────────────────────────────────────

app = FastAPI(title="revive Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：图表输出
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# ── 模型 ──────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    use_tools: bool = True
    system_prompt: str | None = None  # 可选：覆盖默认系统提示词


class ToolTrace(BaseModel):
    tool_name: str
    arguments: dict
    result: str


class ChatResponse(BaseModel):
    reply: str
    tool_traces: list[ToolTrace] = []
    charts: list[str] = []  # 图表 URL 路径，如 /charts/chart_xxx.png


class SavePromptRequest(BaseModel):
    name: str
    content: str


# ── 辅助函数 ──────────────────────────────────────────────────


def _extract_tool_traces(history: list[dict]) -> list[ToolTrace]:
    """从对话历史中提取本轮工具调用信息。"""
    traces: list[ToolTrace] = []

    # 找到最后一个 user 消息的索引
    last_user_idx = max(
        (j for j, m in enumerate(history) if m["role"] == "user"),
        default=-1,
    )

    for j in range(last_user_idx + 1, len(history)):
        m = history[j]
        if m["role"] != "assistant" or not m.get("tool_calls"):
            continue

        for tc in m["tool_calls"]:
            fn = tc["function"]
            # 查找对应的 tool 结果
            tool_result = ""
            for k in range(j + 1, len(history)):
                if (history[k]["role"] == "tool"
                        and history[k].get("tool_call_id") == tc["id"]):
                    tool_result = history[k]["content"]
                    break

            args = {}
            try:
                args = json.loads(fn["arguments"])
            except json.JSONDecodeError:
                args = {"raw": fn["arguments"]}

            traces.append(ToolTrace(
                tool_name=fn["name"],
                arguments=args,
                result=tool_result,
            ))

    return traces


def _extract_chart_urls(traces: list[ToolTrace]) -> list[str]:
    """从工具调用追踪中提取成功的图表 URL。"""
    urls: list[str] = []
    for trace in traces:
        if trace.tool_name != "generate_chart":
            continue
        try:
            r = json.loads(trace.result)
            if r.get("success") and r.get("path"):
                abs_path = r["path"]
                try:
                    rel = os.path.relpath(abs_path, str(CHARTS_DIR))
                    if not rel.startswith(".."):
                        urls.append(f"/charts/{rel}")
                except ValueError:
                    pass
        except (json.JSONDecodeError, KeyError):
            pass
    return urls


def _sanitize_reply(text: str) -> str:
    """将 LLM 回复中的本地文件路径替换为可访问的 /charts/ URL。"""
    import re

    charts_dir = str(CHARTS_DIR)
    # 模式1: file:// 协议
    text = re.sub(
        r'file://+?' + re.escape(charts_dir) + r'/([^\s)\]]+)',
        r'/charts/\1',
        text,
    )
    # 模式2: 裸绝对路径
    text = re.sub(
        re.escape(charts_dir) + r'/([^\s)\]]+)',
        r'/charts/\1',
        text,
    )
    # 模式3: 相对路径 charts_output/xxx.png → /charts/xxx.png
    text = re.sub(
        r'(?<![./\w])charts_output/([^\s)\]]+)',
        r'/charts/\1',
        text,
    )
    return text


# ── API 路由 ──────────────────────────────────────────────────


@app.get("/api/tools")
def list_tools():
    """返回已注册的工具列表。"""
    return {"tools": client.tools, "model": client.model}


@app.get("/api/prompts")
def list_prompts():
    """返回所有可用的提示词列表。"""
    prompts = _load_prompts()
    return {
        "prompts": prompts,
        "active": _active_prompt,
    }


@app.post("/api/prompts")
def save_prompt(req: SavePromptRequest):
    """保存自定义提示词为 .md 文件。

    文件名自动使用 custom_<sanitized_name>.md 格式。
    """
    import re
    safe_name = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fff-]", "_", req.name.strip())
    if not safe_name:
        safe_name = "custom_prompt"

    filename = f"custom_{safe_name}.md"
    filepath = PROMPTS_DIR / filename

    # 避免覆盖已有文件：加数字后缀
    counter = 1
    while filepath.exists():
        filename = f"custom_{safe_name}_{counter}.md"
        filepath = PROMPTS_DIR / filename
        counter += 1

    content = f"# {req.name.strip()}\n{req.content.strip()}"
    filepath.write_text(content, encoding="utf-8")

    prompts = _load_prompts()
    return {"status": "ok", "prompts": prompts}


@app.delete("/api/prompts/{prompt_id}")
def delete_prompt(prompt_id: str):
    """删除自定义提示词（仅允许删除 custom_ 开头的）。"""
    if not prompt_id.startswith("custom_"):
        return {"status": "error", "message": "不允许删除内置提示词"}

    filepath = PROMPTS_DIR / f"{prompt_id}.md"
    if filepath.exists():
        filepath.unlink()

    prompts = _load_prompts()
    return {"status": "ok", "prompts": prompts}


@app.post("/api/reset")
def reset():
    """重置对话历史。"""
    global _active_prompt
    _active_prompt = None
    client.reset()
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """发送消息并获取 LLM 回复（含 tool_use）。

    首次对话时注入系统提示词：
    1. 如果 req.system_prompt 有值，使用它
    2. 否则使用 _active_prompt
    3. 都没有则使用 _DEFAULT_SYSTEM_PROMPT
    """
    global _active_prompt

    if not client.history:
        prompt = req.system_prompt or _active_prompt or _DEFAULT_SYSTEM_PROMPT
        _active_prompt = prompt
        client.add_message("system", prompt)

    reply = client.chat(req.message, use_tools=req.use_tools)

    traces = _extract_tool_traces(client.history)
    chart_urls = _extract_chart_urls(traces)

    # 将回复中的本地路径替换为可访问的 /charts/ URL
    reply = _sanitize_reply(reply)

    # 将 ToolTrace 转为可序列化的 dict
    trace_dicts = [
        {
            "tool_name": t.tool_name,
            "arguments": t.arguments,
            "result": t.result,
        }
        for t in traces
    ]

    return ChatResponse(
        reply=reply,
        tool_traces=trace_dicts,
        charts=chart_urls,
    )


# ── 前端静态文件（放在最后，避免覆盖 API 路由）────────────────

@app.get("/")
def serve_frontend():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ── 启动入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
