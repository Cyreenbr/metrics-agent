"""
Tests unitaires pour le SpikeDetector.

Ces tests vérifient que le détecteur identifie correctement
les pics et chutes soudaines dans les métriques.
"""

import json
import pytest
from datetime import datetime, timedelta
from src.detectors import SpikeDetector
from src.models.metric import Metric, MetricType
from src.models.anomaly import AnomalyType, Severity


class TestSpikeDetector:
    """Tests du SpikeDetector."""
    
    def setup_method(self):
        """Préparation avant chaque test."""
        self.detector = SpikeDetector(config={
            'enabled': True,
            'sensitivity': 0.8,
            'min_change_percent': 50.0
        })
    
    def test_detect_spike_up(self):
        """Test détection d'un pic (hausse soudaine)."""
        # Créer une métrique avec un spike
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        base_time = datetime.now()
        
        # Valeurs normales puis un spike
        values = [100, 100, 100, 100, 300, 100, 100]  # Spike de +200%
        
        for i, value in enumerate(values):
            metric.add_value(
                timestamp=base_time + timedelta(minutes=i),
                value=value
            )
        
        # Détecter
        anomalies = self.detector.detect(metric)
        
        # Vérifications
        assert len(anomalies) >= 1, "Should detect at least one spike"
        
        spike_anomaly = anomalies[0]
        assert spike_anomaly.anomaly_type == AnomalyType.SPIKE
        assert spike_anomaly.value == 300
        assert spike_anomaly.severity in [Severity.HIGH, Severity.CRITICAL]
    
    def test_detect_drop_down(self):
        """Test détection d'une chute (baisse soudaine)."""
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        base_time = datetime.now()
        
        # Valeurs normales puis une chute
        values = [100, 100, 100, 100, 20, 100, 100]  # Chute de -80%
        
        for i, value in enumerate(values):
            metric.add_value(
                timestamp=base_time + timedelta(minutes=i),
                value=value
            )
        
        anomalies = self.detector.detect(metric)
        
        assert len(anomalies) >= 1
        
        drop_anomaly = anomalies[0]
        assert drop_anomaly.anomaly_type == AnomalyType.DROP
        assert drop_anomaly.value == 20
    
    def test_no_spike_small_change(self):
        """Test qu'un petit changement n'est pas détecté."""
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        base_time = datetime.now()
        
        # Changement de seulement 30% (sous le seuil de 50%)
        values = [100, 100, 130, 100, 100]
        
        for i, value in enumerate(values):
            metric.add_value(
                timestamp=base_time + timedelta(minutes=i),
                value=value
            )
        
        anomalies = self.detector.detect(metric)
        
        assert len(anomalies) == 0, "Should not detect small changes"
    
    def test_multiple_spikes(self):
        """Test détection de plusieurs spikes."""
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        base_time = datetime.now()
        
        # Plusieurs spikes
        values = [100, 250, 100, 300, 100, 200, 100]
        
        for i, value in enumerate(values):
            metric.add_value(
                timestamp=base_time + timedelta(minutes=i),
                value=value
            )
        
        anomalies = self.detector.detect(metric)
        
        # Devrait détecter plusieurs anomalies
        assert len(anomalies) >= 2
    
    def test_disabled_detector(self):
        """Test qu'un détecteur désactivé ne détecte rien."""
        detector = SpikeDetector(config={'enabled': False})
        
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        base_time = datetime.now()
        values = [100, 1000, 100]  # Énorme spike
        
        for i, value in enumerate(values):
            metric.add_value(
                timestamp=base_time + timedelta(minutes=i),
                value=value
            )
        
        anomalies = detector.detect(metric)
        
        assert len(anomalies) == 0, "Disabled detector should return empty"
    
    def test_insufficient_data(self):
        """Test avec pas assez de données."""
        metric = Metric(name="test_metric", metric_type=MetricType.GAUGE)
        
        # Seulement 1 point
        metric.add_value(datetime.now(), 100)
        
        anomalies = self.detector.detect(metric)
        
        assert len(anomalies) == 0, "Should not detect with insufficient data"

