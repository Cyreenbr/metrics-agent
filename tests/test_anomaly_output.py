from datetime import datetime, timedelta
from src.models.anomaly import Anomaly, AnomalyType, Severity
import json

def test_orchestrator_output():
    anomaly = Anomaly(
        metric_name="test_latency_ms",
        anomaly_type=AnomalyType.SPIKE,
        severity=Severity.CRITICAL,
        timestamp=datetime.utcnow(),
        value=1200,
        expected_value=400,
        detector_name="spike_detector",
        confidence=0.93,
        description="Latency spike detected",
        labels={"service": "auth", "instance": "auth-1"},
        metadata={
            "threshold": 500,
            "metric_type": "gauge",
            "unit": "ms",
            "lookback_window": "3m"
        }
    )

    output = anomaly.to_orchestrator_dict()

    # Assertions clés
    assert output["source"] == "metrics"
    assert output["metric_name"] == "test_latency_ms"
    assert output["severity"] == "critical"
    assert output["observed_value"] == 1200
    assert output["expected_value"] == 400
    assert output["confidence"] == 0.93
    assert "suggested_category" in output

    print("✅ Orchestrator output OK")
    print(output)

    output = anomaly.to_orchestrator_dict()
    print(json.dumps(output, indent=2))



