# Foreground Scheduler

The Phase 5A scheduler is a foreground-only local process.

Run it from `services/api`:

```powershell
..\..\.venv\Scripts\python.exe -m app.scheduler_runner
```

It does not:

- register a Windows service
- create a scheduled task
- create a startup item
- run hidden in the background
- listen on a network port
- open a public or LAN service
- send system notifications
- connect to OpenD
- request SEC or live market data

Default configuration:

```text
SCHEDULER_ENABLED=false
```

When no jobs are enabled, the scheduler prints `No scheduled jobs are enabled.` and exits safely.

When jobs are enabled, the scheduler checks SQLite every 5 seconds for due jobs and runs at most one job at a time. Closing the terminal stops the scheduler.

The status file, if written, is limited to:

```text
PROJECT_ROOT/.runtime/scheduler/status.json
```

The status file is not a lock and does not contain secrets, paths, accounts, or environment variables. SQLite job locks remain authoritative.

