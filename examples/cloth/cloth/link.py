
from .node import Node


class Link:
    def __init__(self, a: Node, b: Node, *, max_length_ratio=1.5, stiffness=1.0):
        self.a = a
        self.b = b
        self.max_length_ratio = max_length_ratio
        self.stiffness = stiffness

        self.initial_length = abs(a.position - b.position)
        self.is_broken = False

    def step(self):
        if self.is_broken:
            return

        a = self.a
        b = self.b

        a_to_b = a.position - b.position
        current_length = abs(a_to_b)

        if current_length > self.initial_length:
            self.is_broken = current_length > self.max_length_ratio

            normal = a_to_b / current_length
            length_difference = self.initial_length - current_length
            momentum = -(length_difference * self.stiffness) / (a.mass + b.mass) * normal
            a.position -= momentum / a.mass
            b.position += momentum / b.mass
