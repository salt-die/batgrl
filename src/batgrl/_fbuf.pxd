from libc.stdlib cimport malloc, free, realloc
from libc.string cimport memcpy

cdef extern from "_write.h":
    int write(int, const void*, unsigned int)


cdef struct fbuf:
    Py_ssize_t size, len
    char* buf


cdef inline int fbuf_init(fbuf* f):
    f.size = 0x200000
    f.len = 0
    f.buf = <char*>malloc(f.size)
    if f.buf == NULL:
        return -1
    return 0


cdef inline void fbuf_free(fbuf* f):
    if f.buf != NULL:
        free(f.buf)
        f.buf = NULL
    f.size = 0
    f.len = 0


cdef inline int fbuf_grow(fbuf* f, Py_ssize_t n):
    if f.len + n <= f.size:
        return 0
    while f.len + n > f.size:
        f.size <<= 1

    cdef char* new_buf = <char*>realloc(f.buf, f.size)
    if new_buf == NULL:
        return -1

    f.buf = new_buf
    return 0


cdef inline int fbuf_putn(fbuf* f, const char* s, Py_ssize_t len):
    if fbuf_grow(f, len):
        return -1
    memcpy(f.buf + f.len, s, len)
    f.len += len
    return len


cdef inline int fbuf_write(int fd, fbuf* f):
    cdef Py_ssize_t written = 0, wrote
    while written < f.len:
        wrote = write(fd, f.buf + written, f.len - written)
        if wrote < 0:
            return -1
        written += wrote
    f.len = 0
    return 0
