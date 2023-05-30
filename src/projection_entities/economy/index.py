"""
Economic index, like `S&P 500 <https://g.co/finance/.INX:INDEXSP>`_,
`Big Mac <https://www.economist.com/big-mac-index>`_, or `Inverse Cramer <https://g.co/finance/SJIM:BATS>`_.
"""

from datetime import date

from src.system.projection_entity import ProjectionEntity
from src.system.projection.time_steps import TimeSteps
from src.system.projection_entity.projection_value import ProjectionValue

from src.data_sources.annuity import AnnuityDataSources
from src.data_sources.economic_scenarios.economic_scenario import EconomicScenario


class Index(
    ProjectionEntity
):

    """
    Economic index, like `S&P 500 <https://g.co/finance/.INX:INDEXSP>`_,
    `Big Mac <https://www.economist.com/big-mac-index>`_, or `Inverse Cramer <https://g.co/finance/SJIM:BATS>`_.
    """

    data_sources: AnnuityDataSources

    economic_scenario: EconomicScenario     #: The current economic scenario.
    index_name: str                         #: Index name.

    index_value: ProjectionValue            #: Index value.
    pct_change: ProjectionValue             #: Index percent change, from one period to the next.

    def __init__(
        self,
        time_steps: TimeSteps,
        data_sources: AnnuityDataSources,
        index_name: str
    ):

        """
        Constructor method.

        :param time_steps: Projection-wide timekeeping object.
        :param data_sources: Annuity data sources.
        :param index_name: Name of this index.
        """

        ProjectionEntity.__init__(
            self=self,
            time_steps=time_steps,
            data_sources=data_sources
        )

        self.economic_scenario = data_sources.economic_scenario
        self.index_name = index_name

        self.index_value = ProjectionValue(
            init_t=self.init_t,
            init_value=self.economic_scenario.get_rate(
                name=self.index_name,
                t=self.init_t
            )
        )

        self.pct_change = ProjectionValue(
            init_t=self.init_t,
            init_value=0.0
        )

    def __str__(
        self
    ) -> str:

        return f'economy.index.{self.index_name}'

    def calc_pct_change(
        self,
        t1: date,
        t2: date
    ) -> float:

        r"""
        Calculates the percentage growth in the index between two points in time:

        .. math::
            percent\, change = \frac{rate_{t1}}{rate_{t2}} - 1

        .. warning::
            This algorithm does not handle division-by-zero.

        :param t1: Start date.
        :param t2: End date.
        :return: Percent change.
        """

        curr_rate = self.economic_scenario.get_rate(
            name=self.index_name,
            t=t1
        )

        next_rate = self.economic_scenario.get_rate(
            name=self.index_name,
            t=t2
        )

        return (next_rate / curr_rate) - 1.0

    def age_index(
        self
    ) -> None:

        """
        Projects the index forward one time step by:

        #. Updating the index value.
        #. Calculating the percent change in the index from the previous time step to the current time step.

        :return: Nothing.
        """

        self.pct_change[self.time_steps.t] = self.calc_pct_change(
            t1=self.time_steps.prev_t,
            t2=self.time_steps.t
        )

        self.index_value[self.time_steps.t] = self.economic_scenario.get_rate(
            name=self.index_name,
            t=self.time_steps.t
        )
