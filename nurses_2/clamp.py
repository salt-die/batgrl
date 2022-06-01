"""
Clamp a value between min and max.
"""
from numbers import Real

def clamp(value, min: Real | None, max: Real | None):
    """
    Clamp a value between min and max.
    """
    if min is not None and value < min:
        return min

    if max is not None and value > max:
        return max

    return value
