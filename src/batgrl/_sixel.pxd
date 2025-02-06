from ._fbuf cimport fbuf

cdef:
    struct qnode:
        unsigned char[3] srgb
        unsigned long pop
        unsigned int qlink
        unsigned int cidx

    struct onode:
        (qnode *)[8] q

    struct qstate:
        qnode *qnodes
        onode *onodes
        unsigned int dynnodes_free
        unsigned int dynnodes_total
        unsigned onodes_free
        unsigned onodes_total
        unsigned long ncolors
        unsigned char *table

    int sixel(
        fbuf *f,
        qstate *qs,
        unsigned char[:, :, ::1] texture,
        unsigned char[:, :, ::1] stexture,
        unsigned int aspect_h,
        unsigned int aspect_w,
        size_t oy,
        size_t ox,
        size_t h,
        size_t w,
    )

    class OctTree:
        cdef qstate qs
