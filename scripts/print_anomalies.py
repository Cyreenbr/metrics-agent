#!/usr/bin/env python3
"""
Script minimal qui collecte les anomalies et imprime leur JSON via to_orchestrator_dict().
"""
import json
import sys
from pathlib import Path

# Assurer que le projet est dans le path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.main import MetricsAgent


def main():
    agent = MetricsAgent(config_dir="config")
    anomalies = agent.collector.collect_and_analyze()

    out = [a.to_orchestrator_dict() for a in anomalies]

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
