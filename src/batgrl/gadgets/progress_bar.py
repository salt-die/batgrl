"""A progress bar gadget."""

import asyncio
from itertools import chain, cycle

from ..text_tools import smooth_horizontal_bar, smooth_vertical_bar
from .behaviors.themable import Themable
from .gadget import Gadget, Point, PosHint, Size, SizeHint, bindable, clamp
from .text import Text

__all__ = ["ProgressBar", "Point", "Size"]


class ProgressBar(Themable, Gadget):
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
    progress : float | None
        Current progress as a value between `0.0` and `1.0` or `None`.
    animation_delay : float
        Time between loading animation updates.
    is_horizontal : bool
        If true, the bar will progress to the right, else upwards.
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
    update_theme()
        Paint the gadget with current theme.
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
        is_horizontal: bool = True,
        animation_delay: float = 1 / 60,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._bar = Text()
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.add_gadget(self._bar)
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
    @bindable
    def progress(self, progress: float):
        self._progress = None if progress is None else clamp(progress, 0.0, 1.0)
        self._update_bar()

    def _update_bar(self):
        if self.root is None:
            return

        self._bar.size = self.size

        if getattr(self, "_loading_task", False):
            self._loading_task.cancel()

        if self._progress is None:
            self._loading_task = asyncio.create_task(self._loading_animation())
        else:
            self._paint_progress_bar()

    @property
    def is_horizontal(self) -> bool:
        """If true, the bar will progress to the right, else upwards."""
        return self._is_horizontal

    @is_horizontal.setter
    def is_horizontal(self, is_horizontal: bool):
        self._is_horizontal = is_horizontal
        self._update_bar()

    def _paint_small_horizontal_bar(self, progress):
        bar_width = max(1, (self.width - 1) // 2)
        x, offset = divmod(progress * (self.width - bar_width), 1)
        x = int(x)
        smooth_bar = smooth_horizontal_bar(bar_width, 1, offset)

        self._bar.clear()
        canvas = self._bar.canvas
        canvas["char"][:, x : x + len(smooth_bar)] = smooth_bar
        canvas[["fg_color", "bg_color"]] = self.color_theme.progress_bar
        if offset:
            canvas["reverse"][:, x] = True

    def _paint_small_vertical_bar(self, progress):
        bar_height = max(1, (self.height - 1) // 2)
        y, offset = divmod(progress * (self.height - bar_height), 1)
        y = int(y)
        smooth_bar = smooth_vertical_bar(bar_height, 1, offset)

        self._bar.clear()
        canvas = self._bar.canvas
        canvas["char"][::-1][y : y + len(smooth_bar)].T[:] = smooth_bar
        canvas[["fg_color", "bg_color"]] = self.color_theme.progress_bar
        if offset:
            canvas["reverse"][::-1][y] = True

    async def _loading_animation(self):
        if (
            self.is_horizontal
            and self.width < 3
            or not self.is_horizontal
            and self.height < 3
        ):
            return

        self._bar.canvas["char"] = " "

        if self._is_horizontal:
            steps = 8 * self.width
            paint = self._paint_small_horizontal_bar
        else:
            steps = 8 * self.height
            paint = self._paint_small_vertical_bar

        for i in cycle(chain(range(steps + 1), range(steps)[::-1])):
            paint(i / steps)
            await asyncio.sleep(self.animation_delay)

    def on_add(self):
        """Start loading animation on add if progress is None."""
        super().on_add()
        self._update_bar()

    def on_remove(self):
        """Cancel loading animation on remove."""
        super().on_remove()
        if task := getattr(self, "_loading_task", False):
            task.cancel()

    def on_size(self):
        """Repaint bar on resize."""
        self._update_bar()

    def update_theme(self):
        """Paint the gadget with current theme."""
        self._bar.canvas[["fg_color", "bg_color"]] = self.color_theme.progress_bar
        self.default_fg_color = self.color_theme.progress_bar.fg
        self.default_bg_color = self.color_theme.progress_bar.bg

    def _paint_progress_bar(self):
        self._bar.clear()
        canvas = self._bar.canvas
        canvas[["fg_color", "bg_color"]] = self.color_theme.progress_bar
        if self.is_horizontal:
            smooth_bar = smooth_horizontal_bar(self.width, self.progress)
            canvas["char"][:, : len(smooth_bar)] = smooth_bar
        else:
            smooth_bar = smooth_vertical_bar(self.height, self.progress)
            canvas["char"][::-1][: len(smooth_bar)].T[:] = smooth_bar
