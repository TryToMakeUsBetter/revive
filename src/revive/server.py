import logging
import os
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .bot import ChatBot
from .chat import WebChatClient
from .config import load_config
from .llm import DeepSeek

logging.basicConfig(
    level=os.environ.get("REVIVE_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("revive.server")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Web 对话 ----------

DEFAULT_SYSTEM_PROMPT = "你是一个友好的助手，用简短自然的口语回复。"


def _build_web_bot() -> tuple[ChatBot, WebChatClient]:
    cfg = load_config()
    log.info("chat init: deepseek_key=%s", "set" if cfg.deepseek_api_key else "missing")
    client = WebChatClient()
    bot = ChatBot(
        llm=DeepSeek(api_key=cfg.deepseek_api_key),
        client=client,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )
    client.register_handler(bot.handle)
    return bot, client


_web_bot: Optional[ChatBot] = None
_web_client: Optional[WebChatClient] = None
_web_lock = threading.Lock()


def _ensure_web_bot() -> WebChatClient:
    global _web_bot, _web_client
    with _web_lock:
        if _web_client is None:
            _web_bot, _web_client = _build_web_bot()
    return _web_client


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    replies: list[str]


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message 不能为空")
    try:
        client = _ensure_web_bot()
    except Exception as exc:
        log.exception("初始化 bot 失败")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    log.info("chat session=%s text=%r", req.session_id, req.message[:80])
    try:
        replies = client.deliver(req.session_id, "web-user", req.message)
    except Exception as exc:
        log.exception("chat handle 失败")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(replies=replies)


@app.post("/api/chat/reset")
def reset_chat(session_id: str) -> dict:
    if _web_bot is not None:
        _web_bot.histories.pop(session_id, None)
    return {"ok": True}


# ---------- 前端静态资源 ----------


def _find_frontend_dist() -> Path:
    env = os.environ.get("REVIVE_FRONTEND_DIST")
    if env:
        return Path(env).resolve()

    candidates: list[Path] = []
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for p in (start, *start.parents):
            candidates.append(p / "frontend" / "dist")
    for c in candidates:
        if c.is_dir():
            return c.resolve()
    return (Path.cwd() / "frontend" / "dist").resolve()


FRONTEND_DIST = _find_frontend_dist()
FRONTEND_URL = "http://127.0.0.1:8000"


if (FRONTEND_DIST / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )


def _serve_spa(full_path: str = "") -> Response:
    if not FRONTEND_DIST.is_dir():
        return Response(
            content=(
                f"前端产物未找到：{FRONTEND_DIST}\n"
                f"请先 `cd frontend && npm install && npm run build`，"
                f"或通过 REVIVE_FRONTEND_DIST 环境变量指定路径。"
            ),
            media_type="text/plain; charset=utf-8",
            status_code=503,
        )
    if full_path:
        candidate = (FRONTEND_DIST / full_path).resolve()
        try:
            candidate.relative_to(FRONTEND_DIST)
        except ValueError:
            return Response(status_code=404)
        if candidate.is_file():
            return FileResponse(candidate)
    return FileResponse(FRONTEND_DIST / "index.html")


@app.get("/")
def spa_root() -> Response:
    return _serve_spa()


@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> Response:
    if full_path.startswith("api/"):
        return Response(status_code=404)
    return _serve_spa(full_path)


def _open_browser_when_ready(url: str = FRONTEND_URL, delay: float = 1.0) -> None:
    import time
    import webbrowser

    time.sleep(delay)
    webbrowser.open(url)


def main() -> None:
    import uvicorn

    print(f"[revive-server] FRONTEND_DIST = {FRONTEND_DIST}")
    if not FRONTEND_DIST.is_dir():
        print(
            f"[warn] {FRONTEND_DIST} 不存在；先运行 `cd frontend && npm install && npm run build`，\n"
            f"       或者通过 REVIVE_FRONTEND_DIST 环境变量指定其他路径。"
        )
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
