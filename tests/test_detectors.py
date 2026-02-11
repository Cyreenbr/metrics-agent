import unittest
from datetime import datetime, timedelta
from src.models.metric import Metric
from src.detectors.spike_detector import SpikeDetector
from src.detectors.statistical_detector import StatisticalDetector
from src.detectors.threshold_detector import ThresholdDetector
from src.detectors.pattern_detector import PatternDetector

class TestDetectors(unittest.TestCase):

    def test_spike_detector(self):
        detector = SpikeDetector(name="test_spike", config={"threshold_factor": 2.0, "window_size": 3})
        metrics = [
            Metric(name="cpu_usage", timestamp=datetime.now() - timedelta(minutes=5), value=10),
            Metric(name="cpu_usage", timestamp=datetime.now() - timedelta(minutes=4), value=12),
            Metric(name="cpu_usage", timestamp=datetime.now() - timedelta(minutes=3), value=11),
            Metric(name="cpu_usage", timestamp=datetime.now() - timedelta(minutes=2), value=100), # Spike
            Metric(name="cpu_usage", timestamp=datetime.now() - timedelta(minutes=1), value=13),
        ]
        anomalies = detector.detect(metrics)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].value, 100)

    def test_statistical_detector(self):
        detector = StatisticalDetector(name="test_statistical", config={"std_dev_factor": 1.5, "window_size": 4})
        metrics = [
            Metric(name="memory_usage", timestamp=datetime.now() - timedelta(minutes=5), value=50),
            Metric(name="memory_usage", timestamp=datetime.now() - timedelta(minutes=4), value=52),
            Metric(name="memory_usage", timestamp=datetime.now() - timedelta(minutes=3), value=51),
            Metric(name="memory_usage", timestamp=datetime.now() - timedelta(minutes=2), value=53),
            Metric(name="memory_usage", timestamp=datetime.now() - timedelta(minutes=1), value=100), # Anomaly
        ]
        anomalies = detector.detect(metrics)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].value, 100)

    def test_threshold_detector(self):
        detector = ThresholdDetector(name="test_threshold", config={"upper_threshold": 90, "lower_threshold": 10})
        metrics = [
            Metric(name="disk_io", timestamp=datetime.now() - timedelta(minutes=2), value=5),
            Metric(name="disk_io", timestamp=datetime.now() - timedelta(minutes=1), value=95), # Anomaly
        ]
        anomalies = detector.detect(metrics)
        self.assertEqual(len(anomalies), 2)
        self.assertEqual(anomalies[0].value, 5)
        self.assertEqual(anomalies[1].value, 95)

    def test_pattern_detector(self):
        detector = PatternDetector(name="test_pattern", config={"window_size": 3, "deviation_factor": 0.5})
        metrics = [
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=6), value=100),
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=5), value=110),
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=4), value=105),
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=3), value=100),
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=2), value=110),
            Metric(name="daily_traffic", timestamp=datetime.now() - timedelta(days=1), value=105),
            Metric(name="daily_traffic", timestamp=datetime.now(), value=500), # Pattern break
        ]
        anomalies = detector.detect(metrics)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].value, 500)

if __name__ == '__main__':
    unittest.main()
