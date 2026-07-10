"""tools 子包：LLM 工具调用（function calling / tool_use）。

提供 ToolRegistry 以及一系列开箱即用的 LLM 工具：
- chart: 饼图 / 直方图 / 折线图生成
"""

from .registry import ToolRegistry
from .chart import ChartTool, generate_chart, register_chart_tools

__all__ = [
    "ToolRegistry",
    "ChartTool",
    "generate_chart",
    "register_chart_tools",
]
