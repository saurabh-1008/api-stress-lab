from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from rich.console import Console
from rich.table import Table

from api_stress_lab.assertions import AssertionResult
from api_stress_lab.config import LabConfig
from api_stress_lab.metrics import Metrics


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API Stress Lab Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f8fb; }
    main { max-width: 1040px; margin: 0 auto; }
    h1, h2 { color: #101828; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    .metric { background: white; border: 1px solid #d9deea; border-radius: 8px; padding: 16px; }
    .metric strong { display: block; font-size: 24px; margin-top: 8px; }
    table { width: 100%; border-collapse: collapse; background: white; margin: 16px 0; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #d9deea; }
    .pass { color: #047857; font-weight: bold; }
    .fail { color: #b42318; font-weight: bold; }
    code { background: #eef2f7; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <main>
    <h1>API Stress Lab Report</h1>
    <p><strong>Target:</strong> <code>{{ config.target.method }} {{ config.target.url }}</code></p>
    <section class="summary">
      <div class="metric">Total Requests<strong>{{ metrics.total_requests }}</strong></div>
      <div class="metric">Success Rate<strong>{{ success_rate }}%</strong></div>
      <div class="metric">RPS<strong>{{ "%.2f"|format(metrics.requests_per_second) }}</strong></div>
      <div class="metric">P95 Latency<strong>{{ "%.2f"|format(metrics.p95_ms) }}ms</strong></div>
      <div class="metric">P99 Latency<strong>{{ "%.2f"|format(metrics.p99_ms) }}ms</strong></div>
      <div class="metric">Duration<strong>{{ "%.2f"|format(metrics.duration_seconds) }}s</strong></div>
    </section>

    <h2>Assertions</h2>
    <table>
      <thead><tr><th>Name</th><th>Status</th><th>Message</th></tr></thead>
      <tbody>
      {% for assertion in assertions %}
        <tr>
          <td>{{ assertion.name }}</td>
          <td class="{{ 'pass' if assertion.passed else 'fail' }}">{{ 'PASS' if assertion.passed else 'FAIL' }}</td>
          <td>{{ assertion.message }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>

    <h2>Latency</h2>
    <table>
      <tbody>
        <tr><th>Min</th><td>{{ "%.2f"|format(metrics.min_latency_ms) }}ms</td></tr>
        <tr><th>Average</th><td>{{ "%.2f"|format(metrics.avg_latency_ms) }}ms</td></tr>
        <tr><th>P50</th><td>{{ "%.2f"|format(metrics.p50_ms) }}ms</td></tr>
        <tr><th>P90</th><td>{{ "%.2f"|format(metrics.p90_ms) }}ms</td></tr>
        <tr><th>P95</th><td>{{ "%.2f"|format(metrics.p95_ms) }}ms</td></tr>
        <tr><th>P99</th><td>{{ "%.2f"|format(metrics.p99_ms) }}ms</td></tr>
        <tr><th>Max</th><td>{{ "%.2f"|format(metrics.max_latency_ms) }}ms</td></tr>
      </tbody>
    </table>

    <h2>Failures</h2>
    <table>
      <tbody>
        <tr><th>Failed Requests</th><td>{{ metrics.failed_requests }}</td></tr>
        <tr><th>Error Rate</th><td>{{ "%.2f"|format(metrics.error_rate_percent) }}%</td></tr>
        <tr><th>Timeouts</th><td>{{ metrics.timeout_count }}</td></tr>
        <tr><th>Request Errors</th><td>{{ metrics.request_error_count }}</td></tr>
      </tbody>
    </table>

    <h2>Status Codes</h2>
    <pre>{{ status_codes }}</pre>
  </main>
</body>
</html>
"""


def print_summary(metrics: Metrics, assertions: list[AssertionResult]) -> None:
    console = Console(safe_box=True)
    console.rule("[bold]API Stress Lab[/bold]")

    metrics_table = Table(title="Run Summary", safe_box=True)
    metrics_table.add_column("Metric")
    metrics_table.add_column("Value", justify="right")
    rows = {
        "Total requests": str(metrics.total_requests),
        "Successful requests": str(metrics.successful_requests),
        "Failed requests": str(metrics.failed_requests),
        "Duration": f"{metrics.duration_seconds:.2f}s",
        "Requests/sec": f"{metrics.requests_per_second:.2f}",
        "Error rate": f"{metrics.error_rate_percent:.2f}%",
        "P50": f"{metrics.p50_ms:.2f}ms",
        "P95": f"{metrics.p95_ms:.2f}ms",
        "P99": f"{metrics.p99_ms:.2f}ms",
    }
    for name, value in rows.items():
        metrics_table.add_row(name, value)
    console.print(metrics_table)

    assertion_table = Table(title="Assertions", safe_box=True)
    assertion_table.add_column("Name")
    assertion_table.add_column("Status")
    assertion_table.add_column("Message")
    for assertion in assertions:
        status = "[green]PASS[/green]" if assertion.passed else "[red]FAIL[/red]"
        assertion_table.add_row(assertion.name, status, assertion.message)
    console.print(assertion_table)


def write_reports(
    config: LabConfig,
    metrics: Metrics,
    assertions: list[AssertionResult],
) -> tuple[Path, Path]:
    report_dir = _report_dir(config)
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "report.json"
    html_path = report_dir / "index.html"

    payload = {
        "config": config.model_dump(),
        "metrics": asdict(metrics),
        "assertions": [asdict(assertion) for assertion in assertions],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    success_rate = 100 - metrics.error_rate_percent
    html = Template(HTML_TEMPLATE).render(
        config=config,
        metrics=metrics,
        assertions=assertions,
        success_rate=f"{success_rate:.2f}",
        status_codes=json.dumps(metrics.status_code_distribution, indent=2),
    )
    html_path.write_text(html, encoding="utf-8")
    return json_path, html_path


def _report_dir(config: LabConfig) -> Path:
    base = Path(config.report.output_dir)
    name = config.report.name or datetime.now().strftime("%Y%m%d-%H%M%S")
    return base / name
