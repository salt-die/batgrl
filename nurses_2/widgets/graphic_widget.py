"""
Base for graphic widgets.
"""
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from ..colors import TRANSPARENT, AColor, ColorPair
from .texture_tools import Interpolation
from .widget import (
    Anchor,
    Char,
    Easing,
    Point,
    PosHint,
    PosHintDict,
    Rect,
    Size,
    SizeHint,
    SizeHintDict,
    Widget,
    clamp,
    intersection,
    lerp,
    style_char,
    subscribable,
)

__all__ = [
    "Anchor",
    "Char",
    "Easing",
    "GraphicWidget",
    "Interpolation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Rect",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "clamp",
    "intersection",
    "lerp",
    "style_char",
    "subscribable",
]


class GraphicWidget(Widget):
    """
    Base for graphic widgets.

    Graphic widgets are widgets that are rendered entirely with the upper half block
    character, "▀". Graphic widgets' color information is stored in a uint8 RGBA array,
    :attr:`texture`. Note that the height of :attr:`texture` is twice the height of the
    widget.

    Parameters
    ----------
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If widget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: "linear"
        Interpolation used when widget is resized.
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
    texture : NDArray[np.uint8]
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
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
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
        is_transparent: bool = True,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.default_color = default_color
        self.interpolation = interpolation
        self.alpha = alpha

        h, w = self.size
        self.texture = np.full(
            (2 * h, w, 4),
            default_color,
            dtype=np.uint8,
        )

    @property
    def alpha(self) -> float:
        """
        Transparency of widget if :attr:`is_transparent` is true.
        """
        return self._alpha

    @alpha.setter
    @subscribable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    def on_size(self):
        h, w = self._size

        self.texture = cv2.resize(
            self.texture,
            (w, 2 * h),
            interpolation=Interpolation._to_cv_enum[self.interpolation],
        )

    @property
    def interpolation(self) -> Interpolation:
        """
        Interpolation used when widget is resized.
        """
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        if interpolation not in Interpolation.__args__:
            raise TypeError(f"{interpolation} is not a valid interpolation type.")
        self._interpolation = interpolation

    def render(
        self,
        canvas_view: NDArray[Char],
        colors_view: NDArray[np.uint8],
        source: tuple[slice, slice],
    ):
        """
        Paint region given by `source` into `canvas_view` and `colors_view`.
        """
        vert_slice, hori_slice = source
        t = 2 * vert_slice.start
        b = 2 * vert_slice.stop

        texture = self.texture
        even_rows = texture[t:b:2, hori_slice]
        odd_rows = texture[t + 1 : b : 2, hori_slice]

        foreground = colors_view[..., :3]
        background = colors_view[..., 3:]

        if not self.is_transparent:
            foreground[:] = even_rows[..., :3]
            background[:] = odd_rows[..., :3]
        else:
            # If alpha compositing with a text widget, will look better to replace
            # foreground colors with background colors in most cases.
            mask = canvas_view != style_char("▀")
            foreground[mask] = background[mask]

            even_buffer = np.subtract(even_rows[..., :3], foreground, dtype=float)
            odd_buffer = np.subtract(odd_rows[..., :3], background, dtype=float)

            norm_alpha = self.alpha / 255

            even_buffer *= even_rows[..., 3, None]
            even_buffer *= norm_alpha

            odd_buffer *= odd_rows[..., 3, None]
            odd_buffer *= norm_alpha

            np.add(even_buffer, foreground, out=foreground, casting="unsafe")
            np.add(odd_buffer, background, out=background, casting="unsafe")

        canvas_view[:] = style_char("▀")
        self.render_children(source, canvas_view, colors_view)

    def to_png(self, path: Path):
        """
        Write :attr:`texture` to provided path as a `png` image.
        """
        BGRA = cv2.cvtColor(self.texture, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path.absolute()), BGRA)
