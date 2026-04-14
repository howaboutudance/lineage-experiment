"""Ingestion layer: custody-transfer boundary checks.

pytest ingestion contracts live here and in test/test_ingestion/.
Each function that transforms or accepts data should emit an OpenLineage event
via lineage_experiment.lineage before returning.
"""
