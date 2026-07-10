"""图表工具单元测试：覆盖 ChartTool 和 generate_chart 的所有功能。

运行方式：
    python -m pytest tests/test_chart_tool.py -v
    python -m unittest tests.test_chart_tool -v
"""

import json
import os
import tempfile
import unittest

from llm.tools.chart import (
    ChartTool,
    generate_chart,
    register_chart_tools,
    _VALID_CHART_TYPES,
    _ensure_output_ext,
    _normalize_list,
)
from llm.tools import ToolRegistry


# ── 辅助函数与基础工具测试 ────────────────────────────────────

class TestUtilityFunctions(unittest.TestCase):
    """测试 chart 模块中的辅助函数。"""

    def test_valid_chart_types(self):
        """验证合法的图表类型。"""
        self.assertIn("pie", _VALID_CHART_TYPES)
        self.assertIn("bar", _VALID_CHART_TYPES)
        self.assertIn("line", _VALID_CHART_TYPES)
        self.assertEqual(len(_VALID_CHART_TYPES), 3)

    def test_ensure_output_ext_adds_png(self):
        """无扩展名时自动补 .png。"""
        self.assertEqual(_ensure_output_ext("chart"), "chart.png")

    def test_ensure_output_ext_preserves_png(self):
        """已有 .png 不变。"""
        self.assertEqual(_ensure_output_ext("chart.png"), "chart.png")

    def test_ensure_output_ext_preserves_svg(self):
        """已有 .svg 不变。"""
        self.assertEqual(_ensure_output_ext("chart.svg"), "chart.svg")

    def test_ensure_output_ext_preserves_jpg(self):
        """已有 .jpg 不变。"""
        self.assertEqual(_ensure_output_ext("chart.jpg"), "chart.jpg")

    def test_ensure_output_ext_unknown_adds_png(self):
        """未知扩展名补 .png。"""
        self.assertEqual(_ensure_output_ext("chart.xyz"), "chart.xyz.png")

    def test_normalize_list_already_list(self):
        """已经是 list 则原样返回。"""
        self.assertEqual(_normalize_list(["a", "b"], str), ["a", "b"])

    def test_normalize_list_comma_string_to_str_list(self):
        """逗号分隔字符串 → 字符串列表。"""
        self.assertEqual(_normalize_list("a, b, c", str), ["a", "b", "c"])

    def test_normalize_list_comma_string_to_float_list(self):
        """逗号分隔字符串 → 浮点数列表。"""
        self.assertEqual(_normalize_list("10, 20, 30", float), [10.0, 20.0, 30.0])

    def test_normalize_list_single_item_string(self):
        """单元素逗号分隔字符串。"""
        self.assertEqual(_normalize_list("only", str), ["only"])

    def test_normalize_list_empty_string(self):
        """空字符串返回空列表。"""
        self.assertEqual(_normalize_list("", str), [])


# ── ChartTool 静态方法测试 ────────────────────────────────────

