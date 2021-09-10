from .node import Node


class Link:
    def __init__(self, a: Node, b: Node, *, stiffness=8.0):
        self.a = a
        self.b = b
        self.stiffness = stiffness
        self.initial_length = abs(a.position - b.position)

    def step(self):
        a = self.a
        b = self.b

        momentum = (b.position - a.position) * self.stiffness
        a.acceleration += momentum
        b.acceleration -= momentum
