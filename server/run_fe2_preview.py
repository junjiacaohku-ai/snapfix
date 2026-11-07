"""Serve a locally built Flutter web app and the API on one origin."""
from pathlib import Path

from fastapi.staticfiles import StaticFiles
import uvicorn

from main import app


if __name__ == "__main__":
    web = Path(__file__).resolve().parents[1] / "app" / "build" / "web"
    if not (web / "index.html").is_file():
        raise SystemExit("Run flutter build web in app/ first; see docs/fe2/README.md")
    app.mount("/", StaticFiles(directory=web, html=True), name="fe2-preview")
    uvicorn.run(app, host="127.0.0.1", port=8000)
