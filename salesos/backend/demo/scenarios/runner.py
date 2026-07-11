"""Demo Scenario Runner — execute any demo scenario by ID."""

from typing import Any

from app.modules.demo_mode import DemoModeService

SCENARIO_REGISTRY: dict[str, Any] = {}


def _import_scenario(module_path: str):
    import importlib
    return importlib.import_module(module_path)


def _ensure_registry():
    if not SCENARIO_REGISTRY:
        modules = [
            ("enterprise_deal", "demo.scenarios.enterprise_deal"),
            ("pipeline_review", "demo.scenarios.pipeline_review"),
            ("company_research", "demo.scenarios.company_research"),
        ]
        for sid, mod_path in modules:
            try:
                mod = _import_scenario(mod_path)
                SCENARIO_REGISTRY[sid] = mod
            except ImportError:
                try:
                    mod = _import_scenario(mod_path.replace("backend.", "demo.", 1))
                    SCENARIO_REGISTRY[sid] = mod
                except ImportError:
                    pass


def list_scenarios() -> list[dict]:
    _ensure_registry()
    results = []
    for sid, mod in SCENARIO_REGISTRY.items():
        meta = mod.get_scenario_metadata()
        results.append(meta)
    return results


def execute_scenario(scenario_id: str, demo_service: DemoModeService | None = None) -> list[dict]:
    _ensure_registry()
    if scenario_id not in SCENARIO_REGISTRY:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIO_REGISTRY.keys())}")

    from app.modules.demo_mode import get_demo_mode_service
    svc = demo_service or get_demo_mode_service()
    mod = SCENARIO_REGISTRY[scenario_id]
    return mod.execute(svc)
