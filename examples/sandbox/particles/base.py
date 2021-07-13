from abc import ABC, abstractmethod
import asyncio

from .._random import random_sign
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
        self.pos = position

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, new_pos):
        self._pos = new_pos
        self.world[new_pos] = self

    def wake(self):
        pass

    def sleep(self):
        pass

    def step(self):
        pass


class Movable(ABC):
    def __init__(self, world, position):
        self.world = world
        self.coords = complex(*position)
        self._update_task = asyncio.create_task(self.update())

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords = new_coords
        self.world[self.pos] = self

    @staticmethod
    def int_coords(coords):
        return round(coords.real), round(coords.imag)

    @property
    def pos(self):
        return self.int_coords(self.coords)


class MovableSolid(Movable, Solid):
    INERTIAL_RESISTANCE = .5

    def _move(self, old_yx, new_y, new_x):
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
        move = self._move
        pos = y, x = self.pos
        dx = random_sign()

        if not (
            move(pos, y + 1, x)
            or move(pos, y + 1, x + dx)
            or move(pos, y + 1, x - dx)
        ):
            self.sleep()


class Liquid(Movable, Element):
    def _move(self, old_yx, new_y, new_x):
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
        move = self._move
        pos = y, x = self.pos
        dx = random_sign()

        if not (
            move(pos, y + 1, x)
            or move(pos, y + 1, x + dx)
            or move(pos, y + 1, x - dx)
            or move(pos, y, x + dx)
            or move(pos, y, x - dx)
        ):
            self.sleep()
