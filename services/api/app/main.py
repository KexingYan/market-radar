from fastapi import FastAPI

from app.api.routes import alerts, events, filings, health, history, jobs, live, providers, quotes, reports, storage, watchlist
from app.config import settings

app = FastAPI(
    title="Market Radar API",
    description="Mock-only API for Phase 1. No real market data or trading features.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(quotes.router)
app.include_router(events.router)
app.include_router(filings.router)
app.include_router(providers.router)
app.include_router(reports.router)
app.include_router(history.router)
app.include_router(storage.router)
app.include_router(watchlist.router)
app.include_router(alerts.router)
app.include_router(jobs.router)
app.include_router(live.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "provider": settings.provider_name,
        "disclaimer": "仅供信息展示，不构成投资建议。",
    }
