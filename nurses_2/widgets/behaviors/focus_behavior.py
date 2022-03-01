from collections import deque
from weakref import ref, ReferenceType

from ...io import MouseEventType


class FocusBehavior:
    """
    Focusable widgets can be given "focus" by pressing tab or shift + tab
    or by clicking on them. When a widget gains focus the `on_focus` method
    is called. When a widget loses focus the `on_blur` method is called.

    Parameters
    ----------
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.
    """
    _focus_widgets: deque[ReferenceType] = deque()
    _focused = None

    def __init__(self, ptf_on_focus=True, **kwargs):
        FocusBehavior._focus_widgets.append(ref(self))
        self.ptf_on_focus = ptf_on_focus
        super().__init__(**kwargs)

    @property
    def is_focused(self):
        return FocusBehavior._focused is not None and FocusBehavior._focused() is self

    def on_press(self, key_press_event):
        if key_press_event.key != "tab":
            return super().on_press(key_press_event)

        focus_widgets = FocusBehavior._focus_widgets

        if (
            FocusBehavior._focused is None
            or FocusBehavior._focused() is None
        ):
            while (widget := focus_widgets[0]()) is None:
                focus_widgets.popleft()

            FocusBehavior._focused = ref(widget)

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

        last_focused = FocusBehavior._focused()
        FocusBehavior._focused = ref(widget)
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
                FocusBehavior._focused is not None
                and FocusBehavior._focused() is not None
            ):
                last_focused = FocusBehavior._focused()
                FocusBehavior._focused = None
                last_focused.on_blur()

            focus_widgets = FocusBehavior._focus_widgets

            while (widget := focus_widgets[0]()) is not self:
                if widget is None:
                    focus_widgets.popleft()
                else:
                    focus_widgets.rotate(-1)

            FocusBehavior._focused = ref(self)

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
