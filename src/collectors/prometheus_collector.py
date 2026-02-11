""" 
Collecteur de métriques Prometheus.

Responsable de la collecte régulière des métriques depuis Prometheus
et de l'orchestration de la détection d'anomalies.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import time

from ..utils.prometheus_client import PrometheusClient
from ..models.metric import Metric
from ..models.anomaly import Anomaly
from ..detectors import (
    SpikeDetector,
    StatisticalDetector,
    ThresholdDetector,
    PatternDetector,
    LLMValidator
)
from ..utils.logger import get_logger

logger = get_logger()


class PrometheusCollector:
    """
    Collecteur principal de métriques.
    
    Responsabilités:
    - Se connecter à Prometheus
    - Collecter les métriques configurées
    - Appliquer les détecteurs d'anomalies
    - Agréger les résultats
    """
    
    def __init__(
        self,
        prometheus_url: str,
        detectors_config: Dict[str, Any],
        metrics_to_monitor: List[Dict[str, Any]],
        lookback_window: int = 3600
    ):
        """
        Initialise le collecteur.
        
        Args:
            prometheus_url: URL de Prometheus
            detectors_config: Configuration des détecteurs
            metrics_to_monitor: Liste des métriques à surveiller
            lookback_window: Fenêtre d'analyse en secondes (défaut: 1h)
        """
        self.lookback_window = lookback_window
        self.metrics_to_monitor = metrics_to_monitor
        
        # Initialiser le client Prometheus
        logger.info(f"Connecting to Prometheus at {prometheus_url}")
        self.prom_client = PrometheusClient(url=prometheus_url)
        
        # Vérifier la connexion
        if not self.prom_client.check_connection():
            raise ConnectionError("Cannot connect to Prometheus")
        
        # Initialiser les détecteurs
        self.detectors = self._initialize_detectors(detectors_config)
        
        # Initialiser le validateur LLM (optionnel)
        self.llm_validator = LLMValidator(config=detectors_config.get('llm_validator', {}))
        
        logger.info(
            f"PrometheusCollector initialized with {len(self.detectors)} detectors "
            f"and {len(self.metrics_to_monitor)} metrics to monitor"
        )
        
        if self.llm_validator.is_enabled():
            logger.info("LLM Validator enabled for anomaly enrichment")
    
    def _initialize_detectors(self, config: Dict[str, Any]) -> List:
        """
        Initialise tous les détecteurs configurés.

        Args:
            config: Configuration des détecteurs

        Returns:
            Liste des instances de détecteurs initialisées
        """
        detectors = []

        # Spike Detector
        if config.get('spike_detector', {}).get('enabled', True):
            spike_config = config.get('spike_detector', {})
            detectors.append(SpikeDetector(config=spike_config))

        # Statistical Detector
        if config.get('statistical_detector', {}).get('enabled', True):
            stat_config = config.get('statistical_detector', {})
            detectors.append(StatisticalDetector(config=stat_config))

        # Threshold Detector
        if config.get('threshold_detector', {}).get('enabled', True):
            threshold_config = config.get('threshold_detector', {})
            detectors.append(ThresholdDetector(config=threshold_config))

        # Pattern Detector
        if config.get('pattern_detector', {}).get('enabled', True):
            pattern_config = config.get('pattern_detector', {})
            detectors.append(PatternDetector(config=pattern_config))

        logger.info(f"Initialized {len(detectors)} detectors")
        return detectors

    def collect_and_analyze(self) -> List[Anomaly]:
        """
        Collecte les métriques et détecte les anomalies.

        Étapes:
        1. Collecte des métriques depuis Prometheus
        2. Application des détecteurs statistiques
        3. Validation/enrichissement avec LLM (optionnel)

        Returns:
            Liste de toutes les anomalies détectées
        """
        logger.info("Starting metrics collection and analysis...")

        all_anomalies = []

        # Calculer la fenêtre temporelle
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=self.lookback_window)

        logger.info(
            f"Analyzing metrics from {start_time} to {end_time} "
            f"({self.lookback_window}s window)"
        )

        # Pour chaque métrique configurée
        for metric_config in self.metrics_to_monitor:
            metric_name = metric_config['name']

            try:
                # Collecter la métrique
                metric = self._collect_metric(
                    metric_name,
                    start_time,
                    end_time
                )

                if metric is None or len(metric.values) == 0:
                    logger.warning(f"No data for metric '{metric_name}'")
                    continue

                logger.info(
                    f"Collected {len(metric.values)} points for '{metric_name}'"
                )

                # Appliquer tous les détecteurs
                metric_anomalies = self._detect_anomalies(metric)

                if metric_anomalies:
                    logger.info(
                        f"Found {len(metric_anomalies)} anomalies in '{metric_name}'"
                    )
                    all_anomalies.extend(metric_anomalies)

            except Exception as e:
                logger.error(f"Error processing metric '{metric_name}': {e}")
                continue

        logger.info(
            f"Statistical detection completed: {len(all_anomalies)} anomalies detected"
        )

        # ÉTAPE 3: Validation avec LLM (optionnel)
        if hasattr(self, 'llm_validator') and self.llm_validator.is_enabled() and all_anomalies:
            logger.info("Enriching anomalies with LLM validation...")
            try:
                all_anomalies = self._enrich_with_llm(all_anomalies)
            except Exception as e:
                logger.error(f"Error in LLM enrichment: {e}")

        logger.info(
            f"Collection completed: {len(all_anomalies)} total anomalies after processing"
        )

        return all_anomalies
    
    def _enrich_with_llm(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """
        Enrichit les anomalies avec validation LLM.
        
        Utilise un LLM pour valider et ajouter du contexte intelligent.
        
        Args:
            anomalies: Anomalies détectées statistiquement
            
        Returns:
            Anomalies enrichies
        """
        # Valider avec LLM
        enriched = self.llm_validator.validate_anomalies(
            anomalies,
            keep_all=True  # Garder toutes les anomalies avec analysis LLM
        )
        
        # Convertir back en objets Anomaly
        result = []
        for item in enriched:
            if isinstance(item, Anomaly):
                result.append(item)
            elif isinstance(item, dict):
                # Créer une anomalie depuis le dict enrichi
                anomaly = Anomaly.from_dict(item)
                
                # Ajouter les infos LLM aux metadata
                if item.get('llm_analysis'):
                    anomaly.metadata['llm_analysis'] = item['llm_analysis']
                    anomaly.metadata['llm_validation'] = item.get('llm_validation')
                
                result.append(anomaly)
        
        return result
    
    def _collect_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Metric:
        """
        Collecte une métrique depuis Prometheus.
        
        Args:
            metric_name: Nom de la métrique
            start_time: Début de la période
            end_time: Fin de la période
            
        Returns:
            Objet Metric avec les données
        """
        try:
            metric = self.prom_client.get_metric_range(
                query=metric_name,
                start_time=start_time,
                end_time=end_time,
                step="1m"  # 1 point par minute
            )
            
            return metric
            
        except Exception as e:
            logger.error(f"Error collecting metric '{metric_name}': {e}")
            return None
    
    def _detect_anomalies(self, metric: Metric) -> List[Anomaly]:
        """
        Applique tous les détecteurs sur une métrique.
        
        Args:
            metric: Métrique à analyser
            
        Returns:
            Liste des anomalies détectées par tous les détecteurs
        """
        all_anomalies = []
        
        for detector in self.detectors:
            try:
                anomalies = detector.detect(metric)
                
                if anomalies:
                    logger.debug(f"{detector.name} found {len(anomalies)} anomalies")
                    all_anomalies.extend(anomalies)
                    
            except Exception as e:
                logger.error(f"Error in {detector.name} for metric '{metric.name}': {e}")
                continue
        
        return all_anomalies
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé de l'état des métriques.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        summary = {
            'total_metrics': len(self.metrics_to_monitor),
            'detectors': len(self.detectors),
            'prometheus_url': self.prom_client.url,
            'lookback_window': self.lookback_window
        }
        
        return summary