class TestChartTool(unittest.TestCase):
    """测试 ChartTool 的饼图、柱状图、折线图生成。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _tmp_path(self, name: str) -> str:
        return os.path.join(self.tmpdir, name)

    # ── 饼图 ──────────────────────────────────────────────

    def test_pie_creates_file(self):
        path = ChartTool.pie(
            ["A", "B", "C"],
            [30, 45, 25],
            title="Test Pie",
            output_path=self._tmp_path("pie.png"),
        )
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_pie_default_output_path(self):
        """不指定 output_path 时使用默认值。"""
        path = ChartTool.pie(["X", "Y"], [50, 50])
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)
        os.remove(path)  # 清理

    def test_pie_returns_absolute_path(self):
        path = ChartTool.pie(["A"], [100], output_path=self._tmp_path("pie_abs.png"))
        self.assertTrue(os.path.isabs(path))

    def test_pie_single_slice(self):
        """单个扇区也能正常生成。"""
        path = ChartTool.pie(["Only"], [100], output_path=self._tmp_path("pie_one.png"))
        self.assertTrue(os.path.isfile(path))

    def test_pie_many_slices(self):
        """大量扇区（压力测试）。"""
        labels = [f"Item{i}" for i in range(20)]
        values = [i + 1 for i in range(20)]
        path = ChartTool.pie(labels, values, output_path=self._tmp_path("pie_many.png"))
        self.assertTrue(os.path.isfile(path))

    # ── 柱状图 ────────────────────────────────────────────

    def test_bar_creates_file(self):
        path = ChartTool.bar(
            ["Q1", "Q2", "Q3", "Q4"],
            [120, 200, 150, 280],
            title="季度销售额",
            xlabel="季度",
            ylabel="销售额(万元)",
            output_path=self._tmp_path("bar.png"),
        )
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_bar_default_output_path(self):
        path = ChartTool.bar(["A", "B"], [10, 20])
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)
        os.remove(path)

    def test_bar_single_bar(self):
        """单柱也能正常生成。"""
        path = ChartTool.bar(["A"], [42], output_path=self._tmp_path("bar_one.png"))
        self.assertTrue(os.path.isfile(path))

    def test_bar_with_color(self):
        path = ChartTool.bar(
            ["A", "B"], [10, 20],
            color="#FF6B6B",
            output_path=self._tmp_path("bar_color.png"),
        )
        self.assertTrue(os.path.isfile(path))

    def test_bar_negative_values(self):
        """柱状图支持负值。"""
        path = ChartTool.bar(
            ["Jan", "Feb"], [10, -5],
            output_path=self._tmp_path("bar_neg.png"),
        )
        self.assertTrue(os.path.isfile(path))

    # ── 折线图 ────────────────────────────────────────────

    def test_line_creates_file(self):
        path = ChartTool.line(
            ["1月", "2月", "3月", "4月"],
            [100, 150, 130, 180],
            title="月度趋势",
            xlabel="月份",
            ylabel="数值",
            output_path=self._tmp_path("line.png"),
        )
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_line_default_output_path(self):
        path = ChartTool.line(["A", "B", "C"], [1, 3, 2])
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 0)
        os.remove(path)

    def test_line_with_custom_marker_and_color(self):
        path = ChartTool.line(
            ["1", "2", "3"], [5, 10, 8],
            marker="s", color="#2ECC40",
            output_path=self._tmp_path("line_custom.png"),
        )
        self.assertTrue(os.path.isfile(path))

    def test_line_single_point(self):
        """单个数据点的折线图。"""
        path = ChartTool.line(["A"], [5], output_path=self._tmp_path("line_one.png"))
        self.assertTrue(os.path.isfile(path))


# ── generate_chart 统一入口测试 ───────────────────────────────

class TestGenerateChart(unittest.TestCase):
    """测试 generate_chart 统一入口函数。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _tmp_path(self, name: str) -> str:
        return os.path.join(self.tmpdir, name)

    def _parse_result(self, result: str) -> dict:
        return json.loads(result)

    # ── 正常路径 ──────────────────────────────────────────

    def test_generate_pie_success(self):
        result = self._parse_result(
            generate_chart("pie", ["A", "B"], [30, 70],
                           title="饼图", output_path=self._tmp_path("g_pie.png"))
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "pie")
        self.assertTrue(os.path.isfile(result["path"]))

    def test_generate_bar_success(self):
        result = self._parse_result(
            generate_chart("bar", ["A", "B"], [10, 20],
                           title="柱状图", output_path=self._tmp_path("g_bar.png"))
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "bar")
        self.assertTrue(os.path.isfile(result["path"]))

    def test_generate_line_success(self):
        result = self._parse_result(
            generate_chart("line", ["A", "B", "C"], [1, 3, 2],
                           title="折线图", output_path=self._tmp_path("g_line.png"))
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "line")
        self.assertTrue(os.path.isfile(result["path"]))

    # ── 错误路径 ──────────────────────────────────────────

    def test_invalid_chart_type(self):
        result = self._parse_result(
            generate_chart("scatter", ["A"], [1], output_path=self._tmp_path("bad.png"))
        )
        self.assertFalse(result["success"])
        self.assertIn("不支持", result["error"])

    def test_mismatched_lengths(self):
        result = self._parse_result(
            generate_chart("bar", ["A", "B"], [1],
                           output_path=self._tmp_path("bad.png"))
        )
        self.assertFalse(result["success"])
        self.assertIn("不一致", result["error"])

    def test_empty_lists(self):
        result = self._parse_result(
            generate_chart("pie", [], [], output_path=self._tmp_path("bad.png"))
        )
        self.assertFalse(result["success"])
        self.assertIn("不能为空", result["error"])

    # ── 扩展功能 ──────────────────────────────────────────

    def test_generate_bar_with_xlabel_ylabel(self):
        result = self._parse_result(
            generate_chart("bar", ["Q1", "Q2"], [100, 200],
                           xlabel="季度", ylabel="收入",
                           output_path=self._tmp_path("g_bar_labeled.png"))
        )
        self.assertTrue(result["success"])
        self.assertTrue(os.path.isfile(result["path"]))

    def test_generate_line_with_color_and_marker(self):
        result = self._parse_result(
            generate_chart("line", ["1", "2"], [5, 10],
                           color="#FF0000", marker="D",
                           output_path=self._tmp_path("g_line_styled.png"))
        )
        self.assertTrue(result["success"])

    def test_generate_pie_with_autopct(self):
        result = self._parse_result(
            generate_chart("pie", ["A", "B"], [40, 60],
                           autopct="%.2f%%",
                           output_path=self._tmp_path("g_pie_pct.png"))
        )
        self.assertTrue(result["success"])


