"""提示词管理路由：列表、保存、删除。"""

import re

from fastapi import APIRouter

from ..config import PROMPTS_DIR, get_active_prompt
from ..models import SavePromptRequest
from ..services import load_prompts

router = APIRouter()


@router.get("/prompts")
def list_prompts():
    """返回所有可用的提示词列表。"""
    return {
        "prompts": load_prompts(),
        "active": get_active_prompt(),
    }


@router.post("/prompts")
def save_prompt(req: SavePromptRequest):
    """保存自定义提示词为 .md 文件。"""
    safe_name = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fff-]", "_", req.name.strip())
    if not safe_name:
        safe_name = "custom_prompt"

    filename = f"custom_{safe_name}.md"
    filepath = PROMPTS_DIR / filename
    counter = 1
    while filepath.exists():
        filename = f"custom_{safe_name}_{counter}.md"
        filepath = PROMPTS_DIR / filename
        counter += 1

    content = f"# {req.name.strip()}\n{req.content.strip()}"
    filepath.write_text(content, encoding="utf-8")
    return {"status": "ok", "prompts": load_prompts()}


@router.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: str):
    """删除自定义提示词（仅允许删除 custom_ 开头的）。"""
    if not prompt_id.startswith("custom_"):
        return {"status": "error", "message": "不允许删除内置提示词"}
    filepath = PROMPTS_DIR / f"{prompt_id}.md"
    if filepath.exists():
        filepath.unlink()
    return {"status": "ok", "prompts": load_prompts()}
