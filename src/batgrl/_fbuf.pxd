"""A growable string buffer."""

cdef extern from "_fbuf.h":
    ctypedef unsigned long uint32_t
    ctypedef unsigned long long uint64_t

    struct fbuf:
        uint64_t size, len
        char *buf

    ssize_t write(ssize_t, const void*, size_t)
    ssize_t fbuf_init(fbuf *f)
    void fbuf_free(fbuf *f)
    ssize_t fbuf_grow(fbuf *f, size_t n)
    ssize_t fbuf_putn(fbuf *f, const char *s, size_t len)
    ssize_t fbuf_puts(fbuf *f, const char *s)
    ssize_t fbuf_printf(fbuf *f, const char *fmt, ...)
    ssize_t fbuf_putucs4(fbuf *f, uint32_t wc)
    ssize_t fbuf_flush(fbuf *f)


cdef class BytesBuffer:
    cdef fbuf f
