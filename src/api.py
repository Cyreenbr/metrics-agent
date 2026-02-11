"""
API FastAPI pour tester l'agent de détection d'anomalies.

Point d'entrée HTTP pour:
- Déclencher une analyse manuelle
- Récupérer les anomalies détectées
- Configurer les détecteurs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from .main import MetricsAgent
from .models.anomaly import Anomaly
from .utils.logger import get_logger

# Initialiser FastAPI
app = FastAPI(
    title="Metrics Anomaly Detection Agent API",
    description="API pour tester l'agent de détection d'anomalies de métriques",
    version="1.0.0"
)

# Logger
logger = get_logger()

# Instance globale de l'agent (initialisée au démarrage)
_agent: Optional[MetricsAgent] = None


class AnomalyResponse(BaseModel):
    """Réponse contenant une anomalie détectée."""
    metric_name: str
    detected_at: str
    severity: str
    value: float
    threshold: float
    description: str
    detector: str
    recommendations: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    """Réponse d'une analyse."""
    success: bool
    timestamp: str
    anomalies_count: int
    anomalies: List[AnomalyResponse]
    duration_ms: float


@app.on_event("startup")
async def startup_event():
    """Initialise l'agent au démarrage de l'API."""
    global _agent
    try:
        from pathlib import Path
        current_dir = Path(__file__).parent.parent
        config_dir = current_dir / "config"
        
        if not config_dir.exists():
            config_dir = Path("config")
        
        _agent = MetricsAgent(config_dir=str(config_dir))
        logger.info("Agent initialized successfully via API startup")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """Vérifie la santé de l'API et de l'agent."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_name": _agent.settings.agent_config.get("name", "metrics-agent"),
        "prometheus_url": _agent.settings.prometheus_config.get("url")
    }


@app.post("/analyze")
async def analyze_metrics() -> AnalysisResponse:
    """
    Déclenche une analyse manuelle des métriques.
    
    Retourne les anomalies détectées.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        import time
        start_time = time.time()
        
        # Collecter et analyser les métriques
        anomalies = _agent.collector.collect_and_analyze()
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Convertir les anomalies
        anomalies_response = []
        for anomaly in anomalies:
            anomalies_response.append(
                AnomalyResponse(
                    metric_name=anomaly.metric_name,
                    detected_at=anomaly.timestamp.isoformat() if anomaly.timestamp else datetime.now().isoformat(),
                    severity=anomaly.severity.value,
                    value=anomaly.value,
                    threshold=anomaly.expected_value if anomaly.expected_value else anomaly.value,
                    description=anomaly.description,
                    detector=anomaly.detector_name,
                    recommendations=anomaly.metadata.get('recommendations', []) if anomaly.metadata else None
                )
            )
        
        return AnalysisResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            anomalies_count=len(anomalies),
            anomalies=anomalies_response,
            duration_ms=duration_ms
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies")
async def get_anomalies() -> dict:
    """
    Récupère les dernières anomalies détectées.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        anomalies = _agent.collector.collect_and_analyze()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(anomalies),
            "anomalies": [anomaly.to_orchestrator_dict() for anomaly in anomalies]
        }
    
    except Exception as e:
        logger.error(f"Failed to retrieve anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config() -> dict:
    """Récupère la configuration actuelle de l'agent."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "agent": _agent.settings.agent_config,
        "prometheus": _agent.settings.prometheus_config,
        "detectors": _agent.settings.detectors_config,
        "metrics_monitored": list(_agent.settings.metrics_config.keys()) if _agent.settings.metrics_config else [],
        "check_interval": _agent.check_interval
    }


@app.get("/detectors")
async def get_detectors() -> dict:
    """Liste les détecteurs disponibles et leur configuration."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    detectors_info = {}
    for detector_name, detector in _agent.collector.detectors.items():
        detectors_info[detector_name] = {
            "enabled": True,
            "class": detector.__class__.__name__,
            "config": _agent.settings.detectors_config.get(detector_name, {})
        }
    
    return {
        "total_detectors": len(detectors_info),
        "detectors": detectors_info
    }


@app.get("/metrics")
async def get_monitored_metrics() -> dict:
    """Liste les métriques monitorées."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    metrics_list = []
    if _agent.settings.metrics_config:
        for metric_name, metric_config in _agent.settings.metrics_config.items():
            metrics_list.append({
                "name": metric_name,
                "enabled": metric_config.get("enabled", True),
                "detectors": metric_config.get("detectors", [])
            })
    
    return {
        "total_metrics": len(metrics_list),
        "metrics": metrics_list
    }


@app.post("/analyze_metric/{metric_name}")
async def analyze_specific_metric(metric_name: str) -> dict:
    """
    Analyse une métrique spécifique.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Récupérer les données de cette métrique via Prometheus
        from .utils.prometheus_client import PrometheusClient
        
        prom_client = PrometheusClient(
            url=_agent.settings.prometheus_config.get('url', 'http://localhost:9090')
        )
        
        series_data = prom_client.get_metric_data(metric_name)
        
        if not series_data:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found in Prometheus")
        
        return {
            "metric_name": metric_name,
            "timestamp": datetime.now().isoformat(),
            "data_available": len(series_data) > 0,
            "series_count": len(series_data),
            "data_sample": series_data[:10] if series_data else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze metric '{metric_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint racine
@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API."""
    return {
        "name": "Metrics Anomaly Detection Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
            "anomalies": "GET /anomalies",
            "config": "GET /config",
            "detectors": "GET /detectors",
            "metrics": "GET /metrics",
            "analyze_metric": "POST /analyze_metric/{metric_name}",
            "docs": "/docs (Swagger UI)",
            "redoc": "/redoc (ReDoc)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
