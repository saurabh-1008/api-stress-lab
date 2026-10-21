# User Guide

## 1. Install

Use Python 3.11 or newer. Before the first PyPI release, install from the repository:

```bash
git clone https://github.com/saurabh-1008/api-stress-lab.git
cd api-stress-lab
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

```bash
python -m pip install -e .
api-stress-lab --help
```

Once a release is published, `python -m pip install api-stress-lab` installs the
CLI without cloning. Create your own YAML file as below; a wheel installation
does not place the repository's examples or docs in your working directory.

## 2. Verify With The Local Demo

From the repository root, start a local API:

```bash
python examples/demo_api.py
```

Leave it running. In a second terminal, activate the same environment and run:

```bash
api-stress-lab run examples/simple-get.yaml
api-stress-lab run examples/post-json.yaml
```

`GET /health` returns 200. `POST /echo` accepts JSON and returns 201.
Stop the demo with Ctrl+C. If port 8000 is busy, stop your own conflicting service
or use its actual URL in a custom test configuration.

## 3. Configure Your Own GET Endpoint

Create `my-api.local.yaml` in your working directory:

```yaml
target:
  url: "http://127.0.0.1:8000/health"
  method: GET
  headers:
    Accept: "application/json"
  query:
    region: "test"
load:
  total_requests: 100
  concurrency: 5
  timeout_seconds: 10
  ramp_up_seconds: 1
assertions:
  expected_status: [200]
  max_p95_ms: 500
  max_error_rate_percent: 0
```

Replace `target.url` with your application endpoint and remove unnecessary query
parameters. Choose an endpoint that can safely receive repeated requests. Then run:

```bash
api-stress-lab run my-api.local.yaml
```

If the console script is unavailable, use
`python -m api_stress_lab run my-api.local.yaml` with the same interpreter used
for installation. Run from the folder containing your config, or pass its full path.

## 4. Configure POST, Headers, And Authentication

For the bundled demo:

```yaml
target:
  url: "http://127.0.0.1:8000/echo"
  method: POST
  headers:
    Accept: "application/json"
  body:
    message: "load-test"
load:
  total_requests: 100
  concurrency: 5
assertions:
  expected_status: [201]
  max_p95_ms: 500
```

Change the URL and body fields to match your application's contract. A mapping
or list is sent as JSON and HTTPX sets the JSON content type. String/scalar bodies
are sent as text; set `Content-Type` explicitly when your API needs another format.
GET and HEAD cannot include `body`. HTTP methods must be uppercase.

For a bearer-protected endpoint, add a header to your private config:

```yaml
target:
  url: "https://your-staging-host.example/api/profile"
  method: GET
  headers:
    Authorization: "Bearer REPLACE_WITH_TEST_TOKEN"
```

API keys work the same way, for example `X-API-Key: "REPLACE_WITH_TEST_KEY"`.
Use disposable staging credentials. Obtain tokens before the test; automatic
login/token refresh is not available. `${API_TOKEN}` is treated as literal text,
not an environment-variable reference. The repo ignores `*.local.yaml` and
`*.local.yml` to keep private configs out of normal Git commits.

POST, PUT, PATCH, and DELETE may change data. Use isolated test data and plan
cleanup in your application. The runner repeats the same body for every request;
it does not generate unique IDs or correlate responses.

## 5. Choose Load Levels

`total_requests` counts requests across all workers. `concurrency` limits active
workers; each sends the next request after the previous request finishes. It is
not a requests-per-second target or a complete simulated user session.

Start with 100 requests and concurrency 5. After checking the result and server
metrics, try 1,000/20, then 10,000/50. Higher levels require measuring generator CPU,
memory, open connections, and network capacity too. Start each experiment with a
new report name or leave `report.name` unset.

One lakh is 100,000 requests and one million is 1,000,000 requests. Those totals
do not imply that many concurrent users. The worker task count is bounded by
concurrency, but individual results are retained in memory. This release has no
validated million-user or million-RPS capacity claim.

Ramp-up staggers worker starts. Short tests may finish before all workers start;
use enough requests to observe sustained load. RPS includes startup, ramp-up,
request execution, and connection shutdown time. There is no steady-state window
or warm-up exclusion yet. `timeout_seconds` applies to HTTPX network phases;
it is not a total wall-clock limit for a request or run.

Test only systems you own or have permission to test. Start on staging and watch
your server metrics while increasing load.

## 6. Read Reports

By default each run writes `reports/<timestamp>/report.json` and `index.html`.
Output paths are relative to the terminal's current working directory, not the
YAML file. To choose a folder:

```yaml
report:
  output_dir: "reports"
  name: "staging-baseline"
```

Reusing a name overwrites the two report files. Omit `name` for timestamped runs.

| Metric | Interpretation |
| --- | --- |
| Successful/failed | Based on configured `expected_status`; transport failures always fail |
| Error rate | Failed requests divided by total requests, as a percentage |
| RPS | Completed attempts divided by measured run duration, including failed attempts |
| p50 | Median latency |
| p95 / p99 | Interpolated latency percentiles; inspect tail latency rather than only averages |
| Timeout count | HTTPX timeout exceptions, including connection/read/write/pool timeouts |
| Request errors | Other HTTPX transport errors, such as connection failures |
| Status distribution | HTTP response counts; transport failures have no HTTP status |
| Bytes received | Sum of buffered response body lengths, not complete wire traffic |

Latency includes failed attempts and receiving the response body. Percentiles
use linear interpolation on sorted measurements. Small samples make p99 noisy.

Reports redact headers, query parameters, request bodies, URL user information,
query strings, and fragments. Endpoint paths remain visible; review reports for
sensitive path identifiers before sharing. Response bodies are not stored in reports.

## 7. Assertions And CI

```yaml
assertions:
  expected_status: [200, 204]
  max_p95_ms: 500
  max_error_rate_percent: 0
  min_rps: 10
```

Thresholds are inclusive. `expected_status` always creates a strict assertion:
every request must match, so one failure causes exit 1 even when
`max_error_rate_percent` would allow a nonzero rate. This release does not support
a tolerated-error-only verdict. `min_rps` checks observed throughput; it does not
control the sending rate.

| Exit code | Meaning |
| --- | --- |
| 0 | All configured assertions passed |
| 1 | One or more assertions failed; reports were written |
| 2 | Invalid config, file problem, or runtime/report-writing error |

Run the same CLI command in CI against a reachable test deployment and retain
`reports/` as a job artifact. CI should fail on a nonzero CLI exit code. Performance
thresholds need comparable machines, datasets, network paths, and test durations.

## Troubleshooting

- Connection refused: start the target and check its hostname/port from the runner machine.
- 401/403: check test credentials, token expiry, and required headers.
- 404: use the exact route and query parameters your application accepts.
- 301/302: configure the final URL; redirects are not followed.
- 429: the application is rate-limiting; inspect its policy and lower concurrency.
- Timeouts: check server health and networking before increasing timeouts.
- Validation error: use a full HTTP(S) URL, positive load counts, supported uppercase
  methods, and a nonempty expected-status list.
- Slow results: compare generator and target resource usage; the report alone cannot
  identify whether your database, application, network, or generator is the bottleneck.

See the [README](../README.md) for the complete field/default reference.
