"""
A parallax widget.
"""
from collections.abc import Sequence

import numpy as np

from .graphic_widget import GraphicWidget


class Parallax(GraphicWidget):
    """
    A parallax widget.

    Parameters
    ----------
    layers : Sequence[GraphicWidget]
        Individual layers of the parallax in background-to-foreground order.
    speeds : Sequence[float] | None, default: None
        The scrolling speed of each layer. Default speeds are `1/(N - i)`
        where `N` is the number of layers and `i` is the index of a layer.
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
    offset : tuple[float, float]
        Vertical and horizontal offset of first layer of the parallax. Other layers will
        be adjusted automatically.
    vertical_offset : float
        Vertical offset of first layer of the parallax.
    horizontal_offset : float
        Horizontal offset of first layer of the parallax
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
    on_press:
        Handle key press event.
    on_click:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    """
    def __init__(self, *, layers: Sequence[GraphicWidget], speeds: Sequence[float] | None=None, **kwargs):
        super().__init__(**kwargs)

        self.layers = layers

        self._image_copies = [layer.texture.copy() for layer in layers]

        nlayers = len(layers)
        self.speeds = speeds or [1 / (nlayers - i) for i in range(nlayers)]

        self._vertical_offset = self._horizontal_offset = 0.0

        for widget in layers:
            self.add_widget(widget)

    def update_geometry(self):
        super().update_geometry()
        self._image_copies = [layer.texture.copy() for layer in self.layers]

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
        for speed, image, layer in zip(
            self.speeds,
            self._image_copies,
            self.layers,
        ):
            rolls = -round(speed * self._vertical_offset), -round(speed * self._horizontal_offset)
            axis = 0, 1
            layer.texture = np.roll(image, rolls, axis)
