# CE QUE GÉNÈRE L'AGENT METRICS

## RÉSUMÉ RAPIDE

L'agent **metrics-agent** génère **ANOMALIES DÉTECTÉES** dans vos métriques Prometheus sous 3 formats:

1. **Objets Python** (List[Anomaly])
2. **JSON** (compatible API REST)
3. **Logs** (fichier logging)

---

## 1. OUTPUT PRINCIPAL: ANOMALIES

### Exemple de 1 anomalie détectée:

```json
{
  "anomaly_id": "a1b2c3d4-e5f6-4789-0123-456789abcdef",
  "metric_name": "test_pattern_metric",
  "anomaly_type": "spike",
  "severity": "high",
  "timestamp": "2026-02-11T17:24:21.548352",
  "value": 140.18922132758104,
  "expected_value": 56.227391265578575,
  "confidence": 0.95,
  "detector_name": "SpikeDetector",
  "description": "Spike detecte: hausse de 149.3%",
  "deviation": 149.3,
  "metadata": {
    "spike_ratio": 2.493,
    "previous_value": 56.2,
    "current_value": 140.2
  },
  "labels": {},
  "start_time": "2026-02-11T17:22:21",
  "end_time": null,
  "recommendations": [
    "Investigate spike cause",
    "Review recent deployments",
    "Check resource utilization"
  ]
}
```

---

## 2. CE QUE L'AGENT GÉNÈRE

### A. En tant que List[Anomaly] (Python Objects)

```python
anomalies = agent.collector.collect_and_analyze()
# anomalies = [Anomaly(...), Anomaly(...), ...]

for anom in anomalies:
    print(anom.metric_name)         # "test_spike_metric"
    print(anom.severity.value)      # "high"
    print(anom.value)               # 140.18922132758104
    print(anom.description)         # "Spike detecte: hausse de 149.3%"
```

### B. En tant que JSON (to_orchestrator_dict)

```python
json_output = [anom.to_orchestrator_dict() for anom in anomalies]
# Convertible avec: json.dumps(json_output)
```

### C. En tant que API Response (via REST)

```bash
curl -X POST http://localhost:8000/analyze
```

Response:
```json
{
  "success": true,
  "timestamp": "2026-02-11T17:24:21.548352",
  "anomalies_count": 1,
  "anomalies": [
    { /* anomaly object */ }
  ],
  "duration_ms": 96.17972373962402
}
```

### D. En tant que Logs

```
2026-02-11 17:24:21 | INFO | src.main | Starting metrics collection...
2026-02-11 17:24:21 | INFO | src.collectors.prometheus_collector | Analyzing metrics from 2026-02-11 17:21:21 to 2026-02-11 17:24:21
2026-02-11 17:24:21 | INFO | src.utils.prometheus_client | Collected 4 data points for 'test_pattern_metric'
2026-02-11 17:24:21 | INFO | src.detectors.spike_detector | SpikeDetector found 1 anomalies in 'test_pattern_metric'
2026-02-11 17:24:21 | INFO | src.main | Sending 1 anomalies to orchestrator...
```

**Fichier:** `logs/metrics-agent.log`

---

## 3. STRUCTURE COMPLÈTE D'UNE ANOMALIE

### Attributs de l'objet Anomaly:

```
Anomaly
├── Identification
│   ├── anomaly_id: str (UUID)
│   ├── metric_name: str
│   └── detector_name: str
│
├── Classification
│   ├── anomaly_type: AnomalyType enum
│   │   ├── SPIKE (pic soudain)
│   │   ├── DROP (chute soudaine)
│   │   ├── STATISTICAL_OUTLIER (aberration stat)
│   │   ├── THRESHOLD_BREACH (dépassement)
│   │   └── PATTERN_ANOMALY (anomalie pattern)
│   └── severity: Severity enum
│       ├── LOW
│       ├── MEDIUM
│       ├── HIGH
│       └── CRITICAL
│
├── Valeurs
│   ├── value: float (valeur anomale actuelle)
│   ├── expected_value: float (valeur attendue)
│   ├── deviation: float (% d'écart)
│   └── confidence: float (confiance: 0.0-1.0)
│
├── Timing
│   ├── timestamp: datetime (moment de l'anomalie)
│   ├── start_time: datetime (optionnel)
│   └── end_time: datetime (optionnel)
│
└── Métadonnées
    ├── description: str (explication)
    ├── metadata: dict (données supplementaires)
    ├── labels: dict (labels Prometheus)
    └── recommendations: list (suggestions de fix)
```

