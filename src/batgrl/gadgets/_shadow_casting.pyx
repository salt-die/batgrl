from libc.math cimport round, sqrt
from libc.stdlib cimport free, malloc, realloc
from libc.string cimport memmove

cimport cython

ctypedef unsigned char uint8
ctypedef unsigned long ulong


cdef struct Octant:
    int y
    int x
    bint flipped

# An octant represents an eigth of an area around a light source.
#
# If a light source is at `1`, then an octant with y=-1,x=1,flipped=0 looks like:
#
#  456
#  23
#  1
#
# Where the numbers represent the order cells are visited within an octant. Similarly,
# an octant with y=-1,x=1,flipped=1 looks like:
#
#   6
#  35
# 124
#
# `flipped` determines which axis is moved along first (`y` if not flipped, and `x`
# otherwise). And `y` and `x` determine the quadrant with negative y upwards, and
# negative x leftwards.

cdef Octant[8] OCTANTS
OCTANTS[0].y = 1
OCTANTS[0].x = 1
OCTANTS[0].flipped = 0

OCTANTS[1].y = 1
OCTANTS[1].x = 1
OCTANTS[1].flipped = 1

OCTANTS[2].y = 1
OCTANTS[2].x = -1
OCTANTS[2].flipped = 0

OCTANTS[3].y = 1
OCTANTS[3].x = -1
OCTANTS[3].flipped = 1

OCTANTS[4].y = -1
OCTANTS[4].x = 1
OCTANTS[4].flipped = 0

OCTANTS[5].y = -1
OCTANTS[5].x = 1
OCTANTS[5].flipped = 1

OCTANTS[6].y = -1
OCTANTS[6].x = -1
OCTANTS[6].flipped = 0

OCTANTS[7].y = -1
OCTANTS[7].x = -1
OCTANTS[7].flipped = 1


cdef enum Restrictiveness: PERMISSIVE, MODERATE, RESTRICTIVE


cdef struct Interval:
    double start
    double center
    double end


cdef struct IntervalList:
    Interval *buf
    size_t len, size


cdef size_t INITIAL_INTERVAL_SIZE = 64


cdef int init_intervals(IntervalList *intervals):
    intervals.buf = <Interval*>malloc(INITIAL_INTERVAL_SIZE * sizeof(Interval))
    if intervals.buf is NULL:
        return -1

    intervals.len = 0
    intervals.size = INITIAL_INTERVAL_SIZE


cdef void free_intervals(IntervalList *intervals):
    free(intervals.buf)
    intervals.buf = NULL
    intervals.len = 0
    intervals.size = 0


cdef int grow(IntervalList *intervals, size_t n):
    # Ensure intervals has enough room to grow by `n`.
    if n + intervals.len <= intervals.size:
        return 0

    cdef Interval *new_intervals = <Interval*>realloc(
        intervals.buf, (intervals.size << 1) * sizeof(Interval)
    )
    if new_intervals is NULL:
        return -1

    intervals.buf = new_intervals
    return 0


cdef size_t bisect_intervals(IntervalList *intervals, double value):
    cdef size_t lo = 0, hi = intervals.len, mid
    while lo < hi:
        mid = (lo + hi) // 2
        if value < intervals.buf[mid].start:
            hi = mid
        else:
            lo = mid + 1
    return lo


cdef inline int add_obstruction(IntervalList *obstructions, double start, double end):
    # Insert interval in obstructions while maintaining sorted order.
    cdef:
        size_t a = bisect_intervals(obstructions, start)
        size_t b = bisect_intervals(obstructions, end)

    if a > 0 and start <= obstructions.buf[a - 1].end:
        a -= 1
        start = obstructions.buf[a].start

    if b > 0 and end <= obstructions.buf[b - 1].end:
        end = obstructions.buf[b - 1].end
    elif b < obstructions.len and end == obstructions.buf[b].start:
        b += 1

    if a == b:  # Need to grow intervals
        if grow(obstructions, 1):
            return -1

        if a < obstructions.len:
            memmove(
                &obstructions.buf[a + 1],
                &obstructions.buf[a],
                (obstructions.len - a) * sizeof(Interval),
            )
        obstructions.len += 1
    elif b - 1 - a:  # Need to shrink intervals
        memmove(
            &obstructions.buf[a + 1],
            &obstructions.buf[b],
            (obstructions.len - b) * sizeof(Interval),
        )
        obstructions.len -= b - 1 - a

    obstructions.buf[a].start = start
    obstructions.buf[a].end = end
    obstructions.buf[a].center = (start + end) / 2
    return 0


