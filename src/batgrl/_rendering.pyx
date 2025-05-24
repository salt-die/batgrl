from libc.math cimport round, pow
from libc.stdlib cimport div_t, free, div, malloc
from libc.string cimport memset

cimport cython
from uwcwidth cimport wcwidth_uint32, wcswidth

from ._rendering cimport Cell
from ._sixel cimport OctTree, sixel
from .colors import Color
from .geometry.regions cimport CRegion, Region, bounding_rect, contains
from .logging import LogLevel, get_logger
from .terminal._fbuf cimport (
    fbuf,
    fbuf_flush_fd,
    fbuf_grow,
    fbuf_printf,
    fbuf_putn,
    fbuf_putucs4,
)
from .terminal.vt100_terminal cimport Vt100Terminal
from .text_tools import EGC_POOL

logger = get_logger(__name__)

ctypedef unsigned char uint8
ctypedef unsigned long uint32
ctypedef enum CellKind: GLYPH, SIXEL, MIXED, SEE_THROUGH_SIXEL
cdef:
    unsigned int[8] BRAILLE_ENUM = [1, 8, 2, 16, 4, 32, 64, 128]
    uint8 BOLD = 0b000001
    uint8 ITALIC = 0b000010
    uint8 UNDERLINE = 0b000100
    uint8 STRIKETHROUGH = 0b001000
    uint8 OVERLINE = 0b010000
    uint8 REVERSE = 0b100000
    uint32 EGC_BASE = 0x180000
    uint32 SPACE_ORD = 0x20
    uint32 BRAILLE_ORD = 0x2800
    uint32 HALF_BLOCK_ORD = 0x2580
    uint32 END_OF_GEOMETRY_BLOCK_ORD = HALF_BLOCK_ORD + 0x20


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
        a.ord == b.ord
        and a.style == b.style
        and rgb_eq(&a.fg_color[0], &b.fg_color[0])
        and rgb_eq(&a.bg_color[0], &b.bg_color[0])
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline bint see_through_eq(
    Cell *a, Cell *b, uint8[:, :, ::1] g, uint8[:, :, ::1] pg
):
    return (
        a.ord == b.ord
        and a.style == b.style
        and rgb_eq(&a.fg_color[0], &b.fg_color[0])
        # Note that bg_color is not checked because color information for see-through
        # cells is stored in graphics.
        and all_eq(g, pg)
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


cdef inline bint composite_sixels_on_cell(
    uint8 *bg, uint8 *graphics, uint8 *rgba, double alpha
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
        uint32 r = 0, g = 0, b = 0, n = 0

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
    memset(&quant_fg, 0, sizeof(double) * 3)

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


cdef inline uint8 _100_to_uint8(uint8 c):
    return <uint8>(<double>c / 100.0 * 255.0)


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
        cell.ord = 32
        cell.style = 0
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
        if src.ord == SPACE_ORD or src.ord == BRAILLE_ORD:
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
            dst.ord = src.ord
            dst.style = src.style
            dst.fg_color = src.fg_color
            if kind[it.y, it.x] & SIXEL:
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
        cell.ord = 32
        cell.style = 0
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
        dst.ord = HALF_BLOCK_ORD
        dst.style = 0
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
        if rgba_eq(rgba_top, rgba_bot):  # FIXME: Use closeness instead of equality.
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
            dst.style = 0
            if dst.ord != HALF_BLOCK_ORD:
                dst.fg_color = dst.bg_color
                dst.ord = HALF_BLOCK_ORD
            composite(&dst.fg_color[0], rgba_top, a_top)
            composite(&dst.bg_color[0], rgba_bot, a_bot)
        else:
            oy = it.y * h
            ox = it.x * w
            if kind[it.y, it.x] == MIXED:
                kind[it.y, it.x] = SIXEL
                if dst.ord != HALF_BLOCK_ORD:
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
        src_y = <int>h * (it.y - abs_y)
        src_x = <int>w * (it.x - abs_x)
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


DEF VARIANCE_THRESHOLD = 100

cdef bint is_low_variance_region(
    uint8[:, :, ::1] texture, int src_y, int src_x, size_t h, size_t w, uint8 *rgba
):
    cdef:
        double[4] mean_rgba, variance
        int y, x
        size_t area = h * w

    memset(&mean_rgba, 0, sizeof(double) * 4)
    memset(&variance, 0, sizeof(double) * 4)

    for y in range(src_y, src_y + h):
        for x in range(src_x, src_x + w):
            mean_rgba[0] += <double>texture[y, x, 0]
            mean_rgba[1] += <double>texture[y, x, 1]
            mean_rgba[2] += <double>texture[y, x, 2]
            mean_rgba[3] += <double>texture[y, x, 3]

    mean_rgba[0] /= area
    mean_rgba[1] /= area
    mean_rgba[2] /= area
    mean_rgba[3] /= area
    rgba[0] = <uint8>mean_rgba[0]
    rgba[1] = <uint8>mean_rgba[1]
    rgba[2] = <uint8>mean_rgba[2]
    rgba[3] = <uint8>mean_rgba[3]

    for y in range(src_y, src_y + h):
        for x in range(src_x, src_x + w):
            variance[0] += pow(mean_rgba[0] - texture[y, x, 0], 2.0)
            variance[1] += pow(mean_rgba[1] - texture[y, x, 1], 2.0)
            variance[2] += pow(mean_rgba[2] - texture[y, x, 2], 2.0)
            variance[3] += pow(mean_rgba[3] - texture[y, x, 3], 2.0)

    variance[0] /= area
    variance[1] /= area
    variance[2] /= area
    variance[3] /= area

    return (
        variance[0] < VARIANCE_THRESHOLD
        and variance[1] < VARIANCE_THRESHOLD
        and variance[2] < VARIANCE_THRESHOLD
        and variance[3] < VARIANCE_THRESHOLD
    )


cdef:
    uint32[60] SEXTANT_REGIONS = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23,
        24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 43, 44,
        45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
    ]
    uint32[230] OCTANT_REGIONS = [
        4, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28,
        29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49,
        50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 65, 66, 67, 68, 69, 70, 71,
        72, 73, 74, 75, 76, 77, 78, 79, 81, 82, 83, 84, 86, 87, 88, 89, 91, 92, 93, 94,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111,
        112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127,
        129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144,
        145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 161,
        162, 163, 164, 166, 167, 168, 169, 171, 172, 173, 174, 176, 177, 178, 179, 180,
        181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196, 197,
        198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,
        214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229,
        230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 241, 242, 243, 244, 246, 247,
        248, 249, 251, 253, 254,
    ]
    uint32[8] SPECIAL_BLOCK_CHARS = [
        0x1cea0, 0x1cea3, 0x1cea8, 0x1ceab, 0x1fb82, 0x1fb85, 0x1fbe6, 0x1fbe7
    ]
    uint32[8] SPECIAL_REGIONS = [128, 64, 1, 2, 3, 63, 20, 40]


cdef bint is_block_char(uint32 ord_):
    if (
        ord_ == SPACE_ORD
        or HALF_BLOCK_ORD <= ord_ < END_OF_GEOMETRY_BLOCK_ORD  # geometric block
        or 0x1fb00 <= ord_ < 0x1fb3c  # sextants
        or 0x1cd00 <= ord_ < 0x1cde6  # octants
    ):
        return 1

    cdef int i
    for i in range(8):
        if ord_ == SPECIAL_BLOCK_CHARS[i]:  # missing octants in legacy block
            return 1

    return 0


ctypedef bint (*where_glyph)(double v, double u, uint32 region, uint8 block_height)

cdef struct where_fg_result:
    where_glyph where_fg
    uint32 region
    uint8 block_height


# The following functions are used to composite block glyphs onto sixel textures.
# Where they return 0, the background color is used to composite, else the foreground
# color.
cdef bint default_glyph(double v, double u, uint32 region, uint8 block_height):
    return 0

cdef bint upper_half(double v, double u, uint32 region, uint8 block_height):
    return v < .5

cdef bint lower_one_eighth(double v, double u, uint32 region, uint8 block_height):
    return v >= .875

cdef bint lower_one_quarter(double v, double u, uint32 region, uint8 block_height):
    return v >= .75

cdef bint lower_three_eighths(double v, double u, uint32 region, uint8 block_height):
    return v >= .625

cdef bint lower_half(double v, double u, uint32 region, uint8 block_height):
    return v >= .5

cdef bint lower_five_eighths(double v, double u, uint32 region, uint8 block_height):
    return v >= .375

cdef bint lower_three_quarters(double v, double u, uint32 region, uint8 block_height):
    return v >= .25

cdef bint lower_seven_eighths(double v, double u, uint32 region, uint8 block_height):
    return v >= .125

cdef bint full(double v, double u, uint32 region, uint8 block_height):
    return 1

cdef bint left_seven_eigths(double v, double u, uint32 region, uint8 block_height):
    return u < .875

cdef bint left_three_quarters(double v, double u, uint32 region, uint8 block_height):
    return u < .75

cdef bint left_five_eights(double v, double u, uint32 region, uint8 block_height):
    return u < .625

cdef bint left_half(double v, double u, uint32 region, uint8 block_height):
    return u < .5

cdef bint left_three_eighths(double v, double u, uint32 region, uint8 block_height):
    return u < .375

cdef bint left_one_quarter(double v, double u, uint32 region, uint8 block_height):
    return u < .25

cdef bint left_one_eighth(double v, double u, uint32 region, uint8 block_height):
    return u < .125

cdef bint right_half(double v, double u, uint32 region, uint8 block_height):
    return u >= .5

cdef bint light_shade(double v, double u, uint32 region, uint8 block_height):
    cdef int y = <int>(20.0 * v)
    cdef int x = <int>(10.0 * u)
    if y % 2 == 0:
        return x % 4 == 0
    return x % 4 == 2

cdef bint medium_shade(double v, double u, uint32 region, uint8 block_height):
    cdef int y = <int>(20.0 * v)
    cdef int x = <int>(10.0 * u)
    if y % 2 == 0:
        return x % 2 == 0
    return x % 2 == 1

cdef bint dark_shade(double v, double u, uint32 region, uint8 block_height):
    cdef int y = <int>(20.0 * v)
    cdef int x = <int>(10.0 * u)
    if y % 2 == 0:
        return x % 4 != 0
    return x % 4 != 2

cdef bint upper_one_eighth(double v, double u, uint32 region, uint8 block_height):
    return v < .125

cdef bint right_one_eighth(double v, double u, uint32 region, uint8 block_height):
    return u >= .875

cdef bint quadrant_lower_left(double v, double u, uint32 region, uint8 block_height):
    return v >= .5 and u < .5

cdef bint quadrant_lower_right(double v, double u, uint32 region, uint8 block_height):
    return v >= .5 and u >= .5

cdef bint quadrant_upper_left(double v, double u, uint32 region, uint8 block_height):
    return v < .5 and u < .5

cdef bint quadrant_upper_left_and_lower_left_and_lower_right(
    double v, double u, uint32 region, uint8 block_height
):
    return v >= .5 or u < .5

cdef bint quadrant_upper_left_and_lower_right(
    double v, double u, uint32 region, uint8 block_height
):
    return v < .5 and u < .5 or v >= .5 and u >= .5

cdef bint quadrant_upper_left_and_upper_right_and_lower_left(
    double v, double u, uint32 region, uint8 block_height
):
    return v < .5 or u < .5

cdef bint quadrant_upper_left_and_upper_right_and_lower_right(
    double v, double u, uint32 region, uint8 block_height
):
    return v < .5 or u >= .5

cdef bint quadrant_upper_right(double v, double u, uint32 region, uint8 block_height):
    return v < .5 and u >= .5

cdef bint quadrant_upper_right_and_lower_left(
    double v, double u, uint32 region, uint8 block_height
):
    return v < .5 and u >= .5 or v >= .5 and u < .5

cdef bint quadrant_upper_right_and_lower_left_and_lower_right(
    double v, double u, uint32 region, uint8 block_height
):
    return v >= .5 or u >= .5

cdef where_glyph[32] where_glyphs = [
    upper_half,
    lower_one_eighth,
    lower_one_quarter,
    lower_three_eighths,
    lower_half,
    lower_five_eighths,
    lower_three_quarters,
    lower_seven_eighths,
    full,
    left_seven_eigths,
    left_three_quarters,
    left_five_eights,
    left_half,
    left_three_eighths,
    left_one_quarter,
    left_one_eighth,
    right_half,
    light_shade,
    medium_shade,
    dark_shade,
    upper_one_eighth,
    right_one_eighth,
    quadrant_lower_left,
    quadrant_lower_right,
    quadrant_upper_left,
    quadrant_upper_left_and_lower_left_and_lower_right,
    quadrant_upper_left_and_lower_right,
    quadrant_upper_left_and_upper_right_and_lower_left,
    quadrant_upper_left_and_upper_right_and_lower_right,
    quadrant_upper_right,
    quadrant_upper_right_and_lower_left,
    quadrant_upper_right_and_lower_left_and_lower_right,
]


cdef bint block_char_legacy_block(
    double v, double u, uint32 region, uint8 block_height
):
    cdef uint32 reg_enum = 2 * <uint32>(v * block_height)
    if u >= .5:
        reg_enum += 1
    return (1 << reg_enum) & region


cdef inline where_fg_result get_where_fg(uint32 ord_):
    cdef:
        where_fg_result result
        int i

    result.where_fg = default_glyph
    if HALF_BLOCK_ORD <= ord_ < END_OF_GEOMETRY_BLOCK_ORD:
        result.where_fg = where_glyphs[<unsigned int>ord_ - HALF_BLOCK_ORD]
    elif 0x1fb00 <= ord_ < 0x1fb3c:  # sextants
        result.where_fg = block_char_legacy_block
        result.region = SEXTANT_REGIONS[ord_ - 0x1fb00]
        result.block_height = 3
    elif 0x1cd00 <= ord_ < 0x1cde6:  # octants
        result.where_fg = block_char_legacy_block
        result.region = OCTANT_REGIONS[ord_ - 0x1cd00]
        result.block_height = 4
    else:
        for i in range(8):
            if ord_ == SPECIAL_BLOCK_CHARS[i]:
                result.where_fg = block_char_legacy_block
                result.region = SPECIAL_REGIONS[i]
                result.block_height = 4
                break
    return result


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
        int h = <int>graphics_geom_height(cells, graphics)
        int w = <int>graphics_geom_width(cells, graphics)
        int oy, ox, gy, gx, y, x
        uint8 *rgba
        uint8[4] mean
        double a
        where_fg_result where_fg
        Cell *cell

    init_iter(&it, cregion)
    while not it.done:
        cell = &cells[it.y, it.x]
        oy = it.y * h
        ox = it.x * w
        src_y = oy - abs_y * h
        src_x = ox - abs_x * w
        if kind[it.y, it.x] & SIXEL:  # SIXEL or SEE_THROUGH_SIXEL:
            if (
                kind[it.y, it.x] == SEE_THROUGH_SIXEL
                and is_low_variance_region(self_texture, src_y, src_x, h, w, &mean[0])
            ):
                a = alpha * <double>mean[3] / 255
                composite(&cell.fg_color[0], &mean[0], a)
                composite(&mean[0], &graphics[oy, ox, 0], 1 - a)
                for y in range(h):
                    for x in range(w):
                        gy = oy + y
                        gx = ox + x
                        graphics[gy, gx, 0] = mean[0]
                        graphics[gy, gx, 1] = mean[1]
                        graphics[gy, gx, 2] = mean[2]
                        graphics[gy, gx, 3] = 1
            else:
                kind[it.y, it.x] = SIXEL
                for y in range(h):
                    for x in range(w):
                        gy = oy + y
                        gx = ox + x
                        rgba = &self_texture[src_y + y, src_x + x, 0]
                        if rgba[3]:
                            a = alpha * <double>rgba[3] / 255
                            composite(&graphics[gy, gx, 0], rgba, a)
                            graphics[gy, gx, 3] = 1
        elif kind[it.y, it.x] == MIXED:
            kind[it.y, it.x] = SIXEL
            where_fg = get_where_fg(cell.ord)
            for y in range(h):
                for x in range(w):
                    gy = oy + y
                    gx = ox + x
                    if graphics[gy, gx, 3]:
                        rgba = &self_texture[src_y + y, src_x + x, 0]
                        if rgba[3]:
                            a = alpha * <double>rgba[3]/ 255
                            composite(&graphics[gy, gx, 0], rgba, a)
                    elif self_texture[src_y + y, src_x + x, 3]:
                        if where_fg.where_fg(
                            y / h, x / w, where_fg.region, where_fg.block_height
                        ):
                            rgba = &cell.fg_color[0]
                        else:
                            rgba = &cell.bg_color[0]
                        composite_sixels_on_cell(
                            rgba,
                            &graphics[gy, gx, 0],
                            &self_texture[src_y + y, src_x + x, 0],
                            alpha,
                        )
                    else:
                        kind[it.y, it.x] = MIXED
        else:  # GLYPH
            if (
                not is_block_char(cell.ord)
                and is_low_variance_region(self_texture, src_y, src_x, h, w, &mean[0])
            ):
                if mean[3]:
                    kind[it.y, it.x] = SEE_THROUGH_SIXEL
                    a = alpha * <double>mean[3] / 255
                    composite(&cell.fg_color[0], &mean[0], a)
                    # Compositing onto graphics, to be copied back to cell after
                    # quantization, see additional notes in `terminal_render`. Need to
                    # invert alpha:
                    composite(&mean[0], &cell.bg_color[0], 1 - a)
                    for y in range(h):
                        for x in range(w):
                            gy = oy + y
                            gx = ox + x
                            graphics[gy, gx, 0] = mean[0]
                            graphics[gy, gx, 1] = mean[1]
                            graphics[gy, gx, 2] = mean[2]
                            graphics[gy, gx, 3] = 1
                else:
                    kind[it.y, it.x] = GLYPH
                    for y in range(h):
                        for x in range(w):
                            graphics[oy + y, ox + x, 3] = 0
            else:
                kind[it.y, it.x] = SIXEL
                where_fg = get_where_fg(cell.ord)
                for y in range(h):
                    for x in range(w):
                        if where_fg.where_fg(
                            y / h, x / w, where_fg.region, where_fg.block_height
                        ):
                            rgba = &cell.fg_color[0]
                        else:
                            rgba = &cell.bg_color[0]
                        if composite_sixels_on_cell(
                            rgba,
                            &graphics[oy + y, ox + x, 0],
                            &self_texture[src_y + y, src_x + x, 0],
                            alpha,
                        ):
                            kind[it.y, it.x] = MIXED
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
        uint32 ord_

    init_iter(&it, cregion)
    while not it.done:
        src_y = 4 * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        average_alpha = average_quant(
            &fg[0], &pixels[0], self_texture, src_y, src_x, 4, 2
        )
        if average_alpha:
            cell = &cells[it.y, it.x]
            ord_ = 10240
            for i in range(8):
                if pixels[i]:
                    ord_ += BRAILLE_ENUM[i]
            cell.ord = ord_
            cell.style = 0
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
        uint32 ord_

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
        ord_ = 10240
        for i in range(8):
            if pixels[i]:
                ord_ += BRAILLE_ENUM[i]
        cell.ord = ord_
        cell.style = 0
        if kind[it.y, it.x] & SIXEL:
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


cdef:
    # " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"
    uint32[16] QUADS = [
        0x20, 0x2598, 0x259d, 0x2580, 0x2596, 0x258c, 0x259e, 0x259b,
        0x2597, 0x259a, 0x2590, 0x259c, 0x2584, 0x2599, 0x259f, 0x2588,
    ]
    # " 🬀🬁🬂🬃🬄🬅🬆🬇🬈🬉🬊🬋🬌🬍🬎🬏🬐🬑🬒🬓▌🬔🬕🬖🬗🬘🬙🬚🬛🬜🬝🬞🬟🬠🬡🬢🬣🬤🬥🬦🬧▐🬨🬩🬪🬫🬬🬭🬮🬯🬰🬱🬲🬳🬴🬵🬶🬷🬸🬹🬺🬻█"
    uint32[64] SEXTANTS = [
        0x20, 0x1fb00, 0x1fb01, 0x1fb02, 0x1fb03, 0x1fb04, 0x1fb05, 0x1fb06,
        0x1fb07, 0x1fb08, 0x1fb09, 0x1fb0a, 0x1fb0b, 0x1fb0c, 0x1fb0d, 0x1fb0e,
        0x1fb0f, 0x1fb10, 0x1fb11, 0x1fb12, 0x1fb13, 0x258c, 0x1fb14, 0x1fb15,
        0x1fb16, 0x1fb17, 0x1fb18, 0x1fb19, 0x1fb1a, 0x1fb1b, 0x1fb1c, 0x1fb1d,
        0x1fb1e, 0x1fb1f, 0x1fb20, 0x1fb21, 0x1fb22, 0x1fb23, 0x1fb24, 0x1fb25,
        0x1fb26, 0x1fb27, 0x2590, 0x1fb28, 0x1fb29, 0x1fb2a, 0x1fb2b, 0x1fb2c,
        0x1fb2d, 0x1fb2e, 0x1fb2f, 0x1fb30, 0x1fb31, 0x1fb32, 0x1fb33, 0x1fb34,
        0x1fb35, 0x1fb36, 0x1fb37, 0x1fb38, 0x1fb39, 0x1fb3a, 0x1fb3b, 0x2588,
    ]
    # " 𜺨𜺫🮂𜴀▘𜴁𜴂𜴃𜴄▝𜴅𜴆𜴇𜴈▀𜴉𜴊𜴋𜴌🯦𜴍𜴎𜴏𜴐𜴑𜴒𜴓𜴔𜴕𜴖𜴗𜴘𜴙𜴚𜴛𜴜𜴝𜴞𜴟🯧𜴠𜴡𜴢𜴣𜴤𜴥𜴦𜴧𜴨𜴩𜴪𜴫𜴬𜴭𜴮𜴯𜴰𜴱𜴲𜴳𜴴𜴵🮅"
    # "𜺣𜴶𜴷𜴸𜴹𜴺𜴻𜴼𜴽𜴾𜴿𜵀𜵁𜵂𜵃𜵄▖𜵅𜵆𜵇𜵈▌𜵉𜵊𜵋𜵌▞𜵍𜵎𜵏𜵐▛𜵑𜵒𜵓𜵔𜵕𜵖𜵗𜵘𜵙𜵚𜵛𜵜𜵝𜵞𜵟𜵠𜵡𜵢𜵣𜵤𜵥𜵦𜵧𜵨𜵩𜵪𜵫𜵬𜵭𜵮𜵯𜵰"
    # "𜺠𜵱𜵲𜵳𜵴𜵵𜵶𜵷𜵸𜵹𜵺𜵻𜵼𜵽𜵾𜵿𜶀𜶁𜶂𜶃𜶄𜶅𜶆𜶇𜶈𜶉𜶊𜶋𜶌𜶍𜶎𜶏▗𜶐𜶑𜶒𜶓▚𜶔𜶕𜶖𜶗▐𜶘𜶙𜶚𜶛▜𜶜𜶝𜶞𜶟𜶠𜶡𜶢𜶣𜶤𜶥𜶦𜶧𜶨𜶩𜶪𜶫"
    # "▂𜶬𜶭𜶮𜶯𜶰𜶱𜶲𜶳𜶴𜶵𜶶𜶷𜶸𜶹𜶺𜶻𜶼𜶽𜶾𜶿𜷀𜷁𜷂𜷃𜷄𜷅𜷆𜷇𜷈𜷉𜷊𜷋𜷌𜷍𜷎𜷏𜷐𜷑𜷒𜷓𜷔𜷕𜷖𜷗𜷘𜷙𜷚▄𜷛𜷜𜷝𜷞▙𜷟𜷠𜷡𜷢▟𜷣▆𜷤𜷥█"
    uint32[256] OCTANTS = [
        0x20, 0x1cea8, 0x1ceab, 0x1fb82, 0x1cd00, 0x2598, 0x1cd01, 0x1cd02,
        0x1cd03, 0x1cd04, 0x259d, 0x1cd05, 0x1cd06, 0x1cd07, 0x1cd08, 0x2580,
        0x1cd09, 0x1cd0a, 0x1cd0b, 0x1cd0c, 0x1fbe6, 0x1cd0d, 0x1cd0e, 0x1cd0f,
        0x1cd10, 0x1cd11, 0x1cd12, 0x1cd13, 0x1cd14, 0x1cd15, 0x1cd16, 0x1cd17,
        0x1cd18, 0x1cd19, 0x1cd1a, 0x1cd1b, 0x1cd1c, 0x1cd1d, 0x1cd1e, 0x1cd1f,
        0x1fbe7, 0x1cd20, 0x1cd21, 0x1cd22, 0x1cd23, 0x1cd24, 0x1cd25, 0x1cd26,
        0x1cd27, 0x1cd28, 0x1cd29, 0x1cd2a, 0x1cd2b, 0x1cd2c, 0x1cd2d, 0x1cd2e,
        0x1cd2f, 0x1cd30, 0x1cd31, 0x1cd32, 0x1cd33, 0x1cd34, 0x1cd35, 0x1fb85,
        0x1cea3, 0x1cd36, 0x1cd37, 0x1cd38, 0x1cd39, 0x1cd3a, 0x1cd3b, 0x1cd3c,
        0x1cd3d, 0x1cd3e, 0x1cd3f, 0x1cd40, 0x1cd41, 0x1cd42, 0x1cd43, 0x1cd44,
        0x2596, 0x1cd45, 0x1cd46, 0x1cd47, 0x1cd48, 0x258c, 0x1cd49, 0x1cd4a,
        0x1cd4b, 0x1cd4c, 0x259e, 0x1cd4d, 0x1cd4e, 0x1cd4f, 0x1cd50, 0x259b,
        0x1cd51, 0x1cd52, 0x1cd53, 0x1cd54, 0x1cd55, 0x1cd56, 0x1cd57, 0x1cd58,
        0x1cd59, 0x1cd5a, 0x1cd5b, 0x1cd5c, 0x1cd5d, 0x1cd5e, 0x1cd5f, 0x1cd60,
        0x1cd61, 0x1cd62, 0x1cd63, 0x1cd64, 0x1cd65, 0x1cd66, 0x1cd67, 0x1cd68,
        0x1cd69, 0x1cd6a, 0x1cd6b, 0x1cd6c, 0x1cd6d, 0x1cd6e, 0x1cd6f, 0x1cd70,
        0x1cea0, 0x1cd71, 0x1cd72, 0x1cd73, 0x1cd74, 0x1cd75, 0x1cd76, 0x1cd77,
        0x1cd78, 0x1cd79, 0x1cd7a, 0x1cd7b, 0x1cd7c, 0x1cd7d, 0x1cd7e, 0x1cd7f,
        0x1cd80, 0x1cd81, 0x1cd82, 0x1cd83, 0x1cd84, 0x1cd85, 0x1cd86, 0x1cd87,
        0x1cd88, 0x1cd89, 0x1cd8a, 0x1cd8b, 0x1cd8c, 0x1cd8d, 0x1cd8e, 0x1cd8f,
        0x2597, 0x1cd90, 0x1cd91, 0x1cd92, 0x1cd93, 0x259a, 0x1cd94, 0x1cd95,
        0x1cd96, 0x1cd97, 0x2590, 0x1cd98, 0x1cd99, 0x1cd9a, 0x1cd9b, 0x259c,
        0x1cd9c, 0x1cd9d, 0x1cd9e, 0x1cd9f, 0x1cda0, 0x1cda1, 0x1cda2, 0x1cda3,
        0x1cda4, 0x1cda5, 0x1cda6, 0x1cda7, 0x1cda8, 0x1cda9, 0x1cdaa, 0x1cdab,
        0x2582, 0x1cdac, 0x1cdad, 0x1cdae, 0x1cdaf, 0x1cdb0, 0x1cdb1, 0x1cdb2,
        0x1cdb3, 0x1cdb4, 0x1cdb5, 0x1cdb6, 0x1cdb7, 0x1cdb8, 0x1cdb9, 0x1cdba,
        0x1cdbb, 0x1cdbc, 0x1cdbd, 0x1cdbe, 0x1cdbf, 0x1cdc0, 0x1cdc1, 0x1cdc2,
        0x1cdc3, 0x1cdc4, 0x1cdc5, 0x1cdc6, 0x1cdc7, 0x1cdc8, 0x1cdc9, 0x1cdca,
        0x1cdcb, 0x1cdcc, 0x1cdcd, 0x1cdce, 0x1cdcf, 0x1cdd0, 0x1cdd1, 0x1cdd2,
        0x1cdd3, 0x1cdd4, 0x1cdd5, 0x1cdd6, 0x1cdd7, 0x1cdd8, 0x1cdd9, 0x1cdda,
        0x2584, 0x1cddb, 0x1cddc, 0x1cddd, 0x1cdde, 0x2599, 0x1cddf, 0x1cde0,
        0x1cde1, 0x1cde2, 0x259f, 0x1cde3, 0x2586, 0x1cde4, 0x1cde5, 0x2588,
    ]


cdef inline uint32 block_quant(
    uint8 *fg,
    uint8 *bg,
    uint8[3] *pixels,
    uint32 *luminances,
    uint8 h,
):
    # See: https://en.wikipedia.org/wiki/Color_Cell_Compression
    cdef:
        uint8 nfg = 0, nbg = 0, i, n = 2 * h
        uint32 average_luminance = 0, glyph_index = 0
        double[3] total_fg, total_bg

    memset(&total_fg, 0, sizeof(double) * 3)
    memset(&total_bg, 0, sizeof(double) * 3)
    for i in range(n):
        luminances[i] = (
            3 * <uint32>pixels[i][0]
            + 10 * <uint32>pixels[i][1]
            + <uint32>pixels[i][2]
        ) // 14

    for i in range(n):
        average_luminance += luminances[i]
    average_luminance //= n

    for i in range(n):
        if luminances[i] < average_luminance:
            total_bg[0] += pixels[i][0]
            total_bg[1] += pixels[i][1]
            total_bg[2] += pixels[i][2]
            nbg += 1
        else:
            total_fg[0] += pixels[i][0]
            total_fg[1] += pixels[i][1]
            total_fg[2] += pixels[i][2]
            nfg += 1
            glyph_index += 1 << i

    if nbg:
        total_bg[0] /= nbg
        total_bg[1] /= nbg
        total_bg[2] /= nbg
    if nfg:
        total_fg[0] /= nfg
        total_fg[1] /= nfg
        total_fg[2] /= nfg
    else:
        total_fg[0] = total_bg[0]
        total_fg[1] = total_bg[1]
        total_fg[2] = total_bg[2]
    if not nbg:
        total_bg[0] = total_fg[0]
        total_bg[1] = total_fg[1]
        total_bg[2] = total_fg[2]

    fg[0] = <uint8>total_fg[0]
    fg[1] = <uint8>total_fg[1]
    fg[2] = <uint8>total_fg[2]
    bg[0] = <uint8>total_bg[0]
    bg[1] = <uint8>total_bg[1]
    bg[2] = <uint8>total_bg[2]

    return glyph_index


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void opaque_block_char_graphics_render(
    Cell[:, ::1] cells,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    CRegion *cregion,
    uint8 block_height,
):
    cdef:
        RegionIterator it
        int src_y, src_x, y, x
        Cell *dst
        uint32 *glyphs
        uint8 i, n = block_height * 2
        div_t div_result
        uint8[3] fg, bg
        uint8[8][3] pixels
        uint32[8] luminances

    if block_height == 2:
        glyphs = &QUADS[0]
    elif block_height == 3:
        glyphs = &SEXTANTS[0]
    else:  # == 4
        glyphs = &OCTANTS[0]

    init_iter(&it, cregion)
    while not it.done:
        src_y = block_height * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        for i in range(n):
            div_result = div(i, 2)
            y = src_y + div_result.quot
            x = src_x + div_result.rem
            pixels[i][0] = self_texture[y, x][0]
            pixels[i][1] = self_texture[y, x][1]
            pixels[i][2] = self_texture[y, x][2]

        dst = &cells[it.y, it.x]
        dst.ord = glyphs[
            block_quant(&fg[0], &bg[0], &pixels[0], &luminances[0], block_height)
        ]
        dst.style = 0
        dst.fg_color = fg
        dst.bg_color = bg
        next_(&it)


cdef bint is_low_variance_pixels(uint8[3] *pixels, uint8 n):
    cdef:
        double[3] mean_rgb, variance
        uint8 i

    memset(&mean_rgb, 0, sizeof(double) * 3)
    memset(&variance, 0, sizeof(double) * 3)

    for i in range(n):
        mean_rgb[0] += <double>pixels[i][0]
        mean_rgb[1] += <double>pixels[i][1]
        mean_rgb[2] += <double>pixels[i][2]
    mean_rgb[0] /= n
    mean_rgb[1] /= n
    mean_rgb[2] /= n
    for i in range(n):
        variance[0] += pow(mean_rgb[0] - pixels[i][0], 2.0)
        variance[1] += pow(mean_rgb[1] - pixels[i][1], 2.0)
        variance[2] += pow(mean_rgb[2] - pixels[i][2], 2.0)
    variance[0] /= n
    variance[1] /= n
    variance[2] /= n
    return (
        variance[0] < VARIANCE_THRESHOLD
        and variance[1] < VARIANCE_THRESHOLD
        and variance[2] < VARIANCE_THRESHOLD
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trans_block_char_graphics_render(
    Cell[:, ::1] cells,
    uint8[:, :, ::1] graphics,
    uint8[:, ::1] kind,
    int abs_y,
    int abs_x,
    uint8[:, :, ::1] self_texture,
    double alpha,
    CRegion *cregion,
    uint8 block_height,
):
    cdef:
        RegionIterator it
        Cell *dst
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        int src_y, src_x
        size_t oy, ox, y, x, gy, gx, ty, tx
        div_t div_result
        double[4] average_rgba
        double a
        uint8 i, n = block_height * 2
        uint8[3] fg, bg
        uint8[4] mean_rbga
        uint8[8][3] pixels
        uint32[8] luminances
        uint32 *glyphs
        uint32 glyph_index

    if block_height == 2:
        glyphs = &QUADS[0]
    elif block_height == 3:
        glyphs = &SEXTANTS[0]
    else:  # == 4
        glyphs = &OCTANTS[0]

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        src_y = block_height * (it.y - abs_y)
        src_x = 2 * (it.x - abs_x)
        oy = it.y * h
        ox = it.x * w

        if (
            kind[it.y, it.x] == SEE_THROUGH_SIXEL
            and is_low_variance_region(
                self_texture, src_y, src_x, block_height, 2, &mean_rbga[0]
            )
        ):
            a = alpha * <double>mean_rbga[3] / 255
            composite(&dst.fg_color[0], &mean_rbga[0], a)
            composite(&mean_rbga[0], &graphics[oy, ox, 0], 1 - a)
            for y in range(h):
                for x in range(w):
                    gy = oy + y
                    gx = ox + x
                    graphics[gy, gx, 0] = mean_rbga[0]
                    graphics[gy, gx, 1] = mean_rbga[1]
                    graphics[gy, gx, 2] = mean_rbga[2]
                    graphics[gy, gx, 3] = 1
        elif kind[it.y, it.x] != GLYPH:
            kind[it.y, it.x] = SIXEL
            for y in range(h):
                for x in range(w):
                    gy = oy + y
                    gx = ox + x
                    if not graphics[gy, gx, 3]:
                        graphics[gy, gx, 0] = dst.bg_color[0]
                        graphics[gy, gx, 1] = dst.bg_color[1]
                        graphics[gy, gx, 2] = dst.bg_color[2]
                        graphics[gy, gx, 3] = 1
                    ty = src_y + <size_t>(y / h * <double>block_height)
                    tx = src_x
                    if x / w >= .5:
                        tx += 1
                    a = alpha * <double>self_texture[ty, tx, 3] / 255
                    composite(&graphics[gy, gx, 0], &self_texture[ty, tx, 0], a)
        else:
            memset(&average_rgba, 0, sizeof(double) * 4)
            for i in range(n):
                div_result = div(i, 2)
                y = src_y + div_result.quot
                x = src_x + div_result.rem
                average_rgba[0] += <double>self_texture[y, x, 0]
                average_rgba[1] += <double>self_texture[y, x, 1]
                average_rgba[2] += <double>self_texture[y, x, 2]
                average_rgba[3] += <double>self_texture[y, x, 3]
                a = alpha * <double>self_texture[y, x, 3] / 255
                pixels[i] = dst.bg_color
                composite(&pixels[i][0], &self_texture[y, x, 0], a)
            if is_low_variance_pixels(&pixels[0], n):
                fg[0] = <uint8>(average_rgba[0] / n)
                fg[1] = <uint8>(average_rgba[1] / n)
                fg[2] = <uint8>(average_rgba[2] / n)
                a = alpha * average_rgba[3] / n / 255
                composite(&dst.fg_color[0], &fg[0], a)
                composite(&dst.bg_color[0], &fg[0], a)
            else:
                glyph_index = block_quant(
                    &fg[0], &bg[0], &pixels[0], &luminances[0], block_height
                )
                dst.ord = glyphs[glyph_index]
                dst.style = 0
                dst.fg_color = fg
                dst.bg_color = bg
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
        CRegion *cregion = &region.cregion
        int abs_y = abs_pos[0], abs_x = abs_pos[1]
        uint8 block_height

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
    else:
        if blitter == "sextant":
            block_height = 3
        elif blitter == "octant":
            block_height = 4
        else:
            block_height = 2
        if is_transparent:
            trans_block_char_graphics_render(
                cells,
                graphics,
                kind,
                abs_y,
                abs_x,
                self_texture,
                alpha,
                cregion,
                block_height,
            )
        else:
            opaque_block_char_graphics_render(
                cells, abs_y, abs_x, self_texture, cregion, block_height
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
    fg_color: Color | None,
    bg_color: Color | None,
    region: Region,
) -> None:
    cdef:
        CRegion *cregion = &region.cregion
        RegionIterator it
        Cell *dst
        unsigned char off = 255, on = 0

    if bold is not None:
        if bold:
            on |= BOLD
        else:
            off ^= BOLD
    if italic is not None:
        if italic:
            on |= ITALIC
        else:
            off ^= ITALIC
    if underline is not None:
        if underline:
            on |= UNDERLINE
        else:
            off ^= UNDERLINE
    if strikethrough is not None:
        if strikethrough:
            on |= STRIKETHROUGH
        else:
            off ^= STRIKETHROUGH
    if overline is not None:
        if overline:
            on |= OVERLINE
        else:
            off ^= OVERLINE
    if reverse is not None:
        if reverse:
            on |= REVERSE
        else:
            off ^= REVERSE

    init_iter(&it, cregion)
    while not it.done:
        dst = &cells[it.y, it.x]
        dst.style |= on
        dst.style &= off
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
        size_t nparticles = particles.shape[0], i, j, cwidth
        int py, px

    for i in range(nparticles):
        py = <int>coords[i][0] + abs_y
        px = <int>coords[i][1] + abs_x
        if contains(cregion, py, px):
            if particles[i].ord & EGC_BASE:
                cwidth = wcswidth(EGC_POOL[particles[i].ord - EGC_BASE])
            else:
                cwidth = wcwidth_uint32(particles[i].ord)
            if cwidth == 1:
                cells[py, px] = particles[i]
            elif cwidth > 1:
                if contains(cregion, py, px + <int>cwidth - 1):
                    cells[py, px] = particles[i]
                    for j in range(1, cwidth):
                        cells[py, px + j].ord = 0
                        cells[py, px + j].bg_color = particles[i].bg_color


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
        size_t nparticles = particles.shape[0], i, j
        int py, px
        size_t h = graphics_geom_height(cells, graphics)
        size_t w = graphics_geom_width(cells, graphics)
        size_t oy, ox, gy, gx, cwidth
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
        if src.ord == SPACE_ORD or src.ord == BRAILLE_ORD:
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
            if particles[i].ord & EGC_BASE:
                cwidth = wcswidth(EGC_POOL[particles[i].ord - EGC_BASE])
            else:
                cwidth = wcwidth_uint32(particles[i].ord)
            if cwidth > 1:
                if contains(cregion, py, px + <int>cwidth - 1):
                    for j in range(1, cwidth):
                        cells[py, px + j].ord = 0
                else:
                    continue
            elif cwidth < 1:
                continue
            dst.ord = src.ord
            dst.style = src.style
            dst.fg_color = src.fg_color
            if kind[py, px] & SIXEL:
                oy = py * h
                ox = px * w
                average_graphics(
                    &dst.bg_color[0], graphics[oy:oy + h, ox:ox + w * cwidth]
                )
            elif kind[py, px] == MIXED:
                oy = py * h
                ox = px * w
                p = average_graphics(
                    &rgb[0], graphics[oy: oy + h, ox:ox + w * cwidth]
                )
                lerp_rgb(&rgb[0], &dst.bg_color[0], p)
            kind[py, px] = GLYPH
            composite(dst.bg_color, src.bg_color, alpha)
            if cwidth > 1:
                for j in range(1, cwidth):
                    cells[py, px + j].bg_color = dst.bg_color


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
        dst.ord = SPACE_ORD
        dst.style = 0
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
        dst.style = 0
        if py - ipy < .5:
            dst_rgb = &dst.fg_color[0]
        else:
            dst_rgb = &dst.bg_color[0]
        if dst.ord != HALF_BLOCK_ORD:
            dst.fg_color = dst.bg_color
            dst.ord = HALF_BLOCK_ORD
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
            dst.style = 0
            if dst.ord != HALF_BLOCK_ORD:
                dst.fg_color = dst.bg_color
                dst.ord = HALF_BLOCK_ORD
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
                if dst.ord != HALF_BLOCK_ORD:
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
        size_t gh = graphics.shape[0], gw = graphics.shape[1]
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
        if pgy < 0 or pgy >= gh:
            continue
        pgx = ox + <int>round((px - ipx) * w)
        if pgx < 0 or pgx >= gw:
            continue
        graphics[pgy, pgx] = particles[i]
        kind[ipy, ipx] = SIXEL

    # For all sixel cells in region, mark graphics as opaque:
    # ! Should all cells in region be marked sixel? Consider a large region with a
    # ! single sixel pixel. Does entire region really need to be sixel-ized?
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
        size_t gh = graphics.shape[0], gw = graphics.shape[1]
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
        if pgy < 0 or pgy >= gh:
            continue
        pgx = ox + <int>round((px - ipx) * w)
        if pgx < 0 or pgx >= gw:
            continue
        if (
            kind[ipy, ipx] == GLYPH
            or kind[ipy, ipx] == MIXED and not graphics[pgy, pgx, 3]
        ):
            if cells[ipy, ipx].ord == HALF_BLOCK_ORD and py - ipy < .5:
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
    uint32 ord
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
        # ! Why isn't pixel.ord == 0 sufficient?
        if pixel.ord < 10240 or pixel.ord > 10495:
            pixel.ord = 10240
        pgy = <int>((py - ipy) * 4)
        pgx = <int>((px - ipx) * 2)
        pixel.ord |= BRAILLE_ENUM[pgy * 2 + pgx]
        pixel.total_fg[0] += particles[i, 0]
        pixel.total_fg[1] += particles[i, 1]
        pixel.total_fg[2] += particles[i, 2]
        pixel.ncolors += 1

    for i in range(h * w):
        pixel = &pixels[i]
        # ! Why does pixel.ord need to be checked?
        if not pixel.ncolors or pixel.ord < 10240 or pixel.ord > 10495:
            continue
        dst = &cells[(i // w) + y, (i % w) + x]
        dst.ord = pixel.ord
        dst.style = 0
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
        # ! Why isn't pixel.ord == 0 sufficient?
        # ! Assumed if ord is braille, that background has already been composited.
        if pixel.ord < 10240 or pixel.ord > 10495:
            pixel.ord = 10240
            if kind[ipy, ipx] & SIXEL:
                oy = ipy * h
                ox = ipx * w
                average_graphics(
                    &cells[ipy, ipx].bg_color[0], graphics[oy:oy + h, ox:ox + w]
                )
            elif kind[ipy, ipx] == MIXED:
                oy = ipy * h
                ox = ipx * w
                p = average_graphics(&rgb[0], graphics[oy:oy + h, ox: ox + w])
                lerp_rgb(&rgb[0], &cells[ipy, ipx].bg_color[0], p)
            cells[ipy, ipx].fg_color = cells[ipy, ipx].bg_color
        kind[ipy, ipx] = GLYPH
        pgy = <int>((py - ipy) * 4)
        pgx = <int>((px - ipx) * 2)
        pixel.ord |= BRAILLE_ENUM[pgy * 2 + pgx]
        pixel.total_fg[0] += particles[i, 0]
        pixel.total_fg[1] += particles[i, 1]
        pixel.total_fg[2] += particles[i, 2]
        pixel.total_fg[3] += particles[i, 3]
        pixel.ncolors += 1

    for i in range(rh * rw):
        pixel = &pixels[i]
        # ! Why does pixel.ord need to be checked?
        if not pixel.ncolors or pixel.ord < 10240 or pixel.ord > 10495:
            continue
        dst = &cells[(i // rw) + y, (i % rw) + x]
        dst.ord = pixel.ord
        dst.style = 0

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


# TODO: Add an option to disable normalize_canvas and remove normalization in
# text_field_*.
@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline void normalize_canvas(Cell[:, ::1] cells, int[:, ::1] widths):
    cdef:
        size_t h = cells.shape[0], w = cells.shape[1], y, x, sub_x, last_width
        ssize_t last_wide_x = -1

    # Try to prevent wide chars from clipping. If there is clipping,
    # replace wide chars with whitespace.

    for y in range(h):
        for x in range(w):
            if cells[y, x].ord & EGC_BASE:
                widths[y, x] = wcswidth(EGC_POOL[cells[y, x].ord - EGC_BASE])
            else:
                widths[y, x] = wcwidth_uint32(cells[y, x].ord)
            if widths[y, x] < 0:
                widths[y, x] = 0

    for y in range(h):
        for x in range(w):
            if last_wide_x == -1:
                if widths[y, x] == 0:
                    cells[y, x].ord = SPACE_ORD
                    widths[y, x] = 1
                elif widths[y, x] > 1:
                    last_width = widths[y, x]
                    if x + last_width > w:
                        # Wide char clipped by screen
                        widths[y, x] = 1
                        cells[y, x].ord = SPACE_ORD
                    else:
                        last_wide_x = x
            else:
                if widths[y, x] != 0:
                    # Wide char clipped by another char
                    for sub_x in range(last_wide_x, x):
                        widths[y, sub_x] = 1
                        cells[y, sub_x].ord = SPACE_ORD
                    if widths[y, x] > 1:
                        # Two wide chars clip, both become whitespace
                        widths[y, x] = 1
                        cells[y, x].ord = SPACE_ORD
                    last_wide_x = -1
                elif x == last_wide_x + last_width - 1:
                    # End of wide char
                    last_wide_x = -1


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
    if last is NULL:
        write_sgr(f, 1 if cell.style & BOLD else 22, &first)
        write_sgr(f, 3 if cell.style & ITALIC else 23, &first)
        write_sgr(f, 4 if cell.style & UNDERLINE else 24, &first)
        write_sgr(f, 9 if cell.style & STRIKETHROUGH else 29, &first)
        write_sgr(f, 53 if cell.style & OVERLINE else 55, &first)
        write_sgr(f, 7 if cell.style & REVERSE else 27, &first)
        write_rgb(f, 38, &cell.fg_color[0], &first)
        write_rgb(f, 48, &cell.bg_color[0], &first)
    else:
        if cell.style != last.style:
            if cell.style & BOLD != last.style & BOLD:
                write_sgr(f, 1 if cell.style & BOLD else 22, &first)
            if cell.style & ITALIC != last.style & ITALIC:
                write_sgr(f, 3 if cell.style & ITALIC else 23, &first)
            if cell.style & UNDERLINE != last.style & UNDERLINE:
                write_sgr(f, 4 if cell.style & UNDERLINE else 24, &first)
            if cell.style & STRIKETHROUGH != last.style & STRIKETHROUGH:
                write_sgr(f, 9 if cell.style & STRIKETHROUGH else 29, &first)
            if cell.style & OVERLINE != last.style & OVERLINE:
                write_sgr(f, 53 if cell.style & OVERLINE else 55, &first)
            if cell.style & REVERSE != last.style & REVERSE:
                write_sgr(f, 7 if cell.style & REVERSE else 27, &first)
        if not rgb_eq(&cell.fg_color[0], &last.fg_color[0]):
            write_rgb(f, 38, &cell.fg_color[0], &first)
        if not rgb_eq(&cell.bg_color[0], &last.bg_color[0]):
            write_rgb(f, 48, &cell.bg_color[0], &first)
    if not first:
        fbuf_putn(f, "m", 1)
    if cell.ord & EGC_BASE:
        for codepoint in EGC_POOL[cell.ord - EGC_BASE]:
            fbuf_putucs4(f, ord(codepoint))
    else:
        fbuf_putucs4(f, cell.ord)
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
        uint8 *quant_color
        unsigned int aspect_h = aspect_ratio[0], aspect_w = aspect_ratio[1]

    if fbuf_putn(f, "\x1b7", 2):  # Save cursor
        raise MemoryError

    if terminal.sum_supported:
        if fbuf_putn(f, "\x1b[2026h", 7):
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
                    else:
                        gh = y * cell_h
                        gw = x * cell_w
                        if kind[y, x] == SIXEL:
                            # Check if graphics changed.
                            emit_sixel = not all_eq(
                                graphics[gh:gh + cell_h, gw:gw + cell_w],
                                prev_graphics[gh:gh + cell_h, gw:gw + cell_w],
                            )
                        elif kind[y, x] == MIXED:
                            # Check if cell or graphics changed.
                            emit_sixel = not (
                                cell_eq(&cells[y, x], &prev_cells[y, x])
                                and all_eq(
                                    graphics[gh:gh + cell_h, gw:gw + cell_w],
                                    prev_graphics[gh:gh + cell_h, gw:gw + cell_w],
                                )
                            )
                        elif kind[y, x] == SEE_THROUGH_SIXEL:
                            # Check if cell (but not bg_color) or graphics changed.
                            emit_sixel = not see_through_eq(
                                &cells[y, x],
                                &prev_cells[y, x],
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
            elif kind[y, x] == SEE_THROUGH_SIXEL and emit_sixel:
                # Note to future code archaeologists:
                # The reason for SEE_THROUGH_SIXEL is to color match the background of
                # a cell that is seen "under" graphics with the quantized color of the
                # graphics. That is, if the graphics color was composited directly onto
                # the cell background in `trans_sixel_graphics_render`, then once the
                # graphics has passed through quantization, there would be a slight
                # discrepancy with the cell background color and the graphics color.
                # So instead of above, the cell background color is composited onto the
                # graphics and then, after quantization, the graphics color is copied
                # back onto cell background.
                gy = y * cell_h
                gx = x * cell_w
                quant_color = octree.qs.table + 3 * sgraphics[gy, gx, 0]
                cells[y, x].bg_color[0] = _100_to_uint8(quant_color[0])
                cells[y, x].bg_color[1] = _100_to_uint8(quant_color[1])
                cells[y, x].bg_color[2] = _100_to_uint8(quant_color[2])
                if write_glyph(
                    f, oy, ox, y, x, &cursor_y, &cursor_x, cells, widths, &last_sgr
                ):
                    raise MemoryError

    if (
        terminal.sum_supported and f.len == 9
        or not terminal.sum_supported and f.len == 2
    ):
        # Only 'Save Cursor' and 'SUM' in buffer. Don't flush.
        f.len = 0
        return

    if terminal.sum_supported:
        if fbuf_putn(f, "\x1b[2026l", 7):
            raise MemoryError

    if fbuf_putn(f, "\x1b8", 2):  # Restore cursor
        raise MemoryError

    if logger.isEnabledFor(LogLevel.ANSI):
        logger.log(LogLevel.ANSI, f"Frame rendered: {f.len} bytes")
        logger.log(LogLevel.ANSI, "ANSI DUMP")
        logger.log(LogLevel.ANSI, f.buf[:f.len])
    fbuf_flush_fd(f, terminal.stdout)
