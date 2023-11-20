"""A progress bar gadget."""
import asyncio
from itertools import chain, cycle

from numpy.typing import NDArray

from ..colors import WHITE_ON_BLACK, ColorPair
from .behaviors.themable import Themable
from .gadget import clamp, subscribable
from .text import Char, Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict, Text
from .text_tools import smooth_horizontal_bar, smooth_vertical_bar

__all__ = [
    "ProgressBar",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class ProgressBar(Themable, Text):
    r"""
    A progress bar gadget.

    Setting :attr:`progress` to `None` will start a "loading" animation; otherwise
    setting to a value between `0.0` and `1.0` will update the bar.

    Parameters
    ----------
    animation_delay : float, default: 1/60
        Time between loading animation updates.
    is_horizontal : bool, default: True
        If true, the bar will progress to the right, else upwards.
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
    progress : float | None
        Current progress as a value between `0.0` and `1.0` or `None`.
    animation_delay : float
        Time between loading animation updates.
    is_horizontal : bool
        If true, the bar will progress to the right, else upwards.
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
    update_theme():
        Paint the gadget with current theme.
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
        is_horizontal: bool = True,
        animation_delay: float = 1 / 60,
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
            default_char=default_char,
            default_color_pair=default_color_pair,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.animation_delay = animation_delay
        self._is_horizontal = is_horizontal
        self._progress = None

    @property
    def progress(self) -> float:
        """
        Current progress as a value between `0.0` and `1.0` or `None`.

        If progress is `None`, a loading animation will play.
        """
        return self._progress

    @progress.setter
    @subscribable
    def progress(self, progress: float):
        if getattr(self, "_loading_task", False):
            self._loading_task.cancel()

        if progress is None:
            self._progress = progress
            self._loading_task = asyncio.create_task(self._loading_animation())
        else:
            self._progress = clamp(progress, 0.0, 1.0)
            self._repaint_progress_bar()

    @property
    def is_horizontal(self) -> bool:
        """If true, the bar will progress to the right, else upwards."""
        return self._is_horizontal

    @is_horizontal.setter
    def is_horizontal(self, is_horizontal: bool):
        self._is_horizontal = is_horizontal
        self.progress = self.progress  # Trigger a repaint by setting property.

    def _paint_small_horizontal_bar(self, progress):
        bar_width = max(1, (self.width - 1) // 2)
        x, offset = divmod(progress * (self.width - bar_width), 1)
        x = int(x)
        smooth_bar = smooth_horizontal_bar(bar_width, 1, offset)

        self.canvas[:] = self.default_char
        self.canvas["char"][:, x : x + len(smooth_bar)] = smooth_bar
        self.colors[:] = self.color_theme.progress_bar
        if offset != 0:
            self.colors[:, x] = self.color_theme.progress_bar.reversed()

    def _paint_small_vertical_bar(self, progress):
        bar_height = max(1, (self.height - 1) // 2)
        y, offset = divmod(progress * (self.height - bar_height), 1)
        y = int(y)
        smooth_bar = smooth_vertical_bar(bar_height, 1, offset)

        self.canvas[:] = self.default_char
        self.canvas["char"][::-1][y : y + len(smooth_bar)].T[:] = smooth_bar
        self.colors[:] = self.color_theme.progress_bar
        if offset != 0:
            self.colors[::-1][y] = self.color_theme.progress_bar.reversed()

    async def _loading_animation(self):
        if (
            self.is_horizontal
            and self.width < 3
            or not self.is_horizontal
            and self.height < 3
        ):
            return

        self.canvas[:] = self.default_char

        if self._is_horizontal:
            HSTEPS = 8 * self.width
            for i in cycle(chain(range(HSTEPS + 1), range(HSTEPS)[::-1])):
                self._paint_small_horizontal_bar(i / HSTEPS)
                await asyncio.sleep(self.animation_delay)
        else:
            VSTEPS = 8 * self.height
            for i in cycle(chain(range(VSTEPS + 1), range(VSTEPS)[::-1])):
                self._paint_small_vertical_bar(i / VSTEPS)
                await asyncio.sleep(self.animation_delay)

    def on_add(self):
        """Start loading animation on add if progress is None."""
        super().on_add()
        self.progress = self.progress  # Restart loading animation.

    def on_remove(self):
        """Cancel loading animation on remove."""
        super().on_remove()
        if task := getattr(self, "_loading_task", False):
            task.cancel()

    def on_size(self):
        """Repaint bar on resize."""
        super().on_size()
        self.progress = self.progress  # Trigger a repaint by setting property.

    def update_theme(self):
        """Paint the gadget with current theme."""
        self.colors[:] = self.color_theme.progress_bar
        self.default_color_pair = self.color_theme.progress_bar

    def _repaint_progress_bar(self):
        self.canvas[:] = self.default_char
        if self.is_horizontal:
            smooth_bar = smooth_horizontal_bar(self.width, self.progress)
            self.canvas["char"][:, : len(smooth_bar)] = smooth_bar
        else:
            smooth_bar = smooth_vertical_bar(self.height, self.progress)
            self.canvas["char"][::-1][: len(smooth_bar)].T[:] = smooth_bar
