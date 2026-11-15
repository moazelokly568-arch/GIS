import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import router as api_router
from config import settings
from database import init_db

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_db()


os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=settings.ARTIFACTS_DIR), name="artifacts")
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
