"""
Root widget.
"""
import numpy as np
from numpy.typing import NDArray
from wcwidth import wcwidth

from .widget import Char, ColorPair, Point, Region, Widget, style_char


class _Root(Widget):
    """
    Root widget of the widget tree.

    Instantiated only by :class:`nurses_2.app.App`.
    """

    def __init__(
        self,
        app,
        env_out,
        background_char: str,
        background_color_pair: ColorPair,
    ):
        self._app = app
        self.children = []
        self.env_out = env_out
        self.background_char = background_char
        self.background_color_pair = background_color_pair
        self.regions_need_update = True

        self._size = env_out.get_size()
        self.on_size()

    def on_size(self):
        """
        Erase last render and re-make buffers.
        """
        h, w = self._size

        self._last_canvas = np.full((h, w), style_char(self.background_char))
        self._last_colors = np.full(
            (h, w, 6), self.background_color_pair, dtype=np.uint8
        )

        self.canvas = self._last_canvas.copy()
        self.colors = self._last_colors.copy()

        self._redraw_all = True
        self.regions_need_update = True

        # Buffer arrays to re-use in the `render` method:
        self._color_diffs = np.zeros_like(self.colors, dtype=bool)
        self._reduced_color_diffs = np.zeros_like(self.canvas, dtype=bool)

    @property
    def pos(self):
        return Point(0, 0)

    @property
    def absolute_pos(self):
        return Point(0, 0)

    @property
    def is_transparent(self):
        return False

    @property
    def is_visible(self):
        return True

    @property
    def is_enabled(self):
        return True

    @property
    def parent(self):
        return None

    @property
    def root(self):
        return self

    @property
    def app(self):
        return self._app

    def to_local(self, point: Point) -> Point:
        return point

    def collides_point(self, point: Point) -> bool:
        y, x = point
        return 0 <= y < self.height and 0 <= x < self.width

    def _update_regions(self):
        if self.regions_need_update:
            self.region = Region.from_rect(self)
            for child in self.walk_preorder():
                if child.is_enabled and child.is_visible:
                    child.region = child.parent.region & Region.from_rect(child)

            for child in self.walk_reverse_postorder():
                if child.is_enabled and child.is_visible:
                    child.region = self.region & child.region
                    if not child.is_transparent:
                        self.region -= child.region
            self.regions_need_update = False

    def _render_tree(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        transparent_stack = []
        for child in self.walk_reverse_postorder():
            if child.is_enabled and child.is_visible:
                if child.is_transparent:
                    transparent_stack.append(child)
                else:
                    child.render(canvas, colors)

                    while transparent_stack and transparent_stack[-1].parent is child:
                        transparent_stack.pop().render(canvas, colors)

        while transparent_stack:
            transparent_stack.pop().render(canvas, colors)

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        if self.regions_need_update:
            self._update_regions()

        # Swap canvas with last render:
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.colors, self._last_colors = self._last_colors, self.colors

        canvas = self.canvas
        colors = self.colors

        # Erase canvas:
        canvas[:] = style_char(self.background_char)
        colors[:, :] = self.background_color_pair

        self._render_tree(canvas, colors)

        height, width = self.size
        if self._redraw_all:
            self._redraw_all = False
            ys, xs = np.indices((height, width)).reshape(2, height * width)
        else:
            color_diffs = self._color_diffs
            reduced_color_diffs = self._reduced_color_diffs

            # Find differences between current render and last render; i.e.:
            #     (last_canvas != canvas) | np.any(last_colors != colors, axis=-1)
            char_diffs = self._last_canvas != canvas
            np.not_equal(self._last_colors, colors, out=color_diffs)
            np.any(color_diffs, axis=-1, out=reduced_color_diffs)
            np.logical_or(char_diffs, reduced_color_diffs, out=char_diffs)

            ys, xs = char_diffs.nonzero()

        env_out = self.env_out
        write = env_out._buffer.append

        for y, x, style, color_pair in zip(ys, xs, canvas[ys, xs], colors[ys, xs]):
            char, bold, italic, underline, strikethrough, overline = style

            if char == "":
                # `""` is used to indicate the character before it is a full-width
                # character. If this char is appearing in the diffs, we probably need to
                # repaint the full-width character before it, but if the character
                # before it isn't full-width paint whitespace instead.
                if x > 0 and wcwidth(canvas["char"][y, x - 1]) == 2:
                    x -= 1
                    char, bold, italic, underline, strikethrough, overline = canvas[
                        y, x
                    ]
                    color_pair = colors[y, x]
                else:
                    char = " "
            elif (
                x + 1 < width
                and self.canvas["char"][y, x + 1] != ""
                and wcwidth(char) == 2
            ):
                # If the character is full-width, but the following character isn't
                # `""`, assume the full-width character is being clipped, and paint
                # whitespace instead.
                char = " "

            fr, fg, fb, br, bg, bb = color_pair
            write(
                f"\x1b[{y + 1};{x + 1}H"  # Move cursor to (y, x)
                "\x1b[0;"  # Reset
                f"{'1;' if bold else ''}"
                f"{'3;' if italic else ''}"
                f"{'4;' if underline else ''}"
                f"{'9;' if strikethrough else ''}"
                f"{'53;' if overline else ''}"
                f"38;2;{fr};{fg};{fb};48;2;{br};{bg};{bb}m"  # Set color pair
                f"{char}"
            )
        env_out.flush()
