from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Letter = Literal[
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]


@dataclass
class Node:
    letter: Letter | None = None
    dash: Node | None = None
    dot: Node | None = None


TREE = Node()
TREE.dash = Node("T")
TREE.dot = Node("E")
TREE.dot.dot = Node("I")
TREE.dot.dash = Node("A")
TREE.dash.dot = Node("N")
TREE.dash.dash = Node("M")
TREE.dot.dot.dot = Node("S")
TREE.dot.dot.dash = Node("U")
TREE.dot.dash.dot = Node("R")
TREE.dot.dash.dash = Node("W")
TREE.dash.dot.dot = Node("D")
TREE.dash.dot.dash = Node("K")
TREE.dash.dash.dot = Node("G")
TREE.dash.dash.dash = Node("O")
TREE.dot.dot.dot.dot = Node("H")
TREE.dot.dot.dot.dash = Node("V")
TREE.dot.dot.dash.dot = Node("F")
TREE.dot.dash.dot.dash = Node("L")
TREE.dot.dash.dash.dot = Node("P")
TREE.dot.dash.dash.dash = Node("J")
TREE.dash.dot.dot.dot = Node("B")
TREE.dash.dot.dot.dash = Node("X")
TREE.dash.dot.dash.dot = Node("C")
TREE.dash.dot.dash.dash = Node("Y")
TREE.dash.dash.dot.dot = Node("Z")
TREE.dash.dash.dot.dash = Node("Q")
