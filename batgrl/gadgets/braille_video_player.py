"""
A video player that renders to braille unicode characters in grayscale.
"""
import asyncio
import atexit
import time
import warnings
from pathlib import Path
from platform import uname

import cv2
import numpy as np

from ..colors import WHITE_ON_BLACK, ColorPair
from .text import (
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    Text,
    style_char,
)
from .text_tools import binary_to_braille

__all__ = [
    "BrailleVideoPlayer",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

_IS_WSL: bool = uname().system == "Linux" and uname().release.endswith("Microsoft")


class BrailleVideoPlayer(Text):
    """
    A video player that renders to braille unicode characters in grayscale.

    Parameters
    ----------
    source : pathlib.Path | str | int
        A path to video, URL to video stream, or video capturing device (by index).
        Trying to open a video capturing device on WSL will issue a warning.
    loop : bool, default: True
        If true, restart video after last frame.
    gray_threshold : int, default: 127
        Pixel values over this threshold in the source video will be rendered.
    enable_shading : bool, default: False
        If true, foreground will be set to `default_fg_color` multiplied by the
        normalized grays from the source.
    invert_colors : bool, default: False
        Invert the colors in the source before rendering.
    default_char : str, default: " "
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
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    source : Path | str | int
        A path, URL, or capturing device (by index) of the video.
    loop : bool
        If true, video will restart after last frame.
    gray_threshold : int
        Pixel values over this threshold in the source video will be rendered.
    enable_shading : bool
        If true, foreground will be set to `default_fg_color` multiplied by the
        normalized grays from the source.
    invert_colors : bool
        If true, colors in the source are inverted before video is rendered.
    is_device : bool
        If true, video is from a video capturing device.
    canvas : NDArray[Char]
        The array of characters for the gadget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str
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
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
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
    play:
        Play the video. Returns a task.
    pause:
        Pause the video.
    seek:
        Seek to certain time (in seconds) in the video.
    stop:
        Stop the video.
    add_border:
        Add a border to the gadget.
    add_str:
        Add a single line of text to the canvas.
    set_text:
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        source: Path | str | int,
        loop: bool = True,
        gray_threshold: int = 127,
        enable_shading: bool = False,
        invert_colors: bool = False,
        default_char: str = " ",
        default_color_pair: ColorPair = WHITE_ON_BLACK,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )
        self._current_frame = None
        self._resource = None
        self._video_task = None
        self.source = source
        self.loop = loop
        self.gray_threshold = gray_threshold
        self.enable_shading = enable_shading
        self.invert_colors = invert_colors

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
            self.canvas["char"][:] = self.default_char

    def on_size(self):
        h, w = self.size
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)
        self.canvas = np.full((h, w), style_char(self.default_char))

        if self._current_frame is not None:
            upscaled = cv2.resize(self._current_frame, (2 * w, 4 * h)) > 0
            sectioned = np.swapaxes(upscaled.reshape(h, 4, w, 2), 1, 2)
            self.canvas["char"] = binary_to_braille(sectioned)

            if self.enable_shading:
                grays_normalized = cv2.resize(self._current_frame, (w, h)) / 255
                self.colors[..., :3] = (
                    grays_normalized[..., None] * self.default_fg_color
                ).astype(np.uint8)

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
            self._current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.invert_colors:
                self._current_frame = 255 - self._current_frame

            h, w = self.size

            if self.enable_shading:
                grays_normalized = cv2.resize(self._current_frame, (w, h)) / 255
                self.colors[..., :3] = (
                    grays_normalized[..., None] * self.default_fg_color
                ).astype(np.uint8)

            upscaled = (
                cv2.resize(self._current_frame, (2 * w, 4 * h)) > self.gray_threshold
            )
            sectioned = np.swapaxes(upscaled.reshape(h, 4, w, 2), 1, 2)
            self.canvas["char"][:] = binary_to_braille(sectioned)

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
        self.canvas["char"][:] = self.default_char