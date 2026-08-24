import json
import pytest
from app.services.diff_parser import parse_unified_diff, detect_language_from_filename
from app.services.code_quality_engine.calculator import CodeQualityCalculator
from app.services.performance_analyzer.engine import PerformanceAnalyzerEngine
from app.services.security_analyzer.engine import SecurityAnalyzerEngine
from app.services.ai_review.engine import AIReviewEngine
from app.services.repository_settings_service import RepositorySettingsService, RepositorySettingsSchema


def test_complete_end_to_end_review_pipeline_flow():
    """
    End-to-End Workflow Integration Test:
    1. Webhook Payload Ingestion simulation
    2. PR Diff Patch Parsing
    3. Language Detection
    4. Multi-Engine Analysis (Security, Performance, Code Quality)
    5. Repository Settings Filtering & Overrides
    6. AI Reasoning Engine Invocation (with heuristic fallback)
    7. Review Finalization & Consolidated Summary Payload Construction
    """
    # 1. Webhook Payload
    webhook_payload = {
        "action": "synchronize",
        "number": 15,
        "pull_request": {
            "number": 15,
            "title": "Add authentication router and database session handler",
            "head": {"ref": "feature/auth", "sha": "1a2b3c4d5e6f"},
            "base": {"ref": "main"},
        },
        "repository": {"full_name": "enterprise/reviewai-service"},
    }
    assert webhook_payload["action"] == "synchronize"

    # 2. PR Diff Patch Parsing
    filename = "auth_service.py"
    patch = """@@ -1,4 +1,7 @@
 def authenticate_user(db, username, password):
-    return db.query("SELECT * FROM users WHERE user='" + username + "'")
+    secret_key = "AKIAIOSFODNN7EXAMPLE"
+    for i in range(50):
+        for j in range(50):
+            db.execute("SELECT * FROM users WHERE username = '" + username + "'")
+    return True
"""
    language = detect_language_from_filename(filename)
    assert language == "Python"

    parsed_diff = parse_unified_diff(patch)
    assert parsed_diff["additions"] == 5

    # 3. Security Analysis Engine
    sec_findings = SecurityAnalyzerEngine.scan_file_content(filename, patch)
    assert len(sec_findings) >= 1

    # 4. Performance Analysis Engine
    perf_findings = PerformanceAnalyzerEngine.analyze_file_performance(filename, patch)
    assert len(perf_findings) >= 1


    # 5. Code Quality Calculation
    quality = CodeQualityCalculator.calculate_metrics(patch, language, len(sec_findings), len(perf_findings), 1)
    assert quality["overall_quality_score"] > 0

    # 6. Repository Settings Filtering
    settings = RepositorySettingsSchema(min_severity_level="LOW", max_findings_limit=10)
    assert RepositorySettingsService.is_file_excluded(filename, settings) is False

    # 7. AI Review Engine Execution
    context = {
        "pull_request": webhook_payload["pull_request"],
        "changed_files": [{"filename": filename, "patch": patch}],
        "static_analysis": {
            "security_findings": sec_findings,
            "code_smells": [],
        },
        "settings": settings.model_dump(),
    }

    import asyncio
    ai_result = asyncio.run(AIReviewEngine.run_ai_review(context))
    assert ai_result["summary"] is not None
    assert isinstance(ai_result["findings"], list)
    assert ai_result["recommendation"] in ("APPROVE", "REQUEST_CHANGES", "COMMENT")

    print("End-to-End Review Pipeline Integration Test PASSED successfully!")


if __name__ == "__main__":
    test_complete_end_to_end_review_pipeline_flow()
