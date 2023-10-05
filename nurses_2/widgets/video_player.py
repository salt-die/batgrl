"""
A video player widget.
"""
import asyncio
import atexit
import time
import warnings
from pathlib import Path
from platform import uname

import cv2
import numpy as np

from ..colors import ABLACK, AColor, ColorPair
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
    """
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
        If widget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: "linear"
        Interpolation used when widget is resized.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

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
        Transparency of widget if :attr:`is_transparent` is true.
    interpolation : Interpolation
        Interpolation used when widget is resized.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    play:
        Play the video. Returns a task.
    pause:
        Pause the video.
    seek:
        Seek to certain time (in seconds) in the video.
    stop:
        Stop the video.
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )
        self._current_frame = None
        self._resource = None
        self._video_task = None
        self.source = source
        self.loop = loop

    def on_remove(self):
        super().on_remove()
        self.pause()
        self._release_resource()

    @property
    def source(self) -> Path | str | int:
        return self._source

    @source.setter
    def source(self, source: Path | str | int):
        self.pause()
        self._release_resource()
        self._source = source
        self._load_resource()

    @property
    def is_device(self):
        """
        Return true if source is a video capturing device.
        """
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
        """
        Pause video.
        """
        if self._video_task is not None:
            self._video_task.cancel()

    def play(self) -> asyncio.Task:
        """
        Play video.
        """
        self.pause()

        if self._resource is None:
            self._load_resource()

        self._video_task = asyncio.create_task(self._play_video())
        return self._video_task

    def seek(self, time: float):
        """
        If supported, seek to certain time (in seconds) in the video.
        """
        if self._resource is not None and not self.is_device:
            self._resource.set(cv2.CAP_PROP_POS_MSEC, time * 1000)
            self._resource.grab()
            self._start_time = self._time_delta()

    def stop(self):
        """
        Stop video.
        """
        self.pause()
        self.seek(0)
        self._current_frame = None
        self.texture[:] = self.default_color
