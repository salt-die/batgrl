from ..colors import (
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
from .graphic_widget import GraphicWidget
from .text_widget import TextWidget

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

        for i, (left, right) in enumerate(zip(left_side, right_side)):
            self.texture[i] = gradient(left, right, w)

        self.update_swatch_label(*self.last_valid_pos)

    def resize(self, size):
        super().resize(size)
        self.hue = self.hue

    def update_swatch_label(self, y, x):
        self.color_swatch.texture[:] = r, g, b, _ = self.texture[y, x]

        self.label.add_text(f"R: {r:>3}", column=1)
        self.label.add_text(f"G: {g:>3}", row=1, column=1)
        self.label.add_text(f"B: {b:>3}", row=2, column=1)
        self.label.add_text(hex(r * 2**16 + g * 2**8 + b)[2:], row=4, column=1)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        if not self.collides_point(mouse_event.position):
            return

        y, x = self.last_valid_pos = self.to_local(mouse_event.position)
        self.update_swatch_label(y, x)


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
        if not self.collides_point(mouse_event.position):
            return

        _, x = self.to_local(mouse_event.position)
        self.shade_selector.hue = AColor(*self.texture[0, x])


class ColorPicker(GraphicWidget):
    def __init__(self, size=(15, 21), **kwargs):
        super().__init__(size=size, **kwargs)

        self.color_swatch = GraphicWidget(pos=(1, 1), default_color=ARED)

        self.label = TextWidget(size=(5, 8))

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

    def resize(self, size):
        h, w = size

        super().resize(size)

        shades = self.shades
        swatch = self.color_swatch
        hues = self.hues
        label = self.label

        shades.size = max(10, h - 5), max(20, w - 11)

        swatch.size = max(6, h - 9), 8
        swatch.left = shades.right + 1

        hues.size = 2, shades.width
        hues.top = shades.bottom + 1

        label.top = swatch.bottom + 1
        label.left = shades.right + 1
