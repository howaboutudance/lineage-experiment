"""OpenLineage emission helpers.

Wraps the openlineage-python client to emit structured lineage events at
ingestion and derived-endpoint boundaries, forming the provenance spine that
connects raw FCS/MSD payloads to final endpoint values.
"""
