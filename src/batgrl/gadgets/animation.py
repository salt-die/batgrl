"""An animation gadget."""

import asyncio
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Self

import numpy as np
from numpy.typing import NDArray

from ..colors import TRANSPARENT, AColor
from ..texture_tools import read_texture, resize_texture
from .graphics import (
    Blitter,
    Graphics,
    Interpolation,
    Point,
    PosHint,
    Size,
    SizeHint,
    scale_geometry,
)

__all__ = ["Animation", "Interpolation", "Point", "Size"]


class Animation(Graphics):
    r"""
    An animation gadget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for frames in the animation (loaded in lexographical
        order of filenames).
    frame_durations : float | Sequence[float], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length should be
        equal to number of frames.
    loop : bool, default: True
        Whether to restart animation after last frame.
    reverse : bool, default: False
        Whether to play animation in reverse.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        Transparency of gadget.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    blitter : Blitter, default: "half"
        Determines how graphics are rendered.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    frames : list[Image]
        Frames of the animation.
    frame_durations : list[int | float]
        Time each frame is displayed.
    loop : bool
        Whether to animation is restarted after last frame.
    reverse : bool
        Whether to animation is played in reverse.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    blitter : Blitter
        Determines how graphics are rendered.
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
    from_textures(textures, ...)
        Create an :class:`Animation` from an iterable of uint8 RGBA numpy array.
    to_png(path)
        Write :attr:`texture` to provided path as a `png` image.
    clear()
        Fill texture with default color.
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
        path: Path | None = None,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        blitter: Blitter = "half",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.frames: list[NDArray[np.uint8]]
        """Frames of the animation."""
        # Set in `on_size`
        self._sized_frames: list[NDArray[np.uint8]]
        """Resized frames of the animation."""

        if path is None:
            self.frames = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.frames = [read_texture(path) for path in paths]

        self.frame_durations: Sequence[float]
        """Time each frame is displayed."""

        nframes = len(self.frames)
        if isinstance(frame_durations, Sequence):
            if len(frame_durations) != nframes:
                raise ValueError(
                    "number of frames doesn't match number of frame durations"
                )
            self.frame_durations = frame_durations
        else:
            self.frame_durations = [frame_durations] * nframes

        super().__init__(
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            blitter=blitter,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def texture(self) -> NDArray[np.uint8]:
        """uint8 RGBA color array."""
        if self._i < len(self.frames):
            return self._sized_frames[self._i]
        return self._texture

    @texture.setter
    def texture(self, texture: NDArray[np.uint8]) -> None:
        self._texture = texture

    def on_remove(self) -> None:
        """Pause animation."""
        self.pause()
        super().on_remove()

    def on_size(self) -> None:
        """Update size of all frames on resize."""
        size = scale_geometry(self._blitter, self._size)
        self._texture = np.full((*size, 4), self.default_color, np.uint8)
        self._sized_frames = [
            resize_texture(texture, size, self.interpolation) for texture in self.frames
        ]

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
                if self._i >= len(self.frames):
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

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[NDArray[np.uint8]],
        *,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        blitter: Blitter = "half",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> Self:
        """
        Create an :class:`Animation` from an iterable of uint8 RGBA numpy array.

        Parameters
        ----------
        textures : Iterable[NDArray[np.uint8]]
            An iterable of RGBA textures that will be the frames of the animation.
        frame_durations : float | Sequence[float], default: 1/12
            Time each frame is displayed. If a sequence is provided, it's length should
            be equal to number of frames.
        loop : bool, default: True
            Whether to restart animation after last frame.
        reverse : bool, default: False
            Whether to play animation in reverse.
        default_color : AColor, default: AColor(0, 0, 0, 0)
            Default texture color.
        alpha : float, default: 1.0
            Transparency of gadget.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        blitter : Blitter, default: "half"
            Determines how graphics are rendered.
        size : Size, default: Size(10, 10)
            Size of gadget.
        pos : Point, default: Point(0, 0)
            Position of upper-left corner in parent.
        size_hint : SizeHint | None, default: None
            Size as a proportion of parent's height and width.
        pos_hint : PosHint | None, default: None
            Position as a proportion of parent's height and width.
        is_transparent : bool, default: True
            Whether gadget is transparent.
        is_visible : bool, default: True
            Whether gadget is visible. Gadget will still receive input events if not
            visible.
        is_enabled : bool, default: True
            Whether gadget is enabled. A disabled gadget is not painted and doesn't
            receive input events.

        Returns
        -------
        Animation
            A new animation gadget.
        """
        frames = list(textures)
        nframes = len(frames)
        if isinstance(frame_durations, Sequence):
            if len(frame_durations) != nframes:
                raise ValueError(
                    "number of frames doesn't match number of frame durations"
                )
        else:
            frame_durations = [frame_durations] * nframes

        animation = cls(
            loop=loop,
            reverse=reverse,
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            blitter=blitter,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        animation.frames = frames
        animation.frame_durations = frame_durations
        animation.on_size()
        return animation
