"""
Script de test simple pour l'agent d'anomalies.

Teste l'agent directement sans dépendre d'une API HTTP.
Affiche les anomalies détectées en JSON.
"""

import sys
import json
from datetime import datetime

def main():
    """Test l'agent et affiche les résultats."""
    
    print("\n" + "="*70)
    print("METRICS AGENT - TEST DIRECT")
    print("="*70 + "\n")
    
    try:
        # Importer l'agent
        print("[1] Initializing metrics agent...")
        from src.main import MetricsAgent
        from pathlib import Path
        
        # Trouver le répertoire de config
        current_dir = Path(__file__).parent
        config_dir = current_dir / "config"
        if not config_dir.exists():
            config_dir = Path("config")
        
        # Créer l'agent
        agent = MetricsAgent(config_dir=str(config_dir))
        print("    [OK] Agent initialized successfully\n")
        
        # Collecter et analyser les métriques
        print("[2] Collecting and analyzing metrics...")
        anomalies = agent.collector.collect_and_analyze()
        print(f"    [OK] Collection complete\n")
        
        # Afficher les résultats
        print("[3] Analysis Results:")
        print("    " + "-"*66)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent.settings.agent_config.get("name", "metrics-agent"),
            "anomalies_detected": len(anomalies),
            "detectors_used": [d.__class__.__name__ for d in agent.collector.detectors],
            "anomalies": []
        }
        
        if anomalies:
            print(f"    Found {len(anomalies)} anomalies:\n")
            
            for i, anomaly in enumerate(anomalies, 1):
                anom_dict = anomaly.to_orchestrator_dict()
                result["anomalies"].append(anom_dict)
                
                print(f"    Anomaly #{i}:")
                print(f"      - Metric: {anomaly.metric_name}")
                print(f"      - Severity: {anomaly.severity.value}")
                print(f"      - Value: {anomaly.value}")
                print(f"      - Threshold: {anomaly.threshold}")
                print(f"      - Detector: {anomaly.detector_name}")
                print(f"      - Description: {anomaly.description}")
                if anomaly.recommendations:
                    print(f"      - Recommendations: {', '.join(anomaly.recommendations)}")
                print()
        else:
            print("    No anomalies detected - system operating normally.\n")
        
        # Afficher le JSON complet
        print("\n[4] JSON Output:")
        print("    " + "-"*66)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        print("\n" + "="*70 + "\n")
        
        return 0
        
    except ImportError as e:
        print(f"\n[ERROR] Import failed: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install prometheus-api-client numpy pandas scipy scikit-learn")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
