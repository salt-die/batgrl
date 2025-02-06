# distutils: language = c
# distutils: sources = src/batgrl/cwidth.c

cdef extern from "cwidth.h":
    int cwidth(Py_UCS4)

cdef extern from "Python.h":
    Py_ssize_t PyUnicode_GetLength(object)
    void *PyUnicode_DATA(object)
    int PyUnicode_KIND(object)
    Py_UCS4 PyUnicode_READ(int, void*, Py_ssize_t)
    Py_UCS4 PyUnicode_READ_CHAR(object, Py_ssize_t)


cpdef int char_width(str char):
    if not PyUnicode_GetLength(char):
        return 0
    return cwidth(PyUnicode_READ_CHAR(char, 0))


cpdef int str_width(str chars):
    cdef:
        int width = 0
        Py_ssize_t length = PyUnicode_GetLength(chars), i
        const void *chars_buffer = PyUnicode_DATA(chars)
        int kind = PyUnicode_KIND(chars)

    for i in range(length):
        width += cwidth(PyUnicode_READ(kind, chars_buffer, i))
    return width
