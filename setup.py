"""Build cython extensions."""

import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(
        [
            "src/batgrl/geometry/regions.pyx",
            "src/batgrl/colors/quantization.pyx",
            "src/batgrl/_rgb_to_sixel.pyx",
        ]
    ),
    include_dirs=[np.get_include()],
)