# ── ToolRegistry 集成测试 ─────────────────────────────────────

class TestChartToolRegistry(unittest.TestCase):
    """测试图表工具与 ToolRegistry 的集成。"""

    def test_register_chart_tools(self):
        registry = ToolRegistry()
        register_chart_tools(registry)
        self.assertIn("generate_chart", registry)
        self.assertEqual(len(registry), 1)

    def test_execute_via_registry(self):
        """通过 ToolRegistry.execute() 调用图表生成。"""
        registry = ToolRegistry()
        register_chart_tools(registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "via_registry.png")
            args = {
                "chart_type": "bar",
                "labels": ["A", "B"],
                "values": [10, 20],
                "title": "Registry Test",
                "output_path": output_path,
            }
            result_str = registry.execute("generate_chart", args)
            result = json.loads(result_str)
            self.assertTrue(result["success"])
            self.assertTrue(os.path.isfile(result["path"]))

    def test_to_openai_format_includes_chart(self):
        """验证生成的 OpenAI tool schema 包含图表工具。"""
        registry = ToolRegistry()
        register_chart_tools(registry)
        tools = registry.to_openai_format()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "generate_chart")
        self.assertIn("chart_type", tools[0]["function"]["parameters"]["properties"])

    def test_execute_missing_chart_type(self):
        """调用时缺少必要参数应报错（Registry 捕获为通用异常）。"""
        registry = ToolRegistry()
        register_chart_tools(registry)
        result_str = registry.execute("generate_chart", {"labels": ["A"], "values": [1]})
        result = json.loads(result_str)
        # Registry.execute() 将函数抛出的 TypeError 包装为 {"error": ...}
        self.assertIn("error", result)
        self.assertIn("chart_type", result["error"])


# ── 对话中 Tool 调用验证（集成测试，需 API key）───────────────
#
#  核心思路：LLM 对话中 tool 是否被调用，通过检查 client.history 即可判断。
#  当 use_tools=True 且模型决定调用工具时，对话历史中会出现两种特殊消息：
#
#   1. assistant 消息带 tool_calls：{"role":"assistant","tool_calls":[...]}
#      → 模型请求调用工具，tool_calls 中包含 function.name 和 function.arguments
#
#   2. tool 消息：{"role":"tool","tool_call_id":"...","content":"{...}"}
#      → 工具执行结果被追加到历史中
#
#  因此，验证 tool 是否被调用的方法就是：
#    - 遍历 history，找 role=="tool" 的消息
#    - 或找 assistant 消息中 tool_calls 非空的消息
#    - 进一步可以检查 tool_calls 中 function.name 是否为 "generate_chart"

