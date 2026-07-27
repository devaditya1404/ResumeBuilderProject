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
    
    # Provider Abstraction Configuration
    # Options: "ollama" (for local dev) | "groq" (for production cloud)
    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER", 
        "groq" if os.getenv("GROQ_API_KEY") or os.getenv("CLOUD_LLM_API_KEY") else ("ollama" if os.getenv("OLLAMA_MODE", "").lower() == "local" else "groq")
    ).lower()

    # Cloud Production LLM Settings (Groq API)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", os.getenv("CLOUD_LLM_API_KEY", None))
    CLOUD_LLM_API_KEY: Optional[str] = os.getenv("CLOUD_LLM_API_KEY", os.getenv("GROQ_API_KEY", None))
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", os.getenv("CLOUD_LLM_MODEL", "llama-3.1-8b-instant"))
    
    # Local Ollama AI Settings
    OLLAMA_MODE: str = os.getenv("OLLAMA_MODE", "local").lower()
    OLLAMA_API_KEY: Optional[str] = os.getenv("OLLAMA_API_KEY", None)
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", 
        "http://127.0.0.1:11434" if os.getenv("OLLAMA_MODE", "local").lower() == "local" else "https://ollama.com"
    )
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "768"))
    OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120.0"))
    DEBUG_PARSER: bool = os.getenv("DEBUG_PARSER", "true").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
