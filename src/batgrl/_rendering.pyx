"""
Notes:

`graphics` is (h, w, cell_h, cell_w, 4)-shaped where (cell_h, cell_w)
is pixel geometry of terminal and last axis is RGBM, where M is a
mask that indicates non-transparent pixels.
"""
import numpy as np
cimport numpy as cnp

from .geometry import Point
from .geometry.regions cimport Band, CRegion, Region

cdef unsigned char GLYPH = 0, GRAPHICS = 1, MIXED = 2


cdef packed struct Cell:
    Py_UCS4 char_
    unsigned char bold
    unsigned char italic
    unsigned char underline
    unsigned char strikethrough
    unsigned char overline
    unsigned char reverse
    unsigned char[3] fg_color
    unsigned char[3] bg_color


cdef inline void composite(
    unsigned char[::1] dst, unsigned char[::1] src, float alpha
):
    cdef float a, b

    a = <float>src[0]
    b = <float>dst[0]
    dst[0] = <unsigned char>((a - b) * alpha + b)
    a = <float>src[1]
    b = <float>dst[1]
    dst[1] = <unsigned char>((a - b) * alpha + b)
    a = <float>src[2]
    b = <float>dst[2]
    dst[2] = <unsigned char>((a - b) * alpha + b)


cdef inline void composite_graphics(
    unsigned char[:, :, ::1] dst,
    Py_ssize_t h,
    Py_ssize_t w,
    unsigned char[::1] src,
    float alpha,
):
    cdef Py_ssize_t y, x

    for y in range(h):
        for x in range(w):
            if dst[y, x, 3]:
                composite(dst[y, x], src, alpha)


cdef inline float average_graphics(
    unsigned char[::1] bg,
    unsigned char [:, :, ::1] graphics,
    Py_ssize_t h,
    Py_ssize_t w,
):
    cdef:
        Py_ssize_t y, x, n = 0
        unsigned int r = 0, g = 0, b = 0

    for y in range(h):
        for x in range(w):
            if graphics[y, x, 3]:
                n += 1
                r += graphics[y, x, 0]
                g += graphics[y, x, 1]
                b += graphics[y, x, 2]

    bg[0] = <unsigned char>(r // n)
    bg[1] = <unsigned char>(g // n)
    bg[2] = <unsigned char>(b // n)
    return <float>n / <float>(h * w)


cdef void pane_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    Point root_pos,
    Region region,
):
    ...


cdef void opaque_text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    Point root_pos,
    Region region,
    Cell[:, ::1] self_canvas,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        int root_y, root_x, abs_y, abs_x
        int src_y
        int i, j, y, y1, y2, x, x1, x2

    root_y, root_x = root_pos
    abs_y, abs_x = band.y1 - root_y, band.walls[0] - root_x

    for i in range(cregion.len):
        band = &cregion.bands[i]
        y1 = band.y1 - root_y
        y2 = band.y2 - root_y
        j = 0
        while j < band.len:
            x1 = band.walls[j] - root_x
            x2 = band.walls[j + 1] - root_x
            for y in range(y1, y2):
                src_y = y - abs_y
                for x in range(x1, x2):
                    root_canvas[y, x] = self_canvas[src_y, x - abs_x]
                    kind[y, x] = GLYPH


cdef void trans_text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    Point root_pos,
    Region region,
    Cell[:, ::1] self_canvas,
    float alpha,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        Cell *dst
        Cell *src
        int root_y, root_x, abs_y, abs_x, src_y
        Py_ssize_t h, w, i, j
        int y, y1, y2, x, x1, x2
        float wgt, nwgt
        cnp.ndarray[unsigned char, ndim=1] rgb = np.empty(3, np.uint8)
        unsigned char cell_kind

    root_y, root_x = root_pos
    abs_y, abs_x = band.y1 - root_y, band.walls[0] - root_x
    h = graphics.shape[2]
    w = graphics.shape[3]

    for i in range(cregion.len):
        band = &cregion.bands[i]
        y1 = band.y1 - root_y
        y2 = band.y2 - root_y
        j = 0
        while j < band.len:
            x1 = band.walls[j] - root_x
            x2 = band.walls[j + 1] - root_x
            for y in range(y1, y2):
                src_y = y - abs_y
                for x in range(x1, x2):
                    dst = &root_canvas[y, x]
                    src = &self_canvas[src_y, x - abs_x]
                    cell_kind = kind[y, x]

                    # FIXME: Consider all whitespace?
                    if src.char_ == " " or src.char_ == "⠀":
                        if cell_kind != GRAPHICS:
                            composite(dst.fg_color, src.bg_color, alpha)
                            composite(dst.bg_color, src.bg_color, alpha)
                        if cell_kind != GLYPH:
                            composite_graphics(
                                graphics[y, x], h, w, src.bg_color, alpha
                            )
                    else:
                        dst.char_ = src.char_
                        dst.bold = src.bold
                        dst.italic = src.italic
                        dst.underline = src.underline
                        dst.strikethrough = src.strikethrough
                        dst.overline = src.overline
                        dst.reverse = src.reverse
                        dst.fg_color = src.fg_color
                        kind[y, x] = GLYPH
                        if cell_kind == GRAPHICS:
                            average_graphics(dst.bg_color, graphics[y, x], h, w)
                        elif cell_kind == MIXED:
                            wgt = average_graphics(rgb, graphics[y, x], h, w)
                            nwgt = 1 - wgt
                            dst.bg_color[0] = <unsigned char>(
                                <float>rgb[0] * wgt + <float>dst.bg_color[0] * nwgt
                            )
                            dst.bg_color[1] = <unsigned char>(
                                <float>rgb[1] * wgt + <float>dst.bg_color[1] * nwgt
                            )
                            dst.bg_color[2] = <unsigned char>(
                                <float>rgb[2] * wgt + <float>dst.bg_color[2] * nwgt
                            )
                        composite(dst.bg_color, src.bg_color, alpha)


cpdef void text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    Point root_pos,
    bool is_transparent,
    Region region,
    unsigned char[:, ::1] self_canvas,
    float alpha,
):
    if is_transparent:
        trans_text_render(
            root_canvas, graphics, kind, root_pos, region, self_canvas, alpha
        )
    else:
        opaque_text_render(root_canvas, graphics, kind, root_pos, region, self_canvas)


cpdef void graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    bool is_transparent,
    Point root_pos,
    Region region,
    unsigned char[:, :, :, :, ::1] self_texture,
):
    if is_transparent:
        pass
    else:
        pass


cpdef void field_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    bool is_transparent,
    Point root_pos,
    Region region,
):
    if is_transparent:
        pass
    else:
        pass


cpdef void graphics_field_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    bool is_transparent,
    Point root_pos,
    Region region,
):
    if is_transparent:
        pass
    else:
        pass


cpdef void terminal_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    bool is_transparent,
    Point root_pos,
    Region region,
):
    if is_transparent:
        pass
    else:
        pass
