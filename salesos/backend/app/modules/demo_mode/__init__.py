"""Demo Mode module for SalesOS.

Provides DemoModeService to toggle demo mode, which enables:
- Realistic seed data loading
- Faster response times (cached)
- No rate limiting
- Scenario execution for sales demos
"""

from app.modules.demo_mode.service import DemoModeService, get_demo_mode_service

__all__ = ["DemoModeService", "get_demo_mode_service"]
