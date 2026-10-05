"""Bound the complete image multipart body, including chunked requests, before parsing."""
from starlette.responses import JSONResponse


class ImageUploadLimitMiddleware:
    def __init__(self, app, path, max_bytes):
        self.app, self.path, self.max_bytes = app, path, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].rstrip("/") != self.path:
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                response = JSONResponse({"success": False, "error": {
                    "code": "IMAGE_TOO_LARGE", "message": "Image exceeds the maximum allowed upload size."
                }}, status_code=413)
                return await response(scope, receive, send)
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        chunks.clear()
        delivered = False

        async def bounded_receive():
            nonlocal delivered, body
            if delivered:
                return await receive()
            delivered = True
            message = {"type": "http.request", "body": body, "more_body": False}
            body = b""
            return message

        await self.app(scope, bounded_receive, send)
