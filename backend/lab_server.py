"""Authenticated single-port entrypoint for UBET Lab."""
import os
import secrets
from pathlib import Path
from flask import request, Response, send_from_directory, abort
from waitress import serve
from app import create_app
from app.config import Config

password = os.environ.get("LAB_PASSWORD", "")
if len(password) < 20:
    raise RuntimeError("LAB_PASSWORD must have at least 20 characters")
if not os.environ.get("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY is required")
if Config.validate():
    raise RuntimeError("Required configuration is missing or invalid")
app = create_app()
dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

@app.before_request
def require_login():
    if request.path == "/health" and request.method in ("GET", "HEAD"):
        return None
    auth = request.authorization
    if auth and auth.type == "basic" and secrets.compare_digest((auth.username or "").encode(), b"admin") and secrets.compare_digest((auth.password or "").encode(), password.encode()):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("Origin")
            host = os.environ.get("RENDER_EXTERNAL_URL")
            if not host or origin != host:
                abort(403)
        return None
    return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="UBET Lab", charset="UTF-8"', "Cache-Control": "no-store"})

@app.after_request
def privacy_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers.pop("Access-Control-Allow-Origin", None)
    response.headers.pop("Access-Control-Allow-Credentials", None)
    return response

@app.get("/")
@app.get("/<path:filename>")
def frontend(filename="index.html"):
    if filename.startswith("api/") or filename == "api":
        abort(404)
    if (dist / filename).is_file():
        return send_from_directory(dist, filename)
    return send_from_directory(dist, "index.html")

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), threads=8, max_request_body_size=55*1024*1024, channel_timeout=600)
