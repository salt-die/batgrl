from ._fbuf cimport fbuf, fbuf_init, fbuf_free, fbuf_write, fbuf_putn, setmode
from sys import stdout
from cpython.exc cimport PyErr_SetFromErrno
import platform

cdef class MyClass:
    cdef fbuf f

    def __cinit__(self):
        setmode(stdout.fileno(), 0x00040000)  # Does nothing on linux
        if fbuf_init(&self.f):
            raise MemoryError

    def __dealloc__(self):
        fbuf_free(&self.f)

    cpdef write(self, str s):
        if platform.platform().startswith("Win"):
            encoding = "utf-16"
        else:
            encoding = "utf-8"
        b = s.encode(encoding)
        fbuf_putn(&self.f, b, len(b))
        if fbuf_write(stdout.fileno(), &self.f):
            PyErr_SetFromErrno(OSError)
