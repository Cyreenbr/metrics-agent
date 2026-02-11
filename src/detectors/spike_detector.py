"""
Détecteur de pics et chutes soudaines (Spike Detector).

Détecte les changements brusques dans les valeurs des métriques.

Algorithme:
-----------
1. Calcule la différence entre chaque point et le précédent
2. Identifie les changements qui dépassent un seuil (en %)
3. Distingue les pics (hausse) des chutes (baisse)

Exemple:
--------
Si une métrique passe de 100 à 200 en un point,
c'est un pic de +100% (très suspect!)
"""

from typing import List
import numpy as np

from .base_detector import BaseDetector
from ..models.metric import Metric
from ..models.anomaly import Anomaly, AnomalyType, Severity
from ..utils.logger import get_logger

logger = get_logger()


class SpikeDetector(BaseDetector):
    """
    Détecte les pics et chutes soudaines dans les métriques.
    
    Configuration:
        - sensitivity: Sensibilité de détection (0-1), défaut 0.8
        - min_change_percent: Changement minimum en % pour alerter, défaut 50
    """
    
    def __init__(self, config=None):
        """
        Initialise le SpikeDetector.
        
        Args:
            config: Configuration du détecteur
        """
        # Initialiser le parent en premier
        super().__init__(config)
        
        # Paramètres de configuration
        self.sensitivity = self.config.get('sensitivity', 0.8)
        self.min_change_percent = self.config.get('min_change_percent', 50.0)
        
        logger.info(
            f"SpikeDetector configured: sensitivity={self.sensitivity}, "
            f"min_change_percent={self.min_change_percent}%"
        )
    
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Détecte les pics et chutes dans la métrique.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        if not self.is_enabled():
            return []
        
        # Validation : besoin d'au moins 2 points
        if not self.validate_metric(metric, min_points=2):
            return []
        
        anomalies = []
        values = metric.get_values_array()
        
        # Calculer les changements percentuels entre chaque point
        for i in range(1, len(values)):
            previous_value = values[i - 1]
            current_value = values[i]
            
            # Éviter la division par zéro
            if previous_value == 0:
                if current_value != 0:
                    # Si on passe de 0 à non-zéro, c'est un spike de 100%
                    percent_change = 100.0
                else:
                    continue
            else:
                percent_change = ((current_value - previous_value) / previous_value) * 100
            
            # Vérifier si le changement dépasse le seuil
            abs_change = abs(percent_change)
            
            if abs_change >= self.min_change_percent:
                # C'est une anomalie !
                
                # Déterminer le type : spike (hausse) ou drop (chute)
                if percent_change > 0:
                    anomaly_type = AnomalyType.SPIKE
                    description = f"Spike détecté: hausse de {percent_change:.1f}%"
                else:
                    anomaly_type = AnomalyType.DROP
                    description = f"Drop détecté: chute de {abs_change:.1f}%"
                
                # Calculer la sévérité basée sur l'amplitude du changement
                severity = self._calculate_severity(abs_change)
                
                # Calculer la confiance basée sur la sensibilité
                confidence = min(abs_change / 100.0, 1.0) * self.sensitivity
                
                # Créer l'anomalie
                anomaly = self._create_anomaly(
                    metric=metric,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    timestamp=metric.values[i].timestamp,
                    value=current_value,
                    confidence=confidence,
                    description=description,
                    expected_value=previous_value,
                    metadata={
                        'percent_change': round(percent_change, 2),
                        'previous_value': previous_value,
                        'change_magnitude': abs_change
                    }
                )
                
                anomalies.append(anomaly)
                logger.info(f"Spike detected: {description} at {anomaly.timestamp}")
        
        logger.info(f"SpikeDetector found {len(anomalies)} anomalies in '{metric.name}'")
        return anomalies
    
    def _calculate_severity(self, change_percent: float) -> Severity:
        """
        Calcule la sévérité basée sur l'amplitude du changement.
        
        Args:
            change_percent: Pourcentage de changement (absolu)
            
        Returns:
            Niveau de sévérité
        """
        if change_percent >= 200:
            return Severity.CRITICAL  # Changement de plus de 200%
        elif change_percent >= 100:
            return Severity.HIGH      # Changement entre 100-200%
        elif change_percent >= 75:
            return Severity.MEDIUM    # Changement entre 75-100%
        else:
            return Severity.LOW       # Changement entre min_change et 75%