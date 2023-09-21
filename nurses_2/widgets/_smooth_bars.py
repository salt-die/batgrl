"""
Characters and functions to create smooth bars.
"""
VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"


def _create_smooth_bar(
    blocks: str,
    max_length: int,
    proportion: float,
    offset: float,
):
    """
    Create a smooth bar with given blocks.
    """
    if offset >= 1 or offset < 0:
        raise ValueError(
            f"Offset should greater than or equal to 0 and less than 1, but {offset} "
            "was given."
        )

    block_indices = len(blocks) - 1

    fill, partial = divmod(proportion * max_length, 1)
    fill = int(fill)

    if offset == 0.0:
        if fill == max_length:
            return (blocks[-1],) * fill

        index_partial = round(partial * block_indices)
        partial_block = blocks[index_partial]
        return (*(blocks[-1],) * fill, partial_block)

    partial += offset
    if partial > 1:
        partial -= 1
    else:
        fill -= 1

    index_offset = round(offset * block_indices)
    index_partial = round(partial * block_indices)
    offset_block = blocks[index_offset]
    partial_block = blocks[index_partial]
    return (offset_block, *(blocks[-1],) * fill, partial_block)


def create_vertical_bar(
    max_height: int,
    proportion: float,
    offset: float = 0.0,
    reversed: bool = False,
) -> tuple[str, ...]:
    """
    Create a vertical bar that's some proportion of max_height at an offset.

    Offset bars will return a minimum of 2 characters and the first character of the bar
    should have it's colors reversed (or, if bar is reversed, all colors should be
    reversed except first character).
    """
    blocks = VERTICAL_BLOCKS[::-1] if reversed else VERTICAL_BLOCKS
    return _create_smooth_bar(blocks, max_height, proportion, offset)


def create_horizontal_bar(
    max_width: int, proportion: float, offset: float = 0.0
) -> tuple[str, ...]:
    """
    Create a horizontal bar that's some proportion of max_width at an offset.
    The first character of the bar should have it's colors reversed.

    Offset bars will return a minimum of 2 characters and the first character of the bar
    should have it's colors reversed.
    """
    return _create_smooth_bar(HORIZONTAL_BLOCKS, max_width, proportion, offset)
