import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import candidates, resumes, requirements, dashboard

import logging

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize SQLite database and tables on startup
    await init_db()
    logger.info(
        f"Startup Diagnostics: LLM_PROVIDER='{settings.LLM_PROVIDER}', "
        f"OLLAMA_MODE='{settings.OLLAMA_MODE}', GROQ_MODEL='{settings.GROQ_MODEL}', "
        f"GROQ_API_KEY Configured={'YES' if bool(settings.GROQ_API_KEY or settings.CLOUD_LLM_API_KEY) else 'NO'}"
    )
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Explicitly allowed frontend origins for production and local development
default_origins = [
    "https://talentvault-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]

# Parse environment variable ALLOWED_ORIGINS if provided
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = list(default_origins)

if allowed_origins_env and allowed_origins_env.strip():
    for item in allowed_origins_env.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

# Configure FastAPI CORSMiddleware with credentials support
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(candidates.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(requirements.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "database": "SQLite (WAL mode active)",
        "docs": "/docs"
    }
