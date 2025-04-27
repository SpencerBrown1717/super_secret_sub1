"""Configuration and utility functions for submarine tracking."""
import numpy as np
from typing import Any, Union

def _safe_float(value: Any) -> float:
    """Safely convert a value to float, handling None, NaN, and invalid types."""
    try:
        if value is None:
            return float('nan')
        float_val = float(value)
        return float_val if np.isfinite(float_val) else float('nan')
    except (ValueError, TypeError):
        return float('nan') 