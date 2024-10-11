"""
Generate sixel ansi from a palette and an array of indices into the palette.

Notes
-----
The sixel format involves first creating a palette (generally limited to 256 colors) for
the succeeding band data. Each color in the palette uses the ansi "#i;m;r;g;b" where
``i`` is the color register and ``m`` is the "mode" (``1`` for hsl or ``2`` for rgb).
For mode ``2`` (the only mode batgrl uses), the remaining three parameters ``r``, ``g``,
``b`` are the red, green, and blue color components of the color scaled from 0-100
inclusive.

The remaining data for an image is split into 6-pixel high bands. A six-pixel tall
column in that band is called a sixel. For each band, for every color in the band output
"#i" with ``i`` being a color in the palette followed by color data finally ending with
"$" to return to the start of the band (to output a new color). After all colors in the
band are done, output "-".

For the color data, for each pixel in a sixel with values, ``n``, from 0-5 from top-to-
bottom, if that pixel matches the current color add ``2**n``. The result is a value from
0-63. Add 63 to this result to get a character between "?"-"~". If a character is
repeated, run length encoding, "!rc", may be used instead where ``r`` is the number of
times to repeat ``c``.

For generating sixel ansi, batgrl uses a cython implementation of notcurses'
sixel.c.[1]_ This is a very efficient algorithm that requires only a single pass over
the pixel data. First, the pixels are split into 6-pixel tall bands. For each band, for
each sixel, each color encountered in that sixel is stored as an "active color".
Afterwards, for each active color, a new color band is created or a previously created
color band for that color is extended so that all color bands of a band are built up
simlutaneously.

References
----------
.. [1] `sixel.c <https://github.com/dankamongmen/notcurses/blob/master/src/lib/sixel.c>`_.
"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray

def sixel_ansi(
    palette: NDArray[np.uint8],
    pixels: NDArray[np.uint8],
    output_mode: Literal[0, 1] = 0,
) -> str:
    """
    Generate sixel ansi from a palette and an array of indices into the palette.

    `output_mode` determines how unspecified pixels are handled (i.e., the background
    color of the bitmap). `0` sets the background to the terminal's background color (or
    the 0th color in the sixel palette). `1` leaves unspecified pixels untouched (i.e.,
    "transparent" mode).
    """