class TestChartToolInConversation(unittest.TestCase):
    """端到端测试：在真实对话中验证 LLM 是否调用了图表工具。

    这些测试会真实调用 DeepSeek API，需要有效的 api_key。
    运行方式（跳过需要 API 的测试）：
        python -m pytest tests/test_chart_tool.py -v -k "not Conversation"
    运行方式（包含全部）：
        DEEPSEEK_API_KEY=xxx python -m pytest tests/test_chart_tool.py -v
    """

    @classmethod
    def setUpClass(cls):
        from llm import create_client
        try:
            cls.client = create_client("deepseek")
        except ValueError as e:
            raise unittest.SkipTest(f"跳过：无法创建客户端 ({e})")

    def setUp(self):
        self.client.reset()
        self.client.register_tool(
            generate_chart,
            description="生成饼图/柱状图/折线图，需提供 chart_type(labels,values,title,output_path)",
        )
        self.tmpdir = tempfile.mkdtemp()

    def _tmp_path(self, name: str) -> str:
        return os.path.join(self.tmpdir, name)

    # ── 方法1：检查 history 中是否有 tool role 的消息 ──────

    def test_tool_invoked__check_tool_role_in_history(self):
        """最简单的方式：检查 history 中是否出现 role=="tool" 的消息。

        只要有一条 tool 消息，就说明 LLM 确实调用了工具并且拿到了结果。
        """
        output_path = self._tmp_path("conv_pie.png")
        self.client.chat(
            f"请帮我画一张饼图，数据是：A占30%、B占45%、C占25%，"
            f"标题写'占比分布'，保存到 {output_path}",
            use_tools=True,
        )

        # 核心断言：history 中必须出现 tool role
        roles = {m["role"] for m in self.client.history}
        self.assertIn("tool", roles, "LLM 没有调用任何工具！")

    # ── 方法2：检查 assistant 消息中的 tool_calls 字段 ─────

    def test_tool_invoked__check_tool_calls_in_assistant_message(self):
        """更精确：检查 assistant 消息中是否包含 tool_calls。

        可以进一步验证 tool_calls 中的 function.name 是否为 generate_chart。
        """
        output_path = self._tmp_path("conv_bar.png")
        self.client.chat(
            f"画一个柱状图：苹果=100, 香蕉=80, 橘子=60，"
            f"标题'水果销量'，保存到 {output_path}",
            use_tools=True,
        )

        # 找到所有 assistant 消息中带 tool_calls 的
        tool_call_requests = [
            m for m in self.client.history
            if m["role"] == "assistant" and m.get("tool_calls")
        ]
        self.assertGreater(len(tool_call_requests), 0, "LLM 没有请求调用任何工具！")

        # 进一步验证：确认调用的是 generate_chart
        called_functions = set()
        for msg in tool_call_requests:
            for tc in msg["tool_calls"]:
                called_functions.add(tc["function"]["name"])
        self.assertIn("generate_chart", called_functions,
                      f"LLM 调用了工具，但不是 generate_chart，而是: {called_functions}")

    # ── 方法3：验证工具执行产物（文件确实生成了）───────────

    def test_tool_invoked__chart_file_actually_created(self):
        """最终验证：LLM 调用工具后，图表文件确实被生成了。"""
        output_path = self._tmp_path("conv_line.png")
        self.client.chat(
            f"帮我画折线图，1月=10, 2月=25, 3月=15, 4月=30，"
            f"标题'月度趋势'，保存到 {output_path}",
            use_tools=True,
        )

        # 1) 确认 history 中有 tool 消息
        tool_msgs = [m for m in self.client.history if m["role"] == "tool"]
        self.assertGreater(len(tool_msgs), 0, "LLM 没有调用工具")

        # 2) 确认 generate_chart 返回了 success
        chart_results = [
            json.loads(m["content"]) for m in tool_msgs
        ]
        success_results = [r for r in chart_results if r.get("success")]
        self.assertGreater(len(success_results), 0,
                           f"工具虽被调用但都失败了: {chart_results}")

        # 3) 确认文件确实存在
        saved_path = success_results[0]["path"]
        self.assertTrue(os.path.isfile(saved_path),
                        f"工具声称保存到 {saved_path}，但文件不存在")
        self.assertGreater(os.path.getsize(saved_path), 0)

    # ── 方法4：未注册工具时不调用 ──────────────────────────

    def test_tool_not_called_when_not_registered(self):
        """use_tools=True 但没有注册任何工具时，LLM 应直接文本回复。"""
        client2 = self.__class__.client.__class__(
            api_key=self.client.api_key,
            model=self.client.model,
            base_url=self.client.base_url,
        )
        output_path = self._tmp_path("no_tool.png")
        reply = client2.chat(
            f"画饼图：A=50, B=50，保存到 {output_path}",
            use_tools=True,
        )
        # 没有注册工具，所以 history 中不应有 tool role
        roles = {m["role"] for m in client2.history}
        self.assertNotIn("tool", roles, "未注册工具时不应触发 tool 调用")
        # 模型应返回文本回复（可能说它无法画图）
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    # ── 方法5：检查 tool_calls 中的具体参数 ─────────────────

    def test_tool_invoked__verify_arguments_passed(self):
        """深入验证：检查 LLM 传给 generate_chart 的参数是否正确。"""
        output_path = self._tmp_path("conv_args.png")
        self.client.chat(
            f"用饼图画一下三个部门的预算占比：技术部=500, 市场部=300, 行政部=200，"
            f"标题'部门预算'，保存到 {output_path}",
            use_tools=True,
        )

        # 提取所有 tool_calls
        all_tool_calls = []
        for m in self.client.history:
            if m["role"] == "assistant" and m.get("tool_calls"):
                all_tool_calls.extend(m["tool_calls"])

        chart_calls = [
            tc for tc in all_tool_calls
            if tc["function"]["name"] == "generate_chart"
        ]
        self.assertGreater(len(chart_calls), 0, "未找到 generate_chart 的调用记录")

        # 解析 LLM 传入的参数
        args = json.loads(chart_calls[0]["function"]["arguments"])
        # LLM 可能传 "pie" 或 "饼图" 等，宽松校验
        chart_type = args.get("chart_type", "")
        self.assertIn(chart_type, ("pie", "饼图", "Pie"),
                      f"chart_type 不是饼图相关值: {chart_type}")
        # labels/values 可能被 LLM 传为逗号分隔字符串或 JSON 数组，两种都接受
        labels = args.get("labels", [])
        values = args.get("values", [])
        if isinstance(labels, str):
            labels = [s.strip() for s in labels.split(",")]
        if isinstance(values, str):
            values = [float(v.strip()) for v in values.split(",") if v.strip()]
        self.assertIn("技术部", labels)
        # 验证 values 中包含 500（可能是 int 或 float）
        self.assertTrue(any(abs(v - 500) < 0.01 for v in values),
                        f"values 中未找到 500: {values}")


# ── 运行入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
