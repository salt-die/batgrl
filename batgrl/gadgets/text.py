"""
A text gadget.
"""
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
from .text_tools import add_text

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
]
"""Border styles for :meth:`batgrl.text_gadget.Text.add_border`."""


class Text(GadgetBase):
    """
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
    add_str(str, pos, ...):
        Add a single line of text to the canvas.
    set_text(text, ...):
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    on_size():
        Called when gadget is resized.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        True if point collides with an uncovered portion of gadget.
    collides_gadget(other):
        True if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\\*gadgets):
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
        Called after a gadget is added to gadget tree.
    on_remove():
        Called before gadget is removed from gadget tree.
    prolicide():
        Recursively remove all children.
    destroy():
        Destroy this gadget and all descendents.
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
        return self._default_char

    @default_char.setter
    def default_char(self, char: NDArray[Char] | str):
        self._default_char = coerce_char(char, style_char(" "))

    def on_size(self):
        # Preserve content as much as possible.
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
        """
        The default foreground color.
        """
        return self.default_color_pair.fg_color

    @property
    def default_bg_color(self) -> Color:
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
            self.colors[[0, -1]] = color_pair
            self.colors[:, [0, -1]] = color_pair

    def add_syntax_highlight(self, lexer: Lexer | None = None, style: Style = Neptune):
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
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        overline: bool = False,
        truncate_str: bool = False,
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
        overline : bool, default: False
            Whether text is overlined.
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
            bold=bold,
            italic=italic,
            underline=underline,
            strikethrough=strikethrough,
            overline=overline,
            truncate_text=truncate_str,
        )

    def set_text(
        self,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        overline: bool = False,
    ):
        """
        Resize gadget to fit text, erase canvas, then fill canvas with text.

        Parameters
        ----------
        text : str
            Text to add to canvas.
        bold : bool, default: False
            Whether text is bold.
        italic : bool, default: False
            Whether text is italic.
        underline : bool, default: False
            Whether text is underlined.
        strikethrough : bool, default: False
            Whether text is strikethrough.
        overline : bool, default: False
            Whether text is overlined.

        See Also
        --------
        text_tools.add_text : Add multiple lines of text to a view of a canvas.
        """
        lines = text.split("\n")
        height = len(lines)
        width = max(map(wcswidth, lines), default=0)
        self.size = height, width
        self.canvas[:] = self.default_char
        add_text(
            self.canvas,
            text,
            bold=bold,
            italic=italic,
            underline=underline,
            strikethrough=strikethrough,
            overline=overline,
        )

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """
        Paint region given by source into canvas_view and colors_view.
        """
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
