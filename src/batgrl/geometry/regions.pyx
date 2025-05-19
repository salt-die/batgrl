from collections.abc import Iterator

from libc.stdlib cimport malloc, free, realloc
from libc.string cimport memset

from .basic import Point, Size
from .regions cimport Band, CRegion, Region


cdef Band EMPTY
memset(&EMPTY, 0, sizeof(Band))


ctypedef bint (*bool_op)(bint, bint)


cdef bint cor(bint a, bint b):
    return a | b


cdef bint cand(bint a, bint b):
    return a & b


cdef bint cxor(bint a, bint b):
    return a ^ b


cdef bint csub(bint a, bint b):
    return a & (1 - b)


cdef inline int add_wall(Band *band, int wall):
    cdef int *new_walls
    if band.len == band.size:
        new_walls = <int*>realloc(band.walls, sizeof(Band) * (band.size << 1))
        if new_walls is NULL:
            return -1
        band.size <<= 1
        band.walls = new_walls

    band.walls[band.len] = wall
    band.len += 1
    return 0


cdef inline int add_band(CRegion *region):
    cdef size_t i
    if region.len == region.size:
        new_bands = <Band*>realloc(region.bands, sizeof(Band) * (region.size << 1))
        if new_bands is NULL:
            return -1
        for i in range(region.size, region.size << 1):
            new_bands[i].walls = NULL
        region.size <<= 1
        region.bands = new_bands

    cdef Band *new_band = &region.bands[region.len]
    if new_band.walls is NULL:
        new_band.walls = <int*>malloc(sizeof(int) * 8)
        if new_band.walls is NULL:
            return -1
        new_band.size = 8
    new_band.len = 0

    region.len += 1
    return 0


cdef int merge_bands(
    int y1, int y2, Band *r, Band *s, CRegion *region, bool_op op
):
    if add_band(region) == -1:
        return -1

    cdef:
        Band *new_band = &region.bands[region.len - 1]
        size_t i = 0, j = 0
        bint inside_r = 0, inside_s = 0, inside_region = 0
        int threshold

    while i < r.len or j < s.len:
        if i >= r.len:
            threshold = s.walls[j]
            inside_s ^= 1
            j += 1
        elif j >= s.len:
            threshold = r.walls[i]
            inside_r ^= 1
            i += 1
        elif r.walls[i] < s.walls[j]:
            threshold = r.walls[i]
            inside_r ^= 1
            i += 1
        elif s.walls[j] < r.walls[i]:
            threshold = s.walls[j]
            inside_s ^= 1
            j += 1
        else:
            threshold = r.walls[i]
            inside_r ^= 1
            inside_s ^= 1
            i += 1
            j += 1

        if op(inside_r, inside_s) != inside_region:
            inside_region ^= 1
            if add_wall(new_band, threshold) == -1:
                return -1

    if new_band.len == 0:
        region.len -= 1
        return 0

    new_band.y1 = y1
    new_band.y2 = y2

    if region.len < 2:
        return 0

    cdef Band *previous = &region.bands[region.len - 2]
    if previous.y2 < new_band.y1 or previous.len != new_band.len:
        return 0

    for i in range(previous.len):
        if previous.walls[i] != new_band.walls[i]:
            return 0

    # All walls equal, extend previous band and delete new band.
    previous.y2 = new_band.y2
    region.len -= 1
    return 0


cdef int merge_regions(CRegion *a, CRegion *b, CRegion *result, bool_op op):
    cdef:
        Band *r
        Band *s
        unsigned int i = 0, j = 0
        int scanline = 0

    if a.len > 0:
        if b.len > 0:
            if a.bands[0].y1 < b.bands[0].y1:
                scanline = a.bands[0].y1
            else:
                scanline = b.bands[0].y1
        else:
            scanline = a.bands[0].y1
    elif b.len > 0:
        scanline = b.bands[0].y1

    while i < a.len and j < b.len:
        r = &a.bands[i]
        s = &b.bands[j]

        if r.y1 <= s.y1:
            if scanline < r.y1:
                scanline = r.y1
            if r.y2 <= s.y1:
                if merge_bands(scanline, r.y2, r, &EMPTY, result, op) == -1:
                    return -1
                scanline = r.y2
                i += 1
            else:
                if scanline < s.y1:
                    if merge_bands(scanline, s.y1, r, &EMPTY, result, op) == -1:
                        return -1
                    scanline = s.y1
                if r.y2 <= s.y2:
                    if merge_bands(s.y1, r.y2, r, s, result, op) == -1:
                        return -1
                    scanline = r.y2
                    i += 1
                    if r.y2 == s.y2:
                        j += 1
                else:
                    if merge_bands(s.y1, s.y2, r, s, result, op) == -1:
                        return -1
                    scanline = s.y2
                    j += 1
        else:
            if scanline < s.y1:
                scanline = s.y1
            if s.y2 <= r.y1:
                if merge_bands(scanline, s.y2, &EMPTY, s, result, op) == -1:
                    return -1
                scanline = s.y2
                j += 1
            else:
                if scanline < r.y1:
                    if merge_bands(scanline, r.y1, &EMPTY, s, result, op) == -1:
                        return -1
                    scanline = r.y1
                if s.y2 <= r.y2:
                    if merge_bands(r.y1, s.y2, r, s, result, op) == -1:
                        return -1
                    scanline = s.y2
                    j += 1
                    if s.y2 == r.y2:
                        i += 1
                else:
                    if merge_bands(r.y1, r.y2, r, s, result, op) == -1:
                        return -1
                    scanline = r.y2
                    i += 1

    while i < a.len:
        r = &a.bands[i]
        if scanline < r.y1:
            scanline = r.y1
        if merge_bands(scanline, r.y2, r, &EMPTY, result, op) == -1:
            return -1
        i += 1

    while j < b.len:
        s = &b.bands[j]
        if scanline < s.y1:
            scanline = s.y1
        if merge_bands(scanline, s.y2, &EMPTY, s, result, op) == -1:
            return -1
        j += 1

    return 0


