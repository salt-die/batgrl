cdef size_t median_variance_quantization(
    unsigned char[:, :, ::1] texture,
    size_t oy,
    size_t ox,
    size_t h,
    size_t w,
    palette,
    indices,
)
