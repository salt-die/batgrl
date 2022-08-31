"""
Focus behavior for a widget.
"""
from collections import deque
from weakref import ref, ReferenceType

from ...io import MouseEventType


class FocusBehavior:
    """
    Focus behavior for a widget.

    Focusable widgets can be given "focus" by pressing tab or shift + tab
    or by clicking on them. When a widget gains focus :meth:`on_focus`
    is called. When a widget loses focus the :meth:`on_blur` is called.

    Parameters
    ----------
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.

    Attributes
    ----------
    ptf_on_focus : bool
        Pull widget to front when it gains focus.
    is_focused : bool
        True if widget has focus.

    Methods
    -------
    on_focus:
        Called when widget is focused.
    on_blur:
        Called when widget loses focus.
    """
    __focus_widgets: deque[ReferenceType] = deque()
    __focused = None

    def __init__(self, ptf_on_focus=True, **kwargs):
        FocusBehavior.__focus_widgets.append(ref(self))
        self.ptf_on_focus = ptf_on_focus
        super().__init__(**kwargs)

    @property
    def is_focused(self) -> bool:
        return FocusBehavior.__focused is not None and FocusBehavior.__focused() is self

    def dispatch_press(self, key_press_event):
        if key_press_event.key != "tab":
            if self.is_focused:
                return super().dispatch_press(key_press_event)

            return False

        focus_widgets = FocusBehavior.__focus_widgets

        if (
            FocusBehavior.__focused is None
            or FocusBehavior.__focused() is None
        ):
            while (widget := focus_widgets[0]()) is None:
                focus_widgets.popleft()

            FocusBehavior.__focused = ref(widget)

            if widget.ptf_on_focus:
                widget.pull_to_front()

            widget.on_focus()

            return True

        if key_press_event.mods.shift:
            while (widget := focus_widgets[-1]()) is None:
                focus_widgets.pop()

            focus_widgets.rotate(1)
        else:
            focus_widgets.rotate(-1)

            while (widget := focus_widgets[0]()) is None:
                focus_widgets.popleft()

        last_focused = FocusBehavior.__focused()
        FocusBehavior.__focused = ref(widget)
        last_focused.on_blur()

        if widget.ptf_on_focus:
            widget.pull_to_front()

        widget.on_focus()

        return True

    def dispatch_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and not self.is_focused
            and self.collides_point(mouse_event.position)
        ):
            if (
                FocusBehavior.__focused is not None
                and FocusBehavior.__focused() is not None
            ):
                last_focused = FocusBehavior.__focused()
                FocusBehavior.__focused = None
                last_focused.on_blur()

            focus_widgets = FocusBehavior.__focus_widgets

            while (widget := focus_widgets[0]()) is not self:
                if widget is None:
                    focus_widgets.popleft()
                else:
                    focus_widgets.rotate(-1)

            FocusBehavior.__focused = ref(self)

            if self.ptf_on_focus:
                self.pull_to_front()

            self.on_focus()

        return super().dispatch_click(mouse_event)

    def on_focus(self):
        """
        Called when widget gains focus.
        """

    def on_blur(self):
        """
        Called when widget loses focus.
        """
