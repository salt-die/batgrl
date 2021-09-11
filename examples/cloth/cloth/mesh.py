from .node import Node
from .link import Link


class Mesh:
    def __init__(self, size):
        height, width = size

        nodes = [
            [Node(position=complex(y, x)) for x in range(width)]
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

        # nodes[0][0].is_anchored = nodes[0][-1].is_anchored = True
        # nodes[0][width // 3].is_anchored = nodes[0][2 * width // 3].is_anchored = True

        for node in nodes[0]:
            node.is_anchored = True

        self.nodes = [node for row in nodes for node in row]  # flatten
        self.links = links

    def step(self):
        for link in self.links:
            link.step()

        for node in self.nodes:
            node.step()
