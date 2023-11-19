"""Movable behavior for a gadget."""
from ...io import MouseButton
from ..gadget import clamp
from .grabbable import Grabbable

__all__ = ["Movable"]


class Movable(Grabbable):
    """
    Movable behavior for a gadget. Translate a gadget by clicking and dragging it.

    Parameters
    ----------
    disable_oob : bool, default: False
        If true, gadget won't be translated outside of its parent's bounding box.
    allow_vertical_translation : bool, default: True
        Allow vertical translation.
    allow_horizontal_translation : bool, default: True
        Allow horizontal translation.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.

    Attributes
    ----------
    disable_oob : bool
        If true, gadget won't be translated outside of its parent's bounding box.
    allow_vertical_translation : bool
        Allow vertical translation.
    allow_horizontal_translation : bool
        Allow horizontal translation.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        True if gadget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.

    Methods
    -------
    grab(mouse_event):
        Grab the gadget.
    ungrab(mouse_event):
        Ungrab the gadget.
    grab_update(mouse_event):
        Update gadget with incoming mouse events while grabbed.
    """

    def __init__(
        self,
        *,
        disable_oob=False,
        allow_vertical_translation=True,
        allow_horizontal_translation=True,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
        **kwargs,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            disable_ptf=disable_ptf,
            mouse_button=mouse_button,
            **kwargs,
        )
        self.disable_oob = disable_oob
        self.allow_vertical_translation = allow_vertical_translation
        self.allow_horizontal_translation = allow_horizontal_translation

    def grab_update(self, mouse_event):
        """Translate movable on grab update."""
        if self.allow_vertical_translation:
            self.top += self.mouse_dy
        if self.allow_horizontal_translation:
            self.left += self.mouse_dx

        if self.disable_oob:
            self.top = clamp(self.top, 0, self.parent.height - self.height)
            self.left = clamp(self.left, 0, self.parent.width - self.width)
