"""Button behavior for a gadget."""

from typing import Literal

__all__ = ["ButtonState", "ButtonBehavior"]

ButtonState = Literal["normal", "hover", "down", "disallowed"]
"""Button behavior states."""


class ButtonBehavior:
    """
    Button behavior for a gadget.

    A button has four states: "normal", "hover", "down", and "disallowed".

    When a button's state changes one of the following methods are called:
    - :meth:`update_normal`
    - :meth:`update_hover`
    - :meth:`update_down`
    - :meth:`update_disallowed`

    When a button is released, the :meth:`on_release` method is called.

    Parameters
    ----------
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.

    Attributes
    ----------
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    button_state : ButtonState
        Current button state.

    Methods
    -------
    on_release()
        Triggered when a button is released.
    update_normal()
        Paint the normal state.
    update_hover()
        Paint the hover state.
    update_down()
        Paint the down state.
    update_disallowed()
        Paint the disallowed state.
    """

    def __init__(self, *, always_release: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.always_release = always_release
        self.button_state: ButtonState = "normal"

    @property
    def button_state(self) -> ButtonState:
        """Current button state."""
        return self._button_state

    @button_state.setter
    def button_state(self, button_state: ButtonState):
        dispatch = {
            "normal": self.update_normal,
            "hover": self.update_hover,
            "down": self.update_down,
            "disallowed": self.update_disallowed,
        }
        if button_state not in dispatch:
            button_state = "normal"

        self._button_state = button_state
        if self.root:
            dispatch[button_state]()

    def on_add(self):
        """Paint normal state on add."""
        super().on_add()
        self.update_normal()

    def on_mouse(self, mouse_event) -> bool | None:
        """Determine button state from mouse event."""
        if self.button_state == "disallowed":
            return False

        if super().on_mouse(mouse_event):
            return True

        collides = self.collides_point(mouse_event.pos)

        if mouse_event.event_type == "mouse_down":
            if collides:
                self.button_state = "down"
                return True

        elif mouse_event.event_type == "mouse_up" and self.button_state == "down":
            if collides:
                self.on_release()
                self.button_state = "hover"
                return True

            self.button_state = "normal"

            if self.always_release:
                self.on_release()
                return True

        if not collides and self.button_state == "hover":
            self.button_state = "normal"
        elif collides and self.button_state == "normal":
            self.button_state = "hover"

    def on_release(self):
        """Triggered when button is released."""

    def update_normal(self):
        """Paint the normal state."""

    def update_hover(self):
        """Paint the hover state."""

    def update_down(self):
        """Paint the down state."""

    def update_disallowed(self):
        """Paint the disallowed state."""
