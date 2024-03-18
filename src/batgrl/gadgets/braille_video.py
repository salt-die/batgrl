"""A video gadget that renders to braille unicode characters in grayscale."""
import asyncio
import atexit
import time
import warnings
from pathlib import Path
from platform import uname

import cv2
import numpy as np

from ..colors import BLACK, WHITE, Color
from ..geometry import lerp
from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text
from .text_tools import binary_to_braille

__all__ = ["BrailleVideo", "Point", "Size"]

_IS_WSL: bool = uname().system == "Linux" and uname().release.endswith("Microsoft")


class BrailleVideo(Gadget):
    r"""
    A video gadget that renders to braille unicode characters in grayscale.

    Parameters
    ----------
    source : pathlib.Path | str | int
        A path to video, URL to video stream, or video capturing device (by index).
        Trying to open a video capturing device on WSL will issue a warning.
    fg_color : Color, default: WHITE
        Foreground color of video.
    bg_color : Color, default: BLACK
        Background color of video.
    loop : bool, default: True
        If true, restart video after last frame.
    gray_threshold : int, default: 127
        Pixel values over this threshold in the source video will be rendered.
    enable_shading : bool, default: False
        Whether foreground colors are shaded.
    invert_colors : bool, default: False
        Invert the colors in the source before rendering.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
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
    source : Path | str | int
        A path, URL, or capturing device (by index) of the video.
    fg_color : Color
        Foreground color of video.
    bg_color : Color
        Background color of video.
    loop : bool
        If true, video will restart after last frame.
    gray_threshold : int
        Pixel values over this threshold in the source video will be rendered.
    enable_shading : bool
        Whether foreground colors are shaded.
    invert_colors : bool
        If true, colors in the source are inverted before video is rendered.
    alpha : float
        Transparency of gadget.
    is_device : bool
        If true, video is from a video capturing device.
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
        Play the video. Returns a task.
    pause()
        Pause the video.
    seek()
        Seek to certain time (in seconds) in the video.
    stop()
        Stop the video.
    on_size()
        Update gadget after a resize.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root()
        Yield all descendents of the root gadget (preorder traversal).
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    on_key(key_event)
        Handle key press event.
    on_mouse(mouse_event)
        Handle mouse event.
    on_paste(paste_event)
        Handle paste event.
    tween(...)
        Sequentially update gadget properties over time.
    on_add()
        Apply size hints and call children's `on_add`.
    on_remove()
        Call children's `on_remove`.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        source: Path | str | int,
        fg_color: Color = WHITE,
        bg_color: Color = BLACK,
        loop: bool = True,
        gray_threshold: int = 127,
        enable_shading: bool = False,
        invert_colors: bool = False,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._video = Text()
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._current_frame = None
        self._resource = None
        self._video_task = None
        self.add_gadget(self._video)
        self.source = source
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.loop = loop
        self.gray_threshold = gray_threshold
        self.enable_shading = enable_shading
        self.invert_colors = invert_colors
        self.alpha = alpha

    @property
    def is_transparent(self) -> bool:
        """Whether gadget is transparent."""
        return self._video.is_transparent

    @is_transparent.setter
    def is_transparent(self, is_transparent: bool):
        self._video.is_transparent = is_transparent

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._video.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._video.alpha = alpha

    @property
    def bg_color(self) -> Color:
        """Background color of video."""
        return self._video.default_bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._video.default_bg_color = bg_color
        self._video.canvas["bg_color"] = bg_color

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
            self._video.clear()

    def _paint_frame(self):
        h, w = self.size
        if self._current_frame is None or h == 0 or w == 0:
            return

        canvas = self._video.canvas
        upscaled = cv2.resize(self._current_frame, (2 * w, 4 * h)) > self.gray_threshold
        sectioned = np.swapaxes(upscaled.reshape(h, 4, w, 2), 1, 2)
        canvas["char"] = binary_to_braille(sectioned)

        if self.enable_shading:
            normals = cv2.resize(self._current_frame, (w, h)) / 255
            shades = lerp(self.bg_color, self.fg_color, normals[..., None])
            canvas["fg_color"] = shades.astype(np.uint8)
        else:
            canvas["fg_color"] = self.fg_color

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

            try:
                await asyncio.sleep(seconds_ahead)
            except asyncio.CancelledError:
                return

            _, frame = self._resource.retrieve()
            self._current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.invert_colors:
                self._current_frame = 255 - self._current_frame

            self._paint_frame()

        if self.loop:
            self.seek(0)
            self.play()
        else:
            self._current_frame = None
            self._video.clear()

    def on_size(self):
        """Resize canvas and colors arrays."""
        self._video.size = self.size
        self._paint_frame()

    def on_remove(self):
        """Pause video and release resource."""
        super().on_remove()
        self.pause()
        self._release_resource()

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
        self._video.clear()
