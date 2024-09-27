"""Build cython extensions."""

from Cython.Build import cythonize
from setuptools import setup

setup(ext_modules=cythonize(["src/batgrl/geometry/regions.pyx"]))
