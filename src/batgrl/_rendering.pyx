# distutils: language = c
# distutils: sources = src/batgrl/cwidth.c
from libc.string cimport memset

import numpy as np
cimport numpy as cnp

from ._fbuf cimport fbuf, fbuf_flush, fbuf_grow, fbuf_printf, fbuf_putn, fbuf_putucs4
from ._sixel cimport csixel_ansi
from .colors.quantization import median_variance_quantization
from .geometry.regions cimport CRegion, Region
from .terminal._fbuf_wrapper cimport FBufWrapper

ctypedef unsigned char uint8
cdef uint8 GLYPH = 0, SIXEL = 1, MIXED = 2
cdef unsigned int[8] BRAILLE_ENUM = [1, 8, 2, 16, 4, 32, 64, 128]

cdef extern from "cwidth.h":
    int cwidth(Py_UCS4)


cdef struct RegionIterator:
    CRegion* cregion
    size_t i, j
    int y1, y2, y, x1, x2, x
    bint done


cdef void init_iter(RegionIterator* it, CRegion* cregion):
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
        it.j = 0
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


cdef inline bint rgb_eq(uint8* a, uint8* b):
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]


cdef inline bint rgba_eq(uint8[::1] a, uint8[::1] b):
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] == b[3]


cdef inline bint all_eq(uint8[:, :, ::1] a, uint8[:, :, ::1] b):
    cdef size_t h = a.shape[0], w = a.shape[1], y, x
    for y in range(h):
        for x in range(w):
            if not rgba_eq(a[y, x], b[y, x]):
                return 0
    return 1


cdef inline bint cell_eq(Cell* a, Cell* b):
    return (
        a.char_ == b.char_
        and a.bold == b.bold
        and a.italic == b.italic
        and a.underline == b.underline
        and a.overline == b.overline
        and a.reverse == b.reverse
        and rgb_eq(&a.fg_color[0], &b.fg_color[0])
        and rgb_eq(&a.bg_color[0], &b.bg_color[0])
    )


cdef inline size_t graphics_geom_height(Cell[:, ::1] cells, uint8[:, :, ::1] graphics):
    return graphics.shape[0] // cells.shape[0]


cdef inline size_t graphics_geom_width(Cell[:, ::1] cells, uint8[:, :, ::1] graphics):
    return graphics.shape[1] // cells.shape[1]


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


cdef inline double average_graphics(uint8[3] bg, uint8 [:, :, ::1] graphics):
    cdef:
        size_t h = graphics.shape[0]
        size_t w = graphics.shape[1]
        size_t y, x
        unsigned long r = 0, g = 0, b = 0, n = 0

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
    size_t y,
    size_t x,
    size_t h,
    size_t w,
):
    # Quantize a block of colors in texture to two colors by comparing luminances:
    # Find average luminance. Compare each color's luminance to average luminance.
    # If luminance is less than average, add to background else foreground.
    # This is not necessarily a good quantization, but it is fast.

    cdef:
        size_t i, j, k, nfg = 0, nbg = 0
        double average_luminance = 0
        double[3] quant_fg, quant_bg

    memset(luminances, 0, sizeof(double) * (h * w))
    memset(quant_fg, 0, sizeof(double) * 3)
    memset(quant_bg, 0, sizeof(double) * 3)

    k = 0
    for i in range(y, y + h):
        for j in range(x, x + w):
            luminances[k] += .2126 * texture[i, j, 0]
            luminances[k] += .7152 * texture[i, j, 1]
            luminances[k] += .0722 * texture[i, j, 2]
            k += 1

    k = h * w
    for i in range(k):
        average_luminance += luminances[i]
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

    if nbg:
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
    if not nbg:
        quant_bg[0] = quant_fg[0]
        quant_bg[1] = quant_fg[1]
        quant_bg[2] = quant_fg[2]

    fg[0] = <uint8>quant_fg[0]
    fg[1] = <uint8>quant_fg[1]
    fg[2] = <uint8>quant_fg[2]
    bg[0] = <uint8>quant_bg[0]
    bg[1] = <uint8>quant_bg[1]
    bg[2] = <uint8>quant_bg[2]


