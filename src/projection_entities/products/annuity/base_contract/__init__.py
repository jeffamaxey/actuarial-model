"""
Base contract for an annuity product.
"""

from typing import List
from datetime import date

from src.system.projection_entity import ProjectionEntity
from src.system.projection.time_steps import TimeSteps
from src.system.projection_entity.projection_value import ProjectionValue
from src.system.enums import (
    AccountType,
    Rider,
    DeathBenefitOptions
)
from src.system.logger import Logger
from src.system.projection.scripts.get_xversaries import get_xversaries

from src.data_sources.annuity import AnnuityDataSources
from src.data_sources.annuity.model_points.model_point.accounts.account import Account as AccountDataSource
from src.projection_entities.people.annuitants import Annuitants
from src.projection_entities.people.annuitants.annuitant import Annuitant
from src.projection_entities.products.annuity.base_contract.account import Account
from src.projection_entities.products.annuity.base_contract.account.fa import FixedAccount
from src.projection_entities.products.annuity.base_contract.account.ia import IndexedAccount
from src.projection_entities.products.annuity.base_contract.account.va import SeparateAccount
from src.projection_entities.products.annuity.riders.gmwb import Gmwb
from src.projection_entities.products.annuity.riders.gmdb.base import GmdbBase
from src.projection_entities.products.annuity.riders.gmdb.rop import GmdbRop
from src.projection_entities.products.annuity.riders.gmdb.rav import GmdbRav
from src.projection_entities.products.annuity.riders.gmdb.mav import GmdbMav


