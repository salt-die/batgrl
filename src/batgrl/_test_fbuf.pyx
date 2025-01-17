from ._fbuf cimport fbuf, fbuf_init, fbuf_free, fbuf_flush, fbuf_putn, get_value
from sys import stdout
from cpython.exc cimport PyErr_SetFromErrno


cdef class CharBuffer:
    cdef fbuf f

    def __cinit__(self):
        if fbuf_init(&self.f):
            raise MemoryError

    def __dealloc__(self):
        fbuf_free(&self.f)

    cpdef write(self, str s):
        b = s.encode()
        fbuf_putn(&self.f, b, len(b))

    cpdef flush(self):
        if fbuf_flush(&self.f, stdout.fileno()):
            PyErr_SetFromErrno(OSError)

    cpdef get_value(self):
        return get_value(&self.f)


def test():
    c = CharBuffer()
    for test in ["1", "▙", "𜴓"]:
        c.write(test)
        print("get value: ", c.get_value())
        print("flush: ", flush=True, end="")
        c.flush()
        print()
