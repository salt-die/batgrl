"""
A 7x8 14-segment (plus decimal point) display widget.
"""
import numpy as np

from ..colors import Color, ColorPair, BLACK
from .text_widget import TextWidget, Size

DIM_GREEN = Color.from_hex("062b0f")
BRIGHT_GREEN = Color.from_hex("33e860")

DIM_GREEN_ON_BLACK = ColorPair.from_colors(DIM_GREEN, BLACK)
BRIGHT_GREEN_ON_BLACK = ColorPair.from_colors(BRIGHT_GREEN, BLACK)

_CHAR_TO_SEGMENTS = {
    " ": (),
    "0": ("a", "b", "c", "d", "e", "f"),
    "1": ("b", "c"),
    "2": ("a", "b", "g2", "g1", "e", "d"),
    "3": ("a", "b", "g2", "c", "d"),
    "4": ("f", "b", "g1", "g2", "c"),
    "5": ("a", "f", "g1", "m", "d"),
    "6": ("a", "f", "g1", "g2", "e", "c", "d"),
    "7": ("a", "b", "c"),
    "8": ("a", "f", "b", "g1", "g2", "e", "c", "d"),
    "9": ("a", "f", "b", "g1", "g2", "c", "d"),
    "a": ("e", "g1", "l", "d"),
    "b": ("f", "g1", "e", "m", "d"),
    "c": ("g1", "g2", "e", "d"),
    "d": ("k", "g2", "b", "c", "d"),
    "e": ("g1", "e", "k", "d"),
    "f": ("g1", "j", "g2", "l"),
    "g": ("j", "b", "g2", "c", "d"),
    "h": ("f", "g1", "e", "l"),
    "i": ("l",),
    "j": ("e", "k", "i"),
    "k": ("i", "l", "j", "m"),
    "l": ("f", "e"),
    "m": ("e", "g1", "l", "g2", "c"),
    "n": ("e", "g1", "l"),
    "o": ("g1", "g2", "e", "c", "d"),
    "p": ("f", "h", "g1", "e"),
    "q": ("j", "b", "g2", "c"),
    "r": ("e", "g1"),
    "s": ("g2", "m", "d"),
    "t": ("f", "g1", "e", "d"),
    "u": ("e", "d", "c"),
    "v": ("e", "k"),
    "w": ("e", "k", "m", "c"),
    "x": ("h", "j", "k", "m"),
    "y": ("i", "g2", "b", "c", "d"),
    "z": ("g1", "k", "d"),
    "A": ("a", "f", "b", "g1", "g2", "e", "c"),
    "B": ("a", "i", "b", "g2", "l", "c", "d"),
    "C": ("a", "f", "e", "d"),
    "D": ("a", "i", "b", "l", "c", "d"),
    "E": ("a", "f", "g1", "e", "d"),
    "F": ("a", "f", "g1", "e"),
    "G": ("a", "f", "g2", "e", "c", "d"),
    "H": ("f", "b", "g1", "g2", "e", "c"),
    "I": ("a", "i", "l", "d"),
    "J": ("e", "d", "c", "b"),
    "K": ("f", "g1", "j", "e", "m"),
    "L": ("f", "e", "d"),
    "M": ("f", "h", "j", "b", "e", "c"),
    "N": ("f", "h", "b", "e", "m", "c"),
    "O": ("a", "f", "b", "e", "c", "d"),
    "P": ("a", "f", "b", "g1", "g2", "e"),
    "Q": ("a", "f", "b", "e", "m", "c", "d"),
    "R": ("a", "f", "b", "g1", "g2", "e", "m"),
    "S": ("a", "f", "g1", "g2", "c", "d"),
    "T": ("a", "i", "l"),
    "U": ("f", "b", "e", "c", "d"),
    "V": ("f", "e", "k", "j"),
    "W": ("f", "b", "e", "k", "m", "c"),
    "X": ("h", "j", "k", "m"),
    "Y": ("f", "b", "g1", "g2", "c", "d"),
    "Z": ("a", "j", "k", "d"),
    "!": ("b", "c", "dp"),
    '"': ("i", "b"),
    "#": ("g1", "i", "g2", "b", "l", "c", "d"),
    "$": ("a", "f", "i", "g1", "g2", "l", "c", "d"),
    "%": ("f", "h", "j", "g1", "g2", "k", "m", "c"),
    "&": ("a", "h", "i", "g1", "e", "m", "d", "c"),
    "'": ("i",),
    "(": ("j", "m"),
    ")": ("h", "k"),
    "*": ("h", "i", "j", "g1", "g2", "k", "l", "m"),
    "+": ("i", "g1", "g2", "l"),
    ",": ("k",),
    "-": ("g1", "g2"),
    ".": ("dp",),
    "/": ("k", "j"),
    ":": ("i", "l"),
    ";": ("i", "k"),
    "<": ("g1", "j", "m"),
    "=": ("g1", "g2", "d"),
    ">": ("h", "k", "g2"),
    "?": ("a", "b", "g2", "l", "dp"),
    "@": ("i", "g2", "b", "a", "f", "e", "d"),
    "[": ("a", "f", "e", "d"),
    "\\": ("h", "m"),
    "]": ("a", "b", "c", "d"),
    "^": ("k", "m"),
    "_": ("d",),
    "`": ("h",),
    "{": ("a", "h", "g1", "k", "d"),
    "|": ("i", "l"),
    "}": ("a", "j", "g2", "m", "d"),
    "~": ("g1", "j", "g2", "k"),
}


