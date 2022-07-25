"""
:class:`_Traces` handles rendering a line plot in braille unicode characters
for :class:`nurses_2.widgets.line_plot.LinePlot`.
"""
import cv2
import numpy as np

from ...colors import Color, rainbow_gradient
from ...data_structures import Size
from ...easings import lerp
from .._binary_to_braille import binary_to_braille
from ..text_widget import TextWidget, Anchor

TICK_WIDTH = 11
TICK_HALF = TICK_WIDTH // 2
VERTICAL_SPACING = 5
VERTICAL_HALF = VERTICAL_SPACING // 2
PRECISION = 4


class _Traces(TextWidget):
    def __init__(
        self,
        *points: list[float] | np.ndarray,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        line_colors: list[Color] | None=None,
        **kwargs,
    ):
        self.x_ticks = TextWidget(pos_hint=(1.0, None), anchor=Anchor.BOTTOM_LEFT, **kwargs)
        self.y_ticks = TextWidget(**kwargs)

        super().__init__(**kwargs)

        self.all_xs = [np.array(xs, dtype=float) for xs in points[::2]]
        self.all_ys = [np.array(ys, dtype=float) for ys in points[1::2]]
        if len(self.all_xs) != len(self.all_ys):
            raise ValueError("xs given with no ys")

        self.xmin = min(xs.min() for xs in self.all_xs) if xmin is None else xmin
        self.xmax = max(xs.max() for xs in self.all_xs) if xmax is None else xmax
        self.ymin = min(ys.min() for ys in self.all_ys) if ymin is None else ymin
        self.ymax = max(ys.max() for ys in self.all_ys) if ymax is None else ymax

        self.line_colors = rainbow_gradient(len(self.all_xs)) if line_colors is None else line_colors
        if len(self.line_colors) != len(self.all_xs):
            raise ValueError("number of plots inconsistent with number of colors")

        self.on_size()

    def on_size(self):
        h, w = self._size

        offset_h = h - VERTICAL_HALF
        offset_w = w - TICK_HALF * 2 - TICK_WIDTH % 2

        if offset_h <= 1 or offset_w <= 1:
            return

        h4 = offset_h * 4
        w2 = offset_w * 2

        xmin = self.xmin
        xmax = self.xmax
        x_length = xmax - xmin

        ymin = self.ymin
        ymax = self.ymax
        y_length = ymax - ymin

        self.canvas = np.full((h, w), self.default_char, dtype=object)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        canvas_view = self.canvas[:-VERTICAL_HALF, TICK_HALF:-TICK_HALF - TICK_WIDTH % 2]
        colors_view = self.colors[:-VERTICAL_HALF, TICK_HALF:-TICK_HALF - TICK_WIDTH % 2, :3]

        for xs, ys, color in zip(self.all_xs, self.all_ys, self.line_colors, strict=True):
            plot = np.zeros((h4, w2), dtype=np.uint8)

            scaled_ys = h4 - h4 * (ys - ymin) / y_length
            scaled_xs = w2 * (xs - xmin) / x_length
            coords = np.dstack((scaled_xs, scaled_ys)).astype(int)

            cv2.polylines(plot, coords, isClosed=False, color=1)

            sectioned = np.swapaxes(plot.reshape(offset_h, 4, offset_w, 2), 1, 2)
            braille = binary_to_braille(sectioned)
            where_braille = braille != chr(0x2800)  # Empty braille character

            canvas_view[where_braille] = braille[where_braille]
            colors_view[where_braille] = color

        # Regenerate Ticks
        y_ticks = self.y_ticks
        y_ticks.size = h, TICK_WIDTH
        y_ticks.canvas[:] = y_ticks.default_char
        y_ticks.canvas[:, -1] = "│"

        x_ticks = self.x_ticks
        x_ticks.size = 2, w
        x_ticks.canvas[:] = x_ticks.default_char
        x_ticks.canvas[0] = "─"

        for row in range(offset_h - 1, -1, -VERTICAL_SPACING):
            y_label = lerp(ymax, ymin, row / (offset_h - 1))
            y_ticks.add_text(
                f"{y_label:>{TICK_WIDTH - 2}.{PRECISION}g} ┤"[:TICK_WIDTH],
                row=row
            )
        y_ticks.canvas[0, -1] = "┐"

        for column in range(0, offset_w, TICK_WIDTH):
            x_label = lerp(xmin, xmax, column / (offset_w - 1))
            x_ticks.add_text("┬", row=0, column=column + TICK_HALF)
            x_ticks.add_text(
                f"{x_label:^{TICK_WIDTH}.{PRECISION}g}"[:TICK_WIDTH],
                row=1,
                column=column,
            )

        last_tick_column = -TICK_HALF - 1 - TICK_WIDTH % 2
        x_ticks.add_text("┐", row=0, column=last_tick_column)
        x_ticks.canvas[0, last_tick_column + 1:] = x_ticks.default_char

        x_ticks.update_geometry()  # Ensure x-ticks are moved to the bottom of plot.

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value):
        self._left = value
        self.x_ticks.left = value + TICK_WIDTH

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, value):
        self._top = value
        self.y_ticks.top = value
