# ReviewAI - Testing & Quality Assurance Guide

This document outlines the testing architecture, environment setup, execution commands, mocking strategies, and CI/CD integration workflows for the **ReviewAI** platform.

---

## 1. Test Architecture Overview

ReviewAI utilizes a multi-tiered automated testing architecture to validate logic from individual analysis engines up to end-to-end pull request review publication flows.

```
                                 ┌────────────────────────────────────────┐
                                 │     Integration & End-to-End Suite     │
                                 │      (`test_e2e_integration.py`)       │
                                 └──────────────────┬─────────────────────┘
                                                    │
             ┌──────────────────────────────────────┼──────────────────────────────────────┐
             ▼                                      ▼                                      ▼
┌─────────────────────────┐            ┌─────────────────────────┐            ┌─────────────────────────┐
│     Backend Services    │            │     Analysis Engines    │            │    Frontend UI Suite    │
│  - Auth & OAuth         │            │  - Static Analysis      │            │  - Auth & Protected     │
│  - Repo Management      │            │  - Security SAST        │            │  - Dashboard & Filters  │
│  - Webhook Ingestion    │            │  - Performance Analyzer │            │  - PR Inspector & Modal │
│  - PR Diff Parser       │            │  - AST & Code Quality   │            │  - Settings Save/Reset  │
│  - Review Finalization  │            │  - AI Reasoning Mock    │            │  - Vitest / RTL         │
└─────────────────────────┘            └─────────────────────────┘            └─────────────────────────┘
```

---

## 2. Test Execution Commands

### Backend Tests

To run the complete backend test suite:

```bash
# Set PYTHONPATH to project backend directory
set PYTHONPATH=backend

# Run complete backend test suite runner
python backend/tests/run_standalone_tests.py

# Or run individual pytest modules
pytest backend/tests/ -v
```

#### Test Modules Summary:
- `test_auth_and_oauth.py`: JWT token generation, Fernet secret encryption/decryption, mocked GitHub OAuth exchange.
- `test_repository_management.py`: Repository schemas, settings inheritance, pagination simulation.
- `test_github_webhooks.py`: HMAC SHA-256 signature verification and pull_request webhook payload parsing.
- `test_pull_request_analysis.py`: Unified diff hunk parsing, line extraction, language detection, empty/missing diff patch handling.
- `test_analysis_engines.py`: SAST security vulnerability detection, N+1 query/performance bottleneck detection, Halstead quality metrics computation.
- `test_review_finalization.py`: Executive Markdown summary formatting, safe diff line mapping for inline comments.
- `test_repository_settings.py`: Settings CRUD, path exclusion matching (`is_file_excluded`), analyzer toggling.
- `test_e2e_integration.py`: End-to-end integration test (Webhook -> Job Queue -> Diff Parser -> Analysis Engines -> Quality Calculation -> Settings Override -> AI Review -> Finalization Payload).

---

### Frontend Tests

To run the frontend Vitest suite:

```bash
cd frontend

# Run frontend unit tests
npm test

# Run TypeScript type check
npx tsc --noEmit

# Run production build
npm run build
```

---

## 3. Mocking Strategy & Isolation

To ensure tests execute quickly, deterministically, and offline without requiring production API keys:

1. **GitHub OAuth & REST API**: External HTTP requests to `api.github.com` are intercepted and mocked with static test fixtures.
2. **LLM Provider APIs (OpenAI / Anthropic)**: When `OPENAI_API_KEY` is not present, the `AIReviewEngine` automatically falls back to an internal heuristic rule-based analyzer producing realistic structured review payloads.
3. **Database Isolation**: Unit tests utilize in-memory SQLite / mock AsyncSession objects to avoid altering development database states.
4. **Local Binary Wrappers**: Linter processes (Pylint, ESLint, Checkstyle) gracefully fall back to regex heuristic analyzers when host binaries are missing.

---

## 4. Continuous Integration (GitHub Actions)

The repository includes a automated GitHub Actions workflow (`.github/workflows/ci.yml`) triggering on pushes and pull requests to `main` and `develop` branches:

- **Backend Checks**:
  - Python 3.11 environment setup
  - Dependency installation
  - Ruff code linting
  - Full backend test suite execution (`run_standalone_tests.py` & `pytest backend/tests/`)

- **Frontend Checks**:
  - Node.js 20 environment setup
  - Dependency installation (`npm ci`)
  - TypeScript strict type checking (`tsc --noEmit`)
  - Vitest test suite execution (`npm test`)
  - Production bundle build validation (`npm run build`)
