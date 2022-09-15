"""
Rebuild nurses_2 documentation and copy html files to ../docs

Expected directory structure:
    nurses_2
    ├ docs
    ├ docsrc
    │ ├ regen_docs.py  # This file.
    │ └ ...
    └ ...
"""
from pathlib import Path

DOC_SRC = Path(__file__).absolute().parent
DOCS = DOC_SRC.parent / "docs"

SPHINX_BUILD = "sphinx-build"
SOURCE_DIR = "."
BUILD_DIR = "_build"
SPHINX_COMMAND = [SPHINX_BUILD, "-M", "html", SOURCE_DIR, BUILD_DIR]

DIRECTORIES_TO_REMOVE = (
    DOCS,
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

    shutil.copytree(DOC_SRC / BUILD_DIR / "html", DOCS)
    (DOCS / ".nojekyll").touch()
