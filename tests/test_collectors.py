import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.collectors.prometheus_collector import PrometheusCollector
from src.models.metric import Metric

class TestPrometheusCollector(unittest.TestCase):

    @patch("src.utils.prometheus_client.requests.get")
    def test_collect_metric(self, mock_get):
        # Mock a successful Prometheus API response for a single value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "cpu_usage", "instance": "localhost:8080"},
                        "value": [1678886400, "0.5"]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        collector = PrometheusCollector()
        metrics = collector.collect_metric("cpu_usage", "cpu_usage")

        self.assertEqual(len(metrics), 1)
        self.assertIsInstance(metrics[0], Metric)
        self.assertEqual(metrics[0].name, "cpu_usage")
        self.assertEqual(metrics[0].value, 0.5)
        self.assertEqual(metrics[0].labels["instance"], "localhost:8080")

    @patch("src.utils.prometheus_client.requests.get")
    def test_collect_metric_range(self, mock_get):
        # Mock a successful Prometheus API response for a range of values
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "memory_usage", "instance": "localhost:8080"},
                        "values": [
                            [1678886400, "100"],
                            [1678886460, "105"],
                            [1678886520, "110"]
                        ]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        collector = PrometheusCollector()
        start_time = int(datetime.now().timestamp()) - 300
        end_time = int(datetime.now().timestamp())
        metrics = collector.collect_metric_range("memory_usage", "memory_usage", start_time, end_time, "60s")

        self.assertEqual(len(metrics), 3)
        self.assertIsInstance(metrics[0], Metric)
        self.assertEqual(metrics[0].name, "memory_usage")
        self.assertEqual(metrics[0].value, 100.0)
        self.assertEqual(metrics[2].value, 110.0)

    @patch("src.utils.prometheus_client.requests.get")
    def test_collect_metric_empty_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"resultType": "vector", "result": []}}
        mock_get.return_value = mock_response

        collector = PrometheusCollector()
        metrics = collector.collect_metric("non_existent_metric", "non_existent_metric")
        self.assertEqual(len(metrics), 0)

    @patch("src.utils.prometheus_client.requests.get")
    def test_collect_metric_error_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        collector = PrometheusCollector()
        metrics = collector.collect_metric("error_metric", "error_metric")
        self.assertEqual(len(metrics), 0)

if __name__ == '__main__':
    unittest.main()
