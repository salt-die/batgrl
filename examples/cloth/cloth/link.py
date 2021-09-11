from .node import Node


class Link:
    def __init__(self, a: Node, b: Node, *, stiffness=.3):
        self.a = a
        self.b = b
        self.stiffness = stiffness

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
        momentum = force_normal * length_dif * self.stiffness

        a.acceleration += momentum
        b.acceleration -= momentum
