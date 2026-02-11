"""
Package detectors - Détecteurs d'anomalies.
"""

from .base_detector import BaseDetector
__all__ = ['BaseDetector']

# Import optional detectors safely to allow running without all heavy dependencies
try:
    from .spike_detector import SpikeDetector
    __all__.append('SpikeDetector')
except Exception:
    SpikeDetector = None

try:
    from .statistical_detector import StatisticalDetector
    __all__.append('StatisticalDetector')
except Exception:
    StatisticalDetector = None

try:
    from .threshold_detector import ThresholdDetector
    __all__.append('ThresholdDetector')
except Exception:
    ThresholdDetector = None

try:
    from .pattern_detector import PatternDetector
    __all__.append('PatternDetector')
except Exception:
    PatternDetector = None

try:
    from .llm_validator import LLMValidator
    __all__.append('LLMValidator')
except Exception:
    LLMValidator = None