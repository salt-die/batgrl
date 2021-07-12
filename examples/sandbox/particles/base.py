from abc import ABC, abstractmethod
import asyncio
from random import random

from .line import line


class Element(ABC):
    COLOR = None

    @abstractmethod
    def __init__(self, world, position):
        pass

    @property
    @abstractmethod
    def pos(self):
        """
        Position of particle.
        """

    @abstractmethod
    def step(self):
        """
        A single update of the element.
        """

    async def update(self):
        step = self.step

        while True:
            step()

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def wake(self):
        if self._update_task.done():
            self._update_task = asyncio.create_task(self.update())

    def sleep(self):
        self._update_task.cancel()

    def wake_neighbors(self):
        world = self.world
        h, w = world.shape
        y, x = self.pos
        coords = (
            (y - 1, x - 1),
            (y - 1, x),
            (y - 1, x + 1),
            (y, x - 1),
            (y, x + 1),
            (y + 1, x - 1),
            (y + 1, x),
            (y + 1, x + 1),
        )

        for y, x in coords:
            if 0 <= y < h and 0 <= x < w:
                if target := world[y, x]:
                    target.wake()


class Solid(Element):
    def __init__(self, world, position):
        self.world = world
        self._pos = position

    @property
    def pos(self):
        return self._pos

    def step(self):
        pass

    def wake(self):
        pass

    def sleep(self):
        pass


class Movable(ABC):
    FRICTION = .8
    GRAVITY = 1 + 0j

    INERTIAL_RESISTANCE = 0
    MASS = 1

    def __init__(self, world, position):
        self.world = world
        self.coords = complex(*position)
        self._velocity = 10 * random() + 10 * random() * 1j
        self._update_task = asyncio.create_task(self.update())

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        self._velocity = value
        self.wake()

    @property
    def pos(self):
        pos = self.coords
        return round(pos.real), round(pos.imag)

    def fall(self):
        self.velocity += self.GRAVITY
        self.velocity *= self.FRICTION

        previous_yx = self.pos
        new_coords = self.coords + self.velocity
        target_yx = new_y, new_x = round(new_coords.real), round(new_coords.imag)

        world = self.world
        h, w = world.shape

        if new_y < 0:
            new_y = 0
        elif new_y >= h:
            new_y = h - 1

        if new_x < 0:
            new_x = 0
        elif new_x >= w:
            new_x = w - 1

        world[previous_yx] = None
        for yx in line(*previous_yx, new_y, new_x):
            if particle := world[yx]:
                world[previous_yx] = self
                self.coords = complex(*previous_yx)
                return self.collide(particle)

            previous_yx = yx

        if previous_yx == target_yx:
            world[target_yx] = self
            self.coords = new_coords

    def inelastic_collision(self, other):
        """
        Notes
        -----
        Coordinates of the two colliding particles are swapped before their velocities are averaged.
        """

    def elastic_collision(self, other):
        self_mass = self.MASS
        other_mass = other.MASS

        relative_coords = self.coords - other.coords
        relative_velocity = self.velocity - other.velocity

        distance = relative_coords.real**2 + relative_coords.imag**2  # Technically, distance squared

        theta = relative_velocity * relative_coords.conjugate()
        force = 2 * theta * relative_coords / (distance * (self_mass + other_mass))

        self.velocity -= other_mass * force
        other.velocity += self_mass * force

    def step(self):
        move = self.move
        pos = y, x = self.pos

        if self.velocity:
            self.fall()
        elif move(pos, y + 1, x):
            self.velocity += self.GRAVITY
        else:
            move(pos, y + 1, x + 2 * round(random()) - 1)

    @abstractmethod
    def move(self, old_yx, new_y, new_x):
        """
        Particle specific non-kinematic movement.
        """
        # Highly likely this method will be removed entirely.

    @abstractmethod
    def collide(self, other):
        """
        Particle collision. Elastic or in-elastic depending on
        particle types.
        """


class MovableSolid(Movable, Solid):
    def move(self, old_yx, new_y, new_x):
        world = self.world
        h, w = world.shape

        if new_y < h and 0 <= new_x < w:
            target = world[new_y, new_x]

            if isinstance(target, Liquid):
                target.coords = complex(*old_yx)
            elif target is None:
                pass
            else:
                return False

            self.wake_neighbors()
            world[old_yx], world[new_y, new_x] = world[new_y, new_x], world[old_yx]
            self.coords = complex(new_y, new_x)
            return True

        # Fall off the world
        world[old_yx] = None
        self._update_task.cancel()
        return True

    def collide(self, other):
        if not isinstance(other, Movable):
            self.velocity = 0j
        elif isinstance(other, Solid):
            self.elastic_collision(other)
        elif isinstance(other, Liquid):
            self.inelastic_collision(other)


class Liquid(Movable, Element):
    def move(self, old_yx, new_y, new_x):
        world = self.world
        h, w = world.shape

        if new_y < h and 0 <= new_x < w:
            target = world[new_y, new_x]
            if target is None:
                self.wake_neighbors()
                world[old_yx] = None
                world[new_y, new_x] = self
                self.coords = complex(new_y, new_x)
                return True

            return False

        # Fall off the world
        world[old_yx] = None
        self._update_task.cancel()
        return True

    def collide(self, other):
        if not isinstance(other, Movable):
            self.velocity = 0j
        else:
            self.inelastic_collision(other)
