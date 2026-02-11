"""
Détecteur statistique d'anomalies.

Utilise des méthodes statistiques pour détecter les valeurs aberrantes :
1. Z-Score (nombre d'écarts-types)
2. IQR (Interquartile Range)

Concepts mathématiques:
-----------------------
Z-Score: Mesure combien une valeur s'écarte de la moyenne
Formula: z = (x - μ) / σ
où x = valeur, μ = moyenne, σ = écart-type
Si |z| > 3, la valeur est considérée comme aberrante (99.7% des données normales)

IQR: Méthode robuste basée sur les quartiles
Q1 = 25ème percentile, Q3 = 75ème percentile
IQR = Q3 - Q1
Outliers: valeurs < Q1 - 1.5*IQR ou > Q3 + 1.5*IQR
"""

from typing import List
import numpy as np
from scipy import stats

from .base_detector import BaseDetector
from ..models.metric import Metric
from ..models.anomaly import Anomaly, AnomalyType, Severity
from ..utils.logger import get_logger

logger = get_logger()


class StatisticalDetector(BaseDetector):
    """
    Détecteur d'anomalies basé sur l'analyse statistique.
    
    Utilise deux méthodes complémentaires:
    - Z-Score pour détecter les outliers basés sur l'écart-type
    - IQR pour une détection robuste aux valeurs extrêmes
    
    Configuration:
        - z_score_threshold: Seuil du Z-Score, défaut 3.0
        - iqr_multiplier: Multiplicateur IQR, défaut 1.5
    """
    
    def __init__(self, config=None):
        """
        Initialise le StatisticalDetector.
        
        Args:
            config: Configuration du détecteur
        """
        # Initialiser le parent en premier
        super().__init__(config)
        
        # Paramètres statistiques
        self.z_score_threshold = self.config.get('z_score_threshold', 3.0)
        self.iqr_multiplier = self.config.get('iqr_multiplier', 1.5)
        
        logger.info(
            f"StatisticalDetector configured: z_threshold={self.z_score_threshold}, "
            f"iqr_multiplier={self.iqr_multiplier}"
        )
    
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Détecte les anomalies statistiques dans la métrique.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        if not self.is_enabled():
            return []
        
        # Besoin d'au moins 10 points pour une analyse statistique fiable
        if not self.validate_metric(metric, min_points=10):
            return []
        
        anomalies = []
        values = np.array(metric.get_values_array())
        
        # Méthode 1: Z-Score
        zscore_anomalies = self._detect_zscore_anomalies(metric, values)
        anomalies.extend(zscore_anomalies)
        
        # Méthode 2: IQR
        iqr_anomalies = self._detect_iqr_anomalies(metric, values)
        anomalies.extend(iqr_anomalies)
        
        # Dédupliquer les anomalies (même timestamp)
        anomalies = self._deduplicate_anomalies(anomalies)
        
        logger.info(
            f"StatisticalDetector found {len(anomalies)} anomalies in '{metric.name}'"
        )
        return anomalies
    
    def _detect_zscore_anomalies(
        self,
        metric: Metric,
        values: np.ndarray
    ) -> List[Anomaly]:
        """
        Détecte les anomalies avec la méthode Z-Score.
        
        Args:
            metric: Métrique source
            values: Array de valeurs
            
        Returns:
            Liste d'anomalies détectées
        """
        anomalies = []
        
        # Calculer moyenne et écart-type
        mean = np.mean(values)
        std = np.std(values)
        
        # Si écart-type = 0, toutes les valeurs sont identiques
        if std == 0:
            logger.debug("Z-Score: std=0, no anomalies detected")
            return []
        
        # Calculer le Z-Score pour chaque valeur
        z_scores = np.abs((values - mean) / std)
        
        # Trouver les indices des outliers
        outlier_indices = np.where(z_scores > self.z_score_threshold)[0]
        
        for idx in outlier_indices:
            value = values[idx]
            z_score = z_scores[idx]
            
            # Calculer la sévérité basée sur le Z-Score
            severity = self._calculate_zscore_severity(z_score)
            
            # Calculer la confiance (normalisée entre 0 et 1)
            confidence = min(z_score / 5.0, 1.0)  # 5 écarts-types = confiance max
            
            description = (
                f"Valeur aberrante statistique: {value:.2f} "
                f"(écart de {z_score:.2f} σ de la moyenne {mean:.2f})"
            )
            
            anomaly = self._create_anomaly(
                metric=metric,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=severity,
                timestamp=metric.values[idx].timestamp,
                value=value,
                confidence=confidence,
                description=description,
                expected_value=mean,
                metadata={
                    'z_score': round(float(z_score), 2),
                    'mean': round(float(mean), 2),
                    'std': round(float(std), 2),
                    'detection_method': 'z_score'
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_iqr_anomalies(
        self,
        metric: Metric,
        values: np.ndarray
    ) -> List[Anomaly]:
        """
        Détecte les anomalies avec la méthode IQR (Interquartile Range).
        
        Méthode plus robuste aux valeurs extrêmes que le Z-Score.
        
        Args:
            metric: Métrique source
            values: Array de valeurs
            
        Returns:
            Liste d'anomalies détectées
        """
        anomalies = []
        
        # Calculer les quartiles
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        # Si IQR = 0, distribution très concentrée
        if iqr == 0:
            logger.debug("IQR: iqr=0, no anomalies detected")
            return []
        
        # Calculer les limites
        lower_bound = q1 - (self.iqr_multiplier * iqr)
        upper_bound = q3 + (self.iqr_multiplier * iqr)
        
        # Trouver les outliers
        outlier_indices = np.where(
            (values < lower_bound) | (values > upper_bound)
        )[0]
        
        for idx in outlier_indices:
            value = values[idx]
            
            # Calculer la distance à la limite la plus proche
            if value < lower_bound:
                distance = lower_bound - value
                bound_type = "inférieure"
            else:
                distance = value - upper_bound
                bound_type = "supérieure"
            
            # Normaliser la distance pour calculer la sévérité
            normalized_distance = distance / iqr if iqr > 0 else 0
            severity = self._calculate_iqr_severity(normalized_distance)
            
            # Calculer la confiance
            confidence = min(normalized_distance / 2.0, 1.0)
            
            description = (
                f"Outlier IQR: {value:.2f} dépasse la limite {bound_type} "
                f"({lower_bound:.2f} - {upper_bound:.2f})"
            )
            
            # Valeur attendue = médiane
            expected_value = np.median(values)
            
            anomaly = self._create_anomaly(
                metric=metric,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=severity,
                timestamp=metric.values[idx].timestamp,
                value=value,
                confidence=confidence,
                description=description,
                expected_value=expected_value,
                metadata={
                    'q1': round(float(q1), 2),
                    'q3': round(float(q3), 2),
                    'iqr': round(float(iqr), 2),
                    'lower_bound': round(float(lower_bound), 2),
                    'upper_bound': round(float(upper_bound), 2),
                    'detection_method': 'iqr'
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_zscore_severity(self, z_score: float) -> Severity:
        """Calcule la sévérité basée sur le Z-Score."""
        if z_score >= 5.0:
            return Severity.CRITICAL
        elif z_score >= 4.0:
            return Severity.HIGH
        elif z_score >= 3.5:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _calculate_iqr_severity(self, normalized_distance: float) -> Severity:
        """Calcule la sévérité basée sur la distance IQR normalisée."""
        if normalized_distance >= 3.0:
            return Severity.CRITICAL
        elif normalized_distance >= 2.0:
            return Severity.HIGH
        elif normalized_distance >= 1.0:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """
        Déduplique les anomalies détectées par plusieurs méthodes.
        
        Si une même valeur est détectée par Z-Score et IQR,
        on garde celle avec la plus haute confiance.
        """
        if not anomalies:
            return []
        
        # Grouper par timestamp
        by_timestamp = {}
        for anomaly in anomalies:
            ts = anomaly.timestamp
            if ts not in by_timestamp:
                by_timestamp[ts] = []
            by_timestamp[ts].append(anomaly)
        
        # Garder la meilleure anomalie par timestamp
        deduplicated = []
        for ts, anoms in by_timestamp.items():
            # Prendre celle avec la plus haute confiance
            best = max(anoms, key=lambda a: a.confidence)
            deduplicated.append(best)
        
        return deduplicated