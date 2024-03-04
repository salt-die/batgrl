"""Color data structures."""
import re
from typing import NamedTuple, TypedDict

__all__ = ["AColor", "Color", "ColorTheme"]


def validate_hexcode(hexcode: str) -> bool:
    return bool(re.match(r"^#?[0-9a-fA-F]{6}$", hexcode))


def validate_ahexcode(ahexcode: str) -> bool:
    return bool(re.match(r"^#?[0-9a-fA-F]{8}$", ahexcode))


def _to_hex(channel):
    return hex(channel)[2:].zfill(2)


class Color(NamedTuple):
    """
    A 24-bit color.

    Parameters
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.

    Attributes
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.

    Methods
    -------
    from_hex(hexcode)
        Create a :class:`Color` from a hex code.
    to_hex()
        Return color's hexcode.
    count(value)
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807)
        Return first index of value.
    """

    red: int
    green: int
    blue: int

    @classmethod
    def from_hex(cls, hexcode: str) -> "Color":
        """
        Create a :class:`Color` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.

        Returns
        -------
        Color
            A new color.
        """
        if not validate_hexcode(hexcode):
            raise ValueError(f"{hexcode!r} is not a valid hex code.")

        digits = hexcode.removeprefix("#")
        return cls(int(digits[:2], 16), int(digits[2:4], 16), int(digits[4:], 16))

    def to_hex(self) -> str:
        """
        Return color's hexcode.

        Returns
        -------
        str
            The hexcode of the color.
        """
        hexcode = "".join(_to_hex(channel) for channel in self)
        return f"#{hexcode}"


class AColor(NamedTuple):
    """
    A 32-bit color with an alpha channel.

    Parameters
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.
    alpha : int
        The alpha component.

    Attributes
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.
    alpha : int
        The alpha component.

    Methods
    -------
    from_hex(hexcode)
        Create an :class:`AColor` from a hex code.
    to_hex()
        Return color's hexcode.
    count(value)
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807)
        Return first index of value.
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    @classmethod
    def from_hex(cls, hexcode: str) -> "AColor":
        """
        Create an :class:`AColor` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.

        Returns
        -------
        AColor
            A new color with alpha.
        """
        if not validate_ahexcode(hexcode) and not validate_hexcode(hexcode):
            raise ValueError(f"{hexcode!r} is not a valid hex code")

        digits = hexcode.removeprefix("#")
        return cls(
            int(digits[:2], 16),
            int(digits[2:4], 16),
            int(digits[4:6], 16),
            int(digits[6:] or "ff", 16),
        )

    def to_hex(self) -> str:
        """
        Return color's hexcode.

        Returns
        -------
        str
            The hexcode of the color.
        """
        hexcode = "".join(_to_hex(channel) for channel in self)
        return f"#{hexcode}"


class ColorPair(TypedDict):
    """
    A foreground and background hexcode.

    Methods
    -------
    clear()
        Remove all items from the dictionary.
    copy()
        Return a shallow copy of the dictionary.
    fromkeys(iterable, value=None)
        Create a new dictionary with keys from iterable and values set to value.
    get(key, default=None)
        Return the value for key if key is in the dictionary, else default. If default
        is not given, it defaults to None, so that this method never raises a KeyError.
    items()
        Return a new view of the dictionary’s items ((key, value) pairs). See the
        documentation of view objects.
    keys()
        Return a new view of the dictionary’s keys. See the documentation of view
        objects.
    pop(...)
        If key is in the dictionary, remove it and return its value, else return
        default. If default is not given and key is not in the dictionary, a KeyError is
        raised.
    popitem()
        Remove and return a (key, value) pair from the dictionary. Pairs are returned in
        LIFO order. popitem() is useful to destructively iterate over a dictionary, as
        often used in set algorithms. If the dictionary is empty, calling popitem()
        raises a KeyError.
    setdefault(key, default=None)
        If key is in the dictionary, return its value. If not, insert key with a value
        of default and return default. default defaults to None.
    update(...)
        Update the dictionary with the key/value pairs from other, overwriting existing
        keys. Return None.
    values()
        Return a new view of the dictionary’s values. See the documentation of view
        objects.
    """

    fg: str
    bg: str


class ColorTheme(TypedDict, total=False):
    """
    Colors for themable gadgets.

    Methods
    -------
    clear()
        Remove all items from the dictionary.
    copy()
        Return a shallow copy of the dictionary.
    fromkeys(iterable, value=None)
        Create a new dictionary with keys from iterable and values set to value.
    get(key, default=None)
        Return the value for key if key is in the dictionary, else default. If default
        is not given, it defaults to None, so that this method never raises a KeyError.
    items()
        Return a new view of the dictionary’s items ((key, value) pairs). See the
        documentation of view objects.
    keys()
        Return a new view of the dictionary’s keys. See the documentation of view
        objects.
    pop(...)
        If key is in the dictionary, remove it and return its value, else return
        default. If default is not given and key is not in the dictionary, a KeyError is
        raised.
    popitem()
        Remove and return a (key, value) pair from the dictionary. Pairs are returned in
        LIFO order. popitem() is useful to destructively iterate over a dictionary, as
        often used in set algorithms. If the dictionary is empty, calling popitem()
        raises a KeyError.
    setdefault(key, default=None)
        If key is in the dictionary, return its value. If not, insert key with a value
        of default and return default. default defaults to None.
    update(...)
        Update the dictionary with the key/value pairs from other, overwriting existing
        keys. Return None.
    values()
        Return a new view of the dictionary’s values. See the documentation of view
        objects.
    """

    primary: ColorPair
    text_pad_line_highlight: ColorPair
    text_pad_selection_highlight: ColorPair
    textbox_primary: ColorPair
    textbox_selection_highlight: ColorPair
    textbox_placeholder: ColorPair
    button_normal: ColorPair
    button_hover: ColorPair
    button_press: ColorPair
    button_disallowed: ColorPair
    menu_item_hover: ColorPair
    menu_item_selected: ColorPair
    menu_item_disallowed: ColorPair
    titlebar_normal: ColorPair
    titlebar_inactive: ColorPair
    data_table_sort_indicator: ColorPair
    data_table_hover: ColorPair
    data_table_stripe: ColorPair
    data_table_stripe_hover: ColorPair
    data_table_selected: ColorPair
    data_table_selected_hover: ColorPair
    progress_bar: ColorPair
    markdown_link: ColorPair
    markdown_link_hover: ColorPair
    markdown_inline_code: ColorPair
    markdown_quote: ColorPair
    markdown_title: ColorPair
    markdown_image: ColorPair
    markdown_block_code_background: str
    markdown_quote_block_code_background: str
    markdown_header_background: str
    scroll_view_scrollbar: str
    scroll_view_indicator_normal: str
    scroll_view_indicator_hover: str
    scroll_view_indicator_press: str
    window_border_normal: str
    window_border_inactive: str
