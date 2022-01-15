from typing import Callable

from ..colors import Color, ColorPair, BLACK, WHITE, lerp_colors
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .text_widget import TextWidget, Anchor, Size

YELLOW = Color.from_hex("dbd006")
PURPLE = Color.from_hex("462270")
YELLOW_ON_PURPLE = ColorPair.from_colors(YELLOW, PURPLE)
WHITE_ON_WHITE = ColorPair.from_colors(WHITE, WHITE)

class Button(ButtonBehavior, TextWidget):
    """
    A button widget.

    Parameters
    ----------
    label : str, default: ""
        Button label.
    callback : Callable, default: lambda: None
        No-argument callable called when button is released.
    normal_color_pair: ColorPair, default: YELLOW_ON_PURPLE
        Color pair of button in normal state.
    hover_color_pair : ColorPair | None, default: None
        Color pair of button on hover. If None, hover_color_pair
        will be normal_color_pair, but whitened.
    down_color_pair : ColorPair | None, default: None
        Color pair of button in down state. If none, down_color_pair
        will be normal_color_pair, but whitened (and brighter than
        default hover_color_pair).
    background_color : Color, default: BLACK
        Color of background for the button.
    """
    def __init__(
        self,
        *,
        label: str="",
        callback: Callable=lambda: None,
        normal_color_pair: ColorPair=YELLOW_ON_PURPLE,
        hover_color_pair: ColorPair | None=None,
        down_color_pair: ColorPair | None=None,
        background_color: Color=BLACK,
        **kwargs,
    ):
        self._label_widget = TextWidget(
            size=(1, 1),
            pos=(1, 0),
            pos_hint=(None, .5),
            anchor=Anchor.TOP_CENTER,
        )

        self.callback = callback

        self.normal_color_pair = normal_color_pair

        if hover_color_pair is None:
            self.hover_color_pair = lerp_colors(normal_color_pair, WHITE_ON_WHITE, .1)
        else:
            self.hover_color_pair = hover_color_pair

        if down_color_pair is None:
            self.down_color_pair = lerp_colors(normal_color_pair, WHITE_ON_WHITE, .25)
        else:
            self.down_color_pair = down_color_pair

        self.background_color = background_color

        super().__init__(**kwargs)

        self.add_widget(self._label_widget)

        self.label = label

        self.resize(self.size)

    def resize(self, size: Size):
        super().resize(size)

        self.canvas[:] =  self.default_char
        self.canvas[0] = "▀"
        self.canvas[-1] = "▄"

        match self.state:
            case ButtonState.NORMAL:
                self.update_normal()
            case ButtonState.HOVER:
                self.update_hover()
            case ButtonState.DOWN:
                self.update_down()

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
        self.colors[:] = self._label_widget.colors[:] = self.normal_color_pair
        self.colors[0, :, :3] = self.colors[-1, :, :3] = self.background_color
