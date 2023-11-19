"""A 7x8 14-segment (plus decimal point) display gadget."""
import numpy as np
from numpy.typing import NDArray

from ..colors import BLACK, Color, ColorPair
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text

__all__ = [
    "DigitalDisplay",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

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
        instance._display.colors[self.slice] = (
            instance.on_color_pair if value else instance.off_color_pair
        )


class DigitalDisplay(Gadget):
    r"""
    A 7x8 14-segment (plus decimal point) display gadget.

    Segments are labeled according to the following diagram::

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
    background_char : NDArray[Char] | str | None, default: None
        The background character of the gadget. If not given and not transparent, the
        background characters of the root gadget are painted. If not given and
        transparent, characters behind the gadget are visible. The character must be
        single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget. If not given and not transparent, the
        background color pair of the root gadget is painted. If not given and
        transparent, the color pairs behind the gadget are visible.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

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
    background_char : NDArray[Char] | None
        The background character of the gadget.
    background_color_pair : ColorPair | None
        The background color pair of the gadget.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    show_char(char):
        Display an ascii character.
    add_border(style="light", ...):
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style):
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...):
        Add a single line of text to the canvas.
    set_text(text, ...):
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.
    """

    a = _Segment(np.s_[0, 1:6])
    b = _Segment(np.s_[1:3, 6])
    c = _Segment(np.s_[4:6, 6])
    d = _Segment(np.s_[6, 1:6])
    e = _Segment(np.s_[4:6, 0])
    f = _Segment(np.s_[1:3, 0])
    g1 = _Segment(np.s_[3, 1:3])
    g2 = _Segment(np.s_[3, 4:6])
    h = _Segment(((1, 2), (1, 2)))
    i = _Segment(np.s_[1:3, 3])
    j = _Segment(((1, 2), (5, 4)))
    k = _Segment(((4, 5), (2, 1)))
    l = _Segment(np.s_[4:6, 3])  # noqa
    m = _Segment(((4, 5), (4, 5)))
    dp = _Segment(np.s_[6, 7:8])

    def __init__(
        self,
        *,
        off_color_pair: ColorPair = DIM_GREEN_ON_BLACK,
        on_color_pair: ColorPair = BRIGHT_GREEN_ON_BLACK,
        size=Size(7, 8),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: NDArray[Char] | str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.off_color_pair = off_color_pair
        self.on_color_pair = on_color_pair

        self._display = Text(
            default_color_pair=off_color_pair, pos_hint={"y_hint": 0.5, "x_hint": 0.5}
        )
        self._display.set_text(
            " ━━━━━  \n"
            "┃\\ ┃ /┃ \n"
            "┃ \\┃/ ┃ \n"
            " ━━ ━━  \n"
            "┃ /┃\\ ┃ \n"
            "┃/ ┃ \\┃ \n"
            " ━━━━━ ●"
        )
        self.add_gadget(self._display)

    def show_char(self, char: str):
        """
        Show an ascii character in the digital display.

        Parameters
        ----------
        char : str
            The character to display.
        """
        if char not in _CHAR_TO_SEGMENTS:
            raise ValueError(f"{char} is not an ascii character")

        self._display.colors[:] = self.off_color_pair

        for segment in _CHAR_TO_SEGMENTS[char]:
            setattr(self, segment, True)
