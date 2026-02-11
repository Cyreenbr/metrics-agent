"""
Metrics Agent - Système de détection d'anomalies pour métriques Prometheus.

Ce package contient:
- collectors: Collecteurs de métriques
- detectors: Détecteurs d'anomalies
- models: Modèles de données
- config: Système de configuration
- utils: Utilitaires (logger, client Prometheus)
"""

__version__ = "1.0.0"
__author__ = "Metrics Agent Team"

from .main import MetricsAgent

__all__ = ['MetricsAgent']