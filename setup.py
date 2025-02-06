"""Build cython extensions and generated files."""

import sys

import numpy as np
from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.build_py import build_py
from wcwidth import wcwidth

_CWIDTH_HEADER = """\
#ifndef _WIN32
    #include <stddef.h>
#endif
#include "cwidth.h"


int cwidth(uint32_t wc) {
    // Character widths as generated by wcwidth.
    // Each item in `CHAR_WIDTHS` represents an interval of ords with common width,
    // i.e., `{0u, 31u, 0u}` means ords 0 through 31 (inclusive) have width 0.
    // Intervals with width 1 are omitted so if an ord doesn't belong to any interval
    // we can assume it has width 1.
    static const uint32_t CHAR_WIDTHS[][3] = {
"""
_CWIDTH_FOOTER = """\
    };
    static const size_t CHAR_WIDTHS_LEN = sizeof(CHAR_WIDTHS) / sizeof(int[3]);

    size_t lo = 0, hi = CHAR_WIDTHS_LEN, mid;
    while(lo < hi) {
        mid = (lo + hi) / 2;
        if(wc < CHAR_WIDTHS[mid][0]) hi = mid;
        else if(wc > CHAR_WIDTHS[mid][1]) lo = mid + 1;
        else return CHAR_WIDTHS[mid][2];
    }
    return 1;
}
"""


def _create_cwidth():
    """
    Build ``cwidth.c``.

    This function builds the table used in ``cwidth.c`` needed to determine displayed
    width of a character in the terminal. The widths are taken directly from `wcwidth`,
    but the ``cwidth`` function is a couple of magnitude times faster than
    ``wcwidth.wcwidth``.
    """
    groups = []
    start = 0
    group_width = 1
    for codepoint in range(sys.maxunicode + 1):
        char_width = max(wcwidth(chr(codepoint)), 0)
        if char_width != group_width:
            if group_width != 1:
                groups.append((start, codepoint - 1, group_width))
            group_width = char_width
            start = codepoint

    if group_width != 1:
        groups.append((start, codepoint, group_width))

    with open("src/batgrl/cwidth.c", "w") as file:
        file.write(_CWIDTH_HEADER)
        for group in groups:
            file.write("        {{{}u, {}u, {}u}},\n".format(*group))
        file.write(_CWIDTH_FOOTER)


class build_py_with_cwidth(build_py):
    """Generate ``cwidth.c`` on build."""

    def run(self):
        """Generate ``cwidth.c`` on build."""
        super().run()
        _create_cwidth()


setup(
    ext_modules=cythonize(
        [
            "src/batgrl/_fbuf.pyx",
            "src/batgrl/_rendering.pyx",
            "src/batgrl/_sixel.pyx",
            "src/batgrl/char_width.pyx",
            "src/batgrl/geometry/regions.pyx",
        ]
    ),
    include_dirs=[np.get_include()],
    cmdclass={"build_py": build_py_with_cwidth},
)
