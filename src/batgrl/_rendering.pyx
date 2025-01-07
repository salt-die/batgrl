"""
Notes:

`graphics` is (h, w, cell_h, cell_w, 4)-shaped where (cell_h, cell_w)
is pixel geometry of terminal and last axis is RGBM, where M is a
mask that indicates non-transparent pixels.
"""
import numpy as np
cimport numpy as cnp

from libc.string cimport memset
from .geometry.regions cimport CRegion, Region

ctypedef unsigned char uint8
cdef uint8 GLYPH = 0, SIXEL = 1, MIXED = 2

cdef struct RegionIterator:
    CRegion* cregion
    Py_ssize_t i, j
    int y1, y2, y, x1, x2, x
    uint8 done

cdef RegionIterator* iter_(CRegion* cregion):
    cdef RegionIterator it
    if cregion.len == 0:
        it.done = 1
    else:
        it.cregion = cregion
        it.i = 0
        it.j = 0
        it.y1 = cregion.bands[0].y1
        it.y2 = cregion.bands[0].y2
        it.x1 = cregion.bands[0].walls[0]
        it.x2 = cregion.bands[0].walls[1]
        it.y = it.y1
        it.x = it.x1
        it.done = 0
    return &it

cdef void next_(RegionIterator* it):
    if it.done:
        return
    it.x += 1
    if it.x < it.x2:
        return
    it.y += 1
    if it.y < it.y2:
        it.x = it.x1
        return
    it.j += 2
    if it.j < it.cregion.bands[it.i].len:
        it.y = it.y1
        it.x1 = it.cregion.bands[it.i].walls[it.j]
        it.x2 = it.cregion.bands[it.i].walls[it.j + 1]
        it.x = it.x1
        return
    it.i += 1
    if it.i < it.cregion.len:
        it.y1 = it.cregion.bands[it.i].y1
        it.y2 = it.cregion.bands[it.i].y2
        it.y = it.y1
        it.x1 = it.cregion.bands[it.i].walls[it.j]
        it.x2 = it.cregion.bands[it.i].walls[it.j + 1]
        it.x = it.x1
        return
    it.done = 1


cdef packed struct Cell:
    Py_UCS4 char_
    uint8 bold
    uint8 italic
    uint8 underline
    uint8 strikethrough
    uint8 overline
    uint8 reverse
    uint8[3] fg_color
    uint8[3] bg_color


cdef inline unsigned int rgba_eq(uint8[::1] a, uint8[::1] b):
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] == b[3]


cdef inline void composite(
    uint8[::1] dst, uint8[::1] src, double alpha
):
    cdef double a, b

    a = <double>src[0]
    b = <double>dst[0]
    dst[0] = <uint8>((a - b) * alpha + b)
    a = <double>src[1]
    b = <double>dst[1]
    dst[1] = <uint8>((a - b) * alpha + b)
    a = <double>src[2]
    b = <double>dst[2]
    dst[2] = <uint8>((a - b) * alpha + b)


