"""
Index strategy account.
"""

from src.projection_entities.products.annuity.base_contract.account import Account

from src.system.projection.time_steps import TimeSteps
from src.system.projection_entity.projection_value import ProjectionValue
from src.system.projection.scripts.get_xversaries import get_xversaries

from src.data_sources.annuity import AnnuityDataSources
from src.data_sources.annuity.model_points.model_point.accounts.account import Account as AccountDataSource


class IndexedAccount(
    Account
):

    """
    Index strategy account.
    """

    crediting_term_months: int              #: Crediting :meth:`term <src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.term>` duration in months.
    term_start_date: ProjectionValue        #: Crediting term start date.

    def __init__(
        self,
        time_steps: TimeSteps,
        data_sources: AnnuityDataSources,
        account_data_source: AccountDataSource
    ):

        Account.__init__(
            self=self,
            time_steps=time_steps,
            data_sources=data_sources,
            account_data_source=account_data_source
        )

        self.crediting_term_months = self.data_sources.product.base_product.crediting_rate.indexed.term(
            account_name=self.account_data_source.account_name
        ) * 12

        if crediting_terms := get_xversaries(
            issue_date=self.data_sources.model_point.issue_date,
            start_date=self.init_t,
            end_date=self.time_steps.t,
            frequency=self.crediting_term_months,
        ):
            term_start_date = max(crediting_terms)

        else:
            term_start_date = self.data_sources.model_point.issue_date

        self.term_start_date = ProjectionValue(
            init_t=self.init_t,
            init_value=term_start_date
        )

    def credit_interest(
        self
    ) -> None:

        r"""
        Credits interest to the sub\-account, using this formula:

        .. math::
            index \, growth = \frac{index_{t}}{index_{t-1}} - 1

            interest \, credited = account \, value \times \biggl( max(par \times (min(index \, growth, cap) - spread), floor)  \biggr)

        Where:

        - :math:`index_{t}` is the
          :meth:`index <src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.index>`
          at time :math:`t`.

        - :math:`cap` is read in from
          :meth:`~src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.cap`.

        - :math:`spread` is read in from
          :meth:`~src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.spread`.

        - :math:`par` is read in from
          :meth:`~src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.participation_rate`.

        - :math:`floor` is read in from
          :meth:`~src.data_sources.annuity.product.base.crediting_rate.indexed.IndexedCreditingRate.floor`.

        :return: Nothing.
        """

        self.interest_credited[self.time_steps.t] = 0.0

        term_end_dates = get_xversaries(
            issue_date=self.data_sources.model_point.issue_date,
            start_date=self.time_steps.prev_t,
            end_date=self.time_steps.t,
            frequency=self.crediting_term_months
        )

        for term_end_date in term_end_dates:

            # Get growth rate
            start_index = self.data_sources.economic_scenario.get_rate(
                name=self.data_sources.product.base_product.crediting_rate.indexed.index(
                    account_name=self.account_data_source.account_name
                ),
                t=self.term_start_date
            )

            end_index = self.data_sources.economic_scenario.get_rate(
                name=self.data_sources.product.base_product.crediting_rate.indexed.index(
                    account_name=self.account_data_source.account_name
                ),
                t=term_end_date
            )

            crediting_rate = (end_index / start_index) - 1.0

            # Apply cap
            cap = self.data_sources.product.base_product.crediting_rate.indexed.cap(
                account_name=self.account_data_source.account_name
            )

            if cap is not None:

                crediting_rate = min(
                    cap,
                    crediting_rate
                )

            # Apply spread
            spread = self.data_sources.product.base_product.crediting_rate.indexed.spread(
                account_name=self.account_data_source.account_name
            )

            if spread is not None:

                crediting_rate -= spread

            # Apply participation rate
            participation_rate = self.data_sources.product.base_product.crediting_rate.indexed.participation_rate(
                account_name=self.account_data_source.account_name
            )

            if participation_rate is not None:

                crediting_rate *= participation_rate

            # Apply floor
            floor = self.data_sources.product.base_product.crediting_rate.indexed.floor(
                account_name=self.account_data_source.account_name
            )

            if floor is not None:

                crediting_rate = max(
                    floor,
                    crediting_rate
                )

            self.interest_credited[self.time_steps.t] = self.account_value * crediting_rate

            self.account_value[self.time_steps.t] = self.account_value + self.interest_credited

            self.term_start_date[self.time_steps.t] = term_end_date
