// Mostly unashamedly stolen from notcurses' fbuf.h:
//   https://github.com/dankamongmen/notcurses/blob/master/src/lib/fbuf.h
//
// notcurses is copyright 2019-2025 Nick Black et al and is licensed under the Apache
// License, Version 2.0:
//   http://www.apache.org/licenses/LICENSE-2.0
//

#include <stdio.h>
#include <stdint.h>
#ifdef _WIN32
    #include <Windows.h>
    #include <io.h>
    typedef SSIZE_T ssize_t;
#else
    #include <unistd.h>
    #include <poll.h>
#endif


typedef struct fbuf {
  uint64_t size;
  uint64_t len;
  char *buf;
} fbuf;


static inline ssize_t fbuf_init(fbuf *f){
    f->size = 0x200000ul;
    f->len = 0;
    f->buf = (char*)malloc(f->size);
    if(f->buf == NULL) return -1;
    return 0;
}


static inline ssize_t fbuf_small_init(fbuf *f){
    f->size = 0x200ul;
    f->len = 0;
    f->buf = (char*)malloc(f->size);
    if(f->buf == NULL) return -1;
    return 0;
}


static inline void fbuf_free(fbuf *f){
    f->size = 0;
    f->len = 0;
    if(f->buf != NULL){
        free(f->buf);
        f->buf = NULL;
    }
}


static inline ssize_t fbuf_grow(fbuf *f, size_t n){
    if(f->len + n <= f->size) return 0;
    while(f->len + n > f->size){
        f->size *= 2;
    }
    void *tmp = realloc(f->buf, f->size);
    if(tmp == NULL) return -1;
    f->buf = (char*)tmp;
    return 0;
}


static inline ssize_t fbuf_put_char(fbuf *f, const char s){
    if(fbuf_grow(f, 1)) return -1;
    f->buf[f->len++] = s;
    return 0;
}


static inline ssize_t fbuf_putn(fbuf *f, const char *s, size_t len){
    if(fbuf_grow(f, len)) return -1;
    memcpy(f->buf + f->len, s, len);
    f->len += len;
    return 0;
}


static inline ssize_t fbuf_puts(fbuf *f, const char *s){
  size_t slen = strlen(s);
  return fbuf_putn(f, s, slen);
}


static inline ssize_t fbuf_printf(fbuf *f, const char *fmt, ...){
    size_t unused = f->size - f->len;
    if(unused < BUFSIZ){
        if(fbuf_grow(f, BUFSIZ))return -1;
    }
    va_list va;
    va_start(va, fmt);
    size_t wrote = (size_t)vsnprintf(f->buf + f->len, unused, fmt, va);
    va_end(va);
    f->len += wrote;
    return 0;
}


static inline ssize_t fbuf_putucs4(fbuf *f, uint32_t wc){
    // Put PY_UCS4 as utf8.
    // https://github.com/JeffBezanson/cutef8/blob/master/utf8.c
    if(fbuf_grow(f, 4)){
        return -1;
    }
    if(wc < 0x80){
        f->buf[f->len++] = (char)wc;
        return 0;
    }
    if(wc < 0x800){
        f->buf[f->len++] = (wc>>6) | 0xC0;
        f->buf[f->len++] = (wc & 0x3F) | 0x80;
        return 0;
    }
    if(wc < 0x10000){
        f->buf[f->len++] = (wc>>12) | 0xE0;
        f->buf[f->len++] = ((wc>>6) & 0x3F) | 0x80;
        f->buf[f->len++] = (wc & 0x3F) | 0x80;
        return 0;
    }
    if(wc < 0x110000) {
        f->buf[f->len++] = (wc>>18) | 0xF0;
        f->buf[f->len++] = ((wc>>12) & 0x3F) | 0x80;
        f->buf[f->len++] = ((wc>>6) & 0x3F) | 0x80;
        f->buf[f->len++] = (wc & 0x3F) | 0x80;
        return 0;
    }
    return -1;
}


static inline unsigned int fbuf_equals(fbuf *f, const char *string, size_t len){
    if(f->len != len) return 0;
    for(size_t i = 0; i < len; i++){
        if(f->buf[i] != string[i]) return 0;
    }
    return 1;
}


static inline unsigned int fbuf_endswith(fbuf *f, const char *suffix, size_t len){
    if(len > f->len) return 0;
    size_t offset = f->len - len;
    for(size_t i = 0; i < len; i++ ){
        if(f->buf[offset + i] != suffix[i]) return 0;
    }
    return 1;
}


