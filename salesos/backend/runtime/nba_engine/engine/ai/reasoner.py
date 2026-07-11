"""AI Reasoning engine for NBA — evaluates opportunities using LLM."""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("salesos.nba.ai")


class NBAReasoner:
    """Optional AI reasoning layer. Falls back gracefully when no LLM is available."""

    def __init__(self, llm_service: Any | None = None):
        self._llm = llm_service

    async def evaluate(
        self,
        opportunity: dict[str, Any],
        company: dict[str, Any],
        signals: list[dict[str, Any]],
        activities: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Evaluate candidates using LLM. Returns None if no LLM available or on timeout."""
        if not self._llm:
            return None
        try:
            prompt = self._build_prompt(opportunity, company, signals, activities, candidates)
            response = await self._llm.chat(prompt)
            return self._parse_response(response)
        except Exception as exc:
            logger.warning("NBA AI evaluation failed (falling back to rule-only): %s", exc)
            return None

    def _build_prompt(
        self,
        opportunity: dict[str, Any],
        company: dict[str, Any],
        signals: list[dict[str, Any]],
        activities: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        now = datetime.now(timezone.utc)
        opp_name = opportunity.get("name", "")
        stage = opportunity.get("stage", "")
        value = opportunity.get("value", 0)
        health = opportunity.get("health", "healthy")
        company_name = company.get("name_ar") or company.get("name_en", "")
        industry = company.get("industry", "")
        days_since = 0
        if activities:
            last_ts = activities[0].get("timestamp")
            if last_ts and isinstance(last_ts, datetime):
                days_since = (now - last_ts).days

        candidates_text = "\n".join(
            f"{i+1}. {c['action']} — {c['reason']} (confidence: {c.get('score', 0):.0%})"
            for i, c in enumerate(candidates)
        )

        return [
            {
                "role": "system",
                "content": "You are a senior sales strategist evaluating sales opportunities. "
                           "Analyze the context and recommend the single Next Best Action. "
                           "Output valid JSON only.",
            },
            {
                "role": "user",
                "content": json.dumps({
                    "opportunity": {"name": opp_name, "stage": stage, "value": value, "health": health},
                    "company": {"name": company_name, "industry": industry},
                    "days_since_last_activity": days_since,
                    "candidate_actions": candidates,
                    "task": (
                        "1. Evaluate each candidate's relevance to this specific opportunity\n"
                        "2. Rank candidates by expected revenue impact\n"
                        "3. Explain your reasoning\n"
                        "4. Identify any risks\n"
                        "5. Suggest the single Next Best Action\n"
                        'Output format: {"ranking": [...], "explanation": "...", "confidence": 0.0-1.0, "risks": [...]}'
                    ),
                }, ensure_ascii=False),
            },
        ]

    def _parse_response(self, response: Any) -> dict[str, Any]:
        """Parse LLM response JSON."""
        content = response
        if hasattr(response, "choices"):
            content = response.choices[0].message.content
        if isinstance(content, str):
            content = json.loads(content)
        return {
            "ranking": content.get("ranking", []),
            "explanation": content.get("explanation", ""),
            "confidence": float(content.get("confidence", 0.5)),
            "risks": content.get("risks", []),
        }


from datetime import datetime, timezone
