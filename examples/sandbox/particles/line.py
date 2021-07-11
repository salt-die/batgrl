def line(y1, x1, y2, x2):
    """
    Yield integer coordinates for a line from (y1, x1) to (y2, x2).
    """
    dy = abs(y2 - y1)
    dx = abs(x2 - x1)

    if dy == 0:  # Horizontal
        for x in range(x1, x2 + 1):
            yield y1, x

    elif dx == 0: # Vertical
        for y in range(y1, y2 + 1):
            yield y, x1

    elif dy < dx:  # Low-sloped lines
        dx = x2 - x1
        dy, yi = (2 * (y2 - y1), 1) if y2 >= y1 else (2 * (y1 - y2), -1)

        dif = dy - 2 * dx

        delta = dy - dx
        y = y1
        for x in range(x1, x2 + 1):
            yield y, x

            if delta > 0:
                y += yi
                delta += dif
            else:
                delta += dy

    else:  # High-sloped lines
        dx, xi = (2 * (x2 - x1), 1) if x2 >= x1 else (2 * (x1 - x2), -1)
        dy = y2 - y1

        dif = dx - 2 * dy

        delta = dx - dy
        x = x1
        for y in range(y1, y2 + 1):
            yield y, x

            if delta > 0:
                x += xi
                delta += dif
            else:
                delta += dx
