import asyncio
from random import random

from nurses_2.colors import Color

from .line import line


class Element:
    COLOR = None
    DENSITY = 0.0

    all_elements = { }

    def __init_subclass__(cls):
        if cls.COLOR:
            cls.all_elements[cls.__name__] = cls


class StationaryElement(Element):
    """
    Base for stationary elements.
    """
    def __init__(self, world, position):
        self.world = world
        self.pos = position

        self.world[position] = self
        self._update_task = asyncio.create_task(self.update())

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
                world[y, x].wake()

    def sleep(self):
        self._update_task.cancel()

    def step(self):
        self._update_task.cancel()


class MovingElement(StationaryElement):
    """
    Base for moving elements.
    """
    def _move(self, dy, dx):
        world = self.world
        h, w = world.shape
        y, x = self.pos
        new_y = y + dy
        new_x = x + dx

        if 0 <= new_y < h and 0 <= new_x < w:
            neighbor = world[new_y, new_x]

            if (
                neighbor.DENSITY < 10.0
                and (
                    dy > 0
                    and (
                        self.DENSITY > neighbor.DENSITY  # Sink
                        or 0 <= y - 1 and world[y - 1, x].DENSITY >= self.DENSITY  # Pushed down
                    )
                    or dy < 0 and self.DENSITY < neighbor.DENSITY  # Float
                    or dy == 0 and self.DENSITY < 10.0
                )
            ):
                self.wake_neighbors()

                neighbor.pos = y, x
                world[y, x] = neighbor

                self.pos = new_y, new_x
                world[new_y, new_x] = self
                return True

            return False

        # Fall off the world
        world[y, x] = Air(world, (y, x))
        self._update_task.cancel()
        return True

    def step(self):
        move = self._move
        dx = 2 * round(random()) - 1
        dy = 1 if self.DENSITY > 0 else -1

        if not (
            move(dy, 0)
            or move(dy, dx)
            or move(dy, -dx)
            or move(0, dx)
            or move(0, -dx)
        ):
            self.sleep()


class Air(StationaryElement):
    DENSITY = 0.0
    COLOR = Color(25, 25, 25)


class Stone(StationaryElement):
    DENSITY = 100.0
    COLOR = Color(120, 110, 120)


class Sand(MovingElement):
    DENSITY = 50.0
    COLOR = Color(150, 100, 50)


class Water(MovingElement):
    DENSITY = 1.0
    COLOR = Color(20, 100, 170)


class Snow(MovingElement):
    DENSITY = .8
    COLOR = Color(200, 200, 250)


class Steam(MovingElement):
    DENSITY = -1.0
    COLOR = Color(50, 50, 50)
