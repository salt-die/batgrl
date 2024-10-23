"""
Notes:

`graphics` is (h, w, cell_h, cell_w, 4)-shaped where (cell_h, cell_w)
is pixel geometry of terminal and last axis is RGBM, where M is a
mask that indicates non-transparent pixels.
"""
import numpy as np
cimport numpy as cnp

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
    unsigned char[::1] dst, unsigned char[::1] src, double alpha
):
    cdef double a, b

    a = <double>src[0]
    b = <double>dst[0]
    dst[0] = <unsigned char>((a - b) * alpha + b)
    a = <double>src[1]
    b = <double>dst[1]
    dst[1] = <unsigned char>((a - b) * alpha + b)
    a = <double>src[2]
    b = <double>dst[2]
    dst[2] = <unsigned char>((a - b) * alpha + b)


cdef inline void composite_graphics(
    unsigned char[:, :, ::1] dst,
    Py_ssize_t h,
    Py_ssize_t w,
    unsigned char[::1] src,
    double alpha,
):
    cdef Py_ssize_t y, x

    for y in range(h):
        for x in range(w):
            if dst[y, x, 3]:
                composite(dst[y, x], src, alpha)


cdef inline double average_graphics(
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
    return <double>n / <double>(h * w)


cdef void opaque_pane_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    int root_y,
    int root_x,
    Region region,
    unsigned char[3] bg_color,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        int i, j, y, y1, y2, x, x1, x2
        Cell cell

    cell.char_ = u" "
    cell.bold = False
    cell.italic = False
    cell.underline = False
    cell.strikethrough = False
    cell.overline = False
    cell.reverse = False
    cell.bg_color[:] = bg_color

    for i in range(cregion.len):
        band = &cregion.bands[i]
        y1 = band.y1 - root_y
        y2 = band.y2 - root_y
        j = 0
        while j < band.len:
            x1 = band.walls[j] - root_x
            x2 = band.walls[j + 1] - root_x
            for y in range(y1, y2):
                for x in range(x1, x2):
                    root_canvas[y, x] = cell
                    kind[y, x] = GLYPH


cdef void trans_pane_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    int root_y,
    int root_x,
    Region region,
    unsigned char[::1] bg_color,
    double alpha,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        int i, j, y, y1, y2, x, x1, x2
        Py_ssize_t h, w
        Cell *dst
        unsigned char cell_kind

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
                for x in range(x1, x2):
                    dst = &root_canvas[y, x]
                    cell_kind = kind[y, x]
                    if cell_kind != GRAPHICS:
                        composite(dst.fg_color, bg_color, alpha)
                        composite(dst.bg_color, bg_color, alpha)
                    if cell_kind != GLYPH:
                        composite_graphics(
                            graphics[y, x], h, w, bg_color, alpha
                        )


cpdef void pane_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    tuple[int, int] root_pos,
    bint is_transparent,
    Region region,
    tuple[int, int, int] bg_color,
    double alpha,
):
    cdef:
        unsigned char[3] bg
        int root_y, root_x

    bg[0] = bg_color[0]
    bg[1] = bg_color[1]
    bg[2] = bg_color[2]
    root_y, root_x = root_pos

    if is_transparent:
        trans_pane_render(
            root_canvas, graphics, kind, root_y, root_x, region, bg, alpha
        )
    else:
        opaque_pane_render(root_canvas, graphics, kind, root_y, root_x, region, bg)


cdef void opaque_text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    int root_y,
    int root_x,
    Region region,
    Cell[:, ::1] self_canvas,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        int abs_y, abs_x, src_y
        int i, j, y, y1, y2, x, x1, x2

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
    int root_y,
    int root_x,
    Region region,
    Cell[:, ::1] self_canvas,
    double alpha,
):
    cdef:
        CRegion *cregion = &region.cregion
        Band *band = &cregion.bands[0]
        Cell *dst
        Cell *src
        int abs_y, abs_x, src_y
        Py_ssize_t h, w, i, j
        int y, y1, y2, x, x1, x2
        double wgt, nwgt
        cnp.ndarray[unsigned char, ndim=1] rgb = np.empty(3, np.uint8)
        unsigned char cell_kind

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
                    if src.char_ == u" " or src.char_ == u"⠀":
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
                                <double>rgb[0] * wgt + <double>dst.bg_color[0] * nwgt
                            )
                            dst.bg_color[1] = <unsigned char>(
                                <double>rgb[1] * wgt + <double>dst.bg_color[1] * nwgt
                            )
                            dst.bg_color[2] = <unsigned char>(
                                <double>rgb[2] * wgt + <double>dst.bg_color[2] * nwgt
                            )
                        composite(dst.bg_color, src.bg_color, alpha)


cpdef void text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    tuple[int, int] root_pos,
    bint is_transparent,
    Region region,
    Cell[:, ::1] self_canvas,
    double alpha,
):
    cdef int root_y, root_x
    root_y, root_x = root_pos
    if is_transparent:
        trans_text_render(
            root_canvas, graphics, kind, root_y, root_x, region, self_canvas, alpha
        )
    else:
        opaque_text_render(
            root_canvas, graphics, kind, root_y, root_x, region, self_canvas
        )


# cpdef void graphics_render(
#     Cell[:, ::1] root_canvas,
#     unsigned char[:, :, :, :, ::1] graphics,
#     unsigned char[:, ::1] kind,
#     bint is_transparent,
#     Point root_pos,
#     Region region,
#     unsigned char[:, :, :, :, ::1] self_texture,
# ):
#     if is_transparent:
#         pass
#     else:
#         pass


# cpdef void field_render(
#     Cell[:, ::1] root_canvas,
#     unsigned char[:, :, :, :, ::1] graphics,
#     unsigned char[:, ::1] kind,
#     bint is_transparent,
#     Point root_pos,
#     Region region,
# ):
#     if is_transparent:
#         pass
#     else:
#         pass


# cpdef void graphics_field_render(
#     Cell[:, ::1] root_canvas,
#     unsigned char[:, :, :, :, ::1] graphics,
#     unsigned char[:, ::1] kind,
#     bint is_transparent,
#     Point root_pos,
#     Region region,
# ):
#     if is_transparent:
#         pass
#     else:
#         pass


# cpdef void terminal_render(
#     Cell[:, ::1] root_canvas,
#     unsigned char[:, :, :, :, ::1] graphics,
#     unsigned char[:, ::1] kind,
#     bint is_transparent,
#     Point root_pos,
#     Region region,
# ):
#     if is_transparent:
#         pass
#     else:
#         pass
