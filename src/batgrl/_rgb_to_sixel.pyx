from typing import Literal

cpdef str to_sixel_ansi(
    unsigned char[:, ::1] palette,
    unsigned char[:, ::1] pixels,
    output_mode: Literal[0, 1]=0,
):
    """
    Generate sixel ansi from a rect of an rgb texture.

    `output_mode` determines the background color of the bitmap. `0` sets the background
    to the terminal's background color (or the 0th color in the sixel palette). `1`
    means background pixels remain at their current color.
    """
    cdef Py_ssize_t band, y, x, num_bands, h, w, ord_, start_y, end_y, i
    cdef unsigned char color
    cdef set[unsigned char] todo = set()
    cdef set[unsigned char] used = set()
    cdef list[str] ansi = [f"\x1bP;{output_mode};q"]

    for y in range(palette.shape[0]):
        ansi.append(f"#{y};2;{palette[y][0]};{palette[y][1]};{palette[y][2]}")

    h = pixels.shape[0]
    w = pixels.shape[1]
    num_bands = h // 6
    if h % 6 != 0:
        num_bands += 1

    for band in range(num_bands):
        todo.clear()
        used.clear()
        start_y = 6 * band
        end_y = min(start_y + 6, h)
        x = 0
        todo.add(pixels[start_y][x])

        while True:
            color = todo.pop()
            used.add(color)
            ansi.append(f"#{color}")

            for x in range(w):
                i = 1
                ord_ = 63

                for y in range(start_y, end_y):
                    if pixels[y][x] == color:
                        ord_ += i
                    elif pixels[y][x] not in used:
                        todo.add(pixels[y][x])
                    i <<= 1

                ansi.append(chr(ord_))

            if len(todo) == 0:
                ansi.append("-")
                break

            ansi.append("$")

    ansi.append("\x1b\\")
    return "".join(ansi)
