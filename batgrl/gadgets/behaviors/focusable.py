"""Focus behavior for a gadget."""
from collections import deque
from weakref import ReferenceType, WeakSet, ref

from ...io import Key, MouseEventType

__all__ = ["Focusable"]


class Focusable:
    """
    Focus behavior for a gadget.

    Focusable gadgets can be given "focus" by pressing tab or shift + tab
    or by clicking on them. When a gadget is focused, all focusable ancestors
    also gain focus.

    Attributes
    ----------
    is_focused : bool
        True if gadget has focus.
    any_focused : bool
        True if any gadget has focus.

    Methods
    -------
    focus():
        Focus gadget.
    blur():
        Un-focus gadget.
    focus_next():
        Focus next focusable gadget.
    focus_previous():
        Focus previous focusable gadget.
    on_focus():
        Update gadget when it gains focus.
    on_blur():
        Update gadget when it loses focus.
    """

    __focus_gadgets: deque[ReferenceType] = deque()
    __focused = WeakSet()

    def on_add(self):
        """Add to focusable gadgets and focus on add."""
        super().on_add()
        Focusable.__focus_gadgets.append(ref(self))
        self.focus()

    def on_remove(self):
        """Remove from focusable gadgets and blur on remove."""
        self.blur()
        Focusable.__focus_gadgets.remove(ref(self))
        super().on_remove()

    @property
    def is_focused(self) -> bool:
        """True if gadget has focus."""
        return self in Focusable.__focused

    @property
    def any_focused(self) -> bool:
        """True if any gadget has focus."""
        return bool(Focusable.__focused)

    def focus(self):
        """Focus gadget."""
        if not self.is_enabled:
            return

        ancestors = WeakSet(
            ancestor for ancestor in self.ancestors() if isinstance(ancestor, Focusable)
        )
        ancestors.add(self)

        focused = Focusable.__focused
        Focusable.__focused = ancestors

        for blurred in focused - ancestors:
            blurred.on_blur()

        for needs_focus in ancestors - focused:
            needs_focus.on_focus()

        focus_gadgets = Focusable.__focus_gadgets
        while (gadget := focus_gadgets[0]()) is not self:
            if gadget is None:
                focus_gadgets.popleft()
            else:
                focus_gadgets.rotate(-1)

    def blur(self):
        """Un-focus gadget."""
        if self.is_focused:
            for ancestor in self.ancestors():
                if isinstance(ancestor, Focusable):
                    ancestor.focus()
                    return

            Focusable.__focused.remove(self)
            self.on_blur()

    def focus_next(self):
        """Focus next focusable gadget."""
        focus_gadgets = Focusable.__focus_gadgets

        if self.any_focused:
            focus_gadgets.rotate(-1)

        for _ in range(len(focus_gadgets)):
            gadget = focus_gadgets[0]()
            if gadget is None:
                focus_gadgets.popleft()
            elif not gadget.is_visible or not gadget.is_enabled:
                focus_gadgets.rotate(-1)
            else:
                gadget.focus()
                return

    def focus_previous(self):
        """Focus previous focusable gadget."""
        focus_gadgets = Focusable.__focus_gadgets

        if self.any_focused:
            focus_gadgets.rotate(1)

        for _ in range(len(focus_gadgets)):
            gadget = focus_gadgets[0]()
            if gadget is None:
                focus_gadgets.popleft()
            elif not gadget.is_visible or not gadget.is_enabled:
                focus_gadgets.rotate(1)
            else:
                gadget.focus()
                return

    def on_key(self, key_event):
        """Focus next or previous focusable on tab or shift-tab, respectively."""
        if super().on_key(key_event):
            return True

        if key_event.key is Key.Tab:
            if key_event.mods.shift:
                self.focus_previous()
            else:
                self.focus_next()
            return True

        return False

    def dispatch_mouse(self, mouse_event):
        """Focus if mouse event is handled."""
        handled = super().dispatch_mouse(mouse_event)
        if handled and not self.is_focused and self.is_visible:
            self.focus()
        return handled

    def on_mouse(self, mouse_event):
        """Focus on mouse down collision and blur otherwise."""
        if mouse_event.event_type is MouseEventType.MOUSE_DOWN and self.is_visible:
            collides = self.collides_point(mouse_event.position)
            if not self.is_focused and collides:
                self.focus()
            elif self.is_focused and not collides:
                self.blur()

        return super().on_mouse(mouse_event)

    def on_focus(self):
        """Update gadget when it gains focus."""

    def on_blur(self):
        """Update gadget when it loses focus."""
