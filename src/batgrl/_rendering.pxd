from libc.stdint cimport uint32_t


cdef packed struct Cell:
    uint32_t ord
    unsigned char style
    unsigned char[3] fg_color
    unsigned char[3] bg_color
