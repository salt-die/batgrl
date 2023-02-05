import asyncio
import atexit
import time
import warnings
from pathlib import Path
from platform import uname

import cv2
import numpy as np

from ._binary_to_braille import binary_to_braille
from .text_widget import TextWidget, style_char

__all__ = "BrailleVideo",

_IS_WSL: bool = uname().system == "Linux" and uname().release.endswith("Microsoft")


class BrailleVideoPlayer(TextWidget):
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
        If true, foreground will be set to `default_fg_color` multiplied by the normalized grays from the source.
    invert_colors : bool, default: False
        Invert the colors in the source before rendering.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of widget.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    source : Path | str | int
        A path, URL, or capturing device (by index) of the video.
    loop : bool, default: True
        If true, video will restart after last frame.
    gray_threshold : int, default: 127
        Pixel values over this threshold in the source video will be rendered.
    enable_shading : bool, default: False
        If true, foreground will be set to `default_fg_color` multiplied by the normalized grays from the source.
    invert_colors : bool, default: False
        If true, colors in the source are inverted before video is rendered.
    is_device : bool
        If true, video is from a video capturing device.
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str, default: " "
        Default background character.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color pair of widget.
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
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
    add_border:
        Add a border to the widget.
    normalize_canvas:
        Ensure column width of text in the canvas is equal to widget width.
    add_str:
        Add a single line of text to the canvas.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
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
        Yield all descendents (or ancestors if `reverse` is True).
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
        loop: bool=True,
        gray_threshold: int=127,
        enable_shading: bool=False,
        invert_colors: bool=False,
        **kwargs
    ):
        super().__init__(**kwargs)
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
            # Problem: WSL doesn't support most USB devices (yet?), and trying to open one
            # with cv2 will pollute the terminal with cv2 errors (which can't be redirected
            # without duping file descriptors -- though this may be done sometime in the future).
            # Solution: Prevent the error.
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
                self.colors[..., :3] = (grays_normalized[..., None] * self.default_fg_color).astype(np.uint8)

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

            h, w = self.size

            if self.enable_shading:
                grays_normalized = cv2.resize(self._current_frame, (w, h)) / 255
                self.colors[..., :3] = (grays_normalized[..., None] * self.default_fg_color).astype(np.uint8)

            upscaled = cv2.resize(self._current_frame, (2 * w, 4 * h)) > self.gray_threshold
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
