"""
An animation widget.
"""
import asyncio
from collections.abc import Sequence
from pathlib import Path

from .graphic_widget_data_structures import Interpolation
from .image import Image
from .widget import Widget

__all__ = "Animation", "Interpolaton"


class Animation(Widget):
    """
    An animation widget.

    Parameters
    ----------
    path : Path
        Path to directory of images for frames in the animation (loaded
        in lexographical order of filenames).
    alpha : float, default: 1.0
        Transparency of the animation.
    interpolation : Interpolation, default: Interpolation.Linear
        Interpolation used when resizing the animation.
    frame_duration : float | int | Sequence[float| int], default: 1/12
        Time between updates of frames of the animation in seconds.
        Raises `ValueError` if a sequence is provided with length not
        equal to the number of frames.
    loop : bool, default: True
        If true, restart animation after last frame.
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
    path : Path
        Path to directory of images for frames in the animation (loaded
        in lexographical order of filenames).
    alpha : float
        Transparency of the animation.
    interpolation : Interpolation
        Interpolation used when resizing the animation.
    frame_duration : Sequence[float| int]
        Time between updates of frames of the animation in seconds.
    loop : bool
        If true, restart animation after last frame.
    current_frame : Image
        Current frame of the animation.
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
        Play the animation.
    pause:
        Pause the animation
    stop:
        Stop the animation.
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
    on_press:
        Handle key press event.
    on_click:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    """
    def __init__(
        self,
        *,
        path: Path,
        alpha: float=1.0,
        interpolation: Interpolation=Interpolation.LINEAR,
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        paths = sorted(path.iterdir(), key=lambda file: file.name)

        self.frames: list[Image] = [Image(size=self.size, path=path) for path in paths]
        if not self.frames:
            raise ValueError(f"{path} empty")

        if isinstance(frame_durations, (int, float)):
            self.frame_durations = [frame_durations] * len(paths)
        else:
            self.frame_durations = frame_durations
            if len(frame_durations) != len(paths):
                raise ValueError("")

        self.loop = loop

        self.alpha = alpha
        self.interpolation = interpolation

        self._i = 0
        self._animation = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def on_size(self):
        for frame in self.frames:
            frame.size = self.size

    @property
    def current_frame(self) -> Image:
        """
        Current frame of animation.
        """
        return self.frames[self._i]

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = alpha

        for frame in self.frames:
            frame.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        self._interpolation = interpolation

        for frame in self.frames:
            frame.interpolation = interpolation

    async def _play_animation(self):
        while True:
            try:
                await asyncio.sleep(self.frame_durations[self._i])
            except asyncio.CancelledError:
                break

            self._i += 1
            if self._i >= len(self.frames):
                if not self.loop:
                    return

                self._i = 0

    def play(self):
        """
        Play animation.
        """
        self.pause()
        self._animation = asyncio.create_task(self._play_animation())

    def pause(self):
        """
        Pause animation.
        """
        self._animation.cancel()

    def stop(self):
        """
        Stop animation.
        """
        self.pause()
        self._i = 0

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self.current_frame.render(canvas_view, colors_view, source)
        super().render(canvas_view, colors_view, source)
