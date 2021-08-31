from enum import Enum

from ...io import MouseEventType


class ButtonStates(Enum):
    DOWN = "DOWN"
    NORMAL = "NORMAL"


class ButtonBehavior:
    """
    Button behavior for a widget.

    When a button is pressed, its state changes to `ButtonStates.DOWN`. It then calls
    `update_down` (a method meant to redraw the button's canvas).

    When a button is released, its state changes to `ButtonStates.NORMAL`. It then
    calls `update_normal` (to redraw the canvas) and then `on_release` is called.

    Parameters
    ----------
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    """
    def __init__(self, *args, always_release=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.always_release = always_release
        self._release()

    def _press(self):
        self.state = ButtonStates.DOWN
        self.update_down()

    def _release(self):
        self.state = ButtonStates.NORMAL
        self.update_normal()

    def on_click(self, mouse_event):
        if super().on_click(mouse_event):
            return True

        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            if (
                self.state == ButtonStates.NORMAL
                and self.collides_coords(mouse_event.position)
            ):
                self._press()
                return True

            self._release()

        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            if (
                self.state == ButtonStates.DOWN
                and (self.always_release or self.collides_coords(mouse_event.position))
            ):
                self._release()
                self.on_release()

                return True

            self._release()

        return self.state == ButtonStates.DOWN

    def update_down(self):
        """
        Paint the DOWN state.
        """

    def update_normal(self):
        """
        Paint the NORMAL state.
        """

    def on_release(self):
        """
        Triggered when button is released.
        """
