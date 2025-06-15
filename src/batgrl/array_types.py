"""Type annotations for numpy arrays."""

from typing import Literal

from numpy import dtype, float64, intc, ndarray, str_, uint8, ulong

__all__ = [
    "Cell",
    "Cell0D",
    "Cell1D",
    "Cell2D",
    "Coords",
    "Enum2D",
    "Float1D",
    "Float2D",
    "Int1D",
    "Int2D",
    "RGB_1D",
    "RGB_2D",
    "RGBA_1D",
    "RGBA_2D",
    "RGBM_2D",
    "ULong1D",
    "ULong2D",
    "Unicode1D",
    "Unicode2D",
    "cell_dtype",
]

cell_dtype = dtype(
    [
        ("ord", "uint32"),
        ("style", "u1"),
        ("fg_color", "u1", (3,)),
        ("bg_color", "u1", (3,)),
    ]
)
"""A structured array type that represents a single cell in a terminal."""

Cell = ndarray[tuple[int, ...], cell_dtype]
"""An array of ``cell_dtype``."""

Cell0D = ndarray[tuple[()], cell_dtype]
"""A 0-dimensional array of ``cell_dtype``."""

Cell1D = ndarray[tuple[int], cell_dtype]
"""A 1-dimensional array of ``cell_dtype``."""

Cell2D = ndarray[tuple[int, int], cell_dtype]
"""A 2-dimensional array of ``cell_dtype``."""

Float1D = ndarray[tuple[int], dtype[float64]]
"""A 1-dimensional array of floats."""

Float2D = ndarray[tuple[int, int], dtype[float64]]
"""A 2-dimensional array of floats."""

_Coord = ndarray[tuple[Literal[2]] | tuple[Literal[1], Literal[2]], dtype[float64]]
"""2-dimensional coordinates."""

Coords = ndarray[tuple[int, Literal[2]], dtype[float64]]
"""An array of 2-dimensional coordinates."""

Int1D = ndarray[tuple[int], dtype[intc]]
"""A 1-dimensional array of integers."""

Int2D = ndarray[tuple[int, int], dtype[intc]]
"""A 2-dimensional array of integers."""

ULong1D = ndarray[tuple[int], dtype[ulong]]
"""A 1-dimensional array of unsigned long."""

ULong2D = ndarray[tuple[int, int], dtype[ulong]]
"""A 2-dimensional array of unsigned long."""

RGB_1D = ndarray[tuple[int, Literal[3]], dtype[uint8]]
"""A 1-dimensional array of RGB 24-bit colors."""

RGB_2D = ndarray[tuple[int, int, Literal[3]], dtype[uint8]]
"""A 2-dimensional array of RGB 24-bit colors."""

RGBA_1D = ndarray[tuple[int, Literal[4]], dtype[uint8]]
"""A 1-dimensional array of RGBA 32-bit colors."""

RGBA_2D = ndarray[tuple[int, int, Literal[4]], dtype[uint8]]
"""A 2-dimensional array of RGBA 32-bit colors."""

Unicode1D = ndarray[tuple[int], dtype[str_]]
"""A 1-dimensional array of unicode characters."""

Unicode2D = ndarray[tuple[int, int], dtype[str_]]
"""A 2-dimensional array of unicode characters."""

# Rendering array types:

Enum2D = ndarray[tuple[int, int], dtype[uint8]]
"""A 2-dimensional array of bytes used for enumeration."""

RGBM_2D = ndarray[tuple[int, int, Literal[4]], dtype[uint8]]
"""
A 2-dimensional array of RGB 24-bit colors plus a fourth channel ``M`` where non-zero
values indicate opaque pixels and zeros indicate fully transparent pixels.
"""
