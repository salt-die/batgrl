"""
A color picker gadget.
"""
from collections.abc import Callable

import numpy as np

from ..colors import (
    ABLACK,
    ABLUE,
    ACYAN,
    AGREEN,
    AMAGENTA,
    ARED,
    AWHITE,
    AYELLOW,
    RED,
    WHITE,
    AColor,
    Color,
    ColorPair,
    gradient,
)
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .button import Button
from .gadget import Gadget, Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict
from .graphics import Graphics
from .text import Text

__all__ = [
    "ColorPicker",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

GRAD = ARED, AYELLOW, AGREEN, ACYAN, ABLUE, AMAGENTA, ARED
GRAD = tuple(zip(GRAD, GRAD[1:]))
WHITE_ON_RED = ColorPair.from_colors(WHITE, RED)


class _ShadeSelector(Grabbable, Graphics):
    def __init__(self, color_swatch, label, **kwargs):
        super().__init__(**kwargs)

        self._shade_indicator = Text(size=(1, 1), default_color_pair=WHITE_ON_RED)
        self._shade_indicator.add_str("○")
        self._shade_hint = 0.0, 1.0
        self.add_gadget(self._shade_indicator)

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

        self.label.add_str(hex(r * 2**16 + g * 2**8 + b)[2:], (1, 1))
        self.label.add_str(f"R: {r:>3}", (3, 1))
        self.label.add_str(f"G: {g:>3}", (4, 1))
        self.label.add_str(f"B: {b:>3}", (5, 1))

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


class _HueSelector(Grabbable, Graphics):
    def __init__(self, shade_selector, **kwargs):
        super().__init__(**kwargs)
        self.shade_selector = shade_selector

        self._hue_hint = 0.0
        self._hue_indicator = Text(size=(1, 1), default_color_pair=WHITE_ON_RED)
        self._hue_indicator.add_str("▼")

        self.add_gadget(self._hue_indicator)

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


class ColorPicker(Themable, Gadget):
    """
    A color picker gadget.

    Parameters
    ----------
    ok_callback : Callable[[Color], None], default: lambda color: None
        Called with currently selected color when "OK" button is released.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    update_theme:
        Paint the gadget with current theme.
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        background_char=" ",
        ok_callback: Callable[[Color], None] = lambda color: None,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            background_char=background_char,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_color_pair=background_color_pair,
        )

        self.color_swatch = Gadget(
            pos=(1, 1),
            background_char=" ",
            background_color_pair=WHITE_ON_RED,
        )

        self.label = Text(size=(9, 8))
        self.label.add_gadget(
            Button(
                label="OK",
                size=(1, 6),
                pos=(7, 1),
                callback=lambda: ok_callback(
                    self.color_swatch.background_color_pair.bg_color
                ),
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

        self.add_gadgets(self.color_swatch, self.hues, self.shades, self.label)

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
        primary = self.color_theme.primary

        self.background_color_pair = primary
        self.label.default_color_pair = primary
        self.label.colors[:] = primary
