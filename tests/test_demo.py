import json
import runpy
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from api_stress_lab.cli import app


@pytest.mark.parametrize("example", ["simple-get.yaml", "post-json.yaml", "failing-assertion.yaml"])
def test_examples_against_real_demo(example, tmp_path):
    root = Path(__file__).resolve().parents[1]
    handler = runpy.run_path(str(root / "examples" / "demo_api.py"))["Handler"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = yaml.safe_load((root / "examples" / example).read_text(encoding="utf-8"))
        route = "/echo" if example == "post-json.yaml" else "/health"
        config["target"]["url"] = f"http://127.0.0.1:{server.server_port}{route}"
        config["report"] = {"output_dir": str(tmp_path / "reports"), "name": "demo"}
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        result = CliRunner().invoke(app, ["run", str(path)])
        expected_exit = 1 if example == "failing-assertion.yaml" else 0
        assert result.exit_code == expected_exit, result.output
        payload = json.loads((tmp_path / "reports/demo/report.json").read_text(encoding="utf-8"))
        assert payload["metrics"]["total_requests"] == config["load"]["total_requests"]
        assert (tmp_path / "reports/demo/index.html").exists()
        assert "JSON report:" in result.output
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
