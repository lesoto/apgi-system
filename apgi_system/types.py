"""Type definitions for the APGI system.

This module provides type aliases and custom types used throughout the APGI system
to improve type safety and code clarity.
"""

import numpy as np
import numpy.typing as npt

from typing import Dict, Any

# Array types
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

# Configuration types
ConfigDict = Dict[str, Any]
