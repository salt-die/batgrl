"""A text animation gadget."""

import asyncio
from collections.abc import Iterable, Sequence

from ..colors import BLACK, WHITE, Color
from .animation import _check_frame_durations
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .pane import Pane
from .text import Text

__all__ = ["TextAnimation", "Point", "Size"]


class _Frame(Text):
    def on_size(self):
        pass


class TextAnimation(Gadget):
    r"""
    A text animation gadget.

    Parameters
    ----------
    frames : Iterable[str] | None, default: None
        Frames of the animation.
    frame_durations : float | int | Sequence[float| int], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    animation_fg_color : Color, default: WHITE
        Foreground color of animation.
    animation_bg_color : Color, default: BLACK
        Background color of animation.
    loop : bool, default: True
        Whether to restart animation after last frame.
    reverse : bool, default: False
        Whether to play animation in reverse.
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
    frames : list[Text]
        Frames of the animation.
    frame_durations : list[int | float]
        Time each frame is displayed.
    animation_fg_color : Color
        Foreground color of animation.
    animation_bg_color : Color
        Background color of animation.
    loop : bool
        Whether to restart animation after last frame.
    reverse : bool
        Whether to play animation in reverse.
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
        animation_fg_color: Color = WHITE,
        animation_bg_color: Color = BLACK,
        loop: bool = True,
        reverse: bool = False,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.frames: Iterable[Text] = []
        if frames is not None:
            for frame in frames:
                self.frames.append(Text())
                self.frames[-1].set_text(frame)
                self.frames[-1].parent = self
        self._pane = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_transparent=is_transparent,
        )
        self._frame = _Frame(is_enabled=False, is_transparent=True)
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.add_gadgets(self._pane, self._frame)
        self.frame_durations: list[float] = _check_frame_durations(
            self.frames, frame_durations
        )
        self.animation_fg_color = animation_fg_color
        self.animation_bg_color = animation_bg_color
        self.loop = loop
        self.reverse = reverse
        self.alpha = alpha
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def animation_fg_color(self) -> Color:
        """Foreground color pair of animation."""
        return self._pane.fg_color

    @animation_fg_color.setter
    def animation_fg_color(self, animation_fg_color: Color):
        self._pane.fg_color = animation_fg_color
        self._animation_fg_color = animation_fg_color
        for frame in self.frames:
            frame.canvas["fg_color"] = animation_fg_color

    @property
    def animation_bg_color(self) -> Color:
        """Foreground color pair of animation."""
        return self._pane.bg_color

    @animation_bg_color.setter
    def animation_bg_color(self, animation_bg_color: Color):
        self._pane.bg_color = animation_bg_color
        self._animation_bg_color = animation_bg_color
        for frame in self.frames:
            frame.canvas["bg_color"] = animation_bg_color

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._pane.is_transparent = self.is_transparent

    @property
    def alpha(self) -> bool:
        """Transparency of gadget."""
        return self._pane.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._pane.alpha = alpha

    def on_remove(self):
        """Pause animation on remove."""
        self.pause()
        super().on_remove()

    async def _play_animation(self):
        while self.frames:
            current_frame = self.frames[self._i]
            self._frame.canvas = current_frame.canvas
            self._frame.size = current_frame.size
            self._frame.is_enabled = True
            try:
                await asyncio.sleep(self.frame_durations[self._i])
            except asyncio.CancelledError:
                self._frame.is_enabled = False
                return

            if self.reverse:
                self._i -= 1
                if self._i < 0:
                    self._i = len(self.frames) - 1

                    if not self.loop:
                        self._frame.is_enabled = False
                        return
            else:
                self._i += 1
                if self._i == len(self.frames):
                    self._i = 0

                    if not self.loop:
                        self._frame.is_enabled = False
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

    def pause(self):
        """Pause animation."""
        if self._animation_task is not None:
            self._animation_task.cancel()

    def stop(self):
        """Stop the animation and reset current frame."""
        self.pause()
        self._i = len(self.frames) - 1 if self.reverse else 0
