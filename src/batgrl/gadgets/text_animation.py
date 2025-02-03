"""A text animation gadget."""

import asyncio
from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

from ..text_tools import Cell, add_text, str_width
from .text import Point, PosHint, Size, SizeHint, Text

__all__ = ["TextAnimation", "Point", "Size"]


class _Frame(Text):
    def on_size(self):
        pass


class TextAnimation(Text):
    r"""
    A text animation gadget.

    Parameters
    ----------
    frames : Iterable[str] | None, default: None
        Frames of the animation.
    frame_durations : float | int | Sequence[float| int], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    loop : bool, default: True
        Whether to restart animation after last frame.
    reverse : bool, default: False
        Whether to play animation in reverse.
    default_cell : NDArray[Cell] | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 0.0
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
    min_animation_size : Size
        The minimum size needed to not clip any frames of the animation.
    frames : list[str]
        Frames of the animation.
    frame_durations : list[int | float]
        Time each frame is displayed.
    loop : bool
        Whether to restart animation after last frame.
    reverse : bool
        Whether to play animation in reverse.
    canvas : NDArray[Cell]
        The array of characters for the gadget.
    default_cell : NDArray[Cell]
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
    play()
        Play the animation. Returns a task.
    pause()
        Pause the animation
    stop()
        Stop the animation and reset current frame.
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

    def __init__(
        self,
        *,
        frames: Iterable[str] | None = None,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        default_cell: NDArray[Cell] | str = " ",
        alpha: float = 0.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.frames: Iterable[str] = list(frames)
        """Frames of the animation."""
        self.frame_durations: Sequence[float]
        """Time each frame is displayed."""

        nframes = len(frames)
        if isinstance(frame_durations, Sequence):
            if len(frame_durations) != nframes:
                raise ValueError(
                    "number of frames doesn't match number of frame durations"
                )
            self.frame_durations = frame_durations
        else:
            self.frame_durations = [frame_durations] * nframes

        super().__init__(
            default_cell=default_cell,
            alpha=alpha,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self._sized_frames: list[NDArray[Cell]] = []
        """Frames of the animation converted to NDArray[Cell] and sized to gadget."""
        for frame in self.frames:
            canvas = self._canvas.copy()
            add_text(canvas, frame, truncate_text=True)
            self._sized_frames.append(canvas)

        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def canvas(self) -> NDArray[Cell]:
        """The array of characters for the gadget."""
        if self._i < len(self.frames):
            return self._sized_frames[self._i]
        return self._canvas

    @canvas.setter
    def canvas(self, canvas: NDArray[Cell]) -> None:
        self._canvas = canvas

    @property
    def min_animation_size(self) -> Size:
        """The minimum size needed to not clip any frames of the animation."""
        h = w = 0
        for frame in self.frames:
            lines = frame.split("\n")
            if len(lines) > h:
                h = len(lines)
            frame_width = max(str_width(line) for line in lines)
            if frame_width > w:
                w = frame_width
        return Size(h, w)

    def on_remove(self) -> None:
        """Pause animation on remove."""
        self.pause()
        super().on_remove()

    def on_size(self) -> None:
        """Update size of all frames on resize."""
        self._canvas = np.full(self._size, self._default_cell)
        self._sized_frames = []
        for frame in self.frames:
            canvas = self._canvas.copy()
            add_text(canvas, frame, truncate_text=True)
            self._sized_frames.append(canvas)

    async def _play_animation(self):
        while self.frames:
            try:
                await asyncio.sleep(self.frame_durations[self._i])
            except asyncio.CancelledError:
                return

            if self.reverse:
                self._i -= 1
                if self._i < 0:
                    self._i = len(self.frames) - 1

                    if not self.loop:
                        return
            else:
                self._i += 1
                if self._i == len(self.frames):
                    self._i = 0

                    if not self.loop:
                        return

    def play(self) -> asyncio.Task:
        """
        Play animation.

        Returns
        -------
        asyncio.Task
            The task that plays the animation.
        """
        self.pause()

        if self._i == 0 and self.reverse:
            self._i = len(self.frames) - 1
        elif self._i == len(self.frames) - 1 and not self.reverse:
            self._i = 0

        self._animation_task = asyncio.create_task(self._play_animation())
        return self._animation_task

    def pause(self) -> None:
        """Pause animation."""
        if self._animation_task is not None:
            self._animation_task.cancel()

    def stop(self) -> None:
        """Stop the animation and reset current frame."""
        self.pause()
        self._i = len(self.frames) - 1 if self.reverse else 0
