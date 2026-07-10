"""应用配置：目录常量、LLM 客户端初始化、全局状态。"""

from pathlib import Path

from llm import create_client
from llm.tools import register_chart_tools

# ── 目录 ──
BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "charts_output"
CHARTS_DIR.mkdir(exist_ok=True)

PROMPTS_DIR = BASE_DIR / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)

STATIC_DIR = BASE_DIR / "frontend"
STATIC_DIR.mkdir(exist_ok=True)

# ── LLM 客户端 ──
client = create_client("deepseek")
register_chart_tools(client._tool_registry, charts_dir=str(CHARTS_DIR), charts_url="/charts")

# ── 提示词 ──
DEFAULT_SYSTEM_PROMPT = (
    "你是一个有用的 AI 助手。请用中文回答。"
    "当你看到可以量化的数据时，主动将其可视化。"
)

_active_prompt: str | None = None


def get_active_prompt() -> str | None:
    return _active_prompt


def set_active_prompt(prompt: str | None) -> None:
    global _active_prompt
    _active_prompt = prompt
