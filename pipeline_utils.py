"""Adapter to centralized pipeline utilities in salesos/backend/pipeline/.

Usage:
    from pipeline_utils import style_header, auto_width, GREEN_FILL, RED_FILL, YELLOW_FILL
"""

import sys
from pathlib import Path

BACKEND_PIPELINE = Path(__file__).parent / "salesos" / "backend" / "pipeline"
if str(BACKEND_PIPELINE) not in sys.path:
    sys.path.insert(0, str(BACKEND_PIPELINE.parent))

from pipeline.excel_utils import style_header, auto_width, apply_border, HDR_FONT, HDR_FILL, GREEN_FILL, RED_FILL, YELLOW_FILL, LIGHT_BLUE_FILL, THIN_BORDER
from pipeline.validation_engine import DomainValidator, DomainCheckResult

__all__ = [
    "style_header", "auto_width", "apply_border",
    "HDR_FONT", "HDR_FILL", "GREEN_FILL", "RED_FILL", "YELLOW_FILL", "LIGHT_BLUE_FILL", "THIN_BORDER",
    "DomainValidator", "DomainCheckResult",
]
