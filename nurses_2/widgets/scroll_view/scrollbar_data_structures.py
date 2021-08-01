from typing import NamedTuple

from ...colors import Color


class ScrollBarSettings(NamedTuple):
    """
    Settings for ScrollView scrollbars. `indicator_length`
    is doubled for horizontal scrollbars.
    """
    bar_color: Color
    indicator_inactive_color: Color
    indicator_hover_color: Color
    indicator_active_color: Color
    indicator_length: int  # This value doubled for horizontal scrollbars.
