from abc import ABC, abstractmethod
import asyncio
from enum import Enum
from itertools import cycle

import numpy as np

from nurses_2.colors import Color

random = np.random.default_rng().random


class State(Enum):
    """
    Element states.
    """
    GAS = "GAS"
    LIQUID = "LIQUID"
    SOLID = "SOLID"


class CycleColorBehavior:
    """
    Cycles through several colors for an element.

    Notes
    -----
    `COLORS` should be an infinite iterator.
    """
    COLORS = None  # itertools.cycle

    def step(self):
        self.COLOR = next(self.COLORS)
        super().step()


class ColorVariationBehavior:
    """
    Adds a small variation to the element color.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        random_delta = 10 * random(3) - 5  # Three random values between -5 and 5
        random_color = np.clip(
            random_delta + self.COLOR,
            0,
            255,
            dtype=np.uint8,
            casting="unsafe"
        )
        self.COLOR = Color(*random_color)


class Element(ABC):
    """
    Base for elements.
    """
    COLOR = None
    DENSITY = None
    STATE = None
    DEFAULT_REPLACEMENT = None

    LIFETIME = float("inf")  # Replace this element after LIFETIME updates.
    INACTIVE = 100  # Sleep if inactive INACTIVE times in a row.
    SLEEP = 0  # Seconds between updates.

    all_elements = { }

    def __init_subclass__(cls):
        if hasattr(cls, "COLORS"):
            cls.COLOR = next(cls.COLORS)

        if all(getattr(cls, attr) is not None for attr in ("COLOR", "DENSITY", "STATE")):
            cls.all_elements[cls.__name__] = cls

    def __init__(self, world, pos):
        self.world = world
        self.pos = pos

        self.world[pos] = self
        self._update_task = asyncio.create_task(self.update())
        self.inactivity = 0

    def sleep(self):
        """
        Stop updating.
        """
        self.inactivity = 0
        self._update_task.cancel()

    def sleep_if_inactive(self):
        """
        Sleep if inactivity is greater than or equal to INACTIVE else increment inactivity.
        """
        if self.inactivity >= self.INACTIVE:
            self.sleep()
        else:
            self.inactivity += 1

    def wake(self):
        """
        Resume updating.
        """
        if self._update_task.done():
            self._update_task = asyncio.create_task(self.update())

    def replace(self, element=None):
        """
        Stop updating and replace with element or DEFAULT_REPLACEMENT or Air.
        """
        self.sleep()
        self.wake_neighbors()
        (element or self.DEFAULT_REPLACEMENT or Air)(self.world, self.pos)

    async def update(self):
        """
        Coroutine that steps the element.
        """
        step = self.step

        while True:
            step()

            self.LIFETIME -= 1.0

            if self.LIFETIME <= 0.0:
                self.replace()

            try:
                await asyncio.sleep(self.SLEEP)
            except asyncio.CancelledError:
                return

    def neighbors(self):
        """
        Yield all neighbors.
        """
        world = self.world
        h, w = world.shape
        y, x = self.pos
        deltas = (
            (-1, -1),
            (-1,  0),
            (-1,  1),
            ( 0, -1),
            ( 0,  1),
            ( 1, -1),
            ( 1,  0),
            ( 1,  1),
        )

        for dy, dx in deltas:
            if 0 <= y + dy < h and 0 <= x + dx < w:
                yield world[y + dy, x + dx]

    def wake_neighbors(self):
        """
        Wake all neighbors.
        """
        for neighbor in self.neighbors():
            neighbor.wake()

    def update_neighbors(self):
        """
        Update all neighbors or until `update_neighbor` returns True.
        """
        for neighbor in self.neighbors():
            if self.update_neighbor(neighbor):
                return True

        return False

    @abstractmethod
    def update_neighbor(self, neighbor):
        """
        Update neighbor.

        Return True to stop updating.
        """

    @abstractmethod
    def step(self):
        """
        Single step of an element's update.
        """

class InertElement(Element):
    """
    Base for inert elements.
    """
    def update_neighbor(self, neighbor):
        """
        Do nothing.
        """

    def step(self):
        """
        Cancel updating.
        """
        self._update_task.cancel()


class MovingElement(Element):
    """
    Base for moving elements.
    """
    def _move(self, dy, dx):
        """
        Try to move vertically by dy and horizontally by dx.  Return True if successful.
        """
        world = self.world
        h, w = world.shape  # height, width
        y, x = self.pos
        new_y = y + dy
        new_x = x + dx

        if not (0 <= new_y < h and 0 <= new_x < w):
            # Fall off the world
            self.replace(Air)
            return True

        neighbor = world[new_y, new_x]
        neighbor_density = neighbor.DENSITY
        density = self.DENSITY

        if (
            neighbor.STATE == State.SOLID and self.STATE != State.LIQUID
            or density > 0 and density <= neighbor_density
            or density < 0 and density >= neighbor_density
        ):
            # Neighbor is too dense to move.
            return False

        # Swap position with neighbor
        self.wake_neighbors()
        neighbor.wake_neighbors()

        neighbor.pos = y, x
        world[y, x] = neighbor

        self.pos = new_y, new_x
        world[new_y, new_x] = self
        return True

    def update_neighbor(self, neighbor):
        """
        Default implementation.  Return False.
        """
        return False

    def step(self):
        if self.update_neighbors():
            return

        move = self._move
        dy = 1 if self.DENSITY > 0 else -1  # Air has a density of 0, so less than this and element will "fall" up.
        dx = 2 * round(random()) - 1  # -1 or 1 randomly

        if (
            move(dy, 0) or move(dy, dx) or move(dy, -dx)  # Try to move vertically...
            or self.STATE != State.SOLID and (move(0, dx) or move(0, -dx))  # Try to move horizontally...
        ) or self.LIFETIME != float("inf"):  # Elements with finite lifetime don't sleep.
            self.inactivity = 0  # Move was successful so inactivity is reset to 0.
        else:
            self.sleep_if_inactive()  # Move was not successful so increment inactivity or go to sleep.


################
# Particle Zoo #
################


class Air(InertElement):
    COLOR = Color(25, 25, 25)
    DENSITY = 0.0
    STATE = State.GAS


class Stone(ColorVariationBehavior, InertElement):
    COLOR = Color(120, 110, 120)
    DENSITY = 100.0
    STATE = State.SOLID


class Wood(ColorVariationBehavior, InertElement):
    COLOR = Color(81, 42, 6)
    DENSITY = 80.0
    STATE = State.SOLID


class Sand(ColorVariationBehavior, MovingElement):
    COLOR = Color(150, 100, 50)
    DENSITY = 50.0
    STATE = State.SOLID


class Water(ColorVariationBehavior, MovingElement):
    COLOR = Color(20, 100, 170)
    DENSITY = 1.0
    STATE = State.LIQUID


class Snow(ColorVariationBehavior, MovingElement):
    COLOR = Color(200, 200, 250)
    DENSITY = .9
    STATE = State.SOLID
    DEFAULT_REPLACEMENT = Water
    SLEEP = .1
    MELT_TIME = float("inf")

    def _move(self, dy, dx):
        if dx != 0:  # Not allowing snow to move directly down so it meanders more.
            return super()._move(dy, dx)

    def update_neighbor(self, neighbor):
        if self.MELT_TIME == float("inf") and isinstance(neighbor, Water):
            self.MELT_TIME = 30 * random()  # Give the snow some time to settle before it descends into the water.
            self.SLEEP *= 2
            return True

    def step(self):
        self.MELT_TIME -= 1

        if self.MELT_TIME <= 0 and self.DENSITY == .9:
            self.DENSITY = 1.1
            self.LIFETIME = 20 * random()

        super().step()


class Steam(CycleColorBehavior, MovingElement):
    LIFETIME = 1000
    COLORS = cycle((
        Color(148, 174, 204),
        Color(199, 204, 234),
        Color(219, 224, 255),
    ))
    DENSITY = -2.0
    STATE = State.GAS
    DEFAULT_REPLACEMENT = Water


class Oil(ColorVariationBehavior, MovingElement):
    COLOR = Color(56, 54, 33)
    DENSITY = .5
    STATE = State.LIQUID


class Smoke(CycleColorBehavior, MovingElement):
    LIFETIME = 850
    COLORS = cycle((
        Color(140, 140, 140),
        Color(120, 120, 120),
        Color(155, 155, 155),
    ))
    DENSITY = -1.0
    STATE = State.GAS


class Fire(CycleColorBehavior, MovingElement):
    LIFETIME = 1000
    COLORS = cycle((
        Color(186, 105, 29),
        Color(244, 146, 53),
        Color(229, 179, 52),
    ))
    DENSITY = .1
    STATE = State.SOLID

    def update_neighbor(self, neighbor):
        match neighbor:
            case Wood():
                if random() > .99:
                    neighbor.replace(Fire)

                # Return True to stop Fire from moving if
                # it is next to wood, i.e., it sticks to wood.
                return True
            case Air():
                if random() > .989:
                    neighbor.replace(Smoke)
            case Water():
                if random() > .95:
                    neighbor.replace(Steam)

                    self.replace()
                    return True

                elif random() > .95:
                    self.replace(Smoke)
                    return True
            case Snow():
                if random() > .945:
                    neighbor.replace(Water)
            case Oil():
                if random() > .92:
                    neighbor.replace(Fire)
                    # Fire from oil will have a short lifetime.
                    self.world[neighbor.pos].LIFETIME = 25
