from app.repositories.sqlite import (
    DEFAULT_DB_PATH,
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

session_factory = create_session_factory(DEFAULT_DB_PATH)
quote_repository = SQLiteQuoteRepository(session_factory)
event_repository = SQLiteEventRepository(session_factory)
report_repository = SQLiteReportRepository(session_factory)
watchlist_repository = SQLiteWatchlistRepository(session_factory)
alert_rule_repository = SQLiteAlertRuleRepository(session_factory)
alert_repository = SQLiteAlertRepository(session_factory)
job_repository = SQLiteJobRepository(session_factory)
job_run_repository = SQLiteJobRunRepository(session_factory)
job_lock_repository = SQLiteJobLockRepository(session_factory)
storage_metrics = StorageMetrics(session_factory)

__all__ = [
    "alert_repository",
    "alert_rule_repository",
    "event_repository",
    "job_lock_repository",
    "job_repository",
    "job_run_repository",
    "quote_repository",
    "report_repository",
    "storage_metrics",
    "watchlist_repository",
]
