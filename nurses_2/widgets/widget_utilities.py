def clamp(value, min=0.0, max=1.0):
    """
    Return `value` if it's between `min` and `max`, else return
    `min` if `value` is less than `min` or `max` if `value` is
    greater than `max`.
    """
    if value < min:
        return min
    if value > max:
        return max
    return value
