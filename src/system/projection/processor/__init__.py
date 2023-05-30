"""
:class:`~src.system.projection.Projection` processing.
"""

from abc import (
    ABC,
    abstractmethod
)
from typing import (
    List,
    Type
)
from copy import deepcopy
from os.path import splitext
from importlib import import_module

from src.system.projection import Projection
from src.system.projection.parameters import ProjectionParameters
from src.system.data_sources import DataSourcesRoot
from src.system.logger import Logger


class ProjectionProcessor(
    ABC
):

    """
    Abstract class that processes :class:`Projections <src.system.projection.Projection>`.
    """

    projection_parameters: ProjectionParameters     #: Parameters to initialize model objects.
    projections: List[Projection]   #: List of :class:`projections <src.system.projection.Projection>` to run.
    data_sources: DataSourcesRoot   #: Data sources to be read at runtime.
    projection: Type                #: :class:`~src.system.projection.Projection` class definition.

    def __init__(
        self,
        projection_parameters: ProjectionParameters
    ):

        """
        Constructor method. Creates :class:`projections <src.system.projection.Projection>` and
        :class:`root data sources <src.system.data_sources.DataSourcesRoot>`.

        :param projection_parameters: Parameters to initialize model objects.
        """

        self.projection_parameters = projection_parameters

        # Create data sources
        Logger().print(
            message=f'Compiling data sources from: {self.projection_parameters.data_source} ...'
        )

        self.data_sources = self._get_type(
            qualified_path=self.projection_parameters.data_source
        )(
            projection_parameters=self.projection_parameters
        )

        # Create projection objects
        Logger().print(
            message=f'Compiling projections from: {self.projection_parameters.projection} ...'
        )

        self.projection = self._get_type(
            qualified_path=self.projection_parameters.projection
        )

        self.projections = []

        self.projections.extend(
            self.projection(
                projection_parameters=self.projection_parameters,
                data_sources=deepcopy(configured_data_sources),
            )
            for configured_data_sources in self.data_sources.configured_data_sources()
        )

    @staticmethod
    def _get_type(
        qualified_path: str
    ) -> Type:

        """
        WARNING: Allows arbitrary code execution.

        Parses a string and returns a class definition that represents a projection object.

        :return: Class definition.
        """

        module_path, class_name = splitext(
            qualified_path
        )

        module = import_module(
            name=module_path
        )

        return module.__dict__[class_name[1:]]

    @staticmethod
    def run_projection(
        projection: Projection
    ) -> None:

        """
        Runs a single projection and writes output.

        :param projection: Projection to run.
        :return: Nothing.
        """

        # Run projection
        projection.run_projection()

        # Write output
        projection.write_output()

    def setup_output(
        self
    ) -> None:

        """
        Calls :meth:`~src.system.projection.Projection.setup_output` for each projection in
        :attr:`~src.system.projection.processor.ProjectionProcessor.projections`.

        :return: Nothing.
        """

        Logger().print(message='Setting up projection output ...')

        for projection in self.projections:

            projection.setup_output()

    @abstractmethod
    def run_projections(
        self
    ) -> None:

        """
        Abstract method to run all projections in
        :attr:`~src.system.projection.processor.ProjectionProcessor.projections`.

        :return: Nothing.
        """

        ...
