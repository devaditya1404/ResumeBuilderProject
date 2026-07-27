import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, engine
from app.core.config import settings

# Ensure data directories exist
DATA_DIR = Path("./data")
RESUME_DIR = Path(settings.RESUME_STORAGE_PATH)
FAISS_DIR = Path(settings.FAISS_INDEX_PATH)

for d in [DATA_DIR, RESUME_DIR, FAISS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# SQLAlchemy Async Engine
engine_uri = settings.DATABASE_URL
if engine_uri.startswith("sqlite://"):
    engine_uri = engine_uri.replace("sqlite://", "sqlite+aiosqlite://", 1)

async_engine = create_async_engine(
    engine_uri,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Enable WAL Mode and Foreign Keys on SQLite Connect
@event.listens_for(engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
