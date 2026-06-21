from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "environment": "local",
        "provider": settings.provider_name,
        "external_network_enabled": False,
        "trading_enabled": False,
    }
