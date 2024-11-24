"""An ans (ANSI art) file viewer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from ..colors import BLACK, WHITE, Color, lerp_colors
from ..geometry import Point, Size
from ..text_tools import Cell, new_cell
from .gadget import Gadget, PosHint, SizeHint
from .scroll_view import ScrollView
from .text import Text

_CSI_RE: Final = re.compile(r"\x1b\[[;\d]*\w")
"""Control sequence pattern."""
# Colors from VGA column of: https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
_LOW_INTENSITY: Final = (
    BLACK,
    Color(170, 0, 0),
    Color(0, 170, 0),
    Color(170, 85, 0),
    Color(0, 0, 170),
    Color(170, 0, 170),
    Color(0, 170, 170),
    Color(170, 170, 170),
)
"""Low intensity terminal colors."""
_HIGH_INTENSITY: Final = (
    Color(85, 85, 85),
    Color(255, 85, 85),
    Color(85, 255, 85),
    Color(255, 255, 85),
    Color(85, 85, 255),
    Color(255, 85, 255),
    Color(85, 255, 255),
    WHITE,
)
"""High intensity terminal colors."""
_UTF8_CHARS: Final = (
    " ☺☻♥♦♣♠•◘○◙♂♀♪♫☼"
    "►◄↕‼¶§▬↨↑↓→←∟↔▲▼"
    " !\"#$%&'()*+,-./"
    "0123456789:;<=>?"
    "@ABCDEFGHIJKLMNO"
    "PQRSTUVWXYZ[\\]^_"
    "`abcdefghijklmno"
    "pqrstuvwxyz{|}~⌂"
    "ÇüéâäàåçêëèïîìÄÅ"
    "ÉæÆôöòûùÿÖÜ¢£¥₧ƒ"
    "áíóúñÑªº¿⌐¬½¼¡«»"
    "░▒▓│┤╡╢╖╕╣║╗╝╜╛┐"
    "└┴┬├─┼╞╟╚╔╩╦╠═╬╧"
    "╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀"
    "αßΓπΣσµτΦΘΩδ∞φε∩"
    "≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ "
)  # See: https://wikipedia.org/wiki/Code_page_437
_CP437_TO_UTF8: Final = {i: char for i, char in enumerate(_UTF8_CHARS)}
"""Translation table from code page 437 to UTF-8."""
# Following ords interpreted as escapes:
del _CP437_TO_UTF8[0x0A], _CP437_TO_UTF8[0x1A], _CP437_TO_UTF8[0x1B]


class _AnsReader:
    def __init__(self, path: Path, width: int = 80, guess_width: bool = True):
        self.width: int = width
        """Width of ansi art. Determines when to wrap characters."""
        self.guess_width = guess_width
        """Whether to guess width."""
        self.data: str = path.read_text("cp437").translate(_CP437_TO_UTF8)
        """Ansi data."""

        footer_index = self.data[::-1].find("\x1a")
        if footer_index != -1:
            self.data = self.data[: -footer_index - 1]

    def _new_line(self):
        self.lines.append(
            [
                new_cell(fg_color=_LOW_INTENSITY[7], bg_color=_LOW_INTENSITY[0])
                for _ in range(self.width)
            ]
        )

    def _add_chars(self, start: int, stop: int) -> None:
        if isinstance(self.fg_color, int):
            if self.high_intensity:
                fg_color = _HIGH_INTENSITY[self.fg_color]
            else:
                fg_color = _LOW_INTENSITY[self.fg_color]
        else:
            fg_color = self.fg_color

        if isinstance(self.bg_color, int):
            bg_color = _LOW_INTENSITY[self.bg_color]
        else:
            bg_color = self.bg_color

        for i in range(start, stop):
            char = self.data[i]

            if char == "\n":
                self.cursor_y += 1
                self.cursor_x = 0
            else:
                while self.cursor_y >= len(self.lines):
                    self._new_line()

                self.lines[self.cursor_y][self.cursor_x] = new_cell(
                    char, fg_color=fg_color, bg_color=bg_color
                )

                self.cursor_x += 1
                if self.cursor_x >= self.width:
                    self.cursor_y += 1
                    self.cursor_x = 0

    def _parse_ansi(self) -> None:
        current_index = 0
        for match in _CSI_RE.finditer(self.data):
            start, stop = match.span()
            self._add_chars(current_index, start)
            current_index = stop

            escape = match[0]
            command = escape[-1]
            params = (int(n) for n in re.findall(r"\d+", escape))
            if command == "m":
                for param in params:
                    if param == 0:
                        self.high_intensity = False
                        self.fg_color = 7
                        self.bg_color = 0
                    elif param == 1:
                        self.high_intensity = True
                    elif 30 <= param < 38:
                        self.fg_color = param - 30
                    elif 40 <= param < 48:
                        self.bg_color = param - 40
                    elif param == 38 or param == 39:
                        mode = next(params, -1)
                        if mode == 2:
                            color = Color(*(next(params, 0) for _ in range(3)))
                        elif mode == 5:
                            n = next(params, 0)
                            if 0 <= n < 8:
                                color = n
                            elif n < 16:
                                self.high_intensity = True
                                color = n - 8
                            elif n < 232:
                                remainder, b = divmod(n - 16, 6)
                                r, g = divmod(remainder, 6)
                                color = Color(r * 55, g * 55, b * 55)
                            elif n < 256:
                                color = lerp_colors(BLACK, WHITE, (n - 232) / 23)
                            else:
                                continue
                        else:
                            continue

                        if param == 38:
                            self.fg_color = color
                        else:
                            self.bg_color = color
            elif command == "t":
                try:
                    mode, r, g, b = params
                except ValueError:
                    continue

                if mode == 0:
                    self.bg_color = Color(r, g, b)
                elif mode == 1:
                    self.fg_color = Color(r, g, b)
            elif command == "C":
                self.cursor_x = self.cursor_x + next(params, 1)
            elif command == "A":
                self.cursor_y = max(self.cursor_y - next(params, 1), 0)
            elif command == "B":
                self.cursor_y += next(params, 1)
            elif command == "D":
                self.cursor_x = max(self.cursor_x - next(params, 1), 0)
            elif command == "E":
                self.cursor_y += next(params, 1)
                self.cursor_x = 0
            elif command == "F":
                self.cursor_y = max(self.cursor_y - next(params, 1), 0)
                self.cursor_x = 0
            elif command == "G":
                self.cursor_x = self.width - 1
            elif command == "H":
                self.cursor_y = next(params, 1) - 1
                self.cursor_x = next(params, 1) - 1

        self._add_chars(current_index, len(self.data))

    def _create_canvas(self) -> NDArray[Cell]:
        canvas = np.full(
            (len(self.lines), self.width),
            new_cell(fg_color=_LOW_INTENSITY[7], bg_color=_LOW_INTENSITY[0]),
        )
        for y, line in enumerate(self.lines):
            for x, cell in enumerate(line):
                canvas[y, x] = cell
        return canvas

    def _guess_read(self) -> NDArray[Cell]:
        self.high_intensity = False
        self.fg_color = 7
        self.bg_color = 0

        self.lines: list[list[tuple[Cell, int]]] = []
        self.current_line: list[tuple[Cell, int]] = []
        self.cursor_y: int = 0
        self.cursor_x: int = 0
        try:
            self._parse_ansi()
            return self._create_canvas()
        finally:
            del self.lines, self.current_line, self.cursor_y, self.cursor_x

    def read(self) -> NDArray[Cell] | None:
        # How to determine the width of an ans file?
        # Most are 80 width, luckily, but there are exceptions! Sometimes there is a way
        # to discover an incorrect width assumption: an index error. An index error
        # implies cursor was moved to end of a line and then characters were written
        # which implies the line should've been longer which implies the width is
        # incorrect. In this case, try again with increased width.
        if self.guess_width:
            for _ in range(40):
                try:
                    return self._guess_read()
                except IndexError:
                    self.width += 1
        else:
            return self._guess_read()


class AnsViewer(Gadget):
    r"""
    An ans (ANSI art) file viewer.

    Parameters
    ----------
    path : Path
        Path to ans file.
    ans_width : int
        Column width of ansi art.
    guess_width : bool
        Whether to guess column width if ``ans_width`` results in an error.
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
    ans_width : int
        Column width of ansi art.
    guess_width : bool
        Whether to guess column width if ``ans_width`` results in an error.
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
    parent : Gadget | None
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

    def __init__(
        self,
        *,
        path: Path,
        ans_width: int = 80,
        guess_width: bool = True,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, dynamic_bars=True
        )
        self.add_gadget(self._scroll_view)

        self._ans_reader = _AnsReader(path, ans_width, guess_width)
        self._read_ans()

    @property
    def ans_width(self) -> int:
        """Column width of ansi art."""
        return self._ans_reader.width

    @ans_width.setter
    def ans_width(self, ans_width: int):
        self._ans_reader.width = ans_width
        self._read_ans()

    @property
    def guess_width(self) -> bool:
        """Whether to guess column width if ``ans_width`` results in an error."""
        return self._ans_reader.guess_width

    @guess_width.setter
    def guess_width(self, guess_width: bool):
        self._ans_reader.guess_width = guess_width

    def _read_ans(self):
        canvas = self._ans_reader.read()
        if canvas is None:
            return
        ans = Text(size=canvas.shape)
        ans.canvas = canvas
        self._scroll_view.view = ans
        self.on_size()
