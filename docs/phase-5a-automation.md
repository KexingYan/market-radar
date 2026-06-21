# Phase 5A: Local Job Orchestration and Foreground Scheduler

Phase 5A connects the existing Mock provider, archive service, report engine, and alert engine into a local automation pipeline.

## Completed Scope

- Job models.
- Job run history.
- SQLite job locks.
- Static job registry.
- Manual job execution.
- Manual full pipeline execution.
- Foreground scheduler module.
- Scheduler status endpoint.
- Job and job-run APIs.
- iOS Automation source.
- Offline tests.

## Full Pipeline

The fixed pipeline runs:

```text
collect_quotes
-> collect_events
-> archive_market_data
-> generate_intraday_report
-> evaluate_alerts
```

It uses Mock/local data by default and stores only summary counts in job run records.

## Boundaries

- Scheduler is disabled by default.
- Scheduler runs only as a foreground process.
- No Windows service is registered.
- No scheduled task is created.
- No startup item is created.
- No background resident worker is installed.
- No system notification is sent.
- No APNs, Firebase, email, SMS, webhook, or chat integration exists.
- No OpenD, SEC live request, paid provider, AI, or trading feature is used.

