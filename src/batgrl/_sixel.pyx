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
sixel.c.[1]_ This algorithm only requires a single pass over the pixel data; for each
band, for each sixel, each color encountered in that sixel is stored as an "active
color". Afterwards, for each active color, a new color band is created or a previously
created color band for that color is extended so that all color bands of a band are
built up simultaneously.

References
----------
.. [1] `sixel.c <https://github.com/dankamongmen/notcurses/blob/master/src/lib/sixel.c>`_.
"""
from libc.string cimport memset
from libc.stdio cimport sprintf
from libc.stdlib cimport free, malloc

from ._fbuf cimport fbuf, fbuf_printf, fbuf_putn, fbuf_puts

cdef:
    struct BandExtender:
        size_t length, wrote
        int rle
        char rep

    struct SixelMap:
        size_t nbands, ncolors
        char*** bands

    struct ActiveColor:
        int color
        char rep

ctypedef unsigned char uint8


cdef inline size_t sixel_count(size_t h, size_t w):
    return (h + 5) // 6 * w


cdef inline size_t sixel_band_count(size_t h):
    return sixel_count(h, 1)


cdef SixelMap* new_sixel_map(size_t h):
    cdef SixelMap* sixel_map = <SixelMap*>malloc(sizeof(SixelMap))
    if sixel_map is NULL:
        return NULL
    sixel_map.ncolors = 0
    sixel_map.nbands = sixel_band_count(h)
    sixel_map.bands = <char***>malloc(sizeof(char**) * sixel_map.nbands)
    if sixel_map.bands is NULL:
        free(sixel_map)
        return NULL
    return sixel_map


cdef void color_band_free(char** color_band, size_t ncolors):
    cdef size_t i
    for i in range(ncolors):
        if color_band[i] is not NULL:
            free(color_band[i])
    free(color_band)


cdef void sixel_map_free(SixelMap *sixel_map):
    cdef size_t i
    for i in range(sixel_map.nbands):
        if sixel_map.bands[i] is not NULL:
            color_band_free(sixel_map.bands[i], sixel_map.ncolors)
    free(sixel_map.bands)
    free(sixel_map)


cdef inline void write_rle(char* color, size_t *length, ssize_t rle, char rep):
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
    char* color_band, BandExtender *extender, size_t w, size_t x
):
    if color_band is NULL:
        color_band = <char*>malloc(w + 1)
    if color_band is NULL:
        return NULL
    write_rle(color_band, &extender.length, extender.rle, extender.rep + 63)
    cdef ssize_t clear_len = x - (extender.rle + extender.wrote)
    write_rle(color_band, &extender.length, clear_len, 63)
    return color_band


cdef inline int build_sixel_band(
    size_t n,
    SixelMap* sixel_map,
    size_t ncolors,
    uint8[:, ::1] indices,
    uint8[:, :, ::1] texture,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
    size_t *P2,
):
    cdef:
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
        size_t ystart = n * 6, yend = min(ystart + 6, h), x, y, i
        ActiveColor[6] active_colors
        int pixel_color, nactive_colors, color
        BandExtender* extender

    for x in range(w):
        nactive_colors = 0
        for y in range(ystart, yend):
            if not texture[oy + y, ox + x, 3]:
                P2[0] = 1
                continue

            pixel_color = indices[y, x]

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
            color_bands[color] = color_band_extend(
                color_bands[color], extender, w, w - 1
            )
            if color_bands[color] is NULL:
                free(extenders)
                return -1

    free(extenders)
    return 0


cdef ssize_t csixel_ansi(
    fbuf* f,
    uint8[:, ::1] palette,
    uint8[:, ::1] indices,
    uint8[:, :, ::1] texture,
    size_t ncolors,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
):
    cdef:
        size_t n, color, P2 = 0
        bint close_previous
        SixelMap* sixel_map = new_sixel_map(h)
        char** color_bands
        uint8[::1] rgb

    if sixel_map is NULL:
        return -1
    sixel_map.ncolors = ncolors

    for n in range(sixel_map.nbands):
        if build_sixel_band(
            n, sixel_map, ncolors, indices, texture, oy, ox, h, w, &P2
        ) < 0:
            sixel_map_free(sixel_map)
            return -1

    if fbuf_printf(f, "\x1bP;%d;q\"1;1;%d;%d", P2, w, h):
        sixel_map_free(sixel_map)
        return -1

    for color in range(ncolors):
        rgb = palette[color]
        if fbuf_printf(f, "#%d;2;%d;%d;%d", color, rgb[0], rgb[1], rgb[2]):
            sixel_map_free(sixel_map)
            return -1

    for n in range(sixel_map.nbands):
        close_previous = 0
        color_bands = sixel_map.bands[n]
        for color in range(ncolors):
            if color_bands[color] is NULL:
                continue
            if close_previous == 1:
                if fbuf_putn(f, "$", 1):
                    sixel_map_free(sixel_map)
                    return -1
            else:
                close_previous = 1
            if fbuf_printf(f, "#%d", color):
                sixel_map_free(sixel_map)
                return -1
            if fbuf_puts(f, color_bands[color]):
                sixel_map_free(sixel_map)
                return -1
        if fbuf_putn(f, "-", 1):
            sixel_map_free(sixel_map)
            return -1

    sixel_map_free(sixel_map)
    if fbuf_putn(f, "\x1b\\", 3):
        return -1
    return 0
