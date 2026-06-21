import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx

from app.domain.market_event import EventType, MarketEvent, Sentiment
from app.providers.base import ProviderReason, ProviderUnavailableError

SEC_DATA_HOST = "data.sec.gov"
SEC_WWW_HOST = "www.sec.gov"
SUPPORTED_FORMS = {"8-K", "10-K", "10-Q", "6-K", "20-F", "4", "13D", "13G"}
FORM_IMPORTANCE = {
    "8-K": 85,
    "10-K": 80,
    "20-F": 80,
    "10-Q": 75,
    "6-K": 75,
    "13D": 75,
    "13G": 65,
    "4": 55,
}


class SecEdgarEventProvider:
    provider_name = "sec"

    def __init__(
        self,
        user_agent: str | None,
        client: httpx.AsyncClient | None = None,
        request_interval_seconds: float = 0.5,
    ) -> None:
        self._user_agent = user_agent
        self._client = client
        self._request_interval_seconds = request_interval_seconds
        self._last_request_at = 0.0
        self._ticker_cache: tuple[datetime, dict[str, dict[str, Any]]] | None = None
        self._submissions_cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    async def get_events(
        self,
        symbols: list[str] | None = None,
        minimum_importance: int | None = None,
        forms: list[str] | None = None,
        limit: int = 50,
    ) -> list[MarketEvent]:
        if not self._user_agent:
            raise ProviderUnavailableError(ProviderReason.missing_user_agent)
        requested = [symbol.upper() for symbol in (symbols or [])]
        if not requested:
            return []
        if len(requested) > 10:
            raise ProviderUnavailableError(ProviderReason.unsupported_symbol)
        form_filter = set(forms or SUPPORTED_FORMS)
        if not form_filter.issubset(SUPPORTED_FORMS):
            raise ProviderUnavailableError(ProviderReason.unsupported_symbol)

        mapping = await self.get_ticker_mapping()
        events: list[MarketEvent] = []
        for symbol in requested:
            if "." in symbol:
                continue
            record = mapping.get(symbol)
            if not record:
                continue
            submissions = await self.get_company_submissions(str(record["cik_str"]))
            events.extend(self.submissions_to_events(symbol, record, submissions, form_filter))
        if minimum_importance is not None:
            events = [event for event in events if event.importance_score >= minimum_importance]
        return events[:limit]

    async def get_ticker_mapping(self) -> dict[str, dict[str, Any]]:
        now = datetime.now(UTC)
        if self._ticker_cache and now - self._ticker_cache[0] < timedelta(hours=24):
            return self._ticker_cache[1]
        payload = await self._get_json(f"https://{SEC_WWW_HOST}/files/company_tickers.json")
        mapping = self.parse_ticker_mapping(payload)
        self._ticker_cache = (now, mapping)
        return mapping

    async def get_company_submissions(self, cik: str) -> dict[str, Any]:
        padded_cik = cik.zfill(10)
        now = datetime.now(UTC)
        cached = self._submissions_cache.get(padded_cik)
        if cached and now - cached[0] < timedelta(minutes=5):
            return cached[1]
        payload = await self._get_json(f"https://{SEC_DATA_HOST}/submissions/CIK{padded_cik}.json")
        self._submissions_cache[padded_cik] = (now, payload)
        return payload

    @staticmethod
    def parse_ticker_mapping(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        mapping: dict[str, dict[str, Any]] = {}
        for item in payload.values():
            ticker = str(item.get("ticker", "")).upper()
            if ticker:
                mapping[ticker] = item
        return mapping

    def submissions_to_events(
        self,
        symbol: str,
        company: dict[str, Any],
        submissions: dict[str, Any],
        forms: set[str],
    ) -> list[MarketEvent]:
        recent = submissions.get("filings", {}).get("recent", {})
        events: list[MarketEvent] = []
        for form, filing_date, accession, document in zip(
            recent.get("form", []),
            recent.get("filingDate", []),
            recent.get("accessionNumber", []),
            recent.get("primaryDocument", []),
            strict=False,
        ):
            if form not in forms:
                continue
            cik = str(company["cik_str"]).zfill(10)
            company_name = str(company.get("title", symbol))
            submitted_at = datetime.fromisoformat(f"{filing_date}T00:00:00+00:00")
            source_url = self.build_filing_url(cik, str(accession), str(document or ""))
            importance = FORM_IMPORTANCE.get(form, 50)
            events.append(
                MarketEvent(
                    id=f"sec-{symbol}-{str(accession)}",
                    event_type=EventType.regulatory_filing,
                    title=f"{company_name} submitted Form {form}",
                    summary=f"{company_name} submitted Form {form} on {filing_date}.",
                    source_name="SEC EDGAR",
                    source_url=source_url,
                    published_at=submitted_at,
                    received_at=submitted_at,
                    affected_symbols=[symbol],
                    importance_score=importance,
                    reliability_score=100,
                    sentiment=Sentiment.neutral,
                    confidence=1.0,
                    is_mock=False,
                )
            )
        return events

    @staticmethod
    def build_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
        compact_accession = accession_number.replace("-", "")
        if not primary_document:
            return f"https://{SEC_WWW_HOST}/Archives/edgar/data/{int(cik)}/{compact_accession}/"
        return f"https://{SEC_WWW_HOST}/Archives/edgar/data/{int(cik)}/{compact_accession}/{primary_document}"

    async def _get_json(self, url: str) -> dict[str, Any]:
        self._validate_url(url)
        headers = {"User-Agent": self._user_agent or ""}
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                await self._rate_limit()
                async with self._client_or_default() as client:
                    response = await client.get(url, headers=headers, follow_redirects=False)
                if response.status_code == 429 and attempt == 0:
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == 1:
                    break
        raise ProviderUnavailableError(ProviderReason.provider_error) from last_error

    async def _rate_limit(self) -> None:
        loop = asyncio.get_running_loop()
        now = loop.time()
        elapsed = now - self._last_request_at
        if elapsed < self._request_interval_seconds:
            await asyncio.sleep(self._request_interval_seconds - elapsed)
        self._last_request_at = loop.time()

    def _client_or_default(self) -> httpx.AsyncClient:
        if self._client is not None:
            return _BorrowedAsyncClient(self._client)
        return httpx.AsyncClient(timeout=httpx.Timeout(10, connect=5))

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc not in {SEC_DATA_HOST, SEC_WWW_HOST}:
            raise ProviderUnavailableError(ProviderReason.provider_error)


class _BorrowedAsyncClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, *args: object) -> None:
        return None
