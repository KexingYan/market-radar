from fastapi import APIRouter

from app.providers.base import ProvidersStatusResponse
from app.providers.registry import provider_status

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])


@router.get("/status")
async def get_provider_status() -> ProvidersStatusResponse:
    return provider_status()
