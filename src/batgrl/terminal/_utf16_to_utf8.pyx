# Ripped straight outta https://github.com/Davipb/utf8-utf16-converter/blob/master/converter/src/converter.c

from .._fbuf cimport BytesBuffer, fbuf, fbuf_putucs4

ctypedef unsigned int codepoint
ctypedef unsigned char uint8

cdef struct UTF16_STATE:
    codepoint high_surrogate
    bint high_set

# FIXME: Add function to reset this state?!?!?!
cdef UTF16_STATE utf16_state
utf16_state.high_surrogate = 0
utf16_state.high_set = 0

cdef:
    codepoint GENERIC_SURROGATE_VALUE = 0xd800
    codepoint GENERIC_SURROGATE_MASK = 0xf800
    codepoint HIGH_SURROGATE_VALUE = 0xd800
    codepoint LOW_SURROGATE_VALUE = 0xdc00
    codepoint SURROGATE_MASK = 0xfc00
    codepoint SURROGATE_CODEPOINT_OFFSET = 0x10000
    codepoint SURROGATE_CODEPOINT_MASK = 0x03ff
    unsigned char SURROGATE_CODEPOINT_BITS = 10


cpdef inline void decode_utf16(BytesBuffer buf, Py_UCS4 char):
    cdef:
        fbuf *f = &buf.f
        codepoint result, utf16 = <codepoint>char

    if utf16_state.high_set:
        utf16_state.high_set = 0

        if utf16 & SURROGATE_MASK != LOW_SURROGATE_VALUE:
            return # FIXME: Unmatched high surrogate

        result = utf16_state.high_surrogate & SURROGATE_CODEPOINT_MASK
        result <<= SURROGATE_CODEPOINT_BITS
        result |= utf16 & SURROGATE_CODEPOINT_MASK
        result += SURROGATE_CODEPOINT_OFFSET
        fbuf_putucs4(f, result)
    else:
        if utf16 & GENERIC_SURROGATE_MASK != GENERIC_SURROGATE_VALUE:
            fbuf_putucs4(f, utf16)
            return

        if utf16 & SURROGATE_MASK != HIGH_SURROGATE_VALUE:
            return # FIXME: Unmatched low surrogate

        utf16_state.high_surrogate = utf16
        utf16_state.high_set = 1