cdef void opaque_pane_render(
    Cell[:, ::1] cells, uint8[::1] bg_color, CRegion *cregion
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef Cell* cell

    while not it.done:
        cell = &cells[it.y, it.x]
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
        next_(&it)


cdef void trans_pane_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8[::1] bg_color,
    double alpha,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst

    while not it.done:
        dst = &cells[it.y, it.x]
        if kind[it.y, it.x] != SIXEL:
            composite(dst.fg_color, bg_color, alpha)
            composite(dst.bg_color, bg_color, alpha)
        if kind[it.y, it.x] != GLYPH:
            oy = it.y * h
            ox = it.x * w
            for gy in range(h):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(graphics[oy + gy, ox + gx], bg_color, alpha)
        next_(&it)


cpdef void pane_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
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
        trans_pane_render(cells, graphics, kind, bg, alpha, cregion)
    else:
        opaque_pane_render(cells, bg, cregion)


cdef void opaque_text_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    Cell[:, ::1] self_canvas,
    CRegion *cregion
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    while not it.done:
        cells[it.y, it.x] = self_canvas[it.y - abs_y, it.x - abs_x]
        next_(&it)


cdef void trans_text_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    Cell[:, ::1] self_canvas,
    double alpha,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        cnp.ndarray[uint8, ndim=1] rgb = np.empty(3, np.uint8)
        double wgt, nwgt
        Cell *dst
        Cell *src

    while not it.done:
        src = &self_canvas[it.y - abs_y, it.x - abs_x]
        dst = &cells[it.y, it.x]
        # FIXME: Consider all whitespace?
        if src.char_ == u" " or src.char_ == u"⠀":
            if kind[it.y, it.x] != SIXEL:
                composite(dst.fg_color, src.bg_color, alpha)
                composite(dst.bg_color, src.bg_color, alpha)
            if kind[it.y, it.x] != GLYPH:
                oy = it.y * h
                ox = it.x * w
                for gy in range(h):
                    for gx in range(w):
                        if graphics[oy + gy, ox + gx, 3]:
                            composite(graphics[oy + gy, ox + gx], src.bg_color, alpha)
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
                oy = it.y * h
                ox = it.x * w
                average_graphics(dst.bg_color, graphics[oy:oy + h, ox:ox + w])
            elif kind[it.y, it.x] == MIXED:
                oy = it.y * h
                ox = it.x * w
                wgt = average_graphics(rgb, graphics[oy: oy + h, ox:ox + w])
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
        next_(&it)


cpdef void text_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] abs_pos,
    bint is_transparent,
    Region region,
    Cell[:, ::1] self_canvas,
    double alpha,
):
    cdef:
        int abs_y = abs_pos[0], abs_x = abs_pos[1]
        CRegion *cregion = &region.cregion

    if is_transparent:
        trans_text_render(
            cells, graphics, kind, abs_y, abs_x, self_canvas, alpha, cregion
        )
    else:
        opaque_text_render(cells, abs_y, abs_x, self_canvas, cregion)


cdef opaque_half_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        Cell *dst

    while not it.done:
        dst = &cells[it.y, it.x]
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
        next_(&it)


