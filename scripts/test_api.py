"""
Script de test de l'API pour tester l'agent de détection d'anomalies.

Teste les endpoints principaux et affiche les résultats en JSON.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8001"
TIMEOUT = 30

class APITester:
    """Testeur d'API pour l'agent d'anomalies."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Effectue une requête HTTP."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=TIMEOUT, **kwargs)
            elif method == "POST":
                response = requests.post(url, timeout=TIMEOUT, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
            }
        
        except requests.exceptions.ConnectTimeout:
            return {
                "success": False,
                "error": f"Connection timeout. Is the API running at {self.base_url}?",
                "hint": f"Run: uvicorn src.api:app --host 0.0.0.0 --port 8001 --reload"
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "hint": f"Run: uvicorn src.api:app --host 0.0.0.0 --port 8001 --reload"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_root(self):
        """Teste l'endpoint racine."""
        print("\n" + "="*60)
        print("TEST 1: GET / (Root endpoint)")
        print("="*60)
        
        result = self._make_request("GET", "/")
        self.results.append(("Root", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
            if "hint" in result:
                print("Hint:", result["hint"])
        
        return result["success"]
    
    def test_health(self):
        """Teste le health check."""
        print("\n" + "="*60)
        print("TEST 2: GET /health (Health check)")
        print("="*60)
        
        result = self._make_request("GET", "/health")
        self.results.append(("Health", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
            if "hint" in result:
                print("Hint:", result["hint"])
        
        return result["success"]
    
    def test_config(self):
        """Teste la récupération de la configuration."""
        print("\n" + "="*60)
        print("TEST 3: GET /config (Agent configuration)")
        print("="*60)
        
        result = self._make_request("GET", "/config")
        self.results.append(("Config", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
        
        return result["success"]
    
    def test_detectors(self):
        """Teste la récupération des détecteurs."""
        print("\n" + "="*60)
        print("TEST 4: GET /detectors (Available detectors)")
        print("="*60)
        
        result = self._make_request("GET", "/detectors")
        self.results.append(("Detectors", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
        
        return result["success"]
    
    def test_metrics(self):
        """Teste la récupération des métriques monitorées."""
        print("\n" + "="*60)
        print("TEST 5: GET /metrics (Monitored metrics)")
        print("="*60)
        
        result = self._make_request("GET", "/metrics")
        self.results.append(("Metrics", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
        
        return result["success"]
    
    def test_analyze(self):
        """Teste une analyse manuelle."""
        print("\n" + "="*60)
        print("TEST 6: POST /analyze (Manual analysis)")
        print("="*60)
        
        result = self._make_request("POST", "/analyze")
        self.results.append(("Analyze", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
        
        return result["success"]
    
    def test_anomalies(self):
        """Teste la récupération des anomalies."""
        print("\n" + "="*60)
        print("TEST 7: GET /anomalies (Detected anomalies)")
        print("="*60)
        
        result = self._make_request("GET", "/anomalies")
        self.results.append(("Anomalies", result))
        
        if result["success"]:
            print("Status:", result["status_code"])
            print("Response:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print("Error:", result["error"])
        
        return result["success"]
    
    def print_summary(self):
        """Affiche un résumé des tests."""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        success_count = sum(1 for _, result in self.results if result.get("success", False))
        total_count = len(self.results)
        
        print(f"\nTests passed: {success_count}/{total_count}\n")
        
        for test_name, result in self.results:
            status = "PASS" if result.get("success") else "FAIL"
            print(f"  {test_name}: {status}")
        
        return success_count == total_count


def main():
    """Fonction principale."""
    print("\n" + "="*60)
    print("METRICS AGENT API TEST SUITE")
    print("="*60)
    
    tester = APITester()
    
    # Exécuter les tests
    all_pass = True
    
    try:
        # Test 1: Root
        if not tester.test_root():
            all_pass = False
            print("\nWarning: API is not responding. Make sure it's running:")
            print("  cd c:/Users/User/projects/metrics-agent/metrics-agent")
            print("  python -m uvicorn src.api:app --host 0.0.0.0 --port 8001 --reload")
            sys.exit(1)
        
        # Test 2: Health
        if not tester.test_health():
            all_pass = False
        
        # Test 3: Config
        if not tester.test_config():
            all_pass = False
        
        # Test 4: Detectors
        if not tester.test_detectors():
            all_pass = False
        
        # Test 5: Metrics
        if not tester.test_metrics():
            all_pass = False
        
        # Test 6: Analyze (main test)
        if not tester.test_analyze():
            print("\nNote: Analysis might have failed if Prometheus is not running.")
            print("Make sure Prometheus is accessible at the configured URL.")
        
        # Test 7: Anomalies
        if not tester.test_anomalies():
            all_pass = False
        
        # Summary
        tester.print_summary()
        
        if all_pass:
            print("\nAll tests passed!")
            sys.exit(0)
        else:
            print("\nSome tests failed.")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
