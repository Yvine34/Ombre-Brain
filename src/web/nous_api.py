"""
========================================
web/nous_api.py — Nous 前端专用 REST 接口（免鉴权）
========================================

GET  /api/nous/buckets?domain=diary     — 按 domain 筛选桶，返回完整内容
GET  /api/nous/buckets?tags=whisper     — 按 tags 筛选桶
GET  /api/nous/bucket/{id}              — 读取单个桶完整内容
POST /api/nous/bucket/{id}/comments     — 给桶追加评论

不需要鉴权，供 Nous 前端直接调用。

对外暴露：register(mcp)。
========================================
"""

import frontmatter

from starlette.requests import Request
from starlette.responses import Response

from utils import generate_bucket_id, now_iso
from . import _shared as sh


def _bucket_to_dict(b: dict) -> dict:
    meta = b.get("metadata", {})
    return {
        "id": b.get("id", ""),
        "name": meta.get("name", ""),
        "content": b.get("content", ""),
        "domain": meta.get("domain", []),
        "tags": meta.get("tags", []),
        "created": meta.get("created", ""),
        "last_active": meta.get("last_active", ""),
        "importance": meta.get("importance", 5),
        "valence": meta.get("valence", 0.5),
        "arousal": meta.get("arousal", 0.3),
        "resolved": meta.get("resolved", False),
        "pinned": meta.get("pinned", False),
        "date": meta.get("date", ""),
        "comments": meta.get("comments", []),
        "type": meta.get("type", "dynamic"),
    }


def register(mcp) -> None:

    @mcp.custom_route("/api/nous/buckets", methods=["GET"])
    async def api_nous_buckets(request: Request) -> Response:
        from starlette.responses import JSONResponse
        try:
            domain = request.query_params.get("domain", "")
            tags_param = request.query_params.get("tags", "")
            tag_filters = [t.strip() for t in tags_param.split(",") if t.strip()]

            all_buckets = await sh.bucket_mgr.list_all()
            result = []
            for b in all_buckets:
                meta = b.get("metadata", {})
                if meta.get("deleted_at"):
                    continue
                b_domain = meta.get("domain", [])
                b_tags = meta.get("tags", [])
                if domain and domain not in b_domain:
                    continue
                if tag_filters and not any(t in b_tags for t in tag_filters):
                    continue
                result.append(_bucket_to_dict(b))

            result.sort(key=lambda x: x.get("created", ""), reverse=True)
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/nous/bucket/{bucket_id}", methods=["GET"])
    async def api_nous_bucket_detail(request: Request) -> Response:
        from starlette.responses import JSONResponse
        try:
            bucket_id = request.path_params["bucket_id"]
            b = await sh.bucket_mgr.get(bucket_id)
            if not b:
                return JSONResponse({"error": "not found"}, status_code=404)
            return JSONResponse(_bucket_to_dict(b))
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/nous/bucket/{bucket_id}/comments", methods=["POST"])
    async def api_nous_bucket_comment(request: Request) -> Response:
        from starlette.responses import JSONResponse
        bucket_id = request.path_params["bucket_id"]
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid json"}, status_code=400)
        content = str(body.get("content") or "").strip()
        if not content:
            return JSONResponse({"error": "content required"}, status_code=400)

        file_path = sh.bucket_mgr._find_bucket_file(bucket_id)
        if not file_path:
            return JSONResponse({"error": "not found"}, status_code=404)

        try:
            post = frontmatter.load(file_path)
        except Exception:
            return JSONResponse({"error": "read failed"}, status_code=500)

        comments = post.get("comments", [])
        if not isinstance(comments, list):
            comments = []

        now = now_iso()
        entry = {
            "id": generate_bucket_id(),
            "created": now,
            "author": str(body.get("author") or "小颖"),
            "kind": "comment",
            "content": content,
        }
        comments.append(entry)
        post["comments"] = comments
        post["comment_count"] = len(comments)
        post["updated_at"] = now

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
        except Exception:
            return JSONResponse({"error": "write failed"}, status_code=500)

        return JSONResponse({"status": "commented", "id": bucket_id, "comment": entry})
