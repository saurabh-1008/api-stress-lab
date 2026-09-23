# API Stress Lab

API Stress Lab is a Python async CLI tool for testing API reliability, scalability, latency, throughput, and failure behavior from a simple YAML config.

The MVP is intentionally local-first: define a target, choose request volume and concurrency, run the test, and get terminal, JSON, and HTML reports.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
api-stress-lab run examples/simple-get.yaml
```

Every run prints a terminal summary and writes:

```text
reports/<run-name>/report.json
reports/<run-name>/index.html
```

## Config Example

```yaml
target:
  url: "http://127.0.0.1:8000/login"
  method: "GET"
  query:
    username: "saurabh"
    password: "123456"

load:
  total_requests: 1000
  concurrency: 50
  timeout_seconds: 30
  ramp_up_seconds: 0

assertions:
  expected_status: [200]
  max_p95_ms: 500
  max_error_rate_percent: 1
  min_rps: 100
```

## Config Fields

`target` describes the HTTP request:

- `url`: full endpoint URL.
- `method`: one of `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, or `OPTIONS`.
- `headers`: optional request headers.
- `query`: optional query parameters.
- `body`: optional JSON body for non-GET requests.

`load` controls traffic:

- `total_requests`: total requests to send.
- `concurrency`: number of async workers.
- `timeout_seconds`: per-request timeout.
- `ramp_up_seconds`: gradually starts workers across this period.

`assertions` controls pass/fail behavior:

- `expected_status`: status codes treated as successful.
- `max_p95_ms`: fail when p95 latency is above this value.
- `max_error_rate_percent`: fail when failed requests exceed this percentage.
- `min_rps`: fail when throughput is below this value.

`report` controls output:

- `output_dir`: parent folder for generated reports.
- `name`: optional fixed report folder name.

## Demo API

The existing `auth_folder` FastAPI app can be used as a local target:

```bash
cd auth_folder
uvicorn main:app --reload
```

Then run:

```bash
api-stress-lab run examples/login.yaml
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

Generated reports, local databases, caches, and virtual environments are ignored by git.

## Roadmap

- Multi-step API scenarios.
- Authentication helpers for bearer tokens and login flows.
- CSV export and richer HTML charts.
- CI/CD examples for GitHub Actions.
- Historical report comparison.

## Contributing

Keep changes focused, add or update tests for user-facing behavior, and document new config fields in this README.
