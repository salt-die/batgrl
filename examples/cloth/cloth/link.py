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
        length_dif = length - self.rest_length

        if length_dif < 0:
            return

        force_normal = direction / length

        # Typical calculation is `force_normal * length_dif / (a.mass + b.mass)`, but we've implicitly given
        # all nodes a mass of 1.
        momentum = force_normal * length_dif * .5

        a.acceleration += momentum
        b.acceleration -= momentum
