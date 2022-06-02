"""
A button widget.
"""
from collections.abc import Callable

from wcwidth import wcswidth

from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
from .text_widget import TextWidget, Anchor
from .widget import Widget


class Button(Themable, ButtonBehavior, Widget):
    """
    A button widget.

    Parameters
    ----------
    label : str, default: ""
        Button label.
    callback : Callable[[], None], default: lambda: None
        Called when button is released.

    Attributes
    ----------
    label : str, default: ""
        Button label.
    callback : Callable[[], None], default: lambda: None
        Called when button is released.
    """
    def __init__(
        self,
        *,
        background_char=" ",
        label: str="",
        callback: Callable[[], None]=lambda: None,
        **kwargs,
    ):
        self.normal_color_pair = (0, ) * 6  # Temporary assignment

        self._label_widget = TextWidget(pos_hint=(.5, .5), anchor=Anchor.CENTER)

        super().__init__(background_char=background_char, **kwargs)

        self.add_widget(self._label_widget)

        self.label = label
        self.callback = callback

        self.update_theme()

    def update_theme(self):
        ct = self.color_theme

        self.normal_color_pair = ct.primary_color_pair
        self.hover_color_pair = ct.primary_light_color_pair
        self.down_color_pair = ct.secondary_color_pair

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
        self._label_widget.size = 1, wcswidth(label)
        self._label_widget.update_geometry()
        self._label_widget.add_text(label)

    def on_release(self):
        self.callback()

    def update_hover(self):
        self.background_color_pair = self._label_widget.colors[:] = self.hover_color_pair

    def update_down(self):
        self.background_color_pair = self._label_widget.colors[:] = self.down_color_pair

    def update_normal(self):
        self.background_color_pair = self._label_widget.colors[:] = self.normal_color_pair
