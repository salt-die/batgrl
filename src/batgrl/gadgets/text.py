"""A text gadget."""

from typing import Literal

import numpy as np
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer
from pygments.style import Style as PygmentsStyle
from uwcwidth import wcswidth

from .._rendering import text_render
from ..array_types import RGBM_2D, Cell0D, Cell2D, Enum2D, Unicode2D
from ..colors import Color, Neptune
from ..text_tools import (
    Style,
    _parse_batgrl_md,
    _text_to_cells,
    _write_cells_to_canvas,
    add_text,
    canvas_as_text,
    egc_ord,
    new_cell,
)
from .gadget import (
    Gadget,
    Point,
    Pointlike,
    PosHint,
    Size,
    SizeHint,
    Sizelike,
    bindable,
    clamp,
)

__all__ = [
    "Border",
    "Point",
    "Size",
    "Text",
    "add_text",
]

Border = Literal[
    "light",
    "heavy",
    "double",
    "curved",
    "ascii",
    "outer",
    "inner",
    "thick",
    "dashed",
    "dashed_2",
    "dashed_3",
    "heavy_dashed",
    "heavy_dashed_2",
    "heavy_dashed_3",
    "near",
    "octant",
    "octant_rounded",
    "mcgugan_tall",
    "mcgugan_wide",
    "sextant",
    "sextant_rounded",
]
"""Border styles for :meth:`batgrl.text_gadget.Text.add_border`."""

_BORDERS = {
    "light": "┌┐││──└┘",
    "heavy": "┏┓┃┃━━┗┛",
    "double": "╔╗║║══╚╝",
    "curved": "╭╮││──╰╯",
    "ascii": "++||--++",
    "outer": "▛▜▌▐▀▄▙▟",
    "inner": "▗▖▐▌▄▀▝▘",
    "thick": "████▀▄██",
    "dashed": "┌┐╎╎╌╌└┘",
    "dashed_2": "┌┐┆┆┄┄└┘",
    "dashed_3": "┌┐┊┊┈┈└┘",
    "heavy_dashed": "┏┓╏╏╍╍┗┛",
    "heavy_dashed_2": "┏┓┇┇┅┅┗┛",
    "heavy_dashed_3": "┏┓┋┋┉┉┗┛",
    "near": "  ▕▏▁▔  ",
    "octant": "𜵊𜶘▌▐🮂▂𜷀𜷕",
    "octant_rounded": "𜵉𜶗▌▐🮂▂𜶅𜵛",
    "mcgugan_tall": "▕▏▕▏▔▁▕▏",
    "mcgugan_wide": "▁▁▏▕▁▔▔▔",
    "sextant": "🬕🬨▌▐🬂🬭🬲🬷",
    "sextant_rounded": "🬔🬧▌▐🬂🬭🬣🬘",
}
"""Border characters for :meth:`batgrl.text_gadget.Text.add_border`."""


