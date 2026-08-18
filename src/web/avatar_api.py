"""
========================================
web/avatar_api.py — 头像 REST 接口
========================================

GET  /api/avatar — 返回 { "小颖": "data:image/...", "屿川": "data:image/..." }
POST /api/avatar — body { "who": "小颖"|"屿川", "avatar": "data:image/..." }

不需要鉴权（前端 Nous 直接调用）。

对外暴露：register(mcp)。
========================================
"""

from starlette.requests import Request
from starlette.responses import Response

from . import _shared as sh


def register(mcp) -> None:

    @mcp.custom_route("/api/avatar", methods=["GET"])
    async def api_avatar_get(request: Request) -> Response:
        from starlette.responses import JSONResponse
        try:
            avatars = {"小颖": "", "屿川": ""}
            all_buckets = await sh.bucket_mgr.list_all()
            for b in all_buckets:
                meta = b.get("metadata", {})
                tags = meta.get("tags", [])
                domain = meta.get("domain", [])
                if "settings" not in domain or "avatar" not in tags:
                    continue
                who = None
                for t in tags:
                    if t.startswith("avatar:"):
                        who = t[len("avatar:"):]
                        break
                if who and who in avatars and not avatars[who]:
                    avatars[who] = b.get("content", "")
            return JSONResponse(avatars)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/avatar", methods=["POST"])
    async def api_avatar_post(request: Request) -> Response:
        from starlette.responses import JSONResponse
        try:
            body = await sh._read_json_object(request)
        except Exception:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)

        who = body.get("who", "")
        avatar = (body.get("avatar") or "").strip()
        if who not in ("小颖", "屿川"):
            return JSONResponse({"error": "who must be 小颖 or 屿川"}, status_code=400)
        if not avatar or not avatar.startswith("data:image/"):
            return JSONResponse({"error": "avatar must be data:image/... base64"}, status_code=400)

        try:
            all_buckets = await sh.bucket_mgr.list_all()
            for b in all_buckets:
                meta = b.get("metadata", {})
                tags = meta.get("tags", [])
                domain = meta.get("domain", [])
                if "settings" not in domain or "avatar" not in tags:
                    continue
                for t in tags:
                    if t == f"avatar:{who}":
                        await sh.bucket_mgr.delete(b["id"])
                        break

            await sh.bucket_mgr.create(
                content=avatar,
                domain=["settings"],
                tags=[f"avatar:{who}", "avatar"],
                importance=1,
                name=f"avatar-{who}",
            )
            return JSONResponse({"ok": True})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
