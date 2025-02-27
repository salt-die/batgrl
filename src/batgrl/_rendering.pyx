# distutils: language = c
# distutils: sources = src/batgrl/cwidth.c

from libc.math cimport round
from libc.stdlib cimport malloc, free
from libc.string cimport memset

cimport cython

from ._rendering cimport Cell
from ._sixel cimport OctTree, sixel
from .geometry.regions cimport CRegion, Region, bounding_rect, contains
from .terminal._fbuf cimport (
    fbuf,
    fbuf_flush_fd,
    fbuf_grow,
    fbuf_printf,
    fbuf_putn,
    fbuf_putucs4,
)
from .terminal.vt100_terminal cimport Vt100Terminal

ctypedef unsigned char uint8
cdef uint8 GLYPH = 0, SIXEL = 1, MIXED = 2
cdef unsigned int[8] BRAILLE_ENUM = [1, 8, 2, 16, 4, 32, 64, 128]

cdef extern from "cwidth.h":
    int cwidth(Py_UCS4)


cdef struct RegionIterator:
    CRegion *cregion
    size_t i, j
    int y1, y2, y, x1, x2, x
    bint done


cdef void init_iter(RegionIterator *it, CRegion *cregion):
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


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void next_(RegionIterator *it):
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


cdef inline bint rgb_eq(uint8 *a, uint8 *b):
    return (a[0] == b[0]) & (a[1] == b[1]) & (a[2] == b[2])


cdef inline bint rgba_eq(uint8 *a, uint8 *b):
    return (a[0] == b[0]) & (a[1] == b[1]) & (a[2] == b[2]) & (a[3] == b[3])


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline bint all_eq(uint8[:, :, ::1] a, uint8[:, :, ::1] b):
    cdef size_t h = a.shape[0], w = a.shape[1], y, x
    for y in range(h):
        for x in range(w):
            if not rgba_eq(&a[y, x, 0], &b[y, x, 0]):
                return 0
    return 1


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline bint one_color(uint8[:, :, ::1] rgb, int y, int x, size_t h, size_t w):
    cdef size_t i, j
    for i in range(h):
        for j in range(w):
            if not rgba_eq(&rgb[y, x, 0], &rgb[y + i, x + j, 0]):
                return 0
    return 1


