"""
Système de configuration de l'agent.

Charge et gère la configuration depuis les fichiers YAML.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()


class Settings:
    """
    Classe pour charger et gérer la configuration de l'agent.
    
    Charge les fichiers:
    - config.yaml: Configuration principale
    - metrics_rules.yaml: Règles de détection
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialise les settings.
        
        Args:
            config_dir: Répertoire contenant les fichiers de config
        """
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self.rules: Dict[str, Any] = {}
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Charge tous les fichiers de configuration."""
        # Charger config.yaml
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_file}")
        else:
            logger.warning(f"Config file not found: {config_file}")
            self.config = self._get_default_config()
        
        # Charger metrics_rules.yaml
        rules_file = self.config_dir / "metrics_rules.yaml"
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
            logger.info(f"Loaded rules from {rules_file}")
        else:
            logger.warning(f"Rules file not found: {rules_file}")
            self.rules = {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retourne une configuration par défaut."""
        return {
            'prometheus': {
                'url': 'http://localhost:9090',
                'timeout': 30,
                'verify_ssl': False
            },
            'agent': {
                'name': 'metrics-agent',
                'check_interval': 60,
                'lookback_window': 3600
            },
            'logging': {
                'level': 'INFO',
                'format': 'text'
            },
            'detectors': {
                'spike_detector': {'enabled': True},
                'statistical_detector': {'enabled': True},
                'threshold_detector': {'enabled': True},
                'pattern_detector': {'enabled': True}
            }
        }
    
    # Accesseurs pour les différentes sections
    
    @property
    def prometheus_config(self) -> Dict[str, Any]:
        """Configuration Prometheus."""
        return self.config.get('prometheus', {})
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        """Configuration de l'agent."""
        return self.config.get('agent', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Configuration du logging."""
        return self.config.get('logging', {})
    
    @property
    def orchestrator_config(self) -> Dict[str, Any]:
        """Configuration de l'orchestrateur."""
        return self.config.get('orchestrator', {})
    
    @property
    def detectors_config(self) -> Dict[str, Any]:
        """Configuration des détecteurs."""
        return self.config.get('detectors', {})
    
    @property
    def metrics_config(self) -> list:
        """Liste des métriques à surveiller."""
        return self.config.get('metrics', [])
    
    def get_detector_config(self, detector_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un détecteur spécifique.
        
        Args:
            detector_name: Nom du détecteur
            
        Returns:
            Configuration du détecteur
        """
        return self.detectors_config.get(detector_name, {})
    
    def get_metric_rules(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les règles pour une métrique.
        
        Args:
            metric_name: Nom de la métrique
            
        Returns:
            Règles de la métrique ou None
        """
        rules = self.rules.get('rules', {})
        return rules.get(metric_name)
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Récupère les paramètres globaux."""
        return self.rules.get('global_settings', {})
    
    def reload(self):
        """Recharge la configuration depuis les fichiers."""
        logger.info("Reloading configuration...")
        self._load_configuration()
    
    def __repr__(self) -> str:
        return f"Settings(config_dir={self.config_dir})"