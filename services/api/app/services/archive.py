from dataclasses import dataclass

from app.domain.market_event import MarketEvent
from app.domain.quote import QuoteSnapshot
from app.domain.report import MarketReport
from app.repositories.base import EventRepository, QuoteRepository, ReportRepository


@dataclass(frozen=True)
class ArchiveResult:
    inserted: int
    duplicates: int
    failed: int


class ArchiveService:
    def __init__(
        self,
        quote_repository: QuoteRepository,
        event_repository: EventRepository,
        report_repository: ReportRepository,
    ) -> None:
        self._quote_repository = quote_repository
        self._event_repository = event_repository
        self._report_repository = report_repository

    async def archive_quotes(self, quotes: list[QuoteSnapshot]) -> ArchiveResult:
        result = await self._quote_repository.save_snapshots(quotes)
        return ArchiveResult(result.inserted, result.duplicates, result.failed)

    async def archive_events(self, events: list[MarketEvent]) -> ArchiveResult:
        result = await self._event_repository.save_events(events)
        return ArchiveResult(result.inserted, result.duplicates, result.failed)

    async def archive_report(self, report: MarketReport) -> ArchiveResult:
        result = await self._report_repository.save_report(report)
        return ArchiveResult(result.inserted, result.duplicates, result.failed)
