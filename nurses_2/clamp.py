"""
Clamp a value between a min and a max.
"""
from numbers import Real


def clamp(value: Real, min: Real | None, max: Real | None) -> Real:
    """
    If `value` is less than `min`, returns `min`; otherwise if `max` is less than
    `value`, returns `max`; otherwise returns `value`.

    Parameters
    ----------
    value : Real
        Value to clamp.
    min : Real | None
        Minimum of clamped value.
    max : Real | None
        Maximum of clamped value.

    Returns
    -------
    Real
        A value between `min` and `max`, inclusive.
    """
    if min is not None and value < min:
        return min

    if max is not None and value > max:
        return max

    return value