cdef trans_half_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst
        double wgt, nwgt, a
        uint8[::1] rgba
        cnp.ndarray[uint8, ndim=1] rgb = np.empty(3, np.uint8)

    while not it.done:
        src_y = 2 * (it.y - abs_y)
        src_x = it.x - abs_x
        if rgba_eq(
            self_texture[src_y, src_x], self_texture[src_y + 1, src_x]
        ):
            dst = &cells[it.y, it.x]
            rgba = self_texture[src_y, src_x]
            a = alpha * <double>rgba[3] / 255
            if kind[it.y, it.x] != SIXEL:
                composite(dst.fg_color, rgba, a)
                composite(dst.bg_color, rgba, a)
            if kind[it.y, it.x] != GLYPH:
                oy = it.y * h
                ox = it.x * w
                for gy in range(h):
                    for gx in range(w):
                        if graphics[oy + gy, ox + gx, 3]:
                            composite(graphics[oy + gy, ox + gx], rgba, a)
        elif kind[it.y, it.x] == SIXEL:
            oy = it.y * h
            ox = it.x * w
            rgba = self_texture[src_y, src_x]
            a = alpha * <double>rgba[3] / 255
            for gy in range(h // 2):
                for gx in range(w):
                    graphics[oy + gy, ox + gx, 3] = 1
                    composite(graphics[oy + gy, ox + gx], rgba, a)
            rgba = self_texture[src_y + 1, src_x]
            a = alpha * <double>rgba[3] / 255
            for gy in range(h // 2, h):
                for gx in range(w):
                    graphics[oy + gy, ox + gx, 3] = 1
                    composite(graphics[oy + gy, ox + gx], rgba, a)
        else:
            dst = &cells[it.y, it.x]
            dst.bold = False
            dst.italic = False
            dst.underline = False
            dst.strikethrough = False
            dst.overline = False
            dst.reverse = False
            if kind[it.y, it.x] == MIXED:
                dst.char_ = u"▀"
                kind[it.y, it.x] = GLYPH
                oy = it.y * h
                ox = it.x * w
                wgt = average_graphics(rgb, graphics[oy: oy + h, ox: ox + w])
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
        next_(&it)


cdef opaque_sixel_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx

    while not it.done:
        oy = it.y * h
        ox = it.x * w
        src_y = h * (it.y - abs_y)
        src_x = w * (it.x - abs_x)
        kind[it.y, it.x] = SIXEL
        for gy in range(h):
            for gx in range(w):
                graphics[oy + gy, ox + gx, 0] = self_texture[src_y + gy, src_x + gx, 0]
                graphics[oy + gy, ox + gx, 1] = self_texture[src_y + gy, src_x + gx, 1]
                graphics[oy + gy, ox + gx, 2] = self_texture[src_y + gy, src_x + gx, 2]
                graphics[oy + gy, ox + gx, 3] = 1
        next_(&it)


cdef trans_sixel_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        uint8 *bg
        uint8[::1] rgba

    while not it.done:
        oy = it.y * h
        ox = it.x * w
        src_y = oy - abs_y * h
        src_x = ox - abs_x * w
        if kind[it.y, it.x] == SIXEL:
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    composite(
                        graphics[oy + gy, ox + gx], rgba, alpha * <double>rgba[3] / 255
                    )
        elif kind[it.y, it.x] == GLYPH:
            bg = &cells[it.y, it.x].bg_color[0]
            kind[it.y, it.x] = SIXEL
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    if rgba[3]:
                        graphics[oy + gy, ox + gx, 0] = bg[0]
                        graphics[oy + gy, ox + gx, 1] = bg[1]
                        graphics[oy + gy, ox + gx, 2] = bg[2]
                        graphics[oy + gy, ox + gx, 3] = 1
                        composite(
                            graphics[oy + gy, ox + gx],
                            rgba,
                            alpha * <double>rgba[3] / 255,
                        )
                    else:
                        kind[it.y, it.x] = MIXED
        elif kind[it.y, it.x] == MIXED:
            bg = &cells[it.y, it.x].bg_color[0]
            kind[it.y, it.x] = SIXEL
            for gy in range(h):
                for gx in range(w):
                    rgba = self_texture[src_y + gy, src_x + gx]
                    if rgba[3]:
                        if not graphics[oy + gy, ox + gx, 3]:
                            graphics[oy + gy, ox + gx, 0] = bg[0]
                            graphics[oy + gy, ox + gx, 1] = bg[1]
                            graphics[oy + gy, ox + gx, 2] = bg[2]
                            graphics[oy + gy, ox + gx, 3] = 1
                        composite(
                            graphics[oy + gy, ox + gx],
                            rgba,
                            alpha * <double>rgba[3] / 255,
                        )
                    elif not graphics[oy + gy, ox + gx, 3]:
                        kind[it.y, it.x] = MIXED
        next_(&it)


cdef opaque_braille_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        uint8[3] fg, bg
        double[8] luminances
        Cell* cell
        uint8 i
        unsigned long char_

    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        luminance_quant(
            &fg[0], &bg[0], &luminances[0], self_texture, src_y, src_x, 4, 2
        )
        cell = &cells[it.y, it.x]
        if rgb_eq(&fg[0], &bg[0]):
            char_ = 32
        else:
            char_ = 10240
            for i in range(8):
                if luminances[i]:
                    char_ += BRAILLE_ENUM[i]
        cell.char_ = char_
        cell.bold = False
        cell.italic = False
        cell.underline = False
        cell.strikethrough = False
        cell.overline = False
        cell.reverse = False
        cell.fg_color[0] = fg[0]
        cell.fg_color[1] = fg[1]
        cell.fg_color[2] = fg[2]
        cell.bg_color[0] = bg[0]
        cell.bg_color[1] = bg[1]
        cell.bg_color[2] = bg[2]
        next_(&it)


cdef trans_braille_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    cdef RegionIterator it
    init_iter(&it, cregion)
    cdef:
        int src_y, src_x
        uint8[3] fg, bg
        double[8] luminances
        Cell* cell
        uint8 i, j
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox
        cnp.ndarray[uint8, ndim=1] rgb = np.empty(3, np.uint8)
        double alpha_avg = 0
        unsigned long char_

    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        luminance_quant(
            &fg[0], &bg[0], &luminances[0], self_texture, src_y, src_x, 4, 2
        )
        cell = &cells[it.y, it.x]
        if rgb_eq(&fg[0], &bg[0]):
            char_ = 32
        else:
            char_ = 10240
            for i in range(8):
                if luminances[i]:
                    char_ += BRAILLE_ENUM[i]
        cell.char_ = char_
        cell.bold = False
        cell.italic = False
        cell.underline = False
        cell.strikethrough = False
        cell.overline = False
        cell.reverse = False
        cell.fg_color[0] = fg[0]
        cell.fg_color[1] = fg[1]
        cell.fg_color[2] = fg[2]
        if kind[it.y, it.x] == SIXEL:
            oy = it.y * h
            ox = it.x * w
            average_graphics(cell.bg_color, graphics[oy:oy + h, ox:ox + w])
        elif kind[it.y, it.x] == MIXED:
            oy = it.y * h
            ox = it.x * w
            wgt = average_graphics(rgb, graphics[oy:oy + h, ox: ox + w])
            nwgt = 1 - wgt
            cell.bg_color[0] = <uint8>(
                <double>rgb[0] * wgt + <double>cell.bg_color[0] * nwgt
            )
            cell.bg_color[1] = <uint8>(
                <double>rgb[1] * wgt + <double>cell.bg_color[1] * nwgt
            )
            cell.bg_color[2] = <uint8>(
                <double>rgb[2] * wgt + <double>cell.bg_color[2] * nwgt
            )
        kind[it.y, it.x] = GLYPH

        for i in range(src_y, src_y + 4):
            for j in range(src_x, src_x + 2):
                alpha_avg += self_texture[src_y, src_x, 3]
        alpha_avg = alpha * (alpha_avg / (8 * 255))
        composite(cell.bg_color, bg, alpha_avg)
        next_(&it)


cpdef void graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] abs_pos,
    str blitter,
    bint is_transparent,
    uint8[:, :, ::1] self_texture,
    double alpha,
    Region region,
):
    cdef:
        int abs_y = abs_pos[0], abs_x = abs_pos[1]
        CRegion *cregion = &region.cregion

    if blitter == "half":
        if is_transparent:
            trans_half_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_half_graphics_render(cells, abs_y, abs_x, self_texture, cregion)
    elif blitter == "sixel":
        if is_transparent:
            trans_sixel_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_sixel_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, cregion
            )
    elif blitter == "braille":
        if is_transparent:
            trans_braille_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_braille_graphics_render(cells, abs_y, abs_x, self_texture, cregion)


