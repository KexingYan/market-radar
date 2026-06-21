import asyncio

from app.jobs.scheduler import ForegroundScheduler
from app.jobs.service import due_enabled_jobs
from app.providers.registry import provider_status


async def main() -> None:
    status = provider_status()
    jobs = await due_enabled_jobs()
    print("Market Radar foreground scheduler")
    print("mode=foreground_only")
    print(f"enabled_jobs={len(jobs)}")
    print(f"quote_provider={status.quotes.active}")
    print(f"event_provider={status.events.active}")
    print("trading_enabled=false")
    if not jobs:
        print("No scheduled jobs are enabled.")
        return
    scheduler = ForegroundScheduler(check_interval_seconds=5)
    try:
        await scheduler.run()
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())

