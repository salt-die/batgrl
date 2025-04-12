cdef packed struct Cell:
    unsigned long ord
    unsigned char style
    unsigned char[3] fg_color
    unsigned char[3] bg_color
