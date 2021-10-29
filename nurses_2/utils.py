import numpy as np
from wcwidth import wcswidth

def clamp(value, min, max):
    """
    Clamp a value between min and max.
    """
    if value < min:
        return min

    if value > max:
        return max

    return value

character_width = np.vectorize(wcswidth)
"""
Return the width of a single unicode glyph, vectorized.
"""