cpdef void cursor_render(
    Cell[:, ::1] cells,
    bint bold,
    bint italic,
    bint underline,
    bint strikethrough,
    bint overline,
    bint reverse,
    tuple[int, int, int] fg_color,
    tuple[int, int, int] bg_color,
    Region region,
):
    cdef:
        int cbold, citalic, cunderline, cstrikethrough, coverline, creverse
        CRegion* cregion = &region.cregion
        uint8[3] fg, bg
        RegionIterator it
        Cell* dst

    cbold = -1 if bold is None else bold
    citalic = -1 if italic is None else italic
    cunderline = -1 if underline is None else underline
    cstrikethrough = -1 if strikethrough is None else strikethrough
    coverline = -1 if overline is None else overline
    creverse = -1 if reverse is None else reverse
    if fg_color is not None:
        fg[0] = fg_color[0]
        fg[1] = fg_color[1]
        fg[2] = fg_color[2]
    if bg_color is not None:
        bg[0] = bg_color[0]
        bg[1] = bg_color[1]
        bg[2] = bg_color[2]

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        if cbold >= 0:
            dst.bold = cbold
        if citalic >= 0:
            dst.italic = citalic
        if cunderline >= 0:
            dst.underline = cunderline
        if cstrikethrough >= 0:
            dst.strikethrough = cstrikethrough
        if coverline >= 0:
            dst.overline = coverline
        if creverse >= 0:
            dst.reverse = creverse
        if fg_color is not None:
            dst.fg_color[0] = fg[0]
            dst.fg_color[1] = fg[1]
            dst.fg_color[2] = fg[2]
        if bg_color is not None:
            dst.bg_color[0] = bg[0]
            dst.bg_color[1] = bg[1]
            dst.bg_color[2] = bg[2]
        next_(&it)


