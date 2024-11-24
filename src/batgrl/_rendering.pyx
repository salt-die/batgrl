"""
Notes:

`graphics` is (h, w, cell_h, cell_w, 4)-shaped where (cell_h, cell_w)
is pixel geometry of terminal and last axis is RGBM, where M is a
mask that indicates non-transparent pixels.
"""
import numpy as np
cimport numpy as cnp

from .geometry.regions cimport Band, CRegion, Region

cdef unsigned char GLYPH = 0, SIXEL = 1, MIXED = 2


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


cdef inline unsigned int rgba_eq(unsigned char[::1] a, unsigned char[::1] b):
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] == b[3]


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


cdef inline double average_graphics(
    unsigned char[3] bg,
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
    const int root_y,
    const int root_x,
    unsigned char[::1] bg_color,
    CRegion *cregion,
):
    cdef:
        Band *band
        int i, j, y, y1, y2, x, x1, x2
        Cell cell

    cell.char_ = u" "
    cell.bold = False
    cell.italic = False
    cell.underline = False
    cell.strikethrough = False
    cell.overline = False
    cell.reverse = False
    cell.bg_color[0] = bg_color[0]
    cell.bg_color[1] = bg_color[1]
    cell.bg_color[2] = bg_color[2]

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
            j += 2


cdef void trans_pane_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    unsigned char[::1] bg_color,
    double alpha,
    CRegion *cregion,
):
    cdef:
        Band *band
        int i, j, y, y1, y2, x, x1, x2
        Py_ssize_t h, w, gy, gx
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
                    if cell_kind != SIXEL:
                        composite(dst.fg_color, bg_color, alpha)
                        composite(dst.bg_color, bg_color, alpha)
                    if cell_kind != GLYPH:
                        for gy in range(h):
                            for gx in range(w):
                                if graphics[y, x, gy, gx, 3]:
                                    composite(graphics[y, x, gy, gx], bg_color, alpha)
            j += 2


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
        CRegion *cregion = &region.cregion
        cnp.ndarray[unsigned char, ndim=1] bg = np.array(bg_color, np.uint8)
        int root_y, root_x

    root_y, root_x = root_pos

    if is_transparent:
        trans_pane_render(
            root_canvas, graphics, kind, root_y, root_x, bg, alpha, cregion
        )
    else:
        opaque_pane_render(root_canvas, root_y, root_x, bg, cregion)