cdef inline size_t bisect_bands(CRegion *region, int y):
    cdef size_t lo = 0, hi = region.len, mid
    while lo < hi:
        mid = (lo + hi) // 2
        if y < region.bands[mid].y1:
            hi = mid
        else:
            lo = mid + 1
    return lo


cdef inline size_t bisect_walls(Band *band, int x):
    cdef size_t lo = 0, hi = band.len, mid
    while lo < hi:
        mid = (lo + hi) // 2
        if x < band.walls[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


cdef bint contains(CRegion *cregion, int y, int x):
    cdef size_t i

    i = bisect_bands(cregion, y)
    if i == 0:
        return 0

    if cregion.bands[i - 1].y2 <= y:
        return 0

    i = bisect_walls(&cregion.bands[i - 1], x)
    return i % 2 == 1


cdef void bounding_rect(CRegion *cregion, int *y, int *x, size_t *h, size_t *w):
    if not cregion.len:
        return

    cdef:
        size_t i
        int min_x = cregion.bands[0].walls[0], max_x = min_x
        Band *band

    for i in range(cregion.len):
        band = &cregion.bands[i]
        if band.walls[0] < min_x:
            min_x = band.walls[0]
        if band.walls[band.len - 1] > max_x:
            max_x = band.walls[band.len - 1]

    y[0] = cregion.bands[0].y1
    h[0] = cregion.bands[cregion.len - 1].y2 - y[0]
    x[0] = min_x
    w[0] = max_x - min_x


cdef class Region:
    def __cinit__(self):
        self.cregion.bands = <Band*>malloc(sizeof(Band) * 8)
        if self.cregion.bands is NULL:
            raise MemoryError
        cdef int i
        for i in range(8):
            self.cregion.bands[i].walls = NULL
        self.cregion.size = 8
        self.cregion.len = 0

    def __dealloc__(self):
        if self.cregion.bands is NULL:
            return

        cdef size_t i
        for i in range(self.cregion.len):
            if self.cregion.bands[i].walls is not NULL:
                free(self.cregion.bands[i].walls)
                self.cregion.bands[i].walls = NULL
        free(self.cregion.bands)
        self.cregion.bands = NULL

    @classmethod
    def from_rect(cls, pos: Point, size: Size) -> Region:
        out = Region()
        if size[0] == 0 or size[1] == 0:
            return out

        if add_band(&out.cregion) == -1:
            raise MemoryError

        cdef:
            int y, x, h, w
            Band *band

        y, x = pos
        h, w = size
        band = &out.cregion.bands[0]
        band.y1 = y
        band.y2 = y + h
        band.walls[0] = x
        band.walls[1] = x + w
        band.len = 2

        return out

    def __str__(self) -> str:
        cdef Band *band
        band_reprs = []
        for i in range(self.cregion.len):
            band = &self.cregion.bands[i]
            walls = [band.walls[i] for i in range(band.len)]
            band_reprs.append(f"Band(y1={band.y1}, y2={band.y2}, walls={walls})")
        return f"Region(bands=[{', '.join(band_reprs)}])"

    def __and__(self, other: Region) -> Region:
        out = Region()
        if merge_regions(&self.cregion, &other.cregion, &out.cregion, cand) == -1:
            raise MemoryError
        return out

    def __or__(self, other: Region) -> Region:
        out = Region()
        if merge_regions(&self.cregion, &other.cregion, &out.cregion, cor) == -1:
            raise MemoryError
        return out

    def __add__(self, other: Region) -> Region:
        out = Region()
        if merge_regions(&self.cregion, &other.cregion, &out.cregion, cor) == -1:
            raise MemoryError
        return out

    def __sub__(self, other: Region) -> Region:
        out = Region()
        if merge_regions(&self.cregion, &other.cregion, &out.cregion, csub) == -1:
            raise MemoryError
        return out

    def __xor__(self, other: Region) -> Region:
        out = Region()
        if merge_regions(&self.cregion, &other.cregion, &out.cregion, cxor) == -1:
            raise MemoryError
        return out

    def __bool__(self) -> bool:
        return self.cregion.len > 0

    def __eq__(self, other: Region) -> bool:
        if not isinstance(other, Region):
            return False
        
        cdef:
            size_t i, j
            Band *r
            Band *s
        if self.cregion.len != other.cregion.len:
            return False
        for i in range(self.cregion.len):
            r = &self.cregion.bands[i]
            s = &other.cregion.bands[i]
            if r.y1 != s.y1 or r.y2 != s.y2 or r.len != s.len:
                return False
            for j in range(r.len):
                if r.walls[j] != s.walls[j]:
                    return False
        return True

    def __contains__(self, point: Point) -> bool:
        cdef int y = point[0], x = point[1]
        return contains(&self.cregion, y, x)

    def rects(self) -> Iterator[tuple[Point, Size]]:
        cdef:
            size_t i, j
            Band *band

        for i in range(self.cregion.len):
            band = &self.cregion.bands[i]
            j = 0
            while j < band.len:
                yield (
                    Point(band.y1, band.walls[j]),
                    Size(band.y2 - band.y1, band.walls[j + 1] - band.walls[j]),
                )
                j += 2
