#!/bin/bash
# revive Chat — 一键启动脚本
# 同时启动 FastAPI 后端 (:8080) 和 React 前端 (:5173)

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  revive Chat — 启动中..."
echo "========================================"

# 1) 安装 Python 依赖（如需要）
echo "[1/3] 检查 Python 依赖..."
python -c "import fastapi, uvicorn, matplotlib, openai" 2>/dev/null || {
    echo "  安装 Python 依赖..."
    pip install fastapi uvicorn matplotlib openai -q
}

# 2) 安装前端依赖（如需要）
echo "[2/3] 检查前端依赖..."
if [ ! -d "$DIR/frontend/node_modules" ]; then
    echo "  安装前端依赖..."
    cd "$DIR/frontend" && npm install --silent
fi

# 3) 启动服务
echo "[3/3] 启动服务..."
echo ""
echo "  后端 API:  http://localhost:8080"
echo "  前端界面:  http://localhost:5173"
echo "  API 文档:  http://localhost:8080/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================"
echo ""

# 使用 trap 确保退出时清理
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "已停止。"
}
trap cleanup EXIT INT TERM

# 启动后端
cd "$DIR"
python server.py &
BACKEND_PID=$!

# 启动前端
cd "$DIR/frontend"
npx vite --host &
FRONTEND_PID=$!

# 等待任意子进程退出
wait -n $BACKEND_PID $FRONTEND_PID 2>/dev/null
