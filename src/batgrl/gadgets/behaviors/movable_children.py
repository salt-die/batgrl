"""
Movable children behavior for a gadget.

Translate movable's children by dragging them.
"""

from ...geometry import clamp
from ...terminal.events import MouseButton
from .grabbable import Grabbable

__all__ = ["MovableChildren"]


class MovableChildren(Grabbable):
    """
    Movable children behavior for a gadget.

    Translate a gadget's child by clicking and dragging it.

    Parameters
    ----------
    disable_child_oob : bool, default: False
        Disallow child gadgets from being translated out-of-bounds if true.
    disable_child_ptf : bool, default: False
        Whether child gadgets are pulled-to-front when clicked.
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton, default: "left"
        Mouse button used for grabbing.

    Attributes
    ----------
    disable_child_oob : bool
        Disallow child gadgets from being translated out-of-bounds if true.
    disable_child_ptf : bool
        Whether child gadgets are pulled-to-front when clicked.
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
        disable_child_oob=False,
        disable_child_ptf=False,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        **kwargs,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            ptf_on_grab=ptf_on_grab,
            mouse_button=mouse_button,
            **kwargs,
        )
        self.disable_child_oob = disable_child_oob
        self.disable_child_ptf = disable_child_ptf

        self._grabbed_child = None

    def grab(self, mouse_event):
        """Grab the gadget."""
        for child in reversed(self.children):
            if child.collides_point(mouse_event.pos):
                self._is_grabbed = True
                self._grabbed_child = child

                if not self.disable_child_ptf:
                    child.pull_to_front()

                break
        else:
            super().grab(mouse_event)

    def ungrab(self, mouse_event):
        """Ungrab the gadget."""
        self._grabbed_child = None
        super().ungrab(mouse_event)

    def grab_update(self, mouse_event):
        """Update gadget with incoming mouse events while grabbed."""
        if grabbed_child := self._grabbed_child:
            h, w = self.size
            ch, cw = grabbed_child.size
            ct, cl = grabbed_child.pos

            if self.disable_child_oob:
                grabbed_child.top = clamp(ct + mouse_event.dy, 0, h - ch)
                grabbed_child.left = clamp(cl + mouse_event.dx, 0, w - cw)
            else:
                grabbed_child.top = ct + mouse_event.dy
                grabbed_child.left = cl + mouse_event.dx
        else:
            super().grab_update(mouse_event)
