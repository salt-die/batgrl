"""Themable behavior for gadgets."""

from abc import ABC, abstractmethod

from ...colors import DEFAULT_COLOR_THEME, Color, ColorTheme, Hexcode

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
    get_color()
        Get a color by name from the current color theme.
    update_theme()
        Paint the gadget with current theme.
    """

    color_theme: ColorTheme

    @abstractmethod
    def update_theme(self) -> None:
        """Paint the gadget with current theme."""

    @classmethod
    def get_color(cls, color_name: str) -> Color:
        """Get a color by name from the current color theme."""
        hexcode: Hexcode
        if color_name not in cls.color_theme:
            if color_name not in DEFAULT_COLOR_THEME:
                raise KeyError(f"There is no color {color_name!r}.")
            hexcode = DEFAULT_COLOR_THEME[color_name]
        else:
            hexcode = cls.color_theme[color_name]
        return Color.from_hex(hexcode)

    def on_add(self) -> None:
        """Update theme."""
        super().on_add()
        self.update_theme()
