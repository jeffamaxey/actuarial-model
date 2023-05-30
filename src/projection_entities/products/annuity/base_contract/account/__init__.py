r"""
Sub\-accounts within a policy.
"""

from abc import (
    ABC,
    abstractmethod
)
from typing import List
from datetime import date

from src.system.projection_entity import ProjectionEntity
from src.system.projection.time_steps import TimeSteps
from src.system.projection_entity.projection_value import (
    ProjectionValue,
    compare_latest_value
)

from src.data_sources.annuity import AnnuityDataSources
from src.data_sources.annuity.model_points.model_point.accounts.account import Account as AccountDataSource
from src.projection_entities.products.annuity.base_contract.account.premium import Premium


class Account(
    ProjectionEntity,
    ABC
):

    r"""
    Abstract base class for a sub\-account within a policy.
    """

    data_sources: AnnuityDataSources
    account_data_source: AccountDataSource

    premiums: List[Premium]                 #: List of premium payments.

    premium_new: ProjectionValue            #: New premiums received.
    premium_cumulative: ProjectionValue     #: Cumulative premiums received.
    account_value: ProjectionValue          #: Sub-account value.
    interest_credited: ProjectionValue      #: Interest credited.
    gmdb_charge: ProjectionValue            #: GMDB rider charge assessed against sub\-account.
    gmwb_charge: ProjectionValue            #: GMWB rider charge assessed against sub\-account.
    withdrawal: ProjectionValue             #: Withdrawal amount apportioned to sub\-account.
    surrender_charge: ProjectionValue       #: Surrender charge.

    def __init__(
        self,
        time_steps: TimeSteps,
        data_sources: AnnuityDataSources,
        account_data_source: AccountDataSource
    ):

        r"""
        Constructor method. Creates a new sub\-account.

        :param time_steps: Projection-wide timekeeping object.
        :param data_sources: Annuity data sources.
        :param account_data_source: Account data source to initialize this sub\-account.
        """

        ProjectionEntity.__init__(
            self=self,
            time_steps=time_steps,
            data_sources=data_sources,
            init_t=account_data_source.account_date
        )

        self.account_data_source = account_data_source

        self.premiums = self._get_new_premiums(
            t1=self.init_t
        )

        self.premium_new = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_total_premium()
        )

        self.premium_cumulative = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_total_premium()
        )

        self.interest_credited = ProjectionValue(
            init_t=self.init_t,
            init_value=0.0
        )

        self.gmdb_charge = ProjectionValue(
            init_t=self.init_t,
            init_value=0.0
        )

        self.gmwb_charge = ProjectionValue(
            init_t=self.init_t,
            init_value=0.0
        )

        self.withdrawal = ProjectionValue(
            init_t=self.init_t,
            init_value=0.0
        )

        self.account_value = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_total_premium()
        )

        self.surrender_charge = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_surrender_charge()
        )

    def __str__(
        self
    ) -> str:

        return f'contract.account.{self.account_data_source.id}'

    def _get_new_premiums(
        self,
        t1: date,
        t2: date = None
    ) -> List[Premium]:

        return (
            [
                Premium(
                    time_steps=self.time_steps,
                    data_sources=self.data_sources,
                    account_id=self.account_data_source.id,
                    premium_data_source=premium_data_source,
                )
                for premium_date, premium_data_source in self.account_data_source.premiums.items
                if t1 == premium_date
            ]
            if t2 is None
            else [
                Premium(
                    time_steps=self.time_steps,
                    data_sources=self.data_sources,
                    account_id=self.account_data_source.id,
                    premium_data_source=premium_data_source,
                )
                for premium_date, premium_data_source in self.account_data_source.premiums.items
                if t1 < premium_date <= t2
            ]
        )

    def _calc_total_premium(
        self
    ) -> float:

        return sum(subpay.premium_amount for subpay in self.premiums)

    def _calc_surrender_charge(
        self
    ) -> float:

        surrender_charge = sum(subpay.surrender_charge for subpay in self.premiums)

        return min(surrender_charge, self.account_value, key=compare_latest_value)

    def process_premiums(
        self
    ) -> None:

        r"""
        #. Processes premiums paid for a single time step by looping through each premium and calling the
           premium's
           :meth:`~src.projection_entities.products.annuity.base_contract.account.premium.Premium.update_premium`
           method.

        #. Instantiates new premium payments, adding them to :attr:`premiums`.

        #. Updates :attr:`premium_new`, :attr:`premium_cumulative`, and :attr:`account_value` for new premiums.

        :return: Nothing.
        """

        if self.time_steps.t != self.init_t:

            # Age existing premiums
            for subpay in self.premiums:

                subpay.update_premium()

            # Get new premiums
            new_premiums = self._get_new_premiums(
                t1=self.time_steps.prev_t,
                t2=self.time_steps.t
            )

            self.premiums += new_premiums

            # Calculate new premium total
            self.premium_new[self.time_steps.t] = sum(
                subpay.premium_amount for subpay in new_premiums
            )

            # Update values
            self.premium_cumulative[self.time_steps.t] = self.premium_cumulative + self.premium_new

            self.account_value[self.time_steps.t] = self.account_value + self.premium_new

    @abstractmethod
    def credit_interest(
        self
    ) -> None:

        """
        Abstract method that represents an interest crediting mechanism. Inherit and override to implement
        a custom crediting algorithm (e.g. RILA, separate account crediting, or indexed crediting).

        :return: Nothing.
        """

        ...

    def process_charge(
        self,
        charge_amount: float,
        charge_account_name: str
    ) -> None:

        """
        Applies a charge to a specific charge account and reduces the :attr:`account value <account_value>`.

        .. warning:
            This algorithm does not check if the charge amount is greater than the account value.

        :param charge_amount: Withdrawal amount.
        :param charge_account_name: Charge account name.
        :return: Nothing.
        """

        charge_account = self.__dict__[charge_account_name]
        charge_account[self.time_steps.t] = charge_amount

        self.account_value[self.time_steps.t] = self.account_value - charge_amount

    def process_withdrawal(
        self,
        withdrawal_amount: float
    ) -> None:

        """
        Reduces :attr:`account value <account_value>` by a withdrawal amount
        and records the :attr:`withdrawal amount <withdrawal>`.

        .. warning:
            This algorithm does not check if the withdrawal amount is greater than the account value.

        :param withdrawal_amount: Withdrawal amount.
        :return: Nothing.
        """

        self.withdrawal[self.time_steps.t] = withdrawal_amount
        self.account_value[self.time_steps.t] = self.account_value - self.withdrawal

    def update_surrender_charge(
        self
    ) -> None:

        r"""
        Updates the :attr:`surrender charge <surrender_charge>` for this sub\-account.

        :return: Nothing.
        """

        self.surrender_charge[self.time_steps.t] = self._calc_surrender_charge()
