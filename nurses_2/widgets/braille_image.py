"""
An image painted with braille unicode characters.
"""
from pathlib import Path

import cv2
import numpy as np

from ._binary_to_braille import binary_to_braille
from .text_widget import TextWidget


class BrailleImage(TextWidget):
    """
    An image painted with braille unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
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
    path : pathlib.Path
        Path to image.
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str, default: " "
        Default background character.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color pair of widget.
    default_fg_color: Color
        The default foreground color.
    default_bg_color: Color
        The default background color.
    get_view: CanvasView
        Return a :class:`nurses_2.widgets.text_widget_data_structures.CanvasView`
        of the underlying :attr:`canvas`.
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
    add_border:
        Add a border to the widget.
    normalize_canvas:
        Add zero-width characters after each full-width character.
    add_text:
        Add text to the canvas.
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
    def __init__(self, *, path: Path, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self._load_texture()

    def on_size(self):
        h, w = self._size

        self.canvas = np.full((h, w), self.default_char, dtype=object)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self._load_texture()

    def _load_texture(self):
        h, w = self.size

        img = cv2.imread(str(self.path.absolute()), cv2.IMREAD_COLOR)
        img_bgr = cv2.resize(img, (2 * w, 4 * h))

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 4, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 4, w, 2, 3), 1, 2)

        # First, find the average lightness of each 4x2 section of the image (`average_lightness`).
        # Braille dots are placed where the lightness is greater than `average_lightness`.
        # The background color will be the average of the colors darker than `average_lightness`.
        # The foreground color will be the average of the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_dots = lightness > average_lightness[..., None, None]

        self.canvas = binary_to_braille(where_dots)

        ndots = where_dots.sum(axis=(2, 3))
        ndots_neg = 8 - ndots

        background = rgb_sectioned.copy()
        background[where_dots] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            bg = background.sum(axis=(2, 3)) / ndots_neg[..., None]  # average of colors darker than `average_lightness`

        foreground = rgb_sectioned.copy()
        foreground[~where_dots] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            fg = foreground.sum(axis=(2, 3)) / ndots[..., None]  # average of colors lighter than `average_lightness`

        self.colors[..., :3] = np.where(np.isin(fg, (np.nan, np.inf)), bg, fg)
        self.colors[..., 3:] = np.where(np.isin(bg, (np.nan, np.inf)), fg, bg)
