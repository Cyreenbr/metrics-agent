"""
Point d'entrée principal de l'agent Metrics.

Ce fichier orchestre l'ensemble du système:
1. Charge la configuration
2. Initialise le logger
3. Démarre le collecteur
4. Envoie les anomalies à l'orchestrateur
"""

import time
import signal
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import List

from .config import Settings
from .collectors import PrometheusCollector
from .models.anomaly import Anomaly
from .utils.logger import LoggerConfig, get_logger
from dotenv import load_dotenv

load_dotenv()

# Module-level logger for imports and initialization
logger = get_logger()

# Variable globale pour le shutdown gracieux
shutdown_requested = False


def signal_handler(sig, frame):
    """Handler pour les signaux SIGINT et SIGTERM."""
    global shutdown_requested
    logger.info("Shutdown signal received, stopping gracefully...")
    shutdown_requested = True


class MetricsAgent:
    """
    Agent principal de détection d'anomalies métriques.
    
    Responsabilités:
    - Orchestrer la collecte de métriques
    - Coordonner les détecteurs
    - Envoyer les résultats à l'orchestrateur
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialise l'agent.
        
        Args:
            config_dir: Répertoire de configuration
        """
        # Charger la configuration
        self.settings = Settings(config_dir=config_dir)
        
        # Configurer le logger
        self._setup_logging()
        
        logger.info("="*60)
        logger.info("Metrics Agent starting...")
        logger.info("="*60)
        
        # Initialiser le collecteur
        self.collector = self._initialize_collector()
        
        # Configuration de l'orchestrateur
        self.orchestrator_url = self.settings.orchestrator_config.get(
            'endpoint',
            'http://localhost:8000/api/anomalies'
        )
        
        # Paramètres de l'agent
        self.check_interval = self.settings.agent_config.get('check_interval', 60)
        
        logger.info(f"Agent '{self.settings.agent_config.get('name')}' initialized")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info(f"Orchestrator: {self.orchestrator_url}")
    
    def _setup_logging(self):
        """Configure le système de logging."""
        log_config = self.settings.logging_config
        
        LoggerConfig(
            level=log_config.get('level', 'INFO'),
            log_file=log_config.get('file'),
            rotation=log_config.get('rotation', '100 MB'),
            retention=log_config.get('retention', '30 days'),
            format_type=log_config.get('format', 'text')
        )
    
    def _initialize_collector(self) -> PrometheusCollector:
        """
        Initialise le collecteur Prometheus.
        
        Returns:
            Instance du PrometheusCollector
        """
        prom_config = self.settings.prometheus_config
        
        collector = PrometheusCollector(
            prometheus_url=prom_config.get('url', 'http://localhost:9090'),
            detectors_config=self.settings.detectors_config,
            metrics_to_monitor=self.settings.metrics_config,
            lookback_window=self.settings.agent_config.get('lookback_window', 3600)
        )
        
        return collector
    
    def run(self):
        """
        Boucle principale de l'agent.
        
        Exécute la collecte et l'analyse à intervalles réguliers.
        """
        global shutdown_requested
        
        logger.info("Agent started - entering main loop")
        
        iteration = 0
        
        while not shutdown_requested:
            iteration += 1
            logger.info(f"--- Iteration {iteration} ---")
            
            try:
                # Collecter et analyser
                anomalies = self.collector.collect_and_analyze()
                
                # Envoyer les anomalies à l'orchestrateur
                if anomalies:
                    self._send_to_orchestrator(anomalies)
                else:
                    logger.info("No anomalies detected in this iteration")
                
                # Afficher un résumé
                self._print_summary(anomalies)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
            
            # Attendre avant la prochaine itération
            logger.info(f"Waiting {self.check_interval}s before next check...")
            
            # Sleep interruptible
            for _ in range(self.check_interval):
                if shutdown_requested:
                    break
                time.sleep(1)
        
        logger.info("Agent stopped")
    
    def _send_to_orchestrator(self, anomalies: List[Anomaly]):
        """
        Envoie les anomalies détectées à l'orchestrateur.
        
        Args:
            anomalies: Liste des anomalies à envoyer
        """
        if not anomalies:
            return
        
        logger.info(f"Sending {len(anomalies)} anomalies to orchestrator...")
        
        # Convertir les anomalies en JSON
        payload = {
            'agent': self.settings.agent_config.get('name', 'metrics-agent'),
            'timestamp': datetime.now().isoformat(),
            'anomalies': [anomaly.to_orchestrator_dict() for anomaly in anomalies]
        }
        
        try:
            # Envoyer la requête POST
            response = requests.post(
                self.orchestrator_url,
                json=payload,
                timeout=self.settings.orchestrator_config.get('timeout', 10)
            )
            
            if response.status_code == 200:
                logger.info("✓ Anomalies successfully sent to orchestrator")
            else:
                logger.error(
                    f"Failed to send anomalies: HTTP {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to orchestrator: {e}")
            # En production, on pourrait stocker localement pour retry
    
    def _print_summary(self, anomalies: List[Anomaly]):
        """
        Affiche un résumé des anomalies détectées.
        
        Args:
            anomalies: Liste des anomalies
        """
        if not anomalies:
            return
        
        # Grouper par sévérité
        by_severity = {}
        for anomaly in anomalies:
            severity = anomaly.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(anomaly)
        
        # Afficher le résumé
        logger.info("--- Anomalies Summary ---")
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                count = len(by_severity[severity])
                logger.info(f"{severity.upper()}: {count} anomalies")
        
        # Afficher les anomalies critiques en détail
        if 'critical' in by_severity:
            logger.warning("CRITICAL anomalies detected:")
            for anomaly in by_severity['critical']:
                logger.warning(f"  - {anomaly.metric_name}: {anomaly.description}")


def main():
    """Point d'entrée principal."""
    # Configurer les handlers de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Déterminer le répertoire de config
    # Si lancé depuis src/, le config est dans ../config
    # Si lancé depuis la racine, le config est dans ./config
    current_dir = Path(__file__).parent.parent
    config_dir = current_dir / "config"
    
    if not config_dir.exists():
        # Essayer le répertoire courant
        config_dir = Path("config")
    
    # Créer et démarrer l'agent
    try:
        agent = MetricsAgent(config_dir=str(config_dir))
        agent.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


# Pour pouvoir lancer avec python -m src.main
if __name__ == "__main__":
    main()