#ifdef _WIN32
static inline ssize_t fbuf_flush_fd(fbuf *f, int fd){
    HANDLE handle = (HANDLE)_get_osfhandle(fd);
    DWORD wrote = 0, write_len;
    size_t written = 0;
    while(written<f->len){
        if(f->len - written > MAXDWORD){
            write_len = MAXDWORD;
        }else{
            write_len = (DWORD)(f->len - written);
        }
        if (!WriteConsoleA(handle, f->buf + written, write_len, &wrote, NULL)){
            return -1;
        }
        written += wrote;
    }
    f->len = 0;
    return 0;
}


typedef unsigned long codepoint;
codepoint GENERIC_SURROGATE_MASK = 0xf800;
codepoint GENERIC_SURROGATE_VALUE = 0xd800;
codepoint SURROGATE_MASK = 0xfc00;
codepoint HIGH_SURROGATE_VALUE = 0xd800;
codepoint LOW_SURROGATE_VALUE = 0xdc00;
codepoint SURROGATE_CODEPOINT_MASK = 0x03ff;
codepoint SURROGATE_CODEPOINT_OFFSET = 0x10000;
unsigned char SURROGATE_CODEPOINT_BITS = 10;
codepoint _HIGH_SURROGATE = 0;


static inline ssize_t decode_utf16(fbuf *f, unsigned short utf16){
    if((utf16 & GENERIC_SURROGATE_MASK) != GENERIC_SURROGATE_VALUE){
        _HIGH_SURROGATE = 0;
        if(fbuf_putucs4(f, (codepoint)utf16)) return -1;
    }else if((utf16 & SURROGATE_MASK) == HIGH_SURROGATE_VALUE){
        _HIGH_SURROGATE = (codepoint)utf16;
    }else if(
        ((utf16 & SURROGATE_MASK) == LOW_SURROGATE_VALUE) && _HIGH_SURROGATE
    ){
        codepoint result = _HIGH_SURROGATE & SURROGATE_CODEPOINT_MASK;
        result <<= SURROGATE_CODEPOINT_BITS;
        result |= utf16 & SURROGATE_CODEPOINT_MASK;
        result += SURROGATE_CODEPOINT_OFFSET;
        _HIGH_SURROGATE = 0;
        if(fbuf_putucs4(f, result)) return -1;
    }
    return 0;
}


static inline ssize_t fbuf_read_fd(fbuf *f, int fd, int *size_event){
    HANDLE handle = (HANDLE)_get_osfhandle(fd);
    DWORD nevents, events_to_read, events_read;
    if(!GetNumberOfConsoleInputEvents(handle, &nevents)) return -1;
    INPUT_RECORD *records = (INPUT_RECORD*)malloc(sizeof(INPUT_RECORD) * nevents);
    if(!records) return -1;
    events_to_read = nevents;
    while(events_to_read){
        if(!ReadConsoleInputW(handle, records, nevents, &events_read)){
            free(records);
            return -1;
        }
        events_to_read -= events_read;
    }
    for(size_t i = 0; i < nevents; i++){
        INPUT_RECORD *record = &records[i];
        if(record->EventType == KEY_EVENT){
            if(!record->Event.KeyEvent.bKeyDown) continue;
            if(
                record->Event.KeyEvent.dwControlKeyState
                && !record->Event.KeyEvent.wVirtualKeyCode
            ) continue;
            if(decode_utf16(f, record->Event.KeyEvent.uChar.UnicodeChar)){
                free(records);
                return 1;
            }
        }else if(record->EventType == WINDOW_BUFFER_SIZE_EVENT){
            size_event[0] = (int)record->Event.WindowBufferSizeEvent.dwSize.Y;
            size_event[1] = (int)record->Event.WindowBufferSizeEvent.dwSize.X;
        }
    }
    free(records);
    return 0;
}
#else
static inline ssize_t fbuf_flush_fd(fbuf *f, int fd){
    size_t written = 0;
    ssize_t wrote = 0;
    while(written < f->len){
        wrote = write(fd, f->buf + written, f->len - written);
        if (wrote < 0) return -1;
        written += wrote;
    }
    f->len = 0;
    return 0;
}


static inline ssize_t fbuf_read_fd(fbuf *f, int fd, int *size_event){
    struct pollfd pfd = {
        .fd = fd,
        .events = POLLIN,
    };
    size_t MAX_READ = 1024;

    while(1){
        int retval = poll(&pfd, 1, 0);
        if(retval == 0) return 0;
        if(retval < 0) return -1;
        if(fbuf_grow(f, MAX_READ)) return 1;
        ssize_t amt = read(fd, f->buf + f->len, MAX_READ);
        if(amt < 0) return -1;
        f->len += amt;
    }
}
#endif
