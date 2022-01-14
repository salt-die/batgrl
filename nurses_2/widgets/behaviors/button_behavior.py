from enum import Enum

from ...io import MouseEventType, MouseButton


class ButtonStates(Enum):
    NORMAL = "normal"
    HOVER = "hover"
    DOWN = "down"


class ButtonBehavior:
    """
    Button behavior for a widget.

    A button has three states: 'normal', 'hover', and 'down'.

    When a button's state changes one of the following methods are called:
    'update_normal', 'update_hover', and 'update_down'.

    When a button is released, the `on_release` method is called.

    Parameters
    ----------
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    """
    def __init__(self, *, always_release=False, **kwargs):
        super().__init__(**kwargs)

        self.always_release = always_release
        self._normal()

    def _normal(self):
        self.state = ButtonStates.NORMAL
        self.update_normal()

    def _hover(self):
        self.state = ButtonStates.HOVER
        self.update_hover()

    def _down(self):
        self.state = ButtonStates.DOWN
        self.update_down()

    def on_click(self, mouse_event):
        if super().on_click(mouse_event):
            return True

        collides = self.collides_point(mouse_event.position)

        if mouse_event.event_type is MouseEventType.MOUSE_DOWN:
            if collides:
                self._down()
                return True

        elif (
            mouse_event.event_type is MouseEventType.MOUSE_UP
            and self.state is ButtonStates.DOWN
        ):
            self._normal()

            if collides:
                self._hover()
                self.on_release()
                return True

            if self.always_release:
                self.on_release()
                return True

        if not collides and self.state is ButtonStates.HOVER:
            self._normal()
        elif collides and self.state is ButtonStates.NORMAL:
            self._hover()

    def update_normal(self):
        """
        Paint the NORMAL state.
        """

    def update_hover(self):
        """
        Paint the HOVER state.
        """

    def update_down(self):
        """
        Paint the DOWN state.
        """

    def on_release(self):
        """
        Triggered when button is released.
        """
