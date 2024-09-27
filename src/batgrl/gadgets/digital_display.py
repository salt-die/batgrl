"""A 7x8 14-segment (plus decimal point) display gadget."""

import numpy as np

from ..colors import BLACK, Color
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .text import Text

__all__ = ["DigitalDisplay", "Point", "Size"]

DIM_GREEN = Color.from_hex("062b0f")
BRIGHT_GREEN = Color.from_hex("33e860")

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
        segment = instance._display.canvas["fg_color"][self.slice]
        return (segment == instance.on_color).all()

    def __set__(self, instance, value):
        fg = instance._display.canvas["fg_color"]
        fg[self.slice] = instance.on_color if value else instance.off_color


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
    off_color : Color, default: DIM_GREEN
        Color of off segments.
    on_color : Color, default: BRIGHT_GREEN
        Color of on segments.
    bg_color : Color, default: BLACK
        Background color of gadget.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    off_color : Color
        Color of off segments.
    on_color : Color
        Color of on segments.
    bg_color : Color
        Background color of gadget.
    alpha : float
        Transparency of gadget.
    a : bool
        Whether the `a` segment is on.
    b : bool
        Whether the `b` segment is on.
    c : bool
        Whether the `c` segment is on.
    d : bool
        Whether the `d` segment is on.
    e : bool
        Whether the `e` segment is on.
    f : bool
        Whether the `f` segment is on.
    g1 : bool
        Whether the `g1` segment is on.
    g2 : bool
        Whether the `g2` segment is on.
    h : bool
        Whether the `h` segment is on.
    i : bool
        Whether the `i` segment is on.
    j : bool
        Whether the `j` segment is on.
    k : bool
        Whether the `k` segment is on.
    l : bool
        Whether the `l` segment is on.
    m : bool
        Whether the `m` segment is on.
    dp : bool
        Whether the `dp` segment is on.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    show_char(char)
        Display an ascii character.
    add_border(style="light", ...)
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style)
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...)
        Add a single line of text to the canvas.
    set_text(text, ...)
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    clear()
        Fill canvas with default cell.
    shift(n=1)
        Shift content in canvas up (or down in case of negative `n`).
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    a = _Segment(np.s_[0, 1:6])
    b = _Segment(np.s_[1:3, 6])
    c = _Segment(np.s_[4:6, 6])
    d = _Segment(np.s_[6, 1:6])
    e = _Segment(np.s_[4:6, 0])
    f = _Segment(np.s_[1:3, 0])
    g1 = _Segment(np.s_[3, 1:3])
    g2 = _Segment(np.s_[3, 4:6])
    h = _Segment(np.s_[[1, 2], [1, 2]])
    i = _Segment(np.s_[1:3, 3])
    j = _Segment(np.s_[[1, 2], [5, 4]])
    k = _Segment(np.s_[[4, 5], [2, 1]])
    l = _Segment(np.s_[4:6, 3])  # noqa
    m = _Segment(np.s_[[4, 5], [4, 5]])
    dp = _Segment(np.s_[6, 7:8])

    def __init__(
        self,
        *,
        off_color: Color = DIM_GREEN,
        on_color: Color = BRIGHT_GREEN,
        bg_color: Color = BLACK,
        alpha: float = 1.0,
        size: Size = Size(7, 8),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._display = Text(
            pos_hint={"y_hint": 0.5, "x_hint": 0.5}, is_transparent=is_transparent
        )
        self._display.set_text(
            " ━━━━━\n"
            "┃\\ ┃ /┃\n"
            "┃ \\┃/ ┃\n"
            " ━━ ━━\n"
            "┃ /┃\\ ┃\n"
            "┃/ ┃ \\┃\n"
            " ━━━━━ ●"
        )
        self._display.canvas["fg_color"] = off_color
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.add_gadget(self._display)
        self._off_color = off_color
        self._on_color = on_color
        self.bg_color = bg_color
        self.alpha = alpha

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._display.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._display.alpha = alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._display.is_transparent = self.is_transparent

    @property
    def off_color(self) -> Color:
        """Color of off segments."""
        return self._off_color

    @off_color.setter
    def off_color(self, off_color: Color):
        fg_color = self._display.canvas["fg_color"]
        mask = np.all(fg_color == self.off_color, axis=-1)
        fg_color[mask] = off_color
        self._off_color = off_color

    @property
    def on_color(self) -> Color:
        """Color of on segments."""
        return self._on_color

    @on_color.setter
    def on_color(self, on_color: Color):
        fg_color = self._display.canvas["fg_color"]
        mask = np.all(fg_color == self.on_color, axis=-1)
        fg_color[mask] = on_color
        self._on_color = on_color

    @property
    def bg_color(self) -> Color:
        """Background color of gadget."""
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._display.canvas["bg_color"] = bg_color
        self._bg_color = bg_color

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

        self._display.canvas["fg_color"] = self.off_color

        for segment in _CHAR_TO_SEGMENTS[char]:
            setattr(self, segment, True)
