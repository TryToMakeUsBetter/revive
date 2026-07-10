"""聊天相关路由：发送消息、重置对话。"""

from fastapi import APIRouter

from ..config import client, DEFAULT_SYSTEM_PROMPT, get_active_prompt, set_active_prompt
from ..models import ChatRequest, ChatResponse
from ..services import extract_tool_traces, extract_chart_urls, sanitize_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """发送消息并获取 LLM 回复（含 tool_use）。"""
    if not client.history:
        prompt = req.system_prompt or get_active_prompt() or DEFAULT_SYSTEM_PROMPT
        set_active_prompt(prompt)
        client.add_message("system", prompt)

    reply = client.chat(req.message, use_tools=req.use_tools)

    traces = extract_tool_traces(client.history)
    chart_urls = extract_chart_urls(traces)
    reply = sanitize_reply(reply)

    return ChatResponse(
        reply=reply,
        tool_traces=[
            {"tool_name": t.tool_name, "arguments": t.arguments, "result": t.result}
            for t in traces
        ],
        charts=chart_urls,
    )


@router.post("/reset")
def reset():
    """重置对话历史。"""
    set_active_prompt(None)
    client.reset()
    return {"status": "ok"}
