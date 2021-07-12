from abc import ABC, abstractmethod
import asyncio
import random

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
    INERTIAL_RESISTANCE = 0
    FRICTION = .8
    GRAVITY = 1 + 0j
    MASS = 1

    def __init__(self, world, position):
        self.world = world
        self.coords = complex(*position)
        self.velocity = 0j
        self._update_task = asyncio.create_task(self.update())

    @property
    def pos(self):
        pos = self.coords
        return round(pos.real), round(pos.imag)

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

    def step(self):
        move = self.move
        pos = y, x = self.pos
        xs = x, x - 1, x + 1

        if not any(move(pos, y + 1, x) for x in xs):
            self.sleep()


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

    def step(self):
        move = self.move
        pos = y, x = self.pos
        xs = x, x - 1, x + 1

        if not any(move(pos, y + 1, x) for x in xs):
            # Randomly go left or right
            if round(random.random()):
                moved = move(pos, y, x - 1) or move(pos, y, x + 1)
            else:
                moved = move(pos, y, x + 1) or move(pos, y, x - 1)

            if not moved:
                self.sleep()
