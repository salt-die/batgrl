"""Toggle button behavior for a gadget."""
from collections.abc import Hashable
from enum import Enum
from weakref import WeakValueDictionary

from .button_behavior import ButtonBehavior, ButtonState

__all__ = ["ButtonState", "ToggleState", "ToggleButtonBehavior"]


class ToggleState(str, Enum):
    """
    Toggle button states.

    :class:`ToggleState` is one of "on", "off".
    """

    ON = "on"
    OFF = "off"


class ToggleButtonBehavior(ButtonBehavior):
    """
    Toggle button behavior for gadgets.

    Without a group, toggle button's states switch between on and off when pressed.
    With a group, only a single button in the group can be in the "on" state at a time.

    Parameters
    ----------
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.

    Attributes
    ----------
    group : None | Hashable
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool
        If true and button is in a group, every button can be in the off state.
    toggle_state : ToggleState
        Toggle state of button.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of normal, hover or down.

    Methods
    -------
    update_off():
        Paint the off state.
    update_on():
        Paint the on state.
    on_toggle():
        Update gadget on toggle state change.
    update_normal():
        Paint the normal state.
    update_hover():
        Paint the hover state.
    update_down():
        Paint the down state.
    on_release():
        Triggered when a button is released.
    """

    _toggle_groups = WeakValueDictionary()

    def __init__(
        self,
        group: None | Hashable = None,
        allow_no_selection: bool = False,
        toggle_state: ToggleState = ToggleState.OFF,
        always_release: bool = False,
        **kwargs,
    ):
        self.group = group
        self.allow_no_selection = allow_no_selection
        self._toggle_state = ToggleState.OFF

        if (
            group is not None
            and toggle_state is ToggleState.OFF
            and ToggleButtonBehavior._toggle_groups.get(group) is None
            and not allow_no_selection
        ):
            # If a group requires a selection, the first member of the group
            # will be forced on and initial toggle state will be ignored.
            toggle_state = ToggleState.ON
            ToggleButtonBehavior._toggle_groups[group] = self

        super().__init__(always_release=always_release, **kwargs)

        self.toggle_state = toggle_state

    @property
    def toggle_state(self) -> ToggleState:
        """
        Initial toggle state of button.

        If button is in a group and :attr:`allow_no_selection` is false this value will
        be ignored if all buttons would be off.
        """
        return self._toggle_state

    @toggle_state.setter
    def toggle_state(self, toggle_state: ToggleState):
        toggle_state = ToggleState(toggle_state)

        if self._toggle_state is toggle_state or (
            self.group is not None
            and toggle_state is ToggleState.OFF
            and not self.allow_no_selection
        ):
            return

        self._toggle_state = toggle_state

        if toggle_state is ToggleState.ON:
            if (
                self.group is not None
                and (last_on := ToggleButtonBehavior._toggle_groups.get(self.group))
                is not None
                and last_on
                is not self  # last condition is false if initialized in the "on" state
            ):
                last_on._toggle_state = ToggleState.OFF
                last_on.update_off()
                last_on.on_toggle()
            ToggleButtonBehavior._toggle_groups[self.group] = self
            self.update_on()
        else:
            if (
                self.group is not None
                and ToggleButtonBehavior._toggle_groups.get(self.group) is self
            ):
                del ToggleButtonBehavior._toggle_groups[self.group]
            self.update_off()

        self.on_toggle()

    def _down(self):
        self.toggle_state = (
            ToggleState.OFF if self.toggle_state is ToggleState.ON else ToggleState.ON
        )
        super()._down()

    def update_off(self):
        """Paint the off state."""

    def update_on(self):
        """Paint the on state."""

    def on_toggle(self):
        """Update gadget on toggle state change."""
