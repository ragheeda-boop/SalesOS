"""Form Engine REST API."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import verify_token

router = APIRouter(prefix="/api/v1/forms", tags=["Form Engine"], dependencies=[Depends(verify_token)])


class FormGenerateRequest(BaseModel):
    form_id: str
    title: str
    json_schema: dict
    ui_schema: dict = {}


@router.post("/generate")
async def generate_form(req: FormGenerateRequest):
    """Generate a form definition from JSON Schema."""
    from runtime.form_engine import FormEngine
    engine = FormEngine()
    form = engine.generate_from_schema(req.form_id, req.title, req.json_schema, req.ui_schema)
    return form.to_dict()


@router.post("/{form_id}/validate")
async def validate_form(form_id: str, data: dict):
    """Validate form data against its schema."""
    from runtime.form_engine import FormEngine
    engine = FormEngine()
    valid, errors = engine.validate(form_id, data)
    return {"valid": valid, "errors": errors}


@router.get("/{form_id}")
async def get_form(form_id: str):
    """Get a registered form definition."""
    from runtime.form_engine import FormEngine
    engine = FormEngine()
    form = engine.get_form(form_id)
    if not form:
        raise HTTPException(404, "Form not found")
    return form.to_dict()
