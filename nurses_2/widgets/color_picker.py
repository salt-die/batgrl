from typing import Callable

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
)
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.themable import Themable
from .button import Button
from .graphic_widget import GraphicWidget, Anchor
from .text_widget import TextWidget
from .widget import Widget

GRAD = ARED, AYELLOW, AGREEN, ACYAN, ABLUE, AMAGENTA, ARED
GRAD = tuple(zip(GRAD, GRAD[1:]))


class ShadeSelector(GrabbableBehavior, GraphicWidget):
    def __init__(self, color_swatch, label, **kwargs):
        super().__init__(**kwargs)
        self.last_valid_pos = 0, -1
        self.color_swatch = color_swatch
        self.label = label
        self.hue = ARED

    @property
    def hue(self):
        return self._hue

    @hue.setter
    def hue(self, hue):
        self._hue = hue

        h, w = self.size
        left_side = gradient(AWHITE, ABLACK, 2 * h)
        right_side = gradient(hue, ABLACK, 2 * h)

        for row, left, right in zip(self.texture, left_side, right_side):
            row[:] = gradient(left, right, w)

        self.update_swatch_label()

    def update_swatch_label(self):
        y, x = self.last_valid_pos

        h, w, _ = self.texture.shape
        if y * 2 >= h or x >= w:
            return

        r, g, b, _ = self.texture[y * 2, x]
        self.color_swatch.background_color_pair = ColorPair(r, g, b, r, g, b)

        self.label.add_text(hex(r * 2**16 + g * 2**8 + b)[2:], row=1, column=1)
        self.label.add_text(f"R: {r:>3}", row=3, column=1)
        self.label.add_text(f"G: {g:>3}", row=4, column=1)
        self.label.add_text(f"B: {b:>3}", row=5, column=1)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.position):
            self.last_valid_pos = self.to_local(mouse_event.position)
            self.update_swatch_label()


class HueSelector(GrabbableBehavior, GraphicWidget):
    def __init__(self, shade_selector, **kwargs):
        super().__init__(**kwargs)
        self.shade_selector = shade_selector

    def resize(self, size):
        super().resize(size)

        d, r = divmod(self.width, 6)

        rainbow = []
        for i, (a, b) in enumerate(GRAD):
            rainbow.extend(gradient(a, b, d + (i < r)))

        self.texture[:] = rainbow

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if self.collides_point(mouse_event.position):
            _, x = self.to_local(mouse_event.position)
            self.shade_selector.hue = AColor(*self.texture[0, x])


class ColorPicker(Themable, Widget):
    """
    Color picker widget.

    Parameters
    ----------
    ok_callback : Callable[[Color], None], default: lambda color: None
        Called with currently selected color when "OK" button is released.
    """
    def __init__(self, ok_callback: Callable[[Color], None]=lambda color: None, **kwargs):
        super().__init__(**kwargs)

        self.color_swatch = Widget(pos=(1, 1), background_char=" ", background_color_pair=ARED)

        self.label = TextWidget(size=(9, 8))
        self.label.add_widget(
            Button(
                label="OK",
                size=(1, 6),
                pos=(7, 1),
                callback=lambda: ok_callback(self.color_swatch.background_color_pair.bg_color),
            )
        )

        self.shades = ShadeSelector(
            pos=(1, 1),
            color_swatch=self.color_swatch,
            label=self.label,
            disable_ptf=True,
        )

        self.hues = HueSelector(
            pos=(1, 1),
            shade_selector=self.shades,
            disable_ptf=True,
        )

        self.add_widgets(self.color_swatch, self.hues, self.shades, self.label)

        self.update_theme()

    def resize(self, size):
        h, w = size

        super().resize(size)

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
