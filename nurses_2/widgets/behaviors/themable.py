"""
Themable behavior for widgets.
"""
from abc import ABC, abstractmethod

from ...colors import DEFAULT_COLOR_THEME


class Themable(ABC):
    """
    Themable behavior for a widget.

    Themable widgets share a color theme. They must implement :meth:`update_theme`
    which paints the widget with current theme.

    Whenever the running app's theme is changed, `update_theme` will be called
    for all :class:`Themable` widgets.

    Methods
    -------
    update_theme:
        Paint the widget with current theme.
    """

    color_theme = DEFAULT_COLOR_THEME

    def on_add(self):
        super().on_add()
        self.update_theme()

    @abstractmethod
    def update_theme(self):
        """
        Paint the widget with current theme.
        """
