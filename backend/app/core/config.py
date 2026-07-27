import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ResumeX Brain / TalentVault AI"
    API_V1_STR: str = "/api"
    
    # SQLite Database URI
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/talentvault.db")
    
    # Storage Paths
    RESUME_STORAGE_PATH: str = os.getenv("RESUME_STORAGE_PATH", "./data/resumes")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss")
    
    # AI Configuration (Local / Cloud)
    OLLAMA_MODE: str = os.getenv("OLLAMA_MODE", "cloud").lower()
    OLLAMA_API_KEY: Optional[str] = os.getenv("OLLAMA_API_KEY", None)
    
    # Dynamic base URL default based on OLLAMA_MODE
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", 
        "https://ollama.com" if os.getenv("OLLAMA_MODE", "cloud").lower() == "cloud" else "http://127.0.0.1:11434"
    )
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "768"))
    OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120.0"))
    DEBUG_PARSER: bool = os.getenv("DEBUG_PARSER", "true").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
