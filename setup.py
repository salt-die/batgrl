"""Build cython extensions."""

import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(
        [
            "src/batgrl/_fbuf.pyx",
            "src/batgrl/_rendering.pyx",
            "src/batgrl/_sixel.pyx",
            "src/batgrl/gadgets/_raycasting.pyx",
            "src/batgrl/gadgets/_shadow_casting.pyx",
            "src/batgrl/geometry/regions.pyx",
        ]
    ),
    include_dirs=[np.get_include()],
)
