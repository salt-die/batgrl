"""A module for constant motion along a bezier curve."""

import asyncio
from bisect import bisect
from collections.abc import Callable
from dataclasses import dataclass
from itertools import accumulate
from math import comb
from time import perf_counter
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .basic import Point, clamp
from .easings import EASINGS, Easing

__all__ = ["BezierCurve", "Easing", "move_along_path"]


@dataclass
class BezierCurve:
    """
    A Bezier curve.

    Parameters
    ----------
    control_points : NDArray[np.float32]
        Array of control points of Bezier curve with shape `(N, 2)`.
    arc_length_approximation : int, default: 50
        Number of evaluations for arc length approximation.

    Attributes
    ----------
    arc_length : float
        Approximate length of Bezier curve.
    arc_length_approximation : int
        Number of evaluations for arc length approximation.
    arc_lengths : NDArray[np.float32]
        Approximate arc lengths along Bezier curve.
    coef : NDArray[np.float32]
        Binomial coefficients of Bezier curve.
    control_points : NDArray[np.float32]
        Array of control points of Bezier curve with shape `(N, 2)`.
    degree : int
        Degree of Bezier curve.

    Methods
    -------
    evaluate(t)
        Evaluate the Bezier curve at `t` (0 <= t <= 1).
    arc_length_proportion(p)
        Evaluate the Bezier curve at a proportion of its total arc length.
    """

    control_points: NDArray[np.float32]
    """Array of control points of Bezier curve with shape `(N, 2)`."""
    arc_length_approximation: int = 50
    """Number of evaluations for arc length approximation."""

    def __post_init__(self):
        if self.degree == -1:
            raise ValueError("There must be at least one control point.")

        self.coef: NDArray[np.float32] = np.array(
            [comb(self.degree, i) for i in range(self.degree + 1)], dtype=float
        )
        """Binomial coefficients of Bezier curve."""

        evaluated = self.evaluate(np.linspace(0, 1, self.arc_length_approximation))
        norms = np.linalg.norm(evaluated[1:] - evaluated[:-1], axis=-1)
        self.arc_lengths: NDArray[np.float32] = np.append(0, norms.cumsum())
        """Approximate arc lengths along Bezier curve."""

    @property
    def degree(self) -> int:
        """Degree of Bezier curve."""
        return len(self.control_points) - 1

    @property
    def arc_length(self) -> float:
        """Approximate length of Bezier curve."""
        return self.arc_lengths[-1]

    def evaluate(self, t: float | NDArray[np.float32]) -> NDArray[np.float32]:
        """Evaluate the Bezier curve at `t` (0 <= t <= 1)."""
        t = np.asarray(t)
        terms = np.logspace(0, self.degree, num=self.degree + 1, base=t).T
        terms *= np.logspace(self.degree, 0, num=self.degree + 1, base=1 - t).T
        terms *= self.coef
        return terms @ self.control_points

    def arc_length_proportion(self, p: float) -> NDArray[np.float32]:
        """Evaluate the Bezier curve at a proportion of its total arc length."""
        target_length = self.arc_length * p
        n = self.arc_length_approximation
        i = clamp(bisect(self.arc_lengths, target_length) - 1, 0, n - 1)

        previous_length = self.arc_lengths[i]
        if previous_length == target_length:
            return self.evaluate(i / n)

        target_dif = target_length - previous_length
        if i < n - 1:
            arc_dif = self.arc_lengths[i + 1] - previous_length
        else:
            arc_dif = previous_length - self.arc_lengths[i - 1]

        t = (i + target_dif / arc_dif) / n
        return self.evaluate(t)


class HasPos(Protocol):
    """An object with a position."""

    pos: Point


async def move_along_path(
    has_pos: HasPos,
    path: list[BezierCurve],
    *,
    speed: float = 1.0,
    easing: Easing = "linear",
    on_start: Callable[[], None] | None = None,
    on_progress: Callable[[float], None] | None = None,
    on_complete: Callable[[], None] | None = None,
):
    """
    Move `has_pos` along a path of Bezier curves at some speed (in cells per second).

    Parameters
    ----------
    has_pos : HasPos
        Object to be moved along path.
    path : list[BezierCurve]
        A path made up of Bezier curves.
    speed : float, default: 1.0
        Speed of movement in approximately cells per second.
    on_start : Callable[[], None] | None, default: None
        Called when motion starts.
    on_progress : Callable[[float], None] | None, default: None
        Called as motion updates with current progress.
    on_complete : Callable[[], None] | None, default: None
        Called when motion completes.
    """
    cumulative_arc_lengths = [
        *accumulate((curve.arc_length for curve in path), initial=0)
    ]
    total_arc_length = cumulative_arc_lengths[-1]
    easing_function = EASINGS[easing]
    has_pos.pos = path[0].evaluate(0.0)
    last_time = perf_counter()
    distance_traveled = 0.0

    if on_start is not None:
        on_start()

    while True:
        await asyncio.sleep(0)

        current_time = perf_counter()
        elapsed = current_time - last_time
        last_time = current_time
        distance_traveled += speed * elapsed
        if distance_traveled >= total_arc_length:
            has_pos.pos = path[-1].evaluate(1.0)
            break

        p = easing_function(distance_traveled / total_arc_length)
        eased_distance = p * total_arc_length

        i = clamp(bisect(cumulative_arc_lengths, eased_distance) - 1, 0, len(path) - 1)
        distance_on_curve = eased_distance - cumulative_arc_lengths[i]
        curve_p = distance_on_curve / path[i].arc_length
        has_pos.pos = path[i].arc_length_proportion(curve_p)

        if on_progress is not None:
            on_progress(p)

    if on_complete is not None:
        on_complete()
