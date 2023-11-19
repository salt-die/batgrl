"""
Movable children behavior for a gadget.

Translate movable's children by dragging them.
"""
from ...io import MouseButton
from ..gadget import clamp
from .grabbable import Grabbable

__all__ = ["MovableChildren"]


class MovableChildren(Grabbable):
    """
    Movable children behavior for a gadget.

    Translate movable's children by dragging them.

    Parameters
    ----------
    disable_child_oob : bool, default: False
        Disallow child gadgets from being translated out-of-bounds if true.
    disable_child_ptf : bool, default: False
        If true, child gadgets won't be pulled-to-front when clicked.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.

    Attributes
    ----------
    disable_child_oob : bool
        Disallow child gadgets from being translated out-of-bounds if true.
    disable_child_ptf : bool
        If true, child gadgets won't be pulled-to-front when clicked.
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
        disable_child_oob=False,
        disable_child_ptf=False,
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
        self.disable_child_oob = disable_child_oob
        self.disable_child_ptf = disable_child_ptf

        self._grabbed_child = None

    def grab(self, mouse_event):
        """Grab the gadget."""
        for child in reversed(self.children):
            if child.collides_point(mouse_event.position):
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
            dy, dx = self.mouse_dyx
            h, w = self.size
            ch, cw = grabbed_child.size
            ct, cl = grabbed_child.pos

            if self.disable_child_oob:
                grabbed_child.top = clamp(ct + dy, 0, h - ch)
                grabbed_child.left = clamp(cl + dx, 0, w - cw)
            else:
                grabbed_child.top = ct + dy
                grabbed_child.left = cl + dx
        else:
            super().grab_update(mouse_event)