cpdef void text_field_render(
    Cell[:, ::1] cells,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] graphics,
    long[::1] positions,
    Cell[::1] particles,
    double alpha,
    bint is_transparent,
    Region region,
):
    pass


cpdef void graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, ::1] kind,
    uint8[:, :, ::1] graphics,
    long[::1] positions,
    uint8[::1] particles,  # RGBA
    double alpha,
    bint is_transparent,
    Region region,
):
    pass
# TODO: Missing renders: field_render, graphics_field_render


cdef inline void write_sgr(fbuf* f, uint8 param, bint* first):
    if first[0]:
        fbuf_printf(f, "\x1b[%d", param)
        first[0] = 0
    else:
        fbuf_printf(f, ";%d", param)


cdef inline void write_rgb(fbuf* f, uint8 fg, uint8* rgb, bint* first):
    if first[0]:
        fbuf_printf(f, "\x1b[%d;2;%d;%d;%d", fg, rgb[0], rgb[1], rgb[2])
        first[0] = 0
    else:
        fbuf_printf(f, ";%d;2;%d;%d;%d", fg, rgb[0], rgb[1], rgb[2])


cdef inline ssize_t write_glyph(
    fbuf* f,
    size_t oy,
    size_t ox,
    size_t y,
    size_t x,
    ssize_t* cursor_y,
    ssize_t* cursor_x,
    Cell[:, ::1] canvas,
    Cell* last_sgr,
):
    cdef:
        ssize_t abs_y = y + oy, abs_x = x + ox
        Cell* cell = &canvas[y, x]
        bint first = 1

    if abs_y == cursor_y[0]:
        if abs_x != cursor_x[0]:
            # CHA, Cursor Horizontal Absolute
            if fbuf_printf(f, "\x1b[%dG", abs_x):
                return -1
    else:
        # CUP, Cursor Position
        if fbuf_printf(f, "\x1b[%d;%dH", abs_y + 1, abs_x + 1):
            return -1
    cursor_y[0] = abs_y
    cursor_x[0] = abs_x

    if fbuf_grow(f, 128):
        return -1
    # Build up Select Graphic Rendition (SGR) parameters
    if last_sgr == NULL or cell.bold != last_sgr.bold:
        write_sgr(f, 1 if cell.bold else 22, &first)
    if last_sgr == NULL or cell.italic != last_sgr.italic:
        write_sgr(f, 3 if cell.italic else 23, &first)
    if last_sgr == NULL or cell.underline != last_sgr.underline:
        write_sgr(f, 4 if cell.underline else 24, &first)
    if last_sgr == NULL or cell.strikethrough != last_sgr.strikethrough:
        write_sgr(f, 9 if cell.strikethrough else 29, &first)
    if last_sgr == NULL or cell.overline != last_sgr.overline:
        write_sgr(f, 53 if cell.overline else 54, &first)
    if last_sgr == NULL or cell.reverse != last_sgr.reverse:
        write_sgr(f, 7 if cell.reverse else 27, &first)
    if last_sgr == NULL or not rgb_eq(&cell.fg_color[0], &last_sgr.fg_color[0]):
        write_rgb(f, 38, &cell.fg_color[0], &first)
    if last_sgr == NULL or not rgb_eq(&cell.bg_color[0], &last_sgr.bg_color[0]):
        write_rgb(f, 48, &cell.bg_color[0], &first)
    if not first:
        fbuf_putn(f, "m", 1)
    fbuf_putucs4(f, cell.char_)
    cursor_x[0] += cwidth(cell.char_)  # FIXME: Check clipping of wide chars
    return 0


