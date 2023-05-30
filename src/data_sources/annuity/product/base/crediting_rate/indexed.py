"""
:mod:`Data source <src.system.data_sources.data_source>` for the fixed indexed account crediting table.
"""

from pandas import isna

from src.system.data_sources.data_source.file_csv import DataSourceCsvFile
from src.system.projection_entity.projection_value import use_latest_value


class IndexedCreditingRate(
    DataSourceCsvFile
):

    """
    :mod:`Data source <src.system.data_sources.data_source>` for the fixed indexed account crediting table.
    """

    def __init__(
        self,
        path: str
    ):

        """
        Constructor method. Loads data from the fixed indexed account crediting table into cache.

        Relative path to the fixed indexed account crediting table:

        ``resource/annuity/product/base/crediting_rate_indexed.csv``

        :param path: Path to the fixed indexed account crediting table.
        """

        DataSourceCsvFile.__init__(
            self=self,
            path=path
        )

        self.cache.set_index(
            keys='account_name',
            inplace=True
        )

    @use_latest_value
    def index(
        self,
        account_name: str
    ) -> str:

        """
        Returns an account's underlying index.

        :param account_name: Account name.
        :return: Index name.
        """

        return self.cache['index'][account_name]

    @use_latest_value
    def term(
        self,
        account_name: str
    ) -> int:

        """
        Returns a crediting rate term (duration of a crediting strategy), in years.

        :param account_name: Account name.
        :return: Crediting rate term.
        """

        return self.cache['term'][account_name]

    @use_latest_value
    def cap(
        self,
        account_name: str
    ) -> float | None:

        """
        Returns a crediting rate cap.

        :param account_name: Account name.
        :return: Crediting rate cap.
        """

        value = self.cache['cap'][account_name]

        return None if isna(value) else value

    @use_latest_value
    def spread(
        self,
        account_name: str
    ) -> float | None:

        """
        Returns a crediting rate spread.

        :param account_name: Account name.
        :return: Crediting rate spread.
        """

        value = self.cache['spread'][account_name]

        return None if isna(value) else value

    @use_latest_value
    def participation_rate(
        self,
        account_name: str
    ) -> float | None:

        """
        Returns a participation rate.

        :param account_name: Account name.
        :return: Participation rate.
        """

        value = self.cache['participation_rate'][account_name]

        return None if isna(value) else value

    @use_latest_value
    def floor(
        self,
        account_name: str
    ) -> float | None:

        """
        Returns a crediting rate floor.

        :param account_name: Account name.
        :return: Crediting rate floor.
        """

        value = self.cache['floor'][account_name]

        return None if isna(value) else value
