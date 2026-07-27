import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import candidates, resumes, requirements, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize SQLite database and tables on startup
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS dynamically for cloud deployment & local dev ports
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
if allowed_origins_env:
    if allowed_origins_env.strip() == "*":
        origins = ["*"]
    else:
        for o in allowed_origins_env.split(","):
            cleaned = o.strip()
            if cleaned and cleaned not in origins:
                origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True if origins != ["*"] else False,
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
