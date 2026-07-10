"""业务逻辑：工具追踪提取、URL 转换、提示词加载。"""

import json
import os
import re

from .config import CHARTS_DIR, PROMPTS_DIR
from .models import ToolTrace


def load_prompts() -> list[dict]:
    """从 prompts/ 目录加载所有 .md 提示词文件。"""
    prompts: list[dict] = []
    if not PROMPTS_DIR.is_dir():
        return prompts

    for fpath in sorted(PROMPTS_DIR.glob("*.md")):
        text = fpath.read_text(encoding="utf-8").strip()
        if not text:
            continue
        lines = text.split("\n")
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


def extract_tool_traces(history: list[dict]) -> list[ToolTrace]:
    """从对话历史中提取本轮工具调用信息。"""
    traces: list[ToolTrace] = []
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


def extract_chart_urls(traces: list[ToolTrace]) -> list[str]:
    """从工具调用追踪中提取成功的图表 URL。优先使用工具返回的 url 字段。"""
    urls: list[str] = []
    for trace in traces:
        if trace.tool_name != "generate_chart":
            continue
        try:
            r = json.loads(trace.result)
            if r.get("success"):
                url = r.get("url")
                if url:
                    urls.append(url)
                    continue
                if r.get("path"):
                    try:
                        rel = os.path.relpath(r["path"], str(CHARTS_DIR))
                        if not rel.startswith(".."):
                            urls.append(f"/charts/{rel}")
                    except ValueError:
                        pass
        except (json.JSONDecodeError, KeyError):
            pass
    return urls


def sanitize_reply(text: str) -> str:
    """将 LLM 回复中的本地文件路径替换为可访问的 /charts/ URL。"""
    charts_dir = str(CHARTS_DIR)
    text = re.sub(
        r'file://+?' + re.escape(charts_dir) + r'/([^\s)\]]+)',
        r'/charts/\1', text,
    )
    text = re.sub(
        re.escape(charts_dir) + r'/([^\s)\]]+)',
        r'/charts/\1', text,
    )
    text = re.sub(
        r'(?<![./\w])charts_output/([^\s)\]]+)',
        r'/charts/\1', text,
    )
    return text
