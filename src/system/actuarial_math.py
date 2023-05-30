"""
Convenience functions for common actuarial math operations.
"""

from dateutil.relativedelta import relativedelta

from src.system.projection_entity.projection_value import use_latest_value
from src.system.date import relativedelta_to_partial_years


@use_latest_value
def convert_decrement_rate(
    q_x: float,
    interval: relativedelta
) -> float:

    """
    Converts a decrement rate from an annual basis to another basis, using this formula:

    .. math::

        p_{interval} = (1 - q_x) ^ {interval}

        q_{interval} = 1 - p_{interval}

    :param q_x: Annual decrement rate
    :param interval: Target basis
    :return: :math:`q_{interval}`
    """

    t = relativedelta_to_partial_years(
        delta=interval
    )

    t_p_x = (1.0 - q_x) ** t

    return 1.0 - t_p_x
