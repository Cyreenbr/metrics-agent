# 📊 Metrics Agent - Détection d'Anomalies

Agent intelligent professionnel pour la détection d'anomalies dans les métriques Prometheus.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Vue d'Ensemble

Cet agent surveille vos métriques Prometheus en temps réel et détecte automatiquement 4 types d'anomalies:
- **Pics et chutes soudaines** (Spike Detector)
- **Valeurs statistiquement aberrantes** (Statistical Detector)
- **Dépassements de seuils** (Threshold Detector)
- **Changements de patterns temporels** (Pattern Detector)

**Conçu pour l'apprentissage professionnel** avec documentation extensive et code commenté.

## 🏗️ Architecture

```
metrics-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Point d'entrée
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Configuration
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── prometheus_collector.py # Collecte des métriques
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── base_detector.py       # Classe de base
│   │   ├── spike_detector.py      # Pics/Chutes
│   │   ├── statistical_detector.py # Déviations statistiques
│   │   ├── threshold_detector.py  # Seuils
│   │   └── pattern_detector.py    # Patterns temporels
│   ├── models/
│   │   ├── __init__.py
│   │   ├── anomaly.py            # Modèle d'anomalie
│   │   └── metric.py             # Modèle de métrique
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging
│       └── prometheus_client.py  # Client Prometheus
├── tests/
│   ├── __init__.py
│   ├── test_detectors.py
│   └── test_collectors.py
├── config/
│   ├── config.yaml               # Configuration principale
│   └── metrics_rules.yaml        # Règles de détection
├── requirements.txt
├── docker-compose.yml            # Pour tester avec Prometheus
└── README.md
```

## 🔧 Technologies utilisées (100% gratuites)

- **Python 3.9+** : Langage principal
- **prometheus-api-client** : Client pour Prometheus
- **numpy & scipy** : Calculs statistiques
- **pandas** : Manipulation de données
- **scikit-learn** : Détection d'anomalies ML
- **pyyaml** : Configuration
- **loguru** : Logging avancé

## ✨ Fonctionnalités Principales

### 🎯 Détecteurs d'Anomalies

| Détecteur | Description | Cas d'Usage |
|-----------|-------------|-------------|
| **Spike Detector** | Détecte les changements brusques (>50% par défaut) | Pannes, pics de trafic |
| **Statistical Detector** | Identifie les outliers (Z-Score + IQR) | Comportements anormaux |
| **Threshold Detector** | Alerte sur dépassement de seuils | SLA, limites métier |
| **Pattern Detector** | Détecte les changements de tendance | Dégradations progressives |

### 🛠️ Architecture Professionnelle

- ✅ **Modulaire** : Chaque détecteur est indépendant
- ✅ **Configurable** : Configuration YAML flexible
- ✅ **Testable** : Tests unitaires avec pytest
- ✅ **Observable** : Logging structuré (JSON/Text)
- ✅ **Scalable** : Prêt pour la production
- ✅ **Documenté** : Code commenté + guides détaillés

## 🚀 Démarrage Rapide (5 minutes)

### Prérequis
```bash
- Python 3.9+
- Docker & Docker Compose
- 4GB RAM disponible
```

### Installation

```bash
# 1. Cloner le projet (ou télécharger)
cd metrics-agent

# 2. Démarrer Prometheus
docker-compose up -d

# 3. Lancer l'agent (script automatique)
./start.sh
```

**C'est tout !** L'agent commence à surveiller les métriques.

### Alternative Manuelle
```bash
# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Lancer
python3 -m src.main
```

## 📖 Documentation Complète

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Guide de démarrage détaillé |
| **[LEARNING_PATH.md](LEARNING_PATH.md)** | Plan d'apprentissage 4 semaines |
| **[docs/PROMETHEUS_GUIDE.md](docs/PROMETHEUS_GUIDE.md)** | Maîtriser Prometheus & PromQL |
| **[docs/ALGORITHMS.md](docs/ALGORITHMS.md)** | Algorithmes de détection expliqués |

