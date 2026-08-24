from app.services.diff_parser import detect_language_from_filename, parse_unified_diff


def test_language_detection_from_filenames():
    """Verify programming language detection based on extension or basename."""
    assert detect_language_from_filename("main.py") == "Python"
    assert detect_language_from_filename("App.tsx") == "TypeScript"
    assert detect_language_from_filename("service.java") == "Java"
    assert detect_language_from_filename("main.go") == "Go"
    assert detect_language_from_filename("Dockerfile") == "Dockerfile"
    assert detect_language_from_filename("unknown.xyz") == "Plain Text"


def test_parse_unified_diff_hunks_and_lines():
    """Verify parsing unified diff patch string into added/deleted lines."""
    patch = """@@ -1,5 +1,6 @@
 def hello():
-    print("old line")
+    print("new line 1")
+    print("new line 2")
     return True
"""

    parsed = parse_unified_diff(patch)
    assert parsed["additions"] == 2
    assert parsed["deletions"] == 1
    assert len(parsed["hunks"]) == 1
    assert len(parsed["added_lines"]) == 2
    assert len(parsed["deleted_lines"]) == 1

    assert parsed["added_lines"][0]["content"] == '    print("new line 1")'
    assert parsed["added_lines"][0]["line_number"] == 2


def test_parse_unified_diff_empty_or_none():
    """Verify graceful handling of missing or empty diff patches."""
    parsed = parse_unified_diff("")
    assert parsed["additions"] == 0
    assert parsed["deletions"] == 0
    assert parsed["hunks"] == []


if __name__ == "__main__":
    test_language_detection_from_filenames()
    test_parse_unified_diff_hunks_and_lines()
    test_parse_unified_diff_empty_or_none()
    print("Pull Request analysis unit tests PASSED!")
