def clamp(value, min, max):
    """
    Clamp a value between min and max.
    """
    if value < min:
        return min

    if value > max:
        return max

    return value
