from abc import ABC, abstractmethod
import asyncio

from nurses_2.colors import WHITE

from .line import line


class Particle(ABC):
    COLOR = WHITE

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
    async def update(self):
        """
        Coroutine that updates particle.
        """


class MovingParticle(Particle):
    FRICTION = .8
    GRAVITY = 1 + 0j
    MIN_SPEED = .1

    MASS = 1

    def __init__(self, world, position):
        self.world = world
        self.coords = complex(position)
        self.velocity = 0j
        self._update_task = asyncio.create_task(self.update())

    @property
    def pos(self):
        pos = self.coords
        return round(pos.real), round(pos.imag)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, new_velocity):
        self._velocity = new_velocity

        if self._update_task.done():
            self._update_task = asyncio.create_task(self.update())

    def step(self):
        """
        Update position due to velocity or collide with another particle.
        """
        world = self.world
        coords = self.coords
        last_yx = round(coords.real), round(coords.imag)

        self.velocity = velocity = (self.velocity + self.GRAVITY) * self.FRICTION
        new_coords = coords + velocity

        # Check if path to new position is clear.
        # If not, collide with the first thing that gets in the way.

        new_y, new_x = round(new_coords.real), round(new_coords.imag)
        h, w = world.shape
        is_inbounds = 0 <= npy < h and 0 <= npx < w
        if not is_inbounds:
            new_y = 0 if new_y < 0 else h - 1 if new_y >= h else new_y
            new_x = 0 if new_x < 0 else w - 1 if new_x >= w else new_x

        world[last_yx] = None

        for yx in line(*last_yx, npy, npx):
            if world[yx] is not None:
                world[last_yx] = self
                self.coords = complex(last_yx)
                return self.collide(world[yx])

            last_yx = yx

        if is_inbounds:
            world[last_yx] = self
            self.coords = complex(last_yx)
        else:
            # Particle has fallen off the edge of the world.
            # Cancel its updates and let it be garbage-collected.
            self._update_task.cancel()

    async def update(self):
        step = self.step
        last_pos = self.pos
        MIN_SPEED = self.MIN_SPEED

        while True:
            step()

            if self.pos == last_pos and abs(self.velocity) < MIN_SPEED:
                return

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    @abstractmethod
    def collide(self, other):
        """
        Collide with other.
        """


class SolidParticle(MovingParticle):
    """
    A solid particle.
    """


class LiquidParticle(MovingParticle):
    """
    A liquid particle.
    """