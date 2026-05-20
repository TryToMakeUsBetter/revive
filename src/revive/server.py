import logging
import os
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=os.environ.get("REVIVE_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("itchat").setLevel(logging.INFO)
log = logging.getLogger("revive.server")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginState:
    IDLE = "idle"
    WAITING_QR = "waiting_qr"
    WAITING_SCAN = "waiting_scan"
    SCANNED = "scanned"
    LOGGED_IN = "logged_in"
    FAILED = "failed"

    def __init__(self) -> None:
        self.qr_png: Optional[bytes] = None
        self.qr_version: int = 0
        self.status: str = self.IDLE
        self.uuid: Optional[str] = None
        self.error: Optional[str] = None
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.generation: int = 0

    def begin(self) -> int:
        """开启新一轮登录，返回本轮 generation。旧轮的回调凭 generation 自动失效。"""
        with self.lock:
            self.qr_png = None
            self.qr_version = 0
            self.status = self.WAITING_QR
            self.uuid = None
            self.error = None
            self.generation += 1
            return self.generation

    def on_qr(self, generation: int, uuid: str, status: str, qrcode: bytes) -> None:
        with self.lock:
            if generation != self.generation:
                return
            new_qr = uuid != self.uuid
            self.uuid = uuid
            if qrcode:
                if qrcode != self.qr_png:
                    self.qr_png = qrcode
                    self.qr_version += 1

            if new_qr:
                self.status = self.WAITING_SCAN
            elif status == "201":
                self.status = self.SCANNED
            # status "200" 留给 loginCallback 设 LOGGED_IN
            # status "408"（轮询/超时）保持当前状态

    def on_logged_in(self, generation: int) -> None:
        with self.lock:
            if generation != self.generation:
                return
            self.status = self.LOGGED_IN

    def on_failed(self, generation: int, err: str) -> None:
        with self.lock:
            if generation != self.generation:
                return
            self.status = self.FAILED
            self.error = err

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "status": self.status,
                "has_qr": self.qr_png is not None,
                "qr_version": self.qr_version,
                "uuid": self.uuid,
                "error": self.error,
            }


state = LoginState()


def _run_itchat_login(generation: int) -> None:
    try:
        import itchat
        from itchat.components import login as itchat_login

        core = itchat.Core()
        log.info("[gen=%d] itchat.auto_login starting", generation)

        original_check_login = itchat_login.check_login
        check_count = {"n": 0}

        def _check_login_with_log(self, uuid=None):
            check_count["n"] += 1
            n = check_count["n"]
            import time as _t
            t0 = _t.monotonic()
            log.info("[gen=%d] check_login #%d → calling weixin.qq.com (long-poll)…", generation, n)
            try:
                # 给微信的长轮询一个硬上限，否则 requests 会无限 hang
                self.s.request = _wrap_request_with_timeout(self.s.request, 30)
                result = original_check_login(self, uuid=uuid)
                log.info("[gen=%d] check_login #%d → returned %r in %.1fs",
                         generation, n, result, _t.monotonic() - t0)
                return result
            except Exception as e:
                log.warning("[gen=%d] check_login #%d → raised %s after %.1fs",
                            generation, n, e.__class__.__name__, _t.monotonic() - t0)
                raise

        itchat_login.check_login = _check_login_with_log
        # 同名属性也挂到 core 上，因为 load_login 已经把方法绑给实例了
        core.check_login = _check_login_with_log.__get__(core, type(core))

        def _qr_cb(uuid, status, qrcode):
            log.info("[gen=%d] qrCallback uuid=%s status=%s qr_bytes=%d",
                     generation, uuid, status, len(qrcode) if qrcode else 0)
            state.on_qr(generation, uuid, status, qrcode)

        def _login_cb():
            log.info("[gen=%d] loginCallback fired (login successful)", generation)
            state.on_logged_in(generation)

        core.auto_login(
            hotReload=False,
            enableCmdQR=False,
            qrCallback=_qr_cb,
            loginCallback=_login_cb,
        )
        log.info("[gen=%d] itchat.auto_login returned", generation)
    except Exception as exc:
        log.exception("[gen=%d] itchat.auto_login crashed", generation)
        state.on_failed(generation, str(exc))


def _wrap_request_with_timeout(orig_request, default_timeout: float):
    def wrapped(method, url, **kwargs):
        kwargs.setdefault("timeout", default_timeout)
        return orig_request(method, url, **kwargs)
    return wrapped


@app.post("/api/wechat/login/start")
def start_login() -> dict:
    gen = state.begin()
    t = threading.Thread(target=_run_itchat_login, args=(gen,), daemon=True)
    state.thread = t
    t.start()
    return state.snapshot()


@app.get("/api/wechat/status")
def get_status() -> dict:
    return state.snapshot()


@app.get("/api/wechat/qr")
def get_qr() -> Response:
    with state.lock:
        png = state.qr_png
    if not png:
        return Response(status_code=404)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


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
