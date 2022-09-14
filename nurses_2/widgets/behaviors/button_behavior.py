"""
Button behavior for a widget.
"""
from enum import Enum

from ...io import MouseEventType

__all__ = "ButtonState", "ButtonBehavior"


class ButtonState(str, Enum):
    """
    State of a button widget.

    :class:`ButtonState` is one of "normal", "hover", "down".
    """
    NORMAL = "normal"
    HOVER = "hover"
    DOWN = "down"


class ButtonBehavior:
    """
    Button behavior for a widget.

    A button has three states: 'normal', 'hover', and 'down'.

    When a button's state changes one of the following methods are called:
    :meth:`update_normal`, :meth:`update_hover`, and :meth:`update_down`.

    When a button is released, the :meth:`on_release` method is called.

    Parameters
    ----------
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.

    Attributes
    ----------
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of `NORMAL`, `HOVER`, `DOWN`.

    Methods
    -------
    update_normal:
        Paint the normal state.
    update_hover:
        Paint the hover state.
    update_down:
        Paint the down state.
    on_release:
        Triggered when a button is released.
    """
    def __init__(self, *, always_release=False, **kwargs):
        super().__init__(**kwargs)

        self.always_release = always_release
        self._normal()

    def _normal(self):
        self.state = ButtonState.NORMAL
        self.update_normal()

    def _hover(self):
        self.state = ButtonState.HOVER
        self.update_hover()

    def _down(self):
        self.state = ButtonState.DOWN
        self.update_down()

    def on_mouse(self, mouse_event):
        if super().on_mouse(mouse_event):
            return True

        collides = self.collides_point(mouse_event.position)

        if mouse_event.event_type is MouseEventType.MOUSE_DOWN:
            if collides:
                self._down()
                return True

        elif (
            mouse_event.event_type is MouseEventType.MOUSE_UP
            and self.state is ButtonState.DOWN
        ):
            self._normal()

            if collides:
                self._hover()
                self.on_release()
                return True

            if self.always_release:
                self.on_release()
                return True

        if not collides and self.state is ButtonState.HOVER:
            self._normal()
        elif collides and self.state is ButtonState.NORMAL:
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
