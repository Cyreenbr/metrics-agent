"""
Modèle de données pour les anomalies détectées.

Ce module définit la structure des anomalies identifiées par les détecteurs.
"""

from dataclasses import dataclass, field, asdict
from uuid import uuid4
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum
import json


class AnomalyType(Enum):
    """Types d'anomalies détectables."""
    SPIKE = "spike"  # Pic soudain
    DROP = "drop"  # Chute soudaine
    STATISTICAL_OUTLIER = "statistical_outlier"  # Valeur aberrante statistique
    THRESHOLD_BREACH = "threshold_breach"  # Dépassement de seuil
    PATTERN_ANOMALY = "pattern_anomaly"  # Anomalie de pattern temporel


class Severity(Enum):
    """Niveaux de sévérité des anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

DETECTOR_TO_CATEGORY = {
    "spike_detector": "performance",
    "threshold_detector": "capacity",
    "statistical_detector": "performance",
    "pattern_detector": "availability"
}

ANOMALY_TYPE_TO_DETECTOR = {
    AnomalyType.SPIKE: "spike_detector",
    AnomalyType.THRESHOLD_BREACH: "threshold_detector",
    AnomalyType.STATISTICAL_OUTLIER: "statistical_detector",
    AnomalyType.PATTERN_ANOMALY: "pattern_detector"
}


@dataclass
class Anomaly:
    """
    Représente une anomalie détectée dans une métrique.
    
    Attributes:
        metric_name: Nom de la métrique concernée
        anomaly_type: Type d'anomalie détectée
        severity: Niveau de sévérité
        timestamp: Moment de l'anomalie
        value: Valeur anormale
        expected_value: Valeur attendue (si calculable)
        confidence: Niveau de confiance de la détection (0-1)
        detector_name: Nom du détecteur qui a trouvé l'anomalie
        description: Description de l'anomalie
        metadata: Données supplémentaires (seuils, écarts, etc.)
        labels: Labels de la métrique
    """
    metric_name: str
    anomaly_type: AnomalyType
    severity: Severity
    timestamp: datetime
    value: float
    detector_name: str
    confidence: float = 0.0
    expected_value: Optional[float] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    anomaly_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    llm_validated: bool = False
    llm_status: Optional[str] = None

    def __post_init__(self):
        """Validation après initialisation."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    @property
    def deviation(self) -> Optional[float]:
        """
        Calcule la déviation par rapport à la valeur attendue.
        
        Returns:
            Déviation en pourcentage ou None si pas de valeur attendue
        """
        if self.expected_value is None or self.expected_value == 0:
            return None
        return ((self.value - self.expected_value) / self.expected_value) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'anomalie en dictionnaire pour sérialisation.
        
        Returns:
            Dictionnaire représentant l'anomalie
        """
        data = asdict(self)
        data['anomaly_type'] = self.anomaly_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.deviation is not None:
            data['deviation_percent'] = round(self.deviation, 2)
        return data
    
    def to_json(self) -> str:
        """
        Convertit l'anomalie en JSON.
        
        Returns:
            String JSON de l'anomalie
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Anomaly':
        """
        Crée une anomalie depuis un dictionnaire.
        Ignore les clés inconnues comme 'deviation_percent'.
        Args:
            data: Dictionnaire contenant les données
        Returns:
            Instance d'Anomaly
        """
        data = data.copy()
        data['anomaly_type'] = AnomalyType(data['anomaly_type'])
        data['severity'] = Severity(data['severity'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Remove keys not in Anomaly __init__
        allowed_keys = {
            'metric_name', 'anomaly_type', 'severity', 'timestamp', 'value', 'detector_name',
            'confidence', 'expected_value', 'description', 'metadata', 'labels',
            'anomaly_id', 'start_time', 'end_time'
        }
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)
    
    def __repr__(self) -> str:
        return (f"Anomaly(metric={self.metric_name}, "
                f"type={self.anomaly_type.value}, "
                f"severity={self.severity.value}, "
                f"value={self.value}, "
                f"confidence={self.confidence:.2f})")
    
    def to_orchestrator_dict(self) -> Dict[str, Any]:
        detector = ANOMALY_TYPE_TO_DETECTOR.get(
            self.anomaly_type,
            self.detector_name
        )

        result = {
            "anomaly_id": self.anomaly_id,
            "source": "metrics",
            "metric_name": self.metric_name,
            "labels": self.labels,
            "detector": detector,
            "severity": self.severity.value,
            "description": self.description or f"{self.anomaly_type.value} detected",
            "observed_value": self.value,
            "expected_value": self.expected_value,
            "threshold": self.metadata.get("threshold"),
            "confidence": round(self.confidence, 2),
            "start_time": (self.start_time or self.timestamp).isoformat(),
            "end_time": (self.end_time or self.timestamp).isoformat(),
            "context": {
                "metric_type": self.metadata.get("metric_type", "unknown"),
                "unit": self.metadata.get("unit", ""),
                "lookback_window": self.metadata.get("lookback_window", "")
            },
            "suggested_category": DETECTOR_TO_CATEGORY.get(detector, "unknown")
        }
        # Add LLM fields if present
        if hasattr(self, 'llm_analysis') and self.llm_analysis is not None:
            result["llm_analysis"] = self.llm_analysis
        if hasattr(self, 'llm_status') and self.llm_status is not None:
            result["llm_status"] = self.llm_status
        if hasattr(self, 'llm_validated'):
            result["llm_validated"] = self.llm_validated
        # Also check metadata for llm_analysis if not set directly
        if "llm_analysis" not in result and self.metadata.get("llm_analysis"):
            result["llm_analysis"] = self.metadata["llm_analysis"]
        return result
