"""Test all API endpoints"""
import requests
import json
import time

base_url = "http://localhost:8000"

print("\n" + "="*70)
print("METRICS AGENT API - COMPREHENSIVE TEST")
print("="*70 + "\n")

# Test 1: Health Check
print("[1] GET /health - Health Check:")
try:
    r = requests.get(f"{base_url}/health", timeout=5)
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(f"  Error: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Test 2: Config
print("\n[2] GET /config - Agent Configuration:")
try:
    r = requests.get(f"{base_url}/config", timeout=5)
    if r.status_code == 200:
        config = r.json()
        print(f"  Agent Name: {config.get('agent', {}).get('name')}")
        print(f"  Prometheus URL: {config.get('prometheus', {}).get('url')}")
        print(f"  Metrics Monitored: {config.get('metrics_monitored')}")
        print(f"  Check Interval: {config.get('check_interval')}s")
    else:
        print(f"  Error: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Detectors
print("\n[3] GET /detectors - Available Detectors:")
try:
    r = requests.get(f"{base_url}/detectors", timeout=5)
    if r.status_code == 200:
        detectors = r.json()
        print(f"  Total: {detectors.get('total_detectors')}")
        for name, info in detectors.get('detectors', {}).items():
            print(f"    - {name}: {info.get('class')}")
    else:
        print(f"  Error: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Test 4: Metrics
print("\n[4] GET /metrics - Monitored Metrics:")
try:
    r = requests.get(f"{base_url}/metrics", timeout=5)
    if r.status_code == 200:
        metrics = r.json()
        print(f"  Total: {metrics.get('total_metrics')}")
        for metric in metrics.get('metrics', []):
            print(f"    - {metric.get('name')}: enabled={metric.get('enabled')}")
    else:
        print(f"  Error: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Test 5: Anomalies
print("\n[5] GET /anomalies - Latest Anomalies:")
try:
    r = requests.get(f"{base_url}/anomalies", timeout=5)
    if r.status_code == 200:
        anomalies = r.json()
        print(f"  Count: {anomalies.get('count')}")
        if anomalies.get('anomalies'):
            for anom in anomalies.get('anomalies', []):
                print(f"    - {anom.get('metric_name')}: {anom.get('severity')} via {anom.get('detector_name')}")
        else:
            print("  (No anomalies detected)")
    else:
        print(f"  Error: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*70)
print("API Endpoints Available (on port 8000):")
print("="*70)
print("  GET  /              - API Info")
print("  GET  /health        - Health check")
print("  GET  /config        - Agent configuration")
print("  GET  /detectors     - List detectors")
print("  GET  /metrics       - List monitored metrics")
print("  GET  /anomalies     - Get latest anomalies")
print("  POST /analyze       - Trigger analysis")
print("  GET  /docs          - Swagger UI (http://localhost:8000/docs)")
print("="*70 + "\n")
