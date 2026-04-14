"""Synthetic data generators for biomedical data modeled on CRO transfer pipelines.

Generators are deterministic (seeded) so test runs are reproducible.
Covers: FCS-equivalent payloads, MSD/Luminex-equivalent exports, CRO manifest files,
and derived endpoint tables — each with injected known failure modes.
"""
