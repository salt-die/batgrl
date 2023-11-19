"""Themable behavior for gadgets."""
from abc import ABC, abstractmethod

from ...colors import DEFAULT_COLOR_THEME

__all__ = ["Themable"]


class Themable(ABC):
    """
    Themable behavior for a gadget.

    Themable gadgets share a color theme. They must implement :meth:`update_theme`
    which paints the gadget with current theme.

    Whenever the running app's theme is changed, `update_theme` will be called
    for all :class:`Themable` gadgets.

    Methods
    -------
    update_theme():
        Paint the gadget with current theme.
    """

    color_theme = DEFAULT_COLOR_THEME

    def on_add(self):
        """Update theme."""
        super().on_add()
        self.update_theme()

    @abstractmethod
    def update_theme(self):
        """Paint the gadget with current theme."""
