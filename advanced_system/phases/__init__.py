"""
Phases for autonomous pipeline execution
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PhaseResult:
    """Standard result structure for phase execution"""
    success: bool
    phase_name: str
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
