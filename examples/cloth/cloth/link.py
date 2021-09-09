
from .node import Node


class Link:
    def __init__(self, a: Node, b: Node, *, stiffness=3.0):
        self.a = a
        self.b = b
        self.stiffness = stiffness

        self.initial_length = abs(a.position - b.position)

    def step(self):
        a = self.a
        b = self.b

        a_to_b = b.position - a.position
        distance = abs(a_to_b)
        offset = self.initial_length - distance

        momentum = offset * self.stiffness / (a.mass + b.mass) * a_to_b / distance

        a.position -= momentum / a.mass
        b.position += momentum / b.mass
