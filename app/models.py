"""请求/响应数据模型。"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    use_tools: bool = True
    system_prompt: str | None = None


class ToolTrace(BaseModel):
    tool_name: str
    arguments: dict
    result: str


class ChatResponse(BaseModel):
    reply: str
    tool_traces: list[ToolTrace] = []
    charts: list[str] = []


class SavePromptRequest(BaseModel):
    name: str
    content: str


class PromptItem(BaseModel):
    id: str
    name: str
    content: str
    custom: bool = False


class PromptsResponse(BaseModel):
    prompts: list[PromptItem]
    active: str | None = None
