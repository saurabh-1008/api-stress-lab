from api_stress_lab.assertions import all_assertions_passed, evaluate_assertions
from api_stress_lab.config import AssertionConfig
from api_stress_lab.metrics import Metrics


def _metrics(**overrides: float | int | dict[str, int]) -> Metrics:
    values = {
        "total_requests": 10,
        "successful_requests": 10,
        "failed_requests": 0,
        "timeout_count": 0,
        "request_error_count": 0,
        "status_code_distribution": {"200": 10},
        "error_distribution": {},
        "total_bytes_received": 1000,
        "duration_seconds": 1.0,
        "requests_per_second": 10.0,
        "error_rate_percent": 0.0,
        "min_latency_ms": 10.0,
        "max_latency_ms": 100.0,
        "avg_latency_ms": 50.0,
        "p50_ms": 50.0,
        "p90_ms": 90.0,
        "p95_ms": 95.0,
        "p99_ms": 99.0,
    }
    values.update(overrides)
    return Metrics(**values)


def test_assertions_pass_within_thresholds() -> None:
    results = evaluate_assertions(
        AssertionConfig(expected_status=[200], max_p95_ms=100, max_error_rate_percent=1, min_rps=5),
        _metrics(),
    )

    assert all_assertions_passed(results)


def test_assertions_fail_when_thresholds_are_exceeded() -> None:
    results = evaluate_assertions(
        AssertionConfig(expected_status=[200], max_p95_ms=50, max_error_rate_percent=1, min_rps=20),
        _metrics(failed_requests=1, successful_requests=9, error_rate_percent=10.0, requests_per_second=10.0),
    )

    assert not all_assertions_passed(results)
    assert {result.name for result in results if not result.passed} == {
        "expected_status",
        "max_p95_ms",
        "max_error_rate_percent",
        "min_rps",
    }
