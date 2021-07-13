from abc import ABC, abstractmethod
import asyncio
from random import random

from .line import line


class Element(ABC):
    COLOR = None  # COLOR is also a flag that a child class is abstract or implemented.

    all_elements = { }

    def __init_subclass__(cls):
        if cls.COLOR:
            cls.all_elements[cls.__name__] = cls

    def __init__(self, world, position):
        self.world = world
        self.pos = position
        self._update_task = asyncio.create_task(self.update())

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, new_pos):
        self._pos = new_pos
        self.world[new_pos] = self

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

    def sleep(self):
        self._update_task.cancel()

    @abstractmethod
    def step(self):
        """
        A single update of the element.
        """


class Solid(Element):
    """
    A solid element.
    """
    def wake(self):
        pass

    def sleep(self):
        pass

    def step(self):
        self._update_task.cancel()


class Movable(ABC):
    """
    Base for a movable element.
    """

    @abstractmethod
    def _move(self, old_yx, new_y, new_x):
        """
        Try to move from old_yx to (new_y, new_x).
        Return True if successful else False.
        """


class MovableSolid(Movable, Solid):
    """
    Movable solid base.
    """

    def _move(self, old_yx, new_y, new_x):
        world = self.world
        h, w = world.shape

        if new_y < h and 0 <= new_x < w:
            target = world[new_y, new_x]

            if isinstance(target, Liquid):
                target.pos = old_yx
            elif target is None:
                world[old_yx] = None
            else:
                return False

            self.wake_neighbors()
            self.pos = new_y, new_x
            return True

        # Fall off the world
        world[old_yx] = None
        self._update_task.cancel()
        return True

    def step(self):
        move = self._move
        pos = y, x = self.pos
        dx = 2 * round(random()) - 1

        if not (
            move(pos, y + 1, x)
            or move(pos, y + 1, x + dx)
            or move(pos, y + 1, x - dx)
        ):
            self.sleep()


class Liquid(Movable, Element):
    """
    Liquid base.
    """
    def _move(self, old_yx, new_y, new_x):
        world = self.world
        h, w = world.shape

        if new_y < h and 0 <= new_x < w:
            if world[new_y, new_x] is None:
                world[old_yx] = None

                self.wake_neighbors()
                self.pos = new_y, new_x
                return True

            return False

        # Fall off the world
        world[old_yx] = None
        self._update_task.cancel()
        return True

    def step(self):
        move = self._move
        pos = y, x = self.pos
        dx = 2 * round(random()) - 1

        if not (
            move(pos, y + 1, x)
            or move(pos, y + 1, x + dx)
            or move(pos, y + 1, x - dx)
            or move(pos, y, x + dx)
            or move(pos, y, x - dx)
        ):
            self.sleep()
