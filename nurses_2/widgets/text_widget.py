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
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str, default: " "
        Default background character.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color pair of widget.
    default_fg_color: Color
        The default foreground color.
    default_bg_color: Color
        The default background color.
    get_view: CanvasView
        Return a :class:`nurses_2.widgets.text_widget_data_structures.CanvasView`
        of the underlying :attr:`canvas`.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    add_border:
        Add a border to the widget.
    normalize_canvas:
        Add zero-width characters after each full-width character.
    add_text:
        Add text to the canvas.
    on_size:
        Called when widget is resized.
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is True).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
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
        Vectorized :func:`wcwidth.wcswidth`.
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
        Return a :class:`nurses_2.widgets.text_data_structures.CanvasView` that simplifies
        adding text to a view of :attr:`canvas`.
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
