"""
A text widget.
"""
import numpy as np
from wcwidth import wcswidth

from ..colors import WHITE_ON_BLACK, ColorPair, Color
from ..data_structures import *
from .text_widget_data_structures import *
from .widget import Widget
from .widget_data_structures import *

__all__ = (
    "Anchor",
    "CanvasView",
    "ColorPair",
    "Easing",
    "Point",
    "PosHint",
    "Size",
    "SizeHint",
    "TextWidget",
)


class TextWidget(Widget):
    """
    A text widget. Displays arbitrary text data.

    Parameters
    ----------
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of widget.

    Attributes
    ----------
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in `canvas`.
    default_char : str, default: " "
        Default background character.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color pair of widget.
    default_fg_color: Color
        The default foreground color.
    default_bg_color: Color
        The default background color.
    get_view: CanvasView
        A `CanvasView` of the underlying canvas. A `CanvasView` simplifies adding
        text to the canvas with the `add_text` method.

    Methods
    -------
    add_border
        Add a border to the widget.
    normalize_canvas
        Add zero-width characters after each full-width character.
    add_text
        Add text to the canvas.
    """
    def __init__(
        self,
        default_char: str=" ",
        default_color_pair: ColorPair=WHITE_ON_BLACK,
        **kwargs,
    ):
        super().__init__(**kwargs)

        size = self.size

        self.canvas = np.full(size, default_char, dtype=object)
        self.colors = np.full((*size, 6), default_color_pair, dtype=np.uint8)

        self.default_char = default_char
        self.default_color_pair = default_color_pair

    def on_size(self):
        # Preserve content as much as possible.
        old_h, old_w = self.canvas.shape

        h, w = self._size

        old_canvas = self.canvas
        old_colors = self.colors

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.canvas = np.full((h, w), self.default_char, dtype=object)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self.canvas[:copy_h, :copy_w] = old_canvas[:copy_h, :copy_w]
        self.colors[:copy_h, :copy_w] = old_colors[:copy_h, :copy_w]

    @property
    def default_fg_color(self) -> Color:
        """
        The default foreground color.
        """
        return self.default_color_pair.fg_color

    @property
    def default_bg_color(self) -> Color:
        return self.default_color_pair.bg_color

    @staticmethod
    @np.vectorize
    def character_width(char):
        """
        Vectorized `wcswidth`.
        """
        return wcswidth(char)

    def add_border(
        self,
        tl: str="┌",
        tr: str="┐",
        bl: str="└",
        br: str="┘",
        v: str="│",
        h: str="─",
        color_pair: ColorPair | None=None,
    ):
        """
        Add a border. Default border characters are light box-drawing characters.

        Parameters
        ----------
        tl : str, default: "┌"
            Top left character.
        tr : str, default: "┐"
            Top right character.
        bl : str, default: "└"
            Bottom left character.
        br : str, default: "┘"
            Bottom right character.
        v : str, default: "│"
            Vertical character.
        h : str, default: "─"
            Horizontal character.
        color_pair : ColorPair | None, default: None
            Border color pair if not None.
        """
        canvas = self.canvas

        canvas[(0, 0, -1, -1), (0, -1, 0, -1)] = tl, tr, bl, br
        canvas[1: -1, [0, -1]] = v
        canvas[[0, -1], 1: -1] = h

        if color_pair is not None:
            self.colors[[0, -1]] = color_pair
            self.colors[:, [0, -1]] = color_pair

    def normalize_canvas(self):
        """
        Add zero-width characters after each full-width character.

        Raises
        ------
        ValueError
            If full-width character is followed by non-default character.

        Notes
        -----
        In some cases, even with normalized canvases, widgets with full-width characters
        could cause display issues.

        Imagine the following arrangement of widgets:
        ```
                      _________
                     | fw  ____|___
                     | fw | fw  ___|__
                     | fw | fw | fw  _|__
                     | fw | fw | fw | fw |
                     |____|____|____|____|
        ```

        `fw` represents a full-width character and each widget is offset from the next by one.
        One can end up with an entire row of full-width characters which will likely ruin the
        display. If `normalize_canvas` and `add_text` aren't sufficient for the user, a custom
        render method will likely need to be implemented.
        """
        canvas = self.canvas
        default_char = self.default_char

        char_widths = self.character_width(self.canvas)

        canvas[char_widths == 0] = default_char  # Zero-width characters are replaced with the default character.

        where_fullwidth = np.argwhere(char_widths == 2)
        for y, x in where_fullwidth:
            if x == self.width - 1:
                raise ValueError("can't normalize, full-width character on edge")

            if canvas[y, x + 1] != default_char:
                raise ValueError("can't normalize, full-width character followed by non-default char")

            canvas[y, x + 1] = chr(0x200B)  # Zero-width space

    @property
    def get_view(self) -> CanvasView:
        """
        A wrapper around the canvas with an `add_text` method. This is to
        simplify adding text to views of the underlying canvas.

        Notes
        -----
        One-dimensional views will have an extra axis pre-pended to make them two-dimensional.
        E.g., rows and columns with shape (m,) will be re-shaped to (1, m) so that
        the `add_text` `row` and `column` parameters make sense.
        """
        return CanvasView(self.canvas)

    add_text = CanvasView.add_text

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Paint region given by source into canvas_view and colors_view.
        """
        if self.is_transparent:
            source_view = self.canvas[source]
            visible = np.isin(source_view, (" ", "⠀"), invert=True)  # Whitespace isn't painted if transparent.

            canvas_view[visible] = source_view[visible]
            colors_view[visible] = self.colors[source][visible]
        else:
            canvas_view[:] = self.canvas[source]
            colors_view[:] = self.colors[source]

        self.render_children(source, canvas_view, colors_view)