## 📚 Concepts clés que vous allez apprendre

1. **Connexion à Prometheus** : Requêtes PromQL
2. **Détection statistique** : Z-score, IQR, écart-type
3. **Détection de patterns** : Séries temporelles
4. **Architecture modulaire** : Design patterns (Strategy, Factory)
5. **Tests unitaires** : pytest
6. **Logging professionnel** : Structured logging
7. **Configuration YAML** : Séparation code/config

## 💻 Exemples d'Utilisation

### Exemple 1: Détecter un Spike CPU
```python
from datetime import datetime, timedelta
from src.collectors import PrometheusCollector

# Configuration
collector = PrometheusCollector(
    prometheus_url="http://localhost:9090",
    detectors_config={
        'spike_detector': {'enabled': True, 'min_change_percent': 50}
    },
    metrics_to_monitor=[{'name': 'node_cpu_seconds_total'}]
)

# Analyser
anomalies = collector.collect_and_analyze()

# Afficher les résultats
for anomaly in anomalies:
    print(f"🚨 {anomaly.severity.value.upper()}: {anomaly.description}")
    print(f"   Valeur: {anomaly.value}, Attendu: {anomaly.expected_value}")
    print(f"   Confiance: {anomaly.confidence*100:.1f}%\n")
```

### Exemple 2: Configurer des Seuils Custom
```yaml
# config/metrics_rules.yaml
rules:
  my_business_metric:
    thresholds:
      warning: 1000
      critical: 5000
    detectors:
      - threshold_detector
      - spike_detector
    severity: "high"
```

### Exemple 3: Créer un Détecteur Custom
```python
from src.detectors.base_detector import BaseDetector

class MyCustomDetector(BaseDetector):
    def detect(self, metric):
        anomalies = []
        # Votre logique de détection
        if metric.values[-1].value > 1000:
            anomaly = self._create_anomaly(
                metric=metric,
                anomaly_type=AnomalyType.CUSTOM,
                # ...
            )
            anomalies.append(anomaly)
        return anomalies
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=src --cov-report=html

# Test spécifique
pytest tests/test_spike_detector.py -v
```

## 📊 Exemple de Sortie

```
====================================
Metrics Agent starting...
====================================
[INFO] Connected to Prometheus at http://localhost:9090
[INFO] Initialized 4 detectors
[INFO] Agent started - entering main loop

--- Iteration 1 ---
[INFO] Collecting metrics from 2024-02-10 10:00:00 to 2024-02-10 11:00:00
[INFO] Collected 60 points for 'node_cpu_seconds_total'
[WARNING] SpikeDetector found 1 anomalies
[INFO] ✓ Anomalies successfully sent to orchestrator

--- Anomalies Summary ---
HIGH: 1 anomalies
CRITICAL anomalies detected:
  - node_cpu_seconds_total: Spike détecté: hausse de 185.7%
```

## 🤝 Contribution

Contributions bienvenues ! Pour contribuer:

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Guidelines
- Code style: Black + isort
- Tests: Coverage >80%
- Documentation: Docstrings Google Style
- Commits: Conventional Commits

## 📝 Roadmap

- [ ] Détecteur ML avec Isolation Forest
- [ ] Support multi-sources (InfluxDB, Datadog)
- [ ] Dashboard web temps réel
- [ ] Auto-tuning des seuils
- [ ] Détection de saisonnalité
- [ ] Export vers Grafana
- [ ] API REST pour intégrations

## 🐛 Problèmes Connus

Voir [Issues](https://github.com/votre-repo/issues) pour les bugs connus.

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **Metrics Agent Team** - Développement initial

## 🙏 Remerciements

- Prometheus Team pour l'excellent système de monitoring
- Communauté Python pour les bibliothèques
- Vous, pour utiliser et apprendre avec ce projet !

---

**Fait avec ❤️ pour l'apprentissage et la production**