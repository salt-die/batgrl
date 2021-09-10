FRICTION = .95
MASS = 25

class Node:
    def __init__(self, position: complex, *, is_anchored=False):
        self._initial_position = position
        self.position = self.velocity = self.acceleration = 0j
        self.is_anchored = is_anchored

    @property
    def coords(self):
        return self._initial_position + self.position

    def step(self):
        if self.is_anchored:
            self.velocity = 0j
        else:
            self.acceleration -= self.velocity * FRICTION
            self.velocity += self.acceleration / MASS
            self.position += self.velocity

        self.acceleration = 0j
