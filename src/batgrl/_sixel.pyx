"""
Sixel Graphics.

The sixel format involves first creating a palette (generally limited to 256 colors) for
the succeeding band data. Each color in the palette uses the ansi "#i;m;r;g;b" where
``i`` is the color register and ``m`` is the "mode" (``1`` for hsl or ``2`` for rgb).
For mode ``2`` (the only mode batgrl uses), the remaining three parameters ``r``, ``g``,
``b`` are the red, green, and blue color components of the color scaled from 0-100
inclusive.

The remaining data for an image is split into 6-pixel high bands. A six-pixel tall
column in that band is called a sixel. For each band, for every color in the band output
"#i" with ``i`` being a color in the palette followed by color data finally ending with
"$" to return to the start of the band (to output a new color) or "-" to move to the
next band.

For the color data, for each pixel in a sixel with values, ``n``, from 0-5 from top-to-
bottom, if that pixel matches the current color add ``2**n``. The result is a value from
0-63. Add 63 to this result to get a character between "?"-"~". If a character is
repeated, run length encoding, "!rc", may be used instead where ``r`` is the number of
times to repeat ``c``.
"""
# This is nearly verbatim notcurses' sixel.c, but in cython.
# notcurses' sixel.c:
#   https://github.com/dankamongmen/notcurses/blob/master/src/lib/sixel.c
#
# notcurses is copyright 2019-2025 Nick Black et al and is licensed under the Apache
# License, Version 2.0:
#   http://www.apache.org/licenses/LICENSE-2.0
#

from libc.stdio cimport sprintf
from libc.stdlib cimport free, malloc, qsort
from libc.string cimport memset, memcpy
from libc.math cimport round

cimport cython

from ._fbuf cimport fbuf, fbuf_printf, fbuf_putn, fbuf_puts
from ._sixel cimport onode, qnode, qstate

ctypedef unsigned char uint8
ctypedef unsigned int uint

cdef:
    uint QNODES_COUNT = 1000
    uint MAX_COLORS = 256

    class OctTree:
        def __init__(self) -> None:
            if alloc_qstate(&self.qs):
                raise MemoryError

        def __dealloc__(self) -> None:
            free_qstate(&self.qs)

    struct BandExtender:
        size_t length, wrote
        int rle
        char rep

    struct SixelMap:
        size_t nbands
        char ***bands

    struct ActiveColor:
        unsigned int color
        char rep


cdef inline uint8 uint8_to_100(uint8 c):
    cdef uint8 result = <uint8>round(c * 100.0 / 255)
    if result > 99:
        return 99
    return result


