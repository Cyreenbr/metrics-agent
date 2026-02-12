#!/usr/bin/env python3
"""
Script pour générer des métriques de test via Pushgateway.

Usage:
    python generate_test_metrics.py
    
Ce script crée des métriques artificielles avec des anomalies pour tester l'agent.
"""

import requests
import time
import random
import math
from datetime import datetime

PUSHGATEWAY_URL = "http://localhost:9091/metrics/job/test_app"

def send_metric(name, value, labels=None):
    """Envoie une métrique au Pushgateway."""
    metric_data = f"{name}"
    
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        metric_data += f"{{{label_str}}}"
    
    metric_data += f" {value}\n"
    
    try:
        response = requests.post(PUSHGATEWAY_URL, data=metric_data)
        if response.status_code == 200:
            print(f"✓ Envoyé: {name}={value}")
        else:
            print(f"✗ Erreur: {response.status_code}")
    except Exception as e:
        print(f"✗ Erreur de connexion: {e}")

def generate_normal_data(base=100, variation=10):
    """Génère une valeur normale avec variation."""
    return base + random.uniform(-variation, variation)

def main():
    print("🚀 Générateur de Métriques de Test")
    print("=" * 50)
    print("\nCe script va générer 3 types de métriques:")
    print("1. Métrique normale (variations légères)")
    print("2. Métrique avec SPIKE")
    print("3. Métrique dépassant un seuil")
    print("\nAppuyez Ctrl+C pour arrêter\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] Iteration {iteration}")
            print("-" * 50)
            
            # Métrique 1: Valeurs normales
            normal_value = generate_normal_data(100, 5)
            send_metric("test_normal_metric", normal_value, {"type": "normal"})
            
            # Métrique 2: Avec spike occasionnel
            if iteration % 10 == 0:  # Spike toutes les 10 itérations
                spike_value = 500  # Énorme spike !
                print("🔥 GÉNÉRATION D'UN SPIKE !")
            else:
                spike_value = generate_normal_data(100, 10)
            send_metric("test_spike_metric", spike_value, {"type": "spike"})
            
            # Métrique 3: Augmentation progressive (threshold)
            threshold_value = 50 + (iteration * 5)  # Augmente progressivement
            send_metric("test_threshold_metric", threshold_value, {"type": "threshold"})
            
            # Métrique 4: Pattern sinusoïdal
            sine_value = 100 + (50 * math.sin(iteration * 0.5))
            send_metric("test_pattern_metric", sine_value, {"type": "pattern"})
            
            # Métrique 5: Request rate (counter simulé)
            requests_total = iteration * random.randint(50, 150)
            send_metric("test_requests_total", requests_total, {
                "status": "200",
                "method": "GET"
            })
            
            print(f"\n💤 Attente 15 secondes...")
            time.sleep(15)
            
    except KeyboardInterrupt:
        print("\n\n✋ Arrêt du générateur")
        print("Les métriques restent disponibles dans Prometheus")

if __name__ == "__main__":
    main()