from .node import Node


class Link:
    def __init__(self, a: Node, b: Node, *, stiffness=.3, damping=.05):
        self.a = a
        self.b = b
        self.stiffness = stiffness
        self.damping = damping

        self.rest_length = abs(a.position - b.position)

    def step(self):
        a = self.a
        b = self.b

        direction = b.position - a.position
        length = abs(direction)

        if length < self.rest_length:
            return

        force_normal = direction / length
        velocity_dif = b.velocity - a.velocity

        damping = (
            velocity_dif.real * force_normal.real
            + velocity_dif.imag * force_normal.imag
        ) * self.damping

        momentum = force_normal * ((length - self.rest_length) * self.stiffness + damping)

        a.acceleration += momentum
        b.acceleration -= momentum
