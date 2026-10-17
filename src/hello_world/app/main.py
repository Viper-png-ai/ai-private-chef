from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from hello_world.app.api.v1 import api_router

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="AI Private Chef",
    version="0.1.0",
)

app.include_router(api_router)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

@app.get("/health")
def health()->dict[str,str]:
    return {"status": "ok"}

@app.get("/")
def index()->FileResponse:
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/register")
def register_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "register.html")