class _Segment:
    def __init__(self, slice_):
        self.slice = slice_

    def __get__(self, owner, instance):
        return (instance._display.colors[self.slice] == instance.on_color_pair).all()

    def __set__(self, instance, value):
        instance._display.colors[self.slice] = instance.on_color_pair if value else instance.off_color_pair


class DigitalDisplay(TextWidget):
    r"""
    A 7x8 14-segment (plus decimal point) display widget. Segments
    are labeled according to the following diagram::

            a
          ━━━━━
        f┃  ┃i ┃b     h \   / j
         ┃  ┃  ┃         \ /
                     g1 ━━ ━━ g2
        e┃  ┃l ┃c        / \
         ┃  ┃  ┃      k /   \ m
          ━━━━━ ● dp
            d

    Parameters
    ----------
    off_color_pair : ColorPair, default: DIM_GREEN_ON_BLACK
        Color pair of off segments.
    on_color_pair : ColorPair, default: BRIGHT_GREEN_ON_BLACK
        Color pair of on segments.
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
    off_color_pair : ColorPair
        Color pair of off segments.
    on_color_pair : ColorPair
        Color pair of on segments.
    a : bool
        If `a` segment of digital display is on.
    b : bool
        If `b` segment of digital display is on.
    c : bool
        If `c` segment of digital display is on.
    d : bool
        If `d` segment of digital display is on.
    e : bool
        If `e` segment of digital display is on.
    f : bool
        If `f` segment of digital display is on.
    g1 : bool
        If `g1` segment of digital display is on.
    g2 : bool
        If `g2` segment of digital display is on.
    h : bool
        If `h` segment of digital display is on.
    i : bool
        If `i` segment of digital display is on.
    j : bool
        If `j` segment of digital display is on.
    k : bool
        If `k` segment of digital display is on.
    l : bool
        If `l` segment of digital display is on.
    m : bool
        If `m` segment of digital display is on.
    dp : bool
        If `dp` segment of digital display is on.
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
        Determines which point is attached to `pos_hint`.
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
    show_char:
        Display an ascii character.
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
    a  = _Segment(np.s_[0, 1: 6])
    b  = _Segment(np.s_[1: 3, 6])
    c  = _Segment(np.s_[4: 6, 6])
    d  = _Segment(np.s_[6, 1: 6])
    e  = _Segment(np.s_[4: 6,  0])
    f  = _Segment(np.s_[1: 3,  0])
    g1 = _Segment(np.s_[3, 1: 3])
    g2 = _Segment(np.s_[3, 4: 6])
    h  = _Segment(((1, 2), (1, 2)))
    i  = _Segment(np.s_[1: 3, 3])
    j  = _Segment(((1, 2), (5, 4)))
    k  = _Segment(((4, 5), (2, 1)))
    l  = _Segment(np.s_[4: 6, 3])
    m  = _Segment(((4, 5), (4, 5)))
    dp = _Segment(np.s_[6, 7:8])

    def __init__(
        self,
        *,
        off_color_pair: ColorPair=DIM_GREEN_ON_BLACK,
        on_color_pair: ColorPair=BRIGHT_GREEN_ON_BLACK,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.off_color_pair = off_color_pair
        self.on_color_pair = on_color_pair

        self._display = TextWidget(size=(7, 8), default_char=self.default_char)
        canvas = self._display.canvas

        canvas[[0, 6], 1: 6] = canvas[3, 1: 3] = canvas[3, 4: 6] = "━"
        canvas[1: 3,  [0, 3, 6]] = canvas[4: 6, [0, 3, 6]] = "┃"
        canvas[(1, 2, 4, 5), (1, 2, 4, 5)] = "\\"
        canvas[(1, 2, 4, 5), (5, 4, 2, 1)] = "/"
        canvas[6, 7] = "●"

        self._where_segments = canvas != self.default_char
        self._display.colors[self._where_segments] = off_color_pair

        self.add_widget(self._display)

    def show_char(self, char: str):
        if char not in _CHAR_TO_SEGMENTS:
            raise ValueError(f"{char} is not an ascii character")

        self._display.colors[self._where_segments] = self.off_color_pair

        for segment in _CHAR_TO_SEGMENTS[char]:
            setattr(self, segment, True)
