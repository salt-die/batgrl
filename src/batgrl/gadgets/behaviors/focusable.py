"""Focus behavior for a gadget."""

from collections import deque
from weakref import ReferenceType, WeakSet, ref

__all__ = ["Focusable"]


class AnyFocusedProperty:
    def __get__(self, instance, owner):
        return bool(Focusable._Focusable__focused)


class Focusable:
    """
    Focus behavior for a gadget.

    Focusable gadgets can be given "focus" by pressing tab or shift + tab
    or by clicking on them. When a gadget is focused, all focusable ancestors
    also gain focus.

    Attributes
    ----------
    is_focused : bool
        Whether gadget has focus.
    any_focused : bool
        Whether any gadget has focus.

    Methods
    -------
    focus()
        Focus gadget.
    blur()
        Un-focus gadget.
    focus_next()
        Focus next focusable gadget.
    focus_previous()
        Focus previous focusable gadget.
    on_focus()
        Update gadget when it gains focus.
    on_blur()
        Update gadget when it loses focus.
    """

    __focusables: deque[ReferenceType] = deque()
    """Focusables that are part of the gadget tree."""
    __focused: WeakSet = WeakSet()
    """Focused focusables."""
    any_focused: bool = AnyFocusedProperty()
    """Whether any gadget has focus."""

    @classmethod
    def _focus(cls, step: int):
        focusables = cls.__focusables

        for _ in range(len(focusables)):
            gadget = focusables[0]()
            if gadget is None:
                focusables.popleft()
            elif (
                not gadget.is_visible
                or not gadget.is_enabled
                or gadget in cls.__focused
            ):
                focusables.rotate(step)
            else:
                gadget.focus()
                break

    @classmethod
    def focus_next(cls):
        """Focus next focusable gadget."""
        cls._focus(-1)

    @classmethod
    def focus_previous(cls):
        """Focus previous focusable gadget."""
        cls._focus(1)

    @property
    def is_focused(self) -> bool:
        """Whether gadget has focus."""
        return self in Focusable.__focused

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

        focus_gadgets = Focusable.__focusables
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

    def on_focus(self):
        """Update gadget when it gains focus."""

    def on_blur(self):
        """Update gadget when it loses focus."""

    def on_add(self):
        """Add to focusable gadgets and focus on add."""
        super().on_add()
        Focusable.__focusables.append(ref(self))
        self.focus()

    def on_remove(self):
        """Remove from focusable gadgets and blur on remove."""
        self.blur()
        Focusable.__focusables.remove(ref(self))
        super().on_remove()

    def dispatch_key(self, key_event) -> bool | None:
        """Dispatch key press only if focused."""
        return self.is_focused and super().dispatch_key(key_event)

    def dispatch_mouse(self, mouse_event) -> bool | None:
        """Focus if mouse event is handled."""
        handled = super().dispatch_mouse(mouse_event)
        if handled and not self.is_focused and self.is_visible:
            self.focus()
        return handled

    def on_mouse(self, mouse_event) -> bool | None:
        """Focus on mouse down collision and blur otherwise."""
        if mouse_event.event_type == "mouse_down" and self.is_visible:
            collides = self.collides_point(mouse_event.pos)
            if not self.is_focused and collides:
                self.focus()
            elif self.is_focused and not collides:
                self.blur()

        return super().on_mouse(mouse_event)
