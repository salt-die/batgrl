"""A video player gadget."""
import asyncio
import atexit
import time
import warnings
from pathlib import Path
from platform import uname

import cv2
import numpy as np

from ..colors import ABLACK, AColor
from .graphics import (
    Graphics,
    Interpolation,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)

__all__ = [
    "Interpolation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "VideoPlayer",
]

_IS_WSL: bool = uname().system == "Linux" and uname().release.endswith("Microsoft")


class VideoPlayer(Graphics):
    r"""
    A video player.

    Parameters
    ----------
    source : pathlib.Path | str | int
        A path to video, URL to video stream, or video capturing device (by index).
        Trying to open a video capturing device on WSL will issue a warning.
    loop : bool, default: True
        If true, restart video after last frame.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If gadget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
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
    is_transparent : bool, default: False
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
    source : Path | str | int
        A path, URL, or capturing device (by index) of the video.
    loop : bool
        If true, video will restart after last frame.
    is_device : bool
        If true, video is from a video capturing device.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget if :attr:`is_transparent` is true.
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
        Play the video. Returns a task.
    pause():
        Pause the video.
    seek():
        Seek to certain time (in seconds) in the video.
    stop():
        Stop the video.
    to_png(path):
        Write :attr:`texture` to provided path as a `png` image.
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
        source: Path | str | int,
        loop: bool = True,
        default_color: AColor = ABLACK,
        is_transparent: bool = False,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            default_color=default_color,
            is_transparent=is_transparent,
            alpha=alpha,
            interpolation=interpolation,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._current_frame = None
        self._resource = None
        self._video_task = None
        self.source = source
        self.loop = loop

    def on_remove(self):
        """Pause video and release resource on remove."""
        super().on_remove()
        self.pause()
        self._release_resource()

    @property
    def source(self) -> Path | str | int:
        """A path, URL, or capturing device (by index) of the video."""
        return self._source

    @source.setter
    def source(self, source: Path | str | int):
        self.pause()
        self._release_resource()
        if isinstance(source, Path) and not source.exists():
            raise FileNotFoundError(str(source))
        self._source = source
        self._load_resource()

    @property
    def is_device(self):
        """Return true if source is a video capturing device."""
        return isinstance(self._source, int)

    def _load_resource(self):
        source = self.source

        if _IS_WSL and self.is_device:
            # Because WSL doesn't support most USB devices (yet?), and trying to open
            # one with cv2 will pollute the terminal with cv2 errors, we don't attempt
            # to open a device in this case and instead issue a warning.
            warnings.warn("device not available on WSL")
            self._resource = None
            return

        if isinstance(source, Path):
            source = str(source.absolute())

        self._resource = cv2.VideoCapture(source)
        atexit.register(self._resource.release)

    def _release_resource(self):
        if self._resource is not None:
            self._resource.release()
            atexit.unregister(self._resource.release)
            self._resource = None
            self._current_frame = None
            self.texture[:] = self.default_color

    def on_size(self):
        """Resize current frame on resize."""
        h, w = self.size
        h *= 2
        self.texture = np.full((h, w, 4), self.default_color, dtype=np.uint8)

        if self._current_frame is not None:
            self.texture[:] = cv2.resize(
                self._current_frame,
                (w, h),
                interpolation=Interpolation._to_cv_enum[self.interpolation],
            )

    def _time_delta(self) -> float:
        return time.monotonic() - self._resource.get(cv2.CAP_PROP_POS_MSEC) / 1000

    async def _play_video(self):
        if self._resource is None:
            return

        self._start_time = self._time_delta()

        while self._resource.grab():
            if self.is_device:
                seconds_ahead = 0
            elif (seconds_ahead := self._start_time - self._time_delta()) < 0:
                continue

            await asyncio.sleep(seconds_ahead)

            _, frame = self._resource.retrieve()
            self._current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            self.texture[:] = cv2.resize(
                self._current_frame,
                (self.width, 2 * self.height),
                interpolation=Interpolation._to_cv_enum[self.interpolation],
            )

        if self.loop:
            self.seek(0)
            self.play()

    def pause(self):
        """Pause video."""
        if self._video_task is not None:
            self._video_task.cancel()

    def play(self) -> asyncio.Task:
        """
        Play video.

        Returns
        -------
        asyncio.Task
            The task that plays the video.
        """
        self.pause()

        if self._resource is None:
            self._load_resource()

        self._video_task = asyncio.create_task(self._play_video())
        return self._video_task

    def seek(self, time: float):
        """If supported, seek to certain time (in seconds) in the video."""
        if self._resource is not None and not self.is_device:
            self._resource.set(cv2.CAP_PROP_POS_MSEC, time * 1000)
            self._resource.grab()
            self._start_time = self._time_delta()

    def stop(self):
        """Stop video."""
        self.pause()
        self.seek(0)
        self._current_frame = None
        self.texture[:] = self.default_color
