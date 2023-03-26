from nurses_2.widgets.behaviors.button_behavior import ButtonBehavior
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

from .colors import DEFAULT_COLOR_PAIR
from .effects import Darken


class OKButton(ButtonBehavior, TextWidget):
    def __init__(self):
        super().__init__(size=(1, 6), pos=(3, 7), default_color_pair=DEFAULT_COLOR_PAIR)
        self.add_str("[ OK ]")

    def update_hover(self):
        self.colors[:] = DEFAULT_COLOR_PAIR.reversed()

    def update_normal(self):
        self.colors[:] = DEFAULT_COLOR_PAIR

    def on_release(self):
        modal = self.parent.parent
        modal.memory.init_memory()
        modal.is_enabled = False


class Modal(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background = Darken(size_hint=(1.0, 1.0))
        self.message_box = TextWidget(
            size=(6, 20),
            pos_hint=(.5, .5),
            anchor="center",
            default_color_pair=DEFAULT_COLOR_PAIR,
        )
        self.message_box.add_border("heavy")
        self.message_box.add_widget(OKButton())
        self.add_widgets(self.background, self.message_box)

    def show(self, is_win):
        message = " System Accessed. " if is_win else "  System Locked.  "
        self.message_box.add_str(message, pos=(2, 1))
        self.is_enabled = True

    def on_mouse(self, mouse_event):
        """
        Stop mouse dispatching while modal is enabled.
        """
        return True