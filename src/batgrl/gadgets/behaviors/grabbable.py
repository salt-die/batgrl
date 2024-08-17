"""Grabbable behavior for a gadget."""

from ...terminal.events import MouseButton, MouseEvent

__all__ = ["Grabbable"]


class Grabbable:
    """
    Grabbable behavior for a gadget.

    Mouse down events that collide with the gadget will "grab" it, calling :meth:`grab`.
    While grabbed, each mouse event will call :meth:`grab_update` until the gadget is
    ungrabbed, i.e., a mouse up event is received (which calls :meth:`ungrab`).

    To customize grabbable behavior, implement any of :meth:`grab`, :meth:`grab_update`,
    or :meth:`ungrab`.

    Parameters
    ----------
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton, default: "left"
        Mouse button used for grabbing.

    Attributes
    ----------
    is_grabbable : bool
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        Whether gadget is grabbed.

    Methods
    -------
    grab(mouse_event)
        Grab the gadget.
    ungrab(mouse_event)
        Ungrab the gadget.
    grab_update(mouse_event)
        Update gadget with incoming mouse events while grabbed.
    """

    def __init__(
        self,
        *,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.is_grabbable = is_grabbable
        self.ptf_on_grab = ptf_on_grab
        self.mouse_button = mouse_button
        self._is_grabbed = False

    def on_mouse(self, mouse_event):
        """Determine if mouse event grabs or ungrabs gadget."""
        if self.is_grabbable:
            if self.is_grabbed:
                if mouse_event.event_type == "mouse_up":
                    self.ungrab(mouse_event)
                else:
                    self.grab_update(mouse_event)

                return True

            if (
                self.collides_point(mouse_event.pos)
                and mouse_event.event_type == "mouse_down"
                and mouse_event.button == self.mouse_button
            ):
                self.grab(mouse_event)
                return True

        return super().on_mouse(mouse_event)

    @property
    def is_grabbed(self) -> bool:
        """Whether gadget is grabbed."""
        return self._is_grabbed

    def grab(self, mouse_event: MouseEvent):
        """
        Grab gadget.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that grabbed the gadget.
        """
        self._is_grabbed = True

        if self.ptf_on_grab:
            self.pull_to_front()

    def ungrab(self, mouse_event: MouseEvent):
        """
        Ungrab gadget.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that ungrabbed the gadget.
        """
        self._is_grabbed = False

    def grab_update(self, mouse_event: MouseEvent):
        """
        Update grabbed gadget with incoming mouse event.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that updates the grabbed gadget.
        """