class BaseContract(
    ProjectionEntity
):

    """
    Base contract for an annuity product.
    """

    data_sources: AnnuityDataSources

    annuitants: Annuitants                                  #: List of annuitants under the base contract.
    accounts: List[Account]                                 #: List of accounts opened under the base contract.
    riders: List[Gmwb | GmdbRop | GmdbRav | GmdbMav]        #: List of riders attached to the base contract.

    quarterversaries: ProjectionValue                       #: List of quarterversaries within one time step.
    monthiversaries: ProjectionValue                        #: List of monthiversaries within one time step.
    anniversaries: ProjectionValue                          #: List of anniversaries within one time step.
    premium_new: ProjectionValue                            #: New premiums received.
    premium_cumulative: ProjectionValue                     #: Cumulative premiums received.
    interest_credited: ProjectionValue                      #: Interest credited.
    gmdb_charge: ProjectionValue                            #: GMDB rider charge.
    gmwb_charge: ProjectionValue                            #: GMWB rider charge.
    withdrawal: ProjectionValue                             #: Withdrawals taken.
    account_value: ProjectionValue                          #: Account value.
    surrender_charge: ProjectionValue                       #: Point-in-time surrender charge.
    cash_surrender_value: ProjectionValue                   #: Point-in-time cash surrender value.

    def __init__(
        self,
        time_steps: TimeSteps,
        data_sources: AnnuityDataSources
    ):

        """
        Constructor method. Creates an annuity contract, along with sibling Projection Entities:

        - Riders
        - Annuitants
        - Sub-accounts

        :param time_steps: Projection-wide timekeeping object.
        :param data_sources: Annuity data sources.
        """

        ProjectionEntity.__init__(
            self=self,
            time_steps=time_steps,
            data_sources=data_sources
        )

        self.annuitants = Annuitants(
            time_steps=self.time_steps,
            data_sources=self.data_sources
        )

        self.accounts = self._get_new_accounts(
            t1=self.init_t
        )

        self.riders = []

        for rider_data_source in self.data_sources.model_point.riders:

            if rider_data_source.rider_type == Rider.GUARANTEED_MINIMUM_WITHDRAWAL_BENEFIT:

                self.riders.append(
                    Gmwb(
                        time_steps=self.time_steps,
                        data_sources=self.data_sources,
                        gmwb_data_source=rider_data_source
                    )
                )

            elif rider_data_source.rider_type == Rider.GUARANTEED_MINIMUM_DEATH_BENEFIT:

                rider_type = self.data_sources.product.gmdb_rider.gmdb_types.gmdb_type(
                    rider_name=rider_data_source.rider_name
                )

                if rider_type == DeathBenefitOptions.RETURN_OF_PREMIUM:

                    self.riders.append(
                        GmdbRop(
                            time_steps=self.time_steps,
                            data_sources=self.data_sources,
                            gmdb_data_source=rider_data_source
                        )
                    )

                elif rider_type == DeathBenefitOptions.ACCOUNT_VALUE_RATCHET:

                    self.riders.append(
                        GmdbMav(
                            time_steps=self.time_steps,
                            data_sources=self.data_sources,
                            gmdb_data_source=rider_data_source
                        )
                    )

                elif rider_type == DeathBenefitOptions.RETURN_OF_ACCOUNT_VALUE:

                    self.riders.append(
                        GmdbRav(
                            time_steps=self.time_steps,
                            data_sources=self.data_sources,
                            gmdb_data_source=rider_data_source
                        )
                    )

                else:

                    Logger().raise_expr(
                        expr=NotImplementedError(
                            f'Unhandled GMDB rider type: {rider_type} !'
                        )
                    )

        self.quarterversaries = ProjectionValue(
            init_t=self.init_t,
            init_value=[[]],
            print_values=False
        )

        self.monthiversaries = ProjectionValue(
            init_t=self.init_t,
            init_value=[[]],
            print_values=False
        )

        self.anniversaries = ProjectionValue(
            init_t=self.init_t,
            init_value=[[]],
            print_values=False
        )

        self.premium_new = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_new_premium()
        )

        self.premium_cumulative = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_new_premium()
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
            init_value=self._calc_account_value()
        )

        self.surrender_charge = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_surrender_charge()
        )

        self.cash_surrender_value = ProjectionValue(
            init_t=self.init_t,
            init_value=self._calc_cash_surrender_value()
        )

    def __str__(
        self
    ) -> str:

        return 'contract'

    def _get_new_account(
        self,
        account_data_source: AccountDataSource
    ) -> Account:

        if account_data_source.account_type == AccountType.FIXED:

            return FixedAccount(
                time_steps=self.time_steps,
                data_sources=self.data_sources,
                account_data_source=account_data_source
            )

        elif account_data_source.account_type == AccountType.INDEXED:

            return IndexedAccount(
                time_steps=self.time_steps,
                data_sources=self.data_sources,
                account_data_source=account_data_source
            )

        elif account_data_source.account_type == AccountType.SEPARATE:

            return SeparateAccount(
                time_steps=self.time_steps,
                data_sources=self.data_sources,
                account_data_source=account_data_source
            )

        else:

            Logger().raise_expr(
                expr=NotImplementedError(
                    f'Unhandled account type: {account_data_source.account_type} !'
                )
            )

    def _get_new_accounts(
        self,
        t1: date,
        t2: date = None
    ) -> List[Account]:

        return (
            [
                self._get_new_account(account_data_source=account_data_source)
                for account_data_source in self.data_sources.model_point.accounts
                if t1 == account_data_source.account_date
            ]
            if t2 is None
            else [
                self._get_new_account(account_data_source=account_data_source)
                for account_data_source in self.data_sources.model_point.accounts
                if t1 < account_data_source.account_date <= t2
            ]
        )

    def _calc_new_premium(
        self
    ) -> float:

        return sum(sub_account.premium_new for sub_account in self.accounts)

    def _calc_account_value(
        self
    ) -> float:

        return sum(sub_account.account_value for sub_account in self.accounts)

    def _calc_surrender_charge(
        self
    ) -> float:

        return sum(sub_account.surrender_charge for sub_account in self.accounts)

    def _calc_cash_surrender_value(
        self
    ) -> float:

        return max(
            self.account_value - self.surrender_charge,
            0.0
        )

    @property
    def primary_annuitant(
        self
    ) -> Annuitant:

        """
        Convenience property to get the primary annuitant.
        Links to :attr:`~src.projection_entities.people.annuitants.Annuitants.primary_annuitant`.

        :return: Primary annuitant.
        """

        return self.annuitants.primary_annuitant

    def age_contract(
        self
    ) -> None:

        """
        Scans current time step for :attr:`monthiversaries`, :attr:`quarterversaries`, and :attr:`anniversaries` using
        :func:`~src.system.projection.scripts.get_xversaries.get_xversaries`.

        :return: Nothing.
        """

        # Update upcoming anniversaries
        self.monthiversaries[self.time_steps.t] = [get_xversaries(
            issue_date=self.data_sources.model_point.issue_date,
            start_date=self.time_steps.prev_t,
            end_date=self.time_steps.t,
            frequency=1
        )]

        self.quarterversaries[self.time_steps.t] = [get_xversaries(
            issue_date=self.data_sources.model_point.issue_date,
            start_date=self.time_steps.prev_t,
            end_date=self.time_steps.t,
            frequency=3
        )]

        self.anniversaries[self.time_steps.t] = [get_xversaries(
            issue_date=self.data_sources.model_point.issue_date,
            start_date=self.time_steps.prev_t,
            end_date=self.time_steps.t,
            frequency=12
        )]

    def process_premiums(
        self
    ) -> None:

        r"""
        #. Processes premiums paid for a single time step by looping through each sub\-account and calling the
           sub-\account's
           :meth:`~src.projection_entities.products.annuity.base_contract.account.Account.process_premiums` method.

        #. Instantiates new sub\-accounts, adding them to :attr:`accounts`.

        #. Updates :attr:`premium_new`, :attr:`premium_cumulative`, and :attr:`account_value` for new premiums.

        #. Calls :meth:`update_cash_surrender_value` to recalculate cash surrender value.

        :return: Nothing.
        """

        if self.time_steps.t != self.init_t:

            # Process premiums for existing accounts
            for sub_account in self.accounts:

                sub_account.process_premiums()

            # Get new accounts
            if self.time_steps.t != self.init_t:

                new_accounts = self._get_new_accounts(
                    t1=self.time_steps.prev_t,
                    t2=self.time_steps.t
                )

                self.accounts += new_accounts

            # Calculate new premium total
            self.premium_new[self.time_steps.t] = self._calc_new_premium()

            # Update values
            self.premium_cumulative[self.time_steps.t] = self.premium_cumulative + self.premium_new

            self.account_value[self.time_steps.t] = self._calc_account_value()

            self.update_cash_surrender_value()

        # Process premiums for riders
        for rider in self.riders:

            rider.process_premiums(
                base_contract=self
            )

    def credit_interest(
        self
    ) -> None:

        r"""
        #. Projects interest credited for a single time step by looping through each sub\-account and calling the
           sub-\account's
           :meth:`~src.projection_entities.products.annuity.base_contract.account.Account.credit_interest` method.

        #. Updates :attr:`account_value` and :attr:`interest_credited` to reflect interest earned and credited to the
           account value.

        #. Calls :meth:`update_cash_surrender_value` to recalculate cash surrender value.

        :return: Nothing.
        """

        # Credit interest for each account
        interest_credited = 0.0

        for sub_account in self.accounts:

            sub_account.credit_interest()

            interest_credited += sub_account.interest_credited

        # Update values
        self.account_value[self.time_steps.t] = self._calc_account_value()
        self.interest_credited[self.time_steps.t] = interest_credited

        self.update_cash_surrender_value()

    def assess_charge(
        self,
        charge_amount: ProjectionValue,
        charge_account_name: str
    ) -> None:

        r"""
        #. Applies a charge to a specific charge account, pro\-rata across all sub\-accounts, using
           :meth:`~src.projection_entities.products.annuity.base_contract.account.Account.process_charge`.

        #. Updates :attr:`account_value` to reflect charge.

        #. Calls :meth:`update_cash_surrender_value` to recalculate cash surrender value.

        :param charge_amount: Dollar amount of charge.
        :param charge_account_name: Charge account name.
        :return: Nothing.
        """

        # Apply charge pro rata across accounts
        for sub_account in self.accounts:

            if self.account_value:

                pro_rata_factor = sub_account.account_value / self.account_value

            else:

                pro_rata_factor = 0.0

            pro_rata_charge = charge_amount * pro_rata_factor

            sub_account.process_charge(
                charge_amount=pro_rata_charge,
                charge_account_name=charge_account_name
            )

        # Update values
        charge_account = self.__dict__[charge_account_name]
        charge_account[self.time_steps.t] = charge_amount

        self.account_value[self.time_steps.t] = self._calc_account_value()
        self.update_cash_surrender_value()

    def assess_charges(
        self
    ) -> None:

        """
        Loops through each rider and calls the rider's ``process_charge`` method. Depending on the rider, this could be:

        - GMWB :meth:`~src.projection_entities.products.annuity.riders.gmwb.Gmwb.process_charge`
        - GMDB :meth:`~src.projection_entities.products.annuity.riders.gmdb.base.GmdbBase.process_charge`

        :return: Nothing.
        """

        # Assess rider charges
        for rider in self.riders:

            rider.process_charge(
                base_contract=self
            )

    def process_withdrawal(
        self,
        withdrawal_amount: ProjectionValue
    ) -> None:

        r"""
        #. Applies a withdrawal pro\-rata across all sub\-accounts, using
           :meth:`~src.projection_entities.products.annuity.base_contract.account.Account.process_withdrawal`.

        #. Updates :attr:`account_value` to reflect withdrawal.

        #. Calls :meth:`update_cash_surrender_value` to recalculate cash surrender value.

        :param withdrawal_amount: Withdrawal amount.
        :return: Nothing.
        """

        # Apply withdrawal pro rata across accounts
        for sub_account in self.accounts:

            if self.account_value:

                pro_rata_factor = sub_account.account_value / self.account_value

            else:

                pro_rata_factor = 0.0

            pro_rata_withdrawal = withdrawal_amount * pro_rata_factor

            sub_account.process_withdrawal(
                withdrawal_amount=pro_rata_withdrawal
            )

        # Update values
        self.withdrawal[self.time_steps.t] = withdrawal_amount
        self.account_value[self.time_steps.t] = self._calc_account_value()
        self.update_cash_surrender_value()

    def process_withdrawals(
        self
    ) -> None:

        """
        Processes GMWB withdrawals by calling each GMWB rider's
        :meth:`~src.projection_entities.products.annuity.riders.gmwb.Gmwb.process_withdrawal` method.

        :return: Nothing.
        """

        for rider in self.riders:

            if isinstance(rider, Gmwb):

                rider.process_withdrawal(
                    base_contract=self
                )

    def update_gmdb_naar(
        self
    ) -> None:

        """
        Updates GMDB Net Amount At Risk (NAAR) by calling each GMDB rider's
        :meth:`~src.projection_entities.products.annuity.riders.gmdb.base.update_net_amount_at_risk` method.

        :return: Nothing.
        """

        for rider in self.riders:

            if issubclass(type(rider), GmdbBase):

                rider.update_net_amount_at_risk(
                    base_contract=self
                )

    def update_cash_surrender_value(
        self
    ) -> None:

        r"""
        Updates the surrender charge for each sub\-account, using
        :meth:`~src.projection_entities.products.annuity.base_contract.account.Account.update_surrender_charge`.

        Once surrender charges are updated, calculates the aggregate :attr:`surrender charge <surrender_charge>` and
        :attr:`cash surrender value <cash_surrender_value>`.

        :return: Nothing.
        """

        for sub_account in self.accounts:

            sub_account.update_surrender_charge()

        self.surrender_charge[self.time_steps.t] = self._calc_surrender_charge()
        self.cash_surrender_value[self.time_steps.t] = self._calc_cash_surrender_value()
