import shutil
import subprocess
from enum import Enum
from typing import Any


class ToolStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_INSTALLED = "NOT_INSTALLED"
    MISCONFIGURED = "MISCONFIGURED"
    FAILED = "FAILED"


class AnalyzerToolValidator:
    """
    Service to validate system linter binary availability and health.
    Returns status: AVAILABLE, NOT_INSTALLED, MISCONFIGURED, or FAILED.
    """

    TOOLS_CATALOG = {
        "pylint": {"binary": "pylint", "language": "Python", "category": "Code Quality"},
        "bandit": {"binary": "bandit", "language": "Python", "category": "Security SAST"},
        "flake8": {"binary": "flake8", "language": "Python", "category": "Linter"},
        "ruff": {"binary": "ruff", "language": "Python", "category": "Fast Linter"},
        "eslint": {"binary": "eslint", "language": "JavaScript/TypeScript", "category": "Linter & SAST"},
        "java": {"binary": "java", "language": "Java", "category": "Runtime/AST"},
        "node": {"binary": "node", "language": "JavaScript/TypeScript", "category": "Runtime"},
    }

    @classmethod
    def check_tool_status(cls, tool_name: str) -> dict[str, Any]:
        """Check status of a single CLI linter or tool."""
        info = cls.TOOLS_CATALOG.get(tool_name.lower())
        if not info:
            return {"tool": tool_name, "status": ToolStatus.NOT_INSTALLED.value, "detail": "Tool not in catalog"}

        binary = info["binary"]
        executable_path = shutil.which(binary)

        if not executable_path:
            return {
                "tool": tool_name,
                "status": ToolStatus.NOT_INSTALLED.value,
                "language": info["language"],
                "category": info["category"],
                "detail": f"Binary '{binary}' not found on PATH. Falling back to internal rule-based engine.",
            }

        # Attempt executing version check
        try:
            res = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode in (0, 1):
                return {
                    "tool": tool_name,
                    "status": ToolStatus.AVAILABLE.value,
                    "language": info["language"],
                    "category": info["category"],
                    "path": executable_path,
                    "version": (res.stdout or res.stderr).splitlines()[0] if (res.stdout or res.stderr) else "Installed",
                }
            return {
                "tool": tool_name,
                "status": ToolStatus.MISCONFIGURED.value,
                "language": info["language"],
                "category": info["category"],
                "path": executable_path,
                "detail": f"Binary returned exit code {res.returncode}",
            }
        except subprocess.TimeoutExpired:
            return {
                "tool": tool_name,
                "status": ToolStatus.FAILED.value,
                "language": info["language"],
                "category": info["category"],
                "detail": "Version check timed out",
            }
        except Exception as exc:
            return {
                "tool": tool_name,
                "status": ToolStatus.FAILED.value,
                "language": info["language"],
                "category": info["category"],
                "detail": f"Execution failure: {str(exc)}",
            }

    @classmethod
    def get_all_analyzers_status(cls) -> dict[str, Any]:
        """Retrieve overall health and availability matrix of all language analyzers."""
        results = {}
        overall_available = 0
        overall_total = len(cls.TOOLS_CATALOG)

        for tool_name in cls.TOOLS_CATALOG:
            status_data = cls.check_tool_status(tool_name)
            results[tool_name] = status_data
            if status_data["status"] == ToolStatus.AVAILABLE.value:
                overall_available += 1

        return {
            "summary": {
                "total_tools": overall_total,
                "available_tools": overall_available,
                "fallback_active": overall_available < overall_total,
            },
            "analyzers": results,
        }
