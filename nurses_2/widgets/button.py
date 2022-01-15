from typing import Callable

from ..colors import Color, ColorPair, BLACK
from ..easings import lerp
from .behaviors.button_behavior import ButtonBehavior
from .text_widget import TextWidget, Anchor, Size

PURPLE = Color.from_hex("462270")
YELLOW = Color.from_hex("dbd006")
YELLOW_ON_PURPLE = ColorPair.from_colors(YELLOW, PURPLE)

def _whiten_color_pair(color_pair, p):
    return ColorPair(*(int(lerp(c, 255, p)) for c in color_pair))


class Button(ButtonBehavior, TextWidget):
    """
    A button widget.

    Parameters
    ----------
    label : str, default: ""
        Button label.
    callback : Callable, default: lambda: None
        No-argument callable called when button is released.
    hover_color_pair : ColorPair | None, default: None
        Color pair of button on hover. If None, hover_color_pair
        will be default_color_pair, but whitened.
    down_color_pair : ColorPair | None, default: None
        Color pair of button when pressed. If none, down_color_pair
        will be default_color_pair, but whitened (and brighter than
        default hover_color_pair).
    background_color : Color, default: BLACK
        Color of background for the button.
    default_color_pair: ColorPair, default: YELLOW_ON_PURPLE
        Default color pair of button.
    """
    def __init__(
        self,
        *,
        label: str="",
        callback: Callable=lambda: None,
        hover_color_pair: ColorPair | None=None,
        down_color_pair: ColorPair | None=None,
        background_color: Color=BLACK,
        default_color_pair: ColorPair=YELLOW_ON_PURPLE,
        **kwargs,
    ):
        self._label_widget = TextWidget(
            size=(1, 1),
            pos=(1, 0),
            pos_hint=(None, .5),
            anchor=Anchor.TOP_CENTER,
            default_color_pair=default_color_pair,
        )

        self.callback = callback

        if hover_color_pair is None:
            self.hover_color_pair = _whiten_color_pair(default_color_pair, .1)
        else:
            self.hover_color_pair = hover_color_pair

        if down_color_pair is None:
            self.down_color_pair = _whiten_color_pair(default_color_pair, .25)
        else:
            self.down_color_pair = down_color_pair

        self.background_color = background_color

        super().__init__(default_color_pair=default_color_pair, **kwargs)

        self.add_widget(self._label_widget)

        self.label = label

        self.resize(self.size)

    def resize(self, size: Size):
        super().resize(size)

        self.canvas[:] =  self.default_char
        self.colors[:] = self.default_color_pair

        self.canvas[0] = "▀"
        self.canvas[-1] = "▄"
        self.colors[0, :, :3] = self.colors[-1, :, :3] = self.background_color

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, label: str):
        self._label = label
        self._label_widget.resize((1, len(label)))
        self._label_widget.update_geometry()
        self._label_widget.add_text(label)

    def on_release(self):
        self.callback()

    def update_hover(self):
        self.colors[:] = self._label_widget.colors[:] = self.hover_color_pair
        self.colors[0, :, :3] = self.colors[-1, :, :3] = self.background_color

    def update_down(self):
        self.colors[:] = self._label_widget.colors[:] = self.down_color_pair
        self.colors[0, :, :3] = self.colors[-1, :, :3] = self.background_color

    def update_normal(self):
        self.colors[:] = self._label_widget.colors[:] = self.default_color_pair
        self.colors[0, :, :3] = self.colors[-1, :, :3] = self.background_color
