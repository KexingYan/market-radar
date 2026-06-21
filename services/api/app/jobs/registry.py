from collections.abc import Awaitable, Callable

from app.jobs.models import JobType
from app.jobs.tasks import (
    TaskContext,
    archive_market_data,
    collect_events,
    collect_quotes,
    evaluate_alerts,
    generate_close_report,
    generate_intraday_report,
    generate_premarket_report,
)

JobHandler = Callable[[TaskContext], Awaitable[dict[str, object]]]

JOB_HANDLERS: dict[JobType, JobHandler] = {
    JobType.COLLECT_QUOTES: collect_quotes,
    JobType.COLLECT_EVENTS: collect_events,
    JobType.ARCHIVE_MARKET_DATA: archive_market_data,
    JobType.GENERATE_PREMARKET_REPORT: generate_premarket_report,
    JobType.GENERATE_INTRADAY_REPORT: generate_intraday_report,
    JobType.GENERATE_CLOSE_REPORT: generate_close_report,
    JobType.EVALUATE_ALERTS: evaluate_alerts,
}

