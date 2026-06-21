from app.repositories.sqlite import (
    SQLiteAlertRepository,
    SQLiteAlertRuleRepository,
    SQLiteEventRepository,
    SQLiteJobLockRepository,
    SQLiteJobRepository,
    SQLiteJobRunRepository,
    SQLiteQuoteRepository,
    SQLiteReportRepository,
    SQLiteWatchlistRepository,
    StorageMetrics,
    create_session_factory,
)


def create_memory_repositories():
    session_factory = create_session_factory(":memory:")
    return {
        "quotes": SQLiteQuoteRepository(session_factory),
        "events": SQLiteEventRepository(session_factory),
        "reports": SQLiteReportRepository(session_factory),
        "watchlist": SQLiteWatchlistRepository(session_factory),
        "alert_rules": SQLiteAlertRuleRepository(session_factory),
        "alerts": SQLiteAlertRepository(session_factory),
        "jobs": SQLiteJobRepository(session_factory),
        "job_runs": SQLiteJobRunRepository(session_factory),
        "job_locks": SQLiteJobLockRepository(session_factory),
        "metrics": StorageMetrics(session_factory),
    }
