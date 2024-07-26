"""Toggle button behavior for a gadget."""

from collections.abc import Hashable
from typing import Literal, Self
from weakref import WeakValueDictionary

from .button_behavior import ButtonBehavior, ButtonState

__all__ = ["ButtonState", "ToggleState", "ToggleButtonBehavior"]

ToggleState = Literal["on", "off"]
"""Toggle button behavior states."""


class ToggleButtonBehavior(ButtonBehavior):
    """
    Toggle button behavior for gadgets.

    Without a group, toggle button's states switch between "on" and "off" when pressed.
    With a group, only a single button in the group can be in the "on" state at a time.

    Parameters
    ----------
    group : Hashable | None, default: None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the off state.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.

    Attributes
    ----------
    group : Hashable | None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool
        If true and button is in a group, every button can be in the off state.
    toggle_state : ToggleState
        Toggle state of button.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    button_state : ButtonState
        Current button state.

    Methods
    -------
    on_toggle()
        Triggled on toggle state change.
    update_off()
        Paint the off state.
    update_on()
        Paint the on state.
    on_release()
        Triggered when a button is released.
    update_normal()
        Paint the normal state.
    update_hover()
        Paint the hover state.
    update_down()
        Paint the down state.
    update_disallowed()
        Paint the disallowed state.
    """

    _toggle_groups: WeakValueDictionary[Hashable, Self] = WeakValueDictionary()

    def __init__(
        self,
        group: Hashable | None = None,
        allow_no_selection: bool = False,
        always_release: bool = False,
        **kwargs,
    ):
        self._toggle_state = "off"
        super().__init__(always_release=always_release, **kwargs)
        self.group = group
        self.allow_no_selection = allow_no_selection

        if (
            group is not None
            and not allow_no_selection
            and ToggleButtonBehavior._toggle_groups.get(group) is None
        ):
            ToggleButtonBehavior._toggle_groups[group] = self
            self._toggle_state = "on"
            self.update_on()
        else:
            self.update_off()

    @property
    def toggle_state(self) -> ToggleState:
        """Toggle state of button."""
        return self._toggle_state

    @toggle_state.setter
    def toggle_state(self, toggle_state: ToggleState):
        if self._toggle_state == toggle_state:
            return

        groups = ToggleButtonBehavior._toggle_groups
        grouped_on = groups.get(self.group)

        if toggle_state == "on":
            if grouped_on is not None:
                grouped_on._toggle_state = "off"
                grouped_on.update_off()
                grouped_on.on_toggle()
            if self.group is not None:
                groups[self.group] = self
            self.update_on()
        else:
            if grouped_on is self:
                if self.allow_no_selection:
                    del groups[self.group]
                else:
                    return
            self.update_off()

        self._toggle_state = toggle_state
        self.on_toggle()

    def on_toggle(self):
        """Update gadget on toggle state change."""

    def on_release(self):
        """Triggered when button is released."""
        self.toggle_state = "off" if self.toggle_state == "on" else "on"

    def update_off(self):
        """Paint the off state."""

    def update_on(self):
        """Paint the on state."""
