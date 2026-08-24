import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.code_quality_engine.calculator import CodeQualityCalculator
from app.services.doc_generator.generator import AIDocGeneratorEngine
from app.services.performance_analyzer.engine import PerformanceAnalyzerEngine
from app.services.reports.report_generator import ProfessionalReportGeneratorEngine
from app.services.test_generator.generator import AITestGeneratorEngine


def run_tests():
    print("--- Running Performance Analyzer Tests ---")
    # Test 1: Nested Loops
    code1 = """
def process_matrix(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            print(matrix[i][j])
    """
    res1 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code1)
    assert any(f["category"] == "Nested Loops" for f in res1), "Nested Loops detection failed"
    print("PASS: Nested Loops Detection")

    # Test 2: N+1 DB Queries
    code2 = """
def update_users(users, db):
    for user in users:
        result = db.execute(select(User).where(User.id == user.id))
    """
    res2 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code2)
    assert any(f["category"] == "Repeated Database Queries" for f in res2), "N+1 DB Query detection failed"
    print("PASS: Repeated DB Queries Detection")

    # Test 3: Blocking Operations
    code3 = """
async def fetch_data_async(url):
    import time
    time.sleep(5)
    return True
    """
    res3 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code3)
    assert any(f["category"] == "Blocking Operations" for f in res3), "Blocking Operations detection failed"
    print("PASS: Blocking Operations Detection")

    # Test 4: Large Memory Allocations
    code4 = """
def read_all_logs(filepath):
    data = open(filepath).read()
    return data
    """
    res4 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code4)
    assert any(f["category"] == "Large Memory Allocations" for f in res4), "Large Memory Allocations detection failed"
    print("PASS: Large Memory Allocations Detection")

    # Test 5: Repeated API Calls
    code5 = """
def fetch_all(urls):
    for url in urls:
        res = requests.get(url)
    """
    res5 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code5)
    assert any(f["category"] == "Repeated API Calls" for f in res5), "Repeated API Calls detection failed"
    print("PASS: Repeated API Calls Detection")

    # Test 6: Expensive Regex
    code6 = """
import re
def parse_logs(lines):
    for line in lines:
        pattern = re.compile(r'(a+)+')
        match = pattern.search(line)
    """
    res6 = PerformanceAnalyzerEngine.analyze_file_performance("test.py", code6)
    assert any(f["category"] == "Expensive Regex" for f in res6), "Expensive Regex detection failed"
    print("PASS: Expensive Regex Detection")

    print("\n--- Running Code Quality Engine Tests ---")
    clean_code = '''
"""
Module docstring.
"""
def clean_function(x: int) -> int:
    """Computes square."""
    return x * x
'''
    q_metrics = CodeQualityCalculator.calculate_metrics(
        code_content=clean_code,
        language="Python",
        security_findings_count=0,
        performance_findings_count=0,
        code_smells_count=0
    )
    assert q_metrics["maintainability_score"] >= 80, f"Expected high maintainability, got {q_metrics['maintainability_score']}"
    assert q_metrics["technical_debt_hours"] == 0.0, f"Expected 0 tech debt, got {q_metrics['technical_debt_hours']}"
    assert q_metrics["doc_coverage_percentage"] == 100.0, f"Expected 100% doc coverage, got {q_metrics['doc_coverage_percentage']}"
    print(f"PASS: Clean Code Quality Metrics (Score: {q_metrics['overall_quality_score']}, Grade: {q_metrics['grade']})")

    print("\n--- Running AI Test Generator Tests ---")
    py_test = AITestGeneratorEngine.generate_test_suite("user_service.py", clean_code, "pytest", "comprehensive")
    assert py_test["test_name"] == "test_user_service.py"
    assert "import pytest" in py_test["generated_code"]
    print("PASS: pytest Comprehensive Test Suite Generation")

    junit_test = AITestGeneratorEngine.generate_test_suite("UserService.java", "public class UserService {}", "junit", "comprehensive")
    assert "UserserviceTest.java" in junit_test["test_name"] or "UserServiceTest.java" in junit_test["test_name"]
    assert "import org.junit.jupiter.api.Test;" in junit_test["generated_code"]
    print("PASS: JUnit 5 Test Suite Generation")

    jest_test = AITestGeneratorEngine.generate_test_suite("userService.ts", "function getUser() {}", "jest", "comprehensive")
    assert jest_test["test_name"] == "userService.test.ts"
    assert "describe(" in jest_test["generated_code"]
    print("PASS: Jest Test Suite Generation")

    print("\n--- Running AI Documentation Generator Tests ---")
    py_doc = AIDocGeneratorEngine.generate_documentation("user_service.py", clean_code, "docstring")
    assert "Docstrings for user_service.py" in py_doc["doc_title"]
    print("PASS: Python Docstring Generation")

    java_doc = AIDocGeneratorEngine.generate_documentation("UserService.java", "public void process() {}", "javadoc")
    assert "/**" in java_doc["content"]
    print("PASS: JavaDoc Generation")

    readme_doc = AIDocGeneratorEngine.generate_documentation("main.py", clean_code, "readme")
    assert "# Main Component Documentation" in readme_doc["content"]
    print("PASS: README Update Generation")

    api_doc = AIDocGeneratorEngine.generate_documentation("api.py", "@router.get('/api/users')", "api_doc")
    assert "API Reference Specifications" in api_doc["content"]
    print("PASS: API Documentation Generation")

    comments_doc = AIDocGeneratorEngine.generate_documentation("logic.py", "def check(x):\n if x: pass", "missing_comments")
    assert "Branch condition" in comments_doc["content"] or "Entrypoint" in comments_doc["content"]
    print("PASS: Missing Inline Comments Generation")

    func_spec_doc = AIDocGeneratorEngine.generate_documentation("service.py", "def process(): pass", "function_description")
    assert "Functional Specifications" in func_spec_doc["content"]
    print("PASS: Function Descriptions Generation")

    examples_doc = AIDocGeneratorEngine.generate_documentation("client.py", "def run(): pass", "usage_examples")
    assert "Executable Usage Examples" in examples_doc["content"]
    print("PASS: Usage Examples Generation")

    print("\n--- Running Professional Review Report Generator Tests ---")
    md_report, title, meta = ProfessionalReportGeneratorEngine.generate_report("acme/service", 1, "MARKDOWN")
    assert "# Executive Code Review Report" in md_report
    assert "1. Executive Summary" in md_report
    assert "2. Quality Score & Health Metrics" in md_report
    print("PASS: Markdown Executive Review Report Generation")

    html_report, _, _ = ProfessionalReportGeneratorEngine.generate_report("acme/service", 1, "HTML")
    assert "<!DOCTYPE html>" in html_report
    print("PASS: HTML Executive Review Report Generation")

    pdf_report, _, _ = ProfessionalReportGeneratorEngine.generate_report("acme/service", 1, "PDF")
    assert "<!DOCTYPE html>" in pdf_report or "%PDF" in pdf_report
    print("PASS: PDF Executive Review Report Generation")

    json_report, _, _ = ProfessionalReportGeneratorEngine.generate_report("acme/service", 1, "JSON")
    assert '"repository": "acme/service"' in json_report
    print("PASS: JSON Executive Review Report Generation")

    print("\n--- Running Extended QA & Integration Suite ---")
    import tests.test_auth_and_oauth as t_auth
    t_auth.test_jwt_token_generation_and_decoding()
    t_auth.test_token_encryption_and_decryption()
    t_auth.test_invalid_jwt_token_decoding()
    t_auth.test_mocked_github_oauth_callback_flow()
    print("PASS: Authentication & OAuth Flow Tests")

    import tests.test_repository_management as t_repo
    t_repo.test_repository_response_schema()
    t_repo.test_repository_settings_defaults()
    t_repo.test_repository_pagination_mock()
    print("PASS: Repository Management & Pagination Tests")

    import tests.test_github_webhooks as t_wh
    t_wh.test_valid_github_webhook_hmac_signature()
    t_wh.test_invalid_github_webhook_hmac_signature()
    t_wh.test_webhook_event_parsing_opened()
    print("PASS: GitHub Webhooks Signature & Event Ingestion Tests")

    import tests.test_pull_request_analysis as t_pr
    t_pr.test_language_detection_from_filenames()
    t_pr.test_parse_unified_diff_hunks_and_lines()
    t_pr.test_parse_unified_diff_empty_or_none()
    print("PASS: Pull Request Unified Diff Parsing & Language Detection Tests")

    import tests.test_analysis_engines as t_eng
    t_eng.test_code_quality_calculator_metrics()
    t_eng.test_security_analyzer_engine_patterns()
    t_eng.test_performance_analyzer_engine_patterns()
    print("PASS: Analysis Engines (Static, SAST, Perf, Quality) Tests")

    import tests.test_review_finalization as t_fin
    t_fin.test_review_summary_markdown_payload_formatting()
    t_fin.test_diff_line_mapping_safe_verification()
    print("PASS: Review Finalization & Line Mapping Tests")

    import tests.test_repository_settings as t_sett
    t_sett.test_default_repository_settings_schema()
    t_sett.test_resolve_effective_settings_with_custom_overrides()
    t_sett.test_file_exclusion_filtering_directories()
    t_sett.test_file_exclusion_filtering_filenames()
    t_sett.test_file_exclusion_filtering_unsupported_extensions()
    t_sett.test_repository_settings_update_schema_validation()
    print("PASS: Repository Settings CRUD & Path Exclusion Tests")

    import tests.test_e2e_integration as t_e2e
    t_e2e.test_complete_end_to_end_review_pipeline_flow()
    print("PASS: End-to-End Workflow Integration Test")

    print("\nAll backend engine, API, webhook, security, quality, finalization, settings, and E2E integration tests passed successfully!")

if __name__ == "__main__":
    run_tests()

