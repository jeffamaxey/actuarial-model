"""
Projection time synchronization.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from typing import (
    List,
    Self
)


class TimeSteps:

    """
    Time-keeping class, used to synchronize time across model objects in a :class:`~src.system.projection.Projection`.
    """

    _index: int
    _time_step: relativedelta
    _time_steps: List[date]

    def __init__(
        self,
        start_t: date,
        end_t: date,
        time_step: relativedelta
    ):

        """
        Constructor method. Creates a list of time steps a :class:`~src.system.projection.Projection` would iterate
        over.

        :param start_t: Starting time step.
        :param end_t: Ending time step.
        :param time_step: Interval between time steps.
        """

        self._index = 0
        self._time_step = time_step
        self._time_steps = []

        time_step = start_t

        while time_step <= end_t:

            self._time_steps.append(
                time_step
            )

            time_step += self._time_step

    def __iter__(
        self
    ) -> Self:

        self._index = -1
        return self

    def __next__(
        self
    ) -> date:

        if self._index >= len(self._time_steps) - 1:
            raise StopIteration
        self._index += 1
        return self.t

    @property
    def min_t(
        self
    ) -> date:

        """
        First, or earliest time step.

        :return: First time step.
        """

        return min(
            self._time_steps
        )

    @property
    def max_t(
        self
    ) -> date:

        """
        Last, or latest time step.

        :return: Last time step.
        """

        return max(
            self._time_steps
        )

    @property
    def prev_t(
        self
    ) -> date:

        """
        Previous time step during a :class:`~src.system.projection.Projection`.

        :return: Previous time step.
        """

        return self._time_steps[
            max(
                self._index - 1,
                0
            )
        ]

    @property
    def t(
        self
    ) -> date:

        """
        Current time step during a :class:`~src.system.projection.Projection`.

        :return: Current time step.
        """

        return self._time_steps[
            self._index
        ]

    @property
    def next_t(
        self
    ) -> date:

        """
        Next time step during a :class:`~src.system.projection.Projection`.

        :return: Next time step.
        """

        return self._time_steps[
            min(
                self._index,
                len(self._time_steps) - 1
            )
        ]

    @property
    def time_step(
        self
    ) -> relativedelta:

        """
        Interval of time between time steps.

        :return: Time step interval.
        """

        return self._time_step
