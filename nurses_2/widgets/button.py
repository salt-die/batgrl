from typing import Callable

from ..colors import Color, ColorPair, BLACK
from .behaviors.button_behavior import ButtonBehavior
from .text_widget import TextWidget, Anchor

PURPLE = Color.from_hex("462270")
LIGHT_PURPLE = Color.from_hex("592c8c")
LIGHTER_PURPLE = Color.from_hex("753ab7")
YELLOW = Color.from_hex("dbd006")
YELLOW_ON_PURPLE = ColorPair.from_colors(YELLOW, PURPLE)

class Button(ButtonBehavior, TextWidget):
    """
    A button widget.

    Parameters
    ----------
    label : str, default: ""
        Button label.
    callback : Callable, default: lambda: None
        No-argument callable called when button is released.
    hover_color : Color | None, default: LIGHT_PURPLE
        Color of button on hover. If None, hover_color
        will be default_bg_color lightened.
    pressed_color : Color, default: LIGHTER_PURPLE
        Color of button when pressed.
    background_color : Color, default: BLACK
        Color of background for the button. Looks best with
        button's parent's background color.
    """
    def __init__(
        self,
        *,
        label: str="",
        callback: Callable=lambda: None,
        hover_color: Color | None=LIGHT_PURPLE,
        pressed_color: Color=LIGHTER_PURPLE,
        background_color: Color=BLACK,
        default_color_pair: ColorPair=YELLOW_ON_PURPLE,
        **kwargs,
    ):

        self.label = TextWidget(
            size=(1, len(label)),
            pos=(1, 0),
            pos_hint=(None, .5),
            anchor=Anchor.TOP_CENTER,
            default_color_pair=default_color_pair,
        )
        self.label.add_text(label)

        super().__init__(default_color_pair=default_color_pair, **kwargs)

        self.add_widget(self.label)

        if hover_color is None:
            self.hover_color = Color(
                *(127 + c // 2 for c in self.default_bg_color)
            )
        else:
            self.hover_color = hover_color

        self.pressed_color = pressed_color

        self.canvas[0] = "▀"
        self.canvas[-1] = "▄"
        self.colors[0, :, :3] = self.colors[-1, :, :3] = background_color

        self.callback = callback

    def on_release(self):
        self.callback()

    def update_hover(self):
        self.colors[..., -3:] = self.hover_color
        self.label.colors[..., -3:] = self.hover_color

    def update_down(self):
        self.colors[..., -3:] = self.pressed_color
        self.label.colors[..., -3:] = self.pressed_color

    def update_normal(self):
        self.colors[..., -3:] = self.default_bg_color
        self.label.colors[..., -3:] = self.default_bg_color
