from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from api_stress_lab.assertions import all_assertions_passed, evaluate_assertions
from api_stress_lab.config import load_config
from api_stress_lab.metrics import calculate_metrics
from api_stress_lab.reporter import print_summary, write_reports
from api_stress_lab.runner import run_load_test


app = typer.Typer(help="Config-driven API reliability and load testing.")
console = Console()


@app.callback()
def callback() -> None:
    """API Stress Lab command line interface."""


@app.command()
def run(config_path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Run an API stress test from a YAML config file."""
    try:
        config = load_config(config_path)
        run_result = asyncio.run(run_load_test(config))
        metrics = calculate_metrics(run_result, set(config.assertions.expected_status))
        assertion_results = evaluate_assertions(config.assertions, metrics)
        print_summary(metrics, assertion_results)
        json_path, html_path = write_reports(config, metrics, assertion_results)
        console.print(f"JSON report: {json_path}")
        console.print(f"HTML report: {html_path}")
    except Exception as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=2) from error

    if not all_assertions_passed(assertion_results):
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
