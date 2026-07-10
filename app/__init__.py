"""FastAPI 应用工厂：创建 app、注册路由和中间件。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import CHARTS_DIR, STATIC_DIR
from .routes.chat import router as chat_router
from .routes.prompts import router as prompts_router
from .routes.tools import router as tools_router


def create_app() -> FastAPI:
    app = FastAPI(title="revive Chat API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 静态文件
    app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

    # API 路由
    app.include_router(chat_router, prefix="/api")
    app.include_router(prompts_router, prefix="/api")
    app.include_router(tools_router, prefix="/api")

    # 前端入口
    @app.get("/")
    def serve_frontend():
        return FileResponse(str(STATIC_DIR / "index.html"))

    return app


app = create_app()