cdef void opaque_text_render(
    Cell[:, ::1] root_canvas,
    const int root_y,
    const int root_x,
    Cell[:, ::1] self_canvas,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Py_ssize_t i, j
        int abs_y, abs_x, src_y
        int y, y1, y2, x, x1, x2

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
            j += 2


cdef void trans_text_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    Cell[:, ::1] self_canvas,
    double alpha,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Cell *dst
        Cell *src
        int abs_y, abs_x, src_y
        Py_ssize_t h, w, i, j, gy, gx
        int y, y1, y2, x, x1, x2
        double wgt, nwgt
        cnp.ndarray[unsigned char, ndim=1] rgb = np.empty(3, np.uint8)

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
                    # FIXME: Consider all whitespace?
                    if src.char_ == u" " or src.char_ == u"⠀":
                        if kind[y, x] != SIXEL:
                            composite(dst.fg_color, src.bg_color, alpha)
                            composite(dst.bg_color, src.bg_color, alpha)
                        if kind[y, x] != GLYPH:
                            for gy in range(h):
                                for gx in range(w):
                                    if graphics[y, x, gy, gx, 3]:
                                        composite(
                                            graphics[y, x, gy, gx], src.bg_color, alpha
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
                        if kind[y, x] == SIXEL:
                            average_graphics(dst.bg_color, graphics[y, x], h, w)
                        elif kind[y, x] == MIXED:
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
                        kind[y, x] = GLYPH
                        composite(dst.bg_color, src.bg_color, alpha)
            j += 2


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
    cdef:
        CRegion *cregion = &region.cregion
        int root_y, root_x

    root_y, root_x = root_pos

    if is_transparent:
        trans_text_render(
            root_canvas, graphics, kind, root_y, root_x, self_canvas, alpha, cregion
        )
    else:
        opaque_text_render(root_canvas, root_y, root_x, self_canvas, cregion)


cdef opaque_half_graphics_render(
    Cell[:, ::1] root_canvas,
    const int root_y,
    const int root_x,
    unsigned char[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Cell *dst
        Py_ssize_t i, j
        int abs_y, abs_x, src_y, src_x
        int y, y1, y2, x, x1, x2

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
                src_y = 2 * (y - abs_y)
                for x in range(x1, x2):
                    src_x = x - abs_x
                    dst = &root_canvas[y, x]
                    dst.char_ = u"▀"
                    dst.bold = False
                    dst.italic = False
                    dst.underline = False
                    dst.strikethrough = False
                    dst.overline = False
                    dst.reverse = False
                    dst.fg_color[0] = self_texture[src_y, src_x, 0]
                    dst.fg_color[1] = self_texture[src_y, src_x, 1]
                    dst.fg_color[2] = self_texture[src_y, src_x, 2]
                    dst.bg_color[0] = self_texture[src_y + 1, src_x, 0]
                    dst.bg_color[1] = self_texture[src_y + 1, src_x, 1]
                    dst.bg_color[2] = self_texture[src_y + 1, src_x, 2]
            j += 2


cdef trans_half_graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    unsigned char[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Cell *dst
        Py_ssize_t h, w, i, j, gy, gx
        int abs_y, abs_x, src_y, src_x
        int y, y1, y2, x, x1, x2
        double wgt, nwgt, a
        unsigned char[:, :, ::1] sixel
        unsigned char[::1] rgba
        cnp.ndarray[unsigned char, ndim=1] rgb = np.empty(3, np.uint8)

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
                src_y = 2 * (y - abs_y)
                for x in range(x1, x2):
                    src_x = x - abs_x
                    if rgba_eq(
                        self_texture[src_y, src_x], self_texture[src_y + 1, src_x]
                    ):
                        dst = &root_canvas[y, x]
                        rgba = self_texture[src_y, src_x]
                        a = alpha * <double>rgba[3] / 255
                        if kind[y, x] != SIXEL:
                           composite(dst.fg_color, rgba, a)
                           composite(dst.bg_color, rgba, a)
                        if kind[y, x] != GLYPH:
                           for gy in range(h):
                              for gx in range(w):
                                  if graphics[y, x, gy, gx, 3]:
                                      composite(graphics[y, x, gy, gx], rgba, a)
                    elif kind[y, x] == SIXEL:
                        sixel = graphics[y, x]
                        rgba = self_texture[src_y, src_x]
                        a = alpha * <double>rgba[3] / 255
                        for gy in range(h // 2):
                            for gx in range(w):
                                sixel[gy, gx, 3] = 1
                                composite(sixel[gy, gx], rgba, a)
                        rgba = self_texture[src_y + 1, src_x]
                        a = alpha * <double>rgba[3] / 255
                        for gy in range(h // 2, h):
                            for gx in range(w):
                                sixel[gy, gx, 3] = 1
                                composite(sixel[gy, gx], rgba, a)
                    else:
                        dst = &root_canvas[y, x]
                        dst.bold = False
                        dst.italic = False
                        dst.underline = False
                        dst.strikethrough = False
                        dst.overline = False
                        dst.reverse = False
                        if kind[y, x] == MIXED:
                            dst.char_ = u"▀"
                            kind[y, x] = GLYPH
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
                            dst.fg_color[0] = <unsigned char>(
                                <double>rgb[0] * wgt + <double>dst.fg_color[0] * nwgt
                            )
                            dst.fg_color[1] = <unsigned char>(
                                <double>rgb[1] * wgt + <double>dst.fg_color[1] * nwgt
                            )
                            dst.fg_color[2] = <unsigned char>(
                                <double>rgb[2] * wgt + <double>dst.fg_color[2] * nwgt
                            )
                        if kind[y, x] == GLYPH:
                            if dst.char_ != u"▀":
                                dst.char_ = u"▀"
                                dst.fg_color = dst.bg_color
                            rgba = self_texture[src_y, src_x]
                            a = alpha * <double>rgba[3] / 255
                            composite(dst.fg_color, rgba, a)
                            rgba = self_texture[src_y + 1, src_x]
                            a = alpha * <double>rgba[3] / 255
                            composite(dst.bg_color, rgba, a)
            j += 2


cdef inline half_graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    bint is_transparent,
    unsigned char[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if is_transparent:
        trans_half_graphics_render(
            root_canvas,
            graphics,
            kind,
            root_y,
            root_x,
            self_texture,
            alpha,
            cregion,
        )
    else:
        opaque_half_graphics_render(root_canvas, root_y, root_x, self_texture, cregion)


cdef opaque_sixel_graphics_render(
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    unsigned char[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Py_ssize_t i, j, h, w, gy, gx
        int abs_y, abs_x, src_y, src_x
        int y, y1, y2, x, x1, x2

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
                src_y = h * (y - abs_y)
                for x in range(x1, x2):
                    src_x = w * (x - abs_x)
                    kind[y, x] = SIXEL
                    for gy in range(h):
                        for gx in range(w):
                            graphics[y, x, gy, gx, 0] = self_texture[
                                src_y + gy, src_x + gx, 0
                            ]
                            graphics[y, x, gy, gx, 1] = self_texture[
                                src_y + gy, src_x + gx, 1
                            ]
                            graphics[y, x, gy, gx, 2] = self_texture[
                                src_y + gy, src_x + gx, 2
                            ]
                            graphics[y, x, gy, gx, 3] = 1
            j += 2


cdef trans_sixel_graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    unsigned char[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef:
        Band *band = &cregion.bands[0]
        Cell *dst
        Py_ssize_t i, j, h, w, gy, gx
        int abs_y, abs_x, src_y, src_x
        int y, y1, y2, x, x1, x2
        unsigned char *bg_color
        unsigned char[::1] rgba
        unsigned char[:, :, ::1] sixel

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
                src_y = h * (y - abs_y)
                for x in range(x1, x2):
                    src_x = w * (x - abs_x)
                    if kind[y, x] == SIXEL:
                        sixel = graphics[y, x]
                        for gy in range(h):
                            for gx in range(w):
                                rgba = self_texture[src_y + gy, src_x + gx]
                                composite(
                                    sixel[gy, gx],
                                    rgba,
                                    alpha * <double>rgba[3] / 255,
                                )
                    elif kind[y, x] == GLYPH:
                        dst = &root_canvas[y, x]
                        sixel = graphics[y, x]
                        kind[y, x] = SIXEL
                        for gy in range(h):
                            for gx in range(w):
                                rgba = self_texture[src_y + gy, src_x + gx]
                                if rgba[3]:
                                    sixel[gy, gx, 0] = dst.bg_color[0]
                                    sixel[gy, gx, 1] = dst.bg_color[1]
                                    sixel[gy, gx, 2] = dst.bg_color[2]
                                    sixel[gy, gx, 3] = 1
                                    composite(
                                        sixel[gy, gx],
                                        rgba,
                                        alpha * <double>rgba[3] / 255,
                                    )
                                else:
                                    kind[y, x] = MIXED
                    elif kind[y, x] == MIXED:
                        dst = &root_canvas[y, x]
                        sixel = graphics[y, x]
                        kind[y, x] = SIXEL
                        for gy in range(h):
                            for gx in range(w):
                                rgba = self_texture[src_y + gy, src_x + gx]
                                if rgba[3]:
                                    if not sixel[gy, gx, 3]:
                                        sixel[gy, gx, 0] = dst.bg_color[0]
                                        sixel[gy, gx, 1] = dst.bg_color[1]
                                        sixel[gy, gx, 2] = dst.bg_color[2]
                                        sixel[gy, gx, 3] = 1
                                    composite(
                                        sixel[gy, gx],
                                        rgba,
                                        alpha * <double>rgba[3] / 255,
                                    )
                                elif not sixel[gy, gx, 3]:
                                    kind[y, x] = MIXED
            j += 2


cdef inline sixel_graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    const int root_y,
    const int root_x,
    bint is_transparent,
    unsigned char[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if is_transparent:
        trans_sixel_graphics_render(
            root_canvas,
            graphics,
            kind,
            root_y,
            root_x,
            self_texture,
            alpha,
            cregion,
        )
    else:
        opaque_sixel_graphics_render(
            graphics, kind, root_y, root_x, self_texture, cregion
        )


cpdef void graphics_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    tuple[int, int] root_pos,
    str blitter,
    bint is_transparent,
    unsigned char[:, :, ::1] self_texture,
    double alpha,
    Region region,
):
    cdef:
        int root_y, root_x
        CRegion *cregion
    root_y, root_x = root_pos
    cregion = &region.cregion

    if blitter == "half":
        half_graphics_render(
            root_canvas,
            graphics,
            kind,
            root_y,
            root_x,
            is_transparent,
            self_texture,
            alpha,
            cregion,
        )
    elif blitter == "sixel":
        sixel_graphics_render(
            root_canvas,
            graphics,
            kind,
            root_y,
            root_x,
            is_transparent,
            self_texture,
            alpha,
            cregion,
        )


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


cpdef void terminal_render(
    Cell[:, ::1] root_canvas,
    unsigned char[:, :, :, :, ::1] graphics,
    unsigned char[:, ::1] kind,
    tuple[int, int] root_pos,
    Region region,
):
    pass