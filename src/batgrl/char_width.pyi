"""Functions for measuring column width of characters."""

__all__ = ["char_width", "str_width"]

def char_width(char: str) -> int:
    """
    Return the column width of a character.

    If the length of ``char`` is greater than 1, only the column width of the first
    character is returned. If the length of ``char`` is 0, ``0`` is returned.

    Parameters
    ----------
    char : str
        A single character.

    Returns
    -------
    int
        The character column width.
    """

def str_width(chars: str) -> int:
    """
    Return the total column width of a string.

    Parameters
    ----------
    chars : str
        A string.

    Returns
    -------
    int
        The total column width of the string.
    """
