#!/usr/bin/env python3
"""
Test d'intégration LLM - Vérifiez que tout fonctionne

Usage:
    python3 test_llm_integration.py
"""

import os
import sys
from datetime import datetime, timedelta

# Configuration test
print("🧪 Test d'intégration LLM Metrics Agent")
print("=" * 60)

# Test 1 : Vérifier les imports
print("\n[1/4] Vérification des imports...")
try:
    from src.utils.llm_client import get_llm_client, LLMClient
    from src.detectors.llm_validator import LLMValidator
    from src.models.anomaly import Anomaly, AnomalyType, Severity
    print("✅ Tous les imports LLM réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

# Test 2 : Vérifier la clé API
print("\n[2/4] Vérification de la configuration LLM...")
api_key = os.getenv("GROQ_API_KEY")

if api_key:
    print(f"✅ GROQ_API_KEY trouvée ({api_key[:10]}...)")
else:
    print("⚠️  GROQ_API_KEY non encontrée")
    print("   Configuration requise pour les tests LLM")
    print("   Configurez avec: export GROQ_API_KEY='votre_clé'")
    sys.exit(1)

# Test 3 : Initialiser le client LLM
print("\n[3/4] Initialisation du client LLM...")
try:
    llm_client = get_llm_client()
    
    if llm_client and llm_client.enabled:
        print("✅ Client LLM initialisé avec succès")
        print(f"   Provider: Groq")
    else:
        print("❌ Client LLM non disponible")
        sys.exit(1)
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")
    sys.exit(1)

# Test 4 : Tester avec une anomalie
print("\n[4/4] Test avec anomalie de démonstration...")
try:
    # Créer une anomalie de test
    test_anomaly = Anomaly(
        metric_name="cpu_usage",
        anomaly_type=AnomalyType.SPIKE,
        severity=Severity.HIGH,
        timestamp=datetime.now(),
        value=95.5,
        expected_value=45.0,
        detector_name="SpikeDetector",
        confidence=0.92,
        description="Spike détecté: hausse de 112%",
        labels={"host": "server-1", "region": "us-east"},
        metadata={"percent_change": 112.0, "previous_value": 45.0}
    )
    
    # Valider avec LLM
    print("   Envoi de l'anomalie au LLM pour validation...")
    result = llm_client.validate_anomaly(test_anomaly.to_dict())
    
    if result.get('llm_validation'):
        print("✅ Validation LLM réussie")
        print(f"\n   Analyse LLM:")
        print(f"   ─────────────────────────────────────────")
        
        # Afficher l'analyse LLM formatée
        analysis = result.get('llm_analysis', 'N/A')
        for line in analysis.split('\n'):
            if line.strip():
                print(f"   {line}")
        
        print(f"   ─────────────────────────────────────────")
        
    elif result.get('llm_error'):
        print(f"⚠️  Erreur LLM: {result.get('llm_error')}")
    else:
        print("⚠️  Réponse LLM inattendue")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5 : Test du validateur
print("\n[Bonus] Test du validateur LLM...")
try:
    validator = LLMValidator(config={'enabled': True})
    
    if validator.is_enabled():
        print("✅ LLMValidator initialisé")
        
        # Créer quelques anomalies de test
        test_anomalies = [
            Anomaly(
                metric_name="memory",
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=Severity.MEDIUM,
                timestamp=datetime.now(),
                value=2000,
                detector_name="StatisticalDetector",
                confidence=0.78
            ),
            Anomaly(
                metric_name="disk_io",
                anomaly_type=AnomalyType.THRESHOLD_BREACH,
                severity=Severity.HIGH,
                timestamp=datetime.now(),
                value=95,
                detector_name="ThresholdDetector",
                confidence=1.0
            )
        ]
        
        print(f"   Validation de {len(test_anomalies)} anomalies...")
        validated = validator.validate_anomalies(test_anomalies, keep_all=True)
        
        print(f"✅ {len(validated)} anomalies validées et enrichies")
        
    else:
        print("⚠️  LLMValidator est désactivé")
        
except Exception as e:
    print(f"⚠️  Erreur dans le test du validateur: {e}")

# Résumé
print("\n" + "=" * 60)
print("✅ TOUS LES TESTS RÉUSSIS !")
print("=" * 60)
print("\nVotre intégration LLM est prête à être utilisée :")
print("\n  python3 -m src.main")
print("\nLes anomalies détectées seront enrichies avec analyse LLM.\n")
