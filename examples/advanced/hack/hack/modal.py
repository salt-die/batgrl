from batgrl.gadgets.behaviors.button_behavior import ButtonBehavior
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.text import Text

from .colors import DEFAULT_COLOR_PAIR
from .effects import Darken


class OKButton(ButtonBehavior, Text):
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


class Modal(Gadget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background = Darken(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, is_transparent=True
        )
        self.message_box = Text(
            size=(6, 20),
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            default_color_pair=DEFAULT_COLOR_PAIR,
        )
        self.message_box.add_border("heavy")
        self.message_box.add_gadget(OKButton())
        self.add_gadgets(self.background, self.message_box)

    def show(self, is_win):
        message = " System Accessed. " if is_win else "  System Locked.  "
        self.message_box.add_str(message, pos=(2, 1))
        self.is_enabled = True

    def on_mouse(self, mouse_event):
        """
        Stop mouse dispatching while modal is enabled.
        """
        return True
