"""
Health Check API Endpoints for TalentVault.
Provides AI provider health & availability check (/api/health/ai).
"""
import logging
from fastapi import APIRouter
from app.ai.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/ai")
async def check_ai_health():
    """
    Check availability and details of configured AI LLM provider.
    Returns:
        available: bool
        provider: "ollama" | "groq"
        model: str
        error: Optional[str]
    """
    provider = get_llm_provider()
    health_details = await provider.check_health_details()
    logger.info(f"GET /api/health/ai -> available={health_details.get('available')}, provider={health_details.get('provider')}")
    return health_details
