from fastapi import APIRouter

from app.alerts.service import AlertService
from app.live_e2e import LiveAaplE2EResponse, LiveAaplE2EService, LiveWatchlistRefreshResponse
from app.repositories import (
    alert_repository,
    alert_rule_repository,
    event_repository,
    job_run_repository,
    quote_repository,
    report_repository,
    watchlist_repository,
)
from app.services.archive import ArchiveService

router = APIRouter(prefix="/api/v1/live", tags=["live"])


def _alert_service_factory(quote_provider, event_provider) -> AlertService:
    return AlertService(
        rule_repository=alert_rule_repository,
        alert_repository=alert_repository,
        watchlist_repository=watchlist_repository,
        quote_provider=quote_provider,
        event_provider=event_provider,
    )


service = LiveAaplE2EService(
    archive_service=ArchiveService(quote_repository, event_repository, report_repository),
    alert_service_factory=_alert_service_factory,
    job_run_repository=job_run_repository,
)


@router.post("/aapl-e2e")
async def live_aapl_e2e() -> LiveAaplE2EResponse:
    return await service.run()


@router.post("/watchlist-refresh")
async def live_watchlist_refresh() -> LiveWatchlistRefreshResponse:
    watchlist = await watchlist_repository.list_symbols()
    return await service.run_watchlist_refresh(watchlist)
