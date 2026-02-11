"""
Client Prometheus pour la collecte de métriques.

Ce module gère la connexion à Prometheus et l'exécution de requêtes PromQL.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.utils import parse_datetime
import pandas as pd

from ..models.metric import Metric, MetricValue, MetricType
from ..utils.logger import get_logger

logger = get_logger()


class PrometheusClient:
    """
    Client pour interagir avec Prometheus.
    
    Gère la connexion et les requêtes PromQL de manière simplifiée.
    """
    
    def __init__(
        self,
        url: str,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialise le client Prometheus.
        
        Args:
            url: URL du serveur Prometheus (ex: http://localhost:9090)
            timeout: Timeout des requêtes en secondes
            verify_ssl: Vérifier le certificat SSL
        """
        self.url = url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        try:
            self.prom = PrometheusConnect(
                url=url,
                disable_ssl=not verify_ssl
            )
            logger.info(f"Connected to Prometheus at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Prometheus: {e}")
            raise
    
    def check_connection(self) -> bool:
        """
        Vérifie que la connexion à Prometheus fonctionne.
        
        Returns:
            True si la connexion est OK, False sinon
        """
        try:
            # Test simple : récupérer la liste des métriques
            self.prom.all_metrics()
            logger.debug("Prometheus connection check: OK")
            return True
        except Exception as e:
            logger.error(f"Prometheus connection check failed: {e}")
            return False
    
    def get_current_value(self, query: str) -> Optional[float]:
        """
        Récupère la valeur actuelle d'une métrique.
        
        Args:
            query: Requête PromQL (ex: "http_requests_total")
            
        Returns:
            Valeur actuelle ou None si pas de résultat
            
        Example:
            >>> client.get_current_value("up{job='prometheus'}")
            1.0
        """
        try:
            result = self.prom.custom_query(query=query)
            
            if result and len(result) > 0:
                value = float(result[0]['value'][1])
                logger.debug(f"Query '{query}' returned: {value}")
                return value
            
            logger.warning(f"Query '{query}' returned no results")
            return None
            
        except Exception as e:
            logger.error(f"Error executing query '{query}': {e}")
            return None
    
    def get_metric_range(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step: str = "1m"
    ) -> Optional[Metric]:
        """
        Récupère l'historique d'une métrique sur une période.
        
        Args:
            query: Requête PromQL
            start_time: Début de la période
            end_time: Fin de la période
            step: Pas d'échantillonnage (ex: "1m", "5m", "1h")
            
        Returns:
            Objet Metric avec les valeurs ou None
            
        Example:
            >>> start = datetime.now() - timedelta(hours=1)
            >>> end = datetime.now()
            >>> metric = client.get_metric_range("cpu_usage", start, end)
            >>> print(len(metric.values))
            60
        """
        try:
            result = self.prom.custom_query_range(
                query=query,
                start_time=start_time,
                end_time=end_time,
                step=step
            )
            
            if not result or len(result) == 0:
                logger.warning(f"Query '{query}' returned no results")
                return None
            
            # Créer l'objet Metric
            metric = Metric(
                name=query,
                metric_type=MetricType.GAUGE  # On peut améliorer la détection du type
            )
            
            # Extraire les valeurs
            for data_point in result[0]['values']:
                timestamp = datetime.fromtimestamp(data_point[0])
                value = float(data_point[1])
                
                metric.add_value(
                    timestamp=timestamp,
                    value=value,
                    labels=result[0].get('metric', {})
                )
            
            logger.info(f"Collected {len(metric.values)} data points for '{query}'")
            return metric
            
        except Exception as e:
            logger.error(f"Error getting metric range for '{query}': {e}")
            return None
    
    def get_metric_dataframe(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """
        Récupère l'historique sous forme de DataFrame pandas.
        
        Args:
            query: Requête PromQL
            start_time: Début de la période
            end_time: Fin de la période
            step: Pas d'échantillonnage
            
        Returns:
            DataFrame avec colonnes 'timestamp' et 'value'
        """
        metric = self.get_metric_range(query, start_time, end_time, step)
        
        if metric is None or len(metric.values) == 0:
            return None
        
        df = pd.DataFrame([
            {
                'timestamp': v.timestamp,
                'value': v.value
            }
            for v in metric.values
        ])
        
        return df
    
    def list_metrics(self) -> List[str]:
        """
        Liste toutes les métriques disponibles dans Prometheus.
        
        Returns:
            Liste des noms de métriques
        """
        try:
            metrics = self.prom.all_metrics()
            logger.info(f"Found {len(metrics)} metrics in Prometheus")
            return metrics
        except Exception as e:
            logger.error(f"Error listing metrics: {e}")
            return []
    
    def get_metric_metadata(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'une métrique.
        
        Args:
            metric_name: Nom de la métrique
            
        Returns:
            Dictionnaire avec type, help, etc.
        """
        try:
            metadata = self.prom.get_metric_metadata(metric_name)
            return metadata
        except Exception as e:
            logger.error(f"Error getting metadata for '{metric_name}': {e}")
            return None