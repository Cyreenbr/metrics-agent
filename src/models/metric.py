"""
Modèle de données pour les métriques Prometheus.

Ce module définit la structure des métriques collectées.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class MetricType(Enum):
    """Types de métriques Prometheus."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """
    Représente une valeur de métrique à un instant donné.
    
    Attributes:
        timestamp: Moment de la mesure
        value: Valeur de la métrique
        labels: Labels associés (ex: {"status": "200", "method": "GET"})
    """
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"MetricValue(timestamp={self.timestamp}, value={self.value}, labels={self.labels})"


@dataclass
class Metric:
    """
    Représente une métrique complète avec son historique.
    
    Attributes:
        name: Nom de la métrique (ex: "http_requests_total")
        metric_type: Type de métrique
        values: Liste des valeurs collectées
        description: Description de la métrique
    """
    name: str
    metric_type: MetricType
    values: List[MetricValue] = field(default_factory=list)
    description: Optional[str] = None
    
    def add_value(self, timestamp: datetime, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Ajoute une nouvelle valeur à la métrique.
        
        Args:
            timestamp: Moment de la mesure
            value: Valeur mesurée
            labels: Labels optionnels
        """
        metric_value = MetricValue(
            timestamp=timestamp,
            value=value,
            labels=labels or {}
        )
        self.values.append(metric_value)
    
    def get_values_array(self) -> List[float]:
        """Retourne uniquement les valeurs (sans timestamps)."""
        return [v.value for v in self.values]
    
    def get_timestamps_array(self) -> List[datetime]:
        """Retourne uniquement les timestamps."""
        return [v.timestamp for v in self.values]
    
    def get_latest_value(self) -> Optional[MetricValue]:
        """Retourne la dernière valeur collectée."""
        return self.values[-1] if self.values else None
    
    def __len__(self) -> int:
        """Retourne le nombre de valeurs."""
        return len(self.values)
    
    def __repr__(self) -> str:
        return f"Metric(name={self.name}, type={self.metric_type.value}, points={len(self.values)})"