"""Themable behavior for gadgets."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import NamedTuple

from ...colors import DEFAULT_COLOR_THEME, Color, ColorTheme

__all__ = ["Themable"]


class _ColorPair(NamedTuple):
    """A foreground and background pair of colors."""

    fg: Color
    """The foreground color."""
    bg: Color
    """The background color."""


@dataclass
class _ColorTheme:
    def __init__(self, color_theme: ColorTheme):
        for field in fields(self):
            name = field.name
            info = color_theme.get(name, DEFAULT_COLOR_THEME[name])

            if isinstance(info, str):
                color = Color.from_hex(info)
            else:
                color = _ColorPair(
                    Color.from_hex(info["fg"]), Color.from_hex(info["bg"])
                )
            setattr(self, name, color)

    primary: _ColorPair
    """The primary color pair."""
    text_pad_line_highlight: _ColorPair
    """Text pad line highlight color pair."""
    text_pad_selection_highlight: _ColorPair
    """Text pad selection color pair."""
    textbox_primary: _ColorPair
    """Text pad primary color pair."""
    textbox_selection_highlight: _ColorPair
    """Textbox selection color pair."""
    textbox_placeholder: _ColorPair
    """Textbox placeholder color pair."""
    button_normal: _ColorPair
    """Button normal color pair."""
    button_hover: _ColorPair
    """Button hover color pair."""
    button_press: _ColorPair
    """Button press color pair."""
    button_disallowed: _ColorPair
    """Button disallowed color pair."""
    menu_item_hover: _ColorPair
    """Menu item hover color pair."""
    menu_item_selected: _ColorPair
    """Menu item selected color pair."""
    menu_item_disallowed: _ColorPair
    """Menu item disallowed color pair."""
    titlebar_normal: _ColorPair
    """Titlebar normal color pair."""
    titlebar_inactive: _ColorPair
    """Titlebar inactive color pair."""
    data_table_sort_indicator: _ColorPair
    """Data table sort indicator color pair."""
    data_table_hover: _ColorPair
    """Data table hover color pair."""
    data_table_stripe: _ColorPair
    """Data table stripe color pair."""
    data_table_stripe_hover: _ColorPair
    """Data table stripe hover color pair."""
    data_table_selected: _ColorPair
    """Data table selected color pair."""
    data_table_selected_hover: _ColorPair
    """Data table selected hover color pair."""
    progress_bar: _ColorPair
    """Progress bar color pair."""
    markdown_link: _ColorPair
    """Markdown link color pair."""
    markdown_link_hover: _ColorPair
    """Markdown link hover color pair."""
    markdown_inline_code: _ColorPair
    """Markdown inline code color pair."""
    markdown_quote: _ColorPair
    """Markdown quote color pair."""
    markdown_title: _ColorPair
    """Markdown title color pair."""
    markdown_image: _ColorPair
    """Markdown image color pair."""
    markdown_block_code_background: Color
    """Markdown block code background color."""
    markdown_quote_block_code_background: Color
    """Markdown quote block code background color."""
    markdown_header_background: Color
    """Markdown header background color."""
    scroll_view_scrollbar: Color
    """Scroll view scrollbar color."""
    scroll_view_indicator_normal: Color
    """Scroll view indicator normal color."""
    scroll_view_indicator_hover: Color
    """Scroll view indicator hover color."""
    scroll_view_indicator_press: Color
    """Scroll view indicator press color."""
    window_border_normal: Color
    """Window border normal color."""
    window_border_inactive: Color
    """Window border inactive color."""


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

    color_theme: _ColorTheme

    @classmethod
    def set_theme(cls, color_theme: ColorTheme):
        """Set color theme."""
        cls.color_theme = _ColorTheme(color_theme)

    def on_add(self):
        """Update theme."""
        super().on_add()
        self.update_theme()

    @abstractmethod
    def update_theme(self):
        """Paint the gadget with current theme."""
