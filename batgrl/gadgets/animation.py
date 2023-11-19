"""An animation gadget."""
import asyncio
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .gadget_base import (
    Char,
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
    subscribable,
)
from .image import Image, Interpolation

__all__ = [
    "Animation",
    "Interpolation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


def _check_frame_durations(
    frames: list[Image], frame_durations: float | Sequence[float]
) -> Sequence[float]:
    """
    Raise `ValueError` if `frames` and `frame_durations` are incompatible,
    else return a sequence of frame durations.
    """
    if isinstance(frame_durations, float):
        return [frame_durations] * len(frames)

    if len(frame_durations) != len(frames):
        raise ValueError("number of frames doesn't match number of frame durations")

    return frame_durations


class Animation(GadgetBase):
    r"""
    An animation gadget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for frames in the animation (loaded
        in lexographical order of filenames).
    frame_durations : float | Sequence[float], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    loop : bool, default: True
        If true, restart animation after last frame.
    reverse : bool, default: False
        If true, play animation in reverse.
    alpha : float, default: 1.0
        Transparency of the animation.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        A transparent gadget allows regions beneath it to be painted. Additionally,
        non-transparent graphic gadgets are not alpha composited.
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
        If true, animation is restarted after last frame.
    reverse : bool
        If true, animation is played in reverse.
    alpha : float
        Transparency of the animation.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
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
    play():
        Play the animation. Returns a task.
    pause():
        Pause the animation
    stop():
        Stop the animation and reset current frame.
    from_textures(textures, ...):
        Create an :class:`Animation` from an iterable of uint8 RGBA numpy array.
    from_images(images, ...):
        Create an :class:`Animation` from an iterable of :class:`Image`.
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
        path: Path | None = None,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.frames: list[Image] = []
        """Frames of the animation."""

        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        if path is not None:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.frames = [Image(path=path, size=self.size) for path in paths]
            for frame in self.frames:
                frame.parent = self

        self.frame_durations = _check_frame_durations(self.frames, frame_durations)
        self.alpha = alpha
        self.interpolation = interpolation
        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def region(self) -> Region:
        """The visible portion of the gadget on the screen."""
        return self._region

    @region.setter
    def region(self, region: Region):
        self._region = region
        for frame in self.frames:
            frame.region = region

    def on_remove(self):
        """Pause animation."""
        self.pause()
        super().on_remove()

    def on_size(self):
        """Update size of all frames on resize."""
        for frame in self.frames:
            frame.size = self._size

    @property
    def is_transparent(self) -> bool:
        """If false, `alpha` and alpha channels are ignored."""
        return self._is_transparent

    @is_transparent.setter
    def is_transparent(self, transparent: bool):
        self._is_transparent = transparent
        for frame in self.frames:
            frame.is_transparent = True

    @property
    def alpha(self) -> float:
        """Transparency of gadget if :attr:`is_transparent` is true."""
        return self._alpha

    @alpha.setter
    @subscribable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)
        for frame in self.frames:
            frame.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        """Interpolation used when gadget is resized."""
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        self._interpolation = interpolation
        for frame in self.frames:
            frame.interpolation = interpolation

    async def _play_animation(self):
        while self.frames:
            await asyncio.sleep(self.frame_durations[self._i])

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

    def pause(self):
        """Pause animation."""
        if self._animation_task is not None:
            self._animation_task.cancel()

    def stop(self):
        """Stop the animation and reset current frame."""
        self.pause()
        self._i = len(self.frames) - 1 if self.reverse else 0

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """Render visible region of gadget into root's `canvas` and `colors` arrays."""
        if self.frames:
            self.frames[self._i].render(canvas, colors)
        else:
            super().render(canvas, colors)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[NDArray[np.uint8]],
        *,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> "Animation":
        """
        Create an :class:`Animation` from an iterable of uint8 RGBA numpy array.

        Parameters
        ----------
        textures : Iterable[NDArray[np.uint8]]
            An iterable of RGBA textures that will be the frames of the animation.
        frame_durations : float | Sequence[float], default: 1/12
            Time each frame is displayed. If a sequence is provided, it's length
            should be equal to number of frames.
        loop : bool, default: True
            If true, restart animation after last frame.
        reverse : bool, default: False
            If true, play animation in reverse.
        alpha : float, default: 1.0
            Transparency of the animation.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        size : Size, default: Size(10, 10)
            Size of gadget.
        pos : Point, default: Point(0, 0)
            Position of upper-left corner in parent.
        size_hint : SizeHint | SizeHintDict | None, default: None
            Size as a proportion of parent's height and width.
        pos_hint : PosHint | PosHintDict | None , default: None
            Position as a proportion of parent's height and width.
        is_transparent : bool, default: True
            If true, gadget is rendered with alpha compositing; otherwise, alpha values
            are ignored.
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
        animation = cls(
            frame_durations=frame_durations,
            loop=loop,
            reverse=reverse,
            alpha=alpha,
            interpolation=interpolation,
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        animation.frames = [
            Image.from_texture(
                texture,
                size=animation.size,
                alpha=animation.alpha,
                interpolation=animation.interpolation,
            )
            for texture in textures
        ]
        for frame in animation.frames:
            frame.parent = animation
        animation.frame_durations = _check_frame_durations(
            animation.frames, frame_durations
        )
        return animation

    @classmethod
    def from_images(
        cls,
        images: Iterable[Image],
        *,
        frame_durations: float | Sequence[float] = 1 / 12,
        loop: bool = True,
        reverse: bool = False,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> "Animation":
        """
        Create an :class:`Animation` from an iterable of :class:`Image`.

        Parameters
        ----------
        images : Iterable[Image]
            An iterable of images that will be the frames of the animation.
        frame_durations : float | Sequence[float], default: 1/12
            Time each frame is displayed. If a sequence is provided, it's length
            should be equal to number of frames.
        loop : bool, default: True
            If true, restart animation after last frame.
        reverse : bool, default: False
            If true, play animation in reverse.
        alpha : float, default: 1.0
            Transparency of the animation.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        size : Size, default: Size(10, 10)
            Size of gadget.
        pos : Point, default: Point(0, 0)
            Position of upper-left corner in parent.
        size_hint : SizeHint | SizeHintDict | None, default: None
            Size as a proportion of parent's height and width.
        pos_hint : PosHint | PosHintDict | None , default: None
            Position as a proportion of parent's height and width.
        is_transparent : bool, default: True
            If true, gadget is rendered with alpha compositing; otherwise, alpha values
            are ignored.
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
        animation = cls(
            frame_durations=frame_durations,
            loop=loop,
            reverse=reverse,
            alpha=alpha,
            interpolation=interpolation,
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        animation.frames = list(images)
        for image in animation.frames:
            image.interpolation = animation.interpolation
            image.size = animation.size
            image.alpha = animation.alpha
            image.parent = animation
        animation.frame_durations = _check_frame_durations(
            animation.frames, frame_durations
        )
        return animation
