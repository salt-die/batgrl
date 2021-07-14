import asyncio
from enum import Enum
from itertools import cycle
from random import random

from nurses_2.colors import Color


class State(Enum):
    GAS = "GAS"
    LIQUID = "LIQUID"
    SOLID = "SOLID"


class Element:
    COLOR = None
    DENSITY = None
    STATE = None
    LIFETIME = float('inf')

    all_elements = { }

    def __init_subclass__(cls):
        if all(getattr(cls, attr) is not None for attr in ("COLOR", "DENSITY", "STATE")):
            cls.all_elements[cls.__name__] = cls

    def __init__(self, world, pos):
        self.world = world
        self.pos = pos

        self.world[pos] = self
        self._update_task = asyncio.create_task(self.update())

    async def update(self):
        step = self.step

        while True:
            step()

            self.LIFETIME -= 1.0

            if self.LIFETIME <= 0.0:
                self.sleep()

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def wake(self):
        self._update_task.cancel()
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
        if self.LIFETIME != float('inf'):
            self.LIFETIME -= 1.0

            if self.LIFETIME > 0.0:
                return

            Air(self.world, self.pos)


        self._update_task.cancel()


class StationaryElement(Element):
    """
    Base for stationary elements.
    """
    def step(self):
        self._update_task.cancel()


class MovingElement(Element):
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
            neighbor_density = neighbor.DENSITY
            neighbor_state = neighbor.STATE

            density = self.DENSITY
            state = self.STATE

            if neighbor_state == State.SOLID and state != State.LIQUID:
                return False

            if density < 0 and neighbor_density <= density:
                return False

            if density > 0 and neighbor_density >= density:
                return False

            self.wake_neighbors()

            neighbor.pos = y, x
            world[y, x] = neighbor

            self.pos = new_y, new_x
            world[new_y, new_x] = self
            return True

        # Fall off the world
        world[y, x] = Air(world, (y, x))
        self._update_task.cancel()
        return True

    def step(self):
        move = self._move
        dy = 1 if self.DENSITY > 0 else -1
        dx = 2 * round(random()) - 1

        if not (
            move(dy, 0)
            or move(dy, dx)
            or move(dy, -dx)
            or self.STATE != State.SOLID and (
                move(0, dx)
                or move(0, -dx)
            )
        ):
            self.sleep()


class AnimatedBehavior:
    COLORS = None  # itertools.cycle

    def step(self):
        self.COLOR = next(self.COLORS)
        super().step()


################
# Particle Zoo #
################

class Air(StationaryElement):
    COLOR = Color(25, 25, 25)
    DENSITY = 0.0
    STATE = State.GAS


class Stone(StationaryElement):
    COLOR = Color(120, 110, 120)
    DENSITY = 100.0
    STATE = State.SOLID


class Wood(StationaryElement):
    COLOR = Color(81, 42, 6)
    DENSITY = 80.0
    STATE = State.SOLID


class Sand(MovingElement):
    COLOR = Color(150, 100, 50)
    DENSITY = 50.0
    STATE = State.SOLID


class Water(MovingElement):
    COLOR = Color(20, 100, 170)
    DENSITY = 1.0
    STATE = State.LIQUID


class Snow(MovingElement):
    COLOR = Color(200, 200, 250)
    DENSITY = .8
    STATE = State.SOLID

    def step(self):
        if random() > .99:
            self.STATE = State.SOLID if self.STATE == State.LIQUID else State.LIQUID

        if self.STATE == State.LIQUID and random() > .99:
            self.sleep()
            water = Water(self.world, self.pos)
            water.wake_neighbors()
        else:
            super().step()


class Steam(MovingElement):
    COLOR = Color(148, 174, 204)
    DENSITY = -2.0
    STATE = State.GAS

    def sleep(self):
        super().sleep()
        Water(self.world, self.pos)


class Oil(MovingElement):
    COLOR = Color(56, 54, 33)
    DENSITY = .5
    STATE = State.LIQUID


class Smoke(MovingElement):
    LIFETIME = 850
    COLOR = Color(140, 140, 140)
    DENSITY = -1.0
    STATE = State.GAS


class Fire(AnimatedBehavior, MovingElement):
    LIFETIME = 1000
    COLORS = cycle((
        Color(186, 105, 29),
        Color(244, 146, 53),
        Color(229, 179, 52),
    ))
    COLOR = next(COLORS)
    DENSITY = .1
    STATE = State.SOLID

    def _move(self, dy, dx):
        world = self.world
        h, w = world.shape

        y, x = self.pos

        new_y = y + dy
        new_x = x + dx

        if 0 <= new_y < h and 0 <= new_x < w:
            neighbor = world[new_y, new_x]

            if isinstance(neighbor, Oil):
                if random() > .75:
                    neighbor.sleep()
                    Fire(world, (new_y, new_x))

                return True

            elif isinstance(neighbor, Water):
                if random() > .95:
                    neighbor.sleep()
                    Steam(world, (new_y, new_x))

                    self.LIFETIME = 0
                    self.sleep()
                    Air(world, (y, x))

                    return True

            elif isinstance(neighbor, Snow):
                if random() > .75:
                    neighbor.sleep()
                    Water(world, (new_y, new_x))

                    self.LIFETIME = 0
                    self.sleep()
                    Air(world, (y, x))

                    return True

            elif isinstance(neighbor, Wood):
                if random() > .98:
                    Fire(world, (new_y, new_x))

                    return True

            elif isinstance(neighbor, Air):
                if random() > .9:
                    Smoke(world, (new_y, new_x))

            density = self.DENSITY

            if neighbor.STATE == State.SOLID or density > 0 and neighbor.DENSITY >= density:
                return False

            self.wake_neighbors()

            neighbor.pos = y, x
            world[y, x] = neighbor

            self.pos = new_y, new_x
            world[new_y, new_x] = self
            return True

        # Fall off the world
        world[y, x] = Air(world, (y, x))
        self._update_task.cancel()
        return True
