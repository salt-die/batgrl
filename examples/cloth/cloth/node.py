class Node:
    def __init__(self, position, *, is_moving=True):
        self.position = self._previous_position = position
        self.velocity = self.acceleration = 0j
        self.is_moving = is_moving

    def step(self):
        self._previous_position = self.position
        self.velocity += self.acceleration
        self.position += self.velocity

    def update_velocity(self):
        self.velocity = self.position - self._previous_position
        self.acceleration = 0j

    def move(self):
        if self.is_moving:
            self.position += self.velocity
