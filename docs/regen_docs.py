"""
Rebuild nurses_2 documentation.
"""
from pathlib import Path

DOC_SRC = Path(__file__).absolute().parent

SPHINX_BUILD = "sphinx-build"
SOURCE_DIR = "."
BUILD_DIR = "_build"
SPHINX_COMMAND = [SPHINX_BUILD, "-M", "html", SOURCE_DIR, BUILD_DIR]

DIRECTORIES_TO_REMOVE = (
    DOC_SRC / BUILD_DIR,
    DOC_SRC / "reference" / "generated",
)

if __name__ == "__main__":
    import os
    import shutil
    import subprocess

    os.chdir(DOC_SRC)

    for directory in DIRECTORIES_TO_REMOVE:
        if directory.exists():
            shutil.rmtree(directory)

    subprocess.run(SPHINX_COMMAND)

    (DOC_SRC / BUILD_DIR / "html" / ".nojekyll").touch()
