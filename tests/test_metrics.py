import pytest

from api_stress_lab.metrics import calculate_metrics, percentile
from api_stress_lab.runner import RequestResult, RunResult


def test_percentile_interpolates_values() -> None:
    values = [10.0, 20.0, 30.0, 40.0]

    assert percentile(values, 50) == 25.0
    assert percentile(values, 90) == 37.0
    assert percentile(values, 95) == 38.5
    assert percentile(values, 99) == pytest.approx(39.7)


def test_metrics_separates_transport_failures_from_http_failures() -> None:
    run_result = RunResult(
        duration_seconds=2.0,
        results=[
            RequestResult(latency_ms=10, status_code=200, ok=True, bytes_received=100),
            RequestResult(latency_ms=20, status_code=500, ok=False, bytes_received=50),
            RequestResult(latency_ms=30, status_code=None, ok=False, error_type="timeout"),
            RequestResult(latency_ms=40, status_code=None, ok=False, error_type="request_error"),
        ],
    )

    metrics = calculate_metrics(run_result, expected_status={200})

    assert metrics.total_requests == 4
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 3
    assert metrics.timeout_count == 1
    assert metrics.request_error_count == 1
    assert metrics.error_rate_percent == 75.0
    assert metrics.status_code_distribution == {"200": 1, "500": 1}
    assert metrics.total_bytes_received == 150
