from app.services.code_quality_engine.calculator import CodeQualityCalculator
from app.services.performance_analyzer.engine import PerformanceAnalyzerEngine
from app.services.security_analyzer.engine import SecurityAnalyzerEngine



def test_code_quality_calculator_metrics():
    """Verify maintainability, complexity, technical debt, and grade calculation."""
    sample_code = """def process_user_data(users):
    results = []
    for user in users:
        if user.is_active:
            if user.has_permission("read"):
                results.append(user.name)
    return results
"""
    computed = CodeQualityCalculator.calculate_metrics(sample_code, "Python")

    assert "maintainability_score" in computed
    assert "technical_debt_hours" in computed
    assert "complexity_score" in computed
    assert "overall_quality_score" in computed
    assert computed["grade"] in ("A+", "A", "B", "C", "F")


def test_security_analyzer_engine_patterns():
    """Verify detection of hardcoded secrets and SQL injection patterns."""
    vulnerable_code = """
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")
"""
    findings = SecurityAnalyzerEngine.scan_file_content("db_service.py", vulnerable_code)
    assert len(findings) >= 1
    severities = [f["severity"] for f in findings]
    assert "HIGH" in severities or "CRITICAL" in severities



def test_performance_analyzer_engine_patterns():
    """Verify detection of nested loops and repeated DB query bottlenecks."""
    perf_code = """
for i in range(100):
    for j in range(100):
        db.query("SELECT * FROM items")
"""
    findings = PerformanceAnalyzerEngine.analyze_file_performance("order_service.py", perf_code)
    assert len(findings) >= 1



if __name__ == "__main__":
    test_code_quality_calculator_metrics()
    test_security_analyzer_engine_patterns()
    test_performance_analyzer_engine_patterns()
    print("Analysis engines unit tests PASSED!")
