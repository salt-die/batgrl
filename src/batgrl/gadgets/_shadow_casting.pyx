ctypedef unsigned char uint8


cdef struct Interval:
    double start
    double end
    double center


cpdef void cast_shadows(
    uint8[:, :, ::1] texture,
    tuple[double, double] camera_coords,
    list[tuple[int, int, int, int]] tile_colors,
    list[tuple[double, double]] light_coords,
    list[tuple[int, int, int]] light_colors,
    str restrictiveness,
    unsigned int radius,
    double smoothing,
    bint not_visible_blocks,
):
    cdef size_t h = texture.shape[0], w = texture.shape[1]
