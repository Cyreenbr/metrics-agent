"""
Classe de base abstraite pour tous les détecteurs d'anomalies.

Définit l'interface commune que tous les détecteurs doivent implémenter.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.metric import Metric
from ..models.anomaly import Anomaly, Severity
from ..utils.logger import get_logger

logger = get_logger()


class BaseDetector(ABC):
    """
    Classe abstraite de base pour tous les détecteurs.
    
    Chaque détecteur spécifique doit hériter de cette classe
    et implémenter la méthode detect().
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le détecteur.
        
        Args:
            config: Configuration spécifique au détecteur
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.enabled = self.config.get('enabled', True)
        logger.info(f"Initialized detector: {self.name}")
    
    @abstractmethod
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Détecte les anomalies dans une métrique.
        
        Cette méthode doit être implémentée par chaque détecteur.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées (vide si aucune)
        """
        pass
    
    def is_enabled(self) -> bool:
        """Vérifie si le détecteur est activé."""
        return self.enabled
    
    def validate_metric(self, metric: Metric, min_points: int = 2) -> bool:
        """
        Valide qu'une métrique a suffisamment de données.
        
        Args:
            metric: Métrique à valider
            min_points: Nombre minimum de points requis
            
        Returns:
            True si la métrique est valide, False sinon
        """
        if len(metric.values) < min_points:
            logger.warning(
                f"{self.name}: Metric '{metric.name}' has only "
                f"{len(metric.values)} points (minimum: {min_points})"
            )
            return False
        return True
    
    def _create_anomaly(
        self,
        metric: Metric,
        anomaly_type,
        severity: Severity,
        timestamp,
        value: float,
        confidence: float,
        description: str,
        expected_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Anomaly:
        """
        Méthode helper pour créer une anomalie.
        
        Args:
            metric: Métrique source
            anomaly_type: Type d'anomalie
            severity: Sévérité
            timestamp: Moment de l'anomalie
            value: Valeur anormale
            confidence: Niveau de confiance (0-1)
            description: Description
            expected_value: Valeur attendue (optionnel)
            metadata: Données supplémentaires (optionnel)
            
        Returns:
            Objet Anomaly
        """
        return Anomaly(
            metric_name=metric.name,
            anomaly_type=anomaly_type,
            severity=severity,
            timestamp=timestamp,
            value=value,
            detector_name=self.name,
            confidence=confidence,
            expected_value=expected_value,
            description=description,
            metadata=metadata or {}
        )
    
    def __repr__(self) -> str:
        return f"{self.name}(enabled={self.enabled})"