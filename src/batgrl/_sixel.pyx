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
"$" to return to the start of the band (to output a new color) or "-" to move to the
next band.

For the color data, for each pixel in a sixel with values, ``n``, from 0-5 from top-to-
bottom, if that pixel matches the current color add ``2**n``. The result is a value from
0-63. Add 63 to this result to get a character between "?"-"~". If a character is
repeated, run length encoding, "!rc", may be used instead where ``r`` is the number of
times to repeat ``c``.

For generating sixel ansi, batgrl uses a cython implementation of notcurses'
sixel.c.[1]_ This is a very efficient algorithm that requires only a single pass over
the pixel data. For each band, for each sixel, each color encountered in that sixel is
stored as an "active color". Afterwards, for each active color, a new color band is
created or a previously created color band for that color is extended so that all color
bands of a band are built up simultaneously.

References
----------
.. [1] `sixel.c <https://github.com/dankamongmen/notcurses/blob/master/src/lib/sixel.c>`_.
"""

from libc.string cimport memset
from libc.stdio cimport sprintf
from libc.stdlib cimport malloc, free

cdef:
    struct BandExtender:
        Py_ssize_t length, wrote
        int rle
        char rep

    struct SixelMap:
        Py_ssize_t nbands, ncolors
        char*** bands

    struct ActiveColor:
        int color
        char rep

cdef inline Py_ssize_t sixel_count(Py_ssize_t h, Py_ssize_t w):
    return (h + 5) // 6 * w

cdef inline Py_ssize_t sixel_band_count(Py_ssize_t h):
    return sixel_count(h, 1)

cdef SixelMap* new_sixel_map(unsigned char[:, ::1] pixels):
    cdef SixelMap* sixel_map = <SixelMap*>malloc(sizeof(SixelMap))
    if sixel_map is NULL:
        return NULL
    sixel_map.ncolors = 0
    sixel_map.nbands = sixel_band_count(pixels.shape[0])
    sixel_map.bands = <char***>malloc(sizeof(char**) * sixel_map.nbands)
    if sixel_map.bands is NULL:
        free(sixel_map)
        return NULL
    return sixel_map

cdef void color_band_free(char** color_band, Py_ssize_t ncolors):
    cdef Py_ssize_t i
    for i in range(ncolors):
        if color_band[i] is not NULL:
            free(color_band[i])
    free(color_band)

cdef void sixel_map_free(SixelMap *sixel_map):
    cdef Py_ssize_t i
    for i in range(sixel_map.nbands):
        if sixel_map.bands[i] is not NULL:
            color_band_free(sixel_map.bands[i], sixel_map.ncolors)
    free(sixel_map.bands)
    free(sixel_map)

cdef inline void write_rle(char* color, Py_ssize_t *length, Py_ssize_t rle, char rep):
    if rle > 2:
        length[0] += sprintf(&color[length[0]], "!%d", <int>rle)
    elif rle == 2:
        color[length[0]] = rep
        length[0] += 1
    if rle > 0:
        color[length[0]] = rep
        length[0] += 1
    color[length[0]] = 0

cdef inline char* color_band_extend(
    char* color_band, BandExtender *extender, Py_ssize_t w, Py_ssize_t x
):
    if color_band is NULL:
        color_band = <char*>malloc(w + 1)
    if color_band is NULL:
        return NULL
    write_rle(color_band, &extender.length, extender.rle, extender.rep + 63)
    cdef Py_ssize_t clear_len = x - (extender.rle + extender.wrote)
    write_rle(color_band, &extender.length, clear_len, 63)
    return color_band

cdef inline int build_sixel_band(
    int n,
    SixelMap* sixel_map,
    Py_ssize_t ncolors,
    unsigned char[:, ::1] pixels,
):
    cdef:
        Py_ssize_t h = pixels.shape[0], w = pixels.shape[1]
        size_t band_size = sizeof(char*) * ncolors
        size_t extenders_size = sizeof(BandExtender) * ncolors
        BandExtender *extenders = <BandExtender*>malloc(extenders_size)
        char** color_bands

    if extenders is NULL:
        return -1

    sixel_map.bands[n] = <char**>malloc(band_size)
    color_bands = sixel_map.bands[n]
    if color_bands is NULL:
        free(extenders)
        return -1

    memset(color_bands, 0, band_size)
    memset(extenders, 0, extenders_size)

    cdef:
        Py_ssize_t ystart = n * 6, yend = min(ystart + 6, h), x, y, i
        ActiveColor[6] active_colors
        int pixel_color, nactive_colors, color
        BandExtender* extender

    for x in range(w):
        nactive_colors = 0
        for y in range(ystart, yend):
            pixel_color = pixels[y, x]

            for i in range(nactive_colors):
                if active_colors[i].color == pixel_color:
                    active_colors[i].rep += 1 << (y - ystart)
                    break
            else:
                active_colors[nactive_colors].color = pixel_color
                active_colors[nactive_colors].rep = 1 << (y - ystart)
                nactive_colors += 1

        for i in range(nactive_colors):
            color = active_colors[i].color
            extender = &extenders[color]

            if (
                extender.rep == active_colors[i].rep
                and extender.rle + extender.wrote == x
            ):
                extender.rle += 1
            else:
                color_bands[color] = color_band_extend(
                    color_bands[color], extender, w, x
                )
                if color_bands[color] is NULL:
                    free(extenders)
                    return -1
                extender.rle = 1
                extender.wrote = x
                extender.rep = active_colors[i].rep

    for color in range(ncolors):
        extender = &extenders[color]
        if extender.rle == 0:
            color_bands[color] = NULL
        else:
            color_bands[color] = color_band_extend(color_bands[color], extender, w, x)
            if color_bands[color] is NULL:
                free(extenders)
                return -1

    free(extenders)
    return 0

cpdef str sixel_ansi(unsigned char[:, ::1] palette, unsigned char[:, ::1] pixels):
    """
    Generate sixel ansi from a palette and an array of indices into the palette.

    Parameters
    ----------
    palette : NDArray[np.uint8]
        An array of RGB colors scaled to 0-100 which is indexed by pixels. Palettes
        should not be more than 256 colors.
    pixels : NDArray[np.uint8]
        An index into the palette for each pixel in an image.

    Returns
    -------
    str
        The sixel ansi to generate an image give by palette and pixels.
    """
    cdef:
        Py_ssize_t ncolors = palette.shape[0], n
        int color, close_previous
        SixelMap* sixel_map = new_sixel_map(pixels)
        char** color_bands

    if sixel_map is NULL:
        raise MemoryError
    sixel_map.ncolors = ncolors

    for n in range(sixel_map.nbands):
        # TODO: Can be parallelized.
        if build_sixel_band(n, sixel_map, ncolors, pixels) < 0:
            sixel_map_free(sixel_map)
            raise MemoryError

    # Using transparent (the 1 in "\x1bP;1;q") mode, but all pixels are specified.
    cdef list[str] ansi = ["\x1bP;1;q"]
    for color in range(ncolors):
        ansi.append(
            f"#{color};2;{palette[color][0]};{palette[color][1]};{palette[color][2]}"
        )

    for n in range(sixel_map.nbands):
        close_previous = 0
        color_bands = sixel_map.bands[n]
        for color in range(ncolors):
            if color_bands[color] is NULL:
                continue
            if close_previous == 1:
                ansi.append("$")
            else:
                close_previous = 1
            ansi.append(f"#{color}")
            ansi.append(color_bands[color].decode())
        ansi.append("-")

    sixel_map_free(sixel_map)  # TODO: Return as a python object.
    ansi.append("\x1b\\")
    return "".join(ansi)
