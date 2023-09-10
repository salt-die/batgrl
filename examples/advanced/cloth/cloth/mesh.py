import numpy as np

from .link import Link
from .node import Node


class Mesh:
    def __init__(self, size, *, nanchors=None):
        height, width = size

        # Create a grid of nodes.
        nodes = [
            [Node(position=complex(y, x)) for x in range(width)] for y in range(height)
        ]

        # Link adjacent nodes.
        links = []
        for y in range(height):
            for x in range(width):
                a = nodes[y][x]

                if y != height - 1:  # attach down
                    b = nodes[y + 1][x]
                    links.append(Link(a, b))

                if x != width - 1:  # attach right
                    b = nodes[y][x + 1]
                    links.append(Link(a, b))

        if nanchors is None:  # Anchor entire top row.
            for node in nodes[0]:
                node.is_anchored = True
        elif nanchors == 1:  # Anchor midpoint of top row.
            nodes[0][width // 2].is_anchored = True
        else:  # Evenly spaced nanchors anchors on top row.
            for i in np.linspace(0, width - 1, nanchors).astype(int):
                nodes[0][i].is_anchored = True

        self.nodes = [node for row in nodes for node in row]  # flatten
        self.links = links

    def step(self):
        for link in self.links:
            link.step()

        for node in self.nodes:
            node.step()
