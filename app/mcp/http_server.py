import uvicorn

from app.mcp.server import mcp

app = mcp.streamable_http_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
    )