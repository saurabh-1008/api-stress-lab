import json

from api_stress_lab.assertions import evaluate_assertions
from api_stress_lab.config import LabConfig
from api_stress_lab.metrics import calculate_metrics
from api_stress_lab.reporter import write_reports
from api_stress_lab.runner import RequestResult, RunResult


def test_reports_redact_request_data_and_escape_html(tmp_path):
    config = LabConfig.model_validate({
        "target": {
            "url": "https://username:url-password@example.test/<script>alert(1)</script>?token=url-token#private",
            "method": "POST",
            "headers": {"Authorization": "Bearer header-token"},
            "query": {"api_key": "query-token"},
            "body": {"password": "body-secret"},
        },
        "report": {"output_dir": str(tmp_path)},
    })
    metrics = calculate_metrics(
        RunResult([RequestResult(10, 200, True)], 0.1), {200}
    )
    json_path, html_path = write_reports(
        config, metrics, evaluate_assertions(config.assertions, metrics)
    )
    report_json = json_path.read_text(encoding="utf-8")
    report_html = html_path.read_text(encoding="utf-8")
    for secret in ["username", "url-password", "url-token", "header-token", "query-token", "body-secret", "#private"]:
        assert secret not in report_json
        assert secret not in report_html
    assert "<script>" not in report_html
    assert "&lt;script&gt;" in report_html
    assert json.loads(report_json)["metrics"]["total_requests"] == 1
    assert config.target.headers["Authorization"] == "Bearer header-token"
