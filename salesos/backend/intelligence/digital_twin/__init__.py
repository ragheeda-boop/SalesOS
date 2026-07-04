"""
Layer 4b: Digital Twin Engine
Every entity is a living model, not a database record.
Company Twin, Deal Twin, Contact Twin - all with state, behavior, and simulation capability.
"""
from .twin import DigitalTwin, TwinState, TwinEngine
from .company_twin import CompanyTwin, CompanyState

__all__ = ["DigitalTwin", "TwinState", "TwinEngine", "CompanyTwin", "CompanyState"]
