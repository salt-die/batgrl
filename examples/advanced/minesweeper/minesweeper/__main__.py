from batgrl.app import run_gadget_as_app

from .minesweeper import MineSweeper

if __name__ == "__main__":
    run_gadget_as_app(MineSweeper(), title="MineSweeper")
