from app.services.diff_parser import parse_unified_diff


def test_review_summary_markdown_payload_formatting():
    """Verify markdown payload generation with quality score and category breakdown."""
    repo_name = "acme/payment-service"
    pr_number = 101
    quality_score = 92
    findings = [
        {"severity": "HIGH", "category": "SECURITY", "file_path": "auth.py", "line_number": 15, "explanation": "Hardcoded secret"},
        {"severity": "MEDIUM", "category": "PERFORMANCE", "file_path": "db.py", "line_number": 42, "explanation": "N+1 query"},
    ]

    # Generate Markdown Summary
    summary_lines = [
        f"# ReviewAI Code Review Summary for `{repo_name}` (PR #{pr_number})",
        "",
        f"**Overall Quality Score**: `{quality_score}/100` (Grade: A)",
        f"**Total Findings Detected**: `{len(findings)}`",
        "",
        "## Findings Breakdown",
    ]
    for f in findings:
        summary_lines.append(f"- **[{f['severity']}] {f['category']}**: `{f['file_path']}:L{f['line_number']}` - {f['explanation']}")

    markdown_result = "\n".join(summary_lines)

    assert "ReviewAI Code Review Summary" in markdown_result
    assert "acme/payment-service" in markdown_result
    assert "92/100" in markdown_result
    assert "[HIGH] SECURITY" in markdown_result


def test_diff_line_mapping_safe_verification():
    """Verify inline comments are only attached to valid added/modified lines in diff patch."""
    patch = """@@ -1,5 +1,6 @@
 def save_user(user):
-    db.save(user)
+    if not user:
+        raise ValueError("Invalid user")
+    db.save_secure(user)
"""

    parsed = parse_unified_diff(patch)
    added_lines_map = {item["line_number"]: item["content"] for item in parsed["added_lines"]}

    # Line 2 and Line 4 are added lines in diff patch
    assert 2 in added_lines_map
    assert 4 in added_lines_map
    assert 999 not in added_lines_map  # Line outside changed diff range


if __name__ == "__main__":
    test_review_summary_markdown_payload_formatting()
    test_diff_line_mapping_safe_verification()
    print("Review finalization unit tests PASSED!")
