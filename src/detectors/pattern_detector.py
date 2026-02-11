"""
Détecteur de patterns temporels anormaux (Pattern Detector).

Détecte des anomalies basées sur des patterns temporels:
- Changements de tendance (trend)
- Ruptures de saisonnalité
- Comportements cycliques anormaux

Concepts:
---------
1. Tendance: Direction générale (hausse, baisse, stable)
2. Saisonnalité: Patterns qui se répètent (ex: pic chaque jour à 18h)
3. Moyenne mobile: Lisse les variations pour détecter les tendances

Méthodes utilisées:
- Moving Average (MA): Moyenne glissante pour détecter les tendances
- Simple pattern matching: Comparaison avec le comportement historique
"""

from typing import List, Optional
import numpy as np
from scipy import signal

from .base_detector import BaseDetector
from ..models.metric import Metric
from ..models.anomaly import Anomaly, AnomalyType, Severity
from ..utils.logger import get_logger

logger = get_logger()


class PatternDetector(BaseDetector):
    """
    Détecte les anomalies dans les patterns temporels.
    
    Analyse:
    - Tendances (trend changes)
    - Variations cycliques
    - Ruptures de patterns
    
    Configuration:
        - window_size: Taille de la fenêtre d'analyse (nombre de points)
        - seasonality_period: Période de saisonnalité attendue
    """
    
    def __init__(self, config=None):
        """
        Initialise le PatternDetector.
        
        Args:
            config: Configuration du détecteur
        """
        # Initialiser le parent en premier
        super().__init__(config)
        
        # Paramètres
        self.window_size = self.config.get('window_size', 24)
        self.seasonality_period = self.config.get('seasonality_period', 3600)
        
        logger.info(
            f"PatternDetector configured: window_size={self.window_size}, "
            f"seasonality_period={self.seasonality_period}"
        )
    
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Détecte les anomalies de patterns dans la métrique.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        if not self.is_enabled():
            return []
        
        # Besoin d'au moins 2x window_size pour détecter des patterns
        min_points = self.window_size * 2
        if not self.validate_metric(metric, min_points=min_points):
            return []
        
        anomalies = []
        values = np.array(metric.get_values_array())
        
        # Détection 1: Changements de tendance brusques
        trend_anomalies = self._detect_trend_changes(metric, values)
        anomalies.extend(trend_anomalies)
        
        # Détection 2: Déviations par rapport à la moyenne mobile
        ma_anomalies = self._detect_moving_average_deviations(metric, values)
        anomalies.extend(ma_anomalies)
        
        logger.info(
            f"PatternDetector found {len(anomalies)} anomalies in '{metric.name}'"
        )
        return anomalies
    
    def _detect_trend_changes(
        self,
        metric: Metric,
        values: np.ndarray
    ) -> List[Anomaly]:
        """
        Détecte les changements brusques de tendance.
        
        Utilise la dérivée première pour identifier où la tendance change.
        
        Args:
            metric: Métrique source
            values: Array de valeurs
            
        Returns:
            Liste d'anomalies
        """
        anomalies = []
        
        # Calculer la dérivée (gradient)
        gradient = np.gradient(values)
        
        # Lisser le gradient pour réduire le bruit
        window = self.window_size // 2
        smoothed_gradient = np.convolve(
            gradient,
            np.ones(window) / window,
            mode='valid'
        )
        
        # Détecter les changements de signe du gradient (inversions de tendance)
        sign_changes = np.diff(np.sign(smoothed_gradient))
        
        # Trouver les inversions significatives
        significant_changes = np.where(np.abs(sign_changes) > 0)[0]
        
        for idx in significant_changes:
            # Ajuster l'index à cause du smoothing et du diff
            real_idx = idx + window // 2 + 1
            
            if real_idx >= len(values):
                continue
            
            value = values[real_idx]
            
            # Déterminer le type de changement
            before_trend = np.mean(gradient[max(0, real_idx-5):real_idx])
            after_trend = np.mean(gradient[real_idx:min(len(gradient), real_idx+5)])
            
            if before_trend > 0 and after_trend < 0:
                trend_type = "hausse vers baisse"
                severity = Severity.MEDIUM
            elif before_trend < 0 and after_trend > 0:
                trend_type = "baisse vers hausse"
                severity = Severity.MEDIUM
            else:
                continue
            
            description = f"Changement de tendance détecté: {trend_type}"
            
            # Confiance basée sur l'amplitude du changement
            confidence = min(abs(after_trend - before_trend) / np.std(gradient), 1.0)
            
            anomaly = self._create_anomaly(
                metric=metric,
                anomaly_type=AnomalyType.PATTERN_ANOMALY,
                severity=severity,
                timestamp=metric.values[real_idx].timestamp,
                value=value,
                confidence=confidence,
                description=description,
                metadata={
                    'trend_before': round(float(before_trend), 4),
                    'trend_after': round(float(after_trend), 4),
                    'trend_type': trend_type,
                    'detection_method': 'trend_change'
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_moving_average_deviations(
        self,
        metric: Metric,
        values: np.ndarray
    ) -> List[Anomaly]:
        """
        Détecte les déviations significatives par rapport à la moyenne mobile.
        
        La moyenne mobile représente la tendance "normale".
        Les points qui s'en écartent fortement sont anormaux.
        
        Args:
            metric: Métrique source
            values: Array de valeurs
            
        Returns:
            Liste d'anomalies
        """
        anomalies = []
        
        # Calculer la moyenne mobile
        ma = self._calculate_moving_average(values, self.window_size)
        
        # Calculer l'écart-type mobile
        ma_std = self._calculate_moving_std(values, self.window_size)
        
        # Pour chaque point (après la fenêtre initiale)
        start_idx = self.window_size
        
        for i in range(start_idx, len(values)):
            value = values[i]
            expected = ma[i]
            std = ma_std[i]
            
            # Si pas de variabilité, skip
            if std == 0:
                continue
            
            # Calculer la déviation en nombre d'écarts-types
            deviation = abs(value - expected) / std
            
            # Seuil: 2.5 écarts-types
            if deviation > 2.5:
                # Calculer la sévérité
                if deviation > 4.0:
                    severity = Severity.HIGH
                elif deviation > 3.0:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW
                
                # Calculer la confiance
                confidence = min(deviation / 5.0, 1.0)
                
                description = (
                    f"Déviation du pattern normal: valeur={value:.2f}, "
                    f"attendu≈{expected:.2f} (écart de {deviation:.2f}σ)"
                )
                
                anomaly = self._create_anomaly(
                    metric=metric,
                    anomaly_type=AnomalyType.PATTERN_ANOMALY,
                    severity=severity,
                    timestamp=metric.values[i].timestamp,
                    value=value,
                    confidence=confidence,
                    description=description,
                    expected_value=expected,
                    metadata={
                        'deviation_sigma': round(float(deviation), 2),
                        'moving_average': round(float(expected), 2),
                        'moving_std': round(float(std), 2),
                        'detection_method': 'moving_average'
                    }
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_moving_average(
        self,
        values: np.ndarray,
        window: int
    ) -> np.ndarray:
        """
        Calcule la moyenne mobile.
        
        Args:
            values: Valeurs à traiter
            window: Taille de la fenêtre
            
        Returns:
            Array de moyennes mobiles (même taille que values)
        """
        # Utiliser pandas rolling serait plus simple, mais on fait à la main
        ma = np.zeros(len(values))
        
        for i in range(len(values)):
            if i < window:
                # Pour les premiers points, utiliser ce qu'on a
                ma[i] = np.mean(values[:i+1])
            else:
                # Moyenne des 'window' derniers points
                ma[i] = np.mean(values[i-window:i])
        
        return ma
    
    def _calculate_moving_std(
        self,
        values: np.ndarray,
        window: int
    ) -> np.ndarray:
        """
        Calcule l'écart-type mobile.
        
        Args:
            values: Valeurs à traiter
            window: Taille de la fenêtre
            
        Returns:
            Array d'écarts-types mobiles
        """
        std = np.zeros(len(values))
        
        for i in range(len(values)):
            if i < window:
                std[i] = np.std(values[:i+1])
            else:
                std[i] = np.std(values[i-window:i])
        
        return std