"""Movable behavior for a gadget."""

from ...geometry import clamp
from ...terminal.events import MouseButton
from .grabbable import Grabbable

__all__ = ["Movable"]


class Movable(Grabbable):
    """
    Movable behavior for a gadget.

    Translate a gadget by clicking and dragging it.

    Parameters
    ----------
    allow_oob : bool, default: False
        Whether gadget can be dragged out of parent's bounding box.
    allow_vertical_translation : bool, default: True
        Whether to allow vertical translation.
    allow_horizontal_translation : bool, default: True
        Whether to allow horizontal translation.
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton, default: "left"
        Mouse button used for grabbing.

    Attributes
    ----------
    allow_oob : bool
        Whether gadget can be dragged out of parent's bounding box.
    allow_vertical_translation : bool
        Whether to allow vertical translation.
    allow_horizontal_translation : bool
        Whether to allow horizontal translation.
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
        allow_oob=True,
        allow_vertical_translation=True,
        allow_horizontal_translation=True,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        **kwargs,
    ) -> None:
        super().__init__(
            is_grabbable=is_grabbable,
            ptf_on_grab=ptf_on_grab,
            mouse_button=mouse_button,
            **kwargs,
        )
        self.allow_oob: bool = allow_oob
        """Whether gadget can be dragged out of parent's bounding box."""
        self.allow_vertical_translation: bool = allow_vertical_translation
        """Whether to allow vertical translation."""
        self.allow_horizontal_translation: bool = allow_horizontal_translation
        """Whether to allow horizontal translation."""

    def grab_update(self, mouse_event) -> None:
        """Translate movable on grab update."""
        if self.allow_vertical_translation:
            self.top += mouse_event.dy
        if self.allow_horizontal_translation:
            self.left += mouse_event.dx

        if self.parent is None:
            # Should be unreachable.
            return

        if not self.allow_oob:
            self.top = clamp(self.top, 0, self.parent.height - self.height)
            self.left = clamp(self.left, 0, self.parent.width - self.width)
