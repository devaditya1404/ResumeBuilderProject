import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, engine
from app.core.config import settings

import logging
import shutil

logger = logging.getLogger(__name__)

# Ensure data directories exist
DATA_DIR = Path("./data")
RESUME_DIR = Path(settings.RESUME_STORAGE_PATH)
FAISS_DIR = Path(settings.FAISS_INDEX_PATH)

for d in [DATA_DIR, RESUME_DIR, FAISS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Render Persistent Disk One-Time Migration Helper ──
def migrate_ephemeral_to_persistent_storage():
    """
    If running on Render with /app/data mounted, perform a safe one-time copy of existing
    ephemeral database & file assets into persistent storage /app/data if not already present.
    """
    if not os.path.isdir("/app/data"):
        return

    persistent_db = Path("/app/data/talentvault.db")
    ephemeral_db = Path("./data/talentvault.db")

    if not persistent_db.exists() and ephemeral_db.exists():
        try:
            logger.info("Migrating existing ephemeral database to persistent storage at /app/data/...")
            os.makedirs("/app/data", exist_ok=True)
            shutil.copy2(ephemeral_db, persistent_db)

            # Copy WAL and SHM files if present
            for ext in ["-shm", "-wal"]:
                e_file = Path(f"./data/talentvault.db{ext}")
                p_file = Path(f"/app/data/talentvault.db{ext}")
                if e_file.exists():
                    shutil.copy2(e_file, p_file)

            # Copy resumes directory
            e_resumes = Path("./data/resumes")
            p_resumes = Path("/app/data/resumes")
            if e_resumes.exists() and e_resumes.is_dir():
                os.makedirs(p_resumes, exist_ok=True)
                for item in e_resumes.iterdir():
                    if item.is_file():
                        shutil.copy2(item, p_resumes / item.name)

            # Copy FAISS index directory
            e_faiss = Path("./data/faiss")
            p_faiss = Path("/app/data/faiss")
            if e_faiss.exists() and e_faiss.is_dir():
                os.makedirs(p_faiss, exist_ok=True)
                for item in e_faiss.iterdir():
                    if item.is_file():
                        shutil.copy2(item, p_faiss / item.name)

            logger.info("One-time persistent storage migration completed successfully!")
        except Exception as e:
            logger.exception(f"Failed to migrate ephemeral database to persistent storage: {str(e)}")

# Execute one-time storage migration before engine connection
migrate_ephemeral_to_persistent_storage()

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
        # Auto-migrate missing columns for SQLite
        def migrate_sqlite_columns(sync_conn):
            from sqlalchemy import text
            try:
                res = sync_conn.execute(text("PRAGMA table_info(candidates)"))
                columns = [row[1] for row in res.fetchall()]
                if "languages" not in columns:
                    sync_conn.execute(text("ALTER TABLE candidates ADD COLUMN languages JSON"))
            except Exception:
                pass
        await conn.run_sync(migrate_sqlite_columns)
