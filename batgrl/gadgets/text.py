"""A text gadget."""
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer
from pygments.style import Style
from wcwidth import wcswidth

from ..colors import WHITE_ON_BLACK, Color, ColorPair, Neptune
from .gadget_base import (
    Anchor,
    Char,
    Easing,
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
    coerce_char,
    lerp,
    style_char,
    subscribable,
)
from .text_tools import add_text, parse_batgrl_md, text_to_chars, write_chars_to_canvas

__all__ = [
    "Anchor",
    "Border",
    "Char",
    "Easing",
    "Point",
    "PosHint",
    "PosHintDict",
    "Region",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Text",
    "add_text",
    "clamp",
    "coerce_char",
    "lerp",
    "style_char",
    "subscribable",
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
    "mcgugan_tall",
    "mcgugan_wide",
]
"""Border styles for :meth:`batgrl.text_gadget.Text.add_border`."""


class Text(GadgetBase):
    r"""
    A text gadget. Displays arbitrary text data.

    Parameters
    ----------
    default_char : NDArray[Char] | str, default: " "
        Default background character. This should be a single unicode half-width
        grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether whitespace is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    canvas : NDArray[Char]
        The array of characters for the gadget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in :attr:`canvas`.
    default_char : NDArray[Char]
        Default background character.
    default_color_pair : ColorPair
        Default color pair of gadget.
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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

    def __init__(
        self,
        *,
        default_char: NDArray[Char] | str = " ",
        default_color_pair: ColorPair = WHITE_ON_BLACK,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
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

        self.default_char = default_char
        self.default_color_pair = default_color_pair

        self.canvas = np.full(size, self.default_char)
        self.colors = np.full((*size, 6), default_color_pair, dtype=np.uint8)

    @property
    def default_char(self) -> NDArray[Char]:
        """Default character for text canvas."""
        return self._default_char

    @default_char.setter
    def default_char(self, char: NDArray[Char] | str):
        self._default_char = coerce_char(char, style_char(" "))

    def on_size(self):
        """Resize canvas and colors preserving as much content as possible."""
        old_h, old_w = self.canvas.shape

        h, w = self._size

        old_canvas = self.canvas
        old_colors = self.colors

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.canvas = np.full((h, w), self.default_char)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self.canvas[:copy_h, :copy_w] = old_canvas[:copy_h, :copy_w]
        self.colors[:copy_h, :copy_w] = old_colors[:copy_h, :copy_w]

    @property
    def default_fg_color(self) -> Color:
        """The default foreground color."""
        return self.default_color_pair.fg_color

    @property
    def default_bg_color(self) -> Color:
        """The default background color."""
        return self.default_color_pair.bg_color

    def add_border(
        self,
        style: Border = "light",
        bold: bool = False,
        color_pair: ColorPair | None = None,
    ):
        """
        Add a text border.

        Parameters
        ----------
        style : Border, default: "light"
            Style of border. Default style uses light box-drawing characters.
        bold : bool, default: False
            Whether the border is bold.
        color_pair : ColorPair | None, default: None
            Border color pair if not None.
        """
        BORDER_STYLES = {
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
            "mcgugan_tall": "▕▏▕▏▔▁▕▏",
            "mcgugan_wide": "▁▁▏▕▁▔▔▔",
        }
        tl, tr, lv, rv, th, bh, bl, br = BORDER_STYLES[style]

        canvas = self.canvas
        canvas[0, 0] = style_char(tl, bold=bold)
        canvas[0, -1] = style_char(tr, bold=bold)
        canvas[1:-1, 0] = style_char(lv, bold=bold)
        canvas[1:-1, -1] = style_char(rv, bold=bold)
        canvas[0, 1:-1] = style_char(th, bold=bold)
        canvas[-1, 1:-1] = style_char(bh, bold=bold)
        canvas[-1, 0] = style_char(bl, bold=bold)
        canvas[-1, -1] = style_char(br, bold=bold)

        if color_pair is not None:
            if style == "mcgugan_tall":
                self.colors[[0, -1], :, :3] = color_pair[:3]
                self.colors[:, [0, -1]] = color_pair
            elif style == "mcgugan_wide":
                self.colors[[0, -1]] = color_pair
                self.colors[:, [0, -1], :3] = color_pair[:3]
            else:
                self.colors[[0, -1]] = color_pair
                self.colors[:, [0, -1]] = color_pair

    def add_syntax_highlighting(
        self, lexer: Lexer | None = None, style: Style = Neptune
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
        text = "\n".join("".join(line).rstrip() for line in self.canvas["char"])
        if lexer is None:
            lexer = guess_lexer(text)

        self.colors[..., :3] = 0
        self.colors[..., 3:] = Color.from_hex(style.background_color)
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
                    self.colors[y, x:end, :3] = Color.from_hex(token_style["color"])
                if token_style["bgcolor"]:
                    self.colors[y, x:end, 3:] = Color.from_hex(token_style["bgcolor"])
                self.canvas[y, x:end]["bold"] = token_style["bold"]
                self.canvas[y, x:end]["italic"] = token_style["italic"]
                self.canvas[y, x:end]["underline"] = token_style["underline"]
                x = end

    def add_str(
        self,
        str: str,
        pos: Point = Point(0, 0),
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
        pos : Point, default: Point(0, 0)
            Position of first character of string. Negative coordinates position
            from the right or bottom of canvas (like negative indices).
        markdown : bool, default: False
            Whether to parse text for batgrl markdown.
        truncate_str : bool, default: False
            If false, an `IndexError` is raised if the text would not fit on canvas.

        See Also
        --------
        text_tools.add_text : Add multiple lines of text to a view of a canvas.
        """
        y, x = pos
        add_text(self.canvas[y, x:], str, markdown, truncate_text=truncate_str)

    def set_text(self, text: str, markdown: bool = False):
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
        markdown : bool, default: False
            Whether to parse text for batgrl markdown.

        See Also
        --------
        text_tools.add_text : Add multiple lines of text to a view of a canvas.
        """
        self.size, lines = parse_batgrl_md(text) if markdown else text_to_chars(text)

        self.canvas[:] = self.default_char
        self.colors[:] = self.default_color_pair

        write_chars_to_canvas(lines, self.canvas)

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """Render visible region of gadget into root's `canvas` and `colors` arrays."""
        abs_pos = self.absolute_pos
        if self.is_transparent:
            for rect in self.region.rects():
                dst_y, dst_x = rect.to_slices()
                src_y, src_x = rect.to_slices(abs_pos)

                visible = np.isin(
                    self.canvas[src_y, src_x]["char"], (" ", "⠀"), invert=True
                )

                canvas[dst_y, dst_x][visible] = self.canvas[src_y, src_x][visible]
                colors[dst_y, dst_x, :3][visible] = self.colors[src_y, src_x, :3][
                    visible
                ]
        else:
            for rect in self.region.rects():
                dst = rect.to_slices()
                src = rect.to_slices(abs_pos)
                canvas[dst] = self.canvas[src]
                colors[dst] = self.colors[src]
