"""
Rebuild nurses_2 documentation.
"""
from pathlib import Path

DOCS = Path(__file__).absolute().parent
SPHINX_BUILD = "sphinx-build"
BUILD_DIR = "_build"
DIRECTORIES_TO_CLEAN = (
    DOCS / BUILD_DIR,
    DOCS / "reference" / "generated",
)


def recursive_remove_dir(path: Path):
    for child in path.iterdir():
        if child.is_file():
            child.unlink()
        else:
            recursive_remove_dir(child)
    path.rmdir()


if __name__ == "__main__":
    import os
    import subprocess

    for directory in DIRECTORIES_TO_CLEAN:
        if directory.exists():
            for path in directory.iterdir():
                if (
                    path.is_file()
                    and path.suffix != ".git"
                    and path.suffix != ".pre-commit-config.yaml"
                ):
                    path.unlink()
                elif path.is_dir():
                    recursive_remove_dir(path)

    if not (DOCS / BUILD_DIR).exists():
        (DOCS / BUILD_DIR).mkdir()

    os.chdir(DOCS / BUILD_DIR)
    subprocess.run(["git", "worktree", "add", "-f", "html", "gh-pages"])

    os.chdir(DOCS)
    subprocess.run([SPHINX_BUILD, "-M", "html", ".", BUILD_DIR])

    (DOCS / BUILD_DIR / "html" / ".nojekyll").touch()
