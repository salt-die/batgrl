"""A growable string buffer."""

cdef extern from "_fbuf.h":
    struct fbuf:
        unsigned long long size, len
        char* buf

    ssize_t write(ssize_t, const void*, size_t)
    ssize_t fbuf_init(fbuf* f)
    void fbuf_free(fbuf* f)
    ssize_t fbuf_grow(fbuf* f, size_t n)
    ssize_t fbuf_putn(fbuf* f, const char* s, size_t len)
    ssize_t fbuf_printf(fbuf *f, const char* fmt, ...)
    ssize_t fbuf_flush(fbuf* f, int fd)


cdef inline bytes get_value(fbuf* f):
    return f.buf[:f.len]
