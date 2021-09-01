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

@np.vectorize
def character_width(char):
    """
    Return the width of a single unicode glyph, vectorized.
    """
    return wcswidth(char)
