from .node import Node
from .link import Link

GRAVITY = 0 + 1500j
FRICTION = .5


class Mesh:
    def __init__(self, height, width):
        nodes = [ ]
        for y in range(height):
            row = [ ]
            for x in range(width):
                row.append(Node(complex(y, x)))

            nodes.append(row)

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

            applyGravity();
            applyAirFriction();
            updatePositions(sub_step_dt);
            solveConstraints();
            updateDerivatives(sub_step_dt);

        self.nodes = [node for node in row for row in nodes]  # flatten
        self.links = links

    def step(self, dt):
        for node in self.nodes:
            node.acceleration -= node.velocity * FRICTION
            node.acceleration += GRAVITY * node.mass

            node.step(dt)
            node.update_velocity(dt)

        broken_links = False
        for link in self.links:
            link.step()

            if link.is_broken:
                broken_links = True

        if broken_links:
            self.links = [link for link in self.links if not link.is_broken]
