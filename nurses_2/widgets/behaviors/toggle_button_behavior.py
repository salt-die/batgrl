from enum import Enum
from typing import Hashable
from weakref import ref

from .button_behavior import ButtonBehavior, ButtonState

__all__ = (
    "ButtonState",
    "ToggleState",
    "ToggleButtonBehavior",
)


class ToggleState(str, Enum):
    ON = "on"
    OFF = "off"


class ToggleButtonBehavior(ButtonBehavior):
    """
    Toggle button behavior for widgets. Without a group, toggle button's states switch
    between "on" and "off" when pressed. With a group, only a single button in the group can
    be in the "on" state at a time.

    Parameters
    ----------
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to True allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button. If button is in a group and `allow_no_selection`
        is `False` this value will be ignored if all buttons would be "off".
    """
    __groups = { }

    def __init__(
        self,
        group: None | Hashable=None,
        allow_no_selection: bool=False,
        toggle_state: ToggleState=ToggleState.OFF,
        **kwargs
    ):
        self.group = group
        self.allow_no_selection = allow_no_selection
        self._toggle_state = toggle_state

        if group is not None:
            button_group = ToggleButtonBehavior.__groups.setdefault(group, [ ])

            if not button_group and not allow_no_selection:
                # In the case where a group requires a selection and initial `toggle_state`
                # would be off for all members of a group, this will force the first member
                # of the group to be on, ignoring `toggle_state` completely.
                self._toggle_state = ToggleState.ON

            button_group.append(ref(self))

        super().__init__(**kwargs)

        self.toggle_state = toggle_state

    @property
    def toggle_state(self) -> ToggleState:
        return self._toggle_state

    @toggle_state.setter
    def toggle_state(self, toggle_state: ToggleState):
        toggle_state = ToggleState(toggle_state)  # Error will be raised if toggle_state is invalid.

        if (
            self._toggle_state is toggle_state
            or (
                self.group is not None
                and toggle_state is ToggleState.OFF
                and not self.allow_no_selection
            )
        ):
            return

        self._toggle_state = toggle_state

        if toggle_state is ToggleState.ON:
            self.update_on()
        else:
            self.update_off()

        if self.group is not None and toggle_state is ToggleState.ON:
            button_group = ToggleButtonBehavior.__groups[self.group]
            for item in button_group.copy():
                if (widget := item()) is None:
                    button_group.remove(item)
                elif widget is self:
                    continue
                elif widget.toggle_state is ToggleState.ON:
                    widget._toggle_state = ToggleState.OFF
                    widget.update_off()
                    widget.on_toggle()

        self.on_toggle()

    def _down(self):
        self.toggle_state = ToggleState.OFF if self.toggle_state is ToggleState.ON else ToggleState.ON
        super()._down()

    def update_off(self):
        """
        Paint the off state.
        """

    def update_on(self):
        """
        Paint the on state.
        """

    def on_toggle(self):
        """
        Called when the toggle state changes.
        """
