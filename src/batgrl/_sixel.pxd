from ._fbuf cimport fbuf

cdef ssize_t csixel_ansi(
    fbuf *f,
    unsigned char[:, ::1] palette,
    unsigned char[:, ::1] indices,
    unsigned char[:, :, ::1] texture,
    unsigned int aspect_h,
    unsigned int aspect_w,
    size_t ncolors,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
)
