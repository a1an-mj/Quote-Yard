"""Serves the built frontend from the API process, so one service is the whole site."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
# Vite puts a content hash in these file names, so they can be cached for good.
FOREVER = "public, max-age=31536000, immutable"


def add_site(app: FastAPI, api_prefix: str) -> None:
    root = Path(os.environ.get("QUOTE_YARD_SITE_DIR", DEFAULT_DIR)).resolve()
    index = root / "index.html"
    if not index.is_file():
        return  # development: Vite serves the site

    @app.get("/{path:path}", include_in_schema=False)
    def site(path: str):
        # A wrong API path stays an API 404, never the site's page.
        if f"/{path}".startswith(f"{api_prefix}/") or f"/{path}" == api_prefix:
            raise HTTPException(status_code=404, detail="Not Found")
        target = (root / path).resolve()
        if path and target.is_relative_to(root) and target.is_file():
            headers = {"Cache-Control": FOREVER} if path.startswith("assets/") else None
            return FileResponse(target, headers=headers)
        if path.startswith("assets/"):
            raise HTTPException(status_code=404, detail="Not Found")
        # React Router owns every other path; index.html must never be cached.
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
