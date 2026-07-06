"""Quality Checker — Orchestra node 8.

Reviews the Mini Engine's CandidateResponse and returns an immutable QualityResult
(approved / rejected / needs_retry). No AI, no model calls, no final delivery.
See docs/QUALITY_CHECKER.md.
"""

from app.orchestra.quality.checker import check
from app.orchestra.quality.errors import QualityCheckerError
from app.orchestra.quality.schemas import (
    SCHEMA_VERSION,
    QualityResult,
    QualityStatus,
    Severity,
    Violation,
)

__all__ = [
    "check",
    "QualityCheckerError",
    "QualityResult",
    "QualityStatus",
    "Severity",
    "Violation",
    "SCHEMA_VERSION",
]
