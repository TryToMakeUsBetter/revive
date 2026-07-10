"""工具相关路由。"""

from fastapi import APIRouter

from ..config import client

router = APIRouter()


@router.get("/tools")
def list_tools():
    """返回已注册的工具列表。"""
    return {"tools": client.tools, "model": client.model}
