from .node import Node


class Link:
    def __init__(self, a: Node, b: Node):
        self.a = a
        self.b = b

        self.rest_length = abs(a.position - b.position)

    def step(self):
        a = self.a
        b = self.b

        direction = b.position - a.position
        length = abs(direction)
        self.stretch = stretch = (length - self.rest_length) / length

        if stretch > 0:
            # Typical calculation is `direction * stretch / (a.mass + b.mass)`,
            # but nodes have implicit mass of 1.
            momentum = direction * stretch * .5

            a.acceleration += momentum
            b.acceleration -= momentum
