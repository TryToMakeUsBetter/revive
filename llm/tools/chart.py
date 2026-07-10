"""图表生成工具：支持饼图、直方图（柱状图）、折线图。

提供 ChartTool 类和可注册为 LLM tool 的独立函数，均基于 matplotlib 生成图表。
所有函数使用 Agg 后端，无需 GUI，适合服务端 / LLM agent 场景。

Usage:
    from llm.tools.chart import ChartTool, generate_chart

    # 作为独立工具
    path = generate_chart("pie", ["A", "B", "C"], [30, 45, 25], title="分布图")

    # 通过 ToolRegistry 注册给 LLM
    registry.register(generate_chart, description="生成饼图/柱状图/折线图")
"""

from __future__ import annotations

import os
import json
from typing import Union

# 强制使用非交互式后端，避免 GUI 依赖
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 中文字体 ──────────────────────────────────────────────────

def _find_chinese_font() -> str | None:
    """尝试查找系统中可用的中文字体。"""
    candidates = [
        "PingFang SC", "Heiti SC", "STHeiti", "Songti SC",
        "Hiragino Sans GB", "Microsoft YaHei", "SimHei",
        "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Arial Unicode MS",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def _setup_matplotlib():
    """配置 matplotlib 全局样式与中文字体。"""
    font = _find_chinese_font()
    if font:
        plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False  # 避免负号显示异常


_setup_matplotlib()

# ── 参数校验 ──────────────────────────────────────────────────

_VALID_CHART_TYPES = frozenset({"pie", "bar", "line"})

_SUPPORTED_FORMATS = frozenset({".png", ".jpg", ".jpeg", ".svg", ".pdf"})


def _ensure_output_ext(path: str) -> str:
    """确保输出路径有合法的图片扩展名，默认补 .png。"""
    _, ext = os.path.splitext(path)
    if ext.lower() not in _SUPPORTED_FORMATS:
        path += ".png"
    return path


# ── 核心绘图函数 ──────────────────────────────────────────────

class ChartTool:
    """LLM 图表工具类：封装饼图/直方图/折线图的生成逻辑。

    所有方法均返回输出文件路径。
    """

    @staticmethod
    def pie(
        labels: list[str],
        values: list[float],
        title: str = "",
        output_path: str = "pie_chart.png",
        autopct: str = "%1.1f%%",
        startangle: int = 90,
    ) -> str:
        """绘制饼图。

        Args:
            labels: 各扇区的标签列表。
            values: 各扇区的数值列表，与 labels 一一对应。
            title: 图表标题。
            output_path: 输出文件路径。
            autopct: 百分比格式字符串。
            startangle: 起始角度。

        Returns:
            保存的文件绝对路径。
        """
        output_path = _ensure_output_ext(output_path)

        fig, ax = plt.subplots(figsize=(8, 6))
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=autopct,
            startangle=startangle,
            textprops={"fontsize": 11},
        )
        # 百分比文字样式
        for at in autotexts:
            at.set_fontsize(10)
            at.set_color("white")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("equal")

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return os.path.abspath(output_path)

    @staticmethod
    def bar(
        labels: list[str],
        values: list[float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        output_path: str = "bar_chart.png",
        color: str = "#4C72B0",
    ) -> str:
        """绘制柱状图（直方图）。

        Args:
            labels: X 轴类别标签列表。
            values: Y 轴数值列表，与 labels 一一对应。
            title: 图表标题。
            xlabel: X 轴标签。
            ylabel: Y 轴标签。
            output_path: 输出文件路径。
            color: 柱体颜色。

        Returns:
            保存的文件绝对路径。
        """
        output_path = _ensure_output_ext(output_path)

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.8)

        # 在柱顶标注数值
        for bar_rect in bars:
            height = bar_rect.get_height()
            ax.text(
                bar_rect.get_x() + bar_rect.get_width() / 2,
                height,
                f"{height:.1f}" if height % 1 else f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return os.path.abspath(output_path)

    @staticmethod
    def line(
        labels: list[str],
        values: list[float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        output_path: str = "line_chart.png",
        color: str = "#C44E52",
        marker: str = "o",
    ) -> str:
        """绘制折线图。

        Args:
            labels: X 轴数据点标签列表。
            values: Y 轴数值列表，与 labels 一一对应。
            title: 图表标题。
            xlabel: X 轴标签。
            ylabel: Y 轴标签。
            output_path: 输出文件路径。
            color: 折线颜色。
            marker: 数据点标记样式。

        Returns:
            保存的文件绝对路径。
        """
        output_path = _ensure_output_ext(output_path)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(
            labels, values,
            color=color, marker=marker, linewidth=2,
            markersize=8, markerfacecolor="white",
            markeredgewidth=2, markeredgecolor=color,
        )

        # 在数据点旁标注数值
        for i, (x, y) in enumerate(zip(labels, values)):
            ax.annotate(
                f"{y:.1f}" if y % 1 else f"{int(y)}",
                (x, y),
                textcoords="offset points",
                xytext=(0, 12),
                ha="center",
                fontsize=9,
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return os.path.abspath(output_path)


# ── 统一入口（供 LLM tool 注册）──────────────────────────────

def _normalize_list(data, item_type: type) -> list:
    """将 LLM 可能传入的逗号分隔字符串归一化为列表。

    LLM 在 function calling 中偶尔会将列表参数序列化为 "a, b, c" 字符串，
    而不是正确的 JSON 数组 ["a", "b", "c"]。此函数做兼容处理。
    """
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        parts = [p.strip() for p in data.split(",") if p.strip()]
        if item_type is float:
            return [float(p) for p in parts]
        return parts
    return list(data)


def generate_chart(
    chart_type: str,
    labels: list[str],
    values: list[float],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: str = "chart.png",
    color: str = "",
    autopct: str = "%1.1f%%",
    startangle: int = 90,
    marker: str = "o",
) -> str:
    """生成饼图、柱状图或折线图并保存为图片文件。"""
    if chart_type not in _VALID_CHART_TYPES:
        return json.dumps({
            "success": False,
            "error": f"不支持的图表类型: {chart_type}，可选: {', '.join(sorted(_VALID_CHART_TYPES))}",
        }, ensure_ascii=False)

    labels = _normalize_list(labels, str)
    values = _normalize_list(values, float)

    if len(labels) != len(values):
        return json.dumps({
            "success": False,
            "error": f"labels 长度({len(labels)})与 values 长度({len(values)})不一致",
        }, ensure_ascii=False)

    if not labels:
        return json.dumps({
            "success": False,
            "error": "labels 和 values 不能为空",
        }, ensure_ascii=False)

    try:
        if chart_type == "pie":
            kwargs = {"title": title, "output_path": output_path, "autopct": autopct, "startangle": startangle}
            path = ChartTool.pie(labels, values, **kwargs)
        elif chart_type == "bar":
            kwargs = {"title": title, "xlabel": xlabel, "ylabel": ylabel, "output_path": output_path}
            if color:
                kwargs["color"] = color
            path = ChartTool.bar(labels, values, **kwargs)
        elif chart_type == "line":
            kwargs = {"title": title, "xlabel": xlabel, "ylabel": ylabel, "output_path": output_path, "marker": marker}
            if color:
                kwargs["color"] = color
            path = ChartTool.line(labels, values, **kwargs)
        else:
            raise ValueError(f"未知图表类型: {chart_type}")

        # 计算相对路径和 URL（如果 output_path 在 charts_dir 下）
        base_dir = os.environ.get("REVIVE_CHARTS_DIR", "")
        base_url = os.environ.get("REVIVE_CHARTS_URL", "")
        result: dict = {"success": True, "path": path, "chart_type": chart_type}
        if base_dir and base_url:
            try:
                rel = os.path.relpath(path, base_dir)
                if not rel.startswith(".."):
                    result["url"] = f"{base_url.rstrip('/')}/{rel}"
            except ValueError:
                pass

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"图表生成失败: {e}",
        }, ensure_ascii=False)


# ── 工厂函数：批量注册 ───────────────────────────────────────

def register_chart_tools(registry: object, charts_dir: str | None = None,
                       charts_url: str = "/charts") -> None:
    """将图表相关工具批量注册到 ToolRegistry 中。

    Args:
        registry: ToolRegistry 实例。
        charts_dir: 图表输出目录的绝对路径。设置环境变量 REVIVE_CHARTS_DIR。
        charts_url: 图表访问的基础 URL。设置环境变量 REVIVE_CHARTS_URL。
    """
    if charts_dir:
        os.environ["REVIVE_CHARTS_DIR"] = charts_dir
    if charts_url:
        os.environ["REVIVE_CHARTS_URL"] = charts_url

    desc = (
        "生成数据可视化图表。支持 pie（饼图）、bar（柱状图）、line（折线图）。"
    )
    if charts_dir:
        desc += (
            f" output_path 使用 {charts_dir}/chart_<描述>.png 格式。"
            f" 生成成功后，工具返回的 url 字段即图片可访问地址，请用此 url 在回复中展示图片。"
        )

    registry.register(generate_chart, description=desc)