cdef inline bint cell_eq(Cell *a, Cell *b):
    return (
        (a.char_ == b.char_)
        & (a.bold == b.bold)
        & (a.italic == b.italic)
        & (a.underline == b.underline)
        & (a.strikethrough == b.strikethrough)
        & (a.overline == b.overline)
        & (a.reverse == b.reverse)
        & (rgb_eq(&a.fg_color[0], &b.fg_color[0]))
        & (rgb_eq(&a.bg_color[0], &b.bg_color[0]))
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline size_t graphics_geom_height(Cell[:, ::1] cells, uint8[:, :, ::1] graphics):
    return graphics.shape[0] // cells.shape[0]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline size_t graphics_geom_width(Cell[:, ::1] cells, uint8[:, :, ::1] graphics):
    return graphics.shape[1] // cells.shape[1]


cdef inline void composite(uint8 *dst, uint8 *src, double alpha):
    cdef double b = <double>dst[0]
    dst[0] = <uint8>((<double>src[0] - b) * alpha + b)
    b = <double>dst[1]
    dst[1] = <uint8>((<double>src[1] - b) * alpha + b)
    b = <double>dst[2]
    dst[2] = <uint8>((<double>src[2] - b) * alpha + b)


cdef inline bint composite_sixels_on_glyph(
    uint8 *bg, uint8 *rgba, uint8 *graphics, double alpha
):
    if rgba[3]:
        graphics[0] = bg[0]
        graphics[1] = bg[1]
        graphics[2] = bg[2]
        graphics[3] = 1
        composite(graphics, rgba, alpha * <double>rgba[3] / 255)
        return 0
    return 1


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double average_graphics(uint8 *bg, uint8 [:, :, ::1] graphics):
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
    if not n:
        return 0
    bg[0] = <uint8>(r // n)
    bg[1] = <uint8>(g // n)
    bg[2] = <uint8>(b // n)
    return <double>n / <double>(h * w)


cdef inline void lerp_rgb(uint8 *src, uint8 *dst, double p):
    cdef double negp = 1 - p
    dst[0] = <uint8>(<double>src[0] * p + <double>dst[0] * negp)
    dst[1] = <uint8>(<double>src[1] * p + <double>dst[1] * negp)
    dst[2] = <uint8>(<double>src[2] * p + <double>dst[2] * negp)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double average_quant(
    uint8 *fg,
    bint *pixels,
    uint8[:, :, ::1] texture,
    size_t y,
    size_t x,
    size_t h,
    size_t w,
):
    # Average the colors in a rect in texture and return the average alpha.

    cdef:
        size_t i, j, k = 0, nfg = 0
        double a, average_alpha = 0
        double[3] quant_fg

    memset(quant_fg, 0, sizeof(double) * 3)

    for i in range(y, y + h):
        for j in range(x, x + w):
            if texture[i, j, 3]:
                pixels[k] = 1
                a = texture[i, j, 3] / 255
                average_alpha += a
                nfg += 1
                quant_fg[0] += texture[i, j, 0] * a
                quant_fg[1] += texture[i, j, 1] * a
                quant_fg[2] += texture[i, j, 2] * a
            else:
                pixels[k] = 0
            k += 1

    if nfg:
        quant_fg[0] /= nfg
        quant_fg[1] /= nfg
        quant_fg[2] /= nfg
        fg[0] = <uint8>quant_fg[0]
        fg[1] = <uint8>quant_fg[1]
        fg[2] = <uint8>quant_fg[2]
        return average_alpha / nfg
    return average_alpha


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_pane_render(
    Cell[:, ::1] cells, uint8 *bg_color, CRegion *cregion
):
    cdef:
        RegionIterator it
        Cell *cell

    init_iter(&it, cregion)
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


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_pane_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    uint8 *bg_color,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        RegionIterator it
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        if kind[it.y, it.x] != SIXEL:
            composite(&dst.fg_color[0], bg_color, alpha)
            composite(&dst.bg_color[0], bg_color, alpha)
        if kind[it.y, it.x] != GLYPH:
            oy = it.y * h
            ox = it.x * w
            for gy in range(h):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], bg_color, alpha)
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
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
        uint8[3] bg

    bg[0] = bg_color[0]
    bg[1] = bg_color[1]
    bg[2] = bg_color[2]

    if is_transparent:
        trans_pane_render(cells, graphics, kind, &bg[0], alpha, cregion)
    else:
        opaque_pane_render(cells, &bg[0], cregion)


@cython.boundscheck(False)
@cython.wraparound(False)
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


@cython.boundscheck(False)
@cython.wraparound(False)
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
    cdef:
        RegionIterator it
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        uint8[3] rgb
        double p
        Cell *dst
        Cell *src

    init_iter(&it, cregion)
    while not it.done:
        src = &self_canvas[it.y - abs_y, it.x - abs_x]
        dst = &cells[it.y, it.x]
        # FIXME: Consider all whitespace?
        if src.char_ == u" " or src.char_ == u"⠀":
            if kind[it.y, it.x] != SIXEL:
                composite(&dst.fg_color[0], &src.bg_color[0], alpha)
                composite(&dst.bg_color[0], &src.bg_color[0], alpha)
            if kind[it.y, it.x] != GLYPH:
                oy = it.y * h
                ox = it.x * w
                for gy in range(h):
                    for gx in range(w):
                        if graphics[oy + gy, ox + gx, 3]:
                            composite(
                                &graphics[oy + gy, ox + gx, 0], &src.bg_color[0], alpha
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
                oy = it.y * h
                ox = it.x * w
                average_graphics(&dst.bg_color[0], graphics[oy:oy + h, ox:ox + w])
            elif kind[it.y, it.x] == MIXED:
                oy = it.y * h
                ox = it.x * w
                p = average_graphics(&rgb[0], graphics[oy: oy + h, ox:ox + w])
                lerp_rgb(&rgb[0], &dst.bg_color[0], p)
            kind[it.y, it.x] = GLYPH
            composite(&dst.bg_color[0], &src.bg_color[0], alpha)
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void text_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] abs_pos,
    bint is_transparent,
    Cell[:, ::1] self_canvas,
    double alpha,
    Region region,
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


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_full_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        RegionIterator it
        Cell *cell
        uint8 *bg_color

    init_iter(&it, cregion)
    while not it.done:
        cell = &cells[it.y, it.x]
        cell.char_ = u" "
        cell.bold = False
        cell.italic = False
        cell.underline = False
        cell.strikethrough = False
        cell.overline = False
        cell.reverse = False
        bg_color = &self_texture[it.y - abs_y, it.x - abs_x, 0]
        cell.bg_color[0] = bg_color[0]
        cell.bg_color[1] = bg_color[1]
        cell.bg_color[2] = bg_color[2]
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_full_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        RegionIterator it
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst
        uint8 *bg_color
        double a

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        bg_color = &self_texture[it.y - abs_y, it.x - abs_x, 0]
        a = alpha * <double>bg_color[3] / 255
        if kind[it.y, it.x] != SIXEL:
            composite(&dst.fg_color[0], bg_color, a)
            composite(&dst.bg_color[0], bg_color, a)
        if kind[it.y, it.x] != GLYPH:
            oy = it.y * h
            ox = it.x * w
            for gy in range(h):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], bg_color, a)
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_half_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        RegionIterator it
        int src_y, src_x
        Cell *dst

    init_iter(&it, cregion)
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


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_half_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        RegionIterator it
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst
        double a_top, a_bot
        uint8 *rgba_top
        uint8 *rgba_bot

    init_iter(&it, cregion)
    while not it.done:
        src_y = 2 * (it.y - abs_y)
        src_x = it.x - abs_x
        dst = &cells[it.y, it.x]
        rgba_top = &self_texture[src_y, src_x, 0]
        a_top = alpha * <double>rgba_top[3] / 255
        rgba_bot = &self_texture[src_y + 1, src_x, 0]
        a_bot = alpha * <double>rgba_bot[3] / 255
        if rgba_eq(rgba_top, rgba_bot):
            if kind[it.y, it.x] != SIXEL:
                composite(&dst.fg_color[0], rgba_top, a_top)
                composite(&dst.bg_color[0], rgba_top, a_top)
            if kind[it.y, it.x] != GLYPH:
                oy = it.y * h
                ox = it.x * w
                for gy in range(h):
                    for gx in range(w):
                        if graphics[oy + gy, ox + gx, 3]:
                            composite(&graphics[oy + gy, ox + gx, 0], rgba_top, a_top)
        elif kind[it.y, it.x] == GLYPH:
            dst.bold = False
            dst.italic = False
            dst.underline = False
            dst.strikethrough = False
            dst.overline = False
            dst.reverse = False
            if dst.char_ != u"▀":
                dst.fg_color = dst.bg_color
                dst.char_ = u"▀"
            composite(&dst.fg_color[0], rgba_top, a_top)
            composite(&dst.bg_color[0], rgba_bot, a_bot)
        else:
            oy = it.y * h
            ox = it.x * w
            if kind[it.y, it.x] == MIXED:
                kind[it.y, it.x] = SIXEL
                if dst.char_ != u"▀":
                    dst.fg_color = dst.bg_color
                composite(&dst.fg_color[0], rgba_top, a_top)
                composite(&dst.bg_color[0], rgba_bot, a_bot)
            for gy in range(h // 2):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], rgba_top, a_top)
                    else:
                        graphics[oy + gy, ox + gx, 0] = dst.fg_color[0]
                        graphics[oy + gy, ox + gx, 1] = dst.fg_color[1]
                        graphics[oy + gy, ox + gx, 2] = dst.fg_color[2]
                        graphics[oy + gy, ox + gx, 3] = 1
            for gy in range(h // 2, h):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], rgba_bot, a_bot)
                    else:
                        graphics[oy + gy, ox + gx, 0] = dst.bg_color[0]
                        graphics[oy + gy, ox + gx, 1] = dst.bg_color[1]
                        graphics[oy + gy, ox + gx, 2] = dst.bg_color[2]
                        graphics[oy + gy, ox + gx, 3] = 1
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_sixel_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        RegionIterator it
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx

    init_iter(&it, cregion)
    while not it.done:
        oy = it.y * h
        ox = it.x * w
        src_y = h * (it.y - abs_y)
        src_x = w * (it.x - abs_x)
        kind[it.y, it.x] = SIXEL
        for gy in range(h):
            for gx in range(w):
                src = &self_texture[src_y + gy, src_x + gx, 0]
                dst = &graphics[oy + gy, ox + gx, 0]
                dst[0] = src[0]
                dst[1] = src[1]
                dst[2] = src[2]
                dst[3] = 1
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_sixel_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        RegionIterator it
        int src_y, src_x
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        uint8 *rgba
        double a

    init_iter(&it, cregion)
    while not it.done:
        oy = it.y * h
        ox = it.x * w
        src_y = oy - abs_y * h
        src_x = ox - abs_x * w
        if kind[it.y, it.x] == SIXEL:
            for gy in range(h):
                for gx in range(w):
                    rgba = &self_texture[src_y + gy, src_x + gx, 0]
                    if rgba[3]:
                        composite(
                            &graphics[oy + gy, ox + gx, 0],
                            rgba,
                            alpha * <double>rgba[3] / 255,
                        )
                        graphics[oy + gy, ox + gx, 3] = 1
        elif (
            cells[it.y, it.x].char_ != u" "
            and cells[it.y, it.x].char_ != u"▀"
            and one_color(self_texture, src_y, src_x, h, w)
        ):
            # If all rgba colors are equal we can treat the texture as a pane
            # so that glyphs underneath are shown.
            # TODO: Probably this feature could be applied if the texture was
            # *mostly* one color, or all the colors were very close to each other.
            # FIXME: Because the color fidelity of glyphs is higher than sixel,
            # this can create color artifacts in the displayed image. Not sure if
            # anything can be done about it?
            rgba = &self_texture[src_y, src_x, 0]
            if rgba[3]:
                a = alpha * <double>rgba[3]/ 255
                composite(&cells[it.y, it.x].fg_color[0], rgba, a)
                composite(&cells[it.y, it.x].bg_color[0], rgba, a)
        elif kind[it.y, it.x] == GLYPH:
            # ! Special case half-blocks
            # ! For other blitters, probably don't special case.
            kind[it.y, it.x] = SIXEL
            if cells[it.y, it.x].char_ == u"▀":
                for gy in range(h // 2):
                    for gx in range(w):
                        if composite_sixels_on_glyph(
                            &cells[it.y, it.x].fg_color[0],
                            &self_texture[src_y + gy, src_x + gx, 0],
                            &graphics[oy + gy, ox + gx, 0],
                            alpha,
                        ):
                            kind[it.y, it.x] = MIXED
                for gy in range(h // 2, h):
                    for gx in range(w):
                        if composite_sixels_on_glyph(
                            &cells[it.y, it.x].bg_color[0],
                            &self_texture[src_y + gy, src_x + gx, 0],
                            &graphics[oy + gy, ox + gx, 0],
                            alpha,
                        ):
                            kind[it.y, it.x] = MIXED
            else:
                for gy in range(h):
                    for gx in range(w):
                        if composite_sixels_on_glyph(
                            &cells[it.y, it.x].bg_color[0],
                            &self_texture[src_y + gy, src_x + gx, 0],
                            &graphics[oy + gy, ox + gx, 0],
                            alpha,
                        ):
                            kind[it.y, it.x] = MIXED
        elif kind[it.y, it.x] == MIXED:
            kind[it.y, it.x] = SIXEL
            for gy in range(h):
                for gx in range(w):
                    if not graphics[oy + gy, ox + gx, 3]:
                        kind[it.y, it.x] = MIXED
                        composite_sixels_on_glyph(
                            &cells[it.y, it.x].bg_color[0],
                            &self_texture[src_y + gy, src_x + gx, 0],
                            &graphics[oy + gy, ox + gx, 0],
                            alpha,
                        )
                    else:
                        rgba = &self_texture[src_y + gy, src_x + gx, 0]
                        if rgba[3]:
                            a = alpha * <double>rgba[3]/ 255
                            composite(&graphics[oy + gy, ox + gx, 0], rgba, a)
                            graphics[oy + gy, ox + gx, 3] = 1
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_braille_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
):
    cdef:
        RegionIterator it
        int src_y, src_x
        uint8[3] fg
        bint[8] pixels
        Cell *cell
        uint8 i
        double average_alpha
        unsigned long char_

    init_iter(&it, cregion)
    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        average_alpha = average_quant(
            &fg[0], &pixels[0], self_texture, src_y, src_x, 4, 2
        )
        if average_alpha:
            cell = &cells[it.y, it.x]
            char_ = 10240
            for i in range(8):
                if pixels[i]:
                    char_ += BRAILLE_ENUM[i]
            cell.char_ = char_
            cell.bold = False
            cell.italic = False
            cell.underline = False
            cell.strikethrough = False
            cell.overline = False
            cell.reverse = False
            cell.fg_color = cell.bg_color
            composite(&cell.fg_color[0], &fg[0], average_alpha)
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_braille_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        RegionIterator it
        int src_y, src_x
        bint[8] pixels
        Cell *cell
        uint8 i
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox
        uint8[3] rgb, fg
        double p, average_alpha
        unsigned long char_

    init_iter(&it, cregion)
    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        average_alpha = average_quant(
            &fg[0], &pixels[0], self_texture, src_y, src_x, 4, 2
        ) * alpha
        if not average_alpha:
            next_(&it)
            continue
        cell = &cells[it.y, it.x]
        char_ = 10240
        for i in range(8):
            if pixels[i]:
                char_ += BRAILLE_ENUM[i]
        cell.char_ = char_
        cell.bold = False
        cell.italic = False
        cell.underline = False
        cell.strikethrough = False
        cell.overline = False
        cell.reverse = False
        if kind[it.y, it.x] == SIXEL:
            oy = it.y * h
            ox = it.x * w
            average_graphics(&cell.bg_color[0], graphics[oy:oy + h, ox:ox + w])
            kind[it.y, it.x] = GLYPH
        elif kind[it.y, it.x] == MIXED:
            oy = it.y * h
            ox = it.x * w
            p = average_graphics(&rgb[0], graphics[oy:oy + h, ox: ox + w])
            lerp_rgb(&rgb[0], &cell.bg_color[0], p)
            kind[it.y, it.x] = GLYPH
        cell.fg_color = cell.bg_color
        composite(&cell.fg_color[0], &fg[0], average_alpha)
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
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

    if blitter == "full":
        if is_transparent:
            trans_full_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_full_graphics_render(cells, abs_y, abs_x, self_texture, cregion)
    elif blitter == "half":
        if is_transparent:
            trans_half_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_half_graphics_render(cells, abs_y, abs_x, self_texture, cregion)
    elif blitter == "braille":
        if is_transparent:
            trans_braille_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_braille_graphics_render(cells, abs_y, abs_x, self_texture, cregion)
    elif blitter == "sixel":
        if is_transparent:
            trans_sixel_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, alpha, cregion
            )
        else:
            opaque_sixel_graphics_render(
                cells, graphics, kind, abs_y, abs_x, self_texture, cregion
            )


@cython.boundscheck(False)
@cython.wraparound(False)
def cursor_render(
    Cell[:, ::1] cells,
    bold: bool | None,
    italic: bool | None,
    underline: bool | None,
    strikethrough: bool | None,
    overline: bool | None,
    reverse: bool | None,
    fg_color: tuple[int, int, int] | None,
    bg_color: tuple[int, int, int] | None,
    region: Region,
) -> None:
    cdef:
        CRegion *cregion = &region.cregion
        RegionIterator it
        Cell *dst

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        if bold is not None:
            dst.bold = bold
        if italic is not None:
            dst.italic = italic
        if underline is not None:
            dst.underline = underline
        if strikethrough is not None:
            dst.strikethrough = strikethrough
        if overline is not None:
            dst.overline = overline
        if reverse is not None:
            dst.reverse = reverse
        if fg_color is not None:
            dst.fg_color = fg_color
        if bg_color is not None:
            dst.bg_color = bg_color
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_text_field_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    Cell[::1] particles,
    CRegion *cregion
):
    cdef:
        size_t nparticles = particles.shape[0], i
        int py, px

    for i in range(nparticles):
        py = <int>coords[i][0] + abs_y
        px = <int>coords[i][1] + abs_x
        if contains(cregion, py, px):
            cells[py, px] = particles[i]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_text_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    Cell[::1] particles,
    double alpha,
    CRegion *cregion,
):
    cdef:
        size_t nparticles = particles.shape[0], i
        int py, px
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        uint8[3] rgb
        double p
        Cell *dst
        Cell *src

    for i in range(nparticles):
        py = <int>coords[i][0] + abs_y
        px = <int>coords[i][1] + abs_x
        if not contains(cregion, py, px):
            continue
        src = &particles[i]
        dst = &cells[py, px]
        # FIXME: Consider all whitespace?
        if src.char_ == u" " or src.char_ == u"⠀":
            if kind[py, px] != SIXEL:
                composite(&dst.fg_color[0], &src.bg_color[0], alpha)
                composite(&dst.bg_color[0], &src.bg_color[0], alpha)
            if kind[py, px] != GLYPH:
                oy = py * h
                ox = px * w
                for gy in range(h):
                    for gx in range(w):
                        if graphics[oy + gy, ox + gx, 3]:
                            composite(
                                &graphics[oy + gy, ox + gx, 0], &src.bg_color[0], alpha
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
            if kind[py, px] == SIXEL:
                oy = py * h
                ox = px * w
                average_graphics(&dst.bg_color[0], graphics[oy:oy + h, ox:ox + w])
            elif kind[py, px] == MIXED:
                oy = py * h
                ox = px * w
                p = average_graphics(&rgb[0], graphics[oy: oy + h, ox:ox + w])
                lerp_rgb(&rgb[0], &dst.bg_color[0], p)
            kind[py, px] = GLYPH
            composite(dst.bg_color, src.bg_color, alpha)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void text_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] abs_pos,
    bint is_transparent,
    double[:, ::1] coords,
    Cell[::1] particles,
    double alpha,
    Region region,
):
    cdef:
        int abs_y = abs_pos[0], abs_x = abs_pos[1]
        CRegion *cregion = &region.cregion

    if is_transparent:
        trans_text_field_render(
            cells, graphics, kind, abs_y, abs_x, coords, particles, alpha, cregion
        )
    else:
        opaque_text_field_render(cells, abs_y, abs_x, coords, particles, cregion)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_full_graphics_field_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    CRegion *cregion,
):
    cdef:
        size_t nparticles = particles.shape[0], i
        int py, px
        Cell *dst

    for i in range(nparticles):
        py = <int>coords[i][0] + abs_y
        px = <int>coords[i][1] + abs_x
        if not contains(cregion, py, px):
            continue
        dst = &cells[py, px]
        dst.char_ = u" "
        dst.bold = False
        dst.italic = False
        dst.underline = False
        dst.strikethrough = False
        dst.overline = False
        dst.reverse = False
        dst.bg_color[0] = particles[i, 0]
        dst.bg_color[1] = particles[i, 1]
        dst.bg_color[2] = particles[i, 2]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_full_graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        size_t nparticles = particles.shape[0], i
        int py, px
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx
        Cell *dst
        double a
        uint8 *src_rgba

    for i in range(nparticles):
        py = <int>coords[i][0] + abs_y
        px = <int>coords[i][1] + abs_x
        if not contains(cregion, py, px):
            continue
        src_rgba = &particles[i, 0]
        a = alpha * <double>src_rgba[3] / 255
        if kind[py, px] != SIXEL:
            dst = &cells[py, px]
            composite(&dst.fg_color[0], src_rgba, a)
            composite(&dst.bg_color[0], src_rgba, a)
        if kind[py, px] != GLYPH:
            oy = py * h
            ox = px * w
            for gy in range(h):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], src_rgba, a)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_half_graphics_field_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    CRegion *cregion,
):
    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx
        Cell *dst
        uint8 *dst_rgb

    for i in range(nparticles):
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        dst = &cells[ipy, ipx]
        dst.bold = False
        dst.italic = False
        dst.underline = False
        dst.strikethrough = False
        dst.overline = False
        dst.reverse = False
        if py - ipy < .5:
            dst_rgb = &dst.fg_color[0]
        else:
            dst_rgb = &dst.bg_color[0]
        if dst.char_ != u"▀":
            dst.fg_color = dst.bg_color
            dst.char_ = u"▀"
        dst_rgb[0] = particles[i, 0]
        dst_rgb[1] = particles[i, 1]
        dst_rgb[2] = particles[i, 2]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_half_graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx, gtop, gbot
        Cell *dst
        double a
        uint8 *src_rgba
        uint8 *dst_rgb

    for i in range(nparticles):
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        src_rgba = &particles[i, 0]
        a = alpha * <double>src_rgba[3] / 255
        dst = &cells[ipy, ipx]
        if kind[ipy, ipx] == GLYPH:
            dst.bold = False
            dst.italic = False
            dst.underline = False
            dst.strikethrough = False
            dst.overline = False
            dst.reverse = False
            if dst.char_ != u"▀":
                dst.fg_color = dst.bg_color
                dst.char_ = u"▀"
            if py - ipy < .5:
                composite(&dst.fg_color[0], src_rgba, a)
            else:
                composite(&dst.bg_color[0], src_rgba, a)
        else:
            if py - ipy <= .5:
                gtop = 0
                gbot = h // 2
                dst_rgb = &dst.fg_color[0]
            else:
                gtop = h // 2
                gbot = h
                dst_rgb = &dst.bg_color[0]
            if kind[ipy, ipx] == MIXED:
                kind[ipy, ipx] = SIXEL
                if dst.char_ != u"▀":
                    dst.fg_color = dst.bg_color
                composite(dst_rgb, src_rgba, a)
            oy = ipy * h
            ox = ipx * w
            for gy in range(gtop, gbot):
                for gx in range(w):
                    if graphics[oy + gy, ox + gx, 3]:
                        composite(&graphics[oy + gy, ox + gx, 0], src_rgba, a)
                    else:
                        graphics[oy + gy, ox + gx, 0] = dst_rgb[0]
                        graphics[oy + gy, ox + gx, 1] = dst_rgb[1]
                        graphics[oy + gy, ox + gx, 2] = dst_rgb[2]
                        graphics[oy + gy, ox + gx, 3] = 1


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_sixel_graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    CRegion *cregion,
):
    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx, pgy, pgx
        RegionIterator it

    for i in range(nparticles):
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        oy = ipy * h
        ox = ipx * w
        pgy = oy + <int>round((py - ipy) * h)
        if pgy >= graphics.shape[0]:
            continue
        pgx = ox + <int>round((px - ipx) * w)
        if pgx >= graphics.shape[1]:
            continue
        graphics[pgy, pgx] = particles[i]
        kind[ipy, ipx] = SIXEL

    # For all sixel cells in region, mark graphics as opaque:
    init_iter(&it, cregion)
    while not it.done:
        if kind[it.y, it.x] == SIXEL:
            oy = it.y * h
            ox = it.x * w
            for gy in range(h):
                for gx in range(w):
                    graphics[oy + gy, ox + gx, 3] = 1
        next_(&it)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_sixel_graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx, pgy, pgx

    for i in range(nparticles):
        if not particles[i, 3]:
            continue
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        oy = ipy * h
        ox = ipx * w
        pgy = oy + <int>round((py - ipy) * h)
        if pgy >= graphics.shape[0]:
            continue
        pgx = ox + <int>round((px - ipx) * w)
        if pgx >= graphics.shape[1]:
            continue
        if (
            kind[ipy, ipx] == GLYPH
            or kind[ipy, ipx] == MIXED and not graphics[pgy, pgx, 3]
        ):
            if cells[ipy, ipx].char_ == u"▀" and py - ipy < .5:
                graphics[pgy, pgx, 0] = cells[ipy, ipx].fg_color[0]
                graphics[pgy, pgx, 1] = cells[ipy, ipx].fg_color[1]
                graphics[pgy, pgx, 2] = cells[ipy, ipx].fg_color[2]
            else:
                graphics[pgy, pgx, 0] = cells[ipy, ipx].bg_color[0]
                graphics[pgy, pgx, 1] = cells[ipy, ipx].bg_color[1]
                graphics[pgy, pgx, 2] = cells[ipy, ipx].bg_color[2]
        composite(&graphics[pgy, pgx, 0], &particles[i, 0], alpha)
        graphics[pgy, pgx, 3] = 1
        kind[ipy, ipx] = SIXEL
        for gy in range(h):
            for gx in range(w):
                if not graphics[oy + gy, ox + gx, 3]:
                    kind[ipy, ipx] = MIXED
                    break


