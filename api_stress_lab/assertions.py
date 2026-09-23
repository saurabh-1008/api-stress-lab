from __future__ import annotations

from dataclasses import dataclass

from api_stress_lab.config import AssertionConfig
from api_stress_lab.metrics import Metrics


@dataclass(frozen=True)
class AssertionResult:
    name: str
    passed: bool
    message: str


def evaluate_assertions(config: AssertionConfig, metrics: Metrics) -> list[AssertionResult]:
    results = [
        AssertionResult(
            name="expected_status",
            passed=metrics.failed_requests == 0,
            message=(
                f"{metrics.successful_requests}/{metrics.total_requests} requests matched "
                f"expected status codes {config.expected_status}"
            ),
        )
    ]

    if config.max_p95_ms is not None:
        results.append(
            AssertionResult(
                name="max_p95_ms",
                passed=metrics.p95_ms <= config.max_p95_ms,
                message=f"p95 latency {metrics.p95_ms:.2f}ms <= {config.max_p95_ms:.2f}ms",
            )
        )

    if config.max_error_rate_percent is not None:
        results.append(
            AssertionResult(
                name="max_error_rate_percent",
                passed=metrics.error_rate_percent <= config.max_error_rate_percent,
                message=(
                    f"error rate {metrics.error_rate_percent:.2f}% <= "
                    f"{config.max_error_rate_percent:.2f}%"
                ),
            )
        )

    if config.min_rps is not None:
        results.append(
            AssertionResult(
                name="min_rps",
                passed=metrics.requests_per_second >= config.min_rps,
                message=f"RPS {metrics.requests_per_second:.2f} >= {config.min_rps:.2f}",
            )
        )

    return results


def all_assertions_passed(results: list[AssertionResult]) -> bool:
    return all(result.passed for result in results)
