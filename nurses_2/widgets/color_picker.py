"""
A color picker widget.
"""
from collections.abc import Callable

import numpy as np

from ..colors import (
    Color,
    ColorPair,
    AColor,
    gradient,
    AWHITE,
    ABLACK,
    ARED,
    AYELLOW,
    AGREEN,
    ACYAN,
    ABLUE,
    AMAGENTA,
    RED,
    WHITE,
)
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.themable import Themable
from .button import Button
from .graphic_widget import GraphicWidget
from .text_widget import TextWidget
from .widget import Widget

__all__ = "ColorPicker",

GRAD = ARED, AYELLOW, AGREEN, ACYAN, ABLUE, AMAGENTA, ARED
GRAD = tuple(zip(GRAD, GRAD[1:]))
WHITE_ON_RED = ColorPair.from_colors(WHITE, RED)


class _ShadeSelector(GrabbableBehavior, GraphicWidget):
    def __init__(self, color_swatch, label, **kwargs):
        super().__init__(**kwargs)

        self._shade_indicator = TextWidget(size=(1, 1), default_color_pair=WHITE_ON_RED)
        self._shade_indicator.add_text("○")
        self._shade_hint = 0.0, 1.0
        self.add_widget(self._shade_indicator)

        self.color_swatch = color_swatch
        self.label = label
        self.update_hue(ARED)

    def on_size(self):
        h, w = self._size
        hh, wh = self._shade_hint

        self.texture = np.zeros((h * 2, w, 4), dtype=np.uint8)
        self._shade_indicator.pos = round((h - 1) * hh), round((w - 1) * wh)

        self.update_hue(self.hue)

    def update_hue(self, hue: AColor):
        self.hue = hue

        h, w = self._size
        left_side = gradient(AWHITE, ABLACK, 2 * h)
        right_side = gradient(hue, ABLACK, 2 * h)

        for row, left, right in zip(self.texture, left_side, right_side):
            row[:] = gradient(left, right, w)

        self.update_swatch_label()

    def update_swatch_label(self):
        y, x = self._shade_indicator.pos

        r, g, b, _ = self.texture[y * 2, x]
        shade = ColorPair(*WHITE, r, g, b)

        self.color_swatch.background_color_pair = shade

        self._shade_indicator.colors[:] = shade

        self.label.add_text(hex(r * 2**16 + g * 2**8 + b)[2:], row=1, column=1)
        self.label.add_text(f"R: {r:>3}", row=3, column=1)
        self.label.add_text(f"G: {g:>3}", row=4, column=1)
        self.label.add_text(f"B: {b:>3}", row=5, column=1)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.position):
            y, x = self._shade_indicator.pos = self.to_local(mouse_event.position)
            h, w = self.size
            self._shade_hint = (
                0 if h == 1 else y / (h - 1),
                0 if w == 1 else x / (w - 1),
            )
            self.update_swatch_label()


class _HueSelector(GrabbableBehavior, GraphicWidget):
    def __init__(self, shade_selector, **kwargs):
        super().__init__(**kwargs)
        self.shade_selector = shade_selector

        self._hue_hint = 0.0
        self._hue_indicator = TextWidget(size=(1, 1), default_color_pair=WHITE_ON_RED)
        self._hue_indicator.add_text("▼")

        self.add_widget(self._hue_indicator)

    def on_size(self):
        h, w = self._size

        self.texture = np.zeros((h * 2, w, 4), dtype=np.uint8)

        d, r = divmod(w, 6)

        rainbow = []
        for i, (a, b) in enumerate(GRAD):
            rainbow.extend(gradient(a, b, d + (i < r)))

        self.texture[:] = rainbow

        self._hue_indicator.x = round(self._hue_hint * w)
        self.update_hue()

    def update_hue(self):
        x = self._hue_indicator.x
        self._hue_indicator.colors[..., 3:] = self.texture[0, x, :3]
        self.shade_selector.update_hue(AColor(*self.texture[0, x]))

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.position):
            x = self._hue_indicator.x = self.to_local(mouse_event.position).x
            self._hue_hint = 0 if self.width == 1 else x / (self.width - 1)
            self.update_hue()


class ColorPicker(Themable, Widget):
    """
    A color picker widget.

    Parameters
    ----------
    ok_callback : Callable[[Color], None], default: lambda color: None
        Called with currently selected color when "OK" button is released.
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
    ok_callback : Callable[[Color], None]
        Called with currently selected color when "OK" button is released.
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
    update_theme:
        Repaint the widget with a new theme. This should be called at:
        least once when a widget is initialized.
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
        background_char=" ",
        ok_callback: Callable[[Color], None]=lambda color: None,
        **kwargs
    ):
        super().__init__(background_char=background_char, **kwargs)

        self.color_swatch = Widget(
            pos=(1, 1),
            background_char=" ",
            background_color_pair=WHITE_ON_RED,
        )

        self.label = TextWidget(size=(9, 8))
        self.label.add_widget(
            Button(
                label="OK",
                size=(1, 6),
                pos=(7, 1),
                callback=lambda: ok_callback(self.color_swatch.background_color_pair.bg_color),
            )
        )

        self.shades = _ShadeSelector(
            pos=(1, 1),
            color_swatch=self.color_swatch,
            label=self.label,
            disable_ptf=True,
        )

        self.hues = _HueSelector(
            pos=(1, 1),
            shade_selector=self.shades,
            disable_ptf=True,
        )

        self.add_widgets(self.color_swatch, self.hues, self.shades, self.label)

        self.update_theme()

    def on_size(self):
        h, w = self._size

        shades = self.shades
        swatch = self.color_swatch
        hues = self.hues
        label = self.label

        shades.size = max(10, h - 4), max(20, w - 11)

        swatch.size = max(2, h - 12), 8
        swatch.left = shades.right + 1

        hues.size = 1, shades.width
        hues.top = shades.bottom + 1

        label.top = swatch.bottom + 1
        label.left = shades.right + 1

    def update_theme(self):
        ct = self.color_theme

        self.background_color_pair = ct.primary_color_pair

        self.label.default_color_pair = ct.primary_dark_color_pair
        self.label.colors[:] = ct.primary_dark_color_pair
