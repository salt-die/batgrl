r"""
Terminal rendering.

``render_root`` is responsible for generating ansi from the diffs of the root's double
buffer. Ansi is generated in a bit of a naive way, where the cursor is moved to specific
coordinate then all sgr parameters of the cell is output, for each cell in the diff.
This generates a lot of ansi for large diffs. In the future, this function might decide
to try and output as little ansi as possible, if there is a noticable performance gain
to do so.
"""

import numpy as np

from .gadgets._root import _Root
from .terminal import Vt100Terminal
from .text_tools import char_width


def render_root(root: _Root, terminal: Vt100Terminal) -> None:
    """
    Render root canvas into a terminal.

    Parameters
    ----------
    root : _Root
        Root gadget of gadget tree.
    terminal : Vt100Terminal
        A VT100 terminal.
    """
    if terminal.expect_dsr():
        return

    w = root.width
    inline_column = root.pos.x
    write = terminal._out_buffer.append
    inline = not terminal.in_alternate_screen
    last_y = 0

    resized = root._resized  # ! Must grab before calling root._render
    root._render()
    canvas = root.canvas  # ! Must grab after calling root._render

    if resized:
        ys, xs = np.indices(root.size).reshape(2, -1)
    else:
        diffs = root._last_canvas != canvas
        ys, xs = diffs.nonzero()

    # Save cursor
    write("\x1b7")
    if inline:
        terminal.move_cursor(root._pos)
    for y, x, cell in zip(ys, xs, canvas[ys, xs]):
        (
            char,
            bold,
            italic,
            underline,
            strikethrough,
            overline,
            reverse,
            (fr, fg, fb),  # foreground color
            (br, bg, bb),  # background color
        ) = cell.item()

        # The following conditions ensure full-width glyphs "have enough room" else
        # they are not painted.
        if char == "":
            # `""` is used to indicate the character before it is a full-width
            # character. If this char is appearing in the diffs, we probably need to
            # repaint the full-width character before it, but if the character
            # before it isn't full-width paint whitespace instead.
            if x > 0 and char_width(canvas["char"][y, x - 1].item()) == 2:
                x -= 1
                (
                    char,
                    bold,
                    italic,
                    underline,
                    strikethrough,
                    overline,
                    reverse,
                    (fr, fg, fb),
                    (br, bg, bb),
                ) = canvas[y, x].item()
            else:
                char = " "
        elif (
            x + 1 < w
            and canvas["char"][y, x + 1].item() != ""
            and char_width(char) == 2
        ):
            # If the character is full-width, but the following character isn't
            # `""`, assume the full-width character is being clipped, and paint
            # whitespace instead.
            char = " "

        if inline:
            # Note that `y`s are non-decreasing.
            if last_y < y:
                # Move down `y - last_y` rows.
                write(f"\x1b[{y - last_y}B")
            # Move to column `x + 1`.
            write(f"\x1b[{inline_column + x + 1}G")
        else:
            # Move cursor to position `(y + 1, x + 1)`.
            write(f"\x1b[{y + 1};{x + 1}H")
        last_y = y

        write(
            "\x1b[0;"  # Reset attributes.
            f"{'1;' if bold else ''}"
            f"{'3;' if italic else ''}"
            f"{'4;' if underline else ''}"
            f"{'9;' if strikethrough else ''}"
            f"{'53;' if overline else ''}"
            f"{'7;' if reverse else ''}"
            f"38;2;{fr};{fg};{fb};48;2;{br};{bg};{bb}m"  # Set color pair.
            f"{char}"
        )
    # Restore cursor
    write("\x1b8")
    terminal.flush()
