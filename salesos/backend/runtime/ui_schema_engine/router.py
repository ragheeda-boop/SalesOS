"""UI Schema Engine REST API."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/schema", tags=["UI Schema"])


@router.get("/viewer/{entity_type}/{entity_id}")
async def get_viewer_schema(entity_type: str, entity_id: str,
                            user_id: str = "", tenant_id: str = ""):
    """Get the complete UI schema for an object viewer (Company360, Deal360, etc.)."""
    from runtime.capability_framework import Capability
    from runtime.widget_engine import WidgetRegistry
    from runtime.ui_schema_engine import UISchemaEngine

    capabilities = [c.manifest.to_dict() for c in Capability.all()
                    if c.id in ["company", "timeline", "feature-store",
                                "decision-engine", "knowledge-graph", "identity"]]

    # Auto-generate widgets if needed
    WidgetRegistry.generate_from_capabilities()
    all_widgets = [w.to_dict() for w in WidgetRegistry.all()
                   if w.capability_id in ["company", "timeline", "feature-store",
                                          "decision-engine", "knowledge-graph"]]

    engine = UISchemaEngine()
    schema = engine.generate_viewer_schema(
        entity_type=entity_type,
        entity_id=entity_id,
        capabilities=capabilities,
        widgets=all_widgets,
    )
    return schema
