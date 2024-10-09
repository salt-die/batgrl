from typing import Literal

import cython


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef str sixel_ansi(
    unsigned char[:, ::1] palette,
    unsigned char[:, ::1] pixels,
    output_mode: Literal[0, 1]=0,
):
    """
    Generate sixel ansi from a palette and an array of indices into the palette.

    `output_mode` determines the background color of the bitmap. `0` sets the background
    to the terminal's background color (or the 0th color in the sixel palette). `1`
    means background pixels remain at their current color.
    """
    cdef:
        Py_ssize_t h, w, y, x, start_y, end_y, num_bands, band
        unsigned char color, ord_
        set[unsigned char] todo = set(), used = set()
        list[str] ansi = [f"\x1bP;{output_mode};q"]

    for y in range(palette.shape[0]):
        ansi.append(f"#{y};2;{palette[y][0]};{palette[y][1]};{palette[y][2]}")

    h = pixels.shape[0]
    w = pixels.shape[1]
    num_bands = h // 6
    if h % 6 != 0:
        num_bands += 1

    for band in range(num_bands):
        start_y = 6 * band
        end_y = min(start_y + 6, h)
        todo.clear()
        used.clear()
        todo.add(pixels[start_y][0])

        while True:
            color = todo.pop()
            used.add(color)
            ansi.append(f"#{color}")

            for x in range(w):
                ord_ = 63
                for y in range(start_y, end_y):
                    if pixels[y][x] == color:
                        ord_ += 1 << (y - start_y)
                    elif pixels[y][x] not in used:
                        todo.add(pixels[y][x])

                ansi.append(chr(ord_))

            if len(todo) == 0:
                ansi.append("-")
                break

            ansi.append("$")

    ansi.append("\x1b\\")
    return "".join(ansi)
