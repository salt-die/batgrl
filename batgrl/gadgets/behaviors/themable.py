"""Themable behavior for gadgets."""
from abc import ABC, abstractmethod
from typing import NamedTuple

from ...colors import AColor, Color, ColorTheme

__all__ = ["Themable"]


class _ColorPair(NamedTuple):
    fg: Color
    bg: Color


def _build_color_theme(color_theme: ColorTheme):
    """
    Convert a ColorTheme into a class with attribute names given by the color theme's
    keys.

    Attribute values are colors created from ColorTheme hexcodes.
    """

    def color(hexcode):
        if isinstance(hexcode, dict):
            return _ColorPair(
                Color.from_hex(hexcode["fg"]), Color.from_hex(hexcode["bg"])
            )
        if len(hexcode) < 8:
            return Color.from_hex(hexcode)
        return AColor.from_hex(hexcode)

    return type("_ColorTheme", (), {k: color(v) for k, v in color_theme.items()})


class Themable(ABC):
    """
    Themable behavior for a gadget.

    Themable gadgets share a color theme. They must implement :meth:`update_theme`
    which paints the gadget with current theme.

    Whenever the running app's theme is changed, `update_theme` will be called
    for all :class:`Themable` gadgets.

    Methods
    -------
    update_theme()
        Paint the gadget with current theme.
    """

    @classmethod
    def set_theme(cls, color_theme: ColorTheme):
        """Set color theme."""
        cls.color_theme = _build_color_theme(color_theme)

    def on_add(self):
        """Update theme."""
        super().on_add()
        self.update_theme()

    @abstractmethod
    def update_theme(self):
        """Paint the gadget with current theme."""
