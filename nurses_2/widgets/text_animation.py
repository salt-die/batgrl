"""
A text animation widget.
"""
import asyncio
from collections.abc import Iterable, Sequence

from .animation import _check_frame_durations
from .text_widget import TextWidget
from .widget import Widget, style_char, intersection
from .widget_data_structures import Rect


class TextAnimation(Widget):
    """
    A text animation widget.

    Parameters
    ----------
    frames : Iterable[str] | None, default: None
        Frames of the animation.
    frame_durations : float | int | Sequence[float| int], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    loop : bool, default: True
        If true, restart animation after last frame.
    reverse : bool, default: False
        If true, play animation in reverse.
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
        If true, background color and whitespace in text animation won't be painted.
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
    frames : list[TextWidget]
        Frames of the animation.
    frame_durations : list[int | float]
        Time each frame is displayed.
    loop : bool
        If true, animation is restarted after last frame.
    reverse : bool
        If true, animation is played in reverse.
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
        frames: Iterable[str] | None=None,
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        reverse: bool=False,
        **kwargs
    ):
        self.frames = []
        if frames is not None:
            for frame in frames:
                self.frames.append(TextWidget())
                self.frames[-1].set_text(frame)

        super().__init__(**kwargs)

        self.frame_durations = _check_frame_durations(self.frames, frame_durations)
        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def is_transparent(self) -> bool:
        """
        If true, background color and whitespace in text animation won't be painted.
        """
        return self._is_transparent

    @is_transparent.setter
    def is_transparent(self, transparent: bool):
        self._is_transparent = transparent
        for frame in self.frames:
            frame.is_transparent = transparent

    def on_remove(self):
        self.pause()
        super().on_remove()

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
        if self.frames:
            frame = self.frames[self._i]
            vert_slice, hori_slice = source
            dest_rect = Rect(vert_slice.start, vert_slice.stop, hori_slice.start, hori_slice.stop)
            source_rect = Rect(frame.top, frame.bottom, frame.left, frame.right)
            if (slices := intersection(dest_rect, source_rect)) is not None:
                dest_slice, source_slice = slices
                frame.render(canvas_view[dest_slice], colors_view[dest_slice], source_slice)

        self.render_children(source, canvas_view, colors_view)