cdef inline uint qnode_keys(uint8 *srgb, uint8 *skey):
    skey[0] = (
        (((srgb[0] % 10) // 5) << 2)
        + (((srgb[1] % 10) // 5) << 1)
        + ((srgb[2] % 10) // 5)
    )
    return srgb[0] // 10 * 100 + srgb[1] // 10 * 10 + srgb[2] // 10


cdef inline bint is_chosen(const qnode *q):
    return q.cidx & 0x8000


cdef inline uint make_chosen(uint cidx):
    return cidx | 0x8000


cdef inline uint qidx(const qnode *q):
    if q.cidx & 0x8000:
        return q.cidx ^ 0x8000
    return q.cidx


cdef inline int insert_color(qstate *qs, uint8 *srgb):
    cdef:
        uint8 skey, skeynat
        uint key = qnode_keys(srgb, &skey)
        qnode *q
        onode *o

    q = &qs.qnodes[key]
    if q.pop == 0 and q.qlink == 0:
        q.srgb[0] = srgb[0]
        q.srgb[1] = srgb[1]
        q.srgb[2] = srgb[2]
        q.pop = 1
        qs.ncolors += 1
        return 0

    if q.qlink == 0:
        qnode_keys(&q.srgb[0], &skeynat)
        if skey == skeynat:
            q.pop += 1
            return 0

        if qs.onodes_free == 0 or qs.dynnodes_free == 0:
            q.pop += 1
            return 0

        o = qs.onodes + qs.onodes_total - qs.onodes_free
        memset(o, 0, sizeof(onode))
        o.q[skeynat] = &qs.qnodes[QNODES_COUNT + qs.dynnodes_total - qs.dynnodes_free]
        qs.dynnodes_free -= 1
        memcpy(o.q[skeynat], q, sizeof(qnode))
        q.qlink = qs.onodes_total - qs.onodes_free + 1
        qs.onodes_free -= 1
        q.pop = 0
    else:
        o = qs.onodes + q.qlink - 1

    if o.q[skey]:
        o.q[skey].pop += 1
        return 0

    if qs.dynnodes_free == 0:
        return -1

    o.q[skey] = &qs.qnodes[QNODES_COUNT + qs.dynnodes_total - qs.dynnodes_free]
    qs.dynnodes_free -= 1
    o.q[skey].pop = 1
    o.q[skey].srgb[0] = srgb[0]
    o.q[skey].srgb[1] = srgb[1]
    o.q[skey].srgb[2] = srgb[2]
    o.q[skey].qlink = 0
    o.q[skey].cidx = 0
    qs.ncolors += 1
    return 0


cdef inline int find_color(const qstate *qs, uint8 *srgb):
    cdef:
        uint8 skey
        uint key = qnode_keys(srgb, &skey)
        qnode *q = &qs.qnodes[key]

    if q.qlink and q.pop == 0:
        if qs.onodes[q.qlink - 1].q[skey]:
            q = qs.onodes[q.qlink - 1].q[skey]
        else:
            return -1

    return qidx(q)


cdef int qnode_cmp(const void* a, const void* b) noexcept nogil:
    cdef:
        const qnode *qa = <qnode*>a
        const qnode *qb = <qnode*>b
    if qa.pop < qb.pop:
        return -1
    if qa.pop == qb.pop:
        return 0
    return 1


cdef qnode *get_active_set(qstate *qs):
    cdef:
        qnode *active = <qnode*>malloc(sizeof(qnode) * qs.ncolors)
        uint target_idx = 0
        uint total = QNODES_COUNT + qs.dynnodes_total - qs.dynnodes_free
        uint z, s
        onode *o

    if active is NULL:
        return active

    for z in range(total):
        if target_idx >= qs.ncolors:
            break
        if qs.qnodes[z].pop:
            memcpy(&active[target_idx], &qs.qnodes[z], sizeof(qnode))
            active[target_idx].qlink = z
            target_idx += 1
        elif qs.qnodes[z].qlink:
            o = &qs.onodes[qs.qnodes[z].qlink - 1]
            for s in range(8):
                if target_idx >= qs.ncolors:
                    break
                if o.q[s]:
                    memcpy(&active[target_idx], o.q[s], sizeof(qnode))
                    active[target_idx].qlink = o.q[s] - qs.qnodes
                    target_idx += 1
    qsort(active, qs.ncolors, sizeof(qnode), &qnode_cmp)
    return active


cdef inline int find_next_lowest_chosen(
    const qstate *qs, int z, int i, const qnode **hq
):
    cdef:
        const qnode *h
        const onode *o

    while True:
        h = &qs.qnodes[z]
        if h.pop == 0 and h.qlink:
            o = &qs.onodes[h.qlink - 1]
            while i >= 0:
                h = o.q[i]
                if h and is_chosen(h):
                    hq[0] = h
                    return z * 8 + i
                i += 1
                if i >= 8:
                    break
        elif is_chosen(h):
            hq[0] = h
            return z * 8
        z += 1
        if z >= QNODES_COUNT:
            return -1
        i = 0


cdef inline void choose(
    qstate *qs,
    qnode *q,
    int z,
    int i,
    int *hi,
    int *lo,
    const qnode **hq,
    const qnode **lq,
):
    cdef int cur
    if not is_chosen(q):
        if z * 8 > hi[0]:
            hi[0] = find_next_lowest_chosen(qs, z, i, hq)
        cur = z * 8 + (i if i >= 0 else 4)
        if lo[0] == -1:
            q.cidx = qidx(hq[0])
        elif hi[0] == -1 or cur - lo[0] < hi[0] - cur:
            q.cidx = qidx(lq[0])
        else:
            q.cidx = qidx(hq[0])
    else:
        lq[0] = q
        lo[0] = z * 8


cdef inline int merge_color_table(qstate *qs):
    if qs.ncolors == 0:
        return 0

    cdef qnode *qactive = get_active_set(qs)
    if qactive is NULL:
        return -1

    cdef int cidx = 0, z
    for z in range(qs.ncolors - 1, -1, -1):
        if cidx == MAX_COLORS:
            break
        qs.qnodes[qactive[z].qlink].cidx = make_chosen(cidx)
        cidx += 1
    free(qactive)

    if qs.ncolors <= MAX_COLORS:
        return 0

    cdef:
        int lo = -1, hi = -1, i
        const qnode *lq = NULL
        const qnode *hq = NULL
        const onode *o
    for z in range(QNODES_COUNT):
        if qs.qnodes[z].pop == 0:
            if qs.qnodes[z].qlink == 0:
                continue
            o = &qs.onodes[qs.qnodes[z].qlink - 1]
            for i in range(8):
                if o.q[i]:
                    choose(qs, o.q[i], z, i, &hi, &lo, &hq, &lq)
        else:
            choose(qs, &qs.qnodes[z], z, -1, &hi, &lo, &hq, &lq)
    qs.ncolors = MAX_COLORS
    return 0


cdef inline void load_color_table(const qstate *qs):
    cdef:
        int total = QNODES_COUNT + qs.dynnodes_total - qs.dynnodes_free
        int loaded = 0, z
        const qnode *q

    for z in range(total):
        if loaded == qs.ncolors:
            break
        q = &qs.qnodes[z]
        if is_chosen(q):
            qs.table[3 * qidx(q)] = q.srgb[0]
            qs.table[3 * qidx(q) + 1] = q.srgb[1]
            qs.table[3 * qidx(q) + 2] = q.srgb[2]
            loaded += 1


cdef int alloc_qstate(qstate *qs):
    qs.dynnodes_total = MAX_COLORS
    qs.dynnodes_free = qs.dynnodes_total
    qs.qnodes = <qnode*>malloc((QNODES_COUNT + qs.dynnodes_total) * sizeof(qnode))
    if qs.qnodes is NULL:
        return -1

    qs.onodes_total = qs.dynnodes_total // 8
    qs.onodes_free = qs.onodes_total
    qs.onodes = <onode*>malloc(qs.onodes_total * sizeof(onode))
    if qs.onodes is NULL:
        free(qs.qnodes)
        return -1

    qs.table = <uint8*>malloc(3 * MAX_COLORS)
    if qs.table is NULL:
        free(qs.qnodes)
        free(qs.onodes)
        return -1

    memset(qs.qnodes, 0, sizeof(qnode) * QNODES_COUNT)
    qs.ncolors = 0
    return 0


cdef void reset_qstate(qstate *qs):
    memset(qs.qnodes, 0, sizeof(qnode) * QNODES_COUNT)
    qs.dynnodes_free = qs.dynnodes_total
    qs.onodes_free = qs.onodes_total
    qs.ncolors = 0


cdef void free_qstate(qstate *qs):
    if qs is not NULL:
        free(qs.qnodes)
        free(qs.onodes)
        free(qs.table)


cdef inline size_t sixel_count(size_t h, size_t w):
    return (h + 5) // 6 * w


cdef inline size_t sixel_band_count(size_t h):
    return sixel_count(h, 1)


cdef SixelMap *new_sixel_map(size_t h):
    cdef SixelMap *sixel_map = <SixelMap*>malloc(sizeof(SixelMap))
    if sixel_map is NULL:
        return NULL
    sixel_map.nbands = sixel_band_count(h)
    sixel_map.bands = <char***>malloc(sizeof(char**) * sixel_map.nbands)
    if sixel_map.bands is NULL:
        free(sixel_map)
        return NULL
    return sixel_map


cdef void color_band_free(char **color_band, size_t ncolors):
    cdef size_t i
    for i in range(ncolors):
        if color_band[i] is not NULL:
            free(color_band[i])
    free(color_band)


cdef void sixel_map_free(SixelMap *sixel_map, uint ncolors):
    cdef size_t i
    for i in range(sixel_map.nbands):
        if sixel_map.bands[i] is not NULL:
            color_band_free(sixel_map.bands[i], ncolors)
    free(sixel_map.bands)
    free(sixel_map)


cdef inline void write_rle(char *color, size_t *length, ssize_t rle, char rep):
    if rle > 2:
        length[0] += sprintf(&color[length[0]], "!%d", <int>rle)
    elif rle == 2:
        color[length[0]] = rep
        length[0] += 1
    if rle > 0:
        color[length[0]] = rep
        length[0] += 1
    color[length[0]] = 0


cdef inline char *color_band_extend(
    char *color_band, BandExtender *extender, size_t w, size_t x
):
    if color_band is NULL:
        color_band = <char*>malloc(w + 1)
    if color_band is NULL:
        return NULL
    write_rle(color_band, &extender.length, extender.rle, extender.rep + 63)
    cdef ssize_t clear_len = x - (extender.rle + extender.wrote)
    write_rle(color_band, &extender.length, clear_len, 63)
    return color_band


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline int build_sixel_band(
    size_t n,
    SixelMap *sixel_map,
    qstate *qs,
    uint8[:, :, ::1] stexture,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
    size_t *P2,
):
    cdef:
        BandExtender *extenders = <BandExtender*>malloc(
            sizeof(BandExtender) * qs.ncolors
        )
        char **color_bands

    if extenders is NULL:
        return -1

    sixel_map.bands[n] = <char**>malloc(sizeof(char*) * qs.ncolors)
    color_bands = sixel_map.bands[n]
    if color_bands is NULL:
        free(extenders)
        return -1

    memset(color_bands, 0, sizeof(char*) * qs.ncolors)
    memset(extenders, 0, sizeof(BandExtender) * qs.ncolors)

    cdef:
        size_t ystart = n * 6, yend = min(ystart + 6, h), x, y, i
        ActiveColor[6] active_colors
        unsigned int cidx, nactive_colors, color
        BandExtender *extender

    for x in range(w):
        nactive_colors = 0
        for y in range(ystart, yend):
            if not stexture[oy + y, ox + x, 3]:
                P2[0] = 1
                continue

            cidx = find_color(qs, &stexture[oy + y, ox + x, 0])
            if cidx < 0:
                return -1

            for i in range(nactive_colors):
                if active_colors[i].color == cidx:
                    active_colors[i].rep += 1 << (y - ystart)
                    break
            else:
                active_colors[nactive_colors].color = cidx
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
                color_bands[color] = color_band_extend(
                    color_bands[color], extender, w, x
                )
                if color_bands[color] is NULL:
                    free(extenders)
                    return -1
                extender.rle = 1
                extender.wrote = x
                extender.rep = active_colors[i].rep

    for color in range(qs.ncolors):
        extender = &extenders[color]
        if extender.rle == 0:
            color_bands[color] = NULL
        else:
            color_bands[color] = color_band_extend(
                color_bands[color], extender, w, w - 1
            )
            if color_bands[color] is NULL:
                free(extenders)
                return -1

    free(extenders)
    return 0


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int sixel(
    fbuf *f,
    qstate *qs,
    const uint8[:, :, ::1] texture,
    uint8[:, :, ::1] stexture,
    unsigned int aspect_h,
    unsigned int aspect_w,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
):
    reset_qstate(qs)

    cdef size_t y, x
    for y in range(oy, oy + h):
        for x in range(ox, ox + w):
            if texture[y, x, 3]:
                stexture[y, x, 0] = uint8_to_100(texture[y, x, 0])
                stexture[y, x, 1] = uint8_to_100(texture[y, x, 1])
                stexture[y, x, 2] = uint8_to_100(texture[y, x, 2])
                stexture[y, x, 3] = 1
                if insert_color(qs, &stexture[y, x, 0]):
                    return -1
            else:
                stexture[y, x, 3] = 0
    if merge_color_table(qs):
        return -1

    load_color_table(qs)

    cdef:
        size_t n, color, P2 = 0
        bint close_previous
        SixelMap *sixel_map = new_sixel_map(h)
        char **color_bands
        uint8 *rgb = qs.table

    if sixel_map is NULL:
        return -1

    for n in range(sixel_map.nbands):
        if build_sixel_band(n, sixel_map, qs, stexture, oy, ox, h, w, &P2) < 0:
            sixel_map_free(sixel_map, qs.ncolors)
            return -1

    if fbuf_printf(f, "\x1bP;%d;q\"%d;%d;%d;%d", P2, aspect_h, aspect_w, w, h):
        sixel_map_free(sixel_map, qs.ncolors)
        return -1

    for color in range(qs.ncolors):
        if fbuf_printf(f, "#%d;2;%d;%d;%d", color, rgb[0], rgb[1], rgb[2]):
            sixel_map_free(sixel_map, qs.ncolors)
            return -1
        rgb += 3

    for n in range(sixel_map.nbands):
        close_previous = 0
        color_bands = sixel_map.bands[n]
        for color in range(qs.ncolors):
            if color_bands[color] is NULL:
                continue
            if close_previous:
                if fbuf_putn(f, "$", 1):
                    sixel_map_free(sixel_map, qs.ncolors)
                    return -1
            else:
                close_previous = 1
            if fbuf_printf(f, "#%d", color):
                sixel_map_free(sixel_map, qs.ncolors)
                return -1
            if fbuf_puts(f, color_bands[color]):
                sixel_map_free(sixel_map, qs.ncolors)
                return -1
        if fbuf_putn(f, "-", 1):
            sixel_map_free(sixel_map, qs.ncolors)
            return -1

    f.len -= 1  # Remove last "-"
    sixel_map_free(sixel_map, qs.ncolors)
    if fbuf_putn(f, "\x1b\\", 2):
        return -1

    return 0