---

## 4. DÉTECTEURS ET CE QU'ILS GÉNÈRENT

| Détecteur | Détecte | Anomaly Type | Exemples |
|-----------|---------|--------------|----------|
| **SpikeDetector** | Augmentation > 100% | SPIKE | CPU spike, Mémoire pic |
| **StatisticalDetector** | Aberrations (Z-score >= 2) | STATISTICAL_OUTLIER | Valeurs anormales statistiquement |
| **ThresholdDetector** | Dépassement de seuil | THRESHOLD_BREACH | Disk 95%, Response time > 2s |
| **PatternDetector** | Anomalie saisonnière | PATTERN_ANOMALY | Pattern inhabituel |
| **LLMValidator** | Validation par LLM (optionnel) | Enrichissement | Contexte, recommandations |

---

## 5. FLUX COMPLET: INPUT -> OUTPUT

```
Prometheus (port 9090)
    |
    | Scrape toutes les 15s
    v
metrics-agent
    |
    +-- Spike Detector ----+
    +-- Statistical Det ---+  -> List[Anomaly]
    +-- Threshold Det -----+
    +-- Pattern Det -------+
    |
    v
Output Formats:
├── Python List[Anomaly] objects
├── JSON array via to_orchestrator_dict()
├── API Response (REST)
├── Logs (logs/metrics-agent.log)
└── Forward to Orchestrator (HTTP POST)
```

---

## 6. UTILISATION DES OUTPUTS

### Via API REST
```bash
# Trigger analysis
curl -X POST http://localhost:8000/analyze

# Get latest anomalies
curl http://localhost:8000/anomalies

# Get config
curl http://localhost:8000/config
```

### Via Python Direct
```python
from src.main import MetricsAgent

agent = MetricsAgent(config_dir='config')
anomalies = agent.collector.collect_and_analyze()

for anom in anomalies:
    print(f"{anom.metric_name}: {anom.severity.value}")
    # Store in database
    # Send to monitoring system
    # Trigger alert
```

### Via Logs
```bash
tail -f logs/metrics-agent.log | grep CRITICAL
```

---

## 7. EXEMPLE COMPLET D'EXÉCUTION

```python
# 1. Initialize
agent = MetricsAgent(config_dir='config')
# Output: Agent initialized, config loaded, detectors ready

# 2. Collect & Analyze
anomalies = agent.collector.collect_and_analyze()
# Output: Metrics collected, analyzed, anomalies extracted

# 3. Output 1: Python objects
for anom in anomalies:
    print(anom)  # Anomaly object

# 4. Output 2: JSON
import json
json_str = json.dumps([a.to_orchestrator_dict() for a in anomalies])
# Output: {"anomaly_id": "...", "metric_name": "...", ...}

# 5. Output 3: Send to API
payload = {
    "agent": "metrics-agent",
    "timestamp": "2026-02-11T17:24:21",
    "anomalies": [a.to_orchestrator_dict() for a in anomalies]
}
requests.post('http://localhost:8000/api/anomalies', json=payload)

# 6. Output 4: Logs
# 2026-02-11 17:24:21 | INFO | Sending 1 anomalies to orchestrator
```

---

## 8. RÉSUMÉ

**L'agent génère:**

| Type | Format | Destination |
|------|--------|------------|
| **Anomalies** | Python List[Anomaly] | Code, scripts |
| **Données** | JSON | API, Orchestrateur, Base de données |
| **Événements** | Logs | logs/metrics-agent.log |
| **Recommandations** | Text + JSON | Incluses dans anomalies |
| **Détails** | Métadonnées | metadata dict |

**Cas d'utilisation:**
- Alerting en temps réel
- Tableau de bord de monitoring
- Intégration orchestrateurs (Kubernetes, Nomad)
- Stockage pour analyse historique
- Machine Learning (détection d'anomalies avancées)
