from ._fbuf cimport fbuf

cdef ssize_t csixel_ansi(
    fbuf* f, 
    unsigned char[:, ::1] palette, 
    unsigned char[:, ::1] indices, 
    unsigned char[:, :, ::1] texture,
)