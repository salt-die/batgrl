FRICTION = .99
GRAVITY = .01 + 0j


class Node:
    def __init__(self, position: complex, *, is_anchored=False):
        self.position = position
        self.velocity = self.acceleration = 0j
        self.is_anchored = is_anchored

    def step(self):
        if not self.is_anchored:
            self.velocity += self.acceleration
            self.position += self.velocity

            self.velocity *= FRICTION

        self.acceleration = GRAVITY