cdef inline double clamp(double a, double lo, double hi):
    if a < lo:
        return lo
    if a > hi:
        return hi
    return a


cdef inline double dist(double ay, double ax, double by, double bx):
    cdef double y = ay - by, x = ax - bx
    return sqrt(y * y + x * x)


cdef inline double clight_decay(double distance, object light_decay):
    # Need a typed cdef to wrap callable `light_decay`
    return light_decay(distance)


cdef inline bint point_is_visible(
    IntervalList *obstructions,
    double start,
    double end,
    double center,
    Restrictiveness restrict,
):
    cdef:
        bint start_visible = 1, center_visible = 1, end_visible = 1
        size_t a = bisect_intervals(obstructions, start)
        size_t b = bisect_intervals(obstructions, end)
        size_t i
        Interval *obstruction

    if a > 0 and start <= obstructions.buf[a - 1].end:
        a -= 1
    if b < obstructions.len and end == obstructions.buf[b].start:
        end_visible = 1

    for i in range(a, b):
        obstruction = &obstructions.buf[i]
        if start_visible and obstruction.start <= start <= obstruction.end:
            start_visible = 0
        if center_visible and obstruction.start <= center <= obstruction.end:
            center_visible = 0
        if end_visible and obstruction.start <= end <= obstruction.end:
            end_visible = 0

    if restrict == PERMISSIVE:
        return center_visible | start_visible | end_visible
    if restrict == MODERATE:
        return center_visible & (start_visible | end_visible)
    if restrict == RESTRICTIVE:
        return center_visible & start_visible & end_visible


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void cast_shadows(
    uint8[:, :, ::1] texture,
    double[:, :, ::1] light_intensity,
    ulong[:, ::1] caster_map,
    tuple[int, int] camera_pos,
    tuple[int, int] camera_size,
    list[tuple[int, int, int, int]] tile_colors,
    list[tuple[double, double]] light_coords,
    list[tuple[int, int, int]] light_colors,
    str restrictiveness,
    unsigned int radius,
    double smoothing,
    bint not_visible_blocks,
    object light_decay,
):
    cdef Restrictiveness restrict

    if restrictiveness == "permissive":
        restrict = PERMISSIVE
    elif restrictiveness == "moderate":
        restrict = MODERATE
    elif restrictiveness == "restrictive":
        restrict = RESTRICTIVE
    else:
        restrict = PERMISSIVE

    cdef size_t h = texture.shape[0], w = texture.shape[1]
    if h == 0 or w == 0:
        return

    cdef size_t camera_h = camera_size[0], camera_w = camera_size[1]
    if camera_h == 0 or camera_w == 0:
        return

    cdef size_t map_h = caster_map.shape[0], map_w = caster_map.shape[1]
    if map_h == 0 or map_w == 0:
        return

    cdef IntervalList obstructions
    if init_intervals(&obstructions):
        raise MemoryError

    cdef:
        size_t i, j
        int k, m
        size_t nlights = len(light_coords)
        int origin_y, origin_x, y, x, offset_y, offset_x
        int camera_y = camera_pos[0], camera_x = camera_pos[1]
        double scale_y = camera_h / h, scale_x = camera_w / w
        double theta, distance, decay, start, end, center, map_y, map_x
        double smooth_radius = <double>radius + smoothing
        int scaled_radius
        double light_y, light_x
        uint8 r, g, b
        Octant *octant

    for i in range(nlights):
        light_y = light_coords[i][0]
        light_x = light_coords[i][1]

        r = light_colors[i][0]
        g = light_colors[i][1]
        b = light_colors[i][2]

        origin_y = <int>round((light_y - camera_y) / scale_y)
        origin_x = <int>round((light_x - camera_x) / scale_x)

        # Since the octants will be spread around the origin, the origin is handled
        # separately.
        if 0 <= origin_y < h and 0 <= origin_x < w:
            decay = clight_decay(0, light_decay)
            light_intensity[origin_y, origin_x, 0] += r * decay
            light_intensity[origin_y, origin_x, 1] += g * decay
            light_intensity[origin_y, origin_x, 2] += b * decay

        for j in range(8):
            obstructions.len = 0
            octant = &OCTANTS[j]

            # Spread octants around origin so they don't intersect using these offsets.
            # This caster doesn't just mark cells visible or not visible, it
            # determines the brightness of a cell by the distance from the light
            # source. If octants intersected, bright lines would show along their
            # intersection.
            offset_y = octant.y
            offset_x = octant.x
            if offset_y * offset_x > 0:
                offset_y *= 1 - octant.flipped
            else:
                offset_x *= octant.flipped
            if octant.flipped:
                scaled_radius = <int>(radius / scale_x)
            else:
                scaled_radius = <int>(radius / scale_y)

            for k in range(scaled_radius):
                if (
                    obstructions.len == 1
                    and obstructions.buf[0].start == 0.0
                    and obstructions.buf[0].end == 1.0
                ):
                    break

                if octant.flipped:
                    x = origin_x + offset_x + k * octant.x
                else:
                    y = origin_y + offset_y + k * octant.y

                theta = 1.0 / <double>(k + 1)

                for m in range(k + 1):
                    if octant.flipped:
                        y = origin_y + offset_y + m * octant.y
                    else:
                        x = origin_x + offset_x + m * octant.x

                    if y < 0 or y >= h or x < 0 or x >= w:
                        continue

                    map_y = scale_y * y + camera_y
                    map_x = scale_x * x + camera_x
                    distance = dist(light_y, light_x, map_y, map_x)

                    if distance > smooth_radius:
                        continue

                    start = m * theta
                    end = start + theta
                    center = (start + end) / 2

                    if point_is_visible(&obstructions, start, end, center, restrict):
                        decay = clight_decay(distance, light_decay)
                        light_intensity[y, x, 0] += r * decay
                        light_intensity[y, x, 1] += g * decay
                        light_intensity[y, x, 2] += b * decay

                        if map_y < 0 or map_y >= map_h or map_x < 0 or map_x >= map_w:
                            continue
                        if caster_map[<int>map_y, <int>map_x] != 0:
                            if add_obstruction(&obstructions, start, end):
                                raise MemoryError
                    elif not_visible_blocks:
                        if add_obstruction(&obstructions, start, end):
                            raise MemoryError

    free_intervals(&obstructions)

    cdef:
        double intensity_r, intensity_g, intensity_b
        uint8 a
        tuple[int, int, int, int] tile_color

    for y in range(h):
        for x in range(w):
            map_y = y * scale_y + camera_y
            map_x = x * scale_x + camera_x
            if 0 <= map_y < map_h and 0 <= map_x < map_w:
                tile_color = tile_colors[caster_map[<int>map_y, <int>map_x]]
                r = tile_color[0]
                g = tile_color[1]
                b = tile_color[2]
                a = tile_color[3]
            else:
                r = tile_colors[0][0]
                g = tile_colors[0][1]
                b = tile_colors[0][2]
                a = tile_colors[0][3]

            intensity_r = clamp(light_intensity[y, x, 0] / 255, 0.0, 1.0)
            intensity_g = clamp(light_intensity[y, x, 1] / 255, 0.0, 1.0)
            intensity_b = clamp(light_intensity[y, x, 2] / 255, 0.0, 1.0)

            texture[y, x, 0] = <uint8>(r * intensity_r)
            texture[y, x, 1] = <uint8>(g * intensity_g)
            texture[y, x, 2] = <uint8>(b * intensity_b)
            texture[y, x, 3] = a
