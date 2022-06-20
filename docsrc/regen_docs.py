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

EXCLUDED_FILES = (
    DOC_SRC / "conf.py",
    DOC_SRC / "index.rst",
    DOC_SRC / "regen_docs.py",
    DOC_SRC / "requirements.txt",
)

SPHINX_BUILD = "sphinx-build"
SOURCE_DIR = "."
BUILD_DIR = "_build"
SPHINX_COMMAND = [SPHINX_BUILD, "-M", "html", SOURCE_DIR, BUILD_DIR]

if __name__ == "__main__":
    import os
    import shutil
    import subprocess

    os.chdir(DOC_SRC)

    for item in list(DOC_SRC.iterdir()):
        if item.is_dir():
            shutil.rmtree(item)
        elif item not in EXCLUDED_FILES:
            item.unlink()

    subprocess.run(SPHINX_COMMAND)

    try:
        shutil.rmtree(DOCS)
    except FileNotFoundError:
        pass

    shutil.copytree(DOC_SRC / BUILD_DIR / "html", DOCS)
    (DOCS / ".nojekyll").touch()
