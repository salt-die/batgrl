"""
An animation widget.
"""
import asyncio
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np

from ..clamp import clamp
from .graphic_widget_data_structures import Interpolation
from .image import Image
from .widget import Widget, emitter

__all__ = "Animation", "Interpolaton"

def _check_frame_durations(frames, frame_durations):
    """
    Raise `ValueError` if `frames` and `frame_durations` are incompatible,
    else return a sequence of frame durations.
    """
    if isinstance(frame_durations, (int, float)):
        return [frame_durations] * len(frames)

    if len(frame_durations) != len(frames):
        raise ValueError("number of frames doesn't match number of frame durations")

    return frame_durations


class Animation(Widget):
    """
    An animation widget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for frames in the animation (loaded
        in lexographical order of filenames).
    frame_durations : float | int | Sequence[float| int], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    loop : bool, default: True
        If true, restart animation after last frame.
    reverse : bool, default: False
        If true, play animation in reverse.
    alpha : float, default: 1.0
        Transparency of the animation.
    interpolation : Interpolation, default: Interpolation.Linear
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
    loop : bool
        If true, animation is restarted after last frame.
    reverse : bool
        If true, animation is played in reverse.
    alpha : float
        Transparency of the animation.
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
        Play the animation. Returns a task.
    pause:
        Pause the animation
    stop:
        Stop the animation and reset current frame.
    from_textures:
        Create an :class:`Animation` from an iterable of uint8 rgba ndarray.
    from_images:
        Create an :class:`Animation` from an iterable of :class:`Image`.
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
        path: Path | None=None,
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        reverse: bool=False,
        alpha: float=1.0,
        interpolation: Interpolation=Interpolation.LINEAR,
        **kwargs
    ):
        super().__init__(**kwargs)

        if path is None:
            self.frames = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.frames = [Image(path=path, size=self.size) for path in paths]

        self.frame_durations = _check_frame_durations(self.frames, frame_durations)
        self.alpha = alpha
        self.interpolation = interpolation
        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    def on_remove(self):
        self.pause()
        super().on_remove()

    def on_size(self):
        for frame in self.frames:
            frame.size = self._size

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    @emitter
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)
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
                if self._i == len(self.frames):
                    self._i = 0

                    if not self.loop:
                        return

    def play(self) -> asyncio.Task:
        """
        Play animation.
        """
        self.pause()

        if self._i == 0 and self.reverse:
            self._i = len(self.frames) - 1
        elif self._i == len(self.frames) - 1 and not self.reverse:
            self._i = 0

        self._animation_task = asyncio.create_task(self._play_animation())
        return self._animation_task

    def pause(self):
        """
        Pause animation.
        """
        if self._animation_task is not None:
            self._animation_task.cancel()

    def stop(self):
        """
        Stop the animation and reset current frame.
        """
        self.pause()
        self._i = len(self.frames) - 1 if self.reverse else 0

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        if not self.is_transparent:
            if self.background_char is not None:
                canvas_view[:] = self.background_char

            if self.background_color_pair is not None:
                colors_view[:] = self.background_color_pair

        if self.frames:
            self.frames[self._i].render(canvas_view, colors_view, source)

        self.render_children(source, canvas_view, colors_view)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[np.ndarray],
        *,
        frame_durations: float | int | Sequence[float| int]=1/12,
        **kwargs
    ) -> "Animation":
        """
        Create an :class:`Animation` from an iterable of uint8 rgba ndarray.
        """
        animation = cls(**kwargs)
        animation.frames = [
            Image.from_texture(
                texture,
                size=animation.size,
                alpha=animation.alpha,
                interpolation=animation.interpolation
            )
            for texture in textures
        ]
        animation.frame_durations = _check_frame_durations(animation.frames, frame_durations)
        return animation

    @classmethod
    def from_images(
        cls,
        images: Iterable[Image],
        *,
        frame_durations: float | int | Sequence[float| int]=1/12,
        **kwargs
    ) -> "Animation":
        """
        Create an :class:`Animation` from an iterable of :class:`Image`.
        """
        animation = cls(**kwargs)
        animation.frames = list(images)
        for image in animation.frames:
            image.interpolation = animation.interpolation
            image.size = animation.size
            image.alpha = animation.alpha
        animation.frame_durations = _check_frame_durations(animation.frames, frame_durations)
        return animation
