"""
Characters and functions to create smooth bars.
"""
FULL_BLOCK = "█"
VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"
UPPER_HALF_BLOCK = "▀"


def create_vertical_bar(max_height: int, proportion: float) -> tuple[int, str, str]:
    """
    Returns number of full blocks and the partial block needed to create a vertical
    bar that fills `max_height` by `proportion`.
    """
    fill, partial = divmod(proportion * max_height, 1)
    if fill == max_height:
        return int(fill) - 1, FULL_BLOCK, FULL_BLOCK
    index_partial = round(partial * (len(VERTICAL_BLOCKS) - 1))
    return int(fill), FULL_BLOCK, VERTICAL_BLOCKS[index_partial]


def create_horizontal_bar(max_width: int, proportion: float) -> tuple[int, str, str]:
    """
    Returns number of full blocks and the partial block needed to create a horizontal
    bar that fills `max_width` by `proportion`.
    """
    fill, partial = divmod(proportion * max_width, 1)
    if fill == max_width:
        return int(fill) - 1, FULL_BLOCK, FULL_BLOCK
    index_partial = round(partial * (len(HORIZONTAL_BLOCKS) - 1))
    return int(fill), FULL_BLOCK, HORIZONTAL_BLOCKS[index_partial]


def create_vertical_bar_offset_half(
    max_height: int, proportion: float
) -> tuple[str, int, str, str]:
    """
    Returns half block character for bottom of the bar, number of full blocks and the
    full block character for the middle of the bar, and the partial block character
    needed to create a vertical bar that fills `max_height` by `proportion`.
    """
    fill, partial = divmod(proportion * max_height, 1)
    partial += 0.5
    if partial > 1:
        partial -= 1
    else:
        fill -= 1

    index_partial = round(partial * (len(VERTICAL_BLOCKS) - 1))
    return UPPER_HALF_BLOCK, int(fill), FULL_BLOCK, VERTICAL_BLOCKS[index_partial]
