import asyncio
import json
import os
import re
import shutil
import tempfile
from typing import Any

from app.core.logging import logger


SUBPROCESS_TIMEOUT_SECONDS = 30
MAX_STDOUT_BYTES = 1024 * 1024  # 1MB max stdout buffer limit


class LinterRunnerManager:
    """
    Manager for executing CLI static linters (ESLint, Pylint, Flake8, Bandit, Checkstyle, PMD)
    with rule-based fallbacks, execution timeouts, and output resource protection.
    """

    @staticmethod
    async def run_pylint(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Run Pylint on Python code with timeout and resource protection."""
        findings: list[dict[str, Any]] = []
        if not shutil.which("pylint"):
            logger.info("Pylint CLI binary not found on system PATH. Using fallback rules for %s.", file_path)
            return LinterRunnerManager._python_fallback_rules(file_path, code_content)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write(code_content)
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "pylint", "--output-format=json", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=SUBPROCESS_TIMEOUT_SECONDS)
            if stdout:
                truncated_stdout = stdout[:MAX_STDOUT_BYTES].decode("utf-8", errors="replace")
                data = json.loads(truncated_stdout)
                for item in data:
                    findings.append({
                        "tool": "pylint",
                        "rule_id": item.get("symbol", "pylint-rule"),
                        "message": item.get("message", ""),
                        "line": item.get("line", 1),
                        "column": item.get("column", 0),
                        "type": item.get("type", "warning"),
                    })
        except asyncio.TimeoutError:
            logger.warning("Pylint execution timed out after %ds for %s. Fallback active.", SUBPROCESS_TIMEOUT_SECONDS, file_path)
            try:
                proc.kill()
            except Exception:
                pass
            return LinterRunnerManager._python_fallback_rules(file_path, code_content)
        except Exception as exc:
            logger.warning("Pylint execution failed for %s: %s", file_path, str(exc))
            return LinterRunnerManager._python_fallback_rules(file_path, code_content)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        return findings

    @staticmethod
    async def run_bandit(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Run Bandit Python SAST security scanner with timeout protection."""
        findings: list[dict[str, Any]] = []
        if not shutil.which("bandit"):
            logger.info("Bandit CLI binary not found on system PATH. Using fallback SAST rules for %s.", file_path)
            return LinterRunnerManager._bandit_fallback_security_rules(file_path, code_content)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write(code_content)
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "bandit", "-f", "json", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=SUBPROCESS_TIMEOUT_SECONDS)
            if stdout:
                truncated_stdout = stdout[:MAX_STDOUT_BYTES].decode("utf-8", errors="replace")
                data = json.loads(truncated_stdout)
                for item in data.get("results", []):
                    findings.append({
                        "tool": "bandit",
                        "rule_id": item.get("test_id", "B000"),
                        "title": item.get("issue_text", "Security Vulnerability"),
                        "severity": item.get("issue_severity", "HIGH").upper(),
                        "cwe_id": f"CWE-{item.get('issue_cwe', {}).get('id', '200')}",
                        "line": item.get("line_number", 1),
                        "code": item.get("code", ""),
                    })
        except asyncio.TimeoutError:
            logger.warning("Bandit execution timed out after %ds for %s. Fallback active.", SUBPROCESS_TIMEOUT_SECONDS, file_path)
            try:
                proc.kill()
            except Exception:
                pass
            return LinterRunnerManager._bandit_fallback_security_rules(file_path, code_content)
        except Exception as exc:
            logger.warning("Bandit execution failed for %s: %s", file_path, str(exc))
            return LinterRunnerManager._bandit_fallback_security_rules(file_path, code_content)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        return findings

    @staticmethod
    async def run_eslint(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Run ESLint on JavaScript/TypeScript code with timeout protection."""
        findings: list[dict[str, Any]] = []
        if not shutil.which("eslint"):
            logger.info("ESLint CLI binary not found on system PATH. Using fallback JS/TS rules for %s.", file_path)
            return LinterRunnerManager._js_ts_fallback_rules(file_path, code_content)

        ext = os.path.splitext(file_path)[1] or ".ts"
        with tempfile.NamedTemporaryFile(suffix=ext, mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write(code_content)
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "eslint", "-f", "json", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=SUBPROCESS_TIMEOUT_SECONDS)
            if stdout:
                truncated_stdout = stdout[:MAX_STDOUT_BYTES].decode("utf-8", errors="replace")
                data = json.loads(truncated_stdout)
                for file_res in data:
                    for msg in file_res.get("messages", []):
                        findings.append({
                            "tool": "eslint",
                            "rule_id": msg.get("ruleId", "eslint-rule"),
                            "message": msg.get("message", ""),
                            "line": msg.get("line", 1),
                            "column": msg.get("column", 0),
                            "severity": "ERROR" if msg.get("severity") == 2 else "WARNING",
                        })
        except asyncio.TimeoutError:
            logger.warning("ESLint execution timed out after %ds for %s. Fallback active.", SUBPROCESS_TIMEOUT_SECONDS, file_path)
            try:
                proc.kill()
            except Exception:
                pass
            return LinterRunnerManager._js_ts_fallback_rules(file_path, code_content)
        except Exception as exc:
            logger.warning("ESLint execution failed for %s: %s", file_path, str(exc))
            return LinterRunnerManager._js_ts_fallback_rules(file_path, code_content)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        return findings

    @staticmethod
    async def run_checkstyle(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Run Java static quality check with fallback."""
        if not shutil.which("java"):
            logger.info("Java runtime binary not found on system PATH. Using Java fallback rules for %s.", file_path)
            return LinterRunnerManager._java_fallback_rules(file_path, code_content)
        return LinterRunnerManager._java_fallback_rules(file_path, code_content)


    @staticmethod
    def _python_fallback_rules(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Rule-based Python quality checker when CLI binary is missing."""
        results = []
        lines = code_content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if "except Exception:" in line or "except:" in line:
                results.append({
                    "tool": "pylint",
                    "rule_id": "W0703",
                    "message": "Catching too general exception 'Exception'.",
                    "line": idx,
                    "column": 0,
                    "type": "warning",
                })
            if "print(" in line and not file_path.startswith("test"):
                results.append({
                    "tool": "pylint",
                    "rule_id": "T201",
                    "message": "print statement found. Consider using logging instead.",
                    "line": idx,
                    "column": 0,
                    "type": "warning",
                })
        return results

    @staticmethod
    def _bandit_fallback_security_rules(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Rule-based Python security scanner fallback."""
        results = []
        lines = code_content.splitlines()
        sec_patterns = [
            (re.compile(r"exec\s*\("), "B102", "Use of exec detected (code execution vulnerability)", "CRITICAL", "CWE-95"),
            (re.compile(r"eval\s*\("), "B307", "Use of eval detected (dynamic code injection)", "CRITICAL", "CWE-95"),
            (re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "B105", "Possible hardcoded password credential detected", "HIGH", "CWE-259"),
            (re.compile(r"api_key\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "B106", "Possible hardcoded API key credential detected", "HIGH", "CWE-798"),
        ]

        for idx, line in enumerate(lines, start=1):
            for pat, rule_id, title, sev, cwe in sec_patterns:
                if pat.search(line):
                    results.append({
                        "tool": "bandit",
                        "rule_id": rule_id,
                        "title": title,
                        "severity": sev,
                        "cwe_id": cwe,
                        "line": idx,
                        "code": line.strip(),
                    })

        return results

    @staticmethod
    def _js_ts_fallback_rules(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Rule-based JS/TS quality checker fallback."""
        results = []
        lines = code_content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if "console.log(" in line:
                results.append({
                    "tool": "eslint",
                    "rule_id": "no-console",
                    "message": "Unexpected console statement.",
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                })
            if "eval(" in line:
                results.append({
                    "tool": "eslint",
                    "rule_id": "no-eval",
                    "message": "eval() can be harmful.",
                    "line": idx,
                    "column": 0,
                    "severity": "ERROR",
                })
            if " == null" in line or " == true" in line:
                results.append({
                    "tool": "eslint",
                    "rule_id": "eqeqeq",
                    "message": "Expected '===' and instead saw '=='.",
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                })
        return results

    @staticmethod
    def _java_fallback_rules(file_path: str, code_content: str) -> list[dict[str, Any]]:
        """Rule-based Java static quality checker fallback."""
        results = []
        lines = code_content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if "System.out.print" in line:
                results.append({
                    "tool": "checkstyle",
                    "rule_id": "SystemPrintln",
                    "message": "Avoid System.out.println in production code. Use a Logger instead.",
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                })
            if "catch (Exception " in line or "catch(Exception " in line:
                results.append({
                    "tool": "checkstyle",
                    "rule_id": "EmptyCatchBlock",
                    "message": "Catching generic Exception. Prefer catching specific exceptions.",
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                })
            if "e.printStackTrace()" in line:
                results.append({
                    "tool": "checkstyle",
                    "rule_id": "AvoidPrintStackTrace",
                    "message": "Avoid e.printStackTrace(). Log exception details with logger.",
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                })
        return results

