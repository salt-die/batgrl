"""
Focus behavior for a widget.
"""
from collections import deque
from weakref import ref, ReferenceType, WeakSet

from ...io import MouseEventType


class FocusBehavior:
    """
    Focus behavior for a widget.

    Focusable widgets can be given "focus" by pressing tab or shift + tab
    or by clicking on them. When a widget is focused, all focusable ancestors
    also gain focus.

    Parameters
    ----------
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.

    Attributes
    ----------
    ptf_on_focus : bool
        Pull widget to front when it gains focus.
    is_focused : bool
        Return True if widget has focus.
    any_focused : bool
        Return True if any widget has focus.

    Methods
    -------
    focus:
        Focus widget.
    blur:
        Un-focus widget.
    focus_next:
        Focus next focusable widget.
    focus_previous:
        Focus previous focusable widget.
    on_focus:
        Called when widget is focused.
    on_blur:
        Called when widget loses focus.

    Notes
    -----
    Disabled focusables can be focused. This behavior will change in the future.
    """
    __focus_widgets: deque[ReferenceType] = deque()
    __focused = WeakSet()

    def __init__(self, ptf_on_focus=True, **kwargs):
        self.ptf_on_focus = ptf_on_focus
        super().__init__(**kwargs)

    def on_add(self):
        FocusBehavior.__focus_widgets.append(ref(self))
        super().on_add()

    def on_remove(self):
        super().on_remove()

        if self.is_focused:
            FocusBehavior.__focused.remove(self)  # Avoiding `on_blur` being called.

            for ancestor in self.walk(reverse=True):
                if isinstance(ancestor, FocusBehavior):
                    ancestor.focus()
                    break

        FocusBehavior.__focus_widgets.remove(ref(self))

    @property
    def is_focused(self) -> bool:
        """
        Return True if widget has focus.
        """
        return self in FocusBehavior.__focused

    @property
    def any_focused(self) -> bool:
        """
        Return True if any widget has focus.
        """
        return bool(FocusBehavior.__focused)

    def focus(self):
        """
        Focus widget.
        """
        ancestors = WeakSet(
            ancestor
            for ancestor in self.walk(reverse=True)
            if isinstance(ancestor, FocusBehavior)
        )
        ancestors.add(self)

        focused = FocusBehavior.__focused
        FocusBehavior.__focused = ancestors

        for blurred in focused - ancestors:
            blurred.on_blur()

        for needs_focus in ancestors - focused:
            if needs_focus.ptf_on_focus:
                needs_focus.pull_to_front()

            needs_focus.on_focus()

        focus_widgets = FocusBehavior.__focus_widgets
        while (widget := focus_widgets[0]()) is not self:
            if widget is None:
                focus_widgets.popleft()
            else:
                focus_widgets.rotate(-1)

    def blur(self):
        """
        Un-focus widget.
        """
        if self.is_focused:
            for ancestor in self.walk(reverse=True):
                if isinstance(ancestor, FocusBehavior):
                    ancestor.focus()
                    return

            FocusBehavior.__focused.remove(self)
            self.on_blur()

    def focus_next(self):
        """
        Focus next focusable widget.
        """
        focus_widgets = FocusBehavior.__focus_widgets

        if self.any_focused:
            focus_widgets.rotate(-1)

        while (widget := focus_widgets[0]()) is None:
            focus_widgets.popleft()

        widget.focus()

    def focus_previous(self):
        """
        Focus previous focusable widget.
        """
        focus_widgets = FocusBehavior.__focus_widgets

        if self.any_focused:
            while (widget := focus_widgets[-1]()) is None:
                focus_widgets.pop()

            focus_widgets.rotate(1)
        else:
            while (widget := focus_widgets[0]()) is None:
                focus_widgets.popleft()

        widget.focus()

    # TODO: Dispatch to focusables should be handled by the running app. Making the following two methods obsolete.
    def dispatch_key(self, key_event):
        if key_event.key == "tab":
            if not (self.any_focused and FocusBehavior.__focus_widgets[0]().on_key(key_event)):
                if key_event.mods.shift:
                    self.focus_previous()
                else:
                    self.focus_next()
            return True

        return super().dispatch_key(key_event)

    def dispatch_mouse(self, mouse_event):
        if mouse_event.event_type is MouseEventType.MOUSE_DOWN:
            collides = self.collides_point(mouse_event.position)
            if not self.is_focused and collides:
                self.focus()
            elif self.is_focused and not collides:
                self.blur()

        return super().dispatch_mouse(mouse_event)

    def on_focus(self):
        """
        Called when widget gains focus.
        """

    def on_blur(self):
        """
        Called when widget loses focus.
        """
