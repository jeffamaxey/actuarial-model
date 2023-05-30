"""
Model :class:`~src.system.projection.Projection` parameters.
"""

from os.path import exists
from json import load
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Self

from src.system.logger import Logger
from src.system.enums import ProcessingType


class ProjectionParameters:

    """
    Container class for all :class:`~src.system.projection.Projection` parameters.
    Additional projection parameters can be added here (for all projections), or this class can be inherited
    and extended for additional parameters.
    """

    # Time
    start_t: date                           #: Initial projection time step.
    projection_length: relativedelta        #: Projection duration.
    end_t: date                             #: Ending projection time step.
    time_step: relativedelta                #: Projection time step interval.

    # Paths
    resource_dir_path: str                  #: Resource directory path.
    output_dir_path: str                    #: Output directory path.

    # Processing
    processing_type: ProcessingType         #: Processing type. Controls how the projection is run and distributed.

    # Projection
    projection: str                         #: Projection import path.
    data_source: str                        #: Data source import path.

    def __init__(
        self,
        start_t: date,
        projection_length: relativedelta,
        time_step: relativedelta,
        resource_dir_path: str,
        output_dir_path: str,
        processing_type: ProcessingType,
        projection: str,
        data_source: str
    ):
        """
        Constructor method. Initializes all variables in this class.

        :param start_t: Initial projection time step.
        :param projection_length: Projection duration.
        :param time_step: Projection time step interval.
        :param resource_dir_path: Resource directory path.
        :param output_dir_path: Output directory path.
        :param processing_type: Processing type.
        :param projection: Projection import path.
        :param data_source: Data source import path.
        """

        # Time
        self.start_t: date = start_t
        self.projection_length: relativedelta = projection_length
        self.end_t: date = start_t + projection_length
        self.time_step: relativedelta = time_step

        # Paths
        self.resource_dir_path = resource_dir_path
        self.output_dir_path = output_dir_path

        # Processing
        self.processing_type = processing_type

        # Projection
        self.projection = projection
        self.data_source = data_source

    @classmethod
    def from_json(
        cls,
        path: str
    ) -> Self:

        """
        Class factory that constructs an instance of this class by
        `deserializing <https://en.wikipedia.org/wiki/Serialization>`_ a
        `JSON file <https://en.wikipedia.org/wiki/JSON>`_.

        :param path: Input JSON file path.
        :return: Instance of this class.
        """

        if not exists(path):

            Logger().raise_expr(
                expr=FileNotFoundError(
                    f'Could not locate projection parameter file at this location: {path} !'
                )
            )

        with open(file=path, mode='r') as json_file:

            json_payload = load(
                fp=json_file
            )

        return ProjectionParameters(
            start_t=date(
                year=int(json_payload['start_year']),
                month=int(json_payload['start_month']),
                day=int(json_payload['start_day']),
            ),
            projection_length=relativedelta(
                years=int(json_payload['projection_years']),
                months=int(json_payload['projection_months']),
                days=int(json_payload['projection_days']),
            ),
            time_step=relativedelta(
                years=int(json_payload['time_step_years']),
                months=int(json_payload['time_step_months']),
                days=int(json_payload['time_step_days']),
            ),
            resource_dir_path=json_payload['resource_dir_path'],
            output_dir_path=json_payload['output_dir_path'],
            processing_type=ProcessingType(json_payload['processing_type']),
            projection=json_payload['projection'],
            data_source=json_payload['data_source'],
        )
