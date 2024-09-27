"""A color picker gadget."""

from collections.abc import Callable
from itertools import pairwise

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
    gradient,
)
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .button import Button
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .graphics import Graphics
from .pane import Pane
from .text import Text, new_cell

__all__ = ["ColorPicker", "Point", "Size"]

GRAD = tuple(pairwise([ARED, AYELLOW, AGREEN, ACYAN, ABLUE, AMAGENTA, ARED]))


class _ShadeSelector(Grabbable, Graphics):
    def __init__(self, color_swatch, label, **kwargs):
        super().__init__(**kwargs)

        self._shade_indicator = Text(size=(1, 1), is_transparent=True, default_cell="○")
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
        if w == 0:
            return
        left_side = gradient(AWHITE, ABLACK, 2 * h)
        right_side = gradient(hue, ABLACK, 2 * h)

        for row, left, right in zip(self.texture, left_side, right_side):
            row[:] = gradient(left, right, w)

        self.update_swatch_label()

    def update_swatch_label(self):
        y, x = self._shade_indicator.pos

        r, g, b = self.texture[y * 2, x, :3].tolist()

        self.color_swatch.bg_color = r, g, b

        self.label.add_str(hex(r * 2**16 + g * 2**8 + b)[2:], pos=(1, 1))
        self.label.add_str(f"R: {r:>3}", pos=(3, 1))
        self.label.add_str(f"G: {g:>3}", pos=(4, 1))
        self.label.add_str(f"B: {b:>3}", pos=(5, 1))

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.pos):
            y, x = self._shade_indicator.pos = self.to_local(mouse_event.pos)
            h, w = self.size
            self._shade_hint = (
                0 if h <= 1 else y / (h - 1),
                0 if w <= 1 else x / (w - 1),
            )
            self.update_swatch_label()


class _HueSelector(Grabbable, Graphics):
    def __init__(self, shade_selector, **kwargs):
        super().__init__(**kwargs)
        self.shade_selector = shade_selector

        self._hue_hint = 0.0
        self._hue_indicator = Text(
            size=(1, 1), default_cell=new_cell(fg_color=WHITE, bg_color=RED)
        )
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
        self._hue_indicator.canvas["bg_color"] = self.texture[0, x, :3]
        self.shade_selector.update_hue(AColor(*self.texture[0, x]))

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.pos):
            x = self._hue_indicator.x = self.to_local(mouse_event.pos).x
            self._hue_hint = 0 if self.width <= 1 else x / (self.width - 1)
            self.update_hue()


class ColorPicker(Themable, Gadget):
    r"""
    A color picker gadget.

    Parameters
    ----------
    ok_callback : Callable[[Color], None], default: lambda color: None
        Called with currently selected color when "OK" button is released.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    alpha : float
        Transparency of gadget.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    update_theme()
        Paint the gadget with current theme.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        ok_callback: Callable[[Color], None] = lambda color: None,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.color_swatch = Pane(pos=(1, 1), bg_color=RED, is_transparent=False)
        self.label = Text(size=(9, 8), alpha=0, is_transparent=True)
        self.shades = _ShadeSelector(
            pos=(1, 1),
            color_swatch=self.color_swatch,
            label=self.label,
            is_transparent=False,
        )
        self.hues = _HueSelector(
            pos=(1, 1), shade_selector=self.shades, is_transparent=False
        )
        ok_button = Button(
            label="OK",
            size=(1, 6),
            pos=(7, 1),
            callback=lambda: ok_callback(self.color_swatch.bg_color),
        )
        self._container = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_transparent=is_transparent,
        )
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.alpha = alpha
        self.label.add_gadget(ok_button)
        self._container.add_gadgets(
            self.color_swatch, self.hues, self.shades, self.label
        )
        self.add_gadget(self._container)

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._container.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._container.alpha = alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._container.is_transparent = self.is_transparent

    def on_size(self):
        """Resize and reposition children."""
        h, w = self._size

        self.shades.size = max(10, h - 4), max(20, w - 11)

        self.color_swatch.size = max(2, h - 12), 8
        self.color_swatch.left = self.shades.right + 1

        self.hues.size = 1, self.shades.width
        self.hues.top = self.shades.bottom + 1

        self.label.top = self.color_swatch.bottom + 1
        self.label.left = self.shades.right + 1

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary = self.color_theme.primary
        self._container.bg_color = primary.bg
        self.label.default_fg_color = self.label.canvas["fg_color"] = primary.fg
        self.label.default_bg_color = self.label.canvas["bg_color"] = primary.bg