cdef inline double average_graphics(
    uint8[3] bg,
    uint8 [:, :, ::1] graphics,
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

    bg[0] = <uint8>(r // n)
    bg[1] = <uint8>(g // n)
    bg[2] = <uint8>(b // n)
    return <double>n / <double>(h * w)


cdef inline void luminance_quant(
    uint8 *fg,
    uint8 *bg,
    double *luminances,
    uint8[:, :, ::1] texture,
    Py_ssize_t y,
    Py_ssize_t x,
    Py_ssize_t h,
    Py_ssize_t w,
):
    # Quantize a block of colors in texture to two colors by comparing luminances:
    # Find average luminance. Compare each color's luminance to average luminance.
    # If luminance is less than average, add to background else foreground.
    # This is not necessarily a good quantization, but it is fast.

    cdef:
        Py_ssize_t i, j, k = 0, nfg = 0, nbg = 0
        double average_luminance = 0
        double[3] quant_fg, quant_bg

    memset(luminances, 0, sizeof(double) * (h * w))
    memset(quant_fg, 0, sizeof(double) * 3)
    memset(quant_bg, 0, sizeof(double) * 3)

    for i in range(y, y + h):
        for j in range(x, x + w):
            luminances[k] += .2126 * texture[i, j, 0]
            luminances[k] += .7152 * texture[i, j, 1]
            luminances[k] += .0722 * texture[i, j, 2]
            k += 1

    for i in range(k):
        average_luminance += luminances[k]
    average_luminance /= k

    k = 0
    for i in range(y, y + h):
        for j in range(x, x + w):
            if luminances[k] <= average_luminance:
                quant_bg[0] += texture[i, j, 0]
                quant_bg[1] += texture[i, j, 1]
                quant_bg[2] += texture[i, j, 2]
                nbg += 1
                luminances[k] = 0
            else:
                quant_fg[0] += texture[i, j, 0]
                quant_fg[1] += texture[i, j, 1]
                quant_fg[2] += texture[i, j, 2]
                nfg += 1
                luminances[k] = 1
            k += 1

    # nbg won't be 0
    quant_bg[0] /= nbg
    quant_bg[1] /= nbg
    quant_bg[2] /= nbg
    if nfg:
        quant_fg[0] /= nfg
        quant_fg[1] /= nfg
        quant_fg[2] /= nfg
    else:
        quant_fg[0] = quant_bg[0]
        quant_fg[1] = quant_bg[1]
        quant_fg[2] = quant_bg[2]
    fg[0] = <uint8>quant_fg[0]
    fg[1] = <uint8>quant_fg[1]
    fg[2] = <uint8>quant_fg[2]
    bg[0] = <uint8>quant_bg[0]
    bg[1] = <uint8>quant_bg[1]
    bg[2] = <uint8>quant_bg[2]


cdef void opaque_pane_render(
    Cell[:, ::1] root_canvas,
    uint8[::1] bg_color,
    CRegion *cregion,
):
    cdef: 
        RegionIterator* it = iter_(cregion)
        Cell* cell
    
    while not it.done:
        cell = &root_canvas[it.y, it.x]
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
        next_(it)

cdef void trans_pane_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[::1] bg_color,
    double alpha,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        Py_ssize_t h = graphics.shape[2], w = graphics.shape[3], gy, gx
        Cell *dst
        uint8 cell_kind

    while not it.done:
        dst = &root_canvas[it.y, it.x]
        cell_kind = kind[it.y, it.x]
        if cell_kind != SIXEL:
            composite(dst.fg_color, bg_color, alpha)
            composite(dst.bg_color, bg_color, alpha)
        if cell_kind != GLYPH:
            for gy in range(h):
                for gx in range(w):
                    if graphics[it.y, it.x, gy, gx, 3]:
                        composite(graphics[it.y, it.x, gy, gx], bg_color, alpha)
        next_(it)

cpdef void pane_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    bint is_transparent,
    Region region,
    tuple[int, int, int] bg_color,
    double alpha,
):
    cdef:
        CRegion *cregion = &region.cregion
        cnp.ndarray[uint8, ndim=1] bg = np.array(bg_color, np.uint8)

    if is_transparent:
        trans_pane_render(root_canvas, graphics, kind, bg, alpha, cregion)
    else:
        opaque_pane_render(root_canvas, bg, cregion)


cdef void opaque_text_render(
    Cell[:, ::1] root_canvas, Cell[:, ::1] self_canvas, CRegion *cregion
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1

    while not it.done:
        root_canvas[it.y, it.x] = self_canvas[it.y - abs_y, it.x - abs_x]
        next_(it)


cdef void trans_text_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    Cell[:, ::1] self_canvas,
    double alpha,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1
        Py_ssize_t h = graphics.shape[2], w = graphics.shape[3], gy, gx
        cnp.ndarray[uint8, ndim=1] rgb = np.empty(3, np.uint8)
        double wgt, nwgt
        Cell *dst
        Cell *src

    while not it.done:
        src = &self_canvas[it.y - abs_y, it.x - abs_x]
        dst = &root_canvas[it.y, it.x]
        # FIXME: Consider all whitespace?
        if src.char_ == u" " or src.char_ == u"⠀":
            if kind[it.y, it.x] != SIXEL:
                composite(dst.fg_color, src.bg_color, alpha)
                composite(dst.bg_color, src.bg_color, alpha)
            if kind[it.y, it.x] != GLYPH:
                for gy in range(h):
                    for gx in range(w):
                        if graphics[it.y, it.x, gy, gx, 3]:
                            composite(
                                graphics[it.y, it.x, gy, gx], src.bg_color, alpha
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
            if kind[it.y, it.x] == SIXEL:
                average_graphics(dst.bg_color, graphics[it.y, it.x], h, w)
            elif kind[it.y, it.x] == MIXED:
                wgt = average_graphics(rgb, graphics[it.y, it.x], h, w)
                nwgt = 1 - wgt
                dst.bg_color[0] = <uint8>(
                    <double>rgb[0] * wgt + <double>dst.bg_color[0] * nwgt
                )
                dst.bg_color[1] = <uint8>(
                    <double>rgb[1] * wgt + <double>dst.bg_color[1] * nwgt
                )
                dst.bg_color[2] = <uint8>(
                    <double>rgb[2] * wgt + <double>dst.bg_color[2] * nwgt
                )
            kind[it.y, it.x] = GLYPH
            composite(dst.bg_color, src.bg_color, alpha)
        next_(it)

cpdef void text_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    bint is_transparent,
    Region region,
    Cell[:, ::1] self_canvas,
    double alpha,
):
    cdef CRegion *cregion = &region.cregion
    if is_transparent:
        trans_text_render(root_canvas, graphics, kind, self_canvas, alpha, cregion)
    else:
        opaque_text_render(root_canvas, self_canvas, cregion)


cdef opaque_half_graphics_render(
    Cell[:, ::1] root_canvas, uint8[:, :, ::1] self_texture, CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Cell *dst

    while not it.done:
        dst = &root_canvas[it.y, it.x]
        dst.char_ = u"▀"
        dst.bold = False
        dst.italic = False
        dst.underline = False
        dst.strikethrough = False
        dst.overline = False
        dst.reverse = False
        src_y = 2 * (it.y - abs_y)
        src_x = it.x - abs_x
        dst.fg_color[0] = self_texture[src_y, src_x, 0]
        dst.fg_color[1] = self_texture[src_y, src_x, 1]
        dst.fg_color[2] = self_texture[src_y, src_x, 2]
        dst.bg_color[0] = self_texture[src_y + 1, src_x, 0]
        dst.bg_color[1] = self_texture[src_y + 1, src_x, 1]
        dst.bg_color[2] = self_texture[src_y + 1, src_x, 2]
        next_(it)

cdef trans_half_graphics_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Py_ssize_t h = graphics.shape[2], w = graphics.shape[3], gy, gx
        Cell *dst
        double wgt, nwgt, a
        uint8[:, :, ::1] sixel
        uint8[::1] rgba
        cnp.ndarray[uint8, ndim=1] rgb = np.empty(3, np.uint8)

    while not it.done:
        src_y = 2 * (it.y - abs_y)
        src_x = it.x - abs_x
        if rgba_eq(
            self_texture[src_y, src_x], self_texture[src_y + 1, src_x]
        ):
            dst = &root_canvas[it.y, it.x]
            rgba = self_texture[src_y, src_x]
            a = alpha * <double>rgba[3] / 255
            if kind[it.y, it.x] != SIXEL:
                composite(dst.fg_color, rgba, a)
                composite(dst.bg_color, rgba, a)
            if kind[it.y, it.x] != GLYPH:
                for gy in range(h):
                    for gx in range(w):
                        if graphics[it.y, it.x, gy, gx, 3]:
                            composite(graphics[it.y, it.x, gy, gx], rgba, a)
        elif kind[it.y, it.x] == SIXEL:
            sixel = graphics[it.y, it.x]
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
            dst = &root_canvas[it.y, it.x]
            dst.bold = False
            dst.italic = False
            dst.underline = False
            dst.strikethrough = False
            dst.overline = False
            dst.reverse = False
            if kind[it.y, it.x] == MIXED:
                dst.char_ = u"▀"
                kind[it.y, it.x] = GLYPH
                wgt = average_graphics(rgb, graphics[it.y, it.x], h, w)
                nwgt = 1 - wgt
                dst.bg_color[0] = <uint8>(
                    <double>rgb[0] * wgt + <double>dst.bg_color[0] * nwgt
                )
                dst.bg_color[1] = <uint8>(
                    <double>rgb[1] * wgt + <double>dst.bg_color[1] * nwgt
                )
                dst.bg_color[2] = <uint8>(
                    <double>rgb[2] * wgt + <double>dst.bg_color[2] * nwgt
                )
                dst.fg_color[0] = <uint8>(
                    <double>rgb[0] * wgt + <double>dst.fg_color[0] * nwgt
                )
                dst.fg_color[1] = <uint8>(
                    <double>rgb[1] * wgt + <double>dst.fg_color[1] * nwgt
                )
                dst.fg_color[2] = <uint8>(
                    <double>rgb[2] * wgt + <double>dst.fg_color[2] * nwgt
                )
            if kind[it.y, it.x] == GLYPH:
                if dst.char_ != u"▀":
                    dst.char_ = u"▀"
                    dst.fg_color = dst.bg_color
                rgba = self_texture[src_y, src_x]
                a = alpha * <double>rgba[3] / 255
                composite(dst.fg_color, rgba, a)
                rgba = self_texture[src_y + 1, src_x]
                a = alpha * <double>rgba[3] / 255
                composite(dst.bg_color, rgba, a)
        next_(it)


cdef opaque_sixel_graphics_render(
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Py_ssize_t h = graphics.shape[2], w = graphics.shape[3], gy, gx
        uint8[:, :, ::1] sixel

    while not it.done:
        src_y = h * (it.y - abs_y)
        src_x = w * (it.x - abs_x)
        kind[it.y, it.x] = SIXEL
        sixel = graphics[it.y, it.x]
        for gy in range(h):
            for gx in range(w):
                sixel[gy, gx, 0] = self_texture[src_y + gy, src_x + gx, 0]
                sixel[gy, gx, 1] = self_texture[src_y + gy, src_x + gx, 1]
                sixel[gy, gx, 2] = self_texture[src_y + gy, src_x + gx, 2]
                sixel[gy, gx, 3] = 1
        next_(it)

cdef trans_sixel_graphics_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Py_ssize_t h = graphics.shape[2], w = graphics.shape[3], gy, gx
        Cell *dst
        uint8 *bg_color
        uint8[::1] rgba
        uint8[:, :, ::1] sixel

    while not it.done:
        src_y = h * (it.y - abs_y)
        src_x = w * (it.x - abs_x)
        if kind[it.y, it.x] == SIXEL:
            sixel = graphics[it.y, it.x]
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    composite(sixel[gy, gx], rgba, alpha * <double>rgba[3] / 255)
        elif kind[it.y, it.x] == GLYPH:
            dst = &root_canvas[it.y, it.x]
            sixel = graphics[it.y, it.x]
            kind[it.y, it.x] = SIXEL
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    if rgba[3]:
                        sixel[gy, gx, 0] = dst.bg_color[0]
                        sixel[gy, gx, 1] = dst.bg_color[1]
                        sixel[gy, gx, 2] = dst.bg_color[2]
                        sixel[gy, gx, 3] = 1
                        composite(sixel[gy, gx], rgba, alpha * <double>rgba[3] / 255)
                    else:
                        kind[it.y, it.x] = MIXED
        elif kind[it.y, it.x] == MIXED:
            dst = &root_canvas[it.y, it.x]
            sixel = graphics[it.y, it.x]
            kind[it.y, it.x] = SIXEL
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    if rgba[3]:
                        if not sixel[gy, gx, 3]:
                            sixel[gy, gx, 0] = dst.bg_color[0]
                            sixel[gy, gx, 1] = dst.bg_color[1]
                            sixel[gy, gx, 2] = dst.bg_color[2]
                            sixel[gy, gx, 3] = 1
                        composite(sixel[gy, gx], rgba, alpha * <double>rgba[3] / 255)
                    elif not sixel[gy, gx, 3]:
                        kind[it.y, it.x] = MIXED
        next_(it)


cdef opaque_braille_graphics_render(
    Cell[:, ::1] root_canvas, uint8[:, :, ::1] self_texture, CRegion *cregion
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Py_ssize_t gy, gx

    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        for gy in range(4):
            for gx in range(2):
                pass
        next_(it)


cdef trans_braille_graphics_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef:
        RegionIterator* it = iter_(cregion)
        int abs_y = it.y1, abs_x = it.x1, src_y, src_x
        Py_ssize_t gy, gx

    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        for gy in range(4):
            for gx in range(2):
                pass
        next_(it)


cpdef void graphics_render(
    Cell[:, ::1] root_canvas,
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    str blitter,
    bint is_transparent,
    uint8[:, :, ::1] self_texture,
    double alpha,
    Region region,
):
    cdef CRegion *cregion = &region.cregion

    if blitter == "half":
        if is_transparent:
            trans_half_graphics_render(
                root_canvas, graphics, kind, self_texture, alpha, cregion
            )
        else:
            opaque_half_graphics_render(root_canvas, self_texture, cregion)
    elif blitter == "sixel":
        if is_transparent:
            trans_sixel_graphics_render(
                root_canvas, graphics, kind, self_texture, alpha, cregion
            )
        else:
            opaque_sixel_graphics_render(graphics, kind, self_texture, cregion)
    elif blitter == "braille":
        if is_transparent:
            trans_braille_graphics_render(
                root_canvas, graphics, kind, self_texture, alpha, cregion
            )
        else:
            opaque_braille_graphics_render(root_canvas, self_texture, cregion)


# cpdef void field_render(
#     Cell[:, ::1] root_canvas,
#     uint8[:, :, :, :, ::1] graphics,
#     uint8[:, ::1] kind,
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
#     uint8[:, :, :, :, ::1] graphics,
#     uint8[:, ::1] kind,
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
    uint8[:, :, :, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] root_pos,
    Region region,
):
    pass
