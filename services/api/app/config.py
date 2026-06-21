import os

from pydantic import BaseModel, Field


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    service_name: str = "market-radar-api"
    provider_name: str = "mock"
    market_data_provider: str = Field(default="mock", pattern="^(mock|moomoo)$")
    event_data_provider: str = Field(default="mock", pattern="^(mock|sec)$")
    free_only_mode: bool = True
    scheduler_enabled: bool = False
    sec_user_agent: str | None = None
    api_prefix: str = "/api/v1"


settings = Settings(
    market_data_provider=os.getenv("MARKET_DATA_PROVIDER", "mock"),
    event_data_provider=os.getenv("EVENT_DATA_PROVIDER", "mock"),
    free_only_mode=_read_bool("FREE_ONLY_MODE", True),
    scheduler_enabled=_read_bool("SCHEDULER_ENABLED", False),
    sec_user_agent=os.getenv("SEC_USER_AGENT"),
)
