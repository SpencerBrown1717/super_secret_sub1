"""
Public ingestion interface – re-export helpers with *stable* names
so tests and main() can import from `ingestion` or `src.ingestion`.
"""

from .data_loader import (
    load_csv_data,
    fetch_api_data,
    load_data,
    filter_jin_class_subs,
    JIN_SUBMARINES,
)

JIN_CLASS_IDS = JIN_SUBMARINES   # alias main.py expects
__all__ = [
    "load_csv_data", "fetch_api_data", "load_data",
    "filter_jin_class_subs", "JIN_SUBMARINES", "JIN_CLASS_IDS",
]
