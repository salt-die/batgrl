cdef struct Band:
    int y1, y2
    size_t size, len
    int *walls


cdef struct CRegion:
    size_t size, len
    Band *bands


cdef class Region:
    cdef CRegion cregion


cdef bint contains(CRegion *cregion, int y, int x)
cdef void bounding_rect(CRegion *cregion, int *y, int *x, size_t *h, size_t *w)
