from fastapi import APIRouter

from app.repositories import storage_metrics

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


@router.get("/status")
async def storage_status() -> dict[str, int | bool | str]:
    return storage_metrics.status()


@router.get("/retention-preview")
async def retention_preview() -> dict[str, int | bool]:
    return storage_metrics.retention_preview()
