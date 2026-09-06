import os
import json
from typing import Optional, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ResumeX Brain / TalentVault AI"
    API_V1_STR: str = "/api"
    
    # SQLite Database URI
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/talentvault.db")
    
    # Storage Paths
    RESUME_STORAGE_PATH: str = os.getenv("RESUME_STORAGE_PATH", "./data/resumes")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss")
    
    # CORS Origins Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(item).strip().rstrip("/") for item in parsed if item]
                except Exception:
                    pass
            return [i.strip().rstrip("/") for i in v_str.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip().rstrip("/") for i in v if i]
        return []

    # Provider Abstraction Configuration
    # Options: "gemini" (Production Cloud API - Free Tier) | "groq" (Cloud) | "ollama" (Local Dev)
    LLM_PROVIDER: str = "gemini"

    @field_validator("LLM_PROVIDER", mode="before")
    @classmethod
    def validate_llm_provider(cls, v: Union[str, None]) -> str:
        prov = (str(v) if v is not None else "").strip().lower()
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY") or os.getenv("CLOUD_LLM_API_KEY")
        
        if prov == "ollama":
            return "ollama"
        if prov == "gemini" or gemini_key or not groq_key:
            return "gemini"
        if prov == "groq" and groq_key:
            return "groq"
        return "gemini"

    # Gemini API Settings (Free Cloud Tier)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", None))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

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

