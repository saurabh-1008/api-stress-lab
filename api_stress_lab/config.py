from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class TargetConfig(BaseModel):
    url: str
    method: HttpMethod = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    query: dict[str, Any] = Field(default_factory=dict)
    body: Any | None = None

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("target.url is required")
        return value


class LoadConfig(BaseModel):
    total_requests: int = 100
    concurrency: int = 10
    timeout_seconds: float = 30.0
    ramp_up_seconds: float = 0.0

    @field_validator("total_requests", "concurrency")
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def positive_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("ramp_up_seconds")
    @classmethod
    def non_negative_ramp(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be greater than or equal to 0")
        return value


class AssertionConfig(BaseModel):
    expected_status: list[int] = Field(default_factory=lambda: [200])
    max_p95_ms: float | None = None
    max_error_rate_percent: float | None = None
    min_rps: float | None = None

    @field_validator("expected_status")
    @classmethod
    def expected_status_must_not_be_empty(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("assertions.expected_status must not be empty")
        return value

    @field_validator("max_p95_ms", "max_error_rate_percent", "min_rps")
    @classmethod
    def thresholds_must_be_non_negative(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("thresholds must be greater than or equal to 0")
        return value


class ReportConfig(BaseModel):
    output_dir: str = "reports"
    name: str | None = None


class LabConfig(BaseModel):
    target: TargetConfig
    load: LoadConfig = Field(default_factory=LoadConfig)
    assertions: AssertionConfig = Field(default_factory=AssertionConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)

    @model_validator(mode="after")
    def body_only_for_supported_methods(self) -> "LabConfig":
        if self.target.body is not None and self.target.method in {"GET", "HEAD"}:
            raise ValueError("target.body is not supported for GET or HEAD requests")
        return self


def load_config(path: str | Path) -> LabConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    if not isinstance(raw, dict):
        raise ValueError("config file must contain a YAML object")
    return LabConfig.model_validate(raw)
