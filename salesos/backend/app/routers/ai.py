"""AI Domain REST API — prompt registry, evaluation, and generation.

EAB-001-P1-AIGOV-01 / Completion Program Stream B:
``POST /ai/generate`` and ``POST /ai/evaluate`` require ``feature_ai_copilot``
and are OpenAPI-``deprecated`` (experimental — not GA). Prompt list/CRUD
remain readable for Studio honesty surfaces (dual registry with Studio library —
see CAPABILITY-DUP-REGISTER). See AI_HONESTY.md.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.common.exceptions import safe_error_detail
from app.config import settings
from app.dependencies import get_current_tenant_id, require_permission_dep
from domains.ai import AIEvaluator, AIService, OpenAIProvider, PromptRegistry
from domains.ai.schemas import ActivateRequest, EvaluateRequest, GenerateRequest, PromptCreate
from sdk.permissions import PermissionAction

logger = logging.getLogger(__name__)

router = APIRouter()

_registry = PromptRegistry()
_evaluator = AIEvaluator(_registry)
_service = AIService(_registry, _evaluator)
_service.register_provider("openai", OpenAIProvider())

_AI_DISABLED_DETAIL = (
    "AI generation/evaluation is disabled (feature_ai_copilot=False). "
    "Experimental only — not GA. See AI_HONESTY.md."
)


def require_ai_copilot_enabled() -> None:
    """Block live AI generate/evaluate while Settings.feature_ai_copilot is False."""
    if not settings.feature_ai_copilot:
        raise HTTPException(status_code=403, detail=_AI_DISABLED_DETAIL)


async def _get_registry() -> PromptRegistry:
    return _registry


async def _get_evaluator() -> AIEvaluator:
    return _evaluator


async def _get_service() -> AIService:
    return _service


_PROMPT_DUP_DESC = (
    "Domain PromptRegistry — not Studio CAP-089 SoT. "
    "EAB-001-P1-DUP-02 dual-capability residual. See CAPABILITY-DUP-REGISTER."
)


@router.get(
    "/ai/prompts",
    summary="List AI prompts (domain registry; dual with Studio library)",
    description=_PROMPT_DUP_DESC,
)
async def list_prompts(
    domain: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.READ)),
):
    try:
        templates = _registry.list(domain=domain)
        return [
            {
                "id": t.id,
                "name": t.name,
                "version": t.version,
                "domain": t.domain,
                "active": t.active,
                "variables": t.variables,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            }
            for t in templates
        ]
    except Exception as exc:
        logger.error("list_prompts failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/ai/prompts",
    status_code=201,
    summary="Create AI prompt (domain registry; dual)",
    description=_PROMPT_DUP_DESC,
)
async def create_prompt(
    body: PromptCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
):
    try:
        from domains.ai.models import PromptTemplate

        template = PromptTemplate(
            id=body.id,
            name=body.name,
            version=body.version,
            template=body.template,
            variables=body.variables,
            output_schema=body.output_schema,
            domain=body.domain,
        )
        _registry.register(template)
        return {"id": template.id, "name": template.name, "version": template.version}
    except Exception as exc:
        logger.error("create_prompt failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/ai/prompts/activate",
    summary="Activate AI prompt (domain registry; dual)",
    description=_PROMPT_DUP_DESC,
)
async def activate_prompt(
    body: ActivateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.UPDATE)),
):
    template = _registry.activate(body.id, body.version)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return {"id": template.id, "name": template.name, "version": template.version, "active": True}


@router.post(
    "/ai/evaluate",
    deprecated=True,
    summary="Evaluate prompt output (experimental; gated)",
    description=(
        "Requires feature_ai_copilot. OpenAPI-deprecated — not GA AI. "
        "See AI_HONESTY.md / AIGOV-01."
    ),
)
async def evaluate(
    body: EvaluateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
    _flag: None = Depends(require_ai_copilot_enabled),
):
    try:
        result = _evaluator.evaluate(
            prompt_id=body.prompt_id,
            input=body.input,
            output=body.output,
            expected=body.expected,
            metrics=body.metrics,
        )
        return {
            "id": result.id,
            "prompt_id": result.prompt_id,
            "score": result.score,
            "metrics": [
                {"name": m.name, "value": m.value, "threshold": m.threshold, "passed": m.passed}
                for m in result.metrics
            ],
            "timestamp": result.timestamp.isoformat(),
        }
    except Exception as exc:
        logger.error("evaluate failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/ai/metrics/{prompt_id}",
    summary="AI prompt metrics (domain registry; dual)",
    description=_PROMPT_DUP_DESC,
)
async def get_metrics(
    prompt_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.READ)),
):
    try:
        return _evaluator.get_metrics(prompt_id)
    except Exception as exc:
        logger.error("get_metrics failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/ai/generate",
    deprecated=True,
    summary="Generate via prompt template (experimental; gated)",
    description=(
        "Requires feature_ai_copilot. OpenAPI-deprecated — not GA AI. "
        "See AI_HONESTY.md / AIGOV-01."
    ),
)
async def generate(
    body: GenerateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
    _flag: None = Depends(require_ai_copilot_enabled),
):
    try:
        output = await _service.generate(
            prompt_template_id=body.prompt_template_id,
            variables=body.variables,
            provider=body.provider,
            model=body.model,
        )
        return {"prompt_template_id": body.prompt_template_id, "output": output}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=safe_error_detail(exc, "Not found")) from exc
    except Exception as exc:
        logger.error("generate failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
