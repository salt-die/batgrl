"""
Cython implementation of Wu's Color Quantizer.

Notes
-----
Greedy orthogonal bipartition of RGB space for variance minimization aided by
inclusion-exclusion tricks. For speed, no nearest neighbor search is done.

References
----------
Xiaolin Wu, "Efficient Statistical Computations for Optimal Color Quantization",
Graphics Gems II, (ed. James Arvo), Academic Press: Boston, 1991.

`Wu's Implementation <https://gist.github.com/bert/1192520>`_
"""
import cython
import numpy as np
cimport numpy as cnp
from numpy.typing import NDArray

__all__ = ["median_variance_quantization"]

cdef:
    unsigned char RED = 2
    unsigned char GREEN = 1
    unsigned char BLUE = 0

    struct Box:
        unsigned char r0
        unsigned char r1
        unsigned char g0
        unsigned char g1
        unsigned char b0
        unsigned char b1
        int volume


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void hist3d(
    unsigned char[:, :, ::1] texture,
    int[:, :, ::1] wt,
    int[:, :, ::1] mr,
    int[:, :, ::1] mg,
    int[:, :, ::1] mb,
    double[:, :, ::1] m2,
    unsigned char[:, :, ::1] quant,
):
    """Build 3-D color histogram of counts."""
    cdef:
        Py_ssize_t h, w, y, x
        unsigned char r, g, b, inr, ing, inb
        cnp.ndarray[double, ndim=1] sqr = np.arange(256, dtype=float)**2

    h = texture.shape[0]
    w = texture.shape[1]

    for y in range(h):
        for x in range(w):
            r = texture[y, x][0]
            g = texture[y, x][1]
            b = texture[y, x][2]

            inr = (r >> 3) + 1
            ing = (g >> 3) + 1
            inb = (b >> 3) + 1

            wt[inr, ing, inb] += 1
            mr[inr, ing, inb] += r
            mg[inr, ing, inb] += g
            mb[inr, ing, inb] += b
            m2[inr, ing, inb] += sqr[r] + sqr[g] + sqr[b]

            quant[y, x, 0] = inr
            quant[y, x, 1] = ing
            quant[y, x, 2] = inb


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void moments(
    int[:, :, ::1] wt,
    int[:, :, ::1] mr,
    int[:, :, ::1] mg,
    int[:, :, ::1] mb,
    double[:, :, ::1] m2,
):
    """Compute cumulative moments."""
    cdef:
        int line, line_r, line_g, line_b
        unsigned char r, g, b
        double line_2
        cnp.ndarray[int, ndim=1] area = np.empty(33, dtype=np.intc)
        cnp.ndarray[int, ndim=1] area_red = np.empty(33, dtype=np.intc)
        cnp.ndarray[int, ndim=1] area_green = np.empty(33, dtype=np.intc)
        cnp.ndarray[int, ndim=1] area_blue = np.empty(33, dtype=np.intc)
        cnp.ndarray[double, ndim=1] area_2 = np.empty(33, dtype=float)

    for r in range(1, 33):
        area[:] = 0
        area_red[:] = 0
        area_green[:] = 0
        area_blue[:] = 0
        area_2[:] = 0
        for g in range(1, 33):
            line = 0
            line_r = 0
            line_g = 0
            line_b = 0
            line_2 = 0
            for b in range(1, 33):
                line += wt[r, g, b]
                line_r += mr[r, g, b]
                line_g += mg[r, g, b]
                line_b += mb[r, g, b]
                line_2 += m2[r, g, b]

                area[b] += line
                area_red[b] += line_r
                area_green[b] += line_g
                area_blue[b] += line_b
                area_2[b] += line_2

                wt[r, g, b] = wt[r - 1, g, b] + area[b]
                mr[r, g, b] = mr[r - 1, g, b] + area_red[b]
                mg[r, g, b] = mg[r - 1, g, b] + area_green[b]
                mb[r, g, b] = mb[r - 1, g, b] + area_blue[b]
                m2[r, g, b] = m2[r - 1, g, b] + area_2[b]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int volume_int(Box *cube, int[:, :, ::1] moment):
    """Compute sum over a box of any given statistic."""
    return (
        moment[cube.r1, cube.g1, cube.b1]
        - moment[cube.r1, cube.g1, cube.b0]
        - moment[cube.r1, cube.g0, cube.b1]
        + moment[cube.r1, cube.g0, cube.b0]
        - moment[cube.r0, cube.g1, cube.b1]
        + moment[cube.r0, cube.g1, cube.b0]
        + moment[cube.r0, cube.g0, cube.b1]
        - moment[cube.r0, cube.g0, cube.b0]
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double volume_float(Box *cube, double[:, :, ::1] moment):
    """Compute sum over a box of any given statistic."""
    return (
        moment[cube.r1, cube.g1, cube.b1]
        - moment[cube.r1, cube.g1, cube.b0]
        - moment[cube.r1, cube.g0, cube.b1]
        + moment[cube.r1, cube.g0, cube.b0]
        - moment[cube.r0, cube.g1, cube.b1]
        + moment[cube.r0, cube.g1, cube.b0]
        + moment[cube.r0, cube.g0, cube.b1]
        - moment[cube.r0, cube.g0, cube.b0]
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int bottom(Box *cube, unsigned char direction, int[:, :, ::1] moment):
    """
    Compute part of volume(cube, mmt) that doesn't depend on r1, g1, or b1
    (depending on dir).
    """
    if direction == RED:
        return (
            -moment[cube.r0, cube.g1, cube.b1]
            + moment[cube.r0, cube.g1, cube.b0]
            + moment[cube.r0, cube.g0, cube.b1]
            - moment[cube.r0, cube.g0, cube.b0]
        )
    if direction == GREEN:
        return (
            -moment[cube.r1, cube.g0, cube.b1]
            + moment[cube.r1, cube.g0, cube.b0]
            + moment[cube.r0, cube.g0, cube.b1]
            - moment[cube.r0, cube.g0, cube.b0]
        )
    if direction == BLUE:
        return (
            -moment[cube.r1, cube.g1, cube.b0]
            + moment[cube.r1, cube.g0, cube.b0]
            + moment[cube.r0, cube.g1, cube.b0]
            - moment[cube.r0, cube.g0, cube.b0]
        )
    return 0


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int top(
    Box *cube,
    unsigned char direction,
    int[:, :, ::1] moment,
    unsigned char pos,
):
    """
    Compute remainder of volume(cube, mmt), substituting pos for r1, g1, or b1
    (depending on dir).
    """
    if direction == RED:
        return (
            moment[pos, cube.g1, cube.b1]
            - moment[pos, cube.g1, cube.b0]
            - moment[pos, cube.g0, cube.b1]
            + moment[pos, cube.g0, cube.b0]
        )
    if direction == GREEN:
        return (
            moment[cube.r1, pos, cube.b1]
            - moment[cube.r1, pos, cube.b0]
            - moment[cube.r0, pos, cube.b1]
            + moment[cube.r0, pos, cube.b0]
        )
    if direction == BLUE:
        return (
            moment[cube.r1, cube.g1, pos]
            - moment[cube.r1, cube.g0, pos]
            - moment[cube.r0, cube.g1, pos]
            + moment[cube.r0, cube.g0, pos]
        )
    return 0


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double variance(
    Box *cube,
    int[:, :, ::1] wt,
    int[:, :, ::1] mr,
    int[:, :, ::1] mg,
    int[:, :, ::1] mb,
    double[:, :, ::1] m2,
):
    """Compute the weighted variance of a box."""
    cdef int dr, dg, db
    dr = volume_int(cube, mr)
    dg = volume_int(cube, mg)
    db = volume_int(cube, mb)
    return (
        volume_float(cube, m2)
        - (dr ** 2 + dg ** 2 + db ** 2) / <double>volume_int(cube, wt)
    )


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double minimize(
    Box *cube,
    unsigned char direction,
    unsigned char first,
    unsigned char last,
    int *cut,
    int whole_w,
    int whole_r,
    int whole_g,
    int whole_b,
    int[:, :, ::1] wt,
    int[:, :, ::1] mr,
    int[:, :, ::1] mg,
    int[:, :, ::1] mb,
):
    """Minimize the sum of variances of two subboxes."""
    cdef:
        int half_w, half_r, half_g, half_b
        int base_w, base_r, base_g, base_b
        unsigned char i
        double temp, max

    base_w = bottom(cube, direction, wt)
    base_r = bottom(cube, direction, mr)
    base_g = bottom(cube, direction, mg)
    base_b = bottom(cube, direction, mb)

    max = 0.0
    cut[0] = -1
    for i in range(first, last):
        half_w = base_w + top(cube, direction, wt, i)
        if half_w == 0 or half_w == whole_w:
            continue

        half_r = base_r + top(cube, direction, mr, i)
        half_g = base_g + top(cube, direction, mg, i)
        half_b = base_b + top(cube, direction, mb, i)
        temp = <double>(half_r**2 + half_g**2 + half_b**2) / <double>half_w

        half_w = whole_w - half_w
        half_r = whole_r - half_r
        half_g = whole_g - half_g
        half_b = whole_b - half_b
        temp += <double>(half_r**2 + half_g**2 + half_b**2) / <double>half_w

        if temp > max:
            max = temp
            cut[0] = i

    return max


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int cut(
    Box *a,
    Box *b,
    int[:, :, ::1] wt,
    int[:, :, ::1] mr,
    int[:, :, ::1] mg,
    int[:, :, ::1] mb,
):
    cdef:
        unsigned char direction
        int cut_r, cut_g, cut_b, whole_w, whole_r, whole_g, whole_b
        double max_r, max_g, max_b

    whole_w = volume_int(a, wt)
    whole_r = volume_int(a, mr)
    whole_g = volume_int(a, mg)
    whole_b = volume_int(a, mb)

    max_r = minimize(
        a, RED, a.r0 + 1, a.r1, &cut_r,
        whole_w, whole_r, whole_g, whole_b,
        wt, mr, mg, mb,
    )
    max_g = minimize(
        a, GREEN, a.g0 + 1, a.g1, &cut_g,
        whole_w, whole_r, whole_g, whole_b,
        wt, mr, mg, mb,
    )
    max_b = minimize(
        a, BLUE, a.b0 + 1, a.b1, &cut_b,
        whole_w, whole_r, whole_g, whole_b,
        wt, mr, mg, mb,
    )

    if max_r >= max_g and max_r >= max_b:
        if cut_r < 0:
            return 0
        direction = RED
    elif max_g >= max_r and max_g >= max_b:
        direction = GREEN
    else:
        direction = BLUE

    b.r1 = a.r1
    b.g1 = a.g1
    b.b1 = a.b1

    if direction == RED:
        b.r0 = a.r1 = cut_r
        b.g0 = a.g0
        b.b0 = a.b0
    elif direction == GREEN:
        b.r0 = a.r0
        b.g0 = a.g1 = cut_g
        b.b0 = a.b0
    else:
        b.r0 = a.r0
        b.g0 = a.g0
        b.b0 = a.b1 = cut_b

    a.volume = (a.r1 - a.r0) * (a.g1 - a.g0) * (a.b1 - a.b0)
    b.volume = (b.r1 - b.r0) * (b.g1 - b.g0) * (b.b1 - b.b0)
    return 1


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void mark(Box *cube, int label, unsigned char[:, :, ::1] tag):
    cdef Py_ssize_t r, g, b
    for r in range(cube.r0 + 1, cube.r1 + 1):
        for g in range(cube.g0 + 1, cube.g1 + 1):
            for b in range(cube.b0 + 1, cube.b1 + 1):
                tag[r, g, b] = label


@cython.boundscheck(False)
@cython.wraparound(False)
def median_variance_quantization(
    cnp.ndarray[unsigned char, ndim=3] texture,
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """
    Cython implementation of Wu's Color Quantizer.

    Parameters
    ----------
    texture : NDArray[np.uint8]
        A RGB or RGBA texture to quantize.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.uint8]]
        The quantized palette and an array of indices into the palette of each pixel in
        the original texture. Palette color channels range from 0 to 100 to conform to
        the sixel format.

    Notes
    -----
    Greedy orthogonal bipartition of RGB space for variance minimization aided by
    inclusion-exclusion tricks. For speed, no nearest neighbor search is done.

    References
    ----------
    Xiaolin Wu, "Efficient Statistical Computations for Optimal Color Quantization",
    Graphics Gems II, (ed. James Arvo), Academic Press: Boston, 1991.

    `Wu's Implementation <https://gist.github.com/bert/1192520>`_
    """
    cdef:
        Py_ssize_t h, w, y, x
        int i, j, k
        double temp, weight
        Box[256] cubes
        double[256] vv

    h = texture.shape[0]
    w = texture.shape[1]

    cdef:
        cnp.ndarray[unsigned char, ndim=3] quant = np.zeros((h, w, 3), dtype=np.uint8)
        cnp.ndarray[unsigned char, ndim=2] out = np.zeros((h, w), dtype=np.uint8)
        cnp.ndarray[int, ndim=3] wt = np.zeros((33, 33, 33), dtype=np.intc)
        cnp.ndarray[int, ndim=3] mr = np.zeros((33, 33, 33), dtype=np.intc)
        cnp.ndarray[int, ndim=3] mg = np.zeros((33, 33, 33), dtype=np.intc)
        cnp.ndarray[int, ndim=3] mb = np.zeros((33, 33, 33), dtype=np.intc)
        cnp.ndarray[double, ndim=3] m2 = np.zeros((33, 33, 33), dtype=float)
        cnp.ndarray[unsigned char, ndim=3] tag = np.zeros((33, 33, 33), dtype=np.uint8)

    hist3d(texture, wt, mr, mg, mb, m2, quant)
    moments(wt, mr, mg, mb, m2)

    cubes[0].r0 = cubes[0].g0 = cubes[0].b0 = 0
    cubes[0].r1 = cubes[0].g1 = cubes[0].b1 = 32

    i = 0
    j = 1
    while j < 256:
        if cut(&cubes[i], &cubes[j], wt, mr, mg, mb):
            if cubes[i].volume > 1:
                vv[i] = variance(&cubes[i], wt, mr, mg, mb, m2)
            else:
                vv[i] = 0.0
            if cubes[j].volume > 1:
                vv[j] = variance(&cubes[j], wt, mr, mg, mb, m2)
            else:
                vv[j] = 0.0
            j += 1
        else:
            vv[i] = 0.0

        i = 0
        temp = vv[0]
        for k in range(1, j):
            if vv[k] > temp:
                temp = vv[k]
                i = k

        if temp <= 0.0:
            break

    cdef cnp.ndarray[unsigned char, ndim=2] palette = np.ndarray((j, 3), dtype=np.uint8)

    for i in range(j):
        mark(&cubes[i], i, tag)
        weight = <double>volume_int(&cubes[i], wt)
        if weight > 0:
            # Invert and scale weight so we can use multiplies and so that palette
            # values will be between 0-100 for sixel.
            # Magic number is 100 / 255...
            weight = 0.39215686274509803 / weight
            palette[i, 0] = <unsigned char>(volume_int(&cubes[i], mr) * weight)
            palette[i, 1] = <unsigned char>(volume_int(&cubes[i], mg) * weight)
            palette[i, 2] = <unsigned char>(volume_int(&cubes[i], mb) * weight)
        else:
            palette[i, 0] = 0
            palette[i, 1] = 0
            palette[i, 2] = 0

    for y in range(h):
        for x in range(w):
            out[y, x] = tag[quant[y, x, 0], quant[y, x, 1], quant[y, x, 2]]

    return palette, out
