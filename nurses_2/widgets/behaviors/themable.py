"""
Themable behavior for widgets.
"""
from abc import ABC, abstractmethod

from ...colors import DEFAULT_COLOR_THEME


class Themable(ABC):
    """
    Themable widgets share a color theme. They must implement a
    single method, `update_theme` which repaints the widget
    whenever the color theme changes.

    Methods
    -------
    update_theme
        Repaint the widget with a new theme. This should be called at
        least once when a widget is initialized.
    """
    color_theme = DEFAULT_COLOR_THEME

    @abstractmethod
    def update_theme(self):
        """
        Repaint the widget with a new theme.
        """
