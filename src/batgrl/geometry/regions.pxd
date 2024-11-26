cdef struct Band:
    int y1, y2
    Py_ssize_t size, len
    int* walls


cdef struct CRegion:
    Py_ssize_t size, len
    Band* bands


cdef class Region:
    cdef CRegion cregion
