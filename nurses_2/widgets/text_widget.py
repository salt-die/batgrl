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
    "add_text",
    "Anchor",
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
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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
        Ensure column width of text in the canvas is equal to widget width.
    add_str:
        Add a single line of text to the canvas.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
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

        self.canvas = np.full(size, style_char(default_char))
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

        self.canvas = np.full((h, w), style_char(self.default_char))
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

    def add_border(self, style: Border=Border.LIGHT, bold: bool= False, color_pair: ColorPair | None=None,):
        """
        Add a text border.

        Parameters
        ----------
        style : Border, default: Border.LIGHT
            Style of border. Default style uses light box-drawing characters.
        bold : bool, default: False
            Whether the border is bold.
        color_pair : ColorPair | None, default: None
            Border color pair if not None.
        """
        BORDER_STYLES = dict(
            light=  "┌┐│─└┘",
            heavy=  "┏┓┃━┗┛",
            double= "╔╗║═╚╝",
            curved= "╭╮│─╰╯",
            ascii=  "++|-++",
        )
        tl, tr, v, h, bl, br = BORDER_STYLES[style]

        canvas = self.canvas
        canvas["char"][(0, 0, -1, -1), (0, -1, 0, -1)] = tl, tr, bl, br
        canvas["bold"][(0, 0, -1, -1), (0, -1, 0, -1)] = bold
        canvas[["italic", "underline", "strikethrough"]][(0, 0, -1, -1), (0, -1, 0, -1)] = False
        canvas[1: -1, [0, -1]] = style_char(v, bold=bold)
        canvas[[0, -1], 1: -1] = style_char(h, bold=bold)

        if color_pair is not None:
            self.colors[[0, -1]] = color_pair
            self.colors[:, [0, -1]] = color_pair

    def normalize_canvas(self):
        """
        Ensure column width of text in the canvas is equal to widget width.

        Rendering issues can occur when column width of text exceeds widget width.
        To fix this, 0-width characters are replaced with the default character, then
        empty characters are placed after each full-width character.

        Text added with `add_str` or `add_text` is already normalized.
        """
        char_widths = self.character_width(self.canvas["char"])
        self.canvas[char_widths == 0] = style_char(self.default_char)
        self.canvas[:, -1][char_widths[:, -1] == 2] = style_char(self.default_char)
        for x in range(self.width - 1):
            self.canvas[:, x + 1][self.character_width(self.canvas["char"][:, x]) == 2] = style_char("")

    def add_str(
        self,
        str: str,
        pos: Point=Point(0, 0),
        *,
        bold: bool=False,
        italic: bool=False,
        underline: bool=False,
        strikethrough: bool=False,
        truncate_str: bool=False,
    ):
        """
        Add a single line of text to the canvas at position `pos`.

        Parameters
        ----------
        str : str
            A single line of text to add to canvas.
        pos : Point, default: Point(0, 0)
            Position of first character of string. Negative coordinates position
            from the right or bottom of canvas (like negative indices).
        bold : bool, default: False
            Whether text is bold.
        italic : bool, default: False
            Whether text is italic.
        underline : bool, default: False
            Whether text is underlined.
        strikethrough : bool, default: False
            Whether text is strikethrough.
        truncate_str : bool, default: False
            If false, an `IndexError` is raised if the text would not fit on canvas.

        See Also
        --------
        text_widget.add_text : Add multiple lines of text on an arbitrary `numpy.ndarray` or view.
        """
        y, x = pos
        add_text(
            self.canvas[y, x:],
            str,
            bold=bold,
            italic=italic,
            underline=underline,
            strikethrough=strikethrough,
            truncate_text=truncate_str,
        )

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Paint region given by source into canvas_view and colors_view.
        """
        if self.is_transparent:
            source_view = self.canvas[source]
            visible = np.isin(source_view["char"], (" ", "⠀"), invert=True)  # Whitespace isn't painted if transparent.

            canvas_view[visible] = source_view[visible]
            colors_view[visible] = self.colors[source][visible]
        else:
            canvas_view[:] = self.canvas[source]
            colors_view[:] = self.colors[source]

        self.render_children(source, canvas_view, colors_view)
