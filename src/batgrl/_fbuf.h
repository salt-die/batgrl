// This is nearly verbatim notcurses' fbuf.h, but in cython.
// notcurses' fbuf.h:
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
    typedef SSIZE_T ssize_t;
#else
    #include <unistd.h>
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
    if(f->buf == NULL){
        return -1;
    }
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
    if(f->len + n <= f->size){
        return 0;
    }
    while(f->len + n > f->size){
        f->size *= 2;
    }
    void *tmp = realloc(f->buf, f->size);
    if(tmp == NULL){
        return -1;
    }
    f->buf = (char*)tmp;
    return 0;
}


static inline ssize_t fbuf_putn(fbuf *f, const char *s, size_t len){
    if(fbuf_grow(f, len)){
        return -1;
    }
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
        if(fbuf_grow(f, BUFSIZ)){
            return -1;
        }
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
    }if(wc < 0x110000) {
        f->buf[f->len++] = (wc>>18) | 0xF0;
        f->buf[f->len++] = ((wc>>12) & 0x3F) | 0x80;
        f->buf[f->len++] = ((wc>>6) & 0x3F) | 0x80;
        f->buf[f->len++] = (wc & 0x3F) | 0x80;
        return 0;
    }
    return -1;
}


#ifdef _WIN32
static inline ssize_t fbuf_flush(fbuf *f){
    DWORD wrote = 0, write_len;
    size_t written = 0;
    while(written<f->len){
        if(f->len - written > MAXDWORD){
            write_len = MAXDWORD;
        } else {
            write_len = f->len - written;
        }
        if (!WriteConsoleA( // ! Any reason to use WriteFile instead?
            GetStdHandle(STD_OUTPUT_HANDLE), f->buf + written, write_len, &wrote, NULL)
        ){
            return -1;
        }
        written += wrote;
    }
    f->len = 0;
    return 0;
}
#else
static inline ssize_t fbuf_flush(fbuf *f){
    size_t written = 0;
    ssize_t wrote = 0;
    while(written < f->len){
        wrote = write(1, f->buf + written, f->len - written);
        if (wrote < 0){
            return -1;
        }
        written += wrote;
    }
    f->len = 0;
    return 0;
}
#endif
