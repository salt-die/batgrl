"""A growable string buffer."""
from libc.stdint cimport uint32_t, uint64_t

cdef extern from "_fbuf.h":
    struct fbuf:
        uint64_t size, len
        char *buf

    ssize_t write(ssize_t, const void*, size_t)
    ssize_t fbuf_init(fbuf *f)
    ssize_t fbuf_small_init(fbuf *f)
    void fbuf_free(fbuf *f)
    ssize_t fbuf_grow(fbuf *f, size_t n)
    ssize_t fbuf_put_char(fbuf *f, const char s)
    ssize_t fbuf_putn(fbuf *f, const char *s, size_t len)
    ssize_t fbuf_puts(fbuf *f, const char *s)
    ssize_t fbuf_printf(fbuf *f, const char *fmt, ...)
    ssize_t fbuf_putucs4(fbuf *f, uint32_t wc)
    unsigned int fbuf_equals(fbuf *f, const char *string, size_t len)
    unsigned int fbuf_endswith(fbuf *f, const char *suffix, size_t len)
    ssize_t fbuf_flush_fd(fbuf *f, int fd)
    ssize_t fbuf_read_fd(fbuf *f, int fd, int *size)
