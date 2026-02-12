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
python -m venv venv
.\venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Lancer
python -m src.main
```
