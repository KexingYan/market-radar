# Local Development

Phase 2 local development is Mock-only.

## Boundaries

- Use only `127.0.0.1` or `localhost`.
- Do not bind services to `0.0.0.0`.
- Do not use LAN IP addresses.
- Do not create public tunnels.
- Do not create `.env`.
- Do not connect real market, news, AI, broker, account, or trading APIs.

## Windows PowerShell

From `PROJECT_ROOT`:

```powershell
$env:UV_INSTALL_DIR = "$PWD\.tools\uv"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.runtime\python"
$env:UV_PYTHON_BIN_DIR = "$PWD\.runtime\bin"
$env:UV_CACHE_DIR = "$PWD\.cache\uv"
$env:UV_PROJECT_ENVIRONMENT = "$PWD\.venv"
$env:UV_NO_MODIFY_PATH = "1"

.\.tools\uv\uv.exe --no-config python install 3.12
.\.tools\uv\uv.exe --no-config venv .venv --python 3.12
.\.tools\uv\uv.exe --no-config pip install --python .\.venv -e ".\services\api[dev]"
.\.venv\Scripts\python -m pytest .\services\api
Set-Location .\services\api
..\..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Stop the API with `Ctrl+C`.

## macOS/Linux

From `PROJECT_ROOT`:

```bash
export UV_INSTALL_DIR="$PWD/.tools/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/.runtime/python"
export UV_PYTHON_BIN_DIR="$PWD/.runtime/bin"
export UV_CACHE_DIR="$PWD/.cache/uv"
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
export UV_NO_MODIFY_PATH=1

./.tools/uv/uv --no-config python install 3.12
./.tools/uv/uv --no-config venv .venv --python 3.12
./.tools/uv/uv --no-config pip install --python ./.venv -e "./services/api[dev]"
./.venv/bin/python -m pytest ./services/api
cd services/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Stop the API with `Ctrl+C`.

## Health Check

Open:

```text
http://127.0.0.1:8000/health
```

Expected provider: `mock`.

Expected safety flags:

- `external_network_enabled: false`
- `trading_enabled: false`

Provider status:

```text
http://127.0.0.1:8000/api/v1/providers/status
```

Default Phase 3A response should show quotes and events configured as `mock`, `free_only_mode: true`, `trading_enabled: false`, and `paid_data_enabled: false`.

Report endpoints:

```text
http://127.0.0.1:8000/api/v1/reports/premarket
http://127.0.0.1:8000/api/v1/reports/intraday
http://127.0.0.1:8000/api/v1/reports/close
```

Phase 4A reports are offline and deterministic. They use current Mock quotes and Mock events by default.

Storage endpoints:

```text
http://127.0.0.1:8000/api/v1/storage/status
http://127.0.0.1:8000/api/v1/storage/retention-preview
http://127.0.0.1:8000/api/v1/history/reports
```

The SQLite database is created under project runtime storage. Do not upload it, commit it, or edit it with a text editor.

Alert endpoints:

```text
http://127.0.0.1:8000/api/v1/alert-rules
http://127.0.0.1:8000/api/v1/alerts
http://127.0.0.1:8000/api/v1/alerts/summary
```

Manual alert evaluation:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/alerts/evaluate" -Method POST -ContentType "application/json" -Body '{"symbols":["AAPL"],"include_quotes":true,"include_events":true}'
```

Phase 4C alerts are local in-app records. No APNs, system notifications, email, SMS, webhooks, scheduler, polling loop, or trading action is active.

Job endpoints:

```text
http://127.0.0.1:8000/api/v1/jobs
http://127.0.0.1:8000/api/v1/job-runs
http://127.0.0.1:8000/api/v1/scheduler/status
```

Manual pipeline run:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/jobs/pipeline/run" -Method POST
```

Foreground scheduler:

```powershell
Set-Location .\services\api
..\..\.venv\Scripts\python.exe -m app.scheduler_runner
```

The scheduler is disabled by default. It runs only while this foreground process is open. It does not create a Windows service, scheduled task, startup item, background worker, system notification, or public listener.

## Phase 3A Offline Validation

Run:

```powershell
.\.venv\Scripts\python -m pytest .\services\api
```

The test suite uses fake Moomoo adapters and `httpx.MockTransport` for SEC. It must not connect to OpenD, port `11111`, SEC, Moomoo, news services, AI services, or paid data sources.

SEC live validation is deferred until the user can safely configure `SEC_USER_AGENT`. Do not place a user email address in repository files.

## iOS Simulator

The SwiftUI source uses `http://127.0.0.1:8000` for local Mock API access. If the API cannot be reached, the app falls back to bundled Mock data and displays `Bundled Mock Fallback`.

No Xcode project is included in Phase 2. Add the Swift files under `apps/ios/MarketRadar/MarketRadarApp/` to a local SwiftUI app target manually if you want to compile in Xcode.

A physical iPhone cannot use its own `127.0.0.1` to access the Mac backend. Phase 2 intentionally does not support LAN addresses, tunnels, or public hosts.

## Project-Local Python

- uv is stored in `.tools/uv`.
- uv-managed Python is stored in `.runtime/python`.
- uv cache is stored in `.cache/uv`.
- The virtual environment is stored in `.venv`.
- The system PATH is not modified.
- No global Python package installation is required.

## Common Issues

- Python not found: install Python 3.12+ manually outside this repository, then rerun the local commands.
- API not reachable: confirm Uvicorn is running on `127.0.0.1:8000`.
- Port already in use: stop the existing local process or choose another localhost-only port after updating the iOS local URL.
- iOS shows fallback: this is expected when the API is stopped or unreachable.

Do not work around local issues by using public servers, tunnels, LAN addresses, real providers, or broad ATS exceptions.
