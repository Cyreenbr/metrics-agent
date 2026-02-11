"""
Détecteur de dépassement de seuils (Threshold Detector).

Détecte quand une métrique dépasse des seuils prédéfinis.

Concepts:
---------
- Seuils statiques: Limites fixes (ex: CPU > 90%)
- Seuils multiples: Warning, Critical
- Seuils min/max: Détection de valeurs trop basses ou trop hautes

C'est le détecteur le plus simple mais très utile pour des limites connues.
"""

from typing import List, Dict, Optional
from .base_detector import BaseDetector
from ..models.metric import Metric
from ..models.anomaly import Anomaly, AnomalyType, Severity
from ..utils.logger import get_logger

logger = get_logger()


class ThresholdDetector(BaseDetector):
    """
    Détecte les dépassements de seuils configurés.
    
    Les seuils sont définis dans la configuration par métrique.
    
    Configuration example:
        thresholds:
            cpu_usage:
                warning: 70
                critical: 90
            memory_usage:
                max: 16000000000  # 16 GB
                min: 1000000000   # 1 GB
    """
    
    def __init__(self, config=None):
        """
        Initialise le ThresholdDetector.
        
        Args:
            config: Configuration du détecteur
        """
        # Initialiser le parent en premier
        super().__init__(config)
        
        # Dictionnaire des seuils par métrique
        self.thresholds = self.config.get('thresholds', {})
        
        logger.info(
            f"ThresholdDetector configured with thresholds for "
            f"{len(self.thresholds)} metrics"
        )
    
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Détecte les dépassements de seuils dans la métrique.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        if not self.is_enabled():
            return []
        
        if not self.validate_metric(metric, min_points=1):
            return []
        
        # Récupérer les seuils pour cette métrique
        metric_thresholds = self._get_metric_thresholds(metric.name)
        
        if not metric_thresholds:
            logger.debug(f"No thresholds configured for metric '{metric.name}'")
            return []
        
        anomalies = []
        
        # Analyser chaque valeur
        for metric_value in metric.values:
            value = metric_value.value
            timestamp = metric_value.timestamp
            
            # Vérifier chaque type de seuil
            anomaly = self._check_thresholds(
                metric=metric,
                value=value,
                timestamp=timestamp,
                thresholds=metric_thresholds
            )
            
            if anomaly:
                anomalies.append(anomaly)
        
        logger.info(
            f"ThresholdDetector found {len(anomalies)} anomalies in '{metric.name}'"
        )
        return anomalies
    
    def _get_metric_thresholds(self, metric_name: str) -> Optional[Dict]:
        """
        Récupère les seuils configurés pour une métrique.
        
        Essaie de trouver une correspondance exacte ou par pattern.
        
        Args:
            metric_name: Nom de la métrique
            
        Returns:
            Dictionnaire de seuils ou None
        """
        # Correspondance exacte
        if metric_name in self.thresholds:
            return self.thresholds[metric_name]
        
        # Correspondance par pattern (ex: "http_*" match "http_requests")
        for pattern, thresholds in self.thresholds.items():
            if '*' in pattern:
                pattern_regex = pattern.replace('*', '.*')
                import re
                if re.match(pattern_regex, metric_name):
                    return thresholds
        
        return None
    
    def _check_thresholds(
        self,
        metric: Metric,
        value: float,
        timestamp,
        thresholds: Dict
    ) -> Optional[Anomaly]:
        """
        Vérifie si une valeur dépasse les seuils configurés.
        
        Args:
            metric: Métrique source
            value: Valeur à vérifier
            timestamp: Timestamp de la valeur
            thresholds: Seuils configurés
            
        Returns:
            Anomaly si seuil dépassé, None sinon
        """
        # Seuil CRITICAL (le plus important)
        if 'critical' in thresholds and value >= thresholds['critical']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['critical'],
                threshold_type='critical',
                severity=Severity.CRITICAL
            )
        
        # Seuil WARNING
        if 'warning' in thresholds and value >= thresholds['warning']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['warning'],
                threshold_type='warning',
                severity=Severity.HIGH
            )
        
        # Seuil MAX
        if 'max' in thresholds and value > thresholds['max']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['max'],
                threshold_type='max',
                severity=Severity.HIGH
            )
        
        # Seuil MIN
        if 'min' in thresholds and value < thresholds['min']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['min'],
                threshold_type='min',
                severity=Severity.MEDIUM
            )
        
        # Seuil MAX_RATE (pour les counters)
        if 'max_rate' in thresholds and value > thresholds['max_rate']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['max_rate'],
                threshold_type='max_rate',
                severity=Severity.HIGH
            )
        
        # Seuil MIN_RATE (détection de valeurs trop basses)
        if 'min_rate' in thresholds and value < thresholds['min_rate']:
            return self._create_threshold_anomaly(
                metric=metric,
                value=value,
                timestamp=timestamp,
                threshold_value=thresholds['min_rate'],
                threshold_type='min_rate',
                severity=Severity.MEDIUM
            )
        
        return None
    
    def _create_threshold_anomaly(
        self,
        metric: Metric,
        value: float,
        timestamp,
        threshold_value: float,
        threshold_type: str,
        severity: Severity
    ) -> Anomaly:
        """
        Crée une anomalie de dépassement de seuil.
        
        Args:
            metric: Métrique source
            value: Valeur qui dépasse
            timestamp: Timestamp
            threshold_value: Valeur du seuil
            threshold_type: Type de seuil
            severity: Sévérité
            
        Returns:
            Objet Anomaly
        """
        # Calculer le dépassement
        if threshold_type in ['min', 'min_rate']:
            excess = threshold_value - value
            direction = "en dessous"
        else:
            excess = value - threshold_value
            direction = "au-dessus"
        
        excess_percent = (excess / threshold_value * 100) if threshold_value != 0 else 0
        
        description = (
            f"Seuil {threshold_type.upper()} dépassé: "
            f"valeur={value:.2f} {direction} du seuil={threshold_value:.2f} "
            f"(dépassement de {abs(excess_percent):.1f}%)"
        )
        
        # Confiance = 1.0 pour les seuils (détection certaine)
        confidence = 1.0
        
        return self._create_anomaly(
            metric=metric,
            anomaly_type=AnomalyType.THRESHOLD_BREACH,
            severity=severity,
            timestamp=timestamp,
            value=value,
            confidence=confidence,
            description=description,
            expected_value=threshold_value,
            metadata={
                'threshold_type': threshold_type,
                'threshold_value': threshold_value,
                'excess': round(excess, 2),
                'excess_percent': round(excess_percent, 2)
            }
        )
    
    def add_threshold(
        self,
        metric_name: str,
        warning: Optional[float] = None,
        critical: Optional[float] = None,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ):
        """
        Ajoute ou met à jour les seuils pour une métrique.
        
        Utile pour la configuration dynamique.
        
        Args:
            metric_name: Nom de la métrique
            warning: Seuil warning
            critical: Seuil critical
            min_val: Seuil minimum
            max_val: Seuil maximum
        """
        thresholds = {}
        
        if warning is not None:
            thresholds['warning'] = warning
        if critical is not None:
            thresholds['critical'] = critical
        if min_val is not None:
            thresholds['min'] = min_val
        if max_val is not None:
            thresholds['max'] = max_val
        
        self.thresholds[metric_name] = thresholds
        logger.info(f"Updated thresholds for '{metric_name}': {thresholds}")