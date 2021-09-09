

class Node:
    def __init__(self, position: complex, *, mass=1.0, friction=.8, is_anchored=False):
        self.position = position
        self.velocity = self.acceleration = 0j
        self.mass = mass
        self.friction = friction
        self.is_anchored = is_anchored

    def step(self):
        if not self.is_anchored:
            self.velocity += (self.acceleration - self.velocity * self.friction) / self.mass
            self.position += self.velocity
            self.acceleration = 0j
