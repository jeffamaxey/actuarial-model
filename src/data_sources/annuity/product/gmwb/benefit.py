"""
:mod:`Data source <src.system.data_sources.data_source>` for GMWB benefits.
"""

from typing import Dict

from pandas import DataFrame

from src.system.data_sources.data_source.file_json import DataSourceJsonFile
from src.system.projection_entity.projection_value import use_latest_value


class GmwbBenefit(
    DataSourceJsonFile
):

    """
    :mod:`Data source <src.system.data_sources.data_source>` for GMWB benefits.
    """

    def __init__(
        self,
        path: str
    ):

        """
        Constructor method. Loads data from the GMWB benefits table into cache.

        Relative path to the GMWB benefits table:

        ``resource/annuity/product/gmwb/benefit.json``

        :param path: Path to the GMWB benefits table.
        """

        DataSourceJsonFile.__init__(
            self=self,
            path=path
        )

        # Transform tables
        self.cache = self.cache.applymap(
            func=lambda node_dict: self._parse_table_node(
                node_dict=node_dict
            )
        )

    @staticmethod
    def _parse_table_node(
        node_dict: Dict[str, float]
    ) -> DataFrame:

        table_data = DataFrame.from_dict(
            data=node_dict,
            orient='index'
        )

        table_data.index = table_data.index.astype(
            dtype=int
        )

        return table_data

    @staticmethod
    def _withdrawal_rate(
        withdrawal_rate_table: DataFrame,
        age_first_withdrawal: int
    ) -> float:

        lookup_key = withdrawal_rate_table.index[0]

        for attained_age in withdrawal_rate_table.index.to_list():

            if age_first_withdrawal >= attained_age:

                lookup_key = attained_age

            else:

                break

        return withdrawal_rate_table[0][lookup_key]

    @use_latest_value
    def av_active_withdrawal_rate(
        self,
        rider_name: str,
        age_first_withdrawal: int
    ) -> float:

        """
        Returns a GMWB withdrawal rate for policies that still have a positive account value.

        :param rider_name: Rider name.
        :param age_first_withdrawal: Attained age at 1st withdrawal.
        :return: GMWB withdrawal rate.
        """

        withdrawal_rate_table = self.cache[rider_name]['av_active']

        return self._withdrawal_rate(
            withdrawal_rate_table=withdrawal_rate_table,
            age_first_withdrawal=age_first_withdrawal,
        )

    @use_latest_value
    def av_exhaust_withdrawal_rate(
        self,
        rider_name: str,
        age_first_withdrawal: int
    ) -> float:

        """
        Returns a GMWB withdrawal rate for policies that no longer have an account value.

        :param rider_name: Rider name.
        :param age_first_withdrawal: Attained age at 1st withdrawal.
        :return: GMWB withdrawal rate.
        """

        withdrawal_rate_table = self.cache[rider_name]['av_exhausted']

        return self._withdrawal_rate(
            withdrawal_rate_table=withdrawal_rate_table,
            age_first_withdrawal=age_first_withdrawal,
        )
