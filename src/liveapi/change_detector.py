"""Change detection system for OpenAPI specifications.

This module is kept for backward compatibility.
The actual implementation has been moved to the change_detector package.
"""

from .change_detector.models import ChangeType, Change, ChangeAnalysis
from .change_detector.detector import ChangeDetector

__all__ = [
    "ChangeType",
    "Change",
    "ChangeAnalysis",
    "ChangeDetector",
]
