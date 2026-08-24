import json
from typing import Any

import openai

from app.core.config import settings
from app.core.logging import logger
from app.services.ai_review.prompt_templates import SYSTEM_PROMPT, build_user_prompt


class AIReviewEngine:
    """
    AI Review Execution Engine integrating OpenAI GPT-4o JSON mode with heuristic fallback.
    """

    @staticmethod
    async def run_ai_review(context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute AI code review analysis for given PR context.
        """
        # Check settings overrides
        repo_settings = context.get("settings", {})
        if repo_settings.get("ai_review_enabled") is False or repo_settings.get("analysis_enabled") is False:
            return {
                "summary": "AI Review skipped as per repository configuration settings.",
                "score": 100,
                "recommendation": repo_settings.get("review_mode", "APPROVE"),
                "findings": [],
                "inline_comments": [],
            }

        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == "your_openai_api_key_here":
            logger.info("OPENAI_API_KEY is not configured; running rule-based heuristic AI engine.")
            return AIReviewEngine._run_heuristic_fallback_review(context)

        user_prompt = build_user_prompt(context)

        try:
            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_json_str = response.choices[0].message.content or "{}"
            result = json.loads(raw_json_str)
            return AIReviewEngine._normalize_review_response(result)

        except Exception as exc:
            logger.warning("OpenAI API call failed (%s); falling back to heuristic engine.", str(exc))
            return AIReviewEngine._run_heuristic_fallback_review(context)


    @staticmethod
    def _normalize_review_response(data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize and validate LLM JSON output.
        """
        return {
            "summary": data.get("summary", "AI review completed."),
            "score": int(data.get("score", 85)),
            "recommendation": data.get("recommendation", "COMMENT"),
            "findings": data.get("findings", []),
            "inline_comments": data.get("inline_comments", []),
        }

    @staticmethod
    def _run_heuristic_fallback_review(context: dict[str, Any]) -> dict[str, Any]:
        """
        Heuristic rule-based AI review fallback analyzer.
        Calculates findings, SOLID principle suggestions, naming feedback, and inline comments.
        """
        pr = context.get("pull_request", {})
        files = context.get("changed_files", [])
        static = context.get("static_analysis", {})

        findings: list[dict[str, Any]] = []
        inline_comments: list[dict[str, Any]] = []
        score = 90

        # Process pre-detected static analysis findings
        for sf in static.get("security_findings", []):
            score -= 10
            findings.append({
                "severity": sf.get("severity", "HIGH"),
                "category": "SECURITY",
                "explanation": f"Security finding '{sf.get('title')}' flagged by static analysis.",
                "suggested_fix": "Sanitize inputs and use secure parameters.",
                "confidence_score": 0.95,
                "file_path": sf.get("file_path", "unknown"),
                "line_number": sf.get("start_line", 1),
            })

        for cs in static.get("code_smells", []):
            score -= 3
            findings.append({
                "severity": "MEDIUM",
                "category": "MAINTAINABILITY",
                "explanation": cs.get("description", "Code smell detected."),
                "suggested_fix": "Refactor code to improve readability.",
                "confidence_score": 0.85,
                "file_path": cs.get("file_path", "unknown"),
                "line_number": cs.get("start_line", 1),
            })

        # Process diff patches for SOLID principles & naming
        for f in files:
            filename = f.get("filename", "")
            patch = f.get("patch", "")
            if not patch:
                continue

            lines = patch.splitlines()
            for idx, line in enumerate(lines, start=1):
                # Naming Suggestion
                if line.startswith("+") and (" var " in line or " let tmp " in line or "data1" in line):
                    findings.append({
                        "severity": "LOW",
                        "category": "NAMING",
                        "explanation": f"Variable name in '{filename}' is vague or non-idiomatic.",
                        "suggested_fix": "Use descriptive domain-specific variable names.",
                        "confidence_score": 0.80,
                        "file_path": filename,
                        "line_number": idx,
                    })

                # SOLID Principle - Single Responsibility
                if line.startswith("+") and len(line) > 120:
                    findings.append({
                        "severity": "LOW",
                        "category": "SOLID_PRINCIPLE",
                        "explanation": f"Long line in '{filename}' suggests method may be doing too much (SRP violation).",
                        "suggested_fix": "Break method down into smaller single-responsibility methods.",
                        "confidence_score": 0.75,
                        "file_path": filename,
                        "line_number": idx,
                    })

                # Inline comment example
                if line.startswith("+") and "TODO" in line:
                    inline_comments.append({
                        "path": filename,
                        "line": idx,
                        "body": "Unresolved TODO found in pull request.",
                        "suggestion": "// TODO resolved",
                    })

        # Filter by min_severity_level and max_findings_limit
        repo_settings = context.get("settings", {})
        min_sev = repo_settings.get("min_severity_level", "LOW").upper()
        max_limit = repo_settings.get("max_findings_limit", 50)

        severity_ranks = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        min_rank = severity_ranks.get(min_sev, 1)

        filtered_findings = [
            f for f in findings if severity_ranks.get(f.get("severity", "LOW").upper(), 1) >= min_rank
        ][:max_limit]

        score = max(50, min(100, score))
        configured_mode = repo_settings.get("review_mode")
        if configured_mode and configured_mode != "AUTO":
            recommendation = configured_mode
        else:
            recommendation = "APPROVE" if score >= 85 else ("REQUEST_CHANGES" if score < 70 else "COMMENT")

        summary = (
            f"AI Review completed for PR #{pr.get('number')}. "
            f"Analyzed {len(files)} changed files and identified {len(filtered_findings)} findings. "
            f"Overall quality score is {score}%."
        )

        return {
            "summary": summary,
            "score": score,
            "recommendation": recommendation,
            "findings": filtered_findings,
            "inline_comments": inline_comments,
        }