cpdef void terminal_render(
    bint resized,
    FBufWrapper fwrap,
    tuple[int, int] app_pos,
    Cell[:, ::1] cells,
    Cell[:, ::1] prev_cells,
    uint8[:, :, ::1] graphics,
    uint8[:, :, ::1] prev_graphics,
    uint8[:, ::1] kind,
    uint8[:, ::1] prev_kind,
):
    cdef:
        fbuf* f = &fwrap.f
        size_t h = cells.shape[0], w = cells.shape[1], y, x
        size_t cell_h = graphics_geom_height(cells, graphics)
        size_t cell_w = graphics_geom_width(cells, graphics)
        size_t gh, gw
        size_t min_y_sixel = h, min_x_sixel = w, max_y_sixel = 0, max_x_sixel = 0
        size_t oy = app_pos[0], ox = app_pos[1]
        ssize_t cursor_y = -1, cursor_x = -1
        Cell* last_sgr = NULL
        bint emit_sixel = 0
        uint8[:, ::1] palette, indices

    if fbuf_putn(f, "\x1b7", 2):  # Save cursor
        raise MemoryError

    for y in range(h):
        for x in range(w):
            if kind[y, x] != GLYPH:
                if y < min_y_sixel:
                    min_y_sixel = y
                if y > max_y_sixel:
                    max_y_sixel = y
                if x < min_x_sixel:
                    min_x_sixel = x
                if x > max_x_sixel:
                    max_x_sixel = x
                if not emit_sixel:
                    if resized:
                        emit_sixel = 1
                    elif kind[y, x] != prev_kind[y, x]:
                        emit_sixel = 1
                    elif (
                        kind[y, x] == MIXED
                        and not cell_eq(&cells[y, x], &prev_cells[y, x])
                    ):
                        emit_sixel = 1
                    else:
                        gh = y * cell_h
                        gw = x * cell_w
                        emit_sixel = not all_eq(
                            graphics[gh:gh + cell_h, gw:gw + cell_w],
                            prev_graphics[gh:gh + cell_h, gw:gw + cell_w],
                        )
    # Note ALL mixed and ALL sixel cells are re-emitted if any has changed.
    if emit_sixel:
        for y in range(h):
            for x in range(w):
                if kind[y, x] == MIXED:
                    if write_glyph(
                        f, oy, ox, y, x, &cursor_y, &cursor_x, cells, last_sgr
                    ):
                        raise MemoryError
                    last_sgr = &cells[y, x]

        gh = (max_y_sixel + 1 - min_y_sixel) * cell_h
        # If sixel graphics rect reaches last line of terminal, its height must be
        # truncated to nearest multiple of 6 - 6 to prevent scrolling.
        if max_y_sixel + 1 == h:
            gh -= 6 + gh % 6
        gw = (max_x_sixel + 1 - min_x_sixel) * cell_w
        palette, indices = median_variance_quantization(
            graphics, min_y_sixel * cell_h, min_x_sixel * cell_w, gh, gw
        )
        if fbuf_printf(f, "\x1b[%d;%dH", min_y_sixel + 1, min_x_sixel + 1):
            raise MemoryError
        if csixel_ansi(
            f, palette, indices, graphics, min_y_sixel * cell_h, min_x_sixel * cell_w
        ):
            raise MemoryError

    cursor_y = -1
    cursor_x = -1
    for y in range(h):
        for x in range(w):
            if kind[y, x] == GLYPH and (
                resized
                or prev_kind[y, x] != GLYPH
                or not cell_eq(&cells[y, x], &prev_cells[y, x])
            ):
                if write_glyph(
                    f, oy, ox, y, x, &cursor_y, &cursor_x, cells, last_sgr
                ):
                    raise MemoryError
                last_sgr = &cells[y, x]

    if fbuf_putn(f, "\x1b8", 2):  # Restore cursor
        raise MemoryError
    fbuf_flush(f)