cdef struct BraillePixel:
    unsigned long char_
    double[4] total_fg
    unsigned int ncolors


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_braille_graphics_field_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    CRegion *cregion,
):
    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx, y, x, pgy, pgx
        size_t h, w
        Cell *dst

    bounding_rect(cregion, &y, &x, &h, &w)
    cdef:
        BraillePixel *pixels = <BraillePixel*>malloc(sizeof(BraillePixel) * h * w)
        BraillePixel *pixel

    if pixels is NULL:
        return
    memset(pixels, 0, sizeof(BraillePixel) * h * w)

    for i in range(nparticles):
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        pixel = &pixels[(ipy - y) * w + ipx - x]
        # ! Why isn't pixel.char_ == 0 sufficient?
        if pixel.char_ < 10240 or pixel.char_ > 10495:
            pixel.char_ = 10240
        pgy = <int>((py - ipy) * 4)
        pgx = <int>((px - ipx) * 2)
        pixel.char_ |= BRAILLE_ENUM[pgy * 2 + pgx]
        pixel.total_fg[0] += particles[i, 0]
        pixel.total_fg[1] += particles[i, 1]
        pixel.total_fg[2] += particles[i, 2]
        pixel.ncolors += 1

    for i in range(h * w):
        pixel = &pixels[i]
        # ! Why does pixel.char_ need to be checked?
        if not pixel.ncolors or pixel.char_ < 10240 or pixel.char_ > 10495:
            continue
        dst = &cells[(i // w) + y, (i % w) + x]
        dst.char_ = pixel.char_
        dst.bold = False
        dst.italic = False
        dst.underline = False
        dst.strikethrough = False
        dst.overline = False
        dst.reverse = False
        dst.fg_color[0] = <uint8>(pixel.total_fg[0] / pixel.ncolors)
        dst.fg_color[1] = <uint8>(pixel.total_fg[1] / pixel.ncolors)
        dst.fg_color[2] = <uint8>(pixel.total_fg[2] / pixel.ncolors)

    free(pixels)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_braille_graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    double alpha,
    CRegion *cregion,
):
    if alpha == 0:
        return

    cdef:
        size_t nparticles = particles.shape[0], i
        double py, px
        int ipy, ipx, y, x
        Cell *dst
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t rh, rw
        int pgy, pgx
        uint8[3] rgb

    bounding_rect(cregion, &y, &x, &rh, &rw)
    cdef:
        BraillePixel *pixels = <BraillePixel*>malloc(sizeof(BraillePixel) * rh * rw)
        BraillePixel *pixel

    if pixels is NULL:
        return
    memset(pixels, 0, sizeof(BraillePixel) * rh * rw)

    for i in range(nparticles):
        if not particles[i, 3]:
            continue
        py = coords[i][0] + abs_y
        ipy = <int>py
        px = coords[i][1] + abs_x
        ipx = <int>px
        if not contains(cregion, ipy, ipx):
            continue
        pixel = &pixels[(ipy - y) * rw + ipx - x]
        # ! Why isn't pixel.char_ == 0 sufficient?
        # ! Assumed if char_ is braille, that background has already been composited.
        if pixel.char_ < 10240 or pixel.char_ > 10495:
            pixel.char_ = 10240
            if kind[ipy, ipx] == SIXEL:
                oy = ipy * h
                ox = ipx * w
                average_graphics(
                    &cells[ipy, ipx].bg_color[0], graphics[oy:oy + h, ox:ox + w]
                )
                kind[ipy, ipx] = GLYPH
            elif kind[ipy, ipx] == MIXED:
                oy = ipy * h
                ox = ipx * w
                p = average_graphics(&rgb[0], graphics[oy:oy + h, ox: ox + w])
                lerp_rgb(&rgb[0], &cells[ipy, ipx].bg_color[0], p)
                kind[ipy, ipx] = GLYPH
            cells[ipy, ipx].fg_color = cells[ipy, ipx].bg_color
        kind[ipy, ipx] = GLYPH
        pgy = <int>((py - ipy) * 4)
        pgx = <int>((px - ipx) * 2)
        pixel.char_ |= BRAILLE_ENUM[pgy * 2 + pgx]
        pixel.total_fg[0] += particles[i, 0]
        pixel.total_fg[1] += particles[i, 1]
        pixel.total_fg[2] += particles[i, 2]
        pixel.total_fg[3] += particles[i, 3]
        pixel.ncolors += 1

    for i in range(rh * rw):
        pixel = &pixels[i]
        # ! Why does pixel.char_ need to be checked?
        if not pixel.ncolors or pixel.char_ < 10240 or pixel.char_ > 10495:
            continue
        dst = &cells[(i // rw) + y, (i % rw) + x]
        dst.char_ = pixel.char_
        dst.bold = False
        dst.italic = False
        dst.underline = False
        dst.strikethrough = False
        dst.overline = False
        dst.reverse = False

        rgb[0] = <uint8>(pixel.total_fg[0] / pixel.ncolors)
        rgb[1] = <uint8>(pixel.total_fg[1] / pixel.ncolors)
        rgb[2] = <uint8>(pixel.total_fg[2] / pixel.ncolors)
        composite(
            &dst.fg_color[0], &rgb[0], pixel.total_fg[3] / 255 / pixel.ncolors * alpha
        )
    free(pixels)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void graphics_field_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    tuple[int, int] abs_pos,
    str blitter,
    bint is_transparent,
    double[:, ::1] coords,
    uint8[:, ::1] particles,
    double alpha,
    Region region,
):
    cdef:
        int abs_y = abs_pos[0], abs_x = abs_pos[1]
        CRegion *cregion = &region.cregion

    if blitter == "full":
        if is_transparent:
            trans_full_graphics_field_render(
                cells,
                graphics,
                kind,
                abs_y,
                abs_x,
                coords,
                particles,
                alpha,
                cregion,
            )
        else:
            opaque_full_graphics_field_render(
                cells, abs_y, abs_x, coords, particles, cregion
            )
    elif blitter == "half":
        if is_transparent:
            trans_half_graphics_field_render(
                cells,
                graphics,
                kind,
                abs_y,
                abs_x,
                coords,
                particles,
                alpha,
                cregion,
            )
        else:
            opaque_half_graphics_field_render(
                cells, abs_y, abs_x, coords, particles, cregion
            )
    elif blitter == "braille":
        if is_transparent:
            trans_braille_graphics_field_render(
                cells,
                graphics,
                kind,
                abs_y,
                abs_x,
                coords,
                particles,
                alpha,
                cregion,
            )
        else:
            opaque_braille_graphics_field_render(
                cells, abs_y, abs_x, coords, particles, cregion
            )
    elif blitter == "sixel":
        if is_transparent:
            trans_sixel_graphics_field_render(
                cells,
                graphics,
                kind,
                abs_y,
                abs_x,
                coords,
                particles,
                alpha,
                cregion,
            )
        else:
            opaque_sixel_graphics_field_render(
                cells, graphics, kind, abs_y, abs_x, coords, particles, cregion
            )


cdef inline void write_sgr(fbuf *f, uint8 param, bint *first):
    if first[0]:
        fbuf_printf(f, "\x1b[%d", param)
        first[0] = 0
    else:
        fbuf_printf(f, ";%d", param)


cdef inline void write_rgb(fbuf *f, uint8 fg, uint8 *rgb, bint *first):
    if first[0]:
        fbuf_printf(f, "\x1b[%d;2;%d;%d;%d", fg, rgb[0], rgb[1], rgb[2])
        first[0] = 0
    else:
        fbuf_printf(f, ";%d;2;%d;%d;%d", fg, rgb[0], rgb[1], rgb[2])


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline void normalize_canvas(Cell[:, ::1] cells, int[:, ::1] widths):
    cdef size_t h = cells.shape[0], w = cells.shape[1], y, x

    # Try to prevent wide chars from clipping. If there is clipping,
    # replace wide chars with whitespace.

    for y in range(h):
        for x in range(w):
            widths[y, x] = cwidth(cells[y, x].char_)

    for y in range(h):
        for x in range(w):
            if (
                widths[y, x] == 0 and (x == 0 or widths[y, x - 1] != 2)
                or widths[y, x] == 2 and (x == w - 1 or widths[y, x + 1] != 0)
            ):
                cells[y, x].char_ = u" "
                widths[y, x] = 1


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline ssize_t write_glyph(
    fbuf *f,
    size_t oy,
    size_t ox,
    size_t y,
    size_t x,
    ssize_t *cursor_y,
    ssize_t *cursor_x,
    Cell[:, ::1] canvas,
    int[:, ::1] widths,
    Cell **last_sgr,
):
    if not widths[y, x]:
        return 0

    cdef:
        ssize_t abs_y = y + oy, abs_x = x + ox
        Cell *cell = &canvas[y, x]
        Cell *last = last_sgr[0]
        bint first = 1

    if abs_y == cursor_y[0]:
        if abs_x != cursor_x[0]:
            # CHA, Cursor Horizontal Absolute
            if fbuf_printf(f, "\x1b[%dG", abs_x + 1):
                return -1
            cursor_x[0] = abs_x
    else:
        # CUP, Cursor Position
        if fbuf_printf(f, "\x1b[%d;%dH", abs_y + 1, abs_x + 1):
            return -1
        cursor_y[0] = abs_y
        cursor_x[0] = abs_x

    if fbuf_grow(f, 128):
        return -1
    # Build up Select Graphic Rendition (SGR) parameters
    if last is NULL or cell.bold != last.bold:
        write_sgr(f, 1 if cell.bold else 22, &first)
    if last is NULL or cell.italic != last.italic:
        write_sgr(f, 3 if cell.italic else 23, &first)
    if last is NULL or cell.underline != last.underline:
        write_sgr(f, 4 if cell.underline else 24, &first)
    if last is NULL or cell.strikethrough != last.strikethrough:
        write_sgr(f, 9 if cell.strikethrough else 29, &first)
    if last is NULL or cell.overline != last.overline:
        write_sgr(f, 53 if cell.overline else 55, &first)
    if last is NULL or cell.reverse != last.reverse:
        write_sgr(f, 7 if cell.reverse else 27, &first)
    if last is NULL or not rgb_eq(&cell.fg_color[0], &last.fg_color[0]):
        write_rgb(f, 38, &cell.fg_color[0], &first)
    if last is NULL or not rgb_eq(&cell.bg_color[0], &last.bg_color[0]):
        write_rgb(f, 48, &cell.bg_color[0], &first)
    if not first:
        fbuf_putn(f, "m", 1)
    fbuf_putucs4(f, cell.char_)
    cursor_x[0] += widths[y, x]
    last_sgr[0] = cell
    return 0


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void terminal_render(
    Vt100Terminal terminal,
    bint resized,
    OctTree octree,
    tuple[int, int] app_pos,
    Cell[:, ::1] cells,
    Cell[:, ::1] prev_cells,
    int[:, ::1] widths,
    uint8[:, :, ::1] graphics,
    uint8[:, :, ::1] prev_graphics,
    uint8[:, :, ::1] sgraphics,
    uint8[:, ::1] kind,
    uint8[:, ::1] prev_kind,
    tuple[int, int] aspect_ratio,
):
    normalize_canvas(cells, widths)

    cdef:
        fbuf *f = &terminal.out_buf
        size_t h = cells.shape[0], w = cells.shape[1], y, x
        size_t cell_h = graphics_geom_height(cells, graphics)
        size_t cell_w = graphics_geom_width(cells, graphics)
        size_t gy, gx, gh, gw
        size_t min_y_sixel = h, min_x_sixel = w, max_y_sixel = 0, max_x_sixel = 0
        size_t oy = app_pos[0], ox = app_pos[1]
        ssize_t cursor_y = -1, cursor_x = -1
        Cell *last_sgr = NULL
        bint emit_sixel = 0
        unsigned int aspect_h = aspect_ratio[0], aspect_w = aspect_ratio[1]

    if fbuf_putn(f, "\x1b7", 2):  # Save cursor
        raise MemoryError

    for y in range(h):
        for x in range(w):
            if kind[y, x]:
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
        gy = min_y_sixel * cell_h
        gx = min_x_sixel * cell_w
        gh = (max_y_sixel + 1 - min_y_sixel) * cell_h
        # If sixel graphics rect reaches last line of terminal, its height must be
        # clipped to nearest multiple of 6 to prevent scrolling.
        if max_y_sixel + 1 == h:
            y = gh % 6
            if y:
                gh -= y
                # If sixel graphics height is clipped force repaint of sixel cells on
                # last line by changing to mixed cells.
                for x in range(min_x_sixel, max_x_sixel + 1):
                    if kind[max_y_sixel, x]:
                        kind[max_y_sixel, x] = MIXED

        for y in range(h):
            for x in range(w):
                if kind[y, x] == MIXED:
                    if write_glyph(
                        f, oy, ox, y, x, &cursor_y, &cursor_x, cells, widths, &last_sgr
                    ):
                        raise MemoryError

        if gh > 0:
            gw = (max_x_sixel + 1 - min_x_sixel) * cell_w
            if fbuf_printf(
                f, "\x1b[%d;%dH", min_y_sixel + 1 + oy, min_x_sixel + 1 + ox
            ):
                raise MemoryError
            if sixel(
                f, &octree.qs, graphics, sgraphics, aspect_h, aspect_w, gy, gx, gh, gw
            ):
                raise MemoryError

    cursor_y = -1
    cursor_x = -1
    for y in range(h):
        for x in range(w):
            if kind[y, x] == GLYPH and (
                resized
                or prev_kind[y, x]
                or (
                    emit_sixel
                    and min_y_sixel <= y <= max_y_sixel
                    and min_x_sixel <= x <= max_x_sixel
                )
                or not cell_eq(&cells[y, x], &prev_cells[y, x])
            ):
                if write_glyph(
                    f, oy, ox, y, x, &cursor_y, &cursor_x, cells, widths, &last_sgr
                ):
                    raise MemoryError

    if f.len == 2:
        f.len = 0  # Only 'Save Cursor' in buffer. Don't flush.
        return

    if fbuf_putn(f, "\x1b8", 2):  # Restore cursor
        raise MemoryError

    fbuf_flush_fd(f, terminal.stdout)
