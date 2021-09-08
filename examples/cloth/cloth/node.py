class Node:
    def __init__(self, position: complex, *, mass=1.0, is_anchored=False):
        self._position = self._previous_position = position
        self.velocity = self.acceleration = 0j
        self.mass = mass
        self.is_anchored = is_anchored

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if not self.is_anchored:
            self._previous_position = self._position
            self._position = value

    def step(self, dt):
        if not self.is_anchored:
            self.velocity += self.acceleration / self.mass * dt
            self.position += self.velocity * dt

    def update_velocity(self, dt):
        self.velocity = (self.position - self._previous_position) / dt
        self.acceleration = 0j
