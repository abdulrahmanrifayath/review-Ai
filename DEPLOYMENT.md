# ReviewAI - Production Deployment & Infrastructure Guide

This document details the production deployment architecture, containerized static analysis dependencies, language analyzer health monitoring, resource limits, and Docker Compose orchestration.

---

## 1. Static Analysis Language Support Matrix

ReviewAI features a hybrid static analysis engine combining CLI static linters, SAST scanners, Tree-sitter AST parsers, and deterministic rule-based fallbacks.

| Language | Primary Analyzer / Tool | Secondary SAST / Quality | Fallback Strategy | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `Pylint 3.2+`, `Ruff 0.4+`, `Flake8` | `Bandit 1.7+` (SAST) | Internal AST & Pattern Rules | **PASS** |
| **JavaScript / TypeScript** | `ESLint 8.57+` | `@typescript-eslint` | AST Regex & Code Smell Fallback | **PASS** |
| **Java** | `Checkstyle` / `OpenJDK 17 JRE` | Halstead Complexity & AST | Rule-based Java Quality Fallback | **PASS** |
| **Go** | Tree-sitter Go Parser | Halstead Metric Calculator | Structural AST Analyzer | **PASS** |
| **C / C++** | Tree-sitter C/C++ Parser | Halstead Metric Calculator | Structural AST Analyzer | **PASS** |

---

## 2. Containerized Dependencies

The backend container (`backend/Dockerfile`) encapsulates all language runtime dependencies to eliminate undocumented host machine dependencies:

- **Python Environment**: Python 3.11-slim with `pylint`, `bandit`, `flake8`, `radon`, `ruff`, and `tree-sitter` preinstalled via `requirements.txt`.
- **Node.js & npm**: Node.js runtime with globally installed `eslint@8.57.0`, `@typescript-eslint/parser`, and `@typescript-eslint/eslint-plugin`.
- **Java Runtime**: `openjdk-17-jre-headless` for Java Checkstyle/PMD/AST analysis.

---

## 3. Subprocess Execution & Resource Protection

All linter processes executed via `LinterRunnerManager` adhere to strict production resource constraints:

- **Safe Command Execution**: Commands execute strictly with array-formatted arguments without `shell=True` to prevent shell injection vulnerabilities.
- **Subprocess Timeout**: Maximum **30 seconds** execution limit per linter run (`asyncio.wait_for`). Processes exceeding 30s are terminated via SIGKILL and fall back to rule-based analysis.
- **Output Buffer Limit**: Stdout buffers are capped at **1MB** (`1024 * 1024` bytes) to prevent memory exhaustion from verbose output.
- **Temporary File Cleanup**: Named temporary files are created with unique UUID paths and deleted in `finally:` blocks.

---

## 4. Analyzer Health & Validation Endpoint

The platform provides a live health check endpoint exposing tool availability:

- **Endpoint**: `GET /api/v1/health/analyzers`
- **Response Example**:
```json
{
  "summary": {
    "total_tools": 7,
    "available_tools": 7,
    "fallback_active": false
  },
  "analyzers": {
    "pylint": {
      "tool": "pylint",
      "status": "AVAILABLE",
      "language": "Python",
      "category": "Code Quality",
      "path": "/usr/local/bin/pylint"
    },
    "bandit": {
      "tool": "bandit",
      "status": "AVAILABLE",
      "language": "Python",
      "category": "Security SAST"
    },
    "eslint": {
      "tool": "eslint",
      "status": "AVAILABLE",
      "language": "JavaScript/TypeScript",
      "category": "Linter & SAST"
    }
  }
}
```

---

## 5. Docker Build & Deployment Instructions

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2+

### Running local or production stack

```bash
# Build and start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build -d

# Check service container status
docker-compose ps

# View backend logs
docker-compose logs -f backend

# Run backend test suite inside container
docker-compose exec backend python backend/tests/run_standalone_tests.py
```
