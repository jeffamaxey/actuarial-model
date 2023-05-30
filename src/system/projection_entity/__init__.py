"""
Modeling framework :ref:`object model <object_model>` :ref:`Projection Entities <projection_entities>`.
"""

from abc import (
    ABC,
    abstractmethod
)
from datetime import date
from os.path import (
    join,
    dirname
)

from pandas import DataFrame

from src.system.projection.time_steps import TimeSteps
from src.system.data_sources import DataSourcesRoot
from src.system.projection_entity.projection_value import ProjectionValue
from src.system.constants import DEFAULT_COL


class ProjectionEntity(
    ABC
):

    """
    Abstract class that represents an entity within a projection (like a person or a policy). A projection
    entity is the primary building block for projections, and has several defined properties:

    #. A projection entity declares
       :class:`projection values <src.system.projection_entity.projection_value.ProjectionValue>`
       as instance attributes. For example, a *person* might have an *attained age* value.

    #. A projection entity declares instance
       `methods <https://en.wikipedia.org/wiki/Method_(computer_programming)>`_ that update its
       :class:`projection values <src.system.projection_entity.projection_value.ProjectionValue>`. For example,
       a person could have a *death* method that updates a death claim payout amount.

    #. A projection entity implements a special write
       `method <https://en.wikipedia.org/wiki/Method_(computer_programming)>`_, which prints out all its
       :class:`projection values <src.system.projection_entity.projection_value.ProjectionValue>`.

    Inherit this class to implement a custom projection entity.
    """

    time_steps: TimeSteps           #: Projection-wide timekeeping object.
    data_sources: DataSourcesRoot   #: Data sources to initialize projection values.
    init_t: date                    #: Initial time step. Marks when this entity first came into existence.

    def __init__(
        self,
        time_steps: TimeSteps,
        data_sources: DataSourcesRoot,
        init_t: date = None
    ):

        """
        Constructor method. Initializes several critical timekeeping attributes, which synchronize this projection
        entity with other projection entities across time.

        :param time_steps: Projection-wide timekeeping object.
        :param data_sources: Data sources to initialize projection values.
        :param init_t: Optional initial time step. Defaults to time_steps.t if no value is provided.
        """

        self.time_steps: TimeSteps = time_steps
        self.data_sources: DataSourcesRoot = data_sources

        self.init_t = time_steps.t if init_t is None else init_t

    @abstractmethod
    def __str__(
        self
    ) -> str:

        """
        Abstract method that provides a string representation of the projection entity. Used as the
        file name when writing output.

        :return: String representation of this object.
        """

        ...

    def write_projection_values(
        self,
        output_file_path: str
    ) -> None:

        """
        Writes all :class:`~src.system.projection_entity.projection_value.ProjectionValue` attributes in this
        projection entity to a `CSV file <https://en.wikipedia.org/wiki/Comma-separated_values>`_.
        Existing file will be overwritten.

        :param output_file_path: Output file path.
        :return: Nothing.
        """

        # Combine all values into single DataFrame
        output_dataframe = DataFrame()

        for attribute_name, attribute in self.__dict__.items():

            if issubclass(type(attribute), ProjectionValue):

                if attribute.print_values:

                    output_dataframe = output_dataframe.join(
                        other=attribute.history.rename(
                            columns={
                                DEFAULT_COL: attribute_name
                            }
                        ),
                        how='outer'
                    )

        # Write DataFrame to disk
        if not output_dataframe.empty:

            output_dataframe.insert(
                loc=0,
                column='index',
                value=range(output_dataframe.shape[0])
            )

            output_dataframe.set_index(
                keys=['index'],
                append=True
            )

            output_dataframe.to_csv(
                path_or_buf=output_file_path,
                index=True
            )

        else:

            output_dataframe.to_csv(
                path_or_buf=output_file_path,
                index=False
            )

    def write_projection_values_recursively(
        self,
        output_file_path: str
    ) -> None:

        """
        Convenience method that writes
        :class:`~src.system.projection_entity.projection_value.ProjectionValue` attributes for itself,
        as well as any nested :class:`~src.system.projection_entity.ProjectionEntity` attributes.

        This function behaves recursively, writing output for all nested projection entities no matter
        how deeply they are nested.

        :param output_file_path: Output file path
        :return: Nothing.
        """

        def _call_write_projection_values_recursively(
            projection_entity: ProjectionEntity
        ):

            projection_entity_output_file_path = join(
                dirname(output_file_path),
                f'{projection_entity}.csv'
            )

            projection_entity.write_projection_values_recursively(
                output_file_path=projection_entity_output_file_path
            )

        # Write values for this object
        self.write_projection_values(
            output_file_path=output_file_path
        )

        # Write values for all child objects
        for attribute in self.__dict__.values():

            if issubclass(type(attribute), ProjectionEntity):

                _call_write_projection_values_recursively(
                    projection_entity=attribute
                )

            elif isinstance(attribute, list):

                for element in attribute:

                    if issubclass(type(element), ProjectionEntity):

                        _call_write_projection_values_recursively(
                            projection_entity=element
                        )

            elif isinstance(attribute, dict):

                for element in attribute.values():

                    if issubclass(type(element), ProjectionEntity):

                        _call_write_projection_values_recursively(
                            projection_entity=element
                        )
