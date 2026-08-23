"""Grounded Phase 3B — ForecastAgent (deterministic pipeline read).

Forecast shape comes ONLY from EvidencePack opportunity items (stage, status,
probability, banded value). Exact monetary forecasting is impossible by design
(values are confidentiality-banded upstream) and is reported as a limitation,
never invented.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import metrics, opportunities_from
from .llm import LLMService

OPEN_STATUSES = {"open", "in_progress", "qualified", "proposal", "negotiation"}


def build_forecast(pack) -> dict:
    """Pure deterministic pipeline summary over the pack."""

    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "company_id": pack.company_id,
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "forecast": None,
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    deals = opportunities_from(pack)
    if not deals:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "company_id": pack.company_id,
            "summary": "No opportunities are recorded for this company in SalesOS.",
            "forecast": None,
            "missing_information": sorted(set(missing + ["opportunities"])),
            "metrics": metrics(None, pack),
        }

    by_stage: dict[str, dict] = {}
    open_deals = []
    probs: list[float] = []
    bands: dict[str, int] = {}
    for d in deals:
        stage = (d.get("stage") or {}).get("value", "unknown")
        status = (d.get("status") or {}).get("value", "").lower()
        st_eid = (d.get("stage") or {}).get("evidence")
        slot = by_stage.setdefault(stage, {"stage": stage, "count": 0, "evidence": []})
        slot["count"] += 1
        if st_eid:
            slot["evidence"].append(st_eid)

        band = (d.get("value_band") or {}).get("value")
        if band:
            bands[band] = bands.get(band, 0) + 1

        if status in OPEN_STATUSES or status == "":
            open_deals.append(d)
        raw_p = (d.get("probability") or {}).get("value")
        try:
            probs.append(float(str(raw_p).rstrip("%")) / 100 if "%" in str(raw_p) else float(raw_p))
        except (TypeError, ValueError):
            pass

    avg_prob = sum(probs) / len(probs) if probs else None
    if avg_prob is None:
        band_label = "UNKNOWN"
    elif avg_prob >= 0.6:
        band_label = "HIGH"
    elif avg_prob >= 0.3:
        band_label = "MEDIUM"
    else:
        band_label = "LOW"

    limitations = [
        "Exact deal values are confidentiality-banded; a monetary forecast "
        "requires pricing data that is not present in SalesOS."
    ]

    return {
        "status": "OK",
        "company_id": pack.company_id,
        "summary": (
            f"{len(open_deals)} open of {len(deals)} recorded opportunity(ies); "
            f"probability-weighted readiness {band_label}."
        ),
        "forecast": {
            "open_count": len(open_deals),
            "total_count": len(deals),
            "by_stage": list(by_stage.values()),
            "observed_value_bands": [
                {"band": b, "count": c} for b, c in sorted(bands.items())
            ],
            "avg_probability_open": round(avg_prob, 2) if avg_prob is not None else None,
            "readiness_band": band_label,
            "deals": [
                {
                    "id": d.get("id"),
                    "stage": (d.get("stage") or {}).get("value"),
                    "status": (d.get("status") or {}).get("value"),
                    "value_band": (d.get("value_band") or {}).get("value"),
                    "probability": (d.get("probability") or {}).get("value"),
                    "evidence": [
                        v.get("evidence") for v in d.values() if isinstance(v, dict)
                    ],
                }
                for d in deals
            ],
        },
        "limitations": limitations,
        "missing_information": sorted(set(missing + ["exact_deal_values"])),
        "metrics": metrics(None, pack),
    }


class ForecastAgent(BaseAgent):
    """Pipeline forecast grounded in real SalesOS opportunity records."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("forecast", "2.1")
        self._llm = llm
        self._evidence_loader = evidence_loader

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        tenant_id = task.input.get("tenant_id")

        pack = None
        retrieval_ms = None
        if (
            self._evidence_loader is not None
            and tenant_id
            and company_id not in ("", "unknown", None)
        ):
            try:
                t0 = time.monotonic()
                pack = await self._evidence_loader(str(tenant_id), str(company_id))
                retrieval_ms = (time.monotonic() - t0) * 1000
            except Exception:
                pack = None

        if pack is not None:
            out = build_forecast(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.8 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="forecast", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        context = task.input
        pipeline_value = context.get("pipeline_value", 0)
        win_rate = context.get("win_rate", 0)
        avg_deal_size = context.get("avg_deal_size", 0)

        if self._llm:
            response = await self._llm.chat(
                system="أنت محلل مالي. قدم توقعات إيرادات بناءً على البيانات.",
                messages=[{"role": "user", "content": f"حلل التوقعات: قيمة الأنابيب={pipeline_value}, معدل الفوز={win_rate}, متوسط الصفقة={avg_deal_size}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="forecast",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="forecast",
            output={"message": "يتطلب بيانات الأنابيب ومفتاح OpenAI للتوقعات."},
            confidence=0.2,
        )
