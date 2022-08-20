"""
A video player widget.
"""
import asyncio
import atexit
from pathlib import Path
import time

import cv2

from ..colors import ABLACK
from .graphic_widget import GraphicWidget, Interpolation

__all__ = "Interpolation", "VideoPlayer"


# Seeking is not yet implemented
class VideoPlayer(GraphicWidget):
    """
    A video player.

    Parameters
    ----------
    source : pathlib.Path | str | int
        A path to video, URL to video stream, or capturing device (by index).
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If widget is transparent, the alpha channel of the underlying texture will be multiplied by this
        value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: Interpolation.LINEAR
        Interpolation used when widget is resized.
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
    video : asyncio.Task
        The task updating the widget's texture.
    source : Path | str | int
        Source of video.
    texture : numpy.ndarray
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
        Play the video.
    pause:
        Pause the video.
    stop:
        Stop the video.
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
    on_size:
        Called when widget is resized.
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
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
        Yield all descendents.
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_keypress:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    """
    def __init__(
        self,
        *,
        source: Path | str | int,
        default_color=ABLACK,
        is_transparent=False,
        **kwargs
    ):
        super().__init__(
            default_color=default_color,
            is_transparent=is_transparent,
            **kwargs
        )

        self._resource = None
        self._video = asyncio.create_task(asyncio.sleep(0))  # dummy task

        self.source = source

    @property
    def video(self) -> asyncio.Task:
        return self._video

    @property
    def source(self) -> Path | str | int:
        return self._source

    @source.setter
    def source(self, new_source):
        self.stop()
        self._source = new_source

    def _load_video(self):
        source = self.source
        if isinstance(source, Path):
            source = str(source.absolute())

        self._resource = cv2.VideoCapture(source)
        atexit.register(self._resource.release)

    def close(self):
        if self._resource is not None:
            self._resource.release()

            # `cv2` may write warnings to stdout on Windows when releasing cameras.
            # We force a screen regeneration by resizing the root widget.
            self.root.size = self.root.size

            atexit.unregister(self._resource.release)
            self._resource = None
            self._current_frame = None
            self.texture[:] = self.default_color

    def on_size(self):
        super().on_size()

        # If video is paused, resize current frame.
        if self._video.done() and self._current_frame is not None:
            h, w, _ = self.texture.shape
            resized_frame = cv2.resize(self._current_frame, (w, h), interpolation=self.interpolation)
            self.texture[..., :3] = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

    async def _play_video(self):
        # Bring in to locals:
        resize = cv2.resize
        recolor = cv2.cvtColor
        MSEC = cv2.CAP_PROP_POS_MSEC
        BGR2RGB = cv2.COLOR_BGR2RGB
        monotonic = time.monotonic

        video_get = self._resource.get
        video_grab = self._resource.grab
        video_retrieve = self._resource.retrieve

        video_grab()
        start_time = monotonic() - video_get(MSEC) / 1000

        while True:
            if not video_grab():
                break

            seconds_ahead = video_get(MSEC) / 1000 + start_time - monotonic()
            if seconds_ahead < 0:
                continue

            ret_flag, self._current_frame = video_retrieve()
            if not ret_flag:
                break

            size = self.width, 2 * self.height
            resized_frame = resize(self._current_frame, size, interpolation=self.interpolation)
            self.texture[..., :3] = recolor(resized_frame, BGR2RGB)

            try:
                await asyncio.sleep(seconds_ahead)
            except asyncio.CancelledError:
                return

        self.close()

    def play(self):
        """
        Play video.
        """
        if self._resource is None:
            self._load_video()

        self._video.cancel()
        self._video = asyncio.create_task(self._play_video())

    def pause(self):
        """
        Pause video.
        """
        self._video.cancel()

    def stop(self):
        """
        Stop video.
        """
        self.pause()
        self.close()
