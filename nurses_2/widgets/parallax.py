"""
A parallax widget.
"""
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np

from ..clamp import clamp
from .graphic_widget_data_structures import Interpolation, read_texture
from .image import Image
from .widget import Widget, emitter

__all__ = "Interpolation", "Parallax"

def _check_layer_speeds(layers, speeds):
    """
    Raise `ValueError` if `layers` and `speeds` are incompatible,
    else return a sequence of layer speeds.
    """
    nlayers = len(layers)
    if speeds is None:
        return [1 / (nlayers - i) for i in range(nlayers)]

    if len(speeds) != nlayers:
        raise ValueError("number of layers doesn't match number of layer speeds")

    return speeds


class Parallax(Widget):
    """
    A parallax widget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for layers of the parallax (loaded
        in lexographical order of filenames) layered from background to foreground.
    speeds : Sequence[float] | None, default: None
        The scrolling speed of each layer. Default speeds are `1/(N - i)`
        where `N` is the number of layers and `i` is the index of a layer.
    alpha : float, default: 1.0
        Transparency of the parallax.
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
    offset : tuple[float, float]
        Vertical and horizontal offset of first layer of the parallax. Other layers will
        be adjusted automatically.
    vertical_offset : float
        Vertical offset of first layer of the parallax.
    horizontal_offset : float
        Horizontal offset of first layer of the parallax
    alpha : float
        Transparency of the parallax.
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
    from_textures:
        Create a :class:`Parallax` from an iterable of uint8 rgba ndarray.
    from_images:
        Create a :class:`Parallax` from an iterable of :class:`Image`.
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
        speeds: Sequence[float] | None=None,
        alpha: float=1.0,
        interpolation: Interpolation=Interpolation.LINEAR,
        **kwargs
    ):
        super().__init__(**kwargs)

        if path is None:
            self.layers = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.layers = [Image(path=path, size=self.size) for path in paths]

        self.speeds = _check_layer_speeds(self.layers, speeds)
        self.alpha = alpha
        self.interpolation = interpolation

        self._vertical_offset = self._horizontal_offset = 0.0

    def on_size(self):
        for layer in self.layers:
            layer.size = self._size
        self._otextures = [layer.texture for layer in self.layers]

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    @emitter
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)
        for layer in self.layers:
            layer.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        self._interpolation = Interpolation(interpolation)
        for layer in self.layers:
            layer.interpolation = interpolation

    @property
    def vertical_offset(self) -> float:
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset: float):
        self._vertical_offset = offset
        self._adjust()

    @property
    def horizontal_offset(self) -> float:
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset: float):
        self._horizontal_offset = offset
        self._adjust()

    @property
    def offset(self) -> tuple[float, float]:
        return self._vertical_offset, self._horizontal_offset

    @offset.setter
    def offset(self, offset: tuple[float, float]):
        self._vertical_offset, self._horizontal_offset = offset
        self._adjust()

    def _adjust(self):
        for speed, texture, layer in zip(
            self.speeds,
            self._otextures,
            self.layers,
        ):
            rolls = -round(speed * self._vertical_offset), -round(speed * self._horizontal_offset)
            layer.texture = np.roll(texture, rolls, axis=(0, 1))

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        if not self.is_transparent:
            if self.background_char is not None:
                canvas_view[:] = self.background_char

            if self.background_color_pair is not None:
                colors_view[:] = self.background_color_pair

        for layer in self.layers:
            layer.render(canvas_view, colors_view, source)

        self.render_children(source, canvas_view, colors_view)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[np.ndarray],
        *,
        speeds: Sequence[float] | None=None,
        **kwargs
    ) -> "Parallax":
        """
        Create an :class:`Parallax` from an iterable of uint8 rgba ndarray.
        """
        parallax = cls(**kwargs)
        parallax.layers = [
            Image.from_texture(
                texture,
                size=parallax.size,
                alpha=parallax.alpha,
                interpolation=parallax.interpolation
            )
            for texture in textures
        ]
        parallax.speeds = _check_layer_speeds(parallax.layers, speeds)
        return parallax

    @classmethod
    def from_images(
        cls,
        images: Iterable[Image],
        *,
        speeds: Sequence[float] | None=None,
        **kwargs
    ) -> "Parallax":
        """
        Create an :class:`Parallax` from an iterable of :class:`Image`.
        """
        parallax = cls(**kwargs)
        parallax.layers = list(images)
        for image in parallax.layers:
            image.interpolation = parallax.interpolation
            image.size = parallax.size
            image.alpha = parallax.alpha
        parallax.speeds = _check_layer_speeds(parallax.layers, speeds)
        return parallax
