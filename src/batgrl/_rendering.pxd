cdef packed struct Cell:
    Py_UCS4 char_
    unsigned char bold
    unsigned char italic
    unsigned char underline
    unsigned char strikethrough
    unsigned char overline
    unsigned char reverse
    unsigned char[3] fg_color
    unsigned char[3] bg_color