class Text(Gadget):
    r"""
    A text gadget. Displays arbitrary text data.

    Parameters
    ----------
    default_cell : Cell0D | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 0.0
        Transparency of gadget.
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
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
    canvas : Cell2D
        The array of characters for the gadget.
    chars : Unicode2D
        Return a view of the ords field of the canvas as 1-character unicode strings.
    default_cell : Cell0D
        Default cell of text canvas.
    default_fg_color : Color
        Foreground color of default cell.
    default_bg_color : Color
        Background color of default cell.
    alpha : float
        Transparency of gadget.
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
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
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
    app : App | None
        The running app.

    Methods
    -------
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
    add_gadgets(gadget_it, \*gadgets)
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
        default_cell: Cell0D | str = " ",
        alpha: float = 0.0,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
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
        size = self.size
        self.default_cell = default_cell
        self.canvas: Cell2D = np.full(size, self.default_cell)
        self.alpha = alpha

    @property
    def chars(self) -> Unicode2D:
        """
        Return a view of the ords field of the canvas as 1-character unicode strings.

        Warning
        -------
        This view may raise a ``RuntimeError`` if extended grapheme clusters are stored
        in the canvas as the egc flag is greater than sys.maxunicode.
        """
        return self.canvas["ord"].view("<U1")

    @property
    def default_cell(self) -> Cell0D:
        """Default character for text canvas."""
        return self._default_cell

    @default_cell.setter
    def default_cell(self, cell: Cell0D | str):
        if isinstance(cell, str):
            cell = new_cell(ord=egc_ord(cell))
        self._default_cell = cell

    @property
    def default_fg_color(self) -> Color:
        """Foreground color of default character."""
        return Color(*self._default_cell["fg_color"])  # type: ignore

    @default_fg_color.setter
    def default_fg_color(self, default_fg_color: Color):
        self._default_cell["fg_color"] = default_fg_color  # type: ignore

    @property
    def default_bg_color(self) -> Color:
        """Background color of default character."""
        return Color(*self._default_cell["bg_color"])  # type: ignore

    @default_bg_color.setter
    def default_bg_color(self, default_bg_color: Color):
        self._default_cell["bg_color"] = default_bg_color  # type: ignore

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    @bindable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    def on_size(self):
        """Resize canvas preserving as much content as possible."""
        old_canvas = self.canvas
        old_h, old_w = old_canvas.shape

        h, w = self._size

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.canvas = np.full((h, w), self.default_cell)
        self.canvas[:copy_h, :copy_w] = old_canvas[:copy_h, :copy_w]

    def add_border(
        self,
        style: Border = "light",
        bold: bool = False,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
    ):
        """
        Add a text border (gadget height and width must be at least 2).

        Parameters
        ----------
        style : Border, default: "light"
            Style of border. Default style uses light box-drawing characters.
        bold : bool, default: False
            Whether the border is bold.
        fg_color : Color | None, default: None
            Foreground color of border if not None.
        bg_color : Color | None, default: None
            Background color of border if not None.
        """
        if self.height < 2 or self.width < 2:
            return

        slices = [
            np.s_[0, 0],
            np.s_[0, -1],
            np.s_[1:-1, 0],
            np.s_[1:-1, -1],
            np.s_[0, 1:-1],
            np.s_[-1, 1:-1],
            np.s_[-1, 0],
            np.s_[-1, -1],
        ]
        for s, border in zip(slices, _BORDERS[style]):
            self.chars[s] = border
            if bold:
                self.canvas["style"][s] = Style.BOLD

        if fg_color is not None:
            self.canvas["fg_color"][[0, -1]] = fg_color
            self.canvas["fg_color"][:, [0, -1]] = fg_color
        if bg_color is not None:
            self.canvas["bg_color"][[0, -1]] = bg_color
            self.canvas["bg_color"][:, [0, -1]] = bg_color

    def add_syntax_highlighting(
        self, lexer: Lexer | None = None, style: type[PygmentsStyle] = Neptune
    ):
        """
        Add syntax highlighting to current text in canvas.

        Parameters
        ----------
        lexer : pygments.lexer.Lexer | None, default: None
            Lexer for text. If not given, the lexer is guessed.
        style : pygments.style.Style, default: Neptune
            A pygments style to use for syntax highlighting.
        """
        text = canvas_as_text(self.canvas)
        if lexer is None:
            lexer = guess_lexer(text)

        self.canvas["fg_color"] = 0
        self.canvas["bg_color"] = Color.from_hex(style.background_color)
        y = x = 0
        for ttype, value in lexer.get_tokens(text):
            lines = value.split("\n")
            token_style = style.style_for_token(ttype)
            for i, line in enumerate(lines):
                if i > 0:
                    y += 1
                    x = 0

                if len(line) == 0:
                    continue

                end = x + wcswidth(line)
                if token_style["color"]:
                    self.canvas[y, x:end]["fg_color"] = Color.from_hex(
                        token_style["color"]
                    )
                if token_style["bgcolor"]:
                    self.canvas[y, x:end]["bg_color"] = Color.from_hex(
                        token_style["bgcolor"]
                    )
                if token_style["bold"]:
                    self.canvas[y, x:end]["style"] |= Style.BOLD
                if token_style["italic"]:
                    self.canvas[y, x:end]["style"] |= Style.ITALIC
                if token_style["underline"]:
                    self.canvas[y, x:end]["style"] |= Style.UNDERLINE
                x = end

    def add_str(
        self,
        str: str,
        *,
        pos: Pointlike = Point(0, 0),
        fg_color: Color | None = None,
        bg_color: Color | None = None,
        markdown: bool = False,
        truncate_str: bool = False,
    ):
        """
        Add a single line of text to the canvas at position `pos`.

        If `markdown` is true, text can be styled using batgrl markdown. The syntax is:
        - italic: `*this is italic text*`
        - bold: `**this is bold text**`
        - strikethrough: `~~this is strikethrough text~~`
        - underlined: `__this is underlined text__`
        - overlined: `^^this is overlined text^^`

        Parameters
        ----------
        str : str
            A single line of text to add to canvas.
        pos : Pointlike, default: Point(0, 0)
            Position of first character of string. Negative coordinates position
            from the right or bottom of canvas (like negative indices).
        fg_color : Color | None, default: None
            Foreground color of text.
        bg_color : Color | None, default: None
            Background color of text.
        markdown : bool, default: False
            Whether to parse text for batgrl markdown.
        truncate_str : bool, default: False
            If false, an `IndexError` is raised if the text would not fit on canvas.

        See Also
        --------
        text_tools.add_text : Add multiple lines of text to a view of a canvas.
        """
        y, x = pos
        add_text(
            self.canvas[y, x:],
            str,
            fg_color=fg_color,
            bg_color=bg_color,
            markdown=markdown,
            truncate_text=truncate_str,
        )

    def set_text(
        self,
        text: str,
        *,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
        markdown: bool = False,
    ):
        """
        Resize gadget to fit text, erase canvas, then fill canvas with text.

        If `markdown` is true, text can be styled using batgrl markdown. The syntax is:
        - italic: `*this is italic text*`
        - bold: `**this is bold text**`
        - strikethrough: `~~this is strikethrough text~~`
        - underlined: `__this is underlined text__`
        - overlined: `^^this is overlined text^^`

        Parameters
        ----------
        text : str
            Text to add to canvas.
        fg_color : Color | None, default: None
            Foreground color of text.
        bg_color : Color | None, default: None
            Background color of text.
        markdown : bool, default: False
            Whether to parse text for batgrl markdown.

        See Also
        --------
        text_tools.add_text : Add multiple lines of text to a view of a canvas.
        """
        self.size, lines = _parse_batgrl_md(text) if markdown else _text_to_cells(text)
        self.clear()
        _write_cells_to_canvas(lines, self.canvas, fg_color, bg_color)

    def clear(self):
        """Fill canvas with default cell."""
        self.canvas[:] = self.default_cell

    def shift(self, n: int = 1):
        """
        Shift content in canvas up (or down in case of negative `n`).

        Rows at the bottom (or top) will be filled with the default cell.
        """
        if n > 0:
            self.canvas[:-n] = self.canvas[n:]
            self.canvas[-n:] = self.default_cell
        elif n < 0:
            self.canvas[-n:] = self.canvas[:n]
            self.canvas[:-n] = self.default_cell

    def _render(self, cells: Cell2D, graphics: RGBM_2D, kind: Enum2D) -> None:
        """Render visible region of gadget."""
        text_render(
            cells,
            graphics,
            kind,
            self.absolute_pos,
            self._is_transparent,
            self.canvas,
            self.alpha,
            self._region,
        )
