"""
Cython implementation of notcurses' sixel.c (See:
<https://github.com/dankamongmen/notcurses/blob/master/src/lib/sixel.c>).
"""
from typing import Literal

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
        char*** color_bands

    struct ActiveColor:
        int color
        char rep

cdef inline Py_ssize_t sixel_count(Py_ssize_t h, Py_ssize_t w):
    return (h + 5) // 6 * w

cdef inline Py_ssize_t sixel_band_count(Py_ssize_t h):
    return sixel_count(h, 1)

cdef SixelMap* new_sixel_map(unsigned char[:, ::1] pixels):
    cdef SixelMap* result = <SixelMap*>malloc(sizeof(SixelMap))
    if result is NULL:
        return NULL
    result.ncolors = 0
    result.nbands = sixel_band_count(pixels.shape[0])
    result.color_bands = <char***>malloc(sizeof(char**) * result.nbands)
    if result.color_bands is NULL:
        free(result)
        return NULL
    return result

cdef void color_band_free(char** color_band, Py_ssize_t ncolors):
    cdef Py_ssize_t i
    for i in range(ncolors):
        if color_band[i] is not NULL:
            free(color_band[i])
    free(color_band)

cdef void sixel_map_free(SixelMap *sixel_map):
    cdef Py_ssize_t i
    for i in range(sixel_map.nbands):
        if sixel_map.color_bands[i] is not NULL:
            color_band_free(sixel_map.color_bands[i], sixel_map.ncolors)
    free(sixel_map.color_bands)
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

cdef inline char* sixel_band_extend(
    char* color, BandExtender *extender, Py_ssize_t w, Py_ssize_t x
):
    if color is NULL:
        color = <char*>malloc(w + 1)
    if color is NULL:
        return NULL
    write_rle(color, &extender.length, extender.rle, extender.rep + 63)
    cdef Py_ssize_t clear_len = x - (extender.rle + extender.wrote)
    write_rle(color, &extender.length, clear_len, 63)
    return color

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

    if extenders is NULL:
        return -1

    sixel_map.color_bands[n] = <char**>malloc(band_size)
    if sixel_map.color_bands[n] is NULL:
        free(extenders)
        return -1

    memset(sixel_map.color_bands[n], 0, band_size)
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
                sixel_map.color_bands[n][color] = sixel_band_extend(
                    sixel_map.color_bands[n][color], extender, w, x
                )
                if sixel_map.color_bands[n][color] is NULL:
                    free(extenders)
                    return -1
                extender.rle = 1
                extender.wrote = x
                extender.rep = active_colors[i].rep

    for color in range(ncolors):
        extender = &extenders[color]
        if extender.rle == 0:
            sixel_map.color_bands[n][color] = NULL
        else:
            sixel_map.color_bands[n][color] = sixel_band_extend(
                sixel_map.color_bands[n][color], extender, w, x
            )
            if sixel_map.color_bands[n][color] is NULL:
                free(extenders)
                return -1

    free(extenders)
    return 0

cpdef str sixel_ansi(
    unsigned char[:, ::1] palette,
    unsigned char[:, ::1] pixels,
    output_mode: Literal[0, 1]=0,
):
    """
    Generate sixel ansi from a palette and an array of indices into the palette.

    `output_mode` determines how unspecified pixels are handled (i.e., the background
    color of the bitmap). `0` sets the background to the terminal's background color (or
    the 0th color in the sixel palette). `1` leaves unspecified pixels untouched (i.e.,
    "transparent" mode).
    """
    cdef:
        Py_ssize_t ncolors = palette.shape[0], n
        int color, close_previous
        SixelMap* sixel_map = new_sixel_map(pixels)

    if sixel_map is NULL:
        raise MemoryError
    sixel_map.ncolors = ncolors

    for n in range(sixel_map.nbands):
        # TODO: Can be parallelized.
        if build_sixel_band(n, sixel_map, ncolors, pixels) < 0:
            sixel_map_free(sixel_map)
            raise MemoryError

    cdef list[str] lines = [f"\x1bP;{output_mode};q"]
    for color in range(ncolors):
        lines.append(
            f"#{color};2;{palette[color][0]};{palette[color][1]};{palette[color][2]}"
        )

    for n in range(sixel_map.nbands):
        close_previous = 0
        color_band = sixel_map.color_bands[n]
        assert color_band is not NULL
        for color in range(ncolors):
            if color_band[color] is NULL:
                continue
            if close_previous == 1:
                lines.append("$")
            else:
                close_previous = 1
            lines.append(f"#{color}")
            lines.append(color_band[color].decode())
        lines.append("-")

    sixel_map_free(sixel_map)  # TODO: Return as a python object.
    lines.append("\x1b\\")
    return "".join(lines)
