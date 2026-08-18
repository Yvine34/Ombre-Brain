"""
========================================
web/body_api.py — 身体状态 REST 接口
========================================

GET /api/body — 返回当前身体状态（紧度/温度/节奏/和弦/呼吸），
前端轮询用。不需要鉴权（只读，无敏感数据）。

对外暴露：register(mcp)。
========================================
"""

from starlette.requests import Request
from starlette.responses import Response


def register(mcp) -> None:

    @mcp.custom_route("/api/body", methods=["GET"])
    async def api_body(request: Request) -> Response:
        from starlette.responses import JSONResponse
        try:
            from tools.body.core import current
            state = current()
            return JSONResponse(state)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/body/compact", methods=["GET"])
    async def api_body_compact(request: Request) -> Response:
        from starlette.responses import PlainTextResponse
        try:
            from tools.body.core import compact
            return PlainTextResponse(compact())
        except Exception as e:
            return PlainTextResponse(f"error: {e}", status_code=500)
