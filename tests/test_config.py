from pathlib import Path

import pytest
from pydantic import ValidationError

from api_stress_lab.config import LabConfig, load_config


def test_load_config_accepts_valid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
target:
  url: "https://example.com"
  method: "GET"
load:
  total_requests: 5
  concurrency: 2
assertions:
  expected_status: [200]
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.target.url == "https://example.com"
    assert config.load.total_requests == 5
    assert config.assertions.expected_status == [200]


def test_config_rejects_missing_target_url() -> None:
    with pytest.raises(ValidationError):
        LabConfig.model_validate({"target": {"method": "GET"}})


def test_config_rejects_invalid_method() -> None:
    with pytest.raises(ValidationError):
        LabConfig.model_validate({"target": {"url": "https://example.com", "method": "BREW"}})


def test_config_rejects_negative_concurrency() -> None:
    with pytest.raises(ValidationError):
        LabConfig.model_validate(
            {
                "target": {"url": "https://example.com"},
                "load": {"concurrency": -1},
            }
        )


def test_config_rejects_empty_expected_status() -> None:
    with pytest.raises(ValidationError):
        LabConfig.model_validate(
            {
                "target": {"url": "https://example.com"},
                "assertions": {"expected_status": []},
            }
        )
