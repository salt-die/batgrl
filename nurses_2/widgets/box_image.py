"""
An image painted with box unicode characters.
"""
from pathlib import Path

import cv2
import numpy as np

from ..colors import WHITE_ON_BLACK, ColorPair
from .text_tools import binary_to_box
from .text_widget import (
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    TextWidget,
    style_char,
)

__all__ = [
    "BoxImage",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class BoxImage(TextWidget):
    """
    An image painted with box unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width
        grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of widget.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    path : pathlib.Path
        Path to image.
    canvas : NDArray[Char]
        The array of characters for the widget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str
        Default background character.
    default_color_pair : ColorPair
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
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
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
    add_str:
        Add a single line of text to the canvas.
    set_text:
        Resize widget to fit text, erase canvas, then fill canvas with text.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
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
        path: Path,
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

        self.canvas = np.full((h, w), style_char(self.default_char))
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self._load_texture()

    def _load_texture(self):
        h, w = self.size

        img = cv2.imread(str(self.path.absolute()), cv2.IMREAD_COLOR)
        img_bgr = cv2.resize(img, (2 * w, 2 * h))

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 2, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 2, w, 2, 3), 1, 2)

        # First, find the average lightness of each 2x2 section of the image
        # (`average_lightness`). Boxes are placed where the lightness is greater than
        # `average_lightness`. The background color will be the average of the colors
        # darker than `average_lightness`. The foreground color will be the average of
        # the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_boxes = lightness > average_lightness[..., None, None]

        self.canvas["char"] = binary_to_box(where_boxes)

        nboxes = where_boxes.sum(axis=(2, 3))
        nboxes_neg = 4 - nboxes

        background = rgb_sectioned.copy()
        background[where_boxes] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            bg = (
                background.sum(axis=(2, 3)) / nboxes_neg[..., None]
            )  # average of colors darker than `average_lightness`

        foreground = rgb_sectioned.copy()
        foreground[~where_boxes] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            fg = (
                foreground.sum(axis=(2, 3)) / nboxes[..., None]
            )  # average of colors lighter than `average_lightness`

        self.colors[..., :3] = np.where(np.isin(fg, (np.nan, np.inf)), bg, fg)
        self.colors[..., 3:] = np.where(np.isin(bg, (np.nan, np.inf)), fg, bg)
