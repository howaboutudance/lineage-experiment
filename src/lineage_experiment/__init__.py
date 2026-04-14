"""Experimental layered data quality and lineage architecture using synthetic biomedical data.

Validates whether the 2026 tooling stack (Delta Lake, OpenLineage, DuckDB, Great Expectations)
can express the CRO data custody transfer architecture that was built ad-hoc at BMS (2018-2021).

Subpackages:
    synthetic:  Deterministic seeded generators for FCS, MSD, and manifest synthetic data.
    ingestion:  Custody-transfer boundary contracts and OpenLineage emission.
    derived:    Aggregation pipeline and Great Expectations handoff contracts.
    lineage:    OpenLineage client helpers for structured provenance emission.
"""
