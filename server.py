"""revive Chat — 启动入口。

用法：
    python server.py
    uvicorn app:app --reload --port 8080
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
