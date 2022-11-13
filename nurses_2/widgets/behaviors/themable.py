"""
Themable behavior for widgets.
"""
from abc import ABC, abstractmethod

from ...colors import DEFAULT_COLOR_THEME


class Themable(ABC):
    """
    Themable widgets share a color theme. They must implement
    :meth:`update_theme` which paints the widget with current theme.

    :meth:`update_theme` should be called at least once in the `__init__`.

    Whenever the running app's theme is changed, all :class:`Themable` widgets'
    theme will be updated.

    Methods
    -------
    update_theme:
        Paint the widget with current theme.
    """
    color_theme = DEFAULT_COLOR_THEME

    @abstractmethod
    def update_theme(self):
        """
        Paint the widget with current theme.
        """
