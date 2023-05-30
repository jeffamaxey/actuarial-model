"""
Convenience functions for manipulating Python `date` and `datetime` data types.
"""

from datetime import (
    date,
    datetime
)

from dateutil.relativedelta import relativedelta

from src.system.constants import DATE_FORMAT


def str_to_date(
    target_str: str
) -> date:

    """
    Converts a `string` to a `date` object, using :data:`~src.system.constants.DATE_FORMAT`.

    :param target_str: Date as a string.
    :return: A converted `string` as a `date` object.
    """

    return datetime.strptime(
        target_str,
        DATE_FORMAT
    ).date()


def date_to_str(
    target_date: date
) -> str:

    """
    Converts a `date` to a `string` object, using :data:`~src.system.constants.DATE_FORMAT`.

    :param target_date: Date as a date.
    :return: A converted `date` object as a `string`.
    """

    return target_date.strftime(
        DATE_FORMAT
    )


def calc_partial_years(
    dt1: date,
    dt2: date
) -> float:

    """
    Calculates a fractional number of years between two dates. This function is leap-year aware, and precise
    to the day.

    :param dt1: Later date.
    :param dt2: Earlier date.
    :return: Fractional number of years between two dates.
    """

    delta = relativedelta(
        dt1=dt1,
        dt2=dt2
    )

    if delta.months or delta.days:

        prior_anniversary_date = dt2 + relativedelta(
            years=delta.years
        )

        next_anniversary_date = dt2 + relativedelta(
            years=delta.years + 1
        )

        partial_year_days = (dt1 - prior_anniversary_date).days
        total_year_days = (next_anniversary_date - prior_anniversary_date).days

        years = delta.years + (partial_year_days / total_year_days)

    else:

        years = float(delta.years)

    return years


def relativedelta_to_partial_years(
    delta: relativedelta
) -> float:

    """
    Converts a `relativedelta` object to fractional years. This algorithm **is not** aware of leap years,
    and always assumes 365 days in a year.

    :param delta: Input interval.
    :return: Fractional number of years in an interval.
    """

    years = (
        delta.years +
        delta.months / 12.0 +
        delta.days / 365.0
    )

    return years


def calc_whole_years(
    dt1: date,
    dt2: date
) -> int:

    """
    Calculates an integer number of years between two dates. Partial years are rounded up.

    :param dt1: Later date.
    :param dt2: Earlier date.
    :return: Whole years between two dates.
    """

    if delta := relativedelta(dt1=dt1, dt2=dt2):
        years = delta.years + 1 if delta.months or delta.days else delta.years
    else:
        years = 1

    return years
