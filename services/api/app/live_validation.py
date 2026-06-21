import re
from dataclasses import dataclass
from typing import Any

from app.providers.base import ProviderUnavailableError
from app.providers.moomoo_quotes import MoomooQuoteProvider
from app.providers.sec_edgar import SecEdgarEventProvider

SENSITIVE_WORD_RE = re.compile(r"bearer|token|authorization", re.IGNORECASE)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class SecLiveValidationResult:
    user_agent_present: bool
    user_agent_valid: bool
    requested_sec: bool
    request_count: int
    ticker_mapping_found: bool
    aapl_cik_valid: bool
    submissions_json_valid: bool
    parsed_filing_count: int
    converted_market_event: bool
    fallback_used: bool


@dataclass(frozen=True)
class MoomooLiveValidationResult:
    attempted_localhost_11111: bool
    opend_available: bool
    quote_context_opened: bool
    requested_snapshot: bool
    snapshot_returned: bool
    output_real_price: bool
    read_account: bool
    queried_positions_or_assets: bool
    context_closed: bool
    fallback_used: bool


def is_valid_sec_user_agent(value: str | None) -> bool:
    if not value or not value.strip():
        return False
    if len(value) > 200 or "\n" in value or "\r" in value:
        return False
    if SENSITIVE_WORD_RE.search(value):
        return False
    return "/" in value and EMAIL_RE.search(value) is not None


async def run_sec_live_smoke(user_agent: str | None) -> SecLiveValidationResult:
    if not is_valid_sec_user_agent(user_agent):
        return SecLiveValidationResult(
            user_agent_present=bool(user_agent),
            user_agent_valid=False,
            requested_sec=False,
            request_count=0,
            ticker_mapping_found=False,
            aapl_cik_valid=False,
            submissions_json_valid=False,
            parsed_filing_count=0,
            converted_market_event=False,
            fallback_used=True,
        )

    provider = SecEdgarEventProvider(user_agent)
    request_count = 0
    try:
        mapping = await provider.get_ticker_mapping()
        request_count += 1
        aapl = mapping.get("AAPL")
        if not aapl:
            return _sec_result(True, True, True, request_count, False, False, False, 0, False, True)
        cik = str(aapl.get("cik_str", ""))
        submissions = await provider.get_company_submissions(cik)
        request_count += 1
        events = provider.submissions_to_events("AAPL", aapl, submissions, {"8-K", "10-K", "10-Q", "4"})
        return _sec_result(
            True,
            True,
            True,
            request_count,
            True,
            cik.isdigit(),
            isinstance(submissions.get("filings"), dict),
            len(events),
            bool(events),
            False,
        )
    except ProviderUnavailableError:
        return _sec_result(True, True, True, request_count, False, False, False, 0, False, True)


async def run_moomoo_live_smoke(provider: MoomooQuoteProvider | None = None) -> MoomooLiveValidationResult:
    quote_provider = provider or MoomooQuoteProvider()
    try:
        quotes = await quote_provider.get_quotes(["AAPL"])
        return MoomooLiveValidationResult(
            attempted_localhost_11111=True,
            opend_available=bool(quotes),
            quote_context_opened=bool(quotes),
            requested_snapshot=True,
            snapshot_returned=bool(quotes),
            output_real_price=False,
            read_account=False,
            queried_positions_or_assets=False,
            context_closed=True,
            fallback_used=not bool(quotes),
        )
    except (ProviderUnavailableError, PermissionError, OSError, ImportError):
        return MoomooLiveValidationResult(
            attempted_localhost_11111=True,
            opend_available=False,
            quote_context_opened=False,
            requested_snapshot=False,
            snapshot_returned=False,
            output_real_price=False,
            read_account=False,
            queried_positions_or_assets=False,
            context_closed=False,
            fallback_used=True,
        )


def redacted_result_dict(result: Any) -> dict[str, Any]:
    return dict(result.__dict__)


def _sec_result(
    user_agent_present: bool,
    user_agent_valid: bool,
    requested_sec: bool,
    request_count: int,
    ticker_mapping_found: bool,
    aapl_cik_valid: bool,
    submissions_json_valid: bool,
    parsed_filing_count: int,
    converted_market_event: bool,
    fallback_used: bool,
) -> SecLiveValidationResult:
    return SecLiveValidationResult(
        user_agent_present=user_agent_present,
        user_agent_valid=user_agent_valid,
        requested_sec=requested_sec,
        request_count=request_count,
        ticker_mapping_found=ticker_mapping_found,
        aapl_cik_valid=aapl_cik_valid,
        submissions_json_valid=submissions_json_valid,
        parsed_filing_count=parsed_filing_count,
        converted_market_event=converted_market_event,
        fallback_used=fallback_used,
    )
