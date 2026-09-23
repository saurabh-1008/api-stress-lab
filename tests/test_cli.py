from pathlib import Path

from typer.testing import CliRunner

from api_stress_lab import cli
from api_stress_lab.runner import RequestResult, RunResult


runner = CliRunner()


def _write_config(path: Path, expected_status: int) -> None:
    path.write_text(
        f"""
target:
  url: "https://example.test"
load:
  total_requests: 1
  concurrency: 1
assertions:
  expected_status: [{expected_status}]
  max_error_rate_percent: 0
report:
  output_dir: "{path.parent.as_posix()}/reports"
  name: "cli-test"
""",
        encoding="utf-8",
    )


def test_cli_creates_reports_and_exits_zero_when_assertions_pass(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, expected_status=200)

    async def fake_run_load_test(config):
        return RunResult(
            duration_seconds=0.1,
            results=[RequestResult(latency_ms=10, status_code=200, ok=True)],
        )

    monkeypatch.setattr(cli, "run_load_test", fake_run_load_test)

    result = runner.invoke(cli.app, ["run", str(config_path)])

    assert result.exit_code == 0
    assert (tmp_path / "reports" / "cli-test" / "report.json").exists()
    assert (tmp_path / "reports" / "cli-test" / "index.html").exists()


def test_cli_exits_non_zero_when_assertions_fail(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, expected_status=201)

    async def fake_run_load_test(config):
        return RunResult(
            duration_seconds=0.1,
            results=[RequestResult(latency_ms=10, status_code=200, ok=True)],
        )

    monkeypatch.setattr(cli, "run_load_test", fake_run_load_test)

    result = runner.invoke(cli.app, ["run", str(config_path)])

    assert result.exit_code == 1


def test_cli_exits_non_zero_for_invalid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("target: {}\n", encoding="utf-8")

    result = runner.invoke(cli.app, ["run", str(config_path)])

    assert result.exit_code == 2
