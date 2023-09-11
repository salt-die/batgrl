"""
Characters and functions to create smooth bars.
"""
FULL_BLOCK = "█"
VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"


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
