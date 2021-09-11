from .node import Node
from .link import Link

GRAVITY = 1500 + 0j


class Mesh:
    def __init__(self, size):
        height, width = size

        nodes = [
            [Node(complex(y, x)) for x in range(width)]
            for y in range(height)
        ]

        links = [ ]
        for y in range(height):
            for x in range(width):
                a = nodes[y][x]

                if y != height - 1:  # attach down
                    b = nodes[y + 1][x]
                    links.append(Link(a, b))

                if x != width - 1:  # attach right
                    b = nodes[y][x + 1]
                    links.append(Link(a, b))

        for node in nodes[0]:
            node.is_anchored = True

        self.nodes = [node for row in nodes for node in row]  # flatten
        self.links = links

    def step(self):
        for link in self.links:
            link.step()

        for node in self.nodes:
            node.step()
