#!/usr/bin/env python3
"""
Exemple complét de ce que génère l'agent Metrics.

Ce script montre:
1. Ce que l'agent détecte (anomalies)
2. Format de sortie JSON
3. Attributs générés pour chaque anomalie
4. Comment utiliser les résultats
"""

import json
from datetime import datetime
from src.main import MetricsAgent

def main():
    print("\n" + "="*80)
    print("CE QUE GÉNÈRE L'AGENT METRICS - OUTPUT COMPLET")
    print("="*80 + "\n")
    
    # ----- SECTION 1: INITIATE L'AGENT -----
    print("[1] INITIALISATION DE L'AGENT")
    print("    " + "-"*76)
    agent = MetricsAgent(config_dir='config')
    print("    [OK] Agent initialized avec:")
    print(f"         - 4 Detectors: Spike, Statistical, Threshold, Pattern")
    print(f"         - 5 Metrics: test_normal, test_spike, test_threshold, test_pattern, test_requests_total")
    print(f"         - Prometheus: {agent.settings.prometheus_config.get('url')}")
    
    # ----- SECTION 2: COLLECT & ANALYZE -----
    print("\n[2] COLLECTION ET ANALYSE DES METRIQUES")
    print("    " + "-"*76)
    anomalies = agent.collector.collect_and_analyze()
    print(f"    [OK] Analysis complete: {len(anomalies)} anomalies detected")
    
    # ----- SECTION 3: FORMAT OBJET PYTHON -----
    print("\n[3] ANOMALIES EN TANT QU'OBJETS PYTHON")
    print("    " + "-"*76)
    
    if anomalies:
        for i, anom in enumerate(anomalies, 1):
            print(f"\n    Anomaly #{i}:")
            print(f"      anomaly_id: {anom.anomaly_id}")
            print(f"      metric_name: {anom.metric_name}")
            print(f"      anomaly_type: {anom.anomaly_type.value}")
            print(f"      severity: {anom.severity.value}")
            print(f"      timestamp: {anom.timestamp}")
            print(f"      value: {anom.value:.4f}")
            print(f"      expected_value: {anom.expected_value}")
            print(f"      confidence: {anom.confidence}")
            print(f"      detector_name: {anom.detector_name}")
            print(f"      description: {anom.description}")
            print(f"      deviation: {anom.deviation}%")
            print(f"      metadata: {anom.metadata}")
            print(f"      labels: {anom.labels}")
            print(f"      start_time: {anom.start_time}")
            print(f"      end_time: {anom.end_time}")
    else:
        print("    (Aucune anomalie detectée - système opérationnel normal)")
    
    # ----- SECTION 4: FORMAT JSON -----
    print("\n[4] ANOMALIES EN FORMAT JSON (to_orchestrator_dict())")
    print("    " + "-"*76)
    
    if anomalies:
        json_output = [anom.to_orchestrator_dict() for anom in anomalies]
        print(json.dumps(json_output, indent=2))
    else:
        print("    []")
    
    # ----- SECTION 5: PAYLOAD API -----
    print("\n[5] PAYLOAD ENVOYÉ A L'API/ORCHESTRATEUR")
    print("    " + "-"*76)
    
    api_payload = {
        "agent": agent.settings.agent_config.get('name', 'metrics-agent'),
        "timestamp": datetime.now().isoformat(),
        "anomalies": [anom.to_orchestrator_dict() for anom in anomalies]
    }
    print(json.dumps(api_payload, indent=2))
    
    # ----- SECTION 6: LOGS GENERATES -----
    print("\n[6] LOGS GENERES (dans logs/metrics-agent.log)")
    print("    " + "-"*76)
    print("    - Configuration loaded")
    print("    - Prometheus connected")
    print("    - Detectors initialized")
    print("    - Metrics collected")
    print("    - Analysis complete")
    print("    - Anomalies detected/processed")
    
    # ----- SECTION 7: FICHIERS GENERES -----
    print("\n[7] FICHIERS/RESSOURCES GENERES")
    print("    " + "-"*76)
    print("    Output:")
    print("    - Anomaly objects (Python)")
    print("    - JSON array of anomalies")
    print("    - API payload (POST to /api/anomalies)")
    print("    ")
    print("    Files modified:")
    print("    - logs/metrics-agent.log (nouvelle entrée)")
    print("    ")
    print("    Environment:")
    print("    - .env (configuration API keys, si nécessaire)")
    
    # ----- SECTION 8: CAS D'UTILISATION -----
    print("\n[8] CAS D'UTILISATION DES OUTPUTS")
    print("    " + "-"*76)
    print("""
    1. API REST
       POST http://localhost:8000/analyze
       → Retourne: AnalysisResponse (JSON)
    
    2. Direct Python
       agent.collector.collect_and_analyze()
       → Retourne: List[Anomaly]
       → Chaque anomaly a .to_orchestrator_dict()
    
    3. Forwarding à Orchestrateur
       POST http://localhost:8000/api/anomalies
       → Payload: {agent, timestamp, anomalies[]}
    
    4. Logging
       - Tous les events écris dans logs/metrics-agent.log
       - Format: timestamp | LEVEL | module | message
    
    5. Monitoring Dashboard
       - Anomalies JSON peuvent être affichées dans UI
       - Métriques peuvent être enregistrées dans TSDB
    """)
    
    # ----- SECTION 9: TYPES DE DONNEES -----
    print("\n[9] TYPES DE DONNEES GENERES")
    print("    " + "-"*76)
    print("""
    Anomaly Object Attributes:
    ├── Identification
    │   ├── anomaly_id: str (UUID4)
    │   ├── metric_name: str
    │   └── detector_name: str
    │
    ├── Anomaly Info
    │   ├── anomaly_type: AnomalyType (enum)
    │   │   ├── SPIKE
    │   │   ├── DROP
    │   │   ├── STATISTICAL_OUTLIER
    │   │   ├── THRESHOLD_BREACH
    │   │   └── PATTERN_ANOMALY
    │   ├── severity: Severity (enum)
    │   │   ├── LOW
    │   │   ├── MEDIUM
    │   │   ├── HIGH
    │   │   └── CRITICAL
    │   └── confidence: float (0.0-1.0)
    │
    ├── Values
    │   ├── value: float (valeur anomale)
    │   ├── expected_value: float (valeur attendue)
    │   └── deviation: float (% écart)
    │
    ├── Timing
    │   ├── timestamp: datetime
    │   ├── start_time: datetime (optionnel)
    │   └── end_time: datetime (optionnel)
    │
    ├── Metadata
    │   ├── description: str (explication)
    │   ├── metadata: dict (données supplémentaires)
    │   ├── labels: dict (labels Prometheus)
    │   └── recommendations: list (suggestions de fix)
    """)
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
