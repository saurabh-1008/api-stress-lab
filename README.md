# API Stress Lab

Run configurable HTTP load tests from your terminal and get latency percentiles,
throughput, failure breakdowns, and shareable JSON/HTML reports.

Python 3.11+ | MIT license | Early-stage, single-machine CLI

## Install

From a checkout:

```bash
git clone https://github.com/saurabh-1008/api-stress-lab.git
cd api-stress-lab
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
```

After the first PyPI release, users can install with `python -m pip install api-stress-lab`.

## Try It Locally

Start the included demo API in one terminal:

```bash
python examples/demo_api.py
```

In another terminal with the same virtual environment active:

```bash
api-stress-lab run examples/simple-get.yaml
api-stress-lab run examples/post-json.yaml
```

You can also use `python -m api_stress_lab run examples/simple-get.yaml`.
The demo requires only Python's standard library.

## Test Your API

Create `my-api.local.yaml`:

```yaml
target:
  url: "http://127.0.0.1:8000/health"
  method: GET
load:
  total_requests: 1000
  concurrency: 20
  timeout_seconds: 10
  ramp_up_seconds: 2
assertions:
  expected_status: [200]
  max_p95_ms: 500
  max_error_rate_percent: 0
```

Change the URL to your own endpoint, then run:

```bash
api-stress-lab run my-api.local.yaml
```

Run tests only against systems you own or have permission to test.

## Configuration

| Field | Default | Meaning |
| --- | --- | --- |
| `target.url` | Required | Absolute HTTP or HTTPS endpoint |
| `target.method` | `GET` | GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| `target.headers` | `{}` | Request headers, including static auth tokens |
| `target.query` | `{}` | Query parameters |
| `target.body` | None | Object/list sent as JSON; other values as raw text; disallowed for GET/HEAD |
| `load.total_requests` | `100` | Positive number of requests across all workers |
| `load.concurrency` | `10` | Positive maximum worker count |
| `load.timeout_seconds` | `30` | Positive HTTPX timeout for each network phase, not a whole-test deadline |
| `load.ramp_up_seconds` | `0` | Nonnegative period over which workers start |
| `assertions.expected_status` | `[200]` | Nonempty list of successful status codes; every request must match |
| `assertions.max_p95_ms` | Disabled | Maximum inclusive p95 latency |
| `assertions.max_error_rate_percent` | Disabled | Maximum inclusive error percentage |
| `assertions.min_rps` | Disabled | Minimum inclusive observed requests/second |
| `report.output_dir` | `reports` | Output directory relative to the current working directory |
| `report.name` | Timestamp | Run subfolder; a fixed name overwrites that run's report files |

Headers and config values are literal; environment-variable expansion is not
implemented. Keep tokens in ignored `*.local.yaml` files.

## Reports And Exit Codes

Open `reports/<run-name>/index.html` in a browser, or read `report.json` for
automation. Reports include request totals, status codes, timeout and connection
error counts, bytes received, observed RPS, min/average/max latency, p50/p90/p95/p99,
and assertion results. Request headers, query parameters, bodies, URL credentials,
and URL query strings are omitted from reports. Review endpoint paths before sharing.

Exit codes: `0` means all assertions passed; `1` means an assertion failed;
`2` means configuration or execution failed. The expected-status assertion is
strict: any failed request makes the run fail, even if an error-rate threshold
would otherwise allow it.

## Current Limits

This version tests one endpoint per run using a fixed request count and async
workers. It does not provide a fixed arrival-rate scheduler, distributed workers,
duration-based runs, scenario chaining, automatic login, or server-side diagnostics.
Responses are not retried and redirects are not followed. Results are retained in
memory for percentile calculation, so memory grows with request count. Throughput
depends on the generator machine and network as well as the target API.

## Guides

- [User guide: configure and test your application](https://github.com/saurabh-1008/api-stress-lab/blob/main/docs/USER_GUIDE.md)
- [Contributing](https://github.com/saurabh-1008/api-stress-lab/blob/main/CONTRIBUTING.md)

The maintained CLI lives in `api_stress_lab/`.
