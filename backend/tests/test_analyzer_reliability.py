import asyncio
import pytest
from app.services.static_analysis.analyzer_validator import AnalyzerToolValidator, ToolStatus
from app.services.static_analysis.linter_runners import LinterRunnerManager


def test_analyzer_health_status_check():
    """Verify health status catalog checking for all static analyzers."""
    status_report = AnalyzerToolValidator.get_all_analyzers_status()
    assert "summary" in status_report
    assert "analyzers" in status_report
    assert status_report["summary"]["total_tools"] >= 5

    pylint_status = AnalyzerToolValidator.check_tool_status("pylint")
    assert pylint_status["status"] in (ToolStatus.AVAILABLE.value, ToolStatus.NOT_INSTALLED.value)


def test_missing_analyzer_graceful_fallback_and_warning():
    """Verify python & JS linter runners fall back gracefully when CLI tool is not on PATH."""
    py_code = """
def test_func():
    try:
        x = 1 / 0
    except Exception:
        print("Catching broad exception")
"""
    pylint_res = asyncio.run(LinterRunnerManager.run_pylint("test.py", py_code))
    assert len(pylint_res) >= 1
    assert pylint_res[0]["tool"] == "pylint"

    bandit_res = asyncio.run(LinterRunnerManager.run_bandit("test.py", "eval('1+1')"))
    assert len(bandit_res) >= 1
    assert bandit_res[0]["tool"] == "bandit"

    js_code = "console.log('hello world');"
    eslint_res = asyncio.run(LinterRunnerManager.run_eslint("app.js", js_code))
    assert len(eslint_res) >= 1
    assert eslint_res[0]["tool"] == "eslint"

    java_code = "public class Main { public static void main(String[] args) { System.out.println('test'); } }"
    checkstyle_res = asyncio.run(LinterRunnerManager.run_checkstyle("Main.java", java_code))
    assert len(checkstyle_res) >= 1
    assert checkstyle_res[0]["tool"] == "checkstyle"


def test_partial_analysis_success_multi_language():
    """Verify static analysis engine returns combined findings across Python, JS, and Java."""
    py_findings = asyncio.run(LinterRunnerManager.run_pylint("service.py", "print('debug')"))
    js_findings = asyncio.run(LinterRunnerManager.run_eslint("index.ts", "console.log(123);"))
    java_findings = asyncio.run(LinterRunnerManager.run_checkstyle("Service.java", "System.out.println('logs');"))

    total_findings = py_findings + js_findings + java_findings
    assert len(total_findings) >= 3


if __name__ == "__main__":
    test_analyzer_health_status_check()
    test_missing_analyzer_graceful_fallback_and_warning()
    test_partial_analysis_success_multi_language()
    print("Static analysis reliability & fallback tests PASSED!")